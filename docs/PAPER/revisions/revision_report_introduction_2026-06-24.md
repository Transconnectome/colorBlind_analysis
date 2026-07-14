# Revision Report — Introduction (introduction_v2.tex)

Date: 2026-06-24
Target: `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/docs/PAPER/Introduction/introduction_v2.tex`
Rules: `~/.claude/writing/academic_writing_rules.md` §§7, 19, 20, 22, 26
Mode: report only — no .tex edits made.

---

## 1. Reverse outline (one sentence per paragraph, as written)

| Block | Lines | As-written sentence | Needs 2 sentences (§7)? |
|---|---|---|---|
| Intro-1a | 47–48 | CVD arises from an L/M cone opsin shift that weakens but does not abolish the L–M cone-opponent signal. | No |
| Intro-1b | 50 | The weakened signal produces a peripheral phenotype (poor red–green discrimination, confusions, raised thresholds), screened by Ishihara and quantified by psychophysics. | No |
| Intro-2a | 55 | Existing correction methods (hardware notch filters; software simulation/Daltonization) all optimize against a population-average retina and apply one transform to every user. | No |
| Intro-2b | 57 | Personalization attempts tune a retinal cone-shift to appearance reports, hit a ceiling because the phenotype varies within a category, and what is missing is a filter grounded in the user's own neural color geometry. | **Borderline** — packs (a) prior personalization route, (b) two empirical ceiling results, (c) the gap statement. See §7 note below. |
| Intro-3a | 62 | CVD leaves cortical color machinery intact but with a structurally distorted (not absent) representation, making cortex the natural level to examine the distortion. | No |
| Intro-3b | 64 | Cortical color is distributed/hierarchical, with hV4 a hue population-code hub, and the code is shared enough to be read out across people. | No |
| Intro-3c | 66 | Anomalous trichromats also compensate cortically (adaptation, post-receptoral gain, blue–yellow realignment), evidence that motivates but does not establish a cortical locus and is not replicated here. | No |
| Intro-3d | 68 | Because compensation lives in cortex, a retina/appearance-calibrated correction acts at the wrong level, so we take the individual's cortical readout as the reference — a design hypothesis the paper tests. | No |
| Intro-4 | 73 | Three gaps remain: (1) individual CVD cortical geometry uncharacterized, (2) existing CVD measures (magnitude, accuracy) miss continuous relational structure, (3) no filter inverted from an individual's own cortical representation. | **Yes** — three distinct gaps; one summary sentence cannot cover it. This is intentional enumeration, not a §7 violation (see note). |
| Intro-5a | 78 | We ask whether individual cortical color geometry can be the reference for personalized correction, testing two CVD adults (one per subtype) against HC, with the protan case exploratory. | No |
| Intro-5b | 80 | A stimulus-space filter is warranted only when colors stay neurally distinguishable yet the continuous hue arrangement is distorted. | No |
| Intro-5c (Q list) | 82–87 | Four questions: Describe, Summarize, Correct, Validate. | N/A (list) |
| Intro-5d | 89 | We expect selective impairment of continuous hue arrangement (largest blue-to-magenta), capture by a few parameters, and a realizable inverse filter. | No |
| Intro-5e | 91 | The steps yield a single-observer filter (cortical input, fitted parameters, stimulus-shift output) at the level any correction must act. | No |

### §7 / drift notes
- **L57 (Intro-2b)** mixes three roles (prior-approach description + two empirical results + the gap-thesis "what is missing"). Topic sentence is about the personalization *route*; the paragraph then drifts into a gap statement that is later re-stated at L68 and L73 (Gap 3) and L78. Candidate for a clean split: route + ceiling evidence in one paragraph, gap thesis deferred to Intro-4. Flag, do not auto-fix.
- **L73 (Intro-4)** legitimately needs three sentences but is structured as an explicit `(Gap 1)…(Gap 2)…(Gap 3)` enumeration, so it reads as one role ("the gaps"). Acceptable. Not a violation.
- **Outline drift vs pre_draft (§5, lines 86–90)**: The pre-draft outline had **5 Intro paragraphs** (broad / existing tech / cortical compensation / gap ABT / approach+preview). The current draft expands to ~11 paragraphs + Q-list. The expansion is deliberate (per header note 2026-06-11) and the funnel order is preserved. Two substantive drifts:
  1. Pre-draft ¶5 promised "**validated by JND**" / "decompose into retinal+cortical two components" as an explicit **preview of approach + findings** (§22c "connect forward"). The current draft **removes all method/result preview** (Q4 explicitly reserves efficacy for Phase 3; no "we find" anywhere). This is an intentional editorial choice (header L22–24) but it leaves the Intro with **no findings preview** — see §22 finding below and naive-reader flag (a).
  2. Pre-draft ¶3 cited Tregillus 2021 + Emery 2021 for cortical compensation; current draft keeps these and **adds** basim2025, webster2015, boehm2014 — consistent, no drift.

