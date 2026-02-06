# Between-Subject Procrustes with ANOVA Voxel Selection

## Overview

This directory implements an alternative between-subject alignment method using ANOVA-based voxel selection to address voxel count heterogeneity issues.

**Problem**: Current between-subject Procrustes fails due to different voxel counts across subjects (V1: 129-429 voxels), caused by per-subject problematic voxel filtering in baseline preprocessing.

**Solution**:
1. Disable problematic voxel filtering (keep R² filtering)
2. Find spatially corresponding voxels across all subjects
3. Select consistently color-discriminative voxels using ANOVA rankings
4. Apply between-subject Procrustes alignment

## File Structure

```
between_procrustes/
├── README.md                                    # This file
├── fir_reconstruction_no_voxel_filtering.py     # Modified preprocessing (no filtering)
├── run_preprocessing_unfiltered.sbatch          # SLURM script for preprocessing
├── run_pipeline_local.py                        # Main pipeline orchestration
├── evaluate_procrustes_anova.py                 # Between-subject evaluation
├── anova_voxel_selection.py                     # ANOVA aggregation
├── run_local_test.sh                            # Quick test (V1, k=50)
├── run_local_all.sh                             # Full analysis (all ROIs)
└── utils/
    ├── __init__.py
    └── voxel_correspondence.py                  # Coordinate matching utilities
```

## Modified Preprocessing (Phase 0)

### Key Modifications

**File**: `fir_reconstruction_no_voxel_filtering.py`

1. **KEEPS R² filtering** (lines 1189-1223):
   - Top 50% voxels by R² threshold
   - Ensures good HRF estimation quality
   - Result: Subjects still have different voxel counts (this is OK)

2. **DISABLES zero-variance/NaN filtering** (lines 1657-1702):
   - Handles NaN: replace with run-mean using `np.nan_to_num()`
   - Handles zero variance: mean-center only (no filtering)
   - All R²-filtered voxels are retained

3. **Output directory suffix**: `_unfiltered` to distinguish from original

### Expected Voxel Counts

- **Original** (R² + zero-var filtering): V1: 129-429 voxels (high heterogeneity)
- **Modified** (R² only): V1: 200-450 voxels (reduced heterogeneity, more common voxels)

### Server Execution

**Step 1: Upload modified preprocessing script**

```bash
# Single line - no line breaks
scp analysis/validation/scripts/between_procrustes/fir_reconstruction_no_voxel_filtering.py analysis/validation/scripts/between_procrustes/run_preprocessing_unfiltered.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/between_procrustes/
```

**Step 2: Create logs directory and run on server**

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/between_procrustes
mkdir -p logs

# Submit SLURM job
sbatch run_preprocessing_unfiltered.sbatch

# Monitor progress
squeue -u haba6030
tail -f logs/baseline_unfilt_*.log
```

**Expected runtime**: ~2-3 hours per subject-ROI (4 ROIs × 9 subjects = 36 jobs)

**Step 3: Download results**

```bash
# Single line - no line breaks
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/BH2009_deoblique_v2/baseline_unfiltered /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/deoblique_v2/results/baseline_decoding/fixed_perRun_unfiltered
```

## Pipeline Components

### Phase 1: Voxel Correspondence

**File**: `utils/voxel_correspondence.py`

**Key Functions**:
- `load_roi_mask_for_subject()`: Load ROI mask and extract MNI coordinates
- `find_common_voxels_across_subjects()`: Find voxel intersection across all subjects
- `load_unfiltered_amplitudes()`: Load amplitudes from modified preprocessing
- `extract_common_voxel_amplitudes()`: Get amplitudes for common voxels

**Expected**: ~100-200 common voxels for V1

### Phase 2: ANOVA Voxel Selection

**File**: `anova_voxel_selection.py`

**Key Functions**:
- `compute_per_subject_anova()`: Compute F-test per subject
- `aggregate_rankings_mean_rank()`: Aggregate rankings using Borda count
- `select_top_k_voxels()`: Select top-k by mean rank
- `compute_anova_selection_quality()`: Quality metrics

**Logic**:
1. For each subject: compute ANOVA F-statistic for color discrimination
2. Convert F-values to ranks (0 = best discriminative)
3. Compute mean rank across subjects (lower = more consistent)
4. Select top-k voxels by mean rank

### Phase 3: Between-Subject Procrustes

**File**: `evaluate_procrustes_anova.py`

**Key Functions**:
- `compute_between_subject_disparities()`: HC-HC vs CVD-HC disparities
- `compute_rdm_similarities()`: Within/between group RDM correlations
- `evaluate_procrustes_anova()`: Main evaluation pipeline

**Strategy**:
1. Compute HC reference: mean of HC subjects' averaged patterns
2. Align each HC subject to HC reference → HC-HC disparities
3. Align each CVD subject to HC reference → CVD-HC disparities
4. Statistical test: t-test, Cohen's d

## Running the Pipeline

### Quick Test (Recommended First)

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/scripts/between_procrustes

# Activate environment
conda activate nilearn

# Quick test with V1, k=50
./run_local_test.sh

# OR manually:
python run_pipeline_local.py --roi V1 --test-mode
```

**Expected runtime**: <5 minutes
**Expected output**: `results/V1_procrustes_anova_results.json`

### Full Analysis

