# S6' HC Subset Resample — Spearman-Primary Report

**Design**: For each (subject, ROI), enumerate all C(n,k) HC subsets for k∈{4,5,6}, recompute hc_W, ΔRDM_obs, and ΔRDM_sim from subset only, then refit R+C 1-DOF (g grid, Δλ_DPS fixed) and 2-Component (β_s, β_c symmetric grid step 2). Loss = 1 − Spearman ρ (Nili 2014 primary metric). Cosine recorded as secondary.

**Note on V4 cells**: `load_hc_pool` drops sub-07 a priori (16 voxels → degenerate RDM). V4 effective n=6 HCs → C(6,k) subsets k∈{4,5,6} = 15+6+1 = **22 subsets**, NOT 63. V1 cells have full n=7 → 35+21+7 = 63 subsets.

## Main table

| Cell | Model | n | Spearman ρ median | Spearman ρ 95% CI | Cosine median | Cosine 95% CI | Param median ± SD | Sub-04 effect (Δρ median) | Sub-04 param effect |
|---|---|---|---|---|---|---|---|---|---|
| sub-08 V1 | R+C | 63 | +0.257 | [+0.135, +0.390] | +0.025 | [-0.041, +0.124] | 2.70 ± 0.36 | with=+0.263 w/o=+0.245 Δ=+0.018 | with=2.40 w/o=2.80 |
| sub-08 V1 | 2-Comp | 63 | +0.346 | [+0.218, +0.415] | +0.136 | [+0.051, +0.302] | 22.00 ± 22.83 | with=+0.338 w/o=+0.360 Δ=-0.021 | with=10.00 w/o=25.00 |
| sub-08 V4 | R+C | 22 | +0.305 | [+0.201, +0.426] | +0.138 | [+0.066, +0.219] | 0.00 ± 0.91 | with=+0.271 w/o=+0.328 Δ=-0.057 | with=0.00 w/o=0.00 |
| sub-08 V4 | 2-Comp | 22 | +0.468 | [+0.352, +0.665] | +0.330 | [+0.050, +0.465] | -41.00 ± 21.17 | with=+0.492 w/o=+0.424 Δ=+0.067 | with=-40.00 w/o=-45.00 |
| sub-09 V1 | R+C | 63 | +0.271 | [+0.146, +0.370] | +0.093 | [+0.020, +0.176] | 2.90 ± 0.49 | with=+0.297 w/o=+0.222 Δ=+0.075 | with=2.90 w/o=2.75 |
| sub-09 V1 | 2-Comp | 63 | +0.455 | [+0.322, +0.550] | +0.299 | [+0.136, +0.422] | 4.00 ± 12.09 | with=+0.424 w/o=+0.490 Δ=-0.065 | with=6.00 w/o=2.00 |
| sub-09 V4 | R+C | 22 | +0.192 | [+0.151, +0.269] | +0.114 | [+0.016, +0.225] | 1.95 ± 0.97 | with=+0.210 w/o=+0.166 Δ=+0.044 | with=1.95 w/o=2.38 |
| sub-09 V4 | 2-Comp | 22 | +0.286 | [+0.190, +0.453] | +0.260 | [+0.046, +0.338] | -2.00 ± 26.80 | with=+0.270 w/o=+0.307 Δ=-0.037 | with=-2.00 w/o=-26.00 |

## Paired comparison (2-Comp vs R+C, per-subset matched)

| Cell | n | 2-Comp ρ > R+C ρ | Median Δρ (2C − R+C) | Median Δcos | Wilcoxon W (greater) | Wilcoxon p |
|---|---|---|---|---|---|---|
| sub-08 V1 | 63 | 54/63 (85.7%) | +0.063 | +0.086 | 1799.0 | 0.0000 |
| sub-08 V4 | 22 | 20/22 (90.9%) | +0.178 | +0.203 | 246.0 | 0.0000 |
| sub-09 V1 | 63 | 63/63 (100.0%) | +0.180 | +0.195 | 2016.0 | 0.0000 |
| sub-09 V4 | 22 | 21/22 (95.5%) | +0.102 | +0.125 | 251.0 | 0.0000 |

## Paper-relevant verdicts

### Q1 — 2-Comp robustness: Is Spearman ρ 95% CI > 0?

| Cell | Model | 95% CI [q025, q975] | CI excludes 0? |
|---|---|---|---|
| sub-08 V1 | R+C | [+0.135, +0.390] | ✓ |
| sub-08 V1 | 2-Comp | [+0.218, +0.415] | ✓ |
| sub-08 V4 | R+C | [+0.201, +0.426] | ✓ |
| sub-08 V4 | 2-Comp | [+0.352, +0.665] | ✓ |
| sub-09 V1 | R+C | [+0.146, +0.370] | ✓ |
| sub-09 V1 | 2-Comp | [+0.322, +0.550] | ✓ |
| sub-09 V4 | R+C | [+0.151, +0.269] | ✓ |
| sub-09 V4 | 2-Comp | [+0.190, +0.453] | ✓ |

### Q2 — Cosine vs Spearman concordance: same model ranking?

Compare median Spearman ρ and median cosine: does 2-Comp > R+C hold under both metrics?

