"""KPI calculations and filter logic for aviation operations."""
import pandas as pd


def compute_metrics(ops_df: pd.DataFrame,
                    delays_df: pd.DataFrame) -> dict:
    """Compute key aviation operational metrics."""
    total = len(ops_df) if ops_df is not None else 0
    if total == 0:
        return {
            "total_flights": 0, "on_time": 0, "delayed": 0,
            "cancelled": 0, "diverted": 0, "otp_rate": 0,
            "delay_rate": 0, "avg_delay_min": 0, "critical_delays": 0,
            "total_delay_min": 0,
        }

    on_time = int((ops_df["is_delayed"] == 0).sum()) if "is_delayed" in ops_df.columns else 0
    delayed = int((ops_df["is_delayed"] == 1).sum()) if "is_delayed" in ops_df.columns else 0
    cancelled = int(ops_df["cancelled"].sum()) if "cancelled" in ops_df.columns else 0
    diverted = int(ops_df["diverted"].sum()) if "diverted" in ops_df.columns else 0

    # Exclude cancelled from OTP denominator
    operable = total - cancelled
    otp_rate = (on_time / operable * 100) if operable > 0 else 0

    delay_minutes = pd.to_numeric(
        ops_df.get("arr_delay_minutes", pd.Series(dtype=float)),
        errors="coerce"
    ).fillna(0)

    avg_delay = float(delay_minutes[delay_minutes > 0].mean()) if (delay_minutes > 0).any() else 0
    critical = int((delay_minutes > 60).sum())
    total_delay = float(delay_minutes.sum())

    return {
        "total_flights": total,
        "on_time": on_time,
        "delayed": delayed,
        "cancelled": cancelled,
        "diverted": diverted,
        "otp_rate": round(otp_rate, 1),
        "delay_rate": round(delayed / total * 100, 1) if total > 0 else 0,
        "avg_delay_min": round(avg_delay, 1),
        "critical_delays": critical,
        "total_delay_min": round(total_delay, 0),
    }


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """Apply sidebar filters to a flights DataFrame."""
    if df is None or df.empty:
        return df

    filtered = df.copy()

    # Date filter
    if "flight_date" in filtered.columns and filters.get("date_filter"):
        filtered["flight_date"] = pd.to_datetime(filtered["flight_date"], errors="coerce")
        now = pd.Timestamp.now()
        date_filter = filters["date_filter"]
        if date_filter == "Last 24 Hours":
            filtered = filtered[filtered["flight_date"] >= now - pd.Timedelta(hours=24)]
        elif date_filter == "Last 7 Days":
            filtered = filtered[filtered["flight_date"] >= now - pd.Timedelta(days=7)]
        elif date_filter == "Last 30 Days":
            filtered = filtered[filtered["flight_date"] >= now - pd.Timedelta(days=30)]
        elif date_filter == "Last 90 Days":
            filtered = filtered[filtered["flight_date"] >= now - pd.Timedelta(days=90)]

    # Categorical filters
    if filters.get("airline") and filters["airline"] != "All Airlines" and "airline" in filtered.columns:
        filtered = filtered[filtered["airline"] == filters["airline"]]

    if filters.get("origin") and filters["origin"] != "All Origins" and "origin" in filtered.columns:
        filtered = filtered[filtered["origin"] == filters["origin"]]

    if filters.get("dest") and filters["dest"] != "All Destinations" and "dest" in filtered.columns:
        filtered = filtered[filtered["dest"] == filters["dest"]]

    if filters.get("route") and filters["route"] != "All Routes" and "route" in filtered.columns:
        filtered = filtered[filtered["route"] == filters["route"]]

    if filters.get("delay_category") and filters["delay_category"] != "All Categories":
        if "iata_delay_category" in filtered.columns:
            filtered = filtered[filtered["iata_delay_category"] == filters["delay_category"]]

    # Delay severity range
    if "severity_range" in filters and "arr_delay_minutes" in filtered.columns:
        lo, hi = filters["severity_range"]
        delay_mins = pd.to_numeric(filtered["arr_delay_minutes"], errors="coerce").fillna(0)
        # Keep non-delayed flights AND delayed flights within range
        filtered = filtered[(delay_mins <= 0) | ((delay_mins >= lo) & (delay_mins <= hi))]

    return filtered


def safe_unique_sorted(df: pd.DataFrame, col: str) -> list[str]:
    """Get sorted unique values from a column, handling missing data."""
    if df is None or df.empty or col not in df.columns:
        return []
    return sorted(df[col].dropna().astype(str).unique().tolist())
