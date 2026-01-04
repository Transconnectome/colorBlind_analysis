# CVD (색각이상) vs Non-CVD 비교 분석 문서

## 📁 디렉토리 구조

```
docs/cvd_analysis/
├── README.md                                      # 본 파일
├── CVD_ANALYSIS_EXECUTIVE_SUMMARY_KR.md          # 📌 간결한 핵심 요약 (먼저 읽기)
├── CVD_NEURAL_DISSOCIATION_ANALYSIS_KR.md        # ⭐️ 전체 상세 분석 (V1/V2/V3/hV4)
├── EXECUTIVE_SUMMARY_FEATURE_SELECTION_KR.md     # Feature Selection 전체 요약
├── per_color_reconstruction_config32.csv         # 전체 ROI 색상별 데이터 (64 rows)
└── figures/
    ├── all_rois_red_orange_vs_green_cyan.png     # 전체 ROI Red-Orange vs Green-Cyan 비교 ⭐️
    ├── roi_hierarchy_comparison.png              # ROI 계층별 성능 비교 ⭐️
    ├── extreme_cases_per_color.png               # 극단 케이스 색상별 오차 ⭐️
    ├── cvd_red_orange_vs_green_cyan.png          # V1/V2 Red-Orange vs Green-Cyan
    ├── cvd_all_colors_comparison.png             # V1/V2 8개 색상별 오차
    └── cvd_accuracy_comparison.png               # V1/V2 정확도 비교
```

---

## 📊 주요 분석 문서

### 0. **FULL_STATISTICS_SUMMARY.md** 🆕 📊
**전체 피험자 통계 요약 (NonCVD n=6, CVD n=3)**

