# Phase 1: Preprocessing Pipeline & Baseline Color Decoding

> Procrustes alignment of C010-preprocessed fMRI data yields 79% noise ceiling utilization at the pipeline level, establishing a reliable foundation for color representation analysis. hV4 shows the strongest color selectivity (RDM correlation 0.541, noise ceiling 0.697).

---

## Objective

Establish an optimal fMRI preprocessing pipeline for extracting color-selective neural representations from visual cortex. Specifically, determine whether (a) 2nd-level drift removal (C010) is sufficient without additional confound regression, (b) Procrustes alignment can remove geometric variance between runs, and (c) whitening provides any benefit. This phase provides the validated input data for all subsequent analyses (Phase 2 SRM, Phase 2b decoders, and Phase 3 filter design).

## Participants & Data

- **Participants**: 10 subjects (7 HC: sub-01 to sub-07; 3 CVD: sub-08 deutan, sub-09 protan, sub-10 deutan)
- **CVD diagnosis**: Ishihara test
- **Acquisition**: 6 runs per subject, 8 discrete color stimuli per run (red, orange, yellow, green, cyan, blue, purple, magenta)
- **Preprocessing**: fMRIPrep 23.2.3, MNI152NLin2009cAsym space, res-2
- **ROIs**: V1, V2, V3, hV4 (Wang Atlas; Wang et al., 2015)
- **Voxel counts**: Range from 67 (hV4, sub-07) to 568 (V1); top 50% by FIR R-squared retained after voxel selection
- **Samples per run**: 48 trials (6 repetitions x 8 colors), yielding 288 total trials per subject across 6 runs
- **Exclusion**: sub-07 hV4 excluded from noise ceiling analysis (only 16 voxels in C010 pipeline, making correlation distance underdetermined). This exclusion propagates to all downstream analyses involving hV4 group statistics.

## Methods

### GLM Pipeline (C010)

- **1st-level GLM**: FIR basis functions (8 delays, 0-12s post-stimulus at TR = 1.5s). FIR was chosen over canonical HRF to capture the full hemodynamic response shape without making assumptions about peak timing or dispersion, which may differ across visual areas and subjects. Each FIR delay is estimated independently, providing a non-parametric estimate of the BOLD response time course.
- **Voxel selection**: Top 50% by FIR R-squared, retaining only voxels with reliable stimulus-evoked responses. This data-driven selection ensures color-selective voxels are included while removing noise-dominated voxels.
- **2nd-level GLM**: 8 HRF + 8 HRF derivative regressors + 12 per-run drift regressors (linear + constant per run, 2 regressors x 6 runs). The HRF derivative regressors capture timing variability across conditions; the drift regressors handle slow temporal trends without requiring high-pass filtering.
- **Confounds**: None. Motion parameters (6 DOF), tissue signals (CSF/WM mean), and white-matter regression were tested individually and in combination. All confound configurations degraded signal by approximately -60%, likely because confound regressors remove shared variance that overlaps with color-selective activation patterns in visual cortex. This is particularly problematic in early visual areas where color-selective patterns may covary with physiological signals.
- **High-pass filtering**: None. Drift regressors handle slow trends equivalently; explicit HPF provides zero additional benefit when drift regressors are included (tested empirically). The 1st+2nd-level and 2nd-level-only drift models produced identical HRF estimates, confirming the C010 approach is sufficient.

### Procrustes Alignment

Orthogonal transformation (rotation + reflection, no scaling) aligning runs 1-5 to run 0 reference (Gower & Dijksterhuis, 2004). Scaling is excluded to preserve the amplitude information that carries color-selective signal -- if patterns differ in magnitude across runs (e.g., due to attention or adaptation), scaling would conflate these with geometric misalignment. This removes geometric variance between runs, which is approximately 16x larger than color-selective signal in raw data -- the dominant source of noise in multi-run fMRI color experiments.

Procrustes disparity (sum of squared differences after optimal orthogonal transformation) averaged 0.00373 +/- 0.004 across all subject-ROI pairs, confirming good alignment quality. Values near zero indicate that the orthogonal transformation successfully captures the inter-run geometric relationship. The low disparity values across all 40 subject-ROI pairs suggest that the run-to-run geometric variance is well-characterized by rotation and reflection, without needing more complex transformation models.

