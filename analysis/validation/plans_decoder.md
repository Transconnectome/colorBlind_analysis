This is to verify data and model structure in the analysis.
Once finished each part, write the directory of result files in this file.

## 0. Configuration

**Dataset**: `method3_header_mi` (current standard)
**Baseline results**: `analysis/phase1_preprocess_decoding/results/full_dataset_C010`
  - Pipeline: P3 (HRF + time/dispersion derivatives)
  - Confounds: C010 (6 motion + WM/CSF mean)
  - Structure: `sub-{ID}/{ROI}/` with:
    - `amplitudes_raw.npy` (n_runs, n_colors=8, n_voxels)
    - `amplitudes_procrustes.npy` (aligned)
    - `metrics.json` (RDM reliability, disparity, etc.)
    - `config.json` (pipeline settings)

**ROIs**: V1, V2, V3, V4
**Subjects**:
  - HC (non-CVD): sub-01 ~ sub-07 (7명)
  - CVD: sub-08 ~ sub-10 (3명)

**Local paths**:
```
BASELINE_RESULTS=/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/phase1_preprocess_decoding/results/full_dataset_C010
VALIDATION_OUT=/Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/validation/results
```

**Server paths** (for running models):
```
FMRIPREP_OUT=/storage/connectome/haba6030/fmriprep_out_method3_header_mi
BASELINE_RESULTS=/scratch/connectome/haba6030/colorBlind/derivatives/phase1_results/full_dataset_C010
VALIDATION_OUT=/scratch/connectome/haba6030/colorBlind/analysis/validation/results
```

---


## Decoding Model Validation

**Purpose**: 여러 디코딩 모델 비교 및 현재 linear W의 타당성 검증

**Motivation**:
- **How**: Apply non-linearity in phase1's decoder instead of current linear matrix W
- **Why**: Assuming linearity in brain's channel-voxel mapping may be too vulnerable
- **Question**: "정렬이 선형 모델을 살리는가? 정렬 없으면 비선형이 필요한가?"

---

### 5. Model Comparison Design

#### 5.1 Candidate Models

**All models use the same**:
- Input: Beta patterns (n_trials, n_voxels)
- Output: Predicted color (classification) or predicted hue (reconstruction)
- Cross-validation: Leave-One-Run-Out (LORO)
- Hyperparameter tuning: Nested CV (inner loop on train runs)

---

**Model 1: Ridge Regression (Linear Baseline)**
```python
from sklearn.linear_model import Ridge

model = Ridge(alpha=alpha)  # alpha via nested CV
model.fit(X_train, y_train)  # X: voxels, y: color labels or hue angles
```

**Hyperparameters**: alpha ∈ {0.01, 0.1, 1, 10, 100}

---

**Model 2: Kernel Ridge Regression (Non-linear, Stable)**
```python
from sklearn.kernel_ridge import KernelRidge

model = KernelRidge(kernel='rbf', alpha=alpha, gamma=gamma)
```

**Hyperparameters**:
- alpha ∈ {0.01, 0.1, 1, 10}
- gamma ∈ {0.001, 0.01, 0.1, 1} (RBF width)

**Alternative kernel**: 'polynomial' (degree=2 or 3)

---

**Model 3: SVM/SVR (Non-linear Boundary)**

**For classification**:
```python
from sklearn.svm import SVC

model = SVC(kernel='rbf', C=C, gamma=gamma, probability=True)
```

**For reconstruction** (continuous hue prediction):
```python
from sklearn.svm import SVR

model = SVR(kernel='rbf', C=C, gamma=gamma, epsilon=0.1)
```

**Hyperparameters**:
- C ∈ {0.1, 1, 10, 100}
- gamma ∈ {0.001, 0.01, 0.1, 1}

---

**Model 4: MLP (Small Neural Network)**
```python
from sklearn.neural_network import MLPRegressor

model = MLPRegressor(
    hidden_layer_sizes=(64, 32),
    activation='relu',
    alpha=0.01,  # L2 regularization (STRONG)
    early_stopping=True,
    validation_fraction=0.2,
    max_iter=500
)
```

**Hyperparameters**:
- hidden_layer_sizes ∈ {(32,), (64,), (64, 32)}
- alpha ∈ {0.001, 0.01, 0.1} (regularization strength)

