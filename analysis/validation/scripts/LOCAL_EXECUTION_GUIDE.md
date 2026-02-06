# SRM Evaluation - Local Execution Guide

**Last Updated**: 2026-02-06
**Purpose**: Run SRM evaluation locally using downloaded baseline results

---

## 📋 Overview

**Two types of analysis:**
1. **Within-Subject (PCA vs Procrustes)** - 40 subject-ROI pairs
2. **Between-Subject (SRM: HC vs CVD)** - 4 ROIs

**Advantages of local execution:**
- ✅ No conda environment issues on server
- ✅ Interactive development and debugging
- ✅ Easy to monitor progress
- ✅ Results available immediately

**Requirements:**
- Baseline `.npy` files from server
- ~5-10 GB disk space
- ~8-16 GB RAM (for larger ROIs like V1)
- Runtime:
  - Within-subject (40 pairs): ~6-10 hours
  - Between-subject (4 ROIs): ~30-60 minutes

---

## 🚀 Quick Start (4 Steps)

### Step 1: Download Baseline Data from Server

**Option A: Download everything (recommended, ~5 GB):**
```bash
rsync -avz --progress haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline/ /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/baseline/
```

**Option B: Download only amplitudes files (minimal, ~500 MB):**
```bash
rsync -avz --include='*/' --include='amplitudes_*.npy' --exclude='*' haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline/ /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/baseline/
```

**Verify download:**
```bash
ls /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/baseline/sub-01/V1/*.npy
```

Expected files:
- `amplitudes_z.npy`
- `amplitudes_procrustes.npy`

---

### Step 2: Create Local SRM Environment

```bash
# Create environment
conda create -n srm python=3.9 numpy scipy scikit-learn matplotlib seaborn -y

# Activate
conda activate srm

# Install BrainIAK
pip install brainiak

# Verify
python -c "import brainiak; import numpy; print('All packages ready!')"
```

---

### Step 3A: Test Within-Subject Analysis (PCA vs Procrustes)

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts

# Test with 2 subject-ROI pairs (~10-20 min)
bash run_srm_local_test.sh
```

**Expected output:**
```
Testing: sub-01 V1
...
✓ sub-01 V1 completed successfully

Testing: sub-02 V2
...
✓ sub-02 V2 completed successfully

Test completed successfully!
```

**Check results:**
```bash
# View JSON results
cat results/srm_evaluation/test_*/sub-01_V1_srm_results.json | python -m json.tool | head -50

# View plots
open results/srm_evaluation/test_*/*.png
```

### Step 3B: Test Between-Subject Analysis (SRM: HC vs CVD)

```bash
# Test with 2 ROIs (~5-10 min)
bash run_srm_between_subject_local_test.sh
```

**Expected output:**
```
Testing: V1 (k=50)
[1/6] Loading data...
  HC subjects: ['sub-01', 'sub-02', ..., 'sub-06'] (n=6)
  CVD subjects: ['sub-08', 'sub-09', 'sub-10'] (n=3)
...
[4/6] Computing Procrustes disparities...
  HC disparities: 0.12 ± 0.03 (n=6)
  CVD disparities: 0.18 ± 0.05 (n=3)
  t-test: t=2.45, p=0.0234
✓ V1 completed successfully
```

**Check results:**
```bash
# View JSON
cat results/srm_between_subject/test_*/V1_srm_between_subject_results.json | python -m json.tool

# View plots
open results/srm_between_subject/test_*/*.png
```

---

### Step 4A: Run Full Within-Subject Analysis (40 Pairs)

**If test looks good:**
```bash
# Run all 40 subject-ROI pairs
bash run_srm_local_all.sh

# This will run overnight (~6-10 hours)
# Each pair takes 10-30 min depending on ROI size
```

**Monitor progress:**
```bash
# In another terminal, watch progress
tail -f results/srm_evaluation/local_*/sub-*_log.txt

# Check how many completed
ls results/srm_evaluation/local_*/*.json | wc -l
```

---

## ⏱️ Expected Runtime

| ROI | Voxels | Time per Subject | Memory |
|-----|--------|------------------|--------|
| V1  | ~300   | 15-30 min        | 8-12 GB |
| V2  | ~200   | 10-20 min        | 6-10 GB |
| V3  | ~50    | 5-10 min         | 4-6 GB  |
| hV4 | ~70    | 5-15 min         | 4-8 GB  |

**Total for 40 pairs:** 6-10 hours (sequential)

### Step 4B: Run Full Between-Subject Analysis (4 ROIs)

**If between-subject test looks good:**
```bash
# Run all 4 ROIs (V1, V2, V3, hV4)
bash run_srm_between_subject_local_all.sh

# This takes ~30-60 minutes total
# Each ROI takes 5-15 min depending on size
```

**Monitor progress:**
```bash
# Watch progress
tail -f results/srm_between_subject/local_*/V1_log.txt

