# Complete Analysis Pipeline for fMRIPrep original_v3

## Overview

This directory contains the comprehensive analysis pipeline for running all "original phases" analyses on the new fMRIPrep original_v3 dataset. This pipeline covers the primary research questions (RQ1-RQ3) from the project:

- **RQ1**: Neural Color Discrimination Despite Retinal Deficits
- **RQ2**: Inter-Individual Heterogeneity in CVD
- **RQ3**: Neural-Guided Personalized Filter Design

## Dataset Specification: original_v3

### Data Location

**fMRIPrep Output**: `/storage/connectome/haba6030/fmriprep_out_original_v3`
- FreeSurfer removed (`--fs-no-reconall`)
- BBR coregistration without FreeSurfer surface-based alignment
- Standard MNI152NLin2009cAsym space, 2mm resolution

**Events/Stimuli**: `/storage/connectome/haba6030/bids_editted/`
- Original BIDS-formatted event files
- 8 colors × 6 runs per subject
- RSVP task (500ms per stimulus)

### Quality Metrics

Based on preprocessing diagnosis report (docs/0104_Preprocessing_Report.md):

| Metric | Value | Previous (deoblique_v2) | Improvement |
|--------|-------|------------------------|-------------|
| **Dice coefficient (mean)** | 0.889 | 0.376 | +136% |
| **Pass rate (≥0.80)** | 83.3% | 0.0% | +83pp |
| **ROI generation failure** | 0.0% | 45.4% | Complete resolution |
| **Excellent runs (≥0.90)** | 73.3% | 0.0% | +73pp |

### Subject Tiers

#### Tier 1: Excellent (100% pass rate)
- **Subjects**: 01, 03, 04, 08, 09, 10 (6 subjects)
- **Dice**: 0.936-0.954 (mean ≥0.93)
- **Quality**: All 24 runs pass (Dice ≥0.80)
- **Motion**: < 0.2mm mean framewise displacement
- **Usage**: Primary analyses, publications

#### Tier 2: Good (83% pass rate)
- **Subjects**: 02, 05 (2 subjects)
- **Dice**: 0.823, 0.916
- **Quality**: 20/24 runs pass; 4 runs with Dice < 0.80
- **Usage**: Individual-level and group-level (with caution)
- **Recommendation**: Consider excluding bad runs

#### Tier 3: Partial (33% pass rate)
- **Subjects**: 06, 07 (2 subjects)
- **Dice**: 0.730, 0.746
- **Quality**: 8/24 runs pass; high run-to-run variability
- **Issue**: T1w brain mask over-extraction
- **Usage**: Individual-level (good runs only); exclude from group-level
- **Recommendation**: Supplementary analyses or case studies only

## Preprocessing Configuration: Baseline32

The analysis uses the **Baseline32** preprocessing configuration, which was determined through systematic preprocessing review (see docs/SYSTEMATIC_PREPROCESSING_ANALYSIS.md).

### Parameters

```bash
Smoothing:      0mm (no smoothing)
High-pass:      0.01 Hz
Motion:         cosine (6 cosine basis functions)
CompCor:        None
Drift:          none (handled by high-pass filter)
Standardize:    No (raw beta values preserved)
PCA:            30 components
```

### Rationale

- **No smoothing**: Preserves fine-grained voxel patterns for MVPA
- **High-pass 0.01 Hz**: Removes slow drifts while preserving task-related signal
- **Cosine motion**: Lightweight motion correction without over-correction
- **No CompCor**: Avoids removing task-related signal
- **No per-run standardization**: Preserves between-run amplitude differences
- **PCA 30**: Dimensionality reduction for computational efficiency

## Analysis Pipeline Structure

### Phase 0: ROI Building and Baseline Decoding

**0A. ROI Building** (`roi_pipeline_selected_1202used.py`)
- Extract V1, V2, V3, hV4 from Wang Atlas (2015)
- Transform to subject-specific MNI space
- Apply functional brain mask
- Threshold: 50% (atlas probability)

**0B. Overlay Visualization** (`visualize_roi_overlay.py`)
- QC check: ROI alignment on functional data
- Generate overlay figures for all subjects/ROIs

**0C. Baseline Reconstruction & Classification** (`fir_reconstruction_BH2009_system_clean.py`)
- FIR-based HRF estimation (8 delays, 12s window)
- Voxel selection: Top 50% by FIR R²
- 2nd-level GLM with HRF + derivative
- Forward encoding model (6 half-wave rectified channels)
- Leave-one-run-out cross-validation
- **Outputs**:
  - Classification accuracy (8-way)
  - Reconstruction error (circular angular error)
  - Channel amplitudes (z-scored)

### Phase 1: RDM/RSA Analysis

**Representational Similarity Analysis** (`phase1_rsa.py`)
- Compute 8×8 Representational Dissimilarity Matrices (RDM)
- Inter-subject RDM correlation (Spearman)
- Mantel test for statistical significance
- **Purpose**: Quantify consistency of neural color representation geometry across HC subjects

