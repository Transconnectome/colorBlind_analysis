# Output Directory Update (2026-02-22)

The CVD distortion figures are now saved to:

```
analysis/future_phase3_filter_optimization/figures/
```

**Previous location** (no longer used):
```
analysis/phase2_decoder_comparing/visualization/cvd_distortion_figures/
```

## Why the change?

These figures are part of the **filter pre-validation** analysis (B1-B3), which uses FDR-corrected pairwise comparisons to identify reliable distortion targets for the filter optimization pipeline.

They belong in the `future_phase3_filter_optimization/` directory alongside:
- `pre_validation/results/fdr_corrected/` - Statistical results
- `figures/` - Visualization outputs

## Files affected

- `create_cvd_distortion_figure.py` - Line 441: Updated default output path
- All generated figures now go to `future_phase3_filter_optimization/figures/`

## Old files

The old directory `phase2_decoder_comparing/visualization/cvd_distortion_figures/` can be safely deleted.

---
**Date:** 2026-02-22
