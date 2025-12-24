from typing import Tuple

import pyautogui

from .base import BaseMouseControls

pyautogui.MINIMUM_DURATION = 0
pyautogui.MINIMUM_SLEEP = 0
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False


class PyAutoGUIMouseControls(BaseMouseControls):

    _type = "pyautogui"

    def move(self, x: int, y: int) -> None:
        pyautogui.moveTo(x, y)

    def move_relative(self, dx: int, dy: int) -> None:
        pyautogui.moveRel(dx, dy)

    def click(self, button: str = "left") -> None:
        pyautogui.click(button=button)

    def get_position(self) -> Tuple[int, int]:
        pos = pyautogui.position()
        return (pos.x, pos.y)

    def press(self, button: str = "left") -> None:
        pyautogui.mouseDown(button=button)

    def release(self, button: str = "left") -> None:
        pyautogui.mouseUp(button=button)
