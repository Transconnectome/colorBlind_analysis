# SRM Evaluation - Quick Start Guide

**Last Updated**: 2026-02-06

---

## 🚀 Quick Deployment (3 Steps)

### 1️⃣ Upload Scripts to Server

**On local machine:**
```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts

# Upload all files in one command
scp evaluate_srm_vs_procrustes.py evaluate_srm_between_subject.py aggregate_srm_results.py visualize_srm_comparison.py test_srm_server_interactive.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/ && scp sbatch/run_srm_evaluation.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/sbatch/

# Create directories on server
ssh haba6030@node2 "mkdir -p /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/{results/srm_evaluation,logs}"
```

Expected: Files transferred successfully

---

### 2️⃣ Install BrainIAK (First Time Only)

**On server:**
```bash
ssh haba6030@node2
conda activate nilearn
conda install -c brainiak -c conda-forge brainiak

# Verify
python -c "import brainiak; print('OK')"
```

---

### 3️⃣ Test & Submit Job

**Test single subject first:**
```bash
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts
bash test_srm_server_interactive.sh
```

Expected: `✅ Test completed successfully`

**Submit array job for all 40 pairs:**
```bash
sbatch sbatch/run_srm_evaluation.sbatch
```

**Monitor progress:**
```bash
squeue -u haba6030
watch -n 10 squeue -u haba6030
```

---

## 📊 Check Results

**After job completes (~3-4 hours):**

```bash
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts

# Check output files (should be 40 JSON files + 40 PNG plots)
ls -lh results/srm_evaluation/*/sub-*_*.json | wc -l  # Should be 40

# Aggregate results
python aggregate_srm_results.py \
    --results-dir results/srm_evaluation/{TIMESTAMP} \
    --output-dir results/srm_evaluation/aggregated

# Download results to local
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/results/srm_evaluation \
    /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/results/
```

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| BrainIAK not found | `conda install -c brainiak -c conda-forge brainiak` |
| Baseline files missing | Check Phase 1 completed: `ls /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline/sub-01/V1/*.npy` |
| Job fails with OOM | Reduce concurrent tasks: `#SBATCH --array=1-40%5` in sbatch script |
| Slow execution | Normal! V1 takes ~10-15 min per subject |

---

## 📁 What Gets Created

```
results/srm_evaluation/{TIMESTAMP}/
├── sub-01_V1_srm_results.json        # 40 result files
├── sub-01_V1_srm_k_tuning.png        # 40 plots
├── sub-01_V1_memory.log              # Memory usage
└── ... (39 more subject-ROI pairs)
```

**Key metrics in each JSON:**
- Procrustes baseline (RDM correlation, accuracy)
- SRM results for different k values
- Best k selection
- Improvement over Procrustes (%)
- Winner: SRM or Procrustes

---

## ✅ Success Criteria

- [ ] 40 JSON result files created
- [ ] 40 PNG tuning plots created
- [ ] No OOM errors in logs
- [ ] Procrustes metrics match Phase 1 baseline
- [ ] SRM shows +5-15% improvement (expected)

---

**For detailed instructions, see:**
- `EXECUTION_GUIDE_PHASE3_SRM.md` - Full execution guide
- `SRM_BASELINE_ADAPTATION_SUMMARY.md` - Technical implementation details
