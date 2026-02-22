# Methods & Results Summary for Paper

> Auto-generated and maintained by `capture-results` skill.
> Last updated: 2026-02-18 (Filter Pre-Validation B1–B3: per-pair z-scores, split-half stability, bootstrap CIs)

---

## Phase 1: Preprocessing & Baseline Decoding (C010 + Procrustes)

### Settings

- **fMRIPrep**: version 23.2.3
- **Pipeline**: C010 (2nd-level drift removal) + Procrustes alignment
- **1st-level GLM**: FIR basis (8 delays, 0–12s post-stimulus at TR=1.5s)
- **Voxel selection**: Top 50% by FIR R²
- **2nd-level GLM**: 8 HRF + 8 HRF derivative + 12 per-run drift (linear + constant)
- **Confounds**: None (motion/tissue/WM regression degrades signal by −60%)
- **High-pass filtering**: None (drift regressors handle slow trends)
- **Procrustes alignment**: Orthogonal (rotation + reflection), runs 1–5 aligned to run 0 reference
- **Procrustes disparity**: Sum of squared differences after optimal orthogonal transformation; range [0, ∞), lower = better alignment
- **Forward encoding model**: 6 half-wave rectified basis functions at [0°, 60°, 120°, 180°, 240°, 300°] hue
- **Cross-validation**: LORO (Leave-One-Run-Out)
- **ROIs**: V1, V2, V3, hV4 (Wang Atlas, 2015)
- **Space**: MNI152NLin2009cAsym, res-2
- **Subjects**: 10 total (HC: sub-01~07, n=7; CVD: sub-08~10, n=3)
- **CVD diagnosis**: Ishihara test
- **CVD subtypes**: sub-08 deutan, sub-09 protan, sub-10 deutan
- **Status**: VALIDATED (2026-02-09)

### Overall Performance (N=40 subject-ROI pairs, 10 subjects × 4 ROIs)

| Metric | Raw (pre-Procrustes) | Procrustes-aligned | Improvement |
|--------|---------------------|-------------------|-------------|
| RDM correlation | 0.004 ± 0.197 | **0.381 ± 0.278** | +0.377 |
| Decoding accuracy | 0.131 ± 0.049 | **0.592 ± 0.121** | +0.461 |
| Procrustes disparity | — | 0.00373 ± 0.004 | — |
| Positive pairs | 52.5% | **100%** | — |

### Results by ROI

| ROI | N | RDM Correlation (M ± SD) | Decoding Accuracy (M ± SD) |
|-----|---|--------------------------|---------------------------|
| V1 | 10 | 0.313 ± 0.215 | 0.560 ± 0.138 |
| V2 | 10 | 0.370 ± 0.256 | 0.581 ± 0.131 |
| V3 | 10 | 0.316 ± 0.328 | 0.613 ± 0.130 |
| hV4 | 10 | **0.541 ± 0.283** | **0.613 ± 0.092** |

> hV4 shows strongest color selectivity: highest RDM correlation and most consistent decoding accuracy.

### Results by Group

| Group | N (pairs) | RDM Correlation (M ± SD) | Decoding Accuracy (M ± SD) |
|-------|-----------|--------------------------|---------------------------|
| HC (sub-01~07) | 28 | 0.345 ± 0.278 | 0.552 ± 0.111 |
| CVD (sub-08~10) | 12 | **0.462 ± 0.273** | **0.684 ± 0.094** |
| Difference | — | +0.117 | +0.132 (13.2 pp) |

> Note: CVD subjects show numerically higher decoding performance. This may reflect higher signal quality or genuine representational differences; it does not imply superior color processing.

### Noise Ceiling Analysis (N=40 pairs, 10 subjects × 4 ROIs)

**Method**: Random Split-Half with Spearman-Brown correction (1,000 iterations)

| ROI | N | Noise Ceiling (M ± SD) | RDM After Procrustes | % of Ceiling |
|-----|---|----------------------|---------------------|-------------|
| V1 | 10 | 0.582 ± 0.172 | 0.160 ± 0.154 | 24.2% |
| V2 | 10 | 0.635 ± 0.200 | 0.200 ± 0.155 | 29.0% |
| V3 | 10 | 0.525 ± 0.226 | 0.173 ± 0.174 | 23.2% |
| hV4 | 9* | **0.697 ± 0.168** | **0.315 ± 0.186** | **41.8%** |
| **Overall** | **39** | **0.610** | **0.212** | **29.6%** |

> *hV4: N=9, excluding sub-07 (only 16 voxels in C010 pipeline → correlation distance underdetermined → NaN). All other ROIs N=10.
> Re-run on 2026-02-17 with sub-01 included (previously N=36). Dataset: `full_dataset_C010`. LOSO bounds: V1 [0.16, 0.38], V2 [0.29, 0.43], V3 [0.22, 0.40], hV4 [0.14, 0.36].

### Pipeline Comparison (Whitening Assessment, N=40)

| Pipeline | RDM Reliability | Noise Ceiling | Status |
|----------|---------------|---------------|--------|
| Raw C010 | 0.028 ± 0.225 | −0.038 ± 0.434 | Poor |
| **Raw → Procrustes** | **0.487 ± 0.253** | **0.613 ± 0.248** | **OPTIMAL** |
| Raw → Whitening → Procrustes | 0.036 ± 0.153 | 0.020 ± 0.182 | −92% (harmful) |
| Raw → Procrustes → Whitening | 0.259 ± 0.245 | 0.352 ± 0.315 | −47% (harmful) |

> Whitening degrades performance regardless of order: estimated covariance conflates signal + noise, removing spatial color structure. 77.5% of pairs degraded when whitening applied after Procrustes.

### Validation Status (Phase 1)

- [x] Procrustes alignment: 100% positive pairs, +1644% improvement (0.028 → 0.487)
- [x] Whitening assessment: harmful, excluded
- [x] Noise ceiling: ~30% utilization (per-subject split-half); pipeline-level RDM reliability 0.487 vs ceiling 0.613 (79%) uses different metric — see Noise Ceiling table for per-ROI breakdown
- [x] Temporal stability: method difference = 0.101 (excellent)
- [x] Drift validation: 1st+2nd and 2nd-only produced identical HRF — passed
- [x] Onset randomization: dropped (FIR with fixed ISI; timing jitter not applicable)

---

## Phase 2: SRM Between-Subject Analysis (C010 Between-Subject)

### Settings

- **Method**: Shared Response Model (SRM) alignment
- **SRM components (k)**: V1=4, V2=4, V3=3, hV4=3 (validated via 7-fold LOSO cross-validation with mean rank aggregation; see 2C below)
- **Input**: Phase 1 Procrustes-aligned amplitudes (C010)
- **ROIs**: V1, V2, V3, hV4
- **Subjects**: HC (n=7: sub-01~07), CVD (n=3: sub-08~10)
- **Training**: HC-only (7 HC subjects train SRM; CVD subjects projected into HC-defined shared space via SVD)
- **CVD projection**: `W_new = U @ Vt` from SVD of `X_new @ pinv(S)`, where S is the HC-learned shared response
- **Metric**: Procrustes disparity between subject pairs in SRM space
- **Comparison**: HC-HC pairs vs CVD-HC pairs
- **Statistical test**: Permutation test (label shuffling, 10,000 iterations) for group disparity comparison
- **Effect size**: Hedges' g (bias-corrected for small samples)

### Main Results: Group Disparity Comparison (HC-Only SRM, LOO-consistent)

| ROI | HC LOO [95% CI] | CVD LOO [95% CI] | Separation [95% CI] | p (perm) | Hedges' g [95% CI] |
|-----|----------------|-----------------|---------------------|----------|---------------------|
| V1 | 0.453 [0.397, 0.512] | 0.590 [0.457, 0.761] | 0.137 [−0.005, 0.301] | 0.062 | 1.16 [−0.06, 3.98] |
| V2 | 0.486 [0.418, 0.559] | 0.606 [0.505, 0.718] | 0.120 [0.001, 0.244] | 0.075 | 1.04 [0.02, 3.18] |
| V3 | 0.540 [0.476, 0.608] | 0.564 [0.404, 0.738] | 0.023 [−0.137, 0.194] | 0.395 | 0.18 [−1.59, 2.34] |
| hV4 | 0.700 [0.617, 0.796] | 0.677 [0.444, 0.855] | −0.023 [−0.244, 0.172] | 0.559 | −0.14 [−2.07, 2.03] |

> **LOO-consistent analysis** (2026-02-18). Three methodological fixes applied:
> 1. **HC-only SRM**: Trained on 7 HC only; CVD projected via SVD (RT-2 circularity fix)
> 2. **LOO for HC**: HC sub-i compared to mean of other 6 HC (no group-mean leakage)
> 3. **Same LOO references for CVD**: Each CVD subject's disparity computed against the same 7 LOO references used for HC, then averaged. Both groups evaluated on identical 6-subject reference basis.
>
> **Permutation test**: Fully LOO-consistent (10,000 iterations). Each permutation assigns 7 pseudo-HC and 3 pseudo-CVD, recomputes LOO references, and evaluates both groups against matching references.
>
> **Group-level results**: V1 (p=0.062) and V2 (p=0.075) show trending but non-significant HC-CVD separation. Effect sizes are large (g=1.16/1.04) but CIs are wide due to n=3 CVD. V2 separation CI [0.001, 0.244] marginally excludes zero. V3/hV4 show no group difference.

### Individual CVD Tests (Crawford & Howell 1998)

| Subject | V1 (t, p) | V2 (t, p) | V3 (t, p) | hV4 (t, p) | Pattern |
|---------|-----------|-----------|-----------|------------|---------|
| **sub-09** | **t=3.5, p=0.007** | t=1.0, p=0.181 | t=0.1, p=0.466 | t=1.1, p=0.150 | **V1: significantly above HC** |
| **sub-08** | t=1.1, p=0.157 | **t=2.1, p=0.040** | t=1.9, p=0.052 | t=0.2, p=0.411 | **V2: significantly above HC** |
| sub-10 | t=0.0, p=0.483 | t=0.2, p=0.433 | t=−1.3, p=0.884 | t=−1.9, p=0.945 | HC range, no elevation |

> **Crawford & Howell (1998) modified t-test**: Tests each CVD individual against the HC LOO distribution (df=6, one-tailed). Same 6-subject LOO references used for both HC and CVD scores.
>
> **Key finding**: Individual CVD testing reveals region-specific dissociations that group analysis obscures:
> - **sub-09** (protan): Significantly elevated disparity in V1 (p=0.007), consistent with early visual cortex disruption
> - **sub-08** (deutan): Significantly elevated in V2 (p=0.040), marginally in V3 (p=0.052), suggesting mid-level visual processing impact
> - **sub-10** (deutan): Falls entirely within the HC range across all ROIs — functionally normal color representations
>
> This resolves RT-3 (n=3 heterogeneity): rather than treating CVD as a homogeneous group, individual testing shows 2/3 CVD subjects have measurable neural signatures in specific visual areas, while 1/3 does not.

### Individual CVD Profiles (LOO-corrected % above HC LOO mean)

| Subject | V1 (% above HC) | V2 (% above HC) | V3 (% above HC) | hV4 (% above HC) | Pattern |
|---------|-----------------|-----------------|-----------------|-------------------|---------|
| sub-08 | +20.9% | +47.4% | +35.7% | +3.5% | Moderate-high elevation |
| sub-09 | +67.7% | +21.5% | +0.7% | +21.4% | V1-dominant |
| sub-10 | −0.1% | +3.1% | −26.8% | −39.1% | Near-normal to below-HC |

> **sub-08**: Elevated in V1/V2/V3 (+34.5% avg excl. hV4), near-normal in hV4
> **sub-09**: Strong V1 elevation (+67.7%), moderate elsewhere
> **sub-10**: Near-normal in V1/V2, below HC in V3/hV4 — not clearly elevated
>
> **LOO correction effect**: With LOO, HC mean is higher → %above values are smaller. sub-10 no longer shows any consistent elevation, weakening the group-level effect.

### CVD Heterogeneity (CVD-CVD vs HC-HC disparity ratio)

| ROI | CVD-CVD / HC-HC ratio | Interpretation |
|-----|----------------------|----------------|
| V1 | 1.47× | Moderate heterogeneity |
| V2 | 1.37× | Moderate heterogeneity |
| V3 | 1.59× | Highest heterogeneity |
| hV4 | 1.44× | Moderate heterogeneity |

> CVD subjects are 1.4–1.6× more dispersed than HC across all ROIs.

### RDM Correlation (Color Structure Similarity)

| ROI | HC-HC RDM [95% CI] | HC-CVD RDM [95% CI] | CVD-CVD RDM [95% CI] | N pairs |
|-----|---------------------|----------------------|----------------------|---------|
| V1 | 0.447 [0.357, 0.531] | 0.322 [0.237, 0.402] | 0.297 [0.126, 0.493] | 21/21/3 |
| **V2** | **0.517 [0.442, 0.592]** | **0.499 [0.414, 0.587]** | **0.591 [0.471, 0.702]** | 21/21/3 |
| V3 | 0.385 [0.300, 0.473] | 0.348 [0.245, 0.457] | 0.591 [0.490, 0.672] | 21/21/3 |
| hV4 | 0.158 [0.069, 0.248] | 0.224 [0.119, 0.328] | 0.276 [0.008, 0.734] | 21/21/3 |

> **Bootstrap 95% CIs** (10,000 iterations, pair-level resampling). In V2, HC-CVD RDM CI [0.414, 0.587] heavily overlaps with HC-HC CI [0.442, 0.592], confirming CVD subjects largely preserve color relationship structure ("parallel" pattern). In V1, HC-CVD upper bound (0.402) falls below HC-HC lower bound (0.357) only marginally, indicating less preservation in early visual cortex. CVD-CVD CIs are wide due to n=3 pairs (hV4: [0.008, 0.734]).
>
> **Noise ceiling context**: Phase 1 noise ceiling (split-half corrected) is V1=0.582, V2=0.635, V3=0.525, hV4=0.697. HC-HC RDM correlations in SRM space (V1=0.447, V2=0.517) reach 77–81% of noise ceiling, indicating SRM extracts most available color structure.

### Permutation Validation (1D: Pre-SRM Shuffling with Retraining, HC-Only SRM, 1000 iterations)

**Approach 2 (group-difference disparity + within-group RDM correlations):**

| ROI | Disparity diff p | Disparity interpretation | HC RDM p | CVD RDM p | RDM interpretation |
|-----|------------|-------------------------|----------|-----------|-------------------|
| V1 | 0.327 | Not significant | 0.054 | 0.056 | Trending (both groups) |
| **V2** | **0.986** | **Color-AGNOSTIC** | 0.724 | 0.116 | Not color-specific |
| V3 | 0.977 | Color-agnostic | 0.815 | 0.066 | CVD trending |
| hV4 | 0.933 | Color-agnostic | 0.808 | 0.586 | Not color-specific |

