# CVD Color Filter Application Method

**목적**: Phase 2A에서 학습한 linear filter (A, b)를 사용하여 CVD가 보는 색을 HC-like로 변환

**Pipeline**: CVD Raw Voxels → Filter → Filtered Voxels → W Matrix → Channels → RGB

---

## 전체 Pipeline

### Step 1: CVD Neural Pattern 측정

**Input**: Original RGB color stimulus (8 colors)

**fMRI Measurement**:
```python
# CVD subject가 original RGB를 볼 때 측정된 voxel pattern
CVD_raw = load_cvd_pattern(subject='08', roi='V1')
# Shape: (n_colors, n_voxels)
# Example: (8, 356) for baseline32 V1
```

**Data source**:
```python
derivatives/BH2009_deoblique_v2/baseline32_deob_determin/
└── sm*_sub-08_V1_*/
    └── amplitudes_z.npy  # (6 runs, 8 colors, 356 voxels)

# Average across runs
CVD_raw = np.mean(amplitudes_z, axis=0)  # (8, 356)
```

---

### Step 2: Apply Linear Filter (A, b)

**Filter 로드**:
```python
# Phase 2A에서 학습한 filter
filter_path = 'results/phase2/rdm_guided/baseline32_deob_determin/V1/sub-08/'
A = np.load(filter_path + 'A.npy')  # (356, 356)
b = np.load(filter_path + 'b.npy')  # (356,)
```

**Filter 적용**:
```python
# Linear transformation: X_filtered = X_raw @ A + b
X_filtered = CVD_raw @ A + b  # (8, 356)
```

**의미**:
- `A`: Voxel-to-voxel transformation matrix
  - CVD voxel space → HC-like voxel space
  - RDM loss로 학습 (CVD RDM → HC target RDM)
- `b`: Bias term (mean shift)
- `X_filtered`: Pseudo-aligned voxel pattern (HC space에 근사)

**공간 호환성**:
```
CVD raw space     →  [A, b]  →  Pseudo-HC space
(measured data)                  (RDM-aligned)
                                       ↓
                                  [W matrix]
                                       ↓
                                  Channels (6D)
```

Phase 2A의 RDM loss는 Procrustes alignment와 유사한 효과:
- Procrustes: 좌표계 회전/크기 조정으로 HC reference에 맞춤
- RDM loss: Color discriminability structure를 HC target에 맞춤
- 둘 다 "HC-like structure" 유도 → W matrix 호환 가능

---

### Step 3: W Matrix 적용 (Voxels → Channels)

**W Matrix 로드**:
```python
# Procrustes-based HC common W
W_path = 'results/group_level/procrustes_reconstruction/V1/'
model = pickle.load(open(W_path + 'procrustes_model.pkl', 'rb'))
W = model['W_common']  # (356, 6) for baseline32
```

**Channel estimation**:
```python
# Forward encoding: X = W @ C
# Inverse: C = (W^T W)^-1 W^T X^T

C_estimated = np.linalg.pinv(W.T @ W) @ W.T @ X_filtered.T
# C_estimated: (6 channels, 8 colors)
C_estimated = C_estimated.T  # (8, 6)
```

**6-channel color basis**:
```python
# Brouwer & Heeger (2009) basis functions
# 6 half-wave rectified sinusoids in CIELAB a*b* space

def create_basis_functions(n_channels=6):
    """
    Create 6-channel color basis functions
    Each channel: half-wave rectified sinusoid
    """
    hues = np.arange(0, 360, 1)  # 0-360 degrees
    basis = np.zeros((360, n_channels))

    for i in range(n_channels):
        preferred_hue = i * 60  # 0, 60, 120, 180, 240, 300
        for h_idx, hue in enumerate(hues):
            response = np.cos(np.deg2rad(hue - preferred_hue))
            basis[h_idx, i] = np.maximum(response, 0)  # Half-wave rectify

    return basis
```

---

### Step 4: Channels → Hue Reconstruction

**Method A: Template matching (현재 사용)**
```python
# Create basis templates
basis = create_basis_functions(6)  # (360, 6)

# For each color, find best matching hue
reconstructed_hues = []
for color_idx in range(8):
    channels = C_estimated[color_idx, :]  # (6,)

    # Correlation with all hue templates
    correlations = []
    for hue in range(360):
        template = basis[hue, :]  # (6,)
        corr = np.corrcoef(channels, template)[0, 1]
        correlations.append(corr)

    # Best matching hue
    best_hue = np.argmax(correlations)
    reconstructed_hues.append(best_hue)

reconstructed_hues = np.array(reconstructed_hues)  # (8,)
```