**Warning**: Prone to overfitting → use strong regularization + early stopping

---

**Model 5: Current Forward Encoding (Baseline)**

**For comparison**: 현재 phase1에서 사용 중인 방법
```python
# 6-channel forward encoding model
C = channel_response_matrix  # (n_trials, 6)
B = beta_matrix              # (n_trials, n_voxels)

# Train
W = inv(C.T @ C) @ C.T @ B   # (6, n_voxels)

# Test
C_pred = B_test @ W.T        # (n_test, 6)
decoded_color = argmax(correlation(C_pred, C_templates))
```

---

#### 5.2 Evaluation Protocol

**Cross-validation**: Leave-One-Run-Out (LORO)
```python
for test_run in range(6):
    train_runs = [r for r in range(6) if r != test_run]

    # Inner CV for hyperparameter tuning (on train runs only)
    best_params = grid_search_cv(X_train, y_train, params, cv=5)

    # Train with best params
    model.fit(X_train, y_train, **best_params)

    # Test on held-out run
    y_pred = model.predict(X_test)
    scores.append(evaluate(y_test, y_pred))
```

**Important**: 하이퍼파라미터 튜닝은 train set 내에서만 (test set leakage 방지)

---

---

### 6. Performance Metrics

**Goal**: "분포"로 성능 표현 (단일 점수 대신 subject×run-fold 분포)

---

#### 6.1 Classification & Reconstruction Performance
[ ] **Task**: 모델별 성능 계산 (분포 포함)

**Metrics**:

**A. Classification Accuracy**
```python
# 45° accuracy (adjacent colors, chance=2/8=25%)
acc_45 = (predicted in [true-45°, true, true+45°]).mean()

# 90° accuracy (±1 color, chance=3/8=37.5%)
acc_90 = (predicted in [true-90°, true-45°, true, true+45°, true+90°]).mean()

# Exact accuracy (chance=1/8=12.5%)
acc_exact = (predicted == true).mean()
```

**B. Reconstruction Error**
```python
# Circular error in degrees
error = circular_diff_deg(predicted_hue, true_hue)

# Mean absolute error
MAE = mean(error)

# Median absolute error (robust to outliers)
MedAE = median(error)
```

**Output structure**:
```json
{
  "model": "Ridge",
  "subject": "01",
  "roi": "V1",
  "aligned": false,
  "performance": {
    "acc_45": [0.75, 0.80, 0.78, 0.82, 0.77, 0.81],  // 6 runs (LORO)
    "acc_90": [0.85, 0.88, 0.87, 0.90, 0.86, 0.89],
    "acc_exact": [0.62, 0.68, 0.65, 0.70, 0.64, 0.69],
    "mae": [28.5, 25.3, 27.1, 24.8, 26.9, 25.5],
    "medae": [22.1, 19.8, 21.5, 18.9, 20.7, 19.3]
  },
  "summary": {
    "acc_45_mean": 0.788,
    "acc_45_std": 0.025,
    "mae_mean": 26.35,
    "mae_std": 1.31
  }
}
```

**Save**: `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/performance_raw.json`

**Results**: _[write directory here after completion]_

---

#### 6.2 Test-Retest Reliability
[ ] **Task**: 성능 자체의 재현성 검증

**Purpose**: "이 모델의 성능이 안정적으로 재현되는가?"

**Method**: Split-half correlation on fold-wise scores

**Computation**:
```python
# Each subject has 6 LORO fold scores (one per held-out run)
fold_scores = [score_run1, score_run2, ..., score_run6]

# Bootstrap split-half (1000 iterations)
for iteration in range(1000):
    # Randomly split into two halves
    half_A_indices = random.choice([0,1,2,3,4,5], size=3, replace=False)
    half_B_indices = [remaining runs]

    score_A = mean(fold_scores[half_A_indices])
    score_B = mean(fold_scores[half_B_indices])

    # Correlation across subjects
    r = pearsonr([score_A for all subjects], [score_B for all subjects])

    # Spearman-Brown correction (for split-half)
    r_corrected = 2 * r / (1 + r)
    reliability_estimates.append(r_corrected)

# Report: mean, 95% CI
reliability = {
    'mean': mean(reliability_estimates),
    'ci_lower': percentile(reliability_estimates, 2.5),
    'ci_upper': percentile(reliability_estimates, 97.5)
}
```

