# 원고 수정 종합 — 한 번에 반영할 전체 목록 (2026-08-16 · rev.3 2026-08-24)

> **이 문서 하나만 보고 `.tex` 를 수정한다.** `REVISION_PLAN_HMC_DISCLOSURE`(M1–M9) · `REVISION_PLAN_PRESUBMISSION_2026-08-10`(A–I) · `STATUS_ADDITIONAL_ANALYSIS`(§5·§6) 에 흩어져 있던 확정 수정안을 **대상 파일 순서로** 재배열했다. 원 문서의 항목 ID 는 추적을 위해 그대로 붙여 둔다.
>
> **줄번호는 2026-08-16 에 실제 파일과 대조해 확인했다.** 인용된 「현행」 문구는 원고에서 그대로 가져온 것이다.
>
> **반영 상태 (2026-09-01 갱신): §1.1·§1.2·§1.3 반영 완료** — 제목은 T4 로 교체했고, 초록은 234 단어 / 13 문장이 되어 §1.0 의 예측과 일치한다. **나머지 항목은 여전히 미반영이다** (2026-08-24 대조 기준): `supplementary.tex` 에 `tab:motion_loco` 와 SDC 변위 수치가 없고, 46행은 여전히 `Every neural endpoint was recomputed`, 74행은 `cannot generate`, 464-468행은 `remains to be extended` 다. `methods_v2.tex` 에도 재정렬 관련 서술이 없다.
>
> **rev.3 에서 폐기된 두 항목(realignment 문단 · `tab:hmc_robustness`)은 `.tex` 에 없는 것이 정상이다.** 종전 판이 이를 미반영 항목으로 적고 있었으므로 여기서 정정한다.

---

## 0. 반영 순서

| 단계 | 이유 |
|---|---|
| ~~**1. §7 형식 (I3 → I4)**~~ | I3 은 2026-08-17 에 해소됨(§6). **I4(Methods 중복본 참가자 수 상충)만 남는다** — 5분, 아무 때나 |
| **1.9 N3 검정 이름 확정** | §4.5b 문안을 쓰기 **전에** `color-correspondence permutation` 명칭을 정한다. 나중에 바꾸면 문안·캡션·Methods 한 문단을 다시 손대야 한다 (§0.6) |
| **2. §5 Supplementary** | §4.1 이 §S2 을 파이프라인 절로 재편하고 §4.0 이 거기에 SDC 문단을 얹는 구조. 역순이면 §S2 을 두 번 재편한다 |
| **2.5 §1.5 Methods 움직임 문단 + §S2 해체** | §S2·§S3·§S4 와 **한 벌**이다(rev.5). 본문에서 내려보내는 FD 분포를 **§S4** 가 받고, 본문이 §S3 와 §S4 를 가리키므로 **부록 세 문안을 먼저 확정한 뒤** 본문을 넣는다. §1.5(e-3) 의 `no confound regression` 절 삭제도 같은 회차. 번호 당기기는 여기서 하지 않는다(5단계) |
| **3. §2 Results → §3 Discussion → ~~§1 제목·초록~~** | 초록은 본문이 확정된 뒤 마지막에. **⚠ 2026-09-01 에 §1.1–§1.3 을 먼저 반영해 이 순서를 어겼다.** 본문 §2·§3 을 반영한 뒤 **초록을 한 번 재대조할 것** — 특히 §2.5(M3)·§3.1(M5) 이 개인화 논거를 ROI 편재에서 $\hat\beta_c$ 방향과 심리물리 축으로 옮기므로, 초록 8번 문장의 `each` 가 여전히 그 논거와 맞는지 확인한다 |
| **3.5 §4.10 중복 정리·이동** | §4.0–§4.9 문안을 전부 반영한 **뒤에** 한다. 먼저 하면 `supplementary.tex` 줄번호가 밀려 §4.0·§4.1·§4.5·§4.8 의 앵커가 어긋난다 |
| **4. §6 그림 (+ §5.3 · §5.4)** | 별표 제거는 조판 마지막. 단 **§5.3(패널 `B` 삭제)은 §2.4 와 같은 회차**에 해야 한다 |
| ~~**5. §S 번호 당기기 (§1.5 e-2)**~~ | **✅ 완료 (2026-09-02)** — S2–S21 → S1–S20. 제목 20개와 `\S S…` 참조 전량(Supplementary 24건 · Methods 22건 · Results 11건 · Discussion 2건)을 함께 이동했고, 출처 주석의 절 번호도 새 번호로 맞췄다. 2026-09-03 에 본문 첫 인용 순서로 다시 전면 재번호했고, **이 문서의 `§S…` 표기는 그 현행 번호로 일괄 갱신되어 있다**(대응표 = `words_trimming.md` §0.0) |

**차단 항목**: **I2 (데이터 공개 방침)** — IRB 확인이 투고 저널 관리 에이전트 쪽에서 진행 중. 결론 전까지 Methods 문장과 Data availability 절을 **둘 다 비워 둔다**(한쪽만 채우면 상충한다).

---

## 0.4 전처리 파이프라인 — 2 arm 구성 (2026-09-01 확정) ★ **먼저 읽을 것**

### A. 결정

**원고는 두 파이프라인을 보고한다.** `motreg` 와 `motshift` 는 원고에서 뺀다.

| 파이프라인 | 역할 | 볼륨당 변환 | 리샘플링 |
|---|---|---|---|
| `with_residuals` (**Primary**) | 정본. 본문 전 수치의 출처 | $T$ (전 볼륨 동일) | 1회 |
| `hmc_v2` (**Realignment**) | 머리움직임 보정판. 전 종점 재산출 | $T \circ R_i$ | 1회 |

**근거 셋.**

1. **`motreg` 은 `hmc_v2` 가 실제로 하는 것의 근사다.** `supplementary.tex:75` 가 이미 그렇게 적고 있다 — *"does not reconstruct the data that volume realignment would have produced."* 실물을 실으면서 근사를 함께 실을 이유가 없다.
2. **종전 배제 사유가 사실과 달랐다.** `hmc_v2` 는 `mcflirt -mats` → `convert_xfm -concat` → 볼륨당 `applywarp` **1회**로, 정본과 리샘플링 횟수가 같다(`future_phase1_sensitivity/README.md:53`). *"볼륨마다 별도 리샘플링이 필요하다"* 는 보간 2회짜리 구 `hmc` 를 두고 한 말이 옮겨 붙은 것이다. 남는 차이는 변환이 볼륨마다 다르다는 점뿐이다.
3. **측정된 비용은 tSNR $-1.97\%$ 다** (V1 $-2.69$, V2 $-1.88$, V3 $-1.66$, hV4 $-1.75$. `hmc_summary.csv` 에서 직접 산출, sub-10 제외). 재정렬의 통상적 대가이며 표준 절차를 생략할 근거가 되지 못한다.

**`motshift` 는 `motreg` 의 대조였으므로 함께 빠진다**(독립 arm 이 아니었다). 종전 *"세 arm 전부 유의"* 는 **한 arm 과 그 대조를 독립 확인 셋처럼 센 것**이므로, 2 arm 이 독립 확인 개수에 대해 더 정직하다.

> **⚠ 사전등록과의 관계는 판단 근거로 쓰지 않는다 (2026-09-01 저자 지시).** `HMC_REANALYSIS_PRESPEC.md` 의 조항 자체가 같은 용어 오인 위에 쓰였을 가능성이 있다. 위 세 근거는 사전등록과 무관하게 성립한다.

### B. 두 파이프라인의 결과

**hV4 단독 보간 게이트 — 둘 다 통과, 다른 ROI 는 둘 다 미통과**

| | V1 | V2 | V3 | **hV4** |
|---|---|---|---|---|
| Primary | .164 | .424 | .586 | **.011** |
| Realignment | .922 | .228 | .810 | **.023** |

**hV4 LOCO 결손 (CVD 단일사례)**

| | 통제군 평균 | deutan | protan |
|---|---|---|---|
| Primary | 0.456 | 0.250 · $p$=.054 · $d$=$-2.02$ | 0.125 · $p$=.011 · $d$=$-3.25$ |
| Realignment | 0.451 | 0.354 · $p$=.242 · $d$=$-0.80$ | 0.271 · $p$=.108 · $d$=$-1.48$ |

방향은 둘 다에서 보존되고 유의성은 Primary 에서만 성립한다. 순위 근거는 §2.9.

**disparity — 개인별 전 ROI** (Crawford–Howell $t$, $p$)

| | | V1 | V2 | V3 | hV4 |
|---|---|---|---|---|---|
| Primary | deutan | 1.1 (.157) | **2.1 (.040)** | 1.9 (.052) | 0.2 (.411) |
| Primary | protan | **3.5 (.007)** | 1.0 (.181) | 0.1 (.466) | 1.1 (.150) |
| Realignment | deutan | **2.4 (.027)** | $-1.0$ (.825) | 0.6 (.293) | 0.4 (.351) |
| Realignment | protan | 1.6 (.077) | 1.0 (.186) | 1.1 (.151) | 1.4 (.101) |

세 가지가 확인된다. **protan 의 최대 $t$ 영역은 두 파이프라인 모두 V1** 이고 유의성만 약해진다(.007 → .077). **deutan 은 최대 영역이 V2 에서 V1 로 이동**하고 V2 는 부호가 뒤집힌다($t$ $+2.1 \to -1.0$). **네 셀 전부에서 최대 $t$ 가 양수이고 최소 한 ROI 가 $p<.10$ 이다.**

**LORO 8분류 (chance 0.125) — 둘 다에서 보존**

최저 셀은 재정렬 arm 의 deutan V1 $= 0.229$ 로 chance 의 1.8배다. `All eight colors remained decodable` 는 두 파이프라인에서 유지된다.

**disparity — 대칭 LOSO 추정량** (2026-09-02 산출. 정본 스크립트 `rerun_loo_consistent.py` 를 래퍼로 구동해 두 파이프라인을 같은 설정으로 돌렸고, Primary 가 발표본 값을 재현해 산출이 검증된다)

| | | V1 | V2 | V3 | hV4 |
|---|---|---|---|---|---|
| Primary | deutan | 0.5 (.323) | 1.3 (.116) | 1.2 (.143) | 0.1 (.474) |
| Primary | protan | **2.0 (.045)** | 0.8 (.234) | 0.1 (.479) | 0.8 (.228) |
| Realignment | deutan | 1.6 (.080) | $-0.6$ (.723) | 0.4 (.338) | 0.4 (.356) |
| Realignment | protan | 1.3 (.121) | 0.1 (.480) | 1.0 (.178) | 1.1 (.159) |

**⚠ LOSO 아래에서는 재정렬 파이프라인에 유의한 칸이 하나도 없다.** 16칸 중 유의한 것은 **Primary protan V1 하나**다. `results_v4.tex:76` 이 LOSO 를 *"the inferential estimate"* 로 규정하고 있으므로, **disparity 는 보강 증거 이상으로 쓸 수 없다.** C6(해리)의 근거를 LORO 와 hV4 게이트에 두는 §0.5 의 배치가 이 결과로 더 필요해진다.

산출물 `results/loso_arms/loo_consistent_{with_residuals,hmc_v2}.json`, 요약 `results/loso_two_arm_summary.json`, 래퍼 `scripts/_loso_arm_wrapper.py`.

### C. ICC 는 여전히 인용 금지

ICC$_{2,1}$ = 0.825 가 정본↔`hmc_v2` 쌍에서 계산됐다는 사실은 이제 문제가 아니다. 그러나 **arm 쌍 의존성**(정본↔`motreg` 로 바꾸면 통제군 $n{=}7$ 에서 V2 0.826 이 hV4 0.634 를 앞선다)과 **CVD 두 명이 피험자 간 분산을 키워 부풀린 값**이라는 두 사유는 독립적으로 유효하다. §8.1 금지 목록 유지.

