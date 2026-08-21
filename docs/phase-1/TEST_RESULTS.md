# CROWD-SHIELD: Phase 1 Test Results

**Document ID:** CS-DOC-P1-03
**Version:** 1.0.0

## Test Execution Summary
- **Test runner:** `pytest` with `TestClient`
- **Test file:** `backend/tests/test_phase1.py`
- **Total tests:** 11
- **Passed:** 11
- **Failed:** 0
- **Success rate:** 100%

## Test Details

### 1. test_health_endpoint
**Status:** PASSED
**Description:** Verifies `GET /api/health` returns correct response body.
**Response validated:**
- `status` = `"ok"`
- `service` = `"crowd-shield-backend"`
- `phase` = `"phase-1"`

### 2. test_valid_upload
**Status:** PASSED
**Description:** Verifies valid MP4 upload returns video metadata and job ID.
**Fields validated:**
- `status` = `"VALID"`
- `video_id` present
- `job_id` present
- `duration` > 0
- `width` > 0
- `height` > 0
- `fps` > 0
- `frame_count` present

### 3. test_unsupported_extension
**Status:** PASSED
**Description:** Verifies non-video file extensions are rejected.
**Error validated:**
- Status code 400
- Error message includes "Unsupported format"

### 4. test_invalid_video
**Status:** PASSED
**Description:** Verifies corrupted/invalid video content is rejected at the readability check.
**Error validated:**
- Status code 400
- Error message includes "could not be read as a valid video"
- Uses valid `.mp4` extension with invalid binary content

### 5. test_metadata_extraction
**Status:** PASSED
**Description:** Verifies OpenCV metadata extraction (duration, width, height, fps, frame_count).
**Fields validated against `vertical_slice_test.mp4`:**
- `duration` = 6.0s (90 frames at 15 fps)
- `width` = 640 pixels
- `height` = 480 pixels
- `fps` = 15.0
- `frame_count` = 90

### 6. test_job_creation
**Status:** PASSED
**Description:** Verifies job ID is generated and status can be retrieved.
**Validated:**
- `job_id` starts with `"job_"`
- Status endpoint returns matching `job_id`
- Status enum values are valid Phase 1 statuses

### 7. test_missing_job
**Status:** PASSED
**Description:** Verifies 404 response for non-existent job ID.
**Error validated:**
- Status code 404
- Detail message: `"Missing job"`

### 8. test_file_size_validation
**Status:** PASSED
**Description:** Verifies files exceeding MAX_VIDEO_SIZE_MB are rejected.
**Error validated:**
- Status code 400
- Error message includes "100MB"
- 150MB test file correctly rejected

### 9. test_health_route_exists
**Status:** PASSED
**Description:** Verifies `/api/health` is registered in the FastAPI app routes.

### 10. test_video_upload_route_exists
**Status:** PASSED
**Description:** Verifies `/api/videos/upload` is registered in the FastAPI app routes.

### 11. test_analysis_status_route_exists
**Status:** PASSED
**Description:** Verifies `/api/analysis/{job_id}` pattern is registered.

## End-to-End Flow Test
**Status:** VERIFIED MANUALLY
**Flow:**
1. Start FastAPI backend
2. Upload `vertical_slice_test.mp4` (90 frames, 6s, 640x480, 15 fps)
3. Backend receives file, validates extension (.mp4)
4. Backend reads file content, validates video readability via OpenCV
5. Backend generates safe UUID-based filename, stores file to `data/uploads/`
6. Backend extracts metadata: duration=6.0s, width=640, height=480, fps=15.0, frame_count=90
7. Backend creates analysis job with unique job_id
8. Backend stores job in in-memory job_store with metadata
9. Upload response returns `video_id`, `filename`, metadata, and `job_id`
10. Frontend can poll `GET /api/analysis/{job_id}` for status updates

## Known Issues
- Background tasks do not execute in `pytest TestClient` environment, so status polling stays at `UPLOADED`/`Pending` in tests
- In production with uvicorn + real BackgroundTasks, status progresses through `VALIDATING_VIDEO` -> `READING_VIDEO` -> `PREPARING` -> `COMPLETED`
- No AI/YOLO processing occurs in Phase 1; status progression is handled by the background video processor

## Security Observations
- Safe UUID-based filenames generated (no user-trusting)
- File extension validated against allowlist
- MIME type validated where practical
- Maximum file size enforced (100MB default)
- File content read and validated (not trusted blindly)
- Internal filesystem paths never exposed to frontend
- Job IDs validated before access

## Performance Observations
- Video metadata extraction via OpenCV: < 100ms for small test videos (640x480, 90 frames)
- Upload endpoint response time: ~50ms for small test videos
- Job status polling: lightweight JSON response, no heavy computation
- In-memory job store sufficient for hackathon MVP; replace with PostgreSQL for production

