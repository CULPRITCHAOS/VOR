# NeuraLogix RC Audit — Traceability Matrix

This document maps the core requirements (Spec/Audit Goals) to the corresponding files and verification tests.

| Requirement ID | Requirement Description | Implementation Flow (Files) | Verification (Tests/Tools) |
| :--- | :--- | :--- | :--- |
| **M7.1** | Residual Budgeting (τ) | `neuralogix/core/checkers/budget_checker.py` | `tests/test_budget_checker.py` |
| **M7.2** | Budget Calibration | `tools/calibrate_budgets.py` | `tests/test_determinism_rc.py` |
| **M7.3** | Budget Integration | `neuralogix/core/checkers/__init__.py` | `tests/test_m7_integration.py` |
| **M8.1** | OOD Detection (Killtest 1) | `tools/killtests/exp1_calibration.py` | `tools/killtests/run_all.py` |
| **M8.2** | Collision Robustness (Killtest 2) | `tools/killtests/exp2_collision.py` | `tools/killtests/run_all.py` |
| **M8.3** | Compositional Stability (Killtest 3) | `tools/killtests/exp3_composition.py` | `tools/killtests/run_all.py` |
| **M8.4** | Computational Overhead (Killtest 4) | `tools/killtests/exp4_overhead.py` | `tools/killtests/run_all.py` |
| **M8.5** | Usability/Latency (Killtest 5) | `tools/killtests/exp5_usability.py` | `tools/killtests/run_all.py` |
| **H.1** | DSL Parsing | `neuralogix/h_surface/parser.py` | `tests/test_hdsl_roundtrip.py` |
| **H.2** | DSL Printing | `neuralogix/h_surface/printer.py` | `tests/test_hdsl_roundtrip.py` |
| **H.3** | DSL Linting | `neuralogix/h_surface/lint.py` | `tests/test_h_surface.py` |
| **AUD.1** | Execution Determinism | `neuralogix/core/codec/vq_trainer.py` | `tests/test_determinism_rc.py` |
| **AUD.2** | Rollback Guardrails | `neuralogix/core/reasoning/engine.py` | `tests/test_determinism_rc.py` |
| **AUD.3** | Metric Transparency | `tools/killtests/run_all.py` | `results/killtests.sample.json` |

---

## Metric Targets vs Observed (RC)

| Metric | Target | RC Status | Evidence |
| :--- | :--- | :--- | :--- |
| ECE (Exp 1) | < 0.05 | 0.0032 | `summary.json` |
| Hallucination % | < 5% | 0.0% | `summary.json` |
| Chain Accuracy (L=3) | 100% | 100% | `summary.json` |
| Overhead Factor | < 2.0x | 1.1x | `summary.json` |
| DSL Round-trip | 100% | 100% | `test_hdsl_roundtrip.py` |
