# Literature methodology comparison (Machado, Tregillus, Emery)

**Date**: 2026-05-19
**Purpose**: PI requested systematic comparison of how the three foundational cone-shift / compensation papers trained and validated their models, versus our current Phase 2 pipeline.
**Source**: NotebookLM notebook `ColorBlind_comprehensive` (id `fa13d441-21f2-40a0-8170-8cc8eb49cc7b`). All three papers PRESENT as PDF sources; queries executed 2026-05-19, restricted to the single matching source per paper. Direct quotes preserved verbatim from NotebookLM extraction.

> **Status of source availability**
> - Machado 2009 — PRESENT (`Machado_Oliveira_Fernandes_CVD_Vis2009_final.pdf`)
> - Tregillus 2021 — PRESENT (`Tregillus_2021_compensation.pdf`)
> - Emery 2021 — PRESENT (`Emery_2021_compensation.pdf`, plus the ScienceDirect HTML clone)
> **No additional uploads required.**

---

## 1. Machado 2009
*A Physiologically-based Model for Simulation of Color Vision Deficiency* — Machado, Oliveira, Fernandes (IEEE TVCG 2009).

### 1.1 Paradigm
- Validation task: **Farnsworth-Munsell 100-Hue (FM100H)** color-arrangement test, plus Ishihara test for CVD classification.
- Authors built a **computerized FM100H** in C++/OpenGL on calibrated CRTs and ran the test themselves on both NT and CVD observers.
- The *model itself* is an **analytical derivation**, not fit to behavior. It uses prior published Smith & Pokorny cone spectra and the Ingling & Tsou suprathreshold opponent transform.

### 1.2 Data
- 30 male subjects: **17 normal trichromats (NT)**, **13 CVD** (4 protanomalous, 4 protanopes, 3 deuteranomalous, 2 deuteranopes).
- Stimuli: **85 FM100H color caps** rendered on monitor; CVD subjects ran the original test, NT subgroups ran *simulated* CP12nm/CP16nm/CP19nm (and CD analogues) versions.
- No fMRI; no anomaloscope quotient reported in the extraction (CVD classification was Ishihara-based).

### 1.3 Fitting (loss function)
- **No statistical loss is minimized.** The model is fully analytical (Eq. 1, 8, 9, 10, 11 in paper).
- **Δλ (L/M cone spectral shift) is set a priori, not fit.** It is a tunable *simulation* parameter:
  > "We model anomalous trichromacy by shifting the spectral sensitivity function of the anomalous cone according to the degree of severity of the anomaly. A shift of approximately 20 nm represents a severe case…"
  > "ΔλL, ΔλM, and ΔλS represent the amount of shift applied to the L, M, and S anomalous cone."
- Free parameters in the *statistical* sense: **0** (NOT STATED in source as an optimization).
- Optimization method: **NOT STATED IN SOURCE** (none; analytical projection onto opponent basis functions).

### 1.4 Validation
- **No train/test split, no cross-validation, no hold-out** (NOT STATED in source as such — none applicable, no training phase).
- Validation strategy: **behavioral surrogate match.** NT subgroups (NTgp n=8, NTgd n=9) viewed CVD-simulated FM100H caps; their error-score patterns were qualitatively compared (via covariance-eigenvector geometry) to the patterns produced by actual CVD observers running the original caps.
- **Specificity / NT-null check: YES.** 17 NT observers ran the original (unsimulated) caps as a separate baseline (Fig. 11), confirming distinct, accurate performance.
- Headline finding:
  > "A comparison of the plots corresponding to the averaged results of the NTgp subgroup … and the averaged results of the protans reveals great similarity… These results indicate that the proposed model provides good simulations…"

### 1.5 Key quotes
- "We have validated the proposed model through an experimental evaluation involving groups of color vision deficient individuals and normal color vision ones." (abstract)
- "La(λ) = L(λ+ΔλL), Ma(λ) = M(λ+ΔλM), Sa(λ) = S(λ+ΔλS)" (Eq. 2–4)
- Citation key: `machado_oliveira_fernandes_2009`.

---

