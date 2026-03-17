"""Shared test fixtures."""
import os

import pytest
import pandas as pd
import numpy as np

# Ensure project root on path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def tmp_db(tmp_path):
    """Create a temporary SQLite database path."""
    db_path = str(tmp_path / "test.db")
    from aerops.db import init_db
    init_db(db_path)
    return db_path


@pytest.fixture
def sample_bts_df():
    """Create a sample BTS-format DataFrame for testing."""
    rng = np.random.default_rng(99)
    n = 100
    return pd.DataFrame({
        "FlightDate": pd.date_range("2025-10-01", periods=n, freq="h"),
        "Reporting_Airline": rng.choice(["AA", "DL", "UA"], n),
        "Flight_Number_Reporting_Airline": [str(i) for i in range(n)],
        "Tail_Number": [f"N{i:03d}AA" for i in range(n)],
        "Origin": rng.choice(["JFK", "LAX", "ORD", "ATL"], n),
        "Dest": rng.choice(["LAX", "JFK", "DFW", "MIA"], n),
        "CRSDepTime": rng.choice(["0800", "1200", "1600", "2000"], n),
        "DepTime": rng.choice(["0800", "1200", "1600", "2000"], n),
        "DepDelay": rng.normal(5, 20, n).round(),
        "DepDelayMinutes": np.maximum(rng.normal(5, 20, n), 0).round(),
        "DepDel15": (rng.random(n) > 0.8).astype(int),
        "CRSArrTime": rng.choice(["1100", "1500", "1900", "2300"], n),
        "ArrTime": rng.choice(["1100", "1500", "1900", "2300"], n),
        "ArrDelay": rng.normal(5, 25, n).round(),
        "ArrDelayMinutes": np.maximum(rng.normal(10, 25, n), 0).round(),
        "ArrDel15": (rng.random(n) > 0.8).astype(int),
        "Cancelled": np.zeros(n, dtype=int),
        "CancellationCode": [None] * n,
        "Diverted": np.zeros(n, dtype=int),
        "CRSElapsedTime": rng.integers(90, 300, n).astype(float),
        "ActualElapsedTime": rng.integers(90, 300, n).astype(float),
        "AirTime": rng.integers(60, 270, n).astype(float),
        "Distance": rng.integers(300, 2500, n).astype(float),
        "CarrierDelay": np.where(rng.random(n) > 0.7, rng.integers(5, 60, n), 0).astype(float),
        "WeatherDelay": np.where(rng.random(n) > 0.85, rng.integers(10, 90, n), 0).astype(float),
        "NASDelay": np.where(rng.random(n) > 0.8, rng.integers(5, 45, n), 0).astype(float),
        "SecurityDelay": np.zeros(n),
        "LateAircraftDelay": np.where(rng.random(n) > 0.75, rng.integers(10, 80, n), 0).astype(float),
    })


@pytest.fixture
def sample_flights_df():
    """Create a sample flights DataFrame matching our DB schema."""
    rng = np.random.default_rng(42)
    n = 200
    origins = rng.choice(["JFK", "LAX", "ORD", "ATL", "DFW"], n)
    dests = rng.choice(["LAX", "JFK", "MIA", "SFO", "DEN"], n)
    return pd.DataFrame({
        "flight_date": pd.date_range("2025-10-01", periods=n, freq="3h"),
        "airline": rng.choice(["AA", "DL", "UA", "WN"], n),
        "origin": origins,
        "dest": dests,
        "route": [f"{o}-{d}" for o, d in zip(origins, dests)],
        "arr_delay_minutes": np.maximum(rng.normal(10, 30, n), 0).round(),
        "is_delayed": (rng.random(n) > 0.8).astype(int),
        "cancelled": np.zeros(n, dtype=int),
        "diverted": np.zeros(n, dtype=int),
        "dep_hour": rng.integers(0, 24, n),
        "day_of_week": rng.integers(0, 7, n),
        "month": rng.integers(1, 13, n),
        "distance": rng.integers(300, 2500, n).astype(float),
        "iata_delay_category": rng.choice(["Weather", "Reactionary", "ATC/Airport", None], n),
    })
