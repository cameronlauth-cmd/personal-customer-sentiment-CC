"""
Timeline Page - Detailed timeline visualization for cases with Sonnet analysis.
"""

import streamlit as st
import re

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dashboard.branding import (
    COLORS, get_frustration_color, get_severity_color, get_priority_color
)
from src.dashboard.styles import get_global_css
from src.dashboard.filters import get_filtered_cases, get_view_mode_indicator_html

# Page config
st.set_page_config(
    page_title="Timeline - Customer Sentiment",
    page_icon="📅",
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
        st.session_state['view_mode'] = st.session_state['view_mode_timeline']

    st.radio(
        "View Mode",
        ["Recent Issues", "All Cases"],
        index=0 if st.session_state['view_mode'] == 'Recent Issues' else 1,
        help="Recent Issues: Activity in last 14 days + negative sentiment",
        key="view_mode_timeline",
        on_change=on_view_mode_change
    )


def clean_text(text: str) -> str:
    """Remove markdown artifacts and HTML tags from text."""
    if not text:
        return ""

    # Remove markdown bold/italic
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)

    # Remove HTML tags (except our highlight spans)
    text = re.sub(r'<(?!/?font)[^>]+>', '', text)

    # Remove [cid:...] artifacts
    text = re.sub(r'\[cid:[^\]]+\]', '', text)

    # Clean up whitespace
    text = ' '.join(text.split())

    return text.strip()


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

    # Filter to only cases with timeline entries
    cases_with_timelines = [
        c for c in cases
        if (c.get("deepseek_analysis") or {}).get("timeline_entries")
    ]

    # Header
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLORS['surface']} 0%, {COLORS['background']} 100%);
                padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;
                border: 1px solid {COLORS['border']}; border-left: 4px solid {COLORS['primary']};">
        <h1 style="color: {COLORS['primary']}; margin: 0; font-size: 1.8rem;">Case Timelines</h1>
        <p style="color: {COLORS['text_muted']}; margin: 10px 0 0 0;">
            {len(cases_with_timelines)} cases with detailed timeline analysis
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not cases_with_timelines:
        st.info("No cases have timeline analysis. Timeline analysis is generated for top critical cases during Stage 2B analysis.")
        return

    # Sort cases by criticality score descending (highest first)
    cases_with_timelines = sorted(
        cases_with_timelines,
        key=lambda c: c.get("criticality_score", 0),
        reverse=True
    )

    # Case selector (now sorted by criticality)
    case_options = {
        f"Case {c.get('case_number')} - {c.get('customer_name', 'Unknown')[:30]} (Score: {c.get('criticality_score', 0):.0f})": c
        for c in cases_with_timelines
    }

    selected_label = st.selectbox(
        "Select Case",
        options=list(case_options.keys())
    )

    if selected_label:
        selected_case = case_options[selected_label]
        display_case_timeline(selected_case)


