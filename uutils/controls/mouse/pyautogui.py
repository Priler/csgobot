import pyautogui

pyautogui.MINIMUM_DURATION = 0
pyautogui.MINIMUM_SLEEP = 0
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False


class MouseControls:
    type = "pyautogui"

    @staticmethod
    def move(x, y):
        pyautogui.moveTo(x, y)

    @staticmethod
    def move_relative(rel_x, rel_y):
        pyautogui.moveRel(rel_x, rel_y)

    @staticmethod
    def click():
        pyautogui.leftClick()

    @staticmethod
    def get_position():
        point = pyautogui.position()
        return (point.x, point.y)
