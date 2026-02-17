# 3D Brain Visualization Guide

**Purpose:** Generate compelling paper figures showing Procrustes/SRM alignment effects
**Status:** ✅ Ready to use
**Created:** 2026-02-16

---

## Overview

두 가지 핵심 시각화:

1. **`visualize_3d_brain_alignment.py`** - Procrustes 회전 효과
   - 3D PCA feature space rotation (before/after)
   - Voxel correspondence heatmap
   - Noise ceiling brain map
   - Summary figure with key metrics

2. **`visualize_scattered_but_parallel.py`** - CVD 이질성의 구조적 특성
   - MDS spatial scatter (heterogeneity)
   - RDM heatmaps (preserved structure)
   - Dual-level model schematic

---

## Quick Start

### 환경 설정

```bash
conda activate nilearn

# 필요한 패키지 확인
python -c "import numpy, matplotlib, scipy, sklearn, seaborn; print('OK')"
```

---

### 1. Procrustes Alignment Visualization

**기본 실행 (Sub-08, V2):**

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase2_SRM_across_between

python visualize_3d_brain_alignment.py
```

**커스텀 설정:**

```bash
python visualize_3d_brain_alignment.py \
    --subject sub-08 \
    --roi V2 \
    --hc-subjects sub-01 sub-02 sub-03 sub-04 sub-05 sub-06 \
    --base-dir /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding \
    --output-dir ./results/3d_brain_visualization
```

**예상 출력:**

```
results/3d_brain_visualization/
├── sub-08_V2_3d_rotation.png           # 3D 회전 효과 (3 panels)
├── sub-08_V2_voxel_correspondence.png  # Voxel 대응 분석
├── noise_ceiling_brain_map.png         # ROI별 ceiling 개선
├── sub-08_V2_summary.png               # 종합 요약 (one killer slide)
└── sub-08_V2_metrics.json              # 정량적 결과
```

**핵심 메트릭 (sub-08 V2 기준):**
- Disparity reduction: ~51% ↓ (0.92 → 0.45)
- Voxel correlation: 0.12 → 0.48 (+300%)
- Noise ceiling: -0.23 → 0.60 (+0.82)

---

### 2. "Scattered but Parallel" Visualization

**기본 실행:**

```bash
python visualize_scattered_but_parallel.py \
    --roi V2 \
    --output-dir ./results/scattered_parallel_visualization