**Output**: `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/reliability.json`

**Results**: _[write directory here after completion]_

---

#### 6.3 Confidence Intervals
[ ] **Task**: Bootstrap CI for performance metrics

**Computation**:
```python
# Bootstrap at subject level (1000 iterations)
for iteration in range(1000):
    # Resample subjects with replacement
    sampled_subjects = random.choice(subjects, size=len(subjects), replace=True)

    # Compute metric on resampled data
    metric = compute_metric(sampled_subjects)
    bootstrap_distribution.append(metric)

# 95% CI
CI_lower = percentile(bootstrap_distribution, 2.5)
CI_upper = percentile(bootstrap_distribution, 97.5)
```

**Output**: `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/confidence_intervals.json`

**Results**: _[write directory here after completion]_

---

---

### 7. Visualization: Model Performance Summary

#### 7.1 Performance Comparison (Barplot)
[ ] **Task**: 모델별 성능 비교 막대그래프

**Figure A: Classification Performance**
```
Models: [Ridge, KernelRidge, SVM, MLP, ForwardEncoding]
Metrics: acc_45, acc_90, acc_exact

Bar plot (grouped):
- X-axis: Models
- Y-axis: Accuracy (0-1)
- Error bars: 95% CI (bootstrap)
- 3 bars per model (45°, 90°, exact)
- Horizontal line: chance level
```

**Figure B: Reconstruction Error**
```
Metrics: MAE, MedAE

Bar plot:
- X-axis: Models
- Y-axis: Error (degrees, 0-90)
- Error bars: 95% CI
- Lower is better
- Horizontal line: chance level (90°)
```

**Output**: `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/figures/performance_barplot.png`

**Results**: _[write directory here after completion]_

---

#### 7.2 Test-Retest Reliability (Barplot)
[ ] **Task**: 모델별 reliability 비교

**Figure**: Reliability scores with CI
```
Bar plot:
- X-axis: Models
- Y-axis: Split-half correlation (0-1)
- Error bars: 95% CI from bootstrap
- Higher = more reliable/stable performance
```

**Interpretation**:
- r > 0.8: excellent reliability
- r > 0.6: good reliability
- r < 0.4: poor reliability (성능이 불안정)

**Output**: `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/figures/reliability_barplot.png`

**Results**: _[write directory here after completion]_

---

#### 7.3 Calibration & Uncertainty
[ ] **Task**: 모델의 예측 불확실성 평가

**For classification models** (if probability available):
```python
# Reliability diagram (calibration curve)
from sklearn.calibration import calibration_curve

prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10)

# Expected Calibration Error (ECE)
ECE = mean(abs(prob_true - prob_pred))
```

**Alternative** (if no probability):
```python
# Prediction variance across folds
variance = var([predictions from different folds])
mean_variance = mean(variance)  # Per model
```

**Figure**: Calibration curve or variance barplot

**Output**: `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/figures/calibration.png`

**Results**: _[write directory here after completion]_

---

#### 7.4 Alignment Effect: 2×2 Comparison
[ ] **Task**: "비선형이 정말 필요한가?" 검증

**Critical Question**:
- "정렬이 선형 모델을 살리는가?"
- "정렬이 부족하면 비선형이 버텨주는가?"

**Figure**: 2×2 Barplot
```
Conditions:
- Axis 1 (X): Alignment (Before, After)
- Axis 2 (Color): Model type (Linear, Non-linear)

Linear models: Ridge, ForwardEncoding
Non-linear models: KernelRidge, SVM, MLP

Expected pattern:
- Before alignment: Non-linear > Linear (비선형이 필요)
- After alignment: Linear ≈ Non-linear (정렬이 선형 모델을 살림)

Interaction effect:
- Δ(Linear) > Δ(Non-linear)
  → "정렬이 선형 모델에 더 큰 도움"
```

**Statistical test**:
```python
# 2-way repeated measures ANOVA
factors = ['Alignment (before/after)', 'Model (linear/nonlinear)']
DV = 'accuracy'

# Interaction: Alignment × Model
F_interaction, p_interaction = rm_anova(...)
```

**Output**:
- `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/figures/alignment_effect_2x2.png`
- `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/alignment_interaction_stats.json`

**Results**: _[write directory here after completion]_

---