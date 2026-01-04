# Phase 2A: Learning Interpretable fMRI Pattern Transformations for CVD

**Date**: 2025-12-18
**Status**: Implementation-ready
**Focus**: Characterizing CVD-HC differences through learnable transformations

---

## 1. Final Recommended Approach

### Model Architecture

**Linear transformation in fMRI space:**

$$
\mathbf{F}^{(s)} = \mathbf{Y}^{(s)} \mathbf{A}^{(s)} + \mathbf{b}^{(s)}
$$

where:
- $\mathbf{Y}^{(s)} \in \mathbb{R}^{8 \times n}$: CVD subject $s$'s fMRI pattern (8 colors, $n$ voxels)
- $\mathbf{F}^{(s)} \in \mathbb{R}^{8 \times n}$: Transformed pattern
- $\mathbf{A}^{(s)} \in \mathbb{R}^{n \times n}$: Voxel-wise gain (subject-specific)
- $\mathbf{b}^{(s)} \in \mathbb{R}^{n}$: Baseline shift (subject-specific)

**Loss function:**

$$
L_{total}^{(s)} = \lambda_{mag} L_{mag} + \lambda_{base} L_{base} + \lambda_{rdm} L_{rdm}
$$

**Subject-specific weights** (from Phase 1 analysis):

| Subject | $\lambda_{mag}$ | $\lambda_{base}$ | $\lambda_{rdm}$ | Rationale |
|---------|-----------------|------------------|-----------------|-----------|
| Sub-08 | 0.2 | 0.3 | **0.5** | Structure-dominant (Yellow-Green collapse, z=-2.99) |
| Sub-09 | **0.5** | 0.3 | 0.2 | Magnitude-dominant (Red 132%, Yellow 114%) |
| Sub-10 | **0.5** | 0.3 | 0.2 | Magnitude-dominant (Chartreuse 70%, Magenta 69%) |

**Regularization:**

$$
L_{reg} = \alpha \|\mathbf{A} - \mathbf{I}\|_F^2 + \beta \|\mathbf{b}\|_2^2
$$

Encourages small deformations (hyperalignment principle).

---

## 2. Model Explanation

### Purpose

Learn a **subject-specific linear transformation** that maps CVD fMRI patterns to HC-like patterns. This transformation characterizes how CVD subjects' visual cortex representations differ from HC.

### Key Properties

1. **Interpretability**:
   - $\mathbf{A}$: Which voxels need gain adjustment?
   - $\mathbf{b}$: Which voxels have baseline shifts?

2. **Simplicity**: Linear model minimizes overfitting risk (8 colors × $n$ voxels data)

3. **Individual specificity**: Each CVD subject gets unique $(\mathbf{A}, \mathbf{b})$

4. **Validation-ready**:
   - Procrustes disparity: before/after comparison
   - Decoding accuracy: Use HC's W matrix on transformed patterns
   - RDM correlation: Structural similarity to HC

### Relation to Phase 1

**Phase 1** characterized differences:
- Magnitude: Per-color L2 norm ratios
- Structure: Procrustes disparity, RDM correlations
- Individual patterns: Sub-08 structure issues, Sub-09/10 magnitude issues

**Phase 2A** models these differences:
- Learn transformations that correct identified issues
- Validate if differences are learnable/correctable
- Quantify upper bound for Phase 2B performance

---

## 3. Notation

### Data

| Symbol | Dimensions | Description |
|--------|-----------|-------------|
| $\mathbf{Y}^{(s)}$ | $(8, n)$ | CVD subject $s$'s fMRI pattern (Phase 1 data) |
| $\mathbf{H}$ | $(8, n)$ | HC group mean pattern (target) |
| $\mathbf{H}_i$ | $(n,)$ | HC pattern for color $i$ |
| $\mathbf{Y}_i^{(s)}$ | $(n,)$ | CVD pattern for color $i$ |

### Parameters

| Symbol | Dimensions | Description |
|--------|-----------|-------------|
| $\mathbf{A}^{(s)}$ | $(n, n)$ | Transformation matrix (learnable) |
| $\mathbf{b}^{(s)}$ | $(n,)$ | Baseline shift (learnable) |
| $\lambda_{mag}$, $\lambda_{base}$, $\lambda_{rdm}$ | Scalar | Loss weights (subject-specific) |
| $\alpha$, $\beta$ | Scalar | Regularization weights |

