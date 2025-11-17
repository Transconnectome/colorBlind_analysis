# Analysis Summary: zscore vs voxelSelect Methods
**Date:** November 17, 2025
**Analysis of logs:** 20251117_021334 (zscore) vs 20251117_021329 (voxelSelect)

---

## Executive Summary

This analysis compares two preprocessing methods (zscore vs voxelSelect) across:
- **Subjects:** sub-01, sub-02 (Non-CVD) vs sub-03, sub-04 (CVD)
- **ROIs:** V1, V2, V3, hV4
- **Tasks:** Classification, Reconstruction, Novel Color Reconstruction

### Key Findings:
1. **Classification Accuracy:** Perfect (100%) across all conditions
2. **Reconstruction Performance:** zscore method shows lower errors overall
3. **Novel Color Generalization:** Comparable between methods with high variability
4. **Group Differences:** CVD subjects show slightly worse performance than Non-CVD

---

## 1. Method Comparison Overview

### Overall Statistics by Method

| Method | Avg N_voxels | Classification Acc | Reconstruction Error (deg) | Novel Color Error (deg) |
|--------|--------------|-------------------|---------------------------|------------------------|
| **zscore** | 235.0 ± 185.9 | 1.00 ± 0.00 | 20.19 ± 23.64 | 84.88 ± 25.40 |
| **voxelSelect** | 41.4 ± 29.9 | 1.00 ± 0.00 | 22.81 ± 20.65 | 91.17 ± 25.38 |

**Key Observations:**
- zscore uses ~5.7x more voxels than voxelSelect
- zscore shows slightly better reconstruction (20.19° vs 22.81°)
- Novel color errors are high for both methods (>80°)

---

## 2. Performance by ROI

### Average Performance by Method and ROI

#### zscore Method:
| ROI | N_voxels | Classification | Reconstruction Error | Novel Color Error |
|-----|----------|---------------|---------------------|------------------|
| V1  | 482.8    | 1.00          | 37.44°              | 92.53°           |
| V2  | 321.3    | 1.00          | **6.09°** ✓         | 84.56°           |
| V3  | 87.8     | 1.00          | 22.88°              | 76.19°           |
| hV4 | 48.3     | 1.00          | 14.34°              | 86.25°           |

#### voxelSelect Method:
| ROI | N_voxels | Classification | Reconstruction Error | Novel Color Error |
|-----|----------|---------------|---------------------|------------------|
| V1  | 74.8     | 1.00          | **14.91°** ✓        | 95.25°           |
| V2  | 48.3     | 1.00          | **9.81°** ✓         | 68.91°           |
| V3  | 16.0     | 1.00          | 28.72°              | 94.09°           |
| hV4 | 12.0     | 1.00          | 52.81°              | 121.69°          |

**Key Observations:**
- **V2 performs best** for reconstruction in both methods
- **V1 with voxelSelect** shows excellent reconstruction (14.91°)
- **hV4 with voxelSelect** shows worst performance (52.81° reconstruction, 121.69° novel)

---

## 3. Non-CVD vs CVD Comparison

### Group Average Performance

#### Non-CVD (sub-01, sub-02):
| Method | Reconstruction Error | Novel Color Error |
|--------|---------------------|------------------|
| zscore | 13.72° ± 20.07 | 80.05° ± 27.73 |
| voxelSelect | 14.36° ± 13.38 | 93.34° ± 22.52 |

#### CVD (sub-03, sub-04):
| Method | Reconstruction Error | Novel Color Error |
|--------|---------------------|------------------|
| zscore | 26.66° ± 26.45 | 89.72° ± 23.67 |
| voxelSelect | 31.27° ± 24.03 | 89.00° ± 29.62 |

**Key Observations:**
- **CVD subjects show ~2x higher reconstruction errors** (26.66° vs 13.72° for zscore)
- **Novel color errors are similarly high** for both groups (80-93°)
- **CVD subjects show higher variability** in performance

### Detailed Group Comparison by ROI

#### Non-CVD Group:
| ROI | zscore Recon | voxelSelect Recon | zscore Novel | voxelSelect Novel |
|-----|--------------|------------------|--------------|------------------|
| V1  | 34.31°       | **7.00°** ✓      | 82.06°       | 80.94°           |
| V2  | 7.00°        | 8.25°            | 103.69°      | 85.44°           |
| V3  | **4.38°** ✓  | 20.69°           | **53.63°** ✓ | 97.13°           |
| hV4 | **9.19°** ✓  | 28.63°           | **80.81°** ✓ | 126.38°          |

#### CVD Group:
| ROI | zscore Recon | voxelSelect Recon | zscore Novel | voxelSelect Novel |
|-----|--------------|------------------|--------------|------------------|
| V1  | 40.56°       | 22.81°           | 103.00°      | 109.56°          |
| V2  | **5.19°** ✓  | 11.38°           | 65.44°       | **52.38°** ✓     |
| V3  | 41.38°       | 36.75°           | 98.75°       | 91.06°           |
| hV4 | 19.50°       | 77.00°           | 91.69°       | 117.00°          |

