# OHBM 2026 Abstract — v8 (post-Phase 2/3 analyses)

## Title (100 characters max)

Hue Interpolation, Not Discrimination, Is Disrupted in Color Vision Deficiency: An fMRI Study

*Character count: 92*

---

## Authors and Affiliations

Jinil Kim¹, Minkue Cho¹, Jungwoo Seo¹, Jiook Cha¹*

¹Seoul National University, Seoul, South Korea

*Corresponding author

---

## Introduction (2,000 characters max)

Color vision deficiency (CVD) affects ~8% of males and arises from cone-pigment shifts that quantitatively reweight — rather than abolish — cortical color input. Behavioral and fMRI evidence shows that the cortex actively compensates for this reweighting¹, making CVD a paradigmatic case of a *structurally distorted* — not absent — neural representation. This distortion is both a testbed for theories of cortical color computation and a candidate target for individualized corrective filters; both purposes require knowing how the cortical hue space is reshaped *in each subject*. Yet existing fMRI work on CVD has not reached this resolution: studies report group-mean activation or univariate contrasts across V1–hV4¹, leaving open whether the deficit reflects amplitude loss or geometric reshape. Compounding this, "color decoding" indexes two distinct neural properties — the ability to **classify** a presented hue into a learned category, and the ability to **interpolate** the continuous hue manifold to colors never seen in training — and these have rarely been dissociated. Interpolation emerges only above primary visual cortex: Brouwer & Heeger³ localized novel-hue reconstruction to V4/VO1, and Bannert & Bartels² identify hV4 as a perceptual hub for color perception. Here, we dissociate the two properties in 7 controls and 3 CVD individuals (one deutan, one protan, one mild deutan) using **the same forward-encoding model**³ under paired leave-one-run-out (LORO; within-color generalization) and leave-one-color-out (LOCO; across-color interpolation) cross-validation on the same voxels — so that any LORO-vs-LOCO difference indexes the operation, not the model class. A signal-loss account predicts both measures reduced; a geometric-distortion account predicts LORO preserved with LOCO selectively impaired at hV4. Distinguishing them determines whether CVD color geometry is warped or broken — and therefore whether stimulus-space correction has a target to act on.

*Character count: ~1,975*

---

## Methods (4,000 characters max)

Under an IRB-approved protocol, we recruited 10 participants: 7 healthy controls (HC; sub-01 to sub-07; 4M/3F, 23.1±2.4 yrs) and 3 individuals with CVD (sub-08 deuteranope, sub-09 protanomalous, sub-10 mild deuteranope; 2M/1F, 23.3±2.1 yrs). CVD diagnosis was confirmed using Ishihara plates. Functional MRI data were acquired on a 3T Siemens MAGNETOM Trio scanner: T1-MPRAGE (1×1×1 mm³) and T2*-weighted EPI (TR=1500 ms, TE=30 ms, voxel=2×2×2 mm³, 24 oblique slices perpendicular to the calcarine sulcus).

Participants viewed 8 isoluminant colors evenly spaced around the CIE L*a*b* circle (L*=54, radius=38, 45° spacing) plus a neutral gray. Colored circular backgrounds (1.5 s) were presented with 3–6 s ISI. To control for strategic processing, participants performed a rapid serial visual presentation (RSVP) attention task at fixation. Each participant completed 6 runs of ~7 min (48 trials/color total).

Preprocessing was performed using fMRIPrep v20.2.0 (field-map correction, motion correction, slice-timing correction, MNI152 2 mm normalization). Bilateral V1, V2, V3, hV4 ROIs were defined using the Wang et al. probabilistic atlas⁴. We estimated voxel-wise GLM betas for each color and selected informative voxels using nested ANOVA F-tests (k=1–200).

To enable cross-run comparison, voxel patterns were aligned to a within-subject Procrustes reference (orthogonal transform, run-0 anchor). The same 6-channel half-wave rectified squared sinusoidal forward encoding model³ was then evaluated under two complementary cross-validation schemes on the *same* aligned voxels: (i) **LORO** — 6-fold leave-one-run-out cross-validation (all 8 colors present in training; 8-way nearest-template matching, chance=12.5%); (ii) **LOCO** — 8-fold leave-one-color-out cross-validation predicting the held-out hue via correlation against a 360° basis set (circular MAE, chance=90°). Holding the readout fixed isolates the contrast of *within-color generalization* (LORO) vs. *across-color interpolation* (LOCO). Channel weights W were estimated on pooled training samples and ridge-regularized, with λ selected by nested 5-fold leave-one-run-out cross-validation within each fold. To verify that each ROI carried interpolable hue structure independently of the group contrast, we compared observed LOCO MAE against a 1000-iteration label-permutation null computed within HC.

