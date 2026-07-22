# Introduction v2 — TODO 처리 협의록 (2026-07-22)

대상: `Introduction/introduction_v2.tex`
저자가 본문에 남긴 TODO 15건에 대한 처리 방침. **본 문서는 협의용이며, 합의된 블록만 tex에 반영한다.**
처리 순서: Intro-1 → Intro-2 → Intro-3 → Intro-4 → Intro-5.

---

## 진행 상태

| 블록 | 관련 TODO | 상태 |
|---|---|---|
| Intro-1 What CVD is | T1, T2(전반부) | **합의 완료 — 반영 대기** |
| Intro-2 Current correction | T2(후반부), T3, T4, T5, T6, T7 | **합의 완료 — 반영 대기** |
| Intro-3 Neural features | T8, T9, T10, T11, T12, T13 | **합의 완료 — 반영 대기** |
| Intro-4 Gaps | T14, T15 | **합의 완료 — 반영 대기** |
| Intro-5 RQ | — | 변경 없음 |

---

## Intro-1 — 확정안

### 변경 요지

1. **T1 반영(삭제).** `The elevated discrimination thresholds are quantified instead by threshold psychophysics~\citep{boehm2014, bosten2019}.` 제거.
   사유: threshold 측정은 본 연구가 직접 수행하는 절차(JND)이므로 Methods 소관. Intro에서 타 문헌으로 방법을 예고할 이유 없음.
   ("이 문장이 Intro-2의 plate/appearance-test 비판의 복선"이라는 초기 논거는 **철회**. Intro-2의 비판 대상은 검사의 해상도가 아니라 *기준*(appearance report)이므로 선행 설명이 불필요.)

2. **Ishihara 문장 삭제.** `The Ishihara test screens for the resulting red--green confusions~\citep{ishihara1917}.` 제거.
   사유: 표현형 서술 문단에서 검사 도구 언급이 맥락 없이 삽입됨.
   인용 고아 여부 확인 완료 — `ishihara1917`은 `Methods/methods_v2.tex:37`에 존치, `boehm2014`는 `Introduction §Intro-3` 및 Results/Discussion에 존치.

3. **T2 전반부 반영(신규 2문장).** 개인 간 편차를 Intro에서 처음으로 독립 명제로 확립.
   새 문헌을 끌어오지 않고, **본문에 이미 있으나 해석되지 않던 `2--12 nm` 범위를 해석**하는 방식.
   층위를 지키기 위해 두 문단에 나눠 배치: 기전 수준 편차 → ¶1.1, 표현형 수준 편차 → ¶1.2.

### 확정 문안

**¶1.1**

> Color vision deficiency (CVD) affects approximately 8\% of men and 0.4\% of women of European ancestry~\citep{birch2012}.
> It arises from altered spectral sensitivity of the L- or M-cone photopigment. This altered sensitivity is driven by X-linked polymorphisms in the cone opsin genes~\citep{deeb2005, neitz2011}. In anomalous trichromats, the L- and M-cone spectral peaks are separated by only about 2--12~nm, versus roughly 25~nm in normal trichromacy~\citep{neitz2011}. This reduced separation weakens the L--M cone-opponent signal rather than abolishing it. **The size of the shift is not fixed: it varies continuously across affected individuals, and the two red--green subtypes, protan and deutan, differ in which photopigment is displaced~\citep{neitz2011}.**

**¶1.2**

> A weakened L--M signal yields a characteristic peripheral phenotype. Affected observers show reduced red--green discrimination, frequent category confusions, and elevated just-noticeable differences along the L--M chromatic axis. **Because the underlying shift is graded, the severity of this phenotype varies markedly even within one diagnostic subtype~\citep{bosten2019}. Observers who share the same diagnostic label can therefore differ substantially in how their color space is compressed.**

### 문장별 역할

| 문단 | # | 역할 |
|---|---|---|
| ¶1.1 | 1 | 규모(유병률) |
| | 2 | 원인(유전) |
| | 3 | 정량(2–12 vs 25 nm) |
| | 4 | 결과 — 약화이지 소실 아님 |
| | 5 (신규) | 그 수치가 *범위*임을 해석 — 기전 수준 개인차 + 두 subtype |
| ¶1.2 | 1 | 표현형 topic sentence |
| | 2 | 표현형 내용 |
| | 3 (신규) | 기전 개인차 → 표현형 개인차로 전달 |
| | 4 (신규) | 진단 범주가 개인을 특정하지 못함 |

