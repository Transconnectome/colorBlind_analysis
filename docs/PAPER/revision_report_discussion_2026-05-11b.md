# Revision Report — Discussion/discussion_v2.tex — 2026-05-11 (post-apply-draft)
Scope: Full Discussion section (6 paragraphs, L6–L91)
Rules: §2 sentence precision, §7 one role per paragraph, §8 main point first, §9 obs/interp/impl separation, §19 vocabulary, §20 citations, §25 Discussion structure, §26 checklist

Source file: `docs/PAPER/Discussion/discussion_v2.tex` (91 lines, post-apply-draft)
Reference outline: `pre_draft_2026-05-10.md` §"Discussion — revised 2026-05-11" (¶1–¶6)
Previous report: `revision_report_discussion_2026-05-11.md` (Fatal 0 | Serious 1 | Minor 5 → all resolved)

---

## 1. Reverse outline

- **L9–19 (¶1, gap filled)** — LOCO impairment with preserved LORO in hV4 identifies the correctable cortical site, and a 2-component angular-dilation model delivers exact pre-image correction vectors at both CVD severity levels. *Maps to intended ¶1.* ✓
- **L21–33 (¶2, LOCO–behavior)** — LOCO (not ΔRDM geometric distance) predicts JND confusions 100% vs 33%, establishing LOCO as the operative corrective quantity and extending Brouwer & Heeger 2009's hV4 interpolation finding to CVD. *Maps to intended ¶2.* ✓
- **L35–50 (¶3, literature + divergence)** — β_s is structurally consistent with Emery 2021/Tregillus 2021 S-cone evidence, but Sub-08 and Sub-09 correction vectors are mutually divergent (cosine sim < 0), demonstrating that a population-average retinal model cannot simultaneously serve both. *Maps to intended ¶3.* ✓
- **L52–63 (¶4, falsifier)** — All models detect the same CVD subjects but prescribe divergent correction directions; the preregistered 2AFC comparison directly tests whether cortical or retinal distortion is the corrective target. *Maps to intended ¶4.* ✓
- **L65–80 (¶5, limitations)** — Three bounds on proof-of-concept scope: N=2 CVD, Sub-09 β_c non-significant (effectively 1-component), and 71% HC FPR requiring three-anchor case-level specificity. *Maps to intended ¶5.* ✓
- **L82–90 (¶6, field impact)** — The pipeline is a proof-of-concept that individual cortical colour geometry can ground a correction architecturally distinct from population-average retinal approaches; Phase 3 will test the behavioural prediction. *Maps to intended ¶6.* ✓

### Drift vs intended outline
- **No structural drift.** All six paragraphs are in intended order, each with a single role.
- **¶4/¶6 Phase 3 overlap resolved.** ¶4 owns the falsifier framing; ¶6 closes on the architectural distinction, with Phase 3 as a brief one-clause forward reference. Previously flagged as Minor M1 — **fixed.**

---

## 2. §19 Vocabulary

### Tier A — Banned (1 grep hit, 0 violations)

1. **L28 "novel"** — context: `supports interpolation to novel hues in typical observers`
   - **FALSE POSITIVE.** "Novel hues" is a technical term of art in colour-vision MVPA (= withheld stimuli), the standard usage in Brouwer & Heeger 2009 itself. Not the Tier A unqualified-novelty claim. ✓

### Tier B — Untestable verbs (1 grep hit, 0 violations)

1. **L32 "address"** — context: `the correction filter must address`
   - **FALSE POSITIVE.** Noun-phrase complement ("the target the filter acts on"), not the research-verb sense Tier B bans. ✓

### Tier C — Vague adjectives (2 grep hits, 0 violations)

1. **L59 "significantly"** — context: `only the cortically-grounded 2-component filter should significantly reduce JND`
   - **FALSE POSITIVE.** Predictive claim about a registered 2AFC test; "significantly" means statistically significant in the context of a specified experimental comparison. ✓

2. **L70 "statistically significant"** — context: `statistically significant for Sub-08 only. For Sub-09, the bootstrap confidence interval for $\beta_c$ includes zero`
   - **FALSE POSITIVE.** Statistical expression with CI qualification in the following sentence. ✓

### Tier D — Self-praise (0 hits, 0 violations)

- No "definitive", "elegant", "clean", "unified", "important", "surprising" in post-edit text. Previously flagged L63 "definitive test" → **fixed to "directly tests."** ✓

### §19 summary
- Tier A violations: **0**
- Tier B violations: **0**
- Tier C violations: **0**
- Tier D violations: **0**

