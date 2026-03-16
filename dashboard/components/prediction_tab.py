"""ML-powered delay prediction tab."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from pathlib import Path

from aerops.config import CHART_LAYOUT, DB_PATH, DELAY_MODEL_PATH
from aerops.analytics.kpi import safe_unique_sorted


def render_prediction(ops_df: pd.DataFrame, db_path: str = DB_PATH) -> None:
    """Render the delay prediction tab with ML model inference."""
    st.header("ML Delay Prediction")

    model_exists = Path(DELAY_MODEL_PATH).exists()

    if not model_exists:
        st.warning(
            "No trained model found. Run `python scripts/train_model.py` to train the delay prediction model."
        )
        _render_historical_stats(ops_df)
        return

    # Load model
    try:
        from aerops.models.delay_predictor import DelayPredictor
        predictor = DelayPredictor()
        predictor.load()
        st.success("Model loaded successfully")
    except Exception as e:
        st.error(f"Failed to load model: {e}")
        _render_historical_stats(ops_df)
        return

    # User inputs
    st.subheader("Predict Flight Delay")
    col1, col2, col3 = st.columns(3)

    origins = safe_unique_sorted(ops_df, "origin") if ops_df is not None else []
    dests = safe_unique_sorted(ops_df, "dest") if ops_df is not None else []
    airlines = safe_unique_sorted(ops_df, "airline") if ops_df is not None else []

    with col1:
        origin = st.selectbox("Origin Airport", origins if origins else ["ATL", "JFK", "LAX", "ORD", "DFW"], key="pred_origin")
        airline = st.selectbox("Airline", airlines if airlines else ["AA", "DL", "UA", "WN"], key="pred_airline")
    with col2:
        dest = st.selectbox("Destination Airport", dests if dests else ["LAX", "JFK", "ATL", "SFO", "MIA"], key="pred_dest")
        dep_hour = st.slider("Departure Hour", 0, 23, 14, key="pred_hour")
    with col3:
        day_of_week = st.selectbox(
            "Day of Week",
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            key="pred_dow",
        )
        month = st.selectbox("Month", list(range(1, 13)), index=2, key="pred_month")

    dow_map = {"Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
               "Friday": 4, "Saturday": 5, "Sunday": 6}

    if st.button("Predict Delay", type="primary"):
        features = {
            "origin": origin,
            "dest": dest,
            "airline": airline,
            "dep_hour": dep_hour,
            "day_of_week": dow_map[day_of_week],
            "month": month,
            "is_weekend": 1 if dow_map[day_of_week] >= 5 else 0,
            "distance": 1000,
            "crs_elapsed_time": 180,
        }

        # Get distance from data if available
        if ops_df is not None and not ops_df.empty:
            route = f"{origin}-{dest}"
            route_data = ops_df[ops_df["route"] == route]
            if not route_data.empty and "distance" in route_data.columns:
                features["distance"] = float(route_data["distance"].median())
            if not route_data.empty and "crs_elapsed_time" in route_data.columns:
                elapsed = pd.to_numeric(route_data["crs_elapsed_time"], errors="coerce").median()
                if not pd.isna(elapsed):
                    features["crs_elapsed_time"] = float(elapsed)

        try:
            prob, est_minutes = predictor.predict(features)
        except Exception as e:
            st.error(f"Prediction failed: {e}")
            return

        st.markdown("---")

        # Results
        r1, r2, r3 = st.columns(3)
        with r1:
            color = "#ef4444" if prob > 0.5 else "#eab308" if prob > 0.3 else "#22c55e"
            st.markdown(f"### Delay Probability")
            _render_gauge(prob, color)
        with r2:
            st.metric("Estimated Delay", f"{est_minutes:.0f} min" if prob > 0.3 else "On Time")
            risk = "HIGH" if prob > 0.5 else "MEDIUM" if prob > 0.3 else "LOW"
            st.metric("Risk Level", risk)
        with r3:
            st.metric("Route", f"{origin}-{dest}")
            st.metric("Departure", f"{dep_hour:02d}:00 {day_of_week}")

        # Feature importances
        importances = predictor.get_feature_importances()
        if importances:
            st.subheader("Key Prediction Factors")
            top_features = dict(list(importances.items())[:10])
            fig = go.Figure(go.Bar(
                x=list(top_features.values()),
                y=list(top_features.keys()),
                orientation="h",
                marker_color="#0ea5e9",
            ))
            fig.update_layout(
                title="Feature Importance (Top 10)",
                height=350, yaxis=dict(autorange="reversed"),
                **CHART_LAYOUT,
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    _render_historical_stats(ops_df)


def _render_gauge(probability: float, color: str) -> None:
    """Render a probability gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=probability * 100,
        number={"suffix": "%", "font": {"size": 48, "color": color}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "#64748b"},
            "bar": {"color": color},
            "bgcolor": "#1e293b",
            "steps": [
                {"range": [0, 30], "color": "rgba(34, 197, 94, 0.2)"},
                {"range": [30, 50], "color": "rgba(234, 179, 8, 0.2)"},
                {"range": [50, 100], "color": "rgba(239, 68, 68, 0.2)"},
            ],
        },
    ))
    fig.update_layout(height=250, margin=dict(t=20, b=20), **CHART_LAYOUT)
    st.plotly_chart(fig, use_container_width=True)


def _render_historical_stats(ops_df: pd.DataFrame) -> None:
    """Show historical delay statistics as context."""
    if ops_df is None or ops_df.empty:
        return

    st.subheader("Historical Delay Patterns")

    col1, col2 = st.columns(2)

    with col1:
        # Delay rate by hour
        if "dep_hour" in ops_df.columns and "is_delayed" in ops_df.columns:
            hourly = ops_df.groupby("dep_hour")["is_delayed"].mean() * 100
            fig = go.Figure(go.Bar(
                x=hourly.index, y=hourly.values,
                marker_color=["#ef4444" if v > 25 else "#eab308" if v > 15 else "#22c55e" for v in hourly.values],
            ))
            fig.update_layout(
                title="Delay Rate by Departure Hour",
                xaxis_title="Hour", yaxis_title="Delay Rate (%)",
                height=350, **CHART_LAYOUT,
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Delay rate by day of week
        if "day_of_week" in ops_df.columns and "is_delayed" in ops_df.columns:
            dow_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            daily = ops_df.groupby("day_of_week")["is_delayed"].mean() * 100
            fig = go.Figure(go.Bar(
                x=[dow_names[i] for i in daily.index],
                y=daily.values,
                marker_color="#0ea5e9",
            ))
            fig.update_layout(
                title="Delay Rate by Day of Week",
                xaxis_title="Day", yaxis_title="Delay Rate (%)",
                height=350, **CHART_LAYOUT,
            )
            st.plotly_chart(fig, use_container_width=True)
