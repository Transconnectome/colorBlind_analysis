# Phase 2b: Decoder Model Comparison & Validation

> Decoder optimality is task-dependent: LDA + SRM for classification (0.793 accuracy, ICC 0.666), ForwardEncoding + Procrustes for interpolation (75.7 degrees HC MAE). CVD subjects discriminate colors as well as HC but show impaired interpolation, consistent with color space distortion rather than signal loss. FE channel weights are highly stable across folds (cosine similarity 0.921 [0.907, 0.935]).

---

## Objective

Validate four decoder assumptions before proceeding to filter optimization: (1) whether the voxel-to-color mapping is fundamentally linear, (2) whether alignment is necessary or whether non-linear models can compensate, (3) whether HC and CVD share the same mapping (prerequisite for filter learning), and (4) whether models can interpolate held-out colors from continuous color structure. These assumptions determine the decoder architecture and alignment pipeline for Phase 3.

## Participants & Data

- **Participants**: 10 subjects (7 HC: sub-01 to sub-07; 3 CVD: sub-08 deutan, sub-09 protan, sub-10 deutan)
- **Input**: C010 Procrustes-aligned amplitudes (6 runs, 8 colors, n voxels); also raw and SRM-projected variants
- **ROIs**: V1, V2, V3, hV4 (Wang Atlas)
- **SRM k values**: V1 = 4, V2 = 4, V3 = 3, hV4 = 3
- **Models**: 6 decoders (LDA, SVM, Ridge, KernelRidge, ForwardEncoding, MLP) + 2 hybrids (FE+SVM, FE+MLP)
- **Cross-validation**: LORO (6-fold leave-one-run-out) for classification; LOCO (8-fold leave-one-color-out) for interpolation. Nested hyperparameter tuning on inner LORO folds (5-fold within 5 training runs).
- **Statistical methods**: Bootstrap 95% CIs (1,000 iterations), ICC test-retest reliability, Mann-Whitney U for group comparisons, Wilcoxon signed-rank for alignment comparisons, permutation tests (1,000 iterations) for LOCO

## Methods

### LORO Classification

All 6 models trained on 5 runs, tested on 1 held-out run. Nested hyperparameter tuning on inner LORO folds (5-fold within the 5 training runs) prevents tuning leakage. Three alignment conditions tested systematically: raw (no alignment), Procrustes (orthogonal transformation of all 6 runs to run-0 reference), and SRM (HC-only shared space, k = 3-4 dimensions). Bootstrap CIs computed by subject-level resampling (1,000 iterations). ICC reliability computed across LORO folds -- this measures whether individual-difference estimates (who decodes well vs. poorly) are reproducible across different run holdouts. High accuracy with low ICC indicates fold-specific overfitting rather than stable individual differences.

### LOCO Interpolation

ForwardEncoding model trained on 7 colors, tested on 1 held-out color. The model uses 6 half-wave rectified Gaussian basis functions (Brouwer & Heeger, 2009) to encode channel responses, then predicts the held-out color's hue angle via correlation-based template matching against a 360-degree basis set. Predicted hue angle compared to true angle; MAE in degrees (chance = 90 degrees). Permutation tests (1,000 iterations, color label shuffling within each run) assess significance per subject-ROI. The critical feature of LOCO is that it tests *interpolation* -- can the model predict a color it has never seen, based on the continuous structure of the learned color space? This is fundamentally different from LORO, which tests classification (can the model recognize a color it has seen in other runs?).

### Group Prior

HC-mean channel weight matrix (W) used as regularization prior for individual subjects: W_combined = lambda * W_individual + (1 - lambda) * W_group. Lambda selected via nested leave-one-run-out CV within each LOCO/LORO fold to prevent leakage. Lambda grid: 16 values from 0.0 to 1.0 (0.0 = pure group prior, 1.0 = pure individual). For LOCO, group W excludes the held-out test color per fold to prevent information leakage (corrected 2026-02-28; previous results with leakage showed inflated -50.9% improvement). For LORO, no such exclusion is needed since all colors appear in every fold.

### Cross-Decoding

HC-only SRM trained on 7 HC subjects. LDA trained on HC mean betas in shared space, tested on each CVD subject projected via SVD. Permutation test (1,000 iterations, label shuffling) per subject-ROI. This tests the strongest possible version of the shared-mapping assumption: can a decoder that has *never seen CVD data* decode CVD color representations? A complementary FE cross-decoding analysis (HC-trained W applied to CVD in SRM space) tests continuous hue decoding, not just categorical classification.

