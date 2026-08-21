from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class AnalysisMode(str, Enum):
    STANDARD = "STANDARD"
    RETROSPECTIVE_INCIDENT = "RETROSPECTIVE_INCIDENT"
    SIMULATED_SCENARIO = "SIMULATED_SCENARIO"

class RiskLevel(str, Enum):
    SAFE = "SAFE"
    WATCH = "WATCH"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class TrajectoryTrend(str, Enum):
    DECREASING = "DECREASING"
    STABLE = "STABLE"
    INCREASING = "INCREASING"
    RAPIDLY_INCREASING = "RAPIDLY_INCREASING"

class AnonymousDetection(BaseModel):
    id: int
    bbox: List[float] = Field(description="[ymin, xmin, ymax, xmax] normalized 0-1")
    centroid: List[float] = Field(description="[x, y] normalized 0-1")
    confidence: float
    velocity: Optional[List[float]] = Field(default=[0.0, 0.0], description="[vx, vy] flow vector")
    zone_id: Optional[str] = None

class ZoneMetrics(BaseModel):
    zone_id: str
    name: str
    count: int
    capacity: int
    occupancy_pct: float
    density_sqm: float
    mean_speed: float
    turbulence: float
    bottleneck_pressure: float
    risk_score: int
    risk_level: RiskLevel

class FrameAnalysisResult(BaseModel):
    timestamp_sec: float
    formatted_time: str
    frame_index: int
    people_count: int
    mean_density_sqm: float
    mean_speed: float
    turbulence_index: float
    global_risk_score: int
    risk_level: RiskLevel
    trajectory_trend: TrajectoryTrend
    critical_zone_id: Optional[str] = None
    detections: List[AnonymousDetection] = []
    zone_metrics: List[ZoneMetrics] = []
    primary_factors: List[str] = []

class InterventionOption(BaseModel):
    option_id: str
    title: str
    action_type: str
    projected_risk: int
    risk_delta: int
    feasibility: bool
    feasibility_status: str
    reason: str
    is_recommended: bool = False
    details: Dict[str, Any] = {}

class AnalysisSummary(BaseModel):
    session_id: str
    filename: str
    analysis_mode: AnalysisMode
    video_duration_sec: float
    total_frames_processed: int
    peak_people_count: int
    peak_density_sqm: float
    peak_risk_score: int
    highest_risk_timestamp: str
    critical_zone: Optional[str] = None
    overall_trend: TrajectoryTrend
    top_contributing_factors: List[str]
    disclaimer: str
    venue_context_available: bool

class AnalysisSessionResponse(BaseModel):
    session_id: str
    status: str
    progress_pct: float
    current_stage: str
    summary: Optional[AnalysisSummary] = None
    timeline: List[FrameAnalysisResult] = []
    interventions: List[InterventionOption] = []
    recommended_option: Optional[InterventionOption] = None

class OperatorDecision(BaseModel):
    session_id: str
    option_id: str
    decision: str  # APPROVE / REJECT / OVERRIDE
    operator_id: str = "COMMANDER_01"
    notes: Optional[str] = None


# Phase 1 API contracts
class VideoUploadResponse(BaseModel):
    video_id: str
    filename: str
    duration: float
    width: int
    height: int
    fps: float
    frame_count: int
    status: str
    job_id: str


class VideoMetadata(BaseModel):
    video_id: str
    original_filename: str
    stored_filename: str
    file_size: int
    format: str
    upload_time: str
    duration: float
    width: int
    height: int
    fps: float
    frame_count: int
    status: str


class AnalysisStatus(str, Enum):
    UPLOADED = "UPLOADED"
    QUEUED = "QUEUED"
    VALIDATING_VIDEO = "VALIDATING_VIDEO"
    READING_VIDEO = "READING_VIDEO"
    PREPARING = "PREPARING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalysisJob(BaseModel):
    job_id: str
    video_id: str
    status: AnalysisStatus
    progress: int
    stage: str


class APIError(BaseModel):
    error: Dict[str, str]
