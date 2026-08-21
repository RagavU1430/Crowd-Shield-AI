"""Phase 1-only ingestion routes with no dependency on later AI modules."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import os
import uuid

import cv2
from fastapi import APIRouter, File, UploadFile

from app.config import ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_MB, UPLOAD_DIR
from app.models.schemas import AnalysisJob, VideoUploadResponse


router = APIRouter(prefix="/api")
job_store: dict[str, dict[str, Any]] = {}

ALLOWED_MIME_TYPES = {
    ".mp4": {"video/mp4"},
    ".webm": {"video/webm"},
    ".mov": {"video/quicktime"},
    ".jpg": {"image/jpeg", "image/jpg"},
    ".jpeg": {"image/jpeg", "image/jpg"},
    ".png": {"image/png"},
    ".webp": {"image/webp"},
    ".bmp": {"image/bmp", "image/x-ms-bmp"},
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


class Phase1APIError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


def _error(status_code: int, code: str, message: str) -> None:
    raise Phase1APIError(status_code, code, message)


@router.post("/videos/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...)):
    original_filename = Path(file.filename or "").name
    extension = Path(original_filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        _error(
            400,
            "UNSUPPORTED_FORMAT",
            f"Unsupported format: {extension or '(none)'}. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    allowed_mimes = ALLOWED_MIME_TYPES.get(extension, set())
    if file.content_type and allowed_mimes and file.content_type not in allowed_mimes:
        _error(
            400,
            "UNSUPPORTED_MIME_TYPE",
            f"Unsupported MIME type: {file.content_type or '(none)' }.",
        )

    safe_filename = f"{uuid.uuid4().hex}{extension}"
    final_path = (UPLOAD_DIR / safe_filename).resolve()
    upload_root = UPLOAD_DIR.resolve()
    if final_path.parent != upload_root:
        _error(400, "UNSAFE_PATH", "The upload path is invalid.")

    temporary_path = final_path.with_suffix(final_path.suffix + ".part")
    maximum_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    total_bytes = 0

    try:
        with temporary_path.open("wb") as output:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > maximum_bytes:
                    size_str = f"{MAX_UPLOAD_SIZE_MB // 1024}GB" if MAX_UPLOAD_SIZE_MB >= 1024 else f"{MAX_UPLOAD_SIZE_MB}MB"
                    _error(
                        413,
                        "FILE_TOO_LARGE",
                        f"File too large. Maximum size: {size_str}",
                    )
                output.write(chunk)

        if extension in IMAGE_EXTENSIONS:
            image = cv2.imread(str(temporary_path))
            if image is None or image.shape[0] <= 0 or image.shape[1] <= 0:
                _error(400, "INVALID_IMAGE", "The uploaded file could not be read as a valid image.")
            height, width = image.shape[:2]
            fps = 1.0
            frame_count = 1
        else:
            capture = cv2.VideoCapture(str(temporary_path))
            try:
                if not capture.isOpened():
                    _error(400, "INVALID_VIDEO", "The uploaded file could not be read as a valid video.")

                fps = float(capture.get(cv2.CAP_PROP_FPS))
                frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
                width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
                frame_read, _ = capture.read()
                if not frame_read or fps <= 0 or frame_count <= 0 or width <= 0 or height <= 0:
                    _error(400, "INVALID_VIDEO", "The uploaded file could not be read as a valid video.")
            finally:
                capture.release()

        os.replace(temporary_path, final_path)
    except Phase1APIError:
        temporary_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        raise
    except Exception:
        temporary_path.unlink(missing_ok=True)
        final_path.unlink(missing_ok=True)
        _error(500, "UPLOAD_FAILED", "The video upload could not be completed.")
    finally:
        await file.close()

    duration = frame_count / fps
    job_id = f"job_{uuid.uuid4().hex[:12]}"
    job_store[job_id] = {
        "job_id": job_id,
        "video_id": safe_filename,
        "status": "COMPLETED",
        "progress": 100,
        "stage": "Video validated and ready for future analysis",
        "metadata": {
            "original_filename": original_filename,
            "stored_filename": safe_filename,
            "file_size": total_bytes,
            "format": extension,
            "upload_time": datetime.now(timezone.utc).isoformat(),
            "duration": round(duration, 3),
            "width": width,
            "height": height,
            "fps": round(fps, 3),
            "frame_count": frame_count,
        },
    }

    return {
        "video_id": safe_filename,
        "filename": original_filename,
        "duration": round(duration, 3),
        "width": width,
        "height": height,
        "fps": round(fps, 3),
        "frame_count": frame_count,
        "status": "VALID",
        "job_id": job_id,
    }


@router.get("/analysis/{job_id}", response_model=AnalysisJob)
async def get_analysis_status(job_id: str):
    job = job_store.get(job_id)
    if job is None:
        _error(404, "JOB_NOT_FOUND", "Missing job")
    return {
        "job_id": job["job_id"],
        "video_id": job["video_id"],
        "status": job["status"],
        "progress": job["progress"],
        "stage": job["stage"],
    }
