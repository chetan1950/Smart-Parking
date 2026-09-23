"""Ultralytics YOLO vehicle detector with lazy model loading."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class VehicleDetection:
    bbox: tuple[float, float, float, float]
    confidence: float
    class_name: str


class VehicleDetector:
    """Detect configured COCO vehicle classes from BGR OpenCV images."""

    def __init__(self, model_path: str, confidence: float, iou: float, vehicle_classes: tuple[str, ...]) -> None:
        self.model_path = model_path
        self.confidence = confidence
        self.iou = iou
        self.vehicle_classes = {name.lower() for name in vehicle_classes}
        self._model: Any | None = None

    def _load_model(self) -> Any:
        if self._model is None:
            try:
                from ultralytics import YOLO
            except ImportError as exc:
                raise RuntimeError("Ultralytics is not installed. Run: pip install -r requirements.txt") from exc
            LOGGER.info("Loading YOLO model: %s", self.model_path)
            try:
                self._model = YOLO(self.model_path)
            except Exception as exc:
                raise RuntimeError(f"YOLO model could not be loaded: {exc}") from exc
        return self._model

    def detect(self, image: Any) -> list[VehicleDetection]:
        """Run actual model inference and return only configured vehicles."""
        model = self._load_model()
        try:
            result = model.predict(source=image, conf=self.confidence, iou=self.iou, verbose=False)[0]
        except Exception as exc:
            raise RuntimeError(f"YOLO inference failed: {exc}") from exc

        names = result.names
        vehicles: list[VehicleDetection] = []
        for box in result.boxes:
            class_index = int(box.cls[0].item())
            class_name = str(names[class_index]).lower()
            if class_name not in self.vehicle_classes:
                continue
            x1, y1, x2, y2 = (float(value) for value in box.xyxy[0].tolist())
            vehicles.append(
                VehicleDetection(
                    bbox=(x1, y1, x2, y2),
                    confidence=float(box.conf[0].item()),
                    class_name=class_name,
                )
            )
        return vehicles
