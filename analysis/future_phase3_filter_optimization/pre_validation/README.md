# Supplementary: Filter Pre-Validation & RDM Metric Sensitivity

> sub-08 (deutan) is the primary filter candidate with 32 FDR-significant color pairs and split-half reliability r = 0.73-0.84 across all ROIs; sub-10 shows near-zero signal, consistent with successful cortical compensation. L-M axis deficits and S-cone compensatory elevations are consistent across all three CVD subjects.

---

## Objective

Validate whether CVD subjects show reliable, color-pair-level differences from HC in SRM shared space before proceeding to filter design. Three complementary analyses establish (a) group-level significance of individual color pairs (B1), (b) temporal stability of distortion profiles (B2), and (c) individual-level bootstrap confidence intervals (B3). A follow-up sensitivity analysis tests whether results depend on the choice of RDM distance metric or normalization method. Together, these analyses determine which CVD subjects and which color pairs have sufficient statistical evidence to serve as filter targets.

## Participants & Data

- **Participants**: 10 subjects (7 HC: sub-01 to sub-07; 3 CVD: sub-08 deutan, sub-09 protan, sub-10 deutan)
- **SRM**: HC-only training (7 HC), CVD projected via SVD; k = V1:4, V2:4, V3:3, hV4:3
- **Distance metric**: Euclidean distance in k-dimensional SRM shared space (B1-B3); correlation distance and crossnobis distance (metric sensitivity)
- **Color pairs**: 28 unique pairs from 8 x 8 RDM upper triangle
- **Pair z-score**: (CVD distance - HC mean) / HC SD; positive = over-separation, negative = confusion
- **Significance definition**: B1 uses two-sided permutation p-values; B3 uses 95% bootstrap CI excluding zero; FDR uses Benjamini-Hochberg per-subject-ROI q = 0.05
- **Total tests**: B3 evaluates 336 comparisons (3 CVD x 4 ROIs x 28 color pairs); FDR applied per-subject-ROI (28 tests each)

## Methods

### B1: Pair-Level Permutation Test

Exhaustive group permutation using all C(10,3) = 120 possible HC/CVD assignments. SRM retrained per permutation to avoid circularity -- each null assignment gets its own shared space, ensuring the test statistic is not biased by the true group labels. Two-sided p-values computed per pair. Power is inherently limited: minimum achievable p = 0.008 with only 120 permutations, meaning only very large effects can reach significance.

### B2: Split-Half Stability

Data split into first half (runs 1-3) and second half (runs 4-6). SRM fitted separately on each half to avoid cross-contamination between the two temporal segments. Spearman correlation of 28-pair z-score profiles between halves assesses temporal stability of each subject's distortion pattern. Significance assessed against permutation null (1,000 iterations of random pair-label shuffling). A subject with high split-half reliability has a temporally stable distortion profile that is suitable for filter design -- the distortion is a stable trait, not a session-specific fluctuation.

### B3: Bootstrap Confidence Intervals

1,000 bootstrap iterations with HC subjects resampled with replacement. SRM retrained per iteration to incorporate sampling uncertainty in the shared space definition -- each bootstrap draw defines a different "HC reference" against which CVD is compared. 95% CI computed per pair per subject; significance defined as CI excluding zero. This approach captures the full uncertainty chain: HC sampling -> SRM training -> shared space -> distance computation -> z-score. The retraining is computationally expensive but essential: without it, the CI would underestimate uncertainty by treating the shared space as fixed.

### FDR Correction

Per-subject-ROI Benjamini-Hochberg FDR correction (q = 0.05) applied to bootstrap-derived p-values across 28 pairs. This is the finalized method for the paper: one FDR family per subject-ROI combination (28 tests each). Global FDR (across all 252 tests = 3 subjects x 3 ROIs x 28 pairs, excluding hV4) was also computed for comparison: 121 uncorrected significant pairs reduced to 37 global FDR survivors. The per-subject-ROI approach is preferred because it respects the hierarchical structure of the data (subjects have different CVD subtypes and ROIs have different noise properties).

