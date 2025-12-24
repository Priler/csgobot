from abc import ABC, abstractmethod
from typing import Dict, Optional, Any

import numpy as np


class BaseGrabber(ABC):

    _type: str = "base"

    @property
    def type(self) -> str:
        return self._type

    def initialize(self, **kwargs: Any) -> None:
        pass

    @abstractmethod
    def get_image(self, grab_area: Dict[str, int]) -> Optional[np.ndarray]:
        pass

    def cleanup(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False
