import dxcam


class Grabber:
    type="dxcam"
    dxcamera = None
    dxcapture_initialized = False

    def __dxcapture_init(self):
        self.dxcamera = dxcam.create()
        self.dxcapture_initialized = True

    def get_image(self, grab_area):
        """
        Make a screenshot of a given area and return it.
        :param grab_area: Format is {"top": 40, "left": 0, "width": 800, "height": 640}
        :return: numpy array
        """
        if not self.dxcapture_initialized:
            self.__dxcapture_init()

        # noinspection PyTypeChecker
        return self.dxcamera.grab(region=(
                grab_area['left'], grab_area['top'],
                grab_area['width'] + grab_area['left'], grab_area['height'] + grab_area['top']
            ))
