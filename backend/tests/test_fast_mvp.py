from app.services.analytics.fast_mvp import FastCrowdMVP, RISK_WEIGHTS, simulate_interventions
from app.api.phase2 import approve_intervention, detection_store, reject_intervention


def detection(cx=50, cy=50, size=20):
    return {"bbox": [cx-size/2, cy-size/2, cx+size/2, cy+size/2], "centroid": [cx, cy], "confidence": .8, "class_id": 0, "class": "person"}


def flow(speed=0, turbulence=0, vectors=None):
    return {"mean_speed": speed, "turbulence_index": turbulence, "dominant_angle_deg": 0, "grid_vectors": vectors or []}


def test_observed_state_uses_relative_uncalibrated_density():
    state = FastCrowdMVP().analyze([detection()], flow(), 0, 100, 100, 0)
    assert state["signal_source"] == "OBSERVED"
    assert state["calibrated_density"] is False
    assert 0 <= state["relative_density"] <= 100
    assert sum(zone["count"] for zone in state["zones"]) == 1


def test_risk_is_exact_weighted_transparent_formula():
    state = FastCrowdMVP().analyze([detection()], flow(4, .5), 0, 100, 100, 0)
    expected = sum(state[name] * weight for name, weight in RISK_WEIGHTS.items())
    assert state["risk_score"] == round(expected, 2)


def test_opposing_vectors_raise_flow_conflict():
    vectors = [{"x": .2, "y": .5, "vx": 1, "vy": 0}, {"x": .8, "y": .5, "vx": -1, "vy": 0}]
    state = FastCrowdMVP().analyze([], flow(vectors=vectors), 0, 100, 100, 0)
    assert state["flow_conflict"] > 90
    assert state["convergence"] > 90


def test_demo_mode_is_explicit_and_does_not_change_person_count():
    analyzer = FastCrowdMVP(demo_mode=True)
    state = analyzer.analyze([detection()], flow(), 10, 100, 100, 1)
    assert state["signal_source"] == "DEMO_SIMULATION"
    assert state["person_count"] == 1
    assert state["relative_density"] >= 88


def test_interventions_are_simulated_ranked_and_feasible():
    state = FastCrowdMVP(demo_mode=True).analyze([detection()], flow(), 10, 100, 100, 1)
    options = simulate_interventions(state)
    recommended = [item for item in options if item["recommended"]]
    assert len(recommended) == 1
    assert recommended[0]["feasible"] is True
    assert recommended[0]["projected_risk"] < recommended[0]["current_risk"]
    assert all(item["simulation_only"] for item in options)


def test_human_approval_returns_simulation_only_result():
    state = FastCrowdMVP(demo_mode=True).analyze([detection()], flow(), 10, 100, 100, 1)
    options = simulate_interventions(state)
    detection_store["approval-test"] = {"status": "COMPLETED", "result": {"summary": {"interventions": options}}}
    selected = next(item for item in options if item["recommended"])
    result = approve_intervention("approval-test", selected["option_id"])
    assert result["human_decision"] == "APPROVED"
    assert "SIMULATION ONLY" in result["message"]
    detection_store.pop("approval-test")


def test_human_rejection_is_recorded_without_action():
    detection_store["reject-test"] = {"status": "COMPLETED"}
    result = reject_intervention("reject-test", "Operator override")
    assert result == {"status": "REJECTED", "human_decision": "REJECTED", "reason": "Operator override"}
    detection_store.pop("reject-test")
