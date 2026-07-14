# Revision Report — Introduction — 2026-05-13

Target: `docs/PAPER/Introduction/introduction_v2.tex` (216 lines)
Rules: §2–§18, §19, §20, §22, §26
Pre-draft outline: `docs/PAPER/pre_draft_2026-05-10.md`

## 1. Reverse outline

Section §Intro-1 (lines 38–61):
- ¶1a (L38–50): CVD affects ~8% of males/0.5% of females and arises from L/M cone-opsin polymorphisms producing ~2–12 nm spectral shifts that reduce the L–M signal and yield the classical Ishihara phenotype. [intended ¶1 = broad — **on target**]
- ¶1b (L52–61): CVD is not loss but structural distortion of an intact cortical representation, framing the open question of individual cortical geometry. [intended = broad — **drift: introduces "structural distortion" framing earlier than outlined; functions as bridge into §Intro-3, not ¶1**]

Section §Intro-2 (lines 67–102):
- ¶2a (L67–79): Current filters (EnChroma hardware, Brettel/Machado + Daltonization software, learned reformulations) share optimisation against a population-average retinal model. [intended ¶2 = existing tech — **on target**]
- ¶2b (L81–87): Attempts to escape the average-user ceiling tune Machado's cone-shift to user appearance reports, leaving optimisation at appearance, not cortical readout. [intended ¶2 = existing tech ceiling — **on target**]
- ¶2c (L89–102): Cortical adaptation (Tregillus 2021) is inherited by appearance-matched calibration; population-average filters change appearance without shifting thresholds (Somers 2024). [intended ¶2 = clinical validation, Pattie 2022 — **drift: Pattie 2022 missing; Somers 2024 substitutes; this paragraph also re-introduces cortical adaptation, partially duplicating §Intro-3 ¶3b**]

Section §Intro-3 (lines 108–147):
- ¶3a (L108–116): Cortical color is distributed across V1–hV4 with continuous-hue codes readable by forward encoding; SRM has been validated for healthy color decoding (Bannert 2025). [intended ¶3 = cortical compensation — **partial drift: this is the anatomy/methods scaffold, not compensation per se**]
- ¶3b (L118–125): Anomalous trichromats compensate via cortical adaptation; hue-scaling shows ~21.4° S-cone re-weighting (Emery 2021, Isherwood 2020). [intended ¶3 = cortical compensation — **on target**]
- ¶3c (L127–147): Three gaps remain — no inverted high-dimensional CVD geometry, reliance on classification, no concrete criterion for retinal-vs-cortical correction; this study takes up all three. [intended ¶4 = gap/ABT — **on target, but Gap statement also performs ABT "Therefore"; outline placed gap as separate ¶4**]

Section §Intro-4 (lines 153–176):
- ¶4a (L153–165): LORO classification = filter precondition; LOCO interpolation = filter target. [no direct intended-outline counterpart — **drift: outline §5 = "approach + preview"; this introduces a conceptual dichotomy not in the outline**]
- ¶4b (L167–176): Joint pattern (LORO preserved + LOCO impaired) defines the regime where individualized filters are warranted and the LOCO vector is the phenotype to invert. [no direct counterpart — **same drift**]

Section §Intro-5 (lines 182–216):
- ¶5a (L182–185): Three questions posed in two CVD individuals (deutan + protan), Crawford–Howell single-case design with 7 HC normative reference. [intended ¶5 = approach + preview — **on target**]
- ¶5b (L187–212): Q1 LORO/LOCO + vulnerability vector; Q2 1–2 DOF model + ΔRDM/Emery cross-check; Q3 pre-image + falsifiable 2AFC. [intended ¶5 = approach + preview — **on target**]
- ¶5c (L214–216): The three steps yield a per-individual filter with testable input, parameters, and output. [intended ¶5 = preview — **on target**]

### Drift vs intended outline
1. **Pattie 2022 not cited** at L95–102 despite project policy stating clinical-validation citation belongs in ¶2. Somers 2024 substitutes but is not the same evidence (population-level threshold non-shift vs. broad clinical validation).
2. **Outline §5 "Decompose hV4 distortion into retinal + cortical components"** is realized as Q2 (model families) at L195–203, but the outline's signature phrase "retinal + cortical decomposition" never appears verbatim — the 2-component model is named but its retinal-cortical separation logic is not in the Introduction prose.
3. **Sub-09 EXPLORATORY framing absent** (project policy required). L183 says "moderate–severe protan" with no flag that the protan single-case is exploratory; L210 promises a falsifiable behavioural test without noting hV4 LOCO p=0.035 and baseline_sp confound from MEMORY.
4. **HC FPR (7/7) limitation not flagged** anywhere in the Introduction; the gap-closing claim at L143–147 ("validity rests jointly on neural, behavioural, and cross-cohort external evidence") does not concede this.
5. **Cortical adaptation discussed twice** (L89–95 in ¶2c and L118–125 in ¶3b) — zig-zag risk (§17).

