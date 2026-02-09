# C010 Between-Subject SRM Analysis

**Created:** 2026-02-09
**Status:** Ready for execution
**Analysis Type:** HC vs CVD group comparison using validated C010+Procrustes data

---

## Quick Start

### Local Testing (Recommended First)
```bash
cd analysis/validation/SRM

# 1. Optional: Profile resources (measures memory/CPU usage)
bash test_c010_srm_resources.sh

# 2. Run analysis on all 4 ROIs
bash run_c010_between_subject_local.sh

# 3. Generate visualizations
python visualize_srm_c010_between_subject.py --results-dir results/c010/TIMESTAMP/
```

### Server Execution (For Full Analysis)
```bash
cd analysis/validation/SRM

# Upload scripts and submit SLURM job
bash upload_and_run_c010_srm.sh

# Monitor progress
ssh haba6030@node2 'squeue -u haba6030'

# Download results when complete
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/srm_c010_between_subject/TIMESTAMP/ ./results/c010/
```

---

## What's New

### Novel Dual Pipeline Approach
This analysis compares TWO methods for SRM input:

1. **Raw-Averaged SRM** (baseline):
   - Raw amplitudes → average across runs → SRM
   - RDM reliability: 0.042 ± 0.103

2. **Procrustes-Averaged SRM** (novel):
   - Procrustes-aligned amplitudes → average across runs → SRM
   - RDM reliability: 0.496 ± 0.227 (11.7× better!)

**Hypothesis:** Higher geometric stability → cleaner shared response → stronger HC-CVD separation

### Validated High-Quality Data
- **Preprocessing:** C010 (2nd-level drift removal)
- **Alignment:** Procrustes (cross-run geometric alignment)
- **Noise ceiling utilization:** 83.7% (vs 41% in Baseline32)
- **Subjects:** 10 total (HC n=7, CVD n=3)

---

## Files Created

### Core Analysis Scripts
- `evaluate_srm_c010_between_subject.py` - Main dual-pipeline SRM analysis
- `visualize_srm_c010_between_subject.py` - Visualization suite

### Execution Scripts
- `run_c010_between_subject_local.sh` - Local execution (4 ROIs)
- `sbatch/run_c010_between_subject.sbatch` - SLURM array job (conservative settings)
- `upload_and_run_c010_srm.sh` - Upload and submit workflow

### Resource Profiling
- `test_c010_srm_resources.sh` - Local resource test
- `test_c010_srm_server.sh` - Server resource test

### Documentation
- `C010_EXECUTION_GUIDE.md` - Detailed execution instructions
- `C010_BETWEEN_SUBJECT_RESULTS.md` - Results template and interpretation guide
- `C010_README.md` - This file

---

## Expected Outputs

### Results Structure
```
results/c010/TIMESTAMP/
├── V1_raw_srm_results.json
├── V1_procrustes_srm_results.json
├── V1_dual_comparison.json
├── V2_raw_srm_results.json
├── V2_procrustes_srm_results.json
├── V2_dual_comparison.json
├── V3_raw_srm_results.json
├── V3_procrustes_srm_results.json
├── V3_dual_comparison.json
├── V4_raw_srm_results.json
├── V4_procrustes_srm_results.json
├── V4_dual_comparison.json
└── visualizations/
    ├── V1_dual_disparity_comparison.png
    ├── V1_hc_cvd_boxplot.png
    ├── V2_dual_disparity_comparison.png
    ├── V2_hc_cvd_boxplot.png
    ├── V3_dual_disparity_comparison.png
    ├── V3_hc_cvd_boxplot.png
    ├── V4_dual_disparity_comparison.png
    ├── V4_hc_cvd_boxplot.png
    ├── summary_raw_vs_procrustes.png
    └── summary_hc_cvd_separation.png
```

### Key Metrics (per ROI, per method)
- **HC-to-HC disparity:** Within-group consistency
- **CVD-to-HC disparity:** Between-group difference
- **CVD-to-CVD disparity:** CVD internal consistency
- **Statistical tests:** t-test, p-value, Cohen's d
- **RDM similarities:** Within-HC, Within-CVD, Between-HC-CVD

---

