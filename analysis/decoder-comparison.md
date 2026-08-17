# Decoder comparison — why the encoding (ρ) and decoding (accuracy) readouts use different regularization

**Date**: 2026-06-13 · **Status**: reference (records the decoder rule + full dissociation)

## TL;DR (the rule)

The forward-encoding channel model (B&H 2009, FE-6) is read out in **two opposite
directions**, and each direction uses the regularization appropriate to it:

| Task | Direction | Readout | Decoder | Why |
|---|---|---|---|---|
| **Decoding** (color/hue interpolation, LOCO/LORO **accuracy**) | voxels → channels → hue (`ĉ = Wx`, argmax over hue basis) | adjacent_acc, exact_acc, MAE | **α = 0 (pseudoinverse, B&H canonical)** | decode depends on the *angular profile* of `ĉ`; ridge shrinkage flattens it → worse hue decode |
| **Encoding** (voxel-pattern prediction, forward-tuning **ρ**) | channels → voxels (`X̂ = CWᵀ`) | voxel_corr ρ | **ridge-GCV** | regularization improves out-of-sample voxel prediction (standard) |

This is a **principled rule keyed to direction**, not a per-result decoder pick. Both
readouts are reported; the dissociation below is recorded for completeness/transparency.

## The double dissociation (our data — HC group mean, Procrustes voxel space)

Source: `phase4_forward_model/results/validation/validation/sub-*_loco.json`
(per-decoder, per-fold). Chance: adjacent 3/8 = 0.375, exact 1/8 = 0.125. MAE in degrees.
**Decoders are columns** (`_ols` = α=0 pseudoinverse, `_gcv` = ridge-GCV); **bold** = winner
per metric. Left block = **decoding** (α=0 should win); right block = **encoding** (GCV should win).

| ROI | adj_ols | adj_gcv | exact_ols | exact_gcv | MAE_ols | MAE_gcv | ρ_ols | ρ_gcv |
|---|---|---|---|---|---|---|---|---|
| V1 | **0.393** | 0.262 | **0.262** | 0.104 | **76.4** | 92.1 | 0.051 | **0.130** |
| V2 | **0.357** | 0.229 | **0.265** | 0.128 | **80.0** | 95.2 | 0.092 | **0.150** |
| V3 | **0.339** | 0.280 | **0.271** | 0.188 | **76.9** | 85.4 | 0.023 | 0.023 |
| hV4 | **0.456** | 0.364 | **0.360** | 0.270 | **69.0** | 81.0 | 0.158 | **0.183** |
| hV4 (n6) | **0.465** | 0.378 | — | — | — | — | — | — |

- **Decoding (adj / exact / MAE)**: `_ols` (α=0) wins **4/4 ROIs** — higher accuracy, lower MAE.
- **Encoding (ρ)**: `_gcv` wins **V1, V2, hV4** (V3 tie). Clean double dissociation across columns.

## Why it matters for the paper's central result

The interpolation-deficit claim (HC interpolates at hV4, CVD does not) is **clean only
under α=0**, and **muddied under ridge-GCV**:

| hV4 adjacent_acc | HC (above chance?) | sub-08 | sub-09 |
|---|---|---|---|
| **α=0** (Procrustes voxel) | **0.456 ✓** | 0.250 | 0.125 |
| **α=0** (SRM-aligned, paper Fig2) | **0.470 ✓** | 0.271 | 0.104 |
| ridge-GCV (Procrustes voxel) | 0.364 ✗ (≈chance) | 0.021 | 0.167 |

Under ridge-GCV the HC reference itself sits at chance and sub-09 (0.167) is no longer
below it → the deficit disappears. **α=0 is what makes the deficit interpretable.** The
paper's Fig 2/3 LOCO (HC hV4 0.47, p=0.044) is the **SRM-aligned α=0 ForwardEncoding**
(`phase3_decoder_comparing/results/loco_srm/sub-*_loco.json`), and CVD is computed with the
same α=0 → the result is internally consistent.

> Note: α=0 vs space. SRM-α=0 (0.470) ≈ Procrustes-voxel-α=0 (0.456) → the **decisive
> factor is the decoder (α=0), not the alignment space**; SRM adds only a marginal gain.
> Whether SRM's structure is *genuinely* more interpolation-favorable than Procrustes
> (or its PCA) is tested separately in `phase_supplementary/srm_interpolation_structure.md`.

