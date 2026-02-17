# Decoder Model Comparison - Results

**Date**: 2026-02-17
**Data**: `full_dataset_C010` (P3 pipeline, C010 confounds)
**CV**: Leave-One-Run-Out (LORO), nested hyperparameter tuning

---

## Models Tested (6)

### Linear Models

**1. LDA (Linear Discriminant Analysis)**
- 8개 색상 클래스 간 분산을 최대화하는 선형 경계를 찾음
- 입력: voxel 패턴 → 출력: 색상 라벨 (0-7)
- 장점: fMRI처럼 sample 적고 feature 많은 데이터에 shrinkage로 안정적
- 현재 baseline 모델

**2. Ridge Regression**
- sin/cos로 인코딩한 연속 hue 각도를 예측하는 선형 회귀
- 입력: voxel 패턴 → 출력: (sin θ, cos θ) → 역변환으로 hue 각도 복원
- L2 정규화(alpha)로 과적합 방지
- LDA와 달리 색상 간 원형(circular) 관계를 반영

**3. Forward Encoding (6-channel)**
- Brouwer & Heeger 2009의 방법. 뇌가 6개 color channel로 색을 표상한다고 가정
- 학습: 각 voxel이 6개 channel에 어떻게 반응하는지 가중치(W) 추정
- 예측: test 패턴에서 channel 반응을 복원 → 8개 색상 template과 비교
- 신경과학적으로 가장 해석 가능한 모델 (채널 튜닝 자체를 추정)

### Non-linear Models

**4. Kernel Ridge Regression**
- Ridge와 같지만 RBF 커널로 비선형 매핑을 학습
- voxel 공간에서 직선으로 안 되는 패턴도 포착 가능
- gamma 파라미터가 비선형성의 강도를 조절

**5. SVM (Support Vector Machine)**
- RBF 커널로 8개 색상 간 비선형 결정 경계를 학습
- margin 최대화 → 소수 sample에서도 일반화 능력이 좋음
- C(정규화 강도)와 gamma(커널 폭) 두 파라미터

**6. MLP (Multi-Layer Perceptron)**
- 소규모 신경망 (64→32 뉴런, ReLU)
- 가장 유연한 비선형 모델
- 단점: **sample 수가 적을 때 극도로 과적합에 취약** → early stopping + 강한 L2 필수

---

## Phase 1: Local Test (sub-01, V1)

| Model | Type | Raw (45° acc) | Procrustes (45° acc) | Δ | Raw MAE | Procrustes MAE |
|---|---|---|---|---|---|---|
| **LDA** | Linear | 0.479 | **0.917** | +0.438 | 87.19° | **16.88°** |
| **ForwardEnc** | Linear | 0.333 | **0.792** | +0.459 | 92.81° | **40.31°** |
| **Ridge** | Linear | 0.354 | **0.729** | +0.375 | 90.00° | **47.81°** |
| **KernelRidge** | Non-lin | 0.396 | **0.708** | +0.312 | 89.06° | **46.88°** |
| **SVM** | Non-lin | 0.458 | **0.688** | +0.230 | 91.88° | **48.75°** |
| **MLP** | Non-lin | 0.375 | 0.438 | +0.063 | 88.12° | **80.62°** |

**Chance levels**: 45° accuracy = 37.5% (3/8), MAE = 90°

---

## Phase 2: Full Server Results (10 subjects × 4 ROIs)

**Server**: node2, SLURM array job (10 tasks, 4GB/task, ~4min/subject)
**Results**: `model_comparison_server/consolidated/`

### Overall Performance

| Model | Type | Raw (45° acc) | Procrustes (45° acc) | Δ | Proc MAE |
|---|---|---|---|---|---|
| **LDA** | Linear | 0.393 ± 0.157 | **0.821 ± 0.172** | +0.428 | **25.6°** |
| **Ridge** | Linear | 0.375 ± 0.157 | **0.783 ± 0.165** | +0.408 | 41.8° |
| **SVM** | Non-lin | 0.382 ± 0.165 | **0.776 ± 0.164** | +0.393 | 32.9° |
| **KernelRidge** | Non-lin | 0.380 ± 0.148 | **0.739 ± 0.184** | +0.359 | 47.9° |
| **ForwardEnc** | Linear | 0.367 ± 0.154 | **0.736 ± 0.166** | +0.369 | 43.5° |
| **MLP** | Non-lin | 0.370 ± 0.081 | 0.394 ± 0.088 | +0.024 | 87.1° |

### HC vs CVD Breakdown (Procrustes, 45° accuracy)

| Model | HC (n=7) | CVD (n=3) | Δ(HC−CVD) |
|---|---|---|---|
| **LDA** | 0.805 | 0.859 | −0.054 |
| **SVM** | 0.749 | 0.837 | −0.088 |
| **Ridge** | 0.775 | 0.802 | −0.027 |
| **KernelRidge** | 0.746 | 0.720 | +0.026 |
| **ForwardEnc** | 0.749 | 0.707 | +0.043 |
| **MLP** | 0.396 | 0.391 | +0.005 |

**Key observation**: CVD ≈ HC (차이 없거나 CVD가 오히려 약간 높음) → voxel-color mapping은 group 간 공통

---

## Interpretation

### 1. "정렬이 선형 모델을 살린다" — 10명 전체에서 확인

