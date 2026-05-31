# Exp 20 — L_RDM (W-based, 1°) re-fit vs Production atom (45°)

Date: 2026-05-30 (final)
Context: User flagged that the production atom (`make_rdm_atom` in
s10b_v6_pca_rdm.py:120) uses 45° integer quantization, while the project's
other RDM formulation (`L_RDM` in neural_loss.py:156) uses W-based 1° resolution.
This experiment re-fits the 3 candidates with L_RDM to test atom sensitivity.

## TL;DR

**Three candidates split into three patterns** under L_RDM (1°) vs production
(45°) atom comparison:

| Pattern | Candidate | Production (45°) | L_RDM (1°) | Verdict |
|---|---|---|---|---|
| **Robust** | S08-robust | (+6, −42) | (0, −40) | Distance 6.3°. Signal magnitude consistent across atoms. ROBUST SIGNAL |
| **Mis-specified** | S08-stable | (+38, −10) | (0, +2) | Distance 40°. L_RDM rejects 2-comp at production location. 45° atom may overfit. |
| **Truncated** | S09-primary | (+2, +24) | (+2, +50) bdy | β_s consistent. β_c hits +50 boundary under L_RDM → true magnitude > +50 |

**Signal exists in ALL three** (REAL loss 5-10× deeper than SYNTH loss under L_RDM),
but signal's interpretability under the 2-component model varies.

## Loss landscape comparison

| Candidate | REAL argmin (L_RDM) | REAL loss | SYNTH argmin (L_RDM, N=20) | SYNTH loss | Loss ratio | Surface cos sim |
|---|---|---|---|---|---|---|
| S08-stable | (0, +2) bdy | −1.083 | (+50, −8) bdy | −0.219 | **5.0×** | +0.811 |
| S08-robust | (0, −40) bdy | −1.980 | (+44, −14) | −0.203 | **9.8×** | −0.224 |
| S09-primary | (+2, +50) bdy | −0.830 | (+22, −50) bdy | −0.153 | **5.4×** | +0.636 |

All three show STRONG signal evidence: REAL loss is 5-10× deeper than synthetic
HC noise loss. This is unchanged from Exp 17 (which used production atom).

## Per-candidate detailed verdict

### S08-robust — strongest candidate

- **Production atom (45°)**: (+6, −42), loss −2.019
- **L_RDM (1°)**:           (0, −40), loss −1.980

Distance between atoms = 6.3° (β_s 6→0 boundary shift, β_c −42→−40 essentially same).

Both atoms find β_c ≈ −40 to −42. Both have loss ~−2.0. Both surfaces
anti-correlated with synthetic-HC noise (Exp 17 cos sim = −0.28; Exp 20 cos sim
= −0.22 — same orthogonal direction).

→ The signal in sub-08's V2 PCA-RDM is well-explained by 2-component cortical
rotation with β_c ≈ −40° (confusion-axis rotation toward green-purple).
**This finding is robust to atom-resolution choice.**

### S08-stable — atom-sensitive, 2-comp may be mis-specified

- **Production atom (45°)**: (+38, −10), loss −0.889
- **L_RDM (1°)**:           (0, +2), loss −1.083

Distance between atoms = 39.8° (β_s 38→0 boundary shift, β_c −10→+2 sign flip).

Both surfaces have LOSS DEEPER than synth (1.4× / 5.0×) → SIGNAL PRESENT.
But the location is COMPLETELY DIFFERENT.

Interpretation: sub-08's V1 PCA-RDM signal exists but is NOT well-modeled as
2-component rotation at any specific (β_s, β_c). At 45° resolution, the
procedure quantizes the signal into discrete index swaps and finds a "best
discrete approximation" at (38, −10). At 1° resolution, the procedure rejects
this approximation and lands at the null hypothesis (0, +2).

**The production fit (38, −10) for S08-stable is likely an artifact of 45°
quantization fitting non-2-comp signal as a coarse 2-comp pattern.**

### S09-primary — β_s robust, β_c truncated

- **Production atom (45°)**: (+2, +24), loss −1.323
- **L_RDM (1°)**:           (+2, +50) bdy, loss −0.830

