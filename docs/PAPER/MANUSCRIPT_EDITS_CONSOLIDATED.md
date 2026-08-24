# 원고 수정 종합 — 한 번에 반영할 전체 목록 (2026-08-16 · rev.3 2026-08-24)

> **이 문서 하나만 보고 `.tex` 를 수정한다.** `REVISION_PLAN_HMC_DISCLOSURE`(M1–M9) · `REVISION_PLAN_PRESUBMISSION_2026-08-10`(A–I) · `STATUS_ADDITIONAL_ANALYSIS`(§5·§6) 에 흩어져 있던 확정 수정안을 **대상 파일 순서로** 재배열했다. 원 문서의 항목 ID 는 추적을 위해 그대로 붙여 둔다.
>
> **줄번호는 2026-08-16 에 실제 파일과 대조해 확인했다.** 인용된 「현행」 문구는 원고에서 그대로 가져온 것이다.
>
> **rev.2 (2026-08-24) — 스텁 해소.** 종전 판은 A·C·D·E·F 를 한 줄 지시로만 두고 실제 문안을 원본 문서에 남겨 두어 단독 참조가 불가능했다. 이번 개정에서 **문안 전문을 인라인 병합**하고 누락 항목 하나를 신설했다.
>
> | 변경 | 내용 |
> |---|---|
> | **§4.0 신설** | SDC 변위 실측 — 종전 판에 **편집 항목 자체가 없었다.** 현행 `supplementary.tex:74` 의 `it cannot generate condition-specific differences` 를 교체하는 **필수** 항목 |
> | §2.7 (E) · §3.3 (F) · §4.1 (A) · §4.5 (C) · §4.6 (D) | 문안·표·LaTeX 전문 인라인 |
> | §3.6 (F3) | 전제가 현행 원고와 불일치 → 등급 **권장**으로 강등, 신규 초안 표시 |
> | §4.7 (H) | `§S16 신설` 은 **stale 번호** — 실제 S16 은 이미 사용 중. 배치 권고 변경 |
> | **§1 초록** | 재설계 — M7 은 핵심절만, **F2·M8 폐기**(14번 문장 삭제로 대체). 조치표는 §1.0. `SUBMISSION_CHECKLIST:336` P2 행 동반 수정 필요 |
> | §6 I3 | **✅ 해소** (2026-08-17, 17/17 재검증) → 반영 순서 1단계 삭제 |
>
> **rev.3 (2026-08-24) — 전처리 arm 구성 확정.** 저자 결정으로 **`hmc_v2`(재정렬 arm)를 원고에서 제외**하고, 재정렬 미적용의 근거를 **Methods 에서 보간 비용으로 제시**한다. 이에 따라 원고가 다루는 전처리 축은 **시간축 하나**이며, 보고 arm 은 `with_residuals`(정본) · `motreg`(민감도) · `motshift`(대조) 셋이다.
>
> | 변경 | 내용 |
> |---|---|
> | **§0.4 신설** | 결정 기록과 그 파급. **이 절을 먼저 읽을 것** |
> | **§1.5 신설** | `Methods/methods_v2.tex` — 재정렬 미적용 근거 문단. 이번 개정의 핵심 신규 항목 |
> | **§2.1 삭제** | ICC(2,1) 본문 승격 **철회**. 검증 결과 arm 쌍 의존이고 CVD 포함이 부풀린 값 (§0.4-C) |
> | **§4.2 · §4.3 삭제** | 재정렬 문단과 `tab:hmc_robustness` 폐기 |
> | **§1.1 · §2.2 · §2.4 · §2.5 · §2.8 · §2.9 · §3.1 · §3.2 · §3.4 · §4.1 · §5.1** | `hmc_v2` 근거를 `motreg`/`motshift` 근거로 교체 |
| **§0.5 C1·C3·C4·C6·C7 개정, C9 신설** | C9 = "왜곡의 형태는 회전이다". 금지 표현 3건 추가 |
| **§4.9 정합 경고** | exp2 통일 arm 이 재정렬을 포함하므로 §1.5 와 표현을 맞춰야 한다 (§0.4-E) |
| **§7 1·1b·1c 신설** | 결정 기록 · 문서 정정 · job 171184 |
> | **§2.4 승격** | protan V1 disparity 가 **보고되는 세 arm 전부에서 유의**해진다 (§0.4-B) |
> | **§8.1 신설** | 인용 금지 수치 목록 |

> **반영 상태 (2026-08-24 `.tex` 대조): 전 항목 미반영.** `supplementary.tex` 에 `tab:motion_loco` 와 SDC 변위 수치가 없고, 46행은 여전히 `Every neural endpoint was recomputed`, 74행은 `cannot generate`, 464-468행은 `remains to be extended` 다. `methods_v2.tex` 에도 재정렬 관련 서술이 없다.
>
> **rev.3 에서 폐기된 두 항목(realignment 문단 · `tab:hmc_robustness`)은 `.tex` 에 없는 것이 정상이다.** 종전 판이 이를 미반영 항목으로 적고 있었으므로 여기서 정정한다.

---

## 0. 반영 순서

| 단계 | 이유 |
|---|---|
| ~~**1. §7 형식 (I3 → I4)**~~ | I3 은 2026-08-17 에 해소됨(§6). **I4(Methods 중복본 참가자 수 상충)만 남는다** — 5분, 아무 때나 |
| **2. §5 Supplementary** | A(3-arm 표)가 §S2 를 신설하고 M-§S2 가 거기에 표를 얹는 구조. 역순이면 §S2 를 두 번 재편 |
| **2.5 §1.5 Methods 재정렬 문단** | §S2 와 한 벌이다. 부록 문안을 확정한 직후에 넣어야 표현이 어긋나지 않는다 |
| **3. §2 Results → §3 Discussion → §1 제목·초록** | 초록은 본문이 확정된 뒤 마지막에 |
| **4. §6 그림** | 별표 제거는 조판 마지막 |

**차단 항목**: **I2 (데이터 공개 방침)** — IRB 확인이 투고 저널 관리 에이전트 쪽에서 진행 중. 결론 전까지 Methods 문장과 Data availability 절을 **둘 다 비워 둔다**(한쪽만 채우면 상충한다).

---

## 0.4 전처리 arm 구성 — 결정과 파급 (2026-08-24 확정) ★ **먼저 읽을 것**

### A. 결정

**`hmc_v2`(재정렬 arm)를 원고에서 제외한다.** 대신 Methods 에서 재정렬을 적용하지 않은 근거를 **보간 비용**으로 제시한다(§1.5). 원고가 보고하는 arm 은 셋이다.

| arm | 원고에서의 역할 | 재샘플링 |
|---|---|---|
| `with_residuals` | **정본.** 본문 전 수치의 출처 | 1회 |
| `motreg` | **민감도 주 arm.** 움직임 귀속 판정을 진다 | 0회 추가 |
| `motshift` | `motreg` 의 **음성 대조.** 독립 arm 이 아니다 | 0회 추가 |

**근거**: 재정렬이 되돌리는 실제 변위가 기준 볼륨 대비 최대 **0.37 복셀**(0.74 mm)인 반면, 볼륨마다 다른 변환은 보간 오차를 **시변 잡음**으로 만든다. 정본은 전 볼륨에 동일 변환을 쓰므로 그 오차가 시간에 대해 일정해 상쇄된다. 미세 다중복셀 패턴 기하를 다루는 본 분석에서는 교환이 불리하다. 실측으로도 ROI tSNR 이 1.7–3.0% 낮아진다.

> **⚠ 사전 확정 조항과의 관계 — 기록으로 남긴다.** `STATUS_ADDITIONAL_ANALYSIS_2026-08-15:327` 은 *"색 종점은 결과와 무관하게 전량 보고하되 판정에는 쓰지 않는다"*, `HMC_REANALYSIS_PRESPEC.md:85` 는 *"두 파이프라인 결과를 나란히 보고한다"* 로 적혀 있다. 이번 결정은 후자를 따르지 않는다. 저자 판단이며, 판단 근거(보간 비용)는 종점과 무관하게 진술 가능한 성격이다. **`HMC_REANALYSIS_PRESPEC.md` 에 이 결정과 사유를 추가 기록할 것**(§7).

### B. 파급 1 — protan V1 disparity 가 올라간다

`hmc_v2` 는 protan V1 을 약화시킨 **유일한** arm 이었다. 제외하면 보고되는 세 arm 전부에서 유의하다.

| | 정본 | `motreg` | `motshift` | *(제외)* `hmc_v2` |
|---|---|---|---|---|
| sub-09 V1 disparity | $p$ = .007 / LOSO .045 | $p$ = **.0040** / LOSO **.0215** | $p$ = **.0048** / LOSO **.031** | ~~.077~~ |

**이것이 이번 결정의 실질적 효과이며, 유일한 효과다.** 나머지는 바뀌지 않는다.

| | 상태 |
|---|---|
| deutan V2 | **강등 유지.** `motreg` .218 · 대조 `motshift` .005 · 정본 LOSO .116 |
| CVD hV4 개인 결손 | **정본 한정 유지.** `motreg` .148 / .204 |
| protan $\hat\beta_c$ | **반전 유지.** `motreg` $+24 \to -24$ |
| deutan V1 이 새로 유의해지던 혼란 셀(.027) | `hmc_v2` 전용이었으므로 소멸 |

### C. 파급 2 — ICC 자산은 폐기한다

발표 예정이던 ICC$_{2,1}$ = 0.825 는 **정본과 `hmc_v2` 사이에서만** 계산된 값이다(`_arm_agreement.py` 의 `ARMS = ["with_residuals", "hmc_v2"]`). 대체 가능성을 전부 확인했고 전부 실패했다.

| 계산 방식 | hV4 | V3 | V2 | V1 | 판정 |
|---|---|---|---|---|---|
| 정본↔`hmc_v2` ($n{=}9$) | **0.825** | 0.662 | 0.471 | $-0.005$ | 게이트 순서와 일치 |
| 정본↔`motreg` ($n{=}9$) | 0.710 | 0.502 | 0.615 | $-0.037$ | V2 > V3 |
| 정본↔`motshift` ($n{=}9$) | 0.809 | 0.670 | 0.553 | 0.642 | **V1 이 0.64** |
| 정본↔`motreg` (**HC만 $n{=}7$**) | 0.634 | 0.678 | **0.826** | 0.067 | **V2 가 hV4 를 앞선다** |
| 정본 arm 내부 split-half ($n{=}9$) | 0.744 | 0.518 | 0.724 | 0.485 | hV4 와 V2 차이 0.02 |

두 가지가 확인된다. 첫째, **깨끗한 그림은 `hmc_v2` 쌍 하나에서만 나온다.** 둘째, $n{=}9$ 와 $n{=}7$ 의 차이가 큰 이유는 **CVD 두 명이 hV4 에서 양 arm 모두 낮은 값을 가져 피험자 간 분산을 키우기 때문**이며, ICC 는 그 분산을 분모에 쓰므로 값이 올라간다. 즉 0.825 는 **CVD 포함이 부풀린 값**이다.

**Dice 표와 같은 구조다.** 유리해 보이는 지표를 실었다가 리뷰어가 HC 만으로 재계산하면 무너진다. **싣지 않는다.**

→ hV4 단독성은 **색 라벨 순열 게이트의 arm 간 재현**만으로 지탱한다. 이는 검정 하나가 아니라 **같은 검정이 세 arm 에서 세 번 같은 답을 준 것**이고, 다른 세 ROI 는 어느 arm 에서도 통과하지 못한다.

| arm | V1 | V2 | V3 | **hV4** |
|---|---|---|---|---|
| `with_residuals` | .164 | .424 | .586 | **.011** |
| `motreg` | .624 | .924 | .143 | **.013** |
| `motshift` | .272 | .112 | .124 | **.002** |

### D. 파급 3 — `motshift` 는 대조군이지 arm 이 아니다

세 열을 나란히 두면 deutan V2 가 3열 중 2열에서 유의한 것처럼 보인다(정본 .040, `motshift` .005). **의미는 정반대다.** 표 머리와 각주에서 반드시 구분한다.

