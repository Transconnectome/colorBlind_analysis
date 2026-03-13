# Future Phase 1: Forward Model — RESULTS

> Last updated: 2026-03-13
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
| Adaptive basis optimization (per-subj centers) | **DONE** | 38/40 improved (circular); nested LOCO: adaptive ≈ fixed |
| Nested LOCO validation (double-CV) | **DONE** | Center optimization = no benefit; K is the only variable |
| Per-color residual & cross-phase integration | **DONE** | S-axis/cool residual confirmed; SRM ↔ FE convergence on blue/purple |

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

### 4a. Adaptive Basis Optimization (Section 9k-1)

#### Purpose and Test Question

- **Question**: "Does CVD LOCO failure stem from fixed basis mismatch, or from distorted neural representations?"
- **Method**: Freely optimize FE basis centers per subject × ROI via multi-start L-BFGS-B, maximizing 8-fold LOCO voxel_corr
- **t-test**: Paired one-sample t-test (delta = adaptive − fixed, H₀: delta = 0)
  → "Does the adaptive basis significantly improve over the fixed uniform basis?"

#### Fixed vs Adaptive LOCO voxel_corr (per-ROI optimal K)

| Subject | Group | V1(K=2) F/A/Δ | V2(K=3) F/A/Δ | V3(K=8) F/A/Δ | hV4(K=3) F/A/Δ |
|---------|-------|---------------|---------------|---------------|----------------|
| sub-01 | HC | +0.135/+0.147/+0.012 | +0.052/+0.156/+0.104 | +0.222/+0.280/+0.058 | +0.040/+0.132/+0.093 |
| sub-02 | HC | +0.040/+0.142/+0.102 | +0.286/+0.312/+0.026 | +0.104/+0.190/+0.086 | +0.511/+0.554/+0.043 |
| sub-03 | HC | +0.162/+0.187/+0.025 | +0.202/+0.230/+0.029 | +0.045/+0.085/+0.041 | +0.363/+0.466/+0.103 |
| sub-04 | HC | +0.182/+0.303/+0.121 | +0.209/+0.333/+0.124 | +0.074/+0.133/+0.059 | +0.256/+0.338/+0.083 |
| sub-05 | HC | +0.309/+0.305/−0.005 | +0.356/+0.378/+0.022 | +0.423/+0.439/+0.016 | +0.026/+0.088/+0.062 |
| sub-06 | HC | −0.005/+0.025/+0.030 | −0.061/+0.049/+0.111 | −0.269/−0.090/+0.179 | +0.313/+0.382/+0.070 |
| sub-07 | HC | +0.251/+0.255/+0.004 | +0.236/+0.237/+0.001 | +0.043/+0.129/+0.087 | −0.059/+0.130/+0.188 |
| sub-08 | CVD | +0.179/+0.267/+0.088 | +0.003/**+0.265**/+0.262 | +0.192/+0.295/+0.102 | +0.067/**+0.383**/+0.316 |
| sub-09 | CVD | +0.018/+0.036/+0.018 | +0.065/+0.125/+0.060 | +0.032/+0.080/+0.048 | +0.079/+0.147/+0.068 |
| sub-10 | CVD | +0.149/+0.149/+0.000 | −0.166/−0.030/+0.136 | +0.203/+0.225/+0.022 | +0.198/+0.283/+0.085 |
| **HC M (SD)** | | +0.153(0.102)/+0.195(0.094) | +0.183(0.132)/+0.242(0.105) | +0.092(0.193)/+0.167(0.152) | +0.207(0.193)/+0.299(0.170) |
| **CVD M (SD)** | | +0.115(0.070)/+0.151(0.094) | −0.032(0.098)/+0.120(0.120) | +0.143(0.078)/+0.200(0.089) | +0.115(0.059)/+0.271(0.097) |

#### Delta Statistics (paired t-test: adaptive − fixed vs 0)

| ROI | K | HC Delta M (SD) | t(6) | p | Improved |
|-----|---|----------------|------|---|----------|
| V1 | 2 | +0.041 (0.046) | 2.194 | 0.071 | 6/7 |
| **V2** | **3** | **+0.059 (0.047)** | **3.081** | **0.022*** | **7/7** |
| **V3** | **8** | **+0.075 (0.048)** | **3.805** | **0.009*** | **7/7** |
| **hV4** | **3** | **+0.092 (0.044)** | **5.151** | **0.002*** | **7/7** |

