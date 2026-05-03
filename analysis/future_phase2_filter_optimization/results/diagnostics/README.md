# diagnostics/ — Ad-hoc diagnostic analyses

**Status**: ACTIVE (multiple sub-analyses)
**Last update**: 2026-05-04 (regrouped from top-level)

## Subdirs

- `decoder_loco/` — ForwardEncoding LOCO confusion matrices per CVD subject. Used by behav cross-modal analysis.
- `srm_integrated_loco/` — SRM + LOCO integrated analysis (Apr 12). `summary.json` has hV4 LOCO + V1/V2 ΔRDM.
- `srm_precompute/` — HC-only SRM W/A precomputed caches.
- `loco_confusion_direction/` — LOCO confusion direction extraction (per-subject confusion bias).
- `filter_validation_2comp_vs_rc/` — Filter comparison: 2-comp vs R+C swatches + sweep (Apr 7). (was `validation_2component/`)
- `cycle_math_framework/` — Math framework experiments. Single script ref.

These are auxiliary analyses that informed but don't directly produce filters.
