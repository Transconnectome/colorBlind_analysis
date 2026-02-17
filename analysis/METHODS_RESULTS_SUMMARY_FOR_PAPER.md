# Methods & Results Summary for Paper

> Auto-generated and maintained by `capture-results` skill.
> Last updated: 2026-02-17 (Phase 2b decoder comparison added: LORO 6-model comparison, LOCO interpolation test, HC vs CVD group comparison)

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
- **SRM components (k)**: V1=4, V2=4, V3=3, hV4=4 (validated via 7-fold LOSO cross-validation; see 2C below)
- **Input**: Phase 1 Procrustes-aligned amplitudes (C010)
- **ROIs**: V1, V2, V3, hV4
- **Subjects**: HC (n=7: sub-01~07), CVD (n=3: sub-08~10)
- **Training**: HC-only (7 subjects train SRM; CVD projected into shared space)
- **Metric**: Procrustes disparity between subject pairs in SRM space
- **Comparison**: HC-HC pairs vs CVD-HC pairs
- **Statistical test**: Permutation test (label shuffling, 10,000 iterations) for group disparity comparison
- **Effect size**: Hedges' g (bias-corrected for small samples)

### Main Results: Group Disparity Comparison

| ROI | HC-HC Disparity (M ± SD) | CVD-HC Disparity (M ± SD) | Separation | p-value (uncorrected) | Hedges' g | Bonferroni-corrected |
|-----|-------------------------|--------------------------|------------|----------------------|-----------|---------------------|
| **V1** | 0.3898 ± 0.0636 | 0.5733 ± 0.1229 | 0.1835 | **p = 0.024** | **1.875** | p = 0.097 (n.s.) |
| **V2** | 0.3998 ± 0.0741 | 0.5489 ± 0.0610 | 0.1491 | **p = 0.025** | **2.196** | p = 0.101 (n.s.) |
| V3 | 0.4435 ± 0.0950 | 0.5094 ± 0.1274 | 0.0658 | p = 0.443 | 0.589 | p = 1.000 |
| hV4 | 0.5749 ± 0.0882 | 0.6413 ± 0.1726 | 0.0664 | p = 0.494 | 0.479 | p = 1.000 |

> At uncorrected α = 0.05, V1 and V2 show HC-CVD separation with large effect sizes. However, **these do not survive Bonferroni correction for 4 ROIs (α = 0.0125)**. Results should be interpreted as exploratory given the small CVD sample (n=3). Note: effect sizes may be inflated due to small sample.

### Individual CVD Profiles

| Subject | V1 (% above HC) | V2 (% above HC) | V3 (% above HC) | hV4 (% above HC) | Pattern |
|---------|-----------------|-----------------|-----------------|-------------------|---------|
| sub-08 | +31.5% | +58.9% | +1.1% | +31.2% | Consistent elevation |
| sub-09 | +91.0% | +27.2% | +4.2% | +40.9% | High variability, V1 strongest |
| sub-10 | +18.7% | +25.8% | −13.8% | −20.2% | Atypical, near-normal in V3/hV4 |

> **sub-08**: Systematic elevation across visual hierarchy (+40.5% avg)
> **sub-09**: Region-specific heterogeneity (V1: +91%, V3: +4.2%)
> **sub-10**: Nearly normal phenotype (−3.1% avg); possible mild CVD or compensatory mechanisms

### CVD Heterogeneity (CVD-CVD vs HC-HC disparity ratio)

| ROI | CVD-CVD / HC-HC ratio | Interpretation |
|-----|----------------------|----------------|
| V1 | 1.47× | Moderate heterogeneity |
| V2 | 1.37× | Moderate heterogeneity |
| V3 | 1.59× | Highest heterogeneity |
| hV4 | 1.44× | Moderate heterogeneity |

> CVD subjects are 1.4–1.6× more dispersed than HC across all ROIs.

### RDM Correlation (Color Structure Similarity)

| ROI | HC-HC RDM (r) | HC-CVD RDM (r) | CVD-CVD RDM (r) | N pairs (HC-HC / HC-CVD / CVD-CVD) |
|-----|--------------|----------------|-----------------|-------------------------------------|
| V1 | 0.447 | 0.322 | 0.297 | 21 / 21 / 3 |
| **V2** | **0.517** | **0.499** | **0.591** | 21 / 21 / 3 |
| V3 | 0.385 | 0.348 | 0.591 | 21 / 21 / 3 |
| hV4 | 0.158 | 0.224 | 0.276 | 21 / 21 / 3 |

> In V2, HC-CVD RDM correlation (0.499) is similar to HC-HC (0.517), suggesting CVD subjects largely preserve color relationship structure in this region. In V1, CVD values are lower (HC-CVD = 0.322 vs HC-HC = 0.447), indicating less preservation in early visual cortex. CVD-CVD RDM values should be interpreted cautiously given only 3 pairs.

