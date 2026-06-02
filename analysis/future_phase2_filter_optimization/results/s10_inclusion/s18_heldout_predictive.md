# S18 — Held-out-HC predictive eval + standalone fits

_generated: 11.3s, 2 candidates_

## Q2 — Standalone full-pool (7 HC) fits  (beta_s, beta_c)

| Candidate | combined (prod) | gamma-only (behav) | rdm-only (neural) |
|---|---|---|---|
| S08-robust (prod (6,-42)) | (6, -42) | (6, -42) | (4, -26) |
| S09-primary (prod (2,24)) | (2, 24) | (26, 4) | (0, 24) |

## Q1 — Held-out HC-LOO predictive performance: does the stable value beat no-correction (0,0)?

Primary metric = **ΔL vs (0,0)** (test-loss improvement over no-correction), applied uniformly to gamma and rdm. For rdm, (0,0) = no-structure floor (loss≡1.0); the grid percentile de-confounds the (0,0) win (LOW pct = beats arbitrary shift, not just the floor). gen_gap (vs held-out oracle) demoted to footnote — answers 'close to best', not 'good'.

| Candidate | variant | gamma ΔL med (neg_frac) | rdm L_test med | rdm ΔL vs(0,0) med (folds<00) | rdm grid pct med |
|---|---|---|---|---|---|
| S08-robust | combined | -13.85 (0.71) | 0.594 | -0.406 (1.00) | 0.05 |
| S08-robust | gamma | -13.81 (0.71) | — | — | — |
| S08-robust | rdm | — | 0.640 | -0.360 (1.00) | 0.13 |
| S09-primary | combined | +0.01 (0.43) | 0.528 | -0.472 (1.00) | 0.08 |
| S09-primary | gamma | -0.55 (0.57) | — | — | — |
| S09-primary | rdm | — | 0.528 | -0.472 (1.00) | 0.08 |

## Q1 (caveat, NOT the headline) — per-fold oracle β_c spread

The headline is the ΔL-vs-(0,0) table above (stable value beats no-correction). The quantity below is the per-fold ORACLE β_c (each held-out *single*-HC's own argmin) — single-HC target noise + broad-basin shallowness (closure Test 2a ~20° width). It is NOT the test-loss and NOT a basis for an identifiability verdict on the (stable) train fit (s17: S08 β_c[-46,-38]; S09 (2,24) det.).

| Candidate | prod beta_c | per-fold oracle beta_c | neg_frac | oracle bc IQR | note |
|---|---|---|---|---|---|
| S08-robust | -42 | -26,-44,26,26,24,-44,-26 | 0.57 | 60 | single-HC noise / basin width |
| S09-primary | 24 | -32,-32,-22,0,0,24,0 | 0.43 | 27 | single-HC noise / basin width |

**(b) In-sample aggregation sensitivity** — mean-of-cosines argmin vs production-style cosine-of-mean (rdm-only standalone). Both in-sample; disagreement = optimum fragile to HC pooling (NOT a generalization claim).

| Candidate | cosine-of-mean (rdm-only) | mean-of-cosines | low-set beta_c | beta_c sign amb? | aggregation |
|---|---|---|---|---|---|
| S08-robust | (4,-26) | (0,-44) | [-50,-26] | no | FRAGILE |
| S09-primary | (0,24) | (32,0) | [-14,24] | YES | FRAGILE |

## Interpretation guardrails

- gamma dL < 0 = fitted shift explains CVD JND anomaly on held-out HC ref better than no-shift; neg_frac near 1.0 = consistent.
- rdm percentile near 0 = train-fitted shift is also (near-)optimal for held-out HC's CVD-vs-HC geometry = generalizes. Near 0.5 = the specific value does not transfer (any shift comparable).
- These are GENERALIZATION numbers, not specificity (§0). Expected outcome given closure verification (~20-25deg floor): most cells near null. A non-circular reportable metric is the deliverable, not a rescue.