CVD individual deltas (n=3, no group test):

| Subject | V1 | V2 | V3 | hV4 |
|---------|------|------|------|------|
| sub-08 (deutan) | +0.088 | **+0.262** | +0.102 | **+0.316** |
| sub-09 (protan) | +0.018 | +0.060 | +0.048 | +0.068 |
| sub-10 (deutan) | +0.000 | +0.136 | +0.022 | +0.085 |

#### Optimized Center Patterns

**V1 (K=2)**: Uniform = [0, 180]°

| Group | HC Mean (SD) | Pattern |
|-------|-------------|---------|
| HC | [0, 211(26)]° | Shifted ~30° from uniform |
| sub-08 | [0, 180]° | Matched uniform |
| sub-09 | [0, 169]° | Near-uniform |
| sub-10 | [0, 180]° | Matched uniform |

**V2 (K=3)**: Uniform = [0, 120, 240]°

| Group | Centers | Pattern |
|-------|---------|---------|
| HC mean | [0, 117(53), 233(21)]° | Near-uniform |
| **sub-08** | **[0, 180, 359]°** | **Degenerate: K=3 → effective K=2** |
| sub-09 | [0, 145, 271]° | Shifted |
| sub-10 | [0, 116, 326]° | Shifted |

**hV4 (K=3)**: Uniform = [0, 120, 240]°

| Group | Centers | Pattern |
|-------|---------|---------|
| HC mean | [0, 131(47), 247(31)]° | Near-uniform |
| **sub-08** | **[0, 180, 359]°** | **Degenerate: K=3 → effective K=2** |
| sub-09 | [0, 118, 271]° | Near-uniform |
| sub-10 | [0, 180, 286]° | 2 of 3 near 0/180° |

**sub-08 degenerate pattern**: In both V2 and hV4, optimized centers collapse to [0°, 180°, 359°] ≈ effectively K=2 with channels at 0° and 180°. This is consistent with L-M axis compression in deuteranopia — the optimizer finds that a single opponent axis (red-cyan) captures most available structure, with the third channel redundant.

#### Circularity Warning

> **Bias**: Center optimization uses the full 8-color LOCO as objective function, meaning the test color indirectly influences center selection. Performance numbers are **optimistic upper bounds**. Unbiased validation requires nested LOCO (Section 4b, pending).

#### Key Findings

1. **38/40 subject×ROI combinations show delta ≥ 0** — near-universal improvement
2. V2/V3/hV4 HC deltas significant (all p < 0.025); V1 trending (p=0.071)
3. **sub-08 (deutan)**: V2 +0.262, hV4 +0.316 — dramatic improvement under circular optimization
4. **HC also benefit from non-uniform centers** — fixed FE is suboptimal even for typical color vision
5. Circular bias caveat: these results are upper bounds; see Section 4b for unbiased validation

### 4b. Nested LOCO Validation (Section 9k-2)

#### Purpose

Section 4a's center optimization used 8-color LOCO as objective → test color indirectly influenced center selection → optimistic bias. Nested (double) LOCO removes this circularity:

```
Outer fold (8-fold): hold out 1 color for evaluation
  └── Inner optimization (7-fold): optimize centers on remaining 7 colors
  └── Outer evaluation: optimal centers + 7-color W → predict held-out color
```

Three conditions compared:
1. **Fixed FE-6**: 6-channel uniform basis (standard)
2. **Fixed FE-K**: Per-ROI optimal K, uniform centers
3. **Nested Adaptive**: Per-ROI optimal K, nested-optimized centers

#### Results: 3-Way Comparison (mean LOCO voxel_corr)

| ROI | K | HC FE-6 | HC FE-K | HC Nested | CVD FE-6 | CVD FE-K | CVD Nested |
|-----|---|:-------:|:-------:|:---------:|:--------:|:--------:|:----------:|
| V1 | 2 | +0.130 | +0.153 | +0.175 | −0.012 | +0.115 | +0.130 |
| V2 | 3 | +0.150 | +0.180 | +0.174 | −0.174 | −0.032 | −0.002 |
| V3 | 8 | +0.023 | +0.112 | +0.110 | −0.008 | +0.081 | +0.086 |
| hV4 | 3 | +0.183 | +0.205 | +0.164 | −0.058 | +0.116 | +0.096 |

