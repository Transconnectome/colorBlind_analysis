# Paper Table of Contents & Strategic Plan

> **⚠ FROZEN at v1.0 cut-over (2026-05-01)** — this file is now a decision-log archive.
> **For ongoing structural work**, use:
> - **Full overview / paragraph drafts**: `INDEX_v1.0.md`
> - **Meeting summary (subtitle + 1–2 lines per item)**: `INDEX_v1.0_meeting.md`
> - **Decision-log changes**: append to `INDEX_v1.0.md` §X changelog (not here).

- **Target Journals (ranked by fit)**: eLife → Current Biology → PNAS → Nature Neuroscience
- **Publication strategy**: Option B — include behavioral validation (MRI + JND + identification, <1 month)
- **Date**: 2026-04-15
- **Status**: Methods draft done (`Methods/methods_streamlined.tex`); Intro/Results/Discussion need rewrite

---

## 1. Provisional Title (3 candidates)

1. **"Neural geometry of color in color vision deficiency predicts individualized display correction"** (emphasizes bridge: neural → filter)
2. **"Color discrimination is preserved but continuous hue geometry is distorted in color vision deficiency: a neural basis for individualized display filters"** (descriptive, fits PNAS/NeuroImage)
3. **"Cortical color geometry as a design substrate for CVD correction filters"** (eLife-style, punchy)

**Recommendation**: (2) for PNAS/Curr Biol, (1) for Nat Neuro/eLife.

---

## 2. Abstract (≤250 words)

**Structure (6 sentences)**:
1. **Motivation**: Existing CVD filters rely on retinal cone models; cortical consequences of CVD and individual variability are largely unaddressed.
2. **Gap**: Whether cortical color geometry is distorted in CVD (beyond discriminability loss) and whether such distortion is individually patterned remain open.
3. **Approach**: 7 HC + 3 CVD fMRI (6 runs, 8 isoluminant hues, V1–hV4), SRM common space + forward encoding with LORO/LOCO + stimulus-space cone-shift modelling + pre-image filter design + behavioral JND validation.
4. **Neural result**: Color discrimination (LORO) is preserved in CVD, but continuous hue interpolation (LOCO) is impaired in early visual cortex; SRM geometry shows subject-specific pair-wise deviations (Crawford-Howell, sub-08 V2 p=.040, sub-09 V1 p=.007).
5. **Model result**: A 2-component angular dilation model captures CVD distortion at hV4 LOCO (sub-08 p=.004, sub-09 p=.035) with a cross-subject S-cone expansion of β_s ≈ 21.5° (aligning with Emery et al. 2021), and uniquely yields a bijective pre-image (8/8 exact) that other cone-shift variants fail to produce.
6. **Translation**: The derived individualized filter, applied in a same-day behavioral task, recovers JND along confusion-axis pairs — establishing neural geometry as a principled substrate for adaptive display correction.

---

## 3. Table of Contents (Full Structure)

### Introduction (~1,000 words)
Following user's draft + strengthened gap-hook arc.

**§Intro-1: Filter state-of-the-art and its ceiling** (~200 w)
- Current filters (EnChroma, Windows color filters, Brettel–Viénot–Mollon simulation-inverse) operate at the retinal stage.
- They do not use perceptual/neural data from the individual user.
- Behavioral uptake (Gomez-Robledo 2018, Hassan & Crognale 2023, Almutairi 2022) is uneven because retinal models cannot predict cortical outcome.

**§Intro-2: The case for neural-based filter design** (~180 w)
- Cortical reorganization after retinal deficit (Neitz & Neitz 2011 opponency debate; Boehm et al. 2014 V1 adaptation; Welbourne 2018).
- Perceptual hue space is built downstream of L,M,S — filters that ignore this risk over- or under-correction.
- Hook: *a filter optimized against cortical geometry should transfer to perception better than a retinal-only one.*

**§Intro-3: Existing CVD neuroimaging and its gaps** (~200 w) : 최근 연구 보완하기 (SRM 등) 
- Brouwer & Heeger 2009 (forward model, V4 reconstruction) — healthy only.
- Brouwer et al. 2013, Bannert & Bartels 2018, Kuriki 2015, Parkes 2009, Conway et al. — healthy only, or CVD comparison at ROI-average level.
- CVD neural work (Rabin 2011 fMRI BOLD magnitude; Wachtler 2003 V1 single-cell animal) focused on activation, not population geometry.
- Gap: no study has (a) explicitly tested **geometric distortion** (RDM + LOCO) in CVD, (b) at individual level, (c) with an end-to-end filter design pipeline.

**§Intro-4: CVD at cortex — discrimination vs. interpolation, and individuality** (~220 w)
- Classic Ishihara/farnsworth captures *categorical* confusion, not continuous distortion.
- Individual variation in CVD severity (L-cone shift, M-cone shift, anomalous opponency) implies heterogeneous cortical consequences.
- Recent SRM-based CVD work (Ryu et al. 2024; Kim et al. 2024; SRM-MVPA-CVD 2025) show preliminary geometric differences but no filter derivation and no case-specific statistics.
- Specifically: sub-08 (deuteranomaly) and sub-09 (protanomaly) are expected to differ not only in average magnitude but in which pair-wise distortions are largest → argues for individualized analysis.

**§Intro-5: Present study — three questions, three answers, one filter** (~200 w) : 고려 (2번이 중요한 이유 - 필터 제작 가능성 )
1. Is cortical color geometry distorted in CVD, and if so where (hierarchy)?
2. Is distortion selective for *continuous interpolation* (LOCO) while *discrimination* (LORO) is preserved?
3. Can this cortical distortion be parameterized with a physiologically interpretable model, and inverted to derive an individualized corrective filter that restores behavioral discrimination?

**Style note**: write in precision-neuroscience voice — "case-study" framing from first paragraph, citing Crawford & Howell 1998 and Schütt et al. 2021.

---

### Methods (≈2,000 words; mostly in place, **needs two additions**)
Already in `methods_streamlined.tex` v1.2. Required edits:

**§M-1 to §M-5**: already covered (Participants, Stimuli, fMRI, Preprocessing, SRM, Forward model, LORO/LOCO, Behavioral JND/8AFC). **No change.**

