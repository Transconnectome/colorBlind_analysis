# Presentation Figures Generation Scripts

**Purpose**: Generate high-quality visualizations for professor meeting presentation (2026-01-13)

**Created**: 2026-01-13
**For**: Part 1 of presentation (Current Work: Procrustes-based filter design)

---

## Overview

This directory contains Python scripts to generate 4 key figures for the first 10 minutes of the presentation, illustrating:

1. **Decoding Results**: HC vs CVD neural color discrimination across V1-hV4
2. **Procrustes Alignment**: Conceptual visualization of geometric alignment method
3. **3D Loss Function**: Three-component loss (magnitude, baseline, structure)
4. **RDM Recovery**: Structural similarity improvement after filtering

---

## Quick Start

### Generate All Figures (Recommended)

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/docs/presentation_figures
python 00_generate_all_figures.py
```

**Output**: 8 files total (4 PNG + 4 PDF)

### Generate Individual Figures

```bash
# Figure 1: Decoding results bar chart
python 01_decoding_results_bar_chart.py

# Figure 2: Procrustes alignment illustration
python 02_procrustes_alignment_2d.py

# Figure 3: Three-dimensional loss function
python 03_loss_function_3d.py

# Figure 4: RDM heatmaps comparison
python 04_rdm_heatmaps_comparison.py
```

---

## File Descriptions

### Master Script

**`00_generate_all_figures.py`**
- Runs all 4 figure generation scripts sequentially
- Reports success/failure for each script
- Lists all output files with sizes

### Figure 1: Decoding Results

**`01_decoding_results_bar_chart.py`**

**For Slide**: 3 (Decoding Results - Neural-Behavioral Dissociation)

**Output**:
- `01_decoding_results.png` (high-res PNG)
- `01_decoding_results.pdf` (vector PDF)

**Content**:
- Panel A: 8-way classification accuracy (V1-hV4)
- Panel B: Reconstruction error in degrees (V1-hV4)
- HC vs CVD comparison with error bars
- Statistical annotations (p-values, n.s.)
- Chance level references (12.5%, 90°)

**Key Message**: No significant CVD-HC differences (RQ1)

**Data Source**: `/docs/OHBM_abstract/priorworks/FULL_STATISTICS_SUMMARY.md`

---

### Figure 2: Procrustes Alignment

**`02_procrustes_alignment_2d.py`**

**For Slide**: 5 (Procrustes Alignment Method)

**Output**:
- `02_procrustes_alignment.png`
- `02_procrustes_alignment.pdf`

**Content**:
- Panel A: CVD vs HC patterns before alignment (2D projection)
- Panel B: Transformation steps (translation, rotation, no scaling)
- Panel C: CVD vs HC patterns after alignment (near-perfect overlap)
- Disparity metrics (before/after)
- Color-coded 8-color labels

**Key Message**: Geometric alignment enables HC decoder application to CVD

**Method**: Simulated 2D projection for conceptual illustration

---

### Figure 3: Three-Dimensional Loss Function

**`03_loss_function_3d.py`**

**For Slide**: 6 (Three-Dimensional Loss Function)

**Output**:
- `03_loss_function_3d.png`
- `03_loss_function_3d.pdf`

**Content**:
- **Column 1**: Magnitude loss (L2 norm matching)
  - Before/after bar charts
  - Loss reduction percentage
  - Formula panel
- **Column 2**: Baseline loss (mean activation matching)
  - Before/after bar charts
  - DC offset correction
  - Formula panel
- **Column 3**: Structure loss (RDM matching)
  - Before/after 8×8 heatmaps
  - RDM correlation improvement
  - Formula panel

**Key Message**: Three orthogonal dimensions → comprehensive alignment

**Method**: Simulated patterns demonstrating each loss component

---

### Figure 4: RDM Heatmaps

**`04_rdm_heatmaps_comparison.py`**

**For Slide**: 7 (Optimization Results)

**Output**:
- `04_rdm_heatmaps.png`
- `04_rdm_heatmaps.pdf`

**Content**:
- **Row 1 (Sub-08)**: High structure loss case
  - Before: Yellow-Green collapse (RDM corr 0.495)
  - After: Y-G recovered (RDM corr 0.999)
  - HC target + difference map
- **Row 2 (Sub-09)**: Mild distortion case
  - Before: Subtle noise (RDM corr 0.882)
  - After: Near-perfect (RDM corr 0.998)
  - HC target + difference map

**Key Message**: Individual optimization tailored to distortion profiles

**Data Source**: `/analysis/phase3_procrustes_filter/rdm/` (simulated here)

---

## Requirements

### Python Packages

```bash
conda activate nilearn

