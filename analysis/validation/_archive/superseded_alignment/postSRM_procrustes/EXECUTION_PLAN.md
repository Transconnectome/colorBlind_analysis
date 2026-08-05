# Execution Plan: PCA/ANOVA Procrustes vs SRM Comparison

**Date**: 2026-02-08
**Goal**: Grid search optimal dimensions, run Procrustes pipeline, compare with SRM

---

## 📋 Overview

This plan implements:
1. **Grid search** to find optimal PCA dimensions and ANOVA voxel counts
2. **Full Procrustes pipeline** (Steps 1-5) with optimal configurations
3. **Method comparison**: PCA-Procrustes vs ANOVA-Procrustes vs SRM

---

## 🔧 Prerequisites

### 1. Conda Environment
```bash
conda activate nilearn
```

### 2. Required Data
- ✅ Baseline results: `/path/to/baseline/` (amplitudes_z.npy)
- ⏳ SRM results (optional): `../srm/results/srm_between_subject/`

### 3. Expected Runtime
- **Grid search** (local): 4-6 hours per ROI
- **Full pipeline** (after grid search): 30-60 min per ROI
- **Total** (all 4 ROIs): ~20-30 hours local, ~6-8 hours on server

---

## 📊 Grid Search Configuration

### PCA Candidates (All ROIs)
```python
PCA_CANDIDATES = [5, 8, 10, 12, 15, 16]  # Max 16 due to n_samples=16
```

**Rationale**:
- n=5-8: Comparable to SRM (k≤8)
- n=10-12: Mid-range
- n=15-16: Maximum possible

### ANOVA Candidates (ROI-specific)
```python
ANOVA_CANDIDATES = {
    'V1': [50, 100, 150, 200, 250, 300],  # Max 300 (min voxel count)
    'V2': [50, 100, 150, 200, 234],       # Max 234
    'V3': [20, 30, 40, 50],               # Max 50
    'hV4': [30, 40, 50, 57],              # Max 57
}
```

### Selection Criterion
**Primary**: RDM reliability (split-half correlation) averaged across HC subjects

**Secondary**:
- Explained variance (PCA): >80% preferred
- HC internal consistency (ISC)
- Procrustes convergence speed

---

## 🚀 Execution Steps

### Option 1: Automated Full Pipeline (Recommended)

Run everything with a single command:

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrustes

# Full pipeline with user prompts
bash run_full_pipeline_with_grid_search.sh
```

**What it does**:
1. Asks if you want to run grid search (or use existing results)
2. Runs grid search for all ROIs (PCA + ANOVA)
3. Loads optimal dimensions
4. Runs full pipeline (Steps 1-5) with optimal configs
5. Computes SRM metrics (if SRM results exist)
6. Compares all methods

**Interactive prompt**:
```
Run grid search? This will take several hours. (y/n):
```

- Type `y` to run grid search (first time)
- Type `n` to use existing `optimal_dimensions.json`

---

### Option 2: Step-by-Step Manual Execution

#### Step 2.1: Grid Search (Single ROI Test)

Test with V1 first:

```bash
python step0_determine_optimal_dimensions.py \
    --roi V1 \
    --method both \
    --baseline-dir "/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/baseline" \
    --output-dir "./results/step0_grid_search"
```

**Expected output**:
```
Testing PCA V1 with 5...
  Step 1: Dimension reduction (9 subjects)...
  Step 2: Procrustes alignment...
  Step 3: Crossnobis RDMs (9 subjects)...
  Evaluating metrics...
  ✓ Mean RDM reliability: 0.5234

Testing PCA V1 with 8...
  ...

PCA Optimal Configuration
  n_components: 12
  Mean RDM reliability: 0.6543 ± 0.1234
  Mean explained variance: 0.8765
```

**Output files**:
- `results/step0_grid_search/V1_both_grid_search_YYYYMMDD_HHMMSS.json`
- `results/step0_grid_search/optimal_dimensions.json` (updated)

#### Step 2.2: Grid Search (All ROIs)

After V1 test succeeds:

```bash
for roi in V1 V2 V3 hV4; do
    echo "Grid search: ${roi}"
    python step0_determine_optimal_dimensions.py \
        --roi ${roi} \
        --method both \
        --baseline-dir "/path/to/baseline" \
        --output-dir "./results/step0_grid_search"
done
```

#### Step 2.3: Review Optimal Dimensions

```bash
cat results/step0_grid_search/optimal_dimensions.json
```

Expected format:
```json
{
  "pca": {
    "V1": {
      "n_components": 12,
      "rdm_reliability": 0.6543,
      "explained_variance": 0.8765
    },
    "V2": {...},
    ...
  },
  "anova": {
    "V1": {
      "k_voxels": 200,
      "rdm_reliability": 0.5821
    },
    ...
  }
}
```

#### Step 2.4: Run Full Pipeline with Optimal Config

The automated script handles this, but manual execution:

```bash
# Load optimal dimensions
OPTIMAL_PCA_V1=$(jq -r '.pca.V1.n_components' results/step0_grid_search/optimal_dimensions.json)

