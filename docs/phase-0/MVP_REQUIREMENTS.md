# CROWD-SHIELD: MVP Functional & Non-Functional Requirements
**Document ID:** CS-DOC-P0-02  
**Version:** 1.0.0 (Phase 0 Baseline)  
**Status:** APPROVED & LOCKED  
**Module:** System Requirements Specification (SRS)  

---

## 1. Input Specifications

### 1.1 Ingestion Sources
The system accepts inputs across three primary channels without requiring specialized proprietary camera SDKs or physical edge devices:

| Input Channel | Data Format / Type | Specifications & Constraints | Fallback / Default Mode |
|---|---|---|---|
| **A. Video Stream / File** | MP4, WebM, H.264 video file; Simulated loop feed; Optional USB WebCam | Resolution: $720p$ to $1080p$ at $15\text{--}30\text{ fps}$. Single camera viewpoint mapped to defined venue zone. | Bundled sample test clips (Normal, High Density, Bottleneck, Flow Conflict). |
| **B. Venue Model Definition** | JSON configuration file (`venue_config.json`) | Geometric coordinates, zone polygons, rated max capacities ($C_{\text{max}}$), interconnecting gates/corridors, and egress width factors. | Default benchmark stadium / festival concourse layout with 4 zones, 2 entry gates, 2 emergency exits. |
| **C. Simulated Context Stream** | JSON / WebSocket stream payload | Real-time entry rate ($\text{pax/min}$), exit open/closed status, gate flow restrictors, weather/lighting conditions. | Synthetic deterministic generator producing repeatable, testable risk escalations. |

---

## 2. Output Specifications & Contract

The CROWD-SHIELD core engine emits a unified telemetry payload every $500\text{--}1000\text{ ms}$ containing:

```json
{
  "timestamp": "2026-08-20T19:30:00.000Z",
  "frame_id": 482,
  "venue_summary": {
    "total_estimated_occupancy": 3420,
    "global_risk_score": 78,
    "risk_level": "CRITICAL",
    "risk_trajectory": "RAPIDLY_INCREASING",
    "trajectory_trend_slope": 0.84,
    "confidence_score": 0.92,
    "critical_zone_id": "ZONE_B"
  },
  "zone_telemetry": [
    {
      "zone_id": "ZONE_B",
      "zone_name": "Main Stage Concourse",
      "estimated_count": 1280,
      "capacity": 1000,
      "capacity_utilization": 1.28,
      "density_sqm": 6.4,
      "flow_rate_mps": 0.35,
      "flow_convergence_index": 0.89,
      "bottleneck_pressure_index": 0.94,
      "zone_risk_score": 86,
      "risk_status": "CRITICAL"
    }
  ],
  "interventions": {
    "baseline_risk": 86,
    "evaluated_options": [
      {
        "option_id": "OPT_01",
        "action_title": "Close Gate A (Inflow Restriction Only)",
        "projected_risk": 91,
        "risk_delta": +5,
        "status": "REJECTED",
        "feasibility": false,
        "reason": "Traps existing crowd and exacerbates internal chokepoint"
      },
      {
        "option_id": "OPT_02",
        "action_title": "Open Emergency Exit C",
        "projected_risk": 57,
        "risk_delta": -29,
        "status": "FEASIBLE",
        "feasibility": true,
        "reason": "Provides egress path; evacuates 400 pax/min"
      },
      {
        "option_id": "OPT_03",
        "action_title": "Redirect Incoming Flow via Corridor D",
        "projected_risk": 43,
        "risk_delta": -43,
        "status": "FEASIBLE",
        "feasibility": true,
        "reason": "Halts inflow into critical Zone B without trapping perimeter"
      },
      {
        "option_id": "OPT_04",
        "action_title": "Open Exit C + Redirect Inflow to Corridor D",
        "projected_risk": 29,
        "risk_delta": -57,
        "status": "RECOMMENDED",
        "feasibility": true,
        "reason": "Optimal combination: reduces pressure by 66% within safe egress margins"
      }
    ],
    "top_recommendation": {
      "option_id": "OPT_04",
      "action_title": "Open Exit C + Redirect Inflow to Corridor D",
      "urgency": "HIGH",
      "estimated_relief_time_seconds": 180,
      "human_approval_required": true
    }
  }
}
```

---

## 3. Functional Requirements (FR)

### FR-01: Anonymous Perception Engine
- **FR-1.1:** System shall ingest video frames at minimum $10\text{ fps}$ without frame queue blocking.
- **FR-1.2:** System shall perform anonymous person/head detection using YOLOv8n/YOLOv8s bounding boxes.
- **FR-1.3:** System shall discard frame-level visual biometric tokens immediately after centroid and bounding box computation.
- **FR-1.4:** System shall aggregate bounding boxes into spatial heatmaps overlaid on the coordinate space of the venue.

