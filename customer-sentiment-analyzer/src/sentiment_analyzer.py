"""
Main sentiment analysis orchestration.
Implements the three-stage hybrid analysis pipeline:
- Stage 1: Claude Haiku for all cases
- Stage 2A: Claude Sonnet quick scoring for top 25
- Stage 2B: Claude Sonnet detailed timeline for top 10
"""

import time
from typing import Callable, Dict, List, Optional, Tuple
from datetime import datetime
import pandas as pd

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import TOP_QUICK_SCORE, TOP_DETAILED, TRUENAS_CONTEXT
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
        top_detailed: int = TOP_DETAILED
    ) -> Dict:
        """Run the full three-stage analysis pipeline.

        Args:
            file: Excel file (path, bytes, or file object)
            top_quick: Number of cases for Stage 2A quick scoring
            top_detailed: Number of cases for Stage 2B detailed timeline

        Returns:
            Complete analysis results dictionary
        """
        start_time = time.time()

        # Load data
        self._update_progress("Loading Excel data...", 0.05)
        df, current_date = self.loader.load_excel(file)

        total_cases = len(df["Case Number"].unique())
        self._update_progress(f"Loaded {total_cases} cases", 0.10)

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
        }

        start_time = time.time()

        for idx, case_num in enumerate(unique_cases, 1):
            # Progress update every 5 cases
            if idx % 5 == 0 or idx == 1:
                progress = 0.15 + (0.35 * idx / total_cases)
                self._update_progress(
                    f"[{idx}/{total_cases}] Analyzing case {case_num}...",
                    progress
                )

            # Get case data
            case_data = self.loader.get_case_data(df, case_num)
            if not case_data:
                continue

            # Prepare messages for API
            messages_json = self.loader.prepare_messages_for_analysis(case_data)

            # Run Haiku analysis
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