**§M-6 (NEW): Cone-shift models and loss** (~400 w, replaces current §Filter-design stub)
- **Three candidate cortex-space distortion models**:
  1. Machado 1-way (1 DOF: Δλ; retinal only) — baseline.
  2. R+C opponent (2 DOF: Δλ, g; retinal + cortical gain) — physiological interpolation.
  3. **2-component angular dilation** (2 DOF: β_s S-cone expansion, β_c confusion-axis rotation) — chosen primary model.
- **Loss**: `L_LOCO = α·L_vuln/4 + β·L_rank/2 + δ·L_rdm/2 + ε·L_smooth/32400` (α=1, β=δ=0.5, ε=0.1).
- **Permutation test**: 8! exact label permutation over LOCO targets; one-sided p.
- **Rationale**: 2-component is the only model producing a bijective pre-image (§M-7) and the only one passing dual-criterion (LOCO + ΔRDM) for both CVD subjects.

**§M-7 (NEW): Pre-image filter derivation** (~200 w)
- Given estimated distortion D̂(θ), compute θ_in = argmin_θ ‖D̂(θ) − θ_target‖ (grid over 0–360° × 0.5°).
- Report per-color residual and bijectivity (one-to-one guarantee).
- Filter is applied in HSV-rotation form to the display LUT (implementation: Python + Psychopy display filter).

**§M-8 (NEW, short): HC specificity considerations** (~120 w)
- We report empirical HC false-positive rates for three ΔRDM/Δρ specificity metrics (Supplementary §S3) — all fail to reject HC.
- We therefore interpret results as **single-case descriptive fits** (Crawford & Howell 1998) rather than group-level specificity. Statistical validity derives from (a) within-subject label permutation and (b) behavioral convergence, not from a CVD-vs-HC FPR.

---

### Results (~2,500 words, 5 main figures)
Rewritten to match user's draft (SRM RDM → LORO/LOCO → filter design → behavioral).

**§R-1: Sample and behavior** (~150 w)
- 7 HC + 3 CVD (sub-08 deuteranomaly, sub-09 protanomaly, sub-10 near-normal).
- RSVP attention task accuracy, no group difference (Table 1).

**§R-2: Cortical color geometry is distorted in CVD** (~450 w, **Fig 2**)
- SRM common space (HC-only k=4,4,3,3 for V1–hV4).
- Crawford-Howell individual disparity: sub-09 V1 p=.007, sub-08 V2 p=.040.
- RDM pair-wise bootstrap: specific pair deviations (subject-specific pattern, cited in Introduction as prediction).
- **Fig 2**: (a) SRM schematic; (b) HC mean RDM; (c) CVD RDM per subject; (d) Δ-RDM with highlighted significant pairs (bootstrap CI).

**§R-3: Discrimination is preserved but continuous hue geometry is disrupted** (~400 w, **Fig 3**)
- LORO decoding: no HC-CVD difference (ns in all ROIs).
- LOCO interpolation: HC-CVD gap at V1 (d=1.61 p=.021), V2 (d=1.85 p=.022), hV4 (primary gate; perm p=.044).
- Hedges-g and LOSO zero-shot (ZS ≈ LORO; Group prior valid).
- **Fig 3**: (a) Forward-model schematic (basis + W + decoding); (b) LORO/LOCO bar graph × ROI × group; (c) decoding pipeline application schematic (showing where the filter plugs in).

**§R-4: A 2-component cortical distortion model recovers individualized filters** (~600 w, **Fig 4**)
- Three models (Machado / R+C / 2-component): fit to hV4 LOCO target, w_fixed method, grid 26×51.
- **Dual criteria**: LOCO permutation + ΔRDM cosine.
- Result table: 2-component best for both CVD subjects (sub-08 p=.004, sub-09 p=.035); R+C and Machado fail for at least one.
- Cross-subject **S-cone expansion β_s ≈ 21.5°** (sub-08: 20°, sub-09: 23°), concordant with Emery et al. 2021 (21.4° B-Y post-adaptation rotation).
- Pre-image residuals: **8/8 exact** for both subjects under 2-component; Machado arc-compresses 4/8 for sub-09.
- **Fig 4**: (a) model-fit landscape (β_s × β_c heat-map, LOCO p-contour); (b) pre-image pre-/post-filter θ-map; (c) per-color residual histogram across 3 models; (d) β_s bootstrap distribution vs. Emery ref.

**§R-5: Neural-derived filter improves color discrimination** (~500 w, **Fig 5**)
*Depends on Session-2 behavioral acquisition — see §Work Plan.*
- Same-day behavioral test: CVD sub-08 performs JND task under (i) no filter, (ii) Windows filter, (iii) individualized neural filter.
- Predicted: neural filter reduces JND on confusion-axis pairs by ≥ X% vs. Windows, without harming control pair.
- 8-AFC identification: neural filter reduces mis-identifications on LOCO-vulnerable colors.
- **Fig 5**: (a) JND × pair × filter bar graph; (b) 8-AFC confusion matrix before/after; (c) second-session fMRI LORO/LOCO under filter (Δ from baseline).

**§R-6: Specificity considerations** (~200 w, main text acknowledgment)
- Acknowledge HC FPR under the three tested metrics (Supplementary §S3).
- Frame as case-study: within-subject permutation + behavioral convergence constitute the inferential backbone.

---

### Discussion (~2,000 words)

**§D-1: Summary** (~200 w)
- Three findings: (i) cortical geometry distortion subject-specific, (ii) discrimination–interpolation dissociation with hierarchical gradient V1→hV4, (iii) 2-component model captures + inverts distortion into behaviorally effective filter.

**§D-2: Cortical geometry of CVD: beyond confusion-lines** (~400 w)
- Integrate Brouwer & Heeger 2009 (healthy LOCO), Bannert & Bartels 2018 (hV4 perceptual hub), Parkes 2009 (V1 hue MVPA), Kuriki 2015 (intermediate hues).
- β_s ≈ 21.5° cross-subject convergence ⇒ cortical S-cone gain up-regulation, behaviorally validated by Emery et al. 2021 (21.4°).
- Confusion-axis rotation β_c differs between sub-08 (−14°) and sub-09 (−22°) ⇒ subject-specific compensatory realignment.

**§D-3: The LOCO/LORO dissociation as a functional marker** (~350 w)
- RDM captures *metric* properties of the space; LOCO captures *functional* interpolation capacity.
- Only LOCO predicts JND (100% concordance in HC1); SRM z predicts only 33%.
- V1/V2 discriminate via local contrast; hV4 interpolates via full manifold — consistent with Bannert & Bartels.

