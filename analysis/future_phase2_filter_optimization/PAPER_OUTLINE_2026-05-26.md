# Paper Outline (2026-05-26) — Subject-Specific Cortical Compensation Models in CVD

Draft outline for a 2-CVD fMRI methods/findings paper based on Phase A → D pipeline (see `PIPELINE_UPDATED_0524.md`).

---

## 1. Title (working)

**"Subject-Specific Forward Models of Cortical Color Compensation in Color-Vision Deficiency: A Cross-Subject Resample Approach to Identifying Per-Subject Inverse Filters"**

Alternative shorter version: *"Inferring Cortical Compensation in Color-Vision Deficiency: a Per-Subject Forward-Model + Inverse-Filter Framework"*

Working scope tag: *2 CVD case findings + methodological proposal*. Not framed as population study.

---

## 2. Contribution claim

**One-sentence**: We develop a per-subject, neural-data-driven forward-model framework that identifies whether each CVD individual's color perception is best explained by retinal cone-shift × cortical-gain (R+C, 1-DOF) or cortical opponent-rotation (2-Component, 2-DOF), then derive each subject's inverse-filter pre-image — applied here to one deutan and one protan participant.

**Three refinements** (working draft; primary candidates pending Pipeline 3 E2+E3 completion):

- **Novel (method)**: Cross-subject 5-train/2-test HC subset resample for low-DOF physical parameter inference. NotebookLM literature query (Task #53) confirmed no direct precedent — comparable literature (Brouwer & Heeger 2009; van Bergen & Jehee 2015/2017; Benson & Winawer 2018; Sadil 2022) uses within-subject run-level CV.
- **Finding (sub-08 deutan)**: *Atypical yellow-region deficit pattern* (orange-yellow z²=16, yellow-green z²=17 under R+C vs 4.6/0.3 under 2-comp). The canonical 1-DOF R+C cannot represent this pattern — Machado shape is constrained to the red-green axis. Sub-08's primary mechanism is therefore 2-Component cortical opponent-rotation; the specific (β_s, β_c) point estimate is being finalized under Pipeline 3 multi-axis OOS criteria (Layer A+B).
- **Method refinement**: PCA-aligned RDM atom achieves 2× cleaner real-vs-null separation than voxel-RDM. The earlier z-score composite was found to equalize atom information density, motivating Pipeline 3's OOS-based architecture (P1 fit/eval atom separation; E1 behavioral pair-OOS; E2 SRM disparity reduction; E3 multi-point sim).

**Sub-09 protan (case 2)**: R+C over-compensation candidate (Pipeline 2 g=2.60 Δλ=10 nm DPS_lit; Pipeline 3 E1 top g=3.00 Δλ=3 nm Boehm_low). Both lie in the over-comp ceiling region. Phase 3 testable (forward 21° RMS at g=2.60; final selection pending E2+E3).

---

## 3. And-But-Therefore framing

(per `~/.claude/writing/academic_writing_rules.md` §1)

- **And** (background): Cortical compensation in color-vision deficiency is well-documented (Boehm 2014, 2020; Tregillus 2021; Emery 2021), and inverse problems for individualized stimulus-space filters are increasingly tractable (Brouwer & Heeger 2009/2013; Kay 2008; van Bergen & Jehee 2015/2017; Sadil 2022).
- **But** existing population-level cone-shift models (Machado 2009; DeMarco 1992) and aggregate cortical-gain estimates do not commit to a per-subject *mechanism class* (retinal vs cortical), and standard within-subject CV cannot discriminate between same-fit mechanisms with different physical generators. Specifically, a single CVD subject may show behavior the canonical 1-DOF R+C model fundamentally cannot fit because Machado's shape constrains distortion to the red-green axis, while a 2-DOF cortical opponent-rotation model fits such behavior but is non-identifiable at typical HC pool sizes (N=7).
- **Therefore** we develop a per-subject pipeline that (a) screens model–loss combinations by HC-pool resample inclusion, (b) sweeps composite weights on a Dirichlet simplex, (c) validates fits with multi-point simulation under known GT, (d) uses both z-score and explicit raw-weight composites to expose atom-equalization artifacts, and (e) reports each subject's identified mechanism alongside an explicit caveat when statistical identifiability and behavioral fit dissociate.

---

## 4. Section outline

### 4.1 Abstract (~250 words)

Frame: 2 CVD individuals (one deutan, one protan) + 7 HC controls. Pipeline: Phase A precondition → Phase B inclusion via HC resample → Phase C weight sweep → Phase D pre-image. Key findings: sub-09 protan = single robust R+C over-compensation (g=2.60); sub-08 deutan = 2-Component cortical opponent-rotation (β_s=38, β_c=−44) reflecting an atypical yellow-region deficit that the canonical 1-DOF R+C cannot represent — reported with explicit non-identifiability caveat under N=7 HC pool. Methodological contributions: cross-subject HC resample for low-DOF inference; A2 PCA-aligned RDM atom; raw-weight composite (no z-score) exposing atom-equalization artifacts; multi-point validation simulation.

### 4.2 Introduction (~1500 words)

1. **Color-vision deficiency background** (3 paragraphs): retinal cone shift (DeMarco 1992; Machado 2009; Stockman cone fundamentals) → cortical compensation evidence (Boehm 2014, 2020; Tregillus 2021; Emery 2021) → individual variability and need for per-subject inference.
2. **fMRI color representation** (2 paragraphs): hue-selective responses in V1/V4 (Brouwer & Heeger 2009/2013; Parkes 2009; Conway 2007; Bannert & Bartels 2018; Kay 2008); forward-model inference (van Bergen & Jehee 2015/2017; Sadil 2022).
3. **Gap statement** (2 paragraphs): no current framework commits to a per-subject *mechanism class*; within-subject CV cannot discriminate same-fit mechanisms; HC pool sizes typical for high-resolution color fMRI (~6–10) underdetermine 2-DOF models — but this can be diagnosed via cross-subject resample + multi-point sim.
4. **Contribution statement** (1 paragraph): three refinements as listed above (§2).

### 4.3 Methods (~3000 words)

1. **Participants & design**: HC sub-01..07 (N=7); CVD sub-08 deutan, sub-09 protan, sub-10 near-normal (descriptive control). 6 runs × 8 colors (DKL hues, L*=75 equiluminant). 8AFC + JND behavioral protocol.
2. **fMRI preprocessing**: fmriprep_out_method3_header_mi (cite project paths); C010 amplitudes (6, 8, n_voxels) per ROI; ROIs V1, V2, V3, V4 (hV4 → V4 on disk). Cite project memory MEMORY.md.
3. **Forward model class** (§S1):
   - 3.1 R+C 1-DOF: δθ = (2−g)·δθ_Machado(Δλ). Three Δλ priors as sensitivity sweep (DPS_lit, Boehm, JND_Lamb).
   - 3.2 2-Component 2-DOF: δθ = β_s·cos(θ−90°) + β_c·cos(θ−θ_conf). θ_conf = 16° (protan), 150° (deutan).
   - 3.3 g terminology: g=2 operational null (CVD=HC), g=1 raw Machado baseline.
4. **Loss inventory** (§S2): L_α (8AFC softmax), L_γ (per-pair JND z²), L_LOCO (V4 voxel prediction), L_RDM (cosine ΔRDM); composite via z-score per atom.
5. **Phase A precondition** (§S3): signed Cohen's d ≥ +0.5 per (cell × loss); direction-aware admission. Per-subject atom set (sub-08 N=8, sub-09 N=3).
6. **Phase B inclusion screening** (§S4): cross-subject 5-train/2-test HC subset resample; 1000 draws per (subject × model × combo). Selection hierarchy: test_loss median (primary) + IQR (stability) + AIC/BIC (supplementary) + boundary rate (stability).
7. **Phase C weight sweep** (§S5): 2-simplex Dirichlet 10 points (3-atom) or 1-simplex 5 points (2-atom); composite `L = Σ w·z(L_atom)`, `Σ w = 1`; N_RESAMPLES = 100 per cell. No prior, no smoothing.
8. **Validation simulation** (§S5.3, §S5.4):
   - 8.1 Pre-Phase-C null sanity (v1): leave-one-HC-as-CVD; GT δθ=0; PASS R+C, partial 2-comp.
   - 8.2 Post-Phase-C multi-point (Round 1 + Round 2): GT set per candidate (null + fit-point); recovery via same Phase C pipeline.
9. **Phase D pre-image** (§S6): exact numerical inversion of forward δθ over 720 hue angles → 8 canonical pre-image points; required 8/8 exact (err < 0.001°).
10. **Phase 3 trigger conditions** (§S6.4): 5-condition gate (test_loss CI; pre-image exact; param non-boundary; forward ≥ 5°; HC specificity descriptive).
11. **Cross-subject HC resample as novel methodology** (§Discussion 5.3): note Task #53 NotebookLM query confirms no direct precedent.

### 4.4 Results (~2500 words)

1. **Phase A precondition** (§S3 table): sub-08 admits all atoms; sub-09 admits 3; sub-10 zero (correct null).
2. **Phase B inclusion** (§S4.5 table): final candidate set per subject — *Pipeline 3 candidates pending E2+E3*. Pipeline 2 historical: sub-08 S08-B (R+C g=2.60), S08-E (2-comp 38, −44), S08-C (R+C g=1.10 LOCO-only); sub-09 S09-A_DPS (R+C g=2.60 Δλ=10), S09-B. Pipeline 3 E1 top: sub-08 2-comp (β_s=14, β_c=−46) via triple γ; sub-09 R+C g=3.00 Δλ=3 nm.
3. **Phase C weight sweep** (§S5.2): Pipeline 2 sweep results retained as historical evidence; Pipeline 3 uses Layer A P2 lexicographic ranking instead.
4. **Validation diagnostics**:
   - 4.1 Pre-Phase-C null (v1): R+C PASS; 2-comp grid attraction documented.
   - 4.2 Multi-point Round 1 (§S5.4): S09-A_DPS null PASS (g̃=2.00 ± 0.19); S08-B null pull (g̃=0.50 at GT g=2 with fit-point partial recovery g̃=2.45 ± 0.00); S08-E non-identifiable at fit-point (β_c IQR=98) — reported as paper-mandated caveat.
5. **Cycle 1–8 diagnostic findings** (§S8):
   - 5.1 Per-pair JND prediction error (Cycle 1): sub-08 R+C fails OY (z²=16) and YG (z²=17), 2-comp fits OY (z²=4.6) and YG (z²=0.3) — yellow-region deficit outside Machado red-green axis.
   - 5.2 Behavioral-only fit (Cycle 2): sub-08 R+C g shifts 2.25 (behavioral) → 2.60 (composite); sub-08 best behavioral-only = 2-comp z²=46 (~2× lower than R+C z²=82); sub-09 robust (g=2.60 both).
   - 5.3 γ_all atom (Cycle 3–4): z-score composite equalizes atom information density; γ_all standalone reproduces behavioral-only fit exactly.
   - 5.4 A2 PCA-RDM (Cycle 5): 2× cleaner separation; adopted into v6 Phase B rerun. Sensitivity finding only (under-comp branch preference for some sub-08 cells).
   - 5.5 **Raw-weight composite (Cycle 6)**: explicit weights on raw atom values without z-score. Sub-08 top 8 raw = 100% 2-comp (R+C absent); sub-09 top 8 raw = 100% R+C — **decisive evidence that z-score normalization, not signal structure, produces sub-08's R+C top-ranking under composite**.
   - 5.6 SRM RDM atom empirical (Cycle 7b, BrainIAK SRM K=4 V1/V2, K=3 V4): sub-09 V1 sep z = +1.34 (strong; convergent with Cycle 6 raw R+C g=2.60); sub-08 V2 sep z = +0.28 (weak); sub-08 V4 sep z = +0.11 (SRM removes both noise and sub-08 V4 distinct signal — PCA proxy preserves it better at V4); sub-10 null sep z negative (correct rejection).
6. **Final candidate set 4-axis verdict table** (§S0): identifiability / behavioral fit (z² + raw-weight) / neural fit / Phase 3 testable.
7. **Forward δθ visualization** (§S6.3): per-candidate STIM_LAB 4-col rendering — original, CVD perceives, filter pre-image, CVD(filter) perceptual restoration.

### 4.5 Discussion (~2000 words)

1. **Per-subject mechanism identification** (1 paragraph): sub-09 = robust R+C over-comp; sub-08 = 2-Component primary with explicit non-identifiability caveat; mechanism class differs between deutan and protan in our two cases (no claim of generalization).
2. **R+C Machado-shape limit (yellow-region deficit)** (1 paragraph): the canonical 1-DOF compensation form (Boehm 2014) assumes retinal cone-shift drives all hue-direction deficits, with Machado(Δλ) shape fixed on the red-green axis. Sub-08's yellow-region deficit (orange-yellow 3×HC, yellow-green 3.1×HC; Cycle 1) lies orthogonal to this axis and is structurally outside R+C's representational capacity regardless of g. Implications: individualized models must allow cortical opponent rotation, not just retinal-driven gain.
3. **2-Component identifiability under low N** (1 paragraph): N=7 HC pool underdetermines 2-DOF cortical-only model; multi-point sim shows fit-point β_c IQR=98 for S08-E. Reported as paper-mandated caveat — point estimate only, statistical confidence withheld. Future work: larger HC pools or stronger physiological priors.
4. **Z-score atom-equalization artifact** (1 paragraph): standard z-score composite normalizes atoms by their HC-pool SD, which equalizes information density across atoms regardless of effective sample sizes (γ_all = 8 z² terms, γ_focal = 1 z² term). For sub-08, this artificially elevates R+C under z-score; the raw-weight composite (Cycle 6) — with explicit, unequalized weights — yields 100% 2-Component top 8. Methodological recommendation: report both z-score and raw-weight composites side-by-side.
4. **Cross-subject HC resample as novel methodology** (1 paragraph): Task #53 NotebookLM query result; compares to within-subject run-level CV in van Bergen/Jehee, Sadil etc.; trade-off (more samples vs subject-shared structure).
5. **A2 PCA-RDM vs SRM as denoised neural atoms** (1 paragraph): Voxel-level noise inflates raw RDM cosine; both PCA (per-subject decomposition, K=6) and BrainIAK SRM (joint HC-pool training, K-per-ROI) reduce this. Empirical convergence at sub-09 V1 (PCA gap 0.23–0.30; SRM sep z=+1.34) but divergence at sub-08 V4 (PCA gap 0.21–0.36 vs SRM sep z=+0.11) — *SRM's shared-K projection over-removes sub-08 V4's individual voxel-level signal*. Methodological recommendation: report PCA proxy + SRM jointly, treat sub-08 as behavioral-anchored.
6. **Per-subject inverse filter and Phase 3** (1 paragraph): pre-image extraction (8/8 exact for 2-comp both subjects); 5-condition trigger gate; sub-09 S09-B forward 4° < 5° failure as honest exclusion.
7. **Limitations** (§6 below — extensive).
8. **Future work** (1 paragraph): cross-subject SRM-aligned LOCO (resolves double-dipping); larger HC pool for 2-DOF identifiability; Phase 3 behavioral test execution.

---

## 5. Figures plan (6 figures)

- **F1. Pipeline schema (Phase A → D)**.
  - Phase A precondition (Cohen's d signed admission), Phase B HC resample (5-train/2-test diagram), Phase C weight sweep (Dirichlet simplex), Phase D pre-image (forward → inverse).
  - Caption emphasis: novel cross-subject HC resample for low-DOF inference.

- **F2. Per-pair JND prediction error (Cycle 1)**.
  - Bar chart per pair (8 pairs × 4 candidates) showing predicted vs observed JND z².
  - Sub-08 highlight: OY z²=16, YG z²=17 R+C vs 2-comp (OY z²=4.6, YG z²=0.3). Yellow-region deficit cluster visible.
  - Caption emphasis: R+C Machado shape limit traced to specific pairs.

- **F3. Behavioral-only vs composite fit (Cycle 2)**.
  - Two-panel: sub-08 (left) showing R+C g 2.25 → 2.60 shift + 2-comp grid region shift (48,−36) vs (38,−44); sub-09 (right) showing R+C g 2.60 robust + 2-comp grid region shift (26,4) vs (6,46).
  - Caption emphasis: composite g neural-biased for sub-08; 2-comp non-identifiable in both subjects under composite.

- **F4. 4-axis verdict table** (Methods/Results boundary).
  - Identifiability × behavioral fit × neural fit × Phase 3 testable per candidate.
  - Color-coded PASS/FAIL/PARTIAL per cell.
  - Caption emphasis: dual finding for sub-08 made explicit.

- **F5. Final candidate forward δθ in stimulus space** (4-col rendering).
  - Per `scripts/stim_lab_render.py`: Original → CVD perceives → Filter pre-image → CVD(filter) perceptual restoration.
  - 3 rows: S09-A_DPS (sub-09 R+C primary), S08-E (sub-08 2-comp primary), S08-B (sub-08 R+C sensitivity comparison).
  - Caption emphasis: STIM_LAB rendering convention; pre-image 8/8 exact for both 2-comp candidates; R+C row demonstrates Machado red-green limit.

- **F6. Sub-08 z-score vs raw-weight composite (Cycle 6)**.
  - Top panel: composite ranking under z-score (R+C dominant in top 3) vs raw scheme A (γ_all only, 2-comp 100% top 8) vs raw scheme B (γ_all + 50·RDM, 2-comp 100% top 4).
  - Bottom panel: per-pair JND z² breakdown highlighting yellow-region (OY, YG) — R+C unable to fit regardless of g.
  - Caption emphasis: z-score atom-equalization artifact; raw-weight composite reveals 2-Component as best behavioral + neural fit for sub-08.

---

## 6. Caveats / limitations

Stated explicitly in Discussion §4.5.7 and revisited in Conclusion.

1. **n = 2 CVD pool** (one deutan, one protan, plus sub-10 near-normal as descriptive control). Findings are individual-level, not population-level. Inferential generalization deferred to larger N follow-up.

2. **2-Component non-identifiability under N = 7 HC pool**. Multi-point sim Round 1 confirms S08-E fit-point β_c IQR = 98 (near full grid span); sub-09 2-comp also bimodal in both β_s and β_c. State plainly: under our pipeline + HC pool size, the 2-Component model is not identifiable at the fit point, not just at the null. **Sub-08's 2-Component (β_s=38, β_c=−44) is reported as point estimate only — statistical confidence is withheld**.

2b. **Sub-08 R+C representational impossibility (paper-level finding, not a caveat per se)**. Machado(Δλ) shape is fixed on the red-green axis; sub-08's behavioral deficit concentrates on yellow-region pairs (orange-yellow 3×HC, yellow-green 3.1×HC). No g value can rotate Machado shape to fit yellow-region pairs. This is reported as a constructive finding (mechanism class differentiation) rather than as a limitation of our pipeline.

3. **LOCO double-dipping unresolved**. Cycle 5 audit confirms within-CVD ridge LOCO is a direct double-dip (CVD trains and tests on its own data). B1 run-level CV wrapper insufficient (audit shows 0.03 difference). True resolution requires cross-subject SRM-aligned LOCO encoder (deferred to future work).

4. **Δλ-source bimodality (sub-08)**. Same atom configuration gives g = 0.05 under Boehm_mid (8 nm) vs g = 2.60 under DPS_lit (6 nm). Mechanism direction (under-compensation floor vs over-compensation ceiling) is Δλ-prior-determined, not data-identifiable for sub-08. Reported as sensitivity sweep + caveat; primary candidate uses DPS_lit population mean as physiologically primary.

5. **Phase 3 trigger not yet executed**. Behavioral test of filter prediction (forward δθ applied to stimulus space → JND change vs no-filter baseline) is the validation step but has not been run. S09-B variant fails Trigger Condition #4 (forward 4° < 5° perceptual threshold) — honest exclusion from Phase 3 entry.

6. **HC pool is N=7 (effective N=6 for V4 due to sub-07 16-voxel limit)**. Cannot be enlarged within current data acquisition. Statistical specificity claims (HC FPR) suppressed per project §0 framework decision — descriptive percentile only.

7. **A2 PCA-RDM is a proxy for SRM**. Full Shared Response Model (BrainIAK) deferred due to MPI environment constraints (project MEMORY); PCA is a denoising approximation, not a learned shared-space projection.

8. **v6 Phase B rerun pending**. Final candidate set assumes v6 confirms v5 (≤ 10% numerical shift); explicit "v6 pending" markers throughout. Manuscript will not be submitted until v6 results land.

---

## 7. Pre-registration block

### Pre-registered (locked before Cycle 1–5)

- **Phase A precondition criterion**: signed Cohen's d ≥ +0.5, direction-aware (one-sided). Sub-10 V3/V4 RDM (d=−1.08/−1.91) correctly rejected.
- **Phase B inclusion via cross-subject HC resample**: 5-train/2-test, 1000 draws per cell.
- **Candidate selection rule (§S4.3 hierarchy)**: test_loss median primary, IQR stability, AIC/BIC supplementary, boundary rate.
- **Phase 3 trigger 5-condition gate (§S6.4)**: test_loss CI; pre-image exact; param non-boundary; forward ≥ 5°; HC specificity descriptive.
- **Single mechanism per subject (§A11)**: no model averaging.
- **R+C g operational null = g=2** (study H0).
- **2-Component CIELab opponent space (§A12)**.
- **Encoder = ridge_gcv (§A10)**; smooth_tikh rejected after 3 rescue attempts.

### Exploratory (post-hoc, Cycle 1–5)

- Cycle 1 per-pair JND prediction error reframing — motivated by user concern 2026-05-26.
- Cycle 2 behavioral-only fit comparison — post-hoc reanalysis.
- Cycle 3–4 γ_all atom and v5 enumeration extension — diagnostic, not adopted into final pipeline.
- Cycle 5 A2 PCA-RDM atom — adopted into v6 as method refinement.
- Dual-finding sub-08 framing — post-hoc decision after Round 1 multi-point sim.

Pre-registration boundary: Phase B v3/v4/v5 are within pre-registration. Phase B v6 (PCA-RDM) is a registered post-hoc method refinement (Cycle 5 finding).

---

## 8. References (essential, ~15)

1. **Boehm, A. E., Bosten, J. M., & MacLeod, D. I. A. (2014)**. Color discrimination in anomalous trichromacy: Experiment and theory. *Vision Research, 102*, 75–86. — Linear compensation form g for cortical gain; primary mechanistic grounding for R+C.
2. **Boehm, A. E., MacLeod, D. I. A., & Bosten, J. M. (2020)**. — Updated compensation model evidence.
3. **Tregillus, K. E. M., et al. (2021)**. Color compensation in anomalous trichromats assessed with fMRI. *Current Biology*. — Cortical compensation in CVD via fMRI.
4. **Emery, K. J., Webster, M. A., & Conway, B. R. (2021)**. Variations of color vision in modern populations. *Annual Review of Vision Science*. — S-cone cardinal grounding for β_s.
5. **Brouwer, G. J., & Heeger, D. J. (2009)**. Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience, 29*(44), 13992–14003. — Forward-model decoding; LOCO precedent.
6. **Brouwer, G. J., & Heeger, D. J. (2013)**. Categorical clustering of the neural representation of color. *Journal of Neuroscience, 33*(39), 15454–15465.
7. **Kay, K. N., et al. (2008)**. Identifying natural images from human brain activity. *Nature, 452*(7185), 352–355. — fMRI forward modeling.
8. **Dumoulin, S. O., & Wandell, B. A. (2008)**. Population receptive field estimates in human visual cortex. *NeuroImage, 39*(2), 647–660. — pRF / forward-model methodology.
9. **van Bergen, R. S., & Jehee, J. F. M. (2015, 2017)**. — Within-subject voxel CV for forward-model inference; precedent we contrast with cross-subject HC resample.
10. **Benson, N. C., & Winawer, J. (2018)**. — Visual cortex forward modeling.
11. **Sadil, P. S., et al. (2022)**. — Hierarchical Bayesian color decoding; weak prior comparison.
12. **Machado, G. M., Oliveira, M. M., & Fernandes, L. A. F. (2009)**. A physiologically-based model for simulation of color vision deficiency. *IEEE TVCG, 15*(6), 1291–1298. — Machado retinal simulator.
13. **Stockman, A., & Sharpe, L. T. (2000)**. Cone fundamentals. — Cone spectral sensitivities; confusion line derivation.
14. **Conway, B. R. (2007)**. Color vision, cones, and color-coding in the cortex. *The Neuroscientist*. — V4 hue hub.
15. **Bannert, M. M., & Bartels, A. (2018)**. Human V4 activity patterns predict behavioral performance in imagery of object color. *Journal of Neuroscience, 38*(15), 3657–3668. — V4 perceptual hub.
16. **DeMarco, P., Pokorny, J., & Smith, V. C. (1992)**. Full-spectrum cone sensitivity functions for X-chromosome-linked anomalous trichromats. *JOSA A, 9*(9), 1465–1476. — DPS_lit population Δλ source.
17. **Lamb, T. D. (1999)**. Photopigments and the biophysics of transduction in cone photoreceptors. — JND_Lamb Δλ derivation.

---

## 9. Working drafting order

Recommend writing in the order:
1. Methods (most stable; Phase A–D + Cycle 1–5 are documented).
2. Results (built from `PIPELINE_UPDATED_0524.md` §S0–§S8 tables).
3. Discussion limitations § (§6 above; explicit, anti-sycophancy).
4. Discussion findings paragraphs.
5. Introduction (gap statement easier after Methods/Results are concrete).
6. Abstract (last).

Figures F1, F4, F5 can be generated immediately from existing scripts (`stim_lab_render.py`); F2, F3, F6 require small new plotting scripts (Cycle 1 per-pair z² output already exists per `BEHAVIORAL_FIT_DIAGNOSIS_2026-05-26.md`).

---

## 10. Pending items flagged for user

1. **v6 Phase B rerun** (PCA-RDM atom integrated) — currently running; results will update the final candidate set with ≤ 10% numerical shift (working assumption). Until then, all candidate fits are tagged "v5-validated, v6 pending."
2. **Phase D launch decision** — gated on v6 results + user signoff on dual-report sub-08 framing.
3. **Phase 3 protocol design** — separate document needed; outline only at §S6.5 acceptance criteria; not in this paper outline scope.
4. **Working title** — proposed in §1 above; user to confirm or revise.
5. **References list** — 17 items; user to confirm completeness or trim to ~15 essential.
6. **v3 sim (empirical low-rank covariance) launch trigger** — pending Phase C real-data 2-comp grid attraction; not blocking submission.
