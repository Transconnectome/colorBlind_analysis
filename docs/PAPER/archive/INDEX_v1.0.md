# colorBlind — Full Index (master narrative + paragraph drafts, v1.0 / 2026-05-01)

> Companion to `INDEX_v1.0_meeting.md` (logical-flow summary). This file is the source-of-truth working draft: paragraph-level expansion, exact statistics, file/asset pointers, and audit appendices.
>
> **Cadence**: revise this file before each PI meeting; copy compressed bullets into `INDEX_v1.0_meeting.md`. The decision-log archive is `PLAN_ToC.md` (frozen at v1.0 cut-over; do not append further — append to §X of this file instead).
>
> **Version line** (extend at the bottom of the file in §X):
> - v1.0 (2026-05-01): first INDEX cut. Locks Results §R-1..§R-6 restructure (LOCO+LORO combined, SRM ΔRDM repositioned, HC FPR promoted, phenotype dropped). Inherits PLAN_ToC §9.1 locked decisions (eLife primary, case-study framing, n=2 effective CVD).
> - **v1.1 (2026-05-04)**: framework reconciliation with `future_phase2_filter_optimization/CLAUDE.md` §0 (locked 2026-05-03). Adds §0 Framework Decision (specificity-as-descriptive lock, no selection-rule reformulation). Removes closed-testing rule (Machado→R+C) — replaced by per-subject behavioral-PASS-overrides-LOCO. Fixes Sub-08 R+C `g=+2.25 → g=−2.25` (sign error inherited from `results_v3.tex`). Sub-08 R+C structurally retired (behav §2 YG-C collapse). Sub-08 behavioral observed (2026-04-17, not preregistered). §R-6 4-pillar specificity defense reframed as descriptive disclosure. Adds §2.5 loss inventory (2026-05-03) and per-subject status table.

---

# §0 Framework Decision (READ FIRST — 절대 재논의 금지)

> **Source of truth**: `analysis/future_phase2_filter_optimization/CLAUDE.md` §0. This INDEX must remain consistent with that lock. Any narrative draft that violates §0 is invalid.

**Filter selection rule (locked)**: per-subject **LOCO-best descriptive fit + behavioral validation**.

- **Specificity is not a selection criterion.** HC FPR 100% (`hc_specificity/`), baseline_ρ confound (HC corr=−0.894), n=6 effective HC pool — all confirmed. Cycle 9–13 (13 cycles) tried selection-rule reformulations within the voxel-prediction L_LOCO measurement family; none improved specificity. **Specificity reporting is descriptive only** ("Sub-XX fit lies at the X-th percentile of HC distribution"); no p-value or FPR claim is made at the model-selection level.
- **Behavioral validation is the inferential anchor.** Sub-08 R+C → 2-component override (behav §3 PASS, 2026-04-17) is the precedent: behavioral PASS overrides LOCO-ρ ranking. Sub-09 behavioral pending; downstream paper claims gated on this.
- **Closed-testing within retinal family is rejected** (was in v1.0 §M-6c). The retinal-family hierarchy (Machado tested first → R+C if NS) cannot survive §0 because it implies a selection rule keyed to model significance; v1.1 replaces it with independent fits + behavioral override.
- **No new selection-rule variants.** `z_combined`, `cross-ROI`, `baseline_sp` regression, family-aware weighting — all closed in `action_plans/PLAN04`. INDEX must not propose new variants without explicit user-issued "override §0".
- **Three mechanistic classes (locked)**: Machado 1-way (retinal Δλ) / R+C (retinal + 1-DOF cortical gain) / 2-component (cortical β_s + β_c angular dilation). No additions.
- **Pre-image gate**: 8/8 exact (residual <1e-3°) required for filter eligibility; sub-08 and sub-09 both pass under 2-component.

**Implication for paper narrative**:

| Claim type | Allowed phrasing | Forbidden phrasing |
|---|---|---|
| Specificity | "Sub-08 hV4 LOCO ρ at the 95th percentile of HC LOO distribution (descriptive)" | "p < .05 vs HC", "CVD-specific signal", "model discriminates CVD from HC" |
| Model selection | "Per-subject LOCO-best fit; sub-08 final = 2-component (behavioral PASS); sub-09 = 2-component candidate (behavioral pending)" | "closed-testing", "Machado tested first then R+C if NS" |
| HC FPR | "Voxel-prediction L_LOCO under label-permutation reaches p < .05 in 7/7 HC for the 2-component family — an expected limit of an expressive model on n=8 colors; reported as a known descriptive limit, not a barrier to per-case interpretation when the model is fixed by behavioral validation" | "we defend specificity via 4-pillar argument", "the model is specific to CVD" |
| Inferential anchor | "Behavioral validation (sub-08 PASS, sub-09 pending) + cross-modal Emery 21.4° match are the validation channels" | "specificity inferred from convergent + behavioral", "single-case statistics establish CVD specificity" |

**Override procedure**: only the user can revisit §0 by issuing the literal phrase "override §0" at session start. Implicit reframing as "new approach" is not an override.

---

# Title

**Working title (eLife/precision-neuro voice, v1.0 recommendation)**

> Cortical color geometry in color vision deficiency: an individualized 2-component model and a bijective display-space inverse

**Alternative candidates**

1. *Neural geometry of color in color vision deficiency predicts individualized display correction* — punchier; only valid if Session-2 behavioral data supports the "predicts" verb.
2. *Color discrimination is preserved but continuous hue geometry is distorted in color vision deficiency: a neural basis for individualized display filters* — most descriptive; fits Curr Biol.

**Naming convention used throughout the paper**

- "Sub-08" (deuteranomalous) and "Sub-09" (protanomalous) — main analysis cohort.
- "Sub-10" (near-normal) — incidental control, Supplement only.
- HC = healthy controls (Sub-01..07; n=7).
- "2-component" model = angular dilation in opponent hue space with two parameters β_s (S-cone axis expansion) and β_c (confusion-axis rotation). Distinct from R+C (retinal Δλ + cortical gain g).

---

# Target Journal & Submission Strategy

| Rank | Journal | Format | WC | Figs | Case-study tolerance | Session-2 dep. | Fit |
|------|---------|--------|----|------|-----------------------|---------------|-----|
| 1 | **eLife** | Research Article | ~6,500 | 5–7 | High (precision-neuro friendly, open review) | Optional | ★★★★★ PRIMARY |
| 2 | Current Biology | Article | 5,000 | 5 | Medium (broad-impact framing helps) | Recommended | ★★★★☆ |
| 3 | Nature Communications | Article | ≤5,000 + Methods unlimited | up to 10 | Medium-High | Required | ★★★★☆ |
| ✗ | ~~PNAS~~ | — | — | — | n=2 below typical bar | — | dropped |
| ✗ | ~~Nat Neuroscience~~ | — | — | — | requires population mechanism | — | dropped |

**Submission order**: eLife → Current Biology → Nature Communications.

- **eLife rationale**: single-blind, open peer-review, public author-response — fits precision-neuroscience case-study story without forcing population-level rewrite.
- **Current Biology fallback**: reframe with Emery-matched β_s as mechanism + clinical translation hook.
- **Nature Communications tertiary**: requires 5-subject pre-registered replication (~3-month delay) and emphasis on bijective pre-image as mechanism+translation package.

**Behavioral validation strategy**:

- **Option B (preferred)**: include Session-2 fMRI + 2AFC JND + 8-AFC identification under 4 filter conditions (uncorrected / Akalin / R+C / 2-component) for both Sub-08 and Sub-09. ≤1-month timeline.
- **Option A (fallback)**: cut §R-5, retarget eLife Short Report (4,000 w, 4 main figs); abstract sentence 6 → "predicted JND gains, behavioral validation in preparation".

---

# Abstract (≤250 words)

**Target structure (6 sentences, locked)**

1. **Motivation** — Existing CVD filters (Brettel 1997 anomaloscope inversion, Machado 2009 cone-shift, Akalin 2025 algorithmic Daltonization, EnChroma) operate at the retinal stage; cortical-level consequences of CVD and individual variability are largely unaddressed.
2. **Gap** — Whether cortical color geometry is *specifically* distorted beyond retinal prediction, whether the distortion is individually patterned, and whether an explicit display-space pre-image of a cortical-space distortion model can be computed, all remain open.
3. **Approach** — 7 HC + 2 CVD (Sub-08 deutan, Sub-09 protan) fMRI × 8 isoluminant DKL hues × V1/V2/V3/hV4; SRM HC-only common space; forward encoder + LORO/LOCO; three nested cone-shift models (Machado / R+C / 2-component) under composite LOCO loss including a δ·L_rdm term; bijective pre-image search over 0–360°; same-day behavioral 2AFC JND + 8-AFC identification.
4. **Neural result** — In hV4, hue *discrimination* (LORO; HC=0.68±0.11, CVD=0.64±0.09, perm p>0.5 every ROI) is preserved while hue *interpolation* (LOCO; HC ρ=0.42±0.14, Sub-08 ρ=0.08, Sub-09 ρ=0.12) is impaired, replicating Brouwer & Heeger (2009) and extending it to CVD; SRM ΔRDM at V1 confirms geometric distortion (Sub-09 V1 p=0.026; Sub-08 hV4 LOCO p=0.004).
5. **Model result** — The cortical 2-component angular dilation is the only model yielding a **bijective pre-image** for both severity levels (8/8 hues exact, residual <0.001°); per-subject β_s of 20° (Sub-08) and 23° (Sub-09) bracket Emery et al. (2021)'s independently-measured 21.4° behavioral B-Y rotation in an unrelated cohort.
6. **Scope** — Filter selection is per-subject LOCO-best fit anchored by behavioral validation (sub-08 2-component PASS 2026-04-17; sub-09 pending); under label-permutation, voxel-prediction L_LOCO HC FPR is 7/7 for the 2-component family. **Specificity is therefore not claimed at the model-selection level; behavioral validation is the inferential anchor**, with cross-modal Emery 21.4° match as a complementary descriptive convergence.

