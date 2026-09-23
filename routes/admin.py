"""Local administrator tools for reusable parking layouts."""
from __future__ import annotations

import logging
from pathlib import Path

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for

from database_models import ParkingConfiguration, ParkingSpace, db
from utils.file_utils import allowed_file, relative_media_path, save_upload
from utils.validators import validate_image_file

LOGGER = logging.getLogger(__name__)
admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/admin")
def admin():
    configurations = db.session.scalars(db.select(ParkingConfiguration).order_by(ParkingConfiguration.name)).all()
    active = next((item for item in configurations if item.is_active), None)
    return render_template("admin.html", configurations=configurations, active=active)


@admin_bp.post("/admin/configuration")
def create_configuration():
    try:
        name = (request.form.get("name") or "").strip()
        upload = request.files.get("reference_image")
        if not name or upload is None or not upload.filename:
            raise ValueError("A configuration name and reference image are required.")
        if not allowed_file(upload.filename, current_app.config["ALLOWED_IMAGE_EXTENSIONS"]):
            raise ValueError("Reference image must be JPG, JPEG, PNG, or WEBP.")
        path, _ = save_upload(upload, Path(current_app.config["UPLOAD_FOLDER"]) / "images")
        validate_image_file(path)
        configuration = ParkingConfiguration(name=name, reference_image=relative_media_path(path, Path(current_app.root_path)), is_active=True)
        db.session.execute(db.update(ParkingConfiguration).values(is_active=False))
        db.session.add(configuration)
        db.session.commit()
        flash("Configuration created. Draw its parking spaces below.", "success")
    except Exception as exc:
        db.session.rollback()
        flash(str(exc) if isinstance(exc, ValueError) else "Could not create the configuration.", "error")
    return redirect(url_for("admin.admin"))


@admin_bp.post("/admin/configuration/<int:configuration_id>/activate")
def activate_configuration(configuration_id: int):
    configuration = db.get_or_404(ParkingConfiguration, configuration_id)
    db.session.execute(db.update(ParkingConfiguration).values(is_active=False))
    configuration.is_active = True
    db.session.commit()
    flash(f"{configuration.name} is now the active layout.", "success")
    return redirect(url_for("admin.admin"))


@admin_bp.post("/parking-layout/save")
def save_layout():
    payload = request.get_json(silent=True) or {}
    configuration_id = payload.get("configuration_id")
    spaces = payload.get("spaces")
    configuration = db.get_or_404(ParkingConfiguration, configuration_id)
    if not isinstance(spaces, list):
        return jsonify(error="Spaces must be a list."), 400
    normalized: list[tuple[str, list[list[float]]]] = []
    ids: set[str] = set()
    try:
        for item in spaces:
            space_id = str(item.get("id", "")).strip().upper()
            points = item.get("points")
            if not space_id or space_id in ids or not isinstance(points, list) or len(points) < 3:
                raise ValueError("Each space needs a unique ID and at least three points.")
            clean_points = [[round(float(point[0]), 2), round(float(point[1]), 2)] for point in points]
            ids.add(space_id)
            normalized.append((space_id, clean_points))
        db.session.query(ParkingSpace).filter_by(configuration_id=configuration.id).delete()
        db.session.add_all(ParkingSpace(space_id=space_id, coordinates=points, configuration_id=configuration.id) for space_id, points in normalized)
        db.session.commit()
        return jsonify(message="Parking layout saved.", space_count=len(normalized))
    except (TypeError, ValueError, IndexError) as exc:
        db.session.rollback()
        return jsonify(error=str(exc)), 400
    except Exception:
        db.session.rollback()
        LOGGER.exception("Layout save failed")
        return jsonify(error="Could not save parking layout."), 500