#### HC Paired t-tests: Nested Adaptive vs Fixed

| Comparison | V1 | V2 | V3 | hV4 |
|------------|:--:|:--:|:--:|:---:|
| **FE-K vs FE-6** | Δ=+0.023, p=0.194 | Δ=+0.031, p=0.367 | Δ=+0.089, p=0.252 | Δ=+0.022, p=0.451 |
| **Nested vs FE-K** | Δ=+0.022, p=0.372 | Δ=−0.006, p=0.637 | Δ=−0.001, p=0.787 | Δ=−0.041, p=0.075 |

→ **Nested adaptive ≈ Fixed FE-K** in all ROIs. Center optimization provides no benefit. hV4 trends **worse** with adaptive centers.

#### Overestimation: Circular vs Nested (HC Mean)

| ROI | Circular M | Nested M | Bias |
|-----|:----------:|:--------:|:----:|
| V1 | +0.195 | +0.175 | +0.020 |
| V2 | +0.242 | +0.174 | +0.068 |
| V3 | +0.167 | +0.110 | +0.056 |
| hV4 | +0.299 | +0.164 | **+0.135** |

Circular optimization inflated hV4 by +0.135 on average. sub-08 hV4: circular=+0.383 → nested=+0.081 (bias=**+0.302**).

#### HC-CVD Gap Decomposition by Model Specification

| ROI | FE-6 d (p) | FE-K d (p) | Gap Reduction |
|-----|:----------:|:----------:|:-------------:|
| V1 | 2.01 (0.021) | 0.44 (0.581) | **−78%** |
| V2 | 2.25 (0.022) | 1.80 (0.067) | −20% |
| V3 | 0.17 (0.819) | 0.18 (0.843) | — |
| hV4 | 1.36 (0.169) | 0.63 (0.342) | **−54%** |

→ **K selection accounts for 54–78% of the HC-CVD LOCO gap** in V1 and hV4. FE-6 was overparameterized (8 stimuli, K=6 → df=1), and CVD is more sensitive to this misspecification.

#### Key Conclusions

1. **Center optimization = no benefit**. The sole model parameter that matters is K (channel count).
2. **Section 4a's circular results invalidated**: sub-08 "degenerate center" pattern was overfitting artifact, not L-M axis compression evidence.
3. **HC-CVD gap is largely model-specification-dependent**: proper K selection reduces the gap dramatically.
4. **Remaining gap after K correction** (hV4 d=0.63) is not statistically significant (p=0.342), but n=3 CVD is severely underpowered. This residual gap is the target for Phase 2 filter.
5. **FE-K gap non-significance does not mean gap=0**: with HC n=7, CVD n=3, we cannot detect d<1.2 at 80% power.

### 4c. Per-Color Residual Analysis & Cross-Phase Integration (Section 9k-3)

#### Purpose

Decompose the aggregate HC-CVD LOCO gap into per-color contributions under FE-K (per-ROI optimal). Identify which colors drive the residual gap and test convergence with Phase 2 SRM prevalidation (independent pipeline).

#### Per-Color LOCO voxel_corr — hV4 FE-3 (Welch t-test, HC n=7 vs CVD n=3)

| Color | θ | HC M (SD) | CVD M (SD) | Cohen's d | t(Welch) | p |
|-------|-----|-----------|-----------|:---------:|:--------:|:---:|
| red | 0° | +0.353 (0.225) | +0.310 (0.255) | +0.18 | 0.25 | 0.81 |
| orange | 45° | +0.246 (0.316) | +0.502 (0.224) | −0.94 | −1.46 | 0.22 |
| yellow | 90° | +0.135 (0.422) | +0.213 (0.167) | −0.24 | −0.42 | 0.70 |
| green | 135° | +0.107 (0.427) | +0.055 (0.338) | +0.13 | 0.21 | 0.85 |
| cyan | 180° | −0.008 (0.401) | +0.157 (0.524) | −0.35 | −0.49 | 0.66 |
| **blue** | **225°** | **+0.349 (0.315)** | **+0.025 (0.114)** | **+1.37** | **2.38** | **0.046*** |
| purple | 270° | +0.283 (0.319) | −0.124 (0.196) | +1.54 | 2.47 | 0.060† |
| magenta | 315° | +0.171 (0.384) | −0.211 (0.246) | +1.19 | 1.88 | 0.127 |