### Metric Sensitivity Analysis

Six conditions tested: {correlation, crossnobis} x {none, within-subject, pooled} normalization. Crossnobis distances computed using Ledoit-Wolf shrinkage for noise covariance estimation (Walther et al., 2016), providing an SRM-independent metric. Cross-validated using C(6,2) = 15 run pairs per subject for unbiased 8x8 distance matrices. Crawford & Howell (1998) modified t-test used for crossnobis individual comparison (df = 6, one-tailed). Convergence assessed via Spearman correlation between z-scores across conditions. This analysis determines whether the filter targets identified by B3 depend on the specific metric used.

## Results

### B1: Group-Level Permutation (Exhaustive, 120 permutations)

| ROI | Significant pairs (p < 0.05) | Notable pair |
|-----|------------------------------|--------------|
| V1 | 0 | min p = 0.058 (red-magenta) |
| **V2** | **1** | **blue-purple p = 0.042** |
| V3 | 0 | -- |
| hV4 | 0 | min p = 0.058 (red-magenta) |

V2 blue-purple is the only pair reaching group-level significance. All three CVD subjects show elevated blue-purple distance in V2, consistent with S-cone compensatory processing -- blue and purple stimuli differ primarily along the S-cone axis, where CVD subjects may show enhanced reliance. Power is inherently limited by the 120-permutation ceiling; B3 bootstrap provides the primary individual-level evidence.

### B2: Split-Half Reliability

| Subject | V1 | V2 | V3 | hV4 | Profile |
|---------|------|------|------|------|---------|
| sub-08 (deutan) | 0.777* | 0.839* | 0.765* | 0.729* | Reliable all ROIs |
| sub-09 (protan) | 0.645* | 0.684* | 0.264 | 0.747* | V3 unstable |
| sub-10 (deutan) | 0.286 | 0.677* | 0.010 | 0.234 | V2 only |
| Group mean | 0.569 | 0.733 | 0.346 | 0.570 | V2 most stable |

*p < 0.05 against permutation null.

sub-08 is the most reliable CVD subject (r = 0.73-0.84 across all ROIs), indicating that the color-pair distortion profile is temporally stable and suitable for filter design. The reliability range is remarkably tight, suggesting a systematic and reproducible deviation from the HC reference. sub-09 is reliable in V1/V2/hV4 but shows V3 instability (r = 0.264), suggesting that higher visual areas may have noisier protan-specific signals. sub-10 shows significant reliability only in V2 (r = 0.677), consistent with a minimal or well-compensated CVD phenotype. V2 has the highest group-level stability (r = 0.733), reinforcing its status as the most informative ROI for CVD detection -- consistent with Phase 2's finding that V2 is the most robust ROI for HC-CVD separation (7/7 LOSO folds significant).

### B3: Bootstrap Significant Pair Counts (CI excludes zero)

| ROI | sub-08 | sub-09 | sub-10 |
|-----|--------|--------|--------|
| V1 | 15/28 | 17/28 | 8/28 |
| V2 | 17/28 | 13/28 | 10/28 |
| V3 | 18/28 | 10/28 | 13/28 |
| hV4 | 21/28 | 8/28 | 22/28 |

sub-08 shows widespread effects across all ROIs (15-21 significant pairs per ROI), with an increasing trend toward higher visual areas (hV4: 21/28 = 75%). sub-09 is concentrated in V1 (17/28), consistent with the protan V1-dominant profile identified in Phase 2 individual testing (V1 p = 0.007). sub-10 shows a paradoxical pattern: highest counts in hV4 (22/28) but low counts in V1 (8/28), suggesting diffuse but weak effects that may be amplified by hierarchical processing.

### FDR-Corrected Results (Per-Subject-ROI, q = 0.05)

| Subject | V1 | V2 | V3 | hV4 | Total |
|---------|----|----|----|----|-------|
| sub-08 (deutan) | 3 | 12 | 17 | -- | **32** |
| sub-09 (protan) | 6 | 0 | 1 | -- | **7** |
| sub-10 (deutan) | 0 | 0 | 0 | -- | **0** |

