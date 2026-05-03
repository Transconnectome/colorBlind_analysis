# Plan 04 Filter Refinement — Executive Summary

> 생성: 2026-05-02 · 최종 업데이트: 2026-05-03 · Cycle 1~13 종합. **Phase 2 종결**. Phase 3 (behavioral validation) 트리거 문서.

---

## 0. 한 줄 요약

CVD inverse filter selection rule Cycle 1~13. **Cycle 13 baseline_sp 회귀 보정이 framework의 critical limit 노출**: HC corr(baseline_sp, z_combined) = −0.968 V4 deutan. **sub-08 deutan만 baseline 보정 후 robust specific** (V4|V4 z_residual=−58.93). **sub-09 protan은 어떤 cell에서도 baseline 보정 후 NOT specific** (best z_resid=−1.43). 이전 Cycle 11 V1|V4 cross-ROI "sub-09 회복" 주장은 baseline_sp 우연 일치였음. Family assignment (cone-test 가정)는 검증 통과 (Cycle 13). Phase 3 primary는 sub-08만, sub-09는 행동 검증 결정적.

---

## 1. 최종 Selection Rule

```
Subject s 에 대해 family(s) 자동 지정:
  sub-08 (deutan) → c_family=yellow,  sign_family=−1
  sub-09 (protan) → c_family=magenta, sign_family=+1

ROI: V1 + V4 (z_sum). V4 voxel-axis primary, V1 보조.

Loss:
  L = z_set(R) + z_vox-axis(R, c_family)

  z_set      = [l_topk_jaccard(k=3) + 0.2·((β_s/80)² + (β_c/60)²)]_min
                ↳ 8-color set match + Tikhonov

  z_vox-axis = -[ sign_family·z_mean_amp(c_family)
                + |z_rdm-row(c_family)|
                + |z_run_consistency(c_family)| ]
                ↳ within-subject voxel-pattern signature, family-signed

평가: HC pool (n=6, sub-07 제외) 대비 z<−2 → specificity.
```

## 2. 검증 결과 (point estimate)

| 피험자 | z_combined V1+V4 | 판정 |
|---|---:|---|
| **sub-08 (deutan)** | **−19.32** | robust (HC FP max 보다 4× 강함) |
| **sub-09 (protan)** | **−5.95** | fragile (sub-04 HC FP −5.09 와 거의 동급) |
| sub-10 (near-normal) | −0.09 | perfect sanity |

## 3. HC FP rate (Cycle 8 #3)

n=6 HC LOO 검증, V1+V4 selection rule 적용:

| target | deutan z | protan z | verdict |
|---|---:|---:|---|
| sub-01 | −1.87 | −0.68 | marginal |
| sub-02 | −0.57 | **−4.39** | **FP under protan** |
| sub-03 | +0.05 | +1.18 | pass |
| **sub-04** | **−4.40** | **−5.09** | **FP under both** |
| sub-05 | +1.46 | +1.98 | pass |
| sub-06 | +8.71 | +13.52 | pass (반대 방향) |

→ **FP rate = 2/6 (33%)** under either family.

## 4. sub-04 데이터 정밀 진단 (Cycle 8 #4)

**전제**: sub-04 는 진짜 HC. 어떤 데이터가 deutan-like outlier 를 만드는가?

| ROI | sub-04 mean amp z (vs n=5 HC pool) | 진단 |
|---|---|---|
| V1 | yellow z=**+2.21** (양수 outlier) | sub-08 (음수 outlier) 와 **부호 반대**. selection rule 의 |z_rdm|+|z_runc| 이 dominant 해서 부호 mismatch 무시 |
| V2 | yellow z=**+2.57**, green z=−2.63, magenta z=+2.23 | 3개 색 outlier, 가장 noisy ROI |
| V4 | magenta z=+2.07 만 outlier (yellow NS) | sub-04 V4 deutan family 에는 신호 없음 |

**핵심**: sub-04 yellow 신호는 sub-08 과 *부호가 반대*인 양수 outlier (BOLD 더 강함). selection rule 의 family-signed mean term 만으로는 분리되지만, |z_rdm|+|z_runc| 항이 부호와 무관하게 큰 양수로 합산되어 최종 L 음수 (false specificity) 유도.

## 5. Local Bootstrap (n=100) Overlap 정량화

| Cell | L_vox CI95 | family-color |
|---|---|---|
| sub-09 V4 (CVD) | **[−15.15, −6.75]** | protan, magenta |
| sub-04 V4 (HC LOO) | **[−5.38, −0.46]** | deutan, yellow |
| sub-09 V1 (CVD) | [−24.97, −7.76] | protan, magenta |
| sub-04 V1 (HC LOO) | [−26.92, −3.98] | deutan, yellow |

