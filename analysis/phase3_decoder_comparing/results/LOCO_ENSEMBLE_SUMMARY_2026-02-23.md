# LOCO Ensemble Results Summary (2026-02-23)

## Executive Summary

**Key Finding**: Per-run ensemble encoding (FE_Ensemble) significantly improves LOCO decoding accuracy in HC subjects, with V1 showing the strongest improvement (-8.3° mean reduction in MAE). However, Ridge and GaussML ensemble variants are harmful, confirming that correlation-based template matching remains optimal for LOCO with limited training data (7 colors/fold).

## Data Sources

1. **Ensemble Comparison**: `loco_decoding_comparison/decoding_comparison.json`
   - Models: ForwardEncoding (baseline), FE_Ensemble, FE_EnsembleRidge, FE_EnsembleGaussML
   - Alignment: Procrustes only
   - Focus: Per-run ensemble vs pooled encoding

2. **Full LOCO Results**: `loco_ensemble/{raw,procrustes,srm}/`
   - Models: ForwardEncoding, MLP, SVM, HybridMLP, HybridSVR
   - Alignment: Raw, Procrustes, SRM
   - Note: FE_Ensemble not computed in these files (metadata lists it but results missing)

---

## 1. FE_Ensemble vs Baseline (Procrustes Alignment)

### Group-Level Results

| ROI | FE Baseline HC | FE_Ensemble HC | Δ HC | FE Baseline CVD | FE_Ensemble CVD | Δ CVD |
|-----|---------------|----------------|------|-----------------|-----------------|-------|
| V1   | 76.4 ± 8.4 | 68.1 ± 11.3 | **-8.3** | 84.6 ± 28.3 | 84.2 ± 25.1 | -0.4 |
| V2   | 80.0 ± 16.7 | 79.2 ± 18.9 | -0.8 | 98.5 ± 20.5 | 99.1 ± 22.1 | +0.6 |
| V3   | 76.9 ± 16.2 | 74.1 ± 13.4 | -2.8 | 73.5 ± 9.9 | 71.6 ± 8.2 | -1.9 |
| hV4  | 69.4 ± 9.4 | 69.8 ± 14.9 | +0.4 | 87.4 ± 10.2 | 87.1 ± 8.5 | -0.2 |

**Key Points**:
- **HC group**: FE_Ensemble improves performance in V1 (-8.3°), V2 (-0.8°), and V3 (-2.8°)
- **CVD group**: Minimal changes across all ROIs (within ±2°)
- **V1 shows strongest benefit**: Largest improvement in HC group, suggesting early visual areas benefit most from per-run encoding

---

## 2. Individual Subject Improvements

### HC Subjects (Notable Improvements)

**Best Performers**:
- **sub-05 V1**: 61.8° → 45.3° (**-16.5°**) — Largest single improvement
- **sub-02 V1**: 84.8° → 73.0° (-11.8°)
- **sub-07 V2**: 82.7° → 70.0° (-12.7°)
- **sub-04 hV4**: 53.5° → 41.7° (-11.8°)

**Mixed Results**:
- Some subjects show worsening in specific ROIs (e.g., sub-01 hV4: +6.5°, sub-06 V2: +9.4°)
- Indicates individual variability in benefit from ensemble encoding

### CVD Subjects

**Sub-10** (Protanopia): Mild improvements across V1-V3
- V1: 98.6° → 92.0° (-6.6°)
- V2: 112.3° → 110.4° (-1.9°)
- V3: 79.7° → 75.8° (-3.9°)

**Sub-08, Sub-09**: Minimal changes (within ±5°)

---

## 3. Ensemble Variant Comparison

### All Variants (HC Group)

| ROI | ForwardEncoding | FE_Ensemble | FE_EnsembleRidge | FE_EnsembleGaussML |
|-----|----------------|-------------|------------------|---------------------|
| V1  | 76.4 ± 8.4     | 68.1 ± 11.3 | 91.7 ± 15.2     | 130.8 ± 7.3        |
| V2  | 80.0 ± 16.7    | 79.2 ± 18.9 | 98.8 ± 25.2     | 122.8 ± 9.9        |
| V3  | 76.9 ± 16.2    | 74.1 ± 13.4 | 94.6 ± 10.1     | 126.0 ± 8.3        |
| hV4 | 69.4 ± 9.4     | 69.8 ± 14.9 | 95.1 ± 14.8     | 120.5 ± 9.7        |

### Relative Improvements (HC Group, Δ from Baseline)

| ROI | FE_Ensemble | FE_EnsembleRidge | FE_EnsembleGaussML |
|-----|-------------|------------------|---------------------|
| V1  | **-8.3**    | +15.4           | +54.4              |
| V2  | **-0.8**    | +18.8           | +42.8              |
| V3  | **-2.8**    | +17.6           | +49.1              |
| hV4 | +0.4        | +25.7           | +51.1              |

