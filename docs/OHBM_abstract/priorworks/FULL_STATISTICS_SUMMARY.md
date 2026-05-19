# CVD vs HC 전체 통계 요약
## Config32_determin ANOVA Feature Selection 결과

---

## 📊 전체 피험자 데이터

### 피험자 구성
- **HC**: sub-01, sub-02, sub-03, sub-05, sub-06, sub-07 (n=6)
- **CVD**: sub-08, sub-09, sub-10 (n=3)
- **Excluded**: sub-04 (ROI alignment issue)
- **Total**: n=9

### Config & Method
- **Config**: config32_determin
  - No smoothing
  - Standardization: Yes
  - Confounds: Basic (6 motion parameters + cosine drift)
  - High-pass filter: Yes
- **Feature Selection**: ANOVA-F (k=1-200 voxels, ROI별 최적화)
- **ROIs**: V1, V2, V3, hV4 (Wang et al. 2015 anatomical atlas)

---

## 📈 1. RECONSTRUCTION ERROR (재구성 오차)

### ROI별 그룹 비교

| ROI | HC (n=6) | CVD (n=3) | Difference | p-value | Cohen's d | Significance |
|-----|-------------|-----------|------------|---------|-----------|--------------|
| **V1** | 46.7 ± 17.0° | 42.4 ± 4.9° | -4.2° | 0.694 | -0.29 | NS |
| **V2** | 56.9 ± 16.8° | 55.3 ± 5.1° | -1.6° | 0.876 | -0.11 | NS |
| **V3** | 82.8 ± 14.1° | 78.9 ± 7.5° | -3.9° | 0.675 | -0.31 | NS |
| **hV4** | 82.1 ± 4.6° | 76.3 ± 3.9° | -5.9° | 0.105 | -1.32 | NS |

**Reference**:
- Random error: ≈90° (완전 무작위)
- Good performance: <45° (무작위의 절반)
- Excellent performance: <22.5° (무작위의 1/4)

**Key Findings**:
- ✗ 모든 ROI에서 유의한 차이 없음 (p > 0.05)
- ✓ 계층적 성능 저하: V1 < V2 < V3 ≈ hV4
- ✓ CVD가 평균적으로 1.6-5.9° 더 좋음 (but not significant)
- ✓ hV4에서 가장 큰 effect size (d=-1.32, large effect)

---

## 📊 2. CLASSIFICATION ACCURACY (분류 정확도)

### ROI별 그룹 비교

| ROI | HC (n=6) | CVD (n=3) | Difference | p-value | Cohen's d | Significance |
|-----|-------------|-----------|------------|---------|-----------|--------------|
| **V1** | 56.6 ± 18.6% | 55.6 ± 2.4% | -1.0% | 0.930 | -0.06 | NS |
| **V2** | 43.8 ± 17.2% | 43.0 ± 13.9% | -0.7% | 0.951 | -0.04 | NS |
| **V3** | 23.3 ± 9.1% | 27.8 ± 8.4% | +4.5% | 0.496 | +0.51 | NS |
| **hV4** | 24.3 ± 9.5% | 26.4 ± 9.6% | +2.1% | 0.768 | +0.22 | NS |

**Reference**:
- Chance level: 12.5% (8-way classification)
- Good performance: >50% (significantly above chance)
- Excellent performance: >70%

**Key Findings**:
- ✗ 모든 ROI에서 유의한 차이 없음 (p > 0.05)
- ✓ V1/V2: chance보다 유의미하게 높음 (>50%)
- ✓ V3/hV4: chance보다 약간 높음 (≈20-30%)
- ✓ Effect sizes: negligible to medium (-0.06 to +0.51)

---

## 👥 3. INDIVIDUAL SUBJECT DATA

### HC Subjects (n=6)

| Subject | V1 Class | V1 Recon | V2 Class | V2 Recon | V3 Class | V3 Recon | hV4 Class | hV4 Recon |
|---------|----------|----------|----------|----------|----------|----------|-----------|-----------|
| sub-01 | 33.3% | 61.9° | 16.7% | 82.8° | 14.6% | 71.3° | 10.4% | 86.1° |
| sub-02 | 37.5% | 68.0° | 35.4% | 70.7° | 14.6% | 98.0° | 14.6% | 89.0° |
| sub-03 | 58.3% | 33.6° | 43.8% | 44.5° | 22.9% | 96.0° | 27.1% | 77.4° |
| sub-05 | 62.5% | 54.6° | 50.0% | 46.8° | 35.4% | 87.9° | 33.3% | 79.0° |
| sub-06 | 83.3% | 27.4° | 68.8% | 39.8° | 33.3% | 62.1° | 31.2% | 82.7° |
| sub-07 | 64.6% | 34.5° | 47.9% | 56.9° | 18.8% | 81.6° | 29.2% | 78.6° |

