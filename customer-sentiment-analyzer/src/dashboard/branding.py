"""
Branding and color system for Customer Sentiment Analyzer Dashboard.
Provides consistent colors, health score helpers, and styling utilities.
"""

# Color palette - Enterprise dark theme with refined aesthetics
COLORS = {
    # Brand Colors - Professional blue spectrum
    "primary": "#3b82f6",       # Modern blue - more vibrant
    "secondary": "#60a5fa",     # Light blue for accents
    "accent": "#10b981",        # Emerald green for CTAs

    # Dark Theme - Sophisticated neutrals
    "background": "#0f172a",    # Slate 900 - deep navy
    "surface": "#1e293b",       # Slate 800 - card backgrounds
    "surface_light": "#334155", # Slate 700 - hover states
    "border": "#475569",        # Slate 600 - subtle borders

    # Text - High contrast hierarchy
    "text": "#f8fafc",          # Slate 50 - primary text
    "text_muted": "#94a3b8",    # Slate 400 - secondary text

    # Status Colors - Enterprise palette
    "critical": "#ef4444",      # Red 500 - errors/critical
    "warning": "#f59e0b",       # Amber 500 - warnings
    "success": "#10b981",       # Emerald 500 - success
    "info": "#3b82f6",          # Blue 500 - info

    # Gradient (for headers) - Subtle professional gradient
    "gradient": "linear-gradient(135deg, #3b82f6 0%, #10b981 100%)",

    # Glass effects - Modern frosted glass
    "glass": "rgba(30, 41, 59, 0.8)",  # Frosted glass effect base
    "shadow": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)",

    # Additional enterprise colors
    "surface_elevated": "#273548",  # Elevated surfaces
    "border_subtle": "#334155",     # Subtle borders
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
    """Create a branded header HTML with enterprise styling.

    Args:
        title: Main title text
        subtitle: Optional subtitle text

    Returns:
        HTML string for header
    """
    subtitle_html = f'<p style="color: {COLORS["text_muted"]}; margin: 10px 0 0 0; font-weight: 400; font-size: 0.95rem;">{subtitle}</p>' if subtitle else ""

    return f"""
    <div style="background: linear-gradient(180deg, {COLORS["surface"]} 0%, {COLORS["background"]} 100%);
                padding: 2rem 2.5rem;
                border-radius: 12px;
                margin-bottom: 1.5rem;
                border: 1px solid {COLORS["border_subtle"]};
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24);
                position: relative;">
        <div style="position: absolute; top: 0; left: 0; right: 0; height: 2px;
                    background: {COLORS["gradient"]}; border-radius: 12px 12px 0 0;"></div>
        <h1 style="color: {COLORS["primary"]}; margin: 0; font-size: 1.625rem; font-weight: 600;
                   letter-spacing: -0.025em; line-height: 1.2;">{title}</h1>
        {subtitle_html}
    </div>
    """


def create_metric_card(label: str, value: str, color: str = None) -> str:
    """Create a styled metric card HTML with enterprise design.

    Args:
        label: Metric label
        value: Metric value
        color: Optional accent color

    Returns:
        HTML string for metric card
    """
    accent = color or COLORS["primary"]

    return f"""
    <div style="background: {COLORS["surface"]};
                padding: 1.25rem 1.5rem;
                border-radius: 8px;
                border: 1px solid {COLORS["border_subtle"]};
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
                transition: border-color 0.15s ease, box-shadow 0.15s ease;">
        <p style="color: {COLORS["text_muted"]}; margin: 0; font-size: 0.75rem;
                  font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;">{label}</p>
        <p style="color: {accent}; margin: 6px 0 0 0; font-size: 1.5rem;
                  font-weight: 600; letter-spacing: -0.02em; line-height: 1.2;">{value}</p>
    </div>
    """
