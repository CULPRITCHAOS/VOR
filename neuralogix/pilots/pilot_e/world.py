import numpy as np
from typing import Tuple, List, Set, Optional

class GridWorld:
    """
    A 2D deterministic world for Pilot E planning experiments.
    Invariants: No diagonal moves, no moving into obstacles, no moving out of bounds.
    """
    def __init__(self, size: Tuple[int, int], obstacles: List[Tuple[int, int]], start: Tuple[int, int], goal: Tuple[int, int]):
        self.width, self.height = size
        self.obstacles: Set[Tuple[int, int]] = set(obstacles)
        self.start = start
        self.goal = goal
        self.current_pos = start

        # Validate initialization
        self._validate_position(start, "Start")
        self._validate_position(goal, "Goal")

    def _validate_position(self, pos: Tuple[int, int], name: str = "Position"):
        x, y = pos
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise ValueError(f"{name} {pos} is out of bounds (0-{self.width-1}, 0-{self.height-1})")
        if pos in self.obstacles:
            raise ValueError(f"{name} {pos} is inside an obstacle")

    def is_valid_move(self, current: Tuple[int, int], target: Tuple[int, int]) -> bool:
        """
        Check if a move from current to target is valid.
        """
        cx, cy = current
        tx, ty = target

        # 1. Bounds check
        if not (0 <= tx < self.width and 0 <= ty < self.height):
            return False

        # 2. Obstacle check
        if target in self.obstacles:
            return False

        # 3. Adjacency check (No diagonals, step size exactly 1)
        dist = abs(cx - tx) + abs(cy - ty)
        if dist != 1:
            return False

        return True

    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        x, y = pos
        candidates = [(x+1, y), (x-1, y), (x, y+1), (x, y-1)]
        return [c for c in candidates if self.is_valid_move(pos, c)]

    def to_dict(self):
        return {
            "size": (self.width, self.height),
            "obstacles": list(self.obstacles),
            "start": self.start,
            "goal": self.goal,
            "current": self.current_pos
        }

    def __repr__(self):
        return f"GridWorld({self.width}x{self.height}, start={self.start}, goal={self.goal}, pos={self.current_pos})"
