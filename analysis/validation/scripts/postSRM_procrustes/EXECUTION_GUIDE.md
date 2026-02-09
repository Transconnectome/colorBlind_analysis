# Execution Guide: Procrustes Alignment & Geometric Analysis Pipeline

## Overview

This pipeline implements geometry-centered analysis using Procrustes alignment with run averaging and Crossnobis RDMs. The goal is to quantify HC representational consistency and CVD deviations.

**Method**: PCA dimension reduction (RECOMMENDED) or ANOVA voxel selection

## Pipeline Steps

```
Step 1: PCA Dimension Reduction (or ANOVA selection)
   ↓
Step 2: Iterative Procrustes (HC Template)
   ↓
Step 3: Compute Crossnobis RDMs
   ↓
Step 4: Geometric Metrics (ISC, deviation, circularity)
   ↓
Step 5: Visualization & Reporting
```

---

## Local Testing (Quick Start)

### Test 1: Single Subject-ROI (V1, sub-01)

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus

# Step 1: PCA dimension reduction
python step1a_dimension_reduction_pca.py --subject 01 --roi V1 --n-components 50

# Step 2: Procrustes (requires all HC subjects completed Step 1)
# First, complete Step 1 for all HC subjects:
for subj in 01 02 03 04 05 06 08 09 10; do
    python step1a_dimension_reduction_pca.py --subject $subj --roi V1 --n-components 50
done

# Then run Step 2:
python step2_iterative_procrustes.py --roi V1 --max-iter 10 --method pca

# Step 3: Crossnobis RDMs (per subject)
python step3_compute_rdms_crossnobis.py --subject 01 --roi V1 --method pca

# Complete Step 3 for all subjects:
for subj in 01 02 03 04 05 06 08 09 10; do
    python step3_compute_rdms_crossnobis.py --subject $subj --roi V1 --method pca
done

# Step 4: Geometric metrics (requires all subjects)
python step4_geometric_metrics.py --roi V1 --method pca

# Step 5: Visualizations
python step5_visualize_report.py --roi V1 --method pca
```

**Expected Runtime**: 5-10 minutes total for V1

**Validation Checkpoints**:
- Step 1: Check cumulative variance >80% in `results/step1_pca/V1/sub-01_metadata.json`
- Step 2: Check convergence in 3-5 iterations in `results/step2_procrustes/V1/convergence_history.json`
- Step 3: Check split-half reliability >0.5 in `results/step3_rdms/V1/sub-01_split_half_reliability.json`
- Step 4: Check ISC values in `results/step4_metrics/V1/geometric_metrics.json`
- Step 5: Verify PCA color wheel structure in `results/step5_visualizations/V1_pca_diagnostics.png`

---

## Server Execution (Production)

### Preparation

1. **Upload scripts to server** (use single scp command):

```bash
# From local machine
scp -r /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/
```

2. **Update paths in scripts** (if needed):
   - Edit baseline-dir path in `step1a_dimension_reduction_pca.py` line 91
   - Update to: `/scratch/connectome/haba6030/colorBlind/derivatives/baseline`

### Run Full Pipeline

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/postSRM_procrus

# Submit full pipeline (all ROIs)
sbatch sbatch/run_full_pipeline_pca.sbatch
```

### Monitor Progress

```bash
# Check job status
squeue -u haba6030

# Watch output
tail -f results/pipeline_*.log

# Check Step 1 completion
ls results/step1_pca/V1/sub-*_metadata.json | wc -l  # Should be 9 (all subjects)

# Check Step 2 convergence
cat results/step2_procrustes/V1/convergence_history.json

# Check Step 4 statistics
cat results/step4_metrics/V1/hc_vs_cvd_statistics.json
```

---

## Alternative: ANOVA Method

If you want to compare with ANOVA voxel selection:

```bash
# Step 1b: ANOVA selection (instead of PCA)
python step1b_voxel_selection_anova.py --subject 01 --roi V1 --k 500

# Continue with steps 2-5 using --method anova flag
python step2_iterative_procrustes.py --roi V1 --method anova
python step3_compute_rdms_crossnobis.py --subject 01 --roi V1 --method anova
python step4_geometric_metrics.py --roi V1 --method anova
python step5_visualize_report.py --roi V1 --method anova
```

**Note**: PCA is recommended (preserves geometry), ANOVA is for comparison.

---

## Output Structure

```
results/
├── step1_pca/                          # PCA dimension reduction
│   ├── V1/
│   │   ├── sub-01_odd_pc.npy          # (8 colors, 50 components)
│   │   ├── sub-01_even_pc.npy
│   │   ├── sub-01_explained_variance.npy
│   │   └── sub-01_metadata.json
│   └── ...
├── step2_procrustes/                   # HC template & alignment
│   ├── V1/
│   │   ├── template_hc.npy            # (8, 50) HC template
│   │   ├── convergence_history.json
│   │   ├── sub-01_aligned_odd.npy     # (8, 50) aligned
│   │   ├── sub-01_aligned_even.npy
│   │   ├── sub-01_transformation_R.npy # (50, 50) rotation
│   │   └── sub-01_disparity.json
│   └── ...
├── step3_rdms/                         # Crossnobis RDMs
│   ├── V1/
│   │   ├── sub-01_rdm_crossnobis.npy  # (8, 8) Mahalanobis
│   │   ├── sub-01_rdm_odd.npy         # (8, 8) correlation
│   │   ├── sub-01_rdm_even.npy
│   │   ├── sub-01_split_half_reliability.json
│   │   └── sub-01_shrinkage.json
│   └── ...
├── step4_metrics/                      # Geometric metrics
│   ├── V1/
│   │   ├── geometric_metrics.json     # ISC, deviation, circularity per subject
│   │   ├── hc_vs_cvd_statistics.json  # HC vs CVD comparison
│   │   └── rdm_hc_mean.npy
│   └── ...
└── step5_visualizations/               # Publication figures
    ├── V1_pca_diagnostics.png         # PC1-PC2 color wheel, scree
    ├── V1_rdm_heatmaps.png            # HC/CVD RDM comparison
    ├── V1_geometric_metrics_barplot.png
    └── V1_procrustes_convergence.png
```

