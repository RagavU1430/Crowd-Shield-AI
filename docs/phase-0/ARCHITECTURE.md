# CROWD-SHIELD: System & Component Architecture
**Document ID:** CS-DOC-P0-03  
**Version:** 1.0.0 (Phase 0 Baseline)  
**Status:** APPROVED & LOCKED  
**Module:** System Architecture Design  

---

## 1. High-Level Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                   INPUT & INGESTION LAYER                                │
│   ┌───────────────────────────┐   ┌───────────────────────────┐   ┌──────────────────┐   │
│   │   Recorded CCTV Video     │   │   Venue Config (JSON)     │   │ Synthetic Stream │   │
│   │   (MP4 / WebM / 1080p)    │   │   (Zones, Gates, Exits)   │   │ (Simulated Pax)  │   │
│   └─────────────┬─────────────┘   └─────────────┬─────────────┘   └────────┬─────────┘   │
└─────────────────┼───────────────────────────────┼──────────────────────────┼─────────────┘
                  │                               │                          │
┌─────────────────▼───────────────────────────────▼──────────────────────────▼─────────────┐
│                                    AI & PERCEPTION PIPELINE                              │
│   ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ANONYMOUS DETECTOR: YOLOv8 (Person bounding box & head centroids only)          │   │
│   └─────────────────────────────────────────┬────────────────────────────────────────┘   │
│                                             ▼                                            │
│   ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│   │  SPATIO-TEMPORAL FLOW: Farneback Optical Flow (Velocity Vectors & Direction)     │   │
│   └─────────────────────────────────────────┬────────────────────────────────────────┘   │
└─────────────────────────────────────────────┼────────────────────────────────────────────┘
                                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                   CORE ANALYTICS ENGINES                                 │
│   ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│   │  CROWD STATE ENGINE: Density (pax/m²), Convergence, Turbulence, Bottleneck Ratio │   │
│   └─────────────────────────────────────────┬────────────────────────────────────────┘   │
│                                             ▼                                            │
│   ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│   │  CONTEXTUAL RISK ENGINE: Multi-factor dynamic risk weighting (Score: 0–100)      │   │
│   └─────────────────────────────────────────┬────────────────────────────────────────┘   │
│                                             ▼                                            │
│   ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│   │  RISK TRAJECTORY ENGINE: 1st/2nd derivative slope + 60s Autoregressive Forecast  │   │
│   └─────────────────────────────────────────┬────────────────────────────────────────┘   │
└─────────────────────────────────────────────┼────────────────────────────────────────────┘
                                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                               DECISION SUPPORT & SIMULATION                              │
│   ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│   │  INTERVENTION SIMULATOR: Network flow capacity redistribution (What-if modeling) │   │
│   └─────────────────────────────────────────┬────────────────────────────────────────┘   │
│                                             ▼                                            │
│   ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│   │  FEASIBILITY & SAFETY CHECKER: Boundary constraint & downstream overload solver  │   │
│   └─────────────────────────────────────────┬────────────────────────────────────────┘   │
│                                             ▼                                            │
│   ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│   │  RECOMMENDATION OPTIMIZER: Ranks valid interventions by max safe ΔRisk reduction │   │
│   └─────────────────────────────────────────┬────────────────────────────────────────┘   │
└─────────────────────────────────────────────┼────────────────────────────────────────────┘
                                              ▼
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              HUMAN-IN-THE-LOOP INTERFACE (UI)                            │
│   ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│   │  TACTICAL COMMAND DASHBOARD (React + Leaflet + Tailwind/CSS):                     │   │
│   │  - Zone Risk Heatmap & Direction Vectors                                         │   │
│   │  - Real-Time Risk Gauge & Trend Graph (0–100)                                    │   │
│   │  - Ranked Intervention Cards with Predicted Risk Deltas                          │   │
│   │  - [APPROVE] / [REJECT / OVERRIDE] Operator Controls                             │   │
│   │  - Audit Log & Closed-Loop Feedback Monitor                                      │   │
│   └──────────────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Breakdown & Boundaries

