# Forward Model — Current Status & Next Steps

> Date: 2026-03-11 (updated: smooth_tikh investigation complete)
> Focus: HC encoder finalized (ridge_gcv). Next: CVD extension (adaptive basis) → Phase 2.

---

## Current Status ✅

### What's Complete
1. ✅ **Baseline pipeline** (Steps 1-4): ridge_gcv encoder, hV4 permutation-validated (p=0.044)
2. ✅ **Basis ablation** (§9c): FE-6 > LF-4 > LF-6 confirmed
3. ✅ **Extended models** (§9h): 4 prior-based + smooth_tikh tested
4. ✅ **Permutation tests**: ridge_gcv (done), smooth_tikh (done — ALL FAIL)
5. ✅ **smooth_tikh rescue attempts**: Centering (commutes), re-optimization (null beta stays high), RDM (misleading) — ALL FAILED
6. ✅ **RDM structure inspection**: Actual data has NO circular hue structure
7. ✅ **Final encoder decision**: **ridge_gcv confirmed, smooth_tikh REJECTED**

### Key Findings
- **ridge_gcv:** Only hV4 passes permutation (p=0.044); V1/V2 fail due to covariance baseline
- **smooth_tikh:** ALL improvements were artifacts of spatial covariance capture (not color signal)
- **RDM:** Actual data has no ideal circular hue structure; smooth_tikh predicted RDM anti-correlated with ideal (ρ ≈ -0.5)

### Resolved (was "Current Problem")
- **HC model:** ~~Need to decide~~ → **ridge_gcv confirmed**. smooth_tikh REJECTED after exhaustive investigation.
- **CVD model:** All encoders fail for CVD (LOCO ≤ 0), need CVD-specific development (adaptive basis §9k)

---

## smooth_tikh Investigation (RESOLVED — REJECTED)

### What Originally Looked Promising
1. RDM correlation improvement: V1 Δ+0.496, p=0.002
2. HC-CVD separation: V2 d=3.43, p=0.001
3. All 3 CVD subjects significant in V2

### Why It ALL Turned Out to Be Artifacts

**Permutation test (fixed params):** ALL ROIs fail (V1 p=0.331, V2 p=0.188, V3 p=0.613, V4 p=0.613). Observed ≈ null mean.

**Root cause:** β=100 forces near-rank-1 W → ALL predictions dominated by single shared spatial pattern → high voxel_corr from covariance, not color signal.

**Three rescue attempts — ALL FAILED:**

| Attempt | Finding | Why Failed |
|---------|---------|------------|
| Condition-centering | Commutes with shuffle | `mean(amp[:, perm, :], axis=1) == mean(amp, axis=1)` |
| Re-optimized permutation | Null selects β=1000 (45%!) | Smoothness helps fit any data |
| RDM-based evaluation | Predicted RDM anti-correlated with ideal (ρ ≈ -0.5) | rdm_pearson = noise pattern-matching |

**Critical RDM finding:** Actual data has NO ideal circular hue structure (all ROIs ρ ≈ 0 vs ideal). The rdm_pearson "improvement" was compressed smooth_tikh RDM matching actual noise structure.

**Conclusion:** The permutation test was **correct**. smooth_tikh genuinely captures only spatial covariance.

---

## CVD Model Development (After HC Validation)

### Problem
Current encoders fail for CVD subjects:
- ridge_gcv: V1=-0.012, V2=-0.174, V4=-0.058 (all ≤ 0)
- smooth_tikh: Slightly better (V3=+0.151, V4=+0.080) but still weak

### Hypothesis
CVD subjects have **distorted color axes** → fixed FE-6 basis at [0°, 60°, 120°, ...] is misaligned.

### Solution 1: Adaptive Basis Optimization (§9k-1) ⭐ **HIGH PRIORITY**

**Idea:** Optimize basis function centers per subject to match individual color geometry.

**Method:**
```python
def fit_adaptive_basis(X, n_channels=6):
    """
    Optimize basis centers to maximize LOCO cross-validation.

    Returns:
        centers_opt: (6,) array, e.g., [0, 55, 110, 180, 250, 305] for deutan
    """
    from scipy.optimize import minimize

    def objective(centers):
        C = create_basis_matrix(HUE_ANGLES, centers=centers)
        W = fit_W_ridge(C, X, alpha_gcv)
        loco_score = -evaluate_loco(W, C, X)

        # Regularization: penalize uneven spacing
        spacing_penalty = lambda_spacing * np.var(np.diff(sorted(centers)))

        return loco_score + spacing_penalty

    result = minimize(objective, centers_init=[0,60,120,180,240,300],
                     bounds=[(0,360)]*6, method='L-BFGS-B')
    return result.x
```

**Expected results:**
- **HC subjects:** centers ≈ [0°, 60°, 120°, 180°, 240°, 300°] (symmetric)
- **Deutan CVD:** compressed green-red, e.g., [0°, 55°, 110°, 180°, 250°, 305°]
- **Protan CVD:** compressed red-green differently

**Target:** CVD LOCO > 0 in at least 2 ROIs (currently all ≤ 0).

