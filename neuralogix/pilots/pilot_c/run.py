"""Pilot C: Runner."""
import sys
import os
import json
from neuralogix.pilots.pilot_c.pipeline import ReproduciblePipeline

# Mock Data
DATA = [
    {"id": 1, "value": 10},
    {"id": 2, "value": 20},
    {"id": 3, "value": 30},
]

def run_pilot():
    print("🚀 Starting Pilot C: Reproducible Pipelines")

    receipt_file = "pilot_c_receipts.jsonl"
    if os.path.exists(receipt_file):
        os.remove(receipt_file)

    # Run 1
    print("\n▶️  Run 1 (Original)...")
    pipeline1 = ReproduciblePipeline(receipt_file)
    res1, env1, inp1, hash1 = pipeline1.run(DATA)
    print(f"   Result: {res1}")
    print(f"   Env Hash: {env1[:8]}")
    print(f"   Input Hash: {inp1[:8]}")
    print(f"   Final State Hash: {hash1[:8]}")

    # Run 2 (Replay)
    print("\n▶️  Run 2 (Replay Verification)...")
    # In a real replay, we would load receipts and verify step-by-step.
    # Here we re-run and compare final hashes (End-to-End Determinism).
    pipeline2 = ReproduciblePipeline("pilot_c_replay.jsonl") # Dummy log
    res2, env2, inp2, hash2 = pipeline2.run(DATA)
    print(f"   Result: {res2}")
    print(f"   Final State Hash: {hash2[:8]}")

    # Verification
    if res1 != res2:
        print("❌ DETERMINISM FAILURE: Results differ")
        return False

    if hash1 != hash2:
        print("❌ DETERMINISM FAILURE: State hashes differ")
        return False

    if env1 != env2:
        print("❌ ENVIRONMENT DRIFT: Env hashes differ (unexpected for same session)")
        return False

    print("\n✅ SUCCESS: Pipeline is deterministic and replayable.")
    return True

if __name__ == "__main__":
    success = run_pilot()
    sys.exit(0 if success else 1)
