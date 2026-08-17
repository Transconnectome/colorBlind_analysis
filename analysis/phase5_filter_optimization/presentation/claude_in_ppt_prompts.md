# Claude-in-PowerPoint Prompt Bundle — Simulation, Recoverability, Behavioral Comparison

**Usage.** Open PowerPoint, launch the Claude add-in, and paste each prompt below into the chat one at a time. Each prompt is self-contained and names a single absolute image path on this Mac. No prompt asks Claude to generate new imagery. Slide 1 and Slide 6 and Slide 7 are text-only (formula card / text dissociation / literature matrix).

**Global style directive (apply to every slide).**
> Style: academic, 16:9, sans-serif, minimal chrome, single blue accent. Do NOT generate new images. Use only the referenced file path verbatim. Keep body text ≥18pt.

---

## Slide 1 — Three simulation models for CVD (formula card, no image)

```
Create slide 1 titled "Three Forward Models of CVD, at Three Mechanistic Levels".

Layout: three-column formula card, no image. One column per model.

Column 1 — Machado 2009 (retinal, 1-DOF):
- Parameter: Δλ (nm peak-sensitivity shift of L or M cone)
- Forward map: θ' = machado_shifted_hue(Δλ, family)
- Biophysical level: pre-receptoral cone fundamentals
- Invertibility: monotone only for small Δλ; arc collapses at large Δλ

Column 2 — R+C (retinal + cortical opponent gain, 2-DOF):
- Parameters: Δλ, g
- Forward map: rg' = rg_base + (1+g)·(rg_ret − rg_base); hue' = atan2(by_ret, rg')
- Biophysical level: retinal shift + post-receptoral RG gain
- Invertibility: algebraic (bijective) but perceptually single-axis

Column 3 — 2-Component (cortical angular dilation, 2-DOF):
- Parameters: β_s, β_c
- Forward map: θ' = θ + β_s·cos(θ − 90°) + β_c·cos(θ − θ_conf)
- θ_conf = 16° (protan) / 150° (deutan)
- Biophysical level: cortical hue map with S-axis rescaling + confusion-axis rotation
- Invertibility: smooth, bijective over the full hue circle

Bottom takeaway: "Three models, three mechanistic levels — retinal, hybrid retinal–cortical, and purely cortical. Each is invertible in a different sense, and only one is perceptually adequate."

Footer citation (small italic): Machado et al. 2009; Brettel, Viénot & Mollon 1997; Emery et al. 2021.

Style: academic, 16:9, sans-serif, minimal chrome, single blue accent. Do NOT generate new images. Use only the referenced content; no clip-art.
```

---

## Slide 2 — Inverse-inference pipeline

```
Create slide 2 titled "From Structured Neural Representations to Individualized Correction Filters".

Layout: full-width figure, 2-line caption below.

Insert image from absolute path:
/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/docs/ICML_workshop/icml2026/figures/fig1a_pipeline.png
Position: centered, 85% of slide width, fill most of the slide.

Caption (below image, 2 lines):
- "hV4 hue responses → LOCO interpolation-vulnerability profile → inverse inference of low-DOF mechanistic model → stimulus-space correction filter."
- "Each step is subject-specific; the final filter is the individualized digital biomarker."

Footer citation (small italic): Adapted from fig1a_pipeline, SD4H 2026 (LOCO: Brouwer & Heeger 2009).

Style: academic, 16:9, sans-serif, minimal chrome, single blue accent. Do NOT generate new images. Use only the referenced file.
```

---

## Slide 3 — Model fits to LOCO vulnerability

```
Create slide 3 titled "Subject-Specific LOCO Fits: Different Models Win for Different CVD Subjects".

Layout: full-width figure on top (≈70%), short bullet block below.

Insert image from absolute path:
/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/docs/ICML_workshop/icml2026/figures/fig1_panels_bcd.pdf
Position: centered, full width of slide.

Bullets below figure:
- sub-08 (Ishihara-moderate deutan): R+C fit — Spearman ρ = 0.857, label-perm p = 0.005
- sub-09 (Ishihara-moderate protan): Machado fit — Spearman ρ = 0.762, label-perm p = 0.018
- sub-10 (Ishihara-confirmed, behaviorally near-normal): p = 0.559 (null at LOCO and SRM)

Bottom takeaway: "LOCO vulnerability is recoverable by a low-DOF model — but the winning family differs by subject, motivating model comparison rather than a single forward map."

Footer citation (small italic): fig1 b–d, SD4H 2026; Brouwer & Heeger 2009 (LOCO).

Style: academic, 16:9, sans-serif, minimal chrome, single blue accent. Do NOT generate new images. Use only the referenced file.
```

---

## Slide 4 — Recoverability: Machado arc compression

