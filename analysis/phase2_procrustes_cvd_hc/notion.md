# Phase 2: Procrustes 분석 — CVD-HC 비교
> CVD 3인이 서로 다른 3차원 왜곡 프로파일을 보임(개인 간 이질성 확인) → **개인화된 필터 설계 필수**. Procrustes 정렬 후 공통 디코더 공유 가능 (36-42° vs chance 84-96°)

## 목표
- **RQ2**: CVD가 개인 간 이질성을 보이는가? 개인화된 접근이 필요한가?
- **SRQ1**: 정렬 후 HC-CVD 간 공통 디코더를 공유할 수 있는가?
- Procrustes analysis로 CVD-HC 차이를 **3차원**으로 정량화

---

## 결과 (RQ2): 개인별 이질성

### 3차원 특성화

| 피험자 | CVD Type | Magnitude (L2 ratio) | Sign/Baseline | Structure (RDM diff) | Total T |
|--------|----------|---------------------|---------------|---------------------|---------|
| **Sub-08** | Deutan | 0.66 (-34%) | -0.41 | 0.505 | 0.178 (V2) |
| **Sub-09** | Protan | 1.21 (+21%) | +0.32 | 0.118 | 0.115 (V1) |
| **Sub-10** | Deutan | 0.89 (-11%) | -0.05 | 0.310 | 0.117 (V2) |

> 💡 **핵심 발견**: CVD 3인은 **서로 다른 3차원 왜곡 프로파일**을 보임(이질성). 예: sub-08과 sub-09는 모든 축에서 상이:
> - Sub-08 (deutan): 낮은 magnitude, 음성 baseline, 높은 구조적 왜곡
> - Sub-09 (protan): 높은 magnitude, 양성 baseline, 낮은 구조적 왜곡
>
> → 범용 CVD 필터는 피험자별 왜곡 프로파일이 발산하므로 실패. **개인화 필수**

### 통계 검정 (Permutation test, 1,000 iterations)
- 모든 CVD 피험자가 HC와 유의하게 다름 (p < 0.001)

| 피험자-ROI | Procrustes disparity T | p-value |
|------------|----------------------|---------|
| Sub-08 V1 | 0.132 | < 0.001 |
| Sub-08 V2 | 0.178 | < 0.001 |
| Sub-09 V1 | 0.115 | < 0.001 |
| Sub-09 V2 | 0.113 | < 0.001 |
| Sub-10 V1 | 0.101 | < 0.001 |
| Sub-10 V2 | 0.117 | < 0.001 |

---

## 결과 (SRQ1): 공통 디코더 공유

| 조건 | V1 Error | V2 Error | 해석 |
|------|----------|----------|------|
| HC common W (baseline) | 32° | 35° | HC 성능 |
| CVD + Procrustes + HC W | 36-42° | 38-45° | ✅ HC에 근접 |
| CVD without alignment | 84-96° | 88-94° | ❌ Chance 수준 |

> ✅ **선형 변환 (Procrustes)이 디코더 공유에 충분** → Phase 3의 선형 필터 설계 타당성 지지

### Cross-validation 안정성
- Split-half reliability: r > 0.85 (odd vs even runs)
- Leave-one-run-out 검증: 전 ROI에서 안정적

---

## 방법

### Procrustes Analysis (직교 변환 분석)
1. 패턴 중심화 (centering)
2. SVD로 최적 회전 행렬 R 계산: `U, Σ, Vt = SVD(Y_centered.T @ H_centered)`
3. 스케일링 s, 변환 적용: `Y_aligned = s × Y_centered @ R + mean(H)`
4. Disparity T = √(Σ(Y_aligned - H)² / Σ(H²))

### 3차원 분해 (Three-Dimensional Decomposition)
- **Magnitude** (크기): L2 norm ratio = ‖CVD‖ / ‖HC‖
- **Sign/Baseline** (부호/기준선): mean(CVD) - mean(HC)
- **Structure** (구조): correlation distance between RDM_cvd and RDM_hc

---

## Phase 3를 위한 시사점

개인별 이질성 → **피험자별 loss 가중치 필요**:
- **Sub-08**: 높은 λ_structure (기하학적 왜곡 교정)
- **Sub-09**: 높은 λ_magnitude (진폭 차이 교정)
- **Sub-10**: 균형 λ 가중치

SRQ1 성공 → **선형 변환이 충분**:
- Phase 1 Hyperalignment: Procrustes/GPA로 HC common space 구축
- Phase 3 Filter: 선형 필터 프레임워크 적합

### 🔽 스크립트 목록 (12개)

**Core Analysis**
- `option2b_procrustes_alignment.py` — CVD → HC Procrustes 정렬
- `option2d_procrustes_cvd_comparison.py` — CVD-HC 통계 비교 (permutation test)
- `validate_transformation_t.py` — 정렬 후 디코더 전이 검증
- `verify_option_a_robustness.py` — Procrustes 추정 교차 검증

**Visualization**
- `reconstruction_with_procrustes.py` — 정렬 후 색 재구성 (color wheel)
- `reconstruction_with_procrustes_noalign.py` — 비정렬 baseline (ablation)
- `visualize_circular_disparity.py` — 색상별 disparity (radar plot)
- `visualize_circular_activation.py` — 원형 색 공간 활성화 패턴 (polar plot)
- `visualize_activation_vs_disparity.py` — 활성화 vs. disparity 산점도
- `visualize_topology_perspective.py` — 위상 분석 (persistent homology)
- `create_procrustes_color_points_concept.py` — 논문용 색 공간 왜곡 그림
- `create_procrustes_concept_figure.py` — Procrustes 방법 개념도

### 🔽 References
- Gower, J. C. (1975). Generalized procrustes analysis. *Psychometrika*, 40(1), 33-51.
- Haxby, J. V., et al. (2011). A common, high-dimensional model of the representational space in human ventral temporal cortex. *Neuron*, 72(2), 404-416.
