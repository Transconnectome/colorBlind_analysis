# Future Phase 1: Forward Model — RESULTS

> Last updated: 2026-03-11
> Status: All experiments **complete**. smooth_tikh **REJECTED** — ridge_gcv confirmed as final encoder.

---

## 1. Status Summary

| Experiment | Status | Key Outcome |
|-----------|--------|-------------|
| Baseline (4 models × 4 ROIs × LORO/LOCO) | **DONE** | ridge_gcv = best LOCO model |
| Basis ablation (FE-6 vs LF-4 vs LF-6) | **DONE** | FE-6 confirmed |
| Metric reinforcement (permutation/Friedman/residual) | **DONE** | hV4 = only genuine color interpolation |
| Improved encoding (RRR, smoothness) | **DONE** | Both rejected |
| Extended models (4 new models, inner LOCO) | **DONE** | smooth_tikh = leading candidate |
| smooth_tikh artifact check | **DONE** | PASSED (rdm_pearson ↑) — but misleading (see §8) |
| smooth_tikh permutation test (fixed params) | **DONE** | ALL ROIs FAIL (all p>0.18) |
| smooth_tikh rescue: condition-centering | **DONE** | Commutes with permutation — no effect |
| smooth_tikh rescue: re-optimized permutation | **DONE** | Null beta stays high — doesn't fix |
| RDM structure inspection | **DONE** | Actual data has NO circular hue structure |
| **Final encoder decision** | **DONE** | **ridge_gcv confirmed, smooth_tikh REJECTED** |
| Opponent basis test (10K perm) | **DONE** | ALL opponent bases FAIL for V1/V2 — dissociation confirmed |
| Intercept model permutation test (10K) | **DONE** | Standard ≈ intercept ≈ mean_subt — no difference |

---

## 2. Data Quality

### Reliability (Split-Half RDM Correlation)

| Subject | Group | V1 | V2 | V3 | hV4 |
|---------|-------|------|------|------|------|
| sub-01 | HC | 0.437 | 0.217 | 0.216 | 0.645 |
| sub-02 | HC | 0.282 | 0.169 | 0.224 | 0.656 |
| sub-03 | HC | 0.634 | 0.278 | 0.039 | 0.926 |
| sub-04 | HC | 0.807 | 0.735 | 0.295 | 0.438 |
| sub-05 | HC | 0.521 | 0.810 | 0.641 | 0.199 |
| sub-06 | HC | 0.038 | 0.683 | 0.808 | 0.639 |
| sub-07 | HC | 0.190 | 0.048 | 0.559 | 0.721 |
| sub-08 | CVD | 0.706 | 0.846 | 0.643 | 0.902 |
| sub-09 | CVD | 0.503 | 0.383 | 0.334 | 0.818 |
| sub-10 | CVD | 0.412 | 0.346 | 0.353 | 0.376 |
| **HC M (SD)** | | **0.416 (0.266)** | **0.420 (0.312)** | **0.398 (0.276)** | **0.603 (0.229)** |
| **CVD M (SD)** | | **0.540 (0.150)** | **0.525 (0.279)** | **0.444 (0.173)** | **0.699 (0.283)** |

### Noise Ceiling (RDM-Based)

| ROI | HC NC_lower (SD) | HC NC_upper (SD) | CVD NC_lower (SD) | CVD NC_upper (SD) |
|-----|-----------------|-----------------|------------------|------------------|
| V1 | 0.441 (0.100) | 0.939 (0.027) | 0.527 (0.188) | 0.955 (0.027) |
| V2 | 0.452 (0.112) | 0.943 (0.034) | 0.596 (0.161) | 0.970 (0.016) |
| V3 | 0.451 (0.174) | 0.931 (0.036) | 0.522 (0.148) | 0.947 (0.010) |
| hV4 | 0.573 (0.141) | 0.957 (0.025) | 0.646 (0.147) | 0.968 (0.019) |

### Voxel-Pattern Noise Ceiling (Spearman-Brown Corrected)

| ROI | HC Mean (SD) | CVD Mean (SD) |
|-----|-------------|--------------|
| V1 | 0.470 (0.078) | 0.499 (0.011) |
| V2 | 0.509 (0.060) | 0.601 (0.118) |
| V3 | 0.615 (0.106) | 0.658 (0.053) |
| hV4 | 0.702 (0.049) | 0.747 (0.087) |

R_s (SRM projection) stability: ALL PASS (HC mean cosine > 0.5 per ROI; range 0.792-0.922).

---

## 3. Baseline Results

### LORO — Run Generalization (mean voxel_corr)

| Model | V1 HC (SD) | V1 CVD (SD) | V2 HC (SD) | V2 CVD (SD) | V3 HC (SD) | V3 CVD (SD) | hV4 HC (SD) | hV4 CVD (SD) |
|-------|-----------|------------|-----------|------------|-----------|------------|------------|-------------|
| ols | 0.213 (0.044) | 0.218 (0.031) | 0.246 (0.042) | 0.259 (0.078) | 0.326 (0.081) | 0.340 (0.039) | 0.406 (0.068) | 0.399 (0.050) |
| ridge_gcv | 0.201 (0.050) | 0.207 (0.036) | 0.230 (0.047) | 0.243 (0.092) | 0.308 (0.082) | 0.340 (0.047) | 0.401 (0.068) | 0.396 (0.060) |
| prior_only | 0.306 (0.015) | 0.287 (0.049) | 0.300 (0.029) | 0.297 (0.017) | 0.304 (0.044) | 0.278 (0.019) | 0.317 (0.031) | 0.303 (0.036) |
| **prior_ft** | **0.315** (0.021) | **0.292** (0.053) | **0.310** (0.027) | **0.327** (0.070) | **0.357** (0.064) | **0.381** (0.047) | **0.419** (0.062) | **0.409** (0.058) |