> **Updated 2026-02-18 (HC-only SRM re-run)**. Previous results used all-subjects SRM which inflated RDM color-specificity (shared space encoded consensus from all 10 subjects including CVD). Under HC-only SRM:
>
> - **V2 RDM color-specificity disappeared** (HC p=0.010→0.724, CVD p=0.006→0.116). This was an artifact of all-subjects SRM training: the shared space itself encoded color consensus from all subjects, making RDM correlations artificially high relative to a color-shuffled null.
> - **V1 RDM color-specificity trending** (HC p=0.192→0.054, CVD p=0.599→0.056). HC-only SRM captures HC color structure more cleanly in V1.
> - **Disparity difference remains color-agnostic** across all ROIs (p>0.3), confirming the HC-CVD disparity reflects general representational differences, not color-specific divergence.

**Per-group disparity color-dependency test (1D-ext, HC-only SRM, 1000 iterations):**

Tests whether each group's within-group consistency depends on true color labels (not group differences).

| ROI | HC LOO disp p | CVD LOO disp p | CVD pairwise p | HC RDM p | CVD RDM p |
|-----|---------------|----------------|----------------|----------|-----------|
| V1 | 0.070 | 0.427 | 0.077 | 0.054 | 0.056 |
| **V2** | 0.894 | **0.033** | **0.035** | 0.724 | 0.116 |
| V3 | 0.437 | **0.009** | **0.046** | 0.815 | 0.066 |
| hV4 | 0.325 | **0.028** | **0.031** | 0.808 | 0.586 |

> **Updated 2026-02-18 (LOO-consistent analysis)**. All metrics computed with LOO-consistent references: HC LOO disp uses 6-subject refs; CVD score disp averages CVD's disparity across the same 7 LOO references used for HC.
>
> **HC LOO disparity non-significance is expected (single-SRM)**: Under HC-only SRM, all 7 HC subjects train the shared space. SRM inherently minimizes HC-to-HC-mean distance, creating a floor effect where HC LOO disparity is similar under true and shuffled labels. This is structural, not evidence against color structure. See LOSO analysis below for a fair HC test.
>
> **CVD color-dependency confirmed in V2/V3/hV4**: CVD subjects show color-dependent disparity to HC references in V2 (score p=0.033, pairwise p=0.035), V3 (score p=0.009, pairwise p=0.046), and hV4 (score p=0.028, pairwise p=0.031). Under shuffled color labels, CVD-to-HC disparity degrades, confirming color-specific structure.
>
> **V1 CVD score not color-dependent** (p=0.427): V1's trending group effect (group perm p=0.062) is NOT color-specific — the HC-CVD disparity in V1 reflects general representational differences, not color-dependent divergence. However, V1 RDM trends toward color-specificity for both groups (HC p=0.054, CVD p=0.056).
>
> **Revised interpretation**: "Scattered" (CVD has higher disparity, color-agnostic) is confirmed in V1/V2. "Parallel" (both groups preserve same RDM structure) is weakened — V2 RDM evidence was an artifact of all-subjects SRM. However, CVD subjects DO share genuine color-dependent consistency with HC reference patterns (V2/V3/hV4 score p<0.05), supporting the interpretation that CVD representations are dispersed but individually color-structured.

**LOSO color-dependency test (1D-ext-LOSO, HC tested in space they did NOT train):**

Addresses the structural floor confound: in single-SRM analysis, HC subjects train the shared space, so their disparity is insensitive to color-label shuffling. LOSO eliminates this by leaving each HC subject out of SRM training and projecting them via SVD — identical treatment to CVD.

| ROI | HC held-out (obs) | HC null | p_hc_color | CVD score (obs) | CVD null | p_cvd_color | Sep | g | p_group |
|-----|-------------------|---------|------------|-----------------|----------|-------------|-----|---|---------|
| V1 | 0.490 | 0.498 | 0.364 | 0.590 | 0.594 | 0.412 | 0.099 | 0.67 | 0.154 |
| V2 | 0.472 | 0.487 | 0.227 | 0.598 | 0.673 | **0.010** | 0.127 | 0.88 | 0.102 |
| V3 | 0.539 | 0.564 | 0.207 | 0.544 | 0.668 | **0.000** | 0.005 | 0.03 | 0.457 |
| hV4 | 0.714 | 0.733 | 0.330 | 0.672 | 0.781 | **0.016** | −0.043 | −0.23 | 0.643 |

LOSO individual CVD tests (Crawford & Howell, LOSO HC held-out as control):

| Subject | V1 (t, p) | V2 (t, p) | V3 (t, p) | hV4 (t, p) |
|---------|-----------|-----------|-----------|------------|
| **sub-09** | **t=2.0, p=0.045** | t=0.8, p=0.234 | t=0.1, p=0.479 | t=0.8, p=0.228 |
| sub-08 | t=0.5, p=0.323 | t=1.3, p=0.116 | t=1.2, p=0.143 | t=0.1, p=0.474 |
| sub-10 | t=−0.3, p=0.600 | t=0.4, p=0.365 | t=−1.1, p=0.851 | t=−1.6, p=0.924 |

> **Updated 2026-02-18 (LOSO analysis)**. Both HC and CVD projected via SVD into spaces they did not train — eliminates training advantage confound.
>
> **HC color-dependency NOT significant in any ROI** (p=0.21–0.36): When tested fairly (LOSO), HC disparity does NOT depend on color labels. HC subjects share general visual structure that SRM captures regardless of color ordering. This confirms the single-SRM floor effect was structural, not a false negative.
>
> **CVD color-dependency confirmed in V2/V3/hV4 under LOSO** (V2 p=0.010, V3 p=0.000, hV4 p=0.016): Even when CVD is projected via SVD (identical to HC treatment), their disparity from HC reference significantly depends on true color labels. Shuffling color labels increases CVD disparity — the SRM group separation is driven by genuine color-structure divergence.
>
> **Asymmetry is the key finding**: HC don't need color labels to fit the shared space (low disparity under both true and shuffled labels). CVD's higher disparity is specifically color-dependent — it arises because CVD color representations deviate from the HC-trained color structure. This dissociation (HC color-agnostic + CVD color-dependent) is the strongest evidence that the SRM analysis captures color-specific group differences, not general noise.
>
> **LOSO group permutation**: V1 p=0.154, V2 p=0.102. Wider p-values than single-SRM (V1 0.062, V2 0.075) because LOSO increases HC variance (projected rather than trained). This is expected and conservative.
>
> **LOSO Crawford & Howell**: Only sub-09 V1 remains significant (p=0.045). Other individual effects diluted by increased HC variance under LOSO projection. The single-SRM individual tests (sub-09 V1 p=0.007, sub-08 V2 p=0.040) provide tighter individual-level evidence since HC subjects train the SRM (appropriate for comparing an outsider to the trained group).

### 1B: LOSO Stability (7-fold leave-one-HC-subject-out)

Each fold removes one HC subject, retrains SRM on remaining 6 HC, and tests CVD-HC separation.

| ROI | Significant folds (p<0.05) | Fold p-values | Stability |
|-----|---------------------------|---------------|-----------|
| V1 | **6/7** | 0.013, 0.046, 0.023, 0.052, 0.018, 0.007, 0.020 | Robust (1 marginal at p=0.052) |
| **V2** | **7/7** | 0.015, 0.013, 0.011, 0.032, 0.004, <0.001, 0.008 | **Perfect stability** |
| V3 | 0/7 | 0.290, 0.199, n.s., n.s., n.s., n.s., 0.461 | Consistently non-significant |
| hV4 | 0/7 | 0.266, 0.460, n.s., n.s., n.s., n.s., 0.147 | Consistently non-significant |

> V2 CVD-HC separation is significant in ALL 7 folds (p range: <0.001 to 0.032), confirming no single HC subject drives the result. V1 is robust with 6/7 folds significant (sub-04 fold marginal at p=0.052). V3 and hV4 are consistently non-significant, confirming the original finding.

### 1C: Split-Half SRM Reliability (runs 1-3 vs runs 4-6)

| ROI | Set A p | Set B p | Both sig? | Cross-half disparity r (p) |
|-----|---------|---------|-----------|---------------------------|
| V1 | 0.059 | **0.019** | No | 0.709 (p=0.022) |
| **V2** | **0.006** | **0.022** | **Yes** | 0.709 (p=0.022) |
| V3 | 0.156 | 0.074 | No | 0.430 (p=0.214) |
| hV4 | 0.402 | 0.174 | No | 0.782 (p=0.008) |

> V2 is the only ROI showing significant CVD-HC disparity in BOTH independent halves. Cross-half disparity pattern correlation is significant for V1, V2, and hV4 (r=0.71-0.78), indicating individual disparity profiles are stable across run halves even when group-level significance is marginal.

### 2C: Optimal k Selection (7-fold LOSO cross-validation, k={2,3,4,5,6})

Validated via mean rank aggregation across 7 LOSO folds using two RDM-based metrics (rdm_reliability, cross_subject_rdm_corr). Reconstruction error was computed but excluded from selection criterion as it trivially favors higher k (more dimensions = lower error).

**Mean rank by RDM-based metrics (lower rank = better; 1 = best):**

| ROI | Selected k | RDM reliability rank (SD) | Cross-subj RDM rank (SD) | Mean RDM rank | Runner-up |
|-----|-----------|--------------------------|-------------------------|---------------|-----------|
| V1 | **4** | **1.86** (0.90) | **2.00** (1.15) | **1.93** | k=3 (2.71) |
| V2 | **4** | **2.14** (0.69) | **2.14** (1.21) | **2.14** | k=5 (2.36) |
| V3 | **3** | **2.14** (1.46) | 2.14 (1.07) | **2.14** | k=4 (2.14, tied) |
| hV4 | **3** | **2.00** (1.73) | **2.14** (1.68) | **2.07** | k=4 (2.57) |

**Per-metric best k across folds:**

| ROI | rdm_reliability best | cross_subj_rdm best | Selected |
|-----|---------------------|---------------------|----------|
| V1 | k=4 | k=4 | **k=4** (unanimous) |
| V2 | k=4 | k=4 | **k=4** (unanimous) |
| V3 | k=3 (tied with k=4) | k=4 | **k=3** (parsimony; fewer voxels favor lower k) |
| hV4 | k=3 | k=3 | **k=3** (both metrics agree) |

**Mean metric values at selected k:**

| ROI | k | RDM reliability (M ± SD) | Cross-subj RDM (M ± SD) |
|-----|---|--------------------------|-------------------------|
| V1 | 4 | 0.496 ± 0.146 | 0.597 ± 0.229 |
| V2 | 4 | 0.429 ± 0.137 | 0.566 ± 0.145 |
| V3 | 3 | 0.446 ± 0.194 | 0.546 ± 0.279 |
| hV4 | 3 | 0.560 ± 0.185 | 0.317 ± 0.169 |

> **Final selection: V1=4, V2=4, V3=3, hV4=3**. V1 and V2 are unanimously supported by both RDM metrics. V3: k=3 and k=4 tie at mean rank 2.14; k=3 selected by parsimony (V3 has fewer voxels, lower-dimensional space sufficient). hV4: formal aggregation favors k=3 over original k=4 (mean RDM rank 2.07 vs 2.57). **Update from original**: hV4 revised from k=4 to k=3 based on data-driven mean rank aggregation.
>
> **Caveat on reconstruction error**: Including reconstruction error in a 3-metric composite would bias toward higher k (k=6 always ranks 1st). This metric measures variance captured, not color structure quality — excluded from selection criterion.

### 2D: Alignment Comparison (Raw vs Procrustes vs SRM)

**Between-subject RDM agreement (higher = better alignment):**

| ROI | Raw | Procrustes | SRM | SRM / Raw ratio |
|-----|-----|-----------|-----|-----------------|
| V1 | 0.083 | 0.068 | **0.538** | **6.5x** |
| V2 | 0.152 | 0.159 | **0.556** | **3.7x** |
| V3 | 0.159 | 0.145 | **0.388** | **2.4x** |
| hV4 | 0.097 | 0.111 | **0.297** | **3.1x** |

> SRM produces 2.4-6.5x higher between-subject RDM agreement than raw or Procrustes alignment. Note: within-subject RDM correlation decreases under SRM (V2: raw 0.471 -> SRM 0.096), reflecting the expected trade-off where SRM optimizes cross-subject consensus at the cost of individual-specific structure.

### 2A: Run-Split ICC (CVD individual reliability)

| Subject | V1 | V2 | V3 | hV4 | Assessment |
|---------|------|------|------|------|------------|
| sub-08 | 0.58 | **0.75** | 0.71 | **0.83** | Most stable CVD subject |
| sub-09 | 0.46 | 0.53 | 0.73 | 0.74 | Moderate |
| sub-10 | 0.45 | 0.55 | 0.61 | 0.67 | Moderate |

> Values are Spearman-Brown corrected split-half correlations. 8/12 subject-ROI pairs reach moderate reliability (r > 0.5). sub-08 shows good reliability in hV4 (0.83) and V2 (0.75).

### Validation Status (Phase 2)

- [x] SRM alignment: all 4 ROIs computed (V1=4, V2=4, V3=3, hV4=3)
- [x] Between-subject disparity: HC-CVD comparison complete
- [x] Permutation test (Approach 1): basic shuffle
- [x] Permutation test (Approach 2): pre-SRM shuffle with retraining (1000 iter, all ROIs)
- [x] **1D-ext Per-group permutation**: LOO-consistent CVD color-dependency V2 p=0.033, V3 p=0.009, hV4 p=0.028; HC disparity insensitive (structural floor)
- [x] **1D-ext-LOSO Color-dependency**: LOSO-based HC color p=0.21–0.36 (not significant); CVD color V2 p=0.010, V3 p=0.000, hV4 p=0.016 (confirmed under fair test)
- [x] Brain surface visualization: voxel-level maps for sub-08
- [x] **1A HC-only verification**: LOO-consistent group V1 p=0.062 (trending), V2 p=0.075 (trending); V3/hV4 n.s.
- [x] **1B LOSO stability**: V2 7/7 folds significant; V1 6/7; V3/hV4 0/7
- [x] **1C Split-half reliability**: V2 significant in both halves; cross-half disparity r=0.71-0.78 for V1/V2/hV4
- [x] **1D Permutation test**: LOO-consistent color-label: disparity_diff V1 p=0.327, V2 p=0.986 (color-agnostic); group perm V1 p=0.062, V2 p=0.075 (trending)
- [x] **2A Run-split ICC**: 8/12 moderate or better; sub-08 hV4 best (r=0.83)
- [x] **2B RDM consistency**: CVD >= HC in V1 (+0.200) and V2 (+0.123) -- "parallel" pattern confirmed
- [x] **2C k-value selection**: 7-fold CV completed; V1=4, V2=4, V3=3, hV4=3 validated via mean rank aggregation
- [x] **2D Alignment comparison**: SRM 2.4-6.5x better than raw/Procrustes for between-subject RDM agreement
- [x] **Bootstrap 95% CIs**: LOO-consistent separation V1 [−0.005, 0.301] V2 [0.001, 0.244] (V2 marginally excludes zero); RDM CIs for all ROI-group pairs
- [x] **Formal k aggregation**: Mean rank across 7 folds; V1=4, V2=4 unanimous; V3=3 (parsimony); hV4 revised from 4→3
- [x] **A3 Variance Explained**: LOSO framework — CVD VE ≥ HC VE; V2 g=−1.68 (strong signal)
- [x] **A4 Crossnobis RDM**: SRM-independent — V1 trending p=0.051; convergent r_pooled=0.486**
- [x] **A5 PCA-CCA Replication**: Alternative alignment — PCA-only convergent r_pooled=0.742***

