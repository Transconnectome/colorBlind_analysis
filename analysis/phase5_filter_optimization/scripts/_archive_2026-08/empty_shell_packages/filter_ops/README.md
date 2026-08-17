# filter_ops/

Candidate loss/model variants explored as alternatives to the canonical 2-comp standalone Phase 2 BEST. Retained for paper comparison; **not in the canonical pipeline**.

## Contents

### Alternative filter forms (paper Discussion)
- `render_rc_2stage_4col.py` — 4-col viz for R+C 2-stage filter form (rejected per Check 4 empirical falsification; R+C retained as etiology *diagnostic* only)
- `voxel_level_fit.py` — Phase 4 preview: voxel-level direct MSE between HC-pool encoder prediction and CVD-observed Y at shifted angles. Failed pre-committed criteria for both subjects → supports "neural fit ≠ behavioral filter quality" Discussion claim.

### Filter design/feasibility checks
- `loco_filter_derive.py` — Filter derivation from fitted (β_s, β_c)
- `loco_filter_feasibility.py` — Feasibility checks
- `compare_2component_loco.py` — Cross-model comparison utility
- `evaluate_preimage_filter.py` — Pre-image filter evaluation

### Cortical signature descriptive (paper supporting)
- `multi_roi_confusion_diagnostic.py` — Per-pair cc-matrix z-scores across V1/V2/V4 (sub-08 cyan-violet z=+2.49, sub-09 green-violet z=+3.13 at V4; not a CVD-vs-HC test, descriptive direction-of-confusion only)

## What goes here vs root vs _archive

- **scripts/ root**: canonical pipeline (`loco_distortion_fit.py` + its imports + `render_loco_canonical_4col.py`)
- **filter_ops/** (this directory): alternative filter forms and supporting cortical-signature descriptives that the paper compares against the BEST
- **_archive/cleanup_2026-05-19_scripts_root/**: deprecated/exploratory/sub-10-excluded scripts removed from active paper consideration
