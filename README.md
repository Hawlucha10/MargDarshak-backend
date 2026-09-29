# MargDarshak Backend Engine
### Autonomous Multi-Modal Routing, Spatial Pruning, and Delay Probability Microservice

**Architect & Lead Engineer:** Ojas Nagar (`oriio1309` · oriio.1304@gmail.com)  
**Repository:** [Hawlucha10/MargDarshak-backend](https://github.com/Hawlucha10/MargDarshak-backend)  
**CI/CD Pipeline Status:** ![CI/CD Status](https://img.shields.io/badge/CI%2FCD%20Pipeline-Passing%20(40%2F40)-brightgreen) ![Python 3.11](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue) ![License](https://img.shields.io/badge/License-MIT-purple)

---

## 🎯 System Overview

The **MargDarshak Backend** is an asynchronous, high-throughput microservice built with **FastAPI**, **SQLAlchemy 2.0 (asyncio)**, **PostgreSQL 16 / PostGIS**, and **Redis**. It powers real-time multi-modal route planning across the Indian Railways national network (9,022 stations, 22,000 trains, 161,128 timetable stop entries) combined with 33 intercity bus operators.

---

## 🛠️ Architecture & Modules

```text
app/
├── api/v1/
│   ├── search.py               # /search and /search/nlp multi-hop route endpoints
│   ├── stations.py             # Autocomplete, fuzzy matching, hub lookup
│   ├── trains.py               # Live running status, schedule sequences
│   └── availability.py         # Multi-class seat availability & quota arbitrage
├── core/
│   ├── agrd.py                 # Adaptive Geometric Route Deflection (spatial pruning)
│   ├── raptor.py               # Round-Based Public Transit Routing (RAPTOR)
│   ├── pareto.py               # Multi-objective Pareto frontier ranking
│   ├── reliability.py          # Gaussian joint connection survival probability
│   └── demand_buffer.py        # Festival/demand adaptive buffer scaling
├── db/
│   ├── postgres.py             # Async connection pool (with NullPool testing isolation)
│   ├── redis_client.py         # Two-tier cache client (60s telemetry, 15m route cache)
│   └── models.py               # SQLAlchemy PostGIS spatial ORM models
├── ml/
│   ├── delay_predictor.py      # Tri-model ensemble (XGBoost + LightGBM + CatBoost)
│   └── models/                 # Pretrained .joblib model artifacts & junction metrics
├── schemas/
│   ├── route.py                # Pydantic schemas for multi-modal legs and polylines
│   ├── station.py              # Station schemas and autocomplete items
│   ├── train.py                # Live telemetry and schedule response schemas
│   └── availability.py         # PRS seat availability & quota arbitrage tips
└── services/
    ├── gateway.py              # Pluggable RailwayGateway abstraction layer
    ├── cris_simulator.py       # High-fidelity IR Digital Twin (WTT, PRS, RTIS)
    ├── production_cris.py      # Real-world IR RapidAPI / CRIS production adapter
    ├── live_train_service.py   # Telemetry service wrapper
    ├── station_service.py      # In-memory station search index with offline fallback
    ├── bus_service.py          # Multimodal rail-to-bus transfer bridging
    └── nlp_search.py           # Multilingual English/Hindi intent extractor
```

---

## 🔬 Core Engineering Innovations

1. **Adaptive Geometric Route Deflection (AGRD)**:
   Filters out **94.2% of irrelevant stations in $<1\text{ ms}$** using a focal ellipsoidal spatial filter:
   $$\mathcal{E} = \left\{ x \in \mathbb{R}^2 \;\middle|\; d(S_{\text{origin}}, x) + d(x, S_{\text{dest}}) \le \lambda \cdot d(S_{\text{origin}}, S_{\text{dest}}) \right\}$$
2. **Round-Based Public Transit Routing (RAPTOR)**:
   Runs multi-label Pareto dynamic programming across 4 dimensions: Duration, Cost, P85 Reliability, and Comfort.
3. **Tri-Model ML Stacking Delay Prediction**:
   Ensembles XGBoost, LightGBM, and CatBoost with a Level-2 regularized meta-learner (`Meta-AUC = 0.931`) trained on 100,000+ real-world historical records.
4. **P85 Quantile Safety Buffer & Gaussian Joint Reliability**:
   Calculates mathematical survival probability $\Phi(z)$ that a passenger safely makes an intermediate connection.
5. **CRIS PRS Multi-Quota Arbitrage**:
   Scans originating stations to bypass PQWL/RLWL bottlenecks with General Quota (GNWL) seats.
6. **Sub-20ms Response Latency**:
   Bundled geographic coordinates on the server yield an **860x speedup** (from 16,400ms down to 19ms).

---

## 🚀 Setup & Execution

### 1. Local Python Environment
```bash
# Clone and enter directory
git clone https://github.com/Hawlucha10/MargDarshak-backend.git
cd MargDarshak-backend

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1       # Windows PowerShell
# source .venv/bin/activate        # Linux / macOS

# Install dependencies
pip install -r requirements.txt

# Run full automated test suite (40 Tests)
pytest -v

# Start FastAPI development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation live at: **`http://localhost:8000/docs`**

---

### 2. Docker & Kubernetes Deployment

```bash
# Build production Docker image
docker build -t margdarshak-api:latest .

# Deploy via Docker Compose (PostGIS, Redis, API)
docker compose up -d

# Validate Kubernetes manifests
kubectl apply -f k8s/ --dry-run=client
```

---

## 🧪 CI/CD & Automated Verification

- **Automated Test Suite**: 40/40 tests passing in 9.6s.
- **Ruff Linter**: Zero errors (`ruff check app/ tests/`).
- **Docker Container Build**: Verified in GitHub Actions.
- **K8s Manifests**: Validated in GitHub Actions.

---

## 📜 Intellectual Property & Authorship

- **Project**: MargDarshak Backend Microservice
- **Author & Lead Architect**: Ojas Nagar (`oriio1309` · oriio.1304@gmail.com)
- **Pitched At**: Smart India Hackathon (SIH 2026) · Team `potato_1`
- **License**: MIT License
