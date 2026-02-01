import pytest
from typing import Tuple
from neuralogix.pilots.pilot_e.world import GridWorld
from neuralogix.pilots.pilot_e.planner import DeterministicPlanner
from neuralogix.pilots.pilot_e.run import ProofGatedRunner

def test_pilot_e_solvable():
    """Test standard solvable navigation."""
    world = GridWorld(
        size=(3, 3),
        obstacles=[(1, 1)],
        start=(0, 0),
        goal=(2, 2)
    )
    runner = ProofGatedRunner(world)
    metrics = runner.execute_plan()
    
    assert metrics["summary"]["success"] is True
    assert metrics["summary"]["steps_taken"] == 4  # Shortest path is (0,0)->(1,0)->(2,0)->(2,1)->(2,2) or similar
    assert metrics["summary"]["invalid_proposals"] == 0
    assert metrics["summary"]["hallucination_pct"] == 0.0

def test_pilot_e_unsolvable():
    """Test unsolvable (trapped) case."""
    world = GridWorld(
        size=(3, 3),
        obstacles=[(0, 1), (1, 0)], # Trapped at (0,0)
        start=(0, 0),
        goal=(2, 2)
    )
    runner = ProofGatedRunner(world)
    metrics = runner.execute_plan()
    
    assert metrics["summary"]["success"] is False
    assert metrics["summary"]["steps_taken"] == 0
    assert metrics["summary"]["invalid_proposals"] == 0 # Planner should propose nothing

def test_pilot_e_determinism():
    """Test that multiple runs produce identical receipts."""
    world_config = {
        "size": (5, 5),
        "obstacles": [(2, 2), (1, 2), (3, 2)],
        "start": (0, 0),
        "goal": (4, 4)
    }
    
    # Run 1
    w1 = GridWorld(**world_config)
    r1 = ProofGatedRunner(w1)
    m1 = r1.execute_plan()
    receipts1 = [r.to_dict() for r in r1.receipts]
    
    # Run 2
    w2 = GridWorld(**world_config)
    r2 = ProofGatedRunner(w2)
    m2 = r2.execute_plan()
    receipts2 = [r.to_dict() for r in r2.receipts]
    
    assert m1["summary"]["steps_taken"] == m2["summary"]["steps_taken"]
    assert receipts1 == receipts2

def test_pilot_e_proof_gate_rejection():
    """Test that the proof gate rejects an invalid proposal."""
    world = GridWorld(
        size=(3, 3),
        obstacles=[(1, 1)],
        start=(0, 0),
        goal=(2, 2)
    )
    runner = ProofGatedRunner(world)
    
    # Manually inject an invalid proposal (move into obstacle)
    from neuralogix.pilots.pilot_e.ops import MoveOp, Direction
    invalid_op = MoveOp(Direction.RIGHT) # (0,0) -> (1,0) - valid
    invalid_op_2 = MoveOp(Direction.UP)    # (1,0) -> (1,1) - INVALID (obstacle)
    
    # We bypass the planner
    runner.planner.propose_plan = lambda: [invalid_op, invalid_op_2]
    
    metrics = runner.execute_plan()
    
    assert metrics["summary"]["success"] is False
    assert metrics["summary"]["steps_taken"] == 1
    assert metrics["summary"]["invalid_proposals"] == 1
    assert metrics["summary"]["hallucination_pct"] == 50.0  # 1/2 invalid
    assert runner.receipts[1].status == "REJECTED (Invariant Violation)"

def test_pilot_e_non_progress():
    """Test detection of non-progress (legal moves that loop)."""
    world = GridWorld(
        size=(3, 3),
        obstacles=[],
        start=(0, 0),
        goal=(2, 2)
    )
    runner = ProofGatedRunner(world)
    
    # Manually inject a looping proposal (0,0)->(1,0)->(0,0)
    from neuralogix.pilots.pilot_e.ops import MoveOp, Direction
    op1 = MoveOp(Direction.RIGHT) # (0,0) -> (1,0)
    op2 = MoveOp(Direction.LEFT)  # (1,0) -> (0,0) - LOOP
    
    runner.planner.propose_plan = lambda: [op1, op2]
    
    metrics = runner.execute_plan()
    
    assert metrics["summary"]["success"] is False
    assert metrics["summary"]["steps_taken"] == 1
    assert metrics["summary"]["abort_reason"] == "LOOP_DETECTED"
    assert runner.receipts[1].status == "REJECTED (Non-Progress/Loop)"

def test_pilot_f_lying_heuristic():
    """Prove that a 'lying' heuristic can only slow search, not bypass the truth gate."""
    from neuralogix.pilots.pilot_e.heuristics import LearnedProposer
    
    # A heuristic that actively moves AWAY from the goal
    class LyingProposer(LearnedProposer):
        def estimate_cost_to_goal(self, current: Tuple[int, int], goal: Tuple[int, int]) -> float:
            # Reverse Manhattan: larger distance = 'better'
            dist = abs(current[0] - goal[0]) + abs(current[1] - goal[1])
            return -float(dist)
            
    world = GridWorld(size=(5, 5), obstacles=[], start=(0, 0), goal=(4, 4))
    
    # Inject the liar
    from neuralogix.pilots.pilot_e.planner import DeterministicPlanner
    planner = DeterministicPlanner(world, proposer=LyingProposer())
    runner = ProofGatedRunner(world)
    runner.planner = planner
    
    metrics = runner.execute_plan()
    
    # 1. Truth preserved (Success eventually if path exists, or abstains if blocked)
    # Since obstacles=[], it should eventually find the goal.
    assert metrics["summary"]["success"] is True
    
    # 2. Gate respected (0 hallucination)
    assert metrics["summary"]["hallucination_pct"] == 0.0
    
    # 3. Efficiency collapse (Should expand many more nodes than A*-Manhattan)
    # Manhattan A* would expand ~9-10 nodes for (0,0)->(4,4). 
    # Lying A* might expand almost the whole grid.
    print(f"Nodes expanded (Lying): {metrics['summary']['nodes_expanded']}")
    assert metrics["summary"]["nodes_expanded"] > 10 
