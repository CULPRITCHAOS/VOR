# NeuraLogix-Core — Milestone M8: Kill Tests Documentation

This document defines the 5 "Kill Tests" used to validate the core success criteria of the NeuraLogix system.

## Running the Benchmark
Execute the following command from the project root:
```powershell
python tools/killtests/run_all.py
```
Results will be displayed in the console and saved to `results/killtests/summary.json`.

---

## Experiment 1: Calibration/Abstention
**Objective**: Verify that the system correctly abstains when encountering OOD data.
- **Metric**: `abstention_triggered` (bool).
- **Success Criteria**: `abstention_level` is `SOFT_FAIL` or `HARD_FAIL` for OOD samples.

## Experiment 2: Collision vs Retrieval
**Objective**: Measure the capacity limits of the VQ codebook.
- **Metric**: `collision_rate`, `utilization`.
- **Success Criteria**: `utilization` > 50% for 50 samples on a 32-size book without catastrophic collapse.

## Experiment 3: Compositional Stability
**Objective**: Test if quantization error accumulates across a reasoning chain.
- **Metric**: `total_drift` (difference between initial and final error).
- **Success Criteria**: `total_drift` remains within the safety τ buffer over 3+ reasoning steps.

## Experiment 4: Overhead vs Throughput
**Objective**: Baseline the system performance.
- **Metric**: `ops_per_sec`, `latency_ms_per_op`.
- **Success Criteria**: > 10 ops/sec on toy hardware configurations.

## Experiment 5: Usability Harness
**Objective**: Measure the interpretation speed of human-writable inputs.
- **Metric**: `interpretation_latency_sec`, `parse_errors`.
- **Success Criteria**: Interpretation latency < 1.0s per session block.
