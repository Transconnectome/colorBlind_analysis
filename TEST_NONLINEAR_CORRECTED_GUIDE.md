# Nonlinear Forward Model Testing Guide (CORRECTED)

**Created**: 2025-11-18
**Purpose**: Test nonlinear forward models based on **visualize_Edits** baseline (CORRECTED)

---

## ⚠️ Correction Notice

**Previous version** incorrectly used `visualize_Edits_FIXED_20251117/` as baseline.
**Corrected version** now uses `visualize_Edits/` as baseline (as per user feedback).

### Key Changes

| Aspect | Previous (WRONG) | Corrected (RIGHT) |
|--------|------------------|-------------------|
| **Baseline folder** | visualize_Edits_FIXED_20251117/ | **visualize_Edits/** |
| **Baseline file** | UNIFIED_fir_reconstruction_zScore.py | **fir_reconstruction_zScore.py** |
| **Output structure** | test_results_nonlinear/ | **derivatives/{timestamp}/sub-{ID}/zScore_NONLINEAR/{ROI}_universal_hrf/** |
| **Default PCA** | 20 | **6** (as per CLAUDE.md) |
| **Script name** | test_nonlinear_models.py | **test_nonlinear_models_CORRECTED.py** |

---

## 📁 Files (CORRECTED)

### 1. Forward Model Classes (unchanged)
- ✅ `forward_models/__init__.py`
- ✅ `forward_models/base.py`
- ✅ `forward_models/linear_model.py`
- ✅ `forward_models/rf_model.py`
- ✅ `forward_models/mlp_model.py`

### 2. Test Script (CORRECTED)
- ✅ `test_nonlinear_models_CORRECTED.py` - Matches visualize_Edits baseline

### 3. SBATCH Script (CORRECTED)
- ✅ `run_test_nonlinear_CORRECTED.sh` - Updated for correct output structure

### 4. Documentation
- ✅ `TEST_NONLINEAR_CORRECTED_GUIDE.md` - This file
- ⚠️ `TEST_NONLINEAR_GUIDE.md` - Previous version (DEPRECATED)

---

## 🎯 Current Baseline

**Reference**:
- Code: `visualize_Edits/fir_reconstruction_zScore.py`
- Analysis: `ANALYSIS_SUMMARY_20251117.md`
- Guidelines: `CLAUDE.md` (updated)

**Performance**:

| Metric | zscore (baseline) | Target (Nonlinear) |
|--------|------------------|-------------------|
| **PCA** | 6 | 6 |
| **Reconstruction** | 20.19° ± 23.64° | **<15°** |
| **V2 (best)** | 6.09° | **<5°** |
| **Novel color** | 84.88° ± 25.40° | **<75°** |

---

## 🚀 Usage

### Option 1: Local Testing

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

python test_nonlinear_models_CORRECTED.py \
    --subject 01 \
    --roi V2 \
    --n-components 6 \
    --models linear rf mlp
```

### Option 2: Server Testing (Recommended) ⭐

**Step 1**: Upload to server

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis

scp -r forward_models haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp test_nonlinear_models_CORRECTED.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/
scp run_test_nonlinear_CORRECTED.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/
```

**Step 2**: Run on server

```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind

# Direct run
conda activate nilearn
python test_nonlinear_models_CORRECTED.py --subject 01 --roi V2 --models linear rf mlp

# Or submit SBATCH
sbatch run_test_nonlinear_CORRECTED.sh
```

**Step 3**: Download results

```bash
# Find the timestamp directory (e.g., 20251118_143022)
# From local Mac terminal
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/derivatives/20251118_*/ ~/Desktop/
```

---

## 📊 Output Structure (CORRECTED)

```
derivatives/
└── {timestamp}/                   # e.g., 20251118_143022
    └── sub-01/
        └── zScore_NONLINEAR/
            └── V2_universal_hrf/
                ├── summary.csv              # Model comparison table
                ├── results.pkl              # Detailed results
                └── model_comparison.png     # Visualization
```

**IMPORTANT**: Output is now in `derivatives/` folder (matching visualize_Edits structure), NOT `test_results_nonlinear/`

### summary.csv Format

```csv
Subject,ROI,Model,N_voxels,PCA_components,Optimal_delay_TRs,Mean_error,Std_error
sub-01,V2,linear,321,6,3,6.09,1.23
sub-01,V2,rf,321,6,3,5.12,1.05
sub-01,V2,mlp,321,6,3,4.87,0.98
```

---

## ⚙️ Arguments

### Data Selection
- `--subject` : Subject ID (01-04 for test, P01 for pilot) [default: 01]
- `--roi` : ROI name (V1, V2, V3, hV4) [default: V2]
- `--n-components` : PCA components [default: 6]

### Model Selection
- `--models` : Models to test (linear, rf, mlp) [default: all three]

### RF Hyperparameters
- `--rf-n-estimators` : Number of trees [default: 100]
- `--rf-max-depth` : Max tree depth [default: 5]
- `--rf-min-samples-leaf` : Min samples per leaf [default: 3]

### MLP Hyperparameters
- `--mlp-n-hidden` : Hidden units [default: 12, adjusted for PCA=6]
- `--mlp-learning-rate` : Learning rate [default: 0.001]
- `--mlp-weight-decay` : L2 regularization [default: 0.05]
- `--mlp-dropout` : Dropout rate [default: 0.3]
- `--mlp-n-epochs` : Max epochs [default: 100]

### Output
- `--timestamp` : Timestamp for output directory [default: auto-generated]

---

## 🧪 Test Scenarios

### Scenario 1: Quick Validation (Linear only)
```bash
python test_nonlinear_models_CORRECTED.py \
    --subject 01 \
    --roi V2 \
    --models linear \
    --n-components 6
