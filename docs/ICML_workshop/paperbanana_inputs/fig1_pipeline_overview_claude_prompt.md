# Claude Artifact Prompt — Figure 1: Pipeline Overview with CVD Problem

아래 프롬프트를 claude.ai에 붙여넣어 PowerPoint artifact를 생성합니다.

---

## Prompt (아래를 그대로 복사)

```
Create a PowerPoint slide (python-pptx) for an ICML workshop paper figure. The slide should be 6.75 x 4.5 inches (single-column academic figure, tall format). White background, no slide title. No explanatory text in the figure — all annotation goes in the LaTeX caption.

The figure has TWO parts stacked TOP-BOTTOM:

### TOP ROW (~55% of slide height): "The Problem" — CVD distorts hV4 color geometry

Show two color wheels side by side, centered horizontally (each ~1.5 inches diameter):

**Left wheel — HC (Healthy Control):**
- 8 colored dots arranged in a perfect circle (evenly spaced at 0°, 45°, 90°, …, 315°)
- Colors in order: red (#E74C3C), orange (#E67E22), yellow (#F1C40F), green (#2ECC71), cyan (#1ABC9C), blue (#3498DB), purple (#9B59B6), magenta (#E91E9B)
- Thin gray lines connecting adjacent colors (including magenta→red) to show even spacing
- Bold label "HC" centered above the wheel, 11pt Calibri black

**Right wheel — CVD (Color Vision Deficient):**
- Same 8 colored dots but in a DISTORTED arrangement:
  - green, cyan, blue compressed together (closer spacing, ~15° apart instead of 45°)
  - red, orange, magenta expanded (wider spacing, ~65° apart)
  - The overall shape is slightly elliptical / warped
- Same thin gray lines connecting adjacent colors, now showing uneven spacing
- A subtle red bracket or shading in the green-cyan-blue compressed region to highlight collapse
- Bold label "CVD" centered above the wheel, 11pt Calibri, dark red (#C0392B)

Between the two wheels: a rightward arrow (→) with a small "?" or "distortion" label above it, in gray.

A thin horizontal gray line separates the top and bottom sections.

### BOTTOM ROW (~45% of slide height): "The Pipeline" — 4-stage inference

Four rounded rectangles connected left-to-right by dark gray arrows (→), spanning the full slide width. Each box is ~1.3 x 0.8 inches with a distinct light background fill:

**Box 1 — "Structured Representation"** (fill: #EBF5FB, border: #3498DB)
- Small icon: 8 colored dots in a circle (tiny, ~0.3 inch)
- Below icon: "fMRI hV4, K=3" in 8pt
- Arrow to next box, label above arrow: "LOCO CV" in 7pt dark gray

**Box 2 — "Vulnerability Profile"** (fill: #FEF9E7, border: #F39C12)
- Small icon: tiny 8-bar chart silhouette (some bars up, some down)
- Below icon: "v ∈ ℝ⁸" in 8pt
- Arrow to next box, label above arrow: "Grid search" in 7pt dark gray

**Box 3 — "Distortion Parameters"** (fill: #F5EEF8, border: #8E44AD)
- Two sub-labels stacked:
  - "Retinal: Δλ, g" in 8pt
  - "Cortical: βs, βc" in 8pt
- Below: "1–2 DOF" in 7pt gray
- Arrow to next box, label above arrow: "Pre-image" in 7pt dark gray

**Box 4 — "Correction Filter"** (fill: #EAFAF1, border: #27AE60)
- Small icons: ✓ (green) and ✗ (red) side by side
- Below: "stimulus-space filter" in 8pt

Box titles ("Structured Representation", etc.) are 9pt bold, centered at top of each box.

### Style
- All text: Calibri, black unless specified
- All boxes: 1pt borders, rounded corners (radius ~0.08 inch)
- Arrows: 1.5pt dark gray (#555555) with solid arrowheads
- No gradients, no shadows, no 3D effects
- Clean, minimal, publication-quality academic style
- No caption text, no "Figure 1" label — those go in LaTeX

Save as 'fig1_pipeline_overview.pptx'.
```

---

## 사용 후 작업

1. Claude artifact에서 .pptx 다운로드
2. PowerPoint에서 열고 미세 조정 (dot 위치, 화살표, 간격 등)
3. Export → PNG (300 DPI) or PDF
4. `figures/fig1_pipeline_overview.png`으로 저장
5. LaTeX 컴파일 확인

## 대안: PaperBanana

BOTTOM (pipeline) 부분만 PaperBanana에 넣어도 됩니다.
TOP (color wheel)은 matplotlib로도 가능 — 아래 참조.

## 대안: Matplotlib (TOP 부분만)

```python
import numpy as np
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(5, 2.5))
colors = ['#E74C3C','#E67E22','#F1C40F','#2ECC71','#1ABC9C','#3498DB','#9B59B6','#E91E9B']

# HC: evenly spaced
angles_hc = np.linspace(0, 2*np.pi, 8, endpoint=False)
for a, c in zip(angles_hc, colors):
    ax1.scatter(np.cos(a), np.sin(a), c=c, s=100, zorder=5, edgecolors='k', linewidths=0.5)
for i in range(8):
    j = (i + 1) % 8
    ax1.plot([np.cos(angles_hc[i]), np.cos(angles_hc[j])],
             [np.sin(angles_hc[i]), np.sin(angles_hc[j])], 'gray', lw=0.5)
ax1.set_title('HC', fontsize=11, fontweight='bold')
ax1.set_xlim(-1.5, 1.5); ax1.set_ylim(-1.5, 1.5)
ax1.set_aspect('equal'); ax1.axis('off')

# CVD: distorted (green-cyan-blue compressed, red-orange-magenta expanded)
angles_cvd = np.array([0, 55, 100, 150, 165, 180, 250, 330]) * np.pi / 180
for a, c in zip(angles_cvd, colors):
    ax2.scatter(np.cos(a), np.sin(a), c=c, s=100, zorder=5, edgecolors='k', linewidths=0.5)
for i in range(8):
    j = (i + 1) % 8
    ax2.plot([np.cos(angles_cvd[i]), np.cos(angles_cvd[j])],
             [np.sin(angles_cvd[i]), np.sin(angles_cvd[j])], 'gray', lw=0.5)
ax2.set_title('CVD', fontsize=11, fontweight='bold', color='#C0392B')
ax2.set_xlim(-1.5, 1.5); ax2.set_ylim(-1.5, 1.5)
ax2.set_aspect('equal'); ax2.axis('off')

plt.tight_layout()
plt.savefig('hv4_distortion_problem.png', dpi=300, bbox_inches='tight')
```
