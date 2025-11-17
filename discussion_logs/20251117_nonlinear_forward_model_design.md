# Nonlinear Forward Model Design Discussion

**Date**: 2025-11-17
**Topic**: Adding nonlinearity to PCA → Angle reconstruction pipeline
**Participants**: User, Claude Code

---

## Initial Question

**User**: 현재 zScore를 이용하는 분석코드에서, PCA 정보 → angle로 가는 과정에서 비선형을 추가할 수 있지 않을까? 구체적인 코드를 제시하지는 말고 아이디어를 구체화해보자

**Context**:
- Current pipeline: Z-scores → PCA components → Channel estimates → Angle
- All steps are currently linear (except final argmax)
- Goal: Model nonlinearity in cone → brain perception pathway

**Current Baseline Performance** (from ANALYSIS_SUMMARY_20251117.md):
- **Methods**: zscore vs voxelSelect
- **PCA components**: 6 (current standard)
- **Subjects**: sub-01, sub-02 (Non-CVD) vs sub-03, sub-04 (CVD)
- **Performance**:
  - Classification: 100% (perfect)
  - Reconstruction error: **20.19° ± 23.64°** (zscore), 22.81° (voxelSelect)
  - Novel color error: **84.88° ± 25.40°** (zscore), 91.17° (voxelSelect)
- **Best ROI**: V2 (zscore: 6.09°, voxelSelect: 9.81°)
- **Best configuration**: sub-01, V2, voxelSelect (2.38° reconstruction)
- **CVD vs Non-CVD**: CVD shows 2x higher errors (26.66° vs 13.72°)

---

## Current Pipeline Analysis

```
Z-scores → PCA components → Channel estimates → Angle
   (1)          (2)                (3)            (4)

1. (1→2) PCA transformation: Fully linear (linear projection)
2. (2→3) Forward model: Fully linear (matrix multiplication)
   - W = X_train.T @ C_train.T @ (C_train @ C_train.T)^-1
3. (3→4) Template matching: Argmax (nonlinear but discrete)
```

---

## Five Proposed Options

### Option 1: Nonlinear Transformation on PCA Output

**Concept**: PCA components → **Nonlinear transformation** → Modified features → Channel estimation

**Methods**:
- **Polynomial features**: Add interaction terms (PC1², PC1×PC2, PC2², etc.)
- **Kernel-based transformation**: RBF, polynomial kernels
- **Neural network layer**: 1-2 hidden layers with ReLU/tanh

**Pros**:
- Maintains PCA noise reduction
- Can learn nonlinear color boundaries
- Useful for CVD vs Non-CVD mapping

**Cons**:
- Overfitting risk
- Reduced interpretability

---

### Option 2: Replace Channel Estimation with Nonlinear Model ⭐

**Concept**: Replace linear forward model (W) with nonlinear model

**Methods**:
- **Ridge regression → Neural network**:
  ```
  PCA components → Dense(64, ReLU) → Dense(32, ReLU) → Dense(6, Sigmoid)
  ```
- **Gaussian Process Regression**: With uncertainty quantification
- **Random Forest / Gradient Boosting**: Tree-based models learn interactions automatically

**Pros**:
- Better models brain's nonlinear color encoding
- Relaxes B&H 2009 linear assumption
- Automatic interaction learning (RF)

**Cons**:
- Loss of physiological interpretability
- Overfitting with small data (N_RUNS=6)

**User's Interest**: ⭐ **Most interested in this option** ⭐
- Rationale: "원추세포에서 뇌 지각으로 이어지는 과정이 가장 비선형성을 보일 가능성이 크다"
- Preference: Start with simple models (RF, shallow MLP)

---

### Option 3: Nonlinearity in Channel → Angle Conversion

**Methods**:
- **Weighted correlation**: Channel-specific weights
- **Probabilistic inference**: Von Mises distribution for circular data
- **Circular regression**: Direct channels → angle mapping
- **Manifold learning**: UMAP, t-SNE for circular manifold

