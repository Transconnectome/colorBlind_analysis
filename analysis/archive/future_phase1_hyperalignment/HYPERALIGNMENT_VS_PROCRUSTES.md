# Hyperalignment vs Procrustes: Deep Learning 관점 비교

## 핵심 결론

**딥러닝 필터 학습에는 Hyperalignment가 압도적으로 유리합니다.**

---

## 1. 좌표계 통일 문제

### Procrustes의 문제점

```python
# HC 4명 × CVD 3명 = 12개의 pairwise alignment
for hc in ['sub-02', 'sub-03', 'sub-05', 'sub-06']:
    for cvd in ['sub-08', 'sub-09', 'sub-10']:
        R_cvd_to_hc = procrustes(CVD, HC)
        CVD_aligned = CVD @ R_cvd_to_hc

        # 문제: 각 alignment마다 CVD_aligned가 다른 좌표계에 있음!
        # sub-08 aligned to sub-02 좌표계
        # sub-08 aligned to sub-03 좌표계  <- 서로 다른 공간!
        # ...
```

**문제:**
- 12개의 서로 다른 좌표계
- 데이터를 합칠 수 없음 (coordinates incompatible)
- 각 쌍마다 별도 모델 필요

### Hyperalignment의 해결

```python
# 1단계: 모든 HC를 common space로
HC_common = hyperalignment([HC_02, HC_03, HC_05, HC_06])
# → 모두 SAME coordinate system

# 2단계: CVD를 common space로 projection
CVD_08_common = project(CVD_08, HC_common)
CVD_09_common = project(CVD_09, HC_common)
CVD_10_common = project(CVD_10, HC_common)
# → 모두 SAME coordinate system

# 3단계: 이제 모든 데이터를 함께 사용 가능!
all_hc_patterns = [HC_02_common, HC_03_common, HC_05_common, HC_06_common]
all_cvd_patterns = [CVD_08_common, CVD_09_common, CVD_10_common]

# 단일 모델 학습
Filter: HC_common → CVD_common
```

**장점:**
- 1개의 통일된 좌표계
- 모든 데이터 pooling 가능
- 단일 모델로 모든 CVD 학습

---

## 2. 손실함수 정의

### Procrustes 방식

```python
# 문제: 어떤 HC를 reference로 써야 하나?

# Option A: HC별로 따로 학습
for hc_ref in HC_subjects:
    Filter_hc = NeuralNet()
    Loss = 0
    for cvd in CVD_subjects:
        CVD_aligned = align(CVD, hc_ref)  # hc_ref 좌표계
        Loss += ||Filter_hc(hc_ref) - CVD_aligned||^2

    # 문제: HC 개수만큼 모델이 필요 (4개!)
    # 새로운 HC에 적용 불가능

# Option B: 모든 HC 평균? (잘못된 접근)
HC_mean = mean([HC_02, HC_03, HC_05, HC_06])  # Wrong!
# 문제: 서로 다른 좌표계의 평균은 의미 없음
```

**근본적 문제:**
- Reference 선택 ambiguity
- 좌표계 불일치
- 일반화 불가능

### Hyperalignment 방식

```python
# 간단하고 명확!

# 모든 데이터가 common space에 있으므로
HC_patterns = load_all_hc_in_common_space()    # (5 subjects × 48 obs, 279 voxels)
CVD_patterns = load_all_cvd_in_common_space()  # (3 subjects × 48 obs, 279 voxels)

# 손실함수: 단순 명료
Filter = NeuralNet()
Loss = ||Filter(HC_patterns) - CVD_patterns||^2

# 추가 제약 (선택적)
+ λ₁ * RDM_loss(Filter(HC), HC)      # Structure preservation
+ λ₂ * ||Filter(HC) - HC||^2         # Smoothness
```

**장점:**
- 손실함수 명확
- Reference ambiguity 없음
- 모든 데이터 활용

---

## 3. 데이터 활용 효율

### 샘플 수 비교

**Procrustes (pairwise):**
```
각 (HC, CVD) 쌍당 샘플:
- 1 HC × 1 CVD = 48 observations (6 runs × 8 colors)

총 학습 가능 쌍:
- 4 HC × 3 CVD = 12 pairs
- But 각 pair는 다른 좌표계 → 통합 불가

실질적 샘플 수: 48 per model (12개 모델)
```

**Hyperalignment (common space):**
```
Common space의 모든 샘플 통합:
- 5 HC × 48 obs = 240 HC patterns
- 3 CVD × 48 obs = 144 CVD patterns

총 384 samples in SAME coordinate system!

실질적 샘플 수: 144 training pairs
(모든 HC를 reference로 사용 가능)
```

**효율 차이:**
- Procrustes: 48 samples per model × 12 models (분리됨)
- Hyperalignment: **384 samples × 1 unified model**

**샘플 수 8배 차이!**

---

## 4. 모델 구조

### Procrustes 접근

