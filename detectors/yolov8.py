"""
YOLOv8 Detector Implementation
"""

from typing import Dict, List, Any, Optional

import numpy as np
import torch

from .base import BaseDetector


class YOLOv8Detector(BaseDetector):
    """
    YOLOv8-based object detector using Ultralytics library.
    """

    def __init__(
        self,
        class_names: List[str],
        weights_path: str,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        device: Optional[str] = None,
        half_precision: Optional[bool] = None,
    ):
        """
        Initialize YOLOv8 detector.

        Args:
            class_names: List of class names
            weights_path: Path to .pt weights file
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IOU threshold for NMS
            device: Device to run on ("cuda" or "cpu", auto if None)
            half_precision: Use FP16 (auto-enabled on CUDA if None)
        """
        super().__init__(
            class_names=class_names,
            weights_path=weights_path,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold,
        )

        try:
            from ultralytics import YOLO
        except ImportError:
            raise ImportError(
                "ultralytics package required for YOLOv8. "
                "Install with: pip install ultralytics"
            )

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        if half_precision is None:
            self.half_precision = (self.device == "cuda")
        else:
            self.half_precision = half_precision

        self.model = YOLO(weights_path)
        self.model.to(self.device)

        self._warmup()

    def _warmup(self) -> None:
        """Warmup the model with a dummy inference."""
        dummy = np.zeros((640, 640, 3), dtype=np.uint8)
        self.detect(dummy, verbose=False)

    def detect(
        self,
        image: np.ndarray,
        verbose: bool = False,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Run YOLOv8 detection on an image.

        Args:
            image: Input image (HWC format, RGB or BGR)
            verbose: Whether to print verbose output

        Returns:
            Dict mapping class names to lists of detection dicts
        """
        # Validate image
        if image is None or image.size == 0:
            return {}

        if len(image.shape) != 3 or image.shape[2] > 4:
            return {}

        # Remove alpha channel if present
        if image.shape[2] == 4:
            image = image[:, :, :3]

        # Run inference
        results = self.model.predict(
            source=image,
            verbose=verbose,
            half=self.half_precision,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
        )

        # Parse results
        detections: Dict[str, List[Dict]] = {}

        for result in results:
            boxes = result.boxes

            for i, cls_id in enumerate(boxes.cls):
                cls_id_int = int(cls_id)
                class_name = self.get_class_name(cls_id_int)

                if class_name not in detections:
                    detections[class_name] = []

                # Get bounding box
                xyxy = boxes[i].xyxy.cpu().numpy()[0].tolist()
                conf = boxes.conf[i].item()

                detections[class_name].append({
                    "cls": cls_id_int,
                    "conf": conf,
                    "xyxy": xyxy,
                })

        return detections

    def detect_and_filter(
        self,
        image: np.ndarray,
        include_classes: tuple,
        verbose: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Convenience method to detect and filter in one call.

        Args:
            image: Input image
            include_classes: Classes to include in results
            verbose: Verbose output

        Returns:
            List of filtered detection dicts
        """
        detections = self.detect(image, verbose)
        return self.filter_by_classes(detections, include_classes)
