"""Streaming frame-by-frame video analysis pipeline."""
from __future__ import annotations

from pathlib import Path
from time import perf_counter

from services.detector import VehicleDetector
from services.image_processor import annotate_frame
from services.parking_analyzer import ParkingAnalyzer


class VideoProcessor:
    def __init__(self, detector: VehicleDetector, analyzer: ParkingAnalyzer, frame_skip: int, max_width: int) -> None:
        self.detector = detector
        self.analyzer = analyzer
        self.frame_skip = max(1, frame_skip)
        self.max_width = max_width

    def process(self, input_path: Path, output_path: Path, spaces: list[dict]) -> tuple[dict, dict, float]:
        """Read sequentially, infer on sampled frames, and return real frame-derived statistics."""
        import cv2

        started = perf_counter()
        capture = cv2.VideoCapture(str(input_path))
        if not capture.isOpened():
            raise ValueError("Unable to read the uploaded video.")
        fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
        width, height = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width <= 0 or height <= 0:
            capture.release()
            raise ValueError("The uploaded video has invalid dimensions.")
        scale = min(1.0, self.max_width / width) if self.max_width else 1.0
        output_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, output_size)
        if not writer.isOpened():
            capture.release()
            raise RuntimeError("Unable to create the processed video.")

        frame_index = 0
        frame_results: list[dict] = []
        last_result: dict | None = None
        last_detections = []
        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break
                if scale != 1.0:
                    frame = cv2.resize(frame, output_size)
                if frame_index % self.frame_skip == 0:
                    last_detections = self.detector.detect(frame)
                    last_result = self.analyzer.analyze(spaces, last_detections)
                    frame_results.append(last_result)
                if last_result is not None:
                    writer.write(annotate_frame(frame.copy(), last_detections, spaces, last_result))
                else:
                    writer.write(frame)
                frame_index += 1
        finally:
            capture.release()
            writer.release()
        if not frame_results:
            raise ValueError("The uploaded video contains no readable frames.")

        occupancy_values = [item["occupancy_percentage"] for item in frame_results]
        final_result = frame_results[-1]
        video_stats = {
            "processed_frames": len(frame_results),
            "output_frames": frame_index,
            "initial_occupancy": occupancy_values[0],
            "final_occupancy": occupancy_values[-1],
            "maximum_occupancy": max(occupancy_values),
            "minimum_occupancy": min(occupancy_values),
            "average_occupancy": round(sum(occupancy_values) / len(occupancy_values), 2),
        }
        return final_result, video_stats, perf_counter() - started