### ROI Dimensions

| ROI | $n$ (voxels) | Subjects |
|-----|--------------|----------|
| V1 | 279 | All (sub-08, 09, 10) |
| V2 | 392 | All |
| V3 | ~250 | All |
| hV4 | ~200 | All |

**Note**: Each ROI trained separately.

---

## 4. Design Intent & Optimization Strategy

### Design Principles

1. **Minimal complexity**: Linear transformation only
   - 8 colors insufficient for nonlinear model
   - Interpretability critical for neuroscience contribution

2. **Hyperalignment-consistent**: Small deformation assumption
   - Regularization toward identity transformation
   - Preserves shared representational geometry

3. **Component orthogonality**: Three loss components measure distinct aspects
   - Magnitude: Per-color activation strength
   - Baseline: Condition-level DC shift
   - Structure: Color-pair relationships (RDM)

4. **Individual specificity**: Loss weights reflect Phase 1 findings
   - Data-driven personalization
   - Not arbitrary hyperparameter tuning

### Optimization Strategy

**Initialization:**
```python
A = torch.eye(n_voxels)  # Identity
b = torch.zeros(n_voxels)  # Zero baseline
```

**Optimizer**: Adam with learning rate 1e-3

**Training epochs**: 500-1000 (monitor convergence)

**Convergence criteria**:
- Total loss change < 1e-5 for 50 consecutive epochs
- Individual loss components stabilize

**Weight tuning**:
1. Start with Phase 1-informed weights (table above)
2. Grid search if initial weights suboptimal:
   - $\lambda_{mag} \in \{0.2, 0.3, 0.4, 0.5\}$
   - $\lambda_{base} = 0.3$ (fixed)
   - $\lambda_{rdm} \in \{0.2, 0.3, 0.4, 0.5\}$
   - Constraint: $\lambda_{mag} + \lambda_{base} + \lambda_{rdm} = 1.0$
3. Cross-validation: Leave-one-color-out
4. Select weights with best validation loss

---

## 5. Training Process

### Batch and Sample Units

**Training unit: Subject-level**

```python
# One training instance per subject
for subject in ['sub-08', 'sub-09', 'sub-10']:
    for roi in ['V1', 'V2', 'V3', 'hV4']:
        # Load data
        Y = load_cvd_pattern(subject, roi)  # (8, n_voxels)
        H = load_hc_mean_pattern(roi)       # (8, n_voxels)

        # Initialize model
        model = LinearTransform(n_voxels)

        # Training loop
        for epoch in range(max_epochs):
            F = model(Y)  # (8, n_voxels)
            loss = three_component_loss(F, H, weights)
            loss.backward()
            optimizer.step()
```

**Not run-level or trial-level**:
- Phase 1 data already averaged across runs (robust estimate)
- Each color has single pattern vector per subject
- Batch = all 8 colors simultaneously (no mini-batching)

### Data Structure

**Input data** (from Phase 1):
```
derivatives/group_level/
  sub-08/
    V1_pattern.npy  # (8, 279) - 8 colors, 279 voxels
    V2_pattern.npy  # (8, 392)
  sub-09/
    V1_pattern.npy
    ...
  HC_mean/
    V1_pattern.npy  # (8, 279) - target
    V2_pattern.npy
```

**Training outputs**:
```
derivatives/phase2a/
  sub-08/
    V1_A.npy        # (279, 279) - learned transformation
    V1_b.npy        # (279,) - learned baseline
    V1_loss_curve.png
    V1_metrics.json  # disparity, decoding accuracy, etc.
```

### Validation Strategy

**Leave-one-color-out cross-validation:**