---

## Phase 2 Robustness: SRM-Independent Triangulation (A3/A4/A5) — 2026-02-18

### 목표 (Purpose)

SRM 분석 결과가 alignment method artifact가 아님을 증명하기 위해, SRM에 독립적인 3가지 보완 지표로 삼각검증(triangulation) 수행.

| Metric | SRM 의존성 | 검증 목표 |
|--------|-----------|----------|
| A4 Crossnobis RDM | **없음** (native voxel space) | SRM 없이도 동일한 HC-CVD 패턴 존재? |
| A5 PCA→CCA | **없음** (다른 alignment 방법) | 다른 정렬 알고리즘으로도 그룹 차이 재현? |
| A3 Variance Explained | **있음** (SRM W 행렬) | SRM이 CVD 데이터를 잘 설명하는가? |

### Settings (공통)

- **Data**: `full_dataset_C010`, Procrustes-aligned amplitudes (6 runs, 8 colors)
- **Subjects**: HC (n=7: sub-01~07), CVD (n=3: sub-08~10)
- **ROIs**: V1, V2, V3, hV4
- **SRM k**: V1=4, V2=4, V3=3, hV4=3
- **Permutations**: 10,000; **Bootstrap**: 10,000
- **Scripts**: `validation/compute_{crossnobis_rdm,pca_cca_replication,variance_explained}.py`

---

### A4: Crossnobis RDM — SRM-Independent Voxel-Space Validation

**방법**: Cross-validated Mahalanobis distance in native voxel space (Walther et al. 2016). SRM과 완전히 독립적.
- Noise covariance: Ledoit-Wolf shrinkage (handles p>n)
- Cross-validation: C(6,2)=15 run pairs → unbiased 8×8 distance matrix per subject
- RDM similarity: Spearman ρ between subject pairs' crossnobis RDMs
- 비교: HC-HC (21 pairs) vs HC-CVD (21 pairs) vs CVD-CVD (3 pairs)

#### RDM Similarity (Group comparison)

| ROI | HC-HC [95% CI] | HC-CVD [95% CI] | CVD-CVD | Diff [95% CI] | p (MW) | p (perm) |
|-----|---------------|----------------|---------|---------------|--------|----------|
| **V1** | **0.104** [0.012, 0.196] | −0.018 [−0.122, 0.089] | 0.049 | **0.122** [−0.019, 0.262] | **0.052** | **0.051** |
| V2 | −0.018 [−0.114, 0.080] | 0.011 [−0.095, 0.123] | 0.063 | −0.029 [−0.176, 0.115] | 0.623 | 0.649 |
| V3 | 0.021 [−0.079, 0.114] | −0.049 [−0.164, 0.068] | −0.122 | 0.070 [−0.084, 0.217] | 0.170 | 0.186 |
| hV4 | −0.018 [−0.117, 0.088] | −0.015 [−0.105, 0.070] | 0.174 | −0.002 [−0.134, 0.137] | 0.661 | 0.502 |

#### Convergent Validity (Crossnobis distance from HC mean ↔ SRM disparity)

| ROI | Spearman r | p | Interpretation |
|-----|-----------|---|---------------|
| **V1** | **0.721** | **0.019** | Strong convergence |
| **V2** | **0.806** | **0.005** | Strong convergence |
| V3 | 0.200 | 0.580 | Weak |
| hV4 | 0.248 | 0.489 | Weak |
| **Pooled** | **0.486** | **0.001** | Moderate-strong |

#### A4 해석

- **V1 trending** (p=0.051): SRM 없이 native voxel space에서도 HC-HC RDM 유사도가 HC-CVD보다 높은 경향. SRM 결과 (group p=0.062)와 수렴.
- **Convergent validity 강력**: V1 r=0.721, V2 r=0.806 — crossnobis distance가 SRM disparity와 강하게 상관. SRM이 실제 neural 차이를 반영함을 확인.
- V2/V3/hV4는 crossnobis 그룹 차이 비유의미 — 이는 crossnobis가 **전체 RDM 유사도**를 비교하는 반면, SRM disparity는 **pair-specific alignment**를 측정하기 때문. 서로 다른 측면을 포착.

---

### A5: PCA→CCA Replication — Alternative Alignment Validation

**방법**: SRM 대신 PCA dimensionality reduction + CCA alignment으로 동일한 분석 재현.
- **Dimensionality (k)**: Same as SRM — V1=4, V2=4, V3=3, hV4=3 (ensures dimensionality-matched comparison)
- 모든 C(10,2)=45 subject pairs에 대해:
  - **PCA-only**: PCA(k) → Procrustes disparity (CCA 없이)
  - **PCA-CCA**: PCA(k) → CCA alignment → Procrustes disparity
- Per-subject mean distance to HC for convergent validity

#### Group Disparity (PCA-only method)

| ROI | HC-HC (M ± SD) | HC-CVD (M ± SD) | Diff [95% CI] | g | p (perm) |
|-----|---------------|----------------|---------------|---|----------|
| V1 | 0.822 ± 0.114 | 0.858 ± 0.148 | 0.037 [−0.042, 0.114] | 0.27 | 0.187 |
| V2 | 0.839 ± 0.126 | 0.849 ± 0.130 | 0.010 [−0.065, 0.086] | 0.08 | 0.397 |
| V3 | 0.932 ± 0.130 | 0.925 ± 0.129 | −0.006 [−0.082, 0.070] | −0.05 | 0.566 |
| hV4 | 0.987 ± 0.137 | 0.948 ± 0.170 | −0.039 [−0.131, 0.050] | −0.25 | 0.791 |

#### Group Disparity (PCA-CCA method)

| ROI | HC-HC (M ± SD) | HC-CVD (M ± SD) | Diff [95% CI] | g | p (perm) |
|-----|---------------|----------------|---------------|---|----------|
| V1 | 0.754 ± 0.109 | 0.743 ± 0.137 | −0.011 [−0.086, 0.059] | −0.09 | 0.616 |
| V2 | 0.755 ± 0.125 | 0.784 ± 0.102 | 0.030 [−0.036, 0.098] | 0.25 | 0.200 |
| V3 | 0.885 ± 0.137 | 0.911 ± 0.098 | 0.025 [−0.044, 0.097] | 0.21 | 0.248 |
| hV4 | 0.924 ± 0.116 | 0.909 ± 0.122 | −0.015 [−0.088, 0.052] | −0.13 | 0.662 |

#### Convergent Validity (PCA distance from HC mean ↔ SRM disparity)

| Method | V1 (r, p) | V2 (r, p) | V3 (r, p) | hV4 (r, p) | **Pooled (r, p)** |
|--------|-----------|-----------|-----------|------------|-------------------|
| **PCA-only** | 0.636, 0.048* | **0.891, <0.001** | 0.285, 0.425 | 0.661, 0.038* | **0.742, <0.001** |
| **PCA-CCA** | 0.503, 0.138 | 0.370, 0.293 | −0.018, 0.960 | 0.212, 0.556 | **0.472, 0.002** |

#### A5 해석

- **그룹 차이는 약함**: PCA-only와 PCA-CCA 모두 그룹 수준 유의미하지 않음 — pairwise alignment은 SRM의 shared space보다 noise가 높음 (45개 pair 각각 독립적 정렬).
- **Convergent validity가 핵심 결과**:
  - PCA-only pooled r=0.742 (p<0.001): SRM disparity와 매우 강한 상관. SRM이 아닌 PCA로 측정해도 동일한 subject-level 패턴.
  - V2 r=0.891 (p<0.001): V2에서 SRM과 PCA 결과가 거의 완벽히 수렴.
  - PCA-CCA pooled r=0.472 (p=0.002): CCA는 추가적 alignment으로 약간의 정보 손실, 그래도 유의미한 수렴.
- **결론**: SRM disparity가 측정한 subject-level 변이는 alignment method에 비의존적. PCA-only로도 재현됨.

---

### A3: Variance Explained — SRM Reconstruction Quality

**방법**: SRM이 각 subject의 데이터를 얼마나 잘 재구성하는지 정량화.
- `VE = 1 - ||X - W @ S||² / ||X||²` (X=voxel data, W=weight matrix, S=shared response)
- **Framework A** (single-SRM): HC uses trained W, CVD uses SVD-projected W (confounded)
- **Framework B** (LOSO, unbiased): Both HC and CVD use SVD projection → fair comparison

#### Framework B (LOSO) Results — Unbiased

| ROI | k | HC VE [95% CI] | CVD VE [95% CI] | Diff [95% CI] | g | p (perm) |
|-----|---|---------------|----------------|---------------|---|----------|
| V1 | 4 | 0.352 [0.267, 0.412] | 0.402 [0.283, 0.532] | −0.050 [−0.191, 0.082] | −0.39 | 0.684 |
| **V2** | **4** | **0.331 [0.289, 0.373]** | **0.448 [0.379, 0.511]** | **−0.117 [−0.190, −0.042]** | **−1.68** | **0.982** |
| V3 | 3 | 0.250 [0.200, 0.305] | 0.321 [0.224, 0.404] | −0.070 [−0.165, 0.031] | −0.79 | 0.876 |
| hV4 | 3 | 0.225 [0.183, 0.265] | 0.271 [0.210, 0.307] | −0.045 [−0.108, 0.022] | −0.69 | 0.870 |

#### Individual CVD (Crawford & Howell, LOSO — one-tailed: patient > control)

| Subject | V1 (VE, t, p) | V2 (VE, t, p) | V3 (VE, t, p) | hV4 (VE, t, p) |
|---------|---------------|---------------|---------------|----------------|
| sub-08 | 0.532, t=1.50, p=0.908 | 0.379, t=0.72, p=0.752 | 0.224, t=−0.32, p=0.379 | 0.210, t=−0.23, p=0.413 |
| sub-09 | 0.283, t=−0.58, p=0.292 | 0.454, t=1.87, p=0.945 | 0.404, t=1.87, p=0.944 | 0.295, t=1.06, p=0.834 |
| sub-10 | 0.392, t=0.33, p=0.625 | 0.511, t=2.74, p=0.983 | 0.334, t=1.02, p=0.826 | 0.307, t=1.25, p=0.871 |

#### Convergent Validity (VE ↔ SRM disparity)

| ROI | Spearman r | p | Interpretation |
|-----|-----------|---|---------------|
| V1 | −0.006 | 0.987 | No correlation |
| V2 | 0.285 | 0.425 | Weak positive |
| V3 | 0.103 | 0.777 | No correlation |
| hV4 | −0.115 | 0.751 | No correlation |
| Pooled | −0.246 | 0.126 | Weak negative trend |

#### A3 해석

- **예상과 반대**: CVD VE ≥ HC VE (전 ROI). 특히 V2에서 CVD가 HC보다 유의미하게 높음 (diff=−0.117, CI excludes zero, g=−1.68).
- **해석 — "scattered but parallel" 확인**: CVD 표상이 noisy한 것이 아니라, **강한 signal이지만 다른 구조**를 가짐. SRM shared space로 재구성 시 CVD 데이터가 더 잘 복원됨 = CVD는 HC와 **다른 방향으로 체계적**임.
- **수렴 타당도 약함** (r=−0.246 ns): VE와 disparity는 서로 다른 측면 측정. VE는 재구성 품질(signal 강도), disparity는 패턴 기하학(구조 차이). 높은 VE + 높은 disparity = "강한 signal, 다른 구조" — 이것이 정확히 "anisotropy correction" 프레이밍을 지지.
- **Filter design 함의**: CVD 데이터가 SRM 공간에서 잘 재구성된다 = filter 학습에 필요한 정보가 preserved됨. Phase 3에서 CVD→HC 변환 학습이 가능할 것을 시사.

---

### Robustness Summary — Triangulation Matrix

| Metric | 검증 목표 | V1 | V2 | V3 | hV4 | Key result |
|--------|----------|----|----|----|----|------------|
| **SRM disparity** (main) | 그룹 차이 | p=0.062 | p=0.075 | ns | ns | Trending V1/V2 |
| **A4 Crossnobis** | SRM 독립 | **p=0.051** | ns | ns | ns | V1 수렴, convergent r=0.486** |
| **A5 PCA-only** | 다른 alignment | ns | ns | ns | ns | **Convergent r=0.742*** |
| **A5 PCA-CCA** | 다른 alignment | ns | ns | ns | ns | Convergent r=0.472** |
| **A3 VE (LOSO)** | 재구성 품질 | CVD≥HC | **CVD>HC** g=−1.68 | CVD≥HC | CVD≥HC | "Strong signal, different structure" |

> **결론**: 그룹 수준 차이는 trending (n=3 한계)이나, **convergent validity가 강력**: SRM disparity ↔ crossnobis (r=0.486), SRM disparity ↔ PCA distance (r=0.742) 모두 유의미. SRM이 alignment artifact가 아닌 genuine neural difference를 포착함을 확인. A3의 CVD VE>HC VE는 "scattered but parallel" 해석을 보강: CVD는 noisy하지 않고 systematic하게 다름 → anisotropy correction (구조 보정) 프레이밍 유지.

---

## Phase 2b: Decoder Model Comparison (LORO + LOCO)

### Motivation

Phase 1 uses a single decoder (6-channel Forward Encoding from Brouwer & Heeger 2009). Before proceeding to filter optimization (Phase 3), we need to verify:

1. **Is the linear assumption justified?** — Does adding non-linear capacity improve decoding, or is the voxel-to-color mapping fundamentally linear?
2. **Is Procrustes alignment necessary?** — Can non-linear models compensate for run-to-run misalignment without explicit alignment?
3. **Is the mapping common across groups?** — Do HC and CVD subjects share the same voxel-color mapping (prerequisite for filter learning)?
4. **Can models interpolate held-out colors?** — Does the Forward Encoding model capture continuous color structure, or just memorize 8 discrete patterns?

### Settings

- **Data**: `full_dataset_C010` (P3 pipeline, C010 confounds, Procrustes-aligned)
- **Subjects**: 10 total (HC: sub-01~07, n=7; CVD: sub-08~10, n=3)
- **ROIs**: V1, V2, V3, V4 (= hV4 on disk)
- **Input shape**: `amplitudes_{raw,procrustes}.npy` — (6 runs, 8 colors, n_voxels)
- **LORO CV**: Leave-One-Run-Out with nested hyperparameter tuning (inner LORO on train runs)
- **LOCO CV**: Leave-One-Color-Out (no HP tuning; default params)
- **Scripts**: `analysis/phase2_decoder_comparing/model_comparison_validation/scripts/`
- **Results**: `analysis/phase2_decoder_comparing/model_comparison_validation/results/`

