# Revision Report — Figure Captions — 2026-05-13

Target: `docs/PAPER/Figures/FIGURE_CAPTIONS.md` (80 lines)
Cross-checked: `fig{1..5}_notes.md`
Rules: §13, §19, §20, §11, §26

> **Cross-section note (from Results review)**: Results §6.5 (Fig 4) *intentionally* uses Phase A LOCO-ρ argmax (β_s=38°/−14°, 6°/−22°) as the model-class-establishment step, then refines to Phase 2 closure canonical (44°/+28°, 30°/+46°) in §6.6 (Fig 5). So the Fig 4 caption Phase A numbers are *not* stale — they are deliberate. The Fig 5 caption "8/8 exact + mean |δ| 46.3°/20.1° + cosine 0.55" **IS stale** and must be updated to Phase 2 closure canonical.

## 1. Reverse outline (per figure)

### Fig 1 (lines 6–8)
- Caption claim (1 sentence): "The study uses 8 isoluminant DKL hues and a 3-stage pipeline (Stage A SRM → LORO/LOCO decoding → 2-component model + pre-image filter) on 7 HC and 3 CVD subjects."
- [intended: experimental paradigm and pipeline — **match Y**]

### Fig 2 (lines 12–18)
- Caption claim: "LORO discrimination is statistically indistinguishable HC vs CVD (p=0.668); LOCO interpolation at hV4 is significantly impaired for sub-09 (p=0.024); blue and purple hues show the largest per-hue deficits."
- [intended: discrimination preserved, only interpolation impaired — **match Y for content, but title is the only place "but" appears**. Caption itself does not explicitly state the **contrast** as a takeaway sentence; it lists results panel-by-panel.]

### Fig 3 (lines 22–26)
- Caption claim: "ΔRDM at primary ROI (sub-08 V2, sub-09 V1) shows individually-localized geometric distortion; absolute disparity is elevated for sub-08 at V2 (p=0.040) and sub-09 at V1 (p=0.007); sub-10 within HC band."
- [intended: "idiosyncratic distortion" — **partial match**. Title says "distinct ROI" (factual) but not "idiosyncratic"; the pre_draft term is intentionally deferred per line 80 of the file.]

### Fig 4 (lines 30–36)
- Caption claim: "A 2-component model (retinal β_s + cortical β_c) predicts per-hue LOCO vulnerability at hV4 for both CVD subjects (sub-08 ρ=0.88, p=0.004; sub-09 ρ=0.69, p=0.035), with parameters at (38°, −14°) and (6°, −22°)."
- [intended: model class + win over Machado — **partial**. The caption does present 2-comp vs Machado side-by-side in panel B, but does NOT state the win as a takeaway. Panel B caption (line 34) is descriptive: it reports both ρ values for both models without verdict. For sub-09 it shows Machado ρ=0.76 > 2-comp ρ=0.69 with no reconciliation, openly flagged as deferred in line 79.]
- **Parameter set (38°/−14°, 6°/−22°): correct for §6.5 model-class establishment per Results §6.5 framing.**

### Fig 5 (lines 40–46)
- Caption framework: **STALE — Phase A 2-comp, NOT Phase 2 closure canonical (2026-05-12)**.
- Caption claim: "The 2-component pre-image is exact (8/8) for both subjects; Machado fails for sub-09 via arc collapse; filter profiles are individually distinct (cosine 0.55, opposite signs in cyan→magenta arc)."
- [intended: **Phase 2 canonical — sub-08 (44°, +28°), sub-09 (30°, +46°), V4-CCC + λ·l_top-K composite loss, 4/8 and 3/8 exact** per fig5_notes.md "Phase 2 canonical adoption — 2026-05-12 (CURRENT)". **STALE — major drift.**]

### Fig 6
- **Absent** from FIGURE_CAPTIONS.md. Task brief lists Fig 6 (behavioral filter validation, "PENDING Phase 3"). No stub, no flag.

## Drift vs intended figure roles

| Fig | Drift |
|---|---|
| 1 | None |
| 2 | Mild — takeaway not stated as a sentence (only in title) |
| 3 | Mild — "idiosyncratic" intentionally deferred (line 80) |
| 4 | Moderate — model-class win not stated; sub-09 Machado>2-comp deferred |
| 5 | **CRITICAL — Fig 5 caption reflects Phase A 2-comp (β_s 38°/6° — *also* note Fig 5 caption text uses 8/8 exact + mean |δ| 46.3°/20.1° + cosine 0.55), not Phase 2 closure canonical (sub-08 (44°, +28°), sub-09 (30°, +46°), 4/8 and 3/8 exact, V4-CCC + λ·l_top-K). fig5_notes.md §"Phase 2 canonical adoption — 2026-05-12 (CURRENT)" explicitly supersedes; FIGURE_CAPTIONS.md was not updated.** |
| 6 | **Missing entirely** |