> Warm colors (red–green): no HC-CVD gap under FE-3 (all |d| < 1, all p > 0.2).
> Cool colors (blue, purple): d > 1.3 with trending or significant p-values.

#### Warm/Cool Axis Decomposition

| Axis | Colors | FE-6 HC-CVD Gap | FE-K HC-CVD Gap | Reduction |
|------|--------|:---------------:|:---------------:|:---------:|
| **Warm (L-M)** | red, orange, yellow, green | +0.118 | **−0.060** | **>100% (reversal)** |
| **Cool (S)** | cyan, blue, purple, magenta | +0.362 | **+0.237** | **35%** |

> K optimization completely eliminates warm-color gap (reverses it), but only partially reduces cool-color gap. 65% of the cool-color gap persists after model optimization → **residual biology candidate**.

#### Per-Subject Cool-Color Profile (hV4 FE-3)

| Subject | Group | Warm Mean | Cool Mean | Interpretation |
|---------|-------|:---------:|:---------:|----------------|
| sub-08 | CVD (deutan) | +0.227 | −0.058 | Cool still negative |
| sub-09 | CVD (protan) | +0.340 | −0.197 | Cool worst of 3 |
| sub-10 | CVD (deutan) | +0.244 | +0.140 | Cool positive — compensated |
| HC mean | HC | +0.210 | +0.199 | Balanced warm/cool |

> sub-09 (protan) shows the largest cool-color deficit despite having the highest warm-color performance. sub-10 is the only CVD subject with positive cool-color performance, consistent with SRM Phase 2 showing HC-like profile (compensation hypothesis).

#### Cross-Phase Convergence: SRM Prevalidation ↔ Forward Model

SRM prevalidation (crossnobis pairwise distance in native voxel space) and forward model LOCO (voxel_corr in individual subject space) are **completely independent pipelines** that share no model assumptions.

| Signal | SRM Prevalidation (Phase 2) | Forward Model (Phase F1) | Converge? |
|--------|----------------------------|--------------------------|:---------:|
| Blue-purple distortion | V2 blue-purple p=0.042* (z=[4.34, 0.33, 2.08]) | hV4 blue d=+1.37 p=0.046*; purple d=+1.54 p=0.060† | **YES** |
| Green-blue compression | V1/V2/V3 all-3-deficit (z all negative) | Blue = CVD lowest LOCO color under FE-K | **YES** |
| Red-magenta expansion | V1/V2/hV4 all-3-elevation (z=[0.69–4.96]) | Magenta d=+1.19 p=0.127, red d≈0 | **Partial** |
| Warm = recoverable | sub-08 V2 extreme warm z-scores | Warm gap reversed under FE-K | **YES** |
| sub-10 compensation | SRM: HC-like profile (crossnobis V2 r=0.701) | FE-K: cool still positive (only CVD) | **YES** |

> **Key convergence**: V2 blue-purple is the **only significant group-level pair** in SRM prevalidation (p=0.042), and blue is the **only significant per-color gap** in FE hV4 (p=0.046). Two independent pipelines point to the same color region.

#### Key Conclusions

1. **Residual HC-CVD gap under optimal K is S-axis specific**: blue (d=+1.37, p=0.046) and purple (d=+1.54, p=0.060) drive the cool-color gap.
2. **Warm-color gap is entirely model-specification artifact**: reversed under FE-3 (CVD slightly better than HC on warm colors).
3. **Cross-phase convergence confirmed**: SRM pairwise geometry and forward model interpolation independently identify blue/purple/magenta as CVD distortion locus.
4. **sub-10 compensation**: Only CVD subject with positive cool-color LOCO, consistent with SRM-based compensation hypothesis.
5. **Phase 2 filter implication**: T_ψ(θ) should focus correction on θ ∈ [180°, 315°] (cool/S-axis), with minimal or no correction on θ ∈ [0°, 135°] (warm/L-M axis).

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
6. **HC-CVD gap is K-dependent and axis-specific** (updated §4b–4c): Aggregate gap reduces 54–78% with optimal K. Per-color decomposition reveals warm-color (L-M) gap reverses entirely under FE-K, while cool-color (S-axis) gap persists at 65% of FE-6 level. Blue d=+1.37 p=0.046, purple d=+1.54 p=0.060. Center placement irrelevant.
7. **Prior-based models**: All rejected — SRM prior is fundamentally incompatible with LOCO.
8. **smooth_tikh (9h-9i)**: REJECTED — captures spatial covariance, not color signal. rdm_pearson "improvement" was noise pattern-matching.
9. **Intercept model**: Does not change LOCO significance. Shared spatial mean does not drive results.
10. **Phase 2 roles**: hV4 = color interpolation oracle (permutation p=0.026, FE-3). V1/V2 = secondary (gap largely K-dependent; residual gap underpowered). V3 = conditional (FE-8). **Filter target** (§4c): T_ψ(θ) should focus on θ ∈ [180°, 315°] (cool/S-axis); warm region needs minimal correction.
11. **Leakage prevention**: Including held-out color in A_g inflates LOCO by +0.55 to +0.69. Leakage-free pipeline mandatory.
12. **Cross-phase convergence** (§4c): SRM prevalidation (V2 blue-purple p=0.042) and forward model (hV4 blue p=0.046) independently identify S-axis/cool colors as CVD distortion locus. Crossnobis-SRM Spearman r=0.33–0.70 confirms SRM is not artifact.

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

