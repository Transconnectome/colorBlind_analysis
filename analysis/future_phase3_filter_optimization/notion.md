# Future Phase 3: CVD 색상 필터 최적화 (360° Search)
> 최적화를 통해 CVD 뇌 반응이 HC와 일치하는 display 색상을 탐색하고 개인화 Color LUT 생성

## 상태
- 🎯 **Planned** — Future Phase 1-2 완료 후 시작

## 목표
- 각 원래 색상 θ_orig에 대해 CVD 뇌 반응이 HC와 일치하는 **최적 display 색상** θ_display 탐색
- 결과물: 개인화 Color Lookup Table (LUT, θ_orig → θ_display)

## 핵심 수식

```
θ_display = argmin_θ [
    Loss1: ||Ŷ_cvd(θ) - Ŷ_hc(θ_orig)||²    # Brain pattern matching
  + λ × Loss2: ||Decode(Ŷ_cvd(θ)) - θ_orig||²  # Reconstruction accuracy
]
```

> ✅ **기존 voxel-space filter 대비 장점**
> - 360° 연속 최적화 (Phase 2 인코더 기반)
> - 개인화: 각 CVD 피험자의 실제 반응 패턴 사용
> - Dual constraint: 신경 기하학 + 지각 정확도 동시 충족
> - 이론적 근거: CVD brain → HC brain 정렬

## 성공 기준

| 지표 | 목표 |
|------|------|
| Filter smoothness | < 2.0°/deg |
| Reconstruction error | ≤ 32° (baseline) |
| Inter-CVD consistency | < 10° (같은 CVD type 간) |

## 구현 절차
1. CVD 데이터 수집 (기존: sub-08, 09, 10)
2. HC common space로 CVD projection (Phase 1)
3. θ_orig ∈ [0°, 360°] 범위 최적화
4. Lookup Table (LUT) 생성
5. 검증 (in silico + behavioral + fMRI)

---

## 검증 전략

| 검증 방법 | 내용 | 현재 범위 |
|-----------|------|-----------|
| In silico | 학습 데이터에 필터 적용, brain pattern alignment 확인 | ✅ 포함 |
| Psychophysical | Farnsworth-Munsell 100 Hue test, 색 변별 | ⚠️ 추후 |
| fMRI | CVD에 필터링된 이미지로 스캔, HC-like 반응 확인 | ⚠️ 추후 |

> ⚠️ **현재 범위**: In-silico validation only. 실제 필터링된 자극을 이용한 행동/fMRI 검증은 향후 과제

## Current Phase 3 vs Future Phase 3 비교

| 측면 | Current Phase 3 (Procrustes Filter) | Future Phase 3 (360° Optimization) |
|------|-------------------------------------|-------------------------------------|
| **공간** | Voxel space (뇌) | Color space (자극) |
| **방법** | Direct linear transformation | Optimization-based search |
| **커버리지** | 8개 측정 색상 | 360° 연속 색조 |
| **검증** | Retrospective (학습 데이터) | Prospective (계획) |

> 💡 **Current Phase 3** = 필터 타당성의 proof-of-concept / **Future Phase 3** = 전체 자극-공간 필터 파이프라인

## 예상 산출물
- 개인화 Color LUT (θ_orig → θ_display)
- 응용: 실시간 이미지/영상 필터, 디스플레이 보정, AR 안경

### 🔽 작업 위치 및 관련 문서
- 작업 공간: `prediction_model_workspace/`
- 상세 계획: `prediction_model_workspace/docs/PHASE3_CVD_FILTER_OPTIMIZATION.md`