```
Create slide 4 titled "Recoverability I — Retinal-Only Inversion Fails When the Perceived Arc Compresses".

Layout: full-width figure on top (≈65%), bullet block below.

Insert image from absolute path:
/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/docs/ICML_workshop/icml2026/figures/fig2_collapse.png
Position: centered, full width of slide.

Bullets below figure:
- sub-08 Δλ=2.0 nm: perceived hue arc spans the full circle — inverse problem is bijective (8/8 exact).
- sub-09 Δλ=13.5 nm: perceived arc compresses 360° → 96°; c4/c5/c6 map to the same θ′ ≈ 282.1°.
- Consequence: exact pre-image exists for only 4/8 target hues — three distinct stimuli collapse to one perceived color.
- Implication: a 1-DOF retinal model cannot support a universal stimulus-space filter for moderate protanomaly.

Bottom takeaway: "Non-bijectivity is not a numerical artifact — it is a physiological prediction of the 1-DOF cone-shift model."

Footer citation (small italic): fig2_collapse, SD4H 2026; Machado et al. 2009.

Style: academic, 16:9, sans-serif, minimal chrome, single blue accent. Do NOT generate new images. Use only the referenced file.
```

---

## Slide 5 — 2-component universal bijectivity

```
Create slide 5 titled "Recoverability II — A 2-DOF Cortical Model Is Bijective for Both CVD Subjects".

Layout: two images side-by-side (left 50% / right 50%), bullets at bottom (full width).

Insert image 1 from absolute path (left half):
/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization/results/2component_comprehensive_v2/sub-08_delta_theta_bars.png
Caption under left image: "sub-08 (deutan): 2-component preimage — mean |δθ| = 46.3°, max = 104.2°."

Insert image 2 from absolute path (right half):
/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization/results/2component_comprehensive_v2/sub-09_delta_theta_bars.png
Caption under right image: "sub-09 (protan): 2-component preimage — mean |δθ| = 20.1°, max = 48.1°."

Bullet block at bottom:
- 2-component is the only model with exact pre-image (8/8, residual < 10⁻³ °) for BOTH CVD subjects.
- Under 2-component, sub-09 severity reclassifies from "spectral filter required" (Machado arc-collapse) → "stimulus-space sufficient".
- S-cone axis (β_s) design choice is physiologically grounded: Emery 2021's AT hue-scaling data shows step-like expansion near B/Y + compression near R/G — the same geometric operation as β_s·cos(θ−90°).

Bottom takeaway: "Bijectivity and physiologically grounded model design (S-cone + confusion axes from independent literature) make 2-component the Phase-2 filter of record."

Footer citation (small italic): 2component_comprehensive_v2, this study; Emery et al. 2021.

Style: academic, 16:9, sans-serif, minimal chrome, single blue accent. Do NOT generate new images. Use only the two referenced files.
```

---

## Slide 6 — Behavioral report: R+C vs 2-component (sub-08), TEXT ONLY

```
Create slide 6 titled "Behavioral Report (sub-08) — R+C Collapses Yellow-Green–Cyan; 2-Component Preserves the Gradient".

Layout: TWO-COLUMN text slide. NO images on this slide.

Left column header: "R+C filter (Δλ=2.0, g=+2.25)"
Left column bullets:
- c3 yellow + c4 yellow-green + c5 cyan + c6 blue-cyan → reported as one merged color band (YG-C 4-way collapse).
- c1 red reported as ivory / light-pink — red salience lost.
- c5 cyan effectively disappears as a distinct percept.
- Single-knob RG rescaling forces the entire yellow → blue arc through one axis.

Right column header: "2-component filter (β_s=38°, β_c=−14°)"
Right column bullets:
- c3 yellow vs c4 yellow-green: distinct, no merge.
- c5 / c6 / c7: sky-blue → darker-sky → deep-blue — graded, no collapse.
- c1 red: retained as red; c8 magenta: blue-leaning (residual).
- Two independent angular components (S-axis dilation + confusion rotation) preserve local discriminability.

Bottom row (full width, single highlighted line):
"Residual failures under 2-component: c2 orange (narrow-band miss, ~40° off prediction) and c8 magenta (blue-leaning bias, potential β_m extension)."

Bottom takeaway: "Algebraic invertibility is necessary but not sufficient — R+C is invertible yet perceptually collapses; 2-component is invertible AND preserves reported hue separation."

Footer citation (small italic): behav_validation.md §1, §3, §4 (sub-08 qualitative report, this study).

Style: academic, 16:9, sans-serif, minimal chrome, single blue accent. NO IMAGES on this slide. Do NOT generate new visuals.
```

---

## Slide 7 — Literature alignment + Phase-2 decision

