# Phase 1: Preprocessing & Baseline Decoding (C010 + Procrustes)

## Table of Contents
- [Settings](#settings)
- [Overall Performance (N=40 subject-ROI pairs, 10 subjects × 4 ROIs)](#overall-performance-n40-subject-roi-pairs-10-subjects--4-rois)
- [Results by ROI](#results-by-roi)
- [Results by Group](#results-by-group)
- [Noise Ceiling Analysis (N=40 pairs, 10 subjects × 4 ROIs)](#noise-ceiling-analysis-n40-pairs-10-subjects--4-rois)
- [Pipeline Comparison (Whitening Assessment, N=40)](#pipeline-comparison-whitening-assessment-n40)
- [Validation Status (Phase 1)](#validation-status-phase-1)

---

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
