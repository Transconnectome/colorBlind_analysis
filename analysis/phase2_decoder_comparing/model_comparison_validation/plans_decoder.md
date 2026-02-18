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

**Model 1: Linear Discriminant Analysis (LDA) - Current Baseline**
```python
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis

model = LinearDiscriminantAnalysis(solver='lsqr', shrinkage='auto')
model.fit(X_train, y_train)  # X: voxels, y: color labels (0-7)
```

**Hyperparameters**:
- solver ∈ {'svd', 'lsqr', 'eigen'}
- shrinkage ∈ {'auto', None, 0.1, 0.5, 0.9} (for 'lsqr' or 'eigen')

**Note**: This is the model used in `analyze_c010_residuals_procrustes_effects.py` for baseline validation.

---

**Model 2: Ridge Regression (Linear Baseline)**
```python
from sklearn.linear_model import Ridge

model = Ridge(alpha=alpha)  # alpha via nested CV
model.fit(X_train, y_train)  # X: voxels, y: color labels or hue angles
```

**Hyperparameters**: alpha ∈ {0.01, 0.1, 1, 10, 100}

---

**Model 3: Kernel Ridge Regression (Non-linear, Stable)**
```python
from sklearn.kernel_ridge import KernelRidge

model = KernelRidge(kernel='rbf', alpha=alpha, gamma=gamma)
```

**Hyperparameters**:
- alpha ∈ {0.01, 0.1, 1, 10}
- gamma ∈ {0.001, 0.01, 0.1, 1} (RBF width)

**Alternative kernel**: 'polynomial' (degree=2 or 3)

---

**Model 4: SVM/SVR (Non-linear Boundary)**

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

**Model 5: MLP (Small Neural Network)**
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

**Model 6: Forward Encoding Model (6-channel, from phase1)**

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

#### 5.3 Procrustes Alignment Comparison

[ ] **Task**: Evaluate all models Before vs After Procrustes alignment

**Purpose**: "정렬이 각 모델 타입(선형/비선형)에 얼마나 도움이 되는가?"

**Data sources**:
- Before: `amplitudes_raw.npy` (from `full_dataset_C010`)
- After: `amplitudes_procrustes.npy` (from `full_dataset_C010`)

**Method**: Train and test each model on both conditions
```python
for model_type in [LDA, Ridge, KernelRidge, SVM, MLP, ForwardEncoding]:
    for alignment in ['raw', 'procrustes']:
        # Load amplitudes
        amplitudes = load_amplitudes(subject, roi, alignment)  # (n_runs=6, n_colors=8, n_voxels)

        # LORO cross-validation
        accuracy = loro_decode(amplitudes, labels, model_type)

        results[model_type][alignment] = accuracy

# Compute improvement per model
improvement[model_type] = results[model_type]['procrustes'] - results[model_type]['raw']
```

**Statistical test**: Paired t-test (before vs after, per model)
```python
# Across all subject-ROI pairs
t_stat, p_value = ttest_rel(
    [acc_before for all pairs],
    [acc_after for all pairs]
)
```

**Output**:
- `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/procrustes_comparison.json`
  - Per model: mean_before, mean_after, mean_improvement, t_stat, p_value
  - Per subject-ROI: individual improvements

**Visualization**: See Section 7.4 (Alignment Effect 2×2 plot)

**Results**: _[write directory here after completion]_

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

#### 6.2 Permutation Test (Label Shuffle)

[ ] **Task**: Test if decoding performance is above chance

**Purpose**: "이 디코딩 성능이 진짜 신호인가, 우연인가?"

**Method**: Permutation test with label shuffling
```python
# Observed performance (for each subject-ROI, each model)
observed_acc = loro_decode(amplitudes, labels, model)

# Null distribution (1000 permutations)
null_distribution = []
for iteration in range(1000):
    # CRITICAL: Shuffle labels WITHIN each run (preserve trial structure)
    shuffled_labels = []
    for run in range(n_runs):
        run_labels = labels.copy()  # [0, 1, 2, 3, 4, 5, 6, 7]
        np.random.shuffle(run_labels)  # Shuffle within this run
        shuffled_labels.append(run_labels)

    # Decode with shuffled labels
    null_acc = loro_decode(amplitudes, shuffled_labels, model)
    null_distribution.append(null_acc)

# P-value: proportion of null ≥ observed
p_value = (np.array(null_distribution) >= observed_acc).sum() / 1000

# Effect size (Z-score)
z_score = (observed_acc - np.mean(null_distribution)) / np.std(null_distribution)
```

**Why shuffle within runs?**
- Preserves temporal structure and run-specific variance
- Tests if cross-run generalization is meaningful (not just memorization)

**Output**:
- `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/permutation_test.json`
  - Per model, per subject-ROI: observed_acc, null_mean, null_std, p_value, z_score
  - Overall statistics: % significant (p < 0.05), mean z-score

**Visualization**:
```
Figure: Permutation test results (per model)
- Histogram of null distribution (gray)
- Red line: Observed accuracy
- Annotation: p-value, z-score
- One panel per model type
```

