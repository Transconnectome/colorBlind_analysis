# Nonlinear Forward Model Testing Guide

**Created**: 2025-11-17
**Purpose**: Test Random Forest and Light MLP against Linear baseline

---

## 📁 Files Created

### 1. Forward Model Classes
- ✅ `forward_models/__init__.py`
- ✅ `forward_models/base.py` - ForwardModel base class
- ✅ `forward_models/linear_model.py` - Linear baseline (B&H 2009)
- ✅ `forward_models/rf_model.py` - Random Forest regressor
- ✅ `forward_models/mlp_model.py` - Light MLP (1 hidden layer)

### 2. Test Script
- ✅ `test_nonlinear_models.py` - Simplified comparison script (~500 lines)

### 3. Documentation
- ✅ `NONLINEAR_INTEGRATION_GUIDE.md` - Integration guide for UNIFIED version
- ✅ `TEST_NONLINEAR_GUIDE.md` - This file

---

## 🎯 Current Baseline (from ANALYSIS_SUMMARY_20251117.md)

| Metric | zscore (baseline) | Target for Nonlinear |
|--------|------------------|---------------------|
| **PCA components** | 6 | 6 |
| **Reconstruction** | 20.19° ± 23.64° | **<15°** (25% improvement) |
| **Novel color** | 84.88° ± 25.40° | **<75°** (meaningful) |

**Best ROI**: V2 (6.09° zscore)
**Best subject**: sub-01 (Non-CVD)

---

## 🚀 Quick Start

### Option 1: Local Testing (Mac/Linux)

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

# Test all models on sub-01, V2, PCA=6
python test_nonlinear_models.py \
    --subject 01 \
    --roi V2 \
    --n-components 6 \
    --models linear rf mlp
```

### Option 2: Server Testing (Recommended)

**Step 1**: Upload code to server

```bash
# From local Mac terminal
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

scp -r forward_models haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp test_nonlinear_models.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_test_nonlinear.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

**Step 2**: Run on server

```bash
# SSH to server
ssh haba6030@node2

cd /scratch/connectome/haba6030/colorBlind

# Direct run (quick test)
conda activate nilearn
python test_nonlinear_models.py --subject 01 --roi V2 --models linear rf mlp

# Or submit SBATCH job
sbatch run_test_nonlinear.sh
```

**Step 3**: Download results

```bash
# From local Mac terminal
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/test_results_nonlinear ~/Desktop/
```

---

## ⚙️ Arguments

### Data Selection
- `--subject` : Subject ID (01-04) [default: 01]
- `--roi` : ROI name (V1, V2, V3, hV4) [default: V2]
- `--n-components` : PCA components [default: 6]

### Model Selection
- `--models` : Models to test (linear, rf, mlp) [default: all three]

### Random Forest Hyperparameters
- `--rf-n-estimators` : Number of trees [default: 100]
- `--rf-max-depth` : Max tree depth [default: 5]
- `--rf-min-samples-leaf` : Min samples per leaf [default: 3]

### MLP Hyperparameters
- `--mlp-n-hidden` : Hidden units [default: 12]
- `--mlp-learning-rate` : Learning rate [default: 0.001]
- `--mlp-weight-decay` : L2 regularization [default: 0.05]
- `--mlp-dropout` : Dropout rate [default: 0.3]
- `--mlp-n-epochs` : Max epochs [default: 100]

### Output
- `--output-dir` : Output directory [default: test_results_nonlinear]

---

## 📊 Expected Outputs

```
test_results_nonlinear/
└── sub-01_V2/
    ├── summary.csv              # Mean ± Std errors per model
    ├── results.pkl              # Detailed results (Python pickle)
    └── model_comparison.png     # Bar plot + boxplot
```

### summary.csv Format
```csv
Subject,ROI,Model,N_voxels,PCA_components,Mean_error,Std_error
sub-01,V2,linear,321,6,6.09,1.23
sub-01,V2,rf,321,6,5.12,1.05
sub-01,V2,mlp,321,6,4.87,0.98
```

---

## 🧪 Test Scenarios

### Scenario 1: Quick Validation (Linear only)
```bash
python test_nonlinear_models.py \
    --subject 01 \
    --roi V2 \
    --models linear \
    --n-components 6
```
**Expected**: ~6-20° error (V2 baseline)
**Time**: ~5 minutes

### Scenario 2: RF vs Linear (Best ROI)
```bash
python test_nonlinear_models.py \
    --subject 01 \
    --roi V2 \
    --models linear rf \
    --n-components 6
```
**Expected**: RF < Linear (if nonlinearity helps)
**Time**: ~10 minutes

