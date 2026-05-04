# Loss Inventory & HC Sanity Check

Generated: 2026-05-03 by `build_loss_inventory.py`

## Sanity check principle

A "useful" loss should give HC subjects (β_s, β_c) ≈ (0, 0) (no compensation needed) and CVD subjects non-trivial (β_s, β_c) (compensation needed).

Quantitative metric:

  - **HC_mean_norm** = mean(||(β_s, β_c)||) over HC subjects
  - **CVD/HC ratio** = CVD_norm / HC_mean_norm
  - **Threshold**: ratio > 1 means CVD distortion > HC noise; ratio < 1 means loss is fitting noise (HC and CVD indistinguishable).

## Summary table — point estimates

| Loss variant | ROI | HC_mean_norm | sub-08_norm | sub-08/HC | sub-09_norm | sub-09/HC | Verdict (point) |
|---|---|---:|---:|---:|---:|---:|---|
| `cycle12_cross_roi` | V4+V1 | 27.8 (n=6) | 77.9 | 2.80 | 39.7 | 1.43 | ~ both CVD ≥ HC |
| `cycle15_opt2_v4mwj_v1lrank` | V4 | 37.7 (n=6) | 77.9 | 2.07 | 69.7 | 1.85 | ✓ both CVD > HC |
| `cycle15_opt3_v4mwj_v1mwj` | V4 | 29.9 (n=6) | 64.4 | 2.15 | 0.0 | 0.00 | ? insufficient data |
| `cycle15_opt4_v4mwj_v4spear` | V4 | 35.7 (n=6) | 87.2 | 2.44 | 40.0 | 1.12 | ~ both CVD ≥ HC |
| `l_dir` | V4 | 44.6 (n=6) | 98.4 | 2.20 | 60.0 | 1.34 | ~ both CVD ≥ HC |
| `l_mag` | V4 | 67.5 (n=6) | 72.8 | 1.08 | 81.4 | 1.21 | ~ both CVD ≥ HC |
| `l_rank` | V4 | 46.0 (n=6) | 95.3 | 2.07 | 58.0 | 1.26 | ~ both CVD ≥ HC |
| `l_rank_V1` | V1 | 63.8 (n=6) | 77.9 | 1.22 | 53.7 | 0.84 | × partial (one CVD < HC) |
| `l_topk_V1` | V1 | 60.2 (n=6) | 60.0 | 1.00 | 60.0 | 1.00 | ✗ CVD < HC (loss captures noise) |
| `l_topk_jaccard` | V4 | 61.4 (n=6) | 68.3 | 1.11 | 60.0 | 0.98 | × partial (one CVD < HC) |
| `mw_jaccard_loss` | V4 | 60.4 (n=6) | 68.3 | 1.13 | 69.7 | 1.15 | ~ both CVD ≥ HC |
| `norm_resid` | V4 | 83.6 (n=6) | 96.8 | 1.16 | 50.1 | 0.60 | × partial (one CVD < HC) |
| `pearson_r` | V4 | 44.6 (n=6) | 98.4 | 2.20 | 60.0 | 1.34 | ~ both CVD ≥ HC |
| `sign_agree` | V4 | 71.5 (n=6) | 58.9 | 0.82 | 60.0 | 0.84 | ✗ CVD < HC (loss captures noise) |
| `spearman_r` | V4 | 46.0 (n=6) | 95.3 | 2.07 | 58.0 | 1.26 | ~ both CVD ≥ HC |

## Summary table — statistical sanity (bootstrap + rank)

Per user critique 2026-05-03: HC pool of n=6 sensitive to outliers (sub-04 in particular).

- **emp_p**: fraction of HC subjects with norm ≥ CVD norm (rank-based; lower = CVD more outlier above HC distribution; sig threshold ~0.20 = at most 1/6 HC above)
- **boot_HC_CI**: 95% bootstrap CI of HC mean norm (10000 resamples, with replacement)
- **CVD>boot_mean frac**: fraction of bootstrap HC means below CVD norm (higher = more reliably distinct)

