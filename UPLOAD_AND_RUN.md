# Upload and Run Instructions

**Date:** 2025-01-23
**All bugs fixed, ready to test**

---

## Summary of All Fixes

### 1. ✅ Blank Stimulus Bug (CRITICAL)
- **All 3 files**: Exclude blank trials from FIR design matrix
- Blank now serves as implicit baseline

### 2. ✅ Drift Regression Bug (Grid Search)
- **grid_search_preprocessing.py**: Use full matrix for fitting, extract HRF part
- Drift properly regressed out now

### 3. ✅ Global Drift (BH2009)
- **Both BH2009 files**: Changed from per-run drift (12 params) to global drift (2 params)
- Matches grid search approach

### 4. ✅ Efficiency Optimization (BH2009)
- **Both BH2009 files**: Build design matrix once outside voxel loop
- Dramatic speed improvement

---

## Step 1: Upload Files to Server

```bash
# From local machine
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# Upload all 3 fixed files
scp grid_search_preprocessing.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp fir_reconstruction_BH2009_config26.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp fir_reconstruction_BH2009_smooth6mm.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# Verify upload
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# Check blank fix (should show color_events filter)
grep "color_events = events\[events\['trial_type'\]" grid_search_preprocessing.py
grep "color_events = events\[events\['trial_type'\]" fir_reconstruction_BH2009_config26.py
grep "color_events = events\[events\['trial_type'\]" fir_reconstruction_BH2009_smooth6mm.py

# Check drift fix (should show beta_full)
grep "beta_full = np.linalg.pinv(X_all)" grid_search_preprocessing.py

# Check global drift (should show run_idx=None)
grep "run_idx=None, n_runs=None" fir_reconstruction_BH2009_config26.py
grep "run_idx=None, n_runs=None" fir_reconstruction_BH2009_smooth6mm.py
```

---

## Step 2: Test with Single Subject First (RECOMMENDED)

**Purpose:** Quick validation before running all subjects

```bash
cd /scratch/connectome/haba6030/colorBlind

# Option A: Run both 6mm and 8mm for sub-01 V1
sbatch run_BH2009_single_subject.sbatch

# Before running, edit the sbatch file to set:
# SUBJECT="01"
# ROI="V1"
# SMOOTHING="both"  # Test both 6mm and 8mm
```

**Expected time:** ~30-60 minutes for both smoothing levels

**What to check in results:**

```bash
# After completion, check logs
tail -100 logs/BH2009_single_*.out

# Expected metrics (AFTER FIX):
# - HRF correlation: 0.90-0.96 (vs buggy 0.37-0.45)
# - Classification: 40-60% (vs buggy 4-10%)
# - Reconstruction error: 30-45° (vs buggy 85-94°)
# - R²: 0.3-0.5 (vs buggy 0.01)

# Check analysis summary
cat derivatives/BH2009_config26/sub-01_V1/analysis_summary.json
cat derivatives/BH2009_smooth6mm/sub-01_V1/analysis_summary.json
```

---

## Step 3: Re-run Grid Search (OPTIONAL but RECOMMENDED)

**Purpose:** Verify that preprocessing configs are correctly evaluated

```bash
cd /scratch/connectome/haba6030/colorBlind

# Clean old results
rm -f logs/grid_search_results.csv logs/best_config.json

# Submit job
sbatch --job-name=grid_fixed \
       --nodelist=node2 \
       --cpus-per-task=4 \
       --mem=16G \
       --time=04:00:00 \
       --output=logs/grid_search_fixed_%j.out \
       --error=logs/grid_search_fixed_%j.err \
       --wrap="source ~/.bashrc && conda activate nilearn && python grid_search_preprocessing.py"

# Monitor
tail -f logs/grid_search_fixed_*.out
```

**Expected time:** ~2-3 hours

**Expected changes in results:**

```bash
# After completion
head -1 logs/grid_search_results.csv && \
  awk -F',' 'NR>1{print $0}' logs/grid_search_results.csv | \
  sort -t',' -k11 -rn | head -10

# Expected metrics (AFTER FIX):
# - HRF correlation: 0.88-0.96 (vs buggy 0.9998 - inflated by drift)
# - R²: 0.3-0.5 (vs buggy nan)
# - More variation between configs (better discrimination)
# - Smoothing effect should be clearer
```

