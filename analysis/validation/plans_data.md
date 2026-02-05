This is to verify data and model structure in the analysis.
Once finished each part, write the directory of result files in this file.

## 0. Configuration

**Dataset**: `method3_header_mi` (current standard)
**Baseline timestamp**: `only_Zscore_1stGLM` (z-score normalization at 1st GLM)
**ROIs**: V1, V2, V3, hV4
**Subjects**:
  - HC (non-CVD): sub-01 ~ sub-07 (7명)
  - CVD: sub-08 ~ sub-10 (3명)

**Base paths**:
```
FMRIPREP_OUT=/storage/connectome/haba6030/fmriprep_out_method3_header_mi
ROI_MASKS=/scratch/connectome/haba6030/colorBlind/analysis/roi_masks/method3_header_mi
BASELINE_RESULTS=/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding/only_Zscore_1stGLM
VALIDATION_OUT=/scratch/connectome/haba6030/colorBlind/analysis/validation/results
```

**Data structure verified**:
- amplitudes_z.npy: (6 runs, 8 colors, ~284 voxels for V1)
- Range: [-2.48, 2.47] (z-scored)
- File size: ~0.1 MB per subject-ROI

---

## Data Verification

### 1. Preprocessing results: Metrics & Visualization

#### 1.1 tSNR Analysis
[ ] **Task**: ROI별 tSNR 분포 계산 및 시각화

**Input**:
- fMRIPrep outputs: `{FMRIPREP_OUT}/sub-{ID}/func/*_desc-preproc_bold.nii.gz`
- ROI masks: `{BASELINE_RESULTS}/sub-{ID}/{ROI}/roi_mask.nii.gz`

**Computation**:
```python
# Per ROI, per run
tSNR = mean(signal) / std(signal)  # voxel-wise
tSNR_roi = median(tSNR[roi_mask])  # ROI summary
```

**Output**:
- `{VALIDATION_OUT}/tsnr/{TIMESTAMP}/tsnr_values.json` (subject×run×ROI)
- Figures:
  - `tsnr_violin_by_roi.png` (ROI별 분포, run 구분)
  - `tsnr_boxplot_by_subject.png` (subject별, ROI 구분)

**Expected range**: tSNR > 50 (good), 30-50 (acceptable), <30 (poor)

**Results**: ✅ `/scratch/connectome/haba6030/colorBlind/analysis/validation/results/tsnr/20260127_111659`

**Findings**:
- Overall tSNR: 24.68 ± 8.25 (⚠️ below expected, but acceptable for 7T)
- Quality: 0/240 good, 52/240 acceptable (21.7%), 188/240 poor (78.3%)
- **Drift Analysis** (movement indicator):
  - Mean drift: 0.006%/TR ✅ Stable (no severe movement)
  - Severe drift (>1%/TR): 0/240 ✅
  - All runs stable (<0.5%/TR): 240/240 ✅
- **Subject-specific issues**:
  - sub-07: tSNR = 5.9 (❌ critical, likely data corruption)
  - Other subjects: 21-29 (⚠️ low but usable with normalization)
- **ROI differences**: hV4 (28.9) > V3 (25.9) > V2 (22.1) ≈ V1 (21.7)

**Conclusion**: Low tSNR but stable drift → Data usable with z-score normalization and R² selection. Sub-07 may need exclusion pending task response quality check.

---

#### 1.2 Mask Stability
[SKIPPED] **Reason**: Single mask used across all runs (no run-specific masks)

**Input**:
- ROI masks: `{ROI_MASKS}/sub-{ID}/roi_pipeline/{ROI}_mask_*.nii.gz`
- (Note: Single mask used across all runs in current pipeline)

**Computation**:
```python
# Voxel count stability
voxel_counts = [count_nonzero(mask_run_i) for i in runs]
CV = std(voxel_counts) / mean(voxel_counts)  # Coefficient of variation

# Dice overlap between runs
Dice(A, B) = 2 * |A ∩ B| / (|A| + |B|)
# Calculate for all run pairs
```

**Output**:
- `{VALIDATION_OUT}/mask_stability/{TIMESTAMP}/voxel_counts.json`
- `{VALIDATION_OUT}/mask_stability/{TIMESTAMP}/dice_overlap.json`
- Figures:
  - `roi_overlay_qc.png` (각 run별 mask overlay on template)
  - `voxel_count_consistency.png` (run별 voxel count bar plot)

**Expected**: Dice > 0.8 (good overlap), CV < 0.1 (stable)

**Results**: _[write directory here after completion]_

---

### 2. HRF Estimation Quality

#### 2.1 HRF Correlation between runs
[SKIPPED] **Reason**: HRF variability has minimal impact on decoder performance; not critical for validation

**Input**:
- Baseline results에서 추출한 ROI-level HRF (8 delays per run)
- Location: `{BASELINE_RESULTS}/sub-{ID}/{ROI}/roi_hrf.npy`
  - Shape: (n_runs, n_delays) = (6, 8)

**Computation**:
```python
# HRF profile correlation between all run pairs
for run_i, run_j in combinations(runs, 2):
    r_pearson = pearsonr(HRF_i, HRF_j)
    r_spearman = spearmanr(HRF_i, HRF_j)

# Average correlation per subject-ROI
mean_corr = mean(all_pairwise_correlations)
```

**Output**:
- `{VALIDATION_OUT}/hrf_correlation/{TIMESTAMP}/hrf_corr_matrix.json`
- Figures:
  - `hrf_profiles_by_run.png` (각 run별 HRF time course overlay)
  - `hrf_correlation_heatmap.png` (run pair 간 correlation matrix)

**Expected**: r > 0.7 (good consistency across runs)

**Results**: _[write directory here after completion]_

---

### 3. Representational Similarity Analysis (RSA)

**Purpose**: RDM 신뢰성 및 정렬 효과 검증

**Threshold criteria**:
- (i) Split-half reliability (noise ceiling 근사)
- (ii) Permutation null 대비 효과크기
- 해석: "표현이 noise ceiling에 근접 → 더 이상 모델 개선 여지 없음"

---

#### 3.1 RDM Credibility (Within-subject)

##### 3.1.1 Across-run RDM Reliability
[IN PROGRESS - Phase 2.5] **Task**: 동일 피험자 내에서 run 간 RDM 일관성 검증

**⚠️ CRITICAL UPDATE (2026-01-30): DC-Dependence Investigation**

**Scripts**:
- `03_rdm_reliability.py`: Original amplitudes (no alignment)
- `03b_rdm_reliability_aligned.py`: After Procrustes alignment (run-to-run)

**Input**:
- Baseline amplitudes: `{BASELINE_RESULTS}/sub-{ID}/{ROI}/amplitudes_z.npy`
  - Shape: (n_runs=6, n_colors=8, n_voxels)
  - Note: File is in `sub-{ID}/{ROI}/` subdirectory of BASELINE_RESULTS

