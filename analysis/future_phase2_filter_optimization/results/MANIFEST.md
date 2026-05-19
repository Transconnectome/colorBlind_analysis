# Phase 2 Filter Optimization — Results Manifest

**Last updated**: 2026-05-19 (narrative cleanup — cc-matrix Bonferroni anchor removed; scripts/ reorganized: BEST at root, candidates → filter_ops, rest → _archive)

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
├── scripts/                    11 canonical .py at root + 6 subdirs (post 2026-05-19 reorg)
│   ├── # Canonical Phase 2 pipeline (produces BEST)
│   ├── loco_distortion_fit.py        Core fitting (L_fit + grid + perm) — canonical entry
│   ├── machado_simulator.py          Stockman fundamentals + machado_shifted_hue (h_base)
│   ├── utils_distortion_models.py    Model interface (get_design_matrix etc.)
│   ├── step1_fit_loco_v2.py          Helpers: precompute_hc_W, load_cvd_loco_target
│   ├── diagnostic_delta_rdm.py       ΔRDM_obs/_sim used by canonical L_rdm
│   ├── c3_relabel_p2a.py             NEW 9-bin labels (canonical P2a)
│   ├── c3_relabel_both_subjects.py   Per-subject NEW target maps
│   ├── render_loco_canonical_4col.py BEST 4-col viz generator
│   ├── stim_lab_render.py            Color rendering helper
│   ├── landscape_loader.py           Parquet-backed landscape access
│   ├── retinal_cortical.py           R+C functions (paper Tier 2 diagnostic; imported by validate_2comp diagnostics)
│   │
│   ├── forward_models/               two_component (canonical), three_component, opponent_gain, rc_2stage
│   ├── filter_ops/                   Candidate alternative filters + multi-ROI confusion (paper comparison)
│   │   ├── render_rc_2stage_4col.py     R+C 2-stage viz (rejected filter form, retained for paper Discussion)
│   │   ├── voxel_level_fit.py           Phase 4 voxel-level direct MSE (failed alternative)
│   │   ├── multi_roi_confusion_diagnostic.py  Per-pair V1/V2/V4 confusion z-scores (paper supporting)
│   │   ├── loco_filter_derive.py
│   │   ├── loco_filter_feasibility.py
│   │   ├── compare_2component_loco.py
│   │   └── evaluate_preimage_filter.py
│   ├── diagnostics/                  18 diagnostic scripts (baseline_ρ, validate_2comp, etc.)
│   ├── inventory/                    Inventory builders
│   ├── visualization/                Figure-generation scripts
│   ├── slurm/                        SLURM submission scripts
│   └── _archive/                     Archived exploration/cycle scripts
│       └── cleanup_2026-05-19_scripts_root/   Latest reorg batch (11 files: HC specificity descriptives,
│           Option C deprecated viz, sub-10 paper-excluded analyses, OLD-scheme P2a, one-shot data prep)
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
    ├── voxel_level_fit/                                   Phase 4 preview — voxel-level direct MSE (2026-05-18)
    │   ├── voxel_landscape_sub-08.json                    argmin (4,4), ratio 0.017 (flat), P2a 0.688
    │   ├── voxel_landscape_sub-09.json                    argmin (0,+36), ratio 0.601 (sharp, wrong sign), P2a 0.775
    │   └── timing_sub-08.json                             0.1 s/subject (W precomputed once)
    │
    ├── sub10_mild_deutan/                                 Sub-10 (mild deutan, axis=150°) canonical 2comp fit (2026-05-18)
    │   ├── sub-10_V4_2component.json                      argmin (10,+22), L_fit=0.127, perm_p=0.018 ★ — TP (CVD detected); β_c sign flips vs sub-08
    │   └── sub-10_V4_2component_landscape.json            Within-family inconsistency evidence (NOT a false positive)
    │
    ├── sub10_null_control_WRONG_cvd_normal_2026-05-18/    DEPRECATED — wrong axis (83° normal); sub-10 is deutan per CLAUDE.md §6
    │   ├── sub-10_V4_2component.json                      argmin (30,−24), perm_p=0.180 — DO NOT USE
    │   └── sub-10_V4_2component_landscape.json            Kept for traceability of the CVD_TYPE bug fix
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
**results/ subdirs preserved**: c3_relabel/, phase4_preview/, voxel_level_fit/, sub10_mild_deutan/, sub10_null_control_WRONG_cvd_normal_2026-05-18/, fits/, old_formula/, axis_3way/, CANDIDATE/, _archive/, _superseded/

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

- All filter selection is **descriptive** — specificity claims forbidden under HC FPR=100% (HC subjects pass label permutation under canonical loss; `hc_specificity_check.py`)
- L_rank artifact (L@id inversion) documented as methodological subtlety (correlation + HC LOO + small n)
- **Three convergent failures** (L_dir, 3-comp joint, voxel-level direct MSE) — all pre-committed criteria failed; richer neural metrics yield argmins that either flatten the landscape or sharpen toward parameters that degrade behavioral P2a. 2-comp standalone retained as Phase 2 filter form; convergence reframed as paper Discussion claim (neural fit ≠ behavioral filter quality).
- **Sub-10 within-family inconsistency** — sub-10 (mild deutan, sub-10 IS CVD) yields (10, +22), β_c sign opposite to sub-08 severe deutan (38, −14); L_fit at sub-10 lower than sub-08/09. Earlier "sub-10 FP" framing (MEMORY 2026-04-11, 2026-03-23) assumed sub-10 was normal and is superseded — sub-10 perm_p=0.018 is a true positive (CVD detected in CVD), not a false positive. The genuine issue is that (β_s, β_c) is not a stable per-family signature and L_fit does not track severity.
- Per-pair V4 cc-matrix confusion direction (sub-08 cyan-violet z=+2.49, sub-09 green-violet z=+3.13) reported as descriptive evidence of CVD-specific representational geometry, NOT classifier
- Behavioral validation requires **pre-registered independent acquisition** (Phase 3 — TBD)
