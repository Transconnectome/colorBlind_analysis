# HC Specificity — V4-CCC + l_topk wretrained

**Loss**: `L = 1·L_ccc + 0.5·l_topk(V4, K=3) + 0.1·L_smooth`
**Simulator**: wretrained
**HC pool**: sub-01..06 (sub-07 V4 excluded — 16 voxels nan risk)

## HC argmins under V4-CCC + l_topk loss

| HC | argmin (β_s, β_c) | norm | L_combined | ρ | l_topk | CCC |
|---|---|---|---|---|---|---|
| sub-01 | (20, +48) | 52.0° | 0.174 | 0.762 | 0.000 | 0.667 |
| sub-02 | (34, +50) | 60.5° | 0.650 | 0.548 | 0.500 | 0.223 |
| sub-03 | (20, +48) | 52.0° | 0.685 | 0.381 | 0.500 | 0.144 |
| sub-04 | (4, -50) | 50.2° | 0.643 | 0.500 | 0.500 | 0.220 |
| sub-05 | (48, -10) | 49.0° | 0.717 | 0.214 | 0.800 | 0.371 |
| sub-06 | (50, +42) | 65.3° | 0.521 | 0.500 | 0.500 | 0.486 |

**HC mean norm**: 54.83°  std: 6.52°  range [49.0, 65.3]

## Bootstrap CI (n_boot=10000)

| Filter | (β_s, β_c) | norm | boot_frac | Verdict |
|---|---|---|---|---|
| BEST sub-08 V4-CCC+l_topk | (+44, +28) | 52.2° | 0.1323 | ✗ inside HC CI |
| BEST sub-09 V4-CCC alone | (+30, +46) | 54.9° | 0.5439 | ✗ inside HC CI |
| Tier 2 sub-08 V4-CCC+SRM RDM | (+50, +24) | 55.5° | 0.6328 | ✗ inside HC CI |
| Tier 2 sub-09 V4-CCC+SRM RDM | (+34, +44) | 55.6° | 0.6372 | ✗ inside HC CI |
| Previous best sub-08 V4-CCC alone | (+16, +40) | 43.1° | 0.0000 | ✗ inside HC CI |
| §3 canonical sub-08 | (+38, -14) | 40.5° | 0.0000 | ✗ inside HC CI |
| Phase A LOCO sub-09 | (+6, -22) | 22.8° | 0.0000 | ✗ inside HC CI |

## Files
- `hc_argmins.csv` — per-HC argmin under V4-CCC+l_topk
- `hc_specificity.csv` — per-candidate specificity bootstrap result
- `hc_landscape_sub-XX_V4_V4CCCltopk.png/pdf` — per-HC landscape (6 figs)