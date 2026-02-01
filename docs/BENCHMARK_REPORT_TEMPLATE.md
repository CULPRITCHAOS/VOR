# NeuraLogix Benchmark Report Template

Use this report to capture standardized results for NeuraLogix performance runs. The goal is to keep benchmark evidence consistent, traceable, and easy to compare across releases.

## Runtime Configuration

- **Seed**:
- **Fast Mode**: (on/off)
- **Hardware**: (CPU/GPU model, RAM, OS)

## Kill Test Results (5 Experiments)

| Experiment | Key Metrics | Result | Target/Criteria | Pass/Notes |
| :--- | :--- | :--- | :--- | :--- |
| **1. Calibration/Abstention** | ECE, abstention level |  | < 0.05 ECE; OOD triggers SOFT/HARD |  |
| **2. Collision vs Retrieval** | collision rate, utilization |  | utilization > 50%; no collapse |  |
| **3. Compositional Stability** | total drift |  | drift within τ buffer |  |
| **4. Overhead vs Throughput** | ops/sec, latency |  | > 10 ops/sec; low latency |  |
| **5. Usability Harness** | interpretation latency, parse errors |  | < 1.0s/session; zero critical errors |  |

## Interpretation Guide

- **Calibration/Abstention**: Good results show low calibration error and reliable abstention on OOD inputs. Poor results indicate high ECE or failure to abstain.
- **Collision vs Retrieval**: Good results keep collision rates low while maintaining healthy codebook utilization. Poor results show high collisions or collapsed utilization.
- **Compositional Stability**: Good results keep total drift within the safety τ buffer across multi-step chains. Poor results exceed the buffer or show runaway drift.
- **Overhead vs Throughput**: Good results deliver stable ops/sec with modest latency overhead. Poor results indicate severe throughput drops or latency spikes.
- **Usability Harness**: Good results show fast interpretation and minimal parse errors. Poor results show slow parsing or frequent errors.
