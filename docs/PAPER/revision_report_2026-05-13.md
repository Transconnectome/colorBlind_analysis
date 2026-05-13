# Master Revision Report — colorBlind Paper — 2026-05-13

**Scope: Introduction · Methods · Results · Figure captions**
**Excluded per user (2026-05-13): filter-related content (filter analysis not yet complete).**
**Discussion + Abstract not in scope this round.**

Rules: `~/.claude/writing/academic_writing_rules.md` §2–§26
Pre-draft outline: `docs/PAPER/pre_draft_2026-05-10.md`

## DEFERRED — Filter-related content excluded from this review

The following blocks are excluded from priority counts and recommended fixes. Their full reviews remain in the per-section reports for later use, but should **not** be acted on in the current pass:

| Section | Lines | Block |
|---|---|---|
| Introduction | L204–212 (Q3) | falsifiable 2AFC / filter-validation preview |
| Introduction | L214–216 (¶5c) | "individualized filter" preview close |
| Methods | L51–54 | second-session filter-evaluation paragraph |
| Methods | L255–271 (§Stimulus-space filter) | pre-image computation, bijectivity, Brent's method |
| Methods | L281–299 (§Behavioral concordance) | JND staircase / 8AFC filter validation |
| Results | L301–395 (§6.6 / Fig 5) | filter derivation, V4-CCC composite loss, HC LOO range |
| Figures | Fig 5 caption (L40–46) | filter pre-image, cosine 0.55, hue δ |
| Figures | Fig 6 | filter behavioral validation (already PENDING) |

**Issues no longer counted** (full content remains in section reports):
- Fig 5 Phase A vs Phase 2 closure framework drift (X3) — **deferred**
- Methods L268–271 result leak (filter pre-image section) — **deferred**
- Methods L299 result leak (filter behavioral section) — **deferred**
- Intro F2 L210 sub-09 portion ("falsifiable 2AFC") — **deferred** (L183 sub-09 portion still counts)
- Intro M5 "falsifiable behavioural prediction" (L210–211) — **deferred**
- Results §6.6 sub-09 EXPLORATORY at L329 — **deferred** (L246 Fig 4 portion still counts)
- Results Minor 8 Fig 4/Fig 5 caption parameter coexistence — **deferred**
- Results Minor 9 HC FPR duplication in §6.6 — **deferred**
- Figures Fatal 1 (Fig 5 stale framework) — **deferred**
- Figures Minor 8 |δθ| caption definition (Fig 5) — **deferred**

---

## Section reports (filter content marked DEFERRED inside each)

| Section | Report | Fatal | Serious | Minor |
|---|---|:-:|:-:|:-:|
| Introduction | `revision_report_introduction_2026-05-13.md` | 3 | 6 | 6 |
| Methods | `revision_report_methods_2026-05-13.md` | 1 | 3 | 5 |
| Results | `revision_report_results_2026-05-13.md` | 1 | 3 | 4 |
| Figure captions | `revision_report_figures_2026-05-13.md` | 0 | 2 | 5 |
| **Total (filter excluded)** | — | **5** | **14** | **20** |

---

## Cross-section critical issues — fix once, propagate

Two project-policy issues replicate across sections. Fix the canonical sentences once and propagate.

### X1. Sub-09 EXPLORATORY framing absent — Intro + Results + Figures (filter portion deferred)
- **Intro L183**: protan single-case mention without "exploratory / proof-of-concept / requires replication" qualifier.
- **Results L246 (Fig 4)**: sub-08 and sub-09 2-component fits treated symmetrically (p=0.004 vs p=0.035). No exploratory hedge near L246.
- **Figures Fig 2 (B), Fig 3, Fig 4 captions**: no "exploratory", "tentative", "case-study", or "N=1 protan" qualifier in any caption that makes a sub-09 claim.
- **Canonical fix**: project rule (MEMORY 2026-04-11 + CLAUDE.md) requires "proof-of-concept, requires replication" wording for sub-09 results. Compose one sentence; insert at Intro L183, Results L246, Fig 2/3/4 captions.