```bash
# All ROIs, multiple k values
./run_local_all.sh

# OR manually:
python run_pipeline_local.py --roi V1 --k-values 20 50 100
python run_pipeline_local.py --roi V2 --k-values 20 50 100
python run_pipeline_local.py --roi V3 --k-values 20 50 100
python run_pipeline_local.py --roi hV4 --k-values 20 50 100
```

**Expected runtime**: ~20 minutes for all ROIs
**Expected output**: One JSON file per ROI in `results/`

### Custom Configuration

```bash
python run_pipeline_local.py \
    --roi V1 \
    --k-values 50 100 150 \
    --baseline-dir /path/to/baseline_unfiltered \
    --output-dir /path/to/output
```

## Output Structure

### Results JSON Format

```json
{
  "roi": "V1",
  "n_subjects_hc": 6,
  "n_subjects_cvd": 3,
  "k_values": [20, 50, 100],
  "results": {
    "50": {
      "hc_disparities": [...],
      "cvd_disparities": [...],
      "disparity_stats": {
        "hc_mean": 0.4123,
        "hc_std": 0.0823,
        "cvd_mean": 0.5234,
        "cvd_std": 0.1023
      },
      "ttest": {
        "t": 2.345,
        "p": 0.0234,
        "cohens_d": 0.823
      },
      "rdm_correlations": {
        "hc_hc": [...],
        "cvd_cvd": [...],
        "hc_cvd": [...],
        "hc_hc_mean": 0.67,
        "cvd_cvd_mean": 0.45,
        "hc_cvd_mean": 0.52
      },
      "selection_quality": {
        "mean_f_per_subject": {...},
        "mean_rank_coverage": 0.85,
        "min_rank_coverage": 0.75
      },
      "selected_voxel_indices": [...]
    }
  }
}
```

## Expected Outcomes

### Voxel Counts
- **Common voxels (intersection)**: ~100-200 voxels (V1)
- **After ANOVA selection (k=50)**: 50 voxels

### HC Reliability
- **HC-HC RDM correlation**: >0.60 (good alignment)
- **HC-HC mean disparity**: <0.40 (tight clustering)

### HC vs CVD Comparison
- **Expected**: CVD-HC disparity > HC-HC disparity
- **Statistical test**: p < 0.05 (independent samples t-test)
- **Effect size**: Cohen's d > 0.5 (medium effect)

## Troubleshooting

### Issue 1: Few Common Voxels

**Symptom**: `Common voxels: 25` (too few)

**Diagnosis**:
```bash
# Check voxel counts per subject
python -c "
from utils.voxel_correspondence import load_roi_mask_for_subject
from pathlib import Path
baseline_dir = Path('analysis/phase1_preprocess_decoding/deoblique_v2/results/baseline_decoding/fixed_perRun_unfiltered')
for i in range(1, 11):
    if i == 7: continue
    try:
        _, coords = load_roi_mask_for_subject(f'sub-{i:02d}', 'V1', baseline_dir)
        print(f'sub-{i:02d}: {len(coords)} voxels')
    except:
        print(f'sub-{i:02d}: NOT FOUND')
"
```

**Solution**:
- If voxel counts still vary widely: R² filtering may need adjustment
- If some subjects missing: re-run preprocessing for those subjects

### Issue 2: Baseline Directory Not Found

**Symptom**: `ERROR: Baseline directory not found`

**Solution**:
1. Check if preprocessing completed on server
2. Verify download path matches expected structure
3. Use `--baseline-dir` flag to specify correct path

### Issue 3: Low ANOVA Consistency

**Symptom**: `Rank std range: [50, 200]` (high variance)

**Diagnosis**: Voxels ranked very differently across subjects

**Solution**:
- This indicates heterogeneous color representation
- Try larger k values to capture more voxels
- Add metric: only select voxels with rank_std < threshold

## Validation Tests

### Unit Tests

```bash
# Test voxel correspondence
cd utils
python voxel_correspondence.py

# Test ANOVA selection
cd ..
python anova_voxel_selection.py
```

### Integration Test

```bash
# Quick test with V1
python run_pipeline_local.py --roi V1 --test-mode

# Expected output:
# - results/V1_procrustes_anova_results.json exists
# - HC disparities < CVD disparities
# - p-value < 0.05 (if effect exists)
```

## Comparison with SRM

After running this pipeline, compare results with SRM:

```bash
# Load both results
python -c "
import json
with open('results/V1_procrustes_anova_results.json') as f:
    procrustes_res = json.load(f)
with open('../results/srm_between_subject/V1_results.json') as f:
    srm_res = json.load(f)

# Compare disparities
proc_cvd = procrustes_res['results']['50']['disparity_stats']['cvd_mean']
srm_cvd = srm_res['cvd_disparity_mean']
print(f'Procrustes CVD disparity: {proc_cvd:.4f}')
print(f'SRM CVD disparity: {srm_cvd:.4f}')
"
```

## Next Steps

1. **Visualization**: Create plots comparing HC vs CVD disparities
2. **Statistical report**: Generate markdown summary of results
3. **Comparison analysis**: SRM vs Procrustes-ANOVA performance
4. **Hybrid approach**: ANOVA selection + SRM alignment
5. **Scale-up**: Run on server for all subjects and ROIs

## References

- **Original baseline**: `analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py`
- **Procrustes utilities**: `analysis/phase1_preprocess_decoding/utils/procrustes_normalized.py`
- **SRM between-subject**: `analysis/validation/scripts/evaluate_srm_between_subject.py`
- **ANOVA feature selection**: `analysis/phase1_preprocess_decoding/feature_selection/feature_selection_anova.py`
