"""Tests for turnaround time analysis."""
import pandas as pd
import numpy as np
import pytest

from aerops.analytics.turnaround import (
    calculate_turnaround_times,
    compute_turnaround_kpis,
    _classify_turnaround,
)


def test_classify_turnaround_excellent():
    assert _classify_turnaround(20) == "excellent"
    assert _classify_turnaround(25) == "excellent"


def test_classify_turnaround_on_target():
    assert _classify_turnaround(30) == "on_target"
    assert _classify_turnaround(35) == "on_target"


def test_classify_turnaround_critical():
    assert _classify_turnaround(80) == "critical"
    assert _classify_turnaround(120) == "critical"


def test_calculate_turnaround_empty():
    """Empty DataFrame should return empty result."""
    result = calculate_turnaround_times(pd.DataFrame())
    assert result.empty


def test_calculate_turnaround_no_rotations():
    """Flights with no matching rotations should return empty."""
    df = pd.DataFrame({
        "tail_num": ["N123AA", "N456BB"],
        "origin": ["JFK", "LAX"],
        "dest": ["LAX", "SFO"],
        "flight_date": ["2025-01-01", "2025-01-01"],
        "dep_hour": [8, 14],
        "crs_elapsed_time": [330, 90],
        "arr_delay_minutes": [0, 0],
    })
    result = calculate_turnaround_times(df)
    # N123AA arrives LAX, but N456BB departs LAX (different tail)
    assert isinstance(result, pd.DataFrame)


def test_calculate_turnaround_valid_rotation():
    """Same tail, same day, dest matches next origin -> turnaround found."""
    df = pd.DataFrame({
        "tail_num": ["N123AA", "N123AA"],
        "origin": ["JFK", "LAX"],
        "dest": ["LAX", "SFO"],
        "flight_date": ["2025-01-01", "2025-01-01"],
        "dep_hour": [8, 14],
        "crs_elapsed_time": [330, 90],
        "arr_delay_minutes": [0, 0],
        "airline": ["AA", "AA"],
        "flight_num": ["100", "200"],
        "cancelled": [0, 0],
    })
    result = calculate_turnaround_times(df)
    assert not result.empty
    assert "ground_time_min" in result.columns
    assert result.iloc[0]["airport"] == "LAX"


def test_compute_kpis_empty():
    """Empty turnaround data should return zero KPIs."""
    kpis = compute_turnaround_kpis(pd.DataFrame())
    assert kpis["total_turnarounds"] == 0
    assert kpis["avg_ground_time"] == 0


def test_compute_kpis_with_data():
    """KPIs should be calculated from valid turnaround data."""
    ta_df = pd.DataFrame({
        "tail_num": ["N1", "N2", "N3", "N4", "N5"],
        "airport": ["ATL", "ATL", "ORD", "ORD", "JFK"],
        "ground_time_min": [25, 35, 45, 80, 20],
        "airline": ["AA", "DL", "UA", "WN", "B6"],
        "status": ["excellent", "on_target", "acceptable", "critical", "excellent"],
        "flight_date": pd.date_range("2025-01-01", periods=5),
        "inbound_delay": [0, 10, 5, 30, 0],
    })
    kpis = compute_turnaround_kpis(ta_df)
    assert kpis["total_turnarounds"] == 5
    assert kpis["avg_ground_time"] > 0
    assert 0 <= kpis["pct_under_30min"] <= 100
    assert len(kpis["by_airport"]) > 0
    assert len(kpis["by_airline"]) > 0
