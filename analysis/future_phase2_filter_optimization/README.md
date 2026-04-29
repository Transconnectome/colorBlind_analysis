# Future Phase 2: CVD Cone-Shift Pipeline & Stimulus-Space Filter

**SRQ4**: Can we fit a physiologically grounded cone-shift model to CVD fMRI data and derive a stimulus-space color correction filter?

**Status**: Active (Gen-4, Machado-anchored)
**Subjects**: Sub-08 (deutan), Sub-09 (protan), Sub-10 (normal control)
**Data**: C010 amplitudes (6 runs x 8 colors x n_voxels) from V1, V2, hV4

---

## Current Active Configuration (2026-04-16)

**Three models retained. One loss active. Luminance fix is visualization-only.**

### Models (all 3 live; all operate on CIELab L*=75, C*=40 ring)

| # | Name                | DOF | Level            | Forward map                                                                 |
|---|---------------------|-----|------------------|------------------------------------------------------------------------------|
| 1 | Machado 1-way       | 1   | Retinal (cone)   | `L_a(λ) = α·L(λ−Δλ) + (1−α)·k_L·M(λ)` (protan);  Δλ ∈ [0, 20 nm]             |
| 2 | R+C Retinal+Cortical| 2   | Retinal+cortical | `rg' = rg_0 + (1+g)·(rg_ret − rg_0)`;  `g=0` ≡ Machado;  `g<−1` overcompensation |
| 3 | 2-Component dilation | 2   | Stimulus-space    | `θ' = θ + β_s·cos(θ−90°) + β_c·cos(θ−θ_conf)`;  θ_conf = 16° protan, 150° deutan |

No hybrid, no Fourier warp, no additional DOF. Machado is the physiological anchor; 2-Component is the best behavioral/LOCO-aligned fit for both CVD subjects.

### Active Loss — `L_LOCO` (multi-objective, hV4, shift_at_both)

```
L_fit = α·L_vuln/4 + β·L_rank/2 + δ·L_rdm/2 + ε·L_smooth/32400
      = 1.0·L_vuln/4 + 0.5·L_rank/2 + 0.2·L_rdm/2 + 0.1·L_smooth/32400
```

| Term     | Weight | Meaning                                                            |
|----------|--------|---------------------------------------------------------------------|
| L_vuln   | 1.0    | MSE between simulated and observed per-color LOCO vulnerability     |
| L_rank   | 0.5    | 1 − Spearman ρ between simulated and observed vulnerability profiles|
| L_rdm    | 0.2    | 1 − cosine(ΔRDM_sim, ΔRDM_obs)                                      |
| L_smooth | 0.1    | Mean squared adjacent-difference of δθ (angular smoothness)        |

**Script**: `scripts/loco_distortion_fit.py`. **Fit target**: hV4 LOCO vulnerability profile. **Null**: label permutation.

### Filter pipeline (Phase B)

```
δ_fit(θ) from L_LOCO  →  pre-image search: θ_pre = argmin_θ' |forward(θ') − θ_target|
```

- 2-Component: exact pre-image (8/8) for both CVD subjects — **no arc compression**.
- Machado: pre-image OK for sub-08 (Δλ=1.5 nm); 4/8 exact for sub-09 (Δλ=13.5 nm, arc compression).
- R+C: pre-image 8/8 for sub-08 (Δλ=2.0, g=2.25).

### Visualization luminance fix (data-collection control only)

The `filter_visualization/` figures render the "CVD perceives" and "CVD(Filtered)" columns with a Machado-derived Δ L* (cone-response-equivalent Lab). This ensures the displayed swatch luminance reflects cone physics rather than a uniform CIELab ring.

