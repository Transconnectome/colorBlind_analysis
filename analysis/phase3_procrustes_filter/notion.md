# Phase 3: Procrustes 기반 선형 필터 설계
> CVD 뇌 패턴을 HC-like 패턴으로 변환하는 피험자별 선형 필터. 97% 이상의 Procrustes disparity 감소, RDM r > 0.99 달성 (retrospective validation)

## 목표
- Phase 2의 개인별 왜곡 프로파일 기반으로, CVD 패턴 Y를 HC 패턴 H로 매핑하는 **선형 변환 F** 학습
- `F = Y @ A + b` (A: 변환 행렬, b: 편향 벡터)

---

## 방법

### 3차원 Loss Function (3D 손실 함수)

| Loss | 수식 | 역할 |
|------|------|------|
| Magnitude | ‖norm(F) - norm(H)‖² | 색상별 패턴 강도 매칭 |
| Baseline | ‖mean(F) - mean(H)‖² | 평균 voxel 활성화 매칭 |
| Structure | ‖RDM_F - RDM_H‖² | 색상 간 유사성 기하학 매칭 |
| Regularization | ‖A - I‖² + ‖b‖² | 최소 변환 유도 (항등 변환에 가깝게) |

### 개인별 최적화
Phase 2에서 특성화된 왜곡 프로파일에 따라 loss 가중치 조정:

| 피험자 | CVD Type | 주요 왜곡 | 최적 가중치 |
|--------|----------|-----------|-------------|
| Sub-08 | Deutan | 높은 구조적 차이 (0.505) | λ_struct = 1.0 (HIGH) |
| Sub-09 | Deutan | 높은 magnitude ratio (1.21) | λ_mag = 1.0 (HIGH) |
| Sub-10 | Protan | 균형적 왜곡 | λ_mag = λ_base = λ_struct = 0.7 |

### 학습 전략
- PyTorch Adam optimizer (lr = 0.001, 1,000 epochs)
- 초기값: A = 항등 행렬, b = 영벡터
- Cross-validation: 7 runs 학습 → 1 run 검증 (8-fold leave-one-run-out)

---

## 결과

### ✅ 타당성 입증 (Retrospective Validation)

**Procrustes Disparity 감소**

| 피험자 | ROI | 필터 전 | 필터 후 | 감소율 |
|--------|-----|---------|---------|--------|
| Sub-08 | V1 | 0.132 | 0.004 | 97.2% ↓ |
| Sub-08 | V2 | 0.178 | 0.005 | 97.2% ↓ |
| Sub-09 | V1 | 0.115 | 0.005 | 95.8% ↓ |
| Sub-09 | V2 | 0.113 | 0.005 | 95.6% ↓ |
| Sub-10 | V1 | 0.101 | 0.004 | 96.3% ↓ |
| Sub-10 | V2 | 0.117 | 0.004 | 96.6% ↓ |

**RDM Correlation (HC와의 구조적 유사성)**

| 피험자 | 필터 전 | 필터 후 |
|--------|---------|---------|
| Sub-08 | 0.495 | 0.999 |
| Sub-09 | 0.882 | 0.998 |
| Sub-10 | 0.690 | 0.999 |

> ✅ 선형 변환으로 CVD → HC 패턴 정렬 성공 (r > 0.99)
> ✅ 개인별 최적화가 각 왜곡 프로파일에 맞춤형 필터 생성

> ⚠️ **핵심 제한**: Retrospective validation only — 필터가 학습 데이터에서 최적화 및 검증됨

---

## 제한점

| 제한점 | 설명 |
|--------|------|
| Retrospective only | 학습 데이터에서 최적화+검증 → 과적합 위험 |
| 뇌 공간 변환 | voxel 패턴에서 작동 → 실제 자극 색상 필터로 역변환 필요 |
| 행동 검증 없음 | 색 변별 테스트, 주관적 지각 평가 미실시 |

### 향후 검증 필요
1. Stimulus-space color LUT 생성 (역변환)
2. 필터링된 이미지 데이터셋 생성
3. 행동 검증: Farnsworth-Munsell 100 Hue test, 색 명명 정확도
4. fMRI 검증: 필터링된 자극으로 CVD 스캔 → HC-like 반응 확인

> 💡 이 Phase = 필터 타당성의 **proof-of-concept** / Future Phase 1-3 = 자극 공간의 **full pipeline**

### 🔽 스크립트 목록 (14개)

**Core Filter Training**
- `phase2a_train_filter.py` — PyTorch 필터 학습 (3D loss, GPU 가속)
- `phase2a_train_filter_numpy.py` — NumPy 버전 (소규모 데이터용)
- `phase2a_train_single.py` — 단일 피험자 필터 학습
- `phase2a_train_single_baseline81.py` — Baseline81 데이터셋 버전

**Pattern Extraction**
- `phase2a_extract_patterns.py` — CVD/HC 패턴 추출 (amplitudes_z.npy)
- `phase2a_extract_patterns_baseline81.py` — Baseline81 버전

**Validation & Analysis**
- `apply_filter_with_reconstruction.py` — 필터 적용 및 재구성 정확도
- `phase2a_analyze_results.py` — 결과 분석 및 요약 통계
- `phase2a_compute_rdm.py` — RDM 계산 (pre/post filter)
- `phase2a_compute_metrics.py` — 전체 메트릭 (disparity, RDM corr, reconstruction, pattern corr)

**Visualization**
- `visualize_rdm_difference.py` — RDM 비교 히트맵
- `visualize_rdm_improvement_compact.py` — 개선 요약 시각화 (side-by-side)
- `visualize_filter_properties.py` — 필터 속성 (A 행렬 히트맵, b 벡터)
- `verify_w_matrix.py` — W 행렬 일관성 검증

### 🔽 References
- Gower, J. C., & Dijksterhuis, G. B. (2004). *Procrustes Problems*. Oxford University Press.