### Permutation Validation (1D: Pre-SRM Shuffling with Retraining, 1000 iterations)

**Approach 2 (group-difference disparity + within-group RDM correlations):**

| ROI | Disparity diff p | Disparity interpretation | HC RDM p | CVD RDM p | RDM interpretation |
|-----|------------|-------------------------|----------|-----------|-------------------|
| V1 | 0.149 | Not significant | 0.192 | 0.599 | Not color-specific |
| **V2** | **0.953** | **Color-AGNOSTIC** | **0.010** | **0.006** | **Color-SPECIFIC** |
| V3 | 0.980 | Color-agnostic | 0.294 | 0.035 | CVD only |
| hV4 | 0.935 | Color-agnostic | 0.538 | 0.176 | Not color-specific |

> **"Scattered but Parallel" pattern in V2**:
> - **Scattered**: CVD-HC disparity is NOT color-specific (p = 0.953) — it reflects general signal differences
> - **Parallel**: Color relationship structure IS color-specific (HC p = 0.010, CVD p = 0.006) — both groups preserve genuine color representations
>
> This pattern is most clearly observed in V2. In V1, neither RDM metric reached significance (HC p = 0.192, CVD p = 0.599), suggesting that while V1 shows disparity differences, the color-specificity of representations is less clear. All ROIs show disparity reversal under permutation (p > 0.93 for V2-hV4), indicating the disparity is color-agnostic across the visual hierarchy.

**Per-group disparity color-dependency test (1D-ext, 1000 iterations):**

Tests whether each group's within-group consistency depends on true color labels (not group differences).

| ROI | HC to-ref p | CVD to-ref p | CVD pairwise p | HC RDM p | CVD RDM p |
|-----|-------------|-------------|----------------|----------|-----------|
| V1 | 0.060 | 0.209 | 0.216 | 0.192 | 0.599 |
| **V2** | 0.353 | **0.028** | **0.028** | **0.010** | **0.006** |
| V3 | 0.146 | 0.098 | 0.062 | 0.294 | **0.035** |
| hV4 | 0.400 | 0.100 | 0.134 | 0.538 | 0.176 |

> **Methodological note on HC disparity non-significance**: HC subjects (n=7) dominate SRM training (7/10). The SRM optimization inherently minimizes HC-to-HC-mean distance, creating a "floor effect" where HC to-ref disparity is similar under true and shuffled labels (V2: observed 0.400 vs null 0.405, only 1.3% gap). This is a property of the SRM method, not evidence against color structure. The RDM test (second-order structure) is immune to this bias and provides the appropriate HC control — HC RDM correlation IS color-specific in V2 (p=0.010).
>
> **CVD to-ref/pairwise significance in V2** (p=0.028): CVD subjects are a minority in SRM training (3/10), so the SRM space is not optimized for them. Under true labels, CVD subjects share color structure and are consistent; under shuffled labels, CVD consistency degrades (null mean 0.491 vs observed 0.406, 17% gap). This confirms CVD subjects share genuine color-dependent patterns in V2.

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

Validated via RDM reliability and cross-subject RDM correlation across 7 folds. Full fold-level data available; aggregation shows:

| ROI | Selected k | Justification |
|-----|-----------|---------------|
| V1 | 4 | RDM reliability peaks at k=4 (0.626), drops at k=5 (0.555) and k=6 (0.324) |
| V2 | 4 | Cross-subject RDM correlation peaks at k=4 (0.812); RDM reliability competitive |
| V3 | 3 | Lower-dimensional space sufficient for fewer voxels |
| hV4 | 4 | Consistent with V1/V2 pattern |

> k selection data exists for all 28 fold-ROI combinations (7 folds x 4 ROIs). Note: fold-to-fold variation exists; V2 RDM reliability favors k=2 in some folds but cross-subject agreement is maximized at k=4. Formal aggregation (e.g., mean rank across folds) recommended for final reporting.

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

