# filter_ops/_archive/ — Pre-closure filter operation scripts

7 scripts moved 2026-05-28 (Phase B'). All depend on modules archived in
Phase B (`loco_distortion_fit`, `step1_fit_loco_v2`, `c3_relabel_*`) or
import the frozen H_BASE forward (`forward_models.two_component`, NOT
closure). None is referenced by any active doc.

| File | Reason |
|---|---|
| `compare_2component_loco.py` | LOCO-based comparison; closure §0 specificity claim 금지 |
| `evaluate_preimage_filter.py` | Imports archived `step1_fit_loco_v2` |
| `loco_filter_derive.py` | Imports archived `loco_distortion_fit`, `step1_fit_loco_v2` |
| `loco_filter_feasibility.py` | Closure §5.2 identifiability FAIL — feasibility analysis obsoleted |
| `multi_roi_confusion_diagnostic.py` | Cross-ROI loss → Cycle 11/12 REJECTED |
| `render_rc_2stage_4col.py` | Imports archived `c3_relabel_p2a`, `c3_relabel_both_subjects`; R+C 2-stage as filter form deprecated 2026-05-16 (per CLAUDE.md §3) |
| `voxel_level_fit.py` | "Phase 4 preview" — never absorbed into closure |

Closure-consistent filter operations: pre-image solver lives inline in
`scripts/p2_primary_4col.py` (`pre_image_closure`); forward at
`scripts/two_comp.py:forward_2comp`.
