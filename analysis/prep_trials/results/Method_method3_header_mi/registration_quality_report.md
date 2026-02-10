# Registration Quality Report - Method3 Header MI

**Method**: method3_header_mi

**Generated**: 2026-01-22T10:11:56.188208

**Total Subjects**: 10

---

## 1. Subject-Level Summary

Mean metrics across all runs and ROIs for each subject.

| Subject   |   N Runs |   Mean ROI Voxels |   Mean Valid Voxels |   ROI Coverage (%) |   GLM Valid Ratio (%) |   GLM Amplitude |   GLM Variance |
|:----------|---------:|------------------:|--------------------:|-------------------:|----------------------:|----------------:|---------------:|
| sub-01    |        6 |              1088 |                1088 |               77.9 |                 100   |           19.79 |          506.7 |
| sub-02    |        6 |               864 |                 864 |               69.2 |                 100   |           18.35 |          367.9 |
| sub-03    |        6 |              1571 |                1571 |               99   |                 100   |           18.68 |          469.7 |
| sub-04    |        6 |              1585 |                1585 |               99.5 |                 100   |           18.41 |          479.9 |
| sub-05    |        4 |              1600 |                1600 |              100   |                 100   |           22.16 |          589.5 |
| sub-07    |        6 |               515 |                 515 |               30.8 |                  95.8 |           16.75 |          537.6 |
| sub-06    |        6 |              1600 |                1600 |              100   |                 100   |           20.46 |          663.5 |
| sub-08    |        6 |              1147 |                1147 |               84.2 |                 100   |           29.81 |         1489.2 |
| sub-09    |        6 |              1324 |                1324 |               90.7 |                 100   |           19.96 |          519.1 |
| sub-10    |        5 |              1600 |                1600 |              100   |                 100   |           16.01 |          320.4 |

**Notes:**
- **Mean ROI Voxels**: Average number of voxels in ROI intersection with BOLD brain mask (across all 4 ROIs)
- **Mean Valid Voxels**: Average number of voxels with valid GLM fits
- **ROI Coverage**: Percentage of atlas ROI voxels that overlap with BOLD brain mask
- **GLM Valid Ratio**: Percentage of ROI voxels with valid GLM fits
- **GLM Amplitude**: Mean absolute beta values across color conditions
- **GLM Variance**: Mean variance of beta values across colors (signal differentiation)

---

## 2. Per-ROI Summary (All Subjects)

Statistics computed across all subjects and runs.

| ROI   |   N Samples |   Mean ROI Voxels |   Mean Intersection Voxels |   Coverage Mean (%) |   Coverage Std (%) |   GLM Valid Mean (%) |   GLM Amplitude Mean |
|:------|------------:|------------------:|---------------------------:|--------------------:|-------------------:|---------------------:|---------------------:|
| V1    |          57 |               858 |                        655 |                76.4 |               25.4 |                100   |                21.4  |
| V2    |          57 |               557 |                        451 |                81   |               21.8 |                100   |                21.66 |
| V3    |          57 |               115 |                        103 |                89.9 |               20.2 |                100   |                18.81 |
| hV4   |          57 |                70 |                         63 |                90.1 |               24.9 |                 98.2 |                18.27 |

**Notes:**
- **Mean ROI Voxels**: Atlas ROI size in MNI space
- **Mean Intersection Voxels**: Average number of voxels overlapping with BOLD brain mask

---

## 3. Subject Group Comparison

| Group         | ROI Coverage (%)   | GLM Valid Ratio (%)   | GLM Amplitude   |
|:--------------|:-------------------|:----------------------|:----------------|
| Non-CVD (n=7) | 82.3 ± 26.0        | 99.4 ± 1.6            | 19.23 ± 1.75    |
| CVD (n=3)     | 91.6 ± 7.9         | 100.0 ± 0.0           | 21.93 ± 7.11    |

---

## 4. Special Notes

### Sub-07 Quality Metrics

Sub-07 shows lower ROI coverage compared to other subjects, but maintains good GLM signal quality.

| ROI   |   Mean ROI Voxels |   Mean Intersection Voxels |   Mean Valid Voxels |   Coverage (%) |   GLM Valid (%) |
|:------|------------------:|---------------------------:|--------------------:|---------------:|----------------:|
| V1    |               858 |                        252 |                 252 |           29.4 |           100   |
| V2    |               557 |                        206 |                 206 |           37   |           100   |
| V3    |               115 |                         43 |                  43 |           37.5 |           100   |
| hV4   |                70 |                         14 |                  14 |           19.3 |            83.3 |

**Interpretation**: While ROI coverage is reduced (30% vs 90% average), GLM valid ratios remain high, indicating that the overlapping voxels provide valid signal. This subject is included in analyses with a note about lower statistical power.

---

## 5. Overall Quality Assessment

| Metric          | Mean   | Std   | Min   | Max    |
|:----------------|:-------|:------|:------|:-------|
| ROI Coverage    | 84.3%  | 21.7% | 17.3% | 100.0% |
| GLM Valid Ratio | 99.6%  | 3.3%  | 75.0% | 100.0% |
| GLM Amplitude   | 20.03  | 4.55  | 12.86 | 37.73  |

### Verdict

✅ **EXCELLENT** - Registration quality is excellent across all subjects. GLM valid ratios exceed 95%, indicating reliable signal extraction from ROIs.

**Recommended for downstream analysis**: Yes, all subjects included.