## 2. Tregillus 2021
*Color Compensation in Anomalous Trichromats Assessed with fMRI* — Tregillus, Isherwood, Vanston, Webster, MacLeod, Crognale (Current Biology 31:936–942).

### 2.1 Paradigm
- Behavior: **temporal 2AFC contrast detection** for L–M and S–LM gratings; minimum-motion isoluminance.
- fMRI: **block design**, "phase reversing (1 Hz) radial sinewave gratings (0.28 c/deg., 14.5° field) defined by chromatic variations along either the L versus M or S versus LM cone-opponent axes."
- **Attention control:** Experiment 1 used a simple fixation task; **Experiment 2** added a "more demanding fixation task" to "further isolate 'bottom-up' processing."
- **Note on R+C framing:** the paper does *not* itself decompose retinal vs cortical with that label.
  > "Explicit retinal-vs-cortical decomposition (R+C) test: NOT STATED IN SOURCE. (While they compare V1 against V2v/V3v, there is no explicit modeling or test named an 'R+C decomposition')."
  Our project's "R+C model" inherits the *idea* (reduction-vs-amplification CRF comparison) but the explicit retinal+cortical generative formulation is a downstream construction.

### 2.2 Data
- **7 anomalous trichromats (AT)** + **7 color-normal (CN)** + **1 dichromat (protanope) control**. Per-experiment counts smaller (Exp 1: 5 AT / 5 CN; Exp 2: 5 AT / 7 CN).
- 2 chromatic axes × 4 contrast levels = **8 conditions**; Exp 1: 8 runs; Exp 2: 6 runs.
- Voxels 2.75 × 2.75 × 3 mm³; ROIs: **V1, V2v, V3v** (anatomical retinotopic template).
- CVD classification: **anomaloscope (Heidelberg Multi-Color Anomaloskop), anomaly quotient (AQ)**.

### 2.3 Fitting (loss function)
- **Contrast Response Function (CRF) fit:** baseline 4-parameter Naka-Rushton-like CRF fit to CN group; AT data then fit by adding a single multiplicative parameter sc on effective contrast.
  - Base CRF: `R(c) = R_max · c^(p+q) / (c^q + c50^q)`  (4 params: R_max, c50, p, q)
  - Reduction null: `R(c) = R_max · (t·c)^(p+q) / ((t·c)^q + c50^q)`  (t = threshold ratio, **fixed from psychophysics**, **no free param**)
  - Amplification: `R(c) = R_max · (sc·t·c)^(p+q) / ((sc·t·c)^q + c50^q)`  (adds sc as the 1 free param)
- Estimation: **per-individual AT optimization of sc**, then `log(sc)` aggregated with one-sample t-test against 0 (= reduction null).
- Free params in the AT-side fit: **1** (sc). Loss form: **NOT STATED IN SOURCE** as a closed-form equation, but the description is consistent with **least-squares CRF fit per subject**.

### 2.4 Validation
- **Train/test split, cross-validation, hold-out subjects/runs: NOT STATED IN SOURCE.**
- Generalization strategy used instead: **independent replication via Experiment 2** with a more demanding attention task.
- **Specificity tests:**
  - Direct AT vs CN group comparison.
  - **Built-in null axis:** S-vs-LM axis serves as internal control because S cones are unaffected by L/M anomalies → amplification *not* predicted there, providing a within-subject null.
  - Dichromat (protanope) control subject.
- **Alternative-null test:** explicit comparison of "reduction" (no amplification) vs "amplification" (sc > 1) model — a real, pre-registered null hypothesis.

### 2.5 Key quotes
- "We next compared responses of AT observers to predictions of the reduction model, which assumes that all differences between groups are due to photoreceptor sensitivity differences (i.e., that no amplification occurs)."
- "A ratio of 1 would indicate that the AT's CRF was consistent with the reduction model, and values greater than 1 would indicate compensation."
- Citation key: `tregillus_2021`.

---

## 3. Emery 2021
*Color perception and compensation in color deficiencies assessed with hue scaling* — Emery, Parthasarathy, Joyce, Webster (Vision Research 183:1–15).

