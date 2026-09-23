"""Database initialization and models for SmartPark AI."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from database_models.analysis import Analysis, ParkingConfiguration, ParkingSpace  # noqa: E402,F401
