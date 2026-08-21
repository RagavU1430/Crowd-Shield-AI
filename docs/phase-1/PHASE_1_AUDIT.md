# CROWD-SHIELD — Phase 1 Audit

**Audit date:** 2026-08-20  
**Scope:** Phase 1 delivery audit and Phase 2 environment readiness only  
**Boundary:** No crowd-state, risk, trajectory, or intervention feature was implemented or redesigned.

## Audit Outcome

Phase 1 is **PASS with documented limitations** after authorized repairs. The upload, validation, safe storage, metadata, job-status, frontend shell, video playback path, CORS, and error-handling flow work locally. The original Phase 1 delivery was not complete as claimed: the React build compiled only the Vite starter page, the intended TypeScript UI was unreachable and broken, polling used `video_id` instead of `job_id`, error payloads contradicted the API document, dependency declarations were missing, and the backend could not collect tests because Phase 1 eagerly imported a missing later-phase dependency.

Phase 2 readiness is **89/100 — GO WITH CAUTION**. CPU PyTorch, OpenCV, local YOLOv8n loading, person-class inference, sampled-frame inference, and the Phase 1-to-YOLO bridge all pass. CUDA/GPU is unavailable, the supplied crowd video is synthetic particle footage on which pretrained YOLO returns zero people, and no training dataset is present.

## 1. Source of Truth Review

All requested Phase 0 files were present and read: `PROJECT_SCOPE.md`, `MVP_REQUIREMENTS.md`, `ARCHITECTURE.md`, `DATA_FLOW.md`, `API_PLAN.md`, `AI_PIPELINE.md`, `VENUE_MODEL.md`, `INTERVENTION_ENGINE.md`, `2_DAY_PLAN.md`, `RISK_REGISTER.md`, `TEST_PLAN.md`, and `VIDEO_FIRST_UPDATE.md`.

| Document claim | Verification |
|---|---|
| Uploaded MP4/WebM/MOV is the primary MVP input | Verified and enforced by the repaired Phase 1 API/frontend. |
| YOLOv8n, class 0, confidence 0.35 is the Phase 2 detection plan | Verified in Phase 0 documents and readiness probe only. No new product detector was implemented. |
| Anonymous aggregate analysis; no face/ReID/biometrics | Verified by code search and detector output shape. |
| Phase 1 is scaffold/environment setup | Verified in `2_DAY_PLAN.md`; full risk/simulation code is beyond that boundary. |
| Default benchmark venue has four zones | Verified in `backend/venue_config.json`. |
| `configs/venue_config.json` is the benchmark venue | False: this file is an empty placeholder and differs from `backend/venue_config.json`. |
| Phase 1 React upload/dashboard is complete | False before repair; the Vite entry imported the starter `App.jsx`. Verified after repair. |
| Phase 1 had 11 passing tests | Not reproducible initially: collection failed on missing `networkx`. Final audit suite is 17 passed. |
| Phase 1 errors use `{error: {code, message}}` | False before repair; FastAPI `detail` was returned. Verified after repair for Phase 1 routes. |
| Jobs progress through multiple background stages | False: no Phase 1 background lifecycle existed. Repaired behavior truthfully returns `COMPLETED/100` once ingestion and metadata extraction finish; it does not imply AI analysis. |
| Uploads are stored in `data/uploads/` | False: actual path is `backend/uploads/` by default. |
| `PHASE_1_REPORT.md` exists | False; the requested source document is missing. |

Several Phase 0 Markdown files render mojibake characters (`â€”`, `â†’`, box-drawing corruption), indicating an encoding problem. Their semantic content remains readable but presentation should be normalized later.

## 2. Project Structure Audit