**Pros**:
- Maintains physical meaning (channel → angle)
- Uncertainty quantification possible
- Can add smoothness constraints

**Cons**:
- Implementation complexity
- Computational cost

---

### Option 4: Attention Mechanism

**Concept**: Dynamically weight PCA component importance

```
PCA components → Self-Attention → Weighted components → Channel estimation
```

**Pros**:
- Interpretable attention weights
- Color-specific feature importance

**Cons**:
- Unstable with small data
- Needs validation of learned patterns

---

### Option 5: Hybrid Approach (Recommended)

**Phase 1**: PCA → Polynomial features (degree=2)
**Phase 2**: Enhanced features → Linear or shallow NN
**Phase 3**: Channels → Probabilistic inference with Von Mises

**Advantage**: Combines benefits while maintaining interpretability

---

## Selected Approach: Option 2 Implementation

### Models to Implement

1. **Random Forest Regressor** (simple ML)
2. **Light MLP** (1 hidden layer, shallow DL)
3. **Linear** (baseline for comparison)

---

## Detailed Code Structure Design

### 1. Architecture Overview

```
fir_reconstruction_zScore_nonlinear.py
├── Forward Model Classes (abstracted)
│   ├── LinearForwardModel (baseline)
│   ├── RFForwardModel (Random Forest)
│   └── MLPForwardModel (Light MLP)
├── Common Pipeline (existing code)
│   ├── FIR fitting
│   ├── Z-score extraction
│   ├── PCA transformation
│   ├── Forward model training (model-specific)
│   └── Reconstruction & evaluation
└── Visualization (model comparison added)
```

---

### 2. Base Interface

```python
class ForwardModel:
    """Base class for forward models (PCA components → Channels)"""

    def fit(self, X_train, C_train):
        """Train forward model"""
        raise NotImplementedError

    def predict(self, X_test):
        """Predict channel responses"""
        raise NotImplementedError

    def get_name(self):
        """Return model name for logging"""
        raise NotImplementedError
```

---

### 3. Random Forest Implementation

**Key Features**:
- `sklearn.ensemble.RandomForestRegressor` + `MultiOutputRegressor`
- Input: PCA components (e.g., 20-dim)
- Output: 6 channel responses
- Hyperparameters:
  - `n_estimators`: 50~200 trees
  - `max_depth`: 3~10 (prevent overfitting)
  - `min_samples_leaf`: 2~5 (smoothness)

**Advantages**:
- **Automatic interaction learning**: Discovers PC1×PC2 combinations
- **Feature importance**: Identifies which PCs matter for each channel
- **Robust to outliers**
- **No gradient optimization** (more stable)

**Challenges**:
- **Extrapolation weakness**: Poor for novel colors outside training range
  - Mitigation: Colors are circular, so interpolation likely
- **Data efficiency**: ~40 training samples (5 runs × 8 colors)
  - Mitigation: `max_depth=3~5`, `min_samples_leaf=3`, `bootstrap=True`

**Feature Importance Analysis**:
- Which PCs are important for each channel?
- Example hypothesis: PC1 → red-green, PC2 → blue-yellow

---

### 4. Light MLP Implementation

**Architecture**:
```
Input: n_components (e.g., 20)
Hidden: 16~64 units, ReLU activation
Output: 6 channels, no activation (regression)
```

**Loss Function**:
- **MSE**: `||predicted_channels - true_channels||^2`
- **Alternative: Cosine similarity**: `loss = 1 - cosine(pred, true)`
  - Rationale: Channel pattern shape matters more than magnitude

**Regularization** (critical for small data):
- **L2 weight decay**: λ=0.01~0.1
- **Dropout**: 0.1~0.3 after hidden layer
- **Early stopping**: Based on validation loss

