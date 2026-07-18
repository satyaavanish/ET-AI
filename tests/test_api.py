from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_health_and_frontend():
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    frontend = client.get("/")
    assert frontend.status_code == 200
    assert "Zero-Harm" in frontend.text


def test_trigger_demo_and_evidence_report():
    client.post("/api/demo/reset")
    response = client.post("/api/demo/trigger")
    assert response.status_code == 200
    state = response.json()["state"]
    b1 = next(risk for risk in state["risks"] if risk["zone_id"] == "B1")
    assert b1["level"] == "critical"
    assert b1["sensor_only_score"] < b1["score"]
    assert state["orchestrator_log"]

    evidence = client.get("/api/evidence/report")
    assert evidence.status_code == 200
    assert evidence.json()["response_evidence"]["actions_logged"] >= 6


def test_incident_search_validation():
    response = client.get("/api/incidents/search", params={"q": "confined space shift"})
    assert response.status_code == 200
    assert response.json()["results"]
