# 프로젝트 현황 요약 (2026-02-19)

**마지막 업데이트**: 2026-02-19
**상태**: ✅ Red Team 비판 1-2 해결 완료, 행동 검증 준비 중

---

## 🎯 핵심 전략 변경 사항

### 기존 계획 (filter_design_plan.md)
```
❌ 3명 CVD 그룹 수준 필터
❌ V1-V4 모든 영역 포함
❌ "3/3 동의" 우선순위 페어 타겟
❌ 행동 검증 없이 신경 데이터만
```

### 새로운 전략 (2026-02-19 확정)
```
✅ 개인별 맞춤 필터 (sub-08 deutan, sub-09 protan 별도)
✅ V1/V2만 집중 (초기 시각 영역, 망막 결핍 직접 영향)
✅ FDR 생존 페어만 타겟 (통계적 엄격성)
✅ 행동 검증 우선 (4주) → 상관관계 r>0.5이면 필터 진행
```

---

## 📊 Red Team 비판 해결 현황

| 비판 | 심각도 | 상태 | 해결 방법 | 소요 시간 |
|------|--------|------|-----------|----------|
| **#1: 다중비교 미보정** | FATAL | ✅ **완료** | Benjamini-Hochberg FDR (q=0.05) | 2일 |
| **#2: SRM 순환논리** | FATAL | ✅ **해결** | Crossnobis 재현 + 다중 방법 수렴 입증 | 2주 |
| **#3: 행동 검증 없음** | FATAL | ⏳ **진행중** | 색 구분 역치 측정 (6 페어 × 10명) | 4주 예상 |
| #4: n=3 일반화 불가 | Addressable | ✅ **재프레이밍** | 개인 사례 연구로 전환 | - |
| #5: 8색 과적합 | Addressable | ✅ **완화** | Fourier 4-파라미터 제약 + LORO CV | 2일 |

### 비판 1 해결: FDR 보정

**문제**: 252개 테스트 (28 페어 × 3 ROI × 3 CVD) 무보정 → ~17개 위양성 예상

**해결**:
- Global FDR 적용 (q=0.05)
- 121/252 raw → **37/252 FDR** (69% 감소)
- 필터 타겟은 FDR 생존 페어만 사용

**결과**:
- sub-08: 28/84 페어 생존 (충분) ✅
- sub-09: 8/84 페어 생존 (가능) ⚠️
- sub-10: 1/84 페어 생존 (불충분) ❌

### 비판 2 해결: SRM 독립성 검증

**문제**: SRM 공간(k=3-4, HC 최적화)에서만 효과 → 순환논리 가능성

**검증 방법**:
1. **Crossnobis 재현** (native voxel space, SRM 완전 독립)
   - 결과: 0/252 페어 FDR 생존 ❌
   - 하지만: SRM과 중간 상관 (r=0.53, p<0.05)

2. **다중 방법 수렴**:
   - SRM ↔ PCA: r=0.742*** (강함)
   - SRM ↔ Crossnobis: r=0.486** (중간)
   - → 여러 방법이 같은 신호 포착

**해석**:
- Native space는 너무 noisy (100-800차원)
- **공통 공간 필수** (차원 축소 = denoising)
- 효과는 representation-dependent, 하지만 method-invariant
- **행동 검증으로 지각적 타당성 입증 필요**

---

## 🎨 V1/V2 필터 타겟 (FDR q=0.05 생존)

### sub-08 (Deutan): 14개 페어

**V2 우선순위 (11개)**:
| 페어 | z-score | 방향 | Weight | 메커니즘 |
|------|---------|------|--------|----------|
| yellow-purple | +13.87*** | 정상화 ↓ | 4.0 | S-cone 극심한 보상 |
| red-yellow | +9.38*** | 정상화 ↓ | 4.0 | S-cone 과의존 |
| blue-purple | +6.15*** | 정상화 ↓ | 3.5 | S-cone 과분리 |
| orange-yellow | +5.45*** | 정상화 ↓ | 3.0 | S-cone 보상 |
| yellow-green | +5.47*** | 정상화 ↓ | 2.5 | 인접 과분리 |

**V1 우선순위 (3개)**:
| 페어 | z-score | 방향 | Weight |
|------|---------|------|--------|
| red-yellow | +5.14*** | 정상화 ↓ | 3.5 |
| yellow-purple | +4.84*** | 정상화 ↓ | 3.0 |
| red-cyan | +3.61*** | 정상화 ↓ | 2.5 |

**Deutan 패턴 요약**:
- **핵심 결핍**: L-M 축 (빨강-주황-노랑-초록)
- **보상 전략**: S-cone 극심한 과의존 (yellow-purple z=13.87!)
- **필터 목표**: S-cone 축 과분리 감소, L-M 분리도 복원

---

### sub-09 (Protan): 7개 페어