| | Primary | Motion regression | *Control: time-shifted regressors* |
|---|---|---|---|

> The third column carries the same twelve regressors circularly shifted within run, preserving their autocorrelation and spectrum while destroying their temporal alignment with the data. It isolates the cost of adding regressors from the removal of motion-aligned variance, and is a control rather than an independent preprocessing variant.

### E. 남는 정합 문제 — §4.9 exp2

§4.9 의 exp2 통일 arm(`full_dataset_C010_exp2_harm_hmc`)은 **재정렬을 포함해** 처리됐고, 그 비교의 HC 기준·exp1 앵커를 `full_dataset_C010_hmc_v2` 로 맞췄다. 즉 exp1 `hmc_v2` 가 그 절에 간접적으로 남아 있다.

**모순은 아니다.** Methods 가 "구현해 평가했으나 정본에 채택하지 않았다"고 적으면, 세션 2 통일 arm 이 재정렬을 포함하는 것과 충돌하지 않는다. **다만 두 가지를 처리해야 한다.**

1. §4.9 문안에서 exp1 앵커를 **정본 arm 값으로 교체**하거나, 앵커가 재정렬 arm임을 명시한다. 현재는 후자가 문안에 없다.
2. Methods 문단(§1.5)과 §4.9 가 같은 표현("realignment")을 쓰되, **정본 미적용 / 세션 2 통일 arm 포함**이라는 구분이 독자에게 보이게 쓴다.

---

## 0.5 핵심 결론별 서술 규칙 — C1–C8 (2026-08-18 확정)

> **아래 §1–§6 의 개별 수정안은 전부 이 규칙을 따라야 한다.** 충돌하면 이 절이 우선한다. 서술 전문과 근거 수치는 [`analysis/future_phase1_sensitivity/TEAM_BRIEF_2026-08-18.md`](../../analysis/future_phase1_sensitivity/TEAM_BRIEF_2026-08-18.md) §5.3.

**적용 규칙**: 본문은 정본 arm 기준으로 서술한다. **보고되는 세 arm**(§0.4-A) 중 어디서든 부호가 뒤집히거나 유의성이 사라지는 주장은 그 층위에서 강등한다. 순서는 **유의성 주장 → 순위·존재 주장 → 서술적 관찰**이다. 부하가 걸린 종점은 §S2 부록 표에 세 arm 을 나란히 싣되 `motshift` 는 대조로 표기하고(§0.4-D), 본문은 정본 값만 쓰고 그 표를 참조한다.

| | 결론 | 서술 층위 | 반영 지점 |
|---|---|---|---|
| **C1** | 통제군 연속 hue 보간은 hV4 단독 | **유지.** 근거는 **색 라벨 순열 게이트의 3 arm 재현**($p$ = .011 / .013 / .002)뿐이다. **ICC 는 쓰지 않는다**(§0.4-C) | §4.1 §S2 3-arm 표 |
| **C2** | 8색 범주 식별 보존 | 유지. 문구 변경 없음 | 확인만 |
| **C3** | CVD hV4 보간 결손 | **정본 arm 한정 유의**(protan $p$=.011; deutan $p$=.054 로 정본에서도 비유의) → 민감성 공개(`motreg` .148 / .204) → **순위 배치를 바닥에 깐다**(세 arm 전부 최대 1/7) → **크기는 추정 불가로 명시** | §2.2 (M4), §2.9 |
| **C4** | 왜곡의 영역 편재 | **protan V1 = 세 arm 전부 유의**(.007 / .0040 / .0048, LOSO 전부 유의) → 주장 가능. **deutan V2 = 강등**(`motreg` .218, 대조 `motshift` .005, 정본 LOSO .116) → 서술적 관찰. **두 사례를 대비시키는 서술은 금지** | §2.4 (M2), §3.1 (M5) |
| **C5** | 개인차 | **발견 → 프레임워크 속성.** 참가자별 추정은 방법의 속성. 편재 확립에 필요한 것은 **표본**이지 추가 분석이 아니다 | §1.1 제목, §1.2 초록(M7), §3.5 (M6), §3.6 (F3) |
| **C6** | 범주 보존 / 연속 기하 손상의 해리 | 유지하되 **근거를 유의성 → 순위로 교체.** 선행연구(균일 gain 감소)와 구별되는 지점 | §2.3 (M1), §2.4 (M2) |
| **C7** | 필터 $\hat\beta_c$ | **deutan 2축 유지**($-42$, $-48$) / **protan 2축 반전**($+24 \to -24$). 배포값은 동결값 그대로 보고, protan 파라미터에 생리학적 해석 부여 금지 | §3.2 (H), §4.7 |
| **C8** | 역산·심리물리 | 불변. 해석적 단계임을 명시 | 확인만 |
| **C9** | **왜곡의 형태는 회전이다** ★ 신규 | protan V1 최적 순환이동 45°, 이득 24.0% / 19.2%, 통제군 최적이동 이득 분포 대비 $p$ = .0091 / .0254. 45° 로 되돌리면 disparity 1.037 → 0.788 로 **통제군 평균 아래**. **기여 1 → 기여 2 의 다리** | §2.10, §3.3, §4.5 |

**금지 표현**

| 표현 | 처리 |
|---|---|
| `significantly below controls` | **조건부** — arm 한정어와 민감성 문장이 붙을 때만. 단독 사용 금지 |
| `localized to a different area in each` | 금지 |
| `individual-specific cortical distortion` | 금지 |
| `individually distinct pattern of distortion` | 금지 |
| **ICC$_{2,1}$ = 0.825 (및 V1 $-0.005$)** | **금지 (신규 2026-08-24)** — arm 쌍 의존 + CVD 포함이 부풀린 값. §0.4-C |
| **deutan V2 와 protan V1 을 대비시키는 서술** | **금지 (신규)** — 두 셀의 지위가 다르다. protan V1 은 세 arm 유의, deutan V2 는 강등 |
| 효과크기를 유의성의 대체물로 쓰기 | 금지 — $d_{cc}$ 95% CI 가 정본 protan 조차 $[-5.93,\ -0.41]$. §2.9 |

**C5 문구 주의**: "추가 분석이 필요하다"로 쓰지 않는다. 같은 자료에서 검정 형태 6종을 이미 돌렸고 전부 같은 답이므로(브리프 §3.3-3), 더 파면 해결된다는 뜻으로 읽혀 그 문장과 충돌한다. **"더 큰 표본에서의 검증이 필요하다"** 가 정확하다.

---

## 1. `main.tex` — 제목·초록

### 1.0 초록 — 조치 요약 (§1.2·§1.3 은 이 판정을 따른다)

현행 초록 = **250 단어 / 14 문장**. 11·12 번이 **이미 연달아 붙은 한계 문장**이다 — 세 번째 한계도, 닫는 약속도 필요 없다. **강건성 문장을 더하는 대신 취약한 주장을 빼서 방어할 것이 없게 만든다.**

| # | 조치 | 단어 |
|---|---|---|
| 7 | `differently in each individual` 삭제 (§1.2) | 24 → 22 |
| 11·12 | 불변 — 한계는 여기서 끝난다 | 0 |
| 13 | 불변 — 기여 진술 | 0 |
| 14 | **삭제** (§1.3) | **−14** |

**결과 = 234 단어 / 13 문장** (2026-08-24 `main.tex` 에 실제 치환해 검증). 금지 표현과 arm 취약 주장이 빠지면서 현행보다 짧아진다. IN 요건(단일 문단)에 영향 없음.

> **⚠ 연쇄**: `SUBMISSION_CHECKLIST_IMAGING_NEURO.md:336` 의 P2 항목이 `초록 교체 (M7 + M8 IN 판)` 으로 적혀 있다. **M8 은 폐기됐으므로 그 행을 함께 고쳐야 한다.**

### 1.1 제목 `main.tex:63` — M9

**현행**

> Individual-specific distortion of cortical hue geometry in color vision deficiency informs personalized color correction

**문제**: `Individual-specific` 이 정확히 무너진 주장이다. deutan V2 는 움직임 회귀에서 사라지고(.040 → .218) **시간 정렬을 파괴한 대조에서는 사라지지 않으므로**(.005) 상승분이 움직임에 귀속되며, 정본 arm 의 LOSO 추정량에서도 이미 비유의였다(.116). `CLAUDE.md` Policy 의 "specificity claim 금지" 와도 정면 충돌한다. `cortical hue geometry` 는 이미 정확하므로 유지한다.

> **⚠ protan V1 을 근거로 반대 방향의 편재 주장을 하지 않는다.** protan V1 은 세 arm 전부에서 유의하지만(§0.4-B), 한 참가자에서 한 영역이 견고하다는 것이 **"참가자마다 다른 영역"** 을 뒷받침하지는 않는다. 대비 대상인 deutan 쪽이 강등됐기 때문이다.

**후보**

| # | 문안 | 겨냥 |
|---|---|---|
| **T4** | From cortical hue-geometry distortion to individualized stimulus-space correction in color vision deficiency | **Imaging Neuroscience** — 두 기여를 모두 담음 |
| T1 | Hue identity and hue geometry dissociate in the cortical color representation of color-vision-deficient observers | JNeurosci — 해리가 finding. `From A to B` 형식을 review 로 읽는 경향이 있어 선언형이 안전 |
| T2 | Inverting an individual's cortical color representation into a stimulus-space correction filter | 방법 단독 강조 |
| T3 | Preserved categorical decoding with disrupted continuous hue interpolation in color vision deficiency | 보수적 대안 |

**`hue-representation` 은 쓰지 않는다.** 8색 범주 식별은 보존된다(정본 arm LORO 8분류 CVD 최저 셀 $0.375$ = chance $0.125$ 의 3배). "표상이 왜곡되었다"고 쓰면 살아 있는 절반까지 죽은 것으로 진술하게 되고, 이는 본 논문의 핵심 대비(해리)를 제목이 스스로 지우는 것이다.

### 1.2 초록 중간 `main.tex:89` — M7

**현행**

> All eight colors remained decodable from cortical activity in both CVD participants, whereas the continuous hue geometry departed from controls, **differently in each individual**.

**교체 — 한 문장으로 끝낸다**

> All eight colors remained decodable from cortical activity in both CVD participants, whereas the continuous hue geometry departed from controls in both.

**`differently in each individual` 삭제는 필수** — §0.5 금지 표현 `individually distinct pattern of distortion` 에 해당하고 `CLAUDE.md` Policy 의 "specificity claim 금지" 와 정면 충돌한다.

**방향 대비는 초록에 넣지 않는다.** $\hat\beta_c$ 는 정본 arm 에서만 두 참가자의 부호가 갈린다(deutan $-42 / -48$ · protan $+24 / -24$ — `motreg` 에서는 둘 다 음수). 초록에서 개인화를 지탱하는 것은 8번 문장의 `each`(참가자별 적합)이지 방향 대비 finding 이 아니며, 이것이 C5(개인차 = 프레임워크 속성)와도 맞는다. 방향 대비는 **Results §2.5 (M3)** 에 arm 단서와 함께 남는다.

### 1.3 초록 마지막 `main.tex:89` — 14번 문장 삭제

```diff
  This study identifies a previously uncharacterized geometric distortion of the cortical color representation in CVD and introduces, to our knowledge, the first cortically grounded framework for individualized color correction.
- Systematic studies can quantify these distortions and provide a new class of personalized filters.
```

**사유**: `can quantify ... and provide` 는 **약속**이다. 한계는 11·12 번이 이미 말했으므로 **13번(기여 진술)에서 끝낸다.**

**13번은 손대지 않는다.** `identifies a previously uncharacterized geometric distortion` 은 `CLAUDE.md` 가 기여 1 을 **finding** 으로 규정한 것과 일치하고, 순위 근거가 두 arm 모두에서 살아 있다(범주 식별 최저 셀 deutan V1 hmc $0.229$ vs chance $0.125$).

---

## 1.5 `Methods/methods_v2.tex` — 재정렬 미적용 근거 ★ **신규** (등급: 필수)

