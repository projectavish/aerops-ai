<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/Plotly-3b82f6?style=for-the-badge&logo=plotly&logoColor=white" />
  <img src="https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white" />
  <img src="https://img.shields.io/badge/IATA-Standards-22c55e?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" />
</p>

<h1 align="center">✈️ AerOps AI</h1>
<p align="center"><strong>Aviation Operations Intelligence & Predictive Delay Management Platform</strong></p>
<p align="center"><em>Production-grade OCC dashboard for Airlines, MRO, and Ground Handling operations</em></p>

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-features">Features</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-architecture">Architecture</a> •
  <a href="#-data-schema">Data Schema</a> •
  <a href="#-deployment">Deployment</a>
</p>

---

## 🎯 Overview

**AerOps AI** is a real-time aviation operations intelligence platform built for **Operations Control Centers (OCC)**, **Crew Planning**, and **Route Management** teams. It turns raw flight operations data into actionable insights — catching delay cascades before they happen, surfacing crew performance gaps, and producing compliance-ready PDF reports.

### The Problem This Solves

Airlines lose **$25B+ annually** to flight delays. Most operations centers still rely on manual Excel tracking and reactive delay coding — they find out about problems after the cascade has already started. AerOps AI provides the early-warning system that's missing.

### What Makes It Hire-Worthy

This project demonstrates:
- **Domain expertise** — IATA delay codes, OTP, IROPS, duty time regulations, block time, tail-number tracking
- **Production-grade engineering** — NaN-safe pandas filters, session state management, modular render architecture, dynamic data generation, PDF export
- **Real problem framing** — not a tutorial dashboard; built around actual airline operations workflows (OCC, CRM, Route Planning)
- **Scale** — 54,000+ flight records, 52 routes, 600+ flights/day with realistic distributions

---

## ✨ Features

### 🛫 Operations Control Center (OCC)
Real-time command center for dispatchers and duty managers:
- **Live KPIs**: Total Flights, OTP %, Critical Delays (>60 min), In-Air count
- **Delay Trend Charts**: Hourly and daily delay patterns with Plotly
- **IATA Delay Code Breakdown**: Pie/bar charts by delay category
- **Root Cause Analysis**: Ranked delay drivers with frequency and impact
- **Flight Operations Table**: Searchable, filterable, color-coded by status

### 👨‍✈️ Crew & Fleet Performance
Analytics for crew planners and chief pilots:
- **Individual OTP Scores**: Per-captain on-time performance percentages
- **Route Proficiency Heatmap**: Crew performance by route matrix
- **Fatigue Risk Flags**: Duty time and flight frequency indicators
- **Aircraft Utilization**: Tail-number efficiency metrics
- **Fleet Type Comparison**: Performance across aircraft types

### 🌐 Route & Network Analytics
Strategic view for network operations:
- **Route Health Scores**: Delay rate and avg delay by city-pair (52 routes)
- **Hub Congestion Map**: Delay concentration by origin airport
- **Delay Distribution Histograms**: Statistical delay profile per route
- **Aircraft-Route Matrix**: Efficiency heatmap across fleet and network

### 🤖 AI Recommendations
Pattern-driven automated alerts — no LLM needed:
- **High Delay Route**: Routes exceeding 25% delay rate in last 30 days
- **Recurring Tech Issue**: Tail numbers with 3+ technical delay events
- **Crew Fatigue Risk**: Crew members exceeding 40 flights in 30 days
- **Weather Impact Alert**: Airports with 10+ weather delays in last 7 days
- **Confidence Scores**: Data-backed reliability indicators per alert

### 📄 PDF Report Export
One-click operational reports:
- Executive KPI summary
- Delay breakdown by IATA code
- Top delay routes with impact analysis
- Formatted for management briefings and compliance documentation

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/aerops-ai.git
cd aerops-ai

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Launch

```bash
streamlit run dashboard/streamlit_app.py
```

Opens at **http://localhost:8501**

On first launch, the platform auto-generates ~54,000 realistic flight records (52 routes, 90 days, 600+ flights/day). Subsequent launches load from the cached CSV instantly.

---

## 🏗️ Architecture

```
aerops-ai/
├── dashboard/
│   └── streamlit_app.py     # Main application (single-file, ~1500 lines)
├── data/                    # Persistent data store (CSV auto-generated)
├── assets/                  # Screenshots, logos
├── exports/                 # Generated PDF/Excel reports (gitignored)
├── models/                  # Saved ML model artifacts (gitignored)
├── src/                     # Future: extraction of core modules
├── requirements.txt
├── .env.example
├── .gitignore
└── LICENSE
```

### Application Layers

```
┌─────────────────────────────────────────────────────┐
│  PRESENTATION        Streamlit + Custom CSS          │
│  Dark cockpit theme, Font Awesome icons, Plotly      │
├─────────────────────────────────────────────────────┤
│  FILTER ENGINE       apply_filters() + session state │
│  NaN-safe severity filter, isolated ops vs delay     │
│  filter dicts, widget-key-based reset mechanism      │
├─────────────────────────────────────────────────────┤
│  ANALYTICS           Pandas + NumPy + Plotly         │
│  OTP calculations, crew scoring, route aggregations  │
│  AI alert generation from real operational patterns  │
├─────────────────────────────────────────────────────┤
│  DATA LAYER          CSV-backed, Pandas DataFrames   │
│  @st.cache_data, 54k+ records, realistic distributions│
└─────────────────────────────────────────────────────┘
```