**Method B: Pseudo-inverse (alternative)**
```python
# Linear approximation
basis = create_basis_functions(6)  # (360, 6)
basis_pinv = np.linalg.pinv(basis.T)  # (6, 360)

# Channels → hue weights
hue_weights = C_estimated @ basis_pinv  # (8, 360)

# Most likely hue for each color
reconstructed_hues = np.argmax(hue_weights, axis=1)  # (8,)
```

---

### Step 5: Hue → RGB Conversion

**CIELAB conversion**:
```python
from skimage import color

def hue_to_rgb(hue_deg, L=70, chroma=50):
    """
    Convert hue (degrees) to RGB

    Parameters:
    - hue_deg: Hue in degrees [0, 360]
    - L: Lightness (fixed at 70, matching original stimulus)
    - chroma: Chroma radius (fixed at 50)

    Returns:
    - rgb: RGB values [0, 1]
    """
    # Hue → CIELAB a*b*
    hue_rad = np.deg2rad(hue_deg)
    a_star = chroma * np.cos(hue_rad)
    b_star = chroma * np.sin(hue_rad)

    # CIELAB → RGB
    lab = np.array([L, a_star, b_star])
    rgb = color.lab2rgb(lab[np.newaxis, np.newaxis, :])

    return rgb[0, 0, :]

# Convert all reconstructed hues to RGB
modified_rgbs = []
for hue in reconstructed_hues:
    rgb = hue_to_rgb(hue, L=70, chroma=50)
    modified_rgbs.append(rgb)

modified_rgbs = np.array(modified_rgbs)  # (8, 3)
```

**Display to CVD**:
```python
# Original stimulus
original_rgbs = [
    [1.0, 0.0, 0.0],  # Red
    [1.0, 0.5, 0.0],  # Orange
    # ... 8 colors total
]

# Modified stimulus (filter applied)
modified_rgbs = [
    [0.95, 0.15, 0.10],  # Modified red
    [0.90, 0.55, 0.05],  # Modified orange
    # ... 8 colors total
]

# CVD sees modified_rgbs → should perceive like HC sees original_rgbs
```

---

## 전체 코드 예시

```python
import numpy as np
import pickle
from scipy.spatial.distance import squareform, pdist
from skimage import color

# ============================================
# Step 1: Load CVD raw voxel pattern
# ============================================
subject_id = '08'
roi = 'V1'
dataset = 'deoblique_v2'
timestamp = 'baseline32_deob_determin'

# Load amplitudes
amp_path = f'derivatives/BH2009_{dataset}/{timestamp}/sm*_sub-{subject_id}_{roi}_*/'
amplitudes_z = np.load(amp_path + 'amplitudes_z.npy')  # (6, 8, 356)
CVD_raw = np.mean(amplitudes_z, axis=0)  # (8, 356)

# ============================================
# Step 2: Apply filter (A, b)
# ============================================
filter_path = f'results/phase2/rdm_guided/{timestamp}/{roi}/sub-{subject_id}/'
A = np.load(filter_path + 'A.npy')  # (356, 356)
b = np.load(filter_path + 'b.npy')  # (356,)

X_filtered = CVD_raw @ A + b  # (8, 356)

# ============================================
# Step 3: Apply W matrix
# ============================================
W_path = f'results/group_level/procrustes_reconstruction/{roi}/'
model = pickle.load(open(W_path + 'procrustes_model.pkl', 'rb'))
W = model['W_common']  # (356, 6)

C_estimated = np.linalg.pinv(W.T @ W) @ W.T @ X_filtered.T
C_estimated = C_estimated.T  # (8, 6)

# ============================================
# Step 4: Channels → Hue
# ============================================
def create_basis_functions(n_channels=6):
    hues = np.arange(0, 360, 1)
    basis = np.zeros((360, n_channels))
    for i in range(n_channels):
        preferred_hue = i * 60
        for h_idx, hue in enumerate(hues):
            response = np.cos(np.deg2rad(hue - preferred_hue))
            basis[h_idx, i] = np.maximum(response, 0)
    return basis

basis = create_basis_functions(6)  # (360, 6)

reconstructed_hues = []
for color_idx in range(8):
    channels = C_estimated[color_idx, :]
    correlations = [np.corrcoef(channels, basis[h, :])[0, 1]
                   for h in range(360)]
    best_hue = np.argmax(correlations)
    reconstructed_hues.append(best_hue)

reconstructed_hues = np.array(reconstructed_hues)

# ============================================
# Step 5: Hue → RGB
# ============================================
def hue_to_rgb(hue_deg, L=70, chroma=50):
    hue_rad = np.deg2rad(hue_deg)
    a_star = chroma * np.cos(hue_rad)
    b_star = chroma * np.sin(hue_rad)
    lab = np.array([L, a_star, b_star])
    rgb = color.lab2rgb(lab[np.newaxis, np.newaxis, :])
    return rgb[0, 0, :]

modified_rgbs = np.array([hue_to_rgb(hue) for hue in reconstructed_hues])

print("Original hues (ground truth):", [0, 45, 90, 135, 180, 225, 270, 315])
print("Reconstructed hues:", reconstructed_hues)
print("Modified RGBs:", modified_rgbs)
```