**Training Strategy**:
- Fit new model for each leave-one-run-out fold
- Epochs: 50~200
- Learning rate: 0.001~0.01
- Optimizer: Adam

**Advantages**:
- **Gradient-based optimization**: Continuous, smooth
- **Interpolation ability**: Better generalization to novel colors
- **Smooth output**: Activation functions induce smoothness
- **Biological plausibility**: Mimics layered brain processing

**Challenges**:
- **Hyperparameter tuning required**
- **Training instability**: Local minima with 40 samples
- **Overfitting risk**: 32-64 hidden units vs 40 samples
  - Mitigation: Start with 16-32 units, aggressive regularization, ensemble multiple inits

---

### 5. Main Pipeline Changes

**Arguments Added**:
```python
--models linear rf mlp          # Can specify multiple for comparison
--rf-n-estimators 100
--rf-max-depth 5
--rf-min-samples-leaf 3
--mlp-n-hidden 32
--mlp-learning-rate 0.001
--mlp-weight-decay 0.01
--mlp-dropout 0.2
--mlp-n-epochs 100
```

**Model Factory**:
```python
def create_forward_model(model_type, args):
    if model_type == 'linear':
        return LinearForwardModel()
    elif model_type == 'rf':
        return RFForwardModel(...)
    elif model_type == 'mlp':
        return MLPForwardModel(...)
```

**Reconstruction Loop**:
- Loop over models: `for model_type in args.models`
- For each model, run leave-one-run-out CV
- Store results: `all_model_results[model_type]`

---

### 6. Visualization Enhancements

**Model Comparison Plot**:
1. **Bar plot**: Mean error per model
2. **Boxplot**: Per-run error distribution (variability)
3. **Heatmap**: Per-color error (which colors improve?)

**Statistical Test**:
- Paired t-test between models (per-run errors)
- Significance at p < 0.05

**RF-Specific**:
- Feature importance per channel (bar plot for each of 6 channels)
- Identify top 3 PCs per channel

**MLP-Specific**:
- First layer weight heatmap (hidden units × PCA components)
- Weight distribution histogram

---

## Experimental Design

### Phase 1: Proof of Concept

**Setup** (updated to match current baseline):
- **Subject**: sub-01 or sub-02 (Non-CVD, best performing)
- **ROI**: V2 (most stable, current baseline: 6.09° zscore, 9.81° voxelSelect)
- **PCA**: 6 components (current standard)
- **Method**: zscore (baseline comparison target)
- **Target**: Beat current baseline of **6.09° ± SD** reconstruction error

**Models**:
1. **Linear (baseline)**: Current zscore method
   - Expected: ~6-20° reconstruction (based on V2 performance)
2. **RF-simple**: `n_estimators=100, max_depth=5, min_samples_leaf=3`
   - Target: <10° reconstruction (30-50% improvement)
3. **MLP-tiny**: `hidden=8-16, ReLU, L2=0.05, dropout=0.3`
   - Note: Smaller hidden units due to PCA=6 (not 20)
   - Target: <10° reconstruction with better generalization

**Metrics** (compare against baseline):
- Reconstruction error (leave-one-run-out, 6 folds)
  - Baseline: 6.09° (V2 average) to 20.19° (overall average)
- Novel color error (leave-one-color-out, 8×6)
  - Baseline: 84.88° (very challenging, room for improvement)
- Per-color error distribution (which colors improve?)

**Analysis**:
- Error boxplot comparison (Linear vs RF vs MLP)
- Paired t-test (statistical significance vs baseline)
- Feature importance (RF): Which of 6 PCs matter most?
- Weight visualization (MLP): PC interaction patterns
- **Success criterion**: Statistically significant improvement over linear baseline (p < 0.05)

---

### Phase 2: Hyperparameter Optimization

**RF Grid** (if Phase 1 shows promise):
- `max_depth`: {3, 5, 7, 10}
- `n_estimators`: {50, 100, 200}
- `min_samples_leaf`: {2, 3, 5}

