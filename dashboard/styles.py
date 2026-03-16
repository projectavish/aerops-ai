"""Aviation cockpit dark theme CSS."""

FONT_AWESOME_LINK = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">'

COCKPIT_CSS = FONT_AWESOME_LINK + """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap');
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        -webkit-font-smoothing: antialiased;
    }
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    }
    .main .block-container {
        background: rgba(30, 41, 59, 0.95);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        border: 1px solid #334155;
        max-width: 1400px;
        margin: 0 auto;
        backdrop-filter: blur(10px);
    }
    .main-header {
        font-size: 2.75rem;
        font-weight: 800;
        text-align: center;
        padding: 1.5rem 0 0.5rem;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #38bdf8 0%, #0ea5e9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'JetBrains Mono', monospace;
    }
    .sub-header {
        text-align: center;
        color: #94a3b8 !important;
        font-size: 1.125rem;
        margin-bottom: 2.5rem;
        letter-spacing: 0.05em;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #f1f5f9 !important;
        font-weight: 700;
    }
    p, span, div, label {
        color: #cbd5e1 !important;
    }
    div[data-testid="stMetricValue"] {
        color: #38bdf8;
        font-size: 2.25rem;
        font-weight: 800;
        font-family: 'JetBrains Mono', monospace;
    }
    div[data-testid="metric-container"] {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #334155;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -5px rgba(56, 189, 248, 0.15);
        border-color: #38bdf8;
    }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #020617 0%, #0f172a 100%);
        border-right: 1px solid #1e293b;
    }
    section[data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    .stButton button {
        background: #0ea5e9;
        color: white;
        border: 1px solid #38bdf8;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.2s ease;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-size: 0.875rem;
    }
    .stButton button:hover {
        background: #0284c7;
        transform: translateY(-2px);
        box-shadow: 0 0 20px rgba(14, 165, 233, 0.4);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        padding: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"] {
        background-color: #1e293b;
        color: #94a3b8 !important;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 0.875rem 1.5rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease;
    }
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"]:hover {
        border-color: #38bdf8;
        color: #38bdf8 !important;
        background-color: #0f172a;
    }
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #0ea5e9 !important;
        border-color: #38bdf8 !important;
        color: #ffffff !important;
        box-shadow: 0 0 15px rgba(14, 165, 233, 0.3);
    }
    .stTabs [data-baseweb="tab-list"] button[data-baseweb="tab"][aria-selected="true"] * {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    .streamlit-expanderHeader {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
        padding: 1rem;
        color: #e2e8f0 !important;
    }
    .streamlit-expanderHeader:hover {
        background: #0ea5e9;
        color: white !important;
        border-color: #38bdf8;
    }
    .icon-card {
        background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
        padding: 1.25rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 0.75rem;
        box-shadow: 0 4px 6px -1px rgba(14, 165, 233, 0.3);
        transition: transform 0.2s ease;
        border: 1px solid #38bdf8;
    }
    .icon-card:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.4);
    }
    .icon-card i {
        font-size: 2.25rem;
        color: white;
    }
    .dataframe th {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important;
        color: #38bdf8 !important;
        font-weight: 600;
    }
    .dataframe td {
        color: #e2e8f0 !important;
    }
    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: #0f172a; border-radius: 5px; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 5px; }
    ::-webkit-scrollbar-thumb:hover { background: #38bdf8; }
    .js-plotly-plot {
        border: 1px solid #334155;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    section[data-testid="stSidebar"] h3 {
        font-size: 0.8rem;
        font-weight: 700;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
        border-bottom: 1px solid #334155;
        padding-bottom: 0.5rem;
        color: #38bdf8 !important;
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .warning-box {
        background: rgba(234, 179, 8, 0.1);
        border-left: 4px solid #eab308;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
        color: #fbbf24 !important;
    }
    .info-box {
        background: rgba(14, 165, 233, 0.1);
        border-left: 4px solid #0ea5e9;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
        color: #38bdf8 !important;
    }
</style>
"""
