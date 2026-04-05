# Tiered Evaluation: Detailed Failure Analysis

**Date:** 2026-04-04
**Total cases:** 18 (3 subjects × 3 models × 2 metrics)
**Passing cases:** **0**

---

## Evaluation Criteria

### Tier 1: Phase A ΔRDM Fit Quality
| Criterion | Threshold | Purpose |
|-----------|-----------|---------|
| `label_perm_p` | ≤ 0.05 | Fitted δθ better than random permutation |
| `baseline_improvement_p` | ≤ 0.10 | Fitted δθ better than δ=0 baseline |
| `improvement` | ≥ 0.05 | Minimum absolute improvement in loss |

### Tier 2: V4 LOCO Prediction Quality
| Criterion | Threshold | Purpose |
|-----------|-----------|---------|
| `\|spearman_rho\|` | ≥ 0.5 | Strong rank-order prediction |
| `label_perm_p` | ≤ 0.05 | Significant vs random permutation |
| `baseline_improvement_p` | ≤ 0.10 | Better than δ=0 baseline |
| `delta_rho` | ≥ 0.3 | Substantial improvement over baseline |

*Note: Tier 2 requires high ρ + significant p + (baseline_p OR delta_rho)*

### Tier 3: Parameter Stability
| Criterion | Requirement | Purpose |
|-----------|-------------|---------|
| DE `success` | True | Differential Evolution converged |
| For cone_1way | Always passes | Single parameter, no convergence issue |

### Tier 4: Specificity Check
| Criterion | Requirement | Purpose |
|-----------|-------------|---------|
| Sub-10 (normal) | NS or \|ρ\| < 0.3 | Control subject should show null |

---

## COSINE METRIC: Case-by-Case Analysis

### Sub-08 (Deutan)

#### cone_1way
| Tier | Status | Values | Failure Reason |
|------|--------|--------|----------------|
| **T1** | ❌ FAIL | label_p=0.7222, baseline_imp_p=0.7222, improvement=0.0000 | All three criteria fail: NS, no baseline improvement, zero improvement |
| **T2** | ❌ FAIL | ρ=0.429, label_p=0.1496, baseline_imp_p=0.4603, Δρ=0.071 | ρ too low (< 0.5), label_p NS, both baseline criteria weak |
| **T3** | ✅ PASS | cone_1way (single param) | Always passes |
| **Overall** | ❌ HOLD | | Failed T1 AND T2 |

**Best δθ:** [0.0] (no shift found)
**Interpretation:** Optimizer converged to δ=0, meaning no cone-shift explains ΔRDM

---

#### cone_3way ⚠️ (Initially appeared "best")
| Tier | Status | Values | Failure Reason |
|------|--------|--------|----------------|
| **T1** | ❌ FAIL | label_p=0.5660, baseline_imp_p=0.5660, improvement=+0.1075 | p-values NS despite +0.11 improvement |
| **T2** | ✅ PASS | ρ=**0.929***, label_p=0.0011**, baseline_imp_p=0.1165, Δρ=+0.571 | Strong ρ, significant, decent Δρ |
| **T3** | ❌ FAIL | DE success=**False**, n_fev=3640, n_iter=100 | **Optimizer did not converge!** |
| **Overall** | ❌ HOLD | | Failed T1 (NS fit) AND T3 (unstable) |

**Best δθ:** [L=+49.08nm, M=-11.81nm, S=-11.92nm]
**Phase A losses:**
```
best_loss:     -0.0894  (V1=+0.0956, V2=-0.2744)
baseline_loss: -0.1969  (V1=-0.2503, V2=-0.1435)
improvement:   +0.1075  (better but NS, p=0.566)
```

**Critical Issue:**
- ΔRDM fit itself is **NOT significant** (p=0.566)
- Both best and baseline losses are **NEGATIVE** (anticorrelated!)
- DE ran for 3640 function evaluations but **failed to converge**
- V4 LOCO ρ=0.929 is **accidental** - parameters don't actually fit ΔRDM

---

