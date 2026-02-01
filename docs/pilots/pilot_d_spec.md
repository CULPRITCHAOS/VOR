# Pilot D: Structured World Modeling & Prediction

**Status:** 🧪 EXPLORATORY
**Dependencies:** Pilot B Contracts (Frozen)

## Objective
To demonstrate that NeuraLogix can learn and maintain a latent structure of the world to predict missing facts, while strictly obeying proof obligations and abstention rules.

## Core Thesis
> "I can predict X — but I will only assert X if I can prove it."

## Architecture: Latent Proposal, Explicit Proof
1.  **World Model (Learned):** A component that observes the graph and proposes "Next State" or "Missing Link" candidates.
    *   *Implementation:* Simple State Transition Matrix (Mocked or Learned).
2.  **Predictor (Proposer):** Converts latent state into concrete Graph Operations (`ADD_NODE`, `ADD_EDGE`) as *proposals*.
3.  **Proof Gate (Judge):** The Pilot B reasoning engine validation logic.
    *   *Constraint:* A prediction is accepted only if it satisfies a system invariant or consistency check (e.g., "Traffic Light must go Green -> Yellow").

## Scenario: Sequence Completion (Traffic Light)
*   **Facts:** `Light` is `Green` at `T=0`.
*   **Prediction:** What is `Light` at `T=1`?
*   **World Model:** Suggests `Yellow` with high confidence, `Red` with low confidence.
*   **Gate:**
    *   Invariant Rule: `Green -> Yellow` is valid. `Green -> Red` is invalid.
    *   If Model suggests `Yellow` -> Accepted.
    *   If Model suggests `Red` -> Rejected (Abstain/Correction).

## Success Criteria
1.  **Increased Recall:** Can answer "What comes next?" which static QA (Pilot B) cannot.
2.  **Safety:** Bad predictions (e.g., Green -> Red) are rejected by the Gate.
3.  **Auditability:** Prediction source is logged (`origin="prediction"`), and the validating invariant is cited in the receipt.

## Non-Goals
-   Generative text prediction (LLM style).
-   Probabilistic truth (e.g., "Probably Yellow"). It must be "Proven Yellow" by the invariant.