**Criticism:** 4 ROIs tested; Bonferroni threshold = 0.0125; hV4 p=0.044 fails. Also claims HC-CVD hV4 voxel_corr p=0.169 undermines the result.

**Rebuttal — HC-CVD comparison is irrelevant to encoder validation:**

The permutation test answers: *"Does the HC forward model capture genuine color interpolation signal?"* This is a within-group (HC-only) model validation. The HC-CVD voxel_corr comparison (p=0.169) answers a completely different question: *"Do HC and CVD differ in LOCO performance?"* — which is not required for encoder validation. The "cross-pipeline cherry-picking" accusation is also misframed: Phase 1 permutation validates the encoder, Phase 3 LOCO MAE evaluates decoder-based group differences. These answer separate questions in separate pipelines.

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

### RT-5. "CVD Failure = Data" Narrative (Revised after §4b)

**Criticism:** Unfalsifiable; CVD reliability is HIGHER than HC (contradicting "distortion").

**Updated framing — Model Comparison:**

1. **"Failure = data" revised to "model specification sensitivity":**
   - HC-CVD gap is **primarily K-dependent**: V1 d 2.01→0.44 (−78%), hV4 d 1.36→0.63 (−54%) with per-ROI optimal K
   - Center optimization provides no additional benefit (nested LOCO, §4b)
   - The large FE-6 gap was overparameterization: K=6 with 8 stimuli leaves df=1, insufficient for CVD's representations
   - **Reframing**: CVD LOCO failure under FE-6 is a model selection issue, not necessarily a biological deficit

2. **Higher CVD reliability addressed:**
   - Higher reliability (0.699 vs 0.603) means CVD patterns are **consistently reproduced** across runs
   - This is compatible with "consistently different model specification needs" — reliability measures stability, not model fit

3. **Previous falsifiable prediction — RESOLVED:**
   - ~~Adaptive basis: if CVD centers compress along L-M axis → basis mismatch confirmed~~
   - **Result (§4b)**: Adaptive centers ≈ uniform after debiasing. sub-08 "degenerate [0,180,359]°" was overfitting artifact, not biological compression.
   - **New testable question**: Does CVD K-sensitivity arise from model selection (bias-variance tradeoff) or genuine dimensionality reduction? Requires: (a) PCA effective dimensionality analysis, (b) SNR-controlled simulation, or (c) behavioral correlation

4. **Remaining vulnerability — K-sensitivity interpretation:**
   - CVD benefits more from K reduction than HC → two explanations:
     - (A) Model selection: FE-6 is overparameterized for all subjects; CVD is more affected due to representational differences
     - (B) Biological: CVD genuinely has fewer effective color dimensions
   - Current data (n=3 CVD) cannot distinguish A from B
   - **Neutralization needed**: PCA on 8-color patterns, or behavioral (Farnsworth-Munsell) correlation with K-sensitivity

5. **Phase 2 filter consistency:**
   - `W_s @ C(T_psi(θ)) ≈ Y_CVD(θ)` uses HC-derived W_s (hV4, FE-3, ridge_gcv)
   - With proper K, the filter T_psi corrects a **smaller residual** (d=0.63 vs d=1.36)
   - hV4 RDM HC≈CVD (p=0.559) → T_psi is monotonic (order-preserving)

