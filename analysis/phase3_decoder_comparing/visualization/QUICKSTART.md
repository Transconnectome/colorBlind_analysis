# CVD Distortion Figure - Quick Start Guide

## ✓ Status: Implementation Complete & Tested (Updated 2026-02-22)

All required data files are present and validated. RDM computation tested successfully.

**IMPORTANT UPDATES:**
- ✓ Color wheel labels fixed (no overlap)
- ✓ Surface projection improved (34-58 vertices visible)
- ✓ Shows only FDR-corrected significant pairs (q < 0.05)

## Generate Figures

### 1. Single ROI (V2 - strongest effects):
```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis
conda activate srm

python analysis/phase3_decoder_comparing/visualization/create_cvd_distortion_figure.py --roi V2
```

**Expected output:**
```
analysis/phase5_filter_optimization/figures/cvd_distortion_figure_V2.png
```
- Size: ~15-20 MB
- Resolution: 6000×4800 pixels (300 DPI)
- Rows: 3 (sub-08 Deutan, sub-09 Protan, sub-10 Deutan)
- Columns: 4 (Stimuli, Glass Brain, Surface, RDM Distortion)

### 2. All ROIs:
```bash
python analysis/phase3_decoder_comparing/visualization/create_cvd_distortion_figure.py --all-rois
```

**Processing time:** ~5-10 minutes per ROI (surface rendering is slow)

## Test Before Running

### Quick validation:
```bash
# Test data availability
python analysis/phase3_decoder_comparing/visualization/test_cvd_figure.py --data-check

# Test RDM computation
python analysis/phase3_decoder_comparing/visualization/test_cvd_figure.py --rdm-test

# Full test (creates V2 figure)
python analysis/phase3_decoder_comparing/visualization/test_cvd_figure.py --full-test
```

## Expected Scientific Patterns

### Deutan (sub-08, sub-10) - M-cone deficiency:
- **Decreased dissimilarity:** Red-Green, Yellow-Orange pairs
- **Mechanism:** Cannot distinguish wavelengths requiring M-cone contrast
- **V2 strongest:** p=0.040 for sub-08 individual analysis

### Protan (sub-09) - L-cone deficiency:
- **Decreased dissimilarity:** Red-Cyan, Red-Blue pairs
- **More severe:** Longer wavelength sensitivity completely lost
- **Individual effects:** May be more variable than Deutan

## Panel Descriptions

### A. Stimuli (Color Wheel)
- 8 isoluminant hues at 45° intervals
- Red → Orange → Yellow → Green → Cyan → Blue → Purple → Magenta
- Hardcoded RGB values (same as experiment)

### B. Glass Brain (Whole Brain Anatomy)
- 4 orthogonal views (Left/Right/Dorsal/Ventral)
- RMS activation overlay (Reds colormap)
- Shows ROI spatial location in MNI space

### C. Occipital Surface (Posterior Inflated)
- Left hemisphere inflated surface
- Hot colormap (shared scale across subjects)
- Posterior view emphasizes early visual areas
- Surface projection via `vol_to_surf()` with 3mm sampling

### D. RDM Distortion Bars (CVD - HC)
- Top 10 color pairs by absolute difference
- Red bars: CVD > HC (increased dissimilarity)
- Blue bars: CVD < HC (decreased dissimilarity, expected for confusion)
- Sorted by magnitude

## Data Sources (All Validated ✓)

### Amplitudes:
```
analysis/phase1_preprocess_decoding/results/full_dataset_C010/
└── sub-{ID}/{ROI_dir}/amplitudes_procrustes.npy  # (6, 8, n_voxels)
```

### ROI Masks:
```
analysis/roi_masks/method3_header_mi/method3_header_mi/
└── sub-{ID}/roi_pipeline/{ROI}_mask_thr50_intnearest_binTrue_maskfunc_gmTrue_subjFalse.nii.gz
```

**Note:** ROI directory mapping for amplitudes: hV4 → V4, others unchanged

### Subjects:
- **CVD:** sub-08, sub-09, sub-10 (all data present ✓)
- **HC:** sub-01 to sub-07 (all data present ✓)

## Troubleshooting

### Error: Out of Memory
Surface rendering requires ~2-3 GB RAM per figure.

**Solution:** Close other applications or reduce DPI:
```python
# Line 374 in create_cvd_distortion_figure.py
fig = plt.figure(figsize=(20, 16), facecolor='white', dpi=100)  # Instead of 150

# Line 441
plt.savefig(output_path, dpi=150, ...)  # Instead of 300
```

### Warning: Surface looks empty/black
Check nilearn cache:
```bash
ls -lh ~/.nilearn_data/fsaverage5/
# If missing or corrupted:
rm -rf ~/.nilearn_data/
# Script will re-download on next run
```

### RDM shows unexpected patterns
Check HC mean RDM:
```python
from create_cvd_distortion_figure import compute_hc_mean_rdm
import matplotlib.pyplot as plt

hc_rdm = compute_hc_mean_rdm('V2')
plt.imshow(hc_rdm, cmap='viridis')
plt.colorbar()
plt.title('HC Mean RDM V2')
plt.savefig('debug_hc_rdm.png')
```

Expected pattern: Low dissimilarity for adjacent hues, high for complementary colors.

## Files Created

```
analysis/phase3_decoder_comparing/visualization/
├── create_cvd_distortion_figure.py   # Main script ✓
├── test_cvd_figure.py                # Validation script ✓
├── README_cvd_distortion_figure.md   # Full documentation ✓
├── QUICKSTART.md                     # This file ✓
└── cvd_distortion_figures/           # Output directory (auto-created)
    ├── cvd_distortion_figure_V1.png
    ├── cvd_distortion_figure_V2.png
    ├── cvd_distortion_figure_V3.png
    └── cvd_distortion_figure_hV4.png

analysis/matlab_viewers/
├── interactive_surface_viewer.m      # MATLAB 3D viewer ✓
└── prepare_matlab_surface_data.py    # Data prep for MATLAB ✓
```

## Next Steps

1. **Generate V2 figure** (recommended first - strongest effects)
2. **Review output** for expected CVD patterns
3. **Generate all ROIs** if V2 looks good
4. **(Optional)** Set up MATLAB viewer for interactive exploration

## References

- **Statistical framework:** Crawford & Howell (1998) single-case tests
- **SRM configuration:** HC-only training, LOO-consistent references
- **Group results:** V2 p=0.075 (trending), Individual: sub-08 V2 p=0.040*

**Last updated:** 2026-02-22
**Test status:** All data validated ✓ | RDM computation verified ✓
