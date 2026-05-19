# OHBM 2026 Abstract — v8 (post-Phase 2/3 analyses)

## Title (100 characters max)

Color Discrimination Preserved but Hue Interpolation Disrupted in Color Vision Deficiency: An fMRI Study

*Character count: ~107 — TRIM CANDIDATE below.*

**Alternative (≤100):**
"Hue Interpolation, Not Discrimination, Is Disrupted in Color Vision Deficiency: An fMRI Study"

*Character count: 92*

---

## Authors and Affiliations

Jinil Kim¹, Minkue Cho¹, Jungwoo Seo¹, Jiook Cha¹*

¹Seoul National University, Seoul, South Korea

*Corresponding author

---

## Introduction (2,000 characters max)

Individuals with color vision deficiency (CVD) show profound impairments in red-green color discrimination, yet whether these deficits reflect a *loss of color signals* in visual cortex or a *geometric distortion of neural color space* remains unresolved. Prior fMRI work has yielded mixed evidence: some report reduced discriminability in early visual cortex¹, while others suggest preserved categorical responses with altered higher-order representations². A key conceptual issue is that "color decoding" can index two distinct neural properties — the ability to **classify** a presented color into a learned category, and the ability to **interpolate** a continuous hue manifold to colors never seen in training. These two abilities have rarely been dissociated. Here, we test whether CVD selectively impairs one but not the other across the visual hierarchy. We applied two complementary cross-validation schemes to fMRI activity patterns evoked by eight isoluminant hues: leave-one-run-out (LORO) classification (8-way LDA, all colors present in training) and leave-one-color-out (LOCO) interpolation (forward encoding³ predicting the held-out hue). If CVD reflects color-signal loss, both measures should be reduced. If CVD reflects geometric distortion, LORO should be preserved while LOCO should fail — most prominently at hV4, the area implicated in perceptual color binding.

*Character count: ~1,560*

---

## Methods (4,000 characters max)

Under an IRB-approved protocol, we recruited 10 participants: 7 healthy controls (HC; sub-01 to sub-07; 4M/3F, 23.1±2.4 yrs) and 3 individuals with CVD (sub-08 deuteranope, sub-09 protanomalous, sub-10 mild deuteranope; 2M/1F, 23.3±2.1 yrs). CVD diagnosis was confirmed using Ishihara plates and the Cambridge Colour Test. Functional MRI data were acquired on a 3T Siemens MAGNETOM Trio scanner: T1-MPRAGE (1×1×1 mm³) and T2*-weighted EPI (TR=1500 ms, TE=30 ms, voxel=2×2×2 mm³, 24 oblique slices perpendicular to the calcarine sulcus).

Participants viewed 8 isoluminant colors evenly spaced around the CIE L*a*b* circle (L*=54, radius=38, 45° spacing) plus a neutral gray. Colored circular backgrounds (1.5 s) were presented with 3–6 s ISI. To control for strategic processing, participants performed a rapid serial visual presentation (RSVP) attention task at fixation. Each participant completed 6 runs of ~7 min (48 trials/color total).

Preprocessing was performed using fMRIPrep v20.2.0 (field-map correction, motion correction, slice-timing correction, MNI152 2 mm normalization). Bilateral V1, V2, V3, hV4 ROIs were defined using the Wang et al. probabilistic atlas⁴. We estimated voxel-wise GLM betas for each color and selected informative voxels using nested ANOVA F-tests (k=1–200).

To enable cross-run comparison, voxel patterns were aligned to a within-subject Procrustes reference (orthogonal transform, run-0 anchor). Two cross-validated decoding analyses were then applied on the *same* aligned voxels: (i) **LORO classification** — 6-fold leave-one-run-out 8-way LDA, chance=12.5%; (ii) **LOCO interpolation** — 8-fold leave-one-color-out forward encoding model with 6 half-wave rectified squared sinusoidal channels³, predicting the held-out hue via correlation-based template matching against a 360° basis set (circular MAE, chance=90°). Channel weight matrices for LOCO were regularized with a leakage-free group prior W_combined = λ·W_individual + (1−λ)·W_HC-mean, with λ selected via nested LORO within each fold and the held-out color excluded from group W.

