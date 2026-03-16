"""AI-powered operational alerts based on real data patterns."""
import pandas as pd


def generate_alerts(ops_df: pd.DataFrame,
                    delays_df: pd.DataFrame) -> list[dict]:
    """Generate data-driven operational alerts from flight data.

    Alert types:
    1. Route delay rate exceeding threshold
    2. Airline performance degradation
    3. Weather-related delay spikes
    4. Reactionary delay chains (late aircraft cascading)
    5. Airport congestion warnings
    """
    alerts = []
    if ops_df is None or ops_df.empty:
        return alerts

    # 1. High-delay routes (>30% delay rate with minimum sample)
    if "route" in ops_df.columns and "is_delayed" in ops_df.columns:
        route_stats = ops_df.groupby("route").agg(
            total=("is_delayed", "count"),
            delayed=("is_delayed", "sum"),
        )
        route_stats["delay_rate"] = route_stats["delayed"] / route_stats["total"]
        high_delay_routes = route_stats[
            (route_stats["delay_rate"] > 0.30) & (route_stats["total"] >= 10)
        ].sort_values("delay_rate", ascending=False)

        for route, row in high_delay_routes.head(5).iterrows():
            alerts.append({
                "type": "Route Delay Alert",
                "severity": "high" if row["delay_rate"] > 0.40 else "medium",
                "entity": route,
                "message": f"Route {route}: {row['delay_rate']:.0%} delay rate "
                           f"({int(row['delayed'])}/{int(row['total'])} flights)",
                "recommendation": "Review scheduling buffer and ground handling at both endpoints.",
                "confidence": min(95, int(50 + row["total"])),
            })

    # 2. Airline performance issues
    if "airline" in ops_df.columns and "is_delayed" in ops_df.columns:
        airline_stats = ops_df.groupby("airline").agg(
            total=("is_delayed", "count"),
            delayed=("is_delayed", "sum"),
        )
        airline_stats["delay_rate"] = airline_stats["delayed"] / airline_stats["total"]
        problem_airlines = airline_stats[
            (airline_stats["delay_rate"] > 0.25) & (airline_stats["total"] >= 20)
        ]
        for airline, row in problem_airlines.iterrows():
            alerts.append({
                "type": "Airline Performance",
                "severity": "medium",
                "entity": airline,
                "message": f"Airline {airline}: {row['delay_rate']:.0%} delay rate "
                           f"across {int(row['total'])} flights",
                "recommendation": "Investigate carrier-specific delay drivers (crew, maintenance, ops).",
                "confidence": min(90, int(50 + row["total"] * 0.5)),
            })

    # 3. Weather delay concentration
    if delays_df is not None and not delays_df.empty and "iata_delay_category" in delays_df.columns:
        weather_delays = delays_df[delays_df["iata_delay_category"] == "Weather"]
        if len(weather_delays) > 5:
            if "origin" in weather_delays.columns:
                wx_by_airport = weather_delays["origin"].value_counts()
                for airport, count in wx_by_airport.head(3).items():
                    if count >= 3:
                        alerts.append({
                            "type": "Weather Impact",
                            "severity": "high",
                            "entity": airport,
                            "message": f"{airport}: {count} weather-related delays detected",
                            "recommendation": "Monitor METAR/TAF. Consider pre-emptive rebooking for affected routes.",
                            "confidence": 85,
                        })

    # 4. Late aircraft cascade (reactionary delays)
    if delays_df is not None and not delays_df.empty and "iata_delay_category" in delays_df.columns:
        react_delays = delays_df[delays_df["iata_delay_category"] == "Reactionary"]
        if len(react_delays) > 3:
            if "tail_num" in react_delays.columns:
                tail_chains = react_delays["tail_num"].value_counts()
                for tail, count in tail_chains.head(3).items():
                    if count >= 2 and tail and str(tail) != "nan":
                        alerts.append({
                            "type": "Delay Cascade",
                            "severity": "high",
                            "entity": tail,
                            "message": f"Aircraft {tail}: {count} reactionary delays (cascade risk)",
                            "recommendation": "Consider aircraft swap or schedule padding for next rotation.",
                            "confidence": 80,
                        })

    # 5. Airport congestion
    if "origin" in ops_df.columns and "arr_delay_minutes" in ops_df.columns:
        airport_delays = ops_df.groupby("origin").agg(
            avg_delay=("arr_delay_minutes", "mean"),
            flight_count=("origin", "count"),
        )
        congested = airport_delays[
            (airport_delays["avg_delay"] > 20) & (airport_delays["flight_count"] >= 15)
        ].sort_values("avg_delay", ascending=False)

        for airport, row in congested.head(3).iterrows():
            alerts.append({
                "type": "Airport Congestion",
                "severity": "medium",
                "entity": airport,
                "message": f"{airport}: avg {row['avg_delay']:.0f}min delay "
                           f"across {int(row['flight_count'])} departures",
                "recommendation": "Check FAA ATCSCC for ground stops or flow control programs.",
                "confidence": 75,
            })

    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    alerts.sort(key=lambda a: severity_order.get(a["severity"], 2))

    return alerts
