# Results Layout — Phase 2 Filter Optimization

Last updated: 2026-05-03 (cleanup: archived `paper_figures/`, `validation_v2/` → `_archive/`)

## Design Philosophy

- **Active dirs**: referenced by current analysis workflows (CLAUDE.md, behav_validation.md, action_plans/).
- **`_archive/`**: completed/superseded; moved out of main path. Deletion candidates pending user audit.
- **Each subdir has a README.md** with: purpose, last-updated, current/deprecated status, generator script.

## Current top-level layout

```
results/
├── MANIFEST.md                          this map (you are here)
├── loss_inventory.md / .csv             Loss variant × HC sanity table (NEW 2026-05-03)
│
├── _archive/                            superseded dirs (audit before deletion)
│   ├── paper_figures/                      orphaned timestamp dir
│   └── validation_v2/                      superseded by validation_2component
│
├── loco_filter/                         **CORE** — phase A fits + pre-images
│   ├── phase_a/                            Machado, R+C, fourier_warp fits (CVD)
│   ├── phase_a_2component/                 2-component fits (CVD)
│   ├── phase_a_2component_finegrid/        sub-08 fine grid (B1, 2026-05-03)
│   ├── phase_a_2component_hc_sanity/       HC fit (PARTIAL — pending server re-run)
│   ├── phase_a_v2/, phase_b_v2/            older variants — keep for reference
│   ├── phase_a_test/                       test outputs
│   ├── preimage/                           opponent-convention pre-images
│   ├── preimage_2component/                opponent-convention pre-images (2-comp)
│   └── roi_hierarchy/                      cross-ROI agreement
│
├── cycle_filter_refinement/             **CORE** — Cycle 1~15 outputs
│   ├── sub-XX_ROI_landscape.json           per (subject, ROI) metric grids
│   ├── cycle12_loss_cross_roi.{json,csv}   Cycle 12: V4 l_topk + V1 l_rank
│   ├── cycle14_v1_rdm_cross.{json,csv}     Cycle 14: V4 l_topk + V1 ΔRDM cosine
│   ├── cycle15_mwjaccard_cross.{json,csv}  **Cycle 15** (NEW): mw_jaccard cross variants
│   ├── consolidated_phase2_results.csv     Cycle 10d aggregate (48 rows)
│   ├── consolidated_cross_roi.csv          Cycle 11 9-pair × 2-family
│   └── cycleX_*.json                       per-cycle aggregates
│
├── 2component_comprehensive_v2/         Canonical 2-comp fits (Apr 7) — viz scripts ref
├── step2c_retinal_cortical_v2/          Canonical R+C fits (Apr 7) — docs ref
├── validation_2component/               Filter comparison: 2-comp vs R+C (Apr 7)
│
├── figures/                             ALL viz output
│   ├── filter_visualization/               Sub-08, Sub-09 candidate filter swatches
│   │   ├── filter_viz_sub-XX_2comp.png     Phase A LOCO best
│   │   ├── filter_viz_sub-08_c8variants.png c8 magenta variants (B2, 2026-05-03)
│   │   ├── filter_viz_sub-09_c8variants.png
│   │   └── filter_viz_sub-09_mwjaccard.png mw_jaccard winner candidate (NEW)
│   ├── filter_visualization_phase3/        cycle10d/cycle12 candidates (3-way)
│   ├── color_structure/, loco_decomposition/, etc.
│   └── diagnostic_protan_vs_deutan/
│
├── decoder_loco/                        ForwardEncoding LOCO confusion matrices
├── srm_integrated_loco/                 SRM+LOCO integration (Apr 12)
├── srm_precompute/                      HC SRM W/A caches
├── loco_confusion_direction/            Confusion direction extraction
├── cycle_bootstrap/                     Bootstrap CI computations
├── cycle_loss_redesign/                 Older cycle (referenced by cycle_filter_refinement scripts)
└── cycle_math_framework/                Math framework experiments
```

## Pending future migrations (not yet executed)

Per user agreement 2026-05-03, full restructure to `filter_fits/`, `preimages/`, `cross_roi/`, `diagnostics/`, `visualizations/`, `behavioral/` is planned for future session. Current cleanup limited to:
- Archiving 2 clearly orphaned dirs (`paper_figures/`, `validation_v2/`)
- Adding READMEs (this file + subdirs)
- Documenting current candidate table in top-level `../README.md`
