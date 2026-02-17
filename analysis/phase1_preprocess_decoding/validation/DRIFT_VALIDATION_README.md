# Drift Removal Validation

**Status**: Implementation complete, ready for testing
**Date**: 2026-02-16
**Test subjects**: sub-01, ROIs V1 and V2

---

## Overview

Two standalone validation scripts to test the current preprocessing pipeline (C010) drift removal methodology:

1. **validate_drift_removal.py** - Compare 1st+2nd order vs 2nd-only drift
2. **validate_onset_randomization.py** - Verify FIR robustness via onset shuffling

---

## Background

### Current Implementation (C010)

The current pipeline uses **2nd-order drift removal only** (linear + constant per run) during amplitude estimation:

```python
def create_drift_regressors(n_scans, run_idx, n_runs):
    """Current: linear + constant per run"""
    drift_cols = np.zeros((n_scans, n_runs * 2))
    drift_cols[:, run_idx - 1] = np.linspace(-0.5, 0.5, n_scans)  # Linear
    drift_cols[:, n_runs + run_idx - 1] = 1.0                      # Constant
    return drift_cols
```

**Key observations:**
- Drift applied at 2nd level (amplitude estimation), NOT at 1st level (FIR)
- Design matrix: [8 colors | 8 derivatives | 6 linear drift | 6 constants] = 28 columns
- No quadratic drift currently implemented

### Concerns

1. **HRF correlation r=0.9 seems too high** - might indicate drift contamination
2. **Original papers used 1st+2nd order drift** (quadratic + linear + constant)
3. **Convex FIR shape exists** but unclear if real or artifact

---

## Validation 1: Drift Method Comparison

**Script**: `validate_drift_removal.py`

### Purpose

Test if adding 1st-order (quadratic) drift improves HRF estimation quality.

### Methods

**2nd-only drift (current)**:
```python
drift_cols = np.zeros((n_scans, n_runs * 2))
drift_cols[:, run_idx - 1] = np.linspace(-0.5, 0.5, n_scans)  # Linear
drift_cols[:, n_runs + run_idx - 1] = 1.0                      # Constant
```

**1st+2nd drift (test)**:
```python
drift_cols = np.zeros((n_scans, n_runs * 3))
t = np.linspace(-0.5, 0.5, n_scans)

# Quadratic (centered to reduce collinearity)
drift_cols[:, run_idx - 1] = t**2 - np.mean(t**2)

# Linear
drift_cols[:, n_runs + run_idx - 1] = t

# Constant
drift_cols[:, 2 * n_runs + run_idx - 1] = 1.0
```

### Comparison Metrics

1. **HRF voxel correlation** (mean, median)
2. **FIR convexity score** (0-2 scale)
3. **RDM reliability**: raw (odd/even split-half)
4. **RDM reliability**: Procrustes aligned
5. **Procrustes disparity**

### Outputs

```
derivatives/drift_validation/sub-01/
├── V1/
│   ├── drift_comparison.json          # All comparison metrics
│   ├── drift_comparison.png           # 6-panel comparison plot
│   │
│   # 2nd-only drift outputs
│   ├── 2nd_only/
│   │   ├── amplitudes_raw.npy
│   │   ├── amplitudes_procrustes.npy
│   │   ├── roi_hrf.npy
│   │   ├── roi_hrf_deriv.npy
│   │   ├── voxel_hrfs.npy             # Individual voxel HRFs
│   │   ├── hrf_correlations.npy       # Voxel-ROI HRF correlations
│   │   ├── hrf_rmse.npy               # Voxel RMSE from ROI HRF
│   │   ├── hrf_variability.png        # 6-panel HRF variability
│   │   └── metrics.json
│   │
│   # 1st+2nd drift outputs
│   └── 1st_2nd/
│       ├── (same structure as 2nd_only)
│
└── V2/ (same structure)
```

### Visualization

**drift_comparison.png** (2×3 panels):
1. HRF shape comparison (2nd vs 1st+2nd overlaid)
2. HRF correlation distributions (2 histograms overlaid)
3. FIR convexity comparison (bar chart)
4. RDM reliability (raw vs Procrustes for both methods)
5. Procrustes disparity comparison (bar chart)
6. Summary metrics table

**hrf_variability.png** (6-panel, saved per method):
1. Individual Voxel HRFs (n=100 shown) + ROI Mean ±1 SD
2. HRF Correlation Distribution
3. HRF RMSE Distribution
4. HRF Variability Per Timepoint
5. Best (green) vs Worst (red) Fitting Voxels

---

## Validation 2: Onset Randomization

**Script**: `validate_onset_randomization.py`

### Purpose

Verify FIR estimation robustness by shuffling trial order. If the convex FIR shape is real (not drift artifact), it should be destroyed by randomization.

