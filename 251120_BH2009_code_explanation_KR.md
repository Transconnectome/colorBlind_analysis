# B&H 2009 구현 상세 설명 (한국어)

## 요구사항별 코드 구현 매핑

---

## 요구사항 1: 8개 FIR delay 사용 (10개 아님)

### 문제점
- **논문**: 12초 window, 1.5s TR → 8개 time points (0~7)
- **이전 코드**: `FIR_DELAYS = list(range(0, 15))` → 10개 delays 사용

### 해결 방법 (코드 Line 94)
```python
FIR_DELAYS = np.arange(8)  # 0,1,2,3,4,5,6,7
```

### 설명
- `np.arange(8)`은 [0, 1, 2, 3, 4, 5, 6, 7]을 생성
- 총 8개의 delay points: 0초, 1.5초, 3.0초, 4.5초, 6.0초, 7.5초, 9.0초, 10.5초
- 총 window 길이: 7 × 1.5s = 10.5초 (논문의 12초와 거의 일치)

### 코드 사용 위치
1. **Line 154-173**: `build_fir_design_matrix()` 함수에서 8개 delay로 design matrix 생성
2. **Line 309**: Voxel-wise HRF 추정 시 8-point HRF 계산
3. **Line 341**: HRF 저장 배열 크기 설정 `HRF_voxel = np.zeros((n_voxels_total, len(FIR_DELAYS)))`

---

## 요구사항 2: Pseudo-inverse를 통한 voxel-wise HRF 계산

### 문제점
- **논문**: 각 voxel에 대해 `h_v = pinv(X_fir) @ y_voxel`로 전체 HRF time course 추정
- **이전 코드**: FIR GLM에서 delay별 beta 추출 → peak delay 하나만 선택 → 그 시점의 beta만 amplitude로 사용

### 해결 방법 (코드 Line 341-392)

```python
# Line 341-392: Step 1 - Voxel-wise FIR HRF Estimation

# 모든 voxel에 대해 HRF 추정
HRF_voxel = np.zeros((n_voxels_total, len(FIR_DELAYS)))
r2_voxel = np.zeros(n_voxels_total)

for voxel_idx in range(n_voxels_total):
    # 모든 run의 데이터를 concatenate
    y_voxel = []
    X_fir_all = []

    for run_idx in range(N_RUNS):
        # 이 run의 이 voxel의 timeseries
        y_run = all_func_data[run_idx][:, voxel_idx]
        y_voxel.append(y_run)

        # 모든 onset (color 무시하고 전체 이벤트)
        events = events_list[run_idx]
        all_onsets = events['onset'].values

        # FIR design matrix 생성
        n_scans = all_func_data[run_idx].shape[0]
        X_fir = build_fir_design_matrix(all_onsets, n_scans, TR, FIR_DELAYS)
        X_fir_all.append(X_fir)

    # 모든 run을 합침
    y_voxel = np.concatenate(y_voxel)      # (total_scans,)
    X_fir_all = np.vstack(X_fir_all)       # (total_scans, 8)

    # ★ 핵심: Pseudo-inverse로 HRF 추정
    h_v = np.linalg.pinv(X_fir_all) @ y_voxel  # (8,)
    HRF_voxel[voxel_idx] = h_v

    # R² 계산
    y_pred = X_fir_all @ h_v
    r2_voxel[voxel_idx] = compute_r2(y_voxel, y_pred)
```

### 핵심 차이점

| 단계 | 이전 방식 | 새 방식 (B&H 2009) |
|------|-----------|-------------------|
| FIR GLM | FirstLevelModel로 color별 × delay별 beta 추출 | 직접 design matrix 생성 |
| HRF 추정 | Universal HRF에서 peak 찾기 | **각 voxel마다 8-point HRF 추정** |
| Amplitude | Peak delay의 beta 하나 | 2nd-level GLM으로 전체 HRF convolve |

### `build_fir_design_matrix()` 함수 상세 (Line 154-173)