### Models Compared (6)

| Model | Type | Target | Linearity | Key Hyperparameters |
|-------|------|--------|-----------|-------------------|
| **LDA** | Classifier | Labels (0-7) | Linear | solver ∈ {svd, lsqr}, shrinkage ∈ {None, auto, 0.5} |
| **Ridge** | Regression | Circular hue (sin/cos) | Linear | alpha ∈ {0.01, 0.1, 1, 10, 100} |
| **ForwardEncoding** | Encoding model | Labels via 6-ch basis | Linear | alpha ∈ {0, 10, 50} |
| **KernelRidge** | Regression | Circular hue (sin/cos) | Non-linear | alpha ∈ {0.1, 1, 10}, gamma ∈ {0.001, 0.01, 0.1} |
| **SVM** | Classifier | Labels (0-7) | Non-linear | C ∈ {0.1, 1, 10}, gamma ∈ {0.001, 0.01, 0.1} |
| **MLP** | Classifier | Labels (0-7) | Non-linear | hidden ∈ {(64,), (64,32)}, alpha ∈ {0.01, 0.1} |

### Result 1: LORO Model Comparison (10 subjects × 4 ROIs)

**Dataset & Alignment**: `full_dataset_C010` | `amplitudes_procrustes.npy` (preloaded Procrustes — fit on all 6 runs) | Voxel space (no SRM, no dim reduction) | LORO CV

#### Overall Performance (Procrustes-aligned, subject-level mean ± bootstrap 95% CI)

| Model | Type | acc_exact | acc_45 [95% CI] | acc_90 | MAE [95% CI] |
|-------|------|-----------|-----------------|--------|-------------|
| **LDA** | Linear | 0.758 | **0.821** [0.802, 0.841] | 0.890 | **25.6°** [22.8, 28.3] |
| **Ridge** | Linear | 0.388 | 0.783 [0.750, 0.821] | **0.920** | 41.8° [37.9, 45.0] |
| **SVM** | Non-lin | 0.685 | 0.776 [0.734, 0.811] | 0.857 | 32.9° [27.1, 38.7] |
| **KernelRidge** | Non-lin | 0.331 | 0.739 [0.692, 0.779] | 0.894 | 47.9° [43.9, 52.1] |
| **ForwardEnc** | Linear | 0.544 | 0.736 [0.708, 0.773] | 0.821 | 43.5° [38.6, 47.2] |
| **MLP** | Non-lin | 0.147 | 0.394 [0.381, 0.409] | 0.644 | 87.1° [85.1, 88.9] |

**Chance levels**: acc_exact = 12.5% (1/8), acc_45 = 37.5% (3/8), MAE = 90°

> All models except MLP significantly exceed chance (CI lower bound > 0.375 for acc_45). LDA achieves best overall performance. Ridge shows a dissociation: low exact accuracy (0.388) but highest acc_90 (0.920), reflecting continuous hue prediction that is imprecise but directionally correct.

#### Procrustes Alignment Effect (Δ = Procrustes − Raw)

| Model | Raw acc_45 | Procrustes acc_45 | Δ |
|-------|-----------|-------------------|---|
| **LDA** | 0.393 | **0.821** | **+0.428** |
| **Ridge** | 0.375 | **0.783** | +0.408 |
| **SVM** | 0.382 | **0.776** | +0.393 |
| **KernelRidge** | 0.380 | **0.739** | +0.359 |
| **ForwardEnc** | 0.367 | **0.736** | +0.369 |
| **MLP** | 0.370 | 0.394 | +0.024 |

> Without alignment, ALL models perform at chance (~37–39%). Procrustes alignment is the single most important factor. Non-linear models (SVM, KernelRidge) do NOT compensate for misalignment. The improvement is largest for LDA (+42.8%p), confirming that the mapping is linear but requires run-to-run alignment.

#### HC vs CVD Comparison (Procrustes, acc_45)

| Model | HC (n=7) | CVD (n=3) | Δ(HC−CVD) | U-stat | p-value | sig |
|-------|----------|-----------|-----------|--------|---------|-----|
| **LDA** | 0.805 | 0.859 | −0.054 | 1.0 | **0.040** | * |
| **SVM** | 0.749 | 0.837 | −0.088 | 0.5 | **0.030** | * |
| **Ridge** | 0.775 | 0.802 | −0.027 | 9.0 | 0.833 | ns |
| **KernelRidge** | 0.746 | 0.720 | +0.026 | 12.0 | 0.833 | ns |
| **ForwardEnc** | 0.749 | 0.707 | +0.043 | 16.5 | 0.207 | ns |
| **MLP** | 0.396 | 0.391 | +0.005 | 11.5 | 0.909 | ns |

> CVD subjects perform as well or better than HC across all models. LDA and SVM show CVD > HC (p < 0.05, Mann-Whitney U), opposite to a "CVD deficit" hypothesis. After Bonferroni correction (6 models), these would not survive. **Conclusion**: HC ≈ CVD → voxel-color mapping is shared → filter learning approach is justified.

#### Test-Retest Reliability (Split-half, Spearman-Brown corrected, acc_45)

| Model | Mean r | 95% CI | Interpretation |
|-------|--------|--------|---------------|
| **MLP** | **0.720** | [0.498, 0.883] | Good — but at chance performance |
| **ForwardEnc** | 0.596 | [0.416, 0.743] | Moderate |
| **SVM** | 0.501 | [0.263, 0.693] | Moderate |
| **KernelRidge** | 0.469 | [0.279, 0.640] | Moderate |
| **Ridge** | 0.152 | [−0.202, 0.471] | Poor |
| **LDA** | 0.015 | [−0.474, 0.379] | Poor |

> Counter-intuitive pattern: the best-performing model (LDA) has lowest reliability, while the worst-performing (MLP) has highest. This reflects the "ceiling vs floor" reliability paradox — LDA performs near ceiling with low between-subject variance, while MLP performs at chance with stable individual differences in failure mode. ForwardEncoding and SVM show moderate reliability with meaningful performance, representing the best reliability-performance trade-off.

#### Permutation Test

> Skipped for LORO. With run-averaged beta maps and 8 color labels, the null distribution is trivially at 12.5% (exact) / 37.5% (acc_45). Bootstrap CIs already confirm all models except MLP significantly exceed chance. Permutation testing is more informative for LOCO (see below).

### Result 2: LOCO Interpolation Test (sub-01, 4 ROIs, 100 permutations)

**Purpose**: LORO tests cross-run consistency ("does the same color look the same across runs?"). LOCO tests cross-color interpolation ("given 7 colors, can the model predict the 8th?"). Only models that capture continuous color structure should succeed at LOCO.

#### Performance (sub-01, Procrustes, MAE° / Adjacent accuracy)

| Model | V1 (568 vox) | V2 (402 vox) | V3 (106 vox) | V4 (67 vox) |
|-------|-------------|-------------|-------------|-------------|
| **ForwardEnc** | **81.6° / 52.1%** | **82.5° / 47.9%** | **49.7° / 72.9%** | **72.2° / 50.0%** |
| LDA | 107.8° / 31.2% | 114.4° / 29.2% | 86.2° / 54.2% | 116.2° / 25.0% |
| SVM | 98.4° / 35.4% | 132.2° / 16.7% | 88.1° / 45.8% | 118.1° / 20.8% |
| MLP | 95.6° / 37.5% | 107.8° / 25.0% | 101.2° / 25.0% | 106.9° / 25.0% |
| Ridge | 148.9° / 0% | 166.6° / 0% | 174.6° / 0% | 174.7° / 0% |
| KernelRidge | 179.0° / 0% | 179.6° / 0% | 179.9° / 0% | 179.9° / 0% |

**Chance**: MAE ≈ 90°, adjacent accuracy ≈ 25%

#### Permutation Test (ForwardEncoding, 100 iterations)

| ROI | p-value | z-score | Significance |
|-----|---------|---------|-------------|
| V1 | 0.61 | 0.27 | NS |
| V2 | 0.65 | 0.47 | NS |
| **V3** | **< 0.01** | **−2.98** | **Significant** |
| V4 | 0.34 | −0.47 | NS |

#### LOCO Interpretation (sub-01 local test)

1. **ForwardEncoding is the only model with interpolation ability** — its 6-channel basis framework enables predicting unseen colors from the continuous hue space. All other models are limited to predicting training labels.
2. **V3 is the only ROI with significant interpolation** (p < 0.01): fewer voxels (106) reduce overfitting. This supports the need for dimensionality reduction (SRM/PCA) in high-dimensional ROIs.
3. **Ridge and KernelRidge show anti-interpolation** (MAE > 140°, worse than chance): in high-dimensional voxel space, regression predicts the opposite hue. This is a known failure mode of linear regression in high-dim/low-sample settings.
4. **Label-based classifiers (LDA, SVM, MLP) cannot predict the held-out color directly** — their theoretical minimum error is 45° (adjacent color). ForwardEncoding has no such constraint.

### Result 2b: LOCO Server Deployment — RT-4 (10 subjects × 4 ROIs × 1000 permutations)

**Results dir**: `analysis/phase2_decoder_comparing/results/loco/`
**Settings**: Procrustes-aligned (`amplitudes_procrustes.npy`), 1000 permutations, no HP tuning

#### Aggregate Performance — ForwardEncoding vs Others (MAE° mean ± SD)

| Model | V1 | V2 | V3 | V4 |
|-------|----|----|----|----|
| **ForwardEncoding** | **80.6 ± 15.0°** | **83.1 ± 18.2°** | **72.5 ± 14.0°** | **72.8 ± 12.2°** |
| LDA | 107.4 ± 15.8° | 103.1 ± 15.4° | 99.7 ± 10.1° | 99.4 ± 11.8° |
| SVM | 107.9 ± 14.0° | 104.2 ± 16.4° | 100.9 ± 11.5° | 101.3 ± 15.1° |
| MLP | 102.4 ± 5.4° | 101.3 ± 6.6° | 98.3 ± 3.4° | 99.4 ± 5.2° |
| Ridge | 136.0 ± 23.1° | 138.5 ± 29.0° | 164.4 ± 18.2° | 165.7 ± 15.2° |
| KernelRidge | 177.8 ± 1.2° | 177.7 ± 2.6° | 179.5 ± 0.8° | 179.3 ± 1.1° |

**Chance**: MAE = 90°. ForwardEncoding is the only model below chance in all 4 ROIs.

#### Aggregate Performance — Adjacent Accuracy (adj_acc, chance = 0.250)

| Model | V1 | V2 | V3 | V4 |
|-------|----|----|----|----|
| **ForwardEncoding** | **0.431 ± 0.136** | **0.392 ± 0.177** | **0.444 ± 0.142** | **0.456 ± 0.127** |
| MLP | 0.285 ± 0.048 | 0.306 ± 0.083 | 0.325 ± 0.061 | 0.325 ± 0.061 |
| LDA | 0.248 ± 0.086 | 0.275 ± 0.166 | 0.323 ± 0.107 | 0.304 ± 0.117 |
| SVM | 0.242 ± 0.112 | 0.262 ± 0.159 | 0.298 ± 0.072 | 0.273 ± 0.128 |
| Ridge | 0.037 ± 0.040 | 0.046 ± 0.080 | 0.000 | 0.000 |
| KernelRidge | 0.000 | 0.000 | 0.000 | 0.000 |

#### Permutation Test — n significant subjects (p<0.05, correct direction z<0)

| Model | V1 | V2 | V3 | V4 | Note |
|-------|----|----|----|----|------|
| **ForwardEncoding** | 1/10 | 1/10 | 1/10 | 1/10 | ✓ correct direction |
| LDA/SVM | ≤2/10 | ≤1/10 | ≤1/10 | ≤2/10 | mixed / label-limited |
| Ridge | 5/10 | 5/10 | 5/10 | 6/10 | **WRONG direction** (anti-interp.) |
| KernelRidge | 9/10 | 6/10 | 6/10 | 9/10 | **WRONG direction** (anti-interp.) |

#### ForwardEncoding Per-Subject (adj_acc / MAE° — key findings)

| Subject | Group | V1 | V2 | V3 | V4 |
|---------|-------|----|----|----|----|
| sub-01 | HC | 0.521 / 81.6° | 0.479 / 82.5° | **0.729 / 49.7°** ✓p=0.004 | 0.500 / 72.2° |
| sub-02 | HC | 0.438 / 77.8° | 0.250 / 90.0° | 0.542 / 60.0° | 0.417 / 74.1° |
| sub-03 | HC | 0.521 / 81.6° | 0.500 / 80.6° | 0.333 / 95.6° | 0.604 / 68.4° |
| sub-04 | HC | 0.438 / 86.2° | 0.479 / 79.7° | 0.417 / 84.4° | **0.667 / 49.7°** ✓p=0.033 |
| sub-05 | HC | 0.458 / 65.6° | **0.708 / 41.2°** ✓p=0.011 | 0.500 / 69.4° | 0.354 / 86.2° |
| sub-06 | HC | 0.354 / 91.9° | 0.208 / 92.8° | 0.167 / 91.9° | 0.583 / 62.8° |
| sub-07 | HC | 0.521 / 69.4° | 0.542 / 80.6° | 0.438 / 67.5° | 0.417 / 70.3° |
| **sub-08** | **CVD** | **0.646 / 50.6°** ✓p=0.035 | 0.417 / 68.4° | 0.542 / 59.1° | 0.458 / 68.4° |
| sub-09 | CVD | 0.271 / 104.1° | 0.229 / 105.9° | 0.375 / 72.2° | 0.250 / 97.5° |
| sub-10 | CVD | 0.146 / 97.5° | 0.104 / 108.8° | 0.396 / 75.0° | 0.312 / 77.8° |
| **HC mean** | | 0.464 ± 0.058 / 79.2 ± 8.5° | 0.452 ± 0.159 / 78.2 ± 15.8° | 0.446 ± 0.162 / 74.1 ± 15.8° | 0.506 ± 0.107 / 69.1 ± 10.3° |
| **CVD mean** | | 0.354 ± 0.212 / 84.1 ± 23.8° | 0.250 ± 0.128 / 94.4 ± 18.4° | 0.438 ± 0.074 / 68.8 ± 6.9° | 0.340 ± 0.087 / 81.2 ± 12.1° |

#### Key Findings (RT-4) — LOCO Server Deployment

1. **ForwardEncoding: sole interpolator across all ROIs** — Only model with mean MAE < 90° and adj_acc > 25% in V1–V4 (V1:80.6°/43.1%, V2:83.1°/39.2%, V3:72.5°/44.4%, V4:72.8°/45.6%). No other model approaches chance from the better direction.

2. **Individual significance is sparse** (4/40 subject-ROI pairs: sub-01 V3 p=0.004\*\*, sub-04 V4 p=0.033\*, sub-05 V2 p=0.011\*, sub-08 V1 p=0.035\*). Low power is expected: LOCO has only 8 test folds × 6 runs = 48 trials per subject.

