"""
Cases Page - Case browser with filters and AI analysis details.
"""

import streamlit as st
import pandas as pd

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dashboard.branding import (
    COLORS, get_health_color, get_frustration_color,
    get_severity_color, get_priority_color
)
from src.dashboard.styles import get_global_css
from src.dashboard.filters import get_filtered_cases, get_view_mode_indicator_html

# Page config
st.set_page_config(
    page_title="Cases - Customer Sentiment",
    page_icon="📋",
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

    # View Mode Toggle - always visible
    view_mode = st.radio(
        "View Mode",
        ["Recent Issues", "All Cases"],
        index=1 if st.session_state.get('view_mode', 'All Cases') == 'All Cases' else 0,
        help="Recent Issues: Activity in last 14 days + negative sentiment",
        key="cases_view_mode"
    )
    st.session_state['view_mode'] = view_mode


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
        <h1 style="color: {COLORS['primary']}; margin: 0; font-size: 1.8rem;">Case Browser</h1>
        <p style="color: {COLORS['text_muted']}; margin: 10px 0 0 0;">
            {len(cases)} cases analyzed - click a row to view details
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        severity_filter = st.multiselect(
            "Severity",
            options=["S1", "S2", "S3", "S4"],
            default=[]
        )

    with col2:
        min_frustration = st.slider(
            "Min Frustration Score",
            min_value=0,
            max_value=10,
            value=0
        )

    with col3:
        min_criticality = st.slider(
            "Min Criticality Score",
            min_value=0,
            max_value=250,
            value=0
        )

    with col4:
        has_timeline = st.checkbox("Has Timeline", value=False)

    # Filter cases
    filtered_cases = cases
    if severity_filter:
        filtered_cases = [c for c in filtered_cases if c.get("severity") in severity_filter]
    if min_frustration > 0:
        filtered_cases = [c for c in filtered_cases
                        if c.get("claude_analysis", {}).get("frustration_score", 0) >= min_frustration]
    if min_criticality > 0:
        filtered_cases = [c for c in filtered_cases
                        if c.get("criticality_score", 0) >= min_criticality]
    if has_timeline:
        filtered_cases = [c for c in filtered_cases
                        if c.get("deepseek_analysis", {}).get("timeline_entries")]

    st.markdown(f"<p style='color: {COLORS['text_muted']}'>{len(filtered_cases)} cases match filters</p>",
                unsafe_allow_html=True)

    # Build table data
    table_data = []
    for i, case in enumerate(filtered_cases):
        claude = case.get("claude_analysis") or {}
        quick = case.get("deepseek_quick_scoring") or {}
        deepseek = case.get("deepseek_analysis") or {}

        table_data.append({
            "Rank": i + 1,
            "Case #": case.get("case_number"),
            "Customer": str(case.get("customer_name", ""))[:35],
            "Criticality": round(case.get("criticality_score", 0), 1),
            "Frustration": claude.get("frustration_score", 0),
            "Severity": case.get("severity", "S4"),
            "Issue Class": claude.get("issue_class", "Unknown"),
            "Resolution": claude.get("resolution_outlook", "Unknown"),
            "Priority": quick.get("priority", "-"),
            "Age (days)": case.get("case_age_days", 0),
            "Messages": case.get("interaction_count", 0),
            "Has Timeline": "Yes" if deepseek.get("timeline_entries") else "No",
        })

    if table_data:
        df = pd.DataFrame(table_data)

        # Display table with selection
        event = st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
            column_config={
                "Criticality": st.column_config.ProgressColumn(
                    min_value=0,
                    max_value=250,
                    format="%.0f"
                ),
                "Frustration": st.column_config.ProgressColumn(
                    min_value=0,
                    max_value=10,
                    format="%.0f"
                ),
            }
        )

        # Handle row selection
        selected_rows = event.selection.rows if hasattr(event, 'selection') else []

        if selected_rows:
            selected_idx = selected_rows[0]
            selected_case = filtered_cases[selected_idx]
            display_case_detail(selected_case)

    else:
        st.info("No cases match the current filters.")


