# B&H 2009 구현 완성 및 향상된 분석 요약

## 작업 완료 사항

### 1. 기본 요구사항 구현 ✅

251120_perRun_editDirection.md의 모든 요구사항을 정확히 반영하여 `fir_reconstruction_BH2009.py`를 작성했습니다.

| 요구사항 | 구현 위치 | 설명 |
|---------|----------|------|
| **8개 FIR delay** | Line 94 | `FIR_DELAYS = np.arange(8)` |
| **Voxel-wise HRF 추정** | Line 377-379 | `h_v = np.linalg.pinv(X_fir) @ y_voxel` |
| **R² top 50% 선택** | Line 398-399 | `selected = r2_voxel >= median(r2)` |
| **2nd-level GLM** | Line 447-451 | 16-column design matrix (HRF + derivative) |
| **Color-ignored FIR** | Line 365 | `all_onsets = events['onset'].values` |

### 2. 추가 분석 및 시각화 ✅

사용자 요청에 따라 세 가지 주요 분석을 추가했습니다:

#### A. R² 분포 및 커트라인 분석 (Line 438-551)

**계산 지표:**
- R² 기본 통계량: mean, median, std, min, max
- Percentile 분석: 10th, 25th, 50th, 75th, 90th, 95th, 99th
- Good fit voxel 개수: R² > 0.1, 0.2, 0.3, 0.5

**시각화 (4-panel figure):**
1. **Histogram**: R² 분포, median (threshold) 및 mean 표시
2. **Cumulative distribution**: R² cutoff별 선택되는 voxel 비율
3. **Box plot**: 사분위수 및 outlier 표시
4. **Bar plot**: 다양한 threshold에서 선택되는 voxel 비율

**출력 파일:** `r2_distribution_analysis.png`

**해석 기준:**
```python
if r2_median > 0.3:
    "High quality HRF estimates"
elif r2_median > 0.2:
    "Moderate quality"
else:
    "Low quality - consider data quality issues"
```

#### B. ROI HRF와 개별 voxel HRF 차이 분석 (Line 621-801)

**계산 지표:**
- **Correlation**: 각 voxel HRF와 ROI HRF 간 Pearson correlation
- **RMSE**: Root Mean Square Error
- **Normalized RMSE**: RMSE / std(voxel HRF)
- **Representativeness**: r > 0.8, r > 0.9 voxel 비율

**시각화 (6-panel figure):**
1. **Individual HRFs overlay**: 100개 voxel + ROI mean + ±1 SD envelope
2. **Correlation distribution**: voxel-to-ROI correlation histogram
3. **RMSE distribution**: deviation 크기 분포
4. **Per-timepoint variability**: 각 delay에서 mean ± SD
5. **Correlation vs R²**: HRF similarity와 model quality 관계
6. **Best vs Worst voxels**: 가장 잘/못 맞는 voxel 5개씩 표시

**출력 파일:** `hrf_variability_analysis.png`

**해석 기준:**
```python
mean_hrf_correlation:
  > 0.85: "✅ Highly representative"
  > 0.70: "⚠️ Moderately representative"
  < 0.70: "🚨 Low representativeness"
```

**의미:**
- High correlation → ROI HRF가 개별 voxel을 잘 대표
- Low correlation → Voxel-to-voxel HRF 변동성이 큼 → 개별 voxel HRF 사용 고려

#### C. Amplitude SNR 지표 계산 및 시각화 (Line 858-1074)

**계산 지표:**

1. **Raw amplitude statistics**
   - Mean, std, min, max across all runs/colors/voxels

2. **Per-run variability**
   - 각 run의 mean, std, SNR

3. **Per-color statistics**
   - 각 color의 mean, std

4. **Z-scored amplitude check**
   - Mean ≈ 0, std ≈ 1 확인 (normalization 검증)

5. **Voxel-wise SNR** (핵심 지표)
   ```python
   signal = std(mean_amplitude_per_color)  # Color 간 변동
   noise = mean(std_amplitude_per_color_across_runs)  # Run 내 변동
   SNR = signal / noise
   ```
   - High SNR → 이 voxel이 color를 잘 구분함
   - Low SNR → Color discrimination 능력 낮음

6. **Run-to-run reliability**
   - 각 run pair 간 amplitude pattern correlation
   - High correlation → 재현성 높음

