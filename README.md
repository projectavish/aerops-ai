<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" />
  <img src="https://img.shields.io/badge/scikit--learn-ML_Pipeline-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/Plotly-Interactive_Charts-3F4F75?style=for-the-badge&logo=plotly&logoColor=white" />
  <img src="https://img.shields.io/badge/IATA-AHM_730_Delay_Codes-22c55e?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Tests-19%2F19_Passing-22c55e?style=for-the-badge" />
</p>

<h1 align="center">AerOps AI</h1>
<h3 align="center">Aviation Operations Intelligence Platform</h3>
<p align="center"><em>Real data. Real predictions. Real IATA standards.</em></p>

<p align="center">
  An end-to-end data science platform that ingests real US flight data (BTS), integrates live aviation weather (METAR/TAF), and predicts flight delays using gradient-boosted ML models &mdash; all served through an interactive Streamlit dashboard with proper IATA AHM 730 delay code compliance.
</p>

---

## The Problem

> Airlines lose **$25B+ annually** to flight delays. Most operations teams still rely on Excel spreadsheets and reactive decision-making. By the time a delay is identified, the cascade has already begun.

AerOps AI solves this by combining **historical flight performance data**, **live weather conditions**, and **machine learning** to:

1. **Predict delays before they happen** (ML classifier with 77% accuracy, 0.70 AUC)
2. **Identify root causes** using real IATA delay code taxonomy (66 standard codes)
3. **Monitor live conditions** via Aviation Weather Center METAR feeds + FAA airport status
4. **Surface actionable alerts** for route congestion, weather impacts, and delay cascades

---

## Architecture

```
                    +---------------------------+
                    |     DATA SOURCES          |
                    |  BTS Transtats (CSV)      |  <-- Millions of real US flights
                    |  AWC METAR API (JSON)     |  <-- Live weather, no auth
                    |  FAA Status API (JSON)    |  <-- Airport delay status
                    |  OurAirports (CSV)        |  <-- 4,553 airports worldwide
                    +------------+--------------+
                                 |
                    +------------v--------------+
                    |     INGESTION LAYER       |
                    |  bts_loader.py            |  Parse → Engineer → Map IATA codes
                    |  weather_api.py           |  Fetch → Cache (30min TTL)
                    |  faa_status.py            |  Fetch → Cache (15min TTL)
                    |  airports.py              |  Download → Filter → Load
                    +------------+--------------+
                                 |
                    +------------v--------------+
                    |     STORAGE LAYER         |
                    |  SQLite (flight_ops.db)   |
                    |  ├── flights (BTS data)   |  Indexed on date, route, airline
                    |  ├── airports (4,553)     |  IATA/ICAO lookup
                    |  ├── weather_observations |  METAR cache with TTL
                    |  ├── airport_status_cache |  FAA status cache
                    |  ├── iata_delay_codes     |  66 AHM 730 reference codes
                    |  └── predictions          |  ML prediction audit log
                    +------------+--------------+
                                 |
              +-----------+------+------+-----------+
              |           |             |           |
    +---------v---+ +-----v-----+ +----v----+ +----v--------+
    | ANALYTICS   | | ML MODEL  | | ALERTS  | | EXPORT      |
    | kpi.py      | | Gradient  | | Route   | | PDF reports |
    | OTP, delay  | | Boosting  | | Weather | | with FPDF2  |
    | rates, root | | Classifier| | Cascade | |             |
    | cause       | | Regressor | | Airport | |             |
    +------+------+ +-----+-----+ +----+----+ +------+------+
           |              |             |             |
    +------v--------------v-------------v-------------v------+
    |              STREAMLIT DASHBOARD                       |
    |  6 Interactive Tabs:                                   |
    |  [Delay Analysis] [ML Prediction] [Ops Center]        |
    |  [Airline & Fleet] [Route Analytics] [Root Cause]     |
    +--------------------------------------------------------+
```

---

## Key Features

### 1. Real Data Pipeline (Not Synthetic)
- **BTS Transtats Integration**: Ingest millions of real US domestic flight records with actual delay causes, durations, and cancellation codes
- **Live Weather**: Aviation Weather Center METAR API (no authentication required) with 30-minute cache
- **FAA Airport Status**: Real-time delay/ground-stop information for major US airports
- **Demo Mode**: Auto-generates 5,000 realistic flights matching BTS schema for instant demo

### 2. ML Delay Prediction
- **GradientBoostingClassifier**: Predicts P(delay > 15min) with 18 engineered features
- **GradientBoostingRegressor**: Estimates delay duration for high-risk flights
- **Temporal Train/Test Split**: Last 30 days held out (no data leakage)
- **Feature Engineering**: Cyclical hour/month encoding, target-encoded airports/airlines, historical delay rates
- **Model Performance**: 77% accuracy, 0.70 AUC-ROC on held-out test set

### 3. IATA Standard Compliance
- **66 real IATA AHM 730 delay codes** (not made-up categories)
- **BTS-to-IATA mapping**: CarrierDelay→96, WeatherDelay→71, NASDelay→81, SecurityDelay→85, LateAircraftDelay→93
- **Responsibility attribution**: Airline vs ATC vs Weather vs Airport vs Ground Handler

