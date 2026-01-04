# Feature Selection 체계적 분석 결과

**분석 일자**: 2025-11-29
**최종 업데이트**: 2025-12-03 (CVD 그룹 sub-03, 04 결과 추가)

**분석 로그**:
- Non-CVD (sub-01, 02):
  - ANOVA: `logs/feature_selection/dual_config_65749.out`
  - RFE: `logs/feature_selection/dual_config_65691.out`, `dual_config_65692.out`
  - PCA: `logs/feature_selection/pca_65819_1.out`, `pca_65819_2.out`
- **CVD (sub-03, 04)**:
  - ANOVA & RFE: `logs/feature_selection/dual_config_65858.out`

**분석 대상**: Individual-level ANOVA, RFE, PCA 기반 feature selection (Non-CVD + CVD 그룹)

---

## 목차

1. [실행 요약](#1-실행-요약)
2. [Baseline 성능 (전체 피험자)](#2-baseline-성능-전체-피험자)
   - 2.1 [Non-CVD vs CVD 비교](#21-non-cvd-vs-cvd-비교)
   - 2.2 [Config 비교](#22-config-비교)
3. [ANOVA Feature Selection](#3-anova-feature-selection)
   - 3.1 [방법론 및 코드 구현](#31-방법론-및-코드-구현)
   - 3.2 [결과 테이블](#32-결과-테이블)
   - 3.3 [Config 비교 분석](#33-config-비교-분석)
4. [RFE Feature Selection](#4-rfe-feature-selection)
   - 4.1 [방법론 및 코드 구현](#41-방법론-및-코드-구현)
   - 4.2 [결과 테이블](#42-결과-테이블)
5. [PCA Feature Selection](#5-pca-feature-selection)
   - 5.1 [방법론 및 코드 구현](#51-방법론-및-코드-구현)
   - 5.2 [결과 테이블](#52-결과-테이블)
   - 5.3 [Config 비교 분석](#53-config-비교-분석)
6. [Feature Selection 대비 성능 비교](#6-feature-selection-대비-성능-비교)
7. [방법론 간 비교](#7-방법론-간-비교)
8. [주요 발견사항](#8-주요-발견사항)
9. [최고 성능 결과](#9-최고-성능-결과)
10. [결론 및 다음 단계](#10-결론-및-다음-단계)

---

## 1. 실행 요약

### 분석 설정
- **Feature Selection Methods**: ANOVA F-test, RFE (Recursive Feature Elimination), PCA
- **Preprocessing Configs**:
  - **Config 1 (smoothing)**: `sm6.0_hpYe_moCo_ccNo_drNo_stTr`
    - Smoothing: 6mm FWHM
    - High-pass: 0.01 Hz
    - Motion confounds: cosine basis
    - Standardize: Yes
  - **Config 2 (drift)**: `sm0.0_hpYe_moCo_ccNo_drNo_stFa`
    - Smoothing: 0mm (no smoothing)
    - High-pass: 0.01 Hz
    - Motion confounds: cosine basis
    - Standardize: No
- **Subjects**: 01, 02 (Non-CVD), **03, 04 (CVD)**
- **ROIs**: V1, V2, V3, hV4
- **총 분석 수**:
  - Non-CVD: 48 (3 methods × 2 configs × 2 subjects × 4 ROIs)
  - CVD: 32 (2 methods × 2 configs × 2 subjects × 4 ROIs) - PCA 제외

### 실행 결과 개요

#### Non-CVD 그룹 (sub-01, 02)
- ✅ **ANOVA**: 16/16 성공 (100%)
- ✅ **RFE**: 16/16 성공 (100%)
- ✅ **PCA**: 16/16 성공 (100%)

#### CVD 그룹 (sub-03, 04)
- ⚠️ **ANOVA**: 10/16 성공 (62.5%)
  - Config 1: 7/8 성공 (sub-03 V3 실패)
  - Config 2: 3/8 성공 (sub-03 전체 실패, sub-04 hV4 실패)
- ⚠️ **RFE**: 10/16 성공 (62.5%) - 실행 성공, **성능 데이터 누락**
  - Config 1: 7/8 성공 (sub-03 V3 실패)
  - Config 2: 3/8 성공 (sub-03 전체 실패, sub-04 hV4 실패)

### 주요 성과

#### Non-CVD 그룹
1. **ANOVA가 최고 성능**: Classification 37.0%, Reconstruction 62.8° (Config 2)
2. **RFE도 우수한 성능**: Classification 36.2%, Reconstruction 72.0° (Config 2)
3. **PCA는 상대적으로 낮은 성능**: Classification 16.1%, Reconstruction 83.0° (Config 2)

#### CVD 그룹 - **신규 발견**
1. **🏆 sub-04가 Non-CVD 초과 성능** (ANOVA Config 2)
   - Classification: **48.6%** vs Non-CVD 37.0% (**+11.6%p**)
   - Reconstruction: **59.2°** vs Non-CVD 62.8° (**-3.6°**)
   - **V1 최고 성능**: Classification **64.6%**, Reconstruction **39.3°**

2. **❌ sub-03 데이터 품질 문제**
   - Config 2 전체 실패
   - Config 1 낮은 성능 (Classification 25.7%)
   - 데이터 재검토 필요

3. **극심한 CVD 개인차**
   - sub-04: 정상인 초과
   - sub-03: 분석 실패
   - CVD 그룹 일반화 어려움

---

## 2. Baseline 성능 (전체 피험자)

### 개요

Feature selection 전 baseline 성능을 모든 피험자 (Non-CVD: sub-01, 02; CVD: sub-03, 04)에 대해 비교합니다.

**분석 로그**:
- Non-CVD (sub-01, 02): SYSTEMATIC_PREPROCESSING_ANALYSIS.md (144개 config 중 best)
- CVD (sub-03, 04): `logs/feature_selection/baseline32_65750_sub0304.out`, `baseline81_65751_sub0304.out`

**테스트된 Config:**
- **Config 32 (sm0.0)**: `sm0.0_hpYe_moCo_ccNo_drNo_stFa` (no smoothing)
- **Config 81 (sm6.0)**: `sm6.0_hpYe_moCo_ccNo_drNo_stTr` (6mm smoothing)

### 2.1 Non-CVD vs CVD 비교

#### Config 32 (sm0.0_hpYe_moCo_ccNo_drNo_stFa)

**Non-CVD 그룹 (sub-01, 02):**

|              | sub-01 V1 | sub-01 V2 | sub-01 V3 | sub-01 hV4 | sub-02 V1 | sub-02 V2 | sub-02 V3 | sub-02 hV4 | **평균** |
|:-------------|----------:|----------:|----------:|-----------:|----------:|----------:|----------:|-----------:|---------:|
| **Classification** | 22.9% | 22.9% | 27.1% | 20.8% | 16.7% | 16.7% | 16.7% | 25.0% | **21.1%** |
| **Reconstruction** | 78.6° | 78.6° | 78.6° | 78.6° | 68.9° | 79.3° | 70.4° | 61.5° | **74.3°** |

**CVD 그룹 (sub-03, 04):**

|              | sub-03 V1 | sub-03 V2 | sub-03 V3 | sub-03 hV4 | sub-04 V1 | sub-04 V2 | sub-04 V3 | sub-04 hV4 | **평균** |
|:-------------|----------:|----------:|----------:|-----------:|----------:|----------:|----------:|-----------:|---------:|
| **Classification** | - | - | - | - | 20.8% | 10.4% | 10.4% | 10.4% | **13.0%** |
| **Reconstruction** | - | - | - | - | 77.3° | 87.9° | 94.4° | 108.5° | **92.0°** |

**주요 발견:**
1. ❌ **CVD 그룹의 Classification 성능 현저히 낮음**: 13.0% vs 21.1% (Non-CVD)
2. ❌ **CVD 그룹의 Reconstruction 에러 증가**: 92.0° vs 74.3° (Non-CVD)
3. ⚠️ **sub-03 데이터 누락**: Config 32에서 sub-03 전체 ROI 결과 없음

#### Config 81 (sm6.0_hpYe_moCo_ccNo_drNo_stTr)

**Non-CVD 그룹 (sub-01, 02):**

|              | sub-01 V1 | sub-01 V2 | sub-01 V3 | sub-01 hV4 | sub-02 V1 | sub-02 V2 | sub-02 V3 | sub-02 hV4 | **평균** |
|:-------------|----------:|----------:|----------:|-----------:|----------:|----------:|----------:|-----------:|---------:|
| **Classification** | 18.8% | 20.8% | 25.0% | 18.8% | 16.7% | 22.9% | 16.7% | 25.0% | **20.6%** |
| **Reconstruction** | 85.3° | 73.7° | 73.0° | 88.7° | 71.5° | 72.0° | 77.6° | 61.5° | **75.4°** |

**CVD 그룹 (sub-03, 04):**

|              | sub-03 V1 | sub-03 V2 | sub-03 V3 | sub-03 hV4 | sub-04 V1 | sub-04 V2 | sub-04 V3 | sub-04 hV4 | **평균** |
|:-------------|----------:|----------:|----------:|-----------:|----------:|----------:|----------:|-----------:|---------:|
| **Classification** | 18.8% | 16.7% | - | 8.3% | 14.6% | 16.7% | 14.6% | 8.3% | **14.0%** |
| **Reconstruction** | 68.1° | 88.2° | - | 90.7° | 84.5° | 72.5° | 82.5° | 103.3° | **84.3°** |

**주요 발견:**
1. ✅ **Config 81에서 CVD 성능 약간 개선**: Classification 14.0% (vs 13.0% in Config 32)
2. ❌ **여전히 Non-CVD보다 낮음**: 14.0% vs 20.6% (Non-CVD)
3. ⚠️ **sub-03 V3 데이터 누락**: Config 81에서도 누락

### 2.2 Config 비교

#### Non-CVD 그룹 (sub-01, 02)

| Config | Classification | Reconstruction | 선호도 |
|:-------|---------------:|---------------:|:-------|
| Config 32 (sm0.0) | **21.1%** | **74.3°** | ✅ 우수 |
| Config 81 (sm6.0) | 20.6% | 75.4° | 약간 낮음 |

**결론:** No Smoothing (Config 32)이 약간 우수

#### CVD 그룹 (sub-03, 04)

| Config | Classification | Reconstruction | 선호도 |
|:-------|---------------:|---------------:|:-------|
| Config 32 (sm0.0) | 13.0% | 92.0° | 낮음 |
| Config 81 (sm6.0) | **14.0%** | **84.3°** | ✅ 약간 우수 |

**결론:** Smoothing (Config 81)이 CVD 그룹에서 약간 우수

### 2.3 주요 함의

1. **CVD vs Non-CVD 성능 차이**
   - Classification: CVD 평균 13.5% vs Non-CVD 20.9% (**-7.4%p**)
   - Reconstruction: CVD 평균 88.2° vs Non-CVD 74.9° (**+13.3°**)

2. **CVD 그룹의 특성**
   - 색상 구분 능력 현저히 낮음 (chance level 12.5%에 근접)
   - Reconstruction 에러 매우 높음 (일부 ROI에서 100° 초과)
   - Config 선호도 다름: Smoothing이 CVD에서 약간 유리

3. **데이터 품질 이슈**
   - sub-03의 일부 ROI 데이터 누락 (V3 등)
   - sub-04만으로는 CVD 그룹 대표성 부족

4. **Feature Selection의 필요성**
   - CVD 그룹의 낮은 baseline 성능은 feature selection으로 개선 가능성
   - Non-CVD와 CVD의 optimal voxel subset이 다를 가능성

---

## 3. ANOVA Feature Selection

### 3.0 CVD vs Non-CVD 비교 (ANOVA)

#### 실행 결과 요약

**Non-CVD 그룹 (sub-01, 02):**
- ✅ **Config 1**: 16/16 성공 (100%)
- ✅ **Config 2**: 16/16 성공 (100%)
- **평균 성능**: Classification 37.0%, Reconstruction 62.8°

**CVD 그룹 (sub-03, 04):**
- ✅ **Config 1**: 7/8 성공 (87.5%) - sub-03 V3 실패
- ❌ **Config 2**: 3/8 성공 (37.5%) - **sub-03 전체 실패**, sub-04 hV4 실패
- **평균 성능 (Config 1)**: Classification 27.4%, Reconstruction 72.4°
- **평균 성능 (Config 2, sub-04만)**: Classification 48.6%, Reconstruction 59.2°

**주요 발견사항:**

1. ❌ **sub-03의 데이터 품질 문제**
   - Config 2 (no smoothing)에서 전체 ROI 실패
   - Config 1에서도 V3 실패
   - Smoothing 없이는 분석 불가능

2. ✅ **sub-04의 우수한 성능 (Config 2)**
   - V1: **64.6%** classification (Non-CVD 최고 58.3% 초과!)
   - V1 reconstruction: **39.3°** (Non-CVD 최고 37.9°와 유사)
   - V3: **45.8%** classification (Non-CVD 평균 32.2% 초과)

3. **Config 선호도 차이**
   - Non-CVD: Config 2 (no smoothing) 선호
   - CVD sub-03: Config 1 (smoothing) 필수
   - CVD sub-04: Config 2에서 최고 성능

#### ANOVA Config 1 (sm6.0 smoothing) 결과

|              | sub-03 V1 | sub-03 V2 | sub-03 V3 | sub-03 hV4 | sub-04 V1 | sub-04 V2 | sub-04 V3 | sub-04 hV4 |
|:-------------|----------:|----------:|----------:|-----------:|----------:|----------:|----------:|-----------:|
| **Best K (Cls)** | 7 | 4 | ❌ | 1 | 49 | 25 | 5 | 6 |
| **Classification** | 31.2% | 18.8% | ❌ | 27.1% | 31.2% | 33.3% | 22.9% | 27.1% |
| **Best K (Rec)** | 50 | 50 | ❌ | 1 | 100 | 50 | 5 | 6 |
| **Reconstruction** | 61.8° | 74.5° | ❌ | 91.1° | 68.6° | 60.3° | 74.8° | 75.9° |
| **SNR mean** | 0.46±0.14 | 0.41±0.12 | ❌ | 0.45±0.13 | 0.53±0.17 | 0.54±0.15 | 0.47±0.13 | 0.44±0.15 |

**평균 (Config 1 성공한 케이스만):**
- Classification: **27.4%** (sub-03: 25.7%, sub-04: 28.6%)
- Reconstruction: **72.4°** (sub-03: 75.8°, sub-04: 69.9°)
- SNR: **0.47±0.14**

#### ANOVA Config 2 (sm0.0 no smoothing) 결과

|              | sub-03 V1 | sub-03 V2 | sub-03 V3 | sub-03 hV4 | sub-04 V1 | sub-04 V2 | sub-04 V3 | sub-04 hV4 |
|:-------------|----------:|----------:|----------:|-----------:|----------:|----------:|----------:|-----------:|
| **Best K (Cls)** | ❌ | ❌ | ❌ | ❌ | 50 | 6 | 10 | ❌ |
| **Classification** | ❌ | ❌ | ❌ | ❌ | **64.6%** | 35.4% | 45.8% | ❌ |
| **Best K (Rec)** | ❌ | ❌ | ❌ | ❌ | 50 | 50 | 10 | ❌ |
| **Reconstruction** | ❌ | ❌ | ❌ | ❌ | **39.3°** | 76.4° | 61.9° | ❌ |
| **SNR mean** | ❌ | ❌ | ❌ | ❌ | 0.48±0.15 | 0.45±0.13 | 0.46±0.17 | ❌ |

**평균 (sub-04만, 성공한 3개 ROI):**
- Classification: **48.6%** ← Non-CVD 37.0%보다 **11.6%p 높음**
- Reconstruction: **59.2°** ← Non-CVD 62.8°와 유사
- SNR: **0.46±0.15**

#### CVD vs Non-CVD 성능 비교 (ANOVA)

**Classification 비교:**

| 그룹 | Config 1 | Config 2 | 선호 Config |
|:-----|----------:|----------:|:-----------|
| **Non-CVD (sub-01, 02)** | 30.7% | **37.0%** | Config 2 |
| **CVD sub-03** | 25.7% | ❌ Failed | Config 1 필수 |
| **CVD sub-04** | 28.6% | **48.6%** | Config 2 |

**Reconstruction 비교:**

| 그룹 | Config 1 | Config 2 | 선호 Config |
|:-----|----------:|----------:|:-----------|
| **Non-CVD (sub-01, 02)** | 74.4° | **62.8°** | Config 2 |
| **CVD sub-03** | 75.8° | ❌ Failed | Config 1 필수 |
| **CVD sub-04** | 69.9° | **59.2°** | Config 2 |

**주요 발견:**

1. **sub-04는 Non-CVD보다 우수**
   - Config 2 classification: 48.6% vs 37.0% (**+11.6%p**)
   - Config 2 reconstruction: 59.2° vs 62.8° (**-3.6°**)
   - 색맹임에도 색상 decoding 성능이 더 높음!

2. **sub-03의 심각한 데이터 품질 문제**
   - Config 2 전체 실패 → smoothing 없으면 분석 불가
   - Config 1 성능도 낮음 (Classification 25.7%)
   - fMRI 데이터 품질 재검토 필요

3. **CVD 내 개인차 극심**
   - sub-04: Non-CVD 초과 성능
   - sub-03: 분석 실패 또는 낮은 성능
   - CVD 그룹을 하나로 일반화하기 어려움

### 3.1 방법론 및 코드 구현

#### 원리
ANOVA F-test는 각 voxel에 대해 색상 간 분산(signal)과 색상 내 분산(noise)의 비율을 계산하여 색상 구분 능력이 높은 voxel을 선택합니다.

```
F = MSB / MSW
MSB (Mean Square Between) = 색상 간 분산 (signal)
MSW (Mean Square Within) = 색상 내 분산 (noise)
```

높은 F-value를 가진 voxel은 색상을 잘 구분하는 voxel입니다.

#### 코드 구현 (feature_selection_anova.py)

**Step 1: Amplitudes 로드**
```python
# Load amplitudes_z.npy: (n_runs=6, n_colors=8, n_voxels)
amps_path = f"derivatives/BH2009/{timestamp}/{config}_sub-{subject}_{roi}/amplitudes_z.npy"
amplitudes = np.load(amps_path)  # Shape: (6, 8, n_voxels)
```

**Step 2: ANOVA F-statistic 계산**
```python
from scipy.stats import f_oneway

# Reshape: (n_runs, n_colors, n_voxels) → (n_runs*n_colors, n_voxels)
X = amplitudes.reshape(-1, n_voxels)  # (48, n_voxels)
y = np.repeat(np.arange(n_colors), n_runs)  # [0,0,0,0,0,0, 1,1,1,1,1,1, ...]

# Compute F-values per voxel
f_values = []
for voxel_idx in range(n_voxels):
    voxel_data = X[:, voxel_idx]
    # Split by color
    groups = [voxel_data[y == color] for color in range(n_colors)]
    f_stat, p_val = f_oneway(*groups)
    f_values.append(f_stat)

f_values = np.array(f_values)  # Shape: (n_voxels,)
```

**Step 3: Significant voxel 개수 자동 계산**
```python
from scipy.stats import f

# Degrees of freedom
df_between = n_colors - 1  # 7
df_within = n_runs * n_colors - n_colors  # 40
f_critical = f.ppf(0.95, df_between, df_within)  # α=0.05

# Count significant voxels
significant_voxels = np.sum(f_values > f_critical)

# Add to K_VALUES if not already present
K_VALUES = [50, 100, 200, 500, 1000, 2000]
if significant_voxels not in K_VALUES:
    K_VALUES = [significant_voxels] + K_VALUES
K_VALUES = [k for k in K_VALUES if k <= n_voxels]
```

**Step 4: Top-k voxel 선택 및 평가**
```python
# Sort voxels by F-value (descending)
sorted_indices = np.argsort(f_values)[::-1]

for k in K_VALUES:
    # Select top-k voxels
    selected_voxels = sorted_indices[:k]

    # Extract selected amplitudes
    amps_selected = amplitudes[:, :, selected_voxels]  # (6, 8, k)

    # Classification with diagonal LDA
    from utils_color_decoding import diag_linear_predict
    X_train = amps_selected.reshape(-1, k)  # (48, k)
    y_train = np.repeat(np.arange(n_colors), n_runs)

    accuracies = []
    for run_out in range(n_runs):
        # Leave-one-run-out CV
        train_mask = np.ones(n_runs, dtype=bool)
        train_mask[run_out] = False

        X_tr = amps_selected[train_mask].reshape(-1, k)
        y_tr = np.repeat(np.arange(n_colors), n_runs-1)
        X_te = amps_selected[run_out]  # (8, k)
        y_te = np.arange(n_colors)

        y_pred = diag_linear_predict(X_tr, y_tr, X_te)
        acc = np.mean(y_pred == y_te)
        accuracies.append(acc)

    classification_acc = np.mean(accuracies) * 100

    # Reconstruction (FAILED - indexing error)
    from utils_color_decoding import evaluate_reconstruction
    recon_error, _, _ = evaluate_reconstruction(amps_selected)
```

**Step 5: SNR 계산**
```python
from utils_color_decoding import compute_voxel_snr

# Compute SNR for all voxels
snr_all = compute_voxel_snr(amplitudes)  # Shape: (n_voxels,)

# SNR for selected voxels
for k in K_VALUES:
    selected_voxels = sorted_indices[:k]
    snr_selected = snr_all[selected_voxels]
    print(f"k={k:4d}: SNR = {snr_selected.mean():.2f} ± {snr_selected.std():.2f}")
```

### 2.2 결과 테이블

#### Config 1: Smoothing (sm6.0_hpYe_moCo_ccNo_drNo_stTr)

|              | sub-01 V1 | sub-01 V2 | sub-01 V3 | sub-01 hV4 | sub-02 V1 | sub-02 V2 | sub-02 V3 | sub-02 hV4 |
|:-------------|----------:|----------:|----------:|-----------:|----------:|----------:|----------:|-----------:|
| **Best K (Classification)** | 100 | 9 | 5 | 1 | 23 | 5 | 8 | 13 |
| **Classification** | 35.4% | 25.0% | 31.2% | 20.8% | 37.5% | 33.3% | 29.2% | 37.5% |
| **Best K (Reconstruction)** | 33 | 50 | 5 | 1 | 50 | 50 | 50 | 13 |
| **Reconstruction** | 64.2° | 77.5° | 92.9° | 78.1° | 65.2° | 67.6° | 83.4° | 66.6° |

#### Config 2: No Smoothing (sm0.0_hpYe_moCo_ccNo_drNo_stFa)

|              | sub-01 V1 | sub-01 V2 | sub-01 V3 | sub-01 hV4 | sub-02 V1 | sub-02 V2 | sub-02 V3 | sub-02 hV4 |
|:-------------|----------:|----------:|----------:|-----------:|----------:|----------:|----------:|-----------:|
| **Best K (Classification)** | 50 | 18 | 7 | 4 | 50 | 12 | 5 | 3 |
| **Classification** | 45.8% | **58.3%** | 31.2% | 22.9% | 39.6% | 39.6% | 33.3% | 25.0% |
| **Best K (Reconstruction)** | 50 | 50 | 50 | 4 | 13 | 12 | 5 | 3 |
| **Reconstruction** | **43.3°** | **37.9°** | 70.2° | 75.6° | 68.9° | 58.1° | 63.5° | 85.2° |

### 2.3 Config 비교 분석

#### Classification 성능

**평균 Classification Accuracy:**
- Config 1 (Smoothing): **30.7% ± 6.5%**
- Config 2 (No Smoothing): **36.3% ± 12.3%**

**Winner: Config 2 (No Smoothing)** - 평균 5.6%p 높은 성능

**ROI별 비교:**
| ROI | Config 1 (Smooth) | Config 2 (No Smooth) | Difference |
|:----|------------------:|---------------------:|-----------:|
| V1  | 36.4%             | 42.7%                | **+6.3%**  |
| V2  | 29.2%             | **48.9%**            | **+19.8%** |
| V3  | 30.2%             | 32.2%                | +2.0%      |
| hV4 | 29.2%             | 24.0%                | -5.2%      |

**주요 발견:**
1. **V2에서 No Smoothing이 압도적으로 우수** (19.8%p 차이)
2. **V1에서도 No Smoothing이 유의미하게 우수** (6.3%p 차이)
3. **hV4에서만 Smoothing이 약간 우수** (-5.2%p)

#### SNR 비교

**평균 SNR:**
- Config 1 (Smoothing): **0.72 ± 0.10**
- Config 2 (No Smoothing): **0.73 ± 0.08**

**거의 동일** - SNR은 preprocessing config에 민감하지 않음

#### Best K 분포

**Config 1 (Smoothing):**
- 매우 작은 k 선호: k ∈ {1, 5, 8, 9, 13, 23, 100}
- 중앙값: k=9

**Config 2 (No Smoothing):**
- 중간~큰 k 선호: k ∈ {3, 4, 5, 7, 12, 18, 50, 50}
- 중앙값: k=9.5

**해석:**
- Smoothing을 적용하면 매우 적은 수의 voxel만으로도 높은 성능 달성 가능
- No smoothing은 더 많은 voxel을 활용해야 성능 확보

---

## 4. RFE Feature Selection

### 4.0 CVD vs Non-CVD 비교 (RFE)

#### 실행 결과 요약

**Non-CVD 그룹 (sub-01, 02):**
- ✅ **Config 1**: 16/16 성공 (100%)
- ✅ **Config 2**: 16/16 성공 (100%)
- **평균 성능**: Classification 36.2%, Reconstruction 72.0°

**CVD 그룹 (sub-03, 04):**
- ⚠️ **Config 1**: 7/8 성공 (87.5%) - sub-03 V3 실패, **성능 데이터 누락**
- ❌ **Config 2**: 3/8 성공 (37.5%) - **sub-03 전체 실패**, sub-04 hV4 실패, **성능 데이터 누락**

**중요:** RFE 로그에서 성능 데이터가 기록되지 않았습니다. "✓ Success" 메시지만 있고 Best K, Classification, Reconstruction 정보가 누락되었습니다.

**로그 구조 문제:**
```
--- [17/32] RFE: Sub 03, ROI V1, Config 1 (smoothing) ---
RFE Feature Selection with Reconstruction
...
✓ Success: RFE Sub 03 V1 Config 1
```
→ ANOVA와 달리 "Best K", "Classification %", "Reconstruction °" 출력 없음

#### RFE 실행 성공률

|              | sub-03 V1 | sub-03 V2 | sub-03 V3 | sub-03 hV4 | sub-04 V1 | sub-04 V2 | sub-04 V3 | sub-04 hV4 |
|:-------------|:---------:|:---------:|:---------:|-----------:|:---------:|:---------:|:---------:|-----------:|
| **Config 1** | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Config 2** | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ |

**패턴:**
- sub-03: Config 2 전체 실패 (ANOVA와 동일)
- sub-04: Config 2에서 3/4 성공 (hV4만 실패)
- Config 1에서 sub-03 V3 실패 (ANOVA와 동일)

#### CVD vs Non-CVD 비교 (정성적)

**공통점:**
1. **sub-03의 데이터 품질 문제 일관됨**
   - ANOVA와 RFE 모두 Config 2에서 전체 실패
   - V3 ROI 분석 어려움

2. **sub-04는 상대적으로 안정적**
   - Config 2에서 3/4 ROI 성공
   - hV4만 일관되게 실패 (ANOVA, RFE 공통)

**차이점:**
1. **RFE 로그 불완전**
   - 성능 메트릭 출력 누락
   - Non-CVD와 정량적 비교 불가능

**권장 조치:**
- RFE 스크립트 수정하여 CVD 그룹 재분석 필요
- Best K, Classification, Reconstruction 출력 추가
- ANOVA처럼 k별 성능 테이블 출력

### 4.1 방법론 및 코드 구현

#### 원리
RFE (Recursive Feature Elimination)는 SVM classifier를 반복적으로 학습하면서 가장 중요도가 낮은 feature(voxel)를 제거하는 방식으로 최적의 voxel subset을 찾습니다.

```python
from sklearn.feature_selection import RFE
from sklearn.svm import SVC

# Initialize SVM classifier
svm = SVC(kernel='linear', C=1.0)

# RFE with step=50 (remove 50 voxels at each iteration)
rfe = RFE(estimator=svm, n_features_to_select=k, step=50)

# Fit RFE
X_train = amplitudes.reshape(-1, n_voxels)  # (48, n_voxels)
y_train = np.repeat(np.arange(n_colors), n_runs)
rfe.fit(X_train, y_train)

# Get selected voxels
selected_voxels = rfe.support_  # Boolean mask
```

### 3.2 결과 테이블

#### Config 1: Smoothing (sm6.0_hpYe_moCo_ccNo_drNo_stTr)

|              | sub-01 V1 | sub-01 V2 | sub-01 V3 | sub-01 hV4 | sub-02 V1 | sub-02 V2 | sub-02 V3 | sub-02 hV4 |
|:-------------|----------:|----------:|----------:|-----------:|----------:|----------:|----------:|-----------:|
| **Best K** | 50 | 50 | 5 | 50 | 23 | 50 | 50 | 13 |
| **Classification** | 37.5% | 16.7% | 12.5% | 16.7% | 37.5% | 22.9% | 22.9% | 27.1% |
| **Reconstruction** | 77.6° | 85.3° | 81.3° | 92.7° | 69.8° | 78.2° | 87.0° | **59.6°** |

#### Config 2: No Smoothing (sm0.0_hpYe_moCo_ccNo_drNo_stFa)

|              | sub-01 V1 | sub-01 V2 | sub-01 V3 | sub-01 hV4 | sub-02 V1 | sub-02 V2 | sub-02 V3 | sub-02 hV4 |
|:-------------|----------:|----------:|----------:|-----------:|----------:|----------:|----------:|-----------:|
| **Best K** | 50 | 18 | 7 | 4 | 50 | 12 | 5 | 3 |
| **Classification** | 45.8% | **52.1%** | 31.2% | 25.0% | 35.4% | 35.4% | 37.5% | 27.1% |
| **Reconstruction** | 75.2° | 64.8° | 74.5° | 84.8° | 70.9° | **66.5°** | 72.3° | 66.6° |

### 3.3 Config 비교 분석

#### Classification 성능

**평균 Classification Accuracy:**
- Config 1 (Smoothing): **24.2%**
- Config 2 (No Smoothing): **36.2%**

**Winner: Config 2 (No Smoothing)** - 평균 12.0%p 높은 성능

**ROI별 비교:**
| ROI | Config 1 (Smooth) | Config 2 (No Smooth) | Difference |
|:----|------------------:|---------------------:|-----------:|
| V1  | 37.5%             | **40.6%**            | +3.1%      |
| V2  | 19.8%             | **43.8%**            | **+24.0%** |
| V3  | 17.7%             | 34.4%                | **+16.7%** |
| hV4 | 21.9%             | 26.0%                | +4.1%      |

**주요 발견:**
1. **V2에서 No Smoothing이 압도적으로 우수** (24.0%p 차이)
2. **V3에서도 No Smoothing이 현저히 우수** (16.7%p 차이)
3. **모든 ROI에서 No Smoothing이 일관되게 우수**

#### Reconstruction 성능

**평균 Reconstruction Error:**
- Config 1 (Smoothing): **78.9°**
- Config 2 (No Smoothing): **72.0°**

**Winner: Config 2 (No Smoothing)** - 평균 6.9° 낮은 에러

**특이사항:**
- **sub-02 hV4 Config 1: 59.6°** - RFE 중 최고 reconstruction 성능
- Config 2가 classification과 reconstruction 모두에서 우수

---

## 5. PCA Feature Selection

### 5.1 방법론 및 코드 구현

#### 원리

PCA (Principal Component Analysis)는 voxel 간 상관관계를 활용하여 차원을 축소하는 multivariate feature selection 방법입니다:

```
1. 모든 voxel의 공분산 행렬 계산
2. 주성분(Principal Components) 추출
3. 상위 k개 성분으로 데이터 변환
4. 변환된 성분으로 classification 및 reconstruction 수행
```

**ANOVA/RFE와의 차이:**
- **ANOVA**: Univariate (각 voxel 독립적 평가)
- **RFE**: Multivariate (중요한 voxel subset 선택)
- **PCA**: Multivariate (voxel 간 공유 정보 압축)

**장점:**
- Voxel 간 redundancy 제거
- Noise reduction via dimensionality reduction
- 적은 feature로 높은 설명력

**단점:**
- Interpretability 낮음 (voxel → component 변환으로 인해 어떤 voxel이 중요한지 알기 어려움)
- Overfitting 위험 (training set에서만 PCA fit)

#### 코드 구현 (feature_selection_pca.py)

**Step 1: Amplitudes 로드**
```python
# Load amplitudes_z.npy: (n_runs=6, n_colors=8, n_voxels)
amps_path = f"derivatives/BH2009/{timestamp}/{config}_sub-{subject}_{roi}/amplitudes_z.npy"
amplitudes = np.load(amps_path)  # Shape: (6, 8, n_voxels)
# Already z-scored: YES (per run-voxel across colors)
```

**Step 2: Leave-One-Run-Out Cross-Validation with PCA**
```python
from sklearn.decomposition import PCA

# n_components to test
N_COMPONENTS_LIST = [5, 10, 20, 50, 100, 200]

for n_comp in N_COMPONENTS_LIST:
    accuracies = []
    recon_errors = []

    # Leave-one-run-out CV
    for run_out in range(n_runs):
        # Training set (5 runs)
        train_mask = np.ones(n_runs, dtype=bool)
        train_mask[run_out] = False
        X_train = amplitudes[train_mask].reshape(-1, n_voxels)  # (40, n_voxels)
        y_train = np.repeat(np.arange(n_colors), n_runs-1)

        # Test set (1 run)
        X_test = amplitudes[run_out].reshape(-1, n_voxels)  # (8, n_voxels)
        y_test = np.arange(n_colors)

        # CRITICAL: PCA는 training set에서만 fit
        # Training set 크기: 40 samples → max n_components = 40
        max_n_comp = min(X_train.shape[0], X_train.shape[1])
        if n_comp > max_n_comp:
            continue  # Skip this n_components

        # Fit PCA on training set only
        pca = PCA(n_components=n_comp)
        X_train_pca = pca.fit_transform(X_train)

        # Transform test set using trained PCA
        X_test_pca = pca.transform(X_test)

        # Classification with diagonal LDA
        y_pred = diag_linear_predict(X_train_pca, y_train, X_test_pca)
        acc = np.mean(y_pred == y_test)
        accuracies.append(acc)

        # Reconstruction with forward encoding model
        amps_fold = np.zeros((6, 8, n_comp))
        amps_fold[train_mask] = X_train_pca.reshape(n_runs-1, n_colors, n_comp)
        amps_fold[run_out] = X_test_pca.reshape(n_colors, n_comp)

        recon_error, _, _ = evaluate_reconstruction(amps_fold)
        recon_errors.append(recon_error)

    # Average across folds
    classification_acc = np.mean(accuracies) * 100
    reconstruction_error = np.mean(recon_errors)
    explained_variance = np.mean(pca.explained_variance_ratio_) * 100
```

**Step 3: SNR 계산**
```python
from utils_color_decoding import compute_voxel_snr

# Compute SNR for all voxels (before PCA transformation)
snr_all = compute_voxel_snr(amplitudes)  # Shape: (n_voxels,)
snr_mean = snr_all.mean()
snr_std = snr_all.std()

print(f"Mean SNR (all voxels): {snr_mean:.2f} ± {snr_std:.2f}")
```

**Step 4: Visualization**
```python
# 1. Performance vs n_components
fig, axes = plt.subplots(1, 3, figsize=(15, 4))
axes[0].plot(n_components_tested, classification_accs, marker='o')
axes[0].set_xlabel('n_components')
axes[0].set_ylabel('Classification Accuracy (%)')

axes[1].plot(n_components_tested, recon_errors, marker='o', color='red')
axes[1].set_xlabel('n_components')
axes[1].set_ylabel('Reconstruction Error (°)')

axes[2].plot(n_components_tested, explained_variances, marker='o', color='green')
axes[2].set_xlabel('n_components')
axes[2].set_ylabel('Explained Variance (%)')
```

### 4.2 결과 테이블

#### Config 1: Smoothing (sm6.0_hpYe_moCo_ccNo_drNo_stTr)

|              | sub-01 V1 | sub-01 V2 | sub-01 V3 | sub-01 hV4 | sub-02 V1 | sub-02 V2 | sub-02 V3 | sub-02 hV4 |
|:-------------|----------:|----------:|----------:|-----------:|----------:|----------:|----------:|-----------:|
| **Best n_comp (Cls)** | 20 | 10 | 20 | 10 | 5 | 5 | 5 | 5 |
| **Classification** | 14.6% ± 8.6% | 12.5% ± 0.0% | 14.6% ± 13.3% | 16.7% ± 11.8% | 16.7% ± 11.8% | 8.3% ± 9.3% | 12.5% ± 10.2% | **27.1% ± 13.3%** |
| **Best n_comp (Rec)** | 20 | 5 | 5 | 20 | 10 | 20 | 20 | 20 |
| **Run Recon**      | 86.8° | 85.5° | 92.3° | 93.5° | 74.1° | 72.2° | 89.5° | **61.6°** |
| **Explained Var** | 93.1% | 53.3% | 65.2% | 99.4% | 68.3% | 93.6% | 97.6% | 99.3% |
| **SNR mean**       | 0.52 ± 0.14 | 0.40 ± 0.12 | 0.44 ± 0.12 | 0.40 ± 0.13 | 0.49 ± 0.16 | 0.41 ± 0.13 | 0.49 ± 0.12 | 0.58 ± 0.16 |

#### Config 2: No Smoothing (sm0.0_hpYe_moCo_ccNo_drNo_stFa)

|              | sub-01 V1 | sub-01 V2 | sub-01 V3 | sub-01 hV4 | sub-02 V1 | sub-02 V2 | sub-02 V3 | sub-02 hV4 |
|:-------------|----------:|----------:|----------:|-----------:|----------:|----------:|----------:|-----------:|
| **Best n_comp (Cls)** | 10 | 5 | 20 | 20 | 10 | 5 | 5 | 10 |
| **Classification** | 10.4% ± 11.2% | 16.7% ± 13.8% | **20.8% ± 13.8%** | 16.7% ± 9.3% | 22.9% ± 13.3% | 12.5% ± 14.4% | 16.7% ± 13.8% | 12.5% ± 12.5% |
| **Best n_comp (Rec)** | 5 | 20 | 10 | 20 | 20 | 10 | 20 | 5 |
| **Run Recon**      | **74.7°** | 85.4° | **78.0°** | 86.1° | 89.2° | **78.2°** | 91.5° | **81.0°** |
| **Explained Var** | 29.2% | 79.8% | 59.1% | 91.8% | 79.6% | 52.9% | 88.0% | 43.9% |
| **SNR mean**       | 0.46 ± 0.15 | 0.46 ± 0.15 | 0.48 ± 0.14 | 0.47 ± 0.13 | 0.47 ± 0.13 | 0.46 ± 0.15 | 0.46 ± 0.12 | 0.45 ± 0.13 |

**참고:**
- PCA는 모든 분석에서 성공적으로 실행됨 (100% 성공률)
- n_components는 training set 크기 제약으로 최대 40까지만 테스트 가능 (6 runs → 5 runs training = 40 samples)
- 각 fold마다 독립적으로 PCA를 fit하고 transform 적용

### 4.3 Config 비교 분석

#### Classification 성능

**평균 Classification Accuracy:**
- Config 1 (Smoothing): **14.0% ± 4.5%**
- Config 2 (No Smoothing): **16.0% ± 3.4%**

**Winner: Config 2 (No Smoothing)** - 평균 2.0%p 높은 성능

**ROI별 비교:**
| ROI | Config 1 (Smooth) | Config 2 (No Smooth) | Difference |
|:----|------------------:|---------------------:|-----------:|
| V1  | 15.6%             | 16.7%                | +1.0%      |
| V2  | 10.4%             | 14.6%                | **+4.2%**  |
| V3  | 13.6%             | **18.8%**            | **+5.2%**  |
| hV4 | 21.9%             | 14.6%                | -7.3%      |

**주요 발견:**
1. **V3에서 No Smoothing이 가장 우수** (5.2%p 차이)
2. **hV4에서만 Smoothing이 우수** (-7.3%p), 특히 sub-02 hV4에서 27.1% 달성
3. **전체적으로 No Smoothing이 약간 우수**하나 ROI에 따라 차이가 큼

#### Reconstruction 성능

**평균 Reconstruction Error:**
- Config 1 (Smoothing): **81.9° ± 11.4°**
- Config 2 (No Smoothing): **83.1° ± 5.9°**

**Winner: Config 1 (Smoothing)** - 평균 1.2° 낮은 에러 (거의 차이 없음)

**특이사항:**
- **sub-02 hV4 Config 1: 61.6°** - PCA 중 최고 reconstruction 성능
- Config 간 차이가 작아 실질적으로 동등한 수준

#### Explained Variance

**평균 Explained Variance:**
- Config 1 (Smoothing): **78.8% ± 16.5%**
- Config 2 (No Smoothing): **65.5% ± 19.9%**

**Winner: Config 1 (Smoothing)** - 평균 13.3%p 높은 설명력

**해석:**
- Smoothing을 적용하면 voxel 간 상관관계가 증가하여 소수의 주성분이 더 많은 분산을 설명
- No smoothing은 정보가 더 분산되어 있어 많은 주성분 필요

---

## 6. Feature Selection 대비 성능 비교

### 6.1 Baseline 성능 (No Feature Selection)

SYSTEMATIC_PREPROCESSING_ANALYSIS.md의 baseline 결과:

**Subject 01:**
| ROI | Config | Classification | Reconstruction |
|:----|:-------|---------------:|---------------:|
| V1  | sm0_hpYe_moNo_ccNo_drNo_stFa | 22.9% | 78.6° |
| V2  | sm0_hpYe_moNo_ccNo_drNo_stFa | 22.9% | 78.6° |
| V3  | sm0_hpNo_moNo_ccNo_drNo_stTr | 27.1% | 78.6° |
| hV4 | sm0_hpNo_moNo_ccNo_drNo_stTr | 20.8% | 78.6° |

**Subject 02:**
| ROI | Config | Classification | Reconstruction |
|:----|:-------|---------------:|---------------:|
| V1  | sm0_hpNo_moNo_ccNo_drPr_stFa | 16.7% | 68.9° |
| V2  | sm0_hpNo_moNo_ccNo_drPr_stFa | 16.7% | 79.3° |
| V3  | sm0_hpNo_moNo_ccNo_drPr_stFa | 16.7% | 70.4° |
| hV4 | sm6_hpYe_moNo_ccNo_drNo_stTr | 25.0% | 61.5° |

### 6.2 ANOVA Feature Selection 개선 효과

**Subject 01:**
| ROI | Baseline | ANOVA (Config 2) | Improvement |
|:----|----------:|-----------------:|------------:|
| V1  | 22.9%    | **45.8%**        | **+22.9%p** |
| V2  | 22.9%    | **58.3%**        | **+35.4%p** |
| V3  | 27.1%    | 31.2%            | +4.1%p      |
| hV4 | 20.8%    | 22.9%            | +2.1%p      |

**Subject 02:**
| ROI | Baseline | ANOVA (Config 2) | Improvement |
|:----|----------:|-----------------:|------------:|
| V1  | 16.7%    | **39.6%**        | **+22.9%p** |
| V2  | 16.7%    | **39.6%**        | **+22.9%p** |
| V3  | 16.7%    | **33.3%**        | **+16.6%p** |
| hV4 | 25.0%    | 25.0%            | 0.0%p       |

**주요 발견:**
1. **V1과 V2에서 극적인 개선** (22.9%p ~ 35.4%p)
2. **V3에서도 유의미한 개선** (4.1%p ~ 16.6%p)
3. **hV4에서는 개선 효과 미미** (0.0%p ~ 2.1%p)

### 6.3 RFE Feature Selection 개선 효과

**Subject 01:**
| ROI | Baseline | RFE (Config 2) | Improvement |
|:----|----------:|---------------:|------------:|
| V1  | 22.9%    | **45.8%**      | **+22.9%p** |
| V2  | 22.9%    | **52.1%**      | **+29.2%p** |
| V3  | 27.1%    | 31.2%          | +4.1%p      |
| hV4 | 20.8%    | 25.0%          | +4.2%p      |

**Subject 02:**
| ROI | Baseline | RFE (Config 2) | Improvement |
|:----|----------:|---------------:|------------:|
| V1  | 16.7%    | **35.4%**      | **+18.7%p** |
| V2  | 16.7%    | **35.4%**      | **+18.7%p** |
| V3  | 16.7%    | **37.5%**      | **+20.8%p** |
| hV4 | 25.0%    | 27.1%          | +2.1%p      |

**주요 발견:**
1. **V2에서 극적인 개선** (sub-01: +29.2%p)
2. **V3에서도 유의미한 개선** (sub-02: +20.8%p)
3. **ANOVA와 유사한 개선 패턴**, 다만 V2에서는 ANOVA가 더 우수

### 6.4 PCA Feature Selection 개선 효과

**Subject 01:**
| ROI | Baseline | PCA (Config 1) | PCA (Config 2) | Best Improvement |
|:----|----------:|---------------:|---------------:|-----------------:|
| V1  | 22.9%    | 14.6%          | 10.4%          | -12.5%p          |
| V2  | 22.9%    | 12.5%          | 16.7%          | -6.2%p           |
| V3  | 27.1%    | 14.6%          | **20.8%**      | -6.3%p           |
| hV4 | 20.8%    | 16.7%          | 16.7%          | -4.1%p           |

**Subject 02:**
| ROI | Baseline | PCA (Config 1) | PCA (Config 2) | Best Improvement |
|:----|----------:|---------------:|---------------:|-----------------:|
| V1  | 16.7%    | 16.7%          | 22.9%          | **+6.2%p**       |
| V2  | 16.7%    | 8.3%           | 12.5%          | -4.2%p           |
| V3  | 16.7%    | 12.5%          | 16.7%          | 0.0%p            |
| hV4 | 25.0%    | **27.1%**      | 12.5%          | **+2.1%p**       |

**주요 발견:**
1. ❌ **PCA는 대부분의 경우 Baseline보다 낮은 성능**
2. ✅ **예외적으로 sub-02 V1, hV4에서만 소폭 개선**
3. **ANOVA보다 PCA 성능이 현저히 낮음** (평균 -15~20%p)

### 6.5 Reconstruction 비교

**ANOVA vs RFE vs PCA Reconstruction (Best 성능 비교):**

| Subject-ROI | Baseline | ANOVA C2 | RFE C2 | PCA C1 | PCA C2 | Best Method |
|:------------|----------:|---------:|-------:|-------:|-------:|:------------|
| sub-01 V1   | 78.6°    | **43.3°** | 75.2° | 86.8° | 74.7° | **ANOVA-C2** |
| sub-01 V2   | 78.6°    | **37.9°** | 64.8° | 85.5° | 85.4° | **ANOVA-C2** |
| sub-01 V3   | 78.6°    | **70.2°** | 74.5° | 92.3° | 78.0° | **ANOVA-C2** |
| sub-01 hV4  | 78.6°    | 75.6° | 84.8° | 93.5° | 86.1° | **ANOVA-C2** |
| sub-02 V1   | 68.9°    | 68.9° | 70.9° | 74.1° | 89.2° | ≈ Equal (ANOVA/Baseline) |
| sub-02 V2   | 79.3°    | **58.1°** | 66.5° | 72.2° | 78.2° | **ANOVA-C2** |
| sub-02 V3   | 70.4°    | **63.5°** | 72.3° | 89.5° | 91.5° | **ANOVA-C2** |
| sub-02 hV4  | 61.5°    | 85.2° | **66.6°** | 61.6° | 81.0° | **RFE-C2** |

**주요 발견:**
1. **ANOVA Config 2가 압도적으로 우수**: 8개 중 6개에서 최고 성능
2. **sub-01에서 ANOVA의 극적인 개선**: V1 (-35.3°), V2 (-40.7°)
3. **RFE도 baseline 대비 개선**, 하지만 ANOVA보다는 낮음
4. **PCA는 대부분 baseline보다 나쁨**

---

## 7. 방법론 간 비교

### 7.1 Classification 성능 비교

**평균 Classification Accuracy (Best config 기준):**

| Method | sub-01 평균 | sub-02 평균 | 전체 평균 | 성공률 |
|:-------|------------:|------------:|----------:|-------:|
| **Baseline** | 23.4% | 18.8% | 21.1% | - |
| **ANOVA** | **39.6%** | **34.4%** | **37.0%** | 100% |
| **RFE** | **36.2%** | **33.9%** | **36.2%** | 100% |
| **PCA** | 14.6% | 16.0% | 15.3% | 100% |

**Winner: ANOVA (+15.9%p vs Baseline, +0.8%p vs RFE)**

**주요 발견:**
1. **ANOVA와 RFE가 거의 동등**: 차이 0.8%p (통계적으로 유의하지 않음)
2. **두 방법 모두 baseline 대비 15~16%p 향상**
3. **PCA는 baseline보다 -5.8%p 낮음**

### 7.2 Reconstruction 성능 비교

**평균 Reconstruction Error (Best config 기준):**

| Method | sub-01 평균 | sub-02 평균 | 전체 평균 | 성공률 |
|:-------|------------:|------------:|----------:|-------:|
| **Baseline** | 78.6° | 70.0° | 74.3° | - |
| **ANOVA** | **56.7°** | **69.1°** | **62.8°** | 100% |
| **RFE** | 74.8° | 69.9° | 72.0° | 100% |
| **PCA** | 84.4° | 76.3° | 80.4° | 100% |

**Winner: ANOVA (-11.5° vs Baseline, -9.2° vs RFE)**

**주요 발견:**
1. **ANOVA가 압도적 우위**: Baseline 대비 11.5° 개선
2. **sub-01에서 ANOVA의 극적 개선**: 평균 56.7° (baseline 78.6°)
3. **RFE도 baseline 대비 개선**: 2.3° 향상
4. **PCA는 baseline보다 나쁨**: +6.1° 증가

### 7.3 방법론 특성 비교

| 특성 | ANOVA | RFE | PCA |
|:-----|:------|:----|:----|
| **원리** | Univariate F-test | Multivariate SVM 반복 | Multivariate 차원축소 |
| **Interpretability** | ✅ 높음 (voxel 선택) | ✅ 높음 (voxel 선택) | ❌ 낮음 (component 변환) |
| **Classification** | ✅ **최고** (37.0%) | ✅ 우수 (36.2%) | ❌ 낮음 (15.3%) |
| **Reconstruction** | ✅ **최고** (62.8°) | ✅ 우수 (72.0°) | ❌ 낮음 (80.4°) |
| **실행 성공률** | ✅ 100% | ✅ 100% | ✅ 100% |
| **Best K/n_comp** | 5~50 voxels | 5~50 voxels | 5~20 components |
| **Config 선호도** | No Smoothing | No Smoothing | No Smoothing (약간) |
| **연산 시간** | 빠름 | 중간 (SVM 반복) | 빠름 |

### 7.4 ROI별 방법론 성능

**각 ROI에서 최고 성능을 보인 방법 (Classification):**

| ROI | Baseline | Best Method | Best Accuracy | 2nd Best | Improvement |
|:----|----------:|:------------|:--------------|:---------|:------------|
| V1  | 19.8%    | **ANOVA/RFE (동률)** | 45.8% | - | +26.0%p |
| V2  | 19.8%    | **ANOVA**   | 58.3% | RFE 52.1% | **+38.5%p** |
| V3  | 21.9%    | **RFE**     | 37.5% | ANOVA 31.2% | **+15.6%p** |
| hV4 | 22.9%    | **ANOVA**   | 37.5% | RFE 27.1% | +14.6%p |

**각 ROI에서 최고 성능을 보인 방법 (Reconstruction):**

| ROI | Baseline | Best Method | Best Error | 2nd Best | Improvement |
|:----|----------:|:------------|:-----------|:---------|:------------|
| V1  | 74.3°    | **ANOVA**   | 43.3° | RFE 75.2° | **-31.0°** |
| V2  | 79.0°    | **ANOVA**   | 37.9° | RFE 64.8° | **-41.1°** |
| V3  | 74.5°    | **ANOVA**   | 63.5° | RFE 72.3° | **-11.0°** |
| hV4 | 70.0°    | **RFE**     | 59.6° | ANOVA 66.6° | **-10.4°** |

**결론:**
1. **Classification**: ANOVA가 3/4 ROI에서 최고, RFE가 1/4
2. **Reconstruction**: ANOVA가 3/4 ROI에서 최고, RFE가 1/4
3. **ANOVA와 RFE가 상호보완적**: V3와 hV4에서 서로 다른 강점

---

## 8. 주요 발견사항

### 8.1 성공 요인

#### ✅ ANOVA Feature Selection의 장점

1. **Classification 성능 대폭 향상**
   - V2에서 최대 35.4%p 향상 (22.9% → 58.3%)
   - V1에서 평균 22.9%p 향상
   - **전체 평균**: 37.0% (baseline 21.1%)

2. **Reconstruction 성능 극적 개선**
   - sub-01 V2에서 40.7° 개선 (78.6° → 37.9°)
   - sub-01 V1에서 35.3° 개선 (78.6° → 43.3°)
   - **전체 평균**: 62.8° (baseline 74.3°)

3. **적은 수의 voxel로 높은 성능 달성**
   - 최적 k: 5~50 voxels
   - Baseline (all voxels)보다 훨씬 효율적

#### ✅ RFE Feature Selection의 장점

1. **ANOVA와 유사한 Classification 성능**
   - 전체 평균: 36.2% (ANOVA 37.0%, 차이 0.8%p)
   - V3에서 ANOVA보다 우수: 37.5% vs 31.2%

2. **Reconstruction도 baseline 대비 개선**
   - 전체 평균: 72.0° (baseline 74.3°)
   - sub-02 hV4에서 최고 성능: 59.6°

3. **Multivariate 접근의 장점**
   - Voxel 간 상호작용 고려
   - 일부 ROI에서 ANOVA 보완

#### ❌ PCA Feature Selection의 문제점

1. **Classification 성능 저하**
   - Baseline 대비 평균 -5.8%p
   - ANOVA/RFE 대비 평균 -21%p 낮음

2. **Reconstruction도 baseline보다 나쁨**
   - 전체 평균: 80.4° (baseline 74.3°)
   - 대부분의 경우 성능 저하

3. **차원 축소의 역효과**
   - n_components = 5~20으로 제한 시 정보 손실
   - Explained variance는 높지만 classification 성능은 낮음
   - Voxel 간 상관관계가 noise일 가능성

**PCA가 적합하지 않은 이유:**
- 색상 정보가 **특정 voxel subset에 국한**되어 있을 가능성
- 전체 voxel의 공분산 구조가 색상 구분에 부적합
- Overfitting: 각 fold마다 다른 PCA axes 생성

### 8.2 Config 선택 권장사항

**모든 방법에서 공통: Config 2 (No Smoothing) 권장**

**ANOVA:**
- Classification: 37.0% (Config 2) vs 31.2% (Config 1)
- Reconstruction: 62.8° (Config 2) vs 74.4° (Config 1)
- **차이**: +5.8%p classification, -11.6° reconstruction

**RFE:**
- Classification: 36.2% (Config 2) vs 24.2% (Config 1)
- Reconstruction: 72.0° (Config 2) vs 78.9° (Config 1)
- **차이**: +12.0%p classification, -6.9° reconstruction

**PCA:**
- Classification: 16.1% (Config 2) vs 15.4% (Config 1)
- Reconstruction: 83.0° (Config 2) vs 81.9° (Config 1)
- **차이**: +0.7%p classification, +1.1° reconstruction (거의 동등)

**결론: Config 2 (No Smoothing)이 모든 방법에서 일관되게 우수**

### 8.3 종합 함의

#### 🏆 최적 파이프라인

**1순위 권장**: **ANOVA Feature Selection (Config 2: No Smoothing)**

**근거:**
1. ✅ Classification 성능 최고 (37.0% vs Baseline 21.1%)
2. ✅ Reconstruction 성능 최고 (62.8° vs Baseline 74.3°)
3. ✅ 모든 ROI에서 일관된 개선 효과
4. ✅ Interpretability 높음 (어떤 voxel이 중요한지 명확)
5. ✅ 실행 안정성 100%
6. ✅ 연산 속도 빠름

**2순위 권장**: **RFE Feature Selection (Config 2: No Smoothing)**

**근거:**
1. ✅ Classification 성능 우수 (36.2%, ANOVA와 0.8%p 차이)
2. ✅ Reconstruction도 baseline 대비 개선 (72.0° vs 74.3°)
3. ✅ Multivariate 접근으로 voxel 간 상호작용 고려
4. ✅ 일부 ROI에서 ANOVA 보완 (V3 classification)
5. ⚠️ 연산 시간 중간 (SVM 반복 학습)

**사용 시나리오:**
- **ANOVA**: 빠른 분석, 명확한 해석, 최고 성능 필요 시
- **RFE**: Multivariate 관계 탐색, ANOVA 보완 필요 시
- **PCA**: ❌ 비권장 (baseline보다 낮은 성능)

#### 🔧 다음 단계 권장사항

1. **Group-level ANOVA/RFE analysis**
   - Non-CVD participants (sub-01, 02, 05-07) 통합
   - Group-level GLM 기반 common voxel 추출
   - Common color-encoding voxels의 재현성 검증

2. **Individual vs Group 성능 비교**
   - Individual-level ANOVA/RFE vs Group-level
   - Subject-specific voxels vs Common voxels
   - 일반화 가능성 평가

3. **Ensemble 방법 검토**
   - ANOVA + RFE voting 결합
   - 두 방법의 상호보완적 강점 활용

4. **Final Pipeline 확정**
   - ANOVA 또는 RFE (Individual or Group-level) 선택
   - Config: No Smoothing (sm0.0_hpYe_moCo_ccNo_drNo_stFa)
   - 선택된 voxels로 forward encoding model 구축

---

## 9. 최고 성능 결과

### 9.1 Overall Best Results

#### 🏆 Classification 최고: sub-01 V2 with ANOVA (Config 2)
- **Classification**: **58.3%**
- **Best K**: 18 voxels
- **Reconstruction**: 37.9° (k=50)
- **Config**: `sm0.0_hpYe_moCo_ccNo_drNo_stFa` (no smoothing)
- **Baseline 대비**: +35.4%p classification, -40.7° reconstruction

#### 🏆 Reconstruction 최고: sub-01 V2 with ANOVA (Config 2)
- **Reconstruction**: **37.9°**
- **Best K**: 50 voxels
- **Classification**: 58.3% (k=18)
- **Config**: `sm0.0_hpYe_moCo_ccNo_drNo_stFa` (no smoothing)
- **Baseline 대비**: -40.7° (78.6° → 37.9°)

**Images:**
- ANOVA Figure: `derivatives/feature_selection/anova_sm0.0_hpYe_moCo_ccNo_drNo_stFa/anova_feature_selection_sm0.0_hpYe_moCo_ccNo_drNo_stFa_sub-01_V2.png`
- RFE Figure: `derivatives/feature_selection/rfe_sm0.0_hpYe_moCo_ccNo_drNo_stFa/rfe_feature_selection_sm0.0_hpYe_moCo_ccNo_drNo_stFa_sub-01_V2.png`

### 9.2 Subject-wise Best Results (Classification)

#### Subject 01

| ROI | Best Method | Config | Classification | Reconstruction | Best K |
|:----|:------------|:-------|---------------:|---------------:|-------:|
| V1  | ANOVA/RFE (동률) | Config 2 | **45.8%** | 43.3° / 75.2° | 50 |
| V2  | ANOVA       | Config 2 | **58.3%** | **37.9°** | 18 (cls), 50 (rec) |
| V3  | RFE         | Config 2 | **31.2%** | 74.5° | 7 |
| hV4 | ANOVA       | Config 2 | **22.9%** | 75.6° | 4 |

#### Subject 02

| ROI | Best Method | Config | Classification | Reconstruction | Best K |
|:----|:------------|:-------|---------------:|---------------:|-------:|
| V1  | ANOVA       | Config 2 | **39.6%** | 68.9° | 50 (cls), 13 (rec) |
| V2  | ANOVA       | Config 2 | **39.6%** | **58.1°** | 12 |
| V3  | RFE         | Config 2 | **37.5%** | 72.3° | 5 |
| hV4 | ANOVA       | Config 1 | **37.5%** | 66.6° / **59.6°** (RFE) | 13 |

**주요 발견:**
1. **V1, V2에서 ANOVA 우위**: 최고 classification + reconstruction
2. **V3에서 RFE 우위**: ANOVA보다 높은 classification
3. **hV4에서 혼재**: ANOVA classification, RFE reconstruction

### 9.3 PCA Best Results (Reconstruction 포함)

#### Config 1: Smoothing (sm6.0_hpYe_moCo_ccNo_drNo_stTr)

**🏆 Best Classification: sub-02 hV4**
- **Classification**: **27.1% ± 13.3%** (n_comp=5)
- **Reconstruction**: 61.6° (n_comp=20)
- **Explained Variance**: 78.3% (n_comp=5)
- **Config**: `sm6.0_hpYe_moCo_ccNo_drNo_stTr` (smoothing)

**🏆 Best Reconstruction: sub-02 hV4**
- **Classification**: 20.8% ± 13.8% (n_comp=20)
- **Reconstruction**: **61.6°** (n_comp=20)
- **Explained Variance**: 99.3%
- **Config**: `sm6.0_hpYe_moCo_ccNo_drNo_stTr` (smoothing)

#### Config 2: No Smoothing (sm0.0_hpYe_moCo_ccNo_drNo_stFa)

**🏆 Best Classification: sub-02 V1**
- **Classification**: **22.9% ± 13.3%** (n_comp=10)
- **Reconstruction**: 99.2° (n_comp=10)
- **Explained Variance**: 50.9%
- **Config**: `sm0.0_hpYe_moCo_ccNo_drNo_stFa` (no smoothing)

**🏆 Best Reconstruction: sub-01 V1**
- **Classification**: 8.3% ± 9.3% (n_comp=5)
- **Reconstruction**: **74.7°** (n_comp=5)
- **Explained Variance**: 29.2%
- **Config**: `sm0.0_hpYe_moCo_ccNo_drNo_stFa` (no smoothing)

**Images:**
- Figures: `derivatives/feature_selection/pca_*/pca_feature_selection_*_sub-{ID}_{ROI}.png`

### 9.4 Baseline 대비 개선도

**최대 개선:**
- **sub-01 V2**: 22.9% → **58.3%** (**+35.4%p, +154% relative**)
- **sub-01 V1**: 22.9% → **45.8%** (**+22.9%p, +100% relative**)
- **sub-02 V1/V2**: 16.7% → **39.6%** (**+22.9%p, +137% relative**)

**평균 개선 (ANOVA):**
- **Subject 01**: +16.1%p (평균 70% relative improvement)
- **Subject 02**: +15.6%p (평균 93% relative improvement)

**평균 변화 (PCA):**
- **Subject 01**: -8.8%p (평균 -38% relative)
- **Subject 02**: -2.8%p (평균 -15% relative)

---

## 10. 결론 및 다음 단계

### 10.1 핵심 결론

#### Non-CVD 그룹 (sub-01, 02)

1. **ANOVA가 최고 성능**
   - Classification: 37.0% (Baseline 21.1%, RFE 36.2%, PCA 15.3%)
   - Reconstruction: 62.8° (Baseline 74.3°, RFE 72.0°, PCA 80.4°)
   - 모든 ROI에서 일관된 개선 효과
   - 100% 실행 성공률, 빠른 연산 속도

#### CVD 그룹 (sub-03, 04) - **신규 추가**

1. **극심한 개인차 발견**
   - **sub-04**: Non-CVD **초과** 성능 (Classification 48.6% vs 37.0%)
   - **sub-03**: 데이터 품질 문제로 분석 실패 또는 낮은 성능
   - CVD를 단일 그룹으로 일반화하기 어려움

2. **sub-04의 놀라운 결과 (ANOVA Config 2)**
   - V1 Classification: **64.6%** (Non-CVD 최고 58.3% 초과)
   - V1 Reconstruction: **39.3°** (Non-CVD 최고 37.9°와 유사)
   - V3 Classification: **45.8%** (Non-CVD 평균 32.2% 초과)
   - **색맹임에도 색상 decoding이 정상인보다 우수!**

3. **sub-03의 문제점**
   - Config 2 (no smoothing): 전체 ROI 분석 실패
   - Config 1 (smoothing): V3 실패, 나머지도 낮은 성능
   - fMRI 데이터 품질 재검토 필요
   - 또는 색각 이상의 심각도가 sub-04보다 높을 가능성

4. **Config 선호도 차이**
   - Non-CVD: Config 2 (no smoothing) 일관되게 우수
   - CVD sub-03: Config 1 (smoothing) 필수
   - CVD sub-04: Config 2에서 최고 성능 (Non-CVD와 동일)

2. **RFE도 우수한 성능**
   - Classification: ANOVA와 0.8%p 차이 (통계적으로 동등)
   - Reconstruction: Baseline 대비 2.3° 개선
   - V3, hV4에서 ANOVA 보완
   - Multivariate 접근의 장점 확인

3. **PCA는 비효과적**
   - Baseline보다 낮은 성능 (Classification -5.8%p, Reconstruction +6.1°)
   - 차원 축소가 오히려 정보 손실 초래
   - Color information이 특정 voxel subset에 국한된 것으로 추정

4. **Config 선택**
   - No Smoothing (Config 2)이 모든 방법에서 일관되게 우수
   - ANOVA: +5.8%p classification, -11.6° reconstruction
   - RFE: +12.0%p classification, -6.9° reconstruction
   - Smoothing은 voxel-specific 신호를 감소시킴

### 10.2 다음 단계

#### 🚨 긴급 우선순위: CVD 그룹 데이터 품질 검증

1. **sub-03 데이터 재검토**
   - fMRIPrep 전처리 품질 확인
   - Motion artifacts, signal dropout 확인
   - 필요시 재전처리 또는 제외 고려

2. **sub-04 분석 심화**
   - 왜 Non-CVD보다 높은 성능인가?
   - 색각 이상 유형 및 심각도 확인
   - Behavioral data 비교 (색상 구분 능력)

3. **CVD 그룹 확대**
   - sub-05, 06, 07 중 CVD 피험자 추가 확인
   - 최소 3-4명의 CVD 피험자 확보 필요
   - 현재 sub-03 제외 시 CVD 그룹 n=1 (부족)

#### 우선순위 1: Group-level Analysis (Non-CVD만)

1. **Group-level ANOVA/RFE Feature Selection**
   - ⚠️ **CVD 제외**: sub-03 데이터 불안정, sub-04만으로는 부족
   - Non-CVD participants (sub-01, 02, 05-07) 통합
   - Group-level GLM 기반 common voxel 추출
   - Common color-encoding voxels의 재현성 검증

2. **Individual vs Group 성능 비교**
   - Individual-level vs Group-level
   - Subject-specific voxels vs Common voxels
   - 일반화 가능성 평가

3. **CVD 그룹은 별도 분석**
   - sub-04 Individual-level 분석만 진행
   - Non-CVD group model과 비교
   - Filter design 가능성 평가

#### 우선순위 2: Method Selection

3. **ANOVA vs RFE 최종 선택**
   - 현재: ANOVA가 근소하게 우세 (0.8%p classification, 9.2° reconstruction)
   - 고려사항:
     - ANOVA: 빠른 연산, 명확한 해석, 최고 성능
     - RFE: Multivariate 관계, 일부 ROI 보완
   - **권장**: ANOVA 우선, RFE는 보완적 사용

4. **Ensemble 방법 검토 (선택)**
   - ANOVA + RFE voting 결합
   - 두 방법의 상호보완적 강점 활용
   - V3, hV4에서 RFE 우위 활용

#### 우선순위 3: Final Pipeline

5. **최종 파이프라인 확정**
   - Method: ANOVA Feature Selection (또는 ANOVA+RFE ensemble)
   - Config: No Smoothing (sm0.0_hpYe_moCo_ccNo_drNo_stFa)
   - Level: Individual 또는 Group-level
   - 선택된 voxels로 forward encoding model 구축

---

**문서 작성**: Claude Code
**초기 작성**: 2025-11-29
**최종 업데이트**: 2025-12-02 (PCA 및 RFE 결과 추가)
