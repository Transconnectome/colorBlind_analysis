# Preprocessing Registration Methods Comparison

**Test subjects**: Sub-01, 03, 06
**Goal**: Find optimal BOLD→T1w registration for Limited FOV + high obliquity

## Background

Original preprocessing (original_v3) uses FLIRT→BBR with wide search. PI suggested header-based initialization might work better for Limited FOV. Testing 4 alternatives.

BOLD has 29.5° sagittal obliquity. T1w is nearly cardinal. Header contains rotation info but accuracy needs testing.

---

## Methods

### Method 1: FLIRT → BBR (baseline)
```bash
--bold2t1w-init register
--force-bbr
--fs-no-reconall
```
- Initial: FLIRT wide search (MI)
- Refinement: BBR with FSL FAST WM
- Current Dice: 0.889

### Method 2: Header → BBR (FreeSurfer)
```bash
--bold2t1w-init header
--force-bbr
# FreeSurfer recon-all required
```
- Initial: Header qform/sform only
- Refinement: BBR with FreeSurfer WM surfaces
- **Note**: FSL BBR doesn't support header init, must use FreeSurfer
- Time: ~8-10h per subject (recon-all)

### Method 3: Header → MI (mri_coreg)
```bash
mri_coreg --ref T1w --mov BOLD --reg output.lta --regheader
```
- Initial: Header
- Optimization: MI with Powell's method
- No BBR step (MI sufficient for 2mm fMRI)
- Time: ~30 min per subject

### Method 4: Header → BBR 1-pass (conditional)
Direct bbregister with `--init-header --no-pass1`. Only run if Method 2 succeeds.

---

## Execution Plan

**Method 3 first** (fastest, most promising):
```bash
sbatch scripts/run_method3_header_mi.sbatch
# 3 subjects × 30 min = 1.5h
```

**Method 2 later** (when time available):
```bash
sbatch scripts/run_method2_header_bbr.sbatch
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

- ✅ Scripts ready (`run_method2_header_bbr.sbatch`, `run_method3_header_mi.sbatch`)
- ✅ Fixed: Method 2 now uses FreeSurfer BBR (not FSL)
- ✅ Fixed: Removed `--verbose` from mri_coreg
- ✅ Uploaded to server
- ✅ Jobs executing
- ⏳ Compare results
