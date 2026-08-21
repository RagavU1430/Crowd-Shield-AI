# CROWD-SHIELD Final MVP Audit

Audit date: 2026-08-21  
Scope: existing Phase 0/1/2 documents, frontend, backend, AI modules, data/configuration, videos, APIs, and tests. The implementation was inspected before changes; working functionality was retained.

## Component audit

| Component | Initial status | Final status | Location | Action |
|---|---|---|---|---|
| Video upload | IMPLEMENTED | IMPLEMENTED | `frontend/src/components/upload/VideoUploader.tsx`, `backend/app/api/phase1.py` | Retained; verified through the Vite proxy with a 94,899,381-byte MP4. |
| Explicit analysis start | BROKEN | IMPLEMENTED | `frontend/src/components/dashboard/DashboardShell.tsx` | Removed automatic start; added metadata review and **START ANALYSIS**. |
| YOLO | PARTIALLY IMPLEMENTED | IMPLEMENTED | `backend/app/services/detection/` | Uses crowd-specific YOLOv8n checkpoint with pretrained `yolov8n.pt` fallback; verified on CUDA. |
| Person count and confidence | IMPLEMENTED | IMPLEMENTED | `video_detection.py`, dashboard | Retained and exposed as current, average, peak, and trend. Confidence is labelled as model confidence, not accuracy. |
| Density | IMPLEMENTED | IMPLEMENTED | `fast_mvp.py` | Retained transparent image-space relative density; UI explicitly says estimated relative density, never people/m². |
| Movement | IMPLEMENTED | IMPLEMENTED | `optical_flow.py`, `fast_mvp.py` | Retained camera-compensated optical flow; added an availability flag and safe unavailable state. |
| Flow convergence | IMPLEMENTED | IMPLEMENTED | `fast_mvp.py` | Retained computed 0–100 signal and added detected/low presentation. |
| Flow conflict | IMPLEMENTED | IMPLEMENTED | `fast_mvp.py` | Retained opposing-direction circular variance signal. |
| Bottleneck pressure | IMPLEMENTED | IMPLEMENTED | `fast_mvp.py` | Retained transparent density/growth/convergence combination and presentation threshold. |
| Crowd state | IMPLEMENTED | IMPLEMENTED | `fast_mvp.py`, dashboard | Added count/density trends, direction, availability labels, and observed/demo provenance. |
| Contextual risk | IMPLEMENTED | IMPLEMENTED | `fast_mvp.py` | Retained documented weighted 0–100 prototype score and dynamic top contributors. |
| Risk trajectory | IMPLEMENTED | IMPLEMENTED | `fast_mvp.py`, dashboard | Retained per-sample scores, slope, trend, and chart. |
| Critical zone | PARTIALLY IMPLEMENTED | IMPLEMENTED | `fast_mvp.py`, dashboard | Added visible 2×2 zone map, counts, risk, reasons, and uncalibrated venue disclaimer. |
| Intervention simulation | IMPLEMENTED | IMPLEMENTED | `simulate_interventions()` | Retained rule-based signal transformations; all output is marked simulation-only. |
| Feasibility | IMPLEMENTED | IMPLEMENTED | `simulate_interventions()` | Retained destination-capacity check and feasibility reasons. Demo exit topology is explicitly identified. |
| Recommendation | IMPLEMENTED | IMPLEMENTED | `simulate_interventions()`, dashboard | Retained best-feasible ranking; added dynamic rationale and reduction percentage. |
| Human approval | PARTIALLY IMPLEMENTED | IMPLEMENTED | `phase2.py`, dashboard | Added required confirmation dialog with Confirm/Cancel before the API approval call. |
| Simulated result | PARTIALLY IMPLEMENTED | IMPLEMENTED | dashboard | Added strong Before → Simulated Intervention → After presentation and real-world-action warning. |
| Dashboard | PARTIALLY IMPLEMENTED | IMPLEMENTED | `frontend/src/components/dashboard/DashboardShell.tsx`, `App.css` | Completed the one-screen judge story, retrospective warning, fallbacks, and responsive styling. |
| Demo mode | IMPLEMENTED | IMPLEMENTED | `fast_mvp.py`, dashboard | Retained deterministic signal ramp with an unmistakable DEMO / SIMULATION banner; observed person counts remain separate. |
| Privacy boundaries | IMPLEMENTED | IMPLEMENTED | detection pipeline and UI | Person-class detection only. No face recognition, identity tracking, names, or biometrics. |

## Architecture and implementation findings

- The active path is React/Vite → FastAPI → validated upload/job store → sampled OpenCV frames → YOLO person detections → optical-flow/crowd signals → risk/zone/intervention output → human decision API.
- No core architecture was replaced. Existing Phase 1 upload, validation, safe storage, metadata, job status, and playback routes remain in use.
- The frontend now has one canonical entry (`App.tsx`), one dashboard component, one upload component, one API service, and one stylesheet. Confirmed unused Vite demo code, broken duplicate pages, sample assets, and the redundant global stylesheet were removed during the final consolidation requested by the owner.
- Backend upload and detection job stores are process-local. A restart intentionally clears prior jobs; the complete flow was repeated using a fresh upload after restart.
- No calibrated venue area/topology is available. Density and zones are therefore relative image-space estimates; intervention topology is a transparent simulation assumption.
- The crowd-specific checkpoint substantially improves dense-frame recall compared with the generic pretrained fallback, but no held-out ground truth was available for a scientific accuracy claim.
- Observed inference reached 2.02–2.39 analyzed frames/s at 960 px on the local RTX 3050. This is below the aspirational 3–5 FPS target but completes the 39.18-second video in 49–58 seconds and keeps the asynchronous UI responsive.
- The parent Git worktree is rooted above this project and reports unrelated home-directory files. No destructive Git cleanup was attempted.

## Problems fixed in this completion pass

1. Replaced automatic AI start with an explicit, truthful START ANALYSIS action after metadata display.
2. Added approval confirmation and cancellation before the simulation decision API call.
3. Added computed average/peak/current count and count/density trend presentation.
4. Added movement availability, dominant direction, convergence, conflict, and bottleneck labels.
5. Added a visible critical-zone grid with calculated reasons and venue-context warning.
6. Added retrospective-analysis language and removed any implication of causal prediction.
7. Added a strong simulation-only before/after result.
8. Hardened the local launcher so an already-running instance exits successfully instead of producing the port 5173 error.
9. Selected the crowd-specific YOLOv8n checkpoint by default while preserving the small pretrained fallback.
10. Consolidated all active frontend styling into `App.css`; removed the unused `App.jsx`, `src/pages/`, sample assets, and redundant `index.css`. Frontend lint now completes with zero warnings.

## Remaining limitations

- Prototype risk thresholds and intervention effects require domain validation before operational safety use.
- Relative density is not calibrated people/m².
- Logical zones are image quadrants until a venue configuration is supplied.
- The custom detector needs a held-out labelled evaluation set before accuracy can be stated.
- The MVP records decisions but never controls gates, exits, or physical infrastructure.

## Audit conclusion

The final hackathon MVP is **READY** as an explainable retrospective crowd-safety decision-support demonstration. It is not certified for operational or autonomous safety decisions.