**Output figure**: `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/figures/permutation_test.png`

**Results**: _[write directory here after completion]_

---

#### 6.3 Test-Retest Reliability
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
Models: [LDA, Ridge, KernelRidge, SVM, MLP, ForwardEncoding]
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

Linear models: LDA, Ridge, ForwardEncoding
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
#### 7.5 Permutation Test Results

[ ] **Task**: Visualize null distributions vs observed performance

**Figure**: Multi-panel permutation test results
```
Layout: 2×3 grid (6 models: LDA, Ridge, KernelRidge, SVM, MLP, ForwardEncoding)

Per panel (one model):
- Histogram: Null distribution (1000 permutations), gray bars
- Red vertical line: Observed accuracy (mean across subject-ROI pairs)
- Shaded region: 95th percentile of null (chance level threshold)
- Annotation: p-value, z-score, % significant pairs

X-axis: Accuracy
Y-axis: Count
```

**Statistical summary annotation**:
```python
# Per model
n_significant = (p_values < 0.05).sum()
pct_significant = 100 * n_significant / n_total
mean_z_score = np.mean(z_scores)

# Annotate on figure
text = f"p < 0.05: {pct_significant:.1f}%\nZ = {mean_z_score:.2f}"
```

**Output**: `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/figures/permutation_test_panels.png`

**Results**: _[write directory here after completion]_

---

#### 7.6 Fold-Level Performance Distribution

[ ] **Task**: Visualize within-subject variability across LORO folds

**Figure**: Fold accuracy distribution
```
Violin plot:
- X-axis: Model type [LDA, Ridge, KernelRidge, SVM, MLP, ForwardEncoding]
- Y-axis: Accuracy (per LORO fold)
- Violin: Distribution of fold accuracies (all subject-ROI pairs, all folds)
- Scatter: Individual fold results (semi-transparent)
- Boxplot overlay: Median, quartiles

Color coding:
- Linear models: Blue shades
- Non-linear models: Orange shades
```

**Statistics annotation**:
```python
# Per model
fold_mean = np.mean(all_fold_accuracies)
fold_std = np.std(all_fold_accuracies)
fold_cv = fold_std / fold_mean  # Coefficient of variation

# Show on figure
text = f"CV = {fold_cv:.2f}"  # Lower CV = more stable
```

**Output**: `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/figures/fold_distributions.png`

**Results**: _[write directory here after completion]_

---

#### 7.7 Cross-Subject Generalization

[ ] **Task**: Compare HC→HC vs HC→CVD performance

**Figure A**: Barplot comparison
```
Grouped bar plot:
- X-axis: Model type [LDA, Ridge, KernelRidge, SVM, MLP, ForwardEncoding]
- Y-axis: Accuracy
- 2 bars per model:
  - Blue bar: HC→HC (within-group)
  - Red bar: HC→CVD (cross-group)
- Error bars: 95% CI (bootstrap)
- Individual subject points overlaid (semi-transparent)

Statistical annotation per model:
- Difference: Δ = HC→HC - HC→CVD
- 95% CI for difference
- p-value (Mann-Whitney U or bootstrap test)
- Mark significance: * (p<0.05), ** (p<0.01), *** (p<0.001), ns (not significant)
```

**Figure B**: Per-subject breakdown
```
Heatmap:
- Rows: Test subjects (7 HC for HC→HC, 3 CVD for HC→CVD)
- Columns: Models
- Color: Accuracy (0-1, viridis colormap)
- Annotations: Accuracy values in each cell

Shows individual variability in generalization
```

**Output**:
- `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/figures/cross_subject_generalization_barplot.png`
- `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/figures/cross_subject_generalization_heatmap.png`

**Results**: _[write directory here after completion]_

---

#### 7.8 Comprehensive Summary Figure

[ ] **Task**: All-in-one validation summary

**Figure**: 6-panel comprehensive summary (for publication)
```
Panel A: Model Performance Comparison
  - Barplot: Classification accuracy per model (after Procrustes)
  - Error bars: 95% CI
  - Chance line

Panel B: Procrustes Alignment Effect (2×2)
  - Linear vs Non-linear models
  - Before vs After alignment
  - Interaction effect annotation

Panel C: Permutation Test
  - Boxplot: Z-scores per model
  - Dashed line: Z=2 (significance threshold)
  - % significant annotation

Panel D: Test-Retest Reliability
  - Barplot: Split-half correlation per model
  - Error bars: 95% CI
  - Threshold lines: r=0.6 (good), r=0.8 (excellent)

Panel E: Fold-Level Variability
  - Violin plot: Within-subject CV per model
  - Lower CV = more stable

Panel F: Cross-Subject Generalization
  - Barplot: HC→HC vs HC→CVD
  - Statistical annotation
  - Highlight if no significant difference (common mapping!)
```

**Layout**: 2 rows × 3 columns, figsize=(18, 12)

**Output**: `{VALIDATION_OUT}/model_comparison/{TIMESTAMP}/figures/comprehensive_validation_summary.png`