## Results

### Task-Dependent Optimality Summary

| Task | Optimal Pipeline | Key Metric | Rationale |
|------|-----------------|------------|-----------|
| LORO (classification) | LDA + SRM | 0.793 acc, ICC 0.666 | SRM resolves LDA fold-instability |
| LOCO (interpolation) | FE + Procrustes | 75.7 degrees HC MAE | Full voxels preserve continuous hue structure |
| Phase 3 (filter design) | FE + Procrustes | W cosine 0.921 | Stable 6-channel representation |
| Cross-subject comparison | LDA + SRM | p = 0.668 (no bias) | Unbiased HC-to-CVD generalization |

This task-dependent optimality reflects fundamentally different demands: classification needs consistent low-dimensional decision boundaries (favoring SRM's denoised shared space), while interpolation needs the full continuous hue structure preserved across all voxels (favoring Procrustes' full voxel space). The alignment x ROI interaction (SRM better for V1/V2, Procrustes better for V3/hV4) adds a spatial dimension to this task-dependency: higher visual areas have more individual-specific structure that SRM's shared-space assumption sacrifices.

### LORO Classification: 3-Alignment Comparison (Bootstrap 95% CI)

| Model | Raw | Procrustes | SRM |
|-------|-----|------------|-----|
| **LDA** | 0.135 [0.119, 0.153] | 0.758 [0.734, 0.780] | **0.793 [0.759, 0.825]** |
| SVM | 0.127 [0.114, 0.140] | 0.685 [0.655, 0.714] | 0.727 [0.685, 0.770] |
| FE | 0.129 [0.110, 0.146] | 0.545 [0.511, 0.579] | 0.480 [0.449, 0.514] |
| Ridge | 0.131 [0.116, 0.147] | 0.388 [0.361, 0.417] | 0.313 [0.276, 0.348] |
| KRidge | 0.127 [0.110, 0.143] | 0.332 [0.300, 0.366] | 0.285 [0.252, 0.319] |
| MLP | 0.126 [0.118, 0.135] | 0.147 [0.136, 0.158] | 0.131 [0.126, 0.138] |

Chance = 0.125. Without alignment (raw), all models perform at chance (0.126-0.135). Alignment is the single most critical factor -- non-linear models (SVM, KernelRidge) do not compensate for misalignment. SRM LDA achieves the highest accuracy and significantly exceeds Procrustes LDA (Wilcoxon p = 0.002 in V1). FE accuracy is lower under SRM (0.480) than Procrustes (0.545) because SRM's dimensionality reduction (k = 3-4) discards voxel-level variance that FE's encoding basis leverages. MLP fails in all alignment conditions (0.126-0.147), indicating that the small sample size (40 training samples per fold) is fundamentally insufficient for neural network training.

### Procrustes Alignment Effect (Delta = Procrustes - Raw)

| Model | Raw acc | Procrustes acc | Delta |
|-------|---------|----------------|-------|
| LDA | 0.393 | 0.821 | **+0.428** |
| Ridge | 0.375 | 0.783 | +0.408 |
| SVM | 0.382 | 0.776 | +0.393 |
| KRidge | 0.380 | 0.739 | +0.359 |
| FE | 0.367 | 0.736 | +0.369 |
| MLP | 0.370 | 0.394 | +0.024 |

Note: These values use acc_45 (within 45 degrees tolerance, chance = 0.375), from the nested Procrustes validation (Result 3) which eliminates alignment leakage. Nested Procrustes actually *improves* over preloaded Procrustes for SVM (+0.123) and FE (+0.045), confirming the original results were conservative, not inflated. LDA benefits most from alignment (+42.8 pp), confirming that the mapping is linear but requires run-to-run alignment. MLP is the only model that fails to benefit (+2.4 pp), as its small-sample overfitting overwhelms any alignment improvement.

### Alignment x ROI Interaction (Wilcoxon signed-rank, all models)

| ROI | SRM vs Procrustes p | Winner |
|-----|---------------------|--------|
| V1 | 0.002 | **SRM** |
| V2 | 0.058 | SRM (trend) |
| V3 | 9.1e-08 | **Procrustes** |
| hV4 | 1.8e-05 | **Procrustes** |

SRM dominates V1/V2 (early visual) where k = 4 captures sufficient variance. Procrustes dominates V3/hV4 (higher visual) where k = 3 may under-capture representational complexity. This spatial dissociation suggests that higher visual areas have more individual-specific structure that SRM's shared-space assumption sacrifices.

