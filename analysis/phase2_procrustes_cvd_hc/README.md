# Phase 2: Procrustes Analysis - CVD-HC Comparison

**Research Question (RQ2)**: Does CVD show inter-individual heterogeneity requiring personalized approaches?
**색맹은 개인 간 이질성을 보이는가? 개인화된 접근이 필요한가?**

**Supporting Research Question (SRQ1)**: Can a common decoder be shared across HC and CVD after alignment?
**정렬 후 정상인과 색맹 간 공통 디코더를 공유할 수 있는가?**

원인: Voxel-wise group analysis 결과 피험자 별 voxel spatial location이 다르다.

**Status**: Completed ✅
**Scripts**: 12 files

---

## Overview

This phase uses Procrustes analysis to quantify CVD-HC differences in neural color representations and characterizes individual CVD heterogeneity in **three dimensions**:

1. **Magnitude** (크기): Overall pattern strength (L2 norm)
2. **Sign/Baseline** (부호/기준선): Directional biases (mean activation)
3. **Structure** (구조): Representational geometry (RDM differences)

## Key Findings (RQ2)

### ✅ Substantial individual heterogeneity, even within same CVD type

**Three-Dimensional Characterization**:

| Subject | CVD Type | Magnitude (L2 ratio) | Sign/Baseline | Structure (RDM diff) | Total T |
|---------|----------|---------------------|---------------|---------------------|---------|
| **Sub-08** | Deut | 0.66 (-34%) | -0.41 | 0.505 | 0.178 (V2) |
| **Sub-09** | Deut | 1.21 (+21%) | +0.32 | 0.118 | 0.115 (V1) |
| **Sub-10** | Prot | 0.89 (-11%) | -0.05 | 0.310 | 0.117 (V2) |

**Key Insight**: **Sub-08 vs Sub-09** have **identical genotype** (deuteranopia) but **opposite neural phenotypes**:
- Sub-08: Low magnitude, negative baseline, high structural distortion
- Sub-09: High magnitude, positive baseline, low structural distortion

**Conclusion**: Personalized interventions are **necessary**; generic CVD filter would fail due to opposing distortion profiles.

---

## Key Findings (SRQ1)

### ✅ Common decoder successfully applied after Procrustes alignment

**Experiment**:
1. Fit common HC decoder (W matrix) on HC super-participant
2. Apply to aligned CVD patterns (after Procrustes transformation)
3. Measure reconstruction error

**Results**:

| Condition | V1 Error | V2 Error | Interpretation |
|-----------|----------|----------|----------------|
| HC common W (baseline) | 32° | 35° | HC performance |
| CVD + Procrustes + HC W | 36-42° | 38-45° | **Success!** Near-HC performance |
| CVD without alignment | 84-96° | 88-94° | Fails (chance level) |

**Conclusion**: **Linear transformation (Procrustes) is sufficient** for decoder sharing → Supports feasibility of linear filter design (Phase 3)

---

## Key Scripts

### Core Analysis

#### 1. `option2b_procrustes_alignment.py`

**Purpose**: Procrustes alignment of CVD → HC

**Method**:
```python
# Find optimal orthogonal transformation R, scaling s, translation c
CVD_aligned = s * CVD @ R + c
# such that ||CVD_aligned - HC||^2 is minimized
```

**Output**:
- Transformation matrix R
- Procrustes disparity (T)
- Aligned CVD patterns

#### 2. `option2d_procrustes_cvd_comparison.py`

**Purpose**: Statistical comparison of CVD-HC differences

**Methods**:
- Permutation testing (1000 iterations)
- Procrustes disparity as test statistic
- Significance threshold: p < 0.001

**Results**:
All CVD subjects significantly different from HC (p < 0.001)

#### 3. `validate_transformation_t.py`

**Purpose**: Validate that Procrustes transformation improves decoder transfer

**Method**:
1. Align CVD → HC space using Procrustes
2. Apply HC common decoder
3. Measure reconstruction error before/after alignment

**Result**:
- Before: 84-96° error (chance level)
- After: 36-42° error (near-HC performance)

#### 4. `verify_option_a_robustness.py`

**Purpose**: Cross-validation of Procrustes estimates

**Methods**:
- Split-half reliability (odd vs even runs)
- Leave-one-run-out validation
- Stability across ROIs

**Result**: High stability (r > 0.85 split-half correlation)

### Visualization & Exploration

#### 5. `reconstruction_with_procrustes.py`

**Purpose**: Reconstruct colors using Procrustes-aligned patterns

**Output**: Color wheels showing pre/post alignment reconstruction accuracy

#### 6. `reconstruction_with_procrustes_noalign.py`

**Purpose**: Baseline comparison without alignment (ablation study)

**Result**: Confirms necessity of alignment for decoder sharing

#### 7. `visualize_circular_disparity.py`

