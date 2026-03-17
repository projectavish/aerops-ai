"""FAA Airport Status API client with caching."""
import json
import logging
from datetime import datetime, timedelta

import requests

from aerops.config import DB_PATH, FAA_STATUS_CACHE_TTL, FAA_STATUS_URL
from aerops.db import get_connection

logger = logging.getLogger(__name__)


def fetch_airport_status(iata_code: str, timeout: int = 5) -> dict | None:
    """Fetch current delay/status for an airport from FAA API."""
    try:
        url = f"{FAA_STATUS_URL}/{iata_code}"
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data
    except Exception as e:
        logger.warning("FAA status fetch failed for %s: %s", iata_code, e)
        return None


def cache_status(data: dict, db_path: str = DB_PATH) -> None:
    """Cache airport status in SQLite."""
    conn = get_connection(db_path)
    try:
        iata = data.get("IATA", data.get("iata", ""))
        has_delay = 1 if data.get("Delay", "false") == "true" else 0

        # Extract delay reason if present
        delay_reason = ""
        status_list = data.get("Status", [])
        if isinstance(status_list, list):
            reasons = [s.get("Reason", "") for s in status_list if isinstance(s, dict)]
            delay_reason = "; ".join(r for r in reasons if r)
        elif isinstance(status_list, dict):
            delay_reason = status_list.get("Reason", "")

        weather = data.get("Weather", {})
        temp = weather.get("Temp", [""])[0] if isinstance(weather.get("Temp"), list) else str(weather.get("Temp", ""))
        wind = str(weather.get("Wind", ""))
        visibility = str(weather.get("Visibility", ""))

        conn.execute("""
            INSERT OR REPLACE INTO airport_status_cache
            (iata_code, has_delay, delay_reason, temperature, wind, visibility, raw_json, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (iata, has_delay, delay_reason, temp, wind, visibility, json.dumps(data)))
        conn.commit()
    except Exception as e:
        logger.warning("Failed to cache FAA status: %s", e)
    finally:
        conn.close()


def get_cached_status(iata_code: str, db_path: str = DB_PATH) -> dict | None:
    """Get cached status if still fresh."""
    conn = get_connection(db_path)
    try:
        cutoff = (datetime.utcnow() - timedelta(seconds=FAA_STATUS_CACHE_TTL)).isoformat()
        row = conn.execute("""
            SELECT * FROM airport_status_cache
            WHERE iata_code = ? AND fetched_at > ?
        """, (iata_code, cutoff)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_cached_or_fetch(iata_code: str, db_path: str = DB_PATH) -> dict | None:
    """Return cached status if fresh, otherwise fetch and cache."""
    cached = get_cached_status(iata_code, db_path)
    if cached:
        return cached

    data = fetch_airport_status(iata_code)
    if data:
        cache_status(data, db_path)
        return data
    return None
