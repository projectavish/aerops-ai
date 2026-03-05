<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/Plotly-5.15+-3b82f6?style=flat-square&logo=plotly&logoColor=white" />
  <img src="https://img.shields.io/badge/IATA-Delay_Codes-22c55e?style=flat-square" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" />
</p>

# AerOps AI

**Real-time aviation operations intelligence for OCC, Crew Planning, and Network Operations.**

Airlines lose $25B+ annually to flight delays. Most operations centers still react after the cascade starts — tracking delays in spreadsheets, manually coding IATA reasons, and identifying patterns after the damage is done. AerOps AI gives dispatch and network operations teams the early-warning layer they're missing.

---

## What it does

**Operations Control Center view** — live KPIs (OTP, critical delays, in-air count), hourly delay trend, IATA code breakdown, root cause ranking, and a filterable flight ops table. The full filter set (aircraft type, crew, route, status, delay category, delay severity) propagates instantly across every chart.

**Crew & Fleet Performance** — per-captain OTP scores, flight distribution, leaderboard with unique routes and turnaround stats. Useful for crew planners and chief pilots tracking training needs against actual performance data.

**Route Analytics** — flight volume and status breakdown by city-pair across 52 routes. Identifies which routes are driving delay counts, which fleet types are underperforming on specific sectors, and where ground time is being eroded.

**AI Alerts** — pattern detection against the current filtered dataset. Four alert types:
- Routes exceeding 25% delay rate in the active period
- Tail numbers with 3+ technical delay events (AOG risk indicator)
- Crew members exceeding 40 flights in 30 days (duty time pressure)
- Weather delay spikes — 10+ events in 7 days triggers IROPS flag

**PDF Export** — one-click operational report with KPI summary and delay breakdown by IATA code. Formatted for shift handovers and management briefings.

---

## Technical decisions worth noting

**Filter isolation between ops and delays data.** The delay severity slider and IATA code filter only apply to `delays_df` (flights with a delay event). Applying them to `ops_df` silently drops all on-time flights because `pandas` evaluates `NaN >= 0` as `False` — every non-delayed flight has `delay_impact = NaN` and disappears from the filtered set, producing a 100% delay rate. The fix is a separate `ops_filters` dict that strips those keys before `apply_filters()` touches `ops_df`.

```python
# NaN-safe severity filter — preserves on-time flights
filtered = filtered[(numeric.isna()) | ((numeric >= lo) & (numeric <= hi))]

# ops_df and delays_df get different filter dicts
ops_filters = {k: v for k, v in filters.items() if k not in ('delay_code', 'severity_range')}
filtered_ops = apply_filters(ops_df, ops_filters)
filtered_delays = apply_filters(delays_df, filters)
```

**CSV caching.** The demo dataset is ~54,000 rows. Without `@st.cache_data`, every sidebar interaction triggers a full disk read — the page appears frozen. With caching, the CSV is loaded once per session and all filter changes are pure in-memory pandas operations.

**AI alerts from data, not LLMs.** The alert generation runs against the filtered dataset so results stay contextual to what the user is looking at. No external API calls, no hallucinated recommendations — every alert has a traceable source in the data (delay counts, tail numbers, crew frequencies).

**Session state reset.** Sidebar widgets use stable `key=` strings. The reset button sets `st.session_state.reset_trigger = True`, which on next render assigns default values to all widget keys — including the slider (`severity_key`) and dropdown (`delay_code_key`) — before the widgets render, ensuring a clean state without widget orphaning.

---

## Data model

The platform runs on a single denormalized ops CSV. All analytics derive from this schema:

| Column | Type | Notes |
|--------|------|-------|
| `flight_id` | str | Unique per operation |
| `flight_number` | str | Marketing number (AA1234) |
| `tail_number` | str | Aircraft registration — used for MRO alerts |
| `crew` | str | Captain — used for fatigue risk and OTP scoring |
| `aircraft_type` | str | B737-800, A320neo, A321, B777-300ER, A220-300, E175 |
| `route` | str | IATA city-pair (JFK-LAX) |
| `status` | str | On Time / Delayed / Cancelled / In Progress |
| `scheduled_date` | datetime | Used for all time-period filters |
| `delay_code` | str | IATA category — Weather / ATC / Aircraft Tech / Crew / Ground Handling / Passenger |
| `delay_impact` | int | Minutes — NaN for non-delayed flights |
| `root_cause` | str | Free-text reason (e.g. "FOD on runway", "MEL item 29-10") |
| `actual_duration` | int | Block time in minutes |

Demo data: 90 days, 52 routes, ~600 flights/day on weekdays (~54,000 total), realistic delay distributions by route type and time of day.

---

## Stack

| Layer | Technology |
|-------|-----------|
| Dashboard | Streamlit 1.28+ |
| Data | Pandas 2.0+, NumPy |
| Charts | Plotly 5.15+ |
| PDF export | FPDF2 2.7+ |
| Excel export | openpyxl 3.1+ |
| Styling | Custom CSS, Font Awesome 6.4 |

---

## Setup

```bash
git clone https://github.com/yourusername/aerops-ai.git
cd aerops-ai
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run dashboard/streamlit_app.py
```

On first launch the app generates the demo dataset (~54k flights). Subsequent loads use the cached CSV. To regenerate, use the **Regenerate Demo Data** button in the sidebar or delete `flight_operations.csv`.

To use real data, upload a CSV via the sidebar file uploader — any CSV matching the schema above works.

---

## Deployment

**Streamlit Cloud (free)**

Push to a public GitHub repo, connect at [share.streamlit.io](https://share.streamlit.io), set the main file to `dashboard/streamlit_app.py`.

**Docker**

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
CMD ["streamlit", "run", "dashboard/streamlit_app.py", "--server.address=0.0.0.0"]
```

---

## Roadmap

- [ ] Live weather API correlation (OpenWeatherMap / Aviation Weather Center)
- [ ] NOTAM feed parsing for proactive route risk scoring
- [ ] Slack / Teams webhook for critical delay alerts
- [ ] SQLite backend to replace CSV for multi-session persistence
- [ ] Multi-airline tenant support

---

## License

[MIT](LICENSE)

---

*Data privacy note: the platform ships with synthetic demo data only. If connecting to live operational data, ensure compliance with your airline's data governance and GDPR/DPA requirements before deployment.*
