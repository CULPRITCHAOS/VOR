# NeuraLogix-Core Implementation Decisions

## M1 — Typed Graph IR

### Decision: Node ID Strategy (2026-01-21)
**Choice**: User-specified node IDs (current implementation)
**Rationale**: 
- The existing TypedGraph API accepts `node_id` as a parameter, allowing explicit control
- This provides flexibility for tests and user code to create meaningful IDs
- Canonical ordering is achieved by sorting nodes alphabetically by node_id
- Hash determinism is ensured through stable sorting in `to_json()` method

**Alternative considered**: Content-addressed IDs (`sha1(type + value)[:12]`)
**Why not chosen**: Would cause ID collisions for nodes with identical type+value; user control is more flexible

### Decision: Canonical Form Ordering
**Implementation**:
- Nodes: sorted alphabetically by `node_id`
- Edges: sorted by `(edge_type, source, target)` tuple
- JSON attributes: `sort_keys=True`, `separators=(',', ':')` for no whitespace variance

### Decision: Package Configuration
**Choice**: `pyproject.toml` as single source of truth
**Rationale**: Modern Python standard (PEP 517/518); no redundant requirements.txt
**Minimal M1 dependencies**: pytest only (no torch/numpy until M6)

## M2 — Checkers v0

### Decision: Cycle Detection Strategy (2026-01-21)
**Choice**: HARD_FAIL for parent_of cycles
**Rationale**:
- Cycles in parent_of represent logically impossible relationships (A cannot be ancestor of themselves)
- This is a structural invariant violation, not a soft constraint
- SOFT_FAIL is reserved for "suspicious but potentially valid" cases (not applicable for cycles)

**Alternative considered**: SOFT_FAIL with warning
**Why not chosen**: Cycles are categorically invalid, not just suspicious

### Decision: Spouse Symmetry Enforcement
**Choice**: HARD_FAIL for asymmetric spouse_of edges
**Rationale**:
- spouse_of is a symmetric relationship by definition
- Missing reverse edge indicates incomplete data or modeling error
- Prevents downstream logic errors in reasoning engine

### Decision: CheckReport Structure
**Design**: JSON-serializable with code, message, status, node_ids, edge_ids, details
**Rationale**:
- Enables receipt logging in M3 (checkers will be called during reasoning)
- Structured format supports programmatic analysis
- `details` dict allows codec distance metrics in M5+ without schema changes

### Decision: Edge Type Constraints
**Implementation**: Static mapping `EDGE_TYPE_CONSTRAINTS` in TypeChecker
**Rationale**:
- Explicit, auditable type rules
- Easy to extend for new edge types
- Violations caught deterministically before reasoning

**Current constraints**:
- `parent_of`: PERSON -> PERSON
- `spouse_of`: PERSON -> PERSON
- `add`: NUMBER -> NUMBER
- `greater_than`: NUMBER -> NUMBER

## M3 — Receipts v0 + Replayer

### Decision: Event ID Strategy (2026-01-21)
**Choice**: UUID (uuid.uuid4()) for event_id
**Rationale**:
- Globally unique without coordination
- No collision risk across multiple runtime instances
- Standard Python uuid module (no dependencies)
- 36-character string format

**Alternative considered**: Monotonic integers
**Why not chosen**: Requires coordination for uniqueness; UUIDs are simpler for MVP

### Decision: Timestamp Format
**Choice**: ISO8601 with UTC timezone (datetime.utcnow().isoformat() + "Z")
**Rationale**:
- Unambiguous, sortable, human-readable
- Standard format for audit logs
- Includes millisecond precision
- Explicit UTC marker ("Z" suffix)

**Example**: "2026-01-21T22:57:11.123456Z"

### Decision: Canonical JSON for Receipt Hashing
**Implementation**: `json.dumps(data, sort_keys=True, separators=(',', ':'))`
**Rationale**:
- `sort_keys=True`: Deterministic key ordering
- `separators=(',', ':')`: No whitespace variance
- Same rules as M1 `state_hash()` for consistency
- SHA-256 produces 64-character hex digest

### Decision: Hash Chain Bootstrap
**Choice**: "genesis" as prev_receipt_hash for first receipt
**Rationale**:
- Explicit marker for chain start
- Distinguishable from real hashes (not 64-char hex)
- Common pattern in blockchain/audit systems

### Decision: Receipt Storage Format
**Choice**: JSONL (one JSON object per line)
**Rationale**:
- Append-only friendly (no file rewrite needed)
- Streamable (can process line-by-line)
- Human-readable for debugging
- Simple parsing (one `json.loads()` per line)

**Alternative considered**: SQLite
**Why not chosen**: JSONL is simpler for MVP; SQLite adds dependency and complexity

### Decision: Tamper Detection Strategy
**Implementation**: Verify at multiple points
1. **Logger.append()**: Validates prev_receipt_hash and receipt_hash before writing
2. **Replayer.verify_chain()**: Validates entire chain without replay
3. **Replayer.replay()**: Validates chain + graph_hash_before/after during replay

**Failure modes**:
- **TamperDetected**: Hash chain or receipt hash invalid
- **ReplayMismatch**: Graph state doesn't match expected hashes

