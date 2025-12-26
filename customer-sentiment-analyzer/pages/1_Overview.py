"""
Overview Page - Open Case Analysis with actionable insights.
"""

import streamlit as st
import plotly.graph_objects as go
from collections import Counter

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dashboard.branding import COLORS, get_frustration_color
from src.dashboard.styles import get_global_css, apply_plotly_theme
from src.dashboard.filters import get_filtered_cases, get_view_mode_indicator_html

# Page config
st.set_page_config(
    page_title="Open Case Analysis",
    page_icon="📊",
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
        st.session_state['view_mode'] = st.session_state['view_mode_overview']

    st.radio(
        "View Mode",
        ["Recent Issues", "All Cases"],
        index=0 if st.session_state['view_mode'] == 'Recent Issues' else 1,
        help="Recent Issues: Activity in last 14 days + negative sentiment",
        key="view_mode_overview",
        on_change=on_view_mode_change
    )


def get_case_status(case: dict) -> str:
    """Determine if case is improving, deteriorating, or stable."""
    deepseek = case.get("deepseek_analysis") or {}
    claude = case.get("claude_analysis") or {}

    sentiment_trend = deepseek.get("sentiment_trend", "").lower()
    resolution = claude.get("resolution_outlook", "").lower()

    # Check for deteriorating signals
    if any(word in sentiment_trend for word in ["negative", "worsening", "declining", "deteriorat"]):
        return "deteriorating"
    if resolution in ["negative", "stalled"]:
        return "deteriorating"

    # Check for improving signals
    if any(word in sentiment_trend for word in ["positive", "improving", "better"]):
        return "improving"
    if resolution == "positive":
        return "improving"

    return "stable"


def main():
    # Check for results
    if 'analysis_results' not in st.session_state:
        st.warning("No analysis results found. Please run an analysis from the main page first.")
        if st.button("Go to Main Page"):
            st.switch_page("app.py")
        return

    results = st.session_state['analysis_results']
    cases = results.get("cases", [])

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
        <h1 style="color: {COLORS['primary']}; margin: 0; font-size: 1.8rem;">Open Case Analysis</h1>
        <p style="color: {COLORS['text_muted']}; margin: 10px 0 0 0;">
            Identify at-risk customers before issues escalate - {len(cases)} open cases analyzed
        </p>
    </div>
    """, unsafe_allow_html=True)

    # === QUICK STATS ROW ===
    stats = results.get("statistics", {})
    haiku_stats = stats.get("haiku", {})

    # Calculate case statuses
    needs_attention = []
    improving = []
    deteriorating = []

    for case in cases:
        claude = case.get("claude_analysis") or {}
        frustration = claude.get("frustration_score", 0)
        severity = case.get("severity", "S4")
        status = get_case_status(case)

        if status == "deteriorating":
            deteriorating.append(case)
        elif status == "improving":
            improving.append(case)

        # Needs attention: high frustration OR S1/S2 severity
        if frustration >= 7 or severity in ["S1", "S2"]:
            needs_attention.append(case)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Need Immediate Attention",
            len(needs_attention),
            help="High frustration (7+) or S1/S2 severity"
        )
    with col2:
        st.metric(
            "Cases Deteriorating",
            len(deteriorating),
            delta=f"-{len(deteriorating)}" if deteriorating else None,
            delta_color="inverse",
            help="Negative sentiment trend"
        )
    with col3:
        st.metric(
            "Cases Improving",
            len(improving),
            delta=f"+{len(improving)}" if improving else None,
            help="Positive sentiment trend"
        )
    with col4:
        avg_frust = haiku_stats.get("avg_frustration_score", 0)
        st.metric("Avg Frustration", f"{avg_frust:.1f}/10")

    st.divider()

    # === CUSTOMER HOTSPOTS ===
    st.markdown(f"<h3 style='color: {COLORS['text']}'>Customer Hotspots</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: {COLORS['text_muted']}'>Customers with multiple open cases may have systemic issues</p>", unsafe_allow_html=True)

    # Group cases by customer
    customer_cases = {}
    for case in cases:
        customer = case.get("customer_name", "Unknown")
        if customer not in customer_cases:
            customer_cases[customer] = []
        customer_cases[customer].append(case)

    # Find customers with 2+ cases
    hotspots = [(customer, cases_list) for customer, cases_list in customer_cases.items() if len(cases_list) >= 2]
    hotspots.sort(key=lambda x: len(x[1]), reverse=True)

    if hotspots:
        for customer, customer_case_list in hotspots[:5]:  # Top 5
            total_frustration = sum(
                (c.get("claude_analysis") or {}).get("frustration_score", 0)
                for c in customer_case_list
            )
            avg_frust = total_frustration / len(customer_case_list)
            frust_color = get_frustration_color(avg_frust)

            case_nums = ", ".join([str(c.get("case_number", "?")) for c in customer_case_list])

            st.markdown(f"""
            <div style="background: {COLORS['surface']}; padding: 1rem; border-radius: 8px;
                        border: 1px solid {COLORS['border']}; margin-bottom: 0.5rem;
                        border-left: 4px solid {frust_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong style="color: {COLORS['text']};">{customer}</strong>
                        <span style="color: {COLORS['text_muted']}; margin-left: 1rem;">Cases: {case_nums}</span>
                    </div>
                    <div>
                        <span style="background: {frust_color}; color: white; padding: 4px 12px;
                                     border-radius: 20px; font-weight: bold;">
                            {len(customer_case_list)} cases | Avg: {avg_frust:.1f}/10
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No customers with multiple open cases")

    st.divider()

    # === RECENT ESCALATION SIGNALS ===
    st.markdown(f"<h3 style='color: {COLORS['text']}'>Recent Escalation Signals</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: {COLORS['text_muted']}'>Cases showing signs of customer frustration or negative trends</p>", unsafe_allow_html=True)

    escalation_cases = []
    for case in cases:
        claude = case.get("claude_analysis") or {}
        deepseek = case.get("deepseek_analysis") or {}
        frustration = claude.get("frustration_score", 0)
        age = case.get("case_age_days", 0)
        sentiment = deepseek.get("sentiment_trend", "")

        # Escalation signals: high frustration + recent, OR negative sentiment trend
        is_escalating = False
        reason = ""

        if frustration >= 7 and age <= 14:
            is_escalating = True
            reason = f"High frustration ({frustration}/10) on recent case"
        elif any(word in sentiment.lower() for word in ["negative", "worsening", "declining"]):
            is_escalating = True
            reason = f"Negative sentiment trend"
        elif frustration >= 8:
            is_escalating = True
            reason = f"Very high frustration ({frustration}/10)"

        if is_escalating:
            escalation_cases.append((case, reason))

    # Sort by frustration score
    escalation_cases.sort(key=lambda x: (x[0].get("claude_analysis") or {}).get("frustration_score", 0), reverse=True)

    if escalation_cases:
        for case, reason in escalation_cases[:8]:  # Top 8
            claude = case.get("claude_analysis") or {}
            frustration = claude.get("frustration_score", 0)
            frust_color = get_frustration_color(frustration)
            key_phrase = claude.get("key_phrase", "")

            st.markdown(f"""
            <div style="background: {COLORS['surface']}; padding: 1rem; border-radius: 8px;
                        border: 1px solid {COLORS['border']}; margin-bottom: 0.5rem;
                        border-left: 4px solid {frust_color};">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div style="flex: 1;">
                        <strong style="color: {COLORS['text']};">Case {case.get('case_number')}</strong>
                        <span style="color: {COLORS['text_muted']}; margin-left: 1rem;">{case.get('customer_name', 'Unknown')[:30]}</span>
                        <p style="color: {COLORS['warning']}; margin: 5px 0 0 0; font-size: 0.9rem;">{reason}</p>
                        {f'<p style="color: {COLORS["text_muted"]}; margin: 5px 0 0 0; font-style: italic; font-size: 0.85rem;">"{key_phrase[:100]}..."</p>' if key_phrase else ''}
                    </div>
                    <span style="background: {frust_color}; color: white; padding: 4px 12px;
                                 border-radius: 20px; font-weight: bold; white-space: nowrap;">
                        {frustration}/10
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.success("No escalation signals detected")

    st.divider()

    # === KEY METRICS ROW ===
    st.markdown(f"<h3 style='color: {COLORS['text']}'>Analysis Metrics</h3>", unsafe_allow_html=True)

    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        st.metric("Total Cases", results.get("total_cases", 0))
    with m2:
        high_frust = haiku_stats.get("high_frustration", 0)
        st.metric("High Frustration Cases", high_frust)
    with m3:
        critical = len([c for c in cases if c.get("criticality_score", 0) >= 180])
        st.metric("Critical Score Cases", critical)
    with m4:
        msg_count = haiku_stats.get("total_messages_analyzed", 0)
        st.metric("Messages Analyzed", msg_count)
    with m5:
        timing = results.get("timing", {})
        st.metric("Analysis Time", f"{timing.get('total_time', 0):.1f}s")

    st.divider()

    # === DISTRIBUTIONS ===
    distributions = results.get("distributions", {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"<h4 style='color: {COLORS['text']}'>Severity Distribution</h4>", unsafe_allow_html=True)
        severity_dist = distributions.get("severity", {})
        if severity_dist:
            fig = go.Figure(data=[go.Pie(
                labels=list(severity_dist.keys()),
                values=list(severity_dist.values()),
                hole=0.4,
                marker_colors=[COLORS['critical'], COLORS['warning'], COLORS['secondary'], COLORS['text_muted']],
                textfont=dict(color=COLORS['text'], size=12),
                textinfo='label+percent',
                insidetextorientation='radial'
            )])
            fig = apply_plotly_theme(fig)
            fig.update_layout(height=350, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No severity distribution data available")

    with col2:
        st.markdown(f"<h4 style='color: {COLORS['text']}'>Support Level Distribution</h4>", unsafe_allow_html=True)
        support_dist = distributions.get("support_level", {})
        if support_dist:
            fig = go.Figure(data=[go.Pie(
                labels=list(support_dist.keys()),
                values=list(support_dist.values()),
                hole=0.4,
                marker_colors=[COLORS['warning'], COLORS['secondary'], COLORS['text_muted'], COLORS['border']],
                textfont=dict(color=COLORS['text'], size=12),
                textinfo='label+percent',
                insidetextorientation='radial'
            )])
            fig = apply_plotly_theme(fig)
            fig.update_layout(height=350, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No support level distribution data available")

    # Issue classes and resolution outlooks
    col1, col2 = st.columns(2)

    with col1:
        issue_classes = distributions.get("issue_classes", {})
        if issue_classes:
            st.markdown(f"<h4 style='color: {COLORS['text']}'>Issue Classes</h4>", unsafe_allow_html=True)
            fig = go.Figure(data=[go.Bar(
                x=list(issue_classes.keys()),
                y=list(issue_classes.values()),
                marker_color=COLORS['primary']
            )])
            fig = apply_plotly_theme(fig)
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        resolution_outlooks = distributions.get("resolution_outlooks", {})
        if resolution_outlooks:
            st.markdown(f"<h4 style='color: {COLORS['text']}'>Resolution Outlooks</h4>", unsafe_allow_html=True)
            fig = go.Figure(data=[go.Bar(
                x=list(resolution_outlooks.keys()),
                y=list(resolution_outlooks.values()),
                marker_color=COLORS['secondary']
            )])
            fig = apply_plotly_theme(fig)
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
