# 전처리 민감도 정리 — exp1 / exp2 (2026-08-17)

> **수치의 single source of truth 는 `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md` 다.** 이 문서는 그 위에 얹는 **전처리 축 검정 기록**이며, 원고 반영안은 [`docs/PAPER/MANUSCRIPT_EDITS_CONSOLIDATED.md`](../docs/PAPER/MANUSCRIPT_EDITS_CONSOLIDATED.md) 에 있다.
>
> **exp1 과 exp2 는 성격이 다르므로 분리해 기록한다** (§0.2). 두 절을 같은 무게로 읽으면 안 된다.
>
> **위치**: `analysis/future_phase1_sensitivity/` — 산출은 `results/`, 그림은 `figures/`, arm 스크립트는 `scripts/`. `scripts/` 의 스크립트들은 `docs/PAPER/repro/_repro_util.py` 를 데이터 루트 정의로 계속 참조한다(경로 shim 포함).

---

## 0. 이 문서의 범위

### 0.1 고정된 선택

| 항목 | 고정값 | 근거 |
|---|---|---|
| mask variant | **`matched`** | 사용자 결정 2026-08-17. `native` 는 더 이상 산출·인용하지 않는다 |
| 재산출 종점 | **LOCO · LORO · disparity** | exp1 과 동일 구성 |
| 종점–ROI 배정 | **LOCO/LORO = hV4**, **disparity = 사전지정 결손 ROI** (deutan V2 · protan V1) | hV4 는 disparity 종점이 아니다 |

### 0.2 exp1 과 exp2 의 성격 차이 — 이 문서 구조의 근거

| | exp1 | exp2 |
|---|---|---|
| 무엇을 하는 실험인가 | **색각이상의 피질 표상 특징을 포착** | **exp1 에서 얻은 필터의 성능 평가** |
| 전처리 민감도의 의미 | **유의미하다.** 포착된 특징이 분석 선택의 산물인지 아닌지가 곧 주장의 성립 여부 | **제한적이다.** 평가 대상(필터)은 촬영 전에 이미 동결되었고, 그 필터의 타당성은 exp1 이 진다 |
| 이 문서에서의 취급 | **§2 본격 민감도 분석** | **§3 파이프라인 통일 기록 + 결론 불변 확인** |

**exp2 재전처리를 "민감도 분석" 으로 부르지 않는다.** 실행 동기는 외부 검토자가 지적한 **세션 간 디페이싱 비대칭 해소**였고, 종점 재산출은 통일 과정에서 무언가 깨지지 않았는지 확인하는 절차였다. 결과를 본 뒤 이를 민감도 근거로 승격시키는 것은 사후 목적 변경이다.

### 0.3 arm 정의

| arm | 무엇이 다른가 |
|---|---|
| `with_residuals` | **정본.** 발표된 파이프라인 |
| `motreg` | 움직임 회귀자 추가 (시간축) |
| `motshift` | 순환이동 대조 (`motreg` 부산물 해석 기각용) |
| `hmc_v2` | **머리움직임 재정렬**, 단일 보간 (공간축) |

`hmc_v2` 는 `mcflirt -mats` → `convert_xfm -concat` → 볼륨당 `applywarp` 1회. 구버전 `hmc`(= `mcflirt -out` 후 `applywarp`) 는 **보간 2회**이므로 폐기했고 인용하지 않는다.

---

## 1. 전체 판정 한 장

| 결과 | 전처리 축에서 |
|---|---|
| HC 연속 hue 보간은 hV4 단독 | **유지** — 4 arm 전부 통과, 다른 ROI 는 어느 arm 도 미통과 |
| hV4 지표 신뢰도 | **ICC(2,1) = 0.825** (V1 −0.005) — 신규 자산 |
| 8색 범주 식별 보존 | **유지** — 두 arm 전 ROI 에서 chance 1.8배 이상 |
| 필터 역산 8/8 exact | 불변 (수학) |
| 심리물리 전량 | 불변 (전처리 무관) |
| deutan 필터 $\hat\beta_c$ 부호 | **유지** — 시간·기저·공간 3축 전부 |
| CVD hV4 결손의 **유의성** | **유지 안 됨** |
| 개인별 ROI 편재 | **유지 안 됨** — deutan V2 방향 역전 |
| protan 필터 $\hat\beta_c$ 부호 | **유지 안 됨** — 3축 전부 반전 |

