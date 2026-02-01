# Public vs Private Repository Split Plan

> Version: v0.7.3 | Status: PLAN ONLY (no split implemented)

## Overview

This document defines the boundary between public and private components of the NeuraLogix VOR system. The goal is to publish a verifiable safety kernel while protecting proprietary corpora, pack construction recipes, and internal evaluation suites.

---

## Repository Structure After Split

### Public Repository: `neuralogix-vor-public`
**Purpose**: Open-source VOR kernel for verification, demonstration, and academic review.

| Component | Path | Status |
|-----------|------|--------|
| VOR Kernel | `neuralogix/core/` | ✅ PUBLIC |
| Typed Graph IR | `neuralogix/core/ir/` | ✅ PUBLIC |
| Proof Gates | `neuralogix/core/checkers/` | ✅ PUBLIC |
| Receipt System | `neuralogix/core/receipts/` | ✅ PUBLIC |
| CLI Interface | `neuralogix/cli/` | ✅ PUBLIC |
| API Server (demo) | `neuralogix/api/` | ✅ PUBLIC |
| Pilot I (QA Kernel) | `neuralogix/pilots/pilot_i/` | ✅ PUBLIC |
| H-Surface DSL | `neuralogix/h_surface/` | ✅ PUBLIC |
| Public Demo Pack | `data/packs/public_demo_v0_7_1/` | ✅ PUBLIC |
| Adversarial Test Pack | `data/packs/adversarial_v1/` | ✅ PUBLIC |
| Test Suite (non-legacy) | `tests/` (excluding `tests/legacy/`) | ✅ PUBLIC |
| Documentation | `docs/` (public-facing) | ✅ PUBLIC |
| Witness Instructions | `docs/WITNESS_RUN_MESSAGE.txt` | ✅ PUBLIC |

### Private Repository: `neuralogix-internal`
**Purpose**: Proprietary components, customer data, and internal tooling.

| Component | Path | Status |
|-----------|------|--------|
| Pilot A-H | `neuralogix/pilots/pilot_a-h/` | 🔒 PRIVATE |
| Internal Packs | `data/packs/internal_*` | 🔒 PRIVATE |
| Real Corpora | `data/packs/real_r1/`, `wiki_*/` | 🔒 PRIVATE |
| Pack Generation Scripts | `scripts/generate_*.py` | 🔒 PRIVATE |
| Gold Label Construction | `tools/pack_builder/` | 🔒 PRIVATE |
| Customer Packs | `data/packs/customer_*/` | 🔒 PRIVATE |
| Internal Docs | `docs/internal/`, `docs/PACK_*_PLAN.md` | 🔒 PRIVATE |
| Legacy Tests | `tests/legacy/` | 🔒 PRIVATE |
| Benchmark Results (internal) | `results/` | 🔒 PRIVATE |
| VQ Codebooks (trained) | `artifacts/`, `models/` | 🔒 PRIVATE |

---

## Do Not Leak Checklist

Before any public push, verify these items are NOT included:

### ❌ Data Artifacts
- [ ] `data/packs/real_*/` — Real corpus packs
- [ ] `data/packs/wiki_*/` — Wikipedia-derived packs
- [ ] `data/packs/customer_*/` — Customer-specific packs
- [ ] `data/packs/internal_*/` — Internal evaluation packs
- [ ] `*.gold.jsonl` with proprietary annotations
- [ ] Any pack with `"source": "internal"` or `"source": "customer"` in manifest

### ❌ Scripts & Tooling
- [ ] `scripts/generate_*.py` — Pack generation recipes
- [ ] `tools/pack_builder/` — Gold label construction
- [ ] `tools/corpus_ingest/` — Ingestion pipelines
- [ ] Any script referencing SQL dumps, wiki exports, or customer APIs

### ❌ Documentation
- [ ] `docs/internal/` — Internal planning docs
- [ ] `docs/PACK_*_PLAN.md` — Pack construction plans
- [ ] Any doc mentioning customer names or internal project codenames
- [ ] Benchmark results showing internal pack performance

### ❌ Model Artifacts
- [ ] `artifacts/` — Trained VQ codebooks
- [ ] `models/` — Any fine-tuned weights
- [ ] `*.pt`, `*.bin` files not explicitly marked public

### ❌ Results & Evidence
- [ ] `results/` — Internal audit results
- [ ] `*.evidence.jsonl` from internal packs
- [ ] Logs containing internal corpus samples

---

## Git Filter-Repo Split Method

### Prerequisites
```bash
pip install git-filter-repo
```

### Dry-Run Procedure

1. **Create a working copy** (never operate on the original):
   ```bash
   git clone --mirror <internal-repo-url> temp-split
   cd temp-split
   ```

2. **Generate removal list** (paths to exclude from public):
   ```bash
   cat > paths-to-remove.txt << 'EOF'
   data/packs/real_r1/
   data/packs/wiki_*/
   data/packs/customer_*/
   data/packs/internal_*/
   scripts/generate_*.py
   tools/pack_builder/
   tools/corpus_ingest/
   docs/internal/
   docs/PACK_*_PLAN.md
   results/
   artifacts/
   models/
   tests/legacy/
   neuralogix/pilots/pilot_a/
   neuralogix/pilots/pilot_b/
   neuralogix/pilots/pilot_c/
   neuralogix/pilots/pilot_d/
   neuralogix/pilots/pilot_e/
   neuralogix/pilots/pilot_f/
   neuralogix/pilots/pilot_g/
   neuralogix/pilots/pilot_h/
   EOF
   ```

3. **Dry-run filter** (preview what would be removed):
   ```bash
   git filter-repo --paths-from-file paths-to-remove.txt --invert-paths --dry-run
   ```

4. **Review removal summary**:
   - Confirm no public files are being removed
   - Confirm all private paths are in the removal list

5. **Execute filter** (after dry-run approval):
   ```bash
   git filter-repo --paths-from-file paths-to-remove.txt --invert-paths --force
   ```

6. **Verify public repo**:
   ```bash
   # Should NOT contain any private paths
   find . -path "*/pilot_a/*" -o -path "*/real_r1/*" -o -path "*/internal/*"
   
   # Should still work
   pip install -e .[dev]
   pytest
   neuralogix audit --fast
   ```

7. **Push to public remote**:
   ```bash
   git remote add public <public-repo-url>
   git push public --all
   git push public --tags
   ```

---

## Pre-Split Verification Checklist

Before executing the split:

- [ ] All private paths listed in `paths-to-remove.txt`
- [ ] Dry-run produces expected output
- [ ] Public demo pack still validates after filter
- [ ] pytest passes after filter
- [ ] audit --fast passes after filter
- [ ] No private data appears in git log --all --full-history
- [ ] No API keys, credentials, or internal URLs in code
- [ ] README updated to reflect public-only scope

---

## Post-Split Maintenance

### Public Repo Updates
- Cherry-pick kernel improvements from internal repo
- Never merge branches containing private data
- Tag releases with matching version numbers

### Private Repo References
- Keep reference to public repo as submodule or remote
- Document which commits have been synced to public

---

## Contact

For questions about what is safe to publish, consult the maintainer before any push.