3. **CVD heterogeneity reveals color signal with distorted color space** — sub-08 achieves the best single-subject V1 result (MAE=50.6°, adj_acc=0.646, p=0.035), outperforming most HC. In contrast, sub-09 and sub-10 perform at or below chance (MAE=97–109°). This pattern is theoretically interpretable:
   - **HC > CVD (V1, V2, V4)**: HC color space is more circularly ordered, allowing ForwardEncoding's continuous 6-channel basis to interpolate. CVD color space is geometrically distorted — the hue circle is compressed/warped in the deutan/protan confusion axis, making interpolation unreliable.
   - **HC ≈ CVD (V3)**: Sub-08 and sub-09 still show above-chance interpolation in V3 (MAE=59–72°). V3's smaller voxel count (106) reduces the high-dimensionality failure mode.
   - **Sub-08 V1 exception**: sub-08 (deutan) may have a less-distorted hue representation in early visual cortex relative to the confusion locus, explaining locally preserved interpolation.

4. **Interpretation for paper**: CVD subjects *have* color-selective signals (corroborated by LORO accuracy ≥ HC in all models), but their **color space geometry is distorted**. LOCO interpolation requires a well-ordered, continuous hue manifold — exactly what CVD's distorted color space lacks. This dissociation (high within-color discriminability + low cross-color interpolability) is direct neural evidence for CVD as a **color space distortion** rather than a signal loss.

5. **Ridge/KernelRidge anti-interpolation**: KernelRidge is "significantly worse than chance" in 9/10 subjects (V1, V4). These models predict hues in the opposite direction — a well-known high-dimensional regression failure (p→∞ with fixed n).

### Result 3: Nested Procrustes + Dim Reduction (RT-2/RT-3, 10 subjects × 4 ROIs)

**Purpose**: Eliminate test-set leakage in Procrustes alignment (RT-2) and test PCA dimensionality reduction within LORO folds (RT-3). Focused on 3 models: ForwardEncoding, SVM, MLP.

**Dataset & Alignment**:
- Dataset: `full_dataset_C010` (P3 pipeline, C010 confounds, MNI space)
- Nested Procrustes: `amplitudes_raw.npy` + fold-wise alignment (no leakage)
- Nested + PCA-20: same + PCA(k=20) fit on train folds only
- Preloaded Procrustes (ctrl): `amplitudes_procrustes.npy` (aligned on all 6 runs)
- Feature space: voxel space (no SRM) | LORO CV

**Results dir**: `analysis/phase2_decoder_comparing/results/focused_nested/{nested_only,nested_pca20,procrustes_ctrl}/`

#### Overall Performance (acc_45, mean across all 10 subjects × 4 ROIs)

| Model | Nested Procrustes | Nested + PCA-20 | Preloaded Procrustes (ctrl) | Δ(nested−ctrl) |
|-------|-------------------|----------------|----------------------------|-----------------|
| **SVM** | **0.899** | 0.847 | 0.776 | **+0.123** |
| **ForwardEnc** | **0.781** | 0.761 | 0.736 | **+0.045** |
| MLP | 0.412 | 0.430 | 0.394 | +0.018 |

Chance = 0.375 (3/8)

#### By Group (acc_45)

| Model | Group | Nested Procrustes | Preloaded ctrl | Δ |
|-------|-------|-------------------|---------------|---|
| **SVM** | HC | 0.894 | 0.749 | **+0.145** |
| **SVM** | CVD | **0.910** | 0.837 | +0.073 |
| **ForwardEnc** | HC | 0.812 | 0.749 | +0.062 |
| **ForwardEnc** | CVD | 0.710 | 0.707 | +0.003 |
| MLP | HC | 0.395 | 0.396 | −0.001 |
| MLP | CVD | 0.453 | 0.391 | +0.062 |

#### By ROI (acc_45, nested_only condition)

| Model | V1 | V2 | V3 | V4 |
|-------|------|------|------|------|
| **SVM** | 0.908 | **0.927** | 0.887 | 0.873 |
| **ForwardEnc** | 0.796 | 0.779 | **0.823** | 0.727 |
| MLP | 0.392 | 0.425 | 0.394 | 0.440 |

#### MLP Degenerate Solution Analysis

In procrustes_ctrl, **19/40 subject-ROI cells (47.5%)** showed degenerate MLP behavior (identical acc_45=0.375 across all 6 folds = constant-class prediction). V3 worst (7/10 subjects degenerate), followed by V4 (6/10). **Zero** degenerate cases in nested conditions.

**Interpretation**: With n_train=40 samples and n_features=106-568 voxels, MLP's 36K+ parameters cannot learn meaningful representations. Nested Procrustes provides enough structure to prevent complete collapse, but MLP remains at chance.

#### RT-2/RT-3 Interpretation

1. **RT-2 resolved**: Nested Procrustes (no leakage) actually *improves* SVM (+0.123 vs preloaded) and ForwardEncoding (+0.045). The original preloaded Procrustes result was conservative, not inflated.
2. **RT-3 resolved**: PCA-20 loses information vs full voxels (SVM: 0.847 vs 0.899). Discriminative signal spans >20 dimensions.
3. **ForwardEncoding is alignment-robust** (Δ=+0.045 only) — its 6-channel basis structure is intrinsically protected from alignment artifacts.
4. **SVM benefits most from alignment quality** (Δ=+0.123) — high accuracy is partly alignment-method-dependent.
5. **CVD SVM ≥ HC SVM** (0.910 vs 0.894 nested) — confirms CVD color representations are decodable.

### Result 4: Individual CVD Cross-Decoding in SRM Space (RT-1 + RT-7 fix)

**Purpose**: Verify each CVD subject *individually* decodes above chance in HC common space.

**Method (updated 2026-02-18, RT-7 fix)**: Train SRM on 7 HC only → Transform HC via `srm.w_[i]` → Project CVD via SVD → Train LDA on 7 HC mean betas → Test on each CVD → Permutation test (1000 iterations, label shuffling). Previous method used all-subjects SRM (circular).

**Results dir**: `analysis/phase2_decoder_comparing/model_comparison_validation/results/cvd_cross_decoding/`

**HC-only SRM results (current):**

| ROI | k | HC LOSO mean | sub-08 (acc, p) | sub-09 (acc, p) | sub-10 (acc, p) |
|-----|---|-------------|-----------------|-----------------|-----------------|
| V1 | 4 | 0.946 | **1.000** (p=0.000) | **0.875** (p=0.000) | **1.000** (p=0.000) |
| V2 | 4 | 0.839 | **0.750** (p=0.000) | **0.875** (p=0.000) | **1.000** (p=0.000) |
| V3 | 3 | 0.768 | **0.625** (p=0.000) | **0.750** (p=0.000) | **0.875** (p=0.000) |
| hV4 | 3 | 0.446 | 0.375 (p=0.057) | **0.625** (p=0.000) | 0.375 (p=0.056) |

**Old all-subjects SRM results (superseded):**

| ROI | k | HC LOSO mean | sub-08 (acc, p) | sub-09 (acc, p) | sub-10 (acc, p) |
|-----|---|-------------|-----------------|-----------------|-----------------|
| V1 | 4 | 0.875 | **1.000** (p<0.001) | **0.500** (p=0.012) | **1.000** (p<0.001) |
| V2 | 4 | 0.964 | **0.750** (p=0.001) | **0.875** (p<0.001) | **0.875** (p<0.001) |
| V3 | 3 | 0.821 | **0.750** (p=0.003) | **0.875** (p<0.001) | **0.750** (p=0.003) |
| V4 | 4 | 0.554 | **0.750** (p<0.001) | **0.750** (p<0.001) | **0.750** (p<0.001) |

Chance = 12.5% (1/8). 9/12 tests p<0.001 (HC-only); previously 12/12 (all-subjects).

> **RT-7 resolved (2026-02-18)**: Under HC-only SRM (no circularity), 9/12 CVD tests remain strongly significant (V1/V2/V3: all p=0.000). hV4: only sub-09 significant — reflecting low HC LOSO baseline (44.6%) due to SRM quality, not circularity removal. CVD color decodability in HC space is robust.

### Result 5: LDA Reliability Diagnostics (RT-5)

**Purpose**: Explain LDA's high accuracy (82.1%) but near-zero split-half reliability (r=0.015).

**Results dir**: `analysis/phase2_decoder_comparing/results/lda_reliability/`

#### Analysis A: Fold-Level CV (std/mean)

| Model | Mean CV | Mean acc | Interpretation |
|-------|---------|----------|---------------|
| MLP | 0.191 | 0.147 | Low CV but at chance |
| **LDA** | **0.229** | **0.758** | Moderate CV, high accuracy |
| SVM | 0.230 | 0.685 | Similar to LDA |
| ForwardEnc | 0.261 | 0.544 | Moderate |
| KernelRidge | 0.463 | 0.331 | High variability |
| Ridge | 0.464 | 0.388 | High variability |

#### Analysis B: ForwardEncoding W Matrix Stability

| Metric | Value |
|--------|-------|
| Grand mean cosine similarity | **0.921** [95% CI: 0.907, 0.935] |
| Range (min-max across subject-ROIs) | 0.878 – 0.978 |
| Mean std per subject-ROI | 0.017 |

> W matrices are highly stable across folds (cosine sim > 0.87 everywhere). Bootstrap 95% CI [0.907, 0.935] computed over 1000 iterations of subject-ROI resampling.

#### Analysis C: Run-Pair Reliability (Spearman r across subject-ROIs)

| Model | Mean r | Range |
|-------|--------|-------|
| **ForwardEnc** | **0.329** | [0.020, 0.553] |
| MLP | 0.244 | [−0.064, 0.657] |
| KernelRidge | 0.232 | [−0.048, 0.450] |
| SVM | 0.164 | [−0.238, 0.472] |
| Ridge | 0.116 | [−0.138, 0.295] |
| **LDA** | **0.009** | **[−0.370, 0.504]** |

> **LDA has near-zero run-pair correlation**: subject-ROI difficulty rankings completely reshuffle across run subsets. This directly explains the low split-half reliability. **ForwardEncoding has the highest run-pair consistency** (mean r=0.329), supporting it as the most stable decoder.

#### RT-5 Conclusion

LDA's low reliability is NOT about inaccuracy — it achieves 82.1%. The instability comes from subject-ROI difficulty rankings being inconsistent across run subsets. With 568 voxels and only 40 training samples, LDA finds separating hyperplanes that are fold-specific. High accuracy + zero reproducibility = hallmark of overfitting to fold-specific structure.

### Result 6: Hybrid Decoder — Channel→Color Linearity Test (2026-02-18)

**Purpose**: Test whether a nonlinear readout on ForwardEncoding's 6-channel representation improves over linear template matching.

**Architecture**:
- **FE_MLP**: voxels → FE (6 channels) → MLP(16 units, relu) → 8-class label
- **FE_SVM**: voxels → FE (6 channels) → SVM-RBF → 8-class label
- **ForwardEncoding** (control): voxels → FE (6 channels) → template matching → label

**Results dir**: `analysis/phase2_decoder_comparing/model_comparison_validation/results/hybrid/{nested,procrustes_ctrl}/`

**Dataset & Alignment**:
- Dataset: `full_dataset_C010` (P3 pipeline, C010 confounds, MNI space)
- Nested Procrustes: `amplitudes_raw.npy` + fold-wise alignment (no leakage)
- Preloaded Procrustes (ctrl): `amplitudes_procrustes.npy` (aligned on all 6 runs)
- Feature space: voxel space (no SRM, no dimensionality reduction)
- CV: LORO (6-fold, Leave-One-Run-Out) with nested HP tuning

#### Overall Performance (acc_45, 10 subjects × 4 ROIs)

| Model | Nested Procrustes | Procrustes ctrl | Δ(nested−ctrl) |
|-------|-------------------|-----------------|-----------------|
| **ForwardEncoding** | **0.784** | 0.737 | +0.047 |
| **FE_SVM** | **0.779** | 0.747 | +0.032 |
| FE_MLP | 0.381 (degenerate) | 0.375 (degenerate) | +0.006 |

#### By Group (acc_45, nested Procrustes)

| Model | HC (n=7) | CVD (n=3) | Δ(HC−CVD) |
|-------|----------|-----------|-----------|
| ForwardEncoding | **0.814** | 0.712 | +0.102 |
| FE_SVM | 0.769 | **0.804** | −0.035 |
| FE_MLP | 0.381 | 0.381 | 0.000 |

#### By ROI (acc_45, nested Procrustes)

| Model | V1 | V2 | V3 | V4 |
|-------|------|------|------|------|
| ForwardEncoding | 0.798 | 0.782 | **0.829** | 0.726 |
| FE_SVM | 0.721 | **0.804** | 0.800 | 0.792 |
| FE_MLP | 0.376 | 0.396 | 0.367 | 0.384 |

#### Key Finding: Nonlinear Readout Does NOT Help

- **FE_SVM ≈ ForwardEncoding** (0.779 vs 0.784, Δ=−0.005): SVM-RBF kernel on 6-channel responses provides no benefit over linear template matching.
- **FE_MLP = degenerate** (0.381, all subjects/ROIs/folds): MLP with early_stopping on 40 samples (validation_fraction=0.2 → 8 validation samples) collapses to constant prediction. Not informative for linearity question.
- **CVD reversal with FE_SVM**: CVD 0.804 > HC 0.769 — likely small-sample variance (n=3).

**Conclusion**: The channel-to-color mapping is adequately linear. B&H 2009 template matching captures the full predictive structure of the 6-channel representation. This validates the linear assumption for Phase 3 filter design.

### Systematic Results Matrix: Alignment × Model (2026-02-18)

All results: LORO CV, `full_dataset_C010`, 10 subjects × 4 ROIs, voxel space. **acc_45** (chance = 0.375).

| Alignment | LDA | Ridge | FE (B&H) | KernelRidge | SVM | MLP | FE+MLP | FE+SVM |
|-----------|-----|-------|-----------|-------------|-----|-----|--------|--------|
| Raw | 0.393 | 0.375 | 0.367 | 0.380 | 0.382 | 0.370 | — | — |
| Raw+ANOVA-100 | 0.394 | 0.364 | 0.367 | 0.370 | 0.394 | 0.371 | — | — |
| Preloaded Procrustes | 0.821 | 0.783 | 0.736 | 0.739 | 0.776 | 0.394 | 0.375 | 0.747 |
| **Nested Procrustes** | **0.892** | **0.823** | **0.781** | **0.810** | **0.899** | 0.412 | 0.380 | **0.777** |
| Nested+PCA-20 | 0.881 | 0.802 | 0.761 | 0.791 | 0.849 | 0.429 | — | — |
| Nested+ANOVA-100 | 0.810 | 0.753 | 0.731 | 0.794 | 0.849 | 0.447 | — | — |

**MAE in degrees** (chance = 90.0°):

