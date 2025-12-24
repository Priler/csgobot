"""
FOV-based Mouse Movement Calculator
based on: https://stackoverflow.com/questions/74838124/how-to-convert-screen-x-y-cartesian-coordinates-to-3d-world-space-crosshair-mo

This handles the conversion from screen coordinates to mouse movement,
accounting for the non-linear relationship caused by perspective projection.

The key insight is that 3D games use perspective projection to render the scene:
    screen_x = focal_length * tan(angle_x)

Therefore, to convert screen position back to angle:
    angle_x = atan(screen_x / focal_length)

Where focal_length is derived from the field of view:
    focal_length = (screen_width / 2) / tan(fov_h / 2)

* read the stackoverflow post for more details *
"""

from dataclasses import dataclass
from math import atan, tan, radians, degrees, sqrt
from typing import Tuple, Optional

from config import FOVConfig, CaptureRegion


@dataclass
class AimResult:
    """Result of an aim calculation."""
    # Angular offset from crosshair to target (degrees)
    angle_x: float
    angle_y: float

    # Mouse movement required (raw units)
    mouse_x: int
    mouse_y: int

    # Distance from crosshair to target (pixels)
    pixel_distance: float

    # Total angular distance (degrees)
    angular_distance: float


class FOVMouseMovement:
    """
    Converts screen coordinates to mouse movement using correct perspective projection math.

    This solves the problem described in the StackOverflow question:
    "How to convert screen X, Y cartesian coordinates to 3D world space crosshair movement"

    The linear approximation (degs = fov/2 * offset/half_width) fails because:
    - At screen center: tan(angle) ≈ angle (works okay)
    - At screen edges: tan(angle) diverges from linear (increasingly wrong)

    The correct formula uses atan() to reverse the perspective projection.
    """

    def __init__(
        self,
        screen: CaptureRegion,
        fov: FOVConfig,
    ):
        """
        Initialize the FOV mouse movement calculator.

        Args:
            screen: The capture region (provides width/height)
            fov: FOV configuration (provides angles and x360 calibration)
        """
        self.screen = screen
        self.fov = fov

        self._center_x = screen.width / 2
        self._center_y = screen.height / 2

        self._focal_x = (screen.width / 2) / tan(radians(fov.horizontal / 2))
        self._focal_y = (screen.height / 2) / tan(radians(fov.vertical / 2))
        self._pixels_per_degree = fov.x360 / 360.0

    def screen_to_angle(self, target_x: float, target_y: float) -> Tuple[float, float]:
        """
        Convert screen coordinates to angular offset from crosshair.

        This is the core of the fix - using atan() instead of linear interpolation.

        Args:
            target_x: X coordinate of target on screen (pixels)
            target_y: Y coordinate of target on screen (pixels)

        Returns:
            Tuple of (angle_x, angle_y) in degrees
        """
        offset_x = target_x - self._center_x
        offset_y = target_y - self._center_y

        angle_x = degrees(atan(offset_x / self._focal_x))
        angle_y = degrees(atan(offset_y / self._focal_y))

        return angle_x, angle_y

    def angle_to_mouse(self, angle_x: float, angle_y: float) -> Tuple[int, int]:
        """
        Convert angular offset to mouse movement units.

        Args:
            angle_x: Horizontal angle in degrees
            angle_y: Vertical angle in degrees

        Returns:
            Tuple of (mouse_x, mouse_y) in raw mouse units
        """
        mouse_x = int(angle_x * self._pixels_per_degree)
        mouse_y = int(angle_y * self._pixels_per_degree)

        return mouse_x, mouse_y

    def get_move(
        self,
        target_x: float,
        target_y: float,
        smoothing: float = 1.0,
    ) -> AimResult:
        """
        Calculate the complete aim movement for a target.

        This is the main method to call - it handles the full pipeline:
        1. Screen coords → angles (using correct atan)
        2. Angles → mouse units
        3. Apply optional smoothing

        Args:
            target_x: X coordinate of target on screen (pixels)
            target_y: Y coordinate of target on screen (pixels)
            smoothing: Smoothing factor (1.0 = instant, >1.0 = slower)

        Returns:
            AimResult with all calculated values
        """
        angle_x, angle_y = self.screen_to_angle(target_x, target_y)
        mouse_x, mouse_y = self.angle_to_mouse(angle_x, angle_y)

        if smoothing > 1.0:
            mouse_x = int(mouse_x / smoothing)
            mouse_y = int(mouse_y / smoothing)

        pixel_distance = sqrt((target_x - self._center_x)**2 + (target_y - self._center_y)**2)
        angular_distance = sqrt(angle_x**2 + angle_y**2)

        return AimResult(
            angle_x=angle_x,
            angle_y=angle_y,
            mouse_x=mouse_x,
            mouse_y=mouse_y,
            pixel_distance=pixel_distance,
            angular_distance=angular_distance,
        )

    def get_move_to_point(
        self,
        target: Tuple[float, float],
        smoothing: float = 1.0,
    ) -> AimResult:
        """
        Convenience method that accepts a point tuple.

        Args:
            target: (x, y) coordinates of target on screen
            smoothing: Smoothing factor

        Returns:
            AimResult with all calculated values
        """
        return self.get_move(target[0], target[1], smoothing)

    def recalibrate(self, new_x360: int) -> None:
        """
        Update the x360 calibration value.

        This can be called if the user changes game sensitivity.

        Args:
            new_x360: New mouse units for 360 degree rotation
        """
        self.fov.x360 = new_x360
        self._pixels_per_degree = new_x360 / 360.0

    def update_fov(self, horizontal: float, vertical: float) -> None:
        """
        Update FOV values (e.g., if user zooms with a scope).

        Args:
            horizontal: New horizontal FOV in degrees
            vertical: New vertical FOV in degrees
        """
        self.fov.horizontal = horizontal
        self.fov.vertical = vertical

        # Recalculate focal lengths
        self._focal_x = (self.screen.width / 2) / tan(radians(horizontal / 2))
        self._focal_y = (self.screen.height / 2) / tan(radians(vertical / 2))


