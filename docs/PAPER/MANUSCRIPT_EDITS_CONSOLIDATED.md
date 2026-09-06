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

---

## 9. Supplementary 절별 압축 개정 (2026-09-06, 저자 지시)

> **원칙** — 부록은 본문에 없는 것만 담는다. 결과는 서술 대신 표·나열로 제시한다. 해석은 꼭 필요한 곳에만 둔다. 캡션은 측정 대상·방법·기호·검정 방향만 적는다(프로젝트 규칙).
>
> **절차** — 절마다 ⓐ 문안 초안 → ⓑ 본문 포인터 대조(누락·중복) → ⓒ 학술 문체·과대주장·부정 어휘 점검 → ⓓ Fable 서브에이전트 검토 → ⓔ 지적 소진 후 `.tex` 반영.

### 9.1 S11 `app:retinal_family` — 초안

**현황**: 산문 463단어, 최장 문단 273단어. 본문 포인터는 셋이다.

| 포인터 | 본문이 이미 말하는 것 |
|---|---|
| `methods_v2.tex:158` (§2.10) | R+C 를 같은 기준으로 평가했다는 비교 가능성 |
| `methods_v2.tex:221` (§2.12) | $g$ 를 $[0,3]$ 에서 $0.05$ 간격으로 탐색 |
| `results_v4.tex:94` | 단일 이득이 Machado 이동을 혼동축을 따라서만 재척도한다 · S-cone 변위를 표현하지 못한다 · 두 참가자 모두 이득 경계 포화($g=3.0$, $2.95$) · protan $\overline{L}_{\rm test}=-0.86$ 대 $-1.54$ |

→ 현행 S11 의 도입 문단·`Fits` 문단·`Degrees of freedom` 문단이 위 넷을 모두 되풀이한다. **부록에만 있는 것**은 식 (6), Stockman–Sharpe 기저 사용, $g=2$ 의 의미, $\Delta\lambda$ 앵커 세 값, 앵커별 포화 범위 $0$–$100\%$, 이득 $>2$ 의 생리적 함의, $\Delta$RDM 직접 적합 재현, 그리고 축 간 각거리 $60^\circ$ / $74^\circ$ 이다.

**반영 문안**

```latex
\suppsection{Comparison with the retinal-family distortion model}{app:retinal_family}

\paragraph{Model.}
The retinal-family account attributes CVD color distortion to a cone-spectral
shift at the retinal level \parencite{machado2009}, optionally augmented by a
cortical compensation gain $g$ \parencite{boehm2014,tregillus2021},

\begin{equation}
  \delta\theta_{\rm RC}(\theta;\,g)
    = (2 - g)\,\delta\theta_{\rm Mach}(\theta)
  \label{eq:rc}
\end{equation}

where $\delta\theta_{\rm Mach}$ is the per-hue angular shift predicted by the
Machado model, evaluated here on the Stockman and Sharpe cone fundamentals
\parencite{stockman2000} rather than on the Smith and Pokorny fundamentals for
which it is defined. The gain cancels the retinal shift at $g = 2$ and displaces
hues past the undistorted angle above that value. $\Delta\lambda$ was held fixed
rather than fitted, and each participant was evaluated at three published
cone-shift anchors for their subtype, $6.0$, $6.5$ and $8.0$\,nm for deutan and
$1.5$, $3.0$ and $10.0$\,nm for protan, with results reported at the anchor of
lowest held-out loss.

\paragraph{Fits.}
Fitted values appear in \cref{tab:modelfits}. In the protan participant
saturation ranged from $0\%$ to $100\%$ across the three $\Delta\lambda$
anchors, and the reported fit is the anchor of lowest held-out loss. A gain
above $2$ places the perceived hue past the undistorted angle, which is not
compatible with the residual CVD confirmed in both participants. Fitting a
retinal-family model directly against $\Delta$RDM returned the same boundary
behavior.

\paragraph{Degrees of freedom of the family.}
The gain rescales the retinal shift uniformly, so the family displaces hues
along the confusion axis at every value of $g$. The S-cone term of the
2-component model, $\beta_s \cos(\theta - 90^\circ)$, lies $60^\circ$ from the
deutan confusion axis and $74^\circ$ from the protan one. This property of the
model class holds across fitting criteria
(\S\ref{sec:results:rc_insufficient}).
```

**캡션 개정** (`tab:modelfits`) — 결과 진술 두 개(`the deutan R+C was rejected …`, `the protan R+C generalized worse …`)와 그 앞의 콜론을 뺀다. `Each 2-component row …` 의 꼬리절(`which is a $\beta_s$-dominant alternative …`)도 표가 보여 주는 결과이므로 뺀다. 대신 R+C 행이 무엇을 담는지 한 문장 넣는다.

```latex
\caption{Distortion-model fits for both CVD participants, all scored on the same
held-out composite test-loss ($\overline{L}_{\rm test}$, lower is better;
\S\ref{sec:methods:selection}). The neural RDM atom in each adopted fit is V2
for the deutan and V1 for the protan participant. $\overline{L}_{\rm test}$ and
its interquartile range are medians over the $N = 300$ control 5-train/2-test
resamples. Each 2-component row gives the selected combination followed by the
next-ranked combination that passed the boundary-saturation gate. Each
retinal-plus-cortical (R+C) row gives the fitted gain with the percentage of
resample solutions at the grid boundary.}
```

**문체 점검 결과**

| 항목 | 조치 |
|---|---|
| 부정 어휘 | `represents the fitted distortion poorly` 삭제 · `generalized worse than` 삭제. `rejected at the boundary-saturation gate` 은 게이트의 사실적 판정이므로 유지 |
| 과대주장 | `which the participants' confirmed residual CVD excludes` → `which is not compatible with the residual CVD confirmed in both participants` |
| 구어체 | 없음 |
| 본문 중복 | 도입 문단 전체, `Fits` 첫 문장, `cannot express the S-cone displacement`, `the observed interpolation deficit concentrates …`, 적합 절차·비교 가능성 문장 삭제 |
| 본문 문체 정합 | 절차는 과거형(`was held fixed`, `were evaluated`), 모형 성질은 현재형(`cancels`, `lies`)으로 Methods §2.10 과 맞춤 |

**2차 점검에서 추가로 뺀 것**: `Fits` 문단이 표 `tab:modelfits` 와 겹쳤다. 표가 이미 `$g \to 3.0$ ($100\%$ saturated)`, `$g = 2.95$ ($41\%$ saturated)`, `rejected (Gate 2)` 를 담고 있으므로 같은 값을 산문으로 되풀이하지 않는다. 남긴 것은 표에 없는 셋뿐이다 — 앵커별 포화 범위, 이득 $>2$ 의 함의, $\Delta$RDM 직접 적합 결과.

**분량**: 463 → 약 225단어, 최장 문단 273 → 약 100단어.

#### 9.1b S11 — 2차 문안 (Fable 검토 반영)

**반영한 지적**

| # | 지적 | 조치 |
|---|---|---|
| 1 | 60°/74° 앞의 연결 문장 삭제로 논리 단절 | `and none along the S-cone axis` 를 복원하고 `has no counterpart in the R+C family` 로 결론을 명시 |
| 2 | `\S\ref{sec:results:rc_insufficient}` 순환 참조 | 확인 결과 `sec:results:twocomp` 와 **같은 소절에 붙은 두 라벨**이고(`results_v4.tex:83-84`) 그 소절 94행이 이 부록을 가리킨다. 교차참조를 빼고 근거를 문단 안의 $\Delta$RDM 결과로 옮김 |
| 3 | $\Delta\lambda$ 가 원고 어디에도 정의되지 않음 | `for a cone-spectral shift $\Delta\lambda$` 삽입 |
| 4 | $g$ 눈금 불완전 — $[0,3]$ 탐색 범위가 읽히지 않음 | `reproduces the retinal shift at $g = 1$` 추가 |
| 5 | 용어 불일치 — Methods `retinal-plus-gain` vs 캡션 `retinal-plus-cortical` | 부록을 `retinal-plus-cortical (R+C)` 로 통일. **Methods §2.10 도 같이 고쳐야 한다**(약어 R+C 와 맞는 쪽이 cortical) |
| 6 | `three published cone-shift anchors` 에 출전 없음 | `published` 삭제 |
| 7 | 초안 내부 중복 — 앵커 선택 문장이 `Model` 과 `Fits` 에 각각 등장 | `Model` 문단에만 유지 |
| 8 | 캡션이 IQR 을 median 으로 읽히게 함 | `$\overline{L}_{\rm test}$ is the median, and IQR the interquartile range, of the held-out loss over …` 로 분리 |
| 9 | 캡션의 `boundary-saturation gate` 와 표 셀 `rejected (Gate 2)` 가 연결 안 됨 | 캡션에 `(Gate 2)` 병기 |

**과대주장 지적 — 지적이 옳고, 제시된 대안 대신 주장을 삭제했다**

현행 원고의 `A gain above 2 implies cortical overshoot past the undistorted hue, which the participants' confirmed residual CVD excludes` 는 두 가지로 성립하지 않는다.

1. $g > 2$ 는 왜곡이 사라지는 상태가 아니라 **부호가 뒤집힌 왜곡이 남는** 상태다. 잔여 CVD 와 모순되는 것은 $g = 2$ 이지 $g > 2$ 가 아니다.
2. 잔여 CVD 의 근거는 Ishihara 판독(`methods_v2.tex:36`)인데, Ishihara 는 변별을 재는 검사이지 지각 hue 각도의 변위를 재지 않는다. hue 변위 모형의 overshoot 를 배제할 근거가 되지 못한다.

검토자는 Tregillus(2021)의 보고 범위를 근거로 재서술할 것을 제안했으나, 그 논문의 실제 이득 범위를 확인하지 않은 상태이므로 채택하지 않는다. 대신 **생리적 주장을 빼고 모형·탐색의 사실만 남긴다.** Gate 2 의 근거는 적합 진단(경계 포화 = 오설정)이지 생리가 아니므로 이것으로 충분하다.

> A gain above $2$ reverses the sign of the modelled displacement, so estimates at the upper boundary are read as saturation of the search range rather than as gain values.

**반영 문안 (2차)**

```latex
\suppsection{Comparison with the retinal-family distortion model}{app:retinal_family}

\paragraph{Model.}
The retinal-plus-cortical (R+C) model attributes CVD color distortion to a
cone-spectral shift at the retinal level \parencite{machado2009}, optionally
augmented by a cortical compensation gain $g$
\parencite{boehm2014,tregillus2021},

\begin{equation}
  \delta\theta_{\rm RC}(\theta;\,g)
    = (2 - g)\,\delta\theta_{\rm Mach}(\theta)
  \label{eq:rc}
\end{equation}

where $\delta\theta_{\rm Mach}$ is the per-hue angular shift predicted by the
Machado model for a cone-spectral shift $\Delta\lambda$, evaluated here on the
Stockman and Sharpe cone fundamentals \parencite{stockman2000} rather than on
the Smith and Pokorny fundamentals for which it is defined. The gain reproduces
the retinal shift at $g = 1$, cancels it at $g = 2$, and reverses its sign above
that value. $\Delta\lambda$ was held fixed rather than fitted, and each
participant was evaluated at three cone-shift anchors for their subtype, $6.0$,
$6.5$ and $8.0$\,nm for deutan and $1.5$, $3.0$ and $10.0$\,nm for protan, with
the anchor of lowest held-out loss reported.

\paragraph{Fits.}
Fitted values appear in \cref{tab:modelfits}. In the protan participant the
proportion of resample solutions at the grid boundary ranged from $0\%$ to
$100\%$ across the three anchors. A gain above $2$ reverses the sign of the
modelled displacement, so estimates at the upper boundary are read as saturation
of the search range rather than as gain values. Refitting the family against
$\Delta$RDM alone returned the same boundary behavior.

\paragraph{Degrees of freedom of the family.}
The gain rescales $\delta\theta_{\rm Mach}$ uniformly, so every member of the
family displaces hues along the confusion axis and none along the S-cone axis.
The S-cone term of the 2-component model, $\beta_s \cos(\theta - 90^\circ)$,
lies $60^\circ$ from the deutan confusion axis and $74^\circ$ from the protan
one, and has no counterpart in the R+C family. The boundary behavior under the
$\Delta$RDM criterion alone follows from this restriction rather than from the
choice of fitting criterion.
```

**캡션 (2차)**

```latex
\caption{Distortion-model fits for both CVD participants, all scored on the same
held-out composite test-loss ($\overline{L}_{\rm test}$, lower is better;
\S\ref{sec:methods:selection}). The neural RDM atom in each adopted fit is V2
for the deutan and V1 for the protan participant. $\overline{L}_{\rm test}$ is
the median, and IQR the interquartile range, of the held-out loss over the
$N = 300$ control 5-train/2-test resamples. Each 2-component row gives the
selected combination followed by the next-ranked combination that passed the
boundary-saturation gate (Gate 2). Each R+C row gives the fitted gain with the
percentage of resample solutions at the upper grid boundary.}
```

**저자 확인이 필요해 반영하지 않은 지적 넷**

| 지적 | 사유 |
|---|---|
| $\Delta$RDM 직접 적합의 사양(어느 ROI 의 $L_{\rm RDM}$ 을 단독 atom 으로, 같은 grid·resample 인지) | 실제 설정을 확인하지 못했다. 이 문장이 "적합 기준과 무관하다"는 주장의 유일한 근거이므로 사양을 붙이는 편이 낫다 |
| deutan 의 앵커별 결과 부재, 앵커 소표 신설 제안 | 앵커별 $g$·포화율·$\overline{L}_{\rm test}$ 를 확보하지 못했다. protan 의 어느 앵커에서 포화가 $0\%$ 였다면 그 앵커가 왜 채택되지 않았는지 표로 보이는 편이 낫다 |
| R+C 행의 IQR 열이 비어 있는 이유 | protan R+C 는 $\overline{L}_{\rm test} = -0.86$ 이 있는데 IQR 만 없다. Gate 2 탈락 시 손실을 계산하지 않은 것인지 확인 필요 |
| `results_v4.tex:83-84` 의 라벨 두 개가 한 소절에 붙어 있음 | `sec:results:rc_insufficient` 를 따라간 독자가 R+C 전용 절을 기대하고 2-component 절에 도착한다. 라벨 정리는 부록 밖 사안 |

### 9.2 S2 `app:uncorrected` — 초안

**현황**: 산문 896단어(부록 최다), 7문단, 최장 152단어. 본문 포인터는 다섯이다.

| 포인터 | 본문이 이미 서술하는 것 | 부록에 기대하는 것 |
|---|---|---|
| `methods_v2.tex:71` (§2.4) | 두 파이프라인의 구성(단일 보간 대 MCFLIRT 합성), 보간 횟수 동일, 두 방식 모두에서 전 종점 평가, 2차 세션 재처리 | 기각된 경로의 기록 |
| `results_v4.tex:34` (§3.1) | 순열 귀무가 $0.35$ 근처라는 사실, HMC 하 hV4 $0.451$ ($p=.023$), V1–V3 $\ge .228$ | 순열 귀무의 산출 근거 |
| `results_v4.tex:68` (Fig. 캡션) | — | 두 파이프라인·두 기준의 영역별 검정 |
| `discussion_v3.tex:36` | 식별 보존과 보간 저하가 HMC 에서도 유지됨 | — |
| `discussion_v3.tex:51` | 영역 귀속과 protan 부호가 전처리·기저에 따라 달라짐 | — |

**중복으로 판정한 것**

1. `The two readouts dissociate under both pipelines` 이하 문단 — `results_v4.tex:34,45` 가 같은 수치를 이미 싣는다(hV4 $0.451$/$p=.023$, V1–V3 $p \ge .228$, 단일사례 대비가 정본에서만 유의). **표 `tab:interp_arms` 가 전부 담고 있으므로 산문을 최소화한다.**
2. `Procrustes disparity was recomputed under head-motion correction with every other element held fixed` — `results_v4.tex:56` 의 서술과 겹친다.
3. `The protan V1 elevation remained the largest deviation … weakened from $p = .007$ to $p = .077$` 및 `the largest deviation moved from V2 to V1` — `results_v4.tex:56` 과 `discussion_v3.tex:36` 이 같은 내용을 말하고, 표 `tab:motion_arms` 가 수치를 싣는다.
4. `Registration.` 첫 절의 `registration used mutual information initialized from the … header` — `methods_v2.tex:71` 과 겹치나, 부록 문단이 무엇을 다루는지 밝히는 최소 재진술이므로 유지한다.

**반영 문안**

```latex
\suppsection{Preprocessing pipelines and sensitivity analyses}{app:uncorrected}

\paragraph{The two pipelines.}
Head-motion correction lowered ROI temporal signal-to-noise ratio by $1.7$ to
$2.7\%$. In both pipelines the per-run linear and constant drift terms of the
general linear model constituted the entire nuisance model, and both left slice
timing, susceptibility distortion, and temporal filtering out. Within-run motion
was summarized as framewise displacement \parencite{power2012}, with rotations
converted to displacement on a 50\,mm sphere. Across the nine analyzed
participants mean framewise displacement was $0.318 \pm 0.044$\,mm (controls
$0.313 \pm 0.042$, CVD $0.338 \pm 0.046$), and $16.2\%$ of volumes exceeded
$0.5$\,mm.

\paragraph{Endpoints under the two pipelines.}
Interpolation and classification appear in \cref{tab:interp_arms} and Procrustes
disparity in \cref{tab:motion_arms}. The permutation null for interpolation lay
at $0.35$ in both pipelines. Individual cells of these grids are descriptive and
support no claim in the main text.

\paragraph{Session-2 endpoints under the harmonized arm.}
The second session was reprocessed with the anatomical images harmonized to the
first and with head-motion correction, and the fourteen pre-specified endpoints
were recomputed within each arm, so the control reference and the Session-1
unfiltered anchor come from the same reconstruction. The control reference moved
from $0.456$ to $0.445$ in hV4 adjacent accuracy. Eight of the ten directional
contrasts defined on the native voxel mask reversed between arms, as did five of
the ten defined on the run-matched mask, whereas the four contrasts at the
pre-specified target regions held in both arms. Every directional contrast in
the second session is therefore reported as provisional. The psychophysical
endpoints are independent of preprocessing and are unchanged.

\paragraph{Susceptibility distortion.}
A gradient-echo field map was acquired in each session and linked to the
functional runs through the BIDS \texttt{IntendedFor} field, and both pipelines
left it unconsumed, so the data retain distortion along the right--left
phase-encoding direction. Field-map-derived mean displacement within each
analyzed ROI ranged from $0.01$ to $0.76$ voxels ($0.02$--$1.52$\,mm) across the
nine participants. Within-ROI spatial variation, the component that distorts a
pattern rather than translating it, reached $0.05$--$0.21$ voxels in eight
participants and $0.38$ voxels ($0.76$\,mm) in the ninth. The residual cost is
spatial, reducing the precision with which atlas-defined regions are assigned to
functional voxels.

\paragraph{Registration.}
The functional series cover occipital cortex alone, so registration used mutual
information initialized from the scanner-defined obliquity in the NIfTI header,
which tolerates limited coverage and requires no white-matter boundary. Two
standard routes were evaluated first. A container-based route through fMRIPrep
did not complete the coregistration stage with these partial-coverage series.
Boundary-based registration within the custom pipeline placed the functional
slab on a different tissue boundary on visual inspection, an offset on the order
of $10$\,mm, where the mutual-information solution stayed within about $1$\,mm
of the visually verified position. Whole-brain overlap indices favor
boundary-based registration on these data, but Dice and ROI-coverage measures
respond to the extent of overlap rather than to the position of a partial slab
within the brain, so the choice rests on the visual criterion.

The mutual-information optimum is shallow under this field of view. Across the
runs of a single session, where the fitted transform should be identical, the
mean pairwise displacement of the solution ranged from $0.9$ to $4.2$\,mm.
Removing facial voxels from the anatomical image, which leaves the brain
unchanged, moved the solution by $1.9$\,mm in the deutan participant and
$9.4$\,mm in the protan participant. The transform is fixed within a run, so it
enters the eight hues of a run as run-to-run noise alone, which is attenuated by
averaging over the six runs. Rigid-body estimation and distortion correction are
constrained just as weakly when little of the head is imaged, so acquisitions of
this type would benefit from correction validated for partial coverage.
```

**문체 점검 결과**

| 항목 | 조치 |
|---|---|
| 부정 어휘 | `failed at the coregistration stage on every attempt` → `did not complete the coregistration stage` · `snapped the functional slab onto an incorrect tissue boundary` → `placed the functional slab on a different tissue boundary` · `an error on the order of` → `an offset on the order of` |
| 과대주장 | `which places it outside the set of explanations for the observed differences in representational geometry` 삭제. 변위가 subvoxel 이라는 사실은 남기고, 그것이 특정 설명을 배제한다는 추론은 뺀다 |
| 구어체 | `reached $0.318 \pm 0.044$\,mm` → `was $0.318 \pm 0.044$\,mm` (측정값에 도달 동사를 쓰지 않는다) |
| 본문 중복 | 파이프라인 구성 문장 셋, 보간·분류 문단 전체, disparity 문단의 재산출·영역 이동 서술 삭제 |
| 캡션 규칙 | `tab:motion_arms` 아래에 있던 서술적 유보를 본문 문단으로 이미 옮겨 두었으므로(§9 이전 작업) 두 표 캡션은 손대지 않는다 |
| 두괄식 | `Endpoints under the two pipelines.` 문단을 표 포인터로 시작하도록 정리. 결과는 두 표가 담는다 |

**분량**: 896 → 약 430단어, 7문단 → 6문단, 최장 문단 152 → 약 105단어.

**저자 확인이 필요한 항목**

| 항목 | 사유 |
|---|---|
| `The permutation null for interpolation lay at $0.35$ in both pipelines` | `results_v4.tex:34` 가 `the permutation null lay near $0.35$ (Supplementary~\cref{app:uncorrected})` 로 부록을 근거로 지목한다. 부록에 이 값의 산출 근거가 없으므로 표 `tab:interp_arms` 캡션의 `the permutation null mean is $0.35$ in both pipelines` 로 충분한지 판단이 필요하다 |
| 삭제한 `outside the set of explanations` 문장 | 왜곡이 기하 차이의 설명이 아니라는 논증은 심사에서 요구될 수 있다. Discussion 에 옮길지 판단 필요 |

#### 9.1c S11 — 3차 문안 (R+C 자유도 검증 반영)

**정본화한 분석**

`analysis/phase5_filter_optimization/scripts/rc_scone_projection.py` (신규) → `analysis/phase5_filter_optimization/results/rc_scone_projection.json`. 기존 `rc_1dof.delta_machado` 를 그대로 불러 8색 $\delta\theta_{\rm Mach}$ 를 얻고, Methods §2.10 의 2성분 기저 $\{\cos(\theta-90^\circ),\ \cos(\theta-\theta_{\rm conf})\}$ 에 최소제곱 투영한다. 절편이 없는 모형이므로 설명 비율은 비중심 제곱합 기준으로 보고한다.

| 아형 | $\Delta\lambda$ | $\beta_s$ | $\beta_c$ | $\lvert\beta_s/\beta_c\rvert$ | 기저가 담는 제곱합 |
|---|---|---|---|---|---|
| deutan | 6.0 / 6.5 / 8.0 nm | $-24.9$ / $-28.0$ / $-34.3$ | $+26.9$ / $+29.7$ / $+36.0$ | 0.92 / **0.94** / 0.95 | 0.33 / 0.32 / 0.33 |
| protan | 1.5 / 3.0 / 10.0 nm | $+0.4$ / $+1.2$ / $+5.4$ | $-5.6$ / $-10.5$ / $-22.3$ | 0.08 / **0.11** / 0.24 | 0.19 / 0.18 / 0.18 |

**철회하는 주장 둘**

1. `generates no component along the S-cone axis` (부록) 및 `cannot express the S-cone displacement` (`results_v4.tex:94`). deutan 에서 S-cone 성분이 혼동축 성분의 94 % 다. 사실은 **성분이 없다**가 아니라 **비율이 $\Delta\lambda$ 로 고정되어 독립적으로 조절되지 않는다** 이다. 원뿔 신호 수준에서는 $\Delta S = 0$ 이 맞으나, 원고 §2.10 이 S-cone 축을 $\theta = 90^\circ$ 인 hue 축으로 정의하므로 그 독법은 적용되지 않는다.

