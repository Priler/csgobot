import pydirectinput

pydirectinput.MINIMUM_DURATION = 0
pydirectinput.MINIMUM_SLEEP = 0
pydirectinput.PAUSE = 0
pydirectinput.FAILSAFE = False


class MouseControls:
    type = "pydirectinput"

    @staticmethod
    def move(x, y):
        pydirectinput.moveTo(x, y)

    @staticmethod
    def move_relative(rel_x, rel_y):
        pydirectinput.moveRel(rel_x, rel_y)

    @staticmethod
    def click():
        pydirectinput.leftClick()

    @staticmethod
    def get_position():
        return list(pydirectinput.position())
