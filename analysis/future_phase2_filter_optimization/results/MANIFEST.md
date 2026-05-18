# Phase 2 Filter Optimization — Results Manifest

**Last updated**: 2026-05-18 (post-refactor — paper-draft-ready state)

---

## Current Phase 2 Filter (BEST)

| Subject | (β_s, β_c) | perm_p | corrected P2a | Etiology (R+C diagnostic) |
|---|---|---|---|---|
| sub-08 deutan | (38°, −14°) | 0.004 ★★ | 0.750 | cortical-dominant |
| sub-09 protan | (6°, −22°) | 0.035 ★ | 0.975 | retinal-dominant |

**Filter form**: 2-component standalone `δθ = β_s·cos(θ−90°) + β_c·cos(θ−axis°)`
**Loss**: `L_fit = 1.0·L_vuln + 0.5·L_rank + 0.2·L_rdm + 0.1·L_smooth` @ V4 hV4 LOCO
**Source**: `BEST_summary.json`

---

## Directory Structure

```
future_phase2_filter_optimization/
├── CLAUDE.md                   Project instructions (§0 framework, §3 redirects to BEST_summary)
├── README.md                   Project entry
├── raw_behav.md                Behavioral data record
├── mathematical_basis.md       Theory foundation
├── index.md                    Literature positioning
│
├── scripts/                    19 canonical .py at root + 6 subdirs
│   ├── loco_distortion_fit.py     Core fitting (L_fit + grid + perm)
│   ├── machado_simulator.py       Retinal cone shift sim
│   ├── retinal_cortical.py        R+C standalone (diagnostic only, not filter)
│   ├── c3_relabel_p2a.py          NEW labels (9-bin STIM_LAB matching)
│   ├── c3_relabel_both_subjects.py  Per-subject NEW target maps
│   ├── stim_lab_render.py         Color rendering
│   ├── render_loco_canonical_4col.py   BEST viz generator
│   ├── render_rc_2stage_4col.py        R+C 2-stage Phase 4 preview viz
│   ├── multi_roi_confusion_diagnostic.py   Paper finding: V4-specific confusion
│   ├── hc_specificity_check.py    HC LOO bootstrap (descriptive only)
│   ├── diagnostic_delta_rdm.py    ΔRDM diagnostic
│   ├── delta_L_specificity_check.py  HC specificity variant
│   ├── landscape_loader.py        Parquet-backed landscape access
│   ├── consolidate_landscapes_to_parquet.py   30 JSONs → parquet
│   ├── consolidate_phase_a_to_csv.py          70 fit JSONs → CSV
│   ├── step1_fit_loco_v2.py       LOCO simulator (used by loco_distortion_fit)
│   ├── utils_distortion_models.py Forward model utilities
│   ├── p2amax_option_C_visualize.py  Render util (inlined OLD-stub helpers)
│   ├── phase3_candidate_analysis_v2.py  provides pre_image_2comp (with warning header)
│   ├── forward_models/            two_component, three_component, opponent_gain, etc.
│   ├── diagnostics/               18 diagnostic scripts (baseline_ρ, validate_2comp, etc.)
│   ├── filter_ops/                5 filter operation scripts
│   ├── inventory/                 6 inventory builders
│   ├── visualization/             20 figure-generation scripts (figs_*, visualize_*)
│   ├── slurm/                     6 .sh submission scripts
│   └── _archive/                  All archived exploration/cycle scripts (200+ files)
│
└── results/                    (~165 MB, mostly archive)
    ├── BEST_summary.json                                  Canonical filter params
    ├── BEST_4col_sub-{08,09}_V4_LOCO_canonical_*.{png,pdf}  Phase 2 best viz
    ├── MANIFEST.md                                        This file
    ├── SUMMARY.md                                         Phase 2 narrative + closure
    │
    ├── landscapes_consolidated.parquet (2.6M)             30 landscapes → parquet (89.7% reduction)
    ├── phase_a_summary.csv (14K)                          70 fit JSONs → CSV
    ├── smooth_sweep_summary.csv (6K)                      40 ε sweeps → CSV
    │
    ├── CONSOLIDATION_REPORT_2026-05-16.md                 Data consolidation methodology
    ├── LABEL_CLEANUP_PLAN_2026-05-16.md                   OLD-label cleanup record
    ├── multi_roi_confusion.json                           Paper finding: V4-specific confusion
    │
    ├── c3_relabel/                                        NEW-scheme docs + viz
    │   ├── CORRECTED_LOCO_canonical_4col_sub-{08,09}.{png,pdf}   Same as BEST (alt naming)
    │   ├── SCIENTIFIC_NARRATIVE_2026-05-16.md             Forward pipeline writeup
    │   ├── SYNTHESIS_2026-05-16.md                        P2a-max zone synthesis
    │   ├── NEAR_CONTROLS.md                               Rejected candidates record
    │   └── _archive_2026-05-17/                           Track A/B intermediates
    │
    ├── phase4_preview/                                    Phase 4 preview results (NOT for Phase 2 paper)
    │   ├── 3component_joint_oneshot.json                  3-comp joint fit (better neural, worse P2a)
    │   ├── l_dir_one_shot_test.json                       L_dir loss FAIL test
    │   └── 3comp_viz/                                     3-comp 4-col + landscape viz
    │
    ├── fits/                                              Neural fit JSONs (label-independent)
    ├── old_formula/                                       Landscape JSONs (data only, viz archived)
    ├── axis_3way/                                         Stockman axis landscapes
    ├── CANDIDATE/tier2_v4ccc_srm_rdm/                     V4-CCC + SRM RDM landscape
    │
    └── _archive/                                          All archived results
        ├── cleanup_2026-05-17/                              Phase 1 cleanup batch (~28 docs)
        ├── cleanup_2026-05-18/                              Phase 2 cleanup batch (parameter_recovery, sub10_*, etc.)
        └── old_labels_pre_2026-05-16/                       Phase 1 OLD-label era (17 dirs)
```

