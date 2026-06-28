# Phase 2 — Analysis → Code Map (colorBlind PAPER repro)

`id → file:line` of the producing code. Paths relative to repo root `analysis/`.
One notebook per experiment: `01_discrimination` (E1), `02_interpolation` (E2), `03_geometry` (E3), `04_model_selection` (E4), `05_identifiability` (E5), `06_filter_eval` (E6).

## E1 — Discrimination + cross-decoding  → notebook 01
| id | producing code | callable | committed output | input |
|---|---|---|---|---|
| E1.1 LORO 8-class | `future_phase1_forward_model/scripts/validate_loro_loco_loso.py:54-165` | monolithic CLI | `…/results/validation/sub-{01..10}_loro.json` ✓ | C010 amplitudes |
| E1.2 MannWhitney p=0.668 | `phase3_decoder_comparing/model_comparison_validation/scripts/validation_tests.py:477-678` (MW @651) | **import-callable** | `phase3_decoder_comparing/results/loro/srm/validation/cross_subject_generalization.json` ✓ (key `LDA/difference/p_value`=0.6681) | C010 amplitudes_{raw,procrustes,srm} |
| E1.3 hV4 CH p=0.142 | `future_phase1_forward_model/scripts/_compute_paper_stats.py:48-57,234-243` | monolithic, stdout-only | ⚠ **no committed output** (inline print) | sub-*_loco.json |

## E2 — Interpolation / per-hue  → notebook 02
| id | producing code | callable | committed output | input |
|---|---|---|---|---|
| E2.1-2.7 adjacent acc + per-hue CH | `future_phase1_forward_model/scripts/loco_canonical.py:44-115` `loco_forward_readouts` (FE-6 OLS) | **import-callable** | ⚠ **no committed per-hue adj output**; my regen is de-facto driver | C010 V4 amplitudes_procrustes |
| E2.1/2.2 adj-acc above-chance perm (hV4 p=0.008, V1 p=0.164) | `future_phase1_forward_model/scripts/permutation_test_loco.py` (per-subject design); driver `docs/PAPER/repro/_perm_definitive_hv4.py`, `_perm_v1.py` | monolithic + repro driver | committed null arrays `docs/PAPER/repro/perm_definitive_hv4_null.npy`, `perm_v1_null.npy` ✓ | C010 V4/V1 amplitudes |
| (superseded) voxel_corr 8! perm p=0.044 | `permutation_test_loco.py` voxel_corr metric | monolithic | `…/results/loco_reinforcement/permutation_test.json` ✓ — **no longer cited in tex** | same |
| (overall CH t/p) | `_compute_paper_stats.py:48-57` crawford_howell | — | — | — |

## E3 — Geometry / SRM disparity  → notebook 03  ⚠ BrainIAK+MPI
| id | producing code | callable | committed output | input |
|---|---|---|---|---|
| E3.1/E3.2/E3.7 disparity table | `phase2_SRM_across_between/rerun_loo_consistent.py:92-168,295-757` | monolithic, **`mpirun -np 1`** (SRM @46) | `…/results/loo_consistent/20260218_163819/loo_consistent_results.json` ✓ | phase1_preprocess_decoding C010 amplitudes_procrustes |
| E3.3 ΔRDM heatmap | `phase2_SRM_across_between/visualization/visualize_scattered_but_parallel.py:34-50,249-317` | partial **stub** | ⚠ **no committed ΔRDM output** (schematic only) | SRM-aligned (manual) |
| E3.5 SRM k=4/4/3/3 | `…/validation/2C_optimal_k_selection/run_k_selection_cv.py:63-140` + `aggregate_k_selection.py:76-145`; canonical override `rerun_loo_consistent.py:60` | monolithic, MPI | `k_aggregation_results.json` ✓ | same |
| | ⚠ **flag**: raw aggregation selects 4/5/4/6; paper 4/4/3/3 is a **hardcoded canonical override** (rerun L60). | | | |

