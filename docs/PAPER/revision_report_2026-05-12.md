# Revision Report — `docs/PAPER/Results/results_v4.tex` — 2026-05-12

**Scope**: Full Results section (393 lines).
**Rules version**: `~/.claude/writing/academic_writing_rules.md` (§19, §20, §26).
**Pre-draft setup**: `docs/PAPER/pre_draft_2026-05-10.md` (lock date precedes Phase 2 canonical adoption 2026-05-12, so some drift is intentional — see §1).

---

## 1. Reverse outline

### §6.1 Participants and behavioral phenotype
- **L20–35 ¶1**: Two CVD participants and seven HC; phenotype confirmed by Ishihara + 8AFC; all inferences framed as single-case analyses.

### §6.2 Color discrimination preserved (LORO)
- **L71–75 ¶1**: A corrective filter is "meaningful only if" CVD cortex retains categorical discrimination; verified by LORO + LDA on SRM-aligned data.
- **L77–87 ¶2**: Both CVD exceed chance at every ROI; cross-subject and within-hV4 tests show no HC–CVD difference; representational substrate is present.

### §6.3 hV4 interpolation impaired (LOCO)
- **L94–98 ¶1**: We asked where continuous hue geometry fails; LOCO method intro.
- **L100–105 ¶2**: Only hV4 supports above-chance interpolation in HC (p=0.044); V1–V3 do not.
- **L107–121 ¶3**: Both CVD fell at/below chance; impairment concentrated at S-cone intermediate colors (blue, purple, magenta); LOCO–JND concordance 100% (6/6) vs SRM-geometry–JND 33%.

### §6.4 SRM RDM geometry distortion
- **L165–170 ¶1**: We compared CVD vs HC RDM structure; ΔRDM + disparity.
- **L172–180 ¶2**: Sub-08 elevated at V2 (p=0.040); Sub-09 elevated at V1 (p=0.007); ROI specificity diverges between deutan and protan.
- **L182–190 ¶3**: ΔRDM heatmaps show subject-specific structures; R+C model permutation test sig for sub-09 V1, n.s. for sub-08 V2.

### §6.5 Two-component model
- **L235–241 ¶1**: We fitted three nested models by grid search (Machado / 2-component / R+C).
- **L243–252 ¶2**: 2-component reaches significance for both subjects (sub-08 ρ=0.88 p=0.004; sub-09 ρ=0.69 p=0.035); "**preferred for both subjects because it yields exact pre-image solutions for all 8 hues**".
- **L254–264 ¶3**: Parameter landscape shows a ridge; β_s consistent in range with Emery 2021 — physiological grounding only.

### §6.6 Personalized filter (Phase 2 canonical, V4-CCC + l_top-K)
- **L304–320 ¶1**: V4 LOCO restricted by permutation gate; 2-component map scored by composite loss `L = L_CCC + λ·l_top-K + 0.1·Tikh`.
- **L322–330 ¶2**: Canonical filters: sub-08 (44°, +28°) ρ_V4=0.62, l_top-K=0; sub-09 (30°, +46°) ρ_V4=0.50, l_top-K=0.5.
- **L332–336 ¶3**: Filter norms inside HC LOO range; specificity descriptive only.
- **L338–343 ¶4**: 2-component inverse bijective by construction; Machado collapses 3 hues for sub-09.
- **L345–355 ¶5**: 4-column visualisation shows the two filters move several hues in opposite directions.

### Drift vs intended outline (pre_draft_2026-05-10.md §5)

| Pre-draft Fig 5 outline | Current draft Fig 5 |
|---|---|
| ¶G: filter derivation from (β_s, β_c) per subject; full specification | Updated to V4-CCC + l_top-K composite loss derivation |
| ¶H: heterogeneity — mean \|δ\| 46.3° vs 20.1°, cosine sim = 0.55, 4/8 sign opposition | Replaced with ρ_V4 / l_top-K / norm reporting, no \|δ\| numbers, no cosine sim |
| Reported "8/8 exact pre-image" claim | Reports "l_top-K = 0 / 0.5" and "inverse bijective in principle" |

