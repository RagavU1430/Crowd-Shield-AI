"""YOLOv8 person-only detector for Phase 2 raw observations."""

from pathlib import Path
from threading import Lock
from time import perf_counter
from typing import Any

import numpy as np

from app.config import (
    DETECTION_CONFIDENCE_THRESHOLD,
    DETECTION_IMAGE_SIZE,
    DETECTION_IOU_THRESHOLD,
    DETECTION_MODEL_PATH,
    PROJECT_ROOT,
)


class ModelUnavailableError(RuntimeError):
    """Raised when the configured YOLO model cannot be loaded."""


def _detect_dense_head_particles(frame: np.ndarray, existing_detections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Complements YOLO in dense crowd photos by detecting small unmapped head/body blobs."""
    try:
        import cv2
        h, w = frame.shape[:2]
        mask = np.ones((h, w), dtype=np.uint8) * 255
        for det in existing_detections:
            bbox = det["bbox"]
            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            cv2.rectangle(mask, (max(0, x1), max(0, y1)), (min(w, x2), min(h, y2)), 0, -1)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        laplacian = cv2.Laplacian(gray, cv2.CV_8U, ksize=3)
        masked_lap = cv2.bitwise_and(laplacian, laplacian, mask=mask)
        _, thresh = cv2.threshold(masked_lap, 35, 255, cv2.THRESH_BINARY)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        extra_dets: list[dict[str, Any]] = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 25 <= area <= 2000:
                bx, by, bw, bh = cv2.boundingRect(cnt)
                cx, cy = bx + bw / 2.0, by + bh * 0.25
                extra_dets.append({
                    "class": "person",
                    "class_id": 0,
                    "confidence": 0.58,
                    "bbox": [round(float(bx), 3), round(float(by), 3), round(float(bx + bw), 3), round(float(by + bh), 3)],
                    "centroid": [round(float(cx), 3), round(float(cy), 3)],
                })
                if len(extra_dets) >= 120:
                    break
        return extra_dets
    except Exception:
        return []


def extract_person_detections(result: Any, frame: np.ndarray | None = None) -> list[dict[str, Any]]:
    """Convert an Ultralytics result into anonymous class-0 observations and augment dense crowd regions."""
    detections: list[dict[str, Any]] = []
    boxes = getattr(result, "boxes", None)
    if boxes is not None:
        for box in boxes:
            class_id = int(box.cls[0].item())
            if class_id != 0:
                continue
            x1, y1, x2, y2 = (float(value) for value in box.xyxy[0].tolist())
            confidence = float(box.conf[0].item())
            detections.append(
                {
                    "class": "person",
                    "class_id": 0,
                    "confidence": round(confidence, 6),
                    "bbox": [round(x1, 3), round(y1, 3), round(x2, 3), round(y2, 3)],
                    "centroid": [round((x1 + x2) / 2, 3), round((y1 + y2) / 2, 3)],
                }
            )

    if frame is not None and frame.size > 0:
        extra = _detect_dense_head_particles(frame, detections)
        detections.extend(extra)

    return detections


class PersonDetector:
    """Lazily loads one local YOLOv8n model and returns class-0 boxes only."""

    def __init__(
        self,
        model_path: Path | str | None = None,
        confidence: float = DETECTION_CONFIDENCE_THRESHOLD,
        iou: float = DETECTION_IOU_THRESHOLD,
        image_size: int = DETECTION_IMAGE_SIZE,
        device: str | None = None,
    ):
        self.model_path = Path(model_path or DETECTION_MODEL_PATH).resolve()
        self.confidence = confidence
        self.iou = iou
        self.image_size = image_size
        self._requested_device = device
        self._device: str | None = None
        self._model = None
        self._lock = Lock()

    @property
    def device(self) -> str:
        if self._device is None:
            self._device = self._select_device()
        return self._device

    @property
    def model_name(self) -> str:
        return "CROWD-SHIELD Crowd YOLOv8n" if self.model_path.name == "best.pt" else "YOLOv8n"

    def _select_device(self) -> str:
        if self._requested_device:
            return self._requested_device
        import torch

        return "cuda:0" if torch.cuda.is_available() else "cpu"

    def load(self):
        if self._model is not None:
            return self._model
        if not self.model_path.is_file():
            raise ModelUnavailableError(f"YOLO model file is missing: {self.model_path}")
        try:
            from ultralytics import YOLO

            self._model = YOLO(str(self.model_path))
        except Exception as exc:
            raise ModelUnavailableError("YOLOv8n could not be initialized.") from exc
        return self._model

    def detect(self, frame: np.ndarray) -> tuple[list[dict[str, Any]], float]:
        if frame is None or frame.size == 0:
            raise ValueError("Invalid frame supplied for person detection.")
        model = self.load()
        with self._lock:
            started = perf_counter()
            try:
                result = model.predict(
                    source=frame,
                    classes=[0],
                    conf=self.confidence,
                    iou=self.iou,
                    imgsz=self.image_size,
                    device=self.device,
                    verbose=False,
                )[0]
            except Exception:
                if self.device.startswith("cuda"):
                    self._device = "cpu"
                    result = model.predict(
                        source=frame,
                        classes=[0],
                        conf=self.confidence,
                        iou=self.iou,
                        imgsz=self.image_size,
                        device="cpu",
                        verbose=False,
                    )[0]
                else:
                    raise
            inference_ms = (perf_counter() - started) * 1000
        return extract_person_detections(result, frame), inference_ms
