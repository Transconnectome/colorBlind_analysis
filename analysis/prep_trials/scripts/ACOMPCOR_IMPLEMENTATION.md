# aCompCor Implementation for Custom Preprocessing Pipeline

## Overview

Added anatomical Component Correction (aCompCor) to `generate_confounds.py` for robust physiological noise removal.

### Key Features

1. **Conservative tissue masking** to avoid GM contamination
   - ICBM152_2009 tissue probability maps (MNI space)
   - Very high threshold (prob > 0.99) for CSF and WM
   - 1-voxel morphological erosion
   - Intersection with brain mask (partial FOV handling)

2. **aCompCor components** (fMRIPrep standard)
   - 5 components from CSF mask → `a_comp_cor_00` ~ `a_comp_cor_04`
   - 5 components from WM mask → `a_comp_cor_05` ~ `a_comp_cor_09`
   - Total: 10 aCompCor components per run

3. **Partial FOV validation**
   - Checks CSF/WM mask coverage in brain
   - Warns if ventricles not included
   - Generates zero components for empty masks

4. **Quality control visualizations**
   - Tissue mask overlay (axial slices)
   - Component timeseries and variance explained
   - Mask coverage statistics (JSON)

---

## Modified Files

### 1. `generate_confounds.py`

**New functions:**
- `load_tissue_probability_maps()`: Fetch ICBM tissue maps
- `create_conservative_tissue_masks()`: Generate CSF/WM masks
- `compute_acompcor()`: PCA-based component extraction
- `visualize_tissue_masks()`: Axial slice overlay visualization
- `validate_acompcor_quality()`: Component QC plots

**Modified functions:**
- `extract_tissue_signals()`: Now uses atlas-based masks
- `generate_confounds()`: Added aCompCor computation and QC

**New confound columns:**
```python
# Motion (6 DOF)
trans_x, trans_y, trans_z, rot_x, rot_y, rot_z

# aCompCor (10 components)
a_comp_cor_00, a_comp_cor_01, ..., a_comp_cor_09

# Tissue mean signals
csf, white_matter

# Global signal
global_signal

# Drift regressors
cosine00, cosine01, ...
```

---

## Usage

### Step 1: Upload to Server

```bash
# Upload modified script and sbatch files
scp generate_confounds.py *.sbatch \
  haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/scripts/
```

### Step 2: Test on Single Subject/Run

```bash
# SSH to server
ssh haba6030@node2

# Submit test job
cd /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/scripts
sbatch run_generate_confounds_test.sbatch

# Monitor job
squeue -u haba6030

# Check log
tail -f /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/confounds_test_*.out
```

### Step 3: Validate Outputs

**Check confounds file:**
```bash
# View TSV file
cd /storage/connectome/haba6030/fmriprep_out_method3_header_mi/sub-01/func
head -1 sub-01_task-rsvp_run-1_desc-confounds_timeseries.tsv

# Expected columns: trans_x, trans_y, ..., a_comp_cor_00, ..., a_comp_cor_09, csf, white_matter, ...
```

**Check QC visualizations:**
```bash
cd /storage/connectome/haba6030/fmriprep_out_method3_header_mi/qc/sub-01

ls -lh
# Expected files:
#   - sub-01_run-1_tissue_masks.png
#   - sub-01_run-1_acompcor_qc.png
#   - sub-01_run-1_mask_stats.json

# View mask statistics
cat sub-01_run-1_mask_stats.json
```

**Download QC visualizations for inspection:**
```bash
# On local machine
scp -r haba6030@node2:/storage/connectome/haba6030/fmriprep_out_method3_header_mi/qc/sub-01 \
  ~/Downloads/acompcor_qc_sub01/
```

### Step 4: Inspect QC Plots

**tissue_masks.png:**
- Check CSF mask (blue) coverage
  - ✅ Should cover lateral ventricles (if in FOV)
  - ⚠️ May be empty for partial FOV (occipital only)
- Check WM mask (red) coverage
  - ✅ Should cover deep white matter (corpus callosum, internal capsule)
  - ⚠️ Should NOT overlap with GM (cortex)

**acompcor_qc.png:**
- Component timeseries (top row)
  - Should show oscillatory patterns (physiological noise)
  - First component should capture most variance
- Variance explained (bottom row)
  - First 3 components should explain >50% variance
  - Decreasing trend expected

