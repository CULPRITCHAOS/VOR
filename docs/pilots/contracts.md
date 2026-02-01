# NeuraLogix Cognitive Contracts

These formal contracts define the non-negotiable behavior of the reasoning engine. Future pilots must adhere to these rules.

## 1. Proof Obligation
**Rule:** No answer without a valid graph path.
-   **Definition:** A "YES" decision must be accompanied by a sequence of valid IR operations (Receipts) that derive the answer from the initial state.
-   **Enforcement:** `AntiTautologyChecker` and `ReasoningEngine` validation.

## 2. Abstention Default
**Rule:** Default state is `ABSTAIN`.
-   **Definition:** If a proof cannot be constructed, or if the construction fails validation, the system must return `ABSTAIN` (or `None`).
-   **Prohibition:** Speculative generation or "guessing" is strictly forbidden.

## 3. Conflict Resolution
**Rule:** Divergence = `ABSTAIN`.
-   **Definition:** If multiple valid proof paths exist for a single query but yield different values (Divergence), the system must treat this as ambiguity and `ABSTAIN`.
-   **Invariant:** Ambiguity must never be collapsed into fabricated certainty.

## 4. Retriever Non-Authority
**Rule:** Retrieval is proposal only.
-   **Definition:** Learned components (Vector DB, ML Retrievers) can inject nodes/edges into the graph as candidates, but they cannot force a decision.
-   **Constraint:** The Proof Engine treats retrieved facts as untrusted until validated by graph traversal operations. Retrieval confidence scores are ignored for truth determination.
