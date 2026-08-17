# diagnostics/_archive/ — Pre-closure diagnostic scripts

16 scripts moved here on 2026-05-28 (Phase B'). Each was excluded because
no active doc cites it AND/OR it imports a Phase-B-archived module
(`step1_fit_loco_v2`, `loco_distortion_fit`, `retinal_cortical`).

## Files with broken imports (9)

These import modules now under `scripts/_archive_pre_closure/older_forwards/`:

| File | Imports archived |
|---|---|
| `baseline_delta_rho_diagnostic.py` | loco_distortion_fit, step1_fit_loco_v2 |
| `baseline_delta_rho_with_rdm.py` | loco_distortion_fit, step1_fit_loco_v2 |
| `delta_rho_perm_test.py` | loco_distortion_fit, step1_fit_loco_v2 |
| `experiment_b_weight_sweep.py` | loco_distortion_fit, step1_fit_loco_v2 |
| `experiment_delta_vuln.py` | loco_distortion_fit, step1_fit_loco_v2 |
| `hc_specificity_test.py` | loco_distortion_fit, step1_fit_loco_v2 |
| `srm_integrated_loco.py` | loco_distortion_fit, step1_fit_loco_v2 |
| `validate_2component.py` | retinal_cortical |
| `validate_v2_comprehensive.py` | retinal_cortical |

## Files without active citation (7)

`analyze_loco_profile_specificity.py`, `aphi_sanity_check.py`,
`diagnostic_perceptual_distance.py`, `diagnostic_protan_vs_deutan.py`,
`diagnostic_srm_specificity.py`, `extract_loco_confusion_direction.py`,
`summarize_cross_family.py` — all closure §0 forbids specificity claims,
or one-off diagnostics absorbed into Phase B v6.

## KEEP (parent dir)

`cardinal_axis_amplitude.py` — cited by `index.md` (cardinal-axis univariate
post-hoc) and `presentation/`.
