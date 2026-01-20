# Step 1.3 결과 해석 가이드

## 파일 위치 및 구조

### 개별 결과 (40개 디렉토리)

**경로**: `/scratch/connectome/haba6030/colorBlind/prediction_model_workspace/results/trial_wise_glm/`

**구조**:
```
sub-01_V1/
├── trial_betas.npy           # (n_trials, n_voxels) - 핵심 데이터
├── trial_metadata.json       # Trial 정보
├── quality_metrics.json      # Reliability, tSNR 등
└── diagnostic_figure.png     # 4패널 시각화
```

### 집계 결과 (요약)

```
trial_wise_glm/
├── trial_glm_detailed.csv    # 40 rows (전체 결과 테이블)
├── trial_glm_summary.png     # 6패널 시각화
└── trial_glm_summary.txt     # 텍스트 리포트
```

---

## 핵심 메트릭 해석

### 1. Split-half Reliability (Procrustes-based)

**의미**: Odd runs vs Even runs 간 패턴 일관성 (좌표계 무관)

**계산**:
```python
reliability = 1 - procrustes_disparity
# disparity = sqrt(sum((aligned_X - Y)^2) / n_points)
```

**해석 기준**:

| Reliability | 판단 | 의미 |
|-------------|------|------|
| **≥ 0.80** | ✅ **Excellent** | 매우 안정적, 모든 분석 적합 |
| **0.70-0.79** | ✅ **Good** | 안정적, Hyperalignment 적합 |
| **0.50-0.69** | ⚠️ **Acceptable** | 사용 가능, 주의 필요 |
| **0.30-0.49** | ⚠️ **Poor** | 선택적 사용, 일부 ROI만 |
| **< 0.30** | ❌ **Unacceptable** | 파라미터 재조정 필요 |

**Decision Rule**:
```
Mean reliability across all colors:
  ≥ 0.50 → ✅ PROCEED TO STEP 1.4
  ≥ 0.30 → ⚠️ SELECTIVE PROCEED (높은 ROI만)
  < 0.30 → ❌ IMPROVE PARAMETERS
```

### 2. Temporal SNR

**의미**: Trial-to-trial 신호 안정성

**계산**:
```python
tSNR = mean(signal) / std(signal)
# Per voxel across trials
```

**해석 기준**:

| tSNR | 판단 |
|------|------|
| **> 50** | ✅ Excellent |
| **30-50** | ✅ Good |
| **15-30** | ⚠️ Acceptable |
| **< 15** | ❌ Poor |

**참고**: Visual cortex tSNR은 일반적으로 20-40 범위

### 3. Trial Counts

**예상**:
- 각 색상: 54 trials (9 repetitions × 6 runs)
- "blank" 제외 시: 8 colors × 54 = 432 total trials

**체크사항**:
- 모든 색상의 trial 수가 균등한가?
- Missing trials 있는가? (50개 미만이면 문제)

---

## 집계 결과 파일 해석

### A. trial_glm_detailed.csv

**컬럼 구조**:
```csv
subject,roi,n_voxels,total_trials,reliability_mean,tsnr_mean,tsnr_median,smoothing_fwhm,confounds,reliability_red,reliability_orange,...,count_red,count_orange,...
01,V1,450,432,0.65,28.3,26.1,6.0,motion,0.70,0.68,...,54,54,...
```

**체크 포인트**:
1. **reliability_mean 컬럼**: 각 subject-ROI의 평균 reliability
2. **reliability_{color}**: 색상별 reliability (불균형 확인)
3. **tsnr_mean**: 신호 품질 지표
4. **count_{color}**: Trial 누락 확인 (모두 54여야 함)

### B. trial_glm_summary.txt

**구조**:
```
================================================================================
TRIAL-WISE GLM (LS-S) SUMMARY
================================================================================

## Overall Statistics
Total subject-ROI combinations: 40
Subjects: 10
ROIs: 4

## Split-half Reliability (Procrustes)
Overall mean: 0.623 ± 0.145

By ROI:
  V1: 0.712 ± 0.089
  V2: 0.650 ± 0.112
  V3: 0.580 ± 0.145
  hV4: 0.550 ± 0.178

## Temporal SNR
Overall mean: 26.45 ± 5.23

By ROI:
  V1: 28.12 ± 4.56
  V2: 26.78 ± 5.12
  V3: 25.34 ± 5.67
  hV4: 24.56 ± 6.23

## Quality Assessment
Combinations meeting reliability target (≥0.50): 32/40 (80.0%)

⚠️ Cases with low reliability:
  sub-06 V3: 0.421
  sub-06 hV4: 0.389
  sub-07 V3: 0.456
  sub-07 hV4: 0.412
  ...

## Next Steps
✅ PROCEED TO STEP 1.4 (HYPERALIGNMENT)

Most combinations have sufficient reliability.
Ready for trial-aligned GPA (Generalized Procrustes Analysis).
```

