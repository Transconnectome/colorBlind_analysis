# Model Comparison Scripts

**Purpose**: Comprehensive validation of decoding models (plans_decoder.md)

---

## Current Status (2026-02-11)

### ✅ IMPLEMENTATION COMPLETE

**All Files**:
- `decoder_comparison_base.py` - Original 05_decoder_model_comparison.py (archived)
- `visualization_base.py` - Original 05c_decoder_visualization.py (archived)
- `config.py` - Configuration and paths ✅
- `run_model_comparison.py` - **Phase 1 COMPLETE** ✅
- `run_validation_tests.py` - **Phase 2 COMPLETE** ✅
- `visualize_comprehensive.py` - **Phase 3 COMPLETE** ✅
- `utils.py` - Shared utilities ✅

---

### ✅ All Models Implemented (6/6)

1. ✅ **LDA** (Linear Discriminant Analysis) - Current baseline
2. ✅ **Ridge Regression** - Linear with circular hue encoding (sin/cos)
3. ✅ **Kernel Ridge** - Non-linear with RBF kernel
4. ✅ **SVM** - Support Vector Machine with RBF kernel
5. ✅ **MLP** - Multi-Layer Perceptron with strong regularization
6. ✅ **Forward Encoding** - 6-channel forward model with basis functions

**Features**:
- ✅ LORO (Leave-One-Run-Out) cross-validation
- ✅ Nested hyperparameter tuning (no test leakage)
- ✅ Support for both `amplitudes_raw.npy` and `amplitudes_procrustes.npy`
- ✅ Circular metrics for hue continuity (0° = 360°)

---

### ✅ All Validation Tests Implemented (4/4)

1. ✅ **Permutation Test** (Section 6.2)
   - Label shuffle (1000 permutations)
   - Within-run shuffling to preserve temporal structure
   - P-values, z-scores per subject-ROI-model

2. ✅ **Bootstrap CI** (Section 6.4)
   - Subject-level bootstrap (group means)
   - Fold-level bootstrap (individual reliability)
   - 95% confidence intervals

3. ✅ **Test-Retest Reliability** (Section 6.3)
   - Split-half correlation (1000 iterations)
   - Spearman-Brown correction
   - Per model stability assessment

4. ✅ **Cross-Subject Generalization** (Section 6.5)
   - HC→HC (LOSO within HC group)
   - HC→CVD (Train on all HC, test on CVD)
   - Bootstrap difference test, Mann-Whitney U
   - **Answers**: "Is voxel-to-color mapping common across groups?"

---

### ✅ All Visualizations Implemented (4/4)

- ✅ **Section 7.5**: Permutation test panels (2×3 grid, 6 models)
- ✅ **Section 7.6**: Fold distribution violin plots (within-subject variability)
- ✅ **Section 7.7**: Cross-subject generalization (barplot with significance)
- ✅ **Section 7.8**: Comprehensive 6-panel summary (publication-ready)

---

## Data Structure

### Current (decoder_comparison_base.py)
**Data source**: Variable paths via arguments
```
baseline_dir/analysis/phase1_preprocess_decoding/{dataset}/results/baseline_decoding/{timestamp}/
└── sub-{ID}/{ROI}/amplitudes_z.npy
```

### Target (full_dataset_C010)
**Data source**: Fixed baseline directory
```
full_dataset_C010/
├── sub-01/
│   ├── V1/
│   │   ├── amplitudes_raw.npy          # (6, 8, n_voxels) - Before Procrustes
│   │   ├── amplitudes_procrustes.npy   # (6, 8, n_voxels) - After Procrustes
│   │   ├── metrics.json                # RDM reliability, disparity
│   │   └── config.json                 # Pipeline: P3, confounds: C010
│   ├── V2/
│   ├── V3/
│   └── V4/
├── sub-02/
...
└── sub-10/
```

**Key change**:
- Old: `amplitudes_z.npy` (z-scored amplitudes)
- New: `amplitudes_raw.npy` / `amplitudes_procrustes.npy` (raw and aligned)

