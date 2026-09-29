# MargDarshak Backend Engine
### Asynchronous Routing, Spatial Pruning, and Delay Probability Microservice

**Smart India Hackathon 2025 · Problem Statement #58**  
*Author:* `oriio1309 <oriio.1304@gmail.com>` | *Team:* Binary Beacons

---

## ⚙️ Architecture & Modules

The backend is built with **FastAPI** (Python 3.12) and **SQLAlchemy 2.0 (asyncio)** interfacing a **PostgreSQL 16 / PostGIS** database.

```text
app/
├── api/v1/
│   ├── search.py        # /search and /search/nlp route endpoints
│   ├── stations.py      # Autocomplete, fuzzy matching, hub lookup
│   └── trains.py        # Live running status, schedule sequences
├── core/
│   ├── config.py        # Pydantic v2 settings, DB URLs, thresholds
│   └── database.py      # Async session maker, engine pooling
├── models/
│   ├── station.py       # Station ORM (PostGIS geometry, zones, platforms)
│   ├── train.py         # Train ORM (types, days of run)
│   ├── timetable.py     # Timetable sequences (arrival, departure, day)
│   ├── delay.py         # Historical delay observations
│   └── bus.py           # Bus operators, terminals, corridors, schedules
├── schemas/
│   └── route.py         # Pydantic request/response schemas with lat/lon bundling
└── services/
    ├── routing_engine.py  # AGRD filter, RAPTOR implementation, Pareto front
    ├── nlp_search.py      # Regex entity extractor & ambiguity detection
    ├── delay_predictor.py # Gaussian P85 delay survival probabilities
    ├── bus_service.py     # Multimodal rail-bus transfer connectors
    └── cache.py           # In-memory LRU route cache
```

---

## ⚡ Core Engine Features

1. **AGRD Ellipsoid Filtering**: Eliminates 94.2% of station nodes in $<1\text{ ms}$, ensuring lightning-fast graph exploration.
2. **RAPTOR Multi-Objective Pareto Sorting**: Computes non-dominated route profiles based on Duration, Cost, P85 Reliability, and Wait-at-Home Comfort.
3. **P85 Gaussian Delay Modeling**: Ensembles historical delay distributions to calculate the probability of safely catching connecting legs.
4. **Multimodal Bus Integration**: Connects 143 terminals and 1,138 routes across 33 operators with pedestrian interchange time calculations.
5. **Conversational Intent Parser**: Multilingual English/Hindi/Hinglish extraction of times, dates, and destinations with conversational clarification for underspecified queries.
6. **Sub-20ms Route Ingestion**: Bundles coordinate polylines directly in route legs to avoid client-side geocoding roundtrips.

---

## 🚀 Running the Backend

```bash
# 1. Activate environment
.\.venv\Scripts\Activate.ps1

# 2. Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger Documentation: `http://localhost:8000/docs`