### Method

```python
def randomize_onsets(events_df, seed):
    """Shuffle onset times while preserving trial structure"""
    np.random.seed(seed)
    events_randomized = events_df.copy()

    # Extract color trial onsets
    color_mask = events_df['trial_type'].str.contains('color', na=False)
    onset_times = events_df.loc[color_mask, 'onset'].values

    # Shuffle and reassign
    shuffled_onsets = np.random.permutation(onset_times)
    events_randomized.loc[color_mask, 'onset'] = shuffled_onsets

    return events_randomized
```

### FIR Shape Classification

```python
def check_fir_convexity(fir_estimate):
    """
    Classify FIR shape: 'convex', 'linear_ramp', or 'random'

    Returns:
        shape_type: str
        convexity_score: float (0-2)
    """
    # Fit quadratic: check for negative curvature + peak at delays 2-5
    # Fit linear: check R² > 0.7 for linear ramp (drift contamination)
    # Otherwise: random/flat
```

### Expected Outcomes

**PRIMARY METRIC: HRF Correlation (Voxel-ROI)**

This is the **key validation metric** - it directly tests whether high HRF correlations (r ≈ 0.9) are due to real temporal structure or drift contamination.

**Proper FIR (no drift contamination)**:
- **HRF correlation**:
  - Original: r ≈ 0.90 (high voxel-ROI correlation)
  - Randomized: r ≈ 0.0-0.2 (low correlation)
  - Drop: > 0.5 ✓
- **FIR shape**:
  - Original: Convex (score = 2.0)
  - Randomized: Random/flat (score ≈ 0.0-0.5)
- **Interpretation**: High correlations are REAL, temporal structure destroyed by randomization ✓

**Drift contamination present**:
- **HRF correlation**:
  - Original: r ≈ 0.90
  - Randomized: r ≈ 0.85 (still high!)
  - Drop: < 0.1 ⚠
- **FIR shape**:
  - Original: Linear ramp (score = 0.0)
  - Randomized: Linear ramp persists (score = 0.0)
- **Interpretation**: High correlations persist → drift artifact, not real signal ⚠

### Outputs

```
derivatives/onset_validation/sub-01/
├── V1/
│   ├── onset_validation.json       # Classifications and scores
│   ├── onset_validation.png        # 3-panel visualization
│   │
│   # Original onset HRF
│   ├── original/
│   │   ├── roi_hrf.npy
│   │   ├── voxel_hrfs.npy
│   │   ├── hrf_correlations.npy
│   │   ├── hrf_variability.png     # 6-panel HRF analysis
│   │   ├── fir_quality.json        # Convexity score, shape type
│   │   └── metrics.json
│   │
│   # Randomized onset HRFs (5 seeds: 42, 43, 44, 45, 46)
│   ├── random_seed42/
│   │   ├── (same structure as original)
│   ├── random_seed43/
│   ├── random_seed44/
│   ├── random_seed45/
│   └── random_seed46/
│
└── V2/ (same structure)
```

### Visualization

**onset_validation.png** (2×3 grid, 6 panels):

**Top row** (Main validation metrics):
1. **ROI HRF comparison**: Original (red) vs 5 randomized (gray) FIRs
2. **HRF correlation distributions** (KEY METRIC): Original (red, high) vs randomized (gray, low) histograms
3. **HRF correlation boxplot**: Mean correlation comparison with drop quantified

**Bottom row** (Supporting metrics):
4. **FIR shape distribution**: Bar chart of convex/linear_ramp/random counts
5. **Convexity score comparison**: Boxplot showing original vs randomized scores
6. **Validation summary**: Overall interpretation with color-coded result (green=pass, yellow=warning)

---

## Usage

### Option 1: Interactive Mode (RECOMMENDED)

```bash
# SSH to server
ssh haba6030@node2

# Request interactive session
srun --nodelist=node2 --qos=shared --cpus-per-task=4 --mem=32G --time=4:00:00 --pty bash

# Activate environment
source ~/.bashrc
conda activate nilearn

# Navigate to analysis directory
cd /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding

# Run drift validation
python validate_drift_removal.py --subject 01 --roi V1
python validate_drift_removal.py --subject 01 --roi V2

# Run onset randomization validation
python validate_onset_randomization.py --subject 01 --roi V1 --n-seeds 5
python validate_onset_randomization.py --subject 01 --roi V2 --n-seeds 5
```

### Option 2: Batch Mode

```bash
# Create logs directory
mkdir -p logs

# Submit jobs
sbatch validate_drift_removal.sbatch
sbatch validate_onset_randomization.sbatch

# Monitor jobs
squeue -u haba6030

# Check logs
tail -f logs/drift_val_*.out
tail -f logs/onset_val_*.out
```

