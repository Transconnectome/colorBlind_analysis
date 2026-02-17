# Methods & Results Summary for Paper

> Auto-generated and maintained by `capture-results` skill.
> Last updated: 2026-02-17 (noise ceiling N=40, SRM validation 1D/2A/2B completed)

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
- **SRM components (k)**: 4 [k-value selection validation pending]
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

### Permutation Validation (Approach 2: Pre-SRM Shuffling with Retraining, 1000 iterations)

**All ROIs:**

| ROI | Disparity p | Disparity interpretation | HC RDM p | CVD RDM p | RDM interpretation |
|-----|------------|-------------------------|----------|-----------|-------------------|
| V1 | 0.149 | Not significant | 0.192 | 0.599 | Not color-specific |
| **V2** | **0.953** | **Color-AGNOSTIC** | **0.010** | **0.006** | **Color-SPECIFIC** |
| V3 | 0.980 | Color-agnostic | 0.294 | 0.035 | CVD only |
| hV4 | 0.935 | Color-agnostic | 0.538 | 0.176 | Not color-specific |

> **"Scattered but Parallel" pattern in V2**:
> - **Scattered**: CVD-HC disparity is NOT color-specific (p = 0.953) — it reflects general signal differences
> - **Parallel**: Color relationship structure IS color-specific (HC p = 0.010, CVD p = 0.006) — both groups preserve genuine color representations
>
> This pattern is most clearly observed in V2. In V1, neither RDM metric reached significance (HC p = 0.192, CVD p = 0.599), suggesting that while V1 shows disparity differences, the color-specificity of representations is less clear. All ROIs show disparity reversal under permutation (p > 0.93 for V2–hV4), indicating the disparity is color-agnostic across the visual hierarchy.

### Validation Status (Phase 2)

- [x] SRM alignment: all 4 ROIs computed (k=4)
- [x] Between-subject disparity: HC-CVD comparison complete
- [x] Permutation test (Approach 1): basic shuffle
- [x] Permutation test (Approach 2): pre-SRM shuffle with retraining (1000 iter, all ROIs)
- [x] Brain surface visualization: voxel-level maps for sub-08
- [x] **1D Permutation test**: V1 p=0.014, V2 p=0.036 (10,000 iter); V3/hV4 n.s. — disparity difference > chance
- [x] **2A Run-split ICC**: Mean r=0.475 (moderate); sub-08 hV4 best (r=0.71); V1 weakest
- [x] **2B RDM consistency**: CVD ≥ HC in V1 (+0.200) and V2 (+0.123) — "parallel" pattern confirmed
- [ ] LOSO stability: 7-fold leave-one-subject-out (scripts ready, server) — validates that results are not driven by single subject
- [ ] Split-half reliability: run-split SRM stability (scripts ready, server)
- [ ] SRM k-value selection: component number optimization (scripts ready, server) — justifies k=4 choice
- [ ] Bootstrap 95% CIs for key comparisons (disparity, RDM correlations)

---

## Key Findings Summary

1. **C010 + Procrustes is the optimal pipeline**: +1644% improvement in RDM reliability (0.028 → 0.487); per-subject noise ceiling utilization ~30% (individual split-half metric), indicating substantial room for model improvement
2. **V1 and V2 show exploratory CVD-HC separation**: uncorrected p = 0.024 (V1), p = 0.025 (V2), Hedges' g > 1.8; did not survive Bonferroni correction for 4 ROIs
3. **hV4 is the strongest color-selective ROI** in baseline decoding (RDM r = 0.541)
4. **"Scattered but Parallel" pattern in V2**: CVD-HC disparity is color-agnostic (permutation p = 0.953), while color relationship structure is preserved and color-specific (HC RDM p = 0.010, CVD RDM p = 0.006); this pattern was less consistent in other ROIs
5. **CVD heterogeneity**: 3 CVD subjects show distinct individual profiles (sub-08: systematic elevation, sub-09: region-specific variability, sub-10: near-normal)
6. **Whitening is harmful**: degrades performance by 47–92% regardless of application order

---

## Limitations & Caveats

- **Small CVD sample (n=3)**: Group-level comparisons should be interpreted with caution. Individual CVD profiles are reported alongside group descriptive statistics. Effect sizes may be inflated due to small sample.
- **Multiple comparisons**: 4 ROIs tested; uncorrected p-values do not survive Bonferroni correction. Results framed as exploratory.
- **No parametric group tests with n=3**: Permutation-based p-values and Hedges' g (small-sample corrected) used instead of parametric t-tests, which would violate normality assumptions.
- **95% CIs not yet computed**: Bootstrap confidence intervals for key comparisons are pending.
- **CVD individual stability moderate**: Run-split ICC mean r=0.475 (moderate); sub-08 most stable, sub-09/sub-10 lower reliability in V1.
- **V3/hV4 non-significance**: May reflect genuine absence of difference or insufficient power with n=3 CVD.
- **V1 permutation**: Disparity is significant (p = 0.024) but RDM color-specificity is not (p = 0.192 / 0.599), complicating interpretation.
- **CVD subtype mixing**: 2 deutan (sub-08, sub-10) + 1 protan (sub-09), precluding subtype-specific analysis. Notably, sub-09 (protan) shows the highest V1 disparity (+91%), while the two deutan subjects differ markedly (sub-08: consistent elevation vs sub-10: near-normal).
- **SRM k-value**: k=4 used; optimization validation pending.
- ~~**sub-01 noise ceiling**~~: Resolved 2026-02-17 — re-run with N=40.

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
| **LOSO stability** | Phase 2 | Scripts ready | **High** | Verify no single-subject drives results (server) |
| **Split-half reliability** | Phase 2 | Scripts ready | **High** | Test run-split SRM stability (server) |
| **Bootstrap 95% CIs** | Phase 2 | Not started | **High** | Required for paper submission |
| RDM consistency (cross-val) | Phase 2 | Scripts ready | Medium | Cross-validate RDM patterns |
| SRM k-value selection | Phase 2 | Scripts ready | Medium | Justify k=4 choice |
