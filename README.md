#AI-Powered Industrial Safety Intelligence for Zero-Harm
Operations

**Hackathon submission for Problem Statement 1: AI-Powered Industrial Safety Intelligence for Zero-Harm Operations**

ZH-1 converts normally isolated plant signals—gas readings, work permits, maintenance activity, shift context and worker occupancy—into one **explainable compound-risk score per plant zone**.

When a zone becomes critical, the platform coordinates the first response, creates an auditable action timeline, checks illustrative compliance rules and exports a machine-readable evidence snapshot.

---

## Why this submission stands out

- **One-command application** — FastAPI serves both the API and the frontend.
- **Deterministic live demo** — judges can trigger a guaranteed B1 compound-risk event instantly.
- **Explainable risk fusion** — every score contains factors, categories and a sensor-only counterfactual.
- **Strong visual story** — industrial HMI dashboard, zone heatmap, response timeline and live KPIs.
- **Offline operation** — no API key, cloud model or internet connection is required.
- **Evidence export** — incident state and response history can be downloaded as JSON.
- **Deployment-ready packaging** — local scripts, Docker and Docker Compose are included.
- **Automated validation** — tests cover risk fusion, orchestration, retrieval and API routes.

---

## Demo

1. Start the application.
2. Open `http://127.0.0.1:8420`.
3. Click **Run Emergency Demo**.
4. Show zone **B1 — Gas Collection Main** turning critical.
5. Compare the **Sensor-only score**, **Fused-context score** and **Fusion uplift**.
6. Show the contributing factors: elevated CO, active hot-work permit, maintenance in progress, six workers exposed and shift-changeover risk when active.
7. Show the Emergency Response Orchestrator timeline.
8. Show the compliance gap.
9. Search the incident corpus for `hot work near elevated gas`.
10. Click **Download Evidence JSON**.

### Core demonstration message

> The gas reading remains below the critical sensor threshold, so a traditional sensor-only system does not declare a critical emergency. ZH-1 combines the reading with hazardous work, maintenance and worker exposure, detects the compound condition and starts a coordinated response.

---

## Architecture

```text
Plant signals / simulator
        │
        ▼
Time-aligned zone frame
        │
        ├── Compound Risk Engine
        │      └── Sensor-only counterfactual
        ├── Permit Intelligence
        ├── Incident Pattern Retrieval
        └── Continuous Compliance Audit
        │
        ▼
Emergency Response Orchestrator
        │
        ├── Evacuation
        ├── Notification
        ├── Work isolation
        ├── Evidence preservation
        └── Preliminary report timeline
        │
        ▼
FastAPI API + industrial web console
```

See `docs/architecture.svg` for the complete five-layer diagram.

---

## Project structure

```text
ZH1-Zero-Harm-Console-Hackathon-Final/
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
├── requirements-dev.txt
├── run_linux.sh
├── run_windows.bat
├── SUBMISSION_CHECKLIST.md
└── README.md
```

---

## Quick start

### Windows

Extract the ZIP and double-click:

```text
run_windows.bat
```

The script creates a virtual environment, installs dependencies and starts the application.

### Linux or macOS

```bash
chmod +x run_linux.sh
./run_linux.sh
```

### Open the application

- Dashboard: `http://127.0.0.1:8420`
- API documentation: `http://127.0.0.1:8420/api/docs`
- Health check: `http://127.0.0.1:8420/api/health`

Keep the terminal window open while the application is running. Press `Ctrl+C` to stop it.

---

## Manual installation

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate
```

Install dependencies and start the server:

```bash
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8420
```

Open `http://127.0.0.1:8420`.

---

## Run with Docker

```bash
docker compose up --build
```

Then open `http://127.0.0.1:8420`.

Stop the containers with:

```bash
docker compose down
```

---

## Run tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The automated test suite validates:

- compound-risk scoring;
- sensor-only counterfactual scoring;
- compound-category detection;
- deterministic emergency orchestration;
- incident retrieval;
- API health, state, demo and export routes.

---

## API highlights

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/state` | Advance the simulation and return the complete dashboard state |
| `POST` | `/api/demo/trigger` | Start the deterministic B1 compound-risk event |
| `POST` | `/api/demo/reset` | Reset the simulator and response history |
| `GET` | `/api/incidents/search?q=...` | Search the offline incident/reference corpus |
| `GET` | `/api/evidence/report` | Export an auditable JSON incident snapshot |
| `GET` | `/api/health` | Return runtime health, mode and version |

Interactive API documentation is available at `http://127.0.0.1:8420/api/docs`.

---

## What is genuinely implemented

### 1. Explainable compound-risk fusion

For each plant zone, the engine combines independent categories of evidence:

- sensor conditions;
- active work permits;
- maintenance activity;
- shift-change context;
- worker occupancy;
- intrinsic zone hazard.

The result includes:

- fused score and severity level;
- sensor-only counterfactual score and level;
- fusion uplift;
- worker count;
- active factor categories;
- human-readable contributing factors;
- compound-event flag.

A score is marked **compound** only when at least two independent factor categories are present.

### 2. Sensor-only counterfactual

