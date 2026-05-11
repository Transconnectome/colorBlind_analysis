# Revision Report — Results/results_streamlined.tex — 2026-05-11
Scope: Full file (345 lines; R1–R6 subsections)
Rules version: ~/.claude/writing/academic_writing_rules.md (Parts II–V)
Pre-draft reference: docs/PAPER/pre_draft_2026-05-10.md

---

## 1. Reverse outline

### R1 — Clinical phenotype and participants (L21–45)
- L21–29 (¶1): Sub-08 (deutan, mild–moderate) and Sub-09 (protan, moderate–severe) span the deutan/protan and mild/severe range relevant for a clinical filter.
- L31–36 (¶2): 8-AFC identification confirms Ishihara classification, with individual error patterns consistent with each subject's CVD axis.
- L37–40 (¶3): Both cases locate within the physiologically and epidemiologically relevant cone-opsin polymorphism range.
- L42–45 (¶4): All inferences are framed as single-case Crawford–Howell analyses; no group-level CVD claim is made.

### R2 — LORO preserved (L51–69)
- L51–55 (¶1): The filter programme requires cortical discrimination to be intact → LORO is the appropriate test.
- L57–69 (¶2): HC and CVD both exceed chance; no HC–CVD group difference at any ROI; discrimination precondition confirmed.

### R3 — LOCO vulnerability (L75–130)
- L75–78 (¶1): LOCO trains on 7/8 hues and measures held-out-hue prediction error, yielding an 8-dimensional vulnerability vector.
- L80–94 (¶2): ⚠️ **Two roles mixed.** First half establishes HC hV4 hierarchy (hV4 interpolates; V1/V2/V3 do not). Second half profiles CVD near-floor LOCO and per-hue vulnerability patterns. These are two logical steps and should be two paragraphs (§7 violation).
- L96–104 (¶3): LOCO 100% concordance with JND; SRM ΔRDM only 33% — LOCO is the functional predictor of behavior.
- L106–130: Figure caption (fig:main).

### R4 — 2-Component model (L136–211)
- L136–144 (¶1): Three models evaluated by grid search: Machado (1-DOF), R+C (2-DOF retinal+cortical), 2-component dilation (2-DOF cortical).
- L146–155 (¶ "2-component"): 2-component reaches significance for both subjects with a consistent structure; S-cone axis weight consistent with Emery 2021 behavioral evidence.
- L157–172 (¶ "Retinal family"): Retinal family identifies a different model class per subject — preventing common-axis comparison of the two CVD cases.
- L174–195 (Table 1): Model fits per subject.
- L197–210 (¶ "Model selection"): 2-component selected on pre-image bijectivity; Machado collapses 3 hues for Sub-09; 2-comp gives 8/8 exact for both.

### R5 — SRM ΔRDM (L216–244)
- L216–219 (¶1): Question: does the 2-component distortion field explain pairwise RDM geometry independently of LOCO?
- L221–228 (¶2): Methods: voxel crossnobis, SRM projection, ΔRDM computed vs HC-LOO mean, permutation test.
- L230–237 (¶3): Sub-09 2-comp p=0.007; R+C cross-model p=0.026; Sub-08 NS — Sub-08 case rests on LOCO alone.
- L239–244 (¶4): ΔRDM = auxiliary convergence check only; SRM absorbs cone-shift signal; LOCO is the more informative phenotype.

### R6 — Pre-image filter (L250–323)
- L250–256 (¶1): Filter = per-hue pre-image of the distortion; numerical inversion method referenced.
- L258–265 (¶ "Bijectivity"): Sub-08 8/8 exact (mean 46.3°, max 104.2°); Sub-09 8/8 exact (mean 20.1°, max 48.1°); Machado collapses 3 hues for Sub-09.
- L267–276 (¶ "Detection agrees"): Detection converges across models; correction vectors diverge (cosine −0.18, 3/8 sign agreement) → behavioral 2AFC prediction stated.
- L278–285 (¶ "Individual divergence"): Two subjects' filters cosine-similarity < 0 → population-average correction fails at least one.
- L287–302 (Figure 2 caption).
- L304–323 (¶ "Specificity"): HC FPR caveat (15/21 HC tests reach nominal p<0.05); three converging anchors justify case-level specificity.

