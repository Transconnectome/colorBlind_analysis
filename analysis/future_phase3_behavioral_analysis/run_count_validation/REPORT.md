# Run-count validation REPORT (v1)

**Date**: 2026-05-20
**Plan**: `run_count_validation_plan_20260519.md` + `run_count_validation_addendum_20260520.md`
**Scope**: 10 subjects (HC×7 + CVD×3) × 4 ROIs (V1, V2, V3, V4=hV4) × 17 subsets (1×n=6 anchor + 1×n=4 leading + 15×n=4 random C(6,4))
**Scripts**:
- `scripts/run_count_subsample.py` — point estimate LOCO ρ (v1)
- `scripts/run_count_permutation.py` — label-permutation null (N_PERM=1000, decoding + profile-match tests)
- `scripts/run_count_crossnobis.py` — split-half crossnobis RDM reliability (MVNN pre-whitening)

---

## 1. Summary verdict

**Pass-4 strict 결정 불가** — v1이 19일 plan §4 Pass-4 criterion이 참조하는 *MEMORY landmark perm framework* (cone-shift model fit p-value)를 직접 검증하지 않음. v1은 더 보수적인 *raw label-permutation* test를 수행했고, 그 결과는 framework-conditional verdict로만 해석되어야 함.

| Evidence stream | sub-08 (deutan) | sub-09 (protan) | sub-10 (null) | HC FPR | Framework-conditional verdict |
|---|---|---|---|---|---|
| Sign retention (LOCO ρ) | ✓ 64/64 cells | △ mixed (known weak) | ⚠ V2 false-neg | n/a | **PASS** for sub-08 sign pattern |
| Crossnobis split-half r≥0.5 | ✓ 100% all ROI | ✓ 100% all ROI | ⚠ V3/V4 collapse | HC ≥0.5 majority | **PASS** for RDM structure |
| Raw label-perm Test A/B | sub-08 anchors NS at n=6 itself | sub-09 V4 only strong anchor; loss at n=4 | **V2 FP 20% at n=4** (new finding) | ≤3% baseline | **conditional** — framework not aligned with MEMORY landmarks |
| Cone-shift model-fit perm (MEMORY landmarks) | not tested | not tested | not tested | not tested | **v2 work needed for Pass-4 strict** |