## 2. §19 Vocabulary scan

### Tier A (NEVER without explicit evidence)
- Line 14 / 24 / 26 / 34: `significantly` — paired with p-values throughout, acceptable usage (Tier C operationalized).
- Line 40 (Fig 5 title): "**exact** for both CVD subjects" — borderline. Mathematical claim, supported by "maximum residual < 0.001°" in line 42. OK under Phase A framing — but **becomes FALSE under Phase 2 canonical (4/8 and 3/8 are not "exact for both")**.
- No `novel`, `first`, `comprehensive`, `outperforms`, `proves`, `cannot`, `always`, `never` detected.

### Tier B (untestable verbs)
- Line 8: "**assessed** discrimination and interpolation capacity" — "assessed" is borderline (cousin of "investigate"). Acceptable since metrics follow immediately.
- Line 8: "**decomposed**" — concrete, OK.
- Line 8: "**yielded**" — concrete, OK.
- Line 30 (Fig 4 title): "**predicts**" — concrete + numbers, OK.

### Tier C (operationalize vague adjectives)
- Line 12 (Fig 2 title): "**selectively impaired**" — "selectively" is unoperationalized. Replace with "impaired at hV4 LOCO but not LORO". The body of the caption supports the contrast but the word "selectively" itself does no work.
- Line 22 (Fig 3 title): "**significantly elevated**" — operationalized by p-values in (B). OK.
- Line 40 (Fig 5 title): "**individually distinct**" — operationalized by "cosine = 0.55" + "opposite signs hues 5–8" in (C). OK under Phase A; **must be re-operationalized under Phase 2 canonical**.
- Line 46: "**opposite signs**" — concrete. OK.

### Tier D (generous self-praise)
- None detected. Captions are admirably restrained.

## 3. §13 Caption-specific issues

### Takeaway vs description

- **Fig 2 caption — DESCRIPTIVE**. Panels A/B/C each report numbers but never assert the cross-panel takeaway. The title carries "preserved but selectively impaired", but the body reads as three independent panel descriptions.
  Quote (line 14): *"n.s.: HC-to-HC vs HC-to-CVD cross-subject LDA generalization, all ROIs pooled..."* — purely descriptive.
  Proposed fix: add a final summary sentence: *"Together, panels A–B show that color discrimination (LORO) is statistically indistinguishable between HC and CVD across V1–hV4, whereas color interpolation (LOCO) is selectively impaired at hV4 in sub-09 and (at trend level) sub-08."*

- **Fig 3 caption — TAKEAWAY PARTIAL**. Title carries the claim ("at a distinct ROI"). Body reports stats. The note that 3A and 3B are independent measures is important and well-placed. Acceptable.

- **Fig 4 caption — TAKEAWAY HEAVY IN TITLE, ABSENT IN BODY**. Title (line 30) carries the win statement with both ρ values. But Panel B description (line 34) presents 2-comp and Machado bars without a verdict, and sub-09 Machado ρ=0.76 > 2-comp ρ=0.69 is left dangling.
  Proposed fix: after the bar-encoding sentence, add: *"Although sub-09 Machado ρ=0.76 exceeds 2-component ρ=0.69, the 2-component model is preferred on dual-criterion validation (LOCO + exact pre-image; see Fig 5) and biological grounding."*

- **Fig 5 caption — TAKEAWAY-DRIVEN but possibly false**. Title (line 40) "exact for both CVD subjects" is the takeaway. Under Phase A this is true; **under Phase 2 closure canonical it is false** (4/8 sub-08, 3/8 sub-09). See §4 below.

### Axes / metrics / dataset clarity

- **Fig 2 (B) caption (line 16)**: "Adjacent accuracy: proportion of predictions within ±1 hue step (0–1; higher = better)" — good, axes defined.
- **Fig 2 (A) (line 14)**: "Leave-one-run-out (LORO) discrimination accuracy (LDA, 8-class, SRM-aligned)" — good. But y-axis units / range not explicit. Reader infers proportion correct from "1/8 = 0.125".
- **Fig 3 (A) (line 24)**: "ΔRDM = RDM_CVD − mean RDM_HC-LOO" — defined. Colormap saturation (±1.0 clipped at 80%) NOT in caption; only in fig3_notes.md line 33. Minor self-containment gap.
- **Fig 4 (C) (line 36)**: parameter landscape colormap "RdBu_r (blue = low ρ; red = high ρ)" — good, but vmin/vmax not given. Add "(vmin=−0.5, vmax=+0.90)" from fig4_notes.md line 23.
- **Fig 5 (A) (line 42)**: "Hue correction magnitude (|δθ|) at each stimulus position" — y-axis units (degrees) implicit. Add "in degrees".