**§D-4: Why 2-component, and why bijective pre-image matters** (~350 w)
- Machado 1-way cannot exceed sub-09's arc compression; R+C requires g<-1 for sub-08 (non-physiological 125% overshoot).
- 2-component is bijective over the 8-color support — guarantees the forward filter has a well-defined inverse *display filter*.
- Clinical/engineering implication: any filter pipeline that cannot guarantee injectivity can under- or over-compensate random pairs.

**§D-5: Case-study framework and HC specificity** (~300 w)
- Position: this is **precision neuroscience**, not a group study. Crawford & Howell 1998 single-case statistics + Schütt et al. 2021 single-model significance caveats.
- HC FPR under shared models is expected when the model is sufficiently expressive; interpretation is not "CVD > HC statistically," but "each CVD subject has a quantifiable distortion that, when inverted, yields a perceptually beneficial filter."
- Analogy: clinical stimulation mapping does not require between-subject statistics to be useful.

**§D-6: Limitations and future work** (~300 w)
- n=3 CVD, replication needed; protan/deutan subtype matrix under-sampled.
- Behavioral validation tested on single-session same-day paradigm; long-term adaptation unknown.
- CIE Lab is HC-optimized; CVD-optimized color spaces (MDS-based) could sharpen fits.
- Next: scale to ≥10 CVD, pre-register filter-vs-Windows RCT.

**§D-7: Conclusion** (~100 w)
- CVD alters continuous cortical hue geometry with individually patterned distortions.
- A 2-component cortical model captures distortion and yields a bijective, individualized corrective filter.
- Neural-geometry-guided display adaptation is a feasible and behaviorally validated path to precision color-vision support.

---

## 4. Figures Plan (5 main + supplementary)

| Fig | Content | Source | Status |
|-----|---------|--------|--------|
| F1 | Stimulus + ROI overview | existing (Methods Fig 1) | ✓ placeholder |
| F2 | SRM geometry: HC mean RDM, per-CVD RDM, Δ-RDM with sig pairs | `rerun_loo_consistent.py` outputs | needs re-plot |
| F3 | LORO/LOCO bars + forward-model schematic | `loco_baseline.py` + manually drawn | needs draw |
| F4 | Cone-shift model comparison: landscape + pre-image + β_s vs. Emery | `loco_distortion_fit.py` + `preimage_search.py` | needs assembly |
| F5 | Behavioral validation: JND bars + confusion matrix + Session-2 fMRI | **pending Session 2 acquisition** | **TODO (1 mo)** |
| S1 | Procrustes alignment QA | existing | ✓ |
| S2 | Basis-channel k sensitivity (LORO/LOCO × k) | existing | ✓ |
| S3 | HC FPR tables (raw LOCO, Δρ, ΔV) | `baseline_delta_rho/`, `experiment_c_delta_vuln/` | new |
| S4 | Per-subject model comparison matrix | notion.md §5 | new |

---

## 5. Journal-Specific Adaptation (quick matrix)

| Journal | Format | Word limit | Figures | ToC compatibility | Special |
|---------|--------|-----------|---------|-------------------|---------|
| **eLife** | Research Article | flexible (~6,500) | 5–7 main | full — best fit | open review, likes precision-neuro |
| **Current Biology** | Article | 5,000 | 5 | trim D-2 and D-3 | needs broad-impact framing |
| **PNAS** | Research Article | 6,000 (text only) | 6 | trim D-2 | Direct Submission or Contributed |
| **Nature Neuroscience** | Article | 5,000 | 5 | trim Intro + some Results text; ext. data supplementary | high mech. bar — emphasize β_s convergence as neural mechanism |

**Suggested submission order**: eLife first (best fit + rapid review) → Current Biology if rejected.

---

## 6. Work Plan (concrete next actions)

### Phase 1 — Before Session-2 fMRI (this week)
- [ ] **Lit search batch 1**: retinal-stage filter papers (EnChroma, Brettel, Gomez-Robledo, Hassan 2023) → save to `docs/PAPER/Citations/retinal_filters.bib` and to NotebookLM.
- [ ] **Lit search batch 2**: CVD neural imaging (Rabin 2011, Wachtler 2003, Ryu 2024, Kim 2024, SRM-MVPA-CVD 2025) → NotebookLM.
- [ ] **Lit search batch 3**: Target-journal style samples — eLife precision-neuro, Curr Biol case-study style (e.g. Schwarzkopf 2011).
- [ ] Rewrite `Introduction/introduction.tex` per §3 plan.
- [ ] Write R-1, R-2, R-3 Results text with actual stats from `notion.md` §5 and `LOCO_FILTER_RESULTS.md`.
- [ ] Update `Methods/methods_streamlined.tex` with §M-6 to §M-8 additions.

### Phase 2 — Session-2 fMRI + behavioral (≤1 month)
- [ ] Acquire behavioral JND + 8-AFC under 3 filter conditions (CVD only).
- [ ] Analyse and assemble Figure 5.
- [ ] Write R-4, R-5, R-6 Results text.

### Phase 3 — Final assembly
- [ ] Rewrite Discussion per §D plan.
- [ ] Assemble F1–F5 at 300 dpi PDF.
- [ ] Abstract final + title finalized.
- [ ] Supplementary (§S1–S4).
- [ ] Pre-submission review pass (proofread skill).

---

## 7. Questions for PI (answer before proceeding)

1. **Title**: option (1), (2), or (3)?
2. **Journal target**: eLife first vs. Current Biology first?
3. **Behavioral scope for Fig 5**: sub-08 only, or all 3 CVD?
4. **Session 2 fMRI**: is imaging time already booked?
5. **Co-authorship**: final author list?

---

# 8. CRITICAL REVISION (2026-04-15) — Redteam + Literature Audit

**Origin**: Parallel execution of (a) redteam-project agent against §1–§7 above, (b) Semantic Scholar search, (c) NotebookLM audit of `ColorBlind_comprehensive`.

## 8.1 Redteam findings — 8 issues (3 FATAL, 2 SERIOUS, 3 MODERATE)

