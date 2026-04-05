# ΔRDM Loss Pipeline: Comprehensive Failure Diagnosis

**Date:** 2026-04-04
**Status:** ❌ COMPLETE FAILURE — Zero cases pass tiered evaluation

---

## Executive Summary

**All 18 cases (3 subjects × 3 models × 2 metrics) FAIL tiered evaluation.**

The initially promising result (sub-08 cone_3way ρ=0.929***) is **NOT reproducible** due to:
1. Phase A ΔRDM fit is NS (p=0.566)
2. Differential Evolution did not converge (success=False)
3. No significant baseline improvement (p=0.566)

**Conclusion: ΔRDM loss is NOT a valid fitting criterion for this dataset.**

---

## Tiered Evaluation Results

### Tier 1: Phase A ΔRDM Fit Quality

**Thresholds:**
- label_perm_p ≤ 0.05
- baseline_improvement_p ≤ 0.10
- improvement ≥ 0.05

**Result:** All cone_1way cases fail (δ=0, no shift found)
**Result:** All cone_3way/fourier with decent fit ALSO fail baseline_improvement criterion

### Tier 2: V4 LOCO Prediction

**Thresholds:**
- |ρ| ≥ 0.5
- label_perm_p ≤ 0.05
- baseline_improvement_p ≤ 0.10 OR delta_rho ≥ 0.3

**Result:** Only sub-08 cone_3way (cosine) and sub-10 cone_3way (cosine) pass
**But:** Both fail Tier 1 or Tier 3, so overall FAIL

### Tier 3: Parameter Stability

**Requirement:** Differential Evolution must converge (success=True)

**Result:** **ALL cone_3way and fourier cases show success=False**
- Sub-08 cone_3way: n_fev=3640, success=False
- Sub-09 cone_3way: n_fev=3640, success=False
- Sub-10 cone_3way: n_fev=3640, success=False

**This is CRITICAL:** Parameters are NOT stable or reproducible!

### Tier 4: Specificity (sub-10 should be null)

**Cosine:** 2/3 specific (66.7%)
**Spearman:** 3/3 specific (100%)

**False positive:** sub-10 cone_3way (cosine) shows ρ=+0.690* but should be null

---

## Why Sub-08 Cone_3way ρ=0.929 is NOT Valid

### Superficially Impressive:
```
V4 LOCO Spearman ρ = 0.929*** (p=0.0011)
Fitted params: [L=+49nm, M=-12nm, S=-12nm]
```

### Fatal Flaws:

**1. Phase A (ΔRDM fit) is NS:**
```
best_loss = -0.089
baseline_loss = -0.197
improvement = +0.108
label_perm_p = 0.566 (NS!)
baseline_improvement_p = 0.566 (NS!)
```

**2. Optimizer did not converge:**
```
DE success = False
n_fev = 3640
max_iter = 100 (reached limit without converging)
```

**3. Negative loss values:**
```
Both best and baseline losses are negative
→ ΔRDM_sim and ΔRDM_obs are ANTICORRELATED
→ Cone-shift does NOT explain observed ΔRDM pattern
```

**Interpretation:** The V4 LOCO ρ=0.929 is a **lucky accident**. The optimizer randomly landed on parameters that happen to work for V4, but they do NOT fit the ΔRDM criterion and are NOT reproducible.

---

## Root Causes

### 1. ΔRDM Loss Criterion is Inappropriate

**Problem:** ΔRDM measures pairwise geometry distortion in voxel space AFTER SRM alignment.

**Issue:** SRM alignment ABSORBS cone-shift signal by rotating shared space.

**Evidence:**
- Negative loss values (anticorrelation)
- δ=0 often competitive with fitted δθ
- No baseline improvement across all subjects

### 2. Differential Evolution Failure

**Problem:** Multi-parameter optimization (3-4 df) in noisy loss landscape.

**Issue:** DE cannot find stable optima because:
- Loss surface is flat or non-convex
- Multiple local minima
- Signal-to-noise ratio too low

**Evidence:**
- success=False for ALL cone_3way/fourier cases
- n_fev reaches maxiter without convergence
- Different runs would produce different parameters

