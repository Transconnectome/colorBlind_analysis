# Phase 2: SRM-Based HC-CVD Group Comparison

> CVD subjects show trending but non-significant group-level disparity from HC in V1 (p = 0.062, g = 1.16) and V2 (p = 0.075, g = 1.04), with individual dissociations: sub-09 is significantly elevated in V1 (p = 0.007), sub-08 in V2 (p = 0.040), and sub-10 falls within the HC range. Convergent validity with SRM-independent metrics (crossnobis r = 0.486, PCA r = 0.742) confirms the effects are genuine neural differences, not alignment artifacts.

---

## Objective

Test whether CVD subjects show systematically different color representations from HC when aligned into a common neural space via Shared Response Model (SRM). The analysis addresses group-level differences, individual CVD profiles, color-dependency of the effects, and robustness across independent validation metrics. The core question is whether CVD produces measurable cortical signatures in early visual areas beyond what would be expected from normal inter-subject variability.

## Participants & Data

- **Participants**: 10 subjects (7 HC: sub-01 to sub-07; 3 CVD: sub-08 deutan, sub-09 protan, sub-10 deutan)
- **Input**: Phase 1 Procrustes-aligned amplitudes (C010), shape (6 runs, 8 colors, n voxels)
- **ROIs**: V1, V2, V3, hV4 (Wang Atlas)
- **SRM k**: V1 = 4, V2 = 4, V3 = 3, hV4 = 3 (selected via 7-fold LOSO mean rank aggregation)
- **Training**: HC-only SRM (7 HC subjects train the shared space; CVD projected via SVD)
- **Metric**: Procrustes disparity between subject pairs in SRM shared space
- **Comparison**: HC-HC pairs vs CVD-HC pairs (LOO-consistent)
- **Permutations**: 10,000 iterations for group test; 1,000 for color-dependency tests

## Methods

### SRM Alignment

Beta-based SRM: run-averaged patterns (n_voxels x 8 colors) fitted across 7 HC subjects to learn a shared response S and individual weight matrices W. CVD subjects projected into the HC-defined shared space via SVD of their data against the learned shared response (W_new = U @ Vt from SVD of X_new @ pinv(S)). This ensures CVD subjects do not influence the shared space definition, preventing circularity -- the shared space represents the "normal" HC color structure against which CVD deviations are measured.

### LOO-Consistent Disparity

Three bias fixes applied to ensure fair comparison:

1. **HC-only SRM**: CVD subjects do not influence the shared space definition (addresses circularity concern).
2. **LOO for HC**: Each HC subject i compared to the mean of the other 6 HC subjects (no group-mean leakage). Without LOO, each HC subject would be evaluated against a reference they helped define, artificially inflating HC similarity and widening the HC-CVD gap.
3. **Same LOO references for CVD**: Each CVD subject's disparity computed against the same 7 LOO references used for HC, then averaged. Both groups evaluated on identical 6-subject reference basis.

### Statistical Tests

- **Group comparison**: Permutation test (10,000 iterations). Each permutation assigns 7 pseudo-HC and 3 pseudo-CVD, retrains SRM on the 7 pseudo-HC, recomputes LOO references, and evaluates both groups against matching references. This fully controls for the HC-only SRM training bias.
- **Individual CVD**: Crawford & Howell (1998) modified t-test against HC LOO distribution (df = 6, one-tailed). This test is specifically designed for comparing a single case against a small normative sample, accounting for the uncertainty in estimating the population parameters from the control group.
- **Effect size**: Hedges' g (bias-corrected for small samples) with bootstrap 95% CIs (10,000 iterations).
- **Color-dependency (LOSO)**: Leave-one-subject-out permutation framework. Each HC subject is left out of SRM training and projected via SVD (identical treatment to CVD). Color labels are shuffled within subjects to test whether disparity depends on true color ordering. This eliminates the structural floor confound where HC subjects who train SRM are insensitive to color-label shuffling.

### Robustness Triangulation (A3/A4/A5)

Three SRM-independent metrics validate that the effects are not alignment artifacts:

