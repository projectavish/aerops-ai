"""Load OurAirports data for airport reference lookups."""
import logging
from pathlib import Path

import pandas as pd

from aerops.config import AIRPORTS_CSV, DB_PATH
from aerops.db import get_connection, init_db

logger = logging.getLogger(__name__)

OURAIRPORTS_URL = (
    "https://davidmegginson.github.io/ourairports-data/airports.csv"
)

# IATA → ICAO lookup cache
_iata_to_icao: dict[str, str] = {}


def download_airports(output_path: str = AIRPORTS_CSV) -> str:
    """Download OurAirports CSV if not already present."""
    path = Path(output_path)
    if path.exists() and path.stat().st_size > 100_000:
        logger.info("Airports CSV already exists: %s", output_path)
        return output_path

    import requests
    logger.info("Downloading airports from OurAirports ...")
    resp = requests.get(OURAIRPORTS_URL, timeout=30)
    resp.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(resp.content)
    logger.info("Saved %d bytes to %s", len(resp.content), output_path)
    return output_path


def load_airports_to_db(csv_path: str = AIRPORTS_CSV,
                        db_path: str = DB_PATH) -> int:
    """Load filtered airports into the SQLite airports table."""
    init_db(db_path)

    if not Path(csv_path).exists():
        csv_path = download_airports(csv_path)

    df = pd.read_csv(csv_path, low_memory=False)

    # Filter: large and medium airports with IATA codes
    df = df[
        df["type"].isin(["large_airport", "medium_airport"])
        & df["iata_code"].notna()
        & (df["iata_code"].str.len() == 3)
    ].copy()

    # Select and rename columns
    airports = df[["iata_code", "ident", "name", "latitude_deg",
                    "longitude_deg", "elevation_ft", "iso_country",
                    "iso_region"]].copy()
    airports.columns = ["iata_code", "icao_code", "name", "latitude",
                        "longitude", "elevation_ft", "country", "region"]

    # Drop duplicates on IATA code
    airports = airports.drop_duplicates(subset="iata_code", keep="first")

    conn = get_connection(db_path)
    # Clear existing and reload
    conn.execute("DELETE FROM airports")
    airports.to_sql("airports", conn, if_exists="append", index=False)
    conn.commit()
    count = len(airports)
    conn.close()

    logger.info("Loaded %d airports into database", count)
    return count


def get_iata_to_icao(db_path: str = DB_PATH) -> dict[str, str]:
    """Build IATA→ICAO lookup from the airports table."""
    global _iata_to_icao
    if _iata_to_icao:
        return _iata_to_icao

    conn = get_connection(db_path)
    rows = conn.execute(
        "SELECT iata_code, icao_code FROM airports "
        "WHERE icao_code IS NOT NULL"
    ).fetchall()
    conn.close()

    _iata_to_icao = {r["iata_code"]: r["icao_code"] for r in rows}
    return _iata_to_icao


def get_airport_info(iata_code: str, db_path: str = DB_PATH) -> dict | None:
    """Get airport details by IATA code."""
    conn = get_connection(db_path)
    row = conn.execute(
        "SELECT * FROM airports WHERE iata_code = ?", (iata_code,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