### 주장 수준 경계 (필독)

여기서 확립되는 명제는 **"사전에 고정된 단일 변환은 어느 개인에게도 맞을 수 없다"(architecture)** 까지다.
**"개인별 보정이 subtype 평균보다 우수하다"(efficacy)로 읽히면 안 된다** — 해당 명제는 §Intro-5 마지막 문단과 Discussion Limitation 1이 명시적으로 부인하며, 본 연구의 Results가 갚지 못한다.
위 문안은 "진단 범주가 개인을 특정하지 못한다"까지만 말하고 효능 비교를 건드리지 않는다.

### 하류 의존성

¶1.2의 신규 2문장은 **Intro-2의 T6·T7 수정이 인용할 선행 명제**다. 따라서 Intro-1이 먼저 확정되어야 Intro-2를 손댈 수 있다.

---

## Intro-2 — 확정안

### 변경 요지

| TODO | 처리 |
|---|---|
| **T2**(후반) | ¶2.1에 `As CVD varies in type and degree, ...` 신규. Intro-1 ¶1.2를 직접 서술로 회수(초안의 `Given the variation described above`는 지시 대상이 불명확하여 폐기) |
| **T3** | `have mostly taken one route: tuning...` → `have mostly tuned a \emph{single} retinal cone-shift parameter...` |
| **T4** | "report 의존의 비신뢰성" 및 초안의 "no independent way to verify"는 **철회**. 광색소 이동은 opsin genotype·분광감도로 객관적 특정이 가능하므로(`deeb2005`, `stockman2000`) 사실과 다름. 한계를 **"망막 파라미터는 피질 표상이 어떻게 변형되었는지를 담지 못한다"**로 직접 서술. (초안은 `cortical compensation`을 지목했으나, 보상은 변형의 *한 사례*이므로 상위 개념인 `how the cortical color representation is itself altered`로 일반화 — Intro-3이 부호 → 보상 순서를 유지할 수 있게 됨) |
| **T5** | `Their results show the cost.` 삭제, **대체 문장 없음**. 개인화 시도의 성능을 평가한 문헌이 없어 일반화 실패를 경험적으로 주장하지 않음 → ¶2.2는 전체가 개념 논증 (D1 = (b) 확정) |
| **T6** | 독립 문장(`too coarse to span the variation`)은 뜬금없어 **삭제**하고, `single`을 첫 문장 안으로 흡수해 해당 연구들의 서술 자체가 되게 함 |
| **T7** | `patterson2022`, `somers2024` → ¶2.1로 이동 |

부수 정리: 콜론 6개 → 0개. `Across this diversity, the two families share one commitment:` → `These two families optimize against...`. ¶2.2는 7문장 → 5문장.

### 확정 문안

**¶2.1**

> Current CVD correction methods fall into two structurally related families. Hardware filters form the first family. Dichroic notch lenses, such as the EnChroma line, are designed to filter narrow spectral bands and amplify the residual red--green signal. Software filters form the second. Brettel--Vi\'enot--Mollon simulation~\citep{brettel1997} and the parameterized Machado retinal model~\citep{machado2009} forward-project a stimulus onto an anomalous retina. Their Daltonization inverses, including recent algorithmic reformulations~\citep{akalin2025}, redistribute the lost contrast into channels the user can still see. **These two families optimize against a population-average retina and apply the same transform to every user. As CVD varies in type and degree, such a population-level transform cannot be matched to any particular observer. Empirically,** color-enhancing glasses improved discrimination for only one of two consumer products tested~\citep{patterson2022}, and population-average filters shift the appearance of color while leaving generalized discrimination largely unchanged~\citep{somers2024}.

**¶2.2**

> Attempts to escape this average-user ceiling have mostly tuned a \emph{single} retinal cone-shift parameter to a user's responses on plate-style or appearance-matching tests. **The shift itself can be estimated accurately, from opsin genotype or from cone spectral sensitivities measured in observers of known genotype~\citep{deeb2005, stockman2000}. But a retinal parameter, however it is obtained, cannot describe how the cortical color representation is itself altered in CVD. It fixes the input to the visual system, not the representation built from that input.** What is missing is a filter derived from, and grounded in, the user's \emph{own} neural color representation.