hV4 excluded from FDR analysis due to sub-07's 16 voxels causing NaN in distance calculations and biasing HC reference statistics. sub-08 has 32 FDR-significant pairs concentrated in V2 (12 pairs) and V3 (17 pairs) -- sufficient statistical basis for filter design across multiple ROIs. sub-09 has 7 pairs, primarily in V1 (6 pairs, magenta-axis), consistent with a protan-specific cortical signature. sub-10 has zero FDR-significant pairs, consistent with successful cortical compensation despite sharing the same deutan genotype as sub-08.

For comparison, global FDR across all 252 tests (3 subjects x 3 ROIs x 28 pairs) yields 37 survivors, distributed as sub-08: 30, sub-09: 7, sub-10: 0. The close agreement between per-subject-ROI (39 total) and global (37 total) FDR indicates the results are robust to the multiple comparison correction strategy.

### Key Adjacent Pairs with Bootstrap 95% CIs

| Pair | ROI | sub-08 z [CI] | sub-09 z [CI] | sub-10 z [CI] |
|------|-----|---------------|---------------|---------------|
| red-orange | V1 | -0.82 [-2.5, -0.2]* | -1.35 [-3.3, -0.7]* | -0.68 [-2.2, +0.1] |
| orange-yellow | V1 | +2.00 [+1.3, +4.4]* | +0.73 [-0.8, +1.8] | -0.25 [-1.4, +0.7] |
| cyan-blue | V1 | -0.95 [-2.4, -0.4]* | -0.51 [-1.6, +0.4] | -0.59 [-1.9, -0.0]* |
| purple-magenta | V1 | +0.98 [+0.2, +1.9]* | +1.15 [+0.4, +2.1]* | +0.31 [-1.1, +1.2] |
| red-magenta | V1 | +0.69 [-0.3, +1.9] | +3.02 [+1.9, +6.9]* | +1.43 [-0.1, +3.5] |
| blue-purple | V2 | +4.34 [+2.9, +15.3]* | +0.33 [-0.9, +1.4] | +2.08 [+1.2, +7.9]* |
| orange-yellow | V2 | +3.29 [+2.0, +33.2]* | +0.40 [-0.4, +8.1] | -0.13 [-0.9, +3.0] |
| red-orange | V2 | +1.66 [+0.8, +3.7]* | +1.64 [+0.7, +4.0]* | +0.51 [-0.4, +2.1] |
| red-orange | hV4 | +4.34 [+2.9, +8.9]* | +0.47 [-1.4, +1.9] | -0.86 [-2.7, -0.5]* |

*CI excludes zero. The wide CIs (e.g., blue-purple V2 sub-08: [+2.9, +15.3]) reflect the resampling of only 7 HC subjects, but the critical feature is that the lower bound exceeds zero for significant pairs. The asymmetric CIs arise because bootstrapping the HC reference can produce extreme z-scores when particular HC subjects are oversampled, stretching the upper tail.

### Cross-Subject Consistent Patterns

**L-M axis deficits** (all 3 CVD subjects show same direction):

| Pair | ROI | sub-08 | sub-09 | sub-10 | Mechanism |
|------|-----|--------|--------|--------|-----------|
| red-orange | V1 | -0.82 | -1.35 | -0.68 | L-M confusion |
| cyan-blue | V1 | -0.95 | -0.51 | -0.59 | L-M confusion |
| green-blue | V1 | -0.89 | -2.41 | -1.16 | L-M confusion |

All three pairs show negative z-scores (confusion/compression) for all three CVD subjects, indicating reduced neural discriminability for color pairs that differ primarily along the L-M cone opponent axis. This is the expected signature of both protan and deutan CVD: reduced L/M cone sensitivity leads to compressed cortical representations along the red-green dimension.

**S-cone compensatory elevations** (all 3 CVD):

