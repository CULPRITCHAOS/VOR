# NeuraLogix-Core MVP — Implementation Plan

## Summary (one-page max)
NeuraLogix-Core is a discrete, auditable cognition runtime that converts inputs into a typed graph IR, optionally snaps representations onto a discrete codec, performs compositional reasoning, enforces checkers, and emits replayable receipts. The MVP intentionally targets a tiny domain (arithmetic + family relations) to validate the core loop: deterministic IR mutations, checker-driven validity/abstention, and receipt replayability. The system must remain deterministic, replayable, and scope-limited: no UI, no large training pipelines, no LLM replacement. Success is defined by replayable receipts, strong correctness on toy tasks, and 0% hallucination on closed-world unanswerable queries via abstention.

## Non-negotiable step loop
**Parse → Typed Graph IR → (Optional Codec) → Reason/Transform → Checkers → Receipt → (Answer | Abstain | Error)**

## Repo/module layout (authoritative)
```
neuralogix/
  core/
    ir/
      schema.py
      graph.py
    codec/
      base.py
      hdc.py
      vq.py
    checkers/
      base.py
      type_checker.py
      code_checker.py
      op_checker.py
      budget_checker.py
      consistency.py
    receipts/
      schema.py
      logger.py
      replayer.py
    reasoning/
      engine.py
      ops_arith.py
      ops_family.py
  tools/
    synth_data.py
    train_codec.py
    run_bench.py
    run_killtests.py
  tests/
```

## Interfaces (exact contract)
### Typed Graph IR
- **Schema**: versioned node/edge types for Number, Person, Relation, Operation, Boolean.
- **Graph**: stable node IDs, deterministic ordering for hashing, JSON serialization.
- **Mutations**: only via reasoning engine.

### Codec
- `Codec.encode(subgraph) -> CodeResult(code, score, residual, valid)`
- `Codec.decode(code) -> subgraph`
- **CodeResult** fields:
  - `code`: int ID or bitvector
  - `score`: quantization error / Hamming distance
  - `residual`: optional vector
  - `valid`: derived from budget thresholds

### Checkers
All checkers return structured outcomes:
- `OK`, `SOFT_FAIL`, `HARD_FAIL`, `ABSTAIN`

Required checkers:
- **Type checker**: validates operation argument/result types.
- **Code checker**: validates codec outputs against thresholds.
- **Op checker**: validates operation semantics (e.g., add correctness).
- **Budget checker**: enforces residual/quantization thresholds.
- **Consistency checker**: global invariants (e.g., no parent_of cycles).

### Receipts
- **Receipt event**: operation + inputs + output + checker results + decision.
- **Receipt logger**: append-only.
- **Replayer**: re-executes receipts to reconstruct IR and hash deterministically.

### Reasoning engine
- Applies a single operation/rule per step.
- Runs all checkers.
- Appends receipt.
- Returns Answer | Abstain | Error.

### Benchmark harness
- Runs query set (arithmetic + family).
- Collects answers + receipts + timing.
- Computes accuracy, abstention rate, and hallucinatory errors.

## Acceptance gates + MVP success criteria
**Global MVP gates**
1) 0% hallucination on closed-world unanswerable queries (must abstain).
2) Near-perfect accuracy on multi-step toy tasks.
3) Receipt replay deterministically reconstructs the same IR hash.
4) Receipts are human-readable and auditable.
5) Latency sanity (<0.5s/query on toy tasks).

## Kill tests (runnable scripts)
All kill tests are runnable via `tools/run_killtests.py` or individual scripts.
1) `killtest_calibration.py` — abstention calibration vs baseline (ECE, hallucination %, F1 with IDK).
2) `killtest_collision.py` — codec collision rate vs retrieval precision@k.
3) `killtest_compositional.py` — accuracy vs chain length, order invariance, invertibility.
4) `killtest_overhead.py` — throughput overhead with checkers/receipts on vs off.
5) `killtest_usability.py` — human-readable receipt comprehension/time/error.

