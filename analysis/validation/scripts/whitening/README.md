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