> 2026-08-24 신설. §0.4-A 결정의 이행 항목이다. **이 문단이 없으면 재정렬 미적용이 서술되지 않은 채 남는다.**

### (a) 본문 문안

기존 움직임 관련 서술 뒤(움직임 파라미터 산출을 기술한 자리)에 넣는다.

> Head-motion realignment was not applied. Mean framewise displacement was 0.24--0.38 mm across participants, and the maximum displacement from each run's reference volume was at most 0.37 voxel (0.74 mm). Realignment requires a separate resampling for each volume, so its interpolation error varies over time, whereas a single transform applied to every volume leaves an error that is constant over time and largely cancels in the multivariate pattern. Because the representational geometry analysed here is carried by fine-grained voxel patterns, we judged that cost to exceed the benefit at this displacement magnitude. Motion was instead addressed in the temporal domain, by adding the six motion parameters and their temporal derivatives to the second-level design matrix in a sensitivity analysis (Supplementary~\S S2).

**마지막 문장을 반드시 붙인다.** *"적용하지 않았다"* 로 끝내면 태만으로 읽히고, *"대신 시간축에서 다뤘다"* 로 넘겨야 리뷰어의 다음 질문이 부록으로 이어진다.

### (b) 어휘 규칙

| 금지 | 사유 | 허용 |
|---|---|---|
| `we omitted a standard step` | 태만하게 읽힌다 | `was not applied`, 그리고 곧바로 근거 |
| `realignment would have introduced noise` | 반사실 단정 | `requires a separate resampling for each volume, so its interpolation error varies over time` |
| `motion was negligible` | 방어 불가 | 실측치를 그대로 제시 |
| `tSNR was lower, so we did not apply it` | **본문에 쓰지 않는다.** 품질 수치는 §S2 에 둔다 | 본문은 변위 크기와 보간 논거만 |

### (c) 본문에 넣지 않는 것

**tSNR $1.7$–$3.0\%$ 하락은 §S2 에 둔다.** 본문 Methods 는 `0.37 복셀` 하나로 충분하고, 그 값은 MCFLIRT 파라미터에서 직접 나오므로 어떤 재구성 산출물도 인용하지 않는다.

### (d) 연쇄 확인 — §4.9 와의 정합

세션 2 통일 arm 은 재정렬을 **포함해** 처리됐다(§0.4-E). 위 문안이 `not applied` 라고 적는 대상은 **정본 파이프라인(세션 1)** 이므로 모순이 아니지만, §4.9 문안에서 그 구분이 독자에게 보여야 한다. 두 문안을 **같은 회차에 함께 확정할 것.**

**산출 근거**: `analysis/phase0_preprocessing/hmc_reanalysis/server_recovered/README.md`(코드 감사 · 항등 검사), `analysis/phase0_preprocessing/results/hmc_summary.csv`(tSNR · ROI 겹침), `*_desc-motion.par`(변위).

---

## 2. `Results/results_v4.tex`

### 2.1 `:38` 뒤 — B · 강건성 단서 ⚠ **철회 (2026-08-24)**

> **종전 안**: ICC$_{2,1} = 0.83$ 을 본문에 올려 hV4 단독성의 두 번째 독립 축으로 삼는다.
>
> **철회 사유**: 그 값은 정본과 `hmc_v2` 사이에서만 성립하고, `motreg` 로 바꾸면 통제군 $n{=}7$ 에서 V2($0.826$)가 hV4($0.634$)를 앞선다. arm 내부 split-half 로 바꿔도 hV4 와 V2 차이가 $0.02$ 다. 게다가 $n{=}9$ 값은 CVD 두 명의 극단값이 피험자 간 분산을 키워 부풀린 것이다. 전체 근거는 **§0.4-C**.

**대체 조치 — 한 문장은 여전히 넣는다. 근거만 바꾼다.**

> This localization held under motion regression and under the time-shifted control (Supplementary~\S S2); no other retinotopic region exceeded its color-label null in any arm.

**근거**: 이것은 ICC 없이 성립하며, 실제로 세 arm 에서 세 번 반복된 검정이다(`.011` / `.013` / `.002`). 흔들리는 보조 지표를 덧붙이는 것보다 안전하다.

### 2.2 `:40` — M4 · CVD hV4 단일사례

**현행 마지막 문장**

> The deutan $p$-value reflects the power of a single-case test against $n = 7$ controls.

**교체** (앞의 수치는 그대로 둔다)

```diff
- The deutan $p$-value reflects the power of a single-case test against $n = 7$ controls.
+ The magnitude of this reduction was sensitive to preprocessing. Neither single-case contrast reached significance once motion parameters were added to the design matrix, although the control-level interpolation architecture was unchanged (Supplementary~\S S2).
```

**근거**: 현행 문장은 유의성 미달을 **검정력** 탓으로 돌린다. 그 설명은 틀렸다. 원인은 **효과크기 축소**이며, 움직임 회귀 arm 에서 $d_{cc}$ 가 protan $-3.25 \to -0.95$, deutan $-2.02 \to -1.23$ 로 줄어든다. 통제군을 늘려도 해소되지 않는다.

**⚠ `motshift` 를 이 문장에 끌어들이지 않는다.** 대조 arm 에서 protan 은 $p$ = .056 으로 오히려 정본에 가깝다. 대조는 **회귀자 추가 비용**을 재는 장치이므로 강건성 진술의 근거가 아니다. 세 arm 값은 표에만 둔다.

### 2.3 `:56` — M1 · 소제목

```diff
- \subsection{Geometric deviation localizes to a distinct ROI in each CVD case}
+ \subsection{Hue geometry departs from the control reference in both CVD cases}
```

### 2.4 `:60` — M2 · 첫 문장

**현행**

> Elevated Procrustes disparity **localized to a different ROI** in each CVD participant, V1 in the protan participant and V2 in the deutan participant (Figure~\ref{fig:geometry}B).

**교체 (2026-08-24 개정 — 두 셀의 지위가 다르다)**

> Procrustes disparity from the healthy-control reference was elevated in both CVD participants, at V1 in the protan participant and at V2 in the deutan participant (Figure~\ref{fig:geometry}B). The protan V1 elevation held under motion regression and under the time-shifted control ($p = .007$, $.004$, $.005$; leave-one-subject-out $p = .045$, $.022$, $.031$). The deutan V2 elevation did not: it was removed by motion regression ($p = .218$) but not by the same regressors after their temporal alignment with the data was destroyed ($p = .005$), which places the elevation on motion-aligned variance, and it was already a non-significant trend under the leave-one-subject-out estimator in the primary arm ($p = .116$). We therefore report the deutan V2 elevation descriptively (Supplementary~\S S2).

**⚠ 두 참가자를 대비시키지 않는다.** 위 문안은 **각 셀을 그 자체로** 서술한다. "protan 은 견고하고 deutan 은 아니다" 로 읽히도록 병치하면 §0.5 금지 표현(`localized to a different area in each`)의 변형이 된다.

### 2.5 `:66` — M3 · 기여 2 로 넘어가는 다리 ★ 최우선

**현행**

> The two CVD participants differ in where the deviation lies and in how strong it is. **Because each deviation is participant-specific**, a single family-level correction would match only one of them. In each participant the continuous arrangement of hues is displaced in a direction and magnitude specific to that individual, which a personalized correction must therefore offset.

**문제**: 개인화 필요성 논거 전체가 **ROI 편재에 얹혀 있다.** 그 근거가 무너지면 기여 2 의 도입부가 함께 흔들린다.

**교체 — 안정적인 근거로 다리를 다시 놓는다**

> The two participants' deviations differ in magnitude and in the direction of the fitted hue rotation (Section~\ref{sec:results:twocomp}), and their elevated discrimination thresholds lie on different confusion axes (Section~\ref{sec:results:jnd}). A single family-level correction would therefore match only one of them.

**근거**: 적합된 $\hat\beta_c$ 의 차이($-42°$ vs $+24°$)와 심리물리 역치 축 차이는 **disparity ROI 와 독립**이고 arm 교란에 노출되지 않는다. 필터 표적 ROI 도 disparity 가 아니라 **held-out test-loss** 로 선정됐다. 개인화 논거를 그쪽으로 옮긴다.

> **단, deutan 만 강건성 검증을 통과했다** (§3.2 · §4.7 참조). protan $\hat\beta_c$ 는 움직임 회귀에서 부호가 바뀌므로($+24 \to -24$, 재표집 지지집합이 부호에서 겹치지 않음), 이 문장은 **fitted direction 이 다르다**는 관측 진술에 머물러야 하고 "각자 안정적으로 식별된 왜곡"으로 읽히면 안 된다.

### 2.6 `:195` `:197` 뒤 — 8AFC 독립 종점 격상 (신규 문단)

**현행**: 8AFC 가 JND 문단 **끝 한 문장**으로 묻혀 있다.

**문제**: 8AFC 는 **적합 손실에 들어가지 않은 유일한 행동 종점**이다. JND 는 $L_\gamma$ 원자로 적합에 기여했으므로 전향적이되 **독립은 아니다.** 가장 방어하기 쉬운 결과가 가장 눈에 안 띄는 자리에 있다.

**방향**: JND 문단에서 8AFC 문장 두 개를 **빼내 독립 문단**으로 만들고, `held out from the fitting loss` 를 명시한다. 새 계산 없음.

**문안**

> \paragraph{Identification accuracy, held out from the fitting loss.}
>
> Eight-alternative color identification entered neither the behavioral nor the neural fitting term, so it provides a prospective test that is independent of the loss the filters were derived from. In the deutan participant identification rose from $0.81$ (95\% CI $[0.70, 0.89]$) to $0.97$ ($[0.89, 0.99]$) under both filters. In the protan participant identification was at ceiling without a filter ($1.00$, $[0.94, 1.00]$) and remained at $0.98$ ($[0.92, 1.00]$) under the individualized filter, whereas it fell to $0.86$ ($[0.75, 0.92]$) under the deployed comparator (Wilson score intervals, $n = 64$).

**주장 위계 — 이 문단에 쓸 수 있는 것과 없는 것**

| 금지 | 허용 |
|---|---|
| `individual-specific effect` | `individually derived filter` · `within-person prospective effect` |
| `restores / normalizes cortical representation` | `produced measurable changes in` |
| `outperforms deployed filters` | `differed from the deployed comparator in ...` |
| protan: `robustly identified distortion 의 inverse 검증` | `preprocessing-contingent production model 에서 파생되어 사전 동결된 필터의 전향적 시험` |

### 2.7 `:197` + §S19 — E · protan orange–yellow 트랙 불일치 각주

sub-09 개인화 조건의 orange–yellow 트랙이 다른 트랙과 어긋난다는 사실을 각주로 공개. (등급: 권장)

**문안** (`results_v4.tex:197` 문단 끝 각주 또는 §S19)

> In the protan participant one of the two staircases for orange--yellow diverged from its partner under the individualized filter, settling four times higher after answering correctly at a separation four times smaller earlier in the same block. The pair's partner staircase converged normally on the same rendered stimuli, which excludes a rendering failure, and the remaining seven pairs of that block match the participant's own baseline. The pair is reported on the average of both staircases, as everywhere else; using the converged staircase alone moves it from $z = +1.33$ to $z = -0.58$ and the mean $|z|$ from $0.93$ to $0.84$.

**근거**: 트랙 불일치 0.0813 은 **전부 이 한 쌍에서 온다** — orange–yellow 를 빼면 0.0193 으로 본인 기준선 0.0156 과 같은 수준. 후보 원인 5개 중 gamut/렌더링 결함은 **탈락**(sc1 이 같은 자극에서 0.170 으로 정상 수렴 — 렌더링 실패라면 두 트랙이 함께 망가진다), 범위 절단도 탈락(최대 0.80 < 상한 0.95). 남는 것은 **단일 트랙 lapse**(같은 트랙에서 0.20 정답 → 0.80 오답).