---

## Implementation Summary

### ✅ Phase 1: Decoder Models (COMPLETE)
**File**: `run_model_comparison.py`

**Implemented**:
- ✅ Updated data loading for `full_dataset_C010` structure
- ✅ Added LDA, KernelRidge, SVM decoder classes
- ✅ Unified LORO CV function for all 6 models
- ✅ Support for both `raw` and `procrustes` alignment
- ✅ Nested hyperparameter tuning with inner CV
- ✅ Comprehensive metrics (acc_exact, acc_45, acc_90, MAE, MedAE)

**Output**: `{timestamp}/sub-{ID}_performance_raw.json` per subject

---

### ✅ Phase 2: Validation Tests (COMPLETE)
**File**: `run_validation_tests.py`

**Implemented**:
1. ✅ **Permutation test**:
   - Within-run label shuffling (1000 permutations)
   - Null distribution, p-value, z-score per subject-ROI-model
   - Output: `permutation_test.json`

2. ✅ **Bootstrap CI**:
   - Subject-level bootstrap for group means (1000 iterations)
   - 95% confidence intervals
   - Output: `bootstrap_ci.json`

3. ✅ **Test-retest reliability**:
   - Split-half correlation (1000 iterations)
   - Spearman-Brown correction
   - Output: `reliability.json`

4. ✅ **Cross-subject generalization**:
   - HC→HC (LOSO within HC, 7 subjects)
   - HC→CVD (Train on HC, test on CVD, 3 subjects)
   - Bootstrap difference + Mann-Whitney U test
   - Output: `cross_subject_generalization.json`

---

### ✅ Phase 3: Comprehensive Visualization (COMPLETE)
**File**: `visualize_comprehensive.py`

**Implemented**:
- ✅ Section 7.5: Permutation test panels (2×3 grid)
- ✅ Section 7.6: Fold distribution violin plots
- ✅ Section 7.7: Cross-subject generalization barplot
- ✅ Section 7.8: Comprehensive 6-panel summary

**Outputs**: All figures in `{timestamp}/figures/`

---

### ✅ Utilities (COMPLETE)
**File**: `utils.py`

**Implemented**:
- ✅ Circular math functions (circular_diff_deg, labels_to_hue, hue_to_labels)
- ✅ Data loading (load_amplitudes from full_dataset_C010)
- ✅ Statistics (bootstrap_ci, spearman_brown_correction)
- ✅ Model type classification (is_linear_model, uses_labels)
- ✅ Chance levels, summary statistics, group classification

---

## Directory Structure

```
model_comparison/
├── README.md                          # This file
├── config.py                          # Configuration (paths, subjects, ROIs, hyperparameters)
├── decoder_comparison_base.py         # Original 05_decoder_model_comparison.py
├── visualization_base.py              # Original 05c_decoder_visualization.py
│
├── run_model_comparison.py            # [Phase 1] Extended model comparison (6 models)
├── run_validation_tests.py            # [Phase 2] 4 validation tests
├── visualize_comprehensive.py         # [Phase 3] Comprehensive visualization
│
└── utils.py                           # Shared helper functions
```

---

## Workflow

### Step 1: Run Model Comparison (Phase 1)
```bash
# Single subject test
python run_model_comparison.py \
    --baseline_dir /path/to/full_dataset_C010 \
    --output_dir ./results/model_comparison \
    --subject 01 \
    --rois V1 V2 V3 V4 \
    --models LDA Ridge KernelRidge SVM MLP ForwardEncoding \
    --alignment both

# All subjects (SLURM array)
sbatch run_model_comparison.sbatch
```

**Outputs**:
- `{timestamp}/sub-{ID}_performance_raw.json` (per subject)
- `{timestamp}/performance_summary.json` (aggregated)

---

### Step 2: Run Validation Tests (Phase 2)
```bash
python run_validation_tests.py \
    --baseline_dir /path/to/full_dataset_C010 \
    --performance_dir {timestamp} \
    --output_dir {timestamp}
```

