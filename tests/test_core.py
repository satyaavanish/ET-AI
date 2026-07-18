from backend.incident_intel import incident_index
from backend.plant_sim import PlantSimulator
from backend.response_agents import EmergencyOrchestrator
from backend.risk_engine import CompoundRiskEngine


def test_demo_scenario_proves_fusion_value():
    simulator = PlantSimulator(seed=7)
    simulator.trigger_demo_scenario()
    frame = simulator.tick()
    engine = CompoundRiskEngine()
    risks = engine.evaluate(frame)
    b1 = next(risk for risk in risks if risk.zone_id == "B1")

    assert b1.level == "critical"
    assert b1.sensor_only_level in {"normal", "elevated"}
    assert b1.score > b1.sensor_only_score
    assert engine.is_compound(b1)
    assert {"sensor", "permit", "maintenance", "occupancy"}.issubset(set(b1.factor_categories))


def test_orchestrator_creates_auditable_sequence():
    simulator = PlantSimulator(seed=7)
    simulator.trigger_demo_scenario()
    frame = simulator.tick()
    engine = CompoundRiskEngine()
    orchestrator = EmergencyOrchestrator()
    for risk in engine.evaluate(frame):
        orchestrator.handle(risk)

    actions = [entry["action"] for entry in orchestrator.log]
    assert actions == [
        "TRIGGER",
        "EVACUATE",
        "NOTIFY",
        "ISOLATE_WORK",
        "PRESERVE_EVIDENCE",
        "DRAFT_REPORT",
    ]


def test_incident_retrieval_is_deterministic_and_relevant():
    results = incident_index.search("hot work elevated gas")
    assert results
    assert any("hot" in result["matched_terms"] or "gas" in result["matched_terms"] for result in results)
    assert incident_index.stats()["external_api"] is False
