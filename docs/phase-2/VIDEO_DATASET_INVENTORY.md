# CROWD-SHIELD — Local Video Inventory

## Inventory method

All files in `videos/` were inspected locally with OpenCV. Each file opened successfully and yielded a readable first frame. Codec values below are the four-character code reported by OpenCV. No source file was edited.

| Video | Size (bytes) | Duration (s) | Resolution | FPS | Frames | Codec | Open/read |
|---|---:|---:|---|---:|---:|---|---|
| `2026-08-20 21-32-01.mp4` | 75,283,805 | 32.216667 | 1920x1080 | 60 | 1,933 | H264 | PASS |
| `2026-08-20 21-32-40.mp4` | 94,899,381 | 39.183333 | 1920x1080 | 60 | 2,351 | H264 | PASS |
| `2026-08-20 21-33-43.mp4` | 146,559,832 | 66.066667 | 1920x1080 | 60 | 3,964 | H264 | PASS |
| `2026-08-20 21-38-15.mp4` | 147,062,516 | 71.266667 | 1920x1080 | 60 | 4,276 | H264 | PASS |

Total source duration is 208.733334 seconds and total source size is 463,805,534 bytes.

## Selection rationale

An initial five-frame-per-video YOLO sample found only 0–3 visible person detections per sampled image. `2026-08-20 21-38-15.mp4` was selected as the primary baseline because it had the greatest sampled person count. `2026-08-20 21-32-01.mp4` was selected as the secondary baseline because detections were most consistent in the initial sample. All four videos were practical to process, so all four were included in the final run.

| Video | Initial sampled range | Initial sampled mean | Camera-motion observation* | Role |
|---|---:|---:|---|---|
| `21-32-01` | 0–1 | 0.8 | Likely moving | Secondary |
| `21-32-40` | 0–1 | 0.4 | Likely moving | Additional |
| `21-33-43` | 0–1 | 0.2 | Mixed/minor | Additional |
| `21-38-15` | 0–3 | 1.4 | Likely moving | Primary |

\*Camera motion was an inventory-only ORB matched-feature displacement heuristic. It is not optical flow, a product feature, or a scientific camera-motion measurement.

## Representativeness and limitations

- The footage is 1080p and technically clean enough for decoding and baseline inference.
- The model outputs show sparse visible-person scenes, not a dense crowd benchmark.
- Moving-camera footage is represented; fixed surveillance footage is not clearly represented.
- Dense crowding, heavy occlusion, low resolution, and controlled lighting variants are not adequately represented.
- No ground-truth labels exist, so detection accuracy, recall, and false-positive rates cannot be calculated.
- Confidence is the model's score for a prediction; it is not an accuracy percentage.

## Custom training dataset

No suitable local training dataset was found. There are no discovered YOLO dataset YAML files or image/label train-validation-test splits outside generated output and environments. Dataset readiness: **NOT AVAILABLE**. No training or fine-tuning was performed.