### 4. Interactive Dashboard (6 Tabs)
| Tab | What It Shows |
|-----|---------------|
| **Delay Analysis** | IATA code distribution, airline vs delay heatmap, delay duration histogram |
| **ML Prediction** | Select route/airline/time → get delay probability with feature importance breakdown |
| **Ops Control Center** | Live METAR weather cards for 20 airports, FAA delay status, AI-generated alerts |
| **Airline & Fleet** | OTP leaderboard by airline, tail number utilization, fleet performance metrics |
| **Route Analytics** | Top routes by volume, status breakdown, distance vs delay correlation |
| **Root Cause** | BTS delay cause attribution, monthly trends, airport drill-down, responsibility pie chart |

### 5. Production-Grade Engineering
- **Modular architecture**: 15+ Python modules, clean separation of concerns
- **SQLite persistence**: WAL mode, indexed queries, cached API responses
- **19 automated tests**: pytest suite covering data pipeline, IATA codes, KPIs, and ML model
- **CLI tooling**: `seed_db.py`, `ingest_bts.py`, `train_model.py` for reproducible workflows
- **Error handling**: Graceful API failures, defensive data validation, NaN-safe calculations

---

## Quick Start

### Prerequisites
- Python 3.10+
- pip

### 1. Clone and Install

```bash
git clone https://github.com/projectavish/aerops-ai.git
cd aerops-ai
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
python scripts/seed_db.py
```

This will:
- Create the SQLite database with all tables and indexes
- Download 4,553 airports from OurAirports
- Load 66 IATA AHM 730 delay codes
- Generate 5,000 demo flights (if no BTS data is available)

### 3. Train the ML Model

```bash
python scripts/train_model.py
```

Output:
```
  Accuracy  : 0.7665
  AUC-ROC   : 0.7014
  Precision : 0.3918
  Recall    : 0.2242

  Feature Importances (top 5):
  route_delay_rate          0.2925  ############################
  distance                  0.1787  #################
  dest_delay_rate           0.0934  #########
  origin_delay_rate         0.0828  ########
  airline_delay_rate        0.0721  #######
```

### 4. Launch Dashboard

```bash
streamlit run dashboard/streamlit_app.py
```

Open http://localhost:8501 in your browser.

### 5. (Optional) Load Real BTS Data

For real flight data instead of demo data:

1. Download from [BTS Transtats](https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoession_VQ=FGJ)
2. Select fields: FlightDate, Reporting_Airline, Origin, Dest, DepDelay, ArrDelay, etc.
3. Place CSV in `data/bts/`
4. Run:

```bash
python scripts/ingest_bts.py data/bts/*.csv
python scripts/train_model.py  # Retrain on real data
```

### 6. Run Tests

```bash
pytest tests/ -v
```

```
tests/test_iata_codes.py      5 passed
tests/test_bts_loader.py      4 passed
tests/test_kpi.py              6 passed
tests/test_delay_predictor.py  4 passed
========================= 19 passed in 7.09s =========================
```

---

## Project Structure

```
aerops-ai/
├── aerops/                          # Core Python package
│   ├── config.py                    # Central configuration
│   ├── db.py                        # SQLite schema + connection management
│   ├── data/
│   │   ├── bts_loader.py            # BTS CSV → SQLite pipeline
│   │   ├── weather_api.py           # AWC METAR API + cache
│   │   ├── faa_status.py            # FAA airport status API + cache
│   │   ├── airports.py              # OurAirports loader (4,553 airports)
│   │   ├── iata_codes.py            # IATA AHM 730 delay code reference
│   │   └── demo_generator.py        # Realistic demo data generator
│   ├── models/
│   │   └── delay_predictor.py       # GradientBoosting classifier + regressor
│   └── analytics/
│       ├── kpi.py                   # OTP, delay rate, metric calculations
│       └── alerts.py                # Data-driven operational alerts
├── dashboard/
│   ├── streamlit_app.py             # Main orchestrator (~120 lines)
│   ├── styles.py                    # Cockpit dark theme CSS
│   └── components/                  # Modular UI components
│       ├── sidebar.py               # Filter controls
│       ├── header.py                # KPI cards + trend charts
│       ├── delay_tab.py             # Delay analysis
│       ├── prediction_tab.py        # ML prediction interface
│       ├── ops_center_tab.py        # Live weather + FAA status
│       ├── crew_tab.py              # Airline & fleet performance
│       ├── route_tab.py             # Route analytics
│       ├── root_cause_tab.py        # BTS delay cause deep-dive
│       └── export.py                # PDF report generation
├── scripts/
│   ├── seed_db.py                   # Initialize DB + reference data
│   ├── ingest_bts.py               # Import BTS CSV files
│   └── train_model.py              # Train delay prediction model
├── tests/                           # pytest suite (19 tests)
├── data/
│   ├── iata_delay_codes.json        # 66 IATA AHM 730 codes
│   └── airports.csv                 # OurAirports reference (auto-downloaded)
└── models/
    └── delay_model.joblib           # Trained ML model (auto-generated)
```