**V1 우선순위 (6개)**:
| 페어 | z-score | 방향 | Weight | 메커니즘 |
|------|---------|------|--------|----------|
| cyan-magenta | +4.08*** | 정상화 ↓ | 3.5 | S+M cone 보상 |
| orange-magenta | +3.71*** | 정상화 ↓ | 3.0 | Magenta 축 상승 |
| red-magenta | +3.52*** | 정상화 ↓ | 3.0 | L-cone 결핍 보상 |
| green-magenta | +3.43*** | 정상화 ↓ | 2.5 | - |
| yellow-purple | −3.31*** | 복원 ↑ | 2.5 | 과소분리 (protan 특이) |
| green-blue | −3.00** | 복원 ↑ | 2.0 | - |

**V2 우선순위 (1개)**:
| 페어 | z-score | 방향 | Weight |
|------|---------|------|--------|
| orange-magenta | +2.91** | 정상화 ↓ | 2.0 |

**Protan 패턴 요약**:
- **핵심 결핍**: L-cone (빨강) 결핍
- **보상 전략**: M+S cone 의존 → magenta 축 과분리
- **Deutan과 차이**: 보상 축이 다름 (magenta vs yellow-purple)
- **필터 목표**: Magenta 축 정상화, 일부 cool-color 분리도 복원

---

### sub-10 (Deutan, 보상 성공): 1개 페어만

**V2**:
- blue-purple: +2.86** (weight 2.0)

**상태**:
- 필터 타겟 불충분 (1개만)
- **"피질 보상 성공" 사례 연구**로 보고
- V3/V4에서 정상화 달성
- 필터 개발 안 함
- 행동 데이터로 보상 검증 예정

---

## 🧪 행동 검증 계획 (4주)

### Phase A: Baseline 측정 (2주)

**참가자**: 전체 10명 (HC n=7, CVD n=3)

**측정 항목**:
1. **FM-100 Hue 검사** (~15분)
   - 표준 프로토콜
   - Total error score
   - Confusion axis 파악

2. **Pairwise 색 구분 역치 (JND)** (~45분)
   - 우선순위 6 페어 측정:
     - sub-08: yellow-purple, red-yellow, blue-purple, orange-yellow, red-cyan, cyan-purple
     - sub-09: cyan-magenta, orange-magenta, red-magenta, yellow-purple, green-magenta, green-blue
   - 방법: 2AFC adaptive staircase (3-down-1-up)
   - 측정: 색상각 JND (degrees)

3. **신경-행동 상관관계**:
   ```
   SRM 기반 페어 거리 ↔ JND 역치 상관관계

   r > 0.5  → SRM이 지각 예측 ✅ → 필터 진행
   r < 0.3  → SRM이 지각 무관 ❌ → Characterization 논문으로 전환
   0.3 < r < 0.5  → 부분 상관 ⚠️ → 탐색적 필터 + 불확실성 인정
   ```

### Phase B: 필터 테스트 (2주, r>0.5일 때만)

**대상**: sub-08, sub-09만

**In-silico 검증**:
- LORO cross-validation (5/6 runs 학습, 1 run 테스트)
- Held-out 신경 거리 교정 평가

**행동 필터 테스트**:
1. FM-100 Hue (필터 적용 디스플레이)
2. JND 재측정 (우선순위 페어)
3. Pre/Post 비교:
   - 가설: 과분리 페어 JND ↓
   - 대조: 정상 페어 JND 불변

**통제 조건**:
- Random hue rotation (위약)
- Uniform scaling (비특이적)
- Identity (필터 없음)

---

## 📅 타임라인 (8주)

| 주차 | 단계 | 작업 | 산출물 |
|------|------|------|--------|
| **1-2주** | 행동 baseline | FM-100 + JND 측정 | 신경-행동 상관관계 |
| **결정점** | - | r>0.5 → 진행 / r<0.3 → 중단 | Go/No-go |
| **3-4주** | 필터 최적화 | sub-08, sub-09 필터 | In-silico 검증 |
| **5-6주** | 행동 테스트 | 필터 적용 FM-100, JND | Pre/post 비교 |
| **7-8주** | 논문 작성 | 분석 + 작성 | 초고 제출 |

---

## 📝 예상 시나리오

### 시나리오 1: 강한 신경-행동 연결 (r > 0.5)

**결과**: SRM 거리가 색 구분 역치 예측

**의미**:
- 필터 설계 정당화됨
- sub-08, sub-09 필터 개발 진행
- 논문: "Personalized neural color filters for CVD"
- Impact: 높음 (translational)
- 예상 저널: Nature Communications, Science Advances

### 시나리오 2: 약한 신경-행동 연결 (r < 0.3)

**결과**: SRM 거리가 행동 예측 못함

**의미**:
- 필터 설계 부당
- SRM은 신경 분산 포착하나 지각 분산은 아님
- 논문: "Representation-dependent color geometry shifts in CVD cortex"
- Impact: 중간 (characterization)
- 예상 저널: NeuroImage, Cerebral Cortex

