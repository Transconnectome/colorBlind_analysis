# Phase 3 Execution Guide: SRM Evaluation

**Last Updated**: 2026-02-06
**Prerequisites**: Phase 1 (Baseline Procrustes) completed ✅
**Estimated Time**: 3-4 hours total (mostly automated)

---

## Overview

Phase 3 evaluates Shared Response Model (SRM) vs Procrustes alignment on **baseline z-scored data** from Phase 1.

**NOTE**: This guide has been adapted to use baseline results instead of whitening results, allowing immediate SRM testing without waiting for Phase 2 whitening completion.

**Key Questions:**
1. Does SRM improve over Procrustes by >5%? (threshold for adoption)
2. What is the optimal feature count (k) per ROI?
3. Do CVD subjects differ from HC in shared response space?

**Files Created:**
- ✅ `evaluate_srm_vs_procrustes.py` - Within-subject evaluation
- ✅ `evaluate_srm_between_subject.py` - Between-subject HC-CVD comparison
- ✅ `aggregate_srm_results.py` - Results aggregation
- ✅ `visualize_srm_comparison.py` - Publication figures
- ✅ `sbatch/run_srm_evaluation.sbatch` - SLURM array job

---

## Prerequisites Checklist

Before starting Phase 3, ensure:

- [x] Phase 1 (Baseline) completed successfully ✅
- [x] Baseline results directory exists and contains:
  - `sub-{ID}/{ROI}/amplitudes_z.npy` ✅
  - `sub-{ID}/{ROI}/amplitudes_procrustes.npy` ✅
  - `sub-{ID}/{ROI}/analysis_summary.json` ✅
- [ ] BrainIAK installed in nilearn environment:
  ```bash
  conda activate nilearn
  conda install -c brainiak -c conda-forge brainiak
  ```
- [x] Paths configured (auto-detected based on hostname) ✅

---

## Configuration

### Paths (Auto-Configured)

**Good news!** Paths are now auto-detected based on hostname. No manual configuration needed!

**Scripts automatically use:**
- **Server**: `/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline`
- **Local**: `/Users/jinilkim/.../analysis/phase1_preprocess_decoding/results/baseline`

**Data source**: Scripts load `amplitudes_z.npy` (pre-Procrustes) for SRM and compare with `amplitudes_procrustes.npy` (Procrustes baseline).

---

## Execution Steps

### Step 1: Install BrainIAK (One-time Setup)

```bash
# On server
ssh haba6030@node2
conda activate nilearn

# Install BrainIAK
conda install -c brainiak -c conda-forge brainiak

# Verify installation
python -c "import brainiak; print('BrainIAK version:', brainiak.__version__)"
# Expected output: BrainIAK version: 0.11 (or similar)
```

**Note**: BrainIAK installation may take 10-15 minutes.

---

### Step 2: Verify Baseline Data Exists on Server

**On server:**

```bash
ssh haba6030@node2

# Verify baseline results directory
ls /scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline/sub-01/V1/

# Expected output:
# amplitudes_z.npy
# amplitudes_procrustes.npy
# analysis_summary.json
# ... (other files)
```

**On local machine (optional check):**

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts

# Find actual Phase 2 timestamp
ssh haba6030@node2 "ls -d /scratch/connectome/haba6030/colorBlind/analysis/validation/results/whitening_ceiling_snr/20*"
# Example output: /scratch/.../whitening_ceiling_snr/20260205_143022

# Use your editor to update the 3 files mentioned above
# Replace TIMESTAMP_PLACEHOLDER with actual timestamp
```

---

### Step 3: Upload Scripts to Server

```bash
# From local machine
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# Create directories
ssh haba6030@node2 'mkdir -p /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/{utils,sbatch,logs,results/srm_evaluation}'

# Upload all scripts (single command)
scp analysis/validation/scripts/evaluate_srm_vs_procrustes.py \
    analysis/validation/scripts/evaluate_srm_between_subject.py \
    analysis/validation/scripts/aggregate_srm_results.py \
    analysis/validation/scripts/visualize_srm_comparison.py \
    analysis/validation/scripts/sbatch/run_srm_evaluation.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/

# Verify upload
ssh haba6030@node2 "ls -lh /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/*.py"
```

**Expected output:**
```
-rw-r--r-- 1 haba6030 haba6030  22K Feb  5 14:30 evaluate_srm_vs_procrustes.py
-rw-r--r-- 1 haba6030 haba6030  18K Feb  5 14:30 evaluate_srm_between_subject.py
-rw-r--r-- 1 haba6030 haba6030  12K Feb  5 14:30 aggregate_srm_results.py
-rw-r--r-- 1 haba6030 haba6030  15K Feb  5 14:30 visualize_srm_comparison.py
```

---

### Step 4: Submit Array Job (Within-Subject SRM)

```bash
# SSH to server
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts

