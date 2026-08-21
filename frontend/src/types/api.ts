export interface VideoUploadResponse {
  video_id: string;
  filename: string;
  duration: number;
  width: number;
  height: number;
  fps: number;
  frame_count: number;
  status: string;
  job_id: string;
}

export interface AnalysisJob {
  job_id: string;
  video_id: string;
  status: AnalysisStatus;
  progress: number;
  stage: string;
}

export type AnalysisStatus =
  | "UPLOADED"
  | "VALIDATING_VIDEO"
  | "READING_VIDEO"
  | "PREPARING"
  | "COMPLETED"
  | "FAILED";

export interface APIError {
  error: {
    code: string;
    message: string;
  };
}

export interface VideoMetadata {
  video_id: string;
  original_filename: string;
  stored_filename: string;
  file_size: number;
  format: string;
  upload_time: string;
  duration: number;
  width: number;
  height: number;
  fps: number;
  frame_count: number;
  status: string;
}

export type DetectionStatus = "QUEUED" | "PROCESSING" | "COMPLETED" | "FAILED";

export interface DetectionTimelinePoint {
  frame_index: number;
  timestamp: number;
  person_count: number;
  average_confidence: number | null;
}

export interface CrowdTimelinePoint {
  frame_index: number; timestamp: number; signal_source: "OBSERVED" | "DEMO_SIMULATION";
  movement_available: boolean; venue_context_available: boolean;
  relative_density: number; density_label: string; movement_speed: number;
  movement_instability: number; flow_conflict: number; convergence: number;
  bottleneck_pressure: number; risk_score: number; risk_level: string;
  dominant_direction_deg: number;
  risk_slope: number; risk_trend: string; critical_zone: string; critical_zone_reasons: string[];
  zones: Array<{ zone_id: string; count: number; relative_density: number; risk_score: number; reasons: string[] }>;
  top_contributors: string[];
}

export interface InterventionOption {
  option_id: string; title: string; current_risk: number; projected_risk: number;
  risk_reduction: number; risk_reduction_percent: number; feasible: boolean;
  feasibility_reason: string; simulation_only: boolean; recommended: boolean;
}

export interface DetectionResult {
  video: {
    filename: string;
    duration: number;
    fps: number;
    width: number;
    height: number;
    frame_count: number;
  };
  analysis: {
    model: string;
    device: string;
    target_fps: number;
    effective_analysis_fps: number;
    frame_interval: number;
    person_class_id: number;
    confidence_threshold: number;
  };
  summary: {
    frames_analyzed: number;
    maximum_people_detected: number;
    minimum_people_detected: number;
    average_people_detected: number;
    average_confidence: number | null;
    peak_timestamp: number;
    processing_seconds: number;
    inference_seconds: number;
    effective_processing_fps: number;
    inference_device: string;
    person_detection_message: string;
    annotated_video_available: boolean;
    warnings: string[];
    crowd_intelligence: { method: string; signal_source: string; peak_risk: CrowdTimelinePoint; latest_state: CrowdTimelinePoint; calibrated_people_per_sqm: boolean; risk_formula: string; prototype_thresholds: boolean };
    interventions: InterventionOption[];
  };
  timeline: DetectionTimelinePoint[];
  crowd_timeline: CrowdTimelinePoint[];
  artifacts: {
    detections_json: string;
    frame_summary_csv: string;
    summary_json: string;
    annotated_video: string | null;
    annotated_frames: string[];
  };
}

export interface DetectionJob {
  job_id: string;
  video_id: string;
  status: DetectionStatus;
  progress: number;
  stage: string;
  result: DetectionResult | null;
  error?: { code: string; message: string };
}