### Key Engineering Decisions

**Filter isolation**: `ops_df` and `delays_df` use separate filter dicts. Applying `severity_range` to `ops_df` silently drops all non-delayed flights (because `NaN >= 0 == False` in pandas), causing a 100% delay rate bug. The fix strips `delay_code` and `severity_range` from the ops filter dict.

**NaN-safe severity filter**:
```python
# Keep on-time flights (delay_impact = NaN) AND delayed flights in range
filtered = filtered[(numeric.isna()) | ((numeric >= lo) & (numeric <= hi))]
```

**Session state reset**: Each sidebar widget uses a stable `key=`. The reset button sets `st.session_state.reset_trigger = True`, which on next render assigns default values to all widget keys (including `severity_key` and `delay_code_key`) before the widgets render.

---

## 📋 Data Schema

### Flight Operations (`ops_df`)

| Column | Type | Description |
|--------|------|-------------|
| `flight_id` | str | Unique identifier (FLT00001) |
| `flight_number` | str | Marketing flight number (AA1234) |
| `tail_number` | str | Aircraft registration (N001AA) |
| `crew` | str | Captain name |
| `aircraft_type` | str | Aircraft type (B737-800, A320neo, etc.) |
| `route` | str | Origin-Destination pair (JFK-LAX) |
| `status` | str | On Time / Delayed / Cancelled / In Progress |
| `scheduled_date` | datetime | Scheduled departure |
| `actual_duration` | int | Block time in minutes |

### Delay Events (`delays_df`)

| Column | Type | Description |
|--------|------|-------------|
| `delay_code` | str | IATA delay category |
| `delay_impact` | int | Delay in minutes |
| `root_cause` | str | Specific delay reason |

### IATA Delay Codes

| Code | Category | Common Causes |
|------|----------|---------------|
| Weather | Meteorological | Thunderstorms, fog, snow, wind |
| ATC | Air Traffic Control | Flow control, congestion, EDCT |
| Aircraft Tech | Maintenance | MEL items, AOG, unscheduled MX |
| Crew | Crew Resource | Rest violations, late inbound, sick call |
| Ground Handling | Station | Baggage, fueling, catering, de-ice |
| Passenger | Cabin/Gate | Late boarding, security, WCHR |

---

## 🔧 Configuration

### Sidebar Filters

| Filter | Description |
|--------|-------------|
| Time Period | Last 24H / 7D / 30D / All Time |
| Aircraft Type | Filter by fleet type |
| Crew Member | Filter by captain |
| Route | Filter by city-pair |
| Flight Status | On Time / Delayed / Cancelled / In Progress |
| Delay Category | IATA delay code filter |
| Delay Impact | Slider: 0–180 minutes |

All filters are independently resettable via the **Reset Filters** button.

### Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Optional: OpenAI for enhanced AI recommendations
OPENAI_API_KEY=sk-your-key-here

# Optional: OpenWeatherMap for live weather delay correlation
WEATHER_API_KEY=your-weather-api-key
```

---

## 🚀 Deployment

### Streamlit Cloud (Recommended — Free)

1. Push to GitHub (public repo)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect repo → set main file to `dashboard/streamlit_app.py`
4. Deploy

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
CMD ["streamlit", "run", "dashboard/streamlit_app.py", \
     "--server.address=0.0.0.0", "--server.port=8501"]
```

```bash
docker build -t aerops-ai .
docker run -p 8501:8501 aerops-ai
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Dashboard | Streamlit 1.28+ |
| Data Processing | Pandas 2.0+, NumPy |
| Visualization | Plotly 5.15+ |
| PDF Export | FPDF2 2.7+ |
| Excel Export | openpyxl 3.1+ |
| Styling | Custom CSS, Font Awesome 6.4 |

---

## 📈 Roadmap

### Done ✅
- [x] Real-time OTP monitoring (54k+ flights)
- [x] IATA delay code analysis with drill-down
- [x] Crew performance tracking with heatmaps
- [x] Route analytics across 52 city-pairs
- [x] AI-generated alerts from operational patterns
- [x] PDF report generation
- [x] Dark cockpit UI theme
- [x] NaN-safe filter engine with full reset

### Planned 🗓️
- [ ] Live weather API integration for delay forecasting
- [ ] NOTAM feed correlation
- [ ] Slack/Teams webhook for critical alerts
- [ ] Multi-airline tenant support
- [ ] Mobile OCC view

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit: `git commit -m 'Add weather delay correlation'`
4. Push: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

[MIT](LICENSE) © 2026

Built for the aviation community. Ensure compliance with your airline's data governance policy before connecting to live operational data.

---

<p align="center">
  <a href="https://github.com/yourusername/aerops-ai/issues">Report Bug</a> •
  <a href="https://github.com/yourusername/aerops-ai/issues">Request Feature</a>
</p>
<p align="center"><sub>✈️ Built for operations professionals, by someone who cares about the details.</sub></p>
