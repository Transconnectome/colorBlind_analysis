# Quick Fix Guide - TL;DR

**Problem**: ROI voxels increased (310→536), novel error degraded (52°→99°)

**Root Cause**: Different reference image or missing brain mask during ROI building

---

## 🚀 Quick Fix (3 Steps)

### 1. Diagnose on Server
```bash
# Upload & run diagnostic
scp diagnose_server.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
bash diagnose_server.sh
```

**Look for**: V2 mask with 310 voxels (GOOD) vs 536/553 voxels (BAD)

---

### 2. Fix ROI Masks

**If GOOD masks exist** (310 voxels):
```bash
# Backup immediately!
mkdir -p GOOD_MASKS_BACKUP
cp derivatives/sub-01/roi/*.nii.gz GOOD_MASKS_BACKUP/
```

**If GOOD masks don't exist**:
```bash
# Use backup code to rebuild
cp backup/fir_reconstruction_universal_hrf_BEST.py fir_reconstruction_universal_hrf.py
python build_roi_masks.py --subject 01
python check_voxel_count.py derivatives/sub-01/roi/*.nii.gz
```

---

### 3. Test & Verify
```bash
# Single test
python fir_reconstruction_universal_hrf.py --subject P01 --roi V2 --use-pca --n-components 20

# Check result
cat derivatives/sub-P01/fir_reconstruction/V2_universal_hrf/summary.csv
# Should show: 310 voxels, 5 TRs, ~52° novel error
```

---

## 📋 Success Criteria

✅ **V2 ROI**: 310 voxels (not 536 or 553)
✅ **Optimal delay**: 5 TRs / 7.5 seconds (not 0 or 7)
✅ **Novel error**: ~52° (not 86° or 99°)
✅ **Classification**: 100%

---

## 📚 Full Documentation

- **DIAGNOSTIC_REPORT_v2.md** - Detailed problem analysis
- **RECOVERY_PLAN.md** - Complete step-by-step recovery
- **diagnose_server.sh** - Diagnostic script for server

---

## 🆘 If Still Broken

Check these in order:

1. **Wrong reference image**
   - Should be res-2 files (97×115×97)
   - Check: `fslinfo <reference_func>.nii.gz`

2. **Missing brain mask**
   - Look for: `*res-2*brain_mask.nii.gz`
   - Without it: ROI includes non-brain voxels

3. **HRF peak finding**
   - Should be `argmax` not `argmin` or 0
   - Add debug prints around line 600-700

4. **Subject ID confusion**
   - P01 files are named "sub-01" (without P)
   - But derivatives go in "sub-P01" folder
   - Troubleshoot code HAD this right!

---

## 💬 Questions?

Review the full diagnostic reports or ask for specific help with:
- Voxel count still wrong
- Optimal delay detection
- Path configuration
- Batch file creation
