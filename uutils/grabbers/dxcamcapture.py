import dxcam


class Grabber:
    type = "dxcamcapture"
    dxcamera = None
    dxcapture_initialized = False

    def __dxcapture_init(self, grab_area):
        self.dxcamera = dxcam.create()

        self.dxcamera.start(region=(
            grab_area['left'], grab_area['top'],
            grab_area['width'] + grab_area['left'], grab_area['height'] + grab_area['top']
        ))

        if self.dxcamera.is_capturing:
            print("DXCAMERA capturing started ...")
            self.dxcapture_initialized = True
        else:
            print("DXCAMERA capture error.")
            exit(1)

    def get_image(self, grab_area):
        """
        Make a screenshot of a given area and return it.
        :param grab_area: Format is {"top": 40, "left": 0, "width": 800, "height": 640}
        :return: numpy array
        """
        if not self.dxcapture_initialized:
            self.__dxcapture_init(grab_area)

        # noinspection PyTypeChecker
        return self.dxcamera.get_latest_frame()
