# Revision Report — Results/results_streamlined.tex — 2026-05-11 (Cycle 2)
Scope: Full file (351 lines; R1–R6 subsections)
Rules version: ~/.claude/writing/academic_writing_rules.md (Parts II–V)
Pre-draft reference: docs/PAPER/pre_draft_2026-05-10.md
Prior report: revision_report_results_2026-05-11.md (Cycle 1)

---

## Cycle 1 → Cycle 2 resolution

| Cycle 1 issue | Severity | Status |
|---|---|---|
| L94 `cannot` → `do not surface` | Fatal | ✅ FIXED |
| L241 chen2015 for current-study SRM finding | Fatal | ✅ FIXED — citation removed, "in these data" added |
| R3 ¶2 two-role paragraph → split | Serious | ✅ FIXED — split at L85–86 |
| L170 `effective descriptor` → `empirical characterization` | Serious | ✅ FIXED |
| L51 `meaningful` → `applicable` | Serious | ✅ FIXED |
| Per-hue Crawford-Howell stats absent from R3 ¶2 | Serious | ✅ FIXED — added L94–98 (verified from per_color_breakdown.json) |
| L146 `unified parameterization` → `consistent parameterization structure` | Minor | ✅ FIXED |
| L63 bosten2019 citation type | Minor | ✅ VERIFIED — Current Opinion in Behavioral Sciences (review) ✓ |

**All 8 Cycle-1 issues resolved.**

---

## 1. Reverse outline

### R1 — Clinical phenotype (L14–45)
- L21–29 (¶1): Sub-08 (mild–moderate deutan) and Sub-09 (moderate–severe protan) span the clinically relevant diagnostic-axis and severity range.
- L31–36 (¶2): 8-AFC confirms Ishihara classification; error patterns consistent with each subject's CVD axis.
- L37–40 (¶3): Both cases fall within the physiologically and epidemiologically relevant cone-opsin polymorphism range.
- L42–45 (¶4): All inferences are single-case Crawford–Howell analyses; no group-level CVD claim is made.

### R2 — LORO preserved (L47–69)
- L51–55 (¶1): Filter applicability requires preserved cortical discrimination → LORO is the appropriate test.
- L57–69 (¶2): HC and CVD both exceed chance; no group difference at any ROI; discrimination precondition confirmed; LORO establishes filter applicability.

### R3 — LOCO vulnerability (L71–110)
- L75–78 (¶1): LOCO trains on 7/8 hues and yields an 8-dimensional vulnerability vector.
- L80–85 (¶2): HC hV4 achieves above-chance interpolation (p=0.044); V1/V2/V3 discriminate but fail to interpolate.
- L87–100 (¶3): CVD near floor in hV4; per-hue deviations most pronounced at c7 purple (Sub-08) and c6 blue (both), quantified by Crawford–Howell; profiles are individually structured.
- L102–110 (¶4): LOCO 100% concordance with JND vs SRM ΔRDM 33% → LOCO is the functionally predictive metric.

### R4 — 2-Component model (L138–216)
- L142–150 (¶1): Vulnerability vector encodes cortical distortion; three models evaluated by grid search.
- L152–161 (¶ 2-component): 2-component significant for both subjects; S-cone axis weight grounded in Emery 2021.
- L163–178 (¶ Retinal family): Retinal family selects different model class per subject → prevents common-axis comparison.
- L203–216 (¶ Model selection): 2-component selected on pre-image bijectivity; Machado collapses 3 hues at Sub-09.

### R5 — SRM ΔRDM (L218–250)
- L222–225 (¶1): Question: does 2-component also predict pairwise RDM geometry independently?
- L227–234 (¶2): Voxel crossnobis → SRM projection → ΔRDM vs HC-LOO mean; permutation test.
- L236–243 (¶3): Sub-09 2-comp p=0.007; R+C p=0.026 cross-check; Sub-08 NS.
- L245–250 (¶4): ΔRDM = auxiliary check only; SRM absorbs cone-shift signal in these data; LOCO is primary.

### R6 — Pre-image filter (L252–329)
- L256–262 (¶1): Filter = per-hue pre-image of distortion; Brent's method.
- L264–271 (¶ Bijectivity): 8/8 exact for Sub-08 (46.3°) and Sub-09 (20.1°); Machado collapses 3 hues.
- L273–282 (¶ Detection agrees): Detection converges; correction vectors diverge (cos=−0.18, 3/8 sign); behavioral 2AFC prediction stated.
- L284–291 (¶ Individual divergence): Two subjects' filters cosine < 0 → population-average correction fails at least one.
- L310–329 (¶ Specificity): HC FPR caveat; 3 converging anchors justify case-level specificity.

### Drift vs. intended outline
- Pre-draft Fig 3 (standalone SRM RDM section) absent: editorially intentional — SRM is convergence check only (R5). Not drift.
- Pre-draft per-hue Crawford–Howell numbers updated and verified: pre_draft §4 abstract key numbers corrected (verified 2026-05-11).
- No other drift.

---

## 2. §19 Vocabulary

### Tier A — Banned (0 hits) ✅

### Tier B — Untestable verbs (0 real hits) ✅
- **L279** — `"study's primary behavioural prediction"` — possessive noun `study's`, not the verb `study`. False positive. Pass.

### Tier C — Vague adjectives (0 hits) ✅
- `meaningful` → fixed (L51) ✓
- `effective` → fixed (L176) ✓
- `significant` at L59, L64, L81, L106 — all accompanied by p-values and named tests. ✓

### Tier D — Self-praise (0 hits) ✅
- `unified` → fixed (L152) ✓

---

## 3. §20 Citations (0 issues) ✅

