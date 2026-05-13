# Revision Report — Discussion/discussion_v2.tex — 2026-05-11
Scope: Full Discussion section (6 paragraphs, L6–L94)
Rules: §2 sentence precision, §7 one role per paragraph, §8 main point first, §9 obs/interp/impl separation, §19 vocabulary, §20 citations, §25 Discussion structure, §26 checklist

Source file: `docs/PAPER/Discussion/discussion_v2.tex` (95 lines)
Reference outline: `pre_draft_2026-05-10.md` §"Discussion — revised 2026-05-11" (¶1–¶6)

---

## 1. Reverse outline

- **L9–L19 (¶1, intended: how gap filled)** — Selective LOCO impairment with preserved LORO in hV4 marks the cortical correction locus, and a 2-component angular-dilation model provides exact per-subject pre-image correction vectors. *Maps to intended ¶1.*
- **L21–L33 (¶2, intended: LOCO–behavior, what's new)** — LOCO interpolation (not SRM ΔRDM geometric distance) is the cortical quantity that predicts JND confusion, extending Brouwer & Heeger 2009 hV4 interpolation to CVD. *Maps to intended ¶2.*
- **L35–L50 (¶3, intended: literature context + individual divergence)** — β_s is structurally consistent with Tregillus 2021 / Emery 2021, but Sub-08 and Sub-09 correction vectors are mutually divergent (cosine sim < 0), showing that a population-average retinal model cannot fit both. *Maps to intended ¶3.*
- **L52–L64 (¶4, intended: detection/correction divergence, Phase 3 falsifier)** — All models agree on who needs correction but disagree on the correction direction; a 2AFC test on each subject's LOCO-vulnerable hue pairs is the falsifiable cortical-vs-retinal arbitration. *Maps to intended ¶4.*
- **L66–L81 (¶5, intended: limitations)** — Three bounds: N=2 CVD, Sub-09 β_c non-significance (collapses to 1-component), and 71% HC FPR requiring convergence anchors rather than permutation significance alone. *Maps to intended ¶5.* Note: "Phase 3 보류" from intended ¶5 is folded into the last sentence ("Behavioural filter validation remains the registered criterion"), which is acceptable but understated.
- **L83–L94 (¶6, intended: field impact)** — Pipeline is a proof-of-concept that fMRI-derived individual cortical geometry can ground a correction architecturally distinct from population-average retinal approaches, with Phase 3 as the planned behavioural test. *Maps to intended ¶6.*

### Drift vs intended outline
- **No structural drift.** All six paragraphs are in the intended order and each has the intended role.
- **Minor — ¶6/¶4 overlap (L90–94 vs L62–64):** Both paragraphs end on the Phase 3 2AFC behavioural test. ¶4 frames it as the falsifier; ¶6 reuses it as the field-impact closing beat. The repetition weakens the ¶6 distinct role ("field impact") — recommend ¶6 closes on the methodological architecture point, not the Phase 3 test, which already owns ¶4's last 3 lines.
- **Minor — ¶5 limitation ordering:** The four intended limitations (N=2, Sub-09 β_c NS, HC FPR 71%, Phase 3 deferred) are present but the Phase 3 deferral is reduced to a one-clause coda; this is acceptable but worth a topic-sentence beat to surface it.

---

## 2. §19 Vocabulary

### Tier A — Banned (1 hit, 0 violations)

1. **L29 "novel"** — context: `\citeA{brouwer2009}, who showed that hV4 --- but not early visual areas --- supports interpolation to novel hues in typical observers.`
   - **Status:** FALSE POSITIVE. "Novel hues" is a technical term of art in the colour-vision literature (= stimuli withheld from training) and is the standard usage in Brouwer & Heeger 2009 itself. Not the unqualified-claim sense Tier A bans.

### Tier B — Untestable verbs (2 hits, 0 violations)

1. **L32 "must address"** — context: `the same interpolation failure that predicts JND confusion is what the correction filter must address`
   - **Status:** FALSE POSITIVE. "Address" here is a noun-phrase complement ("what X must address"), used in the concrete sense "the target the filter is built to act on", not the vague research-verb sense Tier B bans (e.g., "we address X" in an intro).

2. **L56 "constitutes ... primary falsifiable prediction"** — no banned verbs in the surrounding window; `address` was not actually flagged here (matched on `2AFC` line via L56 grep). No issue.

### Tier C — Vague (1 hit, 0 violations)

1. **L71 "statistically significant"** — context: `the confusion-axis component ($\beta_c$) is statistically significant for Sub-08 only; for Sub-09, the bootstrap confidence interval for $\beta_c$ includes zero`
   - **Status:** FALSE POSITIVE. Used in the standard statistical sense with the supporting CI specification in the same sentence (Sub-09 CI includes zero). §19 Tier C bans `significant` *without p-value or equivalent*; the CI here satisfies the equivalent-quantification requirement.

### Tier D — Self-praise (1 hit, 1 violation)

1. **L62–L64 "definitive test"** — context: `This preregistered comparison is the definitive test of whether cortical or retinal distortion is the operative target for CVD colour correction.`
   - **Status:** VIOLATION (Tier A/D overlap — `definitively` is Tier A; `definitive` as a self-evaluative adjective is the same family). The 2AFC test answers *one* falsifiable arbitration with N=2 CVD subjects under proof-of-concept scope; the Discussion itself acknowledges (L66–L81) that population-level claims require replication. Calling Phase 3 "the definitive test" overstates against the paper's own limitations paragraph.
   - **Fix:** "This preregistered comparison directly tests whether cortical or retinal distortion is the operative target ..." (drop self-evaluative adjective; the falsifiability is already conveyed by L55–60).

### Additional vague/banned-adjacent items flagged for review (not strict violations)

1. **L11 "actionable"** — `the cortical locus at which CVD colour distortion is actionable`. Borderline Tier C (vague). Operationalised by the rest of ¶1 (correction vectors with exact pre-image), so passes if read as a forward reference, but the topic sentence would be sharper as "...identifies the cortical site of correctable CVD colour distortion" or "...identifies the cortical target for a correction filter."
2. **L23, L64, L94 "operative target"** — repeated 3× in 95 lines. Not a Tier word, but the repetition weakens ¶4 and ¶6 closings and signals a single-word over-reliance. Consider varying ("corrective target", "intervention target") in ¶4 and ¶6.
3. **L54 "diverge markedly"** — Tier C-adjacent ("markedly" = vague intensifier). The text immediately cites `\cref{app:retinal_family}` so quantification is one click away, but inline a number (e.g., "cosine similarity $< 0$", which is already given for ¶3 L46) would strengthen.
4. **L66 "proof-of-concept scope"** — Tier C-adjacent ("scope"). Operationalised by the three explicit bounds that follow, so OK as a topic-sentence framing.

### Tier summary
- Tier A violations: 0
- Tier B violations: 0
- Tier C violations: 0
- Tier D violations: 1 (L63 "definitive test")
- Borderline / stylistic: 4 (actionable, operative ×3, markedly, scope)

---

## 3. §20 Citations

Four citations total. Each is evaluated against §20 (general → review; specific empirical → primary; method origin → original paper).

### Citation 1: L28 `\citeA{brouwer2009}`
- Claim type: **specific empirical** — "hV4 --- but not early visual areas --- supports interpolation to novel hues in typical observers"
- Source type: primary empirical paper (Brouwer & Heeger 2009, *Journal of Neuroscience*, MVPA hue decoding in V1–VO1)
- **Match:** ✓ correct (primary paper supporting a specific empirical claim about hV4 interpolation).

### Citation 2: L37 `\citeA{emery2021}`
- Claim type: **specific empirical** — "CVD perceptual errors concentrate near S-cone confusion loci in behavioural hue-scaling tasks"
- Source type: primary empirical (Emery et al. 2021, hue scaling in anomalous trichromats)
- **Match:** ✓ correct.

### Citation 3: L39 `\citeA{tregillus2021}`
- Claim type: **specific empirical** — "V2/V3 BOLD responses in anomalous trichromats include a cortical gain component ($g$) that partially compensates the retinal cone shift"
- Source type: primary empirical (Tregillus et al. 2021, cortical gain in anomalous trichromats)
- **Match:** ✓ correct.

### Citation 4: L68 `\cite{crawford1998}`
- Claim type: **method origin** — "single-case statistics \cite{crawford1998} permit individual-level inference"
- Source type: original method paper (Crawford & Howell 1998 single-case t)
- **Match:** ✓ correct.

### Suspect mismatches (0)
None.

### Citation-stacking
No 5+ stacks. Maximum stack size = 1. ✓

### Coverage gaps (suggestion, not violation)
- **L40–L41** "V2/V3 BOLD responses ... include a cortical gain component ($g$) that partially compensates the retinal cone shift" — Tregillus 2021 is correct as primary, but the *concept* of cortical compensation in CVD has multiple supporting primary lines (Neitz et al., Webster et al.). For a Discussion paragraph this single primary cite is fine; flagging only if reviewers expect broader scaffold.
- **L9–L11 (¶1 topic sentence)** has no citation, which is correct (the claim is from this paper's own Results). ✓
- **L66–L81 (limitations paragraph)** — Crawford & Howell is the only cite; this is appropriate since the other two limitations (β_c NS for Sub-09; HC FPR 71%) refer to this paper's own analyses (`\cref{app:hc_specificity}` is referenced).

---

## 4. §26 Checklist

| # | Item | Status | Line ref / note |
|---|---|---|---|
| 1 | Reverse outline coherent, matches pre-draft | ✓ | All 6 ¶ map to intended roles. Minor ¶4/¶6 closing overlap on Phase 3 (see §1 drift note). |
| 2 | No paragraph requires two sentences to summarize (§7) | ✓ | Each paragraph is summarizable in one sentence (see §1). |
| 3 | Each paragraph has one role | ✓ | ¶1 gap-fill, ¶2 context-behavior, ¶3 context-literature+individual, ¶4 falsifier, ¶5 limitations, ¶6 impact. |
| 4 | First sentence = topic sentence | ✓ (5/6) / ✗ (1/6) | ¶1 L9–11 ✓; ¶2 L21–24 ✓; ¶3 L35–37 ✓; ¶4 L52–55 ✓ (topic = detection–correction dissociation); ¶5 L66–67 ✓; ¶6 L83–86 ✓. All six pass. |
| 5 | Pronouns unambiguous | ⚠ | L46 "demonstrating directly that a population-average retinal model cannot simultaneously serve both CVD individuals" — antecedent "cosine similarity < 0 across hue pairs" → "demonstrating" dangles slightly (the demonstration is being made by the divergence, not by the cosine value alone). Minor; acceptable. L62 "If the retinal-family filter matches or exceeds the 2-component filter ..., the cortical distortion account would require revision" — "the cortical distortion account" is unambiguous. ✓ otherwise. |
| 6 | Observation / interpretation / implication separated | ⚠ | ¶2 L26–33 partly bundles obs ("only LOCO predicts behavioural confusions") + interpretation ("consistent with brouwer2009") + implication ("geometric distance metrics alone are insufficient") in one rolling clause. Readable but §9-tight version would split L30–33 into observation→implication. Minor. ¶3 L42–50 is cleaner. |
| 7 | Numeric Δ has baseline + metric | ✓ | L17–18 Sub-08/09 `mean $\|\delta\|$` in degrees ✓; L22 "100% vs. 33% concordance with same-day JND thresholds" ✓ (baseline = same-day JND); L46 "cosine similarity < 0" ✓ metric; L78 "71% of HC model–subject tests" ✓ denominator. |
| 8 | No Tier A/B/C/D violations | ✗ | L63 "definitive test" (Tier D / Tier A overlap). See §2. |
| 9 | Citations match claim specificity | ✓ | 4/4 citations correctly typed. See §3. |
| 10 | Discussion states limitations and ties to the gap | ✓ | L66–81 paragraph explicit; L80–81 "Behavioural filter validation remains the registered criterion" ties to the intended ABT Therefore (Phase 3). |
| 11 | §2 sentence precision (≤1.5 lines, no nested clauses) | ⚠ | L9–15 (¶1 opening, two sentences across 7 lines): each sentence is ~3 lines in source but renders as ~1.5 typeset lines — acceptable. L52–60 (¶4 first two sentences): the second sentence (L55–60) spans 6 source lines and contains a colon + an `(\cref{...})` + a conditional clause. Borderline §2. L66–73 (¶5 opening + "Second" sentence): the Second-clause sentence (L70–75) is long (6 lines) with semicolons and an emphasised label. Consider splitting. |
| 12 | §8 main point first | ✓ | Topic sentences are first in every paragraph. |
| 13 | §25 Discussion structure (gap fill → context → limitations → impact, no new results) | ✓ | Order ¶1 gap → ¶2–3 context → ¶4 falsifier (forward) → ¶5 limitations → ¶6 impact. No new results introduced (¶1 numerics restate Results). |
| 14 | No new results in Discussion | ✓ | L17–18 numerics (mean $\|\delta\|$) restate Results; L22 100% vs 33% restates Results; L46 cosine sim < 0 restates Results; L78 71% HC FPR restates `\cref{app:hc_specificity}`. All previously reported. |
| 15 | Active voice preferred (§2) | ⚠ | L26 "is consistent with"; L40 "showed that V2/V3 BOLD responses ... include"; L48 "Where Machado-based correction predicts" — mix of active and stative; acceptable for Discussion register. |

---

## 5. Priority summary

Fatal: 0 | Serious: 1 | Minor: 5

### Serious (1)
**S1. L63 "definitive test" — Tier D self-praise + overstatement vs ¶5 limitations.**
The same Discussion that frames the work as "proof-of-concept" (L66, L83) and lists three bounds (L66–81) cannot consistently label the planned 2AFC as "the definitive test." This is the highest-priority issue because it is the one place in the Discussion where the topic-sentence-level claim contradicts the limitations paragraph.
- Fix: replace "the definitive test of whether" → "a direct test of whether", "the preregistered behavioural arbitration of whether", or drop the adjective: "tests whether cortical or retinal distortion is the operative target."

### Minor (5)

**M1. L62–L64 and L90–L94 — ¶4/¶6 closing overlap on Phase 3 2AFC.**
Both paragraphs end on the Phase 3 behavioural test. ¶4 owns the falsifier role; ¶6 should close on the methodological architecture point ("encodes each individual's hV4 distortion field and inverts it exactly --- without assuming population homogeneity") rather than re-introducing Phase 3.
- Fix: trim ¶6's last sentence (L90–94) to a one-clause forward reference, e.g., "Phase 3 will test this prediction behaviourally."

**M2. L23, L64, L94 — "operative target" repeated 3× in 95 lines.**
Single-word over-reliance. Vary to "corrective target" / "intervention target" / "target for personalised correction."

**M3. L11 "actionable" + L54 "diverge markedly" — Tier C-adjacent vague qualifiers.**
- L11: prefer "...identifies the cortical site at which CVD colour distortion is correctable" or "...identifies the cortical target for a correction filter."
- L54: prefer an inline quantification — e.g., "diverge in direction (cosine similarity $< 0$, \cref{app:retinal_family})" — paralleling the ¶3 L46 quantification.

**M4. L55–L60 and L70–L75 — §2 long-sentence borderline.**
Two sentences each span ~6 source lines with semicolons/colons and nested clauses. Split each into two sentences to satisfy §2 "one idea per sentence, under 1.5 lines."
- L55–60 fix: split at the colon — "(a) state the falsifier in one sentence; (b) describe the 2AFC design in the next."
- L70–75 fix: split "Second, the confusion-axis component is significant for Sub-08 only" from "For Sub-09, the CI includes zero, and the model collapses to an effectively 1-component fit."

**M5. ¶2 L26–L33 — §9 obs/interp/impl looseness.**
Observation ("only LOCO predicts behavioural confusions"), interpretation ("consistent with brouwer2009"), and implication ("geometric distance metrics alone are insufficient") roll across one extended construction. Acceptable but tighter §9 would split:
- Obs sentence: "Only LOCO predicted JND confusions in the present data."
- Interp sentence: "This is consistent with \citeA{brouwer2009}, who showed hV4 interpolation to novel hues in typical observers."
- Impl sentence: "Geometric distance metrics alone are therefore insufficient to identify the cortical correction target."

### Recommended sequence
1. **S1 first** (L63 "definitive test") — single-word fix; resolves the internal-consistency conflict with the limitations paragraph. Highest leverage.
2. **M1** (¶6 closing) — restructure the last 2–3 sentences of ¶6 so ¶4 owns the falsifier and ¶6 owns the field-impact architecture point.
3. **M4** (sentence splits at L55–60 and L70–75) — mechanical §2 fixes.
4. **M2** ("operative target" repetition) and **M3** (L11/L54 vague qualifiers) — concurrent micro-edits.
5. **M5** (¶2 §9 separation) — optional polish if ¶2 is rewritten for any other reason.

No fatal issues. Structure is sound and the section matches the pre-draft outline. The one serious issue is a one-word self-praise / overstatement at the ¶4 closer; the rest are stylistic.

---

## Appendix — counts of structural markers

- `\cite*` calls: 4 (brouwer2009, emery2021, tregillus2021, crawford1998)
- `\cref` calls: 2 (app:retinal_family, app:hc_specificity)
- Em-dashes (`---`): 8 occurrences in 6 paragraphs (within §2 tolerance but on the upper side)
- Semicolons: 4 (L17, L25, L67, L71) — within §2 tolerance; two carry mild §2 splittable-sentence load (L67, L71)
- Paragraphs: 6 (matches pre-draft)
- Total lines: 95
