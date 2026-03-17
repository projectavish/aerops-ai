"""EU261 Compensation Exposure tab - financial impact of flight delays."""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px

from aerops.config import CHART_LAYOUT
from aerops.analytics.eu261 import (
    calculate_eu261_compensation,
    calculate_fleet_eu261_exposure,
    calculate_operational_cost,
)


def render_eu261_analysis(ops_df: pd.DataFrame, delays_df: pd.DataFrame) -> None:
    """Render the EU261 Compensation Exposure analysis tab."""
    st.markdown(
        '<h2>EU261 Compensation Exposure</h2>',
        unsafe_allow_html=True,
    )

    st.markdown(
        "**EU Regulation 261/2004** mandates passenger compensation for delays "
        "exceeding 3 hours. This tab quantifies financial exposure across your network."
    )

    if ops_df is None or ops_df.empty:
        st.info("No flight data available.")
        return

    # ------------------------------------------------------------------
    # Fleet-wide exposure
    # ------------------------------------------------------------------
    exposure = calculate_fleet_eu261_exposure(ops_df)

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            "Total EU261 Exposure",
            f"EUR {exposure['total_exposure_eur']:,.0f}",
        )
    with col2:
        st.metric(
            "Affected Flights",
            f"{exposure['affected_flights']:,}",
            f"{exposure['exposure_rate']:.1f}% of total",
        )
    with col3:
        st.metric(
            "Avg Exposure / Flight",
            f"EUR {exposure['exposure_per_flight_eur']:,.0f}",
        )
    with col4:
        st.metric("Total Flights", f"{exposure['total_flights']:,}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Tier breakdown
    # ------------------------------------------------------------------
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Compensation by Tier")
        if exposure["tier_breakdown"]:
            tier_data = []
            for tier_name, info in exposure["tier_breakdown"].items():
                tier_data.append({
                    "Tier": tier_name,
                    "Flights": info["flights"],
                    "Total (EUR)": info["total_eur"],
                })
            tier_df = pd.DataFrame(tier_data)

            fig = px.bar(
                tier_df,
                x="Tier",
                y="Total (EUR)",
                color="Tier",
                text="Flights",
                color_discrete_sequence=["#22c55e", "#eab308", "#ef4444"],
            )
            fig.update_layout(**CHART_LAYOUT, showlegend=False, height=350)
            fig.update_traces(texttemplate="%{text} flights", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No EU261-eligible delays in current selection.")

    with col_right:
        st.markdown("#### EU261 Thresholds")
        st.markdown("""
        | Distance | Min Delay | Compensation |
        |----------|-----------|-------------|
        | ≤ 1,500 km | 3 hours | **EUR 250** per pax |
        | 1,500 - 3,500 km | 3 hours | **EUR 400** per pax |
        | > 3,500 km | 4 hours | **EUR 600** per pax |
        """)

        st.markdown("#### Exemptions")
        st.markdown(
            "- Extraordinary circumstances (severe weather, ATC strikes)\n"
            "- Delays under 3 hours at arrival\n"
            "- Passenger informed 14+ days in advance"
        )

    # ------------------------------------------------------------------
    # Top routes by exposure
    # ------------------------------------------------------------------
    st.markdown("---")
    st.markdown("#### Top Routes by EU261 Exposure")

    if exposure["top_routes"]:
        routes_df = pd.DataFrame(exposure["top_routes"])

        fig = px.bar(
            routes_df.head(10),
            x="route",
            y="total_eur",
            color="total_eur",
            color_continuous_scale="Reds",
            labels={"route": "Route", "total_eur": "EU261 Exposure (EUR)"},
        )
        fig.update_layout(**CHART_LAYOUT, height=400, coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No route-level exposure data available.")

    # ------------------------------------------------------------------
    # Single flight calculator
    # ------------------------------------------------------------------
    st.markdown("---")
    st.markdown("#### Single Flight EU261 Calculator")

    calc_cols = st.columns(3)
    with calc_cols[0]:
        calc_distance = st.number_input("Route Distance (miles)", 100, 8000, 1200)
    with calc_cols[1]:
        calc_delay = st.number_input("Arrival Delay (minutes)", 0, 600, 200)
    with calc_cols[2]:
        calc_pax = st.number_input("Passengers", 50, 400, 160)

    result = calculate_eu261_compensation(calc_distance, calc_delay, calc_pax)

    if result["eligible"]:
        st.error(
            f"**EU261 TRIGGERED** | {result['explanation']} "
        )
    else:
        st.success(f"No EU261 liability. {result['explanation']}")

    # Operational cost breakdown
    st.markdown("#### Operational Cost Breakdown")
    op_cost = calculate_operational_cost(calc_delay)

    cost_items = {k: v for k, v in op_cost.items() if k != "total"}
    cost_df = pd.DataFrame([
        {"Category": k.replace("_", " ").title(), "Cost (EUR)": v}
        for k, v in cost_items.items()
    ])

    col_a, col_b = st.columns([2, 1])
    with col_a:
        fig = px.pie(
            cost_df,
            names="Category",
            values="Cost (EUR)",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        fig.update_layout(**CHART_LAYOUT, height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.metric("Total Operational Cost", f"EUR {op_cost['total']:,.0f}")
        if result["eligible"]:
            total_impact = op_cost["total"] + result["total_compensation_eur"]
            st.metric("Total Impact (Ops + EU261)", f"EUR {total_impact:,.0f}")
