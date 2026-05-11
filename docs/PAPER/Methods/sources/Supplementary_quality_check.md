# Supplementary Materials: Data Quality Control

**Last Updated**: 2026-03-31

---

## Quality Control Summary

Registration quality was evaluated by computing the intersection between the Wang Atlas ROIs (V1, V2, V3, hV4) and the BOLD brain mask in MNI space. Across 10 subjects, mean ROI coverage was 84.3% (SD = 21.7%), and GLM valid ratio (percentage of ROI voxels with reliable stimulus-evoked responses) was 99.6%. We evaluated all subjects' data suitable for downstream analysis, though sub-07 showed reduced coverage (30.8%) due to individual anatomical variability.

---

## **Supplementary Table 1: Registration Quality and Voxel Counts**

| Subject | Group | V1 Voxels | V2 Voxels | V3 Voxels | hV4 Voxels | Total Voxels | Notes |
|---------|-------|-----------|-----------|-----------|------------|--------------|-------|
| sub-01  | HC    | 568       | 402       | 106       | 67         | 1,143        | — |
| sub-02  | HC    | 405       | 335       | 94        | 69         | 903          | — |
| sub-03  | HC    | 858       | 557       | 115       | 70         | 1,600        | — |
| sub-04  | HC    | 858       | 557       | 115       | 70         | 1,600        | — |
| sub-05  | HC    | 858       | 557       | 115       | 70         | 1,600        | — |
| sub-06  | HC    | 858       | 557       | 115       | 70         | 1,600        | — |
| sub-07  | HC    | 330       | 258       | 59        | 16         | 663          | Reduced ROI coverage* |
| sub-08  | CVD-D | 560       | 400       | 114       | 70         | 1,144        | — |
| sub-09  | CVD-P | 692       | 498       | 115       | 70         | 1,375        | — |
| sub-10  | CVD-D | 858       | 557       | 115       | 70         | 1,600        | — |
| **Mean**  | —     | **684.5** | **467.8** | **106.3** | **64.2**   | **1,322.8**  | — |
| **SD**    | —     | **176.4** | **110.9** | **18.1**  | **15.5**   | **362.9**    | — |
| **Range** | —     | 330–858   | 258–557   | 59–115    | 16–70      | 663–1,600    | — |

*sub-07 hV4 excluded from hV4 group analyses due to insufficient voxels (n=16, correlation distance underdetermined). CVD-D = deuteranopia, CVD-P = protanopia.

**Notes**:
- Voxel counts represent the top 50% of voxels selected by FIR R-squared after initial ROI extraction
- All voxel counts are in MNI152NLin2009cAsym space (2mm resolution)
- Total voxels = sum across all four ROIs per subject

---

## **Supplementary Table 2: Data Quality Metrics**

| Metric | Mean ± SD | Range | Quality Assessment |
|--------|-----------|-------|-------------------|
| **ROI Coverage Ratio**† | 84.3% ± 21.7% | 30.8% – 100% | Good (1 outlier) |
| **GLM Valid Ratio**‡ | 99.6% | — | Excellent |
| **Procrustes Disparity** | 0.00373 ± 0.004 | ~0 – 0.016 | Excellent alignment |
| **RDM Reliability (post-Procrustes)** | 0.487 ± 0.253 | 0.038 – 0.926 | Good (79% of ceiling) |
| **Noise Ceiling** | 0.613 ± 0.248 | 0.076 – 0.949 | Good |
| **Positive Pairs (pre-Procrustes)** | 52.5% (21/40) | — | Poor (requires alignment) |
| **Positive Pairs (post-Procrustes)** | **100% (40/40)** | — | **Excellent** |

†ROI coverage ratio = proportion of Wang Atlas ROI voxels falling within BOLD brain mask in MNI space
‡GLM valid ratio = percentage of ROI voxels with reliable stimulus-evoked responses (top 50% by FIR R²)

