"""Dashboard module for Customer Sentiment Analyzer."""
from .branding import (
    COLORS,
    get_health_color,
    get_health_status,
    get_priority_color,
    get_frustration_color,
    get_severity_color,
)
from .styles import get_global_css, apply_plotly_theme

__all__ = [
    "COLORS",
    "get_health_color",
    "get_health_status",
    "get_priority_color",
    "get_frustration_color",
    "get_severity_color",
    "get_global_css",
    "apply_plotly_theme",
]