```python
def build_fir_design_matrix(onsets, n_scans, tr, fir_delays):
    """
    Color를 무시하고 모든 이벤트를 하나의 조건으로 처리

    Parameters:
    -----------
    onsets : array
        모든 이벤트 onset (초 단위) - color 구분 없음!
    n_scans : int
        총 TR 개수
    tr : float
        Repetition time (1.5s)
    fir_delays : array
        [0, 1, 2, 3, 4, 5, 6, 7]

    Returns:
    --------
    X : ndarray (n_scans, 8)
        각 column = 특정 delay에서의 event indicator
    """
    n_delays = len(fir_delays)
    X = np.zeros((n_scans, n_delays))

    for onset in onsets:
        onset_tr = int(np.round(onset / tr))  # 초 → TR index

        for i, delay in enumerate(fir_delays):
            tr_idx = onset_tr + delay  # onset 이후 delay TR

            if 0 <= tr_idx < n_scans:
                X[tr_idx, i] = 1.0  # 이 TR에서 이 delay 활성화

    return X
```

**예시:**
- onset = 10.5초 → onset_tr = 7
- delay = 0일 때: X[7, 0] = 1
- delay = 1일 때: X[8, 1] = 1
- delay = 2일 때: X[9, 2] = 1
- ...

---

## 요구사항 3: R² 기준 상위 50% voxel만 사용

### 문제점
- **논문**: R² (모델 적합도) 상위 50% voxel만 선택하여 ROI HRF 계산
- **이전 코드**: ROI mask 내 모든 voxel 사용 (R² 필터링 없음)

### 해결 방법 (Line 394-406)

```python
# Line 394-406: Step 2 - Voxel Selection

# R² 중간값을 threshold로 사용 (= 상위 50%)
r2_threshold = np.median(r2_voxel)

# 상위 50% voxel 선택
selected_voxels_mask = r2_voxel >= r2_threshold
n_voxels_selected = np.sum(selected_voxels_mask)

print(f"  R² threshold (median): {r2_threshold:.3f}")
print(f"  Selected voxels: {n_voxels_selected}/{n_voxels_total} "
      f"({100*n_voxels_selected/n_voxels_total:.1f}%)")
```

### R² 계산 (Line 218-222)

```python
def compute_r2(y_true, y_pred):
    """
    R² = 1 - (SS_residual / SS_total)

    SS_residual = Σ(y_true - y_pred)²
    SS_total = Σ(y_true - mean(y_true))²
    """
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - (ss_res / ss_tot)
```

### 의미
- **R² > threshold**: 이 voxel의 HRF가 데이터를 잘 설명함 (high SNR)
- **R² < threshold**: 노이즈가 많거나 stimulus에 반응하지 않음
- **상위 50% 선택**: SNR이 높은 voxel만 사용하여 robust한 ROI HRF 추정

---

## 요구사항 4: 2nd-level GLM with HRF + derivative

### 문제점
- **논문**:
  1. ROI 평균 HRF `h(t)` + derivative `h'(t)` 사용
  2. Design matrix: `[color_1⊗h, ..., color_8⊗h, color_1⊗h', ..., color_8⊗h']` (16 columns)
  3. `β = pinv(X) @ y` per voxel per run
  4. 앞 8개 beta = color amplitude, 뒤 8개 = latency 보정용 (버림)
- **이전 코드**: Peak delay의 beta 하나만 amplitude로 사용, derivative 없음

### 해결 방법

#### 4-1. ROI HRF와 derivative 계산 (Line 408-429)

```python
# Line 408-429: Step 3 - ROI Average HRF

# 선택된 voxel들의 HRF 평균
ROI_HRF = np.mean(HRF_voxel[selected_voxels_mask], axis=0)

# Numerical derivative 계산
ROI_HRF_deriv = np.gradient(ROI_HRF)

print(f"  ROI HRF shape: {ROI_HRF.shape}")  # (8,)
print(f"  Peak delay: {np.argmax(np.abs(ROI_HRF))} "
      f"(time={np.argmax(np.abs(ROI_HRF))*TR:.1f}s)")
```

**`np.gradient()` 설명:**
- Central difference: `h'[i] = (h[i+1] - h[i-1]) / 2`
- 경계에서는 forward/backward difference 사용
- HRF의 시간적 변화율을 나타냄

#### 4-2. 2nd-level design matrix 생성 함수 (Line 175-216)