#### fourier
| Tier | Status | Values | Failure Reason |
|------|--------|--------|----------------|
| **T1** | ✅ PASS | label_p=**0.0015**, baseline_imp_p=**0.0015**, improvement=+0.1277 | Significant ΔRDM fit! |
| **T2** | ❌ FAIL | ρ=0.310, label_p=0.2309, baseline_imp_p=0.5411, Δρ=-0.048 | ρ too low, label_p NS, negative Δρ |
| **T3** | ❌ FAIL | DE success=**False**, n_fev=2445 | Optimizer did not converge |
| **Overall** | ❌ HOLD | | Failed T2 (weak V4 prediction) AND T3 (unstable) |

**Best δθ:** [a1=-7.73, b1=-29.93, a2=-28.45, b2=-30.00]
**Interpretation:** ΔRDM fit works, but doesn't predict V4 LOCO (different mechanisms)

---

### Sub-09 (Protan)

#### cone_1way
| Tier | Status | Values | Failure Reason |
|------|--------|--------|----------------|
| **T1** | ❌ FAIL | label_p=0.0719, improvement=0.0000 | Marginally NS (p=0.072), zero improvement |
| **T2** | ❌ FAIL | ρ=-0.095, label_p=0.6035, Δρ=-0.024 | Negative ρ, NS, negative Δρ |
| **T3** | ✅ PASS | cone_1way | Always passes |
| **Overall** | ❌ HOLD | | Failed T1 AND T2 |

**Best δθ:** [0.0] (no shift found)

---

#### cone_3way
| Tier | Status | Values | Failure Reason |
|------|--------|--------|----------------|
| **T1** | ✅ PASS | label_p=**0.0336***, improvement=+0.1067 | Significant ΔRDM fit |
| **T2** | ❌ FAIL | ρ=-0.310, label_p=0.7861, Δρ=-0.238 | Negative ρ, NS, negative Δρ |
| **T3** | ❌ FAIL | DE success=**False**, n_fev=3640 | Optimizer did not converge |
| **Overall** | ❌ HOLD | | Failed T2 (negative V4 prediction!) AND T3 |

**Best δθ:** [L=+44.14nm, M=+8.32nm, S=-4.76nm]
**Interpretation:** ΔRDM fit works, but V4 LOCO goes **opposite direction** (anticorrelated!)

---

#### fourier
| Tier | Status | Values | Failure Reason |
|------|--------|--------|----------------|
| **T1** | ✅ PASS | label_p=**0.0317***, improvement=+0.1214 | Significant ΔRDM fit |
| **T2** | ❌ FAIL | ρ=-0.524, label_p=0.9145, Δρ=-0.452 | Strong negative ρ, NS, large negative Δρ |
| **T3** | ❌ FAIL | DE success=**False**, n_fev=2445 | Optimizer did not converge |
| **Overall** | ❌ HOLD | | Failed T2 (strong anticorrelation!) AND T3 |

**Best δθ:** [a1=+6.14, b1=+8.00, a2=-1.60, b2=+3.39]
**Interpretation:** ΔRDM fit works, but V4 LOCO **strongly anticorrelated** (ρ=-0.52)

---

### Sub-10 (Normal Control) ⚠️ Specificity Check

#### cone_1way
| Tier | Status | Values | Failure Reason |
|------|--------|--------|----------------|
| **T1** | ❌ FAIL | label_p=0.1309, improvement=0.0000 | NS, zero improvement |
| **T2** | ❌ FAIL | ρ=-0.238, label_p=0.7318, Δρ=-0.238 | Low ρ, NS, negative Δρ |
| **T3** | ✅ PASS | cone_1way | Always passes |
| **Overall** | ❌ HOLD | | Failed T1 AND T2 |
| **Specificity** | ✅ PASS | NS (p=0.732) | Correctly null |

**Best δθ:** [0.0] (no shift found) ✅ Correct!

---