| Area | Result | Evidence |
|---|---|---|
| `frontend/` | Present | React 19/Vite 8 project. |
| `backend/` | Present | FastAPI app, static UI, services, tests, uploads. |
| `ai/` | Missing | AI code instead lives under `backend/app/services/`. |
| `data/` | Missing | No dataset or separate upload data root. |
| `configs/` | Present but inconsistent | Contains an empty venue placeholder; backend has the populated config. |
| `docs/` | Present | Phase 0 and Phase 1 documents. |
| root `tests/` | Missing | Tests are under `backend/tests/`; `test_vertical_slice.py` is at root. |

Identified without deletion:

- Duplicate frontend implementations: active `components/dashboard/DashboardShell.tsx`; dead `pages/DashboardShell.tsx`, `pages/UploadPage.tsx`, and starter `App.jsx`.
- Dead frontend files contain broken imports, missing imports, `return null`, and an undeclared `uuid` dependency. They are outside the active build graph and produce lint warnings.
- Duplicate static frontend in `backend/static/` and React frontend in `frontend/`.
- Duplicate identical YOLO weights at root and `backend/yolov8n.pt` (same SHA-256, 6,549,796 bytes each).
- Fifteen duplicate uploaded MP4 copies shared one SHA-256 during the audit; they were retained as instructed.
- `__pycache__`, `.pytest_cache`, runtime upload artifacts, presentation outputs, and generated assets are present. Ignore rules were added; nothing was deleted.
- Hard-coded absolute Windows paths existed in the old backend test, README setup commands, and old test report. The active test path was repaired; documentation paths remain findings.
- Hard-coded localhost defaults remain intentionally configurable through environment variables.
- No backend requirements file existed; root `requirements.txt` was added.
- No project-level `.gitignore` or `.env.example` existed; both were added.
- Git root resolves to `C:/Users/Ragav U`, not this project. All project files appear untracked, so tracked-file and history-based secret auditing is not reliable.
- Secret-pattern search found no API keys, passwords, private keys, credentials, or committed `.env` content in the workspace files.

## 3. Frontend Audit

| Feature | Result | Evidence |
|---|---|---|
| Dependency installation | PASS | Lockfile resolved; npm commands ran successfully. |
| Production build | PASS | Vite 8.2.2, 22 modules, 305 ms final measured build. |
| Frontend tests | PARTIAL | No `npm test` script or frontend unit-test framework exists. |
| React/Vite startup | PASS | Vite served HTTP 200 on `127.0.0.1:5173`. |
| Upload component | PASS | Active React component renders selection, upload, remove, progress, and errors. |
| Drag-and-drop | PASS | `dragenter`, `dragover`, `dragleave`, and `drop` handlers validated by source/build. Browser automation was prohibited. |
| File selection | PASS | Hidden file input with MP4/WebM/MOV accept list and button trigger. |
| Client validation | PASS | Extension and 100 MB checks. |
| Upload reaches backend | PASS | Real HTTP E2E POST succeeded. |
| Upload progress | PASS | `XMLHttpRequest.upload.onprogress` drives a visible progress element. |
| Analysis status | PASS | Polls with `job_id`, displays status/stage/progress. |
| Dashboard shell | PASS | Active dashboard renders after successful upload. |
| Video viewer | PASS | Uses the safe `/uploads/{video_id}` URL; E2E GET returned the complete file. |
| API/backend failure | PASS | Network and structured API errors become visible alerts. |

`npm run lint` has no errors in active code, but reports 14 warnings in retained dead duplicate page files. `npm audit` reported zero vulnerabilities across 67 dependencies.

## 4. Backend Audit

