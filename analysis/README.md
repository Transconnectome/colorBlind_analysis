# Analysis Pipeline for fMRIPrep method3_header_mi

## Overview

Complete analysis pipeline for fMRIPrep method3_header_mi dataset covering three research questions:

- **RQ1**: Neural Color Discrimination Despite Retinal Deficits
- **RQ2**: Inter-Individual Heterogeneity in CVD
- **RQ3**: Neural-Guided Personalized Filter Design

## Dataset: method3_header_mi

### Data Paths

- **fMRIPrep**: `/storage/connectome/haba6030/fmriprep_out_method3_header_mi`
  - FreeSurfer removed (`--fs-no-reconall`)
  - MI-based coregistration with header optimization
  - MNI152NLin2009cAsym 2mm
- **Events**: `/storage/connectome/haba6030/bids_editted/`
  - 8 colors × 6 runs per subject, RSVP (500ms/stimulus)

### Quality Metrics

From preprocessing diagnosis (analysis/prep_trials/results/):

- **Registration method**: Mutual Information (MI) cost function with header optimization
- **Improvement**: Optimized for accurate anatomical-functional alignment
- **See**: `analysis/prep_trials/README.md` for detailed comparison with previous methods

### Subject Groups

All 10 subjects should have improved registration quality with MI-based coregistration:

**Non-CVD subjects**: sub-01, sub-02, sub-03, sub-04, sub-05, sub-06, sub-07 (7 subjects)
**CVD subjects**: sub-08, sub-09, sub-10 (3 subjects)

**Note**: The method3_header_mi dataset uses optimized MI-based registration that should provide more reliable alignment across all subjects compared to BBR-based methods.

## Preprocessing: C010 + Procrustes (Validated 2026-02-09)

**IMPORTANT**: Use C010 + Procrustes pipeline (NOT Baseline32). Validation shows nearly doubled performance.

Parameters validated through systematic comparison (analysis/validation/preprocess_Check/compare_with_previous.md):

```
Smoothing:          0mm
High-pass:          None (0.0 Hz)
Motion confounds:   None
CompCor:            None
1st-level drift:    None
2nd-level drift:    Per-run linear + constant (12 regressors: 6×linear + 6×constant)
Normalization:      None
Procrustes:         ESSENTIAL (align runs 1-5 to run 0)
PCA:                30 components
```

**Performance vs Baseline32**:
- RDM Reliability: 0.154-0.256 → **0.487** (+90-216%)
- Noise Ceiling: 0.434-0.609 → **0.613**
- Ceiling Utilization: 41.3% → **79.4%** (+37.7 pp)

**Rationale**:
- No smoothing: Preserves voxel patterns for MVPA
- No high-pass: Redundant with 2nd-level drift regressors
- No motion/CompCor: Avoids over-correction and signal loss
- **2nd-level drift** (KEY): Captures session-wide temporal trends across 6 runs
- No normalization: Drift regressors handle baseline shifts
- **Procrustes alignment**: Essential for geometric alignment (16.4× improvement)
- PCA 30: Computational efficiency

**Critical**: 2nd-level drift regressors are the primary factor enabling 79% ceiling utilization. Do NOT use only 1st-level drift for multi-run sessions.

## Pipeline Structure

### Phase 0: Baseline Decoding

**0A. ROI Building** (`roi_pipeline_selected_1202used.py`)
- Extract V1, V2, V3, hV4 from Wang Atlas (2015)
- Transform to subject MNI space, apply functional mask
- Threshold: 50% atlas probability

**0B. QC Visualization** (`visualize_roi_overlay.py`)
- ROI alignment check on functional data

**0C. Baseline Analysis** (`fir_reconstruction_BH2009_system_clean.py`)
- **1st-level GLM**: FIR-based HRF estimation (8 delays, 12s window, NO drift)
- Voxel selection: Top 50% by FIR R²
- **2nd-level GLM**: HRF + derivative + **2nd-level drift** (12 regressors: 6×linear + 6×constant)
  - **CRITICAL**: Per-run drift regressors capture session-wide temporal trends
  - Design matrix: (n_scans_total, 28) = [8 HRF + 8 deriv + 12 drift]
- **Procrustes alignment**: Align runs 1-5 to run 0 (ESSENTIAL step)
- Forward encoding (6 half-wave rectified channels, 60° FWHM)
- Leave-one-run-out cross-validation
- Outputs: amplitudes_raw.npy, amplitudes_procrustes.npy, classification/reconstruction results

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

**Execute:**
```bash
bash run_complete_pipeline_parallel.sh
```

Execution details:
- Phase 0: 10 array tasks (1 per subject), each processes 4 ROIs (8-12h per task)
- Phase 1-4: Auto-starts after Phase 0, sequential (2-4h)


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
├── BH2009_method3_header_mi/C010_procrustes_method3_header_mi/
│   ├── sub-01/{V1,V2,V3,hV4}/             # Subject-organized
│   │   ├── amplitudes_raw.npy             # (n_runs, 8, n_voxels) - NO z-score
│   │   ├── amplitudes_procrustes.npy      # After Procrustes alignment
│   │   ├── classification_results.txt
│   │   ├── reconstruction_results.txt
│   │   ├── roi_mask.nii.gz
│   │   └── figures/
│   └── ... (sub-02 through sub-10)
├── phase1_results/                        # RDM/RSA
│   └── rdm_analysis_{ROI}_C010_procrustes_method3_header_mi/
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

### Analysis Scripts in each directory
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

## Version History

**2026-02-09**: Preprocessing validation & C010 adoption (CURRENT)
- **VALIDATED**: C010 + Procrustes pipeline replaces Baseline32
- Performance: RDM reliability 0.487 (was 0.154-0.256), 79% ceiling utilization (was 41%)
- Key change: 2nd-level drift regressors (12 per run) + mandatory Procrustes alignment
- Evidence: analysis/validation/preprocess_Check/compare_with_previous.md
- Rationale: Session-wide temporal drift requires 2nd-level modeling for multi-run fMRI

**2026-01-22**: Dataset migration to method3_header_mi
- Updated dataset from original_v3 to method3_header_mi
- Improved registration: MI-based coregistration with header optimization
- All scripts and configs updated to use new dataset path
- Better alignment expected across all subjects

**2026-01-06**: Parallel execution implementation
- SLURM array jobs (10 subjects simultaneous)
- Runtime reduction: 83-131h → 10-16h
- Directory structure: `V3_Comprehensive/sub-{ID}/{ROI}/`
- Simplified paths: All scripts in ROOT
- Automatic dependencies: Phase 1-4 auto-starts

**2026-01-05**: Initial planning (DEPRECATED: Use C010 instead of Baseline32)
- Config: Baseline32 (replaced by C010 on 2026-02-09)
- Subjects: 10 (01-10)
- ROIs: V1, V2, V3, hV4

## References

- **Preprocessing Validation**: `analysis/validation/preprocess_Check/compare_with_previous.md` (C010 vs Baseline32)
- Registration Comparison: `analysis/prep_trials/README.md`
- Preprocessing Reports: `analysis/prep_trials/results/`
- Systematic Review: `docs/SYSTEMATIC_PREPROCESSING_ANALYSIS.md`
- Project README: `../README.md`
- Development Guide: `../CLAUDE.md`

---

Last Updated: 2026-02-09 (C010 + Procrustes validated)