**Critical Insights:**
1. **V1 in Non-CVD:** voxelSelect excels (7.00° reconstruction)
2. **V2 in CVD:** zscore excels (5.19° reconstruction)
3. **V3 in Non-CVD:** zscore excels (4.38° reconstruction, 53.63° novel)
4. **Novel color reconstruction remains challenging** across all conditions

---

## 4. Best Performing Configurations

### Top 5 Lowest Reconstruction Errors:
1. **sub-01, V2, voxelSelect:** 2.38° ⭐
2. **sub-02, hV4, zscore:** 3.63°
3. **sub-01, V3, zscore:** 4.13°
4. **sub-02, V1, voxelSelect:** 4.25°
5. **sub-04, V2, zscore:** 4.38°

### Top 5 Lowest Novel Color Errors:
1. **sub-02, V3, zscore:** 42.38° ⭐
2. **sub-03, V2, voxelSelect:** 49.63°
3. **sub-04, V2, voxelSelect:** 55.13°
4. **sub-04, V2, zscore:** 58.13°
5. **sub-02, hV4, zscore:** 64.50°

**Key Insight:** Sub-01 and Sub-02 (Non-CVD) dominate the best performing configurations

---

## 5. Task-Specific Analysis

### Task 1: Classification (8-way color discrimination)
- **Performance:** Perfect (100%) across all subjects, ROIs, and methods
- **Conclusion:** Both methods successfully extract discriminable color information

### Task 2: Reconstruction (trained colors)
- **Best Overall:** zscore on V2 (6.09° average)
- **Best Individual:** sub-01, V2, voxelSelect (2.38°)
- **Worst:** voxelSelect on hV4 (52.81° average)
- **Conclusion:** Reconstruction quality varies greatly by ROI and subject

### Task 3: Novel Color Reconstruction
- **Best Overall:** voxelSelect on V2 (68.91° average)
- **Best Individual:** sub-02, V3, zscore (42.38°)
- **Challenge:** All configurations show high errors (>40°)
- **Conclusion:** Generalization to novel colors remains a significant challenge

---

## 6. Statistical Observations

### Variability Analysis:
- **Reconstruction errors:** High variability (std ~20-27°) indicates subject-specific differences
- **Novel color errors:** Consistent high values (~80-90°) suggest systematic limitation
- **Method stability:** voxelSelect shows slightly lower std in reconstruction (20.65° vs 23.64°)

### Missing Data:
- Sub-02, hV4, voxelSelect: MISSING
- Sub-03, hV4, voxelSelect: MISSING

**Note:** Analysis based on 30 complete records (out of 32 expected)

---

## 7. Recommendations

### For Reconstruction Task:
1. **Use zscore for V2 and V3** - consistently low errors
2. **Use voxelSelect for V1** - excellent performance with fewer voxels
3. **Avoid hV4 with voxelSelect** - unreliable performance

### For Novel Color Task:
1. **Both methods struggle** - errors typically >70°
2. **V3 with zscore in Non-CVD** shows promise (53.63°)
3. **Consider alternative approaches** for novel color generalization

### For CVD Analysis:
1. **CVD subjects need special attention** - 2x higher reconstruction errors
2. **V2 shows most robustness** across both groups
3. **Individual variability is high** - subject-specific models may be needed

### For Voxel Efficiency:
- **voxelSelect achieves comparable performance with ~5-6x fewer voxels**
- Useful for computational efficiency and potential overfitting reduction

---

## 8. Conclusions

### Method Comparison:
- **zscore:** Better average reconstruction, uses more voxels
- **voxelSelect:** Competitive performance with fewer voxels, higher variability

### ROI Insights:
- **V2:** Most reliable across subjects and methods
- **V1:** Excellent with voxelSelect in Non-CVD
- **hV4:** Most challenging, inconsistent performance

### Group Differences:
- **Non-CVD subjects:** Superior reconstruction (13-14° vs 26-31°)
- **CVD subjects:** Increased errors suggest altered color processing
- **Novel color task:** Challenging for both groups

### Critical Challenge:
**Novel color reconstruction errors (>70°) indicate that current forward encoding models struggle to generalize beyond trained colors. This suggests:**
1. Models may be overfitting to training colors
2. Channel basis functions may not span full color space
3. Additional regularization or model complexity may be needed

---

## Generated Files:
- `combined_results_20251117.csv` - All results in tabular format
- `detailed_results_by_subject_20251117.csv` - Subject-level details
- `average_by_method_roi_20251117.csv` - Method × ROI averages
- `average_by_group_20251117.csv` - Group comparison tables
- `analysis_comparison_20251117.png` - Comprehensive visualization (12 panels)
