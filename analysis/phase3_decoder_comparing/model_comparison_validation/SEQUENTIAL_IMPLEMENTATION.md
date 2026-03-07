# Sequential Training Implementation — LOCO Decoder Comparison

## Summary

Implemented sequential/incremental learning models based on the insight that "하나의 MLP가 뇌의 구조를 모방하도록 학습하게끔 이를 지속적으로 업데이트" (one model should continuously update to mimic brain structure).

## Key Changes from Ensemble Approach

### Previous (Ensemble)
- **FE_Ensemble**: 6 independent W matrices → circular mean of 6 predictions
- **HybridMLP_Ensemble**: 6 independent MLPs → circular mean
- **HybridSVR_Ensemble**: 6 independent SVRs → circular mean

### New (Sequential)
- **FE_Sequential**: One W matrix trained incrementally (run1 → run1+2 → ... → all 6 runs)
- **HybridMLP_Sequential**: FE (pooled) → MLP with `warm_start=True` (run1 → run2 → ... → run6)
- **HybridSVR_Sequential**: FE (pooled) → SVR with incremental accumulation (run1 → run1+2 → ... → all runs)

## Biological Motivation

- **Ensemble**: Multiple independent models averaging predictions (artificial)
- **Sequential**: One model continuously updating as new data arrives (brain-like plasticity)

Sequential learning better mimics how the brain might adapt representations over time while maintaining stable encoding structure (FE) and updating readout (MLP/SVR).

## Implementation Details

### 1. Circular MSE Loss (added to run_loco_comparison.py)

```python
def circular_distance(y_true, y_pred):
    """Circular distance in degrees (0-180°)"""
    diff = np.abs(y_true - y_pred)
    return np.minimum(diff, 360 - diff)

def circular_mse(y_true, y_pred):
    """Circular mean squared error"""
    return np.mean(circular_distance(y_true, y_pred) ** 2)
```

### 2. ForwardEncodingSequential

- **Training**: Incremental data accumulation
  - Iteration 1: Fit W with run1 (7 samples)
  - Iteration 2: Fit W with run1+2 (14 samples)
  - ...
  - Iteration 6: Fit W with all runs (42 samples)
- **Final W**: Identical to pooled training (42 samples)
- **Learning process**: Sequential (mimics continuous updates)

### 3. HybridMLPSequential

- **Stage 1**: ForwardEncoding with pooled data (42 samples) → W matrix
- **Stage 2**: MLP with `warm_start=True`
  - Fit on run1 (7 samples)
  - Continue fit on run2 (7 samples) with existing weights
  - ...
  - Continue fit on run6 (7 samples) with existing weights
- **Target**: 6-channel basis function values (continuous hue representation)
- **Prediction**: Channel responses → template matching → hue (0-359°)

### 4. HybridSVRSequential

- **Stage 1**: ForwardEncoding with pooled data (42 samples) → W matrix
- **Stage 2**: SVR incremental accumulation (no `warm_start` available)
  - Fit on run1 (7 samples)
  - Refit on run1+2 (14 samples)
  - ...
  - Refit on all runs (42 samples)
- **Note**: SVR doesn't support `warm_start`, so we use incremental data accumulation

## Files Modified

### run_loco_comparison.py
- Added `circular_distance()` and `circular_mse()` utility functions
- Added `ForwardEncodingSequential` class (lines ~720-780)
- Added `HybridMLPSequential` class (lines ~780-860)
- Added `HybridSVRSequential` class (lines ~860-940)
- Added models to `model_map` (lines ~1485)

### utils.py
- Added `FE_Sequential` to `get_model_architecture()` (lines ~425)
- Added `HybridMLP_Sequential` to `get_model_architecture()` (lines ~430)
- Added `HybridSVR_Sequential` to `get_model_architecture()` (lines ~435)
- Added defaults to `get_model_defaults()` (lines ~525-540)

### New Files Created
- `test_sequential_local.py` — Local validation test
- `run_sequential_loco_raw.sbatch` — LOCO raw alignment
- `run_sequential_loco_procrustes.sbatch` — LOCO procrustes alignment
- `run_sequential_loco_srm.sbatch` — LOCO SRM alignment
- `submit_sequential_loco.sh` — Submission wrapper

## Default Hyperparameters

| Model | Parameters |
|-------|------------|
| FE_Sequential | alpha=0, n_channels=6 |
| HybridMLP_Sequential | fe_alpha=0, n_channels=6, hidden_layer_sizes=(64, 32), mlp_alpha=0.1 |
| HybridSVR_Sequential | fe_alpha=0, n_channels=6, C=1.0, epsilon=0.1 |

## Output Structure

```
results/loco_sequential/
├── raw/          sub-{01..10}_loco.json
├── procrustes/   sub-{01..10}_loco.json
└── srm/          sub-{01..10}_loco.json
```

Each JSON contains per-ROI (V1, V2, V3, V4) results for 3 models:
- FE_Sequential
- HybridMLP_Sequential
- HybridSVR_Sequential

## Local Test Results (sub-01 V1 procrustes, held-out color 0°)

| Model | MAE (°) | MSE (°²) |
|-------|---------|----------|
| ForwardEncodingSequential | 90.2 | 11419.2 |
| HybridMLPSequential | 49.0 | 2401.0 |
| HybridSVRSequential | 133.0 | 18265.0 |

✓ All models can fit and predict correctly.

## Server Execution

### 1. Upload files to server

```bash
# Upload modified Python files
scp analysis/phase3_decoder_comparing/model_comparison_validation/scripts/run_loco_comparison.py \
    analysis/phase3_decoder_comparing/model_comparison_validation/scripts/utils.py \
    haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/phase3_decoder_comparing/model_comparison_validation/scripts/

# Upload sbatch files
scp analysis/phase3_decoder_comparing/model_comparison_validation/scripts/run_sequential_loco_*.sbatch \
    analysis/phase3_decoder_comparing/model_comparison_validation/scripts/submit_sequential_loco.sh \
    haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/phase3_decoder_comparing/model_comparison_validation/scripts/
```

### 2. Submit jobs on server

```bash
ssh haba6030@node3
cd /scratch/connectome/haba6030/colorBlind/analysis/phase3_decoder_comparing/model_comparison_validation
bash scripts/submit_sequential_loco.sh
```

### 3. Monitor jobs

```bash
squeue -u haba6030
# Check logs: logs/seq_loco_{raw,proc,srm}_*.out
```

### 4. Download results

```bash
# On local machine
scp -r haba6030@node3:/scratch/connectome/haba6030/colorBlind/analysis/phase3_decoder_comparing/model_comparison_validation/results/loco_sequential/ \
    analysis/phase3_decoder_comparing/results/
```

## Expected Runtime

- **Per task**: ~10-30 minutes (3 models × 4 ROIs × 1 subject)
- **Total**: 30 tasks (3 alignments × 10 subjects) ≈ 2-5 hours on node2

## Next Steps

1. Run sequential LOCO (3 alignments × 10 subjects)
2. Compare Sequential vs Ensemble results
3. Analyze whether sequential training improves interpolation
4. Update METHODS_RESULTS_SUMMARY_FOR_PAPER.md with findings

## Key Question to Answer

**Does sequential/incremental learning (one model, continuous updates) outperform ensemble learning (multiple independent models, averaged predictions) for color hue interpolation?**

This tests whether brain-like continuous plasticity provides better generalization than artificial ensemble averaging.
