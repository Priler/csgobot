"""
WindMouse algorithm for human-like mouse movement.
Original author: Benjamin J. Land
License: GPLv3
"""
from typing import Callable, Tuple

import numpy as np

_SQRT3 = np.sqrt(3)
_SQRT5 = np.sqrt(5)


def wind_mouse(
    start_x: float,
    start_y: float,
    dest_x: float,
    dest_y: float,
    gravity: float = 9.0,
    wind: float = 3.0,
    max_step: float = 15.0,
    target_area: float = 12.0,
    move_callback: Callable[[int, int], None] = lambda x, y: None,
) -> Tuple[int, int]:
    current_x, current_y = start_x, start_y
    v_x = v_y = w_x = w_y = 0.0
    m_0 = max_step

    while True:
        dist = np.hypot(dest_x - start_x, dest_y - start_y)
        if dist < 1:
            break

        w_mag = min(wind, dist)

        if dist >= target_area:
            w_x = w_x / _SQRT3 + (2 * np.random.random() - 1) * w_mag / _SQRT5
            w_y = w_y / _SQRT3 + (2 * np.random.random() - 1) * w_mag / _SQRT5
        else:
            w_x /= _SQRT3
            w_y /= _SQRT3
            if m_0 < 3:
                m_0 = np.random.random() * 3 + 3
            else:
                m_0 /= _SQRT5

        v_x += w_x + gravity * (dest_x - start_x) / dist
        v_y += w_y + gravity * (dest_y - start_y) / dist

        v_mag = np.hypot(v_x, v_y)
        if v_mag > m_0:
            v_clip = m_0 / 2 + np.random.random() * m_0 / 2
            v_x = (v_x / v_mag) * v_clip
            v_y = (v_y / v_mag) * v_clip

        start_x += v_x
        start_y += v_y

        move_x = int(np.round(start_x))
        move_y = int(np.round(start_y))

        if current_x != move_x or current_y != move_y:
            current_x, current_y = move_x, move_y
            move_callback(current_x, current_y)

    return (current_x, current_y)
