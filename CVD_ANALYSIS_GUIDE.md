# CVD Discrimination Analysis Guide

이 가이드는 색약(CVD)과 비색약(Non-CVD) 개인을 구분하는 신경 지표를 찾기 위한 분석 파이프라인을 설명합니다.

## 목표

색약자의 뇌 활동에서 나타나는 특징적인 패턴을 찾아, 색약 여부를 구분할 수 있는 객관적 지표를 개발합니다.

---

## 핵심 분석 지표

### 1. **Red-Green Compression Ratio** ⭐⭐⭐

**가설:** 색약자는 적-녹 색 쌍의 neural representation이 압축되어 있을 것

**측정 방법:**
```
Compression Ratio = Reconstructed Distance / True Distance
```

- **< 0.9**: 압축됨 (색약 가능성 ↑)
- **0.9 - 1.1**: 정상
- **> 1.1**: 확장됨

**기대 결과:**
- Non-CVD: Ratio ≈ 1.0 (정상)
- CVD (Deutan): 적-녹 쌍에서 Ratio < 0.8 (압축)

---

### 2. **Novel Color Reconstruction Bias**

**가설:** 색약자는 특정 색 영역으로 systematic bias를 보일 것

**측정 방법:**
```
Bias = Reconstructed Hue - True Hue  (signed, -180° to +180°)
```

**Polar plot에서 확인:**
- **Arrow 방향**: Bias 방향
- **Arrow 길이**: Bias 크기

**기대 결과:**
- Non-CVD: 무작위 방향, 작은 크기
- CVD: 적-녹 영역에서 systematic shift (예: 모든 녹색이 노란색으로)

---

### 3. **Color Space Structure (MDS)**

**가설:** 색약자는 색 공간의 구조가 왜곡되어 있을 것

**측정 방법:**
- Multidimensional Scaling (MDS)로 8색의 2D 표현 생성
- CVD vs Non-CVD의 구조 비교

**기대 결과:**
- Non-CVD: 원형/균일한 분포
- CVD: 적-녹 축이 압축된 타원형

---

### 4. **Classification Confusion Patterns**

**가설:** 색약자는 특정 색 쌍을 혼동할 것

**측정 방법:**
- Confusion matrix에서 off-diagonal entries
- 어떤 색 쌍이 자주 혼동되는가?

**기대 결과:**
- Non-CVD: Diagonal dominant (높은 정확도)
- CVD: 적-녹 쌍에서 confusion 증가

---

### 5. **PCA Space Coordinates** (향후 구현)

**가설:** 색약자는 PCA의 특정 차원에서 차이를 보일 것

**측정 방법:**
- PC1, PC2, PC3에서 각 색의 좌표
- 적-녹 쌍의 PC 공간 거리

**기대 결과:**
- Non-CVD: PC1이 색조(hue) 축과 대응, 적-녹이 멀리 분리
- CVD: 적-녹이 PC 공간에서 가까이 위치

---

### 6. **Channel Response Profiles** (향후 구현)

**가설:** 색약자는 특정 channel의 response가 약할 것

**측정 방법:**
- 6-channel model의 각 channel weight
- Channel 0 (0°) vs Channel 3 (180°) balance

**기대 결과:**
- Non-CVD: 모든 channel이 균형있게 활성화
- CVD: 특정 channel (red-green axis)이 약함

---

## 분석 파이프라인

### Step 1: 개별 피험자 분석

각 피험자에 대해 메트릭 추출:

```bash
# 서버에서 실행
cd /scratch/connectome/haba6030/colorBlind

# 피험자별 메트릭 추출 (모든 ROI 통합)
python visualize_Edits/extract_colorblind_metrics.py --subject P01 --output-dir cvd_metrics
python visualize_Edits/extract_colorblind_metrics.py --subject 01 --output-dir cvd_metrics
python visualize_Edits/extract_colorblind_metrics.py --subject 02 --output-dir cvd_metrics
python visualize_Edits/extract_colorblind_metrics.py --subject 03 --output-dir cvd_metrics
python visualize_Edits/extract_colorblind_metrics.py --subject 04 --output-dir cvd_metrics
```

**출력 파일:**
- `{subject}_cvd_metrics_summary.txt`: 요약 리포트
- `{subject}_novel_color_angles.csv`: Novel color 복원 각도
- `{subject}_color_pair_distances.csv`: 색 쌍 거리
- `{subject}_red_green_metrics.csv`: 적-녹 압축 비율 ⭐
- `{subject}_classification_confusion.csv`: 혼동 패턴

---

### Step 2: 그룹 간 비교

CVD vs Non-CVD 그룹 비교:

```bash
# 서버에서 실행
python visualize_Edits/compare_subjects_cvd.py \
    --cvd-subjects P01 \
    --non-cvd-subjects 01 02 03 04 \
    --metrics-dir cvd_metrics \
    --output-dir cvd_comparison
```

**출력 파일:**
1. `red_green_compression_comparison.png`: 압축 비율 boxplot
2. `novel_color_bias_comparison.png`: Bias 패턴 polar plot
3. `color_space_structure_comparison.png`: MDS 2D projection
4. `statistical_comparison.txt`: 통계 검정 결과 (t-test, p-values)

