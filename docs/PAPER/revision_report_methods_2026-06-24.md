# Revision Report — Methods (methods_v2.tex)

Date: 2026-06-24
Target: `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/docs/PAPER/Methods/methods_v2.tex`
Rules: `~/.claude/writing/academic_writing_rules.md` (§19, §20, §23, §26)
Reference for §23 order: `Results/results_v4.tex`

Scope note: Report only — no `.tex` edits made. All issues carry file:line + quoted text.

---

## Summary

- **Fatal: 1**
- **Serious: 4**
- **Minor: 9**

Top 5 (one line each):
1. `methods_v2.tex:16` → overview lists **LOCO before LORO**, contradicting body order and Results order (§23 drift) — reorder to LORO→LOCO.
2. `methods_v2.tex:29` vs `:16` → figure `\label{fig:paradigm}` but text `\ref{fig:pipeline}` for the same Fig 1 — broken cross-reference; reconcile labels.
3. `methods_v2.tex:182` → `\citeNP{emery2021}` used to fix a **sign constraint** ($\beta_s\ge0$); verify the cited paper supports this physiological claim, else soften (§20 method/empirical match).
4. `methods_v2.tex:170` → "**cannot** account for distortions in other color directions" — Tier A `cannot`; rephrase to "fails under [stated assumption]".
5. `methods_v2.tex:220,230` → `$N = \langle300\rangle$` literal angle-bracket placeholder in two places — unresolved macro/placeholder leaking into prose.

---

## 1. Reverse outline (one sentence per paragraph, as written)

| Loc | Subsection | One-sentence summary | Flag |
|---|---|---|---|
| L16 | (overview) | Three-stage analysis: neural deficit measures → model fit → invert to filter → evaluate. | §23 order drift (LOCO before LORO; ΔRDM ordering) |
| L37 | Participants | 13 recruited, 7 HC / 2 CVD by Ishihara, single-case Crawford–Howell inference. | OK |
| L44–46 | Stimuli & task | 8 isoluminant L*a*b* hues + gray, RSVP K-detection, 6 runs, PsychoPy. | OK (grating-free, see guardrail check) |
| L48 | (stimuli, sess.) | All did JND in scan session; deutan added a 2nd filter session. | Two-role risk: belongs with Behavioral, not Stimuli (§7) |
| L55–57 | MRI acq/preproc | Siemens 3T, occipital coverage; BIDS, coreg, MNI normalization. | OK |
| L64 | ROI def | V1–hV4 from Wang atlas >50%, voxel counts. | OK |
| L66–68 | Response est. | Two-stage GLM: FIR HRF, top-50% variance voxels, ridge amplitudes 6×8×V. | OK |
| L70 | Procrustes | Runs 2–6 aligned to run 1 by orthogonal rotation. | OK |
| L77–83 | SRM | HC-only SRM, CVD projected by SVD, k per ROI by LOSO. | OK |
| L90 | Forward encoding | Shared FE model: 6 squared-cosine channels, ridge-GCV W, correlation decode. | OK |
| L110–112 | LORO | LORO 8-class exact accuracy + Mann–Whitney cross-subject + Crawford–Howell. | OK |
| L119–125 | LOCO | LOCO adjacent accuracy + vulnerability profile + per-hue tests. | OK |
| L132–138 | RDM | Pairwise disparity (LOO/LOSO references) + ΔRDM model correspondence. | Two measures — borderline two-role but signposted (OK) |
| L145–182 | Candidate models | R+C (retinal+gain) and 2-comp (S-cone + confusion axis) defined. | OK |
| L189–213 | Inverse fitting | Three losses (Lγ, L_RDM, L_LOCO) + grid search. | OK |
| L220–230 | Parameter selection | Three-gate selection on HC resample + LOO held-out loss. | Placeholder `⟨300⟩` leaks |
| L237 | Identifiability | Four pre-specified recovery/null checks, BH-FDR over 6 tests. | OK |
| L244–246 | Filter | Pre-image of fitted transform by Brent root-finding. | OK |
| L254–257 | Behavioral | JND staircases + deutan filter-evaluation session (personalized vs deployed). | L257 very long single paragraph; needs ≥2 sentences to summarize → split (§7/§26) |
| L264 | Reproducibility | Python/seed/code-availability statement. | OK |