**This is a display/data-presentation control**, not a constraint on the filter.
The filter itself operates in the 360° hue domain and does not need to match luminance — stimulus L* is clamped to 75 by the experimental protocol. The luminance-aware rendering exists only so that qualitative evaluators (e.g., sub-08's report) see the correct simulated percept.

### Subjects, parameters, and best-per-subject model

| Subject | CVD group  | Machado (Δλ nm) | R+C (Δλ, g)      | 2-Comp (β_s, β_c) | hV4 LOCO (best)          |
|---------|------------|------------------|--------------------|--------------------|---------------------------|
| sub-08  | deutan (mod) | 1.5             | (2.0, 2.25)        | (38°, −14°)        | **2-Comp, p=0.004**      |
| sub-09  | protan (mod) | 13.5            | (13.5, 0) ≡ Mach   | (6°, −22°)         | **Machado, p=0.018**     |
| sub-10  | normal       | ≈ 0             | —                  | —                   | NS (as expected)         |

Machado → R+C → 2-Component is a nested hierarchy (R+C reduces to Machado at g=0; 2-Component is independent). **All three are retained** because they probe different mechanistic levels (retinal cone / cortical opponent gain / stimulus-space dilation). The current filter is derived from whichever model wins L_LOCO per subject.

---

## Workflow Overview

```
Phase A: DISTORTION FITTING                Phase B: FILTER DERIVATION

  C010 amps + Stockman fundamentals          Pre-image search
          |                                  theta_in = argmin |D(theta) - theta_target|
          v                                          |
  Stage 0: Precompute                                v
  HC W, ΔRDM_obs, Stockman cache             Exact pre-image (2-Comp: 8/8 both subjects)
          |                                  or Separation optimization (Machado sub-09)
          v                                          |
  Stage 1: Model Fitting                             v
  Compare 5 candidate models              Phase C: FILTER EVALUATION
  (Machado / R+C / 2-Component /             Permutation tests
   Fourier / Hybrid)                         L_improve sanity check
          |                                  Specificity (sub-10 = identity)
          v                                  Behavioral JND concordance
  Stage 2: Dual-Criterion Validation
  L_LOCO (hV4 per-color vulnerability)
  L_ΔRDM (V1/V2 pairwise geometry)
          |
          v
  Stage 3: Cross-Validation
  LOHO, LORO, cross-ROI transfer
```

**Key design principle**: A distortion model that reproduces CVD vulnerability does NOT automatically yield a good corrective filter. The ΔRDM inverse failure (-37% to -153%) proved this. Therefore: fit distortion first, derive filter as pre-image, then independently verify improvement.

---

## Models

### 1. Machado 1-Way Cone Shift (1 DOF)

```
Protanomaly:  L_a(lambda) = alpha * L(lambda - Delta_lambda) + (1-alpha) * k_L * M(lambda)
Deuteranomaly: M_a(lambda) = alpha * M(lambda + Delta_lambda) + (1-alpha) * k_M * L(lambda)
```

Single spectral shift parameter Delta_lambda in [0, 20] nm. Based on Machado, Oliveira & Fernandes (2009) Eq 5/6.

### 2. R+C Retinal + Cortical Gain (2-3 DOF)

```
rg_final = rg_baseline + (1 + g) * (rg_ret - rg_baseline)
```

- `g = 0`: pure retinal (= Machado)
- `g = -1`: exact cortical compensation
- `g < -1`: overcompensation (Tregillus et al. 2021)
- `g > 0`: amplification (novel for hV4)

### 3. 2-Component Angular Dilation (2 DOF)

```
theta'(c) = theta_baseline(c)
           + beta_s * cos(theta_baseline(c) - 90)     [S-cone expansion]
           + beta_c * cos(theta_baseline(c) - theta_conf)  [Confusion axis]
```

- `theta_conf = 16 deg (protan), 150 deg (deutan)`
- Cortical-level model: bijective forward map (no arc compression)

### 4. Fourier Warp (4 DOF) — ablation ceiling only

```
delta(theta) = a1*sin(theta) + b1*cos(theta) + a2*sin(2*theta) + b2*cos(2*theta)
```

### 5. Hybrid Cone + 2-Component (3 DOF) — REJECTED

Components not additive. Cone shift becomes redundant or causes overfitting.

---

## Loss Functions

### L_LOCO: Multi-Objective LOCO Loss

**Script**: `scripts/loco_distortion_fit.py`
**Applied to**: All models on hV4 (shift_at_both)

```
L_fit = alpha * L_vuln/4 + beta * L_rank/2 + delta * L_rdm/2 + epsilon * L_smooth/32400
```

| Term     | Weight | Measures                           |
|----------|--------|------------------------------------|
| L_vuln   | 1.0    | MSE(vuln_sim, vuln_cvd)            |
| L_rank   | 0.5    | 1 - Spearman_rho (profile shape)   |
| L_rdm    | 0.2    | 1 - cosine(ΔRDM_sim, ΔRDM_obs)    |
| L_smooth | 0.1    | mean(adj_diff(delta_theta)^2)      |

**Purpose**: Per-color interpolation accuracy -> filter design criterion.

### L_ΔRDM: Cosine Similarity

**Script**: `scripts/comprehensive_2component_analysis.py`
**Applied to**: 2-Component on V1, V2 (separately and joint)

```
L = max cosine(ΔRDM_sim, ΔRDM_obs)
```

Permutation: 8! exact (40,320). Bootstrap CI: n=500.
**Purpose**: Pairwise distance geometry -> mechanism characterization.

### L3: Gen-4 Joint V1+V2 Loss

**Script**: `scripts/l3_loss.py` (L3_MachadoV1V2)
**Applied to**: Machado on joint V1+V2

```
L3 = L1 - lambda_scale * L_scale - lambda_ROI * L_ROI
L1 = 0.5 * sim(ΔRDM_sim_V1, ΔRDM_obs_V1) + 0.5 * sim(ΔRDM_sim_V2, ΔRDM_obs_V2)
```

**Purpose**: Cross-ROI consistency validation.

### L3v2: Gen-4.5 (with sign + family gates)

Adds `L_sign` (sign agreement) and `L_fam` (family discrimination margin). All 3 CVD subjects FAILED the 4-gate criterion -> ΔRDM + Machado structurally incompatible.

### L3rc: Retinal-Cortical Joint Loss

Adds coupling penalty `g^2 / (|mean_Delta_lambda| + epsilon)` and dominance regularizer. LOCO evaluated inline as post-hoc validation only.

---

## Results Summary

### Detection: All Models Converge

| Subject  | Machado    | R+C        | 2-Component | Fourier     |
|----------|------------|------------|-------------|-------------|
| sub-08   | p=0.058 t  | p=0.005**  | **p=0.004** | p=0.0002 (overfit) |
| sub-09   | **p=0.018** | = Machado | p=0.035*    | p=0.018*    |
| sub-10   | p=0.559    | --         | p=0.058 m   | --          |

All models detect distortion in sub-08/09 and null sub-10. **Detection is robust to model choice.**

### Correction Direction: Models Diverge

Machado/R+C vs 2-Component delta_theta: sign agreement 4/8, Spearman rho = -0.714.
Different mechanistic lenses (L-M cone axis vs S-cone/confusion axis) produce different correction prescriptions.

### Best Model by Subject

| Subject  | Primary Model                      | hV4 LOCO    | V1 LOCO     | V1 ΔRDM       |
|----------|-------------------------------------|-------------|-------------|----------------|
| **sub-08** | **2-Component** (beta_s=38, beta_c=-14) | **p=0.004** | **p=0.001** | CI excl 0      |
| sub-08   | R+C (Delta_lambda=2.0, g=2.25)     | p=0.005     | --          | p=0.179        |
| **sub-09** | Machado (Delta_lambda=13.5)        | **p=0.018** | --          | --             |
| sub-09   | 2-Component (beta_s=6, beta_c=-22) | p=0.035     | p=0.018     | **p=0.007***   |
| sub-10   | None                                | All NS      | p=0.058     | --             |

**2-Component is the ONLY model dual-validated (LOCO + ΔRDM) for both CVD subjects.**

### ΔRDM <-> LOCO Dissociation

```
             ΔRDM perm_p    LOCO V1 label_p
Sub-08:      0.179 (NS)     0.047* (SIG)    <- per-color accuracy > geometry
Sub-09:      0.026* (SIG)   0.197 (NS)      <- geometry > per-color accuracy
```

The two criteria share RDM information (L_LOCO includes L_rdm at delta=0.2) but weight it differently. This is a **sensitivity difference**, not a true dissociation.

### beta_s Cross-Subject Convergence

```
Sub-08 (deutan): beta_s = 20.0 +/- 8.0 deg
Sub-09 (protan): beta_s = 23.0 +/- 10.2 deg
Cross-subject mean: ~21.5 deg
Literature (Emery et al. 2021): 21.4 deg B-Y rotation
```

Independent methods (behavioral hue-scaling vs fMRI ΔRDM fitting) converge within 0.1 deg.

### Pre-Image Filter Results

| Model          | Sub-08 (deutan) | Sub-09 (protan)        |
|----------------|-----------------|------------------------|
| R+C            | 8/8 exact       | N/A (= Machado)        |
| Machado        | not primary     | 4/8 exact (**FAIL**)   |
| **2-Component** | **8/8 exact**  | **8/8 exact**          |

2-Component is the only model with exact pre-image for BOTH subjects. Cortical-level angular dilation has no arc compression (unlike Machado's L-cone shift which compresses 360 deg -> ~96 deg for sub-09).

**Under 2-Component, sub-09 is reclassified: "spectral filter required" -> "stimulus-space sufficient".**

### Biological Plausibility

| Parameter               | Our Value | Literature          | Match            |
|------------------------|-----------|---------------------|------------------|
| Sub-08 Delta_lambda    | 2.0 nm    | 1-4 nm (very mild)  | In range         |
| Sub-09 Delta_lambda    | 13.5 nm   | 9-14 nm (moderate)  | In range         |
| beta_s (both subjects) | 20-23 deg | 21.4 deg (Emery 2021) | **Within 0.1-3 deg** |
| Sub-09 g (V1)          | -1.10     | 20-40% overcomp     | Below, plausible |
| Sub-08 g (hV4)         | +2.25     | No precedent        | Novel            |

### Rejected Approaches

| Approach                   | Failure Mode                                      |
|---------------------------|---------------------------------------------------|
| ΔRDM inverse -> filter     | -37% to -153% (WORSE). Pairwise != per-color.    |
| Simple inverse (-delta)    | Assumes linearity. Nonlinear models need pre-image.|
| Hybrid (Cone + 2-Comp)     | Components not additive. Cone shift redundant.     |
| Gen-3 ΔRDM-only (Machado)  | 0/18 passed. ΔRDM_sim anti-correlates ΔRDM_obs.   |
| Fourier as primary          | 4 DOF / 8 colors = overfitting ceiling only.      |

---

## Next Steps

1. **Dual-filter behavioral comparison**: R+C vs 2-Component pre-image for sub-08
2. **2-Component LOCO -> JND concordance**: Does the vulnerability profile predict behavioral JND?
3. **LOHO robustness**: Sensitivity to individual HC in mean-HC

---

## References

1. Machado, Oliveira & Fernandes (2009). *IEEE TVCG*, 15(6), 1291-1298.
2. Tregillus et al. (2021). *Current Biology*, 31(5), 936-942.
3. Emery et al. (2021). *Vision Research*, 183, 1-12.
4. Boehm et al. (2014). *J. Vision*, 14(13), 19.
5. Somers et al. (2024). *Vision Research*. (EnChroma evaluation)
6. Diedrichsen et al. (2020). *NeuroImage*. (WUC method)
7. Walther et al. (2016). *NeuroImage*. (Crossnobis reliability)
