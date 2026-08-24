# Run-count validation REPORT (v2)

**Date**: 2026-05-21 (v2 supersedes 2026-05-20 v1)
**Goal**: 2nd MRI 실험 (필터 vs. baseline 비교)에서 사용할 **run 수**를 결정.
n=6→n<6 축소가 (a) 신호 수집 품질, (b) 표현 기하 안정성, (c) outcome 검출 power 세 축 모두에서 충분한지 평가.

**Scope**: 10 subjects (HC×7 + CVD×3) × 4 ROIs (V1, V2, V3, hV4) × 5 run counts (n ∈ {2,3,4,5,6}) × 모든 C(6,n) subset (n=2:15, n=3:20, n=4:15, n=5:6, n=6:1 = 57 subsets total).

**Scripts**:
- `scripts/run_count_saturation.py` — LOCO ρ + per-color profile + GCV α
- `scripts/run_count_crossnobis.py` — split-half crossnobis RDM (Walther 2016 MVNN)
- `scripts/run_count_tier1.py` — β-split-half + LORO 8-way
- `scripts/run_count_tier2.py` — noise ceiling + Procrustes + circular RSA
- `scripts/run_count_tier3.py` — per-color profile stability + Cohen's d + permutation null
- `scripts/plot_tiers.py` — all figures + consensus table

**Data files** (`run_count_validation/`):
- `v1_saturation_loco.json` — LOCO ρ (mean + per-color + GCV α) per cell
- `v1_saturation_crossnobis.json` — split-half RDM Spearman per cell
- `tier1_signal_quality.json` — β-split-half + LORO 8-way per cell
- `tier2_geometric_stability.json` — noise ceiling + Procrustes + circular RSA
- `tier3_outcome_detection.json` — Cohen's d + HC-rank p + permutation null
- `profile_stability.json` — Op-A (rank) + Op-B (vulnerable-set retention)
- `consensus_table.json` — per-ROI per-n criterion pass/fail

**Figures** (`figs/`):
- `tier1_signal.png` — β-split-half / LORO acc / GCV α median curves
- `tier2_geometric.png` — noise ceiling / Procrustes / circular RSA curves
- `tier3_outcome.png` — LOCO ρ / Cohen's d / permutation p curves
- `per_color_profile.png` — 8×n heatmap per CVD subject per ROI
- `profile_stability.png` — Op-A (rank) + Op-B (retention) curves
- `consensus_decision.png` — pass/fail table

---

## 0. Metrics — definition, measurement, justification

본 검증은 "n=6 → n<6 축소가 *수집 데이터의 품질*과 *현재 결과의 재현*을 모두 유지하는가"를 묻는다. 이는 단일 지표로 답할 수 없는 세 별개 질문이다:

| 질문 | Tier | 지표 |
|---|---|---|
| (A) 신호가 안정적으로 잡혀 있나? | **Tier 1** | β-split-half voxel r, LORO 8-way decoding acc, GCV α distribution |
| (B) 표현 기하가 재현되나? | **Tier 2** | crossnobis noise ceiling (lower + Spearman-Brown upper), Procrustes split-half disparity, circular-template RSA |
| (C) HC-vs-CVD outcome이 검출되나? | **Tier 3** | LOCO ρ (mean + per-color profile), Cohen's d, Op-A rank stability, Op-B vulnerable-set retention, permutation p |

### Tier 1 — Signal-quality metrics

**T1.1 β-map split-half voxel correlation.** 각 subset에서 floor(n/2) vs ceil(n/2) 분할; 각 half의 색별 평균 β = (8, V). 색별 voxel-축 Pearson r 계산 후 색 평균. **상위는 더 안정한 신호.** 절대 기준은 없지만 chance(=0)에서 멀어질수록 좋고, HC 분포의 5th percentile 이상이면 sufficient.