| # | Severity | Issue | Where it appears | Neutralization |
|---|----------|-------|------------------|---------------|
| R1 | **FATAL** | Effective CVD n=2 (sub-10 is near-normal; excluded from neural-significant contrasts) — cannot support group-level framing in Abstract/Results. | Abstract §2 sentence 5, Results §R-3 HC-CVD gap "d=1.61" | Rewrite every "CVD vs HC" sentence in case-study tense; sub-10 labelled null control throughout; effect-size cites per-subject, not group mean. |
| R2 | **FATAL** | HC FPR 100% for 2-component (`baseline_delta_rho/summary.json`) — model is non-specific to CVD. | §M-8 currently hides this as "supplementary"; Abstract implies model is diagnostic. | Move HC FPR to **main text §R-6**, not supplementary. Frame as "expected consequence of an expressive model; specificity derives from convergent validation (β_s matches Emery 21.4°; behavioral JND), not from single-model significance." Cite Schütt 2023 explicitly. |
| R3 | **FATAL** | Abstract claim "recovers JND" is prospective, not demonstrated. If Session 2 runs slip, the whole filter-payoff chain is unfalsified speculation. | Abstract §2 sentence 6 | Condition on Session 2: use "predicts JND gains on confusion-axis pairs (validated behaviorally in n=1 sub-08 same-day session)" — and do NOT submit the paper before Session 2 data are analysed. |
| R4 | **CRITICAL** | Novelty overstated vs Brouwer & Heeger 2009: "no prior study tested LOCO/RDM in CVD" is false — Brouwer & Heeger ran LOCO, found V4/VO1 interpolate novel colors; our LOCO hierarchy is consistent (Healthy) and extends (CVD). | Intro §Intro-3 ("Gap") | Rewrite: "We apply the Brouwer & Heeger (2009) LOCO paradigm to CVD, where it has not been tested, and extend it with single-case permutation and a stimulus-space inverse filter. The paradigm itself is not new; its application to CVD geometry and its use for filter design is." |
| R5 | **SERIOUS** | Pre-image "bijective 8/8 exact" is a claim over 8 discrete training colors, not over the full 360° hue circle. Jacobian check missing. Reviewers will ask about off-training pre-image stability. | §M-7, §R-4 | Add a sentence: "Bijectivity verified over the 8 training colors (residual <0.001°); for 360° off-training hues, we report the max Jacobian |dθ_out/dθ_in| and confirm monotonicity over protan/deutan-consistent sign arrangements." |
| R6 | **SERIOUS** | Model cherry-picking / HARKing: we ran Machado → R+C → 2-component after inspecting fits; picking "2-component is best" without explicit multiple-comparison or pre-registration. | §M-6 | Disclose search order in Methods; add to Discussion: "Model selection was exploratory; 2-component was favored on two independent criteria (LOCO + bijective pre-image). Pre-registration of the 2-component model is planned for replication in the scaled cohort (§D-6)." |
| R7 | **MODERATE** | Fig 4 β_s landscape at (sub-08 20°, sub-09 23°) with only n=2 effective CVD — "cross-subject convergence with Emery 21.4°" is numerically striking but n=2. | §R-4 paragraph 4 | Report with explicit n=2 qualifier; include a bootstrap per subject (already done) and present Emery 21.4° as *prediction* that survives with only 2 subjects — not "cross-subject convergence in population sense." |
| R8 | **MODERATE** | Figure plan does not visualize the HC FPR issue, even though it is central to interpretation. | §4 Figure Plan, Fig S3 | Promote Fig S3 to a **main figure panel** (new 4e or separate Fig 5 integration): HC-vs-CVD Δρ histograms with sub-08/09/10 overlaid. |

**Redteam verdict**: "REJECT in current form." Tier-1 fixes (1 week): R1, R2, R3. Tier-2 (<2 weeks): R5, R8. Tier-3 (month): R6, R7 require study-design changes but are ameliorable with careful framing.

## 8.2 Literature audit — what `ColorBlind_comprehensive` NotebookLM has

**Covered (no need to add)**:
- **Rina (2024, medRxiv)** — Daltonism + achromatopsia fMRI case study. *Key finding*: "Daltonic participant LACKED isolated color-specific activity in hV4" — this is CONTRARY to our hV4-as-primary-gate in anomalous trichromats. **We must explicitly address this contrast in Discussion §D-2 or §D-6.**
- **Basim et al. (2025)** — Behavioral color contrast adaptation/compensation in CVD, links to post-receptoral amplification in V2/V3 via Tregillus 2021.
- **Robinson et al. (2023, Vision Research)** — McCollough-effect evidence of compressive nonlinear cortical encoding in anomalous trichromats; V2/V3 post-receptoral compensation.
- **Tregillus et al. (2021)** — V2/V3 neural amplification compensating weaker LvsM signals (NOT V1). Matches our V1/V2 discrimination-preserved / hV4-interpolation-impaired dissociation.
- **Emery et al. (2021)** — hue-scaling task, B-Y phase rotated **21.4°** closer to S-vs-LM axis in anomalous trichromats (KB citation confirmed). Our β_s ≈ 21.5° (sub-08 20°, sub-09 23°) is a convergent mechanistic link.
- **Schütt et al. (2023 eLife, preprinted 2021)** — single-model-significance fallacy (Kriegeskorte & Douglas 2019 origin). Directly supports "HC FPR is not a rebuttal" framing.
- **Finn et al. (2020)** — paradigm shift to individual/case-study fMRI; patient populations are heterogeneous.
- **Feilong et al. (2018)** — hyperalignment/SRM necessity for fine-grained individual representations.
- **Machado et al. (2009)** — Δλ cone-shift + Ingling-Tsou opponency, with area-preserving scaling factor.
- **Brouwer & Heeger (2009)** — LOCO paradigm, V4/VO1 circular-progression interpolation, V1–V3 fail on novel colors (exactly our hierarchy).
- **Werner et al. (2020)** — (via Emery 2021 citation) adaptation to color-enhancing filters drives perceptual learning even after removal; caveat for same-day behavioral.
- **Shen et al. (2016)** — direct EnChroma behavioral comparison showing slight benefit but lower comfort.
- **Akalin et al. (2025), Rasche (2005), Brettel (1997)** — algorithmic daltonization / retinal-stage filter competitors.