### X2. HC FPR 7/7 qualifier absent — Intro + Figures (Results already correct)
- **Intro L143–147**: gap-closing claim "validity rests jointly on neural, behavioural, and cross-cohort external evidence" does not concede that 7/7 HCs achieve label-permutation significance under the 2-component model.
- **Figures Fig 4 caption**: "predicts hV4 LOCO vulnerability ... sub-08 p=0.004; sub-09 p=0.035" — specificity claim without caveat. Add: "the 2-component model achieves nominal significance for 7/7 HCs under label-permutation; p-values are descriptive fits of LOCO vulnerability geometry, not specificity statements."
- **Canonical source**: Results §6.4 phrasing ("specificity descriptive only") is correct; propagate to Intro + Fig 4 caption.

### X3. ~~Phase 2 closure framework drift~~ — DEFERRED (filter scope).

---

## Per-section fatal items (priority order, filter excluded)

1. **Methods L17** — N=12 vs 13 off-by-one (HC 7 + sub-08 + sub-09 + sub-10 + 3 excluded = 13). Recount.
2. **Intro F1** — Pattie 2022 clinical-validation citation omitted at ~L95–102; Somers 2024 is not a substitute.
3. **Intro F2** — Sub-09 EXPLORATORY flag missing at L183 (filter portion at L210 deferred). See X1.
4. **Intro F3** — L122 "21.4°" numeric claim lacks CI/metric (§11 violation on a load-bearing number that recurs as Q2 cross-check). Q2 is 2-component, not filter — kept in scope.
5. **Results F1** — Sub-09 EXPLORATORY flag missing at L246 (Fig 4 / 2-component). See X1.

---

## Serious items grouped by theme (filter excluded)

### Theme A — Statistical reporting completeness (§11)
- Results L81, L83, L101, L110, L173, L175, L186: p-values reported without effect size or test statistic. **All on non-filter content (LORO, LOCO at hV4, ΔRDM).**
- Results L101 permutation N missing (cf. L246 lists 40,320).
- Intro L98 Somers 2024 claim missing Δ value.
- Intro L122 Emery 2021 CI missing.

### Theme B — Pipeline reconciliation (Methods drift vs outline)
- Methods §ROI L83–91 describes two-stage GLM, but outline ¶2 says GLMsingle. Reconcile.
- Methods L35 CIELab vs L218 Stockman opponent space (and pre-draft DKL): three color spaces, no bridge. Add transformation sentence.

### Theme C — Structural / vocabulary (§7, §17, §19, §22)
- Intro ABT structure: L143 "The present study takes up all three" → "Here we…"; split L127–147 into separate gap + therefore paragraphs.
- Intro Emery cross-check: L202–203 reads as parameter-value convergence; rephrase as structural grounding (MEMORY policy). **Q2 is 2-component, not filter — in scope.**
- Intro Tier C operationalizations: L98 "substantively", L122 "reliable", L124 "the key variance".
- Intro §17 zig-zag: cortical adaptation duplicated ¶2c L89–95 + ¶3b L118–125.
- Intro §19 Tier A bounding: L132–133 "to our knowledge, none…" — add search scope.
- Results §7 paragraph split: lines 107–121 merge ¶C (impairment) + ¶D (LOCO–JND concordance) — split per outline. **Non-filter content.**
- Methods §23 LOCO defined-before-use: L118 uses LOCO 24 lines before L147 definition.
- Figures §13 takeaway: Fig 2 caption body is panel-by-panel description; add cross-panel takeaway sentence.
- Figures §13 reconciliation: Fig 4 (B) Machado>2-comp for sub-09 unresolved; add reconciliation sentence per §13 self-containment.

---

## Pass status (filter excluded)

**Sections passing §26 checklist (non-filter scope)**: NONE.

**Blocking items for any "ready for review" claim (non-filter scope)**:
- Methods L17 N count.
- Sub-09 EXPLORATORY flag globally (Intro L183 + Results L246 + Fig 2/3/4 captions).
- Pattie 2022 citation at Intro L98.
- HC FPR qualifier at Intro L143–147 + Fig 4 caption.

