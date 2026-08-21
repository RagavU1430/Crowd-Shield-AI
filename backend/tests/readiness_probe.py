"""Bounded, read-only Phase 2 environment readiness probe (no product AI implementation)."""

from importlib.metadata import version
from pathlib import Path
from time import perf_counter
import json
import os

RUNTIME_DIR = Path(__file__).resolve().parents[1] / ".runtime"
os.environ.setdefault("YOLO_CONFIG_DIR", str(RUNTIME_DIR))
os.environ.setdefault("MPLCONFIGDIR", str(RUNTIME_DIR / "matplotlib"))

import cv2
import numpy as np
import psutil
import torch
import ultralytics
from ultralytics import YOLO


ROOT = Path(__file__).resolve().parents[2]
VIDEO = ROOT / "backend" / "uploads" / "vertical_slice_test.mp4"
CROWD_VIDEO = ROOT / "backend" / "uploads" / "CS_BENCH_6119FE_benchmark_crowd.mp4"
MODEL = ROOT / "yolov8n.pt"
OUTPUT_FRAME = RUNTIME_DIR / "crowd_shield_test_frame.jpg"


def person_rows(result):
    rows = []
    if result.boxes is None:
        return rows
    for box in result.boxes:
        class_id = int(box.cls[0].item())
        if class_id != 0:
            continue
        x1, y1, x2, y2 = (float(value) for value in box.xyxy[0].tolist())
        rows.append({
            "x1": round(x1, 3),
            "y1": round(y1, 3),
            "x2": round(x2, 3),
            "y2": round(y2, 3),
            "confidence": round(float(box.conf[0].item()), 4),
            "centroid_x": round((x1 + x2) / 2, 3),
            "centroid_y": round((y1 + y2) / 2, 3),
        })
    return rows


def main():
    report = {
        "versions": {
            name: version(name)
            for name in (
                "fastapi", "uvicorn", "pydantic", "opencv-python", "numpy",
                "scipy", "torch", "torchvision", "ultralytics", "networkx",
            )
        },
        "torch": {
            "version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "device_count": torch.cuda.device_count(),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            "cpu_fallback": True,
        },
        "opencv": {"version": cv2.__version__},
    }

    capture = cv2.VideoCapture(str(VIDEO))
    try:
        opened = capture.isOpened()
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        success, frame = capture.read()
        if not success:
            raise RuntimeError("Could not read the Phase 1 sample video frame")
        resized = cv2.resize(frame, (640, 640))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        saved = cv2.imwrite(str(OUTPUT_FRAME), resized)
    finally:
        capture.release()

    report["opencv"].update({
        "opened": opened,
        "fps": fps,
        "frame_count": frame_count,
        "width": width,
        "height": height,
        "duration_seconds": frame_count / fps,
        "read_frame": success,
        "resized_shape": list(resized.shape),
        "rgb_shape": list(rgb.shape),
        "saved_frame": saved,
        "saved_frame_path": str(OUTPUT_FRAME),
    })

    process = psutil.Process()
    memory_before = process.memory_info().rss
    load_started = perf_counter()
    model = YOLO(str(MODEL))
    load_ms = (perf_counter() - load_started) * 1000
    memory_after_load = process.memory_info().rss

    assets = Path(ultralytics.__file__).resolve().parent / "assets"
    person_image = assets / "bus.jpg"
    if not person_image.exists():
        raise RuntimeError(f"Ultralytics local test asset missing: {person_image}")

    model.predict(source=str(person_image), classes=[0], conf=0.35, imgsz=640, device="cpu", verbose=False)
    image_started = perf_counter()
    image_result = model.predict(
        source=str(person_image), classes=[0], conf=0.35, imgsz=640, device="cpu", verbose=False
    )[0]
    image_ms = (perf_counter() - image_started) * 1000
    image_people = person_rows(image_result)

    video_capture = cv2.VideoCapture(str(CROWD_VIDEO))
    sampled = []
    try:
        for frame_index in (0, 5, 10):
            video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
            ok, video_frame = video_capture.read()
            if not ok:
                raise RuntimeError(f"Could not read crowd video frame {frame_index}")
            started = perf_counter()
            result = model.predict(
                source=video_frame, classes=[0], conf=0.35, imgsz=640, device="cpu", verbose=False
            )[0]
            elapsed_ms = (perf_counter() - started) * 1000
            people = person_rows(result)
            sampled.append({
                "frame": frame_index,
                "persons": len(people),
                "inference_ms": round(elapsed_ms, 3),
                "fps": round(1000 / elapsed_ms, 3),
                "confidences": [row["confidence"] for row in people],
            })
    finally:
        video_capture.release()

    bridge_started = perf_counter()
    bridge_result = model.predict(
        source=frame, classes=[0], conf=0.35, imgsz=640, device="cpu", verbose=False
    )[0]
    bridge_ms = (perf_counter() - bridge_started) * 1000

    memory_after_inference = process.memory_info().rss
    measured_times = [row["inference_ms"] for row in sampled]
    average_ms = float(np.mean(measured_times))
    report["yolo"] = {
        "model": str(MODEL),
        "model_exists": MODEL.exists(),
        "load_ms": round(load_ms, 3),
        "test_image": str(person_image),
        "single_image_ms": round(image_ms, 3),
        "single_image_person_count": len(image_people),
        "single_image_people": image_people,
        "video": str(CROWD_VIDEO),
        "sampled_frames": sampled,
        "average_video_inference_ms": round(average_ms, 3),
        "average_video_fps": round(1000 / average_ms, 3),
        "device": "cpu",
        "process_rss_before_mb": round(memory_before / 1024 / 1024, 3),
        "process_rss_after_load_mb": round(memory_after_load / 1024 / 1024, 3),
        "process_rss_after_inference_mb": round(memory_after_inference / 1024 / 1024, 3),
        "process_rss_delta_mb": round((memory_after_inference - memory_before) / 1024 / 1024, 3),
    }
    report["phase1_to_yolo_bridge"] = {
        "source": str(VIDEO),
        "opencv_frame_shape": list(frame.shape),
        "inference_ms": round(bridge_ms, 3),
        "person_count": len(person_rows(bridge_result)),
        "compatible": True,
    }

    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats(0)
        gpu_started = perf_counter()
        model.predict(source=str(person_image), classes=[0], conf=0.35, imgsz=640, device=0, verbose=False)
        gpu_ms = (perf_counter() - gpu_started) * 1000
        report["gpu_performance"] = {
            "inference_ms": round(gpu_ms, 3),
            "fps": round(1000 / gpu_ms, 3),
            "peak_memory_mb": round(torch.cuda.max_memory_allocated(0) / 1024 / 1024, 3),
        }
    else:
        report["gpu_performance"] = None

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
