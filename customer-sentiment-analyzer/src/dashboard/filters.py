"""
Dashboard filtering utilities for view mode switching.

ARCHITECTURE: This is the DISPLAY LAYER - pure UI filtering only.
Scoring decisions (gates, frustration, criticality) are made in the ANALYSIS LAYER.

Provides functions to filter cases between:
- Recent Issues: Cases with activity in last 14 days (triage view)
- All Cases: Complete portfolio (strategic review)

Key principle: Filter decides IF a case shows, not WHAT data shows.
If a case passes the filter, ALL its data is displayed (full history).
"""

from typing import List, Dict
from config.settings import RECENT_WINDOW_DAYS


def filter_recent_issues(cases: List[Dict]) -> List[Dict]:
    """
    Filter to cases with recent activity (last 14 days).

    This is a pure DISPLAY filter - it only checks recency.
    Scoring/analysis decisions are made in the analysis layer.

    If a case passes this filter, ALL its data is shown (not truncated).

    Args:
        cases: List of case dictionaries from analysis results

    Returns:
        Filtered list of cases with recent activity
    """
    recent_issues = []

    for case in cases:
        days_since = case.get("days_since_last_message")

        # Simple recency check - no scoring logic here
        if days_since is not None and days_since <= RECENT_WINDOW_DAYS:
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
            ({case_count} cases with activity in last {RECENT_WINDOW_DAYS} days)
        </span>
    </div>
    """


def diagnose_filter(cases: List[Dict]) -> List[Dict]:
    """
    Return diagnostic info for each case explaining filter decisions.

    Use in sidebar or debug page to understand filtering without re-analysis.

    Args:
        cases: List of case dictionaries

    Returns:
        List of diagnostic dicts with case_number, status, reason, and days_since_last_message
    """
    diagnostics = []
    for case in cases:
        case_num = case.get("case_number")
        days_since = case.get("days_since_last_message")

        # Simple recency-based decision (matches filter_recent_issues logic)
        if days_since is None:
            status = "EXCLUDED"
            reason = "No message date data available"
        elif days_since <= RECENT_WINDOW_DAYS:
            status = "INCLUDED"
            reason = f"Last message {days_since} days ago (within {RECENT_WINDOW_DAYS}d window)"
        else:
            status = "EXCLUDED"
            reason = f"Last message {days_since} days ago (outside {RECENT_WINDOW_DAYS}d window)"

        diagnostics.append({
            "case_number": case_num,
            "status": status,
            "reason": reason,
            "days_since_last_message": days_since
        })
    return diagnostics


def validate_cases_for_filtering(cases: List[Dict]) -> Dict:
    """
    Validate case data quality for filtering.

    Returns dict with issues found - useful for debugging data problems.

    Args:
        cases: List of case dictionaries

    Returns:
        Dictionary with validation issues
    """
    issues = {
        "missing_days_since_last_message": [],
        "suspicious_age_mismatch": [],
        "missing_frustration": [],
        "total_cases": len(cases)
    }

    for case in cases:
        case_num = case.get("case_number")
        days_since = case.get("days_since_last_message")
        case_age = case.get("case_age_days", 0)

        if days_since is None:
            issues["missing_days_since_last_message"].append(case_num)
        elif case_age > 0 and days_since > case_age + 7:
            # Last message older than case creation? Suspicious data
            issues["suspicious_age_mismatch"].append({
                "case": case_num,
                "days_since_msg": days_since,
                "case_age": case_age
            })

        if not case.get("claude_analysis"):
            issues["missing_frustration"].append(case_num)

    return issues
