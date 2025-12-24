"""
Entry point for configuring and running the bot.
"""

import sys
import logging

from config import (
    AppConfig,
    CaptureRegion,
    OBSConfig,
    FOVConfig,
    DetectorConfig,
    DetectorType,
    AimConfig,
    Team,
    PreviewConfig,
    HotkeyConfig,
    adjust_region_to_multiple,
)


# =============
# CONFIGURATION
# =============

# Game window title (must match exactly)
WINDOW_TITLE = "Counter-Strike 2"

# Screen capture method
# Options: "mss", "obs_vc", "dxcam", "dxcam_capture", "win32"
# - "mss": Cross-platform, good performance
# - "obs_vc": Uses OBS Virtual Camera (requires OBS setup) * should be best perf
# - "dxcam": Windows only, GPU accelerated (fastest in theory, but mixed results)
GRABBER_TYPE = "obs_vc"

# OBS Virtual Camera settings (only for GRABBER_TYPE == "obs_vc")
OBS_DEVICE_INDEX = -1  # -1 to use device name instead
OBS_DEVICE_NAME = "OBS Virtual Camera"

# YOLO model settings
YOLO_WEIGHTS = "./yolov8/cs2_yolov8m_640_augmented_v4.pt"
CONFIDENCE_THRESHOLD = 0.7
IOU_THRESHOLD = 0.2

# FOV settings (CS2 defaults for 16:9)
# These are the field of view angles in degrees
FOV_HORIZONTAL = 106.26
FOV_VERTICAL = 73.74

# Mouse calibration
# x360 = mouse movement units required for 360 degree turn
# You might need to calibrate this for your sensitivity:
# 1. Set a marker in-game
# 2. Record mouse movement while doing a full 360
# 3. That number is your x360
# X360 = 16364  # Default for CS2 at sensitivity 1.0
X360 = 7792  # Default for CS2 at sensitivity 1.0

# Aim settings
CURRENT_TEAM = Team.CT  # Your starting team
PRIORITIZE_HEADS = True  # Prefer headshots
MAX_ASSIST_DISTANCE = 300  # Max pixel distance to engage
SMOOTHING = 1.0  # 1.0 = instant, 2.0 = half speed, etc.
AUTO_SHOOT = False  # Automatic shooting (not recommended)
DEAD_ZONE = 5.0  # Minimum pixel distance to move
ONE_SHOT = False  # Only move once per activation

# Hotkeys
ACTIVATION_HOTKEY = 58  # CAPS LOCK
TEAM_CHANGE_HOTKEY = "ctrl+t"
EXIT_HOTKEY = "ctrl+q"

# Preview window
SHOW_PREVIEW = True
PREVIEW_WIDTH = 1280
PREVIEW_HEIGHT = 720


# ===========================
# DON'T TOUCH BELOW THIS LINE
# ===========================

def create_config() -> AppConfig:
    """Create application configuration from settings above."""

    # Create sub-configs
    obs_config = OBSConfig(
        device_index=OBS_DEVICE_INDEX,
        device_name=OBS_DEVICE_NAME,
    )

    fov_config = FOVConfig(
        horizontal=FOV_HORIZONTAL,
        vertical=FOV_VERTICAL,
        x360=X360,
    )

    detector_config = DetectorConfig(
        type=DetectorType.YOLOV8,
        weights_path=YOLO_WEIGHTS,
        confidence_threshold=CONFIDENCE_THRESHOLD,
        iou_threshold=IOU_THRESHOLD,
    )

    aim_config = AimConfig(
        current_team=CURRENT_TEAM,
        prioritize_heads=PRIORITIZE_HEADS,
        max_assist_distance=MAX_ASSIST_DISTANCE,
        smoothing_factor=SMOOTHING,
        auto_shoot=AUTO_SHOOT,
        dead_zone=DEAD_ZONE,
        one_shot=ONE_SHOT,
    )

    preview_config = PreviewConfig(
        enabled=SHOW_PREVIEW,
        size=(PREVIEW_WIDTH, PREVIEW_HEIGHT),
    )

    hotkey_config = HotkeyConfig(
        activation=ACTIVATION_HOTKEY,
        change_team=TEAM_CHANGE_HOTKEY,
        exit=EXIT_HOTKEY,
    )

    # Build grabber options
    grabber_options = {}
    if GRABBER_TYPE == "obs_vc":
        grabber_options = {
            "device_index": OBS_DEVICE_INDEX,
            "device_name": OBS_DEVICE_NAME,
        }

    # Create main config
    config = AppConfig(
        window_title=WINDOW_TITLE,
        grabber_type=GRABBER_TYPE,
        grabber_options=grabber_options,
        obs=obs_config,
        fov=fov_config,
        detector=detector_config,
        aim=aim_config,
        preview=preview_config,
        hotkeys=hotkey_config,
    )

    return config


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("CS2Bot")

    # Create configuration
    config = create_config()

    # Try to get window rect
    try:
        from utils.win32 import get_window_rect
        rect = get_window_rect(
            config.window_title,
            config.border_offsets,
        )
        config.capture_region = CaptureRegion(
            left=rect[0],
            top=rect[1],
            width=rect[2],
            height=rect[3],
        )
        config.capture_region = adjust_region_to_multiple(config.capture_region, 32)
        logger.info(f"Capture region: {config.capture_region}")
    except Exception as e:
        logger.warning(f"Could not get window rect: {e}")
        logger.info("Using default capture region (1920x1080)")
        config.capture_region = CaptureRegion()

    # Import and run
    from main import CS2Bot

    logger.info("=" * 50)
    logger.info("CS2 Bot Starting")
    logger.info("=" * 50)
    logger.info(f"Window: {config.window_title}")
    logger.info(f"Grabber: {config.grabber_type}")
    logger.info(f"FOV: {config.fov.horizontal}° x {config.fov.vertical}°")
    logger.info(f"x360: {config.fov.x360}")
    logger.info(f"Team: {config.aim.current_team.value.upper()}")
    logger.info("=" * 50)
    logger.info(f"Activation: CAPS LOCK")
    logger.info(f"Change Team: Ctrl+T")
    logger.info(f"Exit: Ctrl+Q")
    logger.info("=" * 50)

    bot = CS2Bot(config)
    return bot.run()


if __name__ == "__main__":
    sys.exit(main())
