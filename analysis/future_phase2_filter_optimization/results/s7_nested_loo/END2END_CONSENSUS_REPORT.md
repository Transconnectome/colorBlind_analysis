# S7 End-to-End Nested-LOO Consensus Report

**Question (PI feedback)**: when (model, λ) selection is performed *inside* each outer LOO fold using `argmin inner_CoV s.t. boundary_rate ≤ 0.5`, how often does the **same** (model, λ) win across the 7 outer folds?  This quantifies model+weight *joint* selection stability under leave-one-HC-out.

**Search space per fold**: 4 effective models × 5 λ = 20 candidates per subject (`rc_Boehm_mid` for sub-08/sub-10; `rc_Boehm_low` for sub-09 — mutually exclusive Boehm flavors).  
Chance-level consensus ≈ 1/20 (uniform).  Ties at numerically-equivalent CoV are resolved deterministically and reported in the per-fold detail tables.

**Tiebreaker (deterministic)**: (cov, lowest λ, fixed model order ['rc_DPS_lit', 'rc_Boehm_mid', 'rc_Boehm_low', 'rc_JND_Lamb', '2comp']).

**Boundary filter**: a fold is *degenerate* iff no (model, λ) has `boundary_rate ≤ 0.5`.  Degenerate folds are excluded from the consensus denominator.

**Tiers**: robust ≥ 0.85, moderate ∈ [0.60, 0.85), fragile < 0.60 or n_valid < 4, degenerate-all if n_valid = 0.


## Summary table

| Cell | Mode (model, λ) | rate / n_valid | n_degen | n_variations | Tier |
|---|---|---|---|---|---|
| sub-08_V1 | rc_Boehm_mid, λ=0.25 | 7/7 (1.00) | 0 | 1 | **robust** |
| sub-08_V2 | rc_DPS_lit, λ=0.75 | 7/7 (1.00) | 0 | 1 | **robust** |
| sub-08_V3 | rc_Boehm_mid, λ=0.25 | 3/7 (0.43) | 0 | 5 | **fragile** |
| sub-08_V4 | 2comp, λ=0.00 | 4/7 (0.57) | 0 | 4 | **fragile** |
| sub-09_V1 | rc_DPS_lit, λ=0.00 | 4/7 (0.57) | 0 | 4 | **fragile** |
| sub-09_V2 | rc_Boehm_low, λ=0.75 | 3/7 (0.43) | 0 | 5 | **fragile** |
| sub-09_V3 | rc_DPS_lit, λ=0.00 | 3/7 (0.43) | 0 | 4 | **fragile** |
| sub-09_V4 | rc_Boehm_low, λ=0.75 | 3/7 (0.43) | 0 | 4 | **fragile** |
| sub-10_V1 | rc_Boehm_mid, λ=1.00 | 3/7 (0.43) | 0 | 3 | **fragile** |
| sub-10_V2 | rc_DPS_lit, λ=1.00 | 2/7 (0.29) | 0 | 4 | **fragile** |
| sub-10_V3 | rc_DPS_lit, λ=1.00 | 5/7 (0.71) | 0 | 2 | **moderate** |
| sub-10_V4 | rc_Boehm_mid, λ=1.00 | 5/7 (0.71) | 0 | 2 | **moderate** |

## Per-cell detail


### sub-08_V1

**Mode**: (rc_Boehm_mid, λ=0.25) — 7/7 = 1.000.  Tier: **robust**.  Degenerate folds: 0/7.


*Tie-load*: 7/7 folds had ≥2 candidates tied at the winning CoV (max 9 ties); deterministic tiebreaker selects the mode in those folds.