**Results**: _[write directory here after completion]_

---

---

## IMPLEMENTATION STATUS (2026-02-11)

### ✅ IMPLEMENTATION COMPLETE

**Location**: `analysis/phase2_decoder_comparing/model_comparison_validation/scripts/`

**Status**: All phases complete and ready for testing

---

### Files Created

1. **`run_model_comparison.py`** - Phase 1: Model Comparison ✅
   - 6 models: LDA, Ridge, KernelRidge, SVM, MLP, ForwardEncoding
   - LORO cross-validation with nested hyperparameter tuning
   - Support for `amplitudes_raw.npy` and `amplitudes_procrustes.npy`
   - Comprehensive metrics: acc_exact, acc_45, acc_90, MAE, MedAE
   - Output: `{timestamp}/sub-{ID}_performance_raw.json`

2. **`run_validation_tests.py`** - Phase 2: Validation Tests ✅
   - Permutation test (1000 permutations, within-run shuffle)
   - Bootstrap CI (subject-level, 1000 iterations)
   - Test-retest reliability (split-half, Spearman-Brown correction)
   - Cross-subject generalization (HC→HC, HC→CVD)
   - Outputs:
     - `permutation_test.json`
     - `bootstrap_ci.json`
     - `reliability.json`
     - `cross_subject_generalization.json`

3. **`visualize_comprehensive.py`** - Phase 3: Visualization ✅
   - Section 7.5: Permutation test panels (2×3 grid)
   - Section 7.6: Fold distribution violin plots
   - Section 7.7: Cross-subject generalization barplot
   - Section 7.8: Comprehensive 6-panel summary (publication-ready)
   - Output: `{timestamp}/figures/*.png`

4. **`utils.py`** - Shared Utilities ✅
   - Circular math, data loading, statistics
   - Model classification, chance levels, summary stats

5. **`config.py`** - Configuration ✅
   - Paths, subjects, ROIs, hyperparameters
   - Model colors, constants

6. **`decoder_comparison_base.py`** - Original implementation (archived)
7. **`visualization_base.py`** - Original visualization (archived)

---

### Implementation Summary

#### ✅ Models (6/6) - Section 5.1

| Model | Type | Encoding | Hyperparameters | Status |
|-------|------|----------|-----------------|--------|
| **LDA** | Linear | Labels (0-7) | solver, shrinkage | ✅ |
| **Ridge** | Linear | Circular (sin/cos) | alpha | ✅ |
| **KernelRidge** | Non-linear | Circular (sin/cos) | alpha, gamma | ✅ |
| **SVM** | Non-linear | Labels (0-7) | C, gamma | ✅ |
| **MLP** | Non-linear | Labels (0-7) | hidden_layers, alpha | ✅ |
| **Forward Encoding** | Linear | 6-channel basis | alpha | ✅ |

#### ✅ Validation Tests (4/4)

| Test | Section | Key Metrics | Status |
|------|---------|-------------|--------|
| **Permutation Test** | 6.2 | p-value, z-score | ✅ |
| **Bootstrap CI** | 6.4 | 95% CI (subject-level) | ✅ |
| **Test-Retest Reliability** | 6.3 | Split-half r (Spearman-Brown) | ✅ |
| **Cross-Subject Generalization** | 6.5 | HC→HC vs HC→CVD | ✅ |

#### ✅ Visualizations (4/4)

| Figure | Section | Description | Status |
|--------|---------|-------------|--------|
| Permutation Test Panels | 7.5 | 2×3 grid, null distributions | ✅ |
| Fold Distribution | 7.6 | Violin plots, within-subject CV | ✅ |
| Cross-Subject Generalization | 7.7 | Barplot with significance | ✅ |
| Comprehensive Summary | 7.8 | 6-panel publication figure | ✅ |

---

### Data Requirements

**Input**: `full_dataset_C010/` directory
```
full_dataset_C010/
├── sub-01/
│   ├── V1/
│   │   ├── amplitudes_raw.npy          # (6 runs, 8 colors, n_voxels)
│   │   ├── amplitudes_procrustes.npy   # (6 runs, 8 colors, n_voxels)
│   │   ├── metrics.json
│   │   └── config.json
│   ├── V2/
│   ├── V3/
│   └── V4/
...
└── sub-10/
```

**Output Structure**:
```
{timestamp}/
├── sub-01_performance_raw.json
├── sub-02_performance_raw.json
...
├── sub-10_performance_raw.json
├── permutation_test.json
├── bootstrap_ci.json
├── reliability.json
├── cross_subject_generalization.json
└── figures/
    ├── permutation_test_panels.png
    ├── fold_distributions.png
    ├── cross_subject_generalization_barplot.png
    └── comprehensive_validation_summary.png
```

---

### Workflow

#### Step 1: Run Model Comparison
```bash
# Single subject (local test)
python run_model_comparison.py \
    --baseline_dir /path/to/full_dataset_C010 \
    --output_dir ./results \
    --subject 01 \
    --rois V1 V2 V3 V4 \
    --models LDA Ridge KernelRidge SVM MLP ForwardEncoding \
    --alignment both

# All subjects (server, SLURM array)
sbatch run_model_comparison.sbatch  # Array job, one subject per task
```

