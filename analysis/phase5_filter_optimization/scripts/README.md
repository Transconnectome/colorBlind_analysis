# `scripts/` — Phase 2 code structure & execution guide

Phase B (simulator fit) + Phase C (pre-image filter) code for the CVD
individualized-filter pipeline. Narrative source of truth:
[`../PIPELINE_2_CLOSURE.md`](../PIPELINE_2_CLOSURE.md). Closure-citation index:
[`_ACTIVE.md`](_ACTIVE.md). Framework / forward rules: [`../CLAUDE.md`](../CLAUDE.md) §A13.

> ⚠️ **Flat imports — do NOT move core files into subfolders.** Every script
> imports siblings flat (`from behav_loss import …`, `from two_comp import …`).
> Python puts the run script's own directory on `sys.path[0]`, so
> `python scripts/X.py` resolves these. Relocating a core module into a
> subdirectory breaks the whole pipeline. Organize *logically* (this README),
> not physically.
>
> External dep: `../future_phase1_forward_model/scripts/utils_forward_model.py`
> (`create_basis_full`, `HUE_ANGLES`) — Phase 1 module, added to path by the scripts.

**Environment**: `conda activate srm` (local). All inputs are local (no server).

**2026-06-02 cleanup**: deleted superseded figure iterations
`make_loss_pipeline_{fig,v2..v8}.py` (kept `make_loss_pipeline_v9.py`, repo root);
`git rm` exploratory orphans `exp_atom_decomp_at_zero.py`, `exp_gt_grid_sweep.py`
(recoverable from git history). No core/pipeline files moved (flat-import constraint).

---

## §1 Core library — imported by the pipeline (never delete/move)

| Module | Provides |
|---|---|
| `two_comp.py` ★ | Closure 2-Component forward `forward_2comp` (raw CIElab nominal-θ, A13). |
| `rc_1dof.py` | R+C forward `δθ=(2−g)·δθ_Machado(c;Δλ)`. |
| `machado_simulator.py` | Machado–Smith cone-shift fundamentals. |
| `utils_distortion_models.py` | distortion-model utils (wraps `machado_simulator`). |
| `behav_loss.py` | γ (JND z²) atom factories + HC-pool JND baseline. |
| `neural_loss.py` | `L_LOCO`, `L_RDM` atoms + `precompute_loco_W_within`. |
| `diagnostic_delta_rdm.py` | `precompute_hc_W` for RDM atoms (library, despite name). |
| `s8_loo_train_test.py` | `jnd_baseline_from_pool`, `DELTA_LAMBDA_BY_FAMILY`. |
| `s10b_v6_pca_rdm.py` | v6 PCA-45° atom factories, grid/argmin helpers (also a Step-2/3 entry). |
| `forward_voxel_synth.py` | voxel-level synthesis for verification (used by Tests 1/2a). |

## §2 Pipeline entry points — 5-step closure (per PIPELINE_2_CLOSURE.md)

| Step | Script | Output (`results/…`) |
|---|---|---|
| 1 precondition | `s10a_precondition.py` | `s10_inclusion/precondition_table.json` |
| 2 atoms + cells | `s10b_v6_pca_rdm.py` (`build_cells`) | (in v6 JSON) |
| 3 fit + HC 5/2×300 (main) | `s10b_v6_pca_rdm.py --subject sub-08\|sub-09` ★ | `s10_inclusion/s10b_v6_pca_rdm_results_{sub}.json` |
| 3 strict HC LOO 7-fold | `s17_hc_loo.py` | `s10_inclusion/s17_hc_loo_results.json` |
| 4 raw-weight robustness | `cycle6b_extended_raw_weight.py` | `s10_inclusion/cycle6b_extended_composite_{sub}.json` |
| 5 identifiability (Phase D R3) | `s13_round3.py` | `s13_multipoint_sim/s13_round3_recovery.json` |

## §3 Closure verification — "redteam" 4-test battery (closure.md Tests 1/2)

