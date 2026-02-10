# Procrustes-PCA Pipeline Execution Summary

**Date**: 2026-02-08  
**ROI**: V1  
**PCA Components**: 12  
**Conda Environment**: neuroImage  

## Pipeline Configuration

- **Baseline Directory**: `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/baseline`
- **Output Directory**: `results/quick_test_pca12/`
- **Subjects**: 9 total (6 HC + 3 CVD)
  - HC: sub-01, sub-02, sub-03, sub-04, sub-05, sub-06
  - CVD: sub-08, sub-09, sub-10

## Execution Steps

### Step 1: PCA Dimension Reduction
**Script**: `step1a_dimension_reduction_pca.py`

Processed all 9 subjects individually:
- Loaded z-scored amplitudes from baseline analysis
- Averaged runs (odd/even split)
- Applied PCA with n_components=12
- Mean variance explained: **99.5%**

**Output files per subject**:
- `{sub}_odd_pc.npy` - (8 colors, 12 PCs)
- `{sub}_even_pc.npy` - (8 colors, 12 PCs)
- `{sub}_explained_variance.npy`
- `{sub}_metadata.json`

### Step 2: Iterative Procrustes Alignment
**Script**: `step2_iterative_procrustes.py` + manual alignment

Created HC template and aligned all subjects:
- Built template from 6 HC subjects using iterative Procrustes
- Aligned all 9 subjects (odd and even) to template
- Mean odd disparity: **3.24**
- Mean even disparity: **3.05**

**Output files**:
- `template_hc.npy` - HC group template (8, 12)
- `{sub}_aligned_odd.npy` - Per subject (9 subjects)
- `{sub}_aligned_even.npy` - Per subject (9 subjects)
- `procrustes_disparities.json`
- `convergence_history.json`

### Step 3: Crossnobis RDM Computation
**Script**: `step3_compute_rdms_crossnobis.py`

Computed RDMs for all 9 subjects:
- Used aligned odd/even patterns
- Applied Ledoit-Wolf covariance shrinkage
- Computed crossnobis distances between colors
- Mean shrinkage λ: ~0.22

**Split-half reliability**:
- HC mean: **-0.053**
- CVD mean: **-0.121**

**Output files per subject**:
- `{sub}_rdm_crossnobis.npy` - (8, 8)
- `{sub}_rdm_odd.npy` - (8, 8)
- `{sub}_rdm_even.npy` - (8, 8)
- `{sub}_split_half_reliability.json`
- `{sub}_shrinkage.json`

## Results Summary

### PCA Performance
| Group | Mean Voxels | Mean Variance Explained |
|-------|-------------|-------------------------|
| HC    | 381         | 99.48%                  |
| CVD   | 401         | 99.50%                  |

### Procrustes Alignment
| Metric | Value |
|--------|-------|
| Mean odd disparity | 3.24 |
| Mean even disparity | 3.05 |
| HC template shape | (8, 12) |

### RDM Reliability
| Subject | Reliability |
|---------|-------------|
| sub-01  | -0.038      |
| sub-02  | -0.106      |
| sub-03  | -0.019      |
| sub-04  | +0.011      |
| sub-05  | -0.062      |
| sub-06  | -0.103      |
| sub-08  | -0.102      |
| sub-09  | -0.144      |
| sub-10  | -0.118      |

**Group means**:
- HC: -0.053
- CVD: -0.121

## Files Created

Total: **103 files**

- PCA outputs: 27 files
- Aligned patterns: 18 files
- RDMs: 27 files
- Metadata: 28 files
- Summary: 3 files (including visualization)

## Key Output Files

```
results/quick_test_pca12/V1/
├── template_hc.npy                      # HC group template
├── pipeline_summary.json                # Complete results summary
├── pipeline_results_summary.png         # Visualization
├── procrustes_disparities.json          # Alignment quality
└── [Per-subject files]
    ├── {sub}_odd_pc.npy
    ├── {sub}_even_pc.npy
    ├── {sub}_aligned_odd.npy
    ├── {sub}_aligned_even.npy
    ├── {sub}_rdm_crossnobis.npy
    ├── {sub}_rdm_odd.npy
    ├── {sub}_rdm_even.npy
    ├── {sub}_metadata.json
    └── {sub}_split_half_reliability.json
```

## Notes

1. **Negative reliabilities**: The negative split-half reliabilities indicate low or unstable RDM patterns, possibly due to:
   - High dimensionality (12 PCs for 8 colors)
   - Low signal-to-noise ratio
   - Procrustes alignment artifacts
   
2. **Next steps**: Consider testing with different numbers of PCs (e.g., 4, 6, 8) to optimize reliability

3. **Environment**: All scripts executed successfully in conda environment `neuroImage`