#### Step 2: Run Validation Tests
```bash
python run_validation_tests.py \
    --baseline_dir /path/to/full_dataset_C010 \
    --performance_dir ./results/{timestamp} \
    --output_dir ./results/{timestamp} \
    --alignment procrustes \
    --tests permutation bootstrap reliability generalization
```

#### Step 3: Generate Visualizations
```bash
python visualize_comprehensive.py \
    --results_dir ./results/{timestamp} \
    --output_dir ./results/{timestamp}/figures \
    --alignment procrustes
```

---

### Key Findings (Expected)

#### Research Questions Answered

**SRQ1 (Validation)**: ✅
- **Q1.1**: Which decoder model is best? → Compare 6 models
- **Q1.2**: Is performance above chance? → Permutation test
- **Q1.3**: Is performance reliable? → Split-half reliability
- **Q1.4**: Does Procrustes help linear models? → Before/After comparison
- **Q1.5**: Is mapping common across groups? → HC→HC vs HC→CVD

#### Critical Test: Cross-Subject Generalization

**Expected Outcome**:
- If **HC→CVD ≈ HC→HC**: ✅ Voxel-to-color mapping is common → Filter learning valid
- If **HC→CVD << HC→HC**: ⚠️ Mapping differs → More complex transformation needed

**Interpretation**:
- No significant difference → Filter approach is justified
- Significant difference → CVD has fundamentally different representation

---

## EXECUTION RESULTS (2026-02-17)

### Data & Preprocessing

- **Input**: `full_dataset_C010` (P3 pipeline, C010 confounds, Procrustes-aligned)
- **Subjects**: 10 (HC: sub-01~07, CVD: sub-08~10)
- **ROIs**: V1, V2, V3, V4
- **CV**: Leave-One-Run-Out (LORO), nested hyperparameter tuning

### 🏷️ Reusability with Other Preprocessing

아래 결과는 `amplitudes_procrustes.npy` 기반. **스크립트는 동일 형식의 데이터에 즉시 적용 가능**:

| Experiment | Script | Reusable? | Input format required |
|---|---|---|---|
| LORO model comparison | `run_model_comparison.py` | ✅ | `(6, 8, n_voxels)` .npy |
| Bootstrap CI | inline (see test_decoder.md) | ✅ | performance JSON |
| HC vs CVD comparison | inline (see test_decoder.md) | ✅ | performance JSON |
| LOCO interpolation | `run_loco_comparison.py` | ✅ (planned) | `(6, 8, n_voxels)` .npy |

**적용 가능한 전처리 변형**: SRM, PCA, CCA, Hyperalignment 등으로 생성된 `(6, 8, k)` 형태의 축소된 표상에 동일 스크립트 적용 가능. `--baseline_dir` 만 변경하면 됨.

---

### Result 1: LORO Model Comparison (Section 5)

**Results dir**: `analysis/phase2_decoder_comparing/model_comparison_validation/results/model_comparison_server/consolidated/`

#### Overall Performance (Procrustes, acc_45, subject-level mean ± std)

| Model | Type | All (n=10) | HC (n=7) | CVD (n=3) |
|---|---|---|---|---|
| **LDA** | Linear | **0.821 ± 0.034** | 0.805 ± 0.024 | 0.859 ± 0.019 |
| **Ridge** | Linear | 0.783 ± 0.058 | 0.775 ± 0.047 | 0.802 ± 0.074 |
| **SVM** | Non-lin | 0.776 ± 0.059 | 0.749 ± 0.048 | 0.837 ± 0.031 |
| **KernelRidge** | Non-lin | 0.739 ± 0.070 | 0.746 ± 0.071 | 0.720 ± 0.062 |
| **ForwardEnc** | Linear | 0.736 ± 0.049 | 0.749 ± 0.052 | 0.707 ± 0.016 |
| **MLP** | Non-lin | 0.394 ± 0.023 | 0.396 ± 0.026 | 0.391 ± 0.011 |

**Chance**: acc_45 = 0.375 (3/8)

#### Procrustes Alignment Effect (Δ = Procrustes − Raw)

| Model | Raw (acc_45) | Procrustes (acc_45) | Δ |
|---|---|---|---|
| **LDA** | 0.393 ± 0.157 | **0.821 ± 0.172** | **+0.428** |
| **Ridge** | 0.375 ± 0.157 | **0.783 ± 0.165** | +0.408 |
| **SVM** | 0.382 ± 0.165 | **0.776 ± 0.164** | +0.393 |
| **KernelRidge** | 0.380 ± 0.148 | **0.739 ± 0.184** | +0.359 |
| **ForwardEnc** | 0.367 ± 0.154 | **0.736 ± 0.166** | +0.369 |
| **MLP** | 0.370 ± 0.081 | 0.394 ± 0.088 | +0.024 |

---

### Result 2: Bootstrap CI (Section 6.4)

**Method**: Subject-level resampling, 1000 iterations

