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

**Location**: `analysis/validation/scripts/model_comparison/`

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

### Next Steps

1. **Local Testing** (single subject, quick models):
   ```bash
   python run_model_comparison.py --subject 01 --rois V1 --models LDA Ridge
   ```

2. **Server Deployment**:
   - Upload scripts to server
   - Create SLURM batch scripts
   - Run array job for all subjects

3. **Analysis**:
   - Run validation tests on complete performance data
   - Generate all figures
   - Interpret cross-subject generalization results

4. **Documentation**:
   - Update with actual results
   - Write interpretation section
   - Prepare for manuscript figures

---

**Status**: ✅ READY FOR EXECUTION

**Implementation Date**: 2026-02-11

**Next Action**: Local testing with single subject

---

