# Exp 14 / 15 / 16 — Bias measurement re-validation synthesis

Date: 2026-05-30
Context: Re-examination of yesterday's bias-correction approach after critical issues
were identified (grid mismatch, loss non-linearity, pool contamination).

## TL;DR

**Yesterday's "bias correction" proposal is fundamentally non-recoverable**: the
procedure is non-additive, partially non-identifiable, and grid-conditional.

1. **All three production fits are NS** under matched-grid LOO null (Exp 14).
2. **2×2 factorial** confirms grid mismatch was the dominant bias driver (β_s);
   pool contamination was real but smaller (β_c).
3. **Forward identifiability (Exp 16) FAILS additivity test for all 3 candidates**.
   Sub-09 worst: β_c slope = −0.42 (procedure INVERTS β_c at production magnitude).
4. **S08-robust β_c=−42** is the only signal partially recoverable (slope +0.52, exact
   recovery at GT=−42), but null distribution at GT=0 overlaps signal range.

## What survives, what falls

### FALSE — must be retracted from closure / yesterday's response

- "S08-stable β_s p=0.003 SIG" — was grid-mismatch artifact; under matched grid p=0.184.
- "Bias-corrected magnitudes" (e.g., +50.6, +8.2, +19.4) — bias is non-additive and
  grid-conditional; corrected values vary by ~30-76 across grids (INCONSISTENT
  for all candidates).
- "Phase 3 magnitude ≈ -21" (S08-robust corrected) — based on additive bias subtraction
  that Exp 16 shows is non-additive.
- "Family-specific bias is grounded in HC color-tuning gradient" — partially true
  but the magnitudes vary so much by combo that no single biological story holds.

### TRUE — stands after re-validation

- **Bias EXISTS in the procedure** (Exp 13 already showed this; Exp 14/15 confirm).
- **Family/combo specificity exists** (different cells have different null distributions
  even with all fixes; Exp 16 shows different shrinkage slopes per combo).
- **β_s grid truncation effect is large** (Exp 14 vs 15: grid effect +14 to +34 in β_s
  null mean).
- **Pool contamination was real but smaller** than grid effect (β_c shift +3 to +8).

### NEW finding — supersedes both

**The 2-component fit procedure has limited forward identifiability** under matched-grid
LOO, with combo-specific shrinkage slopes:

| Combo | β_s slope | β_c slope |
|---|---|---|
| S08-stable  (γall+RDMV1) | +0.24 | +0.37 |
| S08-robust  (γOY+RDMV2)  | +0.33 | +0.52 |
| **S09-primary (γall+RDMV1)** | **−0.29** | **−0.42** |

- Slope ≈ 1 ideal; lower = signal compressed toward attractor.
- Sub-09 has NEGATIVE slopes → procedure INVERTS signal direction at production
  magnitude. Recovery is essentially uncorrelated with truth.
- Sub-08 has weak positive slopes (0.2 to 0.5) → procedure responds to large signals
  but compresses them; small signals are invisible.

## 2×2 factorial table (full)

| Cell | β_s μ±σ | β_c μ±σ | bdy% |
|---|---|---|---|
| **S08-stable** | | | |
| Exp13 sym + NoLOO    (N=300) | −12.6±24.3 | −10.1±25.6 | 15 |
| Exp14 one-sided + LOO (N=200) | +20.4±12.3 |  +1.7±31.9 | 29 |
| Exp15 sym + LOO       (N=200) |  −6.5±32.1 | −18.4±24.7 | 28 |
| → grid effect (LOO fixed)    | +26.9 | +20.1 | — |
| → pool contam (sym fixed)    |  −6.2 |  +8.3 | — |
| **S08-robust** | | | |
| Exp13 sym + NoLOO    (N=300) |  −2.2±42.3 | −21.4±20.4 | 45 |
| Exp14 one-sided + LOO (N=200) | +36.4±15.7 | −19.4±22.4 | 36 |
| Exp15 sym + LOO       (N=200) |  +2.1±39.9 | −24.1±18.5 | 42 |
| → grid effect | +34.4 |  +4.7 | — |
| → pool contam |  −4.3 |  +2.7 | — |
| **S09-primary** | | | |
| Exp13 sym + NoLOO    (N=300) |  −0.9±27.6 |  +4.6±20.5 | 14 |
| Exp14 one-sided + LOO (N=200) | +27.1±19.6 |  +4.0±28.3 | 60 |
| Exp15 sym + LOO       (N=200) | +12.6±29.3 |  +0.9±21.3 | 19 |
| → grid effect | +14.5 |  +3.1 | — |
| → pool contam | −13.5 |  +3.7 | — |

Grid effect dominates β_s (truncation artifact under one-sided).
Pool contamination is moderate (β_c +3 to +8, β_s small).

## Statistical significance under matched grids (Exp 14 vs 15)

| Candidate | p (one-sided + LOO, Exp 14) | p (sym + LOO, Exp 15) |
|---|---|---|
| S08-stable  | (0.184, 0.756) | (0.005, 0.771) ← CVD drifted to +46 (near boundary) |
| S08-robust  | (0.095, 0.179) | (0.483, 0.169) ← CVD at corner (+48, −50) |
| S09-primary | (0.279, 0.920) | (0.876, 0.741) |

