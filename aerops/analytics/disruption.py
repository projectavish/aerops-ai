"""Disruption recovery and network propagation simulator.

Models how a delay at one airport cascades through the flight network
via aircraft rotations. Identifies downstream flights at risk and
estimates total network impact.

Key concepts:
    - Aircraft rotation: The sequence of flights operated by one aircraft
    - Delay propagation: A late arrival reduces ground time for the next
      departure, potentially causing a cascading delay
    - Recovery buffer: Scheduled ground time minus minimum turnaround time
    - Propagation factor: Fraction of delay absorbed vs. passed downstream
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Minimum turnaround time (minutes) - below this the next flight is delayed
MIN_TURNAROUND_MINUTES = 25

# Average delay absorption per rotation (industry estimate)
ABSORPTION_RATE = 0.30  # 30% of delay is recovered at each stop


def simulate_disruption(
    flights_df: pd.DataFrame,
    airport: str,
    initial_delay_minutes: int = 60,
    time_window_hours: int = 6,
) -> dict[str, Any]:
    """Simulate delay propagation from a disruption at a single airport.

    Parameters
    ----------
    flights_df : pd.DataFrame
        Flight data with tail_num, origin, dest, dep_hour, flight_date.
    airport : str
        IATA code of the disrupted airport.
    initial_delay_minutes : int
        Initial delay imposed on departures from the airport.
    time_window_hours : int
        Time window to analyze (hours from disruption start).

    Returns
    -------
    dict with simulation results: affected_flights, cascade_depth,
        total_delay_minutes, downstream_airports, timeline.
    """
    if flights_df is None or flights_df.empty:
        return _empty_result(airport, initial_delay_minutes)

    df = flights_df.copy()

    # Filter to non-cancelled flights with tail numbers
    df = df[
        (df.get("cancelled", pd.Series(0)) == 0)
        & df["tail_num"].notna()
        & (df["tail_num"] != "")
    ].copy()

    df["dep_hour"] = pd.to_numeric(df.get("dep_hour", 12), errors="coerce").fillna(12)

    # Find flights departing from the disrupted airport
    departures = df[df["origin"] == airport].copy()
    if departures.empty:
        return _empty_result(airport, initial_delay_minutes)

    # Track affected flights
    affected: list[dict[str, Any]] = []
    visited_tails: set[str] = set()
    total_propagated_delay = 0

    # Level 0: Direct impact - flights departing from disrupted airport
    for _, flight in departures.iterrows():
        tail = flight["tail_num"]
        if tail in visited_tails:
            continue
        visited_tails.add(tail)

        affected.append({
            "flight": f"{flight.get('airline', '')}{flight.get('flight_num', '')}",
            "tail_num": tail,
            "origin": airport,
            "dest": flight["dest"],
            "delay_minutes": initial_delay_minutes,
            "cascade_level": 0,
            "cause": "Direct disruption",
        })
        total_propagated_delay += initial_delay_minutes

        # Trace downstream rotations for this aircraft
        _trace_rotations(
            df, tail, flight["dest"], initial_delay_minutes,
            1, affected, total_propagated_delay, max_depth=4,
        )

    # Aggregate results
    downstream_airports = set()
    for a in affected:
        downstream_airports.add(a["dest"])
    downstream_airports.discard(airport)

    max_level = max((a["cascade_level"] for a in affected), default=0)
    total_delay = sum(a["delay_minutes"] for a in affected)

    # Group by cascade level for timeline
    timeline = {}
    for level in range(max_level + 1):
        level_flights = [a for a in affected if a["cascade_level"] == level]
        timeline[f"Level {level}"] = {
            "flights": len(level_flights),
            "total_delay_min": sum(f["delay_minutes"] for f in level_flights),
            "airports": list({f["dest"] for f in level_flights}),
        }

    return {
        "disrupted_airport": airport,
        "initial_delay_minutes": initial_delay_minutes,
        "affected_flights": len(affected),
        "cascade_depth": max_level,
        "total_network_delay_minutes": round(total_delay),
        "downstream_airports": sorted(downstream_airports),
        "downstream_airport_count": len(downstream_airports),
        "flights": affected[:50],  # Cap for display
        "timeline": timeline,
        "estimated_pax_affected": len(affected) * 160,  # Avg pax per flight
        "recovery_time_hours": round(max_level * 2.5, 1),
    }


def _trace_rotations(
    df: pd.DataFrame,
    tail: str,
    current_airport: str,
    remaining_delay: float,
    level: int,
    affected: list[dict],
    total_delay: float,
    max_depth: int = 4,
) -> None:
    """Recursively trace delay propagation through aircraft rotations."""
    if level > max_depth or remaining_delay < 5:
        return

    # Find next flight for this aircraft from current_airport
    next_flights = df[
        (df["tail_num"] == tail)
        & (df["origin"] == current_airport)
    ]

    if next_flights.empty:
        return

    # Take the next scheduled departure
    next_flight = next_flights.iloc[0]

    # Calculate propagated delay (absorb some at each stop)
    propagated = remaining_delay * (1 - ABSORPTION_RATE)

    if propagated >= 5:  # Only track meaningful delays
        affected.append({
            "flight": f"{next_flight.get('airline', '')}{next_flight.get('flight_num', '')}",
            "tail_num": tail,
            "origin": current_airport,
            "dest": next_flight["dest"],
            "delay_minutes": round(propagated),
            "cascade_level": level,
            "cause": f"Rotation cascade (Level {level})",
        })

        # Continue tracing
        _trace_rotations(
            df, tail, next_flight["dest"], propagated,
            level + 1, affected, total_delay + propagated, max_depth,
        )


def identify_vulnerable_routes(
    flights_df: pd.DataFrame,
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """Identify routes most vulnerable to delay cascades.

    Routes with high delay rates AND high rotation frequency are most
    susceptible to cascading disruptions.

    Parameters
    ----------
    flights_df : pd.DataFrame
        Flight data with route, is_delayed, tail_num columns.
    top_n : int
        Number of top vulnerable routes to return.

    Returns
    -------
    List of dicts with route, vulnerability_score, delay_rate,
        rotation_density, avg_delay_min.
    """
    if flights_df is None or flights_df.empty:
        return []

    df = flights_df.copy()
    required = ["route", "is_delayed"]
    if not all(c in df.columns for c in required):
        return []

    route_stats = df.groupby("route").agg(
        total_flights=("is_delayed", "count"),
        delayed_flights=("is_delayed", "sum"),
        avg_delay=("arr_delay_minutes", "mean"),
        unique_aircraft=("tail_num", "nunique"),
    )

    # Only consider routes with sufficient data
    route_stats = route_stats[route_stats["total_flights"] >= 5]

    if route_stats.empty:
        return []

    route_stats["delay_rate"] = route_stats["delayed_flights"] / route_stats["total_flights"]
    route_stats["rotation_density"] = route_stats["total_flights"] / route_stats["unique_aircraft"]

    # Vulnerability score: high delay rate + high rotation density = cascade risk
    route_stats["vulnerability_score"] = (
        route_stats["delay_rate"] * 0.6
        + (route_stats["rotation_density"] / route_stats["rotation_density"].max()) * 0.4
    )

    top = route_stats.sort_values("vulnerability_score", ascending=False).head(top_n)

    return [
        {
            "route": route,
            "vulnerability_score": round(row["vulnerability_score"], 3),
            "delay_rate": round(row["delay_rate"], 3),
            "rotation_density": round(row["rotation_density"], 1),
            "total_flights": int(row["total_flights"]),
            "avg_delay_min": round(row["avg_delay"], 1),
        }
        for route, row in top.iterrows()
    ]


def _empty_result(airport: str, initial_delay: int) -> dict[str, Any]:
    return {
        "disrupted_airport": airport,
        "initial_delay_minutes": initial_delay,
        "affected_flights": 0,
        "cascade_depth": 0,
        "total_network_delay_minutes": 0,
        "downstream_airports": [],
        "downstream_airport_count": 0,
        "flights": [],
        "timeline": {},
        "estimated_pax_affected": 0,
        "recovery_time_hours": 0,
    }
