# S7 (C) revised — R+C vs 2-Comp δθ agreement metrics

**Replaces Spearman** (rank-only, n=8 inadequate) with magnitude-aware metrics. Primary metric: **Lin's CCC** (concordance with identity line y=x).

## CCC interpretation (Lin 1989)
- < 0.90 poor agreement
- 0.90–0.95 moderate
- 0.95–0.99 substantial
- ≥ 0.99 almost perfect


## Main results table

| cell | Pearson r | Spearman ρ | **CCC** | CCC 95% CI | cos | MAE (°) | RMSE (°) | slope | intercept |
|---|---|---|---|---|---|---|---|---|---|
| sub-08 V1 | +0.552 | +0.595 | **+0.267** | [-0.07, +0.51] | +0.54 | 23.1 | 27.1 | +2.14 | +3.0° |
| sub-08 V4 | +0.552 | +0.595 | **+0.312** | [-0.08, +0.59] | +0.54 | 22.5 | 26.6 | +1.78 | +3.0° |
| sub-09 V1 | +0.101 | +0.119 | **+0.101** | [-0.67, +0.70] | +0.10 | 20.6 | 27.6 | +0.10 | +0.1° |
| sub-09 V4 | +0.101 | +0.119 | **+0.101** | [-0.67, +0.70] | +0.10 | 20.6 | 27.6 | +0.10 | +0.1° |

## Bland-Altman per cell

| cell | bias (°) | SD(diff) | LoA low (°) | LoA high (°) |
|---|---|---|---|---|
| sub-08 V1 | +1.42 | 28.91 | -55.24 | +58.08 |
| sub-08 V4 | +1.70 | 28.39 | -53.95 | +57.35 |
| sub-09 V1 | +1.10 | 29.47 | -56.67 | +58.86 |
| sub-09 V4 | +1.10 | 29.47 | -56.67 | +58.86 |

## Per-color residual diff = (δθ_2C − δθ_RC)

| cell | red | orange | yellow | green | cyan | blue | purple | magenta |
|---|---|---|---|---|---|---|---|---|
| sub-08 V1 | +28.2 | +41.0 | +29.0 | -0.5 | -28.8 | -21.7 | -35.4 | -0.4 |
| sub-08 V4 | +27.6 | +40.6 | +28.8 | -0.5 | -28.4 | -17.4 | -36.4 | -0.6 |
| sub-09 V1 | +0.4 | +18.1 | +25.3 | +17.6 | +3.6 | +22.1 | -64.2 | -14.0 |
| sub-09 V4 | +0.4 | +18.1 | +25.3 | +17.6 | +3.6 | +22.1 | -64.2 | -14.0 |

## Interpretation

CCC threshold for paper-defensible 'two models = same distortion': ≥ 0.95.

- **sub-08 V1**: CCC=+0.267 → ✗ disagreement. Slope=+2.14 (1.0=identity), bias=+1.42°.
- **sub-08 V4**: CCC=+0.312 → ✗ disagreement. Slope=+1.78 (1.0=identity), bias=+1.70°.
- **sub-09 V1**: CCC=+0.101 → ✗ disagreement. Slope=+0.10 (1.0=identity), bias=+1.10°.
- **sub-09 V4**: CCC=+0.101 → ✗ disagreement. Slope=+0.10 (1.0=identity), bias=+1.10°.