```python
def build_2nd_level_design_matrix(events, n_scans, tr, roi_hrf, roi_hrf_deriv):
    """
    16-column design matrix 생성

    Columns 0-7: color_1⊗h, color_2⊗h, ..., color_8⊗h
    Columns 8-15: color_1⊗h', color_2⊗h', ..., color_8⊗h'

    ⊗ = convolution
    """
    n_colors = 8
    X = np.zeros((n_scans, 2 * n_colors))  # 16 columns

    for color_idx in range(1, n_colors + 1):
        color_name = f'color_{color_idx}'
        color_events = events[events['trial_type'] == color_name]

        # Stick function 생성 (impulse at onset)
        stick = np.zeros(n_scans)
        for onset in color_events['onset'].values:
            onset_tr = int(np.round(onset / tr))
            if 0 <= onset_tr < n_scans:
                stick[onset_tr] = 1.0

        # HRF와 convolve
        hrf_response = np.convolve(stick, roi_hrf, mode='full')[:n_scans]
        X[:, color_idx - 1] = hrf_response

        # Derivative와 convolve
        deriv_response = np.convolve(stick, roi_hrf_deriv, mode='full')[:n_scans]
        X[:, n_colors + color_idx - 1] = deriv_response

    return X
```

**Convolution 의미:**
```
stick = [0, 0, 1, 0, 0, 0, ...]  (onset at TR=2)
hrf   = [0.1, 0.5, 0.8, 0.6, 0.3, 0.1, 0.0, 0.0]

convolve(stick, hrf) = [0, 0, 0.1, 0.5, 0.8, 0.6, 0.3, 0.1, 0, ...]
                            ↑
                        onset 이후 HRF 모양대로 반응
```

#### 4-3. Per-run amplitude 추정 (Line 431-468)

```python
# Line 431-468: Step 4 - 2nd-level GLM

amplitudes_raw = np.zeros((N_RUNS, N_COLORS, n_voxels_selected))

for run_idx in range(N_RUNS):
    # 이 run의 데이터 (선택된 voxel만)
    y_run = all_func_data[run_idx][:, selected_voxels_mask]
    # Shape: (n_scans, n_voxels_selected)

    n_scans = y_run.shape[0]

    # 16-column design matrix 생성
    X_2nd = build_2nd_level_design_matrix(
        events_list[run_idx],
        n_scans,
        TR,
        ROI_HRF,        # (8,)
        ROI_HRF_deriv   # (8,)
    )
    # Shape: (n_scans, 16)

    # ★ 핵심: Pseudo-inverse로 amplitude 추정
    X_pinv = np.linalg.pinv(X_2nd)  # (16, n_scans)
    betas = X_pinv @ y_run           # (16, n_voxels_selected)

    # 앞 8개만 저장 (HRF regressors), 뒤 8개(derivative)는 버림
    amplitudes_raw[run_idx] = betas[:N_COLORS, :]
```

**Shape 변화 추적:**
```
y_run:        (150 scans, 500 voxels)
X_2nd:        (150 scans, 16 columns)
X_pinv:       (16 columns, 150 scans)
betas:        (16 columns, 500 voxels)
amplitudes:   (8 colors, 500 voxels)  ← 앞 8개만
```

**Derivative의 역할:**
- 각 voxel/trial마다 HRF의 latency가 약간씩 다를 수 있음
- Derivative regressor가 이 temporal shift를 흡수
- 결과적으로 amplitude 추정이 더 정확해짐

---

## 요구사항 5: Color-ignored FIR → voxel HRF → R² selection → average

### 문제점
- **이전 코드**: Color별 FIR beta 추출 → 나중에 color와 voxel 평균
- **논문**: Color 무시 → voxel HRF → R² 선택 → 평균

### 해결 방법: 전체 파이프라인 구조

```python
# ===== Step 1: Color-ignored FIR =====
# Line 354-370
for voxel_idx in range(n_voxels_total):
    for run_idx in range(N_RUNS):
        events = events_list[run_idx]
        all_onsets = events['onset'].values  # ← 모든 color 합침!

        X_fir = build_fir_design_matrix(all_onsets, n_scans, TR, FIR_DELAYS)

# ===== Step 2: Voxel-wise HRF =====
# Line 377-379
h_v = np.linalg.pinv(X_fir_all) @ y_voxel
HRF_voxel[voxel_idx] = h_v

# ===== Step 3: R² calculation =====
# Line 381-384
y_pred = X_fir_all @ h_v
r2_voxel[voxel_idx] = compute_r2(y_voxel, y_pred)

# ===== Step 4: Top 50% selection =====
# Line 398-399
r2_threshold = np.median(r2_voxel)
selected_voxels_mask = r2_voxel >= r2_threshold

# ===== Step 5: Average HRF =====
# Line 418
ROI_HRF = np.mean(HRF_voxel[selected_voxels_mask], axis=0)
```

