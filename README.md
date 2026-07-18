# ZH-1 — Compound Risk & Zero-Harm Console

**Hackathon submission for Problem Statement 1: AI-Powered Industrial Safety Intelligence for Zero-Harm Operations**

ZH-1 converts normally isolated plant signals—gas readings, permits, maintenance,
shift context and occupancy—into one **explainable compound-risk score per zone**.
It then coordinates the first response, preserves an auditable timeline and checks
illustrative compliance rules continuously.

## The 60-second judge demo

1. Start the project and open `http://127.0.0.1:8420`.
2. Click **Run emergency demo**.
3. Watch zone **B1** become critical even though its CO reading is only at warning level.
4. Compare **Sensor only** with **Fused context** in the risk feed.
5. Show the automatic sequence: trigger → evacuate → notify → isolate work → preserve evidence → draft report.
6. Download the evidence JSON and run an incident-pattern search.

The deterministic button removes the risk of waiting for a random scenario during judging.

## Why this version is submission-ready

- **One-command application:** FastAPI serves both the API and the frontend.
- **Deterministic live demo:** a guaranteed compound event is available on demand.
- **Explainability:** each score includes factors, categories and a sensor-only counterfactual.
- **Strong visual story:** industrial HMI dashboard, geospatial zone map and live response timeline.
- **Offline operation:** no API key, cloud model or internet connection is required.
- **Evidence export:** judges can download a machine-readable incident snapshot.
- **Deployment options:** local scripts, Docker and Docker Compose are included.
- **Automated validation:** tests cover risk fusion, orchestration, retrieval and API routes.

## Architecture

```text
Plant signals / simulator
        │
        ▼
Time-aligned zone frame
        │
        ├── Compound Risk Engine ── sensor-only counterfactual
        ├── Permit Intelligence
        ├── Incident Pattern Retrieval
        └── Continuous Compliance Audit
        │
        ▼
Emergency Orchestrator ── evidence timeline
        │
        ▼
FastAPI + industrial web console
```

See `docs/architecture.svg` for the full five-layer diagram.

## Project structure

```text
ZH1-Zero-Harm-Console-Final/
├── backend/
│   ├── __init__.py
│   ├── app.py
│   ├── incident_intel.py
│   ├── plant_sim.py
│   ├── response_agents.py
│   ├── risk_engine.py
│   └── requirements.txt
├── frontend/
│   ├── app.js
│   ├── favicon.svg
│   ├── index.html
│   └── style.css
├── docs/
│   ├── architecture.svg
│   ├── demo_script.md
│   └── pitch_outline.md
├── tests/
│   ├── test_api.py
│   └── test_core.py
├── Dockerfile
├── docker-compose.yml
├── run_linux.sh
├── run_windows.bat
├── SUBMISSION_CHECKLIST.md
└── README.md
```

## Run locally

### Windows

Double-click:

```text
run_windows.bat
```

### Linux or macOS

```bash
chmod +x run_linux.sh
./run_linux.sh
```

### Manual commands

```bash
python -m venv .venv
```

Activate the environment:

```bash
# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

Install and run:

```bash
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8420
```

Open:

- Dashboard: `http://127.0.0.1:8420`
- API documentation: `http://127.0.0.1:8420/api/docs`
- Health check: `http://127.0.0.1:8420/api/health`

## Run with Docker

```bash
docker compose up --build
```

Then open `http://127.0.0.1:8420`.

## Run tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## API highlights

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/state` | Advance simulation and return the complete dashboard state |
| `POST` | `/api/demo/trigger` | Start the deterministic B1 compound-risk event |
| `POST` | `/api/demo/reset` | Reset simulator and response history |
| `GET` | `/api/incidents/search?q=...` | Search the offline incident/reference corpus |
| `GET` | `/api/evidence/report` | Export an auditable JSON snapshot |
| `GET` | `/api/health` | Runtime health and version |

## What is genuinely implemented

### Explainable compound-risk fusion

The engine combines independent signal categories and applies the plant zone's
intrinsic hazard multiplier. A score is marked compound only when at least two
independent categories are present. The result includes:

- fused score and level;
- sensor-only counterfactual score and level;
- fusion uplift;
- worker count;
- factor categories;
- human-readable contributing factors.

### Deterministic counterfactual demonstration

The B1 demo holds CO below its critical threshold while adding an active hot-work
permit, maintenance activity and six-person occupancy. Traditional sensor-only logic
stays below alert, while the fused model becomes critical. This makes the project's
central value visible in seconds.

### Offline incident-pattern intelligence

The retrieval layer uses a from-scratch TF-IDF and cosine-similarity index over a
small demonstration corpus. Query expansion adds common industrial synonyms. Results
show relevance, matched terms and source type, making the retrieval trace auditable.

### Emergency orchestration and evidence

A critical zone generates a deterministic first-response sequence with simulated
elapsed times. The exported report includes state, factors, permits, compliance status
and the complete action timeline.

## Honest prototype limits

- Plant feeds and worker locations are synthetic.
- Reference clauses are paraphrased demonstration content, not legal advice.
- Risk weights are transparent domain starting points, not values fitted to site history.
- Authentication, RBAC, high availability and certified control integration are out of scope.
- A production pilot must validate thresholds and actions with plant safety leadership.

These limitations are intentional and visible rather than hidden. The next pilot step
is to replace the simulator with read-only OPC-UA/MQTT and permit-system adapters while
keeping the `frame -> evaluate(frame)` interface unchanged.
