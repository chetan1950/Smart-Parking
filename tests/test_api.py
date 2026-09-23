from app import create_app
from database_models import Analysis, db


def test_dashboard_api_returns_empty_state(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}"})
    with app.test_client() as client:
        response = client.get("/api/dashboard")
    assert response.status_code == 200
    assert response.get_json() == {"latest": None, "total_analyses": 0}


def test_history_api_serializes_database_analysis(tmp_path):
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}"})
    with app.app_context():
        db.session.add(Analysis(filename="lot.jpg", media_type="image", total_spaces=50, occupied_spaces=30,
                               available_spaces=20, occupancy_percentage=60.0, vehicles_detected=4,
                               output_path="outputs/images/example.jpg", processing_time=1.2, space_statuses=[]))
        db.session.commit()
    with app.test_client() as client:
        response = client.get("/api/history")
    assert response.status_code == 200
    assert response.get_json()[0]["occupancy_percentage"] == 60.0