### 2.1 Backend Core (FastAPI Service)
- **`app/core/config.py`**: Application settings, thresholds, and execution modes.
- **`app/api/endpoints/`**:
  - `video.py`: File upload, frame extraction, streaming endpoints.
  - `venue.py`: CRUD and geometric representation of venue nodes, edges, gates, and exits.
  - `telemetry.py`: Real-time WebSocket streaming of processed frame analytics.
  - `simulation.py`: On-demand what-if simulation calculation given current crowd state.
  - `decision.py`: Operator approval/rejection capture, audit logging, and state transition.
- **`app/services/perception/`**:
  - `detector.py`: YOLOv8 wrapper (anonymized centroid generator).
  - `flow_analyzer.py`: Dense optical flow vector extraction and grid pooling.
- **`app/services/analytics/`**:
  - `crowd_state.py`: Zone-level aggregation (density, flow convergence, bottleneck indices).
  - `risk_engine.py`: Contextual multi-factor risk formulation.
  - `trajectory.py`: Trend classification and short-term projection.
- **`app/services/simulation/`**:
  - `network_model.py`: Graph-based venue flow network (NetworkX representation).
  - `simulator.py`: Flow redistribution simulation and projected risk score calculator.
  - `feasibility.py`: Rule-based constraint engine (exit status, route clearance, downstream zone limits).

### 2.2 Frontend Client (React + Vite + Modern Web Tech)
- **`src/components/dashboard/`**:
  - `VideoPlayerWithOverlay.jsx`: Synchronous rendering of video with canvas heatmap and velocity vectors.
  - `VenueMapVisualizer.jsx`: Interactive 2D/isometric layout of venue zones, active gates, and bottleneck hotspots.
  - `RiskTelemetryPanel.jsx`: Live gauge (0–100), status indicator (SAFE, WATCH, HIGH, CRITICAL), and historical sparkline.
  - `InterventionMatrix.jsx`: Comparative cards displaying candidate options with projected risk deltas.
  - `HumanApprovalModal.jsx`: High-visibility operator confirmation dialog with audit metadata.
  - `FeedbackMonitor.jsx`: Real-time tracking of post-approval simulated vs. actual risk dissipation.

---

## 3. Technology Stack & Defensibility Matrix

| Layer | Selected Technology | Alternative Considered | Technical Rationale for Hackathon MVP |
|---|---|---|---|
| **Backend API** | **FastAPI (Python 3.11)** | Flask / Node.js Express | High throughput asynchronous I/O, native Python AI ecosystem integration, automated OpenAPI generation. |
| **Object Detection** | **YOLOv8 Nano / Small (Ultralytics)** | Faster-RCNN / Mask-RCNN | Low-latency inference ($\le 25\text{ ms}$ on CPU/GPU), lightweight memory footprint, reliable person detection. |
| **Flow Dynamics** | **OpenCV Farneback Optical Flow** | Lucas-Kanade / RAFT deep flow | High speed CPU performance, robust direction vector fields, zero custom training overhead. |
| **Graph Network** | **NetworkX / NumPy** | Custom adjacency matrices | Industry-standard graph theory algorithms (shortest path, max flow, cut-set capacity) ready out of the box. |
| **Frontend Framework**| **React 18 + Vite** | Next.js / Pure HTML | Ultra-fast Hot Module Reload (HMR), component-driven tactical dashboard, instant state reactivity. |
| **Map & Overlay** | **HTML5 Canvas + SVG / Leaflet** | Mapbox GL / Deck.gl | Zero API key dependency, lightweight local coordinate mapping, deterministic 2D polygon rendering. |
| **Data Persistence** | **In-Memory Cache + JSON / SQLite** | PostgreSQL / Redis | Zero external database setup overhead for 2-day hackathon; completely portable and deterministic. |

---

## 4. Architectural Invariants & Resilience Principles

1. **Decoupled Perception & Simulation:** If video feed frame rate slows down, the Risk and Intervention engines operate seamlessly using cached state and simulated context.
2. **Fail-Safe Fallback:** The backend provides a built-in `SyntheticScenarioGenerator` that can feed realistic crowd escalation scenarios (e.g. Stage Surge, Gate Congestion) even without an external video file.
3. **Stateless Intervention Calculation:** The simulator computes counterfactual outcomes in pure functional functions without mutating the live tracking state until the operator explicitly approves an action.
4. **Zero-PII Storage:** The perception pipeline only outputs numerical vectors `[x, y, vx, vy]` and polygon aggregations; raw camera frames are discarded immediately after processing.