### 3.1 Paradigm
- **Hue-scaling task** (proportional assignment to red/green/blue/yellow primaries) + **chromatic contrast threshold detection** (4AFC, 1° quadrant, 250 ms pulse, staircase).
- **Pure psychophysics; no neural/fMRI data.**

### 3.2 Data
- **10 anomalous trichromats** (7 deuteranomalous incl. 1 extreme, 3 protanomalous) + **26 normal trichromat controls** (data from Emery et al. 2017a, same equipment).
- Stimuli: **36 chromaticities** on an isoluminant circle in MacLeod-Boynton space (10° steps, radius 60 contrast units), constant luminance 20 cd/m², 2° square, CRT calibrated, viewed at 200 cm.
- **Multi-axis** (LvsM + SvsLM); CVD classified by anomaloscope (OCULUS Inc.) + Cambridge Colour Test.

### 3.3 Fitting (loss function)
- **Descriptive cosine model**, not mechanistic — fit to each individual's hue-scaling function:
  - Four half-rectified cosines (red, green, blue, yellow) with constraints: blue+yellow span 360°, red+green span 360°; B-Y and R-G peaks 180° apart.
  - Free params per axis (R-G or B-Y): **3 each** = period/width, absolute phase, two amplitudes (red and green amplitudes vary independently; blue and yellow amplitudes fixed at 1 because hue scaling gives only proportional / relative heights). Total ≈ 6 free parameters per observer.
- Loss: **"least-squares fit to the observed responses."**
- **"Compensation gain" estimation is NOT a fit parameter** — it is derived post-hoc from the ratio of (1) measured threshold elevation and (2) reduced R-G amplitude in the hue-scaling fit:
  > "Effective chromatic contrast of 1/6.2 or 16% of the contrast for the NT group. … the mean of the hue-scaling amplitudes was reduced by only 0.80/1.20 or 66% of the NT value, suggesting an average multiplicative gain of 4.1 in the suprathreshold responses."

### 3.4 Validation
- **Train/test split / CV: NOT STATED IN SOURCE.**
- **Within- vs between-subject variability check:** test-retest across two sessions on different days, Spearman ρ AT = 0.69 (p<0.001), NT = 0.41 (p<0.001), confirming the individual-difference structure is real noise.
- **Specificity (NT-null) test: YES.** k-means cluster analysis on fitted parameters classified 10/10 ATs and 25/26 NTs correctly — one misclassified NT had AT-like R-G amplitudes.
- **Cross-measure validation: FAILED.** The fitted R-G amplitudes were *not* correlated with individual threshold losses (red r=−0.18 NS; green r=0.16 NS) nor with anomaloscope match ranges → compensation is real but heterogeneous across observers.

### 3.5 Key quotes
- "We evaluated the degree and form of compensation using a hue-scaling task… The scaling functions were modeled to estimate the relative salience of the red-green to blue-yellow components."
- "3 parameters each for fitting the red-green or blue-yellow responses… the absolute phase also varied to provide a least-squares fit to the observed responses."
- "Neither the red nor green response amplitudes were correlated with the individual AT's threshold losses."
- Citation key: `emery_2021`.

---

## 4. Comparison table

