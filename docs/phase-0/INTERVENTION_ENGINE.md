# CROWD-SHIELD: Intervention Simulator & Feasibility Engine
**Document ID:** CS-DOC-P0-08  
**Version:** 1.0.0 (Phase 0 Baseline)  
**Status:** APPROVED & LOCKED  
**Module:** Decision Support & Counterfactual Intervention Modeling  

---

## 1. Core Innovation & Purpose

Existing crowd management software stops at **"Detect → Alert"**, leaving emergency managers in a state of high cognitive load during crisis moments without knowing the downstream consequences of tactical actions.

**CROWD-SHIELD transforms this into "Sense → Predict → Simulate → Recommend":**
It evaluates candidate interventions *in silico* on the digital venue graph before recommending the safest, feasible action to the human commander.

```
                  ┌──────────────────────────────────────────────┐
                  │    CURRENT LIVE STATE: Zone B Risk = 86      │
                  └──────────────────────┬───────────────────────┘
                                         │
                 ┌───────────────────────┼───────────────────────┐
                 ▼                       ▼                       ▼
       [ OPTION 1: Close Gate A ] [ OPTION 2: Open Exit C ] [ OPTION 4: Open Exit + Redirect ]
                 │                       │                       │
                 ▼                       ▼                       ▼
         Simulated Risk = 91     Simulated Risk = 57     Simulated Risk = 29
                 │                       │                       │
                 ▼                       ▼                       ▼
          [ ❌ REJECTED ]         [ ⚠️ FEASIBLE ]         [ ✅ BEST RECOMMENDED ]
       (Exacerbates Pressure)   (Relieves 400 pax/min)    (Balanced Safe Clearance)
```

---

## 2. Discrete Intervention Action Space ($\mathcal{A}$)

The prototype engine evaluates five distinct tactical configurations for any critical state:

| Action ID | Action Title | Graph Transformation | Physical Mechanism |
|---|---|---|---|
| **$a_0$** | **Status Quo (Do Nothing)** | Baseline network flow unmodified. | Allows natural crowd accumulation to continue. |
| **$a_1$** | **Inflow Restriction (Close Gate A)** | $\mathcal{C}(\text{Gate A}) \to 0$. | Cuts outer entry; trapped crowd remains stagnant inside. |
| **$a_2$** | **Emergency Egress (Open Exit C)** | $\mathcal{C}(\text{Exit C}) \to 10.0\text{ pax/s}$. | Opens direct pressurized relief valve to safety perimeter. |
| **$a_3$** | **Flow Reroute (Divert to Bypass D)** | Edge weight $(A \to B) \to \infty$, $(A \to D) \to \text{Active}$. | Steers incoming concourse stream away from chokepoint. |
| **$a_4$** | **Synergistic Combo (Open Exit C + Reroute)** | Combined transformations of $a_2$ and $a_3$. | Maximizes outward throughput while stopping new inflow. |

---

## 3. Mathematical Counterfactual Simulation Formulation

For each candidate action $a_j \in \mathcal{A}$, the simulator computes the updated zone density $\hat{\rho}_k(t + \Delta t \mid a_j)$ and flow flux:

$$\hat{\rho}_k(t + \Delta t \mid a_j) = \rho_k(t) + \frac{\Delta t}{\text{Area}(Z_k)} \left[ \sum_{i \in \text{Inlets}(Z_k)} \Phi_{ik}(a_j) - \sum_{m \in \text{Outlets}(Z_k)} \Phi_{km}(a_j) \right]$$

The simulated post-intervention risk $R_k^{\text{sim}}(a_j)$ is then evaluated through the Contextual Risk Engine:
$$R_k^{\text{sim}}(a_j) = \mathcal{F}_{\text{Risk}}\Big(\hat{\rho}_k(a_j), \, \hat{C}_k(a_j), \, \hat{\mathcal{T}}_k(a_j), \, \hat{B}_k(a_j)\Big)$$

---

## 4. Feasibility & Safety Constraint Verification

Before an option can be recommended, it must pass a strict three-tier feasibility filter $\Omega(a_j) \in \{0, 1\}$:

1. **Operational Viability:**
   $$\text{Exit Status Check}(a_j) = \text{True} \iff \text{Exit Door Actuator/Steward is Present and Unblocked}$$
2. **Downstream Safety Buffer (No Risk Shifting):**
   For all neighboring zones $m \neq k$:
   $$\text{Occupancy}_m(a_j) \le 0.85 \times C_{\max, m}$$
   *(If diverting crowd from Zone B causes Zone D to hit 110% capacity, the action is marked INFEASIBLE).*
3. **Emergency Corridor Preservation:**
   $$\text{Width}_{\text{Emergency}}(a_j) \ge 3.0\text{ meters clear}$$

---

## 5. Recommendation Selection Heuristic

The engine selects the optimal recommendation $a^*$ using the **Safest Feasible Optimization (SFO)** policy:

$$a^* = \arg\max_{a_j \in \mathcal{A}} \left\{ \Big( R_k^{\text{baseline}} - R_k^{\text{sim}}(a_j) \Big) \cdot \Omega(a_j) - \lambda \cdot \text{Complexity}(a_j) \right\}$$

- **Guarantees:**
  - Infeasible options are mathematically zeroed out.
  - Recommends the action with the greatest risk reduction $\Delta R$ that preserves safety margins across the entire venue.
  - Human operator retains full authority to approve, reject, or manually override.