#### 포함 내용
- 전체 9명의 reconstruction error & classification accuracy 통계
- Independent t-tests 결과 (p-values, Cohen's d)
- 개별 피험자 데이터 전체
- **주요 결론**: 모든 ROI에서 CVD vs NonCVD 유의차 없음 (p > 0.05)
- 신경-행동 해리 현상 종합 해석

---

### 1. **CVD_ANALYSIS_EXECUTIVE_SUMMARY_KR.md** 📌
**먼저 읽기 - 간결한 핵심 요약 (2페이지)**

#### One-line Summary
> CVD 피험자의 V1~hV4 전체 시각 위계에서 색 신호는 디코딩 가능하지만,
> 특정 영역의 손상이 아닌 의사결정/통합 단계 실패 또는 개인별 이질적 손상 패턴을 보임

#### 포함 내용
- 주요 결과 표 (ROI별, Red-Orange vs Green-Cyan)
- 극단 케이스 (재구성 오차 > 100°)
- 3가지 유력한 가설
- 연구 한계 및 향후 방향

---

### 2. **CVD_NEURAL_DISSOCIATION_ANALYSIS_KR.md** ⭐️
**전체 상세 분석 - V1/V2/V3/hV4 통합 문서 (20페이지)**

#### 핵심 발견
- **V1~hV4 모든 영역**에서 CVD vs Non-CVD 차이 없음
- **ROI별로 상이한 패턴**: 일관된 적록 혼동 없음
  - V1, V3: CVD에서 Red-Orange가 더 잘됨 (❌ 예상과 반대)
  - V2, hV4: CVD에서 Red-Orange가 더 나쁨 (✓ 예상과 일치)
- **개인별 이질적 손상**: sub-08(Blue), sub-09(Green-Cyan), sub-10(Red-Orange)

#### 재해석
> "CVD의 색 지각 결핍은 특정 시각 영역의 손상이 아니라,
> 전체 시각 위계에서 약한 신호가 의사결정 단계에서 적절히 통합/활용되지 못하는 것"

#### 내용 구성 (10개 섹션)
1. 요약
2. 핵심 발견: 예상과의 불일치 (V1/V2)
3. 신경-행동 해리 현상
4. 가능한 메커니즘
5. 개별 색상 분석 (V1/V2)
6. **V3 & hV4 상위 피질 분석** (NEW)
7. 데이터 해석의 한계
8. 신경과학적 함의
9. 향후 연구 방향
10. 결론
11. 전문가 코멘트

---

### 3. **EXECUTIVE_SUMMARY_FEATURE_SELECTION_KR.md**
**전체 Feature Selection 분석 요약**

#### 분석 범위
- Baseline (no feature selection)
- PCA feature selection
- ANOVA feature selection
- RFE feature selection

#### 주요 결론
- ANOVA/RFE가 필수적 (33% classification vs 12.5% chance)
- Config32_determin 추천 (100% 성공률, 39.4% 평균 classification)
- V1/V2가 V3/hV4보다 성능 우수
- CVD vs Non-CVD 간 유의미한 차이 없음

---

## 📈 시각화 자료

### figures/ 디렉토리

#### 1. `all_rois_red_orange_vs_green_cyan.png` ⭐️ NEW
**전체 ROI (V1, V2, V3, hV4) Red-Orange vs Green-Cyan 비교**
- 4개 subplot으로 각 ROI 분리 표시
- CVD vs Non-CVD 막대 그래프
- 핵심 발견: 일관된 계층적 패턴 없음
  - V1, V3: CVD에서 Red-Orange가 더 잘됨 (❌)
  - V2, hV4: CVD에서 Red-Orange가 더 나쁨 (✓)

#### 2. `roi_hierarchy_comparison.png` ⭐️ NEW
**시각 위계별 전체 재구성 오차 비교**
- V1 → V2 → V3 → hV4 계층 표시
- NonCVD vs CVD 막대 그래프
- 핵심 발견: 상위 ROI로 갈수록 성능 저하
  - V1: 29.8-39.0° < V2: 39.8-50.0° < V3: 62.1-70.3° < hV4: 73.9-83.4°

#### 3. `extreme_cases_per_color.png` ⭐️ NEW
**극단 케이스 색상별 오차 (4개 subplot)**
- sub-06 V1 (NonCVD), sub-09 V1 (CVD)
- sub-08 V3 (CVD), sub-08 hV4 (CVD)
- Red-Orange, Green-Cyan 두꺼운 테두리로 강조
- 100° 이상 극단값 annotate
- 핵심 발견:
  - V3 sub-08: Cyan (117.3°), Blue (113.5°) 극도로 나쁨
  - hV4 sub-08: Red (114.7°) 극도로 나쁨

#### 4. `cvd_red_orange_vs_green_cyan.png`
**V1/V2 Red-Orange vs Green-Cyan 직접 비교**
- V1, V2 ROI 각각 표시
- CVD vs Non-CVD 막대 그래프

#### 5. `cvd_all_colors_comparison.png`
**V1/V2 8개 색상별 재구성 오차 비교**
- 4개 subplot (sub-06 V1, sub-09 V1, sub-06 V2, sub-10 V2)
- Red-Orange (빨간 테두리), Green-Cyan (초록 테두리) 강조

#### 6. `cvd_accuracy_comparison.png`
**V1/V2 정확도 (≤22.5°) 비교**
- Red-Orange vs Green-Cyan 정확도
- V1, V2 ROI 분리 표시

---

## 📊 데이터 파일

### `per_color_reconstruction_config32.csv`
**전체 ROI Config32_determin 기반 색상별 상세 통계**

#### 컬럼 구성
- `subject`: 피험자 ID (sub-06, sub-08, sub-09, sub-10)
- `group`: CVD 또는 NonCVD
- `roi`: V1, V2, V3, hV4
- `config`: config32_determin
- `overall_error`: 전체 재구성 오차 (degrees)
- `color_id`: 색상 ID (1-8)
- `color_name`: 색상 이름 (Red, Red-Orange, ...)
- `hue_angle`: 색 각도 (0°, 45°, ..., 315°)
- `reconstruction_error`: 해당 색상의 재구성 오차
- `acc_22.5`: ≤22.5° 정확도 (%)
- `acc_45`: ≤45° 정확도 (%)

#### 데이터 요약 (업데이트됨)
- 총 64 행 (4 ROI × 2-4 피험자 × 8색상)
- **V1**: sub-06 (NonCVD), sub-09 (CVD)
- **V2**: sub-06 (NonCVD), sub-10 (CVD)
- **V3**: sub-06 (NonCVD), sub-08 (CVD)
- **hV4**: sub-06 (NonCVD), sub-08 (CVD)

---

## 🎯 핵심 결론 (V1/V2/V3/hV4 종합)

### 신경-행동 해리 (Neural-Behavioral Dissociation)

**신경 측면 (fMRI 디코딩):**
- ✓ **V1~hV4 모든 영역**에서 색 정보 디코딩 가능
- ✓ MVPA는 약한 신호도 검출 (chance 12.5% vs 실제 25-60%)
- ✓ **CVD와 Non-CVD 간 통계적 차이 없음** (모든 ROI)
- ✓ 상위 ROI로 갈수록 성능 저하 (V1 < V2 < V3 < hV4)

**행동 측면 (실제 색 지각):**
- ✗ CVD 피험자는 **실제로 적록 구분 불가**
- ✗ Ishihara 검사 실패
- ✗ 일상 생활에서 색 혼동

### 최종 해석 (V3/hV4 포함)

**"CVD의 색 지각 결핍은 특정 시각 영역의 손상이 아니라,
전체 시각 위계에서 약한 신호가 의사결정 단계에서
적절히 통합/활용되지 못하는 것으로 보인다."**

**증거:**
1. **V1~hV4 모든 영역**에서 CVD vs NonCVD 차이 없음
2. **ROI별로 상이한 패턴**: 일관된 계층적 변화 없음
   - V1, V3: CVD에서 Red-Orange가 오히려 더 잘됨 (예상과 반대)
   - V2, hV4: CVD에서 Red-Orange가 더 나쁨 (예상과 일치)
3. **개인별로 서로 다른 색상이 문제**:
   - sub-08 V3: Cyan/Blue 극도로 나쁨 (117.3°, 113.5°)
   - sub-08 hV4: Red 극도로 나쁨 (114.7°)
   - sub-09 V1: Green-Cyan 나쁨 (46.1°)
4. **일관된 적록 혼동 패턴 없음**

**함의:**
- 초기/중간/고차 피질 **모두** 약한 색 신호 존재
- 하지만 신호가 **행동으로 연결되지 못함**
- 문제는 **통합/의사결정/의식적 접근성** 단계
- 또는 **개인별 이질적 손상 패턴** (단일 phenotype 아님)

---

## 🔬 분석 방법

### 데이터
- **Config**: config32_determin (no smoothing, standardization, basic confounds)
- **Feature Selection**: ANOVA-F (k=1-200 voxels, ROI별 최적화)
- **피험자 (전체 9명)**:
  - Non-CVD: sub-01, 02, 03, 05, 06, 07 (6명)
  - CVD: sub-08, 09, 10 (3명)
  - Excluded: sub-04 (ROI alignment issue)
- **ROI**: V1, V2, V3, hV4 (Wang et al. 2015 atlas)
- **통계 분석**:
  - ANOVA feature selection 결과 (전체 9명 포함)
  - Independent t-tests for group comparison
  - **결과**: 모든 ROI에서 CVD vs NonCVD 유의차 없음 (p > 0.05)
  - Reconstruction error Cohen's d: -0.29 to -1.32 (small to large effect)
  - Classification accuracy Cohen's d: -0.06 to +0.51 (negligible to medium effect)

### 색상 구성 (8색)
1. Red (0°)
2. Red-Orange (45°)
3. Orange (90°)
4. Yellow (135°)
5. Green (180°)
6. Cyan (225°)
7. Blue (270°)
8. Purple (315°)

### 색상 그룹
- **Red-Orange**: 색 1,2 (L-M 채널 의존)
- **Yellow**: 색 3,4
- **Green-Cyan**: 색 5,6 (L-M 채널 의존)
- **Blue-Purple**: 색 7,8 (S-(L+M) 채널 의존)

---

## 📖 사용 가이드

### 1. 신경과학자/연구자
→ `CVD_NEURAL_DISSOCIATION_ANALYSIS_KR.md` 읽기
- 신경-행동 해리 현상 이해
- 메커니즘 가설 검토
- 향후 연구 아이디어 도출

### 2. 데이터 분석가
→ `per_color_reconstruction_config32.csv` + figures
- CSV 파일로 재분석 가능
- 시각화 코드 참조: `/tmp/visualize_cvd_dissociation.py`
- 통계 검정 재현 가능

### 3. 전체 프로젝트 이해
→ `EXECUTIVE_SUMMARY_FEATURE_SELECTION_KR.md`
- Feature selection 전체 흐름
- ROI별, config별 성능 비교
- 최적 파라미터 선택 근거

---

## ⚠️ 데이터 한계

### 표본 크기
- **Config32_determin에서 CVD 성공 케이스**: 2명만 (V1 1명, V2 1명)
- **Non-CVD V2**: 1명만
- 통계적 검증 불가능 수준

### 개인차
- 재구성 오차 범위: 29.8° ~ 50.0°
- 피험자 간 변동 > CVD/Non-CVD 차이

### ROI 정의
- 해부학적 atlas 기반 (개인별 functional localizer 없음)
- V1/V2 경계 부정확 가능성

---

## 🚀 향후 연구 방향

### 필수 추가 분석
1. **V3/hV4 ROI 상세 분석** (현재 데이터 부족)
2. **전체 Config 통합 분석** (표본 크기 증가)
3. **색상 쌍 혼동 행렬 정량화**
4. **신호 강도(SNR) 직접 측정**

### 추가 데이터 수집 권장
1. **행동 색 변별 과제** (psychophysics)
2. **색 이름 지정 vs 색 매칭 과제** (명시적 vs 암묵적)
3. **V4 기능적 localizer**
4. **시간 해상도 분석** (FIR 모델)

---

## 📚 참고 문헌

- Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience, 29*(44), 13992-14003.

- Gegenfurtner, K. R., & Kiper, D. C. (2003). Color vision. *Annual Review of Neuroscience, 26*, 181-206.

- Dehaene, S., & Changeux, J.-P. (2011). Experimental and theoretical approaches to conscious processing. *Neuron, 70*(2), 200-227.

---

**작성일**: 2025-12-13
**작성자**: Claude Code Analysis
**분석 기반**: Config32_determin, ANOVA feature selection (k=50-100)
**데이터 경로**: `logs/feature_selection/figures/`
