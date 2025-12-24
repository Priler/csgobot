from typing import Tuple, Optional


def get_window_rect(
    window_title: str,
    border_offsets: Tuple[int, int, int, int] = (0, 0, 0, 0),
) -> Tuple[int, int, int, int]:
    import win32gui

    if not window_title:
        raise ValueError("Window title cannot be empty")

    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        raise ValueError(f"Window not found: {window_title}")

    rect = list(win32gui.GetWindowRect(hwnd))

    width = rect[2] - rect[0]
    height = rect[3] - rect[1]

    left = rect[0] + border_offsets[0]
    top = rect[1] + border_offsets[1]
    width -= border_offsets[0] + border_offsets[2]
    height -= border_offsets[1] + border_offsets[3]

    return (left, top, width, height)


def find_window(title: str) -> Optional[int]:
    import win32gui
    return win32gui.FindWindow(None, title) or None


def get_foreground_window_title() -> str:
    import win32gui
    hwnd = win32gui.GetForegroundWindow()
    return win32gui.GetWindowText(hwnd)