**Drift is intentional** — the user's Option A decision (2026-05-12) replaced the Phase A 2-component fit with Phase 2 closure canonical (V4-CCC + l_top-K). Pre-draft outline is now stale for §6.6.

**Drift is NOT intentional** for §6.5 (Fig 4): that section still describes the Phase A fit (ρ=0.88 etc.) and claims "2-component preferred because exact 8/8 pre-image", but §6.6 reveals the canonical operating point has l_top-K = 0.5 for sub-09 (not 8/8 exact). See §5 Priority 1 below.

---

## 2. §19 Vocabulary

### Tier A — Banned without explicit evidence (2 hits)

- **L327** — "Sub-08's filter **perfectly** recovers the top-3 vulnerable color set" → §19A: "perfectly" implies absolute. Already operationalized by "l_top-K = 0" in the same sentence's context; consider rewording to make the operational definition the noun: "Sub-08's filter recovers the top-3 vulnerable color set without error (l_top-K = 0)".
- **L375** (Fig 5 caption) — "colors **perfectly** recovered" → same issue; rephrase to "colors recovered without error" or "(l_top-K = 0)".

### Tier B — Untestable verbs (0 substantive hits)

- L175 false positive: "within-study control" (noun, not the verb "study"). Skip.

### Tier C — Vague adjectives (1 hit + 1 borderline)

- **L71** — "A corrective stimulus-space filter is **meaningful only if** the visual cortex of a CVD individual retains categorical discrimination" → §19C: "meaningful" is vague. The "only if …" clause already operationalizes the criterion; replace with "is **valid only if**" or "is **interpretable only if**".
- **L315** (borderline) — "a **stricter** criterion than Spearman ρ (rank-only) or Pearson r (invariant to scale)" → §19C: "stricter" is operationalized within the same parenthetical (which dimensions Spearman/Pearson miss). Acceptable as-is; flag only because the word can drift in revision.

### Tier D — Self-praise (0 hits)

Clean.

### Filler / nominalization scan (0 hits)

- "in order to", "due to the fact", "it is worth noting", "we would like to emphasize", "has the ability to": none.
- L74–75: "verified this precondition using leave-one-run-out (LORO) cross-validation of a linear discriminant classifier applied to SRM-aligned responses" — long but mechanically clean (no nominalization replaceable by verb).

---

## 3. §20 Citations

### Citation style — **INCONSISTENT** (1 issue across 5 sites)

- L32 `\citeA{crawford1998}`
- L33 `\citeA{schuett2023}`
- L84 `\cite{bosten2019, boehm2014}`  ← style differs
- L105 `\citeA{brouwer2009}`
- L237 `\citeNP{machado2009}`
- L241 `\citeNP{tregillus2021}`
- L259 `\citeA{emery2021}`

Three macros used (`\cite`, `\citeA`, `\citeNP`). If `apacite` is the bibliography package, the convention is `\citeA{...}` (author year style, e.g. "Brouwer & Heeger (2009)") and `\citeNP{...}` (no parentheses, e.g. "Machado et al. 2009"). `\cite{...}` falls back to default numeric.

**Fix**: Use `\citeA{bosten2019}` and `\citeA{boehm2014}` at L84 to match the author-year style of the rest of the document.

### Specificity audit (claim type vs cite type)

| Line | Claim | Cite | Type match? |
|---|---|---|---|
| L32 | Single-case methodological framing | `crawford1998` | ✓ Primary methodological |
| L33 | Single-case framing (modern reframing) | `schuett2023` | ✓ Suspect-OK (Schütt 2023 — verify is the right reference) |
| L84 | "prior work on CVD above-threshold identification" | `bosten2019, boehm2014` | ✓ Two primary empirical papers; a review would also fit. Acceptable. |
| L105 | "replicating Brouwer & Heeger 2009" | `brouwer2009` | ✓ Primary, direct replication |
| L237 | "1-DOF Machado cone shift" model origin | `machado2009` | ✓ Original method paper |
| L241 | R+C model | `tregillus2021` | ✓ Original method paper |
| L259 | "21.4° S-cone phase shift in anomalous trichromats" | `emery2021` | ✓ Specific empirical, primary |