## Staged milestones (M0–M8)
### M0 — Skeleton package + tests scaffold
**DoD**: repo structure + module stubs + pytest green.
**Tests added**: import smoke tests for all required modules.

### M1 — Typed Graph IR
**DoD**: graph storage + schema + JSON serialization; construct `3 + 5 -> 8` and `Alice parent_of Bob`.
**Tests added**: IR node/edge creation, serialization round-trip.

### M2 — Checkers v0
**DoD**: type checker + consistency rules; structured errors.
**Tests added**: type violations, cycle detection, checker outcome enums.

### M3 — Receipts v0 + Replayer
**DoD**: receipt schema/logger + replayer reconstructs IR with same hash.
**Tests added**: replay determinism tests.

### M4 — Reasoning engine v0
**DoD**: step loop with checkers + receipts; arithmetic + grandparent rule.
**Tests added**: arithmetic reasoning, family reasoning, receipt content.

### M5 — Codec interface + HDC backend
**DoD**: HDC encode/decode + code checker thresholds.
**Tests added**: encoding determinism, invalid code detection.

### M6 — VQ backend + synthetic data
**DoD**: synthetic data generator + VQ training script + per-type codebooks.
**Tests added**: training smoke test, quantization error stats.

### M7 — Residual budgets + budget checker
**DoD**: residual ε support, τ calibration, budget checker marks invalid/uncertain.
**Tests added**: off-manifold triggers and receipt annotations.

### M8 — Benchmark harness + baselines + kill tests
**DoD**: benchmark harness output metrics + runnable kill tests.
**Tests added**: benchmark smoke test + kill tests runner.

---

## M1 Completion Status (2026-01-21)

✅ **MILESTONE M1 COMPLETED**

### Deliverables Verified
1. ✅ Package configuration: `pyproject.toml` with pytest dependency
2. ✅ Deterministic canonical hashing: `TypedGraph.canonicalize()` and `TypedGraph.state_hash()`
3. ✅ JSON round-trip determinism: preserves graph semantics and hash
4. ✅ Comprehensive tests: 13 new tests covering examples, round-trips, determinism, and hash sensitivity

### Test Results
- **Total tests**: 20/20 passed
- **M0 tests**: 7 stub/import tests (from `test_skeleton_imports.py`)
- **M1 tests**: 13 new tests
  - `test_ir_examples.py`: 5 tests (arithmetic + family examples, round-trips, numeric types)
  - `test_ir_determinism.py`: 8 tests (insertion-order invariance, hash sensitivity)

### Reference Hashes (for regression testing)
**Arithmetic example** (`3 + 5 -> 8`):
```
ARITHMETIC_HASH=0257b4e8311568265fa35b61f560e
```

**Family example** (`Alice parent_of Bob`):
```
FAMILY_HASH=fdf2c431ac
```
*(Note: These hashes serve as regression checkpoints - any change to canonical form will break these)*

### Files Modified/Added
- **Added**: `pyproject.toml` - Package configuration
- **Modified**: `neuralogix/core/ir/graph.py` - Added `canonicalize()`, `state_hash()`, `__eq__()`, `__repr__()`
- **Added**: `tests/test_ir_examples.py` - Example validation tests
- **Added**: `tests/test_ir_determinism.py` - Determinism and sensitivity tests
- **Added**: `docs/DECISIONS.md` - Implementation decisions log