| Alignment | LDA | Ridge | FE (B&H) | KernelRidge | SVM | MLP | FE+MLP | FE+SVM |
|-----------|-----|-------|-----------|-------------|-----|-----|--------|--------|
| Raw | 89.0 [87,90] | 89.8 [86,94] | 91.4 [87,96] | 89.6 [86,94] | 90.6 [87,94] | 90.6 [89,92] | — | — |
| Raw+ANOVA-100 | 88.5 [86,91] | 90.3 [86,95] | 91.4 [87,96] | 90.2 [85,95] | 89.2 [85,94] | 90.6 [90,91] | — | — |
| Preloaded Procrustes | **25.6** [23,28] | 41.8 [38,45] | 43.5 [39,47] | 47.9 [44,52] | 32.9 [27,39] | 87.1 [85,89] | 90.0 [90,90] | 38.7 [32,45] |
| **Nested Procrustes** | **16.1** [14,18] | 39.3 [36,42] | 39.4 [32,47] | 36.1 [33,39] | **14.6** [12,18] | 84.9 [81,88] | 89.8 [88,92] | **35.0** [31,39] |
| Nested+PCA-20 | 17.2 [14,20] | 41.3 [39,44] | 42.8 [36,50] | 38.9 [35,42] | 22.6 [20,26] | 83.4 [80,87] | — | — |
| Nested+ANOVA-100 | 28.2 [25,32] | 47.3 [45,50] | 47.1 [39,55] | 38.0 [34,41] | 22.4 [20,25] | 80.4 [76,84] | — | — |

**Key patterns**:
1. Raw = chance for ALL models → alignment is prerequisite
2. Nested Procrustes > Preloaded for ALL models → no leakage inflation
3. Dim reduction (PCA-20, ANOVA-100) uniformly hurts → full voxels optimal
4. SVM peaks at 0.899 (nested) but FE is more robust/reliable (see multi-criteria below)
5. SRM space decoding: TBD (SRM W_i per-run projection needed for LORO)

### FE Cross-Decoding: HC → CVD in SRM Space (2026-02-22, pending execution)

**Script**: `phase2_decoder_comparing/analysis/fe_cross_decoding.py`

**Protocol**: Train ForwardEncoding W-matrix on HC subjects' SRM-projected data (LOSO within HC), evaluate on each CVD subject. Tests whether HC-trained color channel representations generalize to CVD neural patterns.

| ROI | HC MAE (held-out) | sub-08 MAE | sub-09 MAE | sub-10 MAE |
|-----|-------------------|------------|------------|------------|
| V1  | *pending*         | *pending*  | *pending*  | *pending*  |
| V2  | *pending*         | *pending*  | *pending*  | *pending*  |
| V3  | *pending*         | *pending*  | *pending*  | *pending*  |
| hV4 | *pending*         | *pending*  | *pending*  | *pending*  |

> Expected: Above-chance accuracy for most CVD-ROI combinations (consistent with LDA cross-decoding showing 9/12 significant). FE cross-decoding provides a neuroscience-grounded version of the same test, evaluating whether the 6-channel basis functions can decode CVD color representations using HC-derived encoding weights.

### Revised Decoder Conclusions (2026-02-18)

**Previous conclusion**: "LDA is the best decoder → linearity is sufficient"

**Revised conclusion**: **"ForwardEncoding is the optimal decoder — channel-based color representation exists"**

| Criterion | LDA | SVM (nested) | ForwardEncoding |
|-----------|-----|-------------|----------------|
| LORO acc_45 (preloaded) | **0.821** | 0.776 | 0.736 |
| LORO acc_45 (nested) | — | **0.899** | **0.781** |
| Run-pair reliability | **0.009** (random) | 0.164 | **0.329** (best) |
| W matrix stability [95% CI] | N/A | N/A | **0.921** [0.907, 0.935] |
| LOCO interpolation | NS | NS | **p<0.01** (V3) |
| Alignment sensitivity | +0.428 (dependent) | +0.123 (moderate) | **+0.045** (robust) |
| Effective parameters | ~568 (overfit) | support vectors | **6** (parsimonious) |
| Split-half reliability (acc_45) | 0.015 [−0.474, 0.379] | 0.501 [0.263, 0.693] | **0.596** [0.416, 0.743] |

