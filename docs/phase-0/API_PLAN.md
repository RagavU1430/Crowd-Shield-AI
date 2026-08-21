# CROWD-SHIELD: API Design & Interface Specifications
**Document ID:** CS-DOC-P0-05  
**Version:** 1.0.0 (Phase 0 Baseline)  
**Status:** APPROVED & LOCKED  
**Module:** Backend API Contract (FastAPI)  

---

## 1. Overview
The CROWD-SHIELD backend exposes RESTful endpoints for configuration, manual control, scenario injection, and human-in-the-loop decisions, combined with high-frequency WebSocket streaming for real-time telemetry and video overlay feeds.

---

## 2. Endpoint Catalog

### 2.1 System & Health Endpoints
- `GET /api/v1/health`  
  **Description:** Returns backend status, GPU/CPU inference availability, and active scenario info.

### 2.2 Video & Scenario Ingestion
- `POST /api/v1/video/upload`  
  **Payload:** `multipart/form-data` with `file: UploadFile`.  
  **Response:** Video metadata, duration, resolution, and assigned `session_id`.
- `POST /api/v1/scenario/load`  
  **Payload:** `{ "scenario_id": "SCENARIO_STAGE_SURGE_01" }`.  
  **Response:** Pre-configured benchmark video and venue topology loaded.

### 2.3 Venue & Topology Configuration
- `GET /api/v1/venue/current`  
  **Response:** Complete JSON venue graph (zones, vertices, gates, exits, nominal capacities).
- `PUT /api/v1/venue/gate/{gate_id}/status`  
  **Payload:** `{ "is_open": true, "capacity_flow_rate": 500 }`.  
  **Response:** Updated gate status.

### 2.4 Telemetry & Live State (WebSocket & REST)
- `WS /api/v1/ws/telemetry`  
  **Description:** Bidirectional WebSocket streaming telemetry at $2\text{--}5\text{ Hz}$.
  **Outbound Message Schema:**
  ```json
  {
    "timestamp": "2026-08-20T19:35:10.500Z",
    "frame_index": 540,
    "global_risk": 86,
    "status": "CRITICAL",
    "trajectory": "RAPIDLY_INCREASING",
    "zones": [
      {
        "id": "ZONE_B",
        "name": "Zone B (Front Concourse)",
        "occupancy": 1280,
        "capacity": 1000,
        "density_sqm": 6.4,
        "speed_mps": 0.35,
        "risk_score": 86,
        "status": "CRITICAL"
      }
    ],
    "critical_zone": "ZONE_B",
    "active_recommendation_id": "OPT_04"
  }
  ```

### 2.5 Simulation & Decision Support
- `POST /api/v1/simulation/evaluate`  
  **Description:** Triggers instantaneous evaluation of all candidate interventions against the current crowd state.  
  **Response:**
  ```json
  {
    "baseline_risk": 86,
    "critical_zone": "ZONE_B",
    "evaluated_options": [
      {
        "option_id": "OPT_01",
        "title": "Close Gate A (Inflow Restriction)",
        "projected_risk": 91,
        "risk_delta": +5,
        "feasibility": false,
        "reason": "Exacerbates internal zone bottleneck",
        "status_color": "RED"
      },
      {
        "option_id": "OPT_02",
        "title": "Open Exit C",
        "projected_risk": 57,
        "risk_delta": -29,
        "feasibility": true,
        "reason": "Evacuates 400 pax/min to safe outer perimeter",
        "status_color": "YELLOW"
      },
      {
        "option_id": "OPT_03",
        "title": "Redirect Incoming Flow via Corridor D",
        "projected_risk": 43,
        "risk_delta": -43,
        "feasibility": true,
        "reason": "Prevents upstream convergence into Zone B",
        "status_color": "GREEN"
      },
      {
        "option_id": "OPT_04",
        "title": "Open Exit C + Redirect Incoming Flow",
        "projected_risk": 29,
        "risk_delta": -57,
        "feasibility": true,
        "reason": "Optimal combination: balanced inflow diversion + rapid egress",
        "status_color": "GREEN",
        "is_recommended": true
      }
    ]
  }
  ```

### 2.6 Human-in-the-Loop Decision & Audit
- `POST /api/v1/decision/submit`  
  **Payload:**
  ```json
  {
    "option_id": "OPT_04",
    "decision": "APPROVE", // or "REJECT" / "OVERRIDE"
    "operator_id": "OP_COMMAND_01",
    "override_notes": null,
    "timestamp": "2026-08-20T19:36:00.000Z"
  }
  ```
  **Response:**
  ```json
  {
    "status": "RECORDED",
    "applied_action": "OPT_04",
    "feedback_monitoring_active": true,
    "audit_id": "AUDIT_20260820_004"
  }
  ```

- `GET /api/v1/decision/audit-log`  
  **Response:** Chronological ledger of all operator interventions, timestamps, and model verification deltas.

---

## 3. Data Type Definitions (Pydantic Models Plan)

```python
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class RiskLevel(str, Enum):
    SAFE = "SAFE"
    WATCH = "WATCH"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class TrajectoryTrend(str, Enum):
    DECREASING = "DECREASING"
    STABLE = "STABLE"
    INCREASING = "INCREASING"
    RAPIDLY_INCREASING = "RAPIDLY_INCREASING"

class ZoneTelemetry(BaseModel):
    zone_id: str
    zone_name: str
    estimated_count: int
    capacity: int
    capacity_utilization: float
    density_sqm: float
    flow_rate_mps: float
    flow_convergence_index: float
    bottleneck_pressure_index: float
    zone_risk_score: int
    risk_status: RiskLevel

class InterventionOption(BaseModel):
    option_id: str
    title: str
    projected_risk: int
    risk_delta: int
    feasibility: bool
    reason: str
    status_color: str
    is_recommended: bool = False

class OperatorDecisionRequest(BaseModel):
    option_id: str
    decision: str
    operator_id: str
    override_notes: Optional[str] = None
```
