# Revision Report — docs/PAPER/main.tex (full paper) — 2026-07-14

Scope: Introduction/introduction_v2.tex, Results/results_v4.tex, Methods/methods_v2.tex, Discussion/discussion_v3.tex, Abstract (main.tex L70–72)
Rules: ~/.claude/writing/academic_writing_rules.md (§2, §7, §11, §19, §20, §22–§25, §26)
Method: deterministic grep scan (§19 Tier A–D, §2) + 4 per-section subagents (reverse outline, §20, §26) + naive-reader on abstract + bib-type cross-check + 3 factual verifications.

> **Overall**: the draft is already well-revised — §19 Tier A/D essentially clean, most Tier B/C hits are false positives (statistical `significant`, humble `exploratory`, nouns). The high-value issues are **3 concrete defects** (below, all confirmed) plus structural/altitude items, not vocabulary.

---

## 0. CONFIRMED DEFECTS (fix before any re-compile)

| # | File:line | Defect | Fix |
|---|---|---|---|
| **D1** | Results L90, L91, L107; Methods L237, L247; Supplementary_content L203, L204 | `$\langle N\rangle$` provisional-number placeholders **render as literal ⟨⟩ brackets in the compiled main.pdf**: ⟨100%⟩, ⟨41%⟩, ⟨87.7%⟩, N=⟨300⟩. These are unfinalized soft numbers. | Resolve each to its verified value and remove `\langle…\rangle`. Currently visible in the 65-pp PDF. |
| **D2** | Methods L56 | "Pairs spanned **three categories**: (i)…(ii)…(iii)…and **(iv)** one control pair." Four groups enumerated; 3+2+2+1 = 8 pairs (matches "eight hue pairs"), so the enumeration is correct and **"three" is wrong**. | "three categories" → "four categories". |
| **D3** | Methods L88 vs L101 | Symbol collision: `W_i ∈ ℝ^{V×k}` (SRM mapping) and `W ∈ ℝ^{F×V}` (channel-to-voxel encoding weights) one subsection apart (§6 notation). | Disambiguate, e.g. `W^{SRM}_i` vs `W^{enc}`. |

---

## 1. Reverse outline & drift

**Introduction (14 ¶, 5 blocks):** funnel intact (what CVD is → correction fails → neural cause → gaps → RQ/hypotheses). Documented expansion from pre-draft's 5 ¶ (header L4–35) — not accidental drift.

**Results (9 subsections):** logical chain sound. **DRIFT — missing logical rung:** pre-draft's intended ¶D payoff (the **LOCO↔behavior dissociation** — LOCO impairment predicts behavioral JND confusion where SRM-geometry does not, establishing LOCO as *the* functional filter target) is **absent from results_v4**. The prose jumps from deficit characterization to filter design without stating why the LOCO/geometry target is the behaviorally relevant one. Consider restoring one paragraph that makes this bridge explicit.

**Methods (16 subsections):** order broadly matches Results (LORO→LOCO→geometry→candidates→fit→selection→identifiability→filter→eval). Pre-draft outline is self-marked superseded (2026-05-12); expansions expected. One flag: **overview (L16) leads with LOCO and omits LORO**, whereas both the Methods body and Results lead with LORO (the discrimination precondition). Align the overview.

**Discussion (12 ¶):** follows §25 order (gap-filled → context → evaluation → limitations → impact). Limitations block (L41) is strong and complete (N=2, single-case, HC cohort, no bootstrap CI, LOCO-not-in-loss). **Prior-literature positioning is thin/scattered** (only boehm2014/emery2021/machado2009) — no consolidated "place against field" paragraph.

### Subsection [SPLIT?] flags
- **Results L98** "A common cortical model fits both CVD cases" — mixes parameter-fit results (L102–108, 114–115) with loss-atom *selection rationale* + ROI-agreement caveat (L110–112, a methodological argument). Consider moving the selection rationale out.
- **Discussion L34** — carries both the behavioral-evaluation verdict and the neural-evaluation verdict; split so each domain owns a paragraph.
- **Methods L152** — pairwise-disparity paragraph both defines the measure and argues the primary-vs-LOSO estimator choice; split the sensitivity rationale.
- **Intro block 3 (¶5–8)** — ¶8 (L71) shifts from *describing the neural cause* to *declaring the design hypothesis* (block-5 material surfacing early).

---

## 2. §19 Vocabulary (grep ground-truth)