**주목할 부분**:
1. **Overall mean reliability**: 전체 평균이 0.50 이상인가?
2. **ROI hierarchy**: V1 > V2 > V3 > hV4 순서 예상됨
3. **Pass rate**: 80% 이상이면 양호
4. **Low reliability cases**: Tier 3 피험자 (sub-06, sub-07) 주의

### C. trial_glm_summary.png (6패널 시각화)

**Panel A**: Reliability by ROI (막대그래프)
- 피험자별, ROI별 reliability 비교
- 목표선 0.50 표시
- **해석**: 대부분 목표선 위에 있는가?

**Panel B**: tSNR by ROI (막대그래프)
- 피험자별, ROI별 tSNR
- **해석**: 20-40 범위에 분포하는가?

**Panel C**: Average Trial Count per ROI (막대그래프)
- ROI별 평균 trial 수
- **해석**: ~432 (또는 ~380 blank 제외)에 가까운가?

**Panel D**: Reliability Distribution by ROI (박스플롯)
- ROI별 reliability 분포
- **해석**:
  - V1의 median이 가장 높은가?
  - Outlier는 어떤 피험자인가?

**Panel E**: tSNR Distribution by ROI (박스플롯)
- ROI별 tSNR 분포
- **해석**: 분산이 크지 않은가?

**Panel F**: Reliability vs tSNR (산점도)
- 두 메트릭 간 상관관계
- **해석**:
  - 양의 상관관계 예상 (high tSNR → high reliability)
  - 이상치(outlier) 식별

---

## 결과 기반 의사결정 트리

### Scenario 1: 이상적 결과 ✅

**조건**:
- Overall mean reliability: **0.65 ± 0.12**
- Pass rate (≥0.50): **85%** (34/40)
- V1 mean: **0.72**, V2: **0.68**, V3: **0.62**, hV4: **0.58**

**해석**:
- ✅ 모든 ROI 사용 가능
- ✅ 모든 피험자 포함 (Tier 1-3)
- ✅ Step 1.4로 즉시 진행

**다음 단계**:
```bash
# Step 1.4 (Hyperalignment) 준비
1. Hyperalignment vs SRM 둘 다 구현
2. HC 5명 (sub-01,02,03,04,05) 사용
3. V1부터 시작, 나머지 ROI 순차 진행
```

---

### Scenario 2: 양호한 결과 (선택적) ⚠️

**조건**:
- Overall mean reliability: **0.45 ± 0.18**
- Pass rate (≥0.50): **60%** (24/40)
- V1 mean: **0.58**, V2: **0.52**, V3: **0.42**, hV4: **0.38**

**해석**:
- ⚠️ V1, V2만 신뢰 가능
- ⚠️ Tier 3 (sub-06, sub-07) 제외 고려
- ⚠️ V3, hV4는 보류

**다음 단계**:
```bash
# 선택적 진행
1. V1, V2만으로 Step 1.4 진행
2. Tier 1+2 피험자만 사용 (sub-01,02,03,04,05,08,09,10)
3. V3, hV4는 파라미터 조정 후 재실행
```

**파라미터 조정 방안** (V3, hV4):
- Smoothing 증가: 6mm → **8mm**
- Confounds 추가: motion → **motion + acompcor**
- HRF model 변경: spm → **spm + derivative**

---

### Scenario 3: 불량한 결과 ❌

**조건**:
- Overall mean reliability: **0.25 ± 0.15**
- Pass rate (≥0.50): **20%** (8/40)
- 대부분 ROI < 0.30

**해석**:
- ❌ 근본적인 문제 (데이터 or 방법론)
- ❌ 파라미터 전면 재검토 필요

**진단 체크리스트**:

1. **데이터 품질 문제?**
   ```bash
   # Step 1.1 실행하여 데이터 완전성 확인
   python 00_check_data_structure.py
   ```
   - Missing trials?
   - Run-to-run inconsistency?

