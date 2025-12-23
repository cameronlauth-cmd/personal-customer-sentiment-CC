"""
Branding and color system for Customer Sentiment Analyzer Dashboard.
Provides consistent colors, health score helpers, and styling utilities.
"""

# Color palette - Dark theme with accent colors
COLORS = {
    # Brand Colors
    "primary": "#0095D5",       # TrueNAS Blue
    "secondary": "#31BEEC",     # Light Blue
    "accent": "#71BF44",        # Green for CTAs

    # Dark Theme
    "background": "#0d1117",    # Page background
    "surface": "#161b22",       # Card backgrounds
    "surface_light": "#21262d", # Hover states
    "border": "#30363d",        # Borders

    # Text
    "text": "#FFFFFF",
    "text_muted": "#8b949e",

    # Status Colors
    "critical": "#dc3545",      # Red
    "warning": "#ffc107",       # Yellow/Orange
    "success": "#28a745",       # Green
    "info": "#0095D5",          # Blue
}

# Health score thresholds
HEALTH_THRESHOLDS = {
    "critical": 40,
    "at_risk": 60,
    "moderate": 80,
}


def get_health_color(score: float) -> str:
    """Get color based on health score.

    Args:
        score: Health score (0-100, higher = healthier)

    Returns:
        Hex color string
    """
    if score < HEALTH_THRESHOLDS["critical"]:
        return COLORS["critical"]
    elif score < HEALTH_THRESHOLDS["at_risk"]:
        return COLORS["warning"]
    elif score < HEALTH_THRESHOLDS["moderate"]:
        return COLORS["secondary"]
    else:
        return COLORS["success"]


def get_health_status(score: float) -> str:
    """Get status text based on health score.

    Args:
        score: Health score (0-100, higher = healthier)

    Returns:
        Status string
    """
    if score < HEALTH_THRESHOLDS["critical"]:
        return "Critical"
    elif score < HEALTH_THRESHOLDS["at_risk"]:
        return "At Risk"
    elif score < HEALTH_THRESHOLDS["moderate"]:
        return "Moderate"
    else:
        return "Healthy"


def get_priority_color(priority: str) -> str:
    """Get color for priority level.

    Args:
        priority: Priority string (Critical/High/Medium/Low)

    Returns:
        Hex color string
    """
    priority_colors = {
        "Critical": COLORS["critical"],
        "High": COLORS["warning"],
        "Medium": COLORS["secondary"],
        "Low": COLORS["success"],
    }
    return priority_colors.get(priority, COLORS["text_muted"])


def get_frustration_color(score: float) -> str:
    """Get color based on frustration score.

    Args:
        score: Frustration score (0-10, higher = more frustrated)

    Returns:
        Hex color string
    """
    if score >= 7:
        return COLORS["critical"]
    elif score >= 4:
        return COLORS["warning"]
    elif score >= 1:
        return COLORS["secondary"]
    else:
        return COLORS["success"]


def get_severity_color(severity: str) -> str:
    """Get color for severity level.

    Args:
        severity: Severity string (S1/S2/S3/S4)

    Returns:
        Hex color string
    """
    severity_colors = {
        "S1": COLORS["critical"],
        "S2": COLORS["warning"],
        "S3": COLORS["secondary"],
        "S4": COLORS["text_muted"],
    }
    return severity_colors.get(severity, COLORS["text_muted"])


def format_score_badge(score: float, max_score: float = 10) -> str:
    """Create an HTML badge for a score.

    Args:
        score: The score value
        max_score: Maximum possible score

    Returns:
        HTML string for badge
    """
    if max_score == 10:
        color = get_frustration_color(score)
    else:
        # Assume criticality score (0-250+)
        if score >= 180:
            color = COLORS["critical"]
        elif score >= 140:
            color = COLORS["warning"]
        elif score >= 100:
            color = COLORS["secondary"]
        else:
            color = COLORS["text_muted"]

    return f"""
    <span style="background-color: {color}; color: white; padding: 2px 8px;
                 border-radius: 4px; font-weight: bold; font-size: 0.9em;">
        {score:.1f}
    </span>
    """


def create_header(title: str, subtitle: str = "") -> str:
    """Create a branded header HTML.

    Args:
        title: Main title text
        subtitle: Optional subtitle text

    Returns:
        HTML string for header
    """
    subtitle_html = f'<p style="color: {COLORS["text_muted"]}; margin: 5px 0 0 0;">{subtitle}</p>' if subtitle else ""

    return f"""
    <div style="background: linear-gradient(135deg, {COLORS["surface"]} 0%, {COLORS["background"]} 100%);
                padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;
                border: 1px solid {COLORS["border"]}; border-left: 4px solid {COLORS["primary"]};">
        <h1 style="color: {COLORS["primary"]}; margin: 0; font-size: 1.8rem;">{title}</h1>
        {subtitle_html}
    </div>
    """


def create_metric_card(label: str, value: str, color: str = None) -> str:
    """Create a styled metric card HTML.

    Args:
        label: Metric label
        value: Metric value
        color: Optional accent color

    Returns:
        HTML string for metric card
    """
    accent = color or COLORS["primary"]

    return f"""
    <div style="background: {COLORS["surface"]}; padding: 1rem; border-radius: 8px;
                border: 1px solid {COLORS["border"]}; border-top: 3px solid {accent};">
        <p style="color: {COLORS["text_muted"]}; margin: 0; font-size: 0.85rem;">{label}</p>
        <p style="color: {COLORS["text"]}; margin: 5px 0 0 0; font-size: 1.5rem; font-weight: bold;">{value}</p>
    </div>
    """