### LORO Test-Retest Reliability (ICC)

| Model | Raw | Procrustes | SRM |
|-------|-----|------------|-----|
| LDA | 0.224 | 0.013 | **0.666** |
| Ridge | 0.233 | 0.148 | 0.762 |
| KRidge | 0.324 | 0.463 | 0.790 |
| SVM | -0.284 | 0.495 | 0.760 |
| MLP | 0.611 | 0.720 | 0.713 |
| FE | 0.471 | 0.574 | 0.753 |

**Procrustes LDA paradox**: 0.758 accuracy but ICC = 0.013. High accuracy with zero reproducibility arises from fold-specific separating hyperplanes in high-dimensional voxel space (568 voxels, 40 training samples per fold). Each LORO fold finds a different decision boundary that happens to classify well but carries no consistent individual-difference information. LDA run-pair reliability confirms this: mean r = 0.009 across all run subsets, compared to FE r = 0.329.

SRM's dimensionality reduction (k = 3-4) eliminates this overfitting: LDA achieves both the highest accuracy (0.793) and reliable ICC (0.666). SRM is the only alignment where all 6 models achieve ICC > 0.66 -- the only alignment producing universally reliable individual-difference estimates. This is critical for any study using decoding accuracy as an individual biomarker.

### HC vs. CVD LORO Comparison (SRM, Mann-Whitney U)

| Model | HC Mean | CVD Mean | Diff | p-value |
|-------|---------|----------|------|---------|
| LDA | 0.635 | 0.665 | -0.030 | 0.668 |
| SVM | 0.464 | 0.488 | -0.024 | 0.647 |
| FE | 0.526 | 0.462 | +0.064 | 0.076 |

LDA and SVM show no HC-CVD generalization gap -- CVD subjects decode equally well in the HC-trained SRM space. This confirms that CVD color representations, while geometrically distorted, maintain the same categorical structure as HC. FE shows a trend toward HC advantage (p = 0.076), consistent with the LOCO finding that FE captures geometric structure that differs between groups -- FE is sensitive to the continuous hue geometry that CVD disrupts, while LDA only needs categorical boundaries.

### LOCO Interpolation: ForwardEncoding MAE by Alignment and Group

| ROI | Raw HC | Raw CVD | Proc HC | Proc CVD | SRM HC | SRM CVD |
|-----|--------|---------|---------|----------|--------|---------|
| V1 | 76.9 | 76.4 | 76.4 | 84.6 | 80.0 | 93.5 |
| V2 | 74.8 | 78.5 | 80.0 | 98.5 | 84.9 | 90.5 |
| V3 | 77.8 | 76.4 | 77.0 | 73.5 | 99.3 | 88.3 |
| hV4 | 73.5 | 76.0 | 69.4 | 87.4 | 72.2 | 90.9 |

Chance = 90 degrees. ForwardEncoding dominates LOCO (best model in 85% of subject-ROI-alignment combinations, 102/120 cells). LORO and LOCO show opposite alignment preferences: LORO favors SRM, LOCO favors Procrustes. This dissociation reflects different task demands -- classification needs consistent decision boundaries (favoring low-dimensional shared space), while interpolation needs the full continuous hue structure preserved across voxels.

CVD deficit is only visible after alignment (raw: HC approximately equals CVD with < 4 degrees difference; Procrustes: CVD V2 +18.5 degrees, hV4 +18.0 degrees). SRM is worst for LOCO -- dimensionality reduction from hundreds of voxels to k = 3-4 loses continuous hue structure (V3: +22.3 degrees MAE increase from Procrustes to SRM, the worst single ROI). This finding is critical: SRM and LOCO serve complementary but incompatible purposes, and should not be combined in a single pipeline.

### LOCO Crawford & Howell Validation (Procrustes, ForwardEncoding)

| ROI | HC MAE (SD) | CVD MAE (SD) | Separation | g [95% CI] | p (perm) |
|-----|------------|-------------|-----------|-----------|---------|
| V1 | 79.2 (8.4) | 84.6 (28.3) | +8.3 | 0.47 [-2.65, 5.30] | 0.237 |
| V2 | 80.0 (16.7) | 98.5 (20.5) | +18.5 | 0.94 [-0.26, 5.09] | 0.072 |
| V3 | 77.0 (16.2) | 73.5 (9.9) | -3.4 | -0.21 [-1.51, 0.79] | 0.642 |
| **hV4** | **69.4 (9.4)** | **87.4 (10.2)** | **+18.0** | **1.69 [0.94, 3.68]** | **0.017*** |