Group comparisons used Welch's two-tailed t-test and one-tailed exact-enumeration permutation (C(10,3)=120 unique group assignments) under a directional dissociation hypothesis pre-specified from prior hV4 hue-representation work (Bannert & Bartels, 2018; Brouwer & Heeger, 2009): CVD worse than HC for LOCO, CVD not worse for LORO. Individual CVD subjects were tested against the HC distribution using Crawford & Howell's modified t-test⁵. Effect sizes are reported as Hedges' g with the small-sample correction. To validate that decoding reflects genuine color-tuned signals, we further computed individual SRM-based representational disparity (HC-only shared response model with ROI-specific dimensionality, k=4 for V1/V2 and k=3 for V3/hV4; cross-validated geometry distance vs HC reference).

*Character count: ~3,172*

---

## Results (4,000 characters max)

### Classification is preserved across the visual hierarchy

Under matched forward-encoding readout, LORO classification accuracy showed no significant CVD decrement at any ROI: V1 HC=0.58±0.07 vs CVD=0.56±0.01 (g=0.37, perm p=.342); V2 HC=0.61±0.11 vs CVD=0.50±0.08 (g=0.92, p=.108); V3 HC=0.57±0.11 vs CVD=0.52±0.17 (g=0.38, p=.300); hV4 HC=0.49±0.11 vs CVD=0.44±0.11 (g=0.43, p=.250). All three CVD subjects fell within the HC distribution at every ROI; the largest numerical decrement (V2) did not reach significance under exact-enumeration permutation. Within-color generalization is therefore preserved within the HC envelope across the hierarchy — no ROI showed the substantial reduction a signal-loss account would predict.

### Interpolation is selectively impaired at hV4

Before contrasting groups, we asked within HC alone whether each ROI carried interpolable hue structure by comparing observed LOCO MAE to a 1000-iteration label-permutation null. Only **hV4** exceeded its null (HC observed 69.4° vs null mean 78.0°, paired one-tailed t p=.026); V1, V2, and V3 LOCO did not differ from null (all p > .35) — consistent with Brouwer & Heeger's³ original observation that V4/VO1, not V1, support novel-hue reconstruction. The CVD impairment therefore tests dissociation specifically at the stage where interpolation is well-defined.

At hV4, LOCO MAE was substantially elevated in CVD — HC 69.4±9.4° vs CVD 87.4±10.2° — yielding **g=1.69, exact-permutation p=.017** (Welch p=.067). The effect size is ~4× the LORO decrement at the same ROI (g=0.43), establishing the dissociation under matched readout. V2 showed a weaker pattern in the same direction (HC 80.0±16.7° vs CVD 98.5±20.5°, g=0.94, p=.075); V1 and V3 did not differ (p=.242, p=.633). Individually, sub-09 (protan) showed the most severe interpolation deficit (V1 104°, V2 106°, hV4 98° — three of four ROIs at or above chance), whereas sub-08 (deutan) achieved the best single-subject V1 LOCO (52°, individual permutation p=.035), suggesting a hue space that is *warped but locally continuous*. sub-10 (mild deutan) showed a mixed profile at intermediate levels.

### Convergent geometric evidence at the individual level

Beyond forward-encoding interpolation, an independent geometric measure converged on the same dissociation. Crawford & Howell tests on SRM-projected representational disparity (HC shared response space, ROI-specific k=3–4) yielded individual-level support: **sub-09 V1 z=5.17, p=.003**; sub-08 V2 z=2.94, p=.033; trends at sub-09 hV4 (z=2.47, p=.061) and sub-08 V3 (z=2.34, p=.071). The mild deuteranope sub-10 was null at every ROI (all p>.14), serving as an internal specificity control. The dissociation pattern is thus reproduced across two independent geometry measures (forward-encoding LOCO and SRM disparity), and is *absent* from the LORO classification measure under the same readout — consistent with a single coherent account in which CVD color codes are geometrically warped rather than reduced in amplitude or categorical separability.

