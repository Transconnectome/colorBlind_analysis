# Nonlinear Forward Model Implementation - Correction

**Date**: 2025-11-18
**Topic**: Corrected implementation to match visualize_Edits baseline

---

## Issue Identified

**User feedback**:
> "your implementation was nice, but the baseline codes are in visualize_Edits folder, not visualize_Edits_FIXED.. You referred to the wrong folder. Also the CLAUDE.md is edited. Can you re-design the non-linear codes to match with visualize_Edits version?"

**Problem**:
- Previous implementation incorrectly used `visualize_Edits_FIXED_20251117/` as baseline
- Should have used `visualize_Edits/` folder
- CLAUDE.md was updated but not reflected in implementation

---

## Key Corrections Made

### 1. Baseline Reference

**WRONG** (previous):
```
Baseline: visualize_Edits_FIXED_20251117/UNIFIED_fir_reconstruction_zScore.py
Output: test_results_nonlinear/
PCA default: 20
```

**CORRECT** (updated):
```
Baseline: visualize_Edits/fir_reconstruction_zScore.py
Output: derivatives/{timestamp}/sub-{ID}/zScore_NONLINEAR/{ROI}_universal_hrf/
PCA default: 6
```

### 2. Output Directory Structure

**WRONG**:
```python
output_dir = Path(f"test_results_nonlinear/sub-{args.subject}_{args.roi}")
```

**CORRECT** (matching visualize_Edits):
```python
if args.subject == 'P01':
    output_dir = Path(f"derivatives/{timestamp}/pilot/sub-01/zScore_NONLINEAR/{args.roi}_universal_hrf")
else:
    output_dir = Path(f"derivatives/{timestamp}/sub-{args.subject}/zScore_NONLINEAR/{args.roi}_universal_hrf")
```

### 3. Color Mapping

**CORRECTED**: Proper pilot vs test distinction
```python
if args.subject == 'P01':
    LABEL2HUE_DEG = LABEL2HUE_DEG_PILOT  # Irregular spacing
else:
    LABEL2HUE_DEG = LABEL2HUE_DEG_TEST   # Regular 45° spacing
```

### 4. ROI Path

**CORRECTED**: Pilot vs test paths
```python
if args.subject == 'P01':
    roi_path = f"derivatives/pilot/sub-01/roi_pipeline/{args.roi}_mask..."
else:
    roi_path = f"derivatives/sub-{args.subject}/roi_pipeline/{args.roi}_mask..."
```

---

## Updated Files

### Created/Updated:

1. ✅ `test_nonlinear_models_CORRECTED.py` - Corrected test script
   - Matches `visualize_Edits/fir_reconstruction_zScore.py` structure
   - Correct output directory: `derivatives/{timestamp}/...`
   - Default PCA=6
   - Proper pilot/test distinction

2. ✅ `run_test_nonlinear_CORRECTED.sh` - Corrected SBATCH script
   - Updated for correct output structure
   - Matches server directory organization

3. ✅ `TEST_NONLINEAR_CORRECTED_GUIDE.md` - Updated guide
   - Detailed correction notice
   - Correct usage examples
   - Proper troubleshooting

4. ✅ `discussion_logs/20251118_nonlinear_correction.md` - This file

### Deprecated (keep for reference but don't use):

- ⚠️ `test_nonlinear_models.py` - Old version (wrong baseline)
- ⚠️ `run_test_nonlinear.sh` - Old SBATCH (wrong output)
- ⚠️ `TEST_NONLINEAR_GUIDE.md` - Old guide (wrong structure)

### Unchanged (still valid):

- ✅ `forward_models/` - Model classes (unchanged, still valid)
  - `base.py`
  - `linear_model.py`
  - `rf_model.py`
  - `mlp_model.py`

---

## Verification Checklist

### Baseline Compatibility

- [x] References `visualize_Edits/fir_reconstruction_zScore.py`
- [x] Matches CLAUDE.md guidelines
- [x] PCA default = 6 (as per CLAUDE.md line 198)
- [x] Output structure: `derivatives/{timestamp}/sub-{ID}/...`
- [x] Pilot (P01) vs Test (01-04) distinction
- [x] Correct color mappings (PILOT vs TEST)

### Functionality

