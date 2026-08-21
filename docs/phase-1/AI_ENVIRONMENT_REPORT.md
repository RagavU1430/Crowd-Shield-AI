# CROWD-SHIELD — AI Environment Report

**Measured:** 2026-08-20  
**Interpreter:** Python 3.14.5, Windows x64  
**Environment result:** PASS with CPU fallback; CUDA not available

## Package Compatibility

| Package | Version | Status | Purpose | Compatibility |
|---|---:|---|---|---|
| fastapi | 0.141.1 | PASS | Backend API | Imports and 17 tests pass on Python 3.14.5. |
| uvicorn | 0.52.1 | PASS | ASGI server | Local server started and served health/upload traffic. |
| pydantic | 2.13.4 | PASS | API schemas | Phase 1 response models validate. |
| python-multipart | 0.0.32 | PASS | Multipart upload parsing | Real E2E upload succeeds. |
| python-dotenv | 1.2.2 | PASS | Local environment configuration | Used by backend startup. |
| opencv-python | 4.13.0.92 | PASS | Video metadata and frame pipeline | Actual MP4 open/read/resize/color/save/release succeeds. |
| numpy | 2.4.6 | PASS | Array/frame computations | Imports and readiness probe pass. |
| scipy | 1.17.1 | PASS / UNUSED | Future scientific utilities | Compatible, but current application code does not import it. |
| torch | 2.13.0+cpu | PASS | YOLO tensor runtime | CPU inference passes; this wheel has no CUDA runtime. |
| torchvision | 0.28.0 | PASS | PyTorch vision compatibility | Imports through the tested vision environment. |
| ultralytics | 8.4.124 | PASS | YOLOv8 model API | Import, model load, image/frame inference pass. |
| networkx | 3.6.1 | PASS | Pre-existing venue graph module | Resolves the previous backend import failure. |
| pytest | 9.1.1 | PASS | Test runner | 17 passed, 0 failed. |
| httpx | 0.28.1 | PASS with warning | FastAPI test client transport | Tests pass; Starlette emits one deprecation warning. |

`pip check` returned: **No broken requirements found.**

## Python Compatibility Finding

The existing Phase 1 report claimed Python 3.11.9, but the active environment is Python 3.14.5. Separate Python 3.11.9 and 3.13.10 executables exist locally, but neither had the required project stack. The tested Python 3.14 environment has compatible current wheels for OpenCV, PyTorch, torchvision, and Ultralytics.

## PyTorch Device Test

```text
torch:           2.13.0+cpu
CUDA available:  False
CUDA devices:    0
GPU name:        not available
CPU fallback:    available
```

**Result: PASS.** GPU inference is **NOT AVAILABLE**, not failed. No driver, CUDA toolkit, Windows setting, or hardware configuration was changed.

## OpenCV Pipeline Test

Input: `backend/uploads/vertical_slice_test.mp4`

| Check | Actual result |
|---|---|
| Import/version | PASS — 4.13.0 |
| Video open | PASS |
| Metadata | 640×480, 15.0 fps, 90 frames, 6.0 seconds |
| Frame read | PASS |
| Resize | PASS — 640×640×3 |
| BGR to RGB | PASS — 640×640×3 |
| Save frame | PASS — `backend/.runtime/crowd_shield_test_frame.jpg` |
| Release | PASS — both captures released in `finally` blocks |

**Result: PASS.** The saved frame and Ultralytics settings are ignored runtime artifacts and were not added to product code.

## Installation Notes

The project originally lacked a requirements file and the active environment lacked `networkx`, `torch`, `torchvision`, and `ultralytics`. The first pip attempt was blocked by sandbox networking. After explicit approval, only declared project/readiness dependencies were installed. No suspicious software or system-level packages were installed.

## Environment Risks

- Python 3.14 is newer than the documentation baseline; pin and reproduce this exact set in CI before team-wide use.
- CPU-only PyTorch means no GPU acceleration or GPU performance claim.
- PyTorch and Ultralytics add a substantial environment footprint.
- The `httpx`/Starlette deprecation warning should be monitored rather than fixed by a blind upgrade.
