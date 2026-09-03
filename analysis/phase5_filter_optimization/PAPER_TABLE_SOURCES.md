# 논문 부록 표의 원본 대응 (2026-09-04)

`docs/PAPER/Supplementary/supplementary.tex` 의 `tab:modelfits`(§S11)와 `tab:fit_stability`(§S12)에 실린 값이 어느 파일의 어느 키에서 나왔는지 적는다. 표를 고칠 때 이 문서를 먼저 본다.

## 추정 경로를 하나로 고정한다

같은 "심리물리 원자 단독 적합" 이 **두 경로**로 존재하고 값이 갈린다. 논문 표는 **전자만** 쓴다.

| 경로 | 파일·키 | deutan | protan |
|---|---|---|---|
| **채택** — N=300 HC 5-train/2-test 재표집 **중앙값** | `results/s10_inclusion/s10b_v6_pca_rdm_results_sub-0{8,9}.json` → `summary[<combo>].per_model.2comp.param_summary.{bs_median,bc_median}` | (16°, −44°) | (26°, +4°) |
| 미채택 — 전체 7-HC 풀 **단일 적합** | `results/s10_inclusion/s18_heldout_predictive.json` → `candidates[].standalone_full_pool.gamma.fit` | (6°, −42°) | (26°, +4°) |

두 경로를 섞으면 deutan 에서 "심리물리 단독 = 결합 적합" 이라는 잘못된 대비가 만들어진다. 원고 본문(`results_v4.tex`, `The neural term relocates ...` 소절)과 `tab:fit_stability` 의 argmin 세 줄은 전부 재표집 중앙값 경로다.

## combo 키 이름

| 참가자 | 심리물리 단독 | ΔRDM 단독 | 선택 조합 | 차순위 조합 |
|---|---|---|---|---|
| deutan (sub-08) | `γOY\|RDM_\|noLOCO` | `γ_\|RDMV2\|noLOCO` | `γOY\|RDMV2\|noLOCO` | `γALL\|RDMV1\|noLOCO` |
| protan (sub-09) | `γALL\|RDM_\|noLOCO` | `γ_\|RDMV1\|noLOCO` | `γALL\|RDMV1\|noLOCO` | `γGB\|RDMV1\|noLOCO` |

SRM 기저 판은 같은 키를 `s10b_v6_srm_rdm_results_sub-0{8,9}.json` 에서 읽는다.

## `tab:modelfits` (§S11)

`per_model.2comp` 아래 `test_loss_median` 과 `test_loss_iqr`, 파라미터는 `param_summary.{bs_median,bc_median}` 이다.

| 행 | deutan | protan |
|---|---|---|
| 선택 조합 | (6°, −42°), L=−2.359, IQR 2.150 | (2°, +24°), L=−1.539, IQR 1.417 |
| 차순위 조합 | (38°, −10°), L=−1.137, IQR 0.857 | (2°, +24°), L=−1.519, IQR 1.412 |

**deutan 과 protan 의 차순위는 성격이 다르다.** deutan 의 차순위는 β_s 우세 대안이고, protan 에는 **β_s 우세이면서 게이트를 통과하는 후보가 존재하지 않는다.** sub-09 의 게이트 통과 RDM 조합은 전부 (2°, +24°) 로 수렴한다. β_s 우세 항목(`γALL|RDM_` (26°,+4°), `γGB|RDM_` (34°,−8°))은 RDM 원자가 없고, ROI 감사 파일의 `γALL|RDMV3`·`γALL|RDMV4` 는 `boundary_rate` 1.00·0.54 로 게이트 탈락이다. 표 캡션은 이 비대칭을 "next-ranked" 로 표현하고 β_s 우세라고 단정하지 않는다.

## `tab:fit_stability` (§S12)

