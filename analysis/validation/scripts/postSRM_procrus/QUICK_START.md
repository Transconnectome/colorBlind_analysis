# Quick Start Guide

## 30-Second Overview

This pipeline computes **geometry-centered analysis** of color representations using:
- **PCA** to preserve geometry while reducing dimensions
- **Procrustes** to align to HC normative template
- **Crossnobis RDMs** for noise-corrected dissimilarity
- **Geometric metrics** to quantify HC consistency and CVD deviations

**Expected result**: HC shows circular color structure, CVD shows distortions (especially V2/V3)

---

## Local Test (5 minutes)

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus

./run_local_test.sh
```

**Check results**:
```bash
# Color wheel structure (should be circular for HC)
open results/step5_visualizations/V1_pca_diagnostics.png

# Statistics
cat results/step4_metrics/V1/hc_vs_cvd_statistics.json | grep -A5 "isc"
```

---

## Server Production (1-2 hours)

```bash
# 1. Upload
scp -r /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/

# 2. Update path (IMPORTANT!)
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/postSRM_procrus
nano step1a_dimension_reduction_pca.py
# Line 91: Change baseline-dir default to /scratch/connectome/haba6030/colorBlind/derivatives/baseline

# 3. Create logs
mkdir -p logs

# 4. Run
sbatch sbatch/run_full_pipeline_pca.sbatch

# 5. Monitor
squeue -u haba6030
tail -f logs/full_pipeline_pca_*.out
```

---

## Download Results

```bash
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/postSRM_procrus/results \
    /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/postSRM_procrus/
```

---

## Key Files to Check

**After each step**:
- Step 1: `results/step1_pca/V1/sub-01_metadata.json` → cumulative_variance >0.8
- Step 2: `results/step2_procrustes/V1/convergence_history.json` → converged in 3-5 iter
- Step 3: `results/step3_rdms/V1/sub-01_split_half_reliability.json` → reliability >0.5
- Step 4: `results/step4_metrics/V1/hc_vs_cvd_statistics.json` → check p-values
- Step 5: `results/step5_visualizations/V1_pca_diagnostics.png` → circular color wheel?

**Key metrics** (in Step 4 JSON):
- `isc`: HC > CVD? (hypothesis)
- `deviation`: CVD > HC? (hypothesis)
- `circularity`: HC ≈ 0.9-1.0, CVD < HC? (hypothesis)

---

## Troubleshooting

**Issue**: Step 1 fails with "file not found"
→ Check baseline path matches your system

**Issue**: Step 2 doesn't converge
→ Normal if takes 5-10 iterations; increase `--max-iter 20` if needed

**Issue**: Step 3 reliability <0.3
→ Low SNR in this ROI; expected for some subjects; check if >80% have reliability >0.5

**Issue**: Step 5 no circular structure
→ Could be real effect; compare HC vs CVD plots

---

## Expected Results

**V1**: Minimal HC-CVD difference (low-level vision)
**V2/V3**: Maximum HC-CVD difference (color processing) ← **KEY RESULT**
**hV4**: Moderate difference (color-selective)

**HC subjects**: ISC 0.7-0.9, Circularity 0.85-0.95
**CVD subjects**: ISC 0.4-0.7, Circularity 0.70-0.90

---

## SRM Comparison (Optional)

**Compare with SRM using identical metrics**:

```bash
# 1. Compute SRM metrics
python compute_srm_metrics.py --roi V1 --srm-dir /path/to/srm/results

# 2. Compare methods
python compare_procrustes_vs_srm.py --roi V1

# 3. View comparison
open results/comparison/V1_method_comparison_barplot.png
```

**What you get**:
- Side-by-side HC vs CVD comparison (both methods)
- Per-subject correlation scatter plots
- Reliability comparison
- Summary table with "winner" for each metric

**Expected**: Procrustes-PCA shows higher reliability and better preserved geometry

**Guide**: `EXECUTION_GUIDE_SRM_COMPARISON.md`

---

## Need More Info?

- **Step-by-step details**: `EXECUTION_GUIDE.md`
- **Conceptual overview**: `README.md`
- **Implementation details**: `IMPLEMENTATION_SUMMARY.md`
- **SRM comparison**: `EXECUTION_GUIDE_SRM_COMPARISON.md`

---

## Commands Reference

**Local test**:
```bash
./run_local_test.sh
```

**Single step** (if needed):
```bash
python step1a_dimension_reduction_pca.py --subject 01 --roi V1
python step2_iterative_procrustes.py --roi V1 --method pca
python step3_compute_rdms_crossnobis.py --subject 01 --roi V1 --method pca
python step4_geometric_metrics.py --roi V1 --method pca
python step5_visualize_report.py --roi V1 --method pca
```

**Monitor server job**:
```bash
squeue -u haba6030                          # Job status
tail -f logs/full_pipeline_pca_*.out        # Live output
sacct -j JOBID --format=JobID,Elapsed,State # Job details
```

**Check results**:
```bash
ls results/step1_pca/V1/sub-*.json | wc -l         # Should be 9
cat results/step2_procrustes/V1/summary.json       # Convergence info
cat results/step4_metrics/V1/hc_vs_cvd_statistics.json | jq '.isc'  # ISC stats
```

---

**Status**: ✅ Ready to run!