**MLP Grid** (adjusted for PCA=6):
- `n_hidden`: {6, 8, 12, 16} (smaller due to 6 input features)
- `learning_rate`: {0.001, 0.005, 0.01}
- `weight_decay`: {0.01, 0.05, 0.1}
- `dropout`: {0.0, 0.2, 0.3, 0.4} (higher dropout for small data)

**Method**: Grid search with nested CV
- Outer loop: Leave-one-run-out (6 folds)
- Inner loop: 5-fold CV for hyperparameter tuning

**Additional consideration**: VoxelSelect option
- Test best models with voxelSelect (fewer voxels, less overfitting risk)
- Compare: zscore + nonlinear vs voxelSelect + nonlinear

---

### Phase 3: Novel Color Generalization

**Critical Test**: Leave-one-color-out reconstruction
- **Current baseline**: 84.88° (zscore), 91.17° (voxelSelect)
- **This is the main challenge** - very high error, near chance (90°)

**Expected Results**:
- **Linear**: ~85-91° (current baseline)
- **RF**: Target <75° (10-15% improvement)
- **MLP**: Target <70° (20%+ improvement through smooth interpolation)

**Analysis**:
- Circular distance from held-out color to nearest training color
- Interpolation vs extrapolation performance
- Per-color analysis: Which novel colors are hardest?
- **Success criterion**: Reduce error below 75° (significantly better than chance)

---

### Phase 4: Multi-ROI & Multi-Subject

**Extension** (based on current baseline data):
- **All ROIs**: V1, V2, V3, hV4
- **All subjects**: sub-01, sub-02 (Non-CVD) vs sub-03, sub-04 (CVD)

**ROI-specific expectations** (from current baseline):
- **V1**: Good with voxelSelect (14.91°), test if nonlinear helps zscore
- **V2**: Already excellent (6.09° zscore), can nonlinear improve further?
- **V3**: Moderate performance (22.88° zscore), room for improvement
- **hV4**: Worst with voxelSelect (52.81°), test if nonlinear helps

**CVD Analysis** (critical for project goal):
- **Current gap**: CVD 26.66° vs Non-CVD 13.72° (2x difference)
- **Hypothesis**: Do CVD individuals have different nonlinearity patterns?
- **Question**: Can nonlinear model reduce this gap?
- **Implication**: If yes, provides insight for filter g(x) design

**Analysis**:
- ROI × Model interaction: Is V1 linear, hV4 nonlinear?
- Subject variability: Individual-specific nonlinearities?
- CVD vs NC: Different interaction patterns in PC space?

---

## Critical Considerations

### 1. Data Scarcity Problem

**Current Data**:
- N_RUNS = 6, N_COLORS = 8
- Leave-one-run-out: **40 training samples, 8 test samples**

**This is very small for nonlinear models!**

**Mitigation Strategies**:
- ✅ Aggressive regularization
- ✅ Simple models first (RF depth=3, MLP hidden=16)
- ✅ Ensemble (multiple initializations → averaging)
- ⚠️ Data augmentation risky (color space discrete)
  - But: Gaussian noise in PCA space is possible

---

### 2. Channel Response Physical Properties

**6-channel basis function characteristics**:
- Smooth circular structure (half-wave rectified sinusoid²)
- Non-negative: All responses ≥ 0
- Energy conservation (sum constraint)

**Question**: Do nonlinear models preserve these properties?

**Solutions**:
- **Output activation**:
  - ReLU or Softplus (non-negativity)
  - Or no activation + post-processing clipping
- **Loss function**:
  - MSE + smoothness regularization
  - Or cosine similarity (shape preservation)

---

### 3. Interpretability

**RF**:
- Feature importance per channel
- Tree structure analysis
- Interaction detection (which PC pairs matter)

**MLP**:
- Weight visualization (input → hidden)
- Gradient-based attribution
- Hidden unit activation patterns

