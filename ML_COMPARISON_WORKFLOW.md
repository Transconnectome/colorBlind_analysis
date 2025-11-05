# ML/DL Forward Model Comparison Workflow

This guide shows how to compare the B&H (2009) linear forward model with ML/DL alternatives.

## Overview

The `ml_forward_model.py` implements 5 different forward encoding models:

1. **Ridge Regression** - Linear with L2 regularization (baseline)
2. **Ridge CV** - Ridge with automatic alpha selection
3. **MLP** - Multi-layer perceptron (captures nonlinearity)
4. **CNN** - 1D convolutional network (spatial structure)
5. **Attention** - Transformer-based (learns voxel importance)

---

## Quick Start (Local Testing)

If you have ROI data locally, test the models:

```bash
# Activate environment
conda activate nilearn

# Compare models for V1
python compare_forward_models.py --roi V1

# Compare specific models only
python compare_forward_models.py --roi V1 --models ridge mlp attention

# Test other ROIs
python compare_forward_models.py --roi BrainMask
```

**Output:**
- `derivatives/sub-01/{ROI}_model_comparison.pkl` - Results
- `derivatives/sub-01/{ROI}_model_comparison.png` - Visualization

---

## Server Workflow (Recommended)

### Step 1: Upload Files

```bash
# Upload ML model implementations
scp ml_forward_model.py node2:/scratch/connectome/haba6030/colorBlind/
scp compare_forward_models.py node2:/scratch/connectome/haba6030/colorBlind/

# Upload SLURM script
scp sbatch_ml_comparison.sub node2:/scratch/connectome/haba6030/colorBlind/
```

### Step 2: Submit Job

```bash
# SSH to server
ssh node2
cd /scratch/connectome/haba6030/colorBlind

# Submit comparison job
sbatch sbatch_ml_comparison.sub

# Check status
squeue -u $USER
```

**Expected runtime:** 2-4 hours for all ROIs
- Ridge models: ~5 min per ROI
- MLP/Attention: ~30 min per ROI (100 epochs each)

### Step 3: Monitor Progress

```bash
# Watch output
tail -f logs/ml_compare_XXXXXX.out

# You'll see output like:
# ========================================
# Testing ROI: V1
# ========================================
# Loaded ROI data: /scratch/.../V1_responses_perrun.npy
#   Shape: (48, 5000)
#
# CV Fold 1/6 (test run: 1)
#   Epoch 20/100, Loss: 0.0234
#   ...
```

### Step 4: Download Results

After job completes:

```bash
# Download comparison results and plots
scp node2:/scratch/connectome/haba6030/colorBlind/derivatives/sub-01/*_model_comparison.* ./derivatives/sub-01/

# Download log files
scp 'node2:/scratch/connectome/haba6030/colorBlind/logs/ml_compare_*.out' ./logs/
scp 'node2:/scratch/connectome/haba6030/colorBlind/logs/ml_compare_*.err' ./logs/
```

---

## Understanding the Results

### Metrics Reported

1. **R² Score** - How well the model reconstructs channel responses
   - Higher is better
   - Typical range: 0.3-0.7 for good models

2. **Decoding Accuracy** - Can we decode the correct color?
   - Chance level: 12.5% (1 out of 8 colors)
   - Good performance: >40%
   - Excellent performance: >60%

### Expected Performance

Based on similar studies:

| Model | Expected R² | Expected Accuracy | Training Time |
|-------|-------------|-------------------|---------------|
| Ridge | 0.30-0.45 | 35-50% | ~2 min |
| Ridge CV | 0.35-0.50 | 40-55% | ~5 min |
| MLP (Small) | 0.40-0.55 | 45-60% | ~20 min |
| MLP (Large) | 0.45-0.60 | 50-65% | ~30 min |
| CNN | 0.40-0.55 | 45-60% | ~25 min |
| Attention | 0.45-0.60 | 50-65% | ~30 min |

**If ML/DL models perform WORSE than Ridge:**
- Possible overfitting (reduce epochs, increase dropout)
- Too little training data (use simpler models)
- Hyperparameter tuning needed

