# Phase 2b: Decoder Model Validation

**Sub-Research Question (SRQ1)**: Can a common color decoder be successfully applied across HC and CVD participants after alignment?

**Status**: Completed ✅ (21/21 validations)
**Canonical methods file**: `analysis/METHODS_phase2b_decoders.md`

---

## Overview

This phase validates decoder assumptions before proceeding to filter optimization (Phase 3). We compare 6 models across 3 alignment methods with both LORO (classification) and LOCO (interpolation) cross-validation to answer:

1. **Is the linear assumption justified?** — Does non-linear capacity improve decoding?
2. **Is alignment necessary?** — Can non-linear models compensate for run-to-run misalignment?
3. **Is the mapping common across groups?** — Do HC and CVD share the same voxel-color mapping?
4. **Can models interpolate held-out colors?** — Does ForwardEncoding capture continuous color structure?

## Settings

- **Data**: `full_dataset_C010` (C010 confounds, Procrustes-aligned)
- **Subjects**: 10 total (HC: sub-01~07, n=7; CVD: sub-08 (deutan), sub-09 (protan), sub-10 (deutan))
- **ROIs**: V1, V2, V3, hV4 (stored as V4 on disk)
- **Input shape**: `amplitudes_{raw,procrustes,srm}.npy` — (6 runs, 8 colors, n_voxels or k)
- **SRM K values**: V1=4, V2=4, V3=3, hV4=3

---

## Key Findings

### Task-Dependent Optimality (Revised Conclusion, 2026-02-27)

| Task | Optimal Pipeline | Key Metric | Why |
|------|-----------------|------------|-----|
| **LORO** (classification) | **LDA + SRM** | 0.793 acc, ICC 0.666 | SRM resolves LDA fold-instability |
| **LOCO** (interpolation) | **FE + Procrustes** | 75.7° HC MAE | Full voxels preserve continuous hue structure |
| Phase 3 (filter design) | **FE + Procrustes** | W cosine 0.921 | Stable 6-channel representation |
| Cross-subject comparison | **LDA + SRM** | p=0.668 (no bias) | Unbiased HC→CVD generalization |

### LORO Model Comparison (Procrustes, acc_45, chance = 0.375)

| Model | acc_45 [95% CI] | MAE [95% CI] |
|-------|-----------------|-------------|
| **LDA** | **0.821** [0.802, 0.841] | **25.6°** [22.8, 28.3] |
| Ridge | 0.783 [0.750, 0.821] | 41.8° [37.9, 45.0] |
| SVM | 0.776 [0.734, 0.811] | 32.9° [27.1, 38.7] |
| KernelRidge | 0.739 [0.692, 0.779] | 47.9° [43.9, 52.1] |
| ForwardEnc | 0.736 [0.708, 0.773] | 43.5° [38.6, 47.2] |
| MLP | 0.394 [0.381, 0.409] | 87.1° [85.1, 88.9] |

**Note**: Under SRM alignment, LDA achieves 0.793 with ICC 0.666 (vs Procrustes ICC 0.013).

### Alignment Effect (LORO, all models at chance without alignment)

| Alignment | LDA | SVM | FE | Ridge |
|-----------|-----|-----|-----|-------|
| Raw | 0.393 | 0.382 | 0.367 | 0.375 |
| Procrustes | **0.821** | 0.776 | 0.736 | 0.783 |
| SRM | **0.793** | 0.727 | 0.480 | 0.313 |

### HC vs CVD (Procrustes, acc_45)

HC ≈ CVD across all models. LDA: HC 0.805, CVD 0.859 (CVD numerically higher). **Shared voxel-color mapping confirmed** → filter learning justified.

### LOCO: ForwardEncoding is the Only Interpolation Model

- **FE+Procrustes HC MAE**: V1 76.4°, V2 80.0°, V3 76.9°, hV4 69.4° (chance = 90°)
- All other models (LDA, SVM, MLP, Ridge, KernelRidge) at or worse than chance in LOCO
- **Correlation-based template matching is optimal** — 4 alternative decoding methods all worse (Result 7)

### Key Negative Results

