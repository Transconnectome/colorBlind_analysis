# S7 Nested-LOO Selection Report

**Design**: Outer 7-fold LOO over HC × inner C(6,4)=15 subset resample × 5 λ on gamma_plus_RDM probe × (R+C [3 Δλ sources] + 2-comp).

**Robustness statement**: Inner CoV measures parameter stability on a 6-HC pool that excludes the outer held-out HC; 
test L_γ is evaluated on the held-out HC at the inner-median δθ. 
Lower inner CoV = more stable selection. Test L_γ is a *Crawford-Howell-style specificity check*: 
if fitted (g) or (β_s, β_c) captures real CVD-axis distortion, applying it to HC should INCREASE L_γ relative to HC's near-zero baseline. 
**Lower test L_γ does NOT mean better filter** — it can mean the fit looks HC-like (selection false positive).

**Comparison with single-LOO S7** (`lambda_optimal_behav_rdm.json`): single-LOO trains on k=5 subsets within full 7-HC pool and tests on complement (1-2 HC). 
Nested-LOO trains on k=4 within 6-HC pool, tests on outer held-out HC. 
Test denominators differ → numerical L_γ values are not directly comparable; 
only the QUALITATIVE patterns (best λ, model rank by CoV) are compared.

---

## sub-08_V1  (family=deutan, K=6, JND=yes)

### 2comp

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | (43.4, -36.9) | 0.1065 | 0.57 | 5.6229 | 7 |
| 0.25 | (0.0, 2.0) | 3.0703 | 0.91 | 1.7118 | 7 |
| 0.50 | (0.0, 2.0) | 3.0703 | 0.91 | 1.7118 | 7 |
| 0.75 | (0.0, 2.0) | 3.0703 | 0.91 | 1.7118 | 7 |
| 1.00 | (0.0, 2.0) | 3.0703 | 0.91 | 1.7118 | 7 |

### rc_Boehm_mid

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 2.914 | 0.0791 | 0.40 | 1.9804 | 7 |
| 0.25 | 1.900 | 0.0138 | 0.00 | 1.7383 | 7 |
| 0.50 | 1.900 | 0.0138 | 0.00 | 1.7383 | 7 |
| 0.75 | 1.900 | 0.0138 | 0.00 | 1.7383 | 7 |
| 1.00 | 1.900 | 0.1177 | 0.03 | 1.7383 | 7 |

### rc_DPS_lit

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 2.993 | 0.0695 | 0.74 | 1.8297 | 7 |
| 0.25 | 1.921 | 0.2055 | 0.20 | 1.7348 | 7 |
| 0.50 | 1.900 | 0.0236 | 0.00 | 1.7310 | 7 |
| 0.75 | 1.900 | 0.0166 | 0.00 | 1.7310 | 7 |
| 1.00 | 1.900 | 0.1201 | 0.03 | 1.7310 | 7 |

### rc_JND_Lamb

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 2.979 | 0.0721 | 0.74 | 1.8864 | 7 |
| 0.25 | 1.900 | 0.1520 | 0.09 | 1.7329 | 7 |
| 0.50 | 1.900 | 0.0166 | 0.00 | 1.7329 | 7 |
| 0.75 | 1.900 | 0.0166 | 0.00 | 1.7329 | 7 |
| 1.00 | 1.900 | 0.1201 | 0.03 | 1.7329 | 7 |

**Optimal λ (lowest inner CoV, non-degenerate boundary_rate ≤ 0.5):**

- 2comp: ALL degenerate (boundary > 0.5 or no valid fit)
- **rc_Boehm_mid**: λ=0.25, g=1.900, inner_CoV=0.0138, test_L_γ_mean=1.7383
- **rc_DPS_lit**: λ=0.75, g=1.900, inner_CoV=0.0166, test_L_γ_mean=1.7310
- **rc_JND_Lamb**: λ=0.50, g=1.900, inner_CoV=0.0166, test_L_γ_mean=1.7329

---

## sub-08_V2  (family=deutan, K=6, JND=yes)

### 2comp

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | (43.4, -36.9) | 0.1065 | 0.57 | 5.6229 | 7 |
| 0.25 | (0.3, -26.0) | 1.1861 | 0.66 | 4.7214 | 7 |
| 0.50 | (0.3, -26.0) | 1.1861 | 0.66 | 4.7214 | 7 |
| 0.75 | (0.3, -26.0) | 1.1861 | 0.66 | 4.7214 | 7 |
| 1.00 | (0.3, -26.0) | 1.1861 | 0.66 | 4.7214 | 7 |