```
**Expected**: ~6-20° (V2 baseline)

### Scenario 2: Full Comparison
```bash
python test_nonlinear_models_CORRECTED.py \
    --subject 01 \
    --roi V2 \
    --models linear rf mlp \
    --n-components 6
```
**Expected**: RF or MLP < Linear (if nonlinearity helps)

### Scenario 3: Different ROI
```bash
python test_nonlinear_models_CORRECTED.py \
    --subject 01 \
    --roi V3 \
    --models linear rf mlp \
    --n-components 6
```
**Baseline**: V3 22.88° (more room for improvement than V2)

### Scenario 4: CVD Subject
```bash
python test_nonlinear_models_CORRECTED.py \
    --subject 03 \
    --roi V2 \
    --models linear rf mlp \
    --n-components 6
```
**Baseline**: CVD 26.66° (2x worse than Non-CVD 13.72°)

---

## 📈 Interpretation

### Success Criteria

| Outcome | Mean Error | Interpretation |
|---------|------------|----------------|
| **Excellent** | <5° | Major improvement |
| **Good** | 5-10° | Moderate improvement |
| **Baseline** | 10-20° | Comparable to linear |
| **Poor** | >20° | Overfitting |

### Statistical Test

- **p < 0.05**: Significant difference
- **p < 0.01**: Highly significant
- **p ≥ 0.05**: No significant difference

---

## 🔍 Key Differences from Previous Version

### 1. **Baseline Reference**

**Previous**:
```python
# Incorrectly referenced UNIFIED version
baseline_file = "visualize_Edits_FIXED_20251117/UNIFIED_fir_reconstruction_zScore.py"
```

**Corrected**:
```python
# Correct baseline
baseline_file = "visualize_Edits/fir_reconstruction_zScore.py"
```

### 2. **Output Directory**

**Previous**:
```python
output_dir = Path(f"test_results_nonlinear/sub-{args.subject}_{args.roi}")
```

**Corrected**:
```python
# Matching visualize_Edits structure
output_dir = Path(f"derivatives/{timestamp}/sub-{args.subject}/zScore_NONLINEAR/{args.roi}_universal_hrf")
```

### 3. **Color Mapping**

**Previous**: Used TEST colors for all subjects

**Corrected**: Properly distinguishes pilot vs test
```python
if args.subject == 'P01':
    LABEL2HUE_DEG = LABEL2HUE_DEG_PILOT  # Irregular spacing
else:
    LABEL2HUE_DEG = LABEL2HUE_DEG_TEST  # Regular 45° spacing
```

### 4. **ROI Path**

**Previous**: Single path format

**Corrected**: Pilot vs test distinction
```python
if args.subject == 'P01':
    roi_path = f"derivatives/pilot/sub-01/roi_pipeline/{args.roi}_mask..."
else:
    roi_path = f"derivatives/sub-{args.subject}/roi_pipeline/{args.roi}_mask..."
```

---

## 🐛 Troubleshooting

### Error: "ROI mask not found"
```bash
# Check correct path
ls derivatives/sub-01/roi_pipeline/

# NOT:
ls derivatives/pilot/sub-01/roi_pipeline/  # Only for P01
```

### Error: "Output directory permission denied"
```bash
# Make sure derivatives/ folder exists
mkdir -p derivatives
```

### Results not matching baseline
- Check you're using `test_nonlinear_models_CORRECTED.py` (not old version)
- Verify PCA=6 (not 20)
- Confirm correct subject ID format (01, not sub-01 in argument)

---

## 🔄 Next Steps

### If Results Show Improvement:

1. **Test on all subjects**:
   ```bash
   for sub in 01 02 03 04; do
       python test_nonlinear_models_CORRECTED.py --subject $sub --roi V2
   done
   ```

2. **Test on all ROIs**:
   ```bash
   for roi in V1 V2 V3 hV4; do
       python test_nonlinear_models_CORRECTED.py --subject 01 --roi $roi
   done
   ```

3. **Full integration**: Modify `visualize_Edits/fir_reconstruction_zScore.py` directly

### If No Improvement:

1. **Diagnose**: Overfitting? PCA bottleneck?
2. **Try**: Different PCA components (6 → 10 → 15)
3. **Test**: voxelSelect method instead of zscore

---

## 📝 Summary of Corrections

✅ **Corrected baseline**: visualize_Edits (not _FIXED)
✅ **Corrected output structure**: derivatives/{timestamp}/...
✅ **Corrected PCA default**: 6 (not 20)
✅ **Corrected pilot/test distinction**
✅ **Corrected ROI paths**

---

## 📚 References

- **Baseline code**: `visualize_Edits/fir_reconstruction_zScore.py`
- **Guidelines**: `CLAUDE.md` (updated)
- **Analysis**: `ANALYSIS_SUMMARY_20251117.md`
- **Discussion**: `discussion_logs/20251117_nonlinear_forward_model_design.md`

---

**Updated**: 2025-11-18 (corrected for visualize_Edits baseline)
