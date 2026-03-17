"""Live Operations Center tab - weather, FAA status, and AI alerts."""
import logging

import streamlit as st
import pandas as pd

from aerops.config import TOP_AIRPORTS
from aerops.data.weather_api import fetch_metar_batch
from aerops.data.faa_status import get_cached_or_fetch as get_faa_status
from aerops.data.airports import get_iata_to_icao
from aerops.analytics.alerts import generate_alerts

logger = logging.getLogger(__name__)

# Flight category colour mapping
_FLTCAT_COLORS = {
    "VFR": "#22c55e",
    "MVFR": "#eab308",
    "IFR": "#f97316",
    "LIFR": "#ef4444",
}


def render_ops_center(ops_df: pd.DataFrame, db_path: str) -> None:
    """Render the live operations centre with weather, FAA status, and alerts."""
    st.markdown(
        '<h2><i class="fas fa-tower-broadcast"></i> Live Operations Center</h2>',
        unsafe_allow_html=True,
    )

    if ops_df is None or ops_df.empty:
        st.info("No operations data available.")

    # ------------------------------------------------------------------
    # Section 1 - Live Weather (METAR)
    # ------------------------------------------------------------------
    st.markdown("#### Live Airport Weather (METAR)")
    _render_weather_section(db_path)

    st.markdown("---")

    # ------------------------------------------------------------------
    # Section 2 - FAA Airport Status
    # ------------------------------------------------------------------
    st.markdown("#### FAA Airport Status")
    _render_faa_status()

    st.markdown("---")

    # ------------------------------------------------------------------
    # Section 3 - AI Operational Alerts
    # ------------------------------------------------------------------
    st.markdown("#### AI Operational Alerts")
    _render_alerts(ops_df)


# ======================================================================
# Private helpers
# ======================================================================

def _render_weather_section(db_path: str) -> None:
    """Fetch live METAR for top airports and display weather cards."""
    airports_to_check = TOP_AIRPORTS[:10]

    # Build IATA -> ICAO mapping
    try:
        iata_to_icao = get_iata_to_icao(db_path)
    except Exception:
        iata_to_icao = {}

    # Map IATA codes to ICAO for METAR lookup
    icao_ids = []
    icao_to_iata = {}
    for iata in airports_to_check:
        icao = iata_to_icao.get(iata)
        if icao:
            icao_ids.append(icao)
            icao_to_iata[icao] = iata
        else:
            # Fallback: US airports typically K + IATA
            fallback = f"K{iata}"
            icao_ids.append(fallback)
            icao_to_iata[fallback] = iata

    if not icao_ids:
        st.info("Could not resolve any ICAO codes. Airport reference data may not be loaded.")
        return

    # Fetch METARs
    try:
        metars = fetch_metar_batch(icao_ids, timeout=10)
    except Exception as exc:
        logger.warning("METAR batch fetch failed: %s", exc)
        metars = []

    if not metars:
        st.warning(
            "Live weather data is currently unavailable. "
            "The Aviation Weather Center API may be unreachable."
        )
        return

    # Build a lookup by ICAO id
    metar_lookup = {}
    for m in metars:
        icao_id = m.get("icaoId", "")
        metar_lookup[icao_id] = m

    # Render weather cards in rows of 5
    cards_per_row = 5
    for row_start in range(0, len(icao_ids), cards_per_row):
        row_icaos = icao_ids[row_start: row_start + cards_per_row]
        cols = st.columns(len(row_icaos))
        for col, icao in zip(cols, row_icaos):
            iata = icao_to_iata.get(icao, icao)
            metar = metar_lookup.get(icao)
            with col:
                _render_weather_card(iata, icao, metar)


