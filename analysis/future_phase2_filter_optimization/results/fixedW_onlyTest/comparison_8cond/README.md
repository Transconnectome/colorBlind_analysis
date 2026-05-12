# 8-Condition Comparison Grid — sub-08 / sub-09 V4

Generated: comparison_8cond_taskCD.py

Compares argmins across **{Machado, 2-component} × {wretrained, wfixed} × {canonical L_fit, CCC loss}** for sub-08 (deutan) and sub-09 (protan) at V4. 16 (subject × condition) cells total.

## Methodology (descriptive only — §0 compliant)

- **Simulators**:
  - `wretrained` (shift_at_both): W retrained at every parameter via LOCO on shifted C; held-out test also uses shifted C.
  - `wfixed` (shift_at_test_only, A1): W_k trained ONCE per (HC × held-out color) on UNSHIFTED C_baseline; only test design is shifted.
- **Losses**:
  - `canonical`: 4-term `1·L_vuln + 0.5·L_rank + 0.2·L_rdm + 0.1·L_smooth` (NORM `{vuln:4, rank:2, rdm:2, smooth:32400}`).
  - `ccc`: `1·(1−CCC)/2 + 0.2·L_rdm + 0.1·L_smooth`, where CCC is Lin's Concordance Correlation Coefficient with ddof=0 std (matches `fixedW_onlyTest_v4ccc.py`).
- **Grids**:
  - 2-component: β_s∈[0,50] step 2, β_c∈[−50,50] step 2 (1326 cells).
  - Machado 1way: Δλ∈[0,20] step 0.5 nm (41 cells). Sign of cone-shift is encoded by family (deutan/protan), not by Δλ.
- **HC pool**: sub-01..07 (n=7), V4 ROI; same as cached wretrained.
- **CVD target vuln**: identical across all conditions per subject (loaded from `sub-XX_V4_wfixed_summary.json`).

## §0 framing reminder

Per project CLAUDE.md §0, this is a **descriptive comparison** of methodological choices. We do **not** claim specificity from any condition; we do **not** use cross-condition agreement to select a "winner" filter. Behavioral validation is the sole filter-selection ground truth (CLAUDE.md §0, behav_validation.md §3).

## Results table (16 rows)

| subject | model | simulator | loss | argmin | norm_or_Δλ | ρ | CCC | L_fit_can | L_fit_ccc | max σ_sim |
|---|---|---|---|---|---|---|---|---|---|---|
| sub-08 | 2comp | wretrained | canonical | bs=10,bc=-32 | 33.53 | +0.833 | +0.105 | 0.2170 | 0.5381 | 0.072 |
| sub-08 | 2comp | wretrained | ccc | bs=48,bc=-2 | 48.04 | +0.309 | +0.186 | 0.3421 | 0.4970 | 0.150 |
| sub-08 | 2comp | wfixed | canonical | bs=6,bc=-48 | 48.37 | +0.762 | +0.090 | 0.2483 | 0.5548 | 0.094 |
| sub-08 | 2comp | wfixed | ccc | bs=46,bc=-20 | 50.16 | +0.286 | +0.121 | 0.3438 | 0.5170 | 0.138 |
| sub-08 | machado | wretrained | canonical | dlam=1.5 | 1.5 | +0.619 | +0.190 | 0.2738 | 0.5114 | 0.113 |
| sub-08 | machado | wretrained | ccc | dlam=1.0 | 1.0 | +0.476 | +0.191 | 0.3083 | 0.5091 | 0.119 |
| sub-08 | machado | wfixed | canonical | dlam=20.0 | 20.0 | +0.619 | +0.096 | 0.2942 | 0.5723 | 0.125 |
| sub-08 | machado | wfixed | ccc | dlam=0.0 | 0.0 | +0.333 | +0.072 | 0.3508 | 0.5699 | 0.145 |
| sub-09 | 2comp | wretrained | canonical | bs=30,bc=+46 | 54.92 | +0.500 | +0.304 | 0.2840 | 0.4760 | 0.157 |
| sub-09 | 2comp | wretrained | ccc | bs=30,bc=+46 | 54.92 | +0.500 | +0.304 | 0.2840 | 0.4760 | 0.157 |
| sub-09 | 2comp | wfixed | canonical | bs=46,bc=+48 | 66.48 | +0.214 | +0.112 | 0.3574 | 0.5620 | 0.137 |
| sub-09 | 2comp | wfixed | ccc | bs=46,bc=+50 | 67.94 | +0.143 | +0.114 | 0.3743 | 0.5602 | 0.139 |
| sub-09 | machado | wretrained | canonical | dlam=13.5 | 13.5 | +0.762 | +0.274 | 0.2099 | 0.4845 | 0.121 |
| sub-09 | machado | wretrained | ccc | dlam=13.5 | 13.5 | +0.762 | +0.274 | 0.2099 | 0.4845 | 0.121 |
| sub-09 | machado | wfixed | canonical | dlam=3.5 | 3.5 | +0.095 | +0.033 | 0.3656 | 0.5830 | 0.143 |
| sub-09 | machado | wfixed | ccc | dlam=0.0 | 0.0 | +0.048 | +0.044 | 0.3716 | 0.5721 | 0.145 |

