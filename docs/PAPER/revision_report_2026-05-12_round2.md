# Revision Report (Round 2) — `docs/PAPER/Results/results_v4.tex` — 2026-05-12

**Scope**: Full Results section (393 lines, post Round 1 fixes).
**Rules**: `~/.claude/writing/academic_writing_rules.md` (§19, §20, §26).
**Pre-draft**: `docs/PAPER/pre_draft_2026-05-10.md` (with 2026-05-12 update note).
**Additional directive**: move Machado-related content to appendix.

---

## 1. Reverse outline (post Round 1)

### §6.1 Participants and behavioral phenotype
- **L20–35 ¶1**: Two CVD participants + 7 HC; phenotype confirmed by Ishihara + 8AFC; single-case analysis framing.

### §6.2 Color discrimination preserved (LORO)
- **L71–75 ¶1**: Filter is "valid only if" cortex retains discrimination; LORO + LDA on SRM-aligned data.
- **L77–87 ¶2**: Both CVD exceed chance at all ROIs; no HC–CVD difference; substrate present.

### §6.3 hV4 interpolation impaired (LOCO)
- **L94–98 ¶1**: We asked where continuous hue geometry fails; LOCO method intro.
- **L100–105 ¶2**: Only hV4 supports above-chance interpolation in HC; V1–V3 do not.
- **L107–121 ¶3**: Both CVD at/below chance; impairment concentrated at S-cone intermediate colors; LOCO–JND 100% concordance vs SRM-geometry–JND 33%.

### §6.4 SRM RDM geometry distortion
- **L165–170 ¶1**: ΔRDM + disparity comparison.
- **L172–180 ¶2**: Sub-08 elevated at V2; Sub-09 at V1; ROI specificity diverges.
- **L182–190 ¶3**: ΔRDM heatmaps show subject-specific structures; **R+C model permutation tests fit sub-09 V1 but not sub-08 V2** (note: R+C used here as a probe for geometric model fit — see §3 below).

### §6.5 Two-component model
- **L235–241 ¶1**: Fitted **three nested models** (Machado / 2-component / R+C) by grid search.
- **L243–260 ¶2**: Under LOCO-ρ argmax, 2-component reaches significance for both subjects; Machado for sub-09 only; **2-component preferred on two grounds**: (i) captures both subjects' profiles, (ii) bijective angular-dilation guarantees pre-image. Last sentence: "operating point refined under stricter loss in §6.6".

### §6.6 Personalized filter (Phase 2 canonical)
- **L313–328 ¶1**: 2-component model class established in §6.5; V4 LOCO permutation gate (§6.3); refine operating point under V4-CCC + l_top-K composite loss.
- **L331–340 ¶2**: Canonical filters (44, +28) / (30, +46); sub-08 l_top-K = 0 ("without error"), sub-09 l_top-K = 0.5.
- **L341–344 ¶3**: Filter norms inside HC LOO range; specificity descriptive only.
- **L346–353 ¶4**: 2-component inverse bijective; **Machado collapses 3 hues for sub-09** (note: this is the only retained Machado mention in §6.6 — see §3).
- **L354–365 ¶5**: 4-column visualisation shows two filters move several hues in opposite directions.

### Drift vs intended outline
- §6.6 drift remains intentional (Phase 2 canonical adoption noted in pre-draft 2026-05-12 update).
- All other sections match the intended outline.

---

## 2. §19 Vocabulary

### Tier A — Banned (0 hits)
✓ Clean. Previous `perfectly` instances replaced with `without error (l_top-K = 0)`.

### Tier B — Untestable verbs (0 hits)
✓ Clean.

### Tier C — Vague adjectives (0 hits)
✓ Clean. Previous `meaningful` replaced with `valid`. The borderline `stricter` (L325) remains operationalized inline.

### Tier D — Self-praise (0 hits)
✓ Clean.

### Filler / passive (0 hits)
✓ Clean.

**Net Tier-level vocab status: PASS.**

---

## 3. Machado → Appendix migration plan

### Current Machado footprint (12 mentions across §6.5 + §6.6 + Fig 4 caption)

| Line | Section | Content | Action |
|---|---|---|---|
| L5 | comment | "2-component throughout; Machado retained as comparator" | UPDATE comment to reflect appendix migration |
| L237 | §6.5 ¶1 | "(i) the 1-DOF Machado cone shift ($\Delta\lambda$; \citeNP{machado2009})" | MOVE to Appendix (model enumeration moves wholesale) |
| L248 | §6.5 ¶2 | "Machado reached significance for Sub-09 ($\Delta\lambda = 13.5$ nm, $\rho_\text{V4} = 0.76$, $p = 0.018$) but not for Sub-08 ($\rho_\text{V4} = 0.62$, $p = 0.058$, n.s.)." | MOVE to Appendix |
| L251–255 | §6.5 ¶2 | "preferred over Machado on two grounds: (i) captures both subjects' profiles whereas Machado fails for Sub-08, (ii) bijective ... Machado loses for Sub-09 (three hues map to a single pre-image angle)" | KEEP (i)/(ii) framing but REPLACE explicit Machado naming with brief generic reference + Appendix pointer |
| L286 | Fig 4 caption | "Dashed lines: Machado (1-parameter cone-shift) prediction." | MOVE caption fragment to Appendix figure caption; consider whether dashed Machado line stays in Fig 4 main or moves entirely |
| L292 | Fig 4 caption | "Solid bars: 2-component model; hatched bars: Machado." | Same — caption fragment + figure panel change |
| L295–298 | Fig 4 caption | "Sub-08: 2-component $\rho_\text{V4} = 0.88$, $p = 0.004$; Machado $\rho_\text{V4} = 0.62$, $p = 0.058$ (n.s.). Sub-09: 2-component $\rho_\text{V4} = 0.69$, $p = 0.035$; Machado $\rho_\text{V4} = 0.76$, $p = 0.018$." | KEEP 2-comp numbers; MOVE Machado numbers to Appendix |
| L352 | §6.6 ¶4 | "By contrast, a 1-DOF Machado fit for sub-09 collapses three hues (green 135°, cyan 180°, blue 225°) onto a single pre-image angle (~127°), which mathematically prevents exact inversion at those positions." | MOVE entire sentence to Appendix or REPLACE with one-sentence summary ("Alternative 1-DOF models can suffer arc-compression failure at intermediate hues — see Appendix~A") |