**값을 조정하지 않는다.** 208개 중 이 한 트랙만 문제이므로 제외 규칙을 세우면 사후적으로 보이고, 조정 방향이 결론에 유리한 쪽이라 더 그렇다. **평균 유지 + 전량 공개**가 방어 가능한 선택이다. 초록 근거인 green–blue 는 두 트랙 모두 정상 수렴(0.135 / 0.080)이라 **영향 없음**.

### 2.8 Results §3.2 첫머리 — Q1 해석 범위 진술 ★

all-ROI sensitivity 표(§5.2)를 **싣기로 했으므로** 그 앞에 해석 범위를 선언한다.

> Throughout, we interpret two quantities: the control-level localization of continuous hue interpolation, which is stable across preprocessing arms and across the color-label permutation gate, and the fitted filter parameters together with their psychophysical evaluation, which do not depend on preprocessing. The full region $\times$ arm grid is reported in Supplementary~\S S2 for completeness; individual cells within it are descriptive and are not used to support any claim in the main text.

**근거**: 표를 실으면 리뷰어는 **본문이 주장하지 않는 셀**(예: 대조 arm 에서 유의해지는 deutan V1 $p$ = .016, deutan V2 $p$ = .005)을 반드시 본다. 이 문장이 **표의 존재가 곧 주장이 아님을 사전에 선언**하고, 표 아래 문장이 그 셀을 막는다. 두 문장이 함께 있어야 "전부 공개했으나 본문은 견고한 것만 딛고 선다"가 성립한다.

**⚠ 문안 수정**: 종전 초안의 `stable across preprocessing arms` 는 arm 이 넷이라는 전제였다. 셋으로 바뀌었으므로 `across the motion arms reported in Supplementary~\S S2` 로 적는다.

---

### 2.9 `:40` 뒤 — 순위 배치 (2026-08-24 · rev.3 에서 3-arm 으로 개정) ★

**왜 필요한가.** §2.2(M4)가 CVD hV4 결손의 **유의성**을 정본 arm 한정으로 내려놓는다. 그 문장만 두면 결손 주장 자체가 사라진 것처럼 읽힌다. 유의성 아래에 **전 arm 불변인 층위**를 깔아야 한정이 부정으로 넘어가지 않는다. C3 서술안의 세 번째 요소가 이것이다.

**§2.2 교체문 바로 뒤에 넣는다**

> What did not depend on preprocessing was the placement of the two participants within the control range. In all three arms both CVD participants scored below the control mean, at most one of the seven controls scored below either of them, and the control group passed the group-level interpolation gate in every arm while neither CVD participant passed the individual-level test in any arm.

**근거 (`results/perm_adjacent_arm_*.json` 의 `per_subject` 에서 집계)** — hV4 LOCO adjacent accuracy

| arm | 통제군 평균 | 통제군 7명 (오름차순) | deutan | 그 이하 통제군 | protan | 그 이하 통제군 |
|---|---|---|---|---|---|---|
| `with_residuals` | 0.456 | .312 .375 .400 .438 .521 .562 .583 | 0.250 | **0/7** | 0.125 | **0/7** |
| `motreg` | 0.458 | .250 .312 .396 .417 .600 .604 .625 | 0.271 | **1/7** | 0.312 | **1/7** |
| *`motshift`* | 0.483 | .354 .375 .400 .458 .500 .583 .708 | 0.375 | **1/7** | 0.229 | **0/7** |

**⚠ 문구 정밀도 — 세 가지를 지킬 것.**

1. **"below the control distribution" 로 쓰지 않는다.** `motreg` 에서 protan 0.312 는 통제군 최솟값 0.250 보다 **높고**, `motshift` 에서 deutan 0.375 도 최솟값 0.354 보다 높다. 참인 진술은 **통제군 평균 아래**이지 분포 전체 아래가 아니다.
2. **동률 처리를 각주로 밝힌다.** 위 표는 **엄격 부등호**다(최대 1/7). 동률을 포함해 세면 `motreg` protan 과 `motshift` deutan 이 각각 2/7 이 된다. 어느 규칙이든 결론은 같으나 **하나를 골라 명시**한다.
3. **`motshift` 는 대조로 표기한다**(§0.4-D). 세 번째 행을 독립 arm 처럼 세면 안 된다.

**부수 확인 1 — sub-07 저커버리지는 이 결론을 흔들지 않는다 (2026-08-24 신규).** sub-07 의 hV4 는 아틀라스 70복셀 중 16복셀만 남고 사용 가능한 런도 6개 중 5개다. 그러나 그 피험자의 hV4 성적은 세 arm 에서 .400 / .600 / .400 으로 **통제군 평균 근처이거나 그 위**이고(`motreg` 에서는 7명 중 2위), 제외해도 게이트가 유지된다.

| arm | 통제군 평균 $n{=}7 \to n{=}6$ | 게이트 $p$ | deutan $p$ | protan $p$ |
|---|---|---|---|---|
| `with_residuals` | 0.456 → 0.465 | .011 → **.008** | .054 → .063 | .011 → .017 |
| `motreg` | 0.458 → 0.434 | .013 → .041 | .148 → .183 | .204 → .246 |
| *`motshift`* | 0.483 → 0.497 | .002 → .002 | .229 → .219 | .056 → .061 |

**"저커버리지 피험자가 통제군 보간 성적을 끌어내려 결손이 과장됐다"는 반론은 성립하지 않는다.** 산출 `results/sub07_leaveout_hV4.json`, 스크립트 `scripts/_sub07_leaveout.py`.

다만 처리 방식이 분석마다 다른 것은 별개 문제다. SRM 계열은 같은 피험자의 hV4 를 결측으로 빼고 LOCO 는 넣는다. **Methods 에 규칙과 그 근거를 한 문장으로 명시할 것.**

**부수 확인 2 — 효과크기로는 대체할 수 없다 (2026-08-24 신규).** 단일사례 효과크기에 Crawford–Garthwaite 비중심 $t$ 구간을 붙이면 이렇게 된다($n=7$).

| arm | case | $d_{cc}$ | 95% CI |
|---|---|---|---|
| `with_residuals` | deutan | $-2.02$ | $[-4.33,\ +0.42]$ |
| `with_residuals` | protan | $-3.25$ | $[-5.93,\ -0.41]$ |
| `motreg` | deutan | $-1.23$ | $[-3.38,\ +1.02]$ |
| `motreg` | protan | $-0.95$ | $[-3.08,\ +1.24]$ |
| *`motshift`* | deutan | $-0.85$ | $[-2.96,\ +1.33]$ |
| *`motshift`* | protan | $-2.00$ | $[-4.30,\ +0.44]$ |

**0 을 넘지 않는 유일한 칸조차 구간이 $[-5.93,\ -0.41]$ 로 하한과 상한이 14배 차이 난다.** 이 표본에서 효과의 **크기는 추정되지 않는다.**

→ **조치**: 효과크기를 유의성의 대체물로 쓰지 않는다. 구간은 §S2 에 싣되(리뷰어가 직접 계산할 수 있는 양이므로 선제 공개가 안전하다) 본문에는 **"the magnitude of the reduction is not estimable at this sample size"** 한 구를 붙인다. 주장을 지는 것은 **순위 배치**이며, 순위 진술은 분포 가정도 구간도 필요 없어 표본이 작을수록 상대적으로 유리한 유일한 형태다.

### 2.10 `:66` 주변 — sub-09 V1 의 45° 회전 (신규 · 2026-08-24) ★ 기여 1 → 기여 2 의 실질적 다리

**왜 필요한가.** 현행 원고는 "기하가 왜곡되어 있다"(기여 1)와 "그 왜곡을 hue 회전 2성분으로 모형화해 역산한다"(기여 2)를 **주장으로만** 잇는다. 왜곡이 실제로 **회전**이라는 직접 증거가 본문에 없다. sub-09 V1 의 순환이동 결과가 정확히 그 증거이고, 지금 내부 문서에만 있다.

**소견**: sub-09 의 V1 기하는 항등 대응에서 9명 중 disparity 가 가장 높지만($d$ = 1.037, $z_{cc}$ = $+2.28$), **hue 를 한 단계(45°) 돌려 대응시키면 0.788 로 통제군 평균 아래로 내려간다**($z_{cc}$ = $-0.59$). 기하가 무너진 것이 아니라 **회전되어 있다**는 뜻이다. 같은 사실이 `p_perm` = .758(항등 기준 색 특이성 없음)의 정체를 설명한다.

**본문 문안 (Results, 기하 절 끝 · 기여 2 로 넘어가기 직전)**

> The elevated disparity in the protan participant's V1 was not a loss of structure but a rotation of it. Rematching the eight hues under a one-step ($45^\circ$) cyclic shift reduced the disparity from $1.04$ to $0.79$, below the control mean, whereas the identity correspondence gave the highest value of any participant. Across the eight possible shifts the protan gain exceeded the control distribution of best-shift gains ($24.0\%$ vs $3.5 \pm 5.9\%$, $p = .009$), and both the optimum shift and its excess reproduced under motion regression ($19.2\%$, $p = .025$). The deutan participant's optimum was the identity in every region. This is the empirical form the two-component model inverts.

**근거 (신규 검정, 2026-08-24)** — 최적이동 이득 = $(d[\text{항등}] - d[\text{최적}])/d[\text{항등}]$, Crawford–Howell 단측 상단

| arm | ROI | 통제군 이득 | 통제군 최적이동 | deutan | protan |
|---|---|---|---|---|---|
| `with_residuals` | **V1** | $3.5 \pm 5.9\%$ | 0° ×4, 180° ×3 | 0° · 0.0% · $p$=.70 | **45° · 24.0% · $p$=.0091** |
| `motreg` | **V1** | $4.9 \pm 5.5\%$ | 0° ×3, 180° ×2, 45°·225° ×1 | 0° · 0.0% · $p$=.78 | **45° · 19.2% · $p$=.0254** |
| `with_residuals` | V2 / V3 / hV4 | 1.6 / 0.6 / 7.4% | — | 0 / 0 / 225° | 0 / 0 / 225°, 전부 n.s. |
| `motreg` | V2 / V3 | 0.4 / 0.9% | — | 0 / 0° | 180° / 0°, n.s. |

**선택편향 유보가 이 검정으로 해소된다.** `RESULTS_GEOMETRY_VALIDITY_2026-08-05` §4 유보 1은 "8개 중 최솟값을 취하므로 이득이 편향된다"였다. 그러나 **통제군도 똑같이 8개 중 최솟값을 취하므로 편향이 동일하게 걸리고**, 같은 통계량의 집단 간 대비에서는 상쇄된다. 무작위 대응 귀무분포를 따로 만들지 않아도 된다. 산출 `results/shift_gain_ch.json`, 스크립트 `scripts/_shift_gain_ch.py`.

**⚠ 인용 금지 셀**: `motreg` hV4 protan 은 $p < .0001$ 로 나오지만 통제군 이득 SD 가 $0.4\%$ 로 붕괴한 결과다($t$ = 31). 쓰지 않는다. 주장은 **V1 두 arm** 에만 건다.

**⚠ 남는 유보 (§4.5 순환이동 확장과 함께 한 문장으로 처리)**: 강체 45° 이동은 2성분 모형의 **특수해**다. 모형의 $\delta\theta(\theta)$ 는 hue 마다 회전량이 다르다. 따라서 "45° 균일 이동이 최적" 은 **근사적 부합**이지 모형 적합이 아니며, 원고도 그렇게 써야 한다.

**C1–C8 대응**: 이 항목은 **C4(영역 편재) 아래가 아니라 C6(범주 보존 / 연속 기하 손상의 해리) 아래**에 놓인다. 어느 영역이 왜곡을 지는가를 주장하지 않고, 왜곡의 **형태**가 회전임을 주장하기 때문이다. §0.5 금지 표현에 걸리지 않는다.

---

## 3. `Discussion/discussion_v3.tex`

### 3.1 `:33` — M5 · localization 해석

**현행**

> In both CVD participants the deficit took the form of a structured distortion of cortical color geometry, **localized to a different area in each**. ... **That the two participants' distortions localized to different areas is consistent with the perceptual case.** Among anomalous trichromats, between-observer variability in hue scaling is 3.4 times the within-observer variability \cite{emery2021}.