No 5+ citation stacks.

### Action

- Normalize all citation macros to `\citeA{...}` (or whatever the bib package mandates) at L84.

---

## 4. §26 Checklist

### Reverse outline
- [✓] One sentence per paragraph as written.
- [⚠] Matches §1 Step 5 outline: §6.6 drifted intentionally (Phase 2 canonical adoption), §6.5 NOT updated (still Phase A) — internal inconsistency, see §5 Priority 1.
- [✓] No paragraph needs two sentences.

### Claims
- [N/A] One-sentence contribution recoverable from title + abstract — title/abstract not in scope of this file.
- [⚠] Numeric Δ has baseline + metric + dataset:
  - L77: chance defined ✓
  - L101: HC mean ± SEM + chance ✓
  - L108–109: C&H t + p, baseline = HC distribution ✓
  - L113–115: per-hue C&H ✓
  - L243–247: ρ, p, n_permutations ✓
  - L322–330: ρ_V4, l_top-K, norm with baseline HC LOO range (L332–333) ✓
  - **L243–252 vs L322–330 inconsistency** — two different ρ/parameter sets for the "2-component model" claim, with no in-text reconciliation. See §5 Priority 1.
- [✓] No "first/only/no X" Tier A overclaims (`no HC–CVD difference` is a statistical statement, not a knowledge claim).
- [⚠] Untestable verbs replaced — clean for §19B.
- [⚠] Vague adjectives operationalized — L71 "meaningful" and L327/L375 "perfectly" need fix.
- [✓] No self-praise.

### Citations
- [⚠] Style inconsistency at L84 (see §3).
- [✓] General claim → review tolerance: prior-work claim L84 cites two primaries, acceptable.
- [✓] Method origin → original paper: machado2009, tregillus2021 ✓.
- [✓] No 5+ stacks.

### Structure
- [✓] Each paragraph has one role.
- [✓] Topic sentence first.
- [✓] Pronouns unambiguous.
- [⚠] Terminology consistency:
  - "δθ" vs "filter" vs "correction vector" — multiple terms used but each is anchored ✓
  - "LOCO ρ" (Phase A) vs "ρ_V4" (Phase 2) — same quantity but different notation. Standardize.
- [✓] Observation / interpretation / implication mostly separated.

### Section-by-section
- [N/A] Abstract / Intro / Methods / Discussion not in this file.
- [⚠] **Forward reference broken**: L305 cites `Section~\ref{sec:results:interpolation}` but no such label exists. The labels defined are `sec:results:loco`, `sec:results:loro`, `sec:results:geometry`, `sec:results:twocomp`, `sec:results:filter`. **Fix to `\ref{sec:results:loco}`**.
- [✓] Each result answers a prior question (LORO precondition → LOCO target → geometric basis → mechanistic model → corrective filter).
- [✓] Figures self-contained; captions state the takeaway.

### Final pass
- [✓] No filler phrases.
- [✓] Negatives mostly stated as positives.
- [✓] Nominalizations few and contextual.
- [⚠] One passive that could be active: L186–188 "A permutation test of the R+C cone-shift model against the observed ΔRDM was significant for Sub-09 at V1 (p = 0.026) but not Sub-08 at V2 (p = 0.179)" → "Permutation tests showed the R+C cone-shift model fits sub-09's ΔRDM at V1 (p = 0.026) but not sub-08's at V2 (p = 0.179)".

---

## 5. Priority summary

**Total issues: 8**

