"""
Base detector interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple

import numpy as np


class BaseDetector(ABC):
    """Abstract base class for object detectors."""

    def __init__(
        self,
        class_names: List[str],
        weights_path: str,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
    ):
        """
        Initialize detector.

        Args:
            class_names: List of class names in order of class index
            weights_path: Path to model weights
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IOU threshold for NMS
        """
        self.class_names = class_names
        self.weights_path = weights_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.colors = self._generate_colors()

    def _generate_colors(self) -> List[Tuple[int, int, int]]:
        """Generate random colors for each class."""
        import random
        return [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
                for _ in self.class_names]

    def set_colors(self, colors: List[Tuple[int, int, int]]) -> None:
        """Set custom colors for classes."""
        self.colors = colors

    def get_class_name(self, class_id: int) -> str:
        """Get class name from class ID."""
        if 0 <= class_id < len(self.class_names):
            return self.class_names[class_id]
        return "unknown"

    @abstractmethod
    def detect(
        self,
        image: np.ndarray,
        verbose: bool = False,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run detection on an image.

        Args:
            image: Input image (HWC format, RGB)
            verbose: Whether to print verbose output

        Returns:
            Dict mapping class names to lists of detection dicts.
            Each detection dict has:
                - "cls": class ID (int)
                - "conf": confidence (float)
                - "xyxy": [x1, y1, x2, y2] bounding box
        """
        pass

    def filter_by_classes(
        self,
        detections: Dict[str, List[Dict]],
        include_classes: Tuple[str, ...],
    ) -> List[Dict[str, Any]]:
        """
        Filter detections to include only specified classes.

        Args:
            detections: Detection results from detect()
            include_classes: Tuple of class names to include

        Returns:
            Flat list of detection dicts with "tcls" field added
        """
        filtered = []

        for class_name, boxes in detections.items():
            if class_name in include_classes:
                for box in boxes:
                    box_copy = box.copy()
                    box_copy["tcls"] = class_name
                    filtered.append(box_copy)

        return filtered

    def draw_boxes(
        self,
        image: np.ndarray,
        detections: Dict[str, List[Dict]],
        min_confidence: float = 0.0,
        line_thickness: int = 2,
    ) -> np.ndarray:
        """
        Draw bounding boxes on image.

        Args:
            image: Input image (will be modified in place)
            detections: Detection results
            min_confidence: Minimum confidence to draw
            line_thickness: Box line thickness

        Returns:
            Image with boxes drawn
        """
        import cv2

        for class_name, boxes in detections.items():
            for box in boxes:
                if box["conf"] < min_confidence:
                    continue

                x1, y1, x2, y2 = [int(v) for v in box["xyxy"]]
                color = self.colors[box["cls"]]

                # Draw box
                cv2.rectangle(image, (x1, y1), (x2, y2), color, line_thickness)

                # Draw label
                label = f"{class_name} {box['conf']:.2f}"
                font_scale = line_thickness / 3
                font_thickness = max(line_thickness - 1, 1)

                (text_w, text_h), _ = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, font_thickness
                )

                # Label background
                cv2.rectangle(
                    image,
                    (x1, y1 - text_h - 4),
                    (x1 + text_w, y1),
                    color,
                    -1,
                )

                # Label text
                cv2.putText(
                    image,
                    label,
                    (x1, y1 - 2),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    (255, 255, 255),
                    font_thickness,
                )

        return image

    def draw_aim_point(
        self,
        image: np.ndarray,
        x: float,
        y: float,
        color: Tuple[int, int, int] = (0, 255, 0),
        radius: int = 5,
    ) -> np.ndarray:
        """
        Draw an aim point marker on the image.

        Args:
            image: Input image
            x, y: Aim point coordinates
            color: Marker color (BGR)
            radius: Marker radius

        Returns:
            Image with marker drawn
        """
        import cv2
        cv2.circle(image, (int(x), int(y)), radius, color, -1)
        cv2.circle(image, (int(x), int(y)), radius + 2, (255, 255, 255), 1)
        return image