```python
# 방법 1: HC별 개별 모델 (비효율)
models = {}
for hc_id in HC_subjects:
    model = NeuralNet(279 → 512 → 256 → 512 → 279)
    # Train only on CVD aligned to this HC
    models[hc_id] = train(model, data_aligned_to_hc_id)

# 추론 시
def predict(new_hc, hc_id):
    return models[hc_id](new_hc)  # 어떤 model 쓸지 명시 필요

# 문제:
# - 4개 모델 필요
# - 새 HC 적용 불가
# - 모델 간 불일치 가능
```

```python
# 방법 2: 좌표계 변환 포함 (복잡)
class ProcrustesFilter(nn.Module):
    def __init__(self):
        self.transform_hc_to_common = nn.Linear(279, 279)  # Learnable?
        self.filter = NeuralNet(279 → ... → 279)
        self.transform_common_to_cvd = nn.Linear(279, 279)

    def forward(self, hc):
        x = self.transform_hc_to_common(hc)  # 학습된 좌표 변환?
        x = self.filter(x)
        x = self.transform_common_to_cvd(x)
        return x

# 문제:
# - 좌표 변환을 학습해야 함 (ill-defined)
# - Procrustes의 기하학적 보장 상실
# - 불안정한 학습
```

### Hyperalignment 접근

```python
# 단순 명료!
class ColorFilter(nn.Module):
    def __init__(self):
        self.filter = NeuralNet(279 → 512 → 256 → 512 → 279)

    def forward(self, hc_in_common_space):
        cvd_in_common_space = self.filter(hc_in_common_space)
        return cvd_in_common_space

# 추론 시
def predict(new_hc_pattern):
    # 1. Project new HC to common space
    hc_common = hyperalignment.project(new_hc_pattern)

    # 2. Apply filter
    cvd_common = filter(hc_common)

    # 3. Done! (same space)
    return cvd_common

# 장점:
# - 단일 모델
# - 좌표 변환 = 기하학적 Procrustes (well-defined)
# - 새 HC 쉽게 추가
```

---

## 5. 일반화 성능

### 새로운 HC 추가 시

**Procrustes:**
```python
# 새 HC (sub-01) 추가
new_hc = load('sub-01')

# 문제: 기존 모델들이 쓸모없음!
# → sub-01 좌표계에서 CVD로의 새 모델 필요
model_sub01 = train_from_scratch(new_hc, all_cvd)

# 기존 모델 재활용 불가
```

**Hyperalignment:**
```python
# 새 HC (sub-01) 추가
new_hc = load('sub-01')

# 1. Common space에 project
new_hc_common = hyperalignment.project(new_hc)

# 2. 기존 필터 바로 적용!
cvd_prediction = filter(new_hc_common)

# 추가 학습 불필요
# 기존 모델 그대로 사용
```

### 새로운 CVD 추가 시

**Procrustes:**
```python
# 새 CVD (sub-11) 추가
new_cvd = load('sub-11')

# 모든 HC에 대해 alignment 필요
for hc in HC_subjects:
    R = procrustes(new_cvd, hc)
    new_cvd_aligned = new_cvd @ R

    # 각 HC별 모델로 평가
    prediction = models[hc](hc)
    error = ||prediction - new_cvd_aligned||

# 문제: N_hc번의 alignment + evaluation
```

**Hyperalignment:**
```python
# 새 CVD (sub-11) 추가
new_cvd = load('sub-11')

# 1. Common space에 project (1회)
new_cvd_common = hyperalignment.project(new_cvd)

# 2. 모든 HC 패턴으로 평가
for hc_pattern in HC_common_space:
    prediction = filter(hc_pattern)
    error = ||prediction - new_cvd_common||

# 장점: 1회 projection으로 모든 HC 사용
```

---

## 6. 해석 가능성

### Procrustes

```
"sub-08의 color representation은 sub-02에 비해 X만큼 다름"
"sub-08의 color representation은 sub-03에 비해 Y만큼 다름"

문제: X와 Y가 다른 좌표계 → 비교 불가
```

### Hyperalignment

```
"CVD의 color representation은 정상(HC common space) 기준으로
 canonical space에서 Δ만큼 왜곡됨"

장점:
- 모든 비교가 같은 기준점 (common space)
- "정상적 색 표상"이라는 명확한 reference
- Distortion이 absolute sense로 정의됨
```

---

## 7. 계산 복잡도

### Procrustes

```
Training:
- 12 models × (N_params × N_samples × N_epochs)
- N_params ≈ 500K per model
- N_samples = 48 per model
- Total: 12 × 500K × 48 × 200 epochs

Inference (새 HC):
- 불가능 (새 모델 학습 필요)

Inference (기존 HC):
- 어떤 model 쓸지 선택 필요
```

### Hyperalignment

