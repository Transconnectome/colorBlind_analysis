# TODO — Additional analyses triggered by Introduction revision

> 서론 개정 중 인용 검증에서 파생된 추가 분석 기록. 각 항목 = 배경 / 과정 / 결과 / 포인터.
> 결과 수치의 single source of truth는 여전히 `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md`.
> 여기 확정된 항목은 그쪽으로 승격할 것.

---

## A1. JND 측정 노이즈 바닥 대비 필터 효과 (patterson2022 기준)

**상태**: 분석 완료 (2026-08-03) · 논문 반영 미정

### 배경

서론 ¶3에서 기존 필터의 한계를 `patterson2022`로 인용하기로 하면서 발생한 자기검증 의무.

Patterson et al. (2022, *Opt. Express* 30:31186)은 상용 CVD 필터의 효과를 **측정 자체의 재검사 변동과 비교**해 판정했다. 51명 red–green CVD에서 CAD 역치 평균 감소는 EnChroma 1.16 units, VINO 8.03 units로 **둘 다 통계적으로 유의(p<0.001)** 했으나, baseline 간 차이의 SD가 1.91이었다. 즉 EnChroma의 효과는 측정 노이즈에 미달(0.61×)하여 "functionally meaningful"하지 않다고 판정됐고, VINO만 통과(4.2×)했다.

서론에서 이 기준으로 선행 필터를 평가하면, 리뷰어는 당연히 **우리 필터에 같은 기준을 적용**한다. 그 답을 우리가 먼저 갖고 있어야 한다.

### 과정

우리 JND 과제는 색쌍마다 **독립 스테어케이스 2개**(start level 0.8 / 0.5)를 돌리고 그 평균을 역치로 쓴다(`analyze_exp2_behavior.py:jnd_per_pair`). 두 스테어케이스의 불일치 `|sc0 − sc1|`은 **필터 효과와 같은 JND 단위의 측정 노이즈**이므로, patterson2022과 동일한 형태의 비교가 가능하다.

1. HC sub-01~07 baseline에서 색쌍별 `|sc0 − sc1|` → 참조 노이즈 바닥
2. CVD sub-08/09의 baseline · window · optimal 세 조건에서 각각 동일 계산 → 조건 pooled 바닥
3. `|baseline − optimal|`, `|baseline − window|` 평균과 바닥의 비율, 바닥 초과 색쌍 수

### 결과

| | 노이즈 바닥 `mean\|Δsc\|` | \|baseline − optimal\| | 비율 | 바닥 초과 |
|---|---|---|---|---|
| HC (n=7) 참조 | 0.0254 (median 0.0150) | — | — | — |
| **sub-08** (deutan) | 0.0226 | 0.1375 | **6.09×** | 6/8 |
| **sub-09** (protan) | 0.0382 | 0.0566 | **1.48×** | 3/8 |

window 조건: sub-08 6.83× (6/8), sub-09 1.28× (4/8).

조건별 바닥 분해:

| | baseline | window | optimal |
|---|---|---|---|
| sub-08 | 0.0150 | 0.0265 | 0.0263 |
| sub-09 | 0.0156 | 0.0177 | **0.0813** |

**해석**

- **sub-08은 patterson2022 기준을 여유 있게 통과**한다. 6.09×는 그 논문에서 유일하게 통과한 VINO(4.2×)보다 크다.
- **sub-09은 1.48×로 미묘**하다. 다만 sub-09은 baseline이 이미 HC 수준이므로(`behavioral_summary_exp1_exp2.md` §1: mean |z| 0.90, CH 유의 색쌍 0개) **변화가 작은 것이 목표**다. 우월성이 아니라 **동등성(equivalence) 논리**로 평가해야 하며, 이 표의 비율은 sub-09에 대해서는 적합한 검정이 아니다.
- **미해결**: sub-09 **optimal 조건의 스테어케이스 불일치가 0.0813으로 baseline(0.0156)의 5.2배**. 이 조건에서 역치 추정이 불안정했다는 뜻이다. 원인 규명 전에는 sub-09 optimal에 대한 어떤 정량 주장도 보류. → **A2로 이관**.

**한계 (반드시 병기)**

`|sc0 − sc1|`은 **같은 세션 내** 스테어케이스 간 불일치다. patterson2022의 재검사 SD는 **세션 간** 변동이라 세션 간 표류를 포함한다. 우리 값은 그 성분이 빠져 있어 **낙관적 상한**이며, like-for-like 재현이 아니다. HC·CVD 모두 JND 반복 세션 데이터가 없어 진짜 재검사 변동은 현재 추정 불가.

### 포인터

- 코드: `analysis/future_phase3_behavioral_analysis/scripts/jnd_noise_floor.py`
- 결과: `analysis/future_phase3_behavioral_analysis/results/exp2_behavior/jnd_noise_floor.json`
- 입력: `data/behavior/sub-0{1..9}_jnd_ses1_no_filter_summary.csv`, `data/behavior/2nd_exp/{sid}/jnd_ses2_run{1,2}_*_summary.csv`
- 맥락: `analysis/future_phase3_behavioral_analysis/results/exp2_behavior/behavioral_summary_exp1_exp2.md`
- 실행: `conda activate srm && python scripts/jnd_noise_floor.py`

### 논문 반영 판단 (미결)

- Results 또는 Supplementary에 넣을지 미정. sub-08 결과는 강점이나, sub-09 A2가 풀리기 전에는 세트로 보고하기 어렵다.
- 넣는다면 **한계 문단을 같은 자리에 병기**할 것 (within-session 바닥이라는 점).

---

## A2. sub-09 optimal 조건 스테어케이스 불안정

**상태**: 미착수

### 배경

A1에서 발견. sub-09의 optimal 조건에서만 두 스테어케이스의 역치 추정이 크게 갈린다(`mean|Δsc|` 0.0813 vs baseline 0.0156, window 0.0177 — 5.2배). sub-08에서는 조건 간 이런 격차가 없다(0.0150 / 0.0265 / 0.0263).

### 확인할 것

1. 어느 색쌍에서 벌어지는가 — 전역인가 특정 쌍인가
2. `n_reversals`, `n_trials`가 해당 쌍에서 정상인가 (스테어케이스 미수렴 여부)
3. start level(0.8 vs 0.5) 의존성 — 한쪽 스테어케이스만 튀는가
4. sub-09 optimal 필터가 특정 쌍에서 자극을 렌더 범위(gamut) 밖으로 밀어냈을 가능성
5. 세션 내 블록 순서(sub-09: window run-1 → optimal run-2) 피로 효과

### 왜 중요한가

sub-09은 exp2에서 **preservation** 논리를 담당한다(`behavioral_summary_exp1_exp2.md` §2). 그 조건의 측정이 불안정하면 "optimal이 HC 수준을 보존한다"는 진술의 근거가 약해진다. 4번이 원인이라면 필터 구현 문제이므로 Methods 수정 사안이 된다.

### 포인터

- 입력: `data/behavior/2nd_exp/sub-09/jnd_ses2_run2_optimal_sub-09_summary.csv` (`staircase_id`, `start_level`, `jnd_mean`, `jnd_std`, `n_reversals`, `n_trials`)
- trial 단위: `data/behavior/*_trials.csv`
- 필터 생성: `analysis/future_phase2_filter_optimization/`

---

## A3. 서론 인용 범위 교정 — somers2024

**상태**: ¶3 적용 시 반영 예정

### 배경

somers2024를 "필터는 appearance를 바꾸지만 threshold discrimination은 못 바꾼다"의 근거로 쓰려 했으나, 두 가지 문제가 있다.

1. **저자 결론과 방향이 어긋남.** somers2024의 헤드라인은 "the **first quantitative experimental evidence that notch filters can enhance** color perception for anomalous trichromats"이다. 세부 결과는 해리(gamut·appearance 유의, threshold minimal)이지 실패가 아니다. 교신저자 Bosten은 우리가 ¶1·¶2에서 인용하는 `bosten2019`의 저자이기도 하다.
2. **우리 Results와 충돌.** 서론이 "필터는 역치를 못 바꾼다"고 일반화하면, Results에서 **배포 중인 macOS Window 필터가 sub-08의 역치를 정상화**했다는 보고(mean |z| 2.24 → 0.85)와 모순된다.

### 조치

- 주어를 `The filters` → **`Notch lenses`**로 한정. somers2024가 실제 시험한 대상(EnChroma 분광 notch 렌즈)에 맞추고, 자극공간 변환인 우리 필터·macOS 필터와 구분한다.
- 결과 서술도 저자 표현을 그대로 사용: `minimal change`(somers2024 원문 단어).