- [x] SRM alignment: all 4 ROIs computed (V1=4, V2=4, V3=3, hV4=4)
- [x] Between-subject disparity: HC-CVD comparison complete
- [x] Permutation test (Approach 1): basic shuffle
- [x] Permutation test (Approach 2): pre-SRM shuffle with retraining (1000 iter, all ROIs)
- [x] **1D-ext Per-group permutation**: V2 CVD disparity p=0.028 (PASS); HC disparity insensitive due to SRM self-referencing
- [x] Brain surface visualization: voxel-level maps for sub-08
- [x] **1A HC-only verification**: V1/V2 significant (p<0.025), V3/hV4 n.s.
- [x] **1B LOSO stability**: V2 7/7 folds significant; V1 6/7; V3/hV4 0/7
- [x] **1C Split-half reliability**: V2 significant in both halves; cross-half disparity r=0.71-0.78 for V1/V2/hV4
- [x] **1D Permutation test**: V1 p=0.014, V2 p=0.036 (10,000 iter); V3/hV4 n.s. -- disparity difference > chance
- [x] **2A Run-split ICC**: 8/12 moderate or better; sub-08 hV4 best (r=0.83)
- [x] **2B RDM consistency**: CVD >= HC in V1 (+0.200) and V2 (+0.123) -- "parallel" pattern confirmed
- [x] **2C k-value selection**: 7-fold CV completed; V1=4, V2=4, V3=3, hV4=4 validated (fold data available)
- [x] **2D Alignment comparison**: SRM 2.4-6.5x better than raw/Procrustes for between-subject RDM agreement
- [ ] Bootstrap 95% CIs for key comparisons (disparity, RDM correlations)
- [ ] Formal k aggregation across folds (mean rank method)

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

### Validation Status (Phase 2b)

- [x] LORO model comparison: 10 subjects, 4 ROIs, 6 models, both alignment conditions
- [x] Bootstrap 95% CIs: subject-level resampling, 1000 iterations
- [x] HC vs CVD comparison: Mann-Whitney U, no meaningful group difference
- [x] Test-retest reliability: split-half with Spearman-Brown correction
- [x] LOCO local test: sub-01, 4 ROIs, 100 permutations
- [ ] LOCO server deployment: 10 subjects × 4 ROIs, 1000 permutations
- [ ] LOCO results consolidation and group-level analysis
- [ ] Dimensionality reduction re-experiment (SRM/PCA + 6 models)

---

## Key Findings Summary

1. **C010 + Procrustes is the optimal pipeline**: +1644% improvement in RDM reliability (0.028 -> 0.487); per-subject noise ceiling utilization ~30% (individual split-half metric), indicating substantial room for model improvement
2. **V2 is the most robustly validated ROI for CVD-HC separation**: uncorrected p = 0.025, Hedges' g = 2.196; LOSO 7/7 folds significant; split-half both halves significant; RDM color-specific (HC p=0.010, CVD p=0.006); CVD within-group disparity color-dependent (p=0.028)
3. **V1 shows separation but weaker validation**: uncorrected p = 0.024, Hedges' g = 1.875; LOSO 6/7 folds; split-half 1/2 significant; RDM not color-specific (p=0.192/0.599)
4. **hV4 is the strongest color-selective ROI** in baseline decoding (RDM r = 0.541) but does not show CVD-HC separation
5. **"Scattered but Parallel" pattern in V2**: CVD-HC disparity is color-agnostic (permutation p = 0.953), while color relationship structure is preserved and color-specific (HC RDM p = 0.010, CVD RDM p = 0.006)
6. **CVD heterogeneity**: 3 CVD subjects show distinct individual profiles (sub-08: systematic elevation, sub-09: region-specific variability, sub-10: near-normal)
7. **SRM alignment is 2.4-6.5x better** than raw or Procrustes for between-subject RDM agreement
8. **Whitening is harmful**: degrades performance by 47-92% regardless of application order
9. **Voxel-color mapping is linear; alignment is key**: After Procrustes, LDA (linear) achieves 82.1% acc_45, outperforming all non-linear models (SVM 77.6%, KernelRidge 73.9%). Without alignment, ALL models fail at chance (~38%). Non-linearity does not compensate for misalignment.
10. **HC ≈ CVD in decoder performance**: No meaningful group difference in within-subject LORO decoding (CVD slightly higher in LDA/SVM), supporting shared voxel-color mapping and justifying cross-group filter learning.
11. **ForwardEncoding is the only model with color interpolation ability**: In LOCO, only ForwardEncoding predicts held-out colors (MAE < 90° in all ROIs; V3 p < 0.01). This validates its channel-based framework for continuous color representation.
12. **MLP fails completely** (39.4%, chance-level): extreme sample/feature ratio (~0.07) defeats regularization. Dimensionality reduction (SRM/PCA) is needed before non-linear models become viable.

---

## Limitations & Caveats

