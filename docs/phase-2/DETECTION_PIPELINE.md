# CROWD-SHIELD — Detection Pipeline

## Runtime flow

`VIDEO -> OPENCV DECODE -> FRAME SAMPLING -> YOLOV8N CLASS 0 -> BOX/CONFIDENCE -> CENTROID/COUNT -> JSON/CSV -> ANNOTATED FRAME/VIDEO -> API -> REACT DASHBOARD`

## Components

| Component | Responsibility |
|---|---|
| `backend/app/services/detection/person_detector.py` | Lazy model loading, CPU/CUDA selection, class-0 inference, output normalization, CPU fallback |
| `backend/app/services/detection/video_detection.py` | Incremental decode, sample scheduling, timestamps, counts, annotation, JSON/CSV/video output, cleanup and errors |
| `backend/app/api/phase2.py` | Start background detection and retrieve status/results |
| `backend/scripts/run_phase2.py` | Repeatable local processing for one or all source videos |
| `frontend/src/services/api.ts` | Typed Phase 2 API calls and artifact URL handling |
| `frontend/src/components/dashboard/DashboardShell.tsx` | Start/status/results UI, metrics, artifacts, video, observation timeline |

## Sampling and memory behavior

For a source rate `S` and target analysis rate `T`, the interval is `max(1, round(S / T))`. All source videos are 60 FPS and the target is 5 FPS, so every twelfth source frame is analyzed. Frames are decoded and processed incrementally; only the current frame and result are required in memory. The sampled annotated video is written at the effective 5 FPS.

## Annotation

Each retained prediction is drawn as a rectangle with a `person` confidence label. The centroid is drawn as a visible point. The frame overlay includes timestamp and person count. An annotated JPEG is saved every 25 analyzed frames, and an annotated sampled MP4 is produced for every successful input.

## Artifacts

| Directory | Contents |
|---|---|
| `data/processed/results/` | Per-frame detection JSON and frame-summary CSV |
| `data/processed/summaries/` | Video metadata, configuration, summary, timeline, artifact names |
| `data/processed/frames/` | Periodic annotated JPEGs |
| `data/processed/annotated/` | Sampled annotated MP4 files |

Partial JSON/CSV files are finalized safely, but a partial annotated MP4 is not published as a successful result. The generated output directory is git-ignored.

## API contract

| Method and path | Purpose |
|---|---|
| `POST /api/analysis/{job_id}/detect` | Resolve a completed Phase 1 upload and start a background Phase 2 detection job |
| `GET /api/analysis/{job_id}/detections` | Return queued/running/completed/failed status, progress, summary, timeline, and artifact URLs |
| `GET /processed/...` | Serve generated local artifacts |

Invalid or missing videos, missing jobs, decode failures, inference failures, memory failures, and interruptions produce structured error states. Internal exception details and stack traces are not returned to the frontend.

## Dashboard behavior

The dashboard adds a user-triggered detection action after Phase 1 upload, polls status, shows progress, and displays model/device/sample-rate metadata. Completed results include current timestamp-aligned observations, person count, mean confidence, an observation timeline, downloads, and the annotated sampled video. API failures are rendered as safe messages.

## Privacy and phase boundary

Person detection is used for aggregate crowd analysis, not identity recognition. The pipeline has no facial recognition, re-identification, person IDs, names, biometric profiles, or identity persistence. It also has no Phase 3 density, flow, crowd-state, trajectory, risk, venue, or intervention logic.