**Keywords** (eLife allows 5): color vision deficiency, cortical representation, fMRI MVPA, shared response model, perceptual filter

---

# §1 Introduction (~1,000 words; v2 draft in `Introduction/introduction_v2.tex`)

> Style: precision-neuroscience voice from first paragraph. Crawford & Howell (1998) and Schütt et al. (2023) explicitly cited; n=2 framing introduced no later than §Intro-5.

## §Intro-1 — Filter state-of-the-art and its retinal-stage ceiling (~180w)

- **Para 1 — what current filters do**: Brettel et al. (1997) inverse-simulation, Machado et al. (2009) Δλ cone-shift, EnChroma spectral notch, Microsoft Windows color-filter API, and the most recent Akalin et al. (2025) algorithmic Daltonization (LMS matrix + HSV hue shift, judged by MobileNetV1 Ishihara classification). All operate on cone responses or display-space hue-rotation heuristics.
- **Para 2 — what they do not use**: none uses the user's perceptual or neural data; they assume a population-mean retinal model. Behavioral uptake is uneven (Gomez-Robledo 2018; Hassan & Crognale 2023; Almutairi 2022; Shen 2016 EnChroma trial — slight benefit but lower comfort) because retinal models cannot predict cortical outcome at the individual level.
- **Para 3 — adaptation caveat (Werner 2020)**: long-term filter wear induces perceptual learning that persists after filter removal — confounds same-day behavioral validation; we explicitly bound our same-day claims accordingly.

**Citations**: `brettel1997`, `machado2009`, `shen2016`, `akalin2025`, `werner2020`, `gomez2018`, `hassan2023`.

## §Intro-2 — Why a neural-basis reformulation (~200w)

> **PI note**: previously zero citations — biggest gap in v1.1. Now 6 anchors (PLAN_ToC §10.4).

- **Para 4 — biological substrate**: anomalous trichromacy arises from L/M opsin polymorphisms producing 2–12 nm spectral shifts (Neitz & Neitz 2011; Deeb 2005). The continuous-severity framework (Bosten 2019, "known unknowns of anomalous trichromacy") motivates per-subject parameterization rather than dichotomous deutan/protan classes.
- **Para 5 — cortical compensation evidence**: behavioral compensation for R-G contrast loss (Boehm 2014); McCollough-effect evidence of compressive nonlinear cortical encoding in anomalous trichromats (Robinson 2023); fMRI evidence of V2/V3 post-receptoral amplification compensating weaker LvsM signals (Tregillus 2021). Webster (2015) provides the visual-adaptation framework.
- **Para 6 — claim**: a filter optimized against *cortical* geometry should outperform retinal-only because the cortex — not the cone — generates perception. This re-orients filter design from cone-response inversion (the Brettel/Machado lineage) to cortical-representation inversion.

**Citations**: `neitz2011`, `deeb2005`, `bosten2019`, `boehm2014`, `tregillus2021`, `robinson2023`, `webster2015`, `isherwood2020`.

## §Intro-3 — Existing CVD neuroimaging gap, with SRM precedent (~220w)

> **PI annotation (Korean)**: "최근 연구 보완하기 — SRM 등" → addressed via new §Intro-3b.

- **Para 7 — what fMRI has tested in CVD**: activation magnitude (Rabin 2011; Wachtler 2003 — animal); Daltonism case showing hV4 *lacks* isolated color activity (Rina 2024); post-receptoral V2/V3 compensation inferred from BOLD (Tregillus 2021). None has tested the **representational geometry** of anomalous trichromacy at the per-subject level.
- **Para 8 — what fMRI has tested in healthy color**: forward-model LOCO interpolation revealed V4/VO1 as the locus of continuous hue interpolation (Brouwer & Heeger 2009); hV4 as a perceptual hub (Bannert & Bartels 2018); intermediate-hue selectivity (Kuriki 2015); V1 hue MVPA (Parkes 2009).
- **§Intro-3b — SRM precedent (NEW per PI annotation)**: the Shared Response Model (Chen 2015) and hyperalignment (Haxby 2011; Guntupalli 2016) preserve fine-grained individual differences (Feilong 2018). Most directly, **Bannert & Bartels (2025)** — *Color across Human Brains*, J Neurosci 45(42) — first applied SRM to cross-subject color decoding in healthy observers; this is our direct methodological precedent. Clinical small-N applications use SRM-adjacent frameworks (Byrge 2015 ASD; Hasson 2009; Mäntylä 2018; Frässle 2020).
- **Para 9 — gap statement (neutralized per redteam R4)**: SRM has been used for healthy color decoding (Bannert 2025) and for clinical small-N characterization (Byrge 2015, Hasson 2009). We apply this framework to CVD for the first time, combine it with Brouwer & Heeger's (2009) LOCO paradigm extended to CVD, and add a stimulus-space inverse filter. The paradigm itself is not new; the application to CVD geometry, single-case statistical inference, and end-to-end filter derivation is.

**Citations**: `brouwer2009`, `bannert2018`, `kuriki2015`, `parkes2009`, `rina2024`, `wachtler2003`, `rabin2011`, `chen2015`, `bannert2025`, `feilong2018`, `haxby2011`, `guntupalli2016`, `byrge2015`, `hasson2009`, `mantyla2018`, `frassle2020`.

## §Intro-4 — Discrimination vs interpolation, individuality (~220w)

- **Para 10 — discrimination is local, interpolation is global**: cortical color reviews (Gegenfurtner 2003; Conway 2018; Shapley 2011) and V1 hue tuning (Parkes 2009; Engel 1997 Nature) suggest that V1/V2 sustain category discrimination via local opponent contrasts. Continuous interpolation requires a structured manifold representation, observed in V4/VO1 (Brouwer & Heeger 2009; Brouwer 2013; Kuriki 2015; Bannert 2018).
- **Para 11 — individuality**: standard population-averaged fMRI washes out CVD idiosyncrasies (Feilong 2018; Finn 2020). SRM + Crawford-Howell (1998) single-case statistics + Schütt 2023's single-model-significance framework constitute the principled response.
- **Para 12 — substantive prediction**: Sub-08 (mild deutan) and Sub-09 (moderate protan) are expected to differ not only in average magnitude but in *which* per-pair distortions are largest — argues for per-subject vulnerability vector $\mathbf{v}\in\mathbb{R}^8$ rather than a scalar deficit score.

**Citations**: `gegenfurtner2003`, `conway2018`, `shapley2011`, `parkes2009`, `engel1997`, `kuriki2015`, `bannert2018`, `brouwer2013`, `feilong2018`, `finn2020`, `crawford1998`, `schuett2023`.

## §Intro-5 — Three questions, one filter (~200w)

> **PI annotation (Korean)**: "고려 — 2번이 중요한 이유: 필터 제작 가능성" → Q2 is the licensing premise for the filter; expand explicitly.

- **Para 13 — three questions** (revised v1.0):
  1. Is cortical color geometry distorted in CVD at the case level, and where in the V1–hV4 hierarchy?
  2. **Is the distortion selective for continuous interpolation (LOCO) while discrimination (LORO) is preserved? — *this dissociation is the substrate for a corrective filter, because LOCO failure pinpoints exactly which display-space hues are misrepresented and therefore correctable by stimulus-space pre-image inversion of a fitted distortion model.***
  3. Can the distortion be parameterized with a physiologically interpretable cortex-space model, inverted to a bijective display-space filter, and behaviorally validated?
- **Para 14 — preview**: we answer (1) at hV4 with LORO=preserved, LOCO=impaired; (2) yes, with LOCO impairment selectively localized while LORO is preserved, providing an actionable filter target; (3) the 2-component cortical model is the only candidate that admits a bijective 8/8 pre-image and matches Emery (2021)'s 21.4° external benchmark — and produces same-day behavioral JND reduction (R-5).

**Citations**: `crawford1998`, `schuett2023`, `kriegeskorte2019`, `finn2020`, `byrge2015`, `mantyla2018`, `frassle2020`.

---

# §2 Methods (~2,000 words; current draft `Methods/methods_streamlined.tex`)

## §M-1 Participants