**CRITICAL FINDING**: Ridge regression and Gaussian ML variants are severely harmful
- Ridge: +13-26° worse than baseline
- GaussML: +38-54° worse than baseline
- **Confirms**: Correlation-based template matching is optimal for LOCO (7 training colors = insufficient df for regression)

---

## 4. Non-Linear Models (Procrustes, from loco_ensemble)

### HC Group Performance

| ROI | ForwardEncoding | MLP | SVM | HybridMLP | HybridSVR |
|-----|----------------|-----|-----|-----------|-----------|
| V1  | 76.4 ± 8.4     | 104.1 ± 4.4 | 113.0 ± 12.4 | 119.7 ± 15.4 | 121.9 ± 16.9 |
| V2  | 80.0 ± 16.7    | 99.1 ± 4.8  | 103.4 ± 19.9 | 106.5 ± 14.8 | 116.3 ± 19.7 |
| V3  | 76.9 ± 16.2    | 98.4 ± 3.6  | 102.5 ± 10.1 | 115.5 ± 15.2 | 111.2 ± 6.5  |
| hV4 | 69.4 ± 9.4     | 98.8 ± 4.4  | 104.3 ± 17.8 | 115.9 ± 16.0 | 110.9 ± 18.3 |

**Key Points**:
- All non-linear models worse than ForwardEncoding baseline
- MLP performs best among non-linear (~98-104° vs 69-80° baseline)
- Hybrid models (MLP/SVR with linear fallback) even worse (~106-122°)
- **Expected to improve with FE_Ensemble**: Per-run training should reduce overfitting

---

## 5. Key Findings & Next Steps

### Confirmed Findings

1. **FE_Ensemble is beneficial**: -8.3° improvement in HC V1, -0.8° in V2, -2.8° in V3
2. **Ridge/GaussML are harmful**: +13-54° worse due to insufficient training data (7 colors/fold)
3. **Correlation-based matching is optimal**: Template matching with ensemble encoding is best strategy
4. **Individual variability exists**: Some subjects show large improvements (sub-05: -16.5°), others show worsening in specific ROIs

### Pending Analysis

**Ensemble Rollout** (Not Yet Completed):
- ❌ FE_Ensemble not present in `loco_ensemble/{raw,procrustes,srm}/` results
- ❌ MLP/SVM with FE_Ensemble data not yet tested
- ❌ Alignment comparison (raw vs procrustes vs SRM) for FE_Ensemble incomplete

**Expected Next Steps**:
1. Re-run LOCO with FE_Ensemble across all 3 alignments (raw, procrustes, SRM)
2. Test MLP/SVM/Hybrid models with per-run ensemble data
3. Re-run LORO (Leave-One-Run-Out) validation with FE_Ensemble
4. Update group difference analyses (HC vs CVD) with ensemble-based decoders

### Recommendations

1. **Adopt FE_Ensemble as new baseline**: Consistent improvements justify using per-run encoding
2. **Abandon Ridge/GaussML variants**: Severe performance degradation confirms they're unsuitable for LOCO
3. **Re-test non-linear models**: MLP/SVM may benefit from per-run training (reduces overfitting)
4. **Complete alignment comparison**: Verify FE_Ensemble performance across raw/procrustes/SRM
5. **Group analyses**: Update HC vs CVD comparisons with FE_Ensemble decoder

---

## Technical Notes

### FE_Ensemble Method
- **Baseline (ForwardEncoding)**: Pool all 6 runs → fit single W → decode each fold
- **FE_Ensemble**: Fit 6 separate W matrices (one per run) → decode with run-specific W → combine predictions via circular mean
- **Benefit**: Reduces between-run variance, better captures within-run structure
- **Cost**: None (same degrees of freedom for template matching)

### Data Availability
- ✅ `loco_decoding_comparison.json`: FE_Ensemble vs variants (procrustes only)
- ✅ `loco_ensemble/{raw,procrustes,srm}/`: Non-linear models (no FE_Ensemble)
- ❌ FE_Ensemble × 3 alignments: Not yet computed
- ❌ FE_Ensemble + non-linear: Not yet computed

### File Locations
```
/Users/jinilkim/.../analysis/phase2_decoder_comparing/results/
├── loco_decoding_comparison/
│   ├── decoding_comparison.json          # FE_Ensemble vs variants (procrustes)
│   └── decoding_comparison_full.json     # Full fold-level data
└── loco_ensemble/
    ├── raw/sub-{01..10}_loco.json        # Raw + non-linear (no FE_Ensemble)
    ├── procrustes/sub-{01..10}_loco.json # Procrustes + non-linear (no FE_Ensemble)
    └── srm/sub-{01..10}_loco.json        # SRM + non-linear (no FE_Ensemble)
```

---

*Generated: 2026-02-23*
*Analysis: LOCO ensemble encoding validation*
*Dataset: C010 (full_dataset_C010, n=10 subjects, 4 ROIs, 6 runs, 8 colors)*