| Severity | Count | Items |
|---|---|---|
| Fatal | 2 | (1) §6.5 ↔ §6.6 internal inconsistency on 2-component fit. (2) Broken `\ref` at L305. |
| Serious | 3 | (3) Citation style mismatch L84. (4) L327 / L375 "perfectly" → operationalize. (5) L71 "meaningful" → "valid". |
| Minor | 3 | (6) "LOCO ρ" vs "ρ_V4" terminology drift. (7) L186 passive→active. (8) Stale pre-draft outline for §6.6 — update outline doc. |

### Detail on Priority 1 (Fatal) — §6.5 ↔ §6.6 inconsistency

**§6.5 (Fig 4, L243–252)** describes Phase A 2-component fit:
- Sub-08: β_s = 38°, β_c = −14°, ρ = 0.88, p = 0.004
- Sub-09: β_s = 6°, β_c = −22°, ρ = 0.69, p = 0.035
- Caption (L292–294): "White star: LOCO-optimal parameters (sub-08: β_s = 38°, β_c = −14°; sub-09: β_s = 6°, β_c = −22°)"
- Justification: "**preferred for both subjects because it yields exact pre-image solutions for all 8 hues**" (L249–251)

**§6.6 (Fig 5, L322–330)** uses Phase 2 canonical (V4-CCC + l_top-K):
- Sub-08: β_s = 44°, β_c = +28°, ρ_V4 = 0.62, l_top-K = 0
- Sub-09: β_s = 30°, β_c = +46°, ρ_V4 = 0.50, l_top-K = 0.5
- "sub-09 recovers only 1.5 of the top-3 positions" — i.e., **not** 8/8 exact

A reader will see **two completely different fits** with no in-text bridge explaining which is canonical. Sub-08's β_c sign even flips (−14° vs +28°).

**Fix options**:
1. **(Recommended)** Update Fig 4 + §6.5 to also use Phase 2 canonical params, OR
2. Add a bridging sentence at L300–304 in §6.6: "While the unweighted Spearman-ρ argmin reported in Section~\ref{sec:results:twocomp} (β = ...) yields the maximum rank correlation, we adopt a composite loss that additionally enforces top-K identity and mean/variance match for filter selection." + adjust the §6.5 "preferred because exact 8/8" claim, because under the canonical loss sub-09 has l_top-K = 0.5 not 8/8.
3. Frame §6.5 result purely as descriptive evidence that 2-component captures the LOCO profile (without claiming "preferred for exact pre-image"), and §6.6 as the formal selection.

The cleanest path is Option 1 (sync both sections to Phase 2 canonical), matching the same Option A logic just applied to Fig 5. The user already flagged this in our prior exchange.

### Detail on Priority 2 (Fatal) — Broken `\ref` at L305

```
Building on the result that hV4 is the only ROI passing the LOCO
permutation gate (Section~\ref{sec:results:interpolation}), ...
```
Label `sec:results:interpolation` is not defined. Replace with `\ref{sec:results:loco}` (the actual LOCO section at L91).

---

### Recommended sequence

1. **Resolve §6.5 ↔ §6.6 inconsistency** — decide whether to sync Fig 4 (and its captions, ρ/p numbers) to Phase 2 canonical, or add a bridging paragraph.
2. **Fix broken `\ref` at L305** → `sec:results:loco`.
3. **L84 citation style** → `\citeA{bosten2019, boehm2014}`.
4. **L327 / L375 "perfectly"** → "(l_top-K = 0)" or "without error".
5. **L71 "meaningful"** → "valid only if" or "interpretable only if".
6. **L186 passive→active**.
7. **Terminology pass**: "LOCO ρ" vs "ρ_V4" — choose one and apply.
8. **Update `pre_draft_2026-05-10.md` §5 Fig 5 outline** to reflect Phase 2 canonical framing (or note it is superseded by the 2026-05-12 framework change).

For iterative fixes, pass this report to `/apply-draft`.
