# results/ — Pipeline 2 output index

각 결과 디렉토리의 Pipeline 2 step 매핑. 자세한 narrative 는 `../PIPELINE_2_CLOSURE.md` 참조.

## Pipeline 2 core outputs (현재 reference)

| Directory / file | Pipeline 2 Step | 내용 |
|---|---|---|
| `s10_inclusion/precondition_table.json` | Step 1 | Phase A HC LOO single-loss precondition table |
| `s10_inclusion/s10b_v6_pca_rdm_results_{sub-08,sub-09}.json` | Step 2 + 3 | Phase B v6 main output: per-cell × per-model (284 sub-08 / 44 sub-09 cells × 4 models), test_loss median/IQR, test_focal, test_agg, test_V1_RDM, AIC/BIC, boundary_rate, param_summary |
| `s10_inclusion/s17_hc_loo_results.json` *(gitignored)* | Step 3 supplement | strict HC LOO 7-fold per candidate, per-fold β/g + holdout HC identifier |
| `s10_inclusion/cycle6b_extended_composite_{sub-08,sub-09}.json` | Step 4 | raw-weight scheme sweep (47 schemes) — Step 3 후보의 cross-scheme robustness |
| `s13_multipoint_sim/s13_round3_recovery.json` | Step 5 (Phase D) | multi-point recovery (null + fit GT × 50 outer × 7 inner) on 3 final candidates |

## Deprecated outputs (참조용 보관)

**2026-05-28 (Phase D)**: 다음 4 dir / 2 file 이 `_archive/` 로 이동되었음. 자세한 매핑은 [`_archive/README.md`](_archive/README.md) §Phase D 표 참조.

| Directory | 상태 | 현재 위치 |
|---|---|---|
| `s12b_phase_c_v2/sweep_*.json` | Phase C v2 — final selection 기여 없음, L8 seed audit 보고용 (sweep_*_seed142.json 포함) | **여전히 `results/s12b_phase_c_v2/`** (L8 audit 한정 보존) |
| `s13_multipoint_sim/s13_multipoint_recovery_round1.json`, `_round2.json` | Phase D Round 1/2 — `s13_round3` 가 final candidates 적용으로 supersede | → `_archive/s13_multipoint_sim_rounds_1_2/` |
| `s11_pre_phase_c_null_sim/` | pre-Phase-C null simulation, Phase B v6 stability check 가 대체 | → `_archive/s11_pre_phase_c_null_sim/` |
| `s14_atom_redesign/` | Cycle 5 atom redesign, PCA-RDM 으로 흡수 | → `_archive/s14_atom_redesign/` |
| `oos_reanalysis_v1/` | Pipeline 3 (s15) output, deprecated | → `_archive/oos_reanalysis_v1/` |
| `_superseded/` | 이전 pipeline-1 era outputs (loco_filter, candidates_p2 등) | (unchanged) |
| `_archive/` | older cleanup (post_consolidation_verify, validation_v2 등) + 위 Phase D 항목 | (this directory) |

## Pipeline 2 final candidates 의 출처 위치

| Candidate | 출처 cell (Phase B v6 label) | JSON path |
|---|---|---|
| sub-08 βs-dom (β_s=38, β_c=−10) | `γALL\|RDMV1\|noLOCO` / `2comp` | `s10_inclusion/s10b_v6_pca_rdm_results_sub-08.json` |
| sub-08 βc-dom (β_s=6, β_c=−42) | `γOY\|RDMV2\|noLOCO` / `2comp` (also `γOY\|RDMV3\|noLOCO`) | (same) |
| sub-09 βc-rot (β_s=2, β_c=24) | `γALL\|RDMV1\|noLOCO` / `2comp` (also `γGB\|RDMV1\|noLOCO`) | `s10_inclusion/s10b_v6_pca_rdm_results_sub-09.json` |
| sub-08 R+C ref (g=2.25) | `γ_\|RDMV1\|noLOCO` / `rc_JND_Lamb` | (same as sub-08) |
| sub-09 R+C ref (g=2.95) | `γALL\|RDMV1\|noLOCO` / `rc_Boehm_low` | (same as sub-09) |

후보의 raw-weight robustness (Step 4) 는 `cycle6b_extended_composite_{sid}.json` 의 `unique_candidates[].schemes_top` 에서 확인 가능.

Identifiability (Step 5 Phase D) 는 `s13_multipoint_sim/s13_round3_recovery.json` 의 `loo_folds`(per-fold) + `summary` (aggregate) 에서 확인.

## Visualization outputs (closure-consistent)

| Directory | Generator | Forward |
|---|---|---|
| `visualizations/pipeline2_primary_4col/` (3 primary + 1 summary PNG) | `scripts/p2_primary_4col.py` | closure (`scripts/two_comp.py`) — raw nominal-θ, fit-code consistent |

**Closure δθ sanity (deutan, β_s=38, β_c=−10)**: `[+8.66, +29.46, +33.0, +17.21, −8.66, −29.46, −33.0, −17.21]`. 어떤 viz 든 이 8-vec 과 다른 δθ 를 그린다면 frozen H_BASE 변형을 사용하고 있는 것이며 closure 와 부합하지 않음 — see `../CLAUDE.md` A13.

Pre-2026-05-27 viz (`scripts/visualization/visualize_phase3_preimage.py`, `scripts/render_loco_canonical_4col.py`, `scripts/s5_*_viz_4col.py`, `scripts/s7_best_models_4col.py`) 는 frozen H_BASE 변형으로 그려진 이력이 있으므로 closure 보고용으로는 사용 금지.