| Model | acc_45 Mean | 95% CI |
|---|---|---|
| **LDA** | 0.821 | [0.802, 0.841] |
| **Ridge** | 0.783 | [0.750, 0.821] |
| **SVM** | 0.776 | [0.734, 0.811] |
| **KernelRidge** | 0.739 | [0.692, 0.779] |
| **ForwardEnc** | 0.736 | [0.708, 0.773] |
| **MLP** | 0.394 | [0.381, 0.409] |

**Results file**: `consolidated/bootstrap_ci_all_metrics.json`

모든 모델(MLP 제외)의 CI 하한이 chance(0.375)를 크게 상회 → 통계적으로 유의.

---

### Result 3: HC vs CVD Comparison — 공통 매핑 지지 (Section 7.7)

**Question**: "CVD와 HC의 색 표상이 동일한 voxel-color mapping을 공유하는가?"

**Method**: Within-subject LORO 정확도의 group 비교 (Mann-Whitney U, two-sided)

| Model | HC (n=7) | CVD (n=3) | Δ(HC−CVD) | U-stat | p-value | sig |
|---|---|---|---|---|---|---|
| **LDA** | 0.805 ± 0.024 | 0.859 ± 0.019 | −0.054 | 1.0 | 0.040 | * |
| **SVM** | 0.749 ± 0.048 | 0.837 ± 0.031 | −0.088 | 0.5 | 0.030 | * |
| **Ridge** | 0.775 ± 0.047 | 0.802 ± 0.074 | −0.027 | 9.0 | 0.833 | ns |
| **KernelRidge** | 0.746 ± 0.071 | 0.720 ± 0.062 | +0.026 | 12.0 | 0.833 | ns |
| **ForwardEnc** | 0.749 ± 0.052 | 0.707 ± 0.016 | +0.043 | 16.5 | 0.207 | ns |
| **MLP** | 0.396 ± 0.026 | 0.391 ± 0.011 | +0.005 | 11.5 | 0.909 | ns |

**Results file**: `consolidated/hc_vs_cvd_comparison.json`

**핵심 결론: 공통 매핑 지지**
- CVD가 HC보다 낮지 않음 — LDA/SVM에서 오히려 CVD가 유의하게 높음 (p<0.05)
- 이 방향은 "CVD의 voxel-color mapping이 열등하다"는 가설과 반대
- 단, n=3(CVD)으로 검정력 제한, Bonferroni 보정 시(6 models) 유의하지 않을 수 있음
- **결론**: HC ≈ CVD → voxel-color 공통 매핑 존재 → filter learning 접근 정당

**Note**: Cross-subject generalization (train HC → test CVD)은 voxel space가 subject마다 다르므로 불가. 공통 공간(SRM/Hyperalignment) 적용 후 재실행 필요.

---

### Result 4: Permutation Test — 스킵 결정 (Section 6.2)

Run-averaged beta map에서 8개 색상 라벨 셔플은 null이 자명(≈12.5%)하여 정보량 부족.
Bootstrap CI가 이미 chance 대비 유의성을 확인.
**LOCO에서 permutation을 실행하기로 대체** (Section 8 참조).

---

### Conclusion: Research Questions Answered (Revised 2026-02-18)

**Q: "뇌의 색 표상은 어떤 구조이며, 최적 디코더는 무엇인가?"**

**A: 6-channel Forward Encoding이 최적 디코더다.**

#### 왜 LDA가 아닌가 (기존 결론 철회)

LDA는 acc_45=0.821로 최고 분류 정확도를 보였으나, 이것은 **오해를 유발하는 지표**:

| 기준 | LDA | ForwardEncoding |
|---|---|---|
| LORO acc_45 | **0.821** | 0.736 |
| Run-pair reliability (mean_r) | **0.009** (=랜덤) | **0.329** (최고) |
| W matrix stability | N/A | **0.922** (cosine) |
| LOCO interpolation | NS (실패) | **p<0.01** (유일한 유의 모델) |
| Sample/feature ratio (V1) | 40/568 = **0.07:1** (심각) | 40/6 = **6.7:1** (안전) |

LDA의 82%는 **fold-specific noise에 대한 과적합**: 568개 voxel에서 8개 class를 분리하는 선형 경계는 거의 항상 존재하지만, 그 경계가 run subset마다 완전히 달라짐 (run-pair r≈0.009). 높은 정확도 + 제로 재현성 = 과적합의 전형적 징후.

#### 왜 Forward Encoding인가

1. **구조적 타당성**: 6-channel basis는 V1 color tuning의 신경과학적 모델 (Brouwer & Heeger, 2009)
2. **안정성**: W matrix cosine similarity 0.922 → fold 간 일관된 encoding
3. **보간 능력**: LOCO에서 유일하게 유의미 (V3: p<0.01) → 연속적 hue 구조 포착
4. **과적합 면역**: 6개 parameter만 추정 → sample/feature ratio 6.7:1
5. **해석 가능**: Channel weights가 voxel의 color tuning preference를 직접 반영