→ **V4 에서 sub-09 vs sub-04 disjoint** (CI 분리 깔끔).
→ **V1 에서는 overlap 상당** ([−15, −7.76] 와 [−27, −3.98] 일부 겹침).

→ **결론**: V4 single-ROI 가 V1+V4 결합보다 specificity 에 더 안전.

## 6. Pre-image Filter (Cycle 8 #2)

Forward T(θ; β_s, β_c, family) = θ + β_s·cos(θ−90°) + β_c·cos(θ−θ_conf) 의 numerical inverse.

### sub-08 V4-only (β_s=38, β_c=7) — best deutan compensation

| color | obs° | pre-image° | shift° |
|---|---:|---:|---:|
| red | 0 | 3.5 | +3.5 |
| orange | 45 | 29.7 | −15.3 |
| yellow | 90 | 58.0 | **−32.0** |
| green | 135 | 93.2 | **−41.8** |
| blue | 225 | 266.0 | +41.0 |
| purple | 270 | 306.8 | +36.8 |

### sub-09 V1+V4 avg (β_s=30.5, β_c=12) — protan compensation

| color | obs° | pre-image° | shift° |
|---|---:|---:|---:|
| yellow | 90 | 55.6 | **−34.4** |
| green | 135 | 105.5 | **−29.5** |
| blue | 225 | 260.3 | +35.3 |

(sub-09 V4-only 는 β_s=0 이라 trivial.)

## 7. 권장 사용 — Phase 3 행동 검증 단계

| 시나리오 | 권장 cell | 신뢰도 |
|---|---|---|
| **sub-08 deutan filter** | V4 single-ROI z=−4.97 (Tikh) + V4 voxel-axis | **high** (boot CI 깔끔) |
| **sub-08 deutan filter (강화)** | V1+V4 z=−19.32 | high (sub-04 V1+V4 −4.40 보다 4× 강함) |
| **sub-09 protan filter** | V4 voxel-axis only z=−2.85 (Cycle 7) | **moderate** (V1 결합 시 sub-04 와 overlap) |
| sub-09 protan (set-match) | V2 perfect set-match (Cycle 6s) | exploratory (β_s grid 모서리) |
| HC verification | z>0 maintained | 통과 (sub-10) |

## 8. 진행 미완 / 다음 단계

1. **Server bootstrap (Jobs 98931, 98945)** PD 4시간+. 결과 도착 시:
   - sub-09 V1+V4 결합 분포 vs sub-04 V1+V4 결합 분포 정확한 overlap 정량화
   - selection rule 보수화 (옵션 B: z<−6) 또는 reformulation 결정

2. **Selection rule reformulation 후보** (sub-04 발견 따라):
   - 부호 mismatch penalty: z_mean 부호가 family-expected 와 다르면 |z_rdm|, |z_runc| 항 감점
   - 또는: z_vox-axis 를 z_mean 단독 (family-signed)으로 단순화 — |z_rdm|, |z_runc| 제거
   - 기존 cycle 7 결과 재계산 필요

3. **sub-08 V1 origin 매칭** Tikhonov 효과 vs baseline 분리 — λ ∈ {0, 0.05, 0.1, 0.2} sweep boot 진행 중.

4. **Phase 3 trigger**: V4-only filter 우선 검증 (가장 robust). V1+V4 강화 filter 는 sub-04 와의 overlap 검증 후.

---

## 9. Cycle 9 실험 — l_signed_jaccard fitting loss (2026-05-03) — **REJECTED**

**가설**: `l_topk_jaccard` (집합 매칭)에 confusion DIRECTION(CW/CCW) 패널티를 추가하면 fitting loss가 더 선택적.

**구현**:
- sim_bias[c] = β_s·cos(θ_c−90°) + β_c·cos(θ_c−θ_conf), θ_c = stimulus angles [0,45,...,315]°
- obs_bias[c] = confusion_bias_summary.csv의 mean_signed_bias
- l_signed = mean over top-3 obs of max(0, −sign_obs·sign_sim) + no-prediction penalty (|sim|<5°)
- 새 loss: l_topk + l_signed + 0.2·Tikh

**결과**:
- sub-08 V4 z_set: −4.54 → −1.01 (악화)
- sub-08 V1/V2, sub-09 전 ROI: 마찬가지로 악화 또는 무효
- HC 신규 FP: sub-02 V2 z=−20.82 (catastrophic), sub-05 V1 z=−8.24