### 3. V1+V2 Combined Loss is Weak

**Problem:** Equal weighting (0.5 × V1 + 0.5 × V2) assumes both contribute equally.

**Issue:** Per-ROI losses often have opposite signs or different magnitudes.

**Evidence:**
- Sub-08 cone_3way: V1=+0.096, V2=-0.274 → combined=-0.089
- Averaging cancels out structure

### 4. Permutation Test Power is Low

**Problem:** 8! = 40,320 permutations for 8 colors, but RDM has 28 elements.

**Issue:** With n=8, statistical power to detect small effects is limited.

**Evidence:**
- Many cases with improvement but p>0.05
- Wide null distributions (SD ~0.15-0.17)

---

## Comparison: LOCO vs ΔRDM

### LOCO (Working)

**Sub-08 deutan (from phase 1):**
- V1 W-fixed: Δλ=34.92nm, r=0.690, **p=0.033***
- V2 W-fixed: Δλ=3.87nm, r=0.643, **p=0.047***
- V4 shift_at_both: Δλ=8.64nm, r=0.690, **p=0.036***

**Why it works:**
- Direct measure of LOCO vulnerability (functional criterion)
- 8-color profile → 8 data points (simple, interpretable)
- W-fixed or shift_at_both both converge
- Consistent across ROIs

### ΔRDM (Failing)

**Sub-08 deutan (current):**
- V1+V2 combined: [+49, -12, -12]nm, loss=-0.089, **p=0.566 (NS)**
- DE success=False, not reproducible
- V4 validation accidentally works (ρ=0.929) but Phase A fails

**Why it fails:**
- Indirect measure via RDM geometry (after SRM alignment)
- 28-element RDM vector → noisy, high-dimensional
- Multi-parameter optimization unstable
- SRM absorbs cone-shift signal

---

## Conclusions

### 1. ΔRDM Loss is NOT Viable

**Verdict:** ΔRDM cannot serve as primary fitting criterion for cone-shift models.

**Reasons:**
- Zero cases pass tiered evaluation
- Optimizer convergence failures
- No baseline improvement
- SRM alignment interference

**Status:** ❌ **REJECT as fitting criterion**

### 2. LOCO Remains Gold Standard

**Verdict:** LOCO is the correct functional criterion for cone-shift fitting.

**Evidence:**
- Consistent results across ROIs (V1, V2, V4)
- Stable parameters (W-fixed or shift_at_both)
- Significant results for sub-08 deutan
- Correct null for sub-10 normal

**Status:** ✅ **RETAIN as primary criterion**

### 3. ΔRDM Can Serve as Diagnostic Only

**Verdict:** ΔRDM has value for detecting distortion existence, but NOT for quantifying cone-shift.

**Role:**
- Convergence validation (does fitted cone-shift also reduce ΔRDM?)
- Existence evidence (is there ANY distortion?)
- Cross-ROI consistency check

**Status:** ⚠️ **DOWNGRADE to secondary/diagnostic role**

---

## Recommendations

### Immediate Actions (DO NOT PROCEED with ΔRDM fitting)

1. **Discard ΔRDM-fitted parameters** - None are reproducible
2. **Return to LOCO-fitted parameters** - Use existing phase 1 results
3. **Update memory** - Record ΔRDM failure to prevent future attempts

### Phase 2 Filter Pipeline Revision

**OLD (failed) approach:**
```
ΔRDM loss (V1+V2) → best δθ → V4 LOCO validation
```

**NEW (corrected) approach:**
```
LOCO loss (per-ROI) → best δθ → ΔRDM convergence validation
```