| 표의 행 | 파일 | 키 | deutan | protan |
|---|---|---|---|---|
| 분리도 $d$ (V1/V2/V3/hV4) | `results/s10_inclusion/precondition_table.json` | `<ROI>.cohens_d.<sub>.L_RDM.d` (ROI 키 `V4` = hV4) | 2.31 / 1.937 / 0.857 / 2.188 | 0.805 / −0.233 / −0.476 / −0.238 |
| 격자 백분위 | `results/s10_inclusion/s19_allcandidate_heldout.json` | `rdm_pct_med` (s18 에서는 `heldout_loo.combined.summary.rdm_percentile_median`) | 0.04600 | 0.08069 |
| $\Delta\overline{L}$ 심리물리 항 · 폴드 | 같은 파일 | `gamma_dL_med`, `gamma_folds_beat00` | −13.846, 5/7 | +0.0108, 3/7 |
| $\Delta\overline{L}$ ΔRDM 항 · 폴드 | 같은 파일 | `rdm_dL_med`, `rdm_folds_beat00` | −0.4058, 7/7 | −0.4720, 7/7 |
| argmin 세 줄 | `s10b_v6_pca_rdm_results_sub-0{8,9}.json` | `param_summary.{bs_median,bc_median}` | (16,−44) / (4,−26) / (6,−42) | (26,+4) / (0,+24) / (2,+24) |
| argmin, SRM 기저 | `s10b_v6_srm_rdm_results_sub-0{8,9}.json` | 같음, 선택 조합 | (8°, −42°) | (32°, 0°) |
| 경계 포화율 | 같은 파일들 | `boundary_rate` | 0.230 → 0.093 | 0.000 → 0.000 |
| 파라미터 IQR, PCA | PCA 파일 | `param_summary.{bs_iqr,bc_iqr}` | (18,6) → (8,2) | (6,4) → (0,0) |
| 파라미터 IQR, SRM | SRM 파일 | 같음 | (18,6) → (10,4) | (6,4) → (0,2) |

## 표에 넣지 않은 것과 그 이유

**1,326 칸 중 정수 순위.** 파일에는 백분위만 저장되어 있다. 분모 1,326 을 곱하면 61 과 107 로 정확히 떨어지고 저장된 부동소수와 비트 단위로 일치하지만, 역산값이므로 표에는 백분위(4.6%, 8.1%)를 싣는다. 정수 순위를 쓰려면 격자 스크립트를 재실행해 확인한다.

**protan 의 ΔRDM 단독 적합에 붙은 `boundary: true`.** `s18_heldout_predictive.json` 의 `standalone_full_pool.rdm.fit.boundary` 가 참이고 재표집 경로의 `boundary_rate` 는 0.877 이다. 즉 protan 의 신경 단독 적합 (0°, +24°) 는 β_s 격자 하한에 붙어 있다. 표는 argmin 만 싣고 이 플래그를 싣지 않으므로, 이 값을 본문에서 해석하려면 함께 보고해야 한다.

**protan 의 "RDM 이 경계 포화를 줄였다" 서사.** PCA 기저에서 0.000 → 0.000 이라 줄일 것이 없고, SRM 기저에서는 0.000 → 0.130 으로 **악화한다**(`PIPELINE_2_CLOSURE.md` §RQ4(a) 에 `worsens` 로 기재). 원고는 이 서술을 deutan 에 한정한다.

**"seven folds" 의 범위.** 7/7 은 **ΔRDM 항**에 한정된다. 심리물리 항은 deutan 5/7, protan 3/7 이다. 원고 본문은 `the fitted distortion predicted the CVD representational geometry more closely` 로 적어 ΔRDM 항으로 범위가 한정되어 있다.

## 격자 크기

`scripts/two_comp.py:47-48` 의 `BS_GRID` 26점 × `BC_GRID` 51점 = **1,326 칸**. `docs/PAPER/repro/MANIFEST.md` E4.12 의 종전 기재(8,281 칸)는 2026-09-04 에 정정했다.