```

**예상 출력:**

```
results/scattered_parallel_visualization/
└── V2_dual_level_schematic.png         # 이중 레벨 모델 개념도
```

**To generate full MDS/RDM plots** (실제 데이터 필요):
```python
# 스크립트 내 plot_mds_spatial_scatter() 함수 사용
# SRM-aligned amplitude data 로드 후 실행
```

---

## Output Details

### Figure 1: 3D Rotation Effect

**`sub-08_V2_3d_rotation.png`** (3 panels):

- **Panel A: Before Alignment**
  - Blue circles: HC reference (8 colors in PCA space)
  - Red triangles: CVD raw patterns (misaligned)
  - Dashed lines: Color correspondence
  - Disparity: ~0.92

- **Panel B: After Procrustes**
  - Red triangles rotate toward blue circles
  - Orange arrows: Rotation direction
  - Disparity: ~0.45 (51% reduction)

- **Panel C: Overlay Comparison**
  - Gray X: Before
  - Red triangles: After
  - Blue circles: HC reference
  - Shows alignment improvement

**Key Message:**
```
Geometric rotation reduces disparity by 51%
→ Reveals latent representational geometry
```

---

### Figure 2: Voxel Correspondence

**`sub-08_V2_voxel_correspondence.png`** (4 panels):

- **Panel A: Raw correlation histogram**
  - Mean: ~0.12 (low)
  - Distribution: Centered near zero

- **Panel B: Procrustes correlation histogram**
  - Mean: ~0.48 (moderate-good)
  - Distribution: Shifted right (improvement)

- **Panel C: Scatter plot (raw vs proc)**
  - Most points above diagonal (improvement)
  - Improved voxels: ~75%

- **Panel D: Improvement heatmap**
  - Green: Positive improvement
  - Red: Negative (rare)
  - Sorted by improvement magnitude

**Key Message:**
```
75% of voxels show improved HC-CVD correspondence
Mean correlation: 0.12 → 0.48 (+300%)
```

---

### Figure 3: Noise Ceiling Brain Map

**`noise_ceiling_brain_map.png`** (2 panels):

- **Left: Raw Pipeline**
  - V1: 0.103 (near-zero)
  - V2: -0.226 (negative!)
  - V3: 0.011 (near-zero)
  - V4: 0.077 (low)
  - Interpretation: Geometric noise dominates

- **Right: Procrustes Pipeline**
  - V1: 0.585 (moderate-good)
  - V2: 0.595 (moderate-good)
  - V3: 0.566 (moderate)
  - V4: 0.745 (good)
  - Improvement lines shown

**Quality thresholds:**
- Orange dashed: 0.4 (moderate)
- Green dashed: 0.6 (high)

**Key Message:**
```
Procrustes alignment: +0.63 average ceiling improvement
Enables reliable analysis (all ROIs > 0.55)
```

---

### Figure 4: Summary (One Killer Slide)

**`sub-08_V2_summary.png`** - Publication-ready comprehensive figure

**Three columns:**

1. **Geometric Rotation**
   - Disparity: 0.92 → 0.45 (51% ↓)
   - Blue box

2. **Voxel Matching**
   - Correlation: 0.12 → 0.48
   - 75% voxels improved
   - Green box

3. **Signal Quality**
   - Ceiling: -0.009 → 0.623 (+0.631)
   - RDM reliability: 0.042 → 0.496 (11.7×)
   - Gold box

**Bottom message:**
```
"Geometric noise removal enables detection of HC-CVD differences
(Example: V1 p=0.057 → p=0.024 after Procrustes)"
```

**Use this for:**
- Conference talks (main result slide)
- Paper graphical abstract
- Grant applications

---

### Figure 5: Dual-Level Model

**`V2_dual_level_schematic.png`** (2 panels):

- **Panel A: Musical Analogy**
  - HC: All in C major (tight cluster, same key)
  - CVD-1: C major (original)
  - CVD-2: D major (transposed +2)
  - CVD-3: E major (transposed +4)
  - Same melody structure, different absolute pitch

- **Panel B: Two-Level Model**
  - **Level 1 (Red box): Spatial Heterogeneity**
    - CVD-CVD disparity: 1.71× > HC-HC
    - Different positions in feature space

  - **Level 2 (Green box): Structural Homogeneity**
    - CVD-CVD RDM: 1.14× > HC-HC
    - Preserved color relationships

**Key Message:**
```
CVD is NOT random noise, but systematic transformation:
• Spatial scatter (explains phenotypic variability)
• Structural preservation (shared compensatory mechanism)
→ "Scattered but parallel" configuration
```

---

## Using Figures in Paper

### Methods Section

**Figure 1 (3D rotation):**
```latex
"We applied orthogonal Procrustes alignment to remove geometric variance
across runs (Fig. 1A-B). This transformation reduced CVD-HC disparity by
51% on average (Fig. 1C), dramatically improving voxel-wise correspondence
(mean correlation: 0.12 → 0.48, Fig. 2)."
```

**Figure 3 (Noise ceiling):**
```latex
"Procrustes alignment increased noise ceiling from -0.009 to 0.623
(+0.631 improvement, Fig. 3). This 11.7-fold increase in RDM reliability
enabled detection of subtle HC-CVD differences that were masked by
geometric noise in the raw pipeline (V1: p=0.057 → p=0.024)."
```

### Results Section

**Figure 4 (Summary):**
```latex
"Geometric noise removal had three critical effects (Fig. 4):
(1) 51% reduction in CVD-HC disparity through optimal rotation,
(2) 300% improvement in voxel-wise HC-CVD correspondence, and
(3) 11.7× increase in representational reliability. Together, these
improvements enabled detection of HC-CVD differences in early visual
cortex (V1, V2)."
```

**Figure 5 (Dual-level):**
```latex
"CVD subjects exhibited a 'scattered but parallel' pattern (Fig. 5):
spatial heterogeneity (CVD-CVD disparity 1.71× > HC-HC) coupled with
structural homogeneity (CVD-CVD RDM correlation 1.14× > HC-HC).
This dual nature suggests CVD is not random variation, but a systematic
transformation analogous to musical transposition—different absolute
positions (keys) but preserved relational structure (melody)."
```

---

## Customization Options

### Change Subject/ROI

```bash
# Different CVD subject
python visualize_3d_brain_alignment.py --subject sub-09 --roi V1

# Different ROI comparison
python visualize_3d_brain_alignment.py --subject sub-08 --roi V3
```

### Adjust Figure Style

**In script, modify:**

```python
# Color schemes
hc_color = 'blue'       # Change to 'steelblue', 'navy', etc.
cvd_color = 'red'       # Change to 'crimson', 'darkred', etc.

# Figure size
figsize=(18, 6)         # Adjust for journal requirements

# DPI
dpi=300                 # Change to 600 for high-res print
```

### Font Sizes (for posters)

```python
plt.rcParams['font.size'] = 14          # Base font
plt.rcParams['axes.titlesize'] = 18     # Title
plt.rcParams['axes.labelsize'] = 16     # Axis labels
plt.rcParams['legend.fontsize'] = 14    # Legend
```

---

## Troubleshooting

### Common Issues

**1. FileNotFoundError: amplitudes not found**
```bash
# Check data directory structure
ls /Users/jinilkim/.../preprocess_Check/full_dataset_C010_with_residuals/sub-08/V2/