**Reverse-outline drift:** The overview (L16) narrates **LOCO → ΔRDM → models → filter**, but both the Methods body and `results_v4.tex` run **LORO → LOCO → RDM → R+C → 2-comp → … → filter**. The overview's "First, two neural measures characterized... (LOCO... and ΔRDM...)" silently drops LORO and reverses the first two analyses. This is the principal structural defect.

---

## 2. §19 Vocabulary scan (Tier A/B/C/D)

| Loc | Tier | Quote | Issue | Fix direction |
|---|---|---|---|---|
| L170 | **A** | "R+C can only displace colors along this single direction and **cannot** account for distortions in other color directions." | `cannot` (absolute). | "fails to account for distortions off this axis" or "is, by construction, confined to this single direction". Frame as structural consequence, not impossibility. |
| L173 | B | "We **propose** a parametric model..." | `propose` is acceptable for introducing a model; borderline. | Acceptable; if tightening, "We define a parametric model". No action required. |
| L84/L135 | — | "to **avoid** circular inference" / "To **control for** this asymmetry" | Both concrete and testable. | False positive — keep. |
| L257 | C | "**robustness** was assessed by leave-one-run separation..." | `robustness` — but the perturbation set (leave-one-run, baseline voxel set) is named in the same sentence. | Borderline OK; §19 Tier C satisfied because the perturbation is operationalized inline. Keep. |
| L257 | C | "the **deployed** comparator" / "**personalized** filter" | Defined-term labels, not vague adjectives. | False positive — keep (terms are operationalized). |

**Tier D self-praise:** none found. No "elegant / principled / clean / unified / surprising". Pass.

**Tier B untestable verbs:** No "study / explore / investigate / understand" in procedural prose. The Methods correctly use "estimated / computed / decoded / assessed / compared". Pass overall except the single Tier A `cannot` above.

---

## 3. §20 Citation specificity audit

