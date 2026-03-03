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

### Primary Result 1: Task-Dependent Optimality

| Task | Optimal Pipeline | Key Metric | Why |
|------|-----------------|------------|-----|
| **LORO** (classification) | **LDA + SRM** | 0.793 acc, ICC 0.666 | SRM resolves LDA fold-instability |
| **LOCO** (interpolation) | **FE + Procrustes** | 75.7° HC MAE | Full voxels preserve continuous hue structure |
| Phase 3 (filter design) | **FE + Procrustes** | W cosine 0.921 | Stable 6-channel representation |
| Cross-subject comparison | **LDA + SRM** | p=0.668 (no bias) | Unbiased HC→CVD generalization |

### Primary Result 2: LORO Classification — 3-Alignment Validation (Result 11)

**Bootstrap Accuracy (95% CI, 1000 iterations)**

| Model | Raw | Procrustes | SRM |
|-------|-----|------------|-----|
| **LDA** | 0.135 [0.119, 0.153] | **0.758** [0.734, 0.780] | **0.793** [0.759, 0.825] |
| SVM | 0.127 [0.114, 0.140] | 0.685 [0.655, 0.714] | 0.727 [0.685, 0.770] |
| FE | 0.129 [0.110, 0.146] | 0.545 [0.511, 0.579] | 0.480 [0.449, 0.514] |
| Ridge | 0.131 [0.116, 0.147] | 0.388 [0.361, 0.417] | 0.313 [0.276, 0.348] |
| KRidge | 0.127 [0.110, 0.143] | 0.332 [0.300, 0.366] | 0.285 [0.252, 0.319] |
| MLP | 0.126 [0.118, 0.135] | 0.147 [0.136, 0.158] | 0.131 [0.126, 0.138] |

**Test-Retest Reliability (ICC)**

| Model | Raw | Procrustes | SRM |
|-------|-----|------------|-----|
| LDA | 0.224 | 0.013 | **0.666** |
| Ridge | 0.233 | 0.148 | **0.762** |
| KRidge | 0.324 | 0.463 | **0.790** |
| SVM | -0.284 | 0.495 | **0.760** |
| MLP | 0.611 | 0.720 | **0.713** |
| FE | 0.471 | 0.574 | **0.753** |

- **SRM LDA is recommended LORO pipeline**: 0.793 accuracy, ICC 0.666, no group bias (p=0.668)
- **Procrustes LDA paradox**: 0.758 accuracy but ICC=0.013 — high fold-to-fold instability
- **Alignment × ROI interaction**: SRM > Proc V1 (p=0.002); Proc > SRM V3 (p=9.1e-08), V4 (p=1.8e-05)
- **Cross-subject generalization**: HC→CVD ≈ HC→HC for LDA (p=0.668), SVM (p=0.647) — no group bias in SRM space

### Primary Result 3: LOCO Interpolation — 3-Alignment Baseline (Result 12)

**ForwardEncoding MAE by Alignment × Group (degrees, chance = 90°)**

| ROI | Raw HC | Raw CVD | Proc HC | Proc CVD | SRM HC | SRM CVD |
|-----|--------|---------|---------|----------|--------|---------|
| V1 | 76.9 | 76.4 | 76.4 | 84.6 | 80.0 | 93.5 |
| V2 | 74.8 | 78.5 | 80.0 | 98.5 | 84.9 | 90.5 |
| V3 | 77.8 | 76.4 | 77.0 | 73.5 | 99.3 | 88.3 |
| V4 | 73.5 | 76.0 | 69.4 | 87.4 | 72.2 | 90.9 |

- **FE dominates LOCO**: best model in 85% of subject-ROI-alignment combinations (102/120)
- **Procrustes optimal alignment for LOCO**: most significant permutation tests (4 sig vs SRM's 1)
- **LORO vs LOCO alignment preference diverges**: LORO → SRM; LOCO → Procrustes
- **CVD deficit visible only with alignment**: Raw HC ≈ CVD; Procrustes reveals CVD distortion (V2 +18.5°, V4 +18.0°)
- **Correlation-based template matching is optimal** — 4 alternative decoding methods all worse (Result 7)

### Primary Result 4: FE Group Prior — HC→CVD Knowledge Transfer (Result 13)

**Method**: W_combined = λ·W_individual + (1-λ)·W_group, nested CV for λ selection
**Subjects**: 9 (6 HC, 3 CVD; sub-07 excluded for hV4 voxel count)

**LOCO GP (leakage-fixed, nested CV)**

| ROI | HC Baseline | HC GP | HC Δ% | CVD Baseline | CVD GP | CVD Δ% |
|-----|-------------|-------|-------|-------------|--------|--------|
| V1 | 80.7° | 77.3° | **+4.3%** | 93.5° | 85.7° | **+8.3%** |
| V2 | 85.9° | 78.7° | **+8.3%** | 90.5° | 85.4° | **+5.7%** |
| V3 | 100.6° | 105.9° | -5.3% | 88.3° | 112.2° | -27.0% |
| V4 | 71.2° | 75.5° | -6.1% | 90.9° | 95.7° | -5.2% |

**LORO GP (no leakage issue)**

| ROI | Baseline Mean | GP Mean | Improvement |
|-----|---------------|---------|-------------|
| V1 | 42.40° | 34.47° | **-18.7%** |
| V2 | 50.96° | 32.72° | **-35.8%** |
| V3 | 60.63° | 54.25° | -10.5% |
| V4 | 62.21° | 61.34° | -1.4% |

**Individual CVD Profiles (LOCO GP)**

| Subject | V1 Δ% | V2 Δ% | V3 Δ% | V4 Δ% |
|---------|--------|--------|--------|--------|
| sub-08 (deutan) | -7.0% | +0.6% | **-59.2%** | -15.6% |
| sub-09 (protan) | **+10.5%** | +1.3% | -31.6% | +7.8% |
| sub-10 (deutan) | **+14.7%** | **+12.9%** | +0.8% | -12.1% |

**λ-MAE curve (Result 14)**: Non-monotonic, ROI-specific. V1 monotonic (λ=0 best, pure GP), V2 shallow U-shape (λ*≈0.1–0.2), V3 HC/CVD reversed, V4 minimal benefit. Early visual (V1/V2) benefits from GP; higher visual (V3/V4) harmed.

**Key interpretation**:
- LOCO GP: V1/V2 benefit (+4–8%), V3/V4 harmful — HC mean does not capture individual V3/V4 variability
- LORO GP more effective than LOCO GP: V1 -18.7%, V2 -35.8% (individual W from 5 runs more stable than from 7 LOCO colors)
- Previous LOCO GP result (median -50.9%) was leakage artifact — resolved 2026-02-28; see METHODS historical note

**Results**: `model_comparison_validation/results/FE_group_prior/`

### Negative Results

- **Result 7**: Decoder bottleneck — PopVec, RidgeEnc, GaussML, RidgeReg all worse than baseline correlation. Encoding estimation (df=1) is the limiting factor, not decoding.
- **Result 10**: Sequential training + MLP architecture sweep — all MLP variants substantially worse than FE baseline. Non-linear readout fundamentally incompatible with LOCO OOD extrapolation.
- **Result 6**: Hybrid decoder (FE+MLP, FE+SVM) — FE_SVM ≈ FE (0.779 vs 0.784). Channel-to-color mapping is adequately linear.

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

**Last Updated**: 2026-03-03
