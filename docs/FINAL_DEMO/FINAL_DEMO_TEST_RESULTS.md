# CROWD-SHIELD Final Demo Test Results

Test date: 2026-08-21  
Method: terminal and local HTTP only; no browser, browser automation, or remote agent was used.

## Automated verification

| Check | Result | Evidence |
|---|---|---|
| Backend test suite | PASS | `36 passed`, `0 failed`, one upstream Starlette/httpx deprecation warning; 17.24 s. |
| Frontend production build | PASS | Vite 8.2.2; 22 modules transformed; build completed in 297 ms. |
| Frontend lint | PASS | Exit 0 with zero errors and zero warnings after legacy frontend consolidation. |
| Health through frontend proxy | PASS | `GET http://127.0.0.1:5173/api/health` returned `status=ok`. |
| Duplicate launcher behavior | PASS | A second `node scripts/dev.mjs` returned exit 0 and: `CROWD-SHIELD is already running at http://localhost:5173`. |
| Frontend root | PASS | HTTP 200 before and after restart. |

## Real-video end-to-end test

Source: `videos/2026-08-20 21-32-40.mp4`  
Size: 94,899,381 bytes  
Metadata: 39.183 seconds, 1920×1080, 60 FPS  
Mode: normal observed analysis (`demo_mode=false`)

| Measurement | Run 1 | Run 2 after restart |
|---|---:|---:|
| Upload time | 1.95 s | 1.68 s |
| Frames analyzed | 118 | 118 |
| Model | CROWD-SHIELD Crowd YOLOv8n | CROWD-SHIELD Crowd YOLOv8n |
| Device | CUDA `cuda:0` | CUDA `cuda:0` |
| Maximum people in a sampled frame | 116 | 116 |
| Average people per analyzed frame | 79.042373 | 79.042373 |
| Average detection confidence | 0.373161 | 0.373161 |
| Processing time | 58.393093 s | 49.377975 s |
| Effective processing rate | 2.020787 FPS | 2.389729 FPS |
| Peak contextual risk | 59.2 / 100 HIGH | 59.2 / 100 HIGH |
| Critical zone | ZONE C | ZONE C |
| Recommended action | Open Exit C + Redirect Flow | Open Exit C + Redirect Flow |
| Simulated risk | 59.2 → 37.69 | 59.2 → 37.69 |
| Simulated reduction | 36.3% | 36.3% |
| Feasible | Yes | Yes |
| Approval API | SIMULATED_INTERVENTION_APPLIED | SIMULATED_INTERVENTION_APPLIED |
| Video byte-range playback | HTTP 206, 1024 bytes | HTTP 206, 1024 bytes |
| Detection JSON artifact | Available | HTTP 200 |

The repeat produced identical model outputs, demonstrating deterministic inference for the same source and configuration. Processing time varied normally with runtime load.

## Acceptance flow

| Requirement | Result | Evidence |
|---|---|---|
| Upload crowd video | PASS | Real 94.9 MB MP4 accepted through frontend proxy. |
| Analyzing status | PASS | Async job reported QUEUED → PROCESSING with measured progress → COMPLETED. |
| YOLO person detection | PASS | Crowd checkpoint loaded on CUDA; annotated/video and JSON artifacts generated. |
| Person count | PASS | Current, average, peak, timeline, and trend are computed. |
| Density and density trend | PASS | Relative image-space signal and growth only; no false people/m² claim. |
| Movement | PASS | Camera-compensated optical flow with availability fallback and direction. |
| Flow convergence/conflict | PASS | Computed 0–100 signals returned per sampled frame. |
| Bottleneck | PASS | Transparent combined pressure signal returned per frame. |
| Risk and explanation | PASS | Weighted risk, level, slope/trend, and dynamic contributors returned. |
| Critical zone | PASS | Four logical zones with counts, risks, reasons, and critical selection. |
| What-if and feasibility | PASS | Five simulation options with projected risk and feasibility reasons. |
| Recommendation | PASS | Lowest-risk feasible intervention selected for the HIGH-risk peak state. |
| Human approval | PASS | UI Confirm/Cancel gate plus simulation approval API. |
| Simulated result | PASS | Before/action/after and 36.3% reduction, explicitly not a real-world action. |
| Restart and repeat | PASS | Exact listeners stopped, ports released, services restarted healthy, full flow repeated. |
| Phase 1 regression | PASS | Health/upload/validation/job/status/playback tests remain green. |

## Non-blocking observations

- No calibrated venue or held-out ground truth dataset is available, so neither people/m² nor detector accuracy is claimed.
- Runtime achieved about 2.0–2.4 analyzed FPS, below the 3–5 FPS aspiration but reliable for the tested demo video.
- The one warning in pytest is an upstream TestClient compatibility deprecation, not a failing behavior.

Final result: **36 PASSED, 0 FAILED. END-TO-END DEMO PASS.**
