# Loss Equations — Bayesian BEST Filter Optimization

**최종 갱신**: 2026-05-13
**Forward model & filter parameters**: (β_s, β_c) ∈ ℝ², θ_conf ∈ {150°, 16°, 11.8°, 175.7°} depending on axis convention

---

## 0. Forward model

8 hue color sample θ ∈ {0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°}.

```
δθ(θ; β_s, β_c, θ_conf) = β_s · cos(θ − 90°)  +  β_c · cos(θ − θ_conf)

θ_perceived(θ) = (θ + δθ(θ)) mod 360°
```

- `β_s` (degrees): S-axis (90°/270°) rotation amplitude — Emery 2021 NT→AT B-Y rotation toward S
- `β_c` (degrees): confusion-axis amplitude (family-specific direction)
- `θ_conf` (degrees): cone-confusion axis angle in chosen color space
  - OLD convention: 150° for both deutan/protan (legacy, used in V1 ΔRDM bootstrap)
  - Stockman opponent space: protan 16°, deutan 163°
  - CIELab L*=75 plane: protan 11.8°, deutan 175.7°

---

## 1. Composite loss (Bayesian framework)

```
L_total(β_s, β_c) = α · L_ccc(V4)  +  (1 − α) · L_lit  +  ε · 50 · Tikh

  α  = 0.3       (data weight)
  ε  = 0.1       (Tikh weight; ×50 scaling for parity)

L_lit = w_E · L_Emery  +  w_T · L_Tregillus  +  w_B · L_Brettel

  w_E = 0.5  (Emery — β_s anchor)
  w_T = 0.5  (Tregillus — norm anchor)
  w_B = 0.3  (Brettel — sign penalty)
```

α=0.3 fixed via sub-09 sign-flip stability (memory): α ≥ 0.4 causes sub-09 BEST β_c sign flip → α=0.3 is the largest α that preserves both subjects' BEST coords.

---

## 2. Individual loss term equations

### 2.1 L_ccc (V4 LOCO neural likelihood)

```
L_ccc = 1 − CCC(vuln_sim, vuln_cvd)
```

where
```
CCC(x, y) = 2 · ρ_xy · σ_x · σ_y  /  (σ_x² + σ_y² + (μ_x − μ_y)²)

ρ_xy = Pearson correlation
σ_x, σ_y = std deviations
μ_x, μ_y = means
```

- `vuln_cvd[θ]` = observed V4 LOCO voxel_corr for CVD subject at each color θ (8 colors)
- `vuln_sim[θ]` = simulator-predicted voxel_corr (HC encoder + δθ-shifted target)
- Range: CCC ∈ [−1, 1], `L_ccc ∈ [0, 2]`. CCC=1 perfect concordance, 0 chance, <0 anti-correlation.

**Note**: vuln_sim 0-clustering 한계 — simulator amplitude only 0.27–0.32× obs range, CCC near 0 even at BEST. This is the **fundamental data limit** that motivated Bayesian framework.

### 2.2 L_Emery (β_s anchor — Emery 2021)

```
L_Emery(β_s) = ((β_s − 21.4) / 10)²
```

- Penalty quadratic in deviation from Emery 21.4°
- Width parameter 10° = ±SD of Emery AT group
- L_Emery(21.4) = 0 (minimum), L_Emery(0) = 4.58, L_Emery(50) = 8.18

**Neural anchor**: V1 ΔRDM bootstrap β_s — sub-08=20°±8 [12, 39], sub-09=23°±10 [2, 36]. Both within Emery CI.

### 2.3 L_Tregillus (norm anchor — Tregillus 2021)

```
L_Tregillus(β_s, β_c) = ((‖(β_s, β_c)‖ − 21.4 · 1.3) / 15)²
                      = ((√(β_s² + β_c²) − 27.82) / 15)²
```

- Penalizes total amplitude `‖(β_s, β_c)‖` deviation from Tregillus 30% overshoot of Emery
- Target: 21.4° × 1.3 = 27.82°
- Width 15° — accommodates 20–40% range
- L_Tregillus(27.82, 0) = 0 (minimum on β_s axis), L_Tregillus(0, 0) = 3.44

**Empirical role** (simplification sweep, 2026-05-13): 제거 시 β_c → 0 collapse, sub-08 P2a −0.088, sub-09 P2a −0.100. **Essential for β_c amplitude maintenance.**

### 2.4 L_Brettel (sign-only penalty — Brettel 1997)

```
L_Brettel(β_c, family) = max(0, −β_c · s_fam / 50)²

s_fam = +1  (deutan; expected β_c > 0 under OLD 150° axis)
       = −1  (protan; expected β_c < 0 under OLD 150° axis)
```

- One-sided penalty: 0 if β_c has expected sign, quadratic otherwise
- Width 50° — soft constraint
- Maximum penalty for wrong-sign |β_c|=50: (50/50)² = 1.0

