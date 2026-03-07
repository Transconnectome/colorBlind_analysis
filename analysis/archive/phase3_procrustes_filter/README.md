# Phase 3: Procrustes-Based Linear Filter Design

**Research Question (RQ3)**: Can three-dimensional neural profiles inform personalized filter design?
**3차원 신경 프로파일이 개인별 맞춤형 필터 설계에 활용될 수 있는가?**

**Status**: In Progress 🔄
**Scripts**: 14 files

---

## Overview

This phase develops **subject-specific linear transformations** to map CVD brain patterns to HC-like patterns, using three-dimensional loss functions tailored to individual distortion profiles (from Phase 2).

## Scripts in This Directory

### Core Filter Training

**1. `phase2a_train_filter.py`** (PyTorch version)
- Main filter training script using PyTorch
- Implements 3D loss function (magnitude + baseline + structure)
- GPU-accelerated optimization
- Outputs: Trained filter (A matrix, b vector), training logs

**2. `phase2a_train_filter_numpy.py`** (NumPy version)
- Pure NumPy implementation (no PyTorch dependency)
- Faster for small datasets
- Same 3D loss function

**3. `phase2a_train_single.py`**
- Train filter for single CVD subject
- Easier debugging and parameter tuning
- Useful for individual subject optimization

**4. `phase2a_train_single_baseline81.py`**
- Baseline81 dataset version (81 trials per color)
- More training data for stable filter learning

### Pattern Extraction

**5. `phase2a_extract_patterns.py`**
- Extract CVD and HC patterns from baseline analysis
- Loads amplitudes_z.npy from derivatives/
- Prepares data for filter training

**6. `phase2a_extract_patterns_baseline81.py`**
- Baseline81 dataset version
- Extracts patterns from larger trial set

### Filter Application & Validation

**7. `apply_filter_with_reconstruction.py`**
- Apply trained filter to CVD patterns
- Compute reconstruction accuracy before/after filtering
- Validate on held-out runs

**8. `phase2a_analyze_results.py`**
- Comprehensive result analysis
- Compare pre/post filter metrics
- Generate summary statistics

### RDM Analysis

**9. `phase2a_compute_rdm.py`**
- Compute Representational Dissimilarity Matrix (RDM)
- Calculate pre/post filter RDM
- RDM correlation with HC

**10. `phase2a_compute_metrics.py`**
- Compute all evaluation metrics:
  - Procrustes disparity
  - RDM correlation
  - Reconstruction error
  - Pattern correlation

### Visualization

**11. `visualize_rdm_difference.py`**
- Visualize RDM before/after filtering
- Heatmaps showing color similarity structure
- Difference plots (HC - CVD)

**12. `visualize_rdm_improvement_compact.py`**
- Compact visualization of RDM improvement
- Side-by-side comparison (pre/post/HC)
- Summary metrics overlay

**13. `visualize_filter_properties.py`**
- Visualize learned filter properties
- Weight matrix heatmap (A)
- Bias vector plot (b)
- Per-color transformation analysis

**14. `verify_w_matrix.py`**
- Verify W matrix (decoder) consistency
- Check if HC decoder works on filtered CVD patterns
- Validation of shared decoder assumption (SRQ1)

## Key Results (RQ3)

### ✅ Feasibility Demonstrated (Retrospective Validation)

**Subject-Specific Linear Filters Successfully Trained**:

| Subject | CVD Type | Geometric Alignment | Structural Recovery | Optimal Loss Weights |
|---------|----------|---------------------|---------------------|----------------------|
| **Sub-08** | Deut | 97.2% disparity ↓ | RDM r = 0.999 | λ_mag=0.5, λ_base=0.3, λ_struct=1.0 |
| **Sub-09** | Deut | 95.8% disparity ↓ | RDM r = 0.998 | λ_mag=1.0, λ_base=0.5, λ_struct=0.3 |
| **Sub-10** | Prot | 96.3% disparity ↓ | RDM r = 0.999 | λ_mag=0.7, λ_base=0.7, λ_struct=0.7 |

**Interpretation**:
- ✅ Linear transformations **successfully align CVD → HC patterns**
- ✅ Individual optimization **tailors filters to each distortion profile**
- ⚠️ **Limitation**: Retrospective validation only (applied to training data)

### ⚠️ Prospective Validation Pending

**Current Scope**:
- ✅ Trained filters on 7 runs
- ✅ Validated on held-out 8th run (brain pattern matching)
- ❌ **NOT yet validated** with actual filtered stimuli in behavioral testing

