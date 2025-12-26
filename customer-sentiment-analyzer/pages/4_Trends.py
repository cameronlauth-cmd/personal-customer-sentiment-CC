"""
Trends Page - Charts and pattern analysis.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dashboard.branding import (
    COLORS, get_health_color, get_frustration_color,
    get_severity_color, get_priority_color
)
from src.dashboard.styles import get_global_css, apply_plotly_theme
from src.dashboard.filters import get_filtered_cases, get_view_mode_indicator_html

# Page config
st.set_page_config(
    page_title="Trends - Customer Sentiment",
    page_icon="📈",
    layout="wide"
)

# Apply global CSS
st.markdown(get_global_css(), unsafe_allow_html=True)

# Sidebar with view mode toggle
with st.sidebar:
    st.markdown(f"""
    <div style="text-align: center; padding: 0.5rem 0; border-bottom: 1px solid {COLORS['border']}; margin-bottom: 0.75rem;">
        <h3 style="color: {COLORS['primary']}; margin: 0;">Customer Sentiment</h3>
    </div>
    """, unsafe_allow_html=True)

    # View Mode Toggle - synced across all pages via session state
    if 'view_mode' not in st.session_state:
        st.session_state['view_mode'] = 'All Cases'

    def on_view_mode_change():
        st.session_state['view_mode'] = st.session_state['view_mode_trends']

    st.radio(
        "View Mode",
        ["Recent Issues", "All Cases"],
        index=0 if st.session_state['view_mode'] == 'Recent Issues' else 1,
        help="Recent Issues: Activity in last 14 days + negative sentiment",
        key="view_mode_trends",
        on_change=on_view_mode_change
    )


def create_top_cases_chart(cases: list, top_n: int = 10) -> go.Figure:
    """Create horizontal bar chart of top critical cases."""
    sorted_cases = sorted(cases, key=lambda x: x.get("criticality_score", 0), reverse=True)[:top_n]

    case_labels = [f"Case {c.get('case_number', 'N/A')}" for c in sorted_cases]
    scores = [c.get("criticality_score", 0) for c in sorted_cases]
    colors = [get_frustration_color(c.get("claude_analysis", {}).get("frustration_score", 0)) for c in sorted_cases]

    fig = go.Figure(go.Bar(
        x=scores,
        y=case_labels,
        orientation='h',
        marker_color=colors,
        text=[f"{s:.0f}" for s in scores],
        textposition='outside'
    ))

    fig.update_layout(
        title=dict(text=f"Top {top_n} Cases by Criticality Score", font=dict(color=COLORS['text'])),
        xaxis_title=dict(text="Criticality Score", font=dict(color=COLORS['text'], size=13)),
        yaxis_title="",
        height=400,
        yaxis=dict(autorange="reversed")
    )
    fig = apply_plotly_theme(fig)
    return fig


def create_frustration_histogram(cases: list) -> go.Figure:
    """Create histogram of frustration score distribution."""
    scores = [c.get("claude_analysis", {}).get("frustration_score", 0) for c in cases]

    fig = go.Figure(go.Histogram(
        x=scores,
        nbinsx=10,
        marker_color=COLORS['primary'],
        marker_line_color=COLORS['border'],
        marker_line_width=1
    ))

    fig.update_layout(
        title=dict(text="Frustration Score Distribution", font=dict(color=COLORS['text'])),
        xaxis_title=dict(text="Frustration Score", font=dict(color=COLORS['text'], size=13)),
        yaxis_title=dict(text="Number of Cases", font=dict(color=COLORS['text'], size=13)),
        height=350,
        bargap=0.1
    )
    fig = apply_plotly_theme(fig)
    return fig


def create_severity_frustration_scatter(cases: list) -> go.Figure:
    """Create scatter plot of severity vs frustration."""
    severity_map = {"S1": 4, "S2": 3, "S3": 2, "S4": 1}

    data = []
    for c in cases:
        frustration = c.get("claude_analysis", {}).get("frustration_score", 0)
        severity = c.get("severity", "S4")
        severity_num = severity_map.get(severity, 1)
        data.append({
            "case_number": c.get("case_number", "N/A"),
            "customer": c.get("customer_name", "Unknown"),
            "frustration": frustration,
            "severity": severity,
            "severity_num": severity_num,
            "criticality": c.get("criticality_score", 0)
        })

    df = pd.DataFrame(data)

    fig = go.Figure()

    for sev in ["S1", "S2", "S3", "S4"]:
        sev_data = df[df['severity'] == sev]
        if len(sev_data) > 0:
            fig.add_trace(go.Scatter(
                x=sev_data['severity_num'],
                y=sev_data['frustration'],
                mode='markers',
                name=sev,
                marker=dict(
                    size=sev_data['criticality'] / 10 + 5,
                    color=get_severity_color(sev),
                    opacity=0.7
                ),
                text=sev_data['case_number'],
                hovertemplate="Case: %{text}<br>Frustration: %{y}<br>Severity: " + sev + "<extra></extra>"
            ))

    fig.update_layout(
        title=dict(text="Severity vs Frustration (bubble size = criticality)", font=dict(color=COLORS['text'])),
        xaxis=dict(
            title=dict(text="Severity", font=dict(color=COLORS['text'], size=13)),
            tickmode='array',
            tickvals=[1, 2, 3, 4],
            ticktext=["S4", "S3", "S2", "S1"]
        ),
        yaxis_title=dict(text="Frustration Score", font=dict(color=COLORS['text'], size=13)),
        height=400,
        showlegend=True
    )
    fig = apply_plotly_theme(fig)
    return fig


def create_issue_class_chart(distributions: dict) -> go.Figure:
    """Create bar chart of issue classifications."""
    issue_classes = distributions.get("issue_classes", {})
    if not issue_classes:
        return None

    labels = list(issue_classes.keys())
    values = list(issue_classes.values())

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation='h',
        marker_color=COLORS['secondary'],
        text=values,
        textposition='outside'
    ))

    fig.update_layout(
        title=dict(text="Issue Classifications", font=dict(color=COLORS['text'])),
        xaxis_title=dict(text="Number of Cases", font=dict(color=COLORS['text'], size=13)),
        yaxis_title="",
        height=300
    )
    fig = apply_plotly_theme(fig)
    return fig


def create_resolution_chart(distributions: dict) -> go.Figure:
    """Create donut chart of resolution outlooks."""
    resolution_outlooks = distributions.get("resolution_outlooks", {})
    if not resolution_outlooks:
        return None

    labels = list(resolution_outlooks.keys())
    values = list(resolution_outlooks.values())

    # Color mapping for resolution types
    color_map = {
        "Positive": COLORS['success'],
        "Uncertain": COLORS['warning'],
        "Negative": COLORS['critical'],
        "Stalled": COLORS['text_muted'],
    }
    colors = [color_map.get(label, COLORS['primary']) for label in labels]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker_colors=colors
    )])

    fig.update_layout(
        title=dict(text="Resolution Outlooks", font=dict(color=COLORS['text'])),
        height=300
    )
    fig = apply_plotly_theme(fig)
    return fig


def create_case_age_vs_frustration(cases: list) -> go.Figure:
    """Create scatter plot of case age vs frustration."""
    ages = [c.get("case_age_days", 0) for c in cases]
    frustrations = [c.get("claude_analysis", {}).get("frustration_score", 0) for c in cases]
    case_nums = [c.get("case_number", "N/A") for c in cases]
    criticalities = [c.get("criticality_score", 0) for c in cases]

    fig = go.Figure(go.Scatter(
        x=ages,
        y=frustrations,
        mode='markers',
        marker=dict(
            size=[max(c/15, 8) for c in criticalities],
            color=criticalities,
            colorscale='RdYlGn_r',
            colorbar=dict(title="Criticality"),
            opacity=0.7
        ),
        text=case_nums,
        hovertemplate="Case: %{text}<br>Age: %{x} days<br>Frustration: %{y}<extra></extra>"
    ))

    fig.update_layout(
        title=dict(text="Case Age vs Frustration Score", font=dict(color=COLORS['text'])),
        xaxis_title=dict(text="Case Age (days)", font=dict(color=COLORS['text'], size=13)),
        yaxis_title=dict(text="Frustration Score", font=dict(color=COLORS['text'], size=13)),
        height=400
    )
    fig = apply_plotly_theme(fig)
    return fig


def create_priority_distribution(cases: list) -> go.Figure:
    """Create bar chart of priority distribution from quick scoring."""
    priority_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}

    for c in cases:
        priority = (c.get("deepseek_quick_scoring") or {}).get("priority", "")
        if priority in priority_counts:
            priority_counts[priority] += 1

    labels = list(priority_counts.keys())
    values = list(priority_counts.values())
    colors = [get_priority_color(p) for p in labels]

    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker_color=colors,
        text=values,
        textposition='outside'
    ))

    fig.update_layout(
        title=dict(text="Priority Distribution", font=dict(color=COLORS['text'])),
        xaxis_title=dict(text="Priority Level", font=dict(color=COLORS['text'], size=13)),
        yaxis_title=dict(text="Number of Cases", font=dict(color=COLORS['text'], size=13)),
        height=300
    )
    fig = apply_plotly_theme(fig)
    return fig


def main():
    # Check for results
    if 'analysis_results' not in st.session_state:
        st.warning("No analysis results found. Please run an analysis from the main page first.")
        if st.button("Go to Main Page"):
            st.switch_page("app.py")
        return

    results = st.session_state['analysis_results']
    cases = results.get("cases", [])
    distributions = results.get("distributions", {})

    # Apply view mode filter
    view_mode = st.session_state.get('view_mode', 'All Cases')
    cases = get_filtered_cases(cases, view_mode)

    # Show view mode indicator
    indicator_html = get_view_mode_indicator_html(view_mode, len(cases), COLORS)
    if indicator_html:
        st.markdown(indicator_html, unsafe_allow_html=True)

    # Header
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLORS['surface']} 0%, {COLORS['background']} 100%);
                padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;
                border: 1px solid {COLORS['border']}; border-left: 4px solid {COLORS['primary']};">
        <h1 style="color: {COLORS['primary']}; margin: 0; font-size: 1.8rem;">Trends & Patterns</h1>
        <p style="color: {COLORS['text_muted']}; margin: 10px 0 0 0;">
            Visualizations and analysis patterns across {len(cases)} cases
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Top critical cases
    st.markdown(f"<h3 style='color: {COLORS['text']}'>Critical Cases</h3>", unsafe_allow_html=True)
    fig = create_top_cases_chart(cases, top_n=10)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Two column layout for distributions
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"<h4 style='color: {COLORS['text']}'>Frustration Distribution</h4>", unsafe_allow_html=True)
        fig = create_frustration_histogram(cases)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(f"<h4 style='color: {COLORS['text']}'>Priority Breakdown</h4>", unsafe_allow_html=True)
        fig = create_priority_distribution(cases)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Scatter plots
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"<h4 style='color: {COLORS['text']}'>Severity vs Frustration</h4>", unsafe_allow_html=True)
        fig = create_severity_frustration_scatter(cases)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(f"<h4 style='color: {COLORS['text']}'>Case Age vs Frustration</h4>", unsafe_allow_html=True)
        fig = create_case_age_vs_frustration(cases)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Issue classes and resolution
    col1, col2 = st.columns(2)

    with col1:
        if distributions.get("issue_classes"):
            st.markdown(f"<h4 style='color: {COLORS['text']}'>Issue Classifications</h4>", unsafe_allow_html=True)
            fig = create_issue_class_chart(distributions)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Issue classification data not available")

    with col2:
        if distributions.get("resolution_outlooks"):
            st.markdown(f"<h4 style='color: {COLORS['text']}'>Resolution Outlook</h4>", unsafe_allow_html=True)
            fig = create_resolution_chart(distributions)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Resolution outlook data not available")

    # Summary statistics table
    st.divider()
    st.markdown(f"<h3 style='color: {COLORS['text']}'>Analysis Summary</h3>", unsafe_allow_html=True)

    stats = results.get("statistics", {})
    haiku_stats = stats.get("haiku", {})
    timing = results.get("timing", {})

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style="background: {COLORS['surface']}; padding: 1rem; border-radius: 8px;
                    border: 1px solid {COLORS['border']};">
            <h5 style="color: {COLORS['primary']}; margin: 0 0 10px 0;">Frustration Analysis</h5>
            <p style="color: {COLORS['text']}; margin: 5px 0;">
                Total Messages: <strong>{haiku_stats.get('total_messages_analyzed', 0)}</strong>
            </p>
            <p style="color: {COLORS['text']}; margin: 5px 0;">
                Frustrated Messages: <strong>{haiku_stats.get('frustrated_messages_count', 0)}</strong>
            </p>
            <p style="color: {COLORS['text']}; margin: 5px 0;">
                High Frustration Cases: <strong>{haiku_stats.get('high_frustration', 0)}</strong>
            </p>
            <p style="color: {COLORS['text']}; margin: 5px 0;">
                Avg Score: <strong>{haiku_stats.get('avg_frustration_score', 0):.1f}/10</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        severity_dist = distributions.get("severity", {})
        st.markdown(f"""
        <div style="background: {COLORS['surface']}; padding: 1rem; border-radius: 8px;
                    border: 1px solid {COLORS['border']};">
            <h5 style="color: {COLORS['primary']}; margin: 0 0 10px 0;">Severity Breakdown</h5>
            <p style="color: {COLORS['critical']}; margin: 5px 0;">
                S1 (Critical): <strong>{severity_dist.get('S1', 0)}</strong>
            </p>
            <p style="color: {COLORS['warning']}; margin: 5px 0;">
                S2 (High): <strong>{severity_dist.get('S2', 0)}</strong>
            </p>
            <p style="color: {COLORS['secondary']}; margin: 5px 0;">
                S3 (Medium): <strong>{severity_dist.get('S3', 0)}</strong>
            </p>
            <p style="color: {COLORS['text_muted']}; margin: 5px 0;">
                S4 (Low): <strong>{severity_dist.get('S4', 0)}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div style="background: {COLORS['surface']}; padding: 1rem; border-radius: 8px;
                    border: 1px solid {COLORS['border']};">
            <h5 style="color: {COLORS['primary']}; margin: 0 0 10px 0;">Performance</h5>
            <p style="color: {COLORS['text']}; margin: 5px 0;">
                Total Time: <strong>{timing.get('total_time', 0):.1f}s</strong>
            </p>
            <p style="color: {COLORS['text']}; margin: 5px 0;">
                Stage 1: <strong>{timing.get('haiku_time', 0):.1f}s</strong>
            </p>
            <p style="color: {COLORS['text']}; margin: 5px 0;">
                Stage 2A: <strong>{timing.get('sonnet_quick_time', 0):.1f}s</strong>
            </p>
            <p style="color: {COLORS['text']}; margin: 5px 0;">
                Stage 2B: <strong>{timing.get('sonnet_timeline_time', 0):.1f}s</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