**핵심**: 무너진 것은 **개인 수준 통계적 주장**, 살아남은 것은 **집단 수준 구조 + 방법론**.

---

## 2. exp1 — 전처리 민감도 분석

### 2.1 HC 연속 hue 보간 게이트 (LOCO adjacent accuracy, 색 라벨 순열)

$n = 7$, 관측값 / 순열 $p$.

| arm | V1 | V2 | V3 | **hV4** |
|---|---|---|---|---|
| `with_residuals` | 0.393 / .164 | 0.357 / .424 | 0.339 / .586 | **0.456 / .011** |
| `motreg` | 0.333 / .624 | 0.292 / .924 | 0.393 / .143 | **0.458 / .013** |
| `motshift` | 0.375 / .272 | 0.408 / .112 | 0.402 / .124 | **0.483 / .002** |
| `hmc_v2` | 0.283 / .922 | 0.381 / .228 | 0.315 / .810 | **0.451 / .023** |

**hV4 만 네 arm 전부에서 통과하고, 나머지 ROI 는 어느 arm 에서도 통과하지 못한다.** 이것이 원고에서 hV4 를 유일한 해석 가능 영역으로 고정하는 근거이며, 전처리 축에 완전히 견딘다.

### 2.2 지표 신뢰도 — ICC(2,1), 정본 vs `hmc_v2`

| ROI | ICC(2,1) |
|---|---|
| **hV4** | **0.825** |
| V3 | 0.662 |
| V2 | 0.471 |
| V1 | $-0.005$ |

**§2.1 의 게이트 순서와 일치한다.** 게이트를 통과하는 유일한 ROI 가 전처리 재현성도 유일하게 높다. 현행 원고는 hV4 단독성을 색 라벨 순열 **하나로만** 정당화하는데, ICC 는 **두 번째 독립 축**에서 같은 결론을 준다 — 논문에 유리한 사실이므로 본문에 올린다.

### 2.3 CVD 개인 수준 — hV4 단일사례 (Crawford–Howell, 단측)

| arm | deutan | protan |
|---|---|---|
| `with_residuals` | 0.250 · $p$=.054 · $d_{cc}$=$-2.02$ | 0.125 · $p$=**.011** · $d_{cc}$=$-3.25$ |
| `motreg` | 0.271 · $p$=.148 · $-1.23$ | 0.312 · $p$=.204 · $-0.95$ |
| `motshift` | 0.375 · $p$=.229 · $-0.85$ | 0.229 · $p$=.056 · $-2.00$ |
| `hmc_v2` | 0.354 · $p$=.242 · $-0.80$ | 0.271 · $p$=.108 · $-1.48$ |

**방향은 네 arm 전부에서 보존된다**(두 CVD 모두 HC 평균 0.451–0.483 아래). **유의성은 정본 arm 에서만 성립한다.**

원인은 검정력이 아니라 **효과크기 축소**다($d_{cc}$ $-3.25 \to -1.48$). HC 를 무한히 늘려도 $p$ 는 .069 에서 멈춘다 — 현행 원고의 "단일사례 검정의 검정력" 설명은 **틀렸으므로 교체해야 한다**.

**검정 형태를 더 시도하지 않는다.** 여섯 형태를 시도했고 전부 같은 답이다.

| 형태 | 정본 | `hmc_v2` |
|---|---|---|
| Crawford–Howell 직접 | .011 | .108 |
| 개인 색라벨 순열 | HC 도 5/7 실패 → 구분 불가 | 〃 |
| 귀무 정규화 $z$ + CH | .021 | .101 |
| 원시 obs$-$null + CH | .013 | .101 |
| run-level bootstrap | arm 간 CI 겹침 17–29% | 〃 |
| 연속 MAE + CH | .011 | .454 |

귀무가 arm 간에 거의 움직이지 않으므로(0.339 → 0.353) 정규화가 흡수할 것이 없다. **더 시도하면 p-hacking 이다. 여섯 형태의 수렴 자체를 강건성 근거로 쓴다.**

### 2.4 disparity — 사전지정 결손 ROI

| | 정본 | `hmc_v2` | 판정 |
|---|---|---|---|
| **protan V1** | $p$ = .007 | $p$ = .077 | 약화, **방향 유지** |
| **deutan V2** | $p$ = .040 | $p$ = **.825** | **방향 역전** ($t$ $+2.1 \to -1.0$) |

