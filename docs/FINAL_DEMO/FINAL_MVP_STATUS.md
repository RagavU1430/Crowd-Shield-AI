# CROWD-SHIELD Final MVP Status

Status date: 2026-08-21  
Overall: **READY** for a local hackathon demonstration.

## Judge-ready experience

The working application now provides a single-screen story:

1. Upload and validate a crowd video.
2. Review filename, duration, resolution, FPS, and frame count.
3. Start an actual asynchronous YOLO analysis or select the explicitly labelled demo/simulation mode.
4. View detected people, relative density, movement, flow convergence/conflict, bottleneck pressure, risk trajectory, and critical logical zone.
5. Compare multiple simulation-only interventions and their feasibility.
6. Review the best feasible recommendation.
7. Approve, then Confirm/Cancel the simulated intervention.
8. View a strong Before → Action → After simulated result.

## Final acceptance status

| Capability | Status |
|---|---|
| Video upload and validation | PASS |
| Explicit analyzing workflow | PASS |
| Crowd-specific YOLOv8n with pretrained fallback | PASS |
| Person counts and confidence | PASS |
| Estimated relative density and trend | PASS |
| Movement magnitude/direction and availability | PASS |
| Flow convergence and conflict | PASS |
| Bottleneck pressure | PASS |
| Explainable contextual risk | PASS |
| Risk trajectory | PASS |
| Critical logical zone | PASS |
| What-if interventions | PASS |
| Feasibility filtering | PASS |
| Best-feasible recommendation | PASS |
| Human approval confirmation | PASS |
| Simulated post-action state | PASS |
| Normal-mode computed values only | PASS |
| Demo/simulation provenance | PASS |
| Retrospective incident disclaimer | PASS |
| Privacy/no identity tracking | PASS |
| Phase 1 regression | PASS |
| Restarted end-to-end repeat | PASS |

## How to run

From the project root:

```powershell
cd frontend
npm run dev
```

Open `http://localhost:5173`. The launcher starts the CUDA-ready FastAPI backend on port 8010 and Vite on port 5173. If the same healthy instance is already running, the command reports that fact and exits successfully instead of raising a port conflict.

Recommended judge video: `videos/2026-08-20 21-32-40.mp4`.

## Safety and interpretation

CROWD-SHIELD is an explainable crowd-safety decision-support prototype that evaluates observable crowd conditions, simulates possible interventions, checks their feasibility, and recommends a feasible action to a human operator. It does not detect or identify a “stampede,” establish causality, identify people, predict guaranteed outcomes, or control physical infrastructure.

Density is relative image-space density. Risk thresholds and intervention effects are prototype constructs. Every post-action result is explicitly labelled **SIMULATED RESULT — NOT A REAL-WORLD ACTION**.
