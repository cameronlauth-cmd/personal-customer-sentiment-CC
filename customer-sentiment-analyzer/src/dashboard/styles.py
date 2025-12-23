"""
Global CSS styles for Customer Sentiment Analyzer Dashboard.
Provides dark theme styling for all Streamlit components.
"""

from .branding import COLORS


def get_global_css() -> str:
    """Get global CSS for the dashboard.

    Returns:
        CSS string to inject via st.markdown
    """
    return f"""
    <style>
        /* Import Inter font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        /* Global styles */
        .stApp {{
            background-color: {COLORS["background"]};
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }}

        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            color: {COLORS["text"]};
            font-weight: 600;
        }}

        h1 {{
            color: {COLORS["primary"]};
        }}

        /* Paragraphs and text */
        p, span, label {{
            color: {COLORS["text"]};
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {COLORS["surface"]};
            border-right: 1px solid {COLORS["border"]};
        }}

        section[data-testid="stSidebar"] .stMarkdown {{
            color: {COLORS["text"]};
        }}

        /* Metrics */
        [data-testid="stMetricValue"] {{
            color: {COLORS["text"]};
            font-weight: 700;
        }}

        [data-testid="stMetricLabel"] {{
            color: {COLORS["text_muted"]};
        }}

        /* Expanders */
        .streamlit-expanderHeader {{
            background-color: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            color: {COLORS["text"]};
            font-weight: 500;
        }}

        .streamlit-expanderHeader:hover {{
            background-color: {COLORS["surface_light"]};
            border-color: {COLORS["primary"]};
        }}

        .streamlit-expanderContent {{
            background-color: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-top: none;
            border-radius: 0 0 8px 8px;
        }}

        /* Dataframes */
        .stDataFrame {{
            background-color: {COLORS["surface"]};
            border-radius: 8px;
        }}

        [data-testid="stDataFrame"] > div {{
            background-color: {COLORS["surface"]};
        }}

        /* Buttons */
        .stButton > button {{
            background-color: {COLORS["primary"]};
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.2s ease;
        }}

        .stButton > button:hover {{
            background-color: {COLORS["secondary"]};
            box-shadow: 0 4px 12px rgba(0, 149, 213, 0.3);
        }}

        /* Download buttons */
        .stDownloadButton > button {{
            background-color: {COLORS["success"]};
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 500;
        }}

        .stDownloadButton > button:hover {{
            background-color: #218838;
        }}

        /* Selectbox */
        .stSelectbox > div > div {{
            background-color: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            color: {COLORS["text"]};
        }}

        /* Slider */
        .stSlider > div > div > div {{
            background-color: {COLORS["primary"]};
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {COLORS["surface"]};
            border-radius: 8px;
            padding: 4px;
        }}

        .stTabs [data-baseweb="tab"] {{
            color: {COLORS["text_muted"]};
            font-weight: 500;
        }}

        .stTabs [aria-selected="true"] {{
            background-color: {COLORS["primary"]};
            color: white;
            border-radius: 6px;
        }}

        /* Dividers */
        hr {{
            border-color: {COLORS["border"]};
        }}

        /* Info/Warning/Error boxes */
        .stAlert {{
            border-radius: 8px;
        }}

        /* Progress bar */
        .stProgress > div > div {{
            background-color: {COLORS["primary"]};
        }}

        /* Spinner */
        .stSpinner > div {{
            border-top-color: {COLORS["primary"]};
        }}

        /* File uploader */
        [data-testid="stFileUploader"] {{
            background-color: {COLORS["surface"]};
            border: 2px dashed {COLORS["border"]};
            border-radius: 8px;
            padding: 1rem;
        }}

        [data-testid="stFileUploader"]:hover {{
            border-color: {COLORS["primary"]};
        }}

        /* Cards and containers */
        .css-1r6slb0, .css-12oz5g7 {{
            background-color: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
        }}

        /* Scrollbar styling */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}

        ::-webkit-scrollbar-track {{
            background: {COLORS["background"]};
        }}

        ::-webkit-scrollbar-thumb {{
            background: {COLORS["border"]};
            border-radius: 4px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: {COLORS["text_muted"]};
        }}

        /* Custom content boxes */
        .content-box-critical {{
            background-color: #2d1515;
            border-left: 4px solid {COLORS["critical"]};
            padding: 15px;
            border-radius: 0 8px 8px 0;
            margin: 10px 0;
        }}

        .content-box-warning {{
            background-color: #2d2315;
            border-left: 4px solid {COLORS["warning"]};
            padding: 15px;
            border-radius: 0 8px 8px 0;
            margin: 10px 0;
        }}

        .content-box-success {{
            background-color: #152d15;
            border-left: 4px solid {COLORS["success"]};
            padding: 15px;
            border-radius: 0 8px 8px 0;
            margin: 10px 0;
        }}

        .content-box-info {{
            background-color: {COLORS["surface"]};
            border-left: 4px solid {COLORS["primary"]};
            padding: 15px;
            border-radius: 0 8px 8px 0;
            margin: 10px 0;
        }}

        .content-box-neutral {{
            background-color: {COLORS["surface"]};
            border-left: 4px solid {COLORS["text_muted"]};
            padding: 15px;
            border-radius: 0 8px 8px 0;
            margin: 10px 0;
        }}
    </style>
    """


def get_plotly_theme() -> dict:
    """Get Plotly theme configuration for dark mode.

    Returns:
        Dictionary with Plotly layout settings
    """
    return {
        "paper_bgcolor": COLORS["background"],
        "plot_bgcolor": COLORS["surface"],
        "font": {
            "color": COLORS["text"],
            "family": "Inter, sans-serif",
        },
        "title": {
            "font": {
                "color": COLORS["text"],
                "size": 16,
            }
        },
        "xaxis": {
            "gridcolor": COLORS["border"],
            "linecolor": COLORS["border"],
            "tickcolor": COLORS["text_muted"],
        },
        "yaxis": {
            "gridcolor": COLORS["border"],
            "linecolor": COLORS["border"],
            "tickcolor": COLORS["text_muted"],
        },
        "legend": {
            "bgcolor": COLORS["surface"],
            "bordercolor": COLORS["border"],
            "font": {"color": COLORS["text"]},
        },
    }


def apply_plotly_theme(fig):
    """Apply dark theme to a Plotly figure.

    Args:
        fig: Plotly figure object

    Returns:
        Updated figure with theme applied
    """
    theme = get_plotly_theme()
    fig.update_layout(**theme)
    return fig