**deutan V2 는 약화가 아니라 부호 반전이다.** 독립 분석(LORO 색대응, 2026-08-05)에서도 같은 반전이 나왔고($p$ = .882), protan V1 도 같은 값으로 약화됐다($p$ = .079). **서로 다른 두 교란이 같은 값으로 수렴한다.**

> **기여 2 는 영향받지 않는다.** 필터 표적 ROI 는 disparity 가 아니라 **held-out test-loss** 로 선정됐다(deutan V2 = 4-ROI 1위 $-2.359$; protan V1 은 하드코딩이나 gate 통과 ROI 전부 동일 해). 배포 필터 파라미터 불변. 다만 **disparity–필터 ROI 일치를 시사하는 서술은 삭제**해야 한다.

### 2.5 LORO 8-way 색 식별 (chance = 0.125)

| ROI | HC 정본 / hmc | deutan 정본 / hmc | protan 정본 / hmc |
|---|---|---|---|
| V1 | 0.571 / 0.515 | 0.562 / 0.229 | 0.562 / 0.521 |
| V2 | 0.574 / 0.512 | 0.521 / 0.521 | 0.562 / 0.333 |
| V3 | 0.589 / 0.560 | 0.375 / 0.479 | 0.458 / 0.500 |
| hV4 | 0.500 / 0.577 | 0.375 / 0.583 | 0.375 / 0.396 |

**최저 셀(deutan V1 hmc = 0.229)도 chance 의 1.8배다.** `All eight colors remained decodable` 는 두 arm 에서 유지된다.

*단서*: 발표 Figure 3A 는 SRM 공간 LORO 이고 위는 진폭 위 직접 계산이므로 정확 재현이 아니라 **구조적 확인**이다. 정성 주장은 두 계산 모두에서 성립한다.

### 2.6 필터 $\hat\beta_c$ 부호 — 3축 (판정 규칙 사전 확정)

`U2_BETA_SIGN_PRESPEC.md` §6: 주 판정 = $\hat\beta_c$ **부호**, 크기는 판정에 쓰지 않는다(2성분 모형 12/12 절대복구 실패 → descriptive embedding). $N=300$ 재표집.

| | baseline | motreg | hmc_v2 | 판정 |
|---|---|---|---|---|
| **deutan** | $-42$ | $-48$ | $-46$ | **부호 유지 3/3** ($P(\hat\beta_c<0) \ge 0.95$ 전부) |
| **protan** | $+24$ | $-24$ | $-12$ | **부호 반전 2/2** |

**protan 의 반전은 분산이 아니라 배타적이다.** baseline 은 300 중 263 이 $+24$, 나머지 37 이 $0$ — **음수가 없다.** motreg 은 218 이 $-24$, 82 가 $-34$ — **양수가 없다.** 두 arm 의 지지집합이 부호에서 겹치지 않는다.

**deutan 에 병기할 단서**: 부호는 유지되나 교란 arm 에서 조건수가 나빠진다. 결합 `boundary_rate` 가 $.09 \to .73 / .72$ 로 **정본 선택 규칙의 `boundary_rate < 0.5` 문턱을 넘는다.** 다만 edge 적중이 세 arm 전부 $-50$ 쪽 단측이고 $+50$ 은 0.00 이므로, 퇴화는 **크기에만** 있고 부호 주장을 훼손하지 않는다.

### 2.7 부수 검정 — SDC 미적용 정당화

전 9명 필드맵. ROI 커버리지 100%, header 정렬 정확, 정합 불량 0명. **ROI 내 미분 변위 0.05–0.38 복셀** → 미적용이 정량적으로 정당화된다. sub-07 은 왜곡이 아니라 **슬랩 커버리지 실패**(V1 330/858, hV4 16/70).

---

## 3. exp2 — 파이프라인 통일 기록

> **이 절은 민감도 분석이 아니다.** §0.2 참조.

### 3.1 왜 재전처리했는가

외부 검토 1차의 최우선 지적: **세션 1 은 ezBIDS 로 디페이싱되었고 세션 2 는 아니었다.** 코드 대조 결과 얼굴 유무가 파이프라인에 들어가는 지점이 두 곳으로 확인됐다.

