"""Upload endpoints and real image/video analysis workflow."""
from __future__ import annotations

import logging
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, flash, redirect, request, url_for

from database_models import Analysis, ParkingConfiguration, db
from services.image_processor import ImageProcessor
from services.video_processor import VideoProcessor
from utils.file_utils import allowed_file, relative_media_path, save_upload
from utils.validators import validate_image_file, validate_video_file

LOGGER = logging.getLogger(__name__)
analysis_bp = Blueprint("analysis", __name__)


def _active_spaces() -> tuple[ParkingConfiguration, list[dict]]:
    configuration = db.session.scalar(db.select(ParkingConfiguration).where(ParkingConfiguration.is_active.is_(True)))
    if configuration is None:
        raise ValueError("No parking configuration has been selected. Create and activate one in Admin first.")
    spaces = [{"id": space.space_id, "points": space.coordinates} for space in configuration.spaces]
    if not spaces:
        raise ValueError("The active parking configuration has no parking spaces.")
    return configuration, spaces


def _upload_and_process(media_type: str):
    upload = request.files.get("file")
    if upload is None or not upload.filename:
        raise ValueError(f"Please upload a {media_type}.")
    config = current_app.config
    allowed = config["ALLOWED_IMAGE_EXTENSIONS"] if media_type == "image" else config["ALLOWED_VIDEO_EXTENSIONS"]
    if not allowed_file(upload.filename, allowed):
        raise ValueError("Unsupported file format.")
    configuration, spaces = _active_spaces()
    upload_dir = Path(config["UPLOAD_FOLDER"]) / ("images" if media_type == "image" else "videos")
    saved_path, original_name = save_upload(upload, upload_dir)
    if media_type == "image":
        validate_image_file(saved_path)
        output_path = Path(config["OUTPUT_FOLDER"]) / "images" / f"processed_{uuid4().hex}.jpg"
        result, duration = ImageProcessor(current_app.extensions["detector"], current_app.extensions["parking_analyzer"]).process(saved_path, output_path, spaces)
        video_stats = None
    else:
        validate_video_file(saved_path)
        output_path = Path(config["OUTPUT_FOLDER"]) / "videos" / f"processed_{uuid4().hex}.mp4"
        result, video_stats, duration = VideoProcessor(
            current_app.extensions["detector"], current_app.extensions["parking_analyzer"], config["VIDEO_FRAME_SKIP"], config["VIDEO_MAX_WIDTH"]
        ).process(saved_path, output_path, spaces)
    record = Analysis(
        filename=original_name, media_type=media_type, output_path=relative_media_path(output_path, Path(current_app.root_path)),
        processing_time=round(duration, 3), configuration_id=configuration.id, space_statuses=result["spaces"],
        video_statistics=video_stats, **{key: result[key] for key in ("total_spaces", "occupied_spaces", "available_spaces", "occupancy_percentage", "vehicles_detected")},
    )
    db.session.add(record)
    db.session.commit()
    LOGGER.info("Completed %s analysis id=%s in %.2fs", media_type, record.id, duration)
    return redirect(url_for("main.analysis_result", analysis_id=record.id))


@analysis_bp.post("/upload/image")
@analysis_bp.post("/analyze/image")
def upload_image():
    try:
        return _upload_and_process("image")
    except Exception as exc:
        LOGGER.exception("Image analysis failed")
        flash(str(exc) if isinstance(exc, (ValueError, RuntimeError)) else "Image analysis failed. Check the server log.", "error")
        return redirect(url_for("main.index") + "#analyze")


@analysis_bp.post("/upload/video")
@analysis_bp.post("/analyze/video")
def upload_video():
    try:
        return _upload_and_process("video")
    except Exception as exc:
        LOGGER.exception("Video analysis failed")
        flash(str(exc) if isinstance(exc, (ValueError, RuntimeError)) else "Video processing failed. Check the server log.", "error")
        return redirect(url_for("main.index") + "#analyze")
