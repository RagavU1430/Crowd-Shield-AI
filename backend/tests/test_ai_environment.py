"""Real AI environment smoke tests; no risk or simulation behavior."""

from pathlib import Path
import os

RUNTIME_DIR = Path(__file__).resolve().parents[1] / ".runtime"
os.environ.setdefault("YOLO_CONFIG_DIR", str(RUNTIME_DIR))
os.environ.setdefault("MPLCONFIGDIR", str(RUNTIME_DIR / "matplotlib"))

import cv2
import torch
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "yolov8n.pt"
VIDEO = ROOT / "backend" / "uploads" / "vertical_slice_test.mp4"


def test_pytorch_import_and_cpu_fallback():
    assert torch.__version__
    assert torch.device("cpu").type == "cpu"


def test_opencv_import_and_video_frame():
    capture = cv2.VideoCapture(str(VIDEO))
    try:
        assert capture.isOpened()
        success, frame = capture.read()
        assert success and frame.size > 0
    finally:
        capture.release()


def test_yolo_model_loads_from_local_file():
    assert MODEL.is_file()
    model = YOLO(str(MODEL))
    assert model.model is not None


def test_yolo_single_frame_inference_returns_result():
    capture = cv2.VideoCapture(str(VIDEO))
    try:
        success, frame = capture.read()
        assert success
    finally:
        capture.release()
    result = YOLO(str(MODEL)).predict(frame, classes=[0], conf=0.35, device="cpu", verbose=False)
    assert len(result) == 1
    assert result[0].boxes is not None
