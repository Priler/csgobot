"""
Recoil Compensation System (experimental, probably not works for now)

Compensates for weapon spray patterns by applying counter-movement
based on timing since first shot.

Spray patterns are loaded from CSV files with format:
    x_offset, y_offset, duration_ms
"""

import csv
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Optional


@dataclass
class RecoilPattern:
    """A single step in a recoil pattern."""
    x: float  # Horizontal offset
    y: float  # Vertical offset
    duration_ms: float  # Duration of this step in milliseconds


@dataclass
class RecoilCompensator:
    """
    Compensates for weapon recoil by tracking shot timing
    and applying counter-movement from a spray pattern.
    """

    # Pattern data
    pattern: List[RecoilPattern] = field(default_factory=list)

    # Compensation multiplier (adjust based on sensitivity)
    multiplier: float = 1.0

    # State
    _firing: bool = False
    _shot_start_time: float = 0.0

    @classmethod
    def from_csv(cls, csv_path: str, multiplier: float = 1.0) -> "RecoilCompensator":
        """
        Load a recoil pattern from a CSV file.

        CSV format: x_offset, y_offset, duration_ms

        Args:
            csv_path: Path to CSV file
            multiplier: Compensation strength multiplier

        Returns:
            RecoilCompensator instance
        """
        pattern = []

        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 3:
                    pattern.append(RecoilPattern(
                        x=float(row[0]),
                        y=float(row[1]),
                        duration_ms=float(row[2]),
                    ))

        compensator = cls(multiplier=multiplier)
        compensator.pattern = pattern
        return compensator

    def start_firing(self) -> None:
        """Call when the player starts firing."""
        self._firing = True
        self._shot_start_time = time.time()

    def stop_firing(self) -> None:
        """Call when the player stops firing."""
        self._firing = False

    def is_firing(self) -> bool:
        """Check if currently tracking a spray."""
        return self._firing

    def get_compensation(self) -> Tuple[float, float]:
        """
        Get the current recoil compensation offset.

        Returns:
            (x_offset, y_offset) to apply to mouse movement
        """
        if not self._firing or not self.pattern:
            return (0.0, 0.0)

        elapsed_ms = (time.time() - self._shot_start_time) * 1000

        # Find the current pattern step based on elapsed time
        cumulative_time = 0.0
        total_x = 0.0
        total_y = 0.0

        for step in self.pattern:
            if elapsed_ms > cumulative_time:
                cumulative_time += step.duration_ms
                total_x = step.x
                total_y = step.y
            else:
                break

        # Apply multiplier and return
        # Note: Y is typically inverted (positive = down in screen coords)
        return (
            total_x * self.multiplier,
            -total_y * self.multiplier,  # Invert Y for compensation
        )

    def get_cumulative_compensation(self) -> Tuple[float, float]:
        """
        Get cumulative recoil compensation (sum of all steps so far).

        This is useful for predicting where the spray will go.

        Returns:
            (total_x, total_y) cumulative offset
        """
        if not self._firing or not self.pattern:
            return (0.0, 0.0)

        elapsed_ms = (time.time() - self._shot_start_time) * 1000

        cumulative_time = 0.0
        total_x = 0.0
        total_y = 0.0

        for step in self.pattern:
            if elapsed_ms > cumulative_time:
                cumulative_time += step.duration_ms
                total_x += step.x
                total_y += step.y
            else:
                break

        return (
            total_x * self.multiplier,
            -total_y * self.multiplier,
        )

    def reset(self) -> None:
        """Reset the compensator state."""
        self._firing = False
        self._shot_start_time = 0.0