2. `Fitting a retinal-family model directly against $\Delta$RDM reproduced the same boundary behavior in both participants`. `s08/s09_pca_allcombos_composite_N300.json` 에서 $\gamma$ 항 없이 RDM 단독으로 적합하면 두 참가자 모두 채택 앵커에서 경계 도달률이 $0.0$ 이다(deutan `γ_|RDMV2|noLOCO` / rc_DPS_lit, protan `γ_|RDMV1|noLOCO` / rc_DPS_lit). 경계 행동은 손실 조합에 따라 달라진다.

**반영 문안 (3차)**

```latex
\suppsection{Comparison with the retinal-family distortion model}{app:retinal_family}

\paragraph{Model.}
The retinal-plus-cortical (R+C) model attributes CVD color distortion to a
cone-spectral shift at the retinal level \parencite{machado2009}, combined with
a cortical compensation gain $g$ \parencite{boehm2014,tregillus2021},

\begin{equation}
  \delta\theta_{\rm RC}(\theta;\,g)
    = (2 - g)\,\delta\theta_{\rm Mach}(\theta)
  \label{eq:rc}
\end{equation}

where $\delta\theta_{\rm Mach}$ is the per-hue angular shift predicted by the
Machado model for a cone-spectral shift $\Delta\lambda$. That model is defined
on the Smith and Pokorny cone fundamentals, and it is evaluated here on the
Stockman and Sharpe fundamentals \parencite{stockman2000}, the cone model used
elsewhere in this analysis. The gain reproduces the retinal shift at $g = 1$,
cancels it at $g = 2$, and reverses its sign above that value. $\Delta\lambda$
was fixed, and each participant was evaluated at three cone-shift anchors for
their subtype, $6.0$, $6.5$ and $8.0$\,nm for deutan and $1.5$, $3.0$ and
$10.0$\,nm for protan.

\paragraph{Fits.}
Fitted values appear in \cref{tab:modelfits}. Estimates at a grid boundary are
treated as saturation of the search range rather than as parameter estimates
(Gate 2; \S\ref{sec:methods:selection}). In the protan participant the
proportion of resample solutions at the boundary ranged from $0\%$ to $100\%$
across the three anchors, and the anchor of lowest held-out loss is reported.

\paragraph{Degrees of freedom of the family.}
The gain rescales one fixed per-hue profile, so the relative weight of the
S-cone-axis and confusion-axis content of $\delta\theta_{\rm Mach}$ is set by
the cone model rather than fitted. Projected onto the basis of
Eq.~\ref{eq:2comp}, that profile has $\lvert\beta_s / \beta_c\rvert = 0.92$ to
$0.95$ in the deutan participant and $0.08$ to $0.24$ in the protan participant
across the three anchors, and the two cosines together account for $0.32$ to
$0.33$ and $0.18$ to $0.19$ of its sum of squares. The 2-component model
assigns the two amplitudes independently, which is the degree of freedom the
family lacks.
```

**본문 동시 개정** (`results_v4.tex:94`)

```latex
By contrast, the retinal-family comparison model carries one free parameter
along a fixed profile. Its gain rescales the Machado cone shift as a whole, so
the relative weight of its S-cone-axis and confusion-axis content is set by the
cone model rather than fitted (Supplementary~\cref{app:retinal_family}), and it
reached the gain boundary in the deutan participant ($g = 3.0$). Scored on the
same held-out composite, its protan fit reached
$\overline{L}_{\rm test} = -0.86$ against $-1.54$ for the 2-component model.
```

**캡션 (3차)**

```latex
\caption{Distortion-model fits for both CVD participants, all scored on the same
held-out composite test-loss ($\overline{L}_{\rm test}$, lower is better;
\S\ref{sec:methods:selection}). Each R+C row is scored on the loss combination
adopted for the same participant's 2-component fit. The neural RDM atom in that
combination is V2 for the deutan and V1 for the protan participant.
$\overline{L}_{\rm test}$ is the median, and IQR the interquartile range, of the
held-out loss over the $N = 300$ control 5-train/2-test resamples. Each
2-component row gives the selected combination followed by the next-ranked
combination that passed the boundary-saturation gate (Gate 2). Each R+C row
gives $\Delta\lambda$ and the median fitted gain with the percentage of resample
solutions at a grid boundary. No held-out loss is reported for a fit rejected at
Gate 2, which precedes ranking.}
```

---

#### 수정 사유 기록

| 수정 | 사유 |
|---|---|
| `cannot express the S-cone displacement` → `the relative weight … is set by the cone model rather than fitted` | 투영 결과 deutan $\lvert\beta_s/\beta_c\rvert = 0.94$. 성분이 없다는 서술이 사실과 어긋난다. 자유도 차이는 성분의 유무가 아니라 **독립 조절 가능성**이다 |
| `saturated the gain boundary in both participants ($g = 3.0$ and $2.95$)` → deutan 만 명시 | protan 은 $41\%$ 로 Gate 2 문턱 $50\%$ 아래이며 게이트를 통과했다. 부록이 이미 그렇게 적고 있어 본문과 어긋났다 |
| $\Delta$RDM 직접 적합 문장 삭제 | 정본 JSON 에서 채택 앵커의 경계 도달률이 $0.0$ 이다 |
| `A gain above $2$ … so estimates at the upper boundary are read as saturation` → `Estimates at a grid boundary are treated as saturation … (Gate 2)` | 두 절 사이에 인과가 없었다. 포화로 읽는 근거는 Gate 2 의 정의이지 부호 반전이 아니다. `upper` 를 뺀 것은 protan 1.5 nm 에서 하한 포화가 나타나기 때문이다 |
| `optionally augmented by` → `combined with` | 식 (6)에 $g$ 가 항상 들어가므로 `optionally` 가 식과 어긋난다 |
| `retinal-plus-gain` → `retinal-plus-cortical` | 약어 R+C 와 맞는 쪽으로 통일. **Methods §2.10 도 함께 고쳐야 한다** |
| `three published cone-shift anchors` → `three cone-shift anchors` | 출전 인용이 없고, 정본 코드의 키가 `rc_DPS_lit`, `rc_Boehm_*`, `rc_JND_Lamb` 이어서 셋 중 하나는 참가자 자신의 JND 에서 역산한 값이다. `published` 는 셋 모두 문헌값이라는 인상을 준다 |
| `Model` 문단 끝의 앵커 선택 문장을 `Fits` 로 이동 | 1차 문안에서 같은 내용이 두 문단에 있었다 |
| 캡션 `$\overline{L}_{\rm test}$ and its interquartile range are medians` → 둘을 분리 | IQR 이 median 으로 읽혔다 |
| 캡션에 `Each R+C row is scored on the loss combination adopted for the same participant's 2-component fit` 추가 | 손실 조합이 다르면 게이트 통과 여부가 달라진다. 비교 가능성의 전제라 표에 명시해야 한다 |
| 캡션에 $\Delta\lambda$ 추가 | R+C 행이 어느 앵커인지 표에서 알 수 없었다 |

#### 9.1d S11 — 과보상 논거 채택 (저자 지시, 채택 조합으로 한정)

R+C 를 쓰지 않는 근거를 **적합된 이득이 완전 상쇄를 넘어선다**는 사실로 앞세운다. 현행 원고의 `which the participants' confirmed residual CVD excludes` 보다 검증 가능한 형태이며, 표에서 바로 읽힌다.

**한정이 필요한 이유** — 과보상은 R+C 부류의 성질이 아니라 **채택 손실 조합에서 관찰된 사실**이다. `s0{8,9}_pca_allcombos_composite_N300.json` 의 채택 앵커 기준 경계 도달률은 다음과 같이 조합에 따라 달라진다.

| 참가자 | 채택 앵커 | 채택 조합 | RDM 단독 |
|---|---|---|---|
| deutan | JND 6.5 nm | $1.000$ | $0.000$ |
| protan | Boehm 3.0 nm | $0.413$ | $0.117$ |

`Fits` 문단을 다음으로 한다.

```latex
\paragraph{Fits.}
Fitted values appear in \cref{tab:modelfits}. Estimates at a grid boundary are
treated as saturation of the search range rather than as parameter estimates
(Gate 2; \S\ref{sec:methods:selection}). Under the loss combination adopted for
each participant the fitted gain lies above the value at which the cortical term
cancels the retinal shift, so these estimates fall outside the range of partial
compensation reported for anomalous trichromats
\parencite{boehm2014,tregillus2021}. In the protan participant the proportion of
resample solutions at the boundary ranged from $0\%$ to $100\%$ across the three
anchors, and the anchor of lowest held-out loss is reported.
```

`Degrees of freedom` 문단은 §9.1c 그대로 두어 기전을 담당한다. 과보상은 적합된 해가 왜 해석되지 않는지를, 자유도는 왜 그런 이득이 필요했는지를 답하므로 둘 다 필요하다.

**저자 확인 필요** — `the range of partial compensation reported for anomalous trichromats` 는 Boehm(2014)·Tregillus(2021)가 실제로 보고한 범위에 근거해야 한다. 두 논문의 보상 범위를 확인하기 전에는 이 절이 문헌 근거가 아니라 사전 믿음이 된다.

---

### 9.3 sub-10 오염 점검 — 해당 없음 (2026-09-06 확인)

`supplementary.tex:347` 의 `raised hue-channel-basis LORO accuracy from $0.545$ to $0.578$` 가 sub-10 을 포함한 10명 풀에서 나왔을 가능성이 제기되어 확인했다. **오염이 아니다.**

`analysis/phase3_decoder_comparing/results/loro/srm/sub-{01..10}_performance_raw.json` 에서 `results.srm.{ROI}.ForwardEncoding[fold].acc_exact` 를 6 fold 평균한 값이다.

| 항목 | 산출값 | `tab:loro_decoders` |
|---|---|---|
| V2 hue-channel, 통제군 $n=7$ | $0.545 \pm 0.077$ | $0.545 \pm 0.077$ |
| V1 hue-channel, 통제군 $n=7$ | $0.542 \pm 0.106$ | $0.542 \pm 0.106$ |
| V2 sub-08 / sub-09 | $0.458$ / $0.438$ | $0.458$ / $0.438$ |
| (참고) V2 sub-10 | $0.354$ | 표에 없음 |

통제군 평균은 sub-01–07 일곱 명이고 CVD 는 두 명이다. 제기된 $0.562$ 는 V1 을 10명으로 평균한 $0.563$ 에 가까워 V1/V2 혼동으로 판단한다.

**다만 같은 문단에 두 가지 문제가 남는다.**

| 문제 | 조치 |
|---|---|
| $0.545$ 가 어느 영역의 값인지 밝히지 않음 (V2 이다) | 영역 명시 |
| `an orthogonal rotation that uses no stimulus labels` | §2.5 는 $8\times8$ 회전이 hue 축에 작용해 hue 행을 대응시킨다고 적는다. 색 라벨을 쓰지 않는다는 서술과 모순이다. 정확한 진술은 **훈련 대상 run 이나 hue 를 참조하지 않는다** 이다 |

```latex
The run-level Procrustes alignment (\S\ref{sec:methods:roi}) maps runs 2--6 onto
a fixed run-1 reference, and the rotation is estimated without reference to the
held-out run or hue, so the alignment frame does not depend on the fold.
Re-estimating the alignment inside each fold raised hue-channel-basis LORO
accuracy at V2 from $0.545$ to $0.578$.
```

---

### 9.4 S12 `app:identifiability` — 초안 (서브에이전트 작성, 저자 검토 대기)

#### §S12 `Identifiability of the fitted parameters` — 압축 개정 초안

대상: `docs/PAPER/Supplementary/supplementary.tex` 539–591행 (`\suppsection{Identifiability of the fitted parameters}{app:identifiability}` 부터 `fig:landscape` 까지). 원고 파일은 수정하지 않았다.

---

##### 1. 본문 포인터와 본문이 이미 서술하는 내용

`grep -rn "app:identifiability" Methods/ Results/ Discussion/ Supplementary/` 결과, 현행 파일 기준 6건(아카이브·`.bak` 제외).

| # | 위치 | 부록에 기대하는 것 | 본문이 그 자리에서 이미 말하는 것 |
|---|---|---|---|
| P1 | `Methods/methods_v2.tex:167` (Fig. pipeline 캡션) | 두 참가자의 loss landscape 와 resample uncertainty 그림 | 그리드 범위·해상도, 그림이 deutan 표면임 |
| P2 | `Methods/methods_v2.tex:216` ($L_{\rm RDM}$) | 두 reduction(PCA vs SRM)의 일치도 | $L_{\rm RDM}$ 이 PCA($K=6$) 공간에서 계산됨, 28쌍 상관 $r=0.77$–$0.89$(V3 $0.39$–$0.58$), PCA 가 production basis, SRM 공간에서 절차 전체를 반복했음 |
| P3 | `Methods/methods_v2.tex:219` (composite loss) | $L_{\rm LOCO}$ 의 정의 | hV4 held-out 반응을 채점하는 atom 이고 두 참가자 모두에서 선택되지 않았음 |
| P4 | `Methods/methods_v2.tex:230` (selection) | control false-positive rate 와 control refit 의 파라미터 크기 분포 (§S12·§S13 에 descriptive 로) | IQR·modal-bin 비율·7-fold 범위로 안정성을 요약했음 |
| P5 | `Methods/methods_v2.tex:237` (§Identifiability and recovery) | 네 검사의 **전체 결과** | 네 검사의 **목적·설계·로직 전부**: Test 1 = 알려진 왜곡을 control encoder 로 통과시켜 합성, 잔차 구조에 맞춘 잡음, 그리드 재적합(선택 절차는 반복 안 함); Test 2a = $(0^\circ,0^\circ)$ 진값 + 실제 control 역치, 축별 불확실성 floor; Test 2b = 7명 control 을 pseudo-CVD 로 재적합, one-sided rank-distance percentile; Test 2c = 8색 라벨 순열 $N=1000$; 검사는 선택에 개입하지 않음; 6검사 BH $\alpha=0.05$ |
| P6 | `Results/results_v4.tex:92` (§twocomp) | 위 결과의 상세 | deutan 은 300 resample·7 fold·두 basis 에서 robust, $42^\circ > 26^\circ$ recovery uncertainty; protan 은 basis-sensitive, PCA $(2^\circ,+24^\circ)$ vs SRM $(32^\circ,0^\circ)$, $24^\circ$ 는 uncertainty 안; 6검사 중 BH 후 유의 없음 → descriptive embedding; S-cone $6^\circ$·$2^\circ$ 는 그 축 uncertainty 아래 |
| P7 | `Discussion/discussion_v3.tex:41` | protan 에서 $\hat\beta_c$ 부호가 reduction basis 에 의존한다는 근거 | 부호 의존 사실 자체, 전처리 의존은 §S13 (`app:fit_stability`) |

부록에 남아야 하는 것(본문에 없는 것)은 다섯 가지다. (i) $L_{\rm LOCO}$ 정의식, (ii) 각 검사의 표본 구성과 합성 설정(140 = 7 donor × 20 draw, 잡음 PC 20 + AR(1) 0.3, 역치 스케일링, 2b 의 결정론적 7건, 2c 의 ROI 공통 순열), (iii) 검사별 기준과 수치(표), (iv) 두 basis 에서의 $\hat\beta_c$ 부호 resample 계수(171/300, 17 %/26 %, 300/300), (v) landscape 그림.

##### 2. 삭제 근거

| 현행 문장 (539–591행) | 처분 | 중복 위치 |
|---|---|---|
| "Test 1 assesses voxel-level parameter recovery, Test 2a measures the algorithm's noise floor, and Tests 2b and 2c assess specificity to CVD data." | 삭제 | P5 (Methods 237행이 네 검사 목적을 서술) |
| "Each ran on the two selected fits with PCA-basis voxel synthesis (spatial PCA(20) on SRM-projected amplitudes) as the feature space." | 삭제, 한 절로 대체 | P5 ("selected for each participant"); 괄호 안 기술은 부정확함 — §6-2 |
| "Benjamini–Hochberg correction across the six test-bearing checks (2 candidates × 3 tests, α = 0.05) returned no result below threshold." | 삭제 | P5 (6검사 BH), P6 ("None … reached significance after BH") |
| "The selected optimum is therefore treated throughout as a descriptive embedding … rather than as a point estimate with physiological magnitude." | 삭제 | P6 ("reported as descriptive embeddings … rather than physiological point estimates") |
| $L_{\rm LOCO}$ 문단 (정의식 포함) | 유지, 압축 | 본문에 없음 (P3 가 여기로 위임) |
| "Fitting the weights within participant keeps the prediction … control-trained weights do not transfer." | 한 문장으로 압축 | 본문에 없음; 설계 근거이므로 유지 |
| "Every check returned a verdict below its pre-specified criterion in both participants" | 삭제 | 표 Verdict 열, P6 |
| Test 1 합성 설정(140, 역치 스케일링, 기준 $f_{10^\circ}\ge0.5$·$\lvert\text{bias}\rvert<10^\circ$, PC 20, AR(1) 0.3) | 목록으로 이동; 기준은 표에만 | 기준은 `tab:identifiability` Criterion 열과 중복 |
| "re-ran the same fitting pipeline on each sample" | 삭제 | P5 ("the grid fit was re-run … repeats the grid search rather than the full selection procedure") |
| "which measures the noise floor free of synthesis-design contamination" | 삭제 | P5 ("sets the per-axis uncertainty floor"); 나머지는 해석 |
| Test 2b 설명 "ranked the selected CVD fit's distance from the origin among the seven control distances" | 삭제 | P5 ("one-sided rank-distance percentile") |
| "Test 2b is descriptive and entered no selection decision." | 삭제 | P5 ("entered no selection decision" 이 네 검사 전체에 적용) |
| "Recovery separates the two axes by magnitude." | 삭제 | 해석 문장; P6 이 결론을 이미 서술 |
| "Test 2a places the effective parameter uncertainty at about 20° on β_s and 25° on β_c" | 삭제 | 표 2a 행(22/26, 16/24)과 세 번째 반올림으로 중복 (`MANUSCRIPT_EDITS_CONSOLIDATED.md:681` 이 지적한 삼중 반올림 20/25·22/26·16/24 의 잔존분); Results 는 $26^\circ$ 를 인용 |
| "so the non-dominant axes ($\lvert\hat\beta_s\rvert \le 6^\circ$) lie below that floor and remain unrecoverable" | 삭제 | P6 ("fitted S-cone amplitudes of 6° and 2° fall below the recovery uncertainty") |
| "The deutan dominant axis (42°) exceeds the floor and was recovered with a bias of 4.7°, against 16° on its non-dominant axis, which is the pattern that partial magnitude recoverability predicts." | 삭제 | 수치는 표 Test 1 행; "exceeds" 는 P6; 마지막 절은 해석 |
| "All four tests use the PCA-basis loss." | 표 캡션으로 이동 | — |
| "For the protan participant the sign of $\hat\beta_c$, which identifies the mechanism class, holds under that loss alone." | 삭제 | P6·P7 (basis-sensitive); "mechanism class" 는 본문 어휘가 아님 (Discussion 은 "sign of the dominant confusion-axis term") |
| "Under the SRM-basis loss the modal argmin is (32°, 0°) in 171 of 300 resamples, leaving $\hat\beta_c$ positive in 17 % and negative in 26 %" | 표로 이동 | 본문에 없음 — 유지 |
| "so the two reductions return different mechanism classes for this participant" | 삭제 | 해석; P6 |
| "The deutan sign holds under both bases, at 300 of 300 resamples in each." | 표로 이동 | 본문에 없음 — 유지 |

##### 3. 개정 LaTeX 문안 전문

```latex
\suppsection{Identifiability of the fitted parameters}{app:identifiability}

\paragraph{Unselected loss atom: hV4 LOCO voxel prediction ($L_{\rm LOCO}$).}
For each held-out hue $c$, ridge weights $W_c$ were estimated from the remaining seven hues across all six runs, with the penalty chosen by generalized cross-validation (\S\ref{sec:methods:encoding}). The candidate distortion relabels each stimulus by its perceived hue, so the held-out response is predicted as $\hat{Y}_c = \mathbf{c}(\theta_c + \delta\theta_c)^\top W_c$, and $\rho_c$ is the Pearson correlation between $\hat{Y}_c$ and the participant's run-averaged pattern at hue $c$. The loss averages the complement over the eight hues:
%
\begin{equation}
  L_{\rm LOCO} = \frac{1}{8}\sum_{c=1}^{8}\bigl(1 - \rho_c\bigr)
  \label{eq:lloco}
\end{equation}
%
The weights were fitted within participant because voxel counts differ across participants and control-trained weights do not transfer.

\paragraph{Sample composition of the four checks.}
Each check was run on the PCA-basis loss of the selected combination (\S\ref{sec:methods:identifiability}). Criteria and outcomes are listed in \cref{tab:identifiability}.
\begin{itemize}
  \item Test~1: synthetic data at the selected optimum from 7 control donors $\times$ 20 noise draws ($n = 140$ per participant). Noise was drawn from the top 20 principal components of each donor's residual spatial covariance with an AR(1) correlation of $0.3$ across runs, and the psychophysical thresholds were scaled to the distortion magnitude at the ground truth.
  \item Test~2a: the same synthesis at a ground truth of $(0^\circ, 0^\circ)$ ($n = 140$), with each donor's measured thresholds in place of scaled ones.
  \item Test~2b: each control participant's measured amplitudes as a pseudo-CVD case ($n = 7$, one deterministic fit each).
  \item Test~2c: $N = 1{,}000$ permutations of the CVD color labels, the same permutation applied in every ROI, with the control data held fixed.
\end{itemize}

\begin{table}[h]
\centering
\caption{Pre-specified identifiability checks on the selected fit of each participant, computed on the PCA-basis loss. Test~1, parameter recovery at the selected optimum; Test~2a, recovery at a null ground truth; Test~2b, rank of the CVD fit among control pseudo-CVD fits; Test~2c, color-label permutation. Bias is the recovered minus the true parameter, given as $(\beta_s, \beta_c)$ and averaged over the seven donor cells; $f_{10^\circ}$ is the fraction of samples recovered within $10^\circ$ on both axes, and $f_{10^\circ}^{\rm origin}$ the same fraction referred to the origin. Test~2a entries give the median $|\hat\beta|$ on each axis with the interquartile range in parentheses. ${\rm rank}_{\rm dist}$ is the one-sided percentile rank of the CVD fit's distance from the origin among the seven control distances. Test~2c entries give the composite loss at the selected cell, the 5th percentile of the permutation distribution, and the one-sided permutation $p$ value, with lower loss indicating a closer fit. Verdict compares each entry with its criterion.}
\label{tab:identifiability}
\small
\begin{tabularx}{\textwidth}{llYYc}
\toprule
Test & Criterion & Deutan $(6^\circ, -42^\circ)$ & Protan $(2^\circ, +24^\circ)$ & Verdict \\
\midrule
1   & $f_{10^\circ} \geq 0.5$, $|$bias$| < 10^\circ$ & $f_{10^\circ} = 0.26$; bias $(+16^\circ, -4.7^\circ)$ & $f_{10^\circ} = 0.14$; bias $(+11^\circ, -27^\circ)$ & FAIL \\
2a  & $|$bias$| < 5^\circ$ & $22^\circ\;(40)$, $26^\circ\;(10.5)$; $f_{10^\circ}^{\rm origin} = 0.00$ & $16^\circ\;(17.5)$, $24^\circ\;(9)$; $f_{10^\circ}^{\rm origin} = 0.00$ & FAIL \\
2b  & ${\rm rank}_{\rm dist} = 1.0$ & $0.875$ & $0.875$ & FAIL \\
2c  & $p_{\rm perm} < 0.05$ & $-2.892$ against a $5\%$ cut of $-3.136$; $p = .167$ & $-1.681$ against $-3.053$; $p = .471$ & FAIL \\
\bottomrule
\end{tabularx}
\end{table}

\paragraph{Sign of $\hat\beta_c$ under the two reduction bases.}
\cref{tab:sign_basis} counts the sign of $\hat\beta_c$ over the $N = 300$ control resamples of \S\ref{sec:methods:selection}, under the PCA-basis loss used by the checks above and under the SRM-basis loss.

\begin{table}[h]
\centering
\caption{Sign of $\hat\beta_c$ across the $N = 300$ control 5-train/2-test resamples, by reduction basis. Entries are counts of resamples; every zero-valued entry is the $(32^\circ, 0^\circ)$ solution.}
\label{tab:sign_basis}
\small
\begin{tabular}{llccc}
\toprule
Participant & Basis & $\hat\beta_c < 0$ & $\hat\beta_c = 0$ & $\hat\beta_c > 0$ \\
\midrule
Deutan & PCA & 300 & 0 & 0 \\
Deutan & SRM & 300 & 0 & 0 \\
Protan & PCA & 0 & 37 & 263 \\
Protan & SRM & 77 & 171 & 52 \\
\bottomrule
\end{tabular}
\end{table}

\begin{figure}[htbp]
  % Supplementary figures are numbered S1, S2, ... \setcounter is global but
  % \renewcommand is local to the float, so the renewal is repeated in every
  % supplementary figure while the reset is made once, here, in the first one.
  \renewcommand{\thefigure}{S\arabic{figure}}\setcounter{figure}{0}
  \centering
  \includegraphics[width=\textwidth]{figS1_landscape}
  \caption{\textbf{Per-subject loss landscape and parameter uncertainty.}
  The $z$-scored composite loss over the $(\beta_s, \beta_c)$ grid, reconstructed on the full seven-control pool, with lower values in yellow.
  The loss combination is $\gamma_{\rm OY} + L_{\rm RDM}^{(V2)}$ for the deutan participant and $\gamma_{\rm all} + L_{\rm RDM}^{(V1)}$ for the protan participant.
  The red star marks the argmin of that surface, at $(\hat\beta_s, \hat\beta_c) = (6^\circ, -42^\circ)$ and $(2^\circ, +24^\circ)$ respectively.
  White points give the per-resample argmins over the $N = 300$ control 5-train/2-test resamples.}
  \label{fig:landscape}
\end{figure}
```