## Key observations

### A. Within (subject × model), do canonical vs CCC argmins agree?

- sub-08 2comp wretrained: canonical=β=(10,-32), ccc=β=(48,-2) → DIVERGE
- sub-08 2comp wfixed: canonical=β=(6,-48), ccc=β=(46,-20) → DIVERGE
- sub-08 machado wretrained: canonical=Δλ=1.5, ccc=Δλ=1.0 → DIVERGE
- sub-08 machado wfixed: canonical=Δλ=20.0, ccc=Δλ=0.0 → DIVERGE

- sub-09 2comp wretrained: canonical=β=(30,+46), ccc=β=(30,+46) → AGREE
- sub-09 2comp wfixed: canonical=β=(46,+48), ccc=β=(46,+50) → DIVERGE
- sub-09 machado wretrained: canonical=Δλ=13.5, ccc=Δλ=13.5 → AGREE
- sub-09 machado wfixed: canonical=Δλ=3.5, ccc=Δλ=0.0 → DIVERGE

### B. Within (subject × loss), do wretrained vs wfixed argmins agree?

- sub-08 2comp canonical: wretrained=β=(10,-32), wfixed=β=(6,-48) → DIVERGE
- sub-08 2comp ccc: wretrained=β=(48,-2), wfixed=β=(46,-20) → DIVERGE
- sub-08 machado canonical: wretrained=Δλ=1.5, wfixed=Δλ=20.0 → DIVERGE
- sub-08 machado ccc: wretrained=Δλ=1.0, wfixed=Δλ=0.0 → DIVERGE

- sub-09 2comp canonical: wretrained=β=(30,+46), wfixed=β=(46,+48) → DIVERGE
- sub-09 2comp ccc: wretrained=β=(30,+46), wfixed=β=(46,+50) → DIVERGE
- sub-09 machado canonical: wretrained=Δλ=13.5, wfixed=Δλ=3.5 → DIVERGE
- sub-09 machado ccc: wretrained=Δλ=13.5, wfixed=Δλ=0.0 → DIVERGE

### C. Behavioral consistency check (per `raw_behav.md`)

User note: sub-09 shows LESS behavioral color distortion than sub-08. Therefore, the sub-09 cone-shift magnitude estimate **SHOULD** be smaller than sub-08's under any behaviorally-consistent simulator/loss combination. Comparisons are made **within model class only** — `norm` (degrees, 2-comp) and `Δλ` (nm, Machado) are not directly comparable.

#### 2-component (norm in degrees)

| simulator | loss | sub-08 norm | sub-09 norm | sub-09 < sub-08? |
|---|---|---|---|---|
| wretrained | canonical | 33.5° | 54.9° | NO |
| wretrained | ccc | 48.0° | 54.9° | NO |
| wfixed | canonical | 48.4° | 66.5° | NO |
| wfixed | ccc | 50.2° | 67.9° | NO |

#### Machado 1way (Δλ in nm)

| simulator | loss | sub-08 Δλ | sub-09 Δλ | sub-09 < sub-08? |
|---|---|---|---|---|
| wretrained | canonical | 1.5 nm | 13.5 nm | NO |
| wretrained | ccc | 1.0 nm | 13.5 nm | NO |
| wfixed | canonical | 20.0 nm | 3.5 nm | YES |
| wfixed | ccc | 0.0 nm | 0.0 nm | NO |

#### Interpretation

Conditions where sub-09's estimate is smaller than sub-08's are **descriptively** consistent with the behavioral evidence. This is a **convergent-validity sanity check**, not a model-selection rule (§0). Filter selection remains governed by per-subject behavioral PASS/FAIL per behav_validation.md §3.

## Files

- `summary_8cond.csv`, `summary_8cond.json` — 16-row table.
- `landscape_sub-XX_{model}_{sim}_{loss}_<param>.png` (16 files).
- `4col_sub-XX_{model}_{sim}_{loss}_<param>.png` (16 files).
- `vuln_hue_sub-XX_{model}_{sim}_{loss}_<param>.png` (16 files).
- `comparison_grid_sub-{08,09}.png` (2 files): 4-row × 4-col matrix of stacked 8-hue swatches.

## Reproduce

```bash
# Task A: augment 2-comp wretrained landscapes with vuln_sim (~10 min each)
python scripts/comparison_8cond_taskA.py 08
python scripts/comparison_8cond_taskA.py 09
# Task B: Machado wfixed landscapes (~10 s each)
python scripts/comparison_8cond_taskB.py 08
python scripts/comparison_8cond_taskB.py 09
# Task C+D: argmins, per-condition figs, grid, CSV, README
python scripts/comparison_8cond_taskCD.py
```