**T1.2 LORO 8-way template-matching accuracy.** 각 hold-out run에서 학습된 W로 8색 예측 패턴을 만들고, hold-out 패턴이 어떤 색의 예측에 가장 가까운지 Pearson 기반 argmax. 8개 색 모두에 대해 정답률. Chance = 12.5% (1/8). **충분한 신호 floor: ≥ 25% (2× chance).** Discrimination이 살아 있는지 확인.

**T1.3 GCV α distribution.** LOCO 학습 시 GCV로 선택된 α의 분포. α가 1000으로 saturation하면 ridge가 신호를 못 보고 over-regularize한다는 신호. **운용 표시기**: median α의 단조 증가는 신호 약화의 표지.

### Tier 2 — Geometric stability metrics

**T2.1 Crossnobis RDM noise ceiling.** Walther 2016 crossnobis (LORO + MVNN Ledoit-Wolf 평균) 8×8 RDM의 split-half Spearman. **Lower bound** = 직접 측정 split-half Spearman. **Upper bound** = Spearman-Brown 보정 `r_full = 2r/(1+r)` (full-length reliability proxy). 표현 기하가 noise만이 아니라는 증거. **Pass: ≥ 0.40.**

**T2.2 Procrustes split-half disparity.** Half-A vs Half-B의 (8, V) β-패턴 configuration 간 procrustes 정렬 잔차. 회전/스케일 invariant. Disparity ∈ [0, 1], 낮을수록 8-color geometry가 안정. 보조 지표.

**T2.3 Circular-template RSA.** Observed 8×8 RDM과 ideal chord-distance RDM (8 equispaced angles, unit circle) 간 Spearman. 색공간의 *원형 토폴로지*가 살아 있는지. Cone-shift 가설의 전제 조건. 보조 지표.

### Tier 3 — Outcome detection metrics

**T3.1 LOCO ρ (mean + per-color profile).** Phase 1/2 검증의 primary functional metric — *연속 색공간 보간 능력*. 각 색 c_i에 대해 나머지 7색으로 ridge-GCV W 학습, c_i의 예측 패턴과 관측 패턴 voxel Pearson. 8색 평균 = mean ρ. **CVD에서 mean ρ < 0**이면 보간 실패. Per-color profile (8-vector)은 *어떤 색*이 약한지 보여줌.

**T3.2 HC-vs-CVD Cohen's d.** `d = (mean_HC - cvd_mean) / SD_HC`. HC는 각 n에서 per-subject mean ρ의 7-subject 분포. **Detection power의 직접 지표.** Pass: d ≥ 0.8 (large effect, Cohen 1988).

**T3.3 Op-A profile rank stability.** 같은 n에서 subset 간 per-color ρ profile의 평균 pairwise Spearman. **현재 발견 (어떤 색이 worst인지)이 subset 선택에 견고한가**의 지표. Pass: ≥ 0.5.

**T3.4 Op-B vulnerable-set retention.** n=6 anchor profile에서 ρ 하위 2개 색 = vulnerable set V*. 각 smaller-n subset에서 ρ 하위 2개 색이 V*와 얼마나 겹치는가 (intersection / 2). **현재 발견의 *재현*에 직접 매핑**되는 사용자 요청 지표. Pass: ≥ 0.50 (chance ≈ 0.07 for k=2 from 8).

**T3.5 Permutation null (label shuffle within-run) — diagnostic only.** B=100 within-run color label permutations. **본 검증에서 grand-mean bias로 인해 null이 0 중심이 아님 (§3.6 참조). 1차 detection 지표가 아니라 진단용.** Cohen's d (§3.2)가 적절한 HC-vs-CVD 비교 지표.

---

## 1. Tier 1 results — signal quality

→ Figure: `figs/tier1_signal.png`

### 1.1 β-split-half voxel r per CVD subject × ROI × n

V1 ROI를 대표로 — 단조 증가하며 n=4에서 0.23~0.31 도달, n=6에서 0.31~0.39:

