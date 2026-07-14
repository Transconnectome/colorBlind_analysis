# Revision Report — `docs/PAPER/Introduction/introduction_v2.tex` — 2026-05-12

Scope: full file (L1–L217), 5 subsections, ~1200 words.
Rules version: `~/.claude/writing/academic_writing_rules.md` (Parts II–V).
Pre-draft reference: `docs/PAPER/pre_draft_2026-05-10.md` §5.

---

## 1. Reverse outline

### §Intro-1 (Opening)
- L38–L50 (¶1): CVD는 인구 ~8%에 영향을 주며 L/M-cone opsin 다형성에서 비롯되어 L–M opponent 신호 감소(폐기 아님)를 만들고 Ishihara/psychophysics 표현형으로 잡힌다.
- L52–L62 (¶2): CVD는 on/off 손실이 아니라 피질 기계가 보존된 상태에서 표상이 *구조적으로 왜곡*되는 사례이며, 개인 수준 피질 기하학 재형성이 미해결 문제다.

### §Intro-2 (Current filters)
- L68–L80 (¶3): 현존 CVD 보정 필터는 하드웨어(EnChroma 노치) + 소프트웨어(BVM/Machado/Daltonization/Akalin) 두 계열로 분류되며, 모두 population-average 망막 모델에 동일한 변환을 모든 사용자에게 적용한다.
- L82–L101 (¶4): **두 문장 요약 필요** — (a) 개인화 시도는 망막 파라미터의 행동 캘리브레이션에 그치며 (b) 피질 적응이 외양을 재형성하므로 외양 매칭 캘리브레이션은 cortical compensation을 무시하고, (c) Somers 2024는 결과적으로 임계 식별이 안 움직임을 보이며, (d) 사용자 신경 색 기하학에 근거한 필터가 부재하다. → §7 위반 (4 roles)

### §Intro-3 (Cortex + gap)
- L107–L116 (¶5): 피질 색 표상은 분산 계층 계산이며 hV4가 연속 hue population code를 지원하고 SRM은 healthy decoding에서 검증되어 본 임상 확장에 발판을 제공한다.
- L118–L125 (¶6): 행동 연구는 anomalous trichromat가 단순 변별 결함이 아닌 cortical adaptation으로 보상하며 S-cone 축 ~21.4° 재가중을 보여, 변이의 핵심이 retinal–cortical 인터페이스에 있다.
- L127–L147 (¶7): 본 연구는 세 gap(Gap 1: 개인화된 distortion field 미부재; Gap 2: classification accuracy 의존; Gap 3: cortical compensation의 필터 설계 기준 미번역)을 한 번에 다룬다.

### §Intro-4 (Discrimination vs interpolation)
- L153–L165 (¶8): 연속 hue 조건의 원리적 필터는 연속 표상을 다뤄야 하며, LORO는 카테고리 변별성(필터 전제), LOCO는 연속 매니폴드 보간(필터 목표)을 측정한다.
- L167–L175 (¶9): LORO 보존 + LOCO 손상의 결합 패턴이 개인화 필터의 정당화·가능성 영역을 정의하며 per-hue LOCO vulnerability vector가 역산 대상 표현형이 된다.

### §Intro-5 (Three Q & contributions)
- L181–L184 (¶10): 본 논문은 두 CVD 개인을 Crawford–Howell 단일사례 분석으로 HC 7명 normative reference와 함께 다룬다.
- L186–L211 (¶11, enumerate): Q1 LORO/LOCO dissociation → vulnerability vector; Q2 1–2 DOF 세 모델 + SRM ΔRDM·Emery 외부 검증; Q3 pre-image bijectivity + retinal/cortical 갈림 → 2AFC falsifier.
- L213–L216 (¶12): 세 단계가 입력·중간 표현형·출력이 단일 CVD 사용자 수준에서 검증가능한 개인 기반 필터 설계 파이프라인을 구성한다.

### Drift vs intended (pre-draft §5)

