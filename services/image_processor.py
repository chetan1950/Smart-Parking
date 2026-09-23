"""Image analysis and annotation pipeline."""
from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Any

from services.detector import VehicleDetector
from services.parking_analyzer import ParkingAnalyzer


def annotate_frame(frame: Any, detections: list, spaces: list[dict], result: dict) -> Any:
    """Draw model boxes, status-labelled spaces, and computed statistics on a BGR frame."""
    import cv2
    import numpy as np

    status_by_id = {space["id"]: space for space in result["spaces"]}
    for detection in detections:
        x1, y1, x2, y2 = map(int, detection.bbox)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 191, 0), 2)
        cv2.putText(frame, f"{detection.class_name} {detection.confidence:.0%}", (x1, max(22, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 191, 0), 2, cv2.LINE_AA)
    for parking_space in spaces:
        status = status_by_id[parking_space["id"]]
        occupied = status["status"] == "occupied"
        color = (45, 55, 235) if occupied else (50, 180, 80)
        polygon = np.array(parking_space["points"], dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame, [polygon], isClosed=True, color=color, thickness=3)
        x, y = map(int, parking_space["points"][0])
        label = f"{parking_space['id']} - {status['status'].upper()}"
        cv2.putText(frame, label, (x, max(22, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.48, color, 2, cv2.LINE_AA)
    panel = f"Total: {result['total_spaces']} | Occupied: {result['occupied_spaces']} | Available: {result['available_spaces']} | Occupancy: {result['occupancy_percentage']:.1f}%"
    cv2.rectangle(frame, (0, 0), (min(frame.shape[1], 900), 42), (20, 29, 52), -1)
    cv2.putText(frame, panel, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
    return frame


class ImageProcessor:
    def __init__(self, detector: VehicleDetector, analyzer: ParkingAnalyzer) -> None:
        self.detector = detector
        self.analyzer = analyzer

    def process(self, input_path: Path, output_path: Path, spaces: list[dict]) -> tuple[dict, float]:
        import cv2

        started = perf_counter()
        image = cv2.imread(str(input_path))
        if image is None:
            raise ValueError("Unable to read the uploaded image.")
        detections = self.detector.detect(image)
        result = self.analyzer.analyze(spaces, detections)
        annotated = annotate_frame(image.copy(), detections, spaces, result)
        if not cv2.imwrite(str(output_path), annotated):
            raise RuntimeError("Unable to save the processed image.")
        return result, perf_counter() - started
