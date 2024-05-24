import mss
import numpy
import cv2


class Grabber:
    type = "mss"
    sct = mss.mss()

    def get_image(self, grab_area):
        """
        Make a screenshot of a given area and return it.
        :param grab_area: Format is {"top": 40, "left": 0, "width": 800, "height": 640}
        :return: numpy array
        """
        return cv2.cvtColor(numpy.array(self.sct.grab(grab_area)), cv2.COLOR_BGR2RGB) # return RGB, not BGRA
