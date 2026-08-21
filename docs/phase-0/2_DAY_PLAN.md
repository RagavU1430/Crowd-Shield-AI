# CROWD-SHIELD: 48-Hour Hackathon Implementation Plan
**Document ID:** CS-DOC-P0-09  
**Version:** 1.0.0 (Phase 0 Baseline)  
**Status:** APPROVED & LOCKED  
**Module:** Execution Timeline & Phase Roadmap  

---

## 1. 48-Hour Milestone Overview

```
DAY 1: SENSE & UNDERSTAND (Perception, Venue Graph & Risk Pipeline)
Hours 00-04:  Phase 0 (Locked Scope & Architecture) + Phase 1 (Project Scaffold & Environment Setup)
Hours 04-10:  Phase 2 (Video Intelligence & YOLO Ingestion) + Phase 3 (Crowd State & Flow Engine)
Hours 10-16:  Phase 4 (Venue Digital Graph & Zone Model) + Phase 5 (Contextual Risk Engine)
Hours 16-24:  Phase 6 (Risk Trajectory & Trend Engine) + Day 1 Integration Milestone Checkpoint

DAY 2: SIMULATE, RECOMMEND & INTERACT (Intervention Engine & HITL Dashboard)
Hours 24-32:  Phase 7 (Intervention Simulator) + Phase 8 (Feasibility & Safety Validation Layer)
Hours 32-40:  Phase 9 (Tactical Command Dashboard & Human-in-the-Loop Approval UI)
Hours 40-44:  Phase 10 (Closed-Loop Feedback Monitor & Audit Log)
Hours 44-48:  End-to-End Rehearsal, Benchmark Verification, Pitch Polish & Slide Deck Alignment
```

---

## 2. Phase-by-Phase Execution Breakdown

| Phase ID | Phase Name | Primary Deliverables | Target Hour Window |
|---|---|---|---|
| **Phase 0** | **Scope & Architecture Freeze** | Documentation bundle in `/docs/phase-0/`, approved boundaries & non-claims. | **Hours 00–02 (CURRENT)** |
| **Phase 1** | **Project Setup & Scaffolding** | FastAPI backend scaffold, React+Vite frontend skeleton, dependencies setup. | **Hours 02–04** |
| **Phase 2** | **Video Intelligence Layer** | Video upload parser, YOLOv8 anonymous centroid detector, test clip ingestion. | **Hours 04–08** |
| **Phase 3** | **Crowd State Engine** | Density ($pax/m^2$), Farneback optical flow vectors, turbulence and divergence metrics. | **Hours 08–12** |
| **Phase 4** | **Venue Digital Model** | `venue_config.json`, NetworkX graph nodes/edges, zone polygon point-in-polygon mapping. | **Hours 12–15** |
| **Phase 5** | **Contextual Risk Engine** | Multi-factor risk equation ($0\text{--}100$), density + capacity + turbulence weighting. | **Hours 15–18** |
| **Phase 6** | **Risk Trajectory Engine** | Derivative slope $dR/dt$, trend state machine, 60-second autoregressive projection. | **Hours 18–24** |
| **Phase 7** | **Intervention Simulator** | Discrete candidate action space ($\mathcal{A}$), counterfactual network flow redistribution. | **Hours 24–28** |
| **Phase 8** | **Feasibility & Safety Layer** | Egress availability check, downstream capacity safety invariant solver. | **Hours 28–32** |
| **Phase 9** | **HITL Command Dashboard** | React tactical UI, live risk gauge, interactive simulation matrix, [APPROVE] modal. | **Hours 32–40** |
| **Phase 10**| **Feedback & Audit Monitor** | Post-approval $\Delta R$ verification tracker, CSV/JSON audit logger, demo recording. | **Hours 40–44** |
| **Final**  | **Presentation & Polish** | 9-slide proposal deck alignment, live demo rehearsal, fail-safe validation. | **Hours 44–48** |

---

## 3. Critical Path & Contingency Fallback Plan

```
[Phase 1 Setup] ──► [Phase 2 & 3 Perception/State] ──► [Phase 4 & 5 Venue/Risk] ──► [Phase 7 & 8 Sim/Feasibility] ──► [Phase 9 Dashboard]
```

- **Perception Latency Risk:** If YOLO/Optical Flow inference drops below $10\text{ fps}$ on CPU, enable the cached synthetic telemetry stream for the live demo while running inference asynchronously in a background thread.
- **Venue Complexity Risk:** Stick strictly to the standard 4-zone benchmark venue model (`VENUE_STADIUM_ARENA_01`) rather than building a dynamic multi-venue creator during the hackathon.