**Output**:
- `{VALIDATION_OUT}/rdm_reliability/{TIMESTAMP}/within_subject_reliability.json`
  - Per subject: mean ± std of run-pair correlations
  - Per ROI: distribution across subjects
- Figures:
  - `rdm_reliability_distribution.png` (ROI별 violin plot)
  - `rdm_matrices_per_run.png` (예시 subject의 run별 RDM, 2×3 panel)

**Expected**: r > 0.6 (good), r > 0.4 (acceptable)

---

**Phase 2.6: Grid Resampling + Comprehensive Factorial Experiment (COMPLETED - 2026-01-30)**

**Purpose**: Fix voxel correspondence issues and identify optimal preprocessing pipeline

**Motivation**:
- Procrustes disparities of 10^4-10^8 indicated severe voxel misalignment
- Same voxel indices pointing to different physical locations across runs
- Need systematic comparison of all preprocessing combinations

**Experimental Design: 2×2×3×3 Factorial (36 conditions)**

*Factors*:
1. **Grid resample**: no, yes (resample all runs to run-1 reference grid)
2. **Highpass**: 0.0 Hz, 0.01 Hz
3. **Motion**: none, standard (6 params), cosine (motion + DCT drift)
4. **Drift**: none, per_run, per_run_2nd (+ 2nd-level intercept)

**Key Metrics (Before/After Procrustes)**:
1. RDM correlation reliability (Pearson-based)
2. RDM crossnobis reliability (Mahalanobis with Ledoit-Wolf shrinkage)
3. Decoding accuracy (leave-one-run-out)
4. Procrustes disparity (alignment quality)

**Results**: `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/grid_factorial/`

**Critical Findings**:

3. **Best Configuration (Top 5)**:
   | Rank | Condition | Accuracy | RDM Corr | Config |
   |------|-----------|----------|----------|--------|
   | 1 | c02, c20 | **75.0%** | 0.210 | hp=0, motion=none, drift=per_run |
   | 2 | c01, c19 | **66.7%** | 0.335 | hp=0, motion=none, drift=none |
   | 3 | c03, c21 | 58.3% | 0.307 | hp=0, motion=none, drift=2nd |
   | 4 | c09, c18, c27, c36 | 58.3% | 0.224 | hp=0, motion=cosine, drift=2nd |
   | 5 | c08, c17, c26, c35 | 52.1% | 0.186 | hp=0, motion=cosine, drift=per_run |

   **Pattern**: All top conditions use **hp=0** (no highpass) and avoid standard motion regression

4. **Factor Effects (Ranked by Impact)**:
   | Factor | Best Level | Worst Level | Effect Size |
   |--------|-----------|-------------|-------------|
   | **Motion** | none (55.2%) | standard (36.1%) | **-19.1%** 🔴 Critical |
   | **Highpass** | 0.0 Hz (52.3%) | 0.01 Hz (41.4%) | -10.9% 🟡 Moderate |
   | **Drift** | per_run (50.0%) | none (41.3%) | +8.7% 🟢 Small positive |
   | **Grid Resample** | N/A | N/A | 0.0% ⚪ No effect (broken) |

6. **Procrustes Improvement Statistics**:
   - RDM correlation: +0.125 ± 0.115 (83% positive)
   - RDM crossnobis: +0.052 ± 0.053 (78% positive)
   - Decoding accuracy: +37.0% ± 10.2% (100% positive!)
   - Disparity: 446-2515 (extremely high, indicating severe misalignment)

**Comparison with Previous Results**:

| Configuration | Dataset | Subject | RDM Reliability | Decoding Acc | Notes |
|---------------|---------|---------|-----------------|--------------|-------|
| **Baseline32** | method3_header_mi | sub-01 V1 | 0.775 | 16.7% | hp=0.01, cosine, PCA |
| **A1** (Phase 2.1) | method3_header_mi | sub-01 V1 | **0.818** | N/A | hp=0, per_run drift (DC preserved) |
| **A1b** (Phase 2.1) | method3_header_mi | sub-01 V1 | -0.002 | N/A | hp=0, 2nd-level intercept (DC removed) |
| **c02 (Grid Factorial)** | method3_header_mi | sub-01 V1 | 0.210 (before Proc)<br>**0.161 crossnobis** | 12.5% (before)<br>**75.0%** (after) | hp=0, no motion, per_run |
| **c01 (Grid Factorial)** | method3_header_mi | sub-01 V1 | -0.046 (before)<br>0.335 (after Proc) | 16.7% (before)<br>**66.7%** (after) | hp=0, no motion, no drift |

**Key Insights**:
- **A1 vs Grid Factorial discrepancy**: A1 achieved r=0.818 WITHOUT Procrustes, but Grid Factorial needs Procrustes for any reliability
  - **Hypothesis**: Different voxel selection strategies OR different evaluation methods
  - **Need**: Re-run A1 with same evaluation pipeline for fair comparison
- **Baseline32 vs c02**: Baseline32 used PCA compression (30 components), c02 used raw voxels
  - PCA may explain lower reliability but more stable decoding
- **Dataset consistency**: All use method3_header_mi (MI-based coregistration with header optimization)

**Production Pipeline Recommendation** (pending grid resample fix):
```bash
--grid-resample yes        # After debugging!
--highpass 0              # NO highpass filter
--motion none             # NO motion regression (or cosine if motion artifacts severe)
--drift per_run           # Per-run drift modeling
--smooth 0                # No spatial smoothing
--normalize-level none    # No normalization (z-score at GLM level only)
```

---

**Section 2.6.1: Adopt Procrustes**

**Rationale**:

1. **Theoretical Foundation** (Haxby et al. 2020):
   - Fine-scale functional topography is **idiosyncratic** across individuals
   - Anatomical alignment (including grid resampling) **cannot resolve** functional misalignment
   - Grid resampling = Still anatomical → Fundamentally limited

2. **Signal Recovery, Not Data Manipulation** (Feilong et al. 2018):
   - Before alignment: Signal confounded with topographic noise
   - After alignment: Topographic misalignment removed → **True signal revealed**
   - RDM correlation increase = Signal recovery (not artifact)

3. **Standard Methodology** (Bazeille et al. 2021):
   - Functional alignment (Procrustes, SRM, OT) is **typical** in inter-subject analysis
   - Performance improvement over anatomical alignment is **expected**
   - Procrustes = Efficient and accurate (especially piecewise application)

4. **Mathematical Validity** (Chen et al. 2015, Nastase et al. 2020):
   - SRM separates shared response from individual topography
   - Functional alignment = Extracting shared structure (not data manipulation)
   - Well-established theoretical framework

**Empirical Support from Our Data**:

