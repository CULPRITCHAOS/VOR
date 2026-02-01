from typing import Tuple

def manhattan_heuristic(pos: Tuple[int, int], goal: Tuple[int, int]) -> float:
    """
    Standard Manhattan distance heuristic for Gridworld.
    Used as a 'proposer' for A* search.
    """
    return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])

class LearnedProposer:
    """
    Wrapper for learned (or mock-learned) heuristics.
    In Pilot F, this is the component being 'improved' by learning,
    but it has no authority over the proof gate.
    """
    def __init__(self, mode: str = "manhattan"):
        self.mode = mode

    def estimate_cost_to_goal(self, current: Tuple[int, int], goal: Tuple[int, int]) -> float:
        if self.mode == "manhattan":
            return manhattan_heuristic(current, goal)
        return 0.0 # Default to BFS behavior (Dijkstra if edges weighted)