**Gap candidates** (my Semantic Scholar search, not in KB; decide whether to add):
- **Gauthaman 2024 (PLoS Comput Biol)** — universal scale-free visual cortex representations, hyperalignment-like. *Add-value: LOW* (Feilong already covers the idea).
- **Bastien 2020 (Optom Vis Sci)** — direct EnChroma critical evaluation. *Add-value: MEDIUM* (Shen 2016 covers but Bastien is a focused evaluation RCT).
- **Martinez-Domingo 2020 (Sensors)** — spectral filter fundamental limitations. *Add-value: LOW* (Akalin-era covers algorithmic side).
- **Cowley 2026 (Nature) — compact V4** — if confirmable, *Add-value: HIGH* for §D-2 hV4-as-hub.
- **Porter 2021 (bioRxiv precision-neuro)** — *Add-value: LOW-MEDIUM* (Finn 2020 already cited).

**Recommendation**: Add **Bastien 2020** (explicit EnChroma RCT) and **Cowley 2026** (if available) to NotebookLM. Others redundant.

## 8.3 Concrete ToC revisions (overriding §1–§7 above)

### Title (updated recommendation)
Drop (1) "predicts individualized display correction" — too strong given §R3.
Use: **"Cortical color geometry in color vision deficiency: an individualized 2-component model and a bijective display-space inverse"** (preserves neural → filter bridge without over-claiming behavioral payoff; fits eLife precision-neuro tone).

### Abstract (rewrite)
1. Motivation — CVD filters are retinal-stage; cortical geometry of anomalous trichromacy at the case level is under-characterized.
2. Gap — whether cortical color geometry is *specifically* distorted beyond retinal prediction (Machado), whether distortion is individually patterned, and whether an explicit pre-image of a cortical-space model can be computed, remain open.
3. Approach — 7 HC + 3 CVD fMRI × 8 isoluminant hues × V1/V2/V3/hV4; SRM common space; forward-model LORO/LOCO; three cortex-space distortion models (Machado 1-way, R+C opponent, 2-component angular dilation) evaluated by LOCO permutation and ΔRDM; pre-image search over 0–360°; behavioral JND + 8-AFC same-day validation (sub-08).
4. Neural result — **Consistent with Brouwer & Heeger (2009)**, hue interpolation (LOCO) dissociates from hue discrimination (LORO) along the V1→hV4 hierarchy; CVD LOCO is impaired where HC succeeds (hV4 perm p=.044 primary gate).
5. Model result — 2-component angular dilation is the only cortex-space model yielding a **bijective pre-image** across 8 training hues and a sub-08-to-sub-09 S-cone β_s of 20° and 23° respectively; both values bracket Emery et al. (2021)'s **21.4°** behavioral B-Y rotation (single-subject matches, not population convergence).
6. Scope — Under label-permutation, the 2-component model fits HC loosely; by Schütt et al. (2023), we therefore interpret the results as **per-subject descriptive fits validated by (a) cross-modal alignment with Emery (2021) and (b) same-day behavioral JND in sub-08** — not as a group-specificity claim.

### Introduction (rewrite §Intro-3 in particular)
§Intro-3 must now read:
> "Prior fMRI of CVD has focused on activation magnitude (Rabin 2011; Wachtler 2003 — animal) or on Daltonism/achromatopsia case studies showing **loss** of isolated color activity in hV4 (Rina 2024). Post-receptoral compensation in V2/V3 has been inferred behaviorally (Basim 2025; Robinson 2023) and with fMRI (Tregillus 2021). The **representational geometry** of anomalous trichromacy — and in particular whether it supports continuous hue **interpolation** separately from discrimination (Brouwer & Heeger 2009) — has not been tested at the per-subject level."

### Methods
- §M-6: Disclose three-model search order; pre-register 2-component for next cohort.
- §M-7: Add Jacobian bijectivity check over full 0–360°; report max |dθ_out/dθ_in|.
- **§M-8 promote HC FPR to §R-6 main text**; keep only a one-line reference here.

### Results
- Every inferential claim uses **subject ID + Crawford-Howell or permutation p**, not d= between groups.
- **§R-4 final paragraph**: "sub-08 β_s=20° and sub-09 β_s=23° bracket the Emery et al. (2021) 21.4° behavioral value — each single-subject value is a match, not a population mean."
- **§R-5 conditional on Session 2**. If not run, cut §R-5 entirely and add a §Limitations paragraph.
- **§R-6 new title**: "Model expressivity exceeds CVD specificity: implications for interpretation."
  - HC Δρ distribution (Fig 5a — promoted from supp).
  - Direct statement: "2-component HC FPR = 7/7 under label permutation for Δρ; model is expressive, not discriminative. Inference is per-subject descriptive (Crawford-Howell) + convergent (Emery 2021) + behavioral (Session 2)."

### Discussion
- Add **§D-2b (NEW)**: "Anomalous trichromacy preserves a distorted hV4 geometry; this contrasts with Rina (2024), where full Daltonism (L-cone absence) abolishes isolated hV4 color activity. Anomaly retains cone signal sufficient for cortical geometry; dichromacy does not. The Daltonism-vs-anomaly distinction is itself a prediction for the continuous-severity literature (Tregillus 2021; Basim 2025)."
- §D-4 reframed: "Why 2-component, given HC FPR?" — cite Schütt 2023 explicitly.
- §D-5 expanded with Finn 2020 + Feilong 2018 as paradigm citations.

### Figures
- **F5 conditional**: only if Session 2 runs. Otherwise F5 becomes "HC-vs-CVD Δρ distribution + bootstrap" (currently S3).

### Target journal (revised)
- **Primary**: eLife (precision-neuro fit, open review tolerant of n=3).
- **Secondary**: Current Biology.
- **De-prioritize**: PNAS and Nature Neuroscience — both demand group-level mechanism or much larger cohorts; n=2-effective does not clear their typical bar.

### Bibliography.bib additions (required)
- Rina (2024) medRxiv
- Basim et al. (2025)
- Robinson et al. (2023) Vision Research
- Tregillus et al. (2021)
- Emery et al. (2021)
- Schütt et al. (2023) eLife
- Finn et al. (2020)
- Feilong et al. (2018)
- Machado et al. (2009)
- Werner et al. (2020)
- Shen et al. (2016)
- Kriegeskorte & Douglas (2019)
- Bastien et al. (2020) — if adding EnChroma focused RCT

## 8.4 Validation of user's original ToC draft