### 관련 확인 (완료)

우리 필터에서 이 해리는 **재현되지 않는다**. sub-08 threshold JND가 실제로 이동했다(mean |z| 2.24 → optimal 0.78, CH 유의 결핍 3쌍 모두 정상화). 다만 window도 동등(0.85)이므로 역치 개선은 우리 필터 고유 속성이 아니다.

### 포인터

- 문헌: `docs/Prior_works/by_section/introduction/introduction_prevFilters_somers2024.pdf`
- 우리 결과: `analysis/future_phase3_behavioral_analysis/results/exp2_behavior/behavioral_summary_exp1_exp2.md` §2

---

## A4. 신규 확보 문헌 — 하드웨어 필터 원리

**상태**: 문헌 확보·노트북 등록 완료 / bib 항목 추가 필요

### 배경

기존 ¶3의 하드웨어 필터 서술("dichroic notch lenses ... amplify the residual red–green signal")에 **인용이 없었다**. 원리 근거 문헌을 탐색했다.

### 확보

| citekey | 논문 | 역할 |
|---|---|---|
| `alvaro2022` | Álvaro, Linhares, Formankiewicz & Waugh (2022) *Sci Rep* 12:11140 | notch 필터 원리 정의 — "reshape M and/or L cone spectra to increase differences between peak spectral energies" |
| `gomezrobledo2018` | Gómez-Robledo et al. (2018) *Opt Express* 26(22):28693 | EnChroma Cx 분광 투과율 실측 — 3개 valley, 그중 594 nm |
| `male2022` | Male, Shamanna, Bhagvati & Theagarayan (2022) *Health Sci Rep* 5:e842 | CVD 기기 체계적 문헌고찰·메타분석 (예비, 미인용) |

Schmeder & McPherson (2019)는 논문이 아니라 **US Patent 10,338,286**이다(somers2024도 특허로 인용). 동료심사 근거가 필요하면 위 문헌으로 대체.

### 채택하지 않은 논증

`gomezrobledo2018`은 "notch 위치가 정상 원추 피크 기준이라 피크가 이동한 개인에게는 겹침 구간과 어긋난다"고 명시한다. 기전적으로 매력적이나 **서론에서 이 논증은 쓰지 않기로 했다** — 이 논증이 유도하는 결론은 "개인의 원추 피크를 측정해 notch를 맞추면 된다"는 **순수 망막적 해법**이고, ¶4가 인용하는 `deeb2005`·`stockman2000`이 그 측정이 정확히 가능하다고 말한다. 우리 논지는 "망막이 개인마다 다르다"가 아니라 "**망막 모델은 피질 재조직을 담지 못한다**"이므로, 이 문단이 다음 문단을 무너뜨리는 구조가 된다. 따라서 `gomezrobledo2018`은 **"정상 망막 기준으로 절삭됐다"는 서술 근거로만** 사용한다.

### 포인터

- PDF: `docs/Prior_works/by_section/introduction/introduction_prevFilters_{alvaro2022,gomezrobledo2018,male2022}.pdf`
- NotebookLM `ColorBlind_comprehensive` 3건 등록 완료
- TODO: `docs/PAPER/bibliography.bib`에 `alvaro2022`, `gomezrobledo2018` 항목 추가
- TODO: `docs/Prior_works/by_section/MANIFEST.md` 갱신 (인용 확정 후)

---

## A5. 서론 인용 정확성 교정 — neitz2011

**상태**: ¶1 적용 완료 (2026-08-03)

### 배경

¶1이 `neitz2011`을 4회 인용했다. 리뷰 논문 반복 인용이 과하다는 판단으로 원 출처를 추적했다(로컬 PDF 전문 + NotebookLM 교차확인).

### 발견

| 주장 | 원 인용 | 판정 |
|---|---|---|
| X-linked 다형성이 shift의 원인 | deeb2005, neitz2011 | ✅ 타당 (원 연구 Nathans et al. 1986) |
| shift 크기의 연속적 개인차 | neitz2011 | ✅ 타당 (원 연구 Merbs & Nathans 1992a/b, Asenjo 1994) |
| 이상삼색형 **2–12 nm** / 정상 **25 nm** | neitz2011 | ❌ **neitz2011 본문에 없음** |
| protan=L·deutan=M 광색소 이동 | neitz2011 | ❌ **neitz2011이 'classic view'로 지목하고 반박하는 서술** |

- "2–12 nm"는 `emery2021`이 neitz2011을 인용하며 만든 요약값이다(연쇄 인용). 직접 측정을 추적한 논문들은 하한을 **1**로 쓴다(boehm2014, somers2024, robinson2022, basim2025).
- 정상값은 소스마다 25/27/30으로 갈린다 — in vitro 색소 피크(≈30) vs cone fundamentals(≈25–27)의 기준 차이.
- neitz2011의 현대적 서술: protanomaly = **M-class 색소 2개**, deuteranomaly = **L-class 색소 2개**. 심각도는 같은 class 내 두 색소의 분광 차이가 결정.

### 조치 (적용됨)

- 수치 문장 인용을 `somers2024`로 교체, 값을 **1–12 nm** / **27 nm** (같은 논문 같은 기준)
- 아형 문장을 "어느 색소가 이동하는가"에서 "**이동의 방향**"으로 전환 — neitz2011 현대적 서술 및 basim2025와 정합
- 연속 변이 인용을 `bosten2019`로
- `neitz2011` 인용 **4회 → 2회**, 남은 2회는 모두 이 논문 고유 기여

### 포인터

- 적용: `docs/PAPER/Introduction/introduction_v2.tex` ¶1 (L55–56)
- 문헌: `docs/Prior_works/by_section/introduction/introduction_cvdGenetics_neitz2011.pdf`, `..._cvdPhenotype_bosten2019.pdf`
- 교차확인: NotebookLM `ColorBlind_comprehensive` conversation `2bd060b9-d9b1-42c4-bfa6-0b3ed4af220d`

---

## A7. Neural-only 피팅 ablation — "신경 데이터가 행동 지표의 보조에 불과한가"

**상태**: **이미 분석·논문 반영 완료** (s18, 2026-06-02). 본 항목은 **독립 재현 + 신규 부수 발견 2건**.

### 배경

예상 비판: *"production loss가 행동(γ, JND)항과 신경(RDM)항의 합인데, 신경항을 빼도 같은 해가 나온다면 신경 데이터는 보조 장식일 뿐이다."*

성립하면 Contribution 2("개인 **자신의 피질 색 표상**에서 역산한 필터")의 근거가 무너진다.

### 선행 분석 (기확보) — `s18_heldout_predictive`

**이 질문은 2026-06-02에 이미 다뤄졌고 Results·Discussion에 반영돼 있다.**

전 pool standalone fit (`results/s10_inclusion/s18_INTERPRETATION.md` Q2):

| | combined (production) | γ-only (행동) | RDM-only (신경) |
|---|---|---|---|
| S08-robust (deutan) | (6, −42) | **(6, −42)** | (4, −26) |
| S09-primary (protan) | (2, +24) | (26, +4) | **(0, +24)** |

held-out 7-fold 예측 성능 (Q1, vs 무보정 (0,0) 기준):

| | RDM ΔL vs (0,0) | (0,0) 이기는 fold | grid 백분위 | γ ΔL |
|---|---|---|---|---|
| S08 | **−0.406** | **7/7** | 0.05 | −13.8 (5/7) |
| S09 | **−0.472** | **7/7** | 0.08 | +0.01 (3/7) ≈ null |

**결론(선행)**: 신경 RDM항은 **두 피험자 모두 7/7 held-out fold에서 무보정을 이긴다.** S08은 행동·신경이 β_c<0로 **독립 수렴(triangulation)**, S09는 production이 **사실상 RDM-only 해**이고 행동항은 held-out 신호가 없다(γ ΔL=+0.01).

논문 반영 확인:
- `Results/results_v4.tex`: "The protan participant's behavioral-only fit yielded β̂_c ≈ +4° and did not beat the no-correction baseline (ΔL = +0.01, 3/7 folds). The RDM term captures a signal that the behavioral loss cannot resolve." / "The behavioral-only and combined fits share the same argmin (6°, −42°)"
- `Discussion/discussion_v3.tex`: 동일 취지 서술 존재

### 독립 재현 (본 항목에서 수행)

다른 추정량으로 재현했다. s18은 **전 pool 단일 fit**, 본 분석은 **5/2 HC split × N=300 resample의 중앙값**이다. 재피팅 없이 production 산출물에서 추출했다(`enumerate_combos_*`가 γ 없는 조합을 이미 포함).

