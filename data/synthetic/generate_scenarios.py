"""
Synthetic Crowd Scenario Generator for CROWD-SHIELD MVP.

DISCLAIMER: This dataset is synthetic and is used for prototype validation
and demonstration of the crowd-risk and intervention engine. It does not
represent measurements from a real incident.

Generates three deterministic scenarios:
  SAFE        – stable low-pressure crowd
  ESCALATING  – gradually increasing pressure toward HIGH risk
  CRITICAL    – rapid buildup toward CRITICAL risk

Each scenario contains ~60 timestamped records at 5-second intervals
(total ~5 minutes of simulated time).

Usage:
    python generate_scenarios.py          # writes synthetic_crowd_scenarios.json
    python generate_scenarios.py --csv    # also writes .csv
"""

from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np


SCENARIOS = ["SAFE", "ESCALATING", "CRITICAL"]
ZONES = ["ZONE_A", "ZONE_B", "ZONE_C", "ZONE_D"]
DURATION_SEC = 300  # 5 minutes
STEP_SEC = 5        # 5-second intervals
NUM_STEPS = DURATION_SEC // STEP_SEC  # 60 steps


def _smooth_ramp(t: float, start: float, end: float, noise_std: float, rng: np.random.Generator) -> float:
    """Smooth sigmoid-ish ramp from start to end over t in [0, 1], with small noise."""
    # Use a smoothstep for natural-looking progression
    t_clamped = max(0.0, min(1.0, t))
    s = 3 * t_clamped**2 - 2 * t_clamped**3  # smoothstep
    value = start + (end - start) * s + rng.normal(0, noise_std)
    return round(float(np.clip(value, 0, 100)), 2)


def _generate_zone_data(
    scenario: str,
    zone: str,
    rng: np.random.Generator,
) -> list[dict]:
    """Generate temporal progression for one zone in one scenario."""
    records = []

    # Zone-specific multipliers (ZONE_B is the critical bottleneck)
    zone_mult = {"ZONE_A": 0.75, "ZONE_B": 1.0, "ZONE_C": 0.65, "ZONE_D": 0.55}
    zm = zone_mult[zone]

    for step in range(NUM_STEPS):
        t = step / max(1, NUM_STEPS - 1)  # 0 → 1
        timestamp = step * STEP_SEC

        if scenario == "SAFE":
            occupancy = _smooth_ramp(t, 30 * zm, 38 * zm, 1.5, rng)
            density = _smooth_ramp(t, 18 * zm, 22 * zm, 1.2, rng)
            density_growth = _smooth_ramp(t, 3 * zm, 6 * zm, 0.8, rng)
            movement = _smooth_ramp(t, 12 * zm, 18 * zm, 1.0, rng)
            convergence = _smooth_ramp(t, 8 * zm, 12 * zm, 0.8, rng)
            conflict = _smooth_ramp(t, 5 * zm, 8 * zm, 0.6, rng)
            bottleneck = _smooth_ramp(t, 6 * zm, 10 * zm, 0.7, rng)

        elif scenario == "ESCALATING":
            occupancy = _smooth_ramp(t, 35 * zm, 72 * zm, 2.0, rng)
            density = _smooth_ramp(t, 22 * zm, 68 * zm, 2.5, rng)
            density_growth = _smooth_ramp(t, 5 * zm, 55 * zm, 2.0, rng)
            movement = _smooth_ramp(t, 18 * zm, 62 * zm, 2.5, rng)
            convergence = _smooth_ramp(t, 10 * zm, 58 * zm, 2.0, rng)
            conflict = _smooth_ramp(t, 8 * zm, 52 * zm, 2.0, rng)
            bottleneck = _smooth_ramp(t, 8 * zm, 60 * zm, 2.5, rng)

        elif scenario == "CRITICAL":
            # Faster ramp with an acceleration phase
            t_accel = min(1.0, t * 1.3)  # accelerated timeline
            occupancy = _smooth_ramp(t_accel, 40 * zm, 95 * zm, 2.0, rng)
            density = _smooth_ramp(t_accel, 28 * zm, 92 * zm, 2.5, rng)
            density_growth = _smooth_ramp(t_accel, 10 * zm, 88 * zm, 3.0, rng)
            movement = _smooth_ramp(t_accel, 22 * zm, 85 * zm, 3.0, rng)
            convergence = _smooth_ramp(t_accel, 15 * zm, 91 * zm, 2.5, rng)
            conflict = _smooth_ramp(t_accel, 10 * zm, 82 * zm, 2.5, rng)
            bottleneck = _smooth_ramp(t_accel, 12 * zm, 90 * zm, 3.0, rng)
        else:
            raise ValueError(f"Unknown scenario: {scenario}")

        records.append({
            "timestamp": timestamp,
            "scenario": scenario,
            "zone": zone,
            "detected_occupancy": occupancy,
            "density_score": density,
            "density_growth": density_growth,
            "movement_score": movement,
            "convergence_score": convergence,
            "conflict_score": conflict,
            "bottleneck_score": bottleneck,
        })

    return records


def generate_all(seed: int = 42) -> dict:
    """Generate the full synthetic dataset."""
    rng = np.random.default_rng(seed)
    dataset = {
        "metadata": {
            "generator": "CROWD-SHIELD Synthetic Scenario Generator",
            "version": "1.0.0",
            "seed": seed,
            "disclaimer": (
                "This dataset is synthetic and is used for prototype validation "
                "and demonstration of the crowd-risk and intervention engine. "
                "It does not represent measurements from a real incident."
            ),
            "scenarios": SCENARIOS,
            "zones": ZONES,
            "duration_sec": DURATION_SEC,
            "step_sec": STEP_SEC,
            "num_steps": NUM_STEPS,
        },
        "scenarios": {},
    }

    for scenario in SCENARIOS:
        scenario_data = []
        for zone in ZONES:
            scenario_data.extend(_generate_zone_data(scenario, zone, rng))
        # Sort by timestamp, then zone for deterministic ordering
        scenario_data.sort(key=lambda r: (r["timestamp"], r["zone"]))
        dataset["scenarios"][scenario] = scenario_data

    return dataset


def write_json(dataset: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dataset, indent=2), encoding="utf-8")
    print(f"  JSON: {path} ({path.stat().st_size:,} bytes)")


def write_csv(dataset: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "timestamp", "scenario", "zone",
        "detected_occupancy", "density_score", "density_growth",
        "movement_score", "convergence_score", "conflict_score", "bottleneck_score",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for scenario in SCENARIOS:
            writer.writerows(dataset["scenarios"][scenario])
    print(f"  CSV:  {path} ({path.stat().st_size:,} bytes)")


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic crowd scenarios for CROWD-SHIELD")
    parser.add_argument("--csv", action="store_true", help="Also write CSV output")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    output_dir = Path(__file__).parent
    dataset = generate_all(seed=args.seed)

    print("CROWD-SHIELD Synthetic Dataset Generator")
    print("=" * 50)
    write_json(dataset, output_dir / "synthetic_crowd_scenarios.json")
    if args.csv:
        write_csv(dataset, output_dir / "synthetic_crowd_scenarios.csv")

    # Print summary
    for scenario in SCENARIOS:
        records = dataset["scenarios"][scenario]
        last_b = [r for r in records if r["zone"] == "ZONE_B"][-1]
        print(f"\n  {scenario}: {len(records)} records, final ZONE_B density={last_b['density_score']}")

    print("\n[OK] Generation complete")


if __name__ == "__main__":
    main()