### FR-02: Crowd State Engine
- **FR-2.1:** System shall compute instantaneous head count and estimated density (people/$m^2$) for each defined polygon zone.
- **FR-2.2:** System shall compute velocity vectors via Farneback dense optical flow / centroid displacement.
- **FR-2.3:** System shall calculate **Flow Convergence Index** (vectors pointing inward toward a common node) and **Flow Conflict Index** (opposing vectors $\approx 180^\circ$).
- **FR-2.4:** System shall measure **Bottleneck Pressure** as a function of incoming flux vs. available exit cross-sectional capacity.

### FR-03: Contextual Risk Engine
- **FR-3.1:** System shall combine Density Factor ($W_d$), Flow Conflict Factor ($W_f$), Capacity Utilization ($W_c$), and Bottleneck Pressure ($W_b$) into a normalized risk score ($0\text{--}100$).
- **FR-3.2:** System shall map risk scores into calibrated visual tiers:
  - **$0\text{--}30$ (SAFE - Green):** Normal fluid movement, occupancy $< 70\%$ rated capacity.
  - **$31\text{--}55$ (WATCH - Yellow):** Density rising, minor turbulence, occupancy $70\text{--}85\%$.
  - **$56\text{--}75$ (HIGH - Orange):** Significant turbulence, speed drop $<0.5\text{ m/s}$, occupancy $85\text{--}105\%$.
  - **$76\text{--}100$ (CRITICAL - Red):** Stop-and-go shockwaves, high opposing vectors, occupancy $>105\%$.

### FR-04: Risk Trajectory Engine
- **FR-4.1:** System shall compute a sliding temporal window ($T = 30\text{ seconds}$) of risk scores.
- **FR-4.2:** System shall calculate the 1st derivative (slope $dR/dt$) to classify the trajectory into:
  - `DECREASING` ($dR/dt < -0.15$)
  - `STABLE` ($-0.15 \le dR/dt \le +0.15$)
  - `INCREASING` ($+0.15 < dR/dt \le +0.50$)
  - `RAPIDLY_INCREASING` ($dR/dt > +0.50$)
- **FR-4.3:** System shall project risk 60 seconds into the future based on linear-exponential autoregression of historical trend features.

### FR-05: Intervention Simulator & Feasibility Engine
- **FR-5.1:** System shall maintain a discrete operational intervention space per venue configuration:
  - Gate throttling ($100\% \to 50\% \to 0\%$)
  - Emergency exit opening ($0\% \to 100\%$)
  - Dynamic corridor diversion (rerouting incoming directed edges in the graph)
  - Combined multi-action topologies.
- **FR-5.2:** For each candidate intervention, the system shall simulate the post-action flow redistribution using a network capacity flux model.
- **FR-5.3:** The feasibility engine shall strictly evaluate:
  - **Egress availability:** Is the designated exit operational?
  - **Downstream safety:** Will diverting Zone B crowd cause Zone C to exceed $100\%$ capacity?
  - **Emergency route preservation:** Does the intervention preserve dedicated clear corridors for emergency responders?
- **FR-5.4:** The system shall reject infeasible options with explicit human-readable operational rationale.
- **FR-5.5:** The system shall select the **Safest Feasible Action** (maximizing $\Delta R_{\text{reduction}}$ while maintaining zero constraint violations).

### FR-06: Human-in-the-Loop (HITL) Decision Support UI
- **FR-6.1:** System UI shall display the top recommended action in a high-visibility, dedicated decision banner.
- **FR-6.2:** System UI shall present interactive **[APPROVE ACTION]** and **[REJECT / OVERRIDE]** controls.
- **FR-6.3:** Upon operator approval, the system shall transition the simulated venue state into "Action Executing" and track real-time risk dissipation vs. projected trajectory.
- **FR-6.4:** System shall log all operator decisions, timestamps, and overrides into an audit log for post-event analysis.

---

## 4. Non-Functional Requirements (NFR)

| Category | Metric / Requirement | Target Baseline for 2-Day MVP |
|---|---|---|
| **Performance** | Video Processing Latency | $\le 100\text{ ms}$ per processed frame ($10\text{ fps}$ continuous throughput) |
| **Responsiveness** | UI Telemetry Refresh Rate | $\le 500\text{ ms}$ latency via WebSocket / Fast HTTP Polling |
| **Simulation Speed** | Intervention Computation | $\le 250\text{ ms}$ to evaluate all 4 candidate scenarios |
| **Privacy & Security** | Data Retention & Anonymity | Zero face images or persistent identity embeddings stored to disk. Local processing only. |
| **Reliability** | Fault Tolerance & Fallback | Graceful fallback to synthetic data generator if video feed is interrupted. |
| **Portability** | Zero-Cloud Self-Contained | Can run fully locally on developer workstation with standard CPU/GPU. |
| **Usability** | Visual Clarity | Dark navy emergency management theme with instant 5-second situational comprehension. |

---

## 5. Requirements Sign-Off
- **Requirements Freeze Status:** 100% COMPLETE & LOCKED FOR PHASE 1–10 IMPLEMENTATION.