**CVD Application**:
- Compare NC vs CVD forward models
- Identify which PCs, which nonlinearities differ
- Provide hints for filter g(x) learning

---

## Additional Methods Proposed

### 1. Hyperparameter Search Automation

**Grid Search Script** (`run_hyperparameter_search.sh`):
- Nested loops over all hyperparameter combinations
- Automatic logging with timestamps
- Results aggregation script

### 2. Multi-ROI & Multi-Subject Batch Processing

**Batch Script** (`run_all_rois_subjects.sh`):
- Loop: subjects × ROIs
- Fixed hyperparameters (from Phase 2)
- Heatmap analysis: ROI × Model

### 3. Ensemble Model

**Concept**: Weighted average of Linear, RF, MLP predictions
```python
class EnsembleForwardModel(ForwardModel):
    def __init__(self, models, weights=[0.3, 0.4, 0.3]):
        self.models = models
        self.weights = weights

    def predict(self, X_test):
        predictions = [m.predict(X_test) for m in self.models]
        return sum(w * p for w, p in zip(self.weights, predictions))
```

### 4. Error Analysis Tools

**Per-color error analysis**:
- Which colors are hardest to reconstruct?
- Do different models fail on different colors?

**Channel prediction quality**:
- Correlation per channel (C_true vs C_pred)
- MSE per channel
- Overall quality metrics

### 5. Interactive Visualization

**Plotly dashboard** (optional):
- Interactive HTML with hover details
- Drill-down by run, color, model
- Exportable for presentations

### 6. SLURM Integration

**SBATCH script** (`submit_nonlinear_models.sh`):
```bash
#SBATCH --nodelist=node2
#SBATCH --time=24:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=16

python fir_reconstruction_zScore_nonlinear.py \
    --models linear rf mlp \
    --rf-max-depth 5 \
    --mlp-n-hidden 32
```

---

## Expected Outcomes

### Best Case Scenario

**RF or MLP shows significant improvement**:
- **Reconstruction**: 6.09° → <5° (20%+ improvement on V2)
- **Novel color**: 84.88° → <70° (meaningful improvement, clearly below chance)
- **CVD gap reduction**: 26.66° → closer to 13.72° (NC level)

**Implications**:
- Brain uses nonlinear color encoding in PCA space
- Validates biological hypothesis (cone → perception nonlinearity)
- Provides insights for CVD filter g(x) design
- Novel color generalization improves (most important for practical application)

### Moderate Success

**Reconstruction improves, novel color stays high**:
- **Reconstruction**: 6.09° → 4-5° (good, but not dramatic)
- **Novel color**: Still >75° (limited generalization)

**Implications**:
- Nonlinearity helps trained colors but doesn't solve generalization
- May need different approach for novel colors (e.g., better basis functions)
- Still useful for CVD analysis (within-training-set colors)

### No Improvement

**Nonlinear models ≈ Linear (within statistical noise)**:
- Possible reasons:
  1. **Data too small**: 40 training samples insufficient for nonlinear learning
  2. **Already optimal**: V2 at 6.09° may be near ceiling given noise
  3. **Linear encoding**: Brain actually uses linear combination in V2
  4. **PCA bottleneck**: 6 components already linear, nonlinearity lost upstream

**Next actions**:
- Test on other ROIs (V3, hV4 have more room for improvement)
- Try voxelSelect (fewer voxels, cleaner signal?)
- Increase PCA components (6 → 10 → 15) to preserve more nonlinearity

### Overfitting Detected

**Train error << Test error**:
- **Sign**: Reconstruction good, novel color terrible (>100°)
- **Cause**: Memorizing 8 training colors without learning structure

**Mitigation**:
- Increase regularization (weight decay, dropout)
- Reduce model complexity (MLP: 16 → 8 hidden, RF: depth 5 → 3)
- Ensemble multiple models (reduce variance)
- Use voxelSelect (cleaner features, less noise)

