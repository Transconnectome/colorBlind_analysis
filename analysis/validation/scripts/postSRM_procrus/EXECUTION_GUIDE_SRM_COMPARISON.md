# Execution Guide: SRM Comparison with Procrustes-PCA

## Overview

This guide explains how to compute the same geometric metrics for SRM results and directly compare them with Procrustes-PCA approach.

**Goal**: Quantitative comparison using identical metrics (ISC, deviation, circularity, reliability)

---

## Prerequisites

### 1. Complete Procrustes-PCA Pipeline

First, run the Procrustes-PCA pipeline:

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus

# Run full pipeline (or at least Steps 1-4)
./run_local_test.sh  # Local test
# OR
sbatch sbatch/run_full_pipeline_pca.sbatch  # Server production
```

**Required outputs**:
- `results/step4_metrics/{ROI}/geometric_metrics.json`
- `results/step4_metrics/{ROI}/hc_vs_cvd_statistics.json`

### 2. Locate SRM Results

Find your SRM results directory. Expected structure:

```
/path/to/srm/results/
├── V1/
│   ├── sub-01_aligned_patterns.npy   # (n_runs, 8, k_srm)
│   ├── sub-02_aligned_patterns.npy
│   └── ...
├── V2/
├── V3/
└── hV4/
```

**Supported filenames**:
- `sub-{ID}_aligned_patterns.npy`
- `sub-{ID}_srm_transformed.npy`
- `sub-{ID}_transformed.npy`

**Expected shape**: `(n_runs, n_colors, k_srm)` where:
- `n_runs` = 6 (or similar)
- `n_colors` = 8
- `k_srm` = SRM dimensionality (typically 3-8)

---

## Step-by-Step Execution

### Step 1: Compute SRM Geometric Metrics

For each ROI, compute the same metrics as Procrustes-PCA:

```bash
python compute_srm_metrics.py \
    --roi V1 \
    --srm-dir /path/to/srm/results \
    --output-dir results/srm_metrics
```

**What it does**:
1. Loads SRM-aligned patterns for all subjects
2. Averages runs into odd/even splits (same as Procrustes)
3. Computes correlation-based RDMs
4. Calculates geometric metrics:
   - ISC (Inter-Subject Correlation)
   - Deviation from HC norm
   - Circularity (MDS-based)
   - MDS stress
   - Split-half reliability
5. Performs HC vs CVD statistical tests

**Output**:
- `results/srm_metrics/{ROI}/geometric_metrics_srm.json` - Per-subject metrics
- `results/srm_metrics/{ROI}/hc_vs_cvd_statistics_srm.json` - Group comparison
- `results/srm_metrics/{ROI}/sub-*_rdm_srm.npy` - RDMs per subject
- `results/srm_metrics/{ROI}/rdm_hc_mean_srm.npy` - HC mean RDM

### Step 2: Compare Methods

Generate comparison plots and tables:

```bash
python compare_procrustes_vs_srm.py \
    --roi V1 \
    --procrustes-dir results/step4_metrics \
    --srm-dir results/srm_metrics \
    --output-dir results/comparison
```

**What it does**:
1. Loads metrics from both methods
2. Generates comparison visualizations:
   - Bar plot: HC vs CVD for each metric (side-by-side methods)
   - Scatter plot: Per-subject correlation between methods
   - Reliability comparison
3. Prints summary table with "winner" for each metric

**Output**:
- `results/comparison/{ROI}_method_comparison_barplot.png`
- `results/comparison/{ROI}_method_correlation_scatter.png`
- `results/comparison/{ROI}_reliability_comparison.png`

---

## Full Workflow Example

### Local Execution (V1 only)

```bash
cd postSRM_procrus

# 1. Compute Procrustes-PCA metrics (if not done)
./run_local_test.sh

# 2. Compute SRM metrics
python compute_srm_metrics.py \
    --roi V1 \
    --srm-dir /path/to/your/srm/results

# 3. Compare methods
python compare_procrustes_vs_srm.py --roi V1

# 4. View results
open results/comparison/V1_method_comparison_barplot.png
cat results/comparison/V1_summary.txt  # If generated
```

### Server Execution (All ROIs)

Create a batch script:

```bash
#!/bin/bash
# compare_all_rois.sh

ROIS=(V1 V2 V3 hV4)
SRM_DIR=/path/to/srm/results

for ROI in "${ROIS[@]}"; do
    echo "Processing $ROI..."

    # Compute SRM metrics
    python compute_srm_metrics.py \
        --roi $ROI \
        --srm-dir $SRM_DIR \
        --output-dir results/srm_metrics

    # Compare methods
    python compare_procrustes_vs_srm.py \
        --roi $ROI \
        --procrustes-dir results/step4_metrics \
        --srm-dir results/srm_metrics \
        --output-dir results/comparison
done

