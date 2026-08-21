# CROWD-SHIELD — YOLO Readiness Report

**Scope:** Environment/model-readiness testing only. No product detection, tracking, crowd-state, risk, or simulation feature was implemented.

## Readiness Summary

| Check | Result | Evidence |
|---|---|---|
| `from ultralytics import YOLO` | PASS | Ultralytics 8.4.124 imported locally. |
| Model initialization | PASS | Local `yolov8n.pt` opened. |
| Model loading | PASS | 81.792 ms measured wall time. |
| Single-image inference | PASS | Local bundled `bus.jpg`, CPU, 405.163 ms after warm-up. |
| Person-class filter | PASS | `classes=[0]`, confidence 0.35; three people returned. |
| Single-video-frame inference | PASS | OpenCV BGR arrays accepted directly. |
| Sampled video inference | PASS | Frames 0, 5, and 10 completed. |
| CPU performance | PASS | Mean 151.760 ms/frame, approximately 6.589 FPS. |
| GPU performance | NOT AVAILABLE | `torch.cuda.is_available()` false; device count 0. |
| Dataset readiness | NOT AVAILABLE | No local YOLO dataset found. |
| Phase 1 bridge | PASS | Uploaded-video OpenCV frame was accepted by YOLO. |

## Model and Input

- Model: root `yolov8n.pt`, 6,549,796 bytes.
- A byte-identical duplicate exists at `backend/yolov8n.pt`; retained per instruction.
- Confidence threshold: 0.35.
- Person class: COCO class 0 only.
- Image size: 640 for inference.
- Device: CPU.
- Person test image: Ultralytics package-local `assets/bus.jpg` (no download during inference).

## Person Detection Output

The small local person image produced:

| # | x1 | y1 | x2 | y2 | Confidence | centroid_x | centroid_y |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 48.550 | 398.552 | 245.346 | 902.703 | 0.8657 | 146.948 | 650.627 |
| 2 | 669.473 | 392.186 | 809.720 | 877.035 | 0.8528 | 739.597 | 634.611 |
| 3 | 221.517 | 405.799 | 344.971 | 857.537 | 0.8252 | 283.244 | 631.668 |

**Single-image person detection result: PASS.** These are direct pretrained-model outputs, not accuracy ground truth.

## Sampled Video Inference

Input: `backend/uploads/CS_BENCH_6119FE_benchmark_crowd.mp4`

```text
Frame 0: 0 persons
Frame 5: 0 persons
Frame 10: 0 persons
```

| Frame | Persons | Inference time | Approx. FPS | Person confidences |
|---:|---:|---:|---:|---|
| 0 | 0 | 158.934 ms | 6.292 | none |
| 5 | 0 | 126.412 ms | 7.911 | none |
| 10 | 0 | 169.934 ms | 5.885 | none |
| **Mean** | — | **151.760 ms** | **6.589** | — |

**Video environment result: PASS.** The model executed successfully on every requested sample. Detection usefulness on this clip is weak because it contains rendered particles rather than photorealistic people.

The pre-existing `VideoAnalysisPipeline` reported approximately 158 “people” on its regenerated synthetic clip, but source verification shows these are contour-fallback particles with fixed 0.88 confidence when YOLO returns fewer than ten detections. They must not be represented as YOLO person detections.

## CPU/GPU Performance

| Device | Inference time/frame | Approx. FPS | Memory | Result |
|---|---:|---:|---:|---|
| CPU | 151.760 ms mean on sampled video frames | 6.589 | Process RSS 262.066 MB before model, 280.027 MB after load, 401.422 MB after inference; +139.355 MB | PASS |
| GPU | Not measured | Not measured | CUDA device count 0 | NOT AVAILABLE |

Memory is process RSS, not isolated model allocation. The single-image wall time was 405.163 ms after one warm-up; source size and preprocessing differ from the video frames.

## Phase 1 → YOLO Compatibility

```text
Uploaded MP4 → Phase 1 safe storage → OpenCV VideoCapture
→ 480×640×3 BGR frame → YOLO.predict(classes=[0]) → result.boxes
```

- Input frame shape: 480×640×3.
- Bridge inference: 166.275 ms on CPU.
- Person count on synthetic frame: 0.
- Type/shape conversion errors: none.

**Result: PASS.** Zero detections are a content result, not a pipeline compatibility failure.

## Crowd Difficulty Evaluation

Skipped. No local photorealistic crowd samples exist for normal crowd, dense crowd, occlusion, low resolution, camera angle, or lighting comparisons. The particle benchmark is not valid evidence for those conditions.

## Dataset Readiness

Repository search found no:

- images/labels dataset tree;
- YOLO `data.yaml`/`data.yml`;
- train/validation/test splits;
- annotation text files or class definitions.

**Status: NOT AVAILABLE.** No local dataset available for training-readiness evaluation. No training, conversion, fine-tuning, or large-model download was performed.

## Recommendation

YOLOv8n is ready for Phase 2 CPU prototyping after approval. Before claiming crowd-video quality or performance targets, add a small ethically sourced, licensed, photorealistic validation set with people at varied density/occlusion and preserve a strict distinction between YOLO boxes and contour fallback particles.
