"""Generate realistic demo data matching BTS schema with real IATA codes.

Used when no BTS data is available so the dashboard works out of the box.
"""
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from aerops.config import DB_PATH, DEMO_FLIGHT_COUNT
from aerops.data.iata_codes import BTS_TO_IATA
from aerops.db import get_connection, init_db, table_row_count

logger = logging.getLogger(__name__)

# Realistic US airline codes
AIRLINES = ["AA", "DL", "UA", "WN", "B6", "AS", "NK", "F9", "HA", "G4"]

# Top 30 US airports by traffic
AIRPORTS = [
    "ATL", "DFW", "DEN", "ORD", "LAX", "CLT", "MCO", "LAS", "PHX", "MIA",
    "SEA", "SFO", "EWR", "JFK", "BOS", "MSP", "DTW", "FLL", "IAH", "DCA",
    "SLC", "SAN", "BWI", "TPA", "PDX", "STL", "HNL", "AUS", "BNA", "RDU",
]

# Realistic route distances (miles) for common pairs
ROUTE_DISTANCES = {
    ("JFK", "LAX"): 2475, ("ATL", "ORD"): 606, ("DFW", "DEN"): 641,
    ("LAX", "SFO"): 337, ("ORD", "DFW"): 802, ("MIA", "JFK"): 1089,
    ("SEA", "LAX"): 954, ("BOS", "DCA"): 399, ("DEN", "PHX"): 602,
    ("ATL", "MIA"): 594, ("ORD", "LAX"): 1745, ("DFW", "ATL"): 731,
    ("JFK", "SFO"): 2586, ("LAX", "DEN"): 862, ("SEA", "SFO"): 679,
}

# BTS delay cause probabilities (based on real BTS averages)
DELAY_CAUSE_PROBS = {
    "CarrierDelay": 0.30,
    "LateAircraftDelay": 0.35,
    "NASDelay": 0.20,
    "WeatherDelay": 0.10,
    "SecurityDelay": 0.05,
}


def _estimate_distance(origin: str, dest: str) -> float:
    """Estimate distance for a route pair."""
    key = (origin, dest)
    rev_key = (dest, origin)
    if key in ROUTE_DISTANCES:
        return ROUTE_DISTANCES[key]
    if rev_key in ROUTE_DISTANCES:
        return ROUTE_DISTANCES[rev_key]
    return np.random.randint(300, 2500)