```
Training:
- 1 model × (N_params × N_samples × N_epochs)
- N_params ≈ 500K
- N_samples = 384 (all data pooled)
- Total: 1 × 500K × 384 × 200 epochs

Inference (새 HC):
- Project to common space (one Procrustes, O(p³))
- Apply filter (forward pass, O(N_params))
- Total: ~10ms

Inference (기존 HC):
- Forward pass only (~1ms)
```

**학습 시간:**
- Procrustes: 12× longer (serial) or 12× more GPU memory (parallel)
- Hyperalignment: 1× (더 많은 데이터로 더 robust)

---

## 8. 실험 설계

### Leave-One-Out Cross-Validation

**Procrustes (어려움):**
```python
# CVD sub-08을 test로
for hc_ref in HC_subjects:
    # Train on sub-09, sub-10 aligned to hc_ref
    model = train(data_aligned_to_hc_ref, cvds=['sub-09', 'sub-10'])

    # Test on sub-08 aligned to hc_ref
    sub08_aligned = align(sub08, hc_ref)
    error = evaluate(model, hc_ref, sub08_aligned)

# 문제: 4개 모델 각각 다른 결과 → 어떻게 aggregate?
```

**Hyperalignment (자연스러움):**
```python
# CVD sub-08을 test로
# 1. Common space는 HC only로 구축 (CVD 무관)
HC_common = hyperalignment(HC_subjects)

# 2. Train on sub-09, sub-10
train_data = [sub09_common, sub10_common]
filter = train(train_data)

# 3. Test on sub-08
sub08_common = project(sub08, HC_common)
error = evaluate(filter, HC_common, sub08_common)

# 명확하고 일관된 평가
```

---

## 9. 논문 서술

### Procrustes

```
"We trained separate color transformation models for each HC reference.
For each HC-CVD pair, we aligned the CVD subject to the HC's coordinate
system using Procrustes rotation, then trained a neural network to
predict the aligned CVD patterns from the HC patterns. This resulted
in 12 separate models (4 HC × 3 CVD), each operating in a different
coordinate system."

리뷰어: "Why separate models? How do they relate? Can you generalize?"
❌ 답변 어려움
```

### Hyperalignment

```
"We constructed a shared representational space from all HC subjects
using hyperalignment, then projected CVD subjects as out-of-sample
alignment. All subjects' data were thus represented in a common
coordinate system, enabling us to train a single unified neural network
filter that transforms HC color patterns to CVD patterns. This approach
allows for straightforward generalization to new subjects via projection."

리뷰어: "Elegant! How does it generalize?"
✅ Clear answer: project new subject → apply filter
```

---

## 10. 실전 권장사항

### 언제 Procrustes?

```
✅ 사용 권장:
- Pairwise 통계 검정 (HC vs CVD disparity)
- 개별 subject 비교
- 탐색적 분석
- 간단한 지표 (disparity, color-wise RMS)

❌ 사용 비추:
- 딥러닝 모델 학습
- 다중 subject 통합
- Predictive modeling
- 새 subject에 일반화
```

### 언제 Hyperalignment?

```
✅ 사용 권장:
- 딥러닝 필터 학습
- 그룹 수준 분석
- Common representational structure 연구
- 새 subject 예측
- CVD simulation tool 개발

⚠️ 주의사항:
- 충분한 HC subject 필요 (≥4)
- T/p ratio 확인 (T=48, p=279 → OK)
- Regularization 필요 (ridge in Procrustes step)
```

---

## 11. 최종 결론

| 측면 | Procrustes | Hyperalignment |
|------|-----------|----------------|
| **통계 검정** | ✅ 우수 | ✅ 우수 |
| **개별 비교** | ✅ 우수 | ✅ 우수 |
| **딥러닝** | ❌ 부적합 | ✅✅ 최적 |
| **데이터 효율** | ❌ 낮음 (48/model) | ✅ 높음 (384 total) |
| **일반화** | ❌ 어려움 | ✅ 자연스러움 |
| **해석** | ⚠️ 복잡 (multiple refs) | ✅ 명확 (canonical space) |
| **구현 복잡도** | ✅ 간단 | ⚠️ 중간 |
| **계산 비용** | ⚠️ N×models | ✅ 1 model |

---

## 추천 워크플로우

```python
# Step 1: Exploratory analysis with Procrustes
for hc in HC_subjects:
    for cvd in CVD_subjects:
        disparity, color_errors = procrustes_analysis(hc, cvd)
        # → 개별 subject 특성 파악

# Step 2: Group analysis and deep learning with Hyperalignment
HC_common = hyperalignment(HC_subjects)
CVD_projected = [project(cvd, HC_common) for cvd in CVD_subjects]

# Step 3: Train unified filter
filter = train_deep_filter(HC_common, CVD_projected)

# Step 4: Validation and application
new_cvd = load_new_subject()
new_cvd_common = project(new_cvd, HC_common)
prediction = filter(HC_common)
evaluate(prediction, new_cvd_common)
```

**결론: 두 방법 모두 가치 있지만, 딥러닝 필터 학습에는 Hyperalignment가 필수!**