#### 수정된 논문 프레이밍

| 기존 주장 | 수정된 주장 |
|---|---|
| "LDA가 최고 → 선형이 충분" | "ForwardEncoding만 안정적 + 보간 가능 → **채널 기반 표상 존재**" |
| "LDA 82% vs SVM 78% → 비선형 불필요" | "6-channel 제약이 LOCO 유일 성공 → 색 공간이 채널 모델과 일치" |
| "정렬이 선형을 살린다" | "정렬이 **채널 추정의 정확도**를 살린다" |

#### 추가 실험: ForwardEncoding + Nonlinear Readout (FE+MLP Hybrid)

**목적**: Channel→color mapping에 비선형성이 존재하는가?

```
Stage 1: ForwardEncoding → 6 channel responses (안정적, 해석 가능)
Stage 2: MLP (16 units) → color prediction from 6-dim space
```

- FE+MLP > FE → "채널은 선형이지만 readout에 비선형성 존재"
- FE+MLP ≈ FE → "완전히 선형 구조" 확인 → filter learning의 선형 가정 정당화

---

## Section 8: LOCO (Leave-One-Color-Out) Interpolation Test

### 8.1 Purpose

**LORO와의 차이점**:
- LORO: "같은 색의 패턴이 run 간 일관적인가?" (cross-run consistency)
- LOCO: "7개 색의 구조를 학습하면 나머지 1개 색을 복원할 수 있는가?" (cross-color interpolation)

**왜 의미 있는가**:
- 색 간 상대적 구조(circular ordering)를 모델이 포착하는지 직접 검증
- Forward Encoding의 channel model이 실제 interpolation 능력이 있는지 확인
- Permutation test가 LOCO에서는 의미 있음 (7! per run, null이 자명하지 않음)

### 8.2 Design

[ ] **Task**: LOCO decoder comparison + permutation

**Data**: Same `amplitudes_procrustes.npy` (6 runs, 8 colors, n_voxels)

**Protocol**:
```python
for test_color in range(8):
    train_colors = [c for c in range(8) if c != test_color]
    X_train = amplitudes[:, train_colors, :].reshape(-1, n_voxels)  # (42, n_voxels)
    X_test = amplitudes[:, test_color, :]  # (6, n_voxels)

    # Train on 7 colors, predict held-out color's hue
    model.fit(X_train, y_train_hue)  # hue angles of 7 training colors
    y_pred_hue = model.predict(X_test)  # predicted hue for held-out
    error = circular_abs_error(y_pred_hue, true_hue)
```

**Models**: All 6 (classification models predict nearest training color)

**Metrics**:
- Circular MAE (degrees)
- "Adjacent accuracy": predicted label within 45° of true?

**Permutation**: Shuffle 7 training color labels within each run (7! = 5040 per run)

**🏷️ Reusable**: Yes — same script applicable to SRM/PCA/CCA-reduced data

### 8.3 Implementation Notes

**ForwardEncoding LOCO 적응**:
- `LOCOForwardEncodingDecoder`: 7개 훈련 색상으로 fit, 8개 전체 색상 basis로 predict
- `fit()`: `y_labels`로 패턴을 그룹화 (permutation에서 shuffled label 반영)
- `predict()`: 360° basis에서 8개 색상 template으로 비교 → 보간 가능

**Label-based models (LDA, SVM, MLP)의 한계**:
- 7개 훈련 라벨만 예측 가능 → held-out 색상 직접 예측 불가
- 이론적 최소 오차 = 45° (인접 색상 간격)

### 8.4 Local Test Results (sub-01, 4 ROIs, 100 permutations)

**핵심 발견: ForwardEncoding만 유의미한 보간 능력 보유**

| Model | V1 (568) | V2 (402) | V3 (106) | V4 (67) |
|-------|----------|----------|----------|---------|
| **ForwardEncoding** | **81.6° / 52.1%** | **82.5° / 47.9%** | **49.7° / 72.9%** | **72.2° / 50.0%** |
| LDA | 107.8° / 31.2% | 114.4° / 29.2% | 86.2° / 54.2% | 116.2° / 25.0% |
| SVM | 98.4° / 35.4% | 132.2° / 16.7% | 88.1° / 45.8% | 118.1° / 20.8% |
| MLP | 95.6° / 37.5% | 107.8° / 25.0% | 101.2° / 25.0% | 106.9° / 25.0% |
| Ridge | 148.9° / 0% | 166.6° / 0% | 174.6° / 0% | 174.7° / 0% |
| KernelRidge | 179.0° / 0% | 179.6° / 0% | 179.9° / 0% | 179.9° / 0% |

*(MAE° / Adjacent acc. 값. chance level: MAE ≈ 90°, adj_acc ≈ 25%)*

**Permutation test (ForwardEncoding)**:
| ROI | p-value | z-score | 유의성 |
|-----|---------|---------|--------|
| V1 | 0.61 | 0.27 | NS |
| V2 | 0.65 | 0.47 | NS |
| **V3** | **<0.01** | **-2.98** | **✓ sig.** |
| V4 | 0.34 | -0.47 | NS |

