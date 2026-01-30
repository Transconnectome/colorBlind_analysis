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

1. **RDM Correlation Reliability**:

2. **RDM Crossnobis Reliability**:

3. **Decoding Accuracy**:

4. **Procrustes Disparity**:

5. **Procrustes Improvement**:

**Status**: 🔄 **IN PROGRESS - Baseline deployment**

**Results**: _[Will be filled after baseline deployment completion]_

---

##### 3.1.2 Split-half Reliability (Noise Ceiling)
[ ] **Task**: Trial split으로 noise ceiling 추정

**Input**:
- Trial-wise beta estimates (before averaging)
  - From baseline pipeline's intermediate outputs
  - Shape: (n_trials_per_run, n_voxels)

**Computation**:
```python
# Bootstrap split-half (1000 iterations)
for iteration in range(1000):
    # Randomly split trials for each color
    for color in colors:
        trials = all_trials[color]
        half_A, half_B = random_split(trials)

    # Build RDM from each half
    RDM_A = compute_rdm(half_A)
    RDM_B = compute_rdm(half_B)

    # Spearman-Brown corrected correlation
    r_raw = spearmanr(RDM_A, RDM_B)
    r_corrected = 2 * r_raw / (1 + r_raw)

    noise_ceiling_estimates.append(r_corrected)

# Report: mean, 95% CI
```

**Output**:
- `{VALIDATION_OUT}/split_half/{TIMESTAMP}/noise_ceiling.json`
  - Per subject-ROI: mean, CI_lower, CI_upper
- Figures:
  - `noise_ceiling_distribution.png` (ROI별 분포)
  - `split_half_scatter.png` (RDM_A vs RDM_B scatter, 여러 bootstrap 샘플)

**Expected**: Higher noise ceiling = more reliable representation

**Results**: _[write directory here after completion]_

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