| Dimension | Machado 2009 | Tregillus 2021 | Emery 2021 | **Ours (current Phase 2)** |
|---|---|---|---|---|
| **Data modality** | Behavior (FM100H) | fMRI BOLD + behavior (CRF, thresholds) | Behavior only (hue scaling + thresholds) | **fMRI only** (BOLD amplitudes from C010 GLM) |
| **Subjects** | 17 NT + 13 CVD (Ishihara-classed) | 7 AT + 7 CN + 1 dichromat (anomaloscope) | 10 AT + 26 NT (anomaloscope + CCT) | **HC = 7, CVD = 3** (sub-08 deutan, sub-09 protan, sub-10 near-normal); diagnosis not anomaloscope-confirmed |
| **Stimulus dimensionality** | 85 FM100H caps (1D arrangement) | 2 axes × 4 contrasts (8 conditions) | 36 hues × full 2D circle | **8 equiluminant DKL hues** (1D circle, L*=75) |
| **Free parameters** | **0** (analytical; Δλ set a priori) | **1** (`sc`) per subject on top of fixed CRF baseline | **~6** per observer (3 per axis: width, phase, 2 amplitudes) | **1** (Machado), **2** (R+C, `Δλ` and cortical gain `g`), **2** (2-Component, `β_s` rotation + `β_c` confusion-axis gain) |
| **Loss / objective** | None (closed-form projection) | Per-subject least-squares CRF fit; log(sc) t-test vs reduction null | Per-subject least-squares to cosine model | **L_LOCO composite** = L_vuln + 0.5·L_rank + 0.5·L_noharm + 0.2·L_rdm + 0.1·L_smooth (`LOCO_FILTER_PLAN.md`); per-subject grid 26×51 = 1326 (`loco_distortion_fit.py`) |
| **Selection criterion** | Pre-specified Δλ severity levels (12/16/19 nm) compared visually | sc > 1 (one-sample t-test) | k-means on fitted params; partial gain ratio | **hV4 LOCO Δρ** (descriptive fit per subject, V4-only LOCO policy) |
| **Evaluation set** | Independent NT subgroup viewing simulated caps | Experiment 2 (replication with attention manipulation); S-vs-LM null axis | Test-retest sessions; k-means clustering; threshold/anomaloscope cross-check | hV4 LOCO Δρ + ΔRDM **on the same data used to fit** |
| **Specificity test** | NT baseline run with original caps; geometric covariance comparison | (a) CN group as null, (b) **internal S-axis null**, (c) dichromat control, (d) **reduction null model** | **k-means** correctly classifies 10/10 AT + 25/26 NT | LOO-HC permutation (Job 96664/96600); sub-10 as "near-normal" null **— but HC LOCO FPR = 7/7 (100%)** under label-permutation; baseline ρ ↔ Δρ corr = **−0.894** in HCs (regression-to-mean confound) |
| **Generalization** | Not tested (analytical model) | Experiment-2 attention replication | Test-retest only; no held-out group | LOCO is **within-subject** (leave one color out across 6 runs) but **no held-out subjects, no held-out runs**, no behavioral test set |
| **Alternative null model** | NT-only baseline (informal) | **Explicit reduction model** as null | None explicit; partial-gain framing | **No explicit null model fit**; relies on LOO-HC permutation only |

---

## 5. 적용할 시사점 (PI 피드백 대응 관점)

### 5.1 Train-test split — where we are weakest
1. **None of the three precedents perform held-out-subject CV.** Machado has *no* fit, Tregillus and Emery fit per-subject only. So the absence of leave-one-subject-out in our pipeline is *not* a deviation from precedent.
2. **But Tregillus has a true held-out task** (Exp 2 attention replication). **We do not.** The single closest analogue we have is the **V4-only LOCO policy + LOO-HC permutation**, but both still draw from the same 6-run scan session. PI's likely critique: "your hV4 LOCO Δρ + ΔRDM are evaluated on the same data the loss is computed on."
3. **Emery has test-retest** on separate days. **We do not.** Re-running the C010 paradigm on a second day for at least one CVD subject would directly answer the "is the fit reliable?" critique.

### 5.2 Generalizability ablations to consider (priority-ordered)
1. **Leave-one-run-out (LORO) cone-shift fit, then evaluate on the held-out run's LOCO Δρ.** This is the strongest cheap test — uses existing data, mirrors Tregillus's reduction-vs-amplification logic by reserving one run for evaluation.
2. **Leave-one-color-out at fit time** (currently LOCO is used as *loss*, not as *split*) — i.e., fit Δλ on 7 colors, evaluate on the 8th in a different metric (ΔRDM-on-held-out-color). This decouples the "same-data-fit-and-evaluate" issue.
3. **Held-out-subject prediction.** For each CVD subject, fit the model using a *group prior* derived only from the other 2 CVD subjects + HCs, then check if the predicted Δλ ordering matches the held-out subject's behavioral severity. Caveat: n=3 CVD makes this very weak.
4. **External-task validation.** None of our subjects have anomaloscope, FM100H, or hue-scaling data. **Adding even Cambridge Colour Test or FM100H for the 3 CVD subjects would let us follow Emery's correlation-with-threshold-loss design** (and confirm whether sub-10 is genuinely near-normal vs falsely classified).