β_s is IDENTICAL across atoms (+2). β_c moves from +24 (interior) to +50
(upper boundary).

The L_RDM surface continues to decrease beyond β_c = +50 — the grid is too
narrow. Under L_RDM, sub-09's protan signal extends past the production grid's
upper boundary.

**True β_c for sub-09 protan is likely > +50°** under the L_RDM model. The
production fit (+2, +24) is a *partial* signal estimate due to 45° quantization
compressing the magnitude.

## Implications

### For S08-robust
Production fit (6, −42) is **directly defensible** as the cortical β_c estimate.
Phase 3 stimulus design at this magnitude is justified.

### For S08-stable
Production fit (38, −10) is **NOT defensible as a cortical 2-comp estimate**.
L_RDM evidence suggests sub-08's V1 PCA-RDM signal is real but doesn't fit
2-component model well. Options:
1. Use S08-robust (6, −42) as the SOLE sub-08 candidate (V2-based, robust)
2. Investigate what model (if not 2-comp) explains S08-stable's signal
3. Drop the S08-stable candidate

### For S09-primary
The (+2, +24) production fit is **truncated by quantization**. L_RDM finds the
signal magnitude is at least +50. Phase 3 design needs to consider:
1. Extended grid (wider BC_GRID to find true β_c)
2. Use production (+2, +24) as conservative lower bound
3. Test multiple magnitudes in stimulus design (sweep 24, 36, 50)

## Wider context — atom choice and project framework

### Why production used 45° atom
Cycle 5 finding (`s10b_v6_pca_rdm.py:121` docstring): PCA-based RDM with
discrete index swap gave 2× better HC-CVD separation than voxel-RDM.

But Cycle 5 tested SEPARATION not IDENTIFIABILITY. Better separation doesn't
mean better cortical parameter estimation. The 45° quantization sacrifices
angular resolution for separation strength.

### Why L_RDM (1°) is the more principled model
- Uses encoder W trained per HC (proper model-based prediction)
- 1° basis lookup (effectively continuous angle)
- Directly tests "if perceived angle is θ', predicted neural response is C(θ')·W"
- Maps closer to forward physiological model

### Asymmetry in current pipeline
- TRAIN atom: `make_rdm_atom` (PCA, 45°)
- TEST atom: `make_test_V1_RDM` uses `L_RDM` (W-based, 1°)

This asymmetry was likely not intentional. The train atom should match the
test atom's resolution for self-consistency.

## What to do with closure

### Production atom record (for traceability)
- KEEP production fits (38,−10), (6,−42), (2,+24) in closure as "Phase B v6
  production atom record"
- Document the atom used (45° PCA)
- Reference Cycle 5 rationale

### L_RDM atom diagnostic (for interpretation)
- ADD §A.13: L_RDM re-fit results (this experiment)
- Report (β_s, β_c) per candidate under both atoms
- Per-candidate verdict (Robust / Mis-specified / Truncated)

### Per-candidate recommendation for Phase 3

| Candidate | Phase 3 recommendation |
|---|---|
| S08-robust | (6, −42) ≈ (0, −40) — atom-robust; use for stimulus design |
| S08-stable | DROP or further investigate; not 2-comp interpretable |
| S09-primary | Use (+2, +24) as conservative lower bound; consider magnitude sweep including β_c ≥ +50 |

### L1 framing — finally settled

> **L_RDM (W-based, 1°) re-fit shows: S08-robust signal is robust across atoms
> (β_c ≈ −40 to −42), S08-stable signal exists but is mis-specified by 2-comp
> at fine resolution, S09-primary β_c is truncated by current grid (true value
> ≥ +50). Production atom (45° PCA) fits should be interpreted as: atom-robust
> for S08-robust, quantization-amplified for S08-stable, magnitude-truncated
> for S09-primary.**

## Files

- `exp20_lrdm_refit.json` — argmin + comparison metrics
- `exp20_lrdm_refit.npz` — full loss surfaces (REAL + SYNTH for 3 candidates)