---

## Next Steps

### Implementation Priority (Updated)

1. **Create base classes**: `ForwardModel`, `LinearForwardModel`
2. **Implement RF**: Simplest, most robust
3. **Implement MLP**: More complex, needs careful tuning (adjusted for PCA=6)
4. **Add comparison visualizations**
5. **Test on sub-01/V2**: Proof of concept (baseline: 6.09°)
6. **Critical test**: Novel color generalization (baseline: 84.88°)
7. **Hyperparameter sweep**: Find best settings (if Phase 1 promising)
8. **Extend to all ROIs**: V1, V2, V3, hV4 (ROI-specific patterns)
9. **CVD analysis**: sub-03, sub-04 (understand nonlinearity differences)

### Questions to Answer

1. **Performance**: Do nonlinear models improve reconstruction below 6.09°?
2. **Generalization**: Do they work on novel colors?
3. **Interpretability**: What interactions do they learn?
4. **ROI differences**: Is V1 linear, hV4 nonlinear?
5. **CVD relevance**: Do CVD individuals have different nonlinearities?

---

## Key Decisions Made

1. ✅ **Focus on Option 2**: PCA components → Channels (forward model)
2. ✅ **Two nonlinear models**: RF (simple ML) + Light MLP (simple DL)
3. ✅ **Modular design**: Abstract base class for extensibility
4. ✅ **Fair comparison**: All models use same data, same evaluation
5. ✅ **Start simple**: Aggressive regularization, small models
6. ✅ **Comprehensive evaluation**: Reconstruction + novel color + per-color analysis

---

## References

- **Current code**: `fir_reconstruction_zScore.py` (lines 1199-1240 for forward model)
- **Basis**: Brouwer & Heeger (2009, J. Neurosci.) - original linear forward model
- **Extension**: Adding nonlinearity to model cone → brain perception pathway

---

## File Structure

```
colorBlind_analysis/
├── fir_reconstruction_zScore.py                   # Current linear version
├── fir_reconstruction_zScore_nonlinear.py         # New: Multi-model comparison
├── forward_models/                                # New: Model classes
│   ├── __init__.py
│   ├── base.py                                    # ForwardModel base class
│   ├── linear_model.py                            # LinearForwardModel
│   ├── rf_model.py                                # RFForwardModel
│   └── mlp_model.py                               # MLPForwardModel
├── scripts/
│   ├── run_hyperparameter_search.sh               # Grid search automation
│   ├── run_all_rois_subjects.sh                   # Batch processing
│   └── submit_nonlinear_models.sh                 # SLURM submission
└── analysis/
    ├── aggregate_hyperparameter_results.py        # Results aggregation
    └── analyze_roi_subject_results.py             # Multi-ROI analysis
```

---

---

## UPDATED: Baseline Comparison (2025-11-17)

**User feedback**: "The current baseline is PCA=6 and voxelSelect option. Update the standard based on ANALYSIS_SUMMARY_20251117.md"

### Current Baseline Performance

| Metric | zscore (baseline) | voxelSelect | Target for Nonlinear |
|--------|------------------|-------------|---------------------|
| **PCA components** | 6 | 6 | 6 (start here) |
| **Voxels** | 235.0 ± 185.9 | 41.4 ± 29.9 | Test both |
| **Classification** | 100% | 100% | Maintain 100% |
| **Reconstruction** | **20.19° ± 23.64°** | 22.81° ± 20.65° | **<15°** (25% improvement) |
| **Novel color** | **84.88° ± 25.40°** | 91.17° ± 25.38° | **<75°** (meaningful) |

### ROI-Specific Baselines (zscore)