```python
colors = ['Red', 'Yellow', 'Green', 'Cyan', 'Blue', 'Magenta',
          'Chartreuse', 'Orange']

for held_out_color in colors:
    # Train on 7 colors
    train_colors = [c for c in colors if c != held_out_color]
    Y_train = Y[train_colors]  # (7, n_voxels)
    H_train = H[train_colors]

    # Learn transformation
    model.train(Y_train, H_train)

    # Test on held-out color
    Y_test = Y[held_out_color]  # (1, n_voxels)
    H_test = H[held_out_color]
    F_test = model(Y_test)

    test_loss = three_component_loss(F_test, H_test, weights)
    validation_losses.append(test_loss)

# Average validation loss across 8 folds
mean_validation_loss = np.mean(validation_losses)
```

This tests generalization to unseen colors (critical for Phase 2B).

---

## 6. Background: Three-Component Framework

### Theoretical Foundation

**Hyperalignment literature** (Haxby et al., 2011; Guntupalli et al., 2016):
- Individual brains share common representational geometry
- Transformations between individuals are typically "small deformations"
- Linear transformations capture most variance

**Representational Similarity Analysis** (Kriegeskorte et al., 2008):
- Neural codes characterized by dissimilarity structures (RDM)
- Magnitude-invariant comparison through correlation-based RDM
- Captures "what is similar to what" relationships

### Why Three Components?

**Total pattern difference** can be decomposed:

$$
\|\mathbf{H} - \mathbf{F}\|_F^2 = \underbrace{\text{Magnitude term}}_{\text{Length differences}} + \underbrace{\text{Angular term}}_{\text{Direction differences}}
$$

**But**: Angular term conflates two distinct aspects:
1. **Baseline shift**: Overall activation level per condition
2. **Geometric structure**: Color-pair relationships

**Therefore**: Three orthogonal components

| Component | Measures | Invariances | Phase 1 Evidence |
|-----------|----------|-------------|------------------|
| **Magnitude** | Per-color L2 norm | Direction | Sub-08 Magenta 121%, Sub-09 Red 132% |
| **Baseline** | Per-color mean activation | Voxel polarity | Sub-08 Red: +0.044 (HC) vs -0.220 (CVD) |
| **Structure** | Color-pair dissimilarities | Magnitude & baseline | Sub-08 Yellow-Green collapse (z=-2.99) |

### Mathematical Decomposition

For a single color $i$:

$$
\|\mathbf{H}_i - \mathbf{F}_i\|_2^2 = (\|\mathbf{H}_i\|_2 - \|\mathbf{F}_i\|_2)^2 + 2\|\mathbf{H}_i\|_2 \|\mathbf{F}_i\|_2 (1 - \cos\theta_i)
$$

where $\theta_i$ is the angle between $\mathbf{H}_i$ and $\mathbf{F}_i$.

**Magnitude loss** isolates the first term.
**Baseline + Structure losses** decompose the angular term:
- Baseline: Mean activation differences (DC component)
- Structure: Mean-centered pattern differences (AC component)

---

## 7. Loss Components: Options & Selection

### Component 1: Magnitude Loss (Fixed)

**Definition:**

$$
L_{mag}(\mathbf{F}, \mathbf{H}) = \frac{1}{8} \sum_{i=1}^{8} \left( \|\mathbf{F}_i\|_2 - \|\mathbf{H}_i\|_2 \right)^2
$$

**Purpose**: Match per-color activation strength

**No alternatives**: This formulation is standard and optimal.

---

### Component 2: Baseline Loss (Fixed)

**Definition:**

$$
L_{base}(\mathbf{F}, \mathbf{H}) = \frac{1}{8} \sum_{i=1}^{8} \left( \mu(\mathbf{F}_i) - \mu(\mathbf{H}_i) \right)^2
$$

where $\mu(\mathbf{v}) = \frac{1}{n}\sum_{j=1}^{n} v_j$ (mean across voxels).

**Purpose**: Match condition-level baseline shifts (DC component)

**Terminology note**: Previously called "Sign loss" - changed to "Baseline loss" to avoid confusion with voxel-level polarity. This measures global activation shifts per color condition.

**No alternatives**: Standard DC component removal.

---

### Component 3: Structure Loss (Multiple Options)

**Purpose**: Match color-pair relationships (magnitude-free)

#### Option A: Per-Color Angular Distance

$$
L_{angle}(\mathbf{F}, \mathbf{H}) = \frac{1}{8} \sum_{i=1}^{8} \theta_i^2
$$