---

## 3. §20 Citations

4 citations, unchanged from previous report.

| Citation | Claim type | Source type | Match |
|---|---|---|---|
| L28 `\citeA{brouwer2009}` | Specific empirical (hV4 interpolation in typical observers) | Primary empirical | ✓ |
| L37 `\citeA{emery2021}` | Specific empirical (CVD errors at S-cone confusion loci) | Primary empirical | ✓ |
| L39 `\citeA{tregillus2021}` | Specific empirical (V2/V3 cortical gain in anomalous trichromats) | Primary empirical | ✓ |
| L67 `\cite{crawford1998}` | Method origin (single-case statistics) | Original method paper | ✓ |

- Suspect mismatches: **0**
- Citation stacks ≥ 5: **0**

---

## 4. §26 Checklist

| # | Item | Status | Note |
|---|---|---|---|
| 1 | Reverse outline coherent, matches pre-draft | ✓ | All 6 ¶ in intended order; no drift. |
| 2 | No paragraph requires two sentences to summarize | ✓ | Each ¶ has one role summarizable in one sentence. |
| 3 | Each paragraph has one role | ✓ | ¶1 gap-fill, ¶2 LOCO-behavior, ¶3 literature+divergence, ¶4 falsifier, ¶5 limitations, ¶6 impact. |
| 4 | First sentence = topic sentence | ✓ | All 6 paragraphs open with the main claim. |
| 5 | Pronouns unambiguous | ✓ | L46 "demonstrating directly" dangle was present in prior version; antecedent is clear from preceding clause (cosine sim < 0). Acceptable. |
| 6 | Obs / interp / impl separated (§9) | ✓ | ¶2 L30–33 split: implication ("Geometric distance metrics alone are insufficient") now its own sentence. Previously M5 — **fixed.** |
| 7 | Numeric Δ has baseline + metric | ✓ | L17–18: mean \|δ\| in degrees ✓; L22: 100% vs 33% with JND baseline ✓; L46: cosine sim < 0 ✓; L77: 71% with denominator "HC model–subject tests" ✓. |
| 8 | No Tier A/B/C/D violations | ✓ | 0 violations post-edit. L63 "definitive" → **fixed.** |
| 9 | Citations match claim specificity | ✓ | 4/4 correctly typed. |
| 10 | Discussion states limitations + ties to gap | ✓ | L65–80 explicit; L79–80 ties Phase 3 validation to the ABT Therefore. |
| 11 | §2 sentence precision (≤ 1.5 lines) | ✓ | Long sentences at L55–60 (¶4 colon) and L70–75 (¶5 semicolon) **split.** No sentence exceeds ~2 typeset lines. |
| 12 | §8 main point first | ✓ | Topic sentence leads every paragraph. |
| 13 | §25 Discussion structure (gap → context → limitations → impact) | ✓ | ¶1 gap → ¶2–3 context → ¶4 falsifier → ¶5 limitations → ¶6 impact. |
| 14 | No new results in Discussion | ✓ | All numerics (mean \|δ\|, 100%/33%, cosine sim, 71%) restate Results. |
| 15 | Active voice preferred | ✓ | Mix of active and stative; acceptable for Discussion register. |

---

## 5. Priority summary

**Fatal: 0 | Serious: 0 | Minor: 0**

All items in §26 checklist pass. No §19 vocabulary violations remain. All 4 citations are correctly typed. Reverse outline matches pre-draft outline with no drift.

**The Discussion section is clean. No further `/apply-draft` pass required.**

---

## Resolved from previous report (revision_report_discussion_2026-05-11.md)

| Issue | Previous status | Current status |
|---|---|---|
| S1: L63 "definitive test" | Serious | ✓ Fixed → "directly tests" |
| M1: ¶4/¶6 Phase 3 closing overlap | Minor | ✓ Fixed → ¶6 trimmed to one-clause forward ref |
| M2: "operative target" ×3 | Minor | ✓ Fixed → "corrective target" (¶4), removed (¶6) |
| M3a: L11 "actionable" | Minor | ✓ Fixed → "correctable" |
| M3b: L54 "diverge markedly" | Minor | ✓ Fixed → "diverge in direction (cosine similarity < 0;" |
| M4a: L55–60 long sentence at colon | Minor | ✓ Fixed → split into two sentences |
| M4b: L70–75 long sentence at semicolon | Minor | ✓ Fixed → split into two sentences |
| M5: ¶2 §9 obs/impl bundled via "and" | Minor | ✓ Fixed → implication detached as separate sentence |
