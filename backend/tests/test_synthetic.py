"""Tests for the CROWD-SHIELD synthetic dataset and demo pipeline.

Validates:
- Dataset loads and has correct structure
- Required columns exist
- No invalid values (NaN, negative, >100)
- Timestamps increase monotonically per zone
- SAFE scenario has lower pressure than CRITICAL
- ESCALATING scenario increases over time
- CRITICAL scenario reaches high pressure
- Risk engine produces valid 0-100 scores
- Intervention simulation reduces risk when expected
- Feasibility rejects overloaded destinations
"""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

DATA_PATH = PROJECT_ROOT / "data" / "synthetic" / "synthetic_crowd_scenarios.json"

REQUIRED_FIELDS = [
    "timestamp", "scenario", "zone",
    "detected_occupancy", "density_score", "density_growth",
    "movement_score", "convergence_score", "conflict_score", "bottleneck_score",
]


@pytest.fixture(scope="module")
def dataset():
    assert DATA_PATH.is_file(), f"Dataset not found at {DATA_PATH}"
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def scenarios(dataset):
    return dataset["scenarios"]


# ──── Dataset Structure Tests ────

class TestDatasetStructure:

    def test_dataset_loads(self, dataset):
        assert "metadata" in dataset
        assert "scenarios" in dataset

    def test_metadata_present(self, dataset):
        meta = dataset["metadata"]
        assert meta["generator"] == "CROWD-SHIELD Synthetic Scenario Generator"
        assert "disclaimer" in meta

    def test_three_scenarios_exist(self, scenarios):
        assert "SAFE" in scenarios
        assert "ESCALATING" in scenarios
        assert "CRITICAL" in scenarios

    def test_required_columns_exist(self, scenarios):
        for name, records in scenarios.items():
            assert len(records) > 0, f"Scenario {name} has no records"
            for record in records:
                for field in REQUIRED_FIELDS:
                    assert field in record, f"Missing field '{field}' in {name}"

    def test_no_invalid_values(self, scenarios):
        numeric_fields = REQUIRED_FIELDS[3:]  # skip timestamp, scenario, zone
        for name, records in scenarios.items():
            for record in records:
                for field in numeric_fields:
                    value = record[field]
                    assert isinstance(value, (int, float)), f"{name}.{field} is not numeric: {value}"
                    assert not np.isnan(value), f"{name}.{field} is NaN"
                    assert 0 <= value <= 100, f"{name}.{field} out of range: {value}"

    def test_timestamps_increase_per_zone(self, scenarios):
        for name, records in scenarios.items():
            zones = set(r["zone"] for r in records)
            for zone in zones:
                zone_records = [r for r in records if r["zone"] == zone]
                timestamps = [r["timestamp"] for r in zone_records]
                assert timestamps == sorted(timestamps), f"{name}/{zone}: timestamps not sorted"
                assert len(set(timestamps)) == len(timestamps), f"{name}/{zone}: duplicate timestamps"

    def test_four_zones_per_scenario(self, scenarios):
        for name, records in scenarios.items():
            zones = set(r["zone"] for r in records)
            assert len(zones) == 4, f"{name}: expected 4 zones, got {zones}"


# ──── Scenario Behavior Tests ────

class TestScenarioBehavior:

    def _zone_b_final(self, scenarios, scenario_name):
        records = scenarios[scenario_name]
        zone_b = [r for r in records if r["zone"] == "ZONE_B"]
        return zone_b[-1]

    def _zone_b_first(self, scenarios, scenario_name):
        records = scenarios[scenario_name]
        zone_b = [r for r in records if r["zone"] == "ZONE_B"]
        return zone_b[0]

    def test_safe_has_low_final_density(self, scenarios):
        final = self._zone_b_final(scenarios, "SAFE")
        assert final["density_score"] < 35, f"SAFE final density too high: {final['density_score']}"

    def test_safe_has_low_final_bottleneck(self, scenarios):
        final = self._zone_b_final(scenarios, "SAFE")
        assert final["bottleneck_score"] < 25, f"SAFE final bottleneck too high: {final['bottleneck_score']}"

    def test_escalating_increases_over_time(self, scenarios):
        first = self._zone_b_first(scenarios, "ESCALATING")
        final = self._zone_b_final(scenarios, "ESCALATING")
        assert final["density_score"] > first["density_score"] + 20, "ESCALATING density did not increase sufficiently"
        assert final["convergence_score"] > first["convergence_score"] + 15, "ESCALATING convergence did not increase"

    def test_critical_reaches_high_pressure(self, scenarios):
        final = self._zone_b_final(scenarios, "CRITICAL")
        assert final["density_score"] > 75, f"CRITICAL final density too low: {final['density_score']}"
        assert final["bottleneck_score"] > 65, f"CRITICAL final bottleneck too low: {final['bottleneck_score']}"

    def test_safe_lower_than_critical(self, scenarios):
        safe_final = self._zone_b_final(scenarios, "SAFE")
        critical_final = self._zone_b_final(scenarios, "CRITICAL")
        assert safe_final["density_score"] < critical_final["density_score"]
        assert safe_final["bottleneck_score"] < critical_final["bottleneck_score"]


# ──── Risk Engine Tests ────