**If ML/DL models perform BETTER:**
- Evidence of nonlinearity in voxel→channel mapping
- Use the best model for CVD correction filter design

---

## Analyzing Results in Python

```python
import pickle
import numpy as np
import matplotlib.pyplot as plt

# Load results
with open('derivatives/sub-01/V1_model_comparison.pkl', 'rb') as f:
    results = pickle.load(f)

# Check R² scores
for name, result in results.items():
    print(f"{name}: R² = {result['mean_r2']:.4f} ± {result['std_r2']:.4f}")

# Get predictions from best model
best_name = max(results.keys(), key=lambda n: results[n]['mean_r2'])
best_preds = results[best_name]['predictions']
true_channels = results[best_name]['ground_truth']

# Visualize predictions
plt.figure(figsize=(10, 8))
for i in range(6):  # 6 channels
    plt.subplot(2, 3, i+1)
    plt.scatter(true_channels[:, i], best_preds[:, i], alpha=0.5)
    plt.plot([0, 1], [0, 1], 'r--')
    plt.xlabel('True')
    plt.ylabel('Predicted')
    plt.title(f'Channel {i+1}')
plt.tight_layout()
plt.savefig('channel_predictions.png')
```

---

## Customizing Models

### Adjust Hyperparameters

Edit `compare_forward_models.py` to tune model settings:

```python
# More epochs for better convergence
'MLP (Large)': (MLPForwardModel, {
    'hidden_dims': [512, 256, 128],
    'epochs': 200,  # Increased from 100
    'lr': 1e-3,
    'batch_size': 16,
    'dropout': 0.3
}),

# Smaller dropout to reduce regularization
'Attention': (AttentionForwardModel, {
    'hidden_dim': 256,
    'n_heads': 8,
    'epochs': 150,
    'lr': 5e-4,  # Smaller learning rate
    'batch_size': 16
}),
```

### Add New Model Architectures

In `ml_forward_model.py`, create new model classes:

```python
class MyCustomModel(ForwardModel):
    def __init__(self, ...):
        super().__init__(n_channels)
        # Your architecture here

    def fit(self, voxels, channels):
        # Training logic
        pass

    def predict(self, voxels):
        # Prediction logic
        pass
```

Then add to comparison:

```python
models_to_test = {
    'My Model': (MyCustomModel, {'param1': value1, ...})
}
```

---

## Integration with CVD Correction Pipeline

Once you identify the best model, use it for CVD correction:

### Step 1: Train on Non-CVD Participants
```python
# Train forward model f_NC: vox_NC → CH_NC
model_nc = BestModel()
model_nc.fit(voxels_nc, channels_nc)
```

### Step 2: Analyze CVD Participants
```python
# Get voxel responses from CVD participant
voxels_cvd = load_cvd_data()

# Predict what channels they would produce
channels_cvd = model_nc.predict(voxels_cvd)

# Compare to normal channels
channels_nc_expected = ...

# Design filter g(color) to correct
filter_cvd = design_correction_filter(channels_cvd, channels_nc_expected)
```

This allows you to implement the correction function g(color) mentioned in CLAUDE.md!

---

## Troubleshooting

### PyTorch Not Available
If you see "PyTorch not available" warning:

```bash
# Install PyTorch in nilearn environment
conda activate nilearn
conda install pytorch torchvision cpuonly -c pytorch
```

### Out of Memory Errors
Reduce batch size or model size:

```python
'MLP': (MLPForwardModel, {
    'hidden_dims': [128, 64],  # Smaller layers
    'batch_size': 8,  # Smaller batches
})
```

### Poor Performance
1. Check data quality first (run diagnostic_analysis.py)
2. Try voxel selection (use top-k voxels)
3. Increase regularization (higher dropout)
4. Use simpler models (Ridge might be best!)

---

## Next Steps

1. **Run diagnostic analysis first** to ensure data quality
2. **Compare models** to find best architecture
3. **Use best model** for Step 1 in CLAUDE.md (color reconstruction)
4. **Design CVD correction filter** using the forward model
5. **Validate** on held-out CVD participants