| Intended ¶ | Actual location | Drift |
|---|---|---|
| ¶1 broad (8%, cone shift, color confusions) | §Intro-1 ¶1 | None |
| ¶2 existing tech (Tinted/recoloring, Pattie 2022) | §Intro-2 ¶3+¶4 | **Expanded 1¶ → 2¶ (+150w)**; cite changed `pattie2022` → `somers2024` (somers2024 not in bib — pre-existing issue) |
| ¶3 cortical compensation (Tregillus, Emery) | §Intro-3 ¶5+¶6 | Expanded 1¶ → 2¶; ¶5(SRM/bannert2025) is **new** addition not in pre-draft |
| ¶4 gap (ABT compact) | §Intro-3 ¶7 (Gap 1-3) | Compact ABT → explicit Gap 1-3 list (justified by narrative validation report) |
| ¶5 approach + preview | §Intro-4 + §Intro-5 (4 ¶) | **1¶ → 4¶** expansion (~400w added) |

**Balance drift**: §Intro-2 (현재 필터) and §Intro-4–5 (approach) grew far beyond the pre-draft 5-paragraph intent. Total intro now ~1200w vs pre-draft target ~700–800w implied by 5 paragraphs.

---

## 2. §19 Vocabulary

### Tier A — Banned (3 fatal, 1 borderline)

- **L132–133** — "*none* has inverted the high-dimensional cortical signal into an interpretable, individualized distortion field" → §19A `no X exists` pattern. The strict negative is asserted without bound. **Fix**: "to our knowledge, has not been combined with [individualized cortical inversion]" or "we found no published study that…", or qualify with venue/year window.
- **L161** — "no stimulus-space nudge *can* restore them" → §19A `cannot` direct. **Fix**: "the filter has no leverage if discrimination is below chance" — keep the logic but remove the absolute modal.
- **L170–171** — "Finding only the second would make a filter *impossible*" → §19A `impossible` direct. **Fix**: "would make a filter inapplicable" or "would preclude a stimulus-space remedy".
- **L82 borderline** — "Attempts to escape this average-user ceiling have, to date, taken a *single* route" → "single route" is a strong universal. **Fix**: "have predominantly taken one route" or cite Flatla 2015 / Lillo et al. exceptions if user wants to acknowledge non-Machado attempts.

### Tier B — Untestable verbs (2 hits)

- **L143** — "The present study *addresses* all three at once" → §19B `address`. **Borderline pass** because the next clause operationalizes ("by recovering…and inverting…"). Acceptable if kept; cleaner: "The present study takes up all three by…".
- **L181** — "We *address* three connected questions" → §19B `address`. The questions follow as enumerate, so this is the standard framing — minor. **Fix**: "We pose three connected questions" or "We test three connected questions".

### Tier C — Vague (1 hit)

- **L153** — "A *principled* filter for a continuous-hue condition must operate on…" → §19C `principled`. The sentence does state the operating principle (continuous-hue representation), so the adjective is partly redundant. **Fix**: drop "principled" → "A filter for a continuous-hue condition must operate on continuous-hue representation, not on categorical labels."

### Tier D — Self-praise (1 mild hit)

- **L213–216** — "Together these three steps constitute an individually-grounded, cortical-geometry-derived filter design pipeline, whose inputs, intermediate phenotype, and output are all testable at the level of the single CVD user." → §19D praising-by-listing-virtues. The triple ("individually-grounded, cortical-geometry-derived… testable") edges toward self-praise. **Fix**: cut to "Together, the three steps yield a per-individual filter whose input (cortical signal), intermediate parameters, and output (stimulus shift) are each testable." — removes adjective stack, keeps the testability claim.

---

## 3. §20 Citations

### General-claim ↔ specific-cite mismatches (1 suspect, 1 mild)

- **L50** — "*subsequent psychophysics*" cites `{brettel1997, bosten2019}`. Brettel 1997 is the BVM *simulation method* paper, not a psychophysics characterization of phenotype. **Fix**: drop `brettel1997` here (already cited correctly at L72); keep `bosten2019` review for the phenotype claim, or add a primary psychophysics paper.

### Citation reused for unsupported claim (1 hit)

- **L99** — `{bosten2019, hayashi2024}` cited for "CVD phenotype varies markedly even within a single diagnostic category." `bosten2019` (review) supports this; `hayashi2024` is the *LLM benchmark* paper (note in bib: "non-competitor for neural-filter framing"). It does **not** characterize CVD phenotype heterogeneity. **Fix**: drop `hayashi2024` here; either (a) restore the original v1 sidebar mention of LLM benchmarks in its own sentence, or (b) remove `hayashi2024` from Intro entirely.

### Citation duplicate stack (1 hit)

