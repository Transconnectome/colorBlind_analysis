# Revision Report — Methods (methods_v2.tex) — 2026-05-19
Scope: full file (`docs/PAPER/Methods/methods_v2.tex`, 254 lines).
Rules: ~/.claude/writing/academic_writing_rules.md (§19 vocab, §20 citations, §23 Methods, §26 checklist).
Plus: Nature reviewer #2 attack (10 issues).

---

## 1. Reverse outline (one sentence per paragraph)

### §Methods intro (L13–19)
- (¶1): Three-stage pipeline preview — neural characterization → distortion fit → pre-image inversion.

### §Participants (L22–31)
- (¶1): N=13 recruited, n=7 HC + n=2 CVD (sub-08 deutan, sub-09 protan) by Ishihara; 4 excluded; single-case framing declared.

### §Stimuli and task (L34–48)
- (¶1, L38–46): Eight CIELab hues, RSVP K-detection task, 6 runs, PsychoPy.
- (¶2, L48): CVD 2nd scan session for filter evaluation.

### §MRI acquisition and preprocessing (L51–60)
- (¶1, L55–56): 3T Siemens, oblique slices, scan parameters.
- (¶2, L58–60): BIDS, deface, FreeSurfer coreg, FSL FLIRT/FNIRT to MNI.

### §ROI definition and response estimation (L63–74)
- (¶1, L67): Wang atlas ROIs + voxel counts.
- (¶2, L69–72): Two-stage GLM, top-50% variance voxel selection, ridge per-trial estimation.
- (¶3, L74): Procrustes inter-run alignment.

### §Shared Response Model (L77–90)
- (¶1, L81–86): SRM definition + objective.
- (¶2, L88–90): HC-only training, CVD projection, k by LOSO.

### §Forward encoding model (L93–114, **Figure** included)
- (¶1, L97–101): Brouwer 2009 channel model + ridge-GCV weight estimation + decoding inversion + Appendix A pointer.

### §Evaluating color discrimination with cross-run decoding (L117–126)
- (¶1, L121–123): LORO cross-validation, 6 folds, 8-class exact accuracy.
- (¶2, L125–126): Group Mann–Whitney + within-ROI Crawford–Howell.

### §Evaluating color interpolation with cross-color decoding (L129–144)
- (¶1, L133–134): LOCO cross-validation, 8 hues held out, pooled 42-sample ridge.
- (¶2 §Adjacent accuracy, L136–138): Metric definition + label-permutation + C–H.
- (¶3 §Vulnerability profile, L140–144): 8-d vector definition + Spearman ρ + per-hue C–H + Hedges' d.

### §Between-group representational dissimilarity (L147–164)
- (¶1, L151–153): Two measures (disparity + ΔRDM).
- (¶2 §Pairwise disparity, L155–160): RDM definition, LOO HC reference, C–H upper-tail.
- (¶3 §Geometric deviation, L162–164): ΔRDM definition + Spearman correspondence with 2-comp.

### §Two-component distortion model (L167–203)
- (¶1, L171–179): δθ definition + parameter interpretation + retinal-family Appendix pointer.
- (¶2, L181–188): L_fit equation + simulated-vulnerability definition.
- (¶3 §Loss-term roles, L191–194): Per-term formula + weight justification.
- (¶4 §ROI scope, L197–199): hV4 only, justified by forward-encoder gate + biological prior.
- (¶5 §Per-subject distortion fit, L201–203): Grid search + argmin + HC LOO anchor pointer.

### §Stimulus-space filter (L206–214)
- (¶1, L210–212): Pre-image filter mapping T⁻¹.
- (¶2, L214): Brent's-method numerical inversion + 8/8 exact verification.

### §Behavioral concordance (L217–243)
- (¶1, L221): Behavioral same-day timing.
- (¶2 §JND, L223–227): Adaptive staircase + 8 pairs + hypo/hyper classification.
- (¶3 §Simulator–JND concordance, L229–232): Per-pair simulator shift vs hypo/hyper label.
- (¶4 §Behavioral color identification, L234): 8AFC, simulator-predicted-angle agreement.
- (¶5 §Filter evaluation session, L237–240): 2nd scan: 2-comp filter vs Windows control.
- (¶6 §[TODO] Planned validation, L242–243): Phase-3 2AFC pre-registered (TODO marker).

