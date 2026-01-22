# Phase 0: Preprocessing & ROI Extraction

**Status**: Completed ✅
**Scripts**: 2 files

---

## Overview

This phase handles fMRI data preprocessing and region-of-interest (ROI) extraction using the forward encoding model framework from Brouwer & Heeger (2009).

## Key Scripts

### 1. `fir_reconstruction_BH2009_system_clean.py`

**Purpose**: Main preprocessing and forward encoding model pipeline

**Features**:
- FIR (Finite Impulse Response) basis GLM for trial-wise beta estimation
- ROI extraction using Wang et al. (2015) probabilistic atlas
- Forward encoding with color-selective channels
- Leave-one-run-out cross-validation
- Color reconstruction and classification

**Input**:
- fMRIPrep preprocessed BOLD data (`/storage/connectome/haba6030/fmriprep_out_method3_header_mi/`)
- Event files (stimulus timings)
- Probabilistic atlas (V1, V2, V3, hV4)

**Output**:
- Beta maps (trial-wise voxel activations)
- Channel weights (W matrix)
- Classification accuracy
- Reconstruction error
- ROI masks

**Usage**:
```bash
python fir_reconstruction_BH2009_system_clean.py \
    --subject 02 \
    --roi V1 \
    --dataset method3_header_mi
```

**Baseline Decoding Settings (Baseline32)**
**Current Standard Configuration:**
```python
# Baseline32 configuration (determined via systematic review)
Smoothing:      0mm (no smoothing)
High-pass:      0.01 Hz
Motion:         cosine (6 cosine basis functions)
CompCor:        None
Drift:          none (handled by high-pass)
Standardize:    False (preserve raw beta values)
```

**FIR GLM Parameters:**
```python
N_DELAYS = 8                    # 8 FIR delays (12s window at TR=1.5s)
VOXEL_SELECTION = 'top50'       # Top 50% voxels by FIR R²
HRF_MODEL = 'fir + derivative'  # 2nd-level GLM with HRF + temporal derivative
```

**Forward Encoding Model:**
```python
N_CHANNELS = 6                  # 6 half-wave rectified basis functions
CHANNEL_CENTERS = [0°, 60°, 120°, 180°, 240°, 300°]  # Equally spaced in hue space
CHANNEL_WIDTH = 60°             # FWHM of Gaussian basis functions
CROSS_VALIDATION = 'LORO'       # Leave-One-Run-Out
CROSS_VALIDATION = 'LOCO'       # Leave-One-Color-Out
```

### 2. `grid_search_preprocessing.py` : NOT USED - ALREADY DONE

**Purpose**: Systematic evaluation of preprocessing configurations

**Features**:
- Grid search over 144 configurations (3×2×3×2×2×2)
- Cross-subject consistency analysis
- Optimal configuration selection

**Evaluated Parameters**:
- Smoothing FWHM: {0, 3, 6} mm
- High-pass filtering: {True, False}
- Motion regressors: {None, basic6, full24}
- CompCor: {True, False}
- Drift terms: {0, 2}
- Standardization: {True, False}

**Recommended Configuration** (from systematic analysis):
- Smoothing: 6mm FWHM
- High-pass: Yes (128s)
- Motion: 6 basic parameters
- CompCor: No
- Drift: 0 (trend removed by high-pass)
- Standardization: Yes (trial-wise)

---

## Methods

### GLM Design

**FIR Basis Functions**:
- 7 time points (0-14s post-stimulus)
- Captures full hemodynamic response
- No assumption about HRF shape

**Confound Regression**:
- Motion parameters (6 or 24)
- CompCor components (optional)
- Polynomial drift terms

### Forward Encoding Model

**Channel Response Functions**:
```python
# 8 color-selective channels (half-wave rectified)
def channel_response(color_angle, channel_center):
    angle_diff = circular_distance(color_angle, channel_center)
    response = max(0, cos(angle_diff))^7  # Raised cosine (exponent=7)
    return response
```

**Training**:
```
C = channel_response_matrix  # (n_trials, n_channels)
B = beta_matrix              # (n_trials, n_voxels)
W = (C^T C)^-1 C^T B        # Weight matrix (n_channels, n_voxels)
```

**Testing**:
```
C_test = test_channel_matrix
B_predicted = C_test @ W
decoded_color = argmax(correlation(B_predicted, B_test))
```

---

## Quality Control

**Metrics**:
- Classification accuracy (chance: 12.5%)
- Reconstruction error (chance: 90°)
- Cross-run stability
- Voxel count per ROI

**Typical Results**:
- HC participants: 60-80% accuracy, 25-40° error
- CVD participants: 55-75% accuracy, 30-50° error

---

## Output Structure

```
derivatives/BH2009_{dataset}/{timestamp}/
└── sm{smooth}_hpYe_mo{motion}_cc{compcor}_dr{drift}_st{stand}_sub-{ID}_{roi}_{extra}/
    ├── amplitudes.npy           # Channel weights (n_runs, n_colors, n_channels)
    ├── amplitudes_z.npy         # Z-scored channel weights
    ├── classification_results.txt
    ├── reconstruction_error.txt
    ├── channel_weights.npy      # W matrix (n_channels, n_voxels)
    ├── roi_mask.nii.gz
    └── figures/
        ├── channel_tuning.png
        └── reconstruction_wheel.png
```

---

## References

- **Brouwer, G. J., & Heeger, D. J. (2009).** Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.
- **Wang, L., et al. (2015).** Probabilistic maps of visual topography in human cortex. *Cerebral Cortex*, 25(10), 3911-3931.
