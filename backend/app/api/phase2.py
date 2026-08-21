"""Phase 2 API for anonymous person-detection jobs."""

from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Body

from app.api.phase1 import Phase1APIError, job_store as upload_job_store
from app.config import UPLOAD_DIR
from app.services.detection import VideoDetectionPipeline
from app.services.detection.video_detection import VideoProcessingError


router = APIRouter(prefix="/api")
pipeline = VideoDetectionPipeline()
detection_store: dict[str, dict[str, Any]] = {}
store_lock = Lock()


def _artifact_urls(result: dict[str, Any]) -> dict[str, Any]:
    artifacts = result["artifacts"]
    return {
        "detections_json": f"/processed/results/{artifacts['detections_json']}",
        "frame_summary_csv": f"/processed/results/{artifacts['frame_summary_csv']}",
        "summary_json": f"/processed/summaries/{artifacts['summary_json']}",
        "annotated_video": (
            f"/processed/annotated/{artifacts['annotated_video']}"
            if artifacts["annotated_video"]
            else None
        ),
        "annotated_frames": [
            f"/processed/frames/{name}" for name in artifacts["annotated_frames"]
        ],
    }


def _run_detection(job_id: str, source_path: Path, demo_mode: bool = False) -> None:
    def progress(percent: float, stage: str) -> None:
        with store_lock:
            detection_store[job_id].update(
                {"status": "PROCESSING", "progress": round(percent, 2), "stage": stage}
            )

    try:
        active_pipeline = VideoDetectionPipeline(demo_mode=True) if demo_mode else pipeline
        result = active_pipeline.process(source_path, progress_callback=progress)
        result["artifacts"] = _artifact_urls(result)
        with store_lock:
            detection_store[job_id].update(
                {
                    "status": "COMPLETED",
                    "progress": 100,
                    "stage": "Person detection complete",
                    "result": result,
                }
            )
    except VideoProcessingError as exc:
        with store_lock:
            detection_store[job_id].update(
                {
                    "status": "FAILED",
                    "stage": str(exc),
                    "error": {"code": "DETECTION_FAILED", "message": str(exc)},
                }
            )
    except Exception:
        with store_lock:
            detection_store[job_id].update(
                {
                    "status": "FAILED",
                    "stage": "Person detection failed",
                    "error": {
                        "code": "DETECTION_FAILED",
                        "message": "Person detection could not be completed.",
                    },
                }
            )


@router.post("/analysis/{job_id}/detect", status_code=202)
def start_person_detection(job_id: str, background_tasks: BackgroundTasks, demo_mode: bool = False):
    upload_job = upload_job_store.get(job_id)
    if upload_job is None:
        raise Phase1APIError(404, "JOB_NOT_FOUND", "Missing job")
    source_path = (UPLOAD_DIR / upload_job["video_id"]).resolve()
    if source_path.parent != UPLOAD_DIR.resolve() or not source_path.is_file():
        raise Phase1APIError(404, "VIDEO_NOT_FOUND", "The uploaded video is missing.")

    with store_lock:
        current = detection_store.get(job_id)
        if current and current["status"] in ("QUEUED", "PROCESSING", "COMPLETED"):
            return current
        detection_store[job_id] = {
            "job_id": job_id,
            "video_id": upload_job["video_id"],
            "status": "QUEUED",
            "progress": 0,
            "stage": "Person detection queued",
            "result": None,
            "demo_mode": demo_mode,
        }

    background_tasks.add_task(_run_detection, job_id, source_path, demo_mode)
    return detection_store[job_id]


@router.get("/analysis/{job_id}/detections")
def get_person_detections(job_id: str):
    with store_lock:
        job = detection_store.get(job_id)
        if job is None:
            raise Phase1APIError(
                404,
                "DETECTION_NOT_STARTED",
                "Person detection has not been started for this job.",
            )
        return dict(job)


@router.post("/analysis/{job_id}/interventions/{option_id}/approve")
def approve_intervention(job_id: str, option_id: str):
    with store_lock:
        job = detection_store.get(job_id)
        if not job or job.get("status") != "COMPLETED" or not job.get("result"):
            raise Phase1APIError(409, "ANALYSIS_NOT_COMPLETE", "Complete analysis before approving an intervention.")
        options = job["result"]["summary"].get("interventions", [])
        option = next((item for item in options if item["option_id"] == option_id), None)
        if not option:
            raise Phase1APIError(404, "INTERVENTION_NOT_FOUND", "The intervention option does not exist.")
        if not option["feasible"]:
            raise Phase1APIError(409, "INTERVENTION_INFEASIBLE", option["feasibility_reason"])
        approval = {
            "status": "SIMULATED_INTERVENTION_APPLIED",
            "human_decision": "APPROVED",
            "option": option,
            "message": "Projected crowd stabilization. SIMULATION ONLY — no physical control action was sent.",
        }
        job["approval"] = approval
        return approval


@router.post("/analysis/{job_id}/interventions/reject")
def reject_intervention(job_id: str, reason: str = Body(default="Operator rejected recommendation", embed=True)):
    with store_lock:
        job = detection_store.get(job_id)
        if not job:
            raise Phase1APIError(404, "DETECTION_NOT_STARTED", "Analysis was not found.")
        job["approval"] = {"status": "REJECTED", "human_decision": "REJECTED", "reason": reason}
        return job["approval"]
