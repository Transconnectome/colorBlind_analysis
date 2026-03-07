# Stimulus-Space Filter Optimization — PLAN

> Last updated: 2026-03-07
> Status: Planning (pre-validation complete; implementation pending)
> Reviewed by: colleague discussion (2026-03-06)

---

## 1. Architecture Overview

**Goal**: Find a smooth hue-angle transformation T_psi that maps CVD-perceived color space to HC-perceived color space, operating entirely in stimulus (theta) space rather than voxel space.

**Key components**:

| Component | Space | Description |
|-----------|-------|-------------|
| HC average target s_bar_HC(theta) | SRM (k-dim) | Mean HC forward-encoding prediction at angle theta |
| CVD individual M_CVD | SRM (k-dim) | Subject-specific forward-encoding weight matrix |
| Fourier transform T_psi | Stimulus (1-dim) | Smooth, monotonic angle remapping with 4 free parameters |

**Pipeline**:
```
theta_orig --> T_psi(theta_orig) --> channels(T_psi(theta_orig)) --> M_CVD --> predicted SRM pattern
                                                                      |
                                                        compare with s_bar_HC(theta_orig)
```

---

## 2. Core Insight: M_s as the Bridge

The subject-specific prediction matrix M_s is computed as:

```
M_s = W_SRM^T @ W_FE    (shape: k x 6)
```

where:
- W_SRM: SRM weight matrix (n_voxels x k), projects voxels to shared space
- W_FE: Forward encoding weight matrix (n_voxels x 6), maps 6 channels to voxel patterns

**Why this works**:
- M_s is (k x 6) — small, subject-specific, and smooth at arbitrary angles
- Prediction at any angle theta: `s(theta) = M_s @ channels(theta)` — a (k,) vector in SRM space
- FE channels are analytic (half-wave rectified cosines) so M_s produces smooth interpolation
- Regularization keeps T_psi near identity, preventing pathological remappings

**Resolves the interpolation problem**: Previous LOCO attempts showed that 7 training colors per fold provide insufficient degrees of freedom for regression. Here, channels(theta) are continuous basis functions defined analytically — no fitting needed for interpolation.

---

## 3. Loss Function

For a CVD subject with transform parameters psi = (a1, b1, a2, b2):

```
L(psi) = sum_i ||M_CVD @ channels(T_psi(theta_i)) - s_bar_HC(theta_i)||^2
         + lambda * ||psi||^2
```

where:
- theta_i are the 8 measured color angles (0, 45, ..., 315 degrees)
- M_CVD is the CVD subject's (k x 6) prediction matrix
- s_bar_HC(theta_i) is the HC group-mean prediction at theta_i
- lambda controls regularization toward identity (T_psi = theta when psi = 0)

**Optimization**: scipy.optimize.minimize (L-BFGS-B), 4 parameters only.

---

## 4. Transform Family: Fourier Parameterization

```
T_psi(theta) = theta + a1*cos(theta) + b1*sin(theta) + a2*cos(2*theta) + b2*sin(2*theta)
```

**Properties**:
- 4 free parameters: psi = (a1, b1, a2, b2)
- Identity when psi = 0 (no transform)
- Circular: T_psi(0) and T_psi(2*pi) connect smoothly
- Low-frequency: 1st and 2nd harmonics only — prevents jagged remappings
- Monotonicity constraint: dT_psi/dtheta > 0 everywhere (enforceable via penalty or constraint)

**Why Fourier?**:
- CVD color distortions are smooth (L-M axis compression, S-cone compensation)
- Pre-validation shows distortion profiles have simple angular structure
- 4 parameters << 8 data points: well-determined even with LOCO (7 train / 1 test)

---

## 5. Validation Strategy (4 Stages)

### Stage 1: M_s Prediction Validation (LOCO of M_s)

**Purpose**: Verify that M_s = W_SRM^T @ W_FE produces accurate predictions at held-out color angles.

**Method**: LOCO CV — train W_FE on 7 colors, predict held-out color via M_s @ channels(theta_held_out).

**Metric**: MAE in SRM space (correlation distance between predicted and actual SRM pattern).

**Pass criterion**: MAE < chance (90 degrees equivalent in SRM correlation space).

### Stage 2: T_psi Optimization (LOCO, 7 train / 1 test)

**Purpose**: Fit T_psi per CVD subject using LOCO — train on 7 colors, evaluate on held-out.

**Method**: For each LOCO fold, optimize psi on 7 training angles, evaluate alignment at held-out angle.

