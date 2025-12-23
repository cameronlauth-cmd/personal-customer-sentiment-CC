"""Source package for Customer Sentiment Analyzer."""
from .claude_client import ClaudeClient
from .data_loader import DataLoader, build_enhanced_message_history
from .scoring import (
    calculate_criticality_score,
    add_quick_score_bonus,
    add_timeline_bonus,
    calculate_account_health_score,
    rank_cases,
    get_frustration_statistics,
)
from .sentiment_analyzer import SentimentAnalyzer
from .visualization import create_all_charts
from .report_generator import generate_html_report

__all__ = [
    "ClaudeClient",
    "DataLoader",
    "build_enhanced_message_history",
    "calculate_criticality_score",
    "add_quick_score_bonus",
    "add_timeline_bonus",
    "calculate_account_health_score",
    "rank_cases",
    "get_frustration_statistics",
    "SentimentAnalyzer",
    "create_all_charts",
    "generate_html_report",
]