Generates `results/redteam/*.json` that back `closure.md`. Run after §2.

| Script | closure.md test | Output |
|---|---|---|
| `param_recovery_voxel.py` | Test 1 (recovery at argmin) | `redteam/param_recovery_voxel_v6_pca_v2.json` |
| `null_within_hc_loo.py` | Test 2a (origin) + 2b (HC pseudo-CVD) | `redteam/null_within_hc_loo_v6_pca.json` |
| `null_label_permutation.py` | Test 2c (label perm) | `redteam/null_label_permutation_v6_pca.json` |
| `null_label_permutation_block.py` | Test 2c block variant | `redteam/null_label_permutation_block_v6_pca.json` |
| `analyze_verification.py` | aggregate → FDR verdict matrix | `redteam/verdict_matrix_v6_pca_v2.{json,md}` |
| `build_uncertainty_summary.py` | effective-uncertainty summary | `redteam/uncertainty_summary.{json,md}` |

## §4 Held-out predictive test-loss (s18/s19) — closure Test 3, NEW 2026-06-02

| Script | Role | Output |
|---|---|---|
| `s18_heldout_predictive.py` | leave-one-HC-out 7-fold **test-loss** (ΔL vs no-correction (0,0)) + neural/behav standalone fits, for the **selected** candidates. Answers "stable value도 *좋은* 값인가". Imports `s17_hc_loo`. | `s10_inclusion/s18_heldout_predictive.{json,md}` |
| `s19_allcandidate_heldout.py` | same held-out metric across **ALL gate-passing candidates** (noLOCO+RDM; S08 30, S09 3). Cross-candidate rank by grid-null **percentile** (ROI-comparable). Corroborates that the stability-pick is goodness top-tier; characterizes the landscape (NOT re-selection, §0). Imports `s18`+`s17`. | `s10_inclusion/s19_allcandidate_heldout.{json,md}` |

Key facts (closure `Test 3`): held-out RDM goodness is **non-discriminative** (45° categorical
quantization → ±~22.5° plateau ≈ Test 2a ~20° floor); selected values are top-tier but the
metric cannot *pin* the value. Phase 3 validates the **behavioral/neural efficacy of the
specific selected value** (not point-precision).
Interpretation: [`../results/s10_inclusion/s18_INTERPRETATION.md`](../results/s10_inclusion/s18_INTERPRETATION.md);
narrative in `closure.md` §Test 3 + PIPELINE_2_CLOSURE.md RQ3(ii)/RQ4(e,f).

## §5 RDM-atom appendix — SRM variants (convergence check, not fitting primary)

| Script | Role |
|---|---|
| `s10b_v6_srm_rdm.py` | SRM-cosine RDM atom variant. |
| `s10b_v6_srm_disparity.py` | SRM Procrustes disparity atom variant. |
| `s17_srm_hc_loo.py` | strict HC LOO, SRM-RDM variant (mirrors `s17_hc_loo`). |
| `compare_primary_candidates.py` | PCA-RDM vs SRM-cos vs SRM-disparity at the 3 primary cells. |

## §6 Figures & visualization (closure-consistent forward only)

| Script | Output |
|---|---|
| `fig_candidates_param_space.py` | `results/figures/fig_candidates_param_space.png` (RQ1/§5.1) |
| `fig_specificity_summary.py` | `results/figures/fig_specificity_summary.png` (§5.2 Theme A) |
| `p2_primary_4col.py` | `results/visualizations/pipeline2_primary_4col/` (3 primary + summary) |
| `p2_alternative_rdm_4col.py` | `results/visualizations/pipeline2_alternative_rdm/` |
| `viz_closure_ground_plot.py` | z-score composite loss landscape PNGs |
| `viz_closure_rdm_compare.py` | PCA vs SRM-cos vs SRM-disparity comparison PNGs |
| `stim_lab_render.py` | STIM_LAB rendering helper (lib for p2_*). |
| `../make_loss_pipeline_v9.py` | loss-pipeline schematic figure (repo root). |
| `../make_meeting_pptx.py`, `revise_ppt_s18.py` | meeting deck generator / s18 patch (repo root + scripts). |