---

## 2. §19 Vocabulary scan

Method: each candidate filtered with ±1 sentence context. Statistics-context "significant" etc. passed. Hits below are genuine.

### Tier A — banned without explicit evidence

| Line | Quote | Issue | Recommended fix |
|---|---|---|---|
| L73 | "we are not aware of a corrective filter inverted from an individual's own cortical representation" | This is a softened "no X exists" claim. §19 allows "we found no [X] in [searched venues, year range]". As phrased it has **no scoped search** (which databases, what years). Borderline-compliant ("we are not aware" is the recommended hedge) but the scope qualifier is missing. | Add scope: "Across studies that analyze multivoxel color patterns, we found no corrective filter inverted from an individual's own cortical representation (search of [venues], [year range])." Respects CLAUDE.md anti-"first" policy. |
| L73 | "is untested" ("Whether such a high-dimensional signal can be turned into a realizable, individualized correction is untested.") | "untested" is an absolute over the whole literature, same class as "no X exists". | Soften/scope: "has not, to our knowledge, been demonstrated" or tie to the same scoped search. |

No instances of `the first`, `novel`, `cannot`, `impossible`, `always`, `never`, `proves`, `comprehensive`, `state-of-the-art`, `outperforms` (unqualified). **Note**: L86 Q4 uses "outperform a deployed accessibility filter" — this is a *question/hypothesis* with a named baseline (deployed accessibility filter), not an unqualified claim. Passes, but the metric is unnamed (see §11/Tier-C note below).

### Tier B — untestable verbs

| Line | Quote | Issue | Recommended fix |
|---|---|---|---|
| — | "characterize" (L78, L73) | §19 lists `characterize` as the *allowed replacement* for `explore`. Passes. | none |
| — | "examine" (L62 "the natural level at which to examine the distortion") | Tier B flags `examine` → `analyze/model/compare`. Here it is used in a framing sentence ("level at which to examine"), not as the study's operational verb. Low priority; acceptable in a motivational sentence. | optional: "the natural level at which to measure the distortion" |

No `improve` (the empirical "improved discrimination" at L57 reports a study *result*, not the paper's own contribution — passes §19 Tier B which targets the authors' claims), no `study/explore/understand/investigate/address/consider` as the paper's own contribution verbs.

### Tier C — vague adjectives needing inline operationalization

| Line | Quote | Issue | Recommended fix |
|---|---|---|---|
| L85, L89 | "realizable, individualized filter" / "realizable, individualized correction" | "realizable" is undefined here (realizable = invertible with bounded error? physically displayable on the monitor gamut?). Used 3× (L85, L86 context, L89). | Operationalize once at first use: e.g. "realizable (an exact stimulus-space pre-image within display gamut)". |
| L57, L62 | "structurally distorted" / "structured distortion" | "structural/structured" is doing load-bearing thesis work but is never operationalized in the Intro. The reader (and naive-reader) cannot tell what "structure" means. Acceptable to leave undefined in a funnel Intro **if** Q1 (L83) operationalizes it — which it does ("categorical discrimination preserved but continuous arrangement impaired"). Marginal pass; flag for awareness. | none required; ensure Q1 stays adjacent. |
| L86 | "outperform a deployed accessibility filter" | §19 Tier C "effective" pattern — comparison without metric. Q4 names baseline but not the metric (HC-likeness? neural distance?). | "outperform a deployed accessibility filter on [cortical-distance-to-HC]". |

