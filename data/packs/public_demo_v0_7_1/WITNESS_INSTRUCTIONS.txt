# NeuraLogix Witness Run Instructions (v0.7.x)

This document provides idiot-proof instructions for certifying the NeuraLogix Verified Observation Runtime (VOR) in a clean-room state.

## 1. Preflight Checklist
- **OS**: Windows / Linux / macOS
- **Python Version**: 3.10+ (Verified on 3.12.10)
- **Tooling**: `git`, `python`, `pip`

### Initial Setup
```bash
# Create and activate a fresh virtual environment
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# Install NeuraLogix in development mode
pip install -e .
```

## 2. Execution Sequence
Run these commands in order. Capture the output of each for the witness bundle.

### A. Version Check
```bash
neuralogix --version
```
**Expected Exit Code**: 0

### B. Pack Validation
```bash
neuralogix pack validate --pack data/packs/public_demo_v0_7_1
```
**Expected Exit Code**: 0 (Should say "✅ Pack validated")

### C. QA Execution (Fast)
```bash
neuralogix qa --pack data/packs/public_demo_v0_7_1 --fast
```
**Expected Exit Code**: 0 (Should display reasoning traces and summary)

### D. Audit Certification
```bash
neuralogix audit --pack data/packs/adversarial_v1 --fast
```
**Expected Exit Code**: 0 (Should report 0.0% Hallucination Rate)

## 3. Artifact Capture
After execution, collect the following files into a single ZIP archive:
- Entire `results/` folder.
- `pip_freeze.txt` (generate with `pip freeze > pip_freeze.txt`).
- `env_info.txt` (generate with `python -c "import platform, sys; print(f'OS: {platform.system()} {platform.release()}\nPython: {sys.version}')" > env_info.txt`).

## 4. Troubleshooting ("If it fails")
- **Wrong Working Directory**: Ensure you are in the root of the `NUERALOGIX-H` repository.
- **Missing venv**: Ensure `.venv` is active (check prompt prefix).
- **Manifest Mismatch**: Check for CRLF vs LF issues in `.jsonl` files (run `git checkout .` to reset).
- **Abstention Trap**: If results show 100% ABSTAIN, ensure you are on the `v0.7.x` branch with the enhanced parser.

**Logs to send**: Attach `audit_error.txt` if any command fails with a non-zero exit code.
