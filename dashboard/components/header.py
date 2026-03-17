"""Executive dashboard header with KPI cards."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from aerops.config import CHART_LAYOUT


def render_executive_dashboard(ops_df: pd.DataFrame,
                               delays_df: pd.DataFrame,
                               metrics: dict) -> None:
    """Render the KPI header row and summary charts."""
    st.markdown(
        '<h1 class="main-header">'
        '<i class="fas fa-plane-departure"></i> AEROOPS INTELLIGENCE</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="sub-header">'
        'REAL-TIME FLIGHT OPERATIONS &amp; PREDICTIVE DELAY MANAGEMENT</p>',
        unsafe_allow_html=True,
    )

    # KPI cards
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1:
        st.markdown('<div class="icon-card"><i class="fas fa-plane"></i></div>', unsafe_allow_html=True)
        st.metric("Total Flights", f"{metrics['total_flights']:,}",
                   f"{metrics['otp_rate']:.1f}% OTP")
    with c2:
        st.markdown('<div class="icon-card"><i class="fas fa-check-circle"></i></div>', unsafe_allow_html=True)
        st.metric("On-Time", f"{metrics['on_time']:,}", "Flights")
    with c3:
        st.markdown('<div class="icon-card"><i class="fas fa-clock"></i></div>', unsafe_allow_html=True)
        st.metric("Delayed", f"{metrics['delayed']:,}",
                   f"{metrics['delay_rate']:.1f}%", delta_color="inverse")
    with c4:
        st.markdown('<div class="icon-card"><i class="fas fa-exclamation-triangle"></i></div>', unsafe_allow_html=True)
        st.metric("Critical (>60m)", f"{metrics['critical_delays']:,}",
                   "High Impact", delta_color="inverse")
    with c5:
        st.markdown('<div class="icon-card"><i class="fas fa-stopwatch"></i></div>', unsafe_allow_html=True)
        st.metric("Avg Delay", f"{metrics['avg_delay_min']:.0f}m", "Target: <15m")
    with c6:
        st.markdown('<div class="icon-card"><i class="fas fa-ban"></i></div>', unsafe_allow_html=True)
        st.metric("Cancelled", f"{metrics['cancelled']:,}",
                   f"+ {metrics['diverted']} diverted")

    st.markdown("---")

    # Trend charts
    col_a, col_b = st.columns([2, 1])

    with col_a:
        _render_delay_trend(ops_df)

    with col_b:
        _render_delay_cause_pie(delays_df)


def _render_delay_trend(ops_df: pd.DataFrame) -> None:
    """Daily delay trend with dual axis."""
    if ops_df is None or ops_df.empty or "flight_date" not in ops_df.columns:
        st.info("No data for trend chart.")
        return

    df = ops_df.copy()
    df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")
    df = df[df["flight_date"].notna()]
    if df.empty:
        return

    daily = df.groupby(df["flight_date"].dt.date).agg(
        total=("is_delayed", "count"),
        delayed=("is_delayed", "sum"),
        avg_delay=("arr_delay_minutes", "mean"),
    ).reset_index()
    daily.columns = ["date", "total", "delayed", "avg_delay"]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Bar(x=daily["date"], y=daily["delayed"], name="Delayed Flights",
               marker_color="#ef4444", opacity=0.8),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(x=daily["date"], y=daily["avg_delay"], name="Avg Delay (min)",
                   line=dict(width=3, color="#38bdf8"), mode="lines+markers"),
        secondary_y=True,
    )
    fig.update_layout(
        title="Daily Delay Trends & Impact",
        hovermode="x unified", height=400, showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        **CHART_LAYOUT,
    )
    fig.update_xaxes(title_text="Date", gridcolor="#334155")
    fig.update_yaxes(title_text="Delayed Flights", secondary_y=False, gridcolor="#334155")
    fig.update_yaxes(title_text="Avg Delay (min)", secondary_y=True)
    st.plotly_chart(fig, use_container_width=True)


def _render_delay_cause_pie(delays_df: pd.DataFrame) -> None:
    """Delay cause distribution donut chart."""
    if delays_df is None or delays_df.empty:
        st.info("No delay data for distribution chart.")
        return

    col = "iata_delay_category" if "iata_delay_category" in delays_df.columns else "primary_delay_cause"
    if col not in delays_df.columns:
        st.info("No delay categories available.")
        return

    counts = delays_df[col].dropna().value_counts()
    if counts.empty:
        return

    fig = go.Figure(data=[go.Pie(
        labels=counts.index, values=counts.values, hole=0.4,
        textinfo="label+percent", textposition="outside",
        marker_colors=["#ef4444", "#f97316", "#eab308", "#22c55e", "#3b82f6", "#8b5cf6"],
    )])
    fig.update_layout(
        title="Delay Cause Distribution (IATA)",
        height=400, showlegend=False, **CHART_LAYOUT,
    )
    st.plotly_chart(fig, use_container_width=True)