ZH-1 calculates what a conventional sensor-only system would have concluded using the same frame.

```text
Sensor-only score  → isolated sensor interpretation
Fused score        → sensor + operational context
Fusion uplift      → value added by context
```

That comparison is the central proof of value.

### 3. Deterministic B1 emergency scenario

The judge demo creates a controlled event in **B1 — Gas Collection Main**:

- CO is elevated but remains below its critical threshold;
- a hot-work permit is active;
- maintenance is in progress;
- six workers are present;
- shift-changeover risk may also apply.

The isolated sensor score remains below critical, while the fused score becomes critical.

Because the scenario is deterministic, the strongest part of the solution can be demonstrated immediately without waiting for a random event.

### 4. Offline incident-pattern intelligence

The retrieval layer uses a from-scratch TF-IDF and cosine-similarity index over a compact demonstration corpus containing near-miss narratives, incident narratives and paraphrased safety-reference clauses.

Query expansion adds common industrial synonyms. Results include relevance score, matched terms, document type, source label and zone where applicable.

No external LLM or cloud search service is used.

### 5. Emergency response orchestration

When a zone becomes critical, the orchestrator creates a timestamped first-response sequence:

1. Detect and register the critical event.
2. Initiate evacuation.
3. Notify response teams and safety leadership.
4. Place hazardous work on hold.
5. Preserve sensor and CCTV evidence.
6. Generate a preliminary incident timeline.

Duplicate actions are prevented while the same incident remains active.

### 6. Continuous compliance audit

The compliance agent continuously checks illustrative rules such as:

- hot work during elevated gas conditions;
- permit-record cross-referencing;
- existence of an auditable escalation pathway.

The references are paraphrased demonstration content and are not legal advice.

### 7. Evidence export

The downloadable JSON report contains:

- simulation tick and operating mode;
- shift and shift-change context;
- full zone-risk scores;
- sensor-only counterfactuals;
- active permits;
- maintenance state;
- worker locations;
- compliance results;
- emergency-response actions;
- incident identifiers and timestamps;
- prototype disclaimer.

---

## Risk model

The model is deliberately transparent rather than a black box.

| Condition | Illustrative contribution |
|---|---:|
| Gas warning threshold crossed | 18 |
| Gas critical threshold crossed | 42 |
| Active hot-work permit | 15 |
| Active confined-space permit | 20 |
| Maintenance in progress | 12 |
| Shift changeover | Up to 10 |
| Additional personnel in a hazardous zone | 8 per worker beyond the baseline |

The raw score is adjusted using the zone's intrinsic hazard multiplier.

| Score | Level |
|---:|---|
| Below 27.5 | Normal |
| 27.5–54.9 | Elevated |
| 55–79.9 | Alert |
| 80–100 | Critical |

These weights are explainable prototype values and must be calibrated against real site history before production use.

---

## Technology stack

- **Backend:** Python and FastAPI
- **Frontend:** HTML, CSS and vanilla JavaScript
- **Server:** Uvicorn
- **Retrieval:** custom TF-IDF and cosine similarity
- **Testing:** Pytest
- **Packaging:** Docker and Docker Compose
- **Operation:** fully offline after dependency installation

---

## Troubleshooting

### `python` is not recognized

Install Python 3.10 or newer and enable **Add Python to PATH** during installation.

```bash
python --version
```

### Port 8420 is already in use

```bash
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8421
```

Then open `http://127.0.0.1:8421`.

### Dashboard shows disconnected

Confirm that the Uvicorn terminal is still open and visit:

```text
http://127.0.0.1:8420/api/health
```

A healthy response should report `"status": "ok"`.

### Windows blocks the batch file

Open Command Prompt in the extracted folder and run:

```bat
run_windows.bat
```

Alternatively, use the manual installation steps above.

---

## Honest prototype limitations

- Plant feeds, permits and worker locations are synthetic.
- Reference clauses are paraphrased demonstration content, not legal advice.
- Risk weights are transparent domain starting points, not values fitted to site history.
- Authentication, RBAC, high availability and certified control integration are outside the prototype scope.
- The platform does not directly control safety-critical plant equipment.
- A production pilot must validate thresholds, actions and escalation rules with plant safety leadership.

These limitations are visible by design rather than hidden.

---

## Path to a production pilot

1. Replace the simulator with read-only OPC-UA, MQTT and permit-system adapters.
2. Replay historical incidents and near misses through the engine.
3. Calibrate weights against site-specific outcomes.
4. Add authentication, RBAC and immutable audit storage.
5. Integrate approved notification and work-isolation workflows.
6. Validate every action with plant operations and safety leadership.
7. Run in shadow mode before enabling operational recommendations.

The core interface remains:

```text
time-aligned plant frame
        ↓
evaluate(frame)
        ↓
explainable zone risks and actions
```

---

## Suggested presentation line

> ZH-1 does not replace existing sensors. It connects sensor readings with the operational context that determines whether a condition is truly dangerous.

---

## Disclaimer

ZH-1 is a hackathon prototype for decision-support demonstration. It is not a certified safety system and must not be used as the sole basis for real-world emergency or plant-control decisions.