Group comparisons used Welch's two-tailed t-test and exact-enumeration one-tailed permutation under the directional dissociation hypothesis (CVD worse than HC for LOCO; CVD not worse for LORO). Individual CVD subjects were tested against the HC distribution using Crawford & Howell's modified t-test⁵. Effect sizes are reported as Hedges' g with the small-sample correction. To validate that decoding reflects genuine color-tuned signals, we further computed individual SRM-based representational disparity (HC-only k=4 shared response model; cross-validated geometry distance vs HC reference).

*Character count: ~3,250*

---

## Results (4,000 characters max)

### Classification is preserved across the visual hierarchy

LORO classification accuracy did not differ between groups in the direction predicted by signal-loss accounts. Across V1–hV4, CVD LDA accuracy met or exceeded HC accuracy: V1 HC=0.74±0.06 vs CVD=0.81±0.09 (g=−0.76, perm p=.900); V2 HC=0.74±0.06 vs CVD=0.83±0.12 (g=−1.17, p=.958); V3 HC=0.76±0.08 vs CVD=0.77±0.11 (g=−0.15, p=.533); hV4 HC=0.71±0.08 vs CVD=0.82±0.05 (g=−1.29, Welch p=.049 two-tailed; CVD numerically *exceeds* HC). All three CVD subjects fell within the HC distribution at every ROI. Categorical color identity is therefore intact in CVD — and the hV4 result rules out a general signal-loss account of any subsequent deficit at that area.

### Interpolation is selectively impaired, with hV4 as primary locus

The picture reverses when the task requires predicting unseen hues from continuous color structure. LOCO mean absolute error was substantially elevated in CVD at hV4 — HC 69.4±9.4° vs CVD 87.4±10.2° — yielding **g=1.69, exact-permutation p=.017** (Welch p=.067). V2 showed a similar but weaker pattern (HC 80.0±16.7° vs CVD 98.5±20.5°, g=0.94, p=.075). V1 and V3 did not differ (p=.242, p=.633). Individually, sub-09 (protan) showed the most severe interpolation deficit (V1 104°, V2 106°, hV4 98° — three of four ROIs at or above chance), whereas sub-08 (deutan) achieved the best single-subject V1 LOCO (52°, individual permutation p=.035), suggesting a hue space that is *warped but locally continuous*. sub-10 (mild deutan) showed a mixed profile at intermediate levels.

### Convergent geometric evidence at the individual level

Crawford & Howell tests on SRM-projected representational disparity (HC k=4 shared response space) yielded convergent individual-level support: **sub-09 V1 z=5.17, p=.003**; sub-08 V2 z=2.94, p=.033; trends at sub-09 hV4 (z=2.47, p=.061) and sub-08 V3 (z=2.34, p=.071). The mild deuteranope sub-10 was null at every ROI (all p>.14), serving as an internal specificity control. The dissociation pattern is thus reproduced across two independent geometry measures (forward-encoding LOCO and SRM disparity), and is *absent* from the categorical LDA measure — consistent with a single coherent account in which CVD color codes are geometrically warped rather than reduced in amplitude or categorical separability.

*Character count: ~2,700*

---

## Conclusions (4,000 characters max)

We provide the first direct dissociation between **color classification** and **hue interpolation** in CVD visual cortex. At every visual area examined (V1 through hV4), CVD subjects classify the eight isoluminant colors as accurately as healthy controls — and at hV4 they numerically *exceed* control performance. However, the *continuous* hue manifold — the ability to predict an unseen color from learned neighbors — is significantly compromised, with the deficit concentrated at **hV4** (g=1.69, p=.017), the area most implicated in perceptual color binding. This pattern is corroborated by convergent SRM-based individual-level geometry tests in V1/V2 (sub-09 protan p=.003, sub-08 deutan p=.033). Together these findings reframe CVD neural pathology from *signal loss* to *geometric distortion of perceptual color space* — the hue circle in CVD is warped, not broken.

**Future work.** Because the deficit appears to be geometric rather than amplitude-based, it is in principle invertible: a stimulus-space "inverse filter" that pre-warps colors prior to viewing could compensate for individual hue-space distortion. Pilot work fitting subject-specific cortical-and-retinal distortion models (cone-shift plus opponent-axis rotation) has recovered candidate filter parameters for both deuteranopic and protanopic participants, and behavioral and fMRI repetition-suppression tests of these filters are planned, offering a path from descriptive neuroimaging to translational color-vision compensation.

