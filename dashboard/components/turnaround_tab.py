"""Turnaround Performance tab - ground operations efficiency analysis."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from aerops.config import CHART_LAYOUT
from aerops.analytics.turnaround import (
    calculate_turnaround_times,
    compute_turnaround_kpis,
    TURNAROUND_BENCHMARKS,
)


def render_turnaround_analysis(ops_df: pd.DataFrame) -> None:
    """Render the Turnaround Performance analysis tab."""
    st.markdown(
        '<h2>Turnaround Performance</h2>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "Aircraft turnaround time (ground time between consecutive flights) "
        "is a critical efficiency metric. LCCs like Ryanair target **25 minutes**."
    )

    if ops_df is None or ops_df.empty:
        st.info("No flight data available for turnaround analysis.")
        return

    # Calculate turnaround times
    with st.spinner("Calculating turnaround times ..."):
        ta_df = calculate_turnaround_times(ops_df)

    if ta_df.empty:
        st.warning(
            "Insufficient rotation data for turnaround analysis. "
            "This requires flights with the same tail number at consecutive airports."
        )
        return

    kpis = compute_turnaround_kpis(ta_df)

    # ------------------------------------------------------------------
    # KPI cards
    # ------------------------------------------------------------------
    cols = st.columns(5)
    with cols[0]:
        st.metric("Total Turnarounds", f"{kpis['total_turnarounds']:,}")
    with cols[1]:
        st.metric("Avg Ground Time", f"{kpis['avg_ground_time']:.0f} min")
    with cols[2]:
        st.metric("Median Ground Time", f"{kpis['median_ground_time']:.0f} min")
    with cols[3]:
        st.metric("Under 30 min", f"{kpis['pct_under_30min']:.1f}%")
    with cols[4]:
        st.metric("Efficiency Score", f"{kpis['efficiency_score']:.0f}/100")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Distribution chart
    # ------------------------------------------------------------------
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Ground Time Distribution")

        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=ta_df["ground_time_min"],
            nbinsx=30,
            marker_color="#0ea5e9",
            opacity=0.7,
            name="Turnarounds",
        ))

        # Add benchmark lines
        fig.add_vline(x=25, line_dash="dash", line_color="#22c55e",
                      annotation_text="LCC Target (25m)")
        fig.add_vline(x=45, line_dash="dash", line_color="#eab308",
                      annotation_text="FSC Target (45m)")
        fig.add_vline(x=75, line_dash="dash", line_color="#ef4444",
                      annotation_text="Critical (75m)")

        fig.update_layout(
            **CHART_LAYOUT,
            height=350,
            xaxis_title="Ground Time (minutes)",
            yaxis_title="Frequency",
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_right:
        st.markdown("#### Status Breakdown")
        status_counts = ta_df["status"].value_counts()
        status_colors = {
            "excellent": "#22c55e",
            "on_target": "#38bdf8",
            "acceptable": "#eab308",
            "warning": "#f97316",
            "critical": "#ef4444",
        }

        fig = px.pie(
            names=status_counts.index,
            values=status_counts.values,
            color=status_counts.index,
            color_discrete_map=status_colors,
        )
        fig.update_layout(**CHART_LAYOUT, height=350)
        st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------
    # By airport
    # ------------------------------------------------------------------
    st.markdown("---")
    st.markdown("#### Turnaround by Airport")

    if kpis["by_airport"]:
        airport_df = pd.DataFrame(kpis["by_airport"])

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=airport_df["airport"],
            y=airport_df["avg_min"],
            marker_color=[
                "#22c55e" if v <= 30 else "#eab308" if v <= 45 else "#ef4444"
                for v in airport_df["avg_min"]
            ],
            text=[f"{v:.0f}m" for v in airport_df["avg_min"]],
            textposition="outside",
        ))
        fig.add_hline(y=25, line_dash="dash", line_color="#22c55e",
                      annotation_text="LCC Target")
        fig.update_layout(
            **CHART_LAYOUT, height=400,
            xaxis_title="Airport", yaxis_title="Avg Ground Time (min)",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------
    # By airline
    # ------------------------------------------------------------------
    st.markdown("#### Turnaround by Airline")

    if kpis["by_airline"]:
        airline_df = pd.DataFrame(kpis["by_airline"])

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=airline_df["airline"],
            y=airline_df["avg_min"],
            marker_color=[
                "#22c55e" if v <= 30 else "#eab308" if v <= 45 else "#ef4444"
                for v in airline_df["avg_min"]
            ],
            text=[f"{v:.0f}m ({c} turns)" for v, c in
                  zip(airline_df["avg_min"], airline_df["count"])],
            textposition="outside",
        ))
        fig.add_hline(y=25, line_dash="dash", line_color="#22c55e",
                      annotation_text="25-min Target")
        fig.update_layout(
            **CHART_LAYOUT, height=400,
            xaxis_title="Airline", yaxis_title="Avg Ground Time (min)",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ------------------------------------------------------------------
    # Industry benchmarks
    # ------------------------------------------------------------------
    st.markdown("---")
    st.markdown("#### Industry Benchmarks")

    bench_data = []
    for category, targets in TURNAROUND_BENCHMARKS.items():
        bench_data.append({
            "Category": category.replace("_", " ").title(),
            "Target (min)": targets["target"],
            "Warning (min)": targets["warning"],
            "Critical (min)": targets["critical"],
        })

    st.dataframe(pd.DataFrame(bench_data), use_container_width=True, hide_index=True)