### §Reproducibility (L246–253)
- (¶1, L250–253): Python stack versions + seed + GitHub URL + data-on-request.

### Drift check vs Results
Methods order (LORO → LOCO → ΔRDM → 2-comp → filter → behavior) matches Results order ✓.

---

## 2. §19 Vocabulary

### Tier A — Banned (must fix or substantiate)
- **L199** — `cone-shift parameters fit on an encoder that cannot interpolate held-out colors` → §19A: replace `cannot` with quantified statement (`fails to interpolate held-out colors above the permutation null`).
- **L202** — `exhaustive grid over β_s ∈ [0°,50°] and β_c ∈ [−50°,50°] (26×51=1,326 cells)` → §19A: `exhaustive` is enumeration claim; specify what was enumerated (already done with explicit ranges and 1,326 cells). Recommended: drop `exhaustive` — the cell count is the enumeration.

### Tier B — Untestable verbs
- None detected.

### Tier C — Vague adjectives
- None detected. `significant` usages are paired with p-values (acceptable per §19C).

### Tier D — Self-praise
- None detected.

### Citation density
- No 5+ stacks. Maximum is 3 (Brouwer/Bannert/Kuriki at L199; Maes/Wells at L59). Acceptable.

---

## 3. §20 Citations

All citations method-origin or primary; specificity matches claim:

- L27 `\cite{ishihara1917}` — method origin (Ishihara plates) ✓
- L31 `\citeA{crawford1998}` — method origin (single-case t-test) ✓
- L42 `\cite{durnez2018}` — method origin (Neurodesign) ✓
- L46 `\cite{peirce2019}` — method origin (PsychoPy) ✓
- L56 `\cite{brouwer2009}` — could be re-examined; cited here for "posterior occipital slice prescription" but Brouwer 2009 is the encoding paper. Original retinotopic-slice reference may be more appropriate.
- L59 `\citeNP{maes1997, wells1996}` — primary refs for mutual-info coreg ✓
- L60 `\citeNP{jenkinson2002, andersson2007}` — primary refs for FLIRT/FNIRT ✓
- L67 `\cite{wang2015}` — primary Wang atlas ✓
- L69 `\cite{dale1999, brouwer2009, brouwer2013}` — method origin for two-stage GLM ✓
- L74 `\cite{gower1975}` — method origin for Procrustes ✓
- L81 `\citeNP{chen2015}` — method origin for SRM ✓
- L97 `\cite{brouwer2009}` — method origin for forward encoding ✓
- L99 `\citeNP{golub1979}` — method origin for GCV ✓
- L138 `\citeA{crawford1998}` — used appropriately ✓
- L144 `\cite{hedges1985}` — method origin for Hedges' d ✓
- L178 `\cite{brettel1997}`, `\cite{stockman2000}`, `\cite{emery2021}` — primary/method origins ✓
- L194 `\citeNP{kriegeskorte2008}` — method origin for RDM cosine ✓
- L199 `\citeNP{brouwer2009, bannert2018, kuriki2015}` — primary refs for hV4 hue hub ✓
- L224 `\cite{levitt1971}` — method origin for adaptive staircase ✓

No mismatches detected.

---

## 4. §23 Methods-section-specific violations

### "No results in Methods"
- **L197–199** — Methods reports the result `p = 0.044 at hV4 vs. NS at V1/V2/V3` inline to justify ROI choice. §23: "State *what was done*, not *what happened*." → Fix: move the gate numbers to Results, and in Methods only state "we fit at hV4 because it was the only ROI to clear the HC group LOCO permutation gate (Results §LOCO)".

### "Order matches Results"
- ✓ Confirmed by Drift check above.

### "Define every variable before later use"
- ✓ All symbols (V, k, F, W, C, X, θ, β_s, β_c, h, δθ, T) introduced before use.

