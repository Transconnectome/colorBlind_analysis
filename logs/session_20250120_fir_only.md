# Session Log: FIR-Only Analysis Pipeline
**Date:** 2025-01-20
**Topic:** Implementing FIR-only approach for color decoding

---

## Context from Previous Session

In the previous conversation, we explored two approaches:
1. **Two-stage GLM approach** (Brouwer & Heeger 2009 style):
   - Stage 1: FIR GLM to estimate HRF
   - Stage 2: Use estimated HRF for amplitude estimation
   - **Result**: Failed with poor accuracy (12.5-14.6%) and high zero-variance (37-76%)
   - **Problems identified**: Circular reasoning, phase cancellation, overfitting

2. **FIR-only approach**: Direct use of FIR amplitudes without two-stage processing

User clarified: "아 근데 저 방법으로는 따로 해보고 이써서, FIR만 이용한 방법을 따로 해보고 있어요"
*(I'm trying the B&H method separately, and also trying a FIR-only method separately)*

---

## Objective

Implement a clean FIR-only pipeline that:
1. Runs per-run FIR GLM to extract amplitudes: β[run, color, voxel, delay]
2. Uses these FIR β values **directly** as amplitudes (not as intermediate step)
3. Tests multiple strategies for using the amplitudes
4. Compares performance across strategies

---

## Key Technical Understanding

### FIR GLM Fundamentals

**FIR (Finite Impulse Response) GLM:**
```python
X_FIR = design_matrix  # (n_scans, 8_colors × 8_delays = 64 regressors)
β = pinv(X_FIR) @ y    # (64, n_voxels)

# Reshape to (8_colors, 8_delays, n_voxels)
# Then transpose to (8_colors, n_voxels, 8_delays)
amplitudes[run] = β.reshape(8, 8, n_voxels).transpose(0, 2, 1)
```

**Critical point:** The β values **ARE** the amplitudes at each delay. No further "deconvolution" or processing needed to extract amplitudes.

### Dimension Preservation

- **Full dimensionality:** (runs=6, colors=8, voxels=N, delays=8)
- **No averaging** across runs (preserve all run information)
- **Color-specific** FIR (separate HRF estimation per color)

---

## Pipeline Overview

### Files Created/Modified

1. **`fir_per_run_simple.py`** (Main analysis script)
   - Already created in previous session
   - Implements 5 strategies for using FIR amplitudes

2. **`run_fir_simple.sbatch`** (SLURM batch script)
   - **NEW**: Created in this session
   - Runs all strategies systematically
   - Tests with/without PCA for 4 subjects × 4 ROIs

3. **`analyze_fir_simple_results.py`** (Results analysis)
   - **NEW**: Created in this session
   - Compares all strategies
   - Creates comprehensive visualizations

---

## Strategies for Using FIR Amplitudes

### Strategy 1: `flatten`
- **Description:** Use all delays, flatten to (runs, colors, voxels × delays)
- **Features per color:** n_voxels × n_delays
- **Rationale:** Preserves full temporal information
```python
features = amplitudes.reshape(N_RUNS, N_COLORS, -1)
# Shape: (6, 8, voxels*8)
```

### Strategy 2: `average`
- **Description:** Average across all delays
- **Features per color:** n_voxels
- **Rationale:** Reduces temporal dimension, summarizes overall response
```python
features = np.mean(amplitudes, axis=3)
# Shape: (6, 8, voxels)
```

### Strategy 3-5: `delay3`, `delay4`, `delay5`
- **Description:** Use single specific delay (3, 4, or 5 → 4.5s, 6.0s, 7.5s)
- **Features per color:** n_voxels
- **Rationale:** Use delay around expected HRF peak
```python
delay_idx = 3  # or 4, or 5
features = amplitudes[:, :, :, delay_idx]
# Shape: (6, 8, voxels)
```

---

## Analysis Pipeline

### Step 1: Load ROI Mask
```python
roi_path = "derivatives/{subject}/roi_pipeline/{ROI}_mask_*.nii.gz"
roi_img = nib.load(roi_path)
masker = NiftiMasker(mask_img=roi_img, standardize=False)
```

### Step 2: Load Data (6 runs)
- Drop first 4 volumes (VOLS_TO_DROP=4)
- Load functional data
- Load confounds (6 motion parameters)
- Clean data (detrend, confound regression)
- Adjust event onsets

### Step 3: Per-Run FIR GLM
```python
for run_idx in range(6):
    X = build_color_fir_design(events, n_scans, TR, FIR_DELAYS, N_COLORS)
    betas = np.linalg.pinv(X) @ y
    amplitudes[run_idx] = betas.reshape(8, 8, n_voxels).transpose(0, 2, 1)
```

### Step 4: Apply Strategy
```python
if strategy == 'flatten':
    features = amplitudes.reshape(N_RUNS, N_COLORS, -1)
elif strategy == 'average':
    features = np.mean(amplitudes, axis=3)
elif strategy.startswith('delay'):
    delay_idx = int(strategy[-1])
    features = amplitudes[:, :, :, delay_idx]
```

### Step 5: Z-score
```python
# Per (run, voxel) or (run, voxel×delay) across colors
for run_idx in range(N_RUNS):
    for feature_idx in range(n_features):
        vals = features[run_idx, :, feature_idx]  # 8 colors
        if np.std(vals) > 0:
            z_features[run_idx, :, feature_idx] = zscore(vals)
```

### Step 6: Classification (Leave-One-Run-Out)
```python
for test_run in range(N_RUNS):
    train_runs = [r for r in range(N_RUNS) if r != test_run]

    X_train = z_features[train_runs].reshape(-1, n_features)
    y_train = np.tile(np.arange(8), 5)  # 5 training runs

    X_test = z_features[test_run]
    y_test = np.arange(8)

    # Optional: StandardScaler + PCA
    # Classify with diagonal LDA
    y_pred = diag_linear_predict(X_train, y_train, X_test)
    accuracy = (y_pred == y_test).mean()
```

---

## Running the Analysis

### On Server (SLURM)

1. **Upload files to server:**
```bash
# From local machine
scp fir_per_run_simple.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_fir_simple.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp analyze_fir_simple_results.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

2. **Submit job:**
```bash
# On server
cd /scratch/connectome/haba6030/colorBlind
sbatch run_fir_simple.sbatch
```

3. **Monitor jobs:**
```bash
squeue -u haba6030
```

4. **Check logs:**
```bash
tail -f logs/fir_simple_*.out
tail -f logs/fir_simple_*.err
```

### After Jobs Complete

5. **Analyze results:**
```bash
# Get timestamp from output directory
ls derivatives/fir_simple/sub-01/

# Run analysis (replace TIMESTAMP with actual value)
python analyze_fir_simple_results.py --timestamp 20250120_123456
```

6. **Download results:**
```bash
# From local machine
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/fir_simple/summary/20250120_123456 .
```

---

## Expected Outputs

### Per Run Outputs
```
derivatives/fir_simple/{subject}/{timestamp}_{roi}_{strategy}_{pca}/
├── summary.json              # Classification results
├── amplitudes.npy            # FIR amplitudes (6, 8, voxels, 8)
├── z_features.npy            # Z-scored features
└── figures/
    ├── fir_per_color.png     # Mean FIR per color
    └── classification_results.png
```

### Summary Analysis Outputs
```
derivatives/fir_simple/summary/{timestamp}/
├── all_results.csv           # All results table
├── best_per_subject_roi.csv  # Best strategy per subject×ROI
├── strategy_averages.csv     # Strategy comparison
└── figures/
    ├── strategy_comparison_heatmap.png
    ├── strategy_comparison_bars.png
    ├── strategy_comparison_by_subject.png
    └── strategy_comparison_by_roi.png
```

---

## Comparison with Two-Stage Approach

| Aspect | Two-Stage Approach | FIR-Only Approach |
|--------|-------------------|-------------------|
| **HRF Estimation** | Stage 1: Per-run color-specific FIR | Same FIR, but use β directly |
| **Amplitude Extraction** | Stage 2: Convolve with estimated HRF | Use FIR β values directly |
| **Circular Reasoning** | Yes (same data for HRF + amplitude) | No |
| **Phase Cancellation** | Yes (if using ROI-average HRF) | No (no averaging) |
| **Dimension Reduction** | Yes (8 delays → 1 amplitude) | Flexible (test multiple strategies) |
| **Previous Results** | 12.5-14.6% accuracy, 37-76% zero variance | To be determined |

---

## Key Differences from B&H (2009)

| Feature | Brouwer & Heeger (2009) | FIR-Only Approach |
|---------|------------------------|-------------------|
| **FIR Type** | Color-IGNORED (all colors combined) | Color-SPECIFIC (per color) |
| **HRF Averaging** | ROI-average HRF | No averaging (preserve voxel info) |
| **2nd Level GLM** | HRF + derivative (16 regressors) | No 2nd level GLM |
| **Feature Extraction** | First 8 betas from 2nd GLM | Direct FIR β values |
| **Temporal Info** | Discarded (single amplitude) | Preserved (multiple strategies) |

---

## Research Questions to Answer

1. **Which strategy performs best?**
   - Flatten (full temporal info) vs. Average vs. Single delay

2. **Does PCA help or hurt?**
   - Compare with/without PCA (n=6 components)

3. **Is there ROI specificity?**
   - Do different ROIs benefit from different strategies?

4. **Subject variability?**
   - How consistent are results across subjects?

5. **Comparison with previous approaches?**
   - How does this compare to `fir_reconstruction_BH2009.py` results?

---

## Next Steps

After analyzing results from `run_fir_simple.sbatch`:

1. **Compare strategies**: Which performs best overall?

2. **Compare with B&H method**:
   - Run B&H two-stage approach properly (color-IGNORED FIR + ROI-average)
   - Compare FIR-only vs. B&H method

3. **Optimal delay analysis**:
   - If `delay4` or `delay5` performs best, validates HRF peak timing
   - If `flatten` performs best, suggests temporal info is important

4. **Further refinements**:
   - Test delay ranges (e.g., average delays 3-5)
   - Test weighted average (weight by response magnitude)
   - Voxel selection based on FIR response quality

---

## Technical Notes

### Z-scoring Strategy
- For `flatten`: Z-score per (run, voxel×delay) across 8 colors
- For others: Z-score per (run, voxel) across 8 colors
- This ensures color discrimination is based on relative responses

### PCA Application
- Applied **after** z-scoring and scaling
- Uses `n_components=6` (matching B&H channel model)
- Separate PCA fit for each fold (no data leakage)

### Classification Method
- Diagonal LDA (same as other analyses)
- Leave-one-run-out cross-validation (6 folds)
- Chance level: 12.5% (8 colors)

---

## References

1. **Brouwer & Heeger (2009).** Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.
   - Original paper implementing two-stage GLM with color-IGNORED FIR

2. **Kriegeskorte et al. (2006).** Information-based functional brain mapping. *PNAS*, 103(10), 3863-3868.
   - Multivariate pattern analysis, against ROI averaging

3. **Mumford et al. (2012).** Deconvolving BOLD activation in event-related designs for multivoxel pattern classification analyses. *NeuroImage*, 59(3), 2636-2643.
   - LSS/LSA methods for event-related designs, FIR usage

---

## Session Summary

**Files Created:**
1. `run_fir_simple.sbatch` - SLURM script for systematic strategy testing
2. `analyze_fir_simple_results.py` - Comprehensive results analysis
3. `logs/session_20250120_fir_only.md` - This documentation

**Files Modified:**
- None (all existing files remain unchanged)

**Key Decisions:**
- Test 5 strategies: flatten, average, delay3, delay4, delay5
- Test with/without PCA
- Systematic comparison across 4 subjects × 4 ROIs
- Comprehensive visualization and analysis

**Status:**
- Code ready to run on server
- Awaiting job submission and results

---

*End of session log*
