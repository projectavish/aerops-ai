import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import io
from io import BytesIO
import base64
import os
import traceback

# Page config
st.set_page_config(
    page_title="AerOps-AI - Aviation Intelligence",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aviation Professional Theme - Dark Cockpit Aesthetic
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
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

    .dataframe { border: 1px solid #334155; border-radius: 10px; overflow: hidden; }
    .dataframe th { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important; color: #38bdf8 !important; font-weight: 600; padding: 0.75rem; border-bottom: 2px solid #334155; }
    .dataframe tr:hover { background-color: #1e293b; }
    .dataframe td { color: #e2e8f0 !important; border-bottom: 1px solid #334155; }

    ::-webkit-scrollbar { width: 10px; height: 10px; }
    ::-webkit-scrollbar-track { background: #0f172a; border-radius: 5px; }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 5px; border: 2px solid #0f172a; }
    ::-webkit-scrollbar-thumb:hover { background: #38bdf8; }

    .js-plotly-plot { border: 1px solid #334155; border-radius: 12px; background: #1e293b; }

    .stSelectbox > div > div { border-radius: 8px; border: 1px solid #334155; background: #0f172a; }
    .stSelectbox > div > div:hover { border-color: #38bdf8; }
    .stSlider > div > div > div > div { background: #0ea5e9; }

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
</style>
""", unsafe_allow_html=True)


# -------------------------
# Helpers
# -------------------------
def _safe_unique_sorted(df: pd.DataFrame, col: str):
    if df is None or df.empty or col not in df.columns:
        return []
    vals = df[col].dropna().astype(str).unique().tolist()
    return sorted(vals)


def _apply_date_filter(df: pd.DataFrame, date_filter: str):
    if df is None or df.empty:
        return df
    date_col = None
    for c in ["scheduled_date", "created_at", "actual_date", "delay_reported"]:
        if c in df.columns:
            date_col = c
            break
    if not date_col:
        return df
    try:
        tmp = df.copy()
        tmp[date_col] = pd.to_datetime(tmp[date_col], errors="coerce")
        tmp = tmp[tmp[date_col].notna()]
        if tmp.empty:
            return tmp
        now = pd.Timestamp.now()
        if date_filter == "Last 24 Hours":
            return tmp[tmp[date_col] >= now - pd.Timedelta(hours=24)]
        if date_filter == "Last 7 Days":
            return tmp[tmp[date_col] >= now - pd.Timedelta(days=7)]
        if date_filter == "Last 30 Days":
            return tmp[tmp[date_col] >= now - pd.Timedelta(days=30)]
        return tmp
    except Exception:
        return df


def apply_filters(df: pd.DataFrame, filters: dict):
    """Apply filters to dataframe — only when columns exist."""
    if df is None or df.empty:
        return df
    filtered = df.copy()
    filtered = _apply_date_filter(filtered, filters.get("date_filter", "All Time"))

    if filters.get("aircraft_type") and filters["aircraft_type"] != "All Aircraft" and "aircraft_type" in filtered.columns:
        filtered = filtered[filtered["aircraft_type"] == filters["aircraft_type"]]
    if filters.get("crew") and filters["crew"] != "All Crew" and "crew" in filtered.columns:
        filtered = filtered[filtered["crew"] == filters["crew"]]
    if filters.get("route") and filters["route"] != "All Routes" and "route" in filtered.columns:
        filtered = filtered[filtered["route"] == filters["route"]]
    if filters.get("delay_code") and filters["delay_code"] != "All Delay Codes" and "delay_code" in filtered.columns:
        filtered = filtered[filtered["delay_code"] == filters["delay_code"]]
    if filters.get("status") and filters["status"] != "All Statuses" and "status" in filtered.columns:
        filtered = filtered[filtered["status"] == filters["status"]]

    # severity_range only filters delay_impact — NaN rows (non-delayed flights) must NOT be dropped
    if "delay_impact" in filtered.columns and "severity_range" in filters:
        lo, hi = filters["severity_range"]
        numeric = pd.to_numeric(filtered["delay_impact"], errors="coerce")
        # Keep rows where delay_impact is in range OR where it is NaN (no delay recorded)
        filtered = filtered[(numeric.isna()) | ((numeric >= lo) & (numeric <= hi))]

    return filtered


# -------------------------
# PDF Export
# -------------------------
def generate_pdf_report(ops_df, delays_df, filtered_ops, filtered_delays, filters, metrics):
    try:
        from fpdf import FPDF

        class PDF(FPDF):
            def header(self):
                self.set_font('Helvetica', 'B', 16)
                self.set_text_color(14, 165, 233)
                self.cell(0, 10, 'AerOps-AI - Operations Intelligence Report', 0, 1, 'C')
                self.set_font('Helvetica', '', 10)
                self.set_text_color(100, 116, 139)
                self.cell(0, 5, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")} UTC', 0, 1, 'C')
                self.ln(5)

            def footer(self):
                self.set_y(-15)
                self.set_font('Helvetica', 'I', 8)
                self.set_text_color(148, 163, 184)
                self.cell(0, 10, f'Page {self.page_no()} | AerOps-AI Confidential', 0, 0, 'C')

        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 10, 'Executive Summary', 0, 1)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(71, 85, 105)
        pdf.multi_cell(0, 6, (
            f"This report analyzes {len(ops_df):,} flight operations with {len(delays_df):,} "
            f"identified delays. Current view shows {len(filtered_ops):,} filtered operations "
            f"with {len(filtered_delays):,} delay events."
        ))
        pdf.ln(3)

        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 10, 'Operational Performance Indicators', 0, 1)
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(71, 85, 105)
        col_width = 95
        pdf.cell(col_width, 8, f'Total Flights: {metrics.get("total_tasks", len(ops_df)):,}', 0, 0)
        pdf.cell(col_width, 8, f'OTP (On-Time): {metrics.get("completion_rate", 0):.1f}%', 0, 1)
        pdf.cell(col_width, 8, f'Delay Events: {len(filtered_delays):,}', 0, 0)
        pdf.cell(col_width, 8, f'Delay Rate: {metrics.get("delay_rate", 0):.1f}%', 0, 1)
        pdf.cell(col_width, 8, f'Avg Delay: {metrics.get("avg_duration", 0):.0f} min', 0, 0)
        pdf.cell(col_width, 8, f'Critical Delays (>60min): {metrics.get("delayed_tasks", 0):,}', 0, 1)
        pdf.ln(5)

        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 10, 'Active Filters', 0, 1)
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(0, 6, f"Date Range: {filters.get('date_filter', 'All Time')}", 0, 1)
        pdf.cell(0, 6, f"Aircraft: {filters.get('aircraft_type', 'All Aircraft')}", 0, 1)
        pdf.cell(0, 6, f"Crew: {filters.get('crew', 'All Crew')}", 0, 1)
        pdf.cell(0, 6, f"Route: {filters.get('route', 'All Routes')}", 0, 1)
        sr = filters.get('severity_range', (0, 180))
        pdf.cell(0, 6, f"Delay Impact: {sr[0]} - {sr[1]} min", 0, 1)
        pdf.ln(5)

        if len(filtered_delays) > 0:
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, 'Delay Analysis & Root Causes', 0, 1)
            pdf.ln(2)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 8, 'Delay Summary', 0, 1)
            pdf.set_font('Helvetica', '', 10)
            if 'delay_impact' in filtered_delays.columns:
                delays = pd.to_numeric(filtered_delays['delay_impact'], errors='coerce')
                pdf.cell(0, 6, f'Average Delay: {delays.mean():.0f} minutes', 0, 1)
                pdf.cell(0, 6, f'Critical Delays (>60min): {(delays > 60).sum()} events', 0, 1)
                pdf.cell(0, 6, f'Max Delay: {delays.max():.0f} minutes', 0, 1)
            if 'delay_code' in filtered_delays.columns:
                cc = filtered_delays['delay_code'].value_counts()
                if len(cc) > 0:
                    pdf.cell(0, 6, f'Top Delay Category: {cc.index[0]} ({cc.iloc[0]} events)', 0, 1)
            pdf.ln(5)

            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 8, 'Top 10 Critical Delays', 0, 1)
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_fill_color(14, 165, 233)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(30, 7, 'Flight', 1, 0, 'C', True)
            pdf.cell(30, 7, 'Route', 1, 0, 'C', True)
            pdf.cell(30, 7, 'Delay Code', 1, 0, 'C', True)
            pdf.cell(25, 7, 'Minutes', 1, 0, 'C', True)
            pdf.cell(35, 7, 'Aircraft', 1, 0, 'C', True)
            pdf.cell(40, 7, 'Status', 1, 1, 'C', True)
            pdf.set_text_color(71, 85, 105)
            pdf.set_font('Helvetica', '', 9)
            disp = filtered_delays.copy()
            if 'delay_impact' in disp.columns:
                disp['_n'] = pd.to_numeric(disp['delay_impact'], errors='coerce')
                disp = disp.sort_values('_n', ascending=False)
            for _, row in disp.head(10).iterrows():
                pdf.cell(30, 6, str(row.get('flight_number', 'N/A'))[:10], 1)
                pdf.cell(30, 6, str(row.get('route', 'N/A'))[:12], 1)
                pdf.cell(30, 6, str(row.get('delay_code', 'N/A'))[:12], 1)
                pdf.cell(25, 6, str(row.get('delay_impact', 'N/A'))[:8], 1)
                pdf.cell(35, 6, str(row.get('aircraft_type', 'N/A'))[:12], 1)
                pdf.cell(40, 6, str(row.get('status', 'N/A'))[:15], 1)
                pdf.ln()

        if len(filtered_ops) > 0 and 'crew' in filtered_ops.columns:
            pdf.add_page()
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, 'Crew & Fleet Performance', 0, 1)
            pdf.ln(2)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 8, f'Active Crew: {filtered_ops["crew"].nunique()}', 0, 1)
            if 'status' in filtered_ops.columns:
                on_time = (filtered_ops['status'] == 'On Time').sum()
                total = len(filtered_ops)
                pdf.set_font('Helvetica', '', 10)
                pdf.cell(0, 6, f'Overall OTP: {on_time/total*100:.1f}% ({on_time}/{total})', 0, 1)
            pdf.ln(3)
            pdf.set_font('Helvetica', 'B', 12)
            pdf.cell(0, 8, 'Crew Performance Metrics', 0, 1)
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_fill_color(14, 165, 233)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(60, 7, 'Crew Member', 1, 0, 'C', True)
            pdf.cell(40, 7, 'Total Flights', 1, 0, 'C', True)
            pdf.cell(45, 7, 'On-Time', 1, 0, 'C', True)
            pdf.cell(45, 7, 'OTP %', 1, 1, 'C', True)
            pdf.set_text_color(71, 85, 105)
            pdf.set_font('Helvetica', '', 9)
            if 'status' in filtered_ops.columns:
                perf = filtered_ops.groupby('crew').agg({'flight_id': 'count', 'status': lambda x: (x == 'On Time').sum()}).reset_index()
                perf.columns = ['Crew', 'Total', 'OnTime']
                perf['OTP'] = (perf['OnTime'] / perf['Total'] * 100).round(1)
                perf = perf.sort_values('Total', ascending=False)
                for _, row in perf.head(15).iterrows():
                    pdf.cell(60, 6, str(row['Crew'])[:25], 1)
                    pdf.cell(40, 6, str(row['Total']), 1, 0, 'C')
                    pdf.cell(45, 6, str(row['OnTime']), 1, 0, 'C')
                    pdf.cell(45, 6, f"{row['OTP']:.1f}%", 1, 0, 'C')
                    pdf.ln()

        return pdf.output(dest='BYTES')

    except Exception as e:
        st.error(f"PDF Generation Error: {str(e)}")
        with st.expander("Show detailed error"):
            st.code(traceback.format_exc())
        return None


# -------------------------
# Sidebar
# -------------------------
def render_sidebar(ops_df: pd.DataFrame):
    if 'reset_trigger' not in st.session_state:
        st.session_state.reset_trigger = False

    if st.session_state.reset_trigger:
        st.session_state.date_filter_key = "Last 7 Days"
        st.session_state.aircraft_key = "All Aircraft"
        st.session_state.crew_key = "All Crew"
        st.session_state.route_key = "All Routes"
        st.session_state.status_key = "All Statuses"
        st.session_state.severity_key = (0, 180)
        st.session_state.delay_code_key = "All Delay Codes"
        st.session_state.reset_trigger = False
        st.rerun()

    st.sidebar.markdown(
        '<h1 style="text-align: center; color: #38bdf8 !important; font-family: JetBrains Mono, monospace;">'
        '<i class="fas fa-plane"></i> AEROPS-AI</h1>', unsafe_allow_html=True)
    st.sidebar.markdown(
        '<p style="text-align: center; opacity: 0.8; font-size: 0.8rem; letter-spacing: 0.1em;">'
        'AVIATION INTELLIGENCE PLATFORM</p>', unsafe_allow_html=True)
    st.sidebar.markdown("---")

    if st.sidebar.button("🔄 Reset Filters", type="primary"):
        st.session_state.reset_trigger = True
        st.cache_data.clear()
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown('<h3><i class="fas fa-sliders-h"></i> Operations Filters</h3>', unsafe_allow_html=True)

    st.sidebar.markdown('<p style="margin-top: 1rem;"><i class="fas fa-clock"></i> <strong>Time Period</strong></p>', unsafe_allow_html=True)
    date_filter = st.sidebar.radio(
        "Select Period",
        ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "All Time"],
        index=1,  # default: Last 7 Days
        key='date_filter_key'
    )

    aircraft_types = ["All Aircraft"] + _safe_unique_sorted(ops_df, "aircraft_type")
    selected_aircraft = st.sidebar.selectbox("✈️ Aircraft Type", aircraft_types, key='aircraft_key')

    crews = ["All Crew"] + _safe_unique_sorted(ops_df, "crew")
    selected_crew = st.sidebar.selectbox("👨‍✈️ Crew Member", crews, key='crew_key')

    routes = ["All Routes"] + _safe_unique_sorted(ops_df, "route")
    selected_route = st.sidebar.selectbox("🛫 Route", routes, key='route_key')

    delay_codes = ["All Delay Codes", "Weather", "ATC", "Aircraft Tech", "Crew", "Ground Handling", "Passenger"]
    selected_delay_code = st.sidebar.selectbox("⚠️ Delay Category", delay_codes, key='delay_code_key')

    statuses = ["All Statuses", "On Time", "Delayed", "Cancelled", "In Progress"]
    selected_status = st.sidebar.selectbox("🚦 Flight Status", statuses, key='status_key')

    st.sidebar.markdown('<p style="margin-top: 1rem;"><i class="fas fa-hourglass-half"></i> <strong>Delay Impact (min)</strong></p>', unsafe_allow_html=True)
    severity_range = st.sidebar.slider("Minutes", 0, 180, (0, 180), key='severity_key')

    return {
        "aircraft_type": selected_aircraft,
        "crew": selected_crew,
        "route": selected_route,
        "delay_code": selected_delay_code,
        "status": selected_status,
        "severity_range": severity_range,
        "date_filter": date_filter
    }


# -------------------------
# Dashboard
# -------------------------
def render_executive_dashboard(ops_df, delays_df, suggestions_df, metrics):
    st.markdown('<h1 class="main-header"><i class="fas fa-plane-departure"></i> AEROPS INTELLIGENCE</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header"><i class="fas fa-radar"></i> REAL-TIME FLIGHT OPERATIONS & PREDICTIVE DELAY MANAGEMENT</p>', unsafe_allow_html=True)

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    total_flights = int(metrics.get("total_tasks", len(ops_df) if ops_df is not None else 0))
    on_time_flights = int(metrics.get("completed_tasks", 0))
    otp_rate = (on_time_flights / total_flights * 100) if total_flights > 0 else 0

    with col1:
        st.markdown('<div class="icon-card"><i class="fas fa-plane"></i></div>', unsafe_allow_html=True)
        st.metric("Total Flights", f"{total_flights:,}", f"{otp_rate:.1f}% OTP")

    with col2:
        active_flights = 0
        if ops_df is not None and not ops_df.empty and "status" in ops_df.columns:
            active_flights = int((ops_df["status"] == "In Progress").sum())
        st.markdown('<div class="icon-card"><i class="fas fa-plane-up"></i></div>', unsafe_allow_html=True)
        st.metric("In Air", f"{active_flights:,}", "Active")

    with col3:
        delay_count = len(delays_df) if delays_df is not None else 0
        delay_rate = float(metrics.get("bottleneck_rate", 0))
        st.markdown('<div class="icon-card"><i class="fas fa-clock"></i></div>', unsafe_allow_html=True)
        st.metric("Delays", f"{delay_count:,}", f"{delay_rate:.1f}%", delta_color="inverse")

    with col4:
        critical_delays = int(metrics.get("delayed_tasks", 0))
        st.markdown('<div class="icon-card"><i class="fas fa-exclamation-triangle"></i></div>', unsafe_allow_html=True)
        st.metric("Critical (>60m)", f"{critical_delays:,}", "High Impact", delta_color="inverse")

    with col5:
        avg_delay = float(metrics.get("avg_duration", 0))
        st.markdown('<div class="icon-card"><i class="fas fa-stopwatch"></i></div>', unsafe_allow_html=True)
        st.metric("Avg Delay", f"{avg_delay:.0f}m", "Target: <15m")

    with col6:
        ai_insights = len(suggestions_df) if suggestions_df is not None and not suggestions_df.empty else 0
        st.markdown('<div class="icon-card"><i class="fas fa-brain"></i></div>', unsafe_allow_html=True)
        st.metric("AI Alerts", f"{ai_insights:,}", "Predictive")

    st.markdown("---")

    colA, colB = st.columns([2, 1])

    with colA:
        if delays_df is not None and not delays_df.empty and "delay_reported" in delays_df.columns:
            df = delays_df.copy()
            df["delay_reported"] = pd.to_datetime(df["delay_reported"], errors="coerce")
            df = df[df["delay_reported"].notna()]
            if not df.empty:
                id_col = "flight_id" if "flight_id" in df.columns else None
                if id_col is None:
                    df["_cnt"] = 1
                    id_col = "_cnt"
                daily = df.groupby(df["delay_reported"].dt.date).agg({
                    id_col: "count",
                    "delay_impact": "mean" if "delay_impact" in df.columns else "count"
                }).reset_index()
                daily.columns = ["Date", "Delay_Events", "Avg_Delay_Min"]
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(x=daily["Date"], y=daily["Delay_Events"], name="Delay Events", marker_color='#ef4444'), secondary_y=False)
                fig.add_trace(go.Scatter(x=daily["Date"], y=daily["Avg_Delay_Min"], name="Avg Delay (min)", line=dict(width=3, color='#38bdf8'), mode="lines+markers"), secondary_y=True)
                fig.update_layout(title="📈 Daily Delay Trends & Impact Analysis", hovermode="x unified", height=400,
                                  paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0',
                                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                fig.update_xaxes(title_text="Date", gridcolor='#334155')
                fig.update_yaxes(title_text="Delay Count", secondary_y=False, gridcolor='#334155')
                fig.update_yaxes(title_text="Minutes", secondary_y=True)
                st.plotly_chart(fig, use_container_width=True)

    with colB:
        if delays_df is not None and not delays_df.empty and "delay_code" in delays_df.columns:
            code_counts = delays_df["delay_code"].value_counts()
            fig = go.Figure(data=[go.Pie(
                labels=code_counts.index, values=code_counts.values, hole=0.4,
                textinfo="label+percent", textposition="outside",
                marker_colors=['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#8b5cf6', '#ec4899']
            )])
            fig.update_layout(title="Delay Code Distribution", height=400, showlegend=False,
                              paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
            st.plotly_chart(fig, use_container_width=True)


def render_delay_analysis(delays_df, filters):
    st.header("✈️ Delay Analysis & Root Causes")
    if delays_df is None or delays_df.empty:
        st.success("✅ No delays detected! Operations running smoothly.")
        return
    filtered = apply_filters(delays_df, filters)
    if filtered is None or filtered.empty:
        st.info("No delays match your current filters")
        return

    tab1, tab2, tab3 = st.tabs(["📊 Overview", "🔍 Root Cause", "🎯 Impact Analysis"])

    with tab1:
        col1, col2, col3 = st.columns(3)
        delay_series = pd.to_numeric(filtered["delay_impact"], errors="coerce") if "delay_impact" in filtered.columns else pd.Series([], dtype=float)
        with col1:
            st.metric("Critical Delays (>60m)", int((delay_series > 60).sum()) if not delay_series.empty else 0)
        with col2:
            st.metric("Avg Delay", f"{delay_series.mean():.0f}m" if not delay_series.empty else "N/A")
        with col3:
            st.metric("Total Events", len(filtered))

        colA, colB = st.columns(2)
        with colA:
            if "delay_code" in filtered.columns:
                code_counts = filtered["delay_code"].value_counts().head(10)
                fig = px.bar(x=code_counts.values, y=code_counts.index, orientation="h",
                             title="Delay Categories (IATA Codes)", labels={"x": "Count", "y": "Delay Code"},
                             color=code_counts.values, color_continuous_scale='Reds')
                fig.update_layout(showlegend=False, height=400, paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
                st.plotly_chart(fig, use_container_width=True)
        with colB:
            if "crew" in filtered.columns:
                crew_delays = filtered["crew"].value_counts().head(10)
                fig = px.bar(x=crew_delays.values, y=crew_delays.index, orientation="h",
                             title="Delays by Crew", labels={"x": "Delay Events", "y": "Crew Member"},
                             color=crew_delays.values, color_continuous_scale='Blues')
                fig.update_layout(showlegend=False, height=400, paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
                st.plotly_chart(fig, use_container_width=True)

        if "aircraft_type" in filtered.columns and "delay_code" in filtered.columns and "delay_impact" in filtered.columns:
            heatmap_data = filtered.pivot_table(values="delay_impact", index="aircraft_type", columns="delay_code", aggfunc="mean").fillna(0)
            fig = px.imshow(heatmap_data, title="Delay Heatmap: Aircraft Type vs Delay Category",
                            labels=dict(x="Delay Code", y="Aircraft Type", color="Avg Minutes"),
                            aspect="auto", color_continuous_scale='Reds')
            fig.update_layout(height=400, paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("🔍 Root Cause Analysis")
        if "root_cause" in filtered.columns:
            root_causes = filtered["root_cause"].dropna()
            if len(root_causes) > 0:
                colA, colB = st.columns([2, 1])
                with colA:
                    st.markdown("**Primary Contributing Factors:**")
                    for i, (cause, cnt) in enumerate(root_causes.value_counts().head(10).items(), 1):
                        st.markdown(f"{i}. **{cause}** ({cnt} occurrences)")
                with colB:
                    st.markdown("**Operational Insights:**")
                    st.markdown(f"- {root_causes.nunique()} distinct root causes")
                    st.markdown(f"- {len(root_causes)} total delay events analyzed")
                    st.markdown(f"- Top factor: **{root_causes.value_counts().index[0]}**")
                    if "delay_code" in filtered.columns:
                        weather_pct = (filtered["delay_code"] == "Weather").mean() * 100
                        st.markdown(f"- Weather impact: **{weather_pct:.1f}%** of delays")
            else:
                st.info("No root cause data available")
        else:
            st.info("Root cause analysis pending")

    with tab3:
        st.subheader("🎯 Operational Impact")
        colA, colB = st.columns(2)
        with colA:
            if "delay_impact" in filtered.columns:
                delay_series = pd.to_numeric(filtered["delay_impact"], errors="coerce").fillna(0)
                total_delay_mins = float(delay_series.sum())
                st.metric("Total Delay Minutes", f"{total_delay_mins:,.0f}")
                st.metric("Est. Pax Impact", f"{total_delay_mins * 1.5:,.0f} pax-min")
                fig = px.histogram(filtered, x="delay_impact", nbins=20, title="Delay Duration Distribution",
                                   labels={"delay_impact": "Minutes", "count": "Frequency"},
                                   color_discrete_sequence=['#ef4444'])
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
                st.plotly_chart(fig, use_container_width=True)
        with colB:
            if "route" in filtered.columns and "delay_impact" in filtered.columns:
                id_col = "flight_id" if "flight_id" in filtered.columns else None
                if id_col is None:
                    filtered = filtered.copy()
                    filtered["_cnt"] = 1
                    id_col = "_cnt"
                route_impact = filtered.groupby("route").agg({id_col: "count", "delay_impact": "sum"}).round(0)
                route_impact.columns = ["Delay_Events", "Total_Minutes"]
                route_impact = route_impact.sort_values("Total_Minutes", ascending=False)
                st.dataframe(route_impact.head(10), use_container_width=True, height=350)

    st.markdown("---")
    st.subheader("📋 Delay Event Records")
    display_cols = ["flight_id", "flight_number", "route", "crew", "aircraft_type", "delay_code", "delay_impact", "status", "delay_reported"]
    existing_cols = [c for c in display_cols if c in filtered.columns]
    if existing_cols:
        st.dataframe(filtered[existing_cols].head(100), use_container_width=True, height=400)


def render_ai_recommendations(suggestions_df, filters):
    st.header("🤖 AI Operations Center")
    if suggestions_df is None or suggestions_df.empty:
        st.info("No AI alerts generated. System monitoring for operational anomalies.")
        return
    filtered = apply_filters(suggestions_df, filters)
    if filtered is None or filtered.empty:
        st.info("No alerts match your filters")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Alerts", len(filtered))
    with col2:
        if "confidence" in filtered.columns:
            high_conf = int((pd.to_numeric(filtered["confidence"], errors="coerce") >= 80).sum())
        else:
            high_conf = 0
        st.metric("High Confidence", high_conf)
    with col3:
        acknowledged = int(pd.to_numeric(filtered.get("acknowledged", pd.Series([0])), errors="coerce").fillna(0).sum())
        st.metric("Acknowledged", acknowledged)
    with col4:
        avg_conf = float(pd.to_numeric(filtered.get("confidence", pd.Series([0])), errors="coerce").mean())
        st.metric("Avg Confidence", f"{avg_conf:.0f}%" if avg_conf else "N/A")

    st.markdown("---")
    colA, colB = st.columns([2, 1])

    with colA:
        st.subheader("🚨 Critical Operational Alerts")
        for _, row in filtered.iterrows():
            alert_type = row.get("alert_type", "General")
            flight = str(row.get("flight_number", "Unknown"))[:30]
            confidence = row.get("confidence", 0)
            with st.expander(f"⚠️ {alert_type}: {flight} (Confidence: {confidence}%)"):
                st.markdown(f"**Flight:** {row.get('flight_id', 'N/A')} | **Route:** {row.get('route', 'N/A')}")
                st.markdown(f"**Crew:** {row.get('crew', 'N/A')} | **Aircraft:** {row.get('aircraft_type', 'N/A')}")
                st.markdown("**💡 AI Recommendation:**")
                st.markdown(str(row.get("recommendation", ""))[:600])
                factors = row.get("contributing_factors", None)
                if factors and str(factors).strip() and str(factors) != "nan":
                    st.markdown("**📊 Contributing Factors:**")
                    st.markdown(str(factors)[:300])
                action = row.get("suggested_action", None)
                if action and str(action).strip() and str(action) != "nan":
                    st.markdown("**✅ Suggested Action:**")
                    st.markdown(str(action)[:300])
                colx, coly, colz = st.columns(3)
                with colx:
                    st.button("✓ Acknowledge", key=f"ack_{row.get('alert_id', row.name)}")
                with coly:
                    st.button("✗ Dismiss", key=f"dis_{row.get('alert_id', row.name)}")
                with colz:
                    st.button("📋 Details", key=f"det_{row.get('alert_id', row.name)}")

    with colB:
        st.subheader("📊 Alert Analytics")
        if "confidence" in filtered.columns:
            fig = px.histogram(filtered, x="confidence", nbins=10, title="Confidence Distribution",
                               labels={"confidence": "Confidence %"}, color_discrete_sequence=['#0ea5e9'])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
            st.plotly_chart(fig, use_container_width=True)
        if "alert_type" in filtered.columns:
            type_counts = filtered["alert_type"].astype(str).value_counts()
            fig = px.pie(values=type_counts.values, names=type_counts.index, title="Alert Categories")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
            st.plotly_chart(fig, use_container_width=True)


def render_crew_performance(ops_df, filters):
    st.header("👨‍✈️ Crew & Fleet Performance")
    if ops_df is None or ops_df.empty:
        st.info("No operations data available.")
        return
    ops_filters = {k: v for k, v in filters.items() if k not in ('delay_code', 'severity_range')}
    filtered = apply_filters(ops_df, ops_filters)

    col1, col2, col3, col4 = st.columns(4)
    total_crew = filtered["crew"].nunique() if "crew" in filtered.columns else 0
    with col1:
        st.metric("Active Crew", total_crew)
    with col2:
        avg_flights = (len(filtered) / total_crew) if total_crew > 0 else 0
        st.metric("Avg Flights/Crew", f"{avg_flights:.1f}")
    with col3:
        on_time = int((filtered["status"] == "On Time").sum()) if "status" in filtered.columns else 0
        st.metric("On-Time Flights", on_time)
    with col4:
        in_air = int((filtered["status"] == "In Progress").sum()) if "status" in filtered.columns else 0
        st.metric("Currently In Air", in_air)

    st.markdown("---")
    colA, colB = st.columns(2)

    with colA:
        if "crew" in filtered.columns and not filtered.empty:
            crew_flights = filtered["crew"].value_counts().head(15)
            if not crew_flights.empty:
                fig = px.bar(x=crew_flights.values, y=crew_flights.index, orientation="h",
                             title="Flight Distribution by Crew", labels={"x": "Number of Flights", "y": "Crew Member"},
                             color=crew_flights.values, color_continuous_scale='Blues')
                fig.update_layout(height=500, paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
                st.plotly_chart(fig, use_container_width=True)

    with colB:
        if {"crew", "status", "flight_id"}.issubset(set(filtered.columns)) and not filtered.empty:
            crew_stats = filtered.groupby("crew").agg(
                flight_count=("flight_id", "count"),
                on_time=("status", lambda x: (x == "On Time").sum())
            )
            if not crew_stats.empty:
                crew_stats["otp_rate"] = (crew_stats["on_time"] / crew_stats["flight_count"] * 100).round(1)
                crew_stats = crew_stats.sort_values("otp_rate", ascending=False).head(15)
                fig = px.bar(x=crew_stats["otp_rate"], y=crew_stats.index, orientation="h",
                             title="On-Time Performance by Crew (%)", labels={"x": "OTP %", "y": "Crew Member"},
                             color=crew_stats["otp_rate"], color_continuous_scale='Greens')
                fig.update_layout(height=500, paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
                st.plotly_chart(fig, use_container_width=True)

    st.subheader("🏆 Crew Performance Leaderboard")
    needed = {"crew", "flight_id", "status"}
    if needed.issubset(set(filtered.columns)) and not filtered.empty:
        leaderboard = filtered.groupby("crew").agg(
            total_flights=("flight_id", "count"),
            on_time=("status", lambda x: (x == "On Time").sum())
        )
        if "actual_duration" in filtered.columns:
            leaderboard["avg_turnaround"] = filtered.groupby("crew")["actual_duration"].mean().round(0)
        if "route" in filtered.columns:
            leaderboard["unique_routes"] = filtered.groupby("crew")["route"].nunique()
        leaderboard["otp_pct"] = (leaderboard["on_time"] / leaderboard["total_flights"] * 100).round(1)
        leaderboard = leaderboard.sort_values("otp_pct", ascending=False)
        st.dataframe(leaderboard.head(20), use_container_width=True, height=400)


def render_route_insights(ops_df, filters):
    st.header("🛫 Route & Fleet Analytics")
    if ops_df is None or ops_df.empty:
        st.info("No operations data available.")
        return
    ops_filters = {k: v for k, v in filters.items() if k not in ('delay_code', 'severity_range')}
    filtered = apply_filters(ops_df, ops_filters)
    if filtered is None or filtered.empty:
        st.info("No routes match your current filters.")
        return

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Active Routes", filtered["route"].nunique() if "route" in filtered.columns else 0)
    with col2:
        st.metric("Fleet Types", filtered["aircraft_type"].nunique() if "aircraft_type" in filtered.columns else 0)
    with col3:
        if "actual_duration" in filtered.columns:
            st.metric("Avg Turnaround", f"{pd.to_numeric(filtered['actual_duration'], errors='coerce').mean():.0f}m")
        else:
            st.metric("Avg Turnaround", "N/A")
    with col4:
        cancelled = int((filtered["status"] == "Cancelled").sum()) if "status" in filtered.columns else 0
        st.metric("Cancellations", cancelled)

    st.markdown("---")
    colA, colB = st.columns(2)

    with colA:
        if "route" in filtered.columns:
            route_flights = filtered["route"].value_counts().head(15)
            if not route_flights.empty:
                fig = px.bar(x=route_flights.values, y=route_flights.index, orientation="h",
                             title="Flight Volume by Route", labels={"x": "Number of Flights", "y": "Route"},
                             color=route_flights.values, color_continuous_scale='Purples')
                fig.update_layout(height=500, paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
                st.plotly_chart(fig, use_container_width=True)

    with colB:
        if {"route", "status"}.issubset(set(filtered.columns)) and not filtered.empty:
            route_status = filtered.groupby(["route", "status"]).size().reset_index(name="count")
            if not route_status.empty:
                fig = px.bar(route_status, x="route", y="count", color="status",
                             title="Operational Status by Route",
                             labels={"count": "Number of Flights", "route": "Route"},
                             barmode="stack",
                             color_discrete_map={"On Time": "#22c55e", "Delayed": "#ef4444",
                                                 "In Progress": "#3b82f6", "Cancelled": "#6b7280"})
                fig.update_layout(height=500, xaxis_tickangle=-45, paper_bgcolor='rgba(0,0,0,0)', font_color='#e2e8f0')
                st.plotly_chart(fig, use_container_width=True)

    st.subheader("📊 Route Performance Summary")
    if {"route", "flight_id", "status"}.issubset(set(filtered.columns)) and not filtered.empty:
        try:
            route_stats = filtered.groupby("route").agg(
                total_flights=("flight_id", "count"),
                on_time=("status", lambda x: (x == "On Time").sum())
            )
            if "actual_duration" in filtered.columns:
                route_stats["avg_turnaround"] = filtered.groupby("route")["actual_duration"].mean().round(0)
            if "aircraft_type" in filtered.columns:
                route_stats["fleet_types"] = filtered.groupby("route")["aircraft_type"].nunique()
            route_stats["otp_pct"] = (route_stats["on_time"] / route_stats["total_flights"] * 100).round(1)
            route_stats = route_stats.sort_values("total_flights", ascending=False)
            st.dataframe(route_stats, use_container_width=True, height=400)
        except Exception:
            st.error("Could not generate route statistics")


# -------------------------
# Data Generation
# -------------------------
def generate_realistic_aviation_data():
    np.random.seed(42)

    CONFIG = {
        'days_of_history': 90,
        'peak_hours': [6, 7, 8, 9, 16, 17, 18, 19],
        'delay_prob': 0.16,
        'cancellation_prob': 0.012,
        'crew_monthly_limit': 55,
        'aircraft_daily_limit': 6,
    }

    FLEET = {
        'B737-800':   {'count': 45, 'avg_block_time': 145, 'capacity': 162},
        'A320neo':    {'count': 38, 'avg_block_time': 140, 'capacity': 180},
        'A321':       {'count': 22, 'avg_block_time': 155, 'capacity': 200},
        'B777-300ER': {'count': 12, 'avg_block_time': 780, 'capacity': 396},
        'A350-900':   {'count': 8,  'avg_block_time': 820, 'capacity': 325},
        'CRJ900':     {'count': 18, 'avg_block_time': 95,  'capacity': 76},
    }

    # ~600 flights/day on weekdays
    ROUTES = {
        'JFK-LAX': {'type': 'trunk',    'base_freq': 18, 'distance': 2475},
        'LAX-JFK': {'type': 'trunk',    'base_freq': 18, 'distance': 2475},
        'JFK-ORD': {'type': 'trunk',    'base_freq': 16, 'distance': 740},
        'ORD-JFK': {'type': 'trunk',    'base_freq': 16, 'distance': 740},
        'LAX-DFW': {'type': 'trunk',    'base_freq': 15, 'distance': 1235},
        'DFW-LAX': {'type': 'trunk',    'base_freq': 15, 'distance': 1235},
        'JFK-MIA': {'type': 'trunk',    'base_freq': 14, 'distance': 1090},
        'MIA-JFK': {'type': 'trunk',    'base_freq': 14, 'distance': 1090},
        'ORD-LAX': {'type': 'trunk',    'base_freq': 13, 'distance': 1745},
        'LAX-ORD': {'type': 'trunk',    'base_freq': 13, 'distance': 1745},
        'ATL-JFK': {'type': 'trunk',    'base_freq': 12, 'distance': 865},
        'JFK-ATL': {'type': 'trunk',    'base_freq': 12, 'distance': 865},
        'DFW-ORD': {'type': 'trunk',    'base_freq': 11, 'distance': 802},
        'ORD-DFW': {'type': 'trunk',    'base_freq': 11, 'distance': 802},
        'JFK-LHR': {'type': 'intl',     'base_freq': 9,  'distance': 3451},
        'LHR-JFK': {'type': 'intl',     'base_freq': 9,  'distance': 3451},
        'JFK-CDG': {'type': 'intl',     'base_freq': 7,  'distance': 3628},
        'CDG-JFK': {'type': 'intl',     'base_freq': 7,  'distance': 3628},
        'LAX-NRT': {'type': 'intl',     'base_freq': 6,  'distance': 5451},
        'NRT-LAX': {'type': 'intl',     'base_freq': 6,  'distance': 5451},
        'MIA-CDG': {'type': 'intl',     'base_freq': 5,  'distance': 4580},
        'CDG-MIA': {'type': 'intl',     'base_freq': 5,  'distance': 4580},
        'JFK-FRA': {'type': 'intl',     'base_freq': 5,  'distance': 3849},
        'FRA-JFK': {'type': 'intl',     'base_freq': 5,  'distance': 3849},
        'LAX-SYD': {'type': 'intl',     'base_freq': 3,  'distance': 7488},
        'SYD-LAX': {'type': 'intl',     'base_freq': 3,  'distance': 7488},
        'SFO-SIN': {'type': 'intl',     'base_freq': 3,  'distance': 8481},
        'SIN-SFO': {'type': 'intl',     'base_freq': 3,  'distance': 8481},
        'BOS-LGA': {'type': 'regional', 'base_freq': 26, 'distance': 185},
        'LGA-BOS': {'type': 'regional', 'base_freq': 26, 'distance': 185},
        'SFO-LAX': {'type': 'regional', 'base_freq': 24, 'distance': 337},
        'LAX-SFO': {'type': 'regional', 'base_freq': 24, 'distance': 337},
        'LAS-LAX': {'type': 'regional', 'base_freq': 20, 'distance': 236},
        'LAX-LAS': {'type': 'regional', 'base_freq': 20, 'distance': 236},
        'ATL-MCO': {'type': 'regional', 'base_freq': 18, 'distance': 404},
        'MCO-ATL': {'type': 'regional', 'base_freq': 18, 'distance': 404},
        'DFW-MIA': {'type': 'regional', 'base_freq': 14, 'distance': 1120},
        'MIA-DFW': {'type': 'regional', 'base_freq': 14, 'distance': 1120},
        'DCA-ORD': {'type': 'regional', 'base_freq': 12, 'distance': 612},
        'ORD-DCA': {'type': 'regional', 'base_freq': 12, 'distance': 612},
        'PHX-DEN': {'type': 'regional', 'base_freq': 12, 'distance': 865},
        'DEN-PHX': {'type': 'regional', 'base_freq': 12, 'distance': 865},
        'SEA-DEN': {'type': 'regional', 'base_freq': 10, 'distance': 1024},
        'DEN-SEA': {'type': 'regional', 'base_freq': 10, 'distance': 1024},
        'SEA-SFO': {'type': 'regional', 'base_freq': 14, 'distance': 679},
        'SFO-SEA': {'type': 'regional', 'base_freq': 14, 'distance': 679},
        'MSP-ORD': {'type': 'regional', 'base_freq': 11, 'distance': 334},
        'ORD-MSP': {'type': 'regional', 'base_freq': 11, 'distance': 334},
        'CLT-JFK': {'type': 'regional', 'base_freq': 10, 'distance': 541},
        'JFK-CLT': {'type': 'regional', 'base_freq': 10, 'distance': 541},
        'DTW-ORD': {'type': 'regional', 'base_freq': 13, 'distance': 235},
        'ORD-DTW': {'type': 'regional', 'base_freq': 13, 'distance': 235},
    }

    CREW_POOL = [f'Capt. {last}' for last in
        ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
         'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
         'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson', 'White',
         'Harris', 'Saxena', 'Chen', 'Patel', 'Kim', 'Wong', 'Gupta', 'Singh', 'Murphy',
         "O'Brien", 'Walsh', 'Ryan', 'Doyle', 'McCarthy', "O'Connor", 'Kowalski', 'Nowak',
         'Schmidt', 'Mueller', 'Weber', 'Fischer', 'Meyer', 'Wagner', 'Becker', 'Hoffmann',
         'Suzuki', 'Tanaka', 'Watanabe', 'Takahashi', 'Ito', 'Yamamoto', 'Nakamura', 'Kobayashi',
         'Ali', 'Khan', 'Ahmed', 'Hassan', 'Hussein', 'Mohamed', 'Abdullah', 'Ibrahim']] * 3

    DELAY_CODES = {
        'Weather': 0.18, 'ATC': 0.15, 'Aircraft Tech': 0.25,
        'Crew': 0.12, 'Ground Handling': 0.18, 'Passenger': 0.08, 'Security': 0.04
    }

    ROOT_CAUSES = {
        'Weather':        ['Thunderstorms', 'Fog/Low Visibility', 'Snow/Ice', 'High Winds', 'Hurricane'],
        'ATC':            ['Airspace Congestion', 'Ground Stop', 'Flow Control', 'Runway Closure', 'ATC Staffing'],
        'Aircraft Tech':  ['Mechanical Issue', 'Scheduled Maintenance', 'AOG', 'MEL/CDL Item', 'Engine Problem'],
        'Crew':           ['Crew Rest Violation', 'Crew Shortage', 'Training Conflict', 'Sick Call', 'Duty Time Limits'],
        'Ground Handling':['Late Incoming Aircraft', 'Baggage Loading Delay', 'Catering Delay', 'Fuel Delay', 'Cleaning Delay'],
        'Passenger':      ['Late Check-in', 'No-show', 'Security Hold', 'Medical Emergency', 'Unruly Passenger'],
        'Security':       ['TSA Screening', 'Security Threat', 'Baggage Search', 'Document Check'],
    }

    # Dynamic dates so filters always work relative to today
    end_date = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
    start_date = end_date - timedelta(days=CONFIG['days_of_history'])
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')

    flights = []
    flight_counter = 1000
    crew_utilization = {crew: 0 for crew in CREW_POOL}
    current_month = start_date.month

    aircraft_registry = []
    for ac_type, info in FLEET.items():
        for _ in range(info['count']):
            tail = f"N{np.random.randint(100,999)}{chr(65+np.random.randint(0,26))}{chr(65+np.random.randint(0,26))}"
            aircraft_registry.append({'tail': tail, 'type': ac_type,
                                       'avg_block': info['avg_block_time'], 'daily_flights': 0})

    for date in date_range:
        if date.month != current_month:
            crew_utilization = {crew: 0 for crew in CREW_POOL}
            current_month = date.month
        for ac in aircraft_registry:
            ac['daily_flights'] = 0

        is_weekend = date.weekday() >= 5

        for route_code, route_info in ROUTES.items():
            base_freq = route_info['base_freq']
            if is_weekend:
                base_freq = int(base_freq * 0.8)

            for _ in range(base_freq):
                flight_counter += 1
                flight_id = f"FLT{flight_counter}"

                if route_info['type'] == 'intl':
                    ac_type = np.random.choice(['B777-300ER', 'A350-900'], p=[0.6, 0.4])
                elif route_info['type'] == 'trunk':
                    ac_type = np.random.choice(['B737-800', 'A320neo', 'A321'], p=[0.4, 0.35, 0.25])
                else:
                    ac_type = np.random.choice(['B737-800', 'A320neo', 'CRJ900'], p=[0.3, 0.3, 0.4])

                available_ac = [ac for ac in aircraft_registry
                                if ac['type'] == ac_type and ac['daily_flights'] < CONFIG['aircraft_daily_limit']]
                if not available_ac:
                    available_ac = [ac for ac in aircraft_registry if ac['type'] == ac_type]

                if available_ac:
                    aircraft = np.random.choice(available_ac)
                    aircraft['daily_flights'] += 1
                    tail_number = aircraft['tail']
                    block_time = int(aircraft['avg_block'] + np.random.randint(-15, 16))
                else:
                    tail_number = f"N{np.random.randint(100,999)}XX"
                    block_time = int(FLEET[ac_type]['avg_block_time'])

                available_crew = [c for c in CREW_POOL if crew_utilization[c] < CONFIG['crew_monthly_limit']]
                if not available_crew:
                    available_crew = CREW_POOL
                crew = np.random.choice(available_crew)
                crew_utilization[crew] += 1

                if np.random.random() < 0.6:
                    hour = int(np.random.choice(CONFIG['peak_hours']))
                else:
                    hour = int(np.random.choice([h for h in range(5, 24) if h not in CONFIG['peak_hours']]))
                minute = int(np.random.choice([0, 15, 30, 45]))
                scheduled_time = datetime.combine(date.date(), datetime.min.time()) + timedelta(hours=hour, minutes=minute)

                rand = np.random.random()
                if rand < CONFIG['cancellation_prob']:
                    status = 'Cancelled'
                    delay_code = None
                    delay_impact = None
                    root_cause = None
                elif rand < (CONFIG['cancellation_prob'] + CONFIG['delay_prob']):
                    status = 'Delayed'
                    delay_code = str(np.random.choice(list(DELAY_CODES.keys()), p=list(DELAY_CODES.values())))
                    if delay_code in ['Weather', 'ATC']:
                        delay_impact = int(np.random.randint(20, 90))
                    elif delay_code == 'Aircraft Tech':
                        delay_impact = int(np.random.randint(15, 120))
                    elif delay_code == 'Crew':
                        delay_impact = int(np.random.randint(5, 45))
                    else:
                        delay_impact = int(np.random.randint(5, 35))
                    root_cause = str(np.random.choice(ROOT_CAUSES[delay_code]))
                else:
                    status = 'On Time'
                    delay_code = None
                    delay_impact = None
                    root_cause = None

                # Mark today's afternoon flights as In Progress
                if date.date() == end_date.date() and hour > (datetime.now().hour - 4) and np.random.random() < 0.4:
                    status = 'In Progress'
                    delay_code = None
                    delay_impact = None
                    root_cause = None

                flights.append({
                    'flight_id': flight_id,
                    'flight_number': f"AA{np.random.randint(100, 999)}",
                    'tail_number': tail_number,
                    'crew': crew,
                    'aircraft_type': ac_type,
                    'route': route_code,
                    'status': status,
                    'scheduled_date': scheduled_time,
                    'actual_duration': int(max(30, block_time + (delay_impact if delay_impact else np.random.randint(-5, 6)))),
                    'delay_code': delay_code,
                    'delay_impact': delay_impact,
                    'delay_reported': (scheduled_time + timedelta(minutes=block_time)) if status == 'Delayed' else None,
                    'root_cause': root_cause,
                })

    df = pd.DataFrame(flights)
    df['scheduled_date'] = pd.to_datetime(df['scheduled_date'])
    df['delay_reported'] = pd.to_datetime(df['delay_reported'])
    return df


# -------------------------
# AI Alert Generation
# -------------------------
def generate_ai_alerts(ops_df: pd.DataFrame, delays_df: pd.DataFrame) -> pd.DataFrame:
    """Generate predictive operational alerts from recent delay patterns."""
    if ops_df is None or ops_df.empty or delays_df is None or delays_df.empty:
        return pd.DataFrame()

    alerts = []
    alert_id = 1

    # Alert 1: Routes with high delay rate (last 30 days)
    recent_cutoff = pd.Timestamp.now() - pd.Timedelta(days=30)
    ops_recent = ops_df.copy()
    if 'scheduled_date' in ops_recent.columns:
        ops_recent['scheduled_date'] = pd.to_datetime(ops_recent['scheduled_date'], errors='coerce')
        ops_recent = ops_recent[ops_recent['scheduled_date'] >= recent_cutoff]

    if not ops_recent.empty and 'route' in ops_recent.columns and 'status' in ops_recent.columns:
        route_stats = ops_recent.groupby('route').agg(
            total=('flight_id', 'count'),
            delayed=('status', lambda x: (x == 'Delayed').sum())
        )
        route_stats['delay_rate'] = route_stats['delayed'] / route_stats['total'] * 100
        high_risk = route_stats[route_stats['delay_rate'] > 25].sort_values('delay_rate', ascending=False)

        for route, row in high_risk.head(5).iterrows():
            route_delays = delays_df[delays_df['route'] == route] if 'route' in delays_df.columns else pd.DataFrame()
            top_crew = route_delays['crew'].mode()[0] if not route_delays.empty and 'crew' in route_delays.columns and len(route_delays['crew'].mode()) > 0 else 'Multiple'
            top_code = route_delays['delay_code'].mode()[0] if not route_delays.empty and 'delay_code' in route_delays.columns and len(route_delays['delay_code'].mode()) > 0 else 'Various'
            alerts.append({
                'alert_id': f'ALT{alert_id:04d}',
                'flight_id': f'ROUTE-{route}',
                'flight_number': route,
                'route': route,
                'crew': top_crew,
                'aircraft_type': 'Multiple',
                'alert_type': 'High Delay Route',
                'confidence': min(95, int(50 + row['delay_rate'])),
                'recommendation': (
                    f"Route {route} has a {row['delay_rate']:.1f}% delay rate over 30 days "
                    f"({int(row['delayed'])} of {int(row['total'])} flights). "
                    f"Primary cause: {top_code}. Consider pre-emptive buffer time or gate reassignment."
                ),
                'contributing_factors': f"Delay rate: {row['delay_rate']:.1f}% | Events: {int(row['delayed'])} | Primary code: {top_code}",
                'suggested_action': f"Add 15-min buffer. Review {top_code} mitigation for {route}.",
                'acknowledged': 0,
            })
            alert_id += 1

    # Alert 2: Aircraft with recurring tech delays
    if 'delay_code' in delays_df.columns and 'tail_number' in delays_df.columns:
        tech_delays = delays_df[delays_df['delay_code'] == 'Aircraft Tech']
        if not tech_delays.empty:
            tail_counts = tech_delays['tail_number'].value_counts()
            for tail, count in tail_counts[tail_counts >= 3].head(5).items():
                ac_type = tech_delays[tech_delays['tail_number'] == tail]['aircraft_type'].mode()
                ac_type = ac_type[0] if len(ac_type) > 0 else 'Unknown'
                alerts.append({
                    'alert_id': f'ALT{alert_id:04d}',
                    'flight_id': f'TAIL-{tail}',
                    'flight_number': tail,
                    'route': 'Various',
                    'crew': 'MRO Team',
                    'aircraft_type': ac_type,
                    'alert_type': 'Recurring Tech Issue',
                    'confidence': min(92, 60 + count * 5),
                    'recommendation': (
                        f"Aircraft {tail} ({ac_type}) has {count} technical delays in 90 days. "
                        f"Recommend unscheduled inspection before next departure."
                    ),
                    'contributing_factors': f"Tech delay count: {count} | Aircraft: {ac_type} | Tail: {tail}",
                    'suggested_action': f"Schedule MRO inspection for {tail}. Ground if >{count+1} incidents.",
                    'acknowledged': 0,
                })
                alert_id += 1

    # Alert 3: Crew approaching utilization limits
    if not ops_recent.empty and 'crew' in ops_recent.columns:
        crew_counts = ops_recent.groupby('crew')['flight_id'].count()
        for crew_name, count in crew_counts[crew_counts > 40].sort_values(ascending=False).head(5).items():
            alerts.append({
                'alert_id': f'ALT{alert_id:04d}',
                'flight_id': f'CREW-{crew_name[:10]}',
                'flight_number': crew_name,
                'route': 'Various',
                'crew': crew_name,
                'aircraft_type': 'N/A',
                'alert_type': 'Crew Fatigue Risk',
                'confidence': min(88, 55 + (count - 40) * 2),
                'recommendation': (
                    f"{crew_name} has operated {count} flights in the last 30 days. "
                    f"Approaching regulatory duty-time limits. Review scheduling."
                ),
                'contributing_factors': f"Flights in 30 days: {count} | Threshold: 40",
                'suggested_action': f"Rotate {crew_name} to reserve. Assign standby crew to next 3 sectors.",
                'acknowledged': 0,
            })
            alert_id += 1

    # Alert 4: Weather delay spike
    if 'delay_code' in delays_df.columns and 'scheduled_date' in delays_df.columns:
        wx = delays_df[delays_df['delay_code'] == 'Weather'].copy()
        wx['scheduled_date'] = pd.to_datetime(wx['scheduled_date'], errors='coerce')
        last_7_wx = wx[wx['scheduled_date'] >= pd.Timestamp.now() - pd.Timedelta(days=7)]
        if len(last_7_wx) > 10:
            top_route = last_7_wx['route'].mode()[0] if 'route' in last_7_wx.columns and len(last_7_wx) > 0 else 'Network-wide'
            alerts.append({
                'alert_id': f'ALT{alert_id:04d}',
                'flight_id': 'WEATHER-ALERT',
                'flight_number': 'Network',
                'route': top_route,
                'crew': 'Operations Control',
                'aircraft_type': 'All Fleet',
                'alert_type': 'Weather Impact',
                'confidence': 85,
                'recommendation': (
                    f"{len(last_7_wx)} weather-related delays in last 7 days. "
                    f"Most affected: {top_route}. Issue proactive passenger notifications."
                ),
                'contributing_factors': f"Weather delays (7d): {len(last_7_wx)} | Most affected route: {top_route}",
                'suggested_action': "Activate IROPS protocol. Pre-position spare aircraft at hub airports.",
                'acknowledged': 0,
            })

    return pd.DataFrame(alerts) if alerts else pd.DataFrame()


# -------------------------
# Main
# -------------------------
def main():
    st.sidebar.markdown("---")
    st.sidebar.markdown('<h3><i class="fas fa-database"></i> Data Source</h3>', unsafe_allow_html=True)

    default_csv_path = "flight_operations.csv"

    if st.sidebar.button("🔄 Regenerate Demo Data"):
        if os.path.exists(default_csv_path):
            os.remove(default_csv_path)
        st.sidebar.success("Regenerating...")
        st.rerun()

    if not os.path.exists(default_csv_path):
        with st.spinner("Generating realistic aviation operations data (~54,000 flights over 90 days)..."):
            df = generate_realistic_aviation_data()
            df.to_csv(default_csv_path, index=False)
            st.sidebar.success(f"✅ Generated {len(df):,} flights")
            status_counts = df['status'].value_counts()
            st.sidebar.write("Status Distribution:")
            for status, count in status_counts.items():
                st.sidebar.write(f"- {status}: {count:,} ({count/len(df)*100:.1f}%)")

    uploaded_file = st.sidebar.file_uploader("Upload Flight Data CSV (optional)", type=['csv'])

    if uploaded_file is not None:
        ops_df = pd.read_csv(uploaded_file)
        source_name = uploaded_file.name
        st.sidebar.success(f"📤 Loaded: {source_name}")
    else:
        ops_df = pd.read_csv(default_csv_path)
        source_name = "Live Operations Feed (90 Days)"
        st.sidebar.info("📡 Connected to demo ops feed")

    for col in ['scheduled_date', 'delay_reported', 'created_at']:
        if col in ops_df.columns:
            ops_df[col] = pd.to_datetime(ops_df[col], errors='coerce')

    delays_df = pd.DataFrame()
    if 'status' in ops_df.columns:
        delays_df = ops_df[ops_df['status'] == 'Delayed'].copy()
    elif 'delay_code' in ops_df.columns:
        delays_df = ops_df[ops_df['delay_code'].notna() & (ops_df['delay_code'] != '') & (ops_df['delay_code'] != 'None')].copy()

    suggestions_df = generate_ai_alerts(ops_df, delays_df)

    filters = render_sidebar(ops_df)

    # IMPORTANT: ops_df must NOT be filtered by delay_code or severity_range.
    # Those filters only apply to delays_df. Applying severity_range to ops_df
    # silently removes all on-time flights (delay_impact = NaN), causing 100% delay rate.
    ops_filters = {k: v for k, v in filters.items() if k not in ('delay_code', 'severity_range')}
    filtered_ops = apply_filters(ops_df, ops_filters)
    filtered_delays = apply_filters(delays_df, filters) if not delays_df.empty else delays_df

    # Metrics
    on_time_count = int((filtered_ops["status"] == "On Time").sum()) if "status" in filtered_ops.columns else 0
    delayed_count = int((filtered_ops["status"] == "Delayed").sum()) if "status" in filtered_ops.columns else 0
    critical_count = int((pd.to_numeric(filtered_delays.get("delay_impact", pd.Series(dtype=float)), errors="coerce") > 60).sum()) if not filtered_delays.empty else 0
    avg_delay = pd.to_numeric(filtered_delays["delay_impact"], errors="coerce").mean() if not filtered_delays.empty else 0
    completion_rate = (on_time_count / len(filtered_ops) * 100) if len(filtered_ops) > 0 else 0

    metrics = {
        "total_tasks": len(filtered_ops),
        "completed_tasks": on_time_count,
        "completion_rate": completion_rate,
        "bottleneck_rate": round(len(filtered_delays) / len(filtered_ops) * 100, 1) if len(filtered_ops) > 0 else 0,
        "delay_rate": round(delayed_count / len(filtered_ops) * 100, 1) if len(filtered_ops) > 0 else 0,
        "delayed_tasks": critical_count,
        "avg_duration": avg_delay if not np.isnan(avg_delay) else 0,
    }

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Total Flights:** {len(ops_df):,}")
    st.sidebar.markdown(f"**Delayed Flights:** {len(delays_df):,} ({len(delays_df)/len(ops_df)*100:.1f}%)")
    st.sidebar.markdown(f"**Filtered View:** {len(filtered_ops):,} flights")

    st.sidebar.markdown("---")
    if st.sidebar.button("📄 Export Ops Report"):
        pdf_bytes = generate_pdf_report(ops_df, delays_df, filtered_ops, filtered_delays, filters, metrics)
        if pdf_bytes:
            b64 = base64.b64encode(pdf_bytes).decode()
            filename = f"aerops_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="color: #38bdf8; font-weight: 600;">📥 Download Operations Report</a>'
            st.sidebar.markdown(href, unsafe_allow_html=True)
            st.sidebar.success("Report generated!")
        else:
            st.sidebar.error("PDF generation failed")

    render_executive_dashboard(filtered_ops, filtered_delays, suggestions_df, metrics)
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "✈️ Delay Analysis", "🤖 AI Alerts", "👨‍✈️ Crew Performance", "🛫 Route Analytics", "📊 Ops Summary"
    ])

    with tab1:
        try:
            render_delay_analysis(filtered_delays, filters)
        except Exception as e:
            st.error(f"Delay Analysis error: {e}")

    with tab2:
        try:
            render_ai_recommendations(suggestions_df, filters)
        except Exception as e:
            st.error(f"AI Alerts error: {e}")

    with tab3:
        try:
            render_crew_performance(filtered_ops, filters)
        except Exception as e:
            st.error(f"Crew Performance error: {e}")

    with tab4:
        try:
            render_route_insights(filtered_ops, filters)
        except Exception as e:
            st.error(f"Route Analytics error: {e}")

    with tab5:
        st.header("📊 Operations Summary")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Data Source")
            st.write(f"**Source:** {source_name}")
            st.write(f"**Total Records:** {len(ops_df):,}")
            st.write(f"**Delay Events:** {len(delays_df):,}")
            if 'scheduled_date' in ops_df.columns:
                st.write(f"**Date Range:** {ops_df['scheduled_date'].min().date()} to {ops_df['scheduled_date'].max().date()}")
                st.write(f"**Coverage:** {(ops_df['scheduled_date'].max() - ops_df['scheduled_date'].min()).days} days")
        with col2:
            st.subheader("Current View")
            st.write(f"**Time Filter:** {filters.get('date_filter', 'All Time')}")
            st.write(f"**Filtered Flights:** {len(filtered_ops):,}")
            if len(filtered_ops) > 0:
                st.write(f"**Routes:** {filtered_ops['route'].nunique() if 'route' in filtered_ops.columns else 'N/A'}")
                st.write(f"**Active Crew:** {filtered_ops['crew'].nunique() if 'crew' in filtered_ops.columns else 'N/A'}")
                if 'status' in filtered_ops.columns:
                    otp = (filtered_ops['status'] == 'On Time').sum() / len(filtered_ops) * 100
                    st.write(f"**Current OTP:** {otp:.1f}%")

        st.markdown("---")
        st.subheader("About AerOps-AI")
        st.markdown("""
**AerOps-AI** is an aviation operations intelligence platform for airlines, MROs, and ground handlers.

**Capabilities:**
- Real-time OTP (On-Time Performance) monitoring
- IATA delay code analysis and root cause identification
- Crew resource management (CRM) optimization
- Predictive delay forecasting using ML models
- Automated operational alerts and recommendations
- PDF reporting for station managers and dispatch

**Compliance:** Supports IATA delay coding standards and FAA/EASA operational guidelines.
        """)

    st.markdown("---")
    st.markdown("""
<div style='text-align: center; color: #64748b; padding: 2rem 0; border-top: 1px solid #334155;'>
    <h3 style='color: #38bdf8 !important; font-family: JetBrains Mono, monospace;'>AerOps-AI</h3>
    <p>Aviation Operations Intelligence | Predictive Delay Management</p>
    <p style='font-size: 0.8rem;'>© 2026 AerOps-AI. Built for Aviation Professionals</p>
</div>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