### Phase 2: Procrustes Analysis and CVD-HC Comparison

**2A. Procrustes Alignment** (`option2b_procrustes_alignment.py`)
- Reference-based alignment (sub-02 as reference)
- Compute HC super-participant template
- Alignment quality: Procrustes disparity, RDM correlation

**2B. HC Training** (`reconstruction_with_procrustes.py --mode train`)
- Learn common W matrix across aligned HC subjects
- Outputs: Shared decoder for HC group

**2C. CVD Testing** (`reconstruction_with_procrustes.py --mode test`)
- Apply Procrustes alignment to CVD subjects
- Test with HC common W matrix
- Evaluate CVD→HC transformation quality

**2D. Systematic CVD-HC Comparison** (`option2d_procrustes_cvd_comparison.py`)
- Three-dimensional characterization:
  - **Magnitude**: L2 norm differences
  - **Sign/Baseline**: Directional biases
  - **Structure**: RDM dissimilarity
- Procrustes disparity and reduction metrics

### Phase 3: Feature Selection

**ANOVA F-test Based Voxel Selection** (`feature_selection/feature_selection_anova.py`)
- **Purpose**: Core quality improvement step for voxel refinement
- **Method**: F-statistic calculation for each voxel
  - F = MSB / MSW (between-color variance / within-color variance)
  - Select voxels with high F-values (high color discriminability)
- **Note**: Complements baseline Top 50% voxels by FIR R² selection
- **Usage**: Runs on all subjects (10 subjects × 4 ROIs) to maximize information quality
- **Outputs**:
  - Selected voxel indices for different K values
  - F-values for all voxels
  - Classification accuracy vs K
  - Reconstruction error vs K
  - SNR statistics

### Phase 4: 3D Loss Function Optimization (Filter Learning)

**Personalized CVD→HC Filter Learning** (`scripts/phase2a_filter_learning/`)
- **Goal**: Learn linear transformation F = Y @ A + b to map CVD patterns to HC-like patterns
- **3-Dimensional Loss Function**:
  ```python
  L_total = λ_mag × L_magnitude + λ_base × L_baseline + λ_rdm × L_RDM
  ```
  - **L_magnitude**: Match color-wise L2 norms (overall activation strength)
  - **L_baseline**: Match color-wise mean activations (baseline shifts)
  - **L_RDM**: Match representational geometry (color discrimination structure)

**Pipeline Steps**:
1. **Pattern Extraction** (`phase2a_extract_patterns.py`)
   - Extract CVD and HC patterns from Procrustes-aligned data
   - Prepare training data for filter learning

2. **Filter Training** (`phase2a_train_filter.py`)
   - Initialize transformation with identity matrix
   - Optimize A and b using PyTorch gradient descent
   - Subject-specific weight tuning: (λ_mag, λ_base, λ_rdm)
   - Regularization: α × ||A - I||² + β × ||b||² (preserve structure)

3. **Filter Analysis** (`phase2a_analyze_results.py`)
   - Evaluate learned filters on validation data
   - Compute Procrustes disparity reduction
   - RDM similarity improvement
   - Reconstruction accuracy

**Outputs**:
- Learned transformation matrices (A, b) per CVD subject per ROI
- Training curves (loss, magnitude, baseline, RDM components)
- Validation metrics (disparity, RDM correlation)
- Transformed CVD patterns

## Running the Pipeline

### 1. Prepare Files (Local)

Update Python scripts to use original_v3 dataset:
```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# Files to modify:
# - analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py
# - roi_pipeline_selected_1202used.py
# - visualize_roi_overlay.py
```

### 2. Upload to Server

```bash
# Upload modified Python scripts
scp analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/

scp roi_pipeline_selected_1202used.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/

scp visualize_roi_overlay.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# Upload sbatch script
scp analysis/comprehensive_first_analysis.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### 3. Submit Job on Server

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# Submit the job
sbatch comprehensive_first_analysis.sbatch

# Monitor progress
tail -f logs/complete_pipeline_v3_*.out

# Check job status
squeue -u haba6030
```

### 4. Monitor Execution

The pipeline logs progress for each phase:
- Phase 0A: ROI building status
- Phase 0B: Overlay visualization (non-critical)
- Phase 0C: Subject×ROI success/failure counts (40 total)
- Phase 1: RDM analysis per ROI (4 ROIs)
- Phase 2: Procrustes alignment, HC training, CVD testing, comparison

## Expected Runtime

