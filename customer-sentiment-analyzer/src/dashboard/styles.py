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
        /* Import Inter font - Professional typography */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Global styles - Enterprise design system */
        .stApp {{
            background-color: {COLORS["background"]};
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}

        /* Subtle transitions */
        *, *::before, *::after {{
            transition: background-color 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
        }}

        /* Headers - Clean enterprise typography */
        h1, h2, h3, h4, h5, h6 {{
            color: {COLORS["text"]};
            font-weight: 600;
            letter-spacing: -0.025em;
        }}

        h1 {{
            color: {COLORS["primary"]};
            font-weight: 600;
            font-size: 1.5rem;
        }}

        h2 {{
            font-size: 1.25rem;
            color: {COLORS["text"]};
        }}

        h3 {{
            font-size: 1rem;
            color: {COLORS["text"]};
        }}

        /* Paragraphs and text */
        p, span, label {{
            color: {COLORS["text"]};
        }}

        /* Sidebar - Clean enterprise styling */
        section[data-testid="stSidebar"] {{
            background: {COLORS["surface"]};
            border-right: 1px solid {COLORS["border"]};
        }}

        section[data-testid="stSidebar"] .stMarkdown {{
            color: {COLORS["text"]};
        }}

        /* Sidebar navigation links */
        section[data-testid="stSidebar"] a {{
            color: {COLORS["text_muted"]};
            text-decoration: none;
            transition: color 0.15s ease;
        }}

        section[data-testid="stSidebar"] a:hover {{
            color: {COLORS["primary"]};
        }}

        /* Metrics */
        [data-testid="stMetricValue"] {{
            color: {COLORS["text"]};
            font-weight: 600;
            font-size: 1.5rem;
        }}

        [data-testid="stMetricLabel"] {{
            color: {COLORS["text_muted"]};
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        /* Expanders - Clean card style */
        .streamlit-expanderHeader {{
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 8px;
            color: {COLORS["text"]};
            font-weight: 500;
        }}

        .streamlit-expanderHeader:hover {{
            background: {COLORS["surface_light"]};
            border-color: {COLORS["primary"]};
        }}

        .streamlit-expanderContent {{
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-top: none;
            border-radius: 0 0 8px 8px;
        }}

        /* Dataframes */
        .stDataFrame {{
            background-color: {COLORS["surface"]};
            border-radius: 8px;
            border: 1px solid {COLORS["border"]};
        }}

        [data-testid="stDataFrame"] > div {{
            background-color: {COLORS["surface"]};
        }}

        /* Buttons - Enterprise flat style */
        .stButton > button {{
            background: {COLORS["primary"]};
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 500;
            padding: 0.625rem 1.25rem;
            transition: all 0.15s ease;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }}

        .stButton > button:hover {{
            background: #2563eb;
            box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.25);
        }}

        .stButton > button:active {{
            background: #1d4ed8;
            box-shadow: none;
        }}

        /* Download buttons */
        .stDownloadButton > button {{
            background: {COLORS["accent"]};
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 500;
            padding: 0.625rem 1.25rem;
            transition: all 0.15s ease;
        }}

        .stDownloadButton > button:hover {{
            background: #059669;
            box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.25);
        }}

        /* Selectbox */
        .stSelectbox > div > div {{
            background: {COLORS["surface"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 6px;
            color: {COLORS["text"]};
        }}

        .stSelectbox > div > div:hover {{
            border-color: {COLORS["primary"]};
        }}

        /* Slider */
        .stSlider > div > div > div {{
            background-color: {COLORS["primary"]};
        }}

        .stSlider [data-baseweb="slider"] {{
            background: {COLORS["surface_light"]};
        }}

        /* Secondary/Danger buttons (for destructive actions) */
        .stButton > button[kind="secondary"],
        div[data-testid="stSidebar"] .stButton > button {{
            background: {COLORS["surface_light"]};
            color: {COLORS["text"]};
            border: 1px solid {COLORS["border"]};
        }}

        div[data-testid="stSidebar"] .stButton > button:hover {{
            background: {COLORS["surface"]};
            border-color: {COLORS["critical"]};
            color: {COLORS["critical"]};
        }}

        /* Tabs - Enterprise segmented control */
        .stTabs [data-baseweb="tab-list"] {{
            background: {COLORS["surface"]};
            border-radius: 8px;
            padding: 4px;
            border: 1px solid {COLORS["border"]};
            gap: 4px;
        }}

        .stTabs [data-baseweb="tab"] {{
            color: {COLORS["text_muted"]};
            font-weight: 500;
            border-radius: 6px;
            transition: all 0.15s ease;
        }}

        .stTabs [data-baseweb="tab"]:hover {{
            color: {COLORS["text"]};
            background: {COLORS["surface_light"]};
        }}

        .stTabs [aria-selected="true"] {{
            background: {COLORS["primary"]};
            color: white;
            border-radius: 6px;
        }}

        /* Dividers */
        hr {{
            border-color: {COLORS["border"]};
            opacity: 0.5;
        }}

        /* Info/Warning/Error boxes */
        .stAlert {{
            border-radius: 8px;
        }}

        /* Progress bar */
        .stProgress > div > div {{
            background-color: {COLORS["primary"]};
            border-radius: 4px;
        }}

        /* Spinner */
        .stSpinner > div {{
            border-top-color: {COLORS["primary"]};
        }}

        /* File uploader */
        [data-testid="stFileUploader"] {{
            background: {COLORS["surface"]};
            border: 2px dashed {COLORS["border"]};
            border-radius: 8px;
            padding: 1.5rem;
            transition: all 0.15s ease;
        }}

        [data-testid="stFileUploader"]:hover {{
            border-color: {COLORS["primary"]};
            background: rgba(59, 130, 246, 0.05);
        }}

        /* Radio buttons and checkboxes */
        .stRadio > div {{
            gap: 0.5rem;
        }}

        .stRadio label {{
            color: {COLORS["text"]};
        }}

        /* Success indicator badges */
        div[data-testid="stSidebar"] .stSuccess,
        .element-container:has(.stSuccess) {{
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid {COLORS["accent"]};
            border-radius: 6px;
        }}

        /* Sidebar metric cards */
        div[data-testid="stSidebar"] .stMetric {{
            background: {COLORS["surface"]};
            padding: 1rem;
            border-radius: 8px;
            border: 1px solid {COLORS["border"]};
        }}

        /* Info text in sidebar */
        div[data-testid="stSidebar"] small {{
            color: {COLORS["text_muted"]};
            font-size: 0.75rem;
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

        /* Custom content boxes - Enterprise style with subtle accents */
        .content-box-critical {{
            background: rgba(239, 68, 68, 0.08);
            border-left: 3px solid {COLORS["critical"]};
            padding: 1rem 1.25rem;
            border-radius: 0 8px 8px 0;
            margin: 0.75rem 0;
        }}

        .content-box-warning {{
            background: rgba(245, 158, 11, 0.08);
            border-left: 3px solid {COLORS["warning"]};
            padding: 1rem 1.25rem;
            border-radius: 0 8px 8px 0;
            margin: 0.75rem 0;
        }}

        .content-box-success {{
            background: rgba(16, 185, 129, 0.08);
            border-left: 3px solid {COLORS["success"]};
            padding: 1rem 1.25rem;
            border-radius: 0 8px 8px 0;
            margin: 0.75rem 0;
        }}

        .content-box-info {{
            background: rgba(59, 130, 246, 0.08);
            border-left: 3px solid {COLORS["primary"]};
            padding: 1rem 1.25rem;
            border-radius: 0 8px 8px 0;
            margin: 0.75rem 0;
        }}

        .content-box-neutral {{
            background: {COLORS["surface"]};
            border-left: 3px solid {COLORS["text_muted"]};
            padding: 1rem 1.25rem;
            border-radius: 0 8px 8px 0;
            margin: 0.75rem 0;
        }}

        /* Status indicator pills */
        .status-pill {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.025em;
        }}

        /* Table styling */
        table {{
            border-collapse: separate;
            border-spacing: 0;
        }}

        th {{
            background: {COLORS["surface"]};
            color: {COLORS["text_muted"]};
            font-weight: 500;
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 0.75rem 1rem;
            border-bottom: 1px solid {COLORS["border"]};
        }}

        td {{
            padding: 0.75rem 1rem;
            border-bottom: 1px solid {COLORS["border"]};
            color: {COLORS["text"]};
        }}

        tr:hover td {{
            background: {COLORS["surface_light"]};
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
            "family": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
            "size": 12,
        },
        "title": {
            "font": {
                "color": COLORS["text"],
                "size": 14,
                "weight": 600,
            },
            "x": 0,
            "xanchor": "left",
        },
        "xaxis": {
            "gridcolor": COLORS["border"],
            "linecolor": COLORS["border"],
            "tickcolor": COLORS["text_muted"],
            "tickfont": {"size": 11},
            "gridwidth": 1,
        },
        "yaxis": {
            "gridcolor": COLORS["border"],
            "linecolor": COLORS["border"],
            "tickcolor": COLORS["text_muted"],
            "tickfont": {"size": 11},
            "gridwidth": 1,
        },
        "legend": {
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": "rgba(0,0,0,0)",
            "font": {"color": COLORS["text"], "size": 11},
        },
        "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
        "colorway": [COLORS["primary"], COLORS["accent"], COLORS["secondary"],
                     COLORS["warning"], COLORS["critical"]],
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
