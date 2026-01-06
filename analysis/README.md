# Analysis Pipeline for fMRIPrep original_v3

## Overview

Complete analysis pipeline for fMRIPrep original_v3 dataset covering three research questions:

- **RQ1**: Neural Color Discrimination Despite Retinal Deficits
- **RQ2**: Inter-Individual Heterogeneity in CVD
- **RQ3**: Neural-Guided Personalized Filter Design

## Dataset: original_v3

### Data Paths

- **fMRIPrep**: `/storage/connectome/haba6030/fmriprep_out_original_v3`
  - FreeSurfer removed (`--fs-no-reconall`)
  - BBR coregistration, MNI152NLin2009cAsym 2mm
- **Events**: `/storage/connectome/haba6030/bids_editted/`
  - 8 colors × 6 runs per subject, RSVP (500ms/stimulus)

### Quality Metrics

From preprocessing diagnosis (docs/0104_Preprocessing_Report.md):

| Metric | Value | Previous | Improvement |
|--------|-------|----------|-------------|
| Dice coefficient (mean) | 0.889 | 0.376 | +136% |
| Pass rate (≥0.80) | 83.3% | 0.0% | +83pp |
| ROI failure rate | 0.0% | 45.4% | Resolved |

### Subject Tiers

**Tier 1 (100% pass)**: 01, 03, 04, 08, 09, 10
- Dice: 0.936-0.954
- All 24 runs pass
- Primary analyses

**Tier 2 (83% pass)**: 02, 05
- Dice: 0.823, 0.916
- 20/24 runs pass
- Use with caution

**Tier 3 (33% pass)**: 06, 07
- Dice: 0.730, 0.746
- 8/24 runs pass
- Supplementary only

## Preprocessing: Baseline32

Parameters determined through systematic review (docs/SYSTEMATIC_PREPROCESSING_ANALYSIS.md):

```
Smoothing:      0mm
High-pass:      0.01 Hz
Motion:         cosine (6 basis functions)
CompCor:        None
Drift:          none
Standardize:    No
PCA:            30 components
```

Rationale:
- No smoothing preserves voxel patterns for MVPA
- High-pass 0.01 Hz removes drift while preserving task signal
- Cosine motion correction avoids over-correction
- No CompCor/standardization preserves task-related signal
- PCA 30 for computational efficiency

## Pipeline Structure

### Phase 0: Baseline Decoding

**0A. ROI Building** (`roi_pipeline_selected_1202used.py`)
- Extract V1, V2, V3, hV4 from Wang Atlas (2015)
- Transform to subject MNI space, apply functional mask
- Threshold: 50% atlas probability

**0B. QC Visualization** (`visualize_roi_overlay.py`)
- ROI alignment check on functional data

**0C. Baseline Analysis** (`fir_reconstruction_BH2009_system_clean.py`)
- FIR-based HRF estimation (8 delays, 12s window)
- Voxel selection: Top 50% by FIR R²
- 2nd-level GLM with HRF + derivative
- Forward encoding (6 half-wave rectified channels, 60° FWHM)
- Leave-one-run-out cross-validation
- Outputs: Classification accuracy, reconstruction error, channel amplitudes

### Phase 1: RSA

**RDM Analysis** (`phase1_rsa.py`)
- 8×8 Representational Dissimilarity Matrices
- Inter-subject RDM correlation (Spearman)
- Mantel test significance
- Quantifies HC neural color representation consistency

### Phase 2: Procrustes & CVD-HC Comparison

**2A. Alignment** (`option2b_procrustes_alignment.py`)
- Reference-based alignment (sub-02)
- HC super-participant template
- Quality metrics: Procrustes disparity, RDM correlation

**2B. HC Training** (`reconstruction_with_procrustes.py --mode train`)
- Learn common W matrix across aligned HC subjects

**2C. CVD Testing** (`reconstruction_with_procrustes.py --mode test`)
- Apply Procrustes to CVD subjects
- Test with HC W matrix

**2D. Systematic Comparison** (`option2d_procrustes_cvd_comparison.py`)
- 3D characterization: Magnitude (L2 norm), Sign/Baseline, Structure (RDM)

### Phase 3: Feature Selection

