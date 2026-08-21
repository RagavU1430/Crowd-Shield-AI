# CROWD-SHIELD: Project Scope & Boundaries
**Document ID:** CS-DOC-P0-01  
**Version:** 1.0.0 (Phase 0 Baseline)  
**Status:** LOCKED & FROZEN  
**Project:** CROWD-SHIELD — Context-Aware Predictive Crowd Safety & Intervention System  
**Tagline:** Sense → Predict → Simulate → Recommend → Protect  

---

## 1. Executive Summary & Objective
**CROWD-SHIELD** is an AI-powered, human-in-the-loop crowd safety decision-support system designed to empower venue managers, event organizers, and public safety personnel. Rather than merely detecting high density and firing alarms after critical congestion has occurred, CROWD-SHIELD analyzes anonymous crowd dynamics, combines them with structural venue topologies, projects short-term risk trajectories, simulates what-if intervention outcomes, and recommends the safest feasible intervention to an authorized human operator.

### Formal Objective Statement
> *"Build a prototype decision-support system that can analyze recorded or simulated crowd video, understand crowd density and movement within a defined venue, estimate evolving crowd-crush risk conditions, simulate feasible interventions, and recommend an action to a human operator."*

---

## 2. Core Paradigm Shift
```
TRADITIONAL APPROACH:
[ CCTV ] ───► [ Person Detection ] ───► [ Density Threshold ] ───► [ Reactive Alarm ]
Problem: Tells you "What is happening right now" (often too late, lacks guidance, creates alarm fatigue).

CROWD-SHIELD PARADIGM:
[ Video + Venue Context ] ───► [ Flow & Density Engine ] ───► [ Contextual Risk Engine ] ───► [ Trajectory ]
                                                                                                    │
[ Feedback Loop ] ◄─── [ Human Approval ] ◄─── [ Feasible Recommendation ] ◄─── [ Intervention Sim ] ◄┘
Value: Answers "What is likely to happen next, and what is the safest feasible action right now?"
```

---

## 3. Strict Boundary & Non-Claims Register (Ethical & Technical Guardrails)

To maintain scientific integrity, legal compliance, and technical defensibility, the CROWD-SHIELD system adheres to strict operational boundaries:

| # | What CROWD-SHIELD IS | What CROWD-SHIELD IS NOT (Strict Disclaimers) |
|---|---|---|
| 1 | **Decision-Support Assistant:** Provides validated, risk-ranked recommendations for human review. | **Autonomous Controller:** Will NEVER directly open/close physical gates or trigger alarms without human sign-off. |
| 2 | **Evolving Crowd-Crush Risk Estimator:** Evaluates flow conflicts, bottlenecks, and capacity ratios. | **Guaranteed Stampede Predictor:** Does NOT claim deterministic or 100% predictive guarantee of crowd panics. |
| 3 | **Anonymous Spatial Analyzer:** Measures bounding boxes, centroids, optical flow, and velocity vectors. | **Surveillance / Facial Recognition Tool:** Does NOT track identities, faces, genders, biometrics, or personal profiles. |
| 4 | **Contextual Venue Modeler:** Interprets crowd behavior through digital venue graphs and exit capacities. | **Generic Density Counter:** Does NOT equate raw crowd size alone with danger (density $\neq$ risk). |
| 5 | **Intervention Simulator:** Mathematically projects risk delta ($\Delta R$) across feasible tactical options. | **Disaster Prevention Guarantee:** Does NOT guarantee prevention of historical or real-world tragedies. |
| 6 | **2-Day Hackathon Prototype:** Evaluated on benchmark video datasets, recorded scenarios, and synthetic venues. | **Deployed Production System:** Does NOT claim pre-existing field deployment or multi-agency city integration. |

---

## 4. MVP Scope Definition (Locked for 48-Hour Implementation)

### 4.1 In-Scope Capabilities (The 13 Core Pillars)
1. **Video Ingestion Pipeline:** File upload (MP4/WebM) and simulated streaming feed support.
2. **Anonymous Detection Module:** Pretrained YOLO-based lightweight bounding-box detection (no identity persistence).
3. **Crowd Density Estimation:** Head/body spatial distribution mapping and per-zone occupancy counts.
4. **Movement & Flow Analysis:** Optical flow vectors, direction variance, and velocity convergence modeling.
5. **Venue & Zone Digital Model:** Configurable geometric zones, gates, directional corridors, and nominal capacity thresholds.
6. **Bottleneck & Chokepoint Identification:** Graph-based capacity restriction detection and flow deceleration spotting.
7. **Contextual Crowd-Risk Engine:** Multi-factor scoring ($0\text{--}100$) evaluating density growth, flow conflict, and exit ratios.
8. **Risk Trajectory Engine:** Short-term trend estimation (Stable, Increasing, Rapidly Increasing, Decreasing).
9. **Intervention Simulator:** Discrete what-if evaluation engine simulating flow redirects, gate throttles, and exit releases.
10. **Feasibility & Safety Validation Layer:** Rule-based constraint checker preventing downstream overflow or blocked egress.
11. **Human-in-the-Loop Recommendation Interface:** Clear risk-ranked intervention cards with explicit **[APPROVE]** and **[REJECT]** controls.
12. **Unified Tactical Dashboard:** Synchronized multi-pane UI featuring live heatmap, venue topology, risk telemetry, and action logs.
13. **Feedback Monitoring Loop:** Post-approval simulation vs. actual risk delta tracking for closed-loop validation.

---

## 5. Explicitly Out-of-Scope (Deferred to Future Roadmap)
The following modules are strictly **EXCLUDED** from the 2-day MVP to prevent scope creep:
- ❌ **Aerial Drone Video Ingestion & Telemetry**
- ❌ **Satellite Imagery & Regional Traffic Geospatial Layers**
- ❌ **Telecom Cellular Density & CDR Data Ingestion**
- ❌ **Live Emergency Services (CAD / 911 / Police Radio) Automated Dispatch**
- ❌ **Direct Hardware / IoT Gate Actuator Automation**
- ❌ **Facial Recognition, Re-Identification (ReID), or Demographic Profiling**
- ❌ **Reinforcement Learning Training from Scratch (Online RL Policy Updates)**
- ❌ **Full City-Scale Multi-Venue Digital Twin Orchestration**
- ❌ **Distributed Microservices / Kubernetes Multi-Cluster Deployment**

---

## 6. Approved Standardized Terminology
Team members, API contracts, documentation, and UI components MUST use standard terminology:
- `crowd-crush risk` (avoid sensationalized and excessive use of "stampede")
- `evolving crowd risk` (dynamic multi-temporal risk evaluation)
- `contextual crowd risk` (risk conditioned on spatial venue topology)
- `risk trajectory` (projected direction of crowd instability)
- `intervention recommendation` (AI-formulated mitigation plan)
- `decision support` (software empowering human operators)
- `human-in-the-loop (HITL)` (mandatory operator validation)
- `feasibility constraint` (operational and physical viability check)
- `prototype / simulated scenario` (accurate portrayal of MVP demonstration)

---

## 7. Scope Sign-Off Matrix
- **Lead Software Architect:** APPROVED & LOCKED
- **Hackathon AI Lead:** APPROVED & LOCKED
- **Frontend / UX Lead:** APPROVED & LOCKED
- **Domain Scope Version:** 1.0.0-FINAL-P0
