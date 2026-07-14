# Revision Report — Results — 2026-05-13

Target: `docs/PAPER/Results/results_v4.tex` (395 lines)
Rules: `~/.claude/writing/academic_writing_rules.md` §2–§18, §19, §20, §24, §26
Pre-draft outline: `docs/PAPER/pre_draft_2026-05-10.md` (Fig 5 framework superseded 2026-05-12 → Phase 2 closure canonical)

## 1. Reverse outline (grouped by figure)

### Fig 1 (paradigm, §6.1 Participants — lines 16–64)
- ¶ (20–35): Participant phenotype + Ishihara + 8AFC + single-case framing + paradigm cross-ref. [Not in pre_draft Results outline; serves as Methods/setup mini-section. Acceptable as a participants paragraph but mixes (i) phenotype, (ii) statistical framing rationale, (iii) figure pointer.]

### Fig 2 (LORO/LOCO — §6.2 lines 67–87, §6.3 lines 90–157)
- ¶A (71–87, LORO discrimination preserved): "LORO preserved in CVD; HC-CVD pooled p=0.668; hV4 within-ROI p=0.142." Match intended ¶A: **Y** (intended cited hV4 p=0.668; draft uses 0.668 for pooled and 0.142 for hV4 — this is a minor expansion).
- ¶B (94–105, hV4 = only interpolation gate in HC): "hV4 adj_acc=0.47±0.05, p_perm=0.044; V1–V3 fail." Match intended ¶B: **Y**.
- ¶C (107–121, CVD hV4 LOCO impaired with per-hue S-cone pattern + LOCO–JND concordance): Match intended ¶C **+** ¶D merged. Sub-08 adj_acc=0.25, p=0.082 n.s.; sub-09 adj_acc=0.13, p=0.024*; both below 3/8 chance; per-hue blue/purple/magenta vulnerability; LOCO–JND 100%, SRM–JND 33%. Effect sizes: per-hue d values present (d=2.13, 2.15, 2.40). **Note in pre_draft says "¶C d-values pending update — MAE→adj_acc transition" — draft now has d values; ASSUMING these are the updated adj_acc-based d. No explicit confirmation in draft text.**
- ¶D (intended): merged into ¶C. Drift: pre_draft separated ¶C (impairment) from ¶D (LOCO–JND concordance). Draft fuses them into one paragraph. **§7 violation candidate** (one role per paragraph): the merged paragraph covers (i) group-level impairment, (ii) per-hue S-cone pattern, (iii) JND concordance.

### Fig 3 (SRM RDM — §6.4 lines 160–227)
- ¶ (165–180, disparity test): "Sub-08 V2 p=0.040; sub-09 V1 p=0.007; sub-10 null; ROI specificity diverges." Match intended ¶D: **Y**.
- ¶ (182–190, ΔRDM + R+C cone-shift model): "Sub-09 V1 p=0.026; sub-08 V2 p=0.179; complementary to LOCO." Drift vs intended outline: pre_draft places R+C cone-shift in §6.5 (Fig 4 two-component). Draft folds R+C fit into Fig 3. Acceptable framing (R+C as a geometry-level diagnostic), but it removes the direct head-to-head 2-comp vs R+C comparison from Fig 4 — see Fig 4 drift below.

### Fig 4 (Two-component — §6.5 lines 230–298)
- ¶ (235–254, 2-comp captures LOCO vulnerability): "Sub-08 β_s=38°, β_c=−14°, ρ=0.88, p=0.004; sub-09 β_s=6°, β_c=−22°, ρ=0.69, p=0.035; 40,320 perms; bijective." Match intended ¶E: **Y, with reframing**. The intended ¶E claim "beats Machado-only and R+C" is **deferred to Appendix A** (line 240, 295–296). Drift: ¶F (intended) "8/8 exact pre-image; Machado 4/8 for sub-09" — this content is **partially absent from Results**: lines 248–250 mention bijectivity and "three hues map to a single pre-image angle for sub-09" in 1-DOF baselines, but the 8/8 vs 4/8 numerical comparison is also deferred to Appendix A.
- ¶ (256–266, parameter landscape + Emery grounding): "Ridge structure; β_s vs Emery 21.4° as physiological grounding, NOT parameter convergence." Match intended outline tone: **Y** (no convergence claim).