## CVD individuals (hV4, decoders as columns, Procrustes voxel)

| subject | adj_ols | adj_gcv | exact_ols | exact_gcv | MAE_ols | MAE_gcv | ρ_ols | ρ_gcv |
|---|---|---|---|---|---|---|---|---|
| sub-08 (deutan) | 0.250 | 0.021 | 0.250 | 0.021 | 82.9 | 100.3 | −0.204 | −0.275 |
| sub-09 (protan) | 0.125 | 0.167 | 0.083 | 0.083 | 99.1 | 96.9 | −0.076 | −0.035 |
| sub-10 (deutan) | 0.167 | 0.125 | 0.146 | 0.083 | 80.2 | 84.3 | 0.079 | 0.137 |

(Both CVD show **negative** ρ at hV4 under both decoders — the channel model predicts CVD
voxel patterns poorly, an encoding-side deficit distinct from the decode deficit.)

## sub-08 exp2 — 2×2 (decoder × task) ON the filter conditions

`exp2_neural/scripts/exp2_decoder_2x2.py` (jobs 108926/108927, 2026-06-13). Each cell is
the within-condition LOCO mean; decoders as columns. ENCODING wants **gcv** high, DECODING
wants **ols** high. Conditions: HC ref (n=7 full) | no-filter (sub-08 exp1) | window | optimal.
**native** voxel set (858 @V1); chance adj 0.375 / exact 0.125.

| ROI | cond | ρ_ols | ρ_gcv | adj_ols | adj_gcv | exa_ols | exa_gcv |
|---|---|---|---|---|---|---|---|
| V1 | HC | 0.051 | **0.130** | **0.393** | 0.262 | **0.262** | 0.104 |
| V1 | no-filter | −0.097 | −0.062 | 0.437 | 0.271 | 0.312 | 0.146 |
| V1 | window | −0.430 | **−0.318** | 0.219 | 0.250 | 0.219 | 0.219 |
| V1 | optimal | 0.112 | **0.212** | **0.406** | 0.344 | **0.344** | 0.188 |
| V2 | HC | 0.092 | **0.150** | **0.357** | 0.229 | **0.265** | 0.128 |
| V2 | optimal | 0.017 | **0.098** | **0.406** | 0.344 | 0.219 | 0.125 |
| V3 | HC | 0.023 | 0.023 | **0.339** | 0.280 | **0.271** | 0.188 |
| V3 | no-filter | −0.041 | **0.049** | **0.375** | 0.208 | **0.354** | 0.146 |
| V3 | optimal | −0.075 | **0.048** | 0.250 | **0.406** | 0.125 | 0.125 |
| hV4 | HC | 0.203 | **0.232** | **0.465** | 0.378 | **0.358** | 0.281 |
| hV4 | no-filter | −0.204 | −0.275 | **0.250** | 0.021 | **0.250** | 0.021 |
| hV4 | window | −0.381 | −0.388 | 0.250 | 0.250 | 0.250 | 0.250 |
| hV4 | optimal | −0.005 | **0.179** | 0.312 | **0.375** | 0.250 | 0.219 |

**The dissociation replicates on exp2** (HC + no-filter): encode ρ favors gcv, decode acc
favors ols (hV4 no-filter adj **ols 0.250 vs gcv 0.021** — gcv collapse). Use ρ from the
**gcv** column, accuracy from the **ols** column.