### Recommended approach (3 options)

**Option M-A (Minimal main text + dedicated Appendix section)** ← Recommended
- §6.5 ¶1: drop the 3-model enumeration. Open with: "We fit the 2-component model
  (β_s, β_c) to each subject's hV4 LOCO vulnerability profile by grid search."
- §6.5 ¶2: drop the Machado comparison sentence and the (i)/(ii) bijection justification. Keep only the 2-component significance result. Add at the end: "Comparison against the 1-DOF Machado cone-shift model and the 2-DOF retinal+cortical model is provided in Appendix~A."
- §6.6 ¶4: drop the Machado collapse sentence. Keep only the positive statement: "The 2-component inverse is bijective by construction, so a stimulus-space pre-image exists for any target hue."
- Fig 4: regenerate without Machado dashed lines + hatched bars (Panel A solid lines only, Panel B 2-comp bars only). Or keep current Fig 4 but mark Machado elements as "see Appendix A" in caption.
- Create new **Appendix A: Alternative model comparison**, containing all moved content with its own figure (the Machado-vs-2-comp panels).

**Option M-B (Keep bijection justification in main, move numbers to Appendix)**
- §6.5 ¶2: keep "(ii) bijective angular-dilation guarantees pre-image exists" with brief mention "a property a 1-DOF retinal-shift model loses (Appendix~A)". Don't name Machado explicitly.
- §6.6 ¶4: same compression.
- Fig 4: same as M-A.

**Option M-C (Inline only the comparison, move bijection theorem)**
- §6.5 ¶2: keep model-class comparison narrative; remove (ii) bijection (move to Appendix).
- More radical. Probably not recommended — bijectivity is part of why 2-component was chosen and should stay visible.

### Why Option M-A is cleanest
- Streamlines §6.5 to a single-model story matching the rest of the paper's 2-component narrative.
- Avoids the awkward "preferred over Machado but only descriptively" framing.
- Reviewers seeking baseline comparison can still find it in Appendix A.
- The bijection property is a structural fact about the 2-component model class; it does NOT require Machado as a foil to be claimed.

---

## 4. §26 Checklist (re-run)

### Reverse outline
- [✓] One sentence per paragraph.
- [✓] Match to §1 Step 5 — drift explicitly documented in pre-draft 2026-05-12 update.
- [✓] No paragraph needs two sentences.

### Claims
- [N/A] Title/abstract not in this file.
- [✓] Numeric Δ has baseline + metric + dataset.
- [✓] No "first / only / no X" overclaims.
- [✓] Untestable verbs replaced.
- [✓] Vague adjectives operationalized.
- [✓] No self-praise.

### Citations
- [✓] Style consistent (`\citeA` for in-text, `\citeNP` for inside parenthetical lists).
- [✓] General claim → primary OK (L84 two primaries, acceptable density).
- [✓] Method origin cites original paper.
- [✓] No 5+ stacks.

### Structure
- [✓] Each paragraph has one role.
- [✓] Topic sentence first.
- [✓] Pronouns unambiguous.
- [✓] Terminology consistent (ρ_V4 now uniform).
- [✓] Observation / interpretation / implication separated.

### Section-by-section
- [N/A] Abstract / Intro / Methods / Discussion not in this file.
- [✓] All `\ref` resolved.
- [✓] Each result answers a prior question.
- [✓] Figures self-contained.

### Final pass
- [✓] No filler.
- [✓] Active voice predominant.
- [✓] Numbers given with context.

**§26 checklist: All applicable items PASS.**

---

## 5. Priority summary

**Total NEW issues: 0** (Round 1 fixes all held).

**Restructure task (separate from rule-driven fixes)**: 1
- **Machado → Appendix migration**: 12 mentions across §6.5, §6.6, and Fig 4 caption. Plan above (Option M-A recommended).

**Estimated scope**:
- Text edits: §6.5 (~12 lines reduced to ~6), §6.6 ¶4 (~3 lines reduced to ~1), Fig 4 caption (~5 lines reduced)
- Figure changes: regenerate Fig 4 without Machado overlays (Panel A dashed lines, Panel B hatched bars)
- New content: Appendix A section + Appendix Fig (moved Machado comparison)

### Recommended sequence
1. **Decide on Option M-A vs M-B**.
2. Cut Machado prose from §6.5 / §6.6 / Fig 4 caption.
3. Decide Fig 4 regeneration scope: full (remove Machado) or annotated (caption-only update with appendix pointer).
4. Draft Appendix A with moved Machado content.
5. Add `\appendix` + `\section{Alternative model comparison}` block.
6. Run `/revise-draft` on the appendix once drafted.

For iterative fixes, pass this report to `/apply-draft`.