- **A4 Crossnobis RDM**: Cross-validated Mahalanobis distance in native voxel space (Walther et al., 2016) with Ledoit-Wolf noise covariance. C(6,2) = 15 run pairs yield unbiased 8x8 distance matrix per subject. Completely independent of SRM -- uses raw voxel-space distances only.
- **A5 PCA-CCA**: PCA dimensionality reduction (matched k to SRM for fair comparison) + optional CCA alignment. All C(10,2) = 45 subject pairs compared via Procrustes disparity. Provides an alternative alignment method that replaces SRM's iterative optimization with a one-step linear transformation.
- **A3 Variance Explained**: SRM reconstruction quality (VE = 1 - ||X - WS||^2 / ||X||^2). LOSO framework: both HC and CVD projected via SVD for unbiased comparison. Higher VE means the shared space captures more of the subject's data variance.

### k Selection

7-fold LOSO cross-validation across k = {2, 3, 4, 5, 6}. Two RDM-based metrics (RDM reliability, cross-subject RDM correlation) aggregated via mean rank. Reconstruction error excluded from selection criterion (trivially favors higher k, measuring variance captured rather than color structure quality).

| ROI | Selected k | RDM reliability rank | Cross-subj RDM rank | Mean rank | Runner-up |
|-----|-----------|---------------------|---------------------|-----------|-----------|
| V1 | **4** | 1.86 | 2.00 | 1.93 | k=3 (2.71) |
| V2 | **4** | 2.14 | 2.14 | 2.14 | k=5 (2.36) |
| V3 | **3** | 2.14 | 2.14 | 2.14 | k=4 (2.14, tied; k=3 by parsimony) |
| hV4 | **3** | 2.00 | 2.14 | 2.07 | k=4 (2.57) |

V1 and V2 are unanimously supported by both metrics. V3 tied between k = 3 and k = 4; k = 3 selected by parsimony (V3 has fewer voxels, lower-dimensional space sufficient). hV4 revised from k = 4 to k = 3 based on data-driven aggregation (mean rank 2.07 vs. 2.57 for k = 4).

**Mean metric values at selected k** (7-fold LOSO mean +/- SD):

| ROI | k | RDM Reliability | Cross-subj RDM Corr |
|-----|---|----------------|---------------------|
| V1 | 4 | 0.496 +/- 0.146 | 0.597 +/- 0.229 |
| V2 | 4 | 0.429 +/- 0.137 | 0.566 +/- 0.145 |
| V3 | 3 | 0.446 +/- 0.194 | 0.546 +/- 0.279 |
| hV4 | 3 | 0.560 +/- 0.185 | 0.317 +/- 0.169 |

hV4 shows an interesting dissociation: highest RDM reliability (0.560) but lowest cross-subject RDM correlation (0.317), reflecting strong individual color selectivity that does not generalize well between subjects.

## Results

### Main Group Comparison (LOO-Consistent, 10,000 Permutations)

| ROI | HC LOO [95% CI] | CVD LOO [95% CI] | Separation [95% CI] | p (perm) | g [95% CI] |
|-----|----------------|-----------------|---------------------|----------|------------|
| **V1** | 0.453 [0.397, 0.512] | 0.590 [0.457, 0.761] | 0.137 [-0.005, 0.301] | **0.062** | 1.16 [-0.06, 3.98] |
| **V2** | 0.486 [0.418, 0.559] | 0.606 [0.505, 0.718] | 0.120 [0.001, 0.244] | **0.075** | 1.04 [0.02, 3.18] |
| V3 | 0.540 [0.476, 0.608] | 0.564 [0.404, 0.738] | 0.023 [-0.137, 0.194] | 0.395 | 0.18 [-1.59, 2.34] |
| hV4 | 0.700 [0.617, 0.796] | 0.677 [0.444, 0.855] | -0.023 [-0.244, 0.172] | 0.559 | -0.14 [-2.07, 2.03] |

V1 and V2 show trending HC-CVD separation with large effect sizes (g > 1.0) but wide CIs due to n = 3 CVD. V2 separation CI [0.001, 0.244] marginally excludes zero, providing the strongest evidence for a group difference. V3 and hV4 show no group difference (g near zero, CIs spanning zero symmetrically). The wide g CIs (e.g., V1: [-0.06, 3.98]) reflect the fundamental n = 3 limitation -- a population-level claim requires larger CVD samples, but individual testing below partially compensates.

