# CROWD-SHIELD: Risk Register & Mitigation Strategy
**Document ID:** CS-DOC-P0-10  
**Version:** 1.0.0 (Phase 0 Baseline)  
**Status:** APPROVED & LOCKED  
**Module:** Technical, Operational & Ethical Risk Analysis  

---

## 1. Comprehensive Risk Matrix

| Risk ID | Category | Risk Description | Severity | Likelihood | Mitigation Strategy & Safeguard |
|---|---|---|---|---|---|
| **TR-01** | **Performance** | High-resolution video inference slows down on CPU-only machines ($\le 5\text{ fps}$). | HIGH | MEDIUM | 1. Use YOLOv8 Nano (`yolov8n.pt`).<br>2. Downsample frames to $640 \times 640$.<br>3. Process optical flow on every 3rd frame with temporal interpolation.<br>4. Implement async background frame pipeline. |
| **TR-02** | **Data & Sensitivity** | Real crowd crush footage is ethically sensitive, sparse, or occluded. | HIGH | HIGH | 1. Strictly utilize open academic crowd datasets (ShanghaiTech, UCF-QNRF, VisDrone).<br>2. Support synthetic scenario injection with deterministic parameters.<br>3. Do NOT scrape or display real tragedy footage. |
| **TR-03** | **Perception Occlusion** | Dense overlapping crowds lead to bounding-box undercounting. | MEDIUM | HIGH | 1. Implement head-centroid bias and density-area regression correction.<br>2. Combine bounding-box count with optical flow motion energy.<br>3. Clearly expose confidence metrics ($C \in [0, 1]$) in the dashboard. |
| **TR-04** | **Scope Creep** | Temptation to integrate drone feeds, IoT gate hardware, or facial recognition during hackathon. | CRITICAL | MEDIUM | 1. Phase 0 hard-freeze: strictly lock all non-MVP features to future roadmap.<br>2. Direct code review enforcement against external hardware APIs. |
| **TR-05** | **Ethical & Legal** | Risk of user or judge misunderstanding the AI as an autonomous decision maker. | CRITICAL | LOW | 1. Mandatory UI disclaimers: *"Decision Support Prototype Only — Human Operator Approval Required."*<br>2. UI enforces physical human click on `[APPROVE]` before any action simulation is logged. |
| **TR-06** | **Network / Graph Drift** | Counterfactual flow simulation calculates mathematically optimal route that overloads a secondary zone. | HIGH | MEDIUM | 1. Hard invariant checks in the Feasibility Engine ($\Omega(a_j)$) that invalidate any action pushing secondary zones past $85\%$ capacity.<br>2. Explicit failure reason logged to operator. |

---

## 2. Ethical AI & Privacy Compliance Rules
1. **Zero Biometrics:** No facial detection, gender classification, age estimation, or personal identifiable information (PII).
2. **Local Execution:** No video frames or crowd imagery are uploaded to third-party public cloud endpoints.
3. **Transparent Heuristics:** The contextual risk engine uses inspectable, interpretable mathematical formulas rather than an opaque black-box neural network with unexplainable predictions.
4. **Accountability:** Every decision approval, rejection, or override is saved to a persistent, immutable audit ledger with operator ID and timestamp.
