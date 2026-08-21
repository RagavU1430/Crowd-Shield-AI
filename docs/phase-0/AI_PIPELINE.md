# CROWD-SHIELD: AI & Computer Vision Pipeline
**Document ID:** CS-DOC-P0-06  
**Version:** 1.0.0 (Phase 0 Baseline)  
**Status:** APPROVED & LOCKED  
**Module:** AI Perception, Flow Analytics & Risk Modeling  

---

## 1. Pipeline Overview

The CROWD-SHIELD AI pipeline operates in four staged layers:
1. **Perception Layer:** Anonymous person/head bounding box detection via YOLOv8.
2. **Kinematic Flow Layer:** Dense optical flow field computation via Farneback algorithm.
3. **Contextual Risk Engine:** Multi-factor spatial-temporal risk scoring ($0\text{--}100$).
4. **Trajectory Forecaster:** First-order differential slope and autoregressive projection.

```
[Raw Frame I(t)] ──► [YOLOv8 Nano] ──► [Centroids (x,y)] ──┐
                                                           ├─► [Crowd State Engine]
[Frame I(t-1)]  ──► [Optical Flow] ──► [Velocity (u,v)]  ──┘           │
                                                                       ▼
                                                          [Contextual Risk Score (0-100)]
                                                                       │
                                                                       ▼
                                                          [Trajectory Trend & Forecast]
```

---

## 2. Layer 1: Anonymous Perception (YOLOv8)

### 2.1 Model Selection & Configuration
- **Model:** `yolov8n.pt` (or `yolov8s.pt` if GPU available).
- **Target Classes:** Class `0` (Person).
- **Confidence Threshold:** $\tau_{\text{conf}} = 0.35$.
- **Intersection over Union (IoU):** $\tau_{\text{iou}} = 0.45$.

### 2.2 Privacy Preservation Protocol
- **Strict Privacy Invariant:** No bounding box image crops, facial landmarks, or ReID feature vectors are stored or transmitted.
- **Centroid Transformation:**
  $$c_i = \left( \frac{x_{\min, i} + x_{\max, i}}{2}, \, y_{\max, i} - 0.85 \cdot h_i \right)$$
  (Using top-center coordinate corresponding to the head region for improved spatial localization).

---

## 3. Layer 2: Kinematic Flow & Spatio-Temporal Turbulence

### 3.1 Farneback Optical Flow Calculation
- Computes velocity components $(u, v)$ for each pixel grid:
  $$\vec{V}(x, y) = \begin{bmatrix} u(x, y) \\ v(x, y) \end{bmatrix}$$
- **Parameters:**
  - `pyr_scale` $= 0.5$, `levels` $= 3$, `winsize` $= 15$, `iterations` $= 3$, `poly_n` $= 5$, `poly_sigma` $= 1.2$.

### 3.2 Key Spatio-Temporal Metrics
1. **Mean Crowd Speed ($\bar{v}_k$):**
   $$\bar{v}_k = \frac{1}{|Z_k|} \sum_{i \in Z_k} \|\vec{V}(c_i)\|$$
2. **Directional Entropy / Turbulence ($\mathcal{T}_k$):**
   Measures irregularity of movement vectors. When people move in a single orderly direction, entropy is near 0. When counter-flows collide, turbulence surges toward 1.0:
   $$\mathcal{T}_k = 1 - \frac{\left\| \sum_{i \in Z_k} \vec{V}(c_i) \right\|}{\sum_{i \in Z_k} \|\vec{V}(c_i)\| + \epsilon}$$
3. **Flow Convergence Index ($\mathcal{C}_k$):**
   Measures inward vector divergence toward a zone bottleneck chokepoint:
   $$\mathcal{C}_k = -\nabla \cdot \vec{V}_{\text{avg}}(Z_k)$$

---

## 4. Layer 3: Contextual Crowd-Risk Engine Formulation

### 4.1 Principle: "Crowd Density $\neq$ Crowd Danger"
A high density in an orderly, slow-moving queue at an amusement park is low danger ($R \approx 25$).  
The same density with opposing flows and a blocked exit is catastrophic danger ($R \approx 90$).

### 4.2 Multi-Factor Risk Equation
For any zone $k$ at time $t$, the composite Contextual Risk Score $R_k(t) \in [0, 100]$ is calculated as:

$$R_k(t) = \text{Clamp}_{[0, 100]}\left( 100 \times \sum_{m=1}^4 w_m \cdot f_m(k, t) \right)$$

Where the normalized factors $f_m \in [0, 1]$ and weights $w_m$ ($\sum w_m = 1.0$) are:

| Factor | Description | Mathematical Expression | Weight ($w$) |
|---|---|---|---|
| **$f_1$: Density Factor** | Normalized crowd density relative to safety threshold ($4\text{ pax}/m^2$) | $f_1 = \min\left(1.0, \, \frac{\rho_k}{\rho_{\text{crit}}}\right)$ where $\rho_{\text{crit}} = 6.0\text{ pax}/m^2$ | $0.25$ |
| **$f_2$: Capacity Ratio** | Current zone occupancy vs. rated design capacity | $f_2 = \min\left(1.0, \, \frac{N_k}{C_{\max, k}}\right)$ | $0.20$ |
| **$f_3$: Turbulence & Conflict** | Opposing velocity angles and kinetic turbulence | $f_3 = \mathcal{T}_k \in [0, 1]$ | $0.30$ |
| **$f_4$: Bottleneck Pressure** | Ratio of incoming flow flux to available egress cross-section | $f_4 = \min\left(1.0, \, \frac{\Phi_{\text{in}, k}}{\Phi_{\text{out, max}, k} + \epsilon}\right)$ | $0.25$ |

### 4.3 Risk Tier Calibration Table

```
Score:    0 ------------ 30 ------------ 55 ------------ 75 ------------ 100
Status:   [    SAFE    ]    [   WATCH    ]    [    HIGH    ]    [  CRITICAL  ]
Color:    #22c55e (Green)   #eab308 (Yel)     #f97316 (Orn)     #ef4444 (Red)
Action:   Normal Ops        Monitor Closely   Stage Interv.     Execute Action
```

---

## 5. Layer 4: Risk Trajectory & Forecasting

### 5.1 Trend Classification
Given a sliding buffer of risk scores $\{ R(t - K\Delta t), \dots, R(t) \}$ over a 30-second window, the slope $S = \frac{dR}{dt}$ is computed via linear least-squares regression:

- **$S < -0.15$:** `DECREASING` (Situation de-escalating)
- **$-0.15 \le S \le +0.15$:** `STABLE` (Steady state)
- **$+0.15 < S \le +0.50$:** `INCREASING` (Crowd gathering, monitor)
- **$S > +0.50$:** `RAPIDLY_INCREASING` (Critical escalation imminent)

### 5.2 Short-Term 60s Projection
$$\hat{R}(t + 60\text{s}) = \text{Clamp}_{[0, 100]}\left( R(t) + S \times 60 \right)$$
*Note: Clearly labeled in UI as "Short-Term Model Projection (Indicative Prototype)*".