def generate_demo_data(db_path: str = DB_PATH,
                       num_flights: int = DEMO_FLIGHT_COUNT) -> int:
    """Generate demo flights using BTS schema with real IATA delay codes."""
    init_db(db_path)

    # Check if data already exists
    try:
        count = table_row_count(db_path, "flights")
        if count > 0:
            logger.info("Database already has %d flights, skipping demo gen", count)
            return count
    except Exception:
        pass

    logger.info("Generating %d demo flights ...", num_flights)
    rng = np.random.default_rng(42)

    # Generate dates over last 90 days
    end_date = datetime.now()
    dates = [end_date - timedelta(hours=int(h))
             for h in rng.integers(0, 90 * 24, num_flights)]

    # Generate origin-dest pairs (avoid same airport)
    origins = rng.choice(AIRPORTS, num_flights)
    dests = []
    for o in origins:
        d = rng.choice([a for a in AIRPORTS if a != o])
        dests.append(d)

    # Scheduled departure times (realistic distribution: peaks at 7-9am, 4-7pm)
    hour_weights = np.array([
        0.02, 0.01, 0.01, 0.01, 0.02, 0.04, 0.08, 0.10, 0.09, 0.08,
        0.07, 0.06, 0.06, 0.06, 0.06, 0.06, 0.05, 0.04, 0.03, 0.02,
        0.01, 0.01, 0.005, 0.005
    ])
    hour_weights /= hour_weights.sum()
    dep_hours = rng.choice(24, num_flights, p=hour_weights)
    dep_minutes = rng.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55],
                             num_flights)
    crs_dep_times = [f"{h:02d}{m:02d}" for h, m in zip(dep_hours, dep_minutes)]

    # Distances
    distances = [_estimate_distance(o, d) for o, d in zip(origins, dests)]

    # Elapsed time based on distance (~500mph average + 30min taxi)
    crs_elapsed = [round(dist / 500 * 60 + 30) for dist in distances]

    # Delay generation: ~20% delayed (BTS average)
    is_delayed = rng.random(num_flights) < 0.20
    cancelled = rng.random(num_flights) < 0.015

    # Generate delay minutes (log-normal distribution for delayed flights)
    arr_delay_minutes = np.zeros(num_flights)
    delay_mask = is_delayed & ~cancelled
    n_delayed = delay_mask.sum()
    arr_delay_minutes[delay_mask] = np.clip(
        rng.lognormal(mean=3.2, sigma=0.8, size=n_delayed), 16, 300
    ).round()

    # Small negative delays for on-time flights (arrived early)
    on_time_mask = ~is_delayed & ~cancelled
    arr_delay_minutes[on_time_mask] = rng.integers(-15, 15, on_time_mask.sum())

    # Assign delay causes to delayed flights
    causes = list(DELAY_CAUSE_PROBS.keys())
    cause_probs = list(DELAY_CAUSE_PROBS.values())

    carrier_delay = np.zeros(num_flights)
    weather_delay = np.zeros(num_flights)
    nas_delay = np.zeros(num_flights)
    security_delay = np.zeros(num_flights)
    late_aircraft_delay = np.zeros(num_flights)
    primary_delay_cause = [None] * num_flights
    iata_delay_code = [None] * num_flights
    iata_delay_category = [None] * num_flights

    for i in range(num_flights):
        if delay_mask[i]:
            cause = rng.choice(causes, p=cause_probs)
            minutes = arr_delay_minutes[i]
            primary_delay_cause[i] = cause
            mapping = BTS_TO_IATA[cause]
            iata_delay_code[i] = mapping["iata_code"]
            iata_delay_category[i] = mapping["iata_category"]

            if cause == "CarrierDelay":
                carrier_delay[i] = minutes
            elif cause == "WeatherDelay":
                weather_delay[i] = minutes
            elif cause == "NASDelay":
                nas_delay[i] = minutes
            elif cause == "SecurityDelay":
                security_delay[i] = minutes
            elif cause == "LateAircraftDelay":
                late_aircraft_delay[i] = minutes

    # Cancellation codes
    cancellation_codes = [None] * num_flights
    cancel_code_choices = ["A", "B", "C", "D"]
    cancel_probs = [0.40, 0.35, 0.20, 0.05]
    for i in range(num_flights):
        if cancelled[i]:
            cancellation_codes[i] = rng.choice(cancel_code_choices, p=cancel_probs)
            arr_delay_minutes[i] = 0

    # Build DataFrame
    df = pd.DataFrame({
        "flight_date": [d.strftime("%Y-%m-%d") for d in dates],
        "airline": rng.choice(AIRLINES, num_flights),
        "flight_num": [str(rng.integers(100, 9999)) for _ in range(num_flights)],
        "tail_num": [f"N{rng.integers(100, 999)}{chr(65 + rng.integers(0, 26))}{chr(65 + rng.integers(0, 26))}"
                     for _ in range(num_flights)],
        "origin": origins,
        "dest": dests,
        "route": [f"{o}-{d}" for o, d in zip(origins, dests)],
        "crs_dep_time": crs_dep_times,
        "dep_time": crs_dep_times,  # Simplified
        "dep_delay": arr_delay_minutes * 0.8,  # Correlated
        "dep_delay_minutes": np.maximum(arr_delay_minutes * 0.8, 0),
        "dep_del15": (arr_delay_minutes * 0.8 > 15).astype(int),
        "crs_arr_time": crs_dep_times,  # Simplified
        "arr_time": crs_dep_times,
        "arr_delay": arr_delay_minutes,
        "arr_delay_minutes": np.maximum(arr_delay_minutes, 0),
        "arr_del15": (arr_delay_minutes > 15).astype(int),
        "is_delayed": is_delayed.astype(int),
        "cancelled": cancelled.astype(int),
        "cancellation_code": cancellation_codes,
        "diverted": (rng.random(num_flights) < 0.003).astype(int),
        "crs_elapsed_time": crs_elapsed,
        "actual_elapsed_time": [
            e + int(d) if not c else None
            for e, d, c in zip(crs_elapsed, arr_delay_minutes, cancelled)
        ],
        "air_time": [max(e - 30, 30) for e in crs_elapsed],
        "distance": distances,
        "carrier_delay": carrier_delay,
        "weather_delay": weather_delay,
        "nas_delay": nas_delay,
        "security_delay": security_delay,
        "late_aircraft_delay": late_aircraft_delay,
        "primary_delay_cause": primary_delay_cause,
        "iata_delay_code": iata_delay_code,
        "iata_delay_category": iata_delay_category,
        "dep_hour": dep_hours.astype(int),
        "day_of_week": [d.weekday() for d in dates],
        "month": [d.month for d in dates],
        "is_weekend": [1 if d.weekday() >= 5 else 0 for d in dates],
    })

    # Load into database
    conn = get_connection(db_path)
    df.to_sql("flights", conn, if_exists="append", index=False)
    conn.commit()
    conn.close()

    logger.info("Generated %d demo flights", len(df))
    return len(df)
