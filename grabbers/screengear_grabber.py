from typing import Dict, Optional, Any

import numpy as np

from .base import BaseGrabber


class ScreenGearGrabber(BaseGrabber):

    _type = "screengear"

    def __init__(self):
        self._stream = None
        self._initialized = False
        self._logging = False

    def initialize(self, logging: bool = False, **kwargs: Any) -> None:
        self._logging = logging

    def _start_stream(self, grab_area: Dict[str, int]) -> None:
        from vidgear.gears import ScreenGear
        self._stream = ScreenGear(logging=self._logging, **grab_area).start()
        self._initialized = True

    def get_image(self, grab_area: Dict[str, int]) -> Optional[np.ndarray]:
        if not self._initialized:
            self._start_stream(grab_area)
        return self._stream.read()

    def cleanup(self) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream = None
            self._initialized = False
