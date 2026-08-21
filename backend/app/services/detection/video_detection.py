"""Incremental Phase 2 video sampling, person detection, and artifact export."""

from collections.abc import Callable
from pathlib import Path
from time import perf_counter
from typing import Any
import csv
import json
import os
import re

import cv2
import numpy as np

from app.config import (
    ANNOTATED_FRAME_INTERVAL,
    DETECTION_PROCESSED_DIR,
    TARGET_ANALYSIS_FPS,
)
from app.services.detection.person_detector import PersonDetector
from app.services.analytics.fast_mvp import FastCrowdMVP, simulate_interventions
from app.services.perception.optical_flow import OpticalFlowAnalyzer


class VideoProcessingError(RuntimeError):
    """A safe, user-facing Phase 2 processing failure."""


def sampling_interval(source_fps: float, target_fps: float) -> int:
    if source_fps <= 0 or target_fps <= 0:
        raise ValueError("Source and target FPS must be positive.")
    return max(1, round(source_fps / min(source_fps, target_fps)))


def confidence_statistics(detections: list[dict[str, Any]]) -> dict[str, float | None]:
    values = [float(item["confidence"]) for item in detections]
    if not values:
        return {"average_confidence": None, "min_confidence": None, "max_confidence": None}
    return {
        "average_confidence": round(float(np.mean(values)), 6),
        "min_confidence": round(min(values), 6),
        "max_confidence": round(max(values), 6),
    }


def annotate_frame(frame: np.ndarray, detections: list[dict[str, Any]], crowd_state: dict[str, Any] | None = None) -> np.ndarray:
    annotated = frame.copy()
    for detection in detections:
        x1, y1, x2, y2 = (int(round(value)) for value in detection["bbox"])
        cx, cy = (int(round(value)) for value in detection["centroid"])
        confidence = float(detection["confidence"])
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (56, 189, 248), 2)
        cv2.circle(annotated, (cx, cy), 4, (16, 185, 129), -1)
        label = f"person {confidence:.2f}"
        cv2.putText(
            annotated,
            label,
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (56, 189, 248),
            2,
            cv2.LINE_AA,
        )
    if crowd_state:
        text = f"EST RISK {crowd_state['risk_score']:.0f}/100 {crowd_state['risk_level']} | {crowd_state['critical_zone']}"
        cv2.rectangle(annotated, (12, 12), (min(760, 18 + len(text) * 13), 54), (5, 9, 20), -1)
        cv2.putText(annotated, text, (24, 42), cv2.FONT_HERSHEY_SIMPLEX, .75, (255, 255, 255), 2, cv2.LINE_AA)
    return annotated


