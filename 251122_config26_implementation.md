# Config 26 Implementation for BH2009 Pipeline

**Date:** 2025-01-22
**Purpose:** Apply best preprocessing settings from grid search to BH2009 universal HRF pipeline

---

## Executive Summary

Grid search identified **Config 26** as optimal preprocessing settings:
- **Spatial smoothing:** 8mm FWHM Gaussian kernel
- **Motion confounds:** 6 parameters (trans_x/y/z, rot_x/y/z)
- **High-pass filtering:** NONE (found to be detrimental)
- **Drift modeling:** Polynomial (constant + linear) in design matrix

**Key Grid Search Findings:**
- Config 26 achieved **HRF variability = 0.9998** (near-perfect voxel homogeneity)
- Temporal SNR: **89.5** (vs ~10 without preprocessing)
- High-pass filtering **reduces HRF correlation** from 0.968 → 0.045-0.087
- Smoothing is critical for HRF consistency across voxels

---

## Files Created

### 1. `fir_reconstruction_BH2009_config26.py`

Modified BH2009 pipeline with Config 26 preprocessing applied.

**Key Changes from Original:**

#### A. Data Loading (Lines 437-513)
```python
# After loading functional image and dropping volumes:

# === CONFIG 26: Spatial Smoothing ===
if SMOOTHING_FWHM > 0:
    func_img = nimg.smooth_img(func_img, fwhm=SMOOTHING_FWHM)

# Extract masked data
func_data = masker.transform(func_img)

# === CONFIG 26: Motion Confound Regression ===
if USE_MOTION_CONFOUNDS:
    confounds_path = f"{FMRIPREP_DIR}/func/{FILE_PREFIX}_task-rsvp_run-{run}_desc-confounds_timeseries.tsv"
    confounds = load_motion_confounds(confounds_path)

    # Drop first VOLS_TO_DROP rows from confounds
    if VOLS_TO_DROP > 0:
        confounds = confounds[VOLS_TO_DROP:, :]

    # Regress out motion
    func_data = regress_confounds(func_data, confounds)
```

#### B. New Helper Functions

**`load_motion_confounds(confounds_path)`** (Lines 107-127)
- Loads 6 motion parameters from fMRIPrep confounds TSV
- Columns: `trans_x, trans_y, trans_z, rot_x, rot_y, rot_z`
- Handles NaN values (fills with 0)

**`regress_confounds(data, confounds)`** (Lines 129-153)
- OLS regression: `data_clean = data - X @ pinv(X) @ data`
- Adds constant term automatically
- Returns cleaned data

#### C. Design Matrix (No Changes Needed)
- Original BH2009 already included drift regressors in `build_fir_design_matrix()`
- Polynomial drift (constant + linear) matches Config 26

#### D. NO High-Pass Filtering
- Grid search showed high-pass is **detrimental**
- Original BH2009 didn't use it either
- Config 26 confirmed this is correct

### 2. `run_BH2009_config26.sbatch`

SLURM batch script for running the analysis.

**Default Settings:**
- Subject: P01 (pilot)
- ROI: V1
- 4 CPUs, 16GB RAM, 4-hour time limit

**To Modify:**
```bash
# Edit these lines in the script
SUBJECT="P01"  # Change to "01", "02", "03", "04" for test subjects
ROI="V1"       # Change to "V2", "V3", "hV4" as needed
```

---

## Expected Results

### Comparison: Voxel-Specific vs Config 26 BH2009

| Metric | Voxel-Specific (No Preprocessing) | Config 26 BH2009 (Expected) |
|--------|-----------------------------------|------------------------------|
| **HRF Homogeneity** | Mean r = 0.066 (very low) | Mean r > 0.95 (high) |
| **Run-to-Run Reliability** | 0.84-0.96 (good) | 0.84-0.96 (maintain) |
| **Classification Accuracy** | 8-15% (failed) | **>50%** (target) |
| **Reconstruction Error** | ~90° (chance) | **<45°** (target) |
| **Amplitude SNR** | 0.16-0.27 (low) | **>1.0** (target) |

### Why Config 26 Should Improve Performance

#### 1. HRF Homogeneity → Better ROI Average
- Voxel-specific: Each voxel has different HRF shape (r = 0.066)
- Config 26: All voxels have similar HRF (r = 0.9998)
- **Result:** ROI average HRF is more representative

#### 2. Smoothing → Higher SNR
- Grid search showed temporal SNR: 89.5 (vs ~10 without smoothing)
- Smoothing reduces noise while preserving signal
- **Result:** Cleaner amplitude estimates