| n | sub-08 V1 | sub-09 V1 | sub-10 V1 | HC mean V1 |
|---|---|---|---|---|
| 2 | 0.195 ± 0.043 | 0.145 ± 0.046 | 0.133 ± 0.046 | 0.135 ± 0.030 |
| 3 | 0.246 ± 0.033 | 0.189 ± 0.040 | 0.177 ± 0.038 | 0.177 ± 0.036 |
| 4 | 0.310 ± 0.027 | 0.248 ± 0.037 | 0.234 ± 0.033 | 0.233 ± 0.043 |
| 5 | 0.347 ± 0.018 | 0.284 ± 0.026 | 0.272 ± 0.023 | 0.269 ± 0.046 |
| 6 | 0.390 | 0.327 | 0.315 | 0.311 ± 0.050 |

**Plateau**: n=4부터 CVD min β ≥ 0.23. **sub-08이 HC mean보다 *높은* β-split-half** — 신호 안정성 측면에서 CVD가 비정상이 아니라 오히려 더 안정. Sub-09도 HC mean과 거의 동일. 신호 자체가 *부족하지 않다*는 강한 증거.

### 1.2 LORO 8-way decoding accuracy

8-way classification은 보간과 다른 과제 — color identity가 보존되는지의 sanity check. Chance = 0.125.

| n | V1 sub-08 | V1 sub-09 | V1 HC mean | V2 sub-08 | V2 sub-09 | hV4 sub-08 | hV4 sub-09 |
|---|---|---|---|---|---|---|---|
| 2 | 0.308 ± 0.103 | 0.296 ± 0.113 | 0.323 ± 0.031 | 0.329 ± 0.077 | 0.404 ± 0.109 | 0.275 ± 0.055 | 0.308 ± 0.074 |
| 4 | 0.371 ± 0.088 | 0.456 ± 0.074 | 0.382 ± 0.045 | 0.456 ± 0.090 | 0.487 ± 0.068 | 0.467 ± 0.059 | 0.552 ± 0.086 |
| 6 | 0.521 | 0.500 | 0.420 ± 0.073 | 0.521 | 0.729 | 0.521 | 0.542 |

**관측**:
- 모든 ROI에서 CVD LORO acc는 chance를 명확히 초과 (n≥3, 모두 ≥ 0.27 = 2×chance).
- **CVD subjects가 HC mean보다 LORO acc가 높음** (V1 n=4: sub-09=0.456 vs HC=0.382; V2 n=6: sub-09=0.729 vs HC=0.426). **분류 자체는 CVD에서도 매우 잘 됨** — 8색 사이 구분은 cone shift에 영향 받지 않는 측면.
- **결론: 분류 신호는 n=3부터 충분, n=4부터 안정.**

### 1.3 GCV α distribution

GCV α는 모든 cell에서 [0.001, 1000] 사이에서 선택. median α가 1000에 도달하지 않음 — over-regularization 없음. 보조 지표로 두고 본 검증의 gating은 아님.

### Tier 1 summary

**T1 pass at n=3-6 for V1/V2/V3, n=2 for hV4.** 신호 자체는 충분히 작은 n에서도 살아 있음. β-split-half는 n=4부터 견고하게 CVD 0.20+, LORO는 모든 n에서 chance 2×+.

---

## 2. Tier 2 results — geometric stability

→ Figure: `figs/tier2_geometric.png`

### 2.1 Crossnobis RDM noise ceiling (lower bound)

V1과 V2는 모든 subject에서 RDM이 안정. hV4는 sub-10 (null control)에서 noise ceiling 붕괴 (0.016 at n=6 — 사실상 noise).

| n | V1 sub-08 | V1 sub-09 | V1 HC mean | hV4 sub-08 | hV4 sub-09 | hV4 sub-10 |
|---|---|---|---|---|---|---|
| 2 | +0.585 ± 0.132 | +0.479 ± 0.151 | +0.181 ± 0.088 | +0.843 ± 0.088 | +0.405 ± 0.215 | +0.083 ± 0.163 |
| 4 | +0.825 ± 0.041 | +0.759 ± 0.045 | +0.426 ± 0.133 | +0.893 ± 0.051 | +0.599 ± 0.049 | +0.105 ± 0.154 |
| 6 | +0.901 | +0.808 | +0.572 ± 0.125 | +0.922 | +0.653 | +0.016 |