### rc_Boehm_mid

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 2.914 | 0.0791 | 0.40 | 1.9804 | 7 |
| 0.25 | 2.421 | 0.1376 | 0.06 | 1.6409 | 7 |
| 0.50 | 2.243 | 0.2002 | 0.00 | 1.6720 | 7 |
| 0.75 | 2.107 | 0.3308 | 0.00 | 1.6672 | 7 |
| 1.00 | 1.786 | 0.4171 | 0.29 | 9.7065 | 7 |

### rc_DPS_lit

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 2.993 | 0.0695 | 0.74 | 1.8297 | 7 |
| 0.25 | 2.971 | 0.1177 | 0.57 | 1.8130 | 7 |
| 0.50 | 2.050 | 0.1881 | 0.23 | 1.7032 | 7 |
| 0.75 | 2.050 | 0.0000 | 0.00 | 1.7032 | 7 |
| 1.00 | 2.050 | 0.2620 | 0.11 | 1.7032 | 7 |

### rc_JND_Lamb

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 2.979 | 0.0721 | 0.74 | 1.8864 | 7 |
| 0.25 | 2.843 | 0.1577 | 0.60 | 1.7669 | 7 |
| 0.50 | 2.050 | 0.1630 | 0.14 | 1.7027 | 7 |
| 0.75 | 2.050 | 0.0000 | 0.00 | 1.7027 | 7 |
| 1.00 | 2.050 | 0.2620 | 0.11 | 1.7027 | 7 |

**Optimal λ (lowest inner CoV, non-degenerate boundary_rate ≤ 0.5):**

- 2comp: ALL degenerate (boundary > 0.5 or no valid fit)
- **rc_Boehm_mid**: λ=0.00, g=2.914, inner_CoV=0.0791, test_L_γ_mean=1.9804
- **rc_DPS_lit**: λ=0.75, g=2.050, inner_CoV=0.0000, test_L_γ_mean=1.7032
- **rc_JND_Lamb**: λ=0.75, g=2.050, inner_CoV=0.0000, test_L_γ_mean=1.7027

---

## sub-08_V3  (family=deutan, K=6, JND=yes)

### 2comp

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | (43.4, -36.9) | 0.1065 | 0.57 | 5.6229 | 7 |
| 0.25 | (0.0, 5.4) | 4.8566 | 1.00 | 1.7424 | 7 |
| 0.50 | (0.0, 5.4) | 4.8566 | 1.00 | 1.7424 | 7 |
| 0.75 | (0.0, 5.4) | 4.8566 | 1.00 | 1.7424 | 7 |
| 1.00 | (0.0, 5.4) | 4.8566 | 1.00 | 1.7424 | 7 |

### rc_Boehm_mid

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 2.914 | 0.0791 | 0.40 | 1.9804 | 7 |
| 0.25 | 1.900 | 0.0875 | 0.00 | 1.7383 | 7 |
| 0.50 | 1.900 | 0.1956 | 0.00 | 1.7383 | 7 |
| 0.75 | 1.600 | 0.3328 | 0.00 | 2.1243 | 7 |
| 1.00 | 1.600 | 0.3575 | 0.00 | 2.1243 | 7 |

### rc_DPS_lit

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 2.993 | 0.0695 | 0.74 | 1.8297 | 7 |
| 0.25 | 1.900 | 0.2537 | 0.29 | 1.7310 | 7 |
| 0.50 | 1.900 | 0.0846 | 0.00 | 1.7310 | 7 |
| 0.75 | 1.900 | 0.1055 | 0.00 | 1.7310 | 7 |
| 1.00 | 1.186 | 0.7988 | 0.00 | 2.1032 | 7 |

### rc_JND_Lamb

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 2.979 | 0.0721 | 0.74 | 1.8864 | 7 |
| 0.25 | 1.900 | 0.1418 | 0.09 | 1.7329 | 7 |
| 0.50 | 1.900 | 0.0641 | 0.00 | 1.7329 | 7 |
| 0.75 | 1.900 | 0.1328 | 0.00 | 1.7329 | 7 |
| 1.00 | 1.186 | 0.7432 | 0.00 | 2.1550 | 7 |

**Optimal λ (lowest inner CoV, non-degenerate boundary_rate ≤ 0.5):**