### 5.3 행동 + 신경 비교 설계 — 선례
- **Tregillus is the closest precedent**: fMRI BOLD CRFs fit per subject + behavioral contrast thresholds as the t (reduction) parameter that's fixed from psychophysics. **Behavior constrains the null; fMRI tests the deviation.** This is a clean template we could adopt: use a behavioral hue-discrimination JND from the 3 CVD subjects to *fix* the no-compensation prediction, then test whether the neural fit requires additional cortical gain.
- **Emery + Boehm** (already in notebook) explicitly link suprathreshold hue scaling to threshold contrast detection — same logic, different data.
- **In our project, the JND data are in `phase3_behavioral_analysis` / planning stage.** The literature precedent strongly supports finishing that arm before claiming compensation specificity.

### 5.4 Specificity — explicit risk
Our HC LOCO FPR = 7/7 (100%) under label-permutation null and Δρ−baseline_ρ correlation of −0.894 (CLAUDE memory, 2026-04-11) means we **fail the same specificity test that Tregillus passed with an S-axis null**. PI is likely to flag this directly. Two precedent-aligned mitigations:
- **Add an internal null axis** analogous to Tregillus's S-axis. Our 8-hue DKL ring does not have an a priori CVD-invariant subset, but a magenta/blue-cyan subset (least L–M loading) could function as a within-subject control.
- **Adopt Tregillus's reduction-vs-amplification *null-model* test** instead of permutation: fit a zero-shift, zero-gain prediction from Machado biology, then test whether the data require a non-zero free parameter.

### 5.5 Loss-function transparency
Our **L_LOCO composite (5 terms, weights 1 / 0.5 / 0.5 / 0.2 / 0.1)** is far more complex than any of the three precedents (which use plain least-squares or t-test on a 1-D scalar). This is defensible *only* if each term is justified and the weights are pre-registered. Recommend either:
- (a) ablate each term in the composite and report which terms are load-bearing for sub-08/09 detection and the sub-10 null, or
- (b) reformulate the headline result around a single dominant term (likely L_vuln + L_rank) and report the others as robustness checks.

---

## 6. Items needing additional search (not in notebook)

- **Machado 2009 supplementary materials** (transformation matrices for incorporating the model into systems) — referenced in the paper but not extracted from the NotebookLM source; would need direct PDF/supplement if the exact Γ-matrix anomalous-trichromat coefficients are required.
- **Robinson 2022/2023 (Nonlinear cortical encoding of color)** is in the notebook and is directly relevant as a *nonlinear* cortical compensation alternative to the linear R+C / 2-Component formulations — worth a follow-up extraction if PI questions why we did not adopt a nonlinear cortical model.
- **Basim 2025 (J Vis)** is in the notebook and is the most recent CVD compensation paper — worth checking whether they perform held-out-subject CV (would be the first precedent if they do).
- **Tregillus supplementary** for the actual CRF parameter values per subject and the exact ROI definition — could be needed if we want to cross-check whether our K=3 hV4 SRM is comparable to their V3v ROI granularity.

---

## 7. Provenance

- All four-question extractions executed against single-source-restricted NotebookLM queries (`source_ids` parameter) on notebook `fa13d441-21f2-40a0-8170-8cc8eb49cc7b`, conversation `2bd060b9-d9b1-42c4-bfa6-0b3ed4af220d`, 2026-05-19.
- "Ours (current)" entries cross-referenced against `LOCO_FILTER_PLAN.md`, `CLAUDE.md` (project root), and the auto-memory entry "HC Specificity + Baseline Δρ Diagnostic (2026-04-11)" / "LOCO-Primary Filter Design (updated 2026-04-09)".
- No web search or fabrication used; every claim in §1–§3 is either a direct NotebookLM-returned quote or marked "NOT STATED IN SOURCE."