| Loss variant | ROI | boot_HC_CI | sub-08 | sub-09 | sub-08 emp_p | sub-08 CVD>boot | sub-09 emp_p | sub-09 CVD>boot | Stat verdict |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| `cycle12_cross_roi` | V4+V1 | [7.6, 48.3] | 77.9 | 39.7 | 0.00 (0/6) | 1.00 | 0.33 (2/6) | 0.87 | ✓ one CVD sig (other inside CI) |
| `cycle15_opt2_v4mwj_v1lrank` | V4 | [13.5, 61.5] | 77.9 | 69.7 | 0.00 (0/6) | 1.00 | 0.17 (1/6) | 1.00 | ✓✓ both CVD > HC bootstrap CI |
| `cycle15_opt3_v4mwj_v1mwj` | V4 | [7.5, 54.9] | 64.4 | 0.0 | 0.17 (1/6) | 1.00 | 1.00 (6/6) | 0.00 | ✓ one CVD sig (other inside CI) |
| `cycle15_opt4_v4mwj_v4spear` | V4 | [10.1, 63.4] | 87.2 | 40.0 | 0.00 (0/6) | 1.00 | 0.50 (3/6) | 0.63 | ✓ one CVD sig (other inside CI) |
| `l_dir` | V4 | [16.6, 75.3] | 98.4 | 60.0 | 0.17 (1/6) | 1.00 | 0.33 (2/6) | 0.85 | ✓ one CVD sig (other inside CI) |
| `l_mag` | V4 | [58.2, 76.7] | 72.8 | 81.4 | 0.50 (3/6) | 0.87 | 0.17 (1/6) | 1.00 | ✓ one CVD sig (other inside CI) |
| `l_rank` | V4 | [18.0, 74.9] | 95.3 | 58.0 | 0.17 (1/6) | 1.00 | 0.50 (3/6) | 0.77 | ✓ one CVD sig (other inside CI) |
| `l_rank_V1` | V1 | [47.3, 80.4] | 77.9 | 53.7 | 0.33 (2/6) | 0.94 | 0.67 (4/6) | 0.14 | ~ one marginal |
| `l_topk_V1` | V1 | [60.0, 60.6] | 60.0 | 60.0 | 1.00 (6/6) | 0.00 | 1.00 (6/6) | 0.00 | ✗ neither sig (inside HC CI) |
| `l_topk_jaccard` | V4 | [49.7, 71.5] | 68.3 | 60.0 | 0.33 (2/6) | 0.88 | 0.83 (5/6) | 0.38 | ✗ neither sig (inside HC CI) |
| `mw_jaccard_loss` | V4 | [48.7, 70.5] | 68.3 | 69.7 | 0.17 (1/6) | 0.94 | 0.17 (1/6) | 0.97 | ~~ both marginal |
| `norm_resid` | V4 | [64.9, 98.7] | 96.8 | 50.1 | 0.50 (3/6) | 0.93 | 0.83 (5/6) | 0.00 | ~ one marginal |
| `pearson_r` | V4 | [16.6, 75.3] | 98.4 | 60.0 | 0.17 (1/6) | 1.00 | 0.33 (2/6) | 0.85 | ✓ one CVD sig (other inside CI) |
| `sign_agree` | V4 | [52.8, 88.0] | 58.9 | 60.0 | 0.67 (4/6) | 0.09 | 0.67 (4/6) | 0.09 | ✗ neither sig (inside HC CI) |
| `spearman_r` | V4 | [18.0, 74.9] | 95.3 | 58.0 | 0.17 (1/6) | 1.00 | 0.50 (3/6) | 0.77 | ✓ one CVD sig (other inside CI) |

## Per-subject details (HC dispersion check)


### `cycle12_cross_roi` @ V4+V1

_α·l_topk(V4) + β·l_rank(V1) + 0.2·Tikh (α=β=1)_

| Subject | role | (β_s, β_c) | norm |
|---|---|---|---:|
| sub-01 | HC | (48, 48) | 67.9 |
| sub-02 | HC | (4, 0) | 4.0 |
| sub-03 | HC | (16, 10) | 18.9 |
| sub-04 | HC | (18, 2) | 18.1 |
| sub-05 | HC | (56, -16) | 58.2 |
| sub-06 | HC | (0, 0) | 0.0 |
| sub-08 | **CVD** | **(68, -38)** | **77.9** |
| sub-09 | **CVD** | **(30, 26)** | **39.7** |

### `cycle15_opt2_v4mwj_v1lrank` @ V4

_2·mw_jaccard(V4) + 1·l_rank(V1) + 0.2·Tikh_

| Subject | role | (β_s, β_c) | norm |
|---|---|---|---:|
| sub-01 | HC | (48, 48) | 67.9 |
| sub-02 | HC | (4, 0) | 4.0 |
| sub-03 | HC | (16, 10) | 18.9 |
| sub-04 | HC | (62, -46) | 77.2 |
| sub-05 | HC | (56, -16) | 58.2 |
| sub-06 | HC | (0, 0) | 0.0 |
| sub-08 | **CVD** | **(68, -38)** | **77.9** |
| sub-09 | **CVD** | **(44, 54)** | **69.7** |

### `cycle15_opt3_v4mwj_v1mwj` @ V4

_1·mw_jaccard(V4) + 1·mw_jaccard(V1) + 0.2·Tikh_