# Utility function for quick testing
def test_fov_math():
    """
    Test the FOV math with known values.

    At screen center, angle should be ~0.
    At screen edge, angle should be ~fov/2.
    """
    screen = CaptureRegion(width=1920, height=1080)
    fov = FOVConfig(horizontal=106.26, vertical=73.74, x360=16364)

    calc = FOVMouseMovement(screen, fov)

    # Test center (should be near 0)
    result = calc.get_move(960, 540)
    print(f"Center: angle=({result.angle_x:.2f}°, {result.angle_y:.2f}°)")
    assert abs(result.angle_x) < 0.1
    assert abs(result.angle_y) < 0.1

    # Test right edge (should be near fov_h/2 = 53.13°)
    result = calc.get_move(1920, 540)
    print(f"Right edge: angle=({result.angle_x:.2f}°, {result.angle_y:.2f}°)")
    assert 52 < result.angle_x < 54  # ~53.13°

    # Test bottom edge (should be near fov_v/2 = 36.87°)
    result = calc.get_move(960, 1080)
    print(f"Bottom edge: angle=({result.angle_x:.2f}°, {result.angle_y:.2f}°)")
    assert 36 < result.angle_y < 38  # ~36.87°

    # Test a point off-center
    result = calc.get_move(1200, 400)
    print(f"Off-center (1200, 400): angle=({result.angle_x:.2f}°, {result.angle_y:.2f}°)")
    print(f"  Mouse move: ({result.mouse_x}, {result.mouse_y})")
    print(f"  Pixel dist: {result.pixel_distance:.1f}px")
    print(f"  Angular dist: {result.angular_distance:.2f}°")

    print("\nAll tests passed!")


if __name__ == "__main__":
    test_fov_math()
