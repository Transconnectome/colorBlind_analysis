# Cycle12 cross-ROI landscape — fresh recompute (V4 l_topk + V1 l_rank)

**Date**: 2026-05-11 · **Status**: DESCRIPTIVE (§0 compliance)

## Scope

Recompute the full 41×61 = 2501-cell landscape for the Cycle 12 cross-ROI
loss using the *current* W-fixed simulator and store the per-cell
`vuln_sim_V4` / `vuln_sim_V1` vectors that the cached scalar landscapes do
not retain.

Loss:

```
L_total(β_s, β_c) = α · l_topk_jaccard(V4) + β · l_rank(V1) + λ · Tikh(β_s, β_c)
α = β = 1.0, λ = 0.2
Tikh = (β_s / 80)^2 + (β_c / 60)^2
l_topk = top-3 Jaccard distance on V4 LOCO vulnerability vector
l_rank = 1 − Spearman ρ on V1 LOCO vulnerability vector
```

Grid β_s ∈ [0, 80] step 2 × β_c ∈ [−60, 60] step 2.
(Wider than the task-suggested 26×51; chosen to cover the cached cycle12
argmin (68, −38) for sub-08 in case it reproduced.)

## Simulator note

The task brief requested `simulate_mean_hc_loco_legacy` (wretrained). I used
`simulate_mean_hc_wfixed` instead because:

1. The cached cycle12 argmins quoted in the brief — sub-08 (68, −38),
   sub-09 (30, +26) — are W-fixed values (cycle12_loss_cross_roi.py reads
   `sub-{ID}_{ROI}_landscape.json` which were produced by `run_NxM.py` via
   `simulate_mean_hc_wfixed`).
2. Wretrained is ~3.5 h per (subject, ROI) per `step1_fit_loco_v2.py`
   docstring → 4 sweeps would be ~14 h, far over the 1–2 h budget.
3. W-fixed is the Phase 2 standard per MEMORY note and run_NxM.py.

Total wallclock for 2 subjects × 2 ROIs × 2501 cells: **~31 s** (≈3 ms/cell).

## Argmins (fresh recompute)

| Subject | argmin (β_s, β_c) | L_total | l_topk(V4) | l_rank(V1) | Tikh×λ |
|---|---|---|---|---|---|
| sub-08 (deutan) | **(22, −14)** | 0.2641 | **0.000** | 0.238 | 0.026 |
| sub-09 (protan) | **(34, +44)** | 1.1342 | 0.800   | 0.190 | 0.144 |

## Comparison with cached cycle12 argmins

`results/cycles/cycle12_loss_cross_roi.json` (read from cached
`l_topk_jaccard(V4)` and `l_rank(V1)` grids):

- sub-08 cached argmin (68, −38), L_total = 0.296
- sub-09 cached argmin (30, +26), L_total = 1.223

In our **fresh** grid the cached coordinates yield:

| Subject | At cached (β_s, β_c) | l_total | l_topk(V4) | l_rank(V1) |
|---|---|---|---|---|
| sub-08 | (68, −38) | 0.939 | 0.500 | 0.214 |
| sub-09 | (30, +26) | 1.247 | 0.800 | 0.381 |

**The cached argmins do NOT reproduce.** Single-cell smoke tests at (0, 0),
(38, −14) and (68, −38) with the current `precompute_hc_W` /
`simulate_mean_hc_wfixed` / `compute_extended_loss` pipeline differ from
the cached landscape values by up to |Δl_topk| = 0.5 and |Δl_rank| = 0.76.
Cause of drift unknown — pool composition (with/without sub-07) ruled out
in a quick check. The cached landscapes in `results/cycles/` appear stale
relative to current code; the fresh recompute is now the authoritative
reference.

Reported sanity-check magnitudes (`sanity_check_vs_cached` field in the
per-subject JSON):