## M4 — Reasoning Engine v0

### Decision: Operation Registry Design (2026-01-21)
**Choice**: Explicit registry with type-checked pure functions
**Rationale**:
- Type safety: Each operation declares input/output NodeTypes
- Purity: Operations are deterministic, side-effect-free functions
- Replay safety: Only registered operations can be replayed
- Extensibility: New operations registered explicitly

**Built-in operations**:
- `add(NUMBER, NUMBER) -> NUMBER`
- `greater_than(NUMBER, NUMBER) -> BOOLEAN`
- `derive_grandparent(PERSON, PERSON) -> RELATION`

### Decision: Single-Step Execution
**Choice**: No loops, no search, no planning in M4
**Rationale**:
- Simplicity: One operation per `engine.step()` call
- Auditability: Each step logged as separate receipt
- Controllability: External orchestrator decides sequence
- Foundation for M5+: Search/planning built as higher-level layer

### Decision: Rollback on Validation Failure
**Choice**: HARD_FAIL or ABSTAIN → rollback graph to previous state
**Rationale**:
- **Conservative**: Don't commit invalid graph states
- **Deterministic**: Same inputs always produce same final graph
- **Receipt integrity**: Rollback logged in receipt notes
- **graph_hash_after**: Set to hash_before when rolled back

**Implementation**: `copy.deepcopy(graph)` beforeoperation for backup

### Decision: Operation Input Format
**Choice**: Dict with string keys for operation inputs
**Rationale**:
- Flexibility: Different operations need different inputs
- JSON-serializable: Can be logged in receipts
- Node references: Use node_id strings (not objects)
- Explicit result IDs: Caller can specify result node ID

**Example**:
```python
engine.step(graph, "add", {
    "a": "n1",           # source node ID
    "b": "n2",           # target node ID
    "result_id": "sum"  # optional result ID
})
```

### Decision: Checker Integration Point
**Choice**: Run all M2 checkers AFTER operation, BEFORE commit
**Rationale**:
- Validation: TypeChecker ensures operation output is well-typed
- Consistency: ConsistencyChecker detects cycles/violations
- Receipt logging: Checker reports included in receipt
- Rollback trigger: HARD_FAIL/ABSTAIN prevents invalid commits

## M5 — Codec Interface + HDC Backend

### Decision: Hypervector Dimension (2026-01-21)
**Choice**: Default 256 bits (32 bytes), configurable
**Rationale**:
- Sufficient for distinguishing small knowledge graphs without excessive storage
- Multiple of 8 for efficient byte-aligned operations
- Standard for binary HDC (common practice)
- Can be increased to 512/1024 for larger graphs if needed

**Implementation**: `HDCCodec(dimension=256)` parameter

### Decision: Similarity Threshold for Validity
**Choice**: Default 0.6 (60% Hamming similarity), configurable
**Rationale**:
- Balance between strictness and flexibility
- Binary hypervectors typically ~50% overlap for random codes
- >60% indicates structural similarity
- Can be tuned per deployment based on empirical data

**Implementation**: `HDCCodec(similarity_threshold=0.6)` parameter

### Decision: SHA256-Based Hypervector Derivation
**Choice**: Content-addressed via SHA256 hash (no randomness)
**Rationale**:
- **Determinism**: Same content always produces same hypervector
- **No seeds**: No random state to manage or serialize
- **Collision resistance**: SHA256 provides strong hash properties
- **Extensibility**: Counter-based expansion for any dimension

**Implementation**:
1. Canonicalize target to JSON (sorted keys, no whitespace)
2. Hash canonical string with SHA256 + counter
3. Expand to desired dimension by repeated hashing
4. Cache results in `_codebook` dict

**Example**:
```python
target = {"type": "PERSON", "id": "n1"}
canonical = '{"id":"n1","type":"PERSON"}'  # sorted keys
seed = canonical.encode('utf-8')
hv = sha256(seed + b'0')[:32]  # First 32 bytes for 256 bits
```

### Decision: Bind Operation (XOR)
**Choice**: Bitwise XOR for binding hypervectors
**Rationale**:
- **Invertible**: `bind(bind(A, B), B) == A` (unbinding property)
- **Commutative**: `bind(A, B) == bind(B, A)`
- **Fast**: Single bitwise operation
- **Standard**: Common HDC practice for role-filler binding

**Use case**: Binding relations to nodes (e.g., `parent_of ⊗ Alice`)

### Decision: Bundle Operation (Majority Vote)
**Choice**: Bit-level majority vote for bundling
**Rationale**:
- **Similarity preservation**: Result similar to all inputs
- **Commutative**: Order doesn't matter
- **Distributed representation**: Captures common patterns
- **Robust**: Works well for 3+ hypervectors

**Implementation**: For each bit position, take majority (>50%) across all inputs

**Use case**: Combining multiple similar entities (e.g., bundling all PERSON nodes)

### Decision: Similarity Metric (Hamming)
**Choice**: Hamming similarity = 1 - (hamming_distance / dimension)
**Rationale**:
- **Natural for binary**: Counts differing bits
- **Normalized**: Range [0.0, 1.0] for easy thresholds
- **Fast**: Single XOR + popcount
- **Symmetric**: `sim(A, B) == sim(B, A)`

