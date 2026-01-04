# Group-Level Analysis Pipeline 비교 및 설명

## 목차
1. [Pipeline 비교 요약](#pipeline-비교-요약)
2. [Original Pipeline 상세](#original-pipeline-상세)
3. [Comprehensive Pipeline 상세](#comprehensive-pipeline-상세)
4. [측정 지표 설명](#측정-지표-설명)
5. [언제 어떤 Pipeline을 사용할까?](#언제-어떤-pipeline을-사용할까)
6. [전체 Workflow](#전체-workflow)

---

## Pipeline 비교 요약

### Original Pipeline (`run_group_level_analysis.sbatch`)
**목적**: 전통적인 feature selection 방법으로 group-level 분석 수행

**단계**:
1. Common voxel identification (SNR-based top-K selection)
2. **PCA analysis** (차원 축소)
3. **ANOVA feature selection** (F-statistic 기반)

**특징**:
- ✅ 전통적인 통계 방법
- ✅ Feature selection 방법 비교 (PCA vs ANOVA)
- ✅ 다양한 K 값 테스트 (50, 100, 200 features)
- ❌ 색상 간 구별 능력 분석 없음
- ❌ 적록색맹 연구에 특화되지 않음

---

### Comprehensive Pipeline (`run_group_level_comprehensive.sbatch`)
**목적**: 색상 변별 능력에 초점을 맞춘 심층 분석 (적록색맹 연구 특화)

**단계**:
1. Common voxel identification (SNR-based top-K selection)
2. **Three statistical tests** (vs 0, selectivity, pairwise)
3. **Union voxel approach** (세 가지 테스트 결과 합집합)
4. **Classification & Reconstruction** on union voxels
5. **PCA analysis** on union voxels (NEW!)

**특징**:
- ✅ 색상 쌍별 변별 능력 분석 (**28 pairwise contrasts**)
- ✅ 적록색맹 연구에 특화
- ✅ Union voxel 접근법 (여러 통계 테스트 통합)
- ✅ T-value threshold 옵션 (N=6일 때 더 적합)
- ✅ 종합적인 시각화 (pairwise grid, union breakdown)
- ✅ PCA 포함 (union voxel 기반)

---

## Original Pipeline 상세

### Step 1: Common Voxel Identification
**스크립트**: `group_level_common_voxels.py`

**입력**:
- 각 피험자의 amplitudes (z-scored beta values)
- Voxel quality metric (SNR or R²)

**처리**:
1. 피험자마다 voxel 수가 다를 수 있음 → SNR 기반 top-K selection
2. K = min(각 피험자의 voxel 수)
3. 각 피험자에서 SNR이 높은 K개 voxel 선택
4. 모든 피험자의 데이터를 통합 → `group_amplitudes_z.npy`

**출력**:
```
derivatives/group_level/{timestamp}/{roi}/common_voxels/
├── group_amplitudes_z.npy        # (N_subjects, N_runs, N_colors, K_voxels)
└── preprocessing_info.json
```

**차원**:
- N_subjects = 6 (sub-01, 02, 03, 05, 06, 07)
- N_runs = 6
- N_colors = 8
- K_voxels = 피험자 간 최소 voxel 수

---

### Step 2: PCA Analysis
**스크립트**: `group_level_pca_analysis.py`

**목적**: 차원 축소를 통한 feature extraction

**방법**:
1. **PCA fitting**: 모든 데이터에 대해 PCA 수행
   ```python
   X_all = (N_subjects × N_runs × N_colors, K_voxels)
   pca.fit(X_all)  # n_components=50 (default)
   ```

2. **Leave-One-Subject-Out CV**:
   - Training: N-1명의 피험자
   - Test: 1명의 피험자
   - Train data에 PCA fitting → Test data transform
   - Classification accuracy 측정

3. **High-loading voxel 시각화**:
   - 각 PC에서 loading이 높은 top-100 voxels
   - Brain 공간에 시각화 (MNI coordinates)

**출력**:
```
derivatives/group_level/{timestamp}/{roi}/pca/
├── pca_model.pkl                     # Fitted PCA model
├── pca_loadings.npy                  # (K_voxels, n_components)
├── high_loading_voxels.npz           # Top voxels per PC
├── group_performance.csv             # Overall metrics
├── per_subject_performance.csv       # Subject-level metrics
└── figures/
    ├── pca_loadings_heatmap.png      # Loadings visualization
    ├── high_loading_voxels_PC1.png   # Brain map for PC1
    ├── high_loading_voxels_PC2.png   # etc.
    ├── explained_variance.png
    ├── classification_performance.png
    └── reconstruction_performance.png
```

**측정 지표**:
- **Explained variance**: 각 PC가 설명하는 분산 비율
- **Cumulative variance**: 누적 설명 분산
- **Classification accuracy**: PCA features로 색상 분류 정확도
- **Reconstruction error**: 색상 복원 오차 (degrees)

---

### Step 3: ANOVA Feature Selection
**스크립트**: `group_level_anova_selection.py`

**목적**: F-statistic 기반 feature selection

**방법**:
1. **ANOVA F-test**:
   - 각 voxel에 대해 8가지 색상 간 차이 검정
   - F-statistic 계산: Between-group variance / Within-group variance

2. **Top-K selection**:
   - F-value가 높은 K개 voxel 선택
   - K = [50, 100, 200] (기본값)

3. **Leave-One-Subject-Out CV**:
   - Train data에서 ANOVA 수행 → Top-K 선택
   - Test data에서 선택된 voxels만 사용
   - Classification & Reconstruction

**출력**:
```
derivatives/group_level/{timestamp}/{roi}/anova/
├── anova_f_values.npy                # F-statistics for all voxels
├── selected_voxels_k50.npz           # Top-50 voxels
├── selected_voxels_k100.npz
├── selected_voxels_k200.npz
├── performance_comparison.csv        # K별 성능 비교
└── figures/
    ├── anova_f_values_distribution.png
    ├── performance_vs_k.png
    └── reconstruction_vs_k.png
```

**측정 지표**:
- **F-statistic**: 색상 간 차이의 통계적 유의성
- **Classification accuracy** (K별)
- **Reconstruction error** (K별)
- **Optimal K**: 성능이 가장 좋은 feature 수

---

## Comprehensive Pipeline 상세

### Step 1: Common Voxel Identification
(Original pipeline과 동일)

---

### Step 2: Three Statistical Tests
**스크립트**: `group_level_analysis_comprehensive.py`

#### 2-1. Three Types of Statistical Tests

##### **Option A: One-sample t-test vs 0**
**목적**: Voxel이 색상에 반응하는가?

**검정**:
```python
# 각 색상에 대해
H0: mean(amplitude) = 0
H1: mean(amplitude) ≠ 0

t-statistic, p-value = ttest_1samp(amplitudes[:, color, voxel], 0)
```

**결과**:
- t_values: (N_colors=8, N_voxels)
- p_values: (N_colors=8, N_voxels)
- significant_mask: FDR-corrected 또는 |t| > threshold

**의미**:
- 각 voxel이 어떤 색상에 대해 유의미한 반응을 보이는가?
- Baseline activation detection

---

##### **Option B-1: Color Selectivity**
**목적**: Voxel이 특정 색상을 선호하는가?

**검정**:
```python
# 각 색상에 대해
this_color = amplitudes[:, color, voxel]
other_colors = mean(amplitudes[:, other_7_colors, voxel])

H0: this_color = other_colors
H1: this_color ≠ other_colors

t-statistic, p-value = ttest_rel(this_color, other_colors)
```

**결과**:
- t_values: (N_colors=8, N_voxels)
- significant_mask: 각 voxel이 어떤 색상에 selective한가?

**의미**:
- Color tuning detection
- 특정 색상에 선호도가 있는 voxel 식별

---

##### **Option B-2: Pairwise Color Contrasts** ⭐ **적록색맹 핵심**
**목적**: Voxel이 두 색상을 구별할 수 있는가?

**검정**:
```python
# 모든 색상 쌍 조합 C(8,2) = 28 pairs
for color1, color2 in all_pairs:
    H0: amplitude(color1) = amplitude(color2)
    H1: amplitude(color1) ≠ amplitude(color2)

    t-statistic, p-value = ttest_rel(
        amplitudes[:, color1, voxel],
        amplitudes[:, color2, voxel]
    )
```

**28 Pairwise Contrasts**:
```
C1 vs C2, C1 vs C3, ..., C1 vs C8  (7 pairs)
C2 vs C3, C2 vs C4, ..., C2 vs C8  (6 pairs)
...
C7 vs C8                           (1 pair)
Total: 7+6+5+4+3+2+1 = 28 pairs
```

**결과**:
- 28개의 contrast, 각각:
  - t_values: (N_voxels,)
  - significant_mask: (N_voxels,)

**의미**:
- **적록색맹 연구의 핵심**
- 어떤 색상 쌍을 구별할 수 있는 voxel인가?
- 예: Red vs Green을 구별 못하면 적록색맹 관련

---

#### 2-2. Voxel Selection Methods

##### **Method 1: FDR Correction** (기본값, N≥10일 때)
```python
reject, p_corrected = multipletests(p_values, alpha=0.05, method='fdr_bh')
significant_mask = reject
```

**장점**:
- False Discovery Rate 통제
- 다중 비교 보정

**단점**:
- N이 작으면 (N<10) power 부족
- 너무 보수적일 수 있음

---

##### **Method 2: T-value Threshold** (N=6일 때 권장)
```python
significant_mask = (|t_values| > threshold)  # default: 5.0
```

**장점**:
- 작은 N에서도 충분한 power
- t > 5.0은 매우 높은 threshold (df=5, p<0.004)

**단점**:
- Multiple comparison correction 없음
- Threshold 선택이 arbitrary

**사용 예**:
```bash
--use-t-threshold \
--t-threshold 5.0
```

---

#### 2-3. Union Voxel Approach

**개념**:
세 가지 통계 테스트에서 유의미한 voxel들의 **합집합** 사용

```python
mask_A = significant in Option A (any color)
mask_B1 = significant in Option B-1 (any color selective)
mask_B2 = significant in Option B-2 (any pair discriminable)

union_mask = mask_A | mask_B1 | mask_B2
```

**이유**:
- 각 테스트는 다른 측면을 포착
- Option A: Activation
- Option B-1: Selectivity
- Option B-2: Discrimination
- Union: 세 가지 중 하나라도 유의미하면 포함

**Breakdown 분석**:
- A only: A에서만 유의미
- B-1 only: B-1에서만 유의미
- B-2 only: B-2에서만 유의미
- A ∩ B-1: 두 테스트 모두 유의미
- All three: 세 테스트 모두 유의미

---

### Step 3: Classification & Reconstruction on Union Voxels

**입력**: Union mask로 선택된 voxels

**방법**: Leave-One-Subject-Out CV

```python
for test_subject in subjects:
    # Train on N-1 subjects
    X_train = union_voxels[other_subjects]
    y_train = color_labels

    # Test on 1 subject
    X_test = union_voxels[test_subject]
    y_test = color_labels

    # Classification (Diagonal Linear Discriminant)
    y_pred = diag_linear_predict(X_train, y_train, X_test)
    acc = accuracy(y_pred, y_test)

    # Reconstruction (Brouwer & Heeger 2009)
    reconstructed_hues, errors = forward_encoding_model(X_test)
```

**측정 지표**:
- **Classification accuracy**: 8-way color classification
- **Reconstruction error**: Circular distance (degrees)
- **Hit rates**: % within ±22.5° and ±45°

---

### Step 4: PCA Analysis on Union Voxels

**목적**: Union voxels의 차원 축소 및 성능 비교

**방법**:
1. Union voxels에 대해 PCA fitting (n_components=50)
2. LOSO-CV로 PCA features 평가
3. Full union voxels vs PCA features 비교

**출력**:
```
comprehensive/pca/
├── pca_results.npz
└── figures/
    ├── pca_explained_variance.png
    ├── pca_loadings_heatmap.png
    └── pca_classification_performance.png
```

---

## 측정 지표 설명

### 1. Classification Metrics

#### Classification Accuracy
**정의**: 8가지 색상을 정확히 분류한 비율

```
Accuracy = (Correctly classified trials) / (Total trials)
```

**해석**:
- Chance level = 12.5% (1/8)
- 50% 이상: 유의미한 색상 정보 포함
- 70% 이상: 매우 좋은 성능
- 100%: 완벽한 분류 (overfitting 의심)

**LOSO-CV**:
- 각 피험자를 test set으로 사용
- 나머지 피험자로 training
- 6명 → 6 folds → 6개의 accuracy
- Mean ± SD 보고

---

#### Confusion Matrix
**정의**: 실제 색상 vs 예측 색상의 교차표

```
           Pred_C1  Pred_C2  ...  Pred_C8
True_C1      n11      n12    ...    n18
True_C2      n21      n22    ...    n28
...
True_C8      n81      n82    ...    n88
```

**분석**:
- **Diagonal**: 정확히 분류된 경우
- **Off-diagonal**: 오분류
- **Confusion patterns**: 어떤 색상 쌍이 헷갈리는가?
  - 예: Red ↔ Orange 혼동 많으면 유사한 색상

**Normalized version**:
```
Normalized[i,j] = n[i,j] / sum(n[i,:])
```
- Row sum = 1.0
- 각 실제 색상의 예측 분포

---

### 2. Reconstruction Metrics

#### Mean Reconstruction Error
**정의**: 예측 hue와 실제 hue 간 circular distance 평균

```python
error = min(|predicted - true|, 360 - |predicted - true|)
Mean Error = mean(errors)  # in degrees
```

**해석**:
- 0°: 완벽한 복원
- 45°: ±1 색상 오차 (8 colors → 360°/8 = 45°)
- 90°: ±2 색상 오차
- 180°: 정반대 색상 (최악)

**참고**: Brouwer & Heeger (2009)
- V1: ~30-40°
- V4: ~20-30°
- hV4가 더 정확한 색상 정보

---

#### Hit Rates
**정의**: 특정 threshold 내 복원 성공률

```python
Hit_rate_22.5 = % of errors <= 22.5°
Hit_rate_45 = % of errors <= 45°
```

**22.5°**: Half of adjacent color bin (±1/2 color)
**45°**: Adjacent color bin (±1 color)

**해석**:
- Hit_rate_45 > 80%: 대부분 인접 색상 내 복원
- Hit_rate_22.5 > 50%: 매우 정확한 복원

---

### 3. Statistical Test Metrics

#### T-statistic
**정의**: 효과 크기의 표준화된 측정

```
t = (mean difference) / (standard error)
t = (mean difference) / (SD / sqrt(N))
```

**해석**:
- |t| > 2: 일반적으로 유의미 (df=5, two-tailed p<0.1)
- |t| > 3: 강한 효과 (p<0.03)
- |t| > 5: 매우 강한 효과 (p<0.004)
- |t| > 10: 극도로 강한 효과

**Degrees of freedom**: df = N_subjects - 1 = 5

---

#### P-value
**정의**: 귀무가설이 참일 때 관찰된 결과 또는 더 극단적인 결과를 얻을 확률

**해석**:
- p < 0.05: 통계적으로 유의미 (전통적)
- p < 0.01: 매우 유의미
- p < 0.001: 극도로 유의미

**주의**:
- N=6일 때 p-value만으로는 power 부족
- Effect size (t-statistic)도 함께 고려

---

#### FDR-corrected p-value
**정의**: Benjamini-Hochberg 방법으로 보정된 p-value

**목적**: Multiple comparison 문제 해결

**예시**:
- 8 colors × 388 voxels = 3,104 tests
- 28 pairs × 388 voxels = 10,864 tests
- 이 중 α=0.05로 유의미한 것만 선택

**문제**: N=6일 때 너무 보수적 → t-threshold 권장

---

### 4. PCA Metrics

#### Explained Variance Ratio
**정의**: 각 PC가 설명하는 전체 분산의 비율

```
Explained_variance_ratio[i] = λ[i] / sum(λ)
```

**해석**:
- PC1: 보통 20-40%
- Top 5 PCs: 보통 60-80% cumulative
- Top 10 PCs: 보통 80-90% cumulative

**Scree plot**: PC별 explained variance
- "Elbow point": 그 이후는 noise 수준

---

#### Cumulative Explained Variance
**정의**: Top-K PCs까지의 누적 설명 분산

```
Cumulative[k] = sum(Explained_variance_ratio[1:k])
```

**목적**: 몇 개의 PC로 충분한가?

**기준**:
- 90%: 일반적으로 충분
- 95%: 보수적
- 99%: 거의 모든 정보 보존

---

#### PCA Loadings
**정의**: 각 original feature (voxel)이 PC에 기여하는 정도

```
Loadings[voxel, PC] = weight of voxel in PC
```

**해석**:
- High positive loading: PC가 증가할 때 voxel activation 증가
- High negative loading: PC가 증가할 때 voxel activation 감소
- Near zero: PC와 무관

**High-loading voxels**: 특정 PC를 주로 설명하는 voxels

---

### 5. Voxel Quality Metrics

#### SNR (Signal-to-Noise Ratio)
**정의**: 신호 강도 대비 잡음 수준

```python
signal = std(mean_response_per_color)
noise = mean(std_response_within_color)
SNR = signal / noise
```

**해석**:
- SNR > 1: 신호가 잡음보다 강함
- SNR > 2: 좋은 quality
- SNR > 3: 매우 좋은 quality

---

#### R² (Coefficient of Determination)
**정의**: 모델이 설명하는 분산 비율

```
R² = 1 - (SS_residual / SS_total)
```

**해석**:
- R² > 0.1: 약한 설명력
- R² > 0.3: 중간 설명력
- R² > 0.5: 강한 설명력

---

## 언제 어떤 Pipeline을 사용할까?

### Original Pipeline 사용 시기

✅ **이런 경우 사용**:
1. **전통적인 feature selection 비교**
   - PCA vs ANOVA 어떤 것이 더 좋은가?
   - Optimal feature 수는?

2. **차원 축소 효과 분석**
   - 몇 개의 PC로 충분한가?
   - PCA가 성능을 향상시키는가?

3. **여러 K 값 테스트**
   - K=50, 100, 200 비교
   - Performance vs. complexity trade-off

4. **Brain 공간 시각화**
   - High-loading voxels의 anatomical location
   - PC별 spatial pattern

❌ **이런 경우 부적합**:
- 색상 간 변별 능력 분석
- 적록색맹 관련 연구
- Pairwise color discrimination

---

### Comprehensive Pipeline 사용 시기

✅ **이런 경우 사용**:
1. **적록색맹 연구** ⭐
   - 어떤 색상 쌍을 구별하는가?
   - Red-Green discrimination 분석

2. **Color selectivity 분석**
   - 특정 색상 선호 voxel 찾기
   - Color tuning 분석

3. **작은 샘플 (N<10)**
   - T-threshold 방법 사용
   - FDR보다 더 적합

4. **종합적인 분석**
   - 여러 통계 방법 결합
   - Union voxel approach

5. **상세한 시각화**
   - 28 pairwise contrasts
   - Union breakdown
   - PCA 포함

❌ **이런 경우 부적합**:
- Brain 공간 시각화 필요 (MNI coordinates)
- 여러 K 값 체계적 비교

---

### 권장 사용법

#### 🎯 **추천 워크플로우**

**Phase 1: Comprehensive Analysis** (메인 분석)
```bash
sbatch run_group_level_comprehensive.sbatch
```
- 적록색맹 관련 핵심 질문 답변
- Union voxels + PCA
- T-threshold (N=6)

**Phase 2: Original Pipeline** (보충 분석)
```bash
sbatch run_group_level_analysis.sbatch
```
- Feature selection 방법 비교
- Brain visualization
- 여러 K 값 테스트

**Phase 3: 통합 분석**
- Comprehensive의 union voxels와 Original의 ANOVA/PCA 비교
- 어떤 방법이 더 좋은 성능?
- Voxel overlap 분석

---

## 전체 Workflow

### 데이터 흐름

```
Individual Subjects (sub-01~07)
├── fMRIPrep preprocessing
├── GLM analysis (per subject)
│   ├── Design matrix construction
│   ├── Beta estimation
│   └── Voxel selection (SNR/R²)
└── Amplitudes extraction
    └── amplitudes_z.npy (N_runs × N_colors × N_voxels)

↓

Group-Level Common Voxels
├── Load all subjects' amplitudes
├── SNR-based top-K selection
│   └── K = min(voxel counts across subjects)
└── group_amplitudes_z.npy (N_subjects × N_runs × N_colors × K_voxels)

↓↓↓ Split ↓↓↓

┌─────────────────────────────────┐      ┌──────────────────────────────────┐
│    Original Pipeline            │      │   Comprehensive Pipeline         │
├─────────────────────────────────┤      ├──────────────────────────────────┤
│ 1. PCA Analysis                 │      │ 1. Three Statistical Tests       │
│    ├── Fit PCA (n_comp=50)      │      │    ├── Option A: vs 0            │
│    ├── LOSO-CV evaluation       │      │    ├── Option B-1: selectivity   │
│    └── High-loading voxels      │      │    └── Option B-2: pairwise (28) │
│                                 │      │                                  │
│ 2. ANOVA Feature Selection      │      │ 2. Voxel Selection               │
│    ├── F-test per voxel         │      │    ├── FDR correction OR         │
│    ├── Top-K selection          │      │    └── T-threshold (|t|>5)       │
│    │   (K=50,100,200)           │      │                                  │
│    └── LOSO-CV evaluation       │      │ 3. Union Voxel Approach          │
│                                 │      │    └── A ∪ B-1 ∪ B-2             │
│                                 │      │                                  │
│                                 │      │ 4. Classification & Recon        │
│                                 │      │    └── LOSO-CV on union          │
│                                 │      │                                  │
│                                 │      │ 5. PCA on Union Voxels           │
│                                 │      │    └── LOSO-CV evaluation        │
└─────────────────────────────────┘      └──────────────────────────────────┘

↓                                        ↓

Results Comparison & Integration
├── Performance metrics comparison
├── Voxel overlap analysis
└── Final interpretation
```

---

### 처리 시간 예상

**Original Pipeline** (per ROI):
- Common voxels: ~5-10분
- PCA analysis: ~10-15분
- ANOVA selection: ~15-20분 (3 K values)
- **Total**: ~30-45분

**Comprehensive Pipeline** (per ROI):
- Common voxels: ~5-10분
- Three statistical tests: ~10-15분
- Union voxel evaluation: ~5-10분
- PCA analysis: ~5-10분
- **Total**: ~25-45분

**4 ROIs in parallel** (SLURM array job):
- Wall time: ~45분 (single ROI의 최대 시간)
- Total CPU time: ~3시간 (4 ROIs × 45분)

---

### 메모리 요구사항

**피험자 수**: N=6
**Runs**: 6
**Colors**: 8
**Voxels**: ~200-400 (SNR-based selection)

**메모리 계산**:
```python
group_amplitudes_z: (6, 6, 8, 400) × 8 bytes = ~1.1 MB
PCA transformed: (6 × 6 × 8, 50) × 8 bytes = ~115 KB
Statistics arrays: (8, 400) × 8 bytes × 3 = ~77 KB
Pairwise contrasts: (28, 400) × 8 bytes = ~90 KB
```

**총 메모리**: <100 MB (매우 가벼움)

**SLURM 설정**: `--mem=64G` (충분히 여유있음)

---

### 디스크 공간

**Original Pipeline** (per ROI):
- PCA results: ~10-20 MB
- ANOVA results: ~5-10 MB
- Figures: ~5-10 MB
- **Total**: ~20-40 MB

**Comprehensive Pipeline** (per ROI):
- Statistics: ~5-10 MB
- PCA: ~5 MB
- Figures: ~10-15 MB
- **Total**: ~20-30 MB

**4 ROIs 전체**: ~80-140 MB (매우 가벼움)

---

## 결과 해석 가이드

### 1. Comprehensive Pipeline 결과

#### Pairwise Contrasts Grid
**파일**: `figures/pairwise_contrasts_grid.png`

**확인사항**:
1. **Red bars**: |t| > threshold인 유의미한 voxels
2. **어떤 pair가 가장 많은 voxels?**
   - 많은 voxels → 쉽게 구별 가능한 색상 쌍
   - 적은 voxels → 구별 어려운 색상 쌍
3. **적록색맹 관련 pairs**:
   - Red vs Green
   - Red vs Yellow
   - Green vs Yellow
   - 이들의 voxel 수가 적다면? → 적록색맹 구별 어려움

**예시 해석**:
```
C1 (Red) vs C3 (Green): 150 sig voxels
C1 (Red) vs C5 (Blue): 200 sig voxels
→ Red-Blue 구별이 Red-Green 구별보다 쉬움
→ 적록색맹 연구에서 중요한 발견
```

---

#### Union Voxels Breakdown
**파일**: `figures/union_voxels_breakdown.png`

**확인사항**:
1. **Union 크기**: 몇 % voxels가 선택되었나?
   - <10%: 매우 선택적
   - 10-30%: 적절
   - >50%: 너무 많음 (threshold 조정 필요)

2. **각 테스트의 기여도**:
   - Option A (vs 0): 기본 activation
   - Option B-1 (selectivity): Color tuning
   - Option B-2 (pairwise): Discrimination

3. **Overlap**:
   - All three: 세 테스트 모두 유의미 → 가장 강한 voxels
   - Exclusive to B-2: Pairwise에서만 잡힌 특수한 voxels

---

#### Classification Performance
**파일**: `performance/classification_results.csv`

**확인사항**:
```csv
test_subject,n_voxels,classification_acc,reconstruction_error,mean_snr
1,180,0.68,28.5,2.1
2,180,0.71,25.3,2.3
3,180,0.65,31.2,1.9
4,180,0.73,24.1,2.4
5,180,0.69,27.8,2.0
6,180,0.67,29.3,2.2
Mean,180,0.69±0.03,27.7±2.8,2.15±0.18
```

**해석**:
- **Mean accuracy 69%**: Chance (12.5%)보다 훨씬 높음 → Good
- **SD 3%**: 피험자 간 일관성 높음
- **Mean error 27.7°**: <45° → 대부분 인접 색상 내 복원
- **Mean SNR 2.15**: >2 → Good quality voxels

---

#### PCA Performance
**파일**: `performance/pca_performance.csv`

**비교**:
```
Union voxels (180): Acc = 69%
PCA (50 components): Acc = 65%
```

**해석**:
- PCA로 차원 축소 후 약간의 성능 감소
- But, 180 → 50 features (72% reduction)
- Trade-off: Performance vs. Dimensionality

---

### 2. Original Pipeline 결과

#### PCA Explained Variance
**파일**: `pca/figures/explained_variance.png`

**확인사항**:
1. **Top PC의 variance**: 얼마나 설명하는가?
   - PC1: 25% → Dominant pattern
   - PC1: 10% → 여러 pattern 분산

2. **Cumulative 90% 도달**: 몇 개 PC?
   - 10 PCs → 매우 효율적
   - 30 PCs → 복잡한 구조

3. **Scree plot의 elbow**:
   - Elbow 이후는 noise 수준

---

#### ANOVA Performance vs K
**파일**: `anova/figures/performance_vs_k.png`

**확인사항**:
1. **Optimal K**: 성능이 최대인 K 값
2. **Plateau**: 성능이 더 이상 증가 안 하는 지점
3. **Overfitting**: K 증가 시 성능 감소?

**예시**:
```
K=50:  Acc=62%, Error=32°
K=100: Acc=68%, Error=28°  ← Optimal
K=200: Acc=67%, Error=29°  (과적합 시작?)
```

---

### 3. 통합 분석

#### 성능 비교표
```
Method                  | Accuracy | Error | N_features
------------------------|----------|-------|------------
Union voxels (t>5)      | 69%     | 27.7° | 180
PCA on union (50 comp)  | 65%     | 30.1° | 50
ANOVA (K=100)           | 68%     | 28.2° | 100
PCA (50 comp)           | 63%     | 32.5° | 50
```

**해석**:
- Union voxels가 가장 좋은 성능
- ANOVA K=100도 유사한 성능
- PCA는 차원 축소 효과가 크지만 성능 약간 감소

---

#### Voxel Overlap 분석
```python
# 어떤 voxels가 여러 방법에서 공통으로 선택되는가?
union_voxels = set(union_mask_indices)
anova_100_voxels = set(anova_k100_indices)
overlap = union_voxels & anova_100_voxels

overlap_ratio = len(overlap) / len(union_voxels)
# 예: 75% overlap → 대부분 일치
```

**의미**:
- High overlap (>70%): 방법들이 유사한 voxels 선택
- Low overlap (<30%): 방법들이 다른 측면 포착

---

## 요약

### Original Pipeline
**강점**:
- ✅ Feature selection 방법 비교
- ✅ Brain 공간 시각화
- ✅ 여러 K 값 체계적 테스트

**약점**:
- ❌ 색상 변별 능력 분석 없음
- ❌ 적록색맹 특화 분석 없음

**사용 시기**: 방법론 비교, visualization

---

### Comprehensive Pipeline
**강점**:
- ✅ 28 pairwise color contrasts
- ✅ 적록색맹 연구 특화
- ✅ Union voxel approach
- ✅ T-threshold (N=6)
- ✅ PCA 포함

**약점**:
- ❌ Brain 공간 시각화 부족
- ❌ 여러 K 값 비교 없음

**사용 시기**: 적록색맹 연구, 메인 분석

---

### 최종 권장
**1단계**: Comprehensive pipeline 실행 (메인 분석)
**2단계**: Original pipeline 실행 (보충 분석)
**3단계**: 결과 통합 및 해석

이렇게 하면 두 방법의 장점을 모두 활용할 수 있습니다! 🎯
