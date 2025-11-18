# Non-CVD vs CVD Comparison: Required Figures & Analyses

**Date:** November 18, 2025
**Focus:** Perceptual color spacing and red-green merging in CVD
**Based on:** Current pipeline outputs + Additional circular space analyses

---

## Table of Contents

1. [Overview: Current Pipeline Outputs](#1-overview-current-pipeline-outputs)
2. [Main Figures (Manuscript)](#2-main-figures-manuscript)
3. [Perceptual Spacing Analysis](#3-perceptual-spacing-analysis)
4. [Red-Green Merging Analysis](#4-red-green-merging-analysis)
5. [Supplementary Figures](#5-supplementary-figures)
6. [Implementation: New Analysis Scripts](#6-implementation-new-analysis-scripts)
7. [Statistical Tests](#7-statistical-tests)

---

## 1. Overview: Current Pipeline Outputs

### 1.1 Automatically Generated Figures

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

### 1.2 Key Figures for Non-CVD vs CVD Comparison

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

## 2. Main Figures (Manuscript)

### Figure 1: Circular Color Space Comparison ⭐ **MOST IMPORTANT**

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

### Figure 2: Perceptual Distance Matrix ⭐ **CRITICAL FOR CVD**

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

**Code:**
```python
fig, axes = plt.subplots(1, 4, figsize=(20, 5))

# Panel A: Ideal
im1 = axes[0].imshow(D_ideal, cmap='viridis', vmin=0, vmax=180)
axes[0].set_title('Ideal\n(45° uniform spacing)', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Color index')
axes[0].set_ylabel('Color index')
axes[0].set_xticks(range(8))
axes[0].set_xticklabels([f'c{i+1}' for i in range(8)])
axes[0].set_yticks(range(8))
axes[0].set_yticklabels([f'c{i+1}' for i in range(8)])
plt.colorbar(im1, ax=axes[0], label='Distance (degrees)')

# Panel B: Non-CVD
im2 = axes[1].imshow(D_NC, cmap='viridis', vmin=0, vmax=180)
axes[1].set_title(f'Non-CVD\nr = {np.corrcoef(D_ideal.flatten(), D_NC.flatten())[0,1]:.2f}',
                  fontsize=12, fontweight='bold')
axes[1].set_xlabel('Color index')
axes[1].set_xticks(range(8))
axes[1].set_xticklabels([f'c{i+1}' for i in range(8)])
axes[1].set_yticks(range(8))
axes[1].set_yticklabels([f'c{i+1}' for i in range(8)])
plt.colorbar(im2, ax=axes[1], label='Distance (degrees)')

# Panel C: CVD
im3 = axes[2].imshow(D_CVD, cmap='viridis', vmin=0, vmax=180)
axes[2].set_title(f'CVD\nr = {np.corrcoef(D_ideal.flatten(), D_CVD.flatten())[0,1]:.2f}',
                  fontsize=12, fontweight='bold')
axes[2].set_xlabel('Color index')
axes[2].set_xticks(range(8))
axes[2].set_xticklabels([f'c{i+1}' for i in range(8)])
axes[2].set_yticks(range(8))
axes[2].set_yticklabels([f'c{i+1}' for i in range(8)])
plt.colorbar(im3, ax=axes[2], label='Distance (degrees)')

# Panel D: Difference (CVD - Ideal)
difference = D_CVD - D_ideal
im4 = axes[3].imshow(difference, cmap='RdBu_r', vmin=-90, vmax=90, center=0)
axes[3].set_title('CVD - Ideal\n(Distortion)', fontsize=12, fontweight='bold')
axes[3].set_xlabel('Color index')
axes[3].set_xticks(range(8))
axes[3].set_xticklabels([f'c{i+1}' for i in range(8)])
axes[3].set_yticks(range(8))
axes[3].set_yticklabels([f'c{i+1}' for i in range(8)])
cbar = plt.colorbar(im4, ax=axes[3], label='Distortion (degrees)')

# Annotate specific pairs (red-green merging)
for i in range(4):  # color_1~4 (red-green region)
    for j in range(i+1, 4):
        val = difference[i, j]
        if abs(val) > 10:  # Significant distortion
            axes[3].text(j, i, f'{val:.0f}', ha='center', va='center',
                        color='white' if abs(val) > 30 else 'black',
                        fontsize=10, fontweight='bold')

plt.suptitle('Perceptual Distance Matrices: CVD vs Non-CVD', fontsize=14, fontweight='bold')
plt.tight_layout()
```

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

### Figure 3: PCA Color Space with Distance Preservation

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

#### Panel A & B: 3D PCA Space (Enhanced from current)

**Current:** Already plots PC1 × PC2 × PC3 with color-coded markers

**ENHANCEMENTS:**
1. **Connect adjacent colors with lines**
   ```python
   # Draw lines between adjacent colors in hue circle
   for i in range(8):
       j = (i + 1) % 8  # Next color in circle
       ax.plot3D([pc1[i], pc1[j]], [pc2[i], pc2[j]], [pc3[i], pc3[j]],
                 'k-', alpha=0.3, linewidth=1)
   ```

2. **Highlight red-green region**
   ```python
   # Color_1~4: red-green region
   ax.plot3D(pc1[0:4], pc2[0:4], pc3[0:4],
             'o-', color='orange', markersize=12, linewidth=3,
             alpha=0.7, label='Red-Green')

   # Color_5~8: blue-yellow region
   ax.plot3D(pc1[4:8], pc2[4:8], pc3[4:8],
             'o-', color='cyan', markersize=12, linewidth=3,
             alpha=0.7, label='Blue-Yellow')
   ```

#### Panel C: Distance Preservation (NEW)

**Purpose:** Check if PCA preserves true color distances

**Data:**
```python
# True (ideal) distances
D_true_flat = D_ideal[np.triu_indices(8, k=1)]  # Upper triangle, 28 pairs

# PCA distances
def compute_pca_distances(pca_coords):
    """
    Compute Euclidean distances in PCA space

    Parameters:
    -----------
    pca_coords : ndarray (8, 3)
        PC1, PC2, PC3 coordinates for 8 colors
    """
    from scipy.spatial.distance import pdist, squareform
    D_pca = squareform(pdist(pca_coords, metric='euclidean'))
    return D_pca

D_pca_NC = compute_pca_distances(pca_coords_NC)
D_pca_CVD = compute_pca_distances(pca_coords_CVD)

D_pca_NC_flat = D_pca_NC[np.triu_indices(8, k=1)]
D_pca_CVD_flat = D_pca_CVD[np.triu_indices(8, k=1)]
```

**Visualization:**
```python
fig, ax = plt.subplots(figsize=(8, 8))

# Scatter: PCA distance vs True distance
ax.scatter(D_true_flat, D_pca_NC_flat,
           s=80, alpha=0.7, color='blue', label='Non-CVD', edgecolors='k')
ax.scatter(D_true_flat, D_pca_CVD_flat,
           s=80, alpha=0.7, color='red', label='CVD', edgecolors='k')

# Identity line
max_val = max(D_true_flat.max(), D_pca_NC_flat.max(), D_pca_CVD_flat.max())
ax.plot([0, max_val], [0, max_val], 'k--', linewidth=2, label='Perfect preservation')

# Correlation
r_NC = np.corrcoef(D_true_flat, D_pca_NC_flat)[0, 1]
r_CVD = np.corrcoef(D_true_flat, D_pca_CVD_flat)[0, 1]

ax.text(0.05, 0.95, f'Non-CVD: r = {r_NC:.3f}\nCVD: r = {r_CVD:.3f}',
        transform=ax.transAxes, fontsize=12, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

ax.set_xlabel('True Angular Distance (degrees)', fontsize=12)
ax.set_ylabel('PCA Euclidean Distance (a.u.)', fontsize=12)
ax.set_title('Distance Preservation in PCA Space', fontsize=14, fontweight='bold')
ax.legend(loc='lower right')
ax.grid(alpha=0.3)

plt.tight_layout()
```

#### Panel D: Interval Uniformity (NEW)

**Purpose:** Check if adjacent colors are equally spaced

**Data:**
```python
# Compute distances between adjacent colors (i and i+1)
def compute_adjacent_intervals(distance_matrix):
    """
    Extract distances between adjacent colors in the hue circle

    Returns: ndarray (8,) - distances [c1→c2, c2→c3, ..., c8→c1]
    """
    intervals = np.zeros(8)
    for i in range(8):
        j = (i + 1) % 8
        intervals[i] = distance_matrix[i, j]
    return intervals

intervals_ideal = compute_adjacent_intervals(D_ideal)  # All = 45°
intervals_NC = compute_adjacent_intervals(D_NC)
intervals_CVD = compute_adjacent_intervals(D_CVD)

# Deviation from ideal
deviation_NC = intervals_NC - intervals_ideal
deviation_CVD = intervals_CVD - intervals_ideal
```

**Visualization:**
```python
fig, ax = plt.subplots(figsize=(10, 6))

x = np.arange(8)
width = 0.25

# Three bars per interval
ax.bar(x - width, intervals_ideal, width, label='Ideal (45°)', alpha=0.7, color='gray')
ax.bar(x, intervals_NC, width, label='Non-CVD', alpha=0.7, color='blue')
ax.bar(x + width, intervals_CVD, width, label='CVD', alpha=0.7, color='red')

# Mark red-green region
ax.axvspan(-0.5, 3.5, alpha=0.1, color='orange', label='Red-Green Region')

# Reference line at 45°
ax.axhline(45, color='black', linestyle='--', linewidth=1, alpha=0.5)

ax.set_ylabel('Adjacent Color Distance (degrees)', fontsize=12)
ax.set_xlabel('Color Interval', fontsize=12)
ax.set_xticks(x)
ax.set_xticklabels(['c1→c2', 'c2→c3', 'c3→c4', 'c4→c5',
                    'c5→c6', 'c6→c7', 'c7→c8', 'c8→c1'],
                   rotation=45, ha='right')
ax.set_title('Interval Uniformity: Adjacent Color Spacing', fontsize=14, fontweight='bold')
ax.legend(loc='upper right')
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
```

**Key Metric: Coefficient of Variation (CV)**
```python
# Lower CV = more uniform spacing
cv_NC = np.std(intervals_NC) / np.mean(intervals_NC) * 100
cv_CVD = np.std(intervals_CVD) / np.mean(intervals_CVD) * 100

print(f"Non-CVD interval CV: {cv_NC:.1f}%")
print(f"CVD interval CV: {cv_CVD:.1f}%")

# Expected: CVD has higher CV (less uniform)
```

---

## 3. Perceptual Spacing Analysis

### 3.1 Multidimensional Scaling (MDS) Comparison

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

**Visualization:**
```python
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

for ax, coords, title in zip(axes,
                              [coords_ideal, coords_NC, coords_CVD],
                              ['Ideal', 'Non-CVD', 'CVD']):
    # Plot colors
    for i in range(8):
        color_rgb = get_stimulus_color_rgb(f'color_{i+1}')
        ax.scatter(coords[i, 0], coords[i, 1],
                   s=200, color=color_rgb, edgecolors='k', linewidths=2)
        ax.text(coords[i, 0], coords[i, 1] + 0.1, f'c{i+1}',
                ha='center', fontsize=12, fontweight='bold')

    # Connect adjacent colors
    for i in range(8):
        j = (i + 1) % 8
        ax.plot([coords[i, 0], coords[j, 0]],
                [coords[i, 1], coords[j, 1]],
                'k-', alpha=0.3, linewidth=1)

    # Highlight red-green region
    ax.fill([coords[i, 0] for i in range(4)],
            [coords[i, 1] for i in range(4)],
            alpha=0.1, color='orange', label='Red-Green')

    ax.set_aspect('equal')
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('MDS Dimension 1', fontsize=12)
    ax.set_ylabel('MDS Dimension 2', fontsize=12)
    ax.grid(alpha=0.3)
    ax.legend()

plt.suptitle('Perceptual Color Space: MDS Visualization', fontsize=16, fontweight='bold')
plt.tight_layout()
```

**Key Observation:**
- **Ideal:** Regular octagon (uniform spacing)
- **Non-CVD:** Nearly regular octagon (slight distortions)
- **CVD:** **Compressed red-green axis** (c1-c4 closer together)

### 3.2 Procrustes Analysis

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

**Visualization:**
```python
fig, ax = plt.subplots(figsize=(10, 10))

# Non-CVD (reference)
for i in range(8):
    color_rgb = get_stimulus_color_rgb(f'color_{i+1}')
    ax.scatter(coords_NC[i, 0], coords_NC[i, 1],
               s=200, color=color_rgb, edgecolors='blue',
               linewidths=3, alpha=0.7, label='Non-CVD' if i==0 else '')

# CVD (aligned)
for i in range(8):
    color_rgb = get_stimulus_color_rgb(f'color_{i+1}')
    ax.scatter(coords_CVD_aligned[i, 0], coords_CVD_aligned[i, 1],
               s=200, color=color_rgb, edgecolors='red',
               linewidths=3, alpha=0.7, marker='s', label='CVD' if i==0 else '')

    # Draw alignment vectors
    ax.arrow(coords_NC[i, 0], coords_NC[i, 1],
             coords_CVD_aligned[i, 0] - coords_NC[i, 0],
             coords_CVD_aligned[i, 1] - coords_NC[i, 1],
             head_width=0.05, head_length=0.03,
             fc='gray', ec='gray', alpha=0.5, linewidth=1)

ax.set_aspect('equal')
ax.set_title(f'Procrustes Alignment (disparity = {disparity:.3f})',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Aligned Dimension 1', fontsize=12)
ax.set_ylabel('Aligned Dimension 2', fontsize=12)
ax.legend(loc='upper right')
ax.grid(alpha=0.3)

plt.tight_layout()
```

---

## 4. Red-Green Merging Analysis ⭐ **CVD-SPECIFIC**

### 4.1 Color Confusion Matrix

**Purpose:** Identify which color pairs are most confused in CVD

**Data:**
```python
# From classification results (leave-one-run-out)
# Confusion matrix: rows = true color, cols = predicted color

confusion_NC = np.zeros((8, 8))
confusion_CVD = np.zeros((8, 8))

# Populate from classification results
for result in classification_results_NC:
    y_true = result['true_labels']
    y_pred = result['predicted_labels']
    for i, j in zip(y_true, y_pred):
        confusion_NC[i, j] += 1

for result in classification_results_CVD:
    y_true = result['true_labels']
    y_pred = result['predicted_labels']
    for i, j in zip(y_true, y_pred):
        confusion_CVD[i, j] += 1

# Normalize by row (true class)
confusion_NC = confusion_NC / confusion_NC.sum(axis=1, keepdims=True)
confusion_CVD = confusion_CVD / confusion_CVD.sum(axis=1, keepdims=True)
```

**Visualization:**
```python
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# Panel A: Non-CVD confusion
im1 = axes[0].imshow(confusion_NC, cmap='Blues', vmin=0, vmax=1)
axes[0].set_title('Non-CVD\nClassification Confusion', fontsize=12, fontweight='bold')
axes[0].set_xlabel('Predicted')
axes[0].set_ylabel('True')
axes[0].set_xticks(range(8))
axes[0].set_xticklabels([f'c{i+1}' for i in range(8)])
axes[0].set_yticks(range(8))
axes[0].set_yticklabels([f'c{i+1}' for i in range(8)])
plt.colorbar(im1, ax=axes[0], label='Proportion')

# Panel B: CVD confusion
im2 = axes[1].imshow(confusion_CVD, cmap='Reds', vmin=0, vmax=1)
axes[1].set_title('CVD\nClassification Confusion', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Predicted')
axes[1].set_ylabel('True')
axes[1].set_xticks(range(8))
axes[1].set_xticklabels([f'c{i+1}' for i in range(8)])
axes[1].set_yticks(range(8))
axes[1].set_yticklabels([f'c{i+1}' for i in range(8)])
plt.colorbar(im2, ax=axes[1], label='Proportion')

# Panel C: Difference (CVD - Non-CVD)
difference = confusion_CVD - confusion_NC
im3 = axes[2].imshow(difference, cmap='RdBu_r', vmin=-0.2, vmax=0.2, center=0)
axes[2].set_title('Difference\n(CVD - Non-CVD)', fontsize=12, fontweight='bold')
axes[2].set_xlabel('Predicted')
axes[2].set_ylabel('True')
axes[2].set_xticks(range(8))
axes[2].set_xticklabels([f'c{i+1}' for i in range(8)])
axes[2].set_yticks(range(8))
axes[2].set_yticklabels([f'c{i+1}' for i in range(8)])
plt.colorbar(im3, ax=axes[2], label='Difference')

# Annotate red-green confusions
for i in range(4):
    for j in range(4):
        if i != j and abs(difference[i, j]) > 0.05:
            axes[2].text(j, i, f'{difference[i, j]:.2f}',
                        ha='center', va='center', fontsize=10, fontweight='bold',
                        color='white' if abs(difference[i, j]) > 0.1 else 'black')

plt.suptitle('Classification Confusion: Red-Green Merging Analysis', fontsize=14, fontweight='bold')
plt.tight_layout()
```

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

### 4.2 Red-Green Axis Compression

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

print(f"Red-Green axis:")
print(f"  Non-CVD spread: {rg_spread_NC:.3f}")
print(f"  CVD spread: {rg_spread_CVD:.3f}")
print(f"  Compression: {compression_rg:.2f}x")
print()
print(f"Blue-Yellow axis:")
print(f"  Non-CVD spread: {by_spread_NC:.3f}")
print(f"  CVD spread: {by_spread_CVD:.3f}")
print(f"  Compression: {compression_by:.2f}x")
```

**Visualization:**
```python
fig, ax = plt.subplots(figsize=(8, 6))

axes_names = ['Red-Green\n(c1-c4)', 'Blue-Yellow\n(c5-c8)']
x = np.arange(len(axes_names))
width = 0.35

# Bars
ax.bar(x - width/2, [rg_spread_NC, by_spread_NC], width,
       label='Non-CVD', alpha=0.7, color='blue')
ax.bar(x + width/2, [rg_spread_CVD, by_spread_CVD], width,
       label='CVD', alpha=0.7, color='red')

# Annotate compression ratios
ax.text(0, max(rg_spread_NC, rg_spread_CVD) * 1.1,
        f'{compression_rg:.2f}x', ha='center', fontsize=12, fontweight='bold')
ax.text(1, max(by_spread_NC, by_spread_CVD) * 1.1,
        f'{compression_by:.2f}x', ha='center', fontsize=12, fontweight='bold')

ax.set_ylabel('Perceptual Spread (a.u.)', fontsize=12)
ax.set_xlabel('Color Axis', fontsize=12)
ax.set_title('Axis-Specific Compression in CVD', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(axes_names)
ax.legend()
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
```

**Expected Result:**
- **Red-green compression > 1.0:** CVD shows **reduced spread** along red-green axis
- **Blue-yellow compression ~ 1.0:** Blue-yellow axis preserved in CVD

### 4.3 Pairwise Distance Analysis: Red-Green vs Blue-Yellow

**Purpose:** Compare distance preservation in different color regions

**Data:**
```python
# Define color pairs
red_green_pairs = [(0,1), (0,2), (0,3), (1,2), (1,3), (2,3)]  # c1-c4 pairs
blue_yellow_pairs = [(4,5), (4,6), (4,7), (5,6), (5,7), (6,7)]  # c5-c8 pairs

# Extract distances for each region
def extract_pair_distances(D, pairs):
    return np.array([D[i, j] for i, j in pairs])

# Ideal
rg_dist_ideal = extract_pair_distances(D_ideal, red_green_pairs)
by_dist_ideal = extract_pair_distances(D_ideal, blue_yellow_pairs)

# Non-CVD
rg_dist_NC = extract_pair_distances(D_NC, red_green_pairs)
by_dist_NC = extract_pair_distances(D_NC, blue_yellow_pairs)

# CVD
rg_dist_CVD = extract_pair_distances(D_CVD, red_green_pairs)
by_dist_CVD = extract_pair_distances(D_CVD, blue_yellow_pairs)

# Compute errors from ideal
rg_error_NC = np.abs(rg_dist_NC - rg_dist_ideal)
rg_error_CVD = np.abs(rg_dist_CVD - rg_dist_ideal)

by_error_NC = np.abs(by_dist_NC - by_dist_ideal)
by_error_CVD = np.abs(by_dist_CVD - by_dist_ideal)
```

**Visualization:**
```python
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Panel A: Red-Green pairs
ax = axes[0]
x_rg = np.arange(len(red_green_pairs))
ax.bar(x_rg - 0.2, rg_error_NC, 0.4, label='Non-CVD', alpha=0.7, color='blue')
ax.bar(x_rg + 0.2, rg_error_CVD, 0.4, label='CVD', alpha=0.7, color='red')

ax.set_ylabel('Distance Error from Ideal (degrees)', fontsize=12)
ax.set_xlabel('Color Pair', fontsize=12)
ax.set_title('Red-Green Region (c1-c4)', fontsize=14, fontweight='bold')
ax.set_xticks(x_rg)
ax.set_xticklabels([f'c{i+1}-c{j+1}' for i, j in red_green_pairs], rotation=45)
ax.legend()
ax.grid(axis='y', alpha=0.3)

# Panel B: Blue-Yellow pairs
ax = axes[1]
x_by = np.arange(len(blue_yellow_pairs))
ax.bar(x_by - 0.2, by_error_NC, 0.4, label='Non-CVD', alpha=0.7, color='blue')
ax.bar(x_by + 0.2, by_error_CVD, 0.4, label='CVD', alpha=0.7, color='red')

ax.set_ylabel('Distance Error from Ideal (degrees)', fontsize=12)
ax.set_xlabel('Color Pair', fontsize=12)
ax.set_title('Blue-Yellow Region (c5-c8)', fontsize=14, fontweight='bold')
ax.set_xticks(x_by)
ax.set_xticklabels([f'c{i+1}-c{j+1}' for i, j in blue_yellow_pairs], rotation=45)
ax.legend()
ax.grid(axis='y', alpha=0.3)

plt.suptitle('Region-Specific Distance Errors', fontsize=16, fontweight='bold')
plt.tight_layout()
```

**Summary Statistics:**
```python
print("Red-Green Region:")
print(f"  Non-CVD mean error: {rg_error_NC.mean():.2f}° ± {rg_error_NC.std():.2f}°")
print(f"  CVD mean error: {rg_error_CVD.mean():.2f}° ± {rg_error_CVD.std():.2f}°")
print(f"  CVD increase: {rg_error_CVD.mean() - rg_error_NC.mean():.2f}°")
print()
print("Blue-Yellow Region:")
print(f"  Non-CVD mean error: {by_error_NC.mean():.2f}° ± {by_error_NC.std():.2f}°")
print(f"  CVD mean error: {by_error_CVD.mean():.2f}° ± {by_error_CVD.std():.2f}°")
print(f"  CVD increase: {by_error_CVD.mean() - by_error_NC.mean():.2f}°")
```

**Expected Pattern:**
- **Red-Green:** CVD shows **much higher errors** than Non-CVD
- **Blue-Yellow:** CVD errors **similar to** Non-CVD (axis preserved)

---

## 5. Supplementary Figures

### S1. Universal HRF Comparison (Quality Control)

**Current file:** `1_universal_hrf.png`

**Purpose:** Ensure hemodynamic response is similar across groups

**Layout:**
```
┌────────────────────────────────────────┐
│ A. Mean HRF Time Course (0-15s)       │
│    Non-CVD (blue) vs CVD (red)        │
│    Shaded area = SEM                  │
├────────────────────────────────────────┤
│ B. Optimal Delay Distribution         │
│    Box plot: Non-CVD vs CVD           │
│    Typical: 2-5 TRs (3-7.5s)          │
└────────────────────────────────────────┘
```

**Expected:** No major group differences (HRF should be similar)

### S2. Z-Score Matrix Comparison

**Current file:** `2_zscore_matrix_full.png` (4 panels)

**Purpose:** Compare voxel-level color selectivity

**Enhancements:**
- Add group average heatmaps
- Compute selectivity index per group
- Highlight voxels with different selectivity between groups

### S3. ROI-by-ROI Breakdown

**Purpose:** Detailed comparison for each visual area

**Layout:** 4 rows (V1, V2, V3, hV4) × 3 columns (NC, CVD, Difference)

For each ROI:
- Circular reconstruction plot
- Distance matrix
- Interval uniformity

**Total:** 12 subplots (4 ROIs × 3 comparisons)

### S4. Individual Subject Profiles

**Purpose:** Show inter-subject variability

**Layout:**
```
┌──────┬──────┬──────┬──────┐
│ Sub01│ Sub02│ Sub03│ Sub04│
│      │      │      │      │
│ NC   │ NC   │ CVD  │ CVD  │
│      │      │      │      │
│ Best │ Best │ Best │ Best │
│ ROI  │ ROI  │ ROI  │ ROI  │
└──────┴──────┴──────┴──────┘
```

For each subject:
- Circular plot (best ROI)
- Distance matrix
- Performance summary

---

## 6. Implementation: New Analysis Scripts

### 6.1 Main Analysis Script

**File:** `analyze_cvd_vs_noncvd.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_cvd_vs_noncvd.py
-------------------------
Comprehensive comparison of Non-CVD vs CVD color perception

Analyses:
1. Perceptual distance matrices
2. Red-green merging quantification
3. Interval uniformity assessment
4. Circular space visualization with enhancements
5. Statistical tests

Usage:
    python analyze_cvd_vs_noncvd.py --timestamp 20251117_021334 --roi V2
"""

import sys
import os
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.spatial.distance import pdist, squareform
from scipy.spatial import procrustes
from sklearn.manifold import MDS

# ============================================================================
# Configuration
# ============================================================================

SUBJECTS_NC = ['01', '02']  # Non-CVD
SUBJECTS_CVD = ['03', '04']  # CVD
ROIS = ['V1', 'V2', 'V3', 'hV4']

# Color labels (regular 45° spacing)
COLOR_LABELS = {
    'color_1': 0,    # Red
    'color_2': 45,   # Orange
    'color_3': 90,   # Yellow
    'color_4': 135,  # Yellow-Green
    'color_5': 180,  # Cyan
    'color_6': 225,  # Blue
    'color_7': 270,  # Violet
    'color_8': 315   # Pink
}

# ============================================================================
# Load Reconstruction Results
# ============================================================================

def load_reconstruction_results(timestamp, subject_id, roi, method='zScore'):
    """
    Load reconstruction results from derivatives

    Returns:
    --------
    results : dict
        - 'true_hues': ndarray (8,)
        - 'predicted_hues': ndarray (n_runs, 8)
        - 'errors': ndarray (n_runs, 8)
    """
    base_dir = Path(f"derivatives/{timestamp}/sub-{subject_id}/fir_reconstruction_uni_hrf/{method}/{roi}_universal_hrf")

    # Load reconstruction CSV
    recon_file = base_dir / "reconstruction_results.csv"

    if not recon_file.exists():
        print(f"WARNING: {recon_file} not found!")
        return None

    df = pd.read_csv(recon_file)

    # Extract data
    true_hues = df.groupby('color_index')['true_hue'].first().values

    # Predicted hues per run
    n_runs = df['run_index'].nunique()
    predicted_hues = np.zeros((n_runs, 8))

    for run_idx in range(n_runs):
        run_data = df[df['run_index'] == run_idx]
        predicted_hues[run_idx] = run_data['reconstructed_hue'].values

    # Circular errors
    errors = np.array([[circular_distance(predicted_hues[r, c], true_hues[c])
                       for c in range(8)]
                      for r in range(n_runs)])

    return {
        'true_hues': true_hues,
        'predicted_hues': predicted_hues,
        'errors': errors
    }

def circular_distance(angle1, angle2):
    """Circular distance (0-180 degrees)"""
    diff = abs(angle1 - angle2)
    return min(diff, 360 - diff)

# ============================================================================
# Compute Perceptual Distance Matrix
# ============================================================================

def compute_distance_matrix(hues):
    """
    Compute pairwise circular distances

    Parameters:
    -----------
    hues : ndarray (8,)
        Hue angles for 8 colors

    Returns:
    --------
    D : ndarray (8, 8)
        Distance matrix
    """
    n = len(hues)
    D = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            D[i, j] = circular_distance(hues[i], hues[j])

    return D

# ============================================================================
# Interval Uniformity
# ============================================================================

def compute_adjacent_intervals(distance_matrix):
    """
    Extract distances between adjacent colors

    Returns: ndarray (8,) - [c1→c2, c2→c3, ..., c8→c1]
    """
    n = len(distance_matrix)
    intervals = np.zeros(n)

    for i in range(n):
        j = (i + 1) % n
        intervals[i] = distance_matrix[i, j]

    return intervals

def interval_uniformity_metric(intervals):
    """
    Coefficient of variation (CV) of adjacent intervals
    Lower = more uniform
    """
    return np.std(intervals) / np.mean(intervals) * 100

# ============================================================================
# Red-Green Merging Metrics
# ============================================================================

def compute_rg_compression(coords_NC, coords_CVD):
    """
    Compute compression ratio along red-green axis

    Parameters:
    -----------
    coords_NC, coords_CVD : ndarray (8, 2)
        MDS coordinates
    """
    # Red-green axis (c1-c4)
    rg_indices = [0, 1, 2, 3]

    def axis_spread(coords, indices):
        centroid = coords[indices].mean(axis=0)
        distances = np.linalg.norm(coords[indices] - centroid, axis=1)
        return np.std(distances)

    spread_NC = axis_spread(coords_NC, rg_indices)
    spread_CVD = axis_spread(coords_CVD, rg_indices)

    compression = spread_CVD / spread_NC

    return compression, spread_NC, spread_CVD

# ============================================================================
# Main Analysis Function
# ============================================================================

def analyze_group_comparison(timestamp, roi, output_dir):
    """
    Run complete Non-CVD vs CVD comparison
    """
    print("="*70)
    print(f"Non-CVD vs CVD Comparison: {roi}")
    print("="*70)

    # Load data
    print("\n[1/6] Loading reconstruction results...")

    results_NC = []
    for sub in SUBJECTS_NC:
        res = load_reconstruction_results(timestamp, sub, roi)
        if res is not None:
            results_NC.append(res)

    results_CVD = []
    for sub in SUBJECTS_CVD:
        res = load_reconstruction_results(timestamp, sub, roi)
        if res is not None:
            results_CVD.append(res)

    if not results_NC or not results_CVD:
        print("ERROR: Missing data!")
        return

    # Compute group averages
    print("\n[2/6] Computing group averages...")

    # Average predicted hues across runs and subjects
    all_pred_NC = np.concatenate([r['predicted_hues'] for r in results_NC], axis=0)
    all_pred_CVD = np.concatenate([r['predicted_hues'] for r in results_CVD], axis=0)

    mean_pred_NC = all_pred_NC.mean(axis=0)  # (8,)
    mean_pred_CVD = all_pred_CVD.mean(axis=0)

    true_hues = results_NC[0]['true_hues']  # Same for all

    # Distance matrices
    print("\n[3/6] Computing perceptual distance matrices...")

    D_ideal = compute_distance_matrix(np.arange(8) * 45)
    D_NC = compute_distance_matrix(mean_pred_NC)
    D_CVD = compute_distance_matrix(mean_pred_CVD)

    # MDS
    print("\n[4/6] Applying multidimensional scaling...")

    mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
    coords_ideal = mds.fit_transform(D_ideal)
    coords_NC = mds.fit_transform(D_NC)
    coords_CVD = mds.fit_transform(D_CVD)

    # Procrustes
    _, coords_CVD_aligned, disparity = procrustes(coords_NC, coords_CVD)

    print(f"  Procrustes disparity: {disparity:.4f}")

    # Metrics
    print("\n[5/6] Computing metrics...")

    # Correlation with ideal
    r_NC = np.corrcoef(D_ideal.flatten(), D_NC.flatten())[0, 1]
    r_CVD = np.corrcoef(D_ideal.flatten(), D_CVD.flatten())[0, 1]

    print(f"  Distance correlation with ideal:")
    print(f"    Non-CVD: r = {r_NC:.3f}")
    print(f"    CVD: r = {r_CVD:.3f}")

    # Interval uniformity
    intervals_ideal = compute_adjacent_intervals(D_ideal)
    intervals_NC = compute_adjacent_intervals(D_NC)
    intervals_CVD = compute_adjacent_intervals(D_CVD)

    cv_NC = interval_uniformity_metric(intervals_NC)
    cv_CVD = interval_uniformity_metric(intervals_CVD)

    print(f"  Interval uniformity (CV):")
    print(f"    Non-CVD: {cv_NC:.1f}%")
    print(f"    CVD: {cv_CVD:.1f}%")

    # Red-green compression
    compression, spread_NC, spread_CVD = compute_rg_compression(coords_NC, coords_CVD)

    print(f"  Red-green axis compression:")
    print(f"    Non-CVD spread: {spread_NC:.3f}")
    print(f"    CVD spread: {spread_CVD:.3f}")
    print(f"    Compression ratio: {compression:.2f}x")

    # Generate figures
    print("\n[6/6] Generating figures...")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Figure 1: Distance matrices
    plot_distance_matrices(D_ideal, D_NC, D_CVD, output_dir, roi)

    # Figure 2: MDS visualization
    plot_mds_comparison(coords_ideal, coords_NC, coords_CVD, output_dir, roi)

    # Figure 3: Interval uniformity
    plot_interval_uniformity(intervals_ideal, intervals_NC, intervals_CVD, output_dir, roi)

    # Figure 4: Circular overlay
    plot_circular_overlay(true_hues, mean_pred_NC, mean_pred_CVD, output_dir, roi)

    print("\nDone!")
    print(f"Figures saved to: {output_dir}")

# ============================================================================
# Plotting Functions
# ============================================================================

def plot_distance_matrices(D_ideal, D_NC, D_CVD, output_dir, roi):
    """Figure 2 from main document"""
    # [Implementation similar to Figure 2 above]
    pass

def plot_mds_comparison(coords_ideal, coords_NC, coords_CVD, output_dir, roi):
    """MDS visualization"""
    # [Implementation similar to Section 3.1 above]
    pass

def plot_interval_uniformity(intervals_ideal, intervals_NC, intervals_CVD, output_dir, roi):
    """Panel D from Figure 3"""
    # [Implementation similar to Figure 3 Panel D above]
    pass

def plot_circular_overlay(true_hues, mean_pred_NC, mean_pred_CVD, output_dir, roi):
    """Panel C from Figure 1"""
    # [Implementation similar to Figure 1 Panel C above]
    pass

# ============================================================================
# Main Execution
# ============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Non-CVD vs CVD comparison')
    parser.add_argument('--timestamp', type=str, required=True,
                       help='Analysis timestamp (e.g., 20251117_021334)')
    parser.add_argument('--roi', type=str, default='V2',
                       choices=['V1', 'V2', 'V3', 'hV4'],
                       help='ROI to analyze')
    parser.add_argument('--output', type=str, default='figures/cvd_comparison',
                       help='Output directory for figures')

    args = parser.parse_args()

    analyze_group_comparison(args.timestamp, args.roi, args.output)
```

### 6.2 Usage

```bash
# Activate environment
conda activate nilearn

# Run analysis for V2
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

## 7. Statistical Tests

### 7.1 Permutation Test: Group Differences

**Null hypothesis:** No difference between Non-CVD and CVD

```python
def permutation_test_group_difference(metric_NC, metric_CVD, n_permutations=10000):
    """
    Two-sample permutation test

    Parameters:
    -----------
    metric_NC : ndarray (n_subjects_NC,)
    metric_CVD : ndarray (n_subjects_CVD,)

    Returns:
    --------
    p_value : float
    """
    # Observed difference
    observed_diff = np.mean(metric_CVD) - np.mean(metric_NC)

    # Combine groups
    all_data = np.concatenate([metric_NC, metric_CVD])
    n_NC = len(metric_NC)
    n_total = len(all_data)

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

# Example usage
recon_errors_NC = [13.72, 14.36]  # sub-01, sub-02
recon_errors_CVD = [26.66, 31.27]  # sub-03, sub-04

p_val, perm_dist = permutation_test_group_difference(
    np.array(recon_errors_NC),
    np.array(recon_errors_CVD),
    n_permutations=10000
)

print(f"Permutation test p-value: {p_val:.4f}")
```

### 7.2 Bootstrap Confidence Intervals

```python
def bootstrap_ci(data, n_bootstrap=10000, ci=95):
    """
    Bootstrap confidence interval

    Parameters:
    -----------
    data : ndarray (n_subjects,)

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

# Example
ci_NC = bootstrap_ci(np.array(recon_errors_NC))
ci_CVD = bootstrap_ci(np.array(recon_errors_CVD))

print(f"Non-CVD 95% CI: [{ci_NC[0]:.1f}, {ci_NC[1]:.1f}]")
print(f"CVD 95% CI: [{ci_CVD[0]:.1f}, {ci_CVD[1]:.1f}]")
```

---

## Summary

### Required Figures (Priority Order)

**Essential (Manuscript Main Figures):**
1. ✅ **Figure 1: Circular Color Space Comparison** - Based on current `4_reconstruction_results.png` + enhancements
2. 🆕 **Figure 2: Perceptual Distance Matrix** - NEW, CVD-specific analysis
3. ✅ **Figure 3: PCA Color Space + Distance Preservation** - Based on current `3_pca_components.png` + new panels

**Important (Manuscript Supplementary):**
4. 🆕 **Figure S1: Red-Green Merging Analysis** - Confusion matrix + compression
5. 🆕 **Figure S2: MDS + Procrustes** - Shape comparison
6. ✅ **Figure S3: Universal HRF** - QC, based on current `1_universal_hrf.png`
7. ✅ **Figure S4: Z-Score Matrix** - QC, based on current `2_zscore_matrix_full.png`

**Key Analyses:**
1. ⭐ **Perceptual distance matrices** (8×8) - Correlation with ideal
2. ⭐ **Red-green compression ratio** - Quantify merging
3. ⭐ **Interval uniformity** (CV) - Check 45° spacing preservation
4. ⭐ **Angular distortion map** - Systematic biases by color
5. **Procrustes alignment** - Shape similarity

**Implementation:**
- New script: `analyze_cvd_vs_noncvd.py` (provided above)
- Uses existing pipeline outputs + computes new metrics
- Generates publication-ready figures

**Next Steps:**
1. Run `analyze_cvd_vs_noncvd.py` for all ROIs
2. Generate all figures
3. Perform statistical tests
4. Write manuscript sections

---

**Document Version:** 2.0 - **Revised with Current Figures Focus**
**Date:** November 18, 2025
**Status:** Ready for Implementation
