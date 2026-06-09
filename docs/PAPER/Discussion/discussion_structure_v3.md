# Discussion v3 — Structure, Evidence Pack & Writing Brief

> Created 2026-06-08. Supersedes the spine of `discussion_v2.tex` (which was hV4-centric and leaned on a now-retired "detection–correction divergence" argument). This file is the **authoritative brief** for drafting Discussion v3 and the reference for downstream work.

---

## 0. Headline reframe (the thing v2 got wrong)

v2 framed the paper as **"hV4 color geometry → filter"** (an ROI-centric causal chain) and treated LOCO as the "operative corrective target." Both are wrong:

- The filter is **not** fit on hV4 LOCO. LOCO did **not** enter either winning loss combination (Methods §selection). Fits use **behavioral JND (γ) + ΔRDM (V1/V2)**.
- LOCO/RDM are **not** "the target." Their **의의 (significance)** is that they **measure a neural representational/geometric difference** — that CVD color deficits are a *structured geometric distortion* of cortical color representation (shape/structure/relational geometry), not a 1-D signal loss.

**Correct headline:**
> CVD color deficits manifest as an **individual-specific geometric distortion** of the cortical color representation. **RDM characterizes the structure** of that distortion; **LOCO is its functional consequence** (broken continuous-hue interpolation). **Neural and behavioral measurements jointly ground** a personalized stimulus-space correction. The filter is *downstream* of the finding — not the headline.

**Banned framing:** the word "target" for LOCO/RDM; the word "diverge"/"divergence" for retinal-vs-cortical corrections; any §S16 cosine-similarity (−0.54) argument (REMOVED entirely, see §4).

---

## 1. Three-contribution spine

| Block | Contribution | Status | ¶ |
|---|---|---|---|
| **C1** | CVD has a **structural/geometric difference** in cortical color representation (RQ1). RDM = structure, LOCO = functional consequence. | current result | ¶2 |
| **C2** | A **personalized filter built from individual cortical structural information** — neural adds information behavior cannot access; the method yields a per-person filter. | current result | ¶3–¶5 |
| **C3** | **Performance superiority** of the personalized filter vs OS-builtin (Windows/macOS) color filters and no-filter baseline. | **Phase 3, forward-looking TODO** | ¶6 |

---

## 2. Paragraph-by-paragraph skeleton (topic sentences)

**¶1 — Executive summary** (Bannert-style: restate what we did + one-two punch of findings, then "these results suggest…"). CVD color deficit = individual geometric distortion of cortical color representation; RDM structure + LOCO function; neural+behavior jointly ground a personalized stimulus-space correction.

**¶2 — C1: structural/geometric distortion (RQ1).** RDM (structure) and LOCO (functional consequence) are two views of one geometric distortion: ΔRDM shows *which pairwise distance structure* deviates from HC (V2 sub-08 p=0.040; V1 sub-09 p=0.007), LOCO shows *where the continuous-hue manifold readout breaks* (hV4 interpolation collapse at S-cone intermediates). CVD is structured warping of the cortical color manifold, not mere signal loss. Close on significance: this is *what kind of thing* the deficit is.

**¶3 — C2a: neural identifies what behavior cannot.** Fitting behavioral (γ) and neural (RDM) atoms independently shows the neural component contributes information the behavioral loss cannot access (sub-09: RDM recovers a protan direction behavior-only cannot, β_c≈+4° behavioral-only fails; sub-08: RDM sharpens/stabilizes the argmin). Close on significance: neural structural information is *load-bearing* for the correction, not decorative.

**¶4 — C2b: individualization.** The method yields a per-person, neurally-grounded filter; the two fitted filters differ by subtype in magnitude and direction. **Scope: between-subtype (one deutan, one protan); within-subtype individuality is untested at N=2 and is the replication question.** Close on significance: architecture is individualizable by construction — the advance over population-average.

**¶5 — caveat bounding ¶4 (brief).** What is robust is the 2-component **mechanism class** and the **direction (sign)** of the dominant confusion-axis term; per-axis magnitudes are not identifiable (0/6 checks; β_s below uncertainty; β_c=42° partial recovery only). Keep short — it bounds ¶4, does not re-defend.

**¶6 — C3: performance (Phase 3, forward-looking).** Rationale = the retinal model is **structurally insufficient** (boundary saturation, over-compensation g>2 inconsistent with confirmed CVD, non-invertibility) → it *cannot represent* the measured distortion, so it cannot serve as the basis for an exact stimulus-space correction (independent of efficacy). Phase 3 (preregistered 2AFC) will test whether the personalized filter reduces JND at each participant's most vulnerable hues vs **OS-builtin (Windows/macOS) color filters** and a no-filter baseline. **If confirmed**, personalized neural-grounded correction is a deployable alternative to population-average approaches; **if not**, the cortical-distortion account requires revision. (Two-directional, falsifiable; do NOT assume success.)

