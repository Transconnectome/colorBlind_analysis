# Gen-4.5 Diagnosis — Corrected (C_baseline bug fix)

**Date**: 2026-04-06 (revised after two bug discoveries)
**Script**: `scripts/step2_finetune_l3_v2.py`
**Result files**: `results/step2_finetune_l3_v2_stockman/sub-{08,09,10}_machado_1way.json`

## TL;DR

Two bugs invalidated the prior Gen-4.5 diagnosis (§A below). After correction,
the conclusion is **stronger**: machado_1way fails the 4-criterion selection gate
for **ALL three CVD subjects** — not just sub-09. The ΔRDM criterion is
structurally incompatible with Machado cone-shift predictions at this scale.

| Subject | Gate | Δλ best | L₁ max (V1) | L_sign max | L_fam max | Verdict |
|---------|------|---------|-------------|------------|-----------|---------|
| sub-08 deutan | 0/4 | (0,0) | 0.000 | n/a | n/a | **REJECT** |
| sub-09 protan | 2/4 | (0.5,0.5) | +0.174 | +0.071 | +0.060 | **REJECT** (sign) |
| sub-10 normal | 2/4 | (18.5,0.5) | +0.187 | +0.143 | −0.021 | **REJECT** (sign+fam) |

## A. Bugs discovered

### Bug 1: Stale `__pycache__`

The initial step2 runs loaded `.cpython-39.pyc` / `.cpython-312.pyc` from a
prior version of `l3_loss.py`. The cached `.pyc` files contained the OLD parent
class `_l1_per_roi` instead of the new `_l1_and_sign_per_roi`. This produced
L₁ values ~3× smaller and L_sign ≡ 0 for all Δλ — leading to "0/1681 pass" in
the original diagnosis.

**Fix**: `rm -rf scripts/__pycache__` + fresh run.

### Bug 2: C_baseline coordinate mismatch (CRITICAL)

`step2_finetune_l3_v2.py` used `C_baseline = create_basis_matrix(HUE_ANGLES,
N_CHANNELS)` where `HUE_ANGLES = [0, 45, 90, ..., 315]° (CIELab nominal)`.
But `_design_matrix()` calls `get_design_matrix('machado_1way', [Δλ], ...)` which
returns basis vectors at **Stockman-derived** hue angles `[299.9°, 288.4°, 278.1°,
266.5°, 243.9°, 142.6°, 105.7°, 16.4°]`.

At Δλ=0: `|C_baseline − C_machado(0)| = 0.957` (max element). This coordinate
mismatch inflated L₁(Δλ=0) to **+0.30** and L_sign to **+0.29** — entirely
artificial. The 4-gate appeared to "pass" at (0.5, 0.5) with L_fam ≈ 0.

**Fix**: `C_baseline = get_design_matrix('machado_1way', [0.0], 'protan')`.
Now L₁(Δλ=0) = 0.000 by construction. Applied to step2_finetune_l3_v2.py.

## 1. Corrected sub-09 landscape (Stockman baseline, L_roi=0)

```
best: Δλ_V1 = 0.5 nm   Δλ_V2 = 0.5 nm
      L_total      = +0.1374
      L₁_joint_T   = +0.1477      L₁_joint_O = +0.1469
      L_sign_joint = −0.036       (chance = 0)
      L_fam        = +0.0008
      L₁_V1        = +0.1737      L₁_V2      = +0.1218
gate: sign=False fam=True V1L1=True V2L1=True => all_pass=False
```

### Per-ROI 1-D slices (sub-09 protan)

```
       V1 target (protan)         V1 other (deutan)
Δλ=0.0    L1=+0.000  Ls=−0.214     L1=+0.000
Δλ=0.5    L1=+0.174  Ls=+0.000     L1=+0.206  ← deutan HIGHER
Δλ=1.0    L1=+0.139  Ls=+0.071     L1=+0.231  ← deutan HIGHER
Δλ=4.5    L1=+0.084  Ls=+0.000     L1=+0.179  ← deutan HIGHER
Δλ=8.0    L1=−0.006  Ls=−0.143     L1=+0.141
Δλ=19.5   L1=+0.011  Ls=+0.000     L1=−0.030  ← protan > deutan here only
```

Key observations:
1. V1 L₁ is positive at small Δλ (max +0.174 at Δλ=0.5), but **deutan fits
   BETTER than protan** across the entire L₁-positive range (L_fam < 0).