**참조 무결성.** `eq:lloco`, `tab:identifiability`, `fig:landscape` 는 그대로 유지했다 (`fig:landscape` 는 §S13 607행이, `app:identifiability` 는 본문 6곳이 참조). `tab:sign_basis` 는 신설 라벨이며 이 절 안에서만 참조한다. `\S\ref{sec:methods:identifiability}` 는 `Methods/methods_v2.tex` 의 기존 라벨이다. `tabularx` 의 `Y` 열 유형은 현행 표가 이미 쓰고 있다.

**§S13 과의 경계.** 전처리 파이프라인 간 부호 안정성(`app:fit_stability` "Sign stability across the two preprocessing pipelines")과 (32°, 0°) 이 PCA landscape 의 2차 basin 이라는 서술("Resample structure")은 §S13 에 그대로 두었다. Discussion 41행이 두 절을 각각 basis·preprocessing 으로 나누어 가리키므로 이 분업이 맞다.

##### 4. 개정 캡션

**`tab:identifiability`** (개정)

> Pre-specified identifiability checks on the selected fit of each participant, computed on the PCA-basis loss. Test 1, parameter recovery at the selected optimum; Test 2a, recovery at a null ground truth; Test 2b, rank of the CVD fit among control pseudo-CVD fits; Test 2c, color-label permutation. Bias is the recovered minus the true parameter, given as $(\beta_s, \beta_c)$ and averaged over the seven donor cells; $f_{10^\circ}$ is the fraction of samples recovered within $10^\circ$ on both axes, and $f_{10^\circ}^{\rm origin}$ the same fraction referred to the origin. Test 2a entries give the median $|\hat\beta|$ on each axis with the interquartile range in parentheses. ${\rm rank}_{\rm dist}$ is the one-sided percentile rank of the CVD fit's distance from the origin among the seven control distances. Test 2c entries give the composite loss at the selected cell, the 5th percentile of the permutation distribution, and the one-sided permutation $p$ value, with lower loss indicating a closer fit. Verdict compares each entry with its criterion.

변경점: (a) "Criteria were fixed before the checks were run" 삭제 — Methods 237행 "pre-specified" 와 중복. (b) 2b 의 ${\rm rank}_{\rm dist}$, 2c 의 세 수치, Test 1 bias 의 부호 규약과 집계 단위를 정의 — 현행 캡션은 이 셋을 정의하지 않아 표를 읽을 수 없었다. (c) 결과 문장은 없다. (d) "averaged over the seven donor cells" 는 §6-1 의 확인 결과에 따라 문구를 바꿔야 할 수 있다.

**`tab:sign_basis`** (신설)

> Sign of $\hat\beta_c$ across the $N = 300$ control 5-train/2-test resamples, by reduction basis. Entries are counts of resamples; every zero-valued entry is the $(32^\circ, 0^\circ)$ solution.

**`fig:landscape`** (소폭)

> Per-subject loss landscape and parameter uncertainty. The $z$-scored composite loss over the $(\beta_s, \beta_c)$ grid, reconstructed on the full seven-control pool, with lower values in yellow. The loss combination is $\gamma_{\rm OY} + L_{\rm RDM}^{(V2)}$ for the deutan participant and $\gamma_{\rm all} + L_{\rm RDM}^{(V1)}$ for the protan participant. The red star marks the argmin of that surface, at $(\hat\beta_s, \hat\beta_c) = (6^\circ, -42^\circ)$ and $(2^\circ, +24^\circ)$ respectively. White points give the per-resample argmins over the $N = 300$ control 5-train/2-test resamples.

변경점: 별 위치 문장에서 참가자명 반복을 제거했을 뿐 내용은 같다. 측정 대상·기호·색 규약만 있고 결과 문장은 없다.

##### 5. 문체 점검

**부정 어휘**

| 현행 | 처리 |
|---|---|
| "remain unrecoverable" | 삭제 (Results 가 "bounded rather than estimated" 로 이미 서술) |
| "no synthetic psychophysical signal", "free of synthesis-design contamination" | "with each donor's measured thresholds in place of scaled ones" 으로 대체 — 무엇을 썼는지만 적음 |
| "returned no result below threshold" | 삭제 (Results 중복) |
| "control-trained weights do not transfer" | 유지 — 설계 근거를 이보다 짧게 쓸 수 없고, 단순 사실 서술 |
| 표의 "FAIL" | 유지 — 사전 지정된 verdict 라벨이며 Methods·Results 가 이 판정 체계를 전제함. 바꾸려면 "Below criterion" 정도가 대안 (§6-6) |

**과대주장·해석**

| 현행 | 처리 |
|---|---|
| "which identifies the mechanism class" / "return different mechanism classes" | 삭제 — Discussion 은 부호를 "sign of the dominant confusion-axis term" 으로만 부르며 mechanism class 라는 상위 개념을 본문 어디에도 정의하지 않음 |
| "which is the pattern that partial magnitude recoverability predicts" | 삭제 — 두 참가자 표본에서 패턴 예측을 말하는 해석 |
| "Recovery separates the two axes by magnitude" | 삭제 — 같은 이유 |
| "The selected optimum is therefore treated throughout as …" | 삭제 — 결론 문장은 Results 의 몫 |

**구어체·전보체**

| 현행 | 처리 |
|---|---|
| "Every check returned a verdict below its pre-specified criterion" | 삭제 (표) |
| "(7 cases per candidate, deterministic)" | "($n = 7$, one deterministic fit each)" — 괄호 안 나열을 완전한 명사구로 |
| "shuffled the CVD trial labels" | "permutations of the CVD color labels" — Methods 237행 어휘("permutes the eight color labels")와 통일. 현행 "trial labels" 는 부정확(순열 단위는 색 라벨) |
| "PCA basis, 7 control donors × 20 noise draws = 140 samples per candidate" | "7 control donors $\times$ 20 noise draws ($n = 140$ per participant)" — "candidate" 를 본문 어휘 "participant" 로 |

**시제·문체 일치.** 절차는 과거형("were estimated", "was run", "was drawn", "were scaled", "were fitted"), 모형 성질은 현재형("relabels", "is predicted", "averages", "differ", "do not transfer"). Methods 237행("Synthetic CVD responses were generated … the grid fit was re-run")과 같은 배치다. 현행의 "Fitting the weights within participant keeps the prediction …"(현재 동명사 주어)은 "The weights were fitted within participant because …" 로 바꿨다.

**§0.7-E(세미콜론).** 산문에는 세미콜론이 없다. 표 셀과 캡션의 목록 구분자에만 남겼다(`MANUSCRIPT_EDITS_CONSOLIDATED.md:682` 의 규칙과 일치).

##### 6. 저자 확인이 필요한 항목

1. **Test 1 행의 집계 단위가 섞여 있다 (수치 불일치, 수정하지 않음).** `results/redteam/param_recovery_voxel_v6_pca_v2.json` 의 7 donor cell 에서 직접 재계산했다.

   | 항목 | deutan mean / median | protan mean / median | 원고 값 | 원고가 따른 집계 |
   |---|---|---|---|---|
   | $f_{10^\circ}$ | 0.264 / 0.200 | 0.136 / 0.150 | 0.26 / 0.14 | **mean** |
   | bias $\beta_s$ | +18.6 / +16.0 | +11.9 / +11.0 | +16 / +11 | **median** |
   | bias $\beta_c$ | −4.7 / −4.0 | −26.4 / −27.0 | −4.7 / −27 | deutan **mean**, protan **median** |

   즉 $f_{10^\circ}$ 는 평균, bias 는 중앙값인데 deutan $\beta_c$ 만 평균이다. 두 정본 요약이 서로 다른 집계를 쓴다: `verdict_matrix_v2.md`(중앙값: f10 0.20/0.15, bias (16,−4)/(11,−27))와 `uncertainty_summary.md`(평균: f10 0.26/0.14, "β_c bias 30.9→4.7"). 아카이브 `Supplementary/archive/S3_identifiability.tex`(2026-06-05)부터 같은 혼합이었다. 한 집계로 통일하고 캡션에 명시할 것을 권한다. 초안 캡션의 "averaged over the seven donor cells" 는 잠정이다. 140개 표본을 합쳐 계산하면 $f_{10^\circ}$ = 0.293 / 0.157 로 또 다르다.

2. **"spatial PCA(20) on SRM-projected amplitudes" 는 코드와 맞지 않아 삭제했다.** `scripts/forward_voxel_synth.py:145–180` 에서 rank 20 은 donor 잔차의 **공간 공분산 PC 수**(`SPATIAL_COV_RANK = 20`)이고, 입력은 `neural_loss.load_amplitudes` 가 읽는 voxel-space `amplitudes_procrustes.npy` 이지 SRM 투영본이 아니다. $L_{\rm RDM}$ 의 PCA 공간은 $K = 6$ 이며 Methods 216행이 이미 서술한다. 초안은 "PCA-basis loss" 와 "top 20 principal components of each donor's residual spatial covariance" 로 두 사실을 분리해 적었다. 이 해석이 맞는지 확인 바란다.

3. **신설 표 `tab:sign_basis` 의 protan PCA 행(0 / 37 / 263)은 원고에 없던 수치다.** `results/closure/selection/s09_pca_allcombos_composite_N300.json` 의 `γALL|RDMV1|noLOCO` 300 resample 에서 계산했다: argmin 이 $(2^\circ,+24^\circ)$ 263회, $(32^\circ,0^\circ)$ 37회, 음수 0회. 표를 완성하기 위해 넣었으며 빼도 나머지 행은 성립한다. 원고의 17 %/26 % 는 정확히 52/300 (17.3 %)·77/300 (25.7 %) 이고, 171/300 과 deutan 300/300(두 basis)도 같은 폴더의 JSON 과 일치한다. 원고 문장의 백분율 대신 계수(count)로 적었다.

4. **`tab:fit_stability` 와의 관계.** §S13 표는 protan 의 SRM-basis IQR 을 $(0^\circ, 2^\circ)$ 로 보고한다. 171/300 이 $(32^\circ,0^\circ)$ 이고 나머지 129 가 양·음으로 갈리는 분포에서 $\beta_c$ IQR 이 $2^\circ$ 인지는 §S13 소관이라 검증하지 않았다. 두 표가 같은 300 resample 을 쓰므로 저자가 한 번 대조하면 좋겠다.

5. **Test 2a 의 출처.** 표의 2a 값은 `null_within_hc_loo_v6_pca.json` 의 B2 arm(140 realization; deutan $|\hat\beta_s|$ 22 (IQR 40), $|\hat\beta_c|$ 26 (10.5); protan 16 (17.5), 24 (9); $f^{\rm origin}_{10^\circ}$ 0/140)에서 그대로 재현됐다. 다만 `verdict_matrix_v2.md` 의 "Algorithm validation" 열은 "no recovery cells @ mag=0.0" 사유로 FAIL 을 적고 있어, 정본 verdict 파일과 표의 2a 행이 같은 산출물을 가리키지 않는다. 표기 문제일 뿐 수치 문제는 아니다.

6. **Verdict 열의 "FAIL".** 부정 어휘 금지 원칙에 걸릴 수 있으나 사전 지정 판정 라벨이라 유지했다. 바꾼다면 열 이름을 "Criterion met" 으로 하고 "No" 를 쓰는 것이 중립적이다.

7. **Test 1 의 역치 스케일링 서술.** "scaled to the distortion magnitude at the ground truth" 는 코드 주석(`synth_jnd = pool baseline × d_phys/d_perc(GT) + N(0, pool_sd)`)을 요약한 것으로 현행 문장을 그대로 유지했다. Methods 237행은 이 스케일링을 언급하지 않으므로 부록에만 있는 정보다.

8. **`\S\ref{sec:methods:identifiability}` 인용.** 현행 절은 Methods 의 identifiability 소절을 되가리키지 않았다. 초안은 목록 도입 문장에서 한 번 가리켜 "왜 네 검사인가" 를 본문에 위임한다. 순환 인용(본문→부록→본문)이 저널 관례상 문제되면 이 참조만 빼면 된다.

##### 7. 개정 전후 분량

산문만 계산(표·그림·수식 환경과 주석 제외, 수식은 1 토큰, 목록 항목은 각각 한 문단으로 셈). 같은 계수기로 현행 절을 재면 554단어·6문단·최장 199단어로, 지시문의 553/6/194 와 반올림 안에서 일치한다.

| | 단어 | 문단 수 | 최장 문단 |
|---|---|---|---|
| 개정 전 | 554 | 6 | 199 |
| 개정 후 | 289 | 8 (수식 앞뒤 2 + 목록 도입 1 + 목록 항목 4 + 부호 표 도입 1) | 85 ($L_{\rm LOCO}$ 정의 문단) |

수식 환경이 $L_{\rm LOCO}$ 문단을 둘로 가르므로 문단 수는 전후 모두 수식 앞뒤를 따로 센 값이다(현행 6 = 서두 1 + $L_{\rm LOCO}$ 2 + 검사 2 + basis 1). 산문 감소 −265단어(−48 %), 최장 문단 199 → 85.

캡션은 별도로 `tab:identifiability` 158단어(현행 92), `tab:sign_basis` 24(신설), `fig:landscape` 67(현행 73). 표 캡션이 길어진 것은 현행 캡션이 정의하지 않던 기호 세 개(${\rm rank}_{\rm dist}$, bias 규약, 2c 의 세 수치)를 정의했기 때문이다. 산문과 캡션을 합하면(표 본체 제외) 현행 719 → 개정 538 단어다.

**조판 확인.** 개정 블록을 `amsmath`·`booktabs`·`tabularx`·`cleveref` 와 `main.tex` 의 `\suppsection` 정의만 넣은 독립 문서로 `pdflatex` 2회 컴파일했다(스크래치패드 `s12_test.tex`). 오류·undefined reference·overfull box 없음. 본문 라벨 세 개(`sec:methods:encoding`, `sec:methods:identifiability`, `sec:methods:selection`)는 더미로 정의해 통과시켰으므로 실제 `main.tex` 에서의 참조 해상은 저자 빌드에서 확인이 필요하다.

---

### 9.5 S13 `app:fit_stability` · S14 `app:filter_eval` — 초안

#### Supplementary §S13·§S14 압축 개정 초안 (2026-09-06)

> 원고 파일은 수정하지 않았다. 아래 LaTeX 는 `Supplementary/supplementary.tex` 의 `\suppsection{Stability of the selected fits}{app:fit_stability}` (현행 598--639행)과 `\suppsection{Filter-evaluation session design and comparator}{app:filter_eval}` (현행 641--667행)을 통째로 대체하는 문안이다. 수치는 원고값을 그대로 옮겼고, 새로 끌어온 수치 한 건(§S13 표의 protan 경계 포화율 0.11)은 §6 에서 따로 표시했다.
>
> 단어 계수 방식: `table`·`figure` 환경과 주석을 제거한 산문만, 수식 `$…$` 는 1 토큰으로 센다. 이 방식으로 현행 산문은 §S13 416 / §S14 439 단어이고, 지시문의 431 / 448 과는 토큰화 차이만 있다.

---

##### §S13 Stability of the selected fits

###### 1. 본문 포인터와 본문이 이미 서술하는 내용

| 포인터 | 위치 | 부록에 기대하는 것 | 본문이 이미 서술하는 것 |
|---|---|---|---|
| `Methods/methods_v2.tex:230` (Parameter selection) | "The control false-positive rate and the distribution of fitted parameter magnitudes over the same control refits are likewise reported descriptively in \cref{app:identifiability} and \cref{app:fit_stability}" | 통제 pseudo-CVD 재적합에서 나온 **적합 크기 분포** | 재적합 절차(7명 통제를 pseudo-CVD 로, 나머지가 기준 풀) 자체는 `methods_v2.tex:237` Test 2b 와 `app:identifiability` 가 서술 |
| `Results/results_v4.tex:86` | "(per-ROI separations in \cref{tab:fit_stability})" | 표의 separation $d$ 행 | 게이트 결과(deutan 4 ROI, protan V1 단독)를 본문이 이미 진술 |
| `Results/results_v4.tex:90` | "(per-participant percentiles and losses in \cref{tab:fit_stability})" | 표의 grid percentile·$\Delta\overline{L}$ 행 | "7 폴드 모두 귀무보다 낫다, 상위 8 %" 를 본문이 진술 |
| `Results/results_v4.tex:102, 104, 106` (neural_role) | "(\cref{tab:fit_stability})" ×3 | 표의 ablation argmin·경계 포화율·IQR 행 | 세 argmin 값, "경계 포화율을 절반 이하로", "두 기저 모두에서 재표집 폭 축소", SRM 기저 $(32^\circ, 0^\circ)$ 를 본문이 전부 진술 |
| `Results/results_v4.tex:114` (filter) | "Both filters were frozen on the primary pipeline before the second session and were not re-derived, so the preprocessing comparison leaves the evaluated filter unchanged (\cref{app:fit_stability})" | 두 파이프라인 간 재적합 결과 | 필터가 primary 파이프라인에서 동결됐다는 사실 |
| `Discussion/discussion_v3.tex:41` | "in the protan participant even that sign depends on the reduction basis and on the preprocessing pipeline (\cref{app:identifiability}, \cref{app:fit_stability})" | 전처리 파이프라인에 따른 protan $\hat\beta_c$ 부호 의존 | 부호가 파이프라인에 의존한다는 결론 문장 |
| `Discussion/discussion_v3.tex:51` | "vary with preprocessing and with the reduction basis, so we report the geometry as descriptive (…\cref{app:fit_stability}…)" | 동일 | 동일 |

부록 밖에서 이미 서술된 것(따라서 §S13 에서 걷어낸 것): 절차(Test 2b 정의, ablation 정의)는 Methods `:230`·`:237` 에, 세 argmin 과 "경계 포화율 절반" 은 Results `:102`--`:106` 에, "descriptive embedding, 생리적 점추정 아님" 은 Results `:94` 와 `app:identifiability` 첫 문단에, SRM 기저 caveat(171/300) 은 `app:identifiability` "Basis caveat" 에 있다.

###### 2. 삭제 근거 (문단별)

| 현행 문단 | 처리 | 근거 |
|---|---|---|
| Control leave-one-out magnitude anchor (94 단어) | 수치 → 표 신설 블록; 산문은 절차 두 문장으로 축소 | 조합명($\gamma_{\rm OY}+L^{(V2)}$, $\gamma_{\rm all}+L^{(V1)}$)은 `tab:modelfits` 캡션·`fig:landscape` 캡션에 이미 두 번 있음. "close to the lower bound" 는 표를 읽으면 드러나는 해석이라 삭제 |
| Sign stability across the two preprocessing pipelines (173 단어) | 수치 → 표 신설 블록; 산문 한 문장("pipeline refit changes the neural atom alone")만 유지 | "the two participants diverge", "sign held / reversed" 는 Discussion `:41` 이 이미 진술. "boundary solutions lie on the same side as the median, so they bear on the magnitude rather than on the sign" 은 해석이며 표의 부호 비율(0.947)이 같은 정보를 담음. "We therefore report the deployed protan parameter as a frozen value and give it no physiological interpretation" 은 Results `:94`·`:114` 재진술 |
| Resample structure (54 단어) | 삭제 | 첫 문장(secondary basin)은 `fig:landscape` 와 `app:identifiability` Basis caveat 의 시각적 재서술. 둘째 문장의 $\hat\beta_c$ 집중·$\hat\beta_s$ 균일 분포는 표의 IQR $(8^\circ, 2^\circ)$ 행이 담는 정보. 구체값 $[-48^\circ, -36^\circ]$·202/300 은 §6 에 보존해 두었으니 행으로 복원할지 저자가 결정 |
| Gate statistics and neural-term ablation (94 단어) | 표 안내 한 문장으로 축소; 나머지는 캡션으로 이동 | "separation block reports the precondition…", "ablation block refits … holding every other element fixed", "All entries are medians over N = 300 … PCA basis unless…" 는 전부 캡션의 방법 기술이라 캡션에 두는 편이 맞음. ablation 정의는 Methods `:231` 재진술 |

###### 3. 개정 LaTeX 문안 (§S13 전문)