- 2comp: ALL degenerate (boundary > 0.5 or no valid fit)
- **rc_Boehm_mid**: λ=0.00, g=2.914, inner_CoV=0.0791, test_L_γ_mean=1.9804
- **rc_DPS_lit**: λ=0.50, g=1.900, inner_CoV=0.0846, test_L_γ_mean=1.7310
- **rc_JND_Lamb**: λ=0.50, g=1.900, inner_CoV=0.0641, test_L_γ_mean=1.7329

---

## sub-08_V4  (family=deutan, K=6, JND=yes)

### 2comp

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | (34.3, -39.4) | 0.1037 | 0.07 | 8.1948 | 6 |
| 0.25 | (44.6, -27.7) | 0.2198 | 0.73 | 11.1890 | 6 |
| 0.50 | (44.6, -27.7) | 0.2198 | 0.73 | 11.1890 | 6 |
| 0.75 | (44.6, -27.7) | 0.2198 | 0.73 | 11.1890 | 6 |
| 1.00 | (44.6, -27.7) | 0.2198 | 0.73 | 11.1890 | 6 |

### rc_Boehm_mid

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 2.857 | 0.1065 | 0.40 | 2.8412 | 6 |
| 0.25 | 1.814 | 0.4196 | 0.33 | 2.9700 | 6 |
| 0.50 | 1.686 | 0.4195 | 0.27 | 3.3112 | 6 |
| 0.75 | 1.686 | 0.4262 | 0.27 | 3.3112 | 6 |
| 1.00 | 1.686 | 0.4262 | 0.27 | 3.3112 | 6 |

### rc_DPS_lit

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 2.921 | 0.1021 | 0.60 | 2.5962 | 6 |
| 0.25 | 2.821 | 0.1643 | 0.67 | 3.0529 | 6 |
| 0.50 | 1.907 | 0.3032 | 0.27 | 2.6197 | 6 |
| 0.75 | 1.600 | 0.3681 | 0.20 | 2.6035 | 6 |
| 1.00 | 1.143 | 0.7238 | 0.13 | 3.0786 | 6 |

### rc_JND_Lamb

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 2.921 | 0.1028 | 0.60 | 2.6657 | 6 |
| 0.25 | 2.643 | 0.2251 | 0.53 | 3.1107 | 6 |
| 0.50 | 1.864 | 0.3328 | 0.27 | 2.6367 | 6 |
| 0.75 | 1.407 | 0.4467 | 0.20 | 3.0459 | 6 |
| 1.00 | 1.286 | 0.4915 | 0.20 | 3.2528 | 6 |

**Optimal λ (lowest inner CoV, non-degenerate boundary_rate ≤ 0.5):**

- **2comp**: λ=0.00, (β_s=34.3, β_c=-39.4), inner_CoV=0.1037, test_L_γ_mean=8.1948
- **rc_Boehm_mid**: λ=0.00, g=2.857, inner_CoV=0.1065, test_L_γ_mean=2.8412
- **rc_DPS_lit**: λ=0.50, g=1.907, inner_CoV=0.3032, test_L_γ_mean=2.6197
- **rc_JND_Lamb**: λ=0.50, g=1.864, inner_CoV=0.3328, test_L_γ_mean=2.6367

---

## sub-09_V1  (family=protan, K=6, JND=yes)

### 2comp

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | (26.3, 4.3) | 0.1689 | 0.00 | 2.8151 | 7 |
| 0.25 | (2.0, 47.1) | 0.2988 | 0.69 | 22.3871 | 7 |
| 0.50 | (2.0, 47.1) | 0.3000 | 0.69 | 22.3871 | 7 |
| 0.75 | (2.0, 47.1) | 0.3000 | 0.69 | 22.3871 | 7 |
| 1.00 | (2.0, 47.1) | 0.3000 | 0.69 | 22.3871 | 7 |

### rc_Boehm_low

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 0.207 | 1.7523 | 0.49 | 2.0739 | 7 |
| 0.25 | 0.164 | 3.1487 | 0.49 | 2.1133 | 7 |
| 0.50 | 1.793 | 1.1218 | 0.17 | 1.7630 | 7 |
| 0.75 | 2.086 | 0.3002 | 0.09 | 1.7067 | 7 |
| 1.00 | 2.171 | 0.2864 | 0.06 | 1.7060 | 7 |

