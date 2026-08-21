# CROWD-SHIELD — Phase 2 Execution Plan

## Scope

Phase 2 delivers offline video intelligence limited to pretrained YOLOv8n person detection. The implemented flow is:

`LOCAL/UPLOADED VIDEO -> SAMPLED OPENCV FRAMES -> YOLO CLASS 0 -> BOXES + CENTROIDS + CONFIDENCE + COUNT -> JSON/CSV + ANNOTATIONS -> API/DASHBOARD`

It does not implement tracking, identities, crowd density, crowd-state classification, optical flow, trajectories, risk scoring, venue reasoning, prediction, or interventions. Originals in `videos/` remain read-only.

## Source-of-truth review

The implementation was bounded against Phase 0 `AI_PIPELINE.md`, `DATA_FLOW.md`, `ARCHITECTURE.md`, and `MVP_REQUIREMENTS.md`, plus Phase 1 `FINAL_READINESS_REPORT.md`, `AI_ENVIRONMENT_REPORT.md`, and `YOLO_READINESS_REPORT.md`. `docs/phase-1/PHASE_1_REPORT.md` was requested but is not present; the final Phase 1 audit/report documents were used instead.

## Work plan and completion

| Step | Deliverable | Status |
|---|---|---|
| 1 | Inventory and validate local videos | Complete |
| 2 | Select primary/secondary footage and record limitations | Complete |
| 3 | Add isolated detection service and incremental video pipeline | Complete |
| 4 | Add Phase 2 API and static artifact access | Complete |
| 5 | Add dashboard detection controls, metrics, video, and timeline | Complete |
| 6 | Add meaningful unit, pipeline, artifact, and API tests | Complete |
| 7 | Run all four practical videos at 5 sampled FPS | Complete |
| 8 | Validate artifacts and rerun Phase 1 regression tests | Complete |
| 9 | Document measured outcomes and limitations | Complete |

## Configuration

| Setting | Default |
|---|---:|
| Model | Local `yolov8n.pt` |
| Person class | COCO class 0 only |
| Confidence threshold | 0.35 |
| IoU threshold | 0.45 |
| Inference image size | 640 |
| Target analysis rate | 5 FPS |
| Annotated JPEG interval | Every 25 analyzed frames |
| Device | Auto-select; CPU in this environment |

The service loads the model lazily, processes one decoded frame at a time, filters at inference and extraction, and falls back to CPU if a CUDA prediction fails. It never loads the entire video into memory.

## Acceptance criteria

- Every persisted detection is `class_id = 0` and `class = person`.
- Bounding boxes, confidence, centroids, frame indexes, and timestamps are persisted.
- JSON, CSV, annotated frames, and annotated sampled video are generated.
- The API starts and retrieves detection jobs without exposing internal exceptions.
- The dashboard displays status, progress, observations, artifact links, and annotated video.
- Phase 1 regressions and the frontend production build remain green.
- No Phase 3 logic is introduced.