| Line | Claim | Citation | Verdict |
|---|---|---|---|
| L24 | Ishihara test | ishihara1917 | Method origin → original ✓ |
| L38 | 2–12 nm cone opsin range | neitz2011, deeb2005 | Specific genetic claim → primary papers ✓ |
| L39 | ~8% male CVD prevalence | bosten2019 | General domain → review journal ✓ |
| L44 | Crawford–Howell tradition | crawford1998, schuett2023 | Method origin → original ✓ |
| L63 | CVD identification at above-threshold contrast | bosten2019, boehm2014 | General domain → review + primary ✓ |
| L82 | LOCO method replication | brouwer2009 | Method origin → original ✓ |
| L148–149 | Machado/R+C model origins | machado2009, tregillus2021 | Method origins → original papers ✓ |
| L160 | CVD errors near S-cone loci | emery2021 | Specific behavioral claim → primary ✓ |
| L172 | Protan shift range | machado2009, neitz2011 | Physiological range → primary ✓ |
| L174 | g=−1 Tregillus level | tregillus2021 | Specific empirical value → primary ✓ |
| L234 | ΔRDM prediction methodology | schuett2023, chen2015, bannert2025 | Combined method citation (3 items, under threshold) ✓ |
| L245–250 | SRM absorbs cone-shift signal | [none — current-study finding] | Fixed: chen2015 removed ✓ |
| L321 | Protan physiological range | neitz2011 | Primary ✓ |
| L325 | S-cone confusion loci | emery2021 | Primary ✓ |

---

## 4. §26 Checklist

### Reverse outline
- [✓] Reverse outline coherent: R1→R2→R3→R4→R5→R6 logical progression.
- [✓] Match to §1 Step 5 outline: no unintended drift (Fig 3 absence intentional).
- [✓] No paragraph needs two sentences to summarize: after R3 split, all paragraphs have single roles.

### Claims
- [N/A] One-sentence contribution: abstract not yet drafted.
- [✓] Every numeric Δ has baseline + metric: HC baseline stated for all comparisons; Hedges' g with ROI labels; Crawford–Howell d with subject labels ✓.
- [✓] "first/only/no X" cited or removed: none present.
- [✓] Untestable verbs replaced: none found.
- [✓] Vague adjectives operationalized: all fixes applied ✓.
- [✓] No self-praise: `unified` fixed ✓.

### Citations
- [✓] General claim → review: bosten2019 (review) for prevalence, CVD identification ✓.
- [✓] Specific claim → primary: all correct ✓.
- [✓] Method origin → original: all correct ✓.
- [✓] No 5+ stacks: max 3 at L234 ✓.

### Structure
- [✓] Each paragraph has one role: split applied; all R1–R6 paragraphs single-role ✓.
- [⚠] First sentence = topic sentence: **R2 ¶1 (L51)** opens with motivating condition ("A per-subject corrective filter is only applicable if…") rather than the LORO finding. The finding itself is in R2 ¶2 L57. Acceptable standard gating structure; cosmetically minor.
- [✓] Pronouns unambiguous throughout ✓.
- [✓] Terminology consistent: LOCO/LORO/CVD/HC/hV4 ✓.
- [✓] Observation/interpretation/implication separated: R5 ¶4 and R6 specificity ¶ correctly structured ✓.

### Section-by-section
- [N/A] Abstract/Introduction/Discussion — not yet drafted.
- [⚠] Methods order matches Results: SRM section precedes FEM in Methods, but ΔRDM (SRM-based) follows LOCO in Results. Minor navigation mismatch — acceptable given logical flow.
- [✓] Each result answers a prior question: R1→R6 ✓.
- [⚠] fig:main caption: y-axis units and scale not specified for LOCO vulnerability bar panels. Not fatal; flagged for figure-caption polish pass.

### New content audit (L94–98, Crawford–Howell sentence)
- **L94–98**: "Relative to the HC reference range, the per-hue deviations are most pronounced at c7 (purple) for Sub-08 (Crawford--Howell $d = 2.40$, $p = 0.033$, one-tailed) and at c6 (blue) for both participants (Sub-08: $d = 2.13$, $p = 0.047$; Sub-09: $d = 2.15$, $p = 0.046$; one-tailed single-case tests, uncorrected for 8 hues)."
  - Statistics verified against per_color_breakdown.json hV4 section ✓
  - Correct formula (Crawford–Howell) cited ✓
  - One-tailed direction stated; multiple-comparison caveat included ✓
  - [⚠] Sentence length borderline (~2 lines): packs 3 parallel statistical comparisons. **Minor** — data-density justifies inline reporting; consider table if journal allows.

---

## 5. Priority summary

**Total issues: 3 (all Minor)**

| Severity | Count | Issues |
|---|---|---|
| **Fatal** | 0 | — |
| **Serious** | 0 | — |
| **Minor** | 3 | R2 ¶1 topic sentence; L94–98 sentence length; fig:main y-axis units |

**All Fatal and Serious issues from Cycle 1 are resolved.**

Remaining minor items require no further `/apply-draft` pass before drafting Introduction and Discussion. They are best addressed in a final pre-submission polish pass.

---

## Next steps

```
✅ Results section §26 CLEAN (0 Fatal, 0 Serious)

Remaining 3 minor items — defer to final pre-submission polish:
  • R2 ¶1 topic sentence (standard gating structure — acceptable)
  • L94–98 sentence length (borderline; justified by data density)
  • fig:main caption y-axis units (figure polish pass)

Drafting order (§1 Step 6):
  1. ✅ Results — LOCKED
  2. → Introduction  (pre-draft ¶1–5, And-But-Therefore at ¶3)
  3. → Discussion
  4. → Abstract (last)

To begin Introduction: `/begin-draft` (existing pre_draft_2026-05-10.md is present — use (a) option)
or draft directly from pre-draft §5 Introduction outline.
```