**Purpose**: Visualize Procrustes disparity for each color

**Output**: Radar plot showing per-color distortion magnitude

#### 8. `visualize_circular_activation.py`

**Purpose**: Visualize activation patterns in circular color space

**Output**: Polar plots of channel responses for each color

#### 9. `visualize_activation_vs_disparity.py`

**Purpose**: Scatter plot of activation magnitude vs. Procrustes disparity

**Finding**: No linear relationship → Disparity driven by structural differences, not magnitude

#### 10. `visualize_topology_perspective.py`

**Purpose**: Topological analysis of color representation geometry

**Methods**:
- Persistent homology
- Manifold curvature estimation

**Finding**: CVD preserves topological structure but distorts metric distances

#### 11. `create_procrustes_color_points_concept.py`

**Purpose**: Generate conceptual figure for paper (color space distortion)

**Output**: 2D projection showing CVD vs. HC color cloud alignment

#### 12. `create_procrustes_concept_figure.py`

**Purpose**: Create schematic diagram of Procrustes method

**Output**: Paper figure illustrating R, s, c transformation

---

## Methods

### Procrustes Analysis

**Standard Procrustes**:
```python
# Given: CVD pattern Y (n_colors × n_voxels), HC pattern H
# Find: R (rotation/reflection), s (scaling), c (translation)

# 1. Center patterns
Y_centered = Y - mean(Y, axis=0)
H_centered = H - mean(H, axis=0)

# 2. Compute optimal rotation via SVD
U, Sigma, Vt = svd(Y_centered.T @ H_centered)
R = U @ Vt

# 3. Compute scaling
s = trace(Sigma) / trace(Y_centered.T @ Y_centered)

# 4. Transformation
Y_aligned = s * Y_centered @ R + mean(H, axis=0)

# 5. Procrustes disparity
T = sqrt(sum((Y_aligned - H)^2) / sum(H^2))
```

**Generalized Procrustes Analysis (GPA)**:
- Simultaneously align multiple subjects to common space
- Iteratively update transformations and consensus target
- Used for HC super-participant construction (Phase 1)

### Three-Dimensional Decomposition

**1. Magnitude** (L2 norm ratio):
```python
magnitude_ratio = norm(CVD) / norm(HC)
```

**2. Sign/Baseline** (mean-centered patterns):
```python
baseline_diff = mean(CVD) - mean(HC)
```

**3. Structure** (RDM differences):
```python
RDM_cvd = pdist(CVD, metric='correlation')
RDM_hc = pdist(HC, metric='correlation')
structure_diff = correlation_distance(RDM_cvd, RDM_hc)
```

---

## Statistical Testing

### Permutation Test

**Null hypothesis**: CVD pattern = random permutation of HC patterns

**Procedure**:
```python
observed_T = procrustes_disparity(CVD, HC)
null_distribution = []
for i in range(1000):
    shuffled_HC = permute_colors(HC)
    null_T = procrustes_disparity(CVD, shuffled_HC)
    null_distribution.append(null_T)
p_value = mean(null_distribution >= observed_T)
```

**Results**:
- Sub-08 V1: T=0.132, p<0.001
- Sub-08 V2: T=0.178, p<0.001
- Sub-09 V1: T=0.115, p<0.001
- Sub-09 V2: T=0.113, p<0.001
- Sub-10 V1: T=0.101, p<0.001
- Sub-10 V2: T=0.117, p<0.001

---

## Implications

### For RQ3 (Personalized Filter Design)

**Individual heterogeneity** → **Subject-specific filters required**

Each CVD subject needs different loss function weights:
- **Sub-08**: High λ_structure (address geometric distortion)
- **Sub-09**: High λ_magnitude (address amplitude differences)
- **Sub-10**: Balanced λ weights

### For Future Phases

**SRQ1 success** → **Linear transformations sufficient** for Phase 1-3:
- Phase 1 (Hyperalignment): Use Procrustes/GPA for HC common space
- Phase 3 (Filter Optimization): Linear filter framework is appropriate

---

## Output Structure

```
analysis/phase2_procrustes_cvd_hc/
├── procrustes_results/
│   ├── sub-08_V1_transformation.npz
│   ├── sub-08_V2_transformation.npz
│   └── ... (all subjects, all ROIs)
├── permutation_tests/
│   ├── sub-08_V1_perm1000.npz
│   └── ...
└── figures/
    ├── circular_disparity_sub08_V1.png
    ├── activation_scatter.png
    └── procrustes_concept.pdf
```

---

## References

- **Gower, J. C. (1975).** Generalized procrustes analysis. *Psychometrika*, 40(1), 33-51.
- **Haxby, J. V., et al. (2011).** A common, high-dimensional model of the representational space in human ventral temporal cortex. *Neuron*, 72(2), 404-416.
