# Pilot E: Bounded Planning Under Proof Gate (v0.3.0)

## Objective
To demonstrate that the NeuraLogix reasoning engine can perform multi-step planning (search-over-futures) without compromising proof-gate integrity. We prove that a planner can act as a "proposer" of future states, while the engine remains the sole "judge" of validity.

## Domain: Gridworld Navigation
*   **World**: A 2D grid with fixed obstacles.
*   **Goal**: Reach a target coordinate `(x_g, y_g)` from a start coordinate `(x_s, y_s)`.
*   **Invariants**:
    *   No diagonal moves.
    *   No moves into obstacles.
    *   No moves out of bounds.
    *   State must match the physical world grid at every step.

## Requirements
### 1. Planning Agency
*   A deterministic planner (e.g., BFS or A*) proposes a sequence of operations.
*   The planner has no authority to commit changes; it only proposes `MOVE` operations.

### 2. Proof Gate
*   The reasoning engine must validate every proposed `MOVE` operation against the world invariants before updating the graph state.
*   Every validated step must generate a receipt.

### 3. Determinism & Audit
*   The sequence of proposed, accepted, and rejected steps must be 100% deterministic given a fixed world and seed.
*   The final audit trail must allow reconstruction of the entire goal-reaching path.

## Metrics & Success Gates
| Category | Metric | Target |
| :--- | :--- | :--- |
| **Safety** | Hallucination (Invalid Step Acceptance) | **0.0%** |
| **Logic** | Valid Proof for Every Step | **100%** |
| **Utility** | Success Rate (Solvable Tasks) | **>= 80%** |
| **Utility** | Abstention Rate (Unsolvable Tasks) | **>= 95%** |
| **Audit** | Deterministic Replay | **100.0%** |

## Deliverables
*   `neuralogix/pilots/pilot_e/world.py`: Gridworld state & invariants.
*   `neuralogix/pilots/pilot_e/ops.py`: Typed IR operations for movement.
*   `neuralogix/pilots/pilot_e/planner.py`: Search-based proposer.
*   `neuralogix/pilots/pilot_e/run.py`: Guided-Planning execution runner.
*   `tests/test_pilot_e.py`: Automated validation suite.
*   `results/pilot_e.json`: Summary metrics.
*   `results/pilot_e.evidence.jsonl`: Detailed receipt stream.