- **L91** `{tregillus2021, webster2015, boehm2014}` for "long-term cortical adaptation in anomalous trichromats…reshape hue appearance independently of the retina" (§Intro-2).
- **L121** `{tregillus2021, boehm2014, webster2015}` for "Long-term cortical adaptation reshapes hue appearance" (§Intro-3 ¶6).
- **Fix**: same 3 citations supporting near-identical claim 30 lines apart. Choose canonical location (recommend §Intro-3 ¶6 where the compensation mechanism is developed); in §Intro-2 ¶4 cite only `tregillus2021` as the most recent exemplar with forward reference ("see §Intro-3").

### Pre-existing bib issue (carried)

- **L98** — `\citep{somers2024}` cited but key is **not defined** in `bibliography.bib`. Verified via `grep -c "somers" bibliography.bib` = 0. This is pre-existing from prior intro revisions, not introduced today. **Fix required before submission**: add @article entry or remove citation.

### Citation density

- No 5+ stacks. Max stack = 3 (L91, L108, L113, L121, L130). All justified per claim.

---

## 4. §26 Checklist

### Reverse outline
- [✓] One sentence per paragraph — possible for 11/12 ¶
- [✗] Matches §1 Step 5 outline — substantial expansion 5¶ → 12¶; balance drift in §Intro-2 (¶2 intent → ¶3+¶4) and §Intro-4–5 (¶5 intent → 4 ¶). Justified by narrative validation, but document the deviation.
- [✗] No paragraph requires two sentences — **§Intro-2 ¶4 (L82–101) requires ≥2 sentences** to summarize (개인화 한계 + 메커니즘 + Somers + gap statement). Split into 2 ¶ (개인화 + 메커니즘 / Somers + missing claim) or trim.

### Claims
- [⚠] One-sentence central contribution recoverable — Abstract not drafted yet (per pre-draft); intro alone yields "individually-grounded cortical-geometry-derived filter design pipeline" which is weaker than pre-draft §1 contribution ("filters demonstrably correct color perception"). Acceptable because Phase 3 behavioral validation pending.
- [⚠] Every numeric Δ has baseline + metric + dataset — **L43 "approximately 2–12 nm"** missing source for "normal value" reference. Add Stockman & Sharpe 2000 or analogous primary. **L123 "21.4°"** OK (Emery 2021 cited; metric = S-cone axis re-weighting; baseline = HC).
- [✗] Every "first / only / no X" cited or removed — **3 hits (L132, L161, L170)** flagged in §2 Tier A.
- [⚠] Untestable verbs replaced — 2 hits at L143, L181 ("address"); borderline pass for L143, minor for L181.
- [✗] Vague adjectives operationalized — L153 "principled".
- [⚠] No self-praise — L213 mild.

### Citations
- [⚠] General claim → review — L50 brettel1997 mismatch (method paper for phenotype claim).
- [✓] Specific empirical → primary — OK.
- [✓] Method origin → original — OK (brettel1997 at L72, machado2009 at L73, bannert2025 at L115, crawford1998 at L183 all OK).
- [✗] hayashi2024 (L99) used for claim it does not support.
- [✗] tregillus+webster+boehm stack duplicated (L91, L121).
- [✗] somers2024 key undefined in `bibliography.bib`.

### Structure
- [✗] Each paragraph has one role — §Intro-2 ¶4 (4 roles).
- [⚠] First sentence = topic sentence — L167 "Predicted and empirically required, therefore, is a joint pattern" is grammatically awkward (post-posed predicate); topic OK but rewrite for cadence.
- [⚠] Pronouns unambiguous — L60 "That question remains open, and it is the question an individualized assistive filter must answer" — "that question / it / the question" all the same referent; remove redundancy ("That question is what an individualized filter must answer before it can be designed").
- [✗] Terminology consistent —
  - "individualized" (L60, L131) / "individual" (L141) / "personalized" (none in current draft but standard in abstract) / "individually-grounded" (L213) — **pick one canonical term**. Recommend "individualized" throughout.
  - "cortical compensation" (L88, L92, L94, L139) and "cortical adaptation" (L120) used interchangeably. Recommend "cortical compensation" when describing the perceptual outcome and "cortical adaptation" only when describing the time-course mechanism.
- [⚠] Observation / interpretation / implication — §Intro-3 ¶6 (L118–125) blends behavioural observation with location-of-variance interpretation in one paragraph. Acceptable for an intro but tighten.

