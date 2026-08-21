"""Synthetic scenario API for CROWD-SHIELD demo mode.

These endpoints serve pre-generated synthetic crowd-state data and run the
SAME risk engine + intervention engine used for real video analysis.  The
synthetic data is clearly labelled and never mixed with real observations.
"""

from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import APIRouter

from app.api.phase1 import Phase1APIError
from app.services.analytics.fast_mvp import RISK_WEIGHTS, _clip, risk_level, simulate_interventions


router = APIRouter(prefix="/api/synthetic")

_DATA_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "synthetic" / "synthetic_crowd_scenarios.json"
_dataset: dict[str, Any] | None = None
_approval_store: dict[str, dict[str, Any]] = {}
_lock = Lock()


def _load_dataset() -> dict[str, Any]:
    global _dataset
    if _dataset is not None:
        return _dataset
    if not _DATA_PATH.is_file():
        raise Phase1APIError(500, "DATASET_MISSING", "Synthetic dataset not found. Run generate_scenarios.py first.")
    _dataset = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return _dataset


def _aggregate_timestamp(records: list[dict[str, Any]], timestamp: int) -> dict[str, Any]:
    """Aggregate all zone records at a given timestamp into a single CrowdState."""
    zone_records = [r for r in records if r["timestamp"] == timestamp]
    if not zone_records:
        return {}

    # Overall state is driven by the highest-pressure zone (worst-case)
    worst = max(zone_records, key=lambda r: r["density_score"])

    # Build per-zone breakdown
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
        reasons = []
        if zr["density_score"] >= 45:
            reasons.append("High relative occupancy")
        if zr["convergence_score"] >= 40:
            reasons.append("Converging crowd flow")
        if zr["conflict_score"] >= 40:
            reasons.append("Conflicting movement directions")
        if zr["bottleneck_score"] >= 45:
            reasons.append("Bottleneck pressure")
        zones.append({
            "zone_id": zr["zone"],
            "count": int(zr["detected_occupancy"]),
            "relative_density": zr["density_score"],
            "risk_score": zone_risk,
            "reasons": reasons or ["Normal crowd dynamics"],
        })

    # Compute global risk from worst-zone signals
    risk_score = _clip(
        RISK_WEIGHTS["density"] * worst["density_score"]
        + RISK_WEIGHTS["density_growth"] * worst["density_growth"]
        + RISK_WEIGHTS["movement_instability"] * worst["movement_score"]
        + RISK_WEIGHTS["flow_conflict"] * worst["conflict_score"]
        + RISK_WEIGHTS["convergence"] * worst["convergence_score"]
        + RISK_WEIGHTS["bottleneck_pressure"] * worst["bottleneck_score"]
    )

    critical_zone = max(zones, key=lambda z: z["risk_score"])

    # Top contributors
    signal_map = {
        "density": worst["density_score"],
        "density_growth": worst["density_growth"],
        "movement_instability": worst["movement_score"],
        "flow_conflict": worst["conflict_score"],
        "convergence": worst["convergence_score"],
        "bottleneck_pressure": worst["bottleneck_score"],
    }
    contributions = {k: round(v * RISK_WEIGHTS[k], 2) for k, v in signal_map.items()}
    top = sorted(contributions, key=contributions.get, reverse=True)[:3]

    return {
        "timestamp": timestamp,
        "signal_source": "SYNTHETIC_DEMO",
        "person_count": int(sum(zr["detected_occupancy"] for zr in zone_records)),
        "relative_density": worst["density_score"],
        "density_label": "CRITICAL" if worst["density_score"] >= 75 else "HIGH" if worst["density_score"] >= 55 else "MEDIUM" if worst["density_score"] >= 30 else "LOW",
        "density": worst["density_score"],
        "density_growth": worst["density_growth"],
        "movement_speed": worst["movement_score"],
        "movement_instability": worst["movement_score"],
        "movement_available": True,
        "dominant_direction_deg": 0.0,
        "flow_conflict": worst["conflict_score"],
        "convergence": worst["convergence_score"],
        "bottleneck_pressure": worst["bottleneck_score"],
        "risk_score": risk_score,
        "risk_level": risk_level(risk_score),
        "risk_slope": 0.0,  # will be computed in timeline
        "risk_trend": "STABLE",
        "top_contributors": [name.replace("_", " ").title() for name in top],
        "critical_zone": critical_zone["zone_id"],
        "critical_zone_reasons": critical_zone["reasons"],
        "zones": zones,
        "calibrated_density": False,
        "venue_context_available": False,
        "flow_vectors": [],
    }