| Fold | HC held out | Best (model, λ) | CoV | Boundary | Ties |
|---|---|---|---|---|---|
| 0 | sub-01 | rc_Boehm_mid, λ=0.25 | 3.63e-16 | 0.00 | 9 ties |
| 1 | sub-02 | rc_Boehm_mid, λ=0.25 | 0.0204 | 0.00 | 4 ties |
| 2 | sub-03 | rc_Boehm_mid, λ=0.25 | 3.63e-16 | 0.00 | 9 ties |
| 3 | sub-04 | rc_Boehm_mid, λ=0.25 | 0.0278 | 0.00 | 3 ties |
| 4 | sub-05 | rc_Boehm_mid, λ=0.25 | 3.63e-16 | 0.00 | 7 ties |
| 5 | sub-06 | rc_Boehm_mid, λ=0.25 | 0.0278 | 0.00 | 7 ties |
| 6 | sub-07 | rc_Boehm_mid, λ=0.25 | 0.0204 | 0.00 | 4 ties |

### sub-08_V2

**Mode**: (rc_DPS_lit, λ=0.75) — 7/7 = 1.000.  Tier: **robust**.  Degenerate folds: 0/7.


*Tie-load*: 7/7 folds had ≥2 candidates tied at the winning CoV (max 4 ties); deterministic tiebreaker selects the mode in those folds.

| Fold | HC held out | Best (model, λ) | CoV | Boundary | Ties |
|---|---|---|---|---|---|
| 0 | sub-01 | rc_DPS_lit, λ=0.75 | 0 | 0.00 | 2 ties |
| 1 | sub-02 | rc_DPS_lit, λ=0.75 | 0 | 0.00 | 2 ties |
| 2 | sub-03 | rc_DPS_lit, λ=0.75 | 0 | 0.00 | 4 ties |
| 3 | sub-04 | rc_DPS_lit, λ=0.75 | 0 | 0.00 | 4 ties |
| 4 | sub-05 | rc_DPS_lit, λ=0.75 | 0 | 0.00 | 2 ties |
| 5 | sub-06 | rc_DPS_lit, λ=0.75 | 0 | 0.00 | 2 ties |
| 6 | sub-07 | rc_DPS_lit, λ=0.75 | 0 | 0.00 | 2 ties |

### sub-08_V3

**Mode**: (rc_Boehm_mid, λ=0.25) — 3/7 = 0.429.  Tier: **fragile**.  Degenerate folds: 0/7.


*Tie-load*: 4/7 folds had ≥2 candidates tied at the winning CoV (max 7 ties); deterministic tiebreaker selects the mode in those folds.

**Variations** (5): rc_Boehm_mid+λ0.25=3; rc_Boehm_mid+λ0.00=1; rc_DPS_lit+λ0.00=1; rc_JND_Lamb+λ0.50=1; rc_DPS_lit+λ0.50=1


| Fold | HC held out | Best (model, λ) | CoV | Boundary | Ties |
|---|---|---|---|---|---|
| 0 | sub-01 | rc_Boehm_mid, λ=0.00 | 0.0614 | 0.40 | — |
| 1 | sub-02 | rc_Boehm_mid, λ=0.25 | 3.63e-16 | 0.00 | 6 ties |
| 2 | sub-03 | rc_DPS_lit, λ=0.00 | 0.118 | 0.47 | — |
| 3 | sub-04 | rc_JND_Lamb, λ=0.50 | 0.149 | 0.00 | — |
| 4 | sub-05 | rc_DPS_lit, λ=0.50 | 3.63e-16 | 0.00 | 2 ties |
| 5 | sub-06 | rc_Boehm_mid, λ=0.25 | 3.63e-16 | 0.00 | 7 ties |
| 6 | sub-07 | rc_Boehm_mid, λ=0.25 | 3.63e-16 | 0.00 | 7 ties |

### sub-08_V4

**Mode**: (2comp, λ=0.00) — 4/7 = 0.571.  Tier: **fragile**.  Degenerate folds: 0/7.


**Variations** (4): 2comp+λ0.00=4; rc_DPS_lit+λ0.75=1; rc_Boehm_mid+λ0.50=1; rc_Boehm_mid+λ0.00=1