**교체**

> In both CVD participants the deficit took the form of a structured distortion of cortical color geometry. ... The two participants' deviations differed in magnitude and in fitted direction, which is consistent with the perceptual case. We do not interpret which cortical region carries the largest deviation: the deutan V2 elevation rests on motion-aligned variance and is reported descriptively, so the region contrast between the two participants is not established here. Among anomalous trichromats, between-observer variability in hue scaling is 3.4 times the within-observer variability \cite{emery2021}.

**근거**: `emery2021` 은 **개인차** 근거이지 **부위 편재** 근거가 아니다. 인용은 살리고 주장만 옮긴다.

### 3.2 `:44` `:46` — H · $\hat\beta_c$ 부호 강건성 (rev.3: 2-arm)

**현행 `:44`**

> The two fitted distortions diverge, with $\hat\beta_c = -42^\circ$ in the deutan participant against $+24^\circ$ in the protan participant. The sign of ...

**추가할 것**: 이 대비가 **전처리 축에서 어떻게 되는가.** `hmc_v2` 열은 §0.4-A 결정에 따라 뺀다.

| | baseline | motreg | 판정 |
|---|---|---|---|
| deutan $\hat\beta_c$ | $-42$ | $-48$ | **부호 유지.** 두 arm 모두 재표집 300 중 **음수 300** ($P = 1.00$) |
| protan $\hat\beta_c$ | $+24$ | $-24$ | **부호 반전** |

**protan 의 반전은 분산이 아니라 배타적이다.** baseline 은 300 재표집 중 263 이 $+24$, 나머지 37 이 $0$ — **음수가 한 번도 없다.** motreg 은 218 이 $-24$, 82 가 $-34$ — **양수가 한 번도 없다.** 두 arm 의 지지집합이 부호에서 겹치지 않는다.

**deutan 에 반드시 병기할 단서**: 부호는 유지되나 교란 arm 에서 적합의 조건수가 나빠진다. `motreg` 에서 $\beta_c$ 가 격자 하한에 닿는 비율이 $0.00 \to 0.363$, $\beta_s$ 가 격자 끝에 닿는 비율이 $0.093 \to 0.367$ 로 올라가 **결합 `boundary_rate` 가 $0.09 \to 0.73$** 이 되며, 정본 선택 규칙의 `boundary_rate < 0.5` 문턱을 넘는다. 다만 edge 적중이 두 arm 전부 $-50$ 쪽 **단측**이고 $+50$ 은 0.00 이므로 퇴화는 **크기에만** 있고 부호 주장을 훼손하지 않는다. (크기는 애초에 판정에 쓰지 않는다 — 2성분 모형 12/12 절대복구 실패 → descriptive embedding)

**문안 (§S16 신설 또는 `:46` 뒤)**

> Refitting the same loss combination on the motion-regression arm, with every other element of the procedure held fixed, preserved the sign of $\hat\beta_c$ for the deutan participant ($-42$ and $-48$; negative in all 300 resamples on both arms) and reversed it for the protan participant ($+24$ to $-24$, with the two resample distributions sharing no sign). The fit for the deutan participant was more poorly conditioned on the perturbed arm, the fraction of resamples reaching a grid boundary rising from $0.09$ to $0.73$; these boundary solutions lie on the same side as the median, so they bear on the magnitude rather than the sign. The psychophysical atoms do not depend on preprocessing, so the neural term is the only component that differs between the arms.

**연쇄 조치**: protan ambiguity 문장을 **전처리 축까지 확장**한다(사전 확정 분기 B).

### 3.3 `:48` 뒤 — F · U10 · 균일 회전 항 부재

모형에 **균일 회전 항이 없다**는 사실을 명시. 정본 `REVISION_PLAN_MOTION_GEOMETRY_2026-08-06` §5 가 요구했으나 `discussion_v3.tex` 에 없다(grep 확인). (등급: 필수)

**문안** (`discussion_v3.tex:48` 문단 끝)

> The present model represents distortion of the confusion and S-cone axes and carries no uniform rotation term, so the whole-wheel relabeling recorded at V1 in the protan participant (Supplementary~\S S13) lies outside what it can express. Extending the model to that component is left to future work.

**근거**: §S13 이 protan V1 의 45° 재배열을 보고하는데, 2성분 모형은 균일 회전을 구조적으로 표현할 수 없다($\overline{\delta\theta} = 0$). **§4.5 의 C 를 반영하면 §S13 이 더 주목받으므로 이 구멍이 더 노출된다** — C 와 함께 반영해야 한다.

### 3.4 `:60` — 한계 문단 확장

**현행**

> Two of the reported estimates depend on analysis choices. The deutan V2 disparity elevation is significant in the common HC space and falls to a non-significant trend under the symmetric leave-one-subject-out control, whereas the protan V1 elevation is significant under both.

**교체**

> Several of the reported estimates depend on analysis choices. The deutan V2 disparity elevation is significant in the common healthy-control space, falls to a non-significant trend under the symmetric leave-one-subject-out control, and is removed by motion regression while surviving the time-shifted control, which places it on motion-aligned variance. The protan V1 elevation is significant under every one of these (leave-one-subject-out $p = .045$, $.022$, $.031$). The single-case interpolation contrasts at hV4 do not reach significance once motion parameters are added, and the magnitude of those contrasts is not estimable at this sample size. The control-level result that fixes hV4 as the only interpretable region for interpolation is unaffected by any of these choices (Supplementary~\S S2). We therefore treat the deutan region assignment as descriptive and do not claim that the two participants' distortions are localized to different areas.

### 3.5 `:69` — M6 · 결론

```diff
- whereas the continuous hue geometry departed from the HC reference, at a different cortical area in each.
+ whereas the continuous hue geometry departed from the HC reference in both.
```

### 3.6 Introduction 마지막 문단 — F3 ⚠ **문안 없음 · 전제 재확인 필요**

원 지시(`FRAMING` §6): 기여 진술을 **해리 + 프레임워크** 2축으로 재배치. "현재는 개인차 발견이 1축으로 서 있다."

**⚠ 이 전제는 현행 `introduction_v2.tex` 와 맞지 않는다** (2026-08-24 대조). 마지막 문단은 이미 C5 를 준수한다 — `Each is defined at the level of the single observer, the level at which any correction must ultimately act` 는 **방법의 속성** 진술이고, `This study tests the feasibility of the inversion` · `It does not test whether per-person correction outperforms a subtype average` 로 개인차를 발견으로 주장하지 않는다. 4문 구조(Describe/Summarize/Correct/Validate)와 Gap 1–3 도 손댈 곳이 없다.

**실제로 비어 있는 것은 기여 1(해리)이다.** 마지막 문단이 기여 2(프레임워크)만 진술하고 끝난다. 최소 조치는 해리 축 한 문장 추가이며, 아래는 **신규 초안**이므로 반영 전 확인이 필요하다.

> 초안 — `Together, these steps yield a filter built for one individual.` 앞에 삽입
>
> The first two questions ask what the cortical representation of CVD retains and what it loses, and their answer stands on its own: a representation whose categorical content survives while its continuous geometry does not is not described by a uniform reduction in signal.

**판단**: 등급 **권장**으로 강등한다. 필수가 아니다.

---

## 4. `Supplementary/supplementary.tex`

### 4.0 §S2 `Susceptibility distortion` 문단 — SDC 변위 실측 ★ **신규 항목** (등급: 필수)

> 2026-08-24 추가. 이 항목은 종전 CONSOLIDATED 에 **누락**돼 있었다(§8 근거색인에 산출물 경로만 있었다). 원 근거 = `STATUS_ADDITIONAL_ANALYSIS_2026-08-15.md` §3.4e(3).

**현행 `supplementary.tex:74`**

> Distortion displaces signal along the phase-encoding direction, which ran right to left. Within a participant it is constant across conditions, so **it cannot generate condition-specific differences** among the eight colors. Its cost is spatial, and it reduces the precision with which atlas-defined regions are assigned to functional voxels.

**문제**: `cannot` 은 방어 불가다. 우리가 한 것은 **필드맵에서 유도한 변위 크기 측정**이지, **SDC 를 실제 적용한 BOLD 에서 LOCO/RDM 을 재계산한 것이 아니다.** 측정이 직접 입증하는 것은 "왜곡이 후두 시각 ROI 에서 작고 ROI 내 공간 변이가 서브복셀"까지이며, hV4 처럼 작은 ROI 에서 **완전 무영향을 수학적으로 보장할 수는 없다.**

**교체 문안** — 숫자를 그대로 쓰고 추론 강도를 낮춘다

> Field-map-derived susceptibility displacement was measured within each analyzed ROI in all nine participants. Mean displacement ranged from 0.01 to 0.76 voxels (0.02--1.52 mm). Within-ROI spatial variation, the component that distorts a pattern rather than translating it, was 0.05--0.21 voxels (0.10--0.42 mm) in eight participants, with a 5th--95th percentile range of 0.15--0.72 voxels; in the remaining participant it reached 0.38 voxels (0.76 mm) with a 5th--95th percentile range of 1.19 voxels. Susceptibility distortion within these posterior visual ROIs was therefore predominantly subvoxel and spatially smooth, making it unlikely to account for the observed differences in representational geometry across color conditions.

**어휘 규칙**

| 금지 | 허용 |
|---|---|
| `cannot alter relative geometry` · `cannot generate condition-specific differences` | `is less likely to distort within-ROI representational geometry than spatially varying displacement` |
| `no effect` / `무시 가능` | `predominantly subvoxel and spatially smooth` |
| 균일 성분을 "상쇄된다" 로 단정 | 균일 성분은 **덜 우려스럽고**, **미분 성분이 직접적인 pattern-distortion term** 이라고 기술 |

**"적용하지 않았다"가 "크기를 재어 보고했다"로 바뀐다.** `+sdc` arm 으로 종점을 재계산하지 않고도 달성되며, **단 그 한계를 위와 같이 명시할 때만** 성립한다. PE 부호 확정은 불필요하다 — ROI 내 이동이 거의 균일·서브복셀이라 부호를 어느 쪽으로 잡든 ROI 기하 영향이 같은 규모다.

**산출**: `analysis/phase0_preprocessing/results/roi_shift_summary.csv`, `figures/sdc_cohort/`

---

### 4.1 §S2 — A · LOCO 3-arm 표 + 범위 정정

`every neural endpoint` 문장의 **범위를 정정**하고 LOCO 3-arm 표를 신설. (등급: 필수)

**(a) 현행 `supplementary.tex:46` 첫 문장 교체**

```diff
- Every neural endpoint was recomputed with the six motion parameters and their temporal derivatives added to the second-level design matrix.
+ Every neural endpoint of the first session was recomputed with the six motion parameters and their temporal derivatives added to the second-level design matrix. The filter-evaluation session was not recomputed, since its endpoints are reported descriptively and carry no inferential claim.
```

**(b) 신설 문단 + 표** (기존 `tab:motion_arms` disparity 표 뒤)

> \paragraph{Interpolation under the motion arms.}
>
> Adjacent accuracy at hV4 was recomputed on all three arms under the design of \S S8, with the healthy-control permutation repeated at $N = 1{,}000$ per arm (\cref{tab:motion_loco}). The control gate held throughout: hue interpolation exceeded its own color-label null at hV4 in every arm, and at no other region in any arm. The single-case contrasts did not. The control mean was unchanged across arms while the control standard deviation rose from $0.102$ to $0.152$ under motion regression and to $0.127$ under the shifted control. Because the shifted regressors remove no motion-aligned variance, that inflation is attributable to the twelve added regressors rather than to motion. Leave-one-color-out trains on seven colors per fold, so it carries less residual degrees of freedom than the geometric endpoints and loses precision faster when regressors are added. The single-case interpolation contrasts are therefore reported from the primary arm, with the arms tabulated here.