@router.get("/scenarios")
def list_scenarios():
    """List available synthetic scenarios."""
    dataset = _load_dataset()
    result = []
    for name in dataset["scenarios"]:
        records = dataset["scenarios"][name]
        num_steps = len(set(r["timestamp"] for r in records))
        result.append({
            "name": name,
            "total_records": len(records),
            "timesteps": num_steps,
            "duration_sec": max(r["timestamp"] for r in records),
            "zones": sorted(set(r["zone"] for r in records)),
        })
    return {
        "scenarios": result,
        "disclaimer": dataset["metadata"]["disclaimer"],
    }


@router.get("/scenarios/{scenario_name}")
def get_scenario(scenario_name: str):
    """Return the raw timeline data for a single scenario."""
    dataset = _load_dataset()
    name = scenario_name.upper()
    if name not in dataset["scenarios"]:
        raise Phase1APIError(404, "SCENARIO_NOT_FOUND", f"Scenario '{scenario_name}' not found. Available: {list(dataset['scenarios'].keys())}")
    return {
        "scenario": name,
        "records": dataset["scenarios"][name],
        "metadata": dataset["metadata"],
    }


@router.post("/scenarios/{scenario_name}/analyze")
def analyze_scenario(scenario_name: str):
    """Run the SAME risk engine + intervention engine on the synthetic scenario."""
    dataset = _load_dataset()
    name = scenario_name.upper()
    if name not in dataset["scenarios"]:
        raise Phase1APIError(404, "SCENARIO_NOT_FOUND", f"Scenario '{scenario_name}' not found.")

    records = dataset["scenarios"][name]
    timestamps = sorted(set(r["timestamp"] for r in records))

    # Build the full crowd-state timeline
    timeline = []
    risk_history = []
    for ts in timestamps:
        state = _aggregate_timestamp(records, ts)

        # Compute risk slope from history
        risk_history.append((ts, state["risk_score"]))
        if len(risk_history) >= 2:
            import numpy as np
            times = np.array([h[0] for h in risk_history[-8:]])
            values = np.array([h[1] for h in risk_history[-8:]])
            dt = times[-1] - times[0]
            if dt > 0:
                slope = float(np.polyfit(times - times[0], values, 1)[0])
                state["risk_slope"] = round(slope, 3)
                if slope > 2.0:
                    state["risk_trend"] = "RAPIDLY INCREASING"
                elif slope > 0.35:
                    state["risk_trend"] = "INCREASING"
                elif slope < -0.35:
                    state["risk_trend"] = "DECREASING"
                else:
                    state["risk_trend"] = "STABLE"

        timeline.append(state)

    # Use peak state for intervention simulation
    peak_state = max(timeline, key=lambda s: s["risk_score"])
    interventions = simulate_interventions(peak_state)

    # Summary
    summary = {
        "scenario": name,
        "signal_source": "SYNTHETIC_DEMO",
        "timesteps_analyzed": len(timestamps),
        "duration_sec": max(timestamps),
        "peak_risk": peak_state["risk_score"],
        "peak_risk_level": peak_state["risk_level"],
        "peak_timestamp": peak_state["timestamp"],
        "critical_zone": peak_state["critical_zone"],
        "interventions": interventions,
        "disclaimer": dataset["metadata"]["disclaimer"],
    }

    return {
        "scenario": name,
        "timeline": timeline,
        "summary": summary,
        "peak_state": peak_state,
    }


@router.post("/scenarios/{scenario_name}/interventions/{option_id}/approve")
def approve_synthetic_intervention(scenario_name: str, option_id: str):
    """Approve a simulated intervention in synthetic demo mode."""
    # First, get the analysis to find the intervention
    analysis = analyze_scenario(scenario_name)
    interventions = analysis["summary"]["interventions"]
    option = next((item for item in interventions if item["option_id"] == option_id), None)
    if not option:
        raise Phase1APIError(404, "INTERVENTION_NOT_FOUND", f"Intervention '{option_id}' not found.")
    if not option["feasible"]:
        raise Phase1APIError(409, "INTERVENTION_INFEASIBLE", option["feasibility_reason"])

    with _lock:
        _approval_store[f"{scenario_name}_{option_id}"] = {
            "status": "SIMULATED_INTERVENTION_APPLIED",
            "human_decision": "APPROVED",
            "option": option,
            "message": "Projected crowd stabilization. SIMULATION ONLY — no physical control action was sent.",
        }
    return _approval_store[f"{scenario_name}_{option_id}"]


@router.post("/scenarios/{scenario_name}/interventions/reject")
def reject_synthetic_intervention(scenario_name: str):
    """Reject a simulated intervention in synthetic demo mode."""
    return {"status": "REJECTED", "human_decision": "REJECTED", "reason": "Operator rejected recommendation"}