| Fold | HC held out | Best (model, λ) | CoV | Boundary | Ties |
|---|---|---|---|---|---|
| 0 | sub-01 | 2comp, λ=0.00 | 0.041 | 0.00 | — |
| 1 | sub-02 | 2comp, λ=0.00 | 0.135 | 0.00 | — |
| 2 | sub-03 | rc_DPS_lit, λ=0.75 | 0 | 0.00 | — |
| 3 | sub-04 | 2comp, λ=0.00 | 0.0267 | 0.00 | — |
| 4 | sub-05 | 2comp, λ=0.00 | 0.0531 | 0.00 | — |
| 5 | sub-06 | rc_Boehm_mid, λ=0.50 | 0.11 | 0.00 | — |
| 6 | sub-07 | rc_Boehm_mid, λ=0.00 | 0.122 | 0.40 | — |

### sub-09_V1

**Mode**: (rc_DPS_lit, λ=0.00) — 4/7 = 0.571.  Tier: **fragile**.  Degenerate folds: 0/7.


**Variations** (4): rc_DPS_lit+λ0.00=4; rc_JND_Lamb+λ0.50=1; rc_JND_Lamb+λ0.75=1; rc_Boehm_low+λ0.75=1


| Fold | HC held out | Best (model, λ) | CoV | Boundary | Ties |
|---|---|---|---|---|---|
| 0 | sub-01 | rc_DPS_lit, λ=0.00 | 0.0786 | 0.00 | — |
| 1 | sub-02 | rc_JND_Lamb, λ=0.50 | 0.124 | 0.00 | — |
| 2 | sub-03 | rc_JND_Lamb, λ=0.75 | 0.0642 | 0.00 | — |
| 3 | sub-04 | rc_Boehm_low, λ=0.75 | 0.0739 | 0.00 | — |
| 4 | sub-05 | rc_DPS_lit, λ=0.00 | 0.0792 | 0.00 | — |
| 5 | sub-06 | rc_DPS_lit, λ=0.00 | 0.104 | 0.00 | — |
| 6 | sub-07 | rc_DPS_lit, λ=0.00 | 0.0983 | 0.00 | — |

### sub-09_V2

**Mode**: (rc_Boehm_low, λ=0.75) — 3/7 = 0.429.  Tier: **fragile**.  Degenerate folds: 0/7.


*Tie-load*: 1/7 folds had ≥2 candidates tied at the winning CoV (max 4 ties); deterministic tiebreaker selects the mode in those folds.

**Variations** (5): rc_Boehm_low+λ0.75=3; rc_JND_Lamb+λ1.00=1; rc_Boehm_low+λ0.50=1; rc_DPS_lit+λ0.25=1; rc_Boehm_low+λ1.00=1


| Fold | HC held out | Best (model, λ) | CoV | Boundary | Ties |
|---|---|---|---|---|---|
| 0 | sub-01 | rc_JND_Lamb, λ=1.00 | 0.0707 | 0.00 | — |
| 1 | sub-02 | rc_Boehm_low, λ=0.50 | 0.0172 | 0.00 | — |
| 2 | sub-03 | rc_DPS_lit, λ=0.25 | 0.037 | 0.00 | 4 ties |
| 3 | sub-04 | rc_Boehm_low, λ=0.75 | 0.0639 | 0.00 | — |
| 4 | sub-05 | rc_Boehm_low, λ=1.00 | 0.0193 | 0.00 | — |
| 5 | sub-06 | rc_Boehm_low, λ=0.75 | 0.0277 | 0.00 | — |
| 6 | sub-07 | rc_Boehm_low, λ=0.75 | 0.0252 | 0.00 | — |

### sub-09_V3

**Mode**: (rc_DPS_lit, λ=0.00) — 3/7 = 0.429.  Tier: **fragile**.  Degenerate folds: 0/7.


*Tie-load*: 1/7 folds had ≥2 candidates tied at the winning CoV (max 2 ties); deterministic tiebreaker selects the mode in those folds.

**Variations** (4): rc_DPS_lit+λ0.00=3; rc_DPS_lit+λ0.75=2; rc_JND_Lamb+λ0.75=1; rc_DPS_lit+λ0.25=1


