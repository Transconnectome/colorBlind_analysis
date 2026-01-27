# Decoder Model Comparison - Quick Start Guide

## Overview

This pipeline tests: **"Does Procrustes alignment particularly help linear models?"**

**3 Models:**
- Ridge Regression (linear)
- Forward Encoding 6-channel (linear)
- Small MLP (non-linear)

**Expected Result:** Alignment should help linear models more than non-linear models.

## Files Created

### Python Scripts
1. `00_prepare_aligned_amplitudes.py` - Procrustes alignment preparation
2. `05_decoder_model_comparison.py` - Main comparison with LORO CV
3. `05c_decoder_visualization.py` - Visualization
4. `06_aggregate_results.py` - Group-level aggregation

### SLURM Scripts
1. `run_prepare_alignment.sbatch` - Alignment job
2. `run_decoder_test_sub01.sbatch` - Sub-01 test
3. `run_decoder_comparison.sbatch` - Full array job (28 tasks)

### Helpers
1. `workflow_helper.sh` - Interactive workflow menu
2. `README_decoder_comparison.md` - Detailed documentation
3. `QUICK_START.md` - This file

## Quick Workflow (Using Helper Script)

### Option 1: Interactive Menu (Recommended)

```bash
cd ~/Projects/colorBlind_analysis

# Run interactive helper
./analysis/validation/scripts/workflow_helper.sh

# Follow menu options 1-5 for sub-01 test
# Then options 6-8 for full pipeline
```

### Option 2: Manual Commands

#### Step 1: Upload Scripts
```bash
scp analysis/validation/scripts/*.py analysis/validation/scripts/*.sbatch \
    haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/scripts/
```

#### Step 2: Prepare Alignment (on server)
```bash
ssh node2
cd /scratch/connectome/haba6030/colorBlind
sbatch analysis/validation/scripts/run_prepare_alignment.sbatch
```

#### Step 3: Test on Sub-01 (on server)
```bash
sbatch analysis/validation/scripts/run_decoder_test_sub01.sbatch
# Wait ~20 minutes
```

#### Step 4: Download and Visualize (local)
```bash
# Download results
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/results/model_comparison/test_sub01_* \
    ./analysis/validation/results/model_comparison/

# Visualize
python analysis/validation/scripts/05c_decoder_visualization.py \
    --before_dir analysis/validation/results/model_comparison/test_sub01_before \
    --after_dir analysis/validation/results/model_comparison/test_sub01_after \
    --subject 01 \
    --output_dir analysis/validation/results/model_comparison/test_sub01_figures

# View figures
open analysis/validation/results/model_comparison/test_sub01_figures/*.png
```

#### Step 5: Full Pipeline (if sub-01 looks good)
```bash
# On server
ssh node2
cd /scratch/connectome/haba6030/colorBlind
sbatch analysis/validation/scripts/run_decoder_comparison.sbatch

# Monitor (28 tasks, ~1 hour total)
squeue -u haba6030
```

#### Step 6: Download All and Aggregate
```bash
# Download all results
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/validation/results/model_comparison/{before_alignment,after_alignment} \
    ./analysis/validation/results/model_comparison/

# Visualize each subject
for SUBJECT in 01 02 03 05 06 07; do
    python analysis/validation/scripts/05c_decoder_visualization.py \
        --before_dir analysis/validation/results/model_comparison/before_alignment \
        --after_dir analysis/validation/results/model_comparison/after_alignment \
        --subject ${SUBJECT} \
        --output_dir analysis/validation/results/model_comparison/figures_sub${SUBJECT}
done

# Group-level aggregation
python analysis/validation/scripts/06_aggregate_results.py \
    --before_dir analysis/validation/results/model_comparison/before_alignment \
    --after_dir analysis/validation/results/model_comparison/after_alignment \
    --subjects 01 02 03 05 06 07 \
    --output_dir analysis/validation/results/model_comparison/group_results
```

## What to Check

### After Sub-01 Test

✓ **Files exist:**
- `test_sub01_before/sub-01_performance_raw.json`
- `test_sub01_after/sub-01_performance_raw.json`

