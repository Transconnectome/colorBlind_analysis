# Sub-08 Pre-Image 벡터 Cosine −0.18 재계산 및 추적

## 1. 비교 대상 두 벡터 확인

**조정 사항**: notion.md §5-6의 cosine = −0.18은 **두 Pre-Image 벡터 간 비교**로 올바르게 해석됨.

- **비교 1 (§5-5 Correction)**: Sub-08 hV4 LOCO fitting의 per-color δθ (phase_a)
  - R+C (Δλ=3.0, g=1.0): `[-11.40, -9.86, -4.75, 1.36, 10.70, -38.44, -18.78, -1.12]`°
  - 2-Component (β_s=38°, β_c=−14°): `[-12.09, -20.21, -25.67, -29.37, -32.14, -10.29, 29.39, 18.52]`°
  - **Spearman ρ = −0.714** ✓ (notion.md 일치)

- **비교 2 (§5-6 Pre-Image)**: 역함수로 구한 자극 공간 보정량 δθ_filter
  - R+C pre-image δθ (δθ_in − θ_original): `[-18.15, -37.18, -34.85, 18.60, 42.93, 3.87, -31.62, -1.03]`°
  - 2-Component pre-image δθ (δθ_in − θ_original): `[-19.18, -45.92, -67.95, -87.77, -104.19, -26.15, 16.99, 2.36]`°
  - **Cosine = −0.182** ≈ −0.18 ✓ (notion.md 일치)

## 2. 계산 공식: 단순 Euclidean Cosine

```
cosine(a, b) = (a · b) / (|a| × |b|)
```

**계산 과정** (Pre-Image):
- δθ_rc · δθ_2comp = −2322.53
- |δθ_rc| = 78.30
- |δθ_2comp| = 163.19
- cosine = −2322.53 / (78.30 × 163.19) = **−0.18178**

**공식 확인**: 단순 Euclidean cosine (각도 wrapping 없음). 왜냐하면 δθ는 보정량으로 이미 스칼라 각도 차이이므로 원 공간의 wrap 보정 불필요.

## 3. JSON 저장 위치 및 필드명

| 데이터 | 경로 | 필드 |
|--------|------|------|
| R+C 사전-이미지 | `results/loco_filter/preimage/sub-08_V4_rc_opponent_preimage.json` | `delta_preimage` (list of 8 floats) |
| 2-Comp 사전-이미지 | `results/loco_filter/preimage_2component/sub-08_V4_2component_preimage.json` | `delta_preimage` (list of 8 floats) |
| R+C Phase A | `results/loco_filter/phase_a/sub-08_V4_rc_opponent.json` | `best_loss.delta_theta` |
| 2-Comp Phase A | `results/loco_filter/phase_a_2component/sub-08_V4_2component.json` | `best_loss.delta_theta` |

`delta_preimage` = θ_input − θ_cielab (8개 색에 대한 입력 각도 조정량)

## 4. Spearman ρ = −0.714 vs Cosine = −0.18의 차이

| 지표 | Spearman ρ (§5-5) | Cosine (§5-6) |
|------|:---:|:---:|
| **데이터** | Phase A fitting δθ | Pre-image filter δθ |
| **의미** | hV4에서 인식되는 왜곡 방향 | 자극을 교정하는 필터의 방향 |
| **계산** | **Rank 기반** (1-2P(σ)/N) | **Continuous 벡터 내적** |
| **크기 영향** | 부호만 고려 (±1, ±0.5) | 벡터 크기 큼 (범위 −180°~+180°) |
| **값** | −0.714 (p=0.047, 유의) | −0.182 (p=0.320, 비유의) |

**핵심 차이**:
1. **Rank vs Magnitude**: Spearman은 두 벡터가 취약성 순위에서만 완전 반대이면 ρ=−1. Cosine은 벡터 크기와 방향 모두 포함 → 크기 차이 때문에 더 약한 상관.
2. **데이터셋**: Phase A는 fitting 동안 모델이 최적화한 δθ (크기 범위 −38°~+29°). Pre-image는 수치적으로 구한 필터 (크기 범위 −104°~+42°) → 2-Component 벡터가 훨씬 큼.
3. **p값 차이**: Phase A Spearman p=0.047 (유의), Pre-image cosine p=0.320 (비유의) → 크기 비균형이 상관을 약화.

## 5. 직접 재계산 검증

**Python 계산 결과**:
```python
import numpy as np
from scipy.stats import spearmanr

# Phase A (§5-5)
delta_rc_phase_a = np.array([-11.40, -9.86, -4.75, 1.36, 10.70, -38.44, -18.78, -1.12])
delta_2comp_phase_a = np.array([-12.09, -20.21, -25.67, -29.37, -32.14, -10.29, 29.39, 18.52])
spearman_rho, _ = spearmanr(delta_rc_phase_a, delta_2comp_phase_a)
# Result: ρ = −0.714286 ✓

# Pre-image (§5-6)
delta_rc_pre = np.array([-18.15, -37.18, -34.85, 18.60, 42.93, 3.87, -31.62, -1.03])
delta_2comp_pre = np.array([-19.18, -45.92, -67.95, -87.77, -104.19, -26.15, 16.99, 2.36])
cosine = np.dot(delta_rc_pre, delta_2comp_pre) / (np.linalg.norm(delta_rc_pre) * np.linalg.norm(delta_2comp_pre))
# Result: cosine = −0.18178 ≈ −0.18 ✓
```

**확인**: notion.md §5-6 표의 "벡터 cosine: −0.18 (반상관)"은 정확한 계산값.

## 결론

- **데이터 구조**: 두 섹션이 **서로 다른 δθ 벡터**를 비교 (Phase A fitting vs Pre-image filter)
- **계산 공식**: 단순 Euclidean cosine, 각도 wrap 불필요
- **일치 확인**: 양쪽 수치 모두 JSON에서 직접 추출하여 재계산 검증 완료
- **해석**: Spearman (Phase A)과 Cosine (Pre-image)의 부호 불일치(−0.714 vs −0.18)는 **데이터셋 + 계산방식 차이**로 설명 (rank vs magnitude, 크기 범위 차이)
