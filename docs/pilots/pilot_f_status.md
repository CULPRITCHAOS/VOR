# Pilot F: Learned Proposers - Status & Contracts

**Status:** ❄️ FROZEN (Stable Cognitive Contract)
**Version:** v0.3.1
**Last Verified:** 2026-01-30

## Overview
Pilot F proves that "Neural" or learned guidance (heuristics) can be safely integrated into a reasoning loop. It demonstrates significant efficiency gains (reduced node expansion) without compromising the truth-gate authority.

## What It Proves
1.  **Safe Heuristic Guidance:** A* search with Manhattan (or learned) heuristics guides the search efficiently while remaining strictly governed.
2.  **Ablation Resilience:** Even an adversarial "Lying Heuristic" (which actively misleads) cannot force the system to accept an invalid move.
3.  **Governance of Intuition:** Proves that "intuition" (learned proposals) can be treated as a purely advisory layer.

## Non-Negotiable Invariants
1.  **Proposal-Only Authority:** Heuristic values influence the *order* of search, never the *validity* of steps.
2.  **Deterministic Tie-breaking:** Maintains replayability even when heuristic scores are identical.
3.  **Ablation Stability:** Hallucination rate remains 0.0% regardless of heuristic quality or intent.

## Efficiency Gains (RC-v0.3.1)
| Scenario | Nodes Expanded (BFS) | Nodes Expanded (A*) | Reduction |
| :--- | :--- | :--- | :--- |
| 10x10 Random | ~50-80 | ~10-25 | ~70% |
| Trap Funnel | ~100+ | ~15-30 | ~80%+ |
| Structural Maze| Full Search | Directed Search | 50%+ |

---
*Contract certified by Antigravity AI — NeuraLogix v0.3.1.*
