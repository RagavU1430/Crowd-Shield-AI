import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi import APIRouter as FastAPIAPIRouter

from app.config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_SIZE_MB
from app.models.schemas import (
    AnalysisMode, AnalysisSessionResponse, OperatorDecision
)
from app.services.video.processor import VideoAnalysisPipeline
from app.services.video.synthetic_generator import generate_benchmark_crowd_video

# Phase 1 API router (new endpoints per Phase 1 spec)
phase1_router = APIRouter(prefix="/api")

# Existing v1 router (AI pipeline, kept for backward compatibility)
api_router = APIRouter(prefix="/api/v1")
pipeline = VideoAnalysisPipeline()


# ──────────────────────────────────────────────────────────────────────
# Phase 1: Video Upload API
# ──────────────────────────────────────────────────────────────────────

@phase1_router.post("/videos/upload")
async def phase1_upload_video(
    file: UploadFile = File(...),
):
    """
    Phase 1 Video Upload endpoint.
    Accepts MP4 / WebM / MOV files, validates, stores safely, extracts metadata,
    and creates an analysis job.
    """
    # 1. Extension validation
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {ext}. Allowed: {ALLOWED_EXTENSIONS}",
        )

    # 2. MIME type validation where practical
    allowed_mime = ["video/mp4", "video/webm", "video/quicktime"]
    if file.content_type not in allowed_mime and file.content_type is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported MIME type: {file.content_type}. Allowed: {allowed_mime}",
        )

    # 3. File content/readability validation
    try:
        contents = await file.read()
        file.file.seek(0)  # reset stream after read
    except Exception:
        raise HTTPException(
            status_code=400, detail="Could not read uploaded file."
        )

    # 4. Configurable maximum file size
    max_size = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(contents) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE_MB}MB",
        )

    # 5. Generate safe unique server-side filename (never trust user filename)
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    stored_path = UPLOAD_DIR / safe_filename

    # 6. Save file (do not trust user-provided paths)
    with open(stored_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)  # file.file may be exhausted; use contents

    # Re-open from saved path for metadata extraction
    import cv2

    cap = cv2.VideoCapture(str(stored_path))
    if not cap.isOpened():
        # Clean up unreadable file
        os.remove(stored_path)
        raise HTTPException(
            status_code=400,
            detail="The uploaded file could not be read as a valid video.",
        )

    # Extract metadata
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    duration_sec = total_frames / fps if fps > 0 else 0.0

    cap.release()

    # 7. Create analysis job
    video_id = safe_filename
    job_id = f"job_{uuid.uuid4().hex[:8]}"

    # Store metadata and create job entry
    job_entry = {
        "video_id": video_id,
        "original_filename": file.filename,
        "stored_filename": safe_filename,
        "file_size": len(contents),
        "format": ext,
        "upload_time": os.popen("date /t & time /t").read() if hasattr(os, "popen") else "",
        "duration": round(duration_sec, 1),
        "width": width,
        "height": height,
        "fps": round(fps, 1),
        "frame_count": total_frames,
        "status": "VALID",
    }
    phase1_job_store[job_id] = job_entry

    # Return upload response
    return {
        "video_id": video_id,
        "filename": file.filename,
        "duration": round(duration_sec, 1),
        "width": width,
        "height": height,
        "fps": round(fps, 1),
        "frame_count": total_frames,
        "status": "VALID",
        "job_id": job_id,
    }


# ──────────────────────────────────────────────────────────────────────
# Phase 1: Analysis Job Status API
# ──────────────────────────────────────────────────────────────────────

# In-memory job store (replace with DB in production)
phase1_job_store: Dict[str, Dict[str, Any]] = {}


@phase1_router.get("/analysis/{job_id}")
async def phase1_get_analysis_status(job_id: str):
    """
    Phase 1 Analysis job status endpoint.
    Polls the current status, progress, and stage of an analysis job.
    """
    job = phase1_job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Missing job")

    # Map internal status to Phase 1 statuses
    status_map = {
        "UPLOADED": "UPLOADED",
        "VALIDATING": "VALIDATING_VIDEO",
        "READY": "READY",
        "PROCESSING": "PROCESSING",
        "COMPLETED": "COMPLETED",
        "FAILED": "FAILED",
    }

    return {
        "job_id": job_id,
        "video_id": job.get("video_id", ""),
        "status": status_map.get(job.get("status", "UPLOADED"), "UPLOADED"),
        "progress": job.get("progress", 0),
        "stage": job.get("stage", "Pending"),
    }


# ──────────────────────────────────────────────────────────────────────
# Existing v1 endpoints (preserved for backward compatibility)
# ──────────────────────────────────────────────────────────────────────