*Character count: ~3,046*

---

## Conclusions (4,000 characters max)

Using the same forward-encoding model under two cross-validation schemes, we provide a direct dissociation between **within-color classification** and **across-color interpolation** in CVD visual cortex. CVD subjects classify the eight isoluminant colors within the healthy-control range at every visual area examined (V1 through hV4), with no statistically significant decrement (largest g=0.92 at V2, p=.108). The *continuous* hue manifold — the ability to predict an unseen color from learned neighbors — is by contrast significantly compromised, with the deficit concentrated at **hV4** (g=1.69, p=.017), a perceptual hub for color perception². The effect-size ratio (interpolation vs. classification at hV4 ≈ 4:1) anchors the dissociation in operation, not model class. This pattern is corroborated by convergent SRM-based individual-level geometry tests in V1/V2 (sub-09 protan p=.003, sub-08 deutan p=.033). Together these findings reframe CVD neural pathology from *signal loss* to *geometric distortion of perceptual color space* — the hue circle in CVD is warped, not broken — defining a target on which stimulus-space correction can, in principle, act.

**Future work.** Because the deficit appears to be geometric rather than amplitude-based, it is in principle invertible: a stimulus-space "inverse filter" that pre-warps colors prior to viewing could compensate for individual hue-space distortion. Pilot work fitting subject-specific cortical-and-retinal distortion models (cone-shift plus opponent-axis rotation) has recovered candidate filter parameters for both deuteranopic and protanopic participants, and behavioral and fMRI repetition-suppression tests of these filters are planned, offering a path from descriptive neuroimaging to translational color-vision compensation.

*Character count: ~1,794*

---

## References (Maximum 5, AMA style)

1. Tregillus KEM, Isherwood ZJ, Vanston JE, et al. Color compensation in anomalous trichromats assessed with fMRI. *Curr Biol.* 2021;31(5):936-942.e4. doi:10.1016/j.cub.2020.11.039

2. Bannert MM, Bartels A. Human V4 activity patterns predict behavioral performance in imagery of object color. *J Neurosci.* 2018;38(15):3657-3668. doi:10.1523/JNEUROSCI.2307-17.2018

3. Brouwer GJ, Heeger DJ. Decoding and reconstructing color from responses in human visual cortex. *J Neurosci.* 2009;29(44):13992-14003. doi:10.1523/JNEUROSCI.3577-09.2009

4. Wang L, Mruczek RE, Arcaro MJ, Kastner S. Probabilistic maps of visual topography in human cortex. *Cereb Cortex.* 2015;25(10):3911-3931. doi:10.1093/cercor/bhu277

5. Crawford JR, Howell DC. Comparing an individual's test score against norms derived from small samples. *Clin Neuropsychol.* 1998;12(4):482-486. doi:10.1076/clin.12.4.482.7241

---

## Figure captions (for poster — abstract may use shorter)

**Figure 1.** Experimental design, dual-CV pipeline (same forward encoder), and reconstruction examples.
**(A)** Eight DKL-defined isoluminant hues evenly spaced around the CIE L*a*b* circle (L*=54), plus neutral gray. **(B)** Shared preprocessing — fMRIPrep, Wang atlas ROIs (V1, V2, V3, hV4), single-trial GLM betas, within-subject Procrustes alignment — feeding the same 6-channel forward encoding model under two cross-validation schemes: LORO (within-color generalization; tests classification) and LOCO (across-color interpolation; tests prediction of an unseen hue). **(C)** LOCO reconstruction comparing HC sub-06 (hV4, MAE 62°) and CVD sub-09 (V1, MAE 103° — near chance); interpolation breaks down most severely for the protanomalous subject. **(D)** Effect-size summary across schemes at hV4: |g|=0.43 for LORO vs |g|=1.69 for LOCO — same readout, dissociation arises from the cross-validation operation.

