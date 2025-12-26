"""
Plotly chart generation for sentiment analysis visualization.
Creates interactive charts for the HTML report and Streamlit display.
"""

from typing import Dict, List
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np

# Import central branding colors
from src.dashboard.branding import COLORS as BRAND_COLORS


# Color schemes - aligned with TrueNAS light theme
COLORS = {
    "frustration": {
        "high": BRAND_COLORS["critical"],     # Apple red #ff3b30
        "medium": BRAND_COLORS["warning"],    # Apple orange #ff9500
        "low": BRAND_COLORS["secondary"],     # TrueNAS lighter cyan #31beef
        "none": BRAND_COLORS["success"],      # TrueNAS green #71bf44
    },
    "severity": {
        "S1": BRAND_COLORS["critical"],       # Apple red
        "S2": BRAND_COLORS["warning"],        # Apple orange
        "S3": BRAND_COLORS["primary"],        # TrueNAS cyan
        "S4": BRAND_COLORS["success"],        # TrueNAS green
    },
    "support": {
        "Gold": "#FFD700",
        "Silver": "#C0C0C0",
        "Bronze": "#CD7F32",
        "Unknown": BRAND_COLORS["text_muted"],
    },
    "chart": {
        "primary": BRAND_COLORS["primary"],   # TrueNAS cyan #0095d5
        "secondary": BRAND_COLORS["accent"],  # TrueNAS green #71bf44
        "accent": BRAND_COLORS["warning"],    # Apple orange #ff9500
    }
}


def create_frustration_distribution_chart(statistics: Dict) -> go.Figure:
    """Create pie chart showing frustration level distribution.

    Args:
        statistics: Dictionary with frustration counts

    Returns:
        Plotly figure
    """
    labels = ['High (7-10)', 'Medium (4-6)', 'Low (1-3)', 'None (0)']
    values = [
        statistics.get("high_frustration", 0),
        statistics.get("medium_frustration", 0),
        statistics.get("low_frustration", 0),
        statistics.get("no_frustration", 0),
    ]
    colors = [
        COLORS["frustration"]["high"],
        COLORS["frustration"]["medium"],
        COLORS["frustration"]["low"],
        COLORS["frustration"]["none"],
    ]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker_colors=colors,
        textinfo='percent+value',
        textposition='outside',
        pull=[0.1, 0, 0, 0],  # Pull out high frustration slice
    )])

    fig.update_layout(
        title={
            'text': "Frustration Distribution",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 18, 'color': COLORS["chart"]["primary"]}
        },
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=80, b=80, l=40, r=40),
    )

    return fig


def create_severity_distribution_chart(distribution: Dict) -> go.Figure:
    """Create pie chart showing severity distribution.

    Args:
        distribution: Dictionary of severity -> count

    Returns:
        Plotly figure
    """
    labels = list(distribution.keys())
    values = list(distribution.values())
    colors = [COLORS["severity"].get(s, "#808080") for s in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker_colors=colors,
        textinfo='percent+label',
        textposition='inside',
    )])

    fig.update_layout(
        title={
            'text': "Severity Distribution",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 18, 'color': COLORS["chart"]["primary"]}
        },
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=80, b=80, l=40, r=40),
    )

    return fig


def create_support_level_chart(distribution: Dict) -> go.Figure:
    """Create pie chart showing support level distribution.

    Args:
        distribution: Dictionary of support level -> count

    Returns:
        Plotly figure
    """
    labels = list(distribution.keys())
    values = list(distribution.values())
    colors = [COLORS["support"].get(s, "#808080") for s in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker_colors=colors,
        textinfo='percent+label',
        textposition='inside',
    )])

    fig.update_layout(
        title={
            'text': "Support Level Distribution",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 18, 'color': COLORS["chart"]["primary"]}
        },
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=80, b=80, l=40, r=40),
    )

    return fig


def create_issue_categories_chart(issue_classes: Dict) -> go.Figure:
    """Create bar chart showing issue category distribution.

    Args:
        issue_classes: Dictionary of issue class -> count

    Returns:
        Plotly figure
    """
    # Sort by count descending
    sorted_items = sorted(issue_classes.items(), key=lambda x: x[1], reverse=True)[:10]
    categories = [item[0] for item in sorted_items]
    counts = [item[1] for item in sorted_items]

    fig = go.Figure(data=[go.Bar(
        x=categories,
        y=counts,
        marker_color=COLORS["chart"]["secondary"],
        text=counts,
        textposition='outside',
    )])

    fig.update_layout(
        title={
            'text': "Issue Categories Distribution",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 18, 'color': COLORS["chart"]["primary"]}
        },
        xaxis_title=dict(text="Issue Category", font=dict(color=BRAND_COLORS["text"], size=13)),
        yaxis_title=dict(text="Number of Cases", font=dict(color=BRAND_COLORS["text"], size=13)),
        xaxis_tickangle=-45,
        margin=dict(t=80, b=120, l=60, r=40),
        showlegend=False,
    )

    return fig


