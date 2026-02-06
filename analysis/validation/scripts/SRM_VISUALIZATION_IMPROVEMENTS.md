# SRM Between-Subject Visualization Improvements

## Overview

Three major improvements have been made to the SRM between-subject analysis visualization based on user feedback:

1. **Fixed title/text overlap** in disparity plots
2. **Added CVD-to-CVD internal consistency analysis**
3. **Created color representational space visualization** per subject

---

## 1. Fixed Title/Text Overlap

### Problem
The disparity comparison plot had overlapping title and axis labels, making it difficult to read.

### Solution
Added `pad=20` parameter to `ax.set_title()` to increase spacing between title and plot area.

```python
ax.set_title(title_text, fontsize=14, fontweight='bold', pad=20)
```

### File Modified
- `evaluate_srm_between_subject.py` (line 444)

---

## 2. CVD-to-CVD Internal Consistency Analysis

### Motivation
Previously, we compared:
- HC-to-HC disparity (internal consistency)
- CVD-to-HC disparity (group difference)

But we didn't know if CVD subjects are internally consistent with each other or if they also show high variability within the CVD group.

### Implementation

**Added CVD-to-CVD pairwise disparity calculation:**

```python
# CVD-to-CVD pairwise disparities (internal consistency)
cvd_cvd_disparities = []
for i, subj_i in enumerate(cvd_subjects_list):
    for j, subj_j in enumerate(cvd_subjects_list):
        if i < j:  # Unique pairs only
            pattern_i = np.mean(all_aligned[subj_i], axis=0)
            pattern_j = np.mean(all_aligned[subj_j], axis=0)
            disparity = compute_procrustes_disparity(pattern_i, pattern_j)
            cvd_cvd_disparities.append(disparity)
```

**Updated boxplot to show 3 groups:**
- HC-to-HC Reference (blue)
- CVD-to-HC Reference (salmon)
- **CVD-to-CVD Pairwise (orchid)** ← NEW!

**Added statistical test:**
```python
# Compare CVD-CVD vs CVD-HC to see if CVD is internally consistent
if len(cvd_cvd_disparities) > 1:
    t_stat_cvd, p_value_cvd = ttest_ind(cvd_cvd_disparities, cvd_disparities)
```

### Results Saved
Updated JSON output includes:

```json
{
  "disparities": {
    "cvd_to_cvd_pairwise": {
      "mean": 0.XX,
      "std": 0.XX,
      "values": [...],
      "n_pairs": 3
    },
    "statistical_test_cvd_cvd_vs_cvd_hc": {
      "t_statistic": X.XX,
      "p_value": 0.XXXX,
      "significant": true/false
    }
  }
}
```

### Interpretation Guide

**Scenario 1: CVD-CVD ≈ HC-HC < CVD-HC**
- CVD subjects are internally consistent
- But different from HC as a group
- Suggests systematic CVD-specific representation

**Scenario 2: CVD-CVD ≈ CVD-HC > HC-HC**
- CVD subjects are not internally consistent
- High variability within CVD group
- Suggests heterogeneous CVD representations

**Scenario 3: CVD-CVD < CVD-HC**
- CVD subjects are MORE consistent with each other than with HC
- Strong evidence for group-level CVD representation

### Files Modified
- `evaluate_srm_between_subject.py`:
  - Lines 282-290: CVD-CVD calculation
  - Lines 304-307: Statistical test
  - Lines 358-374: JSON results update
  - Lines 420-429: Boxplot update

---

## 3. Color Representational Space Visualization

### Motivation
From the user request:
> "RDM을 구했다는 것은 각 색 간의 representative space가 나타났다는 것일텐데, 이를 피험자 별로 시각화할 수 있나요?"

Since we compute RDMs (8×8 dissimilarity matrices), we can visualize the 8-color representational space in 2D using Multidimensional Scaling (MDS).

### New Script: `visualize_color_space_per_subject.py`

**Features:**

1. **Per-subject color space visualization**
   - Loads SRM-aligned amplitudes
   - Computes RDM for each subject (8 colors × 8 colors)
   - Projects to 2D using MDS
   - Shows all subjects in a grid layout

2. **HC vs CVD average comparison**
   - Averages coordinates across HC subjects
   - Averages coordinates across CVD subjects
   - Aligns CVD to HC using Procrustes for better visualization
   - Shows overlay with displacement arrows

3. **Color-coded markers**
   - Red, Orange, Yellow, Green, Cyan, Blue, Purple, Magenta
   - Numbers (1-8) shown on each marker
   - Legend panel included

### Usage

**Step 1: Run between-subject SRM analysis**
```bash
bash run_srm_between_subject_local_test.sh
```

This saves:
- `{ROI}_srm_between_subject_results.json`
- `{ROI}_aligned_amplitudes.npy` ← NEW! (for visualization)

**Step 2: Visualize color spaces**
```bash
bash run_color_space_visualization.sh results/srm_between_subject/test_local_TIMESTAMP
```

Or directly:
```bash
python visualize_color_space_per_subject.py \
    --roi V1 \
    --results-dir results/srm_between_subject/test_local_TIMESTAMP
```

### Output Files