def _render_weather_card(iata: str, icao: str, metar: dict | None) -> None:
    """Display a single airport weather card."""
    if metar is None:
        st.markdown(
            f'<div style="background:#1e293b; border:1px solid #334155; '
            f'border-radius:10px; padding:1rem; text-align:center;">'
            f'<strong style="color:#38bdf8;">{iata}</strong><br>'
            f'<span style="color:#94a3b8; font-size:0.8rem;">Data unavailable</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        return

    temp = metar.get("temp", "N/A")
    wind_speed = metar.get("wspd", 0)
    wind_dir = metar.get("wdir", "VRB")
    visibility = metar.get("visib", "N/A")
    flt_cat = metar.get("fltCat", "VFR")
    cat_color = _FLTCAT_COLORS.get(flt_cat, "#94a3b8")
    wx_string = metar.get("wxString", "")

    temp_display = f"{temp}C" if temp != "N/A" else "N/A"
    wind_display = f"{wind_dir} at {wind_speed} kt" if wind_speed else "Calm"
    vis_display = f"{visibility} SM" if visibility != "N/A" else "N/A"
    wx_display = f"<br><span style='font-size:0.7rem;'>{wx_string}</span>" if wx_string else ""

    st.markdown(
        f'<div style="background:#1e293b; border:1px solid {cat_color}; '
        f'border-radius:10px; padding:1rem; text-align:center;">'
        f'<strong style="color:#38bdf8; font-size:1.1rem;">{iata}</strong><br>'
        f'<span style="background:{cat_color}; color:#fff; padding:2px 8px; '
        f'border-radius:4px; font-size:0.75rem; font-weight:700;">{flt_cat}</span><br>'
        f'<span style="color:#e2e8f0; font-size:0.85rem;">{temp_display}</span><br>'
        f'<span style="color:#94a3b8; font-size:0.75rem;">{wind_display}</span><br>'
        f'<span style="color:#94a3b8; font-size:0.75rem;">Vis: {vis_display}</span>'
        f'{wx_display}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_faa_status() -> None:
    """Fetch and display FAA airport status for key airports."""
    key_airports = ["JFK", "LAX", "ORD", "ATL", "DFW", "SFO"]
    statuses = {}

    for iata in key_airports:
        try:
            data = get_faa_status(iata)
            if data:
                statuses[iata] = data
        except Exception:
            pass

    if not statuses:
        st.info(
            "FAA airport status data is currently unavailable. "
            "The FAA ASWS API may be unreachable."
        )
        return

    cols = st.columns(len(statuses))
    for col, (iata, data) in zip(cols, statuses.items()):
        with col:
            _render_faa_card(iata, data)


def _render_faa_card(iata: str, data: dict) -> None:
    """Display a single FAA airport status card."""
    # Handle both raw API format and cached DB format
    has_delay = False
    delay_reason = ""

    if "Delay" in data:
        has_delay = str(data["Delay"]).lower() == "true"
    elif "has_delay" in data:
        has_delay = bool(data["has_delay"])

    if "Status" in data:
        status_list = data["Status"]
        if isinstance(status_list, list):
            reasons = [s.get("Reason", "") for s in status_list if isinstance(s, dict)]
            delay_reason = "; ".join(r for r in reasons if r)
        elif isinstance(status_list, dict):
            delay_reason = status_list.get("Reason", "")
    elif "delay_reason" in data:
        delay_reason = data.get("delay_reason", "")

    border_color = "#ef4444" if has_delay else "#22c55e"
    status_text = "DELAY" if has_delay else "NORMAL"
    status_color = "#ef4444" if has_delay else "#22c55e"
    reason_html = (
        f'<br><span style="color:#fbbf24; font-size:0.7rem;">{delay_reason}</span>'
        if delay_reason
        else ""
    )

    st.markdown(
        f'<div style="background:#1e293b; border:1px solid {border_color}; '
        f'border-radius:10px; padding:0.75rem; text-align:center;">'
        f'<strong style="color:#38bdf8;">{iata}</strong><br>'
        f'<span style="color:{status_color}; font-weight:700; font-size:0.85rem;">'
        f'{status_text}</span>'
        f'{reason_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_alerts(ops_df: pd.DataFrame) -> None:
    """Generate and display AI operational alerts."""
    if ops_df is None or ops_df.empty:
        st.info("No operational data available for alert generation.")
        return

    # Build a delays subset for the alert engine
    delays_df = None
    if "is_delayed" in ops_df.columns:
        delays_df = ops_df[ops_df["is_delayed"] == 1].copy()

    try:
        alerts = generate_alerts(ops_df, delays_df)
    except Exception as exc:
        logger.warning("Alert generation failed: %s", exc)
        st.warning("Could not generate AI alerts at this time.")
        return

    if not alerts:
        st.success("No active alerts. All operations running within normal parameters.")
        return

    severity_icons = {
        "high": '<i class="fas fa-exclamation-circle" style="color:#ef4444;"></i>',
        "medium": '<i class="fas fa-exclamation-triangle" style="color:#eab308;"></i>',
        "low": '<i class="fas fa-info-circle" style="color:#3b82f6;"></i>',
    }
    severity_border = {
        "high": "#ef4444",
        "medium": "#eab308",
        "low": "#3b82f6",
    }

    for alert in alerts[:10]:
        sev = alert.get("severity", "low")
        icon = severity_icons.get(sev, severity_icons["low"])
        border = severity_border.get(sev, "#3b82f6")
        alert_type = alert.get("type", "Alert")
        message = alert.get("message", "")
        recommendation = alert.get("recommendation", "")
        confidence = alert.get("confidence", 0)

        st.markdown(
            f'<div style="background:#1e293b; border-left:4px solid {border}; '
            f'border-radius:0 8px 8px 0; padding:0.75rem 1rem; margin-bottom:0.5rem;">'
            f'{icon} <strong style="color:#f1f5f9;">{alert_type}</strong>'
            f'<span style="color:#94a3b8; font-size:0.75rem; float:right;">'
            f'Confidence: {confidence}%</span><br>'
            f'<span style="color:#e2e8f0; font-size:0.9rem;">{message}</span><br>'
            f'<span style="color:#38bdf8; font-size:0.8rem;">'
            f'<i class="fas fa-lightbulb"></i> {recommendation}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