#### cone_3way ⚠️ **FALSE POSITIVE**
| Tier | Status | Values | Failure Reason |
|------|--------|--------|----------------|
| **T1** | ✅ PASS | label_p=**0.0221***, improvement=+0.1020 | Significant ΔRDM fit |
| **T2** | ✅ PASS | ρ=+**0.690***, label_p=**0.0347***, baseline_imp_p=0.1295, Δρ=+0.690 | Strong ρ, significant, large Δρ |
| **T3** | ❌ FAIL | DE success=**False**, n_fev=3640 | Optimizer did not converge |
| **Overall** | ❌ **FALSE_POSITIVE** | | Normal subject should be null! |
| **Specificity** | ❌ FAIL | Significant (p=0.035) | **Should be NS!** |

**Best δθ:** [L=+30.92nm, M=+42.88nm, S=+13.52nm]
**Critical Problem:** This is a **FALSE POSITIVE** - sub-10 is normal trichromat but shows significant result!

**Why it's invalid:**
1. Previous LOCO analysis: r=-0.048, p=0.561 ✓ (correct null)
2. Current ΔRDM: ρ=+0.690, p=0.035 ✗ (false positive)
3. DE did not converge (unstable parameters)
4. All positive shifts [+31, +43, +14] unusual (should have opposite signs for CVD)

---

#### fourier
| Tier | Status | Values | Failure Reason |
|------|--------|--------|----------------|
| **T1** | ✅ PASS | label_p=**0.0035**, improvement=+0.1242 | Significant ΔRDM fit |
| **T2** | ❌ FAIL | ρ=-0.595, label_p=0.9425, Δρ=-0.595 | Strong negative ρ, NS |
| **T3** | ❌ FAIL | DE success=**False**, n_fev=2445 | Optimizer did not converge |
| **Overall** | ❌ HOLD | | Failed T2 AND T3 |
| **Specificity** | ✅ PASS | NS (p=0.942) | Correctly null |

---

## SPEARMAN METRIC: Case-by-Case Analysis

*(Summary only - all 9 cases fail, similar patterns to cosine)*

### Key Differences from Cosine:

**Sub-09 cone_1way:**
- Cosine: δ=0 (null)
- Spearman: δ=**23nm** (label_p=**0.0073***) ← Found shift!
- BUT: V4 LOCO ρ=+0.095 (NS, p=0.420) ← Doesn't generalize

**Sub-10 cone_3way (specificity):**
- Cosine: ρ=+0.690* (FALSE POSITIVE)
- Spearman: ρ=-0.690 (NS, p=0.971) ✓ ← Correctly null

**Overall:**
- Spearman: 100% specificity (3/3 sub-10 cases are NS)
- Cosine: 67% specificity (2/3 NS, 1 false positive)
- BUT: Neither metric produces valid fits (all fail T1 or T3)

---

## Summary Statistics

### Pass/Fail by Tier (Cosine)

| Subject | Model | T1 | T2 | T3 | Overall |
|---------|-------|----|----|----|---------|
| sub-08 | cone_1way | ❌ | ❌ | ✅ | ❌ HOLD |
| sub-08 | cone_3way | ❌ | ✅ | ❌ | ❌ HOLD |
| sub-08 | fourier | ✅ | ❌ | ❌ | ❌ HOLD |
| sub-09 | cone_1way | ❌ | ❌ | ✅ | ❌ HOLD |
| sub-09 | cone_3way | ✅ | ❌ | ❌ | ❌ HOLD |
| sub-09 | fourier | ✅ | ❌ | ❌ | ❌ HOLD |
| sub-10 | cone_1way | ❌ | ❌ | ✅ | ❌ HOLD |
| sub-10 | cone_3way | ✅ | ✅ | ❌ | ❌ **FP** |
| sub-10 | fourier | ✅ | ❌ | ❌ | ❌ HOLD |

**Passing rate:**
- T1 only: 5/9 (56%)
- T2 only: 2/9 (22%)
- T3 only: 3/9 (33%) - all cone_1way
- **ALL tiers: 0/9 (0%)**

### Most Common Failure Modes

1. **Tier 1 failure (4 cases):** label_perm_p NS or zero improvement
   - All cone_1way cases (optimizer converges to δ=0)
   - Interpretation: No cone-shift explains ΔRDM