echo "✓ All ROIs processed"
```

Run:
```bash
chmod +x compare_all_rois.sh
./compare_all_rois.sh
```

---

## Interpreting Results

### Summary Table

The comparison script prints a summary table:

```
SUMMARY TABLE: V1 - Procrustes-PCA vs SRM
================================================================================
Metric               Group    Procrustes-PCA       SRM                  Winner
--------------------------------------------------------------------------------
ISC                  HC       0.850 ± 0.080       0.650 ± 0.120       Procrustes
                     CVD      0.450 ± 0.150       0.300 ± 0.200       Procrustes
                     p-value  0.0020 (✓)          0.0500 (✓)
                     Cohen d  2.800               2.000
--------------------------------------------------------------------------------
Deviation            HC       0.120 ± 0.030       0.200 ± 0.050       Procrustes
                     CVD      0.350 ± 0.080       0.450 ± 0.100       Procrustes
                     p-value  0.0010 (✓)          0.0080 (✓)
                     Cohen d  3.500               2.800
--------------------------------------------------------------------------------
Circularity          HC       0.930 ± 0.050       0.850 ± 0.080       Procrustes
                     CVD      0.800 ± 0.100       0.750 ± 0.120       Procrustes
                     p-value  0.0150 (✓)          0.0400 (✓)
                     Cohen d  1.500               1.200
================================================================================
```

**Interpretation**:
- **ISC (higher is better)**: Which method shows better within-group consistency?
- **Deviation (lower is better)**: Which method shows clearer HC-CVD separation?
- **Circularity (closer to 1.0 is better)**: Which method preserves color wheel structure?
- **Winner**: Method with better performance for that metric

### Visualization Plots

**1. Bar Plot** (`{ROI}_method_comparison_barplot.png`):
- Side-by-side comparison of HC vs CVD for each metric
- Blue bars: Procrustes-PCA
- Orange/Coral bars: SRM
- Stars (*) indicate significant HC-CVD differences
- Compare bar heights to see which method shows stronger effects

**2. Scatter Plot** (`{ROI}_method_correlation_scatter.png`):
- Each point = one subject
- Blue: HC subjects
- Red: CVD subjects
- Diagonal line = perfect agreement
- Pearson r and p-value show method consistency
- Points far from diagonal = method disagreement

**3. Reliability Comparison** (`{ROI}_reliability_comparison.png`):
- Split-half reliability for both methods
- Green dashed line at 0.5 = "good" threshold
- Higher bars = more reliable RDMs

---

## Expected Findings

### Hypotheses

**H1: Procrustes-PCA shows higher RDM reliability**
- Reason: Run averaging + Crossnobis + PCA denoising
- Expected: Procrustes reliability >0.5, SRM reliability <0.5 (based on previous results)

**H2: Procrustes-PCA shows stronger HC-CVD separation**
- Metrics: Larger ISC difference, clearer deviation
- Reason: Higher dimensionality (k=50 vs k≤8), normative modeling

**H3: Procrustes-PCA preserves circular structure better**
- Metric: Higher circularity (closer to 1.0)
- Reason: PCA preserves geometry (Brouwer & Heeger 2009)

**H4: Both methods show V2/V3 maximal effects**
- Agreement: Both should show strongest HC-CVD differences in color ROIs
- Validation: Confirms biological reality if both methods converge

### Possible Outcomes

**Scenario A: Strong Procrustes advantage**
- Procrustes wins on all metrics
- Interpretation: Higher dimensionality + geometry preservation critical

**Scenario B: Comparable performance**
- Similar ISC, deviation, circularity
- Interpretation: Both methods capture key effects; dimensionality less critical

**Scenario C: Method-specific advantages**
- Procrustes: Better reliability, circularity
- SRM: Comparable ISC, deviation
- Interpretation: Methods capture different aspects of representation

**Scenario D: ROI-dependent effects**
- V1: Methods similar (low-dimensional sufficient)
- V2/V3: Procrustes advantage (high-dimensional needed)
- Interpretation: ROI complexity determines optimal method

---

## Troubleshooting

### Issue: "SRM patterns not found"

**Cause**: Incorrect SRM directory or filename pattern

**Solution**:
```bash
# Check SRM directory structure
ls /path/to/srm/results/V1/

# If filenames differ, update load_srm_patterns() in compute_srm_metrics.py
# Add your filename pattern to possible_paths list
```

### Issue: "Unexpected shape" warning

**Cause**: SRM output has different dimensions

**Solution**:
1. Check SRM output shape:
```python
import numpy as np
patterns = np.load('/path/to/srm/results/V1/sub-01_aligned_patterns.npy')
print(patterns.shape)  # Should be (n_runs, 8, k_srm)
```

2. If shape is (8, k_srm, n_runs), transpose before saving:
```python
patterns_transposed = np.transpose(patterns, (2, 0, 1))
```

### Issue: Low correlation between methods

**Expected**: Methods may differ due to:
- Dimensionality: k=50 (Procrustes) vs k≤8 (SRM)
- Alignment: Orthogonal Procrustes vs shared response model
- RDM computation: Crossnobis vs correlation

**Interpretation**: Focus on whether both methods show **same direction** of HC-CVD effects, not absolute agreement

### Issue: Missing subjects in comparison

**Cause**: Subject not in both datasets

**Solution**: The comparison script automatically uses common subjects only. Check:
```bash
# Procrustes subjects
ls results/step4_metrics/V1/ | grep sub-

