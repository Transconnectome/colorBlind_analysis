# T1w Space ROI Analysis

## Overview

This pipeline creates individualized ROI masks in T1w space for analysis, as an alternative to MNI-based analysis.

**Key Concept:** Instead of normalizing all subjects to MNI space, we bring the Wang atlas ROIs into each subject's native T1w space and perform analysis there.

## Why T1w Space?

### Advantages over MNI Space

1. **Higher Resolution**: 1mm T1w vs 2mm MNI
2. **Better Registration**: With method3_header_mi's improved BOLD→T1w coregistration (MI-based)
3. **Individual Anatomy**: Preserves subject-specific anatomical structure
4. **MNI-Independent**: Not affected by MNI normalization quality

### Why Not BOLD Native Space?

- T1w space has better resolution than BOLD (1mm vs 2mm)
- fMRIPrep already provides T1w-space BOLD (`space-T1w_desc-preproc_bold.nii.gz`)
- No need for additional BOLD→T1w transform
- More stable (less noise) than BOLD native

## Pipeline

```
Step 1: MNI ROI → T1w space
  Wang atlas (MNI) → subject's T1w space using ANTs transform

Step 2: Create binary mask
  Threshold > 20 to create binary mask

Step 3: Visualizations
  Overlay ROI on T1w space BOLD for QC

Step 4: Functional sanity check
  Extract timeseries from T1w space BOLD
  Verify signal quality and decodability
```

## Dataset

- **fMRIPrep**: `method3_header_mi` (MI-based coregistration)
- **Subjects**: 01-10 (all 10 subjects usable)
- **ROIs**: V1, V2, V3, hV4 (Wang atlas)

## Files

### Scripts

- `transform_roi_to_native.sh` - Main transform script (MNI → T1w)
- `visualize_native_roi.py` - Create QC visualizations
- `sanity_check_native_roi.py` - Functional validation
- `summarize_native_roi_results.py` - Generate HTML report
- `run_native_roi.sbatch` - SLURM batch script

### Key Outputs

Per subject (`/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/results/native_roi/sub-{ID}/`):

- `sub-{ID}_{ROI}_space-T1w.nii.gz` - Probabilistic ROI in T1w space
- `sub-{ID}_{ROI}_space-T1w_mask.nii.gz` - Binary mask (threshold > 20)
- `QC_sub-{ID}_{ROI}_overlay.png` - Quick QC overlay
- `QC_sub-{ID}_{ROI}_detailed.png` - Detailed visualization
- `QC_sub-{ID}_{ROI}_histogram.png` - Intensity distribution
- `sanity_check_sub-{ID}_{ROI}.png` - Functional diagnostics

## Usage

### 1. Test Single Subject Locally

```bash
# On local machine - test script syntax
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/prep_trials/scripts/native_roi

# Check bash syntax
bash -n transform_roi_to_native.sh

# Check Python syntax
python3 -m py_compile visualize_native_roi.py
python3 -m py_compile sanity_check_native_roi.py
```

### 2. Upload to Server

```bash
# Upload all scripts in one command
scp transform_roi_to_native.sh visualize_native_roi.py sanity_check_native_roi.py summarize_native_roi_results.py run_native_roi.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/scripts/native_roi/
```

### 3. Test Interactive on Server

```bash
# SSH to server
ssh haba6030@node2

# Navigate to scripts
cd /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/scripts/native_roi

# Test one ROI
bash transform_roi_to_native.sh 02 V1 1

# Check output
ls -lh /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/results/native_roi/sub-02/
```

### 4. Profile Resource Usage

```bash
# Test with time profiling
/usr/bin/time -v bash transform_roi_to_native.sh 02 V1 1 > test_profile.log 2>&1

# Check peak memory
grep "Maximum resident set size" test_profile.log

# Check CPU usage
grep "Percent of CPU" test_profile.log
```

### 5. Submit Full Batch Job

```bash
# Submit all 10 subjects
sbatch run_native_roi.sbatch

# Monitor progress
squeue -u haba6030

# Check logs
tail -f /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/results/native_roi/logs/native_roi_*_0.out
```

### 6. Generate Summary Report

```bash
# After jobs complete
cd /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/scripts/native_roi

python summarize_native_roi_results.py --output-dir /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/results/native_roi/report

# Download report
# On local machine:
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/analysis/prep_trials/results/native_roi/report ~/Downloads/
```

## Expected Resource Usage

Based on similar transforms:

- **Memory**: ~8-12 GB per subject
- **Time**: ~30-45 min per subject (4 ROIs)
- **CPU**: 2 cores sufficient
- **Parallelism**: 10 subjects can run simultaneously on node2

## Expected Results

### Success Criteria

- ✅ T1w ROI voxel count > 100
- ✅ QC overlay shows ROI in posterior occipital cortex
- ✅ Functional decoding > 20% (chance = 12.5% for 8 colors)
- ✅ tSNR > 20

### Comparison with method3_header_mi Results

With improved MI-based coregistration, expect:

- **Higher success rate** compared to original_v3 (which had ~3% success)
- **Better ROI localization** in visual cortex
- **More consistent voxel counts** across subjects

## Troubleshooting

### Empty ROI after transform

```bash
# Check if transform file exists
ls -lh /storage/connectome/haba6030/fmriprep_out_method3_header_mi/sub-02/anat/*xfm.h5

# Check T1w space BOLD
ls -lh /storage/connectome/haba6030/fmriprep_out_method3_header_mi/sub-02/func/*space-T1w*.nii.gz
```

### Low voxel count

- Check threshold (currently 20) - may need adjustment
- Inspect probabilistic ROI max intensity
- Review QC overlay for alignment quality

### Sanity check fails

- May indicate poor BOLD→T1w coregistration
- Check fMRIPrep QC reports for that subject
- Review registration quality in prep_trials/README.md

## Next Steps

After successful ROI creation:

1. Use T1w space ROIs for decoding analysis
2. Compare results with MNI-based analysis
3. Assess whether individual anatomy preservation improves results
4. Particularly important for CVD subjects (sub-08, 09, 10)

## References

- Wang atlas: doi:10.1093/cercor/bhu277
- fMRIPrep transforms: doi:10.1038/s41592-018-0235-4
- MI-based coregistration: See `prep_trials/README.md`