hV4 단독성은 **게이트의 두 파이프라인 재현**(.011 / .023)만으로 지탱한다.

### D. 45° 순환이동은 주 주장이 아니다 — C9 철회

45° 결과는 **동결 투영** 계열이고 원고가 보고하는 disparity 종점은 **대응 불변**이므로 두 결과가 같은 것을 재지 않는다. Procrustes 는 직교 회전을 최적화해 제거하므로 고리형 배치에서 hue 라벨의 순환이동이 disparity 에 흡수된다. 45° 가 설명하는 것은 sub-09 V1 의 **색 특이성 귀무**($p_{perm}$ = .758)이며, "신호 없음"이 아니라 **"항등 대응이 틀렸다"** 는 진단이다.

또한 보간·disparity 는 **배치의 모양**을, 순환이동은 **라벨의 위치**를 묻는다. sub-09 V1 은 45° 로 되돌리면 $0.788$ 로 통제군 평균 아래이므로 그 ROI 에서 모양은 온전하다. 2성분 모형에는 균일 회전 항이 없어($\bar{\delta\theta} = 0$) 이 성분을 표현하지도 못한다.

**배치**: 정량 결과와 대안 설명은 **§4.5b (§S17)** 에만 둔다. Results 와 Discussion 에는 넣지 않는다. 다만 sub-09 V1 의 색 특이성 실패를 §S17 표에 싣는 이상 그 설명도 같이 실어야 한다. 빼면 그 셀이 근거 없는 귀무로 남는다.

## 0.5 핵심 결론별 서술 규칙 — C1–C8 (2026-09-01 개정)

> **아래 §1–§6 의 개별 수정안은 전부 이 규칙을 따라야 한다.** 충돌하면 이 절이 우선한다.

**적용 규칙**: 본문은 Primary 파이프라인 기준으로 서술한다. **두 파이프라인 중 어디서든 부호가 뒤집히거나 유의성이 사라지는 주장은 그 층위에서 강등한다.** 순서는 **유의성 주장 → 순위·존재 주장 → 서술적 관찰**이다. 부하가 걸린 종점은 부록 표에 두 파이프라인을 나란히 싣고, 본문은 Primary 값을 쓰고 그 표를 참조한다.

| | 결론 | 서술 층위 | 반영 지점 |
|---|---|---|---|
| **C1** | 통제군 연속 hue 보간은 hV4 단독 | **유지.** 근거는 **게이트의 두 파이프라인 재현**($p$ = .011 / .023)이고 다른 세 ROI 는 둘 다 미통과다. **ICC 는 쓰지 않는다**(§0.4-C) | §2.1, §4.1 |
| **C2** | 8색 범주 식별 보존 | 유지. 최저 셀(재정렬 deutan V1 $0.229$)도 chance 의 1.8배 | 확인만 |
| **C3** | CVD hV4 보간 결손 | **Primary 한정 유의**(protan $p$=.011, deutan $p$=.054) → 재정렬 민감성 공개(.242 / .108) → **순위 배치를 바닥에 깐다** → **크기는 추정 불가로 명시**. 네 요소를 한 문단에 붙여 쓴다(§2.2). **⚠ "두 참가자는 개인 관문을 통과하지 못했다" 절은 금지** — 통제군도 5/7 실패한다 | §2.2 + §2.9 |
| **C4** | 왜곡의 영역 귀속 | **주장하지 않는다.** protan 의 최대 영역은 두 파이프라인 모두 V1 로 안정하나 유의성이 .007 → .077 로 약해지고, deutan 은 최대 영역이 V2 → V1 로 이동하며 V2 는 부호가 뒤집힌다. **"어느 영역이 왜곡을 지는가는 이 자료로 결정되지 않는다"** 가 정확한 진술이다. 무너진 것은 **영역 귀속**이지 **왜곡의 존재**가 아니다 | §2.3, §2.4, §3.1 |
| **C5** | 개인차 | **발견이 아니라 프레임워크 속성.** 참가자별 추정은 방법의 속성이다. 편재 확립에 필요한 것은 **표본**이지 추가 분석이 아니다 | §1.1 제목, §1.2 초록, §3.5, §3.6 |
| **C6** | 범주 보존 / 연속 기하 손상의 해리 | **유지되고 강해진다.** 근거는 disparity 가 아니라 **LORO 보존(두 파이프라인)** 과 **hV4 LOCO 감소 + hV4 단독 게이트(두 파이프라인)** 다. 선행연구의 균일 gain 감소와 구별되는 지점 | §2.3, §2.4, §3.1 |
| **C7** | 필터 $\hat\beta_c$ | **deutan 2축 유지**($-42$, $-48$) / **protan 반전**($+24 \to -24$). 배포값은 동결값 그대로 보고, protan 파라미터에 생리학적 해석 부여 금지 | §3.2, §4.7 |
| **C8** | 역산·심리물리 | 불변. 해석적 단계임을 명시 | 확인만 |
| ~~**C9**~~ | ~~왜곡의 형태는 회전이다~~ | **철회.** 45° 순환이동은 §S17 의 대안 설명으로만 둔다. 사유 = §0.4-D | §4.5b |

**금지 표현**

| 표현 | 처리 |
|---|---|
| `significantly below controls` | **조건부** — 파이프라인 한정어와 민감성 문장이 붙을 때만. 단독 사용 금지 |
| `localized to a different area in each` | 금지 |
| `individual-specific cortical distortion` | 금지 |
| `individually distinct pattern of distortion` | 금지 |
| ICC$_{2,1}$ = 0.825 (및 V1 $-0.005$) | 금지. §0.4-C |
| deutan 과 protan 의 영역을 대비시키는 서술 | 금지. 두 사례를 `whereas` 로 병치하지 말고 **각각 그 자체로** 서술한다 |
| 효과크기를 유의성의 대체물로 쓰기 | 금지. $d_{cc}$ 95% CI 가 Primary protan 조차 $[-5.93,\ -0.41]$. §2.9 |

**C5 문구 주의**: "추가 분석이 필요하다"로 쓰지 않는다. 같은 자료에서 검정 형태 6종을 이미 돌렸고 전부 같은 답이므로, 더 파면 해결된다는 뜻으로 읽혀 그 문장과 충돌한다. **"더 큰 표본에서의 검증이 필요하다"** 가 정확하다.

---

## 0.7 범위 결정 — 방법 논문으로 재배치 (2026-09-02 확정) ★

### A. 결정

**효능 주장을 철회하고 방법 기여를 앞세운다.** 결과를 줄이는 것이 아니라 **disparity 가 지고 있던 무게를 해리로 옮긴다.** Results 순 감소는 약 170 단어이고 삭제되는 소절과 그림은 없다.

**근거**: 전향적 신경 평가가 개인화를 지지하지 않는다. deutan 기하는 두 필터 모두 HC 에서 멀어졌고(V2 disparity 0.68 → 개인화 0.77, RDM 유사도 0.42 → 0.05), protan hV4 보간은 개인화 필터가 세 조건 중 최하였다(0.06 대 무필터 0.14, 배포 0.19). 원고가 이미 `Neither index attributes the geometric recovery to individualization.` 이라고 적고 있다.

### B. 주장 층위

| | 층위 |
|---|---|
| 통제군 hue 보간은 hV4 단독 | **유의성 주장.** 두 파이프라인 재현($p$ = .011 / .023) |
| CVD 범주 식별 보존 ↔ hV4 보간 저하의 **해리** | **주장.** Primary 유의, 순위는 두 파이프라인 불변 |
| 개인 피질 표상에서 자극공간 필터를 역산하는 절차 | **방법 기여.** to our knowledge 최초 |
| 전향적 평가 | **혼재로 보고.** JND 는 개인화 필터에서 통제군 범위로 이동, 8AFC 는 deutan 두 필터 동등·protan 배포필터에서 저하, 신경 종점은 개선 없음 |
| 왜곡의 피질 위치 | 주장하지 않음 |
| 필터의 효능 우위 | 주장하지 않음 |

### C. Results 재배치

| # | 조치 |
|---|---|
| **1+2 병합** | `All eight colors remain decodable` 와 `Hue interpolation is reduced at hV4` 를 한 소절로 합치고 제목을 **`Categorical identification is preserved while hue interpolation fails at hV4`** 로 한다. 마지막 문장에서 해리를 진술하고 그것이 SNR 설명을 배제함을 밝힌다 |
| **3 압축** | disparity 소절을 324 → 약 150 단어. 개인별 ROI 표와 LOSO 귀무는 §S2 로. 제목은 `Hue geometry departs from the control reference in both CVD cases` |
| **10 재정렬** | Filter evaluation → Psychophysics → **Identification (신설)** → Colors remained decodable → Interpolation → Geometry. 근거 강도 순이다 |
| **5–9 불변** | 필터 도출 절차가 방법 기여이므로 줄이지 않는다 |

### D. `fig:geometry` 는 본문에 남긴다

필터의 $L_{\rm RDM}$ 이 그 RDM 차이 구조를 읽는다. 근거를 보이지 않고 그것으로 적합했다고 쓸 수 없다. **대신 성격을 바꾼다.** 검정 결과가 아니라 **손실이 평가하는 양의 기술**로 제시한다. 적합은 서술적이고 필터 표적 ROI 는 held-out test-loss 로 선정됐다.

**Methods 에 추가할 한 문장** (`sec:methods:selection` 끝) ✅ **반영 완료 (2026-09-03)** — `These ablation refits entered no selection decision…` 문단 뒤에 새 문단으로 추가. 실제로는 두 문장이다:

> The loss treats the representational geometry as a descriptive quantity. Target regions follow from held-out test-loss, so the fitted parameters stand independently of the inferential status of any single disparity contrast.

### E. 문체 규칙 (2026-09-02 저자 지시)

교체 문안은 다음을 지킨다. **두괄식**으로 결론을 첫 문장에 둔다. **부정 표현을 최소화**하고 가능하면 긍정 서술로 바꾼다. 세미콜론, 콜론, 엠대시를 쓰지 않는다. 완충 표현과 불필요한 문장을 넣지 않는다. **직접적이고 엄밀한 동사**를 쓴다(`rose`, `varied`, `remained`, `reached`, `separated`, `attributes`, `constitutes`, `evaluates`).

### F. 확정 대기 둘

**기여 진술** — `CLAUDE.md` 의 Two Main Contributions 를 아래로 교체할 것을 제안한다.

> **1. 해리의 규명 (finding).** CVD 개인의 피질에서 8색 **범주 식별은 보존**되고 같은 영역의 **연속 hue 보간만 저하**된다. 두 측정이 같은 복셀과 같은 런에서 나오므로 신호 품질 저하로는 이 패턴이 설명되지 않는다. 선행 CVD fMRI 는 magnitude·gain(Tregillus 2021)과 activation(Rina 2024)이며 이 해리를 보고한 바 없다.
>
> **2. 피질 기반 개인화 필터 프레임워크 (method, first).** 개인 자신의 피질 색 표상에서 역산한 필터로, 망막·스펙트럼 모델이 아니다. **"first" 의 스코프는 절차에 한정되며 효능을 포함하지 않는다.** N=2 전향 평가는 개념증명이고 결과는 혼재한다.

**제목** — T4 는 발견에서 응용으로 가는 호를 약속하므로 지금 자료에 과하다. 후보 셋.

| # | 문안 | 겨냥 |
|---|---|---|
| **T5a ✅ 확정 (2026-09-02)** | Preserved categorical identification with impaired hue interpolation in color vision deficiency **motivates** a cortically derived correction filter | `motivates` 가 두 기여의 관계를 진술한다. `grounds` 는 필터가 해리에서 도출됐다는 뜻이 되어 부정확하고(실제 도출은 2성분 기하 적합), `leads to` 는 본 자료가 보이지 않는 인과를 함축한다 |
| **T6** | Inverting an individual's cortical color representation into a stimulus-space correction filter | 방법 단독. 해리가 제목에서 사라진다 |
| **T1** | Hue identity and hue geometry dissociate in the cortical color representation of color-vision-deficient observers | 해리 단독. 필터가 사라진다 |

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