**Figure 2.** Within-color generalization preserved (LORO) vs across-color interpolation impaired (LOCO) under matched forward-encoding readout.
**(A)** LORO classification accuracy by ROI and group; no ROI reaches significance for "CVD < HC" (all permutation p ≥ .10); CVD subjects fall within the HC range everywhere. **(B)** LOCO MAE by ROI and group; hV4 shows a significant CVD deficit (p=.017, g=1.69), V2 a trend (p=.075). **(C)** HC-only label-permutation null per ROI; only hV4 LOCO exceeds null in HC (p=.026), establishing it as the locus where interpolation is well-defined. **(D)** Individual SRM-based representational disparity (Crawford & Howell z scores vs HC reference) per ROI; sub-09 V1 p=.003 and sub-08 V2 p=.033 reach significance; sub-10 (mild deutan) is null everywhere, serving as a specificity control.

---

## Notes for revision (internal — remove before submission)

- **Title**: 92-char alternative adopted ("Hue Interpolation, Not Discrimination, …").
- **N**: 10 total, 7 HC + 3 CVD (corrected from v7's N=9).
- **CVD screening**: Ishihara only (Cambridge Colour Test was not administered — corrected from earlier v8 draft).
- **Decoder (LORO and LOCO unified)**: ForwardEncoding (FE-6) with pooled W + ridge λ via nested LORO 5-fold, sourced from `analysis/phase3_decoder_comparing/results/{loco,loro}/procrustes/`. Same model under two CV schemes — dissociation indexes operation, not model class. Group prior (W_combined = λ·W_ind + (1−λ)·W_HC) was NOT used here — that branch belongs to `future_phase2_filter_optimization`, not this abstract.
- **HC LOCO label-permutation null** (10 subj × 1000 perms, FE-6, per-ROI paired-t one-tailed): V1 p=.354, V2 p=.635, V3 p=.442, **hV4 p=.026**. Only hV4 exceeds null → motivates hV4 as the locus where group dissociation is meaningful. Verified against server `phase2_decoder_comparing/model_comparison_validation/results/loco/procrustes/` (identical files; phase3 is the local rename).
- **Model unification rationale**: v8 originally reported LORO with LDA (g=−1.29 at hV4, CVD>HC). Switched to forward-encoding LORO so that LORO/LOCO contrast varies only the CV scheme. Cost: V4 LORO under FE shows CVD numerically lower (g=+0.43, NS) instead of CVD>HC. Benefit: dissociation interpretable as operation difference, not model artifact. Effect-size ratio at hV4 ≈ 4:1 (LOCO g=1.69 / LORO g=0.43) anchors the dissociation.
- **1-tailed exact permutation justification**: C(10,3)=120 unique group assignments → exact enumeration. Directional hypothesis ("CVD worse for LOCO, not worse for LORO") pre-specified from Bannert & Bartels 2018 + Brouwer & Heeger 2009 hV4 framing. Both 1-tailed perm and 2-tailed Welch reported.
- **SRM K**: ROI-specific (k=4 for V1/V2, k=3 for V3/hV4) per `MEMORY.md > SRM Configuration` (hV4 4→3 update on 2026-02-18). Earlier "k=4" was a simplification — corrected.
- **SRM individual numbers**: sub-09 V1 p=.003, sub-08 V2 p=.033 from `figures/v8/Figure_2_v8_numbers.json`. MEMORY.md still lists older p=.007 / p=.040 — update separately.
- **hV4 framing**: "perceptual hub for color perception" per Bannert & Bartels 2018 Significance Statement (verified via NotebookLM 2026-05-21). "Perceptual color binding" was inaccurate and was removed.
- **Filter / Phase 2 work** appears in Conclusions only ("Future work" paragraph), per OHBM scope decision.
- **Current figure files**: `docs/OHBM_abstract/figures/v8/Figure_{1,2}_v8_1.{pdf,png}` (FE-unified, post-LDA→FE swap). Generated by `docs/OHBM_abstract/v8_figures/make_fig{1,2}_v8_1.py`. Numbers in `Figure_{1,2}_v8_1_numbers.json`. Old `Figure_{1,2}_v8.{pdf,png}` (LDA-based) kept as reference but superseded.
- **Fig 1 v8.1**: 3-panel (A stimulus / B pipeline with FE encoder + dual CV schemes / C LOCO reconstruction example). Dropped LDA-based LORO illustration panel.
- **Fig 2 v8.1**: 4-panel (A LORO FE accuracy with chance line + individual dots / B LOCO MAE / C HC observed vs label-perm null per ROI — only hV4 exceeds null p=.026 / D SRM disparity individual).
- All character counts are approximate; verify before submission with the OHBM portal's counter.