### 문장별 역할

| 문단 | # | 역할 |
|---|---|---|
| ¶2.1 | 1 | topic — 두 계열 |
| | 2–3 | hardware |
| | 4–6 | software / Daltonization |
| | 7 | 공통 약점 지목 (집단평균 + 동일 변환) |
| | 8 (신규) | 원리적 한계 — Intro-1 회수 |
| | 9 (이동) | 경험적 확인 |
| ¶2.2 | 1 | 개인화 시도의 실체 (파라미터 1개) |
| | 2 (신규) | **양보** — 망막 추정은 정확할 수 있다 |
| | 3 (신규) | **반전** — 그래도 피질 표상의 변형은 담지 못한다 |
| | 4 (신규) | 이유 — 입력을 고정할 뿐 표상이 아니다 |
| | 5 | Intro-3으로 넘기는 미완 명사구 (`own`) |

### 하류 의존성 — Intro-3 문단 순서는 유지

초안에서는 ¶2.2-3이 `cortical compensation`을 인용 없이 먼저 지목했고, 그 빚을 즉시 갚기 위해 Intro-3의 보상 문단을 앞으로 당겨야 했다.
확정안은 이를 **`how the cortical color representation is itself altered`(상위 개념)**로 일반화했으므로, 빚을 갚는 주체가 Intro-3 **전체**가 된다. 따라서 문단 순서를 바꿀 필요가 없다.

확정 순서: **(¶3.1 삭제) → 피질 색 부호 → 보상 → 결론**

전개: ¶2.2가 "피질 표상이 변형된다"고 선언 → Intro-3-1이 그 *피질 표상*이 무엇인지 정의(연속 부호·사람 간 공유) → Intro-3-2가 변형의 구체적 사례(보상)를 근거와 함께 제시 → Intro-3-3이 설계 결론.

---

## Intro-3 — 확정안

### 변경 요지

| TODO | 처리 |
|---|---|
| **T8** | 구 ¶3.1 전체 삭제. `not an on--off loss`(¶1.1과 중복), `quantitatively reweighted but qualitatively similar`(무인용·미정의), `not absent but structurally distorted`(결론과 중복) 제거. `downstream machinery stays intact`는 삭제하지 않고 **범위를 좁혀 3문단 말미의 명시적 전제로 재서술** |
| **T9** | 새 문장 없음. "단순 신호 손실이 아니다"는 서술은 보상 문단이 이미 수행하므로 구 ¶3.1 삭제만으로 해결 |
| **T10** | 문단 삭제 반대(연속 부호 + 사람 간 공유 = SRM/공통공간의 유일한 문헌적 근거). 대신 **추상어 전면 재서술**: `This code`(지시 모호), `common space`(불명), `read out`(추상), `recently validated`(비학술적) 모두 제거하고 조작적 서술로 교체. `bannert2018`의 `hub linking seen and remembered color`는 여기서 삭제하고 **3문단으로 이동**(hV4–행동 연결 근거로 실제 기능함) |
| **T11** | `This evidence comes from psychophysics rather than from imaging...` **삭제**. 불필요할 뿐 아니라 **사실과 어긋남** — `tregillus2021`은 fMRI 연구("Color compensation in anomalous trichromats assessed with fMRI", Current Biology). 해당 사실을 근거로 전환하여 `the amplification is measurable in the cortical response itself`로 사용 |
| **T12** | `key variance`·`retinal--cortical interface`(미정의어) 삭제. 2문단 첫 문장을 `This geometry cannot be predicted from the retina alone.`로 직접 진술하고, 마지막 문장에서 결론 회수 |
| **T13** | `inherits it` → `absorbs both into a single retinal parameter`. `, not the simulated retina,` 삽입구 제거(앞서 충분히 서술됨) |
| — | `This is a design hypothesis, and the rest of the paper tests it.` 삭제 (Intro-5가 담당) |

### `emery2021` — NotebookLM 원문 확인 결과

기존 본문의 "chromatic responses realign toward the blue--yellow direction"은 실재하는 결과이나(blue-yellow phase가 SvsLM 축 쪽으로 **21.4°** 회전), **Intro에서는 사용하지 않는다** — 프로젝트에서 anchor 과장 금지로 걸어둔 그 수치이기 때문.

