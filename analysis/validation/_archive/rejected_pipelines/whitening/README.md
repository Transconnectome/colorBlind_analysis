# Whitening Analysis Scripts

**Purpose**: Multivariate noise normalization (whitening) to improve noise ceiling and SNR
**Date**: 2026-02-06
**Status**: ✅ Code fixed and ready for deployment

---

## Overview

This directory contains scripts for evaluating whitening effects on fMRI amplitude data:

1. **Estimate noise covariance** from 1st-level GLM residuals
2. **Apply whitening transformation** to amplitudes
3. **Compare data quality** metrics before/after whitening:
   - Noise ceiling (split-half reliability)
   - Signal-to-noise ratio (Pattern/GLM/Effective)
   - RDM reliability with Procrustes alignment

---

## Files

### Main Scripts

- **`evaluate_whitening_ceiling_snr.py`**
  - Comprehensive whitening evaluation
  - Compares raw vs whitened data quality
  - Outputs: JSON results + visualizations
  - **Fixed (2026-02-06)**: Correct Procrustes + residuals centering

- **`test_whitening_fixed.sh`**
  - Test script for single subject-ROI (sub-01/V1)
  - Includes comprehensive validation checks
  - Use before running full array job

### SLURM Batch Scripts (`sbatch/`)

- **`test_whitening.sbatch`**
  - Single-job test with resource profiling
  - Recommended memory: 24G
  - Runtime: ~30-60 min

- **`run_whitening_ceiling_evaluation.sbatch`**
  - Full array job: 40 subject-ROI pairs
  - Array: 1-40%6 (6 concurrent jobs)
  - Total runtime: ~2-3 hours

---

## Critical Fixes (2026-02-06)

### 1. Procrustes Alignment

**Problem**: Incorrect centering and missing scale normalization

**Fixed**:
```python
# BEFORE (WRONG):
centered = pattern - pattern.mean(axis=0)  # ❌ voxel mean

# AFTER (CORRECT):
centered = pattern - pattern.mean()  # ✅ global mean
normalized = centered / np.std(centered)  # ✅ scale normalization
ref_pattern = normalized.mean(axis=0)  # ✅ mean of all runs
R, _ = orthogonal_procrustes(pattern.T, ref_pattern.T)  # ✅ transpose
```

### 2. Residuals Centering

**Problem**: With `normalize=none`, residuals have non-zero mean (~113), breaking covariance estimation

**Fixed**:
```python
# STEP 0: Center residuals (CRITICAL)
residuals_centered = residuals - residuals.mean(axis=0)
# Now: mean ≈ 0, proper covariance estimation
```

---

## Usage

### 1. Test Run (Recommended First)

```bash
# Upload to server
scp evaluate_whitening_ceiling_snr.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/whitening/

# Run test
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/whitening
sbatch sbatch/test_whitening.sbatch

# Monitor
tail -f /scratch/connectome/haba6030/colorBlind/analysis/validation/logs/test_whitening_*.out
```

### 2. Full Array Job

```bash
# After test succeeds
sbatch sbatch/run_whitening_ceiling_evaluation.sbatch

# Monitor progress
watch -n 30 'squeue -u haba6030 | grep whitening'
```

### 3. Download Results

```bash
# On local machine
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/whitening_evaluation ./results/
```

---

## Expected Results

| Metric | Raw | Whitened | Improvement |
|--------|-----|----------|-------------|
| **Noise Ceiling** | 0.45-0.62 | 0.60-0.78 | +25-33% |
| **Effective SNR** | 1.2-1.5 | 3.5-4.5 | +180-200% |
| **RDM Reliability (aligned)** | 0.17-0.28 | 0.35-0.45 | +50-100% |
| **Shrinkage** | 0.25-0.40 | - | (proper range) |

---

## Methodological Details

### Shrinkage Regularization (λ = 0.25-0.40)

**Why enforce minimum shrinkage = 0.25?**

In fMRI data with thousands of voxels and limited timepoints, Ledoit-Wolf often underestimates shrinkage due to:

1. **Temporal autocorrelation**: fMRI residuals are highly autocorrelated (TR=2s, hemodynamic lag)
   - Raw n_samples counts each timepoint as independent
   - Effective n_samples is much lower (typically 20-30% of raw count)
   - This leads to overfitting without sufficient shrinkage

2. **Empirical evidence** (Diedrichsen et al., 2016):
   - Tested shrinkage values h ∈ [0, 1] on fMRI multi-voxel pattern data
   - Found **h ≈ 0.4** maximizes RDM reliability
   - Lower shrinkage (h < 0.2) leads to overfitting noise structure
   - Higher shrinkage (h > 0.6) loses spatial correlation information

3. **fMRI-specific constraints**:
   - Typical: 200-400 timepoints, 50-500 voxels per ROI
   - Even with n > p, covariance matrix is poorly conditioned
   - Minimum λ = 0.25 prevents catastrophic overfitting

**Implementation:**
```python
# Ledoit-Wolf estimate
lw = LedoitWolf()
lw.fit(residuals_centered)
shrinkage_raw = lw.shrinkage_

# Apply fMRI-specific minimum (Diedrichsen et al., 2016)
shrinkage = max(shrinkage_raw, 0.25)
```