원자 결합 규칙 (`s10b_v6_pca_rdm.py` ~L570): `comp = Σ zscore_grid(atom) / sqrt(n_atoms)` — 전 원자 **동일 가중**. 행동항을 우대하는 자유 가중치는 없다.

채택 조합, 축별:

| 피험자 | 축 | neural-only | behav-only | joint(채택) | 주도항 |
|---|---|---|---|---|---|
| **sub-08** | β_s | 4 | 16 | **6** | neural |
| | β_c | −26 | −44 | **−42** | behavioral |
| **sub-09** | β_s | 0 | 26 | **2** | neural |
| | β_c | 24 | 4 | **24** | neural |

**부호 4/4 일치.** 신경 데이터만으로 두 성분의 방향이 모두 독립 복원된다. 어긋나는 것은 sub-08 β_c의 크기뿐(신경 −26 → 결합 −42). s18의 정성적 결론과 일치한다.

### 신규 발견 1 — 추정량에 따른 수치 차이 (논문 문장 관련)

`Results/results_v4.tex`는 "the behavioral-only and combined fits **share the same argmin** (6°, −42°)"라고 쓴다. 이는 **전 pool 추정량에서만 성립**한다. resample-median 추정량에서는 행동-only가 **(16, −44)**로 결합해 (6, −42)와 β_s가 10° 다르다.

정성적 주장(양쪽 모두 β_c를 강하게 음수로 둔다)은 두 추정량에서 모두 성립하므로 **오류는 아니다.** 다만 "same argmin"이라는 표현은 추정량 특정적이므로, 리뷰어가 리샘플로 재계산하면 다른 수치를 얻는다. → **문장 완화 권고**: "share the same argmin" → "place β_c at the same value (−42°)" 또는 추정량 명시.

### 신규 발견 2 — neural-only 해의 ROI 의존성 (sub-08)

s18은 채택 ROI만 보고한다. 전 ROI를 보면 sub-08의 neural-only 해가 수렴하지 않는다.

| ROI | neural-only (β_s, β_c) | boundary |
|---|---|---|
| V1 | (32, 0) | 0% |
| V2 **(채택)** | (4, −26) | — |
| V3 | **(0, 0)** | 61% |
| V4 | (36, −14) | 30% |
| V1+V4 | (36, −26) | — |

β_c는 V1에서 0, V3에서 0으로 나온다. **채택 ROI(V2)를 벗어나면 신경-only가 confusion-축 성분을 지지하지 않는다.** ROI 선택이 결과를 좌우한다는 뜻이므로, ROI 선택 근거(deutan V2 / protan V1은 왜곡 ROI로 사전 지정)를 Methods에서 명확히 해두어야 방어된다.

### 부수 확인 — LOCO 원자 축퇴

| | LOCO 포함 조합 | boundary 비율 median |
|---|---|---|
| sub-08 | 36 | **1.00** |
| sub-09 | 6 | **0.98** |

거의 모든 조합에서 argmin이 그리드 모서리(대개 β_s = 50)에 붙는다. 내부 최적해를 만들지 못한다. 폴더 CLAUDE.md §2.5의 "LOCO_V4 = precondition gate 전용" 정책을 정량적으로 뒷받침한다.

### 조치 (미결)

1. `Results/results_v4.tex`의 "share the same argmin" 표현 완화 (신규 발견 1)
2. ROI 사전 지정 근거를 Methods에 명시 (신규 발견 2)
3. LOCO 축퇴 수치를 Supplementary에 넣을지 — 현재 "gate 전용"이라고만 서술

### 포인터

- 선행 분석: `analysis/future_phase2_filter_optimization/results/s10_inclusion/s18_INTERPRETATION.md`, `s18_heldout_predictive.{md,json}`, 코드 `scripts/s18_heldout_predictive.py`
- 본 재현 코드: `analysis/future_phase2_filter_optimization/scripts/neural_only_ablation.py`
- 본 재현 결과: `.../results/s10_inclusion/neural_only_ablation.json`
- 피팅 코드: `.../scripts/s10b_v6_pca_rdm.py` (원자 L74–214, 결합 L556–585), 그리드 `.../scripts/two_comp.py` L47–48
- 채택 조합 출처: `docs/PAPER/Results/results_v4.tex`, 폴더 `CLAUDE.md` §3
- 실행: `conda activate srm && python scripts/neural_only_ablation.py`

---

## A6. 저널 분량 기준 확인

**상태**: 확인 완료 · NeuroImage 기준 진행 결정 (2026-08-03)

### 확인 내용

| 저널 | Introduction 규정 |
|---|---|
| **NeuroImage** | **규정 없음** (Abstract ≤250 words, Commentary <2000, Technical Note ~3000만 규정) |
| **J. Neurosci.** | **650 words 상한** (Discussion 1,500) |

코퍼스 실측이 이를 뒷받침한다 — J. Neurosci. 게재 논문 Introduction: brouwer2009 686, bannert2025 664, bannert2018 631, brouwer2013 525. Vision Research / J Vis 계열은 1181–1417.

### 현재 상태

Introduction 본문 **1150 words** (¶1·¶2 개정 반영 전 기준). Vision Research 중앙값(1181) 부근, NeuroImage 무제한.

**결정**: NeuroImage 기준으로 진행. J. Neurosci.가 실질 후보가 되면 별도 **650 압축 패스** 필요 (현재의 약 1.8배).

### 포인터

- 저널 가이드: NeuroImage `sciencedirect.com/journal/neuroimage/publish/guide-for-authors`, J. Neurosci. `jneurosci.org/content/information-authors`
- 관련 메모리: `project_target_journal.md` (1차 eLife, aspirational Nat Comms, safe J. Neurosci.) — **NeuroImage 추가로 갱신 필요**

---

## A8. 전처리·정규화 보고 완결성 감사 (COBIDAS 대조)

**상태**: 감사 완료 · **파이프라인 확정됨 (2026-08-03, 사용자 확인)** · 나머지 누락 항목 기입 대기

### 배경

"MNI space에 대한 구체적 정보(config 포함)가 뇌영상 논문에 보통 제시되는데 누락 여부 점검" 요청. 관행을 인상으로 판단하지 않기 위해 **OHBM COBIDAS 보고 표준**(Nichols et al. 2017, *Nat Neurosci* 20:299–303; 전문 체크리스트 = OHBM COBIDAS Report v1.0, 2016/5/19)을 기준으로 삼았다.

COBIDAS `Intersubject registration` 항목 원문 요구사항:

> ● Name of software/method (e.g., FSL flirt followed by fnirt, FreeSurfer, ...)
> ● Whether volume and/or surface based registration is used
> ● Image types registered (e.g. T2* or T1)
> ● Any preprocessing to images
> ● **Template space ..., modality ..., resolution ..., and the specific name of template image used**
> ● Choice of warp (rigid, nonlinear); **if nonlinear, transformation type** (e.g., B-splines ...); if a parametric transformation is used, **report resolution, e.g., 10x10x10 spline control points**
> ● **Use of regularization, and the parameter(s) used**
> ● **Interpolation type**

### 과정

COBIDAS PDF 전문을 받아 `Intersubject registration` / `Motion correction` / `Spatial smoothing` / `Quality control reports` / `Distortion correction` / `Essential sequence & imaging parameters` / MVPA(`Features extraction and dimension reduction`, `Variable dimension`) 항목을 추출한 뒤, `Methods/methods_v2.tex` §MRI acquisition and preprocessing + §ROI definition + `Supplementary/supplementary.tex`와 대조했다.

### 결과 — 보고되고 있는 항목

| COBIDAS 항목 | 우리 기술 | 위치 |
|---|---|---|
| Scanner vendor/model/coil | Siemens 3T MAGNETOM Cima.X, BioMatrix 3T coils | methods §MRI |
| TR / TE / FA / voxel / matrix / slices | 1.5 s / 30 ms / 75° / 2×2×2 mm / 96×80 / 24 oblique | methods §MRI |
| Coregistration 방법 + cost function | FreeSurfer `mri_coreg`, mutual information | methods §MRI, suppl S11 |
| Warp 종류 (affine + nonlinear) | 12-DOF FLIRT → FNIRT | methods §MRI |
| 출력 해상도 | 2 mm isotropic | methods §MRI |
| ROI atlas + 임계값 + voxel 수 | Wang 2015, >50%, BOLD mask 교집합, 평균±SD | methods §ROI |
| **MVPA: 차원 축소 전/후 voxel 수** | 선택 전 (V1 655±214 …) / 후 (V1 328±107 …) | methods §ROI ✅ COBIDAS 명시 요구 충족 |
| Confound / temporal filtering 정책 | "No temporal filtering or confound regression"; per-run linear drift regressor | suppl S1 |
| 자극 소프트웨어 버전 | PsychoPy 2022.2.5 | methods §stimuli |