| Cell | R+C med ρ | 2C med ρ | 2C > R+C (ρ) | R+C med cos | 2C med cos | 2C > R+C (cos) | Concordant? |
|---|---|---|---|---|---|---|---|
| sub-08 V1 | +0.257 | +0.346 | 2C | +0.025 | +0.136 | 2C | ✓ |
| sub-08 V4 | +0.305 | +0.468 | 2C | +0.138 | +0.330 | 2C | ✓ |
| sub-09 V1 | +0.271 | +0.455 | 2C | +0.093 | +0.299 | 2C | ✓ |
| sub-09 V4 | +0.192 | +0.286 | 2C | +0.114 | +0.260 | 2C | ✓ |

### Q3 — Sub-04 outlier dependence

Δρ = median(ρ | sub-04 in subset) − median(ρ | sub-04 absent). Positive Δρ means inclusion of sub-04 boosts fit. V4 k=6 subset is unique by construction (n=6 HCs, no sub-04 exclusion possible at k=6 for V4 since sub-07 already dropped). For V4-without-sub-04 we only have k∈{4,5}.

| Cell | Model | with sub-04 med ρ | w/o sub-04 med ρ | Δρ |
|---|---|---|---|---|
| sub-08 V1 | R+C | +0.263 | +0.245 | +0.018 |
| sub-08 V1 | 2-Comp | +0.338 | +0.360 | -0.021 |
| sub-08 V4 | R+C | +0.271 | +0.328 | -0.057 |
| sub-08 V4 | 2-Comp | +0.492 | +0.424 | +0.067 |
| sub-09 V1 | R+C | +0.297 | +0.222 | +0.075 |
| sub-09 V1 | 2-Comp | +0.424 | +0.490 | -0.065 |
| sub-09 V4 | R+C | +0.210 | +0.166 | +0.044 |
| sub-09 V4 | 2-Comp | +0.270 | +0.307 | -0.037 |

### Q4 — Paper-grade claim: 2-Comp Spearman ρ robustly > 0?

- **sub-08 V1**: median ρ = +0.346, 95% CI [+0.218, +0.415] → **PASS** (95% CI strictly above 0)
- **sub-08 V4**: median ρ = +0.468, 95% CI [+0.352, +0.665] → **PASS** (95% CI strictly above 0)
- **sub-09 V1**: median ρ = +0.455, 95% CI [+0.322, +0.550] → **PASS** (95% CI strictly above 0)
- **sub-09 V4**: median ρ = +0.286, 95% CI [+0.190, +0.453] → **PASS** (95% CI strictly above 0)

### Q5 — 2-Comp vs R+C paired comparison (Wilcoxon)

- **sub-08 V1**: 2-Comp better in 54/63 subsets, median Δρ = +0.063, Wilcoxon (greater) p = 0.0000 ✓
- **sub-08 V4**: 2-Comp better in 20/22 subsets, median Δρ = +0.178, Wilcoxon (greater) p = 0.0000 ✓
- **sub-09 V1**: 2-Comp better in 63/63 subsets, median Δρ = +0.180, Wilcoxon (greater) p = 0.0000 ✓
- **sub-09 V4**: 2-Comp better in 21/22 subsets, median Δρ = +0.102, Wilcoxon (greater) p = 0.0000 ✓

## Boundary-hit diagnostics (2-Comp)

Fraction of subsets whose 2-Comp grid optimum lands on the [−50, +50] boundary (β_s or β_c). High rates indicate the Spearman-best is being pushed beyond the search box and the median/CI estimates are *clipped*. Treat with caution.

| Cell | n | β_s boundary | β_c boundary |
|---|---|---|---|
| sub-08 V1 | 63 | 0/63 (0%) | 1/63 (2%) |
| sub-08 V4 | 22 | 2/22 (9%) | 1/22 (5%) |
| sub-09 V1 | 63 | 0/63 (0%) | 43/63 (68%) |
| sub-09 V4 | 22 | 9/22 (41%) | 3/22 (14%) |

## Implementation notes

- C_baseline = `create_basis_full(K=6, 'fe')[HUE_ANGLES.astype(int)]` (matches `s5_all_paths_fit.py` L4 convention).
- 2-Comp grid: symmetric β_s ∈ [−50, +50] (51 pts), β_c ∈ [−50, +50] (51 pts), step 2°. This is wider than the `two_comp.BS_GRID` (β_s ∈ [0, 50]) used elsewhere — deliberate to let resampling reveal sign-reversed solutions.
- R+C grid: g ∈ [0, 3] step 0.05 (61 pts), Δλ fixed at DPS lit (sub-08=6 nm, sub-09=10 nm).
- Spearman ρ: `scipy.stats.spearmanr` default (average ranks for ties). Degenerate (constant) inputs handled by returning ρ=0.
- Cosine: `np.dot(a,b) / (||a||·||b||)`, 0 if either vector is zero.
- σ=21° not applicable here (L4 has no σ dependence — purely δθ-driven).

## Files

- Per-cell × model JSON: `{subject}_{ROI}_{RC|2Comp}.json`
- Master summary: `master_summary.json`
- This report: `SUBSET_REPORT.md`
- Distribution figure: `viz_distribution.png`