def display_case_timeline(case: dict):
    """Display the full timeline for a case."""

    claude = case.get("claude_analysis") or {}
    deepseek = case.get("deepseek_analysis") or {}
    timeline_entries = deepseek.get("timeline_entries") or []

    # Case header
    frustration = claude.get("frustration_score", 0)
    frust_color = get_frustration_color(frustration)
    severity_color = get_severity_color(case.get("severity", "S4"))

    st.markdown(f"""
    <div style="background: {COLORS['surface']}; padding: 1.5rem; border-radius: 12px;
                border: 1px solid {COLORS['border']}; margin: 1rem 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <h2 style="color: {COLORS['text']}; margin: 0;">Case {case.get('case_number')}</h2>
                <p style="color: {COLORS['text_muted']}; margin: 5px 0 0 0;">{case.get('customer_name', 'Unknown')}</p>
            </div>
            <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-top: 10px;">
                <span style="background: {frust_color}; color: white; padding: 4px 12px;
                             border-radius: 20px; font-weight: bold;">
                    Frustration: {frustration}/10
                </span>
                <span style="background: {severity_color}; color: white; padding: 4px 12px;
                             border-radius: 20px; font-weight: bold;">
                    {case.get('severity', 'S4')}
                </span>
                <span style="background: {COLORS['border']}; color: {COLORS['text']}; padding: 4px 12px;
                             border-radius: 20px;">
                    {case.get('case_age_days', 0)} days
                </span>
                <span style="background: {COLORS['border']}; color: {COLORS['text']}; padding: 4px 12px;
                             border-radius: 20px;">
                    {case.get('interaction_count', 0)} messages
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Timeline stats
    frustrated_count = sum(
        1 for e in timeline_entries
        if 'yes' in str(e.get('frustration_detected', '')).lower()
    )
    positive_count = sum(
        1 for e in timeline_entries
        if 'yes' in str(e.get('positive_action_detected', '')).lower()
    )
    failure_count = sum(
        1 for e in timeline_entries
        if 'yes' in str(e.get('failure_pattern_detected', '')).lower()
    )
    neutral_count = len(timeline_entries) - frustrated_count - positive_count

    st.markdown(f"""
    <div style="display: flex; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap;">
        <span style="background: {COLORS['critical']}; color: white; padding: 6px 16px;
                     border-radius: 20px; font-weight: 500;">
            {frustrated_count} Frustrated
        </span>
        <span style="background: {COLORS['warning']}; color: white; padding: 6px 16px;
                     border-radius: 20px; font-weight: 500;">
            {failure_count} Failure Patterns
        </span>
        <span style="background: {COLORS['success']}; color: white; padding: 6px 16px;
                     border-radius: 20px; font-weight: 500;">
            {positive_count} Positive Actions
        </span>
        <span style="background: {COLORS['text_muted']}; color: white; padding: 6px 16px;
                     border-radius: 20px; font-weight: 500;">
            {neutral_count} Neutral
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Timeline entries
    st.markdown(f"<h3 style='color: {COLORS['text']}'>Timeline ({len(timeline_entries)} entries)</h3>",
                unsafe_allow_html=True)

    for i, entry in enumerate(timeline_entries):
        display_timeline_entry(i, entry)

    # Summary sections below timeline
    st.divider()
    display_timeline_summary(case, deepseek, claude)


def display_timeline_entry(index: int, entry: dict):
    """Display a single timeline entry as an expander."""

    entry_label = clean_text(entry.get('entry_label', f'Entry {index + 1}'))
    summary = clean_text(entry.get('summary', ''))
    customer_tone = clean_text(entry.get('customer_tone', ''))

    # Detect entry type
    has_frustration = 'yes' in str(entry.get('frustration_detected', '')).lower()
    has_failure = 'yes' in str(entry.get('failure_pattern_detected', '')).lower()
    has_positive = 'yes' in str(entry.get('positive_action_detected', '')).lower()

    # Determine status icon and color
    if has_frustration or has_failure:
        icon = "🔴"
        border_color = COLORS['critical']
    elif has_positive:
        icon = "🟢"
        border_color = COLORS['success']
    else:
        icon = "🟡"
        border_color = COLORS['warning']

    # Build header with status indicators
    header_parts = [f"{icon} {entry_label}"]

    if has_failure:
        header_parts.append("⚠️ Failure")
    if has_frustration:
        header_parts.append("😤 Frustrated")
    if has_positive:
        header_parts.append("✅ Positive")

    # Add excerpt preview
    excerpt = entry.get('message_excerpt') or entry.get('frustration_detail', '')
    if excerpt:
        excerpt_clean = clean_text(excerpt)[:60]
        if len(excerpt_clean) > 0:
            header_parts.append(f'"{excerpt_clean}..."')

    expander_title = " | ".join(header_parts)

    # Expand first 3 entries by default
    with st.expander(expander_title, expanded=(index < 3)):
        # Customer Voice Section (most important - show first)
        message_excerpt = entry.get('message_excerpt', '')
        if message_excerpt and has_frustration:
            st.markdown(f"""
            <div style="background: {COLORS['warning_tint']}; border-left: 4px solid {COLORS['warning']};
                        padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">
                <strong style="color: {COLORS['warning']};">Customer Message:</strong><br/>
                <p style="color: {COLORS['text']}; margin: 10px 0 0 0; font-style: italic;">
                    {message_excerpt}
                </p>
            </div>
            """, unsafe_allow_html=True)

        # Analysis section
        if summary:
            st.markdown(f"**Summary:** {summary}")

        if customer_tone:
            st.markdown(f"**Customer Tone:** {customer_tone}")

        # Issues detected section
        frustration_detail = clean_text(entry.get('frustration_detail', ''))
        if has_frustration and frustration_detail:
            st.markdown(f"""
            <div style="background: {COLORS['critical_tint']}; border-left: 4px solid {COLORS['critical']};
                        padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">
                <strong style="color: {COLORS['critical']};">😤 Frustration Detected:</strong>
                <p style="color: {COLORS['text']}; margin: 10px 0 0 0;">{frustration_detail}</p>
            </div>
            """, unsafe_allow_html=True)

        failure_detail = clean_text(entry.get('failure_pattern_detail', ''))
        if has_failure and failure_detail:
            st.markdown(f"""
            <div style="background: {COLORS['critical_tint']}; border-left: 4px solid {COLORS['critical']};
                        padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">
                <strong style="color: {COLORS['critical']};">⚠️ Failure Pattern:</strong>
                <p style="color: {COLORS['text']}; margin: 10px 0 0 0;">{failure_detail}</p>
            </div>
            """, unsafe_allow_html=True)

        # AI Insight
        analysis = clean_text(entry.get('analysis', ''))
        if analysis:
            st.markdown(f"""
            <div style="background: {COLORS['surface']}; border-left: 4px solid {COLORS['text_muted']};
                        padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">
                <strong style="color: {COLORS['text']};">AI Insight:</strong>
                <p style="color: {COLORS['text_muted']}; margin: 10px 0 0 0;">{analysis}</p>
            </div>
            """, unsafe_allow_html=True)

        # Positive actions
        positive_detail = clean_text(entry.get('positive_action_detail', ''))
        if has_positive and positive_detail:
            st.markdown(f"""
            <div style="background: {COLORS['success_tint']}; border-left: 4px solid {COLORS['success']};
                        padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">
                <strong style="color: {COLORS['success']};">✅ Positive Action:</strong>
                <p style="color: {COLORS['text']}; margin: 10px 0 0 0;">{positive_detail}</p>
            </div>
            """, unsafe_allow_html=True)

        positive_excerpt = entry.get('positive_excerpt', '')
        if positive_excerpt:
            st.markdown(f"""
            <div style="background: {COLORS['success_tint']}; border-left: 4px solid {COLORS['success']};
                        padding: 15px; margin: 10px 0; border-radius: 0 8px 8px 0;">
                <strong style="color: {COLORS['success']};">Customer Quote:</strong>
                <p style="color: {COLORS['text']}; margin: 10px 0 0 0; font-style: italic;">
                    {positive_excerpt}
                </p>
            </div>
            """, unsafe_allow_html=True)

        # Support quality and relationship impact
        col1, col2 = st.columns(2)

        with col1:
            support_quality = clean_text(entry.get('support_quality', ''))
            if support_quality:
                st.markdown(f"**Support Quality:** {support_quality}")

        with col2:
            relationship_impact = clean_text(entry.get('relationship_impact', ''))
            if relationship_impact:
                st.markdown(f"**Relationship Impact:** {relationship_impact}")


def display_timeline_summary(case: dict, deepseek: dict, claude: dict):
    """Display summary sections below the timeline."""

    st.markdown(f"<h3 style='color: {COLORS['text']}'>Summary</h3>", unsafe_allow_html=True)

    # Key customer quote
    key_phrase = claude.get('key_phrase', '')
    if key_phrase:
        st.markdown(f"""
        <div style="background: {COLORS['warning_tint']}; border-left: 4px solid {COLORS['warning']};
                    padding: 15px; margin-bottom: 1rem; border-radius: 0 8px 8px 0;">
            <strong style="color: {COLORS['warning']};">Key Customer Quote:</strong>
            <p style="color: {COLORS['text']}; margin: 10px 0 0 0; font-style: italic; font-size: 1.1rem;">
                "{key_phrase}"
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Executive summary
    exec_summary = deepseek.get('executive_summary', '') or deepseek.get('root_cause', '')
    if exec_summary:
        st.markdown(f"""
        <div style="background: {COLORS['surface']}; border-left: 4px solid {COLORS['primary']};
                    padding: 15px; margin-bottom: 1rem; border-radius: 0 8px 8px 0;">
            <strong style="color: {COLORS['primary']};">Executive Summary:</strong>
            <p style="color: {COLORS['text']}; margin: 10px 0 0 0;">{clean_text(exec_summary)}</p>
        </div>
        """, unsafe_allow_html=True)

    # Two-column layout for details
    col1, col2 = st.columns(2)

    with col1:
        # Pain points
        pain_points = deepseek.get('pain_points', '')
        if pain_points:
            st.markdown(f"""
            <div style="background: {COLORS['warning_tint']}; border-left: 4px solid {COLORS['warning']};
                        padding: 15px; margin-bottom: 1rem; border-radius: 0 8px 8px 0;">
                <strong style="color: {COLORS['warning']};">Pain Points:</strong>
                <p style="color: {COLORS['text']}; margin: 10px 0 0 0;">{clean_text(pain_points)}</p>
            </div>
            """, unsafe_allow_html=True)

        # Sentiment trend
        sentiment_trend = deepseek.get('sentiment_trend', '')
        if sentiment_trend:
            st.markdown(f"""
            <div style="background: {COLORS['surface']}; border-left: 4px solid {COLORS['secondary']};
                        padding: 15px; margin-bottom: 1rem; border-radius: 0 8px 8px 0;">
                <strong style="color: {COLORS['secondary']};">Sentiment Trend:</strong>
                <p style="color: {COLORS['text']}; margin: 10px 0 0 0;">{clean_text(sentiment_trend)}</p>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        # Recommended action
        recommended_action = deepseek.get('recommended_action', '')
        if recommended_action:
            st.markdown(f"""
            <div style="background: {COLORS['success_tint']}; border-left: 4px solid {COLORS['success']};
                        padding: 15px; margin-bottom: 1rem; border-radius: 0 8px 8px 0;">
                <strong style="color: {COLORS['success']};">Recommended Action:</strong>
                <p style="color: {COLORS['text']}; margin: 10px 0 0 0;">{clean_text(recommended_action)}</p>
            </div>
            """, unsafe_allow_html=True)

        # Customer priority
        priority = deepseek.get('customer_priority', '')
        if priority:
            priority_color = get_priority_color(priority)
            st.markdown(f"""
            <div style="background: {COLORS['surface']}; border-left: 4px solid {priority_color};
                        padding: 15px; margin-bottom: 1rem; border-radius: 0 8px 8px 0;">
                <strong style="color: {priority_color};">Customer Priority: {priority}</strong>
            </div>
            """, unsafe_allow_html=True)

    # Critical inflection points
    inflection_points = deepseek.get('critical_inflection_points', '')
    if inflection_points:
        st.markdown(f"""
        <div style="background: {COLORS['surface']}; border-left: 4px solid {COLORS['text_muted']};
                    padding: 15px; margin-top: 1rem; border-radius: 0 8px 8px 0;">
            <strong style="color: {COLORS['text']};">Critical Inflection Points:</strong>
            <p style="color: {COLORS['text_muted']}; margin: 10px 0 0 0;">{clean_text(inflection_points)}</p>
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