**Pre-draft drift summary (non-filter)**:
- Intro: 4 drifts (Pattie missing, retinal+cortical decomp framing not in prose for §Intro-3, sub-09 flag, HC FPR; cortical-adaptation duplication).
- Methods: 2 drifts (GLMsingle vs two-stage GLM, CIELab vs DKL).
- Results: 1 structural drift (¶C/¶D merge at L107–121).
- Figures: 0 drifts in non-filter captions (Fig 1/2/3/4 alignment OK).

---

## Recommended fix sequence (filter excluded)

**Phase 1 — Cross-section project-rule sweep (high leverage)**
1. Compose canonical "sub-09 exploratory" sentence and insert at Intro L183, Results L246, Figures Fig 2/3/4 captions. (X1)
2. Compose canonical "HC FPR 7/7" sentence from Results §6.4 phrasing; insert at Intro L143–147 and Fig 4 caption. (X2)
3. Compose CIELab ↔ Stockman ↔ DKL color-space bridge sentence; insert at Methods §Stimuli + §2-comp + pre-draft alignment.

**Phase 2 — Per-section fatals**
4. Methods L17 N count fix (Twelve → Thirteen, or recount).
5. Intro F1 (Pattie 2022 cite at L98).
6. Intro F3 (Emery CI at L122).

**Phase 3 — Per-section serious**
7. Intro structural ABT split (L127–147 → two paragraphs).
8. Intro Emery cross-check reframing (L202–203 → structural grounding).
9. Results paragraph split (L107–121 → ¶C + ¶D per outline).
10. Results effect-size additions across L81, L83, L101, L110, L173, L175, L186.
11. Methods LOCO-defined-before-use fix at L118.
12. Methods GLMsingle vs two-stage GLM reconciliation (PI input needed).
13. Figures Fig 4 (B) Machado tension reconciliation in caption.
14. Figures Fig 2 takeaway sentence.

**Phase 4 — Minor batch**
15. All Tier B verb replacements, Tier C operationalizations, missing method-origin cites (Ledoit-Wolf, Brouwer 2009 for forward model, Hedges 1981), software versions (FreeSurfer/FSL/ezBIDS/Neurodesign/nilearn).
16. Terminology unification (user/individual, deutan/deuteranomalous).
17. Tier A bounding (L132 search scope).

---

📋 **Revision reports saved** →
- Master: `docs/PAPER/revision_report_2026-05-13.md` (this file)
- Per-section: `revision_report_{introduction,methods,results,figures}_2026-05-13.md` (filter content remains in those reports as reference; not in current scope)

**Summary (filter excluded): Fatal 5, Serious 14, Minor 20.**

**Next steps**:
- **Phase 1 cross-section sweep first** — three canonical sentences each touch 2–3 sections; one canonical version + propagate is more efficient than 4 separate `/apply-draft` passes.
- Then `/apply-draft` per section with the per-section report. Recommended order: **Methods** (1 Fatal: L17 N count + Theme B drifts) → **Results** (sub-09 + paragraph split + effect sizes) → **Intro** (Pattie + Emery + ABT split) → **Figures** (sub-09 + HC FPR + Fig 4 (B) reconciliation).
- Pre-draft setup IS present (`pre_draft_2026-05-10.md`).

After applying fixes, re-run `/revise-draft` per section to confirm Fatal=0 and §26 checklist all ✓.

**Decision points requiring user / PI input before any fix is applied (filter excluded)**:
1. **GLMsingle vs two-stage GLM** — is the methods_v2.tex two-stage pipeline canonical (pre-draft is stale) or is the pre-draft GLMsingle canonical (methods_v2.tex needs rewrite)?
2. **DKL vs CIELab** — pre-draft + CLAUDE.md §10 say DKL; methods_v2.tex L35 says CIELab. Which is canonical?

지금 (a) cross-section canonical 문장 3개 (sub-09 EXPLORATORY + HC FPR + color-space bridge)를 먼저 작성할까요, 아니면 (b) 위 결정사항 2개 (GLMsingle/DKL)를 먼저 확정한 다음 `/apply-draft`로 진행할까요?