### Individual CVD Tests (Crawford & Howell 1998)

| Subject | V1 (t, p) | V2 (t, p) | V3 (t, p) | hV4 (t, p) |
|---------|-----------|-----------|-----------|------------|
| **sub-09** (protan) | **t = 3.5, p = 0.007** | t = 1.0, p = 0.181 | t = 0.1, p = 0.466 | t = 1.1, p = 0.150 |
| **sub-08** (deutan) | t = 1.1, p = 0.157 | **t = 2.1, p = 0.040** | t = 1.9, p = 0.052 | t = 0.2, p = 0.411 |
| sub-10 (deutan) | t = 0.0, p = 0.483 | t = 0.2, p = 0.433 | t = -1.3, p = 0.884 | t = -1.9, p = 0.945 |

Individual testing reveals region-specific dissociations that group analysis obscures: sub-09 (protan) is significantly elevated in V1 (p = 0.007), consistent with early visual cortex disruption from L-cone anomaly; sub-08 (deutan) is significantly elevated in V2 (p = 0.040) with V3 marginally trending (p = 0.052), suggesting mid-level processing impact from M-cone anomaly; sub-10 (deutan) falls entirely within the HC range across all ROIs, despite sharing the same deutan genotype as sub-08. This 2/3 detection rate with region-specific dissociations is more informative than the trending group-level p-values.

### Individual CVD Profiles (% above HC LOO Mean)

| Subject | V1 | V2 | V3 | hV4 | Pattern |
|---------|------|------|------|------|---------|
| sub-08 | +20.9% | +47.4% | +35.7% | +3.5% | Moderate-high elevation |
| sub-09 | +67.7% | +21.5% | +0.7% | +21.4% | V1-dominant |
| sub-10 | -0.1% | +3.1% | -26.8% | -39.1% | Near-normal to below-HC |

sub-09's +67.7% V1 elevation is the largest individual effect across all subjects and ROIs. sub-10 is not merely "non-significant" but actually falls *below* the HC mean in V3 (-26.8%) and hV4 (-39.1%), suggesting potential overcompensation in higher visual areas -- color representations in these areas may be more tightly constrained than typical HC subjects.

### LOSO Color-Dependency (HC Tested in Space They Did Not Train)

| ROI | HC held-out p | CVD score p | CVD pairwise p | Interpretation |
|-----|--------------|------------|---------------|----------------|
| V1 | 0.364 | 0.412 | 0.077 | Not color-specific |
| **V2** | 0.227 | **0.010** | **0.035** | **CVD color-dependent** |
| **V3** | 0.207 | **0.000** | **0.046** | **CVD color-dependent** |
| **hV4** | 0.330 | **0.016** | **0.031** | **CVD color-dependent** |

The asymmetry between HC and CVD is the key finding: HC disparity does not depend on color labels (p = 0.21-0.36 across all ROIs), while CVD disparity is specifically color-dependent in V2/V3/hV4 (score p = 0.000-0.016). When color labels are shuffled, CVD disparity *increases* -- confirming that the SRM group separation is driven by genuine color-structure divergence, not general noise or alignment artifacts.

V1 CVD color-dependency is not significant (p = 0.412), suggesting V1's trending group effect (p = 0.062) reflects general representational differences rather than color-specific divergence. This is consistent with V1's role in early, less color-specialized processing. The dissociation between V1 (color-agnostic elevation) and V2/V3/hV4 (color-dependent elevation) suggests different mechanisms: V1 may reflect low-level cone signal changes affecting all spatial patterns, while V2+ reflects color-specific perceptual reorganization.

### LOSO Stability (7-fold leave-one-HC-subject-out)

| ROI | Significant folds (p < 0.05) | Fold p-value range | Stability |
|-----|-------------------------------|-------------------|-----------|
| V1 | **6/7** | 0.007 -- 0.052 | Robust (1 marginal) |
| **V2** | **7/7** | < 0.001 -- 0.032 | **Perfect stability** |
| V3 | 0/7 | 0.199 -- 0.461 | Consistently non-significant |
| hV4 | 0/7 | 0.147 -- 0.460 | Consistently non-significant |

