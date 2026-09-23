"""SmartPark AI Flask application entry point."""
from __future__ import annotations

import logging
import os

from flask import Flask, render_template

from config import Config
from database_models import db
from routes.admin import admin_bp
from routes.analysis import analysis_bp
from routes.api import api_bp
from routes.main import main_bp
from services.detector import VehicleDetector
from services.parking_analyzer import ParkingAnalyzer


def create_app(test_config: dict | None = None) -> Flask:
    Config.ensure_directories()
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{Config.DATABASE_PATH.as_posix()}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if test_config:
        app.config.update(test_config)

    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    db.init_app(app)
    app.extensions["detector"] = VehicleDetector(app.config["MODEL_PATH"], app.config["CONFIDENCE_THRESHOLD"], app.config["IOU_THRESHOLD"], app.config["VEHICLE_CLASSES"])
    app.extensions["parking_analyzer"] = ParkingAnalyzer(app.config["OCCUPANCY_THRESHOLD"])

    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    @app.errorhandler(413)
    def file_too_large(_error):
        return render_template("error.html", message="Upload exceeds the configured file-size limit."), 413

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", message="The page or media file was not found."), 404

    with app.app_context():
        db.create_all()
    app.logger.info("SmartPark AI initialized. YOLO loads lazily on the first analysis.")
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=os.getenv("FLASK_DEBUG", "0") == "1")