---

### Step 3: 결과 해석

#### A. Red-Green Compression Ratio

**통계적 유의성 확인:**
```
statistical_comparison.txt에서:
  V1:
    CVD:     mean = 0.65, std = 0.12
    Non-CVD: mean = 0.98, std = 0.08
    t-test: t = -4.52, p = 0.0023 ***SIGNIFICANT***
```

**해석:**
- p < 0.05: 유의미한 차이
- CVD < 0.8: 압축됨 → 색약 양성 지표
- Ratio가 ROI별로 다르다면, 어떤 ROI가 민감한가?

#### B. Novel Color Bias Patterns

**Polar plot에서 확인:**
- CVD는 특정 방향으로 systematic shift
- Non-CVD는 무작위 방향

**정량화:**
```python
# Bias의 circular variance 계산
# CVD: Low variance (일관된 방향)
# Non-CVD: High variance (무작위)
```

#### C. MDS Color Space

**시각적 검사:**
- CVD: 적-녹 축이 압축된 타원형
- Non-CVD: 원형/균일

**정량화:**
- 적-녹 쌍의 MDS 거리 / 청-황 쌍의 MDS 거리
- CVD < Non-CVD이면 성공

---

## 추가 권장 분석

### 1. **ROI Hierarchy Analysis**

어떤 ROI가 색약 구분에 가장 민감한가?

```
Sensitivity = |Mean_CVD - Mean_NonCVD| / SD_pooled
```

**예상:**
- hV4 > V3 > V2 > V1 (higher visual areas가 더 민감)

---

### 2. **Individual Color Analysis**

8가지 색 중 어떤 색이 가장 구분력이 높은가?

```python
# color_pair_distances.csv에서:
# 각 색 쌍에 대해 CVD vs Non-CVD 비교
# p-value가 가장 작은 색 쌍 = 가장 discriminative
```

---

### 3. **Machine Learning Classifier**

수집한 메트릭을 feature로 사용하여 CVD 분류기 학습:

**Features:**
1. Red-green compression ratio (per ROI)
2. Novel color mean error (per ROI per color)
3. Classification accuracy (per ROI)
4. Confusion pattern (specific color pairs)

**Model:**
- Logistic Regression
- Support Vector Machine (SVM)
- Random Forest

**평가:**
- Leave-One-Subject-Out Cross-Validation
- ROC AUC

---

## 예상 결과 (가설)

### CVD (Deutan/Protan) 특징:

1. ✓ Red-green compression ratio: **0.6 - 0.8** (압축)
2. ✓ Novel color bias: 녹색 → 노란색으로 **systematic shift**
3. ✓ MDS structure: 적-녹 축 **압축**
4. ✓ Classification confusion: 적-녹 쌍에서 **높은 confusion**
5. ✓ hV4에서 **가장 큰 차이**

### Non-CVD 특징:

1. ✓ Red-green compression ratio: **0.9 - 1.1** (정상)
2. ✓ Novel color bias: **무작위** 방향
3. ✓ MDS structure: **원형/균일**
4. ✓ Classification: **높은 정확도** (diagonal dominant)
5. ✓ 모든 ROI에서 **일관됨**

---

## Troubleshooting

### 문제 1: 모든 피험자가 비슷한 결과

**가능한 원인:**
1. 모든 피험자가 실제로 Non-CVD
2. Task가 색약 구분에 충분히 민감하지 않음
3. 8색이 충분하지 않음 (적-녹 쌍이 적음)

**해결책:**
- 더 많은 적-녹 색 추가
- Ishihara plate 등 behavioral test 확인
- 다른 메트릭 추가 (channel responses, PCA)

### 문제 2: ROI 간 차이가 없음

**가능한 원인:**
1. 모든 ROI가 비슷한 수준의 color processing
2. Voxel selection이 너무 엄격/느슨

**해결책:**
- Voxel selection 기준 조정
- 더 세분화된 ROI 사용 (Wang atlas의 sub-regions)

### 문제 3: 높은 variability

**가능한 원인:**
1. 피험자 수가 적음 (n=1 CVD)
2. Run 간 variability가 큼

**해결책:**
- 더 많은 피험자 모집
- Run 간 평균 사용
- Bootstrapping으로 신뢰구간 추정

---

## 다음 단계

1. ✅ **메트릭 추출** (`extract_colorblind_metrics.py`)
2. ✅ **그룹 비교** (`compare_subjects_cvd.py`)
3. ⏳ **PCA coordinates 저장** (reconstruction code 수정 필요)
4. ⏳ **Channel responses 저장** (reconstruction code 수정 필요)
5. ⏳ **ML Classifier 학습** (새 스크립트 필요)
6. ⏳ **Behavioral test 상관관계** (Ishihara plate vs neural metrics)

---

## 참고 문헌

- Brouwer & Heeger (2009): Forward encoding model
- Rabin et al. (2011): fMRI of color vision deficiency
- Conway (2009): Color vision in primates

---

**작성:** 2025-01-16
**최종 수정:** 2025-01-16