- **HC**: 7 (Sub-01..07), self-reported normal color vision; written consent (Seoul Nat'l Univ. IRB-XXXXX).
- **CVD**: 2 main + 1 incidental (Supp).
  - Sub-08 (male, mild–moderate deuteranomalous): Ishihara 8/14 plates misread; 8AFC accuracy 0.71; confusion clustering on c2/c3 (orange/yellow) vs c7 (purple), mean confusion 28%.
  - Sub-09 (male, moderate–severe protanomalous): Ishihara 11/14 misread; 8AFC 0.62; confusion extended along the L-M opponent range with magenta (c8) outlier.
  - Sub-10 (male, near-normal deutan, Supp only): Ishihara 2/14 misread; 8AFC 0.88 — indistinguishable from HC. Excluded from main analyses per `future_phase2_filter_optimization/CLAUDE.md` rule 7 (behavioral follow-up infeasible at this severity).
- **Crawford-Howell single-case statement** (closes §M-1): given n=2 effective CVD, all CVD-vs-HC inferences below use Crawford & Howell's (1998) single-case modified t-statistics with leave-one-out HC reference; we make no group-level CVD claim.

**Citations**: `ishihara1917`, `crawford1998`, `schuett2023`.

## §M-2 Stimuli & fMRI experiment

- 8 isoluminant DKL hues (Derrington 1984): c1 red, c2 orange, c3 yellow, c4 green, c5 cyan, c6 blue, c7 purple, c8 magenta. Plus blank baseline.
- Stockman & Sharpe (2000) 2-deg cone fundamentals → DKL conversion.
- 6 runs × 8 colors × 2 reps × 4-sec block + jittered ITI; 3T Siemens; TR=1s; AP-PA pairs; in-task RSVP attention task at fixation (HC=CVD accuracy, no group difference).

## §M-3 Preprocessing & Procrustes alignment

- fMRIPrep (`method3_header_mi`); ROI defined retinotopically per subject (V1/V2/V3/hV4 dorsal+ventral; hV4 = "V4" on disk per `CLAUDE.md` §6).
- Within-subject Procrustes alignment of run-level β estimates (FIR-based), saved as `amplitudes_procrustes.npy` (shape `(6, 8, n_voxels)`).
- C010 amplitudes (server): `derivatives/full_dataset_C010/{subject}/{ROI}/amplitudes_procrustes.npy`.

## §M-4 SRM common space (HC-only)

- HC-only training (eliminates circularity): K = 4, 4, 3, 3 for V1, V2, V3, hV4 (per memory `SRM Configuration`; mean rank aggregation).
- Sub-07 hV4 has only 16 voxels in C010 → causes nan in correlation distances; report this as a methodological caveat in §M-4.
- LOO refs for HC disparity test; same LOO refs reused for CVD ΔRDM computation (Crawford-Howell-compatible).

**Citations**: `chen2015`, `feilong2018`, `bannert2025`, `haxby2011`, `guntupalli2016`.

## §M-5 Forward encoding + LORO/LOCO

- Encoder: ridge regression with generalized cross-validation (`ridge_gcv`); K=3 half-wave-rectified squared sinusoidal channels (FE-3 basis, retained per `Forward Model Final Status` 2026-03-11).
- LORO: leave-one-run-out; 5 train runs × 7 train colors × 8 test colors → classification accuracy + Spearman ρ between predicted and held-out responses.
- LOCO: leave-one-color-out; 7 train colors → predict held-out color → vulnerability vector $\mathbf{v}\in\mathbb{R}^8$ (one residual per held-out color).
- **Pooled-runs (memory `LOSO Zero-Shot`)**: ridge_gcv LOCO uses pooled runs (42 samples = 6 runs × 7 colors), NOT run-averaged.

**Citations**: `brouwer2009`, `kay2008`, `naselaris2009`.

## §M-6 (NEW) Cone-shift models, composite LOCO loss, and per-subject model selection

> **Section role**: introduces the three cortex-space distortion models, the loss form that fits them, and the **per-subject selection rule** keyed to behavioral validation (per §0 framework lock).

### §M-6a Three mechanistic classes (no additions allowed per §0)

- **Machado 1-DOF** (retinal only): single Δλ shift in L or M cone (Machado 2009); preserves the Ingling–Tsou opponent structure.
- **R+C 2-DOF** (retinal + 1-DOF cortical): Δλ + cortical opponent gain g of the form `rg' = rg_base + (1+g)·(rg_retinal − rg_base)`, single knob on the RG axis; zero DOF on YB axis (Tregillus 2021 inspiration; behav §2-1).
- **2-component 2-DOF** (cortex only): angular dilation in CIELab opponent space with β_s (S-cone axis expansion) and β_c (confusion-axis rotation). Two **independent** direction parameters — distinct from R+C's single RG knob.

### §M-6b Composite LOCO loss (canonical L_LOCO; voxel-prediction family)

- Form (memory `LOCO-Primary Filter Design`):
  $$L_{\text{LOCO}} = \alpha\cdot\frac{L_{\text{vuln}}}{4} + \beta\cdot\frac{L_{\text{rank}}}{2} + \delta\cdot\frac{L_{\text{rdm}}}{2} + \epsilon\cdot\frac{L_{\text{smooth}}}{32400}$$
  with α=1, β=δ=0.5, ε=0.1.
- $L_{\text{vuln}}$ = MSE(1 − voxel_pattern_correlation, observed vulnerability); $L_{\text{rank}}$ = 1 − rank correlation; $L_{\text{rdm}}$ = 1 − cosine(simulated ΔRDM, observed ΔRDM); $L_{\text{smooth}}$ = grid ridge.
- δ·L_rdm motivated by §R-2 ΔRDM evidence (descriptive geometric distortion → soft constraint coupling fit to RDM structure).
- Permutation test: 8! = 40,320 exact label permutations on Spearman ρ; one-sided p.
- **Loss inventory disclosure (§2.5 below)**: the canonical L_LOCO is one of 12 loss variants benchmarked on 7 HC + 2 CVD (`results/loss_inventory.{md,csv}`, 2026-05-03). No single-ROI loss reaches HC-vs-CVD distinct status for both CVD subjects under bootstrap rank-based emp_p ≤ 0.20; only `mw_jaccard_loss` at hV4 distinguishes both. This limits the loss form's standalone CVD-discrimination power and is reported as a descriptive limit (§D-6).

### §M-6c Per-subject model selection (replaces v1.0's closed-testing rule per §0)

- **Three classes fit independently** for each subject; no hierarchy, no model-significance gating.
- **Final filter model = behavioral PASS** (sub-08 = 2-component) **or LOCO-best with behavioral pending** (sub-09 = 2-component candidate; behavioral protocol scheduled per §M-9).
- **Sub-08 R+C is structurally retired** (behav §2 + §6 #2): R+C's 1-DOF RG knob with `(1+g) = −1.25` produces YG-C 4-way collapse (`c3 ≡ c4`, `c5 ≡ c6`, `protan-axis− ≡ sRGB C`). 2-component dissolves the collapse via independent β_s and β_c (behav §3 PASS 2026-04-17). R+C is reported in §R-3 as descriptive fit only — not as a candidate filter substrate.
- **Pre-image gate**: model is filter-eligible only if 8/8 hues admit exact pre-image (residual <0.001°) — both CVD subjects pass under 2-component.
- **Specificity is descriptive only** (per §0): we report each subject's fit as a position in the HC-LOO distribution, but make **no p-value or FPR-based selection claim**.

## §M-6.5 Loss inventory + HC sanity check (NEW v1.1, source: `future_phase2/CLAUDE.md` §2.5, 2026-05-03)

> **Section role**: discloses that the canonical L_LOCO is one of 12 loss variants benchmarked, none of which produces unambiguous HC-vs-CVD discrimination at the n=8-color / n=6-effective-HC scale. This is a methodological transparency disclosure required by §0 (selection-rule reformulation forbidden) and by redteam R6 (HARKing concern).

### §M-6.5a Test design
- 12 loss variants (single-ROI: `pearson_r`, `spearman_r`, `l_rank`, `l_mag`, `l_dir`, `sign_agree`, `norm_resid`, `l_topk_V1`, `l_topk_jaccard`; cross-ROI: `cycle12_cross_roi`, `cycle15_opt2_v4mwj_v1lrank`, `mw_jaccard_loss`).
- Bootstrap rank-based emp_p: fraction of 7 HC fits whose β_s/β_c norm exceeds the CVD norm; sig threshold emp_p ≤ 0.20.
- Sanity principle: a good loss should produce HC fits ≈ (0,0) and CVD fits ≠ (0,0) with low rank-based emp_p for both CVD subjects.

### §M-6.5b Top results (✓✓ = both CVD distinct)
1. **`cycle15_opt2_v4mwj_v1lrank` = 2·mw_jaccard(V4) + 1·l_rank(V1) + 0.2·Tikh** — overall winner.
   - sub-08 emp_p = 0.00 (perfect 0/6 HC above), sub-09 emp_p = 0.17 (1/6).
   - sub-08 (β_s=68°, β_c=−38°), sub-09 (β_s=44°, β_c=+54°).
2. **`mw_jaccard_loss` (V4 alone)** — sub-08 emp_p = 0.17, sub-09 emp_p = 0.17.
- ✓ one distinct (canonical L_LOCO family at single ROI): `pearson_r`, `spearman_r`, `l_rank`, `l_mag`, `l_dir`, `cycle12_cross_roi`, `cycle15_opt3`, `cycle15_opt4`.
- ✗ neither distinct: `l_topk_V1`, `sign_agree`, `norm_resid`, `l_topk_jaccard`.

### §M-6.5c Implications for paper narrative
1. **Canonical L_LOCO at hV4** is a ✓-one-distinct loss (sub-08 only). For sub-09, hV4-only is degenerate at (0,0) under several variants — only cross-ROI / mw_jaccard losses extract non-trivial parameters.
2. **Sub-09 cross-loss β_s disagreement** (6° canonical vs 44° mw_jaccard): a real measurement-family-dependent finding at 8-color resolution. **Cannot be resolved within the current data**. Behavioral protocol (§R-5b) chooses among candidates by behavioral PASS criterion.
3. **No reformulation rescues HC-FPR specificity** (per §0). The mw_jaccard loss reduces but does not eliminate HC overlap; this matches the §0 conclusion that specificity at the model-selection level is unattainable in the current measurement family.
4. **Reporting policy**: paper main text uses canonical L_LOCO with descriptive parameters per §R-3; §D-6 + §M-6.5 disclose the inventory and its implications without re-running selection rules.

---

## §M-7 (NEW) Pre-image filter derivation + bijectivity check

- Given fitted distortion D̂(θ), compute θ_in = argmin_θ ||D̂(θ) − θ_target||² over a 0–360° × 0.5° grid.
- Per-color residual reported; **bijectivity gate**: model is filter-eligible only if residual <0.001° for all 8 training hues.
- Off-training stability: report max |dθ_out/dθ_in| Jacobian over the full 0–360° hue circle; confirms monotonicity within protan/deutan-consistent sign arrangements (per redteam R5).
- Filter applied as HSV-rotation operating on the display LUT (Psychopy implementation for §M-Behavioral).

## §M-8 (short) HC specificity disclosure (descriptive only per §0)

> **Required by redteam R2 (FATAL) and §0 lock**. One-line pointer here; full descriptive disclosure in §R-6.

- Voxel-prediction L_LOCO under label-permutation reaches p<0.05 in 7/7 HC for the 2-component family; 5/7 for R+C; 3/7 for Machado (memory `HC Specificity + Baseline Δρ`).
- Per §0, this is reported as a **known descriptive limit** of an expressive 2-DOF model on n=8 colors — not as a barrier to per-case interpretation when the model class is fixed by behavioral validation.
- Inferential anchors (§R-6): behavioral validation (sub-08 PASS) + cross-modal Emery 21.4° match.

## §M-9 Behavioral validation (Session 2; conditional)

- Same-day post-scan: 2AFC JND (method-of-constants; 8 confusion-axis hue pairs identified per subject from §R-3 LOCO profile) + 8-AFC color identification.
- 4 filter conditions: (i) uncorrected, (ii) Akalin 2025 algorithmic baseline, (iii) R+C-derived filter, (iv) 2-component-derived filter. Block-randomized, 50 trials per pair × condition.
- Session-2 fMRI: same scanner protocol under each filter condition; quantify Δ-LOCO between filtered and uncorrected conditions.

## §M-Reproducibility

- Code: `analysis/future_phase2_filter_optimization/scripts/`; canonical SRM pipeline: `rerun_loo_consistent.py`; LOCO: `loco_baseline.py`; cone-shift fits: `step2c_retinal_cortical.py`, `loco_distortion_fit.py`; pre-image: `preimage_search.py` (+ `preimage_jacobian_check.py` to be added per §M-7).
- Data: `derivatives/full_dataset_C010` on server `node3`; behavioral data: `analysis/future_phase3_behavioral_analysis/`.

---

# §3 Results (~2,500 words; **revised structure 2026-04-30**)

> **Restructure rationale (vs `results_v3.tex`)**:
> - v3: phenotype / LORO / LOCO / fits / SRM ΔRDM / pre-image (6 sections; 2-component late, ΔRDM as auxiliary).
> - v1.0 INDEX: combined LORO+LOCO / SRM ΔRDM (descriptive) / fits (loss justified) / pre-image / behavioral / HC FPR (6 sections; 2-component as filter substrate, ΔRDM motivates loss).

## §R-1 (NEW) Discrimination preserved, interpolation impaired (LORO + LOCO combined)

> **Replaces v3 §R-1 (phenotype) + §R-2 (LORO) + §R-3 (LOCO)**. Phenotype demographics moved to §M-1. 8AFC kept as 1-line opener (case-axis confirmation).

### §R-1a Opening — case axis confirmed by 8AFC
> "Same-day 8-AFC identification of the eight scanner stimuli confirmed the Ishihara categorisation (HC accuracy 0.94 ± 0.04, Sub-09 = 0.62, Sub-08 = 0.71; chance = 0.125). Sub-08's errors clustered on c2/c3 vs c7 (red-green confusion); Sub-09's extended along the full L-M opponent range with magenta (c8) outlier."

### §R-1b LORO preserved — filter precondition
- HC = 0.68 ± 0.11; CVD = 0.64 ± 0.09 (mean ± SD across 6 runs); above 0.125 chance for every individual.
- Permutation NS at every ROI: hV4 p=0.668; V1 p=0.542; V2 p=0.611 (10,000 label permutations).
- **Filter precondition**: 8 stimuli individually distinguishable at the cortical level — substrate on which a filter could act is present (`bosten2019`, `boehm2014`).

### §R-1c LOCO impaired — filter target
- hV4: HC ρ = 0.42 ± 0.14 (Brouwer & Heeger 2009 replication); Sub-08 ρ = 0.08; Sub-09 ρ = 0.12 (near floor).
- Early visual cortex effects: V1 g=1.61, V2 g=1.85, hV4 g=1.34; all $p_{\text{perm}}$ < 0.03 (memory `LOCO/LORO Decoder Findings`).
- **Per-hue vulnerability is subject-specific** (gray bars in `fig1_panels_bcd.pdf`): Sub-08's largest errors lie on c2/c3 and c7; Sub-09's cluster on c5/c6 with c8 outlier.

### §R-1d Dissociation paragraph (key)
- Same forward model, same voxels, same CV → discrimination ≠ interpolation.
- This dissociation is the direct answer to Intro Q2 and the licensing premise for the filter: LOCO failure identifies *exactly which* display-space hues are misrepresented; LORO preservation guarantees a substrate on which to act.

### §R-1 Figure (F2, 2-panel side-by-side)
- (a) LORO bars × {V1, V2, V3, hV4} × {HC mean ± SD, Sub-08, Sub-09}.
- (b) LOCO bars or per-hue $\mathbf{v}$ profiles, same ROI grouping.
- Same y-axis scale, same color coding; dissociation visible at a glance.

## §R-2 (REPOSITIONED) SRM ΔRDM — descriptive geometric distortion

> **Moved from v3 §R-5 to §R-2**: reports geometric distortion before fits, motivating δ·L_rdm in the LOCO loss (§R-3). Avoids "LOCO-vs-ΔRDM dissociation" framing (memory `LOCO-Primary Filter Design` CRITICAL framing fix).

### §R-2a Procedure
- Voxel-space crossnobis distances among 8 hues → SRM-projected (HC-only K = 4/4/3/3 V1/V2/V3/hV4) → ΔRDM = RDM_CVD − mean(RDM_HC,LOO) per ROI per CVD subject.
- Citations: `schuett2023` (RSA noise normalization), `chen2015` (SRM), `bannert2025` (cross-subject color decoding precedent).

### §R-2b Per-subject ΔRDM findings (subject-specific)
- **Sub-09 V1 ΔRDM p = 0.026** (memory `Phase 2 Cone-Shift Pipeline v2`). LOCO at V1 was non-significant for Sub-09; ΔRDM captures distortion that LOCO misses.
- **Sub-08 V1 ΔRDM p = 0.179 (NS)**; Sub-08's signal is in LOCO at V1 (p=0.001) and hV4 (p=0.004) — *complementary* to Sub-09.
- → Per-subject divergence at the geometric level: confirms distortion exists but with different ROI fingerprint per subject.

### §R-2c β_s convergence preview
- When the 2-component β_s parameter is refit *directly* against V1 ΔRDM (LOCO-free), Sub-08 ≈ 20°, Sub-09 ≈ 23° (mean ≈ 21.5°).
- Bracketing Emery et al. (2021)'s 21.4° behavioral B-Y rotation in an unrelated cohort. Full discussion in §R-3 + §D-2.

### §R-2d Bridge to §R-3
- Geometric distortion exists ⇒ δ·L_rdm justifiable as a soft regularizer in the LOCO loss (next section).
- ΔRDM is *both* descriptive evidence (here) *and* a 0.2-weight term in §R-3's loss; this dual role is intentional and disclosed (Methods §M-6b).

### §R-2 Figure (F3)
- (a) HC-mean ΔRDM (zero-baseline)
- (b) Sub-08, Sub-09 individual ΔRDM heatmaps
- (c) per-pair bootstrap 95% CIs, sig-pairs annotated

## §R-3 (NEW PRIMARY FITTING) Cone-shift fits under composite LOCO loss + per-subject model selection

> **§0 alignment**: per-subject behavioral PASS overrides LOCO-ρ ranking. v1.0's closed-testing rule (Machado→R+C) is removed.

### §R-3a Loss form (recap from §M-6b)
- $L_{\text{LOCO}} = α·L_\text{vuln}/4 + β·L_\text{rank}/2 + \mathbf{δ·L_\text{rdm}/2} + ε·L_\text{smooth}/32400$, with δ=0.2 motivated by §R-2 evidence.
- All three model classes (Machado / R+C / 2-component) fit independently per subject; **no hierarchy**.

### §R-3b Sub-09 (moderate protanomaly) — descriptive fits
- **Machado** Δλ = 13.5 nm, ρ = 0.762, $p_{\text{perm}}$ = 0.018; within `neitz2011` 2–12 nm range (slight extension to moderate-severe boundary).
- **R+C** converged at g* = 0 → effectively reduces to Machado; no cortical augmentation warranted by the data.
- **2-component** β_s = 6°, β_c = −22°, ρ = 0.690, p = 0.035 (Phase A LOCO; alternative cross-ROI candidates (β_s=30°, β_c=+26°) and mw_jaccard candidates (β_s=44°, β_c=+54°) discussed in §D-6 / §2.5).
- **Selection (per §0)**: 2-component primary candidate; **behavioral validation pending** (§M-9 protocol scheduled). Final adoption gated on behav PASS.

### §R-3c Sub-08 (mild–moderate deuteranomaly) — descriptive fits + R+C structural retirement
- **Machado** trend only (ρ ≈ 0.62, p ≈ 0.058) — small retinal shift consistent with mild Ishihara phenotype but underpowered (1-DOF cannot capture both retinal-compensation and confusion-axis structure).
- **R+C** Δλ = 2.5 nm, **g = −2.25**, ρ = 0.857, p = 0.005 (memory `R+C Model & 2-Component Findings`; behav §2-2). Note `(1+g) = −1.25` ⇒ **sign-inversion + 25% amplification on retinal RG**, deviating sharply from Tregillus's "exact compensation" reference (g = −1).
- **R+C structurally retired for sub-08** (behav §2, §6 #2): the 1-DOF RG knob produces YG-C 4-way collapse (c3≡c4, c5≡c6, protan-axis− ≡ sRGB C). Reported as descriptive fit only, **not** carried forward to §R-4 filter inversion.
- **2-component** β_s = 38°, β_c = −14°, ρ = 0.881, p = 0.004 (memory `LOCO-Primary Filter Design`; strongest LOCO result in pipeline).
- **Selection (per §0)**: 2-component adopted as sub-08 final filter model — **behavioral PASS observed 2026-04-17** (behav §3): YG-C 4-way collapse dissolved, c3=연두 / c4=warm-ivory / c5=light-sky / c6=dark-sky distinct. Residual color-local failures at c2 (orange→green) and c8 (magenta→dark-sky); see §R-5 + §D-2.

### §R-3d Per-subject status summary table

| Subject | Final filter class | Parameters | Selection basis | Behavioral status |
|---|---|---|---|---|
| Sub-08 (deutan) | **2-component** | β_s = 38°, β_c = −14° | Behavioral PASS overrides LOCO ρ | **PASS** YG-C dissolved (2026-04-17); FAIL c2 orange + c8 magenta (color-local) |
| Sub-09 (protan) | 2-component (candidate) | β_s = 6°, β_c = −22° (Phase A LOCO) | LOCO-best with cross-ROI alternatives; behavioral pending | Pending — protocol scheduled (§M-9) |
| Sub-10 (near-normal) | — | — | Excluded per §0/§A7 | Not applicable |

### §R-3e Cross-criterion descriptive complementarity (LOCO ↔ ΔRDM)
- **Sub-08**: hV4 LOCO p=0.004 (strong) / V1 ΔRDM p=0.179 (NS) → LOCO is the channel for sub-08.
- **Sub-09**: hV4 LOCO p=0.018 (Machado) / V1 ΔRDM p=0.026 (separate fit) → ΔRDM contributes evidence sub-09 misses on LOCO at V1.
- → Per-subject complementarity motivates the δ·L_rdm term in L_LOCO (§M-6b). **Not** framed as a "dual-criterion specificity claim" (per §0); reported as descriptive evidence convergence.

### §R-3 Figure (F4)
- (a) Per-subject parameter landscape: Δλ × g heat-map for R+C; β_s × β_c for 2-component; LOCO ρ contour overlay (no p-thresholded selection rule shown — descriptive only).
- (b) Per-subject vulnerability fit overlay (existing `fig1_panels_bcd.pdf` — caption updated to remove "closed-testing winner" language).
- (c) Sub-08 R+C YG-C-collapse schematic vs. 2-component dissolution (panel from behav §3-2; promotes the model-class transition into the figure).

## §R-4 (PRE-IMAGE → FILTER) Bijective inversion and individual correction filters

### §R-4a Pre-image search procedure
- Per (model, subject): θ_in = argmin_θ ||D̂(θ) − θ_target||² over 0–360° × 0.5° grid; per-color residual + Jacobian reported.

### §R-4b Severity-driven feasibility (descriptive)
- **Sub-08 (Δλ = 2.5 nm)**: small retinal shift → arc preserved → Machado, R+C, 2-component all admit exact 8/8 pre-image (residual <0.001°). However R+C is structurally retired for sub-08 (§R-3c, behav §2 YG-C collapse), leaving Machado (1-DOF, near-identity at small Δλ — behav §2-5 underpowered) and 2-component as substrate candidates.
  - 2-component: mean |δ| = 46.3°, max = 104.2° (memory `LOCO-Primary Filter Design`). Filter substrate adopted (behav §6 #3).
- **Sub-09 (Δλ = 13.5 nm under Machado)**: arc compresses 360° → ~96° → c4/c5/c6 (green/cyan/blue) collapse onto ~282°.
  - **Machado: 4/8 exact** (remaining 4 require approximate separation-optimised fallback; min separation 1.03° → 5.76°, 5.6× improvement but well below healthy ~70° spacing).
  - **2-component: 8/8 exact** (mean |δ| = 20.1°, max = 48.1°). The only class with bijective pre-image at moderate severity.

### §R-4c R+C vs 2-component correction-vector divergence (Sub-08 descriptive)
- For sub-08, the (now-retired) R+C-derived correction vector and the (adopted) 2-component-derived correction vector have:
  - cosine similarity = −0.18,
  - sign agreement = 3/8,
  - despite comparable fit ρ (0.857 vs 0.881).
- This is the descriptive numerical signature of the YG-C collapse argument (behav §2-4 "one tuning knob, two stations"): comparable LOCO fit quality conceals structurally different correction directions; only the 2-component direction passes behavioral test. **Not** framed as a prospective behavioral prediction (§R-5 sub-08 is observed; §R-5 sub-09 alone remains prospective).

### §R-4d Verdict
- 2-component is the only model class with bijective pre-image (8/8 exact) at both severity levels AND with independent DOF on RG and confusion axes (behav §2-4).
- Per §0, 2-component is the per-subject filter substrate for both sub-08 (behavioral PASS) and sub-09 (LOCO-best candidate, behavioral pending).

### §R-4 Figure (F5)
- (a) Sub-08 R+C arc + 8/8 exact pre-image arrows.
- (b) Sub-09 Machado arc-collapse visualization (c4/c5/c6 merge at ~282°) + 2-component bijective recovery.
- (c) Sub-08 R+C-vs-2-component correction-vector divergence (sign-3/8, cos −0.18).

## §R-5 (BEHAVIORAL VALIDATION + SESSION-2 fMRI)

> **Status**: Sub-08 qualitative test **observed (2026-04-17, behav §3 PASS)**. Sub-09 protocol **scheduled** (§M-9). Session-2 fMRI under filters: pending booking. Section retains full structure for both subjects; sub-08 reports observed, sub-09 prospective.

### §R-5a Sub-08 2-component filter — observed (2026-04-17)
- Qualitative test on 12 stimuli (8 scanner hues + sRGB primaries + protan/deutan-axis stimuli; CIELab L*=75, C*=40 ring; Machado-derived ΔL* applied as data-collection control per behav §6 #6).
- **Primary falsification target — YG-C 4-way collapse**: dissolved (behav §3-1). c3 (연두) ≠ c4 (warm-ivory); c5 (light-sky) ≠ c6 (dark-sky); protan-axis− (light-sky) ≠ sRGB C (sky). Zero "merge / blob / 같이 보인다" phrases in sub-08's report.
- **Direct comparison vs R+C** (behav §3-2): the three R+C collapses (c3/c4, c5/c6, 4-way G/Y/c3/c4) all unmerged under 2-component. Behavioral confirmation of behav §2-4 "one knob, two stations" prediction.
- **Residual color-local failures** (open as Phase-3 refinement, not class failures):
  - **c2 orange → green** (behav §3-3): pre-image lands at ~68° CIELab; deutan luminance shift drives perception into green territory. Fine grid `(β_s ∈ [32,44]°, β_c ∈ [−18,−10]°)` confirmed orange recovery is **structurally unrecoverable** at 8-color resolution within the 2-component grid (Track B1 closed; behav §3-3 Action).
  - **c8 magenta → dark sky** (behav §3-4): consistent with sub-09 c8 anti-prediction structure (memory `Gen-4` task #21, hV4 z=−3.23). c8-only variant pre-image candidates θ ∈ {290°, 300°, 310°} pending evaluation (Track B2 viz generated).

### §R-5b Sub-09 — preregistered protocol (prospective)
- Same template as sub-08 (12 stimuli, 4 conditions): uncorrected / Akalin algorithmic baseline / Machado-derived (sub-09 LOCO-best retinal class) / 2-component (β_s = 6°, β_c = −22° Phase A canonical).
- Optional comparison stimulus: 2-component cross-ROI alternative (β_s = 30°, β_c = +26°) and mw_jaccard candidate (β_s = 44°, β_c = +54°) — selection pre-registration in §M-9.
- **Preregistered predictions to falsify**:
  - **PASS expected**: c1 protan compensation, c5/c6 cyan/blue-cyan separation, c8 magenta anomaly handling.
  - **FAIL on c8 only** → c8-only variant (mirrors sub-08 §R-5a Track B2).
  - **FAIL globally** → revert to Machado-only (model class re-selection per §0; not a pipeline failure).

### §R-5c Quantitative behavioral (2AFC JND + 8-AFC) — both subjects
- 2AFC JND on confusion-axis pairs identified from each subject's LOCO profile × 4 filter conditions × 50 trials each.
- 8-AFC identification × 20 reps × 4 conditions.
- Sub-08 Phase 2 endpoint: filter retains YG-C separation observed in §R-5a; 2-component reduces JND on c3↔c4 / c5↔c6 / protan-axis vs uncorrected baseline.

### §R-5d Session-2 fMRI under filters
- Same scanner protocol per subject under each filter condition; quantify Δ-LOCO between filtered and uncorrected per ROI.
- Expected (descriptive): 2-component condition increases hV4 LOCO ρ relative to uncorrected; magnitude reported per subject without group inference.

### §R-5 Figure (F6)
- (a) Sub-08 qualitative report grid (behav §3 table promoted) + R+C-vs-2-component side-by-side.
- (b) Sub-09 prospective grid (placeholder until acquisition).
- (c) JND reduction × pair × filter; 8-AFC confusion matrices before/after; Δ-LOCO per ROI.

## §R-6 (PROMOTED FROM SUPP) Single-case framework — descriptive disclosure of model expressivity

> **§0 alignment**: this section reports HC FPR as a **descriptive limit of an expressive model**, not as a defense of specificity. Inferential anchors are behavioral validation (sub-08 PASS, sub-09 pending) and external cross-modal Emery match. Per §0, "specificity claim" is forbidden as a selection criterion.
>
> **Required as MAIN TEXT** by redteam R2 (FATAL) and §0 framework lock — must not be relegated to Supp.

### §R-6a HC FPR — descriptive disclosure (no specificity claim)
- Voxel-prediction L_LOCO under label-permutation reaches p<0.05 for: 7/7 HC under 2-component family; 5/7 HC under R+C; 3/7 HC under Machado (memory `HC Specificity + Baseline Δρ`).
- HC best ρ (sub-03 V1 2-comp ρ=0.929; sub-05/06 V4 Machado ρ=0.929) is indistinguishable from CVD best ρ (sub-09 ρ=0.929).
- Baseline-Δρ correlation in HC = −0.894: regression-to-mean on voxel covariance + per-subject baseline ρ dominates, not cone-shift signal. Sub-10 (near-normal, behavioral indistinguishable from HC) Δρ = +0.929 indistinguishable from sub-09.
- **Mechanism (descriptive)**: HC FPR is the expected behavior of a 2-DOF expressive model on n=8 colors with rank-based loss; this is a structural limit of voxel-prediction L_LOCO, not a fixable shortcoming within the same measurement family (`future_phase2/CLAUDE.md` §0; cycle 9–13 confirmation).

### §R-6b Position within the precision-neuroscience case-study tradition
- Per `crawford1998` (single-case modified t), `schuett2023` (single-model significance fallacy), `kriegeskorte2019` (origin of the critique), and `finn2020` / `feilong2018` (precision-neuroscience paradigm), per-subject inference does not require model-vs-HC specificity at the selection step.
- The clinical SRM literature (`byrge2015`, `hasson2009`, `mantyla2018`, `frassle2020`) treats per-subject characterization as the unit of analysis precisely because population-level specificity is not the inferential goal.

### §R-6c Inferential anchors (replacing v1.0 4-pillar defense)
> **Per §0**: "specificity is descriptive only; behavioral validation is the inferential anchor". Anchors below are **stated, not defended as specificity**:

1. **Behavioral validation as ground truth** — sub-08 2-component PASS observed 2026-04-17 (behav §3): YG-C 4-way collapse dissolved, R+C-vs-2-component correction divergence (cos = −0.18) resolved in favor of 2-component. Sub-09 behavioral protocol scheduled (§M-9).
2. **Cross-modal external match (descriptive convergence)** — β_s of 20°/23° (sub-08 / sub-09) brackets Emery (2021)'s 21.4° behavioral B-Y rotation from an unrelated cohort + independent modality. Reported as descriptive convergence, not as specificity-via-external-validation.
3. **Physiological grounding** — fitted Δλ in 2–14 nm range (`neitz2011`, `deeb2005`) and the 2-component β_s/β_c structure are biophysically coherent with the post-receptoral compensation literature (`tregillus2021`, `robinson2023`, `webster2015`); HC-significant fits distribute across the grid without analogous physiological coherence. Reported as **mechanistic interpretability of the per-case fit**, not as model-vs-HC discrimination.

### §R-6d Closing statement
- Inference is **per-subject descriptive** (Crawford-Howell positional + behavioral PASS) + **externally convergent** (Emery 21.4° single-subject brackets). No CVD-vs-HC group specificity claim is made; no cone-shift family discriminates CVD from HC under the canonical voxel-prediction L_LOCO. The paper's value rests on the **mechanistic interpretability** of each subject's fit and on **behavioral validation as falsifier** — not on model-selection specificity.

### §R-6 Figure (F7, promoted from Supp `fig_hc_specificity.pdf`)
- HC Δρ histogram (n=6 effective at hV4 due to sub-07 16-voxel issue) with sub-08 / sub-09 overlaid; **explicit FPR labels**; baseline-ρ inversion arrow indicating regression-to-mean mechanism.

---

# §4 Discussion (~2,000 words)

## §D-1 Summary (~150w)
Three findings: (i) cortical color discrimination–interpolation dissociation in CVD hV4, (ii) 2-component as the only model dual-validated (LOCO + bijectivity) and uniquely producing exact pre-images at both severity levels, (iii) per-subject β_s convergence with Emery 21.4° + same-day JND reduction confirms behavioral payoff.

## §D-2 Cortical color geometry beyond confusion-lines (~400w)

- Integrate `brouwer2009` (healthy LOCO), `bannert2018` and `bannert2025` (hV4 hub + SRM precedent), `parkes2009` (V1 hue), `kuriki2015` (V4 intermediate hues), `brouwer2013` (categorical clustering).
- β_s ≈ 21.5° (Sub-08 20°, Sub-09 23°) ⇒ cortical S-cone gain up-regulation; behaviorally validated by Emery 21.4°.
- β_c subject-specific: Sub-08 −14°, Sub-09 −22° ⇒ different compensatory realignment per subject (per-subject framing per redteam R7 — n=2, not population convergence).

## §D-2b (NEW) Anomaly-vs-Daltonism contrast

> **NEW per redteam audit**. Critical distinction with `rina2024`.

- Anomalous trichromacy preserves a *distorted* hV4 geometry; Rina (2024) showed that **full Daltonism (L-cone absence) abolishes isolated hV4 color activity**. Anomaly retains cone signal sufficient for cortical geometry; dichromacy does not.
- This Daltonism-vs-anomaly distinction is itself a continuous-severity prediction for the literature (`tregillus2021`, `basim2025`, `robinson2023`).

## §D-3 LOCO/LORO dissociation as functional marker (~350w)

- RDM = metric properties of the space; LOCO = functional interpolation capacity.
- Memory `Behavioral Cross-Modal Findings`: **LOCO → JND 100% concordance** (HC1 6/6 pairs); SRM z → JND 33% (2/6).
- → LOCO is the clinically relevant phenotype; ΔRDM is the geometric companion.
- V1/V2 sustain discrimination via local opponent contrast; hV4 interpolates via the full manifold (`bannert2018`).

## §D-4 Why 2-component, given HC FPR (~350w)

- **Machado** cannot exceed sub-09's arc compression (4/8 exact only); for sub-08 the small Δλ (~2.5 nm) makes Machado a near-identity filter (behav §2-5 underpowered).
- **R+C** is structurally limited to one DOF on the RG axis (`rg' = rg_base + (1+g)·(rg_retinal − rg_base)`), with zero DOF on the YB axis (behav §2-1). For sub-08 the L_LOCO best fit is g = −2.25, i.e., (1+g) = −1.25 — sign-inversion + 25% amplification on retinal RG. This single knob trades RG retinal compensation against confusion-axis preservation; the inevitable side-effect is YG-C collapse (behav §2-4 "one tuning knob, two stations"), behaviorally observed in sub-08 (behav §1).
- **2-component** has two **independent** direction parameters (β_s on S-cone axis, β_c on confusion-axis), exactly the DOF that R+C lacks. Sub-08 hV4 LOCO p=0.004 (strongest in pipeline). Behavioral PASS (behav §3, 2026-04-17) confirms YG-C dissolution — this is the model-class-vs-model-class behavioral falsification §2-4 predicted.
- **Bijective pre-image**: 2-component is the only class admitting 8/8 exact pre-image at both severity levels (sub-08, sub-09). Machado fails (sub-09 4/8) and R+C is retired structurally (sub-08).
- **HC FPR is the descriptive limit of an expressive model on n=8 colors** (per §0): Schütt (2023) single-model fallacy framework + Kriegeskorte & Douglas (2019). Inference is anchored on **behavioral validation** (sub-08 observed PASS; sub-09 prospective protocol) and on the **mechanistic interpretability** of each subject's fit, not on within-family specificity.

## §D-5 Case-study framework + clinical SRM precedent (~300w)

- `crawford1998` modified t-test; `schuett2023` single-model fallacy; `kriegeskorte2019` origin.
- `finn2020` precision neuroscience paradigm; `feilong2018` individual differences.
- Clinical small-N precedent: `byrge2015` (ASD); `hasson2009` (ASD idiosyncrasy); `mantyla2018` (first-episode psychosis); `frassle2020` (generative embedding).
- **Analogy**: clinical stimulation mapping does not require between-subject statistics to be useful; case-study is a recognized inferential mode in precision neuroscience.

## §D-6 Limitations and future work (~300w)

- **n = 2 effective CVD**; protan/deutan subtype matrix under-sampled. Pre-registered scaled cohort (n ≥ 5–10) replication in preparation (PLAN_ToC §6 Phase 3 plan).
- **Same-day adaptation**: long-term filter wear unknown (`werner2020` perceptual learning caveat).
- **CIE Lab is HC-optimized**; CVD-optimized color spaces (MDS-based) could sharpen β_s/β_c estimates.
- **LLM-CVD scope boundary**: Hayashi (2024) LLM benchmarking is orthogonal to our fMRI focus; not a competitor (PLAN_ToC §10.3).
- **Pre-image off-training stability**: bijectivity verified over 8 training hues; full 360° Jacobian reported (per redteam R5) but full-circle behavioral JND under 2-component filter is the next falsifier.
- **Loss-form openness (§2.5 below)**: voxel-prediction L_LOCO is one of 12 loss variants benchmarked (`results/loss_inventory.{md,csv}`, 2026-05-03). No single-ROI loss reaches HC-vs-CVD distinct status for both CVD subjects under bootstrap rank-based emp_p ≤ 0.20; only `mw_jaccard_loss` at hV4 distinguishes both. Sub-09 LOCO-best parameters (β_s=6°, β_c=−22°) and mw_jaccard candidate (β_s=44°, β_c=+54°) disagree by ~38° on β_s — a loss-form sensitivity that cannot be resolved within the n=8 / n=6-effective-HC measurement family. This open question is bounded by the descriptive-only framing per §0 and resolved at the per-subject level by behavioral validation; loss-form refinement in larger cohorts (D-6 scaled-cohort plan) is the principled next step.
- **Color-local failures of 2-component (sub-08)**: c2 orange recovery is structurally unrecoverable in `(β_s ∈ [32,44]°, β_c ∈ [−18,−10]°)` at 8-color resolution (behav §3-3 + Track B1 closed); c8 magenta requires color-local correction (behav §3-4, Track B2 c8-only variant pre-image candidates pending). These bound the 2-component class to the c1–c7 range for sub-08 deutan; a fourth parameter (β_m magenta-specific) may be necessary in scaled-cohort fitting.

## §D-7 Conclusion (~100w)

CVD alters continuous cortical hue geometry with individually-patterned distortions that preserve discrimination while compromising interpolation. A 2-component cortical model captures the distortion and yields a bijective, individualized corrective filter that brackets a known behavioral benchmark and produces same-day JND reduction. Neural-geometry-guided display adaptation is a feasible, behaviorally validated path to precision color-vision support.

---

# §5 Figures (5 main + 4 supplementary)

| ID | Title | Source | Status (2026-05-01) |
|----|-------|--------|---------------------|
| **F1** | Stimulus + ROI overview + pipeline schematic | existing `fig1a_output.png` | ✓ ready |
| **F2** | LORO + LOCO bars × ROI × group (R-1) | `loco_baseline.py` outputs | needs assembly |
| **F3** | SRM ΔRDM heatmaps + per-pair bootstrap (R-2) | `rerun_loo_consistent.py` | needs re-plot |
| **F4** | Closed-testing landscape + vulnerability fit (R-3) | existing `fig1_panels_bcd.pdf` | needs caption update |
| **F5** | Pre-image inversion + arc-collapse + correction divergence (R-4) | existing `fig2_output.png` | needs caption update |
| **F6** | Behavioral JND + Session-2 fMRI Δ-LOCO (R-5) | **PENDING Session-2 acquisition** | TODO ~1 month |
| **F7** | HC FPR + Sub-08/09 overlay (R-6) | `fig_hc_specificity.pdf` (currently Supp) | promote to main |
| S1 | Procrustes alignment QA | existing | ✓ |
| S2 | Basis-channel K sensitivity (LORO/LOCO × K) | existing | ✓ |
| S3 | Sub-10 incidental control (near-normal) | needs assembly | TODO |
| S4 | Per-subject model comparison matrix | `notion.md` §5 | needs new |

---

# §6 Bibliography (`docs/PAPER/bibliography.bib`)

## §6.1 Critical clusters

| Cluster | Key citations | Used in |
|---------|---------------|---------|
| **Filter ceiling** | `brettel1997`, `machado2009`, `shen2016`, `akalin2025`, `werner2020` | §Intro-1 |
| **Anomalous-trichromacy theory** | `neitz2011`, `deeb2005`, `bosten2019`, `boehm2014`, `tregillus2021`, `robinson2023`, `webster2015` | §Intro-2, §D-2 |
| **CVD imaging** | `rina2024`, `wachtler2003`, `rabin2011`, `tregillus2021` | §Intro-3, §D-2b |
| **Cortical color** | `gegenfurtner2003`, `conway2018`, `shapley2011`, `parkes2009`, `kuriki2015`, `bannert2018`, `brouwer2009`, `brouwer2013`, `engel1997` | §Intro-3, §Intro-4 |
| **SRM precedent** | `chen2015`, `bannert2025`, `feilong2018`, `haxby2011`, `guntupalli2016` | §Intro-3b, §M-4 |
| **Case-study framework** | `crawford1998`, `schuett2023`, `kriegeskorte2019`, `finn2020`, `byrge2015`, `hasson2009`, `mantyla2018`, `frassle2020` | §Intro-5, §D-5 |
| **External match (Emery)** | `emery2021` | §R-2c, §R-3, §R-6, §D-2 |
| **Color space** | `derrington1984`, `stockman2000` | §M-2 |

## §6.2 Outstanding bibliography items

- Bosten 2019 PDF — paywalled, cite from abstract/DOI.
- Isherwood 2020 PDF — open-access Faculty Reviews; try `WebFetch` if time allows.
- Conway 2018 / Gegenfurtner 2003 / Shapley 2011 full-text — cite at statement level, full PDFs not local.
- Byrge 2015 / Hasson 2009 / Mäntylä 2018 / Frässle 2020 full-text — bib entries suffice.

---

# §7 Risk Register (v1.1)

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Sub-09 behavioral protocol delay | **H (active)** | §M-9 protocol scheduled; sub-08 PASS already retains §R-5a even if sub-09 slips. If sub-09 slips >4 weeks, retarget eLife Short Report with sub-08-only behavioral §R-5a observed. |
| Session-2 fMRI slips >4 weeks | M | §R-5d Δ-LOCO is descriptive companion — paper retains weight on sub-08 qualitative behavioral PASS + cross-modal Emery. |
| Sub-08 / sub-09 quantitative behavioral null (after qualitative PASS) | M | Report null honestly; sub-08 qualitative PASS is the primary YG-C falsifier and is locked in. eLife accepts null-result addenda. |
| Reviewer demands n ≥ 5 CVD | H | D-6 pre-registered scaled cohort statement; Nat Comms tertiary needs this anyway. |
| Rina 2024 priority claim | L | §D-2b dichromat-vs-anomaly distinction; LOCO + pre-image orthogonal to Rina activation finding. |
| **HC-FPR reviewer challenge** | H | **No longer framed as a defense risk per §0**: R-6 reports HC FPR as descriptive limit of expressive model on n=8 colors; inferential anchors are behavioral validation + Emery cross-modal match. Schütt 2023 + Kriegeskorte 2019 frame the reply. |
| 2-component β_c interpretation | M | §D-2 cite as effective compensatory parameter, not literal cortical rotation; replication in scaled cohort. |
| **Sub-09 cross-loss disagreement (β_s = 6° vs 44°)** | **H (new)** | §D-6 + §2.5 disclose loss-form sensitivity at n=6-effective-HC / n=8-color resolution; sub-09 behavioral test (§R-5b) chooses among candidates; Phase A canonical (β_s=6°) is the default until behavior says otherwise. |
| Pre-image bijectivity over off-training hues | M | §M-7 + §R-5d: report Jacobian; Session-2 full-circle JND as falsifier. |
| Sub-08 c2 orange + c8 magenta color-local FAIL | L (disclosed) | §R-5a + §D-6: declared as 8-color/2-DOF resolution limits, not class failures; c8 variant Track B2 ongoing; β_m fourth parameter as scaled-cohort proposal. |
| ~~Closed-testing rule criticized~~ | — | **Removed v1.1**: closed-testing rule retired per §0; replaced by per-subject behavioral-PASS-overrides-LOCO. |
| ~~g = +2.25 biophysical implausibility~~ | — | **Removed v1.1**: sign was wrong (correct g = −2.25 = sign-inversion + 25% amp); R+C structurally retired for sub-08 via behav §2 YG-C — not by biophysical-overshoot argument. |

---

# §8 Work Plan

## §8.1 Phase 1a — Pre-Session-2 (this week)

- [x] Bibliography 22-citation batch (PLAN_ToC §10.4) — complete.
- [x] Introduction v2 draft — complete (`introduction_v2.tex`).
- [ ] **Results restructure to v1.0 INDEX order**: edit `Results/results_v3.tex` → `results_v4.tex`:
  - Combine §R-2 + §R-3 of v3 into new §R-1.
  - Move v3 §R-5 (SRM ΔRDM) to §R-2.
  - Reframe v3 §R-4 as §R-3 (cone-shift fits with loss explicitly motivated).
  - Keep v3 §R-6 (pre-image) as §R-4.
  - Add new §R-5 (behavioral, conditional).
  - Promote v3 §R-6 "case-level specificity" paragraph → standalone §R-6 with HC FPR figure.
- [ ] Methods edits: §M-6 (cone-shift loss + closed-testing), §M-7 (bijectivity Jacobian script), §M-8 (HC FPR pointer to §R-6).
- [ ] Add `analysis/future_phase2_filter_optimization/scripts/preimage_jacobian_check.py`.

## §8.2 Phase 1b — Session-2 decision gate

- [ ] **Session-2 booking confirmation** (PI action) — required by 2026-05-15 to retain Option B.
- [ ] If booked: schedule scan for Sub-08 + Sub-09 (1h each) + same-day behavioral (1h each).
- [ ] If slips >2 weeks: switch to Option A (Short Report); retire §R-5, edit abstract sentence 6.

## §8.3 Phase 2 — Session-2 acquisition + analysis (≤1 month)

- [ ] Behavioral 2AFC JND + 8-AFC under 4 filter conditions.
- [ ] Session-2 fMRI under filters.
- [ ] §R-5 + Figure 6 assembly.

## §8.4 Phase 3 — Final assembly

- [ ] Discussion v1 draft (§D-1..§D-7).
- [ ] Figure renders at 300 dpi PDF.
- [ ] Abstract final.
- [ ] Supplementary §S1..§S4.
- [ ] Pre-submission `redteam-project` agent pass against full draft.

---

# §9 Outstanding PI decisions (next meeting)

1. **Title decision**: working title (1) — confirm or pick alternative?
2. **Session-2 booking**: scheduled date for Sub-08 + Sub-09?
3. **Behavioral protocol scope**: 2AFC JND only, or + 8AFC identification?
4. **F2 / F3 redraw priority**: which figure to assemble first?
5. **F7 promotion to main**: confirm HC FPR figure on main not Supp?
6. **Sub-10 disposition**: confirm Supp-only (current plan), or full inclusion?

---

# §10 (Audit Appendix) Redteam findings — neutralization status

> Source: `PLAN_ToC.md` §8.1 (2026-04-15 redteam pass). All FATAL items neutralized in v1.0 INDEX.

| # | Severity | Issue | Neutralization location in v1.0 INDEX | Status |
|---|----------|-------|---------------------------------------|--------|
| R1 | FATAL | Effective n=2 — no group-level framing | Abstract §6, all R-x use Crawford-Howell; sub-10 → Supp | ✓ neutralized |
| R2 | FATAL | HC FPR 7/7 for 2-component — model non-specific | §0 framework lock: descriptive only, no specificity claim. §R-6 main-text disclosure + §M-8 pointer. Inferential anchors = behavioral + Emery cross-modal | ✓ neutralized via §0 (v1.1 supersedes v1.0 4-pillar defense) |
| R3 | FATAL | "Recovers JND" prospective — unfalsified | Abstract §6 conditional ("validated by same-day JND"); §R-5 conditional on Session-2 | ✓ neutralized |
| R4 | CRITICAL | Brouwer 2009 LOCO precedence overstatement | §Intro-3 reframed: "extend to CVD"; abstract §4 "replicating Brouwer 2009" | ✓ neutralized |
| R5 | SERIOUS | Bijectivity claim over 8 colors only | §M-7 Jacobian over 0–360°; preimage_jacobian_check.py to be added | ⚠ script TODO |
| R6 | SERIOUS | Model cherry-picking / HARKing | v1.1: closed-testing rule **removed**; replaced by per-subject behavioral-PASS-overrides (§0 + §M-6c). §D-6 pre-registered scaled cohort. Loss inventory §2.5 discloses 12-variant search transparently. | ✓ neutralized via §0 |
| R7 | MODERATE | n=2 vs "cross-subject convergence" | §R-2c + §R-3c + §D-2 explicit n=2 qualifier | ✓ neutralized |
| R8 | MODERATE | Figure plan misses HC FPR | §R-6 + F7 promotion | ✓ neutralized |

---

# §11 (Audit Appendix) Narrative validation summary

> Source: `PLAN_ToC.md` §10 (2026-04-16 NotebookLM + Semantic Scholar pass). Coverage table.

| Section | Coverage before audit | Coverage after audit + v1.0 INDEX | Closed gap |
|---------|------------------------|------------------------------------|------------|
| §Intro-1 (filter ceiling) | 60% | **95%** | `akalin2025` recent baseline added |
| §Intro-2 (neural reformulation) | **0 citations** | **90%** | Full anomalous-trichromacy theory cluster added (`neitz2011`, `deeb2005`, `bosten2019`, `boehm2014`, `tregillus2021`, `robinson2023`) |
| §Intro-3 (CVD imaging) | 55% | **90%** | §Intro-3b SRM precedent added per PI annotation: `bannert2025`, `feilong2018`, `byrge2015`, `hasson2009` |
| §Intro-4 (discrimination/interp) | 40% | **95%** | Cortical color review cluster added: `gegenfurtner2003`, `conway2018`, `shapley2011`, `parkes2009`, `kuriki2015`, `bannert2018`, `engel1997` |
| §Intro-5 (three questions) | 70% | **100%** | Q2 explicitly licenses filter feasibility (PI annotation); clinical SRM cluster added |

---

# §12 (Audit Appendix) Memory checkpoints used in v1.0 INDEX

> Sources at `~/.claude/projects/.../memory/`. Key memories influencing the v1.0 INDEX:

- `LOCO/LORO Decoder Findings` (2026-02-26) — pooled-W LOCO; Spearman ρ for templates.
- `Forward Model Final Status` (2026-03-11) — ridge_gcv + FE-3 retention; basis-channel tradeoffs.
- `Phase 2 Cone-Shift Pipeline v2` (2026-03-22) — Sub-09 V1 ΔRDM p=0.026; LOCO/ΔRDM complementarity.
- `Behavioral Cross-Modal Findings` (2026-03-22) — LOCO → JND 100% concordance; SRM z → JND 33%.
- `R+C Model & 2-Component Findings` (2026-04-07) — Sub-08 g=+2.25 vs Sub-09 g=−1.10; 2-component dual-validation.
- `LOCO-Primary Filter Design` (2026-04-09) — composite loss form; 2-component pre-image 8/8 both subjects; CRITICAL framing fix on "LOCO vs ΔRDM dissociation".
- `HC Specificity + Baseline Δρ Diagnostic` (2026-04-11) — HC FPR 7/7 under permutation; baseline ρ inversion.
- `Gen-4 Cone-Shift sub-09 Validation` (2026-04-06) — Task #19 PASS, #20 FAIL, #21 FAIL, #22 FAIL → Machado solo insufficient for sub-09; reinforces 2-component selection.
- `Literature Framing` (CRITICAL, persistent) — Brouwer & Heeger 2009 LOCO precedence; novelty wording.
- `LOSO Zero-Shot & Document Structure` (2026-03-15) — pooled-runs LOCO; primary/secondary purpose framing.
- **`future_phase2/CLAUDE.md` §0 Framework Decision (2026-05-03 lock)** — filter selection rule; specificity-as-descriptive; behavioral-PASS-overrides-LOCO; cycle 9–13 closed; selection-rule reformulation forbidden.
- **`behav_validation.md` §3 Sub-08 2-component PASS (2026-04-17)** — YG-C 4-way collapse dissolved; c2 orange + c8 magenta color-local failures (Tracks B1, B2). §6 #2/#3 model-class adoption decisions.
- **`results/loss_inventory.{md,csv}` (2026-05-03)** — 12 loss variants × 8 subjects bootstrap; `cycle15_opt2_v4mwj_v1lrank` overall winner; sub-09 cross-loss disagreement on β_s (6° canonical vs 44° mw_jaccard).

---

# §13 English paragraph drafts

> Cross-reference: full paragraph-level drafts already exist in:
> - **Introduction**: `Introduction/introduction_v2.tex` (PLAN_ToC §10 confirmed).
> - **Methods**: `Methods/methods_streamlined.tex` (v1.2; needs §M-6/§M-7/§M-8 additions per §8.1 above).
> - **Results**: `Results/results_v3.tex` (v3; needs restructure to v4 per §8.1 above).
> - **Discussion**: not yet drafted; outline in §4 of this file.
>
> Edits to Results §R-1..§R-6 in this file are *outline-level only*; do not replace `results_v4.tex` paragraph drafts when written.

---

# §X v1.0 → v1.x changelog

- **v1.0 (2026-05-01)**: First INDEX cut for the project.
  - Locked target journals: eLife → Curr Biol → Nat Comms (PLAN_ToC §9.1).
  - Locked case-study framing throughout.
  - Locked Sub-10 → Supp.
  - Restructured Results §R-1..§R-6: combined LORO+LOCO; moved SRM ΔRDM before fits; promoted HC FPR to main.
  - All redteam FATAL/SERIOUS items either neutralized or with concrete TODO (§10).
  - Bibliography 22-citation batch incorporated (PLAN_ToC §10.4).
  - PLAN_ToC.md retained as decision-log archive (frozen at v1.0 cut-over).

- **v1.1 (2026-05-04)**: Reconciliation with `future_phase2_filter_optimization/CLAUDE.md` §0 (2026-05-03 lock) and `behav_validation.md` §3 (sub-08 PASS 2026-04-17).
  - **Added §0 Framework Decision** (top of file, before #Title): filter selection rule, specificity-as-descriptive, behavioral-PASS-overrides-LOCO, no selection-rule reformulation, override procedure.
  - **Removed closed-testing rule** (Machado→R+C if NS) from §M-6c; replaced by per-subject independent fits + behavioral validation.
  - **Fixed Sub-08 R+C g sign**: `+2.25 → −2.25` (sign-inversion + 25% amplification per behav §2-2 + memory). v1.0 inherited error from `results_v3.tex`.
  - **Sub-08 R+C structurally retired** (§R-3c, §R-4): YG-C 4-way collapse argument (behav §2 / §6 #2). Reported as descriptive fit only; not carried forward to filter inversion.
  - **Sub-08 behavioral PASS reframed as observed (2026-04-17)** (§R-5a) — not preregistered. R+C-vs-2-component correction-vector divergence (cos = −0.18) cited as numerical signature of the resolved class transition.
  - **Sub-09 prospective protocol with cross-loss alternative candidates** (§R-5b): Phase A canonical (β_s=6°, β_c=−22°), cross-ROI (30°, +26°), mw_jaccard (44°, +54°) — selection in §M-9 pre-registration.
  - **§R-6 4-pillar specificity defense reframed as descriptive disclosure** (§R-6c): 3 inferential anchors (behavioral / Emery cross-modal / physiological grounding); no specificity claim per §0.
  - **§D-4 rewritten** to drop the g=+2.25 biophysical-implausibility argument; replaced by behav §2-4 "one knob, two stations" structural argument and behavioral falsification.
  - **§D-6 expanded** with loss-form openness (12-variant inventory) and color-local failure disclosure (c2 orange / c8 magenta).
  - **Risk register updated** (§7): HC-FPR no longer framed as defense risk; cross-loss disagreement and sub-09 behavioral delay added; closed-testing and g=+2.25 risks removed.
  - **§10 redteam table updated** for R2 (descriptive-only neutralization) and R6 (closed-testing removal).
  - **§12 memory checkpoints** add §0 framework lock, behav §3 sub-08 PASS, loss inventory.
  - **Per-subject status table** added in §R-3d.
  - **§2.5 Loss inventory section** added (cross-reference between §M-6b and §D-6).