### rc_DPS_lit

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 1.357 | 0.0997 | 0.00 | 2.5804 | 7 |
| 0.25 | 2.100 | 0.3110 | 0.14 | 1.6858 | 7 |
| 0.50 | 2.100 | 0.3138 | 0.14 | 1.6858 | 7 |
| 0.75 | 2.100 | 0.3157 | 0.14 | 1.6858 | 7 |
| 1.00 | 2.100 | 0.3157 | 0.14 | 1.6858 | 7 |

### rc_JND_Lamb

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 0.029 | 3.8772 | 0.77 | 1.8440 | 7 |
| 0.25 | 0.000 | NA | 0.83 | 1.8470 | 7 |
| 0.50 | 1.957 | 0.4312 | 0.23 | 1.7063 | 7 |
| 0.75 | 2.164 | 0.1152 | 0.00 | 1.7082 | 7 |
| 1.00 | 2.207 | 0.1381 | 0.00 | 1.7084 | 7 |

**Optimal λ (lowest inner CoV, non-degenerate boundary_rate ≤ 0.5):**

- **2comp**: λ=0.00, (β_s=26.3, β_c=4.3), inner_CoV=0.1689, test_L_γ_mean=2.8151
- **rc_Boehm_low**: λ=1.00, g=2.171, inner_CoV=0.2864, test_L_γ_mean=1.7060
- **rc_DPS_lit**: λ=0.00, g=1.357, inner_CoV=0.0997, test_L_γ_mean=2.5804
- **rc_JND_Lamb**: λ=0.75, g=2.164, inner_CoV=0.1152, test_L_γ_mean=1.7082

---

## sub-09_V2  (family=protan, K=6, JND=yes)

### 2comp

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | (26.3, 4.3) | 0.1689 | 0.00 | 2.8151 | 7 |
| 0.25 | (6.6, 20.3) | 0.7884 | 0.11 | 2.4765 | 7 |
| 0.50 | (6.6, 20.3) | 0.7894 | 0.11 | 2.4765 | 7 |
| 0.75 | (6.6, 20.3) | 0.7894 | 0.11 | 2.4765 | 7 |
| 1.00 | (6.6, 20.3) | 0.7894 | 0.11 | 2.4765 | 7 |

### rc_Boehm_low

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 0.207 | 1.7523 | 0.49 | 2.0739 | 7 |
| 0.25 | 0.186 | 2.5411 | 0.49 | 2.0933 | 7 |
| 0.50 | 2.050 | 0.3629 | 0.20 | 1.7078 | 7 |
| 0.75 | 2.093 | 0.0452 | 0.00 | 1.7112 | 7 |
| 1.00 | 2.150 | 0.0860 | 0.00 | 1.7037 | 7 |

### rc_DPS_lit

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 1.357 | 0.0997 | 0.00 | 2.5804 | 7 |
| 0.25 | 2.143 | 0.0800 | 0.00 | 1.7013 | 7 |
| 0.50 | 2.143 | 0.0800 | 0.00 | 1.7013 | 7 |
| 0.75 | 2.143 | 0.0800 | 0.00 | 1.7013 | 7 |
| 1.00 | 2.143 | 0.0800 | 0.00 | 1.7013 | 7 |

### rc_JND_Lamb

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 0.029 | 3.8772 | 0.77 | 1.8440 | 7 |
| 0.25 | 0.029 | 4.9167 | 0.77 | 1.8440 | 7 |
| 0.50 | 1.800 | 0.4254 | 0.37 | 1.6750 | 7 |
| 0.75 | 2.121 | 0.0554 | 0.00 | 1.7078 | 7 |
| 1.00 | 2.350 | 0.0658 | 0.00 | 1.7040 | 7 |

**Optimal λ (lowest inner CoV, non-degenerate boundary_rate ≤ 0.5):**

- **2comp**: λ=0.00, (β_s=26.3, β_c=4.3), inner_CoV=0.1689, test_L_γ_mean=2.8151
- **rc_Boehm_low**: λ=0.75, g=2.093, inner_CoV=0.0452, test_L_γ_mean=1.7112
- **rc_DPS_lit**: λ=0.25, g=2.143, inner_CoV=0.0800, test_L_γ_mean=1.7013
- **rc_JND_Lamb**: λ=0.75, g=2.121, inner_CoV=0.0554, test_L_γ_mean=1.7078

---

## sub-09_V3  (family=protan, K=6, JND=yes)

