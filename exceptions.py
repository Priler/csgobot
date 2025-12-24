class AICaptureError(Exception):
    pass


class GrabberError(AICaptureError):
    pass


class GrabberInitError(GrabberError):
    pass


class DeviceNotFoundError(GrabberError):
    pass


class CaptureError(GrabberError):
    pass


class ControlsError(AICaptureError):
    pass