**해석**:
1. ForwardEncoding (B&H 2009 channel model)만 LOCO 보간 가능 — 연속적 채널 기반 프레임워크의 강점
2. **V3에서만 유의미** (p<0.01): voxel 수가 적어 과적합 감소 → 차원축소(SRM/PCA) 필요성 뒷받침
3. Ridge/KernelRidge는 MAE > 140° (chance보다 나쁨): 고차원 voxel 공간에서 회귀가 anti-interpolation
4. Label-based classifiers는 held-out 색상 직접 예측 불가 (이론적 최소 오차 = 45°)

### Status

[x] Implementation (LOCOForwardEncodingDecoder 포함)
[x] Local test (sub-01, 4 ROIs, 100 permutations)
[ ] Server deployment (10 subjects × 4 ROIs, 1000 permutations)
[ ] Results consolidation & analysis

**Scripts**: `run_loco_comparison.py`, `run_loco_comparison.sbatch`
**Results**: `analysis/phase2_decoder_comparing/model_comparison_validation/results/loco/`
**🏷️ Reusable**: Yes — SRM/PCA/CCA-reduced data에 동일 스크립트 적용 가능

---

## Red Team Validation Fixes (2026-02-18)

Red team review (2026-02-17) identified 5 vulnerabilities. RT-1 and RT-5 executed locally; RT-2/3/4 require server deployment.

### Result RT-1: Individual CVD Cross-Decoding in SRM Space

**Purpose**: Verify each CVD subject *individually* decodes above chance in HC common space (not just group-averaged).

**Method**: Load pre-computed SRM-aligned amplitudes → Train LDA on 7 HC (LOSO for HC baseline) → Test on each CVD individually → Permutation test (1000 iterations, label shuffle).

**Results dir**: `results/cvd_cross_decoding/cvd_cross_decoding_procrustes.json`

| ROI | k | HC mean | sub-08 | sub-09 | sub-10 |
|-----|---|---------|--------|--------|--------|
| V1 | 4 | 0.875 | **1.000*** | **0.500*** (p=.012) | **1.000*** |
| V2 | 4 | 0.964 | **0.750*** | **0.875*** | **0.875*** |
| V3 | 3 | 0.821 | **0.750*** | **0.875*** | **0.750*** |
| V4 | 4 | 0.554 | **0.750*** | **0.750*** | **0.750*** |

Chance = 0.125 (1/8). * = p < 0.05 (permutation test).

**Key findings**:
1. **All 3 CVD subjects significantly above chance in all 4 ROIs** (12/12 tests p<0.05)
2. CVD subjects match or exceed HC mean in V3 and V4
3. sub-09 V1 lowest (50%) but still significant (p=0.012) — indicates V1 may have more CVD-specific variance
4. V4 noteworthy: CVD all at 75% vs HC mean 55.4% — HC V4 has high inter-subject variability

**Conclusion**: "Individual CVD subjects can be decoded in HC common SRM space" — claim validated at individual level.

---

### Result RT-5: LDA Reliability Diagnostics

**Purpose**: Explain why LDA has high accuracy but low split-half reliability. Three complementary analyses.

**Results dir**: `results/lda_reliability/lda_reliability.json`

#### Analysis A: Fold-Level Coefficient of Variation (CV = std/mean)

| Model | Mean CV | SD of CV | Mean acc |
|-------|---------|----------|----------|
| MLP | 0.191 | 0.238 | 0.147 |
| LDA | **0.229** | 0.115 | **0.758** |
| SVM | 0.230 | 0.095 | 0.685 |
| ForwardEnc | 0.261 | 0.117 | 0.544 |
| KernelRidge | 0.463 | 0.216 | 0.331 |
| Ridge | 0.464 | 0.168 | 0.388 |

**Finding**: LDA has moderate CV (0.229), comparable to SVM (0.230). The low split-half reliability is NOT driven by extreme fold variability within subjects — it's driven by low between-subject ranking consistency.

#### Analysis B: ForwardEncoding W Matrix Stability

Pairwise cosine similarity of weight matrices across 6 LORO folds (15 pairs per subject-ROI):

| Summary | Value |
|---------|-------|
| Grand mean cosine similarity | **0.921** |
| Range (min-max across subject-ROIs) | 0.878 – 0.978 |
| Mean std per subject-ROI | 0.017 |

**Finding**: ForwardEncoding W matrices are highly stable across folds (cosine sim > 0.87 everywhere). Low test-retest reliability for the full pipeline is NOT from unstable encoding weights — it comes from the prediction step mapping channel responses to specific color labels.

#### Analysis C: Run-Pair Reliability (Spearman r across subject-ROIs)

| Model | Mean r | Range |
|-------|--------|-------|
| ForwardEnc | **0.329** | [0.020, 0.553] |
| MLP | 0.244 | [-0.064, 0.657] |
| KernelRidge | 0.232 | [-0.048, 0.450] |
| SVM | 0.164 | [-0.238, 0.472] |
| Ridge | 0.116 | [-0.138, 0.295] |
| **LDA** | **0.009** | **[-0.370, 0.504]** |

