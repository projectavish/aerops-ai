"""Tests for BTS data ingestion pipeline."""
import pandas as pd
from aerops.data.bts_loader import engineer_features, parse_bts_csv


def test_engineer_features_adds_route(sample_bts_df):
    df = engineer_features(sample_bts_df.copy())
    assert "route" in df.columns
    assert all("-" in r for r in df["route"].dropna())


def test_engineer_features_adds_temporal(sample_bts_df):
    df = engineer_features(sample_bts_df.copy())
    assert "dep_hour" in df.columns
    assert "day_of_week" in df.columns
    assert "month" in df.columns
    assert "is_weekend" in df.columns
    assert df["dep_hour"].between(0, 23).all()
    assert df["day_of_week"].between(0, 6).all()


def test_engineer_features_assigns_delay_cause(sample_bts_df):
    df = engineer_features(sample_bts_df.copy())
    assert "primary_delay_cause" in df.columns
    valid_causes = {
        "CarrierDelay", "WeatherDelay", "NASDelay",
        "SecurityDelay", "LateAircraftDelay", None,
    }
    unique_causes = set(df["primary_delay_cause"].dropna().unique())
    assert unique_causes.issubset(valid_causes)


def test_engineer_features_is_delayed_flag(sample_bts_df):
    df = engineer_features(sample_bts_df.copy())
    assert "is_delayed" in df.columns
    assert set(df["is_delayed"].unique()).issubset({0, 1})