| Phase | Description | Estimated Time |
|-------|-------------|----------------|
| **0A** | ROI Building | 5-10 min |
| **0B** | Overlay Visualization | 5-10 min |
| **0C** | Baseline Reconstruction | 80-120 hours |
|        | (10 subjects × 4 ROIs × 2-3 hrs) | |
| **1** | RDM Analysis | 40-80 min |
|        | (4 ROIs × 10-20 min) | |
| **2A-D** | Procrustes Analysis | 30-60 min |
| **3** | Feature Selection | 40-80 min |
|        | (10 subjects × 4 ROIs × 1-2 min) | |
| **4** | 3D Loss Optimization | 2-4 hours |
|        | (3 CVD × 4 ROIs × 20-40 min) | |
| **Total** | **~83-131 hours** | **(3.5-5.5 days)** |

**Note**: Phase 0C is the bottleneck (~95% of total time). Consider using array jobs for parallelization in future runs.

## Output Structure

Results are saved to the following directories:

```
/scratch/connectome/haba6030/colorBlind/derivatives/
├── BH2009_original_v3/
│   └── baseline32_original_v3/
│       ├── sm0.0_hpYe_moCo_ccNo_drNo_stFa_sub-01_V1_None/
│       │   ├── amplitudes_z.npy          # (n_runs, 8, n_voxels)
│       │   ├── classification_results.txt
│       │   ├── reconstruction_results.txt
│       │   ├── roi_mask.nii.gz
│       │   └── figures/
│       └── ... (40 subject-ROI combinations)
│
├── phase1_results/
│   ├── rdm_analysis_V1_baseline32_original_v3/
│   │   ├── rdm_similarity_matrix.npy
│   │   ├── mantel_test_results.txt
│   │   └── figures/
│   └── ... (4 ROIs)
│
├── phase2_procrustes/
│   ├── alignment_quality_metrics.txt
│   ├── hc_common_decoder_V1.npz
│   ├── cvd_procrustes_results_sub-08_V1.npz
│   └── ... (CVD subjects × ROIs)
│
├── feature_selection/
│   ├── anova_results_sub-01_V1.csv
│   ├── selected_voxels_sub-01_V1_k*.npy
│   └── ... (10 subjects × 4 ROIs)
│
└── phase3_filters/
    └── ... (moved to results/group_level/phase2a_data/models/)

/scratch/connectome/haba6030/colorBlind/results/
└── group_level/
    └── phase2a_data/
        ├── patterns/                      # Extracted CVD/HC patterns
        │   ├── cvd_sub-08_V1_patterns.npz
        │   └── hc_target_V1_patterns.npz
        └── models/                        # Learned filters
            ├── filter_sub-08_V1_model.pth
            ├── filter_sub-08_V1_metrics.json
            ├── training_curves_sub-08_V1.png
            └── ... (3 CVD × 4 ROIs)
```

## Key Files Modified

1. **`analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py`**
   - Added 'original_v3' dataset configuration
   - Updated argparse choices

2. **`roi_pipeline_selected_1202used.py`**
   - Updated FMRIPREP_DIR to point to fmriprep_out_original_v3
   - Updated DATA_DIR to bids_editted

3. **`visualize_roi_overlay.py`**
   - Updated FMRIPREP_DIR to point to fmriprep_out_original_v3

## Troubleshooting

### Common Issues

**Issue 1**: ROI generation fails
- **Check**: Brain mask overlap with atlas regions
- **Solution**: Verify fMRIPrep quality with Dice scores

**Issue 2**: Baseline reconstruction fails for specific subject-ROI
- **Check**: Sufficient voxels after thresholding (≥100 voxels recommended)
- **Solution**: Lower threshold or use Tier 1 subjects only

**Issue 3**: Phase 1 RDM analysis fails
- **Check**: Phase 0C completed successfully for all HC subjects
- **Solution**: Re-run Phase 0C for missing subjects

**Issue 4**: Procrustes alignment fails
- **Check**: Matching voxel counts across subjects
- **Solution**: Algorithm automatically truncates to minimum voxel count

### Log Files

- **Pipeline log**: `logs/complete_pipeline_v3_*.out`
- **Error log**: `logs/complete_pipeline_v3_*.err`
- **Phase-specific logs**: Check derivatives directories

### Contact

For questions about this analysis pipeline, refer to:
- **Main README**: `/Users/jinilkim/.../colorBlind_analysis/README.md`
- **CLAUDE.md**: Development guide and conventions
- **Preprocessing report**: `docs/0104_Preprocessing_Report.md`

## Version History

- **2026-01-05**: Initial creation for original_v3 dataset
- **Dataset**: fmriprep_out_original_v3 (FreeSurfer removed, Dice 0.889)
- **Configuration**: Baseline32 (sm0, hp0.01, cosine, PCA30)
- **Subjects**: All 10 (01-10)
- **ROIs**: V1, V2, V3, hV4

## References

- **Preprocessing Report**: docs/0104_Preprocessing_Report.md
- **Systematic Review**: docs/SYSTEMATIC_PREPROCESSING_ANALYSIS.md
- **Project README**: ../README.md
- **CLAUDE.md**: ../CLAUDE.md

---

**Last Updated**: 2026-01-05