No `faithful`, `meaningful`, `robust`, `principled`, `accurate`. "significant"/"significantly" do **not** appear (good — de-jargon pass removed p-values). "markedly" (L57 "varies markedly") is a mild Tier-C intensifier; low priority — backed by the bosten2019 citation, acceptable.

### Tier D — self-praise
None found. No `elegant`, `principled`, `clean`, `unified`, `important`, `surprising`. Clean.

---

## 3. §20 Citation specificity audit

All judgments below are **"suspect" flags** for user adjudication, not directives.

| Line | Citation(s) | Claim type | Suspect issue |
|---|---|---|---|
| L48 | `stockman2000` for "deviant cone peak displaced by roughly 2–12 nm" | Specific empirical quantity | Stockman & Sharpe 2000 is a cone-fundamentals/spectral-sensitivity paper; the 2–12 nm anomalous-pigment displacement range is more naturally a Neitz/opsin-genetics primary result. **Verify** Stockman 2000 itself states the 2–12 nm range; if it only provides the normal fundamentals, pair with or replace by the opsin-shift primary (e.g. neitz2011, already cited L48). |
| L50 | `ishihara1917` for "The Ishihara test screens for the resulting red–green confusions" | Method origin | Correct — original source. Pass. |
| L50 | `boehm2014, bosten2019` for "quantified by threshold psychophysics" | General method statement | Two primaries for a general statement. Borderline; bosten2019 (review-like) likely suffices. Minor. |
| L55 | `brettel1997`, `machado2009`, `akalin2025` | Method origin (each) | Each cited at its own method — correct mapping. Pass. |
| L57 | `bosten2019` for "phenotype varies markedly even within one diagnostic category" | General domain claim | bosten2019 is review-grade; appropriate. Pass. |
| L57 | `patterson2022` for "improved discrimination for only one of two consumer products" | Specific empirical finding | Primary, specific — correct. **But** naive-reader flags no effect size/N; consider adding the magnitude. Citation type OK. |
| L57 | `somers2024` for "shift appearance … while leaving generalized discrimination largely unchanged" | Specific empirical finding | Primary — correct mapping. Pass. |
| L64 | `gegenfurtner2003, shapley2011, conway2018` for "distributed, hierarchical computation" | General domain statement | Three reviews for a general statement — appropriate (well-established fact, representative reviews). Not a 5+ stack. Pass. |
| L64 | `brouwer2009` cited **twice** in one paragraph (population code; continuous reconstruction) | Specific empirical | Both are genuine brouwer2009 results (population code + reconstruction). Acceptable but consider consolidating to one citation instance. Minor. |
| L64 | `parkes2009, kuriki2015` for "hue-selective responses to intermediate colors … as early as V1" | Specific empirical | Primary pair — correct. Consistent with MEMORY.md framing. Pass. |
| L64 | `bannert2025` for "read out in a common space … validated in healthy observers" | Specific empirical (method) | Primary — correct. Pass. |
| L66 | `boehm2014, webster2015, tregillus2021` for "Long-term cortical adaptation reshapes hue appearance" | Mixed | webster2015 is review-grade (good anchor); boehm2014 + tregillus2021 primaries. 3-stack but mixed-purpose, acceptable. Pass. |
| L66 | `basim2025` for "deutan … adaptation exceeds threshold loss predicts … post-receptoral gain" | Specific empirical | Primary, specific — correct. Pass. |
| L66 | `emery2021` for "realign toward the blue–yellow direction" | Specific empirical | Primary — correct. Pass. MEMORY.md caution: do not numerically equate emery2021 21.4° with β_s — Intro does **not** do this. Good. |
| L73 | `brouwer2009, kuriki2015, bannert2018` (Gap 1) | General "group-level in healthy observers" | Mix of primaries used to support a *general* statement ("describe geometry at the group level"). Borderline — for a general statement §20 prefers a review. Low priority since each is genuinely a group-level study. |
| L73 | `tregillus2021` (magnitude/gain), `rina2024` (dichromacy/achromatopsia) | Specific empirical | Primary, correctly mapped to specific findings. Pass. |
| L73 | `brouwer2013` for "continuous relational structure" | Method origin (RDM/relational) | brouwer2013 as the relational-structure source — verify it is the apt origin for "continuous relational structure" rather than a representational-geometry methods paper. Likely fine. Minor. |

