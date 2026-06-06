# Paper Figures — Source of Truth (2026-06-05)

Seven main figures. Captions live in the LaTeX (`Methods/methods_v2.tex`,
`Results/results_v4.tex`), **not** in `FIGURE_CAPTIONS.md` (that file is
2026-05-11 and carries superseded filter parameters — kept for history only).

Figure numbers are assigned by LaTeX float order via semantic `\ref` labels, so
the legacy filenames (e.g. `fig2_loro_loco` = Figure 3) do not match the number.
Map below is authoritative.

| Fig | `\label`         | File (PDF/PNG)        | Generating script                                   | Type        | Data |
|----:|------------------|-----------------------|-----------------------------------------------------|-------------|------|
| 1   | `fig:paradigm`   | `fig1_paradigm`       | `scripts/generate_fig1.py`                           | schematic   | — (PowerPoint/mpl) |
| 2   | `fig:forward`    | `fig_forward_encoder` | `../Scripts/generate_forward_encoder_fig.py`        | schematic   | — (illustrative) |
| 3   | `fig:loco`       | `fig2_loro_loco`      | `scripts/generate_fig2.py`                           | data chart  | LORO/LOCO results |
| 4   | `fig:geometry`   | `fig3_geometry`       | `scripts/generate_fig3.py`                           | data chart  | ΔRDM / disparity |
| 5   | `fig:pipeline`   | `fig5_pipeline`       | `scripts/phase2/generate_fig5_pipeline.py`          | schematic   | — (illustrative) |
| 6   | `fig:landscape`  | `fig6_landscape`      | `scripts/phase2/generate_fig6_landscape.py`         | data chart  | real (7-HC pool + 300 resamples) |
| 7   | `fig:filter`     | `fig7_filter`         | `scripts/phase2/generate_fig7_filter.py`            | rendering   | analytical pre-image |

## Canonical Phase-2 parameters (PIPELINE_2_CLOSURE.md 2026-06-01)

- sub-08 deutan: **(β_s, β_c) = (+6°, −42°)**, loss γ_OY + RDM_V2
- sub-09 protan: **(β_s, β_c) = (+2°, +24°)**, loss γ_all + RDM_V1

Figs 6 & 7 use these via the canonical A13 forward `two_comp.py:forward_2comp`
(raw CIELab nominal-θ). Sign check: sub-08 c4 green δθ = −36.3° (NOT the frozen
+19° variant).

## Regenerating figs 5–7

```bash
conda activate srm
cd docs/PAPER/Figures/scripts/phase2
python generate_fig5_pipeline.py     # schematic, no data
python generate_fig6_landscape.py    # imports viz_closure_ground_plot (real data)
python generate_fig7_filter.py       # imports two_comp + stim_lab_render
```

These three scripts import canonical modules from
`analysis/future_phase2_filter_optimization/scripts/` (added to `sys.path` at
runtime). They are reproducible in-repo but **not** standalone — they depend on
that package and, for fig 6, on the local C010 amplitudes at
`analysis/phase1_procrustes_decoding/results/full_dataset_C010/`.

## Superseded (archived 2026-06-05)

Moved to `../archive/figures_superseded_2026-06-05/`:
`fig4_twocomp` (old landscape, stale params, never wired), `fig5_preimage` +
`fig5a/b_preimage` (old 4-column filter, stale params (38,−14)/(6,−22)).
The old `scripts/generate_fig4.py` (landscape) and `generate_fig5.py` (4-col)
are superseded by `scripts/phase2/` and retained for history only.

## Known open items (NOT yet fixed — need author decision)

1. **Fig 3 metric mismatch**: `generate_fig2.py` plots **MAE (°)** (loads
   `["mae"]`, chance 90°) but the manuscript text/caption report **adjacent
   accuracy** (0.25, 0.13; chance 3/8). One is stale. Reconciling changes the
   reported t/p values — decide the intended metric, then regenerate or rewrite.