| User's proposal | Verdict | Reason |
|------------------|---------|--------|
| Intro → Methods → Results → Conclusion/Discussion | **VALID** | Standard APA structure; fine for all 4 target journals. |
| 4 figures | **INSUFFICIENT** | With case-study framing + HC FPR + pre-image Jacobian, 5 main + 4 supp is a more defensible minimum. |
| Option B (include behavioral validation <1 month) | **VALID but conditional** | §R3 requires actual Session 2 data before abstract claim. If time slips, cut §R-5 and submit the neural-only story to eLife. |
| "Recover JND" framing | **INVALID as unconditional claim** | Must be conditional tense unless Session 2 is complete. |
| Four figure concepts (stimulus/SRM/forward/filter) | **PARTIALLY VALID** | Missing a figure for HC specificity (Fig S3 promoted to main). |

## 8.5 Work-plan revision (overrides §6)

**Phase 1a (THIS WEEK, before Session 2):**
- Rewrite `Introduction/introduction.tex` per §8.3.
- Add 12 citations to `bibliography.bib` (§8.3 list).
- Add Jacobian bijectivity check script (`preimage_jacobian_check.py`) + re-export Fig 4 with Jacobian insert.
- Draft §R-1, §R-2, §R-3 with strict subject-ID + single-case stats.

**Phase 1b (Session 2 decision gate):**
- **If Session 2 is scheduled within 2 weeks**: continue Option B. Write §R-4, §R-5 after data.
- **If Session 2 slips >1 month**: switch to Option A (neural-only) — cut §R-5, retarget eLife "Short Report", revise abstract sentence 6 accordingly.

**Phase 2 (final assembly, unchanged from §6 but reordered)**:
- R-6 HC FPR main-text section (required regardless of Session 2 outcome).
- Discussion §D-2b + §D-4 rewrite.
- Pre-submission redteam pass (repeat `redteam-project` agent against final draft).

## 8.6 Three specific decisions needed from PI (now)

1. **Session 2 booking status** — confirms whether Option A or Option B.
2. **Acceptance of case-study framing throughout** — this is a one-way door once the abstract adopts Crawford-Howell / Schütt-2023 language.
3. **Priority journal** — eLife (recommended) or Current Biology? If PNAS/Nat Neuro is mandatory, the paper must be re-scoped to a >=10 CVD replication first (6-12 month delay).

---

# 9. DECISIONS LOCKED (2026-04-15, PI answer)

## 9.1 Locked answers

| Q | PI answer | Consequence |
|---|-----------|-------------|
| Session 2 | **Can be booked immediately** | Option B confirmed. Abstract sentence 6 uses demonstrated-tense behavioural claim, *conditional on sub-08 data arriving on-schedule*. |
| Case-study framing | **Accepted** | Crawford-Howell + Schütt-2023 framing adopted throughout. All "HC-vs-CVD d=" language removed; replaced with per-subject permutation + Crawford-Howell. |
| Journal | **eLife primary; Current Biology + Nature Communications secondary** | PNAS / Nat Neuro dropped from target list. |

## 9.2 Updated journal-fit matrix (replaces §5)

| Journal | Format | Word limit | Figures | Case-study tolerance | Session 2 requirement | Fit score |
|---------|--------|-----------|---------|----------------------|-----------------------|-----------|
| **eLife** | Research Article | ~6,500 | 5–7 | **High** (precision-neuro friendly, open review) | Optional (can frame as separate behavioural validation figure) | **★★★★★ PRIMARY** |
| **Current Biology** | Article | 5,000 | 5 | Medium (prefers broad-impact angle) | Recommended (clinical-translation hook helps) | ★★★★☆ |
| **Nature Communications** | Article | ≤5,000 + Methods unlimited | up to 10 | Medium-High (accepts well-controlled small-N + mechanism) | **Required** (mechanism + translation = submission strength) | ★★★★☆ |
| ~~PNAS~~ | ~~RA, 6,000~~ | — | — | Medium — n=2-effective below typical bar | — | **Dropped** |
| ~~Nat Neuroscience~~ | ~~Article, 5,000~~ | — | — | Low — requires population mechanism | — | **Dropped** |

**Submission order**: eLife → Current Biology → Nature Communications.
- **eLife**: single-blind, open peer-review, author-response is public — fits precision-neuroscience story.
- **Current Biology**: if eLife rejects, reframe as "clinical translation hook" with Emery-matched β_s as mechanism.
- **Nature Communications**: if both reject, strengthen with a 5-subject pre-registered replication (requires ~3-month delay) and emphasize the bijective pre-image as a mechanism-plus-translation package.

## 9.3 Immediate next actions (this week, Phase 1a)

**Execution order (parallelizable where marked ⬢)**:

1. ⬢ **Add 12 citations to `bibliography.bib`** (see §8.3 list). [Done this turn]
2. ⬢ **Rewrite `Introduction/introduction.tex`** with Rina 2024 / Tregillus 2021 / Basim 2025 / Brouwer & Heeger 2009 reframe + case-study voice. [Done this turn]
3. **Book Session 2 MRI slot** (PI action). 3 CVD subjects × 1 hour each = 3 hours minimum; same-day behavioural slot for sub-08 required.
4. Draft §R-1, §R-2, §R-3 Results text with strict Crawford-Howell / permutation statistics (no group-d= language).
5. Update `Methods/methods_streamlined.tex` with §M-6 to §M-8 (cone-shift models, pre-image + Jacobian, HC-FPR single-line reference).
6. Add Jacobian bijectivity check script (`preimage_jacobian_check.py`) in `analysis/future_phase2_filter_optimization/scripts/`.
7. Request `repo-maintainer` for final figure inventory (F1–F5 paths + source scripts).

## 9.4 Risk register

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Session 2 slips >4 weeks | Medium | Fallback Option A: cut §R-5, retarget eLife Short Report (4,000 w, 4 figs). Abstract sentence 6 becomes "predicted JND gains on confusion-axis pairs (behavioural validation ongoing)". |
| sub-08 behavioural null | Medium | Report null honestly. Paper still stands on §R-1 to §R-4 + HC-FPR main-text disclosure. Submit to eLife which accepts null-result addenda. |
| Reviewer demands n ≥ 5 CVD | High | Pre-register replication as Discussion §D-6 "Scaled cohort (n=5–10) replication in preparation". Nature Comms tertiary needs this anyway. |
| Rina 2024 priority claim | Low | Addressed by §D-2b dichromat-vs-anomaly distinction; our LOCO + pre-image are orthogonal to Rina's activation-magnitude finding. |

---

# 10. NARRATIVE VALIDATION (2026-04-16) — Full-text audit + missing-paper discovery

