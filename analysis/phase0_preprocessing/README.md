# Preprocessing Registration Methods Comparison

**Test subjects**: Sub-01, 03, 06
**Goal**: Find optimal BOLD→T1w registration for Limited FOV + high obliquity

## Background

Original preprocessing (original_v3) uses FLIRT→BBR with wide search. PI suggested header-based initialization might work better for Limited FOV. Testing 4 alternatives.

BOLD has 29.5° sagittal obliquity. T1w is nearly cardinal. Header contains rotation info but accuracy needs testing.

---

## Methods - Intuitive Explanation

**Problem**: Align two transparent maps where one is partial and tilted.
- Map 1 (BOLD): 29.5° tilted, back of head only (Partial FOV), blurry.
- Map 2 (T1w): Normal orientation, whole brain, clear.

**The Core Conflict**:
- **BBR (Boundary-Based Registration)**: The "Wrinkle Matcher". It tries to align the fMRI image by fitting it exactly to the **boundaries between White Matter (WM) and Gray Matter (GM)**—essentially the brain's "wrinkles".
    - *Risk:* With **Partial FOV**, many "wrinkles" are cut off. The algorithm might mistake the edge of the image for a brain fold.
- **MI (Mutual Information)**: The "Pattern Matcher". It ignores specific edges and looks at the **global statistical relationship** between the brightness of T1w and fMRI.
    - *Benefit:* Safe for Partial FOV because it aligns the "texture" of the visible brain chunks without needing complete boundaries.

---

### Method 1: FLIRT → BBR (baseline)
**"Blind Search → Wrinkle Fitting"**

```bash
--bold2t1w-init register
--force-bbr
--fs-no-reconall
```

(a) **FLIRT (Blind Search)**: Like matching puzzle pieces in the dark.
- Ignores header info. Rotates the image 360° to find a rough match.
- **Risk**: With only 1/4 of the brain, it might match the back of the head to the front.

(b) **BBR (Wrinkle Fitting)**: "Boundary-Based Registration".
- Fine-tunes alignment by snapping to the **GM/WM boundaries (wrinkles)**.
- **Risk**: High. If FLIRT was slightly off, or if the necessary wrinkles are outside the Field of View, BBR can distort the alignment.

Current Dice: 0.889 ✅ (Luckily succeeded)

---

### Method 2: Header → BBR (FreeSurfer)
**"Compass Guide → Wrinkle Fitting"**

```bash
--bold2t1w-init header
--force-bbr
# FreeSurfer recon-all required
```

(a) **Header (Compass Guide)**: Trusting the map coordinates.
- Reads the rotation (29.5°) directly from the file header.
- Skips the blind search. Puts us in the "right neighborhood".

(b) **BBR (Wrinkle Fitting)**: The weak link.
- Even though we started in the right spot, we still use the "Wrinkle Fitting" tool to finish.
- **Risk**: BBR expects a whole brain with defined contours. With Partial FOV, the algorithm searches for boundaries that don't exist.

**Note**: FSL BBR doesn't support header init, must use FreeSurfer.

Expected: Dice 0.80-0.92

---

### Method 3: Header → MI (mri_coreg) ⭐
**"Compass Guide → Pattern Matching (MI Only)"**

**Why this is the proposed solution:** It abandons the "Wrinkle Fitting" (BBR) dogma in favor of safety.

```bash
mri_coreg --ref T1w --mov BOLD --reg output.lta --regheader
```

(a) **Header (Compass Guide)**: Starts at the correct angle (~29.5°) provided by the scanner.

(a') **MI Optimization (Pattern Matching)**:
- **Mechanism**: Maximizes **Mutual Information**. Instead of looking for specific lines (edges), it aligns based on the **Global Intensity Pattern** (e.g., "Where T1w is bright, BOLD should be dark").
- **Safety**: It doesn't care if the brain is cut in half. As long as the overlapping texture matches, it locks on.
- **Precision**: ~1mm (Sufficient for 2mm resolution fMRI).

**Why SKIP BBR?**
- BBR strives for 0.1mm precision using wrinkles, but risks 10mm errors on Partial FOV data.
- MI guarantees 1mm precision with near-zero risk of catastrophic failure.

Advantages:
✅ **Robust to Partial FOV** (ignores missing boundaries)
✅ **Fast** (~30 min vs 10 hours for Method 2)
✅ **Safe** (No risk of BBR "snapping" to wrong edges)

Expected: Dice 0.90-0.95

---

### Method 4: Header → BBR 1-pass (conditional)
**"Compass Guide → Aggressive Wrinkle Fitting"**

Direct bbregister with `--init-header --no-pass1`.

(a) **Header**: Start at given angle.

(b) **BBR (1-pass)**:
- Normal BBR has a "coarse search" (Pass 1) to prevent getting lost.
- This method disables Pass 1 to save time.
- **Risk**: If the Header is off by even 5 degrees, BBR will fail completely because it relies solely on local wrinkles without checking the global fit.

Expected: Dice < 0.80 (Too risky)

---

## Execution Plan

**Method 3 first** (fastest, most promising):
```bash
sbatch scripts/run_method3_header_mi_all_subjects.sbatch
# 3 subjects × 30 min = 1.5h
```

**Method 2 later** (when time available):
```bash
# Method 2 was NOT adopted; code archived at _archive/registration_method_selection/
# 3 subjects × 8-10h = 24-30h
```

**Method 1**: Extract Dice from existing original_v3 outputs (no rerun needed)

**Method 4**: Skip unless Method 2 shows Dice > 0.85

---

## Evaluation

**Primary metric**: Dice coefficient of brain masks in MNI space

**Comparison**: `compare_methods.py` generates plots and reports after all methods complete

---

## Current Status

**Last updated**: 2026-01-06

- ✅ Canonical: `run_method3_header_mi_all_subjects.sbatch` (exp1), `run_method3_header_mi_2nd.sbatch` (exp2). Method 2 and the 3-subject pilot are archived under `_archive/registration_method_selection/`.
- ✅ Fixed: Method 2 now uses FreeSurfer BBR (not FSL)
- ✅ Fixed: Removed `--verbose` from mri_coreg
- ✅ Uploaded to server
- ✅ Jobs executing
- ⏳ Compare results

---

## Critical Best Practices

### Storage Management

**Problem**: fMRIPrep work directory deleted or inaccessible
**Cause**: Using `/scratch/` (temporary) instead of `/storage/` (permanent)
**Solution**: Always set `--work-dir /storage/connectome/haba6030/fmriprep_work_*/`

```bash
# ✅ CORRECT
--work-dir /storage/connectome/haba6030/fmriprep_work_method3/

# ❌ WRONG
--work-dir /scratch/connectome/haba6030/fmriprep_work_method3/
```

---

### Container Permission Issue

**Problem**: Cannot delete/modify files in work directory (permission denied)
**Cause**: Running container without `--userns` creates root-owned files (uid=0 inside container)
**Solution**: Always use `apptainer exec --userns` or `singularity exec --cleanenv`

```bash
# ✅ CORRECT
apptainer exec --userns fmriprep.sif fmriprep ...
singularity exec --cleanenv fmriprep.sif fmriprep ...

# ❌ WRONG (creates root-owned files)
apptainer run fmriprep.sif ...
singularity run fmriprep.sif ...
```