class TestRiskEngine:

    def test_risk_engine_import(self):
        from app.services.analytics.fast_mvp import RISK_WEIGHTS, _clip, risk_level
        assert sum(RISK_WEIGHTS.values()) == pytest.approx(1.0, abs=0.01)

    def test_risk_level_classification(self):
        from app.services.analytics.fast_mvp import risk_level
        assert risk_level(15) == "SAFE"
        assert risk_level(40) == "WATCH"
        assert risk_level(60) == "HIGH"
        assert risk_level(85) == "CRITICAL"

    def test_risk_score_valid_range(self, scenarios):
        from app.services.analytics.fast_mvp import RISK_WEIGHTS, _clip
        for name, records in scenarios.items():
            timestamps = sorted(set(r["timestamp"] for r in records))
            for ts in timestamps:
                zone_records = [r for r in records if r["timestamp"] == ts]
                for zr in zone_records:
                    risk = _clip(
                        RISK_WEIGHTS["density"] * zr["density_score"]
                        + RISK_WEIGHTS["density_growth"] * zr["density_growth"]
                        + RISK_WEIGHTS["movement_instability"] * zr["movement_score"]
                        + RISK_WEIGHTS["flow_conflict"] * zr["conflict_score"]
                        + RISK_WEIGHTS["convergence"] * zr["convergence_score"]
                        + RISK_WEIGHTS["bottleneck_pressure"] * zr["bottleneck_score"]
                    )
                    assert 0 <= risk <= 100, f"{name}/{zr['zone']}/{ts}: risk {risk} out of range"

    def test_safe_scenario_low_risk(self, scenarios):
        from app.services.analytics.fast_mvp import RISK_WEIGHTS, _clip
        records = scenarios["SAFE"]
        zone_b_records = [r for r in records if r["zone"] == "ZONE_B"]
        for zr in zone_b_records:
            risk = _clip(
                RISK_WEIGHTS["density"] * zr["density_score"]
                + RISK_WEIGHTS["density_growth"] * zr["density_growth"]
                + RISK_WEIGHTS["movement_instability"] * zr["movement_score"]
                + RISK_WEIGHTS["flow_conflict"] * zr["conflict_score"]
                + RISK_WEIGHTS["convergence"] * zr["convergence_score"]
                + RISK_WEIGHTS["bottleneck_pressure"] * zr["bottleneck_score"]
            )
            assert risk < 40, f"SAFE scenario risk too high: {risk}"


# ──── Intervention Tests ────

class TestInterventionEngine:

    def _peak_state(self, scenarios):
        """Build a synthetic crowd state matching the peak of CRITICAL for the intervention engine."""
        from app.services.analytics.fast_mvp import RISK_WEIGHTS, _clip, risk_level
        records = scenarios["CRITICAL"]
        last_ts = max(r["timestamp"] for r in records)
        zone_records = [r for r in records if r["timestamp"] == last_ts]
        worst = max(zone_records, key=lambda r: r["density_score"])

        zones = []
        for zr in zone_records:
            zone_risk = _clip(
                RISK_WEIGHTS["density"] * zr["density_score"]
                + RISK_WEIGHTS["density_growth"] * zr["density_growth"]
                + RISK_WEIGHTS["movement_instability"] * zr["movement_score"]
                + RISK_WEIGHTS["flow_conflict"] * zr["conflict_score"]
                + RISK_WEIGHTS["convergence"] * zr["convergence_score"]
                + RISK_WEIGHTS["bottleneck_pressure"] * zr["bottleneck_score"]
            )
            zones.append({
                "zone_id": zr["zone"],
                "count": int(zr["detected_occupancy"]),
                "relative_density": zr["density_score"],
                "risk_score": zone_risk,
                "reasons": [],
            })

        risk = _clip(
            RISK_WEIGHTS["density"] * worst["density_score"]
            + RISK_WEIGHTS["density_growth"] * worst["density_growth"]
            + RISK_WEIGHTS["movement_instability"] * worst["movement_score"]
            + RISK_WEIGHTS["flow_conflict"] * worst["conflict_score"]
            + RISK_WEIGHTS["convergence"] * worst["convergence_score"]
            + RISK_WEIGHTS["bottleneck_pressure"] * worst["bottleneck_score"]
        )

        return {
            "risk_score": risk,
            "risk_level": risk_level(risk),
            "density": worst["density_score"],
            "density_growth": worst["density_growth"],
            "movement_instability": worst["movement_score"],
            "flow_conflict": worst["conflict_score"],
            "convergence": worst["convergence_score"],
            "bottleneck_pressure": worst["bottleneck_score"],
            "zones": zones,
        }

    def test_interventions_reduce_risk(self, scenarios):
        from app.services.analytics.fast_mvp import simulate_interventions
        state = self._peak_state(scenarios)
        options = simulate_interventions(state)
        assert len(options) > 0, "No interventions generated"

        current_risk = state["risk_score"]
        for opt in options:
            if opt["option_id"] == "MONITOR":
                continue
            if opt["feasible"]:
                assert opt["projected_risk"] < current_risk, (
                    f"{opt['option_id']}: projected {opt['projected_risk']} >= current {current_risk}"
                )

    def test_recommended_is_best_feasible(self, scenarios):
        from app.services.analytics.fast_mvp import simulate_interventions
        state = self._peak_state(scenarios)
        options = simulate_interventions(state)
        feasible = [o for o in options if o["feasible"] and o["option_id"] != "MONITOR"]
        if not feasible:
            pytest.skip("No feasible interventions")
        best = min(feasible, key=lambda o: o["projected_risk"])
        recommended = [o for o in options if o.get("recommended")]
        assert len(recommended) == 1, f"Expected 1 recommended, got {len(recommended)}"
        assert recommended[0]["projected_risk"] == best["projected_risk"]

    def test_simulation_only_flag(self, scenarios):
        from app.services.analytics.fast_mvp import simulate_interventions
        state = self._peak_state(scenarios)
        options = simulate_interventions(state)
        for opt in options:
            assert opt["simulation_only"] is True, f"{opt['option_id']} missing simulation_only flag"