## Refactor 2026-05-18 summary

**Removed/archived from scripts/**: ~150 files (cycle/exploration/test scripts)
**Kept at scripts/ root**: 19 canonical
**scripts/ subdirs preserved**: forward_models, diagnostics, filter_ops, inventory, visualization, slurm

**Removed/archived from results/**: parameter_recovery/, sub10_diagnostic_*/, unified_pipeline/, today's test JSONs moved to phase4_preview/
**Kept at results/ root**: BEST_summary, BEST viz, MANIFEST, SUMMARY, parquet+CSVs, MD docs, multi_roi_confusion.json
**results/ subdirs preserved**: c3_relabel/, phase4_preview/, fits/, old_formula/, axis_3way/, CANDIDATE/, _archive/, _superseded/

**Total**: scripts/ 1.7 MB, results/ 165 MB (mostly _archive/)

## Phase 2 → 3 → 4 transition

| Phase | Status | Deliverable |
|---|---|---|
| Phase 2 (filter optimization) | **CLOSED** | LOCO-canonical 2-comp filter per subject |
| Phase 3 (behavioral validation) | NEXT | OSF pre-reg + new behavioral acquisition |
| Phase 4 (model class expansion) | PREVIEW | 3-component joint fit (results/phase4_preview/) shows neural-vs-behavioral dissociation |

## Re-generation reference

If a deleted/archived script is needed:
```bash
# Restore from git history
git show HEAD:analysis/future_phase2_filter_optimization/scripts/<name>.py > /tmp/<name>.py

# Or check archive
ls scripts/_archive/cleanup_2026-05-{17,18}/

# Re-generate viz
python scripts/render_loco_canonical_4col.py     # BEST 4-col
python scripts/multi_roi_confusion_diagnostic.py # multi-ROI confusion
python scripts/consolidate_landscapes_to_parquet.py  # parquet refresh
```

## Caveats (per CLAUDE.md §0)

- All filter selection is **descriptive** — specificity claims forbidden under HC FPR=100%
- L_rank artifact (L@id inversion) documented as methodological subtlety (correlation + HC LOO + small n)
- 3-component Phase 4 preview shows: better neural fit, worse P2a (sub-09 Machado c6 wraparound) → 2-comp standalone retained as Phase 2 filter form
- Per-pair V4 cc-matrix confusion direction (sub-08 cyan-violet z=+2.49, sub-09 green-violet z=+3.13) reported as descriptive evidence of CVD-specific representational geometry, NOT classifier
- Behavioral validation requires **pre-registered independent acquisition** (Phase 3 — TBD)
