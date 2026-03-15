# Future Phase 1: Forward Encoding Model (360° Hue Interpolation)

**Research Question (SRQ3)**: Can channel-based forward encoding predict brain responses for held-out colors via continuous interpolation in 360° hue space?

**Status**: Core pipeline COMPLETE. CVD residual analysis + prediction model in progress.
**Last updated**: 2026-03-14

---

## Overview

This phase builds a **forward encoding model** that maps stimulus hue angles to voxel-level brain responses:

```
Y_s(theta) = W_s @ C(theta; K)
```

where `C(theta; K)` is a K-channel half-wave rectified Fourier basis (Brouwer & Heeger, 2009), and `W_s` are subject-specific encoding weights estimated via **ridge regression with GCV-selected alpha** (direct fit, no prior).

The model is validated through **Leave-One-Color-Out (LOCO)** cross-validation: train on 7 of 8 measured colors (45° spacing), predict the held-out 8th, and assess interpolation accuracy via voxel pattern correlation.

### Key Findings

| ROI | Optimal K | Perm p (10K) | Gate |
|-----|:---------:|:------------:|:----:|
| V1  | FE-2      | 0.170        | FAIL |
| V2  | FE-3      | 0.125        | FAIL |
| V3  | FE-8      | 0.045        | CONDITIONAL |
| hV4 | FE-3      | 0.026        | **PRIMARY GO** |

- **Omnibus test**: Stouffer Z=2.87, p=0.002 (cortex-level interpolation exists)
- **Discrimination != Interpolation**: V1/V2 classify colors but cannot interpolate to novel hues
- **HC-CVD gap**: Cool/S-axis colors (blue, purple, magenta) show persistent CVD deficit even after model optimization

---

## Pipeline

### Adopted Model: Direct Ridge (ridge_gcv)

The current optimal model is a **direct ridge regression** per subject, with no group prior:

```
W_s = (C'C + alpha*I)^{-1} C'X
alpha selected via Generalized Cross-Validation (GCV)
```

Per LOCO fold: pool 6 runs x 7 training colors = 42 samples, fit W, predict held-out color.

### Tested but Rejected: SRM Group Prior Pipeline (Step A-D)

Four models were compared in `validate_loro_loco_loso.py`:

| Model | Formula | Prior? | LOCO Result |
|-------|---------|:------:|:-----------:|
| ols | `pinv(C) @ X` | No | Baseline |
| **ridge_gcv** | `(C'C + aI)^{-1} C'X` | **No** | **ADOPTED** |
| prior_only | `W = W0` (zero-shot) | Yes | Failed |
| prior_finetune | `(C'C + lI)^{-1}(C'X + lW0)` | Yes | Failed |

The SRM-based prior pipeline (Steps A-D) was fully implemented and tested:

| Step | Script | Purpose |
|------|--------|---------|
| A | `scripts/step_a_fit_srm.py` | Fit SRM on HC -> R_i projections |
| B | `scripts/step_b_group_prior.py` | Group-mean encoding A_g |
| C | `scripts/step_c_project_prior.py` | Project prior W0 = R_s @ A_g |
| D | `scripts/step_d_finetune.py` | Prior-centered ridge -> W_s |

**Why prior failed for LOCO**: W0 built from all 8 colors leaks held-out color information. Per-fold W0 recomputation (leakage-free, `recompute_W0_excluding_colors()`) removes leakage but adds too much noise with only 7 training colors. Inner CV drives lambda -> 0 (= ignores prior entirely).

Shared utilities: `scripts/utils_forward_model.py` (basis construction, fitting, metrics)

### Validation Protocols

- **LORO** (Leave-One-Run-Out): Train on 5 runs, test on 1. Measures within-color generalization.
- **LOCO** (Leave-One-Color-Out): Train on 7 colors, predict held-out. Measures interpolation.
- **LOSO** (Leave-One-Subject-Out): Test cross-subject generalization.

---

## Statistical Validation

### 1. Omnibus Gate Analysis (N1)

**Script**: `scripts/n1_stouffer_omnibus.py`
**Output**: `results/neutralization/n1_stouffer_omnibus.json`

Addresses the multiple-comparisons critique (testing 4 ROIs inflates false positive rate).

**Method**: Two-level hierarchical Stouffer combination.

```
Level 1: Per-ROI
  For each ROI, combine 7 HC subjects' permutation p-values via Stouffer:
    Z_roi = sum(Phi^-1(1 - p_i)) / sqrt(7)

Level 2: Omnibus
  Combine 4 ROI-level Stouffer p-values:
    Z_omni = sum(Z_roi) / sqrt(4)
```

If omnibus passes (p < 0.05), proceed to post-hoc per-ROI tests. This controls family-wise error.

**Results**:
- Omnibus: **p = 0.002** (PASS). Fisher's method confirms: p = 0.007
- Post-hoc (uncorrected): hV4 p=0.026, V3 p=0.045
- Post-hoc (Bonferroni-4): none survive alpha=0.0125
- **Interpretation**: "Cortex-level color interpolation exists" is omnibus-protected. hV4 is the primary driver.

