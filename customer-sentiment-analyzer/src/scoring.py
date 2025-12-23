"""
Criticality scoring for Customer Sentiment Analysis.
Calculates case priority scores and account health metrics.
Uses three-component frustration formula with peak and percentage bonuses.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timedelta
from config.settings import (
    SEVERITY_WEIGHTS,
    ISSUE_CLASS_WEIGHTS,
    RESOLUTION_WEIGHTS,
    SUPPORT_LEVEL_WEIGHTS,
    get_volume_points,
    get_age_points,
    get_engagement_points,
    RECENT_WINDOW_DAYS,
    TREND_THRESHOLD,
)


def calculate_criticality_score(case: Dict) -> Dict:
    """
    Calculate the full criticality score for a case using hybrid scoring model.

    Scoring components:
    - Claude frustration: 0-100 pts (three-component formula)
      - Base points (0-50): From headline frustration score
      - Peak bonus (0-25): From highest individual message score
      - Percentage bonus (0-25): From % of frustrated messages
    - Severity: 5-35 pts
    - Issue class: 5-30 pts
    - Resolution outlook: 0-15 pts
    - Support level priority: 0-10 pts
    - Message volume: 5-30 pts (more = higher)
    - Case age: 0-10 pts
    - Engagement: 0-15 pts

    Args:
        case: Case dictionary with claude_analysis

    Returns:
        Updated case dictionary with scores
    """
    claude_analysis = case.get('claude_analysis', {})
    frustration_score = claude_analysis.get('frustration_score', 0)
    frustration_metrics = claude_analysis.get('frustration_metrics', {})

    # Component 1: Claude frustration - THREE-COMPONENT FORMULA
    # Base points from headline score (0-50 pts)
    if frustration_score >= 9:
        base_frust_pts = 50
    elif frustration_score >= 7:
        base_frust_pts = 35 + (frustration_score - 7) * 7.5
    elif frustration_score >= 5:
        base_frust_pts = 20 + (frustration_score - 5) * 7.5
    elif frustration_score >= 3:
        base_frust_pts = 10 + (frustration_score - 3) * 5
    else:
        base_frust_pts = frustration_score * 3.33

    # Peak frustration bonus (0-25 pts) - highest individual message score
    peak_score = frustration_metrics.get('peak_score', frustration_score)
    if peak_score >= 9:
        peak_bonus = 25
    elif peak_score >= 7:
        peak_bonus = 15 + (peak_score - 7) * 5
    elif peak_score >= 5:
        peak_bonus = 5 + (peak_score - 5) * 5
    else:
        peak_bonus = peak_score * 1

    # Frustrated message percentage bonus (0-25 pts)
    total_msgs = frustration_metrics.get('total_messages', 1)
    frustrated_count = frustration_metrics.get('frustrated_message_count', 0)
    frustrated_pct = (frustrated_count / max(1, total_msgs)) * 100

    if frustrated_pct >= 30:
        pct_bonus = 25
    elif frustrated_pct >= 20:
        pct_bonus = 15 + (frustrated_pct - 20) * 1
    elif frustrated_pct >= 10:
        pct_bonus = 5 + (frustrated_pct - 10) * 1
    else:
        pct_bonus = frustrated_pct * 0.5

    claude_points = base_frust_pts + peak_bonus + pct_bonus

    # Component 2: Severity (5-35 pts)
    severity = case.get("severity", "S4")
    severity_points = SEVERITY_WEIGHTS.get(severity, 5)

    # Component 3: Issue class (5-30 pts)
    issue_class = claude_analysis.get('issue_class', 'Unknown')
    issue_class_points = ISSUE_CLASS_WEIGHTS.get(issue_class, 10)

    # Component 4: Resolution outlook (0-15 pts)
    resolution = claude_analysis.get('resolution_outlook', 'Unknown')
    resolution_points = RESOLUTION_WEIGHTS.get(resolution, 5)

    # Component 5: Support level priority (0-10 pts)
    support_level = case.get("support_level", "Unknown")
    support_points = SUPPORT_LEVEL_WEIGHTS.get(support_level, 0)

    # Component 6: Message volume (5-30 pts)
    msg_count = case.get("interaction_count", 0)
    volume_points = get_volume_points(msg_count)

    # Component 7: Case age (0-10 pts)
    age = case.get("case_age_days", 0)
    age_points = get_age_points(age)

    # Component 8: Customer engagement (0-15 pts)
    engagement = case.get("customer_engagement_ratio", 0.5)
    engagement_points = get_engagement_points(engagement)

    # Calculate base score
    base_score = (
        claude_points +
        severity_points +
        issue_class_points +
        resolution_points +
        support_points +
        volume_points +
        age_points +
        engagement_points
    )

    # Store score breakdown
    case["initial_criticality_score"] = base_score
    case["score_breakdown"] = {
        "claude_frustration": round(claude_points, 1),
        "claude_frustration_base": round(base_frust_pts, 1),
        "claude_frustration_peak_bonus": round(peak_bonus, 1),
        "claude_frustration_pct_bonus": round(pct_bonus, 1),
        "technical_severity": severity_points,
        "issue_class": issue_class_points,
        "resolution_outlook": resolution_points,
        "support_level_priority": support_points,
        "interaction_volume": volume_points,
        "case_age": age_points,
        "customer_engagement": engagement_points,
        "base_score": round(base_score, 1),
    }
    case["criticality_score"] = base_score

    return case


def add_quick_score_bonus(case: Dict, quick_scoring: Dict) -> Dict:
    """
    Add bonus points from Stage 2A quick scoring.

    Formula: (frustration_rate * 100) + (damage_rate * 50) + priority_bonus

    Args:
        case: Case dictionary with initial scores
        quick_scoring: Quick scoring results from Sonnet

    Returns:
        Updated case dictionary
    """
    if not quick_scoring or not quick_scoring.get('analysis_successful'):
        return case

    frustration_rate = quick_scoring.get('frustration_frequency', 0) / 100
    damage_rate = quick_scoring.get('damage_frequency', 0) / 100

    # Calculate base score
    base_quick = (frustration_rate * 100) + (damage_rate * 50)

    # Priority bonus
    priority = quick_scoring.get('priority', 'Medium')
    priority_bonus = {
        'Critical': 20,
        'High': 10,
        'Medium': 5,
        'Low': 0
    }.get(priority, 0)

    quick_score_points = base_quick + priority_bonus

    # Update case
    case['deepseek_quick_scoring'] = quick_scoring
    case['score_breakdown']['deepseek_quick_score'] = round(quick_score_points, 1)
    case['score_breakdown']['deepseek_frustration_rate'] = round(frustration_rate * 100, 1)
    case['score_breakdown']['deepseek_damage_rate'] = round(damage_rate * 100, 1)
    case['score_breakdown']['deepseek_priority_bonus'] = priority_bonus
    case['criticality_score'] += quick_score_points

    return case


def add_timeline_bonus(case: Dict, timeline_analysis: Dict) -> Dict:
    """
    Add bonus points from Stage 2B timeline analysis.

    Bonus based on percentage of frustrated timeline entries.

    Args:
        case: Case dictionary with scores
        timeline_analysis: Timeline analysis results from Sonnet

    Returns:
        Updated case dictionary
    """
    if not timeline_analysis or not timeline_analysis.get('analysis_successful'):
        return case

    timeline_entries = timeline_analysis.get('timeline_entries', [])
    if not timeline_entries:
        return case

    # Count frustrated entries
    frustrated_count = sum(
        1 for entry in timeline_entries
        if 'yes' in str(entry.get('frustration_detected', '')).lower()
    )

    # Calculate bonus (max 10 pts)
    frustration_rate = frustrated_count / len(timeline_entries) * 100
    timeline_bonus = frustration_rate / 10

    # Update case
    case['deepseek_analysis'] = timeline_analysis
    case['score_breakdown']['deepseek_timeline'] = round(timeline_bonus, 1)
    case['score_breakdown']['timeline_frustrated_entries'] = frustrated_count
    case['score_breakdown']['timeline_total_entries'] = len(timeline_entries)
    case['criticality_score'] += timeline_bonus

    return case


def rank_cases(cases: List[Dict], key: str = "criticality_score") -> List[Dict]:
    """
    Sort cases by score in descending order.

    Args:
        cases: List of case dictionaries
        key: Score key to sort by

    Returns:
        Sorted list of cases
    """
    return sorted(cases, key=lambda x: x.get(key, 0), reverse=True)


def calculate_temporal_clustering_penalty(
    case_analysis: List[Dict],
    lookback_days: int = 60
) -> Tuple[float, Dict]:
    """
    Detect if multiple concerning cases are clustered in recent time.

    Returns:
        Tuple of (penalty_multiplier, clustering_info)
        - penalty_multiplier: 0.0 to 1.0 (0 = no penalty, 1 = full penalty)
        - clustering_info: dict with details for reporting
    """
    current_date = pd.Timestamp.now()
    cutoff_date = current_date - pd.Timedelta(days=lookback_days)

    # Find cases that are concerning AND recent
    scores = [c['criticality_score'] for c in case_analysis]
    if not scores:
        return 0.0, {'detected': False}

    threshold_80th = np.percentile(scores, 80)

    recent_concerning_cases = []
    for case in case_analysis:
        try:
            case_data = case.get('case_data')
            if case_data is not None and not case_data.empty:
                last_msg = case_data['Message Date'].max()
            else:
                last_msg = pd.to_datetime(case.get('last_modified_date', current_date))
        except:
            continue

        is_concerning = (
            case['criticality_score'] >= 140 and
            case['criticality_score'] >= threshold_80th
        )
        is_recent = last_msg >= cutoff_date

        if is_concerning and is_recent:
            recent_concerning_cases.append({
                'case_number': case['case_number'],
                'score': case['criticality_score'],
                'last_activity': last_msg,
                'days_ago': (current_date - last_msg).days
            })

    num_recent = len(recent_concerning_cases)

    if num_recent == 0:
        return 0.0, {'detected': False}

    elif num_recent == 1:
        penalty = 0.1
        description = "1 concerning case in last 60 days"

    elif num_recent == 2:
        dates = [c['last_activity'] for c in recent_concerning_cases[:2]]
        days_between = (max(dates) - min(dates)).days

        if days_between <= 14:
            penalty = 0.4
            description = f"2 concerning cases within {days_between} days - rapid deterioration"
        elif days_between <= 30:
            penalty = 0.25
            description = f"2 concerning cases within {days_between} days - concerning trend"
        else:
            penalty = 0.15
            description = f"2 concerning cases within {days_between} days - isolated incidents"

    else:  # num_recent >= 3
        dates = [c['last_activity'] for c in recent_concerning_cases[:3]]
        days_span = (max(dates) - min(dates)).days

        if days_span <= 14:
            penalty = 0.7
            description = f"{num_recent} concerning cases within {days_span} days - SEVERE deterioration"
        elif days_span <= 30:
            penalty = 0.5
            description = f"{num_recent} concerning cases within {days_span} days - major concern"
        else:
            penalty = 0.3
            description = f"{num_recent} concerning cases within {days_span} days - ongoing issues"

    return penalty, {
        'detected': True,
        'penalty_multiplier': penalty,
        'recent_case_count': num_recent,
        'cases': recent_concerning_cases,
        'description': description,
        'lookback_days': lookback_days
    }


def calculate_catastrophic_override_weight(case: Dict, current_date) -> float:
    """
    Calculate override weight based on recency of catastrophic case.

    Returns:
        Weight from 0.0 to 1.0
        - 1.0 = full override (0-3 months)
        - 0.5 = half override (3-6 months)
        - 0.25 = quarter override (6-12 months)
        - 0.0 = no override (>12 months)
    """
    try:
        case_data = case.get('case_data')
        if case_data is not None and not case_data.empty:
            msg_dates = case_data['Message Date'].dropna()
            if len(msg_dates) > 0:
                last_msg_date = msg_dates.max()
            else:
                last_msg_date = pd.to_datetime(case.get('last_modified_date', current_date))
        else:
            last_msg_date = pd.to_datetime(case.get('last_modified_date', current_date))
    except:
        last_msg_date = current_date

    days_ago = (current_date - last_msg_date).days

    if days_ago <= 90:
        return 1.0
    elif days_ago <= 180:
        return 0.5
    elif days_ago <= 365:
        return 0.25
    else:
        return 0.0


def calculate_account_health_score(
    case_analysis: List[Dict],
    claude_statistics: Dict
) -> Tuple[float, Dict]:
    """
    Calculate holistic account health score (0-100, higher = healthier).

    Components (max 100 points):
    1. Average Frustration Level (0-30 pts)
    2. High Frustration Cases (0-20 pts)
    3. Critical Case Load (0-20 pts)
    4. Systemic Issues (0-15 pts)
    5. Resolution Complexity (0-15 pts)

    Plus temporal clustering and catastrophic override penalties.

    Returns:
        Tuple of (health_score, score_breakdown_dict)
    """
    total_cases = len(case_analysis)

    if total_cases == 0:
        return 100.0, {
            'frustration_component': 30,
            'high_frustration_penalty': 20,
            'critical_load_component': 20,
            'systemic_issues_component': 15,
            'resolution_complexity_component': 15
        }

    # Component 1: Average Frustration (0-30 points)
    avg_frustration = claude_statistics.get('avg_frustration_score', 0)
    frustration_score = max(0, 30 - (avg_frustration * 3))

    # Component 2: High Frustration Cases (0-20 points)
    high_frustration_count = claude_statistics.get('high_frustration', 0)
    high_frustration_ratio = high_frustration_count / total_cases

    # Check for catastrophic cases (>=200)
    catastrophic_cases = [c for c in case_analysis if c.get('criticality_score', 0) >= 200]
    current_date = pd.Timestamp.now()

    if len(catastrophic_cases) > 0:
        override_weights = [
            calculate_catastrophic_override_weight(c, current_date)
            for c in catastrophic_cases
        ]
        max_override = max(override_weights)
        normal_score = max(0, 20 - (high_frustration_ratio * 100))
        high_frustration_score = normal_score * (1 - max_override)
    else:
        high_frustration_score = max(0, 20 - (high_frustration_ratio * 100))
        max_override = 0.0

    # Component 3: Critical Case Load (0-20 points)
    critical_count = len([c for c in case_analysis if c.get('criticality_score', 0) >= 180])
    critical_ratio = critical_count / total_cases

    if max_override > 0:
        normal_score = max(0, 20 - (critical_ratio * 100))
        critical_score = normal_score * (1 - max_override)
    else:
        critical_score = max(0, 20 - (critical_ratio * 100))

    # Component 4: Systemic Issues (0-15 points)
    systemic_count = len([
        c for c in case_analysis
        if c.get('claude_analysis', {}).get('issue_class') == 'Systemic'
    ])
    systemic_ratio = systemic_count / total_cases
    systemic_score = max(0, 15 - (systemic_ratio * 75))

    # Component 5: Challenging Resolutions (0-15 points)
    challenging_count = len([
        c for c in case_analysis
        if c.get('claude_analysis', {}).get('resolution_outlook') == 'Challenging'
    ])
    challenging_ratio = challenging_count / total_cases
    challenging_score = max(0, 15 - (challenging_ratio * 75))

    # Base health score
    base_health_score = (
        frustration_score +
        high_frustration_score +
        critical_score +
        systemic_score +
        challenging_score
    )
    base_health_score = max(0, min(100, base_health_score))

    # Apply temporal clustering penalty
    temporal_penalty, temporal_info = calculate_temporal_clustering_penalty(
        case_analysis, lookback_days=60
    )

    if temporal_penalty > 0:
        health_score = base_health_score * (1 - temporal_penalty)
        health_score = round(max(0, min(100, health_score)), 1)
    else:
        health_score = round(base_health_score, 1)

    return health_score, {
        'frustration_component': round(frustration_score, 1),
        'high_frustration_penalty': round(high_frustration_score, 1),
        'critical_load_component': round(critical_score, 1),
        'systemic_issues_component': round(systemic_score, 1),
        'resolution_complexity_component': round(challenging_score, 1),
        'catastrophic_override_applied': max_override > 0,
        'catastrophic_override_weight': round(max_override, 2),
        'catastrophic_case_count': len(catastrophic_cases),
        'base_health_score': round(base_health_score, 1),
        'temporal_clustering_penalty': round(temporal_penalty, 2),
        'temporal_clustering_info': temporal_info
    }


def get_frustration_statistics(cases: List[Dict]) -> Dict:
    """
    Calculate frustration statistics across all cases.

    Args:
        cases: List of analyzed cases

    Returns:
        Statistics dictionary
    """
    total_analyzed = 0
    high_frustration = 0
    medium_frustration = 0
    low_frustration = 0
    no_frustration = 0
    total_score = 0
    total_messages = 0
    frustrated_messages = 0

    for case in cases:
        claude = case.get('claude_analysis', {})
        if not claude.get('analysis_successful', False):
            continue

        total_analyzed += 1
        score = claude.get('frustration_score', 0)
        total_score += score

        if score >= 7:
            high_frustration += 1
        elif score >= 4:
            medium_frustration += 1
        elif score >= 1:
            low_frustration += 1
        else:
            no_frustration += 1

        metrics = claude.get('frustration_metrics', {})
        total_messages += metrics.get('total_messages', 0)
        frustrated_messages += metrics.get('frustrated_message_count', 0)

    avg_score = total_score / total_analyzed if total_analyzed > 0 else 0
    frustrated_pct = (frustrated_messages / total_messages * 100) if total_messages > 0 else 0

    return {
        "total_analyzed": total_analyzed,
        "high_frustration": high_frustration,
        "medium_frustration": medium_frustration,
        "low_frustration": low_frustration,
        "no_frustration": no_frustration,
        "avg_frustration_score": round(avg_score, 2),
        "total_frustration_score": total_score,
        "total_messages_analyzed": total_messages,
        "frustrated_messages_count": frustrated_messages,
        "frustrated_messages_pct": round(frustrated_pct, 1),
    }


def get_issue_statistics(cases: List[Dict]) -> Dict:
    """
    Calculate issue class and resolution statistics.

    Args:
        cases: List of analyzed cases

    Returns:
        Statistics dictionary
    """
    issue_counts = {}
    resolution_counts = {}

    for case in cases:
        claude = case.get('claude_analysis', {})

        issue = claude.get('issue_class', 'Unknown')
        issue_counts[issue] = issue_counts.get(issue, 0) + 1

        resolution = claude.get('resolution_outlook', 'Unknown')
        resolution_counts[resolution] = resolution_counts.get(resolution, 0) + 1

    return {
        "issue_classes": issue_counts,
        "resolution_outlooks": resolution_counts,
    }


def get_severity_distribution(cases: List[Dict]) -> Dict:
    """
    Calculate severity distribution across cases.

    Args:
        cases: List of cases

    Returns:
        Dictionary of severity counts
    """
    distribution = {}
    for case in cases:
        severity = case.get('severity', 'S4')
        distribution[severity] = distribution.get(severity, 0) + 1
    return distribution


def get_support_level_distribution(cases: List[Dict]) -> Dict:
    """
    Calculate support level distribution across cases.

    Args:
        cases: List of cases

    Returns:
        Dictionary of support level counts
    """
    distribution = {}
    for case in cases:
        level = case.get('support_level', 'Unknown')
        distribution[level] = distribution.get(level, 0) + 1
    return distribution


def calculate_recent_frustration(case: Dict, window_days: int = None) -> Dict:
    """
    Calculate recent vs historical frustration metrics for a case.

    Uses message dates to determine which messages are "recent" and
    calculates trend based on comparing recent to historical averages.

    Args:
        case: Case dictionary with case_data DataFrame
        window_days: Days to consider as "recent" (default from settings)

    Returns:
        Dictionary with recent frustration metrics
    """
    window_days = window_days or RECENT_WINDOW_DAYS
    cutoff = pd.Timestamp.now() - pd.Timedelta(days=window_days)

    case_df = case.get('case_data')
    if case_df is None or case_df.empty:
        return {
            'recent_frustration': 0,
            'historical_frustration': 0,
            'trend': 'stable',
            'has_recent_activity': False,
            'days_since_last_message': None
        }

    # Get frustration score from analysis
    claude_analysis = case.get('claude_analysis', {})
    base_frustration = claude_analysis.get('frustration_score', 0)
    metrics = claude_analysis.get('frustration_metrics', {})
    message_scores = metrics.get('message_scores', [])

    # Parse message dates
    try:
        case_df['Message Date'] = pd.to_datetime(case_df['Message Date'])
        recent_mask = case_df['Message Date'] >= cutoff
        recent_count = recent_mask.sum()
        total_count = len(case_df)
        historical_count = total_count - recent_count

        # Get most recent message date
        latest_date = case_df['Message Date'].max()
        days_since = (pd.Timestamp.now() - latest_date).days if pd.notna(latest_date) else None
    except:
        return {
            'recent_frustration': base_frustration,
            'historical_frustration': base_frustration,
            'trend': 'stable',
            'has_recent_activity': True,
            'days_since_last_message': None
        }

    # If we have individual message scores, use them for more accurate calculation
    if message_scores and len(message_scores) > 0:
        # Estimate which scores are recent vs historical based on position
        # (messages are typically in chronological order)
        total_scored = len(message_scores)
        recent_ratio = recent_count / total_count if total_count > 0 else 0

        # Estimate how many of the scored messages are "recent"
        recent_scored_count = max(1, int(total_scored * recent_ratio))

        # Recent scores are the last N scores
        recent_scores = [s.get('score', 0) for s in message_scores[-recent_scored_count:]]
        historical_scores = [s.get('score', 0) for s in message_scores[:-recent_scored_count]]

        recent_avg = np.mean(recent_scores) if recent_scores else 0
        historical_avg = np.mean(historical_scores) if historical_scores else recent_avg
    else:
        # Fallback: use overall frustration score for both
        recent_avg = base_frustration
        historical_avg = base_frustration

    # Determine trend
    if recent_count == 0:
        trend = 'stable'
    elif recent_avg > historical_avg + TREND_THRESHOLD:
        trend = 'declining'  # Higher frustration = relationship declining
    elif recent_avg < historical_avg - TREND_THRESHOLD:
        trend = 'improving'
    else:
        trend = 'stable'

    return {
        'recent_frustration': round(recent_avg, 1),
        'historical_frustration': round(historical_avg, 1),
        'trend': trend,
        'has_recent_activity': recent_count > 0,
        'days_since_last_message': days_since,
        'recent_message_count': int(recent_count),
        'total_message_count': int(total_count)
    }


def add_recent_metrics_to_cases(cases: List[Dict], window_days: int = None) -> List[Dict]:
    """
    Add recent frustration metrics to all cases.

    Args:
        cases: List of case dictionaries
        window_days: Days to consider as "recent"

    Returns:
        Updated list of cases with recent metrics
    """
    for case in cases:
        recent_metrics = calculate_recent_frustration(case, window_days)
        case['recent_metrics'] = recent_metrics

        # Add to score breakdown if present
        if 'score_breakdown' in case:
            case['score_breakdown']['recent_frustration'] = recent_metrics['recent_frustration']
            case['score_breakdown']['trend'] = recent_metrics['trend']

    return cases


def get_cases_by_trend(cases: List[Dict], trend: str = 'declining') -> List[Dict]:
    """
    Filter cases by their sentiment trend.

    Args:
        cases: List of case dictionaries with recent_metrics
        trend: Trend to filter by ('declining', 'stable', 'improving')

    Returns:
        Filtered list of cases
    """
    return [
        case for case in cases
        if case.get('recent_metrics', {}).get('trend') == trend
    ]


def get_cases_needing_attention(
    cases: List[Dict],
    min_recent_frustration: float = 7.0,
    include_declining: bool = True
) -> List[Dict]:
    """
    Get cases that need attention based on recent activity.

    Flags cases where:
    1. Recent frustration is high (>= min_recent_frustration)
    2. Trend is declining (if include_declining is True)
    3. Has recent activity

    Args:
        cases: List of case dictionaries
        min_recent_frustration: Minimum recent frustration to flag
        include_declining: Also include cases with declining trend

    Returns:
        List of cases needing attention, sorted by recent frustration
    """
    attention_cases = []

    for case in cases:
        metrics = case.get('recent_metrics', {})

        if not metrics.get('has_recent_activity', False):
            continue

        recent_frust = metrics.get('recent_frustration', 0)
        trend = metrics.get('trend', 'stable')

        needs_attention = (
            recent_frust >= min_recent_frustration or
            (include_declining and trend == 'declining')
        )

        if needs_attention:
            attention_cases.append(case)

    # Sort by recent frustration descending
    attention_cases.sort(
        key=lambda x: x.get('recent_metrics', {}).get('recent_frustration', 0),
        reverse=True
    )

    return attention_cases