#### 3. Motion Regression → Less Confounding
- Motion artifacts can mimic color responses
- Regressing motion reduces false positives
- **Result:** More reliable amplitude patterns

#### 4. Maintained Reliability
- Voxel-specific already achieved high reliability (0.84-0.96)
- Config 26 maintains preprocessing across runs consistently
- **Result:** Reliability should remain high

### Why Voxel-Specific Failed Despite High Reliability

**Problem:** High reliability but low amplitude SNR

```
Run-to-run reliability = 0.96  ✓ Good
Amplitude SNR = 0.27           ✗ Too low (need >1.0)
```

**Explanation:**
- Reliability measures **consistency** of patterns across runs
- SNR measures **strength** of signal relative to noise
- You can have consistent patterns that are all weak (high reliability, low SNR)

**Analogy:**
- Like measuring the same faint signal 6 times and getting the same answer
- Measurements are **reliable** (consistent), but signal is still too weak to decode

**Why Config 26 Should Fix This:**
- Smoothing increases SNR by ~9× (from 10 to 89.5)
- Motion regression removes confounding variance
- **Expected:** High reliability + High SNR = Successful decoding

---

## How to Run

### Step 1: Upload Files to Server

```bash
# From local machine
scp fir_reconstruction_BH2009_config26.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_BH2009_config26.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### Step 2: Submit Job

```bash
# SSH to server
ssh haba6030@node2

# Navigate to directory
cd /scratch/connectome/haba6030/colorBlind

# Submit job
sbatch run_BH2009_config26.sbatch
```

### Step 3: Monitor Progress

```bash
# Check job status
squeue -u haba6030

# Watch output in real-time
tail -f logs/BH2009_config26_*.out

# Check for errors
tail -f logs/BH2009_config26_*.err
```

### Step 4: Download Results

```bash
# After job completes, download results from local machine
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/BH2009_config26 ./derivatives/
```

---

## Expected Runtime

Based on grid search timings:
- **Per configuration:** ~60-110 seconds
- **This pipeline:** ~2-3 minutes per ROI
- **Full analysis (1 subject, 1 ROI):** <5 minutes

---

## Output Structure

```
derivatives/BH2009_config26/
└── pilot/  (or sub-01/ for test subjects)
    └── TIMESTAMP_sub-01_V1/
        ├── analysis_summary.json      # All key metrics
        ├── roi_hrf.npy               # ROI average HRF
        ├── amplitudes_z.npy          # Z-scored amplitudes
        ├── selected_voxels_mask.npy  # Which voxels were selected
        └── figures/
            ├── roi_hrf.png
            └── ... (if visualization added)
```

### Key Metrics in `analysis_summary.json`

```json
{
  "preprocessing_config": "Config 26",
  "smoothing_fwhm": 8,
  "motion_confounds": true,
  "high_pass_filter": false,

  "hrf_correlation_mean": 0.95+,  // Target: >0.85
  "run_correlation_mean": 0.85+,  // Target: >0.7
  "classification_accuracy": 0.5+,  // Target: >50%
  "reconstruction_error": 45.0-,  // Target: <45°

  "r2_mean": 0.XX,
  "n_voxels_selected": XXX
}
```

---

## Success Criteria

### Minimum Success
- ✅ HRF correlation mean > 0.85 (Config 26 effect verified)
- ✅ Run-to-run reliability > 0.7 (maintained from voxel-specific)
- ✅ Classification accuracy > 25% (better than chance 12.5%)
- ✅ Reconstruction error < 70° (better than chance 90°)

### Good Success
- ✅ HRF correlation mean > 0.95 (matching grid search)
- ✅ Run-to-run reliability > 0.85
- ✅ Classification accuracy > 50%
- ✅ Reconstruction error < 45°

### Excellent Success
- ✅ HRF correlation mean > 0.98
- ✅ Run-to-run reliability > 0.90
- ✅ Classification accuracy > 70%
- ✅ Reconstruction error < 30°

---

## Troubleshooting

### Issue: HRF correlation still low (<0.8)

**Possible Causes:**
1. Smoothing not applied correctly
2. Motion confounds not loaded properly
3. ROI has inherent variability

**Diagnostics:**
```python
# Check if smoothing was applied
print(f"Smoothing FWHM: {SMOOTHING_FWHM}")  # Should be 8

# Check confounds shape
print(f"Confounds shape: {confounds.shape}")  # Should be (n_scans, 6)