**No 5+ citation stacks.** Largest is 3 (L64, L66, L73) — all defensible. No specific-claim↔review mismatch except the minor L73 Gap-1 case.

---

## 4. §26 Pre-Submission Checklist (Introduction-applicable boxes)

### Reverse outline
- [x] One sentence per paragraph, reads in order — narrates the funnel. **Pass.**
- [~] Matches §1 Step 5 outline — **drift**: findings/approach preview removed vs pre-draft ¶5 (intentional, but §22c "connect forward" now under-served). **Conditional.**
- [~] No paragraph needs two sentences — **L57 borderline** (three roles). **Flag.**

### Claims
- [ ] One-sentence central contribution recoverable — recoverable from L78 + L91, **but** efficacy/result deliberately absent (Phase-3 reserved). Acceptable for this paper's scope; not a fail. **N/A-ish / Pass.**
- [x] Every numeric Δ has baseline+metric+dataset — only numbers are 8%/0.4% (L47), 2–12 nm (L48), both with sources. The one empirical comparison (L57 "one of two products") lacks effect size — **minor**, it's a cited study not the paper's Δ. **Pass with minor.**
- [~] Every "first/only/no X" cites a review or is removed — **FAIL**: L73 "we are not aware of…" and "is untested" lack a scoped search qualifier (venues/years). **Fail → fix.**
- [x] Every untestable verb replaced — **Pass** (no Tier-B contribution verbs).
- [~] Every vague adjective operationalized — **"realizable" (L85/L89) not operationalized inline**. **Fail → fix.**
- [x] No self-praise — **Pass.**

### Citations
- [x] General claim → review — mostly (L64, L66 anchored by reviews). **Pass** (minor L73 Gap-1 caveat).
- [x] Specific empirical claim → primary — **Pass.**
- [x] Method origin → original — **Pass** (ishihara1917, brettel1997, machado2009).
- [x] No 5+ stacks — **Pass** (max 3).

### Structure
- [~] One role per paragraph — **L57 mixes route + evidence + gap.** **Flag.**
- [x] First sentence = topic sentence — every paragraph leads with its topic. **Pass.**
- [~] Pronouns unambiguous (§3) — **L62 "It receives an input…"**: "It" = "cortical color machinery" from prior sentence; acceptable but at paragraph scale slightly loose. **L66 "these observers"** (twice) = deutan/anomalous trichromats, clear. Minor. **Pass with minor.**
- [x] Terminology consistent — "cortical color geometry / neural color geometry / cortical readout / cortical representation" alternate for the same concept. §4 prefers one term. **Flag (minor)** — see below.
- [x] Observation/interpretation/implication separated — Intro is argument, not results; §9 less applicable. **N/A.**

### Section-by-section (§22 Introduction)
- [x] Explicit And–But–Therefore — **And** (L62–66 cortex intact + compensation), **But** (L73 three gaps), **Therefore** (L78 + Q-list). Present and clean. **Pass.**
- [~] Connect forward (§22c map gap→method→results) — gap→questions present; **method and results preview absent** (Q4 reserves efficacy). Borderline vs §22c; intentional. **Conditional.**

### Final pass
- [x] Filler removed (§5) — no "it is worth noting" etc. **Pass.**
- [~] Negatives with positive equivalents — L62 "not absent but structurally distorted", L68 "wrong level", L73 "not aware"/"neither preserves". Several "not X but Y" constructions; mostly rhetorically apt, but L62 "is therefore not absent but structurally distorted" could be positive ("is structurally distorted, not abolished"). **Minor.**
- [x] Nominalizations → verbs — generally verb-forward. **Pass.**
- [x] Passive → active — mixed but readable; "are quantified instead by threshold psychophysics" (L50) passive — minor. **Pass.**

---

## 5. Naive-reader readability (ML reader, zero domain knowledge)

Full report from naive-reader agent. Key actionable flags (flag sentences, do not rewrite):

