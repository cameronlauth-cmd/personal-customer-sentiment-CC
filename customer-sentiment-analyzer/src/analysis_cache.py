"""
Analysis Cache Manager for incremental sentiment analysis.
Stores per-message analysis results to avoid re-processing.
Implements three-gate architecture for efficient analysis triggering.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd

from config.settings import (
    GATE1_AVG_THRESHOLD,
    GATE1_PEAK_THRESHOLD,
    GATE2_CRITICALITY_THRESHOLD,
    RECENT_WINDOW_DAYS,
    normalize_case_number
)


class AnalysisCache:
    """Manages cached analysis results for incremental processing."""

    CLOSED_STATUSES = [
        "Closed", "Closed No Response", "Closed Duplicate",
        "Closed Spam", "Closed-Test", "Closed-NA"
    ]

    def __init__(self, cache_file: str = "data/analysis_cache.json"):
        """Initialize the cache manager.

        Args:
            cache_file: Path to the JSON cache file
        """
        self.cache_file = cache_file
        self.cache = self._load_cache()

    def _load_cache(self) -> Dict:
        """Load cache from disk or create empty structure."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                # Run migration to normalize case number keys
                cache = self._migrate_case_numbers(cache)
                return cache
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load cache file: {e}")
                return self._empty_cache()
        return self._empty_cache()

    def _migrate_case_numbers(self, cache: Dict) -> Dict:
        """
        Migrate existing cache to use normalized case number keys.

        Handles duplicates by keeping the most recently updated entry.
        """
        old_cases = cache.get("cases", {})
        if not old_cases:
            return cache

        new_cases = {}
        migrated = 0

        for old_key, case_data in old_cases.items():
            new_key = normalize_case_number(old_key)

            if new_key != old_key:
                migrated += 1

            # Handle potential duplicates (merge if exists)
            if new_key in new_cases:
                # Keep the more recently updated one
                existing = new_cases[new_key]
                existing_updated = existing.get("last_updated", "")
                case_updated = case_data.get("last_updated", "")
                if case_updated > existing_updated:
                    new_cases[new_key] = case_data
            else:
                new_cases[new_key] = case_data

        if migrated > 0:
            print(f"Migrated {migrated} case number keys to normalized format")

        cache["cases"] = new_cases
        return cache

    def _empty_cache(self) -> Dict:
        """Return empty cache structure."""
        return {
            "cases": {},
            "metadata": {
                "last_open_upload": None,
                "last_closed_upload": None,
                "total_cases": 0,
                "open_cases": 0,
                "closed_cases": 0
            }
        }

    def save_cache(self) -> None:
        """Save cache to disk."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)

        # Update metadata counts
        self._update_metadata_counts()

        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, indent=2, default=str)

    def _update_metadata_counts(self) -> None:
        """Update case counts in metadata."""
        cases = self.cache.get("cases", {})
        open_count = sum(1 for c in cases.values() if c.get("status", "Open") not in self.CLOSED_STATUSES)
        closed_count = len(cases) - open_count

        self.cache["metadata"]["total_cases"] = len(cases)
        self.cache["metadata"]["open_cases"] = open_count
        self.cache["metadata"]["closed_cases"] = closed_count

    def get_cached_case(self, case_number: str) -> Optional[Dict]:
        """Get cached analysis for a case.

        Args:
            case_number: The case number to look up

        Returns:
            Cached case data or None if not found
        """
        return self.cache.get("cases", {}).get(normalize_case_number(case_number))

    def get_all_cases(self, include_closed: bool = False) -> Dict[str, Dict]:
        """Get all cached cases.

        Args:
            include_closed: Whether to include closed cases

        Returns:
            Dictionary of case_number -> case_data
        """
        cases = self.cache.get("cases", {})
        if include_closed:
            return cases
        return {
            k: v for k, v in cases.items()
            if v.get("status", "Open") not in self.CLOSED_STATUSES
        }

    def get_last_message_date(self, case_number: str) -> Optional[datetime]:
        """Get the date of the last analyzed message for a case.

        Args:
            case_number: The case number

        Returns:
            datetime of last message or None
        """
        case = self.get_cached_case(case_number)
        if not case or not case.get("messages"):
            return None

        # Find the most recent message date
        dates = []
        for msg in case["messages"]:
            if msg.get("date"):
                try:
                    dates.append(pd.to_datetime(msg["date"]))
                except:
                    pass

        return max(dates) if dates else None

    def get_new_messages(self, case_number: str, messages_df: pd.DataFrame) -> pd.DataFrame:
        """Filter DataFrame to only include messages newer than cached.

        Args:
            case_number: The case number
            messages_df: DataFrame with all messages for this case

        Returns:
            DataFrame with only new messages
        """
        last_date = self.get_last_message_date(case_number)

        if last_date is None:
            # No cache - all messages are new
            return messages_df

        # Filter to messages after last cached date
        if "Message Date" in messages_df.columns:
            messages_df["Message Date"] = pd.to_datetime(messages_df["Message Date"])
            new_messages = messages_df[messages_df["Message Date"] > last_date]
            return new_messages

        # Can't filter without dates - return all
        return messages_df

    def has_new_messages(self, case_number: str, messages_df: pd.DataFrame) -> bool:
        """Check if there are new messages for a case.

        Args:
            case_number: The case number
            messages_df: DataFrame with all messages for this case

        Returns:
            True if there are new messages to analyze
        """
        new_msgs = self.get_new_messages(case_number, messages_df)
        return len(new_msgs) > 0

    def update_case(self, case_number: str, case_data: Dict) -> None:
        """Update or create a case in the cache.

        Args:
            case_number: The case number
            case_data: Full case data to store
        """
        case_number = normalize_case_number(case_number)
        existing = self.get_cached_case(case_number)

        if existing:
            # Merge new data with existing
            existing.update({
                "customer_name": case_data.get("customer_name", existing.get("customer_name")),
                "severity": case_data.get("severity", existing.get("severity")),
                "support_level": case_data.get("support_level", existing.get("support_level")),
                "status": case_data.get("status", existing.get("status", "Open")),
                "last_updated": datetime.now().isoformat(),
                "last_message_date": case_data.get("last_message_date", existing.get("last_message_date")),
            })

            # Merge messages (add new ones)
            if "messages" in case_data:
                existing_dates = {m.get("date") for m in existing.get("messages", [])}
                for msg in case_data.get("messages", []):
                    if msg.get("date") not in existing_dates:
                        existing.setdefault("messages", []).append(msg)

            # Update context summary if provided
            if "context_summary" in case_data:
                existing["context_summary"] = case_data["context_summary"]

            # Update metrics
            if "metrics" in case_data:
                existing["metrics"] = case_data["metrics"]

            self.cache["cases"][case_number] = existing
        else:
            # New case
            case_data["first_seen"] = datetime.now().isoformat()
            case_data["last_updated"] = datetime.now().isoformat()
            case_data.setdefault("status", "Open")
            self.cache["cases"][case_number] = case_data

    def add_message_analysis(self, case_number: str, message_data: Dict) -> None:
        """Add a single message analysis to a case.

        Args:
            case_number: The case number
            message_data: Message analysis data with date, frustration, summary, etc.
        """
        case_number = normalize_case_number(case_number)
        case = self.get_cached_case(case_number)

        if not case:
            # Create minimal case entry
            case = {
                "first_seen": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "status": "Open",
                "messages": []
            }
            self.cache["cases"][case_number] = case

        # Check if message already exists (by date)
        existing_dates = {m.get("date") for m in case.get("messages", [])}
        if message_data.get("date") not in existing_dates:
            case.setdefault("messages", []).append(message_data)
            case["last_updated"] = datetime.now().isoformat()

            # Update last_message_date
            if message_data.get("date"):
                current_last = case.get("last_message_date")
                if not current_last or message_data["date"] > current_last:
                    case["last_message_date"] = message_data["date"]

    def update_context_summary(self, case_number: str, summary: str) -> None:
        """Update the context summary for a case.

        Args:
            case_number: The case number
            summary: New context summary
        """
        case = self.get_cached_case(str(case_number))
        if case:
            case["context_summary"] = summary
            case["last_updated"] = datetime.now().isoformat()

    def mark_cases_closed(self, case_numbers: List[str], status: str = "Closed") -> int:
        """Mark multiple cases as closed.

        Args:
            case_numbers: List of case numbers to close
            status: The closed status to apply

        Returns:
            Number of cases updated
        """
        updated = 0
        for case_number in case_numbers:
            case = self.get_cached_case(str(case_number))
            if case:
                case["status"] = status
                case["last_updated"] = datetime.now().isoformat()
                updated += 1

        if updated:
            self.cache["metadata"]["last_closed_upload"] = datetime.now().isoformat()

        return updated

    def calculate_recent_metrics(self, case_number: str, window_days: int = 14) -> Dict:
        """Calculate recent frustration metrics for a case.

        Args:
            case_number: The case number
            window_days: Number of days to consider as "recent"

        Returns:
            Dictionary with recent metrics
        """
        case = self.get_cached_case(str(case_number))
        if not case or not case.get("messages"):
            return {
                "recent_frustration": 0,
                "historical_frustration": 0,
                "trend": "stable",
                "has_recent_activity": False,
                "days_since_last_message": None
            }

        messages = case["messages"]
        cutoff = datetime.now() - timedelta(days=window_days)

        recent_scores = []
        historical_scores = []
        latest_date = None

        for msg in messages:
            if not msg.get("date") or msg.get("frustration") is None:
                continue

            try:
                msg_date = pd.to_datetime(msg["date"])
                if latest_date is None or msg_date > latest_date:
                    latest_date = msg_date

                # Only count customer messages for frustration
                if msg.get("is_customer", True):
                    if msg_date >= cutoff:
                        recent_scores.append(msg["frustration"])
                    else:
                        historical_scores.append(msg["frustration"])
            except:
                pass

        # Calculate averages
        recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
        historical_avg = sum(historical_scores) / len(historical_scores) if historical_scores else 0

        # Determine trend
        if not recent_scores:
            trend = "stable"
        elif recent_avg > historical_avg + 1.5:
            trend = "declining"
        elif recent_avg < historical_avg - 1.5:
            trend = "improving"
        else:
            trend = "stable"

        # Days since last message
        days_since = None
        if latest_date:
            days_since = (datetime.now() - latest_date.to_pydatetime().replace(tzinfo=None)).days

        return {
            "recent_frustration": round(recent_avg, 1),
            "historical_frustration": round(historical_avg, 1),
            "trend": trend,
            "has_recent_activity": len(recent_scores) > 0,
            "days_since_last_message": days_since,
            "recent_message_count": len(recent_scores),
            "total_message_count": len(messages)
        }

    def update_case_metrics(self, case_number: str, window_days: int = 14) -> None:
        """Recalculate and update metrics for a case.

        Args:
            case_number: The case number
            window_days: Number of days for recent window
        """
        case = self.get_cached_case(str(case_number))
        if not case:
            return

        metrics = self.calculate_recent_metrics(case_number, window_days)

        # Also calculate peak frustration
        peak = 0
        for msg in case.get("messages", []):
            if msg.get("frustration", 0) > peak:
                peak = msg["frustration"]

        case["metrics"] = {
            "peak_frustration": peak,
            "recent_frustration_14d": metrics["recent_frustration"],
            "historical_frustration": metrics["historical_frustration"],
            "trend": metrics["trend"],
            "has_recent_activity": metrics["has_recent_activity"],
            "days_since_last_message": metrics["days_since_last_message"],
            "message_count": metrics["total_message_count"]
        }

    def get_cases_needing_attention(self, window_days: int = 14, min_frustration: float = 7.0) -> List[Dict]:
        """Get cases with recent declining sentiment or high recent frustration.

        Args:
            window_days: Recent activity window
            min_frustration: Minimum recent frustration to flag

        Returns:
            List of case data for cases needing attention
        """
        attention_cases = []

        for case_number, case in self.get_all_cases(include_closed=False).items():
            metrics = self.calculate_recent_metrics(case_number, window_days)

            # Flag if declining or high recent frustration
            needs_attention = (
                metrics["has_recent_activity"] and
                (metrics["trend"] == "declining" or metrics["recent_frustration"] >= min_frustration)
            )

            if needs_attention:
                attention_cases.append({
                    "case_number": case_number,
                    **case,
                    "calculated_metrics": metrics
                })

        # Sort by recent frustration descending
        attention_cases.sort(key=lambda x: x["calculated_metrics"]["recent_frustration"], reverse=True)

        return attention_cases

    def clear_case(self, case_number: str) -> bool:
        """Remove a case from the cache (for re-analysis).

        Args:
            case_number: The case number to remove

        Returns:
            True if case was removed
        """
        case_number = normalize_case_number(case_number)
        if case_number in self.cache.get("cases", {}):
            del self.cache["cases"][case_number]
            return True
        return False

    def clear_all(self) -> None:
        """Clear entire cache."""
        self.cache = self._empty_cache()

    def get_cache_stats(self) -> Dict:
        """Get statistics about the cache.

        Returns:
            Dictionary with cache statistics
        """
        self._update_metadata_counts()

        cases = self.cache.get("cases", {})
        total_messages = sum(len(c.get("messages", [])) for c in cases.values())

        return {
            **self.cache["metadata"],
            "total_messages_cached": total_messages,
            "cache_file": self.cache_file,
            "cache_file_exists": os.path.exists(self.cache_file)
        }

    def export_for_dashboard(self, include_closed: bool = False) -> List[Dict]:
        """Export cases in format compatible with existing dashboard.

        Args:
            include_closed: Whether to include closed cases

        Returns:
            List of case dictionaries for dashboard display
        """
        export_cases = []

        for case_number, case in self.get_all_cases(include_closed=include_closed).items():
            # Recalculate metrics
            metrics = self.calculate_recent_metrics(case_number)

            # Build deepseek_analysis with timeline entries merged in
            deepseek_analysis = case.get("deepseek_analysis", {}).copy() if case.get("deepseek_analysis") else {}

            # If case has a timeline stored separately (from gate system), merge it into deepseek_analysis
            timeline = case.get("timeline", {})
            if timeline:
                timeline_entries = timeline.get("entries", timeline.get("timeline_entries", []))
                if timeline_entries and not deepseek_analysis.get("timeline_entries"):
                    deepseek_analysis["timeline_entries"] = timeline_entries
                    # Also copy over summary fields from timeline if not in deepseek_analysis
                    if timeline.get("executive_summary") and not deepseek_analysis.get("executive_summary"):
                        deepseek_analysis["executive_summary"] = timeline.get("executive_summary")
                    if timeline.get("recommended_action") and not deepseek_analysis.get("recommended_action"):
                        deepseek_analysis["recommended_action"] = timeline.get("recommended_action")
                    if timeline.get("pain_points") and not deepseek_analysis.get("pain_points"):
                        deepseek_analysis["pain_points"] = timeline.get("pain_points")
                    if timeline.get("sentiment_trend") and not deepseek_analysis.get("sentiment_trend"):
                        deepseek_analysis["sentiment_trend"] = timeline.get("sentiment_trend")
                    if timeline.get("customer_priority") and not deepseek_analysis.get("customer_priority"):
                        deepseek_analysis["customer_priority"] = timeline.get("customer_priority")
                    if timeline.get("critical_inflection_points") and not deepseek_analysis.get("critical_inflection_points"):
                        deepseek_analysis["critical_inflection_points"] = timeline.get("critical_inflection_points")
                    # Mark as successful if it has entries
                    deepseek_analysis["analysis_successful"] = True

            # Build dashboard-compatible structure
            export_case = {
                "case_number": case_number,
                "customer_name": case.get("customer_name", "Unknown"),
                "severity": case.get("severity", "S4"),
                "support_level": case.get("support_level", "Unknown"),
                "status": case.get("status", "Open"),
                "interaction_count": case.get("interaction_count", len(case.get("messages", []))),
                "context_summary": case.get("context_summary", ""),

                # Case metadata
                "case_age_days": case.get("case_age_days", 0),
                "customer_engagement_ratio": case.get("customer_engagement_ratio", 0),
                "created_date": case.get("created_date"),
                "last_modified_date": case.get("last_modified_date"),

                # Metrics for scoring
                "recent_frustration_14d": metrics["recent_frustration"],
                "historical_frustration": metrics["historical_frustration"],
                "trend": metrics["trend"],
                "has_recent_activity": metrics["has_recent_activity"],
                "days_since_last_message": metrics["days_since_last_message"],

                # Include original analysis if present
                "claude_analysis": case.get("claude_analysis", {}),
                "deepseek_analysis": deepseek_analysis,
                "deepseek_quick_scoring": case.get("deepseek_quick_scoring", {}),

                # Gate tracking for dashboard filters
                "gate1_passed": case.get("gate1_passed", False),
                "gate1_passed_date": case.get("gate1_passed_date"),
                "gate2_passed": case.get("gate2_passed", False),
                "criticality_score": case.get("criticality_score", 0),
                "has_timeline": case.get("has_timeline", False),
            }

            export_cases.append(export_case)

        return export_cases

    # =========================================================================
    # THREE-GATE ARCHITECTURE METHODS
    # =========================================================================

    def update_haiku_scores(
        self,
        case_number: str,
        new_scores: List[Dict],
        case_metadata: Optional[Dict] = None,
        claude_analysis: Optional[Dict] = None
    ) -> bool:
        """Update running frustration scores from Haiku analysis.

        Gate 1 Check: Determines if case should proceed to Gate 2 (Sonnet quick).
        Trigger: Avg frustration >= 3 OR Peak frustration >= 6

        Args:
            case_number: The case number
            new_scores: List of dicts with 'frustration', 'date', 'is_customer', etc.
            case_metadata: Optional dict with customer_name, severity, support_level
            claude_analysis: Optional full Haiku analysis dict for dashboard display

        Returns:
            True if Gate 1 threshold crossed (needs Gate 2 analysis)
        """
        case_number = normalize_case_number(case_number)
        case = self.get_cached_case(case_number)

        if not case:
            # Create new case entry
            case = {
                "first_seen": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "status": "Open",
                "messages": [],
                "avg_frustration": 0,
                "peak_frustration": 0,
                "gate1_passed": False,
                "gate1_passed_date": None,
                "gate2_passed": False,
                "criticality_score": 0,
                "sonnet_analysis": None,
                "has_timeline": False,
                "timeline": None,
                "claude_analysis": None,
            }
            self.cache["cases"][case_number] = case

        # Store the full claude_analysis for dashboard display
        if claude_analysis:
            case["claude_analysis"] = claude_analysis

        # Update metadata if provided
        if case_metadata:
            case["customer_name"] = case_metadata.get("customer_name", case.get("customer_name"))
            case["severity"] = case_metadata.get("severity", case.get("severity"))
            case["support_level"] = case_metadata.get("support_level", case.get("support_level"))

        # Add new message scores
        existing_dates = {m.get("date") for m in case.get("messages", [])}
        for score in new_scores:
            if score.get("date") not in existing_dates:
                case.setdefault("messages", []).append(score)

        # Recalculate running avg and peak from ALL messages
        all_frustrations = [
            m["frustration"] for m in case.get("messages", [])
            if m.get("frustration") is not None and m.get("is_customer", True)
        ]

        if all_frustrations:
            case["avg_frustration"] = round(sum(all_frustrations) / len(all_frustrations), 2)
            case["peak_frustration"] = max(all_frustrations)
        else:
            case["avg_frustration"] = 0
            case["peak_frustration"] = 0

        # Update last message date
        msg_dates = []
        for m in case.get("messages", []):
            if m.get("date"):
                try:
                    msg_dates.append(pd.to_datetime(m["date"]))
                except:
                    pass
        if msg_dates:
            case["last_message_date"] = max(msg_dates).isoformat()

        case["last_updated"] = datetime.now().isoformat()

        # Check Gate 1 threshold
        was_passed = case.get("gate1_passed", False)
        passes_gate1 = (
            case["avg_frustration"] >= GATE1_AVG_THRESHOLD or
            case["peak_frustration"] >= GATE1_PEAK_THRESHOLD
        )

        if passes_gate1 and not was_passed:
            case["gate1_passed"] = True
            case["gate1_passed_date"] = datetime.now().isoformat()
            return True  # Newly triggered - needs Gate 2

        return False  # Not newly triggered (may already be passed)

    def update_case_full_data(self, case_number: str, case_data: Dict) -> None:
        """Update cache with full case data for dashboard display.

        Called after all analysis is complete to store fields needed
        for the Load Dashboard feature.

        Args:
            case_number: The case number
            case_data: Full case dict with all analysis results
        """
        case_number = normalize_case_number(case_number)
        case = self.get_cached_case(case_number)

        if not case:
            # Create new cache entry if case doesn't exist
            # This can happen when all messages are "cached" but case wasn't in cache
            case = {
                "first_seen": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "status": case_data.get("status", "Open"),
                "messages": [],
                "avg_frustration": 0,
                "peak_frustration": 0,
                "gate1_passed": False,
                "gate1_passed_date": None,
                "gate2_passed": False,
                "criticality_score": 0,
                "sonnet_analysis": None,
                "has_timeline": False,
                "timeline": None,
                "claude_analysis": case_data.get("claude_analysis"),
                "customer_name": case_data.get("customer_name"),
                "severity": case_data.get("severity"),
                "support_level": case_data.get("support_level"),
            }
            self.cache["cases"][case_number] = case

        # Store dashboard-needed fields
        case["case_age_days"] = case_data.get("case_age_days", 0)
        case["interaction_count"] = case_data.get("interaction_count", 0)
        case["customer_engagement_ratio"] = case_data.get("customer_engagement_ratio", 0)
        case["created_date"] = case_data.get("created_date")
        case["last_modified_date"] = case_data.get("last_modified_date")
        case["criticality_score"] = case_data.get("criticality_score", 0)
        case["issue_category"] = case_data.get("issue_category", "Unknown")

        # Update frustration from claude_analysis if available
        claude_analysis = case_data.get("claude_analysis", {})
        if claude_analysis:
            frustration = claude_analysis.get("frustration_score", 0)
            # Update avg/peak if not already set or if this is higher
            if frustration > case.get("avg_frustration", 0):
                case["avg_frustration"] = frustration
            if frustration > case.get("peak_frustration", 0):
                case["peak_frustration"] = frustration

            # Check Gate 1 eligibility if not already passed
            if not case.get("gate1_passed"):
                avg = case.get("avg_frustration", 0)
                peak = case.get("peak_frustration", 0)
                if avg >= GATE1_AVG_THRESHOLD or peak >= GATE1_PEAK_THRESHOLD:
                    case["gate1_passed"] = True
                    case["gate1_passed_date"] = datetime.now().isoformat()

        # Store deepseek analysis if available
        if case_data.get("deepseek_analysis"):
            case["deepseek_analysis"] = case_data["deepseek_analysis"]

        # Store quick scoring if available
        if case_data.get("deepseek_quick_scoring"):
            case["deepseek_quick_scoring"] = case_data["deepseek_quick_scoring"]

        case["last_updated"] = datetime.now().isoformat()

    def get_cases_for_gate2(self) -> List[Tuple[str, Dict]]:
        """Get cases that passed Gate 1 but haven't passed Gate 2.

        These cases need Sonnet quick analysis to determine if they
        should proceed to timeline generation.

        Returns:
            List of (case_number, case_data) tuples
        """
        gate2_candidates = []

        for case_number, case in self.get_all_cases(include_closed=False).items():
            if case.get("gate1_passed") and not case.get("gate2_passed"):
                gate2_candidates.append((case_number, case))

        return gate2_candidates

    def update_sonnet_analysis(
        self,
        case_number: str,
        analysis: Dict,
        criticality_score: float
    ) -> bool:
        """Update case with Sonnet quick analysis results.

        Gate 2 Check: Determines if case should proceed to Gate 3 (timeline).
        Always caches the Sonnet analysis regardless of gate outcome.

        Args:
            case_number: The case number
            analysis: Sonnet quick analysis (priority, damage_frequency, etc.)
            criticality_score: Calculated criticality score

        Returns:
            True if Gate 2 threshold crossed (needs timeline generation)
        """
        case_number = normalize_case_number(case_number)
        case = self.get_cached_case(case_number)

        if not case:
            return False

        # Always cache the Sonnet analysis (even if gate fails)
        case["sonnet_analysis"] = {
            **analysis,
            "last_analyzed": datetime.now().isoformat()
        }
        case["criticality_score"] = criticality_score
        case["last_updated"] = datetime.now().isoformat()

        # Check Gate 2 threshold
        passes_gate2 = criticality_score >= GATE2_CRITICALITY_THRESHOLD

        if passes_gate2 and not case.get("gate2_passed"):
            case["gate2_passed"] = True
            case["gate2_passed_date"] = datetime.now().isoformat()
            return True  # Needs timeline generation

        return False

    def get_cases_for_gate3(self) -> List[Tuple[str, Dict]]:
        """Get cases that passed Gate 2 and need timeline work.

        Includes:
        - Cases with gate2_passed=True but no timeline
        - Cases with timeline that have new messages

        Returns:
            List of (case_number, case_data) tuples
        """
        gate3_candidates = []

        for case_number, case in self.get_all_cases(include_closed=False).items():
            if not case.get("gate2_passed"):
                continue

            # Needs full timeline generation
            if not case.get("has_timeline"):
                gate3_candidates.append((case_number, case))
                continue

            # Has timeline - check for new messages to append
            timeline = case.get("timeline", {})
            last_timeline_date = timeline.get("last_entry_date")

            if last_timeline_date:
                # Check if any messages are newer than last timeline entry
                for msg in case.get("messages", []):
                    if msg.get("date"):
                        try:
                            msg_date = pd.to_datetime(msg["date"])
                            tl_date = pd.to_datetime(last_timeline_date)
                            if msg_date > tl_date:
                                gate3_candidates.append((case_number, case))
                                break
                        except:
                            pass

        return gate3_candidates

    def has_timeline(self, case_number: str) -> bool:
        """Check if a case has a timeline generated.

        Args:
            case_number: The case number

        Returns:
            True if timeline exists
        """
        case = self.get_cached_case(str(case_number))
        return case.get("has_timeline", False) if case else False

    def set_timeline(self, case_number: str, timeline: Dict) -> None:
        """Set the full timeline for a case.

        Args:
            case_number: The case number
            timeline: Timeline data (executive_summary, timeline_entries, etc.)
        """
        case_number = normalize_case_number(case_number)
        case = self.get_cached_case(case_number)

        if not case:
            return

        # Find the last entry date from timeline entries (check both key names for compatibility)
        last_entry_date = None
        entries = timeline.get("timeline_entries", timeline.get("entries", []))
        for entry in entries:
            entry_date = entry.get("date") or entry.get("entry_label", "")
            if entry_date:
                try:
                    date = pd.to_datetime(entry_date)
                    if last_entry_date is None or date > pd.to_datetime(last_entry_date):
                        last_entry_date = entry_date
                except:
                    pass

        # Normalize to use timeline_entries key for consistency
        normalized_timeline = {**timeline}
        if "entries" in normalized_timeline and "timeline_entries" not in normalized_timeline:
            normalized_timeline["timeline_entries"] = normalized_timeline.pop("entries")

        case["timeline"] = {
            **normalized_timeline,
            "created_date": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "last_entry_date": last_entry_date
        }
        case["has_timeline"] = True
        case["last_updated"] = datetime.now().isoformat()

    def append_timeline_entries(self, case_number: str, new_entries: List[Dict]) -> None:
        """Append new entries to an existing timeline.

        Args:
            case_number: The case number
            new_entries: List of new timeline entries to append
        """
        case_number = normalize_case_number(case_number)
        case = self.get_cached_case(case_number)

        if not case or not case.get("timeline"):
            return

        timeline = case["timeline"]
        # Use timeline_entries key for consistency (check both for compatibility)
        existing_entries = timeline.get("timeline_entries", timeline.get("entries", []))

        # Append new entries
        existing_entries.extend(new_entries)

        # Sort by date
        existing_entries.sort(key=lambda x: x.get("date", ""), reverse=False)

        # Update timeline (use timeline_entries key for consistency)
        timeline["timeline_entries"] = existing_entries
        if "entries" in timeline:
            del timeline["entries"]  # Remove old key if present
        timeline["last_updated"] = datetime.now().isoformat()

        # Update last entry date
        if new_entries:
            for entry in new_entries:
                entry_date = entry.get("date")
                if entry_date:
                    current_last = timeline.get("last_entry_date")
                    if not current_last or entry_date > current_last:
                        timeline["last_entry_date"] = entry_date

        case["last_updated"] = datetime.now().isoformat()

    def get_new_messages_for_timeline(self, case_number: str) -> List[Dict]:
        """Get messages newer than the last timeline entry.

        Used for appending to existing timelines.

        Args:
            case_number: The case number

        Returns:
            List of messages not yet in timeline
        """
        case_number = normalize_case_number(case_number)
        case = self.get_cached_case(case_number)

        if not case:
            return []

        timeline = case.get("timeline", {})
        last_entry_date = timeline.get("last_entry_date")

        if not last_entry_date:
            # No timeline yet - return all messages
            return case.get("messages", [])

        new_messages = []
        for msg in case.get("messages", []):
            if msg.get("date"):
                try:
                    msg_date = pd.to_datetime(msg["date"])
                    tl_date = pd.to_datetime(last_entry_date)
                    if msg_date > tl_date:
                        new_messages.append(msg)
                except:
                    pass

        return new_messages

    def reset_gates(self, case_number: str) -> None:
        """Reset gate status for a case (for re-analysis).

        Args:
            case_number: The case number
        """
        case_number = normalize_case_number(case_number)
        case = self.get_cached_case(case_number)

        if case:
            case["gate1_passed"] = False
            case["gate1_passed_date"] = None
            case["gate2_passed"] = False
            case["gate2_passed_date"] = None
            case["criticality_score"] = 0
            case["sonnet_analysis"] = None
            case["has_timeline"] = False
            case["timeline"] = None
            case["last_updated"] = datetime.now().isoformat()

    def get_cache_diagnostics(self) -> Dict:
        """Return diagnostic info about cache state.

        Useful for debugging duplicate case numbers and missing data.

        Returns:
            Dictionary with diagnostic information
        """
        cases = self.cache.get("cases", {})

        # Check for duplicate patterns (shouldn't happen after migration)
        normalized_keys = {}
        duplicates = []
        for key in cases.keys():
            norm = normalize_case_number(key)
            if norm in normalized_keys:
                duplicates.append((key, normalized_keys[norm]))
            normalized_keys[norm] = key

        # Check for missing critical fields
        missing_message_dates = []
        missing_frustration = []
        for case_num, case in cases.items():
            if not case.get("messages"):
                missing_message_dates.append(case_num)
            if not case.get("claude_analysis"):
                missing_frustration.append(case_num)

        return {
            "total_cases": len(cases),
            "duplicate_case_numbers": duplicates,
            "cases_without_messages": missing_message_dates,
            "cases_without_analysis": missing_frustration,
            "cache_file": self.cache_file
        }
