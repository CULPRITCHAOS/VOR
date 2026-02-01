# Adversarial Pack `adversarial_v1`

## Overview
This pack is designed to stress-test the VOR (Verified Observation Runtime) kernel against common linguistic and semantic pitfalls.

## Scenario Coverage Checklist
- [x] **Entity Ambiguity**: "Paris" (City) vs "Paris" (Person). Forces disambiguation or ABSTAIN.
- [x] **Alias Chains**: NYC -> New York City. Tests multi-hop equivalence.
- [x] **Paraphrase**: Multiple docs with different wording for the same claim.
- [x] **Temporal Conflicts**: CEO changes over time. Tests time-scoping logic.
- [x] **Hard Conflicts**: Incompatible facts (e.g., budgets). Tests CONFLICT detection.
- [x] **Retrieval Traps**: Distractor docs with high lexical overlap. Tests sensitivity to context.

## How to Run Validation
Run these commands from the repository root:

```bash
# Validate manifest hashes
neuralogix pack validate --pack data/packs/adversarial_v1

# Run fast QA (N=148)
neuralogix qa --pack data/packs/adversarial_v1 --fast

# Run fast Audit
neuralogix audit --pack data/packs/adversarial_v1 --fast
```

## Gold/Provenance Construction
Gold decisions and provenance were manually defined in `scripts/generate_adversarial_v1.py`:
- **ANSWER**: Provenance includes specific supporting doc IDs.
- **ABSTAIN**: Given when evidence is missing or ambiguous.
- **CONFLICT**: Given when two sources provide incompatible facts for the same entity/attribute.
