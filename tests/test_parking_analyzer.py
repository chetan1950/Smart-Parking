from services.detector import VehicleDetection
from services.parking_analyzer import ParkingAnalyzer, polygon_rectangle_intersection_area


SPACES = [
    {"id": "P001", "points": [[0, 0], [100, 0], [100, 100], [0, 100]]},
    {"id": "P002", "points": [[110, 0], [210, 0], [210, 100], [110, 100]]},
]


def test_parking_statistics_are_calculated_from_overlap():
    detection = VehicleDetection((0, 0, 80, 100), 0.95, "car")
    result = ParkingAnalyzer(0.30).analyze(SPACES, [detection])
    assert result["total_spaces"] == 2
    assert result["occupied_spaces"] == 1
    assert result["available_spaces"] == 1
    assert result["occupancy_percentage"] == 50.0
    assert result["spaces"][0]["status"] == "occupied"
    assert result["spaces"][1]["status"] == "available"


def test_partial_overlap_respects_configured_threshold():
    detection = VehicleDetection((0, 0, 20, 100), 0.9, "car")
    result = ParkingAnalyzer(0.30).analyze(SPACES[:1], [detection])
    assert result["occupied_spaces"] == 0
    assert result["spaces"][0]["overlap"] == 0.2


def test_empty_layout_has_a_useful_error():
    try:
        ParkingAnalyzer(0.30).analyze([], [])
    except ValueError as exc:
        assert "No parking spaces" in str(exc)
    else:
        raise AssertionError("Expected an empty layout to fail")


def test_polygon_rectangle_overlap_for_non_rectangular_space():
    triangle = [(0, 0), (100, 0), (0, 100)]
    assert polygon_rectangle_intersection_area(triangle, (0, 0, 100, 100)) == 5000