**Status (2026-05-13)**: sub-08 deutan β_c=−18° (CI excl 0) DISAGREES with Brettel s_fam=+1 in **all** axis conventions tested. See `brettel_reconciliation/brettel_reconciliation.json`. → **★ UNDER VERIFICATION**, consider removal or reformulation.

### 2.5 Tikh (L2 regularizer)

```
Tikh(β_s, β_c) = (β_s² + β_c²) / 32400
                = ‖(β_s, β_c)‖² / 180²
```

- Normalization: 180² so Tikh ≤ 1 over the grid β_s ∈ [0, 50] × β_c ∈ [−50, 50]
- ×50 scaling factor in L_total = compensates for low magnitude relative to L_lit terms
- Pure mathematical regularizer — no neural/literature interpretation
- Removal effect: NO Tikh → β_c can explode (sub-09 SIMPLE_no_Tikh: β_c=−78° amplitude blow-up)

---

## 3. Loss term contribution at BEST coords

### sub-08 deutan, BEST = (22, +18), θ_conf=150° OLD

| Term | Value | Contribution to L_total |
|---|---|---|
| L_ccc | ~1.0 (CCC≈0) | 0.30 × 1.0 = **0.300** |
| L_Emery | ((22−21.4)/10)² = 0.0036 | 0.7 × 0.5 × 0.0036 = 0.0013 |
| L_Tregillus | ((√(22²+18²)−27.82)/15)² = ((28.4−27.82)/15)² = 0.0015 | 0.7 × 0.5 × 0.0015 = 0.0005 |
| L_Brettel | max(0, −18·(+1)/50)² = max(0,-0.36)² = 0 (β_c=+18 right sign) | 0.7 × 0.3 × 0 = 0 |
| Tikh | (484+324)/32400 = 0.0249 | 0.1 × 50 × 0.0249 = 0.125 |
| **L_total** | | **≈ 0.43** |

→ L_ccc dominates (0.30/0.43=70%), Tikh secondary (29%), literature priors negligible since BEST already at Emery+Tregillus anchor.

### sub-09 protan, BEST = (22, −16), θ_conf=150° OLD

| Term | Value | Contribution |
|---|---|---|
| L_ccc | ~1.3 (CCC≈−0.3) | 0.30 × 1.3 = 0.390 |
| L_Emery | 0.0036 | 0.0013 |
| L_Tregillus | ((√(22²+16²)−27.82)/15)² ≈ 0.0001 | 0.00003 |
| L_Brettel | max(0, −(−16)·(−1)/50)² = max(0, −0.32)² = 0 (β_c=−16 right sign for protan) | 0 |
| Tikh | (484+256)/32400 = 0.0228 | 0.114 |
| **L_total** | | **≈ 0.51** |

→ L_ccc 우세 (76%), Tikh (22%), literature priors 거의 inactive (이미 anchor 영역).

---

## 4. Recovery tier classification

| Anchor | Literature | Neural recovery | Empirical essential? | Tier |
|---|---|---|---|---|
| Emery β_s 21.4° | population mean (AT) | sub-08=20°, sub-09=23° both within CI | YES (제거 시 β_s drift to grid edge) | **★★★** |
| Machado Δλ severity | severity bands | sub-08=8.6 mild, sub-09=25.2 severe (axis selection grounding) | YES (axis selection) | **★★★** |
| Tregillus 20-40% | overshoot range | sub-09 g=10% partial; sub-08 outlier | YES (simplification sweep: β_c collapses to 0 without) | **★★** |
| Brettel β_c sign | family-specific sign | sub-08 DISAGREE all axes; sub-09 marginal | NO (empirically inert at BEST) | **★** (검증중) |

---

## 5. Open questions

1. **Brettel reformulation**: Under family-specific axis (CIELab 11.8°/175.7°), expected sign FLIPS for protan but STAYS for deutan. sub-08 DISAGREE under all → consider whether L_Brettel should be removed or replaced with a softer family-aware prior (e.g., "Family-asymmetric Tikh").

2. **Tregillus rationale**: Currently anchors `‖(β_s, β_c)‖ ≈ 28°`. But sub-08 BEST norm=28.4°, sub-09 BEST norm=27.2° → both at Tregillus target. Is this coincidence or driven by Tregillus prior? Sensitivity analysis: replace Tregillus with different overshoot anchors {1.0, 1.3, 1.5}.

3. **α sensitivity**: α=0.3 fixed via sub-09 sign-flip. Sub-08 sensitivity check needed — is α=0.3 also sub-08's optimum or just sub-09's?

4. **Without literature priors**: pure L_ccc + Tikh would give BEST = (0, 0) or (β_s_only_argmin, 0) — degenerate. This confirms that literature priors are essential to escape the L_ccc 0-clustering degeneracy.
