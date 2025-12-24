from typing import Dict, Optional, Any

import numpy as np

from .base import BaseGrabber


class DXCamGrabber(BaseGrabber):

    _type = "dxcam"

    def __init__(self):
        self._camera = None

    def initialize(self, **kwargs: Any) -> None:
        import dxcam
        self._camera = dxcam.create()

    def get_image(self, grab_area: Dict[str, int]) -> Optional[np.ndarray]:
        if self._camera is None:
            self.initialize()

        region = (
            grab_area["left"],
            grab_area["top"],
            grab_area["left"] + grab_area["width"],
            grab_area["top"] + grab_area["height"],
        )
        return self._camera.grab(region=region)

    def cleanup(self) -> None:
        if self._camera is not None:
            del self._camera
            self._camera = None