### 결과 — 누락 항목

**★★ 최우선: 파이프라인 기술 불일치**

| | 저장소 기록 | Methods 본문 |
|---|---|---|
| 기반 도구 | **fMRIPrep 23.2.3** (`analysis/METHODS_phase1_baseline.md` L16) | 언급 없음 |
| Deoblique | **AFNI `3dWarp`, quintic interpolation** (`docs/PREPROCESSING_METHOD_UPDATE_2025-12-18.md` §6.3) | 언급 없음 |
| 정규화 | `--output-spaces MNI152NLin2009cAsym:res-2` (동 문서 L345) | "12-DOF affine (FSL FLIRT) → FNIRT" |

fMRIPrep은 정규화에 ANTs를 쓰지 FLIRT/FNIRT를 쓰지 않는다. 즉 Methods 본문이 기술하는 경로와 저장소가 기록한 경로가 **서로 다른 파이프라인**이다. 전처리 문서에는 fMRIPrep BBR 정합 실패 → header-MI 커스텀 경로 전환 이력이 있어(`run_method3_header_mi_all_subjects.sbatch`), 최종 채택본이 커스텀 경로일 가능성이 높다. **어느 쪽이 최종인지 저자 확인이 필요하며, 확정 전에는 나머지 누락 항목을 채울 수 없다.**

**★ 사용자가 지목한 항목: 템플릿 구체 정보**

Methods는 "MNI"라고만 쓴다. COBIDAS는 **specific name + modality + resolution**을 요구한다. 값은 저장소에 이미 있다 — `MNI152NLin2009cAsym`, `res-2` (`analysis/README.md` L57, `analysis/METHODS_phase1_baseline.md` L28, 템플릿 파일 `analysis/phase0_preprocessing/templates/MNI152NLin2009cAsym_res-2_brain_mask.nii.gz`). **기입만 하면 되는 누락.**

**그 외 누락**

| # | 누락 항목 | COBIDAS 근거 | 자료 보유 여부 |
|---|---|---|---|
| 1 | **Motion correction 전체** — 소프트웨어, 참조 볼륨, 변환형, 유사도 척도, interpolation | `Motion correction` 필수(Y) | MCFLIRT 사용 확인 (`phase0_preprocessing/scripts/generate_confounds_mcflirt.py`). **본문에 한 줄도 없음** |
| 2 | Slice timing correction 수행 여부 | `Slice timing` | 미확인 |
| 3 | Distortion correction / fieldmap | `Distortion correction` 필수(Y) | fieldmap(magnitude1/2, phasediff) 존재 언급 있음 (전처리 문서 L324) |
| 4 | Spatial smoothing 수행 여부 | `Spatial smoothing` | MVPA라 미적용 추정 — **"적용하지 않았다"는 진술이 필요** |
| 5 | 비선형 warp 변환형 + 제어점 해상도 | `Choice of warp` | FNIRT 기본값(cubic B-spline, warp res 10 mm) 명시 필요 |
| 6 | 정규화 regularization 파라미터 | `Use of regularization` | FNIRT bending energy 기본값 |
| 7 | Interpolation type (정합·정규화 각각) | `Interpolation type` | deoblique는 quintic 기록 있음, 나머지 미기재 |
| 8 | 소프트웨어 버전 — FSL, FreeSurfer, AFNI, ezBIDS(, fMRIPrep) | `Software version` | PsychoPy만 버전 기재됨 |
| 9 | run당 볼륨 수 | `Number of volumes` 필수(Y) | "≈7 min, TR 1.5 s"에서 유도 가능하나 미기재 |
| 10 | T1w 획득 파라미터 전체 | `Essential sequence & imaging parameters` | 본문에 해부 스캔 기술 자체가 없음 |
| 11 | Phase-encoding 방향 / multiband factor / partial Fourier | `Imaging type` | 미기재 (2 mm EPI 왜곡 해석에 필요) |
| 12 | Motion QC 요약 (mean FD 등) | `Quality control reports` | **데이터 보유** — `future_phase3_behavioral_analysis/exp2_neural/preproc_qc/`, tSNR 값 산출됨 |
| 13 | 분석 유형 라벨 ("Representational Similarity Analysis", "Multivariate intra-subject predictive") | `Analysis type` 필수(Y) | 내용은 있으나 COBIDAS 표준 명칭 미사용 |
| 14 | 템플릿 구체명 (위 ★) | `Intersubject registration` | 저장소 보유 |

### 해석

누락 14건 중 **10건은 저장소에 값이 이미 있고 기입만 하면 되는 항목**이다(템플릿명, MCFLIRT, deoblique, QC, 버전 등). 실제 위험은 두 가지다.

1. **파이프라인 정체성 불일치** — Methods가 실제 수행한 것과 다른 절차를 기술하고 있을 수 있다. 재현성 심사에서 가장 먼저 걸리는 유형이고, fMRIPrep 사용 여부는 Methods 한 문단을 통째로 바꾼다.
2. **Motion correction 완전 누락** — 어떤 fMRI 심사자도 넘어가지 않는 항목이다. confound 미회귀 정책(suppl S1)은 이미 서술돼 있으므로, "MCFLIRT로 정합했으나 motion regressor는 회귀하지 않았다"는 두 진술을 함께 놓아야 한다. 지금은 앞의 절반이 없다.

### 조치 (미결)

1. **저자 확인**: 최종 파이프라인이 (a) fMRIPrep 23.2.3 기반인지 (b) AFNI deoblique + 커스텀 header-MI + FLIRT/FNIRT인지 확정
2. 확정 후 §MRI acquisition and preprocessing 재작성 — 위 표 14항목 반영
3. `analysis/METHODS_phase1_baseline.md`의 fMRIPrep 버전 기재가 stale이면 정정
4. Motion QC 요약값(mean FD 등)을 `preproc_qc/`에서 산출해 Supplementary 표로

### 포인터

- 기준: OHBM COBIDAS Report v1.0 (2016/5/19) `https://www.humanbrainmapping.org/files/2016/COBIDASreport.pdf`; 요약 논문 Nichols et al. 2017 *Nat Neurosci* 20:299–303
- 대조 대상: `docs/PAPER/Methods/methods_v2.tex` §MRI acquisition and preprocessing(L67–73), §ROI definition(L76–86); `docs/PAPER/Supplementary/supplementary.tex` S1, S11
- 저장소 기록: `analysis/METHODS_phase1_baseline.md` L14–33; `docs/PREPROCESSING_METHOD_UPDATE_2025-12-18.md` §6.3, §7.3, L324, L345
- 전처리 코드: `analysis/phase0_preprocessing/scripts/` (`generate_confounds_mcflirt.py`, `run_method3_header_mi_all_subjects.sbatch`)
- QC 자료: `analysis/future_phase3_behavioral_analysis/exp2_neural/preproc_qc/`, `preproc_qc_exp1/`
- 템플릿 파일: `analysis/phase0_preprocessing/templates/MNI152NLin2009cAsym_res-2_brain_mask.nii.gz`

### ✅ 파이프라인 확정 (2026-08-03, 사용자 확인)

**정본 = `analysis/phase0_preprocessing/scripts/run_method3_header_mi_2nd.sbatch`** (exp2)
**exp1 대응본 = `run_method3_header_mi_all_subjects.sbatch`** — 두 스크립트를 diff한 결과 **입출력 경로·코호트·run 수(6 vs 8)를 제외하면 절차가 동일**하다. 즉 두 세션에 같은 전처리가 적용됐다.

**⚠️ fMRIPrep은 사용되지 않았다.** 출력 디렉토리 이름이 `fmriprep_out_method3_*`이지만 내용은 FreeSurfer + FSL 커스텀 파이프라인이다. `analysis/METHODS_phase1_baseline.md` L16의 "fMRIPrep: version 23.2.3" 기재는 **stale이므로 정정 대상**이다. Methods 본문의 FLIRT/FNIRT 기술이 실제와 맞는 쪽이었다.

#### 확정된 절차 (스크립트 라인 기준)