---

## 11. Eigenspectrum Geometry (Pospisil & Pillow 2024)

> **Status**: PLANNED — Awaiting server execution (scripts/analyze_eigenspectrum_decay.py)
> **Framework**: Broken power law eigenvalue decay analysis

### Motivation

Pospisil & Pillow (2024) demonstrated that V1 population eigenspectrum follows a **broken power law** (α≈0.5 for first ~10 modes, α≈1.2 for later modes), not the simple power law (α≈1) assumed by classical models. This suggests ~10 dominant modes shape sensory encoding, while hundreds of additional modes contribute minimally to signal.

**Key questions for our data:**
1. Does our 8-color Procrustes-aligned data show similar broken power law structure?
2. Do CVD subjects show steeper eigenvalue decay (reduced dimensionality hypothesis)?
3. Does the transition point differ by ROI (V1/V2 vs hV4)?

### Method

For each subject-ROI:
1. Concatenate Procrustes-aligned amplitudes across runs/colors → X matrix (48 samples × n_voxels)
2. Compute sample covariance Σ̂ = (1/n) X^T X
3. Extract eigenvalues λ₁ ≥ λ₂ ≥ ... ≥ λₙ via SVD
4. Fit power law λᵢ = c · i^(-α) to early modes (i=1-10) vs late modes (i=10-50) via log-log regression
5. Compare HC vs CVD: Welch t-test for α_early, α_late, transition point

**Expected patterns:**
- If Pospisil's finding generalizes: α_early ≈ 0.5-0.7, α_late ≈ 1.0-1.5
- If CVD has reduced dimensionality: α_CVD > α_HC (steeper decay)
- If hV4 > V1 in representational richness: more eigenvalues above noise floor in hV4

### Results

**TO BE FILLED** after running `run_eigenspectrum_decay.sbatch`

Expected output:
- Figure: 2×4 subplot (HC/CVD × V1/V2/V3/hV4) log-log eigenvalue decay
- Table: α_early, α_late, transition point, p-values per ROI
- Validation: Do SRM k values (V1=4, V2=4, V3=3, hV4=3) capture the shallow-decay regime?

### Connection to Current Findings

**V1/V2 LOCO null ~0.10-0.13**: Pospisil showed that noise eigenspectrum can create spurious low-dimensional structure. Our V1/V2 permutation null likely arises from voxel correlation structure (spatial autocorrelation, measurement noise) rather than true color signal. Only modes above the noise floor carry genuine color information — if V1/V2 have fewer such modes for 8-color interpolation, this explains LOCO failure despite high LORO accuracy.

**Discrimination ≠ Interpolation**: 8-stimulus interpolation may require dimensions beyond the dominant modes (~10), which are optimized for discrimination (categorical perception, Kuriki et al. 2025) rather than continuous hue gradients. V1/V2 eigenspectrum may show steep decay after first few modes, limiting interpolation capacity even with intact discriminability.

---

## 12. Unbiased Dimensionality Estimation (MEME)

> **Status**: PLANNED — Awaiting server execution (scripts/fit_meme_eigenspectrum.py)
> **Framework**: Moment Estimation via Eigenmoments (Li et al. 2014, Pospisil & Pillow 2024)

### Motivation

Standard PCA eigenvalues are downward-biased when n_samples ≈ n_features (high-dimensional noise regime). With 48 samples (6 runs × 8 colors) and 100-800 voxels per subject-ROI, we are in this regime. **MEME** uses eigenmoment matching to recover true signal eigenspectrum.

**Key question:** Are our manually chosen SRM k values (V1=4, V2=4, V3=3, hV4=3) optimal, or do they under/over-estimate true dimensionality?

### Method

For each subject-ROI:
1. Compute sample eigenvalues (biased)
2. Compute eigenmoments m_p = (1/n) Σ λᵢ^p for p=1,2,3
3. Apply Marchenko-Pastur correction for high-dimensional bias
4. Find best-fit eigenspectrum {λ̃ᵢ} matching observed moments
5. Estimate true rank k* = #{λ̃ᵢ > noise floor}
6. Compare to manual SRM k values

**Validation:** If MEME k*_hV4 ≈ 3-4, confirms current SRM rank choice is optimal.

### Results