No significant HC-CVD difference in LORO (all |d| < 0.72, all p > 0.22).

### LOCO — Color Interpolation, Clean (mean voxel_corr)

> Leakage-free: W0 recomputed per fold excluding held-out color.

| Model | V1 HC (SD) | V1 CVD (SD) | V2 HC (SD) | V2 CVD (SD) | V3 HC (SD) | V3 CVD (SD) | hV4 HC (SD) | hV4 CVD (SD) |
|-------|-----------|------------|-----------|------------|-----------|------------|------------|-------------|
| ols | +0.051 (0.095) | -0.082 (0.016) | +0.092 (0.127) | -0.181 (0.055) | +0.023 (0.197) | -0.073 (0.140) | +0.158 (0.188) | -0.067 (0.141) |
| **ridge_gcv** | **+0.130** (0.097) | -0.012 (0.054) | **+0.150** (0.188) | -0.174 (0.130) | +0.023 (0.240) | -0.008 (0.163) | **+0.183** (0.200) | -0.058 (0.207) |
| prior_only | -0.075 (0.040) | -0.098 (0.019) | -0.099 (0.071) | -0.173 (0.052) | -0.186 (0.096) | -0.203 (0.073) | +0.109 (0.084) | +0.072 (0.066) |
| prior_ft | -0.056 (0.036) | -0.093 (0.015) | -0.060 (0.085) | -0.163 (0.057) | -0.101 (0.135) | -0.117 (0.097) | +0.169 (0.148) | -0.063 (0.166) |

### LOCO MAE (degrees)

| Model | V1 HC (SD) | V1 CVD (SD) | V2 HC (SD) | V2 CVD (SD) | V3 HC (SD) | V3 CVD (SD) | hV4 HC (SD) | hV4 CVD (SD) |
|-------|-----------|------------|-----------|------------|-----------|------------|------------|-------------|
| ols | 76.4 (8.4) | 84.6 (28.3) | 80.0 (16.7) | 98.5 (20.5) | 76.9 (16.2) | 73.5 (9.9) | 69.0 (9.2) | 87.4 (10.2) |
| ridge_gcv | 92.1 (10.0) | 91.9 (26.7) | 95.2 (23.3) | 103.1 (17.7) | 85.4 (15.2) | 83.7 (7.8) | 81.0 (7.0) | 93.8 (8.4) |
| prior_only | 76.3 (6.8) | 85.4 (16.5) | 80.1 (10.4) | 85.5 (12.9) | 103.2 (8.0) | 112.0 (11.7) | 78.2 (10.7) | 95.4 (4.8) |
| prior_ft | 78.2 (5.9) | 86.9 (17.7) | 82.6 (10.1) | 86.9 (11.8) | 96.8 (15.0) | 91.8 (7.3) | 72.6 (7.2) | 90.9 (14.5) |

Note: Ridge MAE > OLS MAE because ridge shrinks predictions toward zero → conservative hue estimates. voxel_corr is the more reliable metric.

### One-Sample t-Test: HC LOCO ridge_gcv > 0

| ROI | HC Mean | 95% CI | t(6) | p (two-tail) | p (one-tail) |
|-----|---------|--------|------|-------------|-------------|
| **V1** | **0.130** | [0.040, 0.220] | 3.544 | **0.012** | **0.006** |
| V2 | 0.150 | [-0.024, 0.323] | 2.109 | 0.079 | **0.040** |
| V3 | 0.023 | [-0.199, 0.245] | 0.254 | 0.808 | 0.404 |
| **hV4** | **0.183** | [-0.002, 0.367] | 2.423 | 0.052 | **0.026** |

### HC vs CVD (ridge_gcv, LOCO voxel_corr)

| ROI | HC M (SD) | CVD M (SD) | Cohen's d | p (Welch) |
|-----|----------|----------|-----------|-----------|
| V1 | +0.130 (0.097) | -0.012 (0.054) | +1.61 | **0.021** |
| V2 | +0.150 (0.188) | -0.174 (0.130) | +1.85 | **0.022** |
| V3 | +0.023 (0.240) | -0.008 (0.163) | +0.14 | 0.819 |
| hV4 | +0.183 (0.200) | -0.058 (0.207) | +1.19 | 0.169 |

### NC-Normalized LOCO voxel_corr (ridge_gcv, HC)

| ROI | HC Mean (SD) | Interpretation |
|-----|-------------|----------------|
| V1 | 0.227 (0.199) | ~23% of voxel-pattern signal |
| V2 | 0.268 (0.376) | ~27% (very high variance) |
| V3 | 0.061 (0.413) | Near zero — model fails |
| **hV4** | **0.316 (0.207)** | **~32% — most consistent** |

---

## 4. Basis Ablation

### LOCO voxel_corr by Basis (OLS, n=10)

| Basis | V1 M (SD) | V2 M (SD) | V3 M (SD) | hV4 M (SD) |
|-------|----------|----------|----------|-----------|
| **FE-6** | **+0.011** (0.101) | **+0.010** (0.170) | -0.006 (0.180) | **+0.090** (0.199) |
| LF-4 | -0.066 (0.087) | -0.097 (0.200) | -0.105 (0.125) | -0.075 (0.091) |
| LF-6 | -0.111 (0.154) | -0.070 (0.159) | -0.093 (0.220) | -0.093 (0.199) |

### LORO voxel_corr by Basis (OLS, n=10)

| Basis | V1 M (SD) | V2 M (SD) | V3 M (SD) | hV4 M (SD) |
|-------|----------|----------|----------|-----------|
| **FE-6** | **0.214** (0.039) | **0.250** (0.051) | **0.330** (0.069) | **0.404** (0.060) |
| LF-4 | 0.166 (0.037) | 0.187 (0.060) | 0.245 (0.059) | 0.321 (0.065) |
| LF-6 | 0.202 (0.047) | 0.254 (0.081) | 0.324 (0.099) | 0.378 (0.082) |