1. **`{ROI}_color_space_all_subjects.png`**
   - Grid of all subjects (4 columns)
   - Each subplot shows one subject's color space
   - Legend panel showing color names
   - Title indicates HC vs CVD group membership

2. **`{ROI}_hc_vs_cvd_color_space_comparison.png`**
   - Three panels side-by-side:
     - HC average color space
     - CVD average color space (Procrustes-aligned to HC)
     - Overlay with displacement arrows
   - Shows how CVD representation differs from HC

### Interpretation Guide

**What to look for:**

1. **Color clustering**
   - Do similar hues (e.g., Red-Orange-Yellow) cluster together?
   - Expected in healthy color vision

2. **HC consistency**
   - Do HC subjects show similar color space structure?
   - Variability indicates individual differences

3. **CVD deviations**
   - Which colors show largest displacement from HC?
   - Are confusable colors closer together in CVD?
   - Example: Red-Green closer in CVD subjects

4. **CVD heterogeneity**
   - Do all CVD subjects show similar deviations?
   - Or does each CVD subject have unique distortions?

### Technical Details

**MDS Parameters:**
```python
mds = MDS(n_components=2, dissimilarity='precomputed', random_state=42)
coords_2d = mds.fit_transform(rdm)
```

**RDM Computation:**
```python
# Correlation distance = 1 - correlation
for i in range(n_colors):
    for j in range(n_colors):
        corr = np.corrcoef(amplitudes[i], amplitudes[j])[0, 1]
        rdm[i, j] = 1 - corr
```

### Files Created
- `visualize_color_space_per_subject.py`: Main visualization script
- `run_color_space_visualization.sh`: Wrapper script for batch processing

### Files Modified
- `evaluate_srm_between_subject.py`:
  - Line 418-420: Save aligned amplitudes as .npy file
  - Required for visualization script to load data

---

## Quick Reference

### Running the Complete Analysis

```bash
# 1. Run between-subject SRM (creates disparity plot + saves aligned data)
bash run_srm_between_subject_local_test.sh

# Output directory will be shown, e.g.:
# results/srm_between_subject/test_local_20260206_143052

# 2. Visualize color spaces (creates MDS plots)
bash run_color_space_visualization.sh results/srm_between_subject/test_local_20260206_143052

# 3. View all results
open results/srm_between_subject/test_local_20260206_143052/*.png
```

### Expected Output Files

For each ROI (e.g., V1):

1. **`V1_srm_between_subject_results.json`**
   - Disparities: HC-HC, CVD-HC, CVD-CVD
   - RDM similarities
   - Statistical tests
   - Effect sizes

2. **`V1_aligned_amplitudes.npy`**
   - Dictionary of aligned amplitudes per subject
   - Used by visualization script

3. **`V1_hc_cvd_disparity_comparison.png`**
   - Boxplot with 3 groups (now includes CVD-CVD)

4. **`V1_rdm_similarity_matrix.png`**
   - Heatmap of inter-subject RDM correlations

5. **`V1_color_space_all_subjects.png`**
   - Grid of per-subject color spaces (MDS 2D)

6. **`V1_hc_vs_cvd_color_space_comparison.png`**
   - HC avg vs CVD avg with overlay

---

## Dependencies

All three improvements work with existing dependencies:
- `numpy`, `scipy`, `matplotlib`, `seaborn` (already required)
- `scikit-learn` (for MDS) - should already be in `srm` environment

Test:
```bash
conda activate srm
python -c "from sklearn.manifold import MDS; print('✓ scikit-learn available')"
```

---

## Summary of Changes

| Improvement | Files Modified | Files Created | Lines Changed |
|-------------|---------------|---------------|---------------|
| 1. Fix title overlap | `evaluate_srm_between_subject.py` | - | ~1 line |
| 2. CVD-CVD analysis | `evaluate_srm_between_subject.py` | - | ~50 lines |
| 3. Color space viz | `evaluate_srm_between_subject.py` | 2 new scripts | ~350 lines |

**Total:** 1 file modified, 2 files created, ~400 lines added

---

## Next Steps

1. **Test locally** with 2 ROIs (V1, V2)
   ```bash
   bash run_srm_between_subject_local_test.sh
   bash run_color_space_visualization.sh <OUTPUT_DIR>
   ```

2. **Run all ROIs** if tests look good
   ```bash
   bash run_srm_between_subject_local_all.sh
   bash run_color_space_visualization.sh <OUTPUT_DIR>
   ```

3. **Analyze results**
   - Check if CVD-CVD disparity is high (heterogeneous) or low (consistent)
   - Identify which colors show largest HC-CVD displacement in MDS plots
   - Compare color space structure across visual hierarchy (V1 → V2 → V3 → hV4)

4. **Server deployment** (if needed)
   - Upload modified scripts to server
   - Run with larger datasets or additional subjects
   - May require more memory for MDS with larger feature spaces

---

## Questions or Issues?

- **Missing aligned_amplitudes.npy**: Re-run `evaluate_srm_between_subject.py` with updated version
- **MDS plot looks wrong**: Check if RDMs are symmetric and non-negative
- **Memory issues**: MDS can be memory-intensive; consider using fewer subjects for testing
- **Slow execution**: MDS convergence can take time; this is normal for complex RDMs

---

*Last updated: 2026-02-06*
*Author: Claude Code (based on user feedback)*
