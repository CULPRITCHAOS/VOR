# Pilot E: Bounded Planning - Status & Contracts

**Status:** ❄️ FROZEN (Stable Cognitive Contract)
**Version:** v0.3.0
**Last Verified:** 2026-01-30

## Overview
Pilot E proves that multi-step search (Planning) can be performed without compromising the 0% hallucination gate. It establishes the "Search as Proposal, Engine as Judge" pattern.

## What It Proves
1.  **Verifiable Agency:** A planner can propose complex future actions without having "write" authority.
2.  **Safety Enclosure:** Every transition is checked against world invariants (obstacles, bounds, adjacency).
3.  **Loop/Non-Progress Detection:** Valid but recursive steps are rejected to prevent infinite search cycles.
4.  **Deterministic Audit:** Planning receipts allow 100% reconstruction of the chosen path.

## Non-Negotiable Invariants (Guaranteed)
1.  **0.0% Invalid Step Acceptance:** No transition occurs if it violates a world invariant.
2.  **Proof-Gated Transitions:** Every accepted move creates a verifiable receipt.
3.  **Search Determinism:** Given a fixed world and seed, the plan is always identical.
4.  **Proposal Non-Authority:** The planner only suggests; the Proof Gate decides and commits.

## Non-Goals (v0.3.x)
*   **Stochasticity:** World transitions are strictly deterministic.
*   **Partial Observability:** The planner has a full view of the grid and obstacles.
*   **Learned Authority:** No neural component can commit a move without a proof gate.

## Batch Metrics (RC-v0.3.1 Hard-Mode)
| Metric | Threshold | Observed (Hard) | Pass/Fail |
| :--- | :--- | :--- | :--- |
| **Solvable Success** | >= 80% | **100.0%** | ✅ PASS |
| **Unsolvable Abstain** | >= 100% | **100.0%** | ✅ PASS |
| **Hallucination Rate**| 0.0% | **0.0%** | ✅ PASS |
| **Lying Heuristic Res.**| 0.0% Impact| **100% Res.** | ✅ PASS |

---
*Contract certified by Antigravity AI — NeuraLogix v0.3.0.*
