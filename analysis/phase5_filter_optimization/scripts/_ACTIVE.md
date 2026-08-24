# `scripts/` — Closure-Active Index

**Source of truth**: [`../PIPELINE_2_CLOSURE.md`](../PIPELINE_2_CLOSURE.md) (2026-05-27).
**Last sync**: 2026-05-28.

This index lists the scripts that PIPELINE_2_CLOSURE.md cites as part of the
5-step Phase B v6 pipeline. Anything not on this list is *not* part of the
closure flow — even if it sits in `scripts/` root. See [§Inactive](#inactive)
for the disposition of legacy files.

---

## Closure forward (single source of truth)

| File | Role |
|---|---|
| **[`two_comp.py`](two_comp.py)** ★ | 2-Component forward (raw CIElab nominal-θ). Imported by every closure step. Do not replace with the h_base variant. |
| [`rc_1dof.py`](rc_1dof.py) | R+C forward (1-DOF gain `g` × per-source Δλ). |

⚠ `forward_models/two_component.py` exists but is **NOT** used by the closure
(`loco_distortion_fit.py` is the sole live caller). At the same (β_s, β_c)
the two forwards give different δθ 8-vec. See CLAUDE.md A13.

---

## 5-step closure pipeline (per PIPELINE_2_CLOSURE.md §1–§5)

| Step | Script | Closure section | Output |
|---|---|---|---|
| 1. Model · loss precondition | [`s10a_precondition.py`](s10a_precondition.py) | §Step 1 | `results/s10_inclusion/precondition_table.json` |
| 2. Atom + cell enumeration | [`s10b_v6_pca_rdm.py`](s10b_v6_pca_rdm.py) (`build_cells` block) | §Step 2 | enumerated in the v6 output JSON |
| 3. Fit + HC subset evaluation (main) | [`s10b_v6_pca_rdm.py`](s10b_v6_pca_rdm.py) ★ | §Step 3.1–3.5 | `results/s10_inclusion/s10b_v6_pca_rdm_results_{sub-08,sub-09}.json` |
| 3. Strict HC LOO supplement | [`s17_hc_loo.py`](s17_hc_loo.py) | §Step 3 supplement | `results/s10_inclusion/s17_hc_loo_results.json` (gitignored) |
| 4. Raw-weight robustness | [`cycle6b_extended_raw_weight.py`](cycle6b_extended_raw_weight.py) | §Step 4 | `results/s10_inclusion/cycle6b_extended_composite_{sub-08,sub-09}.json` |
| 5. Phase D Round 3 identifiability | [`s13_round3.py`](s13_round3.py) | §Step 5.2 | `results/s13_multipoint_sim/s13_round3_recovery.json` |

## Appendix A — RDM atom robustness (PIPELINE_2_CLOSURE §A)

| Script | Role |
|---|---|
| [`s10b_v6_srm_rdm.py`](s10b_v6_srm_rdm.py) | SRM-cosine RDM atom variant |
| [`s10b_v6_srm_disparity.py`](s10b_v6_srm_disparity.py) | SRM Procrustes disparity atom variant |
| [`cycle7b_srm_diagnostic.py`](cycle7b_srm_diagnostic.py) | δθ=0 baseline SRM 5-cell diagnostic |
| [`cycle7c_pca_diagnostic.py`](cycle7c_pca_diagnostic.py) | δθ=0 baseline PCA mirror of cycle7b |
| [`compare_primary_candidates.py`](compare_primary_candidates.py) | 3-way comparison runner |

## Test 3 — Held-out predictive test-loss (closure.md §Test 3, 2026-06-02)

| Script | Role | Output |
|---|---|---|
| [`s18_heldout_predictive.py`](s18_heldout_predictive.py) | leave-one-HC-out 7-fold test-loss (ΔL vs no-correction) + standalone fits — **selected** candidates | `results/s10_inclusion/s18_heldout_predictive.{json,md}` (+ `s18_INTERPRETATION.md`) |
| [`s19_allcandidate_heldout.py`](s19_allcandidate_heldout.py) | same metric across **all gate-passing** candidates; cross-candidate rank by grid-null percentile (corroboration, NOT re-selection §0) | `results/s10_inclusion/s19_allcandidate_heldout.{json,md}` |

Finding: held-out goodness non-discriminative (45° categorical quantization → ±~22.5°
plateau ≈ Test 2a floor); selected values top-tier but value not pinned. Phase 3 =
behavioral/neural efficacy of the specific selected value (not point-precision).

## Visualization (closure-consistent)

| Script | Output | Forward used |
|---|---|---|
| [`p2_primary_4col.py`](p2_primary_4col.py) | `results/visualizations/pipeline2_primary_4col/` (3 primary + 1 summary PNG) | closure (`two_comp.py`) ✓ |
| [`stim_lab_render.py`](stim_lab_render.py) | helper for STIM_LAB rendering | n/a |

Other viz under `scripts/visualization/` and `scripts/*.py` were authored
before the 2026-05-27 forward audit; many use the h_base / frozen variant
and therefore display δθ inconsistent with the closure. They are **not**
listed here; see [§Inactive](#inactive).

**2026-05-28 (Phase B')**: `scripts/visualization/` now contains 7 paper-figure
generators kept at root (cited by `mathematical_basis.md` / `presentation/`):
`figs_2comp_anatomy`, `figs_2comp_stretch`, `figs_activation_overview`,
`figs_loss_inventory`, `figs_model_vs_baseline`, `figs_rc_panels`,
`figs_slide5_rc_panels`. The other 12 viz scripts moved to
`visualization/_archive/` (broken deps or forward inconsistency).
`scripts/diagnostics/` keeps only `cardinal_axis_amplitude.py` at root; the
other 16 + all 5 in `inventory/` + all 7 in `filter_ops/` moved to their
respective `_archive/`. `sbatch/_archive/` and `logs/_archive/` hold stale
SLURM jobs and pre-v6 run logs.

## Deprecated but retained for L8 audit

| Script | Reason kept |
|---|---|
| [`s12b_phase_c_v2.py`](s12b_phase_c_v2.py) | Phase C v2 seed sharing audit (PIPELINE_2_CLOSURE §5.3 L8). Did not contribute to final selection. |

---

## Closure helpers (transitive deps imported by the above)

| File | Used by | What it provides |
|---|---|---|
| [`neural_loss.py`](neural_loss.py) | `s10b_v6_pca_rdm`, `s17_hc_loo` | `L_LOCO`, `L_RDM`, `precompute_loco_W_within` |
| [`s8_loo_train_test.py`](s8_loo_train_test.py) | `s10a_precondition`, `s10b_v6_pca_rdm`, `s17_hc_loo`, `s12b_phase_c_v2` | `jnd_baseline_from_pool`, `DELTA_LAMBDA_BY_FAMILY` |
| [`machado_simulator.py`](machado_simulator.py) | `rc_1dof.py`, viz | Machado-Smith cone-shift fundamentals |
| `../phase4_forward_model/scripts/utils_forward_model.py` | most closure scripts | `create_basis_full`, `HUE_ANGLES` (external dep — Phase 1 module) |

These helpers are **not** standalone closure entry-points but cannot be
removed without breaking the closure scripts.

---

## Inactive

The following families live in `scripts/` root or its subdirectories but
are **not** part of the closure. They are retained for git history and
future audit, but should be treated as superseded:

| Family | Disposition per closure |
|---|---|
| `s5_*.py`, `s5p_*.py`, `s6_*.py`, `s6p_*.py`, `s7_*.py`, `s7b_*.py`, `s7c_*.py`, `s8_analysis.py`, `s8_selection_xsubtype_perm.py` | Pre-Phase B v6 sprints; superseded by §Step 1–5. |
| `s10b_v2_resample.py`, `s10b_v3_extended.py`, `s10b_v4_single_atom.py`, `s10b_v5_gamma_all.py` | Earlier Phase B versions; replaced by v6. |
| `s10c_sub09_cosine.py`, `s10d_sub09_weight_sweep.py`, `refit_sub09_lambda_sweep.py`, `analyze_jnd_sub09.py`, `run_sub08_protan_audit.py` | Per-subject one-offs, absorbed into v6. |
| `s11_*.py`, `s12_phase_c_weight_sweep.py`, `s14_atom_redesign.py` | Phase C / atom-redesign predecessors; PIPELINE_2_CLOSURE §Files marks them deprecated. |
| `s10b_cross_roi.py`, `s10b_inclusion_ranking.py` | Cycle 12 REJECTED per CLAUDE.md §5. |
| `s15_oos_reanalysis.py`, `s16_e2_srm_disparity.py` | Pipeline 3 (deprecated per PIPELINE_2_CLOSURE §Pipeline 3 status). |
| `s13_multipoint_validation.py` | Round 1/2 predecessor; `s13_round3.py` supersedes. |
| `c3_relabel_both_subjects.py`, `c3_relabel_p2a.py` | Label scheme — pre-2026-05-16 13-bin SUPERSEDED (project memory `feedback_label_scheme_cutoff`). |
| `step1_fit_loco_v2.py`, `retinal_cortical.py`, `rc_opponent_1dof.py`, `lambda_3source.py`, `landscape_loader.py`, `s10_advisor_fixes.py`, `cycle6_raw_weight.py`, `s9_retroactive_defenses.py`, `fit_sigma_hc_8afc.py` | Older forwards / ad-hoc diagnostics absorbed into closure. All nine are already in `_archive_pre_closure/` with zero live importers (verified 2026-08-05). |
| `forward_models/` (`two_component.py`, `three_component.py`, `opponent_gain.py`, `rc_2stage.py`) | Frozen `H_BASE` variant — sign-flipped δθ vs the closure forward at identical (β_s, β_c). Moved to `_archive_2026-08/frozen_forward_variant/` on 2026-08-05. Its only importer, `results/redteam/exp1_a13_forward_audit.py`, imports it *deliberately* to document the mismatch and was repointed in the same commit. |
| `loco_distortion_fit.py` | Alternative entry — uses frozen H_BASE variant from `forward_models/two_component.py`. Not called by closure. |

> **⚠ 2026-08-05 correction.** This table previously listed `behav_loss.py`,
> `utils_distortion_models.py`, and `diagnostic_delta_rdm.py` as inactive. That
> was wrong: the canonical fitter imports all three
> (`s10b_v6_pca_rdm.py:30,36,37`; 14 / 2 / 5 live importers respectively).
> They are **core library** — see `README.md` §1, which had it right. Trust
> `README.md` §1 over this section where the two disagree.
| `render_loco_canonical_4col.py`, `s5_tregillus_viz_4col.py`, `s5_viz_behav_4col.py`, `s7_best_models_4col.py` | Pre-2026-05-27 viz using h_base / frozen forward — display δθ inconsistent with closure. Use [`p2_primary_4col.py`](p2_primary_4col.py) instead. |
| `scripts/visualization/visualize_phase3_preimage.py` | File header marks itself DEPRECATED (frame mismatch). Do not regenerate from this. |
| `scripts/visualization/visualize_filter_candidates.py` | Forward not yet audited; treat as suspect until verified to match closure. |

Phase B (file-move reorganization) will relocate these into
`scripts/_archive_pre_closure/<category>/` under user approval. Currently
they remain at root to avoid `git mv` until that phase is approved.

---

## How to confirm a script is closure-consistent

```bash
# At repo root for this project:
grep -E "from two_comp import|from forward_models.two_component import" \
    scripts/<your_script>.py
```

- `from two_comp import forward_2comp` → ✓ closure-consistent
- `from forward_models.two_component import (anything)` → ✗ frozen / h_base variant; **not** closure

Sanity assertion (paste into REPL or test):
```python
from two_comp import forward_2comp
# current main candidates (S08-robust, S09-primary):
assert tuple(forward_2comp(6, -42, 'deutan').round(2)) == \
    (36.37, 15.11, -15.0, -36.33, -36.37, -15.11, 15.0, 36.33)   # S08-robust
assert tuple(forward_2comp(2, 24, 'protan').round(2)) == \
    (23.07, 22.41, 8.62, -10.22, -23.07, -22.41, -8.62, 10.22)   # S09-primary
```
