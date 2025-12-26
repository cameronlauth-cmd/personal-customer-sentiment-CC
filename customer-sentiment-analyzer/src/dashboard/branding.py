"""
Branding and color system for Customer Sentiment Analyzer Dashboard.
Provides consistent colors, health score helpers, and styling utilities.
"""

# Color palette - TrueNAS brand colors with Apple-inspired light theme refinement
COLORS = {
    # TrueNAS Brand Colors (exact match from truenas.com)
    "primary": "#0095d5",       # TrueNAS cyan blue
    "secondary": "#31beef",     # Lighter cyan for secondary elements
    "accent": "#71bf44",        # TrueNAS green for CTAs/success

    # Light Theme - Apple-inspired with TrueNAS identity
    "background": "#ffffff",    # Pure white (Apple style)
    "surface": "#f5f5f7",       # Light gray cards (Apple)
    "surface_light": "#e8e8ed", # Hover states / tertiary surface
    "border": "#d2d2d7",        # Subtle borders (Apple light)

    # Text - Apple-style hierarchy for light mode
    "text": "#1d1d1f",          # Primary text (Apple near-black)
    "text_muted": "#6e6e73",    # Secondary text (Apple gray)

    # Status Colors - Apple light mode palette
    "critical": "#ff3b30",      # Apple red
    "warning": "#ff9500",       # Apple orange
    "success": "#71bf44",       # TrueNAS green
    "info": "#0095d5",          # TrueNAS blue

    # Gradient (for headers) - TrueNAS brand gradient
    "gradient": "linear-gradient(135deg, #0095d5 0%, #71bf44 100%)",

    # Light theme effects
    "glass": "rgba(255, 255, 255, 0.72)",
    "shadow": "0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.06)",

    # Additional colors
    "surface_elevated": "#ffffff",  # Cards and elevated elements
    "border_subtle": "#e5e5e7",     # Very subtle borders

    # Light theme tints (for status backgrounds)
    "critical_tint": "#fff5f5",     # Light red background
    "warning_tint": "#fff9e6",      # Light yellow/orange background
    "success_tint": "#f0fdf4",      # Light green background
    "cyan_tint": "#e6f7fc",         # Light cyan background
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
    """Create a branded header HTML with TrueNAS + Apple styling.

    Args:
        title: Main title text
        subtitle: Optional subtitle text

    Returns:
        HTML string for header
    """
    subtitle_html = f'<p style="color: {COLORS["text_muted"]}; margin: 12px 0 0 0; font-weight: 400; font-size: 0.95rem;">{subtitle}</p>' if subtitle else ""

    return f"""
    <div style="background: {COLORS["surface"]};
                padding: 2rem 2.5rem;
                border-radius: 16px;
                margin-bottom: 1.5rem;
                border: 1px solid {COLORS["border_subtle"]};
                box-shadow: {COLORS["shadow"]};
                position: relative;
                overflow: hidden;">
        <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px;
                    background: {COLORS["gradient"]};"></div>
        <h1 style="color: {COLORS["primary"]}; margin: 0; font-size: 1.75rem; font-weight: 600;
                   letter-spacing: -0.02em; line-height: 1.2;">{title}</h1>
        {subtitle_html}
    </div>
    """


def create_metric_card(label: str, value: str, color: str = None) -> str:
    """Create a styled metric card HTML with TrueNAS + Apple design.

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
                border-radius: 12px;
                border: 1px solid {COLORS["border_subtle"]};
                box-shadow: {COLORS["shadow"]};
                transition: all 0.3s cubic-bezier(0.4, 0, 0.6, 1);">
        <p style="color: {COLORS["text_muted"]}; margin: 0; font-size: 0.75rem;
                  font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em;">{label}</p>
        <p style="color: {accent}; margin: 8px 0 0 0; font-size: 1.625rem;
                  font-weight: 600; letter-spacing: -0.02em; line-height: 1.2;">{value}</p>
    </div>
    """