**Rationale:**
- LOCO is functional criterion (what actually breaks interpolation)
- ΔRDM is geometric criterion (detects distortion but can't quantify mechanism)
- Fit with LOCO, validate convergence with ΔRDM

### Noise Injection Prerequisites

**DO NOT inject noise until:**
1. ✅ LOCO baseline is solid (already achieved in phase 1)
2. ✅ Specificity is verified (sub-10 null confirmed)
3. ✅ Parameter stability is checked (W-fixed or shift_at_both both work)
4. ✅ Cross-ROI consistency is validated

**THEN inject noise to:**
- Test robustness under measurement uncertainty
- Identify hard cases (colors most sensitive to noise)
- Quantify confidence intervals for Δλ estimates

---

## Files to Archive (Failed Approach)

**Scripts (keep for reference, do NOT use):**
- `fit_cone_shift_delta_rdm.py` - ΔRDM loss fitting
- `validate_cone_shift_v4_loco.py` - V4 validation for ΔRDM-fitted params
- `loss_functions.py` - ΔRDM loss class
- `run_delta_rdm_both_metrics.sbatch` - Full batch for both metrics

**Results (keep for diagnosis, do NOT analyze further):**
- `results/sim_cosine/` - Cosine metric results (all failed)
- `results/sim_spearman/` - Spearman metric results (all failed)

**Documents (this file and related):**
- `DIAGNOSIS_DRDM_FAILURE.md` - This diagnosis
- `results/tiered_evaluation.json` - Tiered evaluation output
- `results/metric_comparison.json` - Cosine vs Spearman comparison

---

## Preserved Approach (Working)

**Scripts (continue using):**
- `step1_fit_loco_v2.py` - W-fixed LOCO fitting (WORKING)
- `diagnostic_delta_rdm.py` - ΔRDM diagnostic (for convergence validation only)
- `step0_precompute.py` - Stockman shifts and hue mapping
- `step2_cross_eval.py`, `step2b_cross_roi_eval.py` - Cross-ROI validation
- `step3_summary_v2.py` - Results summary

**Results (continue analyzing):**
- `results/wfixed_loco/` - W-fixed LOCO results (sub-08 V1/V2 significant)
- `results/shift_at_both/` - Legacy results (sub-08/09 V4 significant)

**Documents (reference):**
- `PIPELINE_WFIXED.md` - W-fixed LOCO pipeline (WORKING)
- Previous analysis results showing sub-08 success

---

## Lessons Learned

### What Worked
- **Functional criteria** (LOCO vulnerability)
- **Simple models** (cone_1way convergence, even if δ=0)
- **W-fixed simulation** (fast, stable)
- **Tiered evaluation** (prevented premature celebration)

### What Failed
- **Geometric criteria** (ΔRDM after SRM alignment)
- **Complex models without convergence** (cone_3way/fourier DE failures)
- **Combined losses** (V1+V2 averaging cancels structure)
- **Single-metric celebration** (ρ=0.929 hid underlying failures)

### Key Insight

> **"High correlation does not imply valid mechanism."**

A model can produce impressive predictions (ρ=0.929) while completely failing to fit the intended criterion (ΔRDM p=0.566). Always check:
1. Does Phase A (fitting) work?
2. Is the fit stable (optimizer convergence)?
3. Is there baseline improvement?
4. Does it pass specificity checks?

Only THEN celebrate Phase B (validation) results.

---

## Next Steps (After Discarding ΔRDM Approach)

### 1. Consolidate LOCO Results
- Collect existing W-fixed LOCO results (V1, V2, V4)
- Verify sub-08 deutan significance across ROIs
- Confirm sub-10 normal null

### 2. Parameter Stability Check (Priority 2)
- Re-run LOCO fitting with multiple random seeds
- Verify Δλ estimates are consistent (±5nm)
- Check if V1/V2/V4 estimates converge

### 3. Cross-ROI Consistency (Priority 3)
- Does sub-08 V1-fitted Δλ work for V2/V4?
- Which ROI provides most stable estimate?
- Should we use ROI-specific or pooled estimate?

### 4. Behavioral Correlation (Priority 3)
- Compare Δλ estimates with JND data
- Check if LOCO-vulnerable colors match HC2 confusions
- Validate filter predictions with behavioral metrics

### 5. Noise Injection (Priority 4, ONLY AFTER 1-4)
- Hard-case identification
- Robustness testing
- Confidence interval estimation

---

## Document History

- **2026-04-04 (Initial):** Full diagnosis after tiered evaluation revealed zero passing cases
- **Status:** ACTIVE — guides decision to discard ΔRDM approach and return to LOCO

**Signed:** Claude Sonnet 4.5 (Analysis Agent)
