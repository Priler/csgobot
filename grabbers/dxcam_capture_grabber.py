from typing import Dict, Optional, Any

import numpy as np

from .base import BaseGrabber
from exceptions import GrabberInitError


class DXCamCaptureGrabber(BaseGrabber):

    _type = "dxcam_capture"

    def __init__(self):
        self._camera = None
        self._initialized = False
        self._region = None

    def initialize(self, **kwargs: Any) -> None:
        import dxcam
        self._camera = dxcam.create()

    def _start_capture(self, grab_area: Dict[str, int]) -> None:
        if self._camera is None:
            self.initialize()

        self._region = (
            grab_area["left"],
            grab_area["top"],
            grab_area["left"] + grab_area["width"],
            grab_area["top"] + grab_area["height"],
        )

        self._camera.start(region=self._region)

        if not self._camera.is_capturing:
            raise GrabberInitError("DXCam failed to start capture")

        self._initialized = True

    def get_image(self, grab_area: Dict[str, int]) -> Optional[np.ndarray]:
        if not self._initialized:
            self._start_capture(grab_area)
        return self._camera.get_latest_frame()

    def cleanup(self) -> None:
        if self._camera is not None:
            if self._camera.is_capturing:
                self._camera.stop()
            del self._camera
            self._camera = None
            self._initialized = False
