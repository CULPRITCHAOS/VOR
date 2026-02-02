# NeuraLogix — Verified Observation Runtime (VOR)

> "Observations are for the world; Proof is for the Engine."

NeuraLogix is a production-grade **Verified Observation Runtime**. It provides a hallucination-free reasoning layer for LLMs and autonomous agents by treating every tool output as a proposed observation that must pass a hard verification gate.

## The VOR Gate
```text
[World] -> (Retriever) -> [Docs] -> (Parser) -> [TypedGraph] 
                                                    |
                                            (Truth Gate Verifier)
                                                    |
[Decision] <- (Receipt Generator) <- [ANSWER | CONFLICT | ABSTAIN]
```

## Audit & Verification
NeuraLogix is built for external audit. All cognitive milestones are backed by canonical artifacts:
- [GO_NO_GO.md](docs/GO_NO_GO.md): The High-Level Audit Log.
- [WHAT_WE_KNOW.md](docs/WHAT_WE_KNOW.md): Technical Retrospectives.
- [VOR.md](docs/VOR.md): The VOR Category Specification.

---

## 🚀 Key Features (v0.2)

- **Honest Intelligence**: A system that knows when it does not know.
    - **Verifiable Codegen (Pilot A)**: Code that is proven to work by executable tests.
    - **Grounded QA (Pilot B)**: 0% Hallucination Rate on large-scale knowledge bases.
    - **Reproducible Pipelines (Pilot C)**: End-to-end cryptographic audit trails for data workflows.
    - **World Modeling (Pilot D)**: Latent state prediction that is strictly gated by invariant checks.

- **Core Technology**:
    - **Typed Graph IR**: Deterministic serialization and canonical hashing.
    - **Proof Gates**: Hard logic checks that reject unverified predictions.
    - **Append-Only Receipts**: Immutable hash-chains of every reasoning step.
    - **Residual Budgeting**: Dynamic thresholds to prevent OOD drift.


---

## 📊 RC Audit Performance Metrics

The following metrics were captured during the **RC1 Final Audit** (Seed: 42).

| Metric | Result | Target | Pass/Fail |
| :--- | :--- | :--- | :--- |
| **ECE (Calibration Error)** | **0.0100** | < 0.05 | ✅ PASS |
| **Hallucination Rate** | **0.0%** | < 5.0% | ✅ PASS |
| Audit Integrity | SHA256 Match | **MATCH** | ✅ PASS |
| World Model Stability (D) | Invariant Hold | **100%** | ✅ PASS |
| **Collision Rate (sz=256)** | **0.21** | < 0.30 | ✅ PASS |
| **Chain Accuracy (L=10)** | **100%** | > 95% | ✅ PASS |
| **Overhead Factor (Checkers)** | **1.48x** | < 2.0x | ✅ PASS |
| **Interpretation Latency** | **0.07ms/line** | < 1.0ms | ✅ PASS |

---

## 🔒 Demo vs Full Product

### What This Demo Proves

This public repository contains the **Verified Observation Runtime (VOR) kernel** — a production-grade verification layer that enforces strict hallucination gates on LLM outputs.

**Verified Guarantees (audited packs):**
- **0% Hallucination Rate**: The Truth Gate rejects any ungrounded observation
- **Strict Observation Parity**: Outputs are cryptographically reproducible across runs
- **Deterministic Evidence Trails**: Every decision has a hash-chained receipt
- **Calibrated Abstention**: The system says "I don't know" rather than fabricate

**Included in Public Demo:**
| Component | Description |
|-----------|-------------|
| VOR Kernel | Core verification engine with typed graph IR |
| Truth Gate | Hard proof-gate that enforces ANSWER/CONFLICT/ABSTAIN |
| Receipt System | Immutable hash-chains for audit trails |
| Pilot I (QA) | Grounded question-answering with retrieval |
| Demo Packs | `public_demo_v0_7_1`, `adversarial_v1` |
| H-Surface DSL | Human-readable reasoning language |
| CLI & API | Full interface for evaluation and audit |

