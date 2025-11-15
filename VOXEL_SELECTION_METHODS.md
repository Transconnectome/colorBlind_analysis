# Voxel Selection Methods for fMRI Color Encoding

## Problem with Current Approach

**Current method (WRONG for selectivity):**
```python
mean_abs_z_per_voxel = np.mean(np.abs(all_betas), axis=(0, 1))
selected = mean_abs_z_per_voxel > 2.3
```

This selects voxels that respond **uniformly to ALL colors** → Non-selective voxels!

---

## Standard Approaches in Literature

### 1. **MAX Criterion (RECOMMENDED)** ⭐
**Most common for selectivity studies**

```python
# Select voxels with strong response to ANY color
max_abs_z_per_voxel = np.max(np.abs(all_betas), axis=(0, 1))
selected = max_abs_z_per_voxel > 2.3  # p < 0.01
```

**Rationale:**
- Color-selective voxels respond strongly to SOME colors, not all
- This identifies voxels with at least one strong color response
- Used in most selectivity studies (e.g., face-selective, place-selective regions)

**Expected selection:** 30-60% of anatomical ROI voxels

---

### 2. **Percentile-Based Selection**
**Most robust, avoids arbitrary thresholds**

```python
# Select top N% of voxels based on max |z|
max_abs_z_per_voxel = np.max(np.abs(all_betas), axis=(0, 1))
percentile_threshold = np.percentile(max_abs_z_per_voxel, 50)  # Top 50%
selected = max_abs_z_per_voxel > percentile_threshold
```

**Advantages:**
- Guarantees sufficient voxels (no 0-voxel problem)
- Adapts to each ROI's response characteristics
- Common percentiles: 25% (conservative), 50% (moderate), 75% (liberal)

---

### 3. **Variance-Based Selection**
**Explicitly selects for color-selective voxels**

```python
# Select voxels with high variance across colors (= selective)
# Average across runs first, then compute variance across colors
z_per_color = np.mean(all_betas, axis=0)  # (n_colors, n_voxels)
variance_across_colors = np.var(z_per_color, axis=0)  # (n_voxels,)
selected = variance_across_colors > np.percentile(variance_across_colors, 50)
```

**Rationale:**
- High variance across colors = responds differently to different colors = selective
- Low variance = responds uniformly = not selective
- Directly measures selectivity

---

### 4. **F-Test (ANOVA)**
**Statistical test for differential responses**

```python
from scipy import stats

# Test if voxel responds differently to different colors
f_stats = []
for voxel_idx in range(n_voxels):
    # Get data for this voxel: (n_runs, n_colors)
    voxel_data = all_betas[:, :, voxel_idx]

    # Flatten to (n_runs × n_colors,) and create color labels
    data_flat = voxel_data.ravel()
    color_labels = np.tile(np.arange(N_COLORS), N_RUNS)

    # One-way ANOVA: does this voxel respond differently to colors?
    f_stat, p_val = stats.f_oneway(*[voxel_data[:, c] for c in range(N_COLORS)])
    f_stats.append(f_stat)

f_stats = np.array(f_stats)
selected = f_stats > stats.f.ppf(0.99, N_COLORS-1, N_RUNS*N_COLORS - N_COLORS)
```

**Rationale:**
- Tests null hypothesis: "voxel responds equally to all colors"
- Rejecting null = voxel is color-selective
- Most statistically rigorous

---

### 5. **Liberalized Threshold**
**If you want to keep mean criterion but make it less restrictive**

```python
# Option A: Lower threshold (p < 0.05 instead of p < 0.01)
mean_abs_z_per_voxel = np.mean(np.abs(all_betas), axis=(0, 1))
selected = mean_abs_z_per_voxel > 1.96  # p < 0.05 (was 2.3 for p < 0.01)

# Option B: Use "any color" instead of "all colors average"
# Select if |z| > 2.3 for at least 1 color
any_significant = np.any(np.abs(all_betas) > 2.3, axis=(0, 1))
```

**Note:** Still not ideal for selectivity, but better than current approach

---

## What Brouwer & Heeger (2009) Actually Did

From the paper (Methods section):

> "We selected voxels that were significantly more responsive to the color stimuli
> than to the gray-scale stimuli (p < 0.01, uncorrected)."

**They used a functional localizer:**
- Color stimuli > Gray stimuli (t-test)
- NOT "responds to all colors" criterion
- NOT "mean |z| across all colors" criterion

**Modern equivalent:**
```python
# Compare color conditions vs baseline (or vs gray)
# Use max |z| across colors as the functional localizer
max_z_per_voxel = np.max(np.abs(all_betas), axis=(0, 1))
selected = max_z_per_voxel > 2.3
```

---

## Recommended Approach for Your Project

### Primary Recommendation: **MAX + Percentile Hybrid** ⭐⭐⭐

```python
# 1. Compute max |z| across colors per voxel
max_abs_z_per_voxel = np.max(np.abs(all_betas), axis=(0, 1))

# 2. Apply both criteria:
#    - Statistical significance (p < 0.01)
#    - Top 50% within anatomical ROI
threshold_statistical = 2.3  # p < 0.01
threshold_percentile = np.percentile(max_abs_z_per_voxel, 50)
threshold = max(threshold_statistical, threshold_percentile)

selected_voxels_mask = max_abs_z_per_voxel > threshold

# This ensures:
# - All selected voxels are statistically significant
# - Sufficient voxels for analysis (never 0-1 voxels)
# - Adaptive to each ROI's response characteristics
```

**Why this is best:**
1. Identifies color-responsive voxels (max criterion)
2. Ensures statistical significance (p < 0.01 threshold)
3. Guarantees sufficient voxels (percentile)
4. Adapts to ROI characteristics

---

## Expected Results

| Method | Expected Selection | Pros | Cons |
|--------|-------------------|------|------|
| Mean \|z\| > 2.3 (CURRENT) | 0-5% ❌ | - | Selects non-selective voxels |
| Max \|z\| > 2.3 | 30-60% ✓ | Identifies responsive voxels | May select too few in weak ROIs |
| Percentile (top 50%) | 50% ✓ | Guarantees voxels | No statistical threshold |
| Max + Percentile Hybrid | 30-50% ✓✓ | Best of both | Slightly complex |
| Variance-based | 40-60% ✓ | Explicit selectivity | Sensitive to noise |
| F-test | 20-40% ✓ | Most rigorous | Conservative |

---

## Implementation Code

See `visualize_Edits/voxel_selection_comparison.py` for comparison of all methods.

---

## References

- Brouwer & Heeger (2009): Used color > gray functional localizer
- Haxby et al. (2001): Used within-category variance selection
- Naselaris et al. (2009): Used max response criterion
- Kay et al. (2008): Used percentile-based selection (top 500 voxels)
- Kriegeskorte et al. (2008): Used F-test for category selectivity
