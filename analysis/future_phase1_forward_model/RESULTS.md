# Future Phase 1: Forward Model — RESULTS

> Last updated: 2026-03-11 (reorganized)
> Status: Baseline + basis ablation + metric reinforcement + extended models **complete**. smooth_tikh permutation test **pending**.

---

## 1. Status Summary

| Experiment | Status | Key Outcome |
|-----------|--------|-------------|
| Baseline (4 models × 4 ROIs × LORO/LOCO) | **DONE** | ridge_gcv = best LOCO model |
| Basis ablation (FE-6 vs LF-4 vs LF-6) | **DONE** | FE-6 confirmed |
| Metric reinforcement (permutation/Friedman/residual) | **DONE** | hV4 = only genuine color interpolation |
| Improved encoding (RRR, smoothness) | **DONE** | Both rejected |
| Extended models (4 new models, inner LOCO) | **DONE** | smooth_tikh = leading candidate |
| smooth_tikh artifact check | **DONE** | PASSED (rdm_pearson ↑) |
| smooth_tikh permutation test | **PENDING** | Server execution needed |

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

Artifact flags: 0/10 (V1), 0/10 (V2), 0/10 (V3), 1/10 (V4 — sub-10 only). **Section 6g artifact does NOT apply to LOCO** — each predicted pattern is for a held-out color (independent interpolation), not a training color.

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

### ridge_gcv Gate (confirmed)

| ROI | C1 (Reliability) | C2 (Norm. Fit) | C3 (Interpolation) | C3b (Permutation) | Overall |
|-----|-------------------|----------------|---------------------|--------------------|---------|
| V1 | PASS (0.416) | PASS (0.227) | PASS (p=0.006) | FAIL (p=0.274) | **CONDITIONAL GO** |
| V2 | PASS (0.420) | PASS (0.268) | PASS (p=0.040) | FAIL (p=0.311) | **CONDITIONAL GO** |
| V3 | PASS (0.398) | FAIL (0.061) | FAIL (p=0.404) | FAIL (p=0.880) | **NO-GO** |
| hV4 | PASS (0.603) | PASS (0.316) | PASS (p=0.026) | **PASS (p=0.044)** | **PRIMARY GO** |

### smooth_tikh Gate (permutation pending)

| ROI | C1 | C2 (NC-Norm) | C3 (LOCO > 0) | C3c (rdm_pearson) | C3b (Perm) | Status |
|-----|----|----|----|----|----|----|
| V1 | PASS (0.416) | PASS (0.297) | PASS (p=0.007) | PASS (0.531) | PENDING | **PENDING PERM** |
| V2 | PASS (0.420) | PASS (0.475) | PASS (p<0.001) | PASS (0.457) | PENDING | **PENDING PERM** |
| V3 | PASS (0.397) | FAIL (0.185) | FAIL (p=0.170) | PASS (0.398) | PENDING | NO-GO |
| V4 | PASS (0.603) | PASS (0.254) | PASS (p=0.047) | PASS (0.410) | PENDING | **PENDING PERM** |

---

## 8. Decisions

1. **Best LOCO encoder**: ridge_gcv (current). smooth_tikh = leading candidate (pending permutation).
2. **Encoding basis**: FE-6 confirmed (half-wave cos² > Fourier).
3. **Prior-based models**: All rejected — SRM prior is fundamentally incompatible with LOCO.
4. **RRR / Smoothness (9g)**: Both rejected — RRR worse than baseline, smoothness voxel_corr improvement was misleading.
5. **Phase 2 roles**: V1/V2 = filter correction targets (HC-CVD d=1.61/1.85). hV4 = color interpolation oracle (permutation p=0.044). V3 = excluded.
6. **smooth_tikh adoption**: If permutation passes → smooth_tikh replaces ridge_gcv (V2 HC-CVD d=3.43, all CVD V2 significant). If fails → ridge_gcv retained.
7. **Leakage prevention**: Including held-out color in A_g inflates LOCO by +0.55 to +0.69. Leakage-free pipeline mandatory.
