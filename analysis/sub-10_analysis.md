# sub-10 재분석 — CVD signature 탐색 (exploratory)

_2026-06-28. `future_phase2_filter_optimization/CLAUDE.md` §A7/Rule 7 (sub-10 분석 제외)에 대한 **명시적 exploratory override**. production filter selection 불변경, supplementary 탐색 전용._

## 0. 질문

현재 paper(`docs/PAPER/`)는 sub-10을 "near-normal specificity control"로 보고 N=2 CVD(sub-08 deutan, sub-09 protan) case-study로 확정했다. 사용자 질문: **sub-10이 정말 sub-08/09처럼 CVD signature(LORO ok / LOCO fail / RDM deviate)를 안 보이는가? 안 보인다면 sub-10의 색약 특성은 무엇인가?**

가설→분석→실험→결과→가설수정 루프로 진행. 억지 유의성 추구 금지; sub-10이 정말 구별 신호가 없으면 그 자체가 valid 결론.

## 1. 데이터 / provenance

- fMRI amplitudes (local): `phase1_procrustes_decoding/results/visualization/full_dataset_C010_with_residuals/{sub}/{ROI}/amplitudes_procrustes.npy`, shape (6 runs, 8 colors, n_vox). ROI dir: hV4→V4.
- HC sub-01~07 (n=7), CVD sub-08/09/10. 8 등휘도 hue (R 0°…M 315°, 45° step), CIELab a*b* circle.
- **행동 데이터**: sub-10은 **JND·8AFC 미수집** (user-confirmed). 문서의 "sub-10 8AFC=0.88"은 **표기 오류**(repo에 raw 파일 없음).
- **Ishihara**: sub-10 "2/14" 의 정답/오답 규약이 문서 간 불일치(`results_v2`="misread"→경미 vs `methods_v2`="corrected" 규약). user도 헷갈림 → **본 분석은 Ishihara 해석에 의존하지 않음. 문서 미수정.**
- 재현 스크립트: `scratchpad/sub10/*.py` (battery, perpair, axis_test, loco, canon_loco, robust, magenta, perm, confound, voxel_repl2, sensitivity, voxel_allroi, geom, activation, act_robust, act_perm).

## 2. 가설-검정 로그 (차원별)

### 2.1 Geometry / RDM 차원

| # | 가설 | 검정 | sub-10 결과 |
|---|---|---|---|
| H1 | 전역 RDM magnitude 이상 | 10명 cross-val RDM mean | **null** (전 ROI \|z\|<1.1) |
| H2 | deutan red-green 축 압축 | per-pair 편차 vs a*-loading 연속상관 | **null** (전 ROI CH p>0.8) |
| H3 | 원형 hue 위상 약화 | neural RDM vs ideal circular | **null/불일치** (V1 z=−1.38, V4 z=+1.66) |
| G | RDM의 HC-평균 거리 (SRM-free) | 1−corr / Euclid vs HC | **null** (유일 흔적 V1 dcorr z=+1.85 p=0.07) |

**canonical SRM disparity** (project 지표, docs): sub-10 전 ROI HC 범위 (V1 p=.483, V2 p=.433, V3 p=.884, hV4 p=.945), V3/hV4는 오히려 HC보다 *덜* 떨어짐. 대조: sub-08 V2 p=.040*, sub-09 V1 p=.007*.

→ **geometry 차원: sub-10은 두 CVD가 보이는 국소 distortion이 없음 (가장 깨끗한 음성).** sub-08은 voxel RDM Euclid V2 p=.01* (HC-모양 유지 + 확대형); sub-10은 없음.

### 2.2 Interpolation / LOCO 차원 — 철회된 finding 포함

1. **Canonical SRM-aligned ForwardEncoding LOCO**: sub-10 V1 MAE z=+2.76 **p=0.021**, adj-acc z=−2.61 **p=0.025**; magenta 최악(170° vs HC 58°, 6 run 안정). supplementary 독립 결과(p=0.024) 재현. → 처음엔 유의해 보였음.

2. **Permutation 검증 (사용자 지적)**: json 1000-perm null 결과 — V1에서 **HC 7명 전원 chance 미달**(0/7 beat null), sub-10은 자기 셔플 null보다 *나쁨*(obs 108.5 vs null 78, p=0.97). LOCO 보간 신호는 **hV4에서만 해석가능**(group perm p≈0.044와 일치). → "sub-10 V1이 HC보다 나쁨"은 **아무도 신호 없는 영역의 noise 비교**. **finding 철회.**

3. **obs−null 재프레임**: 자기 chance 대비 편차로 보면 sub-09(+32.9)·sub-10(+30.6)만 HC([−16,+14])에서 outlier, voxel-수 confound 무관(r=0.23 ns, regression 후 p=0.039). → 살아남는 듯.

4. **SRM-artifact 결정 검정**: native Procrustes-voxel 공간(SRM 없음)에서 재계산 → **REVERSE**. sub-10 V1 obs−null=−41.5 (chance를 확실히 이김, perm p=0.002), HC와 차이 **p=0.197 (ns)**. voxel 공간에선 HC 7명 전원 chance를 이김(SRM 공간에선 전원 chance). → **SRM K=4 정렬이 V1 보간신호를 모두에게 파괴; sub-10 V1 "distortion"은 SRM 정렬 artifact. 완전 철회.**

