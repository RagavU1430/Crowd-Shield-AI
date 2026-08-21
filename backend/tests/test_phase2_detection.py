"""Phase 2 raw person-observation tests. No Phase 3 metrics are exercised."""

from pathlib import Path
from types import SimpleNamespace
import csv
import json
import os

RUNTIME_DIR = Path(__file__).resolve().parents[1] / ".runtime"
os.environ.setdefault("YOLO_CONFIG_DIR", str(RUNTIME_DIR))
os.environ.setdefault("MPLCONFIGDIR", str(RUNTIME_DIR / "matplotlib"))

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.api import phase2
from app.api.phase1 import job_store as upload_job_store
from app.main import app
from app.services.detection.person_detector import PersonDetector, extract_person_detections
from app.services.detection.video_detection import (
    VideoDetectionPipeline,
    VideoProcessingError,
    annotate_frame,
    confidence_statistics,
    sampling_interval,
)


ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / "yolov8n.pt"
client = TestClient(app, raise_server_exceptions=False)


class Scalar:
    def __init__(self, value):
        self.value = value

    def item(self):
        return self.value


class Values:
    def __init__(self, values):
        self.values = values

    def tolist(self):
        return self.values


def box(class_id, confidence, bbox):
    return SimpleNamespace(
        cls=[Scalar(class_id)],
        conf=[Scalar(confidence)],
        xyxy=[Values(bbox)],
    )


class FakeDetector:
    model_name = "YOLOv8n-test-double"
    device = "cpu"
    confidence = 0.35

    def detect(self, _frame):
        return (
            [{
                "class": "person",
                "class_id": 0,
                "confidence": 0.8,
                "bbox": [10.0, 5.0, 30.0, 45.0],
                "centroid": [20.0, 25.0],
            }],
            2.5,
        )


def make_video(path: Path, frames: int = 12, fps: float = 6.0):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (64, 48))
    assert writer.isOpened()
    try:
        for index in range(frames):
            frame = np.full((48, 64, 3), 30 + index, dtype=np.uint8)
            writer.write(frame)
    finally:
        writer.release()


@pytest.fixture
def processed(tmp_path):
    video = tmp_path / "sample.mp4"
    make_video(video)
    pipeline = VideoDetectionPipeline(
        detector=FakeDetector(),
        output_root=tmp_path / "processed",
        target_fps=3,
        annotated_frame_interval=2,
    )
    return pipeline.process(video), tmp_path / "processed"


def test_yolo_model_loading():
    detector = PersonDetector(model_path=MODEL, device="cpu")
    assert detector.load().model is not None
    assert detector.model_name == "YOLOv8n"


def test_person_class_filtering():
    result = SimpleNamespace(boxes=[box(0, 0.9, [1, 2, 11, 22]), box(2, 0.95, [3, 4, 13, 24])])
    detections = extract_person_detections(result)
    assert len(detections) == 1
    assert detections[0]["class_id"] == 0
    assert detections[0]["class"] == "person"


def test_bounding_box_extraction():
    result = SimpleNamespace(boxes=[box(0, 0.75, [1.25, 2.5, 11.75, 22.5])])
    assert extract_person_detections(result)[0]["bbox"] == [1.25, 2.5, 11.75, 22.5]


def test_centroid_calculation():
    result = SimpleNamespace(boxes=[box(0, 0.75, [10, 20, 30, 60])])
    assert extract_person_detections(result)[0]["centroid"] == [20.0, 40.0]


def test_confidence_calculation():
    detections = [{"confidence": 0.5}, {"confidence": 0.75}, {"confidence": 1.0}]
    assert confidence_statistics(detections) == {
        "average_confidence": 0.75,
        "min_confidence": 0.5,
        "max_confidence": 1.0,
    }
    assert confidence_statistics([])["average_confidence"] is None


def test_frame_sampling():
    assert sampling_interval(60, 5) == 12
    assert sampling_interval(30, 5) == 6
    assert sampling_interval(4, 5) == 1
    with pytest.raises(ValueError):
        sampling_interval(0, 5)


def test_video_processing_and_person_count(processed):
    result, _ = processed
    assert result["summary"]["frames_analyzed"] == 6
    assert result["summary"]["maximum_people_detected"] == 1
    assert result["summary"]["minimum_people_detected"] == 1
    assert all(point["person_count"] == 1 for point in result["timeline"])


def test_json_output(processed):
    result, output = processed
    payload = json.loads((output / "results" / result["artifacts"]["detections_json"]).read_text())
    assert len(payload["frames"]) == 6
    assert payload["frames"][0]["detections"][0]["class_id"] == 0
    assert payload["summary"]["average_confidence"] == 0.8


def test_csv_output(processed):
    result, output = processed
    with (output / "results" / result["artifacts"]["frame_summary_csv"]).open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 6
    assert rows[0]["person_count"] == "1"
    assert rows[0]["average_confidence"] == "0.8"


def test_annotated_frame_and_video_output(processed):
    result, output = processed
    assert result["artifacts"]["annotated_frames"]
    assert (output / "frames" / result["artifacts"]["annotated_frames"][0]).is_file()
    assert result["summary"]["annotated_video_available"]
    assert (output / "annotated" / result["artifacts"]["annotated_video"]).stat().st_size > 0
    source = np.zeros((50, 50, 3), dtype=np.uint8)
    assert np.any(annotate_frame(source, FakeDetector().detect(source)[0]) != source)


def test_invalid_video_handling(tmp_path):
    invalid = tmp_path / "invalid.mp4"
    invalid.write_bytes(b"not a video")
    with pytest.raises(VideoProcessingError, match="could not be opened|corrupted"):
        VideoDetectionPipeline(detector=FakeDetector(), output_root=tmp_path / "out").process(invalid)


def test_detection_api_start_and_retrieve(monkeypatch, tmp_path):
    source = tmp_path / "safe.mp4"
    source.write_bytes(b"placeholder for mocked processing")
    upload_job_store["job_phase2_test"] = {"video_id": source.name}
    monkeypatch.setattr(phase2, "UPLOAD_DIR", tmp_path)

    fake_result = {
        "video": {"filename": source.name},
        "analysis": {"model": "YOLOv8n", "device": "cpu"},
        "summary": {"maximum_people_detected": 1},
        "timeline": [{"frame_index": 0, "timestamp": 0, "person_count": 1, "average_confidence": 0.8}],
        "artifacts": {
            "detections_json": "safe_detections.json",
            "frame_summary_csv": "safe_frame_summary.csv",
            "summary_json": "safe_summary.json",
            "annotated_video": "safe_annotated.mp4",
            "annotated_frames": ["safe_frame_00000000.jpg"],
        },
    }
    monkeypatch.setattr(phase2.pipeline, "process", lambda *_args, **_kwargs: fake_result)
    phase2.detection_store.pop("job_phase2_test", None)

    started = client.post("/api/analysis/job_phase2_test/detect")
    assert started.status_code == 202
    retrieved = client.get("/api/analysis/job_phase2_test/detections")
    assert retrieved.status_code == 200
    body = retrieved.json()
    assert body["status"] == "COMPLETED"
    assert body["result"]["timeline"][0]["person_count"] == 1
    assert body["result"]["artifacts"]["annotated_video"].startswith("/processed/annotated/")