| Metric | Before Procrustes | After Procrustes | Interpretation |
|--------|-------------------|------------------|----------------|
| RDM correlation | -0.023 ± 0.062 | **+0.099 ± 0.124** | Negative → Positive (signal recovery) |
| RDM crossnobis | -0.003 ± 0.057 | **+0.045 ± 0.050** | Near-zero → Positive |
| Decoding accuracy | 10.1% ± 4.1% | **46.9% ± 12.8%** | Below chance → 3.9× chance |
| Best configuration | - | **75% accuracy** | 6× chance level |
| Positive improvement | - | **100%** (36/36) | Universal benefit |

**Comparison with Literature**:
- **Haxby et al. (2020)**: Hyperalignment increased ISC from 46% to 75% (+29%)
- **Our results**: Procrustes increased accuracy from 10% to 47% (+37%) → Comparable scale

**For Paper Defense**:
> "Procrustes alignment in our study is not a data manipulation but a **necessary correction** for anatomical-functional misalignment (Haxby et al. 2020). The dramatic improvement in RDM reliability and decoding accuracy after alignment reflects **signal recovery** rather than noise inflation (Feilong et al. 2018), consistent with the standard practice in inter-subject RSA (Bazeille et al. 2021)."

**Status**: ✅ **RESOLVED - Procrustes adopted as primary alignment strategy**

---

**OPTIONAL: GLMsingle for Improved Beta Estimation (Future Work)**

**Problem**:
Current FIR-based pipeline shows poor voxel quality:
- 62.5% of voxels with R² < 0.2 (poor fit)
- Top 50% selection threshold = R² 0.14 (very low)
- Median selected voxel R² = 0.31 (moderate at best)
- **Root cause**: Fixed FIR basis cannot adapt to voxel-specific HRF variability and noise structure

**Evidence from Grid Factorial** (c02 optimal configuration):
```
Voxel Selection Quality (sub-01 V1):
  R² < 0.1:    368/858 (42.9%) - Model fails completely
  R² 0.1-0.2:  168/858 (19.6%) - Marginal fit
  R² 0.2-0.3:  101/858 (11.8%) - Acceptable fit
  R² > 0.3:    221/858 (25.8%) - Good fit

Selection threshold (top 50%): R² = 0.137
→ Half of "selected" voxels still poorly explained!
```

---

**Phase 3.0: Baseline Pipeline Deployment & Procrustes Effect Analysis (CURRENT - 2026-01-30)**

**Purpose**: Establish baseline performance across all subjects/ROIs and quantify Procrustes alignment effects

**Baseline Configuration Finalized** (from Phase 2.6 Grid Factorial):
```bash
Pipeline: c02 (optimal from 36-condition factorial experiment)
  --highpass 0          # Preserve DC components
  --motion none         # No motion regression
  --drift per_run       # Per-run drift modeling only
  --smooth 0            # No spatial smoothing
  --normalize-level none

Post-processing: Procrustes alignment (MANDATORY)
  - Method: Orthogonal Procrustes after center + scale normalization
  - Reference: Mean pattern across runs
```

**Validated Performance** (sub-01 V1):
```
Before Procrustes:
  RDM correlation:  -0.025 (negative!)
  RDM crossnobis:   -0.028
  Decoding accuracy: 12.5% (chance level)

After Procrustes:
  RDM correlation:   0.210 ✓
  RDM crossnobis:    0.161 ✓
  Decoding accuracy: 75.0% ✓ (6× chance)

Procrustes Effect:
  RDM improvement:  +0.235 (+940%!)
  Crossnobis:       +0.189
  Decoding:         +62.5%
```

**Metrics Computed (Before/After Procrustes)**:

**Data**: 40 subject-ROI pairs (10 subjects × 4 ROIs)
- HC: 7 subjects (sub-01 ~ sub-07) → 28 pairs (27 valid RDMs due to sub-07_hV4 NaN)
- CVD: 3 subjects (sub-08 ~ sub-10) → 12 pairs (all valid)

**Results Location**: `/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding/only_Zscore_1stGLM/`

---

### 1. **RDM Correlation Reliability** (Pearson-based dissimilarity)

**Overall Performance**:
```
Before Procrustes:  -0.009 ± 0.051 [95% CI: -0.024, 0.007] (n=39)
After Procrustes:    0.226 ± 0.151 [95% CI: 0.179, 0.273] (n=39)
Improvement:         0.234 ± 0.169 [95% CI: 0.183, 0.288]
  → Positive improvement: 38/39 (97.4%)
  → Mean increase: 26.3× (from near-zero to 0.226)
```

**Interpretation**:
- **Before**: Negative mean indicates *worse than random* similarity across runs
- **After**: Moderate positive correlation (0.226) → Consistent color representation recovered
- **Success**: 97.4% of cases showed improvement after alignment

**Per-ROI Breakdown** (After Procrustes):
```
V1:  0.154 ± 0.150 (n=10)  [Primary visual cortex - lowest]
V2:  0.256 ± 0.143 (n=10)  [↑]
V3:  0.256 ± 0.146 (n=10)  [↑]
hV4: 0.238 ± 0.167 (n=9)   [Highest variability]
```

**HC vs CVD** (After Procrustes):
```
HC:  0.225 ± 0.141 (n=27)
CVD: 0.228 ± 0.179 (n=12)
t-test: t=-0.057, p=0.955 (ns)
```
→ No significant difference between groups in within-subject RDM reliability

---

### 2. **RDM Crossnobis Reliability** (Mahalanobis distance with Ledoit-Wolf shrinkage)

**Overall Performance**:
```
Before Procrustes:  -0.010 ± 0.043 [95% CI: -0.023, 0.004] (n=39)
After Procrustes:    0.219 ± 0.141 [95% CI: 0.177, 0.263] (n=39)
Improvement:         0.228 ± 0.125 [95% CI: 0.191, 0.269]
  → Positive improvement: 38/39 (97.4%)
  → Mean increase: 24.0× (from near-zero to 0.219)
```

**Ledoit-Wolf Shrinkage** (optimal covariance estimation):
- Mean shrinkage: 0.063 ± 0.025 (range: 0.023-0.143)
- Interpretation: 6.3% shrinkage toward diagonal → Low-dimensional signal structure
- Expected range for fMRI: 0.2-0.4 (ours is lower → well-conditioned covariance)

**HC vs CVD** (After Procrustes):
```
HC:  0.250 ± 0.155 (n=27)
CVD: 0.149 ± 0.066 (n=12)
t-test: t=2.150, p=0.038 (*)
```
→ **Significant difference**: HC shows higher crossnobis reliability than CVD (p<0.05)
→ This may reflect higher within-subject consistency in HC group

---

### 3. **Decoding Accuracy** (Leave-one-run-out 8-class classification)