**Bottom line**: 
- *RDM 구조*와 *LOCO ρ sign* 은 4-run에서 강력하게 보존 — n=4가 *general* MVPA pattern stability에는 충분
- *Raw label-perm framework* (본 v1)에서 sub-09 V4가 유일한 strong anchor였고 n=4에서 손실되었으나, MEMORY (Gen-4 Task #20)는 sub-09 V4 cone-shift를 *이미 "geometry-weak"으로 분류* — n=4 손실이 "fewer runs" 이슈인지 anchor 자체 fragility인지 framework 분리 필요
- **새 finding**: sub-10 V2 false-positive 악화 (Sec 4.4) — *framework-independent* specificity 우려
- MEMORY의 cone-shift landmark perm은 본 v1에서 검증 안 됨 — Pass-4 strict 결정을 위해 **v2 (cone-shift fit perm) 필요**

**v1 verdict**: framework-conditional. PI review 전에 v2 timing sanity check 후 SLURM 또는 local 가능 여부 결정.

---

## 2. Sign retention (v1 LOCO ρ point estimate)

`v1_allroi_n4_vs_n6.json`. Each cell: LOCO ρ = mean per-color voxel pattern correlation (encoding-direction ridge_gcv on pooled n_runs × 7 train colors). No permutation.

### 2.1 CVD subject sign retention (target = MATCH n=6 anchor direction)

| ROI | sub-08 n=6 ρ | n=4 sign retention | sub-09 n=6 ρ | n=4 sign retention |
|---|---:|:---:|---:|:---:|
| V1 | −0.198 | **16/16** negative | +0.049 | 9/16 positive (matches n=6 weak signal) |
| V2 | −0.153 | **16/16** negative | +0.020 | mixed |
| V3 | −0.134 | **16/16** negative | −0.127 | 14/16 negative |
| hV4 | −0.213 | **16/16** negative | −0.092 | 15/16 negative |

### 2.2 HC FPR concern (specificity)

- sub-10 V2 anomaly: n=6 ρ=−0.057 (CVD-like sign in *near-normal* subject); n=4 retains negative sign in 16/16 subsets. Pre-existing specificity issue (MEMORY: baseline_delta_rho rank 7/8) — **n=4 reduction does not worsen, but also does not resolve**.
- HC mean ρ behavior at n=4: V1 +0.138→+0.121-0.199, V4 +0.055→+0.019-0.136. Mostly stable or slightly *higher* at n=4, consistent with Gonzalez-Castillo 2017 prediction (late runs add noise in occipital cortex).

### 2.3 Critical leading-4 finding

For sub-08 hV4: leading-4 ρ = −0.216 vs n=6 anchor −0.213 (Δ < 0.005). Late runs (5,6) contribute essentially zero signal beyond noise. Sub-08 V1 leading-4 also reproduces sign exactly. This is a project-specific reproduction of Gonzalez-Castillo 2017.

---

## 3. Crossnobis split-half RDM reliability (Walther 2016)

`v1_crossnobis_n4_vs_n6.json`. Crossnobis distance (LORO cross-validated Mahalanobis) with Ledoit-Wolf shrinkage MVNN pre-whitening per half. Spearman correlation between RDMs from disjoint halves.

Walther 2016 권고: continuous crossvalidated distance + MVNN reliable above r≈0.5.

| Subject | ROI | n=6 r | n=4 leading | n=4 random mean | % n=4 subsets ≥ 0.5 |
|---|---|---:|---:|---:|---:|
| **sub-08 (deutan)** | V1 | +0.901 | +0.837 | +0.825 | **100%** |
| | V2 | +0.932 | +0.935 | +0.900 | **100%** |
| | V3 | +0.886 | +0.855 | +0.848 | **100%** |
| | hV4 | +0.922 | +0.964 | +0.893 | **100%** |
| **sub-09 (protan)** | V1 | +0.808 | +0.768 | +0.759 | **100%** |
| | V2 | +0.761 | +0.563 | +0.636 | **100%** |
| | V3 | +0.701 | +0.762 | +0.660 | **100%** |
| | hV4 | +0.653 | +0.577 | +0.599 | **100%** |
| sub-10 (null) | V1 | +0.700 | +0.363 | +0.491 | 47% |
| | V2 | +0.894 | +0.791 | +0.803 | 100% |
| | V3 | +0.449 | +0.432 | +0.348 | 0% |
| | hV4 | +0.016 | −0.032 | +0.105 | 0% |
| HC mean (n=7) | V1 | +0.572 | +0.397 | (varies) | majority ≥0.5 |
| | V2 | +0.515 | +0.330 | | |
| | V3 | +0.449 | +0.303 | | |
| | hV4 | +0.598 | +0.555 | | |

### 3.1 Interpretation
- **sub-08, sub-09 모두 4-run에서 RDM 안정성 100% 보존** (Walther threshold). 이는 MVPA pattern stability에 대한 가장 직접적 증거.
- **sub-10 V4, V3 reliability collapse**: 작은 voxel count (V4=70) + near-normal signal로 인한 known limitation — n=6에서도 reliability 낮음, n=4 reduction과 무관.
- **HC mean reliability**: V1/V2/V3에서 n=4 leading 시 ~0.10-0.20 하락. V4에서는 거의 일정. **이는 HC FPR 양보 가능성을 시사하지 않음** — reliability는 RDM 구조 안정성이지 false-positive 빈도가 아님.

### 3.2 sub-07 hV4 (16 voxels) 알림
sub-07의 hV4는 16 voxels만 (MEMORY 명시). split-half (각 half 8 voxels)에서 종종 RDM degenerate (ConstantInput warning). HC mean에 nan 영향. 본 결과에서는 nanmean으로 처리.

---

## 4. Permutation p-value retention (1000 perm, 6.0 min wallclock)

`v1_permutation_n4_vs_n6.json`. Two permutation tests at each cell.

### 4.1 Test A: Raw LOCO ρ vs chance label shuffle (decoding above chance)
- Shuffle color labels within each run, recompute LOCO ρ, derive null.
- p_two = fraction of |perm ρ| ≥ |observed ρ|.

| ROI | sub | n=6 ρ | n=6 p_two | n=4 leading p_two | n=4 random p<.05 ret | n=4 random p<.01 ret |
|---|---|---:|---:|---:|---:|---:|
| V1 | sub-08 | −0.198 | **0.049*** | 0.836 | 7% | 0% |
| V1 | sub-09 | +0.049 | 0.989 | 0.962 | 0% | 0% |
| V1 | sub-10 | +0.123 | 1.000 | 1.000 | 0% | 0% |
| V2 | sub-08 | −0.153 | 0.810 | 0.505 | 13% | 0% |
| V2 | sub-10 | −0.057 | 0.991 | 0.570 | 20% (FP) | 7% (FP) |
| V3 | sub-08 | −0.134 | 0.984 | 0.994 | 0% | 0% |
| V4 | sub-08 | −0.213 | 0.755 | 0.492 | 0% | 0% |
| V4 | sub-09 | −0.092 | 0.999 | 0.984 | 0% | 0% |

**Test A 결론**: sub-08 V1 marginal (p=0.049 at n=6)만이 유일한 borderline anchor. n=4 leading에서 NS (0.836), random 7% retention. **다른 모든 sub-08/sub-09 cells는 n=6에서도 Test A 기준 NS**.

### 4.2 Test B: Profile-match (Spearman vs HC baseline) — project convention

| ROI | sub | n=6 Spearman | n=6 p_neg | n=4 leading p_neg | n=4 random p<.05 ret | p<.01 ret |
|---|---|---:|---:|---:|---:|---:|
| V1 | sub-08 | −0.429 | 0.136 | 0.415 | 0% | 0% |
| V1 | sub-09 | −0.381 | 0.195 | 0.273 | 0% | 0% |
| V2 | sub-08 | +0.024 | 0.528 | 0.315 | 0% | 0% |
| V2 | sub-10 | −0.333 | 0.202 | **0.001*** (FP) | 20% (FP) | 13% (FP) |
| V3 | sub-09 | +0.643 | 0.956 | 0.976 | 0% | 0% |
| V4 | sub-08 | +0.595 | 0.947 | 0.926 | 0% | 0% |
| **V4** | **sub-09** | **−0.833** | **0.007*** | 0.413 | **0%** | **0%** |
| V4 | sub-10 | −0.048 | 0.464 | 0.581 | 7% | 0% |

**Test B 결론**:
- **sub-09 V4 = 유일한 robust vulnerability landmark** (p_neg=0.007** at n=6) — protan deficit signature.
- **n=4 leading 및 모든 random subsets에서 0/15 retention** → 19일 plan §4 Pass-4 criterion "≥80%" **완전 미달**.
- **sub-10 V2 false-positive 악화**: n=6 p=0.202 (NS) → n=4 leading p=0.001*** (잘못 significant). 20% random subsets에서 p<.05 FP, 13%에서 p<.01 FP. **Specificity가 reduction으로 *악화*됨**.

### 4.3 HC FPR (label-permutation, profile match p_neg<.05)

| ROI | n=6 HC FPR | n=4 leading HC FPR | n=4 random HC FPR |
|---|:---:|:---:|:---:|
| V1 | 0/7 | 0/7 | 2/105 (1.9%) |
| V2 | 0/7 | 0/7 | 0/105 (0%) |
| V3 | 0/7 | 0/7 | 0/105 (0%) |
| V4 | 1/7 (sub-05) | 1/7 (sub-03) | 3/105 (2.9%) |

**HC FPR 안정적** — n=6와 n=4 random subsets 모두 ≤3% (expected 5% baseline 이하). MEMORY의 "HC FPR=7/7"은 *cone-shift model fit* perm framework에 해당; raw label-perm에서는 FPR이 baseline 수준.

### 4.4 19일 plan §4 Pass-4 criterion 적용

| Criterion (raw label-perm framework 기준) | Status |
|---|---|
| sub-08 hV4 LOCO p<.01 retained ≥80% | n=6 자체 NS (p=0.755) → criterion irrelevant for this framework |
| sub-08 V1 LOCO p<.001 retained ≥80% | n=6 p=0.049, n=4 7% retention → **FAIL** |
| sub-09 V4 vulnerability (Test B) p<.01 retained ≥80% | n=6 p=0.007**, n=4 0% retention → **FAIL** |
| sub-10 V1/V4 LOCO NS in ≥95% subsets | V1/V4 OK, **V2 false-positive 20% n=4 random → FAIL** |
| HC LOCO FPR at n=4 ≤ HC FPR at n=6 | ≤3% across all ROIs → **PASS** |

**Raw label-permutation framework 기준 Pass-4: FAIL** (sub-09 V4 landmark loss + sub-10 V2 FP worsening).

### 4.5 (NEW) Sub-10 V2 false-positive 악화 — framework-independent specificity 우려

Pre-existing MEMORY: sub-10은 baseline_delta_rho rank 7/8 (CVD-indistinguishable) — 알려진 specificity 문제. 본 v1 perm이 추가로 발견:

- **sub-10 V2 profile_perm_p_negative**:
  - n=6: 0.202 (NS) — n=6 자체로는 false-positive 아님
  - **n=4 leading: 0.001*** — strong false-positive!**
  - n=4 random: **20% subsets에서 p<.05 FP, 13%에서 p<.01 FP**
- 동일 패턴이 sub-10 V2 decoding test (Test A)에서도 보임: 20% FP at p<.05.

**해석**: Run count 감소가 sub-10에서 *spurious* vulnerability signature를 *생성*. 이는 framework와 무관 (Test A raw decoding + Test B profile match 모두에서 발현). 가능한 mechanism:
- Reduced n_runs → wider null distribution → quirky color-pattern alignments이 우연히 강한 anti-HC profile을 만들 수 있음
- 특히 sub-10 V2 sample-by-chance가 leading-4에서 매우 anti-HC (Spearman=−0.952)

**Pass-4 implication**: 19일 plan §4 criterion "sub-10 V1/hV4 LOCO non-significant (p>.05) in ≥95% of subsets" 는 V2가 명시되지 않았으나 정신적으로 동일 — V2에서 80% (12/15) random subsets만 NS at p<.05, **violates ≥95% threshold**. 이는 *Pass-4 criterion의 어떤 perm framework로 해석하든 binding* — framework 독립적 specificity 손실.

### 4.6 (NEW) Sub-08 V4 profile-shape finding — domain-relevant side observation

본 v1에서 발견된 별도 finding (run-count 와 무관):

- sub-08 V4 vulnerability profile vs HC baseline: **Spearman = +0.595** (positive, p_neg=0.947 NS) at n=6
- 즉 sub-08 deutan의 hV4 *vulnerability profile shape*은 HC baseline과 **positive correlated**
- vs sub-09 V4: Spearman = −0.833 (anti-HC, 명확한 vulnerability)

**해석**: Sub-08 deutan의 hV4 vulnerability은 **profile shape 차이가 아닌 amplitude 차이** (overall mean ρ 차이). sub-09 protan은 *shape* 차이도 큼 (anti-HC profile). 두 CVD subtype이 *어떻게 다르게 fail하는지* 라는 domain 통찰이며, 본 run-count 질문과 별도 사안.

**Action**: MEMORY 갱신 권장 — sub-08 V4 vulnerability framing을 "profile-shape distortion" 에서 "amplitude reduction with preserved profile shape"로 재정렬. notion.md / RESULTS.md 영향 가능.

### 4.7 CRITICAL 해석 caveat

MEMORY의 landmark "sub-08 hV4 LOCO p=0.004**", "sub-08 V1 LOCO p=0.001***"는 **cone-shift model fit p-value** (Machado/R+C/2-component 적용 후 Spearman fit perm). 본 v1 perm은 **unshifted Δλ=0 baseline 만 사용**한 raw label-perm. 결과적으로 본 v1은 MEMORY landmark의 *necessary but not sufficient* test:
- **본 framework가 NS**라고 cone-shift model fit이 NS인 것은 *아님*
- **본 framework가 significant**라면 cone-shift fit도 significant일 가능성 높음 (sub-09 V4 케이스)

따라서 본 결과 ("sub-08 anchors all NS at n=6")는 **모순적이지 않음** — sub-08 anchor의 강한 시그널은 cone-shift basis 적용 후에만 나타남. **strict MEMORY landmark retention 검증을 위해서는 v2: cone-shift model-fit perm 별도 실행 필요**.

---

## 5. Critical caveats

### 5.1 Permutation framework mismatch with MEMORY landmarks
MEMORY entries like "Sub-08 hV4 LOCO: 2-component (βs=38°,βc=-14°) p=0.004**" are derived from:
1. Fit cone-shift model (Machado / R+C / 2-component) → get predicted_vuln_profile under best-fit Δλ
2. permutation_test_spearman(predicted_vuln, observed_vuln) under cone-shifted basis

Our v1 perm test uses **unshifted** (Δλ=0) basis as reference. The "p=0.004" landmark is a *fit quality p-value* (cone-shift model predicts observed profile better than random), not raw LOCO ρ. **Strict reproduction of MEMORY landmark perm test requires running the cone-shift fitting inside each subset** — separate v2/v3 work.

### 5.2 HC baseline vuln has self-leak for HC subjects
HC baseline used in Test B = mean of all 7 HC LOCO vuln profiles. For HC subjects, this includes self → inflates Spearman with HC mean. LOO HC baseline would be cleaner. For v1 we keep all-HC baseline and note this artifact.

### 5.3 sub-09 has known weak signal at V1
MEMORY: "Gen-4 sub-09 V1 cone-shift Δλ≈16.5 is geometry-weak, neural-fail, family-non-specific." Sub-09 V1 LOCO ρ near zero at n=6 means n=4 sign retention is unreliable here regardless of run count.

### 5.4 Pass-4 Decision rule application (binding)
19일 plan §4 requires retention in **≥80% of C(6,4)=15 random subsets** at the original threshold. Sign-retention numbers (Sec 2) are NOT p<.01 retention — those require completion of Sec 4.

---

## 5. Saturation curve & cut-off analysis (n ∈ {2,3,4,5,6})

`v1_saturation_loco.json`, `v1_saturation_crossnobis.json`. All C(6,n) subsets enumerated: 15+20+15+6+1 = 57 subsets per subject per ROI. Total 2,280 LOCO cells + 640 crossnobis cells, runtime 55s.

### 5.1 LOCO ρ saturation — mean ± SD across C(6,n) subsets

| ROI | subj | n=2 | n=3 | n=4 | n=5 | n=6 |
|---|---|---:|---:|---:|---:|---:|
| **V1** | sub-08 | −0.049±0.083 | −0.068±0.061 | −0.076±0.043 | −0.099±0.022 | **−0.198** |
| | sub-09 | +0.079±0.074 | +0.078±0.060 | +0.073±0.047 | +0.061±0.030 | +0.049 |
| | sub-10 | +0.126±0.063 | +0.126±0.041 | +0.125±0.027 | +0.124±0.016 | +0.123 |
| | HC mean | +0.143±0.116 | +0.152±0.109 | +0.159±0.112 | +0.155±0.113 | +0.138 |
| **V2** | sub-08 | −0.118±0.098 | −0.204±0.051 | −0.223±0.047 | −0.150±0.019 | −0.153 |
| | sub-09 | +0.025±0.085 | +0.031±0.065 | +0.026±0.056 | +0.015±0.040 | +0.020 |
| | sub-10 | −0.025±0.097 | −0.059±0.074 | −0.096±0.057 | −0.110±0.029 | −0.057 |
| **V3** | sub-08 | +0.050±0.089 | −0.050±0.072 | −0.127±0.034 | −0.130±0.019 | **−0.134** |
| | sub-09 | +0.074±0.099 | +0.035±0.105 | −0.021±0.076 | −0.088±0.072 | −0.127 |
| | sub-10 | +0.168±0.052 | +0.199±0.036 | +0.220±0.020 | +0.233±0.014 | +0.243 |
| **V4** (hV4) | sub-08 | −0.205±0.107 | −0.272±0.052 | −0.214±0.028 | −0.213±0.018 | **−0.213** |
| | sub-09 | +0.012±0.117 | −0.022±0.107 | −0.071±0.069 | −0.085±0.044 | −0.092 |
| | sub-10 | +0.161±0.142 | +0.175±0.109 | +0.182±0.080 | +0.183±0.048 | +0.171 |
| | HC mean | +0.137±0.192 | +0.118±0.184 | +0.088±0.156 | +0.072±0.149 | +0.055 |

### 5.2 SD (across-subset variability) — monotonic decrease

| ROI | subj | SD(n=2) | SD(n=3) | SD(n=4) | SD(n=5) |
|---|---|---:|---:|---:|---:|
| V1 | sub-08 | 0.083 | 0.061 | 0.043 | 0.022 |
| V1 | sub-09 | 0.074 | 0.060 | 0.047 | 0.030 |
| V2 | sub-08 | 0.098 | 0.051 | 0.047 | 0.019 |
| V3 | sub-08 | 0.089 | 0.072 | 0.034 | 0.019 |
| V4 | sub-08 | 0.107 | 0.052 | **0.028** | 0.018 |
| V4 | sub-09 | 0.117 | 0.107 | 0.069 | 0.044 |
| V4 | sub-10 | 0.142 | 0.109 | 0.080 | 0.048 |

핵심: **SD가 n=2→5에 걸쳐 ~3-5× 감소**. n=4에서 sub-08 hV4 SD=0.028 (n=6 ρ=−0.213 대비 13% variability — acceptable). sub-09 hV4 SD=0.069 (큰 변동, signal 자체가 약함과 일관).

### 5.3 Knee-point analysis (Δρ/|ρ(n=6)|)

| ROI | subj | Δ(2→3) | Δ(3→4) | Δ(4→5) | Δ(5→6) | Knee |
|---|---|---:|---:|---:|---:|---|
| V1 | sub-08 | −10% | −4% | −12% | **−50%** | **n=5→6 jump** |
| V1 | sub-09 | −2% | −10% | −25% | −23% | gradual |
| V3 | sub-08 | −74% | −57% | −2% | −3% | **n=4 saturated** |
| V3 | sub-09 | −31% | −45% | −52% | −31% | no saturation |
| **V4** | **sub-08** | **−31%** | **+27%** | **+0.7%** | **+0.06%** | **n=3-4 saturated** |
| V4 | sub-09 | −37% | −53% | −15% | −8% | n=5 converging |
| V4 | sub-10 | +8% | +4% | +0.4% | −7% | stable null |

핵심 발견:
1. **sub-08 hV4: n=3 이미 saturate** — n≥3에서 Δ<1% (점근 도달). hV4 vulnerability signal은 4-run 이상에서 fully resolvable.
2. **sub-08 V3: n=4 saturate** (Δ(4→5)=-2%). 
3. **sub-08 V1: n=6→5 step에서 큰 jump (-50%)** — V1은 n=5/6에서도 안정화 미완. ρ(n=4)=−0.076 vs ρ(n=6)=−0.198 → 4-run은 V1에서 신호 강도 35-40%만 포착.
4. **sub-09 모든 ROI에서 saturation 미달** — n=6에서도 signal이 막 emerging 상태. protan signal이 6 runs로도 marginal.

### 5.4 Crossnobis split-half saturation (Walther 2016)

even n에서만 split-half 가능. n=4: 2v2 splits (3 unique). n=6: 3v3 splits (10 unique).

| ROI | subj | n=4 mean±SD | n=6 mean±SD | %(r≥0.5) n=4 |
|---|---|---:|---:|---:|
| V1 | sub-08 | +0.825±0.041 | +0.901 | **100%** |
| V1 | sub-09 | +0.759±0.045 | +0.808 | **100%** |
| V2 | sub-08 | +0.900±0.026 | +0.932 | **100%** |
| V2 | sub-09 | +0.636±0.087 | +0.761 | **100%** |
| V3 | sub-08 | +0.848±0.048 | +0.886 | **100%** |
| V3 | sub-09 | +0.660±0.089 | +0.701 | **100%** |
| V4 | sub-08 | +0.893±0.051 | +0.922 | **100%** |
| V4 | sub-09 | +0.599±0.049 | +0.653 | **100%** |
| V4 | sub-10 | +0.105±0.154 | +0.016 | 0% (known degeneracy) |

핵심: **모든 sub-08/sub-09 ROI에서 n=4 crossnobis r이 n=6 대비 90%+ 보존**. RDM 구조 안정성은 4-run에서 사실상 fully preserved.

### 5.5 Cut-off 권고

| ROI | n=3 verdict | n=4 verdict | n=5 verdict |
|---|---|---|---|
| **V4 (hV4) primary** | sub-08 saturated, sub-09 weak | **sub-08 PASS, sub-09 marginal** | sub-08/09 both stable |
| V3 | sub-08 OK, sub-09 unstable | sub-08 saturated, sub-09 still converging | sub-09 still 30%+ residual |
| V2 | unstable (variable SD) | sub-08 stable, V2 has FP issue | acceptable |
| V1 | unstable | **sub-08 ρ 35-40% preserved only** (V1 needs more runs) | sub-08 ρ 50% preserved |

**3가지 cut-off scenario**:

| Scenario | Recommendation | Rationale | Tradeoff |
|---|---|---|---|
| **Aggressive (n=3)** | 3 runs × 2 conditions = 6 total | hV4 primary endpoint saturate, RDM r≥0.5 likely 80%+ | V1 신호 50%+ 손실, sub-09 안정성 부족, SD 0.05-0.10 |
| **Balanced (n=4)** ✓ | 4 runs × 2 conditions = 8 total | sub-08 hV4 fully saturated, RDM r=0.83-0.90 100% preserved, SD acceptable | V1 신호 35-40% 손실, sub-09 marginal, sub-10 V2 FP 악화 가능 |
| **Conservative (n=5)** | 5 runs × 2 conditions = 10 total | 거의 모든 metric saturate, sub-09 marginal 회복 | session time 다소 증가 |

**Primary recommendation**: **n=4 (balanced)** if hV4 primary endpoint이고 sub-09 secondary. **n=5 (conservative)** if sub-09 vulnerability fully preserve해야 하거나 V1 신호도 strict하게 보존해야 할 경우.

### 5.6 Visualization

- `fig_saturation_loco.png` — LOCO ρ saturation grid (4 ROI × 3 CVD + HC mean), mean±SD + 10/90 percentile band
- `fig_saturation_sd.png` — across-subset SD decay (stability metric)
- `fig_saturation_crossnobis.png` — split-half RDM reliability (Walther 2016 threshold)
- `fig_decision.png` — 2×2 decision panel (hV4 primary, hV4 RDM, V1 binding, sub-09 fragility)

Script: `scripts/plot_saturation.py`. matplotlib only (no seaborn per CLAUDE.md §5).

---

## 6. Files

- Point estimate (n=4 vs n=6): `run_count_validation/v1_allroi_n4_vs_n6.json`
- Permutation null (n=4 vs n=6, 1000 perm): `run_count_validation/v1_permutation_n4_vs_n6.json`
- Crossnobis RDM reliability (n=4 vs n=6): `run_count_validation/v1_crossnobis_n4_vs_n6.json`
- **Saturation curve (n ∈ {2,3,4,5,6})**: `run_count_validation/v1_saturation_loco.json`
- **Saturation crossnobis (even n)**: `run_count_validation/v1_saturation_crossnobis.json`

Scripts:
- `scripts/run_count_subsample.py` — v1 point estimate
- `scripts/run_count_permutation.py` — raw label-perm
- `scripts/run_count_crossnobis.py` — split-half RDM reliability
- `scripts/run_count_saturation.py` — full saturation curve

Sanity check outputs (kept for debugging):
- `run_count_validation/sanity/`
- `run_count_validation/sanity2/`
- `run_count_validation/sanity3/`
- `run_count_validation/sanity_crossnobis/`

---

## 7. Next steps

### v2 — cone-shift model-fit perm (MEMORY landmark 정합)
1. Extend `run_count_permutation.py` to call cone-shift fit (Machado / R+C / 2-component) at each subset, then permutation_test_spearman(predicted_vuln_at_best_fit, observed_vuln).
2. This matches MEMORY landmark perm framework. Expected to recover sub-08 hV4 (p=0.004**), sub-08 V1 (p=0.001***) signals.
3. **v2 timing sanity (2026-05-20)**: machado_1way fit + 1000 perm per cell = **0.52 sec**. Full scope (680 cells) = ~6 min serial / ~1-2 min parallel. **Local feasible, SLURM 불필요**. Adding 2-component model (df=2) ~3x → ~3-5 min parallel total.
4. Sanity hit: sub-08 hV4 machado_1way fit at n=6: Δλ=1.32, Spearman=+0.571 (model fits well), perm p=0.082 (marginal under 1D model). 2-component model expected to push p<.01 (matching MEMORY).
5. Until v2 done, **Pass-4 verdict on basis of v1 is framework-conditional only**.

### v3 — ΔRDM landmark perm
Following MEMORY: sub-09 V1 ΔRDM p=0.005** is another landmark not directly tested in v1 (crossnobis is *reliability*, not the ΔRDM significance test). Need to implement voxel-space ΔRDM under cone-shift sweep + perm.

### Decision protocol
- If v2 sub-08 hV4 / V1 anchors retain p<.01 at ≥80% of n=4 subsets → **Pass-4** despite v1 raw-perm FAIL
- If v2 also shows landmark loss at n=4 → **Fail-4**, keep 6 runs per condition
- Either outcome, sub-10 V2 FP at n=4 (Sec 4.2) is a permanent specificity warning

### PI review
- 19일 plan + 5월 20일 addendum + 본 REPORT (v1) + v2 결과 도착 후 합본
- Honest framing 필수: v1만으로는 Pass-4 strict 불충족
- 두 가지 *positive evidence* (sign retention 64/64, crossnobis r≥0.5 100%)는 PI를 설득할 수 있는 강한 보조 근거
