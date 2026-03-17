"""Turnaround time analysis for aviation ground operations.

Calculates and analyzes aircraft ground time between consecutive flights
(same tail number at same airport). Key metric for LCCs like Ryanair
where the 25-minute turnaround is a competitive advantage.

Ground time = departure time of next flight - arrival time of previous flight
(for the same aircraft at the same airport).
"""
from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Industry benchmarks (minutes)
TURNAROUND_BENCHMARKS: dict[str, dict[str, int]] = {
    "LCC": {"target": 25, "warning": 35, "critical": 45},
    "FSC_narrowbody": {"target": 45, "warning": 60, "critical": 75},
    "FSC_widebody": {"target": 90, "warning": 120, "critical": 150},
    "regional": {"target": 30, "warning": 40, "critical": 55},
}

# Turnaround process breakdown (typical narrowbody, minutes)
TURNAROUND_PHASES: dict[str, dict[str, Any]] = {
    "deboarding": {"target_min": 5, "description": "Passenger deboarding"},
    "cabin_clean": {"target_min": 7, "description": "Cabin cleaning & prep"},
    "catering": {"target_min": 10, "description": "Catering load/unload"},
    "fueling": {"target_min": 12, "description": "Refueling"},
    "cargo": {"target_min": 10, "description": "Baggage/cargo unload + load"},
    "boarding": {"target_min": 15, "description": "Passenger boarding"},
    "pushback": {"target_min": 3, "description": "Pushback and engine start"},
}


def calculate_turnaround_times(flights_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate ground turnaround time for aircraft rotations.

    Pairs consecutive flights by the same tail number where the
    destination of flight N matches the origin of flight N+1.

    Parameters
    ----------
    flights_df : pd.DataFrame
        Must contain: tail_num, origin, dest, flight_date, dep_hour,
        arr_delay_minutes, crs_elapsed_time.

    Returns
    -------
    pd.DataFrame with turnaround records.
    """
    if flights_df is None or flights_df.empty:
        return pd.DataFrame()

    df = flights_df.copy()

    # Ensure required columns
    required = ["tail_num", "origin", "dest", "flight_date", "dep_hour"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        logger.warning("Missing columns for turnaround analysis: %s", missing)
        return pd.DataFrame()

    # Filter out cancelled flights and null tail numbers
    df = df[
        (df.get("cancelled", pd.Series(0)) == 0)
        & df["tail_num"].notna()
        & (df["tail_num"] != "")
    ].copy()

    if df.empty:
        return pd.DataFrame()

    # Sort by tail number and departure time
    df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")
    df = df.sort_values(["tail_num", "flight_date", "dep_hour"])

    # Calculate estimated arrival time (departure + elapsed)
    elapsed = pd.to_numeric(df.get("crs_elapsed_time", 0), errors="coerce").fillna(150)
    delay = pd.to_numeric(df.get("arr_delay_minutes", 0), errors="coerce").fillna(0)

    df["est_arrival_minutes"] = df["dep_hour"] * 60 + elapsed + delay
    df["dep_minutes"] = df["dep_hour"] * 60

    turnarounds = []
    grouped = df.groupby("tail_num")

    for tail, group in grouped:
        group = group.reset_index(drop=True)
        for i in range(len(group) - 1):
            inbound = group.iloc[i]
            outbound = group.iloc[i + 1]

            # Only valid if inbound destination == outbound origin (same day)
            if (
                inbound["dest"] == outbound["origin"]
                and inbound["flight_date"] == outbound["flight_date"]
            ):
                arr_min = inbound["est_arrival_minutes"]
                dep_min = outbound["dep_minutes"]
                ground_time = dep_min - arr_min

                # Sanity check: ground time between 10 and 300 minutes
                if 10 <= ground_time <= 300:
                    turnarounds.append({
                        "tail_num": tail,
                        "airport": inbound["dest"],
                        "flight_date": inbound["flight_date"],
                        "inbound_flight": f"{inbound.get('airline', '')}{inbound.get('flight_num', '')}",
                        "outbound_flight": f"{outbound.get('airline', '')}{outbound.get('flight_num', '')}",
                        "inbound_origin": inbound["origin"],
                        "outbound_dest": outbound["dest"],
                        "ground_time_min": round(ground_time),
                        "inbound_delay": round(float(inbound.get("arr_delay_minutes", 0))),
                        "airline": inbound.get("airline", ""),
                    })

    if not turnarounds:
        return pd.DataFrame()

    result = pd.DataFrame(turnarounds)

    # Classify turnaround performance
    result["status"] = result["ground_time_min"].apply(_classify_turnaround)

    return result


def _classify_turnaround(ground_time: float) -> str:
    """Classify turnaround time performance."""
    if ground_time <= 25:
        return "excellent"
    elif ground_time <= 35:
        return "on_target"
    elif ground_time <= 50:
        return "acceptable"
    elif ground_time <= 75:
        return "warning"
    else:
        return "critical"


def compute_turnaround_kpis(turnaround_df: pd.DataFrame) -> dict[str, Any]:
    """Compute key turnaround performance indicators.

    Returns
    -------
    dict with KPIs: avg_ground_time, median_ground_time, pct_under_target,
        pct_critical, by_airport, by_airline, efficiency_score.
    """
    if turnaround_df is None or turnaround_df.empty:
        return {
            "total_turnarounds": 0,
            "avg_ground_time": 0,
            "median_ground_time": 0,
            "pct_under_30min": 0,
            "pct_critical": 0,
            "efficiency_score": 0,
            "by_airport": [],
            "by_airline": [],
        }

    df = turnaround_df.copy()
    gt = df["ground_time_min"]

    # By airport
    airport_stats = (
        df.groupby("airport")["ground_time_min"]
        .agg(["mean", "median", "count", "std"])
        .sort_values("count", ascending=False)
        .head(15)
    )
    by_airport = [
        {
            "airport": apt,
            "avg_min": round(row["mean"], 1),
            "median_min": round(row["median"], 1),
            "count": int(row["count"]),
            "std_min": round(row["std"], 1) if not np.isnan(row["std"]) else 0,
        }
        for apt, row in airport_stats.iterrows()
    ]

    # By airline
    airline_stats = (
        df.groupby("airline")["ground_time_min"]
        .agg(["mean", "median", "count"])
        .sort_values("mean")
    )
    by_airline = [
        {
            "airline": al,
            "avg_min": round(row["mean"], 1),
            "median_min": round(row["median"], 1),
            "count": int(row["count"]),
        }
        for al, row in airline_stats.iterrows()
    ]

    # Efficiency score: weighted by how close to 30-min target
    scores = np.clip(1 - (gt - 30) / 60, 0, 1)
    efficiency = round(float(scores.mean()) * 100, 1)

    return {
        "total_turnarounds": len(df),
        "avg_ground_time": round(float(gt.mean()), 1),
        "median_ground_time": round(float(gt.median()), 1),
        "min_ground_time": round(float(gt.min()), 1),
        "max_ground_time": round(float(gt.max()), 1),
        "pct_under_30min": round(float((gt <= 30).mean()) * 100, 1),
        "pct_under_45min": round(float((gt <= 45).mean()) * 100, 1),
        "pct_critical": round(float((gt > 75).mean()) * 100, 1),
        "efficiency_score": efficiency,
        "by_airport": by_airport,
        "by_airline": by_airline,
    }
