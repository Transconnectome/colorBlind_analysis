# Hyperalignment vs SRM: Methodological Comparison

**Purpose**: Compare two approaches for creating HC common representational space

## 배경 (Background)

**문제**: HC subjects have similar color structures (Procrustes stability: 0.91/0.88) but use different coordinate systems (RDM correlation: 0.26/0.24)

**목표**: Align HC subjects into unified representational space for:
1. Robust encoder learning across subjects
2. CVD projection and comparison
3. Phase 2-3 continuous hue prediction

---

## Method 1: Hyperalignment (Exploratory)

### 원리 (Principles)

**Core idea**: Iterative Generalized Procrustes Analysis (GPA)

**Algorithm**:
```python
1. Initialize common_space = first HC subject
2. For n_iter iterations:
   a. Align each HC to current common_space via Procrustes
   b. Update common_space = mean of aligned HC
   c. Check convergence
3. Project CVD as out-of-sample
```

**Key assumptions**:
- Row correspondence: Row i = same stimulus/trial across subjects
- Orthogonal transformations only (magnitude preserved)
- Full voxel space (NO PCA)

### 장점 (Advantages)

✅ **Simple**: Easy to understand and implement
✅ **Interpretable**: Orthogonal rotations maintain geometric properties
✅ **Magnitude-preserving**: L2 norms unchanged
✅ **No dimensionality choice**: Uses full voxel space

### 단점 (Disadvantages)

❌ **Current implementation uses run-averaged data (T=48)**:
   - This creates T << p problem (48 observations, 429 voxels)
   - Run effects ignored (run-to-run correlation ≈ 0.01)
   - Within-color variance = 88% (run effects dominate)

⚠️ **BUT: This can be fixed with stimulus-wise extraction**:
   - Extract individual trials: 8 stimuli/color × 8 colors × 6 runs = **384 trials**
   - T=384 vs p=429 → T/p = 89.5% (much better!)
   - Proper temporal correspondence across subjects
   - Run effects can be modeled explicitly

### 현재 상태 (Current Status)

**⚠️ NEITHER Hyperalignment NOR SRM is properly implemented yet**
- Current exploratory code in `future_phase1_hyperalignment/` uses run-averaged amplitudes (wrong)
- Stimulus-wise GLM extraction not yet conducted
- Run consistency check not yet performed

**Next steps** (from MASTER_PLAN.md):
1. Extract stimulus-wise patterns (LS-S GLM)
2. Check run-to-run consistency
3. THEN implement Hyperalignment AND SRM for comparison

---

## Method 2: Shared Response Model (SRM) [Recommended]

### 원리 (Principles)

**Core idea**: Probabilistic dimensionality reduction for shared responses

**Algorithm**:
```python
# BrainIAK SRM
from brainiak.funcalign.srm import SRM

srm = SRM(n_iter=10, features=k)  # k << p
srm.fit([X_1.T, X_2.T, ..., X_n.T])  # Each X: (T, p)

# Outputs:
# - Shared space: S (T, k)
# - Subject-specific mappings: W_s (p, k) for each subject
```

**Key assumptions**:
- Shared latent space S across subjects
- Subject-specific projections W_s
- Gaussian noise model

### 장점 (Advantages)

✅ **Handles T < p natively**: Built-in dimensionality reduction
✅ **Better sample efficiency**: T/k ratio improved
   - Example: T=384, k=30 → T/k=1280% (vs T/p=89%)

✅ **Regularization built-in**: Probabilistic framework inherently regularized
✅ **Literature-supported**: Proven for task-based fMRI alignment
✅ **Removes low-SNR dimensions**: Focuses on reliable variance
✅ **Run effects can be modeled**: Flexible covariate handling

### 단점 (Disadvantages)

❌ **Dimensionality choice**: Need to select k (hyperparameter)
❌ **Less interpretable**: Probabilistic latent space vs direct rotation
❌ **Computational cost**: Iterative EM-like algorithm
❌ **Black-box**: Not as transparent as Procrustes geometry