```latex
\suppsection{Stability of the selected fits}{app:fit_stability}

Table~\ref{tab:fit_stability} collects, for the two selected fits, the separation precondition, the held-out generalization of the selected cell, the neural-term ablation, the resample stability, the control pseudo-CVD refits, and the refit on the head-motion-corrected pipeline (\cref{app:uncorrected}). Every refit held the selected loss combination and every other element of the procedure fixed. The pipeline refit changes the neural atom alone, because the psychophysical atoms do not depend on preprocessing.

In the control refits each of the seven control participants was fit as a pseudo-CVD case, with the remaining six controls as the reference pool, under the loss combination selected for the CVD participant whose anchor it provides. These are the seven control distances that Test~2b ranks (\cref{tab:identifiability}). Both CVD magnitudes lie inside the corresponding control range, so $\|\hat\beta\|$ serves as a descriptive anchor and not as a test of CVD specificity.

\begin{table}[htbp]
  \caption{Gate statistics, neural-term ablation, resample stability, control pseudo-CVD refits, and preprocessing refit for the two selected fits. Separation $d$ is the standardized distance between the participant's loss value and the control leave-one-out distribution at each ROI, and the $\Delta$RDM atom was admissible only where $d$ met the pre-set threshold (\S\ref{sec:methods:selection}). The grid percentile is the rank of the selected cell's held-out loss among the $1{,}326$ grid cells. $\Delta\overline{L}$ is the change in an atom's held-out loss at the selected cell relative to the no-distortion cell $(0^\circ, 0^\circ)$, negative values favoring the fitted distortion, with the number of the seven leave-one-out folds that favor it in parentheses. Ablation rows give the argmin when the selected combination is refit with the psychophysical atoms alone, with the $\Delta$RDM atom alone, and in full, on the PCA basis unless the row names the SRM basis. The boundary-saturation rate is the fraction of resamples whose solution reached a grid edge, and parameter IQRs are given as $(\beta_s, \beta_c)$. $\|\hat\beta\|$ is the Euclidean norm of $(\hat\beta_s, \hat\beta_c)$; the control range and mean are over the seven control participants refit as pseudo-CVD cases under the CVD participant's selected loss. Preprocessing rows give the primary-pipeline value followed by the head-motion-corrected value (\cref{app:uncorrected}). Unless a block states otherwise, entries are medians over the same $N = 300$ control 5-train/2-test resamples.}
  \label{tab:fit_stability}
  \centering
  \small
  \begin{tabular}{lcc}
    \toprule
    & Deutan & Protan \\ \midrule
    \multicolumn{3}{l}{\emph{Separation precondition}} \\
    \quad $d$ at V1 / V2 / V3 / hV4 & $2.31$ / $1.94$ / $0.86$ / $2.19$ & $0.81$ / $-0.23$ / $-0.48$ / $-0.24$ \\
    \quad Loss combinations passing the gate & 25 & 4 \\ \midrule
    \multicolumn{3}{l}{\emph{Held-out generalization of the selected cell}} \\
    \quad Grid percentile & $4.6\%$ & $8.1\%$ \\
    \quad $\Delta\overline{L}$, psychophysical atom & $-13.85$ (5 of 7) & $+0.01$ (3 of 7) \\
    \quad $\Delta\overline{L}$, $\Delta$RDM atom & $-0.41$ (7 of 7) & $-0.47$ (7 of 7) \\ \midrule
    \multicolumn{3}{l}{\emph{Neural-term ablation (argmin)}} \\
    \quad Psychophysical atoms alone & $(16^\circ, -44^\circ)$ & $(26^\circ, +4^\circ)$ \\
    \quad $\Delta$RDM atom alone & $(4^\circ, -26^\circ)$ & $(0^\circ, +24^\circ)$ \\
    \quad Selected combination & $(6^\circ, -42^\circ)$ & $(2^\circ, +24^\circ)$ \\
    \quad Selected combination, SRM basis & $(8^\circ, -42^\circ)$ & $(32^\circ, 0^\circ)$ \\ \midrule
    \multicolumn{3}{l}{\emph{Resample stability, psychophysical alone $\rightarrow$ selected}} \\
    \quad Boundary-saturation rate & $0.23 \rightarrow 0.09$ & $0.00 \rightarrow 0.00$ \\
    \quad Parameter IQR, PCA basis & $(18^\circ, 6^\circ) \rightarrow (8^\circ, 2^\circ)$ & $(6^\circ, 4^\circ) \rightarrow (0^\circ, 0^\circ)$ \\
    \quad Parameter IQR, SRM basis & $(18^\circ, 6^\circ) \rightarrow (10^\circ, 4^\circ)$ & $(6^\circ, 4^\circ) \rightarrow (0^\circ, 2^\circ)$ \\ \midrule
    \multicolumn{3}{l}{\emph{Control pseudo-CVD refits ($n = 7$, own selected loss)}} \\
    \quad $\|\hat\beta\|$, CVD participant & $42.4^\circ$ & $24.1^\circ$ \\
    \quad $\|\hat\beta\|$, control range (mean) & $30.5^\circ$--$58.1^\circ$ ($49.1^\circ$) & $23.4^\circ$--$55.5^\circ$ ($35.7^\circ$) \\ \midrule
    \multicolumn{3}{l}{\emph{Preprocessing refit, primary $\rightarrow$ head-motion-corrected}} \\
    \quad Median $\hat\beta_c$ & $-42^\circ \rightarrow -46^\circ$ & $+24^\circ \rightarrow -12^\circ$ \\
    \quad Fraction of resamples with $\hat\beta_c < 0$ & $1.000 \rightarrow 0.947$ & $0.000 \rightarrow 0.793$ \\
    \quad Boundary-saturation rate & $0.09 \rightarrow 0.72$ & $0.00 \rightarrow 0.11$ \\
    \bottomrule
  \end{tabular}
\end{table}
```

###### 4. 개정 캡션 (§S13, `tab:fit_stability`)

현행 캡션에서 바꾼 점 두 가지.

- 결과 문장 삭제: "which left all four ROIs in the deutan participant and V1 alone in the protan participant" (Results `:86` 이 진술).
- 신설 블록 두 개의 기호·방법 정의 추가: $\|\hat\beta\|$ 정의, 통제 범위·평균의 산출 모집단(7 통제 pseudo-CVD 재적합), 전처리 행의 표기 순서(primary → head-motion-corrected).

캡션 본문은 위 LaTeX 블록 안의 `\caption{…}` 그대로다.

###### 5. 문체 점검

- 시제: 절차 과거형(`was fit`, `held … fixed`), 표·모형 성질 현재형(`collects`, `changes`, `do not depend`, `serves as`). Methods Parameter selection 소절과 일치.
- 해석 문장은 한 개만 남김: "$\|\hat\beta\|$ serves as a descriptive anchor and not as a test of CVD specificity". Methods `:230` 이 이 분포를 "descriptively" 보고한다고 예고하므로 필요.
- 구어체·과대주장 없음. 부정 어휘는 `not as a test`, `do not depend` 둘.
- 효능 서술 없음. 생리적 점추정 부정 입장은 Results `:94` 에 있으므로 여기서 재진술하지 않음.
- 캡션은 측정 대상·방법·기호·부호 방향만 기술.

###### 6. 저자 확인 항목

1. **표 신설 행의 protan 경계 포화율 `0.00 → 0.11`** 은 원고에 없던 값이다. 출처는 `analysis/phase5_filter_optimization/results/filter_robustness_arms/beta_sign_three_arms.json` 의 `sub-09/arms/hmc_v2/frac_beta_c_at_upper_edge = 0.107`. 싣지 않으려면 그 셀을 비우거나 행을 deutan 전용으로 바꾼다.
2. **deutan 전처리 경계 포화율 0.72 의 정의.** 같은 JSON 에서 `hmc_v2` 의 `frac_beta_c_at_lower_edge = 0.283` 과 `frac_beta_s_at_edge = 0.437` 의 **합**이 0.72 다. 두 축이 동시에 경계에 닿은 재표집이 있으면 이중 계산이다. 현행 원고의 "combined fraction" 표현이 이를 뜻하는지, 캡션의 "fraction of resamples whose solution reached a grid edge" 와 정합하는지 확인. baseline 의 0.09 는 `frac_beta_s_at_edge = 0.093` 단일값이라 문제없음.
3. **통제 앵커 수치의 1차 출처 미확인.** $30.5^\circ$–$58.1^\circ$ (평균 $49.1^\circ$), $23.4^\circ$–$55.5^\circ$ (평균 $35.7^\circ$) 는 `Supplementary/archive/supplementary_content.tex:216` 에 같은 값으로 있을 뿐, `results/closure/` JSON 에서 문자열 검색으로는 찾지 못했다. `specificity/s0809_pca_selected_loss-spec_synth-fakecvd-N200.json` 에 `30.594…` 과 `35.777…` 이 있는데, 이것이 출처라면 반올림은 $30.6$·$35.8$ 이어야 한다(현행은 절사). 원고 수치는 바꾸지 않았다.
4. **Test 2b rank 0.875 와 앵커 범위의 정합**: 두 참가자 모두 CVD 값이 통제 7명 중 최저 1명 위, 나머지 6명 아래이면 $(6+1)/8 = 0.875$ 로 맞는다. 표 자체의 내적 정합은 확인했다($\|\hat\beta\| = \sqrt{6^2+42^2} = 42.43$, $\sqrt{2^2+24^2} = 24.08$).
5. **캡션의 게이트 방향 불일치(기존 문제).** 현행 캡션은 "admissible only where it was positive and exceeded the pre-set threshold" 인데 Methods `:226` 은 "Cohen's $d$ of magnitude 0.5 or greater **in either direction**" 이다. protan V2/V3/hV4 의 음수 $d$ 는 $|d| < 0.5$ 라 결과에는 영향이 없다. 개정 캡션은 방향을 명시하지 않고 "$d$ met the pre-set threshold (\S\ref{sec:methods:selection})" 로 두었으니, Methods 쪽 규칙이 맞는지 확인 후 한쪽을 고칠 것.
6. **삭제한 Resample structure 문단의 수치 보존**: $\hat\beta_c \in [-48^\circ, -36^\circ]$ (300 중 300), $-42^\circ$ 또는 $-44^\circ$ 가 202/300, $\hat\beta_s$ 는 $0^\circ$–$14^\circ$ 에 거의 균일. 행으로 되살리려면 protan 대응값이 필요하다(현행 원고에 없음).
7. 전처리 재적합 수치 대조 결과(변경 없음): deutan $-42 \to -46$, 1.000 → 0.947; protan $+24 \to -12$, 0.000 → 0.793 모두 JSON 과 일치.

###### 7. 개정 전후 분량

| | 산문 단어 | 문단 수 | 최장 문단 |
|---|---|---|---|
| 현행 | 416 (지시문 기준 431) | 4 | 173 |
| 개정 | **139** | 2 | 72 |

표는 15 행에서 20 행으로 늘었다(신설 블록 2, 행 5).

---

##### §S14 Filter-evaluation session design and comparator

###### 1. 본문 포인터와 본문이 이미 서술하는 내용

| 포인터 | 위치 | 부록에 기대하는 것 | 본문이 이미 서술하는 것 |
|---|---|---|---|
| `Methods/methods_v2.tex:247` (Stimulus-space filter and its evaluation) | "Acquisition, comparator, run count, condition order, and single-case-inference details are given in \cref{app:filter_eval}" | 취득·비교자·런 수·조건 순서·단일사례 추론 상세 | 2세션 존재, 두 필터(개인화·macOS 배포), 비교 기준(비필터 1세션 + 통제 분포), 개인화 필터 파라미터 출처 |
| `Methods/methods_v2.tex:249` | (포인터 없음, 내용 중복 지점) | — | 단일사례 추론의 핵심 전부: $d_{cc}$ 로 보고, $p$ 미부착, 사유(grand-mean permutation null 편향), 심리물리 비교도 descriptive |
| `Results/results_v4.tex:151` (`fig:filter_eval` 캡션) | "Every panel is run-matched, with the control reference and the unfiltered baseline built from four runs to match the filter conditions (\cref{app:filter_eval})" | run-matching 절차 | 통제 기준과 비필터 기준을 4 런으로 재구성했다는 사실 |
| `Supplementary/supplementary.tex:677` (`app:exp2_outcomes` 첫 문장) | "run-matched as described in \cref{app:filter_eval}" | 동일 | — |

###### 2. 삭제 근거

| 현행 문단 | 처리 | 근거 |
|---|---|---|
| Comparator (72) | 3 문장으로 압축 | "It is the unmodified shipping product" 와 "operating-system-level post-display transform" 을 한 구로 병합. 선택 사유 한 문장은 설계 근거이므로 유지 |
| Acquisition (55) + Run-count adequacy 1 문단 (109) | 한 문단으로 병합, 스캐너 시간 근거는 한 문장 | "at the lower edge of that window" 삭제. "Four runs preserve the Session-1 separation…", "held that separation at every run count down to four" 는 그림이 보이는 결과의 문장 서술이라 삭제하고 $n = 4$ 수치만 나열 |
| Run-count adequacy 2 문단 (174) | 별도 `\paragraph{Run matching}` 으로 분리, 129 단어 | "an unmatched comparison would penalize the filter conditions twice, once … and once …" 는 앞 문장(noise inflates …)의 부연 해석이라 삭제. "which places the individualized filter's value below that baseline rather than above it" 는 개인화 필터 방향 언급이며 `tab:exp2_geometry` (protan V1 RDM: NF 0.33, Ind 0.26) 가 이미 보이므로 삭제 |
| Single-case inference (28) | 한 문장 유지 + Methods 포인터 | Methods `:249` 가 $d_{cc}$·$p$ 미부착·사유를 이미 담으므로 재진술하지 않음 |
| 주석 블록 (TERMINOLOGY resolved 2026-08-05) | 삭제 | 용어 결정 기록은 원고 조판과 무관. 필요하면 `words_trimming.md` 로 옮길 것 |

###### 3. 개정 LaTeX 문안 (§S14 전문)

```latex
\suppsection{Filter-evaluation session design and comparator}{app:filter_eval}

\paragraph{Comparator and rendering.}
The deployed comparator was the macOS accessibility Color Filter (System Settings $>$ Accessibility $>$ Display, build 26.5.1), an operating-system-level post-display transform used as shipped, at an intensity the participant set before scanning. It was chosen over a re-implemented retinal-simulation transform because it is the correction available to an end user. The individualized filter was rendered in PsychoPy from the frozen per-participant pre-image (\S\ref{sec:results:filter}).

\paragraph{Acquisition and run count.}
Eight runs were acquired, four per filter, in ABBA order. Four runs per condition took about 60 minutes; six would have taken about 90, beyond the 60--75 minutes over which attention and head motion remain acceptable. Across all $\binom{6}{n}$ run subsets of the six-run Session-1 data, hV4 adjacent accuracy at $n = 4$ gave a control mean of $0.45$ ($0.46$ at $n = 6$), a deutan value of $0.23$, and a protan value of $0.14$, with $d_{cc} < -2$ in both participants (\cref{fig:adjacc_saturation}). Four runs are fewer than recommended for RDM-based model comparison, so the session tests movement toward or away from the control reference and not the choice between model classes.

\begin{figure}[tb]
  \renewcommand{\thefigure}{S\arabic{figure}}  % see the note on the first supplementary figure
  \centering
  \includegraphics[width=\linewidth]{figS2_adjacc_saturation}
  \caption{\textbf{Hue-interpolation adjacent accuracy as a function of the number of runs.} LOCO adjacent accuracy (six-channel basis, OLS pseudoinverse decoder) as a function of the number of runs $n$, computed over all $\binom{6}{n}$ run subsets of the Session-1 data, per ROI. Black line, control mean $\pm$ SEM (shaded band); dashed line, the $0.25$ chance level; markers, the two CVD single cases (deutan, protan). The orange guide marks $n = 4$, the per-condition run count of the second session.}
  \label{fig:adjacc_saturation}
\end{figure}

\paragraph{Run matching.}
The filter conditions have four runs each, the Session-1 control reference and the unfiltered baseline six, and noise in either pattern inflates disparity and RDM similarity. Every neural index was therefore computed run-matched, with the filter conditions never subsampled. For the interpolation indices the control reference was subsampled to four runs. For the geometry indices the control means and the unfiltered baseline were rebuilt from all $\binom{6}{4} = 15$ four-run subsets, with the shared response model refit within each subset and the metrics averaged (\texttt{exp2\_runmatched\_geometry.py}). The control reference has $n = 7$ at V1--V3 and $n = 6$ at hV4, where one control has too few voxels. Matching raised the protan V1 RDM similarity of the unfiltered baseline from $0.25$ to $0.33$ and left the ordering of conditions unchanged on all four indices.

\paragraph{Single-case inference.}
Effect sizes follow \S\ref{sec:methods:stats}. Each neural contrast was recomputed after dropping each single run (leave-one-run separation) and after re-extracting both filter conditions on the voxel set of the unfiltered baseline.
```

###### 4. 개정 캡션 (§S14, `fig:adjacc_saturation`)

현행 캡션은 이미 결과 문장이 없어 한 구만 바꿨다: "The orange guide marks the deployed $n = 4$" → "The orange guide marks $n = 4$, the per-condition run count of the second session". "deployed" 는 이 원고에서 배포 필터(deployed filter)를 뜻하는 낱말이라 런 수 수식어로 겹쳐 쓰지 않는다.

###### 5. 문체 점검

- 시제: 절차 과거형(`was acquired`, `was subsampled`, `were rebuilt`, `was recomputed`), 설계·모형 성질 현재형(`have four runs each`, `inflates`, `tests movement`). Methods 필터 평가 소절(`completed`, `recomputed`, `is reported`)과 일치.
- 현행의 현재형 절차 서술("the control reference is subsampled", "are rebuilt") 을 과거형으로 통일.
- 효능 서술 없음: 개인화 필터와 배포 필터를 비교 우위로 놓는 문장 0. 남은 "the correction available to an end user" 는 비교자 선택 사유이지 우열 판단이 아님.
- 해석 문장은 "so the session tests movement toward or away from the control reference and not the choice between model classes" 하나. 세션이 무엇을 검정할 수 있는지 한정하는 문장이라 유지.
- 부정 어휘: `never subsampled`, `not the choice` 둘.

###### 6. 저자 확인 항목

1. **hV4 $n = 4$ 통제 평균 0.45 대 `tab:exp2_geometry` 의 0.46.** `run_count_validation/adjacc_saturation.json` 으로 직접 계산하면 $n = 4$ 통제 6명 평균 = 0.4556 (SD 0.106), $n = 6$ = 0.4653. 같은 값을 §S14 는 0.45(절사), `tab:exp2_geometry` 는 0.46(반올림)으로 적고 있다. 한쪽으로 통일할 것. deutan 0.2313 → 0.23, protan 0.1375 → 0.14 는 일치.
2. **"unchanged on all four indices."** 본문(`fig:filter_eval` 캡션·Results 필터 평가 소절)과 `tab:exp2_geometry` 는 신경 지표를 셋(hV4 adjacent accuracy, SRM disparity, RDM similarity)으로 센다. 넷째가 LORO 인지 forward-tuning $\rho$ 인지 명시하거나 "three" 로 고칠 것. 개정문은 현행 표현을 그대로 두었다.
3. **Single-case inference 문단이 절차만 적고 결과를 보고하지 않는다.** leave-one-run separation 과 baseline voxel set 재추출의 결과는 `analysis/phase6_behavioral_analysis/exp2_neural/RESULTS.md:61, 69--75` 에 있는데, 그 결과는 forward-tuning $\rho$ 의 **Optimal−Window(개인화−배포) 대비**에 대한 것이다. 이 원고는 그 대비를 주장하지 않으므로, (a) 결과를 싣지 않을 거면 이 두 문장 자체를 삭제하는 편이 일관되고, (b) 실으려면 어느 지표·어느 대비에서 유지됐는지 표 행으로 추가해야 한다. 초안은 현행대로 절차 문장을 유지했다.
4. **"noise in either pattern inflates disparity and RDM similarity"** 는 현행 원고 표현을 유지했다. 매칭으로 비필터 기준의 RDM 유사도가 0.25 → 0.33 으로 **올라간** 것과 방향이 맞는지(런이 줄어 잡음이 늘었는데 유사도가 상승) 저자가 한 번 확인할 것. 근거 파일: `exp2_neural/results/exp2_hc_likeness_sub-09_native.json` (비매칭) 대 `exp2_runmatched_geometry_sub-09_matched.json` 의 `V1/srm_rdm_paper/nofilter/spearman_to_hc = 0.332`.
5. macOS 빌드 번호 `26.5.1` 과 "intensity the participant set before scanning" 은 검증할 산출물이 없어 그대로 두었다.
6. 삭제한 주석 블록(`% TERMINOLOGY (resolved 2026-08-05) …`)을 보존하려면 `words_trimming.md` 로 옮긴다.

###### 7. 개정 전후 분량

| | 산문 단어 | 문단 수 | 최장 문단 |
|---|---|---|---|
| 현행 | 439 (지시문 기준 448) | 5 | 174 |
| 개정 | **337** | 4 | 129 |

§S14 는 Methods `:247` 이 다섯 항목(취득·비교자·런 수·조건 순서·단일사례 추론)을 이 절에 위임하고 있어 §S13 만큼 줄지 않는다. 더 줄이려면 §6-3 에 따라 Single-case inference 문단을 삭제(−32)하거나, run-matching 절차 문장 중 `\texttt{exp2\_runmatched\_geometry.py}` 이하를 Reproducibility 소절로 옮기는 방법이 있다.

---

##### 공통 확인: 표 중복 (`tab:fit_stability` ↔ 산문)

현행 §S13 산문이 표 값을 되풀이하는 곳은 없었다. 다만 Resample structure 문단의 "$\hat\beta_c$ concentrates … $\hat\beta_s$ almost uniformly" 는 표의 IQR 행 $(8^\circ, 2^\circ)$ 의 언어적 재서술이라 삭제했다. 본문 Results `:102`--`:106` 은 표의 ablation argmin 세 값과 SRM 기저 $(32^\circ, 0^\circ)$ 을 그대로 나열하므로 **본문–표 중복**은 남아 있다. 이는 본문 편집 범위라 손대지 않았다.

##### 공통 확인: 조판

두 블록을 `article` 클래스 하니스(`s1314_test.tex`, booktabs·cleveref·hyperref, `\suppsection` 매크로 동일 정의)에서 `pdflatex` 2회 통과시켰다. 오류 0, overfull 1건(`tab:fit_stability`, 60.6 pt). 같은 하니스에서 **현행 원본 표도 동일한 60.6 pt overfull** 을 내므로 신설 행이 아니라 하니스의 좁은 본문 폭 때문이다. `imag-ms-template.cls` 에서는 현행 표가 이미 조판되고 있으니 신설 행(가장 넓은 셀 `$30.5^\circ$--$58.1^\circ$ ($49.1^\circ$)` 은 기존 IQR 행보다 좁다)도 문제없을 것으로 본다. 최종 확인은 `main.tex` 빌드로 할 것.

---

### 9.6 S7 `app:cv_metrics` · S9 `app:triangulation` · S16 `app:statistics` — 초안

#### Supplementary S7 · S9 · S16 압축 개정 초안

대상 파일 `docs/PAPER/Supplementary/supplementary.tex` (원고 미수정, 초안만 작성). 본문 대조 파일 `Methods/methods_v2.tex`, `Results/results_v4.tex`, `Discussion/discussion_v3.tex`. 수치 검증은 `analysis/phase2_SRM_across_between/validation/results/*.json`(CVD n=3 저장본에서 sub-10 을 제외하고 재계산)과 `docs/PAPER/PUBLIC_REPO_PLAN_2026-09-05.md` §10.1 을 썼다.

---

##### 공통: 본문 포인터 대조 결과

| 포인터 위치 | 가리키는 절 | 본문이 부록에 기대하는 내용 | 본문이 이미 서술하는 내용 |
|---|---|---|---|
| `methods_v2.tex:124` | `app:cv_metrics` | "the leakage control on the run-level alignment, the cross-subject scheme, and the decoding and voxel-prediction metrics" | LORO·LOCO 폴드 구성(:127, :134), 8지선다 정확도와 chance 0.125(:127), 360도 판독 → 8색 최근접 배정(:105), adjacent accuracy 정의와 chance 0.25(:138) |
| `methods_v2.tex:129` | `app:cv_metrics` | 교차피험자 전이가 이루어지는 SRM 공간의 세부 | 전이의 두 목적지(held-out control / CVD), 인코더 훈련 집합(6명 / 7명), 셀 수(28 / 8), Mann--Whitney $U$ + rank-biserial |
| `methods_v2.tex:150` | `app:triangulation` | "two distances that use no shared response model, which establishes that it tracks a property of the data rather than of the alignment procedure" | disparity 정의(:147), LOO 통제 분포와 대칭 LOSO 추정량(:150), 크기 불변성(:151) |
| `methods_v2.tex:256` | `app:statistics` | $d_{cc} = t\sqrt{8/7}$ 의 상세 | Crawford--Howell $t$ ($df=6$), 기본 단측 방향, $d_{cc}$ 정의, 1,000 색라벨 순열, 10,000 피험자라벨 순열, BH $\alpha=0.05$ 의 두 족(식별성 6검정, 색대응 격자), Wilson 구간($n=64$), Hedges' $g$ |

`Results/`·`Discussion/` 에는 세 절을 가리키는 포인터가 없다. 표 `tab:triangulation`·`tab:variance_explained` 는 S9 안에서만 인용되고, **`tab:effect_sizes` 는 원고 어디에서도 `\cref` 되지 않는다.**

---

#### S7 `\suppsection{Cross-validation procedures and evaluation metrics}{app:cv_metrics}`

##### 1. 포인터와 본문 기존 서술

위 표의 `:124`, `:129`. 본문이 이미 담는 것: LORO/LOCO 폴드 구성, 8지선다 정확도·chance, 최근접 배정 규칙, adjacent accuracy, 교차피험자 전이의 목적지·훈련 집합·셀 수·검정.

##### 2. 삭제 근거

