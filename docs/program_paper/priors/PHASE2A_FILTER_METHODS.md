# Phase 2A: Linear Filter Learning - Methods and Implementation

**Date**: 2025-12-19
**Purpose**: Complete documentation of filter learning methodology, implementation details, and configuration settings

---

## Table of Contents

1. [Overview](#1-overview)
2. [Mathematical Formulation](#2-mathematical-formulation)
3. [Loss Function Design](#3-loss-function-design)
4. [Optimization Method](#4-optimization-method)
5. [Implementation Details](#5-implementation-details)
6. [Configuration Settings](#6-configuration-settings)
7. [Code Structure](#7-code-structure)
8. [Execution Guide](#8-execution-guide)

---

## 1. Overview

### 1.1 Goal

**Learn a linear transformation filter that transforms CVD fMRI patterns to match HC patterns**

- **Input**: CVD pattern Y ∈ ℝ^(8×n) (8 colors, n voxels)
- **Output**: Filtered pattern F ∈ ℝ^(8×n) that matches HC pattern H
- **Filter**: Linear transformation F = Y @ A + b
  - A ∈ ℝ^(n×n): transformation matrix
  - b ∈ ℝ^n: bias vector

### 1.2 Hypothesis

If filter successfully transforms CVD patterns to HC-like patterns:
1. **Procrustes disparity** between F and H should decrease dramatically
2. **RDM similarity** between F and H should approach 1.0
3. CVD subjects viewing filtered images may experience **improved color discrimination**

### 1.3 Design Philosophy

**Individual-specific filters** rather than group-level:
- Each CVD subject has unique distortion patterns (Sub-08: structure, Sub-09/10: magnitude)
- Subject-specific loss weights optimize for individual characteristics
- Personalized correction for optimal results

---

## 2. Mathematical Formulation

### 2.1 Filter Definition

**Linear transformation**:
```
F = Y @ A + b
```

Where:
- Y ∈ ℝ^(8×n): CVD input pattern (measured fMRI responses)
- A ∈ ℝ^(n×n): transformation matrix (learned)
- b ∈ ℝ^n: bias vector (learned)
- F ∈ ℝ^(8×n): filtered output pattern
- H ∈ ℝ^(8×n): target HC pattern (HC_mean)

**Total parameters**: n² + n
- V1 baseline32 (356 voxels): 127,092 parameters
- V1 baseline81 (429 voxels): 184,470 parameters
- V2 baseline32 (172 voxels): 29,756 parameters
- V2 baseline81 (279 voxels): 78,120 parameters

### 2.2 Optimization Objective

**Minimize**:
```
L_total = λ_mag · L_mag + λ_base · L_base + λ_struct · L_struct + α||A - I||²_F + β||b||²
```

Subject to learned parameters (A, b).

**Components**:
1. **L_mag**: Magnitude matching (color-wise activation strength)
2. **L_base**: Baseline matching (color-wise mean activation)
3. **L_struct**: Structure matching (voxel pattern relationships)
4. **Regularization**: Penalize deviation from identity transformation

---

## 3. Loss Function Design

### 3.1 Component 1: Magnitude Loss

**Definition**:
```python
L_mag = (1/8) Σᵢ (||F[i]|| - ||H[i]||)²
```

**Purpose**: Match per-color L2 norm (activation strength)

**Why needed**:
- CVD subjects show **over-activation** for certain colors
- Example: Sub-08 Magenta 121%, Sub-09 Red 132%
- Magnitude loss normalizes activation strength

**Gradient (Analytical)**:
```python
∂L_mag/∂F[i] = (2/8) · (||F[i]|| - ||H[i]||) · (F[i] / ||F[i]||)
```

### 3.2 Component 2: Baseline Loss

**Definition**:
```python
L_base = (1/8) Σᵢ (mean(F[i]) - mean(H[i]))²
```

**Purpose**: Match per-color mean activation (directionality)

**Why needed**:
- L2 norm loses sign information (±0.3 both become 0.3)
- Need to distinguish over-activation (+) from under-activation (-)

**Gradient (Analytical)**:
```python
∂L_base/∂F[i,j] = (1/(4n)) · (mean(F[i]) - mean(H[i]))
```

### 3.3 Component 3: Structure Loss (Option D - RDM-Based)

**Definition**:
```python
L_struct = ||RDM(F) - RDM(H)||²_F
```

Where RDM[i,j] = 1 - Spearman_correlation(pattern[i], pattern[j])

**Purpose**: Match **color-pair dissimilarity structure**

**Why needed**:
- Captures color-pair relationships (e.g., Red-Green collapse in deuteranopia)
- Magnitude-invariant (RDM based on correlation ranks)
- Detects systematic distortions in color space

**Example distortions** (from Phase 1):
- Sub-08: Yellow-Green collapse (z=-2.99), Green-Blue expansion (z=+4.22)
- Need to preserve these relative dissimilarities

**Gradient (Numerical)**:
```python
∂L_struct/∂F ≈ (L_struct(F + ε) - L_struct(F)) / ε
```

Reason: Spearman correlation is rank-based, analytical gradient is complex.

### 3.4 Regularization Terms

**Identity preservation**:
```python
R_A = α · ||A - I||²_F
```
- Penalize deviation from identity matrix
- Encourages minimal transformation
- α = 0.01

**Bias suppression**:
```python
R_b = β · ||b||²
```
- Penalize large bias terms
- Prefer pure linear transformation
- β = 0.01

---

## 4. Optimization Method

### 4.1 L-BFGS-B Algorithm

**Method**: Limited-memory Broyden–Fletcher–Goldfarb–Shanno with Box constraints

**Why L-BFGS-B**:
1. **Efficient for large-scale** problems (100k+ parameters)
2. **Quasi-Newton method**: approximates Hessian from gradients
3. **Memory efficient**: stores only recent gradient history
4. **Proven convergence**: for smooth, differentiable objectives

**Settings**:
```python
minimize(
    fun=loss_function,
    x0=initial_params,
    method='L-BFGS-B',
    jac=True,  # Gradient provided
    options={
        'maxiter': 1000,
        'ftol': 1e-9,  # Function tolerance
        'disp': True   # Display progress
    }
)
```

### 4.2 Initialization

**Identity + zero bias**:
```python
A_init = I  (n×n identity matrix)
b_init = 0  (n-dimensional zero vector)
```

**Rationale**:
- Start from "no transformation" baseline
- Gradient descent finds minimal required transformation
- Regularization prevents overfitting

### 4.3 Convergence Criteria

**Stop when**:
1. `|f(x_k) - f(x_{k-1})| / max(|f(x_k)|, 1) < ftol` (function tolerance)
2. `||∇f(x_k)|| < gtol` (gradient tolerance, default 1e-5)
3. `iteration >= maxiter` (1000)

**Typical convergence**:
- Iterations: 200-400
- Final loss: 0.0003-0.0007
- Time: 5-15 minutes per model (CPU)

---

## 5. Implementation Details

### 5.1 Gradient Computation

**Hybrid approach**: Analytical + Numerical

```python
def compute_gradient(params, Y, H, weights, n_voxels):
    """
    Compute ∂L_total/∂params where params = [A.flatten(), b]
    """
    # 1. Magnitude gradient (Analytical)
    norm_F = ||F||_2 (per color)
    norm_H = ||H||_2 (per color)
    grad_mag_F = (2/8) * (norm_F - norm_H) * (F / norm_F)

    # 2. Baseline gradient (Analytical)
    mean_F = mean(F, axis=1)
    mean_H = mean(H, axis=1)
    grad_base_F = (1/(4n)) * (mean_F - mean_H) * ones_like(F)

    # 3. Structure gradient (Numerical approximation)
    grad_struct_F = approx_fprime(F, rdm_loss, epsilon=1e-8)

    # 4. Combine weighted gradients
    grad_F = λ_mag * grad_mag_F + λ_base * grad_base_F + λ_struct * grad_struct_F

    # 5. Chain rule: F = Y @ A + b
    grad_A = Y.T @ grad_F
    grad_b = sum(grad_F, axis=0)

    # 6. Add regularization gradients
    grad_A += 2α * (A - I)
    grad_b += 2β * b

    return concat([grad_A.flatten(), grad_b])
```

**Why numerical for RDM**:
- Spearman correlation uses **rank ordering** (non-differentiable at ties)
- Analytical gradient requires complex bookkeeping
- Numerical approximation: accurate enough, simpler to implement

**Performance**:
- Analytical gradients: ~10× faster than full numerical
- Numerical RDM gradient: acceptable (only 1/3 of total)

### 5.2 RDM Computation

```python
def compute_rdm(pattern):
    """
    pattern: (8, n_voxels)
    returns: (8, 8) dissimilarity matrix
    """
    n_colors = 8
    rdm = np.zeros((n_colors, n_colors))

    for i in range(n_colors):
        for j in range(n_colors):
            if i != j:
                corr, _ = spearmanr(pattern[i], pattern[j])
                rdm[i, j] = 1 - corr
            else:
                rdm[i, j] = 0

    return rdm
```

**Properties**:
- Symmetric: RDM[i,j] = RDM[j,i]
- Diagonal: RDM[i,i] = 0
- Range: [0, 2] (1 - correlation ∈ [-1, 1])

### 5.3 Voxel Alignment

**Problem**: Different subjects have different voxel counts

**Solution**: Align to minimum voxel count before training

```python
n_voxels_hc = hc_pattern.shape[1]
n_voxels_cvd = cvd_pattern.shape[1]
n_voxels = min(n_voxels_hc, n_voxels_cvd)

if n_voxels_hc != n_voxels_cvd:
    hc_pattern = hc_pattern[:, :n_voxels]
    cvd_pattern = cvd_pattern[:, :n_voxels]
```

**Example (V2, baseline81)**:
- HC_mean: 279 voxels
- sub-08: 279 voxels → no alignment
- sub-09: 233 voxels → align to 233
- sub-10: 263 voxels → align to 263

---

## 6. Configuration Settings

### 6.1 Subject-Specific Weights

**Based on Phase 1 characterization**:

| Subject | λ_mag | λ_base | λ_struct | Rationale |
|---------|-------|--------|----------|-----------|
| **sub-08** | 0.2 | 0.3 | **0.5** | Structure-dominant: Systematic color-pair distortions (Yellow-Green z=-2.99) |
| **sub-09** | **0.5** | 0.3 | 0.2 | Magnitude-dominant: High over-activation (Red 132%) |
| **sub-10** | **0.5** | 0.3 | 0.2 | Magnitude-dominant: Moderate magnitude differences, structure near-normal |

**Tuning strategy**:
1. Identify dominant distortion from Phase 1 Procrustes analysis
2. Increase weight for dominant component
3. Validate with cross-validation (future work)

### 6.2 Hyperparameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| α (alpha) | 0.01 | Regularization strength for ||A - I||²_F |
| β (beta) | 0.01 | Regularization strength for ||b||² |
| max_iter | 1000 | Maximum optimization iterations |
| ftol | 1e-9 | Function convergence tolerance |
| epsilon (numerical gradient) | 1e-8 | Step size for finite differences |

**Rationale for α, β**:
- Too small (< 0.001): Overfitting, large ||A - I||
- Too large (> 0.1): Underfitting, insufficient transformation
- 0.01: Balanced regularization, empirically validated

### 6.3 Preprocessing Pipelines

**Two voxel selection criteria**:

| Pipeline | Voxel Selection | V1 Voxels | V2 Voxels | Disparity Range |
|----------|----------------|-----------|-----------|-----------------|
| **baseline32** | Top 32% variance | 356 | 172 | 0.9-1.1 (high) |
| **baseline81** | Top 81% variance | 429 | 279 | 0.26-0.36 (low) |

**Common settings**:
- Preprocessing: deoblique, deterministic HRF
- ROIs: V1, V2 (V3, hV4 available but not used in Phase 1)
- HC group: n=4 (sub-03, 05, 06, 07)
- CVD group: n=3 (sub-08, 09, 10)

---

## 7. Code Structure

### 7.1 File Organization

```
scripts/
├── phase2a_train_single_baseline81.py   # Training script (baseline81)
├── phase2a_train_array_baseline81.sh    # SBATCH array job
├── phase2a_train_single.py              # Training script (baseline32)
└── phase2a_train_gpu.py                 # GPU version (future)

results/
├── group_level/
│   ├── phase2a_data/                    # baseline32 patterns
│   │   └── patterns/
│   │       ├── HC_mean/
│   │       ├── sub-{03,05,06,07}/      # HC individual
│   │       └── sub-{08,09,10}/         # CVD
│   └── phase2a_data_baseline81/         # baseline81 patterns
│       └── patterns/ (same structure)
│
└── filters/
    ├── models_baseline81/optionD/       # baseline81 models
    │   ├── sub-08/{V1,V2}/
    │   │   ├── A_matrix.npy
    │   │   ├── b_vector.npy
    │   │   └── metadata.json
    │   ├── sub-09/{V1,V2}/
    │   └── sub-10/{V1,V2}/
    └── models/optionD/                  # baseline32 models (same structure)
```

### 7.2 Key Functions

**Training script** (`phase2a_train_single_baseline81.py`):

```python
def magnitude_loss(F, H)                 # L_mag computation
def baseline_loss(F, H)                  # L_base computation
def rdm_loss(F, H)                       # L_struct computation (Option D)
def compute_gradient(params, Y, H, ...)  # Hybrid gradient
def three_component_loss(params, ...)    # Total loss
def three_component_loss_with_grad(...)  # Loss + gradient (for L-BFGS-B)
def train_model(subject_id, roi)         # Main training loop
```

**Output** (`metadata.json`):

```json
{
  "subject": "08",
  "roi": "V1",
  "preprocessing": "baseline81_deob_determin",
  "n_voxels": 429,
  "weights": {
    "magnitude": 0.2,
    "baseline": 0.3,
    "structure": 0.5
  },
  "hyperparameters": {
    "alpha": 0.01,
    "beta": 0.01,
    "max_iter": 1000
  },
  "optimization": {
    "final_loss": 0.000456,
    "success": true,
    "n_iterations": 287,
    "message": "CONVERGENCE: NORM_OF_PROJECTED_GRADIENT_<=_PGTOL"
  },
  "filter_properties": {
    "deviation_from_identity": 1.234,
    "bias_norm": 0.567
  },
  "trained_date": "2025-12-19T13:45:59"
}
```

---

## 8. Execution Guide

### 8.1 Server Execution (Recommended)

**Upload scripts**:
```bash
scp scripts/phase2a_train_single_baseline81.py haba6030@node2:/scratch/connectome/haba6030/colorBlind/scripts/
scp scripts/phase2a_train_array_baseline81.sh haba6030@node2:/scratch/connectome/haba6030/colorBlind/scripts/
```

**Submit SBATCH array job** (trains all 6 models in parallel):
```bash
ssh haba6030@node2
cd /scratch/connectome/haba6030/colorBlind
sbatch scripts/phase2a_train_array_baseline81.sh
```

**Monitor progress**:
```bash
squeue -u haba6030              # Check job status
tail -f logs/phase2a_train_baseline81_*.out  # Watch output
```

**Download results**:
```bash
scp -r haba6030@node2:/scratch/connectome/haba6030/colorBlind/results/filters/models_baseline81 results/filters/
```

### 8.2 Single Model Training (Testing)

```bash
python scripts/phase2a_train_single_baseline81.py --subject 08 --roi V1
```

**Arguments**:
- `--subject`: 08, 09, or 10
- `--roi`: V1 or V2

### 8.3 Expected Runtime

| Configuration | Time (CPU, single core) | Time (parallel, 6 cores) |
|---------------|------------------------|--------------------------|
| V1 baseline32 (356 voxels) | ~10 min | ~10 min |
| V1 baseline81 (429 voxels) | ~15 min | ~15 min |
| V2 baseline32 (172 voxels) | ~5 min | ~5 min |
| V2 baseline81 (279 voxels) | ~8 min | ~8 min |
| **Total (6 models)** | ~60 min | ~15 min |

---

## Appendix A: Comparison with Other Options

### Option A: Angular Distance (Deprecated)

**Definition**:
```python
L_struct_A = (1/8) Σᵢ arccos²(cos_sim(F[i], H[i]))
```

**Pros**:
- Simple, interpretable (angle per color)
- Fully analytical gradient

**Cons**:
- Treats colors independently (no color-pair relationships)
- Missing cross-color structure information

**Performance**: Comparable to Option D, but less interpretable for color-pair distortions

### Option B: Variance Decomposition (Deprecated)

**Definition**:
```python
L_struct_B = Σᵢ 2·||F[i]||·||H[i]||·(1 - cos_sim(F[i], H[i]))
```

**Pros**:
- Mathematically exact: Total² = Magnitude² + Angular²
- Analytical gradient

**Cons**:
- **Empirically poor performance**: 10-100× worse final loss than A/D
- Norm-weighted: large activations dominate
- Deprecated after empirical comparison

**Empirical results** (baseline32):
- Option B: 0/6 wins, final loss 0.005-0.05 (10-100× worse)
- Option D: 6/6 wins, final loss 0.0003-0.0007

---

## Appendix B: Mathematical Derivations

### B.1 Magnitude Loss Gradient

**Loss**:
```
L_mag = (1/8) Σᵢ (||F[i]|| - ||H[i]||)²
```

**Gradient w.r.t. F[i]**:
```
∂L_mag/∂F[i] = (1/8) · 2 · (||F[i]|| - ||H[i]||) · ∂||F[i]||/∂F[i]

where ∂||F[i]||/∂F[i] = F[i] / ||F[i]||

Therefore:
∂L_mag/∂F[i] = (2/8) · (||F[i]|| - ||H[i]||) · (F[i] / ||F[i]||)
```

### B.2 Chain Rule for Transformation

**Forward pass**:
```
F = Y @ A + b  (broadcast b across colors)
```

**Gradient w.r.t. A**:
```
∂L/∂A = Y^T @ (∂L/∂F)
```

**Gradient w.r.t. b**:
```
∂L/∂b = Σᵢ (∂L/∂F[i])  (sum over colors)
```

---

**Document version**: 1.0
**Last updated**: 2025-12-19
**Author**: Phase 2A Analysis Pipeline