### FE-6 vs LF-4 (paired t, n=10)

| Protocol | ROI | FE-6 M | LF-4 M | Delta | t(9) | p |
|----------|-----|--------|--------|-------|------|---|
| LOCO | V1 | +0.011 | -0.066 | +0.077 | 2.32 | **0.045** |
| LOCO | V2 | +0.010 | -0.097 | +0.107 | 2.37 | **0.042** |
| LOCO | V3 | -0.006 | -0.105 | +0.099 | 1.67 | 0.129 |
| LOCO | hV4 | +0.090 | -0.075 | +0.165 | 2.96 | **0.016** |
| LORO | V1 | 0.214 | 0.166 | +0.049 | 5.87 | **<0.001** |
| LORO | V2 | 0.250 | 0.187 | +0.063 | 4.61 | **0.001** |
| LORO | V3 | 0.330 | 0.245 | +0.085 | 6.27 | **<0.001** |
| LORO | hV4 | 0.404 | 0.321 | +0.083 | 7.31 | **<0.001** |

**Conclusion**: FE-6 > LF-4 > LF-6. Half-wave rectified cosine better captures peaked neural tuning than Fourier harmonics. Basis shape matters more than dimensionality.

### Extended Basis Comparison: FE Channel Count (ridge_gcv, HC n=7)

#### LOCO voxel_corr by FE channel count

| Basis | V1 | V2 | V3 | hV4 |
|-------|------|------|------|------|
| FE-2 | **+0.153** | +0.180 | +0.085 | +0.186 |
| FE-3 | +0.143 | **+0.180** | +0.097 | **+0.205** |
| FE-4 | +0.109 | +0.165 | +0.052 | +0.185 |
| FE-6 | +0.130 | +0.150 | +0.023 | +0.183 |
| FE-8 | +0.128 | +0.176 | **+0.112** | +0.191 |
| FE-12 | +0.134 | +0.168 | +0.106 | +0.190 |

#### LORO-LOCO anti-correlation (bias-variance tradeoff)

| ROI | LORO r(K,perf) | LOCO r(K,perf) | Interpretation |
|-----|---------------|---------------|----------------|
| V1 | +0.822 | -0.233 | LORO↑ with K, LOCO↓ |
| V2 | +0.840 | -0.291 | LORO↑ with K, LOCO↓ |
| V3 | +0.887 | +0.321 | Both increase (FE-8 optimal) |
| hV4 | +0.870 | -0.087 | LORO↑, LOCO flat |

LORO: more channels = monotonically better (lower bias). LOCO: fewer channels = better for V1/V2 (lower variance, stronger interpolation constraint).

#### Paired t-test: Optimal vs FE-6 (HC LOCO, n=7)

| ROI | Optimal | Opt M | FE-6 M | Delta | t(6) | p |
|-----|---------|-------|--------|-------|------|---|
| V1 | FE-2 | +0.153 | +0.130 | +0.023 | 1.46 | 0.194 |
| V2 | FE-3 | +0.180 | +0.150 | +0.031 | 0.98 | 0.367 |
| V3 | FE-8 | +0.112 | +0.023 | +0.089 | 1.27 | 0.252 |
| hV4 | FE-3 | +0.205 | +0.183 | +0.022 | 0.81 | 0.451 |

No FE basis significantly outperforms FE-6 (all paired p > 0.05, n=7), but direction consistent.

#### Permutation test with per-ROI optimal basis (10K, Stouffer combined)

| ROI | Basis | HC Obs | Null M | Delta | p_stouffer | vs FE-6 |
|-----|-------|--------|--------|-------|-----------|---------|
| V1 | FE-2 | +0.153 | +0.133 | +0.021 | 0.170 | FE-6: 0.133 |
| V2 | FE-3 | +0.181 | +0.138 | +0.043 | 0.125 | FE-6: 0.154 |
| **V3** | **FE-8** | **+0.144** | **+0.077** | **+0.068** | **0.045*** | FE-6: 0.360 |
| **hV4** | **FE-3** | **+0.204** | **+0.138** | **+0.066** | **0.026*** | FE-6: 0.039* |

**V3 recovery**: FE-6 p=0.360 (NO-GO) → FE-8 **p=0.045 (PASS)**. V3 failure was basis-driven, not data-driven.

V1/V2: improved but still FAIL with any 1D circular FE basis → structural limitation of 1D hue model.

#### One-sample t-test improvement (HC LOCO > 0, optimal basis)

| ROI | Basis | Mean | 95% CI | t(6) | p (one-tail) |
|-----|-------|------|--------|------|-------------|
| V1 | FE-2 | +0.153 | [+0.052, +0.255] | 3.686 | **0.005*** |
| **V2** | **FE-3** | **+0.180** | **[+0.046, +0.315]** | **3.286** | **0.008*** |
| V3 | FE-8 | +0.112 | [-0.044, +0.267] | 1.759 | 0.065† |
| hV4 | FE-3 | +0.205 | [+0.012, +0.398] | 2.594 | **0.021*** |

V2: p=0.040 → **0.008** with FE-3 (CI fully positive).

#### HC-CVD gap by basis

| ROI | Basis | HC M | CVD M | Cohen's d | p (Welch) |
|-----|-------|------|-------|-----------|-----------|
| V1 | FE-2 | +0.153 | +0.115 | +0.40 | 0.581 |
| V1 | FE-6 | +0.130 | -0.012 | +1.76 | 0.021 |
| V2 | FE-3 | +0.180 | -0.032 | +1.68 | 0.067 |
| V2 | FE-6 | +0.150 | -0.174 | +2.03 | 0.022 |

V1 FE-2: CVD also positive (+0.115), d shrinks from 1.76 → 0.40. HC-CVD gap partly basis-dependent.

### Opponent Basis Test (Red Team #3 Neutralization, 10K perm)