### 예상 개선점 (Expected Improvements)

**Sample efficiency** (with stimulus-wise extraction):
- Stimulus-wise: 384 observations → 429 parameters (0.89× slightly underdetermined)
- With SRM k=30: 384 observations → 30 parameters (12.8× overdetermined - excellent!)

**Robustness**:
- Automatic low-rank structure discovery
- Noise filtering through dimensionality reduction
- Less sensitive to trial-to-trial variability
- Run effects can be modeled as covariates

---

## Comparison Table

| Aspect | Hyperalignment | SRM |
|--------|---------------|-----|
| **원리** | Iterative orthogonal alignment | Probabilistic latent space |
| **T < p handling** | ✅ OK with stimulus-wise (T=384) | ✅ Native (dimensionality reduction) |
| **Sample efficiency** | T/p = 89% (stimulus-wise, acceptable) | T/k = 1280% (excellent with k=30) |
| **Interpretability** | ✅ High (geometric) | ❌ Lower (probabilistic) |
| **Assumption match** | ⚠️ Mixed (temporal) | ✅ Better fit (latent structure) |
| **Run effects** | ⚠️ Need explicit modeling | ✅ Can be modeled |
| **Literature support** | Mixed (not for trial-averaged) | ✅ Strong (task fMRI) |
| **Implementation** | ✅ Simple (scipy) | ✅ Easy (brainiak) |
| **Computational cost** | ✅ Low | ⚠️ Moderate |

---

## Recommendation

### Primary Approach: SRM (권장)

**Reasons**:
1. Better suited for T < p regime (even with stimulus-wise data)
2. Literature-supported for task-based fMRI
3. Built-in noise handling
4. Flexible for downstream analyses

**Implementation priority**:
```bash
prediction_model_workspace/scripts/
├── 02_srm_alignment.py          # New: SRM implementation
└── 03_compare_alignment.py      # Compare SRM vs Hyperalignment
```

### Secondary: Hyperalignment (비교용)

Implement with stimulus-wise data for comparison:
1. Use LS-S GLM for trial-wise extraction
2. Model run structure explicitly (if needed)
3. Regularize alignment
4. Compare with SRM results

### Evaluation Criteria (Both Methods)

**Tier-1 (Trial-level)**:
- Inter-subject correlation (ISC) > 0.30
- LOSO decoding > 25% (chance: 12.5%)

**Tier-2 (Color-level)**:
- Procrustes disparity < 0.08
- Run-split stability > 0.80
- RDM between-subject correlation > 0.30

**Downstream**:
- Common W reconstruction error ≤ baseline (32° for V1)

---

## Implementation Strategy

### Step 1: Data Preparation (Week 1)
- Implement LS-S GLM for stimulus-wise extraction
- Check run-to-run consistency
- Verify data quality (reliability checks)

### Step 2: Baseline Comparison (Week 2)
- Implement both methods
- Evaluate on same data (HC 5 subjects, V1)
- Compare alignment quality metrics

### Step 3: Downstream Validation (Week 3)
- Learn common encoder from each aligned space
- Compare Phase 2 prediction quality
- Identify winner or hybrid approach

### Step 4: Full Pipeline (Week 4)
- Extend to all ROIs (V1, V2, V3, hV4)
- CVD projection using best method
- Document decision and rationale

---

## Cross-References

**Detailed plans**:
- `../../prediction_model_workspace/docs/PHASE1_HYPERALIGNMENT.md`
- `../../prediction_model_workspace/MASTER_PLAN.md` (Phase 1 section)

**Critical analysis**:
- `CRITICAL_ISSUES_ANALYSIS.md` (Hyperalignment problems)
- `PROPER_APPROACH_BASED_ON_LITERATURE.md` (SRM recommendation)

**Quick start**:
- `../../prediction_model_workspace/QUICK_START.md` (Step-by-step execution)

---

**Last updated**: 2026-01-07
