# P2a Ranking — sub-08 deutan + sub-09 protan

P2a = mean match score between predicted CVD-percieved color (forward model output) and subject's actual reported HC-name perception (raw_behav.md).
Scoring: exact match = 1.0, adjacent name = partial credit (see `HC_ADJ` in phase3_candidate_analysis_v2.py).

## sub-08 deutan (target = SUB08_ORIGINAL_HC_EQUIV)

| Rank | Filter | β_s | β_c | norm | **P2a** | exact/8 |
|---|---|---|---|---|---|---|
| 1 | sign_agree | 10 | +58 | 58.9° | **0.600** | 4/8 |
| 2 | A wretrained V4-CCC | 16 | +40 | 43.1° | **0.537** | 3/8 |
| 3 | V4-only OLD | 38 | +7 | 38.6° | **0.487** | 2/8 |
| 4 | l_mag | 44 | +58 | 72.8° | **0.463** | 2/8 |
| 5 | Fine grid c2 orange | 44 | -14 | 46.2° | **0.338** | 2/8 |
| 6 | B wfixed   V4-CCC | 46 | -20 | 50.2° | **0.338** | 2/8 |
| 7 | l_rank/spearman_r [edge] | 74 | -60 | 95.3° | **0.325** | 1/8 |
| 8 | β=0 baseline (no filter) | 0 | +0 | 0.0° | **0.325** | 1/8 |
| 9 | Phase A LOCO | 38 | -14 | 40.5° | **0.287** | 1/8 |
| 10 | cycle14_cross_roi_rdm/mw_jaccard/l_topk | 58 | -36 | 68.3° | **0.287** | 1/8 |
| 11 | cycle15_opt3 v4mwj+v1mwj | 58 | -28 | 64.4° | **0.287** | 1/8 |
| 12 | l_dir/pearson_r [edge] | 78 | -60 | 98.4° | **0.263** | 1/8 |
| 13 | norm_resid [edge] | 76 | -60 | 96.8° | **0.263** | 1/8 |
| 14 | A wretrained 4-term/L1/L3a-c | 10 | -32 | 33.5° | **0.250** | 1/8 |
| 15 | B wfixed   4-term | 6 | -48 | 48.4° | **0.250** | 2/8 |
| 16 | cycle12_cross_roi/opt2 | 68 | -38 | 77.9° | **0.200** | 1/8 |
| 17 | cycle15_opt4 v4mwj+v4spear | 70 | -52 | 87.2° | **0.200** | 1/8 |

### Per-color detail (sub-08 top 3)

| Rank | Filter | c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 |
|---|---|---|---|---|---|---|---|---|---|
|  T | target | pink | red | yellow-green | yellow | yellow | sky | sky | blue |
| 1 | sign_agree | magenta(0.5) | orange(0.3) | yellow-green(1.0) | sky(0.0) | sky(0.0) | sky(1.0) | sky(1.0) | blue(1.0) |
| 2 | A wretrained V4-CCC | magenta(0.5) | orange(0.3) | yellow-green(1.0) | cyan(0.0) | sky(0.0) | sky(1.0) | sky(1.0) | violet(0.5) |
| 3 | V4-only OLD | red(0.8) | yellow-orange(0.0) | green(0.6) | cyan(0.0) | cyan(0.0) | sky(1.0) | sky(1.0) | violet(0.5) |

## sub-09 protan (target = SUB09_ORIGINAL_HC_EQUIV)

| Rank | Filter | β_s | β_c | norm | **P2a** | exact/8 |
|---|---|---|---|---|---|---|
| 1 | cycle12_cross_roi | 30 | +26 | 39.7° | **0.775** | 5/8 |
| 2 | cycle15_opt4 v4mwj+v4spear | 24 | +32 | 40.0° | **0.775** | 5/8 |
| 3 | cycle14_cross_roi_rdm | 32 | +22 | 38.8° | **0.737** | 4/8 |
| 4 | cycle15_opt3 v4mwj+v1mwj [DEGEN] | 0 | +0 | 0.0° | **0.700** | 2/8 |
| 5 | β=0 baseline (no filter) | 0 | +0 | 0.0° | **0.700** | 2/8 |
| 6 | l_rank/spearman_r [edge +] | 0 | +58 | 58.0° | **0.663** | 3/8 |
| 7 | l_dir/pearson_r [edge +] | 0 | +60 | 60.0° | **0.663** | 3/8 |
| 8 | norm_resid | 24 | +44 | 50.1° | **0.650** | 3/8 |
| 9 | A wretrained 4-term/V4-CCC | 30 | +46 | 54.9° | **0.650** | 3/8 |
| 10 | B wfixed   4-term | 46 | +48 | 66.5° | **0.612** | 2/8 |
| 11 | cycle15_opt2 v4mwj+v1lrank/mw_jaccard | 44 | +54 | 69.7° | **0.550** | 2/8 |
| 12 | B wfixed   V4-CCC | 46 | +50 | 67.9° | **0.550** | 2/8 |
| 13 | Phase A LOCO | 6 | -22 | 22.8° | **0.500** | 3/8 |
| 14 | l_mag | 72 | +38 | 81.4° | **0.275** | 1/8 |
| 15 | l_topk_jaccard [edge -] | 0 | -60 | 60.0° | **0.212** | 1/8 |
| 16 | sign_agree [edge -] | 0 | -60 | 60.0° | **0.212** | 1/8 |

### Per-color detail (sub-09 top 3)

| Rank | Filter | c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 |
|---|---|---|---|---|---|---|---|---|---|
|  T | target | pink | orange | yellow-green | yellow-green | sky | sky | blue | violet |
| 1 | cycle12_cross_roi | pink(1.0) | orange(1.0) | green(0.6) | cyan(0.0) | sky(1.0) | sky(1.0) | sky(0.6) | violet(1.0) |
| 2 | cycle15_opt4 v4mwj+v4spear | pink(1.0) | orange(1.0) | green(0.6) | cyan(0.0) | sky(1.0) | sky(1.0) | sky(0.6) | violet(1.0) |
| 3 | cycle14_cross_roi_rdm | pink(1.0) | yellow-orange(0.7) | green(0.6) | cyan(0.0) | sky(1.0) | sky(1.0) | sky(0.6) | violet(1.0) |

## Notes

- Forward model: `δθ = β_s·cos(θ-90°) + β_c·cos(θ-150°)`. THETA_CONF=150° applied to both deutan and protan (project convention; CIElab nominal).
- β=0 baseline = no filter applied = original color rendering. Its P2a measures how close original HC colors are to subject perception (lower P2a = more distortion subject reports).
- HC_NAME_BINS span 13 fine bins (red, red-orange, orange, ..., magenta, pink). HC_ADJ provides 1-step adjacency partial credit (0.3-0.8).