# Submit array job (40 subject-ROI pairs)
sbatch sbatch/run_srm_evaluation.sbatch

# Check job status
squeue -u haba6030
# Expected: 40 jobs running (or queued)

# Monitor specific job
tail -f logs/srm_eval_JOBID_1.out
```

**Job Details:**
- **Array size**: 40 tasks (10 subjects × 4 ROIs)
- **Memory**: 32GB per task (SRM is memory-intensive)
- **Time**: ~3 hours total
- **Output**: `results/srm_evaluation/TIMESTAMP/sub-{ID}_{ROI}_srm_results.json`

**Monitoring:**

```bash
# Check running jobs
squeue -u haba6030 | grep srm_eval

# Check completed tasks
ls results/srm_evaluation/*/sub-*_srm_results.json | wc -l
# Expected: 40 (when all jobs complete)

# Check for errors
grep -r "ERROR" logs/srm_eval_*.err
```

---

### Step 5: Aggregate Results

After all 40 jobs complete:

```bash
# On server
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts

# Find your results directory
RESULTS_DIR=$(ls -d results/srm_evaluation/20* | tail -1)
echo "Results directory: ${RESULTS_DIR}"

# Aggregate results
python aggregate_srm_results.py \
    --results-dir "${RESULTS_DIR}" \
    --output-dir "${RESULTS_DIR}"

# Expected output:
#   Saved ROI summary to results/.../summary_by_roi.json
#   Saved recommendations to results/.../optimal_k_recommendations.json
#   Saved overall summary to results/.../summary_all_subjects.json
```

**Aggregation Output:**
```
SRM EVALUATION SUMMARY
================================================================================

V1 (n=10 subjects)
----------------------------------------
Procrustes Baseline:
  RDM correlation: 0.174 ± 0.144
  Decoding accuracy: 58.3% ± 21.2%

SRM (optimal k=50):
  RDM correlation: 0.185 ± 0.150
  Decoding accuracy: 61.2% ± 19.8%

Improvement:
  RDM: +0.011 (+6.3%)
  Accuracy: +0.029 (+5.0%)
  Improved subjects: 7/10 (70.0%)

Statistical Test:
  RDM: t=2.134, p=0.0412 *

Recommendation: Use SRM
  SRM improves RDM by 6.3% (threshold: 5%)

[... V2, V3, hV4 summaries ...]
```

---

### Step 6: Generate Visualizations

```bash
# On server (same session)
python visualize_srm_comparison.py \
    --summary-dir "${RESULTS_DIR}" \
    --output-dir "${RESULTS_DIR}/visualizations"

# Expected output:
#   Saved performance comparison to visualizations/srm_vs_procrustes_performance_by_roi.png
#   Saved feature tuning curves to visualizations/feature_tuning_curves_all_rois.png
#   Saved improvement distribution to visualizations/improvement_distribution_by_roi.png
#   Saved optimal k recommendations to visualizations/optimal_k_recommendations.png
#   Saved winner summary to visualizations/srm_winner_summary.png
```

---

### Step 7: Download Results to Local Machine

```bash
# From local machine
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation

# Download entire results directory
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/results/srm_evaluation/TIMESTAMP ./results/

# Or download only summaries and visualizations
scp haba6030@node2:/scratch/.../results/srm_evaluation/TIMESTAMP/summary_*.json ./results/
scp -r haba6030@node2:/scratch/.../results/srm_evaluation/TIMESTAMP/visualizations ./results/
```

---

### Step 8: Between-Subject Analysis (HC vs CVD)

After within-subject analysis completes:

```bash
# On server
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts

# Run between-subject analysis for each ROI
for ROI in V1 V2 V3 hV4; do
    echo "Processing ${ROI}..."
    python evaluate_srm_between_subject.py \
        --roi "${ROI}" \
        --output-dir "results/srm_between_subject/$(date +%Y%m%d_%H%M%S)" \
        2>&1 | tee "logs/srm_between_${ROI}.log"
done

# Expected runtime: ~30 min per ROI (2 hours total)
```

**Between-Subject Output:**
```
Between-Subject SRM Evaluation: V1
================================================================================
SRM features: 50

[1/6] Loading data...
  HC subjects: ['sub-01', 'sub-02', ..., 'sub-06'] (n=6)
  CVD subjects: ['sub-08', 'sub-09', 'sub-10'] (n=3)

[4/6] Computing Procrustes disparities...
  HC disparities: 245.32 ± 62.15 (n=6)
  CVD disparities: 312.45 ± 78.23 (n=3)
  t-test: t=-1.823, p=0.0891

[5/6] Computing inter-subject RDM similarities...
  HC-HC RDM correlation: 0.143 ± 0.082 (n=15)
  CVD-CVD RDM correlation: 0.098 ± 0.045 (n=3)
  HC-CVD RDM correlation: 0.076 ± 0.063 (n=18)

=== SUMMARY ===
CVD differs from HC: False (p=0.0891, ns)
```

---

## Expected Results & Decision Criteria

### Scenario 1: SRM Substantially Improves (Expected)

**Metrics:**
- RDM improvement: +5-15% over Procrustes
- Decoding improvement: +3-8%
- Optimal k: 30-100 (depending on ROI)

**Decision:** ✅ **Adopt SRM as standard alignment**

**Pipeline Update:**
```python
# Production pipeline
1. Preprocessing (fMRIPrep)
2. Whitening (Phase 2) ← MANDATORY
3. SRM alignment with optimal k ← ADOPT
4. RDM analysis
```

---

### Scenario 2: SRM Minimal Improvement (<5%)

**Metrics:**
- RDM improvement: +1-4%
- Marginal statistical significance

**Decision:** ⚠️ **Use Procrustes (simpler, faster)**

**Rationale:**
- SRM computational cost not justified for <5% improvement
- Procrustes preserves full voxel space interpretability

---

## Troubleshooting

### Error: BrainIAK not available

```bash
# Solution
conda activate nilearn
conda install -c brainiak -c conda-forge brainiak
```

### Error: Whitening results not found

```
ERROR: Whitening results directory not found: .../TIMESTAMP_PLACEHOLDER
```

**Solution:** Update placeholder paths (see Configuration section)

### Error: Out of Memory (OOM)

```
slurmstepd: error: Detected 1 oom-kill event(s) in step XXXX
```

**Solution:** Increase memory in sbatch script:
```bash
#SBATCH --mem=48G  # Increase from 32G to 48G
```

### Error: Array job not starting

**Check node availability:**
```bash
squeue -w node2  # Check if node2 is busy
sinfo -N -l      # Check node status
```

**Solution:** Wait for node to free up, or use alternative node (if available)

---

## Performance Expectations

**Within-Subject SRM (40 jobs):**
- Total time: ~3 hours (all jobs in parallel)
- Peak memory: 20-30GB per job
- Success rate: >95% (38-40 successful jobs)

**Between-Subject SRM (4 ROIs):**
- Total time: ~2 hours (sequential)
- Memory: 16-24GB
- Success rate: 100%

**Total Phase 3 Time:** ~5 hours (mostly automated)

---

## Output Structure

```
results/srm_evaluation/TIMESTAMP/
├── sub-01_V1_srm_results.json          # Individual results (40 files)
├── ...
├── summary_by_roi.json                 # ROI-level aggregation
├── optimal_k_recommendations.json      # Best k per ROI
├── summary_all_subjects.json           # Overall summary
└── visualizations/
    ├── srm_vs_procrustes_performance_by_roi.png
    ├── feature_tuning_curves_all_rois.png
    ├── improvement_distribution_by_roi.png
    ├── optimal_k_recommendations.png
    └── srm_winner_summary.png

results/srm_between_subject/TIMESTAMP/
├── V1_srm_between_subject_results.json
├── V1_hc_cvd_disparity_comparison.png
├── V1_rdm_similarity_matrix.png
└── [same for V2, V3, hV4]
```

---

## Quick Reference Commands

```bash
# Upload scripts
scp analysis/validation/scripts/*.py haba6030@node2:/scratch/.../scripts/

# Submit array job
sbatch sbatch/run_srm_evaluation.sbatch

# Monitor progress
watch -n 10 'squeue -u haba6030 | grep srm_eval | wc -l'

# Aggregate results
python aggregate_srm_results.py --results-dir results/srm_evaluation/TIMESTAMP/

# Visualize
python visualize_srm_comparison.py --summary-dir results/srm_evaluation/TIMESTAMP/

# Download
scp -r haba6030@node2:/scratch/.../results/srm_evaluation/TIMESTAMP ./results/
```

---

## Next Steps After Phase 3

1. **Review results**: Check `summary_all_subjects.json` for overall decision
2. **Update documentation**: Record optimal k values in `PostProcrustes_plan_0130.md`
3. **Prepare for publication**: Use visualizations in methods/results sections
4. **Update production pipeline**: If SRM improves >5%, adopt as standard
5. **Phase 4 (Optional)**: GLMsingle for improved beta estimation

---

## Contact & Support

**Issues**: Report in `/analysis/validation/TROUBLESHOOTING.md`
**Questions**: Check `/analysis/validation/PostProcrustes_plan_0130.md` for theoretical background

---

**Status**: ✅ Ready for deployment after Phase 2 completes
**Last Tested**: Not yet (awaiting Phase 2 completion)
**Expected Completion**: Phase 3 scripts created 2026-02-05
