"""Disruption Recovery tab - network delay propagation simulator."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from aerops.config import CHART_LAYOUT
from aerops.analytics.disruption import (
    simulate_disruption,
    identify_vulnerable_routes,
)


def render_disruption_analysis(ops_df: pd.DataFrame) -> None:
    """Render the Disruption Recovery & Network Resilience tab."""
    st.markdown(
        '<h2>Disruption Recovery Simulator</h2>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "Simulate how a delay at one airport cascades through the flight "
        "network via aircraft rotations. Identifies downstream flights at "
        "risk and estimates total network impact."
    )

    if ops_df is None or ops_df.empty:
        st.info("No flight data available.")
        return

    # ------------------------------------------------------------------
    # Simulator controls
    # ------------------------------------------------------------------
    st.markdown("#### Disruption Scenario")
    sim_cols = st.columns(3)

    with sim_cols[0]:
        available_airports = sorted(ops_df["origin"].dropna().unique().tolist())
        airport = st.selectbox(
            "Disrupted Airport",
            options=available_airports[:20],
            index=0,
        )

    with sim_cols[1]:
        delay_min = st.slider(
            "Initial Delay (minutes)",
            min_value=30, max_value=240, value=60, step=15,
        )

    with sim_cols[2]:
        window_hours = st.slider(
            "Analysis Window (hours)",
            min_value=2, max_value=12, value=6, step=1,
        )

    if st.button("Run Simulation", type="primary"):
        with st.spinner("Simulating delay propagation ..."):
            result = simulate_disruption(
                ops_df, airport, delay_min, window_hours
            )

        # KPI cards
        cols = st.columns(5)
        with cols[0]:
            st.metric("Affected Flights", f"{result['affected_flights']}")
        with cols[1]:
            st.metric("Cascade Depth", f"{result['cascade_depth']} levels")
        with cols[2]:
            st.metric(
                "Total Network Delay",
                f"{result['total_network_delay_minutes']:,} min",
            )
        with cols[3]:
            st.metric(
                "Downstream Airports",
                f"{result['downstream_airport_count']}",
            )
        with cols[4]:
            st.metric(
                "Est. Pax Affected",
                f"{result['estimated_pax_affected']:,}",
            )

        st.markdown("---")

        # Timeline visualization
        if result["timeline"]:
            st.markdown("#### Cascade Timeline")

            timeline_data = []
            for level_name, info in result["timeline"].items():
                timeline_data.append({
                    "Level": level_name,
                    "Flights": info["flights"],
                    "Total Delay (min)": info["total_delay_min"],
                    "Airports": ", ".join(info["airports"][:5]),
                })

            tl_df = pd.DataFrame(timeline_data)

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=tl_df["Level"],
                y=tl_df["Flights"],
                marker_color=["#ef4444", "#f97316", "#eab308", "#22c55e", "#38bdf8"][:len(tl_df)],
                text=tl_df["Flights"],
                textposition="outside",
                name="Affected Flights",
            ))
            fig.update_layout(
                **CHART_LAYOUT, height=350,
                xaxis_title="Cascade Level",
                yaxis_title="Affected Flights",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Affected flights detail
        if result["flights"]:
            st.markdown("#### Affected Flights Detail")
            flights_df = pd.DataFrame(result["flights"][:20])
            display_cols = [
                "flight", "tail_num", "origin", "dest",
                "delay_minutes", "cascade_level", "cause",
            ]
            display_cols = [c for c in display_cols if c in flights_df.columns]
            st.dataframe(
                flights_df[display_cols],
                use_container_width=True,
                hide_index=True,
            )

        # Recovery estimate
        st.markdown("---")
        st.markdown("#### Recovery Estimate")
        st.markdown(
            f"- **Estimated recovery time:** {result['recovery_time_hours']:.1f} hours\n"
            f"- **Downstream airports affected:** {', '.join(result['downstream_airports'][:10])}\n"
            f"- **Recommendation:** {'Consider aircraft swap or schedule padding' if result['cascade_depth'] > 2 else 'Monitor situation - limited cascade risk'}"
        )

    # ------------------------------------------------------------------
    # Vulnerable routes analysis (always visible)
    # ------------------------------------------------------------------
    st.markdown("---")
    st.markdown("#### Most Vulnerable Routes")
    st.markdown(
        "Routes with high delay rates AND high rotation density are most "
        "susceptible to cascading disruptions."
    )

    vulnerable = identify_vulnerable_routes(ops_df, top_n=10)

    if vulnerable:
        vuln_df = pd.DataFrame(vulnerable)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=vuln_df["route"],
            y=vuln_df["vulnerability_score"],
            marker_color=px.colors.sequential.Reds_r[:len(vuln_df)],
            text=[f"{s:.2f}" for s in vuln_df["vulnerability_score"]],
            textposition="outside",
        ))
        fig.update_layout(
            **CHART_LAYOUT, height=400,
            xaxis_title="Route",
            yaxis_title="Vulnerability Score",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            vuln_df.rename(columns={
                "route": "Route",
                "vulnerability_score": "Vulnerability",
                "delay_rate": "Delay Rate",
                "rotation_density": "Flights/Aircraft",
                "total_flights": "Total Flights",
                "avg_delay_min": "Avg Delay (min)",
            }),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Insufficient data for vulnerability analysis.")