### 1.1 제목 `main.tex:63` — M9 ✅ **반영 완료 (2026-09-01, T4 채택)**

> **⚠ protan V1 을 근거로 반대 방향의 편재 주장을 하지 않는다.** protan 의 최대 영역은 두 파이프라인 모두 V1 로 안정하지만 유의성이 .007 에서 .077 로 내려가고(§0.4-B), 한 참가자에서 한 영역이 안정하다는 것이 **"참가자마다 다른 영역"** 을 뒷받침하지도 않는다.

### 1.2 초록 중간 `main.tex:89` — M7 ✅ **반영 완료 (2026-09-01)**

### 1.3 초록 마지막 `main.tex:89` — 14번 문장 삭제 ✅ **반영 완료 (2026-09-01)**

## 1.5 `Methods/methods_v2.tex` — 두 파이프라인 서술 + §S2 해체 ✅ **반영 완료 (2026-09-02)**

> **후속 수정 (2026-09-02, §5 검증 빌드 중 발견)**: 반영된 본문에 수식 모드 누락 2건이 있어 빌드가 실패했다. `:44` `(3840 \times 2160)` → `$3840 \times 2160$`, `:109` `(\hat{\mathbf{c}})` → `$\hat{\mathbf{c}}$` 로 정정 후 빌드 클린.

### (a) 본문 — `:70` 문단의 **마지막 네 문장만** 교체

> **⚠ 앞 문장들은 손대지 않는다.** 정규화 서술(`Normalization to the ICBM 152 Nonlinear Asymmetric 2009c template (MNI152NLin2009cAsym) used a twelve-parameter affine transform (FLIRT) followed by nonlinear warping (FNIRT) ..., yielding 2\,mm isotropic BOLD data in MNI space.`)은 교체 대상이 **아니다.** 아래 문안의 `this composed transform` 이 그 문장을 받는다.

**교체 대상 (현행 마지막 네 문장)**: `Each functional volume was resampled once ...` 부터 `... (Supplementary~\S S2).` 까지.

**교체**

> Each functional volume was resampled once by this composed transform, without slice-timing correction, head-motion correction, susceptibility distortion correction, or spatial smoothing. Because a single transform served every volume in a run, the same spatial interpolation applied throughout. Head-motion correction composes a volume-specific rigid term with that transform. The resampling then attenuates high spatial frequencies and leaves a residual signal change that follows the estimated displacement, raising the error variance of each voxel time series \parencite{grootoonk2000}. Multivoxel pattern analysis operates on those per-voxel values, so every neural endpoint was computed under both pipelines and both are reported. The second pipeline estimated each volume's rigid term with MCFLIRT \parencite{jenkinson2002} and composed it with the normalization transform before the single resampling. The head-motion quality-control record appears in Supplementary~\S S2.

같은 문단 앞쪽의 `and no confound regression was applied at any stage (Supplementary~\S S2)` 절을 **삭제한다.** 런별 선형 표류 회귀자가 실제로 존재하므로 그 전칭 부정은 틀렸다. 표류 회귀자 서술은 §S2 로 옮긴다.

**설계 의도 다섯.**

1. **동기를 주장하지 않는다.** 종전 초안의 `keeps the interpolation error constant over time, which we preferred` 는 오차를 관측한 뒤 방법을 골랐다는 뜻이 되고 그런 설계 기록이 없다. 새 문안은 **연산의 성질과 문헌에 확립된 사실만 진술한다.**
2. **왜 이 분석에서 문제인지를 한 문장이 진다.** `Multivoxel pattern analysis operates on those per-voxel values` 가 앞 문장의 두 결과(고공간주파수 감쇠, 복셀 시계열 오차분산 증가)를 본 분석의 측정량에 연결한다. 이 연결이 없으면 독자는 그 두 사실을 왜 제시했는지 알 수 없다.
3. **결론은 선택이 아니라 양쪽 보고다.** `every neural endpoint was computed under both pipelines and both are reported`. 두 파이프라인을 싣는 이상 정본 선택을 방어할 부담이 없다.
4. **QC 포인터를 분리했다.** 마지막 문장이 따로 선다.
5. 세미콜론과 콜론, 엠대시를 쓰지 않는다.

### (b) 용어 · 보간 우려의 문헌 근거

`realignment` 와 `head-motion correction` 은 영문에서 같은 것을 뜻하며 둘 다 추정과 적용을 함께 가리킨다. **본문은 `head-motion correction` 으로 통일**한다. `applywarp` 는 리샘플링 엔진일 뿐 그 자체가 보정이 아니다. 두 파이프라인의 차이는 볼륨 $i$ 에 적용되는 변환이며 Primary 는 $T$, 재정렬판은 $T \circ R_i$ 다. `applywarp` 호출은 둘 다 볼륨당 1회다.

**문헌 확인 결과 (2026-09-02) — 절반만 지지된다.**

| 명제 | 판정 |
|---|---|
| 재정렬의 리샘플링이 보간 오차를 남기고, 그 오차가 **추정 변위를 따른다** | **지지됨.** Grootoonk et al. (2000) 이 시뮬레이션 변위로 이 인공물을 특성화했고, 보정식이 **추정 변위의 주기 함수**라는 점이 시변성을 함의한다 |
| 그 오차가 **복셀 시계열의 오차분산을 키운다** | **지지됨.** 같은 논문 서론 — *"the detection of true activations may be impaired due to the increase in error variance"* |
| 보간이 **고공간주파수 정보를 깎는다** | **지지됨.** 같은 논문 50쪽 — *"removes some high spatial frequency information from the image"* |
| **평활화·보간이 MVPA 디코딩을 해친다** | **확립되지 않음.** 문헌이 갈린다. Op de Beeck (2010) 은 LOC 물체와 V1 방위에서 평활화가 성능을 떨어뜨리지 않는다고 보고하고, 다른 연구들은 V1 방위·안구우세에서 낮아진다고 보고한다. **정보의 공간 스케일에 따라 갈리므로 근거로 쓰지 않는다** |

**→ 문안 판정.** (a) 문안은 확립된 세 명제만 인용하고, MVPA 는 **그 결과가 본 분석의 측정량에 닿는 이유**를 설명하는 데만 쓴다. 디코딩 성능 손해를 주장하지 않는다.

**본 자료의 실측 둘은 §S2 에 싣되 선택의 근거로 쓰지 않는다.** ROI tSNR $-1.97\%$(V1 $-2.69$, V2 $-1.88$, V3 $-1.66$, hV4 $-1.75$), 런 부트스트랩 95% CI 평균 폭이 hV4 에서 $0.206 \to 0.255$(4개 ROI 중 3개에서 증가). 산출 `results/boot_runs_{with_residuals,hmc_v2}.json`.

**금지 표현**: `realignment would have introduced noise`(반사실 단정), `motion was negligible`(방어 불가), `smoothing degrades decoding`(문헌 미확립).

**추가 인용 필요**: `grootoonk2000` 이 `bibliography.bib` 에 없다. PDF 는 `docs/Prior_works/Preprocessing/Grootoonk(2000)_interpolation_realignment.pdf`, NotebookLM `ColorBlind_comprehensive` 에 등록됨. DOI `10.1006/nimg.1999.0515`.

### (c) §S2 은 삭제한다

§S2 `Confound Regression and Temporal Filtering` 은 본문 `:70` 한 문단이 두 번 가리키는 것이 전부이고(다른 참조 0건), 내용은 전부 갈 곳이 있다.

| §S2 의 내용 | 행선지 |
|---|---|
| MCFLIRT 추정 + FD 분포 · $16.2\%$ | **§S3** (파이프라인 절의 QC 문단) |
| `served as a quality-control record only, ... resampled once` | **삭제** (본문·§S3 와 삼중 중복) |
| 필드맵 미소비로 왜곡이 남는다 | **§S3** (§4.0 과 한자리) |
| 표류 회귀자 · 시간 필터링 없음 | **§S3** |

**§S3 의 제목도 바꾼다.** 재정렬판을 함께 보고하므로 `Uncorrected acquisition artifacts` 는 맞지 않는다. `Preprocessing pipelines and sensitivity analyses` 류로 바꾸고 그 아래에 파이프라인 정의, QC 기록, 종점 2열 표를 둔다.

**번호 당기기는 맨 마지막에 한 번에 한다.** S2–S21 → S1–S20. 대상은 상호참조 **19건**(S2·S5·S7·S8·S10·S11·S12·S15·S18·S19·S21)과 제목 20개다. §S2 을 가리키는 2건은 삭제되는 문단 안에 있어 별도 조치가 필요 없다. 먼저 하면 이 문서의 §4.x 앵커가 전부 무효가 되므로 §4.x 반영이 끝난 뒤에 한다(순서 표 5단계).

### (d) 연쇄 — §4.9 와의 정합

세션 2 통일 arm 은 재정렬을 포함해 처리됐다. **2 arm 결정으로 이 문제가 해소된다.** 원고가 재정렬판을 정식으로 보고하므로 세션 2 통일 arm 이 그것을 포함하는 것과 어긋나지 않는다. §4.9 문안에서 앵커가 어느 파이프라인인지만 명시하면 된다.

**산출 근거**: `future_phase1_sensitivity/README.md`(arm 정의 · 종점), `analysis/phase0_preprocessing/results/hmc_summary.csv`(tSNR), `PREPROCESSING_FINAL_REPORT.md`(FD), `results/sub07_leaveout_hV4.json`(순위).

---

## 2. `Results/results_v4.tex`

### 2.1 `:38` 뒤 — hV4 단독성의 재현 단서 ✅ **반영 완료 (2026-09-02)**

### 2.2 `:40` — CVD hV4 단일사례 (§2.9 와 **한 항목**) ✅ **반영 완료 (2026-09-02)**

> **⚠ 나누어 적용하지 말 것.** 유의성 철회와 순위 진술은 **한 덩어리로 들어가야 유효하다.** 부정문만 먼저 반영되면 그 문단이 순수한 철회로 읽히고 결손 주장 자체가 사라진 것처럼 보인다.

**⚠ 다시 넣지 말 것**: *"두 참가자는 어느 arm 에서도 개인 수준 관문을 통과하지 못했다"*. 개인 색라벨 순열은 **통제군도 7명 중 5명이 실패한다.** 통과율 2/7 이면 참가자 2명에서 기대 통과 수가 0.57 이므로 0 을 관측하는 것은 통제군 통과율과 완전히 양립한다. 정보가 없는 절이면서 집단 관문과 나란히 놓여 대비처럼 읽힌다.

### 2.3 `:29`–`:56` — 1·2번 소절을 병합해 해리를 헤드라인으로 ✅ **반영 완료 (2026-09-02)**

**⚠ `in both CVD cases` 를 반드시 붙인다 (2026-09-02 정정).** 한정 없이 쓰면 **통제군 결과와 어긋난다.** 이 소절은 통제군이 **hV4 에서만 보간에 성공한다**는 것을 함께 보고하므로, hV4 를 무조건 실패 영역으로 읽히게 하는 제목은 자기 소절을 반박한다. `fails` 도 `falls to chance` 로 바꿨다. deutan 0.250 은 chance 0.25 와 같고 protan 0.125 는 그 아래다.

**⚠ 색별 문단(`:38`)에 넣지 않는다 (2026-09-02 정정).** 그 문단은 어느 색이 결손을 이끄는지를 다루고 `hue vulnerability profile` $\mathbf{v}$ 를 정의해 적합 단계로 넘긴다. 소절 전체의 결론을 그 안에 두면 흐름이 끊긴다. 해리 진술에 필요한 두 근거(범주 식별 보존, 보간 저하)는 `:30` 과 `:36` 에서 모두 제시되므로 `:36` 끝이 제자리다.

