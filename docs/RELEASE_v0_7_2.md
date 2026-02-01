# NeuraLogix v0.7.2 Release Notes

## Overview
v0.7.2 fixes pack manifest integrity for legacy/stress packs to ensure fresh-clone audits pass.

## Fixes
- **Pack Integrity**: Standardized pack files (`.jsonl`) to LF line endings and added `.gitattributes` to enforce this across platforms. 
- **Manifests**: Updated all pack manifests with unified LF binary hashes.
- **Guardrail**: Added `tests/test_pack_integrity_guardrail.py` to prevent future manifest regressions.

## Installation
```bash
pip install -e .
```

## CLI Usage

### Run Grounded QA on a Pack
```bash
neuralogix qa --pack data/packs/public_demo_v0_7_1 --fast
```

### Run Full VOR Audit
```bash
neuralogix audit --fast
# or for full multi-seed certification:
neuralogix audit
```

### Validate Pack Integrity
```bash
neuralogix pack validate --pack data/packs/public_demo_v0_7_1
```

## HTTP Service (Local/Demo Only)

> [!WARNING]
> This service is **not production-hardened**. Use for local development and demos only.

```bash
neuralogix api serve --host 127.0.0.1 --port 8000
```

### Endpoints
- `GET /health` - Health check
- `POST /v1/qa/run` - Run QA (accepts JSON or ZIP upload)

## Outputs
All artifacts are written to `results/`:
- `vor_audit_summary.json` - VOR certification dashboard
- `pilot_i_*.summary.json` - Per-pack summaries
- `pilot_i_vor_*.evidence.jsonl` - Evidence receipts

## CI/CD Gates (v0.7.2)
| Gate | Blocking? | Threshold |
|------|-----------|-----------|
| Hallucination Rate | **YES** | Must be 0.0 |
| Parity Breach | **YES** | Must not occur |
| Conflict Precision/Recall | **YES** | ≥80% |
| Manifest Hash Mismatch | **YES** | Must match |
| Accuracy Dips | No (warn) | Reported only |