### 2. K-Selection Bias Test (N2)

**Script**: `scripts/n2_k_selection_bias.py`
**Output**: `results/neutralization/n2_k_selection_bias.json`

Addresses the concern that searching K in {2,3,4,5,6,8,10,12} and selecting HC-optimal K artificially inflates the HC-CVD gap reduction.

**Method**: Label-shuffle permutation test (10,000 iterations).
1. Randomly assign 7/10 subjects as "pseudo-HC", 3 as "pseudo-CVD"
2. Find K that maximizes pseudo-HC mean LOCO
3. Compute gap_reduction = (FE-6_gap - optimal_K_gap) / |FE-6_gap|
4. Compare observed reduction to null distribution

**Results**: All ROIs show gap reduction EXPECTED BY CHANCE (p > 0.13). The 54-78% gap reduction is a statistical artifact of exhaustive K-search. Gap magnitude under any fixed K remains valid, but "gap reduction across K" should not be interpreted as biologically meaningful.

### 3. Opponent Basis Test

**Script**: `scripts/opponent_basis_test.py`
**Output**: `results/opponent_basis/`

Tests whether V1/V2's LOCO failure is due to basis mismatch (using Fourier basis instead of cone-opponent channels). Three opponent bases tested: OPP-2, OPP-4, OPP-4rect.

**Result**: All opponent bases also FAIL for V1/V2. The discrimination-without-interpolation dissociation is a genuine regional property, not a basis artifact.

### 4. Intercept Model Test

**Script**: `scripts/intercept_permutation_test.py`

Tests whether shared spatial mean across colors drives LOCO performance.

**Result**: Standard model, intercept model, and mean-subtracted model produce identical p-values. Spatial mean does not explain LOCO performance.

---

## HC-CVD Comparison

### Warm/Cool Axis Dissociation (hV4 FE-3)

| Axis | Colors | FE-6 Gap | FE-K Gap | Reduction | Interpretation |
|------|--------|:--------:|:--------:|:---------:|----------------|
| Warm (L-M) | red, orange, yellow, green | +0.118 | -0.060 | >100% (reversal) | Model-specification artifact |
| Cool (S) | cyan, blue, purple, magenta | +0.362 | +0.237 | 35% only | **Residual biology** |

The warm-color HC-CVD gap disappears under optimal K (model artifact), but the cool-color gap persists at 65% -- this is the Phase 2 filter target.

### Per-Color LOCO (hV4 FE-3, HC Mean vs CVD Mean)

| Color | HC Mean | CVD Mean | Cohen's d | p |
|-------|:-------:|:--------:|:---------:|:---:|
| red (0) | +0.353 | +0.310 | +0.18 | 0.81 |
| orange (45) | +0.246 | +0.502 | -0.94 | 0.22 |
| yellow (90) | +0.135 | +0.213 | -0.24 | 0.70 |
| green (135) | +0.107 | +0.055 | +0.13 | 0.85 |
| cyan (180) | -0.008 | +0.157 | -0.35 | 0.66 |
| **blue (225)** | **+0.349** | **+0.025** | **+1.37** | **0.046** |
| purple (270) | +0.283 | -0.124 | +1.54 | 0.060 |
| magenta (315) | +0.171 | -0.211 | +1.19 | 0.127 |

Blue is the only color reaching significance. Cool colors (blue, purple, magenta) consistently show large positive d values, indicating CVD deficit in S-axis interpolation.

---

## Track B: CVD Prediction Model

### B1. Subject-Specific K Selection (ADOPTED)

**Script**: `scripts/subject_k_selection.py`
**SLURM**: `sbatch/run_subject_k.sbatch`
**Output**: `results/subject_k/`

Sweeps K in {2,3,4,5,6,8,10,12} per subject to find individual optimal K.

**Key result**: sub-08 hV4 K*=8 (LOCO jumps from 0.084 to 0.541, a 6.4x improvement). HC paired-t: V2 p=0.014, hV4 p=0.031.

### B2. Anisotropic Basis (REJECTED)

**Script**: `scripts/fit_anisotropic_basis.py`

2-parameter channel shift: `centers_shifted = centers_uniform + a*sin(2t) + b*cos(2t)`. Parametric (a,b) shift hurts hV4 HC performance (p=0.010, d=-1.4).

### B3. Hierarchical FE (REJECTED)

**Script**: `scripts/fit_hierarchical_fe.py`

HC group prior regularization: `W_CVD = W_HC + dW`, ridge penalty on dW. No benefit (|delta| < 0.012, lambda -> infinity). Data too noisy for prior tuning with only 6 runs.

---

## Ongoing Tracks

### Track A: Residual Biology Report

Characterizes remaining HC-CVD differences after all model optimization.

| Experiment | Script | Status |
|-----------|--------|:------:|
| A1. FE-K MAE retry | `phase3_.../loco_fek_retry.py` | READY |
| A2. Basis anisotropy | `scripts/basis_anisotropy_test.py` | DONE |
| A3. Signed circular bias | `scripts/signed_circular_bias.py` | DONE |
| A4. 28-pair residual heatmap | `scripts/pairwise_residual_heatmap.py` | DONE |
| A5. Confusion structure | `scripts/confusion_structure.py` | DONE |
| A6. Cross-phase correlation | `scripts/cross_phase_correlation.py` | DONE |

