# Phase 1: Baseline Decoding & Color Discrimination

**Research Question (RQ1)**: Can individuals with CVD distinguish colors neurally despite retinal deficits?
**망막 결함에도 불구하고 색맹자가 신경 수준에서 색을 구별할 수 있는가?**

**Status**: Completed ✅
**Scripts**: 5 files

---

## Overview

This phase establishes baseline neural color discrimination capabilities in both HC and CVD participants using forward encoding models. We demonstrate that **all CVD participants successfully decode colors** despite genetic retinal deficits, with performance approaching HC levels.

## Key Findings (RQ1)

### ✅ CVD participants show successful neural color decoding:

| Group | V1 Accuracy | V2 Accuracy | V3 Accuracy | hV4 Accuracy | V1 Error | V2 Error |
|-------|-------------|-------------|-------------|--------------|----------|----------|
| **HC** | 76% | 71% | 69% | 68% | 32° | 35° |
| **CVD (all)** | 68-76% | 65-71% | 64-69% | 62-68% | 30-48° | 32-50° |
| **Sub-08** (Deut) | 73% | 68% | 66% | 65% | 35° | 38° |
| **Sub-09** (Deut) | 71% | 67% | 65% | 64% | 40° | 42° |
| **Sub-10** (Prot) | 70% | 66% | 64% | 63% | 45° | 48° |

**Chance level**: 12.5% (8 colors), 90° error

### Supporting Evidence

- **RDM structural preservation**: >90% in V1-V2 (Procrustes stability)
- **Reconstruction accuracy**: 32-48° error (far below 90° chance)
- **Cross-run reliability**: >0.80 split-half correlation

**Conclusion**: CVD individuals maintain robust neural color representations despite retinal cone dysfunction, suggesting cortical compensation mechanisms.

---

## Key Scripts

### 1. `phase1_baseline32_full_validation.py`

**Purpose**: Comprehensive baseline validation with 32-color reconstruction

**Methods**:
- Leave-one-run-out cross-validation
- 8-fold classification accuracy
- 32-color circular reconstruction
- Permutation testing (1000 iterations)

**Output**: Classification accuracy, reconstruction error, significance p-values

### 2. `phase1_cross_subject_loso.py`

**Purpose**: Leave-one-subject-out (LOSO) generalization testing

**Methods**:
- Train on N-1 subjects, test on held-out subject
- Assess cross-subject decoder transferability
- Identify subject-specific vs. shared representations

**Result**: Poor cross-subject generalization → High individual variability (motivates RQ2)

### 3. `phase1_rsa.py`

**Purpose**: Representational Similarity Analysis (RSA)

**Methods**:
- Compute RDM (Representational Dissimilarity Matrix) for each subject
- Correlation distance between color pairs
- Between-subject RDM correlation

**Output**: RDM matrices, inter-subject similarity scores

**Finding**: Low RDM correlation (0.26-0.35) despite high Procrustes stability (0.88-0.91) → Different coordinate systems (motivates hyperalignment)

### 4. `phase1_voxel_overlap.py`

**Purpose**: Anatomical consistency across subjects

**Methods**:
- Jaccard index for voxel overlap
- Common voxel identification
- ROI size comparison

**Results**:
| ROI | Mean Jaccard | Common Voxels | Union Voxels |
|-----|--------------|---------------|--------------|
| V1 | 0.083 | 0 | 305 |
| V2 | 0.033 | 0 | 97 |
| V3 | 0.845 | 34 | 58 |
| hV4 | 0.732 | 28 | 70 |

**Insight**: High anatomical overlap (V3/hV4) ≠ High functional similarity → Alignment needed

### 5. `phase1a_rdm_guided.py`

**Purpose**: RDM-guided voxel selection

**Methods**:
- Select voxels with consistent color tuning across subjects
- RDM-based reliability metric
- Compare to anatomical selection

**Result**: Improved stability but still requires alignment

---

## Methods

### Forward Encoding Model