**ANOVA F-test** (`feature_selection_anova.py`)
- F = MSB / MSW voxel-wise
- Complements FIR R² selection
- All subjects (10 × 4 ROIs)
- Outputs: Voxel indices, F-values, accuracy vs K, SNR

### Phase 4: Filter Learning

**CVD→HC Transformation** (`phase2a_filter_learning/`)
- Goal: F = Y @ A + b mapping CVD to HC patterns
- Loss: L = λ_mag × L_magnitude + λ_base × L_baseline + λ_rdm × L_RDM
- Steps:
  1. Pattern extraction (`phase2a_extract_patterns.py`)
  2. Training (`phase2a_train_filter.py`): PyTorch gradient descent
  3. Analysis (`phase2a_analyze_results.py`)
- Outputs: Transformation matrices (A, b), training curves, metrics

## Execution

### Parallel Mode (Production)

Runtime: 10-16 hours (vs 83-131 sequential)

**Upload:**
```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# Python scripts (11 files)
scp roi_pipeline_selected_1202used.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp visualize_roi_overlay.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp analysis/phase2_baseline_comparing/phase1_rsa.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp analysis/phase2_procrustes_cvd_hc/option2b_procrustes_alignment.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp analysis/phase2_procrustes_cvd_hc/reconstruction_with_procrustes.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp analysis/phase2_procrustes_cvd_hc/option2d_procrustes_cvd_comparison.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp analysis/phase1_preprocess_decoding/feature_selection/feature_selection_anova.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp scripts/phase2a_filter_learning/phase2a_extract_patterns.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp scripts/phase2a_filter_learning/phase2a_train_filter.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp scripts/phase2a_filter_learning/phase2a_analyze_results.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# Execution scripts (3 files)
scp analysis/phase0_parallel.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp analysis/phase1to4_sequential.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp analysis/run_complete_pipeline_parallel.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

**Execute:**
```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
chmod +x run_complete_pipeline_parallel.sh
bash run_complete_pipeline_parallel.sh
```

Execution details:
- Phase 0: 10 array tasks (1 per subject), each processes 4 ROIs (8-12h per task)
- Phase 1-4: Auto-starts after Phase 0, sequential (2-4h)

**Monitor:**
```bash
squeue -u haba6030
tail -f logs/phase0_v3_sub-1_*.out
tail -f logs/phase1to4_v3_*.out
grep -h "Success:\|Failed:" logs/phase0_v3_sub-*_*.out | sort
```

### Sequential Mode (Debug Only)

Runtime: 83-131 hours

```bash
scp analysis/comprehensive_first_analysis.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
sbatch comprehensive_first_analysis.sbatch
tail -f logs/complete_pipeline_v3_*.out
```

## Runtime Breakdown

| Phase | Parallel | Sequential |
|-------|----------|------------|
| 0 (Baseline) | 8-12h (10 jobs) | 80-120h |
| 1 (RDM) | 40-80min | 40-80min |
| 2 (Procrustes) | 30-60min | 30-60min |
| 3 (Feature) | 40-80min | 40-80min |
| 4 (Filter) | 2-4h | 2-4h |
| **Total** | **10-16h** | **83-131h** |

## Output Structure

```
derivatives/V3_Comprehensive/
├── sub-{01-10}/roi_pipeline/              # ROI masks
│   ├── V1_mask_*.nii.gz
│   └── ... (V2, V3, hV4)
├── BH2009_original_v3/baseline32_original_v3/
│   ├── sub-01/{V1,V2,V3,hV4}/             # Subject-organized
│   │   ├── amplitudes_z.npy               # (n_runs, 8, n_voxels)
│   │   ├── classification_results.txt
│   │   ├── reconstruction_results.txt
│   │   ├── roi_mask.nii.gz
│   │   └── figures/
│   └── ... (sub-02 through sub-10)
├── phase1_results/                        # RDM/RSA
│   └── rdm_analysis_{ROI}_baseline32_original_v3/
├── phase2_procrustes/                     # Procrustes
│   ├── alignment_quality_metrics.txt
│   ├── hc_common_decoder_{ROI}.npz
│   └── cvd_procrustes_results_sub-{08,09,10}_{ROI}.npz
└── feature_selection/                     # ANOVA
    └── anova_results_sub-{ID}_{ROI}.csv

