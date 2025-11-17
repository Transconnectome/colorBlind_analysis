# Nonlinear Forward Model Integration Guide

**Date**: 2025-11-17
**Purpose**: Add Random Forest and Light MLP support to UNIFIED_fir_reconstruction_zScore.py

---

## Files Created

### 1. Forward Model Classes (`forward_models/`)
- ✅ `__init__.py` - Module initialization
- ✅ `base.py` - ForwardModel base class
- ✅ `linear_model.py` - LinearForwardModel (baseline)
- ✅ `rf_model.py` - RFForwardModel (Random Forest)
- ✅ `mlp_model.py` - MLPForwardModel (Light MLP)

### 2. Main Script
- 🔄 `UNIFIED_fir_reconstruction_zScore_NONLINEAR.py` (to be completed)

---

## Integration Steps

### Step 1: Add Imports (After line 54)

```python
# Import forward models
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))  # Add parent dir to path
from forward_models import LinearForwardModel, RFForwardModel, MLPForwardModel
```

### Step 2: Extend Argument Parsing (After line 191)

```python
def parse_args():
    parser = argparse.ArgumentParser(description='FIR-based color reconstruction (NONLINEAR)')

    # Existing arguments
    parser.add_argument('--subject', type=str, default='01')
    parser.add_argument('--roi', type=str, default='V2')
    parser.add_argument('--use-pca', action='store_true')
    parser.add_argument('--n-components', type=int, default=6)  # Changed default to 6
    parser.add_argument('--timestamp', type=str, default=None)

    # NEW: Model selection
    parser.add_argument('--models', type=str, nargs='+',
                        default=['linear'],
                        choices=['linear', 'rf', 'mlp'],
                        help='Forward models to compare (can specify multiple)')

    # NEW: RF hyperparameters
    parser.add_argument('--rf-n-estimators', type=int, default=100)
    parser.add_argument('--rf-max-depth', type=int, default=5)
    parser.add_argument('--rf-min-samples-leaf', type=int, default=3)

    # NEW: MLP hyperparameters
    parser.add_argument('--mlp-n-hidden', type=int, default=12)  # Small for PCA=6
    parser.add_argument('--mlp-learning-rate', type=float, default=0.001)
    parser.add_argument('--mlp-weight-decay', type=float, default=0.05)
    parser.add_argument('--mlp-dropout', type=float, default=0.3)
    parser.add_argument('--mlp-n-epochs', type=int, default=100)

    return parser.parse_args()
```

### Step 3: Model Factory Function (After parse_args)

```python
def create_forward_model(model_type, args):
    """Factory function to create forward model"""

    if model_type == 'linear':
        return LinearForwardModel()

    elif model_type == 'rf':
        return RFForwardModel(
            n_estimators=args.rf_n_estimators,
            max_depth=args.rf_max_depth,
            min_samples_leaf=args.rf_min_samples_leaf
        )

    elif model_type == 'mlp':
        return MLPForwardModel(
            n_hidden=args.mlp_n_hidden,
            learning_rate=args.mlp_learning_rate,
            weight_decay=args.mlp_weight_decay,
            dropout=args.mlp_dropout,
            n_epochs=args.mlp_n_epochs,
            verbose=False
        )

    else:
        raise ValueError(f"Unknown model type: {model_type}")
```

### Step 4: Replace Forward Model Section (Lines 737-752)

**OLD CODE** (remove):
```python
# Train forward model: B = W × C
C_train = []
for color_idx in y_train:
    color_name = f'color_{color_idx+1}'
    hue_deg = LABEL2HUE_DEG[color_name]
    channels = hue_to_channels(hue_deg)
    C_train.append(channels)
C_train = np.array(C_train).T  # (6, n_train)

# Estimate weights: W = B × C^T × (C × C^T)^-1
W = X_train_final.T @ C_train.T @ np.linalg.inv(C_train @ C_train.T)

# Test: estimate channels from test data
C_test_est = np.linalg.pinv(W.T @ W) @ W.T @ X_test_final.T  # (6, n_test)
```

**NEW CODE** (replace):
```python
# Get channel outputs for training colors
C_train = []
for color_idx in y_train:
    color_name = f'color_{color_idx+1}'
    hue_deg = LABEL2HUE_DEG[color_name]
    channels = hue_to_channels(hue_deg)
    C_train.append(channels)
C_train = np.array(C_train).T  # (6, n_train)

# === KEY CHANGE: Use forward model class ===
forward_model = create_forward_model(current_model_type, args)
forward_model.fit(X_train_final, C_train)
C_test_est = forward_model.predict(X_test_final)
```

### Step 5: Wrap Reconstruction in Model Loop

**Find the reconstruction loop** (line ~711):
```python
reconstruction_results = []

for test_run in range(N_RUNS):
    ...
```

**Wrap it**:
```python
# Store results for all models
all_model_results = {}

for model_type in args.models:
    print(f"\n{'='*70}")
    print(f"Running reconstruction with {model_type.upper()} forward model")
    print(f"{'='*70}\n")

    current_model_type = model_type  # Make accessible in inner loop
    reconstruction_results = []

    for test_run in range(N_RUNS):
        # ... existing code ...

        # Use forward_model as shown in Step 4
        forward_model = create_forward_model(current_model_type, args)
        forward_model.fit(X_train_final, C_train)
        C_test_est = forward_model.predict(X_test_final)

        # ... rest of code ...

    # Store results
    all_model_results[model_type] = {
        'mean_error': np.mean([r['mean_error'] for r in reconstruction_results]),
        'per_run': reconstruction_results
    }
```

---

## Simplified Approach

Due to file complexity, I recommend creating a **minimal nonlinear script** that focuses on core functionality:

1. **Quick test script**: Test forward models in isolation
2. **Full integration**: After validation, integrate into UNIFIED

---

## Next: Create Minimal Test Script

Instead of modifying the full 1283-line file, let's create a standalone test script first.

Would you like me to:
1. ✅ Create `test_forward_models.py` (standalone model comparison)
2. 🔄 Create simplified `NONLINEAR_reconstruction.py` (300-400 lines)
3. ⏸️ Full UNIFIED integration (later, after validation)

**Recommendation**: Start with option 2 (simplified script) for faster iteration.
