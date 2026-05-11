# Figure 4 — 2-Component Model: hV4 LOCO Vulnerability

## Generated
- Script: `generate_fig4.py`
- Run: `conda run -n srm python3 generate_fig4.py`
- Outputs: `fig4_output.png` (300 dpi), `fig4_output.pdf` (vector)

## Panel descriptions

### Panel A — Per-subject vulnerability profile
- **Observed** (filled circles, black): `baseline.vuln_baseline` from `phase_a_2component/sub-XX_V4_2component.json` (identical for both models; these are the CVD hV4 LOCO vulnerability values derived from HC training)
- **2-component** (solid line): `best_loss.vuln_sim` from `phase_a_2component/sub-XX_V4_2component.json` — predicted vulnerability at optimal (β_s, β_c)
- **Machado** (dashed line, lighter): `best_loss.vuln_sim` from `phase_a/sub-XX_V4_machado_1way.json` — predicted vulnerability at optimal Δλ
- Hue x-axis: R=red(0°), O=orange(45°), Y=yellow(90°), G=green(135°), C=cyan(180°), B=blue(225°), P=purple(270°), M=magenta(315°) in DKL space

### Panel B — Model comparison bar chart
- Y-axis: Spearman ρ between observed and model-predicted LOCO vulnerability (across 8 hues)
- Grouped by subject; solid bars = 2-component, hatched bars = Machado
- P-values from label-permutation test (40,320 permutations)
- **IMPORTANT interpretation note**: For sub-09, Machado (ρ=0.762, p=0.018) shows higher LOCO ρ than 2-component (ρ=0.690, p=0.035). Both are statistically significant. The 2-component model preference for sub-09 rests on dual-criterion validation (LOCO + exact pre-image) and physiological interpretability, not raw LOCO ρ superiority.

### Panel C — Parameter landscape
- 2D grid of (β_s, β_c) at 1° resolution from landscape JSON (1,326 evaluations per subject)
- Color encodes Spearman ρ (RdBu_r, vmin=−0.5, vmax=+0.90)
- White star marks the LOCO-optimal (β_s, β_c) selected as canonical filter parameters
- β_s = S-cone retinal shift (degrees of hue rotation)
- β_c = cortical opponent-channel rotation (degrees)

## Key numbers

| | 2-comp β_s | 2-comp β_c | 2-comp ρ | 2-comp p | Machado Δλ | Machado ρ | Machado p |
|---|---|---|---|---|---|---|---|
| Sub-08 (deutan) | 38° | −14° | 0.881 | 0.0036 ** | 1.5 nm | 0.619 | 0.058 n.s. |
| Sub-09 (protan) | 6° | −22° | 0.690 | 0.035 * | 13.5 nm | 0.762 | 0.018 * |

## Data files

| File | Used for |
|---|---|
| `phase_a_2component/sub-08_V4_2component.json` | Sub-08 2-comp fit (best params, vuln_sim, permutation p) |
| `phase_a_2component/sub-09_V4_2component.json` | Sub-09 2-comp fit |
| `phase_a_2component/sub-08_V4_2component_landscape.json` | Sub-08 landscape grid (1326 pts) |
| `phase_a_2component/sub-09_V4_2component_landscape.json` | Sub-09 landscape grid (1326 pts) |
| `phase_a/sub-08_V4_machado_1way.json` | Sub-08 Machado fit |
| `phase_a/sub-09_V4_machado_1way.json` | Sub-09 Machado fit |

All paths relative to `analysis/future_phase2_filter_optimization/results/fits/`

## Style
- Sub-08 (deutan): orange (#E07B2C)
- Sub-09 (protan): teal (#2D8E8B)
- Observed data: black (#222222)
- Significance: ** p<0.01, * p<0.05, n.s. p≥0.05
- Figure width: 180 mm (7.087 in), height: 5.0 in
- Font: Helvetica/Arial, size 7 base
- Landscape colormap: RdBu_r

## QC pass — 2026-05-11

| Item | Status | Note |
|------|--------|------|
| No embedded title | ✓ | Removed `fig.suptitle(...)` (lines 320–322) |
| Text ≥7pt | ✓ | Raised all sub-7pt elements: tick labels 6→7, axis labels 6–6.5→7, legends 5–5.5→7, bar annotations 5–5.5→7, landscape annotation box 5.2→7, colorbar 6–6.5→7 |
| No text overlap | ✓ | Visual inspection confirmed; Panel B footnote tight but not overlapping |
| Legend clear | ✓ | Panel A: per-subject legend upper-right; Panel B: 2-comp vs Machado lower-right |
| Color consistent | ✓ | Sub-08 orange #E07B2C, Sub-09 teal #2D8E8B, observed black #222222 |
| 300 DPI + PDF | ✓ | Both fig4_output.png (300 dpi) and fig4_output.pdf generated |

Residual issues: none
Next action: acceptable for submission
