from pynput.mouse import Button, Controller

mouse = Controller()


class MouseControls:
    type = "pynput"

    @staticmethod
    def move(x, y):
        mouse.position = (x, y)

    @staticmethod
    def move_relative(rel_x, rel_y):
        mouse.move(rel_x, rel_y)

    @staticmethod
    def click():
        mouse.click(Button.left, 1)

    @staticmethod
    def get_position():
        return mouse.position