# Should contain:
# - amplitudes_raw.npy
# - amplitudes_procrustes.npy
# - metrics.json
```

**2. ImportError: No module named 'nilearn'**
```bash
conda activate nilearn
pip install nilearn
```

**3. Memory error with large voxel arrays**
```python
# In script, reduce displayed voxels
if n_voxels > 100:
    display_voxels = sort_idx[:100]  # Show top 100 only
```

**4. 3D plot not rotating**
```python
# Add interactive mode
%matplotlib notebook  # In Jupyter
# Or save static views with different angles
ax.view_init(elev=20, azim=45)  # Adjust elev/azim
```

---

## Advanced: Batch Processing

**Generate for all CVD subjects:**

```bash
#!/bin/bash

SUBJECTS=("sub-08" "sub-09" "sub-10")
ROIS=("V1" "V2" "V3" "V4")

for subj in "${SUBJECTS[@]}"; do
    for roi in "${ROIS[@]}"; do
        echo "Processing ${subj} ${roi}..."
        python visualize_3d_brain_alignment.py \
            --subject ${subj} \
            --roi ${roi} \
            --output-dir ./results/3d_visualization_all/${subj}_${roi}
    done
done
```

**Aggregate metrics:**

```python
import json
from pathlib import Path

all_metrics = []
for metrics_file in Path('./results/3d_visualization_all').rglob('*_metrics.json'):
    with open(metrics_file) as f:
        all_metrics.append(json.load(f))

# Compute statistics
disparities = [m['3d_rotation']['reduction_pct'] for m in all_metrics]
print(f"Mean disparity reduction: {np.mean(disparities):.1f}% ± {np.std(disparities):.1f}%")
```

---

## Expected Runtime

**Single subject-ROI:**
- 3D rotation: ~5 seconds
- Voxel correspondence: ~10 seconds
- Noise ceiling map: ~2 seconds
- Summary figure: ~1 second
- **Total: ~20 seconds**

**All 3 CVD × 4 ROIs (batch):**
- Total: ~4 minutes

---

## File Dependencies

**Required data files:**

```
phase1_preprocess_decoding/
└── preprocess_Check/
    ├── full_dataset_C010_with_residuals/
    │   ├── sub-01/V1/amplitudes_procrustes.npy
    │   ├── sub-01/V2/amplitudes_procrustes.npy
    │   ├── ...
    │   ├── sub-08/V1/amplitudes_raw.npy
    │   ├── sub-08/V1/amplitudes_procrustes.npy
    │   ├── sub-08/V2/amplitudes_raw.npy
    │   ├── sub-08/V2/amplitudes_procrustes.npy
    │   └── ...
    └── noise_ceiling_analysis.json
```

---

## Citation

When using these visualizations in publications:

```bibtex
@article{YourPaper2026,
  title={Procrustes Alignment Reveals Structured Heterogeneity in Color Vision Deficiency},
  author={Your Name et al.},
  journal={Journal Name},
  year={2026},
  note={Visualization code: visualize_3d_brain_alignment.py}
}
```

**Method references:**
- Procrustes: Gower & Dijksterhuis (2004)
- SRM: Chen et al. (2015)
- Noise ceiling: Diedrichsen et al. (2016), Schütt et al. (2021)

---

## Next Steps

### For Paper

1. ✅ Generate figures with default settings
2. Adjust colors/fonts for journal requirements
3. Export to high-res (600 DPI) for print
4. Combine multi-panel figures in Illustrator/Inkscape

### For Presentations

1. Use `summary.png` as main slide
2. Animate 3D rotation (export frames, create GIF)
3. Add pointer annotations for emphasis
4. Simplify for non-expert audience

### For Revisions

1. Save all metrics to JSON for reproducibility
2. Re-run with updated data if preprocessing changes
3. Generate supplementary figures (all subjects)
4. Create comparison table (Table S1)

---

## Contact

**Issues/Questions:**
- Script bugs: Check console output, file paths
- Method questions: See `METHODS_RESULTS_SUMMARY_FOR_PAPER.md`
- Interpretation: See Section 7 (Discussion Points)

**Status:** ✅ Ready for paper figure generation
**Last Updated:** 2026-02-16

---

## Quick Reference: Key Metrics

**Procrustes Effect (Sub-08 V2):**
```
Disparity:    0.92 → 0.45  (51% ↓)
Voxel corr:   0.12 → 0.48  (+300%)
```

**Overall Pipeline (9 subjects):**
```
Noise ceiling:     -0.009 → 0.623  (+0.631)
RDM reliability:    0.042 → 0.496  (11.7×)
Ceiling utilized:   83.7% (excellent)
```

**V2 "Scattered but Parallel":**
```
Spatial:      CVD-CVD disparity 1.71× > HC-HC
Structural:   CVD-CVD RDM corr  1.14× > HC-HC
```

**HC-CVD Group Comparison:**
```
V1: Δ=0.183, p=0.024*, d=1.87
V2: Δ=0.149, p=0.025*, d=2.20 ⭐
```

Use these numbers in figure annotations!
