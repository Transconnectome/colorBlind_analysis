# S19 — Held-out test-loss across ALL gate-passing candidates

_Characterization of the candidate landscape (NOT re-selection, §0). Answers: did stability-pick also rank well on held-out goodness?_

**Rank metric = grid-null percentile** (within-ROI, cross-ROI comparable; LOW = value beats most arbitrary shifts for that ROI). ΔL vs (0,0) shown alongside but is **NOT cross-ROI comparable** (ROI-difficulty confound — achievable depth below the 1.0 floor differs by ROI; ROI shown per row).

## sub-08 — noLOCO + has-RDM combos ranked by held-out percentile (n=30)

| rank | combo | ROI | full-fit (β_s,β_c) | RDM pct med | folds beat(0,0) | ΔL vs(0,0) med | γ ΔL med | role |
|---|---|---|---|---|---|---|---|---|
| 1 | **γOY|RDMV2|noLOCO** | V2 | (6,-42) | 0.046 | 1.00 | -0.406 | -13.85 | S08-robust ★ (selected, stability-pick) |
| 2 | γYG|RDMV2|noLOCO | V2 | (12,-50) | 0.046 | 0.86 | -0.406 | -12.02 |  |
| 3 | γOY,YG,YP|RDMV2|noLOCO | V2 | (14,-48) | 0.046 | 1.00 | -0.406 | -10.22 |  |
| 4 | γYP|RDMV4|noLOCO | V4 | (38,42) | 0.067 | 1.00 | -0.344 | -36.05 |  |
| 5 | γYP|RDMV1|noLOCO | V1 | (48,22) | 0.070 | 1.00 | -0.541 | -36.05 |  |
| 6 | γ_|RDMV1|noLOCO | V1 | (32,0) | 0.085 | 1.00 | -0.541 | — |  |
| 7 | **γALL|RDMV1|noLOCO** | V1 | (38,-4) | 0.085 | 1.00 | -0.541 | -1.63 | S08-stable/βs-dom (dropped 2026-06) |
| 8 | γYP|RDMV3|noLOCO | V3 | (48,22) | 0.087 | 1.00 | -0.493 | -36.05 |  |
| 9 | γ_|RDMV2|noLOCO | V2 | (4,-26) | 0.130 | 1.00 | -0.360 | — |  |
| 10 | γYP|RDMV2|noLOCO | V2 | (44,30) | 0.130 | 1.00 | -0.376 | -36.05 |  |
| 11 | γALL|RDMV2|noLOCO | V2 | (18,-36) | 0.130 | 1.00 | -0.360 | -1.90 |  |
| 12 | γOY|RDMV4|noLOCO | V4 | (48,-50) | 0.133 | 1.00 | -0.341 | -11.34 |  |
| 13 | γYG|RDMV4|noLOCO | V4 | (50,-34) | 0.133 | 1.00 | -0.341 | -12.69 |  |
| 14 | γOY,YG,YP|RDMV4|noLOCO | V4 | (50,-36) | 0.133 | 1.00 | -0.341 | -13.02 |  |
| 15 | γYP|RDMV1+V4|noLOCO | V1 | (50,-26) | 0.137 | 1.00 | -0.513 | -32.33 |  |
| 16 | γOY|RDMV3|noLOCO | V3 | (6,-42) | 0.146 | 1.00 | -0.382 | -10.87 |  |
| 17 | γ_|RDMV3|noLOCO | V3 | (0,-24) | 0.160 | 1.00 | -0.355 | — |  |
| 18 | γALL|RDMV3|noLOCO | V3 | (0,-24) | 0.160 | 1.00 | -0.355 | -2.06 |  |
| 19 | γOY,YG,YP|RDMV3|noLOCO | V3 | (50,-36) | 0.186 | 1.00 | -0.459 | -13.02 |  |
| 20 | γYG|RDMV3|noLOCO | V3 | (50,-34) | 0.194 | 1.00 | -0.459 | -12.02 |  |
| 21 | γ_|RDMV1+V4|noLOCO | V1 | (36,-26) | 0.197 | 1.00 | -0.513 | — |  |
| 22 | γOY|RDMV1+V4|noLOCO | V1 | (48,-50) | 0.197 | 1.00 | -0.513 | -11.34 |  |
| 23 | γYG|RDMV1+V4|noLOCO | V1 | (50,-34) | 0.197 | 1.00 | -0.513 | -12.69 |  |
| 24 | γOY,YG,YP|RDMV1|noLOCO | V1 | (50,-36) | 0.197 | 1.00 | -0.513 | -13.02 |  |
| 25 | γOY,YG,YP|RDMV1+V4|noLOCO | V1 | (50,-36) | 0.197 | 1.00 | -0.513 | -13.02 |  |
| 26 | γALL|RDMV1+V4|noLOCO | V1 | (48,-36) | 0.197 | 1.00 | -0.513 | -3.16 |  |
| 27 | γYG|RDMV1|noLOCO | V1 | (50,-34) | 0.249 | 1.00 | -0.498 | -10.37 |  |
| 28 | γOY|RDMV1|noLOCO | V1 | (48,-50) | 0.317 | 1.00 | -0.450 | -9.98 |  |
| 29 | γ_|RDMV4|noLOCO | V4 | (36,-26) | 0.380 | 1.00 | -0.280 | — |  |
| 30 | γALL|RDMV4|noLOCO | V4 | (48,-36) | 0.380 | 1.00 | -0.280 | -3.16 |  |

### sub-08 — γ-only noLOCO (no RDM target; γ ΔL only)

| combo | γ ΔL med | folds beat(0,0) |
|---|---|---|
| γYP|RDM_|noLOCO | -36.05 | 1.00 |
| γOY|RDM_|noLOCO | -13.81 | 0.71 |
| γYG|RDM_|noLOCO | -12.69 | 0.71 |
| γOY,YG,YP|RDM_|noLOCO | -9.07 | 0.71 |
| γALL|RDM_|noLOCO | -3.16 | 1.00 |

_sub-08: 36 LOCO combos excluded from held-out rank (LOCO held-out degenerate)._

## sub-09 — noLOCO + has-RDM combos ranked by held-out percentile (n=3)

| rank | combo | ROI | full-fit (β_s,β_c) | RDM pct med | folds beat(0,0) | ΔL vs(0,0) med | γ ΔL med | role |
|---|---|---|---|---|---|---|---|---|
| 1 | γ_|RDMV1|noLOCO | V1 | (0,24) | 0.081 | 1.00 | -0.472 | — |  |
| 2 | γGB|RDMV1|noLOCO | V1 | (2,24) | 0.081 | 1.00 | -0.472 | -1.30 |  |
| 3 | **γALL|RDMV1|noLOCO** | V1 | (2,24) | 0.081 | 1.00 | -0.472 | +0.01 | S09-primary ★ (selected) |

### sub-09 — γ-only noLOCO (no RDM target; γ ΔL only)

| combo | γ ΔL med | folds beat(0,0) |
|---|---|---|
| γALL|RDM_|noLOCO | -0.55 | 0.57 |
| γGB|RDM_|noLOCO | -0.53 | 0.71 |

_sub-09: 6 LOCO combos excluded from held-out rank (LOCO held-out degenerate)._

## Pre-committed interpretation

- **Clustering of percentiles** = held-out goodness non-discriminative among gate-passing candidates (consistent with Test 2a ~20° broad basin) → **stability was a reasonable tiebreak among goodness-equivalent candidates**.
- A non-selected combo clearly topping the selected one = reportable limitation (goodness rank ≠ stability rank), NOT a re-selection (§0).
- A sharp clean win for the selected candidate is suspect (ROI confound).