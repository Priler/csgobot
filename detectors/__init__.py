"""
Detection module for CS2 bot.

Supports YOLOv8 (and can be extended for YOLOv7).
"""

from .base import BaseDetector
from .yolov8 import YOLOv8Detector

__all__ = [
    "BaseDetector",
    "YOLOv8Detector",
]


def get_detector(detector_type: str, **kwargs) -> BaseDetector:
    """
    Factory function to get a detector by type.

    Args:
        detector_type: "yolov8" or "yolov7"
        **kwargs: Passed to detector constructor

    Returns:
        Detector instance
    """
    detectors = {
        "yolov8": YOLOv8Detector,
    }

    if detector_type not in detectors:
        raise ValueError(f"Unknown detector type: {detector_type}. Available: {list(detectors.keys())}")

    return detectors[detector_type](**kwargs)