```
run_method3_header_mi_2nd.sbatch:198   bet2 ${T1W_FILE}       ← 원본 T1w 위 뇌 추출
run_method3_header_mi_2nd.sbatch:371   fnirt --in=orig.mgz    ← 전체 머리가 moving image
```

정량 확인(sub-08 T1w, 0 복셀 비율): ses-1 **30.9%** vs ses-2 **13.1%**.

### 3.2 실행 기록

| Stage | 내용 | job | 결과 |
|---|---|---|---|
| A | 디페이싱 T1w 로 anat + transform 재계산 | 168215 | 완료, 각 ~5h. transform 10 / 피험자 |
| QC | `_2nd_harm` vs 기존 `_2nd` 정합 비교 | — | **통과** (§3.3) |
| B | 단일 보간 HMC, 2명 × 8런 | 168305 | 16/16, 볼륨수 292 전건 일치 |
| C | C010 진폭 | 168338 | sub × condition × ROI 정상 |
| D | 종점 재산출 | 168354 / 168358 | 완료 |

디페이싱 검증: 0 복셀 sub-08 **30.9%** · sub-09 **35.1%** (ses-1 30.9% / 33.0%). 중시상면 절단면 형상 4장 동일, 뇌 조직 손실 없음.

### 3.3 QC — 정합이 나빠지지 않았다

| arm | sub | 비영 복셀 | 뇌내 평균강도 |
|---|---|---|---|
| 기존 | 08 | 208,226 | 499.0 |
| **harm** | 08 | 206,536 | 505.8 |
| 기존 | 09 | 218,542 | 548.1 |
| **harm** | 09 | 217,820 | 551.4 |

전부 1–2% 이내. **육안(주 판정)**: 두 피험자 모두 슬랩이 후두엽·소뇌 위치에 정확히 얹혀 있고 기존 arm 과 위치·기울기가 사실상 동일. 공백·시각피질 외 침범 없음.

→ 사전 확정된 승격 조건(*디페이싱 후 정합이 나빠지면 공통 해부 기준으로 승격*)은 **발동하지 않았다.**

**개선도 악화도 아니다. 절차적 일치 수정이지 품질 향상이 아니다.**

### 3.4 종점 재산출 — 결론 불변 확인 (`matched`)

**LOCO adjacent accuracy @ hV4**

| | HC $n{=}4$ | NoFilter | Window | Optimal |
|---|---|---|---|---|
| deutan 정본 | 0.456 | 0.231 | 0.250 | 0.312 |
| deutan harm | 0.445 | 0.342 | 0.156 | 0.281 |
| protan 정본 | 0.456 | 0.138 | 0.188 | 0.062 |
| protan harm | 0.445 | 0.263 | 0.281 | 0.406 |

**LORO FE-6 @ hV4**

| | HC | NoFilter | Window | Optimal |
|---|---|---|---|---|
| deutan 정본 | 0.656 | 0.521 | 0.406 | 0.406 |
| deutan harm | 0.587 | 0.708 | 0.438 | 0.469 |
| protan 정본 | 0.656 | 0.458 | 0.562 | 0.438 |
| protan harm | 0.587 | 0.542 | 0.469 | 0.625 |

**disparity @ 사전지정 결손 ROI** (낮을수록 HC 기하에 근접)

| | HC | NoFilter | Window | Optimal |
|---|---|---|---|---|
| deutan **V2** 정본 | 0.443 | 0.676 | 0.870 | 0.766 |
| deutan **V2** harm | 0.491 | 0.498 | 0.683 | 0.570 |
| protan **V1** 정본 | 0.429 | 0.700 | 0.657 | 0.626 |
| protan **V1** harm | 0.481 | 0.602 | 0.503 | 0.442 |

**판정: 파이프라인 통일이 어떤 결론도 바꾸지 않는다 — 바꿀 결론이 없기 때문이다.** 현행 원고는 exp2 신경 종점에서 이미 방향 주장을 하지 않는다(초록: *The direction of cortical change differed across participants and measures, and neither reached the healthy reference*). 재산출 결과도 같은 상태다.

모든 CVD 조건이 HC 보다 나쁘다(disparity 단측 $p$ 전부 .99 대) — `neither reached the healthy reference` 그대로다.

### 3.5 왜 이것을 민감도 근거로 쓰지 않는가

**첫째, 목적이 다르다.** 실행 동기는 디페이싱 비대칭 해소였다. 결과를 본 뒤 민감도 근거로 승격시키는 것은 사후 목적 변경이다.