**실패 원인**: HC도 noisy LOCO confusion direction이 있어 동일 loss structure로 방향-매칭 parameter를 탐색 가능. Tikhonov(λ=0.2)로 억제 불가. 구조적 결함.

**결정**: l_signed_jaccard fitting loss REJECTED. 기존 l_topk + 0.2·Tikh + z_vox-axis selection rule 유지.

---

## 10. Cycle 10 — z_vox-axis 단순화 variant 비교 (2026-05-03) — **NET 개선 없음**

**가설**: PLAN04 §8 reformulation 후보 #2. sub-04 yellow z=+2.21(부호 반대)이 |z_rdm|+|z_runc|에 흡수되어 FP — 단순화로 해결 가능?

**Variants**:
- A: −(sign·z_mean + |z_rdm_row| + |z_runc|) [현행]
- **B**: −(sign·z_mean) [단순화]
- C: −(sign·z_mean + sign·z_runc)

**HC FP rate (V1+V4 z_combined < −2)**:
| | A | B | C |
|---|---:|---:|---:|
| deutan | 1/6 (sub-04) | 2/6 (sub-01, **sub-04 해소**) | 2/6 |
| protan | 2/6 | 2/6 | 2/6 |

**핵심 발견**:
1. Variant B는 sub-04 deutan FP(z=−4.40→+2.84)을 specifically 해결하지만 sub-01 deutan 신규 FP(z=−3.25) 발생 — 단순화로 FP가 다른 HC로 이동
2. **sub-02 protan FP는 모든 variant에서 지속** (z=−4.39~−4.88) → z_set(V4)=−3.80이 dominant, z_vox 변형으로 해결 불가
3. **sub-04 protan FP도 모든 variant에서 지속** → sub-04 magenta z_mean이 *실제로* 양수 (V1: +1.83, V2: +2.52, V4: +1.67), sub-09 protan signal과 같은 방향. 데이터 자체가 sub-04를 protan-like로 보임
4. **sub-08 deutan detection은 B/C에서도 유지** (B: −17.31)
5. **sub-09 protan detection은 B에서 약화** (−5.95→−4.48)

**sub-04 본질**: yellow와 magenta 양쪽에서 "abnormal" — yellow는 sub-08과 부호 반대, magenta는 sub-09와 같은 방향. 단순 HC outlier가 아닌 BOLD-high subject 또는 mild signal 후보.

**결정**:
- 현행 Variant A 유지 (단순화 net 개선 없음)
- sub-04는 "데이터 outlier" 분류, Phase 3에서 sensitivity analysis 필요
- Phase 3 권장: sub-08 V4 single-ROI 우선 (sub-04 V4 yellow z=+0.77로 weak), sub-09 V1+V4는 bootstrap CI overlap 검증 필수

---

## 11. Cycle 10b — sub-04 제외 sensitivity (2026-05-03) — **TRADE-OFF, fundamental data limit 확인**

**테스트**: HC pool에서 sub-04 제외 시 selection rule 변화

**CVD detection 강화**:
- sub-08 deutan: −19.32 → **−21.96** (Δ=−2.64)
- sub-09 protan: −5.95 → **−8.62** (Δ=−2.67) — fragile에서 robust 영역 진입

**HC FP 악화 (2/6 → 3/6)**:
- sub-01 deutan/protan 신규 FP (z=−3.61, −2.97)
- sub-02 protan FP 유지/악화 (z=−4.39 → −5.56)

**원인 — pool variance 변화**:
- V1 L_vox SD: deutan 1.13→0.60, protan 2.28→1.48 (sub-04가 V1 noise의 큰 source)
- z-score 민감도 증가 → CVD outlier 강화 + HC marginal subject도 FP 진입

**Fundamental finding**: n=6 HC pool은 너무 작음. sub-04 제외해도 sub-01 등 다른 high-variance subject 노출. **Selection rule 정교화로 해결 못함**.

**Phase 2 selection rule 작업 종결**:
- Cycle 9 (l_signed) REJECTED
- Cycle 10 (단순화) NET 개선 없음
- Cycle 10b (sub-04 제외) TRADE-OFF
- → 모든 reformulation 옵션 탐색 완료. 현행 Variant A 유지, Phase 3로 진행

**Phase 3 권장 (최종)**:
- sub-08 V4 filter (β_s=38, β_c=7): 모든 sensitivity test 통과, robust ✓
- sub-09 V1+V4 filter (β_s=30.5, β_c=12): bootstrap CI 검증 후 진행
- HC sanity check: sub-10 z>0 유지 (validated)

---

## 12. Cycle 10c — Server bootstrap (n=200) + threshold envelope (2026-05-03) — **Phase 2 종결**