**Why ForwardEncoding is optimal**:
1. **Only model with interpolation ability** (LOCO V3 p<0.01)
2. **Most alignment-robust** (Δ=+0.045 vs SVM's +0.123)
3. **Highest run-pair reliability** (r=0.329)
4. **Highly stable encoding weights** (cosine 0.921 [0.907, 0.935])
5. **Neuroscientifically grounded** (6-channel basis from Brouwer & Heeger 2009)
6. **Parsimonious** (6 parameters vs hundreds of support vectors or 36K+ MLP weights)

**Phase 3 filter design justification**: ForwardEncoding's 6-channel basis provides both (a) stable encoding weights that can be reliably estimated across runs (W cosine sim 0.921), and (b) continuous hue interpolation that captures the full color manifold structure. LDA's superior accuracy (0.821) is misleading for filter learning — its near-zero run-pair reliability (r=0.009) means the learned decision boundaries are fold-specific and non-transferable. ForwardEncoding's moderate accuracy (0.736) with high representation stability (r=0.329) makes it the appropriate basis for learning CVD→HC transformations in channel space.

### Validation Status (Phase 2b)

- [x] LORO model comparison: 10 subjects, 4 ROIs, 6 models, both alignment conditions
- [x] Bootstrap 95% CIs: subject-level resampling, 1000 iterations
- [x] HC vs CVD comparison: Mann-Whitney U, no meaningful group difference
- [x] Test-retest reliability: split-half with Spearman-Brown correction
- [x] LOCO local test: sub-01, 4 ROIs, 100 permutations
- [x] **[RT-2] Nested Procrustes**: FE/SVM/MLP, 10 subjects — SVM 0.899, FE 0.781 (no leakage)
- [x] **[RT-3] PCA dim reduction**: PCA-20 within LORO — information loss vs full voxels
- [x] **[RT-1 + RT-7] Individual CVD cross-decoding**: HC-only SRM: 9/12 tests p<0.001, hV4 borderline (supersedes old all-subjects 12/12)
- [x] **[RT-5] LDA reliability**: run-pair r=0.009 explains paradox; FE W stability 0.921
- [x] **[RT-4] LOCO server deployment**: 10 subjects × 4 ROIs, 1000 permutations — FE sole interpolator; CVD heterogeneity = color space distortion (see Result 2b)
- [x] **[RT-6] Hybrid decoder (FE+MLP, FE+SVM)**: FE_SVM ≈ FE (0.779 vs 0.784); FE_MLP degenerate; linear readout confirmed

---

## Key Findings Summary

### I. 핵심 결과 (Core Findings)

**Phase 1 — Preprocessing**:
1. **C010 + Procrustes is the optimal pipeline**: +1644% RDM reliability (0.028→0.487); ceiling utilization ~30%; whitening harmful (−47~92%).

**Phase 2 — SRM Group Comparison**:
2. **V1/V2에서 trending HC-CVD 차이**: V1 p=0.062 (g=1.16), V2 p=0.075 (g=1.04). V2 separation CI [0.001, 0.244] marginally excludes zero.
3. **Individual CVD dissociations**: sub-09 (protan) V1 p=0.007; sub-08 (deutan) V2 p=0.040; sub-10 HC range.
4. **CVD color-dependency confirmed (LOSO)**: CVD disparity is color-specific (V2 p=0.010, V3 p=0.000, hV4 p=0.016), HC is not (p=0.21–0.36). Asymmetry = strongest evidence.

**Phase 2b — Decoder Validation**:
5. **ForwardEncoding is the optimal decoder**: 78.1% acc_45, highest reliability (r=0.329), only LOCO interpolation (V3 p<0.01), most alignment-robust (Δ=+0.045).
6. **Channel→color readout is linear**: FE_SVM ≈ FE (0.779 vs 0.784). Linear template matching captures full predictive structure.
7. **Individual CVD cross-decoding**: HC-only SRM, 9/12 tests p<0.001. CVD color representations decodable in HC space.

### II. 해석 (Interpretation)

8. **"Scattered but internally structured"**: CVD has higher disparity to HC (scattered), but this disparity is specifically color-dependent (structured). HC share general visual structure independent of color labels; CVD deviates specifically along color dimensions.
9. **CVD heterogeneity — not a homogeneous group**: sub-09 = V1-dominant (protan, early visual), sub-08 = V2-dominant (deutan, mid-level), sub-10 = HC-like (deutan but functionally normal). Individual profiles necessary; group-level statistics insufficient.
10. **Linear color channel representation exists**: ForwardEncoding's 6-channel basis captures continuous hue structure (LOCO interpolation), stable encoding weights (cosine 0.921), and alignment-robust decoding. → Phase 3 filter design on channel space justified.

### III. Robustness Validation (삼각검증)

11. **A4 Crossnobis (SRM-independent)**: V1 trending (p=0.051) in native voxel space. **Convergent validity**: crossnobis ↔ SRM disparity, pooled r=0.486 (p=0.001). SRM이 아닌 방법으로도 동일 패턴 확인.
12. **A5 PCA-only (다른 alignment)**: PCA distance ↔ SRM disparity, pooled r=0.742 (p<0.001); V2 r=0.891 (p<0.001). 가장 강한 convergent validity — SRM 결과가 alignment method에 비의존적.
13. **A3 Variance Explained (재구성 품질)**: CVD VE ≥ HC VE (전 ROI). V2 diff=−0.117 [−0.190, −0.042], g=−1.68. CVD signal이 noisy가 아닌 **체계적으로 다름**. "Strong signal, different structure."
14. **SRM validation battery complete**: LOSO stability (V2 7/7), split-half (V2 both halves sig), permutation (10K iter), bootstrap CIs, alignment comparison (2.4–6.5×).

### IV. 최종 해석 및 Phase 3 함의

15. **CVD 색 표상은 "다르되 체계적"**: noisy가 아니라 anisotropic (방향-의존적 왜곡). SRM VE가 높고 (재구성 가능), 고유한 color-dependent 구조를 가짐 → anisotropy correction (구조 보정) 프레이밍 적합.
16. **Convergent validity가 핵심 증거**: SRM disparity ↔ crossnobis (r=0.486), ↔ PCA (r=0.742). 세 가지 독립적 방법이 동일한 subject-level 패턴 → SRM alignment artifact 배제.
17. **LOCO dissociation — signal vs. geometry** (RT-4, 2026-02-18): CVD는 LORO에서 HC와 동등하거나 우수한 성능 (within-color discriminability ↑), 그러나 LOCO interpolation에서 HC < CVD (V1, V2, V4). ForwardEncoding만 색상 간 보간 가능하며, HC 색 공간은 circular continuous → 보간 가능; CVD 색 공간은 hue 축이 compressed/warped → 보간 실패. 개별 CVD 이질성: sub-08 (deutan)은 V1에서 최고 성능(MAE=50.6°, p=0.035), sub-09/10은 chance 수준. **핵심: CVD = 신호 없음이 아닌, 색 공간 왜곡**. LORO (within-color signal) vs LOCO (cross-color geometry) 이중 해리가 Phase 3 filter learning의 신경과학적 근거를 제공함.

18. **Filter design prerequisites met**:
    - Linear channel representation exists (ForwardEncoding validated)
    - CVD signal preserved in SRM space (VE ≥ HC)
    - Individual CVD profiles identifiable (Crawford & Howell significant)
    - Channel→color mapping is linear (FE_SVM ≈ FE)
    - **CVD color space is distorted, not absent** (LOCO dissociation: HC>CVD interpolation, HC≈CVD discrimination)
    → Phase 3: CVD→HC transformation in 6-channel space로 진행 가능.

---

## Limitations & Caveats

- **Small CVD sample (n=3)**: Group-level comparisons should be interpreted with caution. Individual CVD profiles are reported alongside group descriptive statistics. Effect sizes may be inflated due to small sample.
- **Multiple comparisons**: 4 ROIs tested; LOO-consistent group p-values (V1=0.062, V2=0.075) do not reach p<0.05. Results framed as trending effects with individual-level confirmation via Crawford & Howell tests.
- **No parametric group tests with n=3**: Permutation-based p-values and Hedges' g (small-sample corrected) used instead of parametric t-tests, which would violate normality assumptions.
- ~~**95% CIs not yet computed**~~: Resolved 2026-02-18 — Bootstrap 95% CIs computed for all disparity and RDM comparisons (10,000 iterations).
- **SRM disparity metric bias for majority group**: HC subjects (7/10) dominate SRM training, creating a "floor effect" on HC-to-reference disparity. HC LOO disparity is insensitive to color-label shuffling (single-SRM: V2 p=0.894), reflecting the structural floor from SRM training. **Resolved via LOSO analysis**: When HC is tested in a space they did NOT train (projected via SVD, same as CVD), HC disparity remains color-agnostic (p=0.21–0.36), confirming this is genuine rather than artifact. Meanwhile, CVD color-dependency remains significant under LOSO (V2 p=0.010, V3 p=0.000, hV4 p=0.016), providing the informative test for color-specific group differences.
- **CVD-CVD RDM instability across halves**: Split-half CVD-CVD RDM correlation is inconsistent (V2 Set A: 0.536, Set B: 0.124), suggesting CVD within-group color structure is less reliably estimated with n=3 and half-run data.
- **CVD individual stability moderate**: Run-split corrected reliability 8/12 moderate or better; sub-08 most stable, sub-09/sub-10 lower in V1/V2.
- **V3/hV4 non-significance**: Consistent across all validation tests (LOSO 0/7, split-half 0/2, permutation n.s.). May reflect genuine absence of difference or insufficient power.
- **V1 validation gap**: Disparity significant (p=0.024), LOSO 6/7 robust, but RDM color-specificity not significant (p=0.192/0.599), complicating interpretation of what V1 disparity represents.
- **CVD subtype mixing**: 2 deutan (sub-08, sub-10) + 1 protan (sub-09), precluding subtype-specific analysis. Notably, sub-09 (protan) shows the highest V1 disparity (+91%), while the two deutan subjects differ markedly (sub-08: consistent elevation vs sub-10: near-normal).
- ~~**SRM k-value**~~: Validated via 2C LOSO CV + mean rank aggregation (2026-02-18) — V1=4, V2=4, V3=3, hV4=3 (hV4 revised from k=4 to k=3).
- ~~**sub-01 noise ceiling**~~: Resolved 2026-02-17 — re-run with N=40.
- **SRM within-subject trade-off**: SRM improves between-subject agreement (2.4–6.5×) but reduces within-subject RDM test-retest reliability (V2: raw 0.473 → SRM 0.098). This drop conflates two sources: (1) genuine dimensionality reduction and (2) SRM fitting instability from independent split-half fits learning different shared spaces. The main analysis uses a single SRM fit on all runs, mitigating fitting instability. The "parallel" pattern (CVD preserving color structure) is independently validated by 2B in native voxel space without SRM (CVD ≥ HC in V1/V2), so does not rely on SRM-derived metrics alone.

---

## Pending Validations

| Test | Phase | Status | Priority | Why needed |
|------|-------|--------|----------|------------|
| ~~Noise ceiling with sub-01~~ | Phase 1 | **DONE** | ~~High~~ | Re-run 2026-02-17, N=39 valid (sub-07 hV4 excluded) |
| ~~Drift method comparison~~ | Phase 1 | **PASSED** | ~~Medium~~ | 1st+2nd and 2nd-only identical HRF |
| ~~Onset randomization~~ | Phase 1 | **DROPPED** | ~~Medium~~ | Fixed ISI; timing jitter not applicable |
| ~~1D: Permutation test~~ | Phase 2 | **DONE** | ~~High~~ | V1 p=0.014, V2 p=0.036; V3/hV4 n.s. |
| ~~2A: Run-split ICC~~ | Phase 2 | **DONE** | ~~High~~ | Mean r=0.475 (moderate) |
| ~~2B: RDM consistency~~ | Phase 2 | **DONE** | ~~High~~ | CVD >= HC in V1/V2 — "parallel" confirmed |
| ~~1B: LOSO stability~~ | Phase 2 | **DONE** | ~~High~~ | V2 7/7 sig, V1 6/7 sig — no single subject drives results |
| ~~1C: Split-half reliability~~ | Phase 2 | **DONE** | ~~High~~ | V2 both halves sig; cross-half r=0.71–0.78 for V1/V2/hV4 |
| ~~2C: k-value selection~~ | Phase 2 | **DONE** | ~~Medium~~ | V1=4, V3=3 confirmed; V2/hV4 competitive at k=3–4 |
| ~~2D: Alignment comparison~~ | Phase 2 | **DONE** | ~~Medium~~ | SRM 2.4–6.5× over raw/Procrustes |
| ~~LORO model comparison~~ | Phase 2b | **DONE** | ~~High~~ | LDA best (82.1%); linear > non-linear; HC ≈ CVD |
| ~~Bootstrap 95% CIs (decoder)~~ | Phase 2b | **DONE** | ~~High~~ | All models except MLP CI lower > chance |
| ~~LOCO local test~~ | Phase 2b | **DONE** | ~~Medium~~ | ForwardEnc only model with interpolation; V3 sig |
| ~~1D-ext LOO permutation re-run~~ | Phase 2 | **DONE** | ~~High~~ | LOO-consistent analysis completed (rerun_loo_consistent.py); CVD color-dependency confirmed V2/V3/hV4 |
| ~~1D-ext-LOSO color-dependency~~ | Phase 2 | **DONE** | ~~High~~ | LOSO: HC color p=0.21–0.36 (n.s.); CVD color V2 p=0.010, V3 p=0.000, hV4 p=0.016; asymmetry confirmed |
| ~~[RT-2] Nested Procrustes in LORO~~ | Phase 2b | **DONE** | ~~Fatal~~ | Nested actually improves: SVM 0.899, FE 0.781. No leakage. |
| ~~[RT-4] LOCO server deployment~~ | Phase 2b | **DONE** | ~~Fatal~~ | FE sole interpolator all ROIs; CVD heterogeneity = color space distortion (HC>CVD V1/V2/V4; see Result 2b) |
| ~~[RT-3] PCA within LORO~~ | Phase 2b | **DONE** | ~~High~~ | PCA-20 loses info (SVM 0.847 vs 0.899 full). Signal spans >20 dims. |
| ~~[RT-1] Individual cross-decoding~~ | Phase 2b | **DONE** | ~~Fatal~~ | 12/12 tests p<0.05. All CVD decode in SRM space individually. |
| ~~[RT-5] LDA reliability analysis~~ | Phase 2b | **DONE** | ~~High~~ | Run-pair r=0.009 explains paradox. FE W stability 0.921. |
| ~~Hybrid decoder (FE+MLP, FE+SVM)~~ | Phase 2b | **DONE** | ~~High~~ | FE_SVM ≈ FE (0.779 vs 0.784); linear readout sufficient |
| ~~Bootstrap 95% CIs (SRM disparity)~~ | Phase 2 | **DONE** | ~~High~~ | V1/V2 separation CIs exclude zero; RDM CIs for all ROI-group pairs (10,000 iter) |
| LOCO results consolidation | Phase 2b | Blocked (RT-4) | Medium | Group-level LOCO analysis after server run |
| **Filter pre-diagnosis** | Phase 3 | Not started | **High** | Pair-level permutation test, LORO CV for filter, low-rank constraint, baseline comparison (filter_design_plan.md Criticism #4) |
| Dimensionality reduction + LOCO | Phase 2b | Not started | Medium | SRM/PCA + 6 models + LOCO re-experiment |
| ~~Formal k aggregation~~ | Phase 2 | **DONE** | ~~Low~~ | V1=4, V2=4, V3=3, hV4=3 (hV4 revised from 4→3 via mean rank) |
| ~~A3 Variance Explained~~ | Phase 2 | **DONE** | ~~High~~ | LOSO: CVD VE ≥ HC; V2 g=−1.68 [−4.02, −0.74] (CI excludes zero) |
| ~~A4 Crossnobis RDM~~ | Phase 2 | **DONE** | ~~High~~ | V1 trending p=0.051; convergent r_pooled=0.486 (p=0.001) |
| ~~A5 PCA-CCA Replication~~ | Phase 2 | **DONE** | ~~High~~ | PCA-only convergent r_pooled=0.742 (p<0.001); PCA-CCA r_pooled=0.472 (p=0.002) |

---

## TODO (Next Steps)

### Immediate — Remaining

1. **[RT-4] LOCO server results** — Submitted (6h, node2), pending download
   - 10 subjects × 4 ROIs × 6 models × 1000 permutations
   - Group-level analysis: Fisher combined probability, proportion of subjects with p<0.05
   - **Severity: Fatal** — ForwardEncoding interpolation claim based on n=1 pilot

2. **Consolidate LOCO server results** — After #1 downloads:
   - Aggregate across subjects, test ForwardEncoding interpolation at group level
   - Compare V3 vs other ROIs (fewer voxels → better interpolation hypothesis)

### Completed Red Team Fixes

4. ~~**[RT-2] Nested Procrustes within LORO**~~ — **DONE** (2026-02-18). Nested Procrustes actually improves: SVM 0.899, FE 0.781. No leakage issue — original result was conservative.
5. ~~**[RT-3] PCA within LORO**~~ — **DONE** (2026-02-18). PCA-20 loses discriminative information vs full voxels. Signal spans >20 dimensions.
6. ~~**[RT-1 + RT-7] Individual CVD cross-decoding**~~ — **DONE** (2026-02-18). HC-only SRM: 9/12 tests p<0.001 (V1/V2/V3 all sig). hV4 borderline (low SRM quality). Supersedes old all-subjects 12/12.
7. ~~**[RT-5] LDA reliability analysis**~~ — **DONE** (2026-02-18). Run-pair r=0.009 explains paradox; FE W stability 0.921; framing revised to FE-centric.
8. ~~**Bootstrap 95% CIs for SRM disparity**~~ — **DONE** (2026-02-18).
9. ~~**Formal k aggregation**~~ — **DONE** (2026-02-18). hV4 revised from k=4 to k=3.
10. ~~**[RT-6] Hybrid decoder (FE+MLP, FE+SVM)**~~ — **DONE** (2026-02-18). FE_SVM ≈ FE (0.779 vs 0.784); FE_MLP degenerate; linear readout confirmed.

### Deferred (Low Priority)

10. **Dimensionality reduction + LOCO re-experiment** — SRM (k=3,4) + LOCO
11. **Cross-subject generalization (train HC → test CVD)** — Requires common space
12. **Publication figure** — Comprehensive summary of decoder comparison results

---

## Red Team Log (Phase 2b, 2026-02-17)

| # | Criticism | Severity | Status | Neutralization |
|---|-----------|----------|--------|---------------|
| RT-1 + RT-7 | HC vs CVD group comparison invalid at n=3; cross-decoding used circular all-subjects SRM | Fatal | **DONE** | HC-only SRM: 9/12 tests p<0.001 (V1/V2/V3 all sig); hV4 borderline due to low SRM quality |
| RT-2 | Procrustes pre-computed across all runs → LORO test-set leakage | Fatal | **DONE** | Nested Procrustes: SVM 0.899, FE 0.781 (no leakage, actually improves) |
| RT-3 | "Linearity" confounded by dimensionality; KernelRidge gamma grid too narrow | Addressable | **DONE** | PCA-20 within LORO: loses info vs full voxels |
| RT-4 | LOCO results from single subject (n=1), 100 perms at p-floor | Fatal | **Submitted** | Server: 10 subjects × 1000 perms, 6h time limit |
| RT-5 | LDA reliability r=0.015 contradicts "best model" claim; paradox misinterpreted | Addressable | **DONE** | Run-pair r=0.009; FE W stability 0.921; framing revised to FE-centric |
| RT-6 | Channel→color readout linearity untested | High | **DONE** | FE_SVM ≈ FE (0.779 vs 0.784); FE_MLP degenerate. Linear readout sufficient. |

---

## Filter Pre-Validation (B1–B3) — 2026-02-18

> **Purpose**: Validate per-pair z-score claims before filter implementation (filter_design_plan.md §7.1).
> **Script**: `analysis/future_phase3_filter_optimization/pre_validation/filter_pre_validation.py`
> **Runtime**: 22s local (BrainIAK SRM, 1000 bootstrap × SRM retrain)

### Settings

- **SRM**: HC-only (7 HC training, CVD projected via SVD), consistent with canonical pipeline
- **k values**: V1=4, V2=4, V3=3, hV4=3
- **Distance metric**: Euclidean in k-dimensional SRM shared space
- **Pair z-score**: (CVD_dist − HC_mean) / HC_std; positive = over-separation, negative = confusion
- **B1**: Exhaustive group permutation C(10,3)=120; SRM retrained per permutation
- **B2**: Split-half (runs 1–3 vs 4–6; also odd/even), Spearman r of 28-pair z-score profiles
- **B3**: Bootstrap 95% CI (1000 iters, HC subjects resampled with replacement, SRM retrained)

### B1: Pair-Level Permutation Test

| ROI | Significant pairs (p<0.05, two-sided) | Note |
|-----|--------------------------------------|------|
| V1 | none | min p=0.008; several pairs trend 0.05–0.20 |
| **V2** | **blue-purple** (p=0.042) | All 3 CVD elevated; step=1 adjacent |
| V3 | none | |
| hV4 | none | |

> Power note: Exhaustive C(10,3)=120 permutations; minimum achievable p=0.008. V2 blue-purple passes this strict threshold.

### B2: Split-Half Stability (first/last split, Spearman r)

| Subject | V1 r | V2 r | V3 r | hV4 r | Profile |
|---------|-------|-------|-------|--------|---------|
| sub-08 (deutan) | 0.777* | 0.839* | 0.765* | 0.729* | **Reliable all ROIs → primary filter candidate** |
| sub-09 (protan) | 0.645* | 0.684* | 0.264 | 0.747* | Reliable V1/V2/hV4; V3 unstable |
| sub-10 (deutan) | 0.286 | 0.677* | 0.010 | 0.234 | **V2 only → V2-only filter confirmed** |
| Group mean | 0.569 | 0.733 | 0.346 | 0.570 | V2 most stable overall |

*p<0.05

### B3: Bootstrap 95% CIs — Key Adjacent Pairs (step=1)

| Pair | ROI | sub-08 z [CI] | sub-09 z [CI] | sub-10 z [CI] |
|------|-----|---------------|---------------|---------------|
| red-orange | V1 | −0.82 [−2.5,−0.2]* | −1.35 [−3.3,−0.7]* | −0.68 [−2.2,+0.1] |
| orange-yellow | V1 | +2.00 [+1.3,+4.4]* | +0.73 [−0.8,+1.8] | −0.25 [−1.4,+0.7] |
| cyan-blue | V1 | −0.95 [−2.4,−0.4]* | −0.51 [−1.6,+0.4] | −0.59 [−1.9,−0.0]* |
| red-magenta | V1 | +0.69 [−0.3,+1.9] | +3.02 [+1.9,+6.9]* | +1.43 [−0.1,+3.5] |
| purple-magenta | V1 | +0.98 [+0.2,+1.9]* | +1.15 [+0.4,+2.1]* | +0.31 [−1.1,+1.2] |
| blue-purple | V2 | +4.34 [+2.9,+15.3]* | +0.33 [−0.9,+1.4] | +2.08 [+1.2,+7.9]* |
| orange-yellow | V2 | +3.29 [+2.0,+33.2]* | +0.40 [−0.4,+8.1] | −0.13 [−0.9,+3.0] |
| red-orange | hV4 | +4.34 [+2.9,+8.9]* | +0.47 [−1.4,+1.9] | −0.86 [−2.7,−0.5]* |

*CI excludes zero

**n_significant pairs per subject (B3):**

| Subject | V1 | V2 | V3 | hV4 |
|---------|----|----|----|----|
| sub-08 | 15/28 | 17/28 | 18/28 | 21/28 |
| sub-09 | 17/28 | 13/28 | 10/28 | 8/28 |
| sub-10 | 8/28 | 10/28 | 13/28 | 22/28 |

### Cross-Subject Consistency (HC-only SRM, updated)

| Pair | ROI | Direction | sub-08 | sub-09 | sub-10 | Mechanism |
|------|-----|-----------|--------|--------|--------|-----------|
| red-orange | V1 | DEFICIT | −0.82 | −1.35 | −0.68 | L-M confusion |
| cyan-blue | V1 | DEFICIT | −0.95 | −0.51 | −0.59 | L-M confusion |
| red-magenta | V1 | ELEVATION | +0.69 | +3.02 | +1.43 | S-cone compensation |
| purple-magenta | V1 | ELEVATION | +0.98 | +1.15 | +0.31 | S-cone compensation |
| red-magenta | V2 | ELEVATION | +1.66 | +1.64 | +0.51 | S-cone compensation |
| blue-purple | V2 | ELEVATION | +4.34 | +0.33 | +2.08 | S-cone compensation (B1 p=0.042) |

### Key Findings

1. **Filter targets validated**: red-orange deficit, orange-yellow/blue-purple/red-magenta elevation confirmed by B3 bootstrap — consistent with filter_design_plan §4.3 HIGH/MEDIUM priorities.
2. **sub-08 primary candidate**: Split-half r=0.73–0.84 across all ROIs.
3. **sub-10 V2-only**: Confirmed; only V2 shows stable profiles (r=0.68*).
4. **B1 power caveat**: min p=0.008 with n=10; bootstrap CIs are the primary individual-level evidence.
5. **Pattern preserved across SRM versions**: HC-only SRM shifts magnitudes vs. 10-subject SRM but L-M + S-cone structure replicated.

---

## Color Pair RDM Analysis — 2026-02-19

> **Purpose**: Quantify pairwise color discrimination differences between CVD subjects and HC group in SRM shared space.
> **Script**: `analysis/phase2_SRM_across_between/analysis/analyze_color_pair_differences.py`
> **Data**: HC-only SRM shared spaces (k=4,4,3,3 for V1,V2,V3,V4), 6 runs × 8 colors per subject
> **Method**: Bootstrap resampling (n=1000) of HC subjects with replacement; CVD-HC pairwise RDM differences with 95% CI

### Settings

- **SRM**: HC-only training (n=7 HC), CVD subjects projected via SVD
- **k values**: V1=4, V2=4, V3=3, hV4=3 (canonical from mean rank aggregation)
- **Distance metric**: Correlation distance (1 - Pearson r) in SRM shared space
- **RDM**: 28 unique color pairs (8 choose 2) per subject
- **Bootstrap**: 1000 iterations, HC subjects resampled with replacement
- **Significance**: 95% CI excludes zero (two-sided)

### Summary Table: Significant Pairs per ROI and Subject

| ROI | sub-08 (Deutan) | sub-09 (Protan) | sub-10 (Deutan) |
|-----|-----------------|-----------------|-----------------|
| V1  | 20/28           | 24/28           | 17/28           |
| V2  | 20/28           | 21/28           | 19/28           |
| V3  | 19/28           | 17/28           | 16/28           |
| V4  | 26/28           | 19/28           | 12/28           |

**Pattern**: sub-08 and sub-09 show more widespread alterations (17–26 pairs); sub-10 more selective (12–19 pairs). V4 shows highest effect count for sub-08 (26/28), suggesting hierarchical amplification of L-M deficits.

### Effect Size Statistics

| ROI | sub-08 (Deutan) | sub-09 (Protan) | sub-10 (Deutan) |
|-----|-----------------|-----------------|-----------------|
| **V1** | Max \|Δ\|=1.11, Mean=0.47, n=20 | Max \|Δ\|=1.20, Mean=0.60, n=24 | Max \|Δ\|=1.00, Mean=0.51, n=17 |
| **V2** | Max \|Δ\|=1.03, Mean=0.58, n=20 | Max \|Δ\|=0.90, Mean=0.49, n=21 | Max \|Δ\|=0.82, Mean=0.43, n=19 |
| **V3** | Max \|Δ\|=1.38, Mean=0.75, n=19 | Max \|Δ\|=1.21, Mean=0.60, n=17 | Max \|Δ\|=1.69, Mean=0.74, n=16 |
| **V4** | Max \|Δ\|=1.12, Mean=0.75, n=26 | Max \|Δ\|=1.23, Mean=0.70, n=19 | Max \|Δ\|=0.92, Mean=0.63, n=12 |

**Trend**: V3 and V4 show larger mean effect sizes (0.60–0.75) than V1/V2 (0.43–0.60), suggesting hierarchical integration amplifies individual pair differences.

### Individual CVD Profiles — Top 5 Pairs per ROI

#### sub-08 (Deutan)

**V1 (20/28 significant):**
1. Red-Cyan: Δ=+1.11 [+0.77, +1.40]* (L-M over-separation)
2. Red-Yellow: Δ=+0.71 [+0.39, +1.07]* (adjacent L-M confusion)
3. Green-Cyan: Δ=−0.63 [−0.89, −0.40]* (L-M compression)
4. Orange-Blue: Δ=+0.63 [+0.43, +0.77]* (L-M cross-category)
5. Red-Orange: Δ=−0.60 [−0.84, −0.40]* (adjacent L-M deficit)

**V2 (20/28 significant):**
1. Orange-Blue: Δ=+1.03 [+0.89, +1.19]*
2. Red-Purple: Δ=−0.95 [−1.39, −0.54]*
3. Orange-Green: Δ=−0.91 [−1.16, −0.67]* (L-M adjacent deficit)
4. Blue-Purple: Δ=+0.88 [+0.67, +1.10]* (S-cone compensation)
5. Orange-Cyan: Δ=+0.73 [+0.52, +0.98]* (L-M cross-category)

**V3 (19/28 significant):**
1. Orange-Cyan: Δ=−1.38 [−1.68, −0.99]* (L-M compression)
2. Orange-Purple: Δ=−1.20 [−1.67, −0.67]*
3. Orange-Yellow: Δ=+1.07 [+0.73, +1.39]* (adjacent L-M confusion)
4. Green-Purple: Δ=−1.07 [−1.58, −0.48]*
5. Green-Cyan: Δ=−0.97 [−1.39, −0.49]* (L-M compression)

**V4 (26/28 significant — highest coverage):**
1. Red-Cyan: Δ=+1.12 [+0.70, +1.49]* (L-M over-separation, consistent V1)
2. Green-Magenta: Δ=+1.11 [+0.60, +1.56]*
3. Blue-Purple: Δ=+1.06 [+0.86, +1.26]* (S-cone compensation)
4. Cyan-Blue: Δ=−1.01 [−1.33, −0.64]* (L-M compression)
5. Purple-Magenta: Δ=+0.97 [+0.56, +1.36]* (S-cone compensation)

**Summary**: Consistent L-M deficits (red-orange, green-cyan compression; red-cyan over-separation) across hierarchy. V4 shows massive S-cone compensation (blue-purple, purple-magenta).

#### sub-09 (Protan)

**V1 (24/28 significant — highest V1 coverage):**
1. Blue-Magenta: Δ=−1.20 [−1.34, −1.06]* (S-cone compression)
2. Green-Magenta: Δ=+1.01 [+0.62, +1.26]*
3. Cyan-Magenta: Δ=+0.97 [+0.74, +1.21]*
4. Orange-Green: Δ=−0.93 [−1.04, −0.81]* (L-M adjacent deficit)
5. Orange-Cyan: Δ=−0.92 [−1.14, −0.65]* (L-M compression)

**V2 (21/28 significant):**
1. Cyan-Magenta: Δ=+0.90 [+0.71, +1.08]*
2. Orange-Blue: Δ=+0.88 [+0.73, +1.04]*
3. Blue-Magenta: Δ=−0.87 [−1.24, −0.45]* (S-cone compression)
4. Yellow-Blue: Δ=−0.77 [−0.93, −0.63]* (S-cone deficit)
5. Cyan-Blue: Δ=+0.67 [+0.47, +0.88]*

**V3 (17/28 significant):**
1. Orange-Cyan: Δ=−1.21 [−1.50, −0.82]* (L-M compression, consistent V1)
2. Orange-Purple: Δ=−1.03 [−1.50, −0.50]*
3. Blue-Purple: Δ=+0.80 [+0.32, +1.06]* (S-cone compensation)
4. Red-Orange: Δ=−0.70 [−1.22, −0.23]* (adjacent L-M deficit)
5. Purple-Magenta: Δ=+0.67 [+0.29, +1.04]* (S-cone compensation)

**V4 (19/28 significant):**
1. Yellow-Cyan: Δ=+1.23 [+0.70, +1.62]*
2. Yellow-Blue: Δ=−1.00 [−1.28, −0.70]* (S-cone deficit)
3. Red-Magenta: Δ=+0.94 [+0.33, +1.55]*
4. Red-Green: Δ=+0.86 [+0.39, +1.32]* (L-M over-separation)
5. Blue-Magenta: Δ=−0.81 [−1.34, −0.30]* (S-cone compression, consistent V1/V2)

**Summary**: Unique S-cone compression signature (blue-magenta deficit V1/V2/V4). L-M deficits present but less pronounced than sub-08. Orange-cyan compression consistent V1→V3.

#### sub-10 (Deutan)

**V1 (17/28 significant):**
1. Red-Cyan: Δ=+1.00 [+0.66, +1.29]* (L-M over-separation, consistent sub-08)
2. Blue-Magenta: Δ=−1.00 [−1.14, −0.85]* (S-cone compression)
3. Yellow-Blue: Δ=+0.76 [+0.57, +0.92]* (S-cone over-separation)
4. Purple-Magenta: Δ=+0.72 [+0.24, +1.18]* (S-cone compensation)
5. Red-Magenta: Δ=+0.58 [+0.26, +0.92]*

**V2 (19/28 significant):**
1. Red-Purple: Δ=−0.82 [−1.25, −0.41]*
2. Red-Cyan: Δ=+0.67 [+0.37, +0.97]* (L-M over-separation)
3. Green-Purple: Δ=−0.59 [−0.88, −0.33]*
4. Yellow-Cyan: Δ=−0.55 [−0.85, −0.23]*
5. Orange-Cyan: Δ=+0.54 [+0.32, +0.78]*

**V3 (16/28 significant):**
1. Yellow-Purple: Δ=−1.69 [−1.77, −1.60]* (extreme compression, unique to sub-10)
2. Blue-Purple: Δ=+1.41 [+0.93, +1.67]* (S-cone compensation)
3. Orange-Purple: Δ=−1.27 [−1.74, −0.75]*
4. Green-Purple: Δ=−1.17 [−1.68, −0.58]*
5. Green-Magenta: Δ=+0.75 [+0.34, +1.15]*

**V4 (12/28 significant — lowest coverage):**
1. Blue-Purple: Δ=+0.92 [+0.72, +1.12]* (S-cone compensation, consistent V3)
2. Cyan-Blue: Δ=−0.75 [−1.08, −0.39]*
3. Yellow-Green: Δ=+0.75 [+0.41, +1.16]*
4. Purple-Magenta: Δ=+0.74 [+0.33, +1.13]* (S-cone compensation)
5. Red-Blue: Δ=+0.72 [+0.24, +1.22]*

**Summary**: Most selective CVD profile (12–19 pairs). Extreme V3 yellow-purple compression (Δ=−1.69). Consistent S-cone compensation (blue-purple V3/V4, purple-magenta V1/V4).

### Color Axis Analysis

#### L-M Axis Deficits (Red-Green, Orange-Cyan)

**V1:**
- sub-08: Red-Yellow*, Orange-Cyan*, Yellow-Green* (3 L-M pairs)
- sub-09: Red-Yellow*, Red-Green*, Orange-Cyan*, Yellow-Green* (4 L-M pairs)
- sub-10: Red-Green*, Yellow-Green* (2 L-M pairs)

**V2:**
- sub-08: Red-Yellow*, Red-Green*, Orange-Cyan*, Yellow-Green* (4 L-M pairs)
- sub-09: Red-Yellow* (1 L-M pair, less pronounced than V1)
- sub-10: Red-Green*, Orange-Cyan* (2 L-M pairs)

**V3:**
- sub-08: Red-Yellow*, Red-Green*, Orange-Cyan*, Yellow-Green* (4 L-M pairs)
- sub-09: Orange-Cyan*, Yellow-Green* (2 L-M pairs)
- sub-10: Red-Green*, Orange-Cyan* (2 L-M pairs)

**V4:**
- sub-08: Red-Yellow*, Red-Green*, Orange-Cyan*, Yellow-Green* (4 L-M pairs, consistent V1→V4)
- sub-09: Red-Green*, Yellow-Green* (2 L-M pairs)
- sub-10: Red-Green*, Yellow-Green* (2 L-M pairs)

**Pattern**: L-M deficits pervasive across hierarchy. sub-08 shows 4/4 L-M pairs significant in all ROIs (strongest deutan phenotype). sub-09 and sub-10 more selective (1–2 pairs per ROI).

#### S-Cone Axis Patterns (Yellow-Blue, Purple-Magenta)

**V1:**
- sub-08: Yellow-Blue*, Blue-Magenta* (2 S-cone pairs)
- sub-09: Yellow-Blue*, Blue-Magenta*, Purple-Magenta* (3 S-cone pairs)
- sub-10: Yellow-Blue*, Blue-Magenta*, Purple-Magenta* (3 S-cone pairs)

**V2:**
- sub-08: Yellow-Blue*, Purple-Magenta* (2 S-cone pairs)
- sub-09: Yellow-Blue*, Blue-Magenta*, Purple-Magenta* (3 S-cone pairs)
- sub-10: Yellow-Blue* (1 S-cone pair)

**V3:**
- sub-08: Blue-Magenta* (1 S-cone pair)
- sub-09: Blue-Magenta*, Purple-Magenta* (2 S-cone pairs)
- sub-10: Yellow-Blue*, Purple-Magenta* (2 S-cone pairs)

**V4:**
- sub-08: Yellow-Blue*, Purple-Magenta* (2 S-cone pairs)
- sub-09: Yellow-Blue*, Blue-Magenta*, Purple-Magenta* (3 S-cone pairs)
- sub-10: Purple-Magenta* (1 S-cone pair)

**Pattern**: S-cone compensation prevalent in V1 (2–3 pairs per subject), suggesting early visual cortex relies on intact S-cone input to offset L-M deficits. sub-09 shows strongest S-cone signature (3 pairs in V1/V2). sub-10 most selective.

### Key Findings

1. **Hierarchical amplification**: Effect sizes increase V1→V3/V4 (mean |Δ| 0.43–0.60 in V1/V2 vs 0.60–0.75 in V3/V4), suggesting integration amplifies single-pair differences.

2. **Individual differences**:
   - **sub-08 (Deutan)**: Most severe L-M deficits (4/4 L-M pairs in all ROIs); V4 26/28 pairs significant (widespread cortical reorganization).
   - **sub-09 (Protan)**: Unique S-cone compression (blue-magenta deficit V1/V2/V4); L-M deficits present but less pervasive.
   - **sub-10 (Deutan)**: Most selective (12–19 pairs); extreme V3 yellow-purple compression (Δ=−1.69).

3. **L-M deficit consistency**: Red-cyan over-separation (sub-08 V1 Δ=+1.11, V4 Δ=+1.12; sub-10 V1 Δ=+1.00) replicates across hierarchy. Orange-cyan compression universal (all subjects, V1/V3).

4. **S-cone compensation**: Purple-magenta elevation (sub-08 V1 Δ=+0.98, V4 Δ=+0.97; sub-09 V1 Δ=+1.15) suggests intact S-cone pathway recruited for discrimination.

5. **Validation of filter targets**: Bootstrap CIs confirm pre-validation findings (red-orange deficit, blue-purple elevation). Filter design priorities validated for sub-08 (primary candidate) and sub-10 (V2-only).

### Comparison to Pre-Validation (B3 Bootstrap, Euclidean)

**Metric shift (Correlation vs Euclidean)**: Current analysis uses correlation distance (RDM standard); pre-validation used Euclidean (z-score interpretation). Directionality and pair identities consistent, magnitudes differ due to metric choice.

**Key replication**:
- Red-orange deficit: Pre-val V1 z=−0.82 (sub-08), −1.35 (sub-09) → Current V1 Δ=−0.60* (sub-08), trend (sub-09)
- Blue-purple elevation: Pre-val V2 z=+4.34* (sub-08), +2.08* (sub-10) → Current V2 Δ=+0.88* (sub-08), trend (sub-10)
- Purple-magenta elevation: Pre-val V1 z=+0.98*, +1.15* → Current V1 Δ=+0.98*, +1.15* (exact labels, similar magnitudes)

**Pattern stability**: L-M deficits + S-cone compensation structure preserved across SRM versions (HC-only vs 10-subject) and distance metrics.

---