- Raw: 모든 모델 chance 근처 (37-39%)
- Procrustes 후: LDA **82.1%**, Ridge 78.3% — 선형 모델이 가장 큰 개선
- Δ(LDA) = +42.8%p vs Δ(SVM) = +39.3%p vs Δ(MLP) = +2.4%p
- **정렬이 없으면 모든 모델이 실패하고, 정렬 후에는 선형이 최고**

### 2. "비선형이 정렬을 대체하지 못한다"

- Raw 조건에서 비선형 ≈ 선형 (모두 chance 근처)
- Procrustes 후에도 비선형(SVM 77.6%) < 선형(LDA 82.1%)
- 비선형성은 run 간 정합 문제를 해결하는 수단이 아님
- **문제의 본질: "비선형 매핑" ≠ "run 간 정합(alignment)"**

### 3. MLP 완전 실패 — 구조적 과적합

- Procrustes 후에도 39.4% (chance 37.5%와 거의 동일)
- 원인: sample/feature 비율 = 40/n_voxels ≈ 0.07 (극단적으로 낮음)
- early stopping + L2 정규화로도 불충분
- **해결 방향**: 차원 축소 (PCA, SRM, CCA) 후 재실험 → TODO 참조

### 4. HC ≈ CVD — cross-group mapping 동일

- LDA: CVD가 오히려 +5.4%p 높음
- SVM: CVD가 +8.8%p 높음
- 전체적으로 HC-CVD 차이 미미 → **filter learning 접근이 정당**
- 통계적 유의성은 validation test (permutation, bootstrap)로 확인 예정

### 5. ForwardEncoding의 위치

- Procrustes 후 73.6% (LDA 82.1%보다 낮지만 chance 대비 충분)
- **이 모델만 채널 가중치(W)로 색 표상 구조를 직접 해석 가능**
- 성능이 낮은 이유: analytical solution이 정규화 없이 과적합 경향

### 6. 연구 질문에 대한 답변

> "정렬이 선형 모델을 살리는가, 아니면 비선형이 필요한가?"

**→ 정렬이 핵심이다.** Procrustes 정렬 후 가장 단순한 LDA가 최고 성능(82.1%). 비선형 모델은 정렬 없이도, 있어도 선형 모델을 능가하지 못함. 이는 voxel-color 매핑이 본질적으로 **선형이지만 run 간 정합이 필요하다**는 것을 시사.

---

## Bugs Fixed Before Testing

1. **ForwardEncodingDecoder.fit** (line 339): `create_basis_functions(HUE_ANGLES, n_channels=...)` → TypeError (double assignment). Fixed: `create_basis_functions(n_channels=...)` then index by `HUE_ANGLES`.
2. **ForwardEncodingDecoder.predict** (line 370-372): `basis_functions` was (360,6), argmax returned degree index (0-359) not label (0-7). Fixed: basis is now (8,6), argmax returns color index.
3. **loro_cv_generic HP tuning** (line 497-498): For hue-based models, score compared `y_tune_test` with itself instead of predictions. Fixed: compare `hue_to_labels(y_tune_test)` with `hue_to_labels(y_tune_pred)`.
4. **Import conflict**: Local `utils.py` shadowed `analysis/utils/` package. Fixed: use `importlib.util` for explicit path import.

---

## Resource Profiling

| Config | Peak Memory | Wall Time | CPU |
|---|---|---|---|
| 2 models, 1 ROI | 218 MB | 48s | 196% |
| 6 models, 1 ROI | 222 MB | 58s | 192% |
| **sbatch setting** | **4 GB** | **30 min limit** | **4 CPUs** |

---

## Validation Tests

### Phase 3a: Local (bootstrap CI, reliability)
- **Status**: _[pending]_
- **Results**: _[write here after completion]_

### Phase 3b: Server (permutation test, cross-subject generalization)
- **Status**: _[pending]_
- **Results**: _[write here after completion]_

---

## TODO: Dimensionality Reduction + Re-experiment

### Problem
MLP (및 잠재적으로 다른 비선형 모델)이 과적합으로 실패.
Sample/feature 비율이 40/500+ ≈ 0.07로 극단적.

### Proposed Solutions

**1. PCA (Principal Component Analysis)**
- Voxel space를 top-k PC로 축소 (e.g., k=20, 50)
- 가장 단순하고 빠름
- 단점: unsupervised → 색 정보와 무관한 분산도 유지

**2. SRM (Shared Response Model)**
- 다수 subject의 공통 표상 공간을 학습 (k=20~50 features)
- Subject 간 정합 + 차원 축소를 동시 수행
- Procrustes보다 강력한 정합 가능
- 장점: cross-subject generalization에 최적화

**3. CCA (Canonical Correlation Analysis)**
- Voxel patterns과 color labels 간 상관을 최대화하는 축소
- Supervised → 색 디코딩에 직접 관련된 차원만 유지
- 단점: 과적합 위험 (supervised 축소 자체가 data leakage 가능)

### Re-experiment Plan
1. Procrustes 정렬 데이터에 PCA/SRM/CCA 적용
2. 축소된 공간(k=10, 20, 50)에서 6개 모델 재비교
3. MLP가 축소된 공간에서 개선되는지 확인
4. 최적 축소 방법 + 최적 모델 조합 선정

### Expected Outcome
- PCA/SRM으로 k=20~50 축소 후 MLP도 작동할 것으로 예상
- 그래도 LDA보다 나을지는 미지수 → "비선형 불필요" 결론 강화 가능