### Fig 5 (Filter — §6.6 lines 301–395)
**NOTE: pre_draft superseded — Phase 2 closure canonical is the source of truth, and the draft correctly reflects it.**

- ¶ (305–323, method): Defines V4-CCC + λ·l_top-K composite loss + Tikhonov; restricts to V4 LOCO; explains CCC vs Spearman/Pearson. Method paragraph — appropriate for Results since the loss form is the novel selection rule, not just a parameter.
- ¶ (326–334, canonical filters): **Phase 2 closure numbers**: sub-08 (44°, +28°), norm=52.2°, ρ_V4=0.62, l_top-K=0; sub-09 (30°, +46°), norm=54.9°, ρ_V4=0.50, l_top-K=0.5. Match Phase 2 closure canonical: **Y**.
- ¶ (336–340, HC FPR + descriptive specificity): HC LOO range [49.0°, 65.3°]; "specificity descriptive only"; HC FPR=100% acknowledged. Match intended outline: **Y, plus mandated HC FPR acknowledgement is present in Results (not deferred).**
- ¶ (342–345, bijective pre-image): Match intended ¶H (heterogeneity) only partially — the "filters heterogeneous; cosine sim=0.55" claim is **dropped**.
- ¶ (347–357, hue-by-hue heterogeneity): "Sub-08 cyan→magenta; sub-09 green/cyan→yellow; would move several hues wrong for the other." Replaces pre_draft's `cosine sim=0.55` with a verbal description. Match intended ¶H in spirit: **Y**.

**Stale pre_draft numbers absent**: 46.3°, 20.1°, "cosine sim=0.55", "4/8 opposite" — none of these appear in §6.6/Fig 5 caption. Draft is aligned to 2026-05-12 canonical.

### Fig 6 (Behavioral JND — pending)
- Lines 359–366: explicitly commented out as Phase 3. Match intended outline: **Y**.

## Drift vs intended outline
1. **¶C and ¶D merged** (lines 107–121). Pre_draft had ¶C = impairment, ¶D = LOCO–JND vs SRM concordance. Draft merges them. Minor §7 issue (one role per paragraph).
2. **Fig 3 absorbs R+C cone-shift fit** (lines 182–190). Pre_draft placed R+C inside Fig 4. Acceptable reframing as geometry diagnostic but downgrades the explicit "2-comp beats R+C/Machado" comparison.
3. **8/8 vs 4/8 pre-image comparison deferred to Appendix A** (line 250, 295–296). Pre_draft intended ¶F to make this comparison in Results. Currently only a passing reference ("three hues map to a single pre-image angle").
4. **Fig 5 "cosine sim=0.55, 4/8 opposite" framing replaced** with verbal hue-direction description (lines 351–356). Reflects the Phase 2 closure canonical (β_s, β_c) update, not stale pre_draft.

## 2. §19 Vocabulary scan

### Tier A
- **Line 24, 100, 104**: `replicating` Brouwer 2009 (line 104) — fine, accompanied by primary citation. No `the first`/`novel`/`no X exists`/`always`/`never`/`proves`/`comprehensive`/`state-of-the-art`/`outperforms` anywhere. **CLEAN**.

### Tier B
- **Line 71**: "is valid only if the visual cortex …retains" — `retains` is testable. OK.
- **Line 84**: `prior work on CVD above-threshold identification` — descriptive, OK.
- **Line 109**: "The impairment was not uniform across hues" — testable description. OK.
- **Line 165**: "To characterise the geometric basis" — `characterize` is Tier B watchword. Here it is operationalized immediately ("we compared the pairwise representational structure… ΔRDM… disparity"), so it satisfies §19 Tier B (operationalized inline). OK but borderline.
- **Line 256**: "reveals a clear ridge structure" — `clear` is vague (Tier C-ish); landscape map (Fig 4C) supports it visually. Minor — consider replacing with "shows a ridge along which β_s and β_c trade off."
- No `study`/`explore`/`understand`/`investigate`/`address`/`consider`/`examine` as primary verbs. **MOSTLY CLEAN.**