# Run Steps 1-5 for V1 PCA
for subj in 01 02 03 04 05 06 08 09 10; do
    python step1a_dimension_reduction_pca.py \
        --subject ${subj} \
        --roi V1 \
        --n-components ${OPTIMAL_PCA_V1} \
        --output-dir results/step1_pca_optimal
done

python step2_iterative_procrustes.py --roi V1 --method pca \
    --input-dir results/step1_pca_optimal \
    --output-dir results/step2_procrustes_pca_optimal

# Continue with steps 3-5...
```

#### Step 2.5: Method Comparison

```bash
# Compare PCA vs ANOVA
for roi in V1 V2 V3 hV4; do
    python compare_procrustes_methods.py \
        --roi ${roi} \
        --pca-dir results/step4_metrics_pca_optimal \
        --anova-dir results/step4_metrics_anova_optimal \
        --output-dir results/method_comparison
done

# Compare with SRM (if available)
for roi in V1 V2 V3 hV4; do
    python compare_procrustes_vs_srm.py \
        --roi ${roi} \
        --procrustes-dir results/step4_metrics_pca_optimal \
        --srm-dir results/srm_metrics \
        --output-dir results/srm_comparison
done
```

---

## 📁 Output Structure

```
postSRM_procrustes/
└── results/
    ├── step0_grid_search/
    │   ├── optimal_dimensions.json          # ← KEY: Selected optimal params
    │   ├── V1_both_grid_search_*.json
    │   ├── V2_both_grid_search_*.json
    │   └── ...
    │
    ├── step1_pca_optimal/                   # PCA with optimal n_components
    │   └── {ROI}/
    │       ├── sub-*_odd_pc.npy
    │       ├── sub-*_even_pc.npy
    │       └── sub-*_metadata.json
    │
    ├── step1_anova_optimal/                 # ANOVA with optimal k_voxels
    │   └── {ROI}/...
    │
    ├── step2_procrustes_pca_optimal/
    │   └── {ROI}/
    │       ├── template_hc.npy
    │       ├── convergence_history.json
    │       └── sub-*_aligned_*.npy
    │
    ├── step3_rdms_pca_optimal/
    │   └── {ROI}/
    │       ├── sub-*_rdm_crossnobis.npy
    │       └── sub-*_split_half_reliability.json  # ← Used for grid search
    │
    ├── step4_metrics_pca_optimal/
    │   └── {ROI}/
    │       ├── geometric_metrics.json       # ← KEY: Per-subject metrics
    │       └── hc_vs_cvd_statistics.json    # ← KEY: Group comparison
    │
    ├── step5_visualizations_pca_optimal/
    │   ├── {ROI}_pca_diagnostics.png
    │   ├── {ROI}_rdm_heatmaps.png
    │   └── {ROI}_geometric_metrics_barplot.png
    │
    ├── method_comparison/
    │   ├── {ROI}_pca_vs_anova_comparison.json
    │   ├── {ROI}_method_comparison_boxplots.png
    │   └── {ROI}_method_correlation_scatter.png
    │
    └── srm_comparison/
        ├── {ROI}_procrustes_vs_srm_comparison.json
        ├── {ROI}_method_comparison_barplot.png
        └── {ROI}_reliability_comparison.png
```

---

## 📊 Expected Results

### Grid Search Outcomes

**Hypothesis**: Optimal n_components likely in 10-16 range

**Expected optimal dimensions**:
```
V1:  PCA n=12-16, ANOVA k=200-300
V2:  PCA n=10-15, ANOVA k=150-234
V3:  PCA n=8-12,  ANOVA k=40-50
hV4: PCA n=10-15, ANOVA k=40-57
```

### Method Comparison (Predicted)

**RDM Reliability** (split-half correlation):

| Method | V1 | V2 | V3 | hV4 |
|--------|----|----|----|----|
| **SRM** (k=3-4) | 0.26 | 0.45 | 0.20 | 0.03 |
| **PCA-Procrustes** (k=10-16) | 0.55-0.70 | 0.60-0.75 | 0.45-0.60 | 0.40-0.55 |
| **ANOVA-Procrustes** (k varies) | 0.50-0.65 | 0.55-0.70 | 0.40-0.55 | 0.35-0.50 |

**Expected improvements**:
- +100-150% reliability increase over SRM
- PCA slightly better than ANOVA (geometry preservation)
- V2 highest reliability across all methods

### HC-CVD Differences

**Prediction**: V2 and V3 show significant HC-CVD differences across all methods

| ROI | SRM Significant? | Procrustes-PCA Expected | Procrustes-ANOVA Expected |
|-----|------------------|-------------------------|---------------------------|
| V1  | ❌ No (p=0.31)  | Borderline (p~0.05)     | Borderline (p~0.05)       |
| V2  | ✅ Yes (p<0.001, d=6.68) | ✅ Yes (p<0.01, d~3-5)  | ✅ Yes (p<0.01, d~2-4)    |
| V3  | ✅ Yes (p=0.002, d=3.71) | ✅ Yes (p<0.05, d~2-3)  | ✅ Yes (p<0.05, d~1.5-2.5)|
| hV4 | ❌ No (p=0.55)  | Maybe (p~0.10)          | Maybe (p~0.10)            |

**Key validation**: If Procrustes also shows V2/V3 effects → SRM findings are real (despite low reliability)

---

## ⚠️ Troubleshooting

### Issue: Grid search takes too long

**Solution**: Run on server with SLURM array jobs

```bash
# Upload to server
scp -r postSRM_procrustes haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/

