# Taken from ??? (unknown source)
import ctypes
import win32api
import win32con


class MouseControls:
    """It simulates the mouse"""
    MOUSEEVENTF_MOVE = 0x0001 # mouse move 
    MOUSEEVENTF_LEFTDOWN = 0x0002 # left button down 
    MOUSEEVENTF_LEFTUP = 0x0004 # left button up 
    MOUSEEVENTF_RIGHTDOWN = 0x0008 # right button down 
    MOUSEEVENTF_RIGHTUP = 0x0010 # right button up 
    MOUSEEVENTF_MIDDLEDOWN = 0x0020 # middle button down 
    MOUSEEVENTF_MIDDLEUP = 0x0040 # middle button up 
    MOUSEEVENTF_WHEEL = 0x0800 # wheel button rolled 
    MOUSEEVENTF_ABSOLUTE = 0x8000 # absolute move 
    SM_CXSCREEN = 0
    SM_CYSCREEN = 1

    def __init__(self):
        self.state_left = win32api.GetKeyState(0x01)

    def __do_event(self, flags, x_pos, y_pos, data, extra_info):
        """generate a mouse event"""
        x_calc = 65536 * x_pos / ctypes.windll.user32.GetSystemMetrics(self.SM_CXSCREEN) + 1
        y_calc = 65536 * y_pos / ctypes.windll.user32.GetSystemMetrics(self.SM_CYSCREEN) + 1

        xl = ctypes.c_long()
        xl.value = int(x_calc)
        yl = ctypes.c_long()
        yl.value = int(y_calc)
        return ctypes.windll.user32.mouse_event(flags, xl, yl, data, extra_info)

    def __get_button_value(self, button_name, button_up=False):
        """convert the name of the button into the corresponding value"""
        buttons = 0
        if button_name.find("right") >= 0:
            buttons = self.MOUSEEVENTF_RIGHTDOWN
        if button_name.find("left") >= 0:
            buttons = buttons + self.MOUSEEVENTF_LEFTDOWN
        if button_name.find("middle") >= 0:
            buttons = buttons + self.MOUSEEVENTF_MIDDLEDOWN
        if button_up:
            buttons = buttons << 1
        return buttons

    def is_left_mouse_down(self):
        a = win32api.GetKeyState(0x01)

        if a < 0:
            return True
        else:
            return False

    def move(self, x, y):
        """move the mouse to the specified coordinates"""
        old_pos = self.get_position()
        x = x if (x != -1) else old_pos[0]
        y = y if (y != -1) else old_pos[1]
        self.__do_event(self.MOUSEEVENTF_MOVE + self.MOUSEEVENTF_ABSOLUTE, x, y, 0, 0)

    def move_relative(self, x, y):
        """move the mouse to the specified coordinates"""
        # self.__do_event(self.MOUSEEVENTF_MOVE, x, y, 0, 0)
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, x, y, 0, 0)

    def get_position(self):
        """get mouse position"""
        return win32api.GetCursorPos()

    def click(self):
        """left mouse button click"""
        self.__do_event(self.__get_button_value("left", False) + self.__get_button_value("left", True), 0, 0, 0, 0)

    def press_button(self, button_name="left", button_up=False):
        """push a button of the mouse"""
        self.__do_event(self.__get_button_value(button_name, button_up), 0, 0, 0, 0)

    def hold_mouse(self, button_name="left"):
        """hold a button of the mouse"""
        self.__do_event(self.__get_button_value(button_name, False), 0, 0, 0, 0)

    def release_mouse(self, button_name="left"):
        """release a button of the mouse"""
        self.__do_event(self.__get_button_value(button_name, True), 0, 0, 0, 0)

    def double_click (self):
        """Double click at the specifed placed"""
        for i in range(0, 1):
            self.click()