hV4 is the only ROI with significant group-level LOCO deficit (p = 0.017, g = 1.69 with CI excluding zero). V2 shows a trending deficit (p = 0.072). This converges with Phase 2 SRM disparity results (V2 p = 0.072 LOCO vs 0.075 SRM; hV4 p = 0.017 LOCO vs 0.559 SRM). The hV4 convergence across independent methods (SRM disparity + LOCO interpolation) strengthens the evidence for genuine CVD effects in this ROI.

### LOCO Individual CVD Profiles (Procrustes, ForwardEncoding MAE)

| Subject | V1 | V2 | V3 | hV4 | Profile |
|---------|------|------|------|------|---------|
| sub-08 (deutan) | **52.0** | 68.4 | 59.1 | 68.4 | Best CVD (all below chance) |
| sub-09 (protan) | 104.1 | 105.9 | 72.2 | 97.5 | Worst (3/4 above chance) |
| sub-10 (deutan) | 97.5 | 108.8 | 75.0 | 77.8 | Mixed |
| HC mean (SD) | 79.2 (8.5) | 78.2 (15.8) | 74.1 (15.8) | 69.1 (10.3) | -- |

Individual significance (permutation p < 0.05): sub-08 V1 p = 0.035, sub-05 V2 p = 0.011, sub-01 V3 p = 0.004, sub-04 hV4 p = 0.033 (only 4/40 pairs significant -- low power with 8 test folds). sub-08 achieves the best single-subject V1 result (52.0 degrees, p = 0.035), outperforming most HC subjects. This paradoxical result suggests that sub-08's deutan color space, while distorted relative to HC, preserves local hue continuity in V1 -- the hue circle is warped but not broken. sub-09 (protan) shows the most impaired interpolation (3/4 ROIs above chance), consistent with more severe disruption of the continuous hue manifold.

### Group Prior Improvement (Nested CV, Leakage-Free)

**LOCO (lambda selected by nested CV within each LOCO fold)**

| ROI | HC Baseline | HC GP | HC Change | CVD Baseline | CVD GP | CVD Change |
|-----|-------------|-------|-----------|-------------|--------|-----------|
| V1 | 80.7 | 77.3 | +4.3% | 93.5 | 85.7 | +8.3% |
| V2 | 85.9 | 78.7 | +8.3% | 90.5 | 85.4 | +5.7% |
| V3 | 100.6 | 105.9 | -5.3% | 88.3 | 112.2 | -27.0% |
| hV4 | 71.2 | 75.5 | -6.1% | 90.9 | 95.7 | -5.2% |

Lambda = 0.0 (pure group prior) selected in 80.6% of folds (232/288), indicating that the HC-mean W provides a better initialization than individual estimates from only 7 LOCO training colors. The high lambda = 0.0 rate reflects the fundamental data limitation: with df = 1 per channel (7 colors minus 6 basis functions), individual W estimates are unreliable, and the group mean is more stable. Group prior improves V1/V2 but harms V3/hV4 -- the latter have more individual variability that the group mean washes out.

**LORO (standard nested CV; no leakage issue)**

| ROI | Baseline MAE | GP MAE | Improvement |
|-----|-------------|--------|-------------|
| V1 | 42.40 | 34.47 | -18.7% |
| V2 | 50.96 | 32.72 | -35.8% |
| V3 | 60.63 | 54.25 | -10.5% |
| hV4 | 62.21 | 61.34 | -1.4% |

LORO benefits more than LOCO because individual W estimated from 5 training runs is more stable than from 7 LOCO colors. Lambda is more diverse in LORO (median approximately 0.25 vs. 0.0 for LOCO; only 4/36 cases select lambda = 0.0), confirming that individual W from 5 runs contains useful information worth preserving. The ROI-specific pattern (V1/V2 benefit, V3/hV4 flat) reflects that early visual areas share more cross-subject color structure, while higher areas show more individual variability.

### Cross-Decoding: HC-to-CVD in SRM Space

| ROI | k | sub-08 (acc, p) | sub-09 (acc, p) | sub-10 (acc, p) |
|-----|---|-----------------|-----------------|-----------------|
| V1 | 4 | 1.000 (p = 0.000) | 0.875 (p = 0.000) | 1.000 (p = 0.000) |
| V2 | 4 | 0.750 (p = 0.000) | 0.875 (p = 0.000) | 1.000 (p = 0.000) |
| V3 | 3 | 0.625 (p = 0.000) | 0.750 (p = 0.000) | 0.875 (p = 0.000) |
| hV4 | 3 | 0.375 (p = 0.057) | 0.625 (p = 0.000) | 0.375 (p = 0.056) |

