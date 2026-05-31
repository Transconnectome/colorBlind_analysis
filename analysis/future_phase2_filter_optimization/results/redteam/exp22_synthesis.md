# Exp 22 — Loss-based specificity test (continuous metrics, v6 PCA 45° categorical RDM atom)

Date: 2026-05-31
Replaces: σ-bin specificity test (rejected — JND atom γ z² is smooth in δθ,
so sub-bin counts are an inappropriate discriminator).

## TL;DR

Three continuous loss-based metrics tested per realization against an
N=200 synthetic-HC fake-CVD null (same B-ROI + LOO carriers as Exp 14, same
RNG_SEED 27182).

| Candidate     | L(0,0) p (real>synth) | distance p (real>synth) | L(argmin) p (real<synth) | Bonferroni p |
|---            |:---:                  |:---:                    |:---:                     |:---:         |
| S08-stable    | 0.119                 | 0.582                   | 0.577                    | 0.358 NS     |
| S08-robust    | 0.851                 | 0.622                   | **0.005**                | **0.0149** SIG |
| S09-primary   | 0.309                 | 0.896                   | 0.468                    | 0.925 NS     |

**One out of three candidates passes loss-based specificity at α=0.05** —
S08-robust, via L(argmin) only. The other two candidates show no
single metric significantly distinguishing the real fit from the synth-HC null.

## Per-candidate verdict

### S08-stable (β_s=38, β_c=−10; γALL|RDMV1|noLOCO)
- L(0,0)=+0.536, synth mean +0.274, p=0.119 → trending but NS
- distance=38.2, synth mean 41.6 → real argmin is *closer* to origin than
  the typical synth argmin. p=0.582 in "real>synth" direction.
- L(argmin)=−0.889, synth mean −1.081 → real well is *shallower* in
  per-surface z units than the typical synth well. p=0.577 in "real<synth"
  direction.
- **No metric passes.** Real argmin (+38, −4) is non-trivial but lies within
  the cloud of synth argmins; the well at that argmin is no deeper than the
  noise floor.

### S08-robust (β_s=6, β_c=−42; γOY|RDMV2|noLOCO)
- L(0,0)=−0.462, synth mean +0.243 → real (0,0) is *lower* than typical
  synth (0,0). p=0.851 in "real>synth" direction — opposite sign of expected.
- distance=42.4, synth mean 43.7 → marginally closer than median synth.
  p=0.622. Synth argmins are typically far from origin under this combo
  (β_c-axis BC_GRID extremes are an easy attractor when the (γOY|RDMV2)
  atom set under-constrains β_s).
- L(argmin)=−2.019, synth mean −1.081, synth std 0.178 → real well is
  ≈5.1 synth-std below synth mean. **p=0.005 (real<synth)**.
- **Passes via L(argmin).** Bonferroni 0.0149 SIG. This is the same well-depth
  ratio (≈5.5×) Exp 17 reported on AVERAGED synth surface; now confirmed at
  the per-realization distribution level. The L(0,0) and distance metrics
  *fail* for this candidate because the loss surface is broad and flat
  (low z everywhere on the β_s≈0 ridge) — origin happens to sit on that
  flat band. So "loss at origin" is uninformative here; only the well's
  exceptional depth at the argmin discriminates.

### S09-primary (β_s=2, β_c=+24; γALL|RDMV1|noLOCO)
- L(0,0)=+0.481, synth mean +0.293 → trending in expected direction but
  p=0.309 NS.
- distance=24.1, synth mean 35.8 → real argmin is *closer* to origin than
  synth (synth median 35.8 vs real 24.1). p=0.896 strongly opposite.
- L(argmin)=−1.323, synth mean −1.322 → **essentially identical** to the
  synth well-depth distribution. p=0.468.
- **No metric passes.** This is the most informative null finding: although
  Exp 17 averaged-surface comparison reported a 3.9× loss ratio at the
  argmin, the per-realization distribution shows individual synth fits
  routinely reach the same depth. The Exp 17 averaging hid heterogeneity;
  averaged surfaces smooth away well-depth, exaggerating apparent CVD vs
  synth separation.

