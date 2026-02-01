# NeuraLogix v0.7.1 Public Demo Pack
Domain: Project Management / Software Releases

## Purpose
This pack showcases the robustness of the **Verified Observation Runtime (VOR)** in a realistic software development context. It demonstrates how the system handles:
1. **Ambiguity**: Identifying different entities with the same surface names (e.g., "Phoenix" project vs "Phoenix" release).
2. **Aliasing**: Mapping different terms ("RC", "Release Candidate", "v0.7.1") to the same underlying entity.
3. **Conflicts**: Proactively identifying contradictory documentation regarding launch dates.
4. **Scale**: Maintaining performance over hundreds of documents.

## Usage
Run the demo using the NeuraLogix CLI:
```bash
neuralogix qa --pack data/packs/public_demo_v0_7_1 --fast
```

Or via the audit suite:
```bash
neuralogix audit --fast
```
