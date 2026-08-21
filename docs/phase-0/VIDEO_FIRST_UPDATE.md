# CROWD-SHIELD: Video-First Architecture Update
**Document ID:** CS-DOC-P0-12  
**Version:** 1.1.0 (Video-First MVP Alignment)  
**Status:** APPROVED & LOCKED  
**Module:** Input Ingestion & Video-First Processing Architecture  

---

## 1. Rationale: Why Uploaded Video is the Primary MVP Input

In hackathon, research, and early evaluation environments, live direct RTSP CCTV integration is constrained by physical camera access, venue network permissions, and privacy clearances. 

**Architectural Decision:**  
The primary, core MVP input modality for CROWD-SHIELD is **Uploaded Recorded Video** (MP4 / WebM / MOV).  
- **Live CCTV** is modeled as an **Optional Future Input Mode** that connects to the exact same perception and analytics pipeline downstream.
- The pipeline processes uploaded videos deterministically with frame-sampling, metadata extraction, timeline generation, spatial heatmap generation, and counterfactual intervention simulation.

---

## 2. Three Operational Analysis Modes

The system provides three distinct analysis profiles selectable upon video upload:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 SELECT ANALYSIS MODE                                   │
├─────────────────────────┬──────────────────────────────┬───────────────────────────────┤
│  1. STANDARD ANALYSIS   │  2. RETROSPECTIVE INCIDENT   │    3. SIMULATED SCENARIO      │
├─────────────────────────┼──────────────────────────────┼───────────────────────────────┤
│ • General public crowd  │ • Historical recorded event  │ • Benchmark test sequences    │
│   footage & festivals   │   analysis (Research mode)   │   with synthetic surges       │
│ • Real-time density &   │ • Escalation timeline curve  │ • Repeatable edge-case        │
│   kinematic flow metrics│ • Observable risk indicators │   feasibility validation      │
│ • Standard safety alerts│ • Mandatory ethical disclaimer│ • Controlled demo testing    │
└─────────────────────────┴──────────────────────────────┴───────────────────────────────┘
```

### 2.1 Retrospective Incident Analysis Disclaimers & Ethics
When analyzing footage of historical incidents, the system strictly enforces the following scientific guardrails:
- **Badge / Watermark:** Displays `RETROSPECTIVE EVALUATION SCENARIO — RESEARCH PROTOTYPE`.
- **No Causal Determinism:** Does NOT claim the system would have prevented a past real-world tragedy.
- **Terminology:** Outputs `Crowd-risk escalation detected` (e.g. *SAFE → WATCH → HIGH → CRITICAL*) rather than sensationalized labels.
- **Disclaimer Banner:**
  > *"This analysis is a research/prototype assessment of observable crowd dynamics in recorded footage. It does not establish causality, predict what would have happened in real time, or demonstrate that the incident could have been prevented."*

---

## 3. End-to-End Video Processing Pipeline

```
[ Uploaded Video (MP4/WebM) ]
              │
              ▼
[ 1. Video Validation & Metadata Extraction ] (Duration, Resolution, FPS, Codec)
              │
              ▼
[ 2. Intelligent Frame Sampling ] (1–5 fps adaptive sampling for low-latency CPU/GPU execution)
              │
              ▼
[ 3. YOLOv8 Anonymous Person Detector ] (Extracts Bounding Boxes & Head Centroids: (x, y))
              │
              ▼
[ 4. Farneback Optical Flow ] (Computes Velocity Vectors (u, v) & Directional Turbulence)
              │
              ▼
[ 5. Crowd State Engine ] (Computes Density pax/m², Count, Convergence, Bottleneck Pressure)
              │
              ▼
[ 6. Venue Context Fusion ]
      ├── (A) If Venue Config Present ──► Maps Centroids to Zones & Rated Capacities
      └── (B) If Venue Config Missing ──► Video-Only Heatmap (Confidence Adjusted: 65%)
              │
              ▼
[ 7. Contextual Risk Engine ] (Calculates Composite 0–100 Risk Score)
              │
              ▼
[ 8. Risk Trajectory & Timeline ] (Computes dR/dt Slope & Interactive Timestamp Matrix)
              │
              ▼
[ 9. Intervention Simulator ] (Simulates Candidate Tactical Options & Downstream Effects)
              │
              ▼
[ 10. Feasibility & Safety Engine ] (Rejects Infeasible/Overloading Actions with Rationale)
              │
              ▼
[ 11. Tactical Command Dashboard & HITL Interface ] ([APPROVE] / [REJECT / OVERRIDE])
              │
              ▼
[ 12. Final Exportable Summary & Report ] (JSON / CSV Telemetry Export)
```

---

## 4. Dual Venue Operation Modes

1. **Default Benchmark Venue (`VENUE_STADIUM_ARENA_01`):**
   - 4 polygonal zones (`ZONE_A` North Plaza, `ZONE_B` Chokepoint Concourse, `ZONE_C` Exhibition Hall, `ZONE_D` Bypass).
   - 2 entry gates, 2 standard exits, 1 emergency exit (`EXIT_C`), 2 bottlenecks.
   - High confidence ($85\text{--}95\%$).

2. **Video-Only Analysis Mode (No Map Uploaded):**
   - System operates in spatial grid mode without geometric zone constraints.
   - UI displays: `Venue Topology: Unavailable (Video-Only Grid Analysis)`.
   - Confidence adjusted to $60\text{--}70\%$ with explicit advisory.

---

## 5. Summary of Architecture Delta
- **Input Layer:** Added `UploadManager`, `VideoFrameExtractor`, `AsyncProcessingJob` with WebSocket progress updates ($0\% \to 100\%$).
- **Timeline Engine:** Added timestamp indexing enabling users to scrub or click any moment in the video ($t = \text{01:42}$) to view instantaneous detections, flow vectors, and risk contributors.
- **Reporting Engine:** Added JSON/CSV export endpoint (`/api/v1/analysis/export`).
- **All Core Algorithms Preserved:** YOLOv8 anonymous centroids, Farneback optical flow, contextual risk formula ($0\text{--}100$), trajectory slope ($dR/dt$), discrete intervention simulation ($\mathcal{A}$), and HITL operator approval remain 100% intact.