## E4 — Simulator model selection  → notebook 04  (CURRENT v6 PCA canonical)
| id | producing code (`future_phase2_filter_optimization/scripts/`) | committed output (`results/`) |
|---|---|---|
| E4.1/4.2 R+C reject | `s10b_v6_pca_rdm.py:216-226` grid_eval_rc | `s10_inclusion/s10b_v6_pca_rdm_results_sub-{08,09}.json` ✓ |
| E4.4/4.5 2-comp argmin | `s10b_v6_pca_rdm.py:229-239` + `s17_hc_loo.py` | same + `s10_inclusion/s17_hc_loo_results.json` ✓ |
| E4.8 held-out folds, NC | `s18_heldout_predictive.py`, `s19_allcandidate_heldout.py` | `s18_heldout_predictive.json`, `s19_allcandidate_heldout.json` ✓ |
| E4.9/4.10 neural benefit | `s18_heldout_predictive.py:150-250` | s18 json (gamma/rdm standalone) ✓ |
| E4.11 3-gate (N=300) | `s10b_v6_pca_rdm.py:49-51,320-550` + `s10a_precondition.py` | `precondition_table.json` ✓ — **N=300 confirmed** |
| E4.12 grid 8281 / g∈[0,3] | `two_comp.py:15-25`, `rc_1dof.py:1-30` | implicit |
| E4.13 pre-image 26.3/16.2 | `exp2_compute_preimage.py:18-44` (brentq @42) | `exp2_preimage/sub-{08,09}_2component_preimage.json` ✓ |

## E5 — Identifiability S15  → notebook 05  (CURRENT v6 PCA)
| id | producing code (`future_phase2_filter_optimization/scripts/`) | committed output (`results/redteam/`) |
|---|---|---|
| E5.2 Test1 f10 | `param_recovery_voxel.py:1-300` | `param_recovery_voxel_v6_pca_v2.json` ✓ |
| E5.3 Test2a / E5.4 Test2b | `null_within_hc_loo.py:1-150` | `null_within_hc_loo_v6_pca.json` ✓ |
| E5.5 Test2c perm | `null_label_permutation_block.py:1-200` | `null_label_permutation_v6_pca.json` ✓ |

## E6 — Filter eval 2nd session  → notebook 06  ⚠ deutan(sub-08) only; ⚠ SRM(E6.2d) MPI
| id | producing code (`future_phase3_behavioral_analysis/exp2_neural/scripts/`) | committed output | sub-09? |
|---|---|---|---|
| E6.1 LOCO ρ + Δρ + d | `exp2_hc_likeness.py:53-59,210-412` (calls loco_canonical) | `results/exp2_hc_likeness_sub-08_{native,matched}.json` ✓ | NO (not collected) |
| E6.2a/b LORO/LOCO acc | `exp2_hc_likeness.py:93-146` | same json ✓ | NO |
| E6.2c deployed adj 0.22 | `exp2_decoder_2x2.py:75-90` | `exp2_decoder_2x2_sub-08_native.json` ✓ | NO |
| E6.2d SRM disp + RDM | `exp2_convergent.py:149-187` (**BrainIAK SRM**) | `exp2_convergent_sub-08_native.json` ✓ | NO |
| E6.3 behavioral JND/8AFC | `analyze_exp2_behavior.py:32-70` | `future_phase3_behavioral_analysis/results/exp2_behavior/sub-08_summary.json` ✓ (wilcoxon p=0.8438, rsvp 0.81→0.97) | NO |
| | condition map: window={1,4,5,8}=deployed, optimal={2,3,6,7}=personalized | | |

---
## (a) Reported but NO committed producing output
- **E1.3** — code exists, stdout-only (regenerable by re-running `_compute_paper_stats.py`).
- **E2.5–2.7 per-hue adjacent acc** — only `loco_canonical` library fn; **my regen script is the driver** (notebook 02 will embed it).
- **E3.3 ΔRDM** — only a visualization stub; needs a small driver to compute RDM_CVD − mean(RDM_HC) from committed SRM amplitudes.

## (b) Code but NOT reported (exploratory — EXCLUDE from notebooks)
- `future_phase2…/scripts/s13_multipoint_sim` (Phase D multipoint), `s19_allcandidate` full ranking, archived `_archive_pre_closure/*`, SRM `visualize_*` schematics. Flag, do not include.

## Execution constraints (for Phase 3/4)
- **BrainIAK + `mpirun -np 1`** required for E3 (disparity/k-selection) and E6.2d (SRM RDM). Plain jupyter kernel cannot `mpirun`. Options per cell: (i) **load committed JSON** and verify (presence + value check) rather than recompute, or (ii) shell-out via `subprocess` to `mpirun -np 1 python …`. Decision needed at GATE 3.
- E4/E5 heavy (N=300 resamples, 1000 perms, SLURM-origin) — notebooks will **load committed result JSON and verify**, not re-run the full server compute, except light recomputation (E2 adjacent acc, E4.13 pre-image) which is cheap locally.