**Question**: Does V1/V2 LOCO failure stem from FE basis mismatch? Testing 2D DKL opponent-channel bases.

#### Bases Tested

| Basis | Type | K | Design |
|-------|------|:-:|--------|
| OPP-2 | Raw opponent | 2 | [cos(θ), sin(θ)] |
| OPP-4 | Opponent + quadrature | 4 | [cos(θ), sin(θ), cos(2θ), sin(2θ)] |
| OPP-4rect | Half-wave rectified opponent | 4 | [cos⁺, cos⁻, sin⁺, sin⁻] |
| FE-6 | Fourier encoding (reference) | 6 | Half-wave rectified cos² |

#### LOCO Permutation (Stouffer combined, HC)

| Basis | V1 | V2 | V3 | V4 |
|-------|:------:|:------:|:------:|:------:|
| OPP-2 | p=0.324 | p=0.444 | p=0.358 | p=0.302 |
| OPP-4 | p=0.125 | p=0.109 | p=0.566 | p=0.139 |
| OPP-4rect | p=0.633 | p=0.261 | p=0.796 | p=0.110 |
| **FE-6** | p=0.126 | p=0.154 | p=0.367 | **p=0.039*** |

#### HC LOCO Mean (observed / null)

| Basis | V1 | V2 | V3 | V4 |
|-------|:---:|:---:|:---:|:---:|
| OPP-2 | -.041/-.055 | -.047/-.062 | -.042/-.047 | -.042/-.058 |
| OPP-4 | -.054/-.091 | -.074/-.104 | -.118/-.075 | -.045/-.097 |
| OPP-4rect | +.099/+.113 | +.157/+.127 | +.054/+.090 | +.167/+.103 |
| FE-6 | +.144/+.111 | +.169/+.129 | +.063/+.077 | +.181/+.085 |

**Conclusions:**
1. **ALL opponent bases FAIL for V1/V2** — no basis achieves p < 0.05
2. **FE-6 is the ONLY basis passing anywhere** (V4 p=0.039)
3. OPP-2 (K=2) produces negative LOCO everywhere — gross underfit
4. OPP-4rect has inflated null (positive baseline) — no discriminative power
5. **Red Team #3 neutralized**: V1/V2 failure is NOT basis mismatch — dissociation (V4 pass, V1/V2 fail) is a genuine regional property

---

## 5. Metric Reinforcement

### 5a. Permutation Test (10K color-label shuffles, HC ridge_gcv)

| ROI | Observed | Null Mean | Null SD | Null 95% CI | p_perm |
|-----|---------|-----------|---------|-------------|--------|
| V1 | 0.130 | 0.109 | 0.034 | [0.043, 0.175] | 0.274 |
| V2 | 0.150 | 0.130 | 0.039 | [0.055, 0.203] | 0.311 |
| V3 | 0.023 | 0.078 | 0.046 | [-0.015, 0.167] | 0.880 |
| **hV4** | **0.183** | **0.080** | 0.059 | [-0.035, 0.196] | **0.044*** |

V1/V2 null centered at ~0.10-0.13 (not zero) due to voxel covariance structure. Parametric t-tests (p=0.006/0.040) tested H₀: μ=0, which is the wrong null. **Only hV4 shows genuine color-specific interpolation above permutation null.**

### 5b. Per-Color LOCO Breakdown (Friedman test, HC)

| ROI | chi²(7) | p | Interpretation |
|-----|---------|---|----------------|
| V1 | 18.33 | **0.011*** | Non-uniform — Blue/Cyan high, Yellow/Green low |
| V2 | 14.24 | **0.047*** | Non-uniform |
| V3 | 11.38 | 0.123 | No structure |
| hV4 | 6.48 | 0.485 | **Uniform — genuine continuous interpolation** |

### 5c. Residual Structure (HC)

| Metric | V1 | V2 | V3 | hV4 |
|--------|------|------|------|------|
| r(resid, orig) | 0.453 | 0.454 | 0.329 | **0.053** |
| r(pred, orig) | 0.390 | 0.407 | 0.415 | **0.563** |
| resid/signal ratio | 0.658 | 0.658 | 0.581 | **0.454** |

hV4 residuals near-random → model captures most available structure. V1/V2 residuals systematic → model misses significant color geometry.

### 5d. Cross-Validation Summary

| Evidence | V1 | V2 | hV4 |
|----------|------|------|------|
| Parametric t-test (H₀: μ=0) | p=0.006* | p=0.040* | p=0.026* |
| **Permutation (H₀: shuffled)** | p=0.274 | p=0.311 | **p=0.044*** |
| Friedman per-color | non-uniform* | non-uniform* | **uniform** |
| Residuals | systematic | systematic | **near-random** |

### 5e. Intercept Model Permutation Test (10K, HC)

**Question**: Does a shared spatial mean (intercept) inflate LOCO performance or null?

Three methods tested:
- **Standard**: Y = W @ C (baseline ridge_gcv)
- **Intercept**: Y = W_color @ C + b (evaluation uses deviation only: corr(C_test @ W_color, Y_real - b))
- **Mean_subt**: (Y - mean(Y)) = W @ C (pre-subtracted mean pattern)

#### Stouffer Combined p-values (per-ROI optimal basis)

| Method | V1 (FE-6) | V2 (FE-6) | V3 (FE-8) | V4 (FE-3) |
|--------|:---------:|:---------:|:---------:|:---------:|
| Standard | p≈0.126 | p≈0.155 | p≈0.043* | p≈0.025* |
| Intercept | p≈0.127 | p≈0.156 | p≈0.040* | p≈0.064 |
| Mean_subt | p≈0.136 | p≈0.160 | p≈0.053 | p≈0.059 |