## 2. §19 Vocabulary scan

### Tier A (count 1 substantive; 1 "first" is a discourse marker, not a claim)
- **L132–133** — "to our knowledge, none has inverted the high-dimensional cortical signal into an interpretable, individualized distortion field." — Tier A "no X exists" pattern in bounded form. Bounded with "to our knowledge" per §19 Tier A allowed pattern; **acceptable** but should add a search scope ("in searched venues, 2009–2025") to fully comply.
- L169 — "Finding only the first would make a filter redundant" — "the first" here is enumeration ("the first of two"), **not** a Tier A novelty claim. Acceptable.

### Tier B (count 4)
- L57–58 — "The scientific and translational question is therefore not whether color information survives the retina --- it manifestly does --- but whether, and how, its cortical geometry is reshaped at the level of the individual." — uses untestable framing; "the scientific and translational question" is filler. **Fix**: "Whether cortical color geometry is reshaped at the level of the individual remains untested." (also addresses §5 filler and §2 nominalization).
- L130 — "Existing neural studies of color characterise population-mean geometry" — "characterise" is borderline Tier B (acceptable when paired with a metric); not paired here. **Fix**: "Existing neural studies of color report population-mean geometry…" or "estimate population-mean geometry by…".
- L143 — "The present study takes up all three by recovering, per individual, a low-dimensional distortion field…" — "takes up" is a vague stand-in. **Fix**: "Here we recover, per individual, a low-dimensional distortion field…" (matches §21/§22c "Here we show" convention).
- L182 — "We pose three connected questions in two CVD individuals…" — "pose" is acceptable as a structural marker, but combined with L188/195/204 the verbs are "Does/Can/Does"; the three questions never name what is **measured**. **Fix**: replace each "Does…?" with the specific quantity tested (e.g., "We test whether the per-hue LOCO vulnerability vector is non-zero…").
- L186 — "alongside a normative reference of seven healthy controls" — "normative reference" is borderline; quantify with the Crawford–Howell statistic. Acceptable as written if Methods defines it.

### Tier C (count 5)
- L98 — "without substantively shifting discrimination thresholds at threshold contrast" — "substantively" is Tier C-adjacent ("meaningful"-class adverb); also redundant with "at threshold contrast" + verb "shifting". **Fix**: "without changing JND at threshold contrast (Δ < [number]; Somers 2024)" — give the magnitude reported by Somers.
- L122 — "reveal a reliable S-cone axis re-weighting of approximately $21.4^\circ$" — "reliable" is Tier C; replace with a statistic. **Fix**: "report an S-cone axis re-weighting of $21.4^\circ$ (95% CI [a, b]; Emery 2021)" — or drop "reliable" and let the numeric value carry the weight.
- L124 — "These results locate the key variance not at the retina alone but at the retinal--cortical interface." — "the key variance" is Tier C ("important"-adjacent) + vague "key" (Tier D). **Fix**: "These results attribute residual hue distortion to the retinal–cortical interface, not the retina alone."
- L172 — "in which individualized corrective filters are simultaneously warranted and tractable" — "warranted" is borderline Tier C; "tractable" is unspecified. **Fix**: name the warrant ("…in which a stimulus-space filter can both reach the cortical readout (LORO preserved) and improve it (LOCO impaired)").
- L210–211 — "generating a falsifiable behavioural prediction to be tested in a same-day 2AFC discrimination experiment" — "falsifiable" is fine; "behavioural prediction" needs the predicted quantity. **Fix**: "predicting a per-hue JND shift Δ(JND) testable in a same-day 2AFC experiment".

### Tier D (count 1)
- L124 — "the key variance" — "key" is Tier D. Same fix as Tier C entry above.

(No occurrences of "elegant", "clean", "unified", "important", "surprising".)

