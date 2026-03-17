"""EU261/2004 passenger compensation calculator.

Implements the EU regulation on air passenger rights for flight delays
and cancellations. Updated to reflect EU2027 proposed revisions.

Compensation thresholds (Regulation EC 261/2004):
    - Flights <= 1500 km:  EUR 250
    - Intra-EU > 1500 km:  EUR 400
    - All other > 1500 km:  EUR 400
    - Flights > 3500 km:    EUR 600

Compensation is triggered when arrival delay exceeds:
    - 3 hours for short/medium haul
    - 4 hours for long haul (>3500 km)
"""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

# EU261 compensation tiers (EUR)
COMPENSATION_TIERS: list[dict[str, Any]] = [
    {"max_distance_km": 1500, "min_delay_hours": 3, "amount_eur": 250},
    {"max_distance_km": 3500, "min_delay_hours": 3, "amount_eur": 400},
    {"max_distance_km": float("inf"), "min_delay_hours": 4, "amount_eur": 600},
]

# Average costs per delay minute (industry estimates, EUR)
COST_PER_MINUTE: dict[str, float] = {
    "fuel_burn": 45.0,        # Extra fuel for holding/taxi
    "crew_overtime": 25.0,     # Crew cost per minute overage
    "airport_fees": 12.0,      # Extended gate/apron charges
    "maintenance": 8.0,        # Increased wear from delays
    "passenger_care": 15.0,    # Meals, hotel, rebooking
}

# Miles to km conversion
MILES_TO_KM = 1.60934


def calculate_eu261_compensation(
    distance_miles: float,
    delay_minutes: float,
    pax_count: int = 180,
) -> dict[str, Any]:
    """Calculate EU261 compensation liability for a single flight.

    Parameters
    ----------
    distance_miles : float
        Great-circle route distance in statute miles.
    delay_minutes : float
        Arrival delay in minutes.
    pax_count : int
        Number of passengers on the flight (default: 180 for narrowbody).

    Returns
    -------
    dict with keys: eligible, tier_eur, total_compensation_eur,
        per_pax_eur, delay_hours, distance_km, explanation
    """
    distance_km = distance_miles * MILES_TO_KM
    delay_hours = delay_minutes / 60.0

    result: dict[str, Any] = {
        "eligible": False,
        "tier_eur": 0,
        "total_compensation_eur": 0,
        "per_pax_eur": 0,
        "delay_hours": round(delay_hours, 1),
        "distance_km": round(distance_km, 0),
        "pax_count": pax_count,
        "explanation": "",
    }

    if delay_minutes < 180:  # Less than 3 hours
        result["explanation"] = (
            f"Delay of {delay_hours:.1f}h is below the 3-hour EU261 threshold."
        )
        return result

    # Find applicable tier
    for tier in COMPENSATION_TIERS:
        if distance_km <= tier["max_distance_km"]:
            if delay_hours >= tier["min_delay_hours"]:
                result["eligible"] = True
                result["tier_eur"] = tier["amount_eur"]
                result["per_pax_eur"] = tier["amount_eur"]
                result["total_compensation_eur"] = tier["amount_eur"] * pax_count
                result["explanation"] = (
                    f"Route distance {distance_km:,.0f} km, delay {delay_hours:.1f}h "
                    f"triggers EU261 compensation of EUR {tier['amount_eur']} per passenger "
                    f"({pax_count} pax = EUR {tier['amount_eur'] * pax_count:,.0f} total)."
                )
            else:
                result["explanation"] = (
                    f"Delay of {delay_hours:.1f}h is below the "
                    f"{tier['min_delay_hours']}h threshold for routes > 3500 km."
                )
            break

    return result


def calculate_operational_cost(
    delay_minutes: float,
    aircraft_type: str = "narrowbody",
) -> dict[str, float]:
    """Estimate total operational cost of a delay.

    Parameters
    ----------
    delay_minutes : float
        Delay duration in minutes.
    aircraft_type : str
        'narrowbody' (A320/B737) or 'widebody' (A330/B777).

    Returns
    -------
    dict with cost breakdown and total.
    """
    multiplier = 1.0 if aircraft_type == "narrowbody" else 1.8

    costs: dict[str, float] = {}
    for category, rate in COST_PER_MINUTE.items():
        costs[category] = round(delay_minutes * rate * multiplier, 2)

    costs["total"] = round(sum(costs.values()), 2)
    return costs


def calculate_fleet_eu261_exposure(
    flights_df: pd.DataFrame,
    pax_per_flight: int = 160,
) -> dict[str, Any]:
    """Calculate total EU261 exposure for a fleet of flights.

    Parameters
    ----------
    flights_df : pd.DataFrame
        Must contain 'arr_delay_minutes' and 'distance' columns.
    pax_per_flight : int
        Average passengers per flight.

    Returns
    -------
    dict with total exposure, affected flights, cost breakdown by tier.
    """
    if flights_df is None or flights_df.empty:
        return {
            "total_exposure_eur": 0,
            "affected_flights": 0,
            "total_flights": 0,
            "exposure_per_flight_eur": 0,
            "tier_breakdown": {},
            "top_routes": [],
        }

    df = flights_df.copy()
    df["arr_delay_minutes"] = pd.to_numeric(
        df.get("arr_delay_minutes", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0)
    df["distance"] = pd.to_numeric(
        df.get("distance", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0)

    # Calculate per-flight EU261 liability
    compensations = []
    for _, row in df.iterrows():
        comp = calculate_eu261_compensation(
            distance_miles=row["distance"],
            delay_minutes=row["arr_delay_minutes"],
            pax_count=pax_per_flight,
        )
        compensations.append(comp)

    comp_df = pd.DataFrame(compensations)
    affected = comp_df[comp_df["eligible"]]

    # Tier breakdown
    tier_breakdown = {}
    if not affected.empty:
        for tier_val in [250, 400, 600]:
            tier_flights = affected[affected["tier_eur"] == tier_val]
            if len(tier_flights) > 0:
                tier_breakdown[f"EUR {tier_val}"] = {
                    "flights": len(tier_flights),
                    "total_eur": int(tier_flights["total_compensation_eur"].sum()),
                }

    # Top routes by exposure
    df["eu261_exposure"] = comp_df["total_compensation_eur"]
    top_routes = []
    if "route" in df.columns and df["eu261_exposure"].sum() > 0:
        route_exposure = (
            df.groupby("route")["eu261_exposure"]
            .agg(["sum", "count", "mean"])
            .sort_values("sum", ascending=False)
            .head(10)
        )
        for route, row in route_exposure.iterrows():
            top_routes.append({
                "route": route,
                "total_eur": int(row["sum"]),
                "flights": int(row["count"]),
                "avg_eur": int(row["mean"]),
            })

    total_exposure = int(comp_df["total_compensation_eur"].sum())
    return {
        "total_exposure_eur": total_exposure,
        "affected_flights": len(affected),
        "total_flights": len(df),
        "exposure_rate": round(len(affected) / len(df) * 100, 1) if len(df) > 0 else 0,
        "exposure_per_flight_eur": round(total_exposure / len(df), 0) if len(df) > 0 else 0,
        "tier_breakdown": tier_breakdown,
        "top_routes": top_routes,
    }