**Next Steps Required**:
1. Generate filtered images using learned color LUTs
2. Psychophysical validation (Farnsworth-Munsell 100 Hue test)
3. fMRI validation (scan CVD with filtered stimuli, verify HC-like responses)

---

## Method

### Linear Filter Formulation

**Goal**: Learn transformation F that maps CVD patterns Y to HC-like patterns H

```python
F = Y @ A + b
```

where:
- **Y**: CVD pattern (8 colors × n_voxels)
- **A**: Transformation matrix (n_voxels × n_voxels)
- **b**: Bias vector (n_voxels)
- **H**: HC target pattern (from super-participant)

### Three-Dimensional Loss Function

**Total Loss**:
```python
L_total = λ_mag * L_magnitude +
          λ_base * L_baseline +
          λ_struct * L_structure +
          λ_reg * L_regularization
```

**1. Magnitude Loss** (L2 norm matching):
```python
L_magnitude = ||norm(F, axis=1) - norm(H, axis=1)||^2
# Matches overall pattern strength per color
```

**2. Baseline Loss** (mean activation matching):
```python
L_baseline = ||mean(F, axis=0) - mean(H, axis=0)||^2
# Matches average voxel activation
```

**3. Structure Loss** (RDM matching):
```python
RDM_F = pdist(F, metric='correlation')
RDM_H = pdist(H, metric='correlation')
L_structure = ||RDM_F - RDM_H||^2
# Matches pairwise color similarity geometry
```

**4. Regularization Loss**:
```python
L_reg = ||A - I||^2 + ||b||^2
# Encourages identity transformation (minimal modification)
```

### Individual Optimization

**Loss weights tailored to Phase 2 characterization**:

| Subject | Dominant Distortion | Optimal Weights |
|---------|---------------------|-----------------|
| **Sub-08** | High structure diff (0.505) | λ_struct = 1.0 (HIGH) |
| **Sub-09** | High magnitude ratio (1.21) | λ_mag = 1.0 (HIGH) |
| **Sub-10** | Balanced distortion | λ_mag = λ_base = λ_struct = 0.7 |

---

## Implementation

**Main Script** (in `scripts/phase2a_filter_learning/`):
- `phase2a_train_filter.py`: PyTorch-based filter optimization
- `apply_filter_with_reconstruction.py`: Apply learned filter and validate

**Training Strategy**:
```python
# 1. Initialize filter parameters
A = torch.eye(n_voxels, requires_grad=True)
b = torch.zeros(n_voxels, requires_grad=True)

# 2. Optimize using Adam
optimizer = torch.optim.Adam([A, b], lr=0.001)
for epoch in range(1000):
    F = Y @ A + b
    loss = compute_loss(F, H, lambdas)
    loss.backward()
    optimizer.step()

# 3. Validate on held-out run
F_test = Y_test @ A_final + b_final
reconstruction_error = evaluate(F_test, H_test)
```

**Cross-Validation**:
- Train on 7 runs, validate on 1 held-out run
- Repeat 8 times (leave-one-run-out)
- Average performance across folds

---

## Results

### Geometric Alignment

**Procrustes Disparity Reduction**:

| Subject | Before Filter | After Filter | Reduction |
|---------|---------------|--------------|-----------|
| Sub-08 V1 | 0.132 | 0.004 | 97.2% ↓ |
| Sub-08 V2 | 0.178 | 0.005 | 97.2% ↓ |
| Sub-09 V1 | 0.115 | 0.005 | 95.8% ↓ |
| Sub-09 V2 | 0.113 | 0.005 | 95.6% ↓ |
| Sub-10 V1 | 0.101 | 0.004 | 96.3% ↓ |
| Sub-10 V2 | 0.117 | 0.004 | 96.6% ↓ |

### Structural Recovery

**RDM Correlation with HC**:

| Subject | Before Filter | After Filter |
|---------|---------------|--------------|
| Sub-08 | 0.495 | 0.999 |
| Sub-09 | 0.882 | 0.998 |
| Sub-10 | 0.690 | 0.999 |

**Interpretation**: Near-perfect structural alignment (r > 0.99) achieved

---

## Limitations & Future Work

### Current Limitations

1. **Retrospective validation only**
   - Filters optimized AND validated on same dataset
   - Risk of overfitting to training data
   - Does NOT confirm behavioral improvement

2. **Brain space transformation**
   - Filter operates on voxel patterns, not stimulus colors
   - Requires inverse mapping (Phase 2-3 of MASTER_PLAN) for actual display filter

3. **No psychophysical validation**
   - No behavioral color discrimination testing
   - No subjective perceptual quality assessment

### Required Next Steps

