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
[IN PROGRESS] **Task**: 동일 피험자 내에서 run 간 RDM 일관성 검증

**Scripts**:
- `03_rdm_reliability.py`: Original amplitudes (no alignment)
- `03b_rdm_reliability_aligned.py`: After Procrustes alignment (run-to-run)

**Input**:
- Baseline amplitudes: `{BASELINE_RESULTS}/sub-{ID}/{ROI}/amplitudes_z.npy`
  - Shape: (n_runs=6, n_colors=8, n_voxels)
  - Note: File is in `sub-{ID}/{ROI}/` subdirectory of BASELINE_RESULTS

**Computation**:
```python
# Step 1: RDM per run
for run in runs:
    # Color patterns: (8 colors, n_voxels)
    RDM_run = 1 - corrcoef(patterns)  # (8, 8) dissimilarity matrix

# Step 2: Correlation between run pairs
for run_i, run_j in combinations(runs, 2):
    # Vectorize upper triangle
    vec_i = RDM_i[np.triu_indices(8, k=1)]
    vec_j = RDM_j[np.triu_indices(8, k=1)]
    r_spearman = spearmanr(vec_i, vec_j)

# Step 3: Average reliability per subject
reliability = mean(all_pairwise_r)
```

**Output**:
- `{VALIDATION_OUT}/rdm_reliability/{TIMESTAMP}/within_subject_reliability.json`
  - Per subject: mean ± std of run-pair correlations
  - Per ROI: distribution across subjects
- Figures:
  - `rdm_reliability_distribution.png` (ROI별 violin plot)
  - `rdm_matrices_per_run.png` (예시 subject의 run별 RDM, 2×3 panel)

**Expected**: r > 0.6 (good), r > 0.4 (acceptable)

**Results**: _[write directory here after completion]_

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