## Test Environment
- **Python:** 3.11.9
- **FastAPI:** latest
- **OpenCV:** 4.x
- **Platform:** Windows 10/11 (WSL2 possible)
- **Backend directory:** `C:\Users\Ragav U\OneDrive\Desktop\Ragav Folder\Projects\Dev Fusion\backend`

---

## Phase 1 Comprehensive Audit Update — 2026-08-20

This section supersedes the earlier execution summary above where results conflict. The original 11/11 result was not reproducible in the active environment: test collection initially failed because importing the Phase 1 app eagerly imported `networkx`, which was undeclared and absent. After authorized Phase 1 isolation, dependency declaration, UI/API fixes, and focused tests, the complete result is below.

### Final Test Summary

```text
17 PASSED
0 FAILED
1 WARNING
```

Command: `python -m pytest -q` from the project root with `PYTHONPATH=backend` and workspace-local Ultralytics configuration.

The warning is a Starlette notice that its current `TestClient` use of `httpx` is deprecated. It does not fail requests.

### Backend/API Tests

| Area | Result | Evidence |
|---|---|---|
| Health | PASS | Exact service/phase JSON asserted. |
| Valid upload | PASS | Real MP4 metadata and job ID asserted. |
| Safe filename | PASS | Traversal-style original name stored only as a UUID basename. |
| Extension validation | PASS | Structured `UNSUPPORTED_FORMAT`. |
| MIME validation | PASS | Structured `UNSUPPORTED_MIME_TYPE`. |
| Invalid content | PASS | Structured `INVALID_VIDEO`; temporary file absent. |
| Size limit | PASS | Chunked limit test returned 413 and removed partial file. |
| Metadata | PASS | 6.0 s, 640×480, 15 fps, 90 frames. |
| Job/status | PASS | `COMPLETED`, 100%, correct job/video IDs. |
| Missing job | PASS | Structured `JOB_NOT_FOUND` 404. |
| CORS allowed origin | PASS | Configured frontend origin returned. |
| CORS untrusted origin | PASS | No allow-origin header. |
| Video open/frame read | PASS | OpenCV real frame shape 480×640×3. |

### AI Environment Tests

| Test | Result |
|---|---|
| PyTorch import and CPU device | PASS |
| OpenCV import and actual video frame | PASS |
| Local YOLOv8n model loading | PASS |
| YOLO single-frame inference result | PASS |

### Frontend Verification

| Command/check | Result | Evidence |
|---|---|---|
| `npm run build` | PASS | 22 modules; 305 ms measured final build. |
| `npm test` | NOT AVAILABLE | No test script exists. |
| `npm run lint` | PARTIAL | No active-code error; 14 warnings in retained dead duplicate page files. |
| Vite startup | PASS | Terminal HTTP request returned 200 at `127.0.0.1:5173`. |
| npm dependency audit | PASS | 0 vulnerabilities across 67 total dependencies. |

### Real End-to-End Upload

| Measurement | Result |
|---|---|
| Input | `vertical_slice_test.mp4` |
| File size during run | 1,457,314 bytes |
| HTTP upload time | 202.359 ms |
| Metadata | 6.0 s; 640×480; 15 fps; 90 frames |
| Job | Created successfully |
| Final status | `COMPLETED`, 100 |
| Video retrieval | HTTP 200, 1,457,314 bytes |
| CORS preflight | HTTP 200, configured origin returned |

Port 8000 was already occupied by an unrelated local service; the backend E2E test used port 8011 and did not terminate or modify the existing service.

### Readiness Probe

- PyTorch 2.13.0+cpu: PASS; CUDA false; 0 devices; CPU fallback available.
- OpenCV 4.13.0: PASS for open/read/metadata/resize/color-convert/save/release.
- Ultralytics 8.4.124: PASS.
- YOLO model load: PASS, 81.792 ms.
- Single local person image: PASS, three class-0 detections.
- Sampled video frames: PASS execution, 0/0/0 people on synthetic particle footage.
- CPU sampled-frame performance: 151.760 ms mean, 6.589 FPS.
- GPU: NOT AVAILABLE.
- Dataset: NOT AVAILABLE.
- `pip check`: no broken requirements.
- Python compile check: PASS.

### Pre-existing Vertical Slice

`python test_vertical_slice.py` completed successfully after dependencies were installed. It regenerated the test video to 1,501,766 bytes and processed 13 frames. Its peak “158 people” result is produced by the code's contour-particle fallback, not YOLO person detections; it is retained as pipeline evidence only and is not a scientific accuracy result.
