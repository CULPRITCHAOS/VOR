# NeuraLogix v0.3: Deep Intelligence via Planning

## Objective
Implement **Pilot E: Bounded Planning Under Proof Gate**. We aim to prove that a reasoning engine can perform multi-step search while maintaining strict 0% hallucination and proof-receipt integrity.

## Roadmap
1.  **Pilot E (Gridworld)**: Multi-step navigation with obstacles.
    *   Planner proposes a sequence.
    *   Proof Engine validates each transition against invariants.
2.  **Pilot F (Extension)**: Learned proposal generators for planning.

## v0.4 Roadmap: Uncertainty without Lies

The objective of v0.4 is to move beyond toy determinism and solve planning under stochasticity and toolchain complexity.

### Pilot G: Stochastic World Planning
**Goal:** Verifiable navigation in worlds with slip-probabilities or dynamic obstacles.
- **Invariant:** Proof gate still enforces hard safety (no out-of-bounds).
- **Metric:** Calibrated Abstention (know when proof is impossible).
- **Mechanism:** Contingency proposal (if A fails, do B) under proof-gate governance.

### Pilot H: Tool-Sequence Planning over TypedGraph IR
**Goal:** Solve the "Chain of Thought" problem by making it a "Chain of Proof."
- **Phase 1:** Planner searches sequences of tool operations (Retrievers, Parsers, Testers).
- **Phase 1.1:** Every "CoT" link is a proof-gated transition in the IR space.
- **Metric:** Artifact Verification (Did the plan produce a verified truth?).

---
*Roadmap drafted by Antigravity AI — NeuraLogix v0.3.1 Baseline.*
*   Success Rate (Solvable): **>= 80%**
*   Abstention Rate (Unsolvable): **>= 95%**
*   Deterministic Replay: **100%**

## Non-Negotiable Gates
*   Invalid Step Acceptance: **0.0%**
