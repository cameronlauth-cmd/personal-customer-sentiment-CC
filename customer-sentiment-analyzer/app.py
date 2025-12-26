"""
Customer Sentiment Analyzer - Streamlit Application

A multi-page dashboard for analyzing TrueNAS customer support case data
for sentiment, frustration levels, and relationship health.

Run with: streamlit run app.py
"""

import os
import json
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Results persistence
RESULTS_FILE = Path(__file__).parent / "data" / "last_analysis.json"

# Import cache manager
from src.analysis_cache import AnalysisCache
from config.settings import CACHE_FILE, RECENT_WINDOW_DAYS, CLOSED_STATUSES, normalize_case_number
from src.dashboard.filters import filter_recent_issues


def save_results(results: dict):
    """Save analysis results to disk for persistence across refreshes."""
    RESULTS_FILE.parent.mkdir(exist_ok=True)
    with open(RESULTS_FILE, "w") as f:
        json.dump(results, f, default=str)


def load_results() -> dict | None:
    """Load saved analysis results from disk."""
    if RESULTS_FILE.exists():
        try:
            with open(RESULTS_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None

# Import our modules
from src.sentiment_analyzer import SentimentAnalyzer
from src.dashboard.branding import COLORS, get_health_color, get_health_status
from src.dashboard.styles import get_global_css

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Customer Sentiment Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply global CSS
st.markdown(get_global_css(), unsafe_allow_html=True)


def main():
    """Main application entry point - handles file upload and analysis."""

    # Load saved results on startup (persists across page refreshes)
    if 'analysis_results' not in st.session_state:
        saved = load_results()
        if saved:
            st.session_state['analysis_results'] = saved

    # Sidebar with branding and controls
    with st.sidebar:
        # Branding header
        st.markdown(f"""
        <div style="text-align: center; padding: 0.5rem 0; border-bottom: 1px solid {COLORS['border']}; margin-bottom: 0.75rem;">
            <h3 style="color: {COLORS['primary']}; margin: 0;">Customer Sentiment</h3>
        </div>
        """, unsafe_allow_html=True)

        # View Mode Toggle - synced across all pages via session state
        if 'view_mode' not in st.session_state:
            st.session_state['view_mode'] = 'All Cases'

        def on_view_mode_change():
            st.session_state['view_mode'] = st.session_state['view_mode_app']

        st.radio(
            "View Mode",
            ["Recent Issues", "All Cases"],
            index=0 if st.session_state['view_mode'] == 'Recent Issues' else 1,
            help="Recent Issues: Activity in last 14 days + negative sentiment",
            key="view_mode_app",
            on_change=on_view_mode_change
        )

        st.divider()

        # API Key status (read from environment variable)
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            st.markdown(f"""
            <div style="background: {COLORS['success_tint']}; padding: 0.5rem 1rem; border-radius: 6px;
                        border: 1px solid {COLORS['success']}; margin-bottom: 0.5rem;">
                <span style="color: {COLORS['success']};">&#10003; API Key Configured</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("API key not found. Set ANTHROPIC_API_KEY in .env file.")

        st.divider()

        # Analysis parameters
        st.markdown(f"<p style='color: {COLORS['text']}; font-weight: 600;'>Analysis Parameters</p>", unsafe_allow_html=True)

        top_quick = st.slider(
            "Quick Scoring (Top N)",
            min_value=5,
            max_value=50,
            value=25,
            help="Cases for Stage 2A quick scoring"
        )

        top_detailed = st.slider(
            "Timeline Analysis (Top N)",
            min_value=3,
            max_value=20,
            value=10,
            help="Cases for Stage 2B detailed timeline"
        )

        st.divider()

        # Show analysis status if results exist
        if 'analysis_results' in st.session_state:
            results = st.session_state['analysis_results']
            health_score = results.get('account_health_score', 0)
            health_color = get_health_color(health_score)
            health_status = get_health_status(health_score)

            st.markdown(f"""
            <div style="background: {COLORS['surface']}; padding: 1rem; border-radius: 8px;
                        border: 1px solid {COLORS['border']}; text-align: center;">
                <p style="color: {COLORS['text_muted']}; margin: 0; font-size: 0.8rem;">Account Health</p>
                <p style="color: {health_color}; margin: 5px 0; font-size: 2rem; font-weight: bold;">{health_score:.0f}</p>
                <p style="color: {health_color}; margin: 0; font-size: 0.9rem;">{health_status}</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style="margin-top: 1rem; padding: 0.5rem; background: {COLORS['surface']};
                        border-radius: 6px; border: 1px solid {COLORS['border']};">
                <p style="color: {COLORS['text_muted']}; margin: 0; font-size: 0.75rem;">
                    {results.get('total_cases', 0)} cases analyzed<br/>
                    {results.get('timing', {}).get('total_time', 0):.1f}s total time
                </p>
            </div>
            """, unsafe_allow_html=True)

            st.divider()

            if st.button("Clear Results", use_container_width=True):
                del st.session_state['analysis_results']
                if RESULTS_FILE.exists():
                    RESULTS_FILE.unlink()
                st.rerun()

            # Filter Diagnostics Panel
            st.divider()
            with st.expander("Filter Diagnostics"):
                from src.dashboard.filters import diagnose_filter
                cases = results.get('cases', [])
                diagnostics = diagnose_filter(cases)

                included = [d for d in diagnostics if d['status'] == 'INCLUDED']
                excluded = [d for d in diagnostics if d['status'] == 'EXCLUDED']

                st.write(f"**Recent Issues:** {len(included)} cases")
                st.write(f"**Excluded:** {len(excluded)} cases")

                # Show cases that might be problematic
                no_date_data = [d for d in diagnostics if d['days_since_last_message'] is None]
                if no_date_data:
                    st.warning(f"{len(no_date_data)} cases missing message date data")
                    for d in no_date_data[:3]:
                        st.caption(f"- {d['case_number']}: {d['reason']}")

                old_but_included = [d for d in diagnostics
                                    if d['days_since_last_message'] and d['days_since_last_message'] > RECENT_WINDOW_DAYS
                                    and d['status'] == 'INCLUDED']
                if old_but_included:
                    st.error(f"BUG: {len(old_but_included)} old cases incorrectly included!")
                    for d in old_but_included[:5]:
                        st.caption(f"- {d['case_number']}: {d['reason']}")

    # Main content area
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {COLORS['surface']} 0%, {COLORS['background']} 100%);
                padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;
                border: 1px solid {COLORS['border']}; border-left: 4px solid {COLORS['primary']};">
        <h1 style="color: {COLORS['primary']}; margin: 0; font-size: 1.8rem;">Customer Sentiment Analyzer</h1>
        <p style="color: {COLORS['text_muted']}; margin: 10px 0 0 0;">
            Cache-first analysis with incremental updates
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Initialize cache
    cache = AnalysisCache(CACHE_FILE)
    cache_stats = cache.get_cache_stats()

    # Show cache status
    if cache_stats["total_cases"] > 0:
        st.markdown(f"""
        <div style="background: {COLORS['success_tint']}; padding: 0.75rem 1rem; border-radius: 6px;
                    border: 1px solid {COLORS['success']}; margin-bottom: 1rem;">
            <span style="color: {COLORS['success']};">&#128202; Cache: {cache_stats['open_cases']} open cases, {cache_stats['closed_cases']} closed</span>
        </div>
        """, unsafe_allow_html=True)

    # Action selector
    st.markdown(f"<h3 style='color: {COLORS['text']}'>Select Action</h3>", unsafe_allow_html=True)

    action = st.radio(
        "What would you like to do?",
        ["View Cached Cases", "Upload Open Cases", "Upload Closed Cases"],
        horizontal=True,
        help="View existing analysis or upload new data"
    )

    # Handle each action
    if action == "View Cached Cases":
        if cache_stats["total_cases"] == 0:
            st.info("No cached cases found. Upload an Excel file to start analyzing.")
        else:
            if st.button("Load Dashboard", type="primary", use_container_width=True):
                # Convert cache to analysis results format
                cases = cache.export_for_dashboard(include_closed=False)

                # Build results structure compatible with existing dashboard
                results = {
                    "cases": cases,
                    "total_cases": len(cases),
                    "source": "cache",
                    "statistics": {
                        "haiku": {
                            "high_frustration": sum(1 for c in cases if c.get("recent_frustration_14d", 0) >= 7),
                            "avg_frustration_score": sum(c.get("recent_frustration_14d", 0) for c in cases) / len(cases) if cases else 0
                        }
                    },
                    "timing": {"total_time": 0}
                }

                st.session_state['analysis_results'] = results
                save_results(results)
                st.success(f"Loaded {len(cases)} cases from cache.")
                st.rerun()

            # Show attention-needed cases
            attention_cases = cache.get_cases_needing_attention(RECENT_WINDOW_DAYS)
            if attention_cases:
                st.markdown(f"<h4 style='color: {COLORS['warning']}'>⚠️ Cases Needing Attention ({len(attention_cases)})</h4>", unsafe_allow_html=True)
                for case in attention_cases[:5]:
                    metrics = case.get("calculated_metrics", {})
                    trend_icon = "📉" if metrics.get("trend") == "declining" else "📊"
                    st.markdown(f"""
                    <div style="background: {COLORS['surface']}; padding: 0.75rem; border-radius: 6px;
                                border-left: 3px solid {COLORS['warning']}; margin-bottom: 0.5rem;">
                        <strong style="color: {COLORS['text']};">{case.get('customer_name', 'Unknown')}</strong>
                        <span style="color: {COLORS['text']};">- Case {case.get('case_number')}</span><br/>
                        <span style="color: {COLORS['text_muted']};">
                            {trend_icon} Recent frustration: {metrics.get('recent_frustration', 0)}/10 |
                            Trend: {metrics.get('trend', 'stable')}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)

    elif action == "Upload Open Cases":
        uploaded_file = st.file_uploader(
            "Upload Excel file with open support cases",
            type=["xlsx", "xls"],
            help="Excel file with columns: Case Number, Customer Name, Message, Severity, Message Date"
        )

        if uploaded_file is not None:
            st.success(f"Loaded: {uploaded_file.name}")

            col1, col2 = st.columns(2)
            with col1:
                force_full = st.checkbox(
                    "Force full re-analysis",
                    help="Re-analyze all messages even if cached (rebuilds cache)"
                )
            with col2:
                incremental = st.checkbox(
                    "Incremental mode",
                    value=True,
                    help="Only analyze new messages (uses cached context)",
                    disabled=force_full
                )

            if st.button("Run Analysis", type="primary", disabled=not api_key, use_container_width=True):
                if not api_key:
                    st.error("Please set ANTHROPIC_API_KEY in .env file.")
                    return

                progress_bar = st.progress(0)
                status_text = st.empty()

                def update_progress(message: str, progress: float):
                    progress_bar.progress(progress)
                    status_text.text(message)

                try:
                    with st.spinner("Initializing..."):
                        analyzer = SentimentAnalyzer(
                            api_key=api_key,
                            progress_callback=update_progress
                        )

                    # Pass cache and mode to analyzer
                    results = analyzer.analyze(
                        file=uploaded_file.getvalue(),
                        top_quick=top_quick,
                        top_detailed=top_detailed,
                        cache=cache if not force_full else None,
                        incremental=incremental and not force_full
                    )

                    # Save updated cache
                    cache.save_cache()

                    progress_bar.empty()
                    status_text.empty()

                    st.session_state['analysis_results'] = results
                    save_results(results)

                    st.success(f"Analysis complete! Processed {results['total_cases']} cases.")
                    st.rerun()

                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"Analysis failed: {str(e)}")
                    st.exception(e)

    elif action == "Upload Closed Cases":
        st.markdown(f"""
        <div style="background: {COLORS['surface']}; padding: 1rem; border-radius: 8px;
                    border: 1px solid {COLORS['border']}; margin-bottom: 1rem;">
            <p style="color: {COLORS['text_muted']}; margin: 0;">
                Upload a report of closed cases to update their status in the cache.
                Cases with status matching: {', '.join(CLOSED_STATUSES[:3])}... will be marked closed.
            </p>
        </div>
        """, unsafe_allow_html=True)

        closed_file = st.file_uploader(
            "Upload Excel file with closed cases",
            type=["xlsx", "xls"],
            help="Excel file with Case Number and Status columns",
            key="closed_upload"
        )

        if closed_file is not None:
            st.success(f"Loaded: {closed_file.name}")

            if st.button("Update Closed Cases", type="primary", use_container_width=True):
                try:
                    import pandas as pd
                    from src.data_loader import DataLoader

                    # Load the closed cases file
                    loader = DataLoader()
                    df = loader.load_excel(closed_file.getvalue())

                    # Find case numbers with closed status (normalize for consistent matching)
                    closed_case_numbers = []
                    for _, row in df.iterrows():
                        status = str(row.get("Status", "")).strip()
                        case_num = normalize_case_number(row.get("Case Number", ""))
                        if status in CLOSED_STATUSES and case_num:
                            closed_case_numbers.append(case_num)

                    # Update cache
                    unique_closed = list(set(closed_case_numbers))
                    updated = cache.mark_cases_closed(unique_closed)
                    cache.save_cache()

                    st.success(f"Marked {updated} cases as closed in cache.")

                except Exception as e:
                    st.error(f"Failed to process closed cases: {str(e)}")
                    st.exception(e)

    # Show results if available
    if 'analysis_results' in st.session_state:
        st.divider()
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {COLORS['surface']} 0%, {COLORS['background']} 100%);
                    padding: 1rem; border-radius: 8px; margin-bottom: 1rem;
                    border: 1px solid {COLORS['border']}; border-left: 4px solid {COLORS['success']};">
            <h3 style="color: {COLORS['success']}; margin: 0;">✓ Results Ready</h3>
            <p style="color: {COLORS['text_muted']}; margin: 5px 0 0 0;">
                Use sidebar navigation: <strong style="color: {COLORS['text']};">Overview</strong>, <strong style="color: {COLORS['text']};">Cases</strong>,
                <strong style="color: {COLORS['text']};">Timeline</strong>, <strong style="color: {COLORS['text']};">Trends</strong>, <strong style="color: {COLORS['text']};">Export</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)

        results = st.session_state['analysis_results']
        stats = results.get("statistics", {}).get("haiku", {})
        total_cases = results.get("total_cases", 0)
        high_frust = stats.get("high_frustration", 0)
        avg_frust = stats.get("avg_frustration_score", 0)

        # Hero metrics for quick summary
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="hero-metric">
                <div class="hero-metric-value" style="color: {COLORS['primary']};">{total_cases}</div>
                <div class="hero-metric-label">Total Cases</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            high_color = COLORS['critical'] if high_frust > 0 else COLORS['success']
            st.markdown(f"""
            <div class="hero-metric" style="border-color: {high_color}; border-width: 2px;">
                <div class="hero-metric-value" style="color: {high_color};">{high_frust}</div>
                <div class="hero-metric-label">High Frustration</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            frust_color = COLORS['critical'] if avg_frust >= 7 else (COLORS['warning'] if avg_frust >= 4 else COLORS['success'])
            st.markdown(f"""
            <div class="hero-metric">
                <div class="hero-metric-value" style="color: {frust_color};">{avg_frust:.1f}</div>
                <div class="hero-metric-label">Avg Frustration /10</div>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            source = results.get("source", "analysis")
            st.markdown(f"""
            <div class="hero-metric">
                <div class="hero-metric-value" style="color: {COLORS['text']}; font-size: 1.5rem;">{source.title()}</div>
                <div class="hero-metric-label">Data Source</div>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