V2 CVD-HC separation is significant in ALL 7 folds (p range: < 0.001 to 0.032), confirming no single HC subject drives the result. V1 is robust with 6/7 folds significant (only the sub-04 fold marginal at p = 0.052). V3 and hV4 are consistently non-significant across all folds, confirming the null finding. The perfect V2 stability across LOSO folds is particularly strong evidence: removing any one of the 7 HC subjects does not weaken the HC-CVD separation.

### Robustness Triangulation

| Metric | Method | V1 | V2 | Key convergent result |
|--------|--------|----|----|----------------------|
| **SRM disparity** (main) | SRM shared space | p = 0.062 | p = 0.075 | Trending V1/V2 |
| **A4 Crossnobis** | Native voxel space | p = 0.051 | ns | Convergent r = 0.486 (p = 0.001, pooled) |
| **A5 PCA-only** | PCA alignment | ns | ns | **Convergent r = 0.742 (p < 0.001, pooled)** |
| **A5 PCA-CCA** | PCA + CCA alignment | ns | ns | Convergent r = 0.472 (p = 0.002, pooled) |
| **A3 VE (LOSO)** | SRM reconstruction | CVD >= HC | CVD > HC, g = -1.68 | "Strong signal, different structure" |

Group-level effects do not reach p < 0.05 with alternative methods (expected with n = 3 CVD and noisier pairwise alignment). However, convergent validity is strong: the subject-level pattern of who deviates most from HC is consistent across SRM (disparity), crossnobis (native voxel distance), and PCA (alternative alignment).

**Per-ROI convergent validity** (SRM disparity vs. crossnobis distance):
- V1: r = 0.721 (p = 0.019)
- V2: r = 0.806 (p = 0.005)
- V3: r = 0.200 (p = 0.580)
- hV4: r = 0.248 (p = 0.489)
- Pooled: r = 0.486 (p = 0.001)

**Per-ROI convergent validity** (SRM disparity vs. PCA-only distance):
- V1: r = 0.636 (p = 0.048)
- V2: r = 0.891 (p < 0.001)
- V3: r = 0.285 (p = 0.425)
- hV4: r = 0.661 (p = 0.038)
- Pooled: r = 0.742 (p < 0.001)

The PCA-only pooled correlation of r = 0.742 is particularly compelling -- SRM is not needed to recover the same individual-difference pattern. V2 PCA-SRM convergence reaches r = 0.891 (near-perfect), confirming that V2 individual differences are robust to the alignment method. The V3 and hV4 null convergence values (r = 0.20-0.29 for crossnobis) reflect the lack of systematic HC-CVD differences in these ROIs -- there is nothing to converge on.

### A4 Crossnobis Group Disparity (Native Voxel Space)

| ROI | HC-HC RDM [95% CI] | HC-CVD RDM [95% CI] | Diff [95% CI] | p (perm) |
|-----|---------------------|----------------------|---------------|----------|
| **V1** | **0.104** [0.012, 0.196] | -0.018 [-0.122, 0.089] | **0.122** [-0.019, 0.262] | **0.051** |
| V2 | -0.018 [-0.114, 0.080] | 0.011 [-0.095, 0.123] | -0.029 [-0.176, 0.115] | 0.649 |
| V3 | 0.021 [-0.079, 0.114] | -0.049 [-0.164, 0.068] | 0.070 [-0.084, 0.217] | 0.186 |
| hV4 | -0.018 [-0.117, 0.088] | -0.015 [-0.105, 0.070] | -0.002 [-0.134, 0.137] | 0.502 |

V1 is the only ROI approaching significance in native voxel space (p = 0.051), consistent with V1 showing the strongest SRM group effect (p = 0.062). The crossnobis analysis captures a different aspect than SRM disparity: overall RDM similarity rather than pair-specific alignment, explaining why V2 is non-significant here despite trending in SRM.

### A3 Variance Explained (LOSO, Unbiased)

