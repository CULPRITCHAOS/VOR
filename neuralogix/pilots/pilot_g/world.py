import random
from typing import Tuple, List, Set, Dict, Optional
from ..pilot_e.world import GridWorld
from ..pilot_e.ops import MoveOp

class StochasticGridWorld(GridWorld):
    """
    A Gridworld where actions have stochastic outcomes (slips/stalls).
    Used for Pilot G to prove 'Observation-Driven Verification'.
    """
    def __init__(
        self, 
        size: Tuple[int, int], 
        obstacles: List[Tuple[int, int]], 
        start: Tuple[int, int], 
        goal: Tuple[int, int],
        p_success: float = 0.85,
        p_stall: float = 0.10,
        seed: Optional[int] = None
    ):
        super().__init__(size, obstacles, start, goal)
        self.p_success = p_success
        self.p_stall = p_stall
        self.p_slip = 1.0 - p_success - p_stall
        self.rng = random.Random(seed)

    def get_allowed_outcomes(self, pos: Tuple[int, int], op: MoveOp) -> Set[Tuple[int, int]]:
        """
        Returns the set of physically possible states given an action.
        In Pilot G, this includes:
        1. Intended target
        2. Current position (Stall)
        3. Adjacent lateral positions (Slip)
        All outcomes are filtered by obstacles and boundaries.
        """
        outcomes = {pos} # Stall is always allowed
        
        intended = op.apply(pos)
        if self.is_valid_move(pos, intended):
            outcomes.add(intended)
            
        # Lateral Slips
        # If MOVE is UP/DOWN, lateral is LEFT/RIGHT, and vice versa
        dx, dy = op.direction.value
        if dx != 0: # Horizontal MOVE
            laterals = [(0, 1), (0, -1)]
        else: # Vertical MOVE
            laterals = [(1, 0), (-1, 0)]
            
        for lx, ly in laterals:
            target = (pos[0] + lx, pos[1] + ly)
            if self.is_valid_move(pos, target):
                outcomes.add(target)
                
        return outcomes

    def step(self, op: MoveOp) -> Tuple[int, int]:
        """
        Executes the move stochastically.
        Returns the OBSERVED next state.
        """
        pos = self.current_pos
        roll = self.rng.random()
        
        allowed = self.get_allowed_outcomes(pos, op)
        intended = op.apply(pos)
        
        # 1. SUCCESS
        if roll < self.p_success and intended in allowed:
            self.current_pos = intended
        # 2. STALL
        elif roll < (self.p_success + self.p_stall):
            self.current_pos = pos
        # 3. SLIP (Randomly pick a lateral if available, else stay)
        else:
            slips = list(allowed - {pos, intended})
            if slips:
                self.current_pos = self.rng.choice(slips)
            else:
                self.current_pos = pos
                
        return self.current_pos

    def to_dict(self) -> Dict:
        d = super().to_dict()
        d.update({
            "p_success": self.p_success,
            "p_stall": self.p_stall,
            "p_slip": self.p_slip
        })
        return d
