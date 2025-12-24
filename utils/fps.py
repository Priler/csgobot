import time
from collections import deque
from typing import Optional


class FPSCounter:

    def __init__(self, sample_size: int = 50):
        self._timestamps: deque = deque(maxlen=sample_size)

    def __call__(self) -> float:
        self._timestamps.append(time.perf_counter())

        if len(self._timestamps) < 2:
            return 0.0

        delta = self._timestamps[-1] - self._timestamps[0]
        if delta <= 0:
            return 0.0

        return (len(self._timestamps) - 1) / delta

    def reset(self) -> None:
        self._timestamps.clear()


class FrameTimer:

    def __init__(self):
        self._start: Optional[float] = None

    def start(self) -> None:
        self._start = time.perf_counter()

    def elapsed(self) -> float:
        if self._start is None:
            return 0.0
        return time.perf_counter() - self._start

    def elapsed_ms(self) -> float:
        return self.elapsed() * 1000