## §7 Phase 3 prep (forward-looking, not closure)

| Script | Role |
|---|---|
| `exp2_compute_preimage.py` | A13 pre-image for exp2 deployment → `results/exp2_preimage/sub-{ID}_2component_preimage.json`. |

## §8 Active diagnostics (cited in `_ACTIVE.md`)

| Script | Role |
|---|---|
| `cycle7b_srm_diagnostic.py` | δθ=0 baseline SRM 5-cell diagnostic. |
| `cycle7c_pca_diagnostic.py` | δθ=0 baseline PCA mirror of cycle7b. |
| `diagnostics/cardinal_axis_amplitude.py` | cardinal-axis amplitude check. |

## §9 Deprecated / superseded — retained for git history & audit

Already archived under `scripts/_archive_pre_closure/<category>/` (s5–s9 sprints,
pre-v6 Phase B, older forwards, phase_c/d predecessors, pipeline3) and
`scripts/_archive/` (cleanup_2026-05-18, cleanup_2026-05-19, zombie_cycle12).
Subpackage dead code under `diagnostics/_archive/`, `filter_ops/_archive/`,
`inventory/_archive/`. `s12b_phase_c_v2.py` kept at root for the §5.3 L8 audit only.
Full disposition table: [`_ACTIVE.md`](_ACTIVE.md) §Inactive.

---

## Execution guide

```bash
conda activate srm        # local; all inputs local

# ── A. Main 5-step pipeline (reproduce candidates) ────────────────
python scripts/s10a_precondition.py
python scripts/s10b_v6_pca_rdm.py --subject sub-08
python scripts/s10b_v6_pca_rdm.py --subject sub-09
python scripts/s17_hc_loo.py
python scripts/cycle6b_extended_raw_weight.py
python scripts/s13_round3.py

# ── B. Held-out predictive test-loss (after s17) — closure Test 3 ─
python scripts/s18_heldout_predictive.py        # ~12s, selected candidates → s10_inclusion/s18_*
python scripts/s19_allcandidate_heldout.py      # ~3min, ALL gate-passing candidates → s19_*

# ── C. Closure verification (redteam → closure.md) ────────────────
python scripts/param_recovery_voxel.py
python scripts/null_within_hc_loo.py
python scripts/null_label_permutation.py
python scripts/null_label_permutation_block.py
python scripts/analyze_verification.py          # verdict matrix
python scripts/build_uncertainty_summary.py     # uncertainty summary

# ── D. Figures ────────────────────────────────────────────────────
python scripts/fig_candidates_param_space.py
python scripts/fig_specificity_summary.py
python scripts/p2_primary_4col.py
python scripts/p2_alternative_rdm_4col.py
```

Outputs are flat under `../results/<analysis_name>/` (no timestamp subdirs;
per-subject `sub-{ID}_*.json`; one `config.json` per output dir — see
[`../CLAUDE.md`](../CLAUDE.md) §7).

## Closure-consistency self-check

A script is closure-consistent iff it uses the `two_comp` forward, **not** the
`forward_models/two_component.py` frozen H_BASE variant (A13):

```bash
grep -E "from two_comp import|from forward_models.two_component import" scripts/<X>.py
```
```python
from two_comp import forward_2comp
# current main candidates (S08-robust, S09-primary):
assert tuple(forward_2comp(6, -42, 'deutan').round(2)) == \
    (36.37, 15.11, -15.0, -36.33, -36.37, -15.11, 15.0, 36.33)   # S08-robust
assert tuple(forward_2comp(2, 24, 'protan').round(2)) == \
    (23.07, 22.41, 8.62, -10.22, -23.07, -22.41, -8.62, 10.22)   # S09-primary
```