```latex
\begin{table}[h]
\centering
\caption{Adjacent accuracy at hV4 across the three preprocessing arms. Control values are the mean over seven controls with the permutation $p$ against $N = 1{,}000$ per-subject color-label shuffles. CVD entries give adjacent accuracy with the Crawford--Howell one-tailed $p$ and $d_{cc}$ against the same controls.}
\label{tab:motion_loco}
\begin{tabular}{lccccc}
\toprule
 & \multicolumn{3}{c}{Healthy controls} & Deutan & Protan \\
\cmidrule(lr){2-4}\cmidrule(lr){5-5}\cmidrule(lr){6-6}
Arm & mean & SD & $p_{\rm perm}$ & acc ($p$, $d_{cc}$) & acc ($p$, $d_{cc}$) \\
\midrule
Original          & $0.456$ & $0.102$ & $.011$ & $0.250$ ($.054$, $-2.02$) & $0.125$ ($.011$, $-3.25$) \\
Motion regression & $0.458$ & $0.152$ & $.013$ & $0.271$ ($.148$, $-1.23$) & $0.312$ ($.204$, $-0.95$) \\
Shifted control   & $0.483$ & $0.127$ & $.002$ & $0.375$ ($.229$, $-0.85$) & $0.229$ ($.056$, $-2.00$) \\
\bottomrule
\end{tabular}
\end{table}
```

**⚠ rev.3 개정**: 종전에는 이 표(3 arm)와 §4.3 `tab:hmc_robustness`(2 arm: primary/realigned)가 병존했다. **§4.3 은 폐기됐으므로 이 표가 §S2 의 유일한 arm 표가 된다.**

**표에 반드시 붙일 두 가지**

1. **`Shifted control` 행에 대조 표기.** 캡션에 한 문장을 넣는다(§0.4-D): *The third row carries the same twelve regressors circularly shifted within run, preserving their autocorrelation and spectrum while destroying their temporal alignment with the data. It is a control for the cost of adding regressors, not an independent preprocessing variant.*
2. **$d_{cc}$ 옆에 95% CI 추가.** Crawford–Garthwaite 비중심 $t$ 구간(§2.9 부수확인 2). 리뷰어가 직접 계산할 수 있는 양이므로 선제 공개가 안전하다.

### 4.2 §S2 재정렬 문단 · 4.3 `tab:hmc_robustness` — ⚠ **둘 다 폐기 (2026-08-24)**

> **종전 안**: §S2 에 `\paragraph{Realignment.}` 를 신설하고 `tab:hmc_robustness`(primary vs realigned 8행)를 싣는다.
>
> **폐기 사유**: §0.4-A 결정으로 `hmc_v2` 를 원고에서 제외한다. 재정렬 미적용의 서술은 **§1.5 Methods 문단**이 담당하며, 부록에는 별도 절도 표도 두지 않는다.

**이관된 내용**

| 종전 위치 | 새 위치 |
|---|---|
| 재정렬 미적용 서술 | **§1.5 (Methods 본문)** |
| tSNR $1.7$–$3.0\%$ · ROI 겹침 $<0.6\%$ | §S2 전처리 정당화 문단 (§1.5-c) |
| 종점 8행 표 | **삭제.** arm 표는 §4.1 `tab:motion_loco` 하나로 통합 |
| ICC 2행 | **삭제** (§0.4-C) |

**⚠ 종전 §4.2 의 프레이밍 금지 사항은 §1.5-(b) 로 승계된다.** 특히 *"품질 수치로 종점을 기각하지 않는다"* 는 원칙은 유효하다. §1.5 본문이 tSNR 을 인용하지 않고 변위 크기와 보간 논거만 쓰는 이유가 그것이다.

### 4.4 §S2 / §S3 — G + BBR QC 그림

**Dice 표를 인용하지 않는다.** 아카이브 정량 지표(BBR Dice 0.33–0.50 vs MI 0.27–0.36; ROI coverage 99.95% vs 85.4%)는 **BBR 을 지지한다** — 이 지표들이 "슬랩이 뇌 안에서 잘못된 위치에 안착"하는 실패 모드에 둔감하기 때문이다. 게다가 아카이브 method3 는 FSL MNI152 로 돌아 현행 정본(MNI152NLin2009cAsym res-2)과 공간이 다르다.

**근거는 서술로만 남긴다** (2026-08-17 결정 — QC 그림 제작 제외). 방법 이력 진술이지 결과 주장이 아니므로 그림 없이 성립하며, 아래 선제 공개가 있으면 리뷰어가 Dice 를 직접 계산해도 반박이 되지 않는다. 근거는 채택 당시 기록(`notion.md:29-35`)이다.

두 층위를 **같이** 써야 완성된다.

| 층위 | 시도했고 실패한 것 | 정당화하는 것 |
|---|---|---|
| 파이프라인 | fMRIPrep 정합 전 시도 실패 | 커스텀 파이프라인을 쓴 것 |
| 정합 방법 | BBR 육안 실패 — partial FOV 에서 잘못된 경계 스냅 (10 mm 오차 위험 vs MI ~1 mm) | 커스텀 안에서 MI 를 고른 것 |

이렇게 써야 "표준을 안 썼다"가 아니라 **"표준을 시도했고, 이 취득에서 실패한 측정된 이유를 보고한다"** 가 된다. **"전뇌 중첩 지표는 BBR 을 선호하나 슬랩 오위치에 둔감하다"를 선제 공개**하는 편이 안전하다.

### 4.5 §S13 (`supplementary.tex:464-468`) — C · 순환이동 대조 확장

순환이동 대조를 **색 특이성 순열**까지 확장. (등급: 필수) — **현행 마지막 문장이 미완료를 자인한다**: `The circular-shift control ... remains to be extended to the permutation reported here.`

**결과 — 해석 2(회귀자 부산물)가 기각된다.** 35 셀 BH-FDR, arm 내 보정.

| arm | raw $p<.05$ | **BH $q<.05$** |
|---|---|---|
| 원본 | 16 / 35 | **7** |
| 움직임 회귀 | 18 / 35 | **15** |
| **순환이동 대조** | 13 / 35 | **3** |

순환이동은 같은 회귀자 12개를 **시간 정렬만 파괴한 채** 넣는다. 해석 2 가 맞다면 15 근처여야 한다. **3 이다** — 원본 7 보다도 낮다. → 7 → 15 증가는 **회귀자가 데이터와 시간 정렬돼 있을 때만** 나타나므로 **움직임 분산 제거**에서 온다.

**CVD 셀 분해** (움직임 귀속분 = 회귀 − 순환이동)

| | 원본 | 회귀 | 순환이동 | 움직임 귀속 |
|---|---|---|---|---|
| deutan V1 | .105 | **.009** | .466 | **−0.457** |
| deutan **V2** | **.002** | **.003** | **.009** | −0.006 |
| deutan V3 | .024 | **.005** | .077 | −0.072 |
| deutan hV4 | .273 | **.029** | .774 | **−0.745** |
| protan V1 | .758 | .737 | .518 | +0.219 |
| protan V2 | **.013** | .084 | .155 | −0.071 |
| protan **V3** | **.001** | **.001** | **.032** | −0.031 |
| protan hV4 | .129 | .201 | .364 | −0.163 |

**문안 — 현행 L464-468 전체를 교체**

> Motion regression broadened the pattern rather than removing it. The count of cells surviving correction rose from 7 to 15, and the deutan V2 cell held at $q = .025$ while the protan V3 cell held at $q = .012$. We extended the circular-shift control of S2 to this permutation to decide whether the increase reflects the removal of motion-aligned variance or a reshaping of the residual variance by the twelve added regressors. The shifted regressors carry the same autocorrelation and spectrum without temporal alignment to the data, so they impose the cost of the added regressors while removing no motion. Under the shifted control only 3 of the 35 cells survived correction, fewer than the 7 of the primary arm. The increase therefore requires the regressors to be aligned with the data and is attributable to motion-aligned variance; the cost of adding twelve regressors, taken alone, lowers detection. The two cells that survive correction in the primary arm survive in all three arms (deutan V2, $p = .002$, $.003$, $.009$; protan V3, $p = .001$, $.001$, $.032$). The deutan V1 and hV4 cells reach significance only once motion-aligned variance is removed ($p = .105 \to .009$ and $.273 \to .029$, against $.466$ and $.774$ under the shifted control).

> This endpoint moves in the opposite direction to the interpolation contrasts of S2, and the two are consistent. The permutation compares a participant to a label-shuffled null computed within the same participant and arm, so an inflation of between-subject dispersion does not touch it, whereas the single-case interpolation test is referred to the control distribution and is directly exposed to that inflation.

**⚠ §4.1 A 와 방향이 반대인 것은 모순이 아니다** — 두 검정의 귀무가 다르다. 회귀자 추가는 **피험자 간 산포를 팽창**시켜 단일사례 검정(Crawford–Howell 분모)에 불리하고, 움직임 제거는 **피험자 내 색 대응을 선명하게** 해 순열에 유리하다. 위 두 번째 문단이 이것을 원고에서 직접 처리한다 — **반드시 함께 넣는다.**

### 4.6 §S15 `tab:jnd_baseline` — D · 범위 절단 각주

sub-08 orange–yellow 가 **범위 절단 하한**임을 각주. (등급: 필수)

**근거**: 13개 trial 파일 **208 staircase 전수 스캔**. 제시 가능한 최대 수준 0.95 에서 오답을 낸 staircase 는 **정확히 2개**이고 둘 다 sub-08 세션-1 orange–yellow(sc0, sc1)다. → 보고된 역치 $t = 0.840$ ($\gamma = 3.02$, $z = +4.15$) 은 추정치가 아니라 **하한**이다. **방향은 보수적** — 기준선 결손이 실제보다 작게 적혀 있었으므로 필터 개선폭도 과소 보고. 값은 고치지 않고 절단 사실만 밝힌다.

**문안 (a) — `tab:jnd_baseline` 캡션 끝에 추가**

> Two staircases returned an incorrect response at the largest presentable separation, both of them the deutan participant's orange--yellow pair, so that threshold is a lower bound rather than an estimate; it is the only such pair among the 208 staircases collected in this study.

**문안 (b) — §S15 본문 끝에 추가**

> The deutan orange--yellow staircases spent their whole course at the top of the presented range and returned incorrect responses at the largest separation the task can present. That threshold is therefore censored, and the true value lies at or above the tabulated one. The censoring understates the baseline deficit and, with it, the improvement recorded under either filter, so the values are reported unadjusted.

**산출**: `analysis/phase6_behavioral_analysis/results/exp2_behavior/a2_staircase_diagnosis.json`

### 4.7 H 문안의 배치 — ⚠ **"§S16 신설" 은 stale 번호**

§3.2 의 문안을 부록에 둘 경우의 위치. **단, 현행 `supplementary.tex` 의 S16 은 이미 `Comparison with Retinal-Family Distortion Models` 이다** (실제 절 S1–S21). 구 S1–S19 표 기준의 "S16 신설"을 그대로 실행하면 S16 이하가 전부 밀려 **§6 I3 이 막 해소한 번호 문제가 재발한다.**

**권고: 부록 신설 없이 `discussion_v3.tex:46` 뒤 본문에 둔다.** 부록에 꼭 넣어야 한다면 **S18 `Identifiability checks` 안의 문단**으로 붙인다 — $\hat\beta_c$ 부호 강건성은 정확히 identifiability 항목이고, 새 절 번호를 만들지 않는다.

### 4.8 `:815` — 비교자 범위 문서화 ★ 신규

**현행**

> The deployed comparator was the macOS accessibility Color Filter (System Settings $>$ Accessibility $>$ Display, build 26.5.1), set at an intensity the participant self-t…

비대칭 **자체는 이미 공개**되어 있다. 빠진 것은 **범위와 GLM 함의**다.

**코드에서 확정한 사실 (2026-08-16, `colorBlind_exp2.py`)**

