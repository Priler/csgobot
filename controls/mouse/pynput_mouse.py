from typing import Tuple

from pynput.mouse import Button, Controller

from .base import BaseMouseControls


class PynputMouseControls(BaseMouseControls):

    _type = "pynput"

    def __init__(self):
        self._controller = Controller()

    def _get_button(self, button: str) -> Button:
        buttons = {
            "left": Button.left,
            "right": Button.right,
            "middle": Button.middle,
        }
        return buttons.get(button, Button.left)

    def move(self, x: int, y: int) -> None:
        self._controller.position = (x, y)

    def move_relative(self, dx: int, dy: int) -> None:
        self._controller.move(dx, dy)

    def click(self, button: str = "left") -> None:
        self._controller.click(self._get_button(button), 1)

    def get_position(self) -> Tuple[int, int]:
        return self._controller.position

    def press(self, button: str = "left") -> None:
        self._controller.press(self._get_button(button))

    def release(self, button: str = "left") -> None:
        self._controller.release(self._get_button(button))
