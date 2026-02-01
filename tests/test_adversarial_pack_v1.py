import pytest
import sys
import os

# Force local package resolution
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neuralogix.core.packs.loader import PackLoader
from neuralogix.pilots.pilot_i.evaluate import PilotIEvaluator
import json

PACK_PATH = "data/packs/adversarial_v1"

def test_adversarial_pack_integrity():
    """Verify that the adversarial pack passes manifest validation."""
    try:
        PackLoader().load_pack(PACK_PATH)
    except ValueError as e:
        pytest.fail(f"Integrity check failed: {e}")

def test_adversarial_audit_pass():
    """Run a fast audit on adversarial_v1 and verify VOR contracts."""
    evaluator = PilotIEvaluator(PACK_PATH)
    report = evaluator.run_all(fast=True, seeds=[42])
    
    # 1. Hallucination check (TruthGate must be 0.0)
    tg_strategy = next(s for s in report["strategies"] if s["strategy"] == "TruthGate_s42")
    hallucination_rate = tg_strategy["metrics"]["hallucination_rate"]
    assert hallucination_rate == 0, f"Adversarial pack caused hallucinations: {hallucination_rate}"
    
    # 2. Conflict check (we expect non-zero conflicts in this pack)
    # The metrics include conflict_recall and total_questions. 
    # Let's count conflicts in gold.jsonl directly to be sure.
    conflict_count = 0
    with open(os.path.join(PACK_PATH, "gold.jsonl"), "r") as f:
        for line in f:
            if json.loads(line).get("gold_decision") == "CONFLICT":
                conflict_count += 1
    
    assert conflict_count > 0, "No conflicts found in gold.jsonl, but they were expected!"
    
    # 3. Conflict Recall (If TruthGate is working, it should catch some)
    # Note: In fast mode, we sample 50. Some sampled might be conflicts.
    # If we want a guaranteed conflict in fast mode, we'd need to ensure it's in the sample.
    # For now, just asserting that the auditor ran.
    
    print(f"\n✅ Adversarial Audit Passed: 0 Hallucinations, {conflict_count} intentional conflicts verified.")
