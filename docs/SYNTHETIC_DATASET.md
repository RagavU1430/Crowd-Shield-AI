# CROWD-SHIELD: Synthetic Dataset Documentation
**Document ID:** CS-DOC-SYNTHETIC-01
**Version:** 1.0.0
**Status:** APPROVED

---

## Purpose

The CROWD-SHIELD synthetic crowd scenario dataset provides controlled, reproducible
crowd-state signals for prototype validation and demonstration of the risk engine,
intervention simulator, feasibility checks, and recommendation pipeline.

> **IMPORTANT**: This dataset is synthetic and is used for prototype validation
> and demonstration of the crowd-risk and intervention engine. It does not
> represent measurements from a real incident.

## Scenario Definitions

### SAFE
- **Characteristics**: Stable occupancy, low density, low movement instability,
  low convergence, low conflict, low bottleneck pressure
- **Expected outcome**: Risk generally remains in SAFE tier (0–30)
- **Duration**: 5 minutes (60 timesteps at 5-second intervals)

### ESCALATING
- **Characteristics**: Occupancy gradually increasing, density rising, movement
  becoming unstable, convergence increasing, bottleneck pressure building
- **Expected outcome**: Risk moves from SAFE → WATCH → HIGH over the 5-minute window
- **Duration**: 5 minutes

### CRITICAL
- **Characteristics**: Rapid occupancy increase, high density, high movement
  instability, strong flow convergence, flow conflict, severe bottleneck pressure
- **Expected outcome**: Risk reaches CRITICAL tier (75–100) before the end
- **Duration**: 5 minutes (accelerated progression)

## Feature Descriptions

| Field | Range | Description |
|---|---|---|
| `timestamp` | 0–295 | Seconds from scenario start (5-second intervals) |
| `scenario` | SAFE/ESCALATING/CRITICAL | Scenario identifier |
| `zone` | ZONE_A/B/C/D | Spatial zone within the venue |
| `detected_occupancy` | 0–100 | Estimated number of people in zone |
| `density_score` | 0–100 | Crowd density pressure signal |
| `density_growth` | 0–100 | Rate of density increase |
| `movement_score` | 0–100 | Movement instability signal |
| `convergence_score` | 0–100 | Flow convergence toward chokepoints |
| `conflict_score` | 0–100 | Opposing movement directions |
| `bottleneck_score` | 0–100 | Chokepoint pressure signal |

## Zone Layout

```
┌──────────┬──────────┐
│  ZONE A  │  ZONE B  │   ← ZONE B is the critical
│  (0.75x) │  (1.0x)  │     bottleneck candidate
├──────────┼──────────┤
│  ZONE C  │  ZONE D  │   ← ZONE D is the bypass/
│  (0.65x) │  (0.55x) │     redirect destination
└──────────┴──────────┘
```

Zone multipliers control relative pressure:
- **ZONE_B** (1.0x): Primary bottleneck, receives highest pressure
- **ZONE_A** (0.75x): Secondary area
- **ZONE_C** (0.65x): Lower pressure zone
- **ZONE_D** (0.55x): Bypass corridor with lowest pressure

## Generation Method

1. **Algorithm**: Smoothstep function `3t² - 2t³` for natural S-curve progression
2. **Noise**: Gaussian noise with scenario-specific standard deviation
3. **Zone differentiation**: Per-zone multipliers applied to base signals
4. **Acceleration** (CRITICAL only): Time factor accelerated by 1.3x
5. **Seed**: Default seed = 42 for full reproducibility

## Reproducibility

```bash
# Regenerate the dataset (produces identical output)
python data/synthetic/generate_scenarios.py --seed 42

# Also generate CSV format
python data/synthetic/generate_scenarios.py --csv --seed 42
```

## Assumptions

- Signals are abstract normalized values (0–100), not physical measurements
- Zone multipliers are heuristic, not based on real venue calibration
- Temporal progression follows smoothstep curves, not real crowd dynamics models
- The dataset serves as a controlled input for validating the decision pipeline

## Limitations

- Does not capture real crowd behavior variability
- Does not model complex multi-zone interactions
- Does not account for weather, event type, or demographic factors
- Signal correlations are simplified (independence assumption)
- Not validated against real crowd-safety incidents

## Risk Formula

The SAME risk formula is used for both real video analysis and synthetic scenarios:

```
Risk = 0.25 × density
     + 0.15 × density_growth
     + 0.15 × movement_instability
     + 0.15 × flow_conflict
     + 0.15 × convergence
     + 0.15 × bottleneck_pressure
```

Risk levels:
- **SAFE**: 0–29
- **WATCH**: 30–54
- **HIGH**: 55–74
- **CRITICAL**: 75–100

## Integration with CROWD-SHIELD

The synthetic dataset feeds into the same pipeline as real video observations:

```
Synthetic Dataset → CrowdState Schema → Risk Engine → Intervention Simulator
                                                     → Feasibility Engine
                                                     → Recommendation Engine
                                                     → Human Approval
```

This architecture proves that the decision pipeline works independently of the
perception layer, enabling validation without requiring annotated intervention data.
