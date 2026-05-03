# Results Layout — Phase 2 Filter Optimization

Last updated: 2026-05-04 (full restructure: 15 dirs → 7 semantic categories)

## New top-level structure

```
results/
├── MANIFEST.md                          this file
│
├── inventory/                           CROSS-CUTTING SUMMARIES
│   ├── loss_inventory.{md,csv}             12+ loss × HC sanity table
│   ├── consolidated_phase2_results.{csv,json}  Cycle 10d 48-row aggregate
│   └── consolidated_cross_roi.csv          Cycle 11 9-pair × 2-family
│
├── fits/                                ALL MODEL FITS (was loco_filter + 2component_v2 + step2c_*)
│   ├── phase_a/                            Machado, R+C, fourier_warp (CVD)
│   ├── phase_a_2component/                 2-component fits (CVD)
│   ├── phase_a_2component_finegrid/        sub-08 fine grid (B1)
│   ├── phase_a_2component_hc_sanity/       HC fits (PARTIAL — server pending)
│   ├── phase_a_v2/, phase_b_v2/            older variants — keep for ref
│   ├── phase_a_test/                       test outputs
│   ├── canonical_2component_v2/            (was 2component_comprehensive_v2)
│   ├── canonical_rc_opponent_v2/           (was step2c_retinal_cortical_v2)
│   ├── preimage/                           opponent-convention pre-images
│   ├── preimage_2component/                opponent-convention 2-comp pre-images
│   └── roi_hierarchy/                      cross-ROI agreement
│
├── cycles/                              CYCLE 1~15 OUTPUTS (was cycle_filter_refinement)
│   ├── sub-XX_ROI_landscape.json           per (subject, ROI) metric grids
│   ├── cycle12_loss_cross_roi.{json,csv}   V4 l_topk + V1 l_rank
│   ├── cycle14_v1_rdm_cross.{json,csv}     V4 l_topk + V1 ΔRDM cosine
│   ├── cycle15_mwjaccard_cross.{json,csv}  ★ Cycle 15 — current winner
│   ├── cycle{1..13}_*.json/csv             per-cycle aggregates
│   ├── bootstrap/, bootstrap_server/       bootstrap CIs
│   └── cycle{6,8}_*/                        sub-analyses
│
├── visualizations/                      ALL VIZ (was figures)
│   ├── filter_visualization/               sub-08, sub-09 candidate filter swatches
│   ├── filter_visualization_phase3/        cycle10d/cycle12 candidates (3-way)
│   ├── color_structure/, loco_decomposition/
│   └── diagnostic_protan_vs_deutan/
│
├── diagnostics/                         AD-HOC DIAGNOSTIC ANALYSES
│   ├── decoder_loco/                       ForwardEncoding LOCO confusion (was results/decoder_loco)
│   ├── srm_integrated_loco/                SRM + LOCO (was results/srm_integrated_loco)
│   ├── srm_precompute/                     HC SRM W/A caches
│   ├── loco_confusion_direction/           Confusion direction extraction
│   ├── filter_validation_2comp_vs_rc/      (was validation_2component)
│   └── cycle_math_framework/               Math framework experiments
│
├── older_cycles/                        OLDER CYCLE WORK (referenced by current scripts)
│   ├── cycle_loss_redesign/                cycle 4 alt metrics
│   └── cycle_bootstrap/                    older bootstrap (Apr 29)
│
└── _archive/                            DELETION CANDIDATES (audit pending)
    ├── paper_figures/                      orphaned timestamp dir
    └── validation_v2/                      superseded by validation_2component
```

## Migration log (2026-05-04)

| Old path | New path | Reason |
|---|---|---|
| `loco_filter/` | `fits/` | Semantic clarity |
| `cycle_filter_refinement/` | `cycles/` | Shorter |
| `figures/` | `visualizations/` | Standard naming |
| `2component_comprehensive_v2/` | `fits/canonical_2component_v2/` | Group with fits |
| `step2c_retinal_cortical_v2/` | `fits/canonical_rc_opponent_v2/` | Group with fits |
| `decoder_loco/` | `diagnostics/decoder_loco/` | Group diagnostics |
| `srm_integrated_loco/` | `diagnostics/srm_integrated_loco/` | Group diagnostics |
| `srm_precompute/` | `diagnostics/srm_precompute/` | Group diagnostics |
| `loco_confusion_direction/` | `diagnostics/loco_confusion_direction/` | Group diagnostics |
| `validation_2component/` | `diagnostics/filter_validation_2comp_vs_rc/` | Renamed for clarity |
| `cycle_math_framework/` | `diagnostics/cycle_math_framework/` | Group diagnostics |
| `cycle_loss_redesign/` | `older_cycles/cycle_loss_redesign/` | Pre-Cycle 9 |
| `cycle_bootstrap/` | `older_cycles/cycle_bootstrap/` | Older bootstrap workflow |
| `loss_inventory.{md,csv}` | `inventory/loss_inventory.{md,csv}` | Group cross-cutting |
| `cycle_filter_refinement/consolidated_*` | `inventory/consolidated_*` | Group cross-cutting |

All Python scripts (~50 files) updated to use new paths via sed migration.

## Design Philosophy

- **`inventory/`**: cross-cutting summaries used across cycles
- **`fits/`**: anything that runs the canonical L_LOCO / phase_a fitting
- **`cycles/`**: cycle 1~15 selection-rule reformulation work
- **`diagnostics/`**: ad-hoc analyses (HC specificity, decoder confusion, SRM, etc.)
- **`older_cycles/`**: pre-Cycle 9 workflows still referenced by current scripts
- **`_archive/`**: superseded; audit before deletion
- **Each subdir has its own `README.md`** with: purpose, last-updated, generator script
