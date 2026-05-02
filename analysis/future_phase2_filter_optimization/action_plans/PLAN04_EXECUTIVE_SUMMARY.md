# Plan 04 Filter Refinement — Executive Summary

> 생성: 2026-05-02 · Cycle 1~8 종합. Phase 3 (behavioral validation) 트리거 문서.

---

## 0. 한 줄 요약

CVD inverse filter 의 ROI/Loss 공통 selection rule 을 도출하여 sub-08(deutan) 에 robust specificity 를 확보했으나, sub-09(protan) 는 voxel-pattern level 에서만 회복되며 V1 결합 시 HC sub-04 와 통계적으로 분리되지 않음.

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

## 산출 파일 (Cycle 1~8)

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
  ├─ cycle8_voxel_bootstrap_server/{...}  ← Jobs 98931, 98945 결과 (PD)
  ├─ bootstrap_server/sub-{08,09}_{V1,V2,V4}.json (Cycle 6s n_boot=200)
  └─ cycle8_figures/{fig1_z_components,fig2_hc_fp_vs_cvd,fig3_preimage_hue,fig4_bootstrap_overlap}.png

action_plans/
  ├─ 01_loss_filter_redesign.md          # Plan 01 (cycle 1~4)
  ├─ 02_bootstrap_variance.md            # Plan 02 (cycle 1)
  ├─ 03_literature_math_framework.md     # Plan 03 (cycle 1~3)
  ├─ 04_filter_refinement_integrated.md  # Plan 04 (cycle 1~8) — 본 master log
  └─ PLAN04_EXECUTIVE_SUMMARY.md         # 본 문서
```
