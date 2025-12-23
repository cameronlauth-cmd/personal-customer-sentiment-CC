"""
Dashboard filtering utilities for view mode switching.

Provides functions to filter cases between:
- Recent Issues: Cases with recent activity AND negative sentiment (triage view)
- All Cases: Complete portfolio (strategic review)

Supports both three-gate architecture (gate1_passed, gate2_passed) and
legacy mode (frustration-based filtering).
"""

from typing import List, Dict
from datetime import datetime, timedelta
from config.settings import RECENT_WINDOW_DAYS, FRUSTRATION_HIGH


def _is_within_window(date_str: str, window_days: int = RECENT_WINDOW_DAYS) -> bool:
    """Check if a date string is within the specified window of days.

    Args:
        date_str: ISO format date string
        window_days: Number of days for the window

    Returns:
        True if date is within window
    """
    if not date_str:
        return False

    try:
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        if date.tzinfo:
            date = date.replace(tzinfo=None)
        cutoff = datetime.now() - timedelta(days=window_days)
        return date >= cutoff
    except (ValueError, TypeError):
        return False


def filter_recent_issues(cases: List[Dict]) -> List[Dict]:
    """
    Filter to cases with recent activity AND negative sentiment.

    Uses three-gate architecture when available:
    - Cases with gate2_passed AND recent activity (timeline-tracked cases)
    - Cases with gate1_passed recently (newly escalating cases)

    Falls back to legacy filtering for cases without gate fields:
    - Recent activity (message within 14 days) + high frustration (≥7)
    - Negative sentiment trend keywords detected
    - Declining trend + high recent frustration

    Args:
        cases: List of case dictionaries from analysis results

    Returns:
        Filtered list of cases needing attention
    """
    recent_issues = []

    for case in cases:
        # Check for gate-based filtering (three-gate architecture)
        gate1_passed = case.get("gate1_passed", False)
        gate2_passed = case.get("gate2_passed", False)
        gate1_passed_date = case.get("gate1_passed_date")

        # Days since last message (from cache), fallback to case age if not available
        days_since_activity = case.get("days_since_last_message")
        if days_since_activity is None:
            days_since_activity = case.get("case_age_days", 0)

        has_recent_activity = days_since_activity is not None and days_since_activity <= RECENT_WINDOW_DAYS

        # GATE-BASED CONDITIONS (when gate fields are present)
        if gate1_passed or gate2_passed:
            # Condition A: Gate 2 passed (detailed analysis) + recent activity
            gate2_with_activity = gate2_passed and has_recent_activity

            # Condition B: Gate 1 passed recently (newly escalating)
            gate1_recent = gate1_passed and _is_within_window(gate1_passed_date)

            if gate2_with_activity or gate1_recent:
                recent_issues.append(case)
                continue

        # LEGACY FALLBACK CONDITIONS (for cases without gate tracking)
        claude = case.get("claude_analysis") or {}
        deepseek = case.get("deepseek_analysis") or {}

        # Extract metrics
        frustration = claude.get("frustration_score", 0)
        sentiment = (deepseek.get("sentiment_trend", "") or "").lower()
        recent_frust = case.get("recent_frustration_14d", 0)
        trend = case.get("trend", "stable")

        # Condition 1: Recent activity with high frustration
        recent_high_frustration = (
            has_recent_activity and
            frustration >= FRUSTRATION_HIGH
        )

        # Condition 2: Negative sentiment trend detected
        negative_keywords = ["negative", "worsening", "declining", "deteriorat"]
        has_negative_sentiment = any(word in sentiment for word in negative_keywords)

        # Condition 3: Declining trend with high recent frustration
        declining_with_frustration = (
            trend == "declining" and
            recent_frust >= FRUSTRATION_HIGH
        )

        # Include if any condition is met
        if recent_high_frustration or has_negative_sentiment or declining_with_frustration:
            recent_issues.append(case)

    return recent_issues


def get_filtered_cases(cases: List[Dict], view_mode: str) -> List[Dict]:
    """
    Apply view mode filter to cases.

    Args:
        cases: List of case dictionaries
        view_mode: "Recent Issues" or "All Cases"

    Returns:
        Filtered (or unfiltered) list of cases
    """
    if view_mode == "Recent Issues":
        return filter_recent_issues(cases)
    return cases  # "All Cases" returns everything


def get_view_mode_indicator_html(view_mode: str, case_count: int, colors: dict) -> str:
    """
    Generate HTML for the view mode indicator banner.

    Args:
        view_mode: Current view mode
        case_count: Number of cases in filtered view
        colors: Color dictionary from branding

    Returns:
        HTML string for the indicator, or empty string for "All Cases"
    """
    if view_mode != "Recent Issues":
        return ""

    return f"""
    <div style="background: #2d1f15; padding: 0.5rem 1rem; border-radius: 6px;
                border-left: 3px solid {colors.get('warning', '#ffc107')}; margin-bottom: 1rem;">
        <span style="color: {colors.get('warning', '#ffc107')};">&#9888; Showing Recent Issues Only</span>
        <span style="color: {colors.get('text_muted', '#8b949e')}; font-size: 0.85rem; margin-left: 0.5rem;">
            ({case_count} cases with activity in last {RECENT_WINDOW_DAYS} days + negative sentiment)
        </span>
    </div>
    """