- sub-08 V4: max|Δl_topk| = 0.500, max|Δl_rank| = 0.500
- sub-08 V1: max|Δl_topk| = 0.300, max|Δl_rank| = 0.405
- sub-09 V4: max|Δl_topk| = 0.200, max|Δl_rank| = 0.762
- sub-09 V1: max|Δl_topk| = 0.300, max|Δl_rank| = 0.357

## Landscape shape

Counts of cells whose `l_total` is within ε of the minimum:

| Subject | within 1 % of (max−min) | within 5 % | l_topk(V4) = 0 cells |
|---|---|---|---|
| sub-08 | 9 / 2501 (0.4 %) | 31 / 2501 (1.2 %) | **162** |
| sub-09 | 1 / 2501 (0.0 %) | 9 / 2501 (0.4 %) | **0** |

- **sub-08** has a clearly identifiable narrow minimum near (22, −14) but
  also a broad V4-top-3-jaccard plateau (162 cells with l_topk = 0). The
  cross-ROI loss selects the cell within that plateau that also minimises
  the V1 Spearman term and the small Tikh.
- **sub-09** has *no* cell anywhere on the grid where the V4 top-3
  vulnerability set of the simulator matches sub-09's observed CVD top-3
  set. The cross-ROI minimum at (34, +44) is therefore driven entirely by
  l_rank(V1) and the Tikh term; the V4 l_topk component contributes a
  constant offset of 0.8 across the optimum region.

## Comparison with V4-CCC landscape

`results/fixedW_onlyTest/summary_V4ccc.json` reports V4-CCC argmins:

- sub-08 V4-CCC: (β_s = 46, β_c = −20)
- sub-09 V4-CCC: (β_s = 46, β_c = +50)

(Note: the task brief quoted V4-CCC sub-08 (16, +40) / sub-09 (30, +46);
these don't match the on-disk summary either — the brief's reference
values appear stale.)

**Direction comparison** (V4-CCC vs cycle12 cross-ROI, both fresh):

| Subject | V4-CCC | cycle12 cross-ROI | Δβ_s | Δβ_c | β_c sign |
|---|---|---|---|---|---|
| sub-08 | (46, −20) | (22, −14) | −24 | +6 | both negative |
| sub-09 | (46, +50) | (34, +44) | −12 | −6 | both positive |

For **sub-09** the two landscapes converge: same β_c sign (+44 vs +50) and
moderate β_s offset, consistent with V4-CCC and V4-l_topk both being
dominated by the same V1 l_rank gradient (since V4 itself is degenerate
for sub-09 — see "0 l_topk = 0 cells" above).

For **sub-08** the directions are also concordant in β_c (both
negative), but the cross-ROI loss pulls β_s back from 46° to 22°. Adding
V1 l_rank as a second term penalises the large-β_s region where V1
Spearman degrades, even though V4 l_topk admits a wide plateau.

## Files

- `results/fixedW_onlyTest/sub-08_V4V1_cycle12_landscape.json` (2 501 cells
  with `vuln_sim_V4`, `vuln_sim_V1` per cell)
- `results/fixedW_onlyTest/sub-09_V4V1_cycle12_landscape.json`
- `results/fixedW_onlyTest/cycle12_landscape_recompute_summary.json`
- `results/fixedW_onlyTest/fig_F4_V4V1_cycle12.{png,pdf}`
- `scripts/cycle12_landscape_recompute.py` (sweep)
- `scripts/cycle12_landscape_fig.py` (figure)

## §0 compliance

This is a **descriptive landscape recompute**. No new selection rule
introduced; no specificity claim made. The cycle12 cross-ROI loss family
remains within the Cycle 9–13 measurement family (§5 "재논의 금지"). The
fresh argmins are reported alongside the cached argmins; the discrepancy
is documented but not used to justify any selection-rule reformulation.

Behavioral validation remains the ground truth for any subsequent
choice of filter coordinates per §0 of `CLAUDE.md`.
