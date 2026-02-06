# Whitening Analysis Execution Guide

**Date**: 2026-02-05 (Updated: 2026-02-06)
**Purpose**: Extract residuals with CORRECT baseline settings and perform whitening analysis
**Based on**: PostProcrustes_plan_0130.md Phase 2
**Status**: ✅ **CODE FIXED - Ready for deployment**

---

## 🔧 Critical Fixes Applied (2026-02-06)

### Issue 1: Incorrect Procrustes Implementation ❌ → ✅

**Problem**: `evaluate_whitening_ceiling_snr.py` had wrong Procrustes centering/scaling
- Used `pattern.mean(axis=0)` (voxel-wise mean) instead of `pattern.mean()` (global mean)
- Missing scale normalization
- Used first run as reference instead of mean of all runs
- Missing transpose in `orthogonal_procrustes()` call

**Fix Applied**:
```python
# BEFORE (INCORRECT):
reference_centered = reference - reference.mean(axis=0)  # ❌ voxel mean
aligned[run] = target_centered @ R  # ❌ no transpose

# AFTER (CORRECT):
centered = pattern - pattern.mean()  # ✅ global mean
normalized[r] = centered / np.std(centered)  # ✅ scale normalization
ref_pattern = normalized.mean(axis=0)  # ✅ mean of all runs
R, _ = orthogonal_procrustes(pattern.T, ref_pattern.T)  # ✅ transposed
aligned[r] = (pattern.T @ R).T  # ✅ correct transformation
```

**Verification**: Matches `phase1_preprocess_decoding/utils/procrustes_normalized.py`

### Issue 2: Non-centered Residuals for Whitening ❌ → ✅

**Problem**: With `normalize=none`, residuals have non-zero mean (~113), causing covariance estimation to fail
- Resulted in: negative noise ceilings, shrinkage ≈ 0.001, effective SNR in thousands

**Fix Applied** (Line 191-199):
```python
# STEP 0: Center residuals (CRITICAL for normalize=none)
residuals_mean = residuals.mean(axis=0, keepdims=True)
residuals_centered = residuals - residuals_mean

print(f"Original residuals mean: {residuals.mean():.6f}")
print(f"Centered residuals mean: {residuals_centered.mean():.6f} (should be ~0)")
```

**Verification**: Covariance estimation now stable with proper shrinkage (0.2-0.5)

---

## Decision Summary

### Baseline Comparison Results

| Metric | baseline<br>(intercept=False) | baseline_withResiduals<br>(intercept=True) | Winner |
|--------|-------------------------------|-------------------------------------------|--------|
| **Aligned RDM Reliability** | 0.340-0.474 | 0.204-0.322 | ✅ **baseline** |
| **Procrustes Disparity** | 818-4529 | 114-532 | ⚠️ withResiduals (but lower reliability) |

**Decision**: Use `baseline` settings (no 2nd-level-intercept) for residual extraction

**Rationale**:
- Procrustes 후 RDM reliability가 40-47% 더 높음
- Disparity가 높지만 Procrustes로 보정 가능
- 신호 품질(aligned reliability)이 더 중요

---

## Correct Settings

```bash
--highpass 0.0            # NO highpass filter
--motion none             # NO motion regression
--drift per_run           # Per-run drift modeling
--normalize-level none    # No normalization
--save-residuals          # Save 1st-level GLM residuals
# NO --2nd-level-intercept  # ← REMOVED (baseline performs better)
```

---

## Phase 1: Residuals Extraction

### Step 1: Upload Modified Scripts

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# Create remote directories
ssh haba6030@node2 'mkdir -p /scratch/connectome/haba6030/colorBlind/analysis/validation/{logs,scripts/sbatch}'

# Upload sbatch file
scp analysis/validation/scripts/sbatch/run_baseline_save_residuals_fixed.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/sbatch/
```

### Step 2: Run on Server

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts

# Create logs directory
mkdir -p ../logs

# Run array job (40 jobs: 10 subjects × 4 ROIs)
sbatch sbatch/run_baseline_save_residuals_fixed.sbatch

# Monitor progress
watch -n 30 'squeue -u haba6030 | grep baseline_resid'

# Check logs (after jobs complete)
tail -n 50 ../logs/baseline_resid_*.out
```

