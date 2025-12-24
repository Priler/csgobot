from typing import Dict, Optional, Tuple

import numpy as np

from .base import BaseGrabber


class Win32Grabber(BaseGrabber):

    _type = "win32"

    def _capture(self, region: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        import win32gui
        import win32ui
        import win32con
        import win32api

        hwin = win32gui.GetDesktopWindow()

        if region:
            left, top, x2, y2 = region
            width = x2 - left
            height = y2 - top
        else:
            width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
            left = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
            top = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)

        hwindc = win32gui.GetWindowDC(hwin)
        srcdc = win32ui.CreateDCFromHandle(hwindc)
        memdc = srcdc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(srcdc, width, height)
        memdc.SelectObject(bmp)
        memdc.BitBlt((0, 0), (width, height), srcdc, (left, top), win32con.SRCCOPY)

        signed_ints_array = bmp.GetBitmapBits(True)
        img = np.frombuffer(signed_ints_array, dtype=np.uint8)
        img.shape = (height, width, 4)

        srcdc.DeleteDC()
        memdc.DeleteDC()
        win32gui.ReleaseDC(hwin, hwindc)
        win32gui.DeleteObject(bmp.GetHandle())

        return img[:, :, :3]

    def get_image(self, grab_area: Dict[str, int]) -> Optional[np.ndarray]:
        region = (
            grab_area["left"],
            grab_area["top"],
            grab_area["left"] + grab_area["width"],
            grab_area["top"] + grab_area["height"],
        )
        return self._capture(region)