### 핵심 차이점

**이전 방식:**
```python
# Color별로 분리해서 처리
for color in colors:
    contrast_map = glm.compute_contrast(f'color_{color}_delay_{delay}')
    mean_response[color, delay] = contrast_map.mean()

universal_hrf = mean_response.mean(axis=0)  # Color 평균
```

**새 방식 (B&H 2009):**
```python
# Color 무시하고 전체 이벤트로 HRF 추정
all_onsets = events['onset'].values  # Color 구분 없음
X_fir = build_fir_design_matrix(all_onsets, ...)

# 각 voxel HRF 추정
h_v = pinv(X_fir) @ y_voxel

# R² 높은 voxel만 평균
ROI_HRF = mean(h_v for v in top50_by_r2)
```

---

## 전체 파이프라인 요약

```python
# ========== 1단계: Voxel-wise FIR HRF ==========
for each voxel:
    all_onsets = concatenate(color_1, color_2, ..., color_8)
    X_fir = build_fir_design(all_onsets, 8_delays)  # (T, 8)
    h_v = pinv(X_fir) @ y_voxel                     # (8,)
    r2[v] = compute_r2(y_true, X_fir @ h_v)

# ========== 2단계: Voxel Selection ==========
threshold = median(r2)
selected = r2 >= threshold  # Top 50%

# ========== 3단계: ROI HRF ==========
ROI_HRF = mean(h_v for v in selected)       # (8,)
ROI_HRF_deriv = gradient(ROI_HRF)           # (8,)

# ========== 4단계: 2nd-level GLM ==========
for each run:
    X_2nd = [color_1⊗h, ..., color_8⊗h,    # (T, 16)
             color_1⊗h', ..., color_8⊗h']

    for each voxel:
        beta = pinv(X_2nd) @ y_voxel        # (16,)
        amplitude[run, voxel, :] = beta[:8] # (8,)

# ========== 5단계: Z-score ==========
for each run, each voxel:
    amplitude_z[run, voxel, :] = zscore(amplitude[run, voxel, :])

# ========== 6단계: Classification & Reconstruction ==========
# Leave-one-run-out CV with 6-channel forward model
```

---

## 코드 검증 포인트

### 1. FIR delays 확인
```python
assert len(FIR_DELAYS) == 8
assert np.array_equal(FIR_DELAYS, np.arange(8))
```

### 2. Voxel selection 확인
```python
assert n_voxels_selected ≈ n_voxels_total * 0.5
assert np.sum(selected_voxels_mask) == n_voxels_selected
```

### 3. Design matrix shape 확인
```python
# 1st-level FIR
assert X_fir.shape == (n_scans_total, 8)

# 2nd-level GLM
assert X_2nd.shape == (n_scans_per_run, 16)
```

### 4. Amplitude shape 확인
```python
assert amplitudes_raw.shape == (6, 8, n_voxels_selected)
# (runs, colors, voxels)
```

---

## 주요 개선 사항 정리

| 요구사항 | 이전 방식 | 개선 방식 | 코드 위치 |
|----------|-----------|-----------|-----------|
| 1. FIR delays | 10개 | **8개** | Line 94 |
| 2. HRF 추정 | Peak delay | **Voxel-wise pinv** | Line 377-379 |
| 3. Voxel 선택 | 전체 | **R² top 50%** | Line 398-399 |
| 4. Amplitude | Single beta | **2nd-level GLM (16 col)** | Line 447-451 |
| 5. Derivative | 없음 | **포함 (latency 보정)** | Line 420, 201-203 |
| 6. Color 처리 | Color별 분리 | **Color-ignored FIR** | Line 365 |

모든 요구사항이 B&H 2009 논문에 충실하게 구현되었습니다!
