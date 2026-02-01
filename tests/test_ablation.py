import pytest
import sys
import os

# Force local package resolution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import neuralogix
print(f"DEBUG: neuralogix file={neuralogix.__file__}")
from neuralogix.pilots.pilot_i.graph import TypedGraph
from neuralogix.pilots.pilot_i.evaluate import PilotIEvaluator
from neuralogix.pilots.pilot_i.decisions import TruthGateStrategy

def test_normalization_ablation():
    """
    Sanity Check 1: Confirm that normalization is necessary for high recall.
    We compare performance with and without normalization.
    """
    import os
    if os.path.exists("results/ablation_norm.jsonl"): os.remove("results/ablation_norm.jsonl")
    if os.path.exists("results/ablation_no_norm.jsonl"): os.remove("results/ablation_no_norm.jsonl")

    pack_path = "data/packs/adversarial_v1"
    evaluator = PilotIEvaluator(pack_path)
    
    # 1. Baseline: Normalization enabled
    metrics_norm, _ = evaluator.evaluate_strategy(TruthGateStrategy, "TruthGate", "results/ablation_norm.jsonl", fast=False)
    acc_norm = metrics_norm["metrics"]["answer_accuracy"]
    
    # 2. Ablation: Disable normalization
    def identity_normalize(val):
        return str(val).strip().lower()
    
    # Capture the original staticmethod from the class __dict__
    original_normalize = TypedGraph.__dict__['normalize_value']
    TypedGraph.normalize_value = staticmethod(identity_normalize)
    
    try:
        metrics_ablation, _ = evaluator.evaluate_strategy(TruthGateStrategy, "TruthGate_Ablated", "results/ablation_no_norm.jsonl", fast=False)
        acc_ablation = metrics_ablation["metrics"]["answer_accuracy"]
    finally:
        # Restore the original staticmethod
        TypedGraph.normalize_value = original_normalize
        
    print(f"\nAblation Results for {pack_path}:")
    print(f"  Metrics (Normalized): {metrics_norm['metrics']}")
    print(f"  Metrics (Ablated):    {metrics_ablation['metrics']}")
    
    # Validation: Accuracy must drop significantly if normalization matters
    assert acc_ablation < acc_norm, f"Ablation failure: Accuracy {acc_ablation:.2%} is not less than {acc_norm:.2%}"
    # Without normalization, hallucinations on numeric values like "$5M" vs "$5,000,000" should increase
    print(f"  Ablation shows normalization impact: acc dropped from {acc_norm:.2%} to {acc_ablation:.2%}")

if __name__ == "__main__":
    test_normalization_ablation()