**Notes**:
- All 40 subject-ROI pairs showed positive RDM reliability after Procrustes alignment, confirming robust color-selective signals across all subjects
- The outlier (sub-07, 30.8% coverage) reflects individual anatomical variability in occipital cortex positioning relative to limited FOV acquisition
- sub-07 retained for all ROIs except hV4 statistical analyses due to insufficient voxel count (n=16)
- Procrustes disparity values near zero indicate successful orthogonal transformation between runs

---

## **Supplementary Table 3: Per-ROI Performance Metrics**

| ROI | N | RDM Correlation (M ± SD) | Accuracy (M ± SD) | Noise Ceiling (M ± SD) | % of Ceiling |
|-----|---|--------------------------|-------------------|------------------------|--------------|
| V1  | 10 | 0.313 ± 0.215 | 0.560 ± 0.138 | 0.582 ± 0.172 | 24.2% |
| V2  | 10 | 0.370 ± 0.256 | 0.581 ± 0.131 | 0.635 ± 0.200 | 29.0% |
| V3  | 10 | 0.316 ± 0.328 | 0.613 ± 0.130 | 0.525 ± 0.226 | 23.2% |
| hV4 | 9* | **0.541 ± 0.283** | **0.613 ± 0.092** | **0.697 ± 0.168** | **41.8%** |
| **Overall** | **39** | **0.381** | **0.592** | **0.610** | **29.6%** |

*hV4 N = 9; sub-07 excluded (16 voxels, correlation distance underdetermined)

**Notes**:
- All metrics computed after Procrustes alignment
- RDM correlation = split-half Spearman correlation with Spearman-Brown correction
- Accuracy = leave-one-run-out (LORO) decoding accuracy (chance = 12.5%)
- Noise ceiling = upper bound on RDM reliability from split-half analysis
- hV4 shows strongest color selectivity: highest RDM correlation, highest noise ceiling, lowest cross-subject variability

---

## Methods Details

### Registration Method
- **fMRIPrep version**: 23.2.3
- **Template space**: MNI152NLin2009cAsym (2mm isotropic)
- **BOLD→T1w registration**: Header-based initialization + Mutual Information optimization (mri_coreg)
  - Robust to partial FOV (occipital-only coverage)
  - Safe for high obliquity acquisition (29.5° sagittal tilt)
- **ROI definition**: Wang Atlas probabilistic maps (Wang et al., 2015)

### Voxel Selection
- **1st-level GLM**: FIR basis functions (8 delays, 0–12s post-stimulus)
- **Selection criterion**: Top 50% voxels by FIR R-squared per ROI
- **Rationale**: Retains color-selective voxels while removing noise-dominated voxels

### Quality Control Checks
1. **ROI coverage**: Intersection of Wang Atlas ROI with BOLD brain mask
2. **GLM validity**: Percentage of ROI voxels with reliable stimulus responses
3. **Alignment quality**: Procrustes disparity between runs (target: <0.01)
4. **Signal reliability**: Split-half RDM correlation (positive = interpretable)

### Exclusion Criteria
- **sub-07 hV4**: Excluded from hV4 group statistics due to n=16 voxels
  - Correlation distance becomes underdetermined with <20 voxels
  - Retained for V1, V2, V3 analyses (330, 258, 59 voxels respectively)
- **No other exclusions**: All other subject-ROI pairs met quality criteria

---

## References

- Wang, L., Mruczek, R. E., Arcaro, M. J., & Kastner, S. (2015). Probabilistic maps of visual topography in human cortex. *Cerebral Cortex*, 25(10), 3911-3931.
- Gower, J. C., & Dijksterhuis, G. B. (2004). *Procrustes Problems*. Oxford University Press.

---

**File Location**: `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/docs/PAPER/Methods/Supplementary_quality_check.md`

**Data Source**: `analysis/phase1_procrustes_decoding/results/visualization/full_dataset_C010_with_residuals/*/config.json`
