from typing import Dict, Optional

import mss
import numpy as np

from .base import BaseGrabber


class MSSGrabber(BaseGrabber):

    _type = "mss"

    def __init__(self):
        self._sct: Optional[mss.mss] = None

    def initialize(self, **kwargs) -> None:
        self._sct = mss.mss()

    def get_image(self, grab_area: Dict[str, int]) -> Optional[np.ndarray]:
        if self._sct is None:
            self.initialize()
        return np.array(self._sct.grab(grab_area))

    def cleanup(self) -> None:
        if self._sct is not None:
            self._sct.close()
            self._sct = None