### 2comp

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | (26.3, 4.3) | 0.1689 | 0.00 | 2.8151 | 7 |
| 0.25 | (4.3, -10.6) | 0.6627 | 0.51 | 1.8922 | 7 |
| 0.50 | (4.3, -10.6) | 0.6693 | 0.51 | 1.8922 | 7 |
| 0.75 | (4.3, -10.6) | 0.6693 | 0.51 | 1.8922 | 7 |
| 1.00 | (4.3, -10.6) | 0.6693 | 0.51 | 1.8922 | 7 |

### rc_Boehm_low

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 0.207 | 1.7523 | 0.49 | 2.0739 | 7 |
| 0.25 | 0.079 | 1.6253 | 0.63 | 2.2005 | 7 |
| 0.50 | 0.293 | 0.4442 | 0.66 | 2.1701 | 7 |
| 0.75 | 0.293 | 0.4287 | 0.63 | 2.1701 | 7 |
| 1.00 | 0.314 | 0.4169 | 0.60 | 2.1748 | 7 |

### rc_DPS_lit

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 1.357 | 0.0997 | 0.00 | 2.5804 | 7 |
| 0.25 | 0.743 | 0.2977 | 0.00 | 53.7536 | 7 |
| 0.50 | 0.700 | 0.2631 | 0.00 | 67.5563 | 7 |
| 0.75 | 0.700 | 0.2573 | 0.00 | 67.5563 | 7 |
| 1.00 | 0.700 | 0.2713 | 0.00 | 67.5563 | 7 |

### rc_JND_Lamb

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 0.029 | 3.8772 | 0.77 | 1.8440 | 7 |
| 0.25 | 0.000 | NA | 0.80 | 1.8470 | 7 |
| 0.50 | 0.307 | 0.2563 | 0.57 | 1.8302 | 7 |
| 0.75 | 1.829 | 0.3978 | 0.31 | 1.6888 | 7 |
| 1.00 | 2.136 | 0.4145 | 0.29 | 1.7082 | 7 |

**Optimal λ (lowest inner CoV, non-degenerate boundary_rate ≤ 0.5):**

- **2comp**: λ=0.00, (β_s=26.3, β_c=4.3), inner_CoV=0.1689, test_L_γ_mean=2.8151
- **rc_Boehm_low**: λ=0.00, g=0.207, inner_CoV=1.7523, test_L_γ_mean=2.0739
- **rc_DPS_lit**: λ=0.00, g=1.357, inner_CoV=0.0997, test_L_γ_mean=2.5804
- **rc_JND_Lamb**: λ=0.75, g=1.829, inner_CoV=0.3978, test_L_γ_mean=1.6888

---

## sub-09_V4  (family=protan, K=6, JND=yes)

### 2comp

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | (24.3, 4.6) | 0.1526 | 0.00 | 4.1457 | 6 |
| 0.25 | (0.0, 4.0) | 0.1217 | 0.80 | 2.3806 | 6 |
| 0.50 | (0.0, 4.0) | 0.1217 | 0.80 | 2.3806 | 6 |
| 0.75 | (0.0, 4.0) | 0.1217 | 0.80 | 2.3806 | 6 |
| 1.00 | (0.0, 4.0) | 0.1217 | 0.80 | 2.3806 | 6 |

### rc_Boehm_low

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 0.407 | 1.8255 | 0.40 | 2.9855 | 6 |
| 0.25 | 0.386 | 4.6908 | 0.47 | 3.0203 | 6 |
| 0.50 | 1.857 | 0.3829 | 0.27 | 2.7830 | 6 |
| 0.75 | 2.243 | 0.0451 | 0.00 | 2.2645 | 6 |
| 1.00 | 2.329 | 0.0706 | 0.00 | 2.2223 | 6 |

### rc_DPS_lit

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 1.464 | 0.0803 | 0.00 | 3.8041 | 6 |
| 0.25 | 1.907 | 0.4226 | 0.00 | 22.5900 | 6 |
| 0.50 | 1.907 | 0.4029 | 0.00 | 22.5900 | 6 |
| 0.75 | 1.907 | 0.4029 | 0.00 | 22.5900 | 6 |
| 1.00 | 1.907 | 0.3904 | 0.00 | 22.5900 | 6 |