### Banned per project policy (CLAUDE.md)
- "novel": no unqualified hits (L164 "a novel hue" = "previously unseen hue" in LOCO context; technical jargon, acceptable but consider "held-out hue" or "untrained hue" for §4 consistency).
- "comprehensive", "outperforms", "state-of-the-art": none found. **Pass.**

## 3. §20 Citation audit

### General-claim ↔ specific-cite mismatches
- L49–50 — "the classical phenotype captured by the Ishihara test~\citep{ishihara1917} and by subsequent psychophysics~\citep{bosten2019}" — General domain claim (phenotype). Ishihara 1917 is a method-origin cite, which is appropriate here; bosten2019 is a review, appropriate. **OK.**
- L98 — "population-average filters change the appearance of color without substantively shifting discrimination thresholds at threshold contrast~\citep{somers2024}" — Specific empirical claim → primary paper; appropriate **if** somers2024 is a primary. Verify the bib entry is a primary trial, not a review. **Project-policy issue: Pattie 2022 was the intended clinical-validation citation per the outline; it is missing.**

### Specific-claim ↔ review-only mismatches
- L122–124 — "hue-scaling experiments in anomalous trichromats reveal a reliable S-cone axis re-weighting of approximately $21.4^\circ$~\citep{emery2021, isherwood2020}" — Specific numerical empirical claim. Emery 2021 is primary; isherwood2020 status should be verified. The 21.4° value is from Emery alone; if Isherwood does not report this exact number, it should be moved to a separate "related" cite. **Fix**: cite emery2021 alone for the 21.4° number; cite isherwood2020 separately for converging evidence.
- L120–121 — "Long-term cortical adaptation reshapes hue appearance \citep{tregillus2021, boehm2014, webster2015}" — three primaries stacked. Tregillus 2021 and Boehm 2014 are primary empirical; Webster 2015 is a review. Acceptable but could compress to webster2015 (review) + tregillus2021 (primary). Project policy notes Tregillus 2021 venue is Curr Biol — verify bib entry.

### Method-origin issues
- L71 — "Brettel--Viénot--Mollon simulation~\citep{brettel1997}" — citing brettel1997 alone, but the standard name is "Brettel, Viénot, and Mollon" (1997). brettel1997 is the original. **OK.**
- L72 — "the parametrised Machado retinal model~\citep{machado2009}" — original. **OK.**
- L75 — "recent learned reformulations~\citep{akalin2025}" — "reformulations" plural, single cite. **Fix**: either cite multiple learned reformulations or change to "a recent learned reformulation~\citep{akalin2025}".

### 5+ citation stacks
- None. Largest stack = 3. **Pass.**

### Project-policy citation issues
- **L122–123 Emery 2021 / β_s connection**: MEMORY says Emery linkage is "model STRUCTURE grounding, not parameter VALUE convergence." The current text reports the 21.4° as a quantitative finding and the §Intro-5 Q2 (L202–203) cross-checks against "an independent cross-cohort behavioural estimate of the S-cone compensation angle." This risks reading as parameter-value convergence. **Fix**: rephrase Q2 cross-check to "cross-check the model's S-cone-axis structure against the behavioural compensation reported by Emery 2021" (structure, not value).
- **Tregillus 2021 venue**: project notes Curr Biol, not eLife. Verify `tregillus2021` in `bibliography.bib`.

## 4. §26 Checklist (Introduction-relevant items)

- **[~] §22a ABT explicit** — *And* (L108–116 distributed hue code) and *But* (L127–142 three gaps) are present; *Therefore* (L143–147) is present but buried in the same paragraph as the gaps, weakening the rhetorical break. **Partial pass**; split into two paragraphs would strengthen.
- **[✓] §22b Three-funnel** — broad (L38–61 CVD biology) → narrower (L67–102 filter ceiling) → paper-sized gap (L127–147). Pass.
- **[~] §22c Connect forward** — gap (L127–142) → method (L153–176 LORO/LOCO + Q1–Q3 L187–212) → preview (L214–216). Connection is present but the bridge between the three gaps (L127–142) and the three questions (L187–212) is implicit rather than explicit; no "Gap 1 → Q1" mapping. **Partial pass**.
- **[~] §7 One role per paragraph** — ¶2c (L89–102) mixes mechanism explanation (cortical adaptation inheritance) and empirical result (Somers); ¶3a (L108–116) mixes anatomy (V1–hV4 hue code) and method-scaffold (SRM Bannert 2025). Acceptable but on the edge.
- **[✓] §8 Topic sentence first** — every paragraph opens with a directional sentence. Pass.
- **[~] §11 Comparisons complete** — L43–44 "2--12~nm" has source (Stockman 2000) but no comparator; L98 "without substantively shifting discrimination thresholds" has no Δ or metric value (§19 Tier C flag above); L122–123 "approximately $21.4^\circ$" has no CI. **Partial fail** — at least the Somers Δ and Emery CI should be added.
- **[~] §4 Consistent terminology** —
  - "CVD" used throughout (16×) — consistent.
  - "anomalous trichromat" and "CVD" both used; **a deliberate choice when the claim is restricted to anomalous trichromats**, but the boundary should be stated once. **Action**: add a single sentence at L52 making the scope explicit.
  - "user" (L76, L79, L81, L83, L85, L101, L216) and "individual" (L60, L133, L143, L182, L193, L214) and "CVD individuals" (L182) — three overlapping referents. **Action**: keep "user" only in ¶2 (the consumer-filter context), then switch deliberately to "individual" / "single case" from ¶3 onward. Currently L216 still says "single CVD user" — change to "single CVD individual".

