"""Aviation Weather Center METAR/TAF API client with SQLite caching."""
import logging
from datetime import datetime, timedelta

import requests

from aerops.config import AWC_METAR_URL, DB_PATH, METAR_CACHE_TTL
from aerops.db import get_connection

logger = logging.getLogger(__name__)


def fetch_metar(icao_id: str, timeout: int = 10) -> dict | None:
    """Fetch current METAR for a single station from AWC API."""
    try:
        resp = requests.get(
            AWC_METAR_URL,
            params={"ids": icao_id, "format": "json"},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0]
        return None
    except Exception as e:
        logger.warning("METAR fetch failed for %s: %s", icao_id, e)
        return None


def fetch_metar_batch(icao_ids: list[str], timeout: int = 15) -> list[dict]:
    """Fetch METARs for multiple stations in one request."""
    if not icao_ids:
        return []
    try:
        ids_str = ",".join(icao_ids)
        resp = requests.get(
            AWC_METAR_URL,
            params={"ids": ids_str, "format": "json"},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.warning("Batch METAR fetch failed: %s", e)
        return []


def cache_metar_to_db(metar: dict, db_path: str = DB_PATH) -> None:
    """Store a METAR observation in the cache table."""
    conn = get_connection(db_path)
    try:
        # Extract ceiling from cloud layers
        ceiling = _extract_ceiling(metar.get("clouds", []))

        conn.execute("""
            INSERT INTO weather_observations
            (icao_id, obs_time, temp, dewp, wind_dir, wind_speed, wind_gust,
             visibility, altimeter, wx_string, flight_category, ceiling, raw_metar)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metar.get("icaoId", ""),
            metar.get("obsTime", ""),
            metar.get("temp"),
            metar.get("dewp"),
            metar.get("wdir"),
            metar.get("wspd"),
            metar.get("wgst"),
            metar.get("visib"),
            metar.get("altim"),
            metar.get("wxString", ""),
            metar.get("fltCat", ""),
            ceiling,
            metar.get("rawOb", ""),
        ))
        conn.commit()
    except Exception as e:
        logger.warning("Failed to cache METAR: %s", e)
    finally:
        conn.close()


def get_cached_metar(icao_id: str, db_path: str = DB_PATH) -> dict | None:
    """Get a cached METAR if still fresh (within TTL)."""
    conn = get_connection(db_path)
    try:
        cutoff = (datetime.utcnow() - timedelta(seconds=METAR_CACHE_TTL)).isoformat()
        row = conn.execute("""
            SELECT * FROM weather_observations
            WHERE icao_id = ? AND fetched_at > ?
            ORDER BY fetched_at DESC LIMIT 1
        """, (icao_id, cutoff)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_cached_or_fetch(icao_id: str, db_path: str = DB_PATH) -> dict | None:
    """Return cached METAR if fresh, otherwise fetch from API and cache."""
    cached = get_cached_metar(icao_id, db_path)
    if cached:
        return cached

    metar = fetch_metar(icao_id)
    if metar:
        cache_metar_to_db(metar, db_path)
        return metar
    return None


def get_flight_category(visibility: float | None,
                        ceiling: int | None) -> str:
    """Determine flight category from visibility and ceiling.

    VFR:  vis > 5 SM and ceiling > 3000 ft
    MVFR: vis 3-5 SM or ceiling 1000-3000 ft
    IFR:  vis 1-3 SM or ceiling 500-1000 ft
    LIFR: vis < 1 SM or ceiling < 500 ft
    """
    if visibility is None and ceiling is None:
        return "VFR"

    vis = visibility if visibility is not None else 10
    ceil = ceiling if ceiling is not None else 10000

    if vis < 1 or ceil < 500:
        return "LIFR"
    if vis < 3 or ceil < 1000:
        return "IFR"
    if vis <= 5 or ceil <= 3000:
        return "MVFR"
    return "VFR"


def _extract_ceiling(clouds: list) -> int | None:
    """Extract ceiling height from cloud layers (BKN or OVC)."""
    if not clouds or not isinstance(clouds, list):
        return None
    for layer in clouds:
        if isinstance(layer, dict):
            cover = layer.get("cover", "")
            if cover in ("BKN", "OVC"):
                base = layer.get("base")
                if base is not None:
                    return int(base)
    return None
