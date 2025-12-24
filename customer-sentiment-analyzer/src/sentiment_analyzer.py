"""
Main sentiment analysis orchestration.
Implements the three-gate hybrid analysis pipeline:
- Gate 1: Claude Haiku for all cases (triggers on Avg ≥ 3 OR Peak ≥ 6)
- Gate 2: Claude Sonnet quick scoring (triggers on Criticality ≥ 175)
- Gate 3: Claude Sonnet detailed timeline (persists until closure)

Legacy mode (no cache): Uses top-N selection instead of gate thresholds.
"""

import time
from typing import Callable, Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    TOP_QUICK_SCORE, TOP_DETAILED, TRUENAS_CONTEXT,
    GATE1_AVG_THRESHOLD, GATE1_PEAK_THRESHOLD, GATE2_CRITICALITY_THRESHOLD,
    normalize_case_number
)
from .claude_client import ClaudeClient
from .data_loader import DataLoader
from .scoring import (
    calculate_criticality_score,
    add_quick_score_bonus,
    add_timeline_bonus,
    rank_cases,
    get_frustration_statistics,
    get_issue_statistics,
    get_severity_distribution,
    get_support_level_distribution,
    calculate_account_health_score,
)


class SentimentAnalyzer:
    """Orchestrates the three-stage sentiment analysis pipeline."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ):
        """Initialize the analyzer.

        Args:
            api_key: Optional Anthropic API key
            progress_callback: Optional callback for progress updates
                               Function signature: (message: str, progress: float)
        """
        self.client = ClaudeClient(api_key)
        self.loader = DataLoader()
        self.progress_callback = progress_callback
        self.analysis_context = TRUENAS_CONTEXT

    def _update_progress(self, message: str, progress: float = 0):
        """Send progress update if callback is set."""
        if self.progress_callback:
            self.progress_callback(message, progress)

    def analyze(
        self,
        file,
        top_quick: int = TOP_QUICK_SCORE,
        top_detailed: int = TOP_DETAILED,
        cache=None,
        incremental: bool = False
    ) -> Dict:
        """Run the analysis pipeline.

        Uses three-gate architecture when cache is provided:
        - Gate 1: Haiku scores all new messages, triggers on Avg ≥ 3 OR Peak ≥ 6
        - Gate 2: Sonnet quick scores Gate 1 cases, triggers on Criticality ≥ 175
        - Gate 3: Sonnet generates/appends timeline for Gate 2 cases

        Falls back to top-N selection when no cache is provided.

        Args:
            file: Excel file (path, bytes, or file object)
            top_quick: Number of cases for Stage 2A (used in legacy mode)
            top_detailed: Number of cases for Stage 2B (used in legacy mode)
            cache: Optional AnalysisCache instance for gate-based analysis
            incremental: If True, only analyze new messages for cached cases

        Returns:
            Complete analysis results dictionary
        """
        start_time = time.time()
        self.cache = cache
        self.incremental = incremental

        # Load data
        self._update_progress("Loading Excel data...", 0.05)
        df, current_date = self.loader.load_excel(file)

        total_cases = len(df["Case Number"].unique())
        self._update_progress(f"Loaded {total_cases} cases", 0.10)

        # Use gate-based flow if cache is provided
        use_gates = cache is not None

        if use_gates:
            return self._analyze_with_gates(
                df, current_date, start_time, top_quick, top_detailed
            )
        else:
            return self._analyze_legacy(
                df, current_date, start_time, top_quick, top_detailed
            )

    def _analyze_with_gates(
        self,
        df: pd.DataFrame,
        current_date: str,
        start_time: float,
        top_quick: int,
        top_detailed: int
    ) -> Dict:
        """Run the three-gate architecture analysis.

        Args:
            df: Prepared DataFrame
            current_date: Current date string
            start_time: Analysis start time
            top_quick: Max cases for Gate 2 (safety limit)
            top_detailed: Max cases for Gate 3 (safety limit)

        Returns:
            Complete analysis results dictionary
        """
        # GATE 1: Claude Haiku analysis - score all new messages
        self._update_progress("Gate 1: Scoring new messages (Haiku)...", 0.15)
        cases, haiku_stats, haiku_time, gate2_triggers = self._run_gate_1(df)

        # Calculate initial criticality scores for all cases
        self._update_progress("Calculating criticality scores...", 0.50)
        cases = [calculate_criticality_score(c) for c in cases]
        cases = rank_cases(cases)

        # Sync gate flags in cache for ALL cases based on calculated values
        # This ensures cached cases (no new messages) still get properly flagged
        for case in cases:
            case_num = case.get("case_number")
            claude_analysis = case.get("claude_analysis", {})
            frustration = claude_analysis.get("frustration_score", 0)
            criticality = case.get("criticality_score", 0)

            cached = self.cache.get_cached_case(case_num)
            if cached:
                # Set Gate 1 if frustration qualifies (avg >= 3 OR peak >= 5)
                if not cached.get("gate1_passed"):
                    avg = cached.get("avg_frustration", frustration)
                    peak = cached.get("peak_frustration", frustration)
                    if avg >= GATE1_AVG_THRESHOLD or peak >= GATE1_PEAK_THRESHOLD:
                        cached["gate1_passed"] = True
                        cached["gate1_passed_date"] = datetime.now().isoformat()

                # Update criticality score in cache
                cached["criticality_score"] = criticality

        # GATE 2: Sonnet quick analysis for cases that passed Gate 1
        gate2_candidates = self.cache.get_cases_for_gate2()
        gate2_count = len(gate2_candidates)

        # Safety limit to prevent runaway API costs
        gate2_limit = min(gate2_count, top_quick)
        self._update_progress(
            f"Gate 2: Quick scoring {gate2_limit} cases (Sonnet)...", 0.55
        )
        quick_stats, quick_time = self._run_gate_2(cases, gate2_candidates[:gate2_limit])

        # Re-rank after quick scoring
        cases = rank_cases(cases)

        # GATE 3: Timeline generation for cases that passed Gate 2
        gate3_candidates = self.cache.get_cases_for_gate3()
        gate3_count = len(gate3_candidates)

        # Safety limit
        gate3_limit = min(gate3_count, top_detailed)
        self._update_progress(
            f"Gate 3: Timeline generation for {gate3_limit} cases (Sonnet)...", 0.70
        )
        detailed_stats, detailed_time = self._run_gate_3(cases, gate3_candidates[:gate3_limit])

        # Update cache with full case data for all cases (enables Load Dashboard)
        for case in cases:
            self.cache.update_case_full_data(case.get("case_number"), case)

        total_time = time.time() - start_time
        self._update_progress("Analysis complete!", 1.0)

        # Compile statistics
        severity_dist = get_severity_distribution(cases)
        support_dist = get_support_level_distribution(cases)
        issue_stats = get_issue_statistics(cases)
        frustration_stats = get_frustration_statistics(cases)

        # Calculate account health score
        health_score, health_breakdown = calculate_account_health_score(
            cases, frustration_stats
        )

        return {
            "cases": cases,
            "current_date": current_date,
            "total_cases": len(cases),
            "source": "gate_analysis",
            "account_health_score": health_score,
            "health_breakdown": health_breakdown,
            "gate_stats": {
                "gate1_triggers": gate2_triggers,
                "gate2_candidates": gate2_count,
                "gate2_processed": gate2_limit,
                "gate3_candidates": gate3_count,
                "gate3_processed": gate3_limit,
            },
            "statistics": {
                "haiku": haiku_stats,
                "frustration": frustration_stats,
                "quick_scoring": {
                    "total_scored": quick_stats.get("total_scored", 0),
                    "api_errors": quick_stats.get("api_errors", 0),
                    "time_seconds": quick_time,
                },
                "detailed_timeline": {
                    "total_analyzed": detailed_stats.get("total_analyzed", 0),
                    "api_errors": detailed_stats.get("api_errors", 0),
                    "time_seconds": detailed_time,
                },
            },
            "distributions": {
                "severity": severity_dist,
                "support_level": support_dist,
                "issue_classes": issue_stats.get("issue_classes", {}),
                "resolution_outlooks": issue_stats.get("resolution_outlooks", {}),
            },
            "timing": {
                "haiku_time": haiku_time,
                "quick_time": quick_time,
                "detailed_time": detailed_time,
                "total_time": total_time,
            },
        }

    def _analyze_legacy(
        self,
        df: pd.DataFrame,
        current_date: str,
        start_time: float,
        top_quick: int,
        top_detailed: int
    ) -> Dict:
        """Run the legacy top-N analysis (when no cache provided).

        Args:
            df: Prepared DataFrame
            current_date: Current date string
            start_time: Analysis start time
            top_quick: Number of cases for Stage 2A
            top_detailed: Number of cases for Stage 2B

        Returns:
            Complete analysis results dictionary
        """
        # Stage 1: Claude Haiku analysis
        self._update_progress("Stage 1: Claude Haiku analysis...", 0.15)
        cases, haiku_stats, haiku_time = self._run_stage_1(df)

        # Calculate initial criticality scores
        self._update_progress("Calculating criticality scores...", 0.50)
        cases = [calculate_criticality_score(c) for c in cases]
        cases = rank_cases(cases)

        # Stage 2A: Quick scoring
        self._update_progress(f"Stage 2A: Scoring top {min(top_quick, len(cases))} cases...", 0.55)
        quick_stats, quick_time = self._run_stage_2a(cases, top_quick)

        # Re-rank after quick scoring
        cases = rank_cases(cases)

        # Stage 2B: Detailed timeline
        self._update_progress(f"Stage 2B: Deep analysis of top {min(top_detailed, len(cases))} cases...", 0.70)
        detailed_stats, detailed_time = self._run_stage_2b(cases, top_detailed)

        total_time = time.time() - start_time
        self._update_progress("Analysis complete!", 1.0)

        # Compile statistics
        severity_dist = get_severity_distribution(cases)
        support_dist = get_support_level_distribution(cases)
        issue_stats = get_issue_statistics(cases)
        frustration_stats = get_frustration_statistics(cases)

        # Calculate account health score
        health_score, health_breakdown = calculate_account_health_score(
            cases, frustration_stats
        )

        return {
            "cases": cases,
            "current_date": current_date,
            "total_cases": len(cases),
            "source": "full_analysis",
            "account_health_score": health_score,
            "health_breakdown": health_breakdown,
            "statistics": {
                "haiku": haiku_stats,
                "frustration": frustration_stats,
                "quick_scoring": {
                    "total_scored": quick_stats.get("total_scored", 0),
                    "api_errors": quick_stats.get("api_errors", 0),
                    "time_seconds": quick_time,
                },
                "detailed_timeline": {
                    "total_analyzed": detailed_stats.get("total_analyzed", 0),
                    "api_errors": detailed_stats.get("api_errors", 0),
                    "time_seconds": detailed_time,
                },
            },
            "distributions": {
                "severity": severity_dist,
                "support_level": support_dist,
                "issue_classes": issue_stats.get("issue_classes", {}),
                "resolution_outlooks": issue_stats.get("resolution_outlooks", {}),
            },
            "timing": {
                "haiku_time": haiku_time,
                "quick_time": quick_time,
                "detailed_time": detailed_time,
                "total_time": total_time,
            },
        }

    def _run_stage_1(self, df: pd.DataFrame) -> Tuple[List[Dict], Dict, float]:
        """Run Stage 1: Claude Haiku analysis on all cases.

        Supports incremental analysis when cache is provided.

        Args:
            df: Prepared DataFrame

        Returns:
            Tuple of (cases list, statistics dict, time in seconds)
        """
        unique_cases = self.loader.get_unique_cases(df)
        total_cases = len(unique_cases)

        cases = []
        stats = {
            "total_analyzed": 0,
            "high_frustration": 0,
            "medium_frustration": 0,
            "low_frustration": 0,
            "no_frustration": 0,
            "total_frustration_score": 0,
            "api_errors": 0,
            "total_messages_analyzed": 0,
            "frustrated_messages_count": 0,
            "cached_cases": 0,
            "incremental_cases": 0,
            "new_cases": 0,
        }

        start_time = time.time()

        for idx, case_num in enumerate(unique_cases, 1):
            # Progress update every 5 cases
            if idx % 5 == 0 or idx == 1:
                progress = 0.15 + (0.35 * idx / total_cases)
                mode = "incremental" if self.incremental else "full"
                self._update_progress(
                    f"[{idx}/{total_cases}] Analyzing case {case_num} ({mode})...",
                    progress
                )

            # Get case data
            case_data = self.loader.get_case_data(df, case_num)
            if not case_data:
                continue

            # Check cache for incremental analysis
            cached_case = None
            if self.cache and self.incremental:
                cached_case = self.cache.get_cached_case(case_num)

            if cached_case and self.incremental:
                # Incremental mode: check for new messages
                case_df = case_data.get("case_data")
                if case_df is not None and self.cache.has_new_messages(case_num, case_df):
                    # Has new messages - run incremental analysis
                    stats["incremental_cases"] += 1
                    analysis = self._analyze_incremental(case_num, case_data, cached_case)
                else:
                    # No new messages - use cached analysis
                    stats["cached_cases"] += 1
                    analysis = cached_case.get("claude_analysis", {
                        "analysis_successful": True,
                        "frustration_score": cached_case.get("metrics", {}).get("peak_frustration", 0),
                        "issue_class": "Unknown",
                        "resolution_outlook": "Unknown"
                    })
            else:
                # Full analysis - no cache or not incremental
                stats["new_cases"] += 1
                messages_json = self.loader.prepare_messages_for_analysis(case_data)

                analysis = self.client.analyze_case_messages(
                    case_number=case_data["case_number"],
                    customer_name=case_data["customer_name"],
                    support_level=case_data["support_level"],
                    case_age=case_data["case_age_days"],
                    interaction_count=case_data["interaction_count"],
                    severity=case_data["severity"],
                    messages_json=messages_json,
                    analysis_context=self.analysis_context
                )

                # Update cache with new analysis
                if self.cache and analysis.get("analysis_successful", False):
                    self._update_cache_from_analysis(case_num, case_data, analysis)

            # Update statistics
            if analysis.get("analysis_successful", False):
                stats["total_analyzed"] += 1
                score = analysis.get("frustration_score", 0)
                stats["total_frustration_score"] += score

                if score >= 7:
                    stats["high_frustration"] += 1
                elif score >= 4:
                    stats["medium_frustration"] += 1
                elif score >= 1:
                    stats["low_frustration"] += 1
                else:
                    stats["no_frustration"] += 1

                metrics = analysis.get("frustration_metrics", {})
                stats["total_messages_analyzed"] += metrics.get("total_messages", 0)
                stats["frustrated_messages_count"] += metrics.get("frustrated_message_count", 0)
            else:
                stats["api_errors"] += 1

            # Build case record
            case_record = {
                "case_number": case_data["case_number"],
                "customer_name": case_data["customer_name"],
                "severity": case_data["severity"],
                "support_level": case_data["support_level"],
                "created_date": case_data["created_date"],
                "last_modified_date": case_data["last_modified_date"],
                "status": case_data["status"],
                "case_age_days": case_data["case_age_days"],
                "interaction_count": case_data["interaction_count"],
                "customer_engagement_ratio": case_data["customer_engagement_ratio"],
                "issue_category": analysis.get("issue_class", "Unknown"),
                "claude_analysis": analysis,
                "deepseek_analysis": None,
                "messages_full": case_data["messages_full"],
                "case_data": case_data["case_data"],
            }
            cases.append(case_record)

        elapsed = time.time() - start_time
        stats["avg_frustration_score"] = (
            stats["total_frustration_score"] / stats["total_analyzed"]
            if stats["total_analyzed"] > 0 else 0
        )

        return cases, stats, elapsed

    def _analyze_incremental(self, case_num: str, case_data: Dict, cached_case: Dict) -> Dict:
        """Analyze only new messages for a cached case.

        Args:
            case_num: Case number
            case_data: Current case data from Excel
            cached_case: Cached case data

        Returns:
            Updated analysis dictionary
        """
        # Get context summary from cache
        context_summary = cached_case.get("context_summary", "")
        cached_messages = cached_case.get("messages", [])

        # Get new messages
        case_df = case_data.get("case_data")
        new_messages_df = self.cache.get_new_messages(case_num, case_df)

        if len(new_messages_df) == 0:
            # No new messages, return cached analysis
            return cached_case.get("claude_analysis", {"analysis_successful": True})

        # Prepare new messages for analysis
        new_case_data = {
            **case_data,
            "case_data": new_messages_df,
            "interaction_count": len(new_messages_df)
        }
        messages_json = self.loader.prepare_messages_for_analysis(new_case_data)

        # Run incremental analysis with context
        analysis = self.client.analyze_incremental(
            case_number=case_data["case_number"],
            customer_name=case_data["customer_name"],
            context_summary=context_summary,
            new_messages_json=messages_json,
            analysis_context=self.analysis_context
        )

        if analysis.get("analysis_successful", False):
            # Update cache with new messages
            self._update_cache_from_incremental(case_num, case_data, new_messages_df, analysis)

            # Merge with cached analysis for overall score
            cached_analysis = cached_case.get("claude_analysis", {})
            analysis["frustration_score"] = max(
                analysis.get("frustration_score", 0),
                cached_analysis.get("frustration_score", 0)
            )

        return analysis

    def _update_cache_from_analysis(self, case_num: str, case_data: Dict, analysis: Dict):
        """Update cache after full analysis.

        Args:
            case_num: Case number
            case_data: Case data from Excel
            analysis: Analysis results
        """
        if not self.cache:
            return

        # Extract message-level data for cache
        case_df = case_data.get("case_data")
        messages = []
        if case_df is not None:
            for _, row in case_df.iterrows():
                msg_date = row.get("Message Date")
                if pd.notna(msg_date):
                    messages.append({
                        "date": str(msg_date),
                        "frustration": analysis.get("frustration_score", 0),
                        "is_customer": True,  # Will be refined later
                        "summary": ""
                    })

        # Build cache entry
        cache_entry = {
            "customer_name": case_data.get("customer_name"),
            "severity": case_data.get("severity"),
            "support_level": case_data.get("support_level"),
            "status": case_data.get("status", "Open"),
            "last_message_date": str(case_data.get("last_modified_date", "")),
            "messages": messages,
            "context_summary": analysis.get("summary", ""),
            "claude_analysis": analysis
        }

        self.cache.update_case(case_num, cache_entry)
        self.cache.update_case_metrics(case_num)

    def _update_cache_from_incremental(self, case_num: str, case_data: Dict,
                                        new_messages_df: pd.DataFrame, analysis: Dict):
        """Update cache after incremental analysis.

        Args:
            case_num: Case number
            case_data: Case data from Excel
            new_messages_df: DataFrame of new messages
            analysis: Incremental analysis results
        """
        if not self.cache:
            return

        # Add new message entries to cache
        for _, row in new_messages_df.iterrows():
            msg_date = row.get("Message Date")
            if pd.notna(msg_date):
                self.cache.add_message_analysis(case_num, {
                    "date": str(msg_date),
                    "frustration": analysis.get("frustration_score", 0),
                    "is_customer": True,
                    "summary": analysis.get("new_message_summary", "")
                })

        # Update context summary if provided
        if analysis.get("updated_context_summary"):
            self.cache.update_context_summary(case_num, analysis["updated_context_summary"])

        # Recalculate metrics
        self.cache.update_case_metrics(case_num)

    def _run_stage_2a(
        self,
        cases: List[Dict],
        top_n: int
    ) -> Tuple[Dict, float]:
        """Run Stage 2A: Quick scoring on top cases.

        Args:
            cases: Ranked list of cases
            top_n: Number of cases to score

        Returns:
            Tuple of (statistics dict, time in seconds)
        """
        top_cases = cases[:min(top_n, len(cases))]
        total = len(top_cases)

        stats = {
            "total_scored": 0,
            "api_errors": 0,
        }

        start_time = time.time()

        for idx, case in enumerate(top_cases, 1):
            progress = 0.55 + (0.15 * idx / total)
            self._update_progress(
                f"[{idx}/{total}] Quick scoring case {case['case_number']}...",
                progress
            )

            scoring = self.client.quick_score(case, self.analysis_context)

            if scoring.get("analysis_successful", False):
                add_quick_score_bonus(case, scoring)
                stats["total_scored"] += 1
            else:
                case["deepseek_quick_scoring"] = scoring
                stats["api_errors"] += 1

            # Small delay to avoid rate limiting
            if idx % 5 == 0:
                time.sleep(0.3)

        return stats, time.time() - start_time

    def _run_stage_2b(
        self,
        cases: List[Dict],
        top_n: int
    ) -> Tuple[Dict, float]:
        """Run Stage 2B: Detailed timeline on top cases.

        Args:
            cases: Ranked list of cases
            top_n: Number of cases for detailed analysis

        Returns:
            Tuple of (statistics dict, time in seconds)
        """
        top_cases = cases[:min(top_n, len(cases))]
        total = len(top_cases)

        stats = {
            "total_analyzed": 0,
            "api_errors": 0,
        }

        start_time = time.time()

        for idx, case in enumerate(top_cases, 1):
            progress = 0.70 + (0.25 * idx / total)
            self._update_progress(
                f"[{idx}/{total}] Deep analysis of case {case['case_number']}...",
                progress
            )

            case_data_df = case.get("case_data")
            analysis = self.client.deep_timeline(
                case,
                case_data=case_data_df,
                analysis_context=self.analysis_context
            )

            if analysis.get("analysis_successful", False):
                case["deepseek_analysis"] = analysis
                add_timeline_bonus(case, analysis)
                stats["total_analyzed"] += 1
            else:
                case["deepseek_analysis"] = analysis
                stats["api_errors"] += 1

            # Small delay to avoid rate limiting
            if idx % 3 == 0:
                time.sleep(0.5)

        return stats, time.time() - start_time

    def set_context(self, context: str):
        """Set custom analysis context.

        Args:
            context: Custom context string to use for analysis
        """
        self.analysis_context = context

    def test_connection(self) -> bool:
        """Test API connection.

        Returns:
            True if connection successful
        """
        return self.client.test_connection()

    # =========================================================================
    # THREE-GATE ARCHITECTURE METHODS
    # =========================================================================

    def _run_gate_1(self, df: pd.DataFrame) -> Tuple[List[Dict], Dict, float, int]:
        """Run Gate 1: Claude Haiku analysis on new messages.

        Scores new messages and updates running frustration metrics.
        Triggers Gate 2 when: Avg frustration >= 3 OR Peak frustration >= 6

        Args:
            df: Prepared DataFrame

        Returns:
            Tuple of (cases list, statistics dict, time in seconds, gate2 triggers count)
        """
        unique_cases = self.loader.get_unique_cases(df)
        total_cases = len(unique_cases)

        cases = []
        gate2_triggers = 0
        stats = {
            "total_analyzed": 0,
            "high_frustration": 0,
            "medium_frustration": 0,
            "low_frustration": 0,
            "no_frustration": 0,
            "total_frustration_score": 0,
            "api_errors": 0,
            "total_messages_analyzed": 0,
            "frustrated_messages_count": 0,
            "cached_cases": 0,
            "incremental_cases": 0,
            "new_cases": 0,
            "gate1_triggers": 0,
        }

        start_time = time.time()

        for idx, case_num in enumerate(unique_cases, 1):
            # Progress update every 5 cases
            if idx % 5 == 0 or idx == 1:
                progress = 0.15 + (0.35 * idx / total_cases)
                self._update_progress(
                    f"[{idx}/{total_cases}] Gate 1: Scoring case {case_num}...",
                    progress
                )

            # Get case data
            case_data = self.loader.get_case_data(df, case_num)
            if not case_data:
                continue

            # Check for new messages
            case_df = case_data.get("case_data")
            new_messages_df = self.cache.get_new_messages(case_num, case_df) if case_df is not None else case_df

            if new_messages_df is None or len(new_messages_df) == 0:
                # No new messages - use cached data
                stats["cached_cases"] += 1
                cached_case = self.cache.get_cached_case(case_num)
                if cached_case:
                    analysis = cached_case.get("claude_analysis", {
                        "analysis_successful": True,
                        "frustration_score": cached_case.get("avg_frustration", 0),
                        "issue_class": "Unknown",
                        "resolution_outlook": "Unknown"
                    })
                else:
                    # Shouldn't happen, but handle gracefully
                    messages_json = self.loader.prepare_messages_for_analysis(case_data)
                    analysis = self.client.analyze_case_messages(
                        case_number=case_data["case_number"],
                        customer_name=case_data["customer_name"],
                        support_level=case_data["support_level"],
                        case_age=case_data["case_age_days"],
                        interaction_count=case_data["interaction_count"],
                        severity=case_data["severity"],
                        messages_json=messages_json,
                        analysis_context=self.analysis_context
                    )
            else:
                # Has new messages - run Haiku analysis
                stats["new_cases"] += 1

                # Prepare new messages for analysis
                new_case_data = {
                    **case_data,
                    "case_data": new_messages_df,
                    "interaction_count": len(new_messages_df)
                }
                messages_json = self.loader.prepare_messages_for_analysis(new_case_data)

                analysis = self.client.analyze_case_messages(
                    case_number=case_data["case_number"],
                    customer_name=case_data["customer_name"],
                    support_level=case_data["support_level"],
                    case_age=case_data["case_age_days"],
                    interaction_count=len(new_messages_df),
                    severity=case_data["severity"],
                    messages_json=messages_json,
                    analysis_context=self.analysis_context
                )

                # Update cache with new scores
                if analysis.get("analysis_successful", False):
                    # Extract per-message scores
                    new_scores = []
                    for _, row in new_messages_df.iterrows():
                        msg_date = row.get("Message Date")
                        if pd.notna(msg_date):
                            new_scores.append({
                                "date": str(msg_date),
                                "frustration": analysis.get("frustration_score", 0),
                                "is_customer": True,  # Refined by message analysis
                            })

                    # Update cache and check if Gate 1 triggered
                    case_metadata = {
                        "customer_name": case_data.get("customer_name"),
                        "severity": case_data.get("severity"),
                        "support_level": case_data.get("support_level"),
                    }
                    triggered = self.cache.update_haiku_scores(
                        case_num, new_scores, case_metadata, claude_analysis=analysis
                    )
                    if triggered:
                        gate2_triggers += 1
                        stats["gate1_triggers"] += 1

            # Update statistics
            if analysis.get("analysis_successful", False):
                stats["total_analyzed"] += 1
                score = analysis.get("frustration_score", 0)
                stats["total_frustration_score"] += score

                if score >= 7:
                    stats["high_frustration"] += 1
                elif score >= 4:
                    stats["medium_frustration"] += 1
                elif score >= 1:
                    stats["low_frustration"] += 1
                else:
                    stats["no_frustration"] += 1

                metrics = analysis.get("frustration_metrics", {})
                stats["total_messages_analyzed"] += metrics.get("total_messages", 0)
                stats["frustrated_messages_count"] += metrics.get("frustrated_message_count", 0)
            else:
                stats["api_errors"] += 1

            # Build case record
            case_record = {
                "case_number": case_data["case_number"],
                "customer_name": case_data["customer_name"],
                "severity": case_data["severity"],
                "support_level": case_data["support_level"],
                "created_date": case_data["created_date"],
                "last_modified_date": case_data["last_modified_date"],
                "status": case_data["status"],
                "case_age_days": case_data["case_age_days"],
                "interaction_count": case_data["interaction_count"],
                "customer_engagement_ratio": case_data["customer_engagement_ratio"],
                "issue_category": analysis.get("issue_class", "Unknown"),
                "claude_analysis": analysis,
                "deepseek_analysis": None,
                "messages_full": case_data["messages_full"],
                "case_data": case_data["case_data"],
            }
            cases.append(case_record)

        elapsed = time.time() - start_time
        stats["avg_frustration_score"] = (
            stats["total_frustration_score"] / stats["total_analyzed"]
            if stats["total_analyzed"] > 0 else 0
        )

        return cases, stats, elapsed, gate2_triggers

    def _run_gate_2(
        self,
        cases: List[Dict],
        gate2_candidates: List[Tuple[str, Dict]]
    ) -> Tuple[Dict, float]:
        """Run Gate 2: Sonnet quick scoring on Gate 1 cases.

        Runs quick analysis and checks if criticality >= 175 to trigger Gate 3.

        Args:
            cases: Full list of cases (to update with analysis)
            gate2_candidates: List of (case_number, cached_case) tuples

        Returns:
            Tuple of (statistics dict, time in seconds)
        """
        total = len(gate2_candidates)

        stats = {
            "total_scored": 0,
            "api_errors": 0,
            "gate2_triggers": 0,
        }

        start_time = time.time()

        # Build lookup from cases list (normalize case numbers)
        case_lookup = {normalize_case_number(c["case_number"]): c for c in cases}

        for idx, (case_num, cached_case) in enumerate(gate2_candidates, 1):
            progress = 0.55 + (0.15 * idx / total) if total > 0 else 0.55
            self._update_progress(
                f"[{idx}/{total}] Gate 2: Quick scoring case {case_num}...",
                progress
            )

            # Find the case in our cases list (normalize case number)
            case = case_lookup.get(normalize_case_number(case_num))
            if not case:
                continue

            # Run Sonnet quick scoring
            scoring = self.client.quick_score(case, self.analysis_context)

            if scoring.get("analysis_successful", False):
                # Calculate criticality with the quick score bonus
                add_quick_score_bonus(case, scoring)
                criticality = case.get("criticality_score", 0)

                # Update cache with Sonnet analysis and check Gate 2
                triggered = self.cache.update_sonnet_analysis(
                    case_num, scoring, criticality
                )

                if triggered:
                    stats["gate2_triggers"] += 1

                stats["total_scored"] += 1
            else:
                case["deepseek_quick_scoring"] = scoring
                stats["api_errors"] += 1

            # Small delay to avoid rate limiting
            if idx % 5 == 0:
                time.sleep(0.3)

        return stats, time.time() - start_time

    def _run_gate_3(
        self,
        cases: List[Dict],
        gate3_candidates: List[Tuple[str, Dict]]
    ) -> Tuple[Dict, float]:
        """Run Gate 3: Timeline generation for Gate 2 cases.

        Generates new timelines or appends to existing ones.

        Args:
            cases: Full list of cases (to update with analysis)
            gate3_candidates: List of (case_number, cached_case) tuples

        Returns:
            Tuple of (statistics dict, time in seconds)
        """
        total = len(gate3_candidates)

        stats = {
            "total_analyzed": 0,
            "new_timelines": 0,
            "appended_timelines": 0,
            "api_errors": 0,
        }

        start_time = time.time()

        # Build lookup from cases list (normalize case numbers)
        case_lookup = {normalize_case_number(c["case_number"]): c for c in cases}

        for idx, (case_num, cached_case) in enumerate(gate3_candidates, 1):
            progress = 0.70 + (0.25 * idx / total) if total > 0 else 0.70
            self._update_progress(
                f"[{idx}/{total}] Gate 3: Timeline for case {case_num}...",
                progress
            )

            # Find the case in our cases list (normalize case number)
            case = case_lookup.get(normalize_case_number(case_num))
            if not case:
                continue

            has_existing_timeline = self.cache.has_timeline(case_num)

            if not has_existing_timeline:
                # Generate full timeline
                case_data_df = case.get("case_data")
                analysis = self.client.deep_timeline(
                    case,
                    case_data=case_data_df,
                    analysis_context=self.analysis_context
                )

                if analysis.get("analysis_successful", False):
                    case["deepseek_analysis"] = analysis
                    add_timeline_bonus(case, analysis)

                    # Save timeline to cache (use timeline_entries key for dashboard compatibility)
                    self.cache.set_timeline(case_num, {
                        "executive_summary": analysis.get("executive_summary", ""),
                        "timeline_entries": analysis.get("timeline_entries", []),
                        "pain_points": analysis.get("pain_points", ""),
                        "recommended_action": analysis.get("recommended_action", ""),
                        "sentiment_trend": analysis.get("sentiment_trend", ""),
                        "customer_priority": analysis.get("customer_priority", ""),
                        "critical_inflection_points": analysis.get("critical_inflection_points", ""),
                    })

                    stats["total_analyzed"] += 1
                    stats["new_timelines"] += 1
                else:
                    case["deepseek_analysis"] = analysis
                    stats["api_errors"] += 1
            else:
                # Append to existing timeline
                new_messages = self.cache.get_new_messages_for_timeline(case_num)

                if new_messages:
                    # Generate entries for new messages only
                    new_entries = self.client.generate_timeline_entries(
                        case,
                        new_messages,
                        self.analysis_context
                    )

                    if new_entries:
                        self.cache.append_timeline_entries(case_num, new_entries)
                        stats["appended_timelines"] += 1

                stats["total_analyzed"] += 1

                # Load existing timeline into case for display
                cached = self.cache.get_cached_case(case_num)
                if cached and cached.get("timeline"):
                    timeline = cached["timeline"]
                    # Map 'entries' key to 'timeline_entries' for dashboard compatibility
                    timeline_entries = timeline.get("entries", timeline.get("timeline_entries", []))
                    case["deepseek_analysis"] = {
                        "analysis_successful": True,
                        "timeline_entries": timeline_entries,
                        "executive_summary": timeline.get("executive_summary", ""),
                        "pain_points": timeline.get("pain_points", ""),
                        "recommended_action": timeline.get("recommended_action", ""),
                        "sentiment_trend": timeline.get("sentiment_trend", ""),
                        "customer_priority": timeline.get("customer_priority", ""),
                        "critical_inflection_points": timeline.get("critical_inflection_points", ""),
                    }

            # Small delay to avoid rate limiting
            if idx % 3 == 0:
                time.sleep(0.5)

        return stats, time.time() - start_time