**Properties**:
- Identity: `sim(A, A) = 1.0`
- Orthogonality: Random codes ≈ 0.5 similarity
- Validity: `sim(code, ref) >= threshold` → valid

### Decision: CodeResult JSON Serialization
**Choice**: `CodeResult.to_dict()` converts bytes → hex string
**Rationale**:
- **JSON compatibility**: bytes not JSON-serializable
- **Compactness**: Hex is 2× size of bytes (vs base64 3× overhead)
- **Readability**: Hex strings easy to inspect
- **Round-trip**: `bytes.fromhex()` for deserialization

**Format**:
```json
{
  "code": "a3f2c8...",  // hex-encoded hypervector
  "score": 1.0,
  "valid_hint": true,
  "metadata": {
    "dimension": 256,
    "similarity_threshold": 0.6,
    "num_ones": 128
  }
}
```

### Decision: CodeChecker Stub Design
**Choice**: Validate `CodeResult.score` and `valid_hint`, return SOFT_FAIL
**Rationale**:
- **M5 scope**: Basic validity checks only
- **Non-blocking**: SOFT_FAIL allows invalid codes with warnings
- **Extensible**: Future M6+ can add codec distance checks
- **Stub-friendly**: Doesn't require full reasoning integration

**Checks**:
- `valid_hint == False` → SOFT_FAIL with "INVALID_CODE_HINT"
- `score < min_score` → SOFT_FAIL with "LOW_CODE_SCORE"

## M6 — VQ Backend + Synthetic Data

### Decision: Synthetic Data Generation Strategy (2026-01-21)
**Choice**: Deterministic, seed-based procedural generation for arithmetic and family relations.
**Rationale**:
- **Reproducibility**: Fixed seed ensures training data is identical across runs.
- **Diversity**: Procedural logic covers edge cases (deep trees, large sums) better than static files.
- **Compactness**: No need to store large CSV/JSON datasets in the repo.

**Implementation**: `SyntheticDataGenerator(seed=42)`

### Decision: Per-Type VQ Codebooks
**Choice**: Separate codebook Tensors for each `NodeType`.
**Rationale**:
- **Avoid Collapse**: Prevents "PERSON" nodes from being quantized to "NUMBER" codes (semantic isolation).
- **Efficiency**: Smaller codebooks are faster to search (lower latency).
- **Granularity**: Allows different dimension/size configurations per type in the future.

**Implementation**: `self.codebooks = {NodeType.PERSON: Tensor, ...}`

### Decision: VQ Embedding Strategy
**Choice**: Initial implementation uses value mapping for numbers and hashing for attributes.
**Rationale**:
- **Numbers**: Mapping scalar to `vec[0]` provides a simple Euclidean distance metric that mirrors numerical difference.
- **Attributes**: JSON-stable hashing intermixed into a vector provides a pseudo-latent space for quantization without a full language model.
- **Future-proof**: Interface accepts any `torch.Tensor`, allowing real vision/language embeddings later.

### Decision: Training via K-Means
**Choice**: Initialize codebooks using K-Means clustering on synthetic embeddings.
**Rationale**:
- **Simplicity**: No need for complex backprop/loss functions in M6.
- **Stability**: Centroids naturally find the most frequent patterns in synthetic data.
- **Performance**: Extremely fast training on toy domains.

**Implementation**: `VQTrainer` with `torch.cdist` and assignment loop.
## M7 — Residual Budgets

### Decision: Budget Policy (OK/SOFT/HARD) (2026-01-22)
**Choice**: Three-tier threshold policy based on calibrated τ.
**Rationale**:
- **OK** (`error <= τ`): Representation is within known distribution.
- **SOFT_FAIL** (`τ < error <= 2τ`): Representation is slightly off-manifold; mark as uncertain.
- **HARD_FAIL** (`error > 2τ`): Clear OOD or invalid state; stop reasoning and rollback.

**Implementation**: `BudgetChecker` enforces this logic on `CodeResult` metrics.

### Decision: τ Calibration Strategy
**Choice**: Use 95th percentile of quantization errors from synthetic validation data.
**Rationale**:
- Data-driven: Captures the natural variance of the trained codebook.
- Robust: Prevents outliers in training from skewing the budget too much.
- Automated: `calibrate_budgets.py` computes these per-type for reproducible configs.

### Decision: CodeResult Residual Vector
**Choice**: Include full ε vector (`embedding - codeword`) in `CodeResult`.
**Rationale**:
- **Information Preservation**: Residuals allow for potentially reconstructing the original continuous input or refining the discrete code later.
- **Auditability**: Receipts can store the exact error vector for offline analysis.

### Decision: Integration with Reasoning Engine
**Choice**: Registry of default checkers now includes `BudgetChecker`.
**Rationale**:
- **Safety First**: Every reasoning step now automatically checks if its outputs are within the calibrated budget.
- **Replay**: Budget violations are recorded in receipts, ensuring the reason for any "ABSTAIN" or "HARD_FAIL" is audit-loggable.