| Fold | HC held out | Best (model, λ) | CoV | Boundary | Ties |
|---|---|---|---|---|---|
| 0 | sub-01 | rc_DPS_lit, λ=0.00 | 0.0786 | 0.00 | — |
| 1 | sub-02 | rc_JND_Lamb, λ=0.75 | 0.00963 | 0.00 | — |
| 2 | sub-03 | rc_DPS_lit, λ=0.25 | 0.0452 | 0.00 | — |
| 3 | sub-04 | rc_DPS_lit, λ=0.75 | 0.0369 | 0.00 | — |
| 4 | sub-05 | rc_DPS_lit, λ=0.75 | 0.0503 | 0.00 | 2 ties |
| 5 | sub-06 | rc_DPS_lit, λ=0.00 | 0.104 | 0.00 | — |
| 6 | sub-07 | rc_DPS_lit, λ=0.00 | 0.0983 | 0.00 | — |

### sub-09_V4

**Mode**: (rc_Boehm_low, λ=0.75) — 3/7 = 0.429.  Tier: **fragile**.  Degenerate folds: 0/7.


*Tie-load*: 4/7 folds had ≥2 candidates tied at the winning CoV (max 4 ties); deterministic tiebreaker selects the mode in those folds.

**Variations** (4): rc_Boehm_low+λ0.75=3; rc_DPS_lit+λ0.25=2; rc_JND_Lamb+λ0.75=1; rc_Boehm_low+λ1.00=1


| Fold | HC held out | Best (model, λ) | CoV | Boundary | Ties |
|---|---|---|---|---|---|
| 0 | sub-01 | rc_Boehm_low, λ=0.75 | 0 | 0.00 | 2 ties |
| 1 | sub-02 | rc_Boehm_low, λ=0.75 | 0.0307 | 0.00 | — |
| 2 | sub-03 | rc_JND_Lamb, λ=0.75 | 0.0365 | 0.00 | 2 ties |
| 3 | sub-04 | rc_DPS_lit, λ=0.25 | 0 | 0.00 | 4 ties |
| 4 | sub-05 | rc_DPS_lit, λ=0.25 | 0 | 0.00 | 4 ties |
| 5 | sub-06 | rc_Boehm_low, λ=1.00 | 0.0805 | 0.00 | — |
| 6 | sub-07 | rc_Boehm_low, λ=0.75 | 0.056 | 0.00 | — |

### sub-10_V1

**Mode**: (rc_Boehm_mid, λ=1.00) — 3/7 = 0.429.  Tier: **fragile**.  Degenerate folds: 0/7.


**Variations** (3): rc_Boehm_mid+λ1.00=3; rc_DPS_lit+λ1.00=3; rc_JND_Lamb+λ1.00=1


| Fold | HC held out | Best (model, λ) | CoV | Boundary | Ties |
|---|---|---|---|---|---|
| 0 | sub-01 | rc_Boehm_mid, λ=1.00 | 1.59 | 0.40 | — |
| 1 | sub-02 | rc_JND_Lamb, λ=1.00 | 0.682 | 0.47 | — |
| 2 | sub-03 | rc_DPS_lit, λ=1.00 | 0.441 | 0.00 | — |
| 3 | sub-04 | rc_DPS_lit, λ=1.00 | 0.353 | 0.40 | — |
| 4 | sub-05 | rc_Boehm_mid, λ=1.00 | 1.53 | 0.27 | — |
| 5 | sub-06 | rc_Boehm_mid, λ=1.00 | 3.98 | 0.47 | — |
| 6 | sub-07 | rc_DPS_lit, λ=1.00 | 0.616 | 0.00 | — |

### sub-10_V2

**Mode**: (rc_DPS_lit, λ=1.00) — 2/7 = 0.286.  Tier: **fragile**.  Degenerate folds: 0/7.


**Variations** (4): rc_DPS_lit+λ1.00=2; rc_JND_Lamb+λ1.00=2; rc_Boehm_mid+λ1.00=2; 2comp+λ1.00=1