2. **GLM 설정 문제?**
   - **HRF model**: spm → spm+derivative → fir?
   - **High-pass filter**: 1/128 → 1/160?
   - **Drift model**: cosine → polynomial?

3. **전처리 문제?**
   - **Smoothing**: 6mm → 8mm → 10mm?
   - **Confounds**: motion → motion+acompcor → motion+acompcor+scrub?
   - **ROI mask**: Subject-specific → Group template?

**파라미터 Grid Search** (Step 1.3 재실행):
```python
# Test configurations
smoothing_fwhm = [6, 8, 10]  # mm
confounds = ['motion', 'motion_acompcor', 'motion_acompcor_scrub']
hrf_model = ['spm', 'spm + derivative', 'fir']

# Run subset (sub-01 V1만)
# 9 configurations × 1 subject-ROI ≈ 3시간
```

---

## ROI별 예상 패턴

### 기대되는 Hierarchy

```
V1 (Primary Visual)
├─ Reliability: 0.70-0.80 (가장 높음)
├─ tSNR: 28-35
└─ 이유: Low-level features, 가장 안정적

V2 (Secondary Visual)
├─ Reliability: 0.65-0.75
├─ tSNR: 26-32
└─ 이유: Intermediate features

V3 (Dorsal Stream)
├─ Reliability: 0.55-0.70
├─ tSNR: 24-30
└─ 이유: Motion/shape 처리

hV4 (Ventral Stream)
├─ Reliability: 0.50-0.65 (가장 낮을 가능성)
├─ tSNR: 22-28
└─ 이유: High-level color, 더 variable
```

**만약 역전 현상이 보이면?** (예: hV4 > V1)
- ⚠️ ROI mask 문제 의심
- ⚠️ Preprocessing 문제 가능성

---

## 피험자별 예상 패턴

### Tier 1 (Excellent, Dice ≥0.93)
**sub-01, 03, 04, 08, 09, 10**

**예상**:
- Reliability: 0.60-0.80 (일관되게 높음)
- tSNR: 26-35
- 모든 ROI 사용 가능

### Tier 2 (Good, Dice ~0.85)
**sub-02, 05**

**예상**:
- Reliability: 0.50-0.70 (약간 낮음)
- tSNR: 23-30
- 대부분 ROI 사용 가능, 일부 주의

### Tier 3 (Partial, Dice ~0.73)
**sub-06, 07**

**예상**:
- Reliability: 0.30-0.50 (낮음) ⚠️
- tSNR: 18-26
- V1만 사용 가능, 나머지 제외 고려

**만약 Tier 3가 양호하면?**
- ✅ Preprocessing quality가 trial-wise에는 영향 적음
- ✅ 모든 피험자 포함 가능

**만약 Tier 1도 낮으면?**
- ❌ Preprocessing 아닌 다른 문제 (파라미터, 방법론)

---

## 색상별 Reliability 패턴

### 균등한 경우 (이상적) ✅

```
Color        Reliability
red          0.68
orange       0.66
yellow       0.67
green        0.69
cyan         0.68
blue         0.70
purple       0.67
magenta      0.68
---
Mean:        0.68 ± 0.01
```

**해석**: 모든 색상 동등하게 안정적

### 불균등한 경우 ⚠️

```
Color        Reliability
red          0.72  ← 높음
orange       0.70
yellow       0.68
green        0.42  ← 낮음!
cyan         0.40  ← 낮음!
blue         0.71
purple       0.69
magenta      0.70
---
Mean:        0.63 ± 0.13
```

**의심되는 원인**:
1. **특정 색상의 stimulus 문제?**
   - Green, cyan의 contrast가 낮은가?
   - Display calibration 문제?

2. **Trial 수 불균형?**
   - Green, cyan의 count가 적은가?
   - Missing trials?

3. **생리적 요인?**
   - S-cone 반응 (blue-yellow axis)?
   - L-M cone 반응 (red-green axis)?

**조치**:
- `trial_glm_detailed.csv`에서 `count_{color}` 확인
- 특정 색상만 낮으면 그 색상 제외 고려

---

## 추가 분석 (Optional)

### 1. Per-color Reliability 히트맵

