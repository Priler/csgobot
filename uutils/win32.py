import win32gui


class WinHelper:
    @staticmethod
    def GetWindowRect(window_title, subtract_window_border=(16, 39, 16, 0)) -> tuple:
        assert len(window_title)
        assert len(subtract_window_border) == 4

        window_handle = win32gui.FindWindow(None, window_title)
        window_rect = list(win32gui.GetWindowRect(window_handle))

        window_rect[2] -= window_rect[0]  # calc width
        window_rect[3] -= window_rect[1]  # calc height

        if subtract_window_border:
            window_rect[0] += subtract_window_border[0]  # left
            window_rect[1] += subtract_window_border[1]  # top
            window_rect[2] -= subtract_window_border[2]  # right
            window_rect[3] -= subtract_window_border[3]  # bottom

        return tuple(window_rect)