**Filter readout with the CORRECT decoders:**
- **Encoding ρ (gcv)**: Optimal ≫ Window in *all* ROIs (V1 +0.21 vs −0.32 … hV4 +0.18 vs −0.39) — robust; this is the paper Fig 8A contrast.
- **Decoding adj (ols)**: Optimal ≥ Window in 4/4 ROIs (V1 .406>.219, V2 .406>.312, V3 .250>.219, hV4 .312>.250). **But Optimal > no-filter only 2/4** (V2, hV4; V1/V3 no-filter is higher). So on decoding accuracy the defensible claim is *"Optimal recovers the Window decoding loss,"* **not** *"Optimal beats no-filter."* (The earlier ridge-GCV-based "Optimal>no-filter 4/4" was the decoder bug.)
- matched variant: same direction; V1 optimal adj 0.406→0.250 (V1's native edge partly occipital coverage).

## hV4-restricted view — the permutation-valid ROI (both aspects)

LOCO interpolation is statistically real **only at hV4**. Group-level HC permutation
(n=7, 10,000 perms, `phase4_forward_model/results/loco_reinforcement/permutation_test.json`),
on the forward-model LOCO metric:

| ROI | observed | p_perm | |
|---|---|---|---|
| V1 | 0.130 | 0.274 | fail |
| V2 | 0.150 | 0.311 | fail |
| V3 | 0.023 | 0.880 | fail |
| **hV4** | **0.183** | **0.0435** | **PASS** |

So V1–V3 LOCO is null-range and must NOT be used to judge the filter; the comparison
collapses to hV4. At hV4 (sub-08 exp2; native = matched, robust), **Optimal beats both
Window and no-filter on BOTH aspects**:

| readout (hV4) | HC | no-filter | Window | Optimal |
|---|---|---|---|---|
| **Encoding** LOCO ρ (forward-tuning) | 0.208 | −0.272 | −0.388 | **0.179** |
| **Decoding** adjacent acc (chance .375) | 0.465 | 0.231 | 0.250 | **0.312** |
| (ref) LORO discrimination acc (chance .125) | 0.656 | 0.521 | 0.406 | 0.406 |

- Encoding: Optimal restored to ≈ HC; Window and no-filter both negative → Optimal ≫ both.
- Decoding: Optimal is the highest of the three filter conditions (recovers ~⅓ of the
  no-filter→HC gap; still below HC).
- The all-ROI "Optimal > no-filter only 2–3/4" weakness was driven by V1/V3, where LOCO is
  permutation-null — not valid evidence. Restricting to the permutation-valid ROI (hV4),
  Optimal is superior on encoding AND decoding.

Caveats: single subject, descriptive (no inferential p on the filter contrast); permutation
establishes hV4 as the interpolation ROI in HC, it is not a test of the filter effect; the
permutation observed (0.183) is the forward-model ρ metric (ridge-GCV voxel_corr).

## Open items this implies

1. **methods_v2 wording** *(paper edit, OPEN)*: §L90/L100 describe a *single* ridge-GCV `W`
   for both LORO and LOCO. Inaccurate — **accuracy** readouts use the α=0 pseudoinverse.
   Methods must state the two-decoder rule (decode = B&H pseudoinverse α=0; encode =
   ridge-GCV) with the B&H citation.
2. **exp2 fix** *(DONE 2026-06-13)*: `exp2_neural/scripts/exp2_hc_likeness.py` —
   `loco_accuracy_within` now uses **α=0** (was ridge-GCV → collapsed HC to chance);
   `loco_rho_within` keeps ridge-GCV. Re-run pending verification (HC hV4 should return to
   ~0.46 n6).
3. **Shared canonical** *(DONE 2026-06-13)*: `phase4_forward_model/scripts/loco_canonical.py`
   — `loco_forward_readouts(amp, C8, basis_full, decoder, tasks)` gives {rho, adj, exact} per
   decoder. `exp2_hc_likeness.py` and `exp2_decoder_2x2.py` both delegate to it (no more
   divergent reimplementation — the root cause of the exp2 bug). FROZEN `utils_forward_model`
   primitives are imported, not changed.
4. **SRM space** *(decided: NO)*: SRM has no genuine interpolation/circular-structure
   advantage over Procrustes voxel space (`phase_supplementary/srm_interpolation_structure.md`);
   exp2 stays in Procrustes voxel + α=0.

## Provenance

- Decoding/encoding per-decoder numbers: `phase4_forward_model/results/validation/validation/sub-*_loco.json` (Procrustes voxel space; keys `ols`, `ridge_gcv`, each with `folds[].errors`, `folds[].pred_hues`, `mean_voxel_corr`).
- Paper Fig 2/3 LOCO (SRM α=0): `phase3_decoder_comparing/results/loco_srm/sub-*_loco.json` (`results[ROI].ForwardEncoding`, params `{alpha:0, n_channels:6}`, `alignment:srm`).
- Numbers regenerated 2026-06-13 (NaN-guarded per-run aggregation).
