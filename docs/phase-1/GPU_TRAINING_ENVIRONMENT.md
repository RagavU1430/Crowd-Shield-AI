# CROWD-SHIELD: GPU Training Environment

**Document ID:** CS-DOC-P1-GPU-01
**Version:** 1.0.0
**Status:** DRAFT (Phase 1 Context)

## Hardware Audit

**Detection Method:** `nvidia-smi`

| Property | Value |
|---|---|
| **GPU Model** | NVIDIA GeForce RTX 3050 |
| **GPU VRAM** | 6144 MiB (6 GB GDDR6) |
| **NVIDIA Driver** | 595.97 |
| **CUDA Version** | 13.2 |
| **GPU PCI-Bus ID** | 00000000:01:00.0 |
| **GPU Utilization (at check)** | 14% |
| **Fan Temperature** | 43°C |
| **Power Usage** | 3W / 75W cap |

**Detection Command:**
```bash
nvidia-smi
```

**GPU Availability to PyTorch (before install):** `False` (CPU-only PyTorch installed)

## Current Environment

| Property | Value |
|---|---|
| **Python Version** | 3.11.9 (CPython) |
| **System Architecture** | x86_64 / AMD64 |
| **OS** | Windows 10/11 (64-bit) |
| **Primary Python Env** | System Python (base) |
| **Project Base Dir** | `C:\Users\Ragav U\OneDrive\Desktop\Ragav Folder\Projects\Dev Fusion` |

### System Python (Base Environment)

| Property | Value |
|---|---|
| **Python** | 3.11.9 |
| **PyTorch** | 2.13.0+cpu (CPU-only) |
| **CUDA Available** | `False` |
| **Ultralytics** | 8.4.124 |
| **YOLO Model** | yolov8n.pt |
| **CPU Inference FPS** | ~6.59 (on sampled video 640x480, 90 frames) |

**Base Environment Status:** `PRESERVED - UNCHANGED`
- The original system Python environment is untouched.
- No global Python packages were uninstalled or modified.
- `nvidia-smi` still reports the same GPU and driver.
- CPU inference performance is unchanged.

### Training Environment (Separate venv)

| Property | Value |
|---|---|
| **Venv Path** | `C:\Users\Ragav U\OneDrive\Desktop\Ragav Folder\Projects\Dev Fusion\.venv-training` |
| **Python Version** | 3.11.9 (via venv) |
| **PyTorch** | 2.2.2+cpu (CPU-only, installed via `pip install torch torchvision torchaudio`) |
| **CUDA Available** | `False` in current venv configuration |
| **Ultralytics** | 8.4.124 (compatible) |
| **YOLO Model** | yolov8n.pt (compatible, runs on CPU) |

**Venv Creation Command:**
```bash
python -m venv "C:\Users\Ragav U\OneDrive\Desktop\Ragav Folder\Projects\Dev Fusion\.venv-training"
```

**Training Venv Status:** `READY (CPU-only)`
- Separate environment created successfully.
- Main system Python is unmodified.
- Venv can be activated with: `.\.venv-training\Scripts\activate`
- Venv is isolated and will not affect the base environment.

## CUDA-Enabled PyTorch Installation Status

**Attempted Installations:** Multiple attempts to install `torch` with CUDA 11.8/12.1/13.2 support.

**Result:** All pip installs timed out (>90s) due to network/index restrictions in the current environment.

**Blocking Issue:** Unable to fetch CUDA PyTorch wheels from `https://download.pytorch.org/whl/...` index URLs.

**Possible Resolution (pending network access):**
- Use a machine with outbound PyPI access.
- Use a CUDA wheel offline installer.
- Install via `conda` channel if available.
- Upgrade pip and retry with corrected index URLs.

**If CUDA PyTorch is successfully installed, verify with:**
```python
import torch
print(torch.__version__)
print(torch.version.cuda)   # e.g., 12.1 or 11.8
print(torch.cuda.is_available())  # True
print(torch.cuda.device_count())    # 1
print(torch.cuda.get_device_name(0))  # "NVIDIA GeForce RTX 3050"
```

## YOLO GPU Readiness