대신 본 논문의 논지와 직결되는 원문 결론을 사용:

> "While the compensation was pronounced it was nevertheless **partial**, and anomalous observers differed systematically from the controls in the **shapes of the hue-scaling functions and the corresponding loci of their color categories**."

즉 보상은 부분적이고, **남는 차이가 진폭이 아니라 형태·범주 위치**(= 구조적)라는 것. 부수 정보: RG 진폭은 1.5배 약한데 역치 민감도는 6배 나빠 약 4배의 suprathreshold gain에 해당하며, 노이즈는 함께 증폭되지 않음.

### bibliography.bib 오류 — **수정 완료 (2026-07-22)**

`emery2021` 저자 항목이 틀려 있었음.

| | 값 |
|---|---|
| 수정 전 | Emery, K. J. and **Volbrecht, V. J. and Peterzell, D. H.** and Webster, M. A. |
| 수정 후 (Vision Research 183:1–15, 2021) | Emery, K. J. and **{Kuppuswamy Parthasarathy}, M. and Joyce, D. S.** and Webster, M. A. |

수정 전 값은 Emery/Volbrecht/Peterzell/Webster의 다른 논문 저자진이었음. volume·pages·doi는 원래부터 정확했으므로 저자만 교체.
`Kuppuswamy Parthasarathy`는 두 단어 성이므로 중괄호로 묶어 apacite가 이름/성을 오분할하지 않게 함. `bibtex main` 재실행으로 `main.bbl` 출력 확인 완료.

### 확정 문안

**¶3.1 — 피질 색 표상의 기하**

> Cortical color is a distributed, hierarchical computation~\citep{gegenfurtner2003, shapley2011, conway2018}. Early visual cortex carries cone-opponent signals, and hue-selective responses to intermediate colors are already present in V1~\citep{parkes2009, kuriki2015}. In higher-order regions, and hV4 in particular, the distributed response to a color specifies more than which color was seen. It also specifies where that color lies relative to the others. A hue withheld from training can be reconstructed from the responses to its neighbours~\citep{brouwer2009}. The cortical representation of color therefore has a geometry, and that geometry is similar enough across people that a color can be identified in one observer from the response patterns of others~\citep{bannert2025}.

**¶3.2 — CVD에서의 변형**

> This geometry cannot be predicted from the retina alone. Anomalous trichromats compensate for the retinal shift at a cortical level, where long-term adaptation reshapes hue appearance independently of the retina~\citep{boehm2014, webster2015} and the amplification is measurable in the cortical response itself~\citep{tregillus2021}. In deutan observers, chromatic-contrast adaptation exceeds what the loss in threshold sensitivity predicts, consistent with a post-receptoral gain that partly offsets the weaker L--M signal~\citep{basim2025}. The compensation is also only partial, and what remains is structural. Anomalous observers still differ from normal trichromats in the shape of their hue-scaling functions and in the loci of their color categories~\citep{emery2021}. The color geometry an observer with CVD actually has is thus settled in cortex, and a model of their color representation should capture it.

**¶3.3 — 설계 결론과 전제**

> A correction calibrated to the retina cannot separate the retinal loss from this cortical reorganization. It absorbs both into a single retinal parameter and so acts at the wrong level. Among the regions carrying this geometry, hV4 lies closest to perception, and its activity patterns predict behavioural performance in color tasks~\citep{bannert2018}. We therefore take the individual's cortical readout as the reference from which to compute a correction to the retinal input, adopting the premise that shifting an individual's hV4 color geometry toward that of the healthy population moves their color perception with it.

### 문단 간 전개

| 위치 | 하는 일 |
|---|---|
| ¶2.2 끝 | "망막 파라미터는 피질 표상의 변형을 담지 못한다" — 빚을 짐 |
| ¶3.1 | 그 *피질 표상*을 정의 — 연속적 기하 + 사람 간 공유 |
| ¶3.2 | 시작 "망막만으로는 예측 불가" → 보상 근거 → 부분적·구조적 잔차 → 끝 "그러므로 피질에서 모델링해야" (수미 대응) |
| ¶3.3 | 망막 보정은 손실과 재조직을 분리 못 함 → hV4가 지각에 가장 근접 → 그 기하를 기준으로 망막 입력을 보정 + 전제 명시 |

