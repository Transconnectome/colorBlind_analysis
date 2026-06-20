# phase_supplementary — Supplementary neural analyses (paper backing)

Consolidates supporting analyses whose results are cited in the paper but were
previously scattered across other phase folders and hard to locate. **No new
data processing** — these read frozen result JSONs and produce paper-ready
tables + figures.

## S1 — Overall cortical color signal is PRESERVED in CVD

**Backs the abstract claim**: the cortical color representation in CVD is
*"not reduced in overall signal but distorted in structure."*

This is the **univariate** counterpart to the paper's multivariate
(LORO/LOCO/RDM/SRM) results. It is the missing N1-type analysis (cf. Tregillus
et al. 2021, the direct CVD-fMRI comparison study, which used univariate
cone-opponent amplitude): it shows the *signal magnitude itself* is not
attenuated in CVD, so the multivariate distortions are about **pattern/geometry,
not amplitude**.

### Result (HC n=7 vs CVD n=3, per ROI)

Five univariate signal-quality metrics — mean |β| (signal magnitude), median
SNR, color modulation depth, run-to-run reliability, spatial variance — show
**no HC–CVD group difference at any ROI** (Welch's t, all p > 0.09). Every CVD
subject (sub-08/09/10) falls **within the HC range** on mean |β| (Crawford &
Howell single-case, all p > 0.18). None of these metrics correlate with SRM
disparity (0/20 Pearson tests significant, all p > 0.13) → the geometric
distortion is **not** a signal-quality confound. Voxel-level color selectivity
is strong in both groups (1-way ANOVA F > 4, p < 0.001 in nearly all ROIs).

Full per-metric table: `results/overall_signal_summary_table.md`.
Figure: `figures/overall_signal_preserved.{png,pdf}`.

### Citable statement (ready for Methods/Results/Supplementary)

> Activation magnitude (mean |β|), signal-to-noise ratio, color modulation
> depth, and run-to-run reliability did not differ between HC and CVD groups
> across all ROIs (Welch's t-tests, all p > 0.09). None of these metrics
> correlated significantly with SRM disparity (Pearson r, all p > 0.13),
> confirming that the geometric differences in shared color representations are
> not attributable to group differences in signal quality or activation
> amplitude.

### Provenance (source of the frozen numbers)

- Source analysis: `analysis/phase2_SRM_across_between/activation_prior_analysis.py`
  (2026-03-27), input `amplitudes_raw.npy` (C010, all 10 subjects).
- Frozen results: `results/overall_signal_results.json`
  (verbatim copy of `phase2_SRM_across_between/results/activation_prior/activation_prior_results.json`).
- Original writeup: `phase2_SRM_across_between/results/RESULTS_PRESRM_ACTIVATION.md`.

### Regenerate the figure + table (local, no server)

```bash
conda activate srm
python scripts/plot_overall_signal.py
```

Reads the local JSON, writes `figures/overall_signal_preserved.{png,pdf}` and
`results/overall_signal_summary_table.md`. Matplotlib only (no seaborn).

## Files

| Path | What |
|---|---|
| `scripts/plot_overall_signal.py` | Reads frozen JSON → S1 figure + summary table |
| `results/overall_signal_results.json` | Frozen univariate results (10 subj × 4 ROI) |
| `results/overall_signal_summary_table.md` | Per-metric Welch HC vs CVD table |
| `figures/overall_signal_preserved.{png,pdf}` | 2×2 paper figure (4 metrics × 4 ROI) |