where:

$$
\theta_i = \arccos\left( \frac{\mathbf{F}_i \cdot \mathbf{H}_i}{\|\mathbf{F}_i\|_2 \|\mathbf{H}_i\|_2} \right)
$$

**Properties**:
- ✅ Magnitude-invariant (L2 normalization)
- ✅ Interpretable (direct angle measurement)
- ❌ Color-independent (treats each color separately)

**When to use**: Simple baseline, no specific color-pair issues identified

---

#### Option B: Variance Decomposition

$$
L_{var}(\mathbf{F}, \mathbf{H}) = \sum_{i=1}^{8} 2\|\mathbf{F}_i\|_2 \|\mathbf{H}_i\|_2 (1 - \cos\theta_i)
$$

**Properties**:
- ✅ Exact decomposition: $\|\mathbf{H} - \mathbf{F}\|_F^2 = L_{mag} + L_{var}$
- ✅ Norm-weighted (larger activations contribute more)
- ❌ Color-independent

**When to use**: Want provable orthogonality to magnitude loss

---

#### Option D: Mean-Centered RDM ⭐ **Selected**

**Definition:**

$$
L_{rdm}(\mathbf{F}, \mathbf{H}) = \| \text{vec}(\mathbf{D}_H) - \text{vec}(\mathbf{D}_F) \|_2^2
$$

where $\mathbf{D}$ is the Representational Dissimilarity Matrix:

$$
D_{ij} = 1 - \frac{\mathbf{v}_i' \cdot \mathbf{v}_j'}{\|\mathbf{v}_i'\|_2 \|\mathbf{v}_j'\|_2}
$$

with mean-centering: $\mathbf{v}_i' = \mathbf{v}_i - \mu(\mathbf{v}_i) \mathbf{1}$

**Properties**:
- ✅ Magnitude-invariant (correlation-based)
- ✅ Baseline-invariant (mean-centered)
- ✅ **Color-pair relationships explicitly constrained**
- ✅ Detects color confusions (e.g., Red-Green collapse)

**Computational cost**: $O(64n)$ vs $O(8n)$ for Options A/B (8× slower, but <1ms)

---

### Selection Rationale

**Why RDM (Option D)?**

1. **Phase 1 evidence**: Sub-08 shows systematic color-pair distortions
   - Yellow-Green collapse: z = -2.99 (***)
   - Green-Blue over-separation: z = +4.22 (***)
   - These are **pair-wise** relationships, not per-color issues

2. **Theoretical consistency**:
   - RSA framework standard in neuroscience
   - Hyperalignment literature uses correlation-based metrics
   - Directly measures "shared representational geometry"

3. **Robustness for Phase 2B**:
   - Encoding model (RGB → fMRI) will have errors
   - RDM constrains color-pair structure → prevents confusion collapse
   - Options A/B treat colors independently → color confusion possible

4. **Unified approach**:
   - All subjects use same structure loss (consistency)
   - Individual differences captured by **weights**, not different losses
   - Simpler implementation and comparison

**Validation in Phase 2A**:

Ablation study will compare:
- Model A: $\lambda_{mag}=0.4, \lambda_{base}=0.3, \lambda_{angle}=0.3$
- Model B: $\lambda_{mag}=0.4, \lambda_{base}=0.3, \lambda_{var}=0.3$
- Model D: $\lambda_{mag}=0.4, \lambda_{base}=0.3, \lambda_{rdm}=0.3$

Metrics:
- Procrustes disparity reduction
- RDM correlation improvement
- Decoding accuracy (HC W matrix)
- Leave-one-color-out validation loss

**Expected outcome**: RDM performs best for Sub-08, comparable for Sub-09/10, justifying unified selection.

---

## 8. Implementation Pseudocode

