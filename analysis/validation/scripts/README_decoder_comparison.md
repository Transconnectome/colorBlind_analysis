# Decoder Model Comparison Pipeline

## Overview

This pipeline tests whether Procrustes alignment particularly helps linear models for color decoding.

**Main Questions:**
1. **Model Comparison**: Ridge vs Forward Encoding - which linear model is better?
2. **Alignment Effect**: Does alignment help linear models more than non-linear models?

**Models (Phase 1):**
- Ridge Regression (linear)
- Forward Encoding 6-channel (linear)
- Small MLP (non-linear)

## Files

### Python Scripts

1. **00_prepare_aligned_amplitudes.py**
   - Applies Procrustes alignment to test_zscore_FINAL baseline
   - Must be run before decoder comparison
   - Input: `amplitudes_z.npy` from baseline results
   - Output: Aligned `amplitudes_z.npy` + disparity metrics

2. **05_decoder_model_comparison.py**
   - Main comparison script
   - Runs LORO CV with nested hyperparameter tuning
   - Computes metrics: acc_45, acc_90, acc_exact, MAE, MedAE
   - Output: `sub-{ID}_performance_raw.json`

3. **05c_decoder_visualization.py**
   - Creates comparison plots
   - Before vs After alignment
   - Linear vs Non-linear interaction
   - Output: PNG figures + CSV summary table

### SLURM Scripts

1. **run_prepare_alignment.sbatch**
   - Prepares Procrustes-aligned data
   - Run once before all comparisons

2. **run_decoder_test_sub01.sbatch**
   - Test pipeline on sub-01 × 4 ROIs
   - Quick validation (< 30 min)
   - Run before full array job

3. **run_decoder_comparison.sbatch**
   - Full array job: 7 subjects × 4 ROIs = 28 tasks
   - Both before and after alignment
   - Run after sub-01 validation

## Workflow

### Step 0: Upload Scripts to Server

```bash
# From local machine
cd ~/Projects/colorBlind_analysis

# Upload all scripts at once
scp analysis/validation/scripts/*.py analysis/validation/scripts/*.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/
```

### Step 1: Prepare Aligned Amplitudes

```bash
# SSH to server
ssh node2

# Submit alignment job
cd /scratch/connectome/haba6030/colorBlind
sbatch analysis/validation/scripts/run_prepare_alignment.sbatch

# Check status
squeue -u haba6030

# After completion, check disparity values
cat analysis/validation/results/aligned_amplitudes/test_zscore_FINAL_procrustes/alignment_summary.json
```

**Expected output:**
```
aligned_amplitudes/test_zscore_FINAL_procrustes/
├── sub-01/
│   ├── V1/
│   │   ├── amplitudes_z.npy              # Aligned
│   │   ├── amplitudes_z_original.npy     # Backup
│   │   └── procrustes_info.json          # Disparity
│   ├── V2/ ...
│   ├── V3/ ...
│   └── hV4/ ...
├── sub-02/ ... (reference subject - disparity = 0)
├── ...
└── alignment_summary.json                # Overall summary
```

**Verify:**
- Disparity values should be < 1.0 (lower is better)
- Reference subject (sub-02) should have disparity = 0

### Step 2: Test on Sub-01

```bash
# Submit test job
sbatch analysis/validation/scripts/run_decoder_test_sub01.sbatch

# Monitor progress (should finish in ~20 min)
tail -f analysis/validation/logs/decoder_test_*.out

# Check for errors
tail analysis/validation/logs/decoder_test_*.err
```

**Validation checklist:**
- [ ] Both before and after jobs completed successfully
- [ ] JSON files created in both directories
- [ ] Accuracy > chance (12.5%)
- [ ] MAE < 90° (random guess)
- [ ] No Python errors or crashes

### Step 3: Download and Visualize Sub-01 Results

```bash
# From local machine
cd ~/Projects/colorBlind_analysis/analysis/validation

# Download test results
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/results/model_comparison/test_sub01_* \
    ./results/model_comparison/

# Run visualization locally
python scripts/05c_decoder_visualization.py \
    --before_dir results/model_comparison/test_sub01_before \
    --after_dir results/model_comparison/test_sub01_after \
    --subject 01 \
    --output_dir results/model_comparison/test_sub01_figures
```

**Expected figures:**
- `sub-01_performance_comparison.png`: Main 2×2 comparison
- `sub-01_roi_comparison.png`: Performance by ROI
- `sub-01_summary_table.csv`: Detailed metrics

**Validation:**
- [ ] After alignment shows improvement over before
- [ ] Linear models improve more than MLP (expected pattern)
- [ ] All ROIs show reasonable performance
- [ ] Figures render correctly

### Step 4: Run Full Array Job (After Validation)

```bash
# SSH to server
ssh node2

# Submit full array job (28 tasks)
cd /scratch/connectome/haba6030/colorBlind
sbatch analysis/validation/scripts/run_decoder_comparison.sbatch

# Monitor progress
squeue -u haba6030

# Check logs for any failures
tail analysis/validation/logs/decoder_comp_*_*.err
```

**Monitor:**
```bash
# Count completed tasks
ls analysis/validation/results/model_comparison/before_alignment/*.json | wc -l
ls analysis/validation/results/model_comparison/after_alignment/*.json | wc -l
# Should each have 28 files (7 subjects × 4 ROIs)
```

### Step 5: Download All Results

