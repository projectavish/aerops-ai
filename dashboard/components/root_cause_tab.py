"""Deep Root Cause Analytics tab - BTS delay causes, trends, and attribution."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from aerops.config import CHART_LAYOUT
from aerops.data.iata_codes import (
    get_code_description,
    load_iata_codes,
    BTS_TO_IATA,
)

# BTS delay cause columns (lowercase, matching DB schema)
_DELAY_CAUSE_COLS = [
    "carrier_delay",
    "weather_delay",
    "nas_delay",
    "security_delay",
    "late_aircraft_delay",
]

# Human-readable labels for the BTS delay cause columns
_CAUSE_LABELS = {
    "carrier_delay": "Carrier",
    "weather_delay": "Weather",
    "nas_delay": "NAS / ATC",
    "security_delay": "Security",
    "late_aircraft_delay": "Late Aircraft",
}

# Responsibility mapping for attribution pie chart
_RESPONSIBILITY_MAP = {
    "carrier_delay": "Airline",
    "weather_delay": "Weather",
    "nas_delay": "ATC / NAS",
    "security_delay": "Airport",
    "late_aircraft_delay": "Airline",
}


def render_root_cause(
    ops_df: pd.DataFrame,
    delays_df: pd.DataFrame,
    filters: dict,
) -> None:
    """Render deep root cause analytics with BTS cause breakdown and trends."""
    st.markdown(
        '<h2><i class="fas fa-search"></i> Root Cause Analytics</h2>',
        unsafe_allow_html=True,
    )

    if ops_df is None or ops_df.empty:
        st.info("No operations data available for root cause analysis.")
        return

    # Identify which delay cause columns exist
    available_cause_cols = [c for c in _DELAY_CAUSE_COLS if c in ops_df.columns]

    if not available_cause_cols:
        st.warning(
            "BTS delay cause breakdown columns (carrier_delay, weather_delay, etc.) "
            "are not present in the dataset. Root cause analysis requires these columns."
        )
        return

    # ------------------------------------------------------------------
    # Section 1: BTS Delay Cause Breakdown (stacked bar)
    # ------------------------------------------------------------------
    st.markdown("#### BTS Delay Cause Breakdown")
    _render_cause_breakdown(ops_df, available_cause_cols)

    st.markdown("---")

    # ------------------------------------------------------------------
    # Section 2: Monthly Trend (stacked area)
    # ------------------------------------------------------------------
    st.markdown("#### Monthly Delay Cause Trend")
    _render_monthly_trend(ops_df, available_cause_cols)

    st.markdown("---")

    # ------------------------------------------------------------------
    # Section 3: Airport drill-down
    # ------------------------------------------------------------------
    st.markdown("#### Airport Delay Cause Profile")
    _render_airport_drilldown(ops_df, available_cause_cols)

    st.markdown("---")

    # ------------------------------------------------------------------
    # Section 4: IATA Code Reference
    # ------------------------------------------------------------------
    st.markdown("#### IATA Delay Code Distribution")
    _render_iata_distribution(delays_df)

    st.markdown("---")

    # ------------------------------------------------------------------
    # Section 5: Responsibility Attribution Pie
    # ------------------------------------------------------------------
    st.markdown("#### Delay Responsibility Attribution")
    _render_responsibility_pie(ops_df, available_cause_cols)


# ======================================================================
# Private helpers
# ======================================================================

def _ensure_numeric_causes(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Ensure delay cause columns are numeric."""
    out = df.copy()
    for c in cols:
        out[c] = pd.to_numeric(out[c], errors="coerce").fillna(0)
    return out