✓ **Performance:**
- All models > chance (12.5%)
- MAE < 90° (random guess)
- After alignment improves over before

✓ **Figures:**
- Performance comparison plot shows clear differences
- Linear models improve more than MLP (expected)

### After Full Pipeline

✓ **Completion:**
- 28 JSON files in `before_alignment/`
- 28 JSON files in `after_alignment/`

✓ **Group results:**
- Summary table shows significant improvements (p < 0.05)
- Cohen's d > 0.5 (medium effect size)
- ROI gradient: V1 > V2 > V3 > hV4

## Expected Results (Hypotheses)

### Hypothesis 1: Ridge vs Forward Encoding
- Forward Encoding should be better (6-channel prior)
- Both should improve after alignment

### Hypothesis 2: Linear vs Non-linear
**Before alignment:**
- MLP > Ridge ≈ Forward Encoding
- (Non-linear needed to handle individual differences)

**After alignment:**
- Ridge ≈ Forward Encoding ≈ MLP
- (Alignment removes individual differences, linear sufficient)

**Interaction:**
- Δ(Ridge) > Δ(Forward Encoding) > Δ(MLP)
- **Conclusion:** Alignment particularly helps linear models

### Hypothesis 3: ROI Gradient
- V1 > V2 > V3 > hV4
- Lower visual areas benefit more from alignment

## Troubleshooting

### Common Issues

**1. Import Error**
```bash
# Solution: Check conda environment
conda activate nilearn
python -c "from analysis.utils.utils_color_decoding import circular_diff_deg; print('OK')"
```

**2. Aligned Data Not Found**
```bash
# Solution: Run alignment first
sbatch analysis/validation/scripts/run_prepare_alignment.sbatch
```

**3. Out of Memory**
```bash
# Solution: Increase memory in sbatch script
#SBATCH --mem=24G  # Instead of 16G
```

**4. MLP Fails to Converge**
- Already handled with strong regularization and early stopping
- If still fails, check voxel count (should be > 100)

## Output Structure

```
analysis/validation/results/
├── aligned_amplitudes/
│   └── test_zscore_FINAL_procrustes/
│       ├── sub-01/ ... sub-07/
│       └── alignment_summary.json
│
├── model_comparison/
│   ├── test_sub01_before/        # Sub-01 test (before)
│   ├── test_sub01_after/         # Sub-01test (after)
│   ├── test_sub01_figures/       # Sub-01 figures
│   ├── before_alignment/         # Full (before)
│   ├── after_alignment/          # Full (after)
│   ├── figures_sub{01-07}/       # Per-subject figures
│   └── group_results/            # Group aggregation
│
└── logs/                         # SLURM logs
```

## Time Estimates

- **Upload scripts:** < 1 min
- **Prepare alignment:** 5-10 min
- **Sub-01 test:** 15-20 min
- **Full array job:** 30-60 min (parallel)
- **Download results:** 2-5 min
- **Visualization:** 1-2 min per subject
- **Group aggregation:** 1-2 min

**Total:** ~1.5-2 hours for complete pipeline

## Next Steps

After completing this pipeline:

1. **Write up results** for validation section
2. **Create publication figures** from group results
3. **Optional extensions:**
   - Add Kernel Ridge, SVR (more non-linear models)
   - Split-half reliability analysis
   - Include CVD subjects for comparison

## Key Questions Answered

✓ **Q1:** Which linear model is better?
- Compare Ridge vs Forward Encoding performance

✓ **Q2:** Does alignment help linear models more?
- Compare Δ(Linear) vs Δ(MLP)
- Statistical test: 2-way ANOVA (Alignment × Model Type)

✓ **Q3:** ROI differences?
- V1 > V2 > V3 > hV4 gradient effect

## Citation

**Methods:**
- Ridge: Hoerl & Kennard (1970)
- Forward Encoding: Brouwer & Heeger (2009, 2013)
- Procrustes: Gower & Dijksterhuis (2004)
- LORO CV: Varoquaux et al. (2017)

## Contact

See main README or CLAUDE.md for project information.

---

**Quick Start:** `./analysis/validation/scripts/workflow_helper.sh`

**Full Docs:** `analysis/validation/scripts/README_decoder_comparison.md`
