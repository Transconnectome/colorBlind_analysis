# Quick Start Guide - Resume Here

**Last Updated:** 2025-11-05
**Status:** Ready to run parallel ROI testing

---

## ⚡ Quick Resume (Copy-Paste)

```bash
# 1. Upload scripts (from local Mac)
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis
scp naive_analysis.py submit_roi_parallel.sh check_parallel_results.sh test_roi_reconstruction.py node2:/scratch/connectome/haba6030/colorBlind/

# 2. Run parallel ROI tests (on server)
ssh node2
cd /scratch/connectome/haba6030/colorBlind
chmod +x *.sh
./submit_roi_parallel.sh

# 3. Monitor (15-20 min)
watch squeue -u $USER

# 4. Check results
./check_parallel_results.sh
```

---

## 📊 Current State

**Brain Mask Baseline:**
- Hit rate: 22.9%, p=0.401 ❌ (not significant)

**Goal:**
- Find ROI with p<0.05 ✅

**Most Promising:**
- **V2**: 310 voxels, 58% overlap
- Expected: 35-40% hit rate, p~0.05

---

## ✅ Completed This Session

1. Fixed ROI selection in naive_analysis.py
2. Created parallel execution scripts (75% time savings)
3. Updated ML files (saved for later - not uploading yet)
4. Initialized git repo (59 files committed)

---

## 🎯 Next Decision Point

**After parallel jobs complete (~20 min):**

| Result | Action |
|--------|--------|
| Any ROI p<0.05 | ✅ Use as baseline → Design CVD filter |
| Best ROI 0.05<p<0.10 | ⚠️ Try FIR model next |
| All ROI p>0.10 | ❌ Try FIR, then ML/DL |

---

## 📁 Key Files

**Ready to upload:**
- naive_analysis.py ✅
- submit_roi_parallel.sh ✅
- check_parallel_results.sh ✅
- test_roi_reconstruction.py ✅

**Keep local (not needed yet):**
- ml_forward_model.py 💾
- compare_forward_models.py 💾

**For context:**
- CURRENT_STATUS.md (full details)
- PARALLEL_ROI_GUIDE.md (parallel testing guide)

---

## 🐛 If Something Goes Wrong

**Jobs failed?**
```bash
cat logs/naive_V2_*.err
cat logs/naive_V2_*.out
```

**Resubmit single ROI:**
```bash
rm -f hrf_test_outputs/cache_V2/*
sbatch --job-name=naive_V2 --output=logs/naive_V2_new_%j.out --mem=16G --time=00:30:00 \
  --wrap="sed 's/ROI_SELECTION = \[.*\]/ROI_SELECTION = [\"V2\"]/' naive_analysis.py > tmp.py && python tmp.py && rm tmp.py"
```

---

**Read CURRENT_STATUS.md for full details**