2. **Tier 2 failure (7 cases):** Low |ρ| or negative ρ
   - Even when T1 passes, V4 prediction fails
   - Some show strong **anticorrelation** (ρ < -0.4)
   - Interpretation: ΔRDM and LOCO measure different things

3. **Tier 3 failure (6 cases):** DE convergence failure
   - ALL cone_3way cases (3/3)
   - ALL fourier cases (3/3)
   - cone_1way always passes (1-parameter, no DE)
   - Interpretation: Loss landscape too flat/noisy for multi-parameter optimization

### Why Sub-08 cone_3way "Best Case" Failed

**Superficial success:**
- V4 LOCO ρ = **0.929*** (p=0.0011) ← Looks amazing!

**Hidden failures:**
1. **T1 FAIL:** ΔRDM fit is NS (p=0.566)
   - best_loss = -0.089 (negative!)
   - baseline_loss = -0.197 (also negative!)
   - improvement = +0.108 (but p=0.566, NS)

2. **T3 FAIL:** DE did not converge
   - success = **False**
   - n_fev = 3640 (many evaluations, still no convergence)
   - Parameters are NOT stable/reproducible

**Conclusion:** The ρ=0.929 is a **lucky accident**, not a valid mechanism.

---

## Key Insights

### 1. ΔRDM Loss ≠ LOCO Loss

**Evidence:**
- Sub-08 fourier: T1 pass (ΔRDM p=0.0015**), T2 fail (V4 ρ=0.31)
- Sub-09 fourier: T1 pass (ΔRDM p=0.0317*), T2 fail (V4 ρ=-0.52**)

**Interpretation:** ΔRDM and LOCO measure **different aspects** of distortion.
- ΔRDM: Pairwise geometry in voxel space (after SRM alignment)
- LOCO: Interpolation failure in color space (functional criterion)

### 2. SRM Alignment Absorbs Cone-Shift

**Evidence:**
- Negative loss values (anticorrelation)
- δ=0 competitive with fitted δθ
- V1+V2 components often have opposite signs

**Interpretation:** SRM rotates shared space to maximize correlation, which ABSORBS the geometric distortion that cone-shift would produce.

### 3. Multi-Parameter Models are Unstable

**Evidence:**
- ALL cone_3way cases: DE success=False (6/6)
- ALL fourier cases: DE success=False (6/6)
- cone_1way cases: always converge (but usually to δ=0)

**Interpretation:** Loss landscape is too flat or noisy for 3-4 parameter optimization. Signal-to-noise ratio insufficient.

### 4. Baseline Improvement is Critical Filter

**Evidence:**
- Sub-08 cone_3way: ρ=0.929 but baseline_imp_p=0.565 (NS)
- Sub-10 cone_3way: ρ=0.690 but baseline_imp_p=0.130 (NS)

**Interpretation:** High ρ without baseline improvement suggests:
- Overfitting
- Lucky parameter combination
- Not a true mechanism

**Rule:** **NEVER celebrate V4 ρ without checking baseline improvement first!**

---

## Recommendations

### 1. Discard ΔRDM-Fitted Parameters ❌
- None are reproducible (DE convergence failures)
- None have baseline improvement
- Sub-08 cone_3way ρ=0.929 is NOT valid

### 2. Return to LOCO-Fitted Parameters ✅
- Use existing phase 1 results (W-fixed or shift_at_both)
- Sub-08 V1/V2 significant (p=0.033, p=0.047)
- Sub-10 correctly null (p=0.561)

### 3. Use ΔRDM as Diagnostic Only ⚠️
- Check if LOCO-fitted δθ also reduces ΔRDM (convergence validation)
- Do NOT use ΔRDM as fitting criterion
- Do NOT trust ΔRDM-fitted parameters

### 4. Before Noise Injection 🛑
- Verify LOCO baseline stability
- Confirm parameter reproducibility (multiple seeds)
- Check cross-ROI consistency
- Validate specificity (sub-10 null)

---

## Document Status

- **Created:** 2026-04-04
- **Status:** ACTIVE - guides phase 2 pipeline revision
- **Action:** Discard ΔRDM fitting approach, return to LOCO

**End of detailed analysis**
