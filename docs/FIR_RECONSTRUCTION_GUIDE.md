# FIR Reconstruction Pipeline Guide

Complete pipeline for color reconstruction using per-voxel FIR estimation.

## Features

✅ **Per-voxel FIR** - Each voxel has its own hemodynamic response curve
✅ **Correct Lab hues** - Uses actual pilot data hue values
✅ **Diagonal LDA** - Classification method from Brouwer & Heeger (2009)
✅ **B&H forward model** - 6-channel basis functions for reconstruction
✅ **Optional PCA** - Dimensionality reduction for parameter efficiency
✅ **Comprehensive visualizations** - HRF plots, z-maps, results
✅ **Parallel execution** - Run multiple ROIs simultaneously

## Quick Start

### Test on Single ROI (V2)

```bash
# Without PCA
sbatch --export=ROI=V2,USE_PCA=0 run_fir_reconstruction_single.sbatch

# With PCA (20 components) - RECOMMENDED
sbatch --export=ROI=V2,USE_PCA=1,N_COMPONENTS=20 run_fir_reconstruction_single.sbatch
```

### Run All ROIs in Parallel

```bash
sbatch run_fir_reconstruction_parallel.sbatch
```

This will process V1, V2, V3, V4, hV4, and VO1 simultaneously.

## Output Structure

```
derivatives/sub-01/fir_reconstruction/{ROI}/
├── log.txt                          # Detailed execution log
├── summary.csv                      # Quick results summary
├── results.pkl                      # Full results (Python pickle)
├── figures/
│   ├── {ROI}_mean_hrf.png          # Mean HRF from FIR
│   ├── color_1_zmap.png            # Z-score maps (if --save-zmaps)
│   ├── color_2_zmap.png
│   └── ...
└── zmaps/                           # NIfTI z-maps (if --save-zmaps)
    ├── color_1_zmap.nii.gz
    └── ...
```

## Command-Line Options

### fir_reconstruction.py

```bash
python fir_reconstruction.py --help

Options:
  --roi ROI              ROI name (V1, V2, V3, V4, hV4, VO1, etc.)
  --use-pca              Enable PCA dimensionality reduction
  --n-components N       Number of PCA components (default: 20)
  --save-zmaps           Save z-score maps for each color
```

### Examples

```bash
# V2 with PCA (20 components)
python fir_reconstruction.py --roi V2 --use-pca --n-components 20

# V4 without PCA, save z-maps
python fir_reconstruction.py --roi V4 --save-zmaps

# hV4 with PCA (30 components)
python fir_reconstruction.py --roi hV4 --use-pca --n-components 30 --save-zmaps
```

## Customizing Parallel Execution

Edit `run_fir_reconstruction_parallel.sbatch`:

```bash
# Add more ROIs
ROIS=(
    "V1"
    "V2"
    "V3"
    "V4"
    "hV4"
    "VO1"
    "LO1"      # Add custom ROIs
    "LO2"
)

# Change PCA settings
USE_PCA=1           # 0=disable, 1=enable
N_COMPONENTS=20     # Number of components

# Update array size to match number of ROIs
#SBATCH --array=0-7  # For 8 ROIs
```

## Results Interpretation

### Summary CSV

```csv
ROI,N_voxels,Use_PCA,N_components,Classification_accuracy,Reconstruction_error_deg,Novel_color_error_deg
V2,310,True,20,1.0,15.3,18.7
```

**Key metrics:**
- **Classification accuracy**: Should be >> 12.5% (chance)
- **Reconstruction error**: Lower is better, chance = 90°
- **Novel color error**: Tests generalization to held-out colors

### Expected Results (based on FIR tests)

With PCA(20):
- **Classification:** ~100% (vs 12.5% chance)
- **Reconstruction:** < 30° error (vs 90° chance)
- **Novel colors:** < 40° error

## Troubleshooting

### Job fails immediately

**Check:**
1. ROI mask exists: `derivatives/sub-01/roi/sub-01_V2_mask.nii.gz`
2. Functional data exists in `output/pilot/sub-01/func/`
3. Event files exist in `pilot/sub-01/func/`

### Memory errors

Increase memory in sbatch script:
```bash
#SBATCH --mem=64G  # Default is 32G
```

### Too slow

- Use PCA to reduce dimensionality
- Disable z-map saving (`SAVE_ZMAPS=0`)
- Reduce number of ROIs processed in parallel

## Monitoring Jobs

```bash
# Check job status
squeue -u $USER

# Check specific job
squeue -j <job_id>

# View output in real-time
tail -f logs/fir_recon_<job_id>.out

# Cancel job
scancel <job_id>

# Cancel all your jobs
scancel -u $USER
```

## Comparing Results Across ROIs

After running all ROIs:

```bash
# Combine all summaries
cat derivatives/sub-01/fir_reconstruction/*/summary.csv > all_roi_results.csv
```

Then analyze in Python/R or view in Excel.

## Next Steps

1. **Run test on V2** to verify pipeline works
2. **Compare with/without PCA** to see impact
3. **Run all ROIs in parallel** for complete analysis
4. **Analyze reconstruction patterns** across visual hierarchy
5. **Proceed to CVD correction filter design**

## Notes

- **Runtime:** ~5-15 minutes per ROI (depending on voxel count)
- **Disk space:** ~100MB per ROI (more if saving z-maps)
- **Recommended:** Start with single ROI to verify, then run parallel
- **PCA recommended:** Improves parameter efficiency without hurting accuracy

## Citation

Methods based on:
- Brouwer & Heeger (2009) *J. Neurosci.* - Forward model & diagonal LDA
- Improved with per-voxel FIR instead of ROI-averaged HIRF