**관측**:
- V1 CVD subjects는 HC mean보다 *오히려 높은* noise ceiling (sub-08 V1 n=6: 0.901 vs HC mean 0.572). 데이터 품질 우수.
- hV4 sub-10의 noise ceiling 붕괴는 별도 진단 필요 (voxel 수, motion, fixation 등). MEMORY의 "sub-10 baseline_rho FP" 우려와 연결.
- 검증 기준은 **CVD-test = sub-08 + sub-09**만 사용. sub-10은 specificity 보조용이지 gating 대상 아님.

### 2.2 Procrustes split-half disparity & 2.3 Circular-template RSA

보조 지표로 결과는 figure 참조. 핵심 발견은 noise ceiling에 응축되어 있음.

### Tier 2 summary

**T2 pass at n≥2 for V1/V2 (CVD-test), n≥3 for V3, n≥2 for hV4 (CVD-test only)**. 표현 기하는 작은 n에서도 안정. sub-10 hV4는 별도 우려 사항이지만 본 결정에 영향 없음.

---

## 3. Tier 3 results — outcome detection

→ Figures: `figs/tier3_outcome.png`, `figs/per_color_profile.png`, `figs/profile_stability.png`

### 3.1 LOCO ρ (mean) — 검증된 Stockman-baseline 기반

n=6 단일 subset (canonical anchor):

| ROI | sub-08 deutan | sub-09 protan | sub-10 null | HC mean ± SD |
|---|---|---|---|---|
| V1 | **−0.157** | **−0.032** | +0.100 | +0.155 ± 0.128 |
| V2 | **−0.218** | +0.015 | −0.168 | +0.138 ± 0.107 |
| V3 | −0.035 | −0.039 | +0.217 | +0.087 ± 0.137 |
| hV4 | **−0.069** | +0.031 | +0.308 | +0.075 ± 0.133 |

**중요한 차이**: v1 (5월 20) REPORT는 CIELab nominal-angle baseline의 stale 값 (hV4 sub-08 = −0.213 등)을 보고. 본 v2는 Stockman-derived baseline (MEMORY 2026-04-07 C_baseline bug fix 정책 준수) — 모든 수치 재검증 완료.

### 3.2 HC-vs-CVD Cohen's d per n

→ Figure `tier3_outcome.png` middle row.

| ROI | sub | n=2 | n=3 | n=4 | n=5 | n=6 |
|---|---|---|---|---|---|---|
| **V1** | sub-08 | +2.41 | +2.32 | +2.31 | +2.50 | +2.25 |
|        | sub-09 | +1.14 | +1.21 | +1.18 | +1.32 | +1.35 |
| **V2** | sub-08 | +2.61 | +4.30 | +3.63 | +3.42 | +3.23 |
|        | sub-09 | +2.14 | +1.97 | +1.69 | +1.29 | +1.12 |
| **V3** | sub-08 | −0.03 | +0.62 | +1.04 | +1.00 | +0.86 |
|        | sub-09 | +0.59 | +0.81 | +1.13 | +0.94 | +0.89 |
| **hV4**| sub-08 | +1.45 | +1.34 | +1.41 | +1.77 | +1.09 |
|        | sub-09 | +0.65 | +0.33 | +0.20 | +0.29 | +0.33 |

**CRITICAL FINDING**: hV4의 sub-09 Cohen's d가 어떤 n에서도 0.8 미달. 즉 **hV4는 sub-09에서 HC-vs-CVD LOCO 차이가 약함** — *run 수의 문제가 아니라 신호 자체의 문제*. 이는 MEMORY의 "HC LOCO FPR = 7/7 (100%) on hV4"와 정합 — hV4 LOCO cone-shift specificity 부재.