## 5. Priority summary

- **Fatal: 3**
  - F1. **Pattie 2022 omitted** despite project-policy ¶2 requirement (clinical-validation citation). Somers 2024 is not a substitute. Add at L98 or L100.
  - F2. **Sub-09 exploratory framing absent** at L183 + L210. Project-policy explicit. Without it, the falsifiable-2AFC promise at L210–211 overclaims given hV4 LOCO p=0.035 + baseline_sp confound (MEMORY).
  - F3. **L122 numeric claim "approximately $21.4^\circ$" lacks CI/metric** (§11 violation on a load-bearing number that recurs as a cross-check in Q2). Add CI from Emery 2021 or drop the number.

- **Serious: 6**
  - S1. L132–133 "to our knowledge, none has inverted…" — bound the search scope (venues, year range) per §19 Tier A allowed pattern.
  - S2. L143 "The present study takes up all three" — replace with "Here we…" per §22c convention.
  - S3. L202–203 Emery cross-check phrased as parameter-value convergence ("S-cone compensation angle") instead of structural grounding (MEMORY policy).
  - S4. L98 Somers 2024 claim missing Δ/metric value (§11).
  - S5. L124 "the key variance" — Tier C+D vague adjective; replace with the attributed quantity.
  - S6. Cortical adaptation duplicated in ¶2c (L89–95) and ¶3b (L118–125) — §17 zig-zag; consolidate ¶2c to the inheritance-by-calibration consequence only, leave the empirical claim to ¶3b.

- **Minor: 7**
  - M1. L57–58 "The scientific and translational question is therefore not whether…" — nominalization + filler; rewrite as a direct claim sentence.
  - M2. L75 "recent learned reformulations~\citep{akalin2025}" — singular cite for plural noun.
  - M3. L121 stack tregillus+boehm+webster — consider compressing to webster (review) + tregillus (primary).
  - M4. L130 "characterise population-mean geometry" — Tier B verb; replace with measured quantity.
  - M5. L210–211 "falsifiable behavioural prediction" — name the predicted quantity (Δ(JND) per hue).
  - M6. L216 "single CVD user" → "single CVD individual" for §4 consistency.
  - M7. Outline-drift: Q3 (L204–211) names "retinal and cortical fits converge on *who* is distorted but diverge on *how* to correct" — strong rhetorical line, but the outline §5 promised explicit "decompose hV4 distortion into retinal + cortical components"; surface that framing earlier in §Intro-3 ¶3c, not only in §Intro-5 Q3.

### Recommended fix order
1. Add Pattie 2022 clinical-validation citation (~L95–102) and Sub-09 exploratory hedge at L183/L210 (Fatal F1–F2).
2. Add Emery 2021 CI to L122–123 and reframe L202–203 as structural grounding (Fatal F3 + Serious S3).
3. Split L127–147 into two paragraphs: "three gaps" (¶3c) and "this study addresses them by…" (new ¶3d/¶4) to strengthen §22a ABT.
4. Consolidate cortical-adaptation duplication between ¶2c and ¶3b (Serious S6).
5. Apply Tier C operationalizations at L98, L122, L124 (Serious S4–S5).
6. Tier B verb replacements at L57, L130, L143 (Minor M1, M4 + Serious S2).
7. Terminology unification (user → individual from ¶3 onward; L216 fix) (Minor M6).
8. Bound the "to our knowledge" claim at L132 with search scope (Serious S1).
