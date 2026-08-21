"""Run Phase 2 YOLOv8n baseline detection on local videos without modifying them."""

from argparse import ArgumentParser
from pathlib import Path
import json
import sys

from app.config import TARGET_ANALYSIS_FPS, VIDEO_SOURCE_DIR
from app.services.detection import VideoDetectionPipeline
from app.services.detection.video_detection import VideoProcessingError


def main() -> int:
    parser = ArgumentParser(description="CROWD-SHIELD Phase 2 person-detection baseline")
    parser.add_argument("videos", nargs="*", type=Path, help="Videos to process; defaults to videos/*")
    parser.add_argument("--target-fps", type=float, default=TARGET_ANALYSIS_FPS)
    args = parser.parse_args()

    videos = args.videos or sorted(
        path for path in VIDEO_SOURCE_DIR.iterdir() if path.suffix.lower() in {".mp4", ".webm", ".mov"}
    )
    pipeline = VideoDetectionPipeline(target_fps=args.target_fps)
    reports = []
    failures = []

    for video in videos:
        print(f"[START] {video}", flush=True)

        def progress(percent: float, stage: str) -> None:
            print(f"[{percent:6.2f}%] {video.name}: {stage}", flush=True)

        try:
            result = pipeline.process(video, progress_callback=progress)
            reports.append(result)
            print(f"[PASS] {video.name}: {json.dumps(result['summary'], separators=(',', ':'))}")
        except VideoProcessingError as exc:
            failures.append({"video": str(video), "error": str(exc)})
            print(f"[FAIL] {video.name}: {exc}", file=sys.stderr, flush=True)

    print(json.dumps({"processed": reports, "failures": failures}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
