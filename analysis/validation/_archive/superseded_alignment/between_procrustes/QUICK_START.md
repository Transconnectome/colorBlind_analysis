# Quick Start Guide

## 🚀 Fast Track to Execution

### Step 1: Upload to Server (1 minute)

```bash
# Single command - copy both files (NO LINE BREAKS!)
scp analysis/validation/scripts/between_procrustes/fir_reconstruction_no_voxel_filtering.py analysis/validation/scripts/between_procrustes/run_preprocessing_unfiltered.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/between_procrustes/
```

### Step 2: Run on Server (8-12 hours, mostly unattended)

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/between_procrustes
mkdir -p logs
sbatch run_preprocessing_unfiltered.sbatch
```

**Monitor progress**:
```bash
# Check queue
squeue -u haba6030

# Check logs
tail -f logs/baseline_unfilt_*.log
```

### Step 3: Download Results (10-30 minutes)

```bash
# Single command (NO LINE BREAKS!)
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/deoblique_v2/results/baseline_decoding/fixed_perRun_unfiltered /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/deoblique_v2/results/baseline_decoding/
```

### Step 4: Run Analysis Locally (<5 minutes)

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/between_procrustes
conda activate nilearn
./run_local_test.sh
```

### Step 5: Check Results

```bash
# View results
cat results/V1_procrustes_anova_results.json | python -m json.tool | less

# Quick summary
python -c "
import json
with open('results/V1_procrustes_anova_results.json') as f:
    res = json.load(f)['results']['50']
print(f'HC disparity: {res[\"disparity_stats\"][\"hc_mean\"]:.4f}')
print(f'CVD disparity: {res[\"disparity_stats\"][\"cvd_mean\"]:.4f}')
print(f'p-value: {res[\"ttest\"][\"p\"]:.4f}')
"
```

---

## 📋 Expected Timeline

| Step | Duration | Activity |
|------|----------|----------|
| 1. Upload | 1 min | scp to server |
| 2. Server run | 8-12 hrs | Unattended |
| 3. Download | 10-30 min | scp from server |
| 4. Analysis | 5 min | Local execution |
| **Total** | **~1 day** | Mostly automated |

---

## 🔍 Verification Checklist

Before uploading to server:
- [ ] Run `python verify_implementation.py` (should show 24/24 checks passed)
- [ ] Activate conda environment: `conda activate nilearn`

After server preprocessing:
- [ ] Check 9 subjects completed (sub-01 to sub-10, excluding sub-07)
- [ ] Check 4 ROIs per subject (V1, V2, V3, hV4)
- [ ] Verify reduced voxel heterogeneity

After local analysis:
- [ ] Results JSON exists for tested ROI
- [ ] HC disparities < CVD disparities (expected)
- [ ] Statistical test shows p-value

---

## ⚠️ Common Issues

### Issue: "Baseline directory not found"

**Solution**: Adjust path in run_pipeline_local.py:
```bash
python run_pipeline_local.py --roi V1 --test-mode \
    --baseline-dir /path/to/actual/baseline_unfiltered
```

### Issue: "Few common voxels"

**Expected**: 100-200 common voxels for V1
**If < 50**: Check that modified preprocessing ran correctly

### Issue: SLURM job fails

**Check**: `cat logs/baseline_unfilt_*.log` for error messages
**Common causes**:
- Out of memory → increase `--mem=64G` in SLURM script
- Wrong QOS → verify `--qos=shared` for node2

---

## 📚 Full Documentation

- **README.md**: Comprehensive overview and detailed instructions
- **SERVER_EXECUTION_GUIDE.md**: Step-by-step server workflow
- **IMPLEMENTATION_SUMMARY.md**: Technical details and status

---

## 🎯 Success Criteria

✅ Implementation complete when:
- All 24 verification checks pass
- Modified preprocessing runs on server without errors
- Common voxels found for all ROIs (>50)
- Between-subject analysis produces results
- HC-HC vs CVD-HC disparities show expected pattern

---

## 🆘 Need Help?

1. Check logs: `logs/baseline_unfilt_*.log`
2. Review troubleshooting in README.md
3. Compare with original baseline script for reference
4. Verify paths and file locations

---

**Created**: 2026-02-06
**Status**: ✅ Ready for execution