**Current State:** YOLOv8n loaded and runs on CPU only.

**Load Command (CPU):**
```python
from ultralytics import YOLO
model = YOLO("yolov8n.pt")  # loads on CPU by default
```

**GPU Load Command (once CUDA PyTorch is installed):**
```python
from ultralytics import YOLO
model = YOLO("yolov8n.pt")  
model.to(device=0)  # move model to GPU
# or
model = YOLO("yolov8n.pt", device=0)  # load directly on GPU
```

**Inference Test (CPU, verified):**
- Sample: 640x480 video, 90 frames
- FPS: ~6.59 (single-threaded CPU)
- Model: yolov8n.pt (PyTorch 2.13.0+cpu)

**GPU Inference (pending CUDA PyTorch):**
- Expected FPS: 25-40+ (depending on batch size and optimization)
- Device transfer: `model.to(0)` or `torch.cuda.is_available()`

## GPU Memory Test

**Allocation Test (CPU-only environment, no CUDA available):**
- `torch.zeros(3, 256, 256, device="cuda")` → raises `RuntimeError: CUDA is not available`
- Memory release: N/A (CUDA not available)

**Expected (with CUDA PyTorch):**
- Small allocation: `torch.zeros(1, 3, 224, 224, device="cuda")` → succeeds
- Allocated VRAM: ~1.4 MB (for 1x3x224x224 float32)
- Release: `torch.cuda.empty_cache()` or let garbage collector handle

## Application Environment Status

| Component | Status | Notes |
|---|---|---|
| **Frontend** | UNCHANGED | React + Vite; no modifications |
| **Backend API** | UNCHANGED | FastAPI + Phase 1 endpoints; no modifications |
| **Crowd-Risk Engine** | UNCHANGED | Python-only; no GPU dependencies |
| **Intervention Engine** | UNCHANGED | Python-only; no GPU dependencies |
| **Video Processing** | UNCHANGED | OpenCV metadata extraction; CPU |
| **Phase 1 AI Pipeline** | UNCHANGED | YOLO + optical flow + risk engine; CPU only |
| **Existing Inference** | FUNCTIONAL | ~6.59 FPS on CPU; works correctly |

**Critical Safety Rule Obeyed:**
- No NVIDIA driver modifications
- No Windows registry changes
- No BIOS changes
- No global PATH alterations
- No unrelated Python installations affected
- Project-local venv used for training environment

## Dependency Isolation

| Layer | Environment | Package Status |
|---|---|---|
| **Application Runtime** | System Python (base) | PyTorch 2.13.0+cpu, CUNA unavailable |
| **Training Environment** | `.venv-training` | PyTorch 2.2.2+cpu, CUNA unavailable |
| **Frontend** | Node.js + React (separate dir) | Vite 6, React 19; completely separate |
| **Backend** | FastAPI (system) | FastAPI, OpenCV, Pydantic; CPU-only |

**Isolation Verification:**
- Application venv vs training venv are separate directory trees.
- No shared site-packages that could contaminate each other.
- Frontend/backend codepaths unchanged.
- CUDA-related packages not installed system-wide.

## Compatibility Issues

| Issue | Severity | Impact | Resolution |
|---|---|---|---|
| **CUDA PyTorch install timeout** | BLOCKER | Prevents GPU training verification | Requires network access or offline wheel |
| **Python 3.11 + CUDA compatibility** | None (if install succeeds) | 3.11 supported by PyTorch 2.2+ CUDA wheels | N/A (pending install) |
| **RTX 3050 + CUDA 13.2 driver** | None (hw verified) | Fully compatible | Verified via `nvidia-smi` |
| **Main env contamination risk** | LOW | Venv isolation practiced | Verified venv directories are separate |

## Changes Made

| Change | Target | Date | Status |
|---|---|---|---|
| Created `.venv-training` | Project dir | See venv creation | `COMPLETE` |
| Installed PyTorch in venv | `.venv-training` | See pip output | `COMPLETE (CPU-only)` |
| Verified `nvidia-smi` | System | Ongoing | `COMPLETE` |
| Verified main Python env | System Python | Ongoing | `COMPLETE (unchanged)` |
| Created `GPU_TRAINING_ENVIRONMENT.md` | docs/phase-1/ | This session | `COMPLETE` |
| Created `GPU_TRAINING_READINESS_REPORT.md` | docs/phase-1/ | Pending | `PENDING` |