**Estimated time:** 3-4 days (implementation + validation)

---

### Solution 2: hV4-Informed Priors (§9j) 🎯

**Idea:** Use hV4's robust color representation to constrain V1/V2 encoding.

**Method 1: hV4-Adaptive Initialization**
```python
# Step 1: Optimize hV4 basis (works for both HC and CVD)
centers_hV4 = fit_adaptive_basis(X_hV4)

# Step 2: Initialize V1/V2 from hV4
centers_V1_init = centers_hV4  # Assume V1 follows hV4 color axes

# Step 3: Fine-tune V1 (small deviations allowed)
centers_V1 = fit_adaptive_basis(X_V1, centers_init=centers_V1_init,
                                lambda_prior=10)  # Stay close to hV4
```

**Advantage:**
- Reduces V1/V2 optimization DOF (6 free parameters → small deviations)
- Leverages hV4's validated signal (permutation p=0.044)
- Single framework for both HC and CVD

**Method 2: RDM-Constrained Fitting**
```python
# Step 1: Compute target RDM from hV4
RDM_target = compute_rdm(W_hV4 @ basis_full)

# Step 2: Fit V1 with RDM constraint
W_V1 = fit_with_rdm_constraint(X_V1, RDM_target, lambda_rdm)
```

**Priority:** MEDIUM (after adaptive basis §9k-1 implemented)

---

## Recommended Execution Plan

### ~~Phase 1b: HC Model Validation~~ COMPLETE

**HC encoder decision: ridge_gcv confirmed.** smooth_tikh REJECTED after exhaustive investigation.

---

### Phase 1c: CVD Model Development (Next)

| Week | Task | Output | Target |
|------|------|--------|--------|
| **Week 3** | Implement adaptive basis (§9k-1) | `fit_adaptive_basis.py` | — |
| **Week 3** | Test on HC subjects (sanity check) | Centers ≈ [0,60,120,...] | Validate implementation |
| **Week 3-4** | Test on CVD subjects | Centers show compression | — |
| **Week 4** | Validate LOCO (adaptive vs fixed) | CVD LOCO improvement | LOCO > 0 in 2+ ROIs |
| **Week 4** | Optional: hV4-informed variant (§9j) | Hierarchical adaptive | Reduce overfitting |

**Deliverable:** CVD encoder (if successful) OR explicit HC-only limitation documented.

---

### Phase 2: Filter Optimization (After CVD model)

**Encoder:** ridge_gcv (confirmed)
- HC: ridge_gcv, hV4 = primary ROI (p=0.044), V1/V2 = conditional
- CVD: Adaptive basis (if §9k-1 succeeds) OR HC encoder with caveats

**Primary metric:** voxel_corr (validated by permutation test)

**Scope:**
- HC validation (required)
- CVD exploratory (if adaptive basis works)

---

## Key Decisions

### Decision 1: HC Encoder ✅ RESOLVED
- [x] **ridge_gcv confirmed** — hV4 validated (perm p=0.044), V1/V2 conditional
- [x] smooth_tikh REJECTED — all rescue attempts failed

### Decision 2: CVD Model Strategy (§9k-1 outcome) — PENDING
- [ ] Adaptive basis → unified HC-CVD framework
- [ ] hV4-only for CVD → single validated ROI
- [ ] HC-only Phase 2 → CVD as exploratory

**Blocker:** Adaptive basis implementation & validation

### Decision 3: Phase 2 Evaluation Metric ✅ RESOLVED
- [x] **voxel_corr (primary)** — validated by permutation test
- [x] RDM correlation (secondary/descriptive only)

---

## Files Updated

1. ✅ **PLAN.md** — §9i updated with smooth_tikh investigation results
2. ✅ **RESULTS.md** — smooth_tikh permutation + rescue attempts + RDM inspection documented
3. ✅ **ANALYSIS_smooth_tikh_paradox.md** — Resolved: all "improvements" were covariance artifacts
4. ✅ **notion.md** — smooth_tikh gate REJECTED, §9 investigation results added
5. ✅ **SUMMARY_next_steps.md** — This document

## Next Actions

### Immediate
1. 🎯 **Implement `fit_adaptive_basis.py`** (scipy.optimize, LOCO objective) — §9k-1
2. 🎯 **Test adaptive basis on HC subjects** (sanity check: centers ≈ symmetric)
3. 🎯 **Test on CVD subjects** → determine if basis distortion detectable

### After CVD Model
1. 🎯 **Phase 2 filter optimization** with ridge_gcv encoder (frozen)
2. 🎯 **HC validation** (required)
3. 🎯 **CVD exploratory** (if adaptive basis succeeds)

---

## Summary

**HC encoder decision: ridge_gcv confirmed.** smooth_tikh REJECTED after exhaustive investigation (permutation FAIL + centering commutes + re-optimization doesn't help + RDM misleading).

**Key lesson:** Permutation test was correct all along. smooth_tikh's ALL "improvements" (voxel_corr, rdm_pearson, HC-CVD separation) were driven by shared spatial covariance capture, not color signal.

**Next:** CVD model development (adaptive basis §9k-1) → Phase 2 filter optimization.