---

## Validation Metrics

### 1. Reconstruction Error
```python
true_hues = np.array([0, 45, 90, 135, 180, 225, 270, 315])

def circular_diff_deg(hue1, hue2):
    diff = np.abs(hue1 - hue2)
    diff = np.where(diff > 180, 360 - diff, diff)
    return diff

errors = circular_diff_deg(reconstructed_hues, true_hues)
mean_error = np.mean(errors)

print(f"Reconstruction error: {mean_error:.1f}°")
# Target: < 90° (chance level)
# Good: < 45°
# Excellent: < 20°
```

### 2. RDM Similarity
```python
# Target HC RDM
HC_RDM_target = load_target_rdm()  # From Phase 2A

# Filtered voxel RDM
filtered_RDM = squareform(pdist(X_filtered, metric='correlation'))

# Correlation
rdm_corr = np.corrcoef(
    squareform(HC_RDM_target),
    squareform(filtered_RDM)
)[0, 1]

print(f"RDM correlation: {rdm_corr:.3f}")
# Target: > 0.5 (moderate similarity)
# Good: > 0.7
```

### 3. Classification Accuracy
```python
# 8 colors at 45° intervals
color_bins = np.arange(0, 360, 45)

def classify_hue(hue, bins):
    diffs = circular_diff_deg(hue, bins)
    return np.argmin(diffs)

predictions = [classify_hue(hue, color_bins) for hue in reconstructed_hues]
true_labels = np.arange(8)
accuracy = np.mean(np.array(predictions) == true_labels)

print(f"Classification accuracy: {accuracy*100:.1f}%")
# Target: > 12.5% (chance)
# Good: > 50%
# Excellent: > 87.5%
```

---

## Baseline Compatibility

### baseline32 vs baseline81

**Voxel Count**:
```
baseline32:
  V1: 356 voxels
  V2: 172 voxels
  V3: 58 voxels
  hV4: 34 voxels

baseline81:
  V1: 429 voxels
  V2: 279 voxels
  V3: 121 voxels
  hV4: 71 voxels
```

**일치 필요 사항**:
- Filter (A, b): Phase 2A 결과
- W matrix: Procrustes reconstruction 결과
- **반드시 같은 baseline 사용!**

**현재 상태**:
- Phase 2A filter: baseline32 완료 ✅
- W matrix: baseline81만 존재 ❌

**해결책**:
```bash
# baseline32로 W matrix 재학습
sbatch run_procrustes_reconstruction_train_baseline32.sbatch
```

---

## 논문 작성용 Summary

### Method

We applied a two-stage process to convert CVD color perception to HC-like:

**Stage 1: Voxel Space Transformation**
- Linear filter (A ∈ ℝ^(n×n), b ∈ ℝ^n) learned via RDM loss
- Transforms CVD voxel patterns to pseudo-HC space
- X_filtered = X_cvd @ A + b

**Stage 2: Color Reconstruction**
- HC common weight matrix W ∈ ℝ^(n×6) from Procrustes analysis
- Maps filtered voxels to 6-channel color representation
- C = (W^T W)^(-1) W^T X_filtered^T
- Hue reconstruction via template matching
- RGB conversion via CIELAB (L=70, chroma=50)

### Results

**Reconstruction Performance** (baseline32, V1):
- CVD subject 08: X.X° error
- CVD subject 09: X.X° error
- CVD subject 10: X.X° error
- Mean: X.X° (vs. 90° chance level)

**RDM Preservation**:
- CVD-HC RDM correlation: 0.XXX
- Color discriminability structure maintained

---

**최종 업데이트**: 2025-12-19
**Configuration**: baseline32 (356 voxels for V1)
**Next Step**: baseline32 W matrix 학습 필요
