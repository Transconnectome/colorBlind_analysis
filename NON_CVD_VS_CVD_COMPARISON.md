# Non-CVD vs CVD Comparison Analysis

**Date:** November 18, 2025
**Project:** Color Perception in Color Vision Deficiency using fMRI Forward Encoding Models
**Based on:** Brouwer & Heeger (2009, J. Neurosci.) methodology

---

## Table of Contents

1. [Research Background & Objectives](#1-research-background--objectives)
2. [Subject Groups Definition](#2-subject-groups-definition)
3. [Comparison Methodology](#3-comparison-methodology)
4. [Statistical Analysis Framework](#4-statistical-analysis-framework)
5. [Current Pipeline Outputs & Main Figures](#5-current-pipeline-outputs--main-figures)
6. [Perceptual Spacing Analysis](#6-perceptual-spacing-analysis)
7. [Red-Green Merging Analysis](#7-red-green-merging-analysis)
8. [Current Results Summary](#8-current-results-summary)
9. [Interpretation Guidelines](#9-interpretation-guidelines)
10. [Implementation Scripts](#10-implementation-scripts)
11. [Statistical Tests](#11-statistical-tests)
12. [Next Steps: Filter Design](#12-next-steps-filter-design)
13. [References & Related Work](#13-references--related-work)
14. [Appendix](#14-appendix)

---

## 1. Research Background & Objectives

### 1.1 Research Questions

**Primary Question:**
> How does color perception differ between individuals with normal color vision (Non-CVD) and those with color vision deficiency (CVD) at the neural level?

**Specific Questions:**
1. Do CVD individuals show different voxel activation patterns in visual cortex (V1-hV4)?
2. Can we successfully decode color information from CVD individuals' brain activity?
3. What are the differences in reconstruction accuracy between Non-CVD and CVD groups?
4. Which brain regions (V1/V2/V3/hV4) show the most significant group differences?
5. Can we design a transformation filter to map CVD patterns to Non-CVD patterns?

### 1.2 Two-Step Analysis Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: Color Reconstruction Method Formation                  │
│ ─────────────────────────────────────────────────────────────── │
│ Goal: Establish reliable forward encoding model for both groups│
│                                                                 │
│ Tasks:                                                          │
│  1. Build forward encoding model f: vox → CH (channels)        │
│  2. Validate on Non-CVD individuals                            │
│  3. Validate on CVD individuals                                │
│  4. Compare reconstruction performance between groups          │
│  5. Identify group-specific patterns                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: Filter Design (CVD → Non-CVD Transformation)          │
│ ─────────────────────────────────────────────────────────────── │
│ Goal: Find transformation g such that vox_NC = g(vox_CVD)     │
│                                                                 │
│ Formulation:                                                    │
│   CH_CVD = f_CVD(vox_CVD)                                      │
│   CH_NC  = f_NC(vox_NC)                                        │
│                                                                 │
│   Find g such that: CH_NC ≈ f_NC(g(vox_CVD))                  │
│                                                                 │
│ Assumption:                                                     │
│   f_CVD ≈ f_NC (encoding function similar)                     │
│   vox_CVD ≠ vox_NC (voxel patterns differ)                     │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Current Status

✅ **STEP 1 Completed:** Forward encoding model established and validated
🔄 **STEP 2 In Progress:** Analyzing group differences to inform filter design

---

## 2. Subject Groups Definition

### 2.1 Subject Categorization

| Subject ID | Group | Color Vision Status | Data Quality | Notes |
|------------|-------|---------------------|--------------|-------|
| **sub-01** | Non-CVD | Normal trichromat | ✅ Excellent | Pilot-matched preprocessing |
| **sub-02** | Non-CVD | Normal trichromat | ✅ Excellent | Best overall performance |
| **sub-03** | CVD | Deuteranomaly (red-green deficiency) | ✅ Good | Higher variability |
| **sub-04** | CVD | Deuteranomaly (red-green deficiency) | ✅ Good | Higher variability |

### 2.2 Group Characteristics

#### Non-CVD Group (N=2)
- Normal color discrimination (8/8 colors distinguishable)
- Regular 45° hue spacing in perceptual space
- Lower inter-subject variability
- Baseline for comparison

#### CVD Group (N=2)
- Deuteranomaly (red-green deficiency)
- Reduced discrimination for red-green axis
- Higher inter-subject variability (individual CVD patterns)
- Test group for transformation

### 2.3 Experimental Design

**Common Parameters:**
- **Stimulus:** 8 colors (45° spacing in CIELab hue space) + gray
- **TR:** 1.5s
- **Runs:** 6 runs per subject
- **ROIs:** V1, V2, V3, hV4 (Wang 2015 atlas)
- **Preprocessing:** fMRIPrep 25.0.0, MNI152NLin2009cAsym:res-2
- **Analysis:** Universal HRF with FIR (0-15s, 10 TRs)

---

## 3. Comparison Methodology

### 3.1 Multi-Level Comparison Framework

```
Level 1: RAW VOXEL PATTERNS
├─ Number of voxels (anatomical ROI size)
├─ Voxel responsiveness (|z| > 2.3)
├─ Peak z-score distributions
└─ Voxel color selectivity patterns

Level 2: UNIVARIATE FEATURES
├─ Universal HRF shape
├─ Optimal delay (peak response timing)
├─ Z-score magnitudes per color
└─ Signal-to-noise ratio

Level 3: MULTIVARIATE FEATURES (PCA)
├─ Component loadings (PC1-PC6)
├─ Explained variance per component
├─ Color space structure (PC1 vs PC2 vs PC3)
└─ Component stability across folds

Level 4: DECODING PERFORMANCE
├─ Classification accuracy (8-way color discrimination)
├─ Reconstruction error (trained colors)
├─ Novel color generalization error
└─ Per-color reconstruction accuracy

Level 5: ROI-SPECIFIC PATTERNS
├─ V1, V2, V3, hV4 comparisons
├─ Hierarchical processing differences
├─ ROI × Group interactions
└─ Method (zscore vs voxelSelect) × ROI interactions
```

### 3.2 Comparison Metrics

#### 3.2.1 Voxel-Level Metrics

| Metric | Definition | Purpose |
|--------|------------|---------|
| **N_voxels_anatomical** | Total voxels in anatomical ROI | Compare ROI sizes |
| **N_voxels_selected** | Voxels with \|z\| > 2.3 | Compare functional responsiveness |
| **Selection_percentage** | (selected / anatomical) × 100 | Group difference in color responsiveness |
| **Mean_max_z** | Average of max \|z\| across voxels | Signal strength comparison |
| **Z_distribution** | Histogram of z-scores | Pattern similarity analysis |

#### 3.2.2 HRF-Level Metrics

| Metric | Definition | Purpose |
|--------|------------|---------|
| **Optimal_delay** | TR of peak HRF response | Hemodynamic response timing |
| **HRF_peak_amplitude** | Maximum HRF magnitude | Response magnitude comparison |
| **HRF_shape** | Full HRF time course (0-15s) | Temporal dynamics comparison |
| **HRF_width** | Full-width at half-maximum | Response duration comparison |

#### 3.2.3 PCA-Level Metrics

| Metric | Definition | Purpose |
|--------|------------|---------|
| **Explained_variance** | Per-component variance (PC1-PC6) | Dimensionality comparison |
| **Component_loadings** | PC × color matrix | Color representation structure |
| **Component_stability** | Std across folds | Cross-validation reliability |
| **Color_space_distance** | Euclidean distances in PC space | Perceptual similarity preservation |

#### 3.2.4 Performance Metrics

| Metric | Definition | Purpose | Chance Level |
|--------|------------|---------|--------------|
| **Classification_accuracy** | Proportion correct (8-way) | Color discrimination | 12.5% |
| **Reconstruction_error** | Circular error (degrees) | Color identification accuracy | 90° |
| **Novel_color_error** | Generalization error (degrees) | Model generalization | 90° |
| **Per_run_variability** | Std of errors across runs | Reliability | - |

### 3.3 Comparison Approaches

#### Approach 1: Group-Level Averaging
```python
# Average across subjects within each group
Non_CVD_mean = mean([sub01, sub02])
CVD_mean = mean([sub03, sub04])

# Compare means
group_difference = CVD_mean - Non_CVD_mean
effect_size = group_difference / pooled_std
```

#### Approach 2: ROI-Specific Comparison
```python
# For each ROI separately
for roi in ['V1', 'V2', 'V3', 'hV4']:
    Non_CVD_roi = mean([sub01[roi], sub02[roi]])
    CVD_roi = mean([sub03[roi], sub04[roi]])
    roi_differences[roi] = CVD_roi - Non_CVD_roi
```

#### Approach 3: Method-Specific Comparison
```python
# For each method (zscore vs voxelSelect)
for method in ['zscore', 'voxelSelect']:
    Non_CVD_method = mean([sub01[method], sub02[method]])
    CVD_method = mean([sub03[method], sub04[method]])
    method_differences[method] = CVD_method - Non_CVD_method
```

#### Approach 4: Individual Subject Profiling
```python
# Treat each subject as unique case
for sub in ['01', '02', '03', '04']:
    subject_profile[sub] = {
        'group': 'CVD' if sub in ['03', '04'] else 'Non-CVD',
        'best_roi': argmin(reconstruction_error[sub, :]),
        'best_method': argmin(reconstruction_error[sub, :, :]),
        'performance_rank': rank(reconstruction_error)
    }
```

---

## 4. Statistical Analysis Framework

### 4.1 Descriptive Statistics

**For each metric, report:**
- **Mean ± Standard Deviation** (across subjects within group)
- **Median [IQR]** (for non-normal distributions)
- **Min, Max** (range)
- **Coefficient of Variation (CV)** = std / mean (for comparing variability)

**Example:**
```
Non-CVD Reconstruction Error: 13.72° ± 20.07° (CV = 146%)
CVD Reconstruction Error: 26.66° ± 26.45° (CV = 99%)
```

### 4.2 Effect Size Calculation

**Cohen's d:**
```python
# Between-group effect size
pooled_std = sqrt((std_NC**2 + std_CVD**2) / 2)
cohen_d = (mean_CVD - mean_NC) / pooled_std

# Interpretation:
#   |d| < 0.2: negligible
#   |d| < 0.5: small
#   |d| < 0.8: medium
#   |d| ≥ 0.8: large
```

### 4.3 Permutation Testing (Non-Parametric)

**Rationale:** Small sample size (N=2 per group) requires non-parametric approach

**Procedure:**
```python
# Null hypothesis: No group difference
# Alternative: CVD ≠ Non-CVD

observed_difference = mean(CVD) - mean(Non_CVD)

# Permutation test (10,000 iterations)
for i in range(10000):
    # Randomly shuffle group labels
    shuffled_labels = permute(['NC', 'NC', 'CVD', 'CVD'])

    # Compute difference under null
    perm_diff[i] = mean(group1) - mean(group2)

# Two-tailed p-value
p_value = mean(abs(perm_diff) >= abs(observed_difference))
```

### 4.4 Bootstrap Confidence Intervals

**For small sample sizes:**
```python
# Bootstrap 95% CI for group means
for _ in range(10000):
    bootstrap_sample_NC = resample([sub01, sub02], replace=True)
    bootstrap_sample_CVD = resample([sub03, sub04], replace=True)

    bootstrap_means_NC.append(mean(bootstrap_sample_NC))
    bootstrap_means_CVD.append(mean(bootstrap_sample_CVD))

# 95% CI
CI_NC = percentile(bootstrap_means_NC, [2.5, 97.5])
CI_CVD = percentile(bootstrap_means_CVD, [2.5, 97.5])
```

### 4.5 ROI × Group Interaction Analysis

**Two-way comparison:**
```
Factor 1: Group (Non-CVD vs CVD)
Factor 2: ROI (V1 vs V2 vs V3 vs hV4)

Interaction: Does group difference vary by ROI?
```

**Approach (descriptive due to small N):**
- Calculate effect size for each ROI separately
- Identify which ROIs show largest group differences
- Visual inspection of interaction patterns

### 4.6 Within-Subject Consistency

**Assess individual reliability:**
```python
# For each subject, compute across-run variability
for sub in subjects:
    run_errors = [reconstruction_error[sub, run] for run in range(6)]
    within_subject_std[sub] = std(run_errors)
    within_subject_cv[sub] = std(run_errors) / mean(run_errors)

# Compare groups
mean_within_subject_variability_NC = mean([std_sub01, std_sub02])
mean_within_subject_variability_CVD = mean([std_sub03, std_sub04])
```

---

## 5. Current Pipeline Outputs & Main Figures

### 5.1 Overview: Automatically Generated Figures

**From:** `fir_reconstruction_zScore.py` (lines 542-1780)

Each subject × ROI × method generates:

```
derivatives/{timestamp}/sub-{ID}/fir_reconstruction_uni_hrf/zScore/{ROI}_universal_hrf/figures/
│
├── 1_universal_hrf.png                    # Universal HRF time course (0-15s)
├── 2_zscore_matrix_full.png              # Z-score matrix (4 panels)
├── 3_pca_components.png                   # PCA color space (PC1×PC2×PC3)
├── 4_reconstruction_results.png           # ⭐ Circular color space (training + novel)
│
├── {ROI}_color_preference_wheel.png       # Voxel preferences (polar plot)
├── {ROI}_pca_component_loadings.png       # PCA loadings (top 5 components)
├── {ROI}_pca_colorspace_3d.png           # 3D scatter (PC1, PC2, PC3)
│
└── [Individual z-maps if --save-zmaps]
    ├── {ROI}_color_1_zmap.png
    ├── {ROI}_color_2_zmap.png
    └── ...
```

### 5.2 Main Figures for Non-CVD vs CVD Comparison

**Priority 1 (Essential):**
1. ✅ **Circular Color Space** (`4_reconstruction_results.png`)
   - Already generated
   - Shows angular accuracy
   - **NEED TO ADD:** Perceptual distance analysis

2. ✅ **PCA Color Space** (`3_pca_components.png`)
   - Already generated
   - Shows multivariate structure
   - **NEED TO ADD:** Distance preservation analysis

**Priority 2 (Important):**
3. 🆕 **Perceptual Distance Matrix** (NEW)
   - Compare pairwise color distances
   - Non-CVD vs CVD heatmap

4. 🆕 **Red-Green Merging Analysis** (NEW)
   - Focus on color_1~4 (red-yellow-green)
   - Angular compression visualization

5. 🆕 **Interval Uniformity Test** (NEW)
   - Are adjacent colors equally spaced?
   - Deviation from 45° intervals

**Priority 3 (Supplementary):**
6. ✅ **Universal HRF** (`1_universal_hrf.png`) - QC
7. ✅ **Z-score Matrix** (`2_zscore_matrix_full.png`) - Feature extraction QC

---

### 5.3 Figure 1: Circular Color Space Comparison ⭐ **MOST IMPORTANT**

**Based on:** Current `4_reconstruction_results.png` **+ New analyses**

**Layout:** 2 rows × 3 columns

```
┌──────────────────┬──────────────────┬──────────────────┐
│ A. Non-CVD       │ B. CVD           │ C. Group Overlay │
│ Training Colors  │ Training Colors  │ (mean ± SEM)     │
│                  │                  │                  │
│ Circular plot    │ Circular plot    │ Comparison       │
│ Error: 13.7°     │ Error: 26.7°     │ Δ = +13.0°       │
├──────────────────┼──────────────────┼──────────────────┤
│ D. Non-CVD       │ E. CVD           │ F. Angular       │
│ Novel Colors     │ Novel Colors     │ Distortion Map   │
│                  │                  │                  │
│ Circular plot    │ Circular plot    │ True vs Pred     │
│ Error: 80.1°     │ Error: 89.7°     │ by color region  │
└──────────────────┴──────────────────┴──────────────────┘
```

#### Panel A & B: Circular Plots (Current + Enhanced)

**Current visualization:**
- True hues at border (r=1.0, large markers)
- Predictions inside (r=0.85, small markers, jittered)
- Color-coded by true stimulus color

**NEW ADDITIONS:**
1. **Color region annotations:**
   ```python
   # Add colored arcs to mark color regions
   regions = {
       'Red-Green': (0, 180),      # color_1~4, CVD confusion zone
       'Blue-Yellow': (180, 360)   # color_5~8, CVD preserved
   }
   ```

2. **Error vectors:**
   ```python
   # Draw error lines from true to mean predicted
   for color in range(8):
       true_angle = true_hues[color]
       pred_angle = mean_predicted_hues[color]
       ax.plot([true_angle, pred_angle], [1.0, 0.85],
               color='gray', alpha=0.5, linewidth=1)
   ```

3. **Interval markers:**
   ```python
   # Mark ideal 45° intervals
   for i in range(8):
       ideal_angle = i * 45
       ax.axvline(np.deg2rad(ideal_angle),
                  color='gray', linestyle='--', alpha=0.3)
   ```

#### Panel C: Group Overlay (NEW)

**Purpose:** Direct visual comparison of Non-CVD vs CVD reconstruction

**Design:**
```python
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))

for color_idx in range(8):
    true_hue = true_hues[color_idx]

    # Non-CVD: blue markers
    mean_pred_NC = mean_predicted_hues_NC[color_idx]
    sem_NC = sem_predicted_hues_NC[color_idx]
    ax.scatter(np.deg2rad(mean_pred_NC), 0.9,
               s=100, color='blue', alpha=0.7, label='Non-CVD' if color_idx==0 else '')

    # CVD: red markers
    mean_pred_CVD = mean_predicted_hues_CVD[color_idx]
    sem_CVD = sem_predicted_hues_CVD[color_idx]
    ax.scatter(np.deg2rad(mean_pred_CVD), 0.85,
               s=100, color='red', alpha=0.7, label='CVD' if color_idx==0 else '')

    # True hue: black marker at border
    ax.scatter(np.deg2rad(true_hue), 1.0,
               s=150, color='black', marker='*', zorder=10)

    # Error bars (circular SEM)
    # Draw arc representing ±1 SEM
    if sem_NC > 0:
        arc_NC = np.linspace(np.deg2rad(mean_pred_NC - sem_NC),
                             np.deg2rad(mean_pred_NC + sem_NC), 20)
        ax.plot(arc_NC, np.full_like(arc_NC, 0.9),
                color='blue', linewidth=3, alpha=0.3)

    if sem_CVD > 0:
        arc_CVD = np.linspace(np.deg2rad(mean_pred_CVD - sem_CVD),
                              np.deg2rad(mean_pred_CVD + sem_CVD), 20)
        ax.plot(arc_CVD, np.full_like(arc_CVD, 0.85),
                color='red', linewidth=3, alpha=0.3)

ax.set_ylim([0, 1.1])
ax.set_title('Group Comparison: Reconstruction Accuracy', fontsize=14, fontweight='bold')
ax.legend(loc='upper right')
```

#### Panel F: Angular Distortion Map (NEW)

**Purpose:** Visualize systematic biases in color reconstruction

**Data:**
```python
# For each color, compute mean prediction error
angular_distortion = {
    'color_1': mean_pred_NC[0] - true_hues[0],  # Signed error (degrees)
    'color_2': mean_pred_NC[1] - true_hues[1],
    # ...
}

# CVD vs Non-CVD distortion
distortion_difference = angular_distortion_CVD - angular_distortion_NC
```

**Visualization:**
```python
fig, ax = plt.subplots(figsize=(10, 6))

colors = ['color_1', 'color_2', 'color_3', 'color_4',
          'color_5', 'color_6', 'color_7', 'color_8']
x = np.arange(len(colors))

# Plot distortion for each group
ax.bar(x - 0.2, distortion_NC, width=0.4, label='Non-CVD', alpha=0.7, color='blue')
ax.bar(x + 0.2, distortion_CVD, width=0.4, label='CVD', alpha=0.7, color='red')

# Mark red-green region
ax.axvspan(-0.5, 3.5, alpha=0.1, color='orange', label='Red-Green Region')

# Zero line
ax.axhline(0, color='black', linestyle='--', linewidth=1)

ax.set_ylabel('Angular Distortion (degrees)', fontsize=12)
ax.set_xlabel('Color', fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(colors, rotation=45)
ax.set_title('Systematic Bias: CVD vs Non-CVD', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(alpha=0.3)

plt.tight_layout()
```

**Interpretation:**
- **Positive distortion:** Predicted hue is clockwise from true hue
- **Negative distortion:** Predicted hue is counterclockwise from true hue
- **Large difference (CVD - Non-CVD):** CVD-specific bias

---

### 5.4 Figure 2: Perceptual Distance Matrix ⭐ **CRITICAL FOR CVD**

**Purpose:** Compare pairwise color distances in perceptual space

**Data:**
```python
# Compute distance matrix (8×8) for each subject
def compute_perceptual_distance_matrix(reconstructed_hues):
    """
    Compute pairwise circular distances between all color pairs

    Parameters:
    -----------
    reconstructed_hues : ndarray (8,)
        Predicted hue angles for 8 colors

    Returns:
    --------
    distance_matrix : ndarray (8, 8)
        Pairwise circular distances
    """
    n_colors = len(reconstructed_hues)
    D = np.zeros((n_colors, n_colors))

    for i in range(n_colors):
        for j in range(n_colors):
            # Circular distance (0-180 degrees)
            diff = abs(reconstructed_hues[i] - reconstructed_hues[j])
            D[i, j] = min(diff, 360 - diff)

    return D

# Compute for each group
D_NC = mean([compute_perceptual_distance_matrix(sub01_hues),
             compute_perceptual_distance_matrix(sub02_hues)])

D_CVD = mean([compute_perceptual_distance_matrix(sub03_hues),
              compute_perceptual_distance_matrix(sub04_hues)])

# Ideal distance matrix (uniform 45° spacing)
D_ideal = np.zeros((8, 8))
for i in range(8):
    for j in range(8):
        angular_diff = abs(i - j) * 45
        D_ideal[i, j] = min(angular_diff, 360 - angular_diff)
```

**Layout:** 1 row × 4 columns

```
┌────────────────┬────────────────┬────────────────┬────────────────┐
│ A. Ideal       │ B. Non-CVD     │ C. CVD         │ D. Difference  │
│ (45° spacing)  │ Actual         │ Actual         │ (CVD - Ideal)  │
│                │                │                │                │
│ 8×8 heatmap    │ 8×8 heatmap    │ 8×8 heatmap    │ 8×8 heatmap    │
│                │                │                │                │
│ Symmetric      │ r = 0.98       │ r = 0.85       │ Red = larger   │
│ Perfect        │ with ideal     │ with ideal     │ distance       │
└────────────────┴────────────────┴────────────────┴────────────────┘
```

**Code (Implementation):** See Section 10.1

**Key Metrics:**
```python
# Correlation with ideal
r_NC = np.corrcoef(D_ideal.flatten(), D_NC.flatten())[0, 1]
r_CVD = np.corrcoef(D_ideal.flatten(), D_CVD.flatten())[0, 1]

# RMSE from ideal
rmse_NC = np.sqrt(np.mean((D_NC - D_ideal)**2))
rmse_CVD = np.sqrt(np.mean((D_CVD - D_ideal)**2))

print(f"Non-CVD: r = {r_NC:.3f}, RMSE = {rmse_NC:.1f}°")
print(f"CVD: r = {r_CVD:.3f}, RMSE = {rmse_CVD:.1f}°")
```

**Expected Results:**
- **Non-CVD:** High correlation with ideal (r > 0.95), low RMSE (<10°)
- **CVD:** Lower correlation (r ~ 0.80-0.90), higher RMSE (>15°)
- **Red-green pairs (c1-c4):** Compressed distances in CVD

---

### 5.5 Figure 3: PCA Color Space with Distance Preservation

**Based on:** Current `3_pca_components.png` **+ New distance analysis**

**Layout:** 2 rows × 2 columns

```
┌──────────────────────┬──────────────────────┐
│ A. Non-CVD           │ B. CVD               │
│ PC1 × PC2 × PC3      │ PC1 × PC2 × PC3      │
│                      │                      │
│ 8 colors in 3D space │ 8 colors in 3D space │
│ Lines connect        │ Lines connect        │
│ adjacent colors      │ adjacent colors      │
├──────────────────────┼──────────────────────┤
│ C. Distance          │ D. Interval          │
│ Preservation         │ Uniformity           │
│                      │                      │
│ PCA dist vs True     │ Adjacent color dist  │
│ Scatter plot         │ Bar plot             │
└──────────────────────┴──────────────────────┘
```

**Code (Implementation):** See Section 10.1

**Key Metric: Interval Uniformity (Coefficient of Variation)**
```python
# Lower CV = more uniform spacing
cv_NC = np.std(intervals_NC) / np.mean(intervals_NC) * 100
cv_CVD = np.std(intervals_CVD) / np.mean(intervals_CVD) * 100

print(f"Non-CVD interval CV: {cv_NC:.1f}%")
print(f"CVD interval CV: {cv_CVD:.1f}%")

# Expected: CVD has higher CV (less uniform)
```

---

### 5.6 Supplementary Figures (Quality Control)

**S1. Universal HRF Comparison**
- **Current file:** `1_universal_hrf.png`
- **Purpose:** Ensure hemodynamic response is similar across groups
- **Expected:** No major group differences (HRF should be similar)

**S2. Z-Score Matrix Comparison**
- **Current file:** `2_zscore_matrix_full.png` (4 panels)
- **Purpose:** Compare voxel-level color selectivity
- **Enhancements:** Add group average heatmaps, compute selectivity index per group

**S3. ROI-by-ROI Breakdown**
- **Layout:** 4 rows (V1, V2, V3, hV4) × 3 columns (NC, CVD, Difference)
- **For each ROI:** Circular reconstruction plot, Distance matrix, Interval uniformity

**S4. Individual Subject Profiles**
- **Layout:** 4 subjects showing best ROI performance
- **Content:** Circular plot, Distance matrix, Performance summary

---

## 6. Perceptual Spacing Analysis

### 6.1 Multidimensional Scaling (MDS) Comparison

**Purpose:** Visualize perceptual color space in 2D

**Method:**
```python
from sklearn.manifold import MDS

# Apply MDS to distance matrices
mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)

coords_ideal = mds.fit_transform(D_ideal)
coords_NC = mds.fit_transform(D_NC)
coords_CVD = mds.fit_transform(D_CVD)
```

**Key Observation:**
- **Ideal:** Regular octagon (uniform spacing)
- **Non-CVD:** Nearly regular octagon (slight distortions)
- **CVD:** **Compressed red-green axis** (c1-c4 closer together)

### 6.2 Procrustes Analysis

**Purpose:** Quantify shape similarity between CVD and Non-CVD perceptual spaces

**Method:**
```python
from scipy.spatial import procrustes

# Align CVD to Non-CVD using Procrustes transformation
_, coords_CVD_aligned, disparity = procrustes(coords_NC, coords_CVD)

print(f"Procrustes disparity (Non-CVD vs CVD): {disparity:.4f}")
# Lower = more similar shape
# Expected: ~0.1-0.3 for CVD (moderate dissimilarity)
```

**Code (Full implementation):** See Section 10.1

---

## 7. Red-Green Merging Analysis ⭐ **CVD-SPECIFIC**

### 7.1 Color Confusion Matrix

**Purpose:** Identify which color pairs are most confused in CVD

**Key Metric: Red-Green Confusion Index**
```python
# Sum off-diagonal elements in red-green block (c1-c4)
rg_confusion_NC = np.sum(confusion_NC[0:4, 0:4]) - np.trace(confusion_NC[0:4, 0:4])
rg_confusion_CVD = np.sum(confusion_CVD[0:4, 0:4]) - np.trace(confusion_CVD[0:4, 0:4])

# Normalize by number of off-diagonal elements (12)
rg_confusion_NC /= 12
rg_confusion_CVD /= 12

print(f"Non-CVD red-green confusion: {rg_confusion_NC:.3f}")
print(f"CVD red-green confusion: {rg_confusion_CVD:.3f}")
print(f"Increase in CVD: {(rg_confusion_CVD - rg_confusion_NC):.3f}")

# Expected: CVD shows higher red-green confusion
```

### 9.2 Red-Green Axis Compression

**Purpose:** Quantify spatial compression along red-green axis

**Method:**
```python
# In perceptual space (MDS coordinates), compute spread along color axes

def compute_axis_spread(coords, axis_colors):
    """
    Compute spread (std) of colors along a specific axis

    Parameters:
    -----------
    coords : ndarray (8, 2)
        MDS coordinates
    axis_colors : list
        Indices of colors defining the axis (e.g., [0,1,2,3] for red-green)
    """
    # Compute centroid of axis colors
    centroid = coords[axis_colors].mean(axis=0)

    # Compute std of distances from centroid
    distances = np.linalg.norm(coords[axis_colors] - centroid, axis=1)
    spread = np.std(distances)

    return spread

# Red-green axis (c1-c4)
rg_spread_NC = compute_axis_spread(coords_NC, [0, 1, 2, 3])
rg_spread_CVD = compute_axis_spread(coords_CVD, [0, 1, 2, 3])

# Blue-yellow axis (c5-c8)
by_spread_NC = compute_axis_spread(coords_NC, [4, 5, 6, 7])
by_spread_CVD = compute_axis_spread(coords_CVD, [4, 5, 6, 7])

# Compression ratio
compression_rg = rg_spread_CVD / rg_spread_NC
compression_by = by_spread_CVD / by_spread_NC
```

**Expected Result:**
- **Red-green compression < 1.0:** CVD shows **reduced spread** along red-green axis
- **Blue-yellow compression ~ 1.0:** Blue-yellow axis preserved in CVD

**Code (Full implementation):** See Section 10.1

---

## 8. Current Results Summary

### 8.1 Overall Group Performance

**From:** `ANALYSIS_SUMMARY_20251117.md`

| Metric | Non-CVD | CVD | Difference | Effect |
|--------|---------|-----|------------|--------|
| **Classification Accuracy** | 100.0% | 100.0% | 0% | None |
| **Reconstruction Error (zscore)** | 13.72° ± 20.07 | 26.66° ± 26.45 | +12.94° | ⚠️ **~2× worse** |
| **Reconstruction Error (voxelSelect)** | 14.36° ± 13.38 | 31.27° ± 24.03 | +16.91° | ⚠️ **~2× worse** |
| **Novel Color Error (zscore)** | 80.05° ± 27.73 | 89.72° ± 23.67 | +9.67° | Moderate |
| **Novel Color Error (voxelSelect)** | 93.34° ± 22.52 | 89.00° ± 29.62 | -4.34° | n.s. |

**Key Findings:**
1. ✅ **Perfect classification** for both groups (100% accuracy)
2. ⚠️ **CVD reconstruction ~2× worse** than Non-CVD (13.72° → 26.66°)
3. ❌ **Novel colors challenging** for both groups (>80° errors)
4. 📊 **Higher variability** in CVD group (CV = 99% vs 146%)

### 8.2 ROI-Specific Findings

**Best Performing Configurations:**

| Rank | Subject | ROI | Method | Group | Reconstruction Error |
|------|---------|-----|--------|-------|---------------------|
| 1 | sub-01 | V2 | voxelSelect | Non-CVD | **2.38°** ⭐ |
| 2 | sub-02 | hV4 | zscore | Non-CVD | 3.63° |
| 3 | sub-01 | V3 | zscore | Non-CVD | 4.13° |
| 4 | sub-02 | V1 | voxelSelect | Non-CVD | 4.25° |
| 5 | sub-04 | V2 | zscore | CVD | 4.38° |

**Observations:**
- **Non-CVD dominates top ranks** (4 out of top 5)
- **V2 shows best performance** across both groups
- **sub-04 (CVD) shows promising V2 performance** (4.38°, rank 5)

**Worst Performing Configurations:**

| Rank | Subject | ROI | Method | Group | Reconstruction Error |
|------|---------|-----|--------|-------|---------------------|
| 1 | sub-04 | hV4 | voxelSelect | CVD | **77.00°** ⚠️ |
| 2 | sub-03 | V3 | voxelSelect | CVD | 51.50° |
| 3 | sub-04 | V3 | zscore | CVD | 41.38° |
| 4 | sub-03 | V1 | zscore | CVD | 40.56° |
| 5 | sub-03 | V3 | zscore | CVD | 41.38° |

**Observations:**
- **CVD subjects dominate worst ranks**
- **hV4 + voxelSelect = catastrophic failure** for CVD (77°)
- **V3 problematic for CVD** with both methods

### 8.3 ROI Comparison Table

**Average Reconstruction Error by Group × ROI:**

| ROI | Non-CVD (zscore) | Non-CVD (voxelSelect) | CVD (zscore) | CVD (voxelSelect) | Group Difference |
|-----|------------------|----------------------|--------------|-------------------|------------------|
| **V1** | 34.31° | **7.00°** ✓ | 40.56° | 22.81° | +13.25° |
| **V2** | 7.00° | 8.25° | **5.19°** ⭐ | 11.38° | -1.81° ✅ |
| **V3** | **4.38°** ⭐ | 20.69° | 41.38° | 36.75° | **+37.00°** ⚠️ |
| **hV4** | **9.19°** ✓ | 28.63° | 19.50° | 77.00° | +10.31° |

**Critical Insights:**
1. **V2 most robust across groups** (-1.81° difference, CVD actually better!)
2. **V3 shows largest group deficit** (+37° for CVD with zscore)
3. **V1 benefits from voxelSelect in Non-CVD** (34.31° → 7.00°)
4. **hV4 + voxelSelect catastrophic for CVD** (77° error)

### 8.4 Statistical Summary

**Effect Sizes (Cohen's d) for Reconstruction Error:**

```python
# Estimated effect sizes (would need individual subject data for precise values)

roi_effect_sizes = {
    'V1': (40.56 - 34.31) / pooled_std,   # Small-Medium
    'V2': (5.19 - 7.00) / pooled_std,      # Negligible (reversed)
    'V3': (41.38 - 4.38) / pooled_std,     # VERY LARGE ⚠️
    'hV4': (19.50 - 9.19) / pooled_std     # Medium
}

# V3 shows strongest group difference (likely |d| > 2.0)
```

---

## 9. Interpretation Guidelines

### 9.1 What Perfect Classification Tells Us

**Finding:** 100% accuracy for both Non-CVD and CVD

**Interpretation:**
- ✅ **8 colors are discriminable** in both groups at neural level
- ✅ **Diagonal LDA successfully separates** color representations
- ✅ **Sufficient signal-to-noise** in fMRI data
- ✅ **Preprocessing pipeline effective** for both groups

**Implication for filter design:**
- Neural representations ARE distinct in CVD
- Problem is NOT discrimination, but **color-to-hue mapping**

### 9.2 What Reconstruction Errors Tell Us

**Finding:** CVD shows ~2× higher errors (26.66° vs 13.72°)

**Interpretation:**
- ⚠️ **Forward encoding model less accurate for CVD**
- ⚠️ **Channel basis functions may not match CVD perceptual space**
- ⚠️ **Voxel patterns differ systematically** from Non-CVD

**Possible Causes:**
1. **Perceptual confusion:** Red-green confusions in CVD alter voxel patterns
2. **Channel mismatch:** 6-channel model (60° spacing) doesn't fit CVD space
3. **Individual variability:** Each CVD subject has unique deficit pattern
4. **Compensation strategies:** CVD may use different cues (luminance, saturation)

**Implication for filter design:**
- Need to transform voxel space, not just rescale
- May require CVD-specific channel basis functions
- Individual calibration likely necessary

### 9.3 What V2 Robustness Tells Us

**Finding:** V2 shows similar performance across groups (CVD even slightly better)

**Interpretation:**
- ✅ **V2 color processing relatively preserved in CVD**
- ✅ **Higher-level color representations more robust**
- ✅ **V2 may compensate for V1 deficits**

**Neural Basis:**
- V2 integrates across V1 inputs → averages out noise
- V2 color-selective cells have broader tuning
- V2 receives feedback from higher areas (color constancy)

**Implication for filter design:**
- **Start with V2 as target** for transformation
- V2 may be better "common space" for CVD ↔ Non-CVD mapping
- Filter could map: V1_CVD → V2_CVD → V2_NC → V1_NC

### 9.4 What V3 Deficit Tells Us

**Finding:** V3 shows largest group difference (+37° for CVD)

**Interpretation:**
- ⚠️ **V3 relies heavily on V1/V2 color opponency**
- ⚠️ **Red-green deficiency maximally impacts V3**
- ⚠️ **V3 color representation most affected in CVD**

**Neural Basis:**
- V3 integrates L-M (red-green) and S-(L+M) (blue-yellow) signals
- Deuteranomaly disrupts L-M channel input to V3
- V3 shape-from-color processing requires intact opponency

**Implication for filter design:**
- V3 is **hardest target** for transformation
- May need separate filter for V3
- Suggests hierarchical filter: V1 → V2 → V3 cascade

### 9.5 What Novel Color Failure Tells Us

**Finding:** Both groups show high errors (>80°) for novel colors

**Interpretation:**
- ❌ **Forward model overfits to 8 training colors**
- ❌ **Channel basis functions don't span full hue circle**
- ❌ **Generalization problem, NOT group-specific**

**Possible Causes:**
1. **Insufficient channel coverage:** 6 channels (60° spacing) too sparse
2. **Training data limitation:** Only 8 colors, 45° spacing
3. **Interpolation failure:** Novel colors fall between channel peaks
4. **Model assumption violation:** Linear model too simple

**Implication for filter design:**
- Novel color problem separate from CVD problem
- Filter design should focus on **trained colors first**
- May need more channels (e.g., 8 or 12) for full hue circle coverage

### 9.6 What Method Comparison Tells Us

**Finding:** zscore uses 235 voxels, voxelSelect 41 voxels (~5.7× reduction)

**Performance Trade-off:**
- zscore: 20.19° error, voxelSelect: 22.81° error (+2.6°)
- **Minimal performance loss with 83% voxel reduction**

**Interpretation:**
- ✅ **Most voxels weakly tuned** to color
- ✅ **Small subset highly color-selective**
- ✅ **Functional localization effective**

**Implication for filter design:**
- Use **voxelSelect for efficiency**
- Filter only needs to transform ~40 voxels, not 235
- Focus on high-SNR voxels reduces noise in filter estimation

---

## 10. Implementation Scripts

### 10.1 Main Analysis Script: `analyze_cvd_vs_noncvd.py`

**Purpose:** Comprehensive comparison of Non-CVD vs CVD color perception

**Key Functions:**
```python
def compute_distance_matrix(hues):
    """Compute pairwise circular distances (8×8 matrix)"""
    pass

def compute_adjacent_intervals(distance_matrix):
    """Extract distances between adjacent colors"""
    pass

def interval_uniformity_metric(intervals):
    """Coefficient of variation (CV) - lower = more uniform"""
    pass

def compute_rg_compression(coords_NC, coords_CVD):
    """Compute compression ratio along red-green axis"""
    pass

def analyze_group_comparison(timestamp, roi, output_dir):
    """Main analysis pipeline"""
    # 1. Load reconstruction results
    # 2. Compute group averages
    # 3. Compute distance matrices
    # 4. Apply MDS
    # 5. Compute metrics
    # 6. Generate figures
    pass
```

**Full implementation:** See REVISED Section 6 (lines 1024-1394)

**Usage:**
```bash
# Run for specific ROI
python analyze_cvd_vs_noncvd.py \
    --timestamp 20251117_021334 \
    --roi V2 \
    --output figures/cvd_comparison/V2

# Run for all ROIs
for roi in V1 V2 V3 hV4; do
    python analyze_cvd_vs_noncvd.py \
        --timestamp 20251117_021334 \
        --roi $roi \
        --output figures/cvd_comparison/$roi
done
```

---

## 11. Statistical Tests

### 11.1 Permutation Test: Group Differences

**Null hypothesis:** No difference between Non-CVD and CVD

```python
def permutation_test_group_difference(metric_NC, metric_CVD, n_permutations=10000):
    """
    Two-sample permutation test

    Returns:
    --------
    p_value : float
    """
    # Observed difference
    observed_diff = np.mean(metric_CVD) - np.mean(metric_NC)

    # Combine groups
    all_data = np.concatenate([metric_NC, metric_CVD])
    n_NC = len(metric_NC)

    # Permutation distribution
    perm_diffs = np.zeros(n_permutations)

    for i in range(n_permutations):
        # Shuffle labels
        shuffled = np.random.permutation(all_data)

        # Compute difference
        perm_NC = shuffled[:n_NC]
        perm_CVD = shuffled[n_NC:]
        perm_diffs[i] = np.mean(perm_CVD) - np.mean(perm_NC)

    # Two-tailed p-value
    p_value = np.mean(np.abs(perm_diffs) >= np.abs(observed_diff))

    return p_value, perm_diffs
```

### 11.2 Bootstrap Confidence Intervals

```python
def bootstrap_ci(data, n_bootstrap=10000, ci=95):
    """
    Bootstrap confidence interval

    Returns:
    --------
    ci_lower, ci_upper : float
    """
    bootstrap_means = np.zeros(n_bootstrap)

    for i in range(n_bootstrap):
        # Resample with replacement
        sample = np.random.choice(data, size=len(data), replace=True)
        bootstrap_means[i] = np.mean(sample)

    # Percentile method
    alpha = (100 - ci) / 2
    ci_lower = np.percentile(bootstrap_means, alpha)
    ci_upper = np.percentile(bootstrap_means, 100 - alpha)

    return ci_lower, ci_upper
```

---

## 12. Next Steps: Filter Design

### 12.1 Filter Design Goals

**Primary Goal:**
> Design transformation **g(x)** such that:
> ```
> CH_NC ≈ f_NC(g(vox_CVD))
> ```
> where **CH_NC** = channel responses from Non-CVD forward model

**Assumptions:**
1. **f_NC ≈ f_CVD:** Forward encoding function similar across groups
2. **vox_CVD ≠ vox_NC:** Voxel activation patterns differ due to CVD
3. **g is learnable:** Transformation exists and can be estimated from data

### 12.2 Filter Design Approaches

#### Approach 1: Linear Transformation Matrix

**Model:**
```python
# Learn linear transformation W
vox_NC_predicted = W @ vox_CVD

# Estimate W by minimizing:
loss = ||vox_NC_actual - W @ vox_CVD||^2

# Regularized least squares
W = (vox_CVD @ vox_CVD.T + λI)^(-1) @ (vox_CVD @ vox_NC.T)
```

**Pros:**
- Simple, interpretable
- Closed-form solution
- Low parameter count

**Cons:**
- May be too restrictive
- Assumes linear relationship

---

#### Approach 2: Nonlinear Neural Network

**Model:**
```python
# 3-layer MLP
def filter_network(vox_CVD):
    h1 = ReLU(W1 @ vox_CVD + b1)  # 50 hidden units
    h2 = ReLU(W2 @ h1 + b2)       # 50 hidden units
    vox_NC_pred = W3 @ h2 + b3     # Output layer
    return vox_NC_pred

# Train with MSE loss
loss = MSE(vox_NC_actual, filter_network(vox_CVD))
```

**Pros:**
- Can capture nonlinear relationships
- Flexible capacity

**Cons:**
- Needs more training data
- Risk of overfitting (only 2 CVD subjects)
- Less interpretable

---

#### Approach 3: Channel-Based Transformation

**Model:**
```python
# Transform in channel space, not voxel space
CH_CVD = f_CVD(vox_CVD)  # Decode to channels
CH_NC_pred = T @ CH_CVD   # Transform channels
vox_NC_pred = f_NC^(-1)(CH_NC_pred)  # Encode to voxels

# Learn channel transformation T (6×6 matrix)
T = argmin ||CH_NC_actual - T @ CH_CVD||^2
```

**Pros:**
- Lower dimensionality (6 channels vs 41 voxels)
- Interpretable (color-to-color mapping)
- Aligns with perceptual space

**Cons:**
- Requires inverting f_NC (may not exist)
- Assumes channels are meaningful intermediate representation

---

#### Approach 4: Color-Specific Shift Vectors

**Model:**
```python
# Learn shift vector for each color
for color in range(8):
    shift_vector[color] = mean(vox_NC[color] - vox_CVD[color])

# Apply color-dependent shift
def transform(vox_CVD, color_label):
    return vox_CVD + shift_vector[color_label]
```

**Pros:**
- Very interpretable
- Color-specific corrections
- Simple to implement

**Cons:**
- Requires knowing color label
- Only works for trained colors
- Doesn't generalize to novel colors

---

### 12.3 Training Data Strategy

**Challenge:** Only 2 CVD subjects

**Solution 1: Leave-One-Subject-Out CV**
```python
# Train on sub-03, test on sub-04
# Train on sub-04, test on sub-03
# Average performance
```

**Solution 2: Augment with Simulated CVD**
```python
# Simulate CVD in Non-CVD subjects by:
# 1. Projecting colors onto CVD confusion line
# 2. Applying Brettel transformation
# 3. Generate "pseudo-CVD" voxel patterns
```

**Solution 3: Use Held-Out Runs**
```python
# Each subject has 6 runs
# Train on runs 1-5, test on run 6
# 6-fold CV within each subject
# Pool across subjects
```

### 12.4 Evaluation Metrics for Filter

**Metric 1: Voxel Pattern Similarity**
```python
# Correlation between transformed and actual
r = corr(g(vox_CVD), vox_NC_actual)
```

**Metric 2: Reconstruction Error After Filtering**
```python
# Apply forward model to filtered voxels
CH_pred = f_NC(g(vox_CVD))
hue_pred = decode_channels(CH_pred)
error = circular_distance(hue_pred, hue_actual)
```

**Metric 3: Channel Space Alignment**
```python
# Compare channel outputs
CH_CVD_filtered = f_NC(g(vox_CVD))
CH_NC_actual = f_NC(vox_NC)
alignment = mean(|CH_CVD_filtered - CH_NC_actual|)
```

**Metric 4: Perceptual Validity**
```python
# Check if color confusions match CVD perceptual confusions
# E.g., red-green should remain confused, blue-yellow preserved
confusion_matrix_filtered = classify(g(vox_CVD))
validate_against_ishihara_scores()
```

### 12.5 Validation Strategy

**Stage 1: Within-Subject Validation**
- Train filter on runs 1-5 of sub-03
- Test on run 6 of sub-03
- Repeat for sub-04

**Stage 2: Cross-Subject Validation**
- Train filter on all runs of sub-03
- Test on all runs of sub-04
- Repeat reversed (train on sub-04, test on sub-03)

**Stage 3: Cross-ROI Validation**
- Train filter on V2 (best ROI)
- Test on V1, V3, hV4
- Check if filter generalizes across visual hierarchy

**Stage 4: Novel Color Test**
- Apply filter to novel color voxel patterns
- Check if generalization improves
- Compare to Non-CVD novel color performance

### 12.6 Success Criteria

**Minimum Criteria (Filter is useful):**
- Reconstruction error reduces by ≥20% after filtering
- Correlation between filtered and actual voxels r > 0.5
- Improvement generalizes to held-out subject

**Target Criteria (Filter is effective):**
- CVD reconstruction error approaches Non-CVD levels (< 15°)
- Channel space alignment within 10% of Non-CVD
- Novel color performance improves (error < 70°)

**Ideal Criteria (Filter is transformative):**
- CVD performance indistinguishable from Non-CVD (p > 0.05)
- Filter generalizes across all ROIs
- Individual filter per subject performs better than group filter

### 12.7 Implementation Plan

```python
# File: cvd_filter_design.py

# ============================================================================
# STEP 1: Load and Prepare Data
# ============================================================================
def load_group_data():
    """
    Load voxel patterns for all subjects
    Returns: dict with keys 'Non-CVD', 'CVD'
    """
    data = {
        'Non-CVD': {
            'sub-01': load_subject_data('01', roi='V2', method='voxelSelect'),
            'sub-02': load_subject_data('02', roi='V2', method='voxelSelect')
        },
        'CVD': {
            'sub-03': load_subject_data('03', roi='V2', method='voxelSelect'),
            'sub-04': load_subject_data('04', roi='V2', method='voxelSelect')
        }
    }
    return data

# ============================================================================
# STEP 2: Estimate Filter (Linear Approach)
# ============================================================================
def estimate_linear_filter(vox_CVD, vox_NC, regularization=0.1):
    """
    Estimate linear transformation W: vox_CVD → vox_NC

    Parameters:
    -----------
    vox_CVD : ndarray (n_samples, n_voxels)
        CVD voxel patterns
    vox_NC : ndarray (n_samples, n_voxels)
        Non-CVD voxel patterns (target)
    regularization : float
        Ridge regularization parameter

    Returns:
    --------
    W : ndarray (n_voxels, n_voxels)
        Transformation matrix
    """
    # Ridge regression
    n_voxels = vox_CVD.shape[1]
    W = np.linalg.solve(
        vox_CVD.T @ vox_CVD + regularization * np.eye(n_voxels),
        vox_CVD.T @ vox_NC
    )
    return W

# ============================================================================
# STEP 3: Apply Filter
# ============================================================================
def apply_filter(vox_CVD, W):
    """
    Transform CVD voxel patterns to Non-CVD-like patterns
    """
    return vox_CVD @ W

# ============================================================================
# STEP 4: Evaluate Filter
# ============================================================================
def evaluate_filter(vox_CVD_filtered, vox_NC_actual):
    """
    Compute evaluation metrics
    """
    # Voxel pattern correlation
    correlations = [
        np.corrcoef(vox_CVD_filtered[i], vox_NC_actual[i])[0, 1]
        for i in range(len(vox_CVD_filtered))
    ]

    # MSE
    mse = np.mean((vox_CVD_filtered - vox_NC_actual)**2)

    # Cosine similarity
    cosine_sim = np.mean([
        np.dot(vox_CVD_filtered[i], vox_NC_actual[i]) /
        (np.linalg.norm(vox_CVD_filtered[i]) * np.linalg.norm(vox_NC_actual[i]))
        for i in range(len(vox_CVD_filtered))
    ])

    return {
        'correlation': np.mean(correlations),
        'mse': mse,
        'cosine_similarity': cosine_sim
    }

# ============================================================================
# STEP 5: Reconstruction Performance After Filtering
# ============================================================================
def test_reconstruction_after_filter(vox_CVD_filtered, true_hues):
    """
    Apply forward encoding model to filtered voxels
    Compare reconstruction error before/after filtering
    """
    # Use Non-CVD forward model
    forward_model = load_forward_model(group='Non-CVD', roi='V2')

    # Decode
    predicted_hues = forward_model.predict(vox_CVD_filtered)

    # Error
    errors = circular_distance(predicted_hues, true_hues)
    mean_error = np.mean(errors)

    return mean_error, errors
```

### 12.8 Expected Outcomes

**Best Case Scenario:**
- Linear filter reduces CVD reconstruction error to Non-CVD levels
- Filter generalizes across subjects and ROIs
- Interpretation: CVD neural representations are linearly transformable

**Moderate Success:**
- Filter reduces error by 30-50%
- Works for some colors (e.g., blue-yellow preserved, red-green improved)
- Requires subject-specific calibration

**Limited Success:**
- Filter provides small improvement (10-20% error reduction)
- Suggests nonlinear or higher-dimensional transformation needed
- Motivates deep learning approach

**Failure Case:**
- No improvement or performance degrades
- Indicates fundamental difference in neural code, not just linear shift
- Suggests CVD representations use different basis (e.g., luminance-based)

---

## 13. References & Related Work

### 13.1 Key Papers

1. **Brouwer, G. J., & Heeger, D. J. (2009).** Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.
   - Foundation for forward encoding model
   - 6-channel basis functions

2. **Barbur, J. L., & Rodriguez-Carmona, M. (2015).** Color vision changes in normal aging. In *Handbook of Color Psychology* (pp. 180-196). Cambridge University Press.
   - CVD neural basis
   - Perceptual compensation strategies

3. **Gegenfurtner, K. R., & Kiper, D. C. (2003).** Color vision. *Annual Review of Neuroscience*, 26, 181-206.
   - V1-V4 color processing hierarchy
   - Color opponency mechanisms

4. **Wang, L., Mruczek, R. E., Arcaro, M. J., & Kastner, S. (2015).** Probabilistic maps of visual topography in human cortex. *Cerebral Cortex*, 25(10), 3911-3931.
   - Visual area atlas (ROI definition)

### 13.2 CVD Resources

- **Ishihara Test:** Standard color vision assessment
- **Farnsworth-Munsell 100 Hue Test:** Fine-grained discrimination
- **Brettel et al. (1997):** CVD simulation algorithms
- **Colorimetry standards:** CIE 1976 L\*a\*b\* color space

---

## 14. Appendix

### 14.1 Statistical Power Analysis

**Sample Size Considerations:**
- N=2 per group is **severely underpowered** for inferential statistics
- Effect sizes can be estimated, but significance testing unreliable
- Focus on **effect sizes and descriptive patterns**
- Bootstrap and permutation tests recommended

**Power Calculation (Example):**
```python
# To detect Cohen's d = 1.0 (large effect) with 80% power:
required_n = 16 per group  # Current: 2 per group

# To detect Cohen's d = 0.5 (medium effect) with 80% power:
required_n = 64 per group

# Current study can only detect VERY large effects (d > 2.0)
```

### 14.2 Data Availability

**Current Data:**
- ✅ 4 subjects fully processed (sub-01, sub-02, sub-03, sub-04)
- ✅ All ROIs available (V1, V2, V3, hV4)
- ✅ Both methods completed (zscore, voxelSelect)
- ✅ Results from timestamp: 20251117_021334

**Location:**
```
/scratch/connectome/haba6030/colorBlind/derivatives/20251117_021334/
├── sub-01/fir_reconstruction_uni_hrf/zScore/{ROI}_universal_hrf/
├── sub-02/fir_reconstruction_uni_hrf/zScore/{ROI}_universal_hrf/
├── sub-03/fir_reconstruction_uni_hrf/zScore/{ROI}_universal_hrf/
└── sub-04/fir_reconstruction_uni_hrf/zScore/{ROI}_universal_hrf/
```

### 14.3 Code for Analysis

**Main Analysis Script:**
```bash
# Compare groups
python compare_cvd_vs_noncvd.py \
    --timestamp 20251117_021334 \
    --subjects 01 02 03 04 \
    --rois V1 V2 V3 hV4 \
    --output figures/group_comparison/
```

**Generate All Figures:**
```bash
# Main figures
python generate_figures.py --type main --output figures/main/

# Supplementary figures
python generate_figures.py --type supplementary --output figures/supplementary/

# QC figures
python generate_figures.py --type qc --output figures/qc/
```

---

## Summary

This document provides a comprehensive framework for comparing Non-CVD and CVD individuals in color perception using fMRI forward encoding models.

**Key Deliverables:**
1. ✅ Comparison methodology defined (Sections 1-4)
2. ✅ Current pipeline outputs documented (Section 5)
3. ✅ Perceptual spacing analysis designed (Section 6)
4. ✅ Red-green merging analysis specified (Section 7)
5. ✅ Current results summarized (Section 8)
6. ✅ Interpretation guidelines provided (Section 9)
7. ✅ Implementation scripts outlined (Section 10)
8. ✅ Statistical tests specified (Section 11)
9. ✅ Filter design plan detailed (Section 12)

**Next Actions:**
1. **Implement** `analyze_cvd_vs_noncvd.py` (Section 10)
2. **Generate** all required figures (Sections 5-7)
3. **Run** statistical analyses (Section 11)
4. **Write** manuscript sections based on results
5. **Begin** filter design experiments (Section 12)

**Key Analyses (Practical Focus):**
- ⭐ Perceptual distance matrices (8×8)
- ⭐ Red-green compression ratio
- ⭐ Interval uniformity (CV)
- ⭐ Angular distortion maps
- ⭐ Procrustes alignment

**For Questions:**
- See `COMPREHENSIVE_PIPELINE_DOCUMENTATION.md` for code details
- See `ANALYSIS_SUMMARY_20251117.md` for latest results
- See `CLAUDE.md` for project context
- See `fir_reconstruction_zScore.py` for current pipeline

---

**Document Version:** 2.0 - **MERGED VERSION**
**Last Updated:** November 18, 2025
**Merge Date:** November 18, 2025
**Status:** Complete - Ready for Implementation

**Changes from v1.0:**
- ✅ Merged with REVISED version focusing on current pipeline outputs
- ✅ Added Perceptual Spacing Analysis (Section 6)
- ✅ Added Red-Green Merging Analysis (Section 7)
- ✅ Added Implementation Scripts (Section 10)
- ✅ Added Statistical Tests (Section 11)
- ✅ Emphasized practical, current-figure-focused approach
- ✅ Integrated circular graph analysis with perceptual spacing metrics