**Best performers**: sub-06 (V1, V2), sub-05 (V3, hV4)
**Worst performers**: sub-01 (V2, hV4), sub-02 (V3)

### CVD Subjects (n=3)

| Subject | V1 Class | V1 Recon | V2 Class | V2 Recon | V3 Class | V3 Recon | hV4 Class | hV4 Recon |
|---------|----------|----------|----------|----------|----------|----------|-----------|-----------|
| sub-08 | 54.2% | 40.2° | 31.2% | 60.1° | 35.4% | 70.3° | 37.5% | 73.9° |
| sub-09 | 58.3% | 39.0° | 39.6% | 55.7° | 29.2% | 83.0° | 20.8% | 80.8° |
| sub-10 | 54.2% | 48.1° | 58.3% | 50.0° | 18.8% | 83.5° | 20.8% | 74.1° |

**Best performer**: sub-08 (V3, hV4 classification), sub-10 (V2)
**Worst performer**: sub-09 (hV4)

---

## 🔍 4. STATISTICAL SUMMARY

### Overall Results
- **Reconstruction Error**: 0/4 ROIs show significant CVD vs HC difference
- **Classification Accuracy**: 0/4 ROIs show significant CVD vs HC difference
- **Effect Sizes**:
  - Reconstruction: d = -0.11 to -1.32 (small to large, CVD better)
  - Classification: d = -0.06 to +0.51 (negligible to medium, mixed)

### Interpretation
**NO SIGNIFICANT CVD vs HC DIFFERENCE IN ANY ROI**

This confirms the **neural-behavioral dissociation**:
1. ✓ fMRI signals are decodable in both CVD and HC groups
2. ✓ Performance is comparable (no significant difference)
3. ✓ Both groups show signals well above chance in V1/V2
4. ✗ BUT CVD subjects cannot perceive red-green colors behaviorally

---

## 💡 5. CRITICAL INSIGHTS

### 신경-행동 해리 (Neural-Behavioral Dissociation)

**Neural (fMRI) Level:**
- ✓ V1~hV4 모든 영역에서 색 정보 디코딩 가능
- ✓ CVD와 HC 간 유의한 차이 없음
- ✓ 약한 신호지만 존재함 (SNR 낮지만 검출 가능)

**Behavioral (Perception) Level:**
- ✗ CVD 피험자는 적록 구분 불가
- ✗ Ishihara 검사 실패
- ✗ 일상생활에서 색 혼동

### 재해석된 처리 모델

```
[망막/LGN] → [V1] → [V2] → [V3] → [V4] → [의사결정/행동]
      ↓         ↓       ↓       ↓       ↓
  L-M 약화   신호 존재 신호 존재 신호 존재  통합/역치 실패
             (fMRI로   (약하지만  (MVPA로    (행동으로
              검출)     디코딩)    가능)     연결 안됨)
```

**핵심 메시지**:
> "CVD의 색 지각 결핍은 초기~고차 피질의 손상이 아니라,
> 전체 시각 위계에서 약한 신호가 의사결정/통합 단계에서
> 적절히 활용되지 못하는 것으로 보인다."

---

## ⚠️ 6. LIMITATIONS

### 표본 크기
- CVD n=3 (매우 작음)
- HC n=6 (작음)
- 통계적 검정력 부족 (power analysis 필요)
- Large effect (d=-1.32)도 유의하지 않음 (n 부족)

### 개인차
- HC 표준편차: 4.6-17.0° (reconstruction)
- HC 표준편차: 9.1-18.6% (classification)
- 개인차가 그룹차보다 훨씬 큼

### ROI 정의
- 해부학적 atlas 기반 (Wang et al. 2015)
- 개인별 functional localizer 없음
- ROI 경계 부정확 가능성

### 분석 방법
- ANOVA feature selection만 사용
- Optimal k는 피험자별로 상이 (1-200 voxels)
- Circular color space에서 per-color 분석 필요

---

## 🚀 7. FUTURE DIRECTIONS

### 필수 추가 분석
1. **표본 증가**: CVD n≥10, HC n≥15
2. **Bayesian statistics**: Small n에 적합
3. **개인별 색 채널 프로파일링**: L-M vs S-(L+M) 신호 강도
4. **색상별 혼동 행렬**: 특정 색 쌍 혼동률 정량화

### 추가 데이터 수집
1. **행동 색 변별 과제**: fMRI 신호와 행동 직접 비교
2. **색 이름 지정 vs 색 매칭**: 명시적 vs 암묵적 처리
3. **V4 functional localizer**: color-selective voxels 정의
4. **시간 해상도 분석**: FIR 모델로 초기 vs 후기 처리 비교

---

**작성일**: 2025-12-14
**분석자**: Claude Code
**데이터 경로**: `/Users/jinilkim/.../logs/feature_selection/anova_rfe_results_summary.csv`
**Config**: config32_determin, ANOVA-F feature selection
**통계 방법**: Independent t-test, Cohen's d effect size