### Forward Encoding Model

Six half-wave rectified Gaussian basis functions at [0, 60, 120, 180, 240, 300] degrees hue, each with 60-degree FWHM (Brouwer & Heeger, 2009). This 6-channel representation provides a smooth basis for the continuous color space, mapping 8 discrete stimuli onto a circular hue representation. Cross-validation: Leave-One-Run-Out (LORO, 6-fold). The encoding model learns voxel-to-channel weight matrices (W) that are later used in Phase 2b decoder comparison and Phase 3 filter design. The W matrices show high stability across LORO folds (cosine similarity 0.921 [0.907, 0.935]; see Phase 2b for validation).

### Noise Ceiling

Random split-half with Spearman-Brown correction (1,000 iterations). Data are randomly split into two halves of 3 runs each; RDM correlations computed within each half and correlated across halves. The Spearman-Brown formula corrects for the reduced reliability of half-length measurements, providing an estimate of full-data reliability. LOSO (leave-one-subject-out) bounds provide confidence ranges by computing the ceiling with each subject excluded.

## Results

### Raw vs. Procrustes Performance (N = 40 subject-ROI pairs)

| Metric | Raw C010 | C010 + Procrustes | Change |
|--------|----------|-------------------|--------|
| RDM correlation | 0.004 +/- 0.197 | **0.381 +/- 0.278** | +0.377 |
| Decoding accuracy | 0.131 +/- 0.049 | **0.592 +/- 0.121** | +0.461 |
| Procrustes disparity | -- | 0.00373 +/- 0.004 | -- |
| Positive subject-ROI pairs | 52.5% | **100%** | All positive |

Procrustes alignment is essential: +1644% improvement in RDM reliability at the pipeline level (0.028 to 0.487), with 100% of subject-ROI pairs showing positive effect. Without alignment, the geometric variance between runs dominates and all downstream analyses -- including SRM, decoders, and filter design -- perform at or near chance. The raw decoding accuracy of 0.131 is near the 0.125 chance level (1/8 colors), confirming that color information is present in the data but completely masked by inter-run geometric variance.

### By-ROI Performance (Procrustes-aligned)

| ROI | N | RDM Correlation (M +/- SD) | Accuracy (M +/- SD) | Noise Ceiling (M +/- SD) | RDM After Procrustes | % of Ceiling | LOSO Ceiling Bounds |
|-----|---|--------------------------|---------------------|------------------------|---------------------|-------------|---------------------|
| V1 | 10 | 0.313 +/- 0.215 | 0.560 +/- 0.138 | 0.582 +/- 0.172 | 0.160 +/- 0.154 | 24.2% | [0.16, 0.38] |
| V2 | 10 | 0.370 +/- 0.256 | 0.581 +/- 0.131 | 0.635 +/- 0.200 | 0.200 +/- 0.155 | 29.0% | [0.29, 0.43] |
| V3 | 10 | 0.316 +/- 0.328 | 0.613 +/- 0.130 | 0.525 +/- 0.226 | 0.173 +/- 0.174 | 23.2% | [0.22, 0.40] |
| hV4 | 9* | **0.541 +/- 0.283** | **0.613 +/- 0.092** | **0.697 +/- 0.168** | **0.315 +/- 0.186** | **41.8%** | [0.14, 0.36] |
| **Overall** | **39** | **0.381** | **0.592** | **0.610** | **0.212** | **29.6%** | -- |

*hV4 N = 9; sub-07 excluded (16 voxels, correlation distance underdetermined). The "RDM After Procrustes" column shows the per-subject split-half RDM correlation, which is the basis for the % of ceiling calculation.

hV4 shows the strongest color selectivity: highest RDM correlation (0.541), highest noise ceiling (0.697), highest ceiling utilization (41.8%), and most consistent decoding accuracy across subjects (lowest SD = 0.092). The LOSO bounds indicate that no single subject drives the noise ceiling estimates. V2 has the tightest LOSO bounds [0.29, 0.43], indicating the most stable ceiling estimate across subjects. The 29.6% per-subject ceiling utilization leaves substantial room for improvement, motivating the between-subject SRM approach in Phase 2. After SRM alignment, between-subject RDM agreement reaches 2.4-6.5x higher than Procrustes alone (see Phase 2).