**¶7 — Limitations.** Four considerations bound the proof-of-concept scope: (1) N=2 CVD; (2) single isoluminant, iso-chroma locus (L*=75, chroma=40) — no luminance/saturation generalization; (3) HC pool n=6 at hV4 (descriptive anchor, not a test); (4) no parameter-level bootstrap CIs on (β_s, β_c).

**¶8 — Synthesis + broader impact.** Restate the program: encode each individual's cortical color geometry and invert it, vs a fixed population-average spectral shift. Close on forward-looking significance (paradigm: from population-average retinal correction to individual neural-geometry-grounded correction).

**REMOVED from v2:** the upstream-input-rejection paragraph (LORO-preserved → not inherited deficit); the detection–correction "divergence" falsifier paragraph and its §S16 cosine statistic.

---

## 3. Evidence pack (CANONICAL — source of truth; do not deviate)

### LORO precondition (Results §loro) — established, NOT re-argued in Discussion
- Both CVD exceed 0.125 chance at every ROI. Cross-subject HC-HC vs HC-CVD MWU p=0.668. Within-ROI hV4 Crawford–Howell p=0.142.

### LOCO interpolation (Results §loco)
- HC hV4 adjacent accuracy 0.47±0.05 SEM, p=0.044 (8!=40,320 exact perms). V1–V3 not above chance.
- sub-08 adj acc 0.25 (t=−1.58, p=0.082 n.s., d_cc=−1.71); sub-09 adj acc 0.13 (t=−2.48, p=0.024, d_cc=−2.68).
- Both near-zero at blue/purple/magenta (S-cone intermediates). Per-hue: blue both d=2.20 p=0.042; purple d=1.02 p=0.19; magenta d=1.89 p=0.064. Vulnerability profile **v ∈ [0,1]^8**.

### Geometry / RDM (Results §geometry)
- ΔRDM = RDM_CVD − mean(RDM_HC). sub-08 elevated disparity **at V2 (p=0.040)** only; sub-09 **at V1 (p=0.007)** only.
- Idiosyncratic ROI specificity (V2 deutan, V1 protan) is inconsistent with a shared group-level gain mechanism.

### Retinal (R+C / Machado) insufficiency (Results §rc_insufficient) — basis for C3 rationale
- sub-08: 100% of resamples saturate grid boundary, g=3.0. sub-09: 41% saturation, g=2.95.
- g>2 ⇒ cortex reverses retinal shift past undistorted hue. Ishihara: sub-08 5/14, sub-09 7/14 (confirmed CVD). g>2 is internally inconsistent with confirmed CVD = **model failure, not a valid estimate**.
- DOF deficit: δθ=(2−g)·δθ_Machado displaces only along the fixed confusion axis.
- Machado non-invertibility (sub-09): collapses green 135°, cyan 180°, blue 225° onto ~127° → no exact pre-image.

### 2-component fits (Results §twocomp) — CANONICAL β
- **sub-08 (deutan, θ_conf=150°)**: loss γ_OY + L_RDM^(V2) → **(β_s, β_c) = (6°, −42°)**. L̄_test=−2.36 (IQR 2.15) vs alt −1.14. HC-resample IQR (8°,2°). Strict 7-fold LOO β_c ∈ [−46°,−38°] (all negative). Pre-image mean |δ| = **26.3°** (max 38°).
- **sub-09 (protan, θ_conf=16°)**: loss γ_all + L_RDM^(V1) → **(β_s, β_c) = (2°, +24°)**. L̄_test=−1.54 (IQR 1.42). HC-resample IQR (0°,0°); 87.7% same 45° bin; LOO IQR (0,0). Metric-dependent (Appendix crossatom). Pre-image mean |δ| = **16.2°** (max 25°).
- Dominant component = β_c for both. RDM held-out LOO: sub-08 0.594, sub-09 0.528; beat (0,0)=1.0 on all 7 folds; fits in top 5–8% of grid. Noise ceiling 0.240/0.274; recover 52%/67% of achievable range.
- RDM atom ROI matches disparity ROI (V2 sub-08, V1 sub-09); the two criteria are independent (loss by test-loss, disparity by Crawford–Howell).

### Neural role (Results §neural_role) — load-bearing for C2a
- sub-09 behavioral-only β_c≈+4°, did NOT beat baseline (ΔL=+0.01, 4/7 folds); RDM captures a signal the behavioral loss cannot detect.
- sub-08 behavioral-only AND combined share argmin (6°,−42°); adding RDM reduced boundary saturation 23%→9.3% (sharpened without shifting). Neural-only sub-08 non-degenerate β_c=−26° (corroborates deutan direction).
- Neural term reduces parameter IQR both: sub-08 (18,6)→(8,2) PCA; sub-09 (6,4)→(0,0) PCA.

### Identifiability (Results §identifiability) — basis for ¶5
- 0/6 checks significant after FDR (BH α=0.05). Voxel-level f_10° < 0.30 both. Non-dominant |β_s|≤6° below ~20–25° uncertainty (not recoverable). Dominant β_c=42° (sub-08) exceeds uncertainty → partial recovery (bias 4.7°).
- Sign of β_c stable across held-out: sub-08 <0 all LOO/resamples; sub-09 >0 **under PCA-basis only** (SRM-basis sign not verified).