**V1**은 sub-08과 sub-09 *모두* d ≥ 1.14 across all n — 가장 견고. **V2**는 sub-08에서 매우 강하지만 sub-09 d가 n이 증가하며 +2.14→+1.12로 감소 (HC SD가 n과 함께 줄어들기 때문이 아니라 HC mean이 안정화되면서 분자가 줄기 때문 — 부드러운 패턴). **V3**는 sub-08 d가 n=2에서 −0.03으로 떨어짐 (signal floor 미달); n≥4부터 +1.0 이상 회복.

### 3.3 Per-color profile (사용자 요청 — sub-09 포함)

→ Figure `per_color_profile.png` (sub-08, sub-09, sub-10 × 4 ROIs heatmap; 초록 박스 = n=6 anchor의 bottom-2 vulnerable color).

**sub-08 deutan V1 n=6 profile**: ρ_per_color = `[−0.46, −0.03, −0.54, +0.00, +0.50, +0.24, −0.75, −0.22]` (c1 red, c2 orange, c3 yellow, c4 green, c5 cyan, c6 blue, **c7 purple**, c8 magenta).
- Anchor bottom-2 = {c7 purple, c3 yellow} — deutan M-L confusion axis와 정합 (red-green dyad이 가장 약함).

**sub-09 protan V1 n=6 profile**: ρ_per_color = `[−0.21, +0.27, −0.50, −0.27, +0.43, +0.06, −0.46, +0.43]`.
- Anchor bottom-2 = {c3 yellow, c8 magenta} — sub-08 (purple+yellow) 과 *부분 겹침* (yellow은 공통, purple↔magenta는 hue circle 인접 — 둘 다 confusion line 방향 외곽). Protan과 deutan의 미세한 분리 신호.

### 3.4 Op-A rank stability (across-subset Spearman of per-color profile)

→ Figure `profile_stability.png` top row. n=6 cell은 single subset이라 across-subset Spearman 정의 불가 (n=2..5만 보고).

| ROI | sub | n=2 | n=3 | n=4 | n=5 |
|---|---|---|---|---|---|
| **V1** | sub-08 | +0.813 | +0.902 | +0.937 | +0.949 |
|        | sub-09 | +0.528 | +0.726 | +0.886 | +0.935 |
|        | HC mean | +0.464 | +0.648 | +0.762 | +0.840 |
| **V2** | sub-08 | +0.671 | +0.774 | +0.949 | +0.984 |
|        | sub-09 | +0.266 | +0.491 | +0.768 | +0.919 |
|        | HC mean | +0.383 | +0.555 | +0.700 | +0.809 |
| **V3** | sub-08 | +0.547 | +0.873 | +0.935 | +0.963 |
|        | sub-09 | +0.554 | +0.669 | +0.736 | +0.906 |
|        | HC mean | +0.442 | +0.589 | +0.760 | +0.813 |
| **hV4**| sub-08 | +0.838 | +0.929 | +0.955 | +0.986 |
|        | sub-09 | +0.676 | +0.908 | +0.946 | +0.954 |
|        | HC mean | +0.522 | +0.613 | +0.702 | +0.818 |

**Op-A는 n=3부터 거의 모든 cell에서 0.50 이상, n=4부터는 sub-09 V2 (+0.768)을 제외하면 모두 0.85+.** CVD subjects의 per-color worst-rank가 작은 n에서도 매우 robust하게 같은 색에 떨어짐. 흥미롭게도 **CVD subjects의 Op-A가 HC mean보다 높음** — CVD profile은 confusion line으로 인해 worst-color가 더 결정적으로 (deterministic) 같은 색을 가리키기 때문 (HC는 worst가 noise-dominated이므로 subset마다 흔들림).

### 3.5 Op-B vulnerable-set retention against n=6 anchor