### By-Group Performance (Procrustes-aligned)

| Group | N (pairs) | RDM Correlation (M +/- SD) | Accuracy (M +/- SD) |
|-------|-----------|--------------------------|---------------------|
| HC (sub-01 to sub-07) | 28 | 0.345 +/- 0.278 | 0.552 +/- 0.111 |
| CVD (sub-08 to sub-10) | 12 | 0.462 +/- 0.273 | 0.684 +/- 0.094 |
| Difference | -- | +0.117 | +0.132 (13.2 pp) |

CVD subjects show numerically higher decoding performance (+0.117 RDM, +13.2 percentage points accuracy). This may reflect higher signal quality, genuine representational differences, or sampling variability with only N = 3 CVD subjects. The group difference is descriptive only; no causal interpretation is warranted. Importantly, the direction of the difference (CVD >= HC) indicates that CVD subjects have *strong* color-selective signals -- the preprocessing pipeline does not disadvantage CVD data. This is a prerequisite for the filter design approach in Phase 3, which assumes CVD color representations exist but are geometrically distorted relative to HC rather than absent or degraded.

### Pipeline Comparison (N = 40)

| Pipeline | RDM Reliability | Noise Ceiling | Status |
|----------|---------------|---------------|--------|
| Raw C010 | 0.028 +/- 0.225 | -0.038 +/- 0.434 | Poor |
| **Raw -> Procrustes** | **0.487 +/- 0.253** | **0.613 +/- 0.248** | **Optimal** |
| Raw -> Whitening -> Procrustes | 0.036 +/- 0.153 | 0.020 +/- 0.182 | -92% (harmful) |
| Raw -> Procrustes -> Whitening | 0.259 +/- 0.245 | 0.352 +/- 0.315 | -47% (harmful) |

Whitening degrades performance regardless of application order: estimated covariance conflates signal and noise, removing spatial color structure. When applied before Procrustes (-92%), the corrupted covariance prevents effective alignment entirely. When applied after Procrustes (-47%), 77.5% of subject-ROI pairs were degraded. The covariance estimation is particularly unreliable in our setting because voxel counts (67-568) are moderate relative to the number of samples (48 per run), leading to ill-conditioned covariance matrices where signal and noise eigenvalues overlap.

### Additional Validation

- **Temporal stability**: Method difference = 0.101, confirming stable color-selective signals across time. This metric compares the first and second halves of data to ensure the color-selective patterns do not drift over the scanning session.
- **Drift validation**: 1st+2nd-level and 2nd-level-only drift models produced identical HRF estimates, confirming the C010 pipeline correctly handles temporal drift. The 2nd-level drift regressors are sufficient without requiring additional 1st-level detrending.
- **Pipeline-level vs. per-subject ceiling**: Pipeline-level RDM reliability (0.487) reaches 79% of noise ceiling (0.613), computed across all subjects. The per-subject split-half analysis (29.6%) is a more conservative metric that accounts for individual variability. The discrepancy arises because pipeline-level aggregation averages over subjects before computing correlations, while per-subject analysis computes correlations within each subject and then averages. Both metrics are informative: the pipeline-level comparison confirms that the preprocessing extracts most of the available color signal, while the per-subject analysis reveals the headroom for improvement that motivates SRM.
- **Onset randomization**: Not applicable. FIR basis with fixed ISI does not benefit from onset jitter, as the FIR model estimates the response at each time point independently.

## Discussion

1. **Procrustes alignment is essential.** Geometric variance between runs is approximately 16x larger than color-selective signal. Without alignment, all models perform at chance. With alignment, 100% of subject-ROI pairs show positive RDM reliability. The +1644% improvement (0.028 to 0.487) confirms that run-to-run geometric variability is the dominant noise source in multi-run fMRI color experiments, not measurement noise or hemodynamic variability.

