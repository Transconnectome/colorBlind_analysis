# Revision Report — PAPER draft — 2026-06-28
Scope: Intro/introduction_v2, Methods/methods_v2, Results/results_v4, Discussion/discussion_v3 (+ supplementary skim)
Method: per-section revise-draft (academic_writing_rules §2/§5/§7/§8/§12/§19/§20/§26) + redteam-project (reviewer #2 / methodologist). Report only.

---

## Already fixed this pass
- **Discussion L40 (Conclusion)** — undefined jargon "forward-tuning" → "cortical hue interpolation" (was a FATAL comprehension stop per naive-reader; regression from earlier jargon-removal).

---

## A. Writing (revise-draft) — ranked

### FATAL
- none remaining (L40 fixed).

### SERIOUS
1. **Discussion L27 "by construction"** — jargon we removed elsewhere still here ("individualizable by construction"). → "individualizable because each filter is built from one participant's own geometry…".
2. **Discussion L27** — 3-role paragraph (architecture + identifiability/FDR + between-subtype). Split.
3. **Discussion em-dash overuse + long sentences** — L29 (1 sentence, 2 em-dashes, ~50w), L36 (two >45w), Conclusion (5 em-dashes); split. Conclusion restates "measure→fit→invert" 3×; cut to 2.
4. **Methods L16 (intro) stale order** — names LOCO+ΔRDM as the two neural measures, omits LORO; body+header run LORO→LOCO→ΔRDM. Reconcile (§26 Methods-order).
5. **Methods §4.6 L90** — 4-role block (basis + decode + encode + regularization justification). Split decode/encode into separate paragraphs; move justification.
6. **Methods terminology** — "nearest-neighbour matching" (L113/L119) vs "highest Pearson correlation" (L90) read as two rules; unify (§4).
7. **Methods L257** — fitted values β_s=6°, β_c=−42° stated in Methods (§23 results-in-methods) → defer to Results; two run-on sentences (~55–60w, semicolons) → split.
8. **Results Fig 3 title L46** — "interpolation is selectively impaired at hV4" overstates the deutan trend (p=0.063); body title (L34) already says "reduced". → "reduced".
9. **Results L187/L192** — "more HC-like in all four ROIs" + "restores" overstate: V1 effect REVERSES under voxel matching (d=−0.82). Qualify single-subject/descriptive; surface the V1 reversal at the claim, not 3 clauses later.
10. **Results L40** — group-result + per-hue vulnerability-profile in one paragraph (§7); split.
11. **Long/semicolon sentences** — Results L66, L207, L210; Methods L135.
12. **Intro P4 (L57)** — method+result+gap in one paragraph (§7); move gap sentence to P9. **Intro Q4 (L86)** "outperform" (Tier A) → baseline-relative phrasing.

### MINOR
- Intro: ABT "But" implicit (add one lexical turn); "examine"→"measure" (L62); gloss "realizable" once; "realistic" recurrences.
- Methods: L170 "cannot/can only" token; L66/L57 citation stacks; reproduce-only detail (L246/L213) could go to supplement.
- Results: L66 obs+interp mixed; "robust" bare adjective (L187, operationalized after — ok); L31 citation specificity.
- Discussion: L18 general claim on 2 primaries (review preferred); "near-control levels" operationalize once.

### CLEAN (verified across all sections)
- Project constraints: **no "grating"** (uniform disc), **no per-subject specificity claim** (descriptive-only enforced), **no "first/novel" overclaim**, **sub-09=protan / sub-10=deutan / sub-08=deutan** consistent (anonymized labels used).
- **Calibrated interpolation stats verified consistent** with canonical values (hV4 p=0.008; protan 0.017 / deutan 0.063 n.s.; per-hue none significant; V1 p=0.164). No overclaim in the interpolation paragraphs.
- Method-origin citations correct (brouwer2009/golub1979/kay2008/naselaris2011/machado2009/stockman2000/crawford1998).
- §4.6 decode/encode purpose split + §4.7 merged topic sentence read cleanly (structural work succeeded).

---

## B. Red-team (project) — top existential risks

1. **Per-person contribution confounded with subtype (N=1 per subtype).** "Individualized, not population-average" cannot be empirically separated with one deutan + one protan (individual ≡ subtype). Discussion L36 itself concedes the decisive experiment (several within one subtype) is undone. → **Reframe** to a constructive feasibility claim ("an individual's cortical geometry is invertible into a realizable filter") up-front in the Intro (free), OR new data (within-subtype N).
2. **The validated subject's target deficit is n.s.** Deutan LOCO p=0.063 (trend), per-hue all sub-threshold; the filter is built/validated on a deutan whose deficit is statistically unestablished. → **Reframe** to effect-size + direction-consistency (d_cc=−1.99), OR more runs on the deutan (most cost-effective new data; shores up both Results keystone and Discussion validation subject).
3. **"Beyond a deployed filter" = 1 of 4 indices, n=1.** RDM not restored (baseline closest to HC), behavior unrankable (p=0.84), winning ROI (V1) is a coverage artifact under voxel matching, shared rendering-pipeline confound, and "RDM isn't the bar" reads as post-hoc criterion. → **Reframe** to voxel-matched forward-tuning as an explicitly descriptive single primary; drop the general "beyond a deployed filter." Strong version needs protan 2nd session + matched-rendering comparator + behavioral 2AFC (new data).

### Method-level red-team (fixable by writing/disclosure)
- **Selection circularity**: the winning RDM-atom ROI (deutan V2 / protan V1) = the elevated-disparity ROI; both track the same CVD–HC deviation, so their "convergence" is not independent. → State this explicitly ("coincide by construction; not treated as independent corroboration"), or report per-ROI held-out test-loss + HC-pseudo-CVD ROI-coincidence rate.
- **Procrustes nesting**: Methods L70 describes across-run Procrustes; your own RT-2 log flagged across-run alignment as Fatal LORO leakage (resolved via nested Procrustes in Phase 2b). State in Methods that LORO/LOCO use train-fold-only (nested) Procrustes, else a reviewer finds your own "Fatal" unaddressed.
- **emery2021 sign-constraint tension**: Intro declines to replicate the cross-paradigm S-cone result but Methods L182 uses emery2021 to fix β_s sign. Disclose/justify the asymmetry.

---

## Next steps
- Writing fixes (A) → `/apply-draft` (Plan gate → 3-iteration). Recommended order: Discussion L27 + em-dash/Conclusion → Methods L16/L90/terminology/L257 → Results L46/L187/L40 → Intro P4/Q4.
- Red-team (B) reframes are partly editorial (do now) and partly data-gated (PI decision): items 1 & 3 largely survivable by disciplined reframing; item 2 is the single most cost-effective new-data investment (more deutan runs).