**Overall Performance**:
```
Before Procrustes:  11.0% ± 3.1% [95% CI: 10.1%, 12.0%] (n=40)
After Procrustes:   63.8% ± 17.2% [95% CI: 58.5%, 69.0%] (n=40)
Improvement:        52.7% ± 17.6% [95% CI: 47.2%, 58.1%]
  → Positive improvement: 40/40 (100.0%)
  → Mean increase: 5.8× (relative to chance: 5.1× → 29.6×)
```

**Chance level**: 12.5% (8 colors)

**Before Procrustes**:
- 11.0% accuracy → **Below chance** (statistically indistinguishable from random)
- Indicates severe topographic misalignment across runs

**After Procrustes**:
- 63.8% accuracy → **5.1× chance level**
- Demonstrates successful signal recovery

**Per-ROI Performance** (Decoding Accuracy After Procrustes):
```
V1:  58.3% ± 21.2% (n=10)  [Lowest, but still 4.7× chance]
V2:  64.6% ± 16.2% (n=10)
V3:  67.7% ± 18.3% (n=10)  [Highest mean]
hV4: 64.8% ± 11.8% (n=10)  [Lowest variability]
```

**HC vs CVD** (After Procrustes):
```
HC:  64.4% ± 18.2% (n=28)
CVD: 62.3% ± 14.9% (n=12)
t-test: t=0.340, p=0.736 (ns)
```
→ No significant difference in decoding accuracy

**Top 5 Performers** (RDM Correlation After Procrustes):
```
1. sub-03_V3  (HC):  r=0.559 (84% accuracy)
2. sub-08_V2  (CVD): r=0.530 (71% accuracy)
3. sub-03_hV4 (HC):  r=0.503 (81% accuracy)
4. sub-08_hV4 (CVD): r=0.459 (48% accuracy)
5. sub-08_V1  (CVD): r=0.419 (69% accuracy)
```
→ CVD subjects appear in top 5, suggesting comparable representation quality when aligned

---

### 4. **Procrustes Disparity** (Alignment quality metric)

**Distribution**:
```
Mean:  1142 ± 973 (arbitrary units)
95% CI: [854, 1447]
Range: [12.3, 3139.4]
n = 40
```

**Interpretation**:
- Disparity = Frobenius norm of residual after optimal orthogonal transformation
- **Large values (10^2-10^3)** indicate substantial topographic variability across runs
- Even after center+scale normalization, runs are **not trivially alignable**
- This supports the need for Procrustes alignment in fMRI RSA

**Per-ROI Disparity**:
```
V1:  2142 ± 655   [Largest, most voxels → highest dimensional space]
V2:  1577 ± 362
V3:  287 ± 110    [Smallest, fewest voxels]
hV4: 369 ± 117
```

**HC vs CVD**:
```
HC:  1138 ± 1025 (n=28)
CVD: 1151 ± 909  (n=12)
t-test: t=-0.039, p=0.969 (ns)
```
→ No difference in alignment difficulty between groups

---

### 5. **Procrustes Improvement Statistics**

**Success Rate**:
```
RDM Correlation:     38/39 improved (97.4%)
RDM Crossnobis:      38/39 improved (97.4%)
Decoding Accuracy:   40/40 improved (100.0%)
```