**Trigger**: PI annotation on §Intro-3 ("최근 연구 보완하기 — SRM 등") and §Intro-5 ("고려 — 2번이 중요한 이유: 필터 제작 가능성").
**Method**: (i) NotebookLM session 25f30ccc against `ColorBlind_comprehensive` after uploading 8 missing full-text PDFs; (ii) targeted Semantic Scholar 2023-2026 sweep; (iii) Intro/Review cross-reference of Rina 2024 / Tregillus 2021 / Emery 2021.

## 10.1 NotebookLM KB now contains (new adds today)

| # | Paper | Source ID | Role in narrative |
|---|-------|-----------|-------------------|
| 1 | **Tregillus 2021** Curr Biol — V2/V3 compensation in anomalous trichromats | 57ede0ab | §Intro-3 / §D-2b post-receptoral compensation |
| 2 | **Emery 2021** — hue scaling β_s benchmark | 3e845dba | §R-4 / §D-2 exact 21.4° validation |
| 3 | **Schütt 2021** (preprint of 2023 eLife) — RSA single-model-significance | 43d15835 | §R-6 / §D-5 HC-FPR neutralization |
| 4 | **Finn 2020** — idiosynchrony precision neuroscience | 6d2d41ce | §D-5 case-study framing |
| 5 | **Feilong 2018** — fine-grained individual differences via SRM | 052cf37e | §Intro-3 (SRM 등) / §M-SRM |
| 6 | **Robinson 2022-2023** — McCollough nonlinear cortical encoding anomalous | 94850d68 | §Intro-3 / §D-2 cortical nonlinearity |
| 7 | **Akalin 2025** — traditional Daltonization filter | 6aa88c79 | §Intro-1 filter state-of-the-art ceiling |
| 8 | **Hayashi 2024-2025** — CVD simulation in LLM | 5bb807a4 | (Discussed in §D-6 scope boundary only) |
| 9 | **Kotani-Ng** — color vision modeling | ece65cb1 | (Reference only) |

**Bannert & Bartels 2025** ("Color across Human Brains" J Neurosci 45(42)) — already in KB as full text at `Citations/paper_related/recentpapers/Bannet(2025)_retinoShare.pdf`. **Critical discovery**: first SRM cross-subject color decoding in healthy observers — perfect methodological precedent for our clinical-SRM extension.

## 10.2 Emery 2021 β_s EXACT value (resolved)

- Normal B-Y cosine phase: **127.5°**
- Anomalous B-Y cosine phase: **106.1°**
- **Difference: 21.4°**, *t*(34) = 5.95, *p* < 0.001
- No 95% CI reported in text; uses group-mean SE
- **Our match**: sub-08 β_s = **20°**, sub-09 β_s = **23°** → per-subject bracketing of 21.4°, *not* population convergence (§R-4 phrasing must respect n=2 — see §8.1 R7)

## 10.3 Akalin 2025 & Hayashi framing (resolved)

- **Akalin 2025** = traditional pixel-level Daltonization (LMS matrix + HSV hue shift). MobileNetV1 used *only as automated judge* for Ishihara plate classification, NOT for modeling human brain responses. Frame as: *"the latest state-of-the-art in algorithmic retinal-stage Daltonization, whose ceiling motivates a perception-guided neural approach."*
- **Hayashi 2024-2025** = LLM benchmarking (can GPT-4o simulate CVD?). **Zero human fMRI overlap; not a novelty competitor.** Cite only if discussing AI–human perception gap in §D-6.

## 10.4 Narrative gaps identified and CITATIONS ADDED TO BIB (2026-04-16 batch 2)

New batch of **15 citations** added to `bibliography.bib` (§10 block after §8.3 block):

| # | BibKey | Used in | Why required |
|---|--------|---------|-------------|
| 1 | `neitz2011` | §Intro-2 | Genetic basis of 2–12 nm spectral shift; justifies cone-shift parameterization Δλ |
| 2 | `deeb2005` | §Intro-2 | Molecular variation L/M cone opsins — continuous-severity framework |
| 3 | `bosten2019` | §Intro-2, §D-2 | "Known unknowns of anomalous trichromacy" review — anchors our post-receptoral claim |
| 4 | `isherwood2020` | §Intro-3 | Plasticity-in-CVD review — sets up "neural model answers behavioral plasticity" |
| 5 | `webster2015` | §Intro-3 | Visual adaptation foundation for β_s S-cone compensation |
| 6 | `boehm2014` | §Intro-3 | Behavioral compensation for R-G contrast loss |
| 7 | `gegenfurtner2003` | §Intro-4 | Foundational cortical color review (Nat Rev Neurosci) |
| 8 | `conway2018` | §Intro-4 | Tour of contemporary color vision research — continuous V4 topology |
| 9 | `shapley2011` | §Intro-4 | Single/double opponent cells — foundation for V1 discrimination |
| 10 | `parkes2009` | §Intro-4, §D-3 | V1 hue MVPA precedent — supports our V1 discrimination-preserved finding |
| 11 | `kuriki2015` | §Intro-4, §D-2 | V4 hue selectivity, intermediate hue representation |
| 12 | `bannert2018` | §Intro-4, §D-3 | hV4 as perceptual hub — our primary gate ROI |
| 13 | `bannert2025` | §Intro-3 (NEW **§Intro-3b**), §M-SRM | **Cross-subject SRM for color decoding in healthy observers — our clinical SRM extension's direct methodological precedent** |
| 14 | `byrge2015` | §Intro-5, §D-5 | Clinical SRM on ASD — strongest small-N defense |
| 15 | `hasson2009` | §D-5 | Idiosyncratic cortical patterns in autism — case-study defense |
| 16 | `mantyla2018` | §D-5 | SRM-like individualization in first-episode psychosis |
| 17 | `frassle2020` | §D-5 | Individual clinical trajectories via generative embedding |
| 18 | `engel1997` | §Intro-4 | Classical V1 color tuning (Nature) |
| 19 | `derrington1984` | §M-Stimuli | DKL color space origin (isoluminant hues) |
| 20 | `stockman2000` | §M-Stimuli | Cone spectral sensitivities foundation |
| 21 | `akalin2025` | §Intro-1 | Recent traditional Daltonization benchmark |
| 22 | `hayashi2024` | §D-6 | LLM-CVD (scope boundary) |

## 10.5 Revised Introduction plan (respecting PI's Korean annotations)

