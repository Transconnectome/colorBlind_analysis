# S18 — Interpretation (held-out predictive + standalone fits)

_2026-06-02. Answers two user questions; tables in `s18_heldout_predictive.md`,
data in `s18_heldout_predictive.json`. Candidates: S08-robust (sub-08 deutan,
γOY+RDMV2, prod (6,−42)) and S09-primary (sub-09 protan, γALL+RDMV1, prod (2,+24))._

## Q1 — Is LOO predictive performance a usable selection criterion?

**What the user asked for = TEST-LOSS in LOO** (held-out predictive loss of the
train fit), **not** parameter/argmin stability. And the right reference for "is the
value GOOD" is the **no-correction baseline (0,0)** — same treatment as γ — NOT the
held-out oracle (oracle answers "how close to best", which is trivially small in a flat
basin and does not test goodness). Reporting that directly:

**The stable value beats no-correction on held-out HC — for BOTH subjects (positive).**
Per fold, fit δθ* on the other 6 HC, evaluate test-loss on the held-out HC, compare to
the (0,0) no-correction baseline:

(combined = the production filter fit; numbers below are for the production filter.)

| Candidate | RDM L_test(fit) med | RDM ΔL vs (0,0) med | folds beating (0,0) | grid pct med (de-confound) |
|---|---|---|---|---|
| S08-robust (6,−42) | 0.594 | **−0.406** | **7/7** | 0.05 (beats 95% of grid) |
| S09-primary (2,+24) | 0.528 | **−0.472** | **7/7** | 0.08 (beats 92% of grid) |

- `ΔL vs (0,0)` = L_test(fit) − L_test(no-correction). For RDM, (0,0) is the
  no-structure floor (loss≡1.0). ΔL<0 every fold → the stable value predicts held-out
  HC geometry better than doing nothing, on EVERY held-out subject, for both candidates.
- **Degeneracy resolved by percentile**: (0,0)=1.0 could be a trivial floor; the
  grid-null percentile shows the production fit is not merely below 1.0 but in the better
  ~92–95% tail (rdm-only standalone is looser, ~87%; an arbitrary shift centers near 1.0),
  so the (0,0) win is non-trivial.
- (gen_gap vs held-out oracle is small too — S08 0.03, S09 0.07 — but oracle is the
  wrong reference for "goodness"; reported only as a closeness-to-best footnote.)
- **Honest bound**: "good vs no-correction / vs arbitrary shift" ≠ "the unique correct
  value." The basin is ~20° wide (Test 2a), so nearby values are similarly good → the
  value is **in the good region**, not point-resolved.

**The train fit itself is stable and reproduces s17 exactly** (NOT re-derived here as a
selection number — just confirming consistency): S08-robust β_c [−46,−38] (β_s [2,12]);
S09-primary (2,24) deterministic all 7 folds. So stability and held-out test-loss are
**both positive**.

**Why this does not contradict the closure's ~20–25° non-identifiability (Test 2a).**
Test 2a is point-precision under synthetic GT recovery; the LOO test-loss is held-out
prediction. Both follow from one geometry — a **broad, shallow low-loss basin**:
consistently centered (→ stability), shared across subjects + beating no-correction
every fold (→ ΔL vs (0,0) < 0), but ~20° wide (→ absolute value not resolvable).
test-loss adds beyond stability by ruling out overfitting (a stable fit could still be
misspecified) and confirming the value beats no-correction; it does **not** pin the value
to <~20° (basin width). Honest statement: *real, shared, reproducible direction that
beats no-correction; value uncertain to ±~20°.*

**Correction to a prior over-claim (retracted).** An earlier draft headlined "does NOT
identify (β_s,β_c)" based on the **per-fold oracle β_c** (each held-out *single*-HC's own
argmin) sign-flipping across folds. That is single-HC *target noise* + basin shallowness,
**not** the test-loss and **not** the right basis for an identifiability verdict. It is
demoted to a caveat below; the headline is the ΔL-vs-(0,0) table above.

