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
        /* Import Inter font - Matches TrueNAS site typography */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

        /* Global styles - TrueNAS + Apple fusion */
        .stApp {{
            background-color: {COLORS["background"]};
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Segoe UI', Roboto, sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            letter-spacing: -0.01em;
        }}

        /* Apple-style transitions - smooth cubic-bezier */
        *, *::before, *::after {{
            transition: background-color 0.3s cubic-bezier(0.4, 0, 0.6, 1),
                        border-color 0.3s cubic-bezier(0.4, 0, 0.6, 1),
                        box-shadow 0.3s cubic-bezier(0.4, 0, 0.6, 1),
                        color 0.3s cubic-bezier(0.4, 0, 0.6, 1),
                        opacity 0.3s cubic-bezier(0.4, 0, 0.6, 1);
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
            color: {COLORS["text_muted"]} !important;
            text-decoration: none;
            transition: color 0.15s ease;
        }}

        section[data-testid="stSidebar"] a:hover {{
            color: {COLORS["primary"]} !important;
        }}

        /* Streamlit multi-page navigation - Force light theme */
        [data-testid="stSidebarNav"] {{
            background: {COLORS["surface"]} !important;
        }}

        [data-testid="stSidebarNav"] li {{
            background: transparent !important;
        }}

        [data-testid="stSidebarNav"] a {{
            color: {COLORS["text_muted"]} !important;
            background: transparent !important;
        }}

        [data-testid="stSidebarNav"] a:hover {{
            color: {COLORS["primary"]} !important;
            background: {COLORS["surface_light"]} !important;
        }}

        [data-testid="stSidebarNav"] a[aria-selected="true"] {{
            background: {COLORS["surface_light"]} !important;
            color: {COLORS["text"]} !important;
        }}

        [data-testid="stSidebarNav"] span {{
            color: inherit !important;
        }}

        /* Fix sidebar nav container backgrounds */
        [data-testid="stSidebarNavItems"],
        [data-testid="stSidebarNavSeparator"],
        section[data-testid="stSidebar"] > div {{
            background: {COLORS["surface"]} !important;
        }}

        /* Ensure all sidebar text is visible */
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label {{
            color: {COLORS["text"]} !important;
        }}

        /* Metrics - Larger for executive visibility */
        [data-testid="stMetricValue"] {{
            color: {COLORS["text"]};
            font-weight: 700;
            font-size: 2.25rem;
            line-height: 1.1;
        }}

        [data-testid="stMetricLabel"] {{
            color: {COLORS["text_muted"]};
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 500;
        }}

        [data-testid="stMetricDelta"] {{
            font-size: 0.9rem;
            font-weight: 600;
        }}

        /* Hero metrics - Extra large for key KPIs */
        .hero-metric {{
            background: {COLORS["surface"]};
            border-radius: 16px;
            padding: 1.5rem 2rem;
            border: 1px solid {COLORS["border"]};
            box-shadow: {COLORS["shadow"]};
            text-align: center;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.6, 1);
        }}

        .hero-metric:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }}

        .hero-metric-value {{
            font-size: 3rem;
            font-weight: 700;
            line-height: 1;
            letter-spacing: -0.02em;
        }}

        .hero-metric-label {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: {COLORS["text_muted"]};
            font-weight: 500;
            margin-top: 0.5rem;
        }}

        /* Trend indicators with bold backgrounds */
        .trend-up {{
            background: {COLORS["success_tint"]};
            border: 2px solid {COLORS["success"]};
            border-radius: 12px;
            padding: 1rem 1.5rem;
        }}

        .trend-down {{
            background: {COLORS["critical_tint"]};
            border: 2px solid {COLORS["critical"]};
            border-radius: 12px;
            padding: 1rem 1.5rem;
        }}

        .trend-neutral {{
            background: {COLORS["surface"]};
            border: 2px solid {COLORS["border"]};
            border-radius: 12px;
            padding: 1rem 1.5rem;
        }}

        /* Section headers - Bolder and more prominent */
        .section-header {{
            color: {COLORS["text"]};
            font-size: 1.25rem;
            font-weight: 600;
            letter-spacing: -0.02em;
            margin: 1.5rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid {COLORS["border"]};
        }}

        .section-subheader {{
            color: {COLORS["text_muted"]};
            font-size: 0.9rem;
            margin-top: -0.75rem;
            margin-bottom: 1rem;
        }}

        /* Expanders - Clean card style for light theme */
        .streamlit-expanderHeader {{
            background: {COLORS["surface"]} !important;
            border: 1px solid {COLORS["border"]} !important;
            border-radius: 8px;
            color: {COLORS["text"]} !important;
            font-weight: 500;
        }}

        .streamlit-expanderHeader:hover {{
            background: {COLORS["surface_light"]} !important;
            border-color: {COLORS["primary"]} !important;
        }}

        .streamlit-expanderContent {{
            background: {COLORS["background"]} !important;
            border: 1px solid {COLORS["border"]} !important;
            border-top: none;
            border-radius: 0 0 8px 8px;
        }}

        /* Expander text visibility */
        .streamlit-expanderHeader span,
        .streamlit-expanderHeader p {{
            color: {COLORS["text"]} !important;
        }}

        /* Streamlit expander modern selectors */
        [data-testid="stExpander"] {{
            background: {COLORS["background"]} !important;
            border: 1px solid {COLORS["border"]} !important;
            border-radius: 8px;
        }}

        [data-testid="stExpander"] summary {{
            background: {COLORS["surface"]} !important;
            color: {COLORS["text"]} !important;
        }}

        [data-testid="stExpander"] summary:hover {{
            background: {COLORS["surface_light"]} !important;
        }}

        [data-testid="stExpander"] summary span {{
            color: {COLORS["text"]} !important;
        }}

        /* Dataframes - iX Blue Theme */
        .stDataFrame {{
            background-color: {COLORS["background"]};
            border-radius: 8px;
            border: 1px solid {COLORS["border"]};
        }}

        [data-testid="stDataFrame"] > div {{
            background-color: {COLORS["background"]};
        }}

        /* Dataframe header - iX Blue */
        [data-testid="stDataFrame"] thead tr th {{
            background-color: {COLORS["primary"]} !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 0.75rem 1rem !important;
            border-bottom: 2px solid #0080b8 !important;
        }}

        /* Dataframe cells */
        [data-testid="stDataFrame"] tbody tr td {{
            color: {COLORS["text"]} !important;
            background-color: {COLORS["background"]} !important;
            padding: 0.5rem 1rem !important;
            border-bottom: 1px solid {COLORS["border"]} !important;
        }}

        /* Dataframe row hover */
        [data-testid="stDataFrame"] tbody tr:hover td {{
            background-color: {COLORS["surface"]} !important;
        }}

        /* Dataframe selected row */
        [data-testid="stDataFrame"] tbody tr[data-selected="true"] td {{
            background-color: rgba(0, 149, 213, 0.15) !important;
            border-left: 3px solid {COLORS["primary"]} !important;
        }}

        /* Progress columns in dataframe */
        [data-testid="stDataFrame"] [role="progressbar"] {{
            background-color: {COLORS["surface_light"]} !important;
        }}

        [data-testid="stDataFrame"] [role="progressbar"] > div {{
            background-color: {COLORS["primary"]} !important;
        }}

        /* Buttons - TrueNAS rounded style with Apple transitions */
        .stButton > button {{
            background: {COLORS["primary"]};
            color: white;
            border: none;
            border-radius: 30px;
            font-weight: 500;
            padding: 0.75rem 1.5rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.6, 1);
            box-shadow: 0 1px 2px rgba(0, 149, 213, 0.15);
            letter-spacing: 0;
        }}

        .stButton > button:hover {{
            background: #0080b8;
            box-shadow: 0 4px 12px rgba(0, 149, 213, 0.25);
            transform: translateY(-1px);
        }}

        .stButton > button:active {{
            background: #006699;
            box-shadow: none;
            transform: translateY(0);
        }}

        /* Download buttons - TrueNAS green */
        .stDownloadButton > button {{
            background: {COLORS["accent"]};
            color: white;
            border: none;
            border-radius: 30px;
            font-weight: 500;
            padding: 0.75rem 1.5rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.6, 1);
            box-shadow: 0 1px 2px rgba(113, 191, 68, 0.15);
        }}

        .stDownloadButton > button:hover {{
            background: #5a9e32;
            box-shadow: 0 4px 12px rgba(113, 191, 68, 0.25);
            transform: translateY(-1px);
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

        /* Secondary/Sidebar buttons - Light theme outline style */
        .stButton > button[kind="secondary"],
        div[data-testid="stSidebar"] .stButton > button {{
            background: {COLORS["background"]};
            color: {COLORS["text"]};
            border: 1px solid {COLORS["border"]};
            border-radius: 30px;
        }}

        div[data-testid="stSidebar"] .stButton > button:hover {{
            background: {COLORS["surface"]};
            border-color: {COLORS["primary"]};
            color: {COLORS["primary"]};
        }}

        /* Tabs - TrueNAS pill-style with Apple transitions */
        .stTabs [data-baseweb="tab-list"] {{
            background: {COLORS["surface"]};
            border-radius: 30px;
            padding: 4px;
            border: 1px solid {COLORS["border"]};
            gap: 4px;
        }}

        .stTabs [data-baseweb="tab"] {{
            color: {COLORS["text_muted"]};
            font-weight: 500;
            border-radius: 30px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.6, 1);
        }}

        .stTabs [data-baseweb="tab"]:hover {{
            color: {COLORS["text"]};
            background: {COLORS["surface_light"]};
        }}

        .stTabs [aria-selected="true"] {{
            background: {COLORS["primary"]};
            color: white;
            border-radius: 30px;
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

        /* Custom content boxes - Light theme with TrueNAS colors */
        .content-box-critical {{
            background: {COLORS["critical_tint"]};
            border-left: 3px solid {COLORS["critical"]};
            padding: 1rem 1.25rem;
            border-radius: 0 12px 12px 0;
            margin: 0.75rem 0;
        }}

        .content-box-warning {{
            background: {COLORS["warning_tint"]};
            border-left: 3px solid {COLORS["warning"]};
            padding: 1rem 1.25rem;
            border-radius: 0 12px 12px 0;
            margin: 0.75rem 0;
        }}

        .content-box-success {{
            background: {COLORS["success_tint"]};
            border-left: 3px solid {COLORS["success"]};
            padding: 1rem 1.25rem;
            border-radius: 0 12px 12px 0;
            margin: 0.75rem 0;
        }}

        .content-box-info {{
            background: {COLORS["cyan_tint"]};
            border-left: 3px solid {COLORS["primary"]};
            padding: 1rem 1.25rem;
            border-radius: 0 12px 12px 0;
            margin: 0.75rem 0;
        }}

        .content-box-neutral {{
            background: {COLORS["surface"]};
            border-left: 3px solid {COLORS["border"]};
            padding: 1rem 1.25rem;
            border-radius: 0 12px 12px 0;
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
    """Get Plotly theme configuration for TrueNAS light mode.

    Returns:
        Dictionary with Plotly layout settings
    """
    return {
        "paper_bgcolor": COLORS["background"],
        "plot_bgcolor": COLORS["surface"],
        "font": {
            "color": COLORS["text"],  # Dark text for light mode
            "family": "Inter, -apple-system, BlinkMacSystemFont, SF Pro Text, sans-serif",
            "size": 12,
        },
        "title": {
            "font": {
                "color": COLORS["text"],
                "size": 14,
            },
            "x": 0,
            "xanchor": "left",
        },
        "xaxis": {
            "gridcolor": COLORS["border"],
            "linecolor": COLORS["border"],
            "tickcolor": COLORS["text_muted"],
            "tickfont": {"size": 11, "color": COLORS["text_muted"]},
            "title": {"font": {"color": COLORS["text"], "size": 12}},
            "gridwidth": 1,
            "zeroline": False,
        },
        "yaxis": {
            "gridcolor": COLORS["border"],
            "linecolor": COLORS["border"],
            "tickcolor": COLORS["text_muted"],
            "tickfont": {"size": 11, "color": COLORS["text_muted"]},
            "title": {"font": {"color": COLORS["text"], "size": 12}},
            "gridwidth": 1,
            "zeroline": False,
        },
        "legend": {
            "bgcolor": "rgba(255,255,255,0)",
            "bordercolor": "rgba(0,0,0,0)",
            "font": {"color": COLORS["text"], "size": 11},
        },
        "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
        # TrueNAS color palette: cyan, green, lighter cyan, warning, critical
        "colorway": ["#0095d5", "#71bf44", "#31beef", "#ff9500", "#ff3b30",
                     "#5856d6", "#ff9f0a", "#34c759"],
    }


def apply_plotly_theme(fig):
    """Apply light theme to a Plotly figure.

    Args:
        fig: Plotly figure object

    Returns:
        Updated figure with theme applied
    """
    theme = get_plotly_theme()
    fig.update_layout(**theme)

    # Explicitly update axis title fonts to ensure they're visible
    # This is needed because string titles don't inherit from theme
    fig.update_xaxes(
        title_font=dict(color=COLORS["text"], size=13, family="Inter, sans-serif"),
        tickfont=dict(color=COLORS["text_muted"], size=11)
    )
    fig.update_yaxes(
        title_font=dict(color=COLORS["text"], size=13, family="Inter, sans-serif"),
        tickfont=dict(color=COLORS["text_muted"], size=11)
    )

    return fig