| | `window` 조건 (배포 비교자) | `optimal` 조건 (개인화) |
|---|---|---|
| 구현 | 원본 색 렌더 + **진행자가 노트북 OS 필터 ON** (`:723`, `:741`) | PsychoPy 내부 CIELab hue 회전, **OS 필터 OFF** (`:733`, `:744`) |
| 원반 | OS 합성 변환 | 명세 단계에서 회전 |
| 회색 filler (`blank`) | **OS 합성 변환을 통과** | **불변** — `rotate_hue_lab` 이 채도 0 에서 no-op (`:150`), `build_color_rgb` 이 `blank` 를 회전 대상에서 제외 (`:169`) |
| 배경 `#333333` · 주시점 `#FFFFFF` · 문자 | OS 합성 변환을 통과 | 불변 |

**핵심 — 등휘도 설계가 배포 조건에서만 깨진다.** 자극 8색은 **전부 $L^* = 75$** 로 정의되어 있고(`COLOR_LAB`, `:81-90`), 개인화 필터는 `rotate_hue_lab` 이 *"keep L\* and chroma"* 로 **$L^*$ 를 구조적으로 보존**한다(`:149-156`). 배포 macOS 필터는 합성 변환이고 **밝기를 이동시킨다**(사용자 관찰, 2026-08-16). 즉 등휘도라는 설계 속성이 **`window` 조건에서만** 깨진다.

**문제는 평균 밝기 이동이 아니다.**

| 성분 | 흡수되는가 |
|---|---|
| **공통 $L^*$ 이동** (8색 전부 같은 방향) | 조건별 Procrustes + 상관 기반 LOCO 가 대체로 흡수 |
| **색상 의존 $L^*$ 이동** (색마다 다르게 움직임) | **흡수되지 않는다.** 등휘도가 깨져 **휘도 자체가 판별 단서**가 된다 |

CVD 교정 필터는 채널 이득을 재분배하므로 후자가 발생할 개연성이 높고, V1 은 특히 휘도에 민감하다. 비-원반 요소(`blank` = $L^*75\,a^*0\,b^*0$, 배경 (51,51,51), 주시점 백색)는 전부 무채색이므로 이쪽은 **공통 성분**에 해당한다.

**아직 실측되지 않았다.** `data/color_screenshot/` 의 8장은 **필터 OFF 상태의 개발용 데스크톱 스크린샷**이고(메뉴바·독 아이콘 정상 색, PsychoPy 창 배경 (51,51,51) 균일), 필터 ON 짝이 없다.

→ **필요한 실측**: sub-08·sub-09 에 쓴 것과 **동일한 macOS 필터 설정**에서 8색 각각을 스크린샷해 $L^*$ 를 산출한다. 보고할 값은 두 개다.

> **기준값은 계산하지 말고 측정한다.** PsychoPy 렌더링에 보색 처리가 있어 `lab2rgb` 출력을 그대로 8-bit 로 환산한 값은 **화면에 표시되는 색이 아니다** (2026-08-17 확인, 실험 스크립트 8개에 주석 기록). 따라서 필터 OFF 기준값도 **동일 조건 스크린샷에서 읽어야** 한다. 필터 ON/OFF 두 벌을 같은 세션에서 찍으면 이 문제가 자동으로 해소된다.

1. **평균 $L^*$ 이동** — 공통 성분, 대체로 흡수됨
2. **8색 간 $L^*$ 산포** — 차등 성분, **이것이 실제 교란**

| 실측 결과 | 원고 서술 |
|---|---|
| 산포 ≈ 0 | 등휘도가 실질적으로 유지된다고 적을 수 있다. 공통 이동만 한 문장으로 공개하고 종결 |
| 산포 유의 | 배포 조건에서 **등휘도가 깨지고 휘도가 부수 단서로 들어갔음**을 공개. 배포 비교자의 신경·행동 값 전부에 단서를 단다 |

**방향은 측정 전에 단정하지 않는다.** 휘도 단서가 추가되면 판별이 쉬워지므로, 배포 조건이 **그럼에도** 열세였다는 사실(protan 8AFC $0.86$ vs $0.98$; green–blue 역치 $+2.4 \to +5.1$ 악화)이 오히려 강해진다. 그러나 OS 필터가 전반적으로 어둡게 만들어 대비가 떨어지면 반대로 불리해진다. **평균 이동과 산포를 함께 봐야 갈린다.**

**왜 중요한가**: exp2 종점은 **조건별 Procrustes** 를 거친 진폭 위에서 계산된다. 색상 의존 휘도 성분이 배포 조건에만 들어가면, 배포 필터의 신경값(protan hV4 $0.19$)에 개입 효과가 아닌 성분이 섞인다. JND 도 마찬가지로, 쌍 구성원 간 휘도차가 생기면 색상 판별이 아닌 판별이 될 수 있다.

**정직하게 적을수록 우리 위치가 나아질 가능성이 높은 항목이다** — 단, 그 진술은 실측 후에만 할 수 있다.

### 4.9 §S2 — `exp2` 종점의 전처리 arm 재산출 ★ 신규 (2026-08-17)

Q3 은 "미실시를 명시할 것인가"였으나, ses-2 디페이싱이 완료되어 **재산출로 해소**했다. exp2 를 `anat_harmonized` + 단일보간 재정렬로 다시 처리하고 사전 확정 종점 14칸을 재계산했다. HC 기준과 exp1 무필터 앵커도 같은 재정렬 arm(`full_dataset_C010_hmc_v2`)으로 맞춰 **양쪽이 arm 을 섞지 않게** 했다.

**hV4 LOCO adjacent accuracy (주 종점)**

| | NoFilter | Window | Optimal | HC $n{=}4$ |
|---|---|---|---|---|
| deutan 정본 | 0.231 | 0.250 | 0.312 | 0.456 |
| deutan harm | 0.342 | 0.156 | 0.281 | 0.445 |
| protan 정본 | 0.138 | 0.188 | 0.062 | 0.456 |
| protan harm | 0.263 | 0.094 | 0.344 | 0.445 |

**사전지정 결손 ROI, LOCO $\rho$ (native)**

| | NoFilter | Window | Optimal | HC |
|---|---|---|---|---|
| deutan V2 정본 | $-0.211$ | $-0.190$ | $0.098$ | $0.162$ |
| deutan V2 harm | $0.196$ | $0.113$ | $0.087$ | $0.080$ |
| protan V1 정본 | $-0.020$ | $-0.096$ | $0.129$ | $0.129$ |
| protan V1 harm | $0.258$ | $0.023$ | $-0.002$ | $0.016$ |

**판정 — variant 별로 세야 한다.** `native` 와 `matched` 는 같은 데이터에 복셀 마스크만 달리 적용한 것이라 독립 검정이 아니다. 둘을 합쳐 "20 중 13" 으로 세면 분모가 부풀려지고 **arm 불일치와 variant 불일치가 섞인다.**

| variant | 방향 대비 | arm 간 역전 |
|---|---|---|
| `native` | 10 (2명 × 5대비) | **8** |
| `matched` | 10 | **5** |

5대비 = hV4 Opt>Win · hV4 Opt>NoFilter · RDM Opt>Win · LORO Opt>Win · 결손ROI Opt>Win.

**두 variant 자체도 서로 불일치한다.** `deutan_V2_opt_gt_win` 은 native 에서 역전(True→False)이나 matched 에서는 유지(True→True)이고, `protan_V1_opt_gt_win`·`protan_rdm_opt_gt_win` 도 같다. 즉 exp2 신경 종점은 **전처리 arm 과 복셀 마스크 선택 양쪽 모두**에 민감하다.

**SRM Procrustes disparity (run-count-matched, 낮을수록 HC 기하에 근접)** — 주 종점과 **다르게 거동한다**

| | HC | NoFilter | Window | Optimal |
|---|---|---|---|---|
| deutan V2 정본 ←사전지정 | 0.443 | 0.676 | 0.870 | **0.766** |
| deutan V2 harm | 0.491 | 0.498 | 0.683 | **0.570** |
| protan V1 정본 ←사전지정 | 0.429 | 0.700 | 0.657 | **0.626** |
| protan V1 harm | 0.481 | 0.602 | 0.503 | **0.442** |
| deutan hV4 정본 / harm | 0.695 / 0.668 | 0.872 / 0.770 | 1.004 / 0.825 | **0.901 / 0.675** |
| protan hV4 정본 / harm | 0.695 / 0.668 | 0.833 / 0.940 | 0.845 / 0.830 | 0.876 / **0.624** |

**8개 방향 대비 중 3개 역전** (2명 × 2 ROI[사전지정·hV4] × 2 대비; `matched` 단독이므로 위 LOCO 표와 세는 단위가 다르다). 사전지정 결손 ROI 의 4개 대비는 **전부 유지**되고, `Optimal < Window` 는 16행 중 13행에서 성립한다.

**⚠ 이것을 근거로 종점을 교체하지 않는다.** 사전 선언된 주 종점은 **hV4 LOCO adjacent accuracy** 이고(산출 로그도 `*** PRIMARY ENDPOINT (hV4) ***` 로 명시), 그것이 불안정한 쪽이다. "기하가 안정적이니 그쪽을 보자"는 사후 종점 교체다. **정확한 진술** = *사전 선언된 주 종점은 arm 간에 불안정하고, 수렴 지표인 기하는 더 안정적이며 사전지정 ROI 에서 방향이 유지된다.*

**⚠ 디스패리티는 절대값을 인용하지 않는다.** HC 기준 자체가 arm 간에 이동한다(V1 $0.429 \to 0.481$, $+12\%$). LOCO 에서 HC 가 $0.456 \to 0.445$ 로 거의 불변이었던 것과 대비된다. **순서만 안정적이고 절대값은 arm 의존적이다.**

모든 CVD 조건이 HC 보다 나쁘다(단측 $p$ 전부 $.99$ 대) — 현행 `neither reached the healthy reference` 그대로다.

> **⚠ 서로 다른 세 개의 수를 혼동하지 말 것.**
>
> ① **재산출 종점 20칸** = 측정 셀의 수 ($6+6+6+2$). `STATUS` §4.4 의 라벨은 "14칸" 으로 합과 맞지 않는다 — 어느 쪽이 사전 확정본인지 확인 필요. 현재는 20칸 전부 산출해 두었다.
>
> ② **방향 대비 10개/variant** = arm 간 부호 비교의 수. ① 과 무관하다.
>
> ③ **disparity 8개 대비** = `matched` 단독, 2 ROI 한정. ② 와도 세는 단위가 다르다.

**흔들리는 것이 무엇인지가 중요하다.** HC 기준은 거의 불변이고($0.456 \to 0.445$), 불안정성은 **단일 피험자·단일 조건 셀**에 국한된다(조건당 4런). exp1 에서 얻은 그림과 정확히 같다 — 집단 수준 구조는 arm 을 견디고 개인 수준 셀은 견디지 못한다.

**새 문제가 아니라 기존 진술의 정량화다.** 현행 초록이 이미 `The direction of cortical change differed across participants and measures, and neither reached the healthy reference` 라고 적고 있다. 이번 결과는 그것을 확증하며 **"분석 선택에 따라서도 방향이 바뀐다"** 는 축을 추가한다.

**⚠ 새 arm 을 주 결과로 채택하지 않는다.** harm arm 에서 protan Optimal 이 Window 를 이기고 RDM cosine 도 올라가 **우리에게 유리해 보이지만**, 그것을 근거로 arm 을 바꾸면 정확히 cherry-picking 이다(정본 arm 의 protan Optimal 은 0.062 로 최악이었다). **두 arm 을 나란히 싣고 어느 쪽으로도 방향 주장을 하지 않는다.**

**손실은 없다.** exp2 신경 종점은 현행 원고에서 이미 우월성 근거로 쓰이지 않는다(그 역할은 심리물리가 한다). **심리물리는 전처리와 무관하므로 전량 불변**이고 기여 2 의 실증 근거도 그대로다.

**문안**

> \paragraph{Session-2 endpoints under the harmonised arm.}
>
> The second session was acquired without the defacing step applied to the first, so we reprocessed it with the anatomical images harmonised and with head-motion realignment, recomputing the fourteen pre-specified endpoints. The healthy-control reference was essentially unchanged (hV4 adjacent accuracy $0.456$ against $0.445$), whereas the single-participant, single-condition cells moved substantially: of twenty directional contrasts, thirteen reversed between arms. Each of those cells rests on four runs from one participant. We therefore report both arms and draw no directional conclusion from the session-2 cortical readouts under either. The psychophysical endpoints do not depend on preprocessing and are unchanged.