**Server bootstrap 도착** (Jobs 98931, 98945) — 12 파일, n_boot=200, family-aware.

**V4-only CI95**:
- sub-09 V4 protan: [−14.66, **−6.73**] (point −7.15)
- sub-04 V4 deutan: [**−7.49**, −0.46] (point −1.44)
- → Overlap = [−7.49, −6.73] (1 단위, CI 폭 5~8 단위 대비 미미). **Effectively disjoint** ✓

**V1+V4 sum instability**:
- sub-04 V1 CI95: [−84.54, −3.98] (heavy-tailed!) → V1+V4 sum std ~110
- sub-09 V1+V4: −15.92, std ~8 (안정)
- sub-08 V1+V4: −24.15, std ~17 (압도적)
- → **sub-09 protan은 V4-only가 더 안전**한 선택 (CI overlap 명확) but V4-only z=−2.85 vs V1+V4 z=−5.95 → strength↓ stability↑ trade-off

**Threshold envelope (z<−6 옵션 B 검토)**:
| 피험자 | z_combined | z<−2 | z<−6 |
|---|---:|---|---|
| sub-08 deutan | −19.32 | detect | detect ✓ |
| sub-09 protan | −5.95 | detect | **MISS** |
| sub-04 protan FP | −5.09 | FP | pass ✓ |
| sub-02 protan FP | −4.39 | FP | pass ✓ |
| sub-04 deutan FP | −4.40 | FP | pass ✓ |

→ z<−6: HC FP 모두 해소, sub-08 robust 유지, **sub-09 always marginal band [−6, −2]**

**CI95의 정의 명확화**:
- Server bootstrap의 `L_vox.ci95`는 voxel-resampling bootstrap CI (HC pool fixed)
- **L_vox CI ≠ z_combined CI** (z_set 점추정 추가 필요)
- Cycle 10c의 P=0.97 separation 등은 L_vox 비교만 — z_combined 비교 시 다른 결론

**Phase 3 trigger 잠정 (Cycle 10d 정식 분석으로 수정됨)**: 아래 §13 참조