---

## Upload to Server

**From local machine**:

```bash
# Combined upload (efficient - uses wildcards)
scp validate_drift_removal.py validate_drift_removal.sbatch validate_onset_randomization.py validate_onset_randomization.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/
```

---

## Download Results

**After completion**:

```bash
# Download validation results
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/drift_validation ./
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/onset_validation ./

# Check outputs
ls drift_validation/sub-01/V1/*.json
ls drift_validation/sub-01/V1/*.png
ls onset_validation/sub-01/V1/*.json
ls onset_validation/sub-01/V1/*.png
```

---

## Interpretation Guide

### Drift Comparison Results

**If 1st+2nd drift is better**:
- HRF correlation increases (e.g., 0.85 → 0.90)
- RDM reliability improves
- **Action**: Adopt 1st+2nd drift for main pipeline

**If 2nd-only drift is sufficient**:
- HRF correlation unchanged (e.g., 0.90 → 0.90)
- RDM reliability similar
- **Action**: Keep current 2nd-only drift

### Onset Randomization Results

**PRIMARY DECISION METRIC: HRF Correlation Drop**

**If FIR is robust (EXPECTED)**:
- **HRF correlation drop > 0.5** (e.g., 0.90 → 0.20)
  - Original has high voxel-ROI correlations
  - Randomization destroys correlations
  - **Interpretation**: High correlations are REAL temporal structure ✓
- **FIR shape**: Convex → Random/flat (supporting evidence)
- **Conclusion**: Current pipeline validated, no drift contamination ✓

**If drift contamination exists (UNEXPECTED)**:
- **HRF correlation drop < 0.1** (e.g., 0.90 → 0.85)
  - Original has high voxel-ROI correlations
  - Randomization does NOT destroy correlations
  - **Interpretation**: High correlations are drift artifact ⚠
- **FIR shape**: Linear ramp persists (supporting evidence)
- **Conclusion**: Drift contamination present ⚠
- **Action**:
  1. Review drift removal methodology
  2. Consider adding drift to 1st level (FIR estimation)
  3. Test 1st+2nd order drift (from drift validation results)

---

## Memory Requirements

**Actual memory usage** (tested with sub-01 V1): **3.2 GB**

**Optimized configuration**:
- `--mem=8G` (2.5x headroom over actual usage)
- `--cpus-per-task=4` (97% CPU utilization achieved)

**Test results**:
```bash
/usr/bin/time -v python validate_drift_removal.py --subject 01 --roi V1
# Maximum resident set size (kbytes): 3239688 (~3.2 GB)
# Elapsed time: 2:18
# Percent of CPU: 97%
```

---

## Expected Runtime

**Actual tested performance (sub-01 V1)**:
- Drift validation: **2:18** (2 methods × 6 runs × 2 levels)
- Onset randomization: **~14 min** (estimated: 6 conditions × 2:18)

**Total runtime for V1 + V2**: **~35 minutes**
- Drift validation: ~5 min (2.3 min × 2 ROIs)
- Onset randomization: ~28 min (14 min × 2 ROIs)
- Buffer: ~2 min

**SLURM time limits** (with safety margin):
- Drift validation: 30 min (6.5x headroom)
- Onset randomization: 1 hour (2x headroom)

---

## Key Differences from Main Pipeline

1. **Drift comparison**: Adds 1st-order (quadratic) drift regressors
2. **Onset randomization**: Shuffles trial onsets before FIR estimation
3. **FIR shape classification**: New convexity scoring function
4. **Test scope**: Only sub-01, V1 and V2 (quick validation)

---

## Next Steps

1. **Run validations** on server (interactive mode recommended)
2. **Download results** and inspect visualizations
3. **Interpret findings**:
   - If 2nd-only sufficient + FIR robust → Current pipeline validated ✓
   - If 1st+2nd better → Update main pipeline
   - If drift contamination → Investigate deeper

4. **Document conclusions** in main pipeline README
5. **Decide**: Keep C010 as-is or modify drift removal

---

## Files Created

**Python scripts**:
- `validate_drift_removal.py` (~900 lines)
- `validate_onset_randomization.py` (~800 lines)

**SLURM batch files**:
- `validate_drift_removal.sbatch`
- `validate_onset_randomization.sbatch`

**Documentation**:
- `DRIFT_VALIDATION_README.md` (this file)

---

## Contact

For questions or issues:
1. Check logs in `logs/drift_val_*.out` and `logs/onset_val_*.out`
2. Review error messages in `logs/*_val_*.err`
3. Verify data paths and file permissions
4. Check memory usage if OOM errors occur

---

**Last updated**: 2026-02-16