| Fold | HC held out | Best (model, λ) | CoV | Boundary | Ties |
|---|---|---|---|---|---|
| 0 | sub-01 | rc_DPS_lit, λ=1.00 | 0.143 | 0.00 | — |
| 1 | sub-02 | 2comp, λ=1.00 | 0.092 | 0.47 | — |
| 2 | sub-03 | rc_JND_Lamb, λ=1.00 | 0.0249 | 0.00 | — |
| 3 | sub-04 | rc_Boehm_mid, λ=1.00 | 0.106 | 0.00 | — |
| 4 | sub-05 | rc_JND_Lamb, λ=1.00 | 0.135 | 0.20 | — |
| 5 | sub-06 | rc_DPS_lit, λ=1.00 | 0.203 | 0.00 | — |
| 6 | sub-07 | rc_Boehm_mid, λ=1.00 | 0.117 | 0.00 | — |

### sub-10_V3

**Mode**: (rc_DPS_lit, λ=1.00) — 5/7 = 0.714.  Tier: **moderate**.  Degenerate folds: 0/7.


**Variations** (2): rc_DPS_lit+λ1.00=5; rc_Boehm_mid+λ1.00=2


| Fold | HC held out | Best (model, λ) | CoV | Boundary | Ties |
|---|---|---|---|---|---|
| 0 | sub-01 | rc_DPS_lit, λ=1.00 | 0.27 | 0.07 | — |
| 1 | sub-02 | rc_Boehm_mid, λ=1.00 | 0.112 | 0.33 | — |
| 2 | sub-03 | rc_Boehm_mid, λ=1.00 | 0.0724 | 0.47 | — |
| 3 | sub-04 | rc_DPS_lit, λ=1.00 | 0.358 | 0.13 | — |
| 4 | sub-05 | rc_DPS_lit, λ=1.00 | 0.452 | 0.27 | — |
| 5 | sub-06 | rc_DPS_lit, λ=1.00 | 0.348 | 0.13 | — |
| 6 | sub-07 | rc_DPS_lit, λ=1.00 | 0.557 | 0.20 | — |

### sub-10_V4

**Mode**: (rc_Boehm_mid, λ=1.00) — 5/7 = 0.714.  Tier: **moderate**.  Degenerate folds: 0/7.


**Variations** (2): rc_Boehm_mid+λ1.00=5; rc_JND_Lamb+λ1.00=2


| Fold | HC held out | Best (model, λ) | CoV | Boundary | Ties |
|---|---|---|---|---|---|
| 0 | sub-01 | rc_JND_Lamb, λ=1.00 | 0.0644 | 0.00 | — |
| 1 | sub-02 | rc_Boehm_mid, λ=1.00 | 0.111 | 0.00 | — |
| 2 | sub-03 | rc_JND_Lamb, λ=1.00 | 0.277 | 0.00 | — |
| 3 | sub-04 | rc_Boehm_mid, λ=1.00 | 0.743 | 0.40 | — |
| 4 | sub-05 | rc_Boehm_mid, λ=1.00 | 0.614 | 0.40 | — |
| 5 | sub-06 | rc_Boehm_mid, λ=1.00 | 0.065 | 0.00 | — |
| 6 | sub-07 | rc_Boehm_mid, λ=1.00 | 0.487 | 0.20 | — |

## Overall verdict


**Bottom line for PI**: Joint model+λ selection under end-to-end nested LOO is **fragile in 8/12 cells**; only 2/12 nominally pass the robust threshold (≥85% agreement), and in those the consensus is **tiebreaker-driven** (3–9 candidates tied at numerically-equal CoV, with the deterministic tiebreaker picking the winner — not a unique data signal).  No cell is fully degenerate.  The PI question — *does the same (model, λ) survive joint selection across LOO folds?* — is answered **negatively for the majority** of subject×ROI cells.

**Tier distribution across 12 cells**: fragile=8, robust=2, moderate=2