### Self-containment

- Fig 5 caption uses "pre-image" without definition. A reader unfamiliar with inverse mapping would need the body. Add a parenthetical at first use: "the exact pre-image (stimulus-space input that maps to the HC-target representation under the fitted 2-component distortion)".

## 4. Project-specific checks

### Fig 5 framework: **STALE (Phase A)**, not Phase 2 closure canonical (2026-05-12)

Stale numbers in FIGURE_CAPTIONS.md Fig 5 (cross-check vs fig5_notes.md §"Phase 2 canonical adoption"):

| Item | FIGURE_CAPTIONS.md says | Phase 2 canonical (fig5_notes.md, MEMORY) |
|---|---|---|
| Fig 5 (A) line 42 | mean |δ| sub-08=46.3°; sub-09=20.1° | sub-08 filter norm 52.2°; sub-09 54.9° |
| Fig 5 (A) line 42 | "Both subjects: 8/8 pre-images exact (maximum residual < 0.001°)" | sub-08 4/8, sub-09 3/8 under composite loss |
| Fig 5 title line 40 | "The 2-component pre-image filter is exact for both CVD subjects" | **factually false under canonical** |
| Fig 5 (B) line 44 | "2-component pre-image maps each stimulus to a distinct corrected position across the full hue circle (8/8 exact)" | not "8/8 exact" anymore |
| Fig 5 (C) line 46 | cosine similarity = 0.55 | computed for Phase A vectors; canonical filter cosine not stated |

Loss function:
- Caption (Fig 5) implies L_LOCO ρ argmax.
- Canonical loss: **V4-CCC + λ·l_top-K composite, λ ∈ [0.25, 2.0], +0.1·Tikh**, with selection rationale = "loss-function semantics (CCC = rank+scale; top-K = identity), not behavioral validation".

**Verdict**: Fig 5 caption reflects a superseded framework. The figure-asset metadata in fig4_notes.md line 33 still reports Phase A values (38°/−14°, 6°/−22°) for Fig 4 — confirm with user whether to (a) regenerate Fig 5 PNG/PDF under canonical Phase 2 closure parameters, or (b) keep figure images as Phase A and rewrite captions to disclose the framework split.

### Sub-09 EXPLORATORY flag

- Required per task brief: any caption asserting sub-09 should mark EXPLORATORY.
- Present in: **NONE**. No "exploratory", "tentative", "preliminary", "case-study", or "N=1 protan" qualifier anywhere in lines 6–46.
- Fig 2 (line 16) and Fig 4 (line 30, 34) make sub-09 claims with p-values but no exploratory qualifier.
- **Missing — should be added** at minimum to Fig 4 title (sub-09 Machado>2-comp tension) and Fig 3 disparity claim.

### HC FPR (7/7 = 100%) qualifier

- Required: any caption asserting hV4 LOCO specificity must qualify with HC FPR.
- Present in: **NONE**.
- Fig 4 title claim ("predicts hV4 LOCO vulnerability ... sub-08 p=0.004; sub-09 p=0.035") is exactly the kind of specificity claim that MEMORY entry "HC Specificity + Baseline Δρ Diagnostic (2026-04-11)" warns about: "HC LOCO FPR = 7/7 (100%) under label-permutation null; 2component=100%, rc=71%, machado=43%."
- Fig 4 caption does not disclose that 7/7 HCs also yield label-permutation significance under the 2-component model. **This is a specificity claim made without a specificity caveat. Must add.**
- Suggested addition to Fig 4 caption: *"Note: under HC label-permutation null (Crawford-Howell-style LOO-HC controls, n=7), the 2-component model achieves nominal significance for 7/7 HCs; these p-values are therefore descriptive fits of LOCO vulnerability geometry, not specificity statements distinguishing CVD from HC."*

### Terminology consistency

- "hV4" used throughout (good). No "V4" leakage in body text. (Note: on-disk dir is V4 per CLAUDE.md §6, but captions correctly use hV4.)
- "LOCO" vs "LORO" — consistent.
- "adjacent accuracy" (Fig 2) vs "ρ" / "Spearman ρ" (Fig 4) — different metrics, used in different panels, both correctly named. OK.
- "CVD" defined inline (line 14 "deutan CVD") but never spelled out ("color vision deficiency") on first use anywhere. Should be defined in Fig 1 caption.
- "DKL" defined in Fig 1 (line 8) — good. "SRM" used line 8 with full name "Shared Response Modeling" — good. "LDA" line 14, "LORO"/"LOCO" line 14/16 — defined inline.

### Notation defined inside caption

