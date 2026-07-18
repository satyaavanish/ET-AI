"""FastAPI entry point for the Zero-Harm Console.

Run from the project root with:
    uvicorn backend.app:app --host 0.0.0.0 --port 8420

The API also serves the frontend, so the complete demo is available at
http://127.0.0.1:8420 after one command.
"""

from __future__ import annotations

import threading
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .incident_intel import incident_index
from .plant_sim import PlantSimulator
from .response_agents import ComplianceAuditor, EmergencyOrchestrator
from .risk_engine import CompoundRiskEngine

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(
    title="ZH-1 Zero-Harm Industrial Safety Intelligence",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8420",
        "http://localhost:8420",
        "http://127.0.0.1:8600",
        "http://localhost:8600",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

simulator = PlantSimulator(seed=7, auto_scenarios=False)
risk_engine = CompoundRiskEngine()
orchestrator = EmergencyOrchestrator()
auditor = ComplianceAuditor()
state_lock = threading.RLock()
_last_frame: dict[str, Any] | None = None
_last_risks = None


def _metrics(frame: dict, risks) -> dict:
    critical = [risk for risk in risks if risk.level == "critical"]
    alerts = [risk for risk in risks if risk.level in {"alert", "critical"}]
    compound = [risk for risk in risks if risk_engine.is_compound(risk)]
    at_risk_zones = {risk.zone_id for risk in alerts}
    people_at_risk = sum(1 for worker in frame["workers"] if worker["zone_id"] in at_risk_zones)
    top = risks[0] if risks else None
    return {
        "max_fused_score": top.score if top else 0,
        "max_sensor_only_score": top.sensor_only_score if top else 0,
        "fusion_uplift": top.fusion_uplift if top else 0,
        "critical_zones": len(critical),
        "alert_zones": len(alerts),
        "compound_zones": len(compound),
        "people_in_alert_zones": people_at_risk,
        "automated_actions": len(orchestrator.log),
    }


def _advance() -> tuple[dict, list]:
    global _last_frame, _last_risks
    with state_lock:
        _last_frame = simulator.tick()
        _last_risks = risk_engine.evaluate(_last_frame)
        for zone_risk in _last_risks:
            orchestrator.handle(zone_risk)
        return _last_frame, _last_risks


def _payload(frame: dict, risks: list) -> dict:
    response_log = orchestrator.recent(30)
    return {
        "tick": frame["tick"],
        "shift": frame["shift"],
        "shift_changeover": frame["shift_changeover"],
        "scenario": frame["scenario"],
        "zones": frame["zones"],
        "risks": [
            asdict(risk) | {"is_compound": risk_engine.is_compound(risk)}
            for risk in risks
        ],
        "permits": frame["permits"],
        "maintenance": frame["maintenance"],
        "workers": frame["workers"],
        "orchestrator_log": response_log,
        "compliance": auditor.audit(frame, risks, response_log),
        "metrics": _metrics(frame, risks),
        "methodology": {
            "risk_model": "Explainable weighted-factor fusion",
            "retrieval": incident_index.stats(),
            "external_api_required": False,
            "data_mode": "Synthetic plant simulator",
        },
    }


@app.get("/api/state")
def get_state():
    frame, risks = _advance()
    return _payload(frame, risks)


@app.post("/api/demo/trigger")
def trigger_demo():
    with state_lock:
        scenario = simulator.trigger_demo_scenario(duration_ticks=10)
        frame, risks = _advance()
    return {"message": "Compound-risk demonstration started", "scenario": scenario, "state": _payload(frame, risks)}


@app.post("/api/demo/reset")
def reset_demo():
    global _last_frame, _last_risks
    with state_lock:
        simulator.reset()
        orchestrator.reset()
        _last_frame = None
        _last_risks = None
        frame, risks = _advance()
    return {"message": "Simulation reset", "state": _payload(frame, risks)}


@app.get("/api/incidents/search")
def search_incidents(q: str = Query(..., min_length=2, max_length=160)):
    return {
        "query": q,
        "results": incident_index.search(q),
        "index": incident_index.stats(),
        "disclaimer": "Demo corpus and paraphrased reference clauses; not legal advice.",
    }


@app.get("/api/evidence/report")
def evidence_report():
    global _last_frame, _last_risks
    with state_lock:
        if _last_frame is None or _last_risks is None:
            _last_frame, _last_risks = _advance()
        payload = _payload(_last_frame, _last_risks)
    return {
        "report_type": "ZH-1 compound-risk evidence snapshot",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "prototype_disclaimer": (
            "Synthetic demonstration data and illustrative compliance rules. "
            "Not for live operational control without validation and governance."
        ),
        "state": payload,
        "response_evidence": orchestrator.evidence_summary(),
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "version": app.version,
        "tick": simulator.tick_count,
        "frontend_served": FRONTEND_DIR.exists(),
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(FRONTEND_DIR / "favicon.svg")


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
