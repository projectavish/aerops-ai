"""Parse and load BTS On-Time Performance data into SQLite."""
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from aerops.config import BTS_DELAY_COLUMNS, DB_PATH
from aerops.data.iata_codes import map_bts_cause_to_iata
from aerops.db import get_connection, init_db

logger = logging.getLogger(__name__)

# Columns we need from the BTS download
BTS_COLUMNS = [
    "FlightDate", "Reporting_Airline", "Flight_Number_Reporting_Airline",
    "Tail_Number", "Origin", "Dest",
    "CRSDepTime", "DepTime", "DepDelay", "DepDelayMinutes", "DepDel15",
    "CRSArrTime", "ArrTime", "ArrDelay", "ArrDelayMinutes", "ArrDel15",
    "Cancelled", "CancellationCode", "Diverted",
    "CRSElapsedTime", "ActualElapsedTime", "AirTime", "Distance",
    "CarrierDelay", "WeatherDelay", "NASDelay", "SecurityDelay",
    "LateAircraftDelay",
]

# Map BTS column names to our DB schema
COLUMN_RENAME = {
    "FlightDate": "flight_date",
    "Reporting_Airline": "airline",
    "Flight_Number_Reporting_Airline": "flight_num",
    "Tail_Number": "tail_num",
    "Origin": "origin",
    "Dest": "dest",
    "CRSDepTime": "crs_dep_time",
    "DepTime": "dep_time",
    "DepDelay": "dep_delay",
    "DepDelayMinutes": "dep_delay_minutes",
    "DepDel15": "dep_del15",
    "CRSArrTime": "crs_arr_time",
    "ArrTime": "arr_time",
    "ArrDelay": "arr_delay",
    "ArrDelayMinutes": "arr_delay_minutes",
    "ArrDel15": "arr_del15",
    "Cancelled": "cancelled",
    "CancellationCode": "cancellation_code",
    "Diverted": "diverted",
    "CRSElapsedTime": "crs_elapsed_time",
    "ActualElapsedTime": "actual_elapsed_time",
    "AirTime": "air_time",
    "Distance": "distance",
    "CarrierDelay": "carrier_delay",
    "WeatherDelay": "weather_delay",
    "NASDelay": "nas_delay",
    "SecurityDelay": "security_delay",
    "LateAircraftDelay": "late_aircraft_delay",
}


def parse_bts_csv(csv_path: str) -> pd.DataFrame:
    """Read a BTS On-Time Performance CSV and select needed columns.

    BTS CSVs may have varying column names. We try the standard names first,
    then fall back to reading all columns.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"BTS CSV not found: {csv_path}")

    df = pd.read_csv(csv_path, low_memory=False)

    # BTS sometimes adds trailing commas creating an unnamed column
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]

    # Select only columns we need (that exist)
    available = [c for c in BTS_COLUMNS if c in df.columns]
    missing = [c for c in BTS_COLUMNS if c not in df.columns]
    if missing:
        logger.warning("Missing BTS columns: %s", missing)

    df = df[available].copy()
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived columns for analytics and ML."""
    # Rename to our schema
    rename_map = {k: v for k, v in COLUMN_RENAME.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    # Route
    df["route"] = df["origin"] + "-" + df["dest"]

    # Parse date
    df["flight_date"] = pd.to_datetime(df["flight_date"], errors="coerce")

    # Temporal features
    df["dep_hour"] = pd.to_numeric(df["crs_dep_time"], errors="coerce")
    df["dep_hour"] = (df["dep_hour"] // 100).clip(0, 23).fillna(12).astype(int)
    df["day_of_week"] = df["flight_date"].dt.dayofweek  # 0=Mon
    df["month"] = df["flight_date"].dt.month
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

    # Delay flag (BTS standard: >15 min arrival delay)
    df["arr_delay_minutes"] = pd.to_numeric(
        df.get("arr_delay_minutes", pd.Series(dtype=float)), errors="coerce"
    ).fillna(0)
    df["is_delayed"] = (df["arr_delay_minutes"] > 15).astype(int)

    # Fill delay cause columns with 0
    for col in ["carrier_delay", "weather_delay", "nas_delay",
                 "security_delay", "late_aircraft_delay"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Primary delay cause (highest contributing factor)
    delay_cols = ["carrier_delay", "weather_delay", "nas_delay",
                  "security_delay", "late_aircraft_delay"]
    existing_delay_cols = [c for c in delay_cols if c in df.columns]

    if existing_delay_cols:
        bts_names = {
            "carrier_delay": "CarrierDelay",
            "weather_delay": "WeatherDelay",
            "nas_delay": "NASDelay",
            "security_delay": "SecurityDelay",
            "late_aircraft_delay": "LateAircraftDelay",
        }
        delay_vals = df[existing_delay_cols]
        max_col = delay_vals.idxmax(axis=1)
        max_val = delay_vals.max(axis=1)
        # Only assign cause when there's an actual delay > 0
        df["primary_delay_cause"] = np.where(
            max_val > 0,
            max_col.map(bts_names),
            None,
        )
    else:
        df["primary_delay_cause"] = None

    return df


def map_to_iata(df: pd.DataFrame) -> pd.DataFrame:
    """Assign IATA delay codes based on primary delay cause."""
    codes = []
    categories = []
    for cause in df["primary_delay_cause"]:
        if pd.isna(cause) or cause is None:
            codes.append(None)
            categories.append(None)
        else:
            code, cat = map_bts_cause_to_iata(cause)
            codes.append(code)
            categories.append(cat)

    df["iata_delay_code"] = codes
    df["iata_delay_category"] = categories
    return df


def load_to_db(df: pd.DataFrame, db_path: str = DB_PATH,
               chunk_size: int = 10_000) -> int:
    """Insert processed flights into SQLite."""
    init_db(db_path)
    conn = get_connection(db_path)

    # Convert date to string for SQLite
    if "flight_date" in df.columns:
        df["flight_date"] = df["flight_date"].dt.strftime("%Y-%m-%d")

    # Only keep columns that match our schema
    schema_cols = [
        "flight_date", "airline", "flight_num", "tail_num", "origin", "dest",
        "route", "crs_dep_time", "dep_time", "dep_delay", "dep_delay_minutes",
        "dep_del15", "crs_arr_time", "arr_time", "arr_delay",
        "arr_delay_minutes", "arr_del15", "is_delayed", "cancelled",
        "cancellation_code", "diverted", "crs_elapsed_time",
        "actual_elapsed_time", "air_time", "distance", "carrier_delay",
        "weather_delay", "nas_delay", "security_delay", "late_aircraft_delay",
        "primary_delay_cause", "iata_delay_code", "iata_delay_category",
        "dep_hour", "day_of_week", "month", "is_weekend",
    ]
    keep_cols = [c for c in schema_cols if c in df.columns]
    df = df[keep_cols]

    total = 0
    for start in range(0, len(df), chunk_size):
        chunk = df.iloc[start:start + chunk_size]
        chunk.to_sql("flights", conn, if_exists="append", index=False)
        total += len(chunk)
        logger.info("Loaded %d / %d rows", total, len(df))

    conn.close()
    return total


def ingest_bts_file(csv_path: str, db_path: str = DB_PATH) -> int:
    """Full pipeline: parse → engineer → map → load."""
    logger.info("Parsing %s ...", csv_path)
    df = parse_bts_csv(csv_path)
    logger.info("Loaded %d raw rows", len(df))

    df = engineer_features(df)
    df = map_to_iata(df)

    count = load_to_db(df, db_path)
    logger.info("Ingested %d flights into %s", count, db_path)
    return count