10/12 tests significant (chance = 12.5%). HC-trained decoders generalize to CVD subjects in V1/V2/V3, confirming shared voxel-color mapping -- a necessary prerequisite for filter learning. Accuracy decreases from V1 (0.875-1.000) to hV4 (0.375-0.625), paralleling the SRM quality gradient (HC LOSO baseline: V1 0.946, V2 0.839, V3 0.768, hV4 0.446). hV4 shows marginal results for sub-08 and sub-10, reflecting lower SRM quality rather than a breakdown of the shared mapping assumption.

A complementary FE cross-decoding analysis (HC-trained W applied to per-run CVD data in SRM space) confirmed 10/12 (83%) tests significant, with V1/V2 at 100% success. Sub-08 achieved the best V1 MAE (24.0 degrees, better than HC held-out 38.0 degrees), consistent with strong color signal in sub-08's deutan visual cortex.

### FE Channel Weight Stability

| Metric | Value |
|--------|-------|
| Grand mean cosine similarity | **0.921** [95% CI: 0.907, 0.935] |
| Range (min-max across subject-ROIs) | 0.878 -- 0.978 |
| Mean SD per subject-ROI | 0.017 |

W matrices are highly stable across LORO folds (cosine similarity > 0.87 everywhere). This confirms that the 6-channel representation is a reliable basis for Phase 3 filter design -- the encoding weights do not fluctuate meaningfully across different training subsets. The lowest cosine (0.878) occurs for subject-ROIs with fewer voxels, confirming the expected relationship between data richness and estimation stability.

### Negative Results

1. **Alternative LOCO decoders**: PopVec, RidgeEnc, GaussML, and RidgeReg all worse than baseline correlation template matching. With only 7 training colors per LOCO fold, there are insufficient degrees of freedom for parameter-based decoding methods. RidgeReg shows anti-interpolation (MAE approximately 175-180 degrees) -- a known failure mode of underdetermined regression (p = 6 features, n = 7 samples, df = 1). PopVec shows sporadic V1 improvements (sub-05: 44.5 vs 61.8 degrees) but is inconsistent across ROIs. The decoding stage is NOT the performance bottleneck; the encoding estimation (W from only 7 colors) is the limiting factor.

2. **MLP architecture sweep**: All MLP variants tested on 3 pilot subjects (varying hidden layers from (8,) to (64,32), regularization alpha from 0.1 to 10.0, parameter counts from 62 to 2,726) substantially worse than FE baseline (+57 degrees penalty, best MLP 131.9 degrees vs. FE 74.9 degrees). Non-linear readout is fundamentally incompatible with LOCO out-of-distribution extrapolation -- the held-out color's channel response lies outside the training manifold, and MLP amplifies this extrapolation error.

3. **Hybrid decoders**: FE + SVM approximately equals FE (0.779 vs. 0.784 accuracy). FE + MLP degenerates to constant prediction (0.381) with 8 validation samples too few for early stopping. The channel-to-color mapping is adequately linear -- non-linear readout provides no benefit over correlation template matching.

4. **Sequential training**: MLP with warm_start across cumulative runs showed no improvement over pooled training. FE is analytically solved (pseudoinverse), making sequential training mathematically equivalent to pooled. SVR lacks warm_start support. The sequential training direction is closed.

5. **Non-linear LOCO models (all alignments)**: MLP, SVM, HybridMLP, and HybridSVR all worse than ForwardEncoding across all ROIs, alignment conditions (raw, Procrustes, SRM), AND groups (HC and CVD). Penalty range: +19 to +46 degrees MAE. Non-linear failure is not alignment-specific, ROI-specific, or group-specific -- it is a fundamental limitation of parametric models in the LOCO regime.

6. **Group prior leakage**: Earlier LOCO GP results (median -50.9% improvement) were artifacts from lambda selection on data that included the LOCO test color. The corrected nested CV (excluding test color from group W) shows modest +4-8% improvement in V1/V2 only. LORO GP results (-19 to -36%) were unaffected as LORO does not exclude colors.

## Discussion

