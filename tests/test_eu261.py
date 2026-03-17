"""Tests for EU261 compensation calculator."""
import pandas as pd
import numpy as np
import pytest

from aerops.analytics.eu261 import (
    calculate_eu261_compensation,
    calculate_operational_cost,
    calculate_fleet_eu261_exposure,
)


def test_short_delay_not_eligible():
    """Delays under 3 hours should not trigger EU261."""
    result = calculate_eu261_compensation(
        distance_miles=500, delay_minutes=120, pax_count=180
    )
    assert result["eligible"] is False
    assert result["total_compensation_eur"] == 0


def test_short_haul_3h_delay():
    """Short haul (<=1500km) with 3h+ delay = EUR 250/pax."""
    result = calculate_eu261_compensation(
        distance_miles=500, delay_minutes=200, pax_count=180
    )
    assert result["eligible"] is True
    assert result["tier_eur"] == 250
    assert result["total_compensation_eur"] == 250 * 180


def test_medium_haul_3h_delay():
    """Medium haul (1500-3500km) with 3h+ delay = EUR 400/pax."""
    result = calculate_eu261_compensation(
        distance_miles=1500, delay_minutes=200, pax_count=160
    )
    assert result["eligible"] is True
    assert result["tier_eur"] == 400
    assert result["total_compensation_eur"] == 400 * 160


def test_long_haul_under_4h():
    """Long haul (>3500km) requires 4h+ delay for EUR 600."""
    result = calculate_eu261_compensation(
        distance_miles=4000, delay_minutes=200, pax_count=300
    )
    # 200 min = 3.33h, under 4h threshold for long haul
    assert result["eligible"] is False


def test_long_haul_over_4h():
    """Long haul (>3500km) with 4h+ delay = EUR 600/pax."""
    result = calculate_eu261_compensation(
        distance_miles=4000, delay_minutes=260, pax_count=300
    )
    assert result["eligible"] is True
    assert result["tier_eur"] == 600
    assert result["total_compensation_eur"] == 600 * 300


def test_operational_cost_positive():
    """Operational costs should be positive for any delay."""
    costs = calculate_operational_cost(delay_minutes=60)
    assert costs["total"] > 0
    assert costs["fuel_burn"] > 0
    assert costs["crew_overtime"] > 0


def test_fleet_exposure_empty_df():
    """Empty DataFrame should return zeros."""
    result = calculate_fleet_eu261_exposure(pd.DataFrame())
    assert result["total_exposure_eur"] == 0
    assert result["affected_flights"] == 0


def test_fleet_exposure_with_data(sample_flights_df):
    """Fleet exposure should calculate for a DataFrame with delays."""
    # Ensure some flights have large delays
    df = sample_flights_df.copy()
    df["arr_delay_minutes"] = np.where(
        np.random.random(len(df)) > 0.8,
        np.random.randint(180, 300, len(df)),
        df["arr_delay_minutes"],
    )
    result = calculate_fleet_eu261_exposure(df, pax_per_flight=160)
    assert result["total_flights"] == len(df)
    assert result["total_exposure_eur"] >= 0