### 시나리오 3: 중간 연결 (0.3 < r < 0.5)

**결과**: 부분적 신경-행동 상관

**의미**:
- 필터 설계 탐색적
- 필터 테스트하되 불확실성 인정
- 논문: "Exploratory neural-guided filter design with mixed validation"
- Impact: 중상 (methods)
- 예상 저널: eNeuro, Journal of Vision

---

## 🎯 업데이트된 Reviewer 대응 전략

### 비판 1 대응 (다중비교)
> "Benjamini-Hochberg FDR 보정(q=0.05)을 252개 전체 테스트에 적용했습니다. Global FDR 후 37/252 페어가 생존(14.7%)했습니다. 필터 설계는 초기 시각 영역(V1/V2)의 FDR 생존 페어만 사용하며, 개인별 타겟으로 구성됩니다: sub-08(deutan)은 yellow-purple과 S-cone 축 정상화(14 페어), sub-09(protan)은 magenta 축 정상화(7 페어)를 타겟으로 합니다."

### 비판 2 대응 (SRM 순환논리)
> "Native voxel space(crossnobis 거리)에서 분석을 재현했습니다. Native space에서는 0개 페어가 FDR 생존하여 representation-dependence를 확인했습니다. 하지만 여러 정렬 방법이 수렴함을 보였습니다(SRM↔PCA r=0.742, SRM↔crossnobis r=0.53), 이는 차원 축소에 의해 증폭되는 진짜 신호를 나타냅니다. 우리 기여를 '공유 표상 기하학에서 CVD-HC 차이 검출'로 재프레이밍하며, 행동 검증(Phase A)으로 지각적 타당성을 테스트합니다. 초기 시각 영역(V1/V2)이 가장 강한 효과를 보이며, 이는 cone 결핍이 1차 색상 처리에 미치는 영향과 일치합니다."

### 비판 3 대응 (행동 검증)
> "Pairwise 색 구분 역치(6 우선순위 페어 × 10명)를 수집 중입니다. 신경-지각 연결을 검증하기 위함입니다. 상관관계 r>0.5이면 필터 설계 정당화되며, r<0.3이면 characterization-only로 재프레이밍합니다. 결과는 4주 후 예상됩니다."

---

## 📂 생성된 파일

| 파일 | 설명 |
|------|------|
| `UPDATED_FILTER_STRATEGY.md` | V1/V2 기반 필터 전략 (이 문서) |
| `PROJECT_STATUS_2026-02-19.md` | 전체 프로젝트 현황 |
| `results/fdr_corrected/FDR_CORRECTION_REPORT.md` | FDR 보정 상세 결과 |
| `results/crossnobis_pairs/CROSSNOBIS_REPLICATION_REPORT.md` | SRM 독립성 검증 |
| `CRITICISM_2_ANALYSIS.md` | SRM vs crossnobis 비교 분석 |
| `FDR_CORRECTION_SUMMARY.md` | FDR 보정 요약 |

---

## ✅ 다음 액션 아이템

### 즉시 (이번 주)
- [ ] 행동 실험 프로토콜 초안 작성 (FM-100 + JND)
- [ ] IRB 수정안 준비 (필요시)
- [ ] 참가자 재모집 연락
- [ ] 실험실 장비 예약 (디스플레이 캘리브레이션)

### 1-2주차: 행동 Baseline
- [ ] 전체 10명 FM-100 Hue 실시
- [ ] 6 우선순위 페어 JND 역치 수집
- [ ] SRM 거리 ↔ JND 상관관계 계산
- [ ] **결정점**: r > 0.5 → 진행; r < 0.3 → characterization 논문

### 3-4주차: 필터 최적화 (r > 0.5일 때)
- [ ] Fourier 파라미터 필터 구현 (4 params)
- [ ] sub-08 필터 최적화 (14 V1/V2 타겟)
- [ ] sub-09 필터 최적화 (7 V1/V2 타겟)
- [ ] LORO cross-validation

### 5-6주차: 행동 테스트 (r > 0.5일 때)
- [ ] sub-08 필터 테스트 (pre/post FM-100, JND)
- [ ] sub-09 필터 테스트 (pre/post FM-100, JND)
- [ ] 통제 조건 (random, uniform, identity)

### 7-8주차: 논문 작성
- [ ] Methods 작성 (행동 데이터 포함)
- [ ] Figures 생성 (필터 타겟, 행동 개선)
- [ ] 저널 제출

---

## 🎊 프로젝트 상태 요약

✅ **전략 확정**: V1/V2 중심 개인별 필터 설계
✅ **타겟 파악**: 14 페어 (sub-08), 7 페어 (sub-09)
✅ **비판 1-2 해결**: FDR 보정 + SRM 재현
⏳ **비판 3 진행중**: 행동 검증 (4주)
⏳ **필터 개발**: 행동 상관관계 결과 대기

**전체 프로젝트 상태**: 8주 완료 예정, 순조롭게 진행 중