## Rollback Instructions

If the training environment needs to be rolled back or deleted:

```bash
# Delete the training venv entirely (safe - does not affect system Python)
rm -rf "C:\Users\Ragav U\OneDrive\Desktop\Ragav Folder\Projects\Dev Fusion\.venv-training"

# Verify main environment still works
python --version  # should still report 3.11.9

# Verify nvidia-smi unchanged
nvidia-smi  # should report same GPU/driver
```

## Final Status

| Criterion | Status | Notes |
|---|---|---|
| NVIDIA GPU detected | `YES` | RTX 3050, 6GB VRAM, driver 595.97, CUDA 13.2 |
| GPU training environment created | `YES` | `.venv-training` venv created and isolated |
| CUDA-enabled PyTorch installed | `NO` | Pip installs timeout; blocker noted |
| `torch.cuda.is_available() = True` | `NO` | Not achieved (CPU-only PyTorch in both envs) |
| GPU name detected by PyTorch | `NO` | Pending CUDA install |
| GPU memory accessible | `NO` | Pending CUDA install |
| Ultralytics loads | `YES` | `YOLO("yolov8n.pt")` loads on CPU |
| YOLO runs on GPU | `NO` | Pending CUDA PyTorch install |
| Training smoke test | `SKIPPED` | Cannot run without CUDA PyTorch |
| Existing application unchanged | `YES` | Main Python/env unmodified |
| Frontend modifications | `NO` | None made |
| Backend architecture changes | `NO` | None made |
| Phase 2 implementation | `NO` | Not started (as instructed) |
| Actual model training | `NO` | Not performed |
| Documentation created | `YES` | `GPU_TRAINING_ENVIRONMENT.md` completed |

## Final Terminal Summary

```bash
========================================
CROWD-SHIELD GPU TRAINING SWITCH
========================================

NVIDIA GPU: DETECTED
  Model: NVIDIA GeForce RTX 3050
  VRAM: 6144 MiB
  Driver: 595.97
  CUDA: 13.2

GPU: 
  Detected by nvidia-smi: YES
  Available to PyTorch: NO (CPU-only)
  PyTorch version: 2.2.2+cpu (venv), 2.13.0+cpu (system)

CUDA: 
  AVAILABLE (driver level): YES
  Available (PyTorch): NO
  Version: 13.2 (driver), N/A (PyTorch)

PYTORCH: 
  Version: 2.2.2+cpu (training venv)
  CUDA: not available

PYTORCH CUDA: 
  false

TRAINING ENVIRONMENT: 
  READY (CPU-only) / FAILED (GPU)
  .venv-training created and isolated

YOLO GPU: 
  PASS (CPU load) / FAIL (GPU load)
  YOLOv8n loads on CPU; GPU not available

GPU MEMORY: 
  PASS (info available) / FAIL (access)
  nvidia-smi shows 6144 MiB; PyTorch cannot access

TRAINING SMOKE TEST: 
  SKIPPED (cannot verify GPU without CUDA PyTorch)

EXISTING APPLICATION: 
  UNCHANGED / ISSUE
  Main Python 3.11.9 environment intact; no modifications

OVERALL: 
  GPU TRAINING READY / NOT READY
  — GPU hardware DETECTED but CUDA PyTorch INSTALL BLOCKED by network restrictions.
  — Separate training environment CREATED (CPU-only).
  — GPU training VERIFICATION PENDING network access for CUDA wheel fetch.
```

**Next Steps (requires approval/network access):**
1. Gain PyPI/cuda-index network access, OR
2. Obtain offline CUDA PyTorch wheel, OR
3. Use `conda` environment for GPU training, OR
4. Proceed with CPU-only training for Phase 1 continuation.

**Task Status:** `GPU TRAINING ENVIRONMENT SETUP INTERRUPTED BY NETWORK BLOCKER`

**Do not proceed to Phase 2. Do not train the actual YOLO model. Wait for explicit approval.**