**시각화 (6-panel figure):**
1. **Raw amplitude distribution**: 원본 amplitude 분포
2. **Z-scored distribution**: 정규화된 amplitude + N(0,1) overlay
3. **Voxel SNR distribution**: SNR > 1.0, 2.0 기준 표시
4. **Per-color mean amplitude**: 8개 color별 평균 ± SEM
5. **Run-to-run correlation matrix**: 6×6 heatmap
6. **SNR vs R²**: Amplitude quality와 HRF quality 관계

**출력 파일:** `amplitude_snr_analysis.png`

**해석 기준:**
```python
Voxel SNR:
  > 2.0: "Excellent color discrimination"
  > 1.0: "Good discrimination"
  < 1.0: "Poor discrimination (high noise)"

Run correlation:
  > 0.7: "✅ High reliability"
  > 0.5: "⚠️ Moderate reliability"
  < 0.5: "🚨 Low reliability"
```

---

## 저장되는 파일 목록

### Numpy 배열 (.npy)
- `roi_hrf.npy`: ROI 평균 HRF (8,)
- `roi_hrf_deriv.npy`: HRF derivative (8,)
- `selected_voxels_mask.npy`: Voxel selection mask (n_voxels_total,)
- `r2_voxel.npy`: 모든 voxel의 R² (n_voxels_total,)
- `hrf_correlations.npy`: ROI HRF와 각 selected voxel HRF 간 correlation (n_voxels_selected,)
- `hrf_rmse.npy`: ROI HRF와 각 selected voxel HRF 간 RMSE (n_voxels_selected,)
- `amplitudes_raw.npy`: Raw amplitudes (6 runs, 8 colors, n_voxels_selected)
- `amplitudes_z.npy`: Z-scored amplitudes (6 runs, 8 colors, n_voxels_selected)
- `voxel_snr.npy`: 각 voxel의 SNR (n_voxels_selected,)

### CSV 파일
- `classification_results.csv`: Per-run classification accuracy
- `reconstruction_results.csv`: Per-run reconstruction errors

### JSON 파일
`analysis_summary.json` - 전체 분석 요약 (확장됨):

```json
{
  // Basic info
  "subject": "P01",
  "roi": "V1",
  "use_pca": true,
  "n_components": 6,
  "fir_delays": 8,

  // Voxel statistics
  "n_voxels_total": 1234,
  "n_voxels_selected": 617,
  "voxel_selection_pct": 50.0,

  // R² statistics (NEW!)
  "r2_threshold": 0.234,
  "r2_mean": 0.245,
  "r2_median": 0.234,
  "r2_std": 0.098,
  "r2_min": -0.123,
  "r2_max": 0.789,

  // HRF statistics
  "peak_delay": 3,
  "peak_delay_seconds": 4.5,

  // HRF variability (NEW!)
  "hrf_correlation_mean": 0.876,
  "hrf_correlation_median": 0.892,
  "hrf_correlation_std": 0.089,
  "hrf_rmse_mean": 0.123,
  "hrf_voxels_high_corr_pct": 78.5,

  // Amplitude SNR (NEW!)
  "amplitude_mean_raw": 12.34,
  "amplitude_std_raw": 5.67,
  "voxel_snr_mean": 1.456,
  "voxel_snr_median": 1.398,
  "voxel_snr_std": 0.567,
  "voxels_snr_gt_1_pct": 62.3,
  "voxels_snr_gt_2_pct": 23.4,

  // Run-to-run reliability (NEW!)
  "run_correlation_mean": 0.734,
  "run_correlation_min": 0.678,
  "run_correlation_max": 0.801,

  // Performance metrics
  "classification_accuracy": 0.875,
  "reconstruction_error": 12.34
}
```

### 시각화 파일 (.png, 300 dpi)
1. `roi_hrf.png`: ROI HRF + derivative (기존)
2. `r2_distribution_analysis.png`: R² 분석 4-panel (신규)
3. `hrf_variability_analysis.png`: HRF 변동성 6-panel (신규)
4. `amplitude_snr_analysis.png`: Amplitude SNR 6-panel (신규)

---

## 분석 흐름 요약