### Track C: Dimensionality & Organization

Resolves whether CVD K-sensitivity reflects genuine dimensionality reduction or bias-variance tradeoff.

| Experiment | Script | Status |
|-----------|--------|:------:|
| C1. Eigenspectrum decay | `scripts/dimensionality/analyze_eigenspectrum_decay.py` | READY |
| C2. MEME k* estimator | `scripts/dimensionality/fit_meme_eigenspectrum.py` | READY |
| C3. Voxel preference map | `scripts/population_organization/map_voxel_color_preference.py` | READY |

---

## Directory Structure

```
future_phase1_forward_model/
|
|-- scripts/                        # All analysis scripts
|   |-- step_a_fit_srm.py           # Core pipeline step A
|   |-- step_b_group_prior.py       # Core pipeline step B
|   |-- step_c_project_prior.py     # Core pipeline step C
|   |-- step_d_finetune.py          # Core pipeline step D
|   |-- utils_forward_model.py      # Shared utilities
|   |-- validate_loro_loco_loso.py  # Main validation
|   |-- n1_stouffer_omnibus.py      # Omnibus gate test
|   |-- n2_k_selection_bias.py      # K-selection bias test
|   |-- opponent_basis_test.py      # Opponent basis control
|   |-- subject_k_selection.py      # Per-subject K sweep (B1)
|   |-- fit_anisotropic_basis.py    # Channel shift (B2)
|   |-- fit_hierarchical_fe.py      # HC prior (B3)
|   |-- signed_circular_bias.py     # Track A3
|   |-- pairwise_residual_heatmap.py # Track A4
|   |-- confusion_structure.py      # Track A5
|   |-- cross_phase_correlation.py  # Track A6
|   |-- dimensionality/             # Track C1-C2
|   |-- population_organization/    # Track C3
|   +-- (diagnostic/investigation scripts)
|
|-- sbatch/                          # SLURM job scripts
|-- results/                         # All outputs (JSON)
|   |-- validation/                  # LORO/LOCO/LOSO
|   |-- basis_comparison/            # FE-K sweep + permutation
|   |-- neutralization/              # n1_stouffer, n2_k_selection
|   |-- subject_k/                   # B1 per-subject K
|   |-- signed_bias/                 # A3 results
|   |-- pairwise_residual/           # A4 results
|   |-- confusion_structure/         # A5 results
|   +-- cross_phase/                 # A6 results
|
|-- PLAN.md                          # Full algorithm specification
|-- RESULTS.md                       # Detailed experimental results
|-- SUMMARY_next_steps.md            # Current status + 3-track plan
|-- RED_TEAM_SUMMARY.md              # Vulnerability matrix
+-- LITERATURE_INTEGRATION_PLAN.md   # Pospisil, Bannert, Kuriki refs
```

---

## Key Decisions Log

| Decision | Rationale | Date |
|----------|-----------|------|
| ridge_gcv encoder adopted | smooth_tikh failed 3 rescue attempts | 2026-03-09 |
| Per-ROI optimal K adopted | V1=2, V2=3, V3=8, hV4=3 maximizes HC LOCO | 2026-03-09 |
| Omnibus gate restructured claim | p=0.002 (cortex-level), not per-ROI | 2026-03-11 |
| K-gap reduction narrative abandoned | N2 permutation: artifact of K-search | 2026-03-11 |
| Opponent basis neutralized RT-3 | OPP-2/4/4rect all fail V1/V2 | 2026-03-11 |
| B1 subject-specific K adopted | sub-08 hV4 K*=8 gives 6.4x improvement | 2026-03-14 |
| B2 anisotropic rejected | Hurts HC hV4 (d=-1.4) | 2026-03-14 |
| B3 hierarchical rejected | No benefit, lambda -> infinity | 2026-03-14 |

---

## Phase 2 Handoff Requirements

The filter `T_psi: theta -> theta'` for Phase 2 (CVD stimulus-space correction) needs:

| Input | Source | Status |
|-------|--------|:------:|
| Target color range | Track A: theta in [180, 315] (cool/S-axis) | DONE |
| Distortion direction | A3: signed circular bias | DONE |
| Pairwise geometry | A4 + A6: 28-pair heatmap + cross-phase | DONE |
| Per-subject optimal K | B1: subject-specific K selection | DONE |
| Dimensionality | C1 + C2: eigenspectrum + MEME | READY |

---

## Related Documentation

- **Detailed algorithm**: `PLAN.md` (2,387 lines, sections 0-13)
- **Full results**: `RESULTS.md` (sections 1-14)
- **Next steps**: `SUMMARY_next_steps.md` (3-track plan)
- **Red Team**: `RED_TEAM_SUMMARY.md` (5 criticisms, 3 neutralized, 1 mitigated, 1 pending)
- **Literature**: `LITERATURE_INTEGRATION_PLAN.md`