| 현행 문단 | 처리 | 근거 |
|---|---|---|
| `Cross-run alignment and leakage control` (106) | 압축 + 결과를 표로 | 부록 고유 내용. 다만 "an orthogonal rotation that uses no stimulus labels" 는 Methods `:84` 의 정의($\|X_1 - Q_r X_r\|_F$ 를 최소화하는 $8\times8$ 회전; 행 = 색)와 맞지 않는다. 회전은 두 런의 색 행 대응을 그대로 사용한다. 이 구절은 삭제하고 "estimated once from all six runs and held fixed" 로 바꿨다. nested 변형의 절차는 `analysis/phase3_decoder_comparing/model_comparison_validation/scripts/loro_baseline.py:131-170` (`procrustes_nested_fold`) 대로 적었다 |
| `Leave-one-subject-out (LOSO)` (81) | 목록으로 축약, 명칭 변경 | 두 목적지·셀 수·검정은 Methods `:129` 가 담는다. 남는 고유 정보는 (i) 공유공간 진입 방식, (ii) 인코더 훈련 데이터, (iii) 판독·채점뿐이다. "LOSO" 라는 약어는 `tab:disparity_loso` 와 S8 의 "symmetric LOSO"(disparity 추정량)와 충돌하므로 본문 용어 "cross-subject transfer" 로 통일했다 |
| `Evaluation metrics` (103) | **전문 삭제** | 8지선다 정확도·chance 0.125·최근접 배정은 Methods `:105`, `:127` 에 있다. 각도 MAE(chance $90^\circ$)는 본문·부록·그림 어디에도 보고되지 않는다. 복셀 예측 Pearson $r$ 은 `app:identifiability` 의 $L_{\rm LOCO}$ 식(`eq:lloco`)이 정의하며 독립 지표로는 보고되지 않는다 |

##### 3. 개정 LaTeX 문안

```latex
\suppsection{Cross-validation procedures and evaluation metrics}{app:cv_metrics}

\paragraph{Leakage control on the run-level alignment.}
The run-level rotation of \S\ref{sec:methods:roi} was estimated once from all six runs and held fixed during cross-validation, so a held-out run or hue contributed to the alignment frame of the training data. To bound the effect, leave-one-run-out classification was repeated with a nested variant in which, on each fold, the five training runs were centered, scaled, and rotated onto their own mean, and the held-out run was rotated onto that mean.

The variant changes the reference together with the nesting and therefore bounds the leakage rather than isolating it. Leakage through the fixed reference would raise the fixed-reference accuracy above the nested one; the observed difference runs the other way (\cref{tab:cv_leakage}).

\begin{table}[h]
\centering
\caption{Eight-way leave-one-run-out classification accuracy of the hue-channel basis model under the two run-alignment procedures, pooled over participants and the four regions (chance $0.125$). The fixed-reference procedure is the one used throughout the main text.}
\label{tab:cv_leakage}
\begin{tabular}{llcc}
\toprule
Procedure & Reference pattern & Rotation estimated from & Accuracy \\
\midrule
Fixed reference & run 1 & all six runs, once & $0.545$ \\
Nested & mean of the five training runs & training runs of each fold & $0.578$ \\
\bottomrule
\end{tabular}
\end{table}

\paragraph{Cross-subject transfer.}
The transfer of \S\ref{sec:methods:loro} differs from the within-participant schemes in three respects.
\begin{itemize}
\item Space. Training and test responses are the $k$-dimensional shared-space patterns of \S\ref{sec:methods:srm}; controls enter through their SRM bases and CVD participants through the SVD projection into the control-trained space.
\item Encoder. $W$ maps the six channels onto the shared dimensions and was estimated by the pseudoinverse of \S\ref{sec:methods:encoding} from the shared-space responses of the training controls, with all eight hues and all runs in training; the scheme therefore has no interpolation counterpart.
\item Readout. The held-out participant's shared-space responses were decoded by the same correlation readout and scored as eight-way classification accuracy against the chance level of $0.125$.
\end{itemize}
```

##### 4. 개정 캡션

- **신설 `tab:cv_leakage`** (위 문안에 포함). 측정 대상(8지선다 LORO 정확도)·풀링 단위·chance·어느 절차가 본문 절차인지만 적었다. 결과 문장 없음.
- 삭제되는 캡션 없음. 현행 절에는 표가 없었다.

##### 5. 문체 점검

- 절차 과거형(`was estimated`, `was repeated`, `were decoded`), 모형 성질 현재형(`replaces`, `maps`, `differs`). Methods `sec:methods:loro` 와 동일한 시제 배분.
- 삭제한 구어·과대 표현: "free of inflation from the alignment step" → 관찰된 방향만 진술. "uses no stimulus labels" → 삭제(§2 근거).
- 남긴 해석 1문장("Leakage through the fixed reference would raise …")은 표의 두 값이 왜 누출 상한이 되는지를 말하는 데 필요하다.
- 부정 어휘: `no interpolation counterpart` 1건(사실 진술, 유지).

##### 6. 저자 확인 항목

1. **`0.545 → 0.578` 은 sub-10 을 포함한 10명 풀링값이다.** `PUBLIC_REPO_PLAN_2026-09-05.md:270` 이 이미 지적했고, 9명 값은 `0.562 → 0.606`(방향 동일). 초안은 원고 값을 그대로 두었다. 교체하거나 캡션에 "ten participants of Session 1" 을 명시해야 한다. 어느 쪽이든 캡션의 "pooled over participants" 에 $n$ 을 적을 것.
2. `tab:cv_leakage` 의 "training runs of each fold" 행은 코드대로 적었다(각 훈련 런을 중심화·표준편차 스케일링 후 훈련 평균으로 회전, 검사 런은 자기 통계로 정규화 후 같은 평균으로 회전). 본문 Methods `:84` 는 "Scaling was not permitted" 라 하므로, nested 변형의 런별 스케일링이 본문 절차와 다른 점을 저자가 인지해야 한다. 초안 문안의 "centered, scaled" 가 그 차이를 드러낸다.
3. 교차피험자 전이에서 held-out control 이 7명 SRM 에서 얻은 자기 기저 $W_i$ 로 공유공간에 진입하는지(초안의 "controls enter through their SRM bases"), 아니면 6명 SRM 을 재훈련하는지 확인 필요. 현행 문단은 이를 명시하지 않았다.
4. 인코더 훈련이 훈련 통제군의 **전체 런을 풀링**하는지, 판독이 held-out 참가자의 **런별**로 이루어져 평균되는지(Results `:32` "Accuracy on their held-out runs") 확인 필요. 초안은 런 단위를 명시하지 않았다.
5. **본문 포인터 수정 제안 (`methods_v2.tex:124`)**: "The leakage control on the run-level alignment and the cross-subject scheme are given in Supplementary~\cref{app:cv_metrics}." 로 줄일 것("and the decoding and voxel-prediction metrics" 삭제). 절 제목도 "Cross-validation procedures" 로 줄이는 편이 내용과 맞는다.
6. 원고 어디에도 각도 MAE 가 보고되지 않는다. 지표를 되살릴 계획이 없다면 삭제가 맞다.

##### 7. 단어 수

| | 산문 단어 | 문단 수 | 최장 문단 |
|---|---|---|---|
| 개정 전 | 290 (사용자 집계 299) | 3 | 106 |
| 개정 후 | 219 (목록 항목 포함) | 산문 3 + 목록 3항 | 71 |

---

#### S9 `\suppsection{Alignment-independent checks on the disparity measure}{app:triangulation}`

##### 1. 포인터와 본문 기존 서술

`methods_v2.tex:150` 하나. 본문이 이미 담는 것: disparity 정의, 공통공간·대칭 LOSO 두 추정량, 크기 불변성, "two distances that use no shared response model" 이라는 목적.

##### 2. 삭제 근거

| 현행 문단 | 처리 | 근거 |
|---|---|---|
| ¶1 "Disparity tracks the same subject-level quantity …" (77) | 수치 삭제, 방법 목록으로 | pooled $r = 0.632 / 0.780$ 과 "strongest at V1 and V2" 는 `tab:triangulation` 의 전사다 |
| ¶2 crossnobis (87) | 정의는 목록으로, 결과는 나열로 | "reproduces the ordering without any alignment step" 은 결론문이자 부정확하다. 이 거리는 `amplitudes_procrustes.npy`(런 정렬본)에서 계산되므로 "no cross-participant alignment" 가 맞다. V1 $r = 0.833$, V2 $r = 0.733$ 은 표 전사 |
| ¶3 PCA / PCA--CCA (100) | 정의는 목록으로, $g$ 범위는 나열로 | "Pairwise alignment … noisier … which accounts for their size" 는 자기변호 해석. pooled $r$ 두 값은 표 전사 |
| ¶4 variance explained (85) | 2문장으로 | "places reconstruction quality outside the set of explanations", "a strong signal held in a different arrangement" 는 해석. "higher in CVD than in controls at all four ROIs" 는 표 전사. 검사의 목적 1절과 상관계수만 남긴다 |
| ¶5 scope (34) | 2문장으로 유지 | 정렬 재적합이 대응을 만들어낼 수 있다는 점을 흐리지 않기 위해, 이 절이 다루는 것(거리의 정렬 의존성)과 다루지 않는 것(색 특이성, 투영 동결 여부에 의존)을 분리해 둔다 |

##### 3. 개정 LaTeX 문안

```latex
\suppsection{Alignment-independent checks on the disparity measure}{app:triangulation}

Three distances that use no shared response model were computed for each of the nine participants from the run-aligned amplitudes of \S\ref{sec:methods:roi} and correlated with SRM disparity (\cref{tab:triangulation}).
\begin{itemize}
\item Crossnobis. An $8 \times 8$ cross-validated Mahalanobis distance matrix per participant in that participant's own voxel space \parencite{walther2016}, cross-validated over the 15 run pairs with Ledoit--Wolf shrinkage of the noise covariance. The participant score is $1 - r_s$ between this matrix and the control-mean matrix.
\item PCA. Each participant's hue-by-voxel pattern reduced to the region's $k$ by principal components, followed by Procrustes disparity over all participant pairs. The participant score is the mean disparity to the seven controls.
\item PCA--CCA. As PCA, with a canonical-correlation alignment of each pair before the Procrustes step.
\end{itemize}
Group-level contrasts under the three distances were as follows.
\begin{itemize}
\item Crossnobis: control-to-control minus control-to-CVD RDM similarity of $0.104$ at V1 (permutation $p = .120$) and below $0.05$ at V2, V3, and hV4.
\item PCA: Hedges' $g$, signed control--CVD minus control--control pairs, from $-0.13$ to $+0.40$ across regions.
\item PCA--CCA: $g$ from $-0.13$ to $+0.16$.
\end{itemize}
Variance explained by the shared response model under the symmetric leave-one-subject-out projection is given in \cref{tab:variance_explained}; the check asks whether elevated disparity could reflect poorer reconstruction of the CVD data. Variance explained and disparity were uncorrelated across participants (Spearman $r = -0.214$ pooled over regions, $p = .211$).

These checks concern the dependence of the distance on the alignment procedure. The color specificity of a deviation, which depends on whether the projection is held fixed, is treated in \cref{app:geometry_validity}.

\begin{table}[h]
\centering
\caption{Spearman correlation between SRM Procrustes disparity and three distances computed without the shared response model, over the nine analyzed participants within each region and pooled over the four regions ($n = 36$). Crossnobis: distance of the cross-validated Mahalanobis RDM from the control-mean RDM in the participant's own voxel space. PCA and PCA--CCA: mean pairwise Procrustes disparity to the seven controls after reduction to the region's $k$, without and with canonical-correlation alignment. Bold: $p < 0.05$.}
\label{tab:triangulation}
\begin{tabular}{lccccc}
\toprule
Distance & V1 & V2 & V3 & hV4 & Pooled \\
\midrule
Crossnobis (voxel space) & \textbf{0.833} & \textbf{0.733} & 0.550 & 0.300 & \textbf{0.632} \\
PCA                      & 0.633 & \textbf{0.850} & 0.333 & 0.533 & \textbf{0.780} \\
PCA-CCA                  & 0.483 & 0.433 & 0.100 & $-0.067$ & \textbf{0.544} \\
\bottomrule
\end{tabular}
\end{table}

\begin{table}[h]
\centering
\caption{Variance explained by the shared response model at the selected dimensionality $k$ under the symmetric leave-one-subject-out projection, in which controls and CVD participants are projected identically. Entries are group means over $n = 7$ controls and $n = 2$ CVD participants. Hedges' $g$ is signed control minus CVD.}
\label{tab:variance_explained}
\begin{tabular}{lcccc}
\toprule
ROI & $k$ & Controls & CVD & $g$ \\
\midrule
V1  & 4 & 0.352 & 0.407 & $-0.40$ \\
V2  & 4 & 0.331 & 0.416 & $-1.26$ \\
V3  & 3 & 0.250 & 0.314 & $-0.66$ \\
hV4 & 3 & 0.225 & 0.253 & $-0.39$ \\
\bottomrule
\end{tabular}
\end{table}
```

##### 4. 개정 캡션

- **`tab:triangulation`**: 상관 종류(Spearman)·표본 단위(영역별 9명, pooled 36)·세 거리의 정의·굵은 글씨 규칙만. 현행 캡션의 "with no alignment step" 은 런 정렬본을 쓰므로 삭제하고 "in the participant's own voxel space" 로 바꿨다.
- **`tab:variance_explained`**: 현행 캡션의 "so negative values indicate better reconstruction of the CVD data" 는 결과 방향 해석에 가까워 "signed control minus CVD" 로 줄였다. 표본 크기($n = 7 / 2$)와 $k$ 가 선택 차원임을 추가했다.

##### 5. 문체 점검

- 절차 과거형(`were computed`, `were as follows`, `were uncorrelated`), 정의 현재형(`is $1 - r_s$`, `concern`, `is treated`).
- 삭제한 결론·해석문 4건(§2 표). 남긴 해석은 VE 검사의 목적 1절뿐이다.
- 부정 어휘: `uncorrelated` 1건(통계적 사실), `no shared response model` 은 절의 정의어.
- "Spearman" 을 VE--disparity 상관에 명시했다. `PUBLIC_REPO_PLAN` §10.1 #5 가 Spearman 으로 정확히 재현됨을 확인했고, 본 검증에서도 $r = -0.214$, $p = .2109$ 로 재현됐다.

##### 6. 저자 확인 항목

1. **수치 재현 결과 (모두 일치)**. 저장 JSON 은 CVD n=3 본이므로 sub-10 을 제외하고 재계산했다.
   - Spearman vs 공통공간 SRM disparity: crossnobis V1 .833 / V2 .733 / V3 .550 / hV4 .300 / pooled .632; PCA .633 / .850 / .333 / .533 / .780; PCA--CCA .483 / .433 / .100 / −.067 / .544. `loo_consistent` 두 타임스탬프(144524, 163819) 모두 동일.
   - crossnobis 유사도 차(control--control − control--CVD): V1 0.104, V2 0.019, V3 0.046, hV4 0.045 → "below 0.05" 성립.
   - Hedges' $g$ (PCA): V1 +0.40, V2 +0.11, V3 −0.06, hV4 −0.13; (PCA--CCA): −0.13, +0.16, +0.14, −0.03 → 원고 범위와 일치.
   - VE (LOSO): 통제 .352/.331/.250/.225, CVD .407/.416/.314/.253, $g$ −0.40/−1.26/−0.66/−0.39 일치. VE--disparity Spearman pooled −0.214, $p$ = .211 일치.
