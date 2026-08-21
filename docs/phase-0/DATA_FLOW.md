# CROWD-SHIELD: End-to-End Data Flow & Lifecycle
**Document ID:** CS-DOC-P0-04  
**Version:** 1.0.0 (Phase 0 Baseline)  
**Status:** APPROVED & LOCKED  
**Module:** System Data Lifecycle & Pipeline Flow  

---

## 1. Sequence & Data Lifecycle Diagram

```
[Camera/File] ──(Raw Frame: RGB)──► [YOLO Detector] ──(Centroids: [x,y])──┐
                                                                           ├─► [Crowd State Engine]
[Frame Pair]  ──(Optical Flow)────► [Vector Field]  ──(Velocities: [u,v])─┘           │
                                                                                      │ (Density, Flow, Instability)
                                    [Venue Config]  ──(Graph: Nodes, Edges)───────────┤
                                                                                      ▼
                                                                        [Contextual Risk Engine]
                                                                                      │ (Risk Score: 0-100)
                                                                                      ▼
                                                                        [Risk Trajectory Engine]
                                                                                      │ (Trend: Rapidly Increasing)
                                                                                      ▼
                                                                        [Intervention Simulator]
                                                                                      │ (Candidate Options 1..4)
                                                                                      ▼
                                                                        [Feasibility & Safety Layer]
                                                                                      │ (Validates Routes & Overloads)
                                                                                      ▼
                                                                        [Recommendation Engine]
                                                                                      │ (Top Feasible Action)
                                                                                      ▼
                                                                        [Human Operator Dashboard]
                                                                                      │
                                                           ┌──────────────────────────┴──────────────────────────┐
                                                           ▼                                                     ▼
                                                   [APPROVE ACTION]                                      [REJECT / OVERRIDE]
                                                           │                                                     │
                                                           ▼                                                     ▼
                                                 [Execute Simulation]                                   [Log In Audit Trail]
                                                           │
                                                           ▼
                                               [Feedback Monitor Loop]
                                           (Track Actual ΔR vs Simulated)
```

---

## 2. Step-by-Step Data Transformations

### Step 1: Video Ingestion & Frame Preprocessing
- **Input:** Video stream or file frame $I_t \in \mathbb{R}^{H \times W \times 3}$ at timestamp $t$.
- **Transformation:** Resized to standardized inference resolution ($640 \times 640$).
- **Output:** Normalized frame tensor $\hat{I}_t$.

### Step 2: Anonymous Perception Processing
- **Sub-step 2A (Centroid Detection):** YOLO generates bounding boxes $B = \{ (x_{\min}, y_{\min}, x_{\max}, y_{\max})_i \}_{i=1}^N$. Centroids $c_i = \left(\frac{x_{\min}+x_{\max}}{2}, \frac{y_{\min}+y_{\max}}{2}\right)$ are calculated.
- **Sub-step 2B (Velocity Vector Field):** Dense optical flow between $\hat{I}_{t-1}$ and $\hat{I}_t$ produces velocity field $(U, V)$ where $U(x, y) = \Delta x / \Delta t$ and $V(x, y) = \Delta y / \Delta t$.
- **Privacy Sanitization:** Raw bounding box crops and frame pixels are purged from memory; only spatial coordinates $c_i$ and vector components $(u_i, v_i)$ persist.

### Step 3: Venue Topology Fusion & Zone Aggregation
- **Input:** Centroids $\{c_i\}$, vectors $\{(u_i, v_i)\}$, and venue polygonal zones $Z_k$.
- **Spatial Binning:** Point-in-polygon test maps each centroid $c_i$ to its corresponding zone $Z_k$.
- **State Output per Zone $Z_k$:**
  - $N_k$: Instantaneous person count.
  - $\rho_k = N_k / \text{Area}(Z_k)$: Zone density ($\text{people}/m^2$).
  - $\bar{v}_k = \frac{1}{N_k}\sum_{i \in Z_k} \sqrt{u_i^2 + v_i^2}$: Mean movement speed.
  - $\theta_k = \operatorname{Var}\left(\operatorname{atan2}(v_i, u_i)\right)$: Angular variance (turbulence indicator).
  - $C_k = N_k / C_{\max, k}$: Capacity utilization percentage.

### Step 4: Contextual Risk Calculation
- The Contextual Risk Engine calculates composite risk $R_k(t) \in [0, 100]$:
  $$R_k(t) = \min\left(100, \, \Big(w_1 \cdot \tilde{\rho}_k + w_2 \cdot \tilde{C}_k + w_3 \cdot \tilde{\theta}_k + w_4 \cdot \tilde{B}_k\Big) \times 100\right)$$
  Where $\tilde{B}_k$ represents the bottleneck pressure (ratio of incoming flux to available exit width).

### Step 5: Trajectory Forecasting
- Rolling history of risk scores for zone $k$: $\mathcal{H}_k = \{ R_k(t - M\Delta t), \dots, R_k(t) \}$.
- First derivative $S_k = \frac{d R_k}{dt}$ computed via Savitzky-Golay smoothed linear regression.
- Forecast $\hat{R}_k(t + 60\text{s}) = R_k(t) + S_k \times 60$.

### Step 6: Intervention Simulation & What-If Branching
- The simulator evaluates candidate tactical actions $\mathcal{A} = \{a_0, a_1, a_2, a_3, a_4\}$:
  - $a_0$: Do Nothing (Baseline status quo).
  - $a_1$: Close Gate A (Inflow throttle).
  - $a_2$: Open Emergency Exit C (Outflow relief).
  - $a_3$: Reroute incoming flow via alternate Corridor D.
  - $a_4$: Combined action (Open Exit C + Reroute).
- For each action $a_j$, the graph flow algorithm recalculates the steady-state flux $\phi_{ij}$ and projects post-intervention risk $R_k^{\text{sim}}(a_j)$.

### Step 7: Feasibility Validation & Ranking
- Feasibility constraints evaluated:
  1. Exit accessibility status ($E_{\text{status}} == \text{AVAILABLE}$).
  2. Downstream capacity headroom: $\forall m \neq k, \, C_m^{\text{sim}} \le 1.0$.
  3. Evacuation path clearance for emergency responders.
- Ranks valid options by $\Delta R = R_k^{\text{baseline}} - R_k^{\text{sim}}$. Selects option with highest positive $\Delta R$ satisfying all feasibility checks.

### Step 8: Human-in-the-Loop Operator Interaction
- The recommendation is sent to the Tactical Dashboard.
- When the human operator clicks **[APPROVE ACTION]**:
  - A timestamped decision record is appended to the audit ledger.
  - The digital venue model updates active routing topologies.
  - The system initiates Step 9 (Feedback Monitoring).

### Step 9: Closed-Loop Feedback Monitoring
- Tracks actual measured risk $R_k(t + \tau)$ vs. simulated projection $R_k^{\text{sim}}$.
- Discrepancy metric $\epsilon = |R_k(t+\tau) - R_k^{\text{sim}}|$ is computed to validate model calibration in real time.