- **Core terms never defined**: "cortical color geometry" / "neural color geometry" (the paper's central object) and "stimulus-space filter" / "pre-image" (the deliverable) are load-bearing yet undefined for an outsider. L57, L62, L78, L80–91. The reader reverse-engineers both from context. Consider one plain gloss at first use of each.
- **Thread-break sentences** (reader took on faith):
  - L57 "The criterion is then the appearance *report*, not the cortical representation that downstream tasks read out." — pivotal retina-vs-cortex contrast lands **before** "cortical representation"/"downstream readout" are introduced.
  - L64 "This code is shared enough across people that one observer's color responses can be read out in a common space…" — "common space" + "validated" both unexplained.
  - L66 "chromatic-contrast adaptation exceeds what threshold sensitivity loss predicts, consistent with a post-receptoral gain…" — three undefined terms in one causal chain; the empirical backbone of the cortex-locus claim is opaque.
  - L73 "neither preserves the continuous relational structure that a hue-space filter must reshape" — argument shape clear, substance ("relational structure", "hue-space filter") ungrounded.
- **No findings preview** (corroborates §22c drift): the Intro states hypotheses (Q1–4, L89) but gives **zero** "we find / we show" — an ML reader finishes not knowing whether the filter worked. This is the deliberate Phase-3 reservation; flagged so the choice is conscious.
- **Restatement / padding**: the closing paragraph (L91) restates Q1–Q4 + the thesis without new information; the core "personalized cortex-based filter" claim is asserted ~4× (L57, L68, L85/89, L91). Consider trimming L91 or merging with L89.
- **Naive-reader verdict**: overall arc (two filter families → escape attempts → three gaps → four questions) is clear and followable; confusion is concentrated in undefined technical terms, not structure. For a vision-science venue (eLife/J.Neurosci) most of these terms are in-audience and acceptable; the four thread-break sentences above are worth a light gloss regardless of venue.

---

## 6. Priority summary

**Counts: Fatal 0 · Serious 3 · Minor 7**

No Fatal issues (no banned Tier-A/D self-praise, no overstatement violating CLAUDE.md; "grating" correctly absent — stimulus described abstractly; no specificity/"first-study" claims).

### Serious (fix before submit)
1. **L73 — scoped-search qualifier missing** (§19 Tier A / §26): "we are not aware of…" and "is untested" need an explicit search scope (venues + year range), per §19 "no X exists" rule and CLAUDE.md anti-overstatement. → add scope.
2. **L85/L89 — "realizable" not operationalized** (§19 Tier C / §26): define inline once (e.g. "exact stimulus-space pre-image within display gamut"). → operationalize at first use.
3. **L57 — paragraph mixes three roles** (§7 / §17): topic = prior personalization route, but body carries two empirical results + the gap-thesis (later re-stated L68/L73/L78). → consider splitting route+evidence from the gap statement; reduces 4× restatement of the central claim.

### Minor
4. **L86 — "outperform … filter" lacks metric** (§11/§19-C): name the metric (cortical distance to HC).
5. **L48 — stockman2000 ↔ 2–12 nm displacement** (§20): verify Stockman 2000 supports the anomalous-shift range; may belong to neitz2011.
6. **Terminology drift** (§4): "cortical color geometry / neural color geometry / cortical readout / cortical representation" used interchangeably — pick one primary term.
7. **L91 — closing paragraph restates Q1–Q4 with no new info** (naive-reader padding): trim or merge with L89.
8. **L57 — patterson2022 result lacks effect size/N** (§11): add magnitude to the one cited empirical comparison.
9. **L64 / L73 — minor citation tightening** (§20): brouwer2009 cited 2× in one paragraph; Gap-1 general claim leans on primaries rather than a review.
10. **Naive-reader thread-breaks** (readability): four sentences (L57, L64, L66, L73) land domain terms before grounding them — light gloss optional, venue-dependent.

### Recommended fix sequence
1. L73 scoped search (Serious #1) — touches §26 Claims box, quickest compliance win.
2. L85/L89 operationalize "realizable" (Serious #2) — single inline insertion.
3. L57 paragraph split (Serious #3) — structural; do this before minor citation/restatement edits since it absorbs #7 and part of the restatement issue.
4. Minor #4, #6 (metric + terminology) — mechanical.
5. Minor #5, #8, #9 (citation verifications) — require checking sources; batch.
6. Minor #7, #10 (padding/readability) — last, optional, venue-dependent.

---

*Report only. No edits applied to introduction_v2.tex. Final adjudication of all "suspect" citation flags is the user's.*