---

## Step 4: Run All Test Subjects (After Validation)

**Only after Step 2 shows good results!**

```bash
cd /scratch/connectome/haba6030/colorBlind

# Clean old results
rm -rf derivatives/BH2009_config26/sub-*/
rm -rf derivatives/BH2009_smooth6mm/sub-*/

# Submit job for all subjects
sbatch run_BH2009_all_subjects.sbatch
```

**Expected time:** ~4-6 hours (4 subjects × 2 smoothing × ~30min)

---

## Step 5: Download and Compare Results

```bash
# From local machine
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# Create results directory
mkdir -p results_fixed

# Download single subject test results
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/BH2009_config26/sub-01_V1 \
  results_fixed/sub-01_V1_8mm/

scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/BH2009_smooth6mm/sub-01_V1 \
  results_fixed/sub-01_V1_6mm/

# Download grid search results
scp haba6030@node2:/scratch/connectome/haba6030/colorBlind/logs/grid_search_results.csv \
  results_fixed/

# Check figures
open results_fixed/sub-01_V1_8mm/figures/
open results_fixed/sub-01_V1_6mm/figures/
```

---

## Expected Improvements

### Before Fix (Buggy):
```json
{
  "hrf_homogeneity": {
    "mean_correlation": 0.37-0.45,
    "explanation": "Blank contamination + heterogeneous drift"
  },
  "classification": {
    "accuracy": 0.04-0.10,
    "explanation": "Worse than chance (0.125)"
  },
  "reconstruction": {
    "mean_error_deg": 85-94,
    "explanation": "Barely better than chance (90°)"
  },
  "model_fit": {
    "r2_mean": 0.01,
    "explanation": "Terrible fit"
  }
}
```

### After Fix (Expected):
```json
{
  "hrf_homogeneity": {
    "mean_correlation": 0.90-0.96,
    "explanation": "Clean HRF, proper drift regression"
  },
  "classification": {
    "accuracy": 0.40-0.60,
    "explanation": "Matching B&H (2009) paper"
  },
  "reconstruction": {
    "mean_error_deg": 30-45,
    "explanation": "Matching B&H (2009) paper"
  },
  "model_fit": {
    "r2_mean": 0.3-0.5,
    "explanation": "Good fit"
  }
}
```

---

## Comparison: 6mm vs 8mm Smoothing

**From grid search (buggy results, but still informative):**
- 6mm: HRF corr = 0.997, tSNR = 59.5
- 8mm: HRF corr = 0.9998, tSNR = 89.5

**Expected after fix:**
- 6mm: Better spatial specificity, slightly lower SNR
- 8mm: Better SNR, slightly lower spatial specificity
- Both should perform well

**Recommendation:**
- Use 6mm as primary (matches literature standard)
- Keep 8mm as comparison

---

## Troubleshooting

### If results are still poor:

1. **Check blank filtering worked:**
   ```bash
   # In job output, should see reduced number of events
   grep "color events" logs/BH2009_*.out
   ```

2. **Check design matrix shape:**
   ```bash
   # Should show (1704, 10) = 8 FIR + 2 drift
   grep "Design matrix shape" logs/BH2009_*.out
   ```

3. **Check HRF estimation:**
   ```bash
   # Should show reasonable HRF peak at delay 3-4
   grep "Peak delay" logs/BH2009_*.out
   ```

4. **Verify events file:**
   ```bash
   head -20 /storage/connectome/haba6030/colorBlind_dataOct/sub-01/func/sub-01_task-rsvp_run-1_events.tsv
   # Should see mix of color_1-8 and blank
   ```

---

## Next Steps After Validation

1. ✅ If single subject results are good → Run all subjects
2. ✅ Compare 6mm vs 8mm → Choose best for final analysis
3. ✅ If grid search shows clear winners → Document optimal preprocessing
4. ✅ Write up results and compare with B&H (2009)

---

## Summary of Expected Timeline

```
Upload files:           5 min
Single subject test:    30-60 min
Grid search (optional): 2-3 hours
All subjects:           4-6 hours
Download & analysis:    30 min

Total (with grid):      7-10 hours
Total (without grid):   5-7 hours
```

**Recommendation:** Start with single subject test, validate results, then decide whether to run grid search before running all subjects.