**Metric**: Improvement over identity (T_psi = theta) — reduction in ||M_CVD @ channels(T_psi(theta)) - s_bar_HC(theta)||.

**Pass criterion**: LOCO improvement > 0 for majority of held-out colors (>= 5/8 folds).

### Stage 3: Permutation Test (1000 shuffles, SLURM)

**Purpose**: Establish null distribution for T_psi improvement.

**Method**: Shuffle HC-CVD labels 1000 times, re-fit T_psi each time, compare observed improvement to null.

**Metric**: p-value from permutation distribution.

**Pass criterion**: p < 0.05 for at least 1 CVD subject.

### Stage 4: Behavioral Validation (future work, deferred)

**Purpose**: Verify that T_psi-corrected stimuli actually improve CVD color perception.

**Status**: Deferred — requires additional scanning session with corrected stimuli.

---

## 6. Implementation Steps

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `step1_prediction_validation.py` | LOCO of M_s in SRM space | amplitudes_srm.npy, amplitudes_procrustes.npy | per-subject LOCO MAE, M_s matrices |
| `step2_stimulus_transform.py` | T_psi optimization per CVD subject | M_s matrices, HC mean targets | fitted psi, transform curves |
| `step3_loco_validation.py` | LOCO of full T_psi pipeline | step1 + step2 outputs | LOCO improvement over identity |
| `step4_permutation_test.py` | Null distribution (1000 shuffles) | all above | p-values, null distributions |
| `step4_permutation.sbatch` | SLURM wrapper for step4 | step4 script | SLURM logs |
| `utils_transform.py` | Shared utilities (channels, Fourier T, M_s) | — | importable module |

**All scripts save to `results/` with flat structure (no timestamp subdirs) per CLAUDE.md convention.**

---

## 7. Directory Structure

```
future_phase2_filter_optimization/
├── PLAN.md              # This document
├── README.md            # Phase overview + relationship to LOCO trials
├── pre_validation/      # Existing pre-validation results
│   ├── notion_prevalidation.md
│   ├── results/
│   └── scripts/
├── figures/             # Existing
│   └── README.md
├── scripts/             # New: implementation (to be created)
│   ├── step1_prediction_validation.py
│   ├── step2_stimulus_transform.py
│   ├── step3_loco_validation.py
│   ├── step4_permutation_test.py
│   ├── step4_permutation.sbatch
│   └── utils_transform.py
└── results/             # New: outputs (to be created)
    ├── step1_prediction/
    ├── step2_transform/
    ├── step3_loco/
    └── step4_permutation/
```

---

## 8. Success Criteria

| Criterion | Threshold | Rationale |
|-----------|-----------|-----------|
| M_s LOCO MAE | Below chance | M_s must predict held-out colors accurately |
| T_psi fit loss | < identity loss | Transform must improve over no-transform |
| LOCO improvement | > 0 for >= 5/8 folds | Majority of held-out colors should benefit |
| Permutation p-value | < 0.05 for >= 1 CVD subject | Statistical significance |
| Monotonicity | dT_psi/dtheta > 0 everywhere | Physically meaningful (no folding) |

---

## 9. Relationship to Existing Analyses

| Component | Source | Status |
|-----------|--------|--------|
| SRM k values (V1=4, V2=4, V3=3, hV4=3) | Phase 2 validation 2C | Confirmed |
| W_FE (forward encoding weights) | phase3_decoder_comparing LOCO/LORO | Pooled W adopted |
| HC-CVD SRM disparity | Phase 2 LOO-consistent | V1 p=0.062, V2 p=0.075 |
| LOCO FE baseline (Procrustes) | phase3_decoder_comparing | HC MAE ~75 degrees |
| SRM continuous structure limits | LOCO_trials Phase 1b MDS | V1 stress plateau, hV4 CIELab sign flip |
| Per-pair CVD distortion profiles | pre_validation B1-B3 | L-M deficit + S-cone compensation |

**Operating space decision**: Procrustes for individual filter application (rich voxel-level info), SRM for HC target definition and cross-subject comparison (per LOCO_trials findings).

---

## 10. Deferred Items

- **Script implementation** (step1-4 .py files): To be created after plan approval
- **Server-side folder renames**: User will handle when ready
- **Behavioral validation** (Stage 4): Requires additional scanning
- **Multi-ROI joint optimization**: Currently per-ROI; joint T_psi across ROIs is a possible extension