```bash
# From local machine
cd ~/Projects/colorBlind_analysis/analysis/validation

# Download all results
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/results/model_comparison/{before_alignment,after_alignment} \
    ./results/model_comparison/
```

### Step 6: Generate Visualizations for All Subjects

```bash
# Create figures for each subject
for SUBJECT in 01 02 03 05 06 07; do
    echo "Processing sub-${SUBJECT}..."

    python scripts/05c_decoder_visualization.py \
        --before_dir results/model_comparison/before_alignment \
        --after_dir results/model_comparison/after_alignment \
        --subject ${SUBJECT} \
        --output_dir results/model_comparison/figures_sub${SUBJECT}
done
```

## Expected Results

### Phase 1: Sub-01 Test

**Before Alignment:**
- Ridge: ~25-30% accuracy (acc_45)
- Forward Encoding: ~30-35% (6-channel prior helps)
- MLP: ~35-40% (non-linearity handles individual differences)

**After Alignment:**
- Ridge: ~50-60% (large improvement)
- Forward Encoding: ~55-65% (improvement)
- MLP: ~45-55% (smaller improvement)

**Key Pattern:**
- Δ(Ridge) > Δ(Forward Encoding) > Δ(MLP)
- **Conclusion**: Alignment particularly helps linear models

### Phase 2: All HC Subjects

**Expected Trends:**
1. V1 > V2 > V3 > hV4 (lower areas benefit more)
2. Linear models show larger alignment effects
3. Inter-subject consistency after alignment

## Troubleshooting

### Problem: Aligned data not found

**Solution:**
```bash
# Check if alignment step completed
ls analysis/validation/results/aligned_amplitudes/test_zscore_FINAL_procrustes/

# If missing, rerun alignment
sbatch analysis/validation/scripts/run_prepare_alignment.sbatch
```

### Problem: Python import errors

**Solution:**
```bash
# Verify conda environment
conda activate nilearn

# Check if utils are accessible
python -c "from analysis.utils.utils_color_decoding import circular_diff_deg; print('OK')"
```

### Problem: Out of memory

**Solution:**
Edit sbatch scripts to increase memory:
```bash
#SBATCH --mem=16G  # Increase to 24G if needed
```

### Problem: MLP fails to converge

This is usually due to:
- Too few voxels (< 100)
- Insufficient regularization

**Solution:** Already handled in code with:
- Strong regularization (alpha >= 0.01)
- Early stopping
- Adaptive learning rate

### Problem: Chance-level performance

Check:
1. Amplitudes data loaded correctly (not all zeros)
2. Label mapping is correct (8 colors, 45° spacing)
3. Enough voxels in ROI (check voxel count)

## Output Structure

```
analysis/validation/results/
├── aligned_amplitudes/
│   └── test_zscore_FINAL_procrustes/
│       ├── sub-01/ ... sub-07/
│       └── alignment_summary.json
│
├── model_comparison/
│   ├── test_sub01_before/
│   │   └── sub-01_performance_raw.json
│   ├── test_sub01_after/
│   │   └── sub-01_performance_raw.json
│   ├── test_sub01_figures/
│   │   ├── sub-01_performance_comparison.png
│   │   ├── sub-01_roi_comparison.png
│   │   └── sub-01_summary_table.csv
│   │
│   ├── before_alignment/
│   │   ├── sub-01_performance_raw.json
│   │   ├── sub-02_performance_raw.json
│   │   └── ... (28 files total)
│   │
│   ├── after_alignment/
│   │   └── ... (28 files)
│   │
│   └── figures_sub{01-07}/
│       └── ... (figures per subject)
│
└── logs/
    ├── prep_align_*.out
    ├── decoder_test_*.out
    └── decoder_comp_*_*.out
```

## Performance Metrics

### Classification Metrics
- **acc_45**: Accuracy within ±45° (adjacent colors)
- **acc_90**: Accuracy within ±90° (2 adjacent colors)
- **acc_exact**: Exact match accuracy (rarely used)

### Reconstruction Metrics
- **mae**: Mean Absolute Error (circular distance in degrees)
- **medae**: Median Absolute Error (robust to outliers)

### Chance Levels
- **Classification**: 1/8 = 12.5% (8 colors)
- **Reconstruction**: 90° (random uniform guess)

## Statistical Tests

### Paired t-test (Before vs After)
Tests whether alignment significantly improves performance.

### 2-way repeated measures ANOVA
- Factor 1: Alignment (Before, After)
- Factor 2: Model Type (Linear, Non-linear)
- **Critical**: Interaction effect tests if alignment helps linear models more

## Next Steps

After completing Phase 1 (3 models):

### Phase 2 (Optional Extensions):
1. Add Kernel Ridge, SVR (more non-linear models)
2. Split-half reliability analysis
3. Include CVD subjects for group comparison
4. Test on different baseline settings

### Publication Figures:
- 2×2 alignment effect (main result)
- ROI gradient (V1 > V2 > V3 > hV4)
- Individual subject consistency
- Statistical summary table

## Contact

For questions or issues:
1. Check logs in `analysis/validation/logs/`
2. Verify conda environment: `conda activate nilearn`
3. Check data paths in CLAUDE.md

## Citations

**Methods:**
- Ridge Regression: Hoerl & Kennard (1970)
- Forward Encoding Model: Brouwer & Heeger (2009, 2013)
- Procrustes Alignment: Gower & Dijksterhuis (2004)
- LORO Cross-validation: Varoquaux et al. (2017)
