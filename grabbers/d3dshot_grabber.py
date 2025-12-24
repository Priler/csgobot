from typing import Dict, Optional, Any

import numpy as np

from .base import BaseGrabber


class D3DShotGrabber(BaseGrabber):

    _type = "d3dshot"

    def __init__(self):
        self._d3d = None

    def initialize(self, **kwargs: Any) -> None:
        import d3dshot
        self._d3d = d3dshot.create(capture_output="numpy")

    def get_image(self, grab_area: Dict[str, int]) -> Optional[np.ndarray]:
        if self._d3d is None:
            self.initialize()

        region = (
            grab_area["left"],
            grab_area["top"],
            grab_area["left"] + grab_area["width"],
            grab_area["top"] + grab_area["height"],
        )
        return self._d3d.screenshot(region=region)

    def cleanup(self) -> None:
        self._d3d = None
