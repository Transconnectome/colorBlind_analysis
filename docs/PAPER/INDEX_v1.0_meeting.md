# colorBlind — Meeting Outline (logical flow only, synced with `INDEX_v1.0.md` / v1.1 2026-05-04)

> Subtitle + 1–2 lines per item so the logical flow is visible at a glance. Full detail in `INDEX_v1.0.md` (§0 framework lock + paragraph drafts) and current `Results/results_v3.tex` / `Introduction/introduction_v2.tex` / `Methods/methods_streamlined.tex`.
>
> **v1.1 key decisions** (2026-05-04 reconciliation with `future_phase2_filter_optimization/CLAUDE.md` §0 lock + `behav_validation.md` §3 sub-08 PASS):
> 1. **§0 Framework Decision (LOCKED, 절대 재논의 금지)**: filter selection = **per-subject LOCO-best fit + behavioral validation**. Specificity는 descriptive only — selection criterion 아님. Cycle 9–13에서 13회 시도된 selection-rule reformulation 모두 closed. Behavioral PASS overrides LOCO ρ ranking (sub-08 R+C → 2-component 사례).
> 2. **Sub-08 R+C structurally retired** (behav §2 / §6 #2): 1-DOF RG knob `(1+g)=−1.25` ⇒ YG-C 4-way collapse 행동검증 확인. v1.0의 "primary description + carried forward" framing 폐기. 2-component이 sub-08 채택 모델 (behav §3 PASS 2026-04-17).
> 3. **Sub-08 behavioral observed (2026-04-17)** — preregistered가 아님. YG-C dissolution (c3≠c4, c5≠c6, protan-axis−≠sRGB C). 잔여: c2 orange (color-local FAIL, B1 closed), c8 magenta (color-local FAIL, B2 c8-only variant 진행 중).
> 4. **Sub-09 behavioral pending** — Phase A LOCO canonical (β_s=6°, β_c=−22°); cross-ROI alternative (30°, +26°); mw_jaccard candidate (44°, +54°). 행동검증으로 후보 선택.
> 5. **Closed-testing rule REMOVED** (v1.0 §M-6c): Machado→R+C 위계 검정은 §0 위반. 3 model classes independently fit; 행동 PASS 또는 LOCO-best (행동 pending) 기준.
> 6. **§R-6 specificity defense reframed**: v1.0 "4-pillar specificity defense" → v1.1 "descriptive disclosure". 추론 anchor는 **behavioral validation + cross-modal Emery 21.4°**, NOT specificity claim.
> 7. **Sub-08 R+C g sign fix**: `+2.25 → −2.25` (sign-inversion + 25% amplification). v1.0/results_v3.tex 부호 오류 inherited. R+C는 어차피 retire되었지만 내러티브 일관성 위해 정정.
> 8. **§2.5 Loss inventory disclosure (NEW, 2026-05-03)**: 12 loss variants × 8 subjects bootstrap. 단 mw_jaccard hV4만이 두 CVD 모두 distinct. Sub-09 cross-loss β_s 6° vs 44° disagreement → 행동검증으로 해결.
>
> **v1.0 inherited decisions** (확정 유지, 변경 없음):
> - Target journals: eLife (★★★★★) → Curr Biol → Nat Comms.
> - Case-study framing (Crawford-Howell + Schütt 2023).
> - n=2 effective CVD (sub-10 Supp only).
> - Results §R-1..§R-6 6-section restructure (LORO+LOCO combined, ΔRDM evidence-first, HC FPR main-text).
> - Bibliography 22-citation batch (PLAN_ToC §10.4): Bannert 2025 SRM, Tregillus 2021, Emery 2021, Schütt 2023, Finn 2020, Feilong 2018, Byrge 2015, Hasson 2009, Neitz 2011, Deeb 2005, Bosten 2019, ...

---

## Provisional Title (3 candidates, decision pending)

1. **"Cortical color geometry in color vision deficiency: an individualized 2-component model and a bijective display-space inverse"** (PLAN_ToC §8.3 recommendation; preserves neural→filter bridge without over-claiming)
2. **"Neural geometry of color in color vision deficiency predicts individualized display correction"** (eLife/Nat Neuro tone)
3. **"Color discrimination is preserved but continuous hue geometry is distorted in color vision deficiency: a neural basis for individualized display filters"** (descriptive)

**Recommendation**: (1) for eLife; (3) for Curr Biol; (2) only if Session-2 behavioral data supports the "predicts" verb.

---

## Abstract (≤250 words, 6-sentence target)

1. **Motivation** — CVD filters (Brettel 1997, Machado 2009, Akalin 2025, EnChroma) operate at the retinal stage; cortical geometry of anomalous trichromacy at the case level is under-characterized.
2. **Gap** — whether cortical color geometry is *specifically* distorted beyond retinal prediction, whether distortion is individually patterned, and whether an explicit display-space pre-image of a cortical-space model can be computed, remain open.
3. **Approach** — 7 HC + 2 CVD (Sub-08 deutan, Sub-09 protan) fMRI × 8 isoluminant hues × V1/V2/V3/hV4; SRM HC-only common space; forward encoder + LORO/LOCO; three cone-shift models (Machado / R+C / 2-component) under composite LOCO loss including δ·L_rdm; bijective pre-image search; same-day behavioral validation (sub-08 / sub-09).
4. **Neural result** — In hV4, hue *discrimination* (LORO) is preserved while hue *interpolation* (LOCO) is impaired (Sub-08 ρ=0.08, Sub-09 ρ=0.12 vs HC ρ=0.42); SRM ΔRDM at V1 confirms geometric distortion (Sub-09 p=.026; Sub-08 V1 LOCO p=.001 / hV4 LOCO p=.004).
5. **Model result** — 2-component angular dilation is the only cortex-space model yielding a **bijective pre-image** for both severity levels (8/8 exact, residual <0.001°), and a per-subject β_s of 20° (Sub-08) / 23° (Sub-09) bracketing Emery et al. (2021)'s 21.4° behavioral B-Y rotation.
6. **Scope** — Filter selection is per-subject LOCO-best fit anchored by behavioral validation (sub-08 2-component PASS observed 2026-04-17; sub-09 pending); under label-permutation voxel-prediction L_LOCO, HC FPR is 7/7 for the 2-component family. **Specificity is not claimed at the model-selection level**; behavioral validation is the inferential anchor, with cross-modal Emery 21.4° match as descriptive convergence (per §0 framework lock).

---

## §Intro Outline (5 subsections, ~1,000 words)

### §Intro-1 — Filter state-of-the-art and its retinal-stage ceiling (~180w)
- Brettel 1997 / Machado 2009 / Shen 2016 / **Akalin 2025** (latest algorithmic benchmark) + EnChroma all act on cone responses. Werner 2020 adaptation caveat.
- **Hook**: behavioral uptake uneven (Gomez-Robledo 2018; Hassan & Crognale 2023) because retinal models cannot predict cortical outcome.

### §Intro-2 — Why a neural-basis reformulation (~200w)
- Genetic 2–12 nm L/M opsin shift (`neitz2011`, `deeb2005`); anomalous-trichromacy theory (`bosten2019`); behavioral compensation (`boehm2014`); cortical compensation in V2/V3 (`tregillus2021`); nonlinear cortical encoding (`robinson2023`).
- **Claim**: a filter optimized against *cortical* geometry should outperform retinal-only because the cortex — not the cone — generates perception.

### §Intro-3 — Existing CVD neuroimaging gap, with SRM precedent (~220w, includes new §Intro-3b per PI annotation "최근 연구 보완하기 — SRM 등")
- LOCO paradigm precedent (`brouwer2009`, healthy only); hV4 perceptual hub (`bannert2018`, `kuriki2015`); V1 hue MVPA (`parkes2009`); CVD-specific imaging (`rina2024` — Daltonism contrast: hV4 lacks isolated color in dichromacy).
- **§Intro-3b SRM precedent**: `bannert2025` first cross-subject SRM color decoding in healthy; `chen2015` SRM foundation; `feilong2018` individual differences; `byrge2015` + `hasson2009` SRM-adjacent clinical small-N.
- **Gap statement (neutralized per redteam R4)**: SRM has been used for healthy color decoding (Bannert 2025) and clinical small-N characterization (Byrge 2015); we apply this to CVD for the first time, combined with Brouwer & Heeger (2009) LOCO extended to CVD, and a stimulus-space inverse filter.

### §Intro-4 — Discrimination vs interpolation, individuality (~220w)
- Cortical color reviews (`gegenfurtner2003`, `conway2018`, `shapley2011`); V1 hue (`parkes2009`, `engel1997`); V4 hue (`kuriki2015`, `bannert2018`, `brouwer2013`).
- **Individuality hook**: `feilong2018`, `finn2020` — population averaging washes out CVD idiosyncrasies; SRM + Crawford-Howell is the principled response.

### §Intro-5 — Three questions, three contributions, one filter (~200w; PI annotation: "Q2 important for filter feasibility")
1. Is cortical color geometry distorted in CVD at the case level, and where in V1–hV4?
2. **Is distortion selective for continuous interpolation (LOCO) while discrimination (LORO) is preserved? — *this dissociation is the substrate for a filter because LOCO failure signals exactly which display-space hues are misrepresented and therefore correctable by stimulus-space pre-image inversion.***
3. Can this distortion be parameterized with a physiologically interpretable cortex-space model, inverted to a bijective display-space filter, and behaviorally validated?

---

## §Methods Outline (7 subsections, ~2,000 words; existing draft mostly intact)

### §M-1 Participants
- 7 HC (Sub-01..07) + 2 main CVD (Sub-08 deutan / Sub-09 protan) + Sub-10 (near-normal, Supp). Demographics + Ishihara plates + 8AFC accuracy (used in R-1 first sentence).
- Crawford-Howell single-case framing statement.

### §M-2 Stimuli & fMRI experiment
- 8 isoluminant DKL hues × 6 runs × 8 colors + blank; RSVP attention task. `derrington1984`, `stockman2000`.

### §M-3 Preprocessing
- fMRIPrep method3_header_mi; Procrustes within-subject; ROI definition (V1/V2/V3/hV4 retinotopic).

### §M-4 SRM common space
- HC-only training (eliminates circularity); K=4/4/3/3 V1/V2/V3/hV4 (mean rank aggregation); LOO refs for CVD. `chen2015`, `feilong2018`, `bannert2025`.

### §M-5 Forward encoding + LORO/LOCO
- ridge_gcv, K=3 half-wave rectified squared sinusoidal channels; LORO leave-one-run-out; LOCO leave-one-color-out → vulnerability vector $\mathbf{v}\in\mathbb{R}^8$; pooled-runs (42 samples = 6×7) per memory `LOSO Zero-Shot`.

### §M-6 (NEW) Cone-shift models, LOCO loss, per-subject selection
- **Three mechanistic classes**: Machado 1-DOF retinal Δλ / R+C 2-DOF (Δλ + 1-DOF cortical RG gain g) / **2-component 2-DOF cortical (β_s S-cone, β_c confusion-axis — independent direction parameters)**.
- **L_LOCO** = α·L_vuln/4 + β·L_rank/2 + **δ·L_rdm/2** + ε·L_smooth/32400 (α=1, β=δ=0.5, ε=0.1). δ·L_rdm motivated by §R-2 ΔRDM evidence.
- **Per-subject selection (per §0)**: 3 classes fit independently; **final model = behavioral PASS** (sub-08 = 2-component) or **LOCO-best with behavioral pending** (sub-09 = 2-component candidate). No closed-testing.
- **Sub-08 R+C structurally retired**: g=−2.25 ⇒ YG-C 4-way collapse (behav §2 / §6 #2). Reported descriptively only.

### §M-6.5 Loss inventory + HC sanity check (NEW v1.1, 2026-05-03)
- 12 loss variants × 8 subjects bootstrap rank-based emp_p ≤ 0.20 sig threshold.
- **Only `mw_jaccard_loss` (hV4)** distinguishes both CVD subjects from HC distribution.
- Canonical L_LOCO is "✓ one distinct" for sub-08 only; sub-09 hV4 is degenerate at (0,0) under several variants — only cross-ROI / mw_jaccard extracts non-trivial parameters.
- **Sub-09 cross-loss β_s disagreement**: 6° (canonical) vs 44° (mw_jaccard) — measurement-family-dependent finding at 8-color resolution; resolved at per-subject level by behavioral validation (§R-5b).

### §M-7 (NEW) Pre-image filter derivation + bijectivity check
- Given fitted distortion D̂(θ), compute θ_in = argmin ‖D̂(θ) − θ_target‖ (grid 0–360° × 0.5°); per-color residual reported.
- **Bijectivity gate**: model is filter-eligible only if pre-image is exact (residual <0.001°) for all 8 training hues; full-circle Jacobian |dθ_out/dθ_in| reported as off-training stability check (per redteam R5).

### §M-8 (NEW, short) HC specificity acknowledgment
- One-line pointer to §R-6: empirical HC FPR for cone-shift family is high (memory `HC Specificity`); single-case interpretation justified by Schütt 2023 + cross-modal Emery convergence + behavioral validation.

---

## §Results Outline (6 subsections, ~2,500 words, **revised structure 2026-04-30**)

> v3 had R-1..R-6 = phenotype / LORO / LOCO / fits / SRM ΔRDM / pre-image. v1.0 INDEX restructures to: combine LORO+LOCO, move SRM ΔRDM before fits, drop standalone phenotype, promote HC FPR to main.

### §R-1 (NEW) Discrimination preserved, interpolation impaired (LORO + LOCO combined)
- **Opening sentence**: 8AFC accuracy confirms each CVD axis (Sub-08 deutan 0.71, Sub-09 protan 0.62, HC 0.94 ± 0.04).
- **LORO**: HC-CVD permutation NS at every ROI (hV4 p=0.668; V1 p=0.542; V2 p=0.611; both classifications above 0.125 chance) → filter precondition met.
- **LOCO at hV4**: HC ρ=0.42 ± 0.14 (Brouwer 2009 replication); Sub-08 ρ=0.08, Sub-09 ρ=0.12 (near floor); V1/V2 large gaps (g>1.6).
- **Per-hue vulnerability is subject-specific**: Sub-08 c2/c3, c7; Sub-09 c5/c6, c8. → individually-structured target.
- **Dissociation paragraph**: same forward model, same voxel set, same CV → discrimination ≠ interpolation. Direct answer to Intro Q2.
- **Figure**: 2-panel side-by-side LORO bars / LOCO bars × ROI × group, same y-scale.

### §R-2 (REPOSITIONED) SRM ΔRDM — descriptive geometric distortion
- ΔRDM = RDM_CVD − mean(RDM_HC,LOO) in HC-trained SRM space.
- **Findings**: Sub-09 V1 ΔRDM p=.026; Sub-08 V1 ΔRDM p=.179 (NS) → per-subject divergence at the geometric level.
- **β_s convergence preview**: when β_s is refit *directly* against V1 ΔRDM (LOCO-free), Sub-08 ≈ 20°, Sub-09 ≈ 23°, mean ≈ 21.5° — bracketing Emery 21.4° (introduced fully in R-3).
- **Bridge to R-3**: this geometric distortion motivates including δ·L_rdm in the LOCO loss → next section justifies the loss form.

### §R-3 (PER-SUBJECT FITS + SELECTION per §0) Cone-shift descriptive fits
- All three classes fit independently per subject (no closed-testing).
- **Sub-09 protan**: Machado Δλ=13.5 nm, ρ=0.762, p=.018 (within 2–12 nm range); R+C g*=0; **2-component β_s=6°, β_c=−22°, p=.035 (Phase A canonical)** + alternative candidates from §M-6.5.
- **Sub-08 deutan**: Machado trend only (p=.058 underpowered); **R+C Δλ=2.5 nm, g=−2.25, p=.005 — STRUCTURALLY RETIRED** (behav §2 YG-C collapse; reported descriptively only); **2-component β_s=38°, β_c=−14°, p=.004 — adopted (behav PASS 2026-04-17)**.
- **Per-subject status table**: sub-08 final = 2-component (behav PASS); sub-09 = 2-component candidate (behav pending); sub-10 excluded.
- **Cross-criterion descriptive complementarity**: sub-08 hV4 LOCO-sig / V1 ΔRDM-NS; sub-09 hV4 LOCO-sig (Machado) / V1 ΔRDM-sig — motivates δ·L_rdm in L_LOCO. **Not** a "dual-criterion specificity claim" (per §0).

### §R-4 (PRE-IMAGE → FILTER) Bijective inversion + per-subject filters
- Pre-image search 0–360° × 0.5° per (model, subject); residual + Jacobian reported.
- **Sub-08 (Δλ=2.5 nm)**: arc preserved; R+C structurally retired (behav §2). Machado underpowered (near-identity, behav §2-5). **2-component 8/8 exact, mean |δ|=46.3°** — adopted.
- **Sub-09 (Δλ=13.5 nm)**: arc compresses 360°→~96°; Machado 4/8 exact only; **2-component 8/8 exact, mean |δ|=20.1°** — only bijective class.
- **R+C vs 2-component correction divergence (sub-08, descriptive)**: cos=−0.18, sign agreement 3/8 despite comparable LOCO ρ — numerical signature of behav §2-4 "one knob, two stations". Behavioral test (§R-5a) **observed PASS** for 2-component direction.
- **Verdict per §0**: 2-component is the per-subject filter substrate for both subjects (sub-08 PASS, sub-09 pending).

### §R-5 (BEHAVIORAL VALIDATION + SESSION-2 fMRI)
- **Sub-08 OBSERVED (2026-04-17, behav §3 PASS)**: 2-component qualitative test on 12 stimuli. **Primary falsifier — YG-C 4-way collapse — DISSOLVED** (c3=연두 / c4=warm-ivory / c5=light-sky / c6=dark-sky distinct). R+C side-by-side comparison resolves 3 collapses. Color-local FAIL: c2 orange→green (B1 fine grid closed unrecoverable), c8 magenta→dark-sky (B2 c8-only variant pending).
- **Sub-09 PROSPECTIVE**: same template, candidates {Phase A (6°,−22°), cross-ROI (30°,+26°), mw_jaccard (44°,+54°)}. PASS criterion: c1 protan compensation, c5/c6 separation, c8 magenta handling.
- **Quantitative 2AFC JND + 8-AFC** under {uncorrected / Akalin / class-specific} × confusion-axis pairs.
- **Session-2 fMRI under filters**: Δ-LOCO descriptive, no group inference.
- **Fallback if sub-09 behav slips >4 weeks**: retain sub-08 §R-5a observed; retarget eLife Short Report.

### §R-6 (PROMOTED FROM SUPP, REFRAMED v1.1) Single-case framework — descriptive disclosure (not specificity defense)
- **Per §0**: HC FPR is reported as **descriptive limit of an expressive model** on n=8 colors / n=6-effective-HC, NOT as defended specificity. Cycle 9–13 (13 cycles) confirmed no reformulation rescues specificity within voxel-prediction L_LOCO family.
- HC FPR: 7/7 (2-component), 5/7 (R+C), 3/7 (Machado) under label-permutation. HC sub-03 V1 2-comp ρ=0.929 = sub-09 best. Baseline-Δρ HC corr=−0.894 dominates.
- **Inferential anchors** (replacing v1.0 4-pillar defense): (i) **behavioral validation as ground truth** (sub-08 PASS observed; sub-09 pending); (ii) **cross-modal Emery 21.4° descriptive convergence** (sub-08 β_s=20°, sub-09 β_s=23° single-subject brackets); (iii) **physiological grounding** (Δλ 2–14 nm range; β_s/β_c structure coherent with Tregillus / Robinson / Webster post-receptoral compensation literature).
- **Closing**: per-subject descriptive (Crawford-Howell positional) + externally convergent (Emery brackets) + behavioral falsifier. **No CVD-vs-HC group specificity claim**.

---

## §Discussion Outline (7 subsections, ~2,000 words)

### §D-1 Summary (~150w)
Three findings: (i) discrimination–interpolation dissociation in CVD hV4, (ii) 2-component as only model dual-validated + bijective, (iii) β_s match with Emery 21.4° + per-subject filter behavioral payoff.

### §D-2 Cortical geometry beyond confusion-lines (~400w)
Integrate Brouwer & Heeger 2009, Bannert & Bartels 2018/2025, Parkes 2009, Kuriki 2015. β_s ≈ 21.5° as cortical S-cone gain up-regulation; behaviorally validated by Emery 21.4°. β_c subject-specific compensatory realignment.

### §D-2b Anomaly-vs-Daltonism contrast (NEW, per redteam audit)
Anomalous trichromacy preserves a *distorted* hV4 geometry; this contrasts with `rina2024` (Daltonism abolishes isolated hV4 color activity). Anomaly retains cone signal sufficient for cortical geometry; dichromacy does not — itself a continuous-severity prediction (`tregillus2021`, `basim2025`).

### §D-3 LOCO/LORO dissociation as functional marker (~350w)
RDM = metric properties; LOCO = functional interpolation. Memory `Behavioral Cross-Modal`: LOCO→JND 100% concordance; SRM z→JND 33%. V1/V2 discriminate via local contrast; hV4 interpolates via full manifold (Bannert 2018).

### §D-4 Why 2-component, given HC FPR (~350w)
Machado cannot exceed Sub-09 arc compression; R+C requires non-physiological g=+2.25 for Sub-08. 2-component is bijective over training support. Schütt 2023: single-model significance is not the inferential basis; convergent + behavioral are.

### §D-5 Case-study framework + clinical SRM precedent (~300w)
`crawford1998`, `schuett2023`, `kriegeskorte2019`, `finn2020`, `feilong2018`, `byrge2015`, `hasson2009`, `mantyla2018`, `frassle2020`. Analogy: clinical stimulation mapping does not require between-subject statistics.

### §D-6 Limitations and future work (~300w)
n=2 effective CVD; protan/deutan subtype matrix under-sampled. Same-day adaptation; long-term unknown (Werner 2020). CIE Lab is HC-optimized. Pre-registered scaled cohort (n≥10) replication. LLM-CVD scope boundary (`hayashi2024`).

### §D-7 Conclusion (~100w)
CVD alters continuous cortical hue geometry with individually-patterned distortions. 2-component cortical model is bijective and behaviorally validated. Neural-geometry-guided display adaptation as a feasible precision color-vision pathway.

---

## Figures (5 main + 4 supplementary)

| Fig | Content | Source / status |
|-----|---------|-----------------|
| **F1** | Stimulus + ROI overview + pipeline schematic | existing `fig1a_output.png` |
| **F2** | LORO + LOCO bars × ROI × group (2-panel side-by-side, NEW for v1.0 R-1) | `loco_baseline.py` outputs; needs assembly |
| **F3** | SRM ΔRDM heatmaps + per-pair bootstrap (R-2) | `rerun_loo_consistent.py` outputs; needs re-plot |
| **F4** | Cone-shift model comparison: closed-testing landscape + per-subject vulnerability fit (R-3); existing `fig1_panels_bcd.pdf` | needs caption update |
| **F5** | Pre-image inversion + arc-collapse + correction-vector divergence (R-4); existing `fig2_output.png` | needs caption update |
| **F6** | Behavioral JND + Session-2 fMRI under filters (R-5) | **PENDING Session-2 acquisition** |
| **F7 / S1–S4** | HC FPR distributions; sub-10 incidental control; Procrustes QA; basis-channel K sensitivity | partial existing; HC-FPR figure may be promoted to main |

---

## Bibliography state (`bibliography.bib`)

- **Total entries**: ~80+ (PLAN_ToC §10.4 batch added 22 new in 2026-04-16)
- **Critical clusters**:
  - **Filter ceiling**: `brettel1997`, `machado2009`, `shen2016`, `akalin2025`, `werner2020`
  - **Anomalous trichromacy theory**: `neitz2011`, `deeb2005`, `bosten2019`, `boehm2014`, `tregillus2021`, `robinson2023`, `emery2021`
  - **CVD imaging**: `rina2024`, `wachtler2003`, `rabin2011`, `tregillus2021`
  - **Cortical color**: `gegenfurtner2003`, `conway2018`, `shapley2011`, `parkes2009`, `kuriki2015`, `bannert2018`, `brouwer2009`, `brouwer2013`, `engel1997`
  - **SRM precedent**: `chen2015`, `bannert2025`, `feilong2018`, `haxby2011`, `guntupalli2016`
  - **Case-study framework**: `crawford1998`, `schuett2023`, `kriegeskorte2019`, `finn2020`, `byrge2015`, `hasson2009`, `mantyla2018`, `frassle2020`
  - **Color space**: `derrington1984`, `stockman2000`

---

## Risk register (v1.1)

| Risk | P | Mitigation |
|------|---|------------|
| **Sub-09 behavioral protocol delay (NEW)** | **H (active)** | §M-9 protocol scheduled; sub-08 §R-5a PASS already locked. If slip >4w: retarget eLife Short Report with sub-08-only behavioral. |
| Session-2 fMRI slips >4 weeks | M | §R-5d Δ-LOCO is descriptive companion; sub-08 qualitative PASS + Emery cross-modal preserved. |
| Sub-08/09 quantitative null after qualitative PASS | M | Report null honestly; sub-08 qualitative PASS is primary falsifier and locked. |
| Reviewer demands n ≥ 5 CVD | H | §D-6 pre-registered scaled cohort statement. |
| Rina 2024 priority claim | L | §D-2b dichromat-vs-anomaly distinction. |
| **HC-FPR reviewer challenge** | H | **No longer defense risk per §0**: R-6 descriptive limit framing; anchors = behavioral + Emery + physiological grounding. Schütt 2023 + Kriegeskorte 2019 frame the reply. |
| 2-component β_c interpretation | M | D-2 effective compensatory parameter framing. |
| **Sub-09 cross-loss disagreement (β_s 6° vs 44°) (NEW)** | **H** | §D-6 + §M-6.5 disclose loss-form sensitivity; sub-09 behavioral test (§R-5b) chooses among candidates. |
| Sub-08 c2 orange + c8 magenta color-local FAIL | L (disclosed) | §R-5a + §D-6: 8-color/2-DOF resolution limits; β_m fourth parameter as scaled-cohort proposal. |
| ~~Closed-testing rule criticized~~ | — | **Removed v1.1**: rule retired per §0. |
| ~~g=+2.25 biophysical implausibility~~ | — | **Removed v1.1**: sign was wrong (correct g=−2.25); R+C retired structurally via behav §2 not via biophysical argument. |

---

## Decision log

- **2026-04-30 (v1.0 cut)**: Created INDEX_v1.0_meeting.md and INDEX_v1.0.md; restructured Results §R-1..R-6 per user proposal (LOCO+LORO combined; SRM ΔRDM moved before fits; HC FPR promoted; phenotype dropped). PLAN_ToC.md retained as decision-log archive.
- **2026-05-04 (v1.1)**: Reconciliation with `future_phase2_filter_optimization/CLAUDE.md` §0 (2026-05-03 lock) + `behav_validation.md` §3 (sub-08 2-component PASS 2026-04-17). Added §0 Framework Decision (specificity-as-descriptive lock); removed closed-testing rule; sub-08 R+C structurally retired and g sign corrected (`+2.25 → −2.25`); §R-6 4-pillar specificity defense reframed as descriptive disclosure; §M-6.5 loss inventory section added; risk register reorganized.

---

## Outstanding items requiring PI input (next meeting)

1. **Title decision**: v1.1 working title is "Cortical color geometry in CVD: an individualized 2-component model and a bijective display-space inverse" — confirm or alternative?
2. **Sub-09 behavioral protocol date**: §M-9 schedule + candidate selection {Phase A canonical / cross-ROI / mw_jaccard} for §R-5b.
3. **Session-2 fMRI booking**: same protocol, both subjects, 4 filter conditions.
4. **Behavioral quantitative scope**: 2AFC JND only, or + 8AFC identification?
5. **F2 / F3 redraw priority**: LOCO+LORO 2-panel vs SRM ΔRDM heatmap — which first?
6. **Promote HC-FPR figure to main F7?** (per §R-6 reframing → main-text descriptive disclosure ✓ recommended.)
7. **Sub-08 c8 magenta variant (Track B2)**: render at θ ∈ {290°, 300°, 310°} for next behavioral test cycle.
8. **Loss inventory disclosure level**: §M-6.5 main text vs Methods Supplement?
