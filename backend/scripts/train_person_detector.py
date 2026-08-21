"""Train the Phase 2 person detector while reserving test media for evaluation."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = PROJECT_ROOT / "CC_Mach_1.v1i.yolov8" / "data.yaml"
DEFAULT_MODEL = PROJECT_ROOT / "yolov8n.pt"
DEFAULT_PROJECT = PROJECT_ROOT / "data" / "training"
os.environ.setdefault("YOLO_CONFIG_DIR", str(PROJECT_ROOT / "backend" / ".runtime"))
os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / "backend" / ".runtime" / "matplotlib"))

from ultralytics import YOLO  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--patience", type=int, default=10)
    parser.add_argument("--batch", type=int, default=4)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--name", default="cc_mach_yolov8n_person")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model = YOLO(str(DEFAULT_MODEL))
    model.train(
        data=str(DEFAULT_DATASET),
        epochs=args.epochs,
        patience=args.patience,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        workers=args.workers,
        project=str(DEFAULT_PROJECT),
        name=args.name,
        exist_ok=True,
        pretrained=True,
        plots=True,
        save=True,
        val=True,
        verbose=True,
    )


if __name__ == "__main__":
    main()