- β_s and β_c: defined in Fig 1 (line 8) parenthetically. Re-defined more fully in Fig 4 (C) (line 36). OK.
- |δθ|: used in Fig 5 (A) line 42 without prior definition in the caption set. The Fig 1 caption mentions "pre-image of the estimated distortion yielded a stimulus-space filter" but never names δ or δθ. Add: "(|δθ| = absolute hue correction magnitude in degrees, computed as the pre-image of the per-subject 2-component distortion)".
- ρ in Fig 4: defined as Spearman in (B). Used in (C) as "Spearman ρ" again. OK.
- Crawford & Howell (1998): full citation given at first use line 16. Good.

## 5. §26 Checklist (figure-relevant)

| Item | Status | Note |
|---|---|---|
| §13 Each caption states takeaway | ✗ | Fig 2 body is descriptive; Fig 4 panel B leaves Machado>2-comp tension unresolved; Fig 5 takeaway is **factually wrong** under canonical. |
| §13 Axes/metrics/dataset clear | ~ | Mostly yes; minor gaps: Fig 5 (A) units, Fig 4 (C) vmin/vmax. |
| §11 Numeric values have baseline + metric + dataset | ✓ | Almost all p-values include test name and df proxy. |
| §4 Terminology consistent | ✓ | hV4 used throughout; LORO/LOCO consistent. |
| §6 Notation defined | ~ | β_s, β_c defined. δθ used in Fig 5 (A) without prior in-caption definition. |
| §3 Pronouns/antecedents unambiguous | ✓ | No floating "this" or "it" detected. |
| Sub-09 EXPLORATORY flag where required | ✗ | Absent everywhere. |
| HC FPR qualifier where required | ✗ | Absent. Critical for Fig 4 and Fig 5 specificity claims. |
| Fig 5 reflects Phase 2 closure canonical | ✗ | **STALE — Phase A 2-comp values throughout. CRITICAL.** |

## 6. Priority summary

### FATAL (block submission)
1. **Fig 5 caption (lines 40, 42, 44, 46) reports stale Phase A 2-component parameters and exact-pre-image counts.** Phase 2 closure (2026-05-12, fig5_notes.md §"Phase 2 canonical adoption — CURRENT") supersedes: sub-08 (44°, +28°), sub-09 (30°, +46°), 4/8 and 3/8 exact under V4-CCC + λ·l_top-K composite loss. Title "exact for both CVD subjects" is no longer true. **Also: the figure assets (fig5_*.png/pdf) may still encode Phase A — confirm with user whether to regenerate Fig 5 or rewrite captions to live with Phase A assets and disclose the framework split.**

### SERIOUS (must fix before submission)
2. **HC FPR 7/7 qualifier missing** from Fig 4 caption. Per MEMORY 2026-04-11, the 2-component model has 100% HC false-positive rate under label-permutation null — Fig 4 title's specificity-flavored claim cannot stand without that caveat.
3. **Sub-09 EXPLORATORY flag absent** from Fig 2 (B), Fig 3, Fig 4. N=1 protan with mixed model-fit evidence requires the qualifier.
4. **Fig 4 (B) Machado>2-comp for sub-09 unresolved in caption.** Per §13 self-containment, the caption must reconcile its own panel; current decision to defer to Results text (line 79) violates §13.

### MINOR (polish)
5. **Fig 2 caption lacks an explicit takeaway sentence**; title carries the contrast but body reads as panel-by-panel description (§13 violation).
6. **"Selectively" in Fig 2 title** (line 12) is Tier C unoperationalized; replace with "at hV4 LOCO but not LORO" or similar.
7. **Fig 1 caption never spells out "color vision deficiency"** on first use of CVD.
8. **|δθ| not defined in-caption** in Fig 5 (A); add one-clause parenthetical.
9. **Fig 4 (C) colormap range** (vmin=−0.5, vmax=+0.90) missing.
10. **Fig 3 (A) colorbar saturation** (±1.0 at 80% of max) missing from caption.
11. **Fig 6 absent.** Either add a stub "Figure 6 — Behavioral validation of personalized filter (Pending Phase 3)" or document the absence in the revision log.

### Recommended fix order
1. Resolve Fig 5 framework question with user (regenerate vs disclose split). **No Fig 5 caption fixes are valid until this is decided.**
2. Once framework chosen, rewrite Fig 5 (A/B/C) with canonical numbers (or Phase A + framework note).
3. Add HC FPR caveat + sub-09 EXPLORATORY flag globally (one sentence each per relevant caption).
4. Fix Fig 4 (B) Machado tension reconciliation inside caption.
5. Add Fig 2 takeaway sentence; replace "selectively" with operationalized phrasing.
6. Tier C polish: in-caption definitions for |δθ|, CVD spelled out, axis ranges.
7. Add Fig 6 stub or revision-log entry.
