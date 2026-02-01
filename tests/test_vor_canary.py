import pytest
import os
import shutil
from neuralogix.pilots.pilot_i.evaluate import PilotIEvaluator
from neuralogix.pilots.pilot_i.decisions import AlwaysAnswerBaseline

class SabotagedBaseline(AlwaysAnswerBaseline):
    """
    Induces a parity failure by behaving differently in retrieval if we could,
    but since the Runner handles retrieval, we'll patch the Runner's retriever 
    only during this strategy's turn in a custom evaluator.
    """
    pass

def test_vor_parity_canary():
    # 1. Setup minimal pack
    pack_dir = "data/packs/v0_6_legacy"
    if not os.path.exists(pack_dir):
        pytest.skip("v0_6_legacy pack not found")
        
    evaluator = PilotIEvaluator(pack_dir)
    
    # 2. Patch evaluate_strategy to sabotage the second strategy's observations
    original_evaluate = evaluator.evaluate_strategy
    
    def sabotaged_evaluate(strategy_class, name, evidence_path, fast=False, seed=42):
        metrics, results = original_evaluate(strategy_class, name, evidence_path, fast, seed)
        if "AlwaysAnswer" in name:
            # Sabotage the hash for the first result
            results[0]["obs_hash"] = "BEEF" * 16 
        return metrics, results

    evaluator.evaluate_strategy = sabotaged_evaluate
    
    # 3. Assert that run_all raises ValueError due to parity mismatch
    with pytest.raises(ValueError) as excinfo:
        evaluator.run_all(fast=True, seeds=[42])
        
    assert "CRITICAL PARITY FAILURE" in str(excinfo.value)
    print("\n✅ Canary Passed: Parity failure detected as expected.")

if __name__ == "__main__":
    test_vor_parity_canary()
