"""Explainable parking-region occupancy calculation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from services.detector import VehicleDetection

Point = tuple[float, float]


@dataclass(frozen=True)
class SpaceResult:
    space_id: str
    status: str
    overlap: float


def polygon_area(points: Sequence[Point]) -> float:
    """Return polygon area using the shoelace formula."""
    if len(points) < 3:
        return 0.0
    return abs(sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    )) / 2.0


def _clip_against_edge(points: list[Point], inside, intersection) -> list[Point]:
    if not points:
        return []
    output: list[Point] = []
    previous = points[-1]
    previous_inside = inside(previous)
    for current in points:
        current_inside = inside(current)
        if current_inside != previous_inside:
            output.append(intersection(previous, current))
        if current_inside:
            output.append(current)
        previous, previous_inside = current, current_inside
    return output


def polygon_rectangle_intersection_area(points: Sequence[Point], bbox: tuple[float, float, float, float]) -> float:
    """Clip a polygon against a vehicle bounding box and calculate the overlap area."""
    x1, y1, x2, y2 = bbox
    if x2 <= x1 or y2 <= y1:
        return 0.0
    clipped = list(points)

    def vertical_intersection(a: Point, b: Point, x: float) -> Point:
        if b[0] == a[0]:
            return (x, a[1])
        ratio = (x - a[0]) / (b[0] - a[0])
        return (x, a[1] + ratio * (b[1] - a[1]))

    def horizontal_intersection(a: Point, b: Point, y: float) -> Point:
        if b[1] == a[1]:
            return (a[0], y)
        ratio = (y - a[1]) / (b[1] - a[1])
        return (a[0] + ratio * (b[0] - a[0]), y)

    clipped = _clip_against_edge(clipped, lambda p: p[0] >= x1, lambda a, b: vertical_intersection(a, b, x1))
    clipped = _clip_against_edge(clipped, lambda p: p[0] <= x2, lambda a, b: vertical_intersection(a, b, x2))
    clipped = _clip_against_edge(clipped, lambda p: p[1] >= y1, lambda a, b: horizontal_intersection(a, b, y1))
    clipped = _clip_against_edge(clipped, lambda p: p[1] <= y2, lambda a, b: horizontal_intersection(a, b, y2))
    return polygon_area(clipped)


class ParkingAnalyzer:
    """Marks a parking region occupied when vehicle coverage reaches the threshold."""

    def __init__(self, occupancy_threshold: float) -> None:
        if not 0 < occupancy_threshold <= 1:
            raise ValueError("Occupancy threshold must be between 0 and 1.")
        self.occupancy_threshold = occupancy_threshold

    def analyze(self, spaces: Iterable[dict], detections: Iterable[VehicleDetection]) -> dict:
        normalized_spaces = list(spaces)
        detection_list = list(detections)
        if not normalized_spaces:
            raise ValueError("No parking spaces have been configured.")

        space_results: list[SpaceResult] = []
        for space in normalized_spaces:
            points = [tuple(map(float, point)) for point in space["points"]]
            region_area = polygon_area(points)
            if region_area <= 0:
                raise ValueError(f"Parking space {space['id']} has invalid coordinates.")
            maximum_overlap = max(
                (polygon_rectangle_intersection_area(points, detection.bbox) / region_area for detection in detection_list),
                default=0.0,
            )
            space_results.append(SpaceResult(
                space_id=str(space["id"]),
                status="occupied" if maximum_overlap >= self.occupancy_threshold else "available",
                overlap=round(maximum_overlap, 4),
            ))

        occupied = sum(result.status == "occupied" for result in space_results)
        total = len(space_results)
        return {
            "total_spaces": total,
            "occupied_spaces": occupied,
            "available_spaces": total - occupied,
            "occupancy_percentage": round((occupied / total) * 100, 2) if total else 0.0,
            "spaces": [
                {"id": item.space_id, "status": item.status, "overlap": item.overlap}
                for item in space_results
            ],
            "vehicles_detected": len(detection_list),
        }