---

## Key Metrics to Check

### Step 1: PCA Validation
- **Cumulative variance**: >80% (indicates sufficient components)
- **First PC variance**: ~15-30% (typical for color data)
- **PC1-PC2 structure**: Circular arrangement of 8 colors (Brouwer & Heeger 2009)

### Step 2: Procrustes Convergence
- **Iterations**: 3-5 (typical)
- **Final template change**: <0.001 (convergence threshold)
- **Mean disparity**: Should decrease monotonically

### Step 3: RDM Quality
- **Split-half reliability**: >0.5 (good), >0.7 (excellent)
- **Shrinkage λ**: 0.2-0.4 (typical for fMRI)
- **RDM symmetry**: Check validation flags

### Step 4: Geometric Metrics
- **ISC**: HC > CVD (hypothesis)
- **Deviation**: CVD > HC (hypothesis)
- **Circularity**: HC ≈ 0.9-1.0, CVD < HC (hypothesis)
- **MDS stress**: <0.15 (good fit)

### Step 5: Visual Checks
- **PC1-PC2 plot**: Colors should form circular arrangement for HC
- **RDM heatmaps**: Check for structured dissimilarity patterns
- **Metrics barplots**: Significant HC-CVD differences (p<0.05)

---

## Troubleshooting

### Issue: Step 1 fails with "cannot normalize near-zero matrix"
**Solution**: Check input amplitudes for NaN/Inf values. Re-run baseline decoding if needed.

### Issue: Step 2 doesn't converge
**Symptoms**: Template change remains >0.001 after 10 iterations
**Solution**: Increase `--max-iter 20` or check if subjects have very different voxel counts

### Issue: Step 3 reliability <0.3
**Symptoms**: Poor split-half correlation
**Possible causes**:
- Low SNR in this ROI
- Insufficient voxels/components
- Procrustes alignment failed
**Solution**: Check Step 2 disparities, try increasing n_components

### Issue: Step 5 PCA color wheel not circular
**Interpretation**:
- HC not circular → Check data quality, may be real effect
- CVD not circular → Expected (hypothesis: CVD distorted)
- Both not circular → Reconsider PCA components or check Procrustes

---

## Expected Results Summary

### Hypotheses

**H1: HC Geometric Consistency**
- ISC_hc: 0.7-0.9 (high within-group consistency)
- Circularity_hc: 0.85-0.95 (circular hue structure)

**H2: CVD Deviations**
- ISC_cvd: 0.4-0.7 (lower consistency, heterogeneous)
- Deviation_cvd > Deviation_hc (distance from norm)
- Circularity_cvd: 0.70-0.90 (distorted structure)

**H3: ROI Hierarchy**
- V1: Minimal HC-CVD difference (low-level)
- V2/V3: Maximum HC-CVD difference (color processing)
- hV4: Moderate difference (color-selective)

---

## Comparison with SRM

**Why Procrustes-PCA over SRM?**

| Feature | SRM (previous) | Procrustes-PCA (this) |
|---------|----------------|------------------------|
| Dimensionality | k≤8 (constrained) | k=50-100 (full variance) |
| Template | Joint HC+CVD | HC-only normative |
| Noise handling | Minimal | Run averaging + Crossnobis |
| Geometry | May distort | PCA preserves (B&H 2009) |
| RDM reliability | 0.03-0.45 (low) | Expected >0.5 |
| CVD heterogeneity | Negative inter-corr | Pairwise deviation |

**Expected Improvements**:
- +30-50% RDM reliability (run averaging + Crossnobis + PCA denoising)
- Better HC-CVD separation (normative modeling)
- Interpretable geometry (PC1-PC2 color wheel)

---

## Download Results

```bash
# From local machine
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/postSRM_procrus/results \
    /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus/
```

---

## Next Steps After Pipeline Completion

1. **Analyze results**: Check Step 4 statistics JSON files
2. **Manuscript figures**: Use Step 5 visualizations
3. **ROI comparison**: Run for all 4 ROIs, compare metrics
4. **Individual CVD analysis**: Check which CVD subjects deviate most
5. **Relate to behavior**: Correlate deviation with color perception tests (if available)

---

## Contact & Support

For issues, consult:
- Plan document: `PLAN_procrustes_geometric_analysis.md`
- Code comments in each step script
- Brouwer & Heeger (2009) for PCA rationale
- Haxby et al. (2011) for iterative Procrustes
- Walther et al. (2016) for Crossnobis theory