| Loc | Citation(s) | Claim | Assessment |
|---|---|---|---|
| L182 | `\citeNP{emery2021}` | "$\beta_s$ is constrained to $\beta_s\ge0$ because CVD perceptual errors concentrate near the S-cone confusion loci, which fixes the sign". | **Suspect.** A single primary paper is asked to license a sign constraint on a model parameter. Confirm Emery 2021 actually reports S-cone-locus error concentration *with directional sign*; if it only illustrates clustering, this is over-attribution (§20 "support vs illustrate"). Mark for verification against source. |
| L162 | `\cite{boehm2014,tregillus2021}` | cortical compensation gain `g`. | OK — two primaries for a specific mechanism claim; not a 5+ stack. |
| L66 | `\cite{dale1999, brouwer2009, brouwer2013}` | two-stage GLM origin. | OK — method-origin stack of 3, each load-bearing (Dale=GLM, Brouwer=this paradigm's two-stage variant). Acceptable, not a gratuitous 5+ stack. |
| L57 | `\citeNP{wells1996, maes1997}` | mutual-information coregistration origin. | OK — method origin, correct (these are the MI-registration originals). |
| L90/L97 | `\citeNP{brouwer2009}` (forward model) | FE model origin. | OK — original-paper citation for the channel model. Correct per §20 method-origin rule. |
| L170 | `\cite{machado2009}` | "cone-spectral shift at the retinal level". | OK — primary for the simulation method used. |
| L162 | "**The prevailing account** attributes CVD color distortion to a cone-spectral shift" cites only `\cite{machado2009}` | A *general/prevailing-account* statement is supported by a single primary (the simulation paper). | **Minor (§20).** A "prevailing account" framing wants a review or 2nd anchor, not one method paper. Consider adding a review or rephrasing to "A retinal-shift account, implemented by Machado et al. (2009),...". |
| L37 | `\cite{ishihara1917}` | Ishihara test. | OK — original. |

No other 5+ stacks detected.

---

## 4. §26 Pre-Submission Checklist

### Reverse outline
- [FAIL] One-sentence-per-paragraph narrates the paper — **L16 overview reverses LOCO/LORO and omits LORO**, so the opening does not narrate the actual body. (Fatal — see §23 below.)
- [FAIL] L257 (Behavioral filter-evaluation paragraph) needs ≥2 sentences to summarize (it carries: 2nd session design, two-filter definition, comparator rationale, neural recompute list, effect-size choice, robustness, behavioral repeat, and an interpretive caveat). Split per §7. (Serious)
- [PASS] All other paragraphs are single-role.

### Claims
- [PASS] Central contribution recoverable (fit-and-invert personalized filter).
- [N/A] Numeric Δ baseline/metric — Methods states procedures, not results; numbers present are parameters (audited in §5 below).
- [FAIL] "first / only / no X" — none of those, **but** L170 `cannot` triggers the same Tier-A rule (absolute claim without "under [assumption]"). (Serious)
- [PASS] Untestable verbs (Tier B) — none in procedural prose.
- [PASS] Vague adjectives — operationalized inline where used.
- [PASS] No self-praise (Tier D).

### Citations
- [PASS] General vs primary mostly correct; one borderline (L162 "prevailing account" on single primary — Minor).
- [FAIL/verify] L182 `emery2021` sign-constraint attribution — verify against source (Serious).
- [PASS] No unjustified 5+ stacks.

### Structure
- [PASS] One role per paragraph (except L257, flagged).
- [PASS] First sentence = topic sentence in each subsection.
- [PASS] Pronouns — antecedents unambiguous throughout.
- [PASS] Terminology consistent (LORO/LOCO/ΔRDM/2-comp used uniformly).
- [N/A] Observation/interpretation/implication separation — Methods, minimal interpretation.

### Section-by-section
- [N/A] Abstract / Intro / Discussion (not this file).
- [**FAIL**] **Methods order matches Results order (§23)** — see below. (Fatal)
- [PASS] Figures self-contained; captions state takeaway (Figs 1, 2, pipeline).

### Final pass
- [PASS] Filler phrases — none egregious.
- [PASS] Negatives-with-positive-equivalents — acceptable.
- [PASS] Nominalizations — converted to verbs in procedure descriptions.
- [PASS] Passive/active — passive is appropriate convention for Methods here.

---

## 4a. §23 Methods-order vs Results-order (detailed)

**Results order** (`results_v4.tex`): LORO → LOCO → geometry(RDM) → R+C-insufficient → 2-comp → neural-role → identifiability → filter → filter-eval.

**Methods body order**: Participants/Stimuli/MRI/ROI/SRM/FE (setup) → LORO → LOCO → RDM → Candidates(R+C, 2-comp) → Inverse-fitting → Parameter-selection → Identifiability → Filter → Behavioral.

The **body order matches Results** (a reader moving Methods→Results does not jump back). The failure is **only in the overview paragraph (L16)**:

- L16: *"First, two neural measures characterized each CVD participant's hue-processing deficit: leave-one-color-out (LOCO) decoding... and the between-group RDM difference (ΔRDM)..."*
- This (a) omits LORO entirely from the stage-1 description, and (b) leads with LOCO though both body and Results lead with LORO.

**Direction:** Rewrite L16 stage-1 to read LORO (discrimination preserved) → LOCO (interpolation impaired) → ΔRDM (geometry), matching the body and Results narrative. This is the single Fatal item.

---

## 5. Methods-specific: reproducibility detail + unitless/baseline parameters

| Loc | Issue | Severity | Fix direction |
|---|---|---|---|
| L220, L230 | `$N = \langle300\rangle$` — literal `\langle...\rangle` angle brackets around 300 in two places; reads as an unresolved placeholder, not a value. | **Serious** | Replace with the actual resample count `N = 300` (or whatever final value). Remove `\langle \rangle`. |
| L29 vs L16 | Fig 1 declares `\label{fig:paradigm}` (L29) but L16 references `Figure~\ref{fig:pipeline}` for "this fit-and-invert workflow". `fig:pipeline` is the **Fig 5** label (L158). L16 likely should ref `fig:pipeline` correctly only if that figure shows the workflow — but L16 also says "Figure~\ref{fig:pipeline} summarizes this fit-and-invert workflow" while Fig 1 (paradigm) is the pipeline overview. Cross-reference/label mismatch. | **Serious** | Verify which figure L16 intends. If the overview pipeline is Fig 1, ref `fig:paradigm`; the workflow schematic is Fig 5 (`fig:pipeline`). Ensure each `\ref` points to the intended float. |
| L48 | Session/JND sentence sits inside **Stimuli and task** but describes the behavioral protocol; duplicated/forward-referenced at L254–257. | Minor (§7) | Move to Behavioral tasks, or keep only a one-line pointer. |
| L55 | "FA $75^\circ$" — flip angle stated; OK. "TR 1.5 s, TE 30 ms" — units present. | PASS | — |
| L122 | "chance level under a uniform random predictor $= 3/8 = 0.375$" — baseline given. | PASS | Good (units + baseline). |
| L246 | "convergence tolerance of $< 0.001^\circ$" — unit present. | PASS | — |
| L152, L182 | $\theta_{\rm conf} = 16^\circ$ protan, $150^\circ$ deutan — stated with units; but **derivation source** ("derived from Stockman & Sharpe cone fundamentals") is asserted without procedure. | Minor | Add one line or supplement pointer on *how* the confusion-axis angle is computed from the LMS fundamentals (reproducibility). |
| L220 | "5-train/2-test HC resample" and "strict 7-fold HC LOO" — the resample N and fold logic are clear, but "the same atom factories" is jargon undefined in-text. | Minor | Define "atom factory" once or replace with "loss-atom generators". |
| L223 | "signed Cohen's $d \ge +0.5$" — threshold with sign; baseline (HC LOO distribution) named. | PASS | — |
| L226 | "$\ge 50\%$ of resample solutions saturated the grid boundary" — threshold + criterion given. | PASS | — |
| L237 | "$f_{10^\circ}\ge 0.5$, $|\text{bias}|<10^\circ$", "$n=140$ per candidate", "$N=1000$" permutations — all quantified with units. | PASS | Good reproducibility detail. |
| L257 | "intensity the participant self-tuned" — the macOS Color Filter intensity value is **not recorded**; not reproducible. | Minor | Report the self-tuned intensity value (or state it was not logged as a limitation). |
| L264 | Software versions + seed=42 + repo URL present. | PASS | Strong. |

---

## 6. Guardrail checks (project CLAUDE.md)

- **Grating vs uniform disc (L65–66 guardrail):** The user-cited line numbers have shifted, but the content is **compliant**. L44–46 describe "a uniform circular chromatic patch (a colored disc, 1.5 s per stimulus)" and never use "grating", "RadialStim", or "sinusoid". **PASS** — no grating language anywhere in the file.
- **No specificity claims as selection criterion:** L230 explicitly states "The HC false-positive rate was not itself used as a selection criterion; it is reported descriptively." **PASS** — consistent with the no-specificity-claim policy.
- **FE-6 uniform basis (Phase 2):** L90 and L97 specify "$F=6$" half-wave rectified squared-cosine channels at $60^\circ$ spacing (uniform). **PASS** — matches the FE-6 uniform-basis requirement.
- **Anti-overstatement:** Single-case framing is maintained (L37, L257 "single deutan case", "descriptive"). The only overstatement is the L170 `cannot` (flagged §2). Otherwise **PASS**.

---

## Issue ledger (severity-sorted)

**Fatal (1)**
- F1. L16 — overview stage order contradicts body + Results (LOCO-before-LORO, LORO omitted). Reorder to LORO→LOCO→ΔRDM.

**Serious (4)**
- S1. L29/L16 — Fig 1 label `fig:paradigm` vs `\ref{fig:pipeline}` mismatch; resolve cross-reference targets.
- S2. L182 — `emery2021` sign-constraint attribution; verify source supports the directional claim or soften.
- S3. L170 — Tier-A `cannot`; restate as structural confinement under the model.
- S4. L220/L230 — `\langle300\rangle` placeholder leaking; insert final N.

**Minor (9)**
- M1. L162 — "prevailing account" on single primary; add review/anchor or rephrase.
- M2. L48 — behavioral session sentence misplaced in Stimuli (§7); move/point.
- M3. L257 — paragraph carries 8 distinct sub-points; split per §7.
- M4. L257 — macOS filter self-tuned intensity not recorded; report or flag.
- M5. L152/L182 — confusion-axis angle derivation from LMS not described; add supplement pointer.
- M6. L220 — "atom factories" jargon undefined; define or rename.
- M7. L173 — `propose` borderline (acceptable; optional tighten to "define").
- M8. L16 — "this fit-and-invert workflow" phrasing fine, but check it lands on correct figure (ties to S1).
- M9. Header comment L8 dates loss change to 2026-05-14; confirm current production loss (per MEMORY: v6 PCA-RDM + behavioral γ) matches what L189–213 describe — possible stale methodology block. (Verify against future_phase2 CLAUDE.md before submission.)