2. **Whitening is harmful.** Both application orders (before and after Procrustes) degrade performance by 47-92%. The covariance estimate conflates signal with noise when voxel counts are moderate (67-568 voxels), a known limitation of empirical covariance estimation in high-dimensional settings with limited samples (Ledoit & Wolf, 2004). This finding led us to exclude whitening from all downstream analyses. Shrinkage-based estimation (Ledoit-Wolf) may perform better but was not tested.

3. **Confound regression is unnecessary.** Adding motion, tissue, or white-matter confounds to C010 reduces RDM by approximately 60%. The 2nd-level drift regressors are sufficient for detrending. This simplifies the pipeline and avoids removing shared variance that carries color-selective information -- a risk that is particularly acute in visual cortex where color-selective patterns may correlate with physiological signals.

4. **hV4 shows strongest color selectivity.** Highest RDM correlation (0.541), highest noise ceiling (0.697), and highest ceiling utilization (41.8%). This is consistent with hV4's known role as the primary color-selective area in human visual cortex (Brouwer & Heeger, 2009; Zeki et al., 1991). The low variability across subjects (SD = 0.092 for accuracy) suggests a consistent color processing architecture in hV4.

5. **Per-subject ceiling utilization is 29.6%.** The pipeline-level comparison (0.487 RDM vs. 0.613 ceiling = 79%) uses a different aggregation. The per-subject split-half analysis shows substantial room for improvement in representational fidelity, motivating the SRM approach in Phase 2 to leverage cross-subject information for denoising. After SRM alignment, HC-HC RDM correlations reach 77-81% of Phase 1 noise ceiling (V1 0.447/0.582, V2 0.517/0.635), confirming that SRM extracts most available color structure.

6. **CVD subjects show intact color-selective signals.** The numerically higher performance for CVD (accuracy 0.684 vs. HC 0.552) confirms that CVD brains have strong, decodable color representations. This is a prerequisite for the filter design approach in Phase 3, which assumes CVD color representations exist but are geometrically distorted relative to HC. Phase 2b's cross-decoding analysis (10/12 tests significant) further confirms this shared mapping.

## Limitations

- **Noise ceiling utilization**: 29.6% per-subject (split-half), leaving substantial room for improvement in representational fidelity. Between-subject alignment (Phase 2 SRM) partially addresses this gap by leveraging shared structure across subjects.
- **sub-07 hV4**: Excluded from noise ceiling analysis due to only 16 voxels in the C010 pipeline. All other ROIs retain N = 10. This exclusion propagates to all downstream analyses involving hV4 statistics.
- **Discrete stimuli**: Only 8 color stimuli, limiting the resolution of the color space that can be recovered. Continuous hue interpolation is addressed in Phase 2b (LOCO decoder comparison).
- **CVD group difference**: CVD numerically outperforms HC, but this is a group-level descriptive finding with N = 3 CVD; no causal interpretation is warranted. The direction rules out a CVD signal deficit but does not distinguish between sampling variability and genuine representational differences.
- **Single reference run**: Procrustes alignment uses run 0 as reference. Alternative reference selection strategies (e.g., mean template, iterative alignment) were not systematically compared, though the choice is unlikely to affect results given the symmetric nature of orthogonal Procrustes alignment.
- **Covariance estimation**: The failure of whitening may be specific to our voxel count range (67-568). With larger ROIs or more data, shrinkage-based covariance estimation (Ledoit-Wolf) might succeed, though this was not tested.

## References

- Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.
- Wang, L., et al. (2015). Probabilistic maps of visual topography in human cortex. *Cerebral Cortex*, 25(10), 3911-3931.
- Gower, J. C., & Dijksterhuis, G. B. (2004). *Procrustes Problems*. Oxford University Press.
- Zeki, S., et al. (1991). A direct demonstration of functional specialization in human visual cortex. *Journal of Neuroscience*, 11(3), 641-649.
- Ledoit, O., & Wolf, M. (2004). A well-conditioned estimator for large-dimensional covariance matrices. *Journal of Multivariate Analysis*, 88(2), 365-411.

---

**Last Updated**: 2026-03-03