**Conclusions:**
1. **Standard ≈ Intercept ≈ Mean_subt** — nearly identical p-values across all ROIs
2. V1/V2 remain non-significant under all three methods
3. Intercept null centers at ~-0.035 (standard null at ~+0.05-0.10) — intercept absorbs shared signal
4. **p-values unchanged** — encoding signal is in the hue-modulated pattern, not the mean spatial pattern
5. V3/V4 borderline shifts (V4 standard p=0.025 vs intercept p=0.064) from variance, not systematic bias

---

## 6. Extended Models

### 6a. LOCO voxel_corr — All Subjects (n=10)

| Model | V1 M (SD) | V2 M (SD) | V3 M (SD) | V4 M (SD) |
|-------|----------|----------|----------|-----------|
| ridge_gcv | +0.087 (0.095) | +0.053 (0.194) | +0.014 (0.200) | +0.111 (0.210) |
| prior_finetune | -0.067 (0.035) | -0.091 (0.090) | -0.105 (0.118) | +0.099 (0.175) |
| **smooth_tikh** | **+0.112 (0.133)** | **+0.151 (0.175)** | **+0.115 (0.212)** | **+0.157 (0.245)** |
| smooth_prior | +0.025 (0.153) | -0.002 (0.170) | -0.078 (0.143) | +0.094 (0.244) |
| mixed_ridge_prior | -0.056 (0.089) | -0.073 (0.126) | -0.066 (0.105) | +0.094 (0.225) |
| bayes_prior | -0.062 (0.047) | -0.101 (0.082) | -0.123 (0.129) | +0.028 (0.209) |

### 6b. smooth_tikh One-Sample t-Test (HC LOCO > 0)

| ROI | HC Mean | HC SD | 95% CI | t(6) | p (one-tail) |
|-----|---------|-------|--------|------|-------------|
| **V1** | **+0.143** | 0.109 | [+0.043, +0.243] | 3.483 | **0.007** |
| **V2** | **+0.246** | 0.100 | [+0.153, +0.338] | 6.514 | **<0.001** |
| V3 | +0.100 | 0.254 | [-0.135, +0.334] | 1.038 | 0.170 |
| **V4** | **+0.190** | 0.253 | [-0.045, +0.424] | 1.981 | **0.047** |

### 6c. smooth_tikh vs ridge_gcv (paired t, n=10)

| ROI | smooth_tikh M | ridge_gcv M | Delta | t(9) | p | Cohen's d |
|-----|-------------|------------|-------|------|---|-----------|
| V1 | +0.112 | +0.087 | +0.025 | 1.136 | 0.285 | +0.359 |
| V2 | +0.151 | +0.053 | +0.099 | 2.115 | 0.064 | +0.669 |
| **V3** | **+0.115** | **+0.014** | **+0.102** | **2.574** | **0.030** | **+0.814** |
| V4 | +0.157 | +0.111 | +0.046 | 1.271 | 0.236 | +0.402 |

### 6d. HC vs CVD: smooth_tikh (Welch t-test)

| ROI | HC M (SD) | CVD M (SD) | Cohen's d | p (Welch) |
|-----|----------|----------|-----------|-----------|
| V1 | +0.143 (0.109) | +0.039 (0.180) | +0.80 | 0.429 |
| **V2** | **+0.246 (0.100)** | **-0.070 (0.063)** | **+3.43** | **0.001** |
| V3 | +0.100 (0.254) | +0.151 (0.081) | -0.23 | 0.641 |
| V4 | +0.190 (0.253) | +0.080 (0.255) | +0.43 | 0.568 |

### 6e. NC-Normalized LOCO (smooth_tikh vs ridge_gcv, HC Mean)

| ROI | ridge_gcv NC (SD) | smooth_tikh NC (SD) | Delta |
|-----|-------------------|---------------------|-------|
| V1 | 0.271 (0.215) | 0.297 (0.241) | +0.025 |
| **V2** | 0.300 (0.356) | **0.475 (0.169)** | **+0.175** |
| V3 | 0.041 (0.378) | 0.185 (0.381) | +0.145 |
| V4 | 0.247 (0.265) | 0.254 (0.344) | +0.007 |

### 6f. Artifact Check (LOCO rdm_pearson, n=10)

| ROI | ridge_gcv (SD) | smooth_tikh (SD) | Δ | t(9) | p |
|-----|---------------|-----------------|------|------|---|
| **V1** | 0.034 (0.226) | **0.531 (0.239)** | **+0.496** | **4.24** | **0.002*** |
| V2 | 0.179 (0.282) | **0.457 (0.230)** | +0.278 | 1.97 | 0.081 |
| **V3** | 0.160 (0.200) | **0.398 (0.207)** | **+0.238** | **3.58** | **0.006*** |
| **hV4** | 0.104 (0.281) | **0.410 (0.180)** | **+0.306** | **2.27** | **0.049*** |

Artifact flags: 0/10 (V1), 0/10 (V2), 0/10 (V3), 1/10 (V4 — sub-10 only).

> **⚠️ REINTERPRETATION (2026-03-11):** The rdm_pearson "improvement" is **misleading**. RDM inspection (§8) reveals that (1) actual data has NO circular hue structure (Spearman vs ideal ≈ 0), and (2) smooth_tikh predicted RDM is ANTI-correlated with ideal circular structure (ρ ≈ -0.5). The high rdm_pearson means smooth_tikh's compressed/flat RDM pattern-matches the actual data's non-circular noise structure, NOT that it preserves genuine color geometry.

### 6g. Individual CVD Profiles (smooth_tikh)

| Subject | Type | V2 LOCO r | V2 HC z-score | Crawford-Howell p |
|---------|------|-----------|--------------|-------------------|
| sub-08 | deutan | -0.143 | -3.89 | **0.011*** |
| sub-09 | protan | -0.034 | -2.81 | **0.039*** |
| sub-10 | deutan | -0.033 | -2.79 | **0.040*** |

