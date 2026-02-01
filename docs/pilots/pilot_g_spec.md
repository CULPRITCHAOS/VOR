# Pilot G: Stochastic World Planning (v0.4.1)

**Status:** 🛠️ IN-DESIGN
**Goal:** Prove that the reasoning engine can govern agents in uncertain environments without losing its "Proof Gate" integrity.

## 1. Domain: Stochastic Gridworld
A standard 2D Gridworld where moves are non-deterministic.
- **Action**: `MOVE(direction)`
- **Outcomes**:
    - **SUCCESS** (p=0.85): Agent moves to target square.
    - **STALL** (p=0.10): Agent stays in the current square.
    - **SLIP** (p=0.05): Agent moves to an adjacent square *not* in the intended direction (lateral slip).
- **Invariants**:
    - Agent cannot move into an obstacle regardless of outcome.
    - Agent cannot exit the grid boundaries.

## 2. Mechanism: Verify Outcome Support
The Proof Gate no longer checks a *single* predicted state. Instead, it checks if the *observed* state is supported by the physics of the world.

### Flow:
1.  Planner proposes `MoveOp(UP)`.
2.  World (Simulator) rolls dice -> `new_pos = (x, y+1)`.
3.  Engine verifies: `(x, y+1)` is a valid outcome for `(x, y) + UP`.
4.  Receipt: `ACCEPTED (STATUS: OBSERVED)`.

## 3. Success Metrics
1.  **Invalid Outcome Acceptance**: **0.0%** (Gate).
2.  **Safety Integrity**: 0.0% collisions even if slipping.
3.  **Abstention Calibration**: System should correctly report failure to guarantee goal-reach if slip probabilities are too high.

---
*Spec drafted by Antigravity AI — NeuraLogix v0.4.1.*