---

## Technical Decisions

### Why SQLite over PostgreSQL?
Zero-config, single-file, handles 3M+ rows with proper indexing. Perfect for a portable analytics platform. The schema is designed to migrate to PostgreSQL with minimal changes.

### Why GradientBoosting over Deep Learning?
Flight delays are a tabular prediction problem. GradientBoosting consistently outperforms neural networks on tabular data (see [Grinsztajn et al. 2022](https://arxiv.org/abs/2207.08815)). It also trains in <3 seconds and serves predictions instantly.

### Why Temporal Train/Test Split?
Random splits cause **data leakage** in time-series problems. A flight's delay is correlated with nearby flights. Using the last 30 days as holdout ensures honest evaluation.

### Why BTS Data?
The Bureau of Transportation Statistics publishes **every US domestic flight** since 1987 with actual delay causes. This is the gold standard for aviation analytics research.

### Why IATA AHM 730 Codes?
The industry standard. Using real codes (71=Weather, 81=ATC, 93=Aircraft Rotation) instead of made-up labels demonstrates domain expertise and makes the platform interoperable with airline systems.

---

## Data Model

### Flights Table (BTS Schema)

| Column | Type | Description |
|--------|------|-------------|
| `flight_date` | DATE | Date of operation |
| `airline` | TEXT | IATA 2-letter airline code (AA, DL, UA...) |
| `origin` / `dest` | TEXT | IATA 3-letter airport codes |
| `arr_delay_minutes` | REAL | Arrival delay in minutes |
| `is_delayed` | INT | 1 if arr_delay > 15min (BTS standard) |
| `carrier_delay` | REAL | Minutes attributed to carrier |
| `weather_delay` | REAL | Minutes attributed to weather |
| `nas_delay` | REAL | Minutes attributed to NAS/ATC |
| `security_delay` | REAL | Minutes attributed to security |
| `late_aircraft_delay` | REAL | Minutes from late inbound aircraft |
| `iata_delay_code` | TEXT | Mapped IATA AHM 730 code |
| `iata_delay_category` | TEXT | Weather, Reactionary, ATC/Airport |

### ML Feature Set (18 features)

| Category | Features |
|----------|----------|
| Temporal | `dep_hour`, `day_of_week`, `month`, `is_weekend` |
| Flight | `distance`, `crs_elapsed_time` |
| Historical | `route_delay_rate`, `origin_delay_rate`, `dest_delay_rate`, `airline_delay_rate` |
| Cyclical | `dep_hour_sin/cos`, `month_sin/cos` |
| Weather | `origin_visibility`, `origin_wind_speed`, `origin_ceiling`, `origin_flight_cat` |

---

## API Integrations

| Source | Endpoint | Auth | Data |
|--------|----------|------|------|
| **AWC METAR** | `aviationweather.gov/api/data/metar` | None | Live weather observations |
| **FAA Status** | `soa.smext.faa.gov/asws/api/airport/status` | None | Airport delay status |
| **OurAirports** | `davidmegginson.github.io/ourairports-data` | None | 4,553 airports with ICAO/IATA |
| **BTS Transtats** | `transtats.bts.gov` | None | Historical on-time performance |

---

## Skills Demonstrated

This project showcases a complete **data science + engineering** skill set:

| Skill Area | Implementation |
|------------|---------------|
| **Data Engineering** | ETL pipeline (BTS CSV → SQLite), API integration, schema design, indexing |
| **Data Analysis** | OTP calculations, delay rate analysis, root cause attribution, trend identification |
| **Machine Learning** | Feature engineering, GradientBoosting, temporal splits, model evaluation (AUC/precision/recall) |
| **Data Visualization** | 15+ interactive Plotly charts, heatmaps, gauges, stacked bars, scatter with trendlines |
| **Software Engineering** | Modular architecture, 19 automated tests, CLI tooling, error handling |
| **Domain Expertise** | IATA AHM 730 compliance, BTS data knowledge, METAR/TAF understanding, aviation KPIs |
| **Product Thinking** | Plug-and-play setup, demo mode, graceful API failures, PDF export for stakeholders |

---

## Roadmap

- [ ] Historical weather correlation (match METAR to past flights for training)
- [ ] NOTAM feed integration for proactive risk scoring
- [ ] Slack/Teams webhook alerts for critical delays
- [ ] Multi-airline tenant support
- [ ] Dockerized deployment with health checks
- [ ] Prophet/ARIMA for seasonal delay forecasting

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| Dashboard | Streamlit 1.28+ |
| Visualization | Plotly 5.15+ |
| ML | scikit-learn (GradientBoosting) |
| Database | SQLite (WAL mode) |
| Data Processing | Pandas, NumPy |
| PDF Export | FPDF2 |
| Testing | pytest |
| APIs | requests (AWC, FAA) |

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Built by <a href="https://github.com/projectavish">Avish</a></strong><br>
  <em>Data Scientist | Aviation Operations Analytics | Ireland</em>
</p>
