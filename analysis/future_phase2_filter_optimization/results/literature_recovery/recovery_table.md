# Neural recovery of literature CVD predictions — Tier classification

## Tier 정의

- **★★★ ESSENTIAL**: Loss에서 제거 시 BEST 좌표 붕괴 + literature value와 신경 데이터 양 피험자 일치
- **★★ ESSENTIAL (revised)**: Loss 제거 시 BEST 붕괴 확인 (literature 일치는 부분)
- **★ UNDER VERIFICATION**: Literature value와 신경 데이터 부분 불일치, 추가 검증 필요

## Tier table

| Anchor | Tier | Rationale |
|---|---|---|
| **Emery 2021** β_s ≈ 21.4° | ★★★ ESSENTIAL | V1 ΔRDM β_s sub-08=20°/sub-09=23° 양 피험자 독립 복원 |
| **Machado 2009** Δλ severity | ★★★ ESSENTIAL | Phase 2 cone-shift v2 sub-08 mild (p=0.036) / sub-09 severe (p=0.009) |
| **Tregillus 2021** 20-40% overshoot | ★★ ESSENTIAL | Loss 제거 시 β_c→0 collapse (sub-08 P2a −0.088, sub-09 P2a −0.100). literature 일치는 sub-09 부분, sub-08 outlier |
| **Brettel 1997** β_c sign | ★ UNDER VERIFICATION | sub-08 β_c=−18° (CI excl 0) — OLD/Stockman/CIELab 모든 규약에서 Brettel expected sign과 DISAGREE; sub-09 CI incl 0 (assessable 안 됨) |

## Empirical recovery values

| Anchor (literature) | sub-08 deutan (neural) | sub-09 protan (neural) | Source |
|---|---|---|---|
| Emery β_s 21.4° | **20°** ±8 [12, 39] | **23°** ±10 [2, 36] | V1 ΔRDM bootstrap 2-comp |
| Machado severity Δλ | **8.6 nm** mild, p=0.036 | **25.2 nm** severe, p=0.009 | Phase 2 cone-shift v2 (V4) |
| Tregillus 20-40% | g=−2.25 → 125% (outlier) | g=−1.10 → **10%** (partial) | R+C model |
| Brettel β_c sign | **−18°** CI[−32, −11] (DISAGREE) | **+3°** CI[−2, +6] (NS) | V1 ΔRDM bootstrap 2-comp |

## Loss simplification finding (2026-05-13)

초기 가설("Tregillus = Emery의 중복")은 simplification sweep으로 **기각**:

| Loss variant | sub-08 (β_s, β_c) | sub-09 (β_s, β_c) | P2a (sub-08, sub-09) |
|---|---|---|---|
| FULL (Emery+Tregillus+Brettel+Tikh) | (22, +12) | (22, −10) | 0.550, 0.887 |
| SIMPLE (Emery+Brettel+Tikh, Tregillus 제거) | (20, **0**) | (20, **+2**) | 0.463, 0.787 |
| Emery only + CCC + Tikh | (20, −4) | (20, +4) | 0.425, 0.787 |

→ **Tregillus는 β_c amplitude를 유지하는 essential 항.** Emery는 β_s anchor, Tregillus는 norm anchor, 두 anchor 모두 필요.

## Brettel sign reconciliation (2026-05-13)

| Axis convention | sub-08 deutan expected | sub-08 observed β_c | sub-09 protan expected | sub-09 observed β_c |
|---|---|---|---|---|
| OLD 150° both | + (β_c>0) | −18° ✗ | − (β_c<0) | +3° (CI incl 0) |
| Stockman 163° / 16° | + (sign STAY) | −17.5° ✗ | + (sign FLIP) | −2.1° (CI incl 0) |
| CIELab 175.7° / 11.8° | + (sign STAY) | −16.2° ✗ | + (sign FLIP) | −2.2° (CI incl 0) |

→ **sub-08 deutan은 모든 axis 규약에서 Brettel 예측과 DISAGREE.** Brettel sign penalty를 loss에 포함시키는 것은 신경 데이터로 정당화되지 않음.

## Loss equations

Forward model:

```
δθ(θ) = β_s · cos(θ − 90°) + β_c · cos(θ − θ_conf)
θ_perceived = (θ + δθ(θ)) mod 360
```

Composite loss (current Bayesian BEST):

```
L_total = α · L_ccc(V4)  +  (1 − α) · L_lit  +  ε · Tikh

  α = 0.3,  ε = 0.1 (scaled ×50 for parity with L_lit terms)

L_ccc(V4)     = 1 − CCC(vuln_sim, vuln_cvd)         [neural likelihood]
                CCC = 2·ρ·σ_x·σ_y / (σ_x² + σ_y² + (μ_x − μ_y)²)

L_lit         = w_E·L_Emery  +  w_T·L_Tregillus  +  w_B·L_Brettel
  w_E = 0.5,  w_T = 0.5,  w_B = 0.3

L_Emery       = ((β_s − 21.4) / 10)²                [β_s anchor]
L_Tregillus   = ((√(β_s² + β_c²) − 21.4·1.3) / 15)²  [norm anchor; 1.3 = 30% overshoot]
L_Brettel     = max(0, −β_c · s_fam / 50)²           [sign-only penalty]
                s_fam = +1 (deutan), −1 (protan)  under OLD axis 150°

Tikh          = (β_s² + β_c²) / 32400                [L2 regularizer]
```

## Implication for filter design

Bayesian framework uses literature anchors as prior. Neural recovery analysis:

- **★★★ Emery + ★★★ Machado**: literature priors가 신경 데이터로 독립 검증됨 → 필터 파라미터의 anchor 선택을 정당화.

- **★★ Tregillus**: literature value 자체는 신경 부분 일치이나, loss에서 제거 시 β_c→0 collapse → empirically essential (정량적으로 확인됨).

- **★ Brettel**: sub-08에서 모든 axis 규약 하 DISAGREE → 추가 검증 또는 alternative formulation 필요. 현재는 weak weight (0.3) + Tikh로 stabilize. Loss에서 제거 가능성 검토 권고.