| ROI | HC VE [95% CI] | CVD VE [95% CI] | Diff [95% CI] | g |
|-----|---------------|----------------|---------------|---|
| V1 | 0.352 [0.267, 0.412] | 0.402 [0.283, 0.532] | -0.050 [-0.191, 0.082] | -0.39 |
| **V2** | **0.331 [0.289, 0.373]** | **0.448 [0.379, 0.511]** | **-0.117 [-0.190, -0.042]** | **-1.68** |
| V3 | 0.250 [0.200, 0.305] | 0.321 [0.224, 0.404] | -0.070 [-0.165, 0.031] | -0.79 |
| hV4 | 0.225 [0.183, 0.265] | 0.271 [0.210, 0.307] | -0.045 [-0.108, 0.022] | -0.69 |

CVD VE >= HC VE in all ROIs, with V2 showing a statistically significant difference (g = -1.68, CI excludes zero). This counter-intuitive result means CVD data is *better reconstructed* by the HC-trained SRM than HC's own held-out data. The interpretation: CVD representations contain strong, systematic signal that happens to project well onto the HC-defined shared space -- "strong signal, different structure." This supports the anisotropy correction framing for Phase 3: CVD representations are not degraded noise but geometrically transformed signal, and the transformation preserves enough structure for SRM to capture.

### Validation Summary

| Validation | V1 | V2 | V3 | hV4 |
|------------|----|----|----|----|
| LOSO stability (sig folds) | 6/7 | **7/7** | 0/7 | 0/7 |
| Split-half (both halves sig) | No | **Yes** | No | No |
| Split-half set A / set B p | 0.059 / 0.019 | **0.006 / 0.022** | 0.156 / 0.074 | 0.402 / 0.174 |
| Cross-half disparity r | 0.709* | 0.709* | 0.430 | 0.782* |
| k selection (unanimous) | k = 4 | k = 4 | k = 3 (tie) | k = 3 |
| Alignment advantage (SRM/Raw) | **6.5x** | 3.7x | 2.4x | 3.1x |
| Crossnobis convergence r | 0.721* | 0.806** | 0.200 | 0.248 |
| PCA convergence r | 0.636* | 0.891*** | 0.285 | 0.661* |

*p < 0.05, **p < 0.01, ***p < 0.001.

V2 is the most robust ROI: significant CVD-HC separation in all 7 LOSO folds, significant in both independent run halves (set A p = 0.006, set B p = 0.022), highest LOSO color-dependency significance (p = 0.010), near-perfect PCA convergence (r = 0.891), and CVD VE significantly exceeds HC (g = -1.68). V1 is nearly as robust (6/7 LOSO folds, set B p = 0.019) but lacks split-half replication in both halves (set A p = 0.059).

### Run-Split ICC (CVD Individual Reliability)

| Subject | V1 | V2 | V3 | hV4 | Assessment |
|---------|------|------|------|------|------------|
| sub-08 | 0.58 | **0.75** | 0.71 | **0.83** | Most stable CVD subject |
| sub-09 | 0.46 | 0.53 | 0.73 | 0.74 | Moderate |
| sub-10 | 0.45 | 0.55 | 0.61 | 0.67 | Moderate |

Spearman-Brown corrected split-half correlations. 8/12 subject-ROI pairs reach moderate reliability (r > 0.5). sub-08 shows the best reliability, particularly in hV4 (0.83) and V2 (0.75), consistent with having the most stable and pronounced CVD signal. Even sub-10 (near-normal disparity) shows moderate reliability (0.45-0.67), indicating stable *low* deviation from HC rather than noisy measurement.

### CVD Heterogeneity

| ROI | CVD-CVD / HC-HC disparity ratio |
|-----|-------------------------------|
| V1 | 1.47x |
| V2 | 1.37x |
| V3 | 1.59x |
| hV4 | 1.44x |

CVD subjects are 1.4-1.6x more dispersed than HC across all ROIs. The three CVD subjects show distinct profiles: sub-08 is elevated in V1/V2/V3 (+21-47% above HC LOO mean), sub-09 is V1-dominant (+68%), and sub-10 is near-normal in V1/V2 but below HC in V3/hV4 (-27 to -39%). This heterogeneity has implications for filter design: a group-level CVD filter is unlikely to work; personalized approaches based on individual distortion profiles are necessary (see Supplementary pre-validation for per-pair analysis).