**mask_stats.json:**
```json
{
  "n_brain_voxels": 50000,
  "n_csf_voxels": 1200,    // ⚠️ May be 0 for partial FOV
  "n_wm_voxels": 8500,
  "csf_coverage": 2.4,     // % of brain
  "wm_coverage": 17.0
}
```

### Step 5: Run for All Subjects

```bash
# Submit array job (10 subjects × 6 runs = 60 tasks)
sbatch run_generate_confounds_all.sbatch

# Monitor progress
watch -n 10 squeue -u haba6030

# Check completion
sacct -j <job_id> --format=JobID,State,Elapsed,MaxRSS
```

---

## Expected Warnings (Partial FOV)

### CSF Mask Empty

```
⚠️  WARNING: CSF mask is empty!
   Partial FOV may not include ventricles.
   CSF aCompCor components will be zero.
```

**Cause:** Partial FOV (occipital cortex) excludes lateral ventricles

**Impact:**
- `a_comp_cor_00` ~ `a_comp_cor_04` will be zero
- WM components (`a_comp_cor_05` ~ `a_comp_cor_09`) still valid
- Mean CSF signal (`csf` column) fallback to intensity-based estimate

**Action:** This is expected for visual cortex studies. WM aCompCor is sufficient.

### Low WM Coverage

```
⚠️  WARNING: WM mask has only 500 voxels (1.2% of brain)
```

**Cause:** Very conservative threshold (prob > 0.99) + erosion

**Impact:** Fewer voxels for PCA, but higher confidence in avoiding GM

**Action:** Acceptable. Quality over quantity for aCompCor.

---

## Validation Checklist

After test run, verify:

- [ ] Confounds TSV contains `a_comp_cor_00` ~ `a_comp_cor_09`
- [ ] Component values are non-zero (except CSF if partial FOV)
- [ ] Variance explained shows decreasing trend
- [ ] Tissue masks do NOT overlap with cortex (inspect PNG)
- [ ] WM mask covers deep white matter (corpus callosum visible)
- [ ] No errors in SLURM log file

---

## Troubleshooting

### Error: "No module named sklearn"

```bash
# In nilearn conda environment
conda install scikit-learn
```

### Error: "Could not load tissue probability maps"

Check internet connection (downloads ICBM atlas on first run):
```bash
python -c "from nilearn import datasets; datasets.fetch_icbm152_2009()"
```

### Masks appear misaligned

Check BOLD and atlas affine matrices match:
```python
import nibabel as nib
bold = nib.load('...bold.nii.gz')
print(bold.affine)
# Should match MNI152NLin2009cAsym
```

---

## Integration with Existing Pipeline

### Usage in `fir_reconstruction_BH2009_system_clean.py`

The generated confounds are compatible with existing code:

```python
# Load confounds (standard mode recommended)
confounds, n_conf = load_motion_confounds(
    confounds_path,
    motion_type='standard',  # Motion + tissue + drift
    compcor_n=5              # Use first 5 aCompCor (CSF)
)
```

**Options:**
- `compcor_n=5`: CSF aCompCor only (conservative)
- `compcor_n=10`: CSF + WM aCompCor (aggressive)
- `compcor_n=None`: No aCompCor (legacy mode)

### Recommended Settings

**For baseline analysis:**
```python
motion_type='standard'  # Motion + tissue + drift
compcor_n=5            # CSF aCompCor
```

**For aggressive denoising:**
```python
motion_type='standard'
compcor_n=10          # CSF + WM aCompCor
```

---

## References

- Behzadi et al. (2007). "A component based noise correction method (CompCor) for BOLD and perfusion based fMRI." NeuroImage.
- Muschelli et al. (2014). "Reduction of motion-related artifacts in resting state fMRI using aCompCor." NeuroImage.
- fMRIPrep documentation: https://fmriprep.org/en/stable/workflows.html#confounds

---

## File Outputs Summary

```
/storage/connectome/haba6030/fmriprep_out_method3_header_mi/
├── sub-01/
│   └── func/
│       └── sub-01_task-rsvp_run-1_desc-confounds_timeseries.tsv  # Confounds with aCompCor
└── qc/
    └── sub-01/
        ├── sub-01_run-1_tissue_masks.png        # Mask visualization
        ├── sub-01_run-1_acompcor_qc.png         # Component QC
        └── sub-01_run-1_mask_stats.json         # Coverage statistics
```

---

**Author:** Claude Code
**Date:** 2026-02-08
**Version:** 1.0
