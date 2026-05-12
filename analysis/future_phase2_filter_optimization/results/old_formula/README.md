# OLD-Formula Refit Results

All artifacts from OLD CIElab-direct 2-component refit (`δθ = β_s·cos(θ−90°) + β_c·cos(θ−150°)`)
consolidated in this single folder. Naming convention:

```
sub-XX_VV_{VARIANT}_{TYPE}.{ext}
```

## VARIANT codes
| Code | Loss formula |
|---|---|
| `simplified` | 1.0·L_vuln + 0.5·L_rank (original 2-term) |
| `4term`      | 1.0·L_vuln + 0.5·L_rank + 0.2·L_rdm + 0.1·L_smooth (§3 canonical 4-term) |
| `V1demeaned` | demeaned MSE: removes offset penalty |
| `V2pearson`  | adds L_pearson term (0.5·L_pearson) |
| `V3rankw03`  | L_rank weight reduced to 0.3 |
| `V3rankw02`  | L_rank weight reduced to 0.2 |
| `V4ccc`      | CCC-based: 1.0·L_ccc + 0.1·L_smooth |

## TYPE codes
- `landscape.json`: full 1326-cell grid (β_s × β_c)
- `summary.json`: best params + top-N
- `4col_sub-XX_VV_VARIANT.png`: 4-column color visualization (Original / CVD perceives / Pre-image / CVD(filtered))
- `fig_F4_VV_VARIANT.{png,pdf}`: F4-style figure (sub-08 + sub-09 in one image)
- `compare_*.png`: side-by-side comparison
- `ANALYSIS_{VARIANT}.md`: variant analysis

## Optima summary (sub-08 V4)

| VARIANT | argmin (β_s, β_c) | ρ | P2a |
|---|---|---|---|
| simplified  | (10, −32) | 0.833 | 0.250 |
| 4term       | (10, −32) | 0.833 | 0.250 |
| V1demeaned  | (10, −32) | 0.833 | 0.250 |
| V2pearson   | (10, −32) | 0.833 | 0.250 |
| V3rankw03   | (10, −32) | 0.833 | 0.250 |
| V3rankw02   | (10, −32) | 0.833 | 0.250 |
| **V4ccc**   | **(16, +40)** | 0.381 | 0.537 |

## Reference (not loss-variant argmin, separately rendered)
- `ref_4col_sub-08_V4_40p26_p2a.png`: (β_s=40, β_c=+26) — P2a-behavior-best within OLD top 10 (P2a=0.575, 4/8 exact)
- `ref_4col_sub-08_V4_38p7_v4only.png`: V4-only OLD (38, +7) — behaviorally PASS (P1=2+3p/8)
- `ref_4col_sub-08_V1_50p50_edge.png`: sub-08 V1 OLD grid-edge degenerate
- `compare_sub-08_V4_40p26-vs-16p40.png`: P2a-best vs V4 CCC argmin side-by-side

## Cache
- `sub-XX_V4_vulnsim_cache.json`: 1326-cell vuln_sim cache (re-used by loss variants)

## Related documents (in parent dir)
- `../../phase3_loss_variants_comparison.md`: full 4-variant comparison
- `../../phase3_old_rendering_optima.md`: original OLD §3 application
- `../../phase3_justify_v4only.md`: 3-approach justification
