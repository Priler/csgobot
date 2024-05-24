import d3dshot


class Grabber:
    type = "d3dshot"
    d = None

    def __init__(self):
        self.d = d3dshot.create(capture_output="numpy")

    def get_image(self, grab_area):
        """
        Make a screenshot of a given area and return it.
        :param grab_area: Format is {"top": 40, "left": 0, "width": 800, "height": 640}
        :return: numpy array
        """

        # noinspection PyTypeChecker
        return self.d.screenshot(region=(grab_area["left"], grab_area["top"], grab_area["left"]+grab_area["width"], grab_area["top"]+grab_area["height"]))