### Scenario 3: Full Comparison (All models)
```bash
python test_nonlinear_models.py \
    --subject 01 \
    --roi V2 \
    --models linear rf mlp \
    --n-components 6
```
**Expected**: Best model < 6° (improvement over baseline)
**Time**: ~15 minutes

### Scenario 4: Hyperparameter Tuning (RF)
```bash
# Shallower trees (prevent overfitting)
python test_nonlinear_models.py \
    --subject 01 \
    --roi V2 \
    --models rf \
    --rf-max-depth 3 \
    --rf-min-samples-leaf 5
```

### Scenario 5: Hyperparameter Tuning (MLP)
```bash
# Smaller network (prevent overfitting)
python test_nonlinear_models.py \
    --subject 01 \
    --roi V2 \
    --models mlp \
    --mlp-n-hidden 8 \
    --mlp-dropout 0.4
```

---

## 📈 Interpretation Guide

### Success Criteria

| Outcome | Mean Error | Interpretation |
|---------|------------|----------------|
| **Excellent** | <5° | Major improvement, nonlinearity matters |
| **Good** | 5-10° | Moderate improvement, promising |
| **Baseline** | 10-20° | Comparable to linear |
| **Poor** | >20° | Overfitting or poor generalization |

### Statistical Significance

The script performs **paired t-test** between models:
- **p < 0.05**: Significant difference
- **p < 0.01**: Highly significant difference
- **p ≥ 0.05**: No significant difference

### What to Look For

1. **Mean error reduction**: Is nonlinear < linear?
2. **Std error**: Is nonlinear more stable? (lower std = better)
3. **Per-run consistency**: Check boxplot for outliers
4. **Statistical significance**: p-value in t-test

---

## 🐛 Troubleshooting

### Error: "Module 'forward_models' not found"
```bash
# Make sure forward_models/ is in the same directory
ls -la forward_models/

# Or add to PYTHONPATH
export PYTHONPATH=/path/to/colorBlind_analysis:$PYTHONPATH
```

### Error: "ROI mask not found"
```bash
# Check ROI path
ls derivatives/sub-01/roi_pipeline/

# Or specify correct path in script (line ~142)
```

### Error: "Functional data not found"
```bash
# Check fMRIPrep output
ls /storage/connectome/haba6030/fmriprep_out/sub-01/func/

# Make sure VOLS_TO_DROP matches preprocessing
```

### Warning: "MLP early stopping"
- This is normal - early stopping prevents overfitting
- If stops at epoch 5-10: Try smaller network or higher dropout
- If runs full epochs: Try more epochs or lower patience

### Poor RF performance
- Try shallower trees: `--rf-max-depth 3`
- Increase min samples: `--rf-min-samples-leaf 5`
- Reduce trees: `--rf-n-estimators 50`

### Poor MLP performance
- Try smaller network: `--mlp-n-hidden 6` or `8`
- Increase dropout: `--mlp-dropout 0.4`
- Increase regularization: `--mlp-weight-decay 0.1`

---

## 🔄 Next Steps

### If Nonlinear Models Show Improvement:

1. **Test on other subjects**:
   ```bash
   for sub in 01 02 03 04; do
       python test_nonlinear_models.py --subject $sub --roi V2
   done
   ```

2. **Test on other ROIs**:
   ```bash
   for roi in V1 V2 V3 hV4; do
       python test_nonlinear_models.py --subject 01 --roi $roi
   done
   ```

3. **Hyperparameter optimization**:
   - Create grid search script
   - Find best settings per ROI

4. **Integrate into UNIFIED**:
   - Follow `NONLINEAR_INTEGRATION_GUIDE.md`
   - Add to full pipeline with all visualizations

### If No Improvement:

1. **Diagnose**:
   - Check if overfitting (train vs test error)
   - Try different PCA components (6 → 10 → 15)
   - Test on voxelSelect instead of zscore

2. **Alternative approaches**:
   - Polynomial features (Option 1 from design doc)
   - Kernel methods
   - Ensemble models

---

## 📝 Logging Results

Create a results log file:

```bash
# Run with logging
python test_nonlinear_models.py \
    --subject 01 \
    --roi V2 \
    --models linear rf mlp \
    2>&1 | tee test_log_20251117.txt
```

Results to record:
- Date/time
- Subject, ROI, PCA components
- Mean ± Std for each model
- p-values for comparisons
- Runtime
- Notes on convergence/warnings

---

## 📧 Questions?

Contact: jinilkim (refer to discussion log: `discussion_logs/20251117_nonlinear_forward_model_design.md`)