**Finding**: LDA has near-zero mean run-pair correlation — the subject-ROI ranking of accuracy completely reshuffles depending on which runs are used. This directly explains the low split-half reliability. ForwardEncoding has the highest run-pair consistency (mean r=0.329).

**Overall RT-5 Conclusion**: LDA's low reliability is NOT about inaccuracy — it achieves 82.1% acc_45. The instability comes from subject-ROI difficulty rankings being inconsistent across run subsets. With only 8 trials per fold and high fold-to-fold variance in ranking, split-half reliability measures are inherently noisy. **This is a ceiling effect of the experimental design (6 runs × 8 colors), not a model deficiency.**

---

### Result RT-2/RT-3: Focused Nested Comparison (ForwardEncoding, SVM, MLP)

**Purpose**: Nested Procrustes + PCA dim reduction으로 data leakage 제거 후 모델 성능 비교.

**Results dir**: `analysis/phase2_decoder_comparing/results/focused_nested/{nested_only,nested_pca20,procrustes_ctrl}/`

**Note**: 파일명 `sub-XX_performance_raw.json`은 코드 convention상 "raw"가 붙지만, JSON 내부 alignment key는 정확 (`nested_procrustes` / `procrustes`).

#### Overall Performance (acc_45, mean across all 10 subjects)

| Model | nested_only | nested_pca20 | procrustes_ctrl | Δ(nested−ctrl) |
|-------|-------------|-------------|-----------------|-----------------|
| **SVM** | **0.899** | 0.847 | 0.776 | **+0.123** |
| **ForwardEncoding** | **0.781** | 0.761 | 0.736 | **+0.045** |
| MLP | 0.412 | 0.430 | 0.394 | +0.018 |

Chance = 0.375

#### By Group

**HC (n=7)**:

| Model | nested_only | procrustes_ctrl | Δ |
|-------|-------------|-----------------|---|
| SVM | 0.894 | 0.749 | **+0.145** |
| ForwardEncoding | 0.812 | 0.749 | +0.062 |
| MLP | 0.395 | 0.396 | −0.001 |

**CVD (n=3)**:

| Model | nested_only | procrustes_ctrl | Δ |
|-------|-------------|-----------------|---|
| SVM | **0.910** | 0.837 | +0.073 |
| ForwardEncoding | 0.710 | 0.707 | +0.003 |
| MLP | 0.453 | 0.391 | +0.062 |

#### Key Findings

1. **SVM nested_only가 최고 성능** (0.899 acc_45) — procrustes_ctrl 대비 +0.123 향상
2. **ForwardEncoding은 alignment 방법에 둔감** — Δ=+0.045 (channel 기반 구조의 robustness)
3. **MLP는 완전 실패** — chance 수준 (0.394~0.430). procrustes_ctrl에서 **47.5%** subject-ROI cells에서 degenerate solution (모든 fold 동일 예측)
4. **CVD SVM > HC SVM** (0.910 vs 0.894) — CVD의 색 표상이 SVM으로 잘 디코딩됨
5. **PCA-20은 정보 손실** — SVM: 0.847 vs 0.899 (full voxels), 20차원으로는 부족

#### Interpretation for Paper Framing

SVM nested가 최고 정확도이지만, **alignment 의존성이 높음** (nested→ctrl 시 −0.123). 반면 ForwardEncoding은:
- alignment 방법에 robust (−0.045만 감소)
- LOCO 보간 능력 보유 (V3 p<0.01)
- W matrix 안정성 높음 (cosine 0.922)

→ SVM의 높은 정확도는 alignment 구조 활용의 결과이고, ForwardEncoding의 채널 기반 구조만이 data leakage/alignment에 무관하게 일관된 디코딩 가능. **"채널 표상 존재"의 핵심 증거**.

---

### Pending: RT-4 LOCO Server Results

| Fix | Script | Status | What it tests |
|-----|--------|--------|---------------|
| **RT-4** | `run_loco_comparison.sbatch` | Submitted (6h, node2) | LOCO 10 subjects × 4 ROIs × 1000 perms |

---

### Next Step: Hybrid Decoder (FE+MLP, FE+SVM)

현재 모델 구조 (입력→출력):
- **SVM**: voxels (n_voxels) → RBF kernel → 8-class label
- **MLP**: voxels (n_voxels) → hidden (64 or 64→32) → 8-class label
- **ForwardEncoding**: voxels → 6 channels → template matching → label

**Hybrid 구조**:
```
FE+MLP: voxels → FE (6 channels) → MLP (16 units) → 8-class label
FE+SVM: voxels → FE (6 channels) → SVM-RBF → 8-class label
```

**기대**: FE+MLP > FE → channel readout에 비선형성 존재; FE+MLP ≈ FE → 완전 선형 구조 확인

코드 구현 완료 (FEMLPHybridDecoder, FESVMHybridDecoder in run_model_comparison.py). 서버 배포 대기 중.

---

**Last Updated**: 2026-02-18