### rc_JND_Lamb

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | 0.229 | 0.3426 | 0.67 | 2.4483 | 6 |
| 0.25 | 0.279 | 0.1274 | 0.67 | 2.4419 | 6 |
| 0.50 | 1.843 | 0.4049 | 0.27 | 2.4225 | 6 |
| 0.75 | 2.379 | 0.0802 | 0.00 | 2.2538 | 6 |
| 1.00 | 2.421 | 0.0757 | 0.00 | 2.2665 | 6 |

**Optimal λ (lowest inner CoV, non-degenerate boundary_rate ≤ 0.5):**

- **2comp**: λ=0.00, (β_s=24.3, β_c=4.6), inner_CoV=0.1526, test_L_γ_mean=4.1457
- **rc_Boehm_low**: λ=0.75, g=2.243, inner_CoV=0.0451, test_L_γ_mean=2.2645
- **rc_DPS_lit**: λ=0.00, g=1.464, inner_CoV=0.0803, test_L_γ_mean=3.8041
- **rc_JND_Lamb**: λ=1.00, g=2.421, inner_CoV=0.0757, test_L_γ_mean=2.2665

---

## sub-10_V1  (family=deutan, K=6, JND=NO)

### 2comp

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | (NA, NA) | NA | NA | NA | 0 |
| 0.25 | (NA, NA) | NA | NA | NA | 0 |
| 0.50 | (NA, NA) | NA | NA | NA | 0 |
| 0.75 | (NA, NA) | NA | NA | NA | 0 |
| 1.00 | (7.7, 28.3) | 0.1689 | 0.91 | 11.7243 | 7 |

### rc_Boehm_mid

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | NA | NA | NA | NA | 0 |
| 0.25 | NA | NA | NA | NA | 0 |
| 0.50 | NA | NA | NA | NA | 0 |
| 0.75 | NA | NA | NA | NA | 0 |
| 1.00 | 1.979 | 1.2407 | 0.54 | 3.1271 | 7 |

### rc_DPS_lit

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | NA | NA | NA | NA | 0 |
| 0.25 | NA | NA | NA | NA | 0 |
| 0.50 | NA | NA | NA | NA | 0 |
| 0.75 | NA | NA | NA | NA | 0 |
| 1.00 | 1.529 | 3.6581 | 0.26 | 2.3884 | 7 |

### rc_JND_Lamb

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | NA | NA | NA | NA | 0 |
| 0.25 | NA | NA | NA | NA | 0 |
| 0.50 | NA | NA | NA | NA | 0 |
| 0.75 | NA | NA | NA | NA | 0 |
| 1.00 | 1.579 | 2.6042 | 0.49 | 2.5472 | 7 |

**Optimal λ (lowest inner CoV, non-degenerate boundary_rate ≤ 0.5):**

- 2comp: ALL degenerate (boundary > 0.5 or no valid fit)
- rc_Boehm_mid: ALL degenerate (boundary > 0.5 or no valid fit)
- **rc_DPS_lit**: λ=1.00, g=1.529, inner_CoV=3.6581, test_L_γ_mean=2.3884
- **rc_JND_Lamb**: λ=1.00, g=1.579, inner_CoV=2.6042, test_L_γ_mean=2.5472

---

## sub-10_V2  (family=deutan, K=6, JND=NO)

### 2comp

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | (NA, NA) | NA | NA | NA | 0 |
| 0.25 | (NA, NA) | NA | NA | NA | 0 |
| 0.50 | (NA, NA) | NA | NA | NA | 0 |
| 0.75 | (NA, NA) | NA | NA | NA | 0 |
| 1.00 | (12.9, -46.3) | 0.2318 | 0.40 | 7.0362 | 7 |

### rc_Boehm_mid

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | NA | NA | NA | NA | 0 |
| 0.25 | NA | NA | NA | NA | 0 |
| 0.50 | NA | NA | NA | NA | 0 |
| 0.75 | NA | NA | NA | NA | 0 |
| 1.00 | 2.207 | 0.2709 | 0.09 | 1.7117 | 7 |

### rc_DPS_lit

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | NA | NA | NA | NA | 0 |
| 0.25 | NA | NA | NA | NA | 0 |
| 0.50 | NA | NA | NA | NA | 0 |
| 0.75 | NA | NA | NA | NA | 0 |
| 1.00 | 2.314 | 0.1463 | 0.00 | 1.7514 | 7 |

