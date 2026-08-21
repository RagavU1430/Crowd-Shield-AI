# CROWD-SHIELD — Phase 2 Test Results

## Final automated result

`29 PASSED, 0 FAILED` in the combined backend/AI suite. Runtime: 14.61 seconds. One non-failing upstream warning reports that Starlette's `httpx` TestClient integration is deprecated in favor of `httpx2`.

Frontend production build: **PASS** — Vite 8.2.2 transformed 22 modules and built successfully in 425 ms.

## Phase 2 focused tests

| Test area | Result | Evidence |
|---|---|---|
| YOLO model loading | PASS | Existing local YOLOv8n weights loaded in the active environment |
| Person-class filtering | PASS | Non-person classes excluded; class 0 retained |
| Bounding-box extraction | PASS | Normalized `[x1,y1,x2,y2]` output verified |
| Centroid calculation | PASS | Midpoint calculation verified |
| Confidence extraction | PASS | Prediction confidence preserved |
| Frame sampling | PASS | 60 FPS source to 5 FPS target gives interval 12 |
| Video processing and count | PASS | Actual small generated video processed through pipeline |
| JSON output | PASS | Schema and records verified |
| CSV output | PASS | Header and per-frame rows verified |
| Annotated frame/video | PASS | Output exists, opens, and contains analyzed frames |
| Invalid video handling | PASS | Safe failure returned for corrupt input |
| API start/retrieve | PASS | Detection background job and retrieval contract verified |

The focused Phase 2 module contributes 12 substantive tests; the other 17 tests protect the existing Phase 1 API, upload, metadata, video, and AI-environment behavior.

## Live terminal-only service checks

| Check | Result | Evidence |
|---|---|---|
| FastAPI startup | PASS | Uvicorn started on local port 8017 |
| Health endpoint | PASS | `GET /api/health` returned HTTP 200 |
| OpenAPI Phase 2 routes | PASS | Both detect and detections paths were present |
| Processed static artifact | PASS | Summary JSON returned HTTP 200 |
| Vite development startup | PASS | Vite ready in 607 ms on local port 5187 |
| Frontend HTTP response | PASS | Root request returned HTTP 200 with application mount element |

These checks used PowerShell HTTP requests only. No browser or browser automation was used. Audit server processes were stopped after the checks.

## Real-video validation

| Validation | Result |
|---|---|
| All four source videos opened/read | PASS |
| All four practical videos processed | PASS |
| 1,045 analyzed frame records | PASS |
| 540 detections all class 0/person | PASS |
| Centroids inside their boxes | PASS |
| JSON frames equal CSV rows | PASS |
| Annotated video frames equal JSON frames | PASS |
| Annotated videos open/read at 5 FPS and 1920x1080 | PASS |
| Original byte sizes/timestamps unchanged | PASS |

## Error and boundary tests

Corrupt input, missing job, invalid state, inference exception, and output failures are handled without exposing stack traces. The implementation contains no tracking, face recognition, density, crowd state, trajectories, risk, predictions, or intervention calculations.