**TO BE FILLED** after running `run_meme_estimator.sbatch`

Expected output:
- Figure: MEME eigenvalues (red) vs PCA eigenvalues (black) vs noise ceiling (gray)
- Table: Estimated k* per ROI, comparison to SRM k, HC vs CVD
- Test: Does CVD k* < HC k* (reduced dimensionality hypothesis)?

### Expected Insights

**Phase 1b finding confirmation:** If MEME shows hV4 k*≈3, this validates our FE-3 optimal basis choice. If k*≈6-8, suggests we under-utilized available dimensions.

**CVD dimensionality hypothesis:** If CVD k* significantly < HC k*, supports biological dimensionality reduction (not just model specification, RT-5). If k*_CVD ≈ k*_HC, suggests CVD's K-sensitivity (Section 4b) is purely bias-variance tradeoff, not genuine dimensionality loss.

---

## 13. Voxel Color Preference Maps (Bannert & Bartels 2025)

> **Status**: PLANNED — Awaiting server execution (scripts/map_voxel_color_preference.py)
> **Framework**: KDE+softmax population-level color preference visualization

### Motivation

Current FE weights show voxel tuning to 6-channel basis, but not direct **per-color preference**. Bannert & Bartels (2025) used KDE+softmax to visualize which voxels prefer each color, revealing population-level color biases. This complements our W matrix analysis by showing if HC vs CVD have shifted color preference distributions (e.g., CVD red-preferring voxels shift toward orange).

**Caveat:** Our data lacks retinotopic coordinates → use voxel response magnitude (SNR) as 1D proxy.

### Method

For each ROI × color:
1. Extract mean response per voxel (averaged across runs)
2. Identify voxels with max response to each color → "color-preferring voxels"
3. Apply KDE to response strength distribution
4. Softmax normalization → % deviation from uniform (12.5% for 8 colors)
5. Statistical test: HC vs CVD preference for each color

**Expected pattern:** If CVD shows cortical reorganization, red-preferring voxels should shift toward green/yellow (deutan) or green-preferring toward red/blue (protan).

### Results

**TO BE FILLED** after running `run_voxel_preference.sbatch`

Expected output:
- Figure: 8 polar plots (one per color), showing KDE preference density
- Figure: Bar plots showing voxel count distribution per color (HC vs CVD)
- Table: Significant HC vs CVD differences per color-ROI combination

### Connection to Cross-Decoding (Phase 3)

Our finding that 10/12 CVD→HC cross-decodings succeed (Phase 3) suggests CVD retains HC-like population geometry. If voxel preference maps show **similar spatial distributions** (no shifted peaks), this confirms that CVD color representation is geometrically distorted in *hue space* (stimulus-level filter T_psi, Phase 2 target) but not in *voxel space* (population organization intact).

If CVD shows shifted preference maps (e.g., fewer red-preferring voxels), this would suggest **cortical reorganization** beyond stimulus-level distortion, requiring voxel-space transformations.

---

## 14. Discussion — Literature Integration

### 14.1 Eigenspectrum Geometry and LOCO Null (Pospisil & Pillow 2024)

Pospisil & Pillow (2024) demonstrated that V1 population eigenspectrum follows a broken power law (α≈0.5 for first 10 modes, α≈1.2 thereafter), not the simple power law assumed by classical models. This suggests ~10 dominant modes shape sensory encoding, while hundreds of additional modes contribute minimally.

**Relevance to our V1/V2 LOCO failure:**

Our finding that V1/V2 fail LOCO despite high LORO accuracy may reflect that 8-stimulus interpolation requires dimensions beyond the dominant modes. The dominant modes are optimized for **discrimination** (categorical perception, consistent with Kuriki et al. 2025 categorical task), not **continuous hue gradients** (Kuriki appearance task).

**LOCO null from voxel covariance:** Our V1/V2 permutation null (~0.10-0.13 MAE, not zero) likely arises from voxel correlation structure rather than true color signal. Pospisil showed that noise eigenspectrum can create spurious low-dimensional structure; similarly, spatial correlations among our 8 stimuli may allow weak above-chance LOCO performance even after color-label permutation. Only hV4 significantly exceeds this null (p=0.044), suggesting genuine color-specific interpolation requires modes beyond those captured by early visual cortex for our 8-color task.

