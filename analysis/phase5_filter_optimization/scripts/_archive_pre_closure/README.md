# `_archive_pre_closure/` — Pre-closure scripts (Phase B reorg 2026-05-28)

68 scripts moved out of `scripts/` root because they are **not** reachable
from any closure entry-point in [`../../PIPELINE_2_CLOSURE.md`](../../PIPELINE_2_CLOSURE.md) (2026-05-27).
Each category lists the absorbing closure step or the reason the work was
superseded. Files are retained for git history, paper-level limitation
audits, and re-running historical analyses if needed.

**Reachability test used**: BFS from 12 closure entry scripts (Steps 1–5
+ Appendix A + closure-consistent viz) over the `from X import …` /
`import X` graph. Every file in this directory is unreachable from that
seed set, and no script under `../visualization/`, `../diagnostics/`,
`../inventory/`, `../filter_ops/` imports any file here (subdir cascade = 0).

**Post-move smoke test** (2026-05-28):
- `forward_2comp(38, −10, 'deutan').round(2) == [+8.66, +29.46, +33.0, +17.21, −8.66, −29.46, −33.0, −17.21]` ✓ (closure δθ sentinel)
- 12 closure entries import 0 failures ✓
- `p2_primary_4col.py` regenerates 4 PNGs ✓

---

## Categories

### `pre_v6_phase_b/` (6) — Phase B versions before v6
`s10b_v2_resample`, `s10b_v3_extended`, `s10b_v4_single_atom`, `s10b_v5_gamma_all`,
`s10b_cross_roi`, `s10b_inclusion_ranking`.
Replaced by `s10b_v6_pca_rdm.py` (Step 2+3 main runner).
`s10b_cross_roi` / `s10b_inclusion_ranking` are Cycle 12 REJECTED per `../../CLAUDE.md` §5.

### `pre_v6_sub09/` (5) — sub-09 / sub-08 one-off audits
`analyze_jnd_sub09`, `refit_sub09_lambda_sweep`, `run_sub08_protan_audit`,
`s10c_sub09_cosine`, `s10d_sub09_weight_sweep`.
Absorbed into v6 per-subject cell enumeration.

### `s5_sprint/` (12) — Sprint 5 (Tregillus / spearman / hc-pool)
Includes `s5_tregillus_*`, `s5_spearman_*`, `s5p_hc_pool_*`, `s5_*_viz_*`.
Pre-Phase-B-v6 sprint; superseded by closure Steps 2–3.

### `s6_sprint/` (4) — Sprint 6 (bootstrap g CI, HC subset resample)
`s6_bootstrap_g_ci{,_trial}`, `s6p_compare`, `s6p_hc_subset_resample`.
Bootstrap framework superseded by v6 5/2 subset resampling.

### `s7_sprint/` (13) — Sprint 7 (loss-combo + lambda + nested LOO + 4-col viz)
Includes `s7_loss_combo_subset`, `s7_lambda_optimal`, `s7_nested_loo*`,
`s7_best_models_4col`, `s7c_rc_vs_2comp_agreement`, etc.
`s7_best_models_4col.py` used the h_base / frozen forward and is therefore
inconsistent with the closure — see `../_ACTIVE.md` ⚠ note.

### `s8_sprint/` (2) — Sprint 8 (cross-subtype perm)
`s8_analysis`, `s8_selection_xsubtype_perm`.
Note: `s8_loo_train_test.py` is **NOT** archived (closure helper, lives in root).

### `s9_sprint/` (1) — Sprint 9 (retroactive defenses)
`s9_retroactive_defenses`. Not part of v6 pipeline.

### `phase_c_predecessors/` (7) — Phase C trials before v2 was stabilized
`s11_constrained_null_v3{,b}`, `s11_diagnose_{multi_iter,null_v3}`,
`s11_pre_phase_c_null_sim{,_v2}`, `s12_phase_c_weight_sweep`.
PIPELINE_2_CLOSURE retains only `s12b_phase_c_v2.py` (root) as L8 audit.

### `phase_d_predecessors/` (1) — Phase D Rounds 1–2
`s13_multipoint_validation`. Superseded by `s13_round3.py` (root).

### `cycle5_atom/` (1) — Cycle 5 atom redesign
`s14_atom_redesign`. Absorbed into v6 PCA-RDM atom (per CLAUDE.md §5).

### `pipeline3_deprecated/` (2) — Pipeline 3 (deprecated per closure)
`s15_oos_reanalysis`, `s16_e2_srm_disparity`.
PIPELINE_2_CLOSURE §Pipeline 3 status note: "Pipeline 3 의 별도 후속 작업 없음."

### `c3_relabel_superseded/` (2) — pre-2026-05-16 label scheme
`c3_relabel_both_subjects`, `c3_relabel_p2a`.
Project memory `feedback_label_scheme_cutoff`: pre-2026-05-16 13-bin scheme SUPERSEDED.

### `older_forwards/` (6) — older forward models (NOT closure forward)
`step1_fit_loco_v2`, `retinal_cortical`, `rc_opponent_1dof`, `lambda_3source`,
`landscape_loader`, `loco_distortion_fit`.
Note: `loco_distortion_fit.py` is the sole live caller of
`scripts/forward_models/two_component.py` (frozen H_BASE alternative entry,
NOT closure forward — see `../../CLAUDE.md` A13).

### `ad_hoc/` (3) — One-off scripts
`s10_advisor_fixes`, `cycle6_raw_weight`, `fit_sigma_hc_8afc`.
`cycle6_raw_weight` superseded by `cycle6b_extended_raw_weight.py` (root, Step 4).

### `older_viz/` (1) — Pre-closure 4-col viz (h_base forward)
`render_loco_canonical_4col`. Uses the frozen H_BASE variant — output δθ
inconsistent with closure. Replaced by `p2_primary_4col.py` (root).

### `comparator_v6_extra/` (2) — Extra v6 comparison runners
`compare_pca_vs_srm_v6`, `compare_three_v6`.
PIPELINE_2_CLOSURE references only `compare_primary_candidates.py` (root)
for Appendix A.

---

## How to revert

Each file was moved with `git mv` (history preserved), except the two
untracked files in `comparator_v6_extra/` which used `mv`. To revert:

```bash
# Phase B reorganization is one git stash/commit. Revert with:
git checkout HEAD~1 -- scripts/   # if Phase B is the previous commit
# or
git mv scripts/_archive_pre_closure/<cat>/<file>.py scripts/<file>.py
```