```python
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

df = pd.read_csv('trial_glm_detailed.csv')

# Extract per-color reliability
colors = ['red', 'orange', 'yellow', 'green', 'cyan', 'blue', 'purple', 'magenta']
reliability_matrix = df[[f'reliability_{c}' for c in colors]].values

# Create heatmap (subjects × colors)
plt.figure(figsize=(10, 8))
sns.heatmap(reliability_matrix,
            xticklabels=colors,
            yticklabels=[f"{row['subject']}-{row['roi']}" for _, row in df.iterrows()],
            cmap='RdYlGn', vmin=0, vmax=1, center=0.5)
plt.title('Per-color Reliability Heatmap')
plt.xlabel('Color')
plt.ylabel('Subject-ROI')
plt.tight_layout()
plt.savefig('reliability_heatmap.png', dpi=300)
```

### 2. Tier별 비교

```python
# Define tiers
tier1 = ['01', '03', '04', '08', '09', '10']
tier2 = ['02', '05']
tier3 = ['06', '07']

df['tier'] = df['subject'].apply(lambda x:
    'Tier1' if x in tier1 else
    'Tier2' if x in tier2 else 'Tier3')

# Compare by tier
import seaborn as sns
sns.boxplot(data=df, x='tier', y='reliability_mean', hue='roi')
plt.axhline(0.50, color='green', linestyle='--')
plt.title('Reliability by Preprocessing Tier')
plt.savefig('reliability_by_tier.png', dpi=300)
```

### 3. tSNR vs Reliability 상관관계

```python
import scipy.stats as stats

corr, pval = stats.pearsonr(df['tsnr_mean'], df['reliability_mean'])
print(f"Correlation: {corr:.3f}, p-value: {pval:.4f}")

plt.scatter(df['tsnr_mean'], df['reliability_mean'],
            c=df['roi'].astype('category').cat.codes,
            cmap='tab10', s=100, alpha=0.7)
plt.xlabel('Temporal SNR')
plt.ylabel('Reliability')
plt.title(f'tSNR vs Reliability (r={corr:.3f}, p={pval:.4f})')
plt.colorbar(label='ROI')
plt.savefig('tsnr_reliability_correlation.png', dpi=300)
```

---

## 빠른 판단 체크리스트

### ✅ 즉시 진행 가능 (Step 1.4)

- [ ] Overall mean reliability ≥ 0.50
- [ ] Pass rate (≥0.50) ≥ 80%
- [ ] V1 mean reliability ≥ 0.60
- [ ] 모든 색상 reliability ≥ 0.40
- [ ] tSNR mean ≥ 20

### ⚠️ 조건부 진행

- [ ] Overall mean 0.30-0.49
- [ ] Pass rate 50-79%
- [ ] V1, V2만 ≥ 0.50
- [ ] → **V1, V2만 사용, Tier 1+2 피험자만**

### ❌ 파라미터 재조정 필요

- [ ] Overall mean < 0.30
- [ ] Pass rate < 50%
- [ ] V1도 < 0.50
- [ ] → **Grid search, 방법론 재검토**

---

## 다음 단계 요약

### Scenario별 Action

| 결과 | Overall Mean | Action |
|------|--------------|--------|
| **Excellent** | ≥ 0.60 | ✅ 즉시 Step 1.4, 모든 ROI/피험자 |
| **Good** | 0.50-0.59 | ✅ Step 1.4, 선택적 ROI (V1>V2>V3>hV4) |
| **Acceptable** | 0.30-0.49 | ⚠️ V1,V2만 Step 1.4, V3,hV4 재실행 |
| **Poor** | < 0.30 | ❌ 파라미터 grid search 필요 |

### 타임라인 (각 scenario)

**Excellent/Good**:
- ✅ 즉시 Step 1.4 시작 (1-2일)
- ✅ Hyperalignment vs SRM 비교
- ✅ Phase 2 준비

**Acceptable**:
- ⚠️ V1,V2로 Step 1.4 (1일)
- ⏳ V3,hV4 재실행 (파라미터 조정, 1일)
- ⚠️ Phase 2는 V1,V2만 또는 전체 대기

**Poor**:
- ❌ Grid search (2-3일)
- ❌ 방법론 재검토 (문헌 조사)
- ❌ Phase 2 지연

---

**Last updated**: 2026-01-10
**Purpose**: Step 1.3 결과 해석 및 의사결정 가이드
**Next**: 결과 확인 후 이 가이드 참조하여 판단
