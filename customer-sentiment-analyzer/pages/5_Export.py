"""
Export Page - Export analysis results in various formats.
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dashboard.branding import COLORS
from src.dashboard.styles import get_global_css
from src.dashboard.filters import get_filtered_cases, get_view_mode_indicator_html
from src.report_generator import generate_html_report, ReportGenerationError

# Page config
st.set_page_config(
    page_title="Export - Customer Sentiment",
    page_icon="📤",
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
        st.session_state['view_mode'] = st.session_state['view_mode_export']

    st.radio(
        "View Mode",
        ["Recent Issues", "All Cases"],
        index=0 if st.session_state['view_mode'] == 'Recent Issues' else 1,
        help="Recent Issues: Activity in last 14 days + negative sentiment",
        key="view_mode_export",
        on_change=on_view_mode_change
    )


def generate_csv_export(cases: list) -> str:
    """Generate CSV export of case data."""
    if not cases:
        return "No cases to export"

    rows = []
    for case in cases:
        # Use 'or {}' pattern to handle None values
        claude = case.get("claude_analysis") or {}
        quick = case.get("deepseek_quick_scoring") or {}
        deepseek = case.get("deepseek_analysis") or {}

        rows.append({
            "Case Number": case.get("case_number", ""),
            "Customer Name": case.get("customer_name", ""),
            "Severity": case.get("severity", ""),
            "Case Age (days)": case.get("case_age_days", 0),
            "Messages": case.get("interaction_count", 0),
            "Criticality Score": round(case.get("criticality_score", 0) or 0, 1),
            "Frustration Score": claude.get("frustration_score", 0),
            "Issue Class": claude.get("issue_class", ""),
            "Resolution Outlook": claude.get("resolution_outlook", ""),
            "Priority": quick.get("priority", ""),
            "Key Phrase": claude.get("key_phrase", ""),
            "Has Timeline": "Yes" if deepseek.get("timeline_entries") else "No",
            "Timeline Entries": len(deepseek.get("timeline_entries") or []),
            "Executive Summary": deepseek.get("executive_summary", ""),
        })

    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


def generate_json_export(results: dict) -> str:
    """Generate JSON export of full analysis results."""
    return json.dumps(results, indent=2, default=str)


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
        <h1 style="color: {COLORS['primary']}; margin: 0; font-size: 1.8rem;">Export Results</h1>
        <p style="color: {COLORS['text_muted']}; margin: 10px 0 0 0;">
            Download analysis results in various formats
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Export options
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div style="background: {COLORS['surface']}; padding: 1.5rem; border-radius: 8px;
                    border: 1px solid {COLORS['border']}; height: 200px;">
            <h4 style="color: {COLORS['text']}; margin: 0 0 10px 0;">CSV Export</h4>
            <p style="color: {COLORS['text_muted']}; font-size: 0.9rem;">
                Spreadsheet-friendly format with case data, scores, and key metrics.
                Ideal for further analysis in Excel or Google Sheets.
            </p>
        </div>
        """, unsafe_allow_html=True)

        try:
            csv_data = generate_csv_export(cases)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"sentiment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"CSV generation failed: {e}")

    with col2:
        st.markdown(f"""
        <div style="background: {COLORS['surface']}; padding: 1.5rem; border-radius: 8px;
                    border: 1px solid {COLORS['border']}; height: 200px;">
            <h4 style="color: {COLORS['text']}; margin: 0 0 10px 0;">JSON Export</h4>
            <p style="color: {COLORS['text_muted']}; font-size: 0.9rem;">
                Complete analysis data including all AI insights, timelines,
                and detailed metrics. Best for programmatic access.
            </p>
        </div>
        """, unsafe_allow_html=True)

        try:
            json_data = generate_json_export(results)
            st.download_button(
                label="Download JSON",
                data=json_data,
                file_name=f"sentiment_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"JSON generation failed: {e}")

    with col3:
        st.markdown(f"""
        <div style="background: {COLORS['surface']}; padding: 1.5rem; border-radius: 8px;
                    border: 1px solid {COLORS['border']}; height: 200px;">
            <h4 style="color: {COLORS['text']}; margin: 0 0 10px 0;">HTML Report</h4>
            <p style="color: {COLORS['text_muted']}; font-size: 0.9rem;">
                Professional report with charts, executive summaries, and detailed timelines.
                Ready to share with stakeholders.
            </p>
        </div>
        """, unsafe_allow_html=True)

        try:
            html_data = generate_html_report(results)
            st.download_button(
                label="Download HTML",
                data=html_data,
                file_name=f"sentiment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                mime="text/html",
                use_container_width=True
            )
        except ReportGenerationError as e:
            st.error(f"HTML report generation failed: {e}")
        except Exception as e:
            st.error(f"Unexpected error generating HTML report: {e}")

    st.divider()

    # Analysis summary
    st.markdown(f"<h3 style='color: {COLORS['text']}'>Export Preview</h3>", unsafe_allow_html=True)

    stats = results.get("statistics", {}).get("haiku", {})
    timing = results.get("timing", {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"""
        <div style="background: {COLORS['surface']}; padding: 1rem; border-radius: 8px;
                    border: 1px solid {COLORS['border']};">
            <h5 style="color: {COLORS['primary']}; margin: 0 0 10px 0;">Data Summary</h5>
            <p style="color: {COLORS['text']}; margin: 5px 0;">Total Cases: <strong>{len(cases)}</strong></p>
            <p style="color: {COLORS['text']}; margin: 5px 0;">Cases with Timelines: <strong>{sum(1 for c in cases if c.get('deepseek_analysis', {}).get('timeline_entries'))}</strong></p>
            <p style="color: {COLORS['text']}; margin: 5px 0;">High Frustration: <strong>{stats.get('high_frustration', 0)}</strong></p>
            <p style="color: {COLORS['text']}; margin: 5px 0;">Messages Analyzed: <strong>{stats.get('total_messages_analyzed', 0)}</strong></p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div style="background: {COLORS['surface']}; padding: 1rem; border-radius: 8px;
                    border: 1px solid {COLORS['border']};">
            <h5 style="color: {COLORS['primary']}; margin: 0 0 10px 0;">Analysis Metadata</h5>
            <p style="color: {COLORS['text']}; margin: 5px 0;">Health Score: <strong>{results.get('account_health_score', 0):.0f}</strong></p>
            <p style="color: {COLORS['text']}; margin: 5px 0;">Analysis Time: <strong>{timing.get('total_time', 0):.1f}s</strong></p>
            <p style="color: {COLORS['text']}; margin: 5px 0;">Avg Frustration: <strong>{stats.get('avg_frustration_score', 0):.1f}/10</strong></p>
            <p style="color: {COLORS['text']}; margin: 5px 0;">Generated: <strong>{datetime.now().strftime('%Y-%m-%d %H:%M')}</strong></p>
        </div>
        """, unsafe_allow_html=True)

    # Preview table
    st.divider()
    st.markdown(f"<h4 style='color: {COLORS['text']}'>Case Data Preview</h4>", unsafe_allow_html=True)

    preview_data = []
    for case in cases[:10]:
        claude = case.get("claude_analysis", {})
        preview_data.append({
            "Case #": case.get("case_number"),
            "Customer": str(case.get("customer_name", ""))[:30],
            "Severity": case.get("severity"),
            "Criticality": round(case.get("criticality_score", 0), 1),
            "Frustration": claude.get("frustration_score", 0),
            "Issue Class": claude.get("issue_class", ""),
        })

    if preview_data:
        df = pd.DataFrame(preview_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown(f"<p style='color: {COLORS['text_muted']}; font-size: 0.9rem;'>Showing first 10 of {len(cases)} cases</p>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