### rc_JND_Lamb

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | NA | NA | NA | NA | 0 |
| 0.25 | NA | NA | NA | NA | 0 |
| 0.50 | NA | NA | NA | NA | 0 |
| 0.75 | NA | NA | NA | NA | 0 |
| 1.00 | 2.307 | 0.1479 | 0.14 | 1.7987 | 7 |

**Optimal λ (lowest inner CoV, non-degenerate boundary_rate ≤ 0.5):**

- **2comp**: λ=1.00, (β_s=12.9, β_c=-46.3), inner_CoV=0.2318, test_L_γ_mean=7.0362
- **rc_Boehm_mid**: λ=1.00, g=2.207, inner_CoV=0.2709, test_L_γ_mean=1.7117
- **rc_DPS_lit**: λ=1.00, g=2.314, inner_CoV=0.1463, test_L_γ_mean=1.7514
- **rc_JND_Lamb**: λ=1.00, g=2.307, inner_CoV=0.1479, test_L_γ_mean=1.7987

---

## sub-10_V3  (family=deutan, K=6, JND=NO)

### 2comp

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | (NA, NA) | NA | NA | NA | 0 |
| 0.25 | (NA, NA) | NA | NA | NA | 0 |
| 0.50 | (NA, NA) | NA | NA | NA | 0 |
| 0.75 | (NA, NA) | NA | NA | NA | 0 |
| 1.00 | (0.0, -18.3) | 0.6224 | 0.94 | 2.0805 | 7 |

### rc_Boehm_mid

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | NA | NA | NA | NA | 0 |
| 0.25 | NA | NA | NA | NA | 0 |
| 0.50 | NA | NA | NA | NA | 0 |
| 0.75 | NA | NA | NA | NA | 0 |
| 1.00 | 2.629 | 0.4240 | 0.60 | 1.6639 | 7 |

### rc_DPS_lit

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | NA | NA | NA | NA | 0 |
| 0.25 | NA | NA | NA | NA | 0 |
| 0.50 | NA | NA | NA | NA | 0 |
| 0.75 | NA | NA | NA | NA | 0 |
| 1.00 | 2.793 | 0.3161 | 0.11 | 1.6954 | 7 |

### rc_JND_Lamb

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | NA | NA | NA | NA | 0 |
| 0.25 | NA | NA | NA | NA | 0 |
| 0.50 | NA | NA | NA | NA | 0 |
| 0.75 | NA | NA | NA | NA | 0 |
| 1.00 | 2.779 | 0.3460 | 0.66 | 1.6908 | 7 |

**Optimal λ (lowest inner CoV, non-degenerate boundary_rate ≤ 0.5):**

- 2comp: ALL degenerate (boundary > 0.5 or no valid fit)
- rc_Boehm_mid: ALL degenerate (boundary > 0.5 or no valid fit)
- **rc_DPS_lit**: λ=1.00, g=2.793, inner_CoV=0.3161, test_L_γ_mean=1.6954
- rc_JND_Lamb: ALL degenerate (boundary > 0.5 or no valid fit)

---

## sub-10_V4  (family=deutan, K=6, JND=NO)

### 2comp

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | (NA, NA) | NA | NA | NA | 0 |
| 0.25 | (NA, NA) | NA | NA | NA | 0 |
| 0.50 | (NA, NA) | NA | NA | NA | 0 |
| 0.75 | (NA, NA) | NA | NA | NA | 0 |
| 1.00 | (38.3, -43.4) | 0.2336 | 0.73 | 23.1137 | 6 |

### rc_Boehm_mid

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | NA | NA | NA | NA | 0 |
| 0.25 | NA | NA | NA | NA | 0 |
| 0.50 | NA | NA | NA | NA | 0 |
| 0.75 | NA | NA | NA | NA | 0 |
| 1.00 | 1.407 | 0.3877 | 0.20 | 3.0151 | 6 |

### rc_DPS_lit

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | NA | NA | NA | NA | 0 |
| 0.25 | NA | NA | NA | NA | 0 |
| 0.50 | NA | NA | NA | NA | 0 |
| 0.75 | NA | NA | NA | NA | 0 |
| 1.00 | 1.107 | 0.5030 | 0.00 | 3.0615 | 6 |

### rc_JND_Lamb

| λ | param/(β_s,β_c) | inner_CoV_mean | boundary_rate | test_L_γ_mean | n_outer_test |
|---|---|---|---|---|---|
| 0.00 | NA | NA | NA | NA | 0 |
| 0.25 | NA | NA | NA | NA | 0 |
| 0.50 | NA | NA | NA | NA | 0 |
| 0.75 | NA | NA | NA | NA | 0 |
| 1.00 | 1.221 | 0.4639 | 0.07 | 2.8635 | 6 |