### Tier C — `significant`/`significantly` audit (the user-flagged false-positive trap)
Allowed: accompanied by p-value/test.
- Line 110 `*` marker only — accompanied by p=0.024 and t=−2.48. **OK**.
- Line 144 (Fig 2 caption) "sub-09 falls significantly below the HC distribution" — paired with t=−2.48, p=0.024. **OK**.
- Line 173 "Sub-08 showed significantly elevated disparity specifically at V2 (Crawford & Howell p=0.040)" — **OK**.
- Line 174–175 "no significant elevation at V1, V3, or hV4" — needs the p-value for those ROIs. Currently absent (sub-08 only). **Minor §19-C**: state "all p > X" for the null ROIs. Sub-09 sub-10 line 175–176 does this ("all p > 0.43"), but sub-08 null ROIs do not.
- Line 175 "Sub-09 showed significantly elevated disparity specifically at V1 (p=0.007)" — **OK**.
- Line 176 "no significant elevation at any ROI (all p > 0.43)" — **OK**.
- Line 186 "Permutation tests of the …model… fit sub-09 at V1 (p=0.026) but not sub-08 at V2 (p=0.179)" — **OK**.
- Line 196 (Fig 3 caption title) "significantly elevated color representation disparity" — paired with p=0.040/0.007. **OK**.
- Line 219 (Fig 3 caption) "significance markers" — descriptive. **OK**.
- Line 242 "the 2-component model reached significance for both" — accompanied by p=0.004 and p=0.035. **OK**.

No bare `significant` in narrative sense. **Tier C significant-audit: CLEAN.**

Other Tier C words:
- Line 246 "clear ridge structure" — vague (`clear`). Minor.
- Line 256 "clear ridge structure" — same instance, same minor.
- Line 318 "stricter criterion than Spearman ρ" — comparative; operationalized in following clause. OK.
- Line 332 "asymmetric per-color signature" — vague; OK because preceding numerics define it.
- No `faithful`/`meaningful`/`robust`/`realistic`/`accurate`/`effective`/`large`/`small`/`principled` unaccompanied.

### Tier D
- Line 256 `clear ridge structure` — borderline self-presentational. Minor.
- No `elegant`/`principled`/`unified`/`important`/`surprising`. **CLEAN.**

## 3. §20 Citation audit (Results-relevant)

- Line 32–33 `crawford1998` + `schuett2023` (single-case framing in Participants). **OK — method origin + recent application; legitimate dual cite.**
- Line 84 `bosten2019, boehm2014` (CVD above-threshold identification). **OK — paired primary citations for an empirical claim.**
- Line 105 `brouwer2009` (replication claim). **OK — primary, method/replication origin.**
- Line 262 `emery2021` (β_s comparison). **OK — primary, paired with explicit no-convergence caveat.**

No 5+ stacks. No general-claim citations in Results. Specificity matches throughout. **§20 CLEAN.**

Citation gap candidate (Tier 2 minor):
- Line 153 "Per-hue Crawford & Howell tests (one-tailed, uncorrected)" — multiple-comparison stance is asserted but not citation-anchored. Methods should cover; if not, brief reference here is warranted.

## 4. §24 Results-specific issues

### Statistical reporting completeness
- **Lines 81 / 137–138**: HC-to-HC vs HC-to-CVD pooled — p=0.668, Mann–Whitney U, n's given. **Missing: U statistic value and effect size (rank-biserial r or Cliff's δ).** §11/§24 violation.
- **Line 83**: "Crawford & Howell t-test… p=0.142" at hV4 — **no t-value, no d** for this null. §11 violation.
- **Line 101**: HC hV4 LOCO p_perm=0.044 — **missing permutation N (cf. line 246 lists 40,320; here unstated). No effect size (d or η²) for HC group-level LOCO above chance.** §11 violation.
- **Lines 107–110**: Sub-08 t=−1.58, p=0.082 — no d (since C&H reports d = |t|·√(n/(n+1)) ≈ 1.48 for n=7). Sub-09 t=−2.48, p=0.024 — no d. §11 violation in Results body; Fig 2C caption (line 154) does give d for per-hue but not for the group adj_acc test.
- **Per-hue tests (lines 113–115, 153–155)**: d, p given. **OK** but missing CI.
- **Line 173**: Sub-08 V2 disparity p=0.040 — no t, no d. §11.
- **Line 175**: Sub-09 V1 p=0.007 — same. §11.
- **Line 186–187**: ΔRDM model fits p=0.026 / p=0.179 — no effect size for the permutation correlation (typically Spearman ρ_obs). §11.
- **Lines 244–246**: 2-comp ρ_V4=0.88, p=0.004; ρ_V4=0.69, p=0.035 — **ρ IS the effect size**. **OK**.
- **Lines 327–329**: filter ρ_V4=0.62, 0.50, l_top-K=0, 0.5 — descriptive, p not reported per stated descriptive-only stance. **OK consistent with §24 framing.**