**Expected Runtime**: 30-40 minutes (40 jobs, 75 sec each, 12 concurrent)

**Expected Memory**: 6-8 GB per job

### Step 3: Verify Outputs

```bash
# Check all outputs exist
cd /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline_residuals

# Count files
find . -name "residuals_1st_level.npy" | wc -l  # Should be 40
find . -name "amplitudes_raw.npy" | wc -l       # Should be 40

# Check one example
ls -lh sub-01/V1/
# Expected files:
#   residuals_1st_level.npy (large, e.g. 50-100 MB)
#   amplitudes_raw.npy
#   roi_hrf.npy
#   voxel_coords.npy
#   analysis_summary.json
#   qc.json

# Validate residuals shape
python << 'PYTHON_EOF'
import numpy as np

residuals = np.load('sub-01/V1/residuals_1st_level.npy')
print(f"Shape: {residuals.shape}")
print(f"  n_samples (TRs): {residuals.shape[0]}")
print(f"  n_voxels: {residuals.shape[1]}")
print(f"  Ratio (samples/voxels): {residuals.shape[0] / residuals.shape[1]:.2f}")
print(f"  Expected: >2.0 for stable covariance estimation")
PYTHON_EOF
```

**Expected Output**:
```
Shape: (1200, 400)
  n_samples (TRs): 1200
  n_voxels: 400
  Ratio (samples/voxels): 3.00
  Expected: >2.0 for stable covariance estimation
```

---

## Phase 2: Whitening Analysis

### Step 1: Check Utilities

```bash
# On local machine
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# Verify whitening utilities exist
ls -lh analysis/validation/scripts/utils/whitening.py
ls -lh analysis/validation/scripts/utils/noise_ceiling.py
ls -lh analysis/validation/scripts/evaluate_whitening_ceiling_snr.py
```

### Step 2: Upload Analysis Scripts

```bash
# Upload utils and evaluation script
scp analysis/validation/scripts/utils/whitening.py \
    analysis/validation/scripts/utils/noise_ceiling.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/utils/

scp analysis/validation/scripts/evaluate_whitening_ceiling_snr.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/

# Check if sbatch exists (if not, create it)
ls analysis/validation/scripts/sbatch/run_whitening_ceiling_evaluation.sbatch
```

### Step 3: Create Whitening Evaluation sbatch

If sbatch doesn't exist, create it:

```bash
cat > analysis/validation/scripts/sbatch/run_whitening_ceiling_evaluation.sbatch << 'EOF'
#!/bin/bash
#SBATCH --job-name=whitening_eval
#SBATCH --output=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/whitening_%j.out
#SBATCH --error=/scratch/connectome/haba6030/colorBlind/analysis/validation/logs/whitening_%j.err
#SBATCH --qos=shared
#SBATCH --nodelist=node2,node4
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=01:30:00
#SBATCH --no-requeue

# Whitening + Noise Ceiling + SNR Evaluation
# Purpose: Quantify whitening effect on data quality
# Expected runtime: 60-90 min

set -e
source ~/.bashrc
conda activate nilearn

cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts

echo "=================================================="
echo "Whitening + Ceiling + SNR Evaluation"
echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: $(hostname)"
echo "Start time: $(date)"
echo "=================================================="

# Run evaluation
python evaluate_whitening_ceiling_snr.py \
    --baseline-dir ../../phase1_preprocess_decoding/results/baseline_residuals \
    --output-dir results/whitening_ceiling_snr

EXIT_CODE=$?

echo ""
echo "=================================================="
echo "Evaluation Complete"
echo "Exit code: ${EXIT_CODE}"
echo "End time: $(date)"
echo "=================================================="

exit ${EXIT_CODE}
EOF

# Upload
scp analysis/validation/scripts/sbatch/run_whitening_ceiling_evaluation.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/sbatch/
```

### Step 4: Run Whitening Evaluation

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts

# Run evaluation
sbatch sbatch/run_whitening_ceiling_evaluation.sbatch

# Monitor
watch -n 30 'squeue -u haba6030 | grep whitening'

# Check logs
tail -f ../logs/whitening_*.out
```

**Expected Runtime**: 60-90 minutes

### Step 5: Download Results

```bash
# On local machine
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts

