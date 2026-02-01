# What We Now Know (v0.1 Retrospective)

**Date:** 2026-01-29
**Status:** Canonical Reference for v0.2 Development

## The Foundation (v0.1)
We have successfully implemented and verified three core pilots, establishing NeuraLogix as a system of **Honest Intelligence**.

### 1. Verifiable Code (Pilot A)
*   **Knowledge:** We can generate code that is guaranteed to match a specification if we treat the test suite as the ground truth.
*   **Mechanism:** `Spec` -> `Code` -> `Test` -> `ExecutionResult`.
*   **Key Insight:** The "Anti-Tautology Rule" is essential. A system cannot be trusted if it writes its own tests without independent verification (System Tests).

### 2. Grounded QA (Pilot B)
*   **Knowledge:** We can answer questions over large-scale knowledge bases with **0% hallucination**.
*   **Mechanism:** "Retriever as Proposer, Engine as Judge."
*   **Key Insight:** Strict Abstention is viable. By refusing to answer ambiguous (Conflict) or incomplete queries, we build trust. Indexing allows this to scale (10k+ facts) without relaxing proof obligations.

### 3. Reproducible Pipelines (Pilot C)
*   **Knowledge:** Logic and data transformations can be cryptographically bound to the environment.
*   **Mechanism:** `Input Hash` + `Env Hash` + `Code Hash` => `Output Hash`.
*   **Key Insight:** Determinism is not just about code; it's about the entire execution context.

## The Next Step (v0.2)
With Pilot D, we have proven that this foundation supports advanced cognition.

### 4. World Modeling (Pilot D)
*   **Knowledge:** We can learn latent structures and predict transitions without fabrication.
*   **Mechanism:** "Latent Proposal, Explicit Proof."
*   **Key Insight:** Predictive models are powerful proposers but must never be truth authorities.

## 🏁 The v0.1.0 Baseline
We have reached a stable, auditable baseline. The system is now frozen for v0.1.0, with all cognitive contracts enforced by the `neuralogix` verifier suite.

## 🔭 The v0.3 Frontier: Planning
With the foundation solid, v0.3 moves into **Bounded Planning**. We will prove that search-over-futures can remain verifiable by treating every planned step as a proposal that must pass the 0% hallucination proof gate.
 
## The Frontier (v0.4)
We have successfully transitioned from deterministic toy worlds to stochastic environments and multi-tool orchestration.

### 5. Stochastic Resilience (Pilot G)
*   **Knowledge**: Agency remains verifiable under uncertainty if the Engine shifts from "Checking exact prediction" to "Checking support set membership."
*   **Mechanism**: Propose -> Observe -> Verify -> Commit.
*   **Key Insight**: Stochastic outcomes do not weaken proof gates; they simply expand the valid target set.

### 6. Tool-Chain Verification (Pilot H)
*   **Knowledge**: Cognitive tools (retrievers, parsers) can be treated as observers governed by strict pre/post condition contracts.
*   **Mechanism**: Sequence Proof Gating.
*   **Key Insight**: A "Chain of Thought" only becomes a "Chain of Proof" when every tool link is verified by an independent guardian.

---

## The Scaling Frontier (v0.6)
High-integrity QA remains stable at N=500+ even with aliasing and paraphrasing.

## The Certification Frontier (v0.7)
We have successfully transitioned NeuraLogix into a **Verified Observation Runtime (VOR)**.

### 8. The VOR Category Proof
*   **Knowledge**: A reasoning engine can maintain 0% hallucination at scale in ambiguous environments if it treats tools as "Observers" and logic as "Authority".
*   **Mechanism**: Standardized **Corpus Packs** (Binary SHA256) + **Observations Hash** (Parity Verification).
*   **Key Insight**: Real-world "messiness" (ambiguity, near-miss distractors) is a retrieval/parsing problem. By isolating these as observations, the Truth Gate remains invariant and bulletproof.
*   **Normalization Laundering Guardrail (E2) Verified**: Exact numeric normalization prevents "$5M" from matching "$5K", and "$5,000,000" from matching "$5,000,001". Truth Gate returns CONFLICT when conflicting values are observed.
*   **Entity Disambiguation Policy**: ANSWER only when there is a single unambiguous grounded match; ABSTAIN when entity binding cannot be resolved with available observations. This policy is immutable — do not "optimize" into guessing.

*Verified by NeuraLogix v0.7.1 — V1 Contract Frozen.*

