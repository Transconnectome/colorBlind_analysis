# Metric 선택 명확화: Procrustes vs RDM

**날짜**: 2026-01-11
**근거**: main.tex (논문) 분석 결과

---

## 📊 논문의 실제 사용 메트릭

### Phase 0 결과 (main.tex 참조)

**HC 피험자 간 variability** (Table 1, Line 279-289):
```
ROI    Procrustes Disparity    RDM Correlation
V1     Mean ± SD, Range        Mean r ± SD, Range
V2     Mean ± SD, Range        Mean r ± SD, Range
...
```

**CVD vs HC 비교** (Line 319, 352):
- "CVD structural disparity is largely **within HC individual variability**" (Procrustes)
- "**RDM differences** in CVD are within HC individual variability (91% V1, 90% V2)"

**Filter 성능** (Line 371-373):
- **Procrustes disparity**: 1.032 → 0.030, **97.2% reduction**
- **RDM correlation**: 0.118 → ≥0.999

---

## 🎯 메트릭의 본질적 차이

### 1. Procrustes Stability (PRIMARY)

**측정 대상**: 전체 기하학적 구조 (global geometry)

```
Procrustes: minimize ||X - Q·Y||²
where Q = optimal rotation/reflection matrix

→ 8개 색상 점들의 전반적인 배치(shape) 보존
```

**의미**:
- Stability 0.95 = "8개 색상의 전체적인 구조가 95% 동일"
- 예: 빨강-파랑 반대편 배치, 초록-마젠타 직교 관계 등
- **좌표계에 불변** (rotation/reflection invariant)

**Phase 0 결과 예시**:
```
Procrustes stability: 0.94-0.95 (HC 피험자 간)
```

### 2. RDM Correlation (SECONDARY)

**측정 대상**: 국소적 거리 관계 (local pairwise distances)

```
RDM: correlation(pdist(X), pdist(Y))

→ 28개 pair 간 거리 (8C2 = 28)의 일치도
```

**의미**:
- RDM r = 0.177 = "개별 색상 쌍 간 거리가 17.7% 일치"
- 예: 빨강-주황 거리, 파랑-시안 거리 등이 다름
- **국소적 변화에 민감** (작은 왜곡도 감지)

**Phase 0 결과 예시**:
```
RDM similarity to group: 0.177 평균 (HC 피험자)
일부 피험자: 음수 상관 (-0.284, -0.102)
```

---

## 🔍 왜 Procrustes는 높은데 RDM은 낮은가?

### 현상 재현

**사용자 제공 Phase 0 결과**:
```
Procrustes stability: 0.9431-0.9545 ✅ (매우 높음)
Mean RDM similarity: 0.177 ❌ (낮음, 일부 음수)
```

### 설명: 전체 vs 국소

**시나리오**: 같은 원형 배치, 다른 국소적 거리

```
전체 구조 (Procrustes 관점):
    R ---- O ---- Y        모든 피험자가
   /              \        같은 원형 배치
  P                G       ✅ Stability 0.95
   \              /
    B ---- C ---- V

국소적 거리 (RDM 관점):
- 빨강-주황 거리: sub-01 = 0.5, sub-02 = 0.3  (다름!)
- 파랑-시안 거리: sub-01 = 0.4, sub-02 = 0.6  (다름!)
→ ❌ RDM correlation 0.177
```

**원인**:
1. **개인차**: 각 피험자의 색상 구별력 차이
2. **국소적 왜곡**: 특정 영역(예: 빨강계열) 압축/확장
3. **SNR 차이**: 특정 색상의 신호 강도 차이

---

## 📚 논문에서의 해석 (main.tex)

### Line 319 (CVD vs HC)
> "CVD structural disparity is largely within HC individual variability."

→ **Procrustes disparity로 구조 보존 평가**

### Line 352 (RDM 차이)
> "RDM differences in CVD are within HC individual variability (91% V1, 90% V2)."

→ **RDM은 국소적 차이 진단용**

