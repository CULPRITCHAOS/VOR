# Pilot C: Reproducible Pipeline Receipts

**Status:** 🚧 PLANNED
**Dependencies:** Pilot B Contracts

## Scope
Pilot C extends the receipt system to cover end-to-end data workflows (ETL + Reasoning). It aims to prove that a complex sequence of operations can be deterministically replayed and audited for environment drift.

## Objectives
1.  **Deterministic Replay:** Prove that `Input Hash + Environment Hash + Code Hash => Output Hash`.
2.  **Environment Fingerprinting:** Capture OS, Python version, and dependency state in the receipt chain.
3.  **Auditability:** Verify that a pipeline run from the past can be re-validated today (or flag why it cannot).

## Non-Goals
-   **New Reasoning:** Pilot C uses existing Pilot B reasoning logic; it does not add new cognitive capabilities.
-   **Big Data:** Focus is on logic reproducibility, not processing terabytes of data.

## Required Receipts
Pilot C introduces specific workflow markers:
-   `PipelineStart`: Captures `env_hash` (OS, Python, Deps) and `input_manifest_hash`.
-   `Step`: Standard operation receipts (as in Pilot A/B).
-   `PipelineEnd`: Captures `output_hash` and `final_status`.

## Failure Modes
-   **Drift:** If `env_hash` differs from the recorded receipt, replay should warn or fail (depending on strictness).
-   **Input Mismatch:** If `input_manifest_hash` differs, replay is impossible (invalidated).
-   **Non-Determinism:** If re-running the same inputs in the same env produces different outputs, the pilot fails.