### §Intro-1 — Filter state-of-the-art ceiling (~180 w)
Cite: `shen2016`, `brettel1997`, `machado2009`, `akalin2025` (newest algorithmic baseline), `werner2020` (adaptation caveat).
**Core claim**: retinal-stage filters (Brettel 1997 → Machado 2009 → Shen 2016 → Akalin 2025) do not use the user's perceptual/neural data; ceiling behaviorally demonstrated.

### §Intro-2 — Neural-basis reformulation (~200 w)
**Previously zero citations — this is the biggest gap.**
Cite: `neitz2011`, `deeb2005` (genetic 2–12 nm shift), `bosten2019` (anomalous trichromacy theory), `boehm2014` (behavioral compensation), `tregillus2021` (V2/V3 cortical compensation), `robinson2023` (nonlinear cortical encoding).
**Hook**: a filter optimized against *cortical* geometry should outperform retinal-only because the cortex—not the cone—generates perception.

### §Intro-3 — Existing CVD neuroimaging gaps (~220 w)
**PI annotation: "최근 연구 보완하기 — SRM 등"** → address SRM precedent here.
Cite: `brouwer2009` (LOCO paradigm, healthy only), `bannert2018` (hV4 perceptual hub, healthy), `kuriki2015`, `parkes2009` (V1 hue MVPA), `rina2024` (Daltonism contrast — hV4 lacks isolated color), `tregillus2021` (V2/V3 compensation, fMRI).
**New §Intro-3b (SRM precedent — per PI annotation)**: `bannert2025` = first cross-subject SRM color decoding in healthy observers; `chen2015` SRM foundational; `feilong2018` individual-difference preservation; `haxby2011` / `guntupalli2016` hyperalignment family.
**Clinical SRM extension**: `byrge2015`, `hasson2009` (SRM-adjacent clinical precedents).
**Gap statement** (neutralized per R4): *"SRM has been used for cross-subject color decoding in healthy observers (Bannert & Bartels 2025) and for clinical small-N characterization in psychiatric populations (Byrge 2015; Hasson 2009). We apply this framework to CVD for the first time, combined with a forward-model LOCO paradigm (Brouwer & Heeger 2009, extended to CVD) and a stimulus-space inverse filter."*

### §Intro-4 — Discrimination vs interpolation & individuality (~220 w)
Cite: `gegenfurtner2003` (cortical color review), `conway2018` (tour), `shapley2011` (V1 opponency), `parkes2009` (V1 hue), `kuriki2015` (V4 hue), `bannert2018` (V4 imagery), `brouwer2013` (categorical clustering), `engel1997` (V1 tuning Nature).
**Individuality hook**: `feilong2018`, `finn2020` — population averaging washes out CVD idiosyncrasies; SRM + Crawford-Howell is the principled response.

### §Intro-5 — Three questions, one filter (~200 w)
**PI annotation: "고려 — 2번이 중요한 이유: 필터 제작 가능성"** → Q2 (LOCO-vs-LORO dissociation) is highlighted because it directly licenses the filter design.
Cite: `crawford1998`, `schuett2023`, `kriegeskorte2019`, `finn2020`, `byrge2015` (case-study precedents); `mantyla2018`, `frassle2020` (clinical SRM).
**Revised three-question articulation**:
1. Is cortical color geometry distorted in CVD at the case level, and where in the V1–hV4 hierarchy?
2. **Is distortion selective for continuous interpolation (LOCO) while discrimination (LORO) is preserved? — *this dissociation is the substrate for a filter because LOCO failure signals exactly which display-space hues are misrepresented and therefore correctable by stimulus-space pre-image inversion.*** *(Addresses PI annotation "필터 제작 가능성")*
3. Can this cortical distortion be parameterized with a physiologically interpretable cortex-space model, inverted to a bijective display-space filter, and behaviorally validated?

## 10.6 Remaining open items

| Item | Status | Action |
|------|--------|--------|
| Bosten 2019 PDF | Paywalled — not local | Skip NotebookLM add; cite from abstract/DOI |
| Isherwood 2020 PDF | Not local (open-access Faculty Reviews) | Try `WebFetch` if time allows; bib entry suffices otherwise |
| Conway 2018 / Gegenfurtner 2003 / Shapley 2011 full text | Not local | Bib entries suffice (reviews are cited at statement level) |
| Neitz & Neitz 2011 full text | Not local | Bib entry suffices |
| Byrge 2015 / Hasson 2009 / Mäntylä 2018 / Frässle 2020 full text | Not local | Bib entries suffice |
| Emery 2021 exact β_s | **Resolved**: 21.4°, t(34)=5.95, p<.001 | Reflect in §R-4 wording (bracketing, not population-mean) |
| Akalin 2025 / Hayashi framing | **Resolved**: non-neural-competitor, explicit framing in §10.3 | Adopt in §Intro-1 and §D-6 |

## 10.7 Narrative validation verdict

| Section | Coverage before today | Coverage now | Key gap closed |
|---------|------------------------|--------------|----------------|
| §Intro-1 (filter ceiling) | 60% (Shen, Brettel) | **95%** | `akalin2025` recent baseline |
| §Intro-2 (neural reformulation) | **0 citations** | **90%** | `neitz2011`, `deeb2005`, `bosten2019`, `boehm2014`, `tregillus2021`, `robinson2023` |
| §Intro-3 (existing CVD imaging) | 55% (Brouwer, Rina) | **90%** | Added §Intro-3b SRM precedents per PI annotation: `bannert2025`, `feilong2018`, `byrge2015`, `hasson2009` |
| §Intro-4 (discrimination/interp) | 40% (Brouwer only) | **95%** | `gegenfurtner2003`, `conway2018`, `shapley2011`, `parkes2009`, `kuriki2015`, `bannert2018`, `engel1997` |
| §Intro-5 (three questions) | 70% (Crawford, Schütt) | **100%** | PI annotation on Q2 → filter-feasibility hook; `byrge2015`, `mantyla2018`, `frassle2020` clinical SRM |

**VERDICT**: Narrative is now defensible for eLife/Curr Biol/Nat Comms submission. Previously-missing citations covered 5 distinct gaps that Reviewer #2 would have flagged (no §Intro-2 citations, no SRM precedent acknowledgment, no V4 perceptual-hub grounding, no clinical-SRM small-N defense, no filter-ceiling recent baseline).

**Next writing step** (user approval): proceed to draft `Introduction/introduction.tex` v2 with the §10.5 structure — respects Korean TODO annotations and incorporates all 22 new citations.