```
데이터 로딩
    ↓
[Step 1] Voxel-wise FIR HRF estimation
    → color-ignored design matrix
    → h_v = pinv(X) @ y per voxel
    → r² 계산
    ↓
[Enhanced Analysis A] R² distribution
    → Histogram, CDF, Box plot
    → Good fit threshold 분석
    ↓
[Step 2] Voxel selection
    → R² >= median(R²) (top 50%)
    ↓
[Step 3] ROI average HRF
    → mean(h_v for selected voxels)
    → numerical derivative
    ↓
[Enhanced Analysis B] HRF variability
    → Correlation with ROI HRF
    → RMSE, representativeness
    ↓
[Step 4] 2nd-level GLM
    → 16-column design (HRF + derivative)
    → β = pinv(X) @ y per run/voxel
    → Extract first 8 betas (amplitudes)
    ↓
[Step 5] Z-score normalization
    → Per voxel, per run, across colors
    ↓
[Enhanced Analysis C] Amplitude SNR
    → Voxel-wise SNR calculation
    → Run-to-run reliability
    → Quality metrics
    ↓
[Step 6] Classification
    → Leave-one-run-out CV
    → Diagonal LDA
    ↓
[Step 7] Reconstruction
    → 6-channel forward model
    → B&H 2009 method
```

---

## 주요 Quality Control 지표

### 1. 데이터 품질 (R²)
- **Good**: r2_median > 0.25
- **Acceptable**: r2_median > 0.15
- **Poor**: r2_median < 0.15

### 2. HRF 대표성 (Correlation)
- **High**: hrf_correlation_mean > 0.85
- **Moderate**: 0.70 < hrf_correlation_mean < 0.85
- **Low**: hrf_correlation_mean < 0.70

### 3. Amplitude 품질 (SNR)
- **Excellent**: voxel_snr_mean > 2.0
- **Good**: 1.0 < voxel_snr_mean < 2.0
- **Poor**: voxel_snr_mean < 1.0

### 4. 재현성 (Run correlation)
- **High**: run_correlation_mean > 0.7
- **Moderate**: 0.5 < run_correlation_mean < 0.7
- **Low**: run_correlation_mean < 0.5

---

## 서버 실행 절차

### 1. 업로드
```bash
scp fir_reconstruction_BH2009.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_BH2009.sbatch haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

### 2. 실행
```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
mkdir -p logs
sbatch run_BH2009.sbatch

# 작업 상태 확인
squeue -u haba6030

# 로그 실시간 모니터링
tail -f logs/BH2009_*.out
```

### 3. 다운로드
```bash
# 특정 subject/ROI 결과
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/BH2009/*P01_V1/ \
    ./derivatives/BH2009/

# 모든 결과
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/BH2009/ \
    ./derivatives/
```

---

## 예상 결과 해석

### V1 영역 (Primary Visual Cortex)
- **R²**: 0.25-0.35 (높은 편) - Stimulus-driven response 강함
- **HRF correlation**: > 0.85 - Uniform HRF shape
- **SNR**: 1.5-2.5 - Good color discrimination
- **Run correlation**: > 0.75 - High reliability

### V4/hV4 영역 (Higher Visual Areas)
- **R²**: 0.15-0.25 (중간) - Top-down effects 포함
- **HRF correlation**: 0.70-0.85 - More variable HRF
- **SNR**: 1.0-2.0 - Moderate discrimination
- **Run correlation**: 0.60-0.75 - Moderate reliability

---

## 이전 코드와의 차이점

| 측면 | 이전 (fir_reconstruction_runSpecific.py) | 신규 (fir_reconstruction_BH2009.py) |
|------|----------------------------------------|-----------------------------------|
| FIR delays | 15개 (0-14) | **8개 (0-7)** ✓ |
| HRF 추정 | Optimal delay 하나 선택 | **전체 HRF pseudo-inverse** ✓ |
| Voxel 선택 | 전체 사용 | **R² top 50%** ✓ |
| Amplitude | Peak delay beta | **2nd-level GLM (16 col)** ✓ |
| Derivative | 사용 안 함 | **HRF derivative 포함** ✓ |
| R² 분석 | 없음 | **4-panel 시각화** ✓ |
| HRF 변동성 | 없음 | **6-panel 시각화** ✓ |
| SNR 분석 | 없음 | **6-panel 시각화** ✓ |
| Summary 지표 | 10개 | **35개** ✓ |

---

## 참고 문헌

Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, *29*(44), 13992-14003.

---

## 문의 사항

각 분석 지표의 의미와 해석은 `251120_BH2009_code_explanation_KR.md` 문서를 참고하세요.

코드 구현의 상세한 설명은 해당 문서의 "요구사항별 코드 구현 매핑" 섹션에 있습니다.
