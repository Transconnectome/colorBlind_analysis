# Advisor-Meeting PPT Bundle  (4 main + 2 supplementary slides, 3-channel composition)

**Date**: 2026-05-04 (revised — CI-based HC sanity, not rank emp_p)
**Scope**: Phase 2 status briefing for advisor.

**Meeting focus** (per user 2026-05-04, all losses at matched α=2.0, β=1.0):

**3 fit-loss candidates, equal level** (sub-08):
1. **A. Canonical L_fit (38°, −14°)** — behavioral §3 PASS (sole in vivo validated filter, gold standard)
2. **B. Cycle 14 V1-RDM (58°, −36°)** — V1's significant signal channel (ΔRDM p=0.005); CI ✓ boot_frac=0.999
3. **C. Cycle 15 opt2 (68°, −38°)** — V1-LOCO Spearman channel; CI ✓ boot_frac=1.000

B and C share V4 mw_jaccard anchor + Tikh — **only V1 channel differs** (RDM vs LOCO). β_c sign agrees (−36° vs −38°). β_s differs (58 vs 68). All three have OPPOSITE β_c sign vs A → selection-rule discussion.

**Sub-09**: A. Phase A (6°, −22°)  vs  B. Cycle 14 V1-RDM (44°, +54°)  vs  C. Cycle 15 opt2 (44°, +54°). **B = C at matched weights → V1-channel-invariant** (44°, +54°). Both B/C boot_frac=1.000; sub-04 HC outlier caveat for both.
**Companion** (academic 10-slide deck): `claude_in_ppt_prompts.md` — do not confuse.

---

## Composition philosophy  (READ FIRST)

Each slide is composed from THREE asset types — never bake them into a single PNG:

| Channel | When to use | Tool | Where it lives |
|---|---|---|---|
| **A. Native PPT text** | bullets · tables · headlines · equations · narrative | Claude-in-PowerPoint prompt | rendered live by Claude in the slide |
| **B. Python data figure** | numbers · bars · heatmaps · CIs · curves with axis values | `scripts/visualization/figs_*.py` (matplotlib, academic style) | `presentation/figures/data/*.png` |
| **C. Generative schematic** | mechanisms · pipelines · conceptual diagrams (NO axis numbers) | GPT-5 Image / nanobanana / Imagen / DALL·E | save under `presentation/figures/schematics/` |

**Rule of thumb**: if a viewer needs to *read a number*, channel B (Python). If they need to *understand a process*, channel C (AI schematic). Otherwise, channel A (text).

