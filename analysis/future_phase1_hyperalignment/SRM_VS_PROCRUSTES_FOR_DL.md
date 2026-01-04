# SRM vs Procrustes for Deep Learning: Honest Analysis

## Date: 2025-12-18
## Question: "SRM은 왜 딥러닝에 좋음?"

---

## 1. 제가 주장했던 것

**SRM이 딥러닝에 좋다고 한 이유:**
1. Low-dimensional space (k=30 vs p=279)
2. Better T/p ratio (8/30 = 27% vs 8/279 = 3%)
3. Unified coordinate system
4. Handles T < p naturally

**하지만 정말 그럴까?** 다시 분석해봅시다.

---

## 2. Sample 수 비교: 정확히 세어보기

### Scenario: 딥러닝 필터 학습

**목표:** HC patterns → CVD patterns transformation 학습

#### Procrustes Approach (Run-Averaged)

```python
# 데이터 준비:
HC subjects: 5명 (sub-02, 03, 05, 06, 07)
CVD subjects: 3명 (sub-08, 09, 10)

# Run averaging 후:
Each subject: 8 color patterns (8, 279)

# Training samples:
Option A: Leave-one-CVD-out
  - Train: 2 CVD subjects = 2 × 8 = 16 samples
  - Test: 1 CVD subject = 8 samples

Option B: Use all CVD
  - Train: 3 CVD subjects = 3 × 8 = 24 samples
  - Input dim: 279

Option C: Use HC as augmentation
  - Assume CVD = HC + Distortion
  - Train: 5 HC + 3 CVD = 8 × 8 = 64 samples?
  - But HC → CVD mapping is what we're learning!
```

**실질적 sample 수: 16-24 samples, input dim 279**

#### SRM Approach

```python
# SRM training (HC only):
HC subjects: 5명
Each: 8 color patterns (8, 279)

srm = SRM(features=30)
srm.fit([sub.T for sub in HC_subjects])  # Input: (279, 8) × 5

# Shared space:
Shared response S: (30, 8)
Subject weights W_i: (279, 30) × 5

# CVD projection:
For each CVD:
  W_cvd = srm.transform([cvd_data.T])  # Learn (279, 30)
  cvd_in_shared = W_cvd.T @ cvd_data  # (30, 8)

# Deep learning training:
Train: 2-3 CVD subjects = 16-24 samples
Input dim: 30
```

**실질적 sample 수: 16-24 samples (동일!), input dim 30**

---

## 3. 차원 감소의 효과: 정말 중요한가?

### Deep Learning Model 복잡도

#### Procrustes (p=279)

```python
# Simple MLP
model = nn.Sequential(
    nn.Linear(279, 128),
    nn.ReLU(),
    nn.Linear(128, 64),
    nn.ReLU(),
    nn.Linear(64, 279)
)

# Parameters:
# 279 → 128: 279 × 128 = 35,712
# 128 → 64: 128 × 64 = 8,192
# 64 → 279: 64 × 279 = 17,856
# Total: ~62,000 parameters

# Training samples: 24
# Parameters per sample: 62,000 / 24 = 2,583

→ SEVERE overfitting risk!
```

#### SRM (k=30)

```python
# Simple MLP
model = nn.Sequential(
    nn.Linear(30, 64),
    nn.ReLU(),
    nn.Linear(64, 32),
    nn.ReLU(),
    nn.Linear(32, 30)
)

# Parameters:
# 30 → 64: 30 × 64 = 1,920
# 64 → 32: 64 × 32 = 2,048
# 32 → 30: 32 × 30 = 960
# Total: ~5,000 parameters

# Training samples: 24
# Parameters per sample: 5,000 / 24 = 208

→ Still high but much better!
```

**차이:**
- Procrustes: 2,583 params/sample
- SRM: 208 params/sample
- **12배 차이!**

---

## 4. 하지만 근본적 문제: Sample 수

### Sample 수가 여전히 너무 적음

```python
# 어떤 방법을 써도:
Training samples: 16-24 (CVD subjects × 8 colors)

# Rule of thumb (deep learning):
Min samples ≈ 10 × parameters

SRM model (5,000 params):
  Min samples: 50,000
  Actual samples: 24
  Ratio: 0.05%

→ 여전히 extremely underdetermined!
```

### 가능한 해결책들

#### Option 1: Data Augmentation

```python
# Procrustes/SRM 모두 가능:
1. Color jittering (simulate slight color variations)
2. Noise injection
3. Interpolation between colors
4. Cross-subject averaging

# 하지만 이것도 "가짜" 데이터...
```

#### Option 2: Transfer Learning

```python
# Pre-train on HC subjects:
1. Train autoencoder on HC patterns
2. Fine-tune on CVD

# 하지만 HC ≠ CVD (근본적으로 다름)
```

#### Option 3: Simpler Model

```python
# Linear or shallow model:
model = nn.Linear(279, 279)  # or (30, 30)
# Parameters: 279² = 77,841 or 30² = 900

# With regularization:
loss = MSE + λ * ||W||²

# SRM이 여기서 advantage (900 << 77,841)
```

---

## 5. SRM의 실제 장점 (딥러닝 관점)

### ✅ Advantage 1: Model Capacity 감소

```
Procrustes: 62,000 parameters (MLP)
SRM: 5,000 parameters (MLP)

→ 12배 fewer parameters
→ Less overfitting risk
```

### ✅ Advantage 2: Feature Interpretability

```python
# SRM의 30 features는:
- Shared across all HC subjects
- Captures "common color structure"
- More interpretable than raw voxels

# Deep learning에서:
- Intermediate layers가 meaningful features 학습하기 쉬움
- 30-dim은 이미 "denoised" representation
```

### ✅ Advantage 3: Regularization Effect

