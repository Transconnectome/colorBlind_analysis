# visualization/_archive/ — Pre-closure visualization scripts

12 scripts moved here on 2026-05-28 (Phase B' follow-up). Each was excluded
from KEEP because (a) no active doc cites it positively, or (b) it imports
a module that Phase B archived (broken dep), or (c) it uses a forward map
inconsistent with PIPELINE_2_CLOSURE.md (raw nominal-θ via `scripts/two_comp.py`).

## Files and reasons

| File | Reason |
|---|---|
| `figs_emery_factor4.py` | No active doc citation (literature comparison; superseded by p2_primary_4col output) |
| `visualize_4ring_wheel.py` | No citation; closure does not use 4-ring viz |
| `visualize_color_structure.py` | No citation |
| `visualize_cone_shift_colors.py` | No citation; Machado cone-shift colors only |
| `visualize_filter_candidates.py` | Imports archived `retinal_cortical`; uses frozen H_BASE forward (NOT closure); `_ACTIVE.md` marks as suspect |
| `visualize_filter_comparison.py` | No citation; filter comparison superseded by p2_primary_4col |
| `visualize_hc_specificity.py` | No citation; closure §0 forbids HC specificity claim |
| `visualize_literature_convergence.py` | No citation |
| `visualize_loco_decomposition.py` | Uses `machado_shifted_hue` h_base (NOT closure forward) |
| `visualize_phase3_preimage.py` | File header marks itself DEPRECATED 2026-05-10; uses frozen forward; `_ACTIVE.md` and `results/README.md` cite it as "do not regenerate from this" |
| `visualize_preimage_3losses.py` | No citation; pre-image alternatives subsumed by p2_primary_4col |
| `visualize_preimage_filter.py` | No citation; same as above |

## KEEP (parent dir)

The 7 figs cited by `mathematical_basis.md` and `presentation/` remain at
`scripts/visualization/`:
`figs_2comp_anatomy`, `figs_2comp_stretch`, `figs_activation_overview`,
`figs_loss_inventory`, `figs_model_vs_baseline`, `figs_rc_panels`,
`figs_slide5_rc_panels`.

Closure-consistent 4-col viz: `scripts/p2_primary_4col.py` (root).
