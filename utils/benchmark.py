import time
from typing import Dict, Optional, Tuple
from contextlib import contextmanager


class Benchmark:

    def __init__(self):
        self._marks: Dict[str, list] = {}

    def start(self, name: str = "default") -> float:
        now = time.perf_counter()
        self._marks[name] = [0.0, now, 0.0]
        return now

    def end(self, name: str = "default") -> Tuple[float, str]:
        now = time.perf_counter()

        if name not in self._marks:
            return (0.0, "0ms")

        self._marks[name][2] = now
        elapsed = now - self._marks[name][1]
        self._marks[name][0] = elapsed

        return (elapsed, f"{int(elapsed * 1000)}ms")

    def clear(self, name: Optional[str] = None) -> None:
        if name is None:
            self._marks.clear()
        elif name in self._marks:
            del self._marks[name]

    @contextmanager
    def measure(self, name: str = "default"):
        self.start(name)
        try:
            yield
        finally:
            self.end(name)

    def get_result(self, name: str = "default") -> Optional[float]:
        if name in self._marks:
            return self._marks[name][0]
        return None