```python
import torch
import torch.nn as nn

class LinearTransform(nn.Module):
    def __init__(self, n_voxels, init='identity'):
        super().__init__()
        if init == 'identity':
            self.A = nn.Parameter(torch.eye(n_voxels))
            self.b = nn.Parameter(torch.zeros(n_voxels))
        elif init == 'random':
            self.A = nn.Parameter(torch.randn(n_voxels, n_voxels) * 0.01
                                   + torch.eye(n_voxels))
            self.b = nn.Parameter(torch.randn(n_voxels) * 0.01)

    def forward(self, Y):
        """
        Y: (8, n_voxels) - CVD pattern
        Returns: F (8, n_voxels) - transformed pattern
        """
        return Y @ self.A + self.b  # Broadcasting b across 8 colors

def magnitude_loss(F, H):
    """L_mag: Per-color L2 norm matching"""
    norm_F = torch.norm(F, dim=1)  # (8,)
    norm_H = torch.norm(H, dim=1)  # (8,)
    return torch.mean((norm_F - norm_H)**2)

def baseline_loss(F, H):
    """L_base: Per-color mean matching"""
    mean_F = torch.mean(F, dim=1)  # (8,)
    mean_H = torch.mean(H, dim=1)  # (8,)
    return torch.mean((mean_F - mean_H)**2)

def rdm_loss(F, H):
    """L_rdm: Mean-centered RDM matching"""
    def compute_rdm(patterns):
        # patterns: (8, n_voxels)
        # Mean-center each color
        patterns_centered = patterns - patterns.mean(dim=1, keepdim=True)

        # Compute correlation-based dissimilarity
        n_colors = patterns.shape[0]
        rdm = torch.zeros(n_colors, n_colors)

        for i in range(n_colors):
            for j in range(n_colors):
                if i == j:
                    rdm[i, j] = 0.0
                else:
                    vi = patterns_centered[i]
                    vj = patterns_centered[j]
                    corr = torch.dot(vi, vj) / (torch.norm(vi) * torch.norm(vj) + 1e-10)
                    rdm[i, j] = 1 - corr
        return rdm

    rdm_F = compute_rdm(F)
    rdm_H = compute_rdm(H)
    return torch.norm(rdm_F - rdm_H, p='fro')**2

def three_component_loss(F, H, weights, alpha=0.01, beta=0.01, A=None, b=None):
    """
    Complete loss with regularization

    weights: (lambda_mag, lambda_base, lambda_rdm)
    alpha, beta: regularization coefficients
    A, b: model parameters (for regularization)
    """
    lambda_mag, lambda_base, lambda_rdm = weights

    l_mag = magnitude_loss(F, H)
    l_base = baseline_loss(F, H)
    l_rdm = rdm_loss(F, H)

    loss = lambda_mag * l_mag + lambda_base * l_base + lambda_rdm * l_rdm

    # Regularization (encourage small deformation)
    if A is not None:
        n = A.shape[0]
        reg_A = alpha * torch.norm(A - torch.eye(n).to(A.device), p='fro')**2
        loss += reg_A

    if b is not None:
        reg_b = beta * torch.norm(b)**2
        loss += reg_b

    return loss, {
        'magnitude': l_mag.item(),
        'baseline': l_base.item(),
        'rdm': l_rdm.item(),
        'total': loss.item()
    }

# Training loop
def train_transformation(Y, H, weights, n_epochs=1000, lr=1e-3):
    """
    Y: (8, n_voxels) - CVD pattern
    H: (8, n_voxels) - HC target
    weights: (lambda_mag, lambda_base, lambda_rdm)
    """
    n_voxels = Y.shape[1]
    model = LinearTransform(n_voxels, init='identity')
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    loss_history = []

    for epoch in range(n_epochs):
        optimizer.zero_grad()

        F = model(Y)
        loss, components = three_component_loss(
            F, H, weights,
            A=model.A, b=model.b
        )

        loss.backward()
        optimizer.step()

        loss_history.append(components)

        if epoch % 100 == 0:
            print(f"Epoch {epoch}: {components}")

        # Early stopping
        if epoch > 50:
            recent_losses = [h['total'] for h in loss_history[-50:]]
            if max(recent_losses) - min(recent_losses) < 1e-5:
                print(f"Converged at epoch {epoch}")
                break

    return model, loss_history
```

---

## 9. Expected Outcomes

### Quantitative Metrics

**Primary outcomes:**

1. **Procrustes disparity reduction**:
   - Baseline (Phase 1): Sub-08 V1 d = 0.189
   - Target (Phase 2A): d < 0.15 (20%+ reduction)

