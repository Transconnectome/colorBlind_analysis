# visualizations/ — All filter swatches, color geometry, diagnostics

**Status**: ACTIVE
**Last update**: 2026-05-03

## Subdirs

- `filter_visualization/` — Per-subject filter swatches (4-column: original/CVD-perceives/filter/CVD-of-filter)
  - `filter_viz_sub-08_2comp.png` — sub-08 Phase A canonical (38, -14)
  - `filter_viz_sub-09_2comp.png` — sub-09 Phase A canonical (6, -22)
  - `filter_viz_sub-08_c8variants.png` — sub-08 c8 magenta variants (290/300/310°)
  - `filter_viz_sub-09_c8variants.png` — sub-09 c8 variants (preemptive)
  - `filter_viz_sub-09_mwjaccard.png` — **sub-09 mw_jaccard winner (44, +54)**
- `filter_visualization_phase3/` — cycle10d/cycle12 candidates (3-way for sub-08, sub-09)
- `color_structure/` — hV4 color geometry
- `loco_decomposition/` — LOCO error analysis
- `diagnostic_protan_vs_deutan/` — protan/deutan baseline diagnostics
- `literature_convergence/` — comparison with prior literature

Generator: `scripts/visualize_filter_candidates.py`, `scripts/sub08_c8_variants_viz.py`, `scripts/sub09_mwjaccard_viz.py`