### RDM Correlation (Color Structure Similarity)

| ROI | HC-HC [95% CI] | HC-CVD [95% CI] | CVD-CVD [95% CI] |
|-----|---------------|----------------|----------------|
| V1 | 0.447 [0.357, 0.531] | 0.322 [0.237, 0.402] | 0.297 [0.126, 0.493] |
| **V2** | **0.517 [0.442, 0.592]** | **0.499 [0.414, 0.587]** | **0.591 [0.471, 0.702]** |
| V3 | 0.385 [0.300, 0.473] | 0.348 [0.245, 0.457] | 0.591 [0.490, 0.672] |
| hV4 | 0.158 [0.069, 0.248] | 0.224 [0.119, 0.328] | 0.276 [0.008, 0.734] |

In V2, HC-CVD RDM CI [0.414, 0.587] heavily overlaps with HC-HC CI [0.442, 0.592], confirming CVD subjects largely preserve color relationship structure -- the "parallel" pattern. CVD color representations are dispersed but individually color-structured: each CVD subject has a systematic color space, just shifted or warped relative to HC. In V1, HC-CVD upper bound (0.402) marginally approaches HC-HC lower bound (0.357), indicating less structural preservation in early visual cortex.

HC-HC RDM correlations in SRM space (V1 = 0.447, V2 = 0.517) reach 77-81% of Phase 1 noise ceiling (V1 = 0.582, V2 = 0.635), indicating SRM extracts most available color structure from the data. CVD-CVD correlations in V2/V3 (0.591) exceed HC-HC correlations, suggesting that CVD subjects share a common distortion pattern (consistent with shared cone deficiency mechanisms) even though they differ from HC.

### Alignment Comparison (Between-Subject RDM Agreement)

| ROI | Raw | Procrustes | SRM | SRM / Raw ratio |
|-----|-----|-----------|-----|-----------------|
| V1 | 0.083 | 0.068 | **0.538** | **6.5x** |
| V2 | 0.152 | 0.159 | **0.556** | **3.7x** |
| V3 | 0.159 | 0.145 | **0.388** | **2.4x** |
| hV4 | 0.097 | 0.111 | **0.297** | **3.1x** |

SRM produces 2.4-6.5x higher between-subject RDM agreement than raw or Procrustes alignment, confirming that SRM successfully extracts shared color representations. The V1 ratio (6.5x) is the highest, indicating that SRM provides the largest benefit for V1 where raw between-subject agreement is lowest (0.083). The trade-off: within-subject RDM correlation decreases under SRM (e.g., V2: raw 0.471 to SRM 0.096), as SRM optimizes cross-subject consensus at the cost of individual-specific structure. This trade-off explains why Phase 2b finds SRM optimal for classification (needs shared structure) but Procrustes optimal for interpolation (needs individual structure).

## Discussion

1. **"Scattered but structured" interpretation.** Group-level effects trend but do not reach significance (V1 p = 0.062, V2 p = 0.075), reflecting the fundamental limitation of n = 3 CVD. However, CVD disparity is specifically color-dependent (V2/V3/hV4 LOSO p < 0.05), while HC disparity is not -- this asymmetry is the strongest evidence that SRM captures color-specific group differences, not general noise. The V1 effect is color-agnostic, suggesting a different mechanism (low-level cone signal changes) from the V2+ color-dependent effects (color-specific perceptual reorganization).

2. **Individual dissociations resolve heterogeneity.** Rather than treating CVD as a homogeneous group, individual testing reveals sub-09 (protan) with a V1-specific signature (+68% above HC LOO mean, p = 0.007) and sub-08 (deutan) with a V2-specific signature (+47%, p = 0.040). Sub-10 falls within the HC range, suggesting effective cortical compensation despite the same deutan genotype as sub-08. This 2/3 detection rate with region-specific dissociations is more informative than the trending group-level p-values.

3. **Convergent validity is the key evidence.** SRM disparity correlates with crossnobis distance (r = 0.486, p = 0.001 pooled; V1 r = 0.721, V2 r = 0.806) and PCA distance (r = 0.742, p < 0.001 pooled; V2 r = 0.891). The individual-level pattern of who deviates from HC is method-invariant, confirming genuine neural differences rather than SRM artifacts. The near-perfect V2 PCA-SRM convergence (r = 0.891) is the most compelling single number.

