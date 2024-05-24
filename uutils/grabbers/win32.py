import win32gui, win32ui, win32con, win32api
import numpy
import cv2


class Grabber:
    type = "win32"

    @staticmethod
    def __win32_grab(region=None):
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

        signedIntsArray = bmp.GetBitmapBits(True)
        img = numpy.fromstring(signedIntsArray, dtype='uint8')
        img.shape = (height, width, 4)  # height, width, channels

        srcdc.DeleteDC()
        memdc.DeleteDC()
        win32gui.ReleaseDC(hwin, hwindc)
        win32gui.DeleteObject(bmp.GetHandle())

        img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB) # convert to RGB

        return img

    def get_image(self, grab_area):
        """
        Make a screenshot of a given area and return it.
        :param grab_area: Format is {"top": 40, "left": 0, "width": 800, "height": 640}
        :return: numpy array
        """
        # noinspection PyTypeChecker
        return self.__win32_grab((
                grab_area['left'], grab_area['top'],
                grab_area['width'] + grab_area['left'], grab_area['height'] + grab_area['top']
            ))
