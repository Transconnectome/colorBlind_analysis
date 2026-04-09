# LOCO-Primary Filter Design Plan

**Date**: 2026-04-08 (revised 2026-04-08)
**Goal**: Design a stimulus-space filter for CVD color correction, optimized via LOCO vulnerability fitting at hV4, with post-hoc inverse validation.

**Narrative**: Neural distortion exists (RDM/ΔRDM) → LOCO identifies which distortion component predicts behavior (100% JND concordance) → **fit distortion to CVD LOCO profile** → **derive filter as inverse** → **independently verify that the inverse actually improves perception**.

**Critical design principle**: A distortion model that reproduces CVD vulnerability does NOT automatically yield a good corrective filter. The ΔRDM inverse failure (-37% to -153%) proved this. Therefore:
- **Fit stage**: target = CVD (reproduce observed vulnerability)
- **Derive stage**: filter = −δ_fit (candidate, not guaranteed)
- **Evaluate stage**: independently verify improvement (L_improve is a POST-FIT sanity check, NOT a training loss)

---

## WORKFLOW OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│ PHASE A: DISTORTION FITTING (target = CVD vulnerability)        │
│                                                                  │
│  STEP 0: Data Preparation                                       │
│  - Load HC W, CVD amplitudes, LOCO targets (hV4)               │
│  - Reuse step0_precompute outputs                               │
│                                                                  │
│  STEP 1: Model Selection                                        │
│  - Compare candidate distortion parameterizations               │
│  - Machado 1-DOF / 2-Component / R+C / Fourier warp            │
│  - Criterion: LOCO Spearman ρ at hV4 (shift_at_both)           │
│                                                                  │
│  STEP 2: Loss Function Design (DISTORTION FIT LOSS)             │
│  - L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth        │
│  - Target = CVD observed vulnerability                          │
│  - NO L_improve here (that's evaluation, not fitting)           │
│                                                                  │
│  STEP 3: Distortion Optimization                                │
│  - Primary: hV4 with shift_at_both                              │
│  - Grid search within physiological bounds                      │
│  - Sub-08 first, then sub-09                                    │
│  - Output: δ_fit(c) per color                                   │
├─────────────────────────────────────────────────────────────────┤
│ PHASE B: FILTER DERIVATION (δ_filter = −δ_fit + constraints)   │
│                                                                  │
│  STEP 4: Filter Derivation & Constraints                        │
│  - Initial candidate: δ_filter = −δ_fit                        │
│  - Constraints: no-harm, identity-near-normal, smoothness       │
│  - Cone-model inversion (if Machado/R+C) → direct remapping    │
├─────────────────────────────────────────────────────────────────┤
│ PHASE C: FILTER EVALUATION (independent verification)           │
│                                                                  │
│  STEP 5: Statistical Validation                                 │
│  - Permutation test: fitted distortion significant?             │
│  - L_improve sanity: does inverse ACTUALLY improve LOCO?        │
│  - Specificity: sub-10 filter ≈ identity                        │
│                                                                  │
│  STEP 6: Simulator Validation                                   │
│  - Apply filter to Machado-simulated CVD at Δλ = 0..20 nm      │
│  - Compare: unfiltered vs LOCO-filter vs ΔRDM-inverse-filter   │
│  - Report improvement_pct per color, per severity               │
│                                                                  │
│  STEP 7: Color Visualization                                    │
│  - Per-color Δθ bars (filter function)                          │
│  - Color wheel: original → filtered                             │
│  - Vulnerability heatmap: before/after filter                   │
│                                                                  │
│  STEP 8: Cross-Validation & Robustness                          │
│  - LOHO, cross-ROI transfer, JND prediction, bootstrap          │
└─────────────────────────────────────────────────────────────────┘
```

### Why this 3-phase structure?

**ΔRDM inverse failure root cause**: ΔRDM is a pairwise metric → inverting pairwise distances is ill-posed (28 constraints on 8 positions). A good ΔRDM fit produced a BAD inverse filter.

**LOCO is better-posed for inversion** because it's per-color (8 constraints on 8 positions), and each color's vulnerability directly maps to its positional error. But "better-posed" ≠ "guaranteed to work."

**Phase C exists because**: even with LOCO, the distortion field δ_fit was measured at stimulus angles θ(c). Applying filter −δ shifts stimuli to θ−δ, where the distortion may differ. The smooth model (Fourier/Machado) extrapolates, but this must be empirically verified.

---

## STEP 0: Data Preparation

### What to load
| Data | Source | Shape | Notes |
|------|--------|-------|-------|
| HC W matrices (hV4) | `step0_precompute/hc_W_hV4.npz` or recompute | {subj: (K, V_s)} | K=3 for hV4, ridge_gcv |
| HC amplitudes (hV4) | C010 `amplitudes_procrustes.npy` | {subj: (6, 8, V_s)} | V4 dir on disk |
| CVD LOCO target | `load_cvd_loco_target(subj, 'hV4')` | (8,) | Per-color voxel corr |
| C_original | `create_basis_full(K=3, basis='fe')` | (8, K) | Unshifted design matrix |
| ΔRDM_obs (hV4) | `compute_delta_rdm_obs()` | (28,) | For L_rdm regularizer |
| Stockman fundamentals | `load_stockman_fundamentals()` | wavelength grid | For Machado models |

### Validation of this step
- [ ] Reproduce known LOCO values: sub-08 hV4 = [0.573, -0.637, -0.733, -0.306, 0.250, -0.251, -0.759, -0.334]
- [ ] HC W matrix count = 7 (sub-01 to sub-07)
- [ ] Gray-point check passes for Machado simulator

---

## STEP 1: Model Selection — Filter Parameterization

### Candidates

| Model | DOF | θ → θ' transformation | Prior results at hV4 | Strengths | Weaknesses |
|-------|-----|----------------------|---------------------|-----------|-----------|
| **Machado 1-way** | 1 | Δλ-based spectral shift | shift_at_both p=0.036* (sub-08) | Physiological, published | 1 DOF may be insufficient; failed for sub-09 ΔRDM |
| **R+C** | 2 | Machado + opponent R-G gain | LOCO V1 p=0.047* (sub-08) | Mechanistic, g=compensation | g=-2.25 non-physiological for sub-08 |
| **2-Component Angular** | 2 | β_s·cos(θ-90°) + β_c·cos(θ-θ_conf) | ΔRDM p=0.007* (sub-09) | Good geometric fit | Anti-aligned with sub-09 LOCO vulnerability |
| **Fourier warp** | 4 | a₁sin(θ) + b₁cos(θ) + a₂sin(2θ) + b₂cos(2θ) | R²=0.817 on sub-08 2-Comp Δθ | Flexible, smooth | 4 DOF on 8 colors = tight; overfitting risk |
| **Cone-shift + 2-Comp hybrid** | 3 | Machado base + angular dilation | Exploratory | Combines mechanisms | 3 DOF → limited validation power |
| **Per-color (free)** | 7 | Independent δ(c) per color | Maximum flexibility | Oracle upper bound | Massively overfits; use as ceiling only |

### Selection criterion
- Fit each model to hV4 LOCO (sub-08) using shift_at_both
- Primary metric: Spearman ρ(vuln_sim, vuln_CVD)
- Secondary: 8! permutation p-value (label_perm and improvement)
- Select model with best ρ AND p < 0.05

### Decision logic
```
IF Machado 1-DOF p < 0.05 at hV4:
    → Use Machado (simplest, most publishable)
    → Add 2-Component as sensitivity analysis
ELIF R+C or 2-Component p < 0.05:
    → Use that model
    → Report Machado 1-DOF as negative control
ELIF Fourier 4-DOF p < 0.05 but simpler models fail:
    → Use Fourier with strong L_noharm + L_smooth regularization
    → Report as "data-driven filter" (less mechanistic)
ELSE:
    → Report negative result (filter not feasible at hV4)
    → Fall back to V1 W-fixed (sub-08 V1 p=0.047 already significant)
```

### Validation of this step
- [ ] All candidate models evaluated on same data/loss
- [ ] Per-color oracle (7-DOF) provides ceiling estimate
- [ ] Selected model has ≥ 3:1 data:parameter ratio (8 colors / DOF)
- [ ] Cross-validate: LOHO (leave-one-HC-out) stability of model ranking

### Literature justification
- **Why hV4 first**: Brouwer & Heeger (2009): V1 classification 0.93 but novel-color reconstruction drops to 0.45; V4 maintains performance. V4 has circular PCA color space; V1 does not. Bannert & Bartels (2018): only hV4 predicts trial-by-trial behavioral performance. Kim et al. (2020): V4/VO1 encodes perceived color, not physical stimulus.
- **Why LOCO as loss**: PCM framework (Diedrichsen & Kriegeskorte 2017) establishes cross-validated prediction accuracy as the normative fitting criterion. Brouwer & Heeger (2009) used LOO-run as primary evaluation. GCV for ridge (Golub et al. 1979) = LOO-based optimization. Our LOCO is a leave-one-condition-out variant.

---

## STEP 2: Loss Function Design (DISTORTION FIT — Phase A)

### Fit loss (target = CVD vulnerability profile)

```
L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth
```

**NOTE**: L_noharm and L_improve are NOT in the fit loss. They belong to Phase B (derivation constraints) and Phase C (evaluation), respectively. The fit stage only cares about reproducing CVD's observed distortion pattern.

### Component definitions

#### (a) L_vuln — Vulnerability profile matching (MSE) [PRIMARY]
```python
L_vuln = (1/8) * Σ_c (v_sim(c) - v_CVD(c))²
```
- v_sim(c): simulated per-color LOCO (mean-HC vuln with shifted C)
- v_CVD(c): CVD observed LOCO from validation
- **Why**: Forces absolute level matching, corrects bias (Diedrichsen et al. 2017: bias² + profile_mse decomposition already in codebase)
- **Reused function**: `mse_decompose()` at step1_fit_loco_v2.py:81

#### (b) L_rank — Ranking loss (1 - Spearman ρ) [SECONDARY]
```python
L_rank = 1 - ρ_Spearman(v_sim, v_CVD)
```
- **Why**: With n=8, rank-based is more robust than parametric correlation. Preserves vulnerability ordering even if absolute magnitudes differ.
- **Reused function**: `scipy.stats.spearmanr`
- **Note**: This is the EXISTING primary metric from `fit_mean_hc()`. Adding L_vuln upgrades from rank-only to rank+level.

#### (c) L_rdm — RDM structure regularizer [AUXILIARY]
```python
L_rdm = 1 - cosine(ΔRDM_sim(δ), ΔRDM_obs)
```
- **Why**: Ensures distortion field is consistent with overall representational structure, not just per-color matching.
- **Reused function**: `compute_delta_rdm_sim()`, `cosine_similarity()` from diagnostic_delta_rdm.py
- **Weight**: Low (δ=0.2). RDM→JND concordance is only 25%, so over-weighting RDM would hurt.

#### (d) L_smooth — Distortion smoothness [REGULARIZER]
```python
L_smooth = Σ_{c=0..6} (δ(c+1) - δ(c))²  # adjacent-color difference
```
- **Why**: Prevents jagged distortion fields that are physiologically implausible.
- **Note**: If using Fourier parameterization, smoothness is partially built-in (low-frequency basis). Still useful as explicit constraint for per-color or hybrid models.

### Recommended starting weights
```python
fit_weights = {
    'alpha': 1.0,    # L_vuln — primary (reproduce CVD vulnerability)
    'beta':  0.5,    # L_rank — secondary (preserve vulnerability ordering)
    'delta': 0.2,    # L_rdm — auxiliary (structural consistency)
    'epsilon': 0.1,  # L_smooth — regularizer (physiological plausibility)
}
```

### What is NOT in the fit loss (and why)
| Term | Where it belongs | Why not in fit |
|------|-----------------|---------------|
| L_noharm | Step 4 (filter derivation constraint) | Fit targets CVD distortion, not filter quality |
| L_improve | Step 5 (post-fit sanity check) | A good distortion fit ≠ good corrective inverse |
| L_identity | Step 4 (sub-10 near-identity constraint) | Specificity is a filter property, not distortion |

### Literature justification for distortion fit loss
- **PCM framework**: Diedrichsen & Kriegeskorte (2017) — cross-validated marginal likelihood as fitting objective. Our L_vuln + L_rank approximates this for a condition-wise LOO setting.
- **Regularized encoding**: Naselaris et al. (2011) — regularization (our L_smooth) prevents overfitting in encoding model parameter estimation.
- **Crossnobis target**: Walther et al. (2016) — cross-validated dissimilarity as unbiased fitting target. Our L_rdm uses crossnobis ΔRDM.
- **Multi-objective**: Schutt et al. (2023) — 2-factor CV prevents overfitting to both subjects and conditions. Our LOHO validation (Step 8) implements this.

---

## STEP 3: Distortion Optimization (Phase A)

### Method: shift_at_both (hV4)

```python
def loco_distortion_objective(params, model, cvd_vuln, hc_amps_dict,
                               cvd_type, delta_rdm_obs, fit_weights):
    """
    Fit distortion δ to reproduce CVD vulnerability profile.
    For each candidate δ (parameterized by `params`):
    1. Generate C_shifted from model(params)  — shifted design matrix
    2. For each HC subject:
       a. Retrain W_hc = ridge_gcv(C_shifted, hc_amps[train_runs])
       b. vuln[c] = corr(C_shifted[c] @ W_hc, hc_amps[:, c].mean(0))
    3. Mean across HC → v_sim (8,)
    4. Compute L_fit(v_sim, cvd_vuln, params, delta_rdm_obs, fit_weights)
    5. Return L_fit (minimize)
    """
```

**Critical note on shift_at_both**:
- W is retrained at every δ evaluation → ~50× slower than W-fixed
- BUT: This is what makes hV4 LOCO significant (p=0.009 for sub-09, p=0.036 for sub-08)
- W-fixed at hV4 K=3 is too weak (NS for both subjects)
- Estimated runtime: ~0.5s per evaluation × grid size

### Optimization strategy

| Model | Method | Grid/Bounds | Evaluations |
|-------|--------|-------------|-------------|
| Machado 1-DOF | Dense grid | Δλ ∈ [0, 20] step 0.5 | 41 |
| R+C | 2D grid | Δλ ∈ [0, 20] × g ∈ [-3, 1] step (0.5, 0.25) | ~41 × 17 = 697 |
| 2-Component | 2D grid | β_s ∈ [0, 50] × β_c ∈ [-50, 50] step 5° | ~11 × 21 = 231 |
| Fourier 4-DOF | L-BFGS-B | |a|,|b| ≤ 30° | ~100-500 iterations |
| Per-color oracle | Exhaustive | δ(c) ∈ [-30, 30] step 5° per color | 13⁸ → infeasible; use DE |

### Sub-08 first, then sub-09

**Sub-08 (deutan)**:
- High feasibility — cross-ROI ρ=0.929, JND validated
- All models can be tested; Machado init from LOCO Δλ=8.64nm
- Expected: Machado or 2-Component sufficient

**Sub-09 (protan)**:
- Moderate feasibility — no cross-ROI consistency, no JND
- Fourier or per-color may be needed (fixed models don't capture hV4 profile)
- Expected: LOCO improvement possible but model selection harder

### Validation of this step
- [ ] shift_at_both reproduces legacy results: sub-08 hV4 Δλ=8.64nm, r=0.690, p=0.036
- [ ] L_fit decreases monotonically during optimization
- [ ] Distortion magnitude |δ(c)| ≤ 30° for all colors (physiological bound)
- [ ] At least one model achieves label_perm_p < 0.05

---

## STEP 4: Filter Derivation & Constraints (Phase B)

### 4a. Initial filter candidate
```python
# δ_fit(c) from Step 3 = distortion that reproduces CVD vulnerability
# δ_filter(c) = −δ_fit(c)   (initial candidate via simple inversion)
```

### 4b. Constraint-based refinement

The raw inverse −δ_fit may not be optimal. Apply constraints:

#### No-harm constraint
```python
# Preserved colors (CVD LOCO > 0.1): sub-08 hV4 c0=red, c4=cyan
# Constraint: |δ_filter(c)| ≤ threshold for preserved colors
# Implementation: clip δ_filter at preserved colors to ±2°
L_noharm = (1/N_pres) * Σ_{c∈preserved} δ_filter(c)²
```

#### Identity-near-normal constraint (sub-10)
```python
# For sub-10 (normal control), distortion should be ≈ 0
# If δ_fit(sub-10) is non-zero, this flags false positive risk
# Constraint: if sub-10 |δ_fit| > 5°, investigate before proceeding
```

#### Smoothness constraint
```python
# δ_filter should be smooth in hue space (no jagged corrections)
# If using Fourier parameterization: already smooth by construction
# If per-color: apply adjacent-difference penalty
L_smooth_filter = Σ_{c=0..6} (δ_filter(c+1) - δ_filter(c))²
```

#### Cone-model inversion (if Machado/R+C)
```python
# For Machado 1-DOF: distortion = machado_shifted_hue(Δλ_fit)
# Inverse = machado_shifted_hue(-Δλ_fit) is NOT valid (Δλ≥0 only)
# Correct: find Δλ_correct such that:
#   machado_hue(Δλ_fit) ∘ machado_hue(Δλ_correct) ≈ identity
# This is a 1D search on [0, 20] — computationally trivial
# For R+C: similarly find (Δλ_correct, g_correct) such that composition ≈ identity
```

### 4c. Filter output
```python
filter_result = {
    'delta_fit': δ_fit,          # (8,) distortion from Step 3
    'delta_filter_raw': -δ_fit,   # (8,) raw inverse
    'delta_filter_constrained': δ_filter,  # (8,) after constraints
    'filter_params': {...},        # model-specific parameters
    'constraints_applied': [...],  # which constraints were active
}
```

### Validation of this step
- [ ] δ_filter is smooth (adjacent-difference < 10° everywhere)
- [ ] Preserved colors have |δ_filter| < 5°
- [ ] Sub-10 filter ≈ identity (mean |δ_filter| < 2°)
- [ ] For cone-model: composition test (distortion ∘ correction ≈ identity within 1°)

---

## STEP 5: Statistical Validation & L_improve Sanity (Phase C)

### Test 1: Distortion fit significance — Label permutation (8! = 40,320 exact)
```python
# Shuffle CVD color labels, recompute L_fit
# H0: Observed L_fit is not better than chance alignment
# p = (# null ≤ obs + 1) / (40321)
```
- **Reused function**: `permutation_test_spearman()` in step1_fit_loco_v2.py:261
- **Extend**: Apply to L_fit, not just Spearman ρ

### Test 2: Distortion improvement over baseline (Δρ > 0)
```python
# H0: Distortion model does not improve over δ=0
# Observed: Δρ = ρ(fitted) - ρ(baseline)
# Null: permuted Δρ distribution
```
- **Reused function**: `permutation_test_improvement()` in step1_fit_loco_v2.py:300

### Test 3: L_improve — POST-FIT sanity check (CRITICAL)
```python
# THIS IS NOT A TRAINING LOSS — it is an independent evaluation
# Does the derived filter actually improve LOCO?
#
# v_baseline(c) = mean-HC LOCO at original angles (no filter)
# v_filtered(c) = mean-HC LOCO at filtered angles (δ_filter applied)
# Δv(c) = v_filtered(c) - v_baseline(c)
#
# Check 1: mean Δv over vulnerable colors > 0 (improvement)
# Check 2: mean Δv over preserved colors ≥ 0 (no-harm)
# Check 3: overall mean Δv > 0 (net improvement)
#
# If Δv < 0 → FILTER FAILS (good distortion fit but bad inverse)
# → Same failure mode as ΔRDM, and we stop here

L_improve = mean_c [v_filtered(c) - v_baseline(c)]
# Positive = filter improves LOCO
# Negative = filter worsens LOCO → ABORT
```

**Why L_improve is in evaluation, not fitting**:
- If L_improve were in L_fit, the optimizer would directly optimize the filter (Option A), but we have no model of CVD's response to new stimuli
- In evaluation, L_improve verifies that the fitted distortion → inverse mapping actually works
- A negative L_improve is the most informative outcome: it means the distortion field, while accurate, does NOT invert well

### Test 4: Specificity (sub-10)
```python
# Run same pipeline on sub-10 (normal control)
# Expected: δ_fit ≈ 0 (no distortion) → δ_filter ≈ 0 (no correction)
# If sub-10 has large distortion → false positive risk
```

### Test 5: Per-color significance (Crawford & Howell)
```python
# For each color c: is CVD vuln(c) outside HC distribution?
# Crawford & Howell (1998) t-test for single-case vs control group
# Already implemented in Phase 1 (SRM analysis)
```

### Validation of this step
- [ ] Sub-08 hV4 label_perm_p < 0.05 for at least one model
- [ ] Sub-08 improvement_p < 0.05 (distortion > baseline)
- [ ] **L_improve > 0 for sub-08** (CRITICAL GATE — filter actually helps)
- [ ] Sub-10 distortion magnitude ≤ 2° mean (specificity)
- [ ] Sub-09: report even if NS (document as moderate feasibility)
- [ ] If L_improve < 0: STOP and report as "accurate distortion, non-invertible"

---

## STEP 6: Simulator Validation (Phase C continued)

### Method: Machado simulator sweep (same as validate_2component.py)

```python
for delta_lambda_true in [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20]:
    # 1. Simulate CVD perception (unfiltered)
    hue_cvd = machado_simulate_perception(stim_colors, delta_lambda_true, cvd_type)
    err_unfiltered = mean_angular_error(hue_cvd, hue_normal)

    # 2. Apply LOCO-optimized filter
    stim_filtered = apply_loco_filter(stim_colors, filter_params)
    hue_filtered = machado_simulate_perception(stim_filtered, delta_lambda_true, cvd_type)
    err_loco_filter = mean_angular_error(hue_filtered, hue_normal)

    # 3. Apply ΔRDM-inverse filter (previous approach, for comparison)
    stim_drdm = apply_drdm_inverse_filter(stim_colors, drdm_params)
    hue_drdm = machado_simulate_perception(stim_drdm, delta_lambda_true, cvd_type)
    err_drdm_filter = mean_angular_error(hue_drdm, hue_normal)

    # 4. Record
    improvement_loco = (err_unfiltered - err_loco_filter) / err_unfiltered * 100
    improvement_drdm = (err_unfiltered - err_drdm_filter) / err_unfiltered * 100
```

### Key comparisons
| Condition | What it tests |
|-----------|--------------|
| Unfiltered | Baseline CVD error |
| LOCO filter | New approach — does LOCO-optimized filter help? |
| ΔRDM inverse filter | Previous approach — confirmed to worsen (-37% to -153%) |
| No-CVD (Δλ=0) | No-harm: filter should add ≈ 0 error |

### Expected outcomes
- **LOCO filter**: improvement_pct > 0 at moderate Δλ (5-10nm) for sub-08
- **ΔRDM filter**: improvement_pct < 0 (replicates previous failure)
- **At Δλ=0**: LOCO filter error ≤ ΔRDM filter error (better no-harm due to L_noharm)

### Validation of this step
- [ ] ΔRDM inverse filter reproduces previous negative results (-36.7% sub-08)
- [ ] LOCO filter achieves improvement_pct > 0 at ≥ 3 severity levels
- [ ] At Δλ=0, LOCO filter error < 5° (no-harm threshold)
- [ ] Per-color breakdown shows improvement at vulnerable colors

---

## STEP 7: Color Visualization (Phase C continued)

### Figure 1: Filter function δ(θ)
- X-axis: hue angle (0-360°), Y-axis: filter shift δ (degrees)
- Plot continuous Fourier curve (if applicable) + discrete points at 8 stimulus colors
- Overlay: LOCO vulnerability profile (secondary Y-axis)
- Compare: LOCO filter vs ΔRDM inverse filter

### Figure 2: Color wheel before/after
- Inner ring: original 8 colors
- Outer ring: filtered colors
- Arrows showing shift direction and magnitude
- Mark vulnerable colors with asterisks

### Figure 3: Vulnerability heatmap
- 3 rows: baseline (no filter), LOCO filter, ΔRDM filter
- 8 columns: colors
- Cell color: green (good LOCO) → red (poor LOCO)
- Shows which colors improve, which are harmed

### Figure 4: Simulator sweep comparison
- X-axis: CVD severity (Δλ nm), Y-axis: mean angular error (degrees)
- 3 lines: unfiltered, LOCO filter, ΔRDM filter
- Shaded region: improvement zone (LOCO filter < unfiltered)
- Annotations: improvement_pct at key severities

### Figure 5: Per-color error radar
- Polar plot with 8 spokes (colors)
- 3 overlaid shapes: unfiltered, LOCO filter, ΔRDM filter
- Visually shows WHERE the improvement occurs

### Reused code
- `validate_2component.py`: machado_simulate_perception(), apply_inverse_filter_cielab()
- `visualize_cone_shift_colors.py`: STIM_LAB, lab2rgb
- `validate_v2_comprehensive.py`: plot structure templates

---

## STEP 8: Cross-Validation & Robustness (Phase C continued)

### (a) LOHO — Leave-One-HC-Out stability
```python
for hc_held_out in sub_01..sub_07:
    hc_train = all HC except held-out
    W_train = precompute_hc_W(hc_train_amps, C)
    filter_params_loho = optimize_loco_filter(W_train, cvd_vuln, ...)
    # Record: filter_params deviation from full-HC filter
```
- **Pass criterion**: filter params within 1 SD of full-HC estimates
- **Literature**: Schutt et al. (2023) 2-factor CV; prevents overfitting to HC composition

### (b) Cross-ROI transfer
```python
# Fit filter on hV4 LOCO → evaluate on V1 LOCO
filter_hv4 = optimize(loss_hv4, ...)
C_filtered = apply_filter(C_original, filter_hv4)
vuln_v1_filtered = simulate_mean_hc_wfixed(hc_W_V1, hc_amps_V1, C_filtered)
rho_transfer = spearmanr(vuln_v1_filtered, cvd_vuln_V1)
```
- **Expected sub-08**: positive transfer (cross-ROI ρ=0.929***)
- **Expected sub-09**: weak/no transfer (cross-ROI ρ NS)

### (c) JND prediction check (sub-08 only)
```python
# For each color pair in JND data:
#   Does filter reduce error at HYPO pairs?
#   Does filter preserve HYPER pairs?
for pair in ['orange-yellow', 'yellow-green', 'yellow-purple']:
    c1, c2 = pair_colors
    delta_vuln_c1 = vuln_filtered[c1] - vuln_baseline[c1]
    delta_vuln_c2 = vuln_filtered[c2] - vuln_baseline[c2]
    # Positive delta = improvement
```

### (d) Bootstrap parameter stability
```python
for boot_iter in range(500):
    hc_boot = resample(hc_subjects, n=7, replace=True)
    filter_boot = optimize(loss_boot, ...)
    record(filter_boot.params)
# Report: mean, SD, 95% CI of filter parameters
```

### Validation of this step
- [ ] LOHO: filter params SD ≤ 30% of mean (stable across HC subsets)
- [ ] Cross-ROI transfer: sub-08 V1 ρ > 0 (positive generalization)
- [ ] JND check: LOCO improves at ≥ 2/3 HYPO pairs (sub-08)
- [ ] Bootstrap CI: filter params exclude zero

---

## APPENDIX A: Key Literature References

### LOCO / CV as optimization criterion
1. **Diedrichsen & Kriegeskorte (2017)** — PCM: CV marginal likelihood as fitting objective
2. **Walther et al. (2016)** — Crossnobis: CV-based dissimilarity as fitting target
3. **Naselaris et al. (2011)** — CV prediction as normative encoding model criterion
4. **Golub, Heath & Wahba (1979)** — GCV for ridge parameter optimization
5. **Schutt et al. (2023)** — 2-factor CV for RSA model comparison
6. **Furst et al. (2022) CLOOB** — InfoLOOB: LOO-based training loss in contrastive learning

### hV4 as primary filter ROI
7. **Brouwer & Heeger (2009)** — V4 novel-color reconstruction; circular PCA color space
8. **Brouwer & Heeger (2013)** — V4 categorical clustering task-dependent
9. **Bannert & Bartels (2018)** — hV4 perceptual hub; only area predicting behavior
10. **Kuriki et al. (2015)** — V4 diverse hue selectivity vs V1 anisotropic
11. **Kim et al. (2020)** — V4/VO1 encodes perceived color, not physical stimulus

### Our prior results supporting this approach
12. **LOCO→JND 100% concordance** — Behavioral validation of LOCO criterion
13. **ΔRDM inverse filter failure** — Geometric inversion ≠ perceptual improvement
14. **hV4 shift_at_both significance** — sub-08 p=0.036, sub-09 p=0.009
15. **Cross-ROI consistency sub-08** — V1↔hV4 ρ=0.929***

---

## APPENDIX B: Existing Code Reuse Map

| Function | File | Used in Step |
|----------|------|-------------|
| `precompute_hc_W()` | step1_fit_loco_v2.py:155 | 0, 3 |
| `simulate_mean_hc_wfixed()` | step1_fit_loco_v2.py:211 | 3 (W-fixed variant) |
| `load_cvd_loco_target()` | step1_fit_loco_v2.py:398 | 0 |
| `permutation_test_spearman()` | step1_fit_loco_v2.py:261 | 4 |
| `permutation_test_improvement()` | step1_fit_loco_v2.py:300 | 4 |
| `mse_decompose()` | step1_fit_loco_v2.py:81 | 2 (L_vuln) |
| `lins_ccc()` | step1_fit_loco_v2.py:68 | 7 (robustness) |
| `compute_delta_rdm_obs()` | diagnostic_delta_rdm.py:197 | 0, 2 (L_rdm) |
| `compute_delta_rdm_sim()` | diagnostic_delta_rdm.py:231 | 2 (L_rdm) |
| `cosine_similarity()` | diagnostic_delta_rdm.py:282 | 2 (L_rdm) |
| `machado_shifted_hue()` | machado_simulator.py | 1, 3 |
| `machado_with_opponent_gain()` | retinal_cortical.py:55 | 1 (R+C model) |
| `get_design_matrix_rc()` | retinal_cortical.py:105 | 1 (R+C model) |
| `machado_simulate_perception()` | validate_2component.py:519 | 5 |
| `apply_inverse_filter_cielab()` | validate_2component.py:542 | 5, 6 |
| `filter_validation_sweep()` | validate_2component.py:554 | 5 |
| `create_basis_full()` | utils_forward_model.py:68 | 0, 3 |
| `load_amplitudes()` | utils_forward_model.py:46 | 0 |
| `STIM_LAB, lab2rgb` | visualize_cone_shift_colors.py | 6 |

### New code needed
| Script | Purpose | Phase | Estimated lines |
|--------|---------|-------|----------------|
| `loco_distortion_fit.py` | Distortion fitting (Steps 1-3) | A | ~400 |
| `loco_filter_derive.py` | Filter derivation + constraints (Step 4) | B | ~150 |
| `loco_filter_evaluate.py` | Statistical + L_improve + simulator (Steps 5-6) | C | ~350 |
| `loco_filter_visualize.py` | All figures (Step 7) | C | ~250 |
| `loco_filter_robustness.py` | LOHO, cross-ROI, JND, bootstrap (Step 8) | C | ~300 |
| `run_loco_filter.sbatch` | SLURM entry point | — | ~30 |

---

## APPENDIX C: Decision Points Requiring User Input

| Decision | Options | Default | When |
|----------|---------|---------|------|
| **Primary model** | Machado / R+C / 2-Comp / Fourier / all | All (compare) | Step 1 |
| **hV4 K value** | K=3 (SRM-optimal) or K=6 (standard) | K=3 | Step 0 |
| **shift_at_both vs W-fixed** | Both for sub-08; shift_at_both only for sub-09 | Both where possible | Step 3 |
| **No-harm constraint type** | Magnitude penalty vs preserved-color clipping | Preserved-color clipping | Step 4 |
| **Include sub-09** | Yes (with caveats) / sub-08 only | Yes | Step 3 |
| **Fourier DOF** | 2 (1st harmonic only) / 4 (2 harmonics) | 4 | Step 1 |
| **Permutation type** | Exact 8! / Bootstrap 10000 | Exact 8! | Step 5 |
| **L_improve gate** | Hard abort if < 0 / report as caveat | Hard abort | Step 5 |
| **Machado simulator in filter** | Apply filter to Machado simulation / skip | Apply | Step 6 |

---

## APPENDIX D: Risk Registry

| Risk | Impact | Mitigation |
|------|--------|-----------|
| shift_at_both too slow | Blocks grid search | Use coarse grid (step 1nm) → refine around peak |
| 4-DOF Fourier overfits | False positive | L_noharm + L_smooth + LOHO validation |
| Sub-10 filter non-zero | Specificity failure | Max-statistic correction; report as caveat |
| hV4 K=3 too few channels | Filter underperforms | Test K=6 as sensitivity analysis |
| Sub-09 LOCO remains NS | Cannot design filter | Document as negative result; focus paper on sub-08 |
| Machado simulator ≠ real CVD | Filter validation invalid | Caveat: "validated on simulator, behavioral test needed" |
