# 📏 QC Metrics 빠른 참조 가이드

**목적**: 각 metric의 의미를 빠르게 참조

---

## 1️⃣ Dice Coefficient ⭐ (가장 중요)

```
공식: Dice = 2 × |A ∩ B| / (|A| + |B|)
```

**의미**: T1 brain mask와 BOLD brain mask의 overlap 정도

**범위**: 0 (완전 불일치) ~ 1 (완전 일치)

**해석**:
- ≥ 0.90: **Excellent** ⭐⭐⭐ → 바로 사용
- ≥ 0.85: **Good** ⭐⭐ → 사용 가능
- ≥ 0.80: **Acceptable** ⭐ → 주의하여 사용
- < 0.80: **Poor** ❌ → 제외

**우리 결과**: Mean 0.889, Median 0.945

**왜 중요한가**: Registration 품질의 직접 지표. Dice < 0.80이면 ROI가 잘못된 위치에 매핑됨.

---

## 2️⃣ Overlap Fraction

```
공식: Overlap = |A ∩ B| / |B|
```

**의미**: BOLD brain mask의 몇 %가 T1 brain mask 안에 있는가

**범위**: 0 ~ 1

**해석**:
- ≥ 0.90: BOLD가 T1 안에 잘 포함됨
- < 0.70: BOLD 일부가 T1 밖 (문제!)

**우리 결과**: Mean 0.949

**Dice와의 차이**:
```
Dice = 양쪽 크기 고려
Overlap = BOLD 기준만

High Overlap + Low Dice = T1 mask가 과도하게 큼 (Sub-06, 07)
```

---

## 3️⃣ T1/BOLD Mask Ratio

```
공식: Ratio = |T1 mask| / |BOLD mask|
```

**의미**: T1 brain mask가 BOLD보다 몇 배 큰가

**이상적**: ~1.0 (비슷한 크기)

**해석**:
- 0.8-1.5: 정상
- > 2.0: T1 over-extraction (Sub-06, 07)
- < 0.7: BOLD가 더 큼 (드묾)

**우리 결과**: 대부분 1.0-1.5, Sub-06/07은 ~3.0

**왜 중요한가**: High overlap but low Dice의 원인 설명

---

## 4️⃣ ROI Voxel Count

```
ROI voxels = Transform 후 threshold 적용한 voxel 개수
```

**의미**: V1/V2/V3/V4 ROI에 몇 개 voxel이 생성되었는가

**해석**:
- = 0: **ROI_ZERO** (transform 실패 또는 threshold 너무 높음)
- < 10: 너무 작음 (신뢰도 낮음)
- 100-5000: 정상 범위

**우리 결과**:
- Old: 45.4% ROI_ZERO
- New: 0% ROI_ZERO ✅

**ROI별 크기**:
- V1: 2000-3500 (가장 큼)
- V2, V3: 1000-3000
- V4: 500-700 (작지만 정상)

---

## 5️⃣ ROI Coverage

```
공식: Coverage = |ROI ∩ Brain| / |ROI|
```

**의미**: 생성된 ROI의 몇 %가 brain mask 안에 있는가

**해석**:
- ≥ 0.90: ROI가 brain 안에 잘 위치
- < 0.70: ROI 일부가 brain 밖 (문제!)

**우리 결과**: 대부분 > 0.95

---

## 6️⃣ Dropout Metric 1

```
공식: Metric1 = p10(ROI) / median(Brain)
```

**의미**: ROI의 가장 낮은 10% signal이 whole brain 대비 얼마나 되는가

**해석**:
- ≥ 0.70: Good
- 0.50-0.70: Moderate dropout
- < 0.50: Severe dropout

**우리 결과**: 대부분 > 0.90

**왜 중요한가**: Susceptibility artifacts (air-tissue interface) 감지

---

## 7️⃣ Dropout Metric 2

```
공식: Metric2 = median(ROI) / median(Brain)
```

**의미**: ROI의 중간값 signal이 whole brain 대비 얼마나 되는가

**해석**:
- ≥ 0.90: Excellent
- 0.70-0.90: Good
- < 0.70: Moderate issues

**우리 결과**: 대부분 > 0.95

**Metric1과의 차이**:
- Metric1: Worst-case scenario (p10)
- Metric2: Typical case (median)

---

## 8️⃣ Framewise Displacement (FD)

```
FD = 머리 움직임의 크기 (mm)
```

**해석**:
- < 0.2mm: Excellent
- < 0.3mm: Good
- < 0.5mm: Acceptable
- ≥ 0.5mm: 문제 (scrubbing 고려)
- ≥ 0.9mm: Severe (제외)

**우리 결과**: 0.1-0.2mm (Excellent!)

---

## 🎯 Metric 우선순위

### **필수 체크 (이것만 봐도 OK)**:

1. **Dice** ≥ 0.80
2. **ROI voxels** > 0
3. **FD** < 0.5mm

→ 3개 모두 pass면 사용 가능!

### **문제 진단용**:

**Dice < 0.80인데 Overlap > 0.90**:
→ T1 mask ratio 확인 (over-extraction 의심)

**ROI voxels = 0**:
→ Transform 실패 또는 threshold 문제

**Dropout metrics < 0.70**:
→ Signal quality 문제 (physical limitation)

---

## 📊 우리 결과 요약표

| Metric | Mean | Median | Pass Rate | 평가 |
|--------|------|--------|-----------|------|
| **Dice** | 0.889 | 0.945 | 83.3% (≥0.80) | ✅ Excellent |
| **Overlap** | 0.949 | 0.973 | 95%+ | ✅ Excellent |
| **ROI voxels** | ~2000 | - | 100% (>0) | ✅ Perfect |
| **Dropout M1** | ~0.95 | - | 99%+ | ✅ Excellent |
| **Dropout M2** | ~0.98 | - | 99%+ | ✅ Excellent |
| **FD** | ~0.15mm | - | 100% (<0.5) | ✅ Excellent |
| **Mask ratio** | ~1.3 | - | 80% (1-2) | ✅ Good |

---

## 🔍 Subject별 빠른 진단

### **Excellent (7명)**:
```
Sub-01, 03, 04, 08, 09, 10
Dice ≥ 0.93, Pass 100%
→ 모든 분석 가능
```

### **Good (2명)**:
```
Sub-02, 05
Dice ~0.82-0.92, Pass 83%
→ 대부분 분석 가능, 일부 run 제외 고려
```

### **Partial (2명)**:
```
Sub-06, 07
Dice ~0.73-0.75, Pass 33%
→ Individual-level만, good runs 선별
→ 원인: T1 mask over-extraction (ratio 3.0)
```

---

## 💡 한 줄 요약

**Dice > 0.80 + ROI voxels > 0 + FD < 0.5mm = 분석 가능!**

---

**비행 중 빠른 참조용**
**1-2분이면 이해 가능**