# Check how many completed
ls results/srm_between_subject/local_*/*_srm_between_subject_results.json | wc -l
```

**Expected runtime per ROI:**
- V1: ~15-20 min (most subjects, most voxels)
- V2: ~10-15 min
- V3: ~5-10 min (fewer voxels)
- hV4: ~5-10 min

---

## 📊 After Completion

### Within-Subject Results

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts

# Find your results directory
RESULTS_DIR=$(ls -td results/srm_evaluation/local_* | head -1)

# Aggregate
python aggregate_srm_results.py \
  --results-dir "${RESULTS_DIR}" \
  --output-dir "${RESULTS_DIR}/aggregated"
```

### Generate Figures

```bash
python visualize_srm_comparison.py \
  --results-file "${RESULTS_DIR}/aggregated/srm_summary.json" \
  --output-dir "${RESULTS_DIR}/figures"
```

### Within-Subject: Check Results

```bash
# Summary statistics
cat "${RESULTS_DIR}/aggregated/srm_summary.json" | python -m json.tool

# View figures
open "${RESULTS_DIR}/figures"/*.png
```

### Between-Subject Results

```bash
# Find your results directory
RESULTS_DIR=$(ls -td results/srm_between_subject/local_* | head -1)

# View results for each ROI
for ROI in V1 V2 V3 hV4; do
  echo "=== ${ROI} ==="
  cat "${RESULTS_DIR}/${ROI}_srm_between_subject_results.json" | python -m json.tool | grep -A 10 "disparities\|statistical_test"
  echo ""
done

# View all plots
open "${RESULTS_DIR}"/*.png
```

**Key metrics to check:**
1. **Disparities**: HC-to-HC vs CVD-to-HC (CVD should be higher)
2. **Statistical significance**: p-value < 0.05?
3. **Effect size**: Cohen's d (0.5 = medium, 0.8 = large)
4. **RDM similarities**: HC-HC, CVD-CVD, HC-CVD patterns

---

## 🔍 Troubleshooting

### Issue: Out of Memory

**Solution:** Run fewer pairs at once or close other applications

```bash
# Edit run_srm_local_all.sh to add delays between tasks
# Add after line 48:
sleep 10  # Give system time to free memory
```

### Issue: BrainIAK import error

**Solution:**
```bash
conda activate srm
pip install --upgrade brainiak
```

### Issue: File not found

**Check baseline data downloaded correctly:**
```bash
ls /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/baseline/sub-01/V1/
```

Should see: `amplitudes_z.npy`, `amplitudes_procrustes.npy`

---

## 💾 Uploading Results Back to Server (Optional)

**If you want to save results on server:**
```bash
# Find your results directory
RESULTS_DIR=$(ls -td results/srm_evaluation/local_* | head -1)

# Upload to server
rsync -avz --progress "${RESULTS_DIR}" \
  haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/results/srm_evaluation/
```

---

## 📁 File Structure

```
analysis/validation/scripts/
├── run_srm_local_test.sh                    # Within-subject test (2 pairs)
├── run_srm_local_all.sh                     # Within-subject full (40 pairs)
├── run_srm_between_subject_local_test.sh    # Between-subject test (2 ROIs) ✨ NEW
├── run_srm_between_subject_local_all.sh     # Between-subject full (4 ROIs) ✨ NEW
├── evaluate_srm_vs_procrustes.py            # Within-subject (PCA)
├── evaluate_srm_between_subject.py          # Between-subject (SRM)
├── aggregate_srm_results.py                 # Results aggregation
└── visualize_srm_comparison.py              # Figure generation

results/
├── srm_evaluation/                          # Within-subject results
│   └── local_YYYYMMDD_HHMMSS/
│       ├── sub-01_V1_srm_results.json
│       ├── sub-01_V1_srm_k_tuning.png
│       └── ... (40 pairs)
└── srm_between_subject/                     # Between-subject results ✨ NEW
    └── local_YYYYMMDD_HHMMSS/
        ├── V1_srm_between_subject_results.json
        ├── V1_hc_cvd_disparity_comparison.png
        ├── V1_rdm_similarity_matrix.png
        └── ... (4 ROIs × 3 files each)
```

---

## ✅ Success Criteria

### Within-Subject (PCA vs Procrustes)
- [ ] 40 JSON result files created
- [ ] 40 PNG tuning plots created
- [ ] Procrustes metrics match Phase 1 baseline
- [ ] PCA shows improvement for some k values
- [ ] Aggregated results generated
- [ ] Figures created

### Between-Subject (SRM: HC vs CVD)
- [ ] 4 JSON result files created (one per ROI)
- [ ] 8 PNG plots created (2 per ROI: disparity + similarity matrix)
- [ ] CVD disparities > HC disparities
- [ ] Statistical tests show significance (ideally p < 0.05)
- [ ] Effect sizes are meaningful (Cohen's d > 0.5)
- [ ] RDM similarities show expected patterns

---

## 🆚 Local vs Server Comparison

| Aspect | Local | Server |
|--------|-------|--------|
| Setup | Easy (conda works) | Hard (env conflicts) |
| Speed | Sequential (~8h) | Parallel (~3h) |
| Monitoring | Easy | Via logs |
| Debugging | Interactive | Batch only |
| Resources | Limited (16 GB?) | More (32 GB) |

**Recommendation:** Local execution is better given server environment issues!

---

**For questions or issues, check:**
- `QUICK_START_SRM.md` - Quick reference
- `SRM_BASELINE_ADAPTATION_SUMMARY.md` - Technical details