| Subject | role | (β_s, β_c) | norm |
|---|---|---|---:|
| sub-01 | HC | (54, 28) | 60.8 |
| sub-02 | HC | (4, 0) | 4.0 |
| sub-03 | HC | (0, 0) | 0.0 |
| sub-04 | HC | (64, -36) | 73.4 |
| sub-05 | HC | (40, 10) | 41.2 |
| sub-06 | HC | (0, 0) | 0.0 |
| sub-08 | **CVD** | **(58, -28)** | **64.4** |
| sub-09 | **CVD** | **(0, 0)** | **0.0** |

### `cycle15_opt4_v4mwj_v4spear` @ V4

_1·mw_jaccard(V4) + 1·(1-spearman_r)(V4) + 0.2·Tikh_

| Subject | role | (β_s, β_c) | norm |
|---|---|---|---:|
| sub-01 | HC | (0, 0) | 0.0 |
| sub-02 | HC | (0, 0) | 0.0 |
| sub-03 | HC | (6, -6) | 8.5 |
| sub-04 | HC | (72, -42) | 83.4 |
| sub-05 | HC | (70, 8) | 70.5 |
| sub-06 | HC | (0, -52) | 52.0 |
| sub-08 | **CVD** | **(70, -52)** | **87.2** |
| sub-09 | **CVD** | **(24, 32)** | **40.0** |

### `l_dir` @ V4

_Directional loss (V4)_

| Subject | role | (β_s, β_c) | norm |
|---|---|---|---:|
| sub-01 | HC | (0, -6) | 6.0 |
| sub-02 | HC | (0, -10) | 10.0 |
| sub-03 | HC | (16, -14) | 21.3 |
| sub-04 | HC | (80, -60) | 100.0 |
| sub-05 | HC | (80, -38) | 88.6 |
| sub-06 | HC | (2, -42) | 42.0 |
| sub-08 | **CVD** | **(78, -60)** | **98.4** |
| sub-09 | **CVD** | **(0, 60)** | **60.0** |

### `l_mag` @ V4

_Magnitude loss (V4)_

| Subject | role | (β_s, β_c) | norm |
|---|---|---|---:|
| sub-01 | HC | (60, -10) | 60.8 |
| sub-02 | HC | (78, 32) | 84.3 |
| sub-03 | HC | (70, 30) | 76.2 |
| sub-04 | HC | (32, -44) | 54.4 |
| sub-05 | HC | (64, -42) | 76.6 |
| sub-06 | HC | (52, 8) | 52.6 |
| sub-08 | **CVD** | **(44, 58)** | **72.8** |
| sub-09 | **CVD** | **(72, 38)** | **81.4** |

### `l_rank` @ V4

_1 - Spearman ρ (V4)_

| Subject | role | (β_s, β_c) | norm |
|---|---|---|---:|
| sub-01 | HC | (0, -2) | 2.0 |
| sub-02 | HC | (0, -4) | 4.0 |
| sub-03 | HC | (2, 24) | 24.1 |
| sub-04 | HC | (80, -54) | 96.5 |
| sub-05 | HC | (70, -28) | 75.4 |
| sub-06 | HC | (46, 58) | 74.0 |
| sub-08 | **CVD** | **(74, -60)** | **95.3** |
| sub-09 | **CVD** | **(0, 58)** | **58.0** |

### `l_rank_V1` @ V1

_1 - Spearman ρ (V1)_

| Subject | role | (β_s, β_c) | norm |
|---|---|---|---:|
| sub-01 | HC | (76, 60) | 96.8 |
| sub-02 | HC | (0, -60) | 60.0 |
| sub-03 | HC | (80, 26) | 84.1 |
| sub-04 | HC | (0, -48) | 48.0 |
| sub-05 | HC | (52, -30) | 60.0 |
| sub-06 | HC | (0, 34) | 34.0 |
| sub-08 | **CVD** | **(68, -38)** | **77.9** |
| sub-09 | **CVD** | **(38, 38)** | **53.7** |

### `l_topk_V1` @ V1

_Top-K Jaccard distance (V1)_

| Subject | role | (β_s, β_c) | norm |
|---|---|---|---:|
| sub-01 | HC | (12, 60) | 61.2 |
| sub-02 | HC | (0, -60) | 60.0 |
| sub-03 | HC | (0, -60) | 60.0 |
| sub-04 | HC | (0, -60) | 60.0 |
| sub-05 | HC | (0, -60) | 60.0 |
| sub-06 | HC | (0, -60) | 60.0 |
| sub-08 | **CVD** | **(0, -60)** | **60.0** |
| sub-09 | **CVD** | **(0, -60)** | **60.0** |

### `l_topk_jaccard` @ V4

_Top-K Jaccard distance (V4)_