### Acceptance Gates Met
Per [spec line 107](file:///C:/Users/13cul/Desktop/Neuralogix%20H/NUERALOGIX-H/NeuraLogix_%20Architectural%20Specification.txt#L107):
- ✅ Can construct `3 + 5 -> 8` example
- ✅ Can construct `Alice parent_of Bob` example  
- ✅ Graph storage + schema + JSON serialization working
- ✅ Tests added: IR node/edge creation, serialization round-trip
- ✅ (Bonus) Canonical hashing for M3 receipt replay validation

---

## M2 Completion Status (2026-01-21)

✅ **MILESTONE M2 COMPLETED**

### Deliverables Verified
1. ✅ Checker framework: `CheckStatus`, `CheckIssue`, `CheckReport`, `combine_reports()`
2. ✅ TypeChecker: validates node types, edge types, and edge type constraints
3. ✅ ConsistencyChecker: detects parent_of cycles and spouse_of asymmetries
4. ✅ Public API: `validate(graph, checkers=None)` returns `(status, reports)`
5. ✅ JSON serialization: all reports convertible to dict for M3 receipts

### Test Results
- **Total tests**: 47/47 passed (20 M0+M1 + 27 M2)
- **M2 tests**: 27 new tests
  - `test_checkers_type.py`: 15 tests (valid graphs, invalid nodes/edges, determinism, serialization)
  - `test_checkers_consistency.py`: 12 tests (valid graphs, cycles, spouse symmetry, determinism)

### Invariants Checked
**TypeChecker**:
- Node types must be valid schema types (NUMBER, PERSON, RELATION, OPERATION, BOOLEAN)
- Edge types must be valid schema types
- Edge constraints enforced:
  - `parent_of`: PERSON → PERSON
  - `spouse_of`: PERSON → PERSON
  - `add`: NUMBER → NUMBER
  - `greater_than`: NUMBER → NUMBER

**ConsistencyChecker**:
- `parent_of` edges must be acyclic (HARD_FAIL on cycles)
- `spouse_of` edges must be symmetric (HARD_FAIL if A→B exists but not B→A)

### Files Modified/Added
- **Modified**: `neuralogix/core/checkers/base.py` - Checker framework with CheckStatus/CheckIssue/CheckReport
- **Modified**: `neuralogix/core/checkers/type_checker.py` - Type validation with edge constraints
- **Modified**: `neuralogix/core/checkers/consistency.py` - Cycle detection and symmetry checks
- **Modified**: `neuralogix/core/checkers/__init__.py` - Public `validate()` API
- **Added**: `tests/test_checkers_type.py` - 15 TypeChecker tests
- **Added**: `tests/test_checkers_consistency.py` - 12 ConsistencyChecker tests
- **Modified**: `docs/DECISIONS.md` - M2 decisions for HARD_FAIL policy and constraints

### Acceptance Gates Met
- ✅ Valid M1 examples validate OK
- ✅ Invalid node types trigger HARD_FAIL
- ✅ Invalid edge types trigger HARD_FAIL
- ✅ Edge type constraint violations trigger HARD_FAIL
- ✅ parent_of cycles trigger HARD_FAIL
- ✅ Validation is deterministic across insertion orders
- ✅ CheckReports are JSON-serializable


- ✅ CheckReports are JSON-serializable

---

## M3 Completion Status (2026-01-21)

✅ **MILESTONE M3 COMPLETED**

### Deliverables Verified
1. ✅ Receipt schema: `ReceiptEvent` with hash-chain and tamper evidence
2. ✅ Append-only logger: `ReceiptLogger` with JSONL storage
3. ✅ Deterministic replayer: `ReceiptReplayer` with tamper detection
4. ✅ Demo script: `tools/demo_receipts.py` showing end-to-end workflow
5. ✅ Comprehensive tests: 12 new tests for tamper evidence and replay determinism

### Test Results
- **Total tests**: 59/59 passed (20 M0+M1 + 27 M2 + 12 M3)
- **M3 tests**: 12 new tests
  - `test_receipts_hashchain.py`: 7 tests (tamper detection, hash integrity)
  - `test_receipts_replay_determinism.py`: 5 tests (deterministic replay, validation preservation)

### Receipt Schema
**ReceiptEvent fields**:
- `event_id`: UUID (globally unique)
- `timestamp`: ISO8601 UTC (\"2026-01-21T22:57:11.123456Z\")
- `actor`: \"system\" for MVP
-`op_name`: Operation name
- `inputs`, `outputs`: Node/edge IDs and values
- `checker_reports`: List of M2 CheckReport.to_dict()
- `status`: OK/SOFT_FAIL/HARD_FAIL/ABSTAIN
- `graph_hash_before`, `graph_hash_after`: 64-char SHA-256 hashes
- `prev_receipt_hash`: Previous receipt hash (or \"genesis\")
- `receipt_hash`: SHA-256 of canonical JSON (excluding this field)
- `notes`: Additional metadata dict

### Hash-Chain Integrity
**Properties**:
- First receipt: `prev_receipt_hash = \"genesis\"`
- Chain: Each receipt's `prev_receipt_hash` must match previous receipt's `receipt_hash`
- Tamper evidence: Any modification breaks hash verification

### Tam per Detection
**Test coverage**:
- ✅ Modify receipt line → TamperDetected
- ✅ Reorder receipts → TamperDetected (broken chain)
- ✅ Delete receipt → TamperDetected (broken chain)
- ✅ Invalid receipt_hash → ValueError in logger
- ✅ Broken prev_receipt_hash → ValueError in logger

### Deterministic Replay
**Verified**:
- ✅ Replay constructs same graph hash as original
- ✅ Multiple replays produce identical results
- ✅ Graph hash verification at each step
- ✅ Checker reports preserved in receipts
- ✅ Empty receipt log replays to empty graph

### Files Modified/Added
- **Added**: `neuralogix/core/receipts/schema.py` - ReceiptEvent with hash-chain
- **Modified**: `neuralogix/core/receipts/logger.py` - Append-only JSONL logger
- **Modified**: `neuralogix/core/receipts/replayer.py` - Deterministic replayer with tamper detection
- **Added**: `tests/test_receipts_hashchain.py` - 7 tamper evidence tests
- **Added**: `tests/test_receipts_replay_determinism.py` - 5 replay tests
- **Added**: `tools/demo_receipts.py` - Demo script
- **Modified**: `docs/DECISIONS.md` - M3 decisions for UUID/timestamps/JSONL

### Demo Script Output (Verified)
```
Phase 1: Building graph with receipt logging
  ✓ 5 receipts logged with hash-chain
Phase 2: Replaying from scratch
  ✓ Hash chain verified
  ✓ 5 operations replayed
Phase 3: Verification
  ✅ SUCCESS: Hashes match - deterministic replay verified!
```

### Acceptance Gates Met
Per [spec line 240](file:///C:/Users/13cul/Desktop/Neuralogix%20H/NUERALOGIX-H/NeuraLogix_%20Architectural%20Specification.txt#L240):
- ✅ Receipt schema + logger implemented
- ✅ Replayer rebuilds IR from receipts
- ✅ Replay yields same final IR state hash
- ✅ (Bonus) Tamper evidence via hash-chain
- ✅ (Bonus) Demo script validates end-to-end workflow

---

## M5: Codec Interface + HDC Backend (✅ COMPLETE - 2026-01-21)

**Status**: All deliverables met, 23 tests passing

### Core Deliverables

#### 1. Codec Interface (`neuralogix/core/codec/base.py`)
**Implementation**:
- `Codec` abstract base class with `encode()`, `decode()`, `similarity()` methods
- `CodeResult` dataclass: `code`, `score`, `valid_hint`, `metadata`
- JSON-serializable via `to_dict()` method (bytes → hex conversion)

**Properties**:
- Deterministic: same input → same output
- Serializable: all outputs JSON-compatible
- Validatable: provides quality metrics

#### 2. HDC Backend (`neuralogix/core/codec/hdc.py`)
**Implementation**:
- Fixed 256-bit binary hypervectors (default, configurable)
- **SHA256-based derivation**: No randomness, content-addressed only
  - Canonical JSON input (sorted keys)
  - Counter-based expansion for any dimension
  - Codebook caching for performance
- **Operations**:
  - `bind(hv_a, hv_b)`: XOR (invertible binding)
  - `bundle(hvs)`: Majority vote (similarity-preserving)
  - `similarity(hv_a, hv_b)`: Hamming similarity [0.0, 1.0]
- **Validity**: Similarity threshold (default 0.6) for `is_valid()` check

**Key Properties Verified**:
- ✅ Deterministic encoding (same target → same code)
- ✅ Insertion-order invariance (dict key order doesn't matter)
- ✅ XOR unbinding: `bind(bind(A, B), B) == A`
- ✅ Bind commutativity: `bind(A, B) == bind(B, A)`
- ✅ Bundle majority vote for 3+ hypervectors
- ✅ Hamming similarity identity: `sim(A, A) = 1.0`
- ✅ Similarity symmetry: `sim(A, B) == sim(B, A)`

#### 3. CodeChecker (`neuralogix/core/checkers/code_checker.py`)
**Implementation**:
- Validates `CodeResult.score` and `valid_hint`
- Returns `SOFT_FAIL` for invalid codes (non-blocking)
- Extensible for future codec distance validation

**Checks**:
- `valid_hint == False` → "INVALID_CODE_HINT"
- `score < min_score` → "LOW_CODE_SCORE"

### Test Coverage (23 tests, all passing)

#### Determinism Tests (3 tests)
- ✅ Same target → same code across calls
- ✅ Different targets → different codes
- ✅ Multiple codec instances → identical results (no random seeds)

#### Insertion-Order Invariance (2 tests)
- ✅ Dict with different key order → same code
- ✅ Nested dicts with reordered keys → same code

#### Validity Tests (4 tests)
- ✅ Identity (self-similarity) always valid
- ✅ Similar targets above threshold
- ✅ Very different targets below threshold
- ✅ Threshold boundary behavior correct

#### Bind/Bundle Tests (5 tests)
- ✅ XOR unbinding property: `bind(bind(A, B), B) == A`
- ✅ Bind commutativity: `bind(A, B) == bind(B, A)`
- ✅ Majority vote bundling produces similar result
- ✅ Bundle single item: `bundle([X]) == X`
- ✅ Bundle preserves dimension

#### Similarity Tests (3 tests)
- ✅ Similarity range [0.0, 1.0]
- ✅ Symmetry: `sim(A, B) == sim(B, A)`
- ✅ Identity: `sim(A, A) = 1.0`

#### JSON Serialization Tests (3 tests)
- ✅ `CodeResult.to_dict()` is JSON-serializable
- ✅ `code` bytes → hex string conversion
- ✅ Metadata includes `dimension` and `similarity_threshold`
- ✅ `valid_hint` deterministic for same target

#### Configuration Tests (3 tests)
- ✅ Custom dimension (512 bits)
- ✅ Custom similarity threshold (0.8)
- ✅ Default parameters (256 bits, 0.6 threshold)

### Files Modified/Added
- **Added**: `neuralogix/core/codec/base.py` - Codec interface + CodeResult
- **Added**: `neuralogix/core/codec/hdc.py` - HDC codec with SHA256 hypervectors
- **Modified**: `neuralogix/core/checkers/code_checker.py` - CodeResult validation
- **Added**: `tests/test_codec_hdc.py` - 23 comprehensive tests
- **Modified**: `docs/DECISIONS.md` - M5 design decisions

### Design Decisions Documented
- **Hypervector dimension**: 256 bits (configurable)
- **Similarity threshold**: 0.6 (configurable)
- **SHA256 derivation**: Content-addressed, no randomness
- **Bind operation**: XOR (invertible, commutative)
- **Bundle operation**: Majority vote (similarity-preserving)
- **Similarity metric**: Hamming distance (normalized to [0, 1])
- **JSON serialization**: bytes → hex string via `to_dict()`
- **CodeChecker**: SOFT_FAIL validation (non-blocking)

### Acceptance Gates Met
Per M5 specification:
- ✅ `Codec` interface with deterministic `encode()`, `decode()`, `similarity()`
- ✅ `CodeResult` dataclass with JSON serialization
- ✅ HDC backend with SHA256-based binary hypervectors
- ✅ `bind` (XOR) and `bundle` (majority) operations
- ✅ Validity rule based on similarity threshold
- ✅ CodeChecker stub for future integration
- ✅ Comprehensive tests (determinism, insertion-order, validity, ops, JSON)
- ✅ Documentation updated (DECISIONS.md)
