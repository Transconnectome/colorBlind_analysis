# SRM Analysis Pipeline

This directory contains all code and results for Shared Response Model (SRM) analysis of color representation in visual cortex.

## Overview

SRM is used for two main purposes:
1. **Within-subject alignment**: Compare SRM vs Procrustes for run-to-run alignment
2. **Between-subject alignment**: Enable HC-CVD comparison despite different voxel counts

## Directory Structure

```
srm/
├── README.md                              # This file
├── QUICK_START.md                         # Quick start guide
├── EXECUTION_GUIDE.md                     # Detailed execution instructions
├── IMPLEMENTATION_SUMMARY.md              # Technical implementation details
│
├── evaluate_srm_vs_procrustes.py          # Within-subject SRM evaluation
├── evaluate_srm_between_subject.py        # Between-subject HC-CVD comparison
├── aggregate_srm_results.py               # Aggregate results across subjects
├── visualize_srm_comparison.py            # Visualize SRM vs Procrustes
├── visualize_color_space_per_subject.py   # Per-subject color space plots
│
├── run_srm_local_test.sh                  # Test within-subject locally
├── run_srm_local_all.sh                   # Run all within-subject locally
├── run_srm_between_subject_local_test.sh  # Test between-subject locally
├── run_srm_between_subject_local_all.sh   # Run all between-subject locally
├── run_color_space_visualization.sh       # Visualize color spaces
│
├── utils/
│   └── srm_alignment.py                   # SRM alignment utilities
│
├── sbatch/
│   └── run_srm_evaluation.sbatch          # Server batch script
│
├── postSRM_procrustes/                    # Post-SRM Procrustes analysis
│   ├── README.md
│   ├── EXECUTION_GUIDE.md
│   ├── step1a_dimension_reduction_pca.py
│   ├── step2_iterative_procrustes.py
│   ├── compute_srm_metrics.py
│   ├── compare_procrustes_vs_srm.py
│   └── utils/
│
└── results/
    ├── SRM_SUMMARY.md                     # Results summary
    ├── BETWEEN_SUBJECT_RESULTS.md         # Between-subject results
    ├── srm_evaluation/                    # Within-subject results
    │   └── local_YYYYMMDD_HHMMSS/
    └── srm_between_subject/               # Between-subject results
        └── test_local_YYYYMMDD_HHMMSS/
```

## Quick Start

### 1. Within-Subject Evaluation (SRM vs Procrustes)

Test with 2 subject-ROI pairs:
```bash
cd srm
bash run_srm_local_test.sh
```

Run full analysis (all 10 subjects × 4 ROIs):
```bash
bash run_srm_local_all.sh
```

### 2. Between-Subject Evaluation (HC vs CVD)

Test with all 4 ROIs:
```bash
bash run_srm_between_subject_local_test.sh
```

Run full analysis:
```bash
bash run_srm_between_subject_local_all.sh
```

### 3. Visualization

Visualize color spaces per subject:
```bash
bash run_color_space_visualization.sh results/srm_between_subject/test_local_YYYYMMDD_HHMMSS
```

## Key Features

### Beta-based SRM
- Uses run-averaged betas: (n_voxels, 8 colors) per run
- Tests k ≤ 8 (constrained by n_colors)
- Recommended for limited samples (B&H 2013)
- Leave-one-run-out cross-validation

### HC-CVD Comparison
- Learns shared space from HC subjects (sub-01 to sub-06)
- Projects CVD subjects (sub-08 to sub-10) to common space
- Solves voxel count heterogeneity problem (V1: 129-429 voxels)
- Enables direct representational comparison

### Metrics Computed
- RDM correlation (Spearman)
- Decoding accuracy (LDA cross-validation)
- Between-group disparity (HC vs CVD)
- Split-half reliability

## Input Requirements

All scripts expect Phase 1 Baseline results:

```
BASELINE_RESULTS_DIR/
├── sub-{ID}/
│   └── {ROI}/
│       ├── amplitudes_z.npy                # (n_runs, n_colors, n_voxels)
│       ├── amplitudes_procrustes.npy       # Procrustes baseline
│       └── analysis_summary.json           # Metadata
```

**Local path**: `/Users/jinilkim/.../analysis/phase1_preprocess_decoding/results/baseline`
**Server path**: `/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/results/baseline`

## Output Structure

### Within-Subject Results
```
results/srm_evaluation/{TIMESTAMP}/
├── sub-{ID}_{ROI}_srm_results.json         # Full metrics
├── sub-{ID}_{ROI}_srm_k_tuning.png         # K-tuning curve
└── sub-{ID}_{ROI}_log.txt                  # Execution log
```

### Between-Subject Results
```
results/srm_between_subject/{TIMESTAMP}/
├── {ROI}_srm_between_subject_results.json  # HC-CVD comparison
├── {ROI}_hc_cvd_disparity_comparison.png   # Disparity plot
├── {ROI}_rdm_similarity_matrix.png         # Cross-subject RDM
└── {ROI}_color_space_per_subject.png       # MDS visualization
```

## Server Execution

Upload to server:
```bash
scp -r srm haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/
```

Submit batch job:
```bash
ssh node2
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/srm/sbatch
sbatch run_srm_evaluation.sbatch
```

Monitor progress:
```bash
watch -n 30 squeue -u haba6030
tail -f ../logs/srm_eval_*.out
```

## Dependencies

- **brainiak**: SRM implementation
- **numpy, scipy**: Core numerical computing
- **scikit-learn**: LDA decoding
- **matplotlib, seaborn**: Visualization

Install BrainIAK:
```bash
conda activate nilearn  # or srm
conda install -c brainiak -c conda-forge brainiak
```

## Key Parameters

### Feature Counts (k)
- **V1, V2, V3, hV4**: k = [2, 3, 4, 5, 6, 8]
- Optimal k typically 3-4 based on tuning results
- Constrained by n_colors = 8 (Beta-based SRM)

### Subject Groups
- **HC**: sub-01, sub-02, sub-03, sub-04, sub-05, sub-06
- **CVD**: sub-08, sub-09, sub-10
- **Excluded**: sub-07 (data quality)

## References

- Chen et al. (2015): A Reduced-Dimension fMRI Shared Response Model
- Buetti-Dinh & Haxby (2013): Beta-based SRM for limited samples
- Analysis adapted from Phase 1 Baseline (Procrustes alignment)

## Documentation

- **QUICK_START.md**: Minimal steps to run analysis
- **EXECUTION_GUIDE.md**: Detailed execution instructions with troubleshooting
- **IMPLEMENTATION_SUMMARY.md**: Technical implementation details and design decisions

## Troubleshooting

**Import Error: No module named 'brainiak'**
```bash
conda activate nilearn
conda install -c brainiak -c conda-forge brainiak
```

**FileNotFoundError: Baseline results not found**
- Ensure Phase 1 Baseline analysis is complete
- Check path in script matches your setup (local vs server)

**Memory Error during SRM**
- Reduce number of voxels (try voxel selection first)
- Use lower k values
- Increase SLURM memory allocation (--mem=64G)

**Poor SRM performance (RDM correlation < Procrustes)**
- Expected for some ROIs (V1 often shows similar performance)
- Check k-tuning plot for optimal feature count
- Verify input data quality (SNR, alignment)

## Results Summary

See `results/SRM_SUMMARY.md` and `results/BETWEEN_SUBJECT_RESULTS.md` for detailed findings.

**Key findings**:
- SRM comparable to Procrustes for within-subject alignment
- Between-subject SRM enables HC-CVD comparison
- Optimal k = 3-4 across ROIs
- CVD shows increased representational disparity vs HC reference