**둘째, 바뀌는 주장이 없다.** 원고가 exp2 신경 종점에서 방향 주장을 하지 않으므로 "전처리에 따라서도 흔들린다" 를 추가해도 지탱되는 것이 없다.

**셋째, 평가 대상이 이미 동결되어 있다.** exp2 는 촬영 전에 동결된 **특정 필터**를 시험한다. 그 필터의 타당성은 exp1 이 지며, exp1 에서 protan $\hat\beta_c$ 가 3축 전부에서 뒤집힌다는 사실은 **exp2 를 어떻게 전처리하든 달라지지 않는다.** exp2 민감도는 프레임워크를 구제할 수 없다.

**넷째, 그럼에도 기록은 남긴다.** 리뷰어가 "세션 2 를 통일했는데 수치가 바뀌었나" 라고 물으면 답할 수 있어야 한다. **한 문장 분량이지 한 절 분량이 아니다.**

> **참고 (본문 미사용)**: 사전지정 결손 ROI 의 disparity 는 arm 간 이동이 런 표집 SD 의 1.0–15.8배로, 런 잡음이 아니라 **체계적 오프셋**이다(6칸 중 5칸이 harm 쪽에서 일제히 낮아짐). 따라서 **절대값은 arm 의존적이고 arm 내 순서만 의미가 있다.** 이 관찰은 어떤 주장도 지탱하지 않으므로 원고에 넣지 않는다.

---

## 4. 원고 반영

문안은 [`docs/PAPER/MANUSCRIPT_EDITS_CONSOLIDATED.md`](../docs/PAPER/MANUSCRIPT_EDITS_CONSOLIDATED.md) 에 있다. 이 문서와의 대응:

| 이 문서 | 원고 |
|---|---|
| §2.1–2.2 | Results `:38` 뒤 강건성 단서 · §S2 표 |
| §2.3 | Results `:40` — "검정력" 설명 교체 |
| §2.4 | Results `:56` `:60` `:66` · Discussion `:33` `:60` `:69` · Fig 4 별표 제거 |
| §2.6 | §S16 신설 (3-arm) |
| §2.7 | §S2 SDC 문단 |
| §3 | §S2 **한 문단** — 통일했고 결론이 바뀌지 않았다 |

**§3 을 절로 키우지 않는다.**

---

## 5. 산출물

| 대상 | 경로 |
|---|---|
| exp1 4-arm 종점 · ICC · MAE 순열 · bootstrap | `results/{perm_adjacent_arm_*,arm_agreement,perm_mae_arm,boot_runs_*}.json` |
| exp1 disparity arm | `analysis/validation/results/disparity_arm_{canonical,hmc_v2}.json` |
| exp1 HMC 품질 | `analysis/phase0_preprocessing/results/{hmc_summary.csv,hmc_roi_comparison.json}` |
| **HMC ROI 겹침 그림** | `figures/hmc_full/` |
| **SDC 코호트 QC 그림** | `figures/sdc_cohort/` |
| **sub-07 커버리지 진단 그림** | `figures/coverage_diag/` |
| **arm 스크립트** | `scripts/{_perm_adjacent_arm,_arm_agreement,_boot_runs_arm,_perm_mae_arm,_fig_delta_loco}.py` |
| $\hat\beta_c$ 3축 | `analysis/phase5_filter_optimization/results/{filter_robustness_arms/beta_sign_three_arms.json, s10_inclusion/u2_{baseline,motreg,hmc_v2}/}` |
| SDC 정량 | `analysis/phase0_preprocessing/results/roi_shift_summary.csv` |
| exp2 진폭 | `derivatives/full_dataset_C010_exp2_harm_hmc_matched` |
| exp2 종점 | `analysis/phase6_behavioral_analysis/exp2_neural/results/exp2_{hc_likeness,runmatched_geometry}_sub-0{8,9}_matched_harmhmc.json` |
| exp2 arm 비교 | `results/{exp2_endpoints_arms,exp2_disparity_arms}.json` |

**재현 훅**: `COLORBLIND_AMP_ROOT`(필터 적합) · `COLORBLIND_HC_C010` / `COLORBLIND_EXP2_C010` / `COLORBLIND_ARM_TAG`(exp2 종점). 모두 기본값이 발표 경로이므로 기존 재현 경로는 불변이다.