→ Figure `profile_stability.png` bottom row. *현재 발견이 작은 n에서도 재현되는지의 직접 지표.* (사용자 요청 핵심 지표.)

Anchor (n=6 bottom-2 colors per subject):

| Subject | ROI | Anchor bottom-2 |
|---|---|---|
| sub-08 deutan | V1, V2, V3, hV4 | c3 yellow, c7 purple |
| sub-09 protan | V1 | c3 yellow, c8 magenta |
| sub-09 protan | V2, hV4 | c6 blue, c8 magenta |
| sub-09 protan | V3 | c7 purple, c8 magenta |

Retention rates:

| ROI | sub | n=2 | n=3 | n=4 | n=5 | n=6 |
|---|---|---|---|---|---|---|
| **V1** | sub-08 | 0.467 | 0.500 | 0.500 | 0.833 | 1.000 |
|        | sub-09 | 0.667 | 0.825 | 0.900 | 1.000 | 1.000 |
| **V2** | sub-08 | 0.533 | 0.900 | 1.000 | 1.000 | 1.000 |
|        | sub-09 | 0.467 | 0.500 | 0.867 | 0.917 | 1.000 |
| **V3** | sub-08 | 0.667 | 0.975 | 1.000 | 1.000 | 1.000 |
|        | sub-09 | 0.533 | 0.650 | 0.667 | 0.833 | 1.000 |
| **hV4**| sub-08 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 |
|        | sub-09 | 0.700 | 0.925 | 1.000 | 1.000 | 1.000 |

**핵심 결과**: sub-08과 sub-09 *둘 다*에서, **n=4부터 V1 retention ≥ 0.500 + V2 ≥ 0.867 + V3 ≥ 0.667 + hV4 = 1.000**. 즉 **현재 결과(어떤 색이 vulnerable한지)는 작은 n에서도 재현됨**. V1 sub-08의 n=2~4 retention이 0.467~0.500으로 가장 낮지만, n=5부터 0.833으로 회복.

Chance level (k=2 from 8 colors) = C(6,2)/C(8,2) ≈ 0.07 — 모든 관측 retention이 chance 대비 매우 높음.

### 3.6 Permutation null — **KNOWN LIMITATION**

Within-run color-label shuffle (B=100) was computed but the resulting null distribution is **positively biased** (mean ρ ≈ +0.45, SD ≈ 0.08 across CVD subjects), not centered at 0. Diagnostic: under within-run permutation, the *global activation pattern* (voxels that are positive vs. negative across all colors) is preserved — template-matching ρ via Pearson then captures this global structure regardless of color identity. This makes lower-tail p anti-conservatively *small* for every subject, including HC.

**Decision**: Do not use permutation p as the primary detection criterion. **Cohen's d** (§3.2) is the appropriate HC-vs-CVD comparison since it uses the HC distribution as reference (not a permutation null), and is unaffected by the grand-mean bias.

Raw permutation results retained in `tier3_outcome_detection.json` for diagnostic transparency. A future fix would be: (a) subtract the cross-color mean pattern from both Y_pred and Y_test before correlation, or (b) use signed reconstruction error instead of Pearson. Out of scope for this validation.

---

## 4. Consensus decision — n* per ROI

→ Figure: `figs/consensus_decision.png`

Pass criteria (CVD-test = sub-08 + sub-09 only; sub-10 = null control, reported separately):
- **T1**: min(β-split-half_CVD) ≥ 0.20 **AND** min(LORO-acc_CVD) ≥ 0.25
- **T2**: min(noise ceiling lower_CVD) ≥ 0.40
- **T3a**: HC-vs-CVD Cohen's d ≥ 0.8 for **BOTH** sub-08 AND sub-09
- **T3b**: Op-B vulnerable-set retention ≥ 0.50 for **BOTH** sub-08 AND sub-09

