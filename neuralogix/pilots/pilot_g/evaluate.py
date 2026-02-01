import json
from typing import List, Dict, Any
from .world import StochasticGridWorld
from .run import PilotGRunner

class PilotGEvaluator:
    """
    Measures Pilot G performance across varying degrees of uncertainty.
    """
    def __init__(self, seed: int = 42):
        self.seed = seed

    def run_batch(self, n_samples: int = 50, p_success_values: List[float] = [1.0, 0.85, 0.6, 0.4]):
        report = {
            "version": "0.4.1-cert",
            "results": {}
        }
        
        for p in p_success_values:
            print(f"📊 Evaluating Pilot G: P(success)={p}")
            stats = {
                "success_count": 0,
                "hallucination_count": 0, # Should be 0
                "total": n_samples,
                "p_success": p
            }
            
            for i in range(n_samples):
                # Using deterministic seed per sample for stability
                world = StochasticGridWorld(
                    size=(10, 10),
                    obstacles=[], # Keep simple for uncertainty testing
                    start=(0, 0),
                    goal=(9, 9),
                    p_success=p,
                    p_stall=(1.0 - p) * 0.7, # 70% of failures are stalls
                    seed=self.seed + i
                )
                runner = PilotGRunner(world)
                metrics = runner.execute_plan(max_steps=100) # Give more steps for slips
                
                if metrics["summary"]["success"]:
                    stats["success_count"] += 1
                
                # Verify 0.0% invalid through receipts
                for r in runner.receipts:
                    if "REJECTED" in r.status and "ImpossibleOutcome" in r.status:
                        stats["hallucination_count"] += 1
                        
            stats["success_rate"] = stats["success_count"] / n_samples
            report["results"][f"p_{p}"] = stats
            
        with open("results/pilot_g_batch.json", "w") as f:
            json.dump(report, f, indent=4)
            
        print(f"✅ Pilot G Evaluation Complete. SUCCESS RATE(p=0.85): {report['results']['p_0.85']['success_rate']:.1%}")
        return report

if __name__ == "__main__":
    evaluator = PilotGEvaluator()
    evaluator.run_batch()