@api_router.post("/video/upload", response_model=Dict[str, Any] if False else None)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    analysis_mode: AnalysisMode = Form(AnalysisMode.STANDARD)
):
    """
    Primary MVP Video Upload endpoint (existing).
    Accepts MP4 / WebM video files and starts asynchronous perception & decision analysis.
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}. Allowed: {ALLOWED_EXTENSIONS}")

    session_id = f"CS_SESSION_{uuid.uuid4().hex[:8].upper()}"
    original_filename = Path(file.filename or "").name
    saved_path = UPLOAD_DIR / f"{session_id}_{uuid.uuid4().hex}{ext}"

    total_bytes = 0
    maximum_bytes = MAX_UPLOAD_SIZE_MB * 1024 * 1024
    try:
        with open(saved_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                total_bytes += len(chunk)
                if total_bytes > maximum_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE_MB}MB",
                    )
                buffer.write(chunk)
    except Exception:
        saved_path.unlink(missing_ok=True)
        raise

    # Initial session placeholder
    pipeline.active_sessions[session_id] = AnalysisSessionResponse(
        session_id=session_id,
        status="QUEUED",
        progress_pct=2.0,
        current_stage="File uploaded. Queuing video analysis pipeline...",
        timeline=[]
    )

    # Launch background processing
    background_tasks.add_task(
        pipeline.process_video_file,
        saved_path,
        session_id,
        analysis_mode
    )

    return {
        "session_id": session_id,
        "filename": original_filename,
        "analysis_mode": analysis_mode,
        "status": "QUEUED",
        "message": "Video uploaded successfully. Analysis running in background."
    }

@api_router.get("/analysis/{session_id}/status", response_model=AnalysisSessionResponse)
async def get_analysis_status(session_id: str):
    """
    Polls current processing status, progress percentage, and complete telemetry timeline.
    """
    if session_id not in pipeline.active_sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    return pipeline.active_sessions[session_id]

@api_router.post("/scenario/benchmark", response_model=AnalysisSessionResponse)
async def run_benchmark_scenario(
    background_tasks: BackgroundTasks,
    analysis_mode: AnalysisMode = AnalysisMode.SIMULATED_SCENARIO
):
    """
    Generates and analyzes the standard CROWD-SHIELD benchmark test scenario immediately.
    """
    session_id = f"CS_BENCH_{uuid.uuid4().hex[:6].upper()}"
    benchmark_video = UPLOAD_DIR / f"{session_id}_benchmark_crowd.mp4"
    
    # Generate benchmark clip
    generate_benchmark_crowd_video(benchmark_video, duration_sec=12, fps=15)
    
    # Process immediately
    result = pipeline.process_video_file(
        benchmark_video,
        session_id,
        analysis_mode
    )
    return result

@api_router.post("/decision/submit")
async def submit_operator_decision(decision: OperatorDecision):
    """
    Captures Human-in-the-Loop operator approval or rejection for the recommended intervention.
    """
    if decision.session_id not in pipeline.active_sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    session = pipeline.active_sessions[decision.session_id]
    
    # Verify option
    chosen_opt = next((o for o in session.interventions if o.option_id == decision.option_id), None)
    
    return {
        "status": "RECORDED",
        "session_id": decision.session_id,
        "option_id": decision.option_id,
        "decision": decision.decision,
        "operator_id": decision.operator_id,
        "applied_projected_risk": chosen_opt.projected_risk if chosen_opt else 29,
        "message": f"Operator {decision.operator_id} marked action {decision.option_id} as {decision.decision}."
    }

@api_router.get("/analysis/{session_id}/export")
async def export_analysis_report(session_id: str, format: str = "json"):
    """
    Exports full timeline telemetry as downloadable JSON or CSV.
    """
    if session_id not in pipeline.active_sessions:
        raise HTTPException(status_code=404, detail="Session not found.")

    session = pipeline.active_sessions[session_id]
    
    if format.lower() == "csv":
        lines = ["timestamp_sec,time,people_count,density_sqm,mean_speed,turbulence,risk_score,risk_level,trajectory_trend,critical_zone"]
        for fr in session.timeline:
            lines.append(f"{fr.timestamp_sec},{fr.formatted_time},{fr.people_count},{fr.mean_density_sqm},{fr.mean_speed},{fr.turbulence_index},{fr.global_risk_score},{fr.risk_level},{fr.trajectory_trend},{fr.critical_zone_id or 'ZONE_B'}")
        csv_content = "\n".join(lines)
        return Response(content=csv_content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={session_id}_report.csv"})

    return session
