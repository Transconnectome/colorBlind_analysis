# closure/ — Phase 2 Closure Result Files

Canonical result files for PIPELINE_2_CLOSURE.md. Source files remain in
`s10_inclusion/` and `redteam/` for backward compatibility with scripts.

## Naming Convention

```
{sub}_{preproc}_{atoms-rois}_{metric}_{estimator}.json
```

| Field | Values |
|---|---|
| `{sub}` | `s08`, `s09`, `s0809` |
| `{preproc}` | `pca`, `srm-cos`, `srm-dis` |
| `{atoms-rois}` | `allcombos`, `selected`, `gOY-rdmV2`, `gALL-rdmV1` |
| `{metric}` | `composite`, `param`, `rdm-gamma-nc`, `rdm-gamma`, `precond`, `null`, `loss-depth`, `loss-spec`, `param-recov`, `algo-val-origin`, `label-perm` |
| `{estimator}` | `N300` (5/2 HC resample ×300), `loo7-refit` (7-fold LOO, per-fold refit), `loo7-fixedparam` (7-fold LOO, production param fixed), `loco-v4-pass` (LOCO V4 single-pass), `synth-hc-*-N200`, `synth-N140`, `within-N1000` |

## Folder → §3.3 Hierarchy Mapping

```
gate/        →  Gate criterion (LOCO V4 precondition)
selection/   →  Primary + Secondary (composite test_loss_median, N300)
validation/  →  Supplementary (7-fold LOO)
specificity/ →  Theme A null testing
```

## Files

### gate/
| File | Source | Content |
|---|---|---|
| `s0809_pca_allcombos_precond_loco-v4-pass.json` | `precondition_table.json` | LOCO V4 pass/fail per combo per ROI |

### selection/
| File | Source | Content |
|---|---|---|
| `s08_pca_allcombos_composite_N300.json` | `s10b_v6_pca_rdm_results_sub-08.json` | Table A primary: test_loss_median, param IQR, mode share |
| `s09_pca_allcombos_composite_N300.json` | `s10b_v6_pca_rdm_results_sub-09.json` | Table A primary |
| `s08_srm-cos_allcombos_composite_N300.json` | `s10b_v6_srm_rdm_results_sub-08.json` | App A.4 cross-metric validation |
| `s09_srm-cos_allcombos_composite_N300.json` | `s10b_v6_srm_rdm_results_sub-09.json` | App A.4 cross-metric validation |

### validation/
| File | Source | Content |
|---|---|---|
| `s0809_pca_selected_param_loo7-refit.json` | `s17_hc_loo_results.json` | RQ2: β IQR/range across 7 folds |
| `s0809_pca_selected_rdm-gamma-nc_loo7-refit.json` | `s18_heldout_predictive.json` | RQ4(e): rdm L_test + γΔL + NC (selected candidates) |
| `s0809_pca_allcombos_rdm-gamma_loo7-fixedparam.json` | `s19_allcandidate_heldout.json` | Table B: rdm ΔL + γΔL for all 82 candidates |

### specificity/
| File | Source | Content |
|---|---|---|
| `s0809_pca_allcombos_null_synth-hc-onesided-N200.json` | `exp14_onesided_loo_null.json` | Theme A(i): matched-grid one-sided null |
| `s0809_pca_allcombos_null_synth-hc-sym-N200.json` | `exp15_symmetric_loo_null.json` | Theme A(i): matched-grid symmetric null |
| `s0809_pca_selected_loss-depth_real-vs-synth.json` | `exp17_loss_landscape.json` | Theme A(ii): real vs synthetic loss depth (2.1–5.5×) |
| `s0809_pca_selected_loss-spec_synth-fakecvd-N200.json` | `exp22_origin_loss_specificity.json` | Theme A(v): Bonferroni 3-test loss specificity |
| `s0809_pca_selected_param-recov_synth-N140.json` | `param_recovery_voxel_v6_pca_v2.json` | Theme A(iv): parameter recovery f10° (Test 1) |
| `s0809_pca_selected_algo-val-origin_synth-N140.json` | `null_within_hc_loo_v6_pca.json` | Theme A(iv): (0,0) algorithm validation, noise floor ~20°/25° (Test 2a) |
| `s0809_pca_selected_label-perm_within-N1000.json` | `null_label_permutation_v6_pca.json` | Theme A(vi): within-subject label permutation (Test 2c) |