**SRM k validation:** If eigenspectrum analysis confirms ~10 dominant modes (α_early regime), our SRM k=3-4 choice captures only the shallowest-decay modes. This may be optimal for **classification** (LORO) but insufficient for **interpolation** (LOCO), explaining the LORO-LOCO dissociation. Higher modes (k>10) may carry continuous hue structure but are discarded by SRM.

### 14.2 Task-Dependent Representation (Kuriki et al. 2025)

Kuriki et al. (2025) found that cortical color representation in V1-V3 differs significantly between categorical judgment vs. appearance (hue-scaling) tasks. Specifically:
- **V1-V3**: Stronger representation during categorical tasks (discrimination)
- **hV4**: Stronger correlation with appearance judgments (continuous hue perception)

**Direct parallel to our LORO-LOCO dissociation:**

| Our Finding | Kuriki Parallel | Interpretation |
|-------------|----------------|----------------|
| V1/V2 LORO: 0.758-0.793 acc | V1-V3 categorical task activation | Discrete category boundaries preserved |
| V1/V2 LOCO: voxel_corr 0.13-0.15 | V1-V3 appearance task weak | Continuous gradients absent |
| hV4 LOCO: voxel_corr 0.183 (p=0.026) | hV4 appearance correlation | Perceptual-level continuous encoding |
| CVD LORO ≈ HC | Categorical boundaries task-independent | Retinal deficit doesn't affect categories |
| CVD hV4 LOCO < HC | Appearance task CVD-sensitive | Perceptual hue gradients distorted |

**Mechanistic explanation:** Kuriki demonstrated that task demands reshape V1-V3 representations through top-down modulation. Our passive RSVP task may default to categorical encoding (preserved in CVD, explaining intact cross-decoding), while continuous hue interpolation (required by LOCO) demands perceptual-level encoding concentrated in hV4. This explains why CVD subjects show:
- **Intact LORO** (categorical boundaries preserved despite L-/M-cone deficit)
- **Impaired hV4 LOCO** (perceptual hue gradients distorted by retinal input distortion)

### 14.3 Shared Population Geometry (Bannert & Bartels 2025)

Bannert & Bartels (2025) used SRM to predict color preferences across subjects in V1-hV4, achieving 39-56% between-subject classification accuracy (8 alternatives). Their key finding: retinotopic color biases are "shared across different human observers" despite individual anatomical variability.

**Convergence with our cross-decoding results (Phase 3):**

Our finding that 10/12 CVD→HC cross-decodings succeed (p<0.05, LDA+SRM) directly validates Bannert's observation. Despite CVD's retinal deficit, the **population-level color geometry** is sufficiently preserved to allow HC-trained decoders to generalize. This suggests:

1. **Voxel-space geometry intact:** CVD does not show cortical reorganization or remapping
2. **Stimulus-space geometry distorted:** CVD's deficit manifests as hue-space transformation T_psi (Phase 2 target), not voxel-space transformation
3. **SRM captures shared structure:** Our SRM k=3-4 extracts the shared color representation that generalizes across HC and CVD

**Voxel preference map prediction:** If Bannert's framework applies to CVD, we expect:
- Similar spatial clustering of color-preferring voxels (no cortical reorganization)
- But potentially shifted preference distributions (e.g., fewer red-preferring voxels in deutan, shifted toward green)
- This would confirm stimulus-level distortion without voxel-level remapping

### 14.4 Dimensionality and Model Specification

**RT-5 question resolved by MEME:** Does CVD K-sensitivity (Section 4b) arise from (A) bias-variance tradeoff or (B) genuine dimensionality reduction?

**MEME prediction:** If k*_CVD < k*_HC significantly, supports (B) biological dimensionality reduction. If k*_CVD ≈ k*_HC, supports (A) model specification issue. This directly addresses the RT-5 vulnerability: "Current data (n=3 CVD) cannot distinguish A from B."

**Connection to Pospisil:** If eigenspectrum shows CVD has steeper decay (higher α), MEME k* will be lower. Combined with behavioral correlation (Farnsworth-Munsell error vs LOCO K-sensitivity), this triangulates whether CVD's LOCO impairment reflects:
- **Fewer effective dimensions** (biological, requires Phase 2 filter to operate in lower-dimensional space)
- **Same dimensions, different tuning** (geometric, requires Phase 2 filter to warp stimulus space)

---

**Last Updated**: 2026-03-13
