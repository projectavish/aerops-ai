"""IATA delay code reference data and BTS-to-IATA mapping."""
import json
from pathlib import Path
from typing import Optional

from aerops.config import IATA_CODES_JSON

# BTS delay cause columns → IATA delay code mapping
BTS_TO_IATA = {
    "CarrierDelay": {
        "iata_code": "96",
        "iata_category": "Reactionary",
        "description": "Carrier - operations control, re-routing",
    },
    "WeatherDelay": {
        "iata_code": "71",
        "iata_category": "Weather",
        "description": "Weather below departure/arrival limits",
    },
    "NASDelay": {
        "iata_code": "81",
        "iata_category": "ATC/Airport",
        "description": "National Airspace System - ATC flow restriction",
    },
    "SecurityDelay": {
        "iata_code": "85",
        "iata_category": "ATC/Airport",
        "description": "Security delay at airport",
    },
    "LateAircraftDelay": {
        "iata_code": "93",
        "iata_category": "Reactionary",
        "description": "Late arriving aircraft from previous sector",
    },
}

# BTS cancellation codes → IATA mapping
BTS_CANCELLATION_TO_IATA = {
    "A": {"iata_code": "96", "description": "Carrier"},
    "B": {"iata_code": "71", "description": "Weather"},
    "C": {"iata_code": "81", "description": "NAS"},
    "D": {"iata_code": "85", "description": "Security"},
}

_codes_cache: Optional[list] = None


def load_iata_codes(json_path: str = IATA_CODES_JSON) -> list[dict]:
    """Load IATA delay codes from the reference JSON file."""
    global _codes_cache
    if _codes_cache is not None:
        return _codes_cache
    path = Path(json_path)
    if not path.exists():
        return []
    with open(path, "r") as f:
        data = json.load(f)
    _codes_cache = data.get("codes", [])
    return _codes_cache


def get_code_description(code: str) -> str:
    """Get the description for an IATA delay code."""
    codes = load_iata_codes()
    for c in codes:
        if c["code"] == code:
            return c["description"]
    return f"Unknown code: {code}"


def get_code_info(code: str) -> Optional[dict]:
    """Get full info for an IATA delay code."""
    codes = load_iata_codes()
    for c in codes:
        if c["code"] == code:
            return c
    return None


def get_category_codes(category: str) -> list[dict]:
    """Get all codes in a given category."""
    codes = load_iata_codes()
    return [c for c in codes if c["category"] == category]


def get_all_categories() -> list[str]:
    """Get all unique delay code categories."""
    codes = load_iata_codes()
    seen = []
    for c in codes:
        if c["category"] not in seen:
            seen.append(c["category"])
    return seen


def get_responsibility_summary() -> dict[str, list[str]]:
    """Group codes by responsibility (Airline, ATC, Weather, etc.)."""
    codes = load_iata_codes()
    result: dict[str, list[str]] = {}
    for c in codes:
        resp = c.get("responsibility", "Unknown")
        if resp not in result:
            result[resp] = []
        result[resp].append(c["code"])
    return result


def map_bts_cause_to_iata(primary_cause: str) -> tuple[str, str]:
    """Map a BTS delay cause column name to (iata_code, iata_category)."""
    mapping = BTS_TO_IATA.get(primary_cause)
    if mapping:
        return mapping["iata_code"], mapping["iata_category"]
    return "99", "Miscellaneous"
