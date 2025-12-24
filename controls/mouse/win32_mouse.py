import ctypes
from typing import Tuple

from .base import BaseMouseControls


class Win32MouseControls(BaseMouseControls):

    _type = "win32"

    MOUSEEVENTF_MOVE = 0x0001
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    MOUSEEVENTF_MIDDLEDOWN = 0x0020
    MOUSEEVENTF_MIDDLEUP = 0x0040
    MOUSEEVENTF_WHEEL = 0x0800
    MOUSEEVENTF_ABSOLUTE = 0x8000
    SM_CXSCREEN = 0
    SM_CYSCREEN = 1

    def _do_event(self, flags: int, x_pos: int, y_pos: int, data: int = 0) -> int:
        x_calc = int(65536 * x_pos / ctypes.windll.user32.GetSystemMetrics(self.SM_CXSCREEN) + 1)
        y_calc = int(65536 * y_pos / ctypes.windll.user32.GetSystemMetrics(self.SM_CYSCREEN) + 1)
        return ctypes.windll.user32.mouse_event(flags, x_calc, y_calc, data, 0)

    def _get_button_flags(self, button: str, up: bool = False) -> int:
        flags = 0
        if "left" in button:
            flags |= self.MOUSEEVENTF_LEFTDOWN
        if "right" in button:
            flags |= self.MOUSEEVENTF_RIGHTDOWN
        if "middle" in button:
            flags |= self.MOUSEEVENTF_MIDDLEDOWN
        if up:
            flags <<= 1
        return flags

    def move(self, x: int, y: int) -> None:
        import win32api
        old_x, old_y = win32api.GetCursorPos()
        x = x if x != -1 else old_x
        y = y if y != -1 else old_y
        self._do_event(self.MOUSEEVENTF_MOVE | self.MOUSEEVENTF_ABSOLUTE, x, y)

    def move_relative(self, dx: int, dy: int) -> None:
        import win32api
        import win32con
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, dx, dy, 0, 0)

    def click(self, button: str = "left") -> None:
        down = self._get_button_flags(button, up=False)
        up = self._get_button_flags(button, up=True)
        self._do_event(down | up, 0, 0)

    def get_position(self) -> Tuple[int, int]:
        import win32api
        return win32api.GetCursorPos()

    def press(self, button: str = "left") -> None:
        self._do_event(self._get_button_flags(button, up=False), 0, 0)

    def release(self, button: str = "left") -> None:
        self._do_event(self._get_button_flags(button, up=True), 0, 0)
