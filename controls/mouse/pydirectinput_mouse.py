from typing import Tuple

import pydirectinput

from .base import BaseMouseControls

pydirectinput.MINIMUM_DURATION = 0
pydirectinput.MINIMUM_SLEEP = 0
pydirectinput.PAUSE = 0
pydirectinput.FAILSAFE = False


class PyDirectInputMouseControls(BaseMouseControls):

    _type = "pydirectinput"

    def move(self, x: int, y: int) -> None:
        pydirectinput.moveTo(x, y)

    def move_relative(self, dx: int, dy: int) -> None:
        pydirectinput.moveRel(dx, dy)

    def click(self, button: str = "left") -> None:
        pydirectinput.click(button=button)

    def get_position(self) -> Tuple[int, int]:
        pos = pydirectinput.position()
        return (pos[0], pos[1])

    def press(self, button: str = "left") -> None:
        pydirectinput.mouseDown(button=button)

    def release(self, button: str = "left") -> None:
        pydirectinput.mouseUp(button=button)
