from typing import Dict, Type, Any

from .base import BaseGrabber

_GRABBERS: Dict[str, Type[BaseGrabber]] = {}
_LOAD_ERRORS: Dict[str, str] = {}


def register_grabber(name: str):
    def decorator(cls: Type[BaseGrabber]):
        _GRABBERS[name] = cls
        return cls
    return decorator


def get_grabber(name: str, **kwargs: Any) -> BaseGrabber:
    _ensure_grabbers_loaded()

    if name not in _GRABBERS:
        available = list(_GRABBERS.keys())
        error_msg = f"Unknown grabber: {name}. Available: {available}"
        if name in _LOAD_ERRORS:
            error_msg += f"\nLoad error for '{name}': {_LOAD_ERRORS[name]}"
        raise ValueError(error_msg)

    grabber = _GRABBERS[name]()
    grabber.initialize(**kwargs)
    return grabber


def list_grabbers() -> list:
    _ensure_grabbers_loaded()
    return list(_GRABBERS.keys())


def _try_load(name: str, module: str, class_name: str) -> None:
    try:
        mod = __import__(module, fromlist=[class_name])
        _GRABBERS[name] = getattr(mod, class_name)
    except Exception as e:
        _LOAD_ERRORS[name] = f"{type(e).__name__}: {e}"


def _ensure_grabbers_loaded():
    if _GRABBERS:
        return

    _try_load("mss", "grabbers.mss_grabber", "MSSGrabber")
    _try_load("dxcam", "grabbers.dxcam_grabber", "DXCamGrabber")
    _try_load("dxcam_capture", "grabbers.dxcam_capture_grabber", "DXCamCaptureGrabber")
    _try_load("win32", "grabbers.win32_grabber", "Win32Grabber")
    _try_load("obs_vc", "grabbers.obs_vc_grabber", "OBSVirtualCameraGrabber")
    _try_load("d3dshot", "grabbers.d3dshot_grabber", "D3DShotGrabber")
    _try_load("screengear", "grabbers.screengear_grabber", "ScreenGearGrabber")


__all__ = [
    "BaseGrabber",
    "get_grabber",
    "list_grabbers",
    "register_grabber",
]