- **Tier A (banned):** no true positives. All hits are false positives — "first family / first session" (enumeration), "we are not aware of" (the §19A-compliant weakened form), mathematical/negated "cannot"/"did not outperform", "exhaustive grid" (conventional term). Minor: Results L119 heading "…what behavior cannot" and Discussion L34 "unproven" could soften but are evidence-backed.
- **Tier B:** `exploratory` (Results L42/52/54/78; Discussion L18) = desirable humble framing, not the banned verb. `studies`/`study` = nouns (Intro L76/94). Real: Intro L65 "examine the distortion" → "characterize"; scattered `improve*` are mostly paired with deltas (OK). 
- **Tier C:** two hits — Results L68 `robust`, L136 `effective` — both need a "to what / by what measure" clause; verify full-line context. `significant` throughout = statistical (p-value/CI adjacent) → all FP.
- **Tier D (self-praise):** **none.** Clean.

---

## 3. §20 Citation specificity

No 5+ stacks anywhere (max 3, all justified). Three **suspects**, all the same class — a general/adjacent source licensing a *specific number*:

1. **Intro L51 — `stockman2000`** for "roughly 2–12 nm" anomalous cone displacement. `stockman2000` = Stockman & Sharpe 2000, *normal* L/M cone spectral sensitivities. Weak home for the anomalous-pigment displacement range. Verify the reference reports 2–12 nm, or cite an anomalous-pigment spectroscopy primary.
2. **Results L90 — `wilson2019`** for the 50% boundary-saturation rejection gate. `wilson2019` = Wilson & Collins, "Ten simple rules for computational modeling" (general best-practice). OK to cite for the *principle* (boundary-saturated fits signal misspecification) but not for the specific 50% threshold, which is a project choice. Reword to "following the general principle that…".
3. **Methods L199 — `stockman2000`** for θ_conf = 16° protan / 150° deutan "derived from Stockman & Sharpe cone fundamentals". §20 provenance honesty: if these axes were computed via Machado simulation or in-house rather than read from that reference, do not attribute them to it.

Non-issues confirmed: Intro L67 3× review stack (gegenfurtner/shapley/conway) for a general claim = correct; method-origins (brettel1997, machado2009, kriegeskorte2008, gower1975, golub1979, chen2015, levitt1971, crawford1998) all cite originals.

Also resolved: `fig:forward_tuning` (Results L218) is **not** dangling — defined in Supplementary/S16_filter_eval_design.tex:59.

---

## 4. §26 structural items

**Topic sentence not first (§8):** Intro ¶7 (L69) opens with a lead-in ("do more than lose sensitivity") before the topic ("They also compensate"); Results L64 opens with method before the ROI-difference finding. Both minor.

**Two-role paragraphs (§7):** Intro ¶8 (L71, interpretation + design-choice + roadmap) and ¶4 (L60, mechanism + result + gap); Results L68 (observation + method distinction + implication); Discussion L34; Methods L187 (equation + g-tutorial + DOF limitation). See [SPLIT?] list.

**Obs/interp/impl in one sentence (§9):** Results L68 (final sentence, 56 w), L93; Intro L69. Dense but mostly standard.

**§11 bare numbers (missing metric/baseline inline):** Results **L136 `f_{10°} < 0.30`** (metric undefined inline — add "fraction of recoveries within 10°"), **L107 "45° bin"** (grid-bin width not introduced), **L114 "top 5–8%"** (of-what ordering implicit, participants lumped). Discussion L21 |δθ| = 26.3°/16.2° (no reference scale for the reader). Elsewhere numeric context is well done (participant + ROI + HC baseline present).

**Pronouns (§3):** clean overall — participants named explicitly ("the deutan/protan participant"). Minor distant referents: Intro L60 "Their results", Discussion L29 "It rests on…".

---

## 5. Section-specific

**§22 Introduction — DOUBLE GAP (main issue):** the "But" pivot is stated twice with near-identical wording — **L60** ("What is missing is a filter derived from … the user's own neural color representation") and **L76 Gap 3** ("we are not aware of a corrective filter inverted from an individual's own cortical representation"). One should *motivate* (block 2), the other be the *formal gap* (block 4); both asserting the same missing-filter claim reads as redundancy, not escalation. Resolve.

**§23 Methods — RESULTS LEAKED INTO METHODS:** L16 overview ("**characterized** each participant's **deficit**", "LOCO **yielded** a vulnerability **profile**") and L199 ("these components **span the axes of distortion identified by** the neural analysis") state outcomes inside method/motivation. Reframe motivation as a question/hypothesis, not its answer. Filter-eval methods (L270–274) are clean.
- Undefined symbols/jargon at first use: `C` (channel design matrix, used L106/L221 never defined); "atom / loss atom / atom factories" (L237+); + the `W` collision (D3).
- Detail-altitude → supplement: grid cell count (L230), Brent tolerance <0.001° (L263), n=140 + noise model + pass-thresholds (L254).