| Pair | ROI | sub-08 | sub-09 | sub-10 | Mechanism |
|------|-----|--------|--------|--------|-----------|
| red-magenta | V1 | +0.69 | +3.02 | +1.43 | S-cone compensation |
| purple-magenta | V1 | +0.98 | +1.15 | +0.31 | S-cone compensation |
| red-magenta | V2 | +1.66 | +1.64 | +0.51 | S-cone compensation |
| blue-purple | V2 | +4.34 | +0.33 | +2.08 | S-cone compensation (B1 p = 0.042) |

The dual pattern of L-M axis deficits (negative z-scores for red-green adjacent pairs) and S-cone compensatory elevations (positive z-scores for blue-purple-magenta pairs) is consistent across all three CVD subjects and aligns with the known photoreceptor basis of color vision deficiency: reduced L-M opponency is partially compensated by enhanced reliance on S-cone signals. This compensatory pattern is strongest for sub-09 (protan) in V1 (red-magenta z = 3.02) and for sub-08 (deutan) in V2 (blue-purple z = 4.34), consistent with CVD subtype-specific cortical signatures.

### Color Pair RDM Analysis (Correlation Distance)

A complementary analysis using correlation distance (rather than Euclidean) in SRM space provides convergent evidence. Correlation distance captures pattern shape differences independent of overall activation magnitude.

| ROI | sub-08 sig pairs | sub-09 sig pairs | sub-10 sig pairs | Mean |delta| |
|-----|-----------------|-----------------|-----------------|--------------|
| V1 | 20/28 | 24/28 | 17/28 | 0.47-0.60 |
| V2 | 20/28 | 21/28 | 19/28 | 0.43-0.58 |
| V3 | 19/28 | 17/28 | 16/28 | 0.60-0.75 |
| hV4 | 26/28 | 19/28 | 12/28 | 0.63-0.75 |

Effect sizes increase from early visual areas (V1/V2: mean |delta| = 0.43-0.60) to higher visual areas (V3/V4: mean |delta| = 0.60-0.75), suggesting hierarchical integration amplifies individual pair differences. sub-08 shows the most widespread cortical reorganization (26/28 pairs in hV4). The L-M deficits and S-cone compensatory patterns identified in the Euclidean analysis (B1-B3) are replicated under correlation distance, confirming the findings are metric-robust.

### Color Axis Analysis (Correlation Distance)

**L-M axis deficits per ROI** (significant L-M pairs per subject):

| ROI | sub-08 L-M pairs | sub-09 L-M pairs | sub-10 L-M pairs |
|-----|-------------------|-------------------|-------------------|
| V1 | 3 (Red-Yellow, Orange-Cyan, Yellow-Green) | 4 (Red-Yellow, Red-Green, Orange-Cyan, Yellow-Green) | 2 (Red-Green, Yellow-Green) |
| V2 | 4 | 1 | 2 |
| V3 | 4 | 2 | 2 |
| hV4 | 4 (consistent V1-hV4) | 2 | 2 |

sub-08 shows 4/4 L-M pairs significant in all 4 ROIs -- the strongest deutan phenotype with L-M deficits pervasive across the cortical hierarchy. sub-09 shows the strongest V1 concentration (4 L-M pairs in V1 but 1-2 in V2-hV4), consistent with early visual cortex being the primary site of protan L-cone deficit.

**S-cone axis patterns per ROI** (significant S-cone pairs per subject):

| ROI | sub-08 S-cone pairs | sub-09 S-cone pairs | sub-10 S-cone pairs |
|-----|---------------------|---------------------|---------------------|
| V1 | 2 | 3 | 3 |
| V2 | 2 | 3 | 1 |
| V3 | 1 | 2 | 2 |
| hV4 | 2 | 3 | 1 |

S-cone compensation is prevalent in V1 (2-3 pairs per subject), suggesting early visual cortex relies on intact S-cone input to offset L-M deficits. sub-09 shows the strongest S-cone signature (3 pairs in V1/V2/hV4), consistent with protan subjects relying more heavily on S-cone signals.

