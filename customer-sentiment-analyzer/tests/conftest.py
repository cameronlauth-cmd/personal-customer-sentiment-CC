"""
Shared pytest fixtures for Customer Sentiment Analyzer tests.
"""

import pytest


@pytest.fixture
def sample_case_data():
    """Sample case dictionary for testing."""
    return {
        "case_number": "00123456",
        "customer_name": "Acme Corp",
        "severity": "S2",
        "support_level": "Gold",
        "case_age_days": 45,
        "interaction_count": 12,
        "messages": [
            {"text": "System is running slow", "date": "2024-01-01", "sender": "customer"},
            {"text": "We are investigating", "date": "2024-01-02", "sender": "support"},
        ],
        "claude_analysis": {
            "frustration_score": 6,
            "issue_class": "Systemic",
            "resolution_outlook": "Manageable",
            "key_phrase": "System performance degradation",
        },
    }


@pytest.fixture
def sample_analysis_results(sample_case_data):
    """Sample analysis results structure."""
    return {
        "total_cases": 1,
        "cases": [sample_case_data],
        "account_health_score": 65,
        "statistics": {
            "haiku": {
                "avg_frustration_score": 6.0,
                "high_frustration": 0,
                "total_messages_analyzed": 2,
            }
        },
        "distributions": {
            "severity": {"S2": 1},
            "support_level": {"Gold": 1},
        },
        "timing": {
            "total_time": 5.2,
        },
    }


@pytest.fixture
def high_frustration_case():
    """Case with high frustration score for threshold testing."""
    return {
        "case_number": "00789012",
        "customer_name": "Frustrated Inc",
        "severity": "S1",
        "support_level": "Gold",
        "case_age_days": 90,
        "interaction_count": 25,
        "claude_analysis": {
            "frustration_score": 9,
            "issue_class": "Systemic",
            "resolution_outlook": "Challenging",
            "key_phrase": "This is unacceptable",
        },
    }
