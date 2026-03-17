"""Sidebar filter controls for the aviation dashboard."""
import streamlit as st
import pandas as pd

from aerops.analytics.kpi import safe_unique_sorted
from aerops.data.iata_codes import get_all_categories


def render_sidebar(ops_df: pd.DataFrame) -> dict:
    """Render sidebar with aviation-specific filters. Returns filter dict."""

    if "reset_trigger" not in st.session_state:
        st.session_state.reset_trigger = False

    if st.session_state.reset_trigger:
        st.session_state.date_filter_key = "Last 90 Days"
        st.session_state.airline_key = "All Airlines"
        st.session_state.origin_key = "All Origins"
        st.session_state.dest_key = "All Destinations"
        st.session_state.route_key = "All Routes"
        st.session_state.delay_cat_key = "All Categories"
        st.session_state.severity_key = (0, 300)
        st.session_state.reset_trigger = False
        st.rerun()

    st.sidebar.markdown(
        '<h1 style="text-align:center; color:#38bdf8 !important; '
        'font-family:JetBrains Mono,monospace;">'
        '<i class="fas fa-plane"></i> AEROOPS AI</h1>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        '<p style="text-align:center; opacity:0.8; font-size:0.75rem; '
        'letter-spacing:0.1em;">AVIATION OPERATIONS INTELLIGENCE v2.0</p>',
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")

    if st.sidebar.button("Reset Filters", type="primary"):
        st.session_state.reset_trigger = True
        st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        '<h3><i class="fas fa-sliders-h"></i> Operations Filters</h3>',
        unsafe_allow_html=True,
    )

    # Time period
    date_filter = st.sidebar.radio(
        "Time Period",
        ["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"],
        index=3,
        key="date_filter_key",
    )

    # Airline
    airlines = ["All Airlines"] + safe_unique_sorted(ops_df, "airline")
    airline = st.sidebar.selectbox("Airline", airlines, key="airline_key")

    # Origin airport
    origins = ["All Origins"] + safe_unique_sorted(ops_df, "origin")
    origin = st.sidebar.selectbox("Origin Airport", origins, key="origin_key")

    # Destination airport
    dests = ["All Destinations"] + safe_unique_sorted(ops_df, "dest")
    dest = st.sidebar.selectbox("Destination Airport", dests, key="dest_key")

    # Route
    routes = ["All Routes"] + safe_unique_sorted(ops_df, "route")
    route = st.sidebar.selectbox("Route", routes, key="route_key")

    # IATA delay category
    categories = ["All Categories"] + get_all_categories()
    delay_cat = st.sidebar.selectbox("Delay Category (IATA)", categories, key="delay_cat_key")

    # Delay severity
    severity = st.sidebar.slider("Delay Severity (min)", 0, 300, (0, 300), key="severity_key")

    return {
        "date_filter": date_filter,
        "airline": airline,
        "origin": origin,
        "dest": dest,
        "route": route,
        "delay_category": delay_cat,
        "severity_range": severity,
    }