**Prospective Validation**:
1. Generate stimulus-space color LUTs (requires inverse transformation)
2. Create filtered image dataset
3. Behavioral testing:
   - Farnsworth-Munsell 100 Hue test (pre/post filtered stimuli)
   - Color naming accuracy
   - Subjective preference ratings
4. fMRI validation:
   - Scan CVD with filtered stimuli
   - Verify HC-like brain responses

**Connection to MASTER_PLAN Phases**:
- This work = **Proof-of-concept** for filter feasibility
- MASTER_PLAN Phase 1-3 = **Full pipeline** for stimulus-space filter

---

## Relationship to Future Phases

### Current Phase 3 vs. Future Phase 3

| Aspect | Current Phase 3 (Procrustes Filter) | Future Phase 3 (360° Optimization) |
|--------|-------------------------------------|-----------------------------------|
| **Space** | Voxel space (brain) | Color space (stimulus) |
| **Method** | Direct linear transformation | Optimization-based search |
| **Coverage** | 8 measured colors | 360° continuous hue |
| **Validation** | Retrospective (training data) | Prospective (behavioral + fMRI) |

**Current Phase 3 demonstrates**:
- Linear filters can align CVD → HC patterns
- Individual optimization improves performance
- Three-dimensional loss functions work

**Future Phase 3 will address**:
- Stimulus-space correction (actual display filter)
- Continuous hue coverage (not just 8 colors)
- Prospective empirical validation

---

## Usage Examples

### 1. Extract Patterns from Baseline Results

```bash
python phase2a_extract_patterns.py \
    --dataset deoblique_v2 \
    --timestamp baseline81_deob_determin
```

**Output**: `patterns/sub-{ID}_{roi}_patterns.npz` containing CVD and HC patterns

### 2. Train Filter for Single Subject

```bash
python phase2a_train_single.py \
    --cvd_subject 08 \
    --roi V1 \
    --lambda_mag 0.5 \
    --lambda_base 0.3 \
    --lambda_struct 1.0 \
    --epochs 1000
```

**Output**: `results/sub-08_V1_filter.npz` (A matrix, b vector, training history)

### 3. Apply Filter and Validate

```bash
python apply_filter_with_reconstruction.py \
    --cvd_subject 08 \
    --roi V1 \
    --filter_path results/sub-08_V1_filter.npz
```

**Output**: Reconstruction accuracy, Procrustes disparity reduction

### 4. Compute RDM Before/After

```bash
python phase2a_compute_rdm.py \
    --cvd_subject 08 \
    --roi V1 \
    --filter_path results/sub-08_V1_filter.npz
```

**Output**: `rdm/sub-08_V1_rdm_comparison.npz` (RDM_cvd_pre, RDM_cvd_post, RDM_hc)

### 5. Visualize Results

```bash
python visualize_rdm_improvement_compact.py \
    --cvd_subject 08 \
    --roi V1
```

**Output**: `figures/sub-08_V1_rdm_improvement.png`

```bash
python visualize_filter_properties.py \
    --cvd_subject 08 \
    --roi V1 \
    --filter_path results/sub-08_V1_filter.npz
```

**Output**: `figures/sub-08_V1_filter_properties.png` (weight matrix heatmap, bias plot)

---

## Output Structure

```
analysis/phase3_procrustes_filter/
├── patterns/                      # Extracted CVD and HC patterns
│   ├── sub-08_V1_patterns.npz
│   ├── sub-09_V1_patterns.npz
│   └── sub-10_V1_patterns.npz
│
├── results/                       # Trained filters
│   ├── sub-08_V1_filter.npz      # A matrix, b vector
│   │   ├── A: (n_voxels, n_voxels)
│   │   ├── b: (n_voxels,)
│   │   └── training_history: dict
│   ├── sub-08_V1_metrics.txt     # Validation metrics
│   └── ... (all subjects, all ROIs)
│
├── rdm/                           # RDM analysis
│   ├── sub-08_V1_rdm_comparison.npz
│   │   ├── RDM_cvd_pre: (8, 8)
│   │   ├── RDM_cvd_post: (8, 8)
│   │   ├── RDM_hc: (8, 8)
│   │   └── correlation_pre/post: float
│   └── ...
│
└── figures/                       # Visualizations
    ├── sub-08_V1_rdm_improvement.png
    ├── sub-08_V1_filter_properties.png
    ├── sub-08_V1_disparity_reduction.png
    └── ...
```

**Note**: Results are also available in `scripts/phase2a_filter_learning/` (original location) for backward compatibility.

---

## References

- See main README.md (RQ3 section)
- Related: Phase 2 (Procrustes CVD-HC analysis)
- Related: Future Phase 3 (360° filter optimization in MASTER_PLAN)