**Global PPT style** (apply to every slide):
> 16:9, sans-serif, minimal chrome, single blue accent (#1f4e79). Body ≥14pt. Headings 18pt bold. NEVER auto-resize text — keep within the layout area.

---

# SLIDE 1 — Project Summary  (4-quadrant overview)

## A. Native PPT text  (paste into Claude-in-PowerPoint)

```
Create slide 1 titled
"Phase 2 — Personalized Inverse Filter for CVD"  with subtitle "Project Summary  |  2026-05-04".

Layout: 2x2 quadrant.
- Header bar (full width, ~10% of height): blue (#1f4e79) with title left + date right.
- Each quadrant: thin 1pt grey separator. Quadrant title in bold blue 14pt at top-left.
- Body bullets: 11pt black, ≥6pt spacing.

QUADRANT Q1 (top-left)  —  "Stage A reminder  (RDM/SRM + LOCO)"
- SRM disparity (Crawford & Howell, 10K perm):  V1 group p = 0.062 (g=1.16), V2 p = 0.075 (g=1.04)
- Per-subject:  sub-09 V1 t=3.5  p = 0.007**   ·   sub-08 V2 t=2.1  p = 0.040*   ·   sub-10 all n.s.
- LOCO (ridge_gcv voxel_corr, leakage-free):  V1 d=1.61 p=0.021*  ·  V2 d=1.85 p=0.022*  ·  hV4 d=1.19
- TAKEAWAY (italic green):  Discrimination preserved; interpolation selectively lost in CVD

QUADRANT Q2 (top-right)  —  "Activation  +  Decoder"
- Activation magnitude:  HC ≈ CVD at every ROI (all p > 0.3) — no signal loss
- LORO classification (chance 0.125):
    Raw 0.135  ·  B&H 2009 (FE+Proc) 0.545  ·  B&B 2025 (SRM 8-AFC) 0.39–0.56  ·  OUR BEST (LDA+SRM) 0.793
    Cross HC→CVD p=0.668 → shared mapping
- LOCO (I) Color decoding vs B&H 2009: HC MAE 75.7° (chance 90°), CVD elevated
- LOCO (II) Voxel prediction (ridge_gcv): V1 d=1.61* · V2 d=1.85* · hV4 d=1.19 (CVD ≤ null)
- TAKEAWAY (italic green):  Discrimination intact + interpolation lost (both LOCOs) = color-space distortion

QUADRANT Q3 (bottom-left)  —  "Phase 2 model + loss"
- 3 forward models (mechanistic level):
    1) Machado 1-way      — 1 DOF — retinal cone shift
    2) R+C                — 2 DOF — retinal + cortical RG gain
    3) 2-Component (★)    — 2 DOF — cortical angular dilation  [best for both CVD]
- 3 fit-loss candidates (equal-level — all use ridge_gcv LOCO voxel_corr):
    A. Canonical L_fit (hV4 only, used to fit sub-08 §3 PASS):
         L = 1.0·L_vuln(hV4) + 0.5·L_rank(hV4) + 0.2·L_rdm(hV4) + 0.1·L_smooth
    B. Cycle 14 (V4 mw_jaccard + V1-RDM, V4 matched to C):
         L = 2.0·L_mwJ(V4) + 1.0·L_rdm(V1) + 0.2·Tikh
    C. Cycle 15 opt2 (V4 mw_jaccard + V1-LOCO Spearman):
         L = 2.0·L_mwJ(V4) + 1.0·(1−ρ_LOCO_V1) + 0.2·Tikh
    ↳ B vs C: same V4 anchor + Tikh; only V1 channel differs
       (L_rdm = 1−cos(ΔRDM); L_mwJ = magnitude-weighted top-K Jaccard, V4 vuln depth)
- Selection rule:  LOCO-best descriptive fit  +  behavioral validation  (override authority)
- HC sanity (CI bootstrap 10K, family-symmetric 2026-05-04, matched α=2.0, β=1.0):
   BOTH cycle 14 and cycle 15 give CI-strict ✓ for BOTH sub-08 and sub-09 (boot_frac ≥ 0.999).
   sub-09 (β_s, β_c) = (44°, +54°) IDENTICAL across V1 channels → V1-channel-invariant convergence.
   Caveat: sub-04 HC norm closely adjacent (outlier-dependent at strict tail). §0 retained as policy.

QUADRANT Q4 (bottom-right)  —  "Status + plans"
- sub-08 deutan  [OK]      :  3 candidates (one per loss)
                              A. canonical (38°, −14°)   §3 behav PASS
                              B. cycle 14 V1-RDM (58°, −36°)   CI-strict ✓
                              C. cycle 15 opt2 (68°, −38°)   boot_frac=1.000
- sub-09 protan  [PENDING] :  3 candidates → behavioral arbitrate (matched α=2,β=1)
                              A. canonical Phase A (6°, −22°)
                              B. cycle 14 V1-RDM (44°, +54°)   boot_frac=1.000
                              C. cycle 15 opt2  (44°, +54°)    boot_frac=1.000
                              (B = C at matched weights → V1-channel-invariant;
                               A vs B,C anti-parallel; sub-04 HC outlier caveat for B,C)
- sub-10 normal  [EXCLUDED]:  no CVD-HC signal at any ROI
- 3 critical limits:  specificity abandoned (Cycle 13)  ·  HC pool n=6 effective  ·  8-color cap
- Next:  HIGH = sub-09 behavioral (4-way) + sub-08 4-way comparison  ·  THEN Phase 3 trigger

Footer (italic 9pt grey, full width):
"Detail in Slide 2 (activation+decoder)  ·  Slide 3 (model+loss)  ·  Slide 4 (status+behavioral+plans)"

Style: 16:9, sans-serif, single blue accent (#1f4e79). Do NOT generate images. Render text only.
```

## B. Python data figures
*None for Slide 1* — summary is text-only by design. (Quantitative detail lives in Slides 2–4.)

## C. Generative schematic  (optional 1 small inset)

Image generation prompt (paste into GPT-5 Image / nanobanana). Save output to
`presentation/figures/schematics/slide1_pipeline_inset.png`, insert as small overlay (~25% slide width) in Q1 corner if you want a visual anchor:

```
Minimalist horizontal pipeline schematic, ~3:1 aspect ratio, white background,
flat illustrator style, single navy-blue (#1f4e79) accent. Five chevron-shaped
stages connected by arrows:

   [Stimulus 8 hues]  ->  [Cones (L,M,S)]  ->  [Retinal opponent (RG, YB)]
   ->  [Cortical hue map V1 -> hV4]  ->  [Perception]

Above stages, a small "CVD intervention" tag with a downward arrow points at
the "Cortical hue map" stage (highlighting where the 2-component model acts).
Below the pipeline, a thin dashed loop labeled "Inverse filter delta(theta)"
runs back from "Perception" to "Stimulus".

Sans-serif labels, no axis numbers, no clip-art faces. 16:9 NOT required;
output 3:1 horizontal banner suitable for slide insert.
```

---

# SLIDE 2 — Activation  +  Decoder vs original-paper baselines

## A. Native PPT text

```
Create slide 2 titled
"Activation  +  Decoder Comparison vs Original-Paper Baselines".

Layout: ONE 2-row layout.
- Row 1 (~50%): one image placeholder + a 2-line text block to the RIGHT of the image
- Row 2 (~45%): one image placeholder + a 2-line text block to the RIGHT of the image
- Top headline (above row 1): bold blue 14pt
- Bottom takeaway (below row 2): italic green 12pt

Top headline (bold blue):
"Activation magnitude is preserved  ·  only INTERPOLATION is impaired in CVD"

ROW 1 image placeholder:
[INSERT: activation_overview.png  —  width fills 65% slide]

ROW 1 text block (right of image, 30% slide width):
"Per-color tuning (V1 / V2 / V3 / hV4):
  CVD curves stay within HC IQR band at all ROIs.

Group magnitude (mean |activation|, modulation depth):
  HC vs CVD all n.s.  (p > 0.3)

→  Deficit is geometric, not signal-loss."

ROW 2 image placeholder:
[INSERT: model_vs_baseline.png  —  width fills 65% slide]

ROW 2 text block (right of image, 30% slide width):
"LORO classification (8-color, chance 0.125):
  Raw 0.135  ·  B&H 2009 (FE+Proc) 0.545  ·  OUR BEST (LDA+SRM) 0.793
  B&B 2025 (SRM, between-subj 8-AFC) 0.39–0.56 across V1–hV4
  Cross HC→CVD p=0.668  →  shared mapping.

LOCO (I) Color decoding  vs  Brouwer & Heeger 2009:
  Predict held-out hue angle, FE+Procrustes (8-ch basis, template match).
  HC mean MAE 75.7° (chance 90°; V1 76.9° · V2 74.8° · V3 77.8°).
  CVD MAE elevated across ROIs. → Direct paradigm match.

LOCO (II) Voxel prediction (ridge_gcv encoder):
  V1 d=1.61 p=0.021* · V2 d=1.85 p=0.022* · hV4 d=1.19
  CVD at or below permutation null.

FE basis ablation: per-ROI optimum differs from B&H FE-6 default."

Bottom takeaway (italic green):
"Discrimination preserved (LORO) + interpolation lost (BOTH LOCOs)  =  CVD = color-space distortion."

Style: 16:9, sans-serif, single blue accent. Do NOT generate images.
Insert images at the indicated absolute paths (provided in user message).
Image absolute paths:
  - /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase5_filter_optimization/presentation/figures/data/activation_overview.png
  - /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase5_filter_optimization/presentation/figures/data/model_vs_baseline.png
```

## B. Python data figures  (already exist — academic style with axis numbers)

| File | Content | Source script |
|---|---|---|
| `presentation/figures/data/activation_overview.png` | Per-color tuning curves (4 ROI × HC IQR + sub-08/09/10) + group magnitude bars (HC vs CVD, all p) | `scripts/figs_activation_overview.py` |
| `presentation/figures/data/model_vs_baseline.png` | LORO 6×3 heatmap (discrimination) + 두 LOCO 결과 (I) Color decoding MAE per ROI [B&H 2009 비교] + (II) Voxel prediction d-effect HC vs CVD per ROI [no direct comparator] + FE-K ablation | `scripts/figs_model_vs_baseline.py` |

## C. Generative schematic
*None for Slide 2* — pure data slide.

---

# SLIDE 3 — Model Comparison  (4 models: 2 ours + 2 literature)

> **Scope**: 4개 모델을 나란히 비교. Machado는 직접 인용 base model이므로 생략.
> 왼쪽 2열 = 우리 모델, 오른쪽 2열 = 문헌 모델.

## A. Native PPT text

```
Create slide 3 titled
"Four Forward Models — Ours vs Literature".

Layout: 3-zone vertical stack.
- Zone 1 (~5%): thin header band with group labels
- Zone 2 (~80%): 4 equal columns — one per model
- Zone 3 (~15%): full-width comparison note + takeaway

ZONE 1 — Header band (full width, ~5%):
  Left half (50%): bold blue 13pt: "OUR MODELS"
  Right half (50%): bold grey 13pt: "LITERATURE"
  Thin vertical divider at center. Thin bottom border under entire band.

──────────────────────────────────────────────────────
ZONE 2 — 4 equal columns, 1pt grey dividers, ~80% of slide height:

  ── COL 1 (left)  "R+C  ·  Δλ + g  ·  retinal + cortical" ──
  Column header (bold blue 12pt, center): "R+C   2 DOF"
  Sub-header (grey 10pt): "retinal Δλ  +  cortical RG-gain"

  INSERT image (top 45% of column):
    …/presentation/figures/data/rc_panel_c.png
  INSERT image (bottom 45% of column, 1pt grey separator between):
    …/presentation/figures/data/rc_panel_d.png

  (No text caption — figures are self-labeled with axes)

  ── COL 2  "2-Component  ·  β_s + β_c  ·  cortical  ★" ──
  Column header (bold blue 12pt, center): "2-Component  ★   2 DOF"
  Sub-header (grey 10pt): "cortical hue-circle warp"

  INSERT image (90% of column height, centered):
    …/presentation/figures/data/two_comp_anatomy.png

  ── COL 3  "Tregillus 2021  ·  BOLD amplitude" ──
  Column header (bold grey 12pt, center): "Tregillus 2021"
  Sub-header (grey 10pt): "BOLD CRF amplitude  ·  Curr Biol"

  INSERT image (generative schematic, top 55% of column):
    …/presentation/figures/schematics/tregillus_bold_schematic.png

  3 bullets (10pt, dark grey):
    · Stimuli: 2 cardinal axes (L-vs-M, S-vs-LM), not full hue ring
    · V1 AT < CN (p=0.04*)  ·  V2v/V3v AT ≈ CN (compensation)
    · Observable: univariate ROI-mean BOLD amplitude scalar
    · Link to R+C g: same cortical RG-axis compensation (different level)

  ── COL 4  "Emery 2021  ·  hue-scaling  ·  CVD" ──
  Column header (bold grey 12pt, center): "Emery 2021"
  Sub-header (grey 10pt): "perceptual hue scaling  ·  Vis Res"

  INSERT image (generative schematic, top 55% of column):
    …/presentation/figures/schematics/emery_factor4_schematic.png

  3 bullets (10pt, dark grey):
    · Subjects: 7 deutan + 3 protan AT  vs  26 NT
    · Factor 4: zero at R/G (0°/180°), peak at B/Y (90°/270°), antiphase
    · Observable: behavioral hue rating (suprathreshold appearance)
    · Link to β_s: Factor 4 = β_s·sin(θ) — same non-uniform warp structure

──────────────────────────────────────────────────────
ZONE 3 — Comparison note + takeaway (~15%):

  Two-line note (italic 9pt grey, full width):
    "All four models detect CVD compensation. Ours differ: (1) individual-level fit vs group mean,
     (2) multivariate cortical pattern vs univariate BOLD scalar or behavioral rating."

  Bottom takeaway (italic blue 11pt, full width):
    "2-Component (★) is the only model with exact 8/8 pre-image for both CVD subjects
     and behavioral PASS — adopted as primary filter."

Style: 16:9, sans-serif, single blue accent (#1f4e79). Do NOT generate images.
Insert images at the indicated absolute paths (provided in user message).
```

## B. Python data figures  (already rendered — insert in Zone 2)

| File | Column | Source script |
|---|---|---|
| `presentation/figures/data/rc_panel_c.png` | Col 1 top (R+C hue circle Δλ) | `scripts/visualization/figs_rc_panels.py` |
| `presentation/figures/data/rc_panel_d.png` | Col 1 bottom (R+C opponent plane g) | `scripts/visualization/figs_rc_panels.py` |
| `presentation/figures/data/two_comp_anatomy.png` | Col 2 (2-comp β_s / β_c anatomy) | `scripts/visualization/figs_2comp_anatomy.py` |

## C. Generative schematics  (need to generate — paste prompts into GPT-5 Image / DALL·E)

### C1. Tregillus BOLD schematic
Save to: `presentation/figures/schematics/tregillus_bold_schematic.png`

```
Minimalist academic bar-chart schematic. White background, flat style, sans-serif.
3:2 aspect ratio. NO axis tick numbers except ROI labels.

Three ROI groups side by side, each with two bars (AT = light blue, CN = navy):
  Group 1 label: "V1"     — AT bar height ~40%, CN bar height ~100%
  Group 2 label: "V2v"    — AT bar height ~90%, CN bar height ~100%
  Group 3 label: "V3v"    — AT bar height ~95%, CN bar height ~100%

A downward red arrow above V1 labeled "reduced*".
A horizontal double-headed arrow above V2v-V3v labeled "compensated".
Left y-axis label: "BOLD amplitude (AT/CN)".
Legend: small square navy = CN, small square light-blue = AT.
NO background grid. NO caption text.
```

### C2. Emery Factor 4 schematic
Save to: `presentation/figures/schematics/emery_factor4_schematic.png`

```
Minimalist academic hue-circle schematic. White background, flat style, sans-serif.
1:1 aspect ratio (square). Single circle with 4 axis labels only: R (right), Y (top), G (left), B (bottom).

Four colored dots on the circle at cardinal positions:
  R (0°, right): red dot — small grey cross = zero displacement
  Y (90°, top): yellow dot — large navy arrow pointing LEFT (counterclockwise)
  G (180°, left): cyan dot — small grey cross = zero displacement
  B (270°, bottom): dark blue dot — large navy arrow pointing LEFT (clockwise)

"Factor 4" label in bold navy at top-left corner of the square frame.
"Emery 2021" label in small grey italic at bottom-right.
NO additional text, no equations, no legend.
```

---

# SLIDE 4 — Fit-Loss Functions

> **Scope**: Loss 후보 3개의 수식 + 각 항(term)의 정의와 역할. 슬라이드 전체가 Loss 전용.

## A. Native PPT text

```
Create slide 4 titled
"Fit-Loss Functions — 3 Candidates".

Layout: 2-zone vertical stack.
- Zone 1 (~40%): loss candidate formulas + selection note
- Zone 2 (~55%): term-by-term explanation grid
- Zone 3 (~5%): bottom footnote

──────────────────────────────────────────────────────
ZONE 1 — Loss candidates (full width, light grey #f5f5f5 background box, 1pt blue border):

  Header (bold blue 13pt): "3 Candidates — all use ridge_gcv LOCO voxel-prediction ρ"

  Three formula rows (monospace 11pt, left-aligned, navy, 1.5× line spacing):
    A.  L = 1.0·L_vuln(hV4) + 0.5·L_rank(hV4) + 0.2·L_rdm(hV4) + 0.1·L_smooth
    B.  L = 2.0·L_mwJ(V4)   + 1.0·L_rdm(V1)           + 0.2·Tikh
    C.  L = 2.0·L_mwJ(V4)   + 1.0·(1 − ρ_LOCO_V1)     + 0.2·Tikh

  Right-aligned labels (bold 10pt, navy):
    A → "Canonical  ·  sub-08 behavioral §3 PASS"
    B → "Cycle 14  ·  V1 RDM channel"
    C → "Cycle 15  ·  V1 LOCO channel  ·  B=C at matched α=2, β=1"

  Two-line distinction note (italic 9.5pt blue, below formulas):
    "A vs B/C: L_vuln (binary) → L_mwJ (magnitude-weighted).  hV4-only → V4+V1 cross-ROI.  L_smooth → Tikh."
    "B vs C: same V4 anchor — differ only in V1 channel (RDM vs LOCO rank). Both boot_frac ≥ 0.996."

──────────────────────────────────────────────────────
ZONE 2 — Term-by-term grid (2 rows × 3 cols, equal cells, 1pt grey borders):

  Each cell layout: term name (bold blue 12pt) | equation (monospace 10pt navy) | plain meaning (10pt) | key note (italic 9pt grey)

  ROW 1:

    Cell [1,1]  L_vuln
      Equation:  L_vuln = mean(1 − ρ_LOCO)  over top-K most vulnerable colors
      Plain:     "Which colors fail to decode?"
      Note:      Top-K = 3 worst LOCO colors per subject. Binary presence — depth ignored.

    Cell [1,2]  L_mwJ
      Equation:  L_mwJ = Σ_k  w_k · 1[c_k ∈ sim ∩ obs]  /  |sim ∪ obs|
                   w_k = vulnerability depth of color k
      Plain:     "Do the same colors fail, and how deeply?"
      Note:      Magnitude-weighted Jaccard. Replaces L_vuln when depth matters (Cycles 14/15).

    Cell [1,3]  L_rank
      Equation:  L_rank = 1 − Spearman ρ(vuln_sim, vuln_obs)
      Plain:     "Is the vulnerability order preserved?"
      Note:      Rank-order only — insensitive to absolute gap sizes.

  ROW 2:

    Cell [2,1]  L_rdm
      Equation:  L_rdm = 1 − cos(ΔRDM_sim,  ΔRDM_obs)
                   ΔRDM = RDM(CVD) − RDM(HC mean)
      Plain:     "Does the simulated pairwise structure match observed?"
      Note:      Cosine similarity on 28-element upper triangle. V1 or V4 separately.

    Cell [2,2]  L_smooth
      Equation:  L_smooth = ‖δθ''(θ)‖²  (2nd derivative of correction curve)
      Plain:     "Is the color correction curve smooth?"
      Note:      Penalizes sharp/oscillatory correction curves. Acts on the full δθ(θ) function.

    Cell [2,3]  Tikh  (Tikhonov)
      Equation:  Tikh = β_s² + β_c²  (L2 norm on parameters)
      Plain:     "Are the model parameters small / well-regularized?"
      Note:      Unlike L_smooth, penalizes parameter magnitude (not curve shape).
                 Prevents β overfit to voxel noise — used in Cycles 14/15 instead of L_smooth.

──────────────────────────────────────────────────────
ZONE 3 — Footnote (italic 9pt grey, full width):
"All losses evaluated on ridge_gcv encoder (fixed, future_phase1) + 2-component forward model.
 L_rdm uses cosine of 28-element ΔRDM vectors.  K=3 for L_vuln and L_mwJ."

Style: 16:9, sans-serif, single blue accent (#1f4e79). Native PPT text only — no images.
```

## B. Python data figures
*None for Slide 4* — pure text/equation slide by design.

## C. Generative schematic
*None needed* — equations and text are sufficient.

---

# SLIDE 5 — Status  ·  Behavioral evidence  ·  Plans

> *(Previously Slide 4 — renumbered to accommodate new Loss slide)*

  [1] PRE-IMAGE
       Forward exact inverse
       8/8 within 1e-3° required

  ->  [2] PERMUTATION
            8! exact label-shuffle null
            on Spearman ρ

  ->  [3] HC SANITY  (NEW)
            15 losses × 6 HC × 2 CVD
            emp_p ≤ 0.20

  ->  [4] BEHAVIORAL  (final arbiter)
            qualitative naming test
            overrides LOCO ρ if conflict

3:1 horizontal banner. No axis numbers.
```

---

# SLIDE 5 — Status  ·  Behavioral evidence  ·  Plans

> *(Previously Slide 4 — renumbered. Slide 3 = Model comparison, Slide 4 = Loss functions.)*

## A. Native PPT text

```
Create slide 4 titled
"Current Status  ·  Behavioral Evidence  ·  Next Steps".

Layout: 3 horizontal sections (top→bottom), each ~30% of body height.

SECTION 1 — "Per-subject candidates (3 fit-losses)"  (2 cards in a row, equal width)

Card sub-08 deutan  (left, green border, ~50% width)
  Status badge: OK  (green pill)
  Compact 4-col table (10pt body, 11pt header):
    | ID | Loss            | (β_s, β_c)  | Verdict                       |
    | A  | Canonical L_fit | (38°, −14°) | ★ behav §3 PASS (gold standard)|
    | B  | Cycle 14 (V1-RDM)| (58°, −36°)| HC sanity ✓ boot_frac=0.999   |
    | C  | Cycle 15 opt2 (V1-LOCO)| (68°, −38°)| HC sanity ✓ boot_frac=1.000 |
  Caption (italic 9pt, 2 lines):
    "B/C share V4 mw_jaccard anchor; differ only in V1 channel (RDM vs LOCO).
     Statistical (B/C, β_c ≈ −37°) ↔ behavioral (A, β_c = −14°) disagree;
     CLAUDE.md A4/A9: behavioral overrides → A adopted, B/C in 3-way test."

Card sub-09 protan  (right, amber border, ~50% width)
  Status badge: PENDING  (amber pill)
  Compact 4-col table  (all losses at matched weights α=2.0, β=1.0):
    | ID | Loss            | (β_s, β_c)  | Verdict                       |
    | A  | Canonical L_fit (Phase A)| (6°, −22°) | LOCO ρ=0.69 p=0.035*, HC pending |
    | B  | Cycle 14 (V1-RDM, mw_jaccard V4)| (44°, +54°)| HC sanity ✓ boot_frac=1.000 |
    | C  | Cycle 15 opt2 (V1-LOCO Spearman)| (44°, +54°)| HC sanity ✓ boot_frac=1.000 |
  Caption (italic 9pt, 3 lines):
    "B and C CONVERGE at matched weights → (44°, +54°) identical despite different V1 channel.
     A vs (B,C) have OPPOSITE β_c sign (−22° vs +54°) → anti-parallel shears.
     Both B,C depend on sub-04 HC outlier (norm 73 at boundary). Behavioral arbitrates."

SECTION 2 — "Behavioral evidence — sub-08 §3 PASS  (R+C vs 2-component head-to-head)"

Render as a compact 4-row × 4-column TABLE (all native PPT, 10pt body, 11pt header):
Header (white text on blue background):
   Stimulus                  | R+C report           | 2-component report                | Verdict

Row 1: YG-C arc (4 stim pairs:
  c3/c4, c5/c6, c5–c7,
  sRGB G/Y/c3/c4)             | 4-way blob / no order (red) | distinct (연두/warm ivory/sky/dark sky/deep blue) | ★ improved
Row 2: c1 (red), p-axis+      | preserved (green)    | preserved (green)                 | = same
Row 3: c2 (orange) narrow     | pale / washed (amber)| 연두/초록 (~40° miss) (amber)      | ≈ marginal
Row 4: c8 (magenta) narrow    | preserved (green)    | darker sky / blue-leaning (amber) | ✗ residual

Below table, add a 2-line italic caption:
"§3 primary hypothesis (YG-C 4-way collapse) FALSIFIED  →  PASS.
Residuals (c2 orange, c8 magenta) are intrinsic 8-color resolution limits, not model-class failures."

SECTION 3 — "Critical limits  +  Next steps"  (2 columns)

Left column (40% width) — "Critical limits  (Cycle 13 framework decision)":
- Specificity ABANDONED — HC FPR = 100%, baseline_ρ confound r = -0.894 across cells
   → 13 reformulations (Cycle 9~13) yielded no net gain.  Reporting: descriptive only.
- HC pool n = 6 effective at hV4 (sub-07 voxel-deficient).  Statistical specificity infeasible.
- 8-color resolution caps narrow-band recovery (c2 orange 45°, c8 magenta 315°).
- sub-10 (near-normal): no CVD-HC signal → excluded from analysis.

Right column (60% width) — "Next steps  →  Phase 3":
- [HIGH]  Sub-09 behavioral (4-way: Phase-A · mw_jaccard NEW · Cycle 12 · Machado)  →  Phase 2 closure gate
- [HIGH]  Sub-08 4-way + canonical (38°, -14°)  →  selection rule choice 직접 검증
- [MED]   Loss inventory v2 — HC fit  (Phase A canonical L_LOCO HC re-run, server pending)
- [MED]   Sub-08 c8 magenta variant  (pre-image θ ∈ {290°, 300°, 310°})
- [LOW]   Phase 2 closure document
- [→]     Phase 3 trigger (post sub-09 PASS):  JND + filtered-stim fMRI re-acquisition

Style: 16:9, sans-serif, single blue accent. Do NOT generate images.
Use status pills (rounded rectangles) for OK / PENDING / EXCLUDED in section 1.
Use ★ / = / ≈ / ✗ glyphs in the verdict column of section 2 table.
```

## B. Python data figures
*Optional* — if the advisor asks "show me where (44°, +54°) lives in HC distribution":

| File | When to insert | Source |
|---|---|---|
| `presentation/figures/data/loss_inventory_summary.png` | Insert as supplementary slide if asked about Cycle 15 winner derivation | `scripts/figs_loss_inventory.py` |

## C. Generative schematic
*None for Slide 4* — text-table layout suffices.

---

# SLIDE 6 (supplementary) — R+C model mechanism, 4-panel pipeline

**Purpose**: 별도 보조 슬라이드. R+C 가 어떻게 retinal Δλ + cortical RG-axis gain 두 단계로 분리되는지 단독으로 설명. Slide 3 Column 2 의 정적 "knob" 다이어그램을 보완.

**Source-of-truth math**: `mathematical_basis.md` §10.

**Channel decision**: 100% Channel B (matplotlib). nanobanana 부적합 — Panel A 는 실측 Stockman cone fundamentals 곡선 (axis 숫자 필수), Panel C/D 는 LMS→opponent 정확한 좌표가 figure 의 본질이라 stylized 그림은 mechanism 을 왜곡함. Panel B 의 수식 카드도 matplotlib annotation 으로 충분.

## A. Native PPT text  (paste into Claude-in-PowerPoint)

```
Create slide 5 titled
"R+C Model — Retinal Δλ + Cortical RG-axis Gain  (Pipeline View)".

Layout: full-width image insert + bottom narrative bullet block (~20% height).

ROW 1 (~75% height) image placeholder:
[INSERT: slide5_rc_panels.png  —  width fills 95% slide, centered]

ROW 2 (~20% height) narrative — 3 bullets, 11pt black, single-spaced:
- Panel A:  Retinal parameter Δλ shifts ONE cone sensitivity (M for deutan, L for protan).
            Other cones unchanged.
- Panels B+C:  The shift propagates LMS → opponent (RG, BY) → atan2 hue.
            Both RG and BY coordinates change — Δλ does NOT directly rotate hue.
- Panel D:  Cortical gain g acts ONLY on the RG-axis displacement
            (RG_ret − RG_base) × (1+g).  BY is untouched.
            g = −1 ⇒ exact compensation;  g < −1 ⇒ overshoot (sub-08 g = −2.25).

Bottom takeaway (italic blue, 11pt, single line):
"Two parameters, two stages — separable mechanism enables stimulus-space inverse via δθ(r, g)."

Footer (italic 9pt grey, full width):
"See mathematical_basis.md §10 for derivation. Test stimuli: 5 monochromatic wavelengths
(red 600, yellow 580, yel-grn 540, cyan 500, blue 460 nm) integrated against Stockman 2-deg fundamentals."

Style: 16:9, sans-serif, single blue accent (#1f4e79). Do NOT generate images.
Insert image at the indicated absolute path (provided in user message).
Image absolute path:
  /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase5_filter_optimization/presentation/figures/data/slide5_rc_panels.png
```

## B. Python data figure  (already rendered)

| File | Content | Source script |
|---|---|---|
| `presentation/figures/data/slide5_rc_panels.png` | 4-panel: A) Stockman LMS + M-cone shift; B) forward-equation card; C) opponent plane baseline→retinal; D) opponent plane retinal→final (RG-axis horizontal displacement) | `scripts/visualization/figs_slide5_rc_panels.py` |

**Tunable parameters** (top of script):
- `DELTA_LAMBDA = 18.0` — retinal shift in nm (chosen for visual clarity; per-subject fits use 0–20 nm)
- `G_GAIN = -0.7` — cortical gain (illustrative; sub-08 actual g = −2.25, sub-09 = −1.10)
- `TEST_WL` — 5 monochromatic test wavelengths spanning visible spectrum

Re-render after parameter change:
```bash
conda activate srm
python analysis/phase5_filter_optimization/scripts/visualization/figs_slide5_rc_panels.py
```

## C. Generative schematic
*None for Slide 5* — entire figure is data-driven. Using AI image generation here would fabricate Stockman curve shapes and (RG, BY) point positions, defeating the figure's purpose.

## Speaking notes  (~1.5 min, when invoked)

1. Panel A: "M-cone sensitivity 가 Δλ 만큼 long-wavelength 쪽으로 shift. L, S 는 그대로."
2. Panel B/C: "이 shift 가 LMS 적분값을 바꾸고, 그 결과 opponent (RG, BY) 좌표가 둘 다 이동. 5색 화살표로 표시."
3. Panel D: "Cortical gain 은 RG 축 변위만 (1+g) 배. BY 는 안 건드림 — 모든 화살표가 수평."
4. Closing: "두 파라미터가 두 stage 로 깨끗이 분리되어 stimulus-space inverse δθ(r, g) 가 정의 가능. 단 atan2 합성 비선형성 때문에 sub-09 처럼 큰 변형에서는 8/8 exact pre-image 가 보장 안 됨 → 2-component 채택 동기."

## When to use this slide
- Advisor 가 R+C 메커니즘을 자세히 묻는 경우 (Slide 3 columnaire 가 부족할 때 backup)
- 논문 figure draft 의 직접 후보 (해당 figure 를 single-column 또는 full-width 로 사용 가능)
- 후속 modeling discussion (g 의 physiological 의미, overshoot 해석) 의 reference

---

# SLIDE 7 (supplementary) — Tregillus 2021 비교 (advisor 질문 대비)

**Purpose**: Advisor 가 "이게 Tregillus 와 어떻게 다르냐"고 물을 때 즉답. 두 연구의 observable·자극·결론 차이를 명확히 구분.

**Source**: NotebookLM ColorBlind_comprehensive Tregillus_2021_compensation.pdf 직접 인용 (2026-05-04 query).

## A. Native PPT text

```
Create slide 6 titled
"Comparison with Tregillus et al. 2021 (Curr Biol)".

Layout: 2-column side-by-side table + bottom takeaway.

LEFT COLUMN (50% width) — "Tregillus 2021"
  Stimuli       :  2 cardinal axes only (L-vs-M, S-vs-LM)
                  × 4 contrasts = 8 conditions
                  reversing radial sinewave gratings
  DV            :  ROI-mean GLM β  (univariate)
  ROIs          :  V1, V2v, V3v
  Analysis      :  Naka-Rushton CRF  R(c) = R_max·c^(p+q)/(c^q + c50^q)
                  + 2x(3x2x4) mixed ANOVA on β
  Compensation  :  contrast scaling factor (scalar per ROI)
  Site          :  V2v/V3v amplified, V1 reduced as predicted
                  V1 AT vs CN p = 0.04*  ·  V2v p = 0.62  ·  V3v p = 1.00
  N             :  5 CN + 5 AT (2 deutan, 3 protan)

RIGHT COLUMN (50% width) — "Our project (Phase 2)"
  Stimuli       :  8 hues at CIELab L*=75 C*=40 ring, single contrast
                  6 runs × 8 colors
  DV            :  voxel pattern (multivariate)
  ROIs          :  V1, V2, V3, hV4
  Analysis      :  ridge_gcv encoder + LOCO + ΔRDM + 2-comp angular
  Compensation  :  angular distortion δθ(c) per color
                  + (β_s, β_c) directional parameters
  Site          :  per-subject best ROI (sub-08 hV4 LOCO p = 0.004**)
                  univariate post-hoc: a*-axis reduced V1→hV4 hierarchy-wide
                  (NOT Tregillus's V1-only reduction pattern)
  N             :  7 HC + 2 actionable CVD (sub-10 excluded)

BOTTOM TAKEAWAY (italic blue, full width):
"Different observables, complementary evidence:
   Tregillus = univariate cortical AMPLITUDE on cardinal-axis stimuli
   Ours      = multivariate pattern GEOMETRY across full hue circle
Univariate post-hoc on our data does NOT replicate Tregillus's
'V1-only reduction' — instead a*-axis reduces hierarchy-wide, with
b*-axis preserved. Pattern-level signal is where compensation/distortion
actually localizes in our 8-hue paradigm."

COMPARATIVE TABLE (compact, 4 rows, 3 columns; insert as compact native table mid-slide):
                       | Tregillus 2021         | Emery 2021                        | Ours
  What is measured     | BOLD amplitude (β CRF) | perceptual hue-scaling response   | cortical voxel pattern (LOCO ρ)
  Functional form      | Naka-Rushton CRF gain  | 1st-harmonic non-uniform warp*    | per-color 1st-harmonic warp δθ(c)
  Per-stim variation   | NO (1 scalar/ROI)      | YES (cardinal=0, S-axis=max)*     | YES (cardinal=0, diag=max)
  Observable level     | univariate ROI-mean β  | behavioral % rating (CVD vs NT)   | multivariate voxel pattern

  *Emery Factor 4: zero loading at LvsM axis (0°/180°), peak at S-axis (90°/270°),
   antiphase B vs Y — same structural form as β_s·sin(θ). [Confirmed NotebookLM 2026-05-06]

EXTENDED TAKEAWAY (italic blue, full width, 3 lines):
"Same 1st-harmonic compensation structure, different observation levels:
   Tregillus = univariate BOLD scalar (cardinal-axis stimuli) ·
   Emery = behavioral B/Y antiphase warp (CVD hue-scaling, Factor 4 ≅ β_s·sin(θ)) ·
   Ours = multivariate cortical per-color warp (8-hue LOCO).
Emery–β_s structural match confirmed; coordinate-frame correction needed for numerical comparison."

Footer (italic 9pt grey):
"Univariate post-hoc result: results/cardinal_axis_amplitude/summary_raw.json"

Style: 16:9, sans-serif, single blue accent. Native PPT text only.
```

## B. Python data figure (optional supplementary)

| File | Content | Source script |
|---|---|---|
| `results/cardinal_axis_amplitude/summary_raw.json` | Per-subject z-scores on a*/b*/diag axes × 4 ROIs | `scripts/diagnostics/cardinal_axis_amplitude.py` |

권장 figure (만들지 않은 상태, 필요 시 생성):
- 4-ROI bar plot, x = ROI, y = a*-axis z-score, points for sub-08/09/10 vs HC band (mean±SD shade)
- Tregillus 패턴 (V1 negative, V2/V3 ≈ 0) overlay 로 dashed reference line

## C. Generative schematic
*None* — 비교 표는 native text 충분.

## Speaking notes (~1 min)
1. "Tregillus 2021 은 univariate ROI-mean β on cardinal-axis 자극으로 V1 reduction + V2v/V3v compensation 을 보임."
2. "우리는 8-hue ring 의 multivariate pattern. 자극·DV 둘 다 다름."
3. "사후 univariate 분석 (cardinal_axis_amplitude.py) 에서 sub-08/09 a*-axis 가 V1→hV4 hierarchy-wide 로 reduced — Tregillus pattern replicate 안 됨. 우리 자극이 cardinal modulation 이 아닌 fixed-chroma ring 이라 cardinal projection 약화되는 게 가장 가능한 설명."
4. "결론: complementary 관계. 그들 = amplitude 측면, 우리 = angular geometry 측면."
5. "세 연구가 같은 1st-harmonic compensation family를 다른 mathematical observable로 잡은 것: Tregillus = scalar amplitude scaling, Emery = uniform 축 위치 회전, 우리 = per-color non-uniform warp. 수치 직접 비교 부적절, structural family로만 비교."

## When to use
- Advisor 가 "Tregillus 와 어떻게 다른가" / "compensation 이 V2/V3 라며 너희는 왜 hV4 fit 이 best 인가" 질문 시
- 논문 discussion §literature comparison 직접 source

---

## Asset inventory  (all paths absolute on this Mac)

### Python data figures (channel B — already rendered)

```
presentation/figures/data/
├── activation_overview.png        ← Slide 2 row 1
├── model_vs_baseline.png          ← Slide 2 row 2
├── loss_inventory_summary.png     ← Slide 4 supplementary
├── slide5_rc_panels.png           ← Slide 5 supplementary (R+C 4-panel mechanism)
├── two_comp_stretch_anatomy.png   ← Slide 5b backup — 2-comp ±β stretch anatomy
│                                    (figs_2comp_stretch.py; explains sign-dependent
│                                     compression/expansion when β framing questioned)
└── (cross-link) ../../results/diagnostics/aphi_sanity/aphi_polar.png
                                     ← Slide 4/Q&A backup — single-shear (A,φ) sanity
                                       (sub-09 Phase A is anti-parallel to other 3 candidates)
```

Composite single-image fallbacks (slide1_summary.png · slide2_activation_decoder.png ·
slide3_model_loss.png · slide4_status_plans.png · phase2_meeting_overview.png) were
**deleted on 2026-05-04**. Their text content is now rendered natively as Channel A
(see Slides 1–4 prompts above), so the duplicated single-image versions are obsolete.

### Generative schematics (channel C — must generate)

```
presentation/figures/schematics/
├── README.md                       ← generation workflow + verification checklist
├── slide3_model_mechanisms.png     ← REQUIRED — Slide 3 row 1
├── slide1_pipeline_inset.png       ← OPTIONAL — Slide 1 Q1 inset
└── slide3_eval_pipeline.png        ← OPTIONAL — alternative to Slide 3 row 3 text
```

To generate the schematics:
1. Open GPT-5 Image / nanobanana / Imagen / DALL·E
2. Paste the prompt from the relevant Slide section's "C. Generative schematic"
3. Download the chosen result
4. Save to the path above
5. Insert into the slide via Claude-in-PPT (or manually)

---

## Speaking notes  (~10-min meeting)

### Slide 1  —  open with summary  (1 min)
1. "프로젝트 전체 요약. 4분면 = 4 슬라이드의 detail 매핑."
2. Q1 → Q2 → Q3 → Q4 순서대로 한 줄씩 읽기.
3. Pivot: "이제 detail로 넘어가겠습니다."

### Slide 2  —  Activation + Decoder detail  (2 min)
1. Row 1 (활성화): "4 ROI tuning 모두 HC IQR 안. Group magnitude 모두 n.s."
2. Pivot: "→ CVD는 magnitude 손실 아님. 그럼 차이는?"
3. Row 2 — LORO classification: "OUR BEST 0.793 vs B&H 2009 0.545 (+25pp). 또한 B&B 2025도 SRM 사용해 8-AFC했는데 between-subject 0.39–0.56 — 우리 within-subject 0.793과 paradigm 차이 있지만 SRM이 색 표현 잡는다는 같은 흐름. HC→CVD p=0.668 → shared mapping."
4. Row 2 — LOCO (I) Color decoding vs B&H 2009: "Predict held-out hue, FE+Proc 8-ch basis. HC MAE 75.7° (chance 90°), CVD elevated."
5. Row 2 — LOCO (II) Voxel prediction (ridge_gcv encoder): "V1 d=1.61* · V2 d=1.85* · hV4 d=1.19. CVD ≤ null."
6. Closing: "Discrimination 보존 + 두 LOCO 모두 impaired = color-space distortion."

### Slide 3  —  Model + Loss  (3 min)
1. Row 1 (3-model schematic): "Mechanistic level 별로 3개. 2-Component이 ★."
2. Row 2 (L_LOCO equation): "α=1.0 vulnerability 가장 큼. 8! exact perm null."
3. Row 3 (4-stage eval): "Pre-image → Permutation → HC sanity (NEW) → Behavioral (final)."
4. Closing: "Behavioral PASS overrides LOCO ρ — sub-08 R+C → 2-comp 사례."

### Slide 4  —  Status + Behavioral + Plans  (3 min)
1. Section 1 (per-subject): "sub-08 OK, sub-09 PENDING (NEW candidate 추가), sub-10 제외."
2. Section 2 (behavioral table): 7행 가리키며 "★ 4개, = 1개, ≈ 1개, ✗ 1개. YG-C 4-way collapse 해소가 primary PASS."
3. Section 3 (limits): 솔직하게 — "Specificity 13 cycle 후 포기, descriptive only."
4. Section 3 (next steps): "두 HIGH = sub-09 + sub-08 4-way 행동. 후 Phase 3 trigger."

### Closing line  (~30 sec)
"활성화 정상 (Slide 2) → discrimination 정상 + interpolation 망가짐 (Slide 2) → stimulus-space inverse filter 설계 (Slide 3) → sub-08 행동 PASS, sub-09 대기 (Slide 4) → 다음 단계 = sub-09 행동 + Phase 3."

---

## Verification checklist  (before pasting)

- [ ] All 4 Claude-in-PPT prompts use ABSOLUTE Mac paths for image references
- [ ] Slide 2 references `activation_overview.png` AND `model_vs_baseline.png`
- [ ] Slide 3 references `schematics/slide3_model_mechanisms.png` (must be generated first)
- [ ] No prompt asks Claude-in-PPT to generate new images (only inserts pre-rendered ones)
- [ ] All quantitative numbers are in Python figures (channel B), not bumbled into the AI schematic
- [ ] All conceptual diagrams are in AI schematics (channel C), not Python
- [ ] All other text is native PPT (channel A), not embedded in figures
- [ ] sub-10 mentioned only as "excluded" in Slides 1, 4 (CLAUDE.md rule §7); appears as near-normal in Slide 2 activation plot (allowed)
- [ ] No specificity claim in any slide — descriptive HC sanity emp_p only
- [ ] Status pills (OK / PENDING / EXCLUDED) use color-coded rounded rectangles, not just text

---

## Regeneration commands

```bash
cd analysis/phase5_filter_optimization
conda activate srm

# Channel B — academic data figures (re-run if numbers change)
python scripts/visualization/figs_activation_overview.py
python scripts/visualization/figs_model_vs_baseline.py
python scripts/visualization/figs_loss_inventory.py
python scripts/visualization/figs_slide5_rc_panels.py    # Slide 5 supplementary

# Channel C — generative schematics (re-run if model definitions change)
# → Open GPT-5 Image / nanobanana, paste the prompt from this file, save to:
#   presentation/figures/schematics/slide3_model_mechanisms.png

# Channel A — native PPT text (re-render if results change)
# → Open PowerPoint with Claude add-in, paste prompts from this file
```

**Source-of-truth files** (update these first, then regenerate):
- `CLAUDE.md` §3 — per-subject status, filter parameters
- `README.md` — current candidate table (section "Current Filter Candidates")
- `behav_validation.md` §3 — sub-08 behavioral verdict matrix
- `results/inventory/loss_inventory.{md,csv}` — loss inventory ratings
- `analysis/phase3_decoder_comparing/README.md` — LORO 3-alignment × 6-model table
- `analysis/phase4_forward_model/RESULTS.md` — LOCO ridge_gcv, FE-K ablation
- `analysis/phase2_SRM_across_between/results/activation_prior/activation_prior_results.json` — activation per-color/group
