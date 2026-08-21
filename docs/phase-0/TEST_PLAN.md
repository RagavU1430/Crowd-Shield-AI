# CROWD-SHIELD: Test & Demo Verification Plan
**Document ID:** CS-DOC-P0-11  
**Version:** 1.0.0 (Phase 0 Baseline)  
**Status:** APPROVED & LOCKED  
**Module:** System Verification, Test Scenarios & Demo Script  

---

## 1. Test Strategy & Scope
The verification strategy ensures that each module (perception, state calculation, risk modeling, simulation, and UI) functions deterministically and handles edge cases under live demo conditions.

---

## 2. Benchmark Demonstration Scenarios

| Scenario ID | Scenario Name | Injected Conditions | Expected System Behavior & Recommendation |
|---|---|---|---|
| **SC-01** | **Normal Event Flow** | Density $< 2.0\text{ pax/m}^2$, unidirectional flow, gates normal. | Global Risk: $18\text{--}25$ (`SAFE`). Status: Green. Recommendation: "Normal Monitoring (No Action Required)". |
| **SC-02** | **Concourse Bottleneck & Surge** | Zone B occupancy surges to $1280/1000$, bottleneck pressure $> 0.90$, exit closed. | Global Risk: $86$ (`CRITICAL`). Trajectory: `RAPIDLY_INCREASING`. Critical Zone: Zone B. Evaluates 4 actions; recommends Option 4 (Open Exit C + Divert). |
| **SC-03** | **Gate Closure Test (Infeasible Check)** | Operator tests Option 1 (Close Gate A). | System simulates Risk $= 91$ (Worse). Feasibility engine flags **REJECTED** with rationale: *"Exacerbates internal crowd pressure without relieving chokepoint."* |
| **SC-04** | **Action Execution & De-escalation** | Operator approves Option 4. | Digital venue updates edge flows. Risk begins decreasing on trajectory graph ($86 \to 52 \to 29$). Feedback monitor logs successful resolution. |

---

## 3. End-to-End Live Hackathon Demonstration Script (Judge Walkthrough)

1. **Step 1: Introduction & Problem Context (15s)**
   - Show the Tactical Command Dashboard in idle mode.
   - Explain: *"Existing systems alert when a crowd is already dense. CROWD-SHIELD models evolving risk and recommends the safest feasible intervention."*
2. **Step 2: Video Stream & Anonymous Perception (20s)**
   - Load Scenario SC-02 (Concourse Surge).
   - Point out anonymous bounding boxes and optical flow velocity vectors.
   - Emphasize zero-PII and anonymous spatial metrics.
3. **Step 3: Risk Trajectory & Critical Zone Identification (20s)**
   - Highlight Zone B turning **RED** as density ($6.4\text{ pax/m}^2$) and bottleneck pressure spike.
   - Show the Risk Gauge jumping to **86 / 100** with trend **↑ RAPIDLY INCREASING**.
4. **Step 4: The Core Differentiator — What-If Intervention Simulation (30s)**
   - Point to the **Intervention Matrix**:
     - *Option 1 (Close Gate A):* Projected Risk = 91 (Rejected).
     - *Option 2 (Open Exit C):* Projected Risk = 57 (Feasible).
     - *Option 3 (Redirect Inflow):* Projected Risk = 43 (Feasible).
     - *Option 4 (Open Exit C + Redirect):* Projected Risk = 29 (Recommended).
   - Explain how the Feasibility Engine verified downstream safety before recommending Option 4.
5. **Step 5: Human-in-the-Loop Approval & Closed-Loop Feedback (20s)**
   - Operator clicks **[APPROVE RECOMMENDATION]**.
   - Confirmation modal logs operator action.
   - The feedback chart dynamically tracks the risk trajectory dropping from $86 \to 29$.
6. **Step 6: Future Vision Summary (15s)**
   - Present the 3-layer future architecture (Drone + Satellite + IoT Smart Gates) clearly delineated as future expansion.