### 2.3b `:32` — 인코더 전이 문단의 결론 문장 ✅ **반영 완료 (2026-09-02)**

**⚠ 과대 진술 금지.** `common representational code` 나 `identical representation` 으로 쓰지 않는다. 검정된 것은 **채널-복셀 가중 행렬의 전이**이지 두 집단의 기하가 같다는 것이 아니며, 논문의 나머지가 기하 차이를 다룬다.

### 2.4 `:60` — disparity 소절 압축 ✅ **반영 완료 (2026-09-02)**

**⚠ `(Figure~\ref{fig:geometry}B)` 에서 `B` 를 뺄 것.** 그 그림에는 패널이 없다. 사유는 §5.3.

**⚠ 그림은 본문에 남긴다.** 사유와 캡션 프레임 변경은 §0.7-D.

### 2.5 `:66` — 기여 2 로 넘어가는 다리 (방법 프레임) ✅ **반영 완료 (2026-09-02)**

**⚠ `differ ... in direction` 에 붙일 단서**: $\hat\beta_c$ 부호 대비($-42$ 대 $+24$)는 Primary 한정이다. 단서는 §3.2(a) 의 한 절이 진다. **§2.5 와 §3.2(a) 를 같은 회차에 반영할 것.**

### 2.6 `:195`–`:199` — 8AFC 를 독립 종점으로 분리 ✅ **반영 완료 (2026-09-02)**

**⚠ deutan 에서 두 필터가 동등했다는 사실을 같은 문단에 둔다.** 첫 문장의 `improved equally under both` 가 그 역할을 진다. 이것이 없으면 protan 한 칸만 읽혀 개인화 우위 주장으로 오해된다.

### 2.7 protan orange–yellow 트랙 불일치 — 본문 미수록

전체 104개 쌍 중 1개 셀이고 주장에 영향이 없다. 초록의 protan 근거는 **green–blue** 이며 그 쌍은 두 트랙이 정상 수렴한다(0.135 / 0.080). 수렴 트랙만 쓰면 $z$ 가 $+1.33 \to -0.58$, 평균 $\lvert z\rvert$ 가 $0.93 \to 0.84$ 로 **저자에게 유리한 방향**이므로 평균을 유지하는 현행이 보수적이다.

**이관처 = §4.6b (§S1 쌍별 스테어케이스 전수 표 + 표 아래 설명).** 전수 표를 실으면 독자가 직접 보고 판단하므로 각주보다 정보가 많고 선택적으로 읽히지 않는다.

---

### 2.8 Results 해석 범위 진술 — ✅ **개정 반영 (2026-09-02 2차): 서두 문단 철회, 내용 분산 배치**

### 2.9 순위 배치 — **§2.2 의 근거** (문안 없음)

> 문안은 §2.2 에 통합돼 있다. 이 절은 그 문장 3의 근거표와 단서만 담는다.

**출처**: `future_phase1_sensitivity/results/sub07_leaveout_hV4.json`. 종전 판이 적은 `perm_adjacent_arm_*.json` 의 `per_subject` 는 **존재하지 않는다**. 그 파일들은 ROI별 HC 집단 게이트만 담는다.

**hV4 LOCO adjacent accuracy**

| | 통제군 평균 | 통제군 7명 (오름차순) | deutan | 그 이하 통제군 | protan | 그 이하 통제군 |
|---|---|---|---|---|---|---|
| Primary | 0.456 | .312 .375 .400 .438 .521 .562 .583 | 0.250 | **0/7** | 0.125 | **0/7** |
| Realignment | 0.451 | .333 .333 .375 .438 .450 .583 .646 | 0.354 | **2/7** | 0.271 | **0/7** |

**⚠ 문구 정밀도 둘.**

1. **"below the control distribution" 로 쓰지 않는다.** 재정렬 파이프라인에서 deutan 0.354 아래에 통제군이 둘 있다(0.333, 0.333). 참인 진술은 **통제군 평균 아래**다. protan 만 두 파이프라인 모두 분포 전체 아래다.
2. **동률은 없다.** 위 네 칸 모두 엄격 부등호로 세었고 동률 셀이 없으므로 각주가 필요 없다.

**부수 확인 1 — sub-07 저커버리지는 이 결론을 흔들지 않는다.** sub-07 의 hV4 는 아틀라스 70복셀 중 16복셀만 남는다. 그러나 Primary 에서 그 피험자의 hV4 성적은 0.400 으로 통제군 평균 근처이고, 제외해도 게이트가 유지된다(.011 → .008, deutan .054 → .063, protan .011 → .017). 산출 `results/sub07_leaveout_hV4.json`.

다만 처리 방식이 분석마다 다른 것은 별개 문제다. SRM 계열은 같은 피험자의 hV4 를 결측으로 빼고 LOCO 는 넣는다. **Methods 에 규칙과 근거를 한 문장으로 명시할 것.**

**부수 확인 2 — 효과크기로는 대체할 수 없다.** Crawford–Garthwaite 비중심 $t$ 구간($n=7$).

| | case | $d_{cc}$ | 95% CI |
|---|---|---|---|
| Primary | deutan | $-2.02$ | $[-4.33,\ +0.42]$ |
| Primary | protan | $-3.25$ | $[-5.93,\ -0.41]$ |
| Realignment | deutan | $-0.80$ | $[-2.91,\ +1.38]$ |
| Realignment | protan | $-1.48$ | $[-3.68,\ +0.82]$ |

**0 을 넘지 않는 유일한 칸조차 구간이 $[-5.93,\ -0.41]$ 로 하한과 상한이 14배 차이 난다.** 재정렬 파이프라인에서는 두 칸 모두 0 을 포함한다. 이 표본에서 효과의 **크기는 추정되지 않는다.** (산출: `scipy.stats.nct` 비중심 $t$ 역산, $n=7$. Primary 두 칸이 발표본 값과 일치해 계산 방식이 검증됨)

→ **조치**: 효과크기를 유의성의 대체물로 쓰지 않는다. 구간은 §S2 에 싣는다. 본문 대응구는 §2.2 문장 1의 `at this sample size the size of the reduction is not estimable` 이다. 주장을 지는 것은 **순위 배치**이고, 순위 진술은 분포 가정도 구간도 필요 없어 표본이 작을수록 상대적으로 유리한 유일한 형태다.

### 2.10 sub-09 V1 의 45° 순환이동 — Results 미수록

사유 = **§0.4-D**. 정량 결과와 대안 설명은 **§4.5b (§S17)** 에만 두고, Discussion 에도 넣지 않는다.

---

## 3. `Discussion/discussion_v3.tex`

### 3.1 `:33` — localization 해석 ✅ **반영 완료 (2026-09-02)** — 현행 P3 이 `leaving the cortical locus of the distortion undetermined` 로 끝난다

**⚠ 교체 시 딸려 나가는 인용 (2026-09-02 확인).** 종전 문단이 지고 있던 인용 4건 중 `kriegeskorte2008` 은 **원고 전체에서 이 문단이 유일한 출처**였다. 교체 후 RDM 의 1차 인용이 사라지므로 **`methods_v2.tex:216`(ΔRDM 정의 자리)로 옮겼다.** `brouwer2009`·`boehm2014`·`ohkoba2021` 은 Introduction·Methods·Results 에 남아 고아가 되지 않는다.

**⚠ `differed in ... direction` 에 붙일 단서**: $\hat\beta_c$ 부호 대비($-42$ vs $+24$)는 Primary 한정이고 protan 은 **재정렬 파이프라인(`hmc_v2`)에서 반전된다**($-12$, §3.2 rev.4). 단서는 §3.2(a) 의 한 절이 진다. **§3.1 과 §3.2(a) 를 같은 회차에 반영할 것.**

### 3.2 `:44` `:46` — $\hat\beta_c$ 부호 강건성 ✅ **반영 완료 (2026-09-02)** — 현행 P5 가 `even that sign depends on the reduction basis and on the preprocessing pipeline` 로 단서를 진다

> **⚠ rev.4 정정 (2026-09-02 반영).** 이 절은 종전에 `baseline` × `motreg` 표를 썼으나, **§0.4-A 는 `motreg` 를 원고에서 빼고 `hmc_v2`(Realignment) 를 남기기로 확정**했다(2026-09-01). 종전 문구 *"`hmc_v2` 열은 §0.4-A 결정에 따라 뺀다"* 는 결정을 거꾸로 옮긴 것이다. 아래 표와 수치는 `hmc_v2` 로 교체했고, 원고에는 이 값이 반영되어 있다. 출처는 `filter_robustness_arms/beta_sign_three_arms.json` 이다.

> **⚠ 이 관례의 대가**: 부록 번호가 바뀔 때마다 **41건을 손으로 고쳐야 한다.** §4.7 의 번호 당기기(구 S2–S21 → 신 S1–S20)에서 실제로 그렇게 했다. 다음에 번호가 또 움직인다면 `\label`/`\ref` 로 전환하는 편이 안전하나, 지금 바꾸면 이번 회차의 검증 결과와 대조가 어려워지므로 **투고 후로 미룬다.**

### 3.3 균일 회전 항 부재 (F · U10) — ⚠ **Discussion 미수록으로 변경 (2026-08-25)**

> **종전 안**: `discussion_v3.tex:48` 문단 끝에 *"모형에 균일 회전 항이 없어 §S17 의 45° 재배열을 표현할 수 없다"* 를 넣는다. 등급 필수.
>
> **철회.** 이 항목은 **C9(45° 를 주 주장으로) 를 전제로 만들어졌다.** 원 지시(`REVISION_PLAN_MOTION_GEOMETRY_2026-08-06` §5)는 45° 를 소견으로 내세우던 시점의 것이고, 그때는 *"당신 모형이 그 회전을 표현 못 하지 않느냐"* 를 선제할 필요가 있었다. **C9 를 철회한 이상(§0.4-F) 선제할 주장이 없다.**

**두 번째 이유가 더 중요하다 — 회전은 기하 왜곡이 아니다.**

강체 회전은 등거리 변환이므로 **모든 쌍거리를 보존한다.** 배치의 모양이 그대로라는 뜻이다. 본 논문의 기여 1 은 **모양의 왜곡**을 주장하는데, 모양을 바꾸지 않는 성분을 Discussion 에서 *"모형이 담지 못하는 한계"* 로 진술하면 **주장하지도 않는 것에 대한 약점을 스스로 만든다.** 리뷰어가 읽는 순서도 나쁘다 — 기하 왜곡을 논하다가 갑자기 기하를 바꾸지 않는 성분의 한계가 나온다.

**세 번째 — 두 측정이 실제로 갈린다.** 이것이 두 소견이 경쟁하지 않는 이유다.

| 측정 | 대응 재배열에 | protan V1 |
|---|---|---|
| 본문 disparity (직교 회전 최적화 **후** 잔차) | **거의 둔감** | Primary .007, 보정 .077 |
| 동결 투영 순열 (항등 대응 기준) | 민감 | 항등 실패, 45° 로 해소 |

**회전에 둔감한 측정이 상승해 있으므로, protan V1 의 이탈은 강체 재배열만으로 설명되지 않는다.** 즉 모양 성분이 따로 있고, 그것이 본문이 보고하는 것이다. 재배열은 별개 현상이며 **동결 투영 순열에만 보인다.**

→ **조치**: Discussion 에서 삭제. 필요한 한 절은 **§4.5b 해석 문안**이 자체적으로 진다(아래 개정). Discussion 은 회전을 언급하지 않는다.

