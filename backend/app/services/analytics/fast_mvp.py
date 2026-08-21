"""Transparent image-space crowd intelligence for the hackathon MVP."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any

import numpy as np


RISK_WEIGHTS = {
    "density": 0.25,
    "density_growth": 0.15,
    "movement_instability": 0.15,
    "flow_conflict": 0.15,
    "convergence": 0.15,
    "bottleneck_pressure": 0.15,
}


def _clip(value: float) -> float:
    return round(float(np.clip(value, 0.0, 100.0)), 2)


def risk_level(score: float) -> str:
    if score < 30:
        return "SAFE"
    if score < 55:
        return "WATCH"
    if score < 75:
        return "HIGH"
    return "CRITICAL"


def _trend(slope: float) -> str:
    if slope > 2.0:
        return "RAPIDLY INCREASING"
    if slope > 0.35:
        return "INCREASING"
    if slope < -0.35:
        return "DECREASING"
    return "STABLE"


@dataclass
class FastCrowdMVP:
    """Stateful frame analyzer. Scores are prototype signals, not safety thresholds."""

    demo_mode: bool = False
    density_history: deque[tuple[float, float]] = field(default_factory=lambda: deque(maxlen=8))
    risk_history: deque[tuple[float, float]] = field(default_factory=lambda: deque(maxlen=8))

    def analyze(
        self,
        detections: list[dict[str, Any]],
        flow: dict[str, Any],
        timestamp: float,
        frame_width: int,
        frame_height: int,
        progress: float,
    ) -> dict[str, Any]:
        frame_area = max(1.0, float(frame_width * frame_height))
        box_area = sum(
            max(0.0, d["bbox"][2] - d["bbox"][0]) * max(0.0, d["bbox"][3] - d["bbox"][1])
            for d in detections
        )
        visible_occupancy = min(1.0, box_area / frame_area)
        count_component = min(1.0, len(detections) / 100.0)

        # Compute spatial packing density from centroid distances
        if len(detections) >= 2:
            centroids = np.array([d["centroid"] for d in detections], dtype=float)
            if centroids.max() > 1.0:
                centroids[:, 0] /= frame_width
                centroids[:, 1] /= frame_height
            dists = np.sqrt(np.sum((centroids[:, None, :] - centroids[None, :, :]) ** 2, axis=-1))
            np.fill_diagonal(dists, np.inf)
            min_dists = np.min(dists, axis=1)
            mean_dist = float(np.mean(min_dists))
            packing_density = float(np.clip((1.0 - mean_dist * 12.0) * 100.0, 0.0, 100.0))
        else:
            packing_density = 0.0

        density = _clip(100 * (0.45 * visible_occupancy + 0.35 * count_component + 0.20 * (packing_density / 100.0)))

        vectors = flow.get("grid_vectors", [])
        convergence_values: list[float] = []
        angles: list[float] = []
        for vector in vectors:
            vx, vy = float(vector["vx"]), float(vector["vy"])
            magnitude = float(np.hypot(vx, vy))
            if magnitude <= 1e-6:
                continue
            angles.append(float(np.arctan2(vy, vx)))
            toward = np.array([0.5 - float(vector["x"]), 0.5 - float(vector["y"])])
            toward_norm = float(np.linalg.norm(toward))
            if toward_norm > 1e-6:
                convergence_values.append(max(0.0, float(np.dot([vx, vy], toward) / (magnitude * toward_norm))))

        if angles:
            resultant = abs(np.mean(np.exp(1j * np.asarray(angles))))
            conflict = _clip((1.0 - resultant) * 100)
        else:
            conflict = 0.0
        convergence = _clip(100 * np.mean(convergence_values)) if convergence_values else 0.0
        movement_speed = _clip(float(flow.get("mean_speed", 0.0)) / 8.0 * 100)
        speeds = [float(item.get("speed", 0.0)) for item in vectors]
        speed_variation = (float(np.std(speeds)) / max(0.001, float(np.mean(speeds)))) * 100 if len(speeds) > 1 else 0.0
        movement_instability = _clip(0.7 * conflict + 0.3 * min(100.0, speed_variation))

        self.density_history.append((timestamp, density))
        density_growth = 0.0
        if len(self.density_history) > 1:
            dt = max(0.001, self.density_history[-1][0] - self.density_history[0][0])
            density_growth = _clip(max(0.0, (density - self.density_history[0][1]) / dt) * 8.0)

        source = "OBSERVED"
        if self.demo_mode:
            # Explicitly simulated stress trajectory; detections and person count remain observed.
            ramp = float(np.clip(progress, 0.0, 1.0))
            density = max(density, _clip(18 + 70 * ramp))
            density_growth = max(density_growth, _clip(15 + 55 * ramp))
            movement_instability = max(movement_instability, _clip(20 + 55 * ramp))
            conflict = max(conflict, _clip(12 + 62 * ramp))
            convergence = max(convergence, _clip(18 + 68 * ramp))
            source = "DEMO_SIMULATION"

        bottleneck = _clip(0.45 * density + 0.25 * density_growth + 0.30 * convergence)
        signals = {
            "density": density,
            "density_growth": density_growth,
            "movement_instability": movement_instability,
            "flow_conflict": conflict,
            "convergence": convergence,
            "bottleneck_pressure": bottleneck,
        }
        risk = _clip(sum(signals[name] * RISK_WEIGHTS[name] for name in RISK_WEIGHTS))
        contributions = {name: round(signals[name] * RISK_WEIGHTS[name], 2) for name in signals}

        zones_data = self._zones(detections, frame_width, frame_height, signals)
        max_zone_risk = max((z["risk_score"] for z in zones_data), default=density)
        max_zone_count = max((z["count"] for z in zones_data), default=0)

        # For static images / single-frame media (where optical flow / temporal signals are 0):
        if not vectors and (len(self.density_history) <= 1 or (conflict == 0 and convergence == 0 and movement_speed == 0)):
            static_risk = _clip(0.55 * density + 0.30 * max_zone_risk + 0.15 * min(100.0, max_zone_count * 2.5))
            bottleneck = max(bottleneck, max_zone_risk)
            signals["bottleneck_pressure"] = bottleneck

        risk = _clip(sum(signals[name] * RISK_WEIGHTS[name] for name in RISK_WEIGHTS))
        contributions = {name: round(signals[name] * RISK_WEIGHTS[name], 2) for name in signals}

        # Any scene with >= 200 detected people is automatically classified as CRITICAL risk (>= 75)
        if len(detections) >= 200:
            critical_floor = _clip(78.0 + min(22.0, (len(detections) - 200) * 0.1))
            risk = max(risk, critical_floor)
            density = max(density, 82.0)
            signals["density"] = density
            signals["bottleneck_pressure"] = max(signals["bottleneck_pressure"], 82.0)

        self.risk_history.append((timestamp, risk))
        slope = 0.0
        if len(self.risk_history) > 1:
            times = np.asarray([item[0] for item in self.risk_history])
            values = np.asarray([item[1] for item in self.risk_history])
            if times[-1] > times[0]:
                slope = float(np.polyfit(times - times[0], values, 1)[0])

        zones = self._zones(detections, frame_width, frame_height, signals)
        critical = max(zones, key=lambda item: item["risk_score"])
        top = sorted(contributions, key=contributions.get, reverse=True)[:3]
        return {
            "signal_source": source,
            "movement_available": bool(vectors),
            "venue_context_available": False,
            "person_count": len(detections),
            "relative_density": density,
            "density_label": "CRITICAL" if density >= 75 else "HIGH" if density >= 55 else "MEDIUM" if density >= 30 else "LOW",
            "movement_speed": movement_speed,
            "dominant_direction_deg": float(flow.get("dominant_angle_deg", 0.0)),
            **signals,
            "risk_score": risk,
            "risk_level": risk_level(risk),
            "risk_slope": round(slope, 3),
            "risk_trend": _trend(slope),
            "top_contributors": [name.replace("_", " ").title() for name in top],
            "critical_zone": critical["zone_id"],
            "critical_zone_reasons": critical["reasons"],
            "zones": zones,
            "flow_vectors": vectors,
            "calibrated_density": False,
        }

    @staticmethod
    def _zones(detections, width: int, height: int, signals: dict[str, float]) -> list[dict[str, Any]]:
        zones = []
        for index, (name, x0, y0, x1, y1) in enumerate((
            ("ZONE A", 0, 0, .5, .5), ("ZONE B", .5, 0, 1, .5),
            ("ZONE C", 0, .5, .5, 1), ("ZONE D", .5, .5, 1, 1),
        )):
            in_zone = [d for d in detections if x0 * width <= d["centroid"][0] < x1 * width and y0 * height <= d["centroid"][1] < y1 * height]
            occupancy = sum(max(0, d["bbox"][2]-d["bbox"][0]) * max(0, d["bbox"][3]-d["bbox"][1]) for d in in_zone) / max(1, width * height / 4)
            zone_density = _clip(100 * (0.65 * min(1, occupancy) + 0.35 * min(1, len(in_zone)/8)))
            zone_risk = _clip(.55 * zone_density + .20 * signals["convergence"] + .15 * signals["flow_conflict"] + .10 * signals["density_growth"])
            reasons = []
            if zone_density >= 30: reasons.append("High relative occupancy")
            if signals["convergence"] >= 45: reasons.append("Converging image-space flow")
            if signals["flow_conflict"] >= 45: reasons.append("Conflicting movement directions")
            zones.append({"zone_id": name, "count": len(in_zone), "relative_density": zone_density, "risk_score": zone_risk, "reasons": reasons or ["Highest relative grid score"]})
        return zones


def simulate_interventions(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Transparent what-if signal transforms; outputs are simulation only."""
    current = float(state["risk_score"])
    candidates = [
        ("MONITOR", "Continue Monitoring", {}, True, "No intervention is recommended while the prototype risk remains SAFE."),
        ("RESTRICT_ENTRANCE_A", "Restrict Entrance A", {"density_growth": .40}, True, "Reduces estimated incoming growth."),
        ("OPEN_EXIT_C", "Open Exit C", {"density": .72, "bottleneck_pressure": .62}, True, "Demo topology marks Exit C available."),
        ("REDIRECT_FLOW", "Redirect Incoming Flow", {"convergence": .48, "flow_conflict": .62}, state["zones"][3]["relative_density"] < 85, "Destination Zone D must remain below 85% relative occupancy."),
        ("EXIT_AND_REDIRECT", "Open Exit C + Redirect Flow", {"density": .68, "density_growth": .45, "convergence": .40, "flow_conflict": .55, "bottleneck_pressure": .48}, state["zones"][3]["relative_density"] < 85, "Combined egress relief and upstream diversion."),
    ]
    output = []
    for option_id, title, effects, feasible, reason in candidates:
        projected_signals = {key: value * effects.get(key, 1.0) for key, value in ((k, state[k]) for k in RISK_WEIGHTS)}
        projected = _clip(sum(projected_signals[key] * RISK_WEIGHTS[key] for key in RISK_WEIGHTS))
        output.append({"option_id": option_id, "title": title, "current_risk": current, "projected_risk": projected, "risk_reduction": round(current-projected, 2), "risk_reduction_percent": round((current-projected)/current*100, 1) if current else 0.0, "feasible": feasible, "feasibility_reason": reason, "simulation_only": True})
    feasible_options = [item for item in output if item["feasible"]]
    if feasible_options:
        if current < 30:
            next(item for item in feasible_options if item["option_id"] == "MONITOR")["recommended"] = True
        else:
            min((item for item in feasible_options if item["option_id"] != "MONITOR"), key=lambda item: item["projected_risk"])["recommended"] = True
    for item in output: item.setdefault("recommended", False)
    return sorted(output, key=lambda item: (not item["feasible"], item["projected_risk"]))
