import cv2
import numpy as np
import time
import os
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from app.config import (
    UPLOAD_DIR, PROCESSED_DIR, DEFAULT_SAMPLE_RATE_FPS
)
from app.models.schemas import (
    AnalysisMode, FrameAnalysisResult, AnonymousDetection,
    ZoneMetrics, AnalysisSummary, AnalysisSessionResponse, InterventionOption
)
from app.services.perception.yolo_detector import AnonymousPersonDetector
from app.services.perception.optical_flow import OpticalFlowAnalyzer
from app.services.simulation.venue_model import VenueModel
from app.services.analytics.crowd_state import CrowdStateEngine
from app.services.analytics.risk_engine import ContextualRiskEngine
from app.services.analytics.trajectory import RiskTrajectoryEngine
from app.services.simulation.intervention_sim import InterventionSimulator

class VideoAnalysisPipeline:
    """
    Core video processing pipeline for CROWD-SHIELD.
    Processes uploaded videos asynchronously, computes timeline telemetry,
    risk trajectories, and counterfactual interventions.
    """
    def __init__(self):
        self.venue_model = VenueModel()
        self.detector = AnonymousPersonDetector()
        self.flow_analyzer = OpticalFlowAnalyzer()
        self.crowd_state_engine = CrowdStateEngine(self.venue_model)
        self.risk_engine = ContextualRiskEngine()
        self.trajectory_engine = RiskTrajectoryEngine()
        self.simulator = InterventionSimulator(self.venue_model)
        self.active_sessions: Dict[str, AnalysisSessionResponse] = {}

    def process_video_file(
        self,
        video_path: Path,
        session_id: str,
        mode: AnalysisMode = AnalysisMode.STANDARD,
        progress_callback: Optional[Callable[[float, str], None]] = None
    ) -> AnalysisSessionResponse:
        """
        Executes full video pipeline on an uploaded file.
        """
        self.flow_analyzer.reset()
        self.trajectory_engine.reset()

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Unable to open video file: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration_sec = total_frames / fps if fps > 0 else 0.0

        # Determine frame sample interval (e.g. 2 fps)
        sample_interval = max(1, int(fps / DEFAULT_SAMPLE_RATE_FPS))

        timeline_results: List[FrameAnalysisResult] = []
        peak_people = 0
        peak_density = 0.0
        peak_risk = 0
        highest_risk_time = "00:00"
        critical_zone_overall = None
        top_factors_overall = []

        frame_count = 0
        processed_frame_idx = 0

        # Initialize session state
        session_resp = AnalysisSessionResponse(
            session_id=session_id,
            status="PROCESSING",
            progress_pct=5.0,
            current_stage="Extracting and sampling video frames...",
            timeline=[]
        )
        self.active_sessions[session_id] = session_resp

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % sample_interval == 0:
                t_sec = round(frame_count / fps, 2)
                mins = int(t_sec // 60)
                secs = int(t_sec % 60)
                formatted_time = f"{mins:02d}:{secs:02d}"

                progress = min(90.0, 10.0 + (frame_count / max(1, total_frames)) * 80.0)
                stage_msg = f"Analyzing crowd kinetics at {formatted_time}..."
                session_resp.progress_pct = round(progress, 1)
                session_resp.current_stage = stage_msg
                if progress_callback:
                    progress_callback(progress, stage_msg)

                # Resize frame for efficient low-latency inference
                inference_frame = cv2.resize(frame, (640, 480))

                # 1. Anonymous Person Detection
                raw_detections = self.detector.detect_anonymous_persons(inference_frame)
                people_count = len(raw_detections)

                # 2. Optical Flow & Velocity Vector Field
                flow_metrics = self.flow_analyzer.compute_flow(inference_frame)

                # 3. Crowd State Engine & Zone Aggregation
                zone_states = self.crowd_state_engine.compute_zone_states(
                    raw_detections, flow_metrics, frame_w=640, frame_h=480
                )

                # 4. Contextual Risk Engine
                global_risk, risk_level, crit_zone, factors = self.risk_engine.evaluate_global_risk(
                    zone_states, flow_metrics
                )

                # 5. Trajectory Engine
                trend, slope = self.trajectory_engine.update_and_evaluate(t_sec, global_risk)

                # Track peaks
                if people_count > peak_people:
                    peak_people = people_count
                
                mean_density = round(np.mean([z["density_sqm"] for z in zone_states]) if zone_states else people_count / 10.0, 2)
                if mean_density > peak_density:
                    peak_density = mean_density

                if global_risk > peak_risk:
                    peak_risk = global_risk
                    highest_risk_time = formatted_time
                    critical_zone_overall = crit_zone
                    top_factors_overall = factors

                # Convert to Pydantic models
                detection_models = [
                    AnonymousDetection(
                        id=d["id"],
                        bbox=d["bbox"],
                        centroid=d["centroid"],
                        confidence=d["confidence"],
                        velocity=d.get("velocity", [0.0, 0.0]),
                        zone_id=d.get("zone_id")
                    )
                    for d in raw_detections
                ]

                zone_models = [
                    ZoneMetrics(
                        zone_id=z["zone_id"],
                        name=z["name"],
                        count=z["count"],
                        capacity=z["capacity"],
                        occupancy_pct=z["occupancy_pct"],
                        density_sqm=z["density_sqm"],
                        mean_speed=z["mean_speed"],
                        turbulence=z["turbulence"],
                        bottleneck_pressure=z["bottleneck_pressure"],
                        risk_score=z.get("risk_score", 20),
                        risk_level=z.get("risk_level", "SAFE")
                    )
                    for z in zone_states
                ]

                frame_result = FrameAnalysisResult(
                    timestamp_sec=t_sec,
                    formatted_time=formatted_time,
                    frame_index=processed_frame_idx,
                    people_count=people_count,
                    mean_density_sqm=mean_density,
                    mean_speed=flow_metrics.get("mean_speed", 0.0),
                    turbulence_index=flow_metrics.get("turbulence_index", 0.0),
                    global_risk_score=global_risk,
                    risk_level=risk_level,
                    trajectory_trend=trend,
                    critical_zone_id=crit_zone,
                    detections=detection_models,
                    zone_metrics=zone_models,
                    primary_factors=factors
                )

                timeline_results.append(frame_result)
                processed_frame_idx += 1

            frame_count += 1

        cap.release()

        # Step 6: Intervention Simulation on peak / final state
        session_resp.current_stage = "Simulating candidate tactical interventions..."
        session_resp.progress_pct = 95.0

        last_zones = timeline_results[-1].zone_metrics if timeline_results else []
        zones_dicts = [z.dict() for z in last_zones]
        
        interventions = self.simulator.evaluate_interventions(
            current_risk=peak_risk,
            critical_zone_id=critical_zone_overall,
            zone_metrics_list=zones_dicts
        )

        recommended = next((opt for opt in interventions if opt.is_recommended), interventions[-1] if interventions else None)

        # Step 7: Formulate Summary & Disclaimers
        disclaimer = (
            "This analysis is a research/prototype assessment of observable crowd dynamics in recorded footage. "
            "It does not establish causality, predict what would have happened in real time, or demonstrate that an incident could have been prevented."
            if mode == AnalysisMode.RETROSPECTIVE_INCIDENT
            else "Decision-support prototype estimates only. Final operational authority remains strictly with authorized human personnel."
        )

        summary = AnalysisSummary(
            session_id=session_id,
            filename=video_path.name,
            analysis_mode=mode,
            video_duration_sec=round(duration_sec, 2),
            total_frames_processed=len(timeline_results),
            peak_people_count=peak_people,
            peak_density_sqm=peak_density,
            peak_risk_score=peak_risk,
            highest_risk_timestamp=highest_risk_time,
            critical_zone=critical_zone_overall or "ZONE_B",
            overall_trend=timeline_results[-1].trajectory_trend if timeline_results else "STABLE",
            top_contributing_factors=top_factors_overall if top_factors_overall else ["Normal Fluid Movement"],
            disclaimer=disclaimer,
            venue_context_available=self.venue_model.is_loaded
        )

        session_resp.status = "COMPLETED"
        session_resp.progress_pct = 100.0
        session_resp.current_stage = "Analysis complete. Decision support dashboard ready."
        session_resp.summary = summary
        session_resp.timeline = timeline_results
        session_resp.interventions = interventions
        session_resp.recommended_option = recommended

        self.active_sessions[session_id] = session_resp
        return session_resp
