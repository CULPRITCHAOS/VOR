# Verified Observation Runtime (VOR)

The Verified Observation Runtime (VOR) is a cognitive architecture that enforces a strict separation between **Observation** (data gathered by tools) and **Decision** (actions or answers verified by proof).

## 1. Definition
VOR is an execution environment where every output must be grounded in a verified proof path. If the available observations do not strictly support a transition, the system must **ABSTAIN** or declare a **CONFLICT**.

## 2. Core Invariants
1.  **Observation ≠ Truth**: Tool outputs (retrieval chunks, parsed facts) are mere observations. They have no authority until verified against the contract.
2.  **Verification Authority**: Only the core Engine/Verifier has the authority to approve an answer. Proposers (LLMs, agents) cannot bypass this gate.
3.  **Auditability & Replay**: Every decision must produce a cryptographic receipt (Evidence Receipt) that allows an independent auditor to replay the exact observation set and verify the outcome.

## 3. What VOR is NOT
-   **Not a RAG system**: RAG systems often "reason over" text and can hallucinate. VOR requires a structured proof path.
-   **Not a Theorem Prover**: While VOR uses logic, it operates on stochastic/messy observations rather than axiomatized symbols.
-   **Not a Black-Box Agent**: VOR is transparent. Every "thought" is a verifiable link in a provenance chain.

## 4. The VOR Cycle
1.  **Observe**: Tools (Retriever, Parser) generate raw facts from the world.
2.  **Ground**: Facts are stored in a `TypedGraph` with strict normalization and source tracking.
3.  **Verify**: The Decision Strategy attempts to find a non-conflicting proof path.
4.  **Audit**: A JSONL receipt is emitted containing the decision, the values, and the hashes of the observations used.

---
*Certified by NeuraLogix v0.7 — Standardized Observation Interface.*
