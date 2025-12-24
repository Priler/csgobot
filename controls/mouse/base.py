from abc import ABC, abstractmethod
from typing import Tuple


class BaseMouseControls(ABC):

    _type: str = "base"

    @property
    def type(self) -> str:
        return self._type

    @abstractmethod
    def move(self, x: int, y: int) -> None:
        pass

    @abstractmethod
    def move_relative(self, dx: int, dy: int) -> None:
        pass

    @abstractmethod
    def click(self, button: str = "left") -> None:
        pass

    @abstractmethod
    def get_position(self) -> Tuple[int, int]:
        pass

    def press(self, button: str = "left") -> None:
        pass

    def release(self, button: str = "left") -> None:
        pass

    def double_click(self, button: str = "left") -> None:
        self.click(button)
        self.click(button)
