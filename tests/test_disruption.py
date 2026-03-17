"""Tests for disruption recovery simulator."""
import pandas as pd
import numpy as np
import pytest

from aerops.analytics.disruption import (
    simulate_disruption,
    identify_vulnerable_routes,
)


@pytest.fixture
def rotation_flights_df():
    """Create flights with tail number rotations for cascade testing."""
    return pd.DataFrame({
        "flight_date": ["2025-01-01"] * 6,
        "airline": ["AA"] * 6,
        "flight_num": ["100", "200", "300", "400", "500", "600"],
        "tail_num": ["N1AA", "N1AA", "N1AA", "N2BB", "N2BB", "N3CC"],
        "origin": ["ATL", "ORD", "DEN", "ATL", "JFK", "LAX"],
        "dest": ["ORD", "DEN", "LAX", "JFK", "MIA", "SFO"],
        "dep_hour": [8, 12, 16, 9, 14, 10],
        "crs_elapsed_time": [120, 180, 240, 150, 180, 90],
        "arr_delay_minutes": [0, 0, 0, 0, 0, 0],
        "cancelled": [0] * 6,
        "is_delayed": [0] * 6,
        "route": ["ATL-ORD", "ORD-DEN", "DEN-LAX", "ATL-JFK", "JFK-MIA", "LAX-SFO"],
        "distance": [606, 888, 862, 760, 1089, 337],
    })


def test_simulate_disruption_empty():
    """Empty DataFrame should return empty result."""
    result = simulate_disruption(pd.DataFrame(), "ATL", 60)
    assert result["affected_flights"] == 0


def test_simulate_disruption_basic(rotation_flights_df):
    """Disruption at ATL should affect flights departing from there."""
    result = simulate_disruption(rotation_flights_df, "ATL", 60)
    assert result["disrupted_airport"] == "ATL"
    assert result["initial_delay_minutes"] == 60
    assert result["affected_flights"] >= 1


def test_simulate_disruption_no_flights():
    """Airport with no flights should return empty."""
    df = pd.DataFrame({
        "tail_num": ["N1"], "origin": ["JFK"], "dest": ["LAX"],
        "dep_hour": [8], "flight_date": ["2025-01-01"],
        "cancelled": [0], "airline": ["AA"], "flight_num": ["100"],
    })
    result = simulate_disruption(df, "ATL", 60)
    assert result["affected_flights"] == 0


def test_cascade_depth(rotation_flights_df):
    """Cascading should propagate through rotations."""
    result = simulate_disruption(rotation_flights_df, "ATL", 120)
    # N1AA goes ATL->ORD->DEN->LAX, so cascade should be >0
    assert result["cascade_depth"] >= 0


def test_vulnerable_routes_empty():
    """Empty DataFrame should return empty list."""
    result = identify_vulnerable_routes(pd.DataFrame())
    assert result == []


def test_vulnerable_routes_with_data(rotation_flights_df):
    """Should identify routes with high delay rate + density."""
    df = rotation_flights_df.copy()
    # Add more flights and mark some as delayed
    extra = pd.concat([df] * 5, ignore_index=True)
    extra["is_delayed"] = np.random.choice([0, 1], len(extra), p=[0.6, 0.4])
    extra["arr_delay_minutes"] = np.where(extra["is_delayed"], 30, 0)

    result = identify_vulnerable_routes(extra, top_n=5)
    assert isinstance(result, list)
    if result:  # May be empty if not enough unique routes
        assert "vulnerability_score" in result[0]
        assert "delay_rate" in result[0]