**⚠ 되살리지 말 것**: `Extending the model to that component is left to future work` 류의 문장은 **넣지 않는다.** 주장하지 않는 성분에 대한 future-work 약속은 그 성분이 결손이라는 인상만 남긴다.

---

### 3.4 `:60` — 한계 문단 (2 파이프라인 · 방법 프레임으로 개정)

**교체**

> Several reported estimates depend on preprocessing. The deutan V2 disparity elevation reverses in sign under head-motion correction, and the region carrying the largest deviation in that participant moves from V2 to V1. The protan V1 elevation weakens from $p = .007$ to $p = .077$. Under the symmetric leave-one-subject-out reference the protan V1 elevation in the primary pipeline is the single cell to reach significance across both pipelines and all four regions. The color-correspondence permutation shows the same lability, with seven cells surviving correction in the primary pipeline and none in the head-motion-corrected pipeline. We therefore report the representational geometry as a descriptive quantity throughout.
>
> The neural loss term evaluates that geometry. Because target regions follow from held-out test-loss rather than from any disparity contrast, the fitted parameters stand independently of the inferential status of those contrasts. The filters reported here are the frozen values that the procedure returned, and we give them no physiological interpretation.
>
> The control-level result is stable across the same comparison. Interpolation across the hue circle exceeded the color-label permutation null at hV4 alone in both pipelines, and eight-way identification stayed above chance at every region in both.

**설계 의도 셋.**

| # | |
|---|---|
| 1 | **한계를 앞세우고 무엇이 남는지로 닫는다.** 세 번째 문단이 두 파이프라인에서 견디는 결과를 진술해 문단이 순수한 철회로 읽히지 않게 한다 |
| 2 | **$L_{\rm RDM}$ 방어가 여기 들어간다.** §0.7-D 는 Methods 한 문장으로 계획했으나, §S17 에서 색 특이성이 보정 파이프라인에서 전멸했으므로 Discussion 에서도 답해야 한다. 리뷰어는 *"적합에 쓴 신경 구조가 두 번째 파이프라인에서 사라진다"* 를 여기서 묻는다 |
| 3 | **두 참가자를 대비시키지 않는다.** deutan 과 protan 을 각각 그 자체로 진술한다 |

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

### 4.0 §S2 `Susceptibility distortion` 문단 — SDC 변위 실측 ★ **신규 항목** (등급: 필수) ✅ **반영 완료 (2026-09-02)** — `roi_shift_summary.csv` 에서 문안의 수치 전부 재현 확인 후 교체. 절 번호는 당기기 뒤 **§S2**

### 4.1 §S2 — 파이프라인 정의 + LOCO 2열 표 (등급: 필수) ✅ **반영 완료 (2026-09-02)** — (a)(b)(c) 는 종전 회차에 반영돼 있었고(2열 표는 `tab:motion_loco` 가 아니라 `tab:interp_arms` 로 존재), 이번에 (c) 의 `Neither single-case contrast reached significance…` 문장과 (d) 의 격자 제한 문장을 보간 표 아래에 추가

**⚠ 철자**: 원고는 미국식(`american`)으로 통일돼 있다. 위 문안의 `analyzed` 를 유지할 것. **`supplementary.tex:535` 의 `analysed` 는 현행 원고의 오류이므로 함께 고친다.**

### 4.2 · 4.3 — 폐기 항목의 이관처

종전의 §S2 재정렬 문단 신설안과 `tab:hmc_robustness` 는 **2 arm 결정으로 대체됐다.** 재정렬은 별도 문단이 아니라 §S2 의 파이프라인 정의와 종점 2열 표에 통합된다.

| 종전 위치 | 새 위치 |
|---|---|
| 재정렬 서술 | §1.5 (Methods) + §S2 파이프라인 정의 |
| tSNR $-1.97\%$ · ROI 겹침 | §S2 QC 문단 |
| 종점 표 | §4.1 `tab:motion_loco` 2열로 통합 |
| ICC 2행 | **삭제** (§0.4-C) |

**원칙 하나는 유효하다 — 품질 수치로 종점을 기각하지 않는다.** tSNR 은 파이프라인 특성 기술이지 어느 결과를 버리는 근거가 아니다.

### 4.4 §S2 / §S3 — G + BBR QC 그림 ✅ **반영 완료 (2026-09-02)** — §S2 에 `Choice of registration method.` 문단 신설. 2층 정당화(fMRIPrep 실패 → 커스텀 / BBR 육안 실패 → MI)와 `전뇌 중첩 지표는 BBR 을 선호하나 슬랩 오위치에 둔감` 선제 공개를 넣었고, Dice 수치는 인용하지 않았다

### 4.5 §S17 (`supplementary.tex:464-468`) — 회귀자 시간축 대조 확장 ⚠ **폐기 (2026-09-01)**

이 항목은 `motreg` 와 `motshift` 를 전제로 한 논증이었다. 둘 다 원고에서 빠지므로(§0.4-A) **문안 전체를 폐기한다.**

**남는 조치 하나** ✅ **완료 (2026-09-02 확인)**: 현행 `:468` 의 `The circular-shift control that separates these accounts was applied to the disparity endpoint (S2) and remains to be extended to the permutation reported here.` 는 존재하지 않는 대조를 가리키게 되므로 **삭제한다.** 그 자리에는 두 파이프라인의 색 대응 순열 결과를 넣는다.
→ 이미 이행되었다. 해당 문장은 살아 있는 `supplementary.tex` 에 없고 `Supplementary/archive/S18_geometry_validity.tex:76` 에만 남아 있다(아카이브이므로 무해).

**~~⚠ 산출 필요~~** ✅ **완료 — 산출도 검증도 끝났다 (2026-09-02)**. 종전 기재 *"현행 표는 Primary 와 `motreg` 기준"* 은 사실과 달랐다. `tab:color_specificity` 는 이미 **Primary + head-motion correction** 두 열이며 `motreg` 열은 없다. 검증 결과는 다음과 같다.

- **35셀 × 2 파이프라인 전부 원시 JSON 과 일치**(불일치 0셀). 양성대조 표 `tab:frozen_control` 16개 항목도 전부 일치.
- **산문 수치 7개 진술 전부 성립.** BH 보정을 파이프라인별 35셀 내에서 재계산해 확인했다(Primary 16셀 $p<.05$ · 7셀 생존, 재정렬 15셀 · 0셀 생존, deutan V2 $q$ .0175 → .0525, protan V1 $p$ .758 → .010). 생존 7셀 = HC2 V1·V3, HC4 V3, HC6 V3, HC7 V3, Deutan V2, Protan V3.
- **산출 스크립트는 `color_correspondence_loro.py` 가 아니라 `analysis/validation/scripts/disparity_frozen_permutation.py`** 다(전자는 별개 산출물). 두 파이프라인은 `data_dir` 만 다르고 순열 1000회·시드 42·$k$(4,4,3,3)·최소 복셀 20·통계량 정의가 모두 같다.
- 살아 있는 `.tex` 에 `motreg`·`motshift`·`motion-regression` 은 **0건**.
- **BH 보정 범위는 현행 유지**(파이프라인별 35셀). 두 파이프라인은 같은 데이터의 대안 전처리이므로 70셀 합산은 과보정이다.
- deutan V2 의 $q$ 정확값이 $0.0525$ 이므로 원고 표기를 `.052` → **`.053`** 으로 정정했다.

### 4.5b §S17 — hue 순환이동으로 sub-09 V1 의 색 특이성 귀무를 설명한다 ★ **신규 (2026-08-25)** ✅ **반영 완료 (2026-09-02)** — 대부분 종전 회차에 들어가 있었고, 이번에 빠져 있던 둘을 채웠다. ① 신호 부족이 아니라는 근거(split-half $.847$, LORO $0.79$) ② 해석 세 진술 중 (iii)`disparity 가 두 파이프라인 모두에서 상승해 있으므로 재배열만으로 설명되지 않는다`. `motreg` 열은 §0.4-A 에 따라 넣지 않았다. 절 번호는 당기기 뒤 **§S17**

> **⚠ §4.5 의 순환이동과 다른 것이다.** §4.5 는 **회귀자를 시간축에서** 순환이동시키는 대조이고, 여기는 **hue 라벨을 색 바퀴에서** 한 칸씩 돌리는 분석이다. 이름이 겹치므로 원고에서 **`time-shifted regressors`** 와 **`cyclic hue relabeling`** 으로 명확히 구분해 쓴다.

**⚠ 인용 금지 셀**: `motreg` hV4 protan 은 $p<.0001$ 로 나오지만 통제군 이득 SD 가 $0.4\%$ 로 붕괴한 결과다($t$ = 31). 주장은 **V1 두 arm 에만** 건다.

**⚠ 모형 포함 여부를 언급하지 않는다 (2026-08-25).** 종전 초안에 *"a rigid one-step shift is also outside the two-component model … (Discussion)"* 가 있었으나 삭제했다. 주장하지 않는 성분에 대해 모형의 표현력을 논하면 **없는 약점을 만든다.** 근거는 §3.3(미수록 사유). 또한 RDM 은 라벨 순열에 민감하므로 *"필터가 이 성분에 무관하다"* 도 단정할 수 없다 — **양쪽 다 말하지 않는 것이 정확하다.**

### 4.6 §S1 `tab:jnd_baseline` — D · 범위 절단 각주 ✅ **반영 완료 (2026-09-02)** — 문안 (a) 는 캡션 끝에, (b) 는 §4.6b 표 바로 앞 문단으로. 세미콜론은 §0.7-E 에 따라 두 문장으로 분리. 절 번호는 당기기 뒤 **§S1**

### 4.6b §S1 — 쌍별 스테어케이스 전수 표 ★ **신규 (2026-08-25)** (등급: 필수) ✅ **반영 완료 (2026-09-02)** — `_staircase_pairs_table.py` 를 실행해 표가 이 문서의 것과 일치함을 확인한 뒤 삽입(`tab:staircase_pairs` = Table S19). 표 아래 문안도 함께 넣었고 세미콜론만 분리했다

**⚠ 값을 조정하지 않는다.** 208개 중 이 한 트랙만 문제이므로 제외 규칙을 세우면 사후적으로 보이고, 조정 방향이 결론에 유리한 쪽이라 더 그렇다. **평균 유지 + 전량 공개**가 방어 가능한 선택이다.

### 4.7 H 문안의 배치 ✅ **해소 (2026-09-02)** — 부록 재편으로 신설이 불필요해졌다. $\hat\beta_c$ 부호 통계는 현 **§S12 Identifiability checks** 에 있고 Discussion 은 그 절을 가리킨다

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

### 4.9 §S2 — `exp2` 종점의 전처리 arm 재산출 ★ 신규 (2026-08-17) ✅ **반영 완료 (2026-09-02, 문안 정정 후)** — ⚠ **이 절의 문안에 오류가 있었다.** `of twenty directional contrasts, thirteen reversed` 는 이 절의 판정 블록과 `exp2_endpoints_arms.json` 의 `counting_note` 가 **둘 다 금지하는 합산**이다. 반영본은 `native 10 중 8, matched 10 중 5` 로 나누어 적었다. 선택지 (i)(앵커 arm 명시 구)도 함께 넣었고, 기하가 더 안정적이라는 진술을 절대값 없이 두 문장으로 덧붙였다

**⚠ 이것을 근거로 종점을 교체하지 않는다.** 사전 선언된 주 종점은 **hV4 LOCO adjacent accuracy** 이고(산출 로그도 `*** PRIMARY ENDPOINT (hV4) ***` 로 명시), 그것이 불안정한 쪽이다. "기하가 안정적이니 그쪽을 보자"는 사후 종점 교체다. **정확한 진술** = *사전 선언된 주 종점은 arm 간에 불안정하고, 수렴 지표인 기하는 더 안정적이며 사전지정 ROI 에서 방향이 유지된다.*