**Grid choice changes significance dramatically.** S08-stable goes from p=0.184 (NS) to
p=0.005 (SIG) under sym, but only because CVD drifted from +38 to +46 — at the +50
boundary. This is loss-surface ridge structure, not bias correction.

## Inter-grid bias-correction agreement (Exp 14 vs 15)

| Candidate | corrected (one-sided) | corrected (sym) | Δβ_s | Δβ_c | Verdict |
|---|---|---|---|---|---|
| S08-stable  | (+17.6, −11.7) | (+52.5, +8.4) | −34.9 | −20.1 | INCONSISTENT |
| S08-robust  | (−30.4, −22.6) | (+45.9, −25.9) | −76.3 | +3.3 | INCONSISTENT |
| S09-primary | (−25.1, +20.0) | (−10.6, +23.1) | −14.5 | −3.1 | INCONSISTENT |

Bias-corrected magnitudes vary by up to 76° across grids → **bias correction is not
a principled point-estimate procedure for this pipeline**.

## Forward identifiability — combo-specific shrinkage attractors

**S08-stable**: attractor near (β_s≈23, β_c≈+6). Small β_s signals invisible (slope 0
for GT_β_s ∈ [0, 10]). Large β_s GT=38 → recovers +32 (compresses ~6). β_c slope 0.37
across [-30, +0] range.

**S08-robust**: attractor near (β_s≈10-20, β_c≈−35). β_c recovers exactly at GT=−42
(slope ≈ 1 locally), but at GT=0 the procedure pulls to −20 (large bias). β_s shrinks
to ~10-20 regardless of GT. Production (6, −42) sits at the attractor — indistinguishable
from "procedure auto-lands here under noise".

**S09-primary** — WORST: at production-matched GT=(0,+24) and (+2,+24), recovered
β_c is −0.4 to −4.3 (inverted toward 0 or negative). Procedure cannot see +24 β_c
signal; instead recovers near 0. β_s wanders to ~20. Both axes effectively
non-identifiable at production magnitude.

## What this means for the closure

### Specificity claims (L1, L9, L10)
**Must be retracted/softened**:
- L1: Cannot claim "+β_s as procedure bias only" — the procedure has limited
  identifiability AND the bias is non-additive. Closure must say:
  "2-comp fit procedure has non-additive bias dependent on (combo, family, signal
  magnitude); statistical significance vs synthetic-HC null is NS for all 3 candidates
  under matched-grid LOO."
- L9 (sub-09 LOO instability): now reinforced — procedure has NEGATIVE β_c slope for
  sub-09, meaning recovery direction is wrong at production magnitude.
- L10 (combo-specific bias) — confirmed AND deepened — bias is also signal-magnitude
  dependent.

### Forward / pre-image claims (RQ5)
- Pre-image math (8/8 exact under 2-comp forward) STANDS — this is a property of the
  forward model algebra, not the fit procedure.
- "(β_s, β_c) as filter parameters" remains valid as a *descriptive fit* but cannot
  be claimed as "the cone-shift parameter the subject has" — procedure recovery is
  too compressed/inverted to support that.

### Phase 3 stimulus design
- **Cannot recommend specific (β_s, β_c) magnitudes** based on production fits — the
  fits' relationship to true parameters is unidentified.
- Phase 3 must EITHER use production fits as-is (descriptive) WITH explicit caveat
  about non-identifiability, OR test multiple candidate magnitudes (e.g., 0.5x, 1x,
  2x production) to find behaviorally effective stimulus.

### S08-robust (6, −42) — special note
The ONLY candidate where forward identifiability is partially good: at GT=(6, −42)
β_c recovery is +exact (bias −0.9). This suggests production (6, −42) might reflect
real signal of similar magnitude. BUT the procedure ALSO pulls GT=(0, 0) to (β_s≈36,
β_c≈−20), so under no-signal data this combo still drifts toward the attractor.
**S08-robust is the strongest candidate to claim signal**, but with the caveat that
null overlaps.

## Decisions

1. **Bias correction (yesterday's table)**: RETRACTED.
2. **Phase 3 magnitude recommendations**: RETRACTED. Phase 3 design must use
   production fits descriptively with magnitude-sweep stimulus tests.
3. **Closure L1**: Rewrite to emphasize non-identifiability across signal magnitudes,
   not just grid/pool bias.
4. **Closure L9**: Strengthen with Exp 16 sub-09 negative-slope evidence.
5. **Closure L10**: Update — bias is combo × family × signal-magnitude dependent;
   no per-cell offset is sufficient.
6. **New L11 (proposed)**: "Forward identifiability of 2-component fit procedure is
   combo-specific and signal-magnitude dependent. Recovery slopes range from -0.42
   (sub-09 β_c, inverted) to +0.52 (sub-08 robust β_c). Production fits are
   descriptive estimates; their relationship to true cortical parameters is
   not directly invertible."

## Next steps

1. Update closure with above retractions/additions.
2. Phase 3 design protocol: include a magnitude-sweep step (e.g., 0.5x and 1.5x
   production) rather than single-point stimulus.
3. Consider whether the 2-component fit's identifiability problem is solvable with
   more atoms / different combo (out of scope for closure; future work).