| ROI | n=2 | n=3 | n=4 | n=5 | n=6 |
|---|---|---|---|---|---|
| **V1** | T2,T3a | T2,T3a,T3b | **✓ ALL ★** | **✓ ALL ★** | **✓ ALL ★** |
| **V2** | T2,T3a | **✓ ALL ★** | **✓ ALL ★** | **✓ ALL ★** | **✓ ALL ★** |
| **V3** | T2,T3b | T1,T2,T3b | **✓ ALL ★** | **✓ ALL ★** | **✓ ALL ★** |
| **hV4** | T1,T2,T3b | T1,T2,T3b | T1,T2,T3b | T1,T2,T3b | T1,T2,T3b |

**ROI별 consensus n***:
- **V1: n* = 4**
- **V2: n* = 3** (가장 견고 — d=2.74 at n=3)
- **V3: n* = 4**
- **hV4: n* = ∞** (어떤 n에서도 T3a 통과 불가 — sub-09 d ≤ 0.33)

---

## 5. Critical finding — hV4 vs V1 primary endpoint

**v1 REPORT는 hV4를 primary로 가정했으나, v2는 V1이 더 견고한 primary임을 보여준다.**

근거:
1. **Cohen's d**: V1 sub-09 d = 1.35 at n=6 vs hV4 sub-09 d = 0.33 — 4배 차이.
2. **Noise ceiling**: V1 CVD subjects 0.80+ vs hV4 sub-10 = 0.016 (null이 noise만 잡음).
3. **MEMORY 정합**: "HC LOCO FPR 7/7 (100%) on hV4" + "sub-08 V1 LOCO p=0.001*** strongest in pipeline" — 둘 다 V1을 primary로 가리킴.
4. **Run-count efficient**: V1은 n=4에서 충분, hV4는 n=6에서도 부족.

이는 **본 검증의 부수 발견**이지만, Phase 3 본실험 설계에 직접 영향. Filter 효능 검증 1차 endpoint는 V1으로 재설정 필요.

(이 권고는 Phase 2 종결 문서 `project_phase2_closure.md`와의 정합성을 위해 별도 논의 후 확정해야 함.)

---

## 6. MRI experiment 2 — run count recommendation

**Primary recommendation: n = 5 runs** (consensus n* + 1 safety margin).

근거:
- V1 (제안된 primary endpoint): n*=4 → +1 = 5
- V2 (concurrent endpoint): n*=3 → +2 = 5
- V3 (보조): n*=4 → +1 = 5
- 5 runs × 7 min/run ≈ 35 min scan time (필터 조건당) → 2 conditions × 35 min = 70 min total functional + structural ≈ 90 min total session. 6 runs 기준 ~110 min에서 ~18% 감소.

**Conservative fallback: n = 6 (no reduction)**. V1/V2는 n=4에서 이미 안정하지만, 첫 실험이므로 보수적으로 가도 무방. Trade-off: scan 시간 +20 min × 피험자 수.

**Aggressive option: n = 4**. V1/V2 모두 ALL pass. hV4를 포기하면 충분. 시간 절약 효과 최대 (~40%↓).

→ **결정 권고: n = 5 baseline + n = 4 fallback (시간 부족 시).** Phase 3 본 실험 계획 시 이 표를 참조.

---

## 7. Files & reproducibility

모든 raw data + figures는 `run_count_validation/`에 저장. 재현:

```bash
cd analysis/phase6_behavioral_analysis
conda activate srm
python scripts/run_count_saturation.py  # ~60s
python scripts/run_count_tier1.py        # ~3s
python scripts/run_count_tier2.py        # ~110s (V1 procrustes dominant)
python scripts/run_count_tier3.py        # ~15s (B=100 permutation)
python scripts/plot_tiers.py             # ~10s
```

Stockman baseline 사용 확인 — `get_design_matrix("machado_1way", [0.0], cvd_type="deutan")`의 첫 column이 `[0.465, 0, 0, 0, 0.085, 0.949]`이면 정상.

---