- **Nominally robust (2/12)**: sub-08_V1, sub-08_V2
- **Moderate (2/12)**: sub-10_V3, sub-10_V4
- **Fragile (8/12)**: sub-08_V3, sub-08_V4, sub-09_V1, sub-09_V2, sub-09_V3, sub-09_V4, sub-10_V1, sub-10_V2

*Tiebreaker caveat*: among nominally robust cells, the following had folds where the winning candidate shared the lowest CoV with ≥1 other candidate: **sub-08_V1 (7 fold(s), max 9 ties), sub-08_V2 (7 fold(s), max 4 ties)**.  The deterministic tiebreaker selects the mode in those folds; a different tiebreaker (e.g., highest λ first, or a different model-order priority) could yield a different mode.

### Reconciliation with prior hypotheses

| Hypothesis (user) | Result | Verdict |
|---|---|---|
| Sub-09 2-comp: high consensus (robust) | 2-comp is mode in 0/4 sub-09 cells; all 4 are fragile | **Falsified** |
| Sub-09 R+C: moderate ~ fragile (g drift) | All 4 sub-09 cells fragile (R+C variants dominate but unstable) | Confirmed |
| Sub-08: mostly R+C, λ varies | 3/4 sub-08 cells mode is R+C variant; λ ∈ {0.00, 0.25, 0.75} | Confirmed |
| Sub-10: degenerate / λ=1.0 fallback only | 0/4 degenerate folds across sub-10; λ=1.0 confirmed for all 4 modes | **Half falsified** (λ=1.0 yes; no degeneracy) |


## Sanity check vs `aggregated.json` (cross-fold argmin)

Cross-fold argmin: from `optimal_per_model`, pick the model with lowest fold-averaged inner CoV (boundary ≤ 0.5).  If per-fold consensus is *real*, mode (model, λ) should match this cross-fold optimum.  Mismatches expose fragility that the existing aggregate hides by averaging CoV before argmin.


| Cell | Per-fold mode | Aggregate argmin | Match? |
|---|---|---|---|
| sub-08_V1 | rc_Boehm_mid, λ=0.25 | rc_Boehm_mid, λ=0.25 (CoV=0.0138) | yes |
| sub-08_V2 | rc_DPS_lit, λ=0.75 | rc_DPS_lit, λ=0.75 (CoV=0) | yes |
| sub-08_V3 | rc_Boehm_mid, λ=0.25 | rc_JND_Lamb, λ=0.50 (CoV=0.0641) | no |
| sub-08_V4 | 2comp, λ=0.00 | 2comp, λ=0.00 (CoV=0.104) | yes |
| sub-09_V1 | rc_DPS_lit, λ=0.00 | rc_DPS_lit, λ=0.00 (CoV=0.0997) | yes |
| sub-09_V2 | rc_Boehm_low, λ=0.75 | rc_Boehm_low, λ=0.75 (CoV=0.0452) | yes |
| sub-09_V3 | rc_DPS_lit, λ=0.00 | rc_DPS_lit, λ=0.00 (CoV=0.0997) | yes |
| sub-09_V4 | rc_Boehm_low, λ=0.75 | rc_Boehm_low, λ=0.75 (CoV=0.0451) | yes |
| sub-10_V1 | rc_Boehm_mid, λ=1.00 | rc_JND_Lamb, λ=1.00 (CoV=2.6) | no |
| sub-10_V2 | rc_DPS_lit, λ=1.00 | rc_DPS_lit, λ=1.00 (CoV=0.146) | yes |
| sub-10_V3 | rc_DPS_lit, λ=1.00 | rc_DPS_lit, λ=1.00 (CoV=0.316) | yes |
| sub-10_V4 | rc_Boehm_mid, λ=1.00 | rc_Boehm_mid, λ=1.00 (CoV=0.388) | yes |

**Agreement**: 10/12 cells.  Disagreements occur where per-fold winners vary enough that averaging CoV before argmin changes the result — a fragility signal.
