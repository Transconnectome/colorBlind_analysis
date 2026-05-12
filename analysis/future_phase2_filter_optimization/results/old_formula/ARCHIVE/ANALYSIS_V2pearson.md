# V2 Pearson-added Loss Variant — Analysis

**Loss**: `L_fit = 1.0·L_vuln + 0.5·L_rank + 0.5·L_pearson + 0.1·L_smooth`

## (a) New optima

| Subject | β_s | β_c | L_fit | Spearman ρ | Pearson r | σ_sim | σ_obs |
|---|---|---|---|---|---|---|---|
| sub-08 V4 deutan | 10° | −32° | 0.2097 | 0.833 | 0.669 | 0.067 | 0.444 |
| sub-09 V4 protan | 30° | +46° | 0.2840 | 0.500 | 0.504 | 0.146 | 0.367 |

## (b) Comparison with original simplified-loss optima
**IDENTICAL.** sub-08 (10, −32) and sub-09 (30, +46) — unchanged from `L_vuln + 0.5·L_rank`. Adding L_pearson with weight 0.5 does not relocate either optimum.

## (c) Dynamic range at new optima
**No change.** sub-08 σ_sim=0.067 (15.1% of σ_obs); sub-09 σ_sim=0.146 (39.9% of σ_obs). Same cells, so dynamic-range mismatch preserved.

**Why**: Adding a Pearson penalty is **redundant** with Spearman here — both r and ρ are scale-invariant, so neither punishes flat-sim. Contrast with V4 (CCC) which relocates sub-08 to σ_sim=0.156 because CCC explicitly contains σ_sim·σ_obs in the numerator and (μ_sim−μ_obs)² in the denominator.

## (d) Sub-09 V4 Spearman above 0.5?
**No.** ρ = 0.500 exactly. The (30, +46) plateau is rank-tied at 0.5; Pearson r merely picks among tied cells (r=0.504) but cannot break ρ above 0.5 on this 2°-resolution grid.

## L_fit breakdown
- sub-08 (10, −32): L_vuln=0.0846 (40%), 0.5·L_rank=0.0417 (20%), 0.5·L_pearson=0.0827 (39%), 0.1·L_smooth=0.0007 (<1%) → 0.2097.
- sub-09 (30, +46): L_vuln=0.0310 (11%), 0.5·L_rank=0.1250 (44%), 0.5·L_pearson=0.1240 (44%), 0.1·L_smooth=0.0040 (1%) → 0.2840.

## Conclusion
**Null result.** Pearson-added is NOT a remedy for the flat-σ_sim paradox at sub-08 (10, −32) — both Pearson and Spearman are scale-invariant and reward the same low-amplitude cell. To escape this loophole, a variance/amplitude-matching term is required. V4 (CCC) is the only variant in this batch that achieves this.

## Files
- `sub-{08,09}_V4_{summary,landscape}.json` — full grids + per-cell decomposition
- `fig_V2_pearson_added.{png,pdf}` — F4-style figure
- Script: `scripts/phase3_loss_variant_V2_pearson.py`