**⚠ 디스패리티는 절대값을 인용하지 않는다.** HC 기준 자체가 arm 간에 이동한다(V1 $0.429 \to 0.481$, $+12\%$). LOCO 에서 HC 가 $0.456 \to 0.445$ 로 거의 불변이었던 것과 대비된다. **순서만 안정적이고 절대값은 arm 의존적이다.**

> **⚠ 서로 다른 세 개의 수를 혼동하지 말 것.**
>
> ① **재산출 종점 20칸** = 측정 셀의 수 ($6+6+6+2$). `STATUS` §4.4 의 라벨은 "14칸" 으로 합과 맞지 않는다 — 어느 쪽이 사전 확정본인지 확인 필요. 현재는 20칸 전부 산출해 두었다.
>
> ② **방향 대비 10개/variant** = arm 간 부호 비교의 수. ① 과 무관하다.
>
> ③ **disparity 8개 대비** = `matched` 단독, 2 ROI 한정. ② 와도 세는 단위가 다르다.

**⚠ 새 arm 을 주 결과로 채택하지 않는다.** harm arm 에서 protan Optimal 이 Window 를 이기고 RDM cosine 도 올라가 **우리에게 유리해 보이지만**, 그것을 근거로 arm 을 바꾸면 정확히 cherry-picking 이다(정본 arm 의 protan Optimal 은 0.062 로 최악이었다). **두 arm 을 나란히 싣고 어느 쪽으로도 방향 주장을 하지 않는다.**

> **⚠ rev.3 정합 경고 (2026-08-24)** — §0.4-E. 이 절의 통일 arm 은 **재정렬을 포함해** 처리됐고, 비교의 HC 기준·exp1 무필터 앵커도 `full_dataset_C010_hmc_v2` 로 맞췄다. §1.5 Methods 가 *"정본 파이프라인에는 재정렬을 적용하지 않았다"* 고 적으므로 **모순은 아니지만**, 위 문안에 그 구분이 없다. 두 조치 중 하나를 택한다.
>
> | 선택지 | 내용 | 비용 |
> |---|---|---|
> | **(i) 권장** | 문안에 한 구를 추가한다: `...with the healthy-control reference and the session-1 anchor taken from the same realigned reconstruction, so that the two sessions are not mixed across arms.` | 문안 한 구 |
> | (ii) | exp1 앵커를 **정본 arm 값으로 재산출**해 교체 | 서버 job 1건 |
>
> (i) 이면 재정렬이 세션 2 통일 arm 에만 쓰였음이 독자에게 보이고, Methods 의 `not applied` 가 세션 1 정본을 가리킨다는 것도 분명해진다.

### 4.10 Methods–Supplementary 중복 정리와 절 이동 (2026-09-02 재판정)

> **근거는 분량이 아니라 중복이다.** Methods 는 6,115 단어로 본문의 약 45%를 차지하지만 IN 은 상한을 두지 않는다. **방법 논문으로 재배치한 이상(§0.7) 방법 서술을 줄이면 기여 자체가 줄어든다.** 아래는 중복이 확인된 것과, 기여가 아닌 보조 자료에 한정한다.

#### (a) S8 ↔ Methods `Two decoding schemes` — 중복 (등급: 권장) ✅ **반영 완료 (2026-09-02)** — S8(현 §S5)의 LORO·LOCO 절차 서술을 삭제하고 Methods 포인터 한 문단으로 축약. 고유 내용인 leakage control 과 LOSO 문단은 유지

#### (b) S9 ↔ S20 — 중복이면서 수치가 어긋난다 (등급: **필수**) ✅ **반영 완료 (2026-09-02)** — 구 S8·S9 가 현 **§S7 Cross-validation procedures and evaluation metrics** 로 병합되고 통계는 현 **§S15 Statistical Analysis** 로 일원화됐다

#### (c) 이동 — 한 건만 남는다 ✅ **확인 완료 (2026-09-02)** — R+C·Machado 파라미터화는 **이미 §S15(현 §S13)에 있고** Methods 에는 한 줄 포인터만 남아 있다. Methods 에 `machado`·`stockman`·$\Delta\lambda$ 잔존 없음을 grep 으로 확인했으므로 추가 조치가 없다

#### (c-2) Methods `Inverse fitting` 정리 ✅ **반영 완료 (2026-09-02)** — 872 → 716 단어

#### (d) 옮기지 않는 것

`Parameter selection` 303 단어(three-gate 절차), `Inverse fitting` 886 단어, `Identifiability and recovery` 317 단어. 앞의 둘은 종전 판단 그대로이고, 셋째는 (c) 에서 새로 추가됐다.

#### (e) 절감 규모

(a)+(b)+(c) 로 약 700 단어가 준다. **§1.5 반영으로 Methods 가 6,144 에서 6,115 로 이미 줄었다.** 비율 개선은 여전히 부산물이며 목표가 아니다.

#### (f) 반영 순서

§4.0–§4.9 문안 반영이 끝난 뒤에 한다. (b) 는 문단 삭제라 앵커 영향이 작으므로 먼저 해도 된다.

---

## 5. 그림

> **⚠ 그림 번호 정정 (2026-09-01).** 이 절이 쓰던 번호는 한 칸씩 밀려 있었다. `main.aux` 의 `\newlabel` 이 정본이며 실제 번호는 **`fig:loco` = Figure 4**, **`fig:geometry` = Figure 5** 다. Methods 에 `fig:forward`(Figure 2)와 `fig:pipeline`(Figure 3)이 들어가면서 Results 쪽이 한 칸씩 밀렸다. 본문 그림은 일곱이 아니라 **여덟**이다. 아래 소제목을 그에 맞게 고쳤다.

### 5.1 `fig:geometry` (**Fig 5**) — 별표 제거 ✅ **반영 완료 (2026-09-02)** — `generate_fig3_geometry_r6.py` 에서 별표 블록 제거 후 재생성(패널에 별표 없음 확인), 캡션의 "Asterisks mark …" 문장을 지정 문안으로 교체

**⚠ protan V1 만 별표를 남기지 않는다.** protan V1 은 Primary 에서 유의하지만 보정 파이프라인에서 .077 로 내려간다. 한쪽에만 별표가 남으면 그림이 **"참가자마다 다른 영역"** 을 시각적으로 주장하게 되고, 이는 §0.5 C4 가 주장하지 않기로 한 것이다. **양쪽 모두 제거하고 유의성은 본문과 부록에서만 진술한다.**

### 5.2 `fig:loco` (**Fig 4**) ✅ **확인 완료 (2026-09-02)** — 그림·캡션 변경 없음을 재확인했고, 부수 확인 항목(README `Known open items 1`)은 §5.4 의 README 재작성에서 닫았다

### 5.3 `fig:geometry` 의 패널 `B` 참조는 존재하지 않는 패널을 가리킨다 ★ **신규 (2026-09-01) · 등급: 필수** ✅ **해소 확인 (2026-09-02)** — §2.4 반영 시 `B` 가 함께 빠져 live `results_v4.tex` 에는 잔존 참조가 없다. `fig:geometry}B` 는 `results_v4_prewrap_backup.tex` · `results_v4_HYBRID_backup.tex` (미조판 백업)에만 남아 있다

**⚠ §2.4(M2) 의 교체 문안이 이 오류를 그대로 물려받는다.** 그 문안 첫 문장이 `(Figure~\ref{fig:geometry}B)` 를 유지하고 있으므로, §2.4 를 반영하면 오류가 새 문장으로 옮겨 갈 뿐이다. **§2.4 를 반영할 때 `B` 를 함께 뺀다.**

### 5.4 `Figures/` 디렉토리 정리 ★ **신규 (2026-09-01) · 등급: 권장** ✅ **반영 완료 (2026-09-02)** — (a) 미사용 4종을 `old/` 로 이동(삭제 대신 이동으로 처리; `.DS_Store` 는 이미 gitignore 등록) · (b) TIF 는 `submission_assets/` 로, PNG 사본은 `old/` 로 · (c) 파일명 유지 · (d) `FIGURES_README.md` 를 `main.aux` 기준 8+2 그림 표로 재작성하고 `Known open items 1` 을 닫음 · (e) `generate_fig3_geometry_r6.py` 도크스트링 번호 정정(Figure 5 / workflow=Figure 3)

## 6. 형식·제출 차단 — I

| # | 항목 | 대상 | 상태 |
|---|---|---|---|
| **I3** | ~~`\S S…` 참조 번호표 stale~~ | `Supplementary/REVISION_WORKLIST.md:10-34` | **✅ 해소 (2026-08-17)** — 번호표는 실제 heading(S1–S21)로 정정 완료. 본문 `\S S…` **17건 전수 재검증 17/17 정상** — 참조는 이미 신 번호를 쓰고 있었고 stale 한 것은 표뿐이었다. **원고 수정 불요.** 단 §4.7 참조: 새 절을 삽입하면 이 문제가 재발한다 |
| **I4** | Methods 중복본 6개가 참가자 수를 `Twelve` / `Thirteen` 으로 상충 기술. `main.tex` 는 `methods_v2` 만 `\input` 하나 **코드 공개 시 읽힌다** | `Methods/methods{,_concise,_streamlined,_bibtex,_for_pi}.tex`, `*_backup.tex` | 5분 |
| **I1** | back matter 4절 `\todo{}` 실채움 (CRediT / 이해관계 / 감사 / 데이터 가용성) | `main.tex:110-146` | I2 후 |
| **I2** | **데이터 공개 방침 결정** — 기탁(OSF/OpenNeuro) vs 요청 시 제공. Methods 문장과 Data availability 절을 **함께** 고쳐야 한다 | `main.tex` + `methods_v2.tex` | **IRB 확인 대기** |

---

## 6.5 2026-09-02 Supplementary 감사에서 추가로 고친 것 (지시서 밖)

| # | 항목 | 조치 |
|---|---|---|
| A1 | **부록 그림 번호 붕괴** | `fig:landscape` 에만 `\renewcommand{\thefigure}` 이 없어 본문 **Figure 8** 로 조판되고 있었다(본문 그림은 7개). 리셋을 첫 부록 그림으로 옮겨 **S1 / S2 / S3** 로 정정 |
| A2 | **`\S\ref{app:…}` 가 `§4.5` 로 렌더링** | `\subsection*` 은 번호가 없어 직전 번호 있는 절(Discussion 4.5)을 집는다. PDF 에 `Supplementary §4.5` 가 실제로 인쇄돼 있었다. 본문 나머지와 같은 하드코딩 `\S S…` 로 교체(Methods 1건 · Discussion 2건) |
| A3 | **부록 8개 절이 본문 미인용** | S3·S4·S6·S8·S9·S14·S17·S20(구 번호)에 Methods 의 해당 지점에서 인용을 추가. 이제 부록 전 절이 최소 1회 인용된다 |
| A4 | **`0.35` 순열 귀무의 포인터 오지정** | `results_v4.tex:34` 이 §S17(구)을 가리켰으나 그 값은 §S3(구) `tab:interp_arms` 캡션에만 있다. **§S2** 로 재지정 |
| A5 | **부록 내부 포인터 둘** | `whether the deviation is specific to color is treated in S12` → **§S17**(구 S13). 리지 페널티가 디코딩을 저하시킨다는 근거 `(\S S8)` → **§S8**(구 S10, `tab:loco_decoders` 가 실제 근거) |
| A6 | **§0.5 C4 금지 표현 1건** | `Both CVD participants carried color-specific geometry, at different ROIs.` 의 뒷부분 삭제 |
| A7 | **영국식 철자 6건** | `behaviour`·`favour(ed)`·`penalises` → 미국식. 원고는 `american` 으로 통일돼 있다 |
| A8 | **§S10 QC 가 sub-10 을 포함하고 있었다** | `ROI coverage averaged 84.3% (SD 21.7%) across the ten scanned participants … all participants entered the downstream analyses` 는 **n=10 기준이고 마지막 절은 사실과 다르다**(sub-10 은 전 분석 제외). `Method_method3_header_mi/results.json` 에서 n=9 로 재산출해 **83.5% (SD 22.7%) · 유효복셀 99.5%** 로 교체하고 집계 방식(참가자별 4 ROI × 6런 평균)을 명시. sub-07 의 30.8% 는 불변. 구 84.3% 는 n=10 의 **셀 풀링** 값이고 SD 21.7% 는 n=10 의 **참가자별** 값이어서 두 집계가 섞여 있었다 |
| A9 | **표 중복** | `tab:motion_arms`(S1)의 Primary 두 열이 `tab:disparity_loso`(S6)와 완전히 같다. 캡션에 재수록임을 명시 |
| A10 | **조판 넘침** | `tab:motion_arms` 가 30.5pt 넘쳐 있었다. `\small` 로 해소. 남은 넘침 3건은 전부 Supplementary 밖의 기존 항목 |