**Optimal λ (lowest inner CoV, non-degenerate boundary_rate ≤ 0.5):**

- 2comp: ALL degenerate (boundary > 0.5 or no valid fit)
- **rc_Boehm_mid**: λ=1.00, g=1.407, inner_CoV=0.3877, test_L_γ_mean=3.0151
- **rc_DPS_lit**: λ=1.00, g=1.107, inner_CoV=0.5030, test_L_γ_mean=3.0615
- **rc_JND_Lamb**: λ=1.00, g=1.221, inner_CoV=0.4639, test_L_γ_mean=2.8635

---

## Comparison with single-LOO S7

Single-LOO source: `results/s7_loss_combo_subset/lambda_optimal_behav_rdm.json`. 
For each cell, we compare nested-LOO optimal λ to single-LOO optimal λ on `rc_DPS` and `2comp`.

| Cell | Model | Single-LOO opt λ | Single g/(β_s,β_c) | Nested opt λ | Nested g/(β_s,β_c) | Same λ? |
|---|---|---|---|---|---|---|
| sub-08_V1 | rc_DPS | 0.25 | 2.15 | 0.75 | 1.90 | NO |
| sub-08_V2 | rc_DPS | 0.25 | 2.70 | 0.75 | 2.05 | NO |
| sub-08_V3 | rc_DPS | 0.75 | 0.35 | 0.50 | 1.90 | NO |
| sub-08_V4 | rc_DPS | 0.00 | 2.05 | 0.50 | 1.91 | NO |
| sub-08_V4 | 2comp | NA | NA | 0.00 | (34.3,-39.4) | NO |
| sub-09_V1 | rc_DPS | 0.00 | 2.60 | 0.00 | 1.36 | yes |
| sub-09_V1 | 2comp | 0.00 | 26.31 | 0.00 | (26.3,4.3) | yes |
| sub-09_V2 | rc_DPS | 0.00 | 2.60 | 0.25 | 2.14 | NO |
| sub-09_V2 | 2comp | 0.00 | 26.31 | 0.00 | (26.3,4.3) | yes |
| sub-09_V3 | rc_DPS | 0.00 | 2.60 | 0.00 | 1.36 | yes |
| sub-09_V3 | 2comp | 0.00 | 26.31 | 0.00 | (26.3,4.3) | yes |
| sub-09_V4 | rc_DPS | NA | NA | 0.00 | 1.46 | NO |
| sub-09_V4 | 2comp | NA | NA | 0.00 | (24.3,4.6) | NO |
| sub-10_V1 | rc_DPS | NA | NA | 1.00 | 1.53 | NO |
| sub-10_V2 | rc_DPS | NA | NA | 1.00 | 2.31 | NO |
| sub-10_V2 | 2comp | NA | NA | 1.00 | (12.9,-46.3) | NO |
| sub-10_V3 | rc_DPS | NA | NA | 1.00 | 2.79 | NO |
| sub-10_V4 | rc_DPS | NA | NA | 1.00 | 1.11 | NO |

## Notes / Caveats

- Sub-10 cells (V1–V4) have no JND data → L_γ unavailable. Only λ=1.0 (pure L_RDM) has fit values via single-loss fallback; other λ are all None.
- HC sub-04 outlier is in the inner pool for 6/7 outer folds. Nested-LOO does NOT remove its influence — 
  it merely de-couples it from the test denominator on the fold where sub-04 is held out.
- Inner k=4 (C(6,4)=15) chosen to match single-LOO k=5 in 'pool minus one' arithmetic; 
  with k=4, inner subsets are more diverse → CoV is upper-bounded relative to single-LOO k=5.
- Test L_γ semantics: test loss closure uses HC_i as TARGET (not CVD subject) with inner_pool as JND baseline. Evaluates L_γ at median(δθ) from CVD fits. A fitted CVD distortion applied to HC should yield L_γ HIGHER than baseline (since HC has no distortion). Read direction with care.
- This nested-LOO is a *robustness check*. The PI feedback on double-dipping is only PARTIALLY addressed: 
  inner CoV is double-dip-free, but the data is still the same fMRI dataset. 
  Real validation = separate behavioral filter test (Phase 3).