results/group_level/phase2a_data/
├── patterns/                              # Filter learning
│   ├── cvd_sub-{08,09,10}_{ROI}_patterns.npz
│   └── hc_target_{ROI}_patterns.npz
└── models/
    ├── filter_sub-{08,09,10}_{ROI}_model.pth
    ├── filter_sub-{08,09,10}_{ROI}_metrics.json
    └── training_curves_sub-{08,09,10}_{ROI}.png
```

## Execution Scripts

### Parallel (Production)
- `phase0_parallel.sbatch`: Array job (tasks 1-10), 8-12h per task
- `phase1to4_sequential.sbatch`: Auto-starts after Phase 0, 2-4h
- `run_complete_pipeline_parallel.sh`: Master orchestrator

### Sequential (Debug)
- `comprehensive_first_analysis.sbatch`: All phases, 83-131h

### Analysis Scripts (ROOT)
1. `roi_pipeline_selected_1202used.py`
2. `visualize_roi_overlay.py`
3. `fir_reconstruction_BH2009_system_clean.py`
4. `phase1_rsa.py`
5. `option2b_procrustes_alignment.py`
6. `reconstruction_with_procrustes.py`
7. `option2d_procrustes_cvd_comparison.py`
8. `feature_selection_anova.py`
9. `phase2a_extract_patterns.py`
10. `phase2a_train_filter.py`
11. `phase2a_analyze_results.py`

## Troubleshooting

### Common Issues

**ROI generation fails**
- Check: Brain mask overlap with atlas
- Solution: Verify Dice scores in preprocessing report

**Baseline fails for subject-ROI**
- Check: Voxel count ≥100 after thresholding
- Solution: Use Tier 1 subjects

**Phase 1 RDM fails**
- Check: Phase 0 completed for all HC subjects
- Solution: Re-run missing subjects

**Array task fails**
- Check: `grep "Failed:" logs/phase0_v3_sub-*_*.out`
- Solution: `sbatch --array=5 phase0_parallel.sbatch` (re-run task 5)

**Phase 1-4 pending**
- Check: `squeue -u haba6030`
- Reason: Waiting for all Phase 0 tasks
- Solution: If some failed, cancel and submit manually:
  ```bash
  scancel JOBID
  sbatch phase1to4_sequential.sbatch
  ```

**Out of memory**
- Check: Logs for "killed" or "out of memory"
- Solution: Edit sbatch `#SBATCH --mem=128GB`

### Log Files

Parallel:
- `logs/phase0_v3_sub-{1-10}_{JOBID}.out/err`
- `logs/phase1to4_v3_{JOBID}.out/err`

Sequential:
- `logs/complete_pipeline_v3_{JOBID}.out/err`

### Progress Check

```bash
# Phase 0 summary
grep -h "Success:\|Failed:" logs/phase0_v3_sub-*_*.out | sort

# Completed subjects
ls -lh derivatives/V3_Comprehensive/BH2009_original_v3/baseline32_original_v3/

# Count ROIs (should be 40)
find derivatives/V3_Comprehensive/BH2009_original_v3/baseline32_original_v3/ -name "amplitudes_z.npy" | wc -l
```

## Version History

**2026-01-06**: Parallel execution implementation
- SLURM array jobs (10 subjects simultaneous)
- Runtime reduction: 83-131h → 10-16h
- Directory structure: `V3_Comprehensive/sub-{ID}/{ROI}/`
- Simplified paths: All scripts in ROOT
- Automatic dependencies: Phase 1-4 auto-starts

**2026-01-05**: Initial planning
- Dataset: fmriprep_out_original_v3 (Dice 0.889)
- Config: Baseline32
- Subjects: 10 (01-10)
- ROIs: V1, V2, V3, hV4

## References

- Preprocessing Report: `docs/0104_Preprocessing_Report.md`
- Systematic Review: `docs/SYSTEMATIC_PREPROCESSING_ANALYSIS.md`
- Project README: `../README.md`
- Development Guide: `../CLAUDE.md`

---

Last Updated: 2026-01-06
