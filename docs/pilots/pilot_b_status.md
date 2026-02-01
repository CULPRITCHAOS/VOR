# Pilot B: Grounded QA - Status & Contracts

**Status:** ❄️ FROZEN (Stable Cognitive Contract)
**Version:** v0.1.5
**Last Verified:** 2026-01-29

## Overview
Pilot B established the core "Honest under Uncertainty" capability of NeuraLogix. It proves that the system can reason over structured knowledge, scale to large graphs, and utilize learned retrieval without hallucinating.

## What It Proves
1.  **Grounded Truth:** Answers are only provided if a deterministic path exists in the Typed Graph IR.
2.  **Honest Abstention:** The system correctly returns `ABSTAIN` when data is missing, ambiguous, or conflicting.
3.  **Scale Safety:** Proof discipline holds firm even with 10,000+ entities and optimized O(1) indexing.
4.  **Retrieval Safety:** Learned retrievers act as "proposers" only; the proof engine filters out noise and hallucinations.

## Non-Goals
-   **Creative Writing:** Pilot B does not generate free-text explanations or summaries.
-   **Soft Reasoning:** It does not use probabilistic logic or "best guess" heuristics.
-   **Ambiguity Resolution:** It does not attempt to resolve conflicts (e.g., by source weighting); it simply detects them and abstains.

## Invariants (Guaranteed)
1.  **0% Hallucination Rate:** The system never invents facts not present in the IR.
2.  **Proof-Gated Answers:** Every `YES` decision is backed by a verifiable execution receipt chain.
3.  **Abstention on Conflict:** If valid proof paths diverge (different answers), the system strictly `ABSTAINS`.
4.  **Retriever Non-Authority:** Facts proposed by retrieval must pass type and graph validation; retrieval score never overrides graph truth.
