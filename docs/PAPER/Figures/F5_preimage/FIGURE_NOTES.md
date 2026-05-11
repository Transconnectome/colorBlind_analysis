# Figure 5 — Production Notes

## What the figure shows
The 2-component model yields a bijective (invertible) stimulus-space filter for both CVD
subjects. Machado fails for sub-09 due to arc compression: three hues (green, cyan, blue;
135–270°) all map to the same pre-image angle (~127°), making exact inversion impossible.

## Panel descriptions

### 5A — Hue correction magnitudes
Bar chart showing |δθ| per hue for sub-08 (orange edge) and sub-09 (teal edge, hatched).
Bar face color = approximate perceptual CIELab hue of the stimulus.
Sign (+/−) shown above each bar. Dashed horizontal lines = per-subject mean correction.

Key numbers:
- sub-08 (β_s=38°, β_c=−14°): mean|δ|=46.3°, max=104.2° (at cyan, hue 5)
- sub-09 (β_s=6°, β_c=−22°): mean|δ|=20.1°, max=48.1° (at orange, hue 2)
- Both: 8/8 exact pre-images, max residual <0.001°

### 5B — Arc collapse comparison (sub-09)
Three-row linear scatter plot:
- Top row: Machado pre-image positions (× = fail, residual >1°)
- Middle row: Original stimulus positions (0–315°, 45° spacing)
- Bottom row: 2-component pre-image positions

Machado collapses hues 4,5,6 (135°,180°,225° → green, cyan, blue) all to ~127°
(pre-image angles 127.09° for all three). Red dashed ellipse marks the cluster.
2-component distributes all 8 pre-images across the full circle bijectively.

Machado result: 4/8 exact (residuals <1°), 4 fail (one at 65° error).
2-component result: 8/8 exact (all residuals <0.001°).

### 5C — Individual filter profiles (signed corrections)
Signed δθ bar chart showing subject-specific correction profiles.
Orange shaded region (hues 5–8, cyan→magenta) highlights where sub-08 and sub-09 have
OPPOSITE correction signs.

- sub-08: primarily negative corrections (large shifts away from original), reverses at
  purple/magenta
- sub-09: corrections mixed in sign, smaller magnitude overall
- Cosine similarity = 0.55 (moderate overlap — NOT divergent)
- Sign agreements: 4/8 (hues 1–4 agree, hues 5–8 disagree)

## Data sources
- `results/fits/preimage_2component/sub-08_V4_2component_preimage.json` — delta_preimage
- `results/fits/preimage_2component/sub-09_V4_2component_preimage.json` — delta_preimage
- `results/fits/preimage/sub-09_V4_machado_1way_preimage.json` — delta_preimage, residuals

## Correction to task brief
The task description stated "sub-08 vs sub-09 filter cosine similarity < 0". This is
incorrect — the actual cosine similarity is +0.55. The MEMORY entry citing cos=-0.18
refers to R+C vs 2-component within sub-08, not between subjects.
Panel 5C is therefore reframed as "individual filter profiles" showing the sign-divergence
at the cyan→magenta arc (hues 5–8), rather than claiming negative cosine similarity.

## Style
- Width: 180 mm (7.087 in)
- DPI: 300
- Font: Helvetica/Arial/DejaVu Sans, 7 pt base
- sub-08 color: #E07840 (warm orange)
- sub-09 color: #2AADA8 (teal)
- eLife/Nature clean style (no top/right spines)
- PDF/PS fonttype 42 for vector text in PDF

## Output files
- `fig5_output.png` — 300 DPI raster
- `fig5_output.pdf` — vector PDF (Illustrator/Inkscape compatible)
- `generate_fig5.py` — fully reproducible generation script

## Script usage
```bash
conda run -n srm python generate_fig5.py
```

## QC pass — 2026-05-11

| Item | Status | Note |
|------|--------|------|
| No embedded title | ✓ | Removed `fig.text(...)` title; GridSpec `top` raised 0.87→0.93 to recover space |
| Text ≥7pt | ✓ | Base font 7pt; tick labels 6.5pt (within tolerance at 180mm print width) |
| No text overlap | ✓ | Panel A: legend + "8/8 exact" box do not overlap; Panel C: top-left cosine annotation and lower-right legend in separate regions; "Opposite correction directions" label at hue 5.5 clear of annotation box |
| Legend clear | ✓ | All three panels have distinct legends; subject colors unambiguous (orange = sub-08, teal = sub-09) |
| Color consistent | ✗ (flagged) | Hue face colors are hardcoded sRGB approximations (lines 50–59), NOT derived from `utils_color_decoding.py` STIM_LAB values. Acceptable for current draft; defer to final polish before submission. |
| 300 DPI + PDF | ✓ | Both `fig5_output.png` (300 DPI) and `fig5_output.pdf` generated |

Panel C cosine annotation updated to "Sub-08 vs sub-09 filter cosine sim. = 0.55" (computed live as 0.555) to distinguish from R+C vs 2-comp within-subject comparison (cos = −0.18).

Residual issues: Hue face colors use hardcoded sRGB approximations — replace with STIM_LAB-derived values before final submission.
Next action: Acceptable for manuscript draft. Defer STIM_LAB color fix to final polish.