| Subject | role | (β_s, β_c) | norm |
|---|---|---|---:|
| sub-01 | HC | (0, -60) | 60.0 |
| sub-02 | HC | (0, -34) | 34.0 |
| sub-03 | HC | (0, -60) | 60.0 |
| sub-04 | HC | (62, -48) | 78.4 |
| sub-05 | HC | (22, 58) | 62.0 |
| sub-06 | HC | (46, 58) | 74.0 |
| sub-08 | **CVD** | **(58, -36)** | **68.3** |
| sub-09 | **CVD** | **(0, -60)** | **60.0** |

### `mw_jaccard_loss` @ V4

_Mann-Whitney Jaccard (V4)_

| Subject | role | (β_s, β_c) | norm |
|---|---|---|---:|
| sub-01 | HC | (32, 60) | 68.0 |
| sub-02 | HC | (0, -34) | 34.0 |
| sub-03 | HC | (0, -60) | 60.0 |
| sub-04 | HC | (62, -48) | 78.4 |
| sub-05 | HC | (22, 58) | 62.0 |
| sub-06 | HC | (0, -60) | 60.0 |
| sub-08 | **CVD** | **(58, -36)** | **68.3** |
| sub-09 | **CVD** | **(44, 54)** | **69.7** |

### `norm_resid` @ V4

_Normalized residual (V4)_

| Subject | role | (β_s, β_c) | norm |
|---|---|---|---:|
| sub-01 | HC | (34, -28) | 44.0 |
| sub-02 | HC | (26, 60) | 65.4 |
| sub-03 | HC | (80, 60) | 100.0 |
| sub-04 | HC | (80, -60) | 100.0 |
| sub-05 | HC | (76, -52) | 92.1 |
| sub-06 | HC | (80, -60) | 100.0 |
| sub-08 | **CVD** | **(76, -60)** | **96.8** |
| sub-09 | **CVD** | **(24, 44)** | **50.1** |

### `pearson_r` @ V4

_Pearson r (V4)_

| Subject | role | (β_s, β_c) | norm |
|---|---|---|---:|
| sub-01 | HC | (0, -6) | 6.0 |
| sub-02 | HC | (0, -10) | 10.0 |
| sub-03 | HC | (16, -14) | 21.3 |
| sub-04 | HC | (80, -60) | 100.0 |
| sub-05 | HC | (80, -38) | 88.6 |
| sub-06 | HC | (2, -42) | 42.0 |
| sub-08 | **CVD** | **(78, -60)** | **98.4** |
| sub-09 | **CVD** | **(0, 60)** | **60.0** |

### `sign_agree` @ V4

_Sign agreement fraction (V4)_

| Subject | role | (β_s, β_c) | norm |
|---|---|---|---:|
| sub-01 | HC | (0, -60) | 60.0 |
| sub-02 | HC | (44, -8) | 44.7 |
| sub-03 | HC | (74, 56) | 92.8 |
| sub-04 | HC | (72, 60) | 93.7 |
| sub-05 | HC | (74, 58) | 94.0 |
| sub-06 | HC | (0, -44) | 44.0 |
| sub-08 | **CVD** | **(10, 58)** | **58.9** |
| sub-09 | **CVD** | **(0, -60)** | **60.0** |

### `spearman_r` @ V4

_Spearman ρ (V4)_

| Subject | role | (β_s, β_c) | norm |
|---|---|---|---:|
| sub-01 | HC | (0, -2) | 2.0 |
| sub-02 | HC | (0, -4) | 4.0 |
| sub-03 | HC | (2, 24) | 24.1 |
| sub-04 | HC | (80, -54) | 96.5 |
| sub-05 | HC | (70, -28) | 75.4 |
| sub-06 | HC | (46, 58) | 74.0 |
| sub-08 | **CVD** | **(74, -60)** | **95.3** |
| sub-09 | **CVD** | **(0, 58)** | **58.0** |

## Verdict legend

- **✓ both CVD > HC** (ratio > 1.5): Loss meaningfully separates CVD from HC. Good candidate.
- **~ both CVD ≥ HC** (1.0 < ratio ≤ 1.5): Marginal. CVD slightly larger but within HC variability range.
- **× partial** (one CVD < HC): Loss works for one subject but not the other. Subject-specific applicability.
- **✗ CVD < HC** (both ratios < 1): Loss is fitting noise. HC subjects look more "compensation-needing" than actual CVD subjects. **REJECT for filter selection.**

## Notes

- Phase A canonical (`L_LOCO`) HC fits not in this inventory — requires re-running `loco_distortion_fit.py` for sub-01..07. Currently flagged as missing.
- Cycle 14 cross-ROI RDM HC values not computed (V1 RDM landscape only generated for sub-08, 09 in cycle14 script).
- Grid bounds: β_s ∈ [0, 80] step 2, β_c ∈ [-60, 60] step 2 (41 × 61 = 2501 points).
- All landscapes computed on local data (`full_dataset_C010_with_residuals`); server canonical phase_a fits use raw `full_dataset_C010` (different).