# Required packages (should already be installed):
numpy
matplotlib
seaborn
scipy
```

### Verify Installation

```python
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.spatial import procrustes
from scipy.stats import pearsonr

print("✅ All packages available")
```

---

## Output File Specifications

### PNG Files (For Slides)

- **Resolution**: 300 DPI
- **Format**: RGB
- **Background**: White
- **Size**: ~1-3 MB each
- **Usage**: Direct import into PowerPoint/Google Slides

### PDF Files (For Print/Vector)

- **Format**: Vector (editable in Illustrator/Inkscape)
- **Size**: ~200-500 KB each
- **Usage**: High-quality print, poster presentations

---

## Customization

### Change Figure Size

```python
# In any script, modify:
fig, axes = plt.subplots(1, 2, figsize=(12, 5))  # Default
fig, axes = plt.subplots(1, 2, figsize=(16, 7))  # Larger for presentation
```

### Change DPI (Resolution)

```python
# In any script, modify:
plt.rcParams['figure.dpi'] = 150  # Default (screen)
plt.rcParams['figure.dpi'] = 300  # High-res (print)
plt.rcParams['figure.dpi'] = 600  # Publication quality
```

### Change Color Scheme

```python
# In any script, modify:
sns.set_palette("husl")      # Default
sns.set_palette("colorblind") # For CVD accessibility
sns.set_palette("Set2")      # Pastel colors
```

### Save Additional Formats

```python
# Add to end of any script:
plt.savefig(output_path.replace('.png', '.svg'))  # SVG vector
plt.savefig(output_path.replace('.png', '.eps'))  # EPS vector
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'matplotlib'"

**Solution**: Activate conda environment
```bash
conda activate nilearn
```

### Issue: Figures too small on slides

**Solution**: Increase figure size in script
```python
fig, axes = plt.subplots(1, 2, figsize=(16, 8))  # Bigger
```

### Issue: Text too small to read

**Solution**: Increase font sizes
```python
plt.rcParams['font.size'] = 14       # Larger base font
plt.rcParams['axes.labelsize'] = 16  # Larger axis labels
plt.rcParams['axes.titlesize'] = 18  # Larger titles
```

### Issue: Slow generation

**Solution**: Reduce DPI for quick preview
```python
plt.rcParams['figure.dpi'] = 100  # Faster (lower quality)
```

Then regenerate at 300 DPI for final version.

---

## Integration with Presentation Plan

These figures correspond to Part 1 slides in `/docs/PRESENTATION_PLAN_NOTION.md`:

| Figure | Slide | Section | Key Message |
|--------|-------|---------|-------------|
| 01 | 3 | Decoding Results | No CVD-HC differences (RQ1) |
| 02 | 5 | Procrustes Method | Geometric alignment concept |
| 03 | 6 | 3D Loss Function | Three-dimensional optimization |
| 04 | 7 | Optimization Results | Structural recovery (RQ3) |

**Part 2 Figures** (Future Phases):
- Use existing high-res images in `/prediction_model_workspace/docs/`:
  - `overall.png` (5.7 MB)
  - `phase1.png` (4.4 MB)
  - `phase2.png` (4.8 MB)
  - `phase3.png` (4.5 MB)

---

## Real Data Integration (Future)

Currently, figures use **simulated data** for quick generation. To use **actual experimental data**:

### Figure 1: Decoding Results
```python
# Load from:
data = np.load('/path/to/derivatives/phase0_baseline/classification_results.npz')
hc_acc = data['hc_accuracy']
cvd_acc = data['cvd_accuracy']
```

### Figure 4: RDM Heatmaps
```python
# Load from:
rdm_data = np.load('/path/to/derivatives/phase3_filters/rdm/sub-08_V1_rdm_comparison.npz')
rdm_cvd_pre = rdm_data['RDM_cvd_pre']
rdm_cvd_post = rdm_data['RDM_cvd_post']
rdm_hc = rdm_data['RDM_hc']
```

**Note**: Actual data paths may vary based on server setup.

---

## Version History

- **2026-01-13**: Initial creation (4 figures for Part 1)
- Future: Add figures for Part 2 if needed

---

## Contact

For questions about these scripts or figure customization, refer to:
- Main documentation: `/docs/PRESENTATION_PLAN_NOTION.md`
- Technical details: `/docs/LOSS_FUNCTION_DETAILED.md`
- Project overview: `/CLAUDE.md`

---

## License

Internal research use only. For publication, ensure all figures comply with journal requirements (resolution, color mode, file format).