# SRM subjects
ls results/srm_metrics/V1/ | grep sub-

# Compare lists
```

---

## Batch Processing

### SLURM Script (Server)

Create `sbatch/compare_with_srm.sbatch`:

```bash
#!/bin/bash
#SBATCH --job-name=srm_comparison
#SBATCH --qos=shared
#SBATCH --nodelist=node2
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=logs/srm_comparison_%j.out
#SBATCH --error=logs/srm_comparison_%j.err

set -e

source ~/.bashrc
conda activate nilearn

cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/postSRM_procrus

ROIS=(V1 V2 V3 hV4)
SRM_DIR=/path/to/your/srm/results

for ROI in "${ROIS[@]}"; do
    echo "=== Processing $ROI ==="

    # Compute SRM metrics
    python compute_srm_metrics.py \
        --roi $ROI \
        --srm-dir $SRM_DIR \
        --output-dir results/srm_metrics

    # Compare methods
    python compare_procrustes_vs_srm.py \
        --roi $ROI \
        --procrustes-dir results/step4_metrics \
        --srm-dir results/srm_metrics \
        --output-dir results/comparison
done

echo "✓ All ROIs compared"
```

Submit:
```bash
sbatch sbatch/compare_with_srm.sbatch
```

---

## Output Summary

After running both scripts for all ROIs, you'll have:

```
results/
├── srm_metrics/                       # SRM geometric metrics
│   ├── V1/
│   │   ├── geometric_metrics_srm.json
│   │   ├── hc_vs_cvd_statistics_srm.json
│   │   ├── sub-*_rdm_srm.npy
│   │   └── rdm_hc_mean_srm.npy
│   ├── V2/
│   ├── V3/
│   └── hV4/
│
└── comparison/                        # Method comparison
    ├── V1_method_comparison_barplot.png
    ├── V1_method_correlation_scatter.png
    ├── V1_reliability_comparison.png
    ├── V2_method_comparison_barplot.png
    ├── V2_method_correlation_scatter.png
    ├── V2_reliability_comparison.png
    ├── V3_*.png
    └── hV4_*.png
```

---

## Manuscript Figures

### Recommended Figures for Paper

**Figure 1: Method Comparison (Main Result)**
- Use: `{ROI}_method_comparison_barplot.png` for all 4 ROIs
- Layout: 4-panel figure (one per ROI)
- Caption: "Geometric metrics comparison: Procrustes-PCA vs SRM. Procrustes-PCA shows higher ISC, lower deviation, and better preserved circularity across all ROIs."

**Figure 2: Method Agreement (Supplementary)**
- Use: `{ROI}_method_correlation_scatter.png` for V2 or V3
- Caption: "Per-subject correlation between methods. Both methods identify similar HC-CVD differences despite different dimensionality (r=0.XX, p<0.05)."

**Figure 3: Reliability (Supplementary)**
- Use: `{ROI}_reliability_comparison.png` for all ROIs
- Caption: "RDM split-half reliability. Procrustes-PCA achieves higher reliability (>0.5) compared to SRM due to run averaging and optimal covariance estimation."

---

## Analysis Checklist

After completing the comparison:

- [ ] Procrustes-PCA pipeline complete (Steps 1-4)
- [ ] SRM metrics computed for all ROIs
- [ ] Comparison plots generated for all ROIs
- [ ] Summary tables reviewed
- [ ] Key findings documented:
  - [ ] Which method shows higher reliability?
  - [ ] Which method shows stronger HC-CVD separation?
  - [ ] Do both methods agree on V2/V3 maximal effects?
  - [ ] Are there ROI-specific differences between methods?
- [ ] Manuscript figures selected
- [ ] Statistical results reported (p-values, effect sizes)

---

## Quick Command Reference

**Compute SRM metrics** (single ROI):
```bash
python compute_srm_metrics.py --roi V1 --srm-dir /path/to/srm/results
```

**Compare methods** (single ROI):
```bash
python compare_procrustes_vs_srm.py --roi V1
```

**Batch process** (all ROIs):
```bash
for roi in V1 V2 V3 hV4; do
    python compute_srm_metrics.py --roi $roi --srm-dir /path/to/srm/results
    python compare_procrustes_vs_srm.py --roi $roi
done
```

**Check outputs**:
```bash
# View comparison plot
open results/comparison/V1_method_comparison_barplot.png

# Check statistics
cat results/srm_metrics/V1/hc_vs_cvd_statistics_srm.json | jq '.isc'
cat results/step4_metrics/V1/hc_vs_cvd_statistics.json | jq '.isc'
```

---

## Support

**For questions**:
- See main `EXECUTION_GUIDE.md` for Procrustes-PCA details
- Check `README.md` for conceptual overview
- Review `IMPLEMENTATION_SUMMARY.md` for technical details

**For SRM-specific issues**:
- Check SRM output directory structure
- Verify filename patterns in `compute_srm_metrics.py`
- Ensure consistent subject IDs between methods

---

**Status**: Ready for SRM comparison analysis