**§24 Results:** missing LOCO↔behavior rung (§1 drift). `fig:filter_eval` caption asserts two findings across 6 panels (interpolation differs AND geometry not restored) — two logical steps in one figure; acceptable as a summary figure, flagged.

**§25 Discussion — RESULTS RE-REPORTED (not "new" — REDUNDANT):** L18, L23–25, L29, L31, L34 re-state inferential stats that already live in Results (p=0.040, 0.007, 0.008; 6°,−42°; 0/6 FDR; g≈3; 0.23→0.31). Cross-checked against Results scan: these numbers **are** in Results, so this is §25 altitude/redundancy (interpret, don't re-derive), **not** a literal "new results" violation. Reduce to qualitative references with pointers. Mild overclaim: L46 "template … beyond color vision" extrapolates from N=1/subtype — soften to "may offer".

---

## 6. Abstract (naive-reader, zero-domain ML reader)

Reader reconstructed the gist correctly but flagged:
- **No quantitative anchor.** Abstract is entirely qualitative ("intact", "inconsistent", "did not reach the healthy reference"). Consider adding 1–2 numbers for the *positive, quantified* part (distortion characterization / model fit), while keeping the (genuinely null) filter-efficacy result qualitative. Judgment call — do not manufacture a positive efficacy number.
- **Undefined jargon stacked in the core method sentence:** "compact two-component cortical model", "inverted", "stimulus-space", "exact for every displayed hue", "cortical hue geometry", "reads out", "categorical color decodability" — all undefined; the reader lost the thread precisely at the two-component/inversion sentence.
- **Redundant closing:** final sentence largely restates sentence 2; "the chromatic signal was intact" restates "not reduced in overall signal".

---

## 7. §2 Long sentences (split candidates)

| File:line | ~words | Trigger |
|---|---|---|
| Results L106 | ~62 | semicolon + "although" chain |
| Results L91 | ~58 | semicolon + 3 clauses |
| Results L68 | ~56 | semicolon + 2 em-dashes |
| Results L192 | ~55 | semicolon (deviant-pairs / mean|JND−HC|) |
| Methods L254 | ~52 | semicolon + 3 clauses |
| Methods L187 | ~48 | **3 semicolons** (g-regimes → make a list) |
| Discussion L29 | ~45 | colon + comma-whereas, 3 clauses |
| Methods L132, L237; Discussion L15, L31, L41; Intro L60 | 34–44 | em-dash/semicolon appositive |

Intro prose is otherwise well-controlled (nothing egregiously >45 w); the recurring pattern is *claim-density per paragraph* (Intro L60, L76), not raw sentence length.

---

## 8. Priority summary

**Total distinct issues: ~30.**

- **Fatal (blocks clean submission / factual / visible in PDF):** 3 — D1 placeholder brackets (7 sites), D2 "three→four" count, D3 `W` collision.
- **Serious:** ~9 — Intro double-gap (L60/L76); Results missing LOCO↔behavior rung; §23 results-in-Methods (L16, L199); undefined `C`/"atom" symbols; 3 citation-provenance suspects (stockman2000 ×2, wilson2019); Discussion results-redundancy (L18/23–25/29/31/34); abstract jargon+no-anchor.
- **Minor:** ~18 — long sentences (§7), topic-sentence lead-ins, two-role paragraphs, detail-altitude to supplement, `f_10°`/"45° bin" inline gloss, Tier C `robust`/`effective`, Discussion L46 soften, prior-literature positioning paragraph.

**Recommended sequence:**
1. **D1–D3** (mechanical, must precede any re-compile).
2. Resolve Intro double-gap (L60 vs L76) — decide which sentence motivates vs states the gap.
3. Restore the LOCO↔behavior rung in Results (or explicitly cut it from the story if descoped).
4. De-leak Methods (L16, L199 → question form) + define `C`/"atom".
5. Reword the 3 citation-provenance lines (or verify sources).
6. Trim Discussion re-reported stats to pointers; soften L46.
7. Abstract: add 1–2 characterization numbers, define/limit core-method jargon, cut redundant closing.
8. Long-sentence split pass (§7 table) — low-risk polish, do last.

For iterative fixes, pass this report to `/apply-draft`.