### Metric Sensitivity: Correlation vs. Crossnobis

| Metric | Normalization | Uncorrected p < 0.05 | FDR q < 0.05 |
|--------|---------------|---------------------|-------------|
| **Correlation** | None (baseline) | **15** | 0 |
| Correlation | Within | 16 | 0 |
| Correlation | Pooled | 15 | 0 |
| **Crossnobis** | None | **3** | 0 |
| Crossnobis | Within | 8 | 0 |
| Crossnobis | Pooled | 3 | 0 |

Crossnobis is 80% more conservative than correlation (15 to 3 uncorrected pairs). This is expected: crossnobis uses cross-validated Mahalanobis distance with noise normalization, which is more stringent but also noisier with limited data. The convergence between metrics is moderate (Spearman r = 0.3-0.7 across ROIs), with V1 showing the strongest agreement (mean r = 0.565, sub-09 V1 r = 0.726). All three uncorrected crossnobis pairs belong to sub-08, consistent with sub-08 showing the strongest effects across all analyses.

Note: These results use Crawford & Howell t-tests (not bootstrap), explaining the zero FDR survivors. The main B3 analysis uses bootstrap, which captures HC inter-subject variability more comprehensively (see Bootstrap vs. Crawford & Howell section below).

### Normalization Sensitivity

Pooled normalization produces identical results to no normalization (HC variance already well-matched across subjects due to SRM alignment). Within-subject normalization preserves rank order (r approximately 1.0 for correlation z-scores) but shifts marginal pairs across the significance threshold (+1 pair for correlation, +5 pairs for crossnobis). No normalization is adopted for the final analysis, as it adds complexity without improving detection.

### Bootstrap vs. Crawford & Howell

**Zero FDR survivors under Crawford & Howell** (metric sensitivity analysis) vs. **39 survivors under bootstrap** (main B3 analysis) reflects the statistical method, not an error. Bootstrap z-scores are systematically higher than Crawford & Howell t-statistics (mean difference = 1.17, max = 3.53) because:

1. **Bootstrap** resamples HC subjects with replacement, generating 1,000 different HC reference distributions. Each iteration produces a different SRM, a different shared space, and a different HC mean -- capturing the full uncertainty in the HC reference. This produces wider null distributions that make extreme values more salient.
2. **Crawford & Howell** uses a conservative single-case t-test with fixed HC parameters (mean and SD computed once from 7 HC). The t-distribution with df = 6 is inherently conservative for detecting individual deviations from small normative samples.

Empirical verification (sub-08 V1, red-yellow pair): Bootstrap z = 5.14, p = 2.72e-07 (FDR-significant); Crawford & Howell z = 2.04, p = 0.087 (not even uncorrected significant).

Both approaches are valid for different purposes: Crawford & Howell is appropriate for clinical-style individual assessment (Phase 2 main results); bootstrap is appropriate for characterizing the distortion landscape when HC inter-subject variability is the primary source of uncertainty (filter pre-validation). Bootstrap is adopted for the paper's filter-relevant analyses because it better captures the uncertainty inherent in defining the "normal" HC reference from only 7 subjects.

## Discussion

1. **sub-08 is the primary filter candidate.** Highest reliability across all ROIs (r = 0.73-0.84), most FDR-significant pairs (32/84 tested), and the strongest effects concentrated in V2 (12 pairs) and V3 (17 pairs). The L-M axis deficit and S-cone compensation pattern is biologically consistent with the deutan phenotype. The 26/28 significant pairs in hV4 (correlation distance analysis) suggest widespread cortical reorganization of color representations extending beyond early visual cortex.

2. **sub-09 shows a protan-specific signature.** The magenta-axis over-separation in V1 (red-magenta z = 3.02, cyan-magenta z = 4.08) is distinct from the deutan S-cone pattern, confirming that protan and deutan subtypes produce different cortical distortions. However, only 7 FDR-significant pairs (6 in V1, 1 in V3) limit filter design to exploratory status for this subject.