---

## Intro-4 — 확정안

### 변경 요지

| 항목 | 처리 |
|---|---|
| **T14a** `neither preserves` | **반영** → `neither captures`. 측정치가 구조를 "보존"한다는 표현이 부적절 |
| **T14b** Gap 1 ↔ Gap 2 모순 여부 | **모순 아님으로 정리.** Gap 1 = *HC·집단 수준은 기술됨 / CVD·개인 수준은 미기술*, Gap 2 = *CVD 연구가 쓴 측정치가 크기·정확도*. 대상이 다름. **두괄식 전환으로 문장 순서만으로 대조가 드러나 우려된 인상도 해소** |
| **T15** "MVPA geometry 자체를 본 적 없다" | **반영하지 않음** — Gap 1 첫 문장 및 Intro-3 ¶3.1(`brouwer2009` 기반)과 직접 모순되며 프로젝트 overstatement 금지 정책에 저촉. 대신 **표현만 완화**하여 `remains underinvestigated` 채택 |
| **두괄식 요구** | **반영.** 각 Gap = 첫 문장 결론 + 이후 근거 |
| `We are not aware of...` | 비학술적 부정 표현 → `remains underinvestigated` |
| `which is the trait a tailored correction would have to be built on` | **삭제.** (가리킨 대상은 보상이 아니라 그 개인의 피질 색 기하였음. 다만 그 관련성은 Intro-3 ¶3.3이 이미 진술하므로 반복 불요) |
| Gap 1의 `bannert2018` | **삭제.** object color imagery 연구라 "집단 수준 기하 기술"의 예로 부정확하고, Intro-3 ¶3.3에서 다른 역할로 이미 사용 |
| `Three concrete gaps` | `concrete` 삭제 |
| Gap 3 도입절 | `Across studies that analyze multivoxel color patterns,` 삭제 (Gap 2가 이미 범위를 설정) |

### 확정 문안

> Three gaps remain. \emph{(Gap 1)} **The cortical color geometry of an individual observer with CVD has not been characterized.** The existing descriptions of this geometry come from healthy observers and are reported at the group level~\citep{brouwer2009, kuriki2015}. \emph{(Gap 2)} **The relational structure among colors has not been analyzed in CVD.** fMRI in CVD has quantified response magnitude, including contrast-response gain in anomalous trichromacy~\citep{tregillus2021} and activation in dichromacy and achromatopsia~\citep{rina2024}, and where multivoxel patterns have been analyzed the readout has been classification accuracy. Magnitude indexes signal strength and accuracy indexes category identity, and neither captures the continuous relational structure~\citep{brouwer2013} that a hue-space filter must reshape. \emph{(Gap 3)} **A corrective filter inverted from an individual's own cortical representation remains underinvestigated.** Whether such a signal can be turned into a realizable, individualized correction is untested.

---

## 미해결 결정 사항

| # | 항목 | 선택지 | 상태 |
|---|---|---|---|
| ~~D1~~ | T4 + T7 연동 | (a) 경험적 / (b) 개념 논증 | **(b)로 확정** (Intro-2 협의 시) |
| ~~D2~~ | T14b · T15 | 반영 / 반대 수용 | **해소** (Intro-4 협의 시) — 두괄식 전환으로 T14b 해소, T15는 `remains underinvestigated` 완화로 대체 |
| ~~D3~~ | `emery2021` bib 저자 오류 | 수정 / 유지 | **수정 완료** |

---

## 반대 의견 (기록)

- **T14b** "Gap 1에서 기하를 봤다고 주장할 수 있나" → 모순 아님. Gap 1 = *HC 집단 수준에서는 기술됨, CVD 개인 수준에서는 미기술*. Gap 2 = *CVD 연구가 사용한 측정치가 크기·정확도*. 대상이 다름.
- **T15** "MVPA geometry 자체를 본 적 없다" → 사실과 다름. Brouwer & Heeger 2009가 hV4에서 연속 hue를 재구성함. Gap 3의 유효 형태는 후반부("기하를 역산해 자극-공간 필터로 만든 적이 없다") 하나이며 현행 본문이 이미 그렇게 기술함.
