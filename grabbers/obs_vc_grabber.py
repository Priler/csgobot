from typing import Dict, Optional, Any

import cv2
import numpy as np

from .base import BaseGrabber
from exceptions import DeviceNotFoundError


class OBSVirtualCameraGrabber(BaseGrabber):

    _type = "obs_vc"

    def __init__(self):
        self._device: Optional[cv2.VideoCapture] = None
        self._size_configured = False

    def initialize(
        self,
        device_index: int = -1,
        device_name: str = "OBS Virtual Camera",
        **kwargs: Any,
    ) -> None:
        if device_index >= 0:
            self._device = cv2.VideoCapture(device_index)
        else:
            from pygrabber.dshow_graph import FilterGraph
            graph = FilterGraph()
            devices = graph.get_input_devices()

            try:
                idx = devices.index(device_name)
            except ValueError:
                raise DeviceNotFoundError(
                    f'Device "{device_name}" not found. Available: {devices}'
                )

            self._device = cv2.VideoCapture(idx)

    def _configure_size(self, width: int, height: int) -> None:
        if self._device is not None:
            self._device.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self._device.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self._size_configured = True

    def get_image(self, grab_area: Dict[str, int]) -> Optional[np.ndarray]:
        if self._device is None:
            self.initialize()

        if not self._size_configured:
            self._configure_size(grab_area["width"], grab_area["height"])

        ret, frame = self._device.read()
        if not ret or frame is None:
            return None

        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def cleanup(self) -> None:
        if self._device is not None:
            self._device.release()
            self._device = None
            self._size_configured = False