| 단계 | 도구 · 파라미터 | 스크립트 |
|---|---|---|
| 해부 영상 | T1w `acq-mprage` (MPRAGE) | L156 |
| Brain extraction | FSL `bet2 -f 0.5 -m` (우선), 폴백 FreeSurfer `mri_watershed -useSRAS` | L196–204 |
| BOLD 참조 볼륨 | **중간 볼륨** (`NVOLS/2`) | L242 |
| BOLD → T1w | FreeSurfer `mri_coreg --regheader` — 헤더 qform/sform 초기화 후 **mutual information, Powell 최적화**. **BBR 생략** (2 mm 해상도에서 MI로 충분하다는 판단) | L264–269, L18–20 |
| BOLD → T1w 적용(중간) | `mri_vol2vol --interp trilin` (중간 산출물, 최종 경로에서는 미사용·삭제) | L282–288, L295 |
| T1w → MNI 선형 | FSL `flirt -dof 12 -bins 256 -cost corratio -searchrx/ry/rz -90 90` | L337–347 |
| T1w → MNI 비선형 | FSL `fnirt --config=T1_2_MNI152_2mm.cnf`, `--refmask=MNI152NLin2009cAsym_res-2_brain_mask`. **입력은 full-head T1w(`orig.mgz`), ref도 full-head 템플릿** | L364–384 |
| LTA → FSL 변환 | `tkregister2 --fslregout` | L439–445 |
| 합성 변환 적용 | `applywarp --premat=<bold→T1w> --warp=<FNIRT cout> --interp=trilinear` — **BOLD 원본에서 MNI로 한 번에 리샘플** | L452–458 |
| Brain mask | `fslmaths -Tmean -bin` (폴백 `3dAutomask` / `mri_binarize`) | L466–494 |

#### 템플릿 (COBIDAS 요구 충족용 확정값)

- **Space/name**: `MNI152NLin2009cAsym`
- **Resolution**: `res-2` (2 mm isotropic)
- **Modality**: T1w
- **Dimensions**: 97 × 115 × 97 — 스크립트가 FSL 기본 `MNI152_T1_2mm`(91×109×97 계열)와 **다른 공간임을 명시적으로 경고**하고 있다 (L314–317)
- 파일: `templates/MNI152NLin2009cAsym_res-2_T1_brain.nii.gz` (brain), `..._T1.nii.gz` (head), `..._brain_mask.nii.gz` (refmask)
- 로컬 사본: `analysis/phase0_preprocessing/templates/MNI152NLin2009cAsym_res-2_brain_mask.nii.gz`

> **주의**: `--config=T1_2_MNI152_2mm.cnf`는 FSL 표준 설정이며 내부적으로 `--ref`/`--refmask`가 FSL의 MNI152_T1_2mm을 가리킨다. 스크립트는 명령행에서 둘 다 2009cAsym으로 **덮어쓴다**(FNIRT는 명령행 우선). 다만 config의 `--subsamp/--infwhm/--reffwhm/--lambda` 스케줄은 FSL 템플릿 기준으로 튜닝된 값이므로, 그대로 2009cAsym에 적용했다는 점을 Methods에 명시하는 편이 안전하다.

#### 수행하지 않은 단계 (모두 명시적 보고 필요)

| 단계 | 상태 | 근거 |
|---|---|---|
| **Motion realignment** | **미수행** | 스크립트 어디에도 realign 단계가 없다. BOLD 원본이 `applywarp`로 직행한다. MCFLIRT는 **별도**로 confound 산출용으로만 실행("Next steps: Generate confounds (mcflirt)", L538), 그리고 `METHODS_phase1_baseline.md`에 따르면 그 confound는 **회귀하지 않았다**. 즉 **모션 보정이 데이터에 적용되지 않았다.** |
| Slice timing correction | 미수행 | 스크립트에 없음 |
| Distortion correction (fieldmap) | **미수행 (의도적)** | "Fieldmaps present in bids_2nd are **IGNORED** (same as 1st-dataset pipeline, keeps registration method identical across sessions)" — L29–30 |
| Spatial smoothing | 미수행 | 스크립트에 없음 (MVPA이므로 타당하나 진술 필요) |
| BBR refinement | **의도적 생략** | "BBR refinement: SKIP (MI sufficient for fMRI 2mm resolution)" — L20 |
| AFNI deoblique | **본 스크립트에는 없음** | exp1 입력이 `bids_editted`, exp2가 `bids_2nd`. `PREPROCESSING_METHOD_UPDATE_2025-12-18.md`가 기술한 AFNI `3dWarp` quintic deoblique는 **BIDS 생성 단계에서 상류 적용**된 것으로 보인다. → **확인 필요 (아래 잔여 항목 1)** |

#### 보간(interpolation) — COBIDAS 필수 항목

- BOLD → T1w 중간 적용: `trilin` (`mri_vol2vol`)
- **최종 BOLD → MNI: `trilinear`** (`applywarp --interp=trilinear`) ← 실제 분석 데이터에 적용된 값
- deoblique(상류, 해당 시): `3dWarp` **quintic**

### 잔여 확인 항목 (파이프라인 확정 후 남은 것)

1. **AFNI deoblique 적용 범위** — `bids_editted`(exp1)·`bids_2nd`(exp2) 생성 시 각각 적용됐는지. exp2에만 미적용이면 두 세션 간 전처리 동일성 주장이 깨진다.
2. **FNIRT config 실제 파라미터** — 서버 `/usr/local/fsl/etc/flirtsch/T1_2_MNI152_2mm.cnf`에서 `--warpres`, `--lambda`, `--regmod`, `--intorder`, `--subsamp`를 읽어 기입. COBIDAS가 warp 제어점 해상도와 regularization 파라미터를 명시 요구. (로컬에 FSL 미설치 → 서버 확인 필요)
3. **소프트웨어 버전** — FreeSurfer(스크립트가 7.2.0 / 7.4.1 경로를 탐색), FSL, AFNI, ezBIDS 실제 사용 버전을 서버 로그에서 확정
4. **run당 볼륨 수** — 스크립트가 `3dinfo -nv`로 읽는 값. 로그에서 추출 가능
5. **T1w 획득 파라미터** — MPRAGE TR/TE/TI/FA/voxel. BIDS JSON sidecar에서 추출
6. **PE 방향 / multiband / partial Fourier** — BOLD JSON sidecar에서 추출
7. **Motion QC 요약** — `preproc_qc/`에서 mean FD 등 산출 (모션 보정 미적용이므로 **더욱 중요**)
8. `analysis/METHODS_phase1_baseline.md` L16 "fMRIPrep: version 23.2.3" 삭제·정정

### 재평가 — 심각도 조정

파이프라인 확정으로 A8의 위험도가 바뀌었다.

- **해소**: "파이프라인 기술 불일치"는 **Methods 본문이 옳고 저장소 메모가 stale**한 경우였다. 본문 재작성 불필요, `METHODS_phase1_baseline.md` 정정으로 충분.
- **격상**: **모션 보정 미수행**이 새로운 최우선 항목이다. 단순 누락이 아니라 **방법론적 선택**이며, 심사에서 반드시 질문받는다. 현재 Methods·Supplementary 어디에도 진술이 없다. Supplementary S1의 "no confound regression"과 짝을 이루어 "정합·회귀 모두 미적용"을 명시하고, 근거(RSVP 과제, 짧은 run, 후두엽 국한 ROI, 그리고 `METHODS_phase1_baseline.md`가 기록한 "motion/tissue/WM regression degrades signal by −60%")를 함께 제시해야 한다.
- **격상**: **fieldmap 의도적 무시**도 진술 필요. 2 mm EPI·후두엽에서 왜곡은 실재하며, "세션 간 정합 방법을 동일하게 유지하기 위해" 무시했다는 근거가 스크립트 주석에 있으므로 그대로 쓰면 된다.

### ✅ 서버 조회 완료 (2026-08-03, node1) — 잔여 항목 확정값

exp1·exp2 동일 방법 확정(사용자). `haba6030@node1`에서 직접 확인.

#### 획득 파라미터 (BIDS sidecar, `bids_editted/sub-01`)

**BOLD** (`sub-01_task-rsvp_run-1_bold.json`)

| 항목 | 값 |
|---|---|
| Manufacturer / Model / Field | Siemens / MAGNETOM Cima.X / 3 T |
| Software | syngo MR XA61 |
| ScanningSequence / Variant | `EP` / `SK\OSP` |
| TR / TE / FA | 1.5 s / 30 ms / 75° |
| Slice thickness / spacing | 2 mm / 2 mm (**gap 없음**) |
| In-plane parallel imaging | `ParallelReductionFactorInPlane = 2` (GRAPPA/iPAT 2) |
| Multiband | **없음** (sidecar에 키 부재) |
| Partial Fourier | `1` (full) |
| **Phase-encoding 방향** | **`i`** |
| EffectiveEchoSpacing / TotalReadoutTime | 0.39156 ms / 37.20 ms |
| SliceTiming | 24개 값, 0–1.4175 s (**sidecar에 존재 — 보정은 미적용**) |
| Coil | `HeadNeck_64_CS` |
| AcquisitionMatrixPE / ReconMatrixPE | 80 / 96 |
| **Run당 볼륨 수** | **288–292** (exp1 로그), **292** (exp2 로그) |