| Capability | Result | Evidence |
|---|---|---|
| FastAPI startup | PASS | Uvicorn health check succeeded locally on port 8011. Port 8000 was already occupied by an unrelated local service and was left untouched. |
| `/api/health` | PASS | Exact expected JSON returned. |
| Upload | PASS | Real multipart request succeeded. |
| Extension/MIME/content validation | PASS | Focused tests cover unsupported extension, MIME, corrupted video, and real OpenCV readability. |
| Safe filename/path | PASS | UUID-only stored name; client basename is display-only; traversal test passed. Legacy v1 storage was also hardened. |
| Size limit | PASS | Streaming 1 MB chunks; 413 at configured limit; partial file removed. |
| Storage | PASS | Final rename only after OpenCV validation; E2E retrieval matched input byte size. |
| Metadata | PASS | 6.0 s, 640×480, 15 fps, 90 frames in the measured E2E run. |
| Job creation/status | PASS | Unique `job_` ID; `COMPLETED`, 100%, explicit Phase 1-ready stage. |
| Missing job | PASS | Structured 404 `JOB_NOT_FOUND`. |
| CORS | PASS | Configured origin allowed; untrusted origin not allowed. |
| Structured errors/no stack trace | PASS | Phase 1 errors return only code/message. |
| Optional later-phase dependency isolation | PASS | Phase 1 routes boot independently; later routes are optional if dependencies are absent. |

In-memory jobs are suitable only for this prototype: state is lost on restart and is not shared across workers.

## 5. End-to-End Phase 1 Test

```text
vertical_slice_test.mp4 → multipart upload → validation → UUID storage
→ OpenCV metadata → Phase 1 job → status → static video response
```

| Measurement | Actual result |
|---|---|
| Input size | 1,457,314 bytes at time of E2E measurement |
| Upload/API time | 202.359 ms |
| Duration | 6.0 s |
| Metadata | 640×480, 15.0 fps, 90 frames |
| Job | `job_1276e3896f28` in that run |
| Final status | `COMPLETED`, progress 100 |
| Stored video retrieval | HTTP 200, 1,457,314 bytes |

The existing vertical-slice script later regenerated the same fixture (still 6 s/90 frames) at 1,501,766 bytes. This explains the current on-disk size difference and is not an invented measurement.

## 6. AI and Video Readiness

- Python 3.14.5 is the active interpreter. The old report's Python 3.11.9 claim was stale.
- PyTorch 2.13.0+cpu imports successfully; CUDA is false; device count is 0; CPU fallback is available.
- OpenCV 4.13.0 opened the actual Phase 1 video, read metadata/frame, resized to 640×640, converted BGR→RGB, saved a test frame, and released both captures.
- Ultralytics 8.4.124 imported and local `yolov8n.pt` loaded.
- The local Ultralytics `bus.jpg` test image yielded three class-0 person boxes with confidences 0.8657, 0.8528, and 0.8252.
- Sampled synthetic crowd-video frames 0/5/10 each yielded zero YOLO persons. Inference still completed successfully; zero detections are expected evidence that particle footage is not a valid photorealistic person benchmark.
- CPU sampled-frame mean was 151.760 ms / 6.589 FPS. Process RSS increased by 139.355 MB from pre-load to post-inference.
- GPU test: NOT AVAILABLE. No driver or system change was attempted.
- Phase 1 OpenCV frame → YOLO input bridge: PASS, 166.275 ms on the tested frame.

## 7. AI Module Architecture Check

**Result: FAIL against the requested expected structure.** There is no top-level `ai/` directory and no `ai/detection/`, `ai/crowd_state/`, `ai/risk/`, `ai/trajectory/`, or `ai/simulation/`. Pre-existing functional modules are under `backend/app/services/perception`, `analytics`, and `simulation`. Crowd-state, risk, trajectory, and intervention implementations already exist, contrary to the Phase 1 status document's boundary claims. They were not extended or redesigned during this audit.

## 8. Dataset and Difficulty Readiness

No image/label tree, dataset YAML, annotation files, classes file, or train/validation/test split exists. **Dataset readiness: NOT AVAILABLE.**

The only local “crowd” clips are synthetic particles. Normal crowd, dense real crowd, occlusion, camera-angle, resolution, and lighting difficulty comparisons were skipped because no valid local samples exist. No scientific accuracy claim is made.

## 9. Privacy Audit

**Result: PASS.** Source search found no facial recognition, face embeddings, ReID, names, identity persistence, or biometric profiling. Detection outputs are boxes, centroids, confidence, and optional zone data.

