"""
Target Selection and Prioritization module
"""

from dataclasses import dataclass
from math import sqrt
from typing import List, Dict, Any, Optional, Tuple

from config import AimConfig, CaptureRegion


@dataclass
class Target:
    """Represents a detected target."""
    # Class info
    class_name: str  # "c", "ch", "t", "th"
    class_id: int
    confidence: float

    # Bounding box (xyxy format)
    x1: float
    y1: float
    x2: float
    y2: float

    # Calculated aim point
    aim_x: float
    aim_y: float

    # Distance from crosshair (pixels)
    distance: float

    # Is it a head hitbox?
    is_head: bool

    @property
    def width(self) -> float:
        return self.x2 - self.x1

    @property
    def height(self) -> float:
        return self.y2 - self.y1

    @property
    def center(self) -> Tuple[float, float]:
        return (
            self.x1 + self.width / 2,
            self.y1 + self.height / 2,
        )

    @property
    def xyxy(self) -> Tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2, self.y2)


class TargetSelector:
    """
    Selects the best target from a list of detections.

    Priority can be configured to prefer:
    - Nearest target (default)
    - Head shots
    - Highest confidence
    """

    # Head class identifiers
    HEAD_CLASSES = {"ch", "th"}  # CT head, T head
    HEAD_CLASS_IDS = {1, 3}

    def __init__(self, aim_config: AimConfig, screen: CaptureRegion):
        """
        Initialize target selector.

        Args:
            aim_config: Aim configuration
            screen: Screen dimensions for center calculation
        """
        self.config = aim_config
        self.screen = screen
        self._center_x = screen.width / 2
        self._center_y = screen.height / 2

    def _is_enemy(self, class_name: str) -> bool:
        """Check if a class is an enemy based on current team."""
        return class_name in self.config.enemy_classes

    def _is_head(self, class_name: str) -> bool:
        """Check if a class is a head hitbox."""
        return class_name in self.HEAD_CLASSES

    def _calculate_aim_point(self, bbox: Dict[str, Any]) -> Tuple[float, float]:
        """
        Calculate the aim point for a bounding box.

        For heads: aim at center
        For bodies: aim at upper portion (towards head area)

        Args:
            bbox: Detection bounding box dict with 'xyxy' key

        Returns:
            (x, y) aim coordinates
        """
        x1, y1, x2, y2 = bbox["xyxy"]
        width = x2 - x1
        height = y2 - y1

        center_x = x1 + width / 2

        # For bodies, aim higher (towards head area)
        if bbox.get("tcls", bbox.get("cls_name", "")) not in self.HEAD_CLASSES:
            # Aim at upper 1/3 of body
            center_y = y1 + height / 3
        else:
            # For heads, aim at center
            center_y = y1 + height / 2

        return center_x, center_y

    def _calculate_distance(self, x: float, y: float) -> float:
        """Calculate distance from screen center."""
        return sqrt((x - self._center_x)**2 + (y - self._center_y)**2)

    def _bbox_to_target(self, bbox: Dict[str, Any]) -> Target:
        """Convert a detection bbox dict to a Target object."""
        x1, y1, x2, y2 = bbox["xyxy"]
        class_name = bbox.get("tcls", bbox.get("cls_name", "unknown"))
        class_id = int(bbox.get("cls", 0))

        aim_x, aim_y = self._calculate_aim_point(bbox)
        distance = self._calculate_distance(aim_x, aim_y)

        return Target(
            class_name=class_name,
            class_id=class_id,
            confidence=float(bbox.get("conf", 0.0)),
            x1=x1, y1=y1, x2=x2, y2=y2,
            aim_x=aim_x,
            aim_y=aim_y,
            distance=distance,
            is_head=self._is_head(class_name),
        )

    def filter_enemies(self, detections: Dict[str, List[Dict]]) -> List[Target]:
        """
        Filter detections to only include enemies.

        Args:
            detections: Dict of class_name -> list of detection dicts

        Returns:
            List of enemy Target objects
        """
        enemies = []

        for class_name, boxes in detections.items():
            if self._is_enemy(class_name):
                for bbox in boxes:
                    bbox_copy = bbox.copy()
                    bbox_copy["tcls"] = class_name
                    target = self._bbox_to_target(bbox_copy)
                    enemies.append(target)

        return enemies

    def select_best_target(
        self,
        detections: Dict[str, List[Dict]],
        max_distance: Optional[float] = None,
    ) -> Optional[Target]:
        """
        Select the best target from detections.

        Priority:
        1. Filter to enemies only
        2. Filter by max distance (if specified)
        3. If prioritize_heads: prefer heads within reasonable distance
        4. Select nearest target

        Args:
            detections: Dict of class_name -> list of detection dicts
            max_distance: Maximum distance from crosshair (pixels)

        Returns:
            Best Target or None if no valid targets
        """
        enemies = self.filter_enemies(detections)

        if not enemies:
            return None

        # Apply distance filter
        if max_distance is not None:
            enemies = [t for t in enemies if t.distance <= max_distance]

        if not enemies:
            return None

        # If prioritizing heads, check if any heads are close enough
        if self.config.prioritize_heads:
            heads = [t for t in enemies if t.is_head]

            if heads:
                # Get nearest head
                nearest_head = min(heads, key=lambda t: t.distance)
                nearest_body = min(enemies, key=lambda t: t.distance)

                # Prefer head if it's not too much further than nearest target
                # (within 1.5x the distance of nearest target)
                if nearest_head.distance <= nearest_body.distance * 1.5:
                    return nearest_head

        # Return nearest target
        return min(enemies, key=lambda t: t.distance)

    def select_all_sorted(
        self,
        detections: Dict[str, List[Dict]],
        max_distance: Optional[float] = None,
    ) -> List[Target]:
        """
        Get all enemy targets sorted by priority.

        Args:
            detections: Dict of class_name -> list of detection dicts
            max_distance: Maximum distance from crosshair (pixels)

        Returns:
            List of Targets sorted by priority (best first)
        """
        enemies = self.filter_enemies(detections)

        if max_distance is not None:
            enemies = [t for t in enemies if t.distance <= max_distance]

        # Sort by: heads first (if prioritized), then by distance
        def sort_key(t: Target) -> Tuple[int, float]:
            head_priority = 0 if (self.config.prioritize_heads and t.is_head) else 1
            return (head_priority, t.distance)

        return sorted(enemies, key=sort_key)

    def update_team(self) -> None:
        """Toggle the current team (called when team switch hotkey is pressed)."""
        from config import Team
        if self.config.current_team == Team.CT:
            self.config.current_team = Team.T
        else:
            self.config.current_team = Team.CT