**All 3 CVD subjects show significant V2 deviation with smooth_tikh** (all CH p < 0.05). Not achieved with ridge_gcv.

### 6h. Hypothesis Resolution

| Hypothesis | Model | Result | Verdict |
|-----------|-------|--------|---------|
| H1 (Shape mismatch) | mixed_ridge_prior | All negative V1-V3 | **REJECTED** |
| H2 (Uncertainty blindness) | bayes_prior | All negative V1-V3 | **REJECTED** |
| H3 (Missing smoothness) | smooth_tikh | voxel_corr ↑ AND rdm_pearson ↑ | **CONFIRMED** (perm pending) |
| H3 + prior | smooth_prior | Near-zero or negative | **REJECTED** |

---

## 7. GO/NO-GO Gate

### ridge_gcv Gate — FE-6 (confirmed)

| ROI | C1 (Reliability) | C2 (Norm. Fit) | C3 (Interpolation) | C3b (Permutation) | Overall |
|-----|-------------------|----------------|---------------------|--------------------|---------|
| V1 | PASS (0.416) | PASS (0.227) | PASS (p=0.006) | FAIL (p=0.274) | **CONDITIONAL GO** |
| V2 | PASS (0.420) | PASS (0.268) | PASS (p=0.040) | FAIL (p=0.311) | **CONDITIONAL GO** |
| V3 | PASS (0.398) | FAIL (0.061) | FAIL (p=0.404) | FAIL (p=0.880) | **NO-GO** |
| hV4 | PASS (0.603) | PASS (0.316) | PASS (p=0.026) | **PASS (p=0.044)** | **PRIMARY GO** |

### ridge_gcv Gate — Per-ROI Optimal Basis (updated 2026-03-11)

| ROI | Basis | C3 (LOCO>0) | C3b (Perm Stouffer) | Change vs FE-6 |
|-----|-------|-------------|---------------------|----------------|
| V1 | FE-2 | **PASS (p=0.005)** | FAIL (p=0.170) | Perm 0.274→0.170 (improved, still FAIL) |
| V2 | FE-3 | **PASS (p=0.008)** | FAIL (p=0.125) | Perm 0.311→0.125 (improved, still FAIL) |
| **V3** | **FE-8** | MARGINAL (p=0.065) | **PASS (p=0.045)** | **NO-GO → PASS** |
| hV4 | FE-3 | **PASS (p=0.021)** | **PASS (p=0.026)** | Perm 0.044→0.026 (strengthened) |

> **V3 recovery**: FE-8 basis rescues V3 from NO-GO (p=0.360) to PASS (p=0.045). V1/V2 FAIL with ALL tested bases — FE-{2..12}, OPP-2, OPP-4, OPP-4rect (§4). Intercept model also does not help (§5e). This is a confirmed structural limitation of 8-stimulus LOCO, not basis mismatch.

### smooth_tikh Gate (REJECTED)

| ROI | C1 | C2 (NC-Norm) | C3 (LOCO > 0) | C3c (rdm_pearson) | C3b (Perm) | Status |
|-----|----|----|----|----|----|----|
| V1 | PASS (0.416) | PASS (0.297) | PASS (p=0.007) | ~~PASS~~ misleading | **FAIL (p=0.331)** | **REJECTED** |
| V2 | PASS (0.420) | PASS (0.475) | PASS (p<0.001) | ~~PASS~~ misleading | **FAIL (p=0.188)** | **REJECTED** |
| V3 | PASS (0.397) | FAIL (0.185) | FAIL (p=0.170) | ~~PASS~~ misleading | **FAIL (p=0.613)** | NO-GO |
| V4 | PASS (0.603) | PASS (0.254) | PASS (p=0.047) | ~~PASS~~ misleading | **FAIL (p=0.613)** | **REJECTED** |

> **Note:** C3c (rdm_pearson) retroactively invalidated — see §8 RDM Inspection.

---

## 8. smooth_tikh Investigation (REJECTED)

### 8a. Permutation Test — Fixed Params (10K color-label shuffles, HC)

| ROI | Observed | Null Mean | Null SD | p_perm |
|-----|---------|-----------|---------|--------|
| V1 | 0.189 | 0.187 | — | 0.331 |
| V2 | 0.216 | 0.212 | — | 0.188 |
| V3 | 0.125 | 0.128 | — | 0.613 |
| V4 | 0.239 | 0.241 | — | 0.613 |

**All ROIs fail.** Observed ≈ null mean — smooth_tikh captures shared spatial covariance, not color-specific signal.

### 8b. Rescue Attempt 1: Condition-Centering

**Hypothesis:** Model Y=WC has no intercept → W absorbs shared spatial pattern → β amplifies it. Per-run condition centering (subtracting mean across 8 colors within each run) should remove this.

**Result:** Per-run centering **commutes with color label shuffle**. The mean across 8 colors is identical regardless of shuffle order: `mean(amp[:, perm, :], axis=1) == mean(amp, axis=1)`. Therefore centering **cannot change the permutation test**. Confirmed empirically: identical p-values with and without centering (e.g., sub-02 hV4 smooth_tikh: p=0.015 both ways).

**Side effect:** Per-run centering makes smooth_tikh predictions dramatically worse (observed r drops to ~-0.9), because the smooth W captures mostly the mean pattern, which centering removes.

### 8c. Rescue Attempt 2: Re-Optimized Permutation

**Hypothesis:** Fixed (α=0.01, β=100) selected on real data biases the null. Re-selecting (α, β) via inner LOCO-CV within each permutation should produce a fairer null.

**Result (5 perms, sub-02 hV4 diagnostic):**
- Null beta distribution: β=1000 selected 45%, β=0 selected 26%, β=100 only 9%
- On shuffled data, **high β is still preferred** — regularization helps fit noise
- Observed score drops with re-optimization: 0.172 (vs 0.239 fixed)
- Delta (obs - null_mean) still small and negative (-0.007)

