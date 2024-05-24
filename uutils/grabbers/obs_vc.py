import cv2
import numpy


class Grabber:
    type = "obs_vc"
    device = None
    cap_size_set = False

    def obs_vc_init(self, capture_device = 0):
        self.device = cv2.VideoCapture(capture_device)

    def set_cap_size(self, w, h):
        # h = 360
        # w = 640

        self.device.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.device.set(cv2.CAP_PROP_FRAME_HEIGHT, h)


    def get_image(self, grab_area):
        """
        Return last frame.
        :return: numpy array
        """
        if not self.cap_size_set:
            self.set_cap_size(grab_area['width'], grab_area['height'])
            self.cap_size_set = True

        ret, frame = self.device.read()
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        return frame