**T1w** (`sub-01_acq-mprage_T1w.json`) — 현재 Methods에 **기술 자체가 없음**

| 항목 | 값 |
|---|---|
| ScanningSequence / Variant | `GR\IR` / `SK\SP\MP` (MPRAGE) |
| TR / TE / TI / FA | 2.0 s / 1.99 ms / 0.9 s / 8° |
| Slice thickness | 1 mm |

#### 소프트웨어 버전 (로그에서 확정)

| 도구 | 버전 | 확인 |
|---|---|---|
| FreeSurfer | **7.2.0** | 로그 `✅ FreeSurfer found: /usr/local/freesurfer/7.2.0/bin/mri_convert` (exp1 `method3_82158_9.out`, exp2 `method3_2nd_118436_2.out` 모두 동일) |
| FSL | **6.0.5.1** (`57b01774`) | `/usr/local/fsl/etc/fslversion` |

> 노드에 FreeSurfer 7.2.0 / 7.3.2 / 7.4.1이 공존하나, 스크립트 탐색 순서상 **7.2.0**이 선택됐음을 두 세션 로그가 확인.

#### FNIRT 설정값 — `/usr/local/fsl/etc/flirtsch/T1_2_MNI152_2mm.cnf` (COBIDAS 필수 항목)

| 파라미터 | 값 | COBIDAS 대응 |
|---|---|---|
| `--warpres` | **10, 10, 10 mm** | "if a parametric transformation is used, report resolution, e.g., 10x10x10 spline control points" |
| `--regmod` | **`bending_energy`** | "Use of regularization" |
| `--lambda` | **300, 150, 100, 50, 40, 30** | regularization 파라미터 |
| `--ssqlambda` | 1 (lambda를 현재 ssq로 가중) | |
| `--subsamp` | 4, 4, 2, 2, 1, 1 | multi-resolution 스케줄 |
| `--miter` | 5, 5, 5, 5, 5, 10 | |
| `--infwhm` / `--reffwhm` | 8,6,5,4.5,3,2 / 8,6,5,4,2,0 mm | |
| `--intmod` / `--intorder` | `global_non_linear_with_bias` / 5 | intensity mapping |
| `--biasres` / `--biaslambda` | 50,50,50 / 10000 | |

config 내부 `--ref=MNI152_T1_2mm`, `--refmask=MNI152_T1_2mm_brain_mask_dil`은 **명령행 인자로 2009cAsym 템플릿·마스크가 덮어씀**(FNIRT는 명령행 우선). 즉 스케줄만 FSL 표준을 따르고 대상 공간은 2009cAsym이다 — Methods에 이 점을 명시할 것.

#### ⚠️ 발견 1 — AFNI deoblique는 최종 파이프라인에 **미적용**

nibabel affine으로 직접 계산한 obliquity:

| 파일 | obliquity |
|---|---|
| `bids_editted/sub-01/func/..._run-1_bold.nii.gz` (exp1 입력) | **26.34°** |
| `bids_2nd/sub-08/func/..._run-1_bold.nii.gz` (exp2 입력) | **41.59°** |
| `fmriprep_out_method3_header_mi/sub-01/func/..._space-MNI152NLin2009cAsym_res-2_...` (출력) | 0.00° |

입력 BOLD가 여전히 oblique하다. **`PREPROCESSING_METHOD_UPDATE_2025-12-18.md` §6.3이 제안한 AFNI `3dWarp` quintic deoblique는 폐기된 fMRIPrep 경로의 것이며, 최종 Method 3에는 들어가지 않았다.** Method 3의 설계 의도 자체가 "MI robust to obliquity"로 deoblique를 대체하는 것이다(스크립트 L23).

→ **Methods에 AFNI 3dWarp를 쓰면 사실과 다르다.** 대신 "oblique prescription을 유지한 채 헤더 초기화 + MI 정합으로 처리했다"고 써야 한다. 앞선 A8 초안에서 deoblique를 누락 항목으로 올린 것은 **철회**한다.

#### ⚠️ 발견 2 — 모션 추정치가 존재하지 않음 (confounds 파일이 placeholder)

`fmriprep_out_method3_header_mi/sub-{01..10}/func/*_desc-confounds_timeseries.tsv`는 10명 × 6 run 모두 존재하나, 내용이 비정상이다.

`sub-01_task-rsvp_run-1`:

| 열 | 값 |
|---|---|
| trans_x / trans_y / trans_z | 207.612 / 290.263 / 54.041 — **288 볼륨 전부 동일, SD = 0** |
| rot_x / rot_y / rot_z | 114.862 / 0.278 / −179.131 — **전부 동일, SD = 0** |
| framewise_displacement | **288/288 전부 0.0** |

값의 크기(수백 mm, ±180°)로 보아 이는 모션 추정치가 아니라 **NIfTI 헤더의 원점/방향 값이 전 볼륨에 복제된 것**이다. `generate_confounds_mcflirt.py`가 실제 MCFLIRT `.par`를 찾지 못하고 헤더 값을 기록한 것으로 보인다(실제 `.par` 파일은 폐기된 `fmriprep_work_ants_test/`의 sub-06 것만 존재).

**따라서**:
- 최종 파이프라인에는 모션 **보정도, 추정도** 없다. (앞서 "보정 미수행"으로 적었으나 실상은 추정조차 없다.)
- **mean FD를 기존 산출물에서 보고할 수 없다.** COBIDAS `Quality control reports` 충족하려면 원본 BOLD에 MCFLIRT를 새로 돌려야 한다.
- `analysis/METHODS_phase1_baseline.md`의 "Confounds: None (motion/tissue/WM regression degrades signal by −60%)" — 이 −60% 비교가 **어느 confounds 파일로 수행됐는지 확인 필요**. 위 placeholder였다면 비교 자체가 무의미하고, `fmriprep_out_new/`(구 fMRIPrep 실 산출물)였다면 최종 파이프라인이 아닌 데이터에 대한 결과다. 어느 쪽이든 논문에 근거로 쓰기 전에 재확인해야 한다.

### 갱신된 잔여 항목

| # | 항목 | 상태 |
|---|---|---|
| 1 | AFNI deoblique 적용 범위 | ✅ **해소 — 미적용 확정.** Methods에서 언급하지 말 것 |
| 2 | FNIRT config 파라미터 | ✅ **해소 — 위 표** |
| 3 | 소프트웨어 버전 | ✅ **해소 — FreeSurfer 7.2.0, FSL 6.0.5.1** |
| 4 | run당 볼륨 수 | ✅ **해소 — 288–292 (exp1), 292 (exp2)** |
| 5 | T1w 획득 파라미터 | ✅ **해소 — 위 표** |
| 6 | PE 방향 / multiband / partial Fourier | ✅ **해소 — PE `i`, multiband 없음, PF 1, iPAT 2** |
| 7 | Motion QC (mean FD) | ❌ **산출 불가 — MCFLIRT 재실행 필요** (발견 2) |
| 8 | `METHODS_phase1_baseline.md` fMRIPrep 기재 정정 | 미조치 |
| **9 (신규)** | "confound 회귀 시 −60%" 근거 데이터 재확인 | 미조치 (발견 2) |

### 조회 명령 기록 (재현용)

```
ssh haba6030@node1
cat /usr/local/fsl/etc/flirtsch/T1_2_MNI152_2mm.cnf      # FNIRT 설정
cat /usr/local/fsl/etc/fslversion                         # FSL 6.0.5.1
ls /scratch/connectome/haba6030/colorBlind/analysis/prep_trials/logs/method3_*.out
#   -> "FreeSurfer found", "Extracting volume N from M volumes"
python3 -c "import nibabel,numpy; ..."                    # obliquity = affine 열벡터 vs cardinal 축 최대각
```

### ⚠️ 발견 2 정정 (2026-08-03) — 모션 추정치는 **존재한다**

앞의 "발견 2 — 모션 추정치가 존재하지 않음"은 **틀렸다.** `find ... -name "*.par" | head -5` 출력이 폐기 디렉토리(`fmriprep_work_ants_test/`) 항목으로 채워진 것을 보고 성급히 결론냈다. 실제로는 method3 산출물 안에 MCFLIRT 파라미터가 있다.