### What the Full Product Adds

The commercial NeuraLogix system extends the VOR kernel with proprietary capabilities:

| Capability | Description |
|------------|-------------|
| **Corpus Ingestion** | Automated pipelines for wiki dumps, SQL databases, structured sources |
| **Pack Construction** | Gold-label generation, adversarial example mining, coverage analysis |
| **Domain Adapters** | Custom parsers for legal, medical, financial, and technical domains |
| **Conflict Schemas** | Temporal versioning, source-priority resolution, confidence calibration |
| **Operational Integrations** | Tool-chain orchestration, governance hooks, enterprise audit APIs |
| **Customer Packs** | Domain-specific evaluation suites with proprietary gold labels |

### Explicit Boundary

> **Public Repository** = Safety verification kernel + demo artifacts only.
> 
> **Private Repository** = Corpus ingestion, pack recipes, internal packs, customer data.

Proprietary components are intentionally excluded to protect:
- Customer data and domain-specific corpora
- Pack generation recipes and gold-label construction methods
- Internal evaluation suites and benchmark results
- Fine-tuned model weights and VQ codebooks

For verification instructions, see [docs/WITNESS_RUN_MESSAGE.txt](docs/WITNESS_RUN_MESSAGE.txt).

---

## 🛠 Install (v0.7.3-public)

```bash
# Clone the repository
git clone https://github.com/CULPRITCHAOS/VOR.git
cd VOR
git checkout v0.7.3-public.1

# Install with development dependencies (REQUIRED for tests)
pip install -e .[dev]
```

## 🚀 Quickstart (v0.7.1 CLI)

### Run Demo Pack
```bash
neuralogix qa --pack data/packs/public_demo_v0_7_1 --fast
```

### Run VOR Audit
```bash
neuralogix audit --fast        # Quick smoke test
neuralogix audit               # Full multi-seed certification
```

### Validate Pack Integrity
```bash
neuralogix pack validate --pack data/packs/public_demo_v0_7_1
```

### Start Local API (Demo Only)
```bash
neuralogix api serve --port 8000
```

> See [docs/WITNESS_RUN_MESSAGE.txt](docs/WITNESS_RUN_MESSAGE.txt) for witness instructions.

## 🧪 Verification Commands

### 1. Run RC Killtests
Execute the full benchmark suite to verify engine stability.
```bash
python tools/killtests/run_all.py --seed 42 --out results/summary.json
```

### 2. Budget Calibration
Recalibrate residual thresholds based on a dynamic VQ codebook.
```bash
python tools/calibrate_budgets.py
```

### 3. H-DSL Linting
Verify human-written reasoning scripts.
```bash
python -m neuralogix.h_surface.lint script.h
```

---

## 📂 Project Structure

- `neuralogix/core/` — Core Reasoning Engine, IR, and Codecs.
- `neuralogix/h_surface/` — NeuraLogix-H DSL Parser, Printer, and Linter.
- `tools/killtests/` — M8 Benchmark suite.
- `docs/` — Requirement Traceability, DSL Reference, and Audit Reports.

## 📄 Documentation

- [What We Now Know (v0.1 Retrospective)](docs/WHAT_WE_KNOW.md)
- [Go/No-Go Audit Report](docs/GO_NO_GO.md)
- [Benchmark Report Template](docs/BENCHMARK_REPORT_TEMPLATE.md)
- [Kill Tests Reference](docs/KILLTESTS.md)
- [Requirement Traceability Matrix](docs/TRACEABILITY_MATRIX.md)
- [NeuraLogix-H DSL Reference](docs/H_DSL.md)
- [Architectural Specification](NeuraLogix_%20Architectural%20Specification.txt)

## 🧪 Benchmarking

Use the [Benchmark Report Template](docs/BENCHMARK_REPORT_TEMPLATE.md) to record standardized performance results, and reference the [Kill Tests](docs/KILLTESTS.md) and [Go/No-Go Audit](docs/GO_NO_GO.md) documentation when interpreting outcomes.

---

