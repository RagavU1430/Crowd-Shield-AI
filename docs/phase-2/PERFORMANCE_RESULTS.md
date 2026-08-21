# CROWD-SHIELD — Phase 2 Performance Results

## Environment

| Item | Result |
|---|---|
| Python | 3.14.5 |
| PyTorch | 2.13.0+cpu |
| CUDA available | No |
| CUDA device count | 0 |
| Model | YOLOv8n |
| Input image size | 640 |
| Target sample rate | 5 FPS |
| Sources | 1920x1080, 60 FPS, H.264 |

The existing `.venv-training` launcher points to an unavailable Python installation and was not used. No GPU driver or system setting was changed. CPU fallback is available and was used for all measurements.

## Per-video measurements

| Video | Analyzed frames | Processing (s) | YOLO inference (s) | End-to-end processing FPS | Mean inference ms/frame* |
|---|---:|---:|---:|---:|---:|
| `21-32-01` | 161 | 54.504000 | 19.611851 | 2.953912 | 121.813 |
| `21-32-40` | 196 | 56.468196 | 19.936814 | 3.470980 | 101.718 |
| `21-33-43` | 331 | 94.207493 | 33.748329 | 3.513521 | 101.958 |
| `21-38-15` | 357 | 105.234661 | 35.735265 | 3.392418 | 100.099 |
| **Aggregate** | **1,045** | **310.414350** | **109.032259** | **3.366466** | **104.337** |

\*Measured YOLO-call time divided by analyzed frames. It excludes decode, annotation, JPEG/MP4 encoding, and JSON/CSV writes.

The 5 FPS value is the analysis sampling rate, not achieved wall-clock throughput. Aggregate offline throughput was 3.366466 analyzed frames/second because processing includes decode and artifact encoding.

## Device comparison

| Device | Inference time/frame | Approx inference FPS | Availability |
|---|---:|---:|---|
| CPU | 104.337 ms aggregate | 9.584 | PASS |
| GPU | Not measured | Not measured | NOT AVAILABLE |

No GPU values are estimated or fabricated. The baseline is suitable for offline sampled processing on this CPU. Realtime or higher-throughput requirements need separate profiling on an available supported GPU and should not be inferred from these measurements.

## Artifact sizes and integrity

| Video | Annotated MP4 bytes | Annotated video frames | Saved JPEGs | Integrity |
|---|---:|---:|---:|---|
| `21-32-01` | 25,484,092 | 161 | 7 | PASS |
| `21-32-40` | 31,125,034 | 196 | 8 | PASS |
| `21-33-43` | 54,784,991 | 331 | 14 | PASS |
| `21-38-15` | 61,973,476 | 357 | 15 | PASS |

For every video, JSON frame count, CSV row count, and annotated MP4 frame count equal the reported analyzed-frame count. Each MP4 opens in OpenCV, yields a readable first frame, reports 5 FPS, and preserves 1920x1080 resolution.