class RecoilManager:
    """
    Manages multiple weapon recoil patterns.

    Allows switching between weapons and loading patterns on demand.
    """

    def __init__(self, patterns_dir: str = "./patterns"):
        """
        Initialize the recoil manager.

        Args:
            patterns_dir: Directory containing pattern CSV files
        """
        self.patterns_dir = Path(patterns_dir)
        self.compensators: dict = {}
        self.active_weapon: Optional[str] = None
        self.multiplier: float = 1.0

    def load_pattern(self, weapon_name: str, csv_filename: str) -> None:
        """
        Load a recoil pattern for a weapon.

        Args:
            weapon_name: Name to identify this weapon
            csv_filename: CSV file name in patterns directory
        """
        csv_path = self.patterns_dir / csv_filename
        if csv_path.exists():
            self.compensators[weapon_name] = RecoilCompensator.from_csv(
                str(csv_path),
                self.multiplier,
            )

    def set_weapon(self, weapon_name: str) -> bool:
        """
        Set the active weapon.

        Args:
            weapon_name: Name of the weapon to activate

        Returns:
            True if weapon exists and was activated
        """
        if weapon_name in self.compensators:
            # Stop any active spray
            if self.active_weapon and self.active_weapon in self.compensators:
                self.compensators[self.active_weapon].stop_firing()

            self.active_weapon = weapon_name
            return True
        return False

    def start_firing(self) -> None:
        """Start tracking recoil for active weapon."""
        if self.active_weapon and self.active_weapon in self.compensators:
            self.compensators[self.active_weapon].start_firing()

    def stop_firing(self) -> None:
        """Stop tracking recoil."""
        if self.active_weapon and self.active_weapon in self.compensators:
            self.compensators[self.active_weapon].stop_firing()

    def get_compensation(self) -> Tuple[float, float]:
        """Get current compensation for active weapon."""
        if self.active_weapon and self.active_weapon in self.compensators:
            return self.compensators[self.active_weapon].get_compensation()
        return (0.0, 0.0)

    def set_multiplier(self, multiplier: float) -> None:
        """Set the compensation multiplier for all weapons."""
        self.multiplier = multiplier
        for comp in self.compensators.values():
            comp.multiplier = multiplier


# Default AK-47 pattern (from recoil.csv)
DEFAULT_AK47_PATTERN = [
    RecoilPattern(0, 0, 30),
    RecoilPattern(0, 0, 99),
    RecoilPattern(0.10497, -26.00426, 99),
    RecoilPattern(-2.49497, -29.9552, 99),
    RecoilPattern(-1.05429, -31.9007, 99),
    RecoilPattern(12.3244, -33.1178, 99),
    RecoilPattern(8.45939, -27.7364, 99),
    RecoilPattern(13.1337, -19.8188, 99),
    RecoilPattern(-16.9038, -15.1133, 99),
    RecoilPattern(-42.0762, 5.02222, 99),
    RecoilPattern(-23.1968, -9.1423, 99),
    RecoilPattern(13.4584, -7.82848, 99),
    RecoilPattern(-16.283, -1.73109, 99),
    RecoilPattern(-26.8526, 9.52371, 99),
    RecoilPattern(-2.44215, -5.35626, 99),
    RecoilPattern(37.232, -8.02386, 99),
    RecoilPattern(23.2809, -5.40851, 99),
    RecoilPattern(14.3236, -5.75076, 99),
    RecoilPattern(26.6208, 2.82855, 99),
    RecoilPattern(34.9165, 8.60448, 99),
    RecoilPattern(-19.1055, -5.58987, 99),
    RecoilPattern(5.08387, 0.156464, 99),
    RecoilPattern(-8.60053, -5.91907, 99),
    RecoilPattern(-9.06119, -2.09341, 99),
    RecoilPattern(20.3148, 2.80682, 99),
    RecoilPattern(6.87328, -5.38808, 99),
    RecoilPattern(-21.3522, -0.609879, 99),
    RecoilPattern(-33.0195, 2.71869, 99),
    RecoilPattern(-47.1704, 21.1572, 99),
    RecoilPattern(-14.4156, -0.197525, 109),
]


def create_ak47_compensator(multiplier: float = 1.0) -> RecoilCompensator:
    """test compensator with the default AK-47 pattern"""
    comp = RecoilCompensator(multiplier=multiplier)
    comp.pattern = DEFAULT_AK47_PATTERN.copy()
    return comp