class VideoDetectionPipeline:
    """Processes sampled frames without loading the full video into memory."""

    def __init__(
        self,
        detector: PersonDetector | Any | None = None,
        output_root: Path | str = DETECTION_PROCESSED_DIR,
        target_fps: float = TARGET_ANALYSIS_FPS,
        annotated_frame_interval: int = ANNOTATED_FRAME_INTERVAL,
        demo_mode: bool = False,
    ):
        self.detector = detector or PersonDetector()
        self.output_root = Path(output_root).resolve()
        self.target_fps = target_fps
        self.annotated_frame_interval = max(1, annotated_frame_interval)
        self.demo_mode = demo_mode

    @staticmethod
    def inspect_video(video_path: Path | str) -> dict[str, Any]:
        path = Path(video_path).resolve()
        if not path.is_file():
            raise VideoProcessingError(f"File is missing: {path.name}")
        ext = path.suffix.lower()
        if ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp"}:
            image = cv2.imread(str(path))
            if image is None or image.shape[0] <= 0 or image.shape[1] <= 0:
                raise VideoProcessingError(f"Image could not be opened: {path.name}")
            height, width = image.shape[:2]
            return {
                "filename": path.name,
                "extension": ext,
                "file_size_bytes": path.stat().st_size,
                "duration": 1.0,
                "fps": 1.0,
                "width": width,
                "height": height,
                "frame_count": 1,
                "is_image": True,
            }

        capture = cv2.VideoCapture(str(path))
        try:
            if not capture.isOpened():
                raise VideoProcessingError(f"Video could not be opened: {path.name}")
            fps = float(capture.get(cv2.CAP_PROP_FPS))
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            success, _ = capture.read()
            if not success or fps <= 0 or frame_count <= 0 or width <= 0 or height <= 0:
                raise VideoProcessingError(f"Video is corrupted or has invalid metadata: {path.name}")
            return {
                "filename": path.name,
                "extension": ext,
                "file_size_bytes": path.stat().st_size,
                "duration": round(frame_count / fps, 6),
                "fps": round(fps, 6),
                "width": width,
                "height": height,
                "frame_count": frame_count,
                "is_image": False,
            }
        finally:
            capture.release()

    def process(
        self,
        video_path: Path | str,
        progress_callback: Callable[[float, str], None] | None = None,
    ) -> dict[str, Any]:
        source = Path(video_path).resolve()
        metadata = self.inspect_video(source)
        interval = sampling_interval(metadata["fps"], self.target_fps) if not metadata.get("is_image") else 1
        effective_fps = metadata["fps"] / interval
        safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", source.stem).strip("._") or "media"

        directories = {
            name: self.output_root / name
            for name in ("annotated", "results", "frames", "summaries")
        }
        for directory in directories.values():
            directory.mkdir(parents=True, exist_ok=True)

        json_path = directories["results"] / f"{safe_stem}_detections.json"
        csv_path = directories["results"] / f"{safe_stem}_frame_summary.csv"
        summary_path = directories["summaries"] / f"{safe_stem}_summary.json"
        annotated_path = directories["annotated"] / f"{safe_stem}_annotated.mp4"
        json_temp = json_path.with_suffix(".json.tmp")
        csv_temp = csv_path.with_suffix(".csv.tmp")
        video_temp = annotated_path.with_name(f"{annotated_path.stem}.part.mp4")

        is_image = metadata.get("is_image", False)
        if is_image:
            writer = None
            video_encoding = False
        else:
            capture = cv2.VideoCapture(str(source))
            writer = cv2.VideoWriter(
                str(video_temp),
                cv2.VideoWriter_fourcc(*"mp4v"),
                effective_fps,
                (metadata["width"], metadata["height"]),
            )
            video_encoding = writer.isOpened()
        warnings: list[str] = []
        if not is_image and not video_encoding:
            writer.release()
            writer = None
            warnings.append("Annotated video encoding failed; annotated frame fallback was used.")

        counts: list[int] = []
        confidence_values: list[float] = []
        timeline: list[dict[str, Any]] = []
        saved_frames: list[str] = []
        analyzed_frames = 0
        inference_ms_total = 0.0
        frame_index = 0
        first_json_frame = True
        completed = False
        processing_started = perf_counter()
        flow_analyzer = OpticalFlowAnalyzer()
        crowd_analyzer = FastCrowdMVP(demo_mode=self.demo_mode)
        crowd_timeline: list[dict[str, Any]] = []
        full_crowd_states: list[dict[str, Any]] = []

        analysis_config = {
            "model": getattr(self.detector, "model_name", "YOLOv8n"),
            "device": getattr(self.detector, "device", "cpu"),
            "target_fps": self.target_fps,
            "effective_analysis_fps": round(effective_fps, 6),
            "frame_interval": interval,
            "person_class_id": 0,
            "confidence_threshold": getattr(self.detector, "confidence", None),
            "mode": "DEMO_SIMULATION" if self.demo_mode else "OBSERVED",
        }

        try:
            with json_temp.open("w", encoding="utf-8") as json_file, csv_temp.open(
                "w", newline="", encoding="utf-8"
            ) as csv_file:
                json_file.write(json.dumps({"video": metadata, "analysis": analysis_config})[:-1])
                json_file.write(',"frames":[')
                csv_writer = csv.DictWriter(
                    csv_file,
                    fieldnames=[
                        "video",
                        "frame_index",
                        "timestamp",
                        "person_count",
                        "average_confidence",
                        "min_confidence",
                        "max_confidence",
                    ],
                )
                csv_writer.writeheader()

                is_image = metadata.get("is_image", False)
                if is_image:
                    image_frame = cv2.imread(str(source))
                    single_frames = [image_frame] if image_frame is not None else []
                else:
                    single_frames = []

                while True:
                    if is_image:
                        if frame_index >= len(single_frames):
                            break
                        frame = single_frames[frame_index]
                    else:
                        if not capture.isOpened():
                            break
                        success, frame = capture.read()
                        if not success:
                            break
                    if frame_index % interval != 0:
                        frame_index += 1
                        continue

                    try:
                        detections, inference_ms = self.detector.detect(frame)
                    except MemoryError as exc:
                        raise VideoProcessingError("Person detection stopped because memory was exhausted.") from exc
                    except Exception as exc:
                        raise VideoProcessingError(f"YOLO inference failed at frame {frame_index}.") from exc

                    stats = confidence_statistics(detections)
                    timestamp = frame_index / metadata["fps"]
                    flow = flow_analyzer.compute_flow(frame, detections)
                    crowd_state = crowd_analyzer.analyze(
                        detections, flow, timestamp, metadata["width"], metadata["height"],
                        frame_index / max(1, metadata["frame_count"] - 1),
                    )
                    frame_result = {
                        "frame_index": frame_index,
                        "timestamp": round(timestamp, 6),
                        "person_count": len(detections),
                        **stats,
                        "detections": detections,
                        "crowd_state": crowd_state,
                    }
                    if not first_json_frame:
                        json_file.write(",")
                    json.dump(frame_result, json_file, separators=(",", ":"))
                    first_json_frame = False
                    csv_writer.writerow(
                        {
                            "video": source.name,
                            "frame_index": frame_index,
                            "timestamp": round(timestamp, 6),
                            "person_count": len(detections),
                            **stats,
                        }
                    )

                    annotated = annotate_frame(frame, detections, crowd_state)
                    if writer is not None:
                        writer.write(annotated)
                    if writer is None or analyzed_frames % self.annotated_frame_interval == 0:
                        frame_name = f"{safe_stem}_frame_{frame_index:08d}.jpg"
                        frame_path = directories["frames"] / frame_name
                        if cv2.imwrite(str(frame_path), annotated):
                            saved_frames.append(frame_name)

                    counts.append(len(detections))
                    confidence_values.extend(float(item["confidence"]) for item in detections)
                    timeline.append(
                        {
                            "frame_index": frame_index,
                            "timestamp": round(timestamp, 3),
                            "person_count": len(detections),
                            "average_confidence": stats["average_confidence"],
                        }
                    )
                    crowd_timeline.append({"frame_index": frame_index, "timestamp": round(timestamp, 3), **{key: crowd_state[key] for key in ("signal_source", "relative_density", "density_label", "movement_speed", "dominant_direction_deg", "movement_instability", "flow_conflict", "convergence", "bottleneck_pressure", "risk_score", "risk_level", "risk_slope", "risk_trend", "critical_zone", "top_contributors")}})
                    full_crowd_states.append(crowd_state)
                    analyzed_frames += 1
                    inference_ms_total += inference_ms
                    if progress_callback and (analyzed_frames == 1 or analyzed_frames % 10 == 0):
                        progress_callback(
                            min(99.0, frame_index / max(1, metadata["frame_count"]) * 100),
                            f"Detecting people at {timestamp:.1f}s",
                        )
                    del annotated, frame
                    frame_index += 1

                if analyzed_frames == 0:
                    raise VideoProcessingError("No valid frames were available for analysis.")

                processing_seconds = perf_counter() - processing_started
                peak_index = int(np.argmax(counts))
                summary = {
                    "video": source.name,
                    "frames_analyzed": analyzed_frames,
                    "maximum_people_detected": max(counts),
                    "minimum_people_detected": min(counts),
                    "average_people_detected": round(float(np.mean(counts)), 6),
                    "average_confidence": round(float(np.mean(confidence_values)), 6)
                    if confidence_values
                    else None,
                    "peak_timestamp": timeline[peak_index]["timestamp"],
                    "processing_seconds": round(processing_seconds, 6),
                    "inference_seconds": round(inference_ms_total / 1000, 6),
                    "effective_processing_fps": round(analyzed_frames / processing_seconds, 6),
                    "inference_device": analysis_config["device"],
                    "person_detection_message": "Person detections generated."
                    if max(counts) > 0
                    else "No person detections were obtained in the analyzed frames.",
                    "annotated_video_available": video_encoding,
                    "warnings": warnings,
                }
                peak_state = max(crowd_timeline, key=lambda item: item["risk_score"])
                summary["crowd_intelligence"] = {
                    "method": "relative image-space prototype",
                    "signal_source": "DEMO_SIMULATION" if self.demo_mode else "OBSERVED",
                    "peak_risk": peak_state,
                    "latest_state": crowd_timeline[-1],
                    "calibrated_people_per_sqm": False,
                    "risk_formula": "0.25 density + 0.15 density growth + 0.15 movement instability + 0.15 flow conflict + 0.15 convergence + 0.15 bottleneck pressure",
                    "prototype_thresholds": True,
                }
                full_peak_state = full_crowd_states[crowd_timeline.index(peak_state)]
                summary["interventions"] = simulate_interventions(full_peak_state)
                json_file.write('],"summary":')
                json.dump(summary, json_file, separators=(",", ":"))
                json_file.write("}")

            os.replace(json_temp, json_path)
            os.replace(csv_temp, csv_path)
            summary_payload = {
                "video": metadata,
                "analysis": analysis_config,
                "summary": summary,
                "timeline": timeline,
                "crowd_timeline": crowd_timeline,
                "artifacts": {
                    "detections_json": json_path.name,
                    "frame_summary_csv": csv_path.name,
                    "summary_json": summary_path.name,
                    "annotated_video": annotated_path.name if video_encoding else None,
                    "annotated_frames": saved_frames,
                },
            }
            summary_path.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")
            completed = True
            if progress_callback:
                progress_callback(100.0, "Person detection complete")
            return summary_payload
        except VideoProcessingError:
            raise
        except Exception as exc:
            raise VideoProcessingError("Video processing was interrupted.") from exc
        finally:
            if 'capture' in locals() and capture is not None:
                capture.release()
            if writer is not None:
                writer.release()
            if completed and video_encoding and video_temp.exists():
                os.replace(video_temp, annotated_path)
            else:
                video_temp.unlink(missing_ok=True)
            json_temp.unlink(missing_ok=True)
            csv_temp.unlink(missing_ok=True)