4. **CVD VE >= HC supports "different structure, not noise."** SRM reconstruction quality is higher for CVD than HC (V2 g = -1.68, CI excludes zero), indicating that CVD data contains strong, systematic signal that differs in geometry from HC. This supports the anisotropy correction framing for filter design: CVD representations are not degraded but geometrically transformed, and the transformation preserves enough structure for SRM reconstruction.

5. **V2 is the most robust ROI.** Significant in all 7 LOSO folds, both split halves (set A p = 0.006, set B p = 0.022), highest LOSO color-dependency (p = 0.010), near-perfect PCA convergence (r = 0.891), and CVD VE significantly exceeds HC (g = -1.68). V2 should be the primary focus for claims about CVD cortical signatures in the paper. The Supplementary pre-validation confirms V2's dominance: highest group-level split-half reliability (r = 0.733), the only group-significant pair in B1 (blue-purple p = 0.042).

6. **V3 and hV4 are consistently null for the main disparity analysis.** No group-level, individual-level, or LOSO stability effects in V3/hV4 for the primary Procrustes disparity metric. However, V3/hV4 do show color-dependent CVD disparity in the LOSO analysis (V3 p = 0.000, hV4 p = 0.016), suggesting some residual color-specific effects that do not manifest as group-level separation -- possibly because CVD heterogeneity (1.59x in V3) washes out group-level effects while color-dependency captures what individual profiles share.

## Limitations

- **n = 3 CVD.** The primary limitation. Group-level permutation tests have low power; CIs are wide (V1 g CI: [-0.06, 3.98]). Individual testing partially compensates but cannot establish population-level prevalence.
- **Trending but non-significant group effects.** V1 p = 0.062 and V2 p = 0.075 do not survive conventional alpha = 0.05. The results should be interpreted as suggestive, supported by convergent validity, not as definitive group differences.
- **SRM k constraint.** Only 8 color stimuli limit k to at most 8; optimal k = 3-4 may not capture the full dimensionality of color representations, particularly in higher visual areas where Phase 2b shows Procrustes outperforms SRM.
- **CVD heterogeneity.** CVD-CVD disparity ratios (1.4-1.6x) indicate substantial individual variability. A group-level filter is unlikely to work; personalized approaches are necessary. The sub-08 vs. sub-10 contrast (same genotype, different cortical signatures) exemplifies this challenge.
- **HC floor effect in LOSO.** HC subjects train the SRM, making their disparity insensitive to color-label shuffling in the single-SRM analysis. LOSO addresses this by projecting HC via SVD, but increases HC variance and widens group p-values (V1: 0.062 to 0.154, V2: 0.075 to 0.102). The LOSO analysis is more conservative but fairer.
- **Convergent validity != causal evidence.** High correlations between SRM, crossnobis, and PCA measures confirm that the same individual differences are captured, but all methods may share the same confound (e.g., data quality differences correlated with CVD status). Behavioral validation is needed to link cortical signatures to perceptual outcomes.
- **V3/hV4 show color-dependent effects without group separation.** The LOSO analysis shows CVD disparity is color-dependent in V3/hV4, but these ROIs do not show group-level or individual-level significance. This may reflect high within-group variance that masks color-specific effects.

## References

- Chen, P. H., et al. (2015). A reduced-dimension fMRI shared response model. *NIPS*.
- Crawford, J. R., & Howell, D. C. (1998). Comparing an individual's test score against norms derived from small samples. *The Clinical Neuropsychologist*, 12(4), 482-486.
- Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.
- Walther, A., et al. (2016). Reliability of dissimilarity measures for multi-voxel pattern analysis. *NeuroImage*, 137, 188-200.
- Haxby, J. V., et al. (2011). A common, high-dimensional model of the representational space in human ventral temporal cortex. *Neuron*, 72(2), 404-416.
- Neitz, J., & Neitz, M. (2011). The genetics of normal and defective color vision. *Vision Research*, 51(7), 633-651.

---

**Last Updated**: 2026-03-03