def create_top_25_critical_chart(cases: List[Dict]) -> go.Figure:
    """Create horizontal bar chart of top 25 critical cases.

    Args:
        cases: List of case dictionaries (already sorted by criticality)

    Returns:
        Plotly figure
    """
    top_25 = cases[:25]
    case_labels = [str(c["case_number"]) for c in top_25]
    scores = [c.get("criticality_score", 0) for c in top_25]
    severities = [c.get("severity", "S4") for c in top_25]
    colors = [COLORS["severity"].get(s, "#808080") for s in severities]

    fig = go.Figure(data=[go.Bar(
        y=case_labels,
        x=scores,
        orientation='h',
        marker_color=colors,
        text=[f"{s:.0f}" for s in scores],
        textposition='outside',
    )])

    fig.update_layout(
        title={
            'text': "Top 25 Critical Cases",
            'y': 0.98,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 18, 'color': COLORS["chart"]["primary"]}
        },
        xaxis_title=dict(text="Criticality Score", font=dict(color=BRAND_COLORS["text"], size=13)),
        yaxis_title=dict(text="Case Number", font=dict(color=BRAND_COLORS["text"], size=13)),
        yaxis=dict(
            autorange="reversed",  # Highest at top
            type='category'  # Force categorical axis for case numbers
        ),
        margin=dict(t=80, b=60, l=80, r=80),
        height=max(400, len(top_25) * 25),
        showlegend=False,
    )

    return fig


def create_score_breakdown_chart(cases: List[Dict]) -> go.Figure:
    """Create stacked bar chart showing score components for top 10 cases.

    Args:
        cases: List of case dictionaries (already sorted)

    Returns:
        Plotly figure
    """
    top_10 = cases[:10]
    case_labels = [str(c["case_number"]) for c in top_10]

    # Extract score components
    components = {
        "Claude Frustration": [],
        "Resolution Outlook": [],
        "Issue Class": [],
        "Severity": [],
        "Message Volume": [],
        "Support Level": [],
        "Engagement": [],
        "Case Age": [],
    }

    for case in top_10:
        breakdown = case.get("score_breakdown", {})
        components["Claude Frustration"].append(breakdown.get("claude_frustration", 0))
        components["Resolution Outlook"].append(breakdown.get("resolution_outlook", 0))
        components["Issue Class"].append(breakdown.get("issue_class", 0))
        components["Severity"].append(breakdown.get("technical_severity", 0))
        components["Message Volume"].append(breakdown.get("interaction_volume", 0))
        components["Support Level"].append(breakdown.get("support_level_priority", 0))
        components["Engagement"].append(breakdown.get("customer_engagement", 0))
        components["Case Age"].append(breakdown.get("case_age", 0))

    # Colors for each component - TrueNAS/Apple palette
    colors = [
        BRAND_COLORS["critical"],   # Claude Frustration - Apple red
        "#8B5A2B",                   # Resolution Outlook - Brown (neutral)
        BRAND_COLORS["warning"],    # Issue Class - Apple orange
        "#ff9f0a",                   # Severity - Lighter orange
        BRAND_COLORS["primary"],    # Message Volume - TrueNAS cyan
        "#5856d6",                   # Support Level - Purple
        BRAND_COLORS["success"],    # Engagement - TrueNAS green
        BRAND_COLORS["text_muted"], # Case Age - Gray
    ]

    fig = go.Figure()

    for i, (name, values) in enumerate(components.items()):
        fig.add_trace(go.Bar(
            name=name,
            x=case_labels,
            y=values,
            marker_color=colors[i],
        ))

    fig.update_layout(
        title={
            'text': "Score Breakdown - Top 10 Cases",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 18, 'color': COLORS["chart"]["primary"]}
        },
        xaxis_title=dict(text="Case Number", font=dict(color=BRAND_COLORS["text"], size=13)),
        yaxis_title=dict(text="Points", font=dict(color=BRAND_COLORS["text"], size=13)),
        xaxis=dict(type='category'),  # Force categorical axis for case numbers
        barmode='stack',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            font=dict(color=BRAND_COLORS["text"])
        ),
        margin=dict(t=80, b=120, l=60, r=40),
    )

    return fig


def create_all_charts(results: Dict) -> Dict[str, go.Figure]:
    """Create all charts from analysis results.

    Args:
        results: Complete analysis results dictionary

    Returns:
        Dictionary of chart name -> Plotly figure
    """
    stats = results.get("statistics", {}).get("haiku", {})
    distributions = results.get("distributions", {})
    cases = results.get("cases", [])

    charts = {
        "frustration_distribution": create_frustration_distribution_chart(stats),
        "severity_distribution": create_severity_distribution_chart(
            distributions.get("severity", {})
        ),
        "support_level_distribution": create_support_level_chart(
            distributions.get("support_level", {})
        ),
        "issue_categories": create_issue_categories_chart(
            distributions.get("issue_classes", {})
        ),
        "top_25_critical": create_top_25_critical_chart(cases),
        "score_breakdown": create_score_breakdown_chart(cases),
    }

    return charts


def chart_to_html(fig: go.Figure, include_plotlyjs: bool = False) -> str:
    """Convert a Plotly figure to HTML string.

    Args:
        fig: Plotly figure
        include_plotlyjs: Whether to include Plotly.js library

    Returns:
        HTML string
    """
    return fig.to_html(
        full_html=False,
        include_plotlyjs='cdn' if include_plotlyjs else False,
    )


def save_chart(fig: go.Figure, filepath: str, format: str = "html"):
    """Save a chart to file.

    Args:
        fig: Plotly figure
        filepath: Output file path
        format: 'html' or 'png'
    """
    if format == "html":
        fig.write_html(filepath)
    elif format == "png":
        fig.write_image(filepath, scale=2)
    else:
        raise ValueError(f"Unsupported format: {format}")
