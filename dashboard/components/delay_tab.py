"""Delay Analysis tab - breakdown by category, root cause, and impact."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from aerops.config import CHART_LAYOUT
from aerops.data.iata_codes import BTS_TO_IATA


def render_delay_analysis(delays_df: pd.DataFrame, filters: dict) -> None:
    """Render the Delay Analysis tab with Overview, Root Cause, and Impact sub-tabs."""
    st.markdown(
        '<h2><i class="fas fa-clock"></i> Delay Analysis</h2>',
        unsafe_allow_html=True,
    )

    if delays_df is None or delays_df.empty:
        st.info("No delay records available for the current filter selection.")
        return

    # ------------------------------------------------------------------
    # Top metrics row
    # ------------------------------------------------------------------
    total_delays = len(delays_df)
    avg_delay = 0.0
    critical_delays = 0

    if "arr_delay_minutes" in delays_df.columns:
        delay_mins = pd.to_numeric(delays_df["arr_delay_minutes"], errors="coerce").fillna(0)
        avg_delay = float(delay_mins[delay_mins > 0].mean()) if (delay_mins > 0).any() else 0.0
        critical_delays = int((delay_mins > 60).sum())

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Delays", f"{total_delays:,}")
    with c2:
        st.metric("Avg Delay", f"{avg_delay:.1f} min")
    with c3:
        st.metric("Critical (>60 min)", f"{critical_delays:,}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Sub-tabs
    # ------------------------------------------------------------------
    overview_tab, root_cause_tab, impact_tab = st.tabs(
        ["Overview", "Root Cause", "Impact"]
    )

    # ==================================================================
    # OVERVIEW
    # ==================================================================
    with overview_tab:
        _render_overview(delays_df)

    # ==================================================================
    # ROOT CAUSE
    # ==================================================================
    with root_cause_tab:
        _render_root_cause(delays_df)

    # ==================================================================
    # IMPACT
    # ==================================================================
    with impact_tab:
        _render_impact(delays_df)

    # ------------------------------------------------------------------
    # Bottom: raw data table
    # ------------------------------------------------------------------
    st.markdown("---")
    with st.expander("View Delay Records", expanded=False):
        display_cols = [
            c for c in [
                "flight_date", "airline", "flight_num", "route",
                "arr_delay_minutes", "primary_delay_cause",
                "iata_delay_category", "iata_delay_code",
            ]
            if c in delays_df.columns
        ]
        if display_cols:
            st.dataframe(
                delays_df[display_cols].sort_values(
                    "arr_delay_minutes", ascending=False
                ) if "arr_delay_minutes" in display_cols else delays_df[display_cols],
                use_container_width=True,
                height=400,
            )
        else:
            st.dataframe(delays_df.head(200), use_container_width=True, height=400)


# ======================================================================
# Private helpers
# ======================================================================

def _render_overview(delays_df: pd.DataFrame) -> None:
    """Horizontal bar of delay counts by IATA category + airline vs category heatmap."""
    col_left, col_right = st.columns(2)

    # -- Bar chart: delay counts by IATA delay category --
    with col_left:
        cat_col = "iata_delay_category"
        if cat_col in delays_df.columns:
            counts = delays_df[cat_col].dropna().value_counts().reset_index()
            counts.columns = ["Category", "Count"]
            if not counts.empty:
                fig = px.bar(
                    counts,
                    y="Category",
                    x="Count",
                    orientation="h",
                    color="Count",
                    color_continuous_scale=["#3b82f6", "#ef4444"],
                    title="Delay Count by IATA Category",
                )
                fig.update_layout(
                    height=400,
                    showlegend=False,
                    yaxis=dict(categoryorder="total ascending"),
                    **CHART_LAYOUT,
                )
                fig.update_xaxes(gridcolor="#334155")
                fig.update_yaxes(gridcolor="#334155")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No IATA delay categories recorded.")
        else:
            st.info("IATA delay category column not available in data.")

    # -- Heatmap: airline vs delay category --
    with col_right:
        if "airline" in delays_df.columns and "iata_delay_category" in delays_df.columns:
            cross = pd.crosstab(
                delays_df["airline"], delays_df["iata_delay_category"]
            )
            if not cross.empty:
                fig = go.Figure(
                    data=go.Heatmap(
                        z=cross.values,
                        x=cross.columns.tolist(),
                        y=cross.index.tolist(),
                        colorscale="YlOrRd",
                        hovertemplate="Airline: %{y}<br>Category: %{x}<br>Count: %{z}<extra></extra>",
                    )
                )
                fig.update_layout(
                    title="Airline vs Delay Category",
                    height=400,
                    xaxis_title="Delay Category",
                    yaxis_title="Airline",
                    **CHART_LAYOUT,
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough data for airline-category heatmap.")
        else:
            st.info("Airline or delay category column missing for heatmap.")


def _render_root_cause(delays_df: pd.DataFrame) -> None:
    """Show ranked primary delay causes if the column exists."""
    if "primary_delay_cause" not in delays_df.columns:
        st.info(
            "Primary delay cause column is not present in the dataset. "
            "This analysis requires BTS delay cause breakdown data."
        )
        return

    causes = delays_df["primary_delay_cause"].dropna().value_counts().reset_index()
    causes.columns = ["Cause", "Count"]

    if causes.empty:
        st.info("No primary delay causes recorded for the current selection.")
        return

    # Map BTS cause names to readable descriptions
    cause_labels = {}
    for bts_name, info in BTS_TO_IATA.items():
        cause_labels[bts_name] = f"{info['iata_category']} - {info['description']}"
    causes["Description"] = causes["Cause"].map(cause_labels).fillna(causes["Cause"])
    causes["Percentage"] = (causes["Count"] / causes["Count"].sum() * 100).round(1)

    st.markdown("#### Top Delay Causes (Ranked)")

    fig = px.bar(
        causes,
        x="Count",
        y="Description",
        orientation="h",
        text="Percentage",
        color="Count",
        color_continuous_scale=["#22c55e", "#eab308", "#ef4444"],
        title="Primary Delay Causes Ranked",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(
        height=max(350, len(causes) * 60),
        showlegend=False,
        yaxis=dict(categoryorder="total ascending"),
        **CHART_LAYOUT,
    )
    fig.update_xaxes(gridcolor="#334155", title_text="Number of Delays")
    fig.update_yaxes(gridcolor="#334155")
    st.plotly_chart(fig, use_container_width=True)

    # Summary table
    st.dataframe(
        causes[["Cause", "Description", "Count", "Percentage"]].rename(
            columns={"Percentage": "% of Total"}
        ),
        use_container_width=True,
        hide_index=True,
    )


def _render_impact(delays_df: pd.DataFrame) -> None:
    """Delay distribution histogram and route impact table."""
    col_hist, col_table = st.columns(2)

    # -- Histogram of delay distribution --
    with col_hist:
        if "arr_delay_minutes" in delays_df.columns:
            delay_mins = pd.to_numeric(
                delays_df["arr_delay_minutes"], errors="coerce"
            ).dropna()
            positive = delay_mins[delay_mins > 0]

            if not positive.empty:
                fig = px.histogram(
                    positive,
                    nbins=30,
                    title="Delay Duration Distribution",
                    labels={"value": "Delay (minutes)", "count": "Flights"},
                    color_discrete_sequence=["#ef4444"],
                )
                fig.update_layout(
                    height=400,
                    showlegend=False,
                    xaxis_title="Delay (minutes)",
                    yaxis_title="Number of Flights",
                    **CHART_LAYOUT,
                )
                fig.update_xaxes(gridcolor="#334155")
                fig.update_yaxes(gridcolor="#334155")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No positive delay values for histogram.")
        else:
            st.info("Arrival delay minutes column not available.")

    # -- Route impact table --
    with col_table:
        if "route" in delays_df.columns and "arr_delay_minutes" in delays_df.columns:
            delay_mins = pd.to_numeric(
                delays_df["arr_delay_minutes"], errors="coerce"
            ).fillna(0)
            df_tmp = delays_df.copy()
            df_tmp["_delay_min"] = delay_mins

            route_impact = (
                df_tmp.groupby("route")
                .agg(
                    delay_count=("_delay_min", "count"),
                    total_minutes=("_delay_min", "sum"),
                    avg_delay=("_delay_min", "mean"),
                )
                .reset_index()
                .sort_values("total_minutes", ascending=False)
            )
            route_impact.columns = [
                "Route",
                "Delay Count",
                "Total Minutes",
                "Avg Delay (min)",
            ]
            route_impact["Total Minutes"] = route_impact["Total Minutes"].round(0).astype(int)
            route_impact["Avg Delay (min)"] = route_impact["Avg Delay (min)"].round(1)

            st.markdown("#### Route Impact Summary")
            st.dataframe(
                route_impact.head(20),
                use_container_width=True,
                hide_index=True,
                height=400,
            )
        else:
            st.info("Route or delay minutes data not available for impact table.")