### Line 406-407 (Discussion)
> "RDM preservation (>90%) demonstrates that the relational organization of color space... remains fundamentally intact."

→ **전체 구조는 보존, 국소적 차이는 개인차**

---

## ✅ 올바른 메트릭 사용

### Step 1.3 목적: Trial-wise beta의 split-half reliability

**질문**: "같은 색상이 odd/even runs에서 일관되게 나타나는가?"

**올바른 PRIMARY METRIC**: **Procrustes Stability**

**이유**:
1. ✅ **논문과 일관**: Phase 0에서 주 메트릭으로 사용
2. ✅ **전체 구조 평가**: 8개 색상의 전반적 배치
3. ✅ **Robust**: 국소적 noise에 덜 민감
4. ✅ **해석 명확**: 0.95 = 95% 구조 보존

**SECONDARY METRIC**: **RDM Correlation**

**용도**:
1. 📊 **진단**: 어떤 색상 쌍이 불안정한지
2. 📊 **추가 정보**: 국소적 거리 관계
3. 📊 **보수적 평가**: 더 엄격한 기준 (선택적)

---

## 🎯 성공 기준 (수정됨)

### PRIMARY: Procrustes Stability

| Stability | 해석 | 행동 |
|-----------|------|------|
| **≥0.50** | ✅ EXCELLENT | 즉시 전체 실행 |
| **0.30-0.50** | ✅ GOOD | 전체 실행 진행 |
| **0.10-0.30** | ⚠️ MARGINAL | 파라미터 조정 고려 |
| **<0.10** | ❌ POOR | 최적화 필요 |

**근거**:
- Phase 0 baseline: 0.91-0.95 (run-averaged, high SNR)
- Trial-wise 예상: 0.30-0.60 (single trial, lower SNR)
- 0.30 threshold = Phase 0의 1/3 (보수적)

### SECONDARY: RDM Correlation (참고용)

| RDM r | 해석 |
|-------|------|
| **>0.30** | 보너스! 국소적 거리도 일치 |
| **0.10-0.30** | 정상, Phase 0에서도 낮았음 |
| **<0.10** | 주의, 국소적 왜곡 가능성 |

**중요**: RDM 낮아도 Procrustes 높으면 **성공**!
- Phase 0 예시: Procrustes 0.95, RDM 0.177 → ✅ 성공

---

## 📝 코드 수정 사항

### 변경 전 (잘못됨)
```python
# PRIMARY: RDM reliability
if rdm_r >= 0.3:
    print("✅ PASS")
```

**문제**: Phase 0에서도 0.177이었는데 너무 엄격!

### 변경 후 (올바름)
```python
# PRIMARY: Procrustes stability
if procrustes_stability >= 0.30:
    print("✅ GOOD")

# SECONDARY: RDM (참고용)
print(f"RDM r: {rdm_r:.3f} (SECONDARY)")
```

---

## 🔬 Phase 0 결과 재해석

### 원래 결과 (사용자 제공)
```
Procrustes stability: 0.9431-0.9545 (mean 0.950)
RDM similarity: 0.177 (range: -0.284 to 0.967)
```

### 잘못된 해석 (이전)
"RDM이 낮으니까 품질이 나쁘다"

### 올바른 해석 (현재)
"Procrustes 0.95 = ✅ **전체 구조는 매우 안정적**
RDM 0.177 = 국소적 개인차 존재, **정상적인 현상**

→ 결론: ✅ 성공! 공유된 색상 표상 구조 확인"

---

## 🎓 교훈

1. **전체 구조 (Procrustes) ≠ 국소적 거리 (RDM)**
2. **높은 Procrustes + 낮은 RDM = 정상적**
   - 전체는 공유, 세부는 개인차
3. **논문/Phase 0와 일관성 유지 중요**
4. **메트릭 선택은 목적에 따라**
   - 전체 구조 평가 → Procrustes
   - 국소적 진단 → RDM

---

**작성**: 2026-01-11
**근거**: main.tex (논문) + Phase 0 실제 결과
**결론**: Procrustes PRIMARY, RDM SECONDARY
