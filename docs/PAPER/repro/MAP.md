# Phase 2 — Analysis → Code Map (colorBlind PAPER repro)

`id → file:line` of the producing code. Paths relative to repo root `analysis/`.
One notebook per experiment: `01_discrimination` (E1), `02_interpolation` (E2), `03_geometry` (E3), `04_model_selection` (E4), `05_identifiability` (E5), `06_filter_eval` (E6).

## E1 — Discrimination + cross-decoding  → notebook 01
| id | producing code | callable | committed output | input |
|---|---|---|---|---|
| E1.1 LORO 8-class | `phase3_decoder_comparing/model_comparison_validation/scripts/loro_baseline.py` | monolithic CLI | `phase3_decoder_comparing/results/loro/srm/sub-{01..10}_performance_raw.json` ✓ (`results.srm.{ROI}.ForwardEncoding[].acc_exact`) | C010 amplitudes |
| | ⚠ **corrected 2026-08-05** — see note below. `future_phase1_forward_model/…/validate_loro_loco_loso.py` → `sub-*_loro.json` reports voxel_corr / R² / rdm_corr, **not** 8-class accuracy, so it cannot back the "exceeded 0.125 chance" claim. | | | |
| E1.2 MannWhitney p=0.668 | `phase3_decoder_comparing/model_comparison_validation/scripts/validation_tests.py:477-678` (MW @651) | **import-callable** | `phase3_decoder_comparing/results/loro/srm/validation/cross_subject_generalization.json` ✓ (key `LDA/difference/p_value`=0.6681) | C010 amplitudes_{raw,procrustes,srm} |
| E1.3 hV4 CH p=0.142 | `future_phase1_forward_model/scripts/_compute_paper_stats.py:48-57,234-243` | monolithic, stdout-only | ⚠ **no committed output** (inline print) | sub-*_loco.json |

> **E1.1 source correction (2026-08-05).** `01_discrimination.ipynb` verifies E1.1
> against `model_comparison_validation/results/cvd_cross_decoding/cvd_cross_decoding_procrustes.json`.
> That file is the **pre-RT-7 run** (all-subject SRM, `alignment: procrustes`,
> 2026-02-18 12:50), superseded 5 hours later by the HC-only RT-7 fix
> (`cvd_cross_decoding_hconly.json`, 17:38) that exists to remove that run's
> circularity. Its producer had been deleted in commit `3ec8e51` and was restored
> on 2026-08-05 to `model_comparison_validation/scripts/run_cvd_cross_decoding.py`
> (RT-7 version, writes the `hconly` output).
>
> `results_v4.tex:31` cites **Figure 3A**, which `generate_fig2.py:108-112` builds
> from `results/loro/srm/sub-*_performance_raw.json` — a live source with a live
> producer. Those LORO values clear chance comfortably (sub-08 V1 0.604 / V2 0.458
> / V3 0.375 / V4 0.354; sub-09 0.625 / 0.438 / 0.312 / 0.354, all ≫ 0.125), so
> **the manuscript claim is sound**; only the notebook's verification cell points
> at the wrong file.
>
> ⚠ Note for whoever repoints the cell: the RT-7 (non-circular) cross-decoding
> numbers are *weaker at hV4* than the superseded ones (sub-08 0.75 → 0.375,
> permutation p = 0.057; sub-09 0.75 → 0.625). Do not present the pre-RT-7 values.

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
| E3.3 ΔRDM heatmap | `docs/PAPER/Figures/scripts/generate_fig3.py:31,88` | figure generator | `future_phase2_filter_optimization/results/diagnostics/srm_precompute/delta_rdm_obs_srm_{roi}.npz` ⚠ **directory currently missing** | SRM-aligned amplitudes |
| | ⚠ **corrected 2026-08-05** — the former pointer, `phase2_SRM_across_between/visualization/visualize_scattered_but_parallel.py`, was a schematic stub that never produced the published panel; it moved to `_archive/visualization_unused/` on 2026-08-05. | | | |

> **Fig 4 (fig3\_geometry) is not currently regenerable — do not "restore" the archived precompute.**
> The only surviving `srm_precompute` lives at
> `future_phase2_filter_optimization/results/_archive/old_labels_pre_2026-05-16/phase2_artifacts/diagnostics/srm_precompute/`
> and is unusable for two independent reasons:
> 1. It covers **V1 and V2 only** (`manifest.json` → `rois: [V1, V2]`), while
>    `generate_fig3.py:39` requires `[V1, V2, V3, hV4]`.
> 2. It is dated **2026-04-12**, i.e. **before the 2026-05-16 label-scheme cutoff**,
>    and is filed under `old_labels_pre_2026-05-16/` — the 13-bin scheme superseded
>    by `c3_relabel_p2a` 9-bin (project memory `feedback_label_scheme_cutoff`).
>
> The published `fig3_geometry.pdf` therefore has no reproducible source in the tree.
> Regenerating it requires a fresh 4-ROI ΔRDM precompute under the current label scheme.
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

## E6 — Filter eval 2nd session  → notebook 06  ⚠ N=2 (sub-08 deutan + sub-09 protan); ⚠ SRM(E6.2d) MPI

> **Corrected 2026-08-05.** This section previously marked every row "sub-09: NO
> (not collected)". That was stale — the full sub-09 set exists on disk and
> `METHODS_RESULTS_SUMMARY_FOR_PAPER.md` §Future Phase 3 reports its numbers
> (hV4 LOCO adjacent accuracy 0.14 / 0.19 / 0.06 for no-filter / deployed /
> individualized; $d_{cc} = -3.70$) as part of the N=2 descriptive reframe.
> `exp2_neural/SUB09_MANUSCRIPT_TODO.md` §C1 lists the tex lines that still
> assert non-collection and must be revised.

| id | producing code (`future_phase3_behavioral_analysis/exp2_neural/scripts/`) | committed output | sub-09? |
|---|---|---|---|
| E6.1 LOCO ρ + Δρ + d | `exp2_hc_likeness.py:53-59,210-412` (calls loco_canonical) | `results/exp2_hc_likeness_sub-0{8,9}_{native,matched}.json` ✓ | YES |
| E6.2a/b LORO/LOCO acc | `exp2_hc_likeness.py:93-146` | same json ✓ | YES |
| E6.2c deployed adj 0.22 | `exp2_decoder_2x2.py:75-90` | `exp2_decoder_2x2_sub-0{8,9}_{native,matched}.json` ✓ | YES |
| E6.2d SRM disp + RDM | `exp2_convergent.py:149-187` (**BrainIAK SRM**) | `exp2_convergent_sub-0{8,9}_{native,matched}.json` ✓ | YES |
| E6.3 behavioral JND/8AFC | `analyze_exp2_behavior.py:32-70` | `…/results/exp2_behavior/sub-0{8,9}_summary.json` ✓ (sub-08: wilcoxon p=0.8438, rsvp 0.81→0.97) | YES |
| | condition map: window={1,4,5,8}=deployed, optimal={2,3,6,7}=personalized (sub-09 = mirror of sub-08) | | |
| | ⚠ sub-09 `exp2_geometry_derived` exists for `matched` only (no `native`). | | |

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