What LOO *also* discriminates (reportable):
1. **Direction (β_c sign) is held-out-robust for S08 only.** Production, γ-only,
   RDM-only, and the across-HC averaged RDM surface all place S08 β_c strongly
   negative (−26 to −44; in-sample low-set [−50,−26], no sign ambiguity). For S09 the
   sign is ambiguous in-sample (low-set [−14,+24] crosses 0).
2. **The behavioral (γ) term carries real held-out signal for S08, none for S09.**
   S08 γ beats no-shift by ΔL=−13.8 (neg_frac 0.71); S09 γ ΔL=+0.01 (neg_frac 0.43)
   — γ does not beat the no-correction baseline for sub-09. Consistent with the
   closure's behavioral-validation suspension (A4) and behav β_c≈0 for sub-09.

**Caveat (demoted, not headline):** per-fold oracle β_c — S08 −26,−44,+26,+26,+24,−44,−26
(IQR 60°); S09 −32,−32,−22,0,0,+24,0 (IQR 27°). This is single-HC noise + basin
shallowness, consistent with Test 2a's basin width; it is NOT evidence against the
train fit, which is stable (above) and beats no-correction every fold (ΔL-vs-(0,0) table).

(γ uses the held-out HC JND as baseline input, normalized by train 6-HC SD, target =
CVD JND → "reference-robustness". RDM (0,0) is degenerate (always 1.0) = the
no-structure floor; ΔL vs (0,0) is meaningful because the grid percentile shows the win
is in the better tail, not just beating the floor.)

## Q2 — Neural-only (RDM) standalone fit performance

Reporting each term's standalone full-pool fit (not just the neural *increment*):

| | combined (prod) | γ-only (behav) | RDM-only (neural) |
|---|---|---|---|
| S08-robust | (6, −42) | (6, −42) | (4, −26) |
| S09-primary | (2, +24) | (26, +4) | (0, +24) |

- **S08-robust = triangulation.** Behavioral-only and neural-only independently put
  β_c strongly negative (−42 / −26). The combined fit is not driven by one term; both
  agree on the deutan cortical direction. This is the robust, reportable convergence.
- **S09-primary = behavioral/neural disagreement, neural-driven.** γ-only says β_c≈+4
  (≈0) with large β_s; RDM-only says β_c=+24 with β_s≈0. The production (2,+24) is
  essentially the **neural(RDM)-only fit** — behavior does not support it (γ ΔL≈0). The
  neural term, however, **does carry held-out signal**: RDM ΔL vs (0,0) = −0.47, beating
  no-correction on 7/7 folds (Q1). So the S09 filter rests on the neural RDM term, and
  that term is predictively good vs no-correction — but its absolute value/sign is not
  pinned (in-sample sign-ambiguous, ~20° basin), and behavior does not corroborate it.

## Bottom line

- Adding LOO predictive performance is a **good methodological upgrade** and is now
  reported. Result is **positive**: the stable value beats no-correction (ΔL vs (0,0) < 0)
  on every held-out HC for both subjects, and sits in the better ~92–95% of the grid —
  i.e. the stable value is also a **good** value, not just a reproducible one (rules out
  overfitting + arbitrariness). It does **not** pin the absolute value (~20° basin width,
  Test 2a), so it is a reportable generalization metric, not a value-crowning criterion.
  Both production filters remain descriptive embeddings (§0 intact, no override used).
- The clean new statements are: **S08 direction (β_c<0) is held-out-robust and
  behavior/neural-triangulated; S09's β_c=+24 is neural-only — it beats no-correction
  out-of-sample (RDM ΔL=−0.47, 7/7) but is not behavior-supported, its absolute value is
  not pinned (sign-ambiguous in-sample, ~20° basin), and it is aggregation-fragile.** This
  sharpens — does not contradict — the closure's "S08 stronger / S09 weak, behavioral
  test pending" stance.
- Caveats: held-out target = single HC (noisy); n=6 effective HC; 8 colors × model =
  data at expressive limit (A8). These are generalization/descriptive numbers, not
  specificity claims.
