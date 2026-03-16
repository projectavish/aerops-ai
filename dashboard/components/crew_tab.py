"""Airline & Fleet Performance tab (replaces crew tab for BTS data)."""
import streamlit as st
import pandas as pd
import plotly.express as px

from aerops.config import CHART_LAYOUT


def render_airline_performance(ops_df: pd.DataFrame, filters: dict) -> None:
    """Render airline and fleet performance metrics, charts, and leaderboard."""
    st.markdown(
        '<h2><i class="fas fa-building"></i> Airline & Fleet Performance</h2>',
        unsafe_allow_html=True,
    )

    if ops_df is None or ops_df.empty:
        st.info("No operations data available for airline performance analysis.")
        return

    # ------------------------------------------------------------------
    # Top metrics
    # ------------------------------------------------------------------
    unique_airlines = ops_df["airline"].nunique() if "airline" in ops_df.columns else 0
    avg_flights = 0
    best_otp_airline = "N/A"

    if "airline" in ops_df.columns:
        flights_per_airline = ops_df.groupby("airline").size()
        avg_flights = int(flights_per_airline.mean()) if not flights_per_airline.empty else 0

        if "is_delayed" in ops_df.columns:
            airline_stats = ops_df.groupby("airline").agg(
                total=("is_delayed", "count"),
                delayed=("is_delayed", "sum"),
            )
            airline_stats["otp"] = (
                (airline_stats["total"] - airline_stats["delayed"])
                / airline_stats["total"]
                * 100
            )
            if not airline_stats.empty:
                best_otp_airline = airline_stats["otp"].idxmax()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Unique Airlines", f"{unique_airlines}")
    with c2:
        st.metric("Avg Flights / Airline", f"{avg_flights:,}")
    with c3:
        st.metric("Best OTP Airline", best_otp_airline)

    st.markdown("---")

    # ------------------------------------------------------------------
    # Charts row
    # ------------------------------------------------------------------
    if "airline" not in ops_df.columns:
        st.info("Airline column not found in the dataset.")
        return

    col_left, col_right = st.columns(2)

    # -- Flights by airline bar chart --
    with col_left:
        flight_counts = (
            ops_df["airline"]
            .value_counts()
            .reset_index()
        )
        flight_counts.columns = ["Airline", "Flights"]
        if not flight_counts.empty:
            fig = px.bar(
                flight_counts.head(15),
                x="Airline",
                y="Flights",
                color="Flights",
                color_continuous_scale=["#3b82f6", "#0ea5e9"],
                title="Total Flights by Airline",
            )
            fig.update_layout(
                height=400,
                showlegend=False,
                **CHART_LAYOUT,
            )
            fig.update_xaxes(gridcolor="#334155")
            fig.update_yaxes(gridcolor="#334155")
            st.plotly_chart(fig, use_container_width=True)

    # -- OTP% by airline bar chart --
    with col_right:
        if "is_delayed" in ops_df.columns:
            airline_otp = ops_df.groupby("airline").agg(
                total=("is_delayed", "count"),
                delayed=("is_delayed", "sum"),
            ).reset_index()
            airline_otp["on_time"] = airline_otp["total"] - airline_otp["delayed"]
            airline_otp["OTP%"] = (
                airline_otp["on_time"] / airline_otp["total"] * 100
            ).round(1)
            airline_otp = airline_otp.sort_values("OTP%", ascending=False)

            if not airline_otp.empty:
                fig = px.bar(
                    airline_otp.head(15),
                    x="airline",
                    y="OTP%",
                    color="OTP%",
                    color_continuous_scale=["#ef4444", "#eab308", "#22c55e"],
                    title="On-Time Performance by Airline",
                    range_color=[60, 100],
                )
                fig.update_layout(
                    height=400,
                    showlegend=False,
                    xaxis_title="Airline",
                    **CHART_LAYOUT,
                )
                fig.update_xaxes(gridcolor="#334155")
                fig.update_yaxes(gridcolor="#334155")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Delay flag column not available for OTP calculation.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Leaderboard table
    # ------------------------------------------------------------------
    st.markdown("#### Airline Performance Leaderboard")
    _render_leaderboard(ops_df)

    # ------------------------------------------------------------------
    # Tail number analysis
    # ------------------------------------------------------------------
    if "tail_num" in ops_df.columns:
        st.markdown("---")
        st.markdown("#### Aircraft (Tail Number) Utilization")
        _render_tail_analysis(ops_df)


# ======================================================================
# Private helpers
# ======================================================================

def _render_leaderboard(ops_df: pd.DataFrame) -> None:
    """Build and display airline leaderboard with key stats."""
    if "airline" not in ops_df.columns:
        st.info("No airline data available.")
        return

    agg_dict = {"airline": "count"}
    rename = {"airline": "Total Flights"}

    if "is_delayed" in ops_df.columns:
        agg_dict["is_delayed"] = "sum"
        rename["is_delayed"] = "Delayed"

    if "arr_delay_minutes" in ops_df.columns:
        agg_dict["arr_delay_minutes"] = "mean"
        rename["arr_delay_minutes"] = "Avg Delay (min)"

    leaderboard = (
        ops_df.groupby("airline", as_index=False)
        .agg(agg_dict)
        .rename(columns=rename)
    )
    leaderboard = leaderboard.rename(columns={"airline": "Airline"})

    if "Delayed" in leaderboard.columns:
        leaderboard["On Time"] = leaderboard["Total Flights"] - leaderboard["Delayed"]
        leaderboard["OTP%"] = (
            leaderboard["On Time"] / leaderboard["Total Flights"] * 100
        ).round(1)
        leaderboard["Delayed"] = leaderboard["Delayed"].astype(int)
        leaderboard["On Time"] = leaderboard["On Time"].astype(int)

    if "Avg Delay (min)" in leaderboard.columns:
        leaderboard["Avg Delay (min)"] = leaderboard["Avg Delay (min)"].round(1)

    leaderboard = leaderboard.sort_values("Total Flights", ascending=False)

    # Reorder columns for display
    display_order = [
        "Airline", "Total Flights", "On Time", "Delayed", "OTP%", "Avg Delay (min)"
    ]
    display_order = [c for c in display_order if c in leaderboard.columns]

    st.dataframe(
        leaderboard[display_order],
        use_container_width=True,
        hide_index=True,
        height=400,
    )


def _render_tail_analysis(ops_df: pd.DataFrame) -> None:
    """Show most-used aircraft by tail number."""
    tails = ops_df["tail_num"].dropna().astype(str)
    tails = tails[tails.str.strip() != ""]

    if tails.empty:
        st.info("No tail number data available.")
        return

    tail_counts = tails.value_counts().reset_index()
    tail_counts.columns = ["Tail Number", "Flights"]

    col_chart, col_table = st.columns(2)

    with col_chart:
        fig = px.bar(
            tail_counts.head(15),
            x="Tail Number",
            y="Flights",
            color="Flights",
            color_continuous_scale=["#3b82f6", "#8b5cf6"],
            title="Most Active Aircraft",
        )
        fig.update_layout(
            height=350,
            showlegend=False,
            **CHART_LAYOUT,
        )
        fig.update_xaxes(gridcolor="#334155", tickangle=45)
        fig.update_yaxes(gridcolor="#334155")
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown("**Top 20 Aircraft by Flight Count**")
        st.dataframe(
            tail_counts.head(20),
            use_container_width=True,
            hide_index=True,
            height=350,
        )