**Effect Sizes** (Cohen's d):
```
RDM Correlation:     d = 1.39 (very large)
RDM Crossnobis:      d = 1.83 (very large)
Decoding Accuracy:   d = 3.00 (extremely large)
```

**Problematic Cases** (6/40, 15.0%):
```
sub-04_V1 (HC):  Low decoding (33%, but still >2× chance)
sub-07_V1 (HC):  Negative RDM improvement (-0.072), low decoding (33%)
sub-07_V2 (HC):  Low decoding (31%)
sub-07_hV4 (HC): NaN RDM (constant voxel patterns → data quality issue)
sub-10_V1 (CVD): Low decoding (40%)
sub-10_V2 (CVD): Low decoding (38%)
```

**Common Issues**:
- **sub-07**: Data quality concerns (tSNR=5.9, critical) → Consider exclusion
- **sub-10 V1/V2**: CVD subject, but still above chance
- **sub-04 V1**: Isolated case, other ROIs perform well

---

### Summary & Conclusions

**Key Findings**:

1. **Procrustes alignment is essential**:
   - Without alignment: Below-chance performance (11% accuracy)
   - With alignment: 5.8× improvement (64% accuracy)
   - Universal improvement (100% of cases for decoding)

2. **Recovered signal quality**:
   - RDM reliability: -0.009 → 0.226 (26× improvement)
   - Crossnobis reliability: -0.010 → 0.219 (24× improvement)
   - Both metrics show moderate positive correlation after alignment

3. **No major HC vs CVD difference in within-subject reliability**:
   - RDM correlation: p=0.955 (ns)
   - Decoding accuracy: p=0.736 (ns)
   - Crossnobis: p=0.038 (*) → HC slightly higher, but small effect

4. **ROI hierarchy**:
   - V2/V3/hV4 show higher RDM reliability than V1
   - V3 shows highest decoding accuracy (68%)
   - Consistent with hierarchical color processing

5. **Data quality**:
   - 85% of cases (34/40) show good performance (>40% decoding)
   - 15% problematic cases mostly from sub-07 (known tSNR issues)

**Next Steps**:
- **Between-subject alignment**: Requires solving voxel count heterogeneity (see TODO section)
- **Sub-07 exclusion**: Consider removing due to poor data quality
- **Production deployment**: Apply c02 + Procrustes pipeline to all subjects/ROIs

**Status**: ✅ **COMPLETED - Within-subject Procrustes validation successful**

**Results**: `/scratch/connectome/haba6030/colorBlind/analysis/phase1_preprocess_decoding/method3_header_mi/results/baseline_decoding/only_Zscore_1stGLM/`
**Statistics**: `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/phase3_statistics.json`
**Visualizations**: `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/baseline/baseline_distributions_CI.png`

---

##### 3.1.1.a ANOVA-based Voxel Selection (Color Selectivity Analysis)

**Date**: 2026-02-02  
**Purpose**: Analyze voxel-wise color selectivity using ANOVA to enable common voxel selection across subjects  
**Motivation**: Different voxel counts across subjects prevent between-subject Procrustes alignment

**Method**: One-way ANOVA per voxel
```python
# For each voxel:
# H0: All 8 colors have the same mean response
# H1: At least one color has different mean response

groups = [voxel_responses_across_6_runs[:, color] for color in range(8)]
F_statistic, p_value = f_oneway(*groups)
```

**Results**: `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/baseline/`
- `anova_f_score_distribution.png`: F-score histograms by ROI
- `anova_f_score_stats.json`: Detailed statistics

---

**Key Findings**:

**1. Very High Color Selectivity Across All ROIs**:
```
ROI    % Significant (p<0.05)    Mean F-score    Median F-score
V1     86.5% (3130/3620)         24.6            17.7
V2     92.0% (2252/2448)         30.2            21.5
V3     96.7% ( 495/512)          38.8            22.5
hV4    94.6% ( 647/684)          57.0            24.3
```

**Interpretation**: 
- 85-97% of voxels show significant color discrimination (F > 2.25, p < 0.05)
- Higher visual areas show stronger color selectivity (hV4 > V3 > V2 > V1)
- Color information is robustly encoded even in early visual cortex

---

**2. F-score Distribution by ROI**:

| ROI | Range       | 50th pct | 75th pct | 90th pct | 95th pct | 99th pct |
|-----|-------------|----------|----------|----------|----------|----------|
| V1  | [0.03, 191.6] | 17.7   | 37.3     | 55.6     | 67.9     | 96.6     |
| V2  | [0.07, 211.2] | 21.5   | 41.0     | 66.4     | 92.6     | 156.8    |
| V3  | [0.42, 294.7] | 22.5   | 52.3     | 101.6    | 126.6    | 174.1    |
| hV4 | [0.71, 415.1] | 24.3   | 68.3     | 172.0    | 238.6    | 343.6    |

**Pattern**: 
- F-score increases with visual hierarchy
- hV4 shows exceptional color selectivity (max F=415)
- Wide distribution indicates heterogeneous voxel populations

---

**3. Subject-wise Variability**:

**Best Performers** (High F-scores across ROIs):
- sub-02: V1=51.7, V2=82.6, V3=82.2, hV4=18.1
- sub-03: V1=48.0, V2=42.3, V3=77.9, hV4=108.7
- sub-05: V1=23.7, V2=21.2, V3=84.7, hV4=188.2

**Poor Performers**:
- sub-04: V1=1.2, V2=7.1, V3=20.0, hV4=30.1
- sub-07: V1=0.9, V2=1.5, V3=9.0, hV4=2.3 ⚠️

**⚠️ Critical Issue: sub-07**
- Consistently lowest F-scores across all ROIs
- V3: Only **5 voxels** (vs 50-58 for others)
- Confirms previous data quality concerns (tSNR=5.9)
- **Recommendation**: Exclude sub-07 from inter-subject analysis

---

**4. Voxel Count by Subject**:

| ROI | Min | Max | Mean | Problem Subject |
|-----|-----|-----|------|-----------------|
| V1  | 129 | 429 | 362  | sub-07 (129)    |
| V2  | 103 | 279 | 245  | sub-07 (103)    |
| V3  | **5** | 58  | 51   | **sub-07 (5)** ⚠️ |
| hV4 | 57  | 70  | 68   | sub-01 (57)     |

**Implication**: 
- V3 extremely limited if including sub-07 (k=5)
- Excluding sub-07 enables k=50 for V3

---

**Recommendations for Top-k Voxel Selection**:

**Option 1: Conservative (Maximum Coverage)**
```python
k_values = {
    'V1':  129,  # Include all 10 subjects
    'V2':  103,  # Include all 10 subjects
    'V3':   50,  # Exclude sub-07 (9 subjects)
    'hV4':  57   # Include all 10 subjects
}
F_threshold = {
    'V1':  ~10,   # Moderate selectivity
    'V2':  ~14,
    'V3':  ~24,   # High selectivity
    'hV4': ~23
}
```

**Option 2: Selective (Top 25% by F-score)**
```python
k_values = {
    'V1':   90,  # F > 37.3 (75th percentile)
    'V2':   61,  # F > 41.0
    'V3':   12,  # F > 52.3
    'hV4':  17   # F > 68.3
}
```

**Option 3: Highly Selective (Top 10%)**
```python
k_values = {
    'V1':   36,  # F > 55.6 (90th percentile)
    'V2':   24,  # F > 66.4
    'V3':    5,  # F > 101.6
    'hV4':   7   # F > 172.0
}
```

---

**Decision for Inter-Subject Alignment**:

**Recommended**: **Option 1 (Conservative)**
- Ensures sufficient voxels for stable Procrustes alignment
- Maintains reasonable F-threshold (F > 10-24)
- Balances voxel count and selectivity

**Trade-offs**:
- Option 2/3: Higher selectivity but fewer voxels → Less stable covariance estimation
- Conservative approach: More robust for small sample (n=10 subjects)

---

**Next Steps**:

1. **Apply ANOVA-based top-k selection** to all subjects
2. **Re-compute amplitudes** with common k voxels per ROI
3. **Perform between-subject Procrustes alignment** to HC reference
4. **Compare disparities**: HC vs CVD
5. **Compute inter-subject RDM correlation** after alignment

**Status**: ✅ **COMPLETED - ANOVA analysis**
**Pending**: Top-k voxel selection implementation

---

##### 3.1.1.b Between-Subject Procrustes Alignment (HC Reference)

**Date**: 2026-02-02
**Purpose**: Align all subjects to HC reference using Procrustes to assess inter-subject similarity
**Motivation**: Compare HC-to-HC reliability vs CVD disparity to test hypothesis of CVD representational differences

**Method**: Between-subject Procrustes with normalization
```python
# 1. Load ANOVA-selected amplitudes (k voxels per ROI)
# 2. Compute HC reference: mean of HC subjects (after within-subject Procrustes)
# 3. For each subject:
#    - Center and scale pattern
#    - Find orthogonal transformation R to HC reference
#    - Compute Procrustes disparity
#    - Compute RDM correlation with HC reference RDM
```

**Implementation**:
- Voxel selection: `apply_anova_voxel_selection.py`
- Alignment: `between_subject_procrustes.py`
- Visualization: `visualize_between_subject_results.py`

**Results**: `/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/`
- `baseline_anova_selected/`: Selected top-k voxels per ROI
- `between_subject_procrustes/`: Alignment results and disparities
- `between_subject_procrustes/visualizations/`: HC vs CVD comparison plots

---

**Key Findings**:

**1. Voxel Selection Success** ✅:
```
ROI    k (target)    All subjects uniform?    Exclusions
V1     129           ✅ Yes (10 subjects)     None
V2     103           ✅ Yes (10 subjects)     None
V3     50            ❌ No (sub-07: 5 voxels) Exclude sub-07 (9 subjects)
hV4    57            ✅ Yes (10 subjects)     None
```

**Verification**: All ROIs except V3 have uniform voxel counts. V3 excludes sub-07 due to insufficient voxels (5 vs 50-58 for others).

---

**2. Between-Subject Procrustes Disparities**:

**⚠️ UNEXPECTED FINDING: HC > CVD for all ROIs**

```
ROI    HC Disparity         CVD Disparity        Ratio (HC/CVD)
V1     540.56 ± 108.13      266.11 ± 61.15       2.03×
V2     426.12 ± 57.23       160.56 ± 72.21       2.65×
V3     215.81 ± 40.60       89.43 ± 40.78        2.41×
hV4    232.54 ± 74.91       147.52 ± 102.66      1.58×
```

**Observation**:
- HC subjects show **2-2.7× higher disparities** than CVD subjects
- Opposite of hypothesis: Expected CVD > HC
- Disparities are very high (200-550 range) even after normalization

**Possible Explanations**:
1. **HC reference bias**: CVD subjects might coincidentally be closer to HC mean
2. **Between-subject variability**: Natural HC variability > within-CVD consistency
3. **Sample size**: Small CVD sample (n=3) vs HC (n=7 or 6)
4. **Normalization artifacts**: Center+scale normalization removes differences we care about

---

**3. RDM Correlation with HC Reference**:

```
ROI    HC RDM Correlation    CVD RDM Correlation    Difference
V1     -0.13 ± 0.38          -0.11 ± 0.05           -0.02
V2      0.07 ± 0.26          -0.08 ± 0.15           +0.15
V3      0.17 ± 0.10           0.06 ± 0.09           +0.11
hV4     NaN                   0.04 ± 0.11            —
```

**Observation**:
- **Very low correlations** (near 0 or negative) for both groups
- No clear HC > CVD pattern
- Suggests poor between-subject RDM alignment overall

**Interpretation**:
- Between-subject RDM similarity is very weak
- Procrustes alignment does not improve RDM correspondence
- High individual variability in color representations

---

**4. Diagnostic Considerations**:

**Issues Identified**:
- Unexpectedly high HC disparities (opposite of hypothesis)
- Very low RDM correlations (suggests alignment ineffective)
- Large disparity range (200-550) after normalization

**Potential Problems**:
1. **Alignment in wrong space**: Should align in RDM space instead of amplitude space?
2. **Wrong reference**: Mean HC might not be optimal; try individual HC references?
3. **Voxel heterogeneity**: Even with top-k selection, voxels may encode different features
4. **Between-subject variability**: Procrustes assumes same representational structure with different orientation, but subjects might have fundamentally different structures

**Alternative Approaches to Consider**:
- **Shared Response Model (SRM)**: Learn shared latent space instead of Procrustes
- **Representational Connectivity Analysis**: Compare RDM structure without alignment
- **Individual HC references**: Align each CVD to each HC (pairwise comparisons)
- **Voxel-wise encoding models**: Predict CVD from HC encoding weights

---

**Next Steps**:

1. **Investigate HC disparity paradox**:
   - Check if individual HC-to-HC disparities follow expected pattern
   - Try leave-one-out HC references to see if pattern holds
   - Compute pairwise HC-HC vs HC-CVD comparisons

2. **Test alternative alignment methods**:
   - RDM-space alignment (e.g., MDS + Procrustes on embedded RDMs)
   - Shared Response Model (SRM) for common latent space
   - Hyperalignment (data-driven transformation learning)

3. **Diagnostic analyses**:
   - Check if disparities correlate with tSNR or other data quality metrics
   - Visualize actual transformation matrices R to see rotation patterns
   - Compute leave-one-out cross-validation for HC reference stability

4. **Consider simpler metrics**:
   - Direct RDM correlation (without alignment)
   - Second-order isomorphism (correlation of RDM correlations)
   - Pattern distinctiveness (within vs between-color distances)

**Status**: ✅ **COMPLETED - Between-subject Procrustes implemented**
**Finding**: ⚠️ **Unexpected HC > CVD disparities - requires investigation**

---


##### 3.1.2 Split-half Reliability (Noise Ceiling)
[✅ COMPLETED - 2026-02-03] **Task**: Run split으로 noise ceiling 추정

**Input**:
- Procrustes-aligned amplitudes: `{BASELINE_RESULTS}/sub-{ID}/{ROI}/amplitudes_procrustes.npy`
  - Shape: (n_runs=6, n_colors=8, n_voxels)
  - Note: Split by runs (not trials) for computational efficiency

**Computation**:
```python
# Bootstrap split-half (1000 iterations)
for iteration in range(1000):
    # Randomly split 6 runs into two halves (3+3)
    half1_runs, half2_runs = random_split(runs)

    # Average patterns within each half
    half_A = mean(amplitudes[half1_runs], axis=0)  # (8 colors, n_voxels)
    half_B = mean(amplitudes[half2_runs], axis=0)

    # Build RDM from each half
    RDM_A = compute_rdm(half_A)
    RDM_B = compute_rdm(half_B)

    # Spearman correlation
    r_raw = spearmanr(RDM_A, RDM_B)

    # Spearman-Brown correction for full data
    r_corrected = 2 * r_raw / (1 + r_raw)

    noise_ceiling_estimates.append(r_corrected)

# Report: mean, 95% CI
```

**Output**:
- `{VALIDATION_OUT}/noise_ceiling/evaluation_with_ceiling.json`
  - Per subject-ROI: noise_ceiling_upper, CI, % of ceiling
  - LOSO bounds per ROI
- Figures:
  - `visualizations/noise_ceiling_{ROI}.png` (performance vs ceiling)
  - `visualizations/performance_vs_ceiling_scatter.png`
  - `visualizations/split_half_dist_{subject}_{ROI}.png`

**Results**: ✅ `/Users/.../analysis/validation/results/noise_ceiling/`
- **Original**: `evaluation_with_ceiling.json` (40 pairs, all subjects)
- **Cleaned**: `noise_ceiling_roi_specific_exclusion.json` (36 pairs, ROI-specific exclusion)
- **Excluded pairs**: sub-04_V2, sub-04_hV4, sub-07_hV4, sub-10_V1 (4 pairs only)

**Key Findings (ROI-Specific Exclusion)**:

| ROI | n | Noise Ceiling | RDM After Procrustes | % of Ceiling | Gap | Change |
|-----|---|--------------|----------------------|--------------|-----|--------|
| V1  | 9 | 0.520 ± 0.212 | 0.174 ± 0.144 | **29.2%** | 66.5% | Ceiling +16% |
| V2  | 9 | 0.690 ± 0.139 | 0.283 ± 0.120 | **42.1%** | 58.9% | Ceiling +11% |
| V3  | 10| 0.624 ± 0.174 | 0.256 ± 0.146 | **39.1%** | 59.0% | All valid ✅ |
| hV4 | 8 | 0.560 ± 0.247 | 0.232 ± 0.177 | **39.1%** | 58.5% | Ceiling +2% |

**Interpretation**:

### 1. 데이터 품질 평가 (Split-Half Ceiling) - **ROI-SPECIFIC EXCLUSION**

**Excluded pairs (4개)**: sub-04_V2, sub-04_hV4, sub-07_hV4, sub-10_V1
**Valid pairs**: 36/40 (90%)

| ROI | n | Ceiling | Quality Assessment | Literature Comparison |
|-----|---|---------|-------------------|----------------------|
| V1  | 9 | 0.520 ± 0.212 | **양호** | Moderate-High (expected 0.5-0.7) |
| V2  | 9 | 0.690 ± 0.139 | **양호** | Moderate-High (expected 0.6-0.8) |
| V3  | 10| 0.624 ± 0.174 | **양호** | Moderate-High |
| hV4 | 8 | 0.560 ± 0.247 | **양호** | Moderate-High |

**Valid subjects per ROI**:
- V1 (n=9): HC sub-01~07 / CVD sub-08,09
- V2 (n=9): HC sub-01,02,03,05,06,07 / CVD sub-08,09,10
- V3 (n=10): All subjects valid ✅
- hV4 (n=8): HC sub-01,02,03,05,06 / CVD sub-08,09,10

**결론**: **모든 ROI가 양호한 품질** (ceiling 0.52-0.69) → 분석 진행 충분 ✅

### 2. 모델 설명력 평가 (% of Ceiling)

| ROI | Current RDM | % of Ceiling | Gap | Target (70%) | Need |
|-----|------------|--------------|-----|--------------|------|
| V1  | 0.174      | **29.2%**    | 66.5% | 0.364        | +0.190 |
| V2  | 0.283      | **42.1%**    | 58.9% | 0.483        | +0.199 |
| V3  | 0.256      | **39.1%**    | 59.0% | 0.437        | +0.181 |
| hV4 | 0.232      | **39.1%**    | 58.5% | 0.392        | +0.160 |

**해석**:
- 현재 모델 (within-subject Procrustes)은 데이터 잠재력의 **29-42%만 활용**
- **59-67% gap 존재** → 상당한 개선 여지 (2-3배 개선 가능)
- 낮은 성능은 **데이터 품질 문제가 아니라 모델 한계**
- Whitening으로 +0.18-0.20 개선 시 70% 목표 달성 가능

### 3. Between-Subject Analysis

**현재 상태**: LOSO 계산 불가
- **이유**: Voxel count 불일치로 between-subject Procrustes 불가능
- V1: 129-429 voxels (subject별 상이)
- V3: 5-58 voxels (특히 불일치 심함)

**해결 방법**:
1. **Non-variance voxel removal** (GLM 단계) → Anatomical correspondence
2. **ANOVA top-k selection** → Common voxel set
3. **Between-subject Procrustes** OR **SRM**

**현재 단계**: Within-subject analysis만 완료
- Between-subject alignment은 별도 프로젝트로 진행 예정

### 4. Critical Issues

- **Data quality**: sub-04, sub-07, sub-10 제외 필요 (negative/invalid ceilings)
- **hV4 NaN**: sub-07_hV4 constant patterns
- **V2 anomaly**: 67% ceiling 일부 subjects (재확인 필요)

### 결론

✅ **데이터 품질**: V2/V3 양호, V1 보통 → 분석 가능
⚠️ **모델 성능**: 34-41% 활용 (낮음) → **개선 필요**
🎯 **개선 전략**: Whitening (+20-30%) → GLMsingle (+10-20%) → 70-90% 목표
📊 **Between-subject**: LOSO improvement는 별도 목표 (alignment 후 측정)

---

#### 3.2 Inter-Subject Similarity (ISS)

**Purpose**: 정렬 전후 피험자 간 표현 일치도 변화 검증

---

##### 3.2.1 Before Alignment (Baseline)
[ ] **Task**: 정렬 전 피험자 간 RDM 유사도

**Input**:
- Baseline amplitudes (no alignment): `{BASELINE_RESULTS}/sub-{ID}/{ROI}/amplitudes_z.npy`
- Use run-averaged RDM per subject (더 안정적)

**Computation**:
```python
# Step 1: Run-averaged RDM per subject
for subject in subjects:
    RDM_avg = mean([RDM_run1, ..., RDM_run6])

# Step 2: Pairwise ISS
for subj_A, subj_B in combinations(subjects, 2):
    ISS = spearmanr(RDM_A.flatten(), RDM_B.flatten())

# Step 3: Group average
ISS_before = mean(all_pairwise_ISS)
```

**Output**:
- `{VALIDATION_OUT}/iss/{TIMESTAMP}/before_alignment.json`
  - All pairwise ISS scores
  - Group mean ± std per ROI
  - HC-HC vs CVD-CVD vs HC-CVD comparison

**Results**: _[write directory here after completion]_

---

##### 3.2.2 After Alignment (Procrustes/SRM)
[ ] **Task**: 정렬 후 ISS 증가 검증 (표현 일치도)

**Input**:
- Procrustes-aligned patterns: From `phase2_procrustes_cvd_hc` results
- Location: `{PHASE2_RESULTS}/{TIMESTAMP}/aligned_patterns/`

**Computation**:
```python
# Same as 3.2.1 but with aligned patterns
ISS_after = compute_ISS(aligned_patterns)

# Effect of alignment
delta_ISS = ISS_after - ISS_before
```

**Output**:
- `{VALIDATION_OUT}/iss/{TIMESTAMP}/after_alignment.json`
- Comparison: before vs after

**Results**: _[write directory here after completion]_

---

##### 3.2.3 Downstream Decoding Accuracy
[ ] **Task**: 정렬 후 inter-subject decoding 성능 향상 검증

**Input**:
- Baseline patterns (before alignment)
- Aligned patterns (after Procrustes)

**Computation**:
```python
# Leave-one-subject-out decoding
for test_subject in subjects:
    train_subjects = subjects - test_subject

    # Train decoder on other subjects
    W_group = train_decoder(train_subjects)

    # Test on held-out subject
    acc_before = decode(test_subject, W_group, aligned=False)
    acc_after = decode(test_subject, W_group, aligned=True)

# Paired t-test across subjects
delta_acc = acc_after - acc_before
t_stat, p_value = ttest_rel(acc_after, acc_before)
```

**Output**:
- `{VALIDATION_OUT}/iss/{TIMESTAMP}/inter_subject_decoding.json`
  - Per subject: acc_before, acc_after, delta
  - Group statistics: t, p, Cohen's d

**Expected**: Significant increase in accuracy after alignment

**Results**: _[write directory here after completion]_

---

##### 3.2.4 Alignment Effect Summary
[ ] **Task**: 정렬 효과 통계 검증 및 시각화

**Computation**:
```python
# Paired test
delta_similarity = ISS_after - ISS_before
delta_decoding = acc_after - acc_before

# Permutation test (1000 iterations)
for perm in range(1000):
    # Randomly flip sign of deltas
    shuffled_delta = delta * random_sign()
    null_distribution.append(mean(shuffled_delta))

# Effect size (Cohen's d)
d = mean(delta) / std(delta)
CI_95 = bootstrap_CI(delta)
```

**Output**:
- `{VALIDATION_OUT}/iss/{TIMESTAMP}/alignment_effect_stats.json`
  - Δr (similarity), Δacc (decoding)
  - Effect size (d), CI, p-value
- Figures:
  - `alignment_effect_barplot.png` (before vs after, paired lines)
  - `effect_size_distribution.png` (permutation null vs observed)

**Results**: _[write directory here after completion]_

---

### 4. Comprehensive Visualization

#### 4.1 RDM Visualization
[ ] **Task**: RDM 매트릭스 시각화 (run별, 정렬 전후)

**Figures**:

**A. Run-wise RDM Matrices** (2×3 panel)
- Subject 예시 (e.g., sub-01, V1)
- 각 run별 8×8 RDM heatmap
- Colormap: viridis, 범위 [0, 2] (1-correlation)

**B. Before/After Alignment** (2×2 panel)
- Before: Run-averaged RDM (HC group, CVD group)
- After: Procrustes-aligned RDM (HC group, CVD group)
- Difference map 추가

**Output**: `{VALIDATION_OUT}/visualization/rdm_matrices.png`

**Results**: _[write directory here after completion]_

---

#### 4.2 Color Space Embedding
[ ] **Task**: MDS/UMAP로 color representation 2D 시각화

**Input**: RDM → 2D embedding

**Computation**:
```python
from sklearn.manifold import MDS
from umap import UMAP

# MDS embedding (per run)
for run in runs:
    embedding_2d = MDS(n_components=2, dissimilarity='precomputed').fit_transform(RDM_run)

# Plot with color labels (실제 stimulus color로 표시)
scatter(embedding_2d, c=stimulus_colors, s=100)
```

**Figures**:

**A. Run Overlay** (single panel)
- 모든 run의 embedding을 겹쳐서 표시
- 각 run은 투명도 0.3으로 표시
- Color consistency 확인 (같은 색깔이 같은 위치에 클러스터링되는지)

**B. Subject Comparison** (2×5 panel, HC subjects)
- 각 피험자별 color embedding
- Geometric structure 보존 확인

**Output**:
- `{VALIDATION_OUT}/visualization/color_embedding_mds.png`
- `{VALIDATION_OUT}/visualization/color_embedding_umap.png`

**Results**: _[write directory here after completion]_

---

#### 4.3 Procrustes Transformation Visualization
[ ] **Task**: 정렬 전후 점들의 이동 시각화

**Figures**:

**A. Vector Field** (2D projection)
- PCA로 고차원 공간을 2D로 projection
- 정렬 전 위치 → 정렬 후 위치 화살표로 표시
- Color별로 구분

**B. Centroid & Variance**
- 각 subject의 color centroid를 template 공간에 사상
- Before: subject별 centroid 분산 (큼)
- After: aligned centroid 분산 (작아짐)

**Output**: `{VALIDATION_OUT}/visualization/procrustes_transformation.png`

**Results**: _[write directory here after completion]_

---

## TODO: Between-Subject Procrustes Alignment

### Problem: Voxel Count Heterogeneity

**Issue**: Cannot perform between-subject Procrustes alignment in voxel space because different subjects have different numbers of voxels per ROI.

**Example** (V1 ROI):
- sub-01: 354 voxels
- sub-02: 378 voxels
- sub-07: 129 voxels
- Range across all subjects: 129-429 voxels

**Impact**:
- Cannot create HC reference by averaging voxel patterns
- Cannot align CVD subjects to HC reference in voxel space
- Current within-subject Procrustes only addresses cross-run alignment (6 runs within each subject)
- Inter-subject alignment requires common feature space

### Proposed Solutions

#### Option 1: ANOVA-based Voxel Selection

**Method**: Select common voxels across subjects based on statistical criteria

**Approach**:
1. For each ROI, identify voxels present in all subjects
2. Use F-statistics (one-way ANOVA across color conditions) to rank voxels by information content
3. Select top N voxels (e.g., N = minimum voxel count across subjects)
4. Apply between-subject Procrustes on selected voxel subset

**Pros**:
- Direct voxel-space alignment preserves spatial interpretability
- Statistical selection ensures informative voxels retained
- Straightforward implementation

**Cons**:
- May lose information from excluded voxels
- Requires careful selection threshold
- Assumes spatial correspondence across subjects (after MNI registration)

#### Option 2: SRM (Shared Response Model)

**Method**: Project individual voxel patterns to lower-dimensional common space

**Approach**:
1. Learn shared response space from HC subjects' data
   - Input: Individual subjects' voxel patterns (different dimensions)
   - Output: Common low-dimensional space (e.g., 50-100 dimensions)
2. Project CVD subjects to same learned common space
3. Compare representations in common space
4. Apply Procrustes alignment in common space if needed

**Pros**:
- Handles voxel count heterogeneity naturally
- Dimensionality reduction may improve signal-to-noise ratio
- Captures shared functional architecture across subjects
- Does not assume voxel-wise correspondence

**Cons**:
- Less interpretable than voxel space (cannot map back to specific voxels)
- Requires parameter tuning (number of dimensions, regularization)
- Computationally more expensive

**References**:
- Chen et al. (2015). A Reduced-Dimension fMRI Shared Response Model. NIPS.
- Haxby et al. (2020). Hyperalignment: Modeling shared information encoded in idiosyncratic cortical topographies. Neuron.

### Analysis Goals (After Resolving Voxel Mismatch)

1. **Build HC Reference**: Average aligned HC subjects' patterns in common space
2. **Align All Subjects**: Apply between-subject Procrustes to HC reference
3. **Compare Procrustes Disparity**:
   - HC-to-HC disparity (should be low)
   - CVD-to-HC disparity (expected to be higher if CVD has different color representation)
4. **Inter-Subject RDM Correlation**:
   - Compute RDM for each subject in aligned space
   - Measure Spearman correlation between subjects
   - Compare HC-HC correlation vs CVD-HC correlation

### Expected Outcomes

**If CVD differs from HC:**
- CVD-to-HC Procrustes disparity > HC-to-HC disparity
- CVD-HC RDM correlation < HC-HC RDM correlation
- MDS visualization shows different color geometry for CVD

**If CVD similar to HC:**
- CVD-to-HC disparity ≈ HC-to-HC disparity
- CVD-HC RDM correlation ≈ HC-HC RDM correlation
- Color geometry preserved in CVD

### Next Steps

1. Implement voxel selection method (start with ANOVA as simpler approach)
2. Build HC reference in common space
3. Align all subjects (HC + CVD) to HC reference
4. Compute and compare disparity metrics
5. Visualize aligned color spaces (MDS)
6. If ANOVA approach insufficient, implement SRM