## Sub-08 vs Sub-09 contrast

- Both S08 candidates have at least one metric trending in the expected
  direction (S08-stable L(0,0)=+0.536, S08-robust L(argmin)=−2.019).
- S08-robust is the ONLY candidate where a per-realization metric reaches
  significance.
- S09-primary fails all three metrics. Particularly damning: L(argmin) is
  numerically identical to synth mean (−1.323 vs −1.322), so there is no
  evidence that the (2, +24) well is distinct from a typical synth-HC
  attractor under this combo.
- This is consistent with the broader Phase-2 reality: sub-09 V1 RDM
  evidence has always been weaker than sub-08's, and the production
  fit (2, +24) sits very close to origin in parameter space — making
  distance-from-origin discrimination structurally difficult.

## How this complements Exp 17 / 18 / 19

Exp 17 compared real vs the *mean* synth surface (averaged over 20 carriers).
That smoothing collapses noise heterogeneity and inflates apparent contrast.
Exp 22 keeps per-realization variation, asking: "How exceptional is the real
fit *vs the spread* of single synth fits?" Three of the six (candidate ×
metric pair) deepenings Exp 17 highlighted as 2–5× ratios survive
per-realization scrutiny only for S08-robust L(argmin).

This does NOT overturn Exp 18C's identifiability claim — that result is about
forward injection recoverability, which is procedure-level. Exp 22 is about
signal-vs-noise contrast at the realization level. Both can hold:
the procedure CAN recover injected signal exactly (Exp 18C), AND most CVD
real fits are still within the noise distribution of synth-HC fits (Exp 22).

Joint interpretation: production (β_s, β_c) for S08-stable, S09-primary
remain *valid descriptive signal estimates* (Exp 17/18 evidence) but
*do not exceed the synth-HC noise floor* on any of the three continuous
loss metrics at α=0.05 (this experiment). This is consistent with the
"matched-grid LOO p NS" finding of Exp 14/15 — just measured through
a different lens (surface geometry vs argmin position).

S08-robust receives genuine specificity support from L(argmin).
S08-stable and S09-primary do not.

## Methodological caveats

1. **Per-surface z-scoring** (s10b_v6_pca_rdm.zscore_grid). L(0,0) and
   L(argmin) are in per-realization standard units, NOT raw loss units. A
   surface with very flat composite loss will show L(argmin) ≈ −2 to −3
   purely from N(0,1) tails, regardless of true signal. The discriminator
   is "how exceptional is the argmin within its own surface's spread,
   *compared* to synth surfaces' argmin exceptionalness". Cross-candidate
   comparison of raw L(argmin) numbers is therefore not meaningful; only
   within-candidate real vs synth comparison is.
2. **Distance is on a one-sided BS grid**: distance = sqrt(β_s² + β_c²)
   with β_s ≥ 0 by construction. For synth argmins that hit β_s = 0 (a
   common attractor when noisy data has no β_s signal), distance reduces
   to |β_c|; synth distributions are therefore concentrated in 30–50,
   making "real > synth" hard to pass even when real is genuinely
   non-trivial.
3. **Bonferroni at 3 tests**: chosen over Fisher because the three
   metrics are derived from the same surface (highly correlated). Fisher
   independence assumption would overstate significance; Bonferroni is
   conservative but appropriate.
4. **N=200, same seed as Exp 14**: synth realizations are identical to
   those characterized in Exp 14 by argmin alone. Exp 22 adds 3 metrics to
   the same draws — cross-experiment comparison is direct.

## Files

- `exp22_origin_loss_specificity.py` — runnable script
- `exp22_origin_loss_specificity.json` — per-candidate metrics + raw 200-vec
  distributions for L(0,0), distance, L(argmin) per metric
- `exp22_run.log` — full execution log