**남은 부산물 둘 (조치 안 함, 기록만)**

- ~~그림 **파일명**이 구 절 번호를 쓴다~~ → **해소 (2026-09-02, 저자 지시).** `figS18_landscape` → `figS1_landscape`, `figS16_adjacc_saturation` → `figS2_adjacc_saturation`, `figS_forward_tuning` → `figS3_forward_tuning`. 이제 **조판되는 그림 번호**를 담는다. 생성 스크립트 3개도 같은 이름으로 옮겼고, `FIGURES_README.md`·`FIGURE_CAPTIONS.md`·`FONT_POLICY.md`·`generate_fig8.py` 의 참조를 함께 고쳤다. 본문 그림 파일명은 §5.4(c) 결정대로 그대로 둔다.
- §S14 의 Test 1 / 2a / 2b / 2c 네 표가 `\label` 없이 Table **S14–S17** 번호를 차지한다. 번호열은 연속이고 본문이 이름으로 부르므로 조판 결함은 아니다.

**§8.1 금지 목록 두 행을 갱신했다 (2026-09-02).** `hmc_v2 종점 전량` 행은 §0.4-A 가 뒤집은 옛 결정 위에 쓰인 것이어서 **철회**하고, 대신 그 값들에 걸리는 인용 규칙 셋(서술적 셀 · 영역 귀속 금지 · Primary 한정 유의성)을 명시했다. `exp2 "14칸"` 행은 JSON 의 `prespecified_cells = 14` 확인으로 **해소**했고, 금지가 남는 것은 방향 대비의 variant 간 합산임을 분명히 했다.

---

## 6.6 Supplementary 집약 개정 (2026-09-02 2차, 저자 지시)

**저자가 지적한 셋을 먼저 고쳤다.**

| 지적 | 조치 |
|---|---|
| `Nuisance model.` 문단이 필요한가 | **문단 해체.** 표류 회귀자·시간 필터 미적용은 Methods `:86` 의 GLM 서술과 겹치므로 §S2 `The two pipelines.` 안의 한 구로 축약했고, 필드맵 미소비 문장은 §4.0 이 지정한 대로 `Susceptibility distortion.` 서두로 옮겼다. 적용하지 않은 것을 절 제목으로 세우던 구조가 사라진다 |
| `Regressing the motion parameters…` 가 지금 파이프라인과 맞는가 | **문장 삭제. 지적이 맞다.** 이 문장의 `run-shifted null` 은 `motshift` 이고, §0.4-A 가 `motreg` 와 함께 원고에서 뺀 arm 이다. §4.5 가 §S17 쪽 같은 성격의 문장을 *"존재하지 않는 대조를 가리킨다"* 며 삭제하도록 했는데 §S2 쪽 잔여분이 남아 있었다 |
| `was acquired without the defacing step` | **경위 삭제.** 수정된 arm 에서 결과 일치를 확인했으므로 우리가 먼저 결함 이력을 말할 이유가 없다. `The second session was reprocessed with the anatomical images harmonized to the first and with head-motion correction` 로 바꿨다 |

**전반 집약.** 절 **20 → 17**, 조판 **69 → 67 쪽**.

| 유형 | 내용 |
|---|---|
| **절 병합 3건** | 구 §S3 `Image Orientation`(37 단어) → §S2 `Registration` 문단. 구 §S16 `Evaluation Metrics`(90) → §S5 로 합쳐 `Cross-validation procedures and evaluation metrics`. 구 §S15 `HC magnitude anchor`(130) → §S12 `Identifiability checks` 의 한 문단(Test 2b 와 같은 HC 재적합을 쓰므로 같은 자리) |
| **중복 삭제** | §S17 이 `35칸 중 16, BH 7 생존`을 두 문단에서 반복 · protan V1 `.758 → .010` 을 두 번 진술 · §S12 가 파라미터 불확실성을 세 곳에서 서로 다른 반올림으로 진술(20/25, 22/26, 16/24) · §S12 의 FDR 요약이 서두 문단과 완전 중복 · §S11 이 `Fitting.` 블록에서 서두 문장을 그대로 반복 · §S9 이 결론 문장을 서두에서 이미 진술 |
| **문체** | 한 문장 한 줄로 끊어져 있던 문단을 이어 붙이고, §0.7-E 에 따라 본문 산문의 세미콜론·콜론을 문장 분리로 바꿨다(캡션의 목록 구분자는 유지). `Pass criterion:` 형태의 전보체 서술을 완전한 문장으로 |
| **절 번호** | 21개 판 → **S1–S17**(2026-09-02), 이어서 본문 첫 인용 순서에 맞추어 전면 재번호(2026-09-03). 참조 33건, 제목 17개, 출처 주석을 함께 이동했다. 병합된 절을 가리키던 Methods 인용 3건은 병합처로 합치면서 중복 인용을 제거했다 |

**검증.** 조판 클린(67쪽, undefined reference 0건, Supplementary 내 넘침 0건). 세션 시작본과 숫자 토큰을 대조해 **삭제된 수치가 전부 의도된 것임을 확인**했다(중복 진술 제거 · n=10 → n=9 재산출 · `N = 1000` → `$N = 1{,}000$` 표기 통일). 대조 과정에서 §S15 의 `nichols2002` 인용이 §4.10(b) 문단 삭제로 원고 전체에서 사라진 것을 발견해 §S15 의 집단 순열 문장에 되살렸다.

> **⚠ 이 문서의 §4.x 에 적힌 `§S…` 는 이제 두 세대 전 번호다.** 대응표: 구 S2→S1, S3→S2, S4→S3, S5→S4, S6→S5, S7·S8→S6, S9→S7, S10→S8, S11→S9, S12→S10, S13→S11, S14→S12, S15→S13, S16·S17→S14, S18→S15, S19→S16, S20→S17. (구 번호는 §1.5(c) 이전 기준으로 여기서 다시 한 칸 더 올라간다.)

**세션 중 저자 편집 감지.** §S17 의 deutan V2 보정값이 세션 시작본의 `q = .052` 에서 현재 `q = .053` 으로 바뀌어 있다. 이 변경은 본 작업에서 하지 않았으므로 저자 편집으로 보고 그대로 두었다. 같은 시각에 `discussion_v3.tex` 도 짧아져 있었고, 번호 갱신은 그 편집본 위에 적용됐다.

---

## 6.7 Supplementary 문장 단위 점검 (2026-09-03, 두괄식 · 단일 의미)

**§6.6 의 압축이 만든 부작용을 되돌리는 회차다.** 단어 수를 줄이려고 문장을 합치면서 한 문장에 두세 개의 주장이 실린 곳이 생겼고, 이번에 전부 분해했다. 기준은 **문장 하나가 한 가지만 말한다**이며, 분량은 목표가 아니다.

**자체 점검에서 나온 결함 넷 (지시서 밖).**

| # | 결함 | 조치 |
|---|---|---|
| B1 | **§S7 의 자기 서술이 틀렸다.** §6.6 에서 구 §S16 `Evaluation Metrics` 를 §S5(현 §S7)에 병합했는데, 절 서두는 여전히 `This section reports the two procedural checks` 였다. 실제로는 네 문단이다 | `the fold-level checks and the evaluation metrics` 로 정정 |
| B2 | **§S6 가 지시 대상 없는 대명사로 시작했다.** `This penalty applies to…` 의 `This` 가 절 첫 문장이라 받을 것이 없다 | `The ridge penalty applies to…` |
| B3 | **§S10 마지막 문장이 같은 주장을 두 번 했다.** `resides in the representational pattern rather than in response amplitude, so the cortical color response retains its strength while its geometry departs` 는 앞뒤가 동어반복 | 뒷절 삭제, 결론을 문단 앞으로 |
| B4 | **§S15 의 `nichols2002` 가 원고에서 사라져 있었다** (§6.6 검증에서 발견, 그 회차에 복구) | 집단 순열 문장에 재인용 |

**두괄식 정리 6개 절.** 절 또는 문단의 결론이 뒤에 놓여 있던 곳을 앞으로 옮겼다.

| 절 | 종전 첫 문장 | 개정 첫 문장 |
|---|---|---|
| §S2 `Classification and interpolation` | 재산출 절차 | `The two readouts dissociate under both pipelines.` |
| §S2 `Session-2 endpoints` | 재처리 절차 | `We report both preprocessing arms … and draw no directional conclusion …` |
| §S2 `Susceptibility distortion` | 필드맵 취득 | `Susceptibility distortion within the analyzed ROIs is predominantly subvoxel and spatially smooth …` |
| §S3 | 산출 방법 | `ROI coverage averaged $83.5\%$ …` |
| §S10 | 비교 절차 | `Both CVD participants fell inside the control distribution on every activation metric at every ROI.` |
| §S4 | 선택 절차 | `SRM used $k = 4$ at V1 and V2 and $k = 3$ at V3 and hV4 …` |
| §S16 | 왜 Procrustes 를 쓰는가 | `The two alignment spaces agree on the pattern that carries the Results.` |
| §S17 | `This section reports …` (메타 문장) | `The color-correspondence permutation carries power only when the shared projection is held fixed …` |
| §S11 | 적합 절차 | `The retinal-family (R+C) model does not represent the fitted distortion and saturated its gain boundary in both participants.` |
| §S12 | 선택되지 않은 $L_{\rm LOCO}$ 정의 | `Four pre-specified checks bound what the fit can estimate.` ($L_{\rm LOCO}$ 정의는 그 뒤 문단으로. §4.10(c-2) 가 지정한 "§S12 서두" 안에 그대로 있다) |

**단일 의미 분해 약 30문장.** 대표적으로 §S2 파이프라인 서술의 3중 문장, §S2 세션-2 의 `Eight of the ten … as did five of the ten …, and the two masks disagree`, §S2 registration 의 `because … so …` 3단 연결, §S13 run-matching 의 60단어 문장, §S7 의 `(1) … and (2) …` 지표 정의를 각각 둘에서 셋으로 나눴다.

**§S4 목록 제거.** `\begin{itemize}` 4항목(각 한 줄)을 한 문장으로 합쳤다.

**결과.** 산문 6,828 → 7,115 단어(§4.x 필수 추가분 약 880 단어 포함), **문장 360개 · 평균 19.6단어**, 42단어 초과 문장 0개(남은 3건은 수식 뒤 where-절과 절 경계 오검출). 절 17개, 조판 67쪽, undefined reference 0건.

**숫자 무결성.** 세션 시작본과 대조해 감소한 토큰 19종이 전부 의도된 것임을 재확인했다. 이번 회차에서 새로 줄어든 것은 §S10 의 중복 `p = 0.182` 하나와, §S7 지표 정의에서 `12.5\% = 1/8` 의 뒤쪽 동어반복뿐이다.

---

## 6.8 Supplementary ↔ 본문 정합 개정 (2026-09-03, 3축 점검)

