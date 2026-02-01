import json
import time
import os
from datetime import datetime
from typing import List, Dict, Any
from .world import GridWorld
from .ops import MoveOp, TransitionReceipt
from .planner import DeterministicPlanner

class ProofGatedRunner:
    """
    Consumes planner proposals and validates every step before execution.
    Generates deterministic receipts and metrics.
    """
    def __init__(self, world: GridWorld):
        self.world = world
        self.planner = DeterministicPlanner(world)
        self.receipts: List[TransitionReceipt] = []
        self.start_time = None

    def execute_plan(self) -> Dict[str, Any]:
        self.start_time = time.time()
        
        # 1. Propose
        proposal: List[MoveOp] = self.planner.propose_plan()
        
        # 2. Judge & Commit
        current_pos = self.world.start
        visited = {current_pos}
        valid_steps = 0
        invalid_steps = 0
        abort_reason = None
        
        for op in proposal:
            target = op.apply(current_pos)
            
            # THE PROOF GATE
            if self.world.is_valid_move(current_pos, target):
                # 2.1 Non-Progress Check (Adversarial Detection)
                if target in visited:
                    receipt = TransitionReceipt(current_pos, op, target, "REJECTED (Non-Progress/Loop)")
                    self.receipts.append(receipt)
                    abort_reason = "LOOP_DETECTED"
                    break
                
                # ACCEPTED
                receipt = TransitionReceipt(current_pos, op, target, "ACCEPTED")
                self.receipts.append(receipt)
                current_pos = target
                visited.add(target)
                self.world.current_pos = target
                valid_steps += 1
            else:
                # REJECTED (This should not happen with a perfect planner, but the gate must exist)
                receipt = TransitionReceipt(current_pos, op, target, "REJECTED (Invariant Violation)")
                self.receipts.append(receipt)
                invalid_steps += 1
                abort_reason = "INVARIANT_VIOLATION"
                break # Terminate on invalid step

        duration = time.time() - self.start_time
        success = (current_pos == self.world.goal)
        
        # 3. Report
        metrics = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "world": self.world.to_dict(),
            "summary": {
                "success": success,
                "steps_taken": valid_steps,
                "invalid_proposals": invalid_steps,
                "abort_reason": abort_reason,
                "duration_sec": duration,
                "hallucination_pct": (invalid_steps / len(proposal) * 100) if proposal else 0.0,
                "heuristic_mode": self.planner.proposer.mode,
                "nodes_expanded": self.planner.stats["nodes_expanded"]
            }
        }
        
        return metrics

    def save_results(self, json_path: str, jsonl_path: str, metrics: Dict[str, Any]):
        # Save Summary
        with open(json_path, 'w') as f:
            json.dump(metrics, f, indent=4)
        
        # Save Evidence (JSONL)
        with open(jsonl_path, 'w') as f:
            for r in self.receipts:
                f.write(json.dumps(r.to_dict()) + "\n")

def run_smoke_test():
    # Define a simple 5x5 world with one obstacle
    world = GridWorld(
        size=(5, 5),
        obstacles=[(2, 2)],
        start=(0, 0),
        goal=(4, 4)
    )
    
    runner = ProofGatedRunner(world)
    metrics = runner.execute_plan()
    
    # Ensure results directory exists
    os.makedirs("results", exist_ok=True)
    
    runner.save_results(
        json_path="results/pilot_e.json",
        jsonl_path="results/pilot_e.evidence.jsonl",
        metrics=metrics
    )
    
    print(f"Pilot E Run Complete: Success={metrics['summary']['success']}, Steps={metrics['summary']['steps_taken']}")
    return metrics

if __name__ == "__main__":
    run_smoke_test()