**Outputs**:
- `{timestamp}/permutation_test.json`
- `{timestamp}/bootstrap_ci.json`
- `{timestamp}/reliability.json`
- `{timestamp}/cross_subject_generalization.json`

---

### Step 3: Generate Visualizations (Phase 3)
```bash
python visualize_comprehensive.py \
    --results_dir {timestamp} \
    --output_dir {timestamp}/figures
```

**Outputs**: All figures in `{timestamp}/figures/`

---

## Key Design Decisions

### 1. Data Format
- **Original**: `amplitudes_z.npy` (z-scored)
- **New**: `amplitudes_raw.npy` / `amplitudes_procrustes.npy` (unnormalized)
- **Reason**: Need both before/after Procrustes for alignment effect analysis

### 2. Model Classes
- All models follow same interface: `fit(X, y)` and `predict(X)`
- Circular hue encoding (sin/cos) for continuous models (Ridge, MLP)
- Label-based for classification models (LDA, SVM)

### 3. Hyperparameter Tuning
- Nested CV: Inner loop on training set only (no test leakage)
- Simple grid search for smaller models (LDA, Ridge)
- Reduced grid for expensive models (KernelRidge, SVM, MLP)

### 4. Validation Tests
- **Permutation**: Within-run shuffle to preserve temporal structure
- **Bootstrap**: Subject-level for group means, fold-level for individuals
- **Reliability**: Split-half with Spearman-Brown correction
- **Generalization**: LOSO (Leave-One-Subject-Out) for fairness

---

## References

- **Original code**: `analysis/validation/scripts/05_decoder_model_comparison.py`
- **Plan document**: `analysis/validation/plans_decoder.md`
- **Baseline data**: `analysis/phase1_preprocess_decoding/results/full_dataset_C010`
- **Baseline analysis**: `analysis/phase1_preprocess_decoding/analyze_c010_residuals_procrustes_effects.py`

---

## Notes

- **Server vs Local**: Use `config.py` to switch between paths
- **Dependencies**: sklearn, scipy, numpy, matplotlib (no seaborn on server)
- **SLURM**: Array jobs for parallelizing across subjects
- **Memory**: ~2-4GB per subject-ROI for MLP and KernelRidge models

---

## Testing & Next Steps

### Local Testing (Single Subject)
```bash
# Test run_model_comparison.py
python run_model_comparison.py \
    --baseline_dir /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/full_dataset_C010 \
    --output_dir ./test_results \
    --subject 01 \
    --rois V1 \
    --models LDA Ridge \
    --alignment procrustes

# Test run_validation_tests.py
python run_validation_tests.py \
    --baseline_dir .../full_dataset_C010 \
    --performance_dir ./test_results/{timestamp} \
    --output_dir ./test_results/{timestamp} \
    --alignment procrustes \
    --tests permutation bootstrap

# Test visualize_comprehensive.py
python visualize_comprehensive.py \
    --results_dir ./test_results/{timestamp} \
    --output_dir ./test_results/{timestamp}/figures \
    --alignment procrustes
```

### Server Deployment

1. Upload to server:
```bash
scp run_model_comparison.py run_validation_tests.py visualize_comprehensive.py utils.py config.py \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/model_comparison/
```

2. Create SLURM scripts for array jobs (see CLAUDE.md for SLURM configuration)

3. Run on all subjects:
```bash
# Phase 1: Model comparison (array job, one subject per task)
sbatch run_model_comparison.sbatch

# Phase 2: Validation tests (single job after Phase 1 completes)
sbatch run_validation_tests.sbatch

# Phase 3: Visualization (local, after downloading results)
python visualize_comprehensive.py --results_dir {timestamp} --output_dir {timestamp}/figures
```

---

**Status**: ✅ **IMPLEMENTATION COMPLETE** - Ready for testing and deployment
**Last updated**: 2026-02-11