Results·Discussion 현행본을 통독한 뒤 부록을 (1) 본문과의 수치·주장 일치, (2) 표현, (3) §0.7 프레임(방법 논문 · 효능 미주장 · 영역 미귀속) 기준으로 대조했다. **본문 핵심 수치 26종을 부록에서 교차 확인해 26/26 일치.**

**(1) 본문과 어긋나거나 본문이 하지 않는 주장 — 7건 정정**

| 위치 | 문제 | 조치 |
|---|---|---|
| §S13 LORO | `neither filter degraded the second-session color signal` 은 본문에 없는 주장이며, 최저 셀 0.50 은 HC 범위 0.71–0.77 **아래**다 | 주장 삭제, 최저 셀과 HC 범위를 수치로 병기 |
| §S13 forward tuning | `reaches the HC level` — $+0.18$ 대 $+0.21$ 은 본문 `against` 다 | `approaches` |
| §S9 | `the two ROIs carrying the single-case elevations` — 영역 귀속 서술 (§0.5 C4) | 삭제, `V1 and V2` 만 |
| §S8 | 유의성 진술에 파이프라인 한정어 없음 (§0.5 C3) | `In the primary pipeline` 추가 + `tab:motion_arms` 참조 |
| §S15 | Crawford 검정의 꼬리를 `CVD disparity exceeds HC` 한 방향만 적음 | 종점별 꼬리(disparity 상측 · 보간 하측 · 분류·활성 양측) 명시 |
| §S10 | `the procedure used for the geometric and interpolation endpoints` 가 양측/단측 차이를 흐림 | `applied one-tailed to …` 로 구분 |
| §S14 | `sub-10 is excluded here as everywhere else` — 본문에 없는 참가자 ID | 삭제(Methods 가 이미 제외를 서술) |

**(2) 표현**

- 내부 용어 제거: `S08-robust`/`S09-primary` → Deutan/Protan(표 4개 포함), `production argmin/loss/candidates` → `selected`, `Phase-1` 과 2026 년 월 표기 삭제, `zero-shot` 삭제, `canonical FE-6 basis` → `six-channel basis`, `canonical hue map` → `reference hue map`, `pre-specified deficit regions` → `target regions`(§0.7-D 의 Methods 문장과 일치).
- 절 제목 17개를 본문과 같은 sentence case 로 통일. 콜론·괄호 제거(`Filter-evaluation session: design and comparator` → `… session design and comparator`, `(K-Selection)` 삭제).
- 모호한 강조어를 수치로 교체: `essentially unchanged` → `moved from 0.456 to 0.445`, `well below` → 실제 값 병기, `far above` 삭제.
- `\citealp` 2건을 `\textcite`/`\parencite` 로(괄호 없는 인용이 문장 안에서 어색했다). `Two rows require care` → `Two rows are constant-output artifacts`. §S7 의 메타 문장 삭제, §S1 를 소견으로 시작.

**(3) 프레임 정합 — 확인 결과**

| 항목 | 부록 진술 | 판정 |
|---|---|---|
| 해리(기여 1) | §S2 `The two readouts dissociate under both pipelines.` | 본문 §results:loco 와 일치 |
| 신호 강도 | §S10 `resides in the representational pattern rather than in response amplitude` | 초록 `distorts the geometry rather than weakening its overall signal` 과 일치 |
| 영역 미귀속 | §S2 `Individual cells of this grid are descriptive …` ×2, §S9 귀속 서술 삭제 | Discussion `leaving the cortical locus … undetermined` 과 일치 |
| 효능 미주장 | §S2 세션-2 `draw no directional conclusion`, §S13 `neither filter degraded` 삭제 | Results `Neither index attributes the geometric recovery to individualization` 과 일치 |
| 파라미터 지위 | §S12 `descriptive embedding … rather than a point estimate` | Results·Discussion 과 일치 |
| R+C | §S11 `does not represent the fitted distortion and saturated its gain boundary` | Results §rc_insufficient 와 일치 |

조판 67쪽, undefined reference 0건. 숫자 무결성 재확인(감소분은 전부 코드명·연월·참가자 ID 삭제와 중복 제거).

---

## 7. 원고 밖 잔여 작업

| # | 작업 | 산출물 | 왜 필요한가 |
|---|---|---|---|
| ~~1~~ | ~~`HMC_REANALYSIS_PRESPEC.md` 에 원고 제외 결정 기록~~ | — | **소멸 2026-09-01.** 재정렬 파이프라인을 정식으로 보고하므로 제외 결정 자체가 없어졌다 |
| **1b** | **`TEAM_BRIEF` · `future_phase1_sensitivity/README` 정정** | ICC 0.825 를 "신규 자산"으로 적은 대목에 인용 금지 사유 추가 | 두 문서가 그 값을 본문 승격 대상으로 명시하고 있어, 두면 다음 회차에 또 올라온다 |
| ~~1c~~ | ~~재정렬 파이프라인의 미산출 값 3종~~ | — | **완료 2026-09-02.** ① LOSO 는 래퍼로 로컬 산출(§0.4-B). ② 색 대응 순열은 `disparity_frozen_permutation_hmc_v2.json` 으로 **이미 존재**했다. ③ CG 구간은 `scipy.stats.nct` 로 산출(§2.9). **BrainIAK 는 로컬에 있다(0.12)** — 기록의 '서버 전용'은 사실이 아니다 |
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
| 색 특이성 arm 비교 (§4.5b) | `analysis/validation/results/disparity_frozen_permutation_{current,motreg,motshift,hmc_v2}.json` |
| **재정렬 미적용 근거 (§1.5)** | `hmc_reanalysis/server_recovered/README.md`(코드 감사·항등 검사), `phase0_preprocessing/results/hmc_summary.csv`(tSNR), `*_desc-motion.par`(변위) |
| $\hat\beta_c$ arm 비교 | `analysis/phase5_filter_optimization/results/filter_robustness_arms/beta_sign_three_arms.json`, `results/s10_inclusion/u2_{baseline,motreg,hmc_v2}/` — **원고는 `baseline`·`motreg` 두 열만 쓴다** |
| 필터 교차평가 | `results/filter_robustness_arms/filter_robustness_arms.json` |
| 비교자 구현 | `~/…/OneDrive-Personal/Projects/colorBlind/colorBlind_exp2.py:150,169,723,733,741,744,799` |
| **쌍별 스테어케이스 표 (§4.6b)** | `analysis/phase6_behavioral_analysis/results/exp2_behavior/a2_staircase_diagnosis.json`, `scripts/_staircase_pairs_table.py` |
| SDC 미적용 정당화 | `analysis/phase0_preprocessing/results/roi_shift_summary.csv`, `figures/sdc_cohort/` |
| **순위 배치 (§2.9)** | `analysis/future_phase1_sensitivity/results/perm_adjacent_arm_*.json` 의 `per_subject` |
| **sub-07 제외 재산출 (§2.9)** | `analysis/future_phase1_sensitivity/results/sub07_leaveout_hV4.json`, `scripts/_sub07_leaveout.py` |
| **hue 순환이동 이득 검정 (§4.5b)** | `analysis/future_phase1_sensitivity/results/shift_gain_ch.json`, `scripts/_shift_gain_ch.py` |
| **`hmc_v2` 생성 스크립트 · 코드 감사 · 항등 검사** | `analysis/phase0_preprocessing/hmc_reanalysis/server_recovered/` |
| **ICC 전 쌍 재계산 (§0.4-C)** | `analysis/future_phase1_sensitivity/results/icc_all_pairs.json`, `scripts/_icc_all_pairs.py` |
| **원고 제외 결정 기록** | `analysis/phase0_preprocessing/HMC_REANALYSIS_PRESPEC.md` 부록 A |

---

## 8.1 인용 금지 수치 — 원고·발표·서신 어디에도 쓰지 않는다

| 수치 | 출처 | 사유 |
|---|---|---|
| **ICC$_{2,1}$ = 0.825 (hV4), $-0.005$ (V1)** | `arm_agreement.json` | 정본↔`hmc_v2` 쌍 전용. `motreg` 로 바꾸면 HC $n{=}7$ 에서 V2 가 hV4 를 앞선다. $n{=}9$ 값은 CVD 두 명이 부풀린 것. **§0.4-C** |
| **BBR vs MI Dice 0.33–0.50 / 0.27–0.36, ROI coverage 99.95% / 85.4%** | `_archive/registration_method_selection/` | 지표가 슬랩 오위치에 둔감해 **BBR 을 지지한다.** 아카이브 method3 는 FSL MNI152 로 돌아 정본과 공간도 다르다. **§4.4** |
| **DVARS $-16.3\%$, tSNR $+18.6\%$** | sub-01 run-1 파일럿 | **보간 2회 구버전** 산출. 단일 보간 정본에서는 부호가 반대다(tSNR $-1.9$–$3.0\%$) |
| **`motreg` hV4 protan 45° 이동 $p<.0001$** | `shift_gain_ch.json` | 통제군 이득 SD 가 $0.4\%$ 로 붕괴해 $t$ 가 31 까지 부풀었다. 45° 주장은 **V1 두 arm 에만** 건다. **§2.10** |
| ~~**`hmc_v2` 종점 전량**~~ | `disparity_individual_arms.json`, `perm_adjacent_arm_hmc_v2.json`, `results/loso_arms/loo_consistent_hmc_v2.json` | **행 철회 (2026-09-02).** 이 행은 `hmc_v2` 를 원고에서 뺀다는 옛 결정 위에 쓰였고, **§0.4-A(2026-09-01)가 그 결정을 뒤집어 두 파이프라인을 나란히 보고하기로 확정했다.** 현행 §S2 의 `tab:motion_arms` 와 `tab:interp_arms` 가 여기 나열된 값들(deutan V1 $p$=.027, deutan V2 $p$=.825, protan V1 $p$=.077, hV4 $p$=.108/.242)을 이미 싣고 있다. **대신 인용 규칙 셋이 이 값들에 걸린다** — ⓐ 개별 셀은 서술적이며 본문 주장을 받치지 않는다(§4.1-d 문장이 두 표 아래에 붙어 있다), ⓑ 영역 귀속을 주장하지 않는다(§0.5 C4), ⓒ 유의성 주장은 Primary 한정이고 재정렬판의 민감성을 함께 적는다(§0.5 C3) |
| **exp2 "14칸"** | `STATUS` §4.4 | **해소 (2026-09-02).** `exp2_endpoints_arms.json` 의 `prespecified_cells` 가 **14** 로 적혀 있어 "14" 는 사전 확정 종점의 수가 맞고, "20" 은 그것을 측정한 셀의 수다. 둘은 다른 것을 세므로 충돌이 아니다. **여전히 금지되는 것은 방향 대비의 합산이다** — `native` 8/10 과 `matched` 5/10 을 "20 중 13" 으로 묶으면 안 되며, JSON 의 `counting_note` 가 같은 취지로 적혀 있다. §4.9 반영본은 두 variant 를 나누어 적었다 |

**상세 논거**: [`REVISION_PLAN_HMC_DISCLOSURE_2026-08-15.md`](REVISION_PLAN_HMC_DISCLOSURE_2026-08-15.md) · [`REVISION_PLAN_PRESUBMISSION_2026-08-10.md`](REVISION_PLAN_PRESUBMISSION_2026-08-10.md) · [`STATUS_ADDITIONAL_ANALYSIS_2026-08-15.md`](STATUS_ADDITIONAL_ANALYSIS_2026-08-15.md) · [`FRAMING_JNEURO_IMAGINGNEURO_2026-08-16.md`](FRAMING_JNEURO_IMAGINGNEURO_2026-08-16.md) · [`FILTER_ROBUSTNESS_ARMS.md`](../../analysis/phase5_filter_optimization/FILTER_ROBUSTNESS_ARMS.md)
