"""Central configuration for AerOps AI."""
import os
from pathlib import Path

# Project root
ROOT_DIR = Path(__file__).resolve().parent.parent

# Database
DB_PATH = os.environ.get("DATABASE_PATH", str(ROOT_DIR / "data" / "flight_ops.db"))

# Data directories
BTS_DATA_DIR = str(ROOT_DIR / "data" / "bts")
AIRPORTS_CSV = str(ROOT_DIR / "data" / "airports.csv")
IATA_CODES_JSON = str(ROOT_DIR / "data" / "iata_delay_codes.json")

# API endpoints (no auth required)
AWC_METAR_URL = "https://aviationweather.gov/api/data/metar"
AWC_TAF_URL = "https://aviationweather.gov/api/data/taf"
FAA_STATUS_URL = "https://soa.smext.faa.gov/asws/api/airport/status"

# Optional API keys
CHECKWX_API_KEY = os.environ.get("CHECKWX_API_KEY", "")

# Cache TTL (seconds)
METAR_CACHE_TTL = 1800   # 30 minutes
FAA_STATUS_CACHE_TTL = 900  # 15 minutes

# ML model paths
MODEL_DIR = str(ROOT_DIR / "models")
DELAY_MODEL_PATH = os.path.join(MODEL_DIR, "delay_model.joblib")
FEATURE_COLUMNS_PATH = os.path.join(MODEL_DIR, "feature_columns.json")

# Dashboard theme constants
THEME = {
    "bg_primary": "#0f172a",
    "bg_secondary": "#1e293b",
    "accent": "#0ea5e9",
    "accent_light": "#38bdf8",
    "text_primary": "#f1f5f9",
    "text_secondary": "#cbd5e1",
    "text_muted": "#94a3b8",
    "border": "#334155",
    "success": "#22c55e",
    "warning": "#eab308",
    "danger": "#ef4444",
    "info": "#3b82f6",
}

# Chart layout defaults
CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#e2e8f0",
    font_family="Inter, sans-serif",
)

# Top US airports for weather monitoring
TOP_AIRPORTS = [
    "ATL", "DFW", "DEN", "ORD", "LAX", "CLT", "MCO", "LAS",
    "PHX", "MIA", "SEA", "SFO", "EWR", "JFK", "BOS", "MSP",
    "DTW", "FLL", "IAH", "DCA",
]

# BTS delay cause columns
BTS_DELAY_COLUMNS = [
    "CarrierDelay", "WeatherDelay", "NASDelay",
    "SecurityDelay", "LateAircraftDelay",
]

# Demo data size
DEMO_FLIGHT_COUNT = 5000