```
/storage/connectome/haba6030/fmriprep_out_method3_header_mi/sub-XX/func/
    sub-XX_task-rsvp_run-N_desc-motion.par     ← 10 subj × 6 run 전부 존재
```

#### mean FD (Power et al. 2012, 회전 반경 50 mm)

| subject | mean FD (mm) | worst run |
|---|---|---|
| sub-01 | 0.354 | 0.403 |
| sub-02 | 0.243 | 0.302 |
| sub-03 | 0.320 | 0.368 |
| sub-04 | 0.276 | 0.334 |
| sub-05 | 0.379 | 0.448 |
| sub-06 | 0.303 | 0.354 |
| sub-07 | 0.313 | 0.350 |
| **sub-08** (deutan) | **0.384** | 0.492 |
| **sub-09** (protan) | **0.292** | 0.370 |
| sub-10 (제외) | 0.321 | 0.392 |

| 그룹 | n | mean FD |
|---|---|---|
| 전체 | 10 | **0.319 ± 0.042 mm** (범위 0.243–0.384) |
| HC (sub-01~07) | 7 | **0.313 ± 0.042 mm** |
| CVD (sub-08, 09) | 2 | **0.338 mm** |

**→ COBIDAS `Quality control reports` 항목을 지금 채울 수 있다.** MCFLIRT 재실행 불필요.

#### 여전히 유효한 사실

1. **모션 보정은 데이터에 적용되지 않았다.** 파이프라인에 realign 단계가 없고 원본 BOLD가 `applywarp`로 직행한다. `.par`는 별도 산출된 추정치일 뿐이다. → "모션을 추정했으나 보정·회귀 모두 하지 않았다"가 정확한 서술이다.
2. **confounds TSV는 손상돼 있다.** `*_desc-confounds_timeseries.tsv`의 trans/rot 6열이 전 볼륨 상수(헤더 원점·방향 값), `framewise_displacement` 전부 0. `.par`가 멀쩡하므로 TSV 생성 단계의 버그다. **confound를 회귀하지 않았으므로 결과에는 영향이 없으나, 이 TSV를 근거로 아무것도 계산하면 안 된다.**
3. **exp2에는 `.par`가 없다** (`fmriprep_out_method3_2nd`에서 0개). exp1만 모션 추정치를 갖는다. exp2 QC를 보고하려면 2nd 세션 BOLD에 MCFLIRT를 돌려야 한다.

#### 추가 발견 — `qc/`의 조직 마스크 통계가 "confound 미회귀" 결정을 정당화한다

`qc/sub-XX/sub-XX_run-N_mask_stats.json` (60개 파일):

| 지표 | 평균 | 범위 |
|---|---|---|
| `csf_coverage` | **0.0036** (0.36 %) | 0.0000–0.0068 |
| `n_csf_voxels` | **8.1개** | **0–15개** |
| `wm_coverage` | 0.127 | 0.030–0.319 |

FOV가 후두엽 24 슬라이스로 한정되어 **CSF 복셀이 run당 0–15개**에 불과하다. 이 표본으로 만든 aCompCor 성분은 신호가 아니라 잡음이다. `analysis/METHODS_phase1_baseline.md`의 "motion/tissue/WM regression degrades signal by −60%"라는 관찰에 **기전적 근거가 생겼다** — 근거 없는 선택이 아니라 FOV 제약의 필연적 귀결로 서술할 수 있다.

→ 잔여 항목 9("−60% 근거 데이터 재확인")의 우선순위는 낮아졌다. 어느 파일로 쟀든, CSF 8복셀로는 조직 기반 회귀가 성립하지 않는다는 것이 독립적으로 확인된다.

#### 잔여 항목 재갱신

| # | 항목 | 상태 |
|---|---|---|
| 7 | Motion QC (mean FD) | ✅ **해소 — exp1 0.319 ± 0.042 mm** (위 표). exp2는 미산출 |
| 9 | "−60%" 근거 | 🔽 **강등** — CSF 8복셀 사실로 결정 자체는 정당화됨 |
| **10 (신규)** | exp2 모션 추정 (`.par` 부재) | 필요 시 2nd 세션 MCFLIRT 실행 |
| **11 (신규)** | confounds TSV 손상 | 결과 무영향(미사용). 재생성 여부는 선택 |

### ✅ FNIRT 실행 로그 확보 (2026-08-03) — .cnf 인용보다 강한 1차 증거

`fmriprep_work_method3{,_2nd}_sub-XX/sub-XX_T1w_head_to_MNI152NLin2009cAsym_res-2_T1.log`

FNIRT가 **실제 사용한 해결된 파라미터 전체**를 피험자마다 기록해 둔 파일이다. 존재 확인: **exp1 sub-01~10 전원 ✅, exp2 sub-08·09 ✅**.

`.cnf` 파일을 인용하는 대신 이 로그를 근거로 쓰면 (a) 명령행 덮어쓰기가 실제로 적용됐음이 증명되고, (b) 피험자별 동일성이 직접 확인된다.

#### 로그가 확정하는 값

| 파라미터 | 값 | 비고 |
|---|---|---|
| `--ref` | `MNI152NLin2009cAsym_res-2_T1.nii.gz` | **config의 FSL MNI152_T1_2mm이 아님 — 덮어쓰기 성공 확인** |
| `--refmask` | `MNI152NLin2009cAsym_res-2_brain_mask.nii.gz` | 동일 |
| `--in` | `sub-XX_T1w_head.nii.gz` (full head) | brain이 아니라 head 입력 |
| `--aff` | FLIRT 12-DOF 결과 `..._t1w_to_mni_affine.mat` | |
| **`--splineorder`** | **3 (cubic B-spline)** | ← **COBIDAS "transformation type" 항목. `.cnf`에는 없던 값** |
| **`--warpres`** | **10, 10, 10 mm** | COBIDAS "spline control point resolution" |
| **`--regmod`** | **`bending_energy`** | COBIDAS "regularization" |
| `--lambda` | 300, 150, 100, 50, 40, 30 | |
| `--ssqlambda` | 1 | lambda를 현재 ssq로 가중 |
| `--jacrange` | 0.01, 100 | Jacobian 허용 범위 |
| `--subsamp` / `--miter` | 4,4,2,2,1,1 / 5,5,5,5,5,10 | multi-resolution 스케줄 |
| `--infwhm` / `--reffwhm` | 8,6,5,4.5,3,2 / 8,6,5,4,2,0 mm | |
| `--intmod` / `--intorder` | `global_non_linear_with_bias` / 5 | |
| `--biasres` / `--biaslambda` | 50,50,50 / 10000 | |
| **`--interp`** | **linear** | FNIRT 내부 영상 보간 (최종 `applywarp`의 trilinear와 별개) |
| `--numprec` | double | Hessian 정밀도 |

#### 세션 간 동일성 — 직접 증명

경로 의존 인자(`--ref/--in/--aff/--cout/--iout/--refmask`)를 제외한 **알고리즘 파라미터가 exp1(sub-01)과 exp2(sub-08)에서 완전 일치**한다. exp2 sub-08 vs sub-09도 완전 일치. → "두 세션에 동일 방법을 적용했다"는 진술을 스크립트 diff가 아니라 **실행 로그로 뒷받침**할 수 있다.

### exp2 모션 — 부재 확정

`fmriprep_work_method3_2nd_sub-{08,09}/` 내용물:

```
freesurfer_subjects/  T1w_brain.nii.gz  T1w_brain.nii.gz_mask.nii.gz
sub-XX_T1w_brain.nii.gz  sub-XX_T1w_head.nii.gz
sub-XX_T1w_in_MNI_{linear,nonlinear}.nii.gz
sub-XX_T1w_head_to_MNI152NLin2009cAsym_res-2_T1.log
```

`.par`·`*mcf*`·`*motion*` **0건**. exp2 출력 디렉토리도 BOLD / brain_mask / `.lta` / warp 뿐이다. → **exp2 모션 추정은 수행되지 않았음이 확정.** (잔여 항목 10 유지)

### 최종 잔여 항목

| # | 항목 | 상태 |
|---|---|---|
| 1–7 | deoblique, FNIRT config, 버전, 볼륨 수, T1w, PE/MB/PF, motion QC(exp1) | ✅ 전부 해소 |
| 8 | `METHODS_phase1_baseline.md` fMRIPrep 기재 정정 | 미조치 (로컬 편집) |
| 9 | "−60%" 근거 | 🔽 강등 (CSF 8복셀로 독립 정당화) |
| **10** | **exp2 모션 추정 (`.par` 부재)** | **미해결 — Phase 3 결과 보고 시 필요** |
| 11 | exp1 confounds TSV 손상 | 결과 무영향, 재생성 선택 |

