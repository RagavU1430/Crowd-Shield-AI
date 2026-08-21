"""Focused Phase 1 API and video-ingestion tests."""

from pathlib import Path
import re

import cv2
import pytest
from fastapi.testclient import TestClient

from app.api import phase1
from app.main import app


ROOT = Path(__file__).resolve().parents[2]
SAMPLE_VIDEO = ROOT / "backend" / "uploads" / "vertical_slice_test.mp4"
client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def isolated_upload_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(phase1, "UPLOAD_DIR", tmp_path)
    phase1.job_store.clear()


def sample_bytes() -> bytes:
    return SAMPLE_VIDEO.read_bytes()


def upload(name: str = "test_video.mp4"):
    return client.post(
        "/api/videos/upload",
        files={"file": (name, sample_bytes(), "video/mp4")},
    )


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "crowd-shield-backend",
        "phase": "phase-1",
    }


def test_valid_upload_returns_metadata_and_job():
    response = upload()
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "VALID"
    assert body["duration"] == pytest.approx(6.0, abs=0.01)
    assert (body["width"], body["height"], body["frame_count"]) == (640, 480, 90)
    assert body["fps"] == pytest.approx(15.0, abs=0.01)
    assert body["job_id"].startswith("job_")


def test_upload_uses_safe_server_filename(tmp_path):
    body = upload("../../unsafe name.mp4").json()
    assert re.fullmatch(r"[0-9a-f]{32}\.mp4", body["video_id"])
    assert body["filename"] == "unsafe name.mp4"
    assert (tmp_path / body["video_id"]).is_file()
    assert not (tmp_path / "unsafe name.mp4").exists()


def test_unsupported_extension_has_structured_error():
    response = client.post(
        "/api/videos/upload",
        files={"file": ("test.exe", b"bad", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_FORMAT"


def test_unsupported_mime_has_structured_error():
    response = client.post(
        "/api/videos/upload",
        files={"file": ("test.mp4", sample_bytes(), "text/plain")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "UNSUPPORTED_MIME_TYPE"


def test_invalid_video_is_rejected_and_removed(tmp_path):
    response = client.post(
        "/api/videos/upload",
        files={"file": ("invalid.mp4", b"\x00\x00\x00\x01", "video/mp4")},
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_VIDEO"
    assert list(tmp_path.iterdir()) == []


def test_file_size_limit_is_streamed_and_enforced(monkeypatch, tmp_path):
    monkeypatch.setattr(phase1, "MAX_UPLOAD_SIZE_MB", 1)
    response = client.post(
        "/api/videos/upload",
        files={"file": ("large.mp4", b"x" * (1024 * 1024 + 1), "video/mp4")},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "FILE_TOO_LARGE"
    assert list(tmp_path.iterdir()) == []


def test_job_creation_and_status_retrieval():
    uploaded = upload().json()
    response = client.get(f"/api/analysis/{uploaded['job_id']}")
    assert response.status_code == 200
    assert response.json() == {
        "job_id": uploaded["job_id"],
        "video_id": uploaded["video_id"],
        "status": "COMPLETED",
        "progress": 100,
        "stage": "Video validated and ready for future analysis",
    }


def test_missing_job_has_structured_error():
    response = client.get("/api/analysis/job_missing")
    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "JOB_NOT_FOUND", "message": "Missing job"}
    }


def test_cors_allows_configured_frontend():
    response = client.options(
        "/api/videos/upload",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"


def test_cors_does_not_allow_unknown_origin():
    response = client.options(
        "/api/videos/upload",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in response.headers


def test_video_can_open_read_frame_and_extract_metadata():
    capture = cv2.VideoCapture(str(SAMPLE_VIDEO))
    try:
        assert capture.isOpened()
        assert int(capture.get(cv2.CAP_PROP_FRAME_COUNT)) == 90
        assert capture.get(cv2.CAP_PROP_FPS) == pytest.approx(15.0, abs=0.01)
        success, frame = capture.read()
        assert success
        assert frame.shape == (480, 640, 3)
    finally:
        capture.release()


def test_phase1_routes_are_reachable():
    assert client.get("/api/analysis/job_missing").status_code == 404
    assert client.post("/api/videos/upload").status_code == 422
