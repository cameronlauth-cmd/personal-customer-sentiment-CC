"""
TrueNAS Enterprise Account Health Dashboard
Main Streamlit application entry point.
"""

import json
import streamlit as st
from pathlib import Path
import sys

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core import Config
from src.dashboard.branding import COLORS, get_health_color, get_health_status
from src.dashboard.styles import get_global_css


def get_available_analyses():
    """Get list of available analysis folders."""
    outputs_dir = Config.OUTPUT_DIR
    if not outputs_dir.exists():
        return []

    analyses = []
    for folder in sorted(outputs_dir.iterdir(), reverse=True):
        if folder.is_dir() and folder.name.startswith("analysis_"):
            summary_file = folder / "json" / "summary_statistics.json"
            if summary_file.exists():
                try:
                    with open(summary_file) as f:
                        data = json.load(f)
                    analyses.append({
                        "folder": folder,
                        "name": folder.name,
                        "account": data.get("account_name", "Unknown"),
                        "date": data.get("analysis_date", "Unknown"),
                        "health_score": data.get("account_health_score", 0),
                    })
                except Exception:
                    pass
    return analyses


def load_analysis_data(folder: Path):
    """Load all analysis data from a folder."""
    data = {}

    # Load summary statistics
    summary_file = folder / "json" / "summary_statistics.json"
    if summary_file.exists():
        with open(summary_file) as f:
            data["summary"] = json.load(f)

    # Load top 25 cases
    cases_file = folder / "json" / "top_25_critical_cases.json"
    if cases_file.exists():
        with open(cases_file) as f:
            data["cases"] = json.load(f)

    # Load all cases
    all_cases_file = folder / "json" / "all_cases.json"
    if all_cases_file.exists():
        with open(all_cases_file) as f:
            data["all_cases"] = json.load(f)

    # Get chart paths
    charts_dir = folder / "charts"
    if charts_dir.exists():
        data["charts"] = {
            f.stem: str(f) for f in charts_dir.glob("*.png")
        }

    return data


# Page configuration
st.set_page_config(
    page_title="TrueNAS Enterprise - Account Health",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply global TrueNAS branded dark theme
st.markdown(get_global_css(), unsafe_allow_html=True)

# Sidebar - Analysis Selection
st.sidebar.markdown(f"""
<div style="padding: 0.5rem 0; margin-bottom: 1rem;">
    <span style="font-size: 1.3rem; font-weight: 800; color: {COLORS['primary']};">TrueNAS</span>
    <span style="font-size: 1.3rem; font-weight: 800; color: {COLORS['white']};">Enterprise</span>
    <div style="color: {COLORS['text_muted']}; font-size: 0.85rem;">Account Health Dashboard</div>
</div>
""", unsafe_allow_html=True)

analyses = get_available_analyses()

if not analyses:
    st.sidebar.warning("No analyses found. Run an analysis first:")
    st.sidebar.code("python -m src.cli analyze 'input/data.xlsx'")
    st.title("TrueNAS Enterprise - Account Health")
    st.info("No analysis data available. Please run an analysis first using the CLI.")
    st.stop()

# Analysis selector
# Include timestamp in display to ensure uniqueness (prevents key collisions)
analysis_options = {
    f"{a['account']} ({a['name'][-6:]}) - {a['health_score']:.0f}/100": a
    for a in analyses
}

selected_label = st.sidebar.selectbox(
    "Select Analysis",
    options=list(analysis_options.keys()),
    index=0
)

selected_analysis = analysis_options[selected_label]
st.session_state["analysis_folder"] = selected_analysis["folder"]
st.session_state["analysis_data"] = load_analysis_data(selected_analysis["folder"])

# Display selected analysis info
st.sidebar.markdown("---")

health = selected_analysis['health_score']
health_color = get_health_color(health)
health_status = get_health_status(health)

st.sidebar.markdown(f"""
<div style="background-color: {COLORS['surface']}; padding: 1rem; border-radius: 8px;
            border-left: 3px solid {health_color};">
    <div style="color: {COLORS['text_muted']}; font-size: 0.85rem;">Account</div>
    <div style="color: {COLORS['white']}; font-weight: 600; margin-bottom: 0.75rem;">
        {selected_analysis['account']}
    </div>
    <div style="color: {COLORS['text_muted']}; font-size: 0.85rem;">Analysis Date</div>
    <div style="color: {COLORS['white']}; margin-bottom: 0.75rem;">
        {selected_analysis['date']}
    </div>
    <div style="color: {COLORS['text_muted']}; font-size: 0.85rem;">Health Score</div>
    <div style="color: {health_color}; font-size: 1.5rem; font-weight: 800;">
        {health:.0f}<span style="font-size: 1rem; color: {COLORS['text_muted']};">/100</span>
    </div>
    <div style="color: {health_color}; font-size: 0.9rem; font-weight: 600;">
        {health_status}
    </div>
</div>
""", unsafe_allow_html=True)

# Redirect to Overview page (the main dashboard view)
st.switch_page("pages/1_Overview.py")