---

## A9. Methods 복셀 선택 문장 — 구 파이프라인 서술이 남아 있음

**상태**: 사실관계 확정 (2026-08-03) · **판단 미결 (의도적 제거인지 확인 필요)**

### 발단

`methods_v2.tex` L83의 복셀 선택 문장이 실제 코드에 있는지 검증하다 발견.

> L80: "...Wang probabilistic atlas at $>50\%$ probability, intersected with each participant's BOLD brain mask (voxel counts: V1 655±214; V2 451±145; V3 103±29; hV4 63±22)"
>
> L83: "Voxels in the top 50\% of variance explained by the mean ROI HRF were retained (V1 328±107; V2 226±73; V3 52±15; hV4 32±11 voxels)"

### 확정된 사실

**(1) 그 단계는 실제로 존재했다.** 구 파이프라인 `fir_reconstruction_BH2009_system_clean.py` (commit `acebb94`, 당시 `analysis/phase1_preprocess_decoding/`, 이후 `phase0_preprocessing/`로 이동, 현재 트리에서 삭제됨):

```python
r2_threshold = np.median(r2_voxel[valid_r2_mask])          # 중앙값 임계 = 상위 50%
selected_voxels_mask = (r2_voxel >= r2_threshold) & valid_r2_mask
```

중앙값 임계이므로 결과가 정확히 절반이 되는 것이 정상이다. L83의 수치는 실측값이다.

**(2) 현 파이프라인(C010)에는 없다.** 확인 범위:

| 위치 | R² 선택 |
|---|---|
| `phase0_preprocessing/` (현재) | 없음 — 정합 방법 비교 전용(Method 1–4) |
| `phase1_procrustes_decoding/run_full_dataset_C010.py` | 없음 |
| `exp2_neural/scripts/exp2_C010_conditions.py` | 없음 |
| 로드 시점 (`utils/data_loader.py`, `rerun_loo_consistent.py`, `loco_canonical.py`, `s10b_v6_pca_rdm.py`) | 없음 |

**(3) 저장 데이터가 선택 전 수치와 일치한다.** `amplitudes_procrustes.npy` 실측 (sub-10 제외, n=9):

| ROI | 실제 저장값 | L80 기재 | L83 기재 |
|---|---|---|---|
| V1 | **665 ± 209** | 655 ± 214 | 328 ± 107 |
| V2 | **458 ± 113** | 451 ± 145 | 226 ± 73 |
| V3 | **105 ± 19** | 103 ± 29 | 52 ± 15 |
| hV4 | **64 ± 18** | 63 ± 22 | 32 ± 11 |

전 커버리지 피험자는 V1=858이 그대로 저장돼 있다(아틀라스 마스크 전체). 파생 데이터셋 4종(`full_dataset_C010`, `_with_residuals`, `full_dataset_P3`, `_P3_C011`) 모두 동일하며, 절반값을 가진 데이터셋은 서버에 없다.

### 결론

L83은 **틀린 서술이 아니라 오래된 서술**이다. 구 BH2009-FIR 파이프라인을 정확히 기술하고 있으나, 논문의 모든 결과가 산출된 C010 파이프라인에는 그 단계가 없다.

### 결정적 근거 — `compare_with_previous.md` (2026-02-09, 현재 트리에서 삭제됨)

`analysis/README.md`가 C010 검증 근거로 지목하는 문서. `git show 47bac51:analysis/validation/preprocess_Check/compare_with_previous.md`로 복원.

**§1.1 Original (Baseline32)** — 복셀 선택을 **별도 항목으로 명시**:

> - **Voxel selection: Top 50% by R² (FIR model fit)**
> - Amplitudes: `amplitudes_z.npy` (6 runs, 8 colors, **~284 voxels for V1**)
> - Range: [−2.48, 2.47] (z-scored)

**§1.2 Current (C010 + Procrustes)** — 해당 항목 **없음**:

> ```
> # 1st-level GLM: FIR (16 time points, 0-32s), Drift: None
> # 2nd-level GLM: 8 HRF + 8 deriv + 12 per-run drift = 28 regressors
> # Confounds: None (C010 = drift only)
> # High-pass: None
> ```

**두 파이프라인 대조**

| | Baseline32 (구) | C010 (현) |
|---|---|---|
| 복셀 선택 | **Top 50% by R²** → V1 ~284 | **없음** → V1 665±209 |
| z-score | 있음 (`amplitudes_z.npy`) | 없음 |
| 1st-level drift | per-run linear+const | 없음 |
| 2nd-level drift | 없음 | **12 regressor (핵심 변경)** |
| Procrustes | 있음 | 있음 |

Methods L83의 문장과 328±107이라는 수치는 **Baseline32 시대 서술**이다. C010 전환에서 z-score·1st-level drift와 **함께** 제거됐으나, 전환 문서가 "2nd-level drift가 핵심"으로만 요약하면서 복셀 선택 제거는 별도 언급하지 않았다.

### 조치 (적용됨 2026-08-03)

`methods_v2.tex` L83을 **주석 처리**했다(삭제 아님). 주석 안에 위 근거와 미결 사항을 함께 기록.

**L80 복셀 수 갱신 (2026-08-03, n=9 기준 확정).** 실제 분석에 쓰인 `full_dataset_C010/sub-{01..09}/{ROI}/amplitudes_procrustes.npy`의 `shape[2]`로 교체:

| ROI | 기존 기재 | **갱신값 (n=9)** | per-subject (sub-01~09) |
|---|---|---|---|
| V1 | 655 ± 214 | **665 ± 209** | 568 405 858 858 858 858 330 560 692 |
| V2 | 451 ± 145 | **458 ± 113** | 402 335 557 557 557 557 258 400 498 |
| V3 | 103 ± 29 | **105 ± 19** | 106 94 115 115 115 115 59 114 115 |
| hV4 | 63 ± 22 | **64 ± 18** | 67 69 70 70 70 70 **16** 70 70 |

sub-10은 전 분석에서 제외되므로 n=9. 기존 기재값의 출처·피험자 집합은 특정되지 않았고, 평균보다 **SD 차이가 컸다**(V2 145→113, V3 29→19). hV4 sub-07=16은 기지의 이상치(메모리: correlation distance 미결정 → nan).

본문에 `$n = 9$`를 명시했고, per-subject 수치를 tex 주석으로 함께 남겨 재현 가능하게 했다.

### 미결 판단

C010 전환 시 복셀 선택 제거가 **의도적 설계**였는지 **누락**이었는지는 문서가 답하지 않는다. 문서는 *무엇이* 바뀌었는지만 보여주고 *왜*는 적지 않았다.

- **일괄 재설계 해석**: Baseline32의 전처리 스택(z-score, 1st-level drift, 복셀 선택)을 통째로 걷어내고 drift만 남기는 것이 C010의 정의였다면, 복셀 선택 제거는 그 설계의 일부다. 주석 `# Confounds: None (C010 = drift only)`이 이를 지지한다. 성능 근거도 이쪽이다 — ceiling utilization 41.3% → 79.4% 개선이 복셀 선택 없이 달성됐다.
- **누락 해석**: 재설계 과정에서 항목이 빠졌고 검토되지 않았을 가능성.

추가 확인처(모두 `compare_with_previous.md`가 C010 출처로 지목, 현재 트리에 없음 → git 복원 필요): `preprocess_tests.md`, `updated_noise_procrustes.md`, `preprocess_detrend_temp/README.md`.

- **의도적이면** → L83 삭제, L80 수치를 실측값으로 갱신. 결과 영향 없음.
- **의도치 않게 누락이면** → 복원 시 전면 재분석. 현 결과 전부가 선택 없는 데이터 기반이므로 비용이 크다.

관련 결정 기록이 있을 만한 곳: `docs/SYSTEMATIC_PREPROCESSING_ANALYSIS.md`, `docs/SYSTEMATIC_SELECTION_ANALYSIS.md`, `analysis/phase1_procrustes_decoding/` 내 전환 문서.

### 포인터

- 구 코드: `git show acebb94:analysis/phase1_preprocess_decoding/fir_reconstruction_BH2009_system_clean.py` (L1173–1191)
- 이력 추적: `git log -S "r2_threshold" -- analysis/`
- 현 산출물: `/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010/{subject}/{ROI}/amplitudes_procrustes.npy`
- 대상 문장: `docs/PAPER/Methods/methods_v2.tex` L80, L83
