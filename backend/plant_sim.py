"""Deterministic plant simulator used by the hackathon demo.

The simulator produces a complete operating frame containing gas readings,
permits, maintenance flags, worker locations and shift context.  A real plant
adapter can replace :meth:`PlantSimulator.tick` without changing the risk
engine contract.
"""

from __future__ import annotations

import random
import uuid
from dataclasses import asdict, dataclass
from typing import Dict, List

ZONE_LAYOUT = [
    ("A1", "Coke Oven Battery - Charge Side", 0, 0, 0.80),
    ("A2", "Coke Oven Battery - Push Side", 1, 0, 0.80),
    ("B1", "Gas Collection Main", 2, 0, 0.90),
    ("B2", "By-Product Plant", 3, 0, 0.60),
    ("C1", "Coal Handling Yard", 0, 1, 0.40),
    ("C2", "Quenching Tower", 1, 1, 0.50),
    ("C3", "Blast Furnace Stockhouse", 2, 1, 0.70),
    ("C4", "Sinter Plant", 3, 1, 0.55),
    ("D1", "Boiler House", 0, 2, 0.45),
    ("D2", "Substation & Switchyard", 1, 2, 0.50),
    ("D3", "Rolling Mill", 2, 2, 0.35),
    ("D4", "Central Stores", 3, 2, 0.15),
]

GAS_TYPES = ("CO", "H2S", "CH4")
SHIFTS = ("A (06:00-14:00)", "B (14:00-22:00)", "C (22:00-06:00)")
DEMO_ZONE = "B1"
DEMO_PERMIT_ID = "DEMO-HW-01"


@dataclass(frozen=True)
class SensorReading:
    zone_id: str
    gas: str
    ppm: float
    threshold_warn: float
    threshold_crit: float


@dataclass(frozen=True)
class Permit:
    permit_id: str
    zone_id: str
    kind: str
    issued_by: str
    active: bool = True


@dataclass(frozen=True)
class WorkerPing:
    worker_id: str
    zone_id: str
    role: str