## Research Questions

### Q1: Are HC and CVD groups significantly different?
**Expectation:** Yes, based on previous work (V2 d>6, V3 d>3)
**Evaluation:** Compare p-values and effect sizes across ROIs

### Q2: Does Procrustes-averaged SRM outperform Raw-averaged SRM?
**Expectation:** Yes, due to higher RDM reliability (0.496 vs 0.042)
**Evaluation:** Compare HC-CVD separation between methods

### Q3: Which ROIs show strongest group differences?
**Expectation:** V2, V3 (color-processing areas)
**Evaluation:** Rank ROIs by effect size and significance

---

## Configuration

### SRM Features (k) per ROI
- **V1:** k=4 (mid-range for early visual)
- **V2:** k=4 (color processing)
- **V3:** k=3 (fewer voxels, lower k)
- **V4:** k=4 (color-selective)

### SLURM Settings (Conservative)
```bash
--cpus-per-task=2       # SRM is memory-bound
--mem=16G               # Per task (adjust after profiling)
--array=1-4%2           # Max 2 concurrent (32GB total)
--qos=shared            # Node2/4 shared access
--time=2:00:00          # 2 hours per ROI (conservative)
```

**Total resource footprint:** 32GB peak (safe for node2's 450GB free)

---

## Validation & Quality Checks

### Before Running
- [ ] C010 data exists (`sub-01/V1/amplitudes_*.npy` present)
- [ ] BrainIAK installed (`pip install brainiak`)
- [ ] Conda environment activated (`conda activate nilearn`)

### After Running
- [ ] All 4 ROIs completed (12 JSON files total)
- [ ] Both pipelines executed (raw + procrustes)
- [ ] No NaN values in results
- [ ] Visualizations generated (10 PNG files)

### Quality Metrics
- [ ] CVD-to-HC > HC-to-HC (group difference detected)
- [ ] p-values reasonable (not all 0 or 1)
- [ ] Effect sizes (d) match expectations (V2, V3 large)
- [ ] Winner method (Raw/Procrustes) consistent across subjects

---

## Troubleshooting

### Common Issues

**"C010 data not found"**
→ Check path: `ls analysis/validation/preprocess_Check/full_dataset_C010_with_residuals/sub-01/V1/`

**"BrainIAK not available"**
→ Install: `pip install brainiak`

**SLURM OOM (Out of Memory)**
→ Run `test_c010_srm_server.sh` to measure actual usage, then adjust `--mem`

**Different voxel counts**
→ Expected! SRM handles heterogeneous dimensions by mapping to common k-dimensional space

---

## Next Steps After Analysis

1. **Review Results:** Fill in `C010_BETWEEN_SUBJECT_RESULTS.md` with actual values
2. **Interpret Findings:** Which method won? Are HC-CVD differences significant?
3. **Compare to Previous:** How do C010 results compare to Baseline32?
4. **Recommend Method:** Should future analyses use Procrustes averaging?

---

## Related Documentation

- **Plan:** See plan document for detailed rationale and expected outcomes
- **Execution Guide:** `C010_EXECUTION_GUIDE.md` for step-by-step instructions
- **Results Template:** `C010_BETWEEN_SUBJECT_RESULTS.md` for interpretation
- **C010 Validation:** `analysis/validation/preprocess_Check/` for data quality metrics

---

## Timeline

**Development:** ~4 hours (completed 2026-02-09)
**Resource Profiling:** ~10 minutes (single ROI test)
**Execution:** ~30-90 minutes (depending on concurrency)
**Visualization:** ~5 minutes
**Total:** ~1-2 hours from start to finish (after scripts are ready)

---

## Contact & Support

**For questions:**
- Check `C010_EXECUTION_GUIDE.md` for detailed instructions
- Review plan document for design rationale
- Check SLURM logs (`logs/c010_srm_*.err`) for error messages

**Data locations:**
- **Local:** `analysis/validation/preprocess_Check/full_dataset_C010_with_residuals/`
- **Server:** `/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010_hrf_analysis/`
- **Results:** `analysis/validation/SRM/results/c010/`

---

**Status:** ✅ Ready for execution
**Last Updated:** 2026-02-09