**Training**:
```python
# For each subject, each run
C_train = channel_matrix(training_colors)  # (n_trials, 8)
B_train = beta_matrix(training_trials)     # (n_trials, n_voxels)
W = fit_weights(C_train, B_train)          # (8, n_voxels)
```

**Testing** (Classification):
```python
B_test = test_beta_matrix  # (n_test_trials, n_voxels)
for test_trial in B_test:
    predicted_channels = inv(W) @ test_trial
    predicted_color = argmax(channel_response(predicted_channels))
```

**Testing** (Reconstruction):
```python
# Reconstruct 32 equally-spaced hues
predicted_channels = inv(W) @ B_test
predicted_hue = argmax(correlation(predicted_channels, all_32_channels))
reconstruction_error = circular_distance(predicted_hue, true_hue)
```

### Permutation Testing

**Null hypothesis**: Decoding performance = chance level

**Procedure**:
1. Shuffle color labels 1000 times
2. Recompute classification accuracy for each shuffle
3. p-value = proportion of shuffles exceeding observed accuracy

**Result**: All HC and CVD participants: p < 0.001

---

## Visualization

### 1. LOCO Color Wheel Plots (NEW - 2026-02-19) ✓ RECOMMENDED

**Script**: `visualization/visualize_loco_color_wheel.py`

**Purpose**: Color wheel visualization showing true vs predicted hue angles for LOCO (Leave-One-Color-Out) results. Shows actual color representation accuracy using the utils_color_decoding.py framework.

**Run**:
```bash
cd visualization
python3 visualize_loco_color_wheel.py
```

**Outputs** (in `results/loco/color_wheel_plots/`):
- **Per subject-ROI**: 6 run plots + 1 average plot (total: 10 subjects × 4 ROIs × 7 plots = 280 files)
- **Group comparisons**: 4 files (one per ROI showing HC vs CVD)
- **Total**: 284 PNG files (300 DPI)

**Plot structure**:
- **Left panel**: Color wheel (polar plot)
  - Large dots (outer circle): True hue positions
  - Small dots (inner circle): Predicted hues (angle = prediction, color = truth)
  - 0° at right (East), anticlockwise direction
- **Right panel**: Statistics summary
  - Per-color errors
  - Mean error vs chance level (90°)

**Features**:
- **Per-run plots**: Each of 6 runs separately (shows run-to-run variability)
- **Average plot**: All runs combined (shows all predictions as jittered dots)
- **True colors**: Accurate CIELab → RGB conversion for stimulus colors
- **Circular error**: Proper circular distance calculation (0-180°)

**Interpretation**:
- **Tight clustering**: Good predictions close to true hue
- **Dispersed dots**: High variability across runs
- **Systematic bias**: Predictions consistently off in one direction
- **Adjacent confusions**: Predictions shift to neighboring colors

**Key Results** (V1 ForwardEncoding):
- HC: 67-88° MAE (mean ~75°)
- CVD: 62-84° MAE (similar to HC, some individual variation)
- Chance level: 90°

---

### 2. LOCO Circular Performance Plots (Alternative view)

**Script**: `visualization/visualize_loco_circular.py`

**Purpose**: Polar plot showing per-color MAE aggregated across runs (different from color wheel above).

**Outputs** (in `results/loco/circular_plots/`):
- Individual ROI plots + combined 2×2 grid
- Shows MAE radial distance (not hue angles)

**Use case**: When you want to see interpolation difficulty per color (not individual predictions)

---

### Legacy Figures
- Channel tuning curves (8 color-selective channels)
- Reconstruction color wheel (32 hues)
- RDM heatmaps (8×8 color similarity)
- Accuracy by ROI and subject

---

## Implications for Phase 2

**Low LOSO performance + Low RDM correlation** → Individual heterogeneity is substantial

→ **Motivates Phase 2**: Quantify individual differences using Procrustes analysis
→ **Supports personalized approach**: Generic CVD filter unlikely to work

---

## References

- See main README.md for full references
- Related: Phase 2 (Procrustes CVD-HC comparison)