*Character count: ~1,560*

---

## References (Maximum 5, AMA style)

1. Tregillus KEM, Isherwood ZJ, Vanston JE, et al. Color compensation in anomalous trichromats assessed with fMRI. *Curr Biol.* 2021;31(5):936-942.e4. doi:10.1016/j.cub.2020.11.039

2. Bannert MM, Bartels A. Human V4 activity patterns predict behavioral performance in imagery of object color. *J Neurosci.* 2018;38(15):3657-3668. doi:10.1523/JNEUROSCI.2307-17.2018

3. Brouwer GJ, Heeger DJ. Decoding and reconstructing color from responses in human visual cortex. *J Neurosci.* 2009;29(44):13992-14003. doi:10.1523/JNEUROSCI.3577-09.2009

4. Wang L, Mruczek RE, Arcaro MJ, Kastner S. Probabilistic maps of visual topography in human cortex. *Cereb Cortex.* 2015;25(10):3911-3931. doi:10.1093/cercor/bhu277

5. Crawford JR, Howell DC. Comparing an individual's test score against norms derived from small samples. *Clin Neuropsychol.* 1998;12(4):482-486. doi:10.1076/clin.12.4.482.7241

---

## Figure captions (for poster — abstract may use shorter)

**Figure 1.** Experimental design, dual-decoder pipeline, and reconstruction examples.
**(A)** Eight DKL-defined isoluminant hues evenly spaced around the CIE L*a*b* circle (L*=54), plus neutral gray. **(B)** Shared preprocessing — fMRIPrep, Wang atlas ROIs (V1, V2, V3, hV4), single-trial GLM betas, within-subject Procrustes alignment — feeding two cross-validation branches: LORO 8-way LDA classification (tests discrimination) and LOCO forward-encoding interpolation (tests prediction of an unseen hue). **(C)** LORO reconstruction at hV4 for one HC (sub-06) and one CVD (sub-08) — both achieve ~81% classification accuracy and ~16° MAE; categorical discrimination is intact. **(D)** LOCO reconstruction comparing HC sub-06 (hV4, MAE 62°) and CVD sub-09 (V1, MAE 103° — near chance); interpolation breaks down most severely for the protanomalous subject.

**Figure 2.** Discrimination preserved (LORO) vs interpolation impaired (LOCO).
**(A)** LORO LDA accuracy by ROI and group; no ROI shows reduced CVD performance (all permutation p > .5 against the "CVD < HC" hypothesis); at hV4, CVD numerically exceeds HC. **(B)** LOCO MAE by ROI and group; hV4 shows a robust CVD deficit (p=.017, g=1.69), V2 a trend (p=.075). **(C)** Individual hV4 LOCO MAE; all three CVD subjects fall at or above the HC range, with sub-09 protan above chance. **(D)** Individual SRM-based representational disparity (Crawford & Howell z scores vs HC reference) per ROI; sub-09 V1 p=.003 and sub-08 V2 p=.033 reach significance; sub-10 (mild deutan) is null everywhere, serving as a specificity control.

---

## Notes for revision (internal — remove before submission)

- **Title trim**: pick one of the two title variants; current top option exceeds 100 chars.
- **N**: 10 total, 7 HC + 3 CVD (corrected from v7's N=9).
- **hV4 LORO surprise** (g=−1.29, CVD>HC): kept as positive evidence against signal-loss; framed as one-tail "CVD not worse than HC" in the abstract.
- **SRM numbers updated** from memory snapshots: sub-09 V1 p=.003 (was .007), sub-08 V2 p=.033 (was .040). Numbers above are from `figures/v8/Figure_2_v8_numbers.json` and are the canonical values.
- **Filter / Phase 2 work** appears in Conclusions only ("Future work" paragraph), per OHBM scope decision.
- Figure files: `docs/OHBM_abstract/figures/v8/Figure_{1,2}_v8.{pdf,png}`. Regeneration scripts at `docs/OHBM_abstract/v8_figures/`.
- All character counts are approximate; verify before submission with the OHBM portal's counter.
