# CVD 분석 Executive Summary
## 색각이상 신경-행동 해리 현상 요약

---

## 🎯 핵심 발견 (One-line Summary)

> **CVD 피험자의 V1~hV4 전체 시각 위계에서 색 신호는 디코딩 가능하지만,
> 특정 영역의 손상이 아닌 의사결정/통합 단계 실패 또는 개인별 이질적 손상 패턴을 보임**

---

## 📊 주요 결과

### 1. 신경 신호 (fMRI Decoding)

#### 1.1 Classification Accuracy

| ROI | Non-CVD | CVD | p-value | 차이 |
|-----|---------|-----|---------|------|
| **V1** | 60.8 ± 16.2% | 55.8 ± 2.2% | 0.513 | 없음 |
| **V2** | 47.3 ± 15.1% | 40.0 ± 11.1% | 0.355 | 없음 |
| **V3** | 25.0 ± 8.5% | 29.6 ± 6.8% | > 0.05 | 없음 |
| **hV4** | 26.7 ± 7.8% | 27.5 ± 9.1% | > 0.05 | 없음 |

- **Chance level**: 12.5% (8-way classification)
- **결론**: 모든 ROI에서 CVD vs Non-CVD 차이 없음

#### 1.2 Reconstruction Error (재구성 오차)

**ANOVA Feature Selection (전체 피험자):**

| ROI | Non-CVD | CVD | Difference | p-value |
|-----|---------|-----|------------|---------|
| **V1** | 46.7 ± 17.0° (n=6) | 42.4 ± 4.9° (n=3) | -4.2° | 0.694 |
| **V2** | 56.9 ± 16.8° (n=6) | 55.3 ± 5.1° (n=3) | -1.6° | 0.876 |
| **V3** | 82.8 ± 14.1° (n=6) | 78.9 ± 7.5° (n=3) | -3.9° | 0.675 |
| **hV4** | 82.1 ± 4.6° (n=6) | 76.3 ± 3.9° (n=3) | -5.9° | 0.105 |

- **Random error**: ≈90° (완전 무작위)
- **Good performance**: <45° (무작위의 절반)
- **계층적 성능 저하**: V1 (46-42°) < V2 (57-55°) < V3≈hV4 (79-82°)
- **통계 결론**: 모든 ROI에서 CVD vs NonCVD 차이 없음 (p > 0.05)

### 2. Red-Orange vs Green-Cyan 혼동 패턴

| ROI | Non-CVD (RO vs GC) | CVD (RO vs GC) | CVD 차이 | 예상 일치? |
|-----|-------------------|---------------|---------|-----------|
| **V1** | 32.8° vs 27.8° | 30.0° vs 46.1° | **-16.1°** (RO better) | ❌ |
| **V2** | 32.0° vs 44.7° | 51.8° vs 34.9° | **+16.9°** (RO worse) | ✓ |
| **V3** | 52.6° vs 74.4° | 63.2° vs 86.2° | **-23.0°** (RO better) | ❌ |
| **hV4** | 71.2° vs 89.0° | 76.5° vs 68.3° | **+8.2°** (RO worse) | ✓ |

- **예상**: CVD에서 Red-Orange가 Green-Cyan보다 더 나빠야 함 (적록 혼동)
- **실제**: ROI별로 상이한 패턴, 일관성 없음

### 3. 극단 케이스 (재구성 오차 > 100°)

| Subject | ROI | Color | Error | 해석 |
|---------|-----|-------|-------|------|
| sub-08 (CVD) | V3 | Cyan (225°) | 117.3° | Green-Cyan 구분 실패 |
| sub-08 (CVD) | V3 | Blue (270°) | 113.5° | Blue 재구성 불가 |
| sub-08 (CVD) | hV4 | Red (0°) | 114.7° | Red 재구성 불가 |

- **개인별 서로 다른 색상 문제**: 일관성 없음

---

## 💡 이론적 함의

### 신경-행동 해리 (Neural-Behavioral Dissociation)

**신경 측면 (fMRI)**:
- ✓ V1~hV4 모든 영역에서 색 정보 디코딩 가능
- ✓ CVD vs Non-CVD 차이 없음

**행동 측면 (실제 지각)**:
- ✗ CVD 피험자는 적록 구분 불가
- ✗ Ishihara 검사 실패

### 재해석된 처리 모델

```
[망막/LGN] → [V1/V2] → [V3] → [V4] → [의사결정/행동]
    ↓          ↓        ↓      ↓         ↓
  L-M 약화   약한 신호  약한 신호 약한 신호  통합/역치
                                           실패!
```

**결론**: 문제는 특정 피질 영역이 아닌 **의사결정/통합 단계**

---

## 🔍 가설

### 가장 유력한 3가지 가설

1. **의사결정/통합 실패 가설** (가장 유력)
   - V1~hV4의 약한 신호들이 의사결정 단계에서 통합되지 못함
   - 의식적 지각을 위한 역치(threshold) 통과 실패

2. **개인별 이질성 가설**
   - CVD는 단일 phenotype이 아님
   - 각 피험자마다 서로 다른 색 채널 손상
   - sub-08(Blue), sub-09(Green-Cyan), sub-10(Red-Orange)

3. **약한 신호 가설**
   - V1~hV4 모두 SNR 부족
   - MVPA는 검출 가능하지만 single-trial 행동에는 불충분

### 기각된 가설

- ~~V4 특정 손상 가설~~ → hV4도 차이 없음
- ~~초기 피질 부재 가설~~ → V1/V2에서 신호 존재

---

## ⚠️ 연구 한계

1. **표본 크기**: ROI당 CVD 1-2명만 (통계 검증 불가)
2. **개인차 > 그룹차**: 피험자 간 변동이 매우 큼
3. **복셀 수**: V3/hV4는 k=4-14로 매우 적음 (노이즈 취약)
4. **행동 데이터 없음**: fMRI-행동 직접 비교 불가

---

## 📋 향후 연구 방향

### 필수 분석

1. **표본 확대**: CVD 피험자 n ≥ 10
2. **개인별 프로파일링**: 이질적 손상 패턴 확인
3. **행동-신경 비교**: Psychophysics + fMRI
4. **의사결정 단계 분석**: Reaction time, confidence rating

### 실험 개선

1. **복셀 수 증가**: V3/hV4에서 k ≥ 50-100
2. **Functional localizer**: 개인별 color-selective ROI
3. **시간 해상도 분석**: FIR 모델

---

## 📁 관련 문서

- **CVD_NEURAL_DISSOCIATION_ANALYSIS_KR.md**: 전체 상세 분석 (10개 섹션)
- **EXECUTIVE_SUMMARY_FEATURE_SELECTION_KR.md**: Feature selection 전체 요약
- **per_color_reconstruction_config32.csv**: 색상별 데이터 (64 rows)
- **figures/**: 6개 시각화 (ROI 비교, 계층 비교, 극단 케이스)

---

## 📖 참고문헌

- Brouwer & Heeger (2009). *J. Neurosci.* - Color decoding & reconstruction
- Gegenfurtner & Kiper (2003). *Ann. Rev. Neurosci.* - V4 color constancy
- Dehaene & Changeux (2011). *Neuron* - Conscious access

---

**작성일**: 2025-12-13
**분석**: Config32_determin, ANOVA feature selection
**ROI**: V1, V2, V3, hV4 (전체 시각 위계)
**피험자**: NonCVD 6명, CVD 3명 (sub-08, 09, 10)
