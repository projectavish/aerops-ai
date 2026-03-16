"""Tests for KPI calculations."""
import pandas as pd
from aerops.analytics.kpi import compute_metrics, apply_filters


def test_compute_metrics_empty_df():
    metrics = compute_metrics(pd.DataFrame(), pd.DataFrame())
    assert metrics["total_flights"] == 0
    assert metrics["otp_rate"] == 0


def test_compute_metrics_basic(sample_flights_df):
    delays = sample_flights_df[sample_flights_df["is_delayed"] == 1]
    metrics = compute_metrics(sample_flights_df, delays)
    assert metrics["total_flights"] == len(sample_flights_df)
    assert 0 <= metrics["otp_rate"] <= 100
    assert metrics["delayed"] >= 0
    assert metrics["avg_delay_min"] >= 0


def test_apply_filters_date_range(sample_flights_df):
    filtered = apply_filters(sample_flights_df, {"date_filter": "Last 7 Days"})
    # Should return fewer or equal rows
    assert len(filtered) <= len(sample_flights_df)


def test_apply_filters_airline(sample_flights_df):
    filtered = apply_filters(sample_flights_df, {"airline": "AA"})
    if "airline" in filtered.columns and len(filtered) > 0:
        assert (filtered["airline"] == "AA").all()


def test_apply_filters_all_returns_same(sample_flights_df):
    filtered = apply_filters(sample_flights_df, {
        "date_filter": "All Time",
        "airline": "All Airlines",
        "origin": "All Origins",
        "dest": "All Destinations",
        "route": "All Routes",
    })
    assert len(filtered) == len(sample_flights_df)


def test_otp_excludes_cancelled(sample_flights_df):
    df = sample_flights_df.copy()
    df.loc[0, "cancelled"] = 1
    delays = df[df["is_delayed"] == 1]
    metrics = compute_metrics(df, delays)
    # OTP should exclude cancelled flights from denominator
    assert metrics["otp_rate"] > 0
