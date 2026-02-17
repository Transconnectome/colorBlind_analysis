# Decoder Model Comparison - Local Test Results

**Date**: 2026-02-17
**Subject**: sub-01 | **ROI**: V1 | **Voxels**: 568
**Data**: `full_dataset_C010` (P3 pipeline, C010 confounds)

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

## Results: sub-01, V1

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

## Interpretation

### 1. "정렬이 선형 모델을 살린다" — 확인됨

- Raw에서 LDA와 SVM은 비슷했지만 (47.9% vs 45.8%)
- Procrustes 후 LDA가 **91.7%**로 SVM(68.8%)을 크게 앞섬
- Procrustes가 run 간 비선형 잡음을 제거하면, 단순 선형 모델로 충분

### 2. "비선형이 정렬을 대체하지 못한다"

- Raw 조건에서 비선형 모델(SVM 45.8%)이 선형(LDA 47.9%)보다 낫지 않음
- 비선형성은 run 간 정렬 문제를 해결하는 수단이 아님
- 문제의 본질은 "비선형 매핑"이 아니라 "run 간 정합(alignment)"

### 3. MLP는 과적합

- 학습 데이터: run당 8개 sample × 5 train runs = 40개, 568 voxels
- sample/feature 비율이 40/568 ≈ 0.07로 극단적 → 어떤 정규화로도 한계
- Procrustes 후에도 43.8%로 chance 근처 → 이 데이터 규모에 부적합

### 4. ForwardEncoding의 의미

- Procrustes 후 79.2%로 준수한 성능
- 이 모델은 신경과학적 해석이 가능 (6-channel 색상 튜닝)
- 성능은 LDA보다 낮지만, 채널 가중치(W)가 색 표상의 구조를 직접 보여줌

### 5. 연구 질문에 대한 잠정 답변

> "정렬이 선형 모델을 살리는가, 아니면 비선형이 필요한가?"

**→ 정렬이 핵심이다.** Procrustes 정렬 후 가장 단순한 LDA가 최고 성능. 비선형 모델은 정렬 없이도, 있어도 선형 모델을 능가하지 못함. 이는 voxel-color 매핑이 본질적으로 **선형이지만 run 간 정합이 필요하다**는 것을 시사.

---

## Bugs Fixed Before Testing

1. **ForwardEncodingDecoder.fit** (line 339): `create_basis_functions(HUE_ANGLES, n_channels=...)` → TypeError (double assignment). Fixed: `create_basis_functions(n_channels=...)` then index by `HUE_ANGLES`.
2. **ForwardEncodingDecoder.predict** (line 370-372): `basis_functions` was (360,6), argmax returned degree index (0-359) not label (0-7). Fixed: basis is now (8,6), argmax returns color index.
3. **loro_cv_generic HP tuning** (line 497-498): For hue-based models, score compared `y_tune_test` with itself instead of predictions. Fixed: compare `hue_to_labels(y_tune_test)` with `hue_to_labels(y_tune_pred)`.
4. **Import conflict**: Local `utils.py` shadowed `analysis/utils/` package. Fixed: use `importlib.util` for explicit path import.

---

## Caveats

- **N=1 subject, 1 ROI only** — 10명 × 4 ROI 전체 결과에서 확인 필요
- MLP의 과적합은 데이터 규모의 구조적 한계 → 전체 결과에서도 동일할 가능성 높음
- Forward Encoding의 상대적 저성능이 모든 ROI에서 일관적인지 확인 필요

---

## Next Step

- Server deployment: 10 subjects × 4 ROIs × 6 models (SLURM array job)
- Then: validation tests (permutation, bootstrap CI, reliability, cross-subject generalization)
- Then: comprehensive visualization
