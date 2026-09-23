"""Small JSON API for dashboard integrations."""
from __future__ import annotations

from flask import Blueprint, jsonify
from sqlalchemy import func

from database_models import Analysis, db

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/dashboard")
def dashboard_data():
    latest = db.session.scalar(db.select(Analysis).order_by(Analysis.created_at.desc()))
    total = db.session.scalar(db.select(func.count(Analysis.id))) or 0
    return jsonify({"total_analyses": total, "latest": serialize(latest) if latest else None})


@api_bp.get("/parking-status")
def parking_status():
    latest = db.session.scalar(db.select(Analysis).order_by(Analysis.created_at.desc()))
    if latest is None:
        return jsonify(error="No completed analysis exists."), 404
    return jsonify({"analysis_id": latest.id, "spaces": latest.space_statuses, "occupancy_percentage": latest.occupancy_percentage})


@api_bp.get("/history")
def history_data():
    analyses = db.session.scalars(db.select(Analysis).order_by(Analysis.created_at.desc())).all()
    return jsonify([serialize(item) for item in analyses])


def serialize(item: Analysis) -> dict:
    return {"id": item.id, "filename": item.filename, "media_type": item.media_type, "created_at": item.created_at.isoformat(),
            "total_spaces": item.total_spaces, "occupied_spaces": item.occupied_spaces, "available_spaces": item.available_spaces,
            "occupancy_percentage": item.occupancy_percentage, "vehicles_detected": item.vehicles_detected}