# Check HRF correlation distribution
plt.hist(hrf_correlations, bins=30)
```

### Issue: Classification still at chance level

**Possible Causes:**
1. Amplitude SNR still too low
2. Too few voxels selected (R² threshold too high)
3. Colors not separable in this ROI

**Diagnostics:**
```python
# Check voxel SNR
voxel_snr = ...  # From analysis
print(f"Voxels with SNR > 1.0: {np.sum(voxel_snr > 1.0)}")

# Check number of voxels
print(f"Selected voxels: {n_voxels_selected}")  # Need >100

# Check per-color amplitudes
for color in range(8):
    print(f"Color {color}: mean={np.mean(amplitudes_raw[:, color, :]):.3f}")
```

### Issue: Job fails with memory error

**Solution:**
```bash
# Edit run_BH2009_config26.sbatch
#SBATCH --mem=32G  # Increase from 16G to 32G
```

---

## Next Steps After Results

### 1. Compare with Voxel-Specific

Create comparison table:

| Method | HRF Corr | Reliability | Classification | Reconstruction |
|--------|----------|-------------|----------------|----------------|
| Voxel-Specific | 0.066 | 0.96 | 8% | 90° |
| Config 26 BH2009 | ? | ? | ? | ? |

### 2. If Config 26 Succeeds

- Run on all ROIs (V1, V2, V3, hV4)
- Run on all subjects (P01, 01, 02, 03, 04)
- Analyze cross-subject consistency

### 3. If Config 26 Fails

Investigate further:
- Try different smoothing levels (6mm, 10mm)
- Try PCA with different component numbers
- Analyze which colors are confused most
- Check if specific runs are problematic

---

## Grid Search Results Reference

### All 36 Configurations Tested

**Best Configs (HRF corr > 0.99):**
- Config 26: smooth=8mm + motion_6 → **HRF corr = 0.9998** ⭐
- Config 27: smooth=8mm + motion_6 + demean → HRF corr = 0.9998
- Config 18: smooth=6mm + motion_6 → HRF corr = 0.9971
- Config 14: smooth=6mm + motion_6 → HRF corr = 0.9971

**Worst Configs (HRF corr < 0.1):**
- Config 10: no_smooth + high_pass + motion_6 → HRF corr = 0.045
- Config 22: smooth=6mm + high_pass + motion_6 → HRF corr = -0.012
- Config 34: smooth=8mm + high_pass + motion_6 → HRF corr = 0.009

**Key Finding:** High-pass filtering is DETRIMENTAL (reduces correlation by ~100×)

---

## Questions to Answer with Results

1. **Did Config 26 improve HRF homogeneity?**
   - Compare: Config 26 HRF corr vs voxel-specific (0.066)
   - Target: >0.95

2. **Did preprocessing maintain reliability?**
   - Compare: Config 26 reliability vs voxel-specific (0.96)
   - Target: >0.85

3. **Did smoothing improve decoding?**
   - Compare: Config 26 classification vs voxel-specific (8%)
   - Target: >50%

4. **Is the improvement from smoothing or motion regression?**
   - Compare: Config 26 (smooth+motion) vs Config 24 (smooth only)
   - Expected: Both contribute, but smoothing is primary

5. **Does ROI universal HRF outperform voxel-specific?**
   - Compare: Config 26 BH2009 vs voxel-specific on all metrics
   - Hypothesis: Yes, because better HRF homogeneity

---

## Scientific Interpretation

### If Config 26 Succeeds

**Conclusion:** Preprocessing is **critical** for BH2009 pipeline
- Voxel-specific failed due to high HRF variability (0.066)
- Smoothing dramatically improves HRF homogeneity (0.066 → 0.9998)
- ROI universal HRF requires homogeneous voxel responses
- **Implication:** Original B&H (2009) paper likely used substantial preprocessing

### If Config 26 Partially Succeeds

**Conclusion:** Preprocessing improves quality but insufficient for decoding
- High HRF homogeneity achieved (>0.85)
- But amplitude SNR still too low (<1.0)
- **Next:** Try advanced preprocessing (ICA-AROMA, CompCor, etc.)

### If Config 26 Fails

**Conclusion:** Problem is not preprocessing-related
- Could be:
  1. ROI selection issue (wrong voxels)
  2. Stimulus timing/presentation issue
  3. Subject attention/engagement issue
  4. Fundamental limitation of this ROI for color decoding
- **Next:** Investigate data quality and experimental design

---

## Contact

For questions or issues:
1. Check error logs: `logs/BH2009_config26_*.err`
2. Review output: `logs/BH2009_config26_*.out`
3. Compare with grid search results: `logs/grid_search_results.csv`

**Expected next conversation topics:**
- Results interpretation
- Comparison with voxel-specific approach
- Extension to all ROIs and subjects
