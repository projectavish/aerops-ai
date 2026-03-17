"""Route Analytics tab - route volume, performance, and distance analysis."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from aerops.config import CHART_LAYOUT


def render_route_insights(ops_df: pd.DataFrame, filters: dict) -> None:
    """Render route analytics with volume, status breakdown, and scatter plot."""
    st.markdown(
        '<h2><i class="fas fa-route"></i> Route Analytics</h2>',
        unsafe_allow_html=True,
    )

    if ops_df is None or ops_df.empty:
        st.info("No operations data available for route analysis.")
        return

    if "route" not in ops_df.columns:
        st.info("Route column not found in the dataset.")
        return

    # ------------------------------------------------------------------
    # Top metrics
    # ------------------------------------------------------------------
    active_routes = ops_df["route"].nunique()

    avg_distance = 0.0
    if "distance" in ops_df.columns:
        dist = pd.to_numeric(ops_df["distance"], errors="coerce").dropna()
        avg_distance = float(dist.mean()) if not dist.empty else 0.0

    busiest_route = "N/A"
    route_counts = ops_df["route"].value_counts()
    if not route_counts.empty:
        busiest_route = f"{route_counts.index[0]} ({route_counts.iloc[0]:,})"

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Active Routes", f"{active_routes:,}")
    with c2:
        st.metric("Avg Distance", f"{avg_distance:,.0f} mi")
    with c3:
        st.metric("Busiest Route", busiest_route)

    st.markdown("---")

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------
    col_left, col_right = st.columns(2)

    # -- Top 15 routes by flight volume --
    with col_left:
        top_routes = route_counts.head(15).reset_index()
        top_routes.columns = ["Route", "Flights"]

        fig = px.bar(
            top_routes,
            x="Flights",
            y="Route",
            orientation="h",
            color="Flights",
            color_continuous_scale=["#3b82f6", "#0ea5e9"],
            title="Top 15 Routes by Flight Volume",
        )
        fig.update_layout(
            height=500,
            showlegend=False,
            yaxis=dict(categoryorder="total ascending"),
            **CHART_LAYOUT,
        )
        fig.update_xaxes(gridcolor="#334155")
        fig.update_yaxes(gridcolor="#334155")
        st.plotly_chart(fig, use_container_width=True)

    # -- Stacked bar: route status breakdown --
    with col_right:
        _render_status_breakdown(ops_df, route_counts)

    st.markdown("---")

    # ------------------------------------------------------------------
    # Route performance summary table
    # ------------------------------------------------------------------
    st.markdown("#### Route Performance Summary")
    _render_route_table(ops_df)

    st.markdown("---")

    # ------------------------------------------------------------------
    # Distance vs Delay scatter
    # ------------------------------------------------------------------
    st.markdown("#### Distance vs Delay Analysis")
    _render_distance_scatter(ops_df)


# ======================================================================
# Private helpers
# ======================================================================

def _render_status_breakdown(ops_df: pd.DataFrame, route_counts: pd.Series) -> None:
    """Stacked bar of on-time / delayed / cancelled for top routes."""
    top_route_names = route_counts.head(15).index.tolist()
    subset = ops_df[ops_df["route"].isin(top_route_names)].copy()

    if subset.empty:
        st.info("No route data for status breakdown.")
        return

    # Classify flights
    def _classify(row):
        if "cancelled" in row.index and row.get("cancelled", 0) == 1:
            return "Cancelled"
        if "is_delayed" in row.index and row.get("is_delayed", 0) == 1:
            return "Delayed"
        return "On Time"

    has_status_cols = "is_delayed" in subset.columns or "cancelled" in subset.columns
    if not has_status_cols:
        st.info("Delay/cancellation columns not available for status breakdown.")
        return

    subset["_status"] = subset.apply(_classify, axis=1)

    status_counts = (
        subset.groupby(["route", "_status"])
        .size()
        .reset_index(name="count")
    )

    color_map = {"On Time": "#22c55e", "Delayed": "#ef4444", "Cancelled": "#94a3b8"}

    fig = px.bar(
        status_counts,
        x="count",
        y="route",
        color="_status",
        orientation="h",
        color_discrete_map=color_map,
        title="Route Status Breakdown",
        labels={"_status": "Status", "count": "Flights", "route": "Route"},
    )
    fig.update_layout(
        height=500,
        barmode="stack",
        yaxis=dict(categoryorder="total ascending"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        **CHART_LAYOUT,
    )
    fig.update_xaxes(gridcolor="#334155")
    fig.update_yaxes(gridcolor="#334155")
    st.plotly_chart(fig, use_container_width=True)


def _render_route_table(ops_df: pd.DataFrame) -> None:
    """Route performance summary with OTP%, avg delay, distance."""
    agg_dict = {"route": "count"}
    rename_map = {"route": "Flights"}

    if "is_delayed" in ops_df.columns:
        agg_dict["is_delayed"] = "sum"
        rename_map["is_delayed"] = "Delayed"

    if "arr_delay_minutes" in ops_df.columns:
        agg_dict["arr_delay_minutes"] = "mean"
        rename_map["arr_delay_minutes"] = "Avg Delay (min)"

    if "distance" in ops_df.columns:
        agg_dict["distance"] = "mean"
        rename_map["distance"] = "Avg Distance (mi)"

    summary = (
        ops_df.groupby("route", as_index=False)
        .agg(agg_dict)
        .rename(columns=rename_map)
    )
    summary = summary.rename(columns={"route": "Route"})

    if "Delayed" in summary.columns:
        summary["OTP%"] = (
            (summary["Flights"] - summary["Delayed"]) / summary["Flights"] * 100
        ).round(1)
        summary["Delayed"] = summary["Delayed"].astype(int)

    if "Avg Delay (min)" in summary.columns:
        summary["Avg Delay (min)"] = summary["Avg Delay (min)"].round(1)

    if "Avg Distance (mi)" in summary.columns:
        summary["Avg Distance (mi)"] = summary["Avg Distance (mi)"].round(0).astype(int)

    summary = summary.sort_values("Flights", ascending=False)

    display_order = [
        "Route", "Flights", "OTP%", "Avg Delay (min)", "Avg Distance (mi)"
    ]
    display_order = [c for c in display_order if c in summary.columns]

    st.dataframe(
        summary[display_order].head(30),
        use_container_width=True,
        hide_index=True,
        height=400,
    )


def _render_distance_scatter(ops_df: pd.DataFrame) -> None:
    """Scatter plot of distance vs arrival delay."""
    if "distance" not in ops_df.columns or "arr_delay_minutes" not in ops_df.columns:
        st.info("Distance or delay data not available for scatter analysis.")
        return

    df = ops_df[["distance", "arr_delay_minutes"]].copy()
    df["distance"] = pd.to_numeric(df["distance"], errors="coerce")
    df["arr_delay_minutes"] = pd.to_numeric(df["arr_delay_minutes"], errors="coerce")
    df = df.dropna()

    # Only show delayed flights for clearer visualization
    df = df[df["arr_delay_minutes"] > 0]

    if df.empty or len(df) < 5:
        st.info("Not enough data points for distance-delay scatter plot.")
        return

    # Sample for performance if too many points
    if len(df) > 2000:
        df = df.sample(2000, random_state=42)

    fig = px.scatter(
        df,
        x="distance",
        y="arr_delay_minutes",
        opacity=0.5,
        color="arr_delay_minutes",
        color_continuous_scale=["#3b82f6", "#eab308", "#ef4444"],
        title="Route Distance vs Arrival Delay",
        labels={
            "distance": "Distance (miles)",
            "arr_delay_minutes": "Arrival Delay (min)",
        },
    )
    # Add trendline manually with OLS
    try:
        import numpy as np
        z = np.polyfit(df["distance"], df["arr_delay_minutes"], 1)
        p = np.poly1d(z)
        x_range = [df["distance"].min(), df["distance"].max()]
        fig.add_trace(
            go.Scatter(
                x=x_range,
                y=[p(x_range[0]), p(x_range[1])],
                mode="lines",
                name="Trend",
                line=dict(color="#38bdf8", width=2, dash="dash"),
            )
        )
    except Exception:
        pass  # Skip trendline if numpy not available or fit fails

    fig.update_layout(
        height=450,
        showlegend=True,
        **CHART_LAYOUT,
    )
    fig.update_xaxes(gridcolor="#334155")
    fig.update_yaxes(gridcolor="#334155")
    st.plotly_chart(fig, use_container_width=True)
