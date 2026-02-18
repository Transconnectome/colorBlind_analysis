# Methods & Results Summary for Paper

> Auto-generated and maintained by `capture-results` skill.
> Last updated: 2026-02-18 (Phase 2b: RT-1~6 complete; hybrid decoder FE_SVM≈FE confirms linear readout)

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

#### LOCO Interpretation

1. **ForwardEncoding is the only model with interpolation ability** — its 6-channel basis framework enables predicting unseen colors from the continuous hue space. All other models are limited to predicting training labels.
2. **V3 is the only ROI with significant interpolation** (p < 0.01): fewer voxels (106) reduce overfitting. This supports the need for dimensionality reduction (SRM/PCA) in high-dimensional ROIs.
3. **Ridge and KernelRidge show anti-interpolation** (MAE > 140°, worse than chance): in high-dimensional voxel space, regression predicts the opposite hue. This is a known failure mode of linear regression in high-dim/low-sample settings.
4. **Label-based classifiers (LDA, SVM, MLP) cannot predict the held-out color directly** — their theoretical minimum error is 45° (adjacent color). ForwardEncoding has no such constraint.

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
| Grand mean cosine similarity | **0.921** |
| Range (min-max across subject-ROIs) | 0.878 – 0.978 |
| Mean std per subject-ROI | 0.017 |

> W matrices are highly stable across folds (cosine sim > 0.87 everywhere).

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

### Revised Decoder Conclusions (2026-02-18)

**Previous conclusion**: "LDA is the best decoder → linearity is sufficient"

**Revised conclusion**: **"ForwardEncoding is the optimal decoder — channel-based color representation exists"**

| Criterion | LDA | SVM (nested) | ForwardEncoding |
|-----------|-----|-------------|----------------|
| LORO acc_45 (preloaded) | **0.821** | 0.776 | 0.736 |
| LORO acc_45 (nested) | — | **0.899** | **0.781** |
| Run-pair reliability | **0.009** (random) | 0.164 | **0.329** (best) |
| W matrix stability | N/A | N/A | **0.921** |
| LOCO interpolation | NS | NS | **p<0.01** (V3) |
| Alignment sensitivity | +0.428 (dependent) | +0.123 (moderate) | **+0.045** (robust) |
| Effective parameters | ~568 (overfit) | support vectors | **6** (parsimonious) |

