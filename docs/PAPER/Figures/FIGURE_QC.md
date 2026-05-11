# Figure QC Checklist — colorBlind_analysis matplotlib pipeline

After every `generate_figN.py` run, the generating agent MUST read back the PNG with the image-capable Read tool and verify all items below before declaring the figure done.

## Mandatory visual checklist

### Layout & structure
- [ ] Figure title NOT embedded in the figure body — title belongs in the manuscript caption only
- [ ] Panel labels (A, B, C …) are bold, same font size (10pt), top-left of each panel
- [ ] No panel overflows into adjacent panel space
- [ ] White space at figure edges ≤ 5mm (no large blank margins)

### Text readability
- [ ] All text ≥ 7pt at final print size (180mm wide = two-column)
- [ ] Axis labels present on every panel (x and y)
- [ ] No text overlapping with data, bars, or other text
- [ ] Tick labels readable (not rotated >45° unless unavoidable)

### Data display
- [ ] Legend does not overlap with data points or bars
- [ ] Error bars (SEM/SD) labeled in legend or caption
- [ ] Significance markers (*, **, ns) placed without ambiguity
- [ ] Color scheme consistent with paper convention:
  - HC group: gray bars, individual dots as gray circles
  - sub-08 deutan: orange / warm (#E07030 or similar)
  - sub-09 protan: teal / cool (#30A090 or similar)
  - HC individuals (dots): light gray circles
- [ ] Hue colors for stimuli derived from `utils_color_decoding.py` STIM_LAB values

### Publication compliance
- [ ] 300 DPI PNG + vector PDF both generated
- [ ] Figure width: 180mm (two-column) or 86mm (single-column) — do not exceed
- [ ] No rasterized elements inside PDF that should be vector (matplotlib default is fine)
- [ ] Font: DejaVu Sans or Arial (avoid bitmap fonts)

## QC output format

After visual inspection, the agent must append to `FIGURE_NOTES.md`:

```
## QC pass — YYYY-MM-DD

| Item | Status | Note |
|------|--------|------|
| No embedded title | ✓/✗ | |
| Text ≥7pt | ✓/✗ | |
| No text overlap | ✓/✗ | |
| Legend clear | ✓/✗ | |
| Color consistent | ✓/✗ | |
| 300 DPI + PDF | ✓/✗ | |

Residual issues: [list or "none"]
Next action: [fix now / acceptable / defer to final polish]
```

If any ✗ items exist, fix them in the same session before closing.

## Common fixes

| Issue | Fix |
|---|---|
| Embedded figure title | Remove `fig.suptitle(...)` or `ax.set_title("Figure N ...")` |
| Legend overlap | `ax.legend(loc='upper left', bbox_to_anchor=(1, 1))` or `bbox_inches='tight'` |
| Text too small | Increase `fontsize` param or set `plt.rcParams['font.size'] = 8` globally |
| Text overlap | Adjust annotation offset: `xytext=(x, y+offset)` |
| Bars cut off | `plt.tight_layout(pad=0.5)` or adjust `subplot_adjust` |
