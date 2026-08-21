# CROWD-SHIELD — Phase 2 Video Intelligence Report

## 1. Executive summary

Phase 2 is complete within the authorized person-detection boundary. The repository now has an isolated YOLOv8n service, incremental sampled-video processor, JSON/CSV/annotated outputs, background API integration, and a React observation dashboard. All four practical local videos were processed on CPU. The final automated result is 29 passed and 0 failed, and the frontend production build passes.

This establishes a working video-to-person-observation foundation. It is not a crowd-risk system and makes no accuracy claim: the local footage is sparse, moving-camera material without labels or dense-crowd coverage.

## 2. Scope compliance

| Requirement | Result | Evidence |
|---|---|---|
| Reuse existing YOLOv8n | PASS | Local `yolov8n.pt` loaded; no training or large-model download |
| Person class only | PASS | All 540 persisted detections validated as class 0/person |
| Sample long videos | PASS | 60 FPS sources analyzed every 12 frames at 5 FPS |
| Box, centroid, count, confidence, timestamp | PASS | Stored per frame in JSON; counts/timing also in CSV |
| Annotated outputs | PASS | Four MP4s and 44 periodic JPEGs generated |
| Backend API | PASS | Start/retrieve routes plus static artifact mount |
| Frontend integration | PASS | Trigger, progress, metrics, timeline, artifacts, annotated player |
| Preserve originals | PASS | Source byte sizes and timestamps unchanged |
| Avoid Phase 3 | PASS | No density, flow, state, tracking, risk, venue, prediction, or intervention logic |

## 3. Dataset inventory and selection

Four H.264 MP4 files were found, totaling 463,805,534 bytes and 208.733334 seconds. All are 1920x1080 at 60 FPS and passed OpenCV open/read validation. `21-38-15` was the primary baseline based on the greatest initial sampled count; `21-32-01` was secondary based on initial consistency. All four were ultimately processed.

The footage is a valid engineering integration baseline but a weak model-validation dataset: detected counts were 0–4 per sampled frame, dense crowds were not represented, and no ground truth exists.

## 4. Detection pipeline

The pipeline reads frames incrementally with OpenCV, analyzes every twelfth frame, runs local YOLOv8n at image size 640 and confidence 0.35, retains class 0, calculates box midpoints, and streams records to output files. It writes a 5 FPS annotated sampled video plus periodic JPEGs. It never buffers the full video.

The service selects CUDA only when PyTorch reports it available. The active environment is CPU-only, so all inference used CPU. A prediction-time CUDA exception would safely retry on CPU.

## 5. Measured results

| Video | Frames | Total detections* | Mean persons/frame | Max | Mean confidence | Processing FPS |
|---|---:|---:|---:|---:|---:|---:|
| `21-32-01` | 161 | 123 | 0.763975 | 4 | 0.476785 | 2.953912 |
| `21-32-40` | 196 | 110 | 0.561224 | 4 | 0.474542 | 3.470980 |
| `21-33-43` | 331 | 42 | 0.126888 | 2 | 0.474025 | 3.513521 |
| `21-38-15` | 357 | 265 | 0.742297 | 4 | 0.582691 | 3.392418 |
| **Total/weighted** | **1,045** | **540** | **0.516746** | **4** | **0.528086** | **3.366466** |

\*Total detections are the exact sums of per-frame person counts.

Total wall-clock processing was 310.414350 seconds; measured YOLO-call time was 109.032259 seconds. Aggregate inference-only time was 104.337 ms/frame, approximately 9.584 inference FPS. End-to-end artifact-producing throughput was 3.366466 analyzed FPS.

## 6. Detection quality observations

The output is technically usable for engineering integration: detections have valid boxes, confidence values, centroids, frame indexes, and timestamps. Moving-camera operation was stable, but person counts were intermittent and the footage does not support claims about dense crowds, occlusion, low-resolution performance, or general accuracy. Confidence is not accuracy.

## 7. Backend and API

Phase 2 adds `POST /api/analysis/{job_id}/detect` and `GET /api/analysis/{job_id}/detections`. Work runs in the background, reports progress, and returns summary/timeline/artifact URLs. Generated output is served below `/processed`. Safe errors cover missing/corrupt videos, decode/inference/output problems, memory pressure, and interruption without returning stack traces.

Live terminal-only checks confirmed FastAPI health, OpenAPI route registration, processed-artifact access, Vite startup, and frontend HTTP 200 responses.

## 8. Frontend integration

The existing dashboard now starts detection after upload, polls job status, shows progress and safe failures, displays annotated video, and aligns current person observations to player time. It reports person count, mean confidence, timestamp, model/device/sample rate, a per-frame observation timeline, and JSON/CSV downloads. It explicitly presents observations rather than risk or safety conclusions.

## 9. Privacy and security

Person detection is used for aggregate crowd analysis, not identity recognition. There is no face recognition, identity assignment, name storage, biometric profiling, re-identification, or cross-frame tracking. Source resolution is confined to known Phase 1 jobs or the configured video directory, artifact filenames are sanitized, generated content is segregated and git-ignored, and client errors are structured.

## 10. Test results

- Backend/AI: **29 passed, 0 failed**; one upstream deprecation warning.
- Frontend build: **PASS**, 22 modules transformed, 425 ms.
- Phase 2 focused: **12 passed**, covering model load, filtering, geometry, sampling, processing, artifacts, invalid input, and API.
- Real artifacts: **PASS** for JSON/CSV/video count agreement, person-only records, valid centroids, OpenCV playback, FPS, and resolution.

## 11. Issues found and resolved

| Issue | Resolution/status |
|---|---|
| No Phase 2 detection service or API | Added isolated detection modules and endpoints |
| No detection dashboard/timeline | Added typed frontend integration and observation UI |
| Long 60 FPS videos would be unnecessarily expensive at full rate | Added configurable sampling; default 5 FPS |
| Potential GPU prediction failure | Added safe CPU fallback |
| Partial annotated videos could appear successful after failure | Publish only after successful completion |
| Duplicate YOLO weight files at root/backend | Not deleted; root canonical file is reused by new service |
| `.venv-training` launcher is broken | Documented; active CPU environment used; system Python/drivers untouched |
| Requested Phase 1 `PHASE_1_REPORT.md` missing | Documented; available final Phase 1 reports used |
| No labeled/custom dataset | Not available; no training performed |

## 12. Remaining limitations

- No supported GPU is available in the active environment; GPU performance is not measured.
- CPU end-to-end throughput (3.366 analyzed FPS) is below the 5 FPS sampling rate, so processing is offline rather than realtime.
- The local videos do not constitute a representative crowd-validation set.
- No ground truth exists, so precision, recall, mAP, and accuracy cannot be reported.
- Confidence threshold 0.35 is an engineering baseline, not a calibrated operating point.
- A duplicate local weight file remains; it was not removed because deletion was outside the requested implementation.

## 13. Phase completion decision

**PHASE 2 DELIVERY: PASS.** The authorized video-intelligence slice works end to end on every practical local source, integrates with the Phase 1 job flow, and preserves Phase 1 behavior. Proceed to Phase 3 only with explicit approval and with the limitations above understood.

## 14. Next-phase boundary

The next phase would be Phase 3 — Crowd State Estimation. It has not been started. This Phase 2 output provides only frame-level person boxes, centroids, counts, confidence, and timestamps; it contains no density, motion, risk, or intervention semantics.