### Selection (Methods §selection)
- 3 gates: directional precondition (signed d≥+0.5) → boundary saturation (<50%) → held-out test-loss (primary), test-loss IQR (secondary). **LOCO loss did NOT enter the winning combination for either participant.** Specificity is descriptive only, not a selection criterion.

---

## 4. Anti-overstatement constraints (CRITICAL — apply to every paragraph)

From project policy (`future_phase2_filter_optimization/CLAUDE.md` §0, §2.6; memory `project_v6_pca_closure`, `feedback_physiological_grounding`):
- **Descriptive only.** No specificity claim (HC FPR 100%; no p-value/FPR claim). State as "mechanism class (sign quadrant) descriptive."
- **No absolute (β_s, β_c) or g physiological interpretation.** R+C is an exploratory descriptive companion (near-degenerate loss; g unstable); **no etiological claim**.
- **"Individual" = between-subtype at N=2**, never within-subtype.
- **LOCO interpolation is robust only at hV4**; V1/V2 interpolation is below null. The geometric-distortion claim rests on RDM disparity (V1/V2) + hV4 interpolation failure — state it that way.
- **Mechanism class + sign robust; per-axis magnitude not.**
- **No "target" for LOCO/RDM. No "diverge" for retinal-vs-cortical.** Retinal argument = **insufficiency** (boundary saturation / over-compensation / non-invertibility), framed as model FAILURE.
- **§S16 divergence / cosine −0.54 REMOVED** from Discussion AND supplementary.
- **Phase 3 efficacy is forward-looking and two-directional** (state both "if confirmed" and "if not"); never assume success.

---

## 5. Genre templates (from NotebookLM analysis of comparable papers)

> Caveat: NotebookLM stores some PDFs as fragmentary excerpts; templates below are partly inferred heuristics, not verified full-paragraph maps.

**(A) Empirical fMRI color-neuroscience** (Bannert 2018, Brouwer & Heeger 2009, Tregillus 2021):
- First ¶ = executive summary (restate goal + neural finding + behavioral link, then "results suggest…").
- Middle = methodological-uniqueness defense ("simpler model, reconstructs *novel* stimuli") → "Nonetheless" limitation pivot → cross-species/literature grounding.
- Later = anatomical locus interpretation → mechanism (adaptation/gain).
- Last = broader significance → clinical implication → limitation (compensation incomplete) → future direction.

**(B) Model→correction bridge** (WHIS/Irino 2023 = structural twin, Akalin 2025, Boehm 2014) — 4-step justification:
1. **Baseline failure** — pure retinal/physical model fails to explain the phenomenon (Boehm: threshold 38% ≠ perception 86%).
2. **Parameterized bridge** — the specific transform (gain / inverse function).
3. **Validity defense** — objective metric OR rule out alternatives as implausible.
4. **"Restored symmetry" closure** — translate the math fix into a human benefit.

Our paper sits at (A)+(B); WHIS is the closest structural analog ("characterize structured deformation → parameterize → invert → correct").

NotebookLM CVD-framing support (use for ¶1–¶2):
- CVD = multidimensional geometric distortion/warping of cortical color space, not 1-D loss (MDS compression: Boehm; angular hue-scaling warp: Emery; representational geometry: Kriegeskorte 2008/2019 — RDM = what the brain "knows" about stimulus relationships).
- "Scattered but parallel": CVD relational structure preserved but scattered 1.4–1.6× more (our SRM/RDM result).
- Brouwer & Heeger: novel-color interpolation tests a continuous perceptual manifold; V4 supports it, V1–V3 do not; CVD interpolation failure = "broken color wheel."
- Population retinal model can't capture individual cortical compensation: Boehm (threshold≠suprathreshold), Emery (R-G amplitude uncorrelated with threshold loss), Bosten 2019 (large individual differences not associated with sensitivity loss).

---

## 6. Citation keys (valid in `docs/PAPER/bibliography.bib`)

brouwer2009, bannert2018, emery2021, tregillus2021, boehm2014, bosten2019, kriegeskorte2008, kriegeskorte2019, crawford1998, machado2009, isherwood2020, ishihara1917, akalin2025, feilong2018, conway2018, shapley2011, kuriki2015, parkes2009, brettel1997, hayashi2024, robinson2023, stockman2000, neitz2011, deeb2005, benjamini1995, nichols2002.

Use only these or keys already present in `discussion_v2.tex`/`results_v4.tex`. Do not invent keys; flag any concept lacking a key.

---

## 7. Output conventions for drafting

- LaTeX prose matching `discussion_v2.tex` (\section, \citeA{} for narrative cites, \cite{} for parenthetical, \ref{}, \emph{}, °/$^\circ$).
- One idea per paragraph; topic sentence first (C-C-C). Every paragraph closes on significance ("how it matters / the difference made"), per `~/.claude/writing/academic_writing_rules.md` and the Mensh & Kording scientific-writing guide.
- Active voice; no hedging clusters; no "very/clearly/importantly" filler.