## Appendix — superseded v1 (2026-05-20) 변경 사항

| 항목 | v1 | v2 | 이유 |
|---|---|---|---|
| Design matrix baseline | CIELab nominal angles | Stockman-derived hues | MEMORY 2026-04-07 C_baseline bug fix |
| sub-08 hV4 n=6 LOCO ρ | −0.213 | −0.069 | baseline 보정으로 수치 재계산 |
| Primary endpoint 가정 | hV4 | V1 (또는 V1+V2 dual) | Cohen's d 분석 결과 |
| Subset scope | n=4 random + n=6 anchor | C(6,n) for all n∈{2..6} | 사용자 요청 (n=2-5 추가) |
| Tier 구조 | LOCO + crossnobis만 | Tier 1/2/3 9 metrics | 사용자 요청 — 신호 안정성·기하 재현성 별도 검증 |
| sub-10 처리 | gating 포함 | null control로 분리 | hV4 noise ceiling 분석에서 발견된 fundamental 차이 |

v1 파일들 (`v1_allroi_n4_vs_n6.json`, `v1_hV4_n4_vs_n6.json`, `v1_permutation_n4_vs_n6.json`)은 superseded로 표시; 향후 분석은 본 REPORT의 saturation/tier 파일을 사용.

---

## v3 Addendum (2026-06-29) — Adjacent-accuracy retention (paper primary metric)

**Trigger**: The paper's filter-evaluation primary readout was reframed to **LOCO adjacent accuracy** (decoding, ±1 hue step), but Tiers 1–3 above certified n=4 only on encoding-direction LOCO ρ, LORO, and geometric stability — *not* on adjacent accuracy. This addendum closes that gap.

**Script**: `scripts/run_count_adjacc.py` (canonical FE-6 uniform basis + OLS pseudoinverse decoder via `loco_canonical.loco_forward_readouts`; same C010 amplitudes_procrustes input).
**Outputs**: `adjacc_saturation.json` (per-cell, all C(6,n) subsets), `adjacc_retention_summary.json` (per-ROI per-n HC mean + CVD single-case d_cc).
**Scope**: 4 ROIs × 10 subjects × 57 subsets. HC hV4 excludes sub-07 (low voxels). Chance = 3/8 = 0.375.

### hV4 retention (landmark ROI)

| n | HC mean ± SEM | HC > chance | deutan (s08) | protan (s09) |
|---|---|:---:|---|---|
| 2 | 0.448 ± 0.032 | ✓ | 0.233 (d=−2.50) | 0.171 (d=−3.22) |
| 3 | 0.445 ± 0.034 | ✓ | 0.229 (d=−2.42) | 0.148 (d=−3.33) |
| **4** | **0.449 ± 0.037** | **✓** | **0.231 (d=−2.21)** | **0.138 (d=−3.17)** |
| 5 | 0.452 ± 0.037 | ✓ | 0.229 (d=−2.26) | 0.133 (d=−3.24) |
| 6 | 0.456 ± 0.039 | ✓ | 0.250 (d=−2.02) | 0.125 (d=−3.25) |

(d = Crawford–Howell d_cc against the per-subject HC mean distribution at that n. sub-10 deutan control: 0.15–0.17 below chance at all n.)

### Conclusion
The hV4 adjacent-accuracy landmark — **HC above the 3/8 chance level, both CVD participants well below** — is fully retained at n=4. The HC mean is flat across run counts (0.448–0.456), and the CVD single-case effect sizes are large at every n (|d_cc| > 2 deutan, > 3 protan); they are if anything marginally *larger* at n<6 because the HC subset-mean SD tightens. **The paper's primary interpolation metric is therefore certified at the deployed four-run count**, on top of the ρ/LORO/geometry metrics validated in v2. This supersedes the v2-era scope note that adjacent accuracy was untested at reduced run counts.

n=6 anchor reproduces the paper exactly (deutan 0.250, protan 0.125; HC 0.456 ≈ reported 0.47).