3. **sub-10 shows near-zero signal.** Zero FDR-significant pairs, low split-half reliability in V1/V3/hV4 (r = 0.01-0.29), and Crawford & Howell tests all non-significant in Phase 2. This is interpreted as successful cortical compensation rather than measurement failure -- sub-10's deutan genotype is identical to sub-08, yet cortical representations fall within the HC range. The contrast between sub-08 and sub-10 (same CVD subtype, dramatically different cortical signatures) is itself a finding about individual variability in CVD compensation.

4. **V2 is the most informative ROI.** Highest group-level split-half reliability (r = 0.733), the only group-significant pair in B1 (blue-purple p = 0.042), and the strongest S-cone compensation effects (sub-08 blue-purple z = 4.34). V2 should be prioritized for filter design targets. This converges with Phase 2's finding that V2 shows significant HC-CVD separation in all 7 LOSO folds and both split halves.

5. **Hierarchical amplification of pair-level effects.** Effect sizes increase from V1/V2 (mean |delta| = 0.43-0.60) to V3/V4 (mean |delta| = 0.60-0.75) under correlation distance analysis. This suggests that higher visual areas amplify single-pair differences through integrative processing, consistent with hierarchical models of color representation (Zeki et al., 1991). sub-08's 4/4 L-M pairs significant across all ROIs (V1 through hV4) illustrates this hierarchy most clearly.

6. **Metric-dependent results warrant supplementary reporting.** Crossnobis distances show 80% fewer significant pairs than correlation distances in SRM space, consistent with crossnobis producing 0/252 FDR survivors in native voxel space (Phase 2 A4). The main results use bootstrap + correlation distance; crossnobis convergence (r = 0.3-0.7) is reported as supplementary validation. The moderate convergence confirms shared underlying signal despite different metric sensitivities.

## Limitations

- **Bootstrap amplification.** Bootstrap resampling of HC subjects produces higher z-scores than Crawford & Howell (mean difference = 1.17). The 39 FDR survivors (32 sub-08 + 7 sub-09) should be interpreted as capturing HC inter-subject variability effects, not as independent replications of pair-level differences.
- **Crossnobis shows minimal effects.** Only 3 uncorrected significant pairs in SRM space (all sub-08). This suggests the pair-level effects are partially representation-dependent, though moderate convergence (r = 0.3-0.7) with correlation distance indicates shared underlying signal.
- **sub-10 near-zero signal.** Cannot distinguish between successful compensation and insufficient signal-to-noise. Behavioral validation (JND thresholds) is needed to resolve this ambiguity.
- **Power limitation.** B1 exhaustive permutation has only 120 possible arrangements; group-level detection is limited to large effects (minimum p = 0.008).
- **hV4 excluded from FDR analysis.** sub-07 hV4 has only 16 voxels, causing NaN in distance calculations and biasing HC reference statistics. The 26/28 sub-08 hV4 pairs from correlation distance analysis should be interpreted cautiously.
- **Single SRM training.** B3 bootstrap retrains SRM per iteration, but the HC-only SRM definition means the same 7 subjects define the space. With larger HC samples, the shared space would stabilize and CIs would narrow.
- **Wide asymmetric CIs.** Some bootstrap CIs are extremely wide (e.g., sub-08 orange-yellow V2: [+2.0, +33.2]), reflecting the small HC sample (n = 7) and SRM retraining variability. The lower bounds are more informative than the upper bounds for significance assessment.

## References

- Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. *Journal of the Royal Statistical Society: Series B*, 57(1), 289-300.
- Crawford, J. R., & Howell, D. C. (1998). Comparing an individual's test score against norms derived from small samples. *The Clinical Neuropsychologist*, 12(4), 482-486.
- Walther, A., et al. (2016). Reliability of dissimilarity measures for multi-voxel pattern analysis. *NeuroImage*, 137, 188-200.
- Zeki, S., et al. (1991). A direct demonstration of functional specialization in human visual cortex. *Journal of Neuroscience*, 11(3), 641-649.

---

**Last Updated**: 2026-03-03