| ROI | Voxels | Reconstruction | Novel Color | Nonlinear Target |
|-----|--------|---------------|-------------|-----------------|
| **V2** | 321.3 | **6.09°** ⭐ | 84.56° | <5° recon, <70° novel |
| V1 | 482.8 | 37.44° | 92.53° | <30° recon |
| V3 | 87.8 | 22.88° | 76.19° | <15° recon, <65° novel |
| hV4 | 48.3 | 14.34° | 86.25° | <10° recon |

### Group Comparison (Critical for CVD)

| Group | Subjects | Reconstruction | Novel Color | CVD Gap |
|-------|----------|---------------|-------------|---------|
| **Non-CVD** | sub-01, sub-02 | **13.72° ± 20.07°** | 80.05° ± 27.73° | Baseline |
| **CVD** | sub-03, sub-04 | **26.66° ± 26.45°** | 89.72° ± 23.67° | **2x worse** |

**Key Target**: Can nonlinear models reduce CVD gap from 2x to <1.5x?

### Updated Experimental Plan

**Phase 1 Target**:
- Subject: sub-01 (Non-CVD, best baseline)
- ROI: V2 (6.09° baseline, most stable)
- Beat: **6.09°** reconstruction, **84.56°** novel color
- Success: <5° reconstruction (20% improvement) OR <70° novel (meaningful)

**Critical Challenge**: Novel color error (84.88°) is near chance (90°)
- This is THE main problem to solve
- Linear model already perfect at classification
- Linear model decent at reconstruction (6-20° range)
- But generalization to novel colors fails

**Hypothesis**: Nonlinear models may learn smoother interpolation in color space, improving novel color reconstruction

---

## End of Discussion Summary

**Status**: Conceptual design complete, baseline updated to match current results
**Next Action**: Code implementation (start with ForwardModel classes)
**Timeline**:
- Phase 1 (PoC on sub-01/V2): 1-2 days
- Phase 2 (Hyperparameter if promising): 3-5 days
- Phase 3-4 (All ROIs, CVD analysis): 1 week

**Updated**: 2025-11-17 - Baseline targets adjusted based on ANALYSIS_SUMMARY_20251117.md
**User's Request**: Record this discussion for future follow-up ✅

---

## CORRECTION (2025-11-18)

**User feedback**: "baseline codes are in visualize_Edits folder, not visualize_Edits_FIXED"

### Issues Found

1. ❌ **Wrong baseline**: Used `visualize_Edits_FIXED_20251117/` instead of `visualize_Edits/`
2. ❌ **Wrong output structure**: Used `test_results_nonlinear/` instead of `derivatives/{timestamp}/...`
3. ❌ **Wrong PCA default**: Used 20 instead of 6

### Corrected Files

1. ✅ `test_nonlinear_models_CORRECTED.py` - Matches visualize_Edits baseline
2. ✅ `run_test_nonlinear_CORRECTED.sh` - Corrected SBATCH script
3. ✅ `TEST_NONLINEAR_CORRECTED_GUIDE.md` - Updated guide
4. ✅ `discussion_logs/20251118_nonlinear_correction.md` - Detailed correction log

### Key Changes

**Baseline reference**:
```
WRONG: visualize_Edits_FIXED_20251117/UNIFIED_fir_reconstruction_zScore.py
RIGHT: visualize_Edits/fir_reconstruction_zScore.py
```

**Output structure**:
```
WRONG: test_results_nonlinear/sub-01_V2/
RIGHT: derivatives/{timestamp}/sub-01/zScore_NONLINEAR/V2_universal_hrf/
```

**PCA default**:
```
WRONG: 20 components
RIGHT: 6 components (as per CLAUDE.md)
```

### Usage (Corrected)

```bash
# Upload corrected version
scp -r forward_models test_nonlinear_models_CORRECTED.py run_test_nonlinear_CORRECTED.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/

# Run
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
sbatch run_test_nonlinear_CORRECTED.sh
```

**See**: `TEST_NONLINEAR_CORRECTED_GUIDE.md` for full details

---

**Updated**: 2025-11-18 - Corrected for visualize_Edits baseline