2. **RDM correlation improvement**:
   - Baseline: r = 0.82 (Sub-08 V1)
   - Target: r > 0.90

3. **Decoding accuracy** (using HC W matrix):
   - Baseline: 45% (Sub-08, chance=12.5%)
   - Target: >60%

**Per-subject expectations:**

| Subject | Primary Issue | Expected Improvement |
|---------|---------------|---------------------|
| Sub-08 | Structure (RDM) | Large disparity reduction (20-30%) |
| Sub-09 | Magnitude | Moderate (15-20%), mostly magnitude correction |
| Sub-10 | Magnitude | Moderate (15-20%), similar to Sub-09 |

### Qualitative Insights

**Learned transformation ($\mathbf{A}$, $\mathbf{b}$) reveals**:

1. **Which voxels need correction?**
   - Diagonal elements of $\mathbf{A}$: Voxel-wise gain
   - Large deviations from 1.0 → problematic voxels

2. **What is the nature of deficit?**
   - $\mathbf{b}$ positive/negative: Baseline shift direction
   - Off-diagonal $\mathbf{A}$: Voxel interactions (if non-diagonal)

3. **Are deficits correctable?**
   - If loss decreases significantly → learnable transformation exists
   - If loss plateaus high → fundamental representational difference

### Validation for Phase 2B

**Phase 2A establishes upper bound**:
- Best-case scenario: Perfect encoding (RGB → fMRI)
- Phase 2B performance ≤ Phase 2A performance
- If Phase 2A fails → Phase 2B infeasible

**Critical decision point**:
- Phase 2A disparity reduction >20% → Proceed to Phase 2B
- Phase 2A disparity reduction <10% → Re-evaluate approach

---

## 10. Timeline & Deliverables

### Week 1-2: Implementation
- [ ] Code three loss components (magnitude, baseline, RDM)
- [ ] Implement LinearTransform model
- [ ] Training loop with regularization
- [ ] Validation framework (leave-one-color-out)

### Week 3: Experiments
- [ ] Train models for Sub-08, 09, 10 (V1, V2)
- [ ] Ablation study: RDM vs Angle vs Variance
- [ ] Weight tuning (grid search if needed)
- [ ] Convergence analysis

### Week 4: Analysis
- [ ] Compute metrics (disparity, RDM corr, decoding)
- [ ] Visualize learned A, b
- [ ] Compare subjects and ROIs
- [ ] Statistical tests (paired t-test, before/after)

### Week 5-6: Paper Writing
- [ ] Draft Methods section (Phase 2A)
- [ ] Results figures (loss curves, metrics, A/b heatmaps)
- [ ] Discussion (interpretability, limitations)
- [ ] Appendix (ablation study results)

**Deliverable**: Phase 2A manuscript ready for submission (~6 weeks)

---

## 11. Limitations & Future Directions

### Limitations

1. **Small sample size**: 8 colors × 1 pattern per subject
   - Limits model complexity (linear only)
   - Cross-validation critical

2. **fMRI space only**: Not directly applicable to real-world use
   - Phase 2B required for practical application

3. **ROI-specific**: Separate models per ROI
   - No cross-ROI generalization tested

4. **Static patterns**: No temporal dynamics
   - Phase 1 patterns averaged across time

### Future Directions

**Short-term (Phase 2B)**:
- Encoding model (RGB → fMRI)
- RGB filter learning
- Behavioral validation

**Long-term**:
- Nonlinear transformations (if more data available)
- Multi-ROI joint model
- Temporal dynamics inclusion
- Generalization to natural images

---

## References

1. Haxby, J. V., et al. (2011). A common, high-dimensional model of the representational space in human ventral temporal cortex. *Neuron*, 72(2), 404-416.

2. Guntupalli, J. S., et al. (2016). A model of representational spaces in human cortex. *Cerebral Cortex*, 26(6), 2919-2934.

3. Kriegeskorte, N., et al. (2008). Representational similarity analysis - connecting the branches of systems neuroscience. *Frontiers in Systems Neuroscience*, 2, 4.

4. Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003.

---

**Document Status**: Ready for implementation
**Next Action**: Begin Week 1 implementation tasks
