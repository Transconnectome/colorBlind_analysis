# _archive/ — Deprecated / superseded directories

**Status**: ARCHIVE (deletion candidates pending audit)
**Created**: 2026-05-03
**Last update**: 2026-05-28 (Phase D)

## Contents

### Pre-Phase D (existing)
- `paper_figures/` — Orphaned timestamp dir from Apr 20. **0 references** in any script or doc. Safe to delete.
- `validation_v2/` — Superseded by `validation_2component/`. Only 1 script ref (`validate_v2_comprehensive.py`). Generator script kept in scripts/ for reproducibility.
- `cleanup_2026-05-17/`, `cleanup_2026-05-18/` — earlier cleanup batches
- `old_labels_pre_2026-05-16/` — pre-cutoff 13-bin label scheme outputs
- `post_consolidation_verify_sub08/`, `post_consolidation_verify_sub09/` — post-consolidation audit
- `prev_pipeline_2026-05-25/` — previous-pipeline snapshot before closure

### Phase D (2026-05-28) — moved per PIPELINE_2_CLOSURE.md §Deprecated

| Source | Reason | Now at |
|---|---|---|
| `results/oos_reanalysis_v1/` | Pipeline 3 (s15) output — closure §Pipeline 3 status: "Pipeline 3 의 별도 후속 작업 없음" | `_archive/oos_reanalysis_v1/` |
| `results/s11_pre_phase_c_null_sim/` | Phase B v6 stability check 가 대체 | `_archive/s11_pre_phase_c_null_sim/` |
| `results/s14_atom_redesign/` | Cycle 5 atom redesign — PCA-RDM 으로 흡수 | `_archive/s14_atom_redesign/` |
| `results/s13_multipoint_sim/s13_multipoint_recovery_round1.json` | Phase D Round 1 — `s13_round3_recovery.json` 가 supersede | `_archive/s13_multipoint_sim_rounds_1_2/round1.json` |
| `results/s13_multipoint_sim/s13_multipoint_recovery.json` (Round 2) | 동일 — Round 3 가 supersede | `_archive/s13_multipoint_sim_rounds_1_2/round2.json` |

## Action

- These directories were moved here progressively during cleanup phases
- Deletion pending user explicit confirmation (per CLAUDE.md project guidance: "destructive operations require user approval")
- Phase D moves are reversible via `mv` (most files untracked at time of move; the one tracked file `s14_atom_redesign/atom_comparison.md` used `git mv`)