```python
# SRM 자체가 regularization:
- 279 voxels → 30 features
- Noise가 많이 제거됨
- Signal-to-noise improved

# Deep learning benefit:
- Cleaner input → better learning
```

### ❌ Disadvantage 1: Sample 수는 동일

```
Both:
- Training samples: 16-24
- 여전히 너무 적음
```

### ❌ Disadvantage 2: 추가 Assumption

```
SRM assumes:
- Shared response structure across HC
- CVD도 같은 structure에 project 가능

Procrustes:
- Geometric alignment만 (more general)
```

---

## 6. 실증적 비교가 필요

### 실험 설계

```python
# Experiment: Cross-validated prediction

for test_cvd in CVD_subjects:
    train_cvds = [other CVDs]

    # Method 1: Procrustes
    model_procrustes = train_DL(
        HC_patterns_procrustes,  # (N, 279)
        train_cvds_procrustes,   # (M, 279)
    )
    pred_procrustes = model_procrustes(test_cvd)

    # Method 2: SRM
    model_srm = train_DL(
        HC_patterns_srm,  # (N, 30)
        train_cvds_srm,   # (M, 30)
    )
    pred_srm = model_srm(test_cvd)

    # Compare:
    error_procrustes = MSE(pred_procrustes, test_cvd_true)
    error_srm = MSE(pred_srm, test_cvd_true)
```

**예상:**
- SRM이 더 낮은 error (fewer params, less overfitting)
- 하지만 둘 다 high error (sample 수 부족)

---

## 7. 대안: Linear Model

### 사실 딥러닝이 필요한가?

```python
# Sample 수가 24개면:
# Linear model이 더 적합할 수 있음!

# Linear transformation:
Y_cvd = W @ X_hc + b

# Procrustes:
W: (279, 279) → 77,841 parameters (너무 많음)

# SRM:
W: (30, 30) → 900 parameters (관리 가능!)

# With ridge regularization:
W* = (X.T @ X + λI)^(-1) @ X.T @ Y

# SRM이 여기서 clear advantage!
```

### Ridge Regression 비교

```python
# Sample 수: 24
# Regularization: Ridge (L2)

Procrustes Ridge:
- X: (24, 279)
- Y: (24, 279)
- W: (279, 279)
- Need strong λ to avoid overfitting

SRM Ridge:
- X: (24, 30)
- Y: (24, 30)
- W: (30, 30)
- Less regularization needed

→ SRM advantage 명확!
```

---

## 8. 최종 답변: "SRM은 왜 딥러닝에 좋음?"

### 정직한 답변:

**✅ SRM이 딥러닝에 좋은 이유:**

1. **Model capacity 감소**
   - 62,000 params → 5,000 params (MLP)
   - 77,841 params → 900 params (Linear)
   - **Overfitting 위험 크게 감소**

2. **Feature quality**
   - 30-dim shared features = denoised, structured
   - Raw 279 voxels보다 clean
   - Learning이 더 쉬움

3. **Regularization 효과**
   - Dimensionality reduction 자체가 regularization
   - Better generalization

**❌ 하지만 근본적 한계:**

1. **Sample 수는 여전히 적음**
   - Procrustes: 24 samples
   - SRM: 24 samples (동일!)
   - 둘 다 deep learning에 부족

2. **추가 가정**
   - SRM은 shared structure 가정
   - Procrustes는 더 general

**🤔 진짜 질문:**

"딥러닝이 필요한가?"

Sample 24개로는:
- **Linear model이 더 적합!**
- SRM + Ridge Regression
- 또는 Procrustes + Strong regularization

Deep learning:
- Sample 수 ≥ 100-1,000 필요
- 우리는 24개...

---

## 9. 실용적 권장사항

### For Your Data (24 samples)

#### Best Approach: SRM + Linear Model

```python
# 1. SRM for dimensionality reduction
srm = SRM(features=30)
srm.fit(HC_data)

HC_shared = srm.shared_response  # (30, 8)
CVD_shared = [srm.transform(cvd) for cvd in CVD_data]

# 2. Linear regression (Ridge)
from sklearn.linear_model import Ridge

X = HC_shared.T  # (8, 30)
Y = CVD_shared_avg.T  # (8, 30)

model = Ridge(alpha=1.0)
model.fit(X, Y)

# Parameters: 30 × 30 = 900
# Samples: 24
# Manageable!
```

#### Alternative: Procrustes (Already Working)

```python
# 이미 잘 작동하고 있음
# Deep learning 추가 불필요
# Statistical analysis로 충분
```

#### If You Really Want Deep Learning: Procrustes + Heavy Regularization

```python
model = nn.Sequential(
    nn.Linear(279, 64),
    nn.ReLU(),
    nn.Dropout(0.5),  # Strong dropout
    nn.Linear(64, 279)
)

# Training:
optimizer = optim.Adam(params, lr=1e-4, weight_decay=1e-2)  # Strong L2
# + Early stopping
# + Data augmentation
```

---

## 10. 결론

**"SRM은 왜 딥러닝에 좋음?"**

**정확한 답:**

SRM이 딥러닝에 "좋은" 이유는:
1. ✅ **모델 복잡도 크게 감소** (12배)
2. ✅ **Cleaner features**
3. ✅ **Built-in regularization**

**하지만:**
- Sample 수는 동일 (24개)
- 여전히 deep learning에 부족
- **Linear model이 더 적합할 수 있음!**

**실용적 결론:**

Sample 24개로는:
- **SRM + Linear**: Best for prediction
- **Procrustes**: Best for interpretation
- **Deep learning**: Risky (overfitting)

제가 "SRM이 딥러닝에 좋다"고 과장했을 수 있습니다.
정확히는 "SRM이 Procrustes보다 적은 파라미터로 모델링 가능"입니다!
