from pathlib import Path
import os

# Base Paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
configured_upload_dir = Path(os.getenv("UPLOAD_DIRECTORY", "uploads"))
UPLOAD_DIR = configured_upload_dir if configured_upload_dir.is_absolute() else BASE_DIR / configured_upload_dir
PROCESSED_DIR = BASE_DIR / "processed"
STATIC_DIR = BASE_DIR / "static"
VENUE_CONFIG_PATH = BASE_DIR / "venue_config.json"

for d in [UPLOAD_DIR, PROCESSED_DIR, STATIC_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Phase 2 raw person-observation outputs. This is intentionally separate from
# the pre-existing later-phase pipeline under backend/processed.
configured_video_source = Path(os.getenv("VIDEO_SOURCE_DIRECTORY", "videos"))
VIDEO_SOURCE_DIR = (
    configured_video_source
    if configured_video_source.is_absolute()
    else PROJECT_ROOT / configured_video_source
)
configured_detection_output = Path(os.getenv("DETECTION_OUTPUT_DIRECTORY", "data/processed"))
DETECTION_PROCESSED_DIR = (
    configured_detection_output
    if configured_detection_output.is_absolute()
    else PROJECT_ROOT / configured_detection_output
)
for d in [
    DETECTION_PROCESSED_DIR / "annotated",
    DETECTION_PROCESSED_DIR / "results",
    DETECTION_PROCESSED_DIR / "frames",
    DETECTION_PROCESSED_DIR / "summaries",
]:
    d.mkdir(parents=True, exist_ok=True)

# Processing Configuration
YOLO_MODEL_NAME = "yolov8n.pt"
CONFIDENCE_THRESHOLD = 0.30
IOU_THRESHOLD = 0.45
DEFAULT_SAMPLE_RATE_FPS = 2.0  # Sample 2 frames per second for high responsiveness
TARGET_ANALYSIS_FPS = float(os.getenv("TARGET_ANALYSIS_FPS", "3"))
DETECTION_CONFIDENCE_THRESHOLD = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.15"))
DETECTION_IOU_THRESHOLD = float(os.getenv("YOLO_IOU_THRESHOLD", "0.45"))
DETECTION_IMAGE_SIZE = int(os.getenv("YOLO_IMAGE_SIZE", "1024"))
configured_model_path = Path(os.getenv("YOLO_MODEL_PATH", "data/training/cc_mach_yolov8n_person/weights/best.pt"))
DETECTION_MODEL_PATH = configured_model_path if configured_model_path.is_absolute() else PROJECT_ROOT / configured_model_path
if not DETECTION_MODEL_PATH.is_file():
    DETECTION_MODEL_PATH = PROJECT_ROOT / "yolov8n.pt"
ANNOTATED_FRAME_INTERVAL = int(os.getenv("ANNOTATED_FRAME_INTERVAL", "25"))
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "1024"))
ALLOWED_EXTENSIONS = {
    f".{item.strip().lower().lstrip('.')}"
    for item in os.getenv("ALLOWED_VIDEO_FORMATS", "mp4,webm,mov,jpg,jpeg,png,webp,bmp").split(",")
    if item.strip()
}

# Risk Calculation Weights
WEIGHT_DENSITY = 0.25
WEIGHT_CAPACITY = 0.20
WEIGHT_TURBULENCE = 0.30
WEIGHT_BOTTLENECK = 0.25

# Calibrated Risk Interpretation
RISK_THRESHOLDS = {
    "SAFE": (0, 30),
    "WATCH": (31, 55),
    "HIGH": (56, 75),
    "CRITICAL": (76, 100)
}
