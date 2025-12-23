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
        <div style="text-align: center; padding: 1rem 0; border-bottom: 1px solid {COLORS['border']}; margin-bottom: 1rem;">
            <h2 style="color: {COLORS['primary']}; margin: 0;">Customer Sentiment</h2>
            <p style="color: {COLORS['text_muted']}; margin: 5px 0 0 0; font-size: 0.9rem;">Analyzer Dashboard</p>
        </div>
        """, unsafe_allow_html=True)

        # API Key status (read from environment variable)
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            st.markdown(f"""
            <div style="background: #152d15; padding: 0.5rem 1rem; border-radius: 6px;
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

            if st.button("Clear Results", use_container_width=True):
                del st.session_state['analysis_results']
                if RESULTS_FILE.exists():
                    RESULTS_FILE.unlink()
                st.rerun()

    # Main content area
    # Check if we have results to display
    if 'analysis_results' in st.session_state:
        # Show navigation hint
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {COLORS['surface']} 0%, {COLORS['background']} 100%);
                    padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;
                    border: 1px solid {COLORS['border']}; border-left: 4px solid {COLORS['success']};">
            <h2 style="color: {COLORS['success']}; margin: 0;">Analysis Complete</h2>
            <p style="color: {COLORS['text_muted']}; margin: 10px 0 0 0;">
                Use the sidebar navigation to explore your results:
                <strong>Overview</strong>, <strong>Cases</strong>, <strong>Timeline</strong>,
                <strong>Trends</strong>, and <strong>Export</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Quick summary
        results = st.session_state['analysis_results']
        stats = results.get("statistics", {}).get("haiku", {})

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Cases", results.get("total_cases", 0))
        with col2:
            st.metric("High Frustration", stats.get("high_frustration", 0))
        with col3:
            st.metric("Avg Frustration", f"{stats.get('avg_frustration_score', 0):.1f}/10")
        with col4:
            st.metric("Analysis Time", f"{results.get('timing', {}).get('total_time', 0):.1f}s")

    else:
        # Show upload interface
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {COLORS['surface']} 0%, {COLORS['background']} 100%);
                    padding: 1.5rem; border-radius: 12px; margin-bottom: 1.5rem;
                    border: 1px solid {COLORS['border']}; border-left: 4px solid {COLORS['primary']};">
            <h1 style="color: {COLORS['primary']}; margin: 0; font-size: 1.8rem;">Customer Sentiment Analyzer</h1>
            <p style="color: {COLORS['text_muted']}; margin: 10px 0 0 0;">
                Hybrid AI Analysis: Claude Haiku (bulk) + Claude Sonnet (deep analysis)
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"<h3 style='color: {COLORS['text']}'>Upload Data</h3>", unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload Excel file with support case data",
            type=["xlsx", "xls"],
            help="Excel file with columns: Case Number, Customer Name, Message, Severity"
        )

        if uploaded_file is not None:
            st.success(f"Loaded: {uploaded_file.name}")

            # Analyze button
            if st.button("Run Analysis", type="primary", disabled=not api_key, use_container_width=True):
                if not api_key:
                    st.error("Please enter your Anthropic API key in the sidebar.")
                    return

                # Create progress containers
                progress_bar = st.progress(0)
                status_text = st.empty()

                def update_progress(message: str, progress: float):
                    """Callback for progress updates."""
                    progress_bar.progress(progress)
                    status_text.text(message)

                try:
                    # Run analysis
                    with st.spinner("Initializing..."):
                        analyzer = SentimentAnalyzer(
                            api_key=api_key,
                            progress_callback=update_progress
                        )

                    results = analyzer.analyze(
                        file=uploaded_file.getvalue(),
                        top_quick=top_quick,
                        top_detailed=top_detailed
                    )

                    # Clear progress
                    progress_bar.empty()
                    status_text.empty()

                    # Store results in session state and save to disk
                    st.session_state['analysis_results'] = results
                    save_results(results)

                    st.success(f"Analysis complete! Processed {results['total_cases']} cases.")
                    st.rerun()

                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"Analysis failed: {str(e)}")
                    st.exception(e)

        else:
            # Show instructions
            st.markdown(f"""
            <div style="background: {COLORS['surface']}; padding: 1.5rem; border-radius: 8px;
                        border: 1px solid {COLORS['border']}; margin-top: 1rem;">
                <h4 style="color: {COLORS['text']}; margin: 0 0 1rem 0;">Getting Started</h4>
                <ol style="color: {COLORS['text_muted']}; margin: 0; padding-left: 1.5rem;">
                    <li>Upload an Excel file with support case data</li>
                    <li>Click "Run Analysis" to start the 3-stage AI analysis</li>
                    <li>Explore results across the dashboard pages</li>
                </ol>
            </div>

            <div style="background: {COLORS['surface']}; padding: 1.5rem; border-radius: 8px;
                        border: 1px solid {COLORS['border']}; margin-top: 1rem;">
                <h4 style="color: {COLORS['text']}; margin: 0 0 1rem 0;">Analysis Pipeline</h4>
                <ul style="color: {COLORS['text_muted']}; margin: 0; padding-left: 1.5rem;">
                    <li><strong>Stage 1 - Claude Haiku:</strong> Message-by-message frustration scoring for all cases</li>
                    <li><strong>Stage 2A - Claude Sonnet:</strong> Quick pattern scoring for top cases</li>
                    <li><strong>Stage 2B - Claude Sonnet:</strong> Detailed timeline analysis for critical cases</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
