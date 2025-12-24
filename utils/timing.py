import time


def precise_sleep(duration: float, precision: float = 0.0005) -> None:
    if duration <= 0:
        return

    end = time.perf_counter() + duration

    if duration > precision * 2:
        time.sleep(duration - precision)

    while time.perf_counter() < end:
        pass


def busy_sleep(duration: float) -> None:
    if duration <= 0:
        return

    end = time.perf_counter() + duration
    while time.perf_counter() < end:
        pass
