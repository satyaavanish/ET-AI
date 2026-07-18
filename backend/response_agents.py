"""Emergency response and continuous-compliance agents."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Dict, List

from .incident_intel import CORPUS


class EmergencyOrchestrator:
    def __init__(self):
        self.log: List[Dict[str, Any]] = []
        self._active_incident_ids: Dict[str, str] = {}

    def reset(self) -> None:
        self.log.clear()
        self._active_incident_ids.clear()

    def _stamp(
        self,
        incident_id: str,
        zone_id: str,
        action: str,
        detail: str,
        elapsed_seconds: int,
    ) -> None:
        self.log.append(
            {
                "incident_id": incident_id,
                "zone_id": zone_id,
                "action": action,
                "detail": detail,
                "elapsed_seconds": elapsed_seconds,
                "automated": True,
                "t": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            }
        )

    def handle(self, zone_risk) -> None:
        zone_id = zone_risk.zone_id
        if zone_risk.level != "critical":
            self._active_incident_ids.pop(zone_id, None)
            return
        if zone_id in self._active_incident_ids:
            return

        incident_id = f"INC-{uuid.uuid4().hex[:6].upper()}"
        self._active_incident_ids[zone_id] = incident_id
        factor_text = "; ".join(zone_risk.factors)

        sequence = [
            ("TRIGGER", f"Fused score {zone_risk.score} crossed critical threshold", 0),
            ("EVACUATE", f"Evacuation signal issued for {zone_id} and adjoining zones", 12),
            ("NOTIFY", "Emergency team, control room and safety lead notified", 25),
            ("ISOLATE_WORK", "Active hazardous-work permit placed on emergency hold", 35),
            ("PRESERVE_EVIDENCE", "Sensor buffer and CCTV evidence window marked for retention", 48),
            ("DRAFT_REPORT", f"Preliminary report created. Factors: {factor_text}", 75),
        ]
        for action, detail, elapsed in sequence:
            self._stamp(incident_id, zone_id, action, detail, elapsed)

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self.log[-limit:][::-1]

    def evidence_summary(self) -> dict:
        incident_ids = list(dict.fromkeys(entry["incident_id"] for entry in self.log))
        return {
            "incident_count": len(incident_ids),
            "actions_logged": len(self.log),
            "latest_incident_id": incident_ids[-1] if incident_ids else None,
            "timeline": self.recent(50),
        }


class ComplianceAuditor:
    """Illustrative continuous checks against paraphrased demo clauses."""

    def __init__(self):
        self.clauses = {str(item["id"]): item for item in CORPUS if item["type"] == "regulation"}

    def audit(
        self,
        frame: Dict[str, Any],
        zone_risks,
        response_log: List[Dict[str, Any]] | None = None,
    ) -> List[Dict[str, Any]]:
        response_log = response_log or []
        permits_by_zone: Dict[str, list] = {}
        for permit in frame["permits"]:
            permits_by_zone.setdefault(permit["zone_id"], []).append(permit)
        risk_by_zone = {risk.zone_id: risk for risk in zone_risks}

        hot_work_violations = []
        for zone_id, permits in permits_by_zone.items():
            if any(permit["kind"] == "hot_work" for permit in permits):
                risk = risk_by_zone.get(zone_id)
                if risk and "sensor" in risk.factor_categories:
                    hot_work_violations.append(zone_id)

        critical_zones = [risk.zone_id for risk in zone_risks if risk.level == "critical"]
        response_zones = {entry["zone_id"] for entry in response_log}
        uncovered_critical = [zone for zone in critical_zones if zone not in response_zones]

        return [
            {
                "clause_id": "OISD-105-DEMO",
                "summary": self.clauses["OISD-105-DEMO"]["text"],
                "status": "gap" if hot_work_violations else "compliant",
                "severity": "high" if hot_work_violations else "none",
                "zones_in_violation": hot_work_violations,
            },
            {
                "clause_id": "PTW-RECORD-DEMO",
                "summary": self.clauses["PTW-RECORD-DEMO"]["text"],
                "status": "compliant",
                "severity": "none",
                "zones_in_violation": [],
            },
            {
                "clause_id": "ESCALATION-DEMO",
                "summary": self.clauses["ESCALATION-DEMO"]["text"],
                "status": "gap" if uncovered_critical else ("compliant" if critical_zones else "monitoring"),
                "severity": "critical" if uncovered_critical else "none",
                "zones_in_violation": uncovered_critical,
            },
        ]