# Create SLURM script for grid search (TODO: implement)
sbatch sbatch/run_grid_search_array.sbatch
```

### Issue: Out of memory during PCA

**Symptom**: Script crashes during step1_pca

**Solution**: PCA with n_components=16 should be fine for all ROIs
- V3/hV4 have <60 voxels → very low memory
- V1/V2 have 200-400 voxels → still manageable

If issues persist: reduce to smaller grid [5, 8, 12, 16]

### Issue: Step 3 reliability computation fails

**Symptom**: NaN values in split_half_reliability.json

**Possible causes**:
1. Procrustes alignment failed (check step2 convergence)
2. Insufficient signal (check SNR in baseline results)
3. Shrinkage covariance issues (check shrinkage lambda values)

**Solution**: Check step2 convergence_history.json and step1 metadata

### Issue: No SRM results for comparison

**Expected**: SRM comparison will be skipped

**To generate SRM results**:
```bash
cd ../srm
bash run_srm_between_subject_local_all.sh
```

---

## 🎯 Success Criteria

### Minimum Success
1. ✅ Grid search completes for all 4 ROIs
2. ✅ Optimal dimensions selected based on RDM reliability
3. ✅ Full pipeline (Steps 1-5) runs successfully
4. ✅ PCA and ANOVA results comparable (correlation r>0.7)

### Expected Success
1. ✅ RDM reliability >0.5 for V1/V2 (vs SRM 0.26/0.45)
2. ✅ V2/V3 show significant HC-CVD differences (p<0.05)
3. ✅ PCA outperforms ANOVA slightly (better geometry)
4. ✅ Results consistent with SRM (V2/V3 effects validated)

### Ideal Success
1. ✅ RDM reliability >0.6 for all ROIs
2. ✅ V2/V3 HC-CVD effects robust (p<0.01, d>2)
3. ✅ Clear winner method (PCA or ANOVA)
4. ✅ SRM comparison confirms findings across methods

---

## 📝 Next Steps After Completion

1. **Analyze optimal dimensions**:
   - Why is optimal n_components X for each ROI?
   - Relationship to explained variance?

2. **Interpret HC-CVD differences**:
   - Which colors drive V2/V3 effects?
   - Color-specific analysis (Step 6, TODO)

3. **Method selection for publication**:
   - PCA or ANOVA?
   - Justify choice based on reliability + interpretability

4. **Within-subject analysis** (from TODO_ENHANCEMENTS.md):
   - Compare within-subject stability across methods
   - Validate that between-subject differences > within-subject noise

5. **Manuscript preparation**:
   - Use visualizations from step5
   - Report optimal dimensions in methods
   - Show method comparison in supplementary

---

## 📚 Key Files to Monitor

### During Grid Search
```bash
# Watch progress
tail -f results/step0_grid_search/V1_both_grid_search_*.json

# Check optimal dimensions so far
cat results/step0_grid_search/optimal_dimensions.json
```

### After Full Pipeline
```bash
# Check HC-CVD statistics
cat results/step4_metrics_pca_optimal/V2/hc_vs_cvd_statistics.json

# View key plots
open results/step5_visualizations_pca_optimal/V2_pca_diagnostics.png
open results/method_comparison/V2_method_comparison_boxplots.png
```

### For Manuscript
```bash
# Optimal dimensions table
jq . results/step0_grid_search/optimal_dimensions.json

# HC-CVD statistics all ROIs
for roi in V1 V2 V3 hV4; do
    echo "=== ${roi} ==="
    jq '.isc, .deviation' results/step4_metrics_pca_optimal/${roi}/hc_vs_cvd_statistics.json
done
```

---

**Status**: ✅ Ready to execute
**Estimated total time**: 20-30 hours local (or 6-8 hours on server with parallelization)
**Bottleneck**: Grid search (can be parallelized)

**Recommendation**: Start with V1 grid search as test, then run all ROIs overnight or on server
