# v0.4 Cognitive Contract: Stochastic Outcomes, Verified Support

**Status:** ❄️ FROZEN
**Version:** v0.4.1
**Context:** Transition from deterministic toy worlds to stochastic/real-world environments.

## The Principle: "Observation-Driven Verification"
In deterministic worlds (v0.3), the Engine predicts exactly what *will* happen. In stochastic worlds (v0.4), the Engine defines exactly what *is allowed* to happen.

### 1. The Proposer-Observer-Judge Loop
1.  **Propose**: Planner suggests an action $A$ from state $S$.
2.  **Observe**: World executes $A$ and returns an observed outcome $S'$.
3.  **Verify (Outcome Support)**: The Engine checks if $S' \in \text{AllowedOutcomes}(S, A)$.
4.  **Receipt**: If verified, a receipt is issued with state "OBSERVED". If not, the transition is aborted as a world-model violation.

### 2. The Honesty Rule (Abstention under Uncertainty)
The system must not claim a guaranteed path if the outcomes are stochastic and no contingency plan covers all high-probability failure states.
- **Calibrated Abstention**: If the probability of reaching the goal falls below a threshold $\tau$, the system must ABSTAIN unless a safe "Back-off" or "Retry" policy is proven.

### 3. Non-Negotiable Invariants
1.  **Impossible Outcome Rejection**: 0.0% acceptance of states that are not permitted by the world model (e.g., teleporting to an non-adjacent square during a SLIP).
2.  **Deterministic Verification**: Given $(S, A, S')$, the verification process must be 100% deterministic and reproducible.
3.  **No Ghost Commits**: No state transition is committed to the "Proven Graph" until the observation is verified.

---
*Contract drafted by Antigravity AI — NeuraLogix v0.4.0.*