- **Result 7**: Decoder bottleneck — PopVec, RidgeEnc, GaussML, RidgeReg all worse than baseline correlation. Encoding estimation (df=1) is the limiting factor, not decoding.
- **Result 10**: Sequential training + MLP architecture sweep — all MLP variants substantially worse than FE baseline. Non-linear readout fundamentally incompatible with LOCO OOD extrapolation.
- **Result 6**: Hybrid decoder (FE+MLP, FE+SVM) — FE_SVM ≈ FE (0.779 vs 0.784). Channel-to-color mapping is adequately linear.

### Group Prior (HC-mean W for CVD)

- HC-mean encoding weights (W) improve CVD LOCO MAE by +4–8%
- Leakage-free nested CV validated
- Results: `model_comparison_validation/results/FE_group_prior/`

---

## Models Compared (6)

| Model | Type | Target | Linearity | Key Hyperparameters |
|-------|------|--------|-----------|-------------------|
| **LDA** | Classifier | Labels (0-7) | Linear | solver ∈ {svd, lsqr}, shrinkage ∈ {None, auto, 0.5} |
| **Ridge** | Regression | Circular hue (sin/cos) | Linear | alpha ∈ {0.01, 0.1, 1, 10, 100} |
| **ForwardEncoding** | Encoding model | Labels via 6-ch basis | Linear | alpha ∈ {0, 10, 50} |
| **KernelRidge** | Regression | Circular hue (sin/cos) | Non-linear | alpha ∈ {0.1, 1, 10}, gamma ∈ {0.001, 0.01, 0.1} |
| **SVM** | Classifier | Labels (0-7) | Non-linear | C ∈ {0.1, 1, 10}, gamma ∈ {0.001, 0.01, 0.1} |
| **MLP** | Classifier | Labels (0-7) | Non-linear | hidden ∈ {(64,), (64,32)}, alpha ∈ {0.01, 0.1} |

---

## Scripts

### Core Analysis (`model_comparison_validation/scripts/`)

| Script | Purpose |
|--------|---------|
| `loro_baseline.py` | LORO CV for 6 models × 3 alignments |
| `loco_baseline.py` | LOCO CV with ForwardEncoding + permutation tests |
| `validation_tests.py` | Bootstrap CI, ICC reliability, cross-subject generalization |
| `group_prior.py` | HC-mean W group prior for CVD LOCO/LORO improvement |
| `utils.py` | Shared utilities (data loading, metrics, channel basis) |
| `visualize_model_comparison.py` | Results visualization |
| `plot_lambda_curve.py` | Group prior lambda regularization curve |

### SLURM Batch (`model_comparison_validation/scripts/`)

| Sbatch | Purpose |
|--------|---------|
| `loro_baseline_{raw,procrustes,srm}.sbatch` | LORO per-alignment jobs |
| `loco_baseline_{raw,procrustes,srm}.sbatch` | LOCO per-alignment jobs |
| `validation_tests.sbatch` | Bootstrap + ICC validation |
| `validation_loro_3aln.sbatch` | 3-alignment LORO validation |
| `group_prior_{loro,loco}.sbatch` | Group prior jobs |
| `group_prior_cvd_srm.sbatch` | CVD-specific SRM group prior |
| `run_hybrid.sbatch` | Hybrid decoder (FE+MLP, FE+SVM) |

### Analysis & Parsing (`analysis/`)

| Script | Purpose |
|--------|---------|
| `parse_loco_results.py` | Parse LOCO JSON results |
| `compute_srm_amplitudes.py` | Compute SRM-projected amplitudes |
| `validate_loco_srm.py` | Validate LOCO in SRM space |
| `fe_cross_decoding.py` | FE cross-decoding HC→CVD in SRM space |
| `test_decoding_methods.py` | Test alternative LOCO decoding methods |

### Legacy Phase 1 Scripts (historical, pre-Phase 2b)

| Script | Note |
|--------|------|
| `phase1_baseline32_full_validation.py` | Legacy — superseded by C010 pipeline |
| `phase1_baseline32_validation.py` | Legacy — superseded by C010 pipeline |
| `phase1_cross_subject_loso.py` | Legacy — LOSO analysis |
| `phase1_rsa.py` | Legacy — RSA analysis |
| `phase1_voxel_overlap.py` | Legacy — voxel overlap |