### Section-by-section
- [✓] Introduction has explicit And–But–Therefore — And (§Intro-1, §Intro-3 ¶5,¶6) + But (§Intro-3 ¶7 Gap 1-3) + Therefore (§Intro-4 + §Intro-5). **Therefore split across two subsections**; consider one consolidating sentence at the end of §Intro-3 ¶7 (already present at L143–147, but it anticipates ¶8 LORO/LOCO and ¶11 contributions — mild zigzag).

### Final pass
- [⚠] Sentence length — multiple sentences exceed 1.5 lines and use long dashes / nested clauses (§2):
  - L42–50 (one sentence): nested "rather than its abolition" + long dash list.
  - L72–77: BVM + Machado + Daltonization + Akalin in one sentence with two long-dash insertions.
  - L82–87: "Attempts… have, to date, taken a single route: tuning a retinal-model parameter — the simulated L- or M-cone shift in Machado-class models — to a user's responses…" — 3 lines, 2 long dashes, nested clauses.
  - L88–94: "This matters because long-term cortical adaptation… has been shown to reshape hue appearance independently of the retina: appearance-matched calibration therefore inherits whatever compensation the cortex has already imposed, and a device tuned to undo only the retinal component re-renders the input as if that cortical compensation did not exist." — colon + semicolon-like chain.
  - L94–101: stacked behavioural evidence + phenotype heterogeneity sentence.
  - **Recommend split into shorter sentences** (§2: under 1.5 lines, one idea per sentence).
- [✓] Filler phrases mostly OK; minor: "at once" (L143), "at the level of" (L60, L184, L216 — used 3 times for slightly different scopes).
- [✓] Negatives — rhetorical contrasts ("not an on/off loss") intentional.
- [✓] Nominalizations — none egregious.
- [✓] Passive — L114 ("has recently been validated") acceptable for method attribution.

---

## 5. Priority summary

**Total issues: 22**
- **Fatal (3)**: Tier A `no X / cannot / impossible` direct hits at L132–133, L161, L170–171.
- **Serious (10)**:
  - L99 hayashi2024 citation category error (cite supports unrelated claim)
  - L91 vs L121 duplicate citation stack (tregillus + webster + boehm)
  - L50 brettel1997 misattribution (simulation method vs psychophysics phenotype)
  - L98 somers2024 undefined in bibliography.bib
  - L82 "single route" Tier A borderline
  - L153 "principled" Tier C
  - L213 self-praise Tier D
  - §Intro-2 ¶4 (L82–101) multi-role paragraph (§7) — split into 2 ¶
  - §2 violations: 4–5 sentences exceed 1.5 lines (L42–50, L72–77, L82–87, L88–94)
  - Terminology inconsistency: "individualized/individual/individually-grounded" mixed; "cortical compensation/adaptation" mixed
- **Minor (9)**:
  - L43 "2–12 nm" missing source citation
  - L60 pronoun chain redundancy
  - L143, L181 Tier B "address" verb
  - L167 awkward inversion ("Predicted and empirically required, therefore, is…")
  - "at the level of" repeated 3× (L60, L184, L216)
  - "filter" / "device" / "pipeline" used variably for same referent
  - §Intro-3 ¶7 Gap 3 sentence (L139–142) borderline filler at "an omission that directly limits filter design"
  - §Intro-3 ¶5 (bannert2025 SRM) is a methodological addition not in pre-draft outline — keep, but consider moving to Methods if balance is the priority

**Recommended fix sequence**:
1. **Fatal Tier A** (L132, L161, L170) — soften 3 absolute claims.
2. **Citation hygiene** — add somers2024 to bib OR remove cite; remove hayashi2024 from L99; remove brettel1997 from L50; consolidate tregillus stack (drop from L91 → cite only at L121).
3. **Structure** — split §Intro-2 ¶4 (L82–101) into two paragraphs: (a) personalization-attempt limitation, (b) cortical mechanism + Somers convergence + missing-filter claim.
4. **§2 sentence splits** — break L42–50, L72–77, L82–87, L88–94 into 2 sentences each (target < 1.5 lines).
5. **Terminology lock** — global replace "individually-grounded → individualized", "cortical adaptation → cortical compensation" (except L120 where time-course is the point).
6. **Tier C/D polish** — L153 drop "principled"; L213 trim adjective stack.
7. **Minor cleanup** — L43 add Stockman&Sharpe 2000 source; L60 pronoun trim; L167 invert "A joint pattern is predicted and empirically required".

After fix, re-run `/revise-draft` to confirm §26 all-pass.

---

For iterative fixes, pass this report to `/apply-draft`.