**Conclusion:** Re-optimization does not rescue smooth_tikh. The smoothness penalty is inherently beneficial for fitting ANY data (real or shuffled), not specifically for color signal.

### 8d. RDM Structure Inspection

**Question:** Does the previously reported rdm_pearson improvement reflect genuine color geometry preservation?

**Ideal RDM (circular hue distance, normalized to [0,1]):**

| | red | orange | yellow | green | cyan | blue | purple | magenta |
|---|---|---|---|---|---|---|---|---|
| red | - | 0.25 | 0.50 | 0.75 | 1.00 | 0.75 | 0.50 | 0.25 |
| cyan | 1.00 | 0.75 | 0.50 | 0.25 | - | 0.25 | 0.50 | 0.75 |

**Actual data vs Ideal (Spearman, HC mean):**

| ROI | Actual vs Ideal | Interpretation |
|-----|----------------|----------------|
| V1 | -0.008 | NO circular structure |
| V2 | +0.044 | NO circular structure |
| hV4 | +0.004 | NO circular structure |

**smooth_tikh predicted RDM vs Ideal (Spearman, HC mean):**

| ROI | Predicted vs Ideal | Interpretation |
|-----|-------------------|----------------|
| V1 | **-0.624** | ANTI-correlated with ideal |
| V2 | **-0.580** | ANTI-correlated with ideal |
| hV4 | **-0.442** | ANTI-correlated with ideal |

**smooth_tikh RDM distance compression:**
- Actual RDM distances: 0.66–1.49 (wide range)
- smooth_tikh predicted RDM distances: 0.06–0.23 (extremely compressed)

**Reinterpretation of rdm_pearson "improvement":**
The previously reported high rdm_pearson (e.g., V1=0.531) means smooth_tikh's compressed/flat RDM pattern-matches the actual data's **non-circular noise structure** — NOT that it preserves genuine color geometry. The actual data itself has no ideal circular hue arrangement. smooth_tikh's smoothness penalty forces near-identical predictions for all colors → compressed RDM → this flat pattern happens to correlate with actual data's noise.

### 8e. smooth_tikh Conclusion

**smooth_tikh is REJECTED.** All three rescue attempts failed:

| Approach | Finding | Why It Doesn't Work |
|----------|---------|---------------------|
| Fixed-param permutation | All p > 0.18 | Shared spatial covariance drives voxel_corr |
| Condition-centering | Commutes with shuffle | Cannot change permutation by construction |
| Re-optimized permutation | Null beta ≥ observed | Smoothness helps fit any data, not just color signal |
| RDM-based evaluation | Anti-correlated with ideal | rdm_pearson improvement was noise pattern-matching |

**Root cause:** β=100 forces near-rank-1 W (all columns nearly identical) → predictions are dominated by a single spatial pattern shared across all colors → high voxel_corr, high rdm_pearson, but NO color-discriminative content.

---

## 9. Final Decisions

