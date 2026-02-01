from enum import Enum
from typing import Tuple, Dict, Any

class Direction(Enum):
    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class MoveOp:
    """
    Typed operation representing a discrete movement in the Gridworld.
    Used for proposal and proof-gating.
    """
    def __init__(self, direction: Direction):
        self.direction = direction

    def apply(self, current_pos: Tuple[int, int]) -> Tuple[int, int]:
        dx, dy = self.direction.value
        x, y = current_pos
        return (x + dx, y + dy)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "MOVE",
            "direction": self.direction.name,
            "vector": self.direction.value
        }

    def __repr__(self):
        return f"MoveOp({self.direction.name})"

class TransitionReceipt:
    """
    A cryptographic-style receipt for a validated transition.
    In Pilot E, this represents an accepted proposal.
    """
    def __init__(self, from_pos: Tuple[int, int], op: MoveOp, to_pos: Tuple[int, int], status: str = "ACCEPTED"):
        self.from_pos = from_pos
        self.op = op
        self.to_pos = to_pos
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_pos,
            "op": self.op.to_dict(),
            "to": self.to_pos,
            "status": self.status
        }
