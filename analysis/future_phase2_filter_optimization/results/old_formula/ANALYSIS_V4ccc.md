# Loss Variant V4 — Concordance Correlation Coefficient (CCC)

**Date**: 2026-05-11
**Loss**: `L_fit = 1.0·L_ccc + 0.1·L_smooth`, where `L_ccc = (1−CCC)/2`, and
`L_smooth = mean(circular_adjacent_diff(δθ)²) / 32400`.

CCC integrates Pearson `r` and matched moments:
`CCC = 2·r·σ_sim·σ_obs / (σ_sim² + σ_obs² + (μ_sim − μ_obs)²)`.

## (a) New optima vs original (L_vuln + 0.5·L_rank) optima

| Subject | Original (L_vuln+0.5·L_rank) | V4 CCC best | β_c sign |
|---|---|---|---|
| sub-08 V4 | (β_s=10, β_c=−32), ρ=0.833 | **(β_s=16, β_c=+40)**, ρ=0.381 | **flipped** |
| sub-09 V4 | (β_s=30, β_c=+46), ρ=0.500 | **(β_s=30, β_c=+46)**, ρ=0.500 | identical |

Sub-09 CCC optimum **coincides exactly** with the original optimum (and with
phase3_old_rendering_optima.md §3-Primary). Sub-08 jumps to a positive-β_c
family — the same region that produced top10 P2a-best (40, +26).

## (b) CCC at new optimum vs at original optimum

| Subject | CCC @ original | CCC @ V4-best | Δ |
|---|---|---|---|
| sub-08 | 0.1053 | **0.1897** | +0.084 |
| sub-09 | 0.3037 | 0.3037 | 0 |

Sub-08: CCC nearly doubles when we abandon the rank-friendly minimum. The
original (10, −32) has Pearson r=0.669 and Spearman 0.833 but extremely flat
sim (σ_sim=0.067), so the σ_sim·σ_obs numerator is small and CCC is suppressed.

## (c) sim_std at new optimum vs original — does CCC drive dynamic range up?

| Subject | σ_obs | σ_sim @ original | σ_sim @ V4-best | ratio |
|---|---|---|---|---|
| sub-08 | 0.444 | 0.067 | **0.156** | **2.32×** |
| sub-09 | 0.367 | 0.146 | 0.146 | 1.00× |

**Yes** — for sub-08, CCC actively penalizes the flat prediction and pushes the
optimum into a higher-σ_sim region. σ_sim grows from 15% of σ_obs to 35%.
Sub-09's original was already at the CCC-best simultaneously (no migration
needed), so no further increase happens.

## (d) Is sub-08's "flat-but-high-ρ" paradox eliminated?

**Partially.** The CCC optimum is no longer the flat (10, −32) point; it picks
a much more dynamic prediction (σ_sim=0.156). But CCC at (16, +40) is still
only 0.190, dragged down by:
- residual variance mismatch: σ_sim² + σ_obs² = 0.221 still ≫ 2·σ_sim·σ_obs = 0.138, and
- offset Δμ² = 0.096 contributing ~30% of the denominator.

So CCC eliminates the flat-prediction loophole that L_vuln+0.5·L_rank
rewarded, but it does NOT recover sub-08's high-ρ signal. The L_vuln+L_rank
formulation finds ρ=0.833 because rank correlation is invariant to scale;
CCC's variance-matching constraint deliberately throws that away. The two
losses pick *different families*: rank-best at β_c<0, CCC-best at β_c>0.

## CCC decomposition at V4-best

Sub-08 (16, +40):
- num = 2·r·σ_sim·σ_obs = 2·0.435·0.156·0.444 = 0.0601
- denom = σ_sim² + σ_obs² + Δμ² = 0.0242 + 0.1968 + 0.0957 = 0.3168
- CCC = 0.1897 ; Pearson r=0.435 ; Spearman ρ=0.381

Sub-09 (30, +46):
- num = 2·0.504·0.146·0.367 = 0.0542
- denom = 0.0214 + 0.1347 + 0.0223 = 0.1783
- CCC = 0.3037 ; Pearson r=0.504 ; Spearman ρ=0.500

## Caveat (consistent with §0 framework)

CCC selects a *different* (β_s, β_c) family for sub-08 than the canonical
L_LOCO criterion. Per CLAUDE.md §0/§8, this is **descriptive only** —
behavioral validation remains the ground truth for filter selection. CCC's
interpretation here is methodological: it confirms that the sub-08 (10, −32)
optimum survives only because rank correlation tolerates flat predictions.