def _render_cause_breakdown(ops_df: pd.DataFrame, cause_cols: list[str]) -> None:
    """Stacked bar chart showing proportional delay cause minutes."""
    df = _ensure_numeric_causes(ops_df, cause_cols)

    # Only include rows that have at least some delay
    df["_total_cause"] = df[cause_cols].sum(axis=1)
    delayed = df[df["_total_cause"] > 0]

    if delayed.empty:
        st.info("No delay cause data to display.")
        return

    # Aggregate totals
    totals = {}
    for col in cause_cols:
        totals[_CAUSE_LABELS.get(col, col)] = float(delayed[col].sum())

    cause_df = pd.DataFrame(
        {"Cause": list(totals.keys()), "Total Minutes": list(totals.values())}
    )
    cause_df = cause_df.sort_values("Total Minutes", ascending=True)
    cause_df["Percentage"] = (
        cause_df["Total Minutes"] / cause_df["Total Minutes"].sum() * 100
    ).round(1)

    colors = ["#3b82f6", "#eab308", "#8b5cf6", "#94a3b8", "#ef4444"]

    fig = px.bar(
        cause_df,
        x="Total Minutes",
        y="Cause",
        orientation="h",
        color="Cause",
        color_discrete_sequence=colors[: len(cause_df)],
        text="Percentage",
        title="Total Delay Minutes by BTS Cause Category",
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig.update_layout(
        height=350,
        showlegend=False,
        yaxis=dict(categoryorder="total ascending"),
        **CHART_LAYOUT,
    )
    fig.update_xaxes(gridcolor="#334155", title_text="Total Delay Minutes")
    fig.update_yaxes(gridcolor="#334155")
    st.plotly_chart(fig, use_container_width=True)


def _render_monthly_trend(ops_df: pd.DataFrame, cause_cols: list[str]) -> None:
    """Stacked area chart of delay causes over time (monthly)."""
    if "flight_date" not in ops_df.columns:
        st.info("Flight date column not available for trend analysis.")
        return

    df = _ensure_numeric_causes(ops_df, cause_cols)
    df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")
    df = df[df["flight_date"].notna()]

    if df.empty:
        st.info("No valid dates for monthly trend.")
        return

    df["month_period"] = df["flight_date"].dt.to_period("M").dt.to_timestamp()

    monthly = df.groupby("month_period")[cause_cols].sum().reset_index()

    # Rename columns for display
    rename = {c: _CAUSE_LABELS.get(c, c) for c in cause_cols}
    monthly = monthly.rename(columns=rename)
    label_cols = [rename[c] for c in cause_cols]

    fig = go.Figure()
    area_colors = ["#3b82f6", "#eab308", "#8b5cf6", "#94a3b8", "#ef4444"]
    for i, col in enumerate(label_cols):
        fig.add_trace(
            go.Scatter(
                x=monthly["month_period"],
                y=monthly[col],
                name=col,
                mode="lines",
                stackgroup="one",
                line=dict(width=0.5, color=area_colors[i % len(area_colors)]),
                fillcolor=area_colors[i % len(area_colors)],
            )
        )

    fig.update_layout(
        title="Monthly Delay Cause Trend (Stacked)",
        height=400,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis_title="Month",
        yaxis_title="Total Delay Minutes",
        **CHART_LAYOUT,
    )
    fig.update_xaxes(gridcolor="#334155")
    fig.update_yaxes(gridcolor="#334155")
    st.plotly_chart(fig, use_container_width=True)


def _render_airport_drilldown(ops_df: pd.DataFrame, cause_cols: list[str]) -> None:
    """Selectbox to pick an airport, then show that airport's delay profile."""
    airport_col = "origin"
    if airport_col not in ops_df.columns:
        st.info("Origin airport column not found.")
        return

    airports = sorted(ops_df[airport_col].dropna().unique().tolist())
    if not airports:
        st.info("No airports available for drill-down.")
        return

    selected = st.selectbox(
        "Select Airport",
        airports,
        key="root_cause_airport_select",
    )

    df = _ensure_numeric_causes(ops_df, cause_cols)
    airport_data = df[df[airport_col] == selected]

    if airport_data.empty:
        st.info(f"No data available for airport {selected}.")
        return

    # Aggregate causes for this airport
    totals = {}
    for col in cause_cols:
        totals[_CAUSE_LABELS.get(col, col)] = float(airport_data[col].sum())

    total_all = sum(totals.values())
    if total_all == 0:
        st.info(f"No recorded delay cause minutes for {selected}.")
        return

    cause_df = pd.DataFrame(
        {"Cause": list(totals.keys()), "Minutes": list(totals.values())}
    )
    cause_df["Percentage"] = (cause_df["Minutes"] / total_all * 100).round(1)
    cause_df = cause_df.sort_values("Minutes", ascending=False)

    col_chart, col_stats = st.columns([2, 1])

    with col_chart:
        fig = px.pie(
            cause_df,
            names="Cause",
            values="Minutes",
            title=f"Delay Cause Profile - {selected}",
            color_discrete_sequence=["#3b82f6", "#eab308", "#8b5cf6", "#94a3b8", "#ef4444"],
            hole=0.35,
        )
        fig.update_layout(height=350, **CHART_LAYOUT)
        fig.update_traces(textinfo="label+percent", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col_stats:
        total_flights = len(airport_data)
        delayed_flights = int((airport_data[cause_cols].sum(axis=1) > 0).sum())
        avg_delay = 0.0
        if "arr_delay_minutes" in airport_data.columns:
            d = pd.to_numeric(airport_data["arr_delay_minutes"], errors="coerce")
            avg_delay = float(d[d > 0].mean()) if (d > 0).any() else 0.0

        st.metric("Total Flights", f"{total_flights:,}")
        st.metric("Delayed Flights", f"{delayed_flights:,}")
        st.metric("Avg Delay", f"{avg_delay:.1f} min")
        st.markdown("**Cause Breakdown:**")
        st.dataframe(
            cause_df[["Cause", "Minutes", "Percentage"]].rename(
                columns={"Percentage": "%"}
            ),
            use_container_width=True,
            hide_index=True,
        )


def _render_iata_distribution(delays_df: pd.DataFrame) -> None:
    """Show IATA delay codes with their descriptions."""
    if delays_df is None or delays_df.empty:
        st.info("No delay data available for IATA code analysis.")
        return

    code_col = "iata_delay_code"
    cat_col = "iata_delay_category"

    if code_col not in delays_df.columns:
        st.info("IATA delay code column not available in the dataset.")
        return

    code_counts = delays_df[code_col].dropna().value_counts().reset_index()
    code_counts.columns = ["IATA Code", "Count"]

    if code_counts.empty:
        st.info("No IATA delay codes recorded.")
        return

    # Add descriptions
    code_counts["Description"] = code_counts["IATA Code"].apply(
        lambda c: get_code_description(str(c))
    )

    # Add category if available
    if cat_col in delays_df.columns:
        cat_map = (
            delays_df[[code_col, cat_col]]
            .dropna()
            .drop_duplicates()
            .set_index(code_col)[cat_col]
            .to_dict()
        )
        code_counts["Category"] = code_counts["IATA Code"].map(cat_map).fillna("Unknown")

    code_counts["Percentage"] = (
        code_counts["Count"] / code_counts["Count"].sum() * 100
    ).round(1)

    col_chart, col_table = st.columns([1, 1])

    with col_chart:
        fig = px.bar(
            code_counts,
            x="IATA Code",
            y="Count",
            color="Count",
            color_continuous_scale=["#3b82f6", "#ef4444"],
            title="IATA Delay Code Frequency",
            hover_data=["Description"],
        )
        fig.update_layout(
            height=350,
            showlegend=False,
            **CHART_LAYOUT,
        )
        fig.update_xaxes(gridcolor="#334155", type="category")
        fig.update_yaxes(gridcolor="#334155")
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        display_cols = ["IATA Code", "Description"]
        if "Category" in code_counts.columns:
            display_cols.append("Category")
        display_cols += ["Count", "Percentage"]

        st.markdown("**IATA Delay Code Reference**")
        st.dataframe(
            code_counts[display_cols],
            use_container_width=True,
            hide_index=True,
            height=350,
        )


def _render_responsibility_pie(ops_df: pd.DataFrame, cause_cols: list[str]) -> None:
    """Pie chart: Airline vs ATC vs Weather vs Airport responsibility."""
    df = _ensure_numeric_causes(ops_df, cause_cols)

    responsibility_totals: dict[str, float] = {}
    for col in cause_cols:
        resp = _RESPONSIBILITY_MAP.get(col, "Other")
        responsibility_totals[resp] = (
            responsibility_totals.get(resp, 0.0) + float(df[col].sum())
        )

    total = sum(responsibility_totals.values())
    if total == 0:
        st.info("No delay cause minutes available for responsibility attribution.")
        return

    resp_df = pd.DataFrame(
        {
            "Responsibility": list(responsibility_totals.keys()),
            "Minutes": list(responsibility_totals.values()),
        }
    )
    resp_df["Percentage"] = (resp_df["Minutes"] / total * 100).round(1)
    resp_df = resp_df.sort_values("Minutes", ascending=False)

    color_map = {
        "Airline": "#3b82f6",
        "ATC / NAS": "#8b5cf6",
        "Weather": "#eab308",
        "Airport": "#94a3b8",
        "Other": "#64748b",
    }

    col_pie, col_summary = st.columns([2, 1])

    with col_pie:
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=resp_df["Responsibility"],
                    values=resp_df["Minutes"],
                    hole=0.4,
                    textinfo="label+percent",
                    textposition="outside",
                    marker_colors=[
                        color_map.get(r, "#64748b")
                        for r in resp_df["Responsibility"]
                    ],
                )
            ]
        )
        fig.update_layout(
            title="Delay Responsibility Attribution",
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.15,
                xanchor="center",
                x=0.5,
            ),
            **CHART_LAYOUT,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_summary:
        st.markdown("**Attribution Summary**")
        for _, row in resp_df.iterrows():
            resp = row["Responsibility"]
            mins = int(row["Minutes"])
            pct = row["Percentage"]
            color = color_map.get(resp, "#64748b")
            st.markdown(
                f'<div style="border-left:4px solid {color}; padding:0.5rem 0.75rem; '
                f'margin-bottom:0.4rem; background:#1e293b; border-radius:0 6px 6px 0;">'
                f'<strong style="color:{color};">{resp}</strong><br>'
                f'<span style="color:#e2e8f0;">{mins:,} min ({pct}%)</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.markdown(
            '<p style="font-size:0.75rem; color:#94a3b8 !important;">'
            "Attribution based on BTS delay cause columns: Carrier and Late Aircraft "
            "delays are attributed to Airlines; NAS delays to ATC; Weather delays to "
            "Weather; Security delays to Airport operations.</p>",
            unsafe_allow_html=True,
        )