### "Move secondary detail to appendix"
- ✓ GCV implementation, Machado/R+C alternatives, P2a/HC permutation all in Supp.

---

## 5. §26 Pre-submission checklist (Methods scope)

| Item | Status | Note |
|---|:-:|---|
| Reverse outline coherent | ✓ | each ¶ has one role |
| One-sentence contribution recoverable | ✓ | three-stage intro L16–19 |
| Numeric Δ has baseline + metric | ✓ | chance levels stated (1/8, 3/8) |
| "first/only/no X" cited or removed | ✗ | L199 "the only ROI" + "cannot interpolate" + L202 "exhaustive grid" |
| Untestable verbs replaced | ✓ | none |
| Vague adjectives operationalized | ✓ | none |
| No self-praise | ✓ | none |
| Topic sentence first | ✓ | subsection openers are topical |
| **No results in Methods** | ✗ | L199 reports p=0.044 inline |
| Methods order matches Results | ✓ | LORO→LOCO→ΔRDM→2-comp→filter |
| Citations match claim specificity | ✓ | all method-origin/primary |
| Pronouns unambiguous | ✓ | — |
| Reproducibility section present | ✓ | §Reproducibility |

---

## 6. Nature reviewer #2 attack (10 issues)

### Fatal (4)

**Issue 1 — ROI selection circularity.**
hV4 gate is single uncorrected p=0.044 across four ROIs (Bonferroni α=0.0125 fails). SUMMARY shows V1 has lower L_fit (0.159 vs 0.201 sub-08) and stronger perm_p (0.001 vs 0.004); V4 is adopted via gate that specifically discards the ROI with better fit — post-hoc selection rationalized as biological prior.
**Fix**: Report Bonferroni threshold explicitly; run pre-image + behavioral evaluation at V1 in parallel; let behavior — not the gate — differentiate.

**Issue 2 — HC FPR=100% kills C–H specificity.**
Methods uses C–H one-tailed α=0.05 (n=6); project records show HC FPR=100% under the same criterion. The HC LOO anchor has zero specificity by the authors' own diagnostics. Inferential framing of C–H results is statistically empty.
**Fix**: Report HC FPR=7/7 explicitly in Methods; reframe all C–H as descriptive percentiles; or use bootstrap interval that controls for the documented HC FPR.

**Issue 6 — Loss-development contamination by behavioral data.**
`future_phase2/CLAUDE.md §0.1` says P2a (color identification) served as a "selection guardrail" throughout loss development. Methods calls 8AFC a "post-hoc consistency check," but the internal record shows it shaped which loss survived. Loss is not pre-registered; same-subject behavioral data informed it.
**Fix**: Pre-register loss form + weights + selection criterion *before* Phase 3. Current 8AFC cannot serve as independent validation — partition from development set or replace with new data.

**Issue 10 — Windows accessibility filter is an inappropriate control.**
Filter evaluation compares 2-component filter vs "Windows accessibility filter" — but Windows Color Filters are *daltonization simulations for normal observers*, not corrective filters for CVD. Either it operates on already-collapsed CVD cone space (no effect) or further distorts. It is not a matched-difficulty correction comparator.
**Fix**: Replace with (a) identity control, (b) equal-amplitude angular rotation, or (c) Machado/R+C-derived filter matched in angular norm. Document which Windows mode was used.

### Serious (4)

**Issue 3 — Mann–Whitney on non-independent pairs.**
LORO group test uses M–W U on 21 HC–HC + 14 HC–CVD pairwise scores. Each HC contributes to ≤6 HC–HC and ≤2 HC–CVD pairs — observations not independent. M–W assumes independence; pair-level resampling inflates n_eff and deflates p.
**Fix**: Subject-level label permutation (permute CVD/HC label, not pairs); or linear mixed model with random subject effect.

**Issue 4 — 2-component identifiability not tested.**
2 free params + 4-term loss → effective dof ≠ 8-vs-2. No ablation: β_s-only, β_c-only, uniform-δθ null. Sub-08 V1 β_s hits grid boundary (50°) — at least one parameter unidentified within the search.
**Fix**: Report L_fit for (β_s=0, β̂_c), (β̂_s, β_c=0), uniform-δθ null. Extend V1 grid beyond [0,50] and verify interior optimum.

