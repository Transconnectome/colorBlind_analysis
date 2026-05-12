# V1 — Demeaned MSE Loss Variant Analysis

**Loss**: `L_fit = 1.0·L_vuln_dm + 0.5·L_rank + 0.1·L_smooth`
where `L_vuln_dm = mean(((sim - sim.mean()) - (obs - obs.mean()))²) / 4.0`

**Cache**: 1326 cells × 2 subjects (`results/old_formula_vulnsim_cache/sub-{08,09}_V4_cache.json`).

## (a) New optima

| Subject | β_s | β_c | L_fit | ρ (Spearman) | r (Pearson) | sim_std | obs_std |
|---|---|---|---|---|---|---|---|
| sub-08 V4 deutan | 10° | −32° | 0.0828 | 0.833 | 0.669 | 0.067 | 0.444 |
| sub-09 V4 protan | 30° | +46° | 0.1545 | 0.500 | 0.504 | 0.146 | 0.367 |

## (b) Comparison to original simplified-loss optimum

Both optima are **IDENTICAL** to the original simplified-loss (`L_vuln + 0.5·L_rank`):
- sub-08: (10, −32) — unchanged
- sub-09: (30, +46) — unchanged

For sub-08, the offset penalty was huge (offset² = 0.1768 → 52.3% of original L_vuln MSE), yet removing it does not reroute the optimum. The original optimum already had a small offset attainable within the L_rank-favored family.

## (c) vuln_sim dynamic range at new optimum

The dynamic-range mismatch is intrinsic to the model class, not the loss:

- **sub-08**: best-cell sim_std = 0.067 vs obs_std = 0.444 (15% of observed range). Across the full 1326-cell grid, the **max** sim_std reachable anywhere is only **0.247** (at β_s=48, β_c=+34, where ρ collapses to 0.19). No cell in the grid has sim_std > 0.3 — HC-mean LOCO ρ cannot reach the negative voxel-corr values that drive the observed range.
- **sub-09**: best-cell sim_std = 0.146 vs obs_std = 0.367 (40%). Same grid-wide max sim_std = 0.247.

Demeaning does not change which cell wins → no dynamic-range improvement at new optimum.

## (d) Sub-08 paradox: mitigated?

**No.** The paradox — high Spearman ρ paired with collapsed simulation amplitude — is preserved verbatim. Removing the offset makes L_vuln smaller in absolute value (0.0846 → 0.0404, −52%), but its **gradient** across (β_s, β_c) still favors the same cell that L_rank favors (ρ=0.833). L_vuln_dm reaches its minimum within the same low-amplitude shape family.

**Why**: Demeaning removes a constant shift but adds no scale-matching term. Higher-sim_std cells (e.g. β_s=48, β_c=+34, sim_std=0.247) destroy the rank ordering (ρ drops to 0.19), so L_rank punishes them harder than L_vuln_dm rewards them. Net: same optimum.

## L_fit composition at new optimum

| | L_vuln_dm contrib | L_rank contrib | L_smooth contrib | Total L_fit |
|---|---|---|---|---|
| sub-08 (10, −32) | 0.0404 (49%) | 0.0417 (50%) | 0.0007 (1%) | 0.0828 |
| sub-09 (30, +46) | 0.0255 (16%) | 0.1250 (81%) | 0.0040 (3%) | 0.1545 |

L_rank dominates sub-09; L_vuln_dm and L_rank balance for sub-08.

## Conclusion

Removing offset from L_vuln (V1 variant) does **not** alter the optimum for either subject. The "52% offset penalty" observed in the original loss for sub-08 is not the binding constraint — L_rank is. To escape the low-amplitude family, the loss would need a scale-matching term (e.g. amplitude ratio, std-normalized MSE) or a different model class that can produce sim_std comparable to obs_std (0.4+). Demeaning alone is insufficient.
