"""Central configuration for SmartPark AI."""
from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "local-development-key-change-me")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 500 * 1024 * 1024))
    UPLOAD_FOLDER = BASE_DIR / "uploads"
    OUTPUT_FOLDER = BASE_DIR / "outputs"
    DATABASE_PATH = BASE_DIR / "database" / "parking.db"
    MODEL_PATH = os.getenv("MODEL_PATH", str(BASE_DIR / "models" / "yolo11n.pt"))
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.35"))
    IOU_THRESHOLD = float(os.getenv("IOU_THRESHOLD", "0.45"))
    OCCUPANCY_THRESHOLD = float(os.getenv("OCCUPANCY_THRESHOLD", "0.30"))
    VIDEO_FRAME_SKIP = max(1, int(os.getenv("VIDEO_FRAME_SKIP", "1")))
    VIDEO_MAX_WIDTH = int(os.getenv("VIDEO_MAX_WIDTH", "1280"))
    VEHICLE_CLASSES = tuple(
        item.strip().lower()
        for item in os.getenv("VEHICLE_CLASSES", "car,motorcycle,bus,truck").split(",")
        if item.strip()
    )
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "avi", "mov", "mkv"}

    @classmethod
    def ensure_directories(cls) -> None:
        for directory in (
            cls.UPLOAD_FOLDER / "images",
            cls.UPLOAD_FOLDER / "videos",
            cls.OUTPUT_FOLDER / "images",
            cls.OUTPUT_FOLDER / "videos",
            cls.DATABASE_PATH.parent,
            BASE_DIR / "parking_configs",
            BASE_DIR / "models",
        ):
            directory.mkdir(parents=True, exist_ok=True)
