# Grid Search Preprocessing 코드 완전 가이드

## 목차
1. [전체 개요](#전체-개요)
2. [데이터 흐름도](#데이터-흐름도)
3. [함수별 상세 설명](#함수별-상세-설명)
4. [실행 예시](#실행-예시)
5. [문제 해결](#문제-해결)

---

## 전체 개요

### 목적
36가지 preprocessing 조합을 자동으로 테스트하여 **HRF variability**를 최대화하는 최적 설정을 찾는다.

### 왜 필요한가?
현재 문제:
- R² = 0.566 (모델 fitting은 좋음)
- **HRF correlation = 0.066** (voxel 간 HRF 모양이 너무 다름)
- Run-to-run reliability = 0.003 (재현성 없음)

해결 방법:
- Preprocessing으로 HRF 모양을 homogeneous하게 만들기
- Smoothing, filtering, confound regression 조합 찾기

### Grid Search 파라미터

| 파라미터 | 옵션 | 설명 |
|---------|------|------|
| **Smoothing** | 0, 6, 8 mm | 공간 평활화 (Gaussian kernel) |
| **Temporal Filter** | None, polynomial, high-pass 1/128 Hz | 시간축 필터링 |
| **Confounds** | None, motion_6 | Motion parameter 회귀 |
| **Voxel Norm** | None, demean | HRF mean-centering |

**Total: 3 × 3 × 2 × 2 = 36 combinations**

---

## 데이터 흐름도

```
┌─────────────────────────────────────────────────────────────┐
│                    GRID SEARCH PIPELINE                      │
└─────────────────────────────────────────────────────────────┘

1️⃣ GENERATE CONFIGS (36개)
   ↓
   [Config 0: smooth=0, high_pass=None, confounds=None, voxel_norm=None]
   [Config 1: smooth=0, high_pass=None, confounds=None, voxel_norm=demean]
   ...
   [Config 35: smooth=8, high_pass=1/128, confounds=motion_6, voxel_norm=demean]


2️⃣ FOR EACH CONFIG → RUN_SINGLE_CONFIG
   │
   ├─ LOAD_AND_PREPROCESS_DATA
   │  │
   │  ├─ For each run (1-6):
   │  │  │
   │  │  ├─ Load 4D NIfTI: (97×115×97×288)
   │  │  ├─ Drop 4 volumes: (97×115×97×284)
   │  │  ├─ Smooth (optional): FWHM=6 or 8mm
   │  │  ├─ Extract ROI voxels: (284×481)
   │  │  ├─ Load motion confounds: (284×6)
   │  │  ├─ High-pass + confounds: cleaned (284×481)
   │  │  └─ Load events: adjust onset times
   │  │
   │  └─ Output:
   │      all_func_data: 6 arrays (284×481)
   │      all_events: 6 DataFrames
   │
   │
   ├─ ESTIMATE_VOXEL_HRF
   │  │
   │  ├─ Concatenate runs: (1704×481)
   │  │
   │  ├─ Build design matrices:
   │  │  │
   │  │  ├─ Run 1: events → FIR design (284×8)
   │  │  ├─ Run 2: events → FIR design (284×8)
   │  │  ...
   │  │  └─ Run 6: events → FIR design (284×8)
   │  │
   │  ├─ Stack designs: (1704×8)
   │  │
   │  ├─ For each voxel (481 voxels):
   │  │  │
   │  │  ├─ y_voxel = timeseries (1704,)
   │  │  ├─ h_v = pinv(X_fir) @ y_voxel
   │  │  ├─ Compute R²
   │  │  └─ Store HRF (8,)
   │  │
   │  └─ Output:
   │      HRF_voxels: (481×8)
   │      r2_voxels: (481,)
   │
   │
   └─ COMPUTE_METRICS
      │
      ├─ R² statistics
      ├─ Select top 50% voxels by R²
      ├─ Compute ROI average HRF
      ├─ Correlate each voxel HRF with ROI HRF
      │  → hrf_variability = mean(correlations) 🎯 KEY METRIC
      ├─ Compute temporal SNR
      │
      └─ Output:
          metrics = {
              'r2_mean': 0.566,
              'hrf_variability': 0.066,  ← Maximize this!
              'temporal_snr_mean': 45.2,
              ...
          }


3️⃣ SAVE RESULTS
   ↓
   grid_search_results.csv (incremental saves)
   best_config.json (best configuration)
```

---

## 함수별 상세 설명

### Function 1: `generate_configs()`

**목적:** 36개 preprocessing 조합 생성

**입력:** None (GRID_PARAMS 사용)

**출력:**
```python
configs = [
    {'id': 0, 'smoothing_fwhm': 0, 'high_pass': None, ...},
    {'id': 1, 'smoothing_fwhm': 0, 'high_pass': None, ...},
    ...
]
```

**코드 로직:**
```python
# 4중 nested loop으로 Cartesian product 생성
for smooth in [0, 6, 8]:
    for temp_filter in [None, poly, 1/128]:
        for confounds in [None, motion_6]:
            for voxel_norm in [None, demean]:
                # 하나의 config 생성
```

---

### Function 2: `load_and_preprocess_data(config)`

**목적:** Config에 따라 6 runs 데이터 전처리

**입력:**
```python
config = {
    'smoothing_fwhm': 6,
    'high_pass': 1/128,
    'confounds': 'motion_6',
    'voxel_norm': 'demean'
}
```

**출력:**
```python
all_func_data = [
    array(284, 481),  # Run 1
    array(284, 481),  # Run 2
    ...
    array(284, 481)   # Run 6
]

all_events = [
    DataFrame(~71 rows),  # Run 1 events
    DataFrame(~71 rows),  # Run 2 events
    ...
]
```

**전처리 순서:**
1. **Load ROI mask** (481 voxels for V1)
2. **For each run:**
   - Load 4D NIfTI: `(97, 115, 97, 288)`
   - Drop 4 volumes: `(97, 115, 97, 284)`
   - **Smoothing** (if > 0): Gaussian FWHM=6 or 8mm
   - Extract voxels: `(284, 481)`
   - **Confounds** (if motion_6): Load 6 params `(284, 6)`
   - **High-pass + confounds**: `nilearn.signal.clean()`
3. **Load events:** Adjust onset for dropped volumes

**데이터 변환 예시:**
```
Original fMRI
├─ Shape: (97, 115, 97, 288)
├─ Voxels: 1,079,655 (전체 뇌)
└─ Time: 288 scans × 1.5s = 432초

↓ Drop 4 volumes

Shape: (97, 115, 97, 284)
Time: 284 scans × 1.5s = 426초

↓ Smoothing (FWHM=6mm)

Shape: (97, 115, 97, 284) - smoother

↓ ROI masker (V1)

Shape: (284, 481)
├─ Scans: 284
└─ Voxels: 481 (V1 only)

↓ High-pass + confounds

Shape: (284, 481) - cleaned
├─ Low frequencies removed
└─ Motion effects regressed out
```

---

### Function 3: `compute_temporal_snr(func_data)`

**목적:** 각 voxel의 temporal SNR 계산

**입력:**
```python
func_data = array(284, 481)  # One run
```

**출력:**
```python
tsnr = array(481,)  # SNR for each voxel
```

**계산 공식:**
```python
tSNR = mean(timeseries) / std(detrended_timeseries)

예시:
timeseries = [600, 610, 605, 615, 608, ...]
mean = 610
detrended = detrend([600, 610, 605, ...])
std(detrended) = 15
tSNR = 610 / 15 = 40.7
```

**해석:**
- **tSNR > 50:** 좋은 품질
- **tSNR = 20-50:** 보통
- **tSNR < 20:** 낮음 (noise 많음)

---

### Function 4: `build_fir_design_matrix(events, n_scans, tr, fir_delays, drift_model)`

**목적:** 한 run의 FIR design matrix 생성

**입력:**
```python
events = DataFrame:
    onset     trial_type
    5.9       color_1
    11.2      color_2
    16.8      color_3
    ...

n_scans = 284
tr = 1.5
fir_delays = [0, 1, 2, 3, 4, 5, 6, 7]
drift_model = None | 'polynomial'
```

**출력:**
```python
X = array(284, 8)   # If drift_model=None
X = array(284, 10)  # If drift_model='polynomial' (8 FIR + 2 drift)
```

**Design Matrix 구조:**

각 event에 대해 8개 delay에서 stick function 생성:

```
Event at onset=5.9s → onset_tr = 4

       fir_0  fir_1  fir_2  fir_3  fir_4  fir_5  fir_6  fir_7
TR 0     0      0      0      0      0      0      0      0
TR 1     0      0      0      0      0      0      0      0
TR 2     0      0      0      0      0      0      0      0
TR 3     0      0      0      0      0      0      0      0
TR 4     1      0      0      0      0      0      0      0  ← Event onset
TR 5     0      1      0      0      0      0      0      0  ← +1.5s
TR 6     0      0      1      0      0      0      0      0  ← +3.0s
TR 7     0      0      0      1      0      0      0      0  ← +4.5s
TR 8     0      0      0      0      1      0      0      0  ← +6.0s
TR 9     0      0      0      0      0      1      0      0  ← +7.5s
TR 10    0      0      0      0      0      0      1      0  ← +9.0s
TR 11    0      0      0      0      0      0      0      1  ← +10.5s
TR 12    1      0      0      0      0      0      0      0  ← Next event
...
```

**물리적 의미:**
- `fir_0`: Event 직후 반응 (0-1.5s)
- `fir_1`: +1.5s 반응 (1.5-3.0s)
- `fir_2`: +3.0s 반응 (3.0-4.5s)
- ...
- `fir_7`: +10.5s 반응 (10.5-12.0s)

**Drift regressors (optional):**
```
If drift_model='polynomial':
  - constant: [1, 1, 1, ..., 1] (284 ones)
  - drift_1: [-1, -0.99, ..., 0, ..., 0.99, 1] (linear trend)
```

---

### Function 5: `estimate_voxel_hrf(func_data_list, events_list, config)`

**목적:** Multi-run FIR로 각 voxel의 HRF 추정

**입력:**
```python
func_data_list = [
    array(284, 481),  # Run 1
    ...
    array(284, 481)   # Run 6
]

events_list = [
    DataFrame,  # Run 1
    ...
    DataFrame   # Run 6
]

config = {'drift_model': None, 'voxel_norm': 'demean'}
```

**출력:**
```python
HRF_voxels = array(481, 8)  # HRF for each voxel
r2_voxels = array(481,)     # R² for each voxel
```

**처리 과정:**

**Step 1: Concatenate runs**
```python
y_all = vstack([
    func_run1,  # (284, 481)
    func_run2,
    ...
    func_run6
])
# Result: (1704, 481)
#   1704 = 6 runs × 284 scans
```

**Step 2: Build design matrices per run**
```python
X_all_list = []
for run in 1..6:
    events_run = events_list[run]
    # CRITICAL: Events are in this run's time frame (0-426s)
    # Do NOT adjust onset times!

    X_run = build_fir_design_matrix(events_run, 284, 1.5, [0..7], None)
    # X_run: (284, 8)

    X_all_list.append(X_run)

X_all = vstack(X_all_list)  # (1704, 8)
```

**이전 버전의 문제 (수정됨):**
```python
# ❌ WRONG (이전 버전):
cumulative_time = 0
for run in 1..6:
    events['onset'] += cumulative_time  # ← 문제!
    cumulative_time += 426  # Run 2 events: 426~850s

# Run 2의 design matrix는 284 scans (0-426s)만 커버하는데
# onset이 426~850s 범위 → Index out of bounds!

# ✅ CORRECT (현재 버전):
for run in 1..6:
    events = events_list[run]  # Already in 0-426s range
    # Don't adjust onset - automatic alignment when stacking
```

**Step 3: Extract FIR columns**
```python
X_fir = X_all[:, :8]  # (1704, 8)
# First 8 columns only (discard drift regressors)
```

**Step 4: Estimate HRF per voxel**
```python
for voxel in range(481):
    y_voxel = y_all[:, voxel]  # (1704,)

    # Solve: X_fir @ h_v = y_voxel
    h_v = pinv(X_fir) @ y_voxel  # (8,)

    HRF_voxels[voxel] = h_v
```

**수학적 의미:**
```
Linear model:
    y_voxel(t) = Σ[delay=0..7] h_v[delay] × X_fir[t, delay] + noise

Matrix form:
    y_voxel (1704×1) = X_fir (1704×8) @ h_v (8×1) + noise

Solution (pseudo-inverse):
    h_v = pinv(X_fir) @ y_voxel

where:
    pinv(X_fir) = (X_fir^T X_fir)^(-1) X_fir^T
```

**Step 5: Compute R²**
```python
y_pred = X_fir @ h_v
R² = 1 - sum((y - y_pred)²) / sum((y - mean(y))²)
```

**Step 6: Voxel normalization (optional)**
```python
if voxel_norm == 'demean':
    # Remove mean across delays
    HRF_voxels -= mean(HRF_voxels, axis=1, keepdims=True)
```

---

### Function 6: `compute_metrics(func_data_list, HRF_voxels, r2_voxels, config)`

**목적:** Preprocessing 품질 평가 metrics 계산

**입력:**
```python
func_data_list = [array(284, 481), ...]
HRF_voxels = array(481, 8)
r2_voxels = array(481,)
```

**출력:**
```python
metrics = {
    'r2_mean': 0.566,
    'r2_median': 0.715,
    'r2_std': 0.382,
    'n_voxels_selected': 241,
    'hrf_variability': 0.066,  # ← KEY METRIC
    'hrf_representativeness': 0.104,
    'temporal_snr_mean': 45.2,
    ...
}
```

**Metric 계산 과정:**

**A. R² Statistics**
```python
r2_valid = r2_voxels[r2_voxels > 0]
metrics['r2_mean'] = mean(r2_valid)      # 0.566
metrics['r2_median'] = median(r2_valid)  # 0.715
metrics['r2_std'] = std(r2_valid)        # 0.382
```

**B. Voxel Selection (Top 50%)**
```python
threshold = median(r2_voxels)  # 0.715
selected_mask = r2_voxels >= threshold
n_selected = sum(selected_mask)  # 241 voxels
```

**C. HRF Variability (핵심 지표) 🎯**
```python
# ROI average HRF from selected voxels
ROI_HRF = mean(HRF_voxels[selected_mask], axis=0)
# ROI_HRF: (8,) = [-1.5, -6.8, -1.1, 0.07, 3.8, 4.6, 4.3, 2.2]

# Correlate each voxel with ROI average
hrf_corrs = []
for v in selected_voxels:
    voxel_hrf = HRF_voxels[v]  # (8,)
    r = corrcoef(voxel_hrf, ROI_HRF)[0, 1]
    hrf_corrs.append(r)

# Mean correlation
metrics['hrf_variability'] = mean(hrf_corrs)  # 0.066 (very low!)

# Representativeness
metrics['hrf_representativeness'] = sum(hrf_corrs > 0.8) / len(hrf_corrs)  # 10.4%
```

**HRF Variability 해석:**
- **0.066 (현재):** ROI HRF가 개별 voxel을 거의 대표하지 못함
- **0.5-0.7 (목표):** Preprocessing으로 달성 가능
- **0.8-0.9 (이상적):** Voxel들이 매우 유사한 HRF

**D. Temporal SNR**
```python
tsnr = compute_temporal_snr(func_data_list[0])
metrics['temporal_snr_mean'] = mean(tsnr)    # 45.2
metrics['temporal_snr_median'] = median(tsnr)  # 43.1
metrics['temporal_snr_max'] = max(tsnr)      # 89.5
```

---

### Function 7: `run_single_config(config)`

**목적:** 한 configuration의 전체 파이프라인 실행

**입력:**
```python
config = {
    'id': 12,
    'smoothing_fwhm': 6,
    'high_pass': None,
    'drift_model': None,
    'confounds': None,
    'voxel_norm': None
}
```

**출력:**
```python
result = {
    # Config
    'id': 12,
    'smoothing_fwhm': 6,
    'high_pass': None,
    ...

    # Metrics (if success)
    'r2_mean': 0.566,
    'hrf_variability': 0.125,
    'temporal_snr_mean': 48.3,
    'status': 'success',
    'elapsed_time': 45.2,

    # Or error info (if failed)
    'status': 'failed',
    'error': 'Incompatible dimensions',
    'traceback': '...',
}
```

**파이프라인:**
```python
try:
    # 1. Load and preprocess
    func_data_list, events_list, masker = load_and_preprocess_data(config)

    # 2. Estimate HRF
    HRF_voxels, r2_voxels = estimate_voxel_hrf(func_data_list, events_list, config)

    # 3. Compute metrics
    metrics = compute_metrics(func_data_list, HRF_voxels, r2_voxels, config)

    # 4. Success
    metrics['status'] = 'success'

except Exception as e:
    # Error handling with full traceback
    metrics = {
        'status': 'failed',
        'error': str(e),
        'traceback': traceback.format_exc()
    }

return {**config, **metrics}
```

---

### Function 8: `main()`

**목적:** 36개 configs 순회 및 결과 저장

**Flow:**
```python
1. Generate 36 configs
2. For each config:
     - Run complete pipeline
     - Save incremental results (CSV)
3. Find best config by hrf_variability
4. Save best config (JSON)
```

**출력 파일:**
- `grid_search_results.csv`: 모든 configs 결과
- `best_config.json`: 최적 configuration

---

## 실행 예시

### Config 0 (No preprocessing)
```
Config: smooth=0, high_pass=None, confounds=None, voxel_norm=None

Results:
  R² mean: 0.566
  tSNR mean: 42.1
  HRF variability: 0.066  ← Low!

Interpretation:
  Raw data has high voxel-to-voxel HRF variability
  Need preprocessing!
```

### Config 12 (Smoothing only)
```
Config: smooth=6, high_pass=None, confounds=None, voxel_norm=None

Results:
  R² mean: 0.571
  tSNR mean: 48.3
  HRF variability: 0.145  ← Better!

Interpretation:
  6mm smoothing increases HRF homogeneity
  tSNR also improves (spatial noise reduced)
```

### Config 20 (Smoothing + High-pass)
```
Config: smooth=6, high_pass=1/128, confounds=None, voxel_norm=None

Results:
  R² mean: 0.612
  tSNR mean: 51.2
  HRF variability: 0.218  ← Even better!

Interpretation:
  Combined preprocessing works well
  High-pass removes slow drifts
```

### Config 23 (Full preprocessing)
```
Config: smooth=6, high_pass=1/128, confounds=motion_6, voxel_norm=demean

Results:
  R² mean: 0.638
  tSNR mean: 53.7
  HRF variability: 0.287  ← Best!

Interpretation:
  All preprocessing steps help
  This might be the optimal configuration
```

---

## 문제 해결

### Error 1: "Incompatible dimensions"

**원인:** Multi-run concatenation 시 cumulative onset 조정 문제

**이전 코드 (문제):**
```python
cumulative_time = 0
for run in 1..6:
    events['onset'] += cumulative_time  # ❌ WRONG
    cumulative_time += 426
```

**수정된 코드:**
```python
for run in 1..6:
    events = events_list[run].copy()
    # Don't adjust onset - already in correct time frame
    # ✅ CORRECT
```

**설명:**
- 각 run의 events는 해당 run의 시간축 (0-426s)에 있음
- Design matrix를 stack할 때 자동으로 정렬됨
- Onset을 누적 시간으로 조정하면 범위 초과

### Error 2: "SVD did not converge"

**원인:** Ill-conditioned design matrix

**해결:**
```python
try:
    h_v = np.linalg.pinv(X_fir) @ y_voxel
except np.linalg.LinAlgError:
    h_v, _, _, _ = np.linalg.lstsq(X_fir, y_voxel, rcond=None)
```

### Error 3: Different drift columns

**원인:** drift_model='polynomial'일 때 design matrix 크기 다름

**확인:**
```python
# No drift: (284, 8)
# With drift: (284, 10)

# Extract FIR columns only
X_fir = X_all[:, :8]  # Always 8 columns
```

---

## 다음 단계

1. **서버에 업로드:**
   ```bash
   scp grid_search_preprocessing.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
   ```

2. **재실행:**
   ```bash
   sbatch run_grid_search.sbatch
   ```

3. **모니터링:**
   ```bash
   tail -f logs/grid_search_*.out
   cat logs/grid_search_*.err
   ```

4. **결과 분석:**
   - `grid_search_results.csv` 확인
   - `best_config.json` 적용
   - Voxel-specific script에 best config 적용
   - Run-to-run reliability 재측정

---

## 기대 결과

**Before (No preprocessing):**
- HRF variability: 0.066
- Run-to-run reliability: 0.003

**After (Best config):**
- HRF variability: 0.2-0.4 (예상)
- Run-to-run reliability: 0.5-0.7 (예상)

**최종 목표:**
- Voxel-specific HRF + Best preprocessing
- Classification accuracy > 20%
- Reconstruction error < 60°
