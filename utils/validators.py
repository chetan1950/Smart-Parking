"""Media validation before costly computer-vision processing."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError


def validate_image_file(path: Path) -> None:
    try:
        with Image.open(path) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("The uploaded image is corrupted or unreadable.") from exc


def validate_video_file(path: Path) -> None:
    try:
        import cv2
    except ImportError as exc:
        raise RuntimeError("OpenCV is not installed; video validation is unavailable.") from exc
    capture = cv2.VideoCapture(str(path))
    try:
        if not capture.isOpened():
            raise ValueError("Unable to read the uploaded video.")
        ok, _ = capture.read()
        if not ok:
            raise ValueError("The uploaded video contains no readable frames.")
    finally:
        capture.release()