> Person detection is used for aggregate crowd analysis, not identity recognition.

The pre-existing detector does assign frame-local numeric IDs, but no identity matching or cross-frame re-identification exists.

## 10. Security Audit

**Result: PARTIAL.** Phase 1 upload controls pass. Remaining limitations are repository/process concerns rather than an exploitable Phase 1 path:

- The workspace is not its own Git repository; the parent user-profile repository makes tracked-secret verification unreliable.
- Many old upload copies and two identical model files consume unnecessary space.
- Backend has no authentication, appropriate only for a local MVP.
- Uploaded videos remain accessible by unguessable URL and have no retention policy.
- In-memory jobs have no persistence or multi-worker safety.
- No npm advisories and no broken Python requirements were found.

## 11. Dependency Audit

- Added declared root `requirements.txt`; installation and `pip check` pass.
- `scipy` is installed and verified but not imported by current application code.
- `torchvision` is not directly imported by project code but is part of the tested PyTorch/Ultralytics vision environment.
- `networkx` and `ultralytics` are used by pre-existing later-phase modules.
- Frontend dependency tree resolves cleanly. All declared runtime packages are used by the active app; dead code references undeclared `uuid` but is not in the build graph.
- No blind upgrades were performed; constrained major-version ranges were added.

## 12. Problems Fixed

1. Isolated Phase 1 routes from optional later-phase imports.
2. Replaced whole-file upload buffering with chunked size enforcement.
3. Added safe UUID storage, basename handling, traversal guard, temporary-file cleanup, and OpenCV content validation.
4. Added structured Phase 1 errors and response models.
5. Corrected job lifecycle to a truthful completed-ingestion state.
6. Made size, formats, upload directory, and origins configurable; added `.env.example`.
7. Wired Vite to the real Phase 1 React UI.
8. Implemented rendered selection, drag/drop, validation, upload progress, status, dashboard, video viewer, and graceful errors.
9. Corrected frontend polling to use `job_id`.
10. Fixed the video-viewer syntax error.
11. Added requirements and ignore rules.
12. Hardened the legacy v1 upload filename and size handling without changing its architecture.
13. Replaced hard-coded test paths and added meaningful API/video/AI tests.

## 13. Remaining Problems

- Missing `PHASE_1_REPORT.md` source document.
- Missing expected top-level `ai/`, `data/`, and `tests/` structure.
- Pre-existing later-phase engines violate the claimed Phase 1-only repository state.
- Duplicate/dead frontends, duplicate configs, duplicate model weights, and duplicate uploads remain (not deleted per instruction).
- Empty `configs/venue_config.json` conflicts with the populated backend config.
- No frontend unit/integration test command.
- No local training dataset or real crowd difficulty samples.
- No CUDA device; CPU wheel only.
- Synthetic fallback contour detections must not be presented as YOLO people or accuracy evidence.
- Existing Markdown encoding corruption and stale README/status claims need a later documentation cleanup.

## 14. Phase 2 Readiness Score

| Component | Score |
|---|---:|
| Phase 1 Functionality | 85% |
| Video Pipeline | 100% |
| OpenCV | 100% |
| PyTorch | 90% |
| YOLO Import & Model | 100% |
| Single-Frame Inference | 100% |
| Video Inference | 85% |
| CPU/GPU Availability | 60% |
| Frontend/Backend Integration | 90% |
| Test Coverage | 80% |
| **OVERALL READINESS** | **89/100** |

The overall value is the arithmetic mean of the ten equally weighted measured component scores.

## Recommendation

**GO WITH CAUTION.** Phase 2 video intelligence can begin after approval using CPU fallback, but the team should first establish a project-scoped Git repository, select one model/config location, add a real ethically sourced crowd validation set, and keep contour-fallback outputs clearly separated from YOLO detections.

Phase 2 implementation has not started as part of this audit.
