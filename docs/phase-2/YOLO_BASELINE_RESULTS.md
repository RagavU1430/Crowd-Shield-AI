# CROWD-SHIELD — YOLOv8n Baseline Results

## Baseline configuration

| Item | Value |
|---|---|
| Model | YOLOv8n, existing local `yolov8n.pt` |
| Task | Detection only |
| Included class | Person, COCO class 0 |
| Confidence threshold | 0.35 |
| IoU threshold | 0.45 |
| Image size | 640 |
| Sample rate | 5 FPS from 60 FPS sources; interval 12 |
| Device | CPU |

## Full-video baseline

| Video | Frames analyzed | Min | Max | Mean persons/frame | Mean detection confidence | Peak time (s) |
|---|---:|---:|---:|---:|---:|---:|
| `21-32-01` | 161 | 0 | 4 | 0.763975 | 0.476785 | 21.8 |
| `21-32-40` | 196 | 0 | 4 | 0.561224 | 0.474542 | 28.8 |
| `21-33-43` | 331 | 0 | 2 | 0.126888 | 0.474025 | 50.2 |
| `21-38-15` | 357 | 0 | 4 | 0.742297 | 0.582691 | 30.8 |
| **Total/weighted** | **1,045** | **0** | **4** | **0.516746** | **0.528086** | — |

There were 540 persisted person detections across all sampled frames. Every persisted record was validated as class 0/person, and every calculated centroid was inside its corresponding bounding box.

## Qualitative observations

These labels describe the evidence available in this local footage, not scientific model accuracy.

| Condition | Result | Observation |
|---|---|---|
| Clear 1080p frames | MODERATE | Person detections were produced with usable boxes and centroids, but counts were intermittent. |
| Moving camera | MODERATE | The pipeline remained stable and emitted detections; camera motion makes frame-to-frame comparison less controlled. |
| Dense crowd | WEAK | Dense crowds are not represented by the observed 0–4 detections/frame. |
| Heavy occlusion | WEAK | No labeled occlusion cases exist, so robustness cannot be established. |
| Low resolution | NOT EVALUATED | All source videos are 1920x1080. |
| Different lighting | NOT EVALUATED | No labeled condition groups are available. |

## Output schema

Each analyzed frame records `frame_index`, `timestamp`, `person_count`, `average_confidence`, and a list of detections. Each detection contains:

```json
{
  "class": "person",
  "class_id": 0,
  "confidence": 0.83,
  "bbox": [x1, y1, x2, y2],
  "centroid": [centroid_x, centroid_y]
}
```

The results deliberately contain no tracking ID, name, identity, biometric value, density label, crowd-state label, risk score, prediction, or intervention.

## Baseline conclusion

The pretrained local model is operational for Phase 2 engineering integration. This baseline proves the decode-to-detection-to-artifact bridge; it does not establish production accuracy. A labeled and representative validation set is required before making accuracy claims or selecting a final threshold.