class PlantSimulator:
    """Small, reproducible digital-twin-like simulator for judging.

    ``trigger_demo_scenario`` creates a deterministic compound event.  The CO
    reading is only at warning level, but an active hot-work permit,
    maintenance and high occupancy lift the fused score into the critical
    range.  This is intentionally designed to prove the value of data fusion.
    """

    def __init__(self, seed: int = 7, auto_scenarios: bool = False):
        self.seed = seed
        self.auto_scenarios = auto_scenarios
        self.zones = {
            row[0]: {
                "id": row[0],
                "label": row[1],
                "x": row[2],
                "y": row[3],
                "base_hazard": row[4],
            }
            for row in ZONE_LAYOUT
        }
        self.reset()

    def reset(self) -> None:
        self._rng = random.Random(self.seed)
        self.tick_count = 0
        self._demo_ticks_remaining = 0
        self._scenario_id: str | None = None
        self._maintenance_flags: Dict[str, bool] = {zone: False for zone in self.zones}
        self._active_permits: List[Permit] = [
            Permit("PTW-ELEC-014", "D2", "electrical", "electrical_supervisor"),
            Permit("PTW-GEN-205", "C4", "general", "area_manager"),
        ]

    @property
    def demo_active(self) -> bool:
        return self._demo_ticks_remaining > 0

    def trigger_demo_scenario(self, duration_ticks: int = 8) -> dict:
        duration = max(4, min(duration_ticks, 20))
        self._demo_ticks_remaining = duration
        self._scenario_id = f"SCN-{uuid.uuid4().hex[:6].upper()}"
        self._maintenance_flags[DEMO_ZONE] = True
        self._active_permits = [p for p in self._active_permits if p.permit_id != DEMO_PERMIT_ID]
        self._active_permits.append(
            Permit(DEMO_PERMIT_ID, DEMO_ZONE, "hot_work", "shift_supervisor_demo")
        )
        return {
            "scenario_id": self._scenario_id,
            "zone_id": DEMO_ZONE,
            "duration_ticks": duration,
            "description": (
                "Warning-level CO + hot-work permit + maintenance + concentrated occupancy"
            ),
        }

    def _current_shift(self) -> str:
        return SHIFTS[(self.tick_count // 40) % len(SHIFTS)]

    def _shift_changeover_now(self) -> bool:
        return (self.tick_count % 40) < 3

    def _roll_gas_reading(self, zone_id: str, gas: str) -> SensorReading:
        baseline = {"CO": 20.0, "H2S": 5.0, "CH4": 300.0}[gas]
        warn = {"CO": 50.0, "H2S": 10.0, "CH4": 1000.0}[gas]
        crit = {"CO": 100.0, "H2S": 20.0, "CH4": 5000.0}[gas]
        hazard = self.zones[zone_id]["base_hazard"]

        noise = self._rng.gauss(0, baseline * 0.14 * (1 + hazard))
        value = max(0.0, baseline + noise)

        if self.demo_active and zone_id == DEMO_ZONE:
            # Deliberately below the critical threshold. Sensor-only alerting
            # sees a warning; the fusion engine sees a critical compound event.
            if gas == "CO":
                value = 78.0
            elif gas == "H2S":
                value = 7.5
            elif gas == "CH4":
                value = 620.0

        return SensorReading(zone_id, gas, round(value, 1), warn, crit)

    def _workers(self) -> List[WorkerPing]:
        if self.demo_active:
            fixed = [
                WorkerPing(f"DEMO-W-{idx:02d}", DEMO_ZONE, role)
                for idx, role in enumerate(
                    [
                        "Welder",
                        "Fitter",
                        "Permit Holder",
                        "Contractor",
                        "Operator",
                        "Safety Observer",
                    ],
                    start=1,
                )
            ]
            remaining_zones = [zone for zone in self.zones if zone != DEMO_ZONE]
            roaming = [
                WorkerPing(
                    f"W-{idx:03d}",
                    self._rng.choice(remaining_zones),
                    self._rng.choice(["Operator", "Fitter", "Safety Officer", "Contractor"]),
                )
                for idx in range(7, 13)
            ]
            return fixed + roaming

        return [
            WorkerPing(
                f"W-{idx:03d}",
                self._rng.choice(list(self.zones)),
                self._rng.choice(["Operator", "Fitter", "Safety Officer", "Contractor"]),
            )
            for idx in range(1, 13)
        ]

    def _maybe_auto_inject(self) -> None:
        if self.auto_scenarios and not self.demo_active and self._rng.random() < 0.008:
            self.trigger_demo_scenario()

    def _expire_background_activity(self) -> None:
        if self.demo_active:
            return
        if self._rng.random() < 0.04:
            zone_id = self._rng.choice(list(self.zones))
            self._maintenance_flags[zone_id] = not self._maintenance_flags[zone_id]

    def _end_demo_if_needed(self) -> None:
        if not self.demo_active:
            return
        self._demo_ticks_remaining -= 1
        if self._demo_ticks_remaining == 0:
            self._maintenance_flags[DEMO_ZONE] = False
            self._active_permits = [p for p in self._active_permits if p.permit_id != DEMO_PERMIT_ID]

    def tick(self) -> dict:
        self.tick_count += 1
        self._maybe_auto_inject()
        self._expire_background_activity()

        readings = [self._roll_gas_reading(zone, gas) for zone in self.zones for gas in GAS_TYPES]
        workers = self._workers()
        scenario_snapshot = {
            "active": self.demo_active,
            "scenario_id": self._scenario_id,
            "zone_id": DEMO_ZONE if self.demo_active else None,
            "ticks_remaining": self._demo_ticks_remaining,
            "label": "Deterministic compound-risk demonstration" if self.demo_active else "Normal simulation",
        }

        frame = {
            "tick": self.tick_count,
            "shift": self._current_shift(),
            "shift_changeover": self._shift_changeover_now(),
            "readings": [asdict(r) for r in readings],
            "permits": [asdict(p) for p in self._active_permits],
            "maintenance": {zone: active for zone, active in self._maintenance_flags.items() if active},
            "workers": [asdict(w) for w in workers],
            "zones": self.zones,
            "scenario": scenario_snapshot,
        }
        self._end_demo_if_needed()
        return frame