### Drift vs. intended outline

**Pre-draft [Fig 3]** ("SRM RDM — geometric characterization," intended as standalone figure section with sub-08 V2/sub-09 V1/sub-10 HC-CI-within detail) is **absent** from results_streamlined. SRM content is folded into R5 as an auxiliary ΔRDM check. This is an intentional editorial choice consistent with the updated pipeline (SRM = convergence check, not primary result), but the pre-draft lists Fig 3 as draftable. Flag for author confirmation.

**Pre-draft abstract key numbers** include "CVD failure at blue (d=1.37, p=0.046), purple (d=1.54, p=0.060)" — per-hue Hedges' d values. These are absent from R3 ¶2, which reports only ROI-level Hedges' g (V1 g=1.61, V2 g=1.85, hV4 g=1.34). If these per-hue statistics are valid and reproducible, they should be added to R3. If superseded, update the pre-draft abstract key numbers.

---

## 2. §19 Vocabulary

### Tier A — Banned (1 real hit)

- **L94** — `"group-level classification metrics cannot surface"` → §19A: `cannot` without stated assumption. Full context: *"Each participant's vulnerability profile is an individually-structured target that group-level classification metrics cannot surface."* The word `cannot` asserts logical impossibility. Fix: `"do not surface"` or `"fail to capture"` (empirical observation rather than logical claim).

### Tier B — Untestable verbs (0 real hits)
- L273 `"study's primary behavioural prediction"` — possessive noun, not the verb `study`. False positive. Pass.
- L332 — in comment block; ignored.

### Tier C — Vague (2 real hits)

- **L51** — `"only meaningful if"` → §19C: `meaningful`. Full context: *"A per-subject corrective filter is only meaningful if the visual cortex of a CVD individual still supports categorical discrimination."* Fix: `"is only applicable if"` or `"is only valid if"`. The criterion (categorical discrimination) is already stated, so the vagueness is minimal — but `meaningful` adds no precision and should be replaced.

- **L170** — `"effective descriptor"` → §19C: `effective`. Full context: *"is treated as an effective descriptor of the residual hV4 structure."* Fix: `"is treated as an empirical characterization of the residual hV4 structure"`. Dropping `effective` removes the vagueness without losing meaning.

### Tier D — Self-praise (1 borderline hit)