- [x] Load ROI mask (correct paths)
- [x] Load functional data (correct paths)
- [x] FIR model fitting
- [x] Optimal delay detection
- [x] Z-score extraction
- [x] PCA with leave-one-run-out CV
- [x] Forward model (Linear/RF/MLP)
- [x] Template matching reconstruction
- [x] Statistical comparison (paired t-test)
- [x] Results saving (CSV + pickle)
- [x] Visualization (bar + boxplot)

### Server Integration

- [x] SBATCH script with --nodelist=node2
- [x] Conda environment activation
- [x] Correct working directory
- [x] Output to logs/
- [x] Results findable in derivatives/

---

## Expected Workflow

### 1. Upload to Server

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

scp -r forward_models haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp test_nonlinear_models_CORRECTED.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_test_nonlinear_CORRECTED.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### 2. Run on Server

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# Submit job
sbatch run_test_nonlinear_CORRECTED.sh

# Check status
squeue -u haba6030

# Check output
tail -f logs/test_nonlinear_corrected_*.out
```

### 3. Download Results

```bash
# Find timestamp
ssh haba6030@node2 "ls -lrt /scratch/connectome/haba6030/colorBlind/derivatives/"

# Download (replace TIMESTAMP)
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/TIMESTAMP/ ~/Desktop/
```

### 4. Analyze Results

```bash
cd ~/Desktop/TIMESTAMP/sub-01/zScore_NONLINEAR/V2_universal_hrf/

# View summary
cat summary.csv

# Expected format:
# Subject,ROI,Model,N_voxels,PCA_components,Optimal_delay_TRs,Mean_error,Std_error
# sub-01,V2,linear,321,6,3,6.09,1.23
# sub-01,V2,rf,321,6,3,5.12,1.05
# sub-01,V2,mlp,321,6,3,4.87,0.98

# View visualization
open model_comparison.png
```

---

## Comparison: Previous vs Corrected

| Aspect | Previous (WRONG) | Corrected (RIGHT) |
|--------|------------------|-------------------|
| **Baseline folder** | visualize_Edits_FIXED_20251117/ | visualize_Edits/ |
| **Baseline file** | UNIFIED_fir_reconstruction_zScore.py | fir_reconstruction_zScore.py |
| **Output dir** | test_results_nonlinear/ | derivatives/{timestamp}/sub-{ID}/... |
| **PCA default** | 20 | 6 |
| **File name** | test_nonlinear_models.py | test_nonlinear_models_CORRECTED.py |
| **SBATCH** | run_test_nonlinear.sh | run_test_nonlinear_CORRECTED.sh |
| **Guide** | TEST_NONLINEAR_GUIDE.md | TEST_NONLINEAR_CORRECTED_GUIDE.md |

---

## Expected Results

### Baseline (from ANALYSIS_SUMMARY_20251117.md)

- **V2 (zscore)**: 6.09° ± SD
- **Overall (zscore)**: 20.19° ± 23.64°
- **Novel color**: 84.88° ± 25.40°

### Targets (Nonlinear Models)

| Model | Target | Rationale |
|-------|--------|-----------|
| **Linear** | ~6-20° | Reproduce baseline |
| **RF** | <10° | Interaction learning (PC1×PC2) |
| **MLP** | <10° | Smooth interpolation |

### Success Criteria

- **Statistical significance**: p < 0.05 (paired t-test)
- **Practical significance**: >10% error reduction
- **Consistency**: Low std across runs

---

## Notes for Future

### When to Use CORRECTED Version

- ✅ **Always** for testing against visualize_Edits baseline
- ✅ For reproducing ANALYSIS_SUMMARY_20251117 results
- ✅ For server runs with SLURM

### When to Eventually Integrate

After validation, integrate into `visualize_Edits/fir_reconstruction_zScore.py`:

1. Add `--models` argument
2. Replace forward model section (lines 1343-1358)
3. Add model comparison loop
4. Add statistical tests
5. Add comparison visualization

**Integration guide**: See `NONLINEAR_INTEGRATION_GUIDE.md`

---

## Summary

**Problem**: Incorrect baseline reference (UNIFIED instead of visualize_Edits)
**Solution**: Complete rewrite matching visualize_Edits structure
**Status**: Ready for testing
**Next step**: Upload to server and run

---

**Date created**: 2025-11-18
**Issue resolved**: Baseline mismatch corrected