```
Create slide 7 titled "Literature Alignment and Phase-2 Decision".

Layout: compact table on top (≈55% of slide), decision + next-steps block below. NO image.

Table columns: Citation | Method (one-line) | Our relation
Table rows:
- Machado et al. 2009 | 1-DOF cone-fundamental shift fit to dichromat matching | REPLICATES as baseline forward map
- Brettel, Viénot & Mollon 1997 | Confusion-line dichromat simulator | Predecessor to Machado; context only
- Tregillus & Webster 2021 | Longitudinal contrast adaptation, hue scaling (20–40%) | CONTRADICTS: R+C g=+2.25 (≈125%) exceeds the physiological gain range
- Emery et al. 2021 | Behavioral hue scaling; B–Y axis rotation = 21.4° | S-cone axis (β_s) design GROUNDED by AT expansion/compression pattern
- Brouwer & Heeger 2009 | V4/VO1 LOCO reconstruction of novel hues | SUPPORTS hV4-primary inversion; EXTENDS from HC to CVD
- Bannert & Bartels 2018 / 2025 | SRM on hue-preferring voxels + trial-by-trial decoding | REPLICATES shared HC–CVD geometry; EXTENDS to distortion quantification

Decision block (full width, below table, highlighted):
"Phase-2 filter adopted: 2-Component (β_s, β_c). Rationale — only model that is (i) bijective for both CVD subjects, (ii) perceptually adequate on sub-08, and (iii) physiologically grounded via Emery 2021 (S-cone axis) + Brettel 1997 (confusion axis)."

Phase-3 next steps (bullet row below decision block):
- sub-08 fine-grid behavioral retest around c2 (orange) and c8 (magenta) residuals.
- sub-09 2-component qualitative test (analogous to sub-08 protocol).
- Note: sub-10 excluded per Phase-2 CLAUDE.md rule (no CVD-vs-HC signal).

Framing note (small italic, bottom-left): "Framing: this CVD × hue-interpolation × alignment × filter-design combination is rare or absent in the literature — not claimed as a first study."

Footer citation (small italic, bottom-right): References list — see markdown companion simulation_recoverability_behavior.md.

Style: academic, 16:9, sans-serif, minimal chrome, single blue accent. NO IMAGES. Table should fit in one screen without scrollbar.
```

---

## Slide 8 — Physiological Grounding: S-Cone Axis + hV4 ROI (IMAGE SLIDE)

```
Create slide 8 titled "Physiological Grounding: Model Design Choices Supported by Independent Literature".

Layout: full-width figure on top (≈60%), structured bullet block below.

Insert image from absolute path:
/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization/results/figures/literature_convergence/beta_s_emery_convergence.png
Position: centered, full width of slide.

Bullet block below figure (two columns):

Left column header: "S-Cone Axis Choice ← Emery et al. 2021"
Left column bullets:
- AT hue-scaling raw data: expansion near B/Y poles, compression near R/G — step-like pattern.
- This pattern is geometrically identical to angular dilation: β_s·cos(θ−90°).
- Emery's 21.4° phase shift is a summary statistic DERIVED FROM this underlying dilation.
- Our model directly parameterizes the operation that produces Emery's observed pattern.
- NOTE: β_s values and Emery's 21.4° are DIFFERENT physical quantities (dilation vs rotation phase) — no numerical comparison claimed.

Right column header: "hV4 ROI Choice ← B&H 2009 + Kuriki 2025"
Right column bullets:
- Brouwer & Heeger 2009: V4/VO1 are the ONLY areas supporting novel-color reconstruction (same method as our LOCO).
- Kuriki et al. 2025: hV4 cortical RDM correlates with appearance-based perceptual RDM → cortical geometry directly linked to perception.
- Tregillus et al. 2021: higher visual areas show progressive compensation → hV4 > V1 direction consistent.
- Our 2-component model significant at hV4: sub-08 p=0.004**, sub-09 p=0.035*.

Bottom takeaway (full width, highlighted):
"The 2-component model encodes physiologically established structure: S-cone axis (Emery 2021 expansion/compression pattern) and confusion lines (Brettel 1997). It fits significantly at hV4, the cortical locus independently established as the color interpolation hub (B&H 2009) with direct perceptual relevance (Kuriki 2025). The grounding is structural, not numerical."

Footer citation (small italic): Emery et al. 2021; Brouwer & Heeger 2009; Kuriki et al. 2025; Brettel et al. 1997.

Style: academic, 16:9, sans-serif, minimal chrome, single blue accent. Do NOT generate new images. Use only the referenced file.
```

---

## Slide 9 — Tregillus cortical compensation hierarchy (IMAGE SLIDE)

