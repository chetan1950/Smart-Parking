"""SQLite persistence models for analyses and reusable parking layouts."""
from __future__ import annotations

from datetime import datetime, timezone

from database_models import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ParkingConfiguration(db.Model):
    __tablename__ = "parking_configurations"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    reference_image = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    spaces = db.relationship("ParkingSpace", back_populates="configuration", cascade="all, delete-orphan", order_by="ParkingSpace.space_id")


class ParkingSpace(db.Model):
    __tablename__ = "parking_spaces"
    id = db.Column(db.Integer, primary_key=True)
    space_id = db.Column(db.String(50), nullable=False)
    configuration_id = db.Column(db.Integer, db.ForeignKey("parking_configurations.id"), nullable=False)
    coordinates = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    configuration = db.relationship("ParkingConfiguration", back_populates="spaces")
    __table_args__ = (db.UniqueConstraint("configuration_id", "space_id", name="unique_space_per_configuration"),)


class Analysis(db.Model):
    __tablename__ = "analyses"
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    media_type = db.Column(db.String(10), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    total_spaces = db.Column(db.Integer, nullable=False)
    occupied_spaces = db.Column(db.Integer, nullable=False)
    available_spaces = db.Column(db.Integer, nullable=False)
    occupancy_percentage = db.Column(db.Float, nullable=False)
    vehicles_detected = db.Column(db.Integer, nullable=False, default=0)
    output_path = db.Column(db.String(500), nullable=False)
    processing_time = db.Column(db.Float, nullable=False)
    configuration_id = db.Column(db.Integer, db.ForeignKey("parking_configurations.id"), nullable=True)
    space_statuses = db.Column(db.JSON, nullable=False, default=list)
    video_statistics = db.Column(db.JSON, nullable=True)
    configuration = db.relationship("ParkingConfiguration")