### Sub-09 EXPLORATORY framing
- **Project-rule violation (Serious)**: User instructions specify "Sub-09 framing = EXPLORATORY ONLY (p=0.035 + baseline_sp confound). Manuscript must say 'proof-of-concept, requires replication'."
- Draft text **does NOT** flag sub-09 as exploratory or proof-of-concept. Lines 230–298 (Fig 4) and 301–395 (Fig 5) treat sub-08 and sub-09 symmetrically. The only relevant hedge is the single-case framing at lines 31–33 (covers both). **No "exploratory" or "proof-of-concept" or "requires replication" label anywhere for sub-09 specifically.**
- Specifically missing: a sentence near line 246 or 329 stating that sub-09 p=0.035 is exploratory and the corresponding filter is proof-of-concept pending Phase 3 JND validation.

### HC FPR acknowledgement
- Lines 339–340 and 391–393: HC FPR=100% under label-permutation explicitly stated; "specificity is reported descriptively only." **Present in Results — meets user requirement.**

### Stale Fig 5 numbers (pre_draft) vs Phase 2 closure canonical
**Highest-priority check — RESULT: NO stale numbers found.**

Pre_draft Fig 5 numerics (46.3°, 20.1°, cosine sim=0.55, 4/8 opposite) are **absent**. Draft uses Phase 2 closure canonical exclusively:
- sub-08 (β_s, β_c) = (44°, +28°), norm=52.2°, ρ_V4=0.62, l_top-K=0 (lines 326–327, 375–377).
- sub-09 (30°, +46°), norm=54.9°, ρ_V4=0.50, l_top-K=0.5 (lines 328–329, 378–379).
- HC LOO range [49.0°, 65.3°] (lines 337, 390–391).
- V4-CCC + λ·l_top-K loss with λ ∈ [0.25, 2.0] (lines 314–316, 388–389).
**Phase 2 closure alignment: PASS.**

However, **stale pre_draft numbers persist in §6.5 (Fig 4)**:
- Lines 244–245: 2-comp β_s=38°, β_c=−14° (sub-08); β_s=6°, β_c=−22° (sub-09). These are the **LOCO-ρ argmax** numbers, not the Phase 2 closure canonical. The draft is internally consistent because §6.5 explicitly states (lines 252–254): "these LOCO-ρ argmax parameters establish that the 2-component model class captures the phenomenon; the operating point used for filter selection is refined under a stricter loss in Section 6.6." **The two parameter sets coexist on purpose.** This is defensible but creates risk: the reader sees four numbers per subject (Fig 4 caption: 38/−14 vs Fig 5 caption: 44/+28) without a side-by-side table.

### Over-interpretation in Results (belongs in Discussion)
- **Lines 86–87**: "the representational substrate on which a corrective filter could act is present" — implication/interpretation. Acceptable per §24 ("interpret in Results when needed") but borderline.
- **Lines 178–180**: "is inconsistent with a shared group-level gain mechanism" — interpretation tied to data, OK in Results.
- **Lines 188–190**: "geometric distortion measured at the population-code level is complementary to, not redundant with, the LOCO-based functional characterisation" — interpretation, OK.
- **Lines 261–266**: Emery 2021 grounding — interpretation but carefully hedged ("not as parameter-value convergence claims"). OK.
- **Lines 355–357**: "A correction optimised for one participant's geometry would move several hues in the wrong direction for the other participant, motivating individual-derivation." — interpretation/implication. **Borderline Discussion material; acceptable as it directly motivates the filter design choice.**