5. **SRM-free voxel obs−null (전 ROI, 최종)**:

   | ROI | HC | sub-08 | sub-09 | sub-10 |
   |---|---|---|---|---|
   | V1 | −56.1 | −43.4 (ns) | −29.7 (p=.07) | −42.2 (ns) |
   | V2 | −43.4 | −28.0 (ns) | −30.4 (ns) | −3.4 (p=.10) |
   | V3 | −23.4 | −42.2 (ns) | −24.4 (ns) | −2.0 (ns) |
   | hV4 | −14.0 | −4.8 (ns) | +17.9 (ns) | −5.9 (ns) |

   → **깨끗한 voxel 공간에선 어떤 CVD도 어떤 ROI도 단일피험자 유의 없음.** 메타-발견: **프로젝트 CVD signature는 group-pooled + SRM-space 효과**; 단일피험자론 sub-08/09조차 voxel 공간 개별 유의 안 됨. "sub-10 개인이 보이나"는 프로젝트 기준 저파워.

6. **Sensitivity 시뮬**: sub-10 V1에 매끄러운 red-green 압축 주입 → LOCO obs−null이 **17°까지도 안 나빠짐**(detector가 매끄러운 압축에 둔감; 비매끄러운 회전형만 잡음). → LOCO null은 부분적으로 **detector 한계**.

### 2.3 Activation 차원

전역 (기존 + 본 분석): mean|β|, modulation depth, SNR, run-reliability — sub-10 전부 **HC 범위 내, ns** (대부분 약간 낮음, 비유의). 단변량 tuning(selectivity/sharpness/reliability)도 sub-10 정상~enhanced.

**색-분해 activation (신규 가설 A2)** — 색별 distinctiveness(mean-removed per-color energy):

> **V2에서 warm(R,O,Y,G) 색 distinctiveness가 cool(C,B,P,M) 대비 선택적으로 약화.**

| 검정 | 결과 |
|---|---|
| warm−cool contrast vs HC (energy) | z=−2.98, **p=0.02\*** |
| raw mean\|β\| 동일 contrast | z=−1.97, p=0.06 (trend), 같은 방향 |
| region 정의 robustness (R,O,G / O,Y,G / warm-cool) | 전부 유의 |
| **35개 4-4 색 split 중 위치** | **warm/cool = 최대 \|z\| (z=−4.15, 97th pctile)** |
| split-half 안정성 | 양쪽 half warm/cool ratio <1 (0.93, 0.83) |
| ROI 국재 | **V2 단독** (V1/V3/V4 비특이) |
| sub-08/09 대비 | 둘은 **반대 방향(warm 강화/+)** → sub-10 특이 |

**이론 정합**: warm = L/M-cone(red-green opponent) 구동, cool = S-cone(blue-yellow) 구동. warm 약화 + cool 보존 = **L-M(red-green) 색신호 결손** = deutan/protan 본질 축과 일치 → **CVD-consistent**. 또한 aggregate RDM-거리(§2.1 G)가 *놓친* 신호 → geometry 재탕 아닌 독립 차원.

## 3. 두-표현형 해석 (잠정, n=1 대비)

- **sub-08 = 보상형**: L-M 열화를 cortical over-gain(paper g>2)으로 증폭 → warm **강화**(z=+3.25). 여러 지표서 역설적 *우수*.
- **sub-10 = 미보상형**: raw L-M under-representation 노출 → warm **약화**(z=−2.98).

→ 같은 deutan이라도 보상 수준이 부호를 가른다는 가설. 단 2-사례 대비라 잠정.

## 4. 최종 종합

| 차원 | sub-10 |
|---|---|
| geometry (SRM disparity / RDM 거리) | **null** (전 ROI HC 범위; 두 CVD 중 가장 control-스러움) |
| interpolation (LOCO, voxel-space) | null (개별 ns — 단 sub-08/09도 단일피험자론 ns) |
| 전역/단변량 activation | null (HC 범위) |
| **색-분해 activation (warm/cool)** | **V2 시사적 signature (robust-within-V2)** |

**답**: sub-10은 두 CVD가 보이는 **interpolation·geometrical distortion을 유의하게 보이지 않는다**(단 단일피험자 LOCO는 sub-08/09도 마찬가지로 group-level에서만 나옴). 그러나 **"CVD 특성 전무"는 아니다** — **activation 차원에서 V2 warm-color(L-M축) distinctiveness 약화**라는 sub-10-특이·이론정합 신호가 robust하게 나온다.

## 5. Calibration / 한계 (반드시 동반)

1. V2 warm-suppression: **p=0.02 uncorrected**, 전체 ~14 분석 중 1셀, **V2 단독**(4 ROI 중). color-split permutation(97th)은 clean하나 ROI 선택은 미보정. → **"V2 내 robust한 시사 소견", definitive 아님.** 유의한 건 distinctiveness(energy); 순수 진폭은 trend(p=0.06).
2. **행동 cross-validation 불가** (sub-10 행동 데이터 없음). sub-08/09는 행동 검증됨; sub-10 지위는 **미결정(indeterminate)**, 2nd MRI/행동 수집 없이는 확정 불가.
3. **SRM-의존성 caveat (sub-10 너머)**: 단일피험자 CVD LOCO signature가 SRM 정렬에 의존함이 드러남 → paper의 sub-08/09 개별 ROI 주장(V2/V1 localized)에도 함의 가능. (행동 권고 아님, 인지 차원 기록.)
4. n=1, Ishihara 모호, detector(LOCO)는 압축형에 둔감.

## 6. 다음 단계 (현 데이터 상한 초과)

- sub-10 행동(JND 8쌍 + 8AFC) 수집 → activation signature 행동 cross-validation.
- 다른 ROI/voxel 선택(eccentricity-conditioned 등) 하 V2 warm-suppression 재현성.
- warm-suppression의 forward-model(L-M gain 파라미터) 정량화.
