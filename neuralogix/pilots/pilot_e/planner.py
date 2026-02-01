import heapq
from typing import List, Tuple, Optional, Dict
from .world import GridWorld
from .ops import MoveOp, Direction
from .heuristics import LearnedProposer

class DeterministicPlanner:
    """
    An A*-based deterministic planner for GridWorld.
    Uses a LearnedProposer for heuristics but remains deterministic
    via fixed tie-breaking order.
    """
    def __init__(self, world: GridWorld, proposer: Optional[LearnedProposer] = None):
        self.world = world
        self.proposer = proposer or LearnedProposer(mode="manhattan")
        self.stats = {"nodes_expanded": 0}

    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[MoveOp]]:
        """
        A* search to find the shortest path.
        """
        self.stats["nodes_expanded"] = 0
        # Priority Queue stores: (f_score, tie_break, current_pos, path)
        tie_break = 0
        open_set = [(0, tie_break, start, [])]
        g_scores = {start: 0}
        
        while open_set:
            f, _, current, path = heapq.heappop(open_set)
            self.stats["nodes_expanded"] += 1

            if current == goal:
                return path

            for neighbor in self.world.get_neighbors(current):
                new_g = g_scores[current] + 1
                
                if neighbor not in g_scores or new_g < g_scores[neighbor]:
                    g_scores[neighbor] = new_g
                    h = self.proposer.estimate_cost_to_goal(neighbor, goal)
                    f_score = new_g + h
                    
                    # Calculate direction
                    dx = neighbor[0] - current[0]
                    dy = neighbor[1] - current[1]
                    
                    direction = None
                    for d in Direction:
                        if d.value == (dx, dy):
                            direction = d
                            break
                    
                    if direction:
                        tie_break += 1
                        new_path = path + [MoveOp(direction)]
                        heapq.heappush(open_set, (f_score, tie_break, neighbor, new_path))
        
        return None

    def propose_plan(self) -> List[MoveOp]:
        return self.find_path(self.world.current_pos, self.world.goal) or []