## 5. §26 Checklist (Results-relevant)

- [✓] §24 Each result answers a prior question — §6.2/§6.3/§6.4/§6.5/§6.6 each open with a question or motivation.
- [✓] §24 Each figure = one logical step — Fig 2 (discrimination/interpolation), Fig 3 (geometry), Fig 4 (model fit), Fig 5 (filter). Clear.
- [✗] §11 Numeric Δ has baseline + metric + dataset — **multiple p-values without effect sizes/CIs** (see §4 above). Baseline + metric + dataset are present; effect sizes are inconsistent.
- [✗] §9 Observation/interpretation/implication separated — ¶ at lines 107–121 mixes observation (sub-08/09 numbers), pattern interpretation (S-cone intermediate), and implication (LOCO–JND concordance → functional phenotype). Split recommended.
- [✗] §7 One role per paragraph — same paragraph (107–121) mixes group impairment + per-hue + JND concordance.
- [✓] §8 Topic sentence first — every paragraph opens with the claim.
- [✓] §17 No zig-zag — figures and ROIs follow consistent order V1→hV4.
- [N/A] Figure ordering matches Methods ordering — Methods not in scope here; assumed checked elsewhere.

## 6. Priority summary

**Fatal**
1. **Sub-09 exploratory framing absent** (§4 above; project rule). Add a sentence near line 246 (Fig 4 ¶) AND line 329 (Fig 5 ¶) stating sub-09 result is exploratory / proof-of-concept pending Phase 3 JND replication. **Fix order: 1st.**

**Serious**
2. **Effect sizes missing alongside p-values** (lines 81, 83, 101, 110, 173, 175, 186). Add d (Crawford–Howell), permutation null ρ-distribution summary, or Cliff's δ where applicable. §11 + project rule. **Fix order: 2nd.**
3. **§7/§9 paragraph split at lines 107–121.** Split into ¶C (group-level adj_acc impairment) + ¶D (per-hue S-cone pattern + LOCO–JND concordance) per the intended outline. **Fix order: 3rd.**
4. **Permutation N inconsistently reported.** Line 101 (HC group LOCO p_perm=0.044) lacks N; line 246 gives 40,320. Add N=… everywhere. **Fix order: 4th.**

**Minor**
5. **Sub-08 null-ROI disparity p's** missing from line 174–175 ("no significant elevation at V1, V3, or hV4" — supply "all p > X").
6. **Line 246 "reached significance"** — replace with "predicted observed vulnerability above the permutation null (sub-08 ρ=0.88, p=0.004; sub-09 ρ=0.69, p=0.035)." Minor Tier-C polish.
7. **Lines 246, 256 "clear ridge structure"** — drop "clear"; rely on Fig 4C.
8. **Fig 4 caption/Fig 5 caption coexisting parameter sets** (38°/−14° vs 44°/+28°) risks reader confusion. Add a one-line note in Fig 5 caption: "Operating point differs from Fig 4 LOCO-ρ argmax because the composite loss penalizes amplitude mismatch in addition to rank."
9. **HC FPR mentioned twice** (lines 339–340 and 391–393); fine but consider consolidating to the body once and a brief caption note.
10. **Line 153 multiple-comparison stance** ("uncorrected, one-tailed") — make sure Methods §23 covers this; flag here is fine.

**Notes on PASS items**
- Phase 2 closure canonical numbers (44°/+28°, 30°/+46°, 52.2°, 54.9°, V4-CCC + λ·l_top-K, [49.0°, 65.3°]) **all match** the 2026-05-12 update.
- HC FPR=100% acknowledged in Results (lines 339–340, 391–393) — meets user requirement.
- No stale pre_draft Fig 5 numbers (46.3°, 20.1°, cosine=0.55) found.
- §19 Tier A/D: clean. Tier C `significant` audit: all instances accompanied by p/test.
- §20 citations: clean, no 5+ stacks.