2. Family discrimination (L_fam > 0) only at Δλ ≥ 19.5 nm where L₁ ≈ 0.
3. L_sign never exceeds +0.071 (chance + 7%). 0/1681 grid points reach the
   0.25 sign gate.
4. V2 L₁ is positive at small Δλ (up to +0.122) but also family-non-specific.

## 2. Sub-08 result (deutan) — complete failure

```
best: Δλ_V1 = 0.0 nm   Δλ_V2 = 0.0 nm
      L_total = −0.0643
gate: sign=False fam=False V1L1=False V2L1=True => all_pass=False
```

ALL L₁ values are ≤ 0 across the entire [0, 20] nm grid. Machado's predicted
ΔRDM_sim is **anti-correlated** with the observed ΔRDM_obs:

```
sub-08 V1 ΔRDM_obs: mean=+0.109, 19 positive / 9 negative
ΔRDM_sim(Δλ=5, deutan): 9 positive / 18 negative
cosine(sim, obs) = −0.340
```

The Machado model predicts cone shifts should *compress* color distances
(ΔRDM_sim is predominantly negative), but the observed CVD–HC difference
shows expanded distances. This directional mismatch is structural.

Note: sub-08 is the subject with the strongest prior LOCO evidence
(V1 p=0.033, V2 p=0.047). **LOCO and ΔRDM measure different things.**

## 3. Sub-10 result (normal, specificity check) — expected null

```
best: Δλ_V1 = 18.5 nm   Δλ_V2 = 0.5 nm
gate: sign=False fam=False V1L1=True V2L1=True => all_pass=False
```

L_sign max=+0.143, L_fam=−0.021 (wrong family direction). Correctly rejected.

## 4. Scientific interpretation

1. **ΔRDM criterion + Machado = structural mismatch.** The Machado simulator
   produces ΔRDM_sim vectors whose sign distribution (predominatly negative =
   compression) contradicts the observed ΔRDM_obs (predominantly positive =
   expansion). This is not a Δλ-tuning problem; it's a model-class failure at
   the level of distance-structure prediction.

2. **LOCO ≠ ΔRDM.** The LOCO criterion (correlation between per-color
   predictions and observations) can succeed even when the overall distance
   structure is wrong. Sub-08 V1 LOCO p=0.033 despite ΔRDM cosine = −0.34.
   These criteria are **complementary but not concordant**.

3. **Gen-4 v1 was doubly wrong.** The (16.5, 3.0) "optimum" was both (a) an
   L_roi artifact (§5 of the original diagnosis, still correct) and (b) computed
   with the CIELab→Stockman coordinate bias that inflated L₁ by +0.30.

4. **The C_baseline fix is permanent.** All future ΔRDM-based cone-shift
   analyses must use Stockman-derived normal-vision basis as C_baseline to
   avoid the coordinate inflation artifact.

## 5. Actionable conclusions

1. **Abandon the ΔRDM criterion for Machado cone-shift fitting.** The sign
   structure of Machado-predicted ΔRDM is directionally incompatible with
   observed ΔRDM in this dataset. This applies to all three CVD subjects.

2. **Retain LOCO as the primary cone-shift criterion.** The LOCO W-fixed
   approach (Gen-2, step1_fit_loco_v2.py) remains the valid fitting engine
   for sub-08 (V1 p=0.033, V2 p=0.047). Sub-09's LOCO and ΔRDM results
   are complementary but neither produces a clean Machado fit.

3. **Phase 2 filter design**: Use LOCO-derived Δλ for sub-08 only.
   Sub-09 and sub-10 remain negative results for Machado cone-shift.

4. **Do NOT revert C_baseline.** The Stockman baseline is scientifically
   correct. The nominal-baseline results (stored in `results/step2_finetune_
   l3_v2_fresh/`) are preserved for audit but should not be used.

## 6. Files

### Corrected results (use these)
- `results/step2_finetune_l3_v2_stockman/sub-{08,09,10}_machado_1way.json`

### Stale/buggy results (preserved for audit only)
- `results/step2_finetune_l3_v2/` — pycache bug (wrong L₁ and L_sign)
- `results/step2_finetune_l3_v2_noroi/` — pycache bug + nominal baseline
- `results/step2_finetune_l3_v2_fresh/` — correct code, nominal baseline (coordinate inflation)
- `results/step2_finetune_l3_v2_fresh_noroi/` — same as above, L_roi=0