def display_case_detail(case: dict):
    """Display detailed case information."""

    st.divider()

    claude = case.get("claude_analysis") or {}
    quick = case.get("deepseek_quick_scoring") or {}
    deepseek = case.get("deepseek_analysis") or {}
    criticality = case.get("criticality_score", 0)

    # Case header
    frustration = claude.get("frustration_score", 0)
    frust_color = get_frustration_color(frustration)
    severity_color = get_severity_color(case.get("severity", "S4"))

    st.markdown(f"""
    <div style="background: {COLORS['surface']}; padding: 1.5rem; border-radius: 12px;
                border: 1px solid {COLORS['border']}; margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="color: {COLORS['text']}; margin: 0;">Case {case.get('case_number')}</h2>
                <p style="color: {COLORS['text_muted']}; margin: 5px 0 0 0;">{case.get('customer_name', 'Unknown')}</p>
            </div>
            <div style="text-align: right;">
                <span style="background: {frust_color}; color: white; padding: 4px 12px;
                             border-radius: 20px; font-weight: bold; margin-left: 8px;">
                    Frustration: {frustration}/10
                </span>
                <span style="background: {severity_color}; color: white; padding: 4px 12px;
                             border-radius: 20px; font-weight: bold; margin-left: 8px;">
                    {case.get('severity', 'S4')}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # AI Summary Card for high criticality cases (>= 100)
    if criticality >= 100:
        summary_content = []

        # Gather available summary info
        if deepseek.get("executive_summary"):
            summary_content.append(("Executive Summary", deepseek["executive_summary"], COLORS['primary']))
        if deepseek.get("recommended_action"):
            summary_content.append(("Recommended Action", deepseek["recommended_action"], COLORS['success']))
        if quick.get("justification"):
            summary_content.append(("Priority Analysis", quick["justification"], COLORS['warning']))
        if claude.get("key_phrase") and not deepseek.get("executive_summary"):
            summary_content.append(("Key Phrase", f'"{claude["key_phrase"]}"', COLORS['warning']))

        if summary_content:
            crit_color = COLORS['critical'] if criticality >= 180 else COLORS['warning']
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {COLORS['surface']} 0%, #1a1a2e 100%);
                        padding: 1.25rem; border-radius: 10px; margin-bottom: 1rem;
                        border: 1px solid {crit_color}; border-left: 4px solid {crit_color};">
                <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
                    <span style="font-size: 1.1rem; margin-right: 8px;">🤖</span>
                    <strong style="color: {crit_color};">AI Case Summary</strong>
                    <span style="color: {COLORS['text_muted']}; margin-left: auto; font-size: 0.85rem;">
                        Criticality: {criticality:.0f}
                    </span>
                </div>
            """, unsafe_allow_html=True)

            for title, content, color in summary_content:
                st.markdown(f"""
                <div style="margin-bottom: 0.75rem;">
                    <strong style="color: {color}; font-size: 0.9rem;">{title}</strong>
                    <p style="color: {COLORS['text']}; margin: 4px 0 0 0; font-size: 0.95rem;">{content}</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("</div>", unsafe_allow_html=True)

    # Metrics row
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Criticality Score", f"{case.get('criticality_score', 0):.0f}")
    with col2:
        st.metric("Issue Class", claude.get("issue_class", "Unknown"))
    with col3:
        st.metric("Resolution Outlook", claude.get("resolution_outlook", "Unknown"))
    with col4:
        st.metric("Case Age", f"{case.get('case_age_days', 0)} days")
    with col5:
        st.metric("Messages", case.get("interaction_count", 0))

    # Quick scoring info
    if quick and quick.get("analysis_successful"):
        priority = quick.get("priority", "Medium")
        priority_color = get_priority_color(priority)

        st.markdown(f"""
        <div style="background: {COLORS['surface']}; padding: 1rem; border-radius: 8px;
                    border: 1px solid {COLORS['border']}; margin: 1rem 0;">
            <span style="background: {priority_color}; color: white; padding: 4px 12px;
                         border-radius: 4px; font-weight: bold;">Priority: {priority}</span>
            <span style="color: {COLORS['text_muted']}; margin-left: 1rem;">
                Frustration Rate: {quick.get('frustration_frequency', 0)}% |
                Damage Rate: {quick.get('damage_frequency', 0)}%
            </span>
        </div>
        """, unsafe_allow_html=True)

        if quick.get("justification"):
            st.markdown(f"""
            <div style="background: {COLORS['surface']}; border-left: 4px solid {COLORS['primary']};
                        padding: 15px; border-radius: 0 8px 8px 0; margin-bottom: 1rem;">
                <strong style="color: {COLORS['text']};">Justification:</strong>
                <p style="color: {COLORS['text_muted']}; margin: 5px 0 0 0;">{quick['justification']}</p>
            </div>
            """, unsafe_allow_html=True)

    # Detailed analysis (if available)
    if deepseek and deepseek.get("analysis_successful"):
        st.markdown(f"<h3 style='color: {COLORS['text']}'>AI Analysis</h3>", unsafe_allow_html=True)

        # Executive summary
        if deepseek.get("executive_summary"):
            st.markdown(f"""
            <div style="background: {COLORS['surface']}; border-left: 4px solid {COLORS['primary']};
                        padding: 15px; border-radius: 0 8px 8px 0; margin-bottom: 1rem;">
                <strong style="color: {COLORS['primary']};">Executive Summary</strong>
                <p style="color: {COLORS['text']}; margin: 10px 0 0 0;">{deepseek['executive_summary']}</p>
            </div>
            """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)

        with col1:
            # Pain points
            if deepseek.get("pain_points"):
                st.markdown(f"""
                <div style="background: #2d2315; border-left: 4px solid {COLORS['warning']};
                            padding: 15px; border-radius: 0 8px 8px 0;">
                    <strong style="color: {COLORS['warning']};">Pain Points</strong>
                    <p style="color: {COLORS['text']}; margin: 10px 0 0 0;">{deepseek['pain_points']}</p>
                </div>
                """, unsafe_allow_html=True)

            # Sentiment trend
            if deepseek.get("sentiment_trend"):
                st.markdown(f"""
                <div style="background: {COLORS['surface']}; border-left: 4px solid {COLORS['secondary']};
                            padding: 15px; border-radius: 0 8px 8px 0; margin-top: 1rem;">
                    <strong style="color: {COLORS['secondary']};">Sentiment Trend</strong>
                    <p style="color: {COLORS['text']}; margin: 10px 0 0 0;">{deepseek['sentiment_trend']}</p>
                </div>
                """, unsafe_allow_html=True)

        with col2:
            # Recommended action
            if deepseek.get("recommended_action"):
                st.markdown(f"""
                <div style="background: #152d15; border-left: 4px solid {COLORS['success']};
                            padding: 15px; border-radius: 0 8px 8px 0;">
                    <strong style="color: {COLORS['success']};">Recommended Action</strong>
                    <p style="color: {COLORS['text']}; margin: 10px 0 0 0;">{deepseek['recommended_action']}</p>
                </div>
                """, unsafe_allow_html=True)

            # Customer priority
            if deepseek.get("customer_priority"):
                priority = deepseek['customer_priority']
                priority_color = get_priority_color(priority)
                st.markdown(f"""
                <div style="background: {COLORS['surface']}; border-left: 4px solid {priority_color};
                            padding: 15px; border-radius: 0 8px 8px 0; margin-top: 1rem;">
                    <strong style="color: {priority_color};">Customer Priority: {priority}</strong>
                </div>
                """, unsafe_allow_html=True)

        # Critical inflection points
        if deepseek.get("critical_inflection_points"):
            st.markdown(f"""
            <div style="background: {COLORS['surface']}; border-left: 4px solid {COLORS['text_muted']};
                        padding: 15px; border-radius: 0 8px 8px 0; margin-top: 1rem;">
                <strong style="color: {COLORS['text']};">Critical Inflection Points</strong>
                <p style="color: {COLORS['text_muted']}; margin: 10px 0 0 0;">{deepseek['critical_inflection_points']}</p>
            </div>
            """, unsafe_allow_html=True)

        # Timeline link
        timeline_entries = deepseek.get("timeline_entries", [])
        if timeline_entries:
            st.markdown(f"""
            <div style="background: {COLORS['surface']}; padding: 1rem; border-radius: 8px;
                        border: 1px solid {COLORS['border']}; margin-top: 1rem; text-align: center;">
                <p style="color: {COLORS['text']}; margin: 0;">
                    This case has <strong>{len(timeline_entries)}</strong> timeline entries.
                    View the full timeline on the <strong>Timeline</strong> page.
                </p>
            </div>
            """, unsafe_allow_html=True)

    # Key phrase (fallback if no detailed analysis)
    elif claude.get("key_phrase"):
        st.markdown(f"<h3 style='color: {COLORS['text']}'>Key Phrase</h3>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background: #2d2315; border-left: 4px solid {COLORS['warning']};
                    padding: 15px; border-radius: 0 8px 8px 0;">
            <p style="color: {COLORS['text']}; margin: 0; font-style: italic;">
                "{claude['key_phrase']}"
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Frustration metrics
    metrics = claude.get("frustration_metrics", {})
    if metrics:
        with st.expander("Frustration Metrics Details"):
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Average Score", f"{metrics.get('average_score', 0):.1f}")
            with col2:
                st.metric("Peak Score", metrics.get('peak_score', 0))
            with col3:
                st.metric("Frustration Frequency", f"{metrics.get('frustration_frequency', 0):.0f}%")
            with col4:
                st.metric("Frustrated Messages", f"{metrics.get('frustrated_message_count', 0)}/{metrics.get('total_messages', 0)}")

            # Message-level scores
            message_scores = metrics.get("message_scores", [])
            if message_scores:
                st.markdown(f"<p style='color: {COLORS['text']}; margin-top: 1rem;'><strong>Message Scores (first 10):</strong></p>", unsafe_allow_html=True)
                for msg in message_scores[:10]:
                    score = msg.get('score', 0)
                    color = get_frustration_color(score)
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; margin: 5px 0;">
                        <span style="background: {color}; color: white; padding: 2px 8px;
                                     border-radius: 4px; font-weight: bold; min-width: 30px; text-align: center;">
                            {score}
                        </span>
                        <span style="color: {COLORS['text_muted']}; margin-left: 10px; font-size: 0.9rem;">
                            Msg {msg.get('msg', '?')}: {msg.get('reason', 'No reason provided')}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
