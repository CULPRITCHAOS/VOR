import pytest
from neuralogix.pilots.pilot_g.world import StochasticGridWorld
from neuralogix.pilots.pilot_g.run import PilotGRunner
from neuralogix.pilots.pilot_e.ops import MoveOp, Direction

def test_pilot_g_slip_verification():
    """Verify that a slip is detected and accepted as a valid (but unintended) outcome."""
    # Force a stall/slip scenario by pinning the seed
    world = StochasticGridWorld(
        size=(5, 5),
        obstacles=[],
        start=(0, 0),
        goal=(4, 4),
        p_success=0.0, # Always slip or stall
        p_stall=1.0,   # Force always stall for this test case
        seed=42
    )
    runner = PilotGRunner(world)
    
    # MOVE RIGHT (0,0 -> 1,0) but world forces stall at (0,0)
    op = MoveOp(Direction.RIGHT)
    ok, status = runner.execute_step(op)
    
    assert ok is True
    assert status == "STALLED (VERIFIED)"
    assert world.current_pos == (0, 0)
    assert runner.receipts[0].status == "STALLED (VERIFIED)"

def test_pilot_g_integrity_violation():
    """Adversarial: Verify that if the world returns an impossible state, the runner rejects it."""
    world = StochasticGridWorld(
        size=(5, 5),
        obstacles=[],
        start=(0, 0),
        goal=(4, 4)
    )
    runner = PilotGRunner(world)
    
    # Force the world state to something impossible for MOVE RIGHT from (0,0)
    # Impossible state = (4,4) (Teleportation)
    world.step = lambda op: (4, 4)
    
    op = MoveOp(Direction.RIGHT)
    ok, status = runner.execute_step(op)
    
    assert ok is False
    assert "Unsupported outcome" in status
    assert runner.receipts[0].status == "REJECTED (Impossible Outcome)"

def test_pilot_g_end_to_end_unsolvable():
    """Verify that if the goal is enclosed, the runner eventually abstains (no plan)."""
    world = StochasticGridWorld(
        size=(3, 3),
        obstacles=[(1, 0), (0, 1)], # Enclosed at (0,0)
        start=(0, 0),
        goal=(2, 2)
    )
    runner = PilotGRunner(world)
    metrics = runner.execute_plan()
    
    assert metrics["summary"]["success"] is False
    assert metrics["summary"]["abort_reason"] == "NO_PLAN_AVAILABLE"