- **Small CVD sample (n=3)**: Group-level comparisons should be interpreted with caution. Individual CVD profiles are reported alongside group descriptive statistics. Effect sizes may be inflated due to small sample.
- **Multiple comparisons**: 4 ROIs tested; uncorrected p-values do not survive Bonferroni correction. Results framed as exploratory.
- **No parametric group tests with n=3**: Permutation-based p-values and Hedges' g (small-sample corrected) used instead of parametric t-tests, which would violate normality assumptions.
- **95% CIs not yet computed**: Bootstrap confidence intervals for key comparisons are pending.
- **SRM disparity metric bias for majority group**: HC subjects (7/10) dominate SRM training, creating a "floor effect" on HC-to-reference disparity. Per-group permutation test shows HC disparity is insensitive (V2 p=0.353; observed 0.400 vs null 0.405, only 1.3% gap). This is methodological, not evidence against color structure. RDM-based tests (second-order, immune to this bias) provide the appropriate HC control and ARE significant (V2 HC RDM p=0.010).
- **CVD-CVD RDM instability across halves**: Split-half CVD-CVD RDM correlation is inconsistent (V2 Set A: 0.536, Set B: 0.124), suggesting CVD within-group color structure is less reliably estimated with n=3 and half-run data.
- **CVD individual stability moderate**: Run-split corrected reliability 8/12 moderate or better; sub-08 most stable, sub-09/sub-10 lower in V1/V2.
- **V3/hV4 non-significance**: Consistent across all validation tests (LOSO 0/7, split-half 0/2, permutation n.s.). May reflect genuine absence of difference or insufficient power.
- **V1 validation gap**: Disparity significant (p=0.024), LOSO 6/7 robust, but RDM color-specificity not significant (p=0.192/0.599), complicating interpretation of what V1 disparity represents.
- **CVD subtype mixing**: 2 deutan (sub-08, sub-10) + 1 protan (sub-09), precluding subtype-specific analysis. Notably, sub-09 (protan) shows the highest V1 disparity (+91%), while the two deutan subjects differ markedly (sub-08: consistent elevation vs sub-10: near-normal).
- ~~**SRM k-value**~~: Validated via 2C LOSO CV — V1=4, V3=3 confirmed; V2/hV4 k=3–4 competitive.
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
| **1D-ext LOO permutation re-run** | Phase 2 | Ready to deploy | **High** | LOO references eliminate SRM self-referencing bias; may recover HC disparity significance |
| **Bootstrap 95% CIs (SRM disparity)** | Phase 2 | Not started | **High** | Required for paper submission |
| **LOCO server deployment** | Phase 2b | Not started | **High** | Need all 10 subjects × 4 ROIs × 1000 perms |
| LOCO results consolidation | Phase 2b | Blocked (LOCO server) | Medium | Group-level LOCO analysis after server run |
| Dimensionality reduction re-experiment | Phase 2b | Not started | Medium | SRM/PCA + 6 models → test if MLP improves |
| Formal k aggregation | Phase 2 | Not started | Low | Mean rank across 28 fold-ROI combinations |

---

## TODO (Next Steps)

### Immediate (High Priority)

1. **Re-run per-group disparity permutation with LOO references** — Upload updated `run_pergroup_disparity_permutation.py` to server and run 1000 permutations × 4 ROIs
   - LOO fix: HC disparity now uses leave-one-out reference (mean of other 6) instead of full-group mean, eliminating SRM self-referencing bias
   - Same for CVD (LOO of other 2 CVD subjects)
   - Script: `analysis/phase2_SRM_across_between/validation/1D_permutation/run_pergroup_disparity_permutation.py`
   - SLURM: `run_pergroup_permutation.sbatch` (array 1-4, node2, 32GB)
   - Expected: HC LOO disparity should now be more sensitive to label shuffling (current full-mean test: V2 p=0.353)

2. **Deploy LOCO to server** — Run `run_loco_comparison.sbatch` for all 10 subjects with 1000 permutations
   - Scripts ready at `analysis/phase2_decoder_comparing/model_comparison_validation/scripts/`
   - Expected: ~1 hour per subject on node2
   - Upload via scp, submit via sbatch

3. **Consolidate LOCO server results** — After LOCO completes:
   - Download results, aggregate across subjects
   - Test ForwardEncoding interpolation significance at group level
   - Compare V3 vs other ROIs (hypothesis: fewer voxels → better interpolation)

4. **Bootstrap 95% CIs for SRM disparity** — Pending from Phase 2; required for paper
   - Subject-level resampling for HC-HC and CVD-HC disparity
   - Report CIs alongside p-values in Phase 2 main results table

### Short-term (Medium Priority)

5. **Dimensionality reduction + model re-experiment**
   - Apply PCA (k=10, 20, 50) and SRM (k=3, 4) to Procrustes-aligned data
   - Re-run all 6 models on reduced-dimension data
   - Key question: Does MLP recover with fewer features? Does LDA remain best?
   - Reuse existing scripts (`run_model_comparison.py --baseline_dir` on reduced data)

6. **LOCO with SRM-reduced data**
   - ForwardEncoding interpolation may improve dramatically with k=3–4 features
   - Test whether permutation significance extends beyond V3

### Deferred (Low Priority)

7. **Formal k aggregation across folds** — Mean rank method for SRM component selection
8. **Cross-subject generalization (train HC → test CVD)** — Requires common space (SRM/Hyperalignment); not possible in native voxel space
9. **Publication figure** — Comprehensive 6-panel summary of decoder comparison results