- **L146** — `\paragraph{2-component model --- unified parameterization across both subjects.}` → §19D: `unified`. The word has defensible technical content here (single model class vs. retinal family's different classes per subject), but `unified` has a self-congratulatory ring. Consider: `"2-component model --- consistent parameterization structure across both subjects"` or simply `"2-component model fits: both subjects"`.

---

## 3. §20 Citations

### General-claim ↔ specific-cite mismatch (1 suspect)

- **L241** — Claim: *"SRM-alignment partially absorbs cone-shift signal into the shared basis~\cite{chen2015}"* → **SUSPECT**. chen2015 is the SRM method paper. The claim that SRM absorbs cone-shift signal is an empirical finding from this study's own diagnostic analysis (documented in project memory: "RDM criterion FAILED all ROIs: SRM alignment absorbs cone shift signal"). Chen 2015 does not establish or document this behavior. Fix: remove chen2015 from this clause and reframe as a current-study observation: *"SRM-alignment was found to partially absorb cone-shift signal into the shared basis (see Supplementary Methods)"*, or cite the specific diagnostic result from this study.

### General domain claim → primary paper (1 borderline)

- **L63** — Claim: *"in line with previous work on CVD identification performance at above-threshold contrast~\cite{bosten2019, boehm2014}"* → General domain statement citing two primary papers. A methodological review would be more appropriate per §20, if one exists. **Flag for author**: verify whether bosten2019 is a review paper (if so, acceptable). If both are primary papers, this borderline citation can stand if no review covers the claim.

### Method origin issues (0)
All method citations correct: ishihara1917 (Ishihara test), machado2009 (Machado cone-shift model), tregillus2021 (R+C model), brouwer2009 (LOCO paradigm), crawford1998 (Crawford–Howell single-case), chen2015 (SRM) — all original papers. ✓

### Citation density warnings (0)
Largest stack: `\cite{schuett2023, chen2015, bannert2025}` at L228 — 3 citations for combined methodological approach. Under threshold. ✓

---

## 4. §26 Checklist

### Reverse outline
- [✓] Reverse outline coherent: logical progression R1→R2→R3→R4→R5→R6.
- [⚠] Match to §1 Step 5 outline: pre-draft [Fig 3] SRM RDM section absent; per-hue Hedges' d values from pre-draft abstract key numbers missing from R3 ¶2. See "Drift" above.
- [✗] No paragraph needs two sentences to summarize: **R3 ¶2 (L80–94) requires two sentences**. Split required (§7).

### Claims
- [N/A] One-sentence contribution recoverable from title + abstract — abstract not yet drafted.
- [✓] Every numeric Δ has baseline + metric + dataset: HC accuracy baseline (0.125 chance, 0.94±0.04 HC) ✓; LOCO ρ with HC mean±SD as anchor ✓; Hedges' g labelled HC vs CVD ✓; pre-image |δ| stated ✓.
- [✗] "first/only/no X" cited or removed: L94 `cannot`. Fix required.
- [✓] Untestable verbs: clean.
- [✗] Vague adjectives operationalized: L51 `meaningful`, L170 `effective`. Fix required.
- [⚠] No self-praise: L146 `unified` — borderline. Recommend revision.

### Citations
- [✗] Specific empirical claim → primary: L241 chen2015 cited for current-study finding about SRM signal absorption. Fix required.
- [⚠] General claim → review: L63 — verify bosten2019 type.
- [✓] Method origin → original paper: all correct.
- [✓] No 5+ citation stacks.

### Structure
- [✗] Each paragraph has one role: R3 ¶2 (L80–94) has two roles. Fix: split at "Both CVD participants fell near floor in hV4..."
- [⚠] First sentence = topic sentence: R2 ¶1 (L51–55) opens with a motivating condition ("A per-subject corrective filter is only meaningful if...") rather than the paragraph's finding. Minor — the framing is standard for a gating result, but the finding itself (LORO preserved) is buried at the end.
- [✓] Pronouns unambiguous throughout.
- [✓] Terminology consistent: LOCO/LORO/CVD/HC/hV4 used consistently.
- [✓] Observation / interpretation / implication separated: correctly handled in R5 ¶4 and R6 specificity paragraph.

### Section-by-section (Results only; other sections not yet drafted)
- [N/A] Abstract, Introduction, Discussion — not yet drafted.
- [⚠] Methods order matches Results order: SRM appears before FEM in Methods, but ΔRDM (SRM-based) appears after LOCO in Results. Minor navigation mismatch — acceptable given logical flow.
- [✓] Each result answers a prior question: all six subsections open with or follow from an explicit question.
- [⚠] Figures self-contained: fig:main caption does not specify y-axis units or scale for the vulnerability bar panels. Not fatal but flagged for figure-caption polish pass.

---

## 5. Priority summary

**Total issues: 8**

| Severity | Count | Issues |
|---|---|---|
| **Fatal** | 2 | L94 `cannot`; L241 citation mismatch |
| **Serious** | 4 | R3 ¶2 two-roles split; L170 `effective`; L51 `meaningful`; pre-draft per-hue d-values absent |
| **Minor** | 3 | L146 `unified`; R2 ¶1 topic sentence; L63 citation verification |

**Recommended sequence:**
1. **L94**: `cannot` → `"do not surface"` (§19A, Fatal).
2. **L241**: Remove chen2015 from SRM-absorbs-signal claim; reframe as current-study finding (§20, Fatal).
3. **R3 ¶2 (L80–94)**: Split into two paragraphs at "Both CVD participants fell near floor..." (§7, Serious).
4. **L170**: `"effective descriptor"` → `"empirical characterization"` (§19C, Serious).
5. **L51**: `"meaningful"` → `"applicable"` or `"valid"` (§19C, Serious).
6. **Pre-draft alignment**: Verify whether per-hue Hedges' d values (blue d=1.37, purple d=1.54) should be added to R3 ¶2 or removed from pre-draft (Serious).
7. **L146**: `"unified parameterization"` → `"consistent parameterization structure"` (§19D, Minor).
8. **L63**: Verify bosten2019 is review vs. primary (Minor).

For iterative fixes, pass this report to `/apply-draft`.
