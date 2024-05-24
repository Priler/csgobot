from vidgear.gears import ScreenGear


class Grabber:
    type = "screengear"
    stream = None
    stream_initialized = False

    def __stream_init(self, grab_area):
        self.stream = ScreenGear(logging=True, **grab_area).start()
        self.stream_initialized = True

    def get_image(self, grab_area):
        """
        Make a screenshot of a given area and return it.
        :param grab_area: Format is {"top": 40, "left": 0, "width": 800, "height": 640}
        :return: numpy array
        """
        if not self.stream_initialized:
            self.__stream_init(grab_area)

        # noinspection PyTypeChecker
        return self.stream.read()
