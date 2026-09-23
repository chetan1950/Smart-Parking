"""Read-only application pages."""
from __future__ import annotations

from pathlib import Path

from flask import Blueprint, abort, current_app, render_template, send_from_directory
from sqlalchemy import func

from database_models import Analysis, ParkingConfiguration, db

main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return render_template("index.html")


@main_bp.get("/dashboard")
def dashboard():
    latest = db.session.scalar(db.select(Analysis).order_by(Analysis.created_at.desc()))
    total_analyses = db.session.scalar(db.select(func.count(Analysis.id))) or 0
    aggregates = db.session.execute(
        db.select(
            func.avg(Analysis.occupancy_percentage), func.max(Analysis.occupancy_percentage), func.min(Analysis.occupancy_percentage)
        )
    ).one()
    return render_template("dashboard.html", latest=latest, total_analyses=total_analyses,
                           average=round(aggregates[0] or 0, 2), maximum=round(aggregates[1] or 0, 2), minimum=round(aggregates[2] or 0, 2))


@main_bp.get("/history")
def history():
    analyses = db.session.scalars(db.select(Analysis).order_by(Analysis.created_at.desc())).all()
    return render_template("history.html", analyses=analyses)


@main_bp.get("/analysis/<int:analysis_id>")
def analysis_result(analysis_id: int):
    analysis = db.get_or_404(Analysis, analysis_id)
    return render_template("analysis.html", analysis=analysis)


@main_bp.get("/analytics")
def analytics():
    analyses = db.session.scalars(db.select(Analysis).order_by(Analysis.created_at.asc())).all()
    values = [item.occupancy_percentage for item in analyses]
    return render_template("analytics.html", analyses=analyses, values=values)


@main_bp.get("/parking-layout")
def parking_layout():
    configuration = db.session.scalar(db.select(ParkingConfiguration).where(ParkingConfiguration.is_active.is_(True)))
    latest = db.session.scalar(db.select(Analysis).order_by(Analysis.created_at.desc()))
    return render_template("parking_layout.html", configuration=configuration, latest=latest)


@main_bp.get("/media/<path:relative_path>")
def media(relative_path: str):
    base_dir = Path(current_app.root_path)
    requested = (base_dir / relative_path).resolve()
    permitted_roots = [(base_dir / "uploads").resolve(), (base_dir / "outputs").resolve()]
    if not any(requested.is_relative_to(root) for root in permitted_roots) or not requested.is_file():
        abort(404)
    return send_from_directory(requested.parent, requested.name)