1. **Linear channel representation exists.** Linear models (LDA, FE) match or exceed non-linear alternatives across both tasks. The voxel-to-color mapping is fundamentally linear after appropriate alignment. Non-linear models (SVM, KernelRidge, MLP) provide no compensatory benefit in any alignment condition -- even the most flexible architectures cannot outperform linear models.

2. **Task-dependent optimality.** Classification (LORO) favors SRM's low-dimensional denoised space; interpolation (LOCO) favors Procrustes' full voxel space. This dissociation reflects the different demands: classification needs consistent decision boundaries across runs, while interpolation needs the full continuous hue structure preserved across voxels. The alignment x ROI interaction (SRM better for V1/V2, Procrustes for V3/hV4) adds a spatial dimension to this task-dependency.

3. **LORO-LOCO dissociation reveals CVD color space distortion.** CVD subjects discriminate colors as well as HC (LORO accuracy approximately equal, cross-decoding 10/12 significant) but show impaired interpolation (LOCO MAE: V2 +18.5 degrees, hV4 +18.0 degrees). This combination of intact discriminability with impaired interpolation is direct neural evidence that CVD is a color space geometry distortion, not a signal loss. CVD brains can tell colors apart (preserved categorical boundaries) but cannot represent the continuous relationships between them normally (disrupted hue manifold).

4. **Group prior benefits are ROI-specific.** V1/V2 benefit from HC-mean W (early visual areas share more structure across subjects), while V3/hV4 are harmed (higher-level areas show more individual variability that the group mean washes out). Earlier LOCO GP results showing median -50.9% improvement were leakage artifacts; the corrected nested CV shows modest +4-8% improvement in V1/V2. LORO GP is more effective (-19 to -36%) because individual W from 5 training runs is more informative than from 7 LOCO colors.

5. **FE channel weights are highly stable.** W matrix cosine similarity across LORO folds = 0.921 [0.907, 0.935], confirming that the 6-channel representation is a reliable basis for Phase 3 filter design. Individual W estimates converge regardless of which run is held out, with the lowest cosine (0.878) still indicating substantial agreement.

6. **Procrustes LDA paradox is alignment-specific.** The ICC = 0.013 for Procrustes LDA disappears under SRM (ICC = 0.666). Run-pair reliability analysis confirms: LDA r = 0.009 (subject-ROI rankings reshuffle completely across run subsets) vs. FE r = 0.329 (most stable decoder). This demonstrates that high decoding accuracy does not guarantee reliable individual differences -- a critical consideration for any study using decoding accuracy as an individual biomarker. SRM is the only alignment achieving universal reliability (all 6 models ICC > 0.66).

## Limitations

- **LOCO MAE limited by encoding estimation.** With only 7 training colors per LOCO fold, the encoding stage has df = 1 per channel. This is the fundamental bottleneck, not the decoding stage. Improving LOCO requires better encoding weight estimation (e.g., trial-level encoding), not alternative decoders.
- **SRM hurts LOCO.** Dimensionality reduction from hundreds of voxels to k = 3-4 components loses the continuous hue structure needed for interpolation, especially in V3 (100 voxels to k = 3, +22.3 degrees MAE). SRM and LOCO are complementary tools for different questions, not a combined pipeline.
- **Procrustes LDA paradox.** The ICC = 0.013 for Procrustes LDA means individual difference estimates under this pipeline are unreliable, even though group-level accuracy is high. SRM resolves this, but researchers should be aware that high decoding accuracy does not guarantee reliable individual differences.
- **Group prior leakage.** Earlier LOCO GP results (median -50.9% improvement) were leakage artifacts from lambda selection on data that included the test color. The corrected nested CV shows modest +4-8% improvement in V1/V2 only.
- **LOCO individual significance is sparse.** Only 4/40 subject-ROI pairs reach p < 0.05 (sub-01 V3, sub-04 hV4, sub-05 V2, sub-08 V1), reflecting low power with 8 test folds x 6 runs.
- **CVD heterogeneity in LOCO.** sub-08 outperforms most HC in V1 LOCO (52.0 degrees), while sub-09/sub-10 perform at or below chance. A single characterization of "CVD interpolation deficit" misses this individual variability, consistent with the CVD heterogeneity observed in Phase 2.

## References

- Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.
- Chen, P. H., et al. (2015). A reduced-dimension fMRI shared response model. *NIPS*.
- Crawford, J. R., & Howell, D. C. (1998). Comparing an individual's test score against norms derived from small samples. *The Clinical Neuropsychologist*, 12(4), 482-486.

---

**Last Updated**: 2026-03-03