---

## Visualization

### 1. LOCO Color Wheel Plots

**Script**: `visualization/visualize_loco_color_wheel.py`

**Purpose**: Color wheel visualization showing true vs predicted hue angles for LOCO results.

**Outputs** (in `results/loco/color_wheel_plots/`):
- **Per subject-ROI**: 6 run plots + 1 average (10 subjects x 4 ROIs x 7 = 280 files)
- **Group comparisons**: 4 files (one per ROI, HC vs CVD)

**Key Results** (V1 ForwardEncoding):
- HC: 67–88° MAE (mean ~75°)
- CVD: 62–84° MAE (similar to HC)
- Chance level: 90°

### 2. LOCO Circular Performance Plots

**Script**: `visualization/visualize_loco_circular.py`

**Purpose**: Polar plot showing per-color MAE aggregated across runs.

### 3. CVD Distortion Figure

**Script**: `visualization/create_cvd_distortion_figure.py`

**Purpose**: Publication figure showing CVD-specific color space distortions.

---

## Results Structure

```
results/
├── loco/
│   ├── procrustes/          # LOCO results (Procrustes alignment)
│   ├── raw/                 # LOCO results (no alignment)
│   ├── srm/                 # LOCO results (SRM alignment)
│   └── color_wheel_plots/   # Visualization outputs
├── loro/                    # LORO results per alignment
├── loco_decoding_comparison/ # Alternative decoding method results
├── FE_group_prior/          # Group prior results
└── loco_ensemble/           # Ensemble variant results (legacy)

model_comparison_validation/results/
├── loro_{raw,procrustes,srm}/   # LORO per-alignment results
├── loco_{raw,procrustes,srm}/   # LOCO per-alignment results
├── validation_3aln/             # 3-alignment validation (ICC, bootstrap)
├── hybrid/                      # Hybrid decoder results
└── FE_group_prior/              # Group prior (nested CV)
```

---

## Validation Status (21/21 complete)

- [x] LORO model comparison: 10 subjects, 4 ROIs, 6 models, 3 alignments
- [x] Bootstrap 95% CIs: subject-level resampling, 1000 iterations
- [x] HC vs CVD comparison: Mann-Whitney U, no meaningful group difference
- [x] Test-retest reliability: ICC across 3 alignments (SRM all > 0.66)
- [x] LOCO local test + server deployment (10 subj x 4 ROIs x 1000 perms)
- [x] Nested Procrustes: no leakage confirmation (SVM 0.899, FE 0.781)
- [x] PCA dim reduction: information loss vs full voxels
- [x] Individual CVD cross-decoding: HC-only SRM, 10/12 tests significant
- [x] LDA reliability diagnostics: run-pair r=0.009 explains paradox; FE W cosine 0.921
- [x] Hybrid decoder (FE+MLP, FE+SVM): linear readout confirmed
- [x] LOCO decoder improvement: 4 alt. methods all worse (negative result)
- [x] LORO 3-alignment validation: raw/procrustes/SRM with bootstrap + ICC
- [x] LOCO 3-alignment baseline: raw/procrustes/SRM with permutation
- [x] FE Group Prior: nested λ CV, LOCO + LORO
- [x] Sequential training + MLP sweep: negative result (terminated)
- [x] LOCO cross-alignment validation: FE across 3 alignments
- [x] Non-linear model LOCO performance: all worse than FE
- [x] CVD color-space distortion analysis
- [x] FE cross-decoding HC→CVD in SRM: 10/12 pairs significant
- [x] 3-alignment Wilcoxon comparison: SRM > Proc in LORO (V1 p=0.002)
- [x] Group prior leakage-free nested CV: validated

---

## References

- **Detailed methods & statistics**: `analysis/METHODS_phase2b_decoders.md` (authoritative)
- **Overall project**: `README.md` (root)
- **Phase 2 SRM**: `analysis/phase2_SRM_across_between/README.md`
- **Phase 1 baseline**: `analysis/phase1_preprocess_decoding/README.md`

---

**Last Updated**: 2026-02-28
