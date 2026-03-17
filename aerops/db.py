"""SQLite database initialization and connection management."""
import sqlite3
from pathlib import Path

import pandas as pd


def get_connection(db_path: str) -> sqlite3.Connection:
    """Return a SQLite connection with WAL mode for better concurrency."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    """Create all tables and indexes if they don't exist."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.executescript("""
    -- Core flights table (populated from BTS data or demo generator)
    CREATE TABLE IF NOT EXISTS flights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        flight_date DATE NOT NULL,
        airline TEXT NOT NULL,
        flight_num TEXT,
        tail_num TEXT,
        origin TEXT NOT NULL,
        dest TEXT NOT NULL,
        route TEXT NOT NULL,
        crs_dep_time TEXT,
        dep_time TEXT,
        dep_delay REAL,
        dep_delay_minutes REAL DEFAULT 0,
        dep_del15 INTEGER DEFAULT 0,
        crs_arr_time TEXT,
        arr_time TEXT,
        arr_delay REAL,
        arr_delay_minutes REAL DEFAULT 0,
        arr_del15 INTEGER DEFAULT 0,
        is_delayed INTEGER DEFAULT 0,
        cancelled INTEGER DEFAULT 0,
        cancellation_code TEXT,
        diverted INTEGER DEFAULT 0,
        crs_elapsed_time REAL,
        actual_elapsed_time REAL,
        air_time REAL,
        distance REAL,
        carrier_delay REAL DEFAULT 0,
        weather_delay REAL DEFAULT 0,
        nas_delay REAL DEFAULT 0,
        security_delay REAL DEFAULT 0,
        late_aircraft_delay REAL DEFAULT 0,
        primary_delay_cause TEXT,
        iata_delay_code TEXT,
        iata_delay_category TEXT,
        dep_hour INTEGER,
        day_of_week INTEGER,
        month INTEGER,
        is_weekend INTEGER DEFAULT 0
    );

    CREATE INDEX IF NOT EXISTS idx_flights_date ON flights(flight_date);
    CREATE INDEX IF NOT EXISTS idx_flights_origin ON flights(origin);
    CREATE INDEX IF NOT EXISTS idx_flights_dest ON flights(dest);
    CREATE INDEX IF NOT EXISTS idx_flights_route ON flights(route);
    CREATE INDEX IF NOT EXISTS idx_flights_airline ON flights(airline);
    CREATE INDEX IF NOT EXISTS idx_flights_delayed ON flights(is_delayed);
    CREATE INDEX IF NOT EXISTS idx_flights_month ON flights(month);

    -- Airports reference table
    CREATE TABLE IF NOT EXISTS airports (
        iata_code TEXT PRIMARY KEY,
        icao_code TEXT,
        name TEXT NOT NULL,
        latitude REAL,
        longitude REAL,
        elevation_ft REAL,
        country TEXT,
        region TEXT
    );

    -- Weather observations cache
    CREATE TABLE IF NOT EXISTS weather_observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        icao_id TEXT NOT NULL,
        obs_time TEXT,
        temp REAL,
        dewp REAL,
        wind_dir INTEGER,
        wind_speed INTEGER,
        wind_gust INTEGER,
        visibility REAL,
        altimeter REAL,
        wx_string TEXT,
        flight_category TEXT,
        ceiling INTEGER,
        raw_metar TEXT,
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_weather_icao ON weather_observations(icao_id);
    CREATE INDEX IF NOT EXISTS idx_weather_fetched ON weather_observations(fetched_at);

    -- FAA airport status cache
    CREATE TABLE IF NOT EXISTS airport_status_cache (
        iata_code TEXT PRIMARY KEY,
        has_delay INTEGER DEFAULT 0,
        delay_reason TEXT,
        temperature TEXT,
        wind TEXT,
        visibility TEXT,
        raw_json TEXT,
        fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    -- IATA delay codes reference
    CREATE TABLE IF NOT EXISTS iata_delay_codes (
        code TEXT PRIMARY KEY,
        category TEXT NOT NULL,
        subcategory TEXT,
        description TEXT NOT NULL,
        responsibility TEXT
    );

    -- ML model predictions log
    CREATE TABLE IF NOT EXISTS predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        origin TEXT NOT NULL,
        dest TEXT NOT NULL,
        airline TEXT,
        dep_hour INTEGER,
        day_of_week INTEGER,
        month INTEGER,
        predicted_delay_prob REAL,
        predicted_delay_minutes REAL,
        weather_factor TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    conn.close()


def query_df(db_path: str, sql: str, params: tuple = ()) -> pd.DataFrame:
    """Execute a SQL query and return results as a DataFrame."""
    conn = get_connection(db_path)
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df


def table_row_count(db_path: str, table: str) -> int:
    """Return the number of rows in a table."""
    conn = get_connection(db_path)
    cur = conn.execute(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
    count = cur.fetchone()[0]
    conn.close()
    return count