**미완 (low priority)**:
- 부호 mismatch penalty (term weighting 조정) — Cycle 10 단순 제거 net 개선 없음 → 동일 한계 예상
- sub-08 V1 Tikhonov sweep (§8 #3) — V4보다 weak signal, 부차

---

## 13. Cycle 10d — 정확한 z_combined CI 재계산 (2026-05-03) — **Phase 3 권장 결정적 수정**

**동기**: Cycle 10c의 L_vox 비교는 z_combined 비교가 아님. z_combined = z_set (point) + (L_vox − μ_pool)/σ_pool로 정확히 계산.

**Same-family CVD vs HC z_combined CI overlap**:
| Cell | CVD CI | HC CI | overlap | 판정 |
|---|---|---|---:|---|
| **V4 deutan**: sub-08 vs sub-04 | [−94.85, −27.58] | [−10.25, +0.73] | **0** | ✓ DISJOINT |
| V4 protan: sub-09 vs sub-02 | [−7.92, −2.87] | [−8.22, −3.81] | **4.11** | ✗ FULL OVERLAP |
| V1 deutan: sub-08 vs sub-04 | [−13.37, −3.11] | [−73.37, −2.08] | **10.26** | ✗ MASSIVE |
| **V1 protan**: sub-09 vs sub-02 | [−10.93, −2.93] | [−2.34, +0.18] | **0** | ✓ DISJOINT |
| V1+V4 deutan | [−108, −31] | [−84, −1] | 53 | ✗ MASSIVE |
| V1+V4 protan | [−19, −6] | [−11, −4] | 5 | ✗ overlap |

**핵심 finding — 진짜 robust한 cell은 두 개뿐**:
1. **sub-08 V4 deutan**: CI 완전 disjoint (gap 17 units)
2. **sub-09 V1 protan**: CI 완전 disjoint (sub-02 V1 protan ≈ 0)
3. 다른 모든 cell: substantial overlap

**Sub-09 V1의 결정적 한계**:
- V1 specificity는 robust ✓
- 그러나 V1 forward model fit이 **degenerate** (sub-09 V1: β_s=0, β_c=0 — null filter)
- "Specificity 입증 ≠ Filter 추정 가능"이 명확히 분리됨

**수정된 Phase 3 권장**:
| 시나리오 | 권장 cell | z_combined CI95 | filter 가능 | confidence |
|---|---|---|---|---|
| sub-08 deutan | V4 single (β_s=38, β_c=7) | [−95, −28] vs HC [−10, +1] | ✓ exact pre-image | **HIGH** |
| sub-09 protan | V1 specificity robust but **filter degenerate** | [−11, −3] vs HC [−2, 0] | ✗ V1 β=0 | **EXPLORATORY** (filter는 V4 또는 V1+V4 사용 — specificity overlap 감수) |
| HC verification | sub-10 z>0 | — | — | high |

**솔직한 종합 평가**:
- **sub-08 V4 filter는 dual-validated 가능 cell**: 통계적 robustness + filter parameters 명확 + pre-image exact
- **sub-09 protan은 fundamental gap**: 통계적 separability와 filter 추정이 같은 ROI에서 동시 만족 안 됨
- → Phase 3 primary endpoint는 **sub-08만**, sub-09는 exploratory only

---

## 14. Cycle 10e — HC group distribution (n=6) 비교 (2026-05-03)

**동기**: Cycle 10d의 비교는 worst-case HC (sub-04, sub-02) 개별 비교. 옳은 framing은 HC LOO 분포 전체 vs CVD point + bootstrap CI.

**HC distribution vs CVD bootstrap CI**:
| Cell | HC mean ± SD | HC range | CVD pt | CVD CI95 | 판정 |
|---|---|---|---:|---|---|
| **sub-08 deutan V4** | -0.22 ± 0.97 | [-1.57, +1.07] | **-31.30** | [-94.85, -27.58] | ✓ outside HC, CI disjoint |
| **sub-08 deutan V1+V4** | +0.56 ± 4.46 | [-4.40, +8.71] | **-35.08** | [-108, -31] | ✓ outside HC (27 unit gap) |
| sub-09 protan V4 | +0.15 ± 2.83 | [-3.98, +4.49] | -3.14 | [-7.92, -2.87] | ✗ within HC (**sub-02 -3.98이 더 음수**) |
| sub-09 protan V1+V4 | +1.09 ± 6.73 | [-5.09, +13.52] | -6.54 | [-18.85, -5.80] | marginal (sub-04 -5.09보다 1.5 unit) |

**결정적 finding**: sub-09 V4-only는 sub-02보다 덜 extreme → V4-only로 sub-09를 specifically identify 불가. sub-08은 어느 ROI 구성에서도 robust.

**수정된 Phase 3 trigger**:
| 시나리오 | 권장 cell | confidence |
|---|---|---|
| sub-08 deutan filter (primary) | V4-only (β_s=38, β_c=7) | **HIGH** |
| sub-08 deutan filter (강화) | V1+V4 (β_s=19, β_c=3.5) | high (V1 degenerate caveat) |
| sub-09 protan filter | V1+V4 (β_s=30.5, β_c=12) | **EXPLORATORY only** |
| sub-09 protan V4-only | β_s=0, β_c=2 | **NOT recommended** (HC 분포 내) |

**Phase 3 candidate visualizations**: `results/figures/filter_visualization_phase3/` 4개 figure 생성.

---

## 15. Cycle 10f — Per-term cross-ROI rule (UNTESTED, 후속 후보)

**사용자 제기 미검증 변형**:
```
현행: z_combined = z_set(V1) + z_set(V4) + z_vox(V1) + z_vox(V4)  (same ROI per term)
가능: z_combined = z_set(V4) + z_vox(V1)  (cross-ROI per term)
```

**근거**: V4 set 강함, V1 voxel pattern 강함 → 결합으로 cleaner specificity 가능?

**우려**: multiple testing burden, mechanistic 정당화 불명확, Cycle 1~10에서 시도 안 됨 (모두 same-ROI).

**Status**: Phase 3 후 sub-09 specificity 보강 필요 시 후속 cycle 후보.

---

## 16. Cycle 11 — Per-term cross-ROI 실행 결과 (2026-05-03) — **sub-09 specificity 회복**

**실행**: 9 (R_set, R_vox) pairs × 2 family × subjects 평가.
스크립트: `cycle11_per_term_cross_roi.py`, 결과: `cycle11_per_term_cross_roi.json`

**핵심 발견**:

| 피험자 | Best pair | z_combined | HC FP | 비교 |
|---|---|---:|---|---|
| sub-08 deutan | V4\|V4 (same) | −15.02 | 0/6 | baseline 변화 없음 |
| **sub-09 protan** | **V1\|V4 (cross)** | **−3.37** | **0/6** | **개선** vs V4\|V4 (-2.26, FP 1/6) |

**메커니즘 — sub-04 FP 해소**:
- V1+V4 sum: sub-04 protan z=-5.09 (FP)
- V1|V4 cross: sub-04 protan z=**-1.57** (PASS)

**sub-09 V1|V4 정확한 z_combined CI**:
- CVD: pt=-4.25, CI95=[-9.03, -3.99]
- HC range V1|V4: [-1.57, +10.71]
- **CI 완전 disjoint, gap 2.42 units** ✓

**Caveat**:
- 9 pairs × 2 family = 18 tests → multiple comparison. Bonferroni post-hoc도 z=-4.25 통과 (p≈0.00001).
- n=6 LOO FP=0/6 → Wilson CI [0%, 39%]
- Mechanistic: z_set(V1) = forward set match V1 강함, z_vox(V4) = voxel pattern V4 강함. 두 다른 evidence type → noise correlation 감소.

**수정된 Phase 3 권장 (Cycle 11 반영)**:
| 시나리오 | Selection rule | Filter parameters | confidence |
|---|---|---|---|
| sub-08 deutan | V4\|V4 same-ROI | V4 (β_s=38, β_c=7) | **HIGH** |
| **sub-09 protan** | **V1\|V4 cross-ROI** | V1+V4 avg (β_s=30.5, β_c=12) | **moderate-to-good** (이전 exploratory에서 격상) |
| HC verification | sub-10 z>0 | — | high |

**Framing 변경**: sub-09는 same-ROI에서 marginal, **cross-ROI rule에서 robust**. Manuscript에서 cross-ROI rule 필수 명시. Selection rule과 filter parameters가 다른 ROI mix인 점도 명시.

---

## 17. Cycle 11b — V1|V4 권장 철회 (post-hoc selection bias) (2026-05-03)

**사용자 정당한 비판**: cycle11에서 9 pairs × 2 family = 18 tests에서 best 골랐음 → selection bias.

**이론적 framework 검증**:
- z_set = LOCO-derived → V4 (LOCO gate ROI)
- z_vox-axis = RDM/pattern-derived → V1 (SRM 강한 ROI)
- → 이론적 cross-ROI = **V4|V1**

**이론 vs 경험 대조**:
| 피험자 | 이론 V4\|V1 | 경험 V1\|V4 | Same V4\|V4 |
|---|---|---|---|
| sub-08 deutan | z=−8.32, FP=2/6 | z=−11.00, FP=1/6 | **z=−15.02, FP=0/6** |
| sub-09 protan | z=−2.59, **FP=2/6** | z=−3.37, FP=0/6 | z=−2.26, FP=1/6 |

**결정적 결과**: 이론적 V4|V1는 sub-09 specificity *악화* (FP 1→2). 경험적 V1|V4는 이론과 정확히 반대 — fishing.

**정정된 Phase 3 권장 (post-Cycle 11b)**:
| 시나리오 | Selection rule | Filter param | confidence |
|---|---|---|---|
| sub-08 deutan | **V4\|V4 same-ROI** | V4 (β_s=38, β_c=7) | **HIGH** |
| sub-09 protan | **V4\|V4 same-ROI (revert)** | V1+V4 avg (β_s=30.5, β_c=12) | **EXPLORATORY** |
| sub-09 alt | V1\|V4 cross | V1+V4 avg | post-hoc only, 명시 필수 |

**데이터 저장**:
- `consolidated_phase2_results.csv` (48 rows: subject × ROI × family)
- `consolidated_cross_roi.csv` (144 rows: subject × family × R_set × R_vox)
- `consolidated_phase2_results.json`
→ 이후 분석은 직접 로드, 재계산 불필요

---

## 18. Cycle 11c — Loss에 cross-ROI 적용 가능성 (사용자 제안) — **결정 보류**

**제안**: "각 CVD가 유의미하게 달랐던 지표"로 cross-ROI loss 구성

**기술적 제약**:
- z_vox-axis는 (β_s, β_c) 무관 (관찰 데이터에서 직접 계산) → loss landscape 불가
- Loss landscape 활용 가능: l_topk_jaccard, l_rank, l_dir, xnobis_cosine, l_rdm

**제안 가능 형태**:
```
L_cross(β_s, β_c) = α·l_topk(V4) + β·xnobis(V1) + λ·Tikh
```

**우려**:
1. 여전한 selection bias (어느 지표가 유의미했는지 자체가 prior data)
2. Pre-registration 필요 (Phase 3 전)
3. 단위가 다른 항 결합 (α, β 가중치 정당화)
4. Per-subject custom loss = overfit risk

**4개 옵션**:
- A: Pre-registered theoretical loss (모든 subject 동일)
- B: Per-subject 적응형 loss
- C: Multi-criterion Pareto landscape
- D: 현행 유지, Phase 3 후 별도 Cycle 12로 검증

**권장 = 옵션 D**:
- Phase 3는 already-derived parameters로 진행
- cross-ROI loss는 Phase 3 결과가 marginal일 때 reformulation 정당화
- 현 시점 loss 변경하면 (a) bias 누적, (b) Phase 3 design 지연

---

## 19. Cycle 12 — Pre-registered cross-ROI LOSS 실행 (사용자 결정 진행)

**Pre-registered formula** (모든 CVD 동일):
```
L_cross(β_s, β_c) = α·l_topk_jaccard(V4) + β·l_rank(V1) + 0.2·Tikh
```

**Filter parameter shift (α=β=1)**:
| 피험자 | role | V4-only baseline | Cross-ROI loss | 변화 |
|---|---|---|---|---|
| **sub-09** | CVD | **(0, 0) degenerate** | **(30, 26) non-trivial** | **degeneracy 해소** ✓ |
| sub-08 | CVD | (58, −28) | (68, −38) | (+10, −10) 강화 |
| sub-04 | HC | (64, −36) | (18, 2) | null 방향 ✓ |
| sub-06 | HC | (62, 36) | (0, 0) | null 방향 ✓ |
| sub-01 | HC | (0, 0) | (48, 48) | non-trivial로 이동 (concern) |

**중요한 수렴**: sub-09 cross-ROI (30, 26)이 cycle8_preimage V1+V4 avg (30.5, 12)와 매우 가까움 → **두 독립 derivation 수렴**.

**Specificity (L_cross로)**:
| 피험자 | z_V4_only | z_cross_ROI |
|---|---:|---:|
| sub-08 | −4.54 | **−4.78** ✓ 강화 |
| sub-09 | +0.59 | −0.46 (여전히 not specific) |
| sub-02 (HC) | **−3.80 FP** | **−0.83 PASS** ✓ |
| sub-06 (HC) | −0.28 | +3.92 |

**결정적 분리**: Cross-ROI loss는 두 다른 역할:
- ✓ **더 좋은 parameter estimator** (sub-09 degeneracy 해소, sub-09 V1+V4 avg와 수렴)
- ✗ **더 좋은 specificity 지표는 아님** (sub-09 L_cross 분리 못함)

**Phase 3 함의**:
- sub-09 filter parameters에 대한 confidence 향상 (두 derivation 수렴)
- specificity는 여전히 marginal — 행동 검증 결정적
- Pre-image viz: `phase3_sub-09_cross_roi_loss_cycle12.png`, `phase3_sub-08_cross_roi_loss_cycle12.png`

---

## 20. Cycle 13 — Family 검증 + Baseline_sp 회귀 보정 (2026-05-03) — **CRITICAL FINDING**

**Family assignment 검증 (cone-test 가정 옳은가)**:
- sub-08 deutan: V4|V4 margin +11.11, V1+V4 sum +14.58 → ✓ matches cone test
- sub-09 protan: V4|V4 margin −1.76, V1+V4 sum −5.79 → ✓ matches cone test
- 단 sub-09 단일 ROI margin 약함

**Baseline_sp confound 정량 (HC pool 회귀)**:

| Cell | HC corr(baseline_sp, z) | sub-08 z_residual | sub-09 z_residual |
|---|---:|---:|---:|
| **V4|V4 deutan** | **−0.968** (massive!) | **−58.93 ✓✓** | −3.49 (cross-fam) |
| V4|V4 protan | −0.439 | −1.39 | **−1.25 NOT** |
| **V1|V4 deutan** | −0.542 | **−2.74 ✓** | −0.80 NOT |
| V1|V4 protan | −0.594 | +0.65 | **−1.01 NOT** |
| V1|V1 protan | −0.656 | +0.56 | −1.43 NOT |

**결정적 발견**:
1. **HC V4 z_combined는 거의 전적으로 baseline_sp가 결정** (r=−0.968)
2. **sub-08 deutan만 baseline 보정 후도 robust specific** (V4 z_resid=−58.93)
3. **sub-09 protan은 어떤 cell에서도 baseline 보정 후 NOT specific**
4. Cycle 11 V1|V4 cross-ROI "sub-09 specificity 회복"은 **baseline_sp confound 활용한 우연** — sub-04 FP 안 잡은 것은 sub-04 V1 baseline_sp(+0.667)와 sub-09 V1 baseline_sp(+0.357) 차이로 설명됨

**최종 Phase 3 권장 (Cycle 13 정정)**:
| 시나리오 | Selection rule | baseline-corrected | confidence |
|---|---|---|---|
| **sub-08 deutan** | V4|V4 same-ROI | z_resid = **−58.93** | **HIGH** ✓ |
| sub-08 deutan (강화) | V1|V4 cross-ROI | z_resid = −2.74 | high |
| **sub-09 protan** | (어느 cell도 NOT specific) | best z_resid = −1.43 | **EXPLORATORY only** |
| HC verification | sub-10 별도 분석 | — | — |

**Methodological 함의 (manuscript 필수)**:
- n=6 HC pool은 baseline_sp 변동 (V4 [-0.74, +0.79]) 정확 추정 부족
- baseline_sp confound가 framework의 가장 critical limit
- sub-08 deutan은 raw + baseline-corrected 양쪽에서 robust → 진짜 finding
- sub-09 protan은 baseline 보정 시 신호 사라짐 → Phase 3 행동 결정적

산출: `cycle13_family_baseline.json`

---

## 산출 파일 (Cycle 1~13)

```
scripts/cycle_filter_refinement/
  ├─ run_NxM.py                   # Cycle 1: N×M baseline
  ├─ cycle2_alt_combos.py         # Cycle 2: V2 sign-flip, Mahalanobis
  ├─ cycle3_unique_loss.py        # Cycle 3: Tikhonov
  ├─ run_bootstrap.py             # Cycle 4: HC subject boot
  ├─ cycle5_c8drop.py             # Cycle 5 Task 1: c8 magenta drop
  ├─ cycle5_cross_sim.py          # Cycle 5 Task 2: cross-simulator
  ├─ cycle6_voxel_diag.py         # Cycle 6 Step 1: per-color signature
  ├─ cycle6_step3_specificity.py  # Cycle 6 Step 3: HC sub-04 제외 효과
  ├─ cycle7_dual_criterion.py     # Cycle 7 Task A: family-aware dual
  ├─ cycle7_blend_wspearman.py    # Cycle 7 Task B: weighted Spearman
  ├─ cycle7_3way_blend.py         # Cycle 7 Alt: 3-way blend
  ├─ cycle8_voxel_bootstrap.py    # Cycle 8 #1: voxel-axis bootstrap
  ├─ cycle8_preimage.py           # Cycle 8 #2: pre-image filter
  ├─ cycle9_signed_jaccard.py     # Cycle 9: l_signed fitting loss (REJECTED)
  ├─ cycle10_simplified_voxaxis.py # Cycle 10: z_vox-axis 단순화 (NET 개선 없음)
  └─ cycle10b_exclude_sub04.py    # Cycle 10b: sub-04 제외 sensitivity (TRADE-OFF)
  ├─ cycle8_hc_fp.py              # Cycle 8 #3: HC LOO FP check
  └─ cycle8_viz.py                # Cycle 8: 4-figure visualization

results/cycle_filter_refinement/
  ├─ cycle{1,2,3}_aggregate.json
  ├─ cycle5_{c8drop,cross_sim}_aggregate.json
  ├─ cycle6_voxel_diag/{V1,V2,V4}_summary.json + aggregate.json
  ├─ cycle6_step3_specificity.json
  ├─ cycle7_{dual_criterion,blend_wspearman,3way_blend}.json
  ├─ cycle8_preimage.json
  ├─ cycle8_hc_fp.json
  ├─ cycle8_voxel_bootstrap_local/sub-{04,09}_{V1,V4}.json
  ├─ cycle8_voxel_bootstrap_server/{sub-02,04,08,09}_{V1,V2,V4}.json  ← Cycle 10c 도착 완료 (n=200)
  ├─ bootstrap_server/sub-{08,09}_{V1,V2,V4}.json (Cycle 6s n_boot=200)
  ├─ cycle8_figures/{fig1_z_components,fig2_hc_fp_vs_cvd,fig3_preimage_hue,fig4_bootstrap_overlap}.png
  ├─ cycle9_signed_jaccard.json     ← Cycle 9 실험 결과 (l_signed REJECTED)
  ├─ cycle10_simplified_voxaxis.json ← Cycle 10 결과 (variant A/B/C 비교)
  └─ cycle10b_exclude_sub04.json    ← Cycle 10b 결과 (sub-04 제외 sensitivity)

action_plans/
  ├─ 01_loss_filter_redesign.md          # Plan 01 (cycle 1~4)
  ├─ 02_bootstrap_variance.md            # Plan 02 (cycle 1)
  ├─ 03_literature_math_framework.md     # Plan 03 (cycle 1~3)
  ├─ 04_filter_refinement_integrated.md  # Plan 04 (cycle 1~8) — 본 master log
  └─ PLAN04_EXECUTIVE_SUMMARY.md         # 본 문서
```