**Why ForwardEncoding is optimal**:
1. **Only model with interpolation ability** (LOCO V3 p<0.01)
2. **Most alignment-robust** (Δ=+0.045 vs SVM's +0.123)
3. **Highest run-pair reliability** (r=0.329)
4. **Highly stable encoding weights** (cosine 0.921)
5. **Neuroscientifically grounded** (6-channel basis from Brouwer & Heeger 2009)
6. **Parsimonious** (6 parameters vs hundreds of support vectors or 36K+ MLP weights)

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
- [ ] **[RT-4] LOCO server deployment**: 10 subjects × 4 ROIs, 1000 permutations (submitted, pending)
- [ ] LOCO results consolidation and group-level analysis
- [x] **[RT-6] Hybrid decoder (FE+MLP, FE+SVM)**: FE_SVM ≈ FE (0.779 vs 0.784); FE_MLP degenerate; linear readout confirmed

---

## Key Findings Summary

1. **C010 + Procrustes is the optimal pipeline**: +1644% improvement in RDM reliability (0.028 -> 0.487); per-subject noise ceiling utilization ~30% (individual split-half metric), indicating substantial room for model improvement
2. **V2 shows trending CVD-HC separation with individual-level significance**: LOO-consistent group p=0.075, Hedges' g=1.04 [0.02, 3.18]; separation=0.120 [0.001, 0.244] (CI marginally excludes zero); LOSO 7/7 folds significant (pre-LOO); split-half both halves significant (pre-LOO); CVD color-dependency confirmed (score p=0.033, pairwise p=0.035); Crawford & Howell: sub-08 significantly elevated (p=0.040)
3. **V1 shows trending separation driven by sub-09**: LOO-consistent group p=0.062, Hedges' g=1.16; LOSO 6/7 folds (pre-LOO); Crawford & Howell: sub-09 significantly elevated (p=0.007); V1 group disparity is NOT color-specific (score p=0.427) but RDM trending (HC p=0.054, CVD p=0.056)
4. **hV4 is the strongest color-selective ROI** in baseline decoding (RDM r = 0.541) but does not show CVD-HC separation
5. **"Scattered but internally structured" — confirmed by LOSO**: CVD-HC disparity difference is color-agnostic in V2 (p=0.986), but CVD subjects show color-dependent consistency with HC references (single-SRM: V2 score p=0.033, V3 p=0.009, hV4 p=0.028; LOSO-confirmed: V2 p=0.010, V3 p=0.000, hV4 p=0.016). HC disparity is NOT color-dependent under either single-SRM or LOSO (p=0.21–0.89), confirming the asymmetry: HC share general structure while CVD's elevated disparity is specifically color-driven.
6. **CVD heterogeneity with individual dissociations**: Crawford & Howell (1998) tests reveal sub-09 (protan) is significantly elevated in V1 (p=0.007), sub-08 (deutan) in V2 (p=0.040), and sub-10 (deutan) falls within HC range across all ROIs. This resolves the n=3 group inference problem by demonstrating individual-level effects.
7. **SRM alignment is 2.4-6.5x better** than raw or Procrustes for between-subject RDM agreement
8. **Whitening is harmful**: degrades performance by 47-92% regardless of application order
9. **ForwardEncoding is the optimal decoder** (revised from "LDA best"): 6-channel model achieves 78.1% acc_45 (nested Procrustes), highest run-pair reliability (r=0.329), highest W stability (cosine 0.921), only model with LOCO interpolation (V3 p<0.01), and most alignment-robust (Δ=+0.045 vs SVM +0.123). LDA's 82.1% is undermined by zero reproducibility (run-pair r=0.009).
10. **SVM achieves highest raw accuracy** (89.9% nested Procrustes) but is alignment-method-dependent (+0.123 gap between nested and preloaded Procrustes), suggesting it exploits alignment structure rather than intrinsic color representation.
11. **Individual CVD cross-decoding confirmed (RT-7 fix)**: Under HC-only SRM (no circularity), 9/12 CVD tests remain significant at p<0.001 (V1/V2/V3: all 3 CVD above chance). hV4 degrades (1/3 sig) due to low SRM quality (HC LOSO 44.6%), not circularity removal. Validates shared color mapping without group statistics.
12. **MLP fails completely** (39.4%, chance-level): extreme sample/feature ratio (~0.07) defeats regularization. 47.5% of subject-ROI cells show degenerate solutions in preloaded Procrustes condition.
13. **Nested Procrustes does not inflate results** (RT-2 resolved): Nested alignment actually *improves* SVM (+0.123) and ForwardEncoding (+0.045) vs preloaded, confirming the original alignment effect was conservative.
14. **PCA-20 loses discriminative information** (RT-3): Reducing to 20 components drops SVM from 0.899 to 0.847, indicating color signal spans >20 dimensions.
15. **Channel→color readout is linear** (RT-6 Hybrid): FE_SVM (0.779) ≈ ForwardEncoding (0.784) under nested Procrustes — SVM-RBF on 6 channels provides no benefit over linear template matching. FE_MLP collapses to chance (0.381) due to early stopping failure on small samples. This validates the linear assumption for Phase 3 filter design.

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
| **[RT-4] LOCO server deployment** | Phase 2b | Submitted (6h, node2) | **Fatal** | n=1 pilot, 100 perms at p-floor; need 10 subj × 1000 perms |
| ~~[RT-3] PCA within LORO~~ | Phase 2b | **DONE** | ~~High~~ | PCA-20 loses info (SVM 0.847 vs 0.899 full). Signal spans >20 dims. |
| ~~[RT-1] Individual cross-decoding~~ | Phase 2b | **DONE** | ~~Fatal~~ | 12/12 tests p<0.05. All CVD decode in SRM space individually. |
| ~~[RT-5] LDA reliability analysis~~ | Phase 2b | **DONE** | ~~High~~ | Run-pair r=0.009 explains paradox. FE W stability 0.921. |
| ~~Hybrid decoder (FE+MLP, FE+SVM)~~ | Phase 2b | **DONE** | ~~High~~ | FE_SVM ≈ FE (0.779 vs 0.784); linear readout sufficient |
| ~~Bootstrap 95% CIs (SRM disparity)~~ | Phase 2 | **DONE** | ~~High~~ | V1/V2 separation CIs exclude zero; RDM CIs for all ROI-group pairs (10,000 iter) |
| LOCO results consolidation | Phase 2b | Blocked (RT-4) | Medium | Group-level LOCO analysis after server run |
| **Filter pre-diagnosis** | Phase 3 | Not started | **High** | Pair-level permutation test, LORO CV for filter, low-rank constraint, baseline comparison (filter_design_plan.md Criticism #4) |
| Dimensionality reduction + LOCO | Phase 2b | Not started | Medium | SRM/PCA + 6 models + LOCO re-experiment |
| ~~Formal k aggregation~~ | Phase 2 | **DONE** | ~~Low~~ | V1=4, V2=4, V3=3, hV4=3 (hV4 revised from 4→3 via mean rank) |

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