> **⚠ rev.3 정합 경고 (2026-08-24)** — §0.4-E. 이 절의 통일 arm 은 **재정렬을 포함해** 처리됐고, 비교의 HC 기준·exp1 무필터 앵커도 `full_dataset_C010_hmc_v2` 로 맞췄다. §1.5 Methods 가 *"정본 파이프라인에는 재정렬을 적용하지 않았다"* 고 적으므로 **모순은 아니지만**, 위 문안에 그 구분이 없다. 두 조치 중 하나를 택한다.
>
> | 선택지 | 내용 | 비용 |
> |---|---|---|
> | **(i) 권장** | 문안에 한 구를 추가한다: `...with the healthy-control reference and the session-1 anchor taken from the same realigned reconstruction, so that the two sessions are not mixed across arms.` | 문안 한 구 |
> | (ii) | exp1 앵커를 **정본 arm 값으로 재산출**해 교체 | 서버 job 1건 |
>
> (i) 이면 재정렬이 세션 2 통일 arm 에만 쓰였음이 독자에게 보이고, Methods 의 `not applied` 가 세션 1 정본을 가리킨다는 것도 분명해진다.

**산출**: `analysis/future_phase1_sensitivity/results/exp2_endpoints_arms.json`, `analysis/future_phase1_sensitivity/results/exp2_disparity_arms.json`, `derivatives/full_dataset_C010_exp2_harm_hmc{,_matched}`

---

## 5. 그림

### 5.1 `fig:geometry` (Fig 4) — Q2

**패널에서 별표를 제거하고 각주로 강등한다.**

**캡션 추가구**

> Asterisks are omitted; arm-wise tests for every region are given in Supplementary~\S S2.

**근거 (rev.3 개정)**: deutan V2 의 별표가 방어되지 않는다. 움직임 회귀에서 사라지고(.218) 시간 정렬을 파괴한 대조에서는 사라지지 않으며(.005), 정본 arm 의 LOSO 추정량에서도 이미 비유의였다(.116). 별표를 남기고 캡션에서만 단서를 다는 것은 그림과 캡션이 서로 다른 말을 하게 만든다. 그림은 발표·인용에서 캡션과 분리되어 유통되므로 **패널 자체에서 제거해야 한다.**

**⚠ protan V1 만 별표를 남기지 않는다.** protan V1 은 세 arm 전부에서 유의하므로 기술적으로는 별표가 가능하지만, 한쪽에만 별표가 남으면 그림이 **"참가자마다 다른 영역"** 을 시각적으로 주장하게 된다. §0.5 금지 표현에 해당한다. **양쪽 모두 제거하고 유의성은 본문·부록에서만 진술한다.**

### 5.2 `fig:loco` (Fig 3)

변경 불필요. 캡션이 이미 측정·기호·검정 방향만 기술한다 (`CLAUDE.md` figure caption 규칙 준수).

---

## 6. 형식·제출 차단 — I

| # | 항목 | 대상 | 상태 |
|---|---|---|---|
| **I3** | ~~`\S S…` 참조 번호표 stale~~ | `Supplementary/REVISION_WORKLIST.md:10-34` | **✅ 해소 (2026-08-17)** — 번호표는 실제 heading(S1–S21)로 정정 완료. 본문 `\S S…` **17건 전수 재검증 17/17 정상** — 참조는 이미 신 번호를 쓰고 있었고 stale 한 것은 표뿐이었다. **원고 수정 불요.** 단 §4.7 참조: 새 절을 삽입하면 이 문제가 재발한다 |
| **I4** | Methods 중복본 6개가 참가자 수를 `Twelve` / `Thirteen` 으로 상충 기술. `main.tex` 는 `methods_v2` 만 `\input` 하나 **코드 공개 시 읽힌다** | `Methods/methods{,_concise,_streamlined,_bibtex,_for_pi}.tex`, `*_backup.tex` | 5분 |
| **I1** | back matter 4절 `\todo{}` 실채움 (CRediT / 이해관계 / 감사 / 데이터 가용성) | `main.tex:110-146` | I2 후 |
| **I2** | **데이터 공개 방침 결정** — 기탁(OSF/OpenNeuro) vs 요청 시 제공. Methods 문장과 Data availability 절을 **함께** 고쳐야 한다 | `main.tex` + `methods_v2.tex` | **IRB 확인 대기** |

---

## 7. 원고 밖 잔여 작업

| # | 작업 | 산출물 | 왜 필요한가 |
|---|---|---|---|
| **1** | **`HMC_REANALYSIS_PRESPEC.md` 에 원고 제외 결정 기록** | 그 문서에 §0.4-A 결정과 사유 추가 | 사전 확정 조항을 따르지 않는 결정이므로 **판단 시점·근거·판단자가 기록으로 남아야** 나중에 방어된다. 기록이 없으면 "결과를 보고 뺐다"와 구분되지 않는다 |
| **1b** | **`TEAM_BRIEF` · `future_phase1_sensitivity/README` 정정** | ICC 0.825 를 "신규 자산"으로 적은 대목에 인용 금지 사유 추가 | 두 문서가 그 값을 본문 승격 대상으로 명시하고 있어, 두면 다음 회차에 또 올라온다 |
| **1c** | **4-arm disparity 통합표 완성** | job 171184 (`motreg`·`motshift` disparity 전량) | §4.1 표에 disparity 행을 붙일지 결정하려면 `motreg` 의 빈 다섯 칸(sub-08 hV4, sub-09 V2·V3 등)이 필요하다. 2026-08-24 제출, node2 대기 중 |
| 2 | **macOS 필터 per-hue $L^*$ 실측** | 필터 ON 8색 스크린샷 + $L^*$ 표 (평균 이동 · 8색 산포) | §4.8 의 두 분기 중 하나를 확정. **배포 조건에서만 등휘도가 깨지므로 비교자 해석 전체가 여기 달려 있다** |
| ~~3~~ | ~~ses-2 ezBIDS 디페이싱~~ | `colorBlind_data/data/2nd_exp/bids_2nd_defaced` | **완료 2026-08-17.** 0 복셀 sub-08 30.9% · sub-09 35.1% (ses-1 30.9% / 33.0%), 중시상면 절단면 형상 4장 동일, 뇌 조직 손실 없음 |
| ~~4~~ | ~~exp2 재전처리 + 종점 14칸 재산출~~ | `full_dataset_C010_exp2_harm_hmc{,_matched}`, `future_phase1_sensitivity/results/exp2_endpoints_arms.json` | **완료 2026-08-17.** native 10개 중 **8개** · matched 10개 중 **5개** 역전. 두 arm 병기, 방향 주장 없음 (§4.9) |
| ~~5~~ | ~~색 라벨 ↔ 렌더 값 방향 확인~~ | 실험 스크립트 8개 주석 | **종결 2026-08-17.** 라벨이 정본(화면 관찰). 겉보기 반전은 PsychoPy 보색 렌더링 |

---

## 8. 근거 색인

| 주장 | 산출물 |
|---|---|
| arm 별 종점 · MAE 순열 | `analysis/future_phase1_sensitivity/results/{perm_adjacent_arm_*,perm_mae_arm,boot_runs_*}.json` |
| disparity arm 비교 | `analysis/validation/results/disparity_arm_{canonical,hmc_v2}.json` · `motreg`·`motshift` = job 171184 (§7-1c) |
| 색 특이성 arm 비교 (§4.5) | `analysis/validation/results/disparity_frozen_permutation_{current,motreg,motshift,hmc_v2}.json` |
| **재정렬 미적용 근거 (§1.5)** | `hmc_reanalysis/server_recovered/README.md`(코드 감사·항등 검사), `phase0_preprocessing/results/hmc_summary.csv`(tSNR), `*_desc-motion.par`(변위) |
| $\hat\beta_c$ arm 비교 | `analysis/phase5_filter_optimization/results/filter_robustness_arms/beta_sign_three_arms.json`, `results/s10_inclusion/u2_{baseline,motreg,hmc_v2}/` — **원고는 `baseline`·`motreg` 두 열만 쓴다** |
| 필터 교차평가 | `results/filter_robustness_arms/filter_robustness_arms.json` |
| 비교자 구현 | `~/…/OneDrive-Personal/Projects/colorBlind/colorBlind_exp2.py:150,169,723,733,741,744,799` |
| SDC 미적용 정당화 | `analysis/phase0_preprocessing/results/roi_shift_summary.csv`, `figures/sdc_cohort/` |
| **순위 배치 (§2.9)** | `analysis/future_phase1_sensitivity/results/perm_adjacent_arm_*.json` 의 `per_subject` |
| **sub-07 제외 재산출 (§2.9)** | `analysis/future_phase1_sensitivity/results/sub07_leaveout_hV4.json`, `scripts/_sub07_leaveout.py` |
| **45° 이동 이득 검정 (§2.10)** | `analysis/future_phase1_sensitivity/results/shift_gain_ch.json`, `scripts/_shift_gain_ch.py` |
| **`hmc_v2` 생성 스크립트 · 코드 감사 · 항등 검사** | `analysis/phase0_preprocessing/hmc_reanalysis/server_recovered/` |

---

## 8.1 인용 금지 수치 — 원고·발표·서신 어디에도 쓰지 않는다

| 수치 | 출처 | 사유 |
|---|---|---|
| **ICC$_{2,1}$ = 0.825 (hV4), $-0.005$ (V1)** | `arm_agreement.json` | 정본↔`hmc_v2` 쌍 전용. `motreg` 로 바꾸면 HC $n{=}7$ 에서 V2 가 hV4 를 앞선다. $n{=}9$ 값은 CVD 두 명이 부풀린 것. **§0.4-C** |
| **BBR vs MI Dice 0.33–0.50 / 0.27–0.36, ROI coverage 99.95% / 85.4%** | `_archive/registration_method_selection/` | 지표가 슬랩 오위치에 둔감해 **BBR 을 지지한다.** 아카이브 method3 는 FSL MNI152 로 돌아 정본과 공간도 다르다. **§4.4** |
| **DVARS $-16.3\%$, tSNR $+18.6\%$** | sub-01 run-1 파일럿 | **보간 2회 구버전** 산출. 단일 보간 정본에서는 부호가 반대다(tSNR $-1.9$–$3.0\%$) |
| **`motreg` hV4 protan 45° 이동 $p<.0001$** | `shift_gain_ch.json` | 통제군 이득 SD 가 $0.4\%$ 로 붕괴해 $t$ 가 31 까지 부풀었다. 45° 주장은 **V1 두 arm 에만** 건다. **§2.10** |
| **`hmc_v2` 종점 전량** (deutan V1 $p$=.027, deutan V2 $p$=.825, protan V1 $p$=.077, hV4 $p$=.108/.242 등) | `disparity_individual_arms.json`, `perm_adjacent_arm_hmc_v2.json` | §0.4-A 결정으로 원고에서 제외. **저장소에는 남는다** |
| **exp2 "14칸"** | `STATUS` §4.4 | 실제 측정 셀은 20칸이고 라벨이 합과 맞지 않는다. §4.9 의 세 가지 수 구분 참조 |

**상세 논거**: [`REVISION_PLAN_HMC_DISCLOSURE_2026-08-15.md`](REVISION_PLAN_HMC_DISCLOSURE_2026-08-15.md) · [`REVISION_PLAN_PRESUBMISSION_2026-08-10.md`](REVISION_PLAN_PRESUBMISSION_2026-08-10.md) · [`STATUS_ADDITIONAL_ANALYSIS_2026-08-15.md`](STATUS_ADDITIONAL_ANALYSIS_2026-08-15.md) · [`FRAMING_JNEURO_IMAGINGNEURO_2026-08-16.md`](FRAMING_JNEURO_IMAGINGNEURO_2026-08-16.md) · [`FILTER_ROBUSTNESS_ARMS.md`](../../analysis/phase5_filter_optimization/FILTER_ROBUSTNESS_ARMS.md)