2. **재현 불가 1건**: crossnobis V1 순열 $p = .120$ (n=2). 커밋된 JSON 은 n=3 본($p = .0508$, diff 0.122)이며 n=2 재실행 산출물이 없다(`PUBLIC_REPO_PLAN` §10.1 #8 과 동일 지적). 서버 산출물 회수 또는 재실행 필요.
3. `methods_v2.tex:150` 은 "two distances" 라 하는데 부록은 셋(crossnobis, PCA, PCA--CCA)이다. PCA--CCA 를 PCA 의 변형으로 보면 둘이지만, 표는 세 행이다. 본문을 "distances that use no shared response model" 로 바꾸거나 부록 첫 문장을 "two families of distance" 로 맞출 것.
4. 위 §6-1 의 영역별 $g$ 와 유사도 차는 원고에 없는 값이다. 범위 대신 영역별 값을 작은 표로 싣고 싶다면 그 값들을 쓸 수 있으나, 초안에는 원고에 있는 범위만 남겼다.
5. Hedges' $g$ 의 부호 규약("control--CVD minus control--control", 양수 = CVD 쌍이 더 멀다)은 `compute_pca_cca_replication.py:166-176` 의 `hedges_g(hc_hc, hc_cvd)` = (group2 − group1) 에서 확인했다. 현행 원고는 부호 규약을 밝히지 않았으므로 초안이 이를 추가했다.
6. 마지막 문단은 정렬 재적합이 색 대응을 흡수할 수 있다는 프로젝트 내부 결론(`app:geometry_validity` 첫 문장이 이미 원고에서 인정)과 어긋나지 않도록, 이 절의 주장 범위를 "거리의 정렬 의존성" 으로 한정했다. PCA--CCA 도 쌍별 라벨 대응에 정렬을 적합하므로 세 거리 중 crossnobis 만 적합된 투영이 없다는 점을 본문에 쓸지는 저자 판단에 맡긴다(초안에는 넣지 않았다).

##### 7. 단어 수

| | 산문 단어 | 문단 수 | 최장 문단 |
|---|---|---|---|
| 개정 전 | 383 | 5 | 100 |
| 개정 후 | 249 (목록 항목 포함) | 산문 4 + 목록 6항 | 48 |

---

#### S16 `\suppsection{Statistical analysis and effect sizes}{app:statistics}`

##### 1. 포인터와 본문 기존 서술

`methods_v2.tex:256` 하나. Methods `sec:methods:stats` 가 이미 담는 것: Crawford--Howell $t$ ($df = 6$), 기본 단측(결손 방향), $d_{cc} = t\sqrt{8/7}$, 1,000 색라벨 순열, 10,000 피험자라벨 순열, BH $\alpha = 0.05$ 의 두 족(식별성 6검정, 색대응 격자), Wilson 구간($n = 64$), Hedges' $g$. Methods `:129` 가 Mann--Whitney $U$ 와 rank-biserial 을 담는다. 검정 방향은 Methods `:127`(LORO 양측), `:139`(LOCO 단측 하), `:141`(색별 단측·비보정), `:150`(disparity 단측 상), `app:activation`(양측), `fig:filter_eval` 캡션(2차 세션 단측) 에 흩어져 있다.

##### 2. 삭제 근거

| 현행 문장 | 처리 | 근거 |
|---|---|---|
| "Unless noted otherwise, the significance threshold was $\alpha = 0.05$" | 삭제 | Methods `:150`, `:256` |
| "FDR correction was applied within two pre-specified families alone, the RDM hue-pair comparisons ($q = 0.05$, 28 pairs per participant) and the six parameter-identifiability checks" | **족 정의 교체** | 원고 어디에도 hue-pair RDM 비교에 FDR 을 적용한 결과가 없다(`grep "28 pairs\|hue-pair"` 0건). Methods `:256` 은 족을 "식별성 6검정 + 색대응 격자" 로 정의하고, `tab:color_specificity` 캡션은 파이프라인별 35셀 BH 를 적는다. 초안은 Methods 와 일치하는 족을 표에 적었다 |
| "The exploratory per-hue vulnerability comparisons and the per-pair identification tests, including the blue-hue deficit, are reported one-tailed and uncorrected" | 색별 검정만 표 행으로 | 색별 검정은 Methods `:141`. "per-pair identification tests" 에 해당하는 검정을 원고에서 찾지 못했다(§6) |
| "Individual CVD participants were compared … modified $t$-test, [문단 끊김] with the tail set by the pre-specified direction of each endpoint, …" | 표로 이관 | 방향의 종점별 배정은 부록 고유 내용이며 표가 산문보다 낫다. 문장 중간의 빈 줄(문단 끊김)은 오타 |
| "$d_{cc} = \dots = t\sqrt{(n+1)/n}$, where $n$ is the control sample size" | 유지 | Methods 는 $\sqrt{8/7}$ 만 준다. `tab:exp2_geometry` 는 hV4 에서 $n = 6$ 이므로 일반형이 필요하다 |
| "Mann--Whitney $U$ tests use $r_{\rm rb}$ … group-level effect sizes are Hedges' $g$" | 삭제(표 행으로 흡수) | Methods `:129`, `:256` |
| "Effect sizes for the single-case interpolation comparisons appear in `tab:effect_sizes`, and the geometric-disparity effect sizes … in `tab:disparity_loso`" | 표의 "reported in" 열로 흡수 | |
| LORO 단일사례 결과 3문장 | 나열로 유지 | 본문 Results `:30` 은 "no single-case contrast approached significance" 만 말하고 수치가 없다. 부록 고유 결과 |
| `tab:effect_sizes` | **삭제 제안** | Results `:36`--`:38` 이 표의 8개 통계량($t$, $p$, $d_{cc}$ × 두 참가자, 색별 $d_{cc}$ 셋과 blue $p = 0.051$)을 전부 담는다. 원고 어디에서도 `\cref` 되지 않는다. 캡션의 "Blue lies just above the conventional threshold and is the largest per-hue deviation" 은 결과 문장이다 |

##### 3. 개정 LaTeX 문안

```latex
\suppsection{Statistical analysis and effect sizes}{app:statistics}

\cref{tab:test_directions} lists, for each endpoint, the test, the direction of the alternative hypothesis, the multiple-comparison family, and the location of the values. Single-case effect sizes are the case-control index $d_{cc} = (x_{\rm case} - \bar{x}_{\rm ctrl}) / s_{\rm ctrl} = t\sqrt{(n+1)/n}$, where $n$ is the number of controls entering the test; $n = 7$ throughout except at hV4 in the second session, where $n = 6$ (\cref{tab:exp2_geometry}).

Single-case comparisons of within-participant classification accuracy, in the Procrustes-aligned space of the main text, were as follows.
\begin{itemize}
\item Eight tests (two participants by four regions), two-tailed, all $p \geq 0.189$.
\item $|d_{cc}|$ from $0.25$ to $1.58$; the largest deviation was the deutan participant at V3 ($d_{cc} = -1.58$).
\item At hV4 both participants gave $d_{cc} = -1.08$ ($p = 0.352$).
\end{itemize}

\begin{table}[h]
\centering
\caption{Test and direction of the alternative hypothesis by endpoint. CH, Crawford--Howell modified $t$ against $n$ controls ($df = n - 1$); BH, Benjamini--Hochberg at $\alpha = 0.05$ within the stated family. Uncorrected tests are pre-specified unless marked exploratory.}
\label{tab:test_directions}
\small
\begin{tabular}{p{4.0cm}p{3.6cm}p{2.4cm}p{4.6cm}}
\toprule
Endpoint & Test & Alternative & Correction; reported in \\
\midrule
LORO classification, Session 1 & CH & two-tailed & none; \cref{tab:interp_arms,tab:alignment} \\
LOCO adjacent accuracy at hV4 & CH & one-tailed, lower & none; \S\ref{sec:results:loco}, \cref{tab:interp_arms} \\
Per-hue adjacent accuracy at hV4 & CH & one-tailed, lower & none, exploratory over eight hues; Figure~\ref{fig:loco}C \\
Control interpolation gate & color-label permutation, $N = 1{,}000$ & one-tailed, upper & none; \cref{tab:interp_arms} \\
Procrustes disparity & CH & one-tailed, upper & none; \cref{tab:disparity_loso,tab:motion_arms} \\
Activation metrics & CH & two-tailed & none; \cref{tab:activation} \\
Color-correspondence permutation & label permutation, $N = 1{,}000$ & one-tailed [confirm] & BH over the 35 cells of each pipeline; \cref{tab:color_specificity} \\
Identifiability checks & \cref{app:identifiability} & --- & BH over six tests; \cref{tab:identifiability} \\
Cross-subject transfer & Mann--Whitney $U$, $r_{\rm rb}$ & [confirm] & none; \cref{app:decoders} \\
Group control--CVD contrasts & subject-label permutation, $N = 10{,}000$; Hedges' $g$ & [confirm] & none; \cref{app:triangulation} \\
Second-session interpolation and disparity & CH & one-tailed, toward the control range & none; \cref{tab:exp2_geometry} \\
Second-session identification & Wilson score interval, $n = 64$ & --- & none; \cref{tab:exp2_8afc} \\
\bottomrule
\end{tabular}
\end{table}
```

`tab:effect_sizes` 를 **남기기로 결정할 경우**의 대체 캡션(결과 문장 제거):

```latex
\caption{Single-case hue-interpolation comparisons at hV4: Crawford--Howell $t$ ($df = 6$), one-tailed lower $p$, and $d_{cc} = t\sqrt{8/7}$ against $n = 7$ controls. Per-hue rows are exploratory and uncorrected over eight hues; the two participants share one row at each listed hue because both gave the same adjacent accuracy there.}
```

##### 4. 개정 캡션

- **신설 `tab:test_directions`**: 약어 정의와 보정 규칙만. 결과 없음.
- **`tab:effect_sizes`**: 삭제 제안. 남길 경우 위 대체 캡션("Blue lies just above …" 삭제, "(main text, §…)" 는 표의 성격상 불필요).

##### 5. 문체 점검

- 절차 과거형(`were as follows`, `gave`), 정의 현재형(`are the case-control index`, `lists`).
- 삭제한 중복 4건(§2). 결과는 나열과 표로만 제시.
- 부정 어휘 없음. "none" 은 표 셀의 보정 여부 표기.
- 문단 중간 빈 줄(현행 `modified $t$-test,` 뒤)은 개정문에서 사라진다.

##### 6. 저자 확인 항목

1. **표의 `[confirm]` 셀 3곳**: (a) 색대응 순열의 방향 — `tab:frozen_control` 캡션은 "lower $z$ indicates a better identity correspondence" 라 하므로 단측 하가 유력하나 확정 못 함. (b) 교차피험자 전이 Mann--Whitney ($U = 163.5$, $p = 0.052$)의 방향 — `app:decoders` 가 밝히지 않는다. (c) 집단 순열(10,000)과 Hedges' $g$ 의 방향 — `loo_consistent_results.json` 의 `group_perm_p` 정의 확인 필요.
2. **`p = 0.352` vs `.351`**: S16 의 hV4 LORO $p = 0.352$ 와 `tab:interp_arms` 의 `.351` 이 마지막 자리에서 다르다(`PUBLIC_REPO_PLAN` §10.1 #7 유형). 초안은 원고 값을 유지했다.
3. **FDR 족 정의 교체**: 현행 "RDM hue-pair comparisons, 28 pairs per participant" 족은 원고의 어느 결과에도 대응하지 않는다. 이전 판의 잔재로 보인다. 초안은 Methods `:256` 의 족(식별성 6검정, 색대응 격자 35셀 × 파이프라인)을 따랐다. 실제로 hue-pair FDR 분석이 있다면 표에 행을 추가해야 한다.
4. "per-pair identification tests, including the blue-hue deficit" 에 해당하는 검정을 찾지 못했다. blue 결손은 색별 LOCO 검정(`Figure fig:loco C`, $p = 0.051$)이고 2차 세션 8AFC 는 Wilson 구간만 보고한다. 삭제해도 잃는 정보가 없다고 판단했다.
5. **`tab:effect_sizes` 삭제 여부**. Results `:36`--`:38` 과 완전 중복이고 참조가 없다. 남긴다면 대체 캡션을 쓰고 본문 어딘가에서 `\cref` 해야 한다.
6. LORO 단일사례 8셀 중 원고에 있는 값은 세 개뿐이다($|d_{cc}|$ 범위, V3 deutan, hV4 둘). 8셀 표로 바꾸려면 나머지 5셀을 `docs/PAPER/repro` 경로에서 재산출해야 한다. 초안은 원고 값만 나열했다.
7. 표가 넓다. `p{}` 열 폭은 임시값이며 조판 후 조정 필요. Imaging Neuroscience 템플릿에서 `\small` 로 한 열에 들어가지 않으면 "reported in" 열을 별도 열로 분리하거나 `\resizebox` 를 쓸 것.
8. Methods `:256` 포인터는 그대로 두어도 된다. 표가 $d_{cc}$ 일반형과 방향 배정을 담으므로 포인터가 기대하는 내용과 맞는다.

##### 7. 단어 수

| | 산문 단어 | 문단 수 | 최장 문단 |
|---|---|---|---|
| 개정 전 | 224 | 3 (문장 중간 끊김 포함) | 124 |
| 개정 후 | 124 (목록 항목 포함) | 산문 2 + 목록 3항 | 67 |

---

##### 세 절 합계

| | 산문 단어 | 표 |
|---|---|---|
| 개정 전 | 897 (사용자 집계 906) | 3 (`tab:triangulation`, `tab:variance_explained`, `tab:effect_sizes`) |
| 개정 후 | 592 | 4 (`tab:cv_leakage` 신설, `tab:triangulation`, `tab:variance_explained`, `tab:test_directions` 신설; `tab:effect_sizes` 삭제 제안) |

단어 집계 방법: 표·그림·수식 환경과 `%` 주석을 제거하고, `\suppsection`·`\paragraph` 헤더를 뺀 뒤 빈 줄로 문단을 나눠 세었다. 개정 후의 목록 항목(`\item`)은 각각 한 문단으로 세었다. 사용자 집계와 S7 에서 9단어 차이가 나는 것은 LaTeX 명령 토큰 처리 차이다.

##### 원고 불일치 종합 (수정하지 않고 보고)

| # | 위치 | 내용 |
|---|---|---|
| 1 | S7 `0.545 → 0.578` | sub-10 포함 10명 풀링. 9명 값 0.562 → 0.606 |
| 2 | S7 "uses no stimulus labels" | Methods `:84` 의 회전 정의(색 행 대응 사용)와 불일치 |
| 3 | S9 "without any alignment step" / "native voxel space" | 런 정렬본(`amplitudes_procrustes.npy`) 사용. 교차피험자 정렬이 없다는 뜻으로 한정해야 함 |
| 4 | S9 crossnobis V1 순열 $p = .120$ | n=2 산출물 미커밋 |
| 5 | S9 VE--disparity $r$ | 상관 종류 미명시(Spearman 으로 재현) |
| 6 | Methods `:150` "two distances" | 부록은 세 행 |
| 7 | S16 FDR 족 "RDM hue-pair, 28 pairs" | 원고에 대응 결과 없음; Methods `:256` 과 불일치 |
| 8 | S16 "per-pair identification tests" | 대응 검정 없음 |
| 9 | S16 $p = 0.352$ vs `tab:interp_arms` `.351` | 마지막 자리 불일치 |
| 10 | S16 문단 중간 빈 줄 | 조판 오류 |
| 11 | `tab:effect_sizes` | 참조 0회, Results 와 완전 중복, 캡션에 결과 문장 |
| 12 | S7 "LOSO" | S8·`tab:disparity_loso` 의 "symmetric LOSO"(disparity 추정량)와 같은 약어로 다른 절차를 지칭 |

---

### 9.7 S18 `app:geometry_validity` — 초안

#### S18 압축 개정 초안 — `\suppsection{Validity of the geometric comparison}{app:geometry_validity}`

대상 파일: `/Users/jinilkim/LocalProj/colorBlind_analysis/docs/PAPER/Supplementary/supplementary.tex` 843–893행. **원고는 수정하지 않았다.** 이 파일은 초안뿐이다.

---

##### 1. 본문 포인터와 각 포인터가 이미 서술하는 내용

| # | 위치 | 포인터 문장 | 본문이 이미 말하는 것 | 부록에 기대하는 것 |
|---|---|---|---|---|
| 1 | `Results/results_v4.tex:58` (§results:geometry 끝) | "the validity checks for the geometric comparison appear in Supplementary~\cref{app:geometry_validity}" | disparity 상승, 최대 편차 ROI가 전처리에 따라 이동(protan V1 고정, deutan V2↔V1), 대칭 LOSO에서 protan V1만 p=.045, 지역 귀속은 서술적(results_v4.tex:54) | 검사 자체(동결 투영 대조, 참가자×ROI 색 대응 격자) |
| 2 | `Discussion/discussion_v3.tex:51` | "The regional attribution … and the sign of the protan confusion-axis term vary with preprocessing and with the reduction basis … \cref{app:geometry_validity}" | 전처리·기저 의존성이 있다는 결론 자체 | 기저 의존성의 근거(SRM 기저 vs PCA 기저 최적 이동), 전처리 의존성의 근거(두 파이프라인 격자) |
| 3 | `Supplementary/supplementary.tex:403` (§app:loo_disparity 말미) | "the color-correspondence permutation of \cref{app:geometry_validity} asks whether the identity mapping … outperforms a shuffled mapping" | **disparity 와 색 대응 순열의 개념 구분 전체**(회전 불변 거리 vs 항등 대응 검정; 멀면서 항등이 최적일 수도, 가까우면서 이동 대응이 나을 수도) | 순열의 절차와 결과 |
| 4 | `Supplementary/supplementary.tex:416` (§app:triangulation 끝) | "Whether the deviation is specific to color is treated in \cref{app:geometry_validity}" | 정렬 독립 검사 3종이 측정만을 다룬다는 것 | 참가자별 색 특이성 결과 |
| 5 | `Methods/methods_v4.tex:256` (§methods:stats) | BH 보정을 "the participant-by-region grids of the supplementary color-correspondence analysis" 에 적용 | BH α=.05, 격자 단위 보정 | 격자 표 + 보정 결과 |
| 6 | `Methods:135,138`, `Results:38` | LOCO 의 색 라벨 순열 귀무(참가자 내 1,000회) 정의 | 본문 순열 귀무의 정의와 용도 | (부록 첫 문단이 "differs from the color-label permutation null of the main text" 로 재설명 → 불요) |

`Supplementary/archive/S18_geometry_validity.tex` 는 구판(모션 회귀 arm, `HC` 표기)이며 현재 본문 포인터가 가리키지 않는다.

---

##### 2. 삭제 근거

현행 5문단(572단어)에서 걷어낸 문장과 그 이유. 행 번호는 `supplementary.tex` 기준.

| 현행 문장 (845·868·891·892·893행) | 처리 | 근거 |
|---|---|---|
| ¶1 "The permutation asks whether a participant's colors map onto the control geometry in the identity order, which differs from the color-label permutation null of the main text, where the question is whether the control group interpolates above chance in a region." | 삭제 → `\cref{app:loo_disparity}` 참조 한 절로 대체 | 403행이 항등 대응 vs 셔플 대응을 이미 정의; 본문 순열 귀무는 Methods 135·138행에 정의 |
| ¶1 "Re-estimation detected 0 of 7 at V1, V2 and V3 and 0 of 6 at hV4, with mean permutation $z$ near zero in every ROI, whereas freezing the projection recovered detection, reaching 5 of 7 at V3 and 2 to 3 of 7 elsewhere" | 삭제 | `tab:frozen_control` 의 detected·mean $z$ 열을 그대로 읽은 것 |
| ¶2 "The deutan participant reached $p = .002$ at V2, the lowest V2 value among the nine participants, and $p = .024$ at V3. The protan participant reached $p = .001$ at V3 and $p = .013$ at V2, while V1 returned $p = .758$." | 삭제(protan V1 .758 만 이동 분석의 전제로 한 절 유지) | 다섯 값 모두 `tab:color_specificity` 셀; "lowest V2 value" 는 열을 읽으면 나옴 |
| ¶2 "V3 showed color specificity most broadly, with 5 of its 9 cells surviving." | 삭제 | 표에 BH 생존 셀을 굵게 표시하면 열에서 바로 셈 |
| ¶3 "The deutan V2 cell remained at its nominal value across the two pipelines ($p = .002$ and $p = .003$) while its corrected value moved from $q = .018$ to $q = .053$" | 삭제 | 두 $p$ 는 표 셀; 셀 단위 서술은 정책상 주장 근거가 아니므로 산문에 둘 이유 없음 |
| ¶4 "which is computed under the same minimum-over-eight rule and is therefore subject to the same selection bias" | 캡션(방법)으로 이동 | 대조군 이득 분포의 계산 규칙 = 방법 |
| ¶4 수치 전체 (1.037→0.788, 24.0%, 3.5±5.9%, t=3.22, p=.009, d_cc=3.44, 0.839±0.087, ρ 0.00→+0.52, 0.45, z=+5.02, p=.002, p_adj=.032) | 새 표 `tab:cyclic_shift` 로 이동 | 결과는 표로 제시 |
| ¶5 "Under the SRM basis a $225^\circ$ shift ($+0.50$) is close to the $315^\circ$ optimum ($+0.52$). Under the PCA basis the optimum falls at $135^\circ$ ($p = .048$…)" | 같은 표의 기저 블록으로 이동 | Discussion:51 이 기대하는 기저 의존성 근거이므로 유지하되 표로 |
| ¶4 "Disparity at this region is nonetheless elevated in both pipelines, so the departure is not accounted for by a rigid relabeling alone." | 한 절로 압축 유지 | 이동 결과의 과대해석을 막는 범위 한정 — 필요한 해석. "elevated in both pipelines" 는 Results:54 가 이미 보고하므로 참조만 |
| ¶4 "The account applies to the primary pipeline, since that cell is no longer null under head-motion correction." | 압축 유지 | 적용 범위 한정 — 필요 |
| ¶3 "Individual cells of this grid are descriptive and support no claim in the main text." | 유지 | 정책 문장 |

**추가한 것 (본문·현행 부록 어디에도 없음)**: 동결 설계의 절차 한 문단(7 참가자 fold × 6 run fold, SRM·참조·투영을 어디서 적합하고 무엇을 순열하는지). 현행 판은 "frozen"이 무엇인지 정의하지 않은 채 결과만 적고 있다. 출처 = `analysis/validation/scripts/disparity_frozen_permutation.py` 15–40, 160–185행.

---

##### 3. 개정 LaTeX 문안 전문

```latex
% --------------------------------------------------------------------------
% ==== S17  (was Supplementary/S18_geometry_validity.tex) ====
% --------------------------------------------------------------------------
% Supplementary — Validity of the geometric comparison
% Compressed 2026-09-06. Procedure: analysis/validation/scripts/disparity_frozen_permutation.py
% Raw outputs: analysis/future_phase1_sensitivity/results/{with_residuals,hmc_v2}/color_correspondence/frozen_permutation.json,
%   analysis/validation/results/cyclic_shift_disparity.json (primary pipeline only)
% Counts and BH-FDR recomputed from the JSON on 2026-09-06:
%   primary 35 cells, 16 raw p<.05, 7 surviving BH; head-motion-corrected 15 raw / 0 BH.
% The cyclic-shift gain is referred to the control gain distribution, which is computed
%   under the same minimum-over-eight rule and therefore absorbs the same selection
%   bias. hV4 shift gains are omitted: the ROI carries no geometric endpoint.

\suppsection{Validity of the geometric comparison}{app:geometry_validity}

The color-correspondence permutation asks whether the identity mapping between a participant's eight colors and the control reference outperforms a shuffled mapping (\cref{app:loo_disparity}). It was computed under a leave-one-run-out design that holds the shared projection fixed. On each of the $7 \times 6$ participant-by-run folds, the shared response model was fitted to the six training controls' five-run mean patterns, the reference was their held-out run in the shared space, and the target participant's projection was fitted to its own five training runs and applied unchanged to its held-out run. Procrustes disparity between the projected held-out run and the reference was then compared with the distribution obtained by permuting the eight color labels of that run $1{,}000$ times; $z$ and $p_{\rm perm}$ are computed after averaging over folds, and each CVD participant contributes the mean over the seven participant folds. A projection re-estimated on the held-out run, the procedure of the main analyses, absorbs the permutation, because the singular-value fit selects a subspace matched to whichever label order it receives. \cref{tab:frozen_control} gives both variants on the controls, in whom color structure is established; every result below uses the frozen projection.

\begin{table}[h]
\centering
\caption{Color-correspondence permutation on the controls, used as a positive control for the two projection variants. Entries give the number of controls with $p_{\rm perm} < .05$ and the mean permutation $z$ under a projection re-estimated on the held-out run and under a projection fitted to the training runs and frozen. $z$ is the observed disparity minus the permutation-null mean in null SD units, so negative values indicate a better identity correspondence than the shuffled null. Control 7 is omitted at hV4 (ROI below the voxel minimum of the shared-space analyses).}
\label{tab:frozen_control}
\begin{tabular}{lccccc}
\toprule
 & & \multicolumn{2}{c}{Re-estimated} & \multicolumn{2}{c}{Frozen} \\
\cmidrule(lr){3-4}\cmidrule(lr){5-6}
ROI & $n$ & detected & mean $z$ & detected & mean $z$ \\
\midrule
V1  & 7 & 0 & $-0.04$ & 2 & $-1.58$ \\
V2  & 7 & 0 & $-0.04$ & 3 & $-1.00$ \\
V3  & 7 & 0 & $-0.78$ & 5 & $-2.39$ \\
hV4 & 6 & 0 & $+0.06$ & 2 & $-1.07$ \\
\bottomrule
\end{tabular}
\end{table}

\cref{tab:color_specificity} gives the full participant-by-region grid in both preprocessing pipelines. In the primary pipeline 16 of the 35 cells fell below $.05$, against a chance expectation of $1.8$, and 7 survived Benjamini--Hochberg correction over the 35 cells, among them the deutan V2 cell ($q = .018$) and the protan V3 cell ($q = .012$). Under head-motion correction 15 cells fell below $.05$ and none survived correction. The protan V1 cell was null in the primary pipeline ($p = .758$) and not under head-motion correction ($p = .010$). Individual cells of this grid are descriptive and support no claim in the main text.

\begin{table}[h]
\centering
\caption{Color-correspondence permutation under the frozen projection, one cell per participant and region, in the primary and head-motion-corrected pipelines. Entries give $p_{\rm perm}$ against $N = 1{,}000$ label permutations of the held-out run, with the test direction observed disparity below the null. Bold: $q < 0.05$ after Benjamini--Hochberg correction over the 35 cells of the same pipeline. Control 7 is omitted at hV4 (ROI below the voxel minimum of the shared-space analyses).}
\label{tab:color_specificity}
\begin{tabular}{lcccccccc}
\toprule
 & \multicolumn{4}{c}{Primary} & \multicolumn{4}{c}{Head-motion correction} \\
\cmidrule(lr){2-5}\cmidrule(lr){6-9}
Participant & V1 & V2 & V3 & hV4 & V1 & V2 & V3 & hV4 \\
\midrule
Control 1 & $0.088$ & $0.020$ & $0.062$ & $0.393$ & $0.012$ & $0.072$ & $0.018$ & $0.290$ \\
Control 2 & $\mathbf{0.001}$ & $0.016$ & $\mathbf{0.004}$ & $0.136$ & $0.437$ & $0.420$ & $0.191$ & $0.019$ \\
Control 3 & $0.109$ & $0.520$ & $0.255$ & $0.272$ & $0.325$ & $0.113$ & $0.176$ & $0.101$ \\
Control 4 & $0.152$ & $0.014$ & $\mathbf{0.001}$ & $0.041$ & $0.420$ & $0.006$ & $0.015$ & $0.173$ \\
Control 5 & $0.057$ & $0.773$ & $0.034$ & $0.031$ & $0.079$ & $0.194$ & $0.032$ & $0.038$ \\
Control 6 & $0.407$ & $0.290$ & $\mathbf{0.009}$ & $0.220$ & $0.373$ & $0.117$ & $0.010$ & $0.012$ \\
Control 7 & $0.034$ & $0.159$ & $\mathbf{0.004}$ & --- & $0.008$ & $0.005$ & $0.391$ & --- \\
\textbf{Deutan} & $0.105$ & $\mathbf{0.002}$ & $0.024$ & $0.273$ & $0.022$ & $0.003$ & $0.047$ & $0.257$ \\
\textbf{Protan} & $0.758$ & $0.013$ & $\mathbf{0.001}$ & $0.129$ & $0.010$ & $0.148$ & $0.053$ & $0.815$ \\
\bottomrule
\end{tabular}
\end{table}

Because the protan V1 identity correspondence was null in the primary pipeline while its disparity was elevated (Section~\ref{sec:results:geometry}), we evaluated the eight cyclic shifts of that participant's color labels under the same frozen design and referred the gain of the best shift to the seven controls' gains (\cref{tab:cyclic_shift}). The V1 correspondence is displaced by one hue step. That participant's V1 split-half pattern reliability reaches $.847$, above the highest control value, and eight-way classification there reaches $0.79$ against a chance level of $0.125$. % AUTHOR CHECK: neither value traces to a committed artifact; see draft_S18.md §6
The deutan participant's optimal shift was the identity at V1, V2 and V3. The rotation does not account for the elevation itself, which holds in both pipelines, and the shift analysis applies to the primary pipeline alone, since the cell is not null under head-motion correction. The optimal shift depends on the reduction basis (\cref{tab:cyclic_shift}, last three rows), and which rearrangement restores control-level similarity remains open.

\begin{table}[h]
\centering
\caption{Cyclic-shift analysis of the protan V1 correspondence under the frozen projection, primary pipeline. The eight cyclic shifts of the color labels were evaluated, and the gain is the proportional reduction of Procrustes disparity from the identity to the best shift. Control gains are computed under the same minimum-over-eight rule and therefore carry the same selection bias; the control reference is mean $\pm$ SD over $n = 7$. The single-case test is the Crawford--Howell one-tailed $t$ ($df = 6$) with $d_{cc} = t\sqrt{8/7}$, upper-tailed for the gain. Second-order RSA similarity is the Spearman $\rho$ between the participant's RDM and the control-mean RDM; its $z$ and $p$ are referred to a selection-bias null of the same minimum-over-eight rule, and $p_{\rm adj}$ is Benjamini--Hochberg corrected. The basis rows give the optimal shift under the SRM and PCA reductions.}
\label{tab:cyclic_shift}
\begin{tabular}{llccl}
\toprule
Quantity & Condition & Protan & Controls & Test \\
\midrule
Procrustes disparity & identity & $1.037$ & $0.839 \pm 0.087$ & \\
 & $45^\circ$ shift & $0.788$ & & \\
Gain, best shift & & $24.0\%$ & $3.5 \pm 5.9\%$ & $t = 3.22$, $p = .009$, $d_{cc} = 3.44$ \\
\midrule
RSA $\rho$ & identity & $\approx 0.00$ & $0.45$ & \\
 & best shift, SRM basis ($315^\circ$) & $+0.52$ & & $z = +5.02$, $p = .002$, $p_{\rm adj} = .032$ \\
 & $225^\circ$, SRM basis & $+0.50$ & & \\
Optimal shift & PCA basis & $135^\circ$ & & $p = .048$, uncorrected \\
\bottomrule
\end{tabular}
\end{table}
```

---

##### 4. 개정 캡션 둘 (표 3 참조; 여기 재수록)

**`tab:frozen_control`**

> Color-correspondence permutation on the controls, used as a positive control for the two projection variants. Entries give the number of controls with $p_{\rm perm} < .05$ and the mean permutation $z$ under a projection re-estimated on the held-out run and under a projection fitted to the training runs and frozen. $z$ is the observed disparity minus the permutation-null mean in null SD units, so negative values indicate a better identity correspondence than the shuffled null. Control 7 is omitted at hV4 (ROI below the voxel minimum of the shared-space analyses).

변경점: "detected" 의 정의($p_{\rm perm} < .05$)와 $z$ 의 정의를 캡션에 넣었고(현행 산문이 담고 있던 기호 설명), hV4 $n=6$ 의 이유를 명시. 결과 문장 없음.

**`tab:color_specificity`**

> Color-correspondence permutation under the frozen projection, one cell per participant and region, in the primary and head-motion-corrected pipelines. Entries give $p_{\rm perm}$ against $N = 1{,}000$ label permutations of the held-out run, with the test direction observed disparity below the null. Bold: $q < 0.05$ after Benjamini--Hochberg correction over the 35 cells of the same pipeline. Control 7 is omitted at hV4 (ROI below the voxel minimum of the shared-space analyses).

변경점: 현행 캡션의 결과 문장("Seven cells survive … none survive it in the head-motion-corrected pipeline") 삭제 → 굵게 표시 규칙으로 대체. 검정 방향 추가. 굵게 표시한 7셀은 JSON 에서 BH 재계산한 것과 일치(Control 2 V1·V3, Control 4 V3, Control 6 V3, Control 7 V3, Deutan V2, Protan V3).

(세 번째 표 `tab:cyclic_shift` 는 신설이며 캡션은 §3 에 있다.)

---

##### 5. 문체 점검 결과

- **시제**: 절차는 과거형("was computed", "was fitted", "we evaluated", "fell below", "survived"), 모형 성질은 현재형("absorbs the permutation", "selects a subspace", "is displaced by one hue step", "depends on the reduction basis"). Methods §methods:srm("SRM was trained … Each CVD participant was subsequently projected")·Results §results:geometry("rose", "remained", "reached") 와 일치.
- **구어체**: 없음. "sat below", "showed", "failure is not one of signal" 은 제거.
- **부정 어휘**: "fail/failure", "has power only when" 제거. "null" 은 검정 결과의 기술어로만 사용.
- **과대주장**: "Both CVD participants showed color-specific geometry" (¶2 첫 문장) 삭제 — 셀 단위 결과를 참가자 단위 주장으로 격상하는 문장이었고, 정책("개별 셀을 근거로 국재 주장 금지")과 충돌. "The evidence supports the existence of a color rearrangement" 계열 문장은 현행 판에 이미 없음. 남긴 해석 문장은 셋뿐: (i) 재적합 투영이 순열을 흡수하는 기전(이 절의 핵심, 보존), (ii) 이동이 상승 자체를 설명하지 않는다는 범위 한정, (iii) 이동 분석은 primary 파이프라인에만 적용된다는 범위 한정.
- **정책 준수**: "Individual cells of this grid are descriptive and support no claim in the main text" 유지. 색 특이성을 선택 기준으로 쓰는 문장 없음. 국재 서술 없음(deutan V2 "lowest among nine" 삭제).
- **캡션 규칙**: 세 캡션 모두 측정 대상·방법·기호·검정 방향만 담음.
- **용어 일치**: "color-correspondence permutation"(Methods:256, Supp:403 과 동일), "frozen projection"/"re-estimated"(tab:frozen_control 열 이름과 동일), "$d_{cc} = t\sqrt{8/7}$"(tab:disparity_loso 캡션과 동일 표기), "head-motion correction"(Results·tab:motion_arms 와 동일).
- **`academic-humanizer` 적용 여부**: 이 문안은 논문 갈래이므로 일반 humanizer 를 적용하지 않았다. §27 표층 다듬기는 저자 확인 항목(§6) 해소 후 `/revise-draft` 순환에서 돌리는 것이 순서다.

---

##### 6. 저자 확인이 필요한 항목

수치는 바꾸지 않았다. 아래는 확인·결정만 요청하는 항목이다.

1. **Split-half 신뢰도 $.847$ 와 8-way 분류 $0.79$ (protan V1) — 커밋 산출물 없음.**
   - `analysis/validation/results/within_hc_reliability.json` 의 sub-09 V1 split-half 는 voxel 공간 Pearson $0.50$(Spearman–Brown $0.67$), PCA6 $0.62$ 로 $.847$ 이 아니다. $.847$ 은 `RESULTS_GEOMETRY_VALIDITY_2026-08-05.md` §3 표(SRM 공간 추정)에만 있고 JSON 이 없다.
   - $0.79$ 는 원고 자체의 표와 맞지 않는다: `tab:alignment` protan V1 LORO = $0.562$(Procrustes), `tab:loro_decoders` hue-channel basis = $0.625$, LDA = $0.854$. `tab:exp2_loro` 의 NF protan V1 셀이 우연히 $0.79$ 이나 2차 세션 값이다.
   - `PUBLIC_REPO_PLAN_2026-09-05.md` §10.1 항목 8 이 이미 두 값 모두를 "커밋 산출물 없는 값"으로 표시.
   - **결정 요청**: 문장을 삭제하거나, 원고의 `tab:alignment`/`tab:loro_decoders` 값으로 교체하거나, 서버 산출물을 회수해 커밋. 초안에는 `% AUTHOR CHECK` 주석을 달아 원문 그대로 두었다.
2. **2차 RSA 순환 이동 결과 ($\rho \approx 0.00 \to +0.52$, 대조군 $0.45$, $z = +5.02$, $p = .002$, $p_{\rm adj} = .032$; SRM 기저 $225^\circ$ $+0.50$ / $315^\circ$ $+0.52$; PCA 기저 $135^\circ$ $p = .048$) — 커밋 산출물 없음.** `analysis/validation/results/` 와 `future_phase1_sensitivity/results/` 어디에도 없고, cyclic-shift 스크립트도 `analysis/validation/scripts/` 에 없다. 같은 PUBLIC_REPO_PLAN 항목 8. 초안 표 `tab:cyclic_shift` 의 캡션에서 RSA 의 정의("Spearman ρ between the participant's RDM and the control-mean RDM"; 선택 편향 귀무; BH 보정)를 **현행 산문의 서술에서 추론**해 적었으므로 스크립트로 확인 필요.
3. **$45^\circ$ 와 $315^\circ$ 의 부호 관례.** 현행 산문은 disparity 최적 이동을 "$45^\circ$ / one hue step" 이라 하고 "the same rotation" 이 RSA 를 $+0.52$ 로 올렸다고 한 뒤, SRM 기저 RSA 최적을 $315^\circ$ 라 적는다. 라벨을 한 칸 밀면 기하는 반대 방향으로 $45^\circ$ 돌므로 두 값이 같은 회전일 수 있으나, 원고가 관례를 밝히지 않는다. 초안 표는 "best shift, SRM basis ($315^\circ$)" 로 적어 등치를 단언하지 않았다. 등치 여부와 표기 관례 확인 요청.
4. **Control 7 hV4 결측 사유.** JSON 메타의 `min_voxels = 20` 을 근거로 "ROI below the voxel minimum of the shared-space analyses" 로 적었다. 원고 Methods·`app:roi_coverage` 어디에도 20-voxel 최소 기준이 명시돼 있지 않으므로, (a) Methods 에 기준을 추가하거나 (b) 캡션 문구를 원고에 있는 표현으로 바꾸어야 한다.
5. **Deutan V2 의 HMC 파이프라인 $q$.** 현행 산문 $q = .053$; JSON 의 미반올림 $p$ ($3/1001$, $12/1001$)로 BH 를 재계산하면 $.0525 \to .052$. 반올림 경로 차이(반올림된 $p = .012$ 로 계산하면 $.0525 \to .053$). 초안은 이 값을 산문에서 삭제했으므로 문제가 사라지지만, 다른 곳에서 인용한다면 통일 필요.
6. **주석 헤더 838행 stale.** "motion-regressed 18 raw / 15 BH" 는 폐기된 motreg arm 의 값이고 현재 표·산문은 hmc_v2 arm(15 raw / 0 BH)이다. 초안 헤더에서 정정했다. 831행의 "Governing document: docs/PAPER/REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md" 는 파일이 존재하지 않아 초안 헤더에서 뺐다.
7. **표 3 셀 값 검증 결과 (변경 없음)**: 두 파이프라인 35셀 × 2 의 $p_{\rm perm}$, `tab:frozen_control` 의 detected·mean $z$ 8쌍, 순환 이동의 $1.037$/$0.788$/$24.0\%$/$3.5 \pm 5.9\%$/$t = 3.22$/$p = .009$/$d_{cc} = 3.44$/$0.839 \pm 0.087$, deutan V1–V3 항등 최적 — 모두 커밋된 JSON 에서 그대로 재현됨. BH 생존 7셀도 일치.
8. **`tab:cyclic_shift` 의 hV4 미포함**: 헤더 주석 관행("hV4 carries no geometric endpoint")을 따랐다. JSON 상 protan·deutan hV4 최적 이동은 $225^\circ$($+6.8\%$, $+2.1\%$)이며 초안에 넣지 않았다.

---

##### 7. 개정 전후 단어 수와 최장 문단 길이

산문만 계산(표 환경·`\suppsection`·LaTeX 주석 제외).

| | 단어 | 문단 수 | 최장 문단 | 표 |
|---|---|---|---|---|
| 현행 | 572 | 5 | 215 | 2 |
| 개정 | 438 | 3 | 188 (¶1 방법) | 3 |

문단별: ¶1 방법 188, ¶2 격자 결과 102, ¶3 순환 이동 148. ¶1 이 긴 이유는 동결 설계의 절차 서술(fold 구조·적합 위치·순열 대상)을 새로 넣었기 때문이며, 이 내용은 본문·현행 부록 어디에도 없다. ¶3 의 148단어 중 25단어는 §6-1 의 `AUTHOR CHECK` 문장이다. 그 문장을 삭제하면 개정판은 413단어, 최장 문단 188단어(방법 문단)가 된다. 절차 문단을 더 줄이려면 "A projection re-estimated … label order it receives" 한 문장(핵심 기전)을 남기고 fold 구조 서술을 스크립트 참조로 대체할 수 있으나, 재현에 필요한 정보이므로 초안에서는 유지했다.

---

### 9.8 이미 `.tex` 에 반영된 절 (2026-09-06)

아래 넷은 검토가 끝나 이미 적용했다. 문안은 현행 `supplementary.tex` 가 정본이다.

| 절 | 조치 | 분량 |
|---|---|---|
| **S4** `app:dimensionality` | 선택 규칙을 실제 규칙으로 정정하고 $4\times5$ 지표 표 `tab:kselect` 신설 | 133 → 136 (+표) |
| **S5** `app:decoders` | LORO·LOCO 결과 양상과 hue-channel 채택 사유만 유지, 해석 문장 삭제 | 424 → 301, 최장 170 → 89 |
| **S8** `app:loo_disparity` | §2.9 와 겹치는 서술 삭제, 고유 내용만 유지 | 364 → 208, 최장 160 → 82 |
| **S10** `app:activation` | $4\times2\times2$ 단일사례 표 `tab:activation` 신설, 해석 문장 삭제 | 239 → 171 (+표) |

**S4 에서 정정한 것 (본문 §2.6 동시 수정)**

`aggregate_k_selection.py` 를 커밋된 fold 결과에 돌린 결과, 원고가 기술하던 3지표 composite 는 배포된 $k$ 를 만들지 않는다.

| ROI | RDM split-half 단독 | composite (3지표) | 배포값 |
|---|---|---|---|
| V1 | 4 | 4 | 4 |
| V2 | 4 | **5** | 4 |
| V3 | 3 | **4** | 3 |
| hV4 | 3 | **6** | 3 |

reconstruction error 는 $k$ 에 단조라 모든 fold 에서 순위 SD $0$ 으로 $k=6$ 을 1위에 놓는다. 배포값은 RDM split-half 단독과 4/4 일치한다. 서술을 실제 규칙으로 고치고, composite 가 더 큰 $k$ 를 고른다는 사실은 민감도 서술로 남겼다.

---

### 9.9 미해결 항목 대장

**A. 검증 완료 — 원고 수정 필요**

| # | 위치 | 내용 | 근거 |
|---|---|---|---|
| A1 | `results_v4.tex:94`, S11 두 곳 | R+C 가 `S-cone 변위를 표현할 수 없다` | `rc_scone_projection.json`: deutan $\lvert\beta_s/\beta_c\rvert = 0.94$ |
| A2 | `supplementary.tex` S11 | $\Delta$RDM 직접 적합이 같은 경계 행동 | 채택 앵커에서 경계 도달률 deutan $0.000$, protan $0.117$ |
| A3 | `results_v4.tex:94` | `saturated … in both participants` | protan $41\%$ 는 Gate 2 문턱 $50\%$ 아래이며 게이트를 통과했다 |
| A4 | `supplementary.tex:347` | `rotation that uses no stimulus labels` | §2.5 의 $8\times8$ hue 회전과 모순 |
| A5 | `supplementary.tex:347` | $0.545$ 의 영역 미표기 | V2 값이다 |
| A6 | S13 | `$0.09$ → $0.72$` | $0.72 = 0.283 + 0.437$ 로 합집합이 아니라 합계다. 기준값 $0.09$ 는 단일 축 |
| A7 | S12 | `spatial PCA(20) on SRM-projected amplitudes` | rank 20 은 잔차 공분산 PC 이고 입력은 복셀 공간 진폭 |
| A8 | S16 | BH 족으로 `RDM hue-pair comparisons, 28 pairs` 를 지목 | 그런 결과가 원고에 없다. §2.15 의 족은 식별 검사 6 + 색 대응 35 셀 |
| A9 | `tab:effect_sizes` (S16) | `\cref` 0회, 값은 `results_v4.tex:36-38` 과 중복, 캡션에 결과 문장 | 삭제 후보 |
| A10 | S9 | crossnobis 가 `no alignment step` | `amplitudes_procrustes.npy` 는 런 정렬을 거친다. 정확한 진술은 **참가자 간 정렬 없음** |

**B. 산출물 확인 필요**

| # | 위치 | 내용 |
|---|---|---|
| B1 | `supplementary.tex:892` | protan V1 8분류 $0.79$ — 원고 표는 $0.562$(Procrustes) / $0.625$(SRM hue-channel) / $0.854$(LDA) / $0.771$(SVM) |
| B2 | `supplementary.tex:892` | split-half $.847$ 의 커밋 산출물 |
| B3 | S12 | Table S11 Test 1 행의 집계 단위 혼합 — $f_{10^\circ}$ 는 평균, bias 는 중앙값 |
| B4 | S13 | 통제 앵커 $30.5$–$58.1$, $49.1$, $23.4$–$55.5$, $35.7$ 의 1차 출처 |
| B5 | S18 | 순환 이동 RSA ($\rho +0.52$, $z +5.02$) 산출물 |
| B6 | S14 | hV4 $n=4$ 통제 평균 $0.45$ 대 `tab:exp2_geometry` 의 $0.46$ |
| B7 | S11 | Boehm(2014)·Tregillus(2021)가 보고한 보상 범위 — 과보상 논거의 문헌 근거 |
| B8 | S9 | crossnobis V1 순열 $p = .120$ 의 $n=2$ 산출물 |

**C. 원고 밖 정리 대상**

| # | 내용 |
|---|---|
| C1 | `results_v4.tex:83-84` 에 `sec:results:twocomp` 와 `sec:results:rc_insufficient` 두 라벨이 한 소절에 붙어 있다. 후자를 따라간 독자가 R+C 전용 절을 기대하고 2성분 절에 도착한다 |
| C2 | `Methods §2.10` 의 `retinal-plus-gain` 을 `retinal-plus-cortical` 로 통일 (약어 R+C 와 맞춤) |
| C3 | `supplementary.tex` 838행 주석의 `18 raw / 15 BH` 는 폐기된 `motreg` arm 값이며, 참조하는 `REVISION_PLAN` 파일이 존재하지 않는다 |
| C4 | `bibliography.bib` 미인용 항목 28개, 고아 `Methods/bibliography.bib` 27개, 중복 `brouwer2013additional` |
| C5 | `main.tex:183` 의 Zenodo DOI `\todo` — 제출 전 저장소 공개와 DOI 발급 필요 |

---

### 9.10 `rather than` 대비 구문 점검 (2026-09-06, 저자 지시)

**기준** — 진행한 절차가 통상적 파이프라인이 아니어서 **정당화가 필요한 경우**, 또는 대비 자체가 **결과의 내용**인 경우에만 남긴다. 표준적인 선택을 아무도 가정하지 않는 대안에 맞세워 방어하는 서술은 지운다.

원고 다섯 파일에서 42회 나타난다. 아래 넷을 지우고 나머지는 위 기준으로 유지한다.

#### 지우는 것

| 위치 | 현재 | 개정 | 사유 |
|---|---|---|---|
| `methods_v2.tex:47` | All analyses below use a single amplitude per hue and run **rather than individual trials**, so the varying counts do not enter them. | All analyses below use a single amplitude per hue and run, so the varying counts do not enter them. | run 단위 GLM 진폭은 표준 단위다. 시행 단위를 가정할 독자가 없으므로 방어가 불필요하다 |
| `results_v4.tex:106` | the SRM reduction places the optimum at $(32^\circ, 0^\circ)$ **rather than at the PCA solution** | the SRM reduction places the optimum at $(32^\circ, 0^\circ)$ | PCA 해 $(2^\circ, +24^\circ)$ 는 같은 문단과 표에 이미 있다. 대비가 정보를 더하지 않는다 |
| `supplementary.tex:652` | which places the individualized filter's value below that baseline **rather than above it** | which places the individualized filter's value below that baseline | `raises … from $0.25$ to $0.33$` 가 이미 방향을 말한다. 덧붙은 대비는 개인화 필터의 상대 위치를 강조하는 서술이 되어, 효능 우위를 주장하지 않는다는 원칙과도 맞지 않는다 |
| S11 문안 (§9.1c) | $\Delta\lambda$ was held fixed **rather than fitted**, and each participant was evaluated at three cone-shift anchors | $\Delta\lambda$ was fixed, and each participant was evaluated at three cone-shift anchors | 뒤따르는 절이 앵커 세 값을 열거하므로 적합하지 않았다는 사실이 드러난다 |

#### 유지하는 것과 그 근거

**절차가 비표준이어서 정당화가 필요한 경우 (7)**

| 위치 | 구문 |
|---|---|
| `methods_v2.tex:47` | optimized for detection power **rather than for equal counts** |
| `methods_v2.tex:71` | a custom pipeline **rather than a standard container** |
| `methods_v2.tex:138` | against an empirical null of 1,000 permutations **rather than against the analytic chance level** |
| `methods_v2.tex:237` | repeats the grid search **rather than the full selection procedure** |
| `supplementary.tex:161` | Dice … respond to the extent of overlap **rather than to the position of a partial slab** |
| `supplementary.tex:497` | Stockman and Sharpe fundamentals **rather than** Smith and Pokorny, for which it is defined |
| `supplementary.tex:644` | compared against the shipping product **rather than a re-implemented retinal-simulation transform** |

**대비가 곧 결과의 내용인 경우 (9)**

`introduction_v2.tex:102` (redistributed / improving), `:102` (average cone sensitivities / the user's own), `:107` (redistribute / remove), `:114` (strength / geometry), `:116` (judgments / cortical response), `results_v4.tex:36` (interpolation-specific / general signal loss), `:79` (axis-specific / general sensitivity loss), `:104` (precision / direction), `supplementary.tex:21` (specific axes / overall sensitivity).

**주장의 범위를 제한하는 경우 (10)** — 삭제하면 과대주장이 된다

`introduction_v2.tex:121` (feasibility / superiority), `methods_v2.tex:183` (assumption / biologically grounded mechanism), `results_v4.tex:92` (descriptive embeddings / physiological point estimates), `:92` (bounded / estimated), `discussion_v3.tex:39` ×3, `:49` (Ishihara / anomaloscopy), `:51` (standard observer / each participant), `supplementary.tex:347` (bounds the leakage question / isolating the nesting), `:601` (descriptive anchor / a test of specificity), `:650` (movement toward the reference / adjudication between model classes).

**기술적 구별에 필요한 경우 (8)**

`methods_v2.tex:36` (anomalous trichromacy / dichromacy), `:135` (specificity to hue identity / overall decodability), `:150` (property of the data / of the alignment procedure), `supplementary.tex:25` (lower bound / estimate), `:158` (distorts a pattern / translates it), `:246` (interpolation behavior / classification accuracy), `:250` (vary the readout / the decoder), `:604` (bear on the magnitude / on the sign), `:748` (encoding fit / decoding accuracy).

#### 판단 근거 요약

42회 중 4회만 지운다. 나머지가 남는 이유는 이 원고의 대비 구문 대부분이 **방어가 아니라 (i) 결과 진술, (ii) 주장 범위의 제한, (iii) 두 양의 구별** 세 갈래이기 때문이다. 특히 (ii)는 프로젝트 정책(효능 우위 비주장, 서술적 임베딩)이 요구하는 헤지이므로 지우면 과대주장이 된다.


#### 9.10 보유 — Stockman 기저 문장 개정 (저자 지시)

`evaluated here on the Stockman and Sharpe cone fundamentals … rather than on the Smith and Pokorny fundamentals for which it is defined` 는 §9.10 에서 `유지` 로 분류했으나, 문장이 **편차를 공개하면서 이유를 대지 않아** 질문에 답하는 대신 질문을 부르는 상태였다. `개정` 으로 옮긴다.

실제 이유는 `rc_1dof.py`, `machado_simulator.py`, `two_comp.py` 가 모두 Stockman 기저를 쓴다는 것이다. 즉 **2성분 모형과 R+C 모형을 같은 원뿔 공간에서 계산하기 위해서**이며, 그것이 두 모형 부류를 비교 가능하게 만드는 조건이다. 그 전제가 현재 원고 어디에도 없다.

두 절로 나누어 대비 구문이 사라지고, 편차는 그대로 공개되며, R+C 비교의 전제가 명시된다. 같은 문단의 `$\Delta\lambda$ was held fixed rather than fitted` 도 `was fixed` 로 줄였다.

---

### 9.11 R+C 보상 문헌 근거 확인 (2026-09-06) — 과대주장 정정

`Boehm_compensation_JV(2014).pdf` 와 `Tregillus(2021)_compenstaion.pdf` 를 전문 확인한 결과, §9.1d 에서 넣은 다음 문장이 성립하지 않는다.

> so these estimates fall outside the range of partial compensation reported for anomalous trichromats \parencite{boehm2014,tregillus2021}

**성립하지 않는 이유 셋**

1. **측정량이 다르다.** Boehm 의 sensitivity ratio·color-difference ratio 와 Tregillus 의 대비 배율 $s_c$ 는 모두 **L--M 축의 진폭 배율**이다. 원고의 $g$ 는 **hue 각도 변위의 배율**이고 $g > 2$ 는 각도 변위의 부호 반전을 뜻한다. 축 진폭을 키우는 것은 비등방 스케일링이고 Machado 변위는 회전성 변위이므로, 축 배율은 아무리 커져도 회전의 부호를 뒤집지 않는다. 두 논문 어느 쪽도 hue 변위의 부호를 측정하거나 배제하지 않는다.
2. **`partial` 이 사실과 다르다.** Tregillus 는 V2v·V3v 에서 통제군과 구별 불가하다고 보고한다(Exp1 $p = .62$, $1.00$; Exp2 $p = .995$, $1.00$). 저자 표현은 `almost completely compensated` 이다.
3. **상한이 존재하지 않는다.** Boehm 의 개인 color-difference ratio 는 deutan 에서 정상 평균의 $45$–$121\%$ 이고(Results, Fig. 5), Tregillus 의 V3v 평균 $s_c = 7.82$ 는 완전 보상 기준 $7.3$ 을 넘는다. 정상 수준을 초과하는 개인이 양쪽에 있다.

이 원고의 아카이브판(`archive/appendix_absorbed_2026-09-02/appendix_alternative_models.tex:16`)은 이미 `whose gains scale response amplitude rather than a hue displacement` 라는 단서를 달고 있었고, 현행 본문이 그것을 잃었다.

**반영한 정정 (`.tex` 적용 완료)**

`Model` 문단 — 문헌을 이득의 **동기**로 인용하되 양이 다르다는 단서를 되살린다.

```latex
combined with a cortical compensation gain $g$. The gain is motivated by the
red--green contrast gain reported for anomalous trichromats
\parencite{boehm2014,tregillus2021}, whose measures scale response amplitude
rather than a hue displacement,
```

`Fits` 문단 — 문헌 범위에 기대지 않고 모형 내부의 사실로만 서술한다.

```latex
Under the loss combination adopted for each participant the fitted gain exceeds
$2$, the value at which the cortical term cancels the retinal shift, so the
family matches the data only by reversing the sign of the retinal hue
displacement.
```

이제 R+C 를 채택하지 않는 근거는 둘로 정리된다. **(i)** 적합이 이득의 정의역 밖(부호 반전 영역)에서만 자료를 맞춘다, **(ii)** deutan 은 Gate 2 의 경계 포화로 기각된다. 문헌은 이득 항의 동기만 제공하고 그 범위를 규정하지 않는다.

**되살리지 않는 것** — 아카이브판의 `inconsistent with the participants' confirmed residual CVD`. 부호가 반전된 변위도 여전히 왜곡이므로 잔여 CVD 와 논리적으로 모순되지 않는다.

---

### 9.12 S7 적용 시 정정한 것 — 정렬 누출 서술

§9.3 에서 `an orthogonal rotation that uses no stimulus labels` 를 `the rotation is estimated without reference to the held-out run or hue, so the alignment frame does not depend on the fold` 로 고쳤으나, **이 수정이 틀렸다.**

§2.5 에 따르면 각 런 $r$ 의 회전 $Q_r$ 은 $\|X_1 - Q_r X_r\|_F$ 를 최소화하므로 **그 런 자신의 데이터로 추정**되고, 정렬은 교차검증 이전에 여섯 런 전체로 한 번 수행된다. 따라서 fold 독립성이 성립하지 않는다. 원문의 `uses no stimulus labels` 도 틀렸지만(hue 행을 대응시킨다), 정정안이 다른 오류를 넣었다.

S7 문안 적용으로 해당 문단이 교체되며 정정되었다. 새 문안은 누출을 부정하지 않고 인정한 뒤 관측된 방향이 부풀림과 반대임을 보인다.

> The run-level rotation of \S\ref{sec:methods:roi} was estimated once from all six runs and held fixed during cross-validation, so a held-out run or hue contributed to the alignment frame of the training data. … Leakage through the fixed reference would raise the fixed-reference accuracy above the nested one; the observed difference runs the other way (\cref{tab:cv_leakage}).

$0.545 \to 0.578$ 쌍은 표 `tab:cv_leakage` 로 옮겨 산문에서 빠졌다.

---

### 9.13 S18 적용 — protan V1 신호 품질 근거 교체 (2026-09-06)

**추적 결과**

| 수치 | 판정 |
|---|---|
| `eight-way classification there reaches $0.79$` | **정확도가 아니라 효과크기다.** protan V1 hue-channel LORO 의 $0.625$ 를 통제군 $0.542 \pm 0.106$ 에 견준 $d_{cc} = +0.790$ 이며, 같은 부록의 다른 문단이 이미 `$d_{cc} = +0.59$ and $+0.79$` 로 싣고 있다. exp2 파이프라인의 상관 template-matching 정확도 $0.7917$ 과도 일치하나 그것은 Session-1 hue-channel 8분류가 아니다 |
| `split-half pattern reliability reaches $.847$` | **실재한다.** `analysis/validation/results/color_correspondence_heldout.json` 의 `V1/within_subject_split_half_rdm_r/sub-09` 이며 재현된다. 다만 런 1--3 대 4--6 의 **고정 단일 분할**이고, 복셀 공간 유클리드 RDM 의 Pearson $r$ 이다. 원고가 정의하는 split-half(SRM 공간·Spearman·홀짝 런, `supplementary.tex` S4)와 다른 지표이며 원고에 정의가 없다. 10개 분할을 모두 돌리면 통제군 단일 분할 최댓값이 $.952$ 라 `above the highest control value` 가 성립하지 않는다 |

**반영한 교체 (`.tex` 적용 완료)** — 새 수치를 도입하지 않고 원고 표만으로 같은 논증을 세운다.

```latex
The V1 correspondence is displaced by one hue step, and the departure is not one
of signal quality. At that region the participant's eight-way classification
accuracy was $0.562$ under the Procrustes readout and $0.625$ in the SRM space,
against control means of $0.580$ and $0.542 \pm 0.106$
(\cref{tab:alignment,tab:loro_decoders}), and linear discriminant analysis
reached $0.854$ against a control mean of $0.878 \pm 0.050$, all above the
$0.125$ chance level. The activation-level metrics, including run-to-run
reliability, likewise placed the participant inside the control distribution at
V1 (\cref{app:activation}).
```

**부수 수정** — 신설한 `tab:cyclic_shift` 가 $54.3$pt 넘쳐 `\small` 과 열 간격 $4$pt 를 적용하고, `best shift, SRM basis ($315^\circ$)` 를 `$315^\circ$, SRM basis` 로 줄여 아래 행과 형식을 맞췄다.

---

### 9.14 S13 적용 — 경계 포화율을 축별로 분리 (2026-09-06)

현행 원고의 `the combined fraction of resamples reaching a grid boundary rising from $0.09$ to $0.72$` 에서 $0.72 = 0.283 + 0.437$ 은 두 축 비율의 **합계**이며, `fraction of resamples reaching a grid boundary` 가 뜻하는 **합집합**이 아니다. 비교 대상인 $0.09$ 는 단일 축 값이라 기준도 어긋난다.

`beta_sign_three_arms.json` 확인 결과 네 칸 중 deutan HMC 만 두 축에 걸쳐 있다.

| | deutan baseline | deutan hmc | protan baseline | protan hmc |
|---|---|---|---|---|
| $\beta_c$ 하단 | $0.000$ | $0.283$ | $0.000$ | $0.000$ |
| $\beta_c$ 상단 | $0.000$ | $0.000$ | $0.000$ | $0.107$ |
| $\beta_s$ 경계 | $0.093$ | $0.437$ | $0.000$ | $0.000$ |

축별로 나누면 모든 칸이 정확해지고, HMC 에서 흔들린 축이 주로 $\beta_s$ 라는 사실도 드러난다. 합계 표기로는 보이지 않던 정보다.

| 행 | deutan | protan |
|---|---|---|
| Resamples with $\hat\beta_s$ at a grid edge | $0.09 \rightarrow 0.44$ | $0.00 \rightarrow 0.00$ |
| Resamples with $\hat\beta_c$ at a grid edge | $0.00 \rightarrow 0.28$ | $0.00 \rightarrow 0.11$ |

---

### 9.15 S12 적용 — 집계 단위 평균 통일 (2026-09-06)

**평균을 택한 근거**

`param_recovery_voxel_v6_pca_v2.json` 의 실제 값이다.

| 후보 | $f_{10^\circ}$ 평균 / 중앙값 | bias $\beta_s$ 평균 / 중앙값 | bias $\beta_c$ 평균 / 중앙값 |
|---|---|---|---|
| deutan | $0.26$ / $0.20$ | $+18.6$ / $+16.0$ | $-4.7$ / $-4.0$ |
| protan | $0.14$ / $0.15$ | $+11.9$ / $+11.0$ | $-26.4$ / $-27.0$ |

1. **$f_{10^\circ}$ 가 결정적이다.** donor 마다 노이즈 실현이 정확히 20 개씩이므로 7 개 비율의 평균이 **140 회 재적합 전체의 비율**과 같다. 통과 기준 $f_{10^\circ} \ge 0.5$ 가 묻는 것이 그 전체 비율이고, 부록도 $n = 140$ 이라 적는다. 7 개 비율의 중앙값에는 대응하는 해석이 없다.
2. bias 기준 $\lvert\text{bias}\rvert < 10^\circ$ 는 계통 편차를 묻는다. donor 값이 이미 20 회의 중앙값이므로 안쪽 중앙값·바깥 평균이라는 표준 구조가 된다.
3. **자기유리 편향이 없다.** 평균이 deutan bias 를 $+16.0$ 에서 $+18.6$ 으로 키워 실패를 더 두드러지게 한다.

현행 표의 deutan 괄호는 **한 쌍 안에 중앙값과 평균이 섞여 있었다**($+16$ 은 중앙값, $-4.7$ 은 평균). 이것이 가장 확실한 오류다.

| | 현재 | 반영 |
|---|---|---|
| deutan | $(+16^\circ, -4.7^\circ)$ | $(+18.6^\circ, -4.7^\circ)$ |
| protan | $(+11^\circ, -27^\circ)$ | $(+11.9^\circ, -26.4^\circ)$ |

캡션에 `averaged over the seven donor cells` 를 명시했다. 산문의 `bias of $4.7^\circ$ ... against $16^\circ$` 문장은 Results `:92` 와 중복이라 문단째 삭제되어 불일치가 함께 사라졌다.

**함께 반영한 둘**

- `spatial PCA(20) on SRM-projected amplitudes` → `the top 20 principal components of each donor's residual spatial covariance with an AR(1) correlation of $0.3$ across runs`. 코드(`forward_voxel_synth.py`, `neural_loss.load_amplitudes`)상 rank 20 은 잔차 공분산의 주성분 수이고 입력은 복셀 공간 진폭이다.
- Test 2b 의 verdict 를 `FAIL` 에서 `not met` 으로 완화했다. 2b 는 순위 백분위를 내는 서술적 검사이고 선택 결정에 들어가지 않으므로 검정과 같은 라벨을 달지 않는다.

---

### 9.16 C 군 정리 (2026-09-06)

| # | 조치 | 결과 |
|---|---|---|
| C1 | `results_v4.tex:84` 의 `\label{sec:results:rc_insufficient}` 삭제 | S11 개정으로 참조가 0 회가 되어 안전하게 제거. 심사자가 R+C 전용 절을 기대하고 2성분 절에 도착하는 문제도 사라진다 |
| C2 | `methods_v2.tex:158` 의 `retinal-plus-gain` → `retinal-plus-cortical` | 약어 R+C 와 부록 표기에 통일 |
| C3 | `supplementary.tex` S18 앞 주석 정리 | 존재하지 않는 `REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md` 참조와 폐기된 `motreg` arm 수치(`18 raw / 15 BH`)를 제거하고 현행 표를 가리키게 고침 |
| C4 | `Methods/bibliography.bib`(고아, 27 항목) 삭제, `brouwer2013additional`(중복) 삭제 | `main.tex` 가 부르지 않는 파일이었고 중복 항목은 인용 0 회. 미인용 88 개 중 나머지는 **유보**(향후 인용 가능, 출력 무영향) |
| C5 | Zenodo DOI | **저자가 이미 처리.** `main.tex` 가 `doi:10.5281/zenodo.22369832`, release v1.0.0, 저장소 `haba6030/colorblind_public` 으로 갱신되어 미해결 `\todo` 는 없다 |

**부수 발견** — 갱신된 Data and Code Availability 문단에 영국식 `organised` 가 들어와 있어 `organized` 로 고쳤다(`main.tex:27` 의 `[american]{babel}` 선언과 일치).

---

### 9.17 §9 작업 종료 요약

부록 18 개 절을 전부 개정하고 `.tex` 에 반영했다. 매 단계 `biber` + `pdflatex` 로 검증했으며 최종 상태는 **overfull 0, 미해결 참조 0, biber 경고 0** 이다.

| 지표 | 개정 전 | 개정 후 |
|---|---|---|
| 부록 산문 | 6,445 단어 | **4,690 단어** (−27 %) |
| 표 | 18 | **24** (S4 `tab:kselect`, S7 `tab:cv_leakage`, S10 `tab:activation`, S12 `tab:sign_basis`, S16 `tab:test_directions`, S18 `tab:cyclic_shift` 신설, `tab:effect_sizes` 삭제) |
| 최장 문단 | 273 단어 | 199 단어 |

**개정 과정에서 확인한 사실관계 오류 (전부 반영)**

| 위치 | 오류 | 확인 방법 |
|---|---|---|
| 본문 §2.6, S4 | $k$ 선택 규칙이 배포값을 만들지 않음(3지표 composite 1/4 일치) | `aggregate_k_selection.py` 재실행 |
| S11, `results_v4.tex:94` | R+C 가 S-cone 변위를 표현하지 못한다 | `rc_scone_projection.py` 신설, deutan $\lvert\beta_s/\beta_c\rvert = 0.94$ |
| S11 | $\Delta$RDM 직접 적합이 같은 경계 행동 | `s0{8,9}_pca_allcombos_composite_N300.json`, 채택 앵커에서 $0.000$/$0.117$ |
| S11 | 두 참가자 모두 경계 포화 | protan $41\%$ 는 Gate 2 문턱 아래 |
| S11 | `partial compensation` 범위를 문헌 근거로 사용 | Boehm·Tregillus 전문 확인, 측정량이 hue 각도가 아님 |
| S12 | Test 1 행에 평균과 중앙값 혼재 | `param_recovery_voxel_v6_pca_v2.json` |
| S12 | `spatial PCA(20) on SRM-projected amplitudes` | 코드 대조 |
| S13 | 경계 포화율 $0.72$ 가 합집합이 아닌 합계 | `beta_sign_three_arms.json` |
| S18 | protan V1 8분류 $0.79$ | 효과크기 $d_{cc} = +0.790$ 의 오독 |
| S18 | split-half $.847$ 이 `above the highest control value` | 10 분할 전체에서 통제군 최댓값 $.952$ |
| `supplementary.tex` 정렬 문단 | `rotation that uses no stimulus labels` | §2.5 의 $8\times8$ hue 회전과 모순 |

**sub-10 오염 점검** — `tab:loro_decoders` 를 의심했으나 통제군 $n=7$·CVD $n=2$ 로 정확히 구성되어 있음을 산출물로 확인했다(§9.3).

**남은 항목** — §9.9 B 군의 B4(통제 앵커 수치 1차 출처), B5(순환 이동 RSA 산출물), B6(hV4 $0.45$/$0.46$), B8(crossnobis V1 $p=.120$ 의 $n=2$ 산출물). 넷 다 원고에 실린 값이 산출물과 어긋난다는 증거는 없고, 1 차 출처를 특정하지 못한 상태다.

---

### 9.18 부정 결과의 해석 공백 보완 (2026-09-06, 저자 지시)

압축 과정에서 **결과는 남기고 그것을 어떻게 읽어야 하는지를 지운** 자리가 넷 있었다. 실패나 영(null)을 제시한 뒤 결론 없이 끝나면 부록만 읽는 심사자에게 원고의 가치를 낮춘다.

#### S12 — 검사 넷이 전부 실패로 제시되고 끝남

`tab:identifiability` 가 FAIL·FAIL·not met·FAIL 을 싣고 문단이 종료됐다. 이전 판의 마무리 문장은 Results `:91` 과 중복이라 삭제됐으나, 그 결과 부록에는 결론이 없어졌다. Results 를 되풀이하지 않고 **검사가 무엇을 제한하고 무엇을 제한하지 않는지**를 새로 적는다.

```latex
\paragraph{What the checks bound.}
The four checks concern the parameters as magnitudes. Test~1 and Test~2a place
the recovery uncertainty of the procedure above the fitted S-cone amplitudes in
both participants, so those amplitudes are bounded and not estimated, and the
deutan confusion-axis magnitude is the one fitted value that exceeds that
uncertainty. Test~2b and Test~2c place the fits inside the range that control
data and permuted labels produce, so the values do not separate the CVD
participants from either reference. The parameters are accordingly read as the
direction and relative weight of a distortion and not as physiological
quantities, and magnitudes are not compared between participants or attributed
to regions.

These checks are distinct from the generalization tested at selection. Gate 3
ranks candidates by held-out loss on control references withheld from training
(\S\ref{sec:methods:selection}), which asks whether the loss surface transfers to
unseen references, whereas Test~1 asks whether the location of its minimum can be
recovered under matched noise. A surface can transfer while remaining flat near
its minimum, and the resample spread of \cref{tab:fit_stability} is consistent
with that combination. The stimulus-space filter follows from the fitted
transform whatever the status of its parameters, and its evaluation is the
prospective session of \S\ref{sec:methods:filter}, which does not rest on the
parameters being point estimates.
```

둘째 문단이 핵심이다. **일반화 통과와 복원 실패가 모순이 아니라는 것**을 밝히지 않으면, 심사자는 Gate 3 을 통과한 적합이 왜 Test 1 에서 실패하는지를 결함으로 읽는다. 손실면이 이전(transfer)되면서 최솟값 근방이 평탄할 수 있고, `tab:fit_stability` 의 resample 산포가 그 조합과 일치한다.

#### S9 — 절의 결론 문장이 사라짐

압축판이 `Disparity tracks the same subject-level quantity when the alignment method changes.` 라는 주장 문장을 지우고 방법 서술로 시작하게 되었으며, 이 절의 유일한 긍정 결과(피험자 수준 일치도)가 표에만 남았다. 두괄식 원칙에도 어긋난다. 복원하고 수치를 함께 적었다.

> Disparity tracks the same subject-level quantity when the alignment method changes. … Agreement was substantial under both reductions (pooled Spearman $r = 0.780$ for PCA and $0.544$ for PCA--CCA, both $p < .001$) and highest at V1 and V2.

또한 집단 수준 Hedges' $g$ 가 $-0.13$–$+0.40$ 로 작다는 사실만 남고 그 이유가 삭제되어 있었다. 쌍별 정렬이 공동 적합 공유공간보다 잡음이 크다는 설명과, 이 절의 주장이 집단 대비가 아니라 피험자 수준 일치도에 근거한다는 한정을 되살렸다.

#### S18 — `remains open` 으로 종료

부정 서술 10 개 뒤에 열린 질문으로 끝났다. 이 절이 실제로 확립하는 것(동결 투영이 검정력을 갖는 설계이고, 그 아래에서 두 참가자의 편차가 색 특이적이다)을 적되, 국재 주장은 하지 않는다.

```latex
Taken together, these checks establish the design under which the comparison is
read. The frozen projection is the variant with power, as the control positive
control shows, and under it the deviations of both CVD participants depend on
which hue evoked which response rather than on generic pattern differences. What
the checks do not establish is where that dependence sits: the grid is
descriptive, its cells shift between preprocessing pipelines, and the regional
attribution is left open in the main text (\S\ref{sec:results:geometry}).
```

#### S14 — 강건성 점검의 결과가 없음

`Each neural contrast was recomputed after dropping each single run … and after re-extracting … on the voxel set of the unfiltered baseline.` 로 끝나 **절차만 있고 결과가 없었다.** 결과 없는 강건성 점검은 실패를 감춘 것으로 읽힌다. `exp2_neural/RESULTS.md:61,69` 의 결과를 효능 대비 서술 없이 옮겼다.

> Dropping a run left the direction of every contrast in \cref{app:exp2_outcomes} unchanged. Re-extraction on the baseline voxel set lowered the V1 magnitudes, one of the reasons the second-session contrasts are reported as provisional (\cref{app:uncorrected}).

V1 축소는 통과가 아니므로 통과로 적지 않고, 원고가 이미 취하는 잠정(provisional) 입장의 근거로 연결했다.

---

### 9.19 B 군 출처 추적 결과 (2026-09-06)

| # | 항목 | 분류 | 조치 |
|---|---|---|---|
| B4 | 통제 pseudo-CVD 앵커 | **확인·일치** | 조치 없음 |
| B5 | 순환 이동 RSA | **미특정** | 해당 행·정의 삭제 |
| B6 | hV4 통제 평균 $0.45$ / $0.46$ | **확인·집계 풀 차이** | 풀을 명시 |
| B8 | crossnobis V1 $p = .120$ | **확인·일치** | $n=2$ 산출물 커밋 |

#### B4 — 확인·일치, 조치 없음

1차 산출물은 `analysis/phase5_filter_optimization/results/redteam/null_within_hc_loo_v6_pca.json` 의 `cells/{S08-robust, S09-primary}/B1_records[*]` 이며, $\|\hat\beta\| = \mathrm{hypot}(\beta_s, \beta_c)$ 로 유도된다. HC 7명만 들어가고 sub-10 은 없다.

| | 산출값 | 원고 |
|---|---|---|
| deutan | min $30.463$, max $58.138$, mean $49.138$ | $30.5$–$58.1$ ($49.1$) |
| protan | min $23.409$, max $55.462$, mean $35.666$ | $23.4$–$55.5$ ($35.7$) |

앞서 제기된 `30.594` / `35.777` 은 `closure/specificity/…synth-fakecvd-N200.json` 의 **합성 CVD 거리 배열** 원소로 통제 앵커와 무관하다. 실제 최솟값이 $30.463$ 이므로 반올림 $30.5$ 가 맞다.

#### B5 — 미특정, 해당 내용 삭제

RSA 쪽 수치(항등 $\rho \approx 0.00$, $315^\circ$ $+0.52$, $225^\circ$ $+0.50$, 통제군 $0.45$, $z = +5.02$, $p = .002$, $p_{\rm adj} = .032$)는 **어느 JSON 이나 스크립트에도 없다.** 텍스트상 최초 출처는 삭제된 `REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md`(commit `e3c676d`)이고 그 문서도 경로를 인용하지 않는다.

삭제한 이유는 산출물 부재만이 아니다.

1. **$z$ 에서 $p$ 가 도출되지 않는다.** $z = (0.523 - 0.037)/0.097 = 5.01$ 은 재현되나, 정규근사로는 $p \approx 10^{-7}$ 이지 $.002$ 가 아니다. 어떤 재표집 귀무인지 기재가 없다.
2. **`16칸 가족`이 정의되지 않는다.** $p_{\rm adj} = .032 = .002 \times 16$ 이나 그 16칸의 구성이 어디에도 없다. 원고의 BH 족은 식별 검사 6 개와 색 대응 35 칸이다.
3. **같은 문서 안에서 값이 충돌한다.** 다른 표는 동일 통계량에 대해 `sub-09 V1 만 명목 유의 (SRM p = .025, PCA p = .034), 16칸 FDR 통과 0` 이라 적는다. $p = .002$ 와 $p = .025$ 가 같은 문서에 공존한다.

재현 가능한 Procrustes disparity 분석($1.037 \to 0.788$, 이득 $24.0\%$, 통제군 $3.5 \pm 5.9\%$, $t = 3.22$, $p = .009$, $d_{cc} = 3.44$)은 `cyclic_shift_disparity.json` 과 `shift_gain_ch.json` 에서 확인되므로 **그대로 둔다.** 한 색 단계 이동이라는 결론은 이것만으로 성립한다. RSA 는 수렴 증거였을 뿐이다.

되살리려면 분석을 정본 스크립트로 재실행하고 $p$ 의 귀무와 검정족을 정의해야 한다.

#### B6 — 두 값은 다른 집계, 풀을 명시

같은 per-subject 값의 두 집계였다.

| 출처 | 풀 | $n=4$ 런 | $n=6$ 런 |
|---|---|---|---|
| `run_count_validation/adjacc_retention_summary.json` (S14) | HC 7 | $0.4491$ | $0.4560$ |
| `exp2_neural/…_matched.json` (`tab:exp2_geometry`) | HC 6 (sub-07 제외) | $0.4556$ | $0.4653$ |

S14 의 run-count 분석은 **Session-1 자료의 민감도 분석**이므로 본문 §3.1 의 관례(hV4 통제군 $n=7$, 평균 $0.456$)와 같은 풀을 쓰는 것이 맞다. 실제로 S14 의 `$0.46$ at $n=6$` 이 본문 $0.456$ 과 같은 값이다. `tab:exp2_geometry` 의 $0.46 \pm 0.11$ 은 2차 세션 기준이라 하나를 뺀 6명 풀이며, S14 가 이미 `n = 6 at hV4, where one control has too few voxels` 라 적는다.

수치를 바꾸지 않고 풀만 명시했다.

> hV4 adjacent accuracy at $n = 4$ gave a mean of $0.45$ **over the seven controls** ($0.46$ at $n = 6$, the Session-1 value of \S\ref{sec:results:loco}), …

**코드 쪽 확인 사항** — `run_count_adjacc.py:116` 이 `hc_pool = HC_HV4 if roi == "V4"` 로 sub-07 제외를 의도하나 요약값은 7명 평균이다. `HC_SUBJECTS` 의 ID 형식(`"07"`) 때문에 필터가 걸리지 않았을 가능성이 있다. 원고는 7명 풀이 맞으므로 수치 영향은 없으나 메타데이터(`config.hc_hv4_excludes`)와 산출이 어긋난다.

#### B8 — 확인·일치, 산출물 커밋

커밋본 `crossnobis_results.json` 은 sub-10 을 포함한 $n=3$ 이며 V1 $0.122$ / $p = .0508$ 이다. 원고 값은 $n=2$ 기준이고 스크립트 재실행으로 정확히 재현되었다(V1 $0.104$, $p_{\rm perm} = .1197$; V2 $.019$, V3 $.046$, hV4 $.045$; Spearman $.833$/$.733$/$.550$/$.300$, pooled $.632$ — `tab:triangulation` 5 값 전부 일치).

재현 결과를 `analysis/phase2_SRM_across_between/validation/results/crossnobis_rdm/crossnobis_results_n2.json` 로 보존했다. 이제 원고의 모든 crossnobis 수치가 커밋된 산출물을 갖는다.

**주의** — 커밋본 `crossnobis_results.json` 은 sub-10 을 포함하므로 인용하면 안 된다. CLAUDE.md 의 경고가 그대로 적용되는 사례다.