```
Create slide 9 titled "Cortical Compensation Hierarchy: V1 Deficit Disappears at V2v/V3v".

Layout: full-width figure on top (≈55%), structured content below.

Insert image from absolute path:
/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization/results/figures/literature_convergence/tregillus_compensation_hierarchy.png
Position: centered, full width of slide.

Content below figure — a compact 3-row table + takeaway:

Table columns: Visual Area | AT vs CN (L-vs-M) | Amplification Factor | Interpretation
Table rows:
- V1 | AT < CN (p = 0.04*) | 2.94× (SD = 2.81) | Retinal deficit passes through — no compensation
- V2v | AT ≈ CN (p = 0.62, NS) | 6.39× (SD = 5.21) | Full compensation — AT indistinguishable from CN
- V3v | AT ≈ CN (p = 1.00, NS) | 7.82× (SD = 5.76) | Full or slight over-compensation

Below table, annotation box:
"Our R+C model's g = −1.10 for sub-09 (10% overcompensation) falls within the range implied by V2v/V3v amplification factors. Tregillus's V1→V2v dissociation parallels our finding that V1 LOCO fails (null-level) while hV4 LOCO succeeds — compensation emerges between early and mid-level cortex."

Additional context line (small):
"Sample: N=7 AT (3 DA, 4 PA) vs 7 CN. Two experiments: simple fixation (Exp1) + attentional control (Exp2). Results replicated across both tasks → not top-down modulation."

Footer citation (small italic): Tregillus et al. (2021) Current Biology, 31(5), 936-942; Werner, Marsh-Armstrong & Knoblauch (2020) Curr Biol (filter-induced plasticity).

Style: academic, 16:9, sans-serif, minimal chrome, single blue accent. Do NOT generate new images. Use only the referenced file.
```

---

## Slide 10 — Literature convergence summary (IMAGE SLIDE)

```
Create slide 10 titled "Literature Verification Summary — Three Independent Lines of Evidence".

Layout: full-width figure on top (≈65%), compact summary below.

Insert image from absolute path:
/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization/results/figures/literature_convergence/literature_convergence_summary.png
Position: centered, full width of slide.

Summary below figure (3 numbered points):

1. S-cone axis (β_s) design is physiologically grounded: Emery 2021's AT hue-scaling shows step-like expansion near B/Y + compression near R/G — the same geometric operation as β_s·cos(θ−90°). The grounding is structural (model encodes the right axis), not numerical (β_s values and Emery's 21.4° are different physical quantities). 2-component with this S-cone axis fits significantly at hV4 for both CVD subjects (p=0.004/0.035).

2. g = −1.10 (this study, R+C model) is consistent with Tregillus 2021's fMRI evidence of V2v/V3v amplification restoring AT responses to CN levels — 10% overcompensation within the physiological range.

3. hV4 as interpolation primary (this study, LOCO permutation) replicates Brouwer & Heeger 2009's finding that V4/VO1 are the only areas supporting novel-color reconstruction, and extends it from HC to CVD for the first time.

Bottom takeaway (full width, highlighted):
"The 2-component model is not merely a curve fit — its design encodes physiologically established structure: S-cone axis (Emery 2021), confusion lines (Brettel 1997), fitted at hV4 (B&H 2009 + Kuriki 2025). Machado Δλ provides the only direct numerical comparison (severity ranges match). This physiological grounding, not parameter-value convergence, justifies cortical-level correction filters."

Footer citation (small italic): Emery et al. 2021; Tregillus et al. 2021; Brouwer & Heeger 2009; Bannert & Bartels 2018.

Style: academic, 16:9, sans-serif, minimal chrome, single blue accent. Do NOT generate new images. Use only the referenced file.
```

---

## Verification checklist (before pasting into Claude-in-PowerPoint)

- [ ] Slide 1, Slide 6, and Slide 7 contain NO image path (text-only slides).
- [ ] Slides 2, 3, 4, 5 reference existing file paths verified on this Mac.
- [ ] Slides 8, 9, 10 reference literature convergence figures (newly generated).
- [ ] No prompt asks Claude to generate, synthesize, or redraw imagery.
- [ ] R+C sign convention cited as `g = +2.25` (from the preimage JSON; behav_validation §2-2 uses the opposite sign — conclusion is invariant).
- [ ] sub-10 is mentioned once (Slide 3, null result) and excluded from Phase-3 next steps per CLAUDE.md rule 7.
- [ ] "Rare or absent" framing in Slide 7 — no "first study" language.
- [ ] Emery 2021 values cited correctly: 21.4° B-Y rotation, t(34)=5.95, p<0.001, N=10 AT vs 26 NT.
- [ ] Tregillus 2021 values cited correctly: V1 2.94×, V2v 6.39×, V3v 7.82×; V1 p=0.04, V2v p=0.62, V3v p=1.00.
- [ ] β_s framed as physiological grounding (S-cone axis choice supported by Emery 2021's step-like dilation pattern) — NOT numerical convergence. β_s and Emery's 21.4° are different physical quantities. Claim: model structure is physiologically grounded, not parameter-value match. hV4 LOCO significance (p=0.004/0.035) is the primary evidence.