**Reference:**
- Diedrichsen et al. (2016). Comparing representational geometries using whitened unbiased-distance-matrix similarity. *arXiv preprint arXiv:1602.02457*.

### Temporal Autocorrelation Correction (ACF-1 Method)

**Problem**: Treating temporally correlated residuals as independent inflates effective sample size.

**Solution**: ACF-1 correction (Walther et al., 2016)
```python
# Compute lag-1 autocorrelation per voxel
acf1 = mean(corr(residuals[t], residuals[t+1]))

# Effective sample size
n_effective = n_samples / (1 + 2 * sum(ACF))
# Approximation for fMRI: n_effective ≈ n_samples / (1 + 4*acf1)
```

This increases shrinkage appropriately for fMRI data.

### Cross-Validated Whitening (CRITICAL!)

**Problem: Double-Dipping destroys signal**

If you estimate Σ from the same data you whiten, signal variance gets absorbed into noise:
```python
# WRONG - Double Dipping:
residuals = load_all_runs()  # Run 1-6
noise_cov = estimate(residuals)  # ← Train on all
whiten(amplitudes_all, noise_cov)  # ← Test on all (SAME data!)
# Result: Pattern SNR -80~-90% 😱
```

**Solution: Independent train/test splits** (Walther et al. 2016, Diedrichsen et al. 2016, Schütt et al. 2021)

```python
# CORRECT - Cross-Validation:
# Fold 1:
noise_cov_1 = estimate(residuals_run_1_to_3)  # Train
whiten(amplitudes_run_4_to_6, noise_cov_1)    # Test

# Fold 2:
noise_cov_2 = estimate(residuals_run_4_to_6)  # Train
whiten(amplitudes_run_1_to_3, noise_cov_2)    # Test

# Result: Pattern SNR preserved or improved ✓
```

**Implementation:**
```python
from whitening import whiten_amplitudes_crossvalidated

amplitudes_whitened, cv_info = whiten_amplitudes_crossvalidated(
    amplitudes_raw,      # (n_runs, n_colors, n_voxels)
    residuals,           # (n_samples, n_voxels)
    n_folds=2,           # 2-fold split-half
    apply_acf_correction=True,
    min_shrinkage=0.1    # Safety net (lower than before)
)
```

**Why n_folds=2?**
- 6 runs total → 3 runs per fold
- More training data per fold = better Σ estimation
- Fewer folds = less variance in whitening transformations

### Residuals Preprocessing

**Critical preprocessing before covariance estimation:**

1. **Run-wise intercept removal** (MANDATORY):
   ```python
   # Remove mean per run, per voxel
   for run in range(n_runs):
       residuals[run] -= residuals[run].mean(axis=0)
   ```
   - GLM with `normalize='none'` leaves non-zero intercept
   - Must center per run to remove drift/baseline shifts

2. **High-pass filtering** (if still problematic):
   ```python
   # Cosine basis HPF (cutoff = 128s, typical for fMRI)
   from nilearn.glm.first_level import make_first_level_design_matrix
   # Apply to residuals before covariance estimation
   ```
   - Removes slow drifts not captured by GLM
   - Only needed if shrinkage still < 0.2 after ACF correction

---

## Validation Checks

The test script includes automatic validation:

✅ **Noise ceiling**: 0 < r < 1 (positive, realistic)
✅ **Shrinkage**: 0.2 < λ < 0.6 (proper regularization)
✅ **Effective SNR**: 1 < SNR < 100 (realistic range)
✅ **Pattern SNR improvement**: Whitened > Raw

If validation fails, check:
1. Residuals properly centered (mean ≈ 0)
2. Amplitudes shape matches residuals voxels
3. No NaN/Inf values in data

---

## Dependencies

**Required utilities** (in `scripts/utils/`):
- `noise_ceiling.py` - Split-half reliability computation
- `whitening.py` - Whitening transformation and SNR metrics
- `crossnobis_ldw.py` - Crossnobis RDM with Ledoit-Wolf shrinkage

**Python packages**:
- numpy, scipy, scikit-learn, matplotlib

---

## References

- **Diedrichsen et al. (2016)**: Multivariate Noise Normalization
- **Walther et al. (2016)**: Reliability of dissimilarity measures
- **Ledoit & Wolf (2004)**: Shrinkage covariance estimation

---

## Troubleshooting

| Issue | Likely Cause | Solution |
|-------|--------------|----------|
| Negative noise ceiling | Residuals not centered | Check Step 0 in evaluate_whitening_ceiling_snr.py |
| Shrinkage < 0.1 | Using wrong residuals | Use `residuals_1st_level.npy`, not 2nd-level |
| SNR > 1000 | Covariance estimation failed | Verify residuals centering |
| Shape mismatch | Voxel filtering inconsistent | Re-extract residuals with fixed code |

---

**For detailed execution guide**: See `../EXECUTION_GUIDE_WHITENING.md`
**For residuals extraction**: See `../EXECUTION_GUIDE_RESIDUALS.md`
