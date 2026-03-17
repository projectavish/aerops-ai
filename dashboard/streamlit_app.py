"""
AeroOps AI v2.0 - Aviation Operations Intelligence Platform
Real data integration | ML delay prediction | Live weather monitoring
"""
import sys
import os
import base64
from datetime import datetime

import streamlit as st
import pandas as pd

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.styles import COCKPIT_CSS
from dashboard.components.sidebar import render_sidebar
from dashboard.components.header import render_executive_dashboard
from dashboard.components.delay_tab import render_delay_analysis
from dashboard.components.prediction_tab import render_prediction
from dashboard.components.ops_center_tab import render_ops_center
from dashboard.components.crew_tab import render_airline_performance
from dashboard.components.route_tab import render_route_insights
from dashboard.components.root_cause_tab import render_root_cause
from dashboard.components.eu261_tab import render_eu261_analysis
from dashboard.components.turnaround_tab import render_turnaround_analysis
from dashboard.components.disruption_tab import render_disruption_analysis
from dashboard.components.export import generate_pdf_report
from aerops.config import DB_PATH
from aerops.db import init_db, query_df, table_row_count
from aerops.analytics.kpi import compute_metrics, apply_filters
from aerops.data.demo_generator import generate_demo_data

# Page config
st.set_page_config(
    page_title="AeroOps AI - Aviation Intelligence",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(COCKPIT_CSS, unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_flights(db_path: str) -> pd.DataFrame:
    """Load flights from SQLite with 5-min cache."""
    return query_df(db_path, "SELECT * FROM flights ORDER BY flight_date DESC")


def main():
    """Main application orchestrator."""
    # Initialize database
    init_db(DB_PATH)

    # Auto-generate demo data if DB is empty
    try:
        count = table_row_count(DB_PATH, "flights")
    except Exception:
        count = 0

    if count == 0:
        with st.spinner("Generating demo aviation data ..."):
            generate_demo_data(DB_PATH)

    # Load data
    ops_df = load_flights(DB_PATH)

    # Ensure numeric types
    for col in ["arr_delay_minutes", "dep_delay_minutes", "distance",
                 "carrier_delay", "weather_delay", "nas_delay",
                 "security_delay", "late_aircraft_delay",
                 "is_delayed", "cancelled", "diverted"]:
        if col in ops_df.columns:
            ops_df[col] = pd.to_numeric(ops_df[col], errors="coerce").fillna(0)

    # Sidebar filters
    filters = render_sidebar(ops_df)

    # Apply filters
    filtered_ops = apply_filters(ops_df, filters)
    filtered_delays = filtered_ops[filtered_ops["is_delayed"] == 1].copy() if "is_delayed" in filtered_ops.columns else pd.DataFrame()

    # Warn if filters too restrictive
    if len(filtered_ops) == 0:
        st.markdown(
            '<div class="warning-box">No flights match current filters. '
            'Try "All Time" or reset filters.</div>',
            unsafe_allow_html=True,
        )

    # Compute metrics
    metrics = compute_metrics(filtered_ops, filtered_delays)

    # Sidebar stats
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Total in DB:** {len(ops_df):,} flights")
    st.sidebar.markdown(f"**Filtered:** {len(filtered_ops):,} flights")
    st.sidebar.markdown(f"**Delayed:** {len(filtered_delays):,} flights")

    # PDF export
    st.sidebar.markdown("---")
    if st.sidebar.button("Export PDF Report"):
        pdf_bytes = generate_pdf_report(ops_df, filtered_delays, metrics, filters)
        if pdf_bytes:
            b64 = base64.b64encode(pdf_bytes).decode()
            fname = f"aeroops_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            st.sidebar.markdown(
                f'<a href="data:application/pdf;base64,{b64}" download="{fname}" '
                f'style="color:#38bdf8; font-weight:600;">Download Report</a>',
                unsafe_allow_html=True,
            )

    # Executive dashboard header
    render_executive_dashboard(filtered_ops, filtered_delays, metrics)

    st.markdown("---")

    # Main tabs (9 tabs - comprehensive aviation ops platform)
    tabs = st.tabs([
        "Delay Analysis",
        "Delay Prediction",
        "Ops Control Center",
        "EU261 Exposure",
        "Turnaround",
        "Disruption Recovery",
        "Airline & Fleet",
        "Route Analytics",
        "Root Cause",
    ])

    with tabs[0]:
        render_delay_analysis(filtered_delays, filters)

    with tabs[1]:
        render_prediction(filtered_ops, DB_PATH)

    with tabs[2]:
        render_ops_center(filtered_ops, DB_PATH)

    with tabs[3]:
        render_eu261_analysis(filtered_ops, filtered_delays)

    with tabs[4]:
        render_turnaround_analysis(filtered_ops)

    with tabs[5]:
        render_disruption_analysis(filtered_ops)

    with tabs[6]:
        render_airline_performance(filtered_ops, filters)

    with tabs[7]:
        render_route_insights(filtered_ops, filters)

    with tabs[8]:
        render_root_cause(filtered_ops, filtered_delays, filters)

    # Footer
    st.markdown("---")
    st.markdown(
        '<div style="text-align:center; color:#64748b; padding:2rem 0;">'
        '<p style="font-family:JetBrains Mono,monospace; color:#38bdf8 !important;">'
        'AeroOps AI v2.1</p>'
        '<p style="font-size:0.8rem;">Real Data | ML Predictions | Live Weather | EU261 | Turnaround | Disruption Recovery</p>'
        '</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