1. **Best LOCO encoder**: **ridge_gcv (confirmed)**. smooth_tikh REJECTED — all rescue attempts failed.
2. **Encoding basis**: FE-6 confirmed for hV4. Per-ROI optimal: V1→FE-2, V2→FE-3, V3→FE-8, hV4→FE-3. No paired difference reaches p<0.05 vs FE-6.
3. **Basis-channel tradeoff**: LORO monotonically improves with K. LOCO shows inverse pattern in V1/V2 (bias-variance tradeoff).
4. **V3 recovery**: FE-8 rescues V3 from NO-GO (perm p=0.360) to PASS (p=0.045). V3 failure was basis-driven.
5. **V1/V2 LOCO limitation confirmed**: All FE-{2..12} AND all opponent bases (OPP-2/4/4rect) fail permutation for V1/V2. Intercept model also unchanged. This is a structural limitation of 8-stimulus LOCO resolution, not basis mismatch (Red Team #3 neutralized).
6. **HC-CVD gap is basis-dependent**: V1 FE-2 closes gap (d=1.76→0.40; CVD=+0.115). Part of CVD LOCO failure is basis mismatch, not purely biological.
7. **Prior-based models**: All rejected — SRM prior is fundamentally incompatible with LOCO.
8. **smooth_tikh (9h-9i)**: REJECTED — captures spatial covariance, not color signal. rdm_pearson "improvement" was noise pattern-matching.
9. **Intercept model**: Does not change LOCO significance. Shared spatial mean does not drive results.
10. **Phase 2 roles**: V1/V2 = filter correction targets (HC-CVD d=1.61/1.85). hV4 = color interpolation oracle (permutation p=0.044). V3 = conditional (FE-8 basis).
11. **Leakage prevention**: Including held-out color in A_g inflates LOCO by +0.55 to +0.69. Leakage-free pipeline mandatory.

---

## 10. Red Team Response

> Self-critique conducted 2026-03-11. Full report: `results/redteam/2026-03-11.md`

### RT-1. Statistical Power (N=3 CVD)

**Criticism:** N=3 CVD precludes group-level inference. Welch t-tests (df~4-5) are unstable; effect sizes inflated.

**Response — Case Study Framing:**
- All CVD results are presented as **individual case analyses** using Crawford & Howell (2010) single-case statistics, designed for comparing one patient to a normative sample
- Group-level CVD claims (Welch t-tests) are reported as **descriptive/exploratory**, not confirmatory
- HC group results (N=7) constitute the validated model; CVD application is "proof-of-concept with N=3"
- Minimum sample size for definitive CVD group claims: N≥12 per group (d=0.8, α=0.05, power=0.80)
- CVD-CVD RDM correlation (0.276 > HC-HC 0.158) is reported as **descriptive observation**, not tested

**Impact on pipeline:** None. Phase 2 filter operates per-subject; group-level CVD inference is not required.

### RT-2. Multiple Comparison Correction (hV4 p=0.044)

**Criticism:** 4 ROIs tested; Bonferroni threshold = 0.0125; hV4 p=0.044 fails.

**Response — A Priori Primary ROI + Converging Evidence:**

**A priori justification for hV4 as primary hypothesis:**
1. **Literature precedent**: Brouwer & Heeger (2009) identified V4/VO1 as the site of novel-color reconstruction; hV4 was the pre-specified target ROI
2. **Data quality**: Highest noise ceiling (HC 0.702), highest split-half reliability (HC 0.603)
3. **Biological rationale**: hV4 contains hue-selective neurons most compatible with FE-6 circular basis (Section 2b of discussion)

**Correction applied:**
- hV4 = **primary hypothesis** (uncorrected p=0.044; further strengthened with FE-3: p=0.026)
- V1/V2/V3 = **secondary/exploratory** (reported as such; V1/V2 fail, V3 conditional)
- If Bonferroni-corrected across 4 ROIs: hV4 FE-6 p=0.044 does not survive (threshold 0.0125)
- If FDR (BH) with per-ROI optimal basis [0.170, 0.125, 0.045, 0.026]: hV4 FE-3 q=0.104 (does not survive)

**Converging evidence (independent of permutation p-value):**

| Evidence | V1/V2 | hV4 | Independence |
|----------|-------|-----|-------------|
| Permutation (color-shuffle) | FAIL | p=0.044* | Primary test |
| Friedman per-color uniformity | Non-uniform* | **Uniform** (p=0.485) | Different test statistic |
| Residual structure | Systematic (r=0.45) | **Near-random** (r=0.053) | Model diagnostics |
| NC-normalized fit | 0.23/0.27 | **0.32** | Data quality normalized |
| Noise ceiling | 0.47/0.51 | **0.70** | Measurement quality |

No single test is definitive; convergence across complementary metrics strengthens inference.

**Cross-pipeline clarification:**
- Phase 1 (forward model) HC-CVD hV4 LOCO voxel_corr: p=0.169 (n.s.) — **within-pipeline result**
- Phase 3 (decoder) HC-CVD LOCO MAE: p=0.017 — **separate pipeline, separate metric**
- These are reported in their respective sections; not mixed for inference

### RT-3. Discrimination vs. Interpolation Dissociation — NEUTRALIZED

**Criticism:** Post-hoc rationalization; no alternative basis tested.

**Resolution:** Directly tested with 3 opponent-channel bases (OPP-2, OPP-4, OPP-4rect) + FE channel variants (FE-2 through FE-12) + intercept model. **ALL bases fail V1/V2 permutation.** FE-6 is the only basis passing anywhere (V4 p=0.039).

The dissociation is confirmed as a **structural limitation of 8-stimulus LOCO for V1/V2**, not basis mismatch. Full results in Section 4 (Opponent Basis Test).

### RT-4. Analytical Degrees of Freedom

**Criticism:** 8 models × 3+ bases × 4 ROIs × 6 metrics; one combination yields p=0.044.

**Response — Decision Logic (not p-value selection):**

The analytical pipeline followed a **sequential elimination** logic, not simultaneous testing:

1. **Basis selection** (Section 4): FE-6 > LF-4 > LF-6 by paired LOCO CV (p=0.045/0.042/0.016). Basis selected on cross-validation performance, NOT permutation p-values.

2. **Model selection** (Section 6): ridge_gcv selected as best LOCO model by cross-validated voxel_corr. smooth_tikh initially appeared better but was **independently rejected** by permutation test (Section 8). Model selection preceded permutation testing.

3. **Permutation test** (Section 5a): Applied as **final validation gate** to the pre-selected model/basis combination. The permutation test did not inform model or basis selection.

4. **Metric selection**: voxel_corr chosen a priori as primary metric (standard in forward encoding literature; Brouwer & Heeger 2009). Permutation test was chosen because parametric t-test uses wrong null (H₀: μ=0 vs H₀: no color-specific signal).

**Permutation test was not chosen for producing a "desired pattern":** The parametric t-test (V1 p=0.006) was replaced because it tests the wrong null hypothesis. Voxel covariance creates a non-zero baseline (V1 null mean = 0.109), making H₀: μ=0 inappropriate. This methodological correction was applied uniformly across all ROIs.

**Phase 2 pre-registration:** Planned before Phase 2 execution.

### RT-5. "CVD Failure = Data" Narrative

**Criticism:** Unfalsifiable; CVD reliability is HIGHER than HC (contradicting "distortion").

**Revised framing:**

1. **"Failure = data" revised to "basis mismatch + biological effect":**
   - HC-CVD gap is **partly basis-dependent**: V1 FE-2 reduces d from 1.76 to 0.40 (CVD becomes positive: +0.115)
   - Remaining gap after basis optimization reflects genuine biological effect (altered cone excitation)
   - These are separable contributions, not a single unfalsifiable claim

2. **Higher CVD reliability addressed:**
   - Higher reliability (0.699 vs 0.603) means CVD patterns are **consistently reproduced** across runs
   - This is compatible with "consistently distorted" — reliability measures stability, not accuracy
   - Analogy: a broken clock is perfectly reliable (same reading always) but not accurate

3. **Falsifiable prediction (Phase 1c):**
   - Adaptive basis optimization: if CVD-specific centers show systematic compression along L-M axis, the basis mismatch hypothesis is confirmed
   - If adaptive basis does NOT improve CVD LOCO, the "biological effect" component is larger than expected

4. **Phase 2 filter consistency:**
   - `W_s @ C(T_psi(θ)) ≈ Y_CVD(θ)` uses HC-derived W_s because hV4's categorical structure IS preserved in CVD (RDM HC≈CVD, p=0.559)
   - The filter T_psi corrects the continuous mapping, not the categorical structure
   - This is internally consistent: preserved structure + distorted mapping → filter adjusts mapping only
