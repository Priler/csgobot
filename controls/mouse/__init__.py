from typing import Dict, Type

from .base import BaseMouseControls

_CONTROLS: Dict[str, Type[BaseMouseControls]] = {}
_LOAD_ERRORS: Dict[str, str] = {}


def get_mouse_controls(name: str) -> BaseMouseControls:
    _ensure_controls_loaded()

    if name not in _CONTROLS:
        available = list(_CONTROLS.keys())
        error_msg = f"Unknown mouse control: {name}. Available: {available}"
        if name in _LOAD_ERRORS:
            error_msg += f"\nLoad error for '{name}': {_LOAD_ERRORS[name]}"
        raise ValueError(error_msg)

    return _CONTROLS[name]()


def list_mouse_controls() -> list:
    _ensure_controls_loaded()
    return list(_CONTROLS.keys())


def _try_load(name: str, module: str, class_name: str) -> None:
    try:
        mod = __import__(module, fromlist=[class_name])
        _CONTROLS[name] = getattr(mod, class_name)
    except Exception as e:
        _LOAD_ERRORS[name] = f"{type(e).__name__}: {e}"


def _ensure_controls_loaded():
    if _CONTROLS:
        return

    _try_load("win32", "controls.mouse.win32_mouse", "Win32MouseControls")
    _try_load("pyautogui", "controls.mouse.pyautogui_mouse", "PyAutoGUIMouseControls")
    _try_load("pydirectinput", "controls.mouse.pydirectinput_mouse", "PyDirectInputMouseControls")
    _try_load("pynput", "controls.mouse.pynput_mouse", "PynputMouseControls")


__all__ = [
    "BaseMouseControls",
    "get_mouse_controls",
    "list_mouse_controls",
]