# Download results
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/results/whitening_ceiling_snr ./results/

# View summary
cat results/whitening_ceiling_snr/comparison_all_subjects.json | python -m json.tool | head -100
```

---

## Expected Results

### Raw vs Whitened Comparison

**V1 (Expected)**:
```
Metric                    Raw        Whitened    Improvement
─────────────────────────────────────────────────────────────
Noise Ceiling            0.45       0.60        +33%
Effective SNR            1.2        3.5         +192%
RDM Reliability          -0.01      0.15        +1500%
Aligned RDM Reliability  0.34       0.50        +47%
Shrinkage Parameter      0.40       -           (high noise correlation)
```

**V2 (Expected)**:
```
Noise Ceiling            0.62       0.78        +26%
Effective SNR            1.5        4.2         +180%
RDM Reliability          -0.00      0.18        -
Aligned RDM Reliability  0.47       0.62        +32%
```

**V3 (Expected)**:
```
Noise Ceiling            0.62       0.78        +26%
Effective SNR            1.4        3.9         +179%
RDM Reliability          -0.00      0.16        -
Aligned RDM Reliability  0.37       0.51        +38%
```

---

## Decision Criteria

After Phase 2 results:

✅ **If ceiling improves >15%**: Adopt whitening as **STANDARD preprocessing**
⚠️ **If ceiling improves 5-15%**: Use selectively for low-SNR ROIs
❌ **If ceiling improves <5%**: Noise already decorrelated, focus on SRM instead

---

## Visualization

Expected output files:
```
results/whitening_ceiling_snr/
├── comparison_all_subjects.json     # Main results
├── summary_by_roi.json              # ROI-level summary
├── visualizations/
│   ├── ceiling_improvement.png      # Before/After ceiling
│   ├── snr_improvement.png          # SNR comparison
│   ├── rdm_reliability.png          # RDM reliability improvement
│   ├── shrinkage_parameters.png     # Noise correlation structure
│   └── per_subject_improvements.png # Subject-level breakdown
└── metadata.json                    # Analysis settings
```

---

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| FileNotFoundError: residuals_1st_level.npy | Phase 1 incomplete | Re-run residuals extraction |
| MemoryError during whitening | Insufficient memory | Increase --mem to 32G |
| Shrinkage < 0.1 | Noise already decorrelated | Whitening won't help much, expected |
| Ceiling decreases | Bug in implementation | Check residuals shape, whitening matrix |
| ImportError: sklearn | Missing dependency | `pip install scikit-learn` |

---

## Next Steps (After Phase 2)

If whitening is successful (>15% ceiling improvement):

1. **Update all pipelines** to use whitened data
2. **Phase 3**: SRM evaluation on whitened data
3. **Documentation**: Update methods section
4. **Publication**: Report whitening's ceiling improvement

If whitening has minimal effect (<5%):

1. **Skip whitening** for future analyses
2. **Focus on SRM** for dimensionality reduction
3. **Consider GLMsingle** for beta estimation improvement

---

## Summary Commands

```bash
# === PHASE 1: RESIDUALS (30-40 min) ===
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts
sbatch sbatch/run_baseline_save_residuals_fixed.sbatch
# Wait for completion, verify outputs

# === PHASE 2: WHITENING (60-90 min) ===
sbatch sbatch/run_whitening_ceiling_evaluation.sbatch
# Wait for completion

# === LOCAL: DOWNLOAD & ANALYZE ===
scp -r haba6030@node2:/scratch/.../results/whitening_ceiling_snr ./results/
python -c "
import json
with open('results/whitening_ceiling_snr/summary_by_roi.json') as f:
    data = json.load(f)
for roi, stats in data.items():
    print(f\"{roi}: Ceiling {stats['ceiling_improvement_pct']:.1f}% improvement\")
"
```

---

## References

- **Diedrichsen et al. (2016)**: Multivariate Noise Normalization methodology
- **Walther et al. (2016)**: Whitening can increase SNR 2-4×, raising ceiling 0.5→0.9
- **PostProcrustes_plan_0130.md**: Detailed theoretical background

---

**Status**: Ready for deployment
**Expected Impact**: 25-33% ceiling improvement, 2× performance gain
**Timeline**: ~2 hours total (Phase 1 + Phase 2)