**Issue 5 — Encoder-channel/color phase mismatch absorbs distortion.**
6 cosine channels at 60° vs 8 colors at 45°. W is HC-fixed; CVD distortion enters only via C(θ+δθ). Encoder mis-specification cannot be falsified by CVD data — any 6-channel/8-color basis mismatch gets routed into (β_s, β_c).
**Fix**: Refit 6-channel W on CVD data; if W differs from HC-W, fixed-W conflates encoder mismatch with distortion. (β_s, β_c) interpretation requires this control.

**Issue 8 — Continuous-angle injectivity not proven.**
"8/8 exact" is bijectivity at training set. T(θ) = θ + δθ(θ) is continuous; for sub-08 (max shift 32° at cyan) T could become non-monotonic between training hues → pre-image fails or non-unique. Not verified.
**Fix**: Plot T(θ) continuously [0°, 360°) both subjects; verify dT/dθ > 0; report injective range. If non-monotonic, state filter is defined only at 8 DKL hues.

### Addressable (2)

**Issue 7 — sub-07 exclusion is pipeline-endogenous.**
sub-07 hV4 has 16 voxels after top-50% variance retention; exclusion criterion (no LOCO target file) is produced by the same pipeline. n=6 instead of n=7 shifts the C–H reference; no sensitivity analysis reported.
**Fix**: Report all stats with sub-07 imputed (group-mean hV4) and excluded; show conclusions invariant.

**Issue 9 — JND concordance underpowered + label timing unclear.**
6 pairs, ratio-based hypo/hyper, no multiple-comparison correction. Min one-tailed permutation p = 1/64 = 0.016 with 6 ordered pairs. Methods does not state achieved p nor whether hypo/hyper labels frozen *before* or *after* (β_s, β_c) fit.
**Fix**: State label-timing explicitly; if post-fit, concordance is circular and must be excluded.

---

## 7. Priority summary

Total issues: **14** (2 vocab + 1 Methods-style + 10 reviewer = 13 unique; +1 sub-07 sensitivity overlaps).

- **Fatal** (block submission): 4 reviewer + 1 §23 violation = **5**
  - L199 "no results in Methods" (move p=0.044 to Results)
  - Issue 1 ROI circularity (V1 vs V4)
  - Issue 2 HC FPR=100% framing
  - Issue 6 loss-development contamination
  - Issue 10 Windows filter control
- **Serious**: 4 reviewer + 2 vocab Tier A = **6**
  - Issue 3 M–W independence
  - Issue 4 identifiability ablation
  - Issue 5 encoder phase mismatch
  - Issue 8 continuous-angle injectivity
  - L199 "cannot interpolate" (rephrase)
  - L202 "exhaustive grid" (drop adjective)
- **Addressable**: **2** (Issue 7 sub-07 sensitivity; Issue 9 JND label timing)

### Recommended sequence

1. **Move L199 gate result to Results** (fast, mechanical, removes §23 violation).
2. **Add Bonferroni qualifier** to the ROI gate; explicitly report HC FPR=7/7 next to any C–H test result; reframe C–H from inferential to descriptive.
3. **Pre-register Phase-3 loss form**; explicitly state that current 8AFC analysis is post-hoc consistency only (already done in latest edits, may need re-emphasis).
4. **Replace Windows filter** with identity or rotation-matched control (or document mode + justify).
5. **Add ablation paragraph** in §Two-component (β_s-only / β_c-only / uniform-δθ baselines) — referenced to Supp table if numerical results are extensive.
6. **Verify continuous monotonicity** of T(θ) and add a Methods sentence stating injective range.
7. **Vocabulary fixes** L199 "cannot" / L202 "exhaustive" (1-line edits).
8. **Subject-level permutation** for the M–W group test (Methods edit + supp reanalysis).

For iterative fixes pass this report to `/apply-draft`.
