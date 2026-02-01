import pytest
import os
from neuralogix.pilots.pilot_i.evaluate import PilotIEvaluator

def test_adversarial_v1_non_zero_abstention():
    """Fail if adversarial_v1 results in 100% abstention (trap for primitive parsers)."""
    pack_path = "data/packs/adversarial_v1"
    if not os.path.exists(pack_path):
        pytest.skip("adversarial_v1 pack not found")
        
    evaluator = PilotIEvaluator(pack_path)
    # Use TruthGate strategy (strategy[0] in run_all)
    report = evaluator.run_all(fast=True, seeds=[42])
    
    # Check the first strategy (usually TruthGate)
    tg_metrics = report["strategies"][0]["metrics"]
    
    # We expect some answers now with the new parser
    # Hallucination MUST stay 0.0
    assert tg_metrics["hallucination_rate"] == 0.0
    
    # False abstain rate should be < 1.0 (meaning we answered SOMETHING)
    assert tg_metrics["false_abstain_rate"] < 1.0, "100% abstention detected on adversarial_v1"
    
    # Answer accuracy should be > 0
    assert tg_metrics["answer_accuracy"] > 0, "0% answer accuracy on adversarial_v1"

def test_demo_pack_recall_floor():
    """Fail if demo pack recall drops below 75%."""
    pack_path = "data/packs/public_demo_v0_7_1"
    if not os.path.exists(pack_path):
        pytest.skip("demo pack not found")
        
    evaluator = PilotIEvaluator(pack_path)
    report = evaluator.run_all(fast=True, seeds=[42])
    
    tg_metrics = report["strategies"][0]["metrics"]
    
    # Hallucination MUST stay 0.0
    assert tg_metrics["hallucination_rate"] == 0.0
    
    # Recall floor check (Accuracy)
    # The user asked for "missed > 25% triggers FAIL", so Accuracy >= 75%
    assert tg_metrics["answer_accuracy"] >= 0.75, f"Demo pack recall dropped below floor: {tg_metrics['answer_accuracy']}"
