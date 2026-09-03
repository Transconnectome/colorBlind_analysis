# 분량 조정 — `ImagingNeuro_cha.pdf` 대비 절별 비교와 교체 문안 (2026-09-02)

> **기준 논문**: Kwon et al., *Imaging Neuroscience* 3 (2025), `docs/PAPER/ImagingNeuro_cha.pdf`. 같은 저널의 방법 중심 게재본이며, 내용이 1:1 로 대응하지 않아도 **절별 분량 배분과 보고 방식**의 기준점으로 쓴다. 한 편이므로 규범이 아니라 참조점이다. IN 은 분량 상한을 두지 않으므로 초과가 형식 위반은 아니고, 문제는 리뷰어 부담이다.
>
> **계수 방식**: 본 원고는 `.tex` 에서 주석을 제거한 뒤 캡션을 포함해 센다. 기준 논문은 `pdftotext` 추출본에서 머리글·쪽번호를 제거한 뒤 캡션을 포함해 센다. 이전 회차의 단어 수는 `\%` 를 주석 시작으로 오인해 소폭 과소 계산되어 있었고, 이 문서의 값이 정확하다.
>
> **문체 규칙** (`MANUSCRIPT_EDITS_CONSOLIDATED.md` §0.7-E): 두괄식, 부정 표현 최소화, 세미콜론·콜론·엠대시 미사용, 완충 표현 제거, 직접적이고 엄밀한 동사. 프레이밍은 §0.7 의 기여 진술을 따르며 효능 우위를 주장하지 않는다.

## 0.0 부록 번호 대응표

부록 번호가 세 차례 바뀌었다. 2026-09-02 재편에서 21개가 병합·삭제를 거쳐 17개로 줄었고, 2026-09-03 과 2026-09-04 에 각각 **본문 첫 인용 순서**에 맞추어 전면 재번호했다. 09-04 재번호는 Methods 의 JND 스테어케이스 포인터와 효과크기 참조가 이동하면서 어긋난 두 자리(S17 이 첫째, S7 이 열넷째)를 바로잡은 것이다. 구 번호가 적힌 문서를 읽을 때 이 표를 쓴다. 현행 번호가 기준 열이다.

| 현행 | 절 | 09-03 판 | 09-02 판 | 21개 판 |
|---|---|---|---|---|
| **S1** | Session-1 hue-discrimination thresholds | S17 | S12 | S15 |
| **S2** | Preprocessing pipelines and sensitivity analyses | S1 | S1 | S2 |
| **S3** | ROI coverage | S2 | S2 | S4 |
| **S4** | Dimensionality selection for the SRM | S3 | S4 | S6 |
| **S5** | Comparison with alternative decoders | S4 | S7 | S10 |
| **S6** | Generalized cross-validation for the ridge penalty | S5 | S5 | S7 |
| **S7** | Cross-validation procedures and evaluation metrics | S6 | S6 | S8 + S9 (병합) |
| **S8** | Leave-one-out disparity estimation | S8 | S9 | S12 |
| **S9** | Alignment-independent checks on the disparity measure | S9 | S11 | S14 |
| **S10** | Activation-level comparison | S10 | S3 | S5 |
| **S11** | Comparison with the retinal-family distortion model | S11 | S13 | S16 |
| **S12** | Identifiability checks | S12 | S14 | S18 |
| **S13** | Filter-evaluation session design and comparator | S13 | S15 | S19 |
| **S14** | Effect sizes for single-case comparisons | S7 | S17 | S21 |
| **S15** | Statistical analysis | S14 | S16 | S20 |
| **S16** | Alignment robustness of the within-subject readouts | S15 | S8 | S11 |
| **S17** | Validity of the geometric comparison | S16 | S10 | S13 |

21개 판에서 삭제된 절은 셋이다. S1 Confound Regression(내용은 현행 S2 로 분산), S3 Image Orientation Initialization, S17 HC LOO magnitude-anchor.

**부록 표 번호는 절 순서를 따르므로 09-04 재번호로 다시 이동했다.** 현행 순서는 다음과 같다.

| 표 | 라벨 |
|---|---|
| Table S1 | `tab:jnd_baseline` |
| Table S2 | `tab:staircase_pairs` |
| Table S3 | `tab:motion_arms` |
| Table S4 | `tab:interp_arms` |
| Table S5 | `tab:loro_decoders` |
| Table S6 | `tab:loco_decoders` |
| Table S7 | `tab:disparity_loso` |
| Table S8 | `tab:triangulation` |
| Table S9 | `tab:variance_explained` |
| Table S10 | `tab:modelfits` |
| Table S11 | `tab:fit_stability` |
| Table S12 | `tab:exp2_8afc` |
| Table S13 | `tab:exp2_loro` |
| Table S14 | `tab:exp2_geometry` |
| Table S15 | `tab:effect_sizes` |
| Table S16 | `tab:alignment` |
| Table S17 | `tab:frozen_control` |
| Table S18 | `tab:color_specificity` |

그림은 S1 `figS1_landscape`, S2 `figS2_adjacc_saturation`, S3 `figS3_forward_tuning` 이다. 본문은 표·그림을 전부 `\cref` 경유로 부르므로 손으로 적은 번호는 없다. 다만 `MANUSCRIPT_EDITS_CONSOLIDATED.md` 등 계획 문서에 적힌 `Table S<n>` 는 이 이동을 반영하지 않았다.

## 0. 전체 비교 (2026-09-02 21:10 재계수)

> **⚠ 이 표의 이전 판은 오계수였다.** Methods 6,008 · Results 3,186 · Discussion 1,958 로 적혀 있었으나 실측은 아래와 같다. 계수는 줄 단위로 주석을 제거한 뒤(`^\s*%` 줄 삭제, 이후 이스케이프되지 않은 `%` 뒤 절단) 캡션을 포함해 센다. `sed 's/%.*$//'` 방식은 `2.7\%` 같은 이스케이프 백분율에서 문장을 잘라내므로 쓰지 않는다.

| 절 | Kwon 2025 | 현재 | 캡션 제외 | 비율 |
|---|---|---|---|---|
| Abstract | 210 | 234 | | 1.11 |
| **Introduction** | 730 | 1,252 | 1,252 | **1.72** |
| **Methods** | 3,811 | 6,219 | 5,627 | **1.63** |
| Results | 1,858 | 2,836 | 2,242 | 1.53 |
| **Discussion (+Conclusion)** | 1,303 | **1,406** | 1,406 | **1.08** |
| 본문 합계 | 7,702 | 11,713 | 10,591 | 1.52 |

**Methods 비중은 정상이다.** Kwon 2025 도 Methods 가 본문의 49% 이고 본 원고는 53% 다. 문제는 비중이 아니라 절대 분량이며, 부푼 순서는 **Introduction(1.72) → Methods(1.63) → Results(1.53) → Discussion(1.08)** 이다.

**Discussion 은 총량은 목표 범위에 있으나 Limitations 비중(36%)이 문제다.** 아래 §4 참조.

### 0.1 목표치 (2026-09-03 실측 재검토 후)

| 절 | 현재 (캡션 제외) | 종전 목표 | **개정 목표** | 근거 |
|---|---|---|---|---|
| Introduction | 873 | 800 | 873 (적용 완료) | §1 |
| Methods | 5,627 | 4,900 | **5,200** | §2.4. 조치를 모두 적용해도 5,198 이 하한이다 |
| Results | 2,242 | 1,800 | **1,950** | §3.5. 남은 차이는 보호 문단에서만 나온다 |
| Discussion | 1,406 | 1,530 | **약 1,020** | §4.1·§4.2. Limitations 를 2문단으로 압축(2026-09-04) |
| **본문 합계** | 10,148 | | **약 9,040** | 기준 논문 7,702 의 1.17배 |

종전 목표(4,900 / 1,800)는 항목별 추정치의 합과 맞지 않았고, 실측으로 재계산한 값이 위 표다.

---

## 1. Introduction — 1,252 → 873 단어 (**2026-09-03 본문 적용 완료**)

> **적용됨.** `Introduction/introduction_v2.tex` 를 §1.3 문안으로 교체했고, `Methods/methods_v2.tex:196` 의 `indented` 를 `compressed` 로 통일했다. HEAD 대비 인용 키 29개 동일(누락·추가 0), 본문 세미콜론·엠대시 0, 콜론은 `\label{sec:intro}` 하나뿐이다. Ohkoba 2021 원문 대조는 **여전히 미완**이며 §1.5 (a) 의 조건이 그대로 남아 있다.
>
> **아직 적용하지 않은 것**: §4.4 의 Discussion Limitations 두 문장.

### 1.1 구조 비교

**Kwon 2025** 는 네 동작으로 구성된다. 문제 제기 → 기존 접근 → 그 한계 → 본 연구의 기여. 열거된 gap 목록, 연구 질문 목록, 가설 목록이 **없다.** 기여는 한 문단에서 한 번 진술된다.

**본 원고** 는 14 문단이다.

| 문단 | 단어 | 내용 | 판정 |
|---|---|---|---|
| P1 | 119 | CVD 유병률과 기전 | 유지, 압축 |
| P2 | 49 | 아형 내 개인 간 변이 | P1 에 흡수 |
| P3 | 185 | 현행 교정 = 집단 평균 망막 | 유지, 압축 |
| P4 | 143 | 망막 수준 개인화 선행연구 | 유지 |
| P5 | 103 | 피질 패턴은 정체와 배열을 모두 담는다 | 유지 |
| P6 | 82 | CVD fMRI 가 측정한 것 = magnitude | 유지 |
| P7 | 123 | CVD 는 색의 상대 위치를 바꾼다 | 유지 |
| P8 | 58 | 우리 접근 | **P10·P14 와 삼중 진술** → 병합 |
| P9 | 93 | `Three gaps remain` 열거 | **삭제.** P4·P6·P7 이 각 gap 을 이미 보였다. 인용은 동작 2·3 으로 이관 |
| P10 | 38 | `We ask whether ...` | P8 과 병합 |
| P11 | 56 | 필터가 성립하는 두 조건 | P8 과 병합 |
| P12 | 78 | Describe / Summarize / Correct / Validate 목록 | 산문으로 압축 |
| P13 | 34 | 기대(가설) | **삭제.** P12 와 중복 |
| P14 | 89 | `Together, these steps yield a filter ...` | P8 과 병합 |

**진단**: 문단 1–7(804 단어)은 기준 논문의 동작 1–3 에 해당하고 압축 여지가 있다. **문단 8–14(446 단어)가 문제다.** 기준 논문이 한 문단(약 130 단어)으로 하는 기여 진술을 일곱 문단이 하고 있고, "개인의 피질 표상을 역산한다"가 P8·P10·P14 에 세 번, 질문이 P9(gap)·P12(질문)·P13(가설) 세 형태로 반복된다.

### 1.2 프레이밍 정정 — 분량과 별개로 필수

**P12 항목 4** `Validate. Does the filter move the cortical representation closer to the healthy-control reference than a deployed accessibility filter does?` 는 §0.7 로 철회한 **효능 우위 질문**이다. 답이 "아니오"로 나온 질문을 서론이 제기하면 논문 전체가 실패 보고로 읽힌다. 아래 문안은 평가를 **전향적 개념증명**으로 진술하고 우위 질문을 던지지 않는다.

**P8 문장 3 — 지각 연결 전제. 서론에서 명시적 전제로 세우지 않는다 (2026-09-03 결정).** `Our design adopts the premise that shifting an individual's hV4 color geometry toward that of the healthy controls moves their color perception with it.` 는 전제로 진술되어 허위가 아니다. 그러나 §1.2 가 남긴 숙제("Discussion §3.4 가 이 전제를 신경 결과와 대조하는지 확인할 것")를 실제로 확인한 결과 **대조하지 않는다.** `discussion_v3.tex` 어디에도 이 전제가 다시 등장하지 않고, 결과는 이 전제와 어긋난다. 심리물리 종점은 개선됐으나 신경 기하는 개선되지 않았고 두 종점이 같은 필터 아래에서 따로 움직였다(§Filter evaluation). 검증되지 않았고 결과와도 어긋나는 명제를 서론에서 전제로 선언하면 §0.7 의 방법 논문 프레임과 충돌한다.

두 전제가 서로 다른 일을 하며, 논문이 실제로 이행하는 쪽은 아래쪽이다.

| 전제 | 하는 일 | 본 연구가 검증하는가 |
|---|---|---|
| hV4 기하를 통제군 쪽으로 옮기면 지각이 따라 온다 | 결과를 **지각 교정으로 해석**할 근거 | **아니오** |
| 색은 여전히 디코딩되고 연속 배열만 왜곡된다 | 필터의 **구성 가능성**을 licence 함 | **예. 기여 1 그 자체** |

**조치 세 가지**로 나눈다.

1. hV4 의 지각 대응 성질(`brouwer2009`)은 **hV4 가 처음 쓰이는 자리**, 즉 기여 1 의 `falls to chance at hV4` 에 종속절로 한 번만 붙인다. 종전 문장이 쉼표 앞뒤에서 hV4–지각 연결을 두 번 진술하던 중복이 소멸한다.
2. 지각 연결 명제 자체는 동작 2 의 `the cortical representation that is built from that input **and determines color perception**` 으로 흡수한다. 원문 `introduction_v2.tex:27` 에 있던 절이 압축 과정에서 삭제됐던 것이므로 새 주장을 추가하지 않는다.
3. 검증되지 않았다는 사실은 **Discussion Limitations 에 두 문장으로 명시한다**(§4.5 신설 항목).

### 1.3 교체 문안 (874 단어, 4 동작)

> **실측**: 같은 계수 방식(주석·`\citep` 제거)으로 원문 1,240 → 교체문 892, 절감 348 단어(28%). §1 제목의 목표 800 에는 92 단어 못 미친다. §1.5 의 오류 정정과 절 복원, 문단 종결 문장, 그리고 출처 대조로 추가된 소프트웨어 필터 결과 문장이 분량을 늘렸으며 모두 정확성 사유이므로 되돌리지 않는다. 800 을 맞춰야 한다면 동작 1 둘째 문단의 노치 렌즈 서술(`They change appearance ...`)을 한 문장으로 줄이는 것이 유일하게 안전한 자리다.

> **동작 2·3 의 문단 배정이 종전 판과 다르다.** 구 P4(CVD 피질 = magnitude)와 구 P5(피질이 배열을 담는다)를 맞바꾼다. 사유는 §1.5 를 볼 것.

**동작 1 — 문제** (P1 + P2 + P3)

> Color vision deficiency (CVD) affects approximately 8\% of men and 0.4\% of women of European ancestry~\citep{birch2012}. It arises from an X-linked opsin polymorphism that shifts the peak spectral sensitivity of the L- or M-cone photopigment toward the other, narrowing the separation between the two peaks from roughly 27~nm in normal trichromacy to between 1 and 12~nm in anomalous trichromacy~\citep{deeb2005, neitz2011, bosten2019}. The narrowed separation attenuates the L--M cone-opponent signal without abolishing it, and the two red--green subtypes, protan and deutan, differ in which of the two pigments is altered~\citep{neitz2011}. Anomalous trichromats show reduced red--green discrimination, frequent category confusions, and elevated just-noticeable differences along the L--M axis. Within one subtype the severity of these signs extends from near-normal to near-dichromatic~\citep{bosten2019, neitz2011}.
>
> Correction does not follow that variation. It is calibrated to a population-average retina and applies one transform to every user. Notch lenses attenuate the spectral band where L and M cones overlap~\citep{alvaro2022, gomezrobledo2018}. They change appearance, with colors looking more saturated along the red--green axis, while discrimination thresholds move minimally and diagnostic classification stays unchanged~\citep{somers2024, gomezrobledo2018, alvaro2022}. Software filters forward-project a stimulus onto a deficient retina by the Brettel--Vi\'enot--Mollon construction or the Machado model, both built on standard-observer cone fundamentals~\citep{brettel1997, machado2009}. Daltonization then inverts that projection and recolors the image, carrying the lost red--green differences toward the blue end of the spectrum~\citep{fidaner2005}. In a visual-search evaluation of four such methods the benefit appeared on Ishihara plates for every method and on natural images for one~\citep{simonliedtke2016}. Across 51 individuals with red--green CVD, between-observer variation in the threshold shift exceeded the mean effect for both of two commercial lenses~\citep{patterson2022}, so a fixed transform shifts thresholds inconsistently across users.

**동작 2 — 개인화는 망막에서 이루어졌고, 필요한 것은 피질 표상이다** (P4 + 구 P5)

> Individualized correction has been implemented at the retinal level, by tuning a cone-shift parameter to a user's responses on plate or matching tests, or by estimating it from genotype or measured cone sensitivities~\citep{deeb2005, stockman2000}. Discrimination follows that parameter only loosely. Some anomalous trichromats with very small spectral separations discriminate better than their separation predicts~\citep{neitz2011}, and across observers the correlation between separation and discrimination is weaker than expected~\citep{bosten2019}. One evaluation of these lenses argues that even a spectral filter customized to an individual observer would redistribute confusions rather than remove them~\citep{gomezrobledo2018}. A retinal parameter fixes the input to the visual system and leaves undescribed the cortical representation that is built from that input and determines color perception.
>
> Cortical activity patterns specify both which color was seen and where that color lies among the others. Cortical color processing is distributed and hierarchical~\citep{gegenfurtner2003, shapley2011, conway2018}. In V1 perceptual hues form spatially clustered response patterns~\citep{parkes2009} and responses are selective for hues between the cone-opponent axes~\citep{kuriki2015}. In hV4 a hue withheld from training can be reconstructed from the responses to its neighbors, an interpolation across the hue circle~\citep{brouwer2009}. The relative positions of colors in these patterns constitute a geometry, and a color can be identified in one observer from the patterns of others~\citep{bannert2025}. Existing descriptions of this geometry come from healthy observers~\citep{brouwer2009, brouwer2013, kuriki2015}.

**동작 3 — CVD 에서 측정된 것은 신호의 크기이고, 배열 변화는 심리물리에만 있다** (구 P4 + P7 + P9 의 인용)

> What has been measured in CVD is the strength of the color signal. Anomalous trichromats perceive more red--green contrast than a cone-sensitivity account predicts~\citep{boehm2014}, deutan observers adapt to chromatic contrast more than the same account predicts~\citep{basim2025}, and both results fit a post-receptoral gain that magnifies the weakened L--M signal~\citep{webster2015}. In V1 color responses are weaker in anomalous than in normal trichromats, and in ventral V2 and V3 the two groups are indistinguishable~\citep{tregillus2021}. Activation has been reported in three observers, one with dichromacy and two with achromatopsia~\citep{rina2024}. Each of these measures how strongly a region responds, not where the colors lie relative to one another.
>
> Psychophysics shows where colors lie relative to one another in CVD. Anomalous trichromats describe stimuli with all four hue primaries, but each primary lands on a different stimulus than in normal trichromats~\citep{emery2021}. Difference judgments by dichromats yield a map with one axis where normal trichromats have two~\citep{saysani2018}. Judgments by protan and deutan observers yield a map whose red--green distances collapse while its yellow--blue distances are preserved, and three of twenty such observers were indistinguishable from normal trichromats~\citep{ohkoba2021}. All of this evidence comes from judgments rather than from the cortical response. Corrections individualized on that basis invert the map those judgments yield~\citep{ohkoba2021}.

**동작 4 — 기여** (P8 + P10 + P11 + P12 + P14. P9·P13 삭제)

> Here we recover that map from an individual's cortical response instead and invert it into a correction on the stimulus, with the healthy-control geometry as the target. A stimulus-space filter is constructible under two conditions. The displayed colors must remain decodable from the cortical response, which gives the filter a signal to act on. Their continuous arrangement must be distorted, which leaves something to correct. We characterize two adults with CVD, one deutan and one protan, against seven healthy controls, and report two contributions. First, categorical identification of the eight displayed hues is preserved in both participants while interpolation across the hue circle falls to chance at hV4, the region where the arrangement of responses follows perceptual color space~\citep{brouwer2009}. Second, we model each participant's departure from the control geometry with two interpretable parameters, invert them into a stimulus-space filter for that participant, and evaluate the filters in a prospective session of fMRI and psychophysics. To our knowledge this is the first correction filter derived from an individual's cortical representation. With two participants the evaluation is a proof of concept, and it tests the feasibility of the inversion rather than the superiority of a per-person correction over a subtype-average one.

### 1.4 점검

| 항목 | 상태 |
|---|---|
| 인용 보존 | 원문 29개 키 전부 유지, 신규 키 0. 스크립트로 대조 완료 (2026-09-03) |
| §0.5 금지 표현 | `individual-specific`, `localized to`, 우위 주장 없음 |
| `first` 스코프 | 절차에 한정. `To our knowledge` 헤지. 효능 불포함 |
| 문체 | 세미콜론·콜론·엠대시 0. `rather than` 2회는 대조가 실질이라 유지 |
| 제목·초록 정합 | Results 소절 제목의 `falls to chance at hV4` 와 같은 표현 |
| 대명사 | `those judgments`·`the distortion` 등 선행사 불명 대명사 0 |

**적용 시 확인 (2026-09-03 완료).** `sec:intro` 는 원고 어디에서도 `\ref` 되지 않고, 서론 `enumerate` 에는 `\label` 이 없다. 교체 시 깨지는 상호참조가 없다.

### 1.5 어휘·논리 수정 사유 (2026-09-03 사용자 검토 반영)

#### (a) `dent` → `compressed` — 종전 문안의 표현을 폐기한다

의미는 "움푹 팬 자국"이고 MDS 배치가 yellow·purple-blue 근처에서 안쪽으로 들어간 형태를 가리킨다. **엄밀한 학술 어휘가 아니며 네 가지 문제가 있다.**

1. **측정량을 지정하지 않는다.** 어느 방향으로 얼마나 들어갔는지 말하지 않으면서 바로 다음에 `the dent varies more than tenfold` 라며 스칼라로 취급한다. 정의되지 않은 양의 10배 변동을 보고하는 셈이다.
2. **원고 내부에서 어휘가 갈린다.** Introduction 은 `dented`, `methods_v2.tex:196` 은 `indented` 다. Methods 쪽은 그 진술을 $\beta_s \geq 0$ 사전제약의 **유일한 경험적 근거**로 쓰므로, 근거 문장의 용어가 흔들리면 제약의 정당화도 흔들린다.
3. **교체 문안에서 주어가 잘못 붙었다.** `Judgments ... dent the map` 은 판단이 지도를 찌그러뜨린다는 뜻인데, 판단은 지도를 복원하는 재료이지 변형시키는 행위자가 아니다. 원문의 수동형(`the map ... is dented`)에는 없던 오류다.
4. §0.7-E 의 "직접적이고 엄밀한 동사" 규칙에 어긋난다.

**원문 대조 완료 (Wiley Open Access, 전문·표·그림).** `compressed` 도 채택할 수 없다. 저자들이 쓰는 표현은 `concave shape bending at Y and PB`, 곧 **C자 형태**이고, 정량 지표는 원형으로부터의 왜곡도 `distortion index` 다. `indented` 는 이 논문에서 **정상 색각자** 배치도의 국소 불규칙성을 가리키는 말이다.

**용어보다 기하 주장이 더 문제였다.** Ohkoba 모형은 y/b 이득을 모든 관찰자에게 1로 **고정**하고 r/g 이득만 자유로 두어 정상 4.33 에서 protan 1.51, deutan 0.84 로 감소시킨다. MDS 에서 Y 와 PB 는 가장 멀리 떨어진 두 점이 되어 제1축으로 승격되고 R 과 G 가 뭉친다. 저자 진술도 `shorter distance between reddish and greenish stimuli relative to that between yellowish and bluish stimuli` 다. C자 오목함은 축 왜곡이 아니라 판단 단계의 포화 비선형에서 나오며, 선형 모형만으로는 재현되지 않았다고 저자들이 밝힌다. 따라서 Y 와 PB 는 함몰점이 아니라 아치의 양 끝 꼭짓점이고, 대안으로 검토했던 `contracted toward the centre` 도 틀렸다.

**채택**: `a map whose red--green distances collapse while its yellow--blue distances are preserved`. 축 특이적 거리 변화라는 실제 소견을 그대로 쓴다. 이는 저희 적합 결과와도 일치한다. 두 참가자 모두 혼동축 항이 지배적이고 S-cone 항은 회복 불확도 아래다.

**개인 간 변이 수치.** `varies more than tenfold` 는 저자 문장이 아니라 Table 3 에서 도출한 값이고 high chroma 조건에서만 성립한다(11.1× / 11.0×, medium chroma 는 6.4× / 8.5×). DI 는 바닥값이 1인 지수라 비율 해석도 왜곡된다. 따라서 삭제한다. 대신 논문이 수를 명시해 진술하는 `20명 중 3명이 정상 색각자와 유사한 배치` 를 쓴다. DI 가 0이 되는 것이 아니라 정상 범위에 드는 것이므로 `absent` 대신 `indistinguishable from normal trichromats` 로 적는다.

**🔴 Methods 로 이월되는 사안.** `methods_v2.tex:196` 은 $\beta_s \geq 0$ 을 `the perceptual hue circle ... being compressed at yellow and purple-blue, the two ends of the S-cone axis` 로 정당화하며 이 인용이 유일한 경험적 근거다. Ohkoba 는 이를 지지하지 않고 구조적으로 반대를 지지한다. 그 모형에서 감소하는 자유 이득은 혼동축에 있고 S-cone 축에는 자유 파라미터가 없다. 선택지는 셋이다. (A) 다른 근거 탐색, (B) 경험적 주장을 걷고 식별가능성 규약으로 재서술, (C) 제약 재검토 후 재적합. **B 를 권한다.** $\beta_s\cos(\theta-90^\circ)$ 의 부호 반전은 축 방향을 180° 돌리는 것과 같으므로 $\beta_s \geq 0$ 은 부호 축퇴를 제거하는 규약으로 읽을 수 있고, 원고는 이미 그 진폭을 추정하지 않는다고 진술한다. 이 결정은 분량 조정 범위 밖이므로 별도 승인이 필요하다.

#### (b) `those judgments` — 대명사 제거

`the one individualized filter built from color judgments inverts those judgments` 에서 `those judgments` 는 문법적으로 같은 문장의 `color judgments` 를 가리키므로 "색 판단으로 만든 필터가 그 색 판단을 역산한다"는 동어반복이 된다. 의도한 대비는 **판단에서 복원한 지도 대 피질 측정**인데 그 대비가 문장에 없다. 부수적으로 `the one individualized filter` 는 그런 필터가 하나뿐이라는 개수 주장으로 읽힌다. 교체문은 대명사를 없애고 `invert a map recovered from an observer's own color judgments rather than a measurement of the cortex` 로 대비를 문장의 골자로 만든다.

#### (c) 압축 중 발생한 사실관계 오류 1건

종전 교체 문안 P1: `a shift in the spectral sensitivity of the L- or M-cone photopigment, **which** X-linked opsin polymorphisms narrow from roughly 27~nm to between 1 and 12~nm`.

`narrow` 가 타동사이고 `which` 가 목적어, `polymorphisms` 가 주어이므로 선행사가 **spectral sensitivity** 인지 **photopigment** 인지 갈리고, `narrow` 의 자동사 용법 탓에 `polymorphisms` 자체가 줄어든다는 오독까지 유발한다. **그리고 셋 다 틀렸다.** 27 nm → 1–12 nm 로 좁아지는 것은 감도도 색소도 아니라 **두 색소 정점 사이의 간격**인데 그 명사가 문장에 없다. 올바른 읽기가 존재하지 않으므로 모호성이 아니라 사실관계 오류다. 원문 `introduction_v2.tex:18`(`The two pigments lie between 1 and 12~nm apart ...`)은 정확했고 압축하면서 지시 대상이 틀어졌다.

교체 문안은 `narrow ... from ... to ...` 구문을 되살리되 주어를 이동 사건으로, 목적어를 `the separation between the two peaks` 로 명시한다. `toward the other` 는 이동이 왜 간격 축소로 이어지는지를 밝히고, 이로써 다음 문장의 `The narrowed separation` 도 선행사를 얻는다.

#### (d) 압축 중 소실된 load-bearing 절 3건 — 복원

| 소실된 절 | 결과 | 복원 위치 |
|---|---|---|
| `without abolishing it` | L−M 신호가 남는다는 진술이 사라져, 디코딩 가능성 조건의 생리적 근거가 없어진다 | 동작 1 P1 |
| `the severity of **these signs**` 의 선행사(변별 저하·범주 혼동·JND 상승) | `the severity` 가 무엇의 심각도인지 지시 대상이 없다 | 동작 1 P1 |
| `and determines color perception` | 피질 표상이 왜 중요한지가 진술되지 않은 채 gap 만 남는다 | 동작 2 P1 (§1.2 조치 2) |

#### (e) 문단 순서 — 구 P4 ↔ 구 P5 교환

종전 순서는 **CVD 피질 연구가 magnitude 만 쟀다**를 **피질이 배열을 담는다**보다 먼저 놓았다. 그런데 앞의 것이 결함으로 읽히려면 잴 수 있는 다른 것, 곧 배열이 있다는 사실을 독자가 이미 알아야 한다. 순서를 바꾸면 각 문단의 gap 이 그 gap 을 이해할 재료가 제시된 뒤에 등장한다. 이에 따라 동작 2·3 의 제목도 다시 붙였다.

#### (f) 문단 종결 문장 2건 신설

기준 논문은 문단을 해석 한 문장으로 닫는다(§3.2 e 가 Results 에 적용한 규칙과 같다). 종전 문안의 동작 1 둘째 문단은 소프트웨어 필터 서술로, 구 P4 는 `rina2024` 인용으로 끝났다. 각각 마무리 문장을 넣고 그 문장이 다음 문단으로 넘어가는 다리를 겸하게 했다.

#### (g) 수정 후 문단 연결 사슬

| 앞 문단 끝 | 뒤 문단 첫 문장 | 연결 |
|---|---|---|
| `near-normal to near-dichromatic` | `Correction does not follow that variation.` | 개인 변이 ↔ 단일 변환 |
| `not predictable from the group mean` | `Individualized correction has been implemented at the retinal level` | 고정 변환 → 개인화 |
| `the cortical representation ... determines color perception` | `Cortical activity patterns specify both ...` | 피질 표상 → 피질 패턴 |
| `come from healthy observers` | `What has been measured in CVD is ...` | 통제군 → CVD |
| `not where the colors lie relative to one another` | `Psychophysics shows where colors lie relative to one another in CVD.` | 어휘 반복 |
| `rather than a measurement of the cortex` | `Here we take an individual's own cortical color representation ...` | 명시적 대조 |

#### (h) 두 조건 문장을 세 문장으로 분할

종전 문안은 `A stimulus-space filter is constructible under two conditions, that ..., and that ...` 로 `that` 절 두 개를 한 문장에 담았고, 각 절이 다시 `so that` 목적절을 달아 한 문장에 종속절이 넷이었다. 조건을 제시하는 문장이 조건 자체보다 읽기 어려워지므로 세 문장으로 나눈다. 원문 `introduction_v2.tex:50` 도 원래 분할된 형태였다.

> A stimulus-space filter is constructible under two conditions. The displayed colors must remain decodable from the cortical response, which gives the filter a signal to act on. Their continuous arrangement must be distorted, which leaves something to correct.

셋째 문장의 `Their` 가 `the displayed colors` 를 받으므로 `of hues` 반복이 사라진다.

#### (i) 용어 심기

기여 1 의 `interpolation across the hue circle` 는 종전 문안에서 그 자리에 처음 등장했다. 동작 2 의 `brouwer2009` 문장에 `an interpolation across the hue circle` 를 붙여 용어를 미리 심었다. 마찬가지로 종전 기여 2 의 `the distortion` 은 기여 1 이 도입한 적 없는 구성물을 정관사로 받았으므로 `each participant's departure from the control geometry` 로 바꿨다.

---

## 2. Methods — 6,219 (캡션 제외 **5,627** 실측) → 목표 **약 5,200** (2026-09-03 하향 조정, §2.4)

### 2.1 보고 방식 비교

| | Kwon 2025 | 본 원고 |
|---|---|---|
| 단어 (캡션 제외) | 3,811 | 5,679 |
| 제목 단위 수 | 11 (`2.1` … `2.6`, 최대 `2.1.1.3`) | **35** (subsection 16 + paragraph 19) |
| 단위당 평균 | 약 350 단어 | **약 155 단어** |
| 60 단어 미만 단위 | 0 | **9** |
| 오버뷰 문단 | 없음 | 있음 (133 단어) |
| 통계 절차 | Methods 끝 한 절(`2.6`)에 일원화 | **분산.** Methods 본문·Results 캡션(`:67`, `:170`)·S20·S21 |
| 수식 | 4 | 4 |
| Methods 안의 표 | 0 | 0 |
| 주어 | `We [동사]` 능동 | 수동·능동 혼재 |

**진단**: 본 원고의 Methods 는 기준 논문보다 **단위가 두 배 이상 잘게 쪼개져** 있다. 60 단어 미만 문단이 아홉 개이고, 그중 `Identifiability and recovery` 는 소절 본문이 15 단어에 그친 채 하위 문단 넷으로 갈라진다.

**진단 정정 (2026-09-03).** 종전 판의 "단일사례 검정의 정의가 Methods 에 없다"는 현행 원고와 맞지 않는다. `crawford1998` 은 현행 `methods_v2.tex` 에 **5회** 등장한다 (`:38` participants, `:136` LORO 양측, `:147` LOCO 단측 하방, `:150` vulnerability 단측 무보정, `:159` disparity 단측 상방). 결함은 부재가 아니라 **산재**다. 검정의 방향이 소절마다 제각기 선언되고, $d_{cc}$ 공식·순열 횟수·BH 적용 범위·Wilson 구간이 Methods 여러 곳과 §S15·S17 에 나뉘어 있다. 따라서 신설 절의 역할은 정의 추가가 아니라 **일원화**이고, 산재한 문장들은 포인터로 줄인다.

### 2.2 조치

#### (a) 단위 병합 — 35 → 약 20

| 현재 | 단어 | 조치 |
|---|---|---|
| `Parameter selection` 본문 + Gate 1 · 2 · 3 | 43 + 33 + 55 + 205 | **한 문단**으로. 세 관문을 문장 단위로 잇는다 |
| `Identifiability and recovery` 본문 + Parameter recovery · Origin-recovery null · HC pseudo-CVD · Color-label permutation | 15 + 135 + 47 + 38 + 80 | **두 문단**으로. 회복 시뮬레이션 하나, 귀무 검정 셋 하나. **§S12 로 옮기지 않는다** (§4.10 c 철회) |
| `Forward encoding model` 본문 + Decoding · Encoding | 94 + 91 + 86 | 소절 본문에 흡수. 두 추정량의 차이는 한 문장이면 된다 |
| `Two decoding schemes` 서두 | 88 | 삭제. LORO·LOCO 문단이 각자 첫 문장에서 목적을 말한다 |
| `hV4 LOCO voxel-prediction` | 41 | `Composite loss` 첫머리에 한 문장으로 흡수 |
| 오버뷰 문단 | 133 | 존치 (이전 결정). 다만 Figure 1C 와 단계 명칭을 맞춘다 |

예상 절감 약 250 단어. 소제목이 줄면 각 소절이 기준 논문처럼 200–400 단어 단위가 된다.

#### (b) 통계 절 신설 — `\subsection{Statistical analysis}` (`Filter evaluation` 뒤 · `Reproducibility` 앞, 약 145 단어)

**종전 초안을 폐기한다 (2026-09-03 원고 대조).** 세 가지가 원고와 어긋났다.

1. `Crawford--Garthwaite interval` — **원고 어디에도 없다** (`Garthwaite` 검색 0건). §S14 은 $d_{cc} = t\sqrt{8/7}$ 만 정의한다. 계산한 적 없는 구간을 보고한다고 주장하게 되므로 삭제한다. 인용도 잘못이었다. 그 구간의 출처는 `crawford1998` 이 아니다.
2. `one-tailed in the direction of a deficit` 의 전칭 — LORO 는 보존 가설이라 **양측**이다 (`methods_v2.tex:136`). 예외를 인정하는 형태로 고치고, 방향 선언 자체는 가설이 정의된 소절에 남긴다.
3. `Every neural endpoint was computed under both preprocessing pipelines of \S\ref{sec:methods:mri} (Supplementary~\S S15)` — 같은 진술이 `:73` 에 이미 있고 파이프라인의 소관 부록은 §S2 이다. 중복이므로 넣지 않는다. 대칭 LOSO 추정량 문장도 §rdm `:163` 이 이미 담으므로 넣지 않는다.

교체 초안은 다음이다. exp2 의 Cohen's $d$ 보고 문장은 §2.3(G) 둘째 문단이 설계 특이적 사유와 함께 유지하므로 여기 넣지 않는다.

> \subsection{Statistical analysis}
> \label{sec:methods:stats}
>
> Single-case comparisons of a CVD participant against the seven controls used the Crawford--Howell modified $t$ with $df = 6$ \parencite{crawford1998}, one-tailed toward a deficit unless a subsection states otherwise, and are reported with the case-control effect size $d_{cc} = t\sqrt{8/7}$ (Supplementary~\S S14). Control-level interpolation was tested against an empirical null of $1{,}000$ within-participant color-label permutations, and group HC--CVD comparisons against $10{,}000$ subject-label permutations \parencite{nichols2002}. Families of related tests were corrected by the Benjamini--Hochberg procedure at $\alpha = 0.05$, applied to the six identifiability tests of \S\ref{sec:methods:identifiability} and to the participant-by-region grids of the supplementary color-correspondence analysis. Identification accuracy carries Wilson score intervals over the $n = 64$ trials of each condition, and group effect sizes are reported as Hedges' $g$. Full definitions appear in Supplementary~\S S15 and \S S14.

**신설에 딸려 나가는 정리 3건.**

| 위치 | 조치 |
|---|---|
| `:150` vulnerability 의 $d_{cc}$ 공식 문장 | `Effect sizes are reported as the case-control index $d_{cc}$ (\S\ref{sec:methods:stats})` 로 축약 |
| Reproducibility(스테이징판)의 `The correction families, the single-case test, and the permutation counts used throughout are collected in Supplementary~\S S15.` | 신설 절 말미의 포인터와 중복이므로 삭제 |
| 각 소절의 검정 방향 선언 (`:136` 양측과 그 사유, `:147` 하방, `:159` 상방) | **존치.** 방향은 가설에 붙는 정보이므로 검정이 정의된 자리에 남긴다 |

#### (c) 심리물리 JND 문단 (355 단어)

스테어케이스 파라미터(초기 간격, 단계 규칙, 수렴 기준, 트랙 수)는 §4.6b 가 신설한 §S1 쌍별 스테어케이스 표로 옮기고, 본문은 과제 구조와 산출 지표만 남긴다. 예상 절감 약 120 단어.

#### (d) `Filter evaluation` (239 단어) ↔ §S13

§S13 가 설계(4 런, ABBA 상쇄, macOS 비교자)를 이미 서술한다. Methods 는 조건 구성과 종점만 남기고 설계 상세는 §S13 를 가리킨다. 예상 절감 약 80 단어.

#### (e) 손대지 않는 것

`MRI acquisition and preprocessing`(433)은 COBIDAS 필수 보고이고 §1.5 로 이미 정리됐다. `Inverse fitting`(716)은 §4.10(c-2) 로 이미 정리됐다. `Cortical distortion model`(241)은 기여의 핵심이다.

### 2.3 교체 문안

> 아래 문안은 `Methods/methods_v2.tex` 의 현행 본문을 실측(주석 제거·캡션 제외)한 뒤 작성했다. 각 항목의 단어 수는 §2.4 의 표에 정리되어 있다.

#### (A) `Forward encoding model` — 소절 본문 + `Decoding` + `Encoding` 을 한 문단으로 (264 → 약 215)

두 추정량이 갈라지는 지점은 "무엇을 최적화하는가" 하나뿐이므로, 문단 제목 둘을 없애고 그 대비를 문장 안에서 처리한다.

> \subsection{Forward encoding model}
> \label{sec:methods:encoding}
>
> Both classification (LORO) and interpolation (LOCO) decoding used the same forward encoding model~\parencite{brouwer2009}. The model represents each stimulus as a $F = 6$-dimensional channel vector $\mathbf{c}(\theta) = [c_1(\theta), \ldots, c_F(\theta)]^\top$, where $c_k(\theta) = \max\!\bigl(0,\,\cos(\theta - \theta_k)\bigr)^2$ is a half-wave rectified squared cosine tuned to preferred hue $\theta_k$, with preferred hues spaced equally at $60^\circ$. Stacking the eight stimulus channel vectors row-wise gives the channel design matrix $C \in \mathbb{R}^{8 \times F}$. Decoding and encoding optimize different targets and therefore estimate the channel-to-voxel weight matrix $W \in \mathbb{R}^{F \times V}$ differently. Decoding recovers the stimulus hue from voxel responses, so we estimated $W$ by the ordinary least-squares pseudoinverse of $C$, reconstructed channel activations for a held-out voxel pattern $\mathbf{x}$ as $\hat{\mathbf{c}} = W\mathbf{x}$, and read out the hue angle, among all 360 integer angles, whose basis vector correlated most strongly with $\hat{\mathbf{c}}$ (\citealp{brouwer2009}; Figure~\ref{fig:forward}). Eight-way classification assigned that angle to the nearest of the eight stimulus hues, and five alternative decoders are compared in Supplementary~\S S5. Encoding predicts the voxel responses as $\hat{X} = CW$ with $\hat{X} \in \mathbb{R}^{8 \times V}$, so we estimated $W$ by ridge regression under a single penalty $\alpha$ chosen for each fit by generalized cross-validation over the voxels of the ROI~\parencite{golub1979} (Supplementary~\S S6). Regularization is warranted because the few stimuli and the correlated basis channels would otherwise overfit $W$ and degrade prediction of held-out responses~\parencite{kay2008,naselaris2011}, and this ridge prior is isotropic and imposes no spatial structure on the voxels.

#### (B) `Two decoding schemes` 서두 — 삭제가 아니라 축약 (112 → 약 45)

**§2.2(a) 의 "삭제" 판정을 정정한다.** 이 서두에는 LORO·LOCO 문단이 반복하는 목적 진술 외에, 다른 곳에 없는 정보가 둘 있다. 두 도식이 모두 Procrustes 정렬 진폭 위에서 계산된다는 사실과, 폴드 구성·누출 통제·지표 정의를 §S7 이 담는다는 포인터다. 서두를 통째로 지우면 이 둘이 사라지므로 두 문장만 남긴다.

> Two cross-validation schemes applied the forward encoding model, both computed on the Procrustes-aligned amplitudes of \S\ref{sec:methods:roi}. Fold construction, the leakage control on the run-level alignment, the cross-subject scheme, and the decoding and voxel-prediction metrics are given in Supplementary~\S S7.

**보강 (2026-09-03 검수).** 서두가 담고 있던 개념 문장, 곧 모든 색이 훈련에 남으면 **범주** 표상을 재고 색 하나가 훈련에서 빠지면 **연속** 표상을 잰다는 대응은, 현행 LORO·LOCO 문단 어디에도 없어 서두 축약과 함께 원고에서 사라진다. 이 대응은 기여 1 의 해리를 정의하는 골격이므로 두 문단의 첫 문장으로 이관한다.

> Color classification was assessed by leave-one-run-out (LORO) cross-validation, in which every hue remains in the training set, so the scheme tests the categorical representation of the eight hues.

> Continuous hue interpolation was assessed by leave-one-color-out (LOCO) cross-validation, in which the held-out hue never appears in training.

#### (C) `Parameter selection` — 본문 + Gate 1–3 을 한 문단으로 (348 → 약 305, 4단위 → 2문단)

현행 `Gate 3` 문단은 순위 규칙(약 100 단어)과 "순위에 들어가지 않는 기록 항목"(약 115 단어)이라는 서로 다른 두 주제를 담고 있다. 셋을 한 문단으로 잇되, 뒤쪽 절반은 별도 문단으로 유지한다.

> \subsection{Parameter selection}
> \label{sec:methods:selection}
>
> Per-subject loss combinations and model class were selected by a pre-specified three-gate procedure, with inputs from two resampling schemes over the seven HC references, a 5-train/2-test resample repeated $N = 300$ times and a strict 7-fold leave-one-HC-out, both using the same loss atoms. Gate 1 set a separation precondition, admitting an atom only when its CVD loss value differed from the HC leave-one-out distribution by a Cohen's $d$ of magnitude $0.5$ or greater in either direction. Gate 2 rejected admitted combinations in which at least half of the resample solutions saturated the grid boundary, since boundary saturation indicates model misspecification. It also rejected combinations whose recovered parameters collapsed across resamples, defined as an interquartile range above $50^\circ$ or a sign reversal between the training and test argmin exceeding $5^\circ$. Gate 3 ranked the surviving combinations by the median composite test-loss $\overline{L}_{\rm test}$ over the $N = 300$ resamples, evaluated for each resample at the training argmin on the two held-out HC and z-normalized relative to the training grid, so that a lower value indicates generalization to unseen HC references. Ties were broken by the test-loss interquartile range, which measures the stability of that generalization estimate, and these two quantities were the only ranking criteria.
>
> (이하 `Further quantities were recorded for each candidate outside the ranking ...` 문단은 현행 그대로 유지한다.)

#### (D) `Identifiability and recovery` — 5단위 → 2문단 (313 → 약 270)

첫 문단은 회복 시뮬레이션(회복 검정 + 원점 귀무)을 담고, 둘째 문단은 나머지 두 귀무 검정과 FDR 보정을 담는다. **§S12 로 옮기지 않는다**(§4.10 c 철회 유지).

> \subsection{Identifiability and recovery}
> \label{sec:methods:identifiability}
>
> Four pre-specified checks were run on the loss combination selected for each participant in \S\ref{sec:methods:selection}, hereafter that participant's production candidate. The checks bound what the fit can estimate and entered no selection decision. They appear in Supplementary~\S S12 as Tests 1, 2a, 2b, and 2c, in that order. The first establishes whether a known distortion can be recovered at the present sample size and noise level. Synthetic CVD responses were generated at a known ground truth by passing that distortion through each HC participant's encoder, with noise matched to that participant's residual structure through the top 20 principal components of its spatial covariance and an AR(1) correlation of $0.3$ across runs. Re-running the grid fit on each synthetic dataset gave $n = 140$ refits per candidate, from seven HC encoders and twenty noise realizations. Recovery was summarized by $f_{10^\circ}$, the fraction of refits within $10^\circ$ of ground truth on both axes, against a pass criterion of $f_{10^\circ} \geq 0.5$ with $|\text{bias}| < 10^\circ$. The refit repeats the grid search rather than the full selection procedure, so it measures recoverability at a fixed loss combination. The second, an origin-recovery null, runs the same synthesis with ground truth at $(0^\circ, 0^\circ)$ and each HC participant's real JND. The spread it returns when no distortion is present sets the per-axis uncertainty floor. It yields no $p$-value and was excluded from the test pool.
>
> The third and fourth ask what the estimate depends on. Substituting each HC participant's real amplitudes into the CVD slot in turn asks whether a control placed in the CVD position yields a comparable estimate, and gives a seven-member null with a one-sided rank-distance percentile. Permuting the eight color labels of the real CVD amplitudes $N = 1000$ times, with the same permutation applied across ROIs and the HC pool left unchanged, asks whether the estimate depends on which color evoked which response, and gives a one-sided $p_{\rm perm}$. The three test-bearing checks across the two production candidates gave six tests, corrected together under the Benjamini--Hochberg false-discovery rate ($\alpha = 0.05$). Outcomes are summarized in \S\ref{sec:results:twocomp} and reported in full in Supplementary~\S S12.

#### (E) `hV4 LOCO voxel-prediction` — `Composite loss` 첫머리로 흡수 (121 → 약 110)

> \paragraph{Composite loss.}
> A third atom, $L_{\rm LOCO}$, scored how well a candidate distortion accounted for the CVD participant's own held-out responses at hV4. It was available to every candidate objective, is defined in Supplementary~\S S12, and the selection procedure admitted it in neither participant. The atoms differ in scale, since $L_\gamma$ is built from threshold ratios while $L_{\rm RDM}$ and $L_{\rm LOCO}$ are bounded dissimilarities. Each atom was therefore evaluated over the full parameter grid and standardized to zero mean and unit standard deviation across that grid. Standardization equalizes the spread of the atoms over the grid and leaves the composite invariant to rescaling an individual atom by a positive constant. The composite loss is the sum of the standardized atoms divided by $\sqrt{n_a}$, where $n_a$ is the number of atoms.

#### (F) JND 문단 — 스테어게이스 상세를 §S1 로 (350 → 약 265)

**이관 대상 표는 이미 존재한다**: `tab:staircase_pairs`(`supplementary.tex:522`). 시작 수준·단계 크기·종료 규칙·트랙 수를 그 표의 각주 또는 표 앞 문단으로 옮기고, 본문은 과제 구조와 산출 지표만 남긴다.

> \paragraph{Just-noticeable difference (JND).}
> On each trial two chromatic discs appeared simultaneously to the left and right of fixation, and participants judged whether the two were the same or different. Each disc had a radius of 96 pixels in a $1024 \times 768$ window, their centers were separated by 260 pixels, and their positions were randomized across trials. A fixation cross preceded each trial for 0.5\,s, and the discs remained on screen until the participant responded. The two hues were separated by a fraction $t$ of the pair's full separation, interpolated in CIE $LCh$, and $t$ served as the level of two interleaved 1-up/1-down staircases converging on the level that yields $50\%$ ``different'' responses~\parencite{levitt1971}. The threshold was the mean of the last six reversal levels. Starting levels, step sizes, and termination rules are given in Supplementary~\S S1. Because the two discs always differed, no same trials were included, and the threshold may therefore reflect response bias as well as perceptual sensitivity.

(뒤따르는 pair-selection 문단은 현행 그대로 유지한다. 여덟 쌍의 선정 근거는 §0.7 의 2성분 모형과 직접 맞물리므로 축약 대상이 아니다.)

**§S1 삽입 문안 (2026-09-03 보강 — 없으면 정보가 소실된다).** 위 문안은 시작 수준·단계 크기·종료 규칙을 §S1 로 "옮긴다"고 하였으나 삽입할 문안이 없었다. 이대로 적용하면 그 파라미터들이 원고 전체에서 사라진다. §S1 첫 문단 뒤에 다음을 삽입한다 (약 65 단어).

> Each pair was measured by two interleaved staircases from starting levels $t = 0.8$ and $t = 0.5$, both following a 1-up/1-down rule with a step of $0.15$ until the second reversal and $0.03$ thereafter. A staircase terminated at eight reversals and at least 20 trials, extended by two further reversals whenever the SD of the last six reversal levels exceeded $0.10$.

#### (G) `Filter evaluation` — 설계 상세를 §S13 로, 3문단 → 2문단 (240 → 약 185)

> Both CVD participants completed a second scanning session that compared the individualized filter and a deployed macOS accessibility filter against the unfiltered Session-1 baseline. The individualized filter was the per-subject 2-component stimulus-space pre-image, with parameters frozen from the main analysis and therefore out-of-sample. Acquisition, comparator, run count, condition order, and single-case-inference details are given in Supplementary~\S S13.
>
> Within each condition we recomputed the primary Session-1 interpolation metric (LOCO adjacent accuracy, \S\ref{sec:methods:loco}), LORO classification, SRM Procrustes disparity into the HC shared space, and the representational dissimilarity matrices, and we repeated the JND and 8AFC tasks of \S\ref{sec:methods:psychophysical} against both the unfiltered Session-1 baseline and the HC distribution. Each neural index was reported as a standardized single-case effect size (Cohen's $d$ against the HC distribution) rather than an inferential $p$, because the grand-mean permutation null is biased for this design, and the cross-session psychophysical comparison is descriptive. A secondary forward-tuning correlation, the Pearson $r$ between the predicted and the observed voxel pattern averaged over the eight held-out hues, indexes the encoding fit rather than the decoding accuracy that carries the comparison and is reported as corroboration only. With two participants every filter effect is measured within a person, and which of the two filters performs better remains open.

---

### 2.4 ⚠ 산술 재검토 — §2.2 의 조치만으로는 4,900 에 닿지 않는다

실측 단어 수로 각 조치의 증감을 합산하면 다음과 같다. 계수는 §0 과 같은 방식(주석 제거, 캡션 제외)이고, 교체 문안은 §2.3 의 실제 문안을 센 값이다.

| 조치 | 예측 증감 | **실측 증감** |
|---|---|---|
| (A) 전방 인코딩 모형 3단위 병합 | −49 | **−34** |
| (B) 두 디코딩 도식 서두 축약 | −67 | **−52** |
| (C) 파라미터 선정 4단위 → 2문단 | −43 | **−14** |
| (D) 식별가능성 5단위 → 2문단 | −43 | **+30** |
| (E) $L_{\rm LOCO}$ 원자 → 복합 손실 흡수 | −11 | **+3** |
| (F) JND 스테어케이스 → §S1 | −85 | **−50** |
| (G) 필터 평가 → §S13 | −55 | **−32** |
| (H) 통계 절 신설 | +145 | **+126** |
| Reproducibility 중복 문장 삭제 | — | **−17** |
| **소계** | **−208** | **−40** |

**실측 (2026-09-03 적용 후, 캡션 제외)**: 5,734 → **5,696**. HEAD(5,662) 대비로는 **+34** 이며, $\beta_s$ 근거 교체(+72)가 §2.3 의 절감을 상쇄했다.

**예측이 −208, 실측이 −40 으로 어긋난 원인은 검토 과정 자체다.** 위 표의 예측은 초안 기준이고, 이후 정확성을 위해 문장을 계속 추가했다. (D)가 −43 예측에서 +30 으로 73 단어 반전한 것이 가장 크며, `production candidate` 정의·`entered no selection decision`·`Tests 1, 2a, 2b, 2c` 대응 표기가 모두 검토 중 추가됐다. (C)는 Gate 2 문장 분할, (E)는 `invariant` 정정으로 각각 예상 절감을 잃었다. 셋 다 정확성 사유이므로 되돌리지 않는다.

**이 절의 실질 성과는 분량이 아니라 구조다.** 제목 단위 37 → 28, 60단어 미만 단위 7 → 2, 통계 절차 일원화가 달성됐다. §2 가 내건 4,900 은 여기서 519 단어 더 줄여야 닿는다. §2.2 의 항목별 추정치(−250, −120, −80)를 그대로 더해도 −450 이고 여기에 통계 절 +150 이 붙으므로, **"합계 예상 5,679 → 약 4,900" 은 §2.2 자신의 항목 합계와도 맞지 않는다.** 이전 판의 이 문장은 근거 없는 값이었다.

#### 추가 후보 (§2.2 에 없던 단위)

| 단위 | 현행 | 조치 | 증감 |
|---|---|---|---|
| `Representational geometry` ¶3–4 | 345 | 두 추정량의 정당화 서술을 §S8 로 이관하고 "둘을 보고하되 대칭 추정량이 추론용" 한 문장만 남긴다 | −95 |
| `Cross-run classification (LORO)` ¶2 | 209 | 교차피험자 전이 절차(인코더 이식 가능성 논증)를 §S7 으로 이관하고 본문은 두 목적지와 검정만 남긴다 | −69 |
| `Reproducibility` | 106 | 저널 표준 형식의 데이터·코드 가용성 문단으로 축약한다 | −46 |
| `Grid search` + `Composite loss` | 136 | 두 문단 병합 | −21 |
| **소계** | | | **−231** |

**둘을 합치면 약 5,188 이 현실적 하한이다** (교체 문안 실측 후 약 5,235, 아래 "추가 후보 실측 재검토" 표 참조). 기준 논문 3,811 의 **1.36배**이며, 그 이상은 §2.2(e) 가 보호 대상으로 지정한 `MRI acquisition`(445)·`Inverse fitting`(727)·`Cortical distortion model`(235) 을 건드려야만 가능하다.

**권고**: §2 의 목표치를 **4,900 에서 5,200 으로 조정한다.** 이 절의 실질적 성과는 절대 분량이 아니라 **단위 수 35 → 약 20** 과 **통계 절차의 일원화**이고, 그 둘은 위 조치만으로 달성된다.

#### 추가 후보 교체 문안 (I)–(L) — 2026-09-03 작성

> 위 표의 "현행" 열은 소절·문단 전체를 센 값이다. `Representational geometry` 345 는 소절 전체(¶1–¶4 + 말미 고아 문장), `LORO` 209 는 ¶1(87) + ¶2(122) 다. 아래 문안은 실제로 손대는 문단만 교체하며, 손대지 않는 문단은 그대로 둔다. 각 항목의 실측은 말미 표에 있다.

##### (I) `Representational geometry` ¶3–¶4 → 한 문단 (209 → 123), 이관분은 §S8 로

현행 ¶3 은 두 추정량의 **정의**(108 단어), ¶4 는 **정당화**(101 단어)이고, 그 뒤에 27 단어짜리 문장(`Because both patterns are scaled to unit norm ...`)이 줄 첫머리에 공백을 둔 채 고아로 붙어 있다(`methods_v2.tex:164`). 그 문장은 disparity 의 **정의**에 딸린 성질이므로 ¶1 끝으로 옮긴다. ¶3·¶4 는 정의와 정당화를 한 문단에 접는다. 접을 때 사라지는 것은 두 가지다. 폴드 분산의 비대칭성 서술("CVD 는 7폴드 평균, HC 는 자기 폴드 단일값이므로 보수적")과 "다른 모든 단계가 all-HC 공간에서 돈다"는 근거 문장인데, 전자는 §S8 로 옮기고 후자는 종속절로 줄여 본문에 남긴다.

> Two estimates of the control distribution were computed (Supplementary~\S S8). The first keeps the shared space trained on all seven controls, in which every other stage of the pipeline operates and the filter is fitted, so each control reference is in-sample while the projected CVD participant is out-of-sample. The second retrains the space on six controls at each fold and projects the held-out control on the same terms as each CVD participant, which is the appropriate test of departure from the control distribution. We report both and treat the symmetric estimate as the inferential test (\cref{tab:disparity_loso}). Disparity was also recomputed with two distances that use no shared response model, which shows that it tracks the data rather than the alignment procedure (Supplementary~\S S9).

**§S8 삽입 문안** (`Common-space and symmetric-LOSO estimates` 문단의 `Both use the \textcite{crawford1998} one-tailed single-case $t$ ...` 문장 **앞**에 넣는다. 약 67 단어).

> Under the symmetric estimate each CVD participant receives the mean of its seven fold disparities, whereas each control contributes the single value from the fold that held it out. The control distribution therefore retains fold-to-fold variance that the CVD statistic averages out, which makes the comparison conservative. The common space is retained alongside it because every other stage of the pipeline, including the filter fit, operates there.

**정합성 확인 1건.** §S8 의 그 문단은 `reported primarily in the common HC-trained SRM space` 로 시작하고, 본문은 `treat the symmetric estimate as the inferential test` 라고 한다. 두 진술은 양립한다(기술은 공통 공간, 추론은 대칭 추정량). 그러나 `primarily` 는 독자에게 공통 공간이 추론용으로 읽히게 하므로, 삽입과 함께 그 첫 문장의 `reported primarily in` 을 `described in` 으로 바꿀 것을 권한다. 이 문서 §4.2 의 Discussion 문안(`Under the symmetric leave-one-subject-out reference the protan V1 cell ... is the only one to reach significance`)도 대칭 추정량을 추론용으로 전제한다.

##### (J) `Cross-run classification (LORO)` ¶2 → 두 목적지와 검정만 (122 → 65), 인코더 이식 논증은 §S7 로

현행 ¶2 의 앞 절반(`To test whether hue representations were sufficiently shared ... which the SRM-aligned space supplies`, 약 57 단어)은 **왜 교차피험자 전이가 공통 공간을 요구하는가**라는 논증이고, §S7 의 `Leave-one-subject-out (LOSO)` 문단이 이미 같은 사실을 절반만 말하고 있다(`Cross-subject prediction needs a common voxel space`). 논증을 §S7 로 옮겨 그 문단을 완성하고, 본문은 두 목적지·셀 수·검정만 남긴다. `(Supplementary~\S S7)` 포인터가 §2.3(B) 의 서두 축약문에도 있으므로 여기서는 공간을 명시하는 자리에 한 번만 붙인다.

> Cross-subject transfer of the classifier was evaluated separately in the SRM-aligned space (Supplementary~\S S7). Transfer to a held-out control used a leave-one-control-out encoder trained on the remaining six controls, giving 28 participant-by-ROI cells, and transfer to CVD used an encoder trained on all seven controls, giving 8 cells. The two destinations were compared by a Mann--Whitney $U$ test with rank-biserial correlation as the effect size.

**§S7 `Leave-one-subject-out (LOSO)` 문단 교체 문안** (현행 72 → 약 107 단어). 현행 문단은 HC 목적지만 서술하고 CVD 목적지(7 HC 전부로 훈련)를 빠뜨리고 있어, 본문 ¶2 를 줄이면 그 정의가 원고에서 사라진다. 교체문이 두 목적지를 모두 담는다.

> \paragraph{Leave-one-subject-out (LOSO).}
> LOSO is the cross-subject transfer of \S\ref{sec:methods:loro} and tests whether hue representations are shared across participants closely enough for one participant's encoder to decode another's responses. All eight hues enter training, so the scheme extends LORO across participants and has no interpolation counterpart. The encoder $W$ maps the six channels onto the voxels of the participant it was fitted to, and applying it to a second participant requires the two voxel spaces to correspond, which the SRM-aligned space supplies. For each held-out control, $W$ was trained on the shared-space data of the remaining six controls, and for each CVD participant on the shared-space data of all seven.

§3.4(c) 가 Results 의 Mann--Whitney $U = 163.5$ 와 rank-biserial $r = 0.46$ 을 §S14 로 보내므로, 검정 **이름**은 Methods 에, **값**은 §S14 에 남는 배치가 된다.

##### (K) `Reproducibility` → 소프트웨어·시드·포인터 세 문장 (105 → 62)

현행 문단은 네 가지를 담는다. 소프트웨어 버전, §S15 포인터, 시드 세 개, 코드 URL 과 데이터 접근 조건이다. §S15 포인터 문장은 §2.2(b) 의 정리표가 이미 삭제 대상으로 지정했다(신설 통계 절 말미의 포인터와 중복). 코드 URL 은 `main.tex:160` 의 Data and Code Availability 절이 같은 주소를 싣고 있고, 제출 시 Zenodo DOI 가 그 절에 붙을 예정이므로, 같은 주소를 두 곳에 두면 제출 직전에 한쪽만 갱신될 위험이 있다. Methods 는 그 절을 가리키기만 한다. 시드 값은 재현에 필요한 정보이므로 본문에 남긴다.

> \subsection{Reproducibility}
> \label{sec:methods:repro}
>
> All analyses were run in Python 3.10 with numpy 1.24.3, scipy 1.11.3, scikit-learn 1.3.0 \parencite{pedregosa2011}, and BrainIAK 0.11. Random seeds were fixed for every permutation test and bootstrap, 42 throughout except 31337 for the parameter-recovery synthesis and 27182 for the color-label permutation, and each script records its own value. Code and data access are described in the Data and Code Availability section.

**확인 사항 1건.** 본문의 BrainIAK 판본은 0.11 이고, 로컬 `srm` 환경은 0.12 다(2026-09-02 확인). 보고된 SRM 산출이 서버 0.11 로 나온 것인지, §S2 재산출이 로컬 0.12 로 나온 것인지 확인하고, 둘 다 쓰였다면 두 판본을 병기해야 한다. 이 확인은 분량 조정 범위 밖이다.

##### (L) `Composite loss` + `Grid search` → 한 문단 (§2.3(E) 위에 얹는다)

§2.3(E) 가 `hV4 LOCO voxel-prediction` 문단을 `Composite loss` 첫머리로 흡수한 뒤, 그 문단 끝에 `Grid search` 를 이어 붙인다. 현행 `Grid search` 의 마지막 문장(`Per-subject loss combinations and parameter selection are described in \S\ref{sec:methods:selection}`)은 바로 다음 소절 제목이 같은 정보를 주므로 삭제한다. 병합의 실질 이득은 단어보다 **전방 참조 해소**다. 현행 `Composite loss` 는 `evaluated over the full parameter grid and standardized ... across that grid` 라고 하면서 그 grid 를 다음 문단에서야 정의한다. 한 문단이 되면 같은 문단 안에서 정의된다.

> \paragraph{Composite loss and grid search.}
> A third atom, $L_{\rm LOCO}$, scored how well a candidate distortion accounted for the CVD participant's own held-out responses at hV4. It was available to every candidate objective, is defined in Supplementary~\S S12, and the selection procedure admitted it in neither participant. The atoms differ in scale, since $L_\gamma$ is built from threshold ratios while $L_{\rm RDM}$ and $L_{\rm LOCO}$ are bounded dissimilarities. Each atom was therefore evaluated over the full parameter grid and standardized to zero mean and unit standard deviation across that grid. Standardization equalizes the spread of the atoms over the grid and leaves the composite invariant to rescaling an individual atom by a positive constant. The composite loss is the sum of the standardized atoms divided by $\sqrt{n_a}$, where $n_a$ is the number of atoms. The grid was exhaustive at $2^\circ$ resolution, with $\beta_s$ over $[0^\circ, 50^\circ]$ (26 values) and $\beta_c$ over $[-50^\circ, 50^\circ]$ (51 values), giving $1{,}326$ cells, and for the R+C comparison model (Supplementary~\S S11) $g$ was searched over $[0, 3]$ in steps of $0.05$ (61 values).

##### 추가 후보 실측 재검토

| 항목 | 현행 | 교체 | 증감 | 표의 추정 | 비고 |
|---|---|---|---|---|---|
| (I) `Representational geometry` 소절 전체 | 346 | 260 | **−86** | −95 | ¶1 60 + 고아 문장 27 + ¶2 50 + 신규 123. §S8 에 +67 |
| (J) `LORO` ¶2 | 122 | 65 | **−57** | −69 | ¶1 87 은 불변. §S7 에 +35 |
| (K) `Reproducibility` | 105 | 62 | **−43** | −46 | §S15 포인터 삭제분 포함 |
| (L) $L_{\rm LOCO}$ + `Composite` + `Grid` | 176 | 167 | −9 | −21 | 이 중 −11 은 (E) 가 이미 계상. **(L) 의 순증감은 약 +2** |
| **소계 (E 중복 제외)** | | | **−184** | −231 | |

**5,419 − 184 = 약 5,235.** §2.4 권고치 5,200 과 35 단어 차이이므로 권고를 유지한다. 표의 추정 −231 이 실측 −184 로 줄어든 이유는 (L) 이 단어를 거의 줄이지 않기 때문이며, (L) 은 분량이 아니라 단위 수 감소(2 → 1)와 전방 참조 해소를 위해 유지한다. 부록은 §S7 +35, §S8 +67, §S1 +65(§2.3 F) 로 합계 약 +167 이 늘며, 부록 분량은 이 문서의 계수 대상 밖이다.

---

## 3. Results — 2,836 (캡션 제외 **2,242** 실측) → 목표 **약 1,950** (2026-09-03 조정, §3.5)

### 3.1 보고 방식 비교

| | Kwon 2025 | 본 원고 |
|---|---|---|
| 단어 (캡션 제외) | 1,860 | 2,254 |
| 수치 토큰 / 100 단어 | **3.0** | **8.3** |
| 본문 `p` 표기 | 26회, 전부 **역치**(`p < 0.05`) | 13회, 전부 **정확값** |
| 본문 검정통계량 | 없음. 효과크기 $D$ 만 2회 | $t$, $d_{cc}$, CI, IQR, 재표집 수, 폴드 범위 |
| 문단 구성 | **그림 패널 하나 = 문단 하나.** 끝에 해석 한 문장 | 수치 열거 뒤 해석 |
| 표 | Results 안에 없음. Supplementary 로 | Results 안에 없음. 부록 표 5개를 가리킴 |

**진단**: 기준 논문은 정확한 통계량을 본문에 쓰지 않는다. 방향, 유의 역치, 그림 패널 참조로 문단을 구성하고 정확값은 부록 표에 둔다. 본 원고는 수치 밀도가 **2.8배**다. 소절별로 보면 `Psychophysical and neural filter evaluation`(591 단어, 12.2/100w)과 `A common cortical model fits both`(431 단어, 7.2/100w)가 가장 조밀하다.

### 3.2 조치 — 정확값은 표로, 본문은 방향과 해석으로

#### (a) 모형 적합 두 소절 (431 + 230 = 661 단어 → 약 350)

`A common cortical model fits both` 와 `The neural term relocates` 가 IQR, 재표집 300 중 263, 7폴드 범위 $[-46, -38]$, 차점 손실 $-1.52$ 등을 본문에 나열한다. **§S11 의 `tab:modelfits` 가 이미 있으므로** 파라미터·손실·재표집 통계를 그 표(또는 신설 `tab:fit_stability`)로 옮기고, 본문은 각 참가자의 $(\hat\beta_s, \hat\beta_c)$, $\overline{L}_{\rm test}$, 그리고 **안정성 한 문장**만 남긴다.

**예시 — protan 문단 (현행 약 170 단어)**

> 현행: For the protan participant ($\theta_{\rm conf} = 16^\circ$), the selected loss combination $\gamma_{\rm all} + L_{\rm RDM}^{(V1)}$ yielded $(\hat\beta_s, \hat\beta_c) = (2^\circ, +24^\circ)$. The held-out test-loss was $\overline{L}_{\rm test} = -1.54$ (IQR $= 1.42$). The runner-up loss combination replaced $\gamma_{\rm all}$ with $\gamma_{\rm GB}$ and reached $-1.52$ at the same estimate $(2^\circ, +24^\circ)$, so the fitted parameters do not depend on which psychophysical atom enters. Both combinations improved on the retinal-plus-cortical class scored on the same composite ($\overline{L}_{\rm test} = -0.86$). The HC-resample parameter IQR was $(0^\circ, 0^\circ)$, and $263$ of the $300$ resamples returned the identical cell $(2^\circ, +24^\circ)$, with the remainder at $(32^\circ, 0^\circ)$. The strict 7-fold leave-one-out refit returned $(2^\circ, +24^\circ)$ on all seven folds. This stability holds for the PCA-basis loss. The argmin shifts under the alternative SRM-basis reduction, so the recovered position is metric-dependent (Supplementary~\S S12).
>
> 교체 (약 75 단어): In the protan participant the selected combination $\gamma_{\rm all} + L_{\rm RDM}^{(V1)}$ returned $(\hat\beta_s, \hat\beta_c) = (2^\circ, +24^\circ)$ with $\overline{L}_{\rm test} = -1.54$, and the runner-up combination returned the same estimate. The estimate held on every leave-one-out fold and in $263$ of $300$ control resamples (Table~\ref{tab:modelfits}). The position depends on the basis, shifting under the SRM reduction (Supplementary~\S S12).

#### (b) 필터 평가 소절 (591 단어 → 약 400)

`Geometry` 문단이 2 참가자 × 3 조건 × 2 지표 = **12개 수치**를 한 문단에 담는다. 신설 표 `tab:exp2_geometry`(부록 §S13)로 옮기고 본문은 방향만 진술한다.

**예시 — Geometry 문단 (현행 약 130 단어, 14 수치)**

> 현행: Both filters left the representational geometry short of the HC level, and the direction of the filter effect reversed between the two participants (Fig.~\ref{fig:filter_eval}B,C,E,F; all values from the run-matched estimates of Supplementary~\S S13). In the deutan participant both filters moved the geometry further from HC than the unfiltered baseline: V2 SRM disparity rose from $0.68$ to $0.87$ deployed and $0.77$ individualized (HC $0.44$), and V2 RDM similarity fell from $0.42$ to $0.16$ and $0.05$ (HC self-consistency $0.59$). In the protan participant the two indices disagreed: V1 SRM disparity improved comparably under both filters ($0.70$ unfiltered to $0.66$ deployed and $0.63$ individualized; HC $0.43$), whereas V1 RDM similarity rose only under the deployed filter ($0.33$ to $0.38$) and fell under the individualized one ($0.26$; HC self-consistency $0.66$). Neither index attributes the geometric recovery to individualization.
>
> 교체 (약 70 단어, 수치 0): Both filters left the representational geometry short of the control level, and the direction of the filter effect reversed between participants (Fig.~\ref{fig:filter_eval}B, C, E, F). In the deutan participant both filters moved the geometry away from the control reference on disparity and on RDM similarity. In the protan participant both filters reduced disparity, while RDM similarity rose under the deployed filter and fell under the individualized one. Neither index attributes the geometric change to individualization (Supplementary Table~\ref{tab:exp2_geometry}).

**⚠ 현행 문단이 콜론과 세미콜론을 쓴다.** 이 세션 이전의 미커밋 편집으로 압축된 형태이며 §0.7-E 문체 규칙과 어긋난다. 교체문은 그것도 함께 고친다.

같은 소절의 `Interpolation` 문단(hV4 세 조건 × 2 참가자 + $d_{cc}$)도 같은 방식으로 표로 넘긴다.

#### (c) 첫 소절 (514 단어, 8.6/100w)

헤드라인 소절이므로 수치를 남긴다. 다만 인코더 전이 문단의 Mann–Whitney $U = 163.5$, rank-biserial $r = 0.46$ 은 §S14 로 보내고 본문은 `0.432` 와 `0.526` 두 값과 $p$ 만 남긴다. 절감 약 30 단어.

#### (d) `Per-subject stimulus-space filter` (96 단어, 10.4/100w)

색별 $\delta\theta$ 값이 Figure 7 에 이미 그려져 있다. 본문의 수치 나열을 빼고 그림을 가리킨다. 절감 약 40 단어.

#### (e) 문단마다 해석 한 문장

기준 논문의 문단은 끝에 해석 한 문장을 둔다(`This means that ...`). 본 원고의 적합·평가 문단은 수치 열거로 끝나는 경우가 있다. 각 문단이 결과 진술 → 해석 한 문장으로 닫히게 한다.

**합계 예상**: §3.5 에서 실측으로 재계산한다.

---

### 3.3 삭제된 소절의 복원 여부 — **복원하지 않는다** (2026-09-03 확인 후 판정 번복)

#### 결론 한 줄

**그 소절은 삭제된 것이 아니라 Supplementary §S12 로 전량 이관되었다.** 본문에는 105 단어 요약이 남아 있고, Figure 6 은 Supplementary Figure S1 로 개명되어 살아 있다. 복원할 것이 없으므로 **복원하지 않고, 빠진 문장 하나만 본문에 되돌린다.**

> **이전 판의 판정은 근거가 없었다.** 종전 §3.3 은 이 변경을 "삭제"로 보고 §0.7-C·`CLAUDE.md` 기여 진술과 충돌한다고 판단해 복원(약 250 단어 추가)을 권고했다. `git show HEAD` 와 현행 `supplementary.tex` 를 대조하지 않은 채 `git diff` 의 삭제 표시만 읽은 결과다.

#### 대조표 — HEAD 의 소절이 지금 어디에 있는가

| HEAD `results_v4.tex:136–159` 의 내용 | 현재 위치 | 상태 |
|---|---|---|
| ¶1 deutan 부호 300/300·7/7 폴드, protan 기저 의존 (263/300 vs 171/300, 부호 +17% / −26%) | `supplementary.tex:707` | 원문 그대로 |
| ¶1 `(32°, 0°)` = protan PCA 지형의 2차 분지 | `supplementary.tex:707` | 원문 그대로 |
| ¶2 축별 회복 불확도 22°/26°(deutan), 16°/24°(protan) | `supplementary.tex:708` | 원문 그대로 |
| ¶2 deutan 4.7° vs protan 26.4° 회복 오차 | `supplementary.tex:708` | 원문 그대로 |
| ¶2 **`beta_s` 절대값 6°·2° 는 불확도 이하 → S-cone 진폭을 0 과 구별할 수 없다** | `supplementary.tex:708` + §S12 Test 1 표 캡션 | 부록에만 있음 ⚠ |
| ¶2 $f_{10^\circ}$ = 26% / 14% (사전 기준 50%) | `supplementary.tex:628` 표 캡션 | 원문 그대로 |
| ¶3 deutan `beta_c` 는 202/300 이 [−48°, −36°], `beta_s` 는 0–14° 균일 | `supplementary.tex:709` | 원문 그대로 |
| **Figure 6 `fig6_landscape`** | `supplementary.tex:720` 에 **`figS1_landscape`** 로 | 개명 이관, 파일 디스크에 존재 |
| 소절 요약 (전역 최소·기저 민감성·6검정 전량 비유의) | `results_v4.tex:93` ¶4, 105 단어 | 본문에 압축 잔존 |

#### 정합성 점검 — 깨진 것이 없다

| 항목 | 결과 |
|---|---|
| 빌드 체인의 `sec:results:identifiability` 미해결 참조 | **0건.** 유일한 참조는 `Discussion/archive/discussion_v2.tex:20` 이고 `main.tex` 가 읽지 않는다 |
| `fig:landscape` 참조 | `supplementary.tex:707` → 같은 파일 `:724` 라벨로 해소 |
| `fig6_landscape.pdf/.png` 스테이징된 삭제 | **정상.** `figS1_landscape.pdf/.png`(2026-08-17 생성)가 디스크에 있고 부록이 그것을 부른다 |
| §0.7-C "소절 5–9 불변" 과의 충돌 | **없음.** 내용·그림·검정이 모두 보존되었고 이동만 일어났다 |

이 변경은 오히려 §3.2 가 내건 원칙("정확값은 표와 부록으로, 본문은 방향과 해석으로")을 그대로 실행한 사례다.

#### 다만 하나가 빠졌다 — 본문에 되돌릴 문장

부록으로 간 문장 가운데 **본문에 반드시 남아야 하는 것이 하나** 있다. 적합된 $\hat\beta_s$ 의 크기가 회복 불확도 아래에 있어 **S-cone 축 진폭을 0 과 구별할 수 없다**는 진술이다.

이 논문의 기여 2 는 왜곡을 **2성분**(S-cone축 + 혼동축)으로 기술하는 것이다. 그중 한 성분의 진폭이 측정되지 않는다는 사실이 본문에 없으면, 독자는 두 성분이 대등하게 추정된 것으로 읽는다. 현행 ¶4 는 protan 추정치가 "회복 불확도 안에 있다"고만 말할 뿐, **두 참가자 모두에서 S-cone 진폭이 식별되지 않는다**는 더 강한 사실은 말하지 않는다. 리뷰어가 가장 먼저 물을 지점이다.

현행 `results_v4.tex:93` ¶4 의 끝에 한 문장을 덧붙인다 (약 25 단어).

> ... so the fitted optima are reported as descriptive embeddings of the distortion rather than physiological point estimates. The fitted S-cone amplitudes of $6^\circ$ and $2^\circ$ fall below the recovery uncertainty on that axis in both participants, so that component's magnitude is bounded rather than estimated (Supplementary~\S S12).

#### ✅ 최종 판정

| 선택지 | 분량 | 판정 |
|---|---|---|
| 소절 250 단어 + Figure 6 을 본문에 복원 | +250, 본문 그림 +1 | **기각.** 내용이 이미 §S12 에 있으므로 중복이고, 본문 그림이 7장에서 8장으로 늘고 그중 하나를 회복 진단에 쓰게 된다 |
| 현행 유지 | 0 | 기각. S-cone 진폭 미식별이 본문에서 사라진다 |
| **현행 유지 + 한 문장 보강** | **+25** | **채택** |

### 3.4 교체 문안

> `Results/results_v4.tex` 실측(주석 제거·캡션 제외) 2,242 단어 기준이다. 소절별 실측은 §3.5 표에 있다.
>
> 소제목의 ✅ = 본문 적용 완료, 🔸 = 일부만 적용.

#### ⚠ 먼저: §3.2(a) 의 예시가 낡았다

§3.2(a) 가 "현행"으로 인용한 protan 문단(약 170 단어, runner-up 손실·263/300 재표집·7폴드 재적합을 모두 담은 형태)은 **현재 작업 트리에 없다.** 현행 `results_v4.tex:88` 은 deutan 과 protan 을 한 문단(105 단어)에 담고 있고, 재표집·폴드·기저 의존성은 뒤쪽 문단으로 이미 옮겨져 있다. 즉 §3.2(a) 가 제안한 압축은 **상당 부분 이미 반영되어 있다.** 아래 문안은 현행 본문을 기준으로 다시 작성한 것이다.

#### ✅ (a-1) `A common cortical model fits both` ¶1 — 분리도 8개를 표로 (100 → 약 65)

V1–hV4 각각의 분리 $d$ 여덟 개는 방향을 말하지 않고 자리만 차지한다. `tab:modelfits` 에 열을 추가해 옮긴다.

> The separation precondition determined the candidate grid. The RDM atom entered only at ROIs where it separated the participant from the control distribution (Section~\ref{sec:methods:selection}), which left all four ROIs in the deutan participant and V1 alone in the protan participant (per-ROI separations in \cref{tab:modelfits}). The psychophysical axis was enumerated in full. Both winning loss combinations paired a JND atom with a $\Delta$RDM atom, and the LOCO family entered neither.

#### ✅ (a-2) 같은 소절 ¶2 — 손실값과 IQR 을 표로 (105 → 약 70)

> For the deutan participant ($\theta_{\rm conf} = 150^\circ$), $\gamma_{\rm OY} + L_{\rm RDM}^{(V2)}$ ranked first among the 25 combinations passing the boundary-saturation gate and returned $(\hat\beta_s, \hat\beta_c) = (6^\circ, -42^\circ)$. For the protan participant ($\theta_{\rm conf} = 16^\circ$), $\gamma_{\rm all} + L_{\rm RDM}^{(V1)}$ ranked first among four and returned $(2^\circ, +24^\circ)$. Each selected cell generalized better to held-out control references than the competing $\beta_s$-dominant candidate of the same participant (\cref{tab:modelfits}).

**필요한 표 작업**: `tab:modelfits`(`supplementary.tex:570`)는 현재 4열(참가자·모형·적합 파라미터·held-out fit)이다. 여기에 **분리 $d$(ROI별)**, **$\overline{L}_{\rm test}$ IQR**, **차점 후보의 $\overline{L}_{\rm test}$** 열을 추가한다. 행 구성이 이미 참가자 × 모형이므로 새 표를 만들 필요가 없다.

#### ✅ (a-3) ¶4·¶5 는 유지한다

식별가능성 문단(105 단어)과 망막계 비교 문단(80 단어)은 §0.7 의 "효능을 주장하지 않는다"·"절대값 해석 금지" 프레임을 본문에서 지탱하는 유일한 자리다. 수치를 빼면 그 제약이 부록으로 밀려나므로 손대지 않는다.

#### ✅ (a-4) `The neural term relocates ...` ¶3 — IQR 12개를 표로 (95 → 약 50)

> The neural term also narrowed the resample spread in both participants, under both basis reductions (\cref{tab:modelfits}). In the protan participant the SRM reduction places the optimum at $(32^\circ, 0^\circ)$ rather than at the PCA solution. The neural term therefore contributed information that the psychophysical atoms alone did not carry.

#### ✅ (a-5)–(a-7) §3.2(a) 의 범위 안에서 문안이 없던 세 문단 (2026-09-03 보강)

§3.2(a) 는 `A common cortical model fits both`(431)와 `The neural term relocates`(230)를 통째로 대상으로 삼았으나, §3.4 는 그중 ¶1·¶2·(neural term) ¶3 만 문안을 두었다. 남은 세 문단의 문안을 아래에 둔다. §3.2(a) 가 열거한 네 수치 가운데 현행 본문에 남아 있는 것은 **IQR 뿐**이며, `263/300`·`[−46°, −38°]`·`−1.52` 는 이미 부록 §S15 로 옮겨져 본문에 없다.

**표 배치 권고.** (a-4)·(a-6)·(a-7) 가 표로 보내는 수치는 전부 **신경 항 소거(ablation) 통계**다. 심리물리 단독·신경 단독·결합 적합의 argmin, 원자별 귀무 대비 $\Delta L$, 경계 포화율, 기저별 재표집 IQR, 격자 순위 백분위가 그것이며, `tab:modelfits`(참가자 × 모형 구조)에 열로 붙이면 표가 두 주제를 섞는다. §3.2(a) 가 대안으로 언급한 **`tab:fit_stability` 를 §S13 에 신설**하고 이 다섯 항목을 모으는 편을 권한다. 채택 시 (a-4) 문안의 `\cref{tab:modelfits}` 를 `\cref{tab:fit_stability}` 로 바꾼다. `tab:modelfits` 는 (a-1)·(a-2) 의 분리 $d$·IQR·차점 손실만 받는다.

**(a-5) `A common cortical model` ¶3 — 폴드 일반화 (73 → 48).** 상위 5%·8% 두 값을 하나의 상한으로 묶고 개별 순위는 표로 보낸다.

> Both fits generalized to held-out control data. On every leave-one-out fold the fitted distortion predicted the CVD geometry more closely than the null distortion $(0^\circ, 0^\circ)$, and on held-out loss each selected cell ranked within the top $8\%$ of the $1{,}326$-cell grid (per-participant ranks and losses in \cref{tab:fit_stability}).

**(a-6) `The neural term relocates` ¶1 (86 → 66).** 두 좌표는 소절 제목이 말하는 "이동" 그 자체이므로 남기고, $\Delta L = +0.01$·`3 of 7 folds`·$0.47$ 은 표로 보낸다. 현행 첫 문장의 셋째 절(`narrowed the resample spread in both`)은 ¶3 의 첫 문장과 축자 중복이므로 뺀다.

> The neural term moved the fitted optimum in the protan participant and sharpened it in the deutan participant. Without the RDM atom the protan optimum sits at the S-cone-dominant $(26^\circ, +4^\circ)$, and with it at the confusion-axis-dominant $(2^\circ, +24^\circ)$. At that estimate only the RDM term separates from the no-distortion control (\cref{tab:fit_stability}), so the confusion-axis component of the protan distortion is carried by the neural data.

**(a-7) 같은 소절 ¶2 (55 → 67, 해석 문장 포함).** 세 좌표는 "방향이 아니라 정밀도"라는 주장의 증거이므로 남기고, 포화율 $23\% \to 9.3\%$ 는 방향만 진술하고 값은 표로 보낸다. (f) 표의 둘째 행이 이 문단에 덧붙이려던 해석 문장은 현행 첫 문장(`adds precision rather than direction`)과 같은 내용이므로, 별도로 붙이지 않고 `all on the same side of the confusion axis` 절과 마무리 문장으로 접는다. **(f) 둘째 행은 이 문안에 흡수된다.**

> In the deutan participant the RDM atom adds precision rather than direction. The psychophysical atoms alone settle at $(16^\circ, -44^\circ)$, the combined fit at $(6^\circ, -42^\circ)$, and a neural-only fit at $(4^\circ, -26^\circ)$, all on the same side of the confusion axis, and adding the RDM atom more than halved the boundary-saturation rate (\cref{tab:fit_stability}). The neural term therefore sharpens a direction that the psychophysical atoms already fix.

#### ✅ (b-1) `Geometry` 문단 (136 → 약 70, 수치 0)

§3.2(b) 의 문안을 그대로 채택한다. 콜론·세미콜론도 함께 제거된다.

> Both filters left the representational geometry short of the control level, and the direction of the filter effect reversed between participants (Fig.~\ref{fig:filter_eval}B, C, E, F). In the deutan participant both filters moved the geometry away from the control reference on disparity and on RDM similarity. In the protan participant both filters reduced disparity, while RDM similarity rose under the deployed filter and fell under the individualized one. Neither index attributes the geometric change to individualization (Supplementary Table~\ref{tab:exp2_geometry}).

#### ✅ (b-2) `Interpolation` 문단 (130 → 약 80)

> At hV4 the individualized filter raised interpolation in the deutan participant and lowered it in the protan participant (Fig.~\ref{fig:filter_eval}A, D). In the deutan participant it was the only one of the three conditions to exceed the analytic chance level. In the protan participant it gave the lowest of the three conditions, and all three fell below chance. Per-condition values and single-case effect sizes are in Supplementary Table~\ref{tab:exp2_geometry}.

**필요한 표 작업**: `tab:exp2_geometry` 는 **아직 존재하지 않는다.** §S13 에 신설해야 하며, 담을 것은 참가자 2 × 조건 3 × 지표 3(LOCO adjacent accuracy, SRM disparity, RDM similarity) 에 HC 기준값과 $d_{cc}$ 를 더한 형태다. `tab:exp2_loro`(`supplementary.tex:773`)와 같은 자리에 둔다.

#### ✅ (b-3) `Identification accuracy, held out from the fitting loss.` 문단 (82 → 61, 2026-09-03 보강)

§3.2(b) 의 591 단어에는 이 문단이 포함되지만 §3.4 에 문안이 없었다. 현행 문단은 정확도 6개와 95% CI 6쌍, 곧 **18개 수치**를 한 문단에 담는다. 현행 마지막 문장(`held out of both fitting terms ... prospective test`)은 이 문단이 존재하는 이유이므로 첫 문장으로 올리고, 방향만 진술하되 deutan 의 상승 폭 한 쌍만 남긴다. protan 의 `fell under the deployed comparator` 는 CI 가 겹치지 않으므로($[0.94, 1.00]$ 대 $[0.75, 0.92]$) 값 없이 방향만 적어도 근거가 표에 있다.

> Eight-alternative identification was held out of both fitting terms and is therefore a prospective test of the filters. In the protan participant identification was at ceiling without a filter, stayed there under the individualized filter, and fell under the deployed comparator. In the deutan participant it rose from $0.81$ to $0.97$ under each filter (accuracies and Wilson intervals in Supplementary Table~\ref{tab:exp2_8afc}).

**필요한 표 작업**: `tab:exp2_8afc` 는 **아직 존재하지 않는다.** §S16 는 8AFC 과제를 본문(`supplementary.tex:620`)에서 서술만 하고 표가 없다. 참가자 2 × 조건 3 의 정확도와 Wilson 95% 구간(각 $n = 64$)을 담는 6행 표를 `tab:exp2_loro` 옆에 신설한다. exp2 JND 도 마찬가지로 표가 없으나, (e) 문안이 §S12 를 가리키고 있으므로 그쪽에 조건별 $z$ 열을 붙일지, 같은 §S16 표에 합칠지는 (e) 적용 시 함께 정한다.

#### ✅ (c) 첫 소절 인코더 전이 문단 (545 → 약 490)

Mann–Whitney $U = 163.5$ 와 rank-biserial $r = 0.46$ 을 §S14 로 보내고 본문에는 두 정확도와 $p$ 만 남긴다.

> An encoder built from the healthy controls also decoded hues from the CVD participants' cortical responses. Accuracy on their held-out runs averaged $0.432$ over the eight participant-by-ROI cells, above the $0.125$ chance level ($t(7) = 6.51$, $p < 0.001$), against $0.526$ over the 28 cells of the held-out controls ($p = 0.052$; Supplementary~\S S14). A channel-to-voxel weight matrix estimated in the controls therefore predicts CVD responses, and each participant's own accuracy lies within the control range.

#### ✅ (d) `Per-subject stimulus-space filter` (96 → 약 62)

색별 $\delta\theta$ 의 범위는 Figure 7 이 이미 그린다.

> Each filter is the exact numerical pre-image of that participant's fitted 2-component transform (Section~\ref{sec:methods:filter}). The mean per-hue correction is $26.3^\circ$ for the deutan participant ($\hat\beta_s = 6^\circ$, $\hat\beta_c = -42^\circ$, $\theta_{\rm conf} = 150^\circ$) and $16.2^\circ$ for the protan participant ($2^\circ$, $+24^\circ$, $16^\circ$), and the per-hue values are drawn in Figure~\ref{fig:filter}. Both filters were frozen on the primary pipeline before the second session and were not re-derived, so the preprocessing comparison leaves the evaluated filter unchanged (Supplementary~\S S12).

#### ✅ (e) `Psychophysics` 문단 (182 → 약 140)

여덟 쌍의 $z$ 값은 `tab:jnd_baseline`(`supplementary.tex:493`)에 이미 있다. 본문은 방향과 임계 통과 여부만 진술한다.

> In the deutan participant both filters removed the baseline deficit. All three elevated pairs returned to within $\pm 1.8$ control SDs, the mean $|z|$ fell from $2.24$ to below $0.9$ under each filter, and the two filters were indistinguishable on thresholds (Wilcoxon $p = 0.84$).
>
> In the protan participant the two filters diverged. The deployed filter left two pairs deviant and raised the mean $|z|$ from $0.90$ to $1.78$, whereas the individualized filter held every pair within $\pm 1.5$ and left the mean $|z|$ unchanged at $0.93$ (Supplementary~\S S1). Of the two filters, only the individualized one kept every previously non-deviant pair inside the control range in both participants.

#### ✅ (f) 해석 문장이 없는 문단 (§3.2 e 의 구체화)

실측 결과 결과 진술로만 끝나는 문단은 다음 셋이다. 각각 한 문장을 덧붙인다.

| 위치 | 현재 끝 문장 | 덧붙일 해석 (교체 문안) |
|---|---|---|
| `Hue-discrimination thresholds ...` ¶2 | `Values for all eight pairs appear in Supplementary~\S S1.` | `The elevations are therefore axis-specific rather than a general loss of chromatic sensitivity.` |
| `The neural term relocates ...` ¶2 | — | **(a-7) 문안에 흡수됨** |
| `Colors remained decodable.` | `... against an HC range of $0.71$ to $0.77$ (Supplementary Table~\ref{tab:exp2_loro}).` | `Both filters therefore preserved the color signal that the correction acts on.` |

첫 행의 문안은 축 특이성만 진술하고 2성분 모형을 근거로 끌어오지 않는다. JND 소절이 `A common cortical model fits both`(`results_v4.tex:83`)보다 앞에 있어 순방향 참조가 되기 때문이다. 근거는 앞 두 문단이 이미 제시한다. ¶1 이 상승한 쌍마다 어느 축을 끼고 있는지 밝히고, ¶2 가 나머지 쌍은 통제 범위 안이며 $180^\circ$ 통제 쌍은 더 미세하다고 적는다. 근거를 한 번 더 붙이는 판본은 `Every pair off those axes lies within the control range, so the elevations are axis-specific rather than a general loss of chromatic sensitivity.` 이다.

**소절 제목 점검이 남아 있다.** 현행 제목은 `Hue-discrimination thresholds are elevated on each participant's own confusion axis` 인데, deutan 의 최대 상승 쌍은 혼동축이 아니라 S-cone 쌍 yellow--purple($z = +6.70$)이다.

#### §3.2 조치 ↔ §3.4 문안 대응표 (2026-09-03)

§3.2 의 조치 항목마다 §3.4 의 어느 문안이 이행하는지 적는다. 이 표로 §3.4 가 §3.2 를 빠짐없이 덮는다.

| §3.2 조치 | 대상 문단 | §3.4 문안 |
|---|---|---|
| (a) 모형 적합 두 소절 | `A common cortical model` ¶1 / ¶2 / ¶3 / ¶4·¶5 | (a-1) / (a-2) / **(a-5)** / (a-3) 유지 |
| (a) 〃 | `The neural term relocates` ¶1 / ¶2 / ¶3 | **(a-6)** / **(a-7)** / (a-4) |
| (b) 필터 평가 소절 | Psychophysics ¶1–¶3 / Identification / Colors decodable / Interpolation / Geometry | (e) / **(b-3)** / (f) 셋째 행 / (b-2) / (b-1) |
| (c) 첫 소절 인코더 전이 | ¶2 | (c) |
| (d) `Per-subject stimulus-space filter` | 전체 | (d) |
| (e) 문단마다 해석 한 문장 | JND ¶2 · neural ¶2 · Colors decodable | (f). 둘째 행은 (a-7) 에 흡수 |

**부수 확인 — Results 의 부록 번호 참조는 전부 맞다.** 현행 `supplementary.tex` 의 절 배치와 대조한 결과다.

| 위치 | 참조 | 가리키는 절 | 판정 |
|---|---|---|---|
| `:30` | §S16 | SRM 정렬 공간 판독 재현 (S15 = Alignment robustness) | 정합 |
| `:34` · `:56` · `:68` | §S2 | 전처리 민감도 (S1 = Preprocessing pipelines) | 정합 |
| `:58` | §S17 | 기하 비교 타당성 (S16 = Validity of the geometric comparison) | 정합 |
| `:93` | §S12 | 식별가능성 검정 (S12 = Identifiability checks) | 정합 |
| `:95` | §S11 | 망막계 비교 모형 (S11 = Retinal-family) | 정합 |
| `:159` (캡션) · `:179` | §S13 | exp2 run-matched 추정 (`supplementary.tex:636`) | 정합 |

선행 조건 목록의 부록 번호도 현행 배치로 고쳤다. `tab:modelfits` = §S11, `tab:fit_stability` = §S12, `tab:exp2_8afc` · `tab:exp2_geometry` = §S13 이다.

---

### 3.5 산술 재검토 — Results 는 목표에 거의 닿는다

| 조치 | 현행 | 교체 | 증감 |
|---|---|---|---|
| (a-1) 분리 $d$ 8개 → `tab:modelfits` | 100 | 65 | −35 |
| (a-2) $\overline{L}_{\rm test}$·IQR → `tab:modelfits` | 105 | 70 | −35 |
| (a-4) 재표집 IQR 12개 → 표 | 95 | 50 | −45 |
| (b-1) `Geometry` 문단 | 136 | 70 | −66 |
| (b-2) `Interpolation` 문단 (forward-tuning 지표 제외) | 130 | 68 | −62 |
| (c) 인코더 전이 $U$·$r$ → §S14 | 545 | 490 | −55 |
| (d) `Per-subject stimulus-space filter` | 96 | 62 | −34 |
| (e) `Psychophysics` 문단 | 182 | 140 | −42 |
| (f) 해석 문장 3개 → 2개 추가 (둘째 행은 (a-7) 에 흡수) | 0 | 30 | +30 |
| (g) S-cone 진폭 미식별 문장 보강 (§3.3) | 0 | 25 | +25 |
| (a-5) 폴드 일반화 ¶3 → `tab:fit_stability` | 73 | 48 | −25 |
| (a-6) `The neural term relocates` ¶1 → 표 | 86 | 66 | −20 |
| (a-7) 같은 소절 ¶2 (해석 문장 포함) | 55 | 67 | +12 |
| (b-3) `Identification accuracy` → `tab:exp2_8afc` | 82 | 61 | −21 |
| **소계** | | | **−343** (2026-09-03 보강 전 −292) |

**적용 실측 (2026-09-04). §3.4 전 항목과 §3.3 보강까지 적용 완료.** `results_v4.tex` 는 캡션 제외 **2,389 → 2,091 단어**(−298)다. 이 계수는 주석 줄 제거·이스케이프 없는 `%` 절단·`\caption{}` 제거만 적용한 것으로, 아래 예측치의 기준이 된 2,242 와는 계수기가 다르다.

**2,242 − 343 = 약 1,900 (캡션 제외).** 기준 논문 1,858 의 **1.03배**이고, 수치 밀도는 8.3/100w 에서 약 5/100w 로 내려간다. (a-5)–(a-7)·(b-3) 보강 전 예상은 1,950 이었고, 그 값으로 §0.1 의 개정 목표를 잡았다. 보강 후 실측이 목표 아래로 내려가므로 **목표 1,950 은 그대로 두고** 초과 달성분 약 40 단어는 여유로 남긴다. §3 의 종전 목표 1,800 과의 차이 110 은 (a-3) 의 보호 문단 두 개에서만 나올 수 있다.

#### 선행 조건 네 가지

이 절의 절감은 전부 "수치를 표로 옮긴다"에 의존하므로, **표가 먼저 존재해야 본문을 줄일 수 있다.**

1. `tab:exp2_geometry` **신설** (§S13). (b-1)·(b-2) 의 −128 이 전부 여기에 걸려 있다.
2. ✅ `tab:modelfits` **행·열 확장** (§S11). 선택 조합과 차순위 조합을 행으로, $\overline{L}_{\rm test}$ IQR 을 열로 넣었다.
3. ✅ `tab:fit_stability` **신설** (§S12). 분리도 $d$, 게이트 통과 조합 수, 격자 백분위, 원자별 $\Delta\overline{L}$ 과 폴드 수, 소거별 argmin, 경계 포화율, 기저별 파라미터 IQR 을 담는다. 분리도는 모형이 아니라 선택 통계이므로 `tab:modelfits` 가 아니라 이 표로 갔고, (a-1) 문안의 `\cref` 도 이 표를 가리킨다.
4. ✅ `tab:exp2_8afc` **신설** (§S13). 참가자 2 × 조건 3 의 정확도와 Wilson 95% 구간($n = 64$).

표 네 건을 만들지 않은 채 본문만 줄이면 보고되지 않는 수치가 생긴다. 순서는 **표 신설 → 본문 교체**이다.

#### §3.3 과의 관계

§3.3 의 판정이 "복원하지 않고 한 문장만 보강"으로 확정되었으므로 **이 절의 합계에 미치는 영향은 +25 단어뿐이다.** 최종 예상은 **약 1,910** 이고 기준 논문 1,858 의 1.03배다. 종전 §3.3 이 상정했던 +250(약 2,175)은 더 이상 고려 대상이 아니다.

---

## 4. Discussion — 1,406 → **1,023 실측** (2026-09-04 §4.2 Limitations · §4.3 P2 · §4.3b Conclusion **본문 적용 완료**)

### 4.1 현황 — 분량이 아니라 구성이 문제다

Discussion 은 기준 논문의 1.08배로 네 절 중 유일하게 목표 범위 안에 있으나, **Limitations 다섯 문단 513 단어가 Discussion 의 36% 를 차지한다.** 여기에 §4.2 구판(+118)과 §4.4(+40)를 얹으면 608 단어(44%)가 되어 한계가 기여를 덮는다. 2026-09-04 사용자 판정에 따라 Limitations 를 **두 문단으로 줄이고**, 구판 문안(전처리 의존성 전량 공개, 3문단 185 단어)은 폐기한다. 그 문안의 수치는 전부 이미 본문과 부록에 있으므로(§4.2 폐기 사유) Limitations 에서 다시 쓸 이유가 없다.

| 항목 | 현행 | 계획 | 증감 |
|---|---|---|---|
| §3.1 localization 해석 | — | — | **0.** 이미 반영됨 |
| §3.2 $\hat\beta_c$ 부호 단서 | — | — | **0.** 이미 반영됨 |
| Limitations 5문단 → 2문단 (§4.2 신판) | 513 | 234 | **−279** |
| P2 압축 (§4.3 문안) | 205 | 145 | **−60** |
| P14 삭제 (§4.3) | 51 | 0 | **−51** |
| **합계** | 1,406 | **약 1,016** | **−390** (0.78배) |

**§3.1·§3.2 는 작업 트리에 이미 적용되어 있다.** 현행 P3 이 `leaving the cortical locus of the distortion undetermined` 로 끝나고, P5 가 `The fits recover the sign of the dominant confusion-axis term. No recovery check established the magnitude on either axis` 로 적혀 있다. 두 문단 모두 §0.7 프레임과 일치하므로 추가 조치가 없다.

기준 논문보다 짧아지지만(0.78배) 감수한다. 줄어드는 390 단어 중 279 가 Limitations 에서 나오고, 기여를 서술하는 §Geometric distortion·§Correction filter·§Filter evaluation 세 소절은 건드리지 않는다. Limitations 는 Discussion 의 36% 에서 **23%** 로 내려간다.

### 4.2 Limitations — 교체 문안 (2026-09-04 개정판, 2문단 234 단어) ✅ **본문 적용 완료 (2026-09-04, 빌드 확인)**

**구판(2026-09-03, 3문단 185 단어) 폐기 사유.** 구판이 담으려던 수치와 판정은 이미 네 곳에 있다. Results `results_v4.tex:56` 이 deutan 최대 편차 영역의 V2→V1 이동과 LOSO 단일 유의 셀을 적고 `regional attribution as descriptive` 로 닫는다. Methods `methods_v2.tex:234` 가 기하를 서술량으로 다루고 표적 영역이 held-out test-loss 로 정해진다고 적는다. Discussion P3 `:33` 이 해리가 head-motion correction 에서도 성립함을 적는다. 부록 §S2(`:55`, `:63` 의 $.007 \to .077$), §S12(`:561` 의 $\hat\beta_c$ 부호), §S17(`:827` 의 순열 15 nominal / 0 surviving)이 수치 전부를 담는다. Limitations 가 이를 다섯 번째로 반복하면 한계 절이 결과 절을 다시 쓰는 형태가 되고, 리뷰어가 물을 항목을 **가리키는** 절이라는 본래 역할에서 벗어난다. 첫째 문단은 표본과 추론 범위, 둘째 문단은 분석 의존성과 측정 범위로 묶는다.

> The CVD sample is $N = 2$, one participant per subtype, with subtype assigned from Ishihara plates rather than anomaloscopy. Single-case statistics \parencite{crawford1998} support inference about each individual, and the seven controls serve only to place each CVD estimate relative to the control range. Claims about deutan or protan subtypes, and the separation of a per-person correction from a subtype-average one, require several participants within each subtype. The fitted parameters are reported without confidence intervals, because six runs per participant are too few for stable resampling.
>
> Several estimates depend on analysis choices, and the measurements cover a narrow stimulus range. The regional attribution of the geometric distortion and the sign of the protan confusion-axis term vary with preprocessing and with the reduction basis, so we report the geometry as descriptive and select filter targets by held-out test-loss (Section~\ref{sec:results:geometry}; Supplementary~\S S2, \S S12, \S S17). The two neural loss terms read different regions and moved in different directions at evaluation, so no neural endpoint is yet stable enough for a larger study, and the assumption that shifting cortical geometry toward the control reference shifts perception with it remains untested. The stimuli occupied a single lightness and chroma locus, lightness was equated for the standard observer rather than for each participant, and the scanner task directed attention away from color \parencite{brouwer2013}. Extending the correction to natural scenes and to attended color requires refitting under those conditions.

**현행 다섯 문단의 행방.**

| 현행 문단 | 단어 | 신판 처리 |
|---|---|---|
| L1 표본 (`:46`) | 111 | P1 로 압축(86). `The control cohort has to grow with it` 와 LOO $\|\hat\beta\|$ 유의검정 불가 설명은 `serve only to place each CVD estimate relative to the control range` 한 절로 |
| L2 분석 의존 (`:48`) | 67 | P2 둘째 문장 하나로. 신뢰구간 문장은 P1 마지막으로 이동한다. P5 `:38` 의 recovery check 는 식별성이고 신뢰구간은 추정 정밀도이므로 서로 대체하지 못한다(§4.2 구판의 "의도된 삭제" 판정을 번복) |
| L3 자극 궤적 (`:50`) | 97 | P2 넷째·다섯째 문장. $L^{*} = 75$, chroma $= 40$ 수치와 CIE $L^{*}a^{*}b^{*}$ 설명은 Methods 에 있으므로 삭제. 개인별 luminous efficiency 측정 제안은 `for each participant` 한 절로 |
| L4 주의 (`:52`) | 80 | P2 넷째 문장의 한 절. brouwer2013 인용은 유지, `should resolve it more sharply` 는 삭제 |
| L5 두 신경 항 (`:54`) | 158 | P2 셋째 문장 전반. 두 항이 읽는 영역, 보간 항 미채택, 세 종점의 명칭은 Results §neural_role·§filter_eval 이 이미 담으므로 삭제 |
| §4.4 지각 연결 전제 미검증 | +40 | P2 셋째 문장 후반 한 절(`the assumption that shifting cortical geometry ... remains untested`) |
| §4.2 구판 전처리 공개 | +118 | P2 둘째 문장 한 절 + 부록 포인터 셋 |

**의도된 삭제 3건.** ① 구판 셋째 문단 `The dissociation itself survives both pipelines` 는 P3 `:33` 이 이미 진술한다. ② L5 의 `Summing the two terms in a single objective therefore does not reconcile them` 은 Results §filter_eval 의 관찰을 재진술한다. ③ L5 의 미래 종점 세 요건(`stable across preprocessing, defined on a region fixed in advance, and shared between the fit and the evaluation`)은 `no neural endpoint is yet stable enough for a larger study` 로 줄인다. 세 요건을 남기고 싶다면 Limitations 가 아니라 Conclusion 마지막 문장에 한 절로 두는 편이 자리에 맞는다.

### 4.3 그 대신 줄일 곳 — P2 압축 · P14 삭제 (2026-09-03 문안 유지)

| 문단 | 단어 | 조치 |
|---|---|---|
| P2 (요약, `discussion_v3.tex:30`) | 205 | 결과 재진술을 줄이고 해석으로 진입. → 문안 아래, 약 −60 |
| ~~P12 (두 신경 항, `:54`)~~ | ~~158~~ | **§4.2 신판에 흡수.** 별도 문안 없음 |
| P14 (전망) | 51 | **§4.3b 문안으로 대체 (적용 완료).** 결론은 P13 에서 끝난다. "effect varied by participant and by measure" 는 §Filter evaluation 이 이미 담는다. −51 |

**P2 교체 문안 (205 → 약 145 단어)** ✅ **본문 적용 완료 (2026-09-04)**

> In both CVD participants categorical color identification was preserved while continuous hue interpolation fell to chance at hV4, and the hue geometry of both departed from the healthy-control (HC) reference by more than the controls departed from one another. We modeled that distortion as a hue rotation about the subtype confusion axis and the S-cone axis, fitted it to each participant's own neural and psychophysical measurements, and inverted it into a per-person stimulus-space filter evaluated in a second session. Under the individualized filter the elevated discrimination thresholds of both participants returned to the control range, the deployed accessibility filter left two pairs deviant in the protan participant, and the neural endpoints varied by participant and by measure. Together these results locate the CVD deficit in continuous hue geometry, which categorical decoding does not detect, and they show that an individual's own cortical color representation can be inverted into a correction filter for that individual.

### 4.3b Conclusion — P13+P14 를 Kwon 2025 형식의 한 문단으로 ✅ **본문 적용 완료 (2026-09-04, 빌드 확인)**

Kwon 2025 의 결론은 두 문장이다. `This study suggests that ...` 로 발견을 요약하고 `In the future, we anticipate ...` 로 확장 전망을 적는다. 현행 P13(87)+P14(51)=138 단어를 같은 구조의 한 문단 84 단어로 바꾼다(2026-09-04 사용자 수정 4건 반영: `rather than retinal measurements` 삭제, `within each subtype` → `CVD and control samples`, `characterize` → `quantify`, `whose solution is` → `which is`). §4.3 의 P14 삭제 항목은 이 문안으로 대체된다.

> This study shows that in two individuals with CVD categorical hue identification was preserved while continuous hue interpolation at hV4 was reduced, and that an individual's own cortical color representation can be inverted into a per-person stimulus-space correction filter. In the future, we anticipate that scaling this procedure to larger CVD and control samples will quantify the cortical color distortions of CVD, yield a fitting procedure which is stable across preprocessing and analysis choices, and deliver individualized filters whose effect on color perception can be established.

**§0.7 정합.** 첫 문장은 해리(주장)와 절차(방법 기여)만 진술하고 효능을 담지 않는다. 둘째 문장의 세 목적(특성 규명, 강건 적합, 필터 제공)은 모두 미래형이며, `whose effect on color perception can be established` 는 효능이 아직 확립되지 않았음을 전제한다. P13 의 `hue rotation about two axes` 와 `fitted parameters differed between the two` 는 P2 요약과 §Correction filter 소절이 이미 담으므로 삭제한다.

### 4.4 지각 연결 전제의 미검증 — §4.2 신판에 흡수 (2026-09-04)

서론에서 `shifting an individual's hV4 color geometry ... moves their color perception with it` 를 전제로 세우지 않기로 했으므로(§1.2) 그 명제가 검증되지 않았다는 사실은 Limitations 가 받는다. 별도 문단(2026-09-03 판, 40 단어) 대신 §4.2 신판 P2 셋째 문장의 후반 절로 넣었다. 앞 절이 두 종점의 불일치를 서술하므로 근거가 같은 문장 안에 있다.

### 4.5 부수 확인 — 부록 번호 당기기가 완료되어 있다

`supplementary.tex` 의 절이 **S1–S17** 이고 본문 참조도 S1–S17 이며, **존재하지 않는 절을 가리키는 참조가 0건**이다. 2026-09-03 재번호 뒤 본문 첫 인용 순서가 1부터 17까지 단조 증가함을 빌드로 확인했다. `MANUSCRIPT_EDITS_CONSOLIDATED.md` §1.5(c) 가 "맨 마지막에 한 번에" 로 잡아 두었던 작업이 이미 수행됐다. 그 문서의 반영 순서 표 5단계와 §1.5(c) 를 완료로 갱신할 것.

**이에 따라 이 문서와 편집 계획의 S-번호 표기를 재확인해야 한다.** 예를 들어 **대조 완료 (2026-09-02).** 통계 = §S15, `tab:exp2_geometry` 배치처 = §S13, identifiability = §S12, 스테어케이스 = §S1, 색 대응 순열 = §S17, 모형 적합 표 = §S11.

---

## 5. Supplementary — 산문 7,401 → **6,544 실측** · 기준 부록 대비 구조 정렬 (2026-09-04 **본문 적용 완료**)

> **§5.4 의 목표 4,900 과 §5.6 의 예측 5,180 은 둘 다 달성되지 않았고, 그 사유와 실측은 §5.7 에 있다.** 아래 §5.1--§5.6 은 적용 전 진단과 계획을 그대로 보존한 것이다. 실제로 무엇이 적용되었는지는 §5.7 을 본다.

> **⚠ 계수 기준 정정.** 이 절의 최초 판은 산문 7,394 로 적었으나, 같은 시점 작업 트리의 실측은 **7,401** 이다. 차이는 `\suppsection` 매크로 도입으로 헤딩이 두 줄에서 한 줄로 바뀐 것과 HC → Controls 용어 통일에서 나온다. 아래 표의 7,394 는 정정하지 않고 둔다.

> **기준 부록**: `docs/PAPER/imag_a_00440-supp.pdf`. §0 의 분량 기준으로 쓰는 Kwon et al., *Imaging Neuroscience* 3 (2025) 의 **같은 논문 부록**이다. 본문 기준과 부록 기준이 한 편에서 나오므로 §1–§4 와 같은 참조점을 쓴다.
>
> **계수 방식**: 본 원고 부록은 `supplementary.tex` 에서 주석을 제거한 뒤 `table`·`figure` 환경을 통째로 뺀 **산문 단어**를 센다. 기준 부록은 `pdftotext -layout` 추출본에서 쪽 머리글과 캡션·표 본문을 제거한 값이다. 표 본문과 캡션을 포함한 총량은 본 원고 11,750, 기준 부록 1,548 이다.

### 5.1 전체 비교

| 항목 | 기준 부록 | 본 원고 부록 | 비율 |
|---|---|---|---|
| 절 수 | 8 | 17 | 2.1 |
| 산문 단어 | 약 820 | **7,394** | **9.0** |
| 총 단어 (캡션·표 포함) | 1,548 | 11,750 | 7.6 |
| 표 | 2 | **22** | 11.0 |
| 그림 | 6 | 3 | 0.5 |
| 전시물(표+그림) 합 | 8 | 25 | 3.1 |
| `\paragraph` 단위 | 0 | **35** | — |
| 전시물이 없는 절 | 0 | **6** (S3·S4·S6·S7·S10·S15) | — |

**기준 부록의 구성 규칙은 하나다. 절 하나에 전시물 하나를 놓고, 산문은 그 전시물을 읽는 데에만 쓴다.** 여덟 절이 여덟 전시물에 정확히 대응하고, 절 5·6·7 은 산문이 아예 없이 그림과 캡션만으로 성립한다. 산문이 있는 절도 첫 문장이 전시물을 가리키며 시작한다(`In Figure S1 (a), we confirmed whether the sequence length impacts ...`, `In Table S1, we compared the performances of ConnTask with ...`). 방법을 다시 정의하는 절은 없고, 결과를 자기변호하는 문장도 없다.

**본 원고 부록은 세 가지 축에서 이 규칙을 벗어난다.**

1. **전시물 없는 절이 여섯 개다.** S3(ROI 커버리지)·S4(SRM 차원 선택)·S6(GCV)·S7(교차검증 절차)·S10(활성 수준 비교)·S15(통계)는 산문만으로 이루어져 있고, 이 중 S6·S7·S15 는 내용이 방법이다. 기준 부록에 이런 절이 없는 이유는 해당 내용이 그 논문 Methods 안에 있기 때문이다.
2. **절 하나가 전시물 여러 개와 `\paragraph` 여러 개를 거느린다.** S12 는 `\paragraph` 10개·표 5개·그림 1개, S13 은 `\paragraph` 9개·표 3개·그림 2개, S2 는 `\paragraph` 6개·표 2개다. 본문 Methods 가 `\paragraph` 를 8개, Results 가 5개 쓰는 것을 감안하면 **부록 한 절이 본문 한 절보다 더 잘게 쪼개져 있다.**
3. **산문이 표를 읽지 않고 옮겨 적는다.** S8 둘째 문단은 `tab:disparity_loso` 의 네 셀을 문장으로 다시 쓰고, S9 넷째 문단은 `tab:variance_explained` 의 세 값을 그대로 옮기며, S12 의 `Resample structure` 문단은 Test 1·Test 2a 표의 수치를 통째로 재진술한다.

### 5.2 절별 실측과 진단

| 절 | 산문 | `\par` | 표 | 그림 | 수치/100w | 주 진단 |
|---|---|---|---|---|---|---|
| S1 스테어케이스 임계 | 533 | 0 | 2 | 0 | 5.3 | 104셀 중 1셀의 이상치 진단에 240 단어 |
| S2 전처리·민감도 | **1,013** | 6 | 2 | 0 | 5.2 | 최대 절. 두 주제(운동 민감도 / 취득·정합 한계)가 한 절에 |
| S3 ROI 커버리지 | 75 | 0 | 0 | 0 | 12.0 | 적정 |
| S4 SRM 차원 선택 | 133 | 0 | 0 | 0 | 14.3 | 적정 |
| S5 대체 디코더 | 428 | 0 | 2 | 0 | 4.9 | 출처 방어 문단 1개 |
| S6 GCV | 155 | 0 | 0 | 0 | 12.3 | 방법 유도. 적정 |
| S7 교차검증 절차 | 383 | 4 | 0 | 0 | 2.3 | 4문단 중 3문단이 Methods 재진술 |
| S8 LOO disparity | 355 | 1 | 1 | 0 | 3.4 | 둘째 문단(230)이 표를 문장으로 전사 |
| S9 정렬 무관 검증 | 410 | 0 | 2 | 0 | 8.5 | `tab:variance_explained` **인용 0회**, 값은 산문에 전사 |
| S10 활성 수준 비교 | 245 | 0 | 0 | 0 | 9.4 | 적정 |
| S11 망막군 모형 | 537 | 5 | 1 | 0 | 6.1 | 단일축 논증이 2개 문단에 중복 |
| S12 식별성 검정 | **1,120** | **10** | 5 | 1 | 8.3 | 2행짜리 표 4개가 **라벨 없음**. 재진술 문단 1개(200) |
| S13 필터 평가 설계 | 772 | 9 | 3 | 2 | 7.5 | 설계·결과 두 주제. Methods 재진술 문단 1개 |
| S14 효과크기 | 223 | 0 | 1 | 0 | 10.3 | S15 와 $d_{cc}$ 정의 순환 참조 |
| S15 통계 | 165 | 0 | 0 | 0 | 9.1 | §2.2(b) 신설 Methods 절과 대부분 중복 |
| S16 정렬 강건성 | 204 | 0 | 1 | 0 | 4.4 | 표의 절반이 S5 의 전사 |
| S17 기하 비교 타당성 | 643 | 0 | 2 | 0 | 12.3 | 마지막 문단이 개념 설명 |
| **합계** | **7,394** | **35** | **22** | **3** | | |

### 5.3 검증된 중복과 결함 — 문안을 쓰기 전에 확인한 것

이 절의 판정은 전부 `supplementary.tex` 와 `main.aux` 에서 실제로 대조한 결과다.

#### (a) 표 3건이 다른 표의 셀을 그대로 담고 있다

| 중복 | 검증 결과 |
|---|---|
| **S16 `tab:alignment` 의 SRM 블록 ⊂ S5 `tab:loro_decoders` · `tab:loco_decoders` 의 forward-encoding 행** | 24셀 전부 일치. LORO SRM V1 `0.542/0.604/0.625` = S5 FE V1 `0.542/0.604/0.625`, LOCO SRM hV4 `0.470/0.271/0.104` = S5 FE hV4 `0.470/0.271/0.104`. 어긋나는 셀은 반올림 차 0.001 이 두 개뿐이다 |
| **S2 `tab:interp_arms` 의 Primary 정확도 열 ⊂ S16 `tab:alignment` 의 Procrustes 블록** | 9셀 전부 일치. HC V1 `0.393`, hV4 `0.456`, deutan hV4 `0.250`, protan hV4 `0.125`, LORO hV4 `0.488/0.375/0.375`. `tab:interp_arms` 가 새로 담는 것은 $p$ 값과 HMC 팔뿐이다 |
| **S2 `tab:motion_arms` 의 Primary 두 열 = S8 `tab:disparity_loso` 의 $t$·$p$ 열** | 캡션이 스스로 인정한다(`The two primary-pipeline columns restate \cref{tab:disparity_loso}`). 16셀 일치 |

세 건 모두 "두 팔" 또는 "두 공간"을 나란히 놓은 표이고, 그 **첫 열이 다른 표 전체**다. 기준 부록에는 같은 수를 두 번 인쇄한 표가 없다.

#### (b) 표 5건이 어디에서도 인용되지 않는다

- `tab:variance_explained`(Table S9): `\label` 한 줄이 원고 전체에서 유일한 등장이다. 그 값 `0.331 / 0.416 / g = -1.26` 은 S9 산문에 따로 적혀 있어서, 독자는 표를 보지 않고도 값을 얻고 표는 참조 없이 떠 있다.
- S12 의 Test 1·Test 2a·Test 2b·Test 2c 표 4건: `\caption` 은 있고 `\label` 이 없다. 번호는 배정되지만 어떤 `\cref` 도 가리키지 못한다.

#### (c) ⚠ §0.0 의 부록 표 번호 대응표가 뒤 8행에서 틀렸다

`main.aux` 가 배정한 실제 번호는 다음과 같다. S12 의 라벨 없는 표 4건이 **S11–S14 를 소비**하므로, 그 뒤 표가 전부 4 만큼 밀려 있다.

| 라벨 | §0.0 표기 | **실제 (`main.aux`)** |
|---|---|---|
| `tab:jnd_baseline` … `tab:modelfits` | S1 … S10 | S1 … S10 (일치) |
| (라벨 없는 식별성 표 4건) | 미기재 | **S11 · S12 · S13 · S14** |
| `tab:fit_stability` | S11 | **S15** |
| `tab:exp2_8afc` | S12 | **S16** |
| `tab:exp2_loro` | S13 | **S17** |
| `tab:exp2_geometry` | S14 | **S18** |
| `tab:effect_sizes` | S15 | **S19** |
| `tab:alignment` | S16 | **S20** |
| `tab:frozen_control` | S17 | **S21** |
| `tab:color_specificity` | S18 | **S22** |

본문은 전부 `\cref` 를 거치므로 **빌드된 원고에는 오류가 없다.** 틀린 것은 §0.0 의 계획 표이고, 그 표를 보고 손으로 번호를 적는 문서(`MANUSCRIPT_EDITS_CONSOLIDATED.md` 등)가 오염된다. 아래 (5.4 S12) 의 표 병합을 적용하면 라벨 없는 표 4건이 하나로 합쳐지면서 번호가 다시 당겨지므로, **§0.0 의 표는 병합 이후에 한 번만 갱신한다.**

#### (d) 같은 방어 문장이 세 번 나온다

`Individual cells of this grid are descriptive and support no claim in the main text.` 가 S2 에 두 번, S17 에 한 번 있다. 세 자리 모두 표 바로 뒤다. 한 번만 남기고, 나머지는 해당 표의 캡션 마지막 절로 넣는다.

### 5.4 절별 조치

> 예상 단어는 아래 문안이 없는 항목의 경우 **추정치**이며, 실측은 적용 후에 다시 낸다.

| 절 | 현행 | 조치 | 예상 |
|---|---|---|---|
| S1 | 533 | 셋째 문단(orange–yellow 이상치 진단 240)을 **약 60 단어로 압축**. 렌더링·절단 배제 논증과 `9 of 13 blocks` 논증은 삭제하고, 이상치의 크기·원인 판정·보고 방침만 남긴다. 검열 문단(60)은 `tab:jnd_baseline` 캡션이 이미 담으므로 삭제 | 300 |
| S2 | 1,013 | **두 절로 분리.** S2a = 두 파이프라인·disparity·분류/보간·세션 2(운동 민감도), S2b = 자화율 왜곡·정합(취득 한계). `tab:motion_arms` 는 **Primary 두 열을 삭제**하고 HMC 팔만 남긴 뒤 `tab:disparity_loso` 를 가리킨다. `Registration` 두 문단(300)에서 fMRIPrep·BBR 기각 경위는 결정과 그 근거 한 문장으로 줄이고, 얕은 최적값 측정(0.9–4.2 mm, 1.9/9.4 mm)은 유지한다 | 620 |
| S3 | 75 | 유지 | 75 |
| S4 | 133 | 유지 | 133 |
| S5 | 428 | `The correlation readout entered this comparison as the incumbent`(55) 삭제. 출처 방어는 코드 공개가 대신한다. `Two rows are constant-output artifacts` 후반(제외된 세 변종, 45)은 `tab:loco_decoders` 캡션으로 이관. **S14 의 인코더 전이 문단(115)을 이 절로 이동** | 390 |
| S6 | 155 | 유지 | 155 |
| S7 | 383 | 첫 문단(LORO/LOCO 정의 재진술)과 `Color decoding metrics`·`Voxel prediction metrics` 두 문단 삭제. 세 문단 모두 Methods §`sec:methods:loro`·§`sec:methods:encoding` 이 담는다. **남는 것은 누출 통제 결과(0.545 → 0.578)와 LOSO 문단** | 200 |
| S8 | 355 | 둘째 문단(230)에서 표 전사 네 문장 삭제. 두 추정량이 무엇을 위해 존재하는가(공통 공간 = 필터가 적합되는 표상, 대칭 LOSO = 투영 조건을 맞춘 검정)만 남기고 수치는 `tab:disparity_loso` 로 보낸다 | 230 |
| S9 | 410 | `tab:variance_explained` 를 **`\cref` 로 인용**하고 넷째 문단의 값 전사를 삭제. 마지막 문단(`These checks concern the measurement alone` 이하 65)은 첫 문장만 남긴다 | 290 |
| S10 | 245 | 유지 | 245 |
| S11 | 537 | `Inverse-mapping behavior`(35)는 Methods §`Inverse fitting` 소관이므로 이관. `Why the cortical gain cannot recover the distortion`(110)의 단일축 논증은 `Model` 문단이 이미 진술하므로 **S-cone 축 각도(60°·74°)와 보간 결손 위치만 두 문장으로** 남긴다. `Relation to $\Delta$RDM`(30)은 `Fits` 문단 끝 한 문장으로 흡수 | 330 |
| S12 | 1,120 | **두 절로 분리.** S12a = 네 검정(Test 1·2a·2b·2c), S12b = 적합 안정성·부호 강건성·재표집 구조. **라벨 없는 2행 표 4건을 라벨 하나짜리 4행 표로 병합**(5.3c 의 번호 밀림이 해소된다). `Resample structure and recovery`(200)에서 Test 1·2a 재진술 삭제, 남기는 것은 두 축의 제약 차이와 protan 이차 분지 두 문장. `Unselected loss atom`(§2.3(E) 의 이관 목적지)은 유지 | 700 |
| S13 | 772 | **두 절로 분리.** S13a = 설계(비교자·취득·런 수 적정성·단일사례 추론), S13b = 조건별 결과(8AFC·LORO·기하·forward-tuning). `Psychophysical battery`(40)는 Methods §`sec:methods:psychophysical` 재진술이므로 삭제. `Run-count adequacy` 둘째 문단(220)의 런 맞춤 근거는 유지하되 이동 수치(0.49→0.44, 0.45→0.43, 0.25→0.33)는 셋 중 마지막 하나만 남긴다 | 520 |
| S14+S15 | 388 | **한 절로 병합** (`Statistical analysis and effect sizes`). $d_{cc}$ 정의가 S14 에 있고 S15 가 그것을 가리키며 S15 의 $t^{*}$ 식이 다시 같은 양을 정의하는 순환을 끊는다. 인코더 전이 문단은 S5 로 이동(위) | 230 |
| S16 | 204 | `tab:alignment` 의 **SRM 블록 삭제**(S5 의 forward-encoding 행과 동일), Procrustes 블록만 남기고 비교는 `\cref{tab:loro_decoders,tab:loco_decoders}` 로 건다. 셋째 문단(V1 분류 불일치)은 유지 | 150 |
| S17 | 643 | 마지막 문단(disparity 와 색 특이성의 개념 구분, 85)은 disparity 가 도입되는 S8 로 이동하거나 삭제. 반복 방어 문장 1건 삭제 | 430 |
| **합계** | **7,394** | | **약 4,900** |

절 수는 **17 → 20** 으로 늘고(S2·S12·S13 분리, S14+S15 병합), `\paragraph` 는 35 → 약 14 로, 표는 22 → **17** 로(4건 병합, 1건 열 삭제는 표 수 유지) 줄어든다. **절 수가 느는 것이 기준 부록에 맞추는 방향이다.** 기준 부록은 전시물 8개에 절 8개이고, 본 원고는 전시물 20개에 절 17개인데 그 불균형이 전부 S2·S12·S13 세 절에 몰려 있다.

### 5.5 교체 문안

#### (A) S1 셋째 문단 — 이상치 진단 (240 → 62)

현행은 렌더링 실패 가설과 검열 가설을 차례로 배제한 뒤 실수 가설을 채택하는 과정을 서술한다. 배제된 가설은 보고할 필요가 없다.

> \cref{tab:staircase_pairs} gives both staircase estimates for every pair and condition. The two staircases of a pair differed by a median of $0.015$ across the $104$ pairs, and three cells exceeded $0.10$. The largest, at $0.515$, is the protan participant's orange--yellow pair under the individualized filter, where one track settled at $0.715$ after answering correctly at a four-fold smaller separation earlier in the same block while its partner converged at $0.200$. We attribute it to a single lapse and report every threshold as the unadjusted mean of the two tracks. Using the converged track alone would move that cell from $z = +1.33$ to $z = -0.58$.

#### (B) S7 — 4문단 383 → 2문단 약 200

첫 문단과 두 지표 문단을 삭제하고, 부록에만 있는 내용인 누출 통제와 LOSO 만 남긴다.

> \paragraph{Cross-run alignment and leakage control.}
> The run-level Procrustes alignment (\S\ref{sec:methods:roi}) maps runs 2--6 onto a fixed run-1 reference by an orthogonal rotation that uses no stimulus labels, so the held-out run or color does not define the alignment frame. Re-estimating the alignment inside each fold raised forward-encoding LORO accuracy from $0.545$ to $0.578$. Leakage in the fixed-reference pipeline would predict the opposite direction, so the reported estimate is not inflated by the alignment step. That variant also replaces the run-1 reference with the training-run mean, so it bounds the leakage question rather than isolating the nesting itself.
>
> \paragraph{Leave-one-subject-out (LOSO).}
> LOSO is the cross-subject transfer of \S\ref{sec:methods:loro} and evaluates generalization to held-out participants. All eight hues enter training, so it extends LORO across participants and has no interpolation counterpart. The encoder $W$ maps the six channels onto the voxels of the participant it was fitted to, so cross-subject prediction requires a common voxel space and LOSO ran on the SRM-transformed data. For each control participant, $W$ was trained on the remaining control participants' shared-space data and tested on the held-out participant.

**삭제되는 것과 그 소재.** LORO/LOCO 정의는 `methods_v2.tex` §`sec:methods:loro`, 의사역행렬 디코딩은 §`sec:methods:encoding`, 각도 오차 90° 와 8지선다 12.5% 는 §`sec:methods:loro`, 복셀 예측의 Pearson $r$ 은 §2.3(E) 문안의 `Composite loss` 가 담는다.

#### (C) S8 둘째 문단 — 표 전사 삭제 (230 → 130)

> \paragraph{Common-space and symmetric-LOSO estimates.}
> The geometric-disparity tests (\S\ref{sec:results:geometry}) are reported primarily in the common control-trained SRM space, in which the seven controls train the shared space and each subject of interest is projected in. In that space the held-out control reference is in-sample whereas the projected CVD participant is out-of-sample. We therefore computed a symmetric leave-one-subject-out estimate as well, in which every control and CVD subject alike is projected by SVD into a space trained on the remaining six controls (Methods, \S\ref{sec:methods:rdm}). The two estimates answer different questions. The common space defines the representation the filter is fitted in, since every other stage of the pipeline operates there, whereas testing whether a participant departs from the control distribution requires the held-out participant to be projected on the same terms as the CVD participants. \cref{tab:disparity_loso} reports both estimators for all four regions under the primary pipeline, and \cref{tab:motion_arms} repeats them under head-motion correction.

#### (D) S16 첫 문단 — SRM 블록 이관 (204 → 약 150 의 첫 문단)

> The two alignment spaces agree on the pattern that carries the Results. LORO and LOCO are trained and tested within a single participant, so the main text computes them on the Procrustes-aligned amplitudes, which retain that participant's voxels at full resolution, and SRM is applied only where a comparison spans participants. \cref{tab:alignment} gives both readouts in the Procrustes space, and the forward-encoding rows of \cref{tab:loro_decoders,tab:loco_decoders} give the same readouts in the SRM space.

#### (E) S12 — 병합 표 문안

라벨 없는 2행 표 4건을 다음 하나로 대체한다. 검정별 합격 기준이 서로 다르므로 기준 열을 명시한다.

> \begin{table}[h]
> \centering
> \caption{Results of the four pre-specified identifiability checks. Test~1 assesses voxel-level parameter recovery, Test~2a the algorithm's noise floor under a null ground truth, Test~2b specificity against control pseudo-CVD carriers, and Test~2c specificity against a color-label permutation null. All four use the PCA-basis loss. No check reached its pre-specified criterion in either participant.}
> \label{tab:identifiability}
> \begin{tabular}{llccc}
> \toprule
> Test & Criterion & Deutan $(6^\circ, -42^\circ)$ & Protan $(2^\circ, +24^\circ)$ & Verdict \\
> \midrule
> 1 & $f_{10^\circ} \geq 0.5$, $|$bias$| < 10^\circ$ & $f = 0.26$; bias $(+16^\circ, -4.7^\circ)$ & $f = 0.14$; bias $(+11^\circ, -27^\circ)$ & FAIL \\
> 2a & $|$bias$| < 5^\circ$ & $|\hat\beta| = (22^\circ, 26^\circ)$; $f^{\rm origin} = 0.00$ & $(16^\circ, 24^\circ)$; $f^{\rm origin} = 0.00$ & FAIL \\
> 2b & rank$_{\rm dist} = 1.0$ & $0.875$ & $0.875$ & FAIL \\
> 2c & $p_{\rm perm} < 0.05$ & $-2.892$ vs cut $-3.136$; $p = .167$ & $-1.681$ vs cut $-3.053$; $p = .471$ & FAIL \\
> \bottomrule
> \end{tabular}
> \end{table}

Test 1 캡션에 있던 해석 두 문장(비우세 축이 잡음 바닥 아래라는 것, deutan 우세 축의 편향이 더 작다는 것)은 캡션이 아니라 본문 문단으로 내린다. 이 프로젝트의 캡션 규칙(CLAUDE.md, `측정 대상·방법·기호·검정 방향만`)에 맞춘다.

### 5.6 산술

| 조치 | 현행 | 교체 | 증감 |
|---|---|---|---|
| (A) S1 이상치 진단 + 검열 문단 | 300 | 62 | −238 |
| S2 `Registration` 2문단 압축 | 300 | 170 | −130 |
| S2 `Session-2 endpoints` 압축 | 200 | 110 | −90 |
| S2 `Susceptibility distortion` 압축 | 170 | 110 | −60 |
| S5 출처 방어 문단 + 변종 목록 → 캡션 | 100 | 0 | −100 |
| S5 ← S14 인코더 전이 문단 이동 | 0 | +115 | +115 |
| (B) S7 3문단 삭제 | 383 | 200 | −183 |
| (C) S8 둘째 문단 | 230 | 130 | −100 |
| S9 값 전사 + 마지막 문단 | 410 | 290 | −120 |
| S11 3문단 정리 | 537 | 330 | −207 |
| (E) S12 표 병합 + 재진술 문단 삭제 | 1,120 | 700 | −420 |
| S13 `Psychophysical battery` + 런 수 압축 | 772 | 520 | −252 |
| S14+S15 병합 (인코더 전이 이동분 제외) | 388 | 230 | −158 |
| (D) S16 SRM 블록 이관 | 204 | 150 | −54 |
| S17 마지막 문단 + 반복 방어 문장 | 643 | 430 | −213 |
| **소계** | | | **−2,210** |

**7,394 − 2,210 = 약 5,180.** §5.4 의 절별 예상 합계 4,900 과 280 단어 차이가 나는데, 그 차이는 위 표에 항목으로 세우지 않은 잔여 압축(S2 의 첫 두 문단, S13 의 단일사례 추론 문단, S17 의 문장 단위 정리)에서 나온다. **보수적으로 5,180 을 예상치로 잡고 목표는 4,900 으로 둔다.** 기준 부록 820 의 6.0–6.3배이며, 이 배율을 1 에 가깝게 만드는 것은 목표가 아니다. 기준 논문의 부록은 절제 실험만 담고, 본 원고의 부록은 $N = 2$ 설계가 요구하는 강건성 분석 전량과 §2·§3 이 본문에서 밀어낸 상세를 함께 담기 때문이다.

**본문 이관으로 들어오는 증가분은 이 계산에 이미 반영되어 있다.** §2.2(c) 의 스테어케이스 파라미터(+65)는 S1 에 **이미 적용**되어 있고(`supplementary.tex:22`), §2.3(E) 의 $L_{\rm LOCO}$ 목적지는 S12 에 이미 있으며, §3.5 의 선행 조건 표 네 건 중 셋이 이미 신설되었다. 미적용은 `tab:exp2_geometry` 하나이고 그것도 이미 존재한다.

### 5.7 적용 결과 — 실측 (2026-09-04, 빌드 확인) ✅ **본문 적용 완료**

**§5.6 의 예측 5,180 은 과다 절감 추정이었다.** 실제 결과는 **산문 7,401 → 6,544 (−857, 0.88배)** 이고, 총 단어는 11,750 → 10,902 이다. 예측이 어긋난 이유는 §5.4 의 항목 다수가 "문단 X 를 300 에서 170 으로 압축" 형태의 눈대중 추정이었고, 실제로 문장을 하나씩 검토하니 대부분이 서로 다른 사실을 담고 있어 삭제 대상이 아니었기 때문이다. **실제로 확보된 절감은 산문 압축이 아니라 구조 정리에서 나왔다.**

| 지표 | 적용 전 | 적용 후 |
|---|---|---|
| 절 | 17 | **18** |
| 산문 단어 | 7,401 | **6,544** |
| 총 단어 (캡션·표 포함) | 11,750 | **10,902** |
| 표 | 22 | **19** |
| `\paragraph` | 35 | **28** |
| 라벨 없는 표 | 4 | **0** |
| 인용 0회 표 | 1 | **0** |
| 본문 미인용 절 | 0 | **0** |
| 세미콜론 (산문) | 3 | **0** (수식 내 인자 구분 1건 제외) |
| 엠대시 | 0 | **0** |
| 부정 표현 | 45 | **11** |
| 원고 쪽수 | 66 | **63** |

#### 실제 수행 내역

| 항목 | 조치 |
|---|---|
| **절 분리** | 구 S12 → S12 `app:identifiability` + S13 `app:fit_stability`; 구 S13 → S14 `app:filter_eval` + S15 `app:exp2_outcomes` |
| **절 병합** | 구 S14 + 구 S15 → S16 `app:statistics`. $d_{cc}$ 를 서로 참조하던 순환이 해소됐다 |
| **S2 는 분리하지 않았다** | §5.4 의 계획을 철회했다. 뒤쪽 절반(자화율 왜곡·정합)이 전시물을 갖지 않아, 분리하면 §5.1 이 지적한 "전시물 없는 절"을 6개에서 7개로 늘리게 된다 |
| **표 중복 3건 제거** | `tab:motion_arms` 의 Primary 두 열 삭제(`tab:disparity_loso` 로 포인터), `tab:alignment` 의 SRM 블록 삭제(S5 forward-encoding 행으로 포인터), `tab:interp_arms` 캡션에 `tab:alignment` 중복 고지 |
| **표 4건 병합** | S12 의 라벨 없는 Test 1·2a·2b·2c 표를 `tab:identifiability` 하나로. 표 번호를 4칸 밀던 원인(§5.3c)이 소멸했다 |
| **고아 표 해소** | `tab:variance_explained` 를 S9 본문에서 `\cref` 로 인용하고, 산문에 전사돼 있던 세 값을 삭제 |
| **문단 이동 3건** | 인코더 전이 비교 구 S14 → S5(디코더 결과이므로), disparity 대 색 특이성 구분 구 S18 → S8(disparity 도입부이므로), 역상 존재 문단 S11 → 삭제(Methods `:250`--`:252` 가 근찾기 절차까지 전량 담는다) |
| **Methods 재진술 삭제** | S7 의 LORO/LOCO 정의 문단, S14 의 `Psychophysical battery` 문단, S12 의 Test 1·2a 재진술 문단, S5 의 출처 방어 문단 |
| **반복 방어 문장** | 3회 중 2회를 해당 표 캡션으로 이관하고 본문에는 1회만 남겼다 |
| **문체** | 두괄식으로 재배치(S1·S2·S5·S8·S9·S11·S12·S13·S15), 부정 표현 45 → 11, 콜론 1건 제거, 표 참조를 `\paragraph` 제목에서 본문 첫 문장으로 이동(`Fits (Table~\ref{...})` → `Fits.`) |

#### 본문 포인터 갱신 9건

`main.tex` 의 `\suppsection` 매크로가 `suppsec` 카운터로 번호를 배정하므로 **본문에 하드코딩된 S-번호는 없다.** 분리·병합에 따라 가리키는 라벨만 바꿨다.

| 위치 | 종전 | 신규 | 사유 |
|---|---|---|---|
| `methods:126` | `Fold construction, the leakage control ...` | `Fold construction` 삭제 | Methods §LORO·§LOCO 가 폴드 구성을 이미 진술한다 |
| `methods:232` | `app:identifiability` | `app:identifiability` + `app:fit_stability` | 통제 위양성률은 Test 2b, 적합 크기 분포는 통제 LOO 앵커다 |
| `methods:261` | (없음) | `app:exp2_outcomes` 신설 | S15 의 최초 인용. 이 자리가 있어야 첫 인용 순서가 단조로 유지된다 |
| `methods:268` | `app:effect_sizes` + `app:statistics` | `app:statistics` 1회 | 병합에 따라 한 문단에 같은 절을 두 번 가리키던 중복 해소 |
| `results:32` | `app:effect_sizes` | `app:decoders` | 인코더 전이 비교가 S5 로 이동했다 |
| `results:115` | `app:identifiability` | `app:fit_stability` | 파이프라인 간 부호 안정성 진술이다 |
| `discussion:41` | `app:identifiability` | `app:identifiability` + `app:fit_stability` | 기저 의존은 식별성, 전처리 의존은 안정성이다 |
| `discussion:51` | `app:identifiability` | `app:fit_stability` | 같은 사유 |

#### 검증

빌드 오류 0, 미정의 참조 0, 표·그림 22건 전부 인용됨, 절 18개 전부 본문에서 인용됨, 첫 인용 순서 S1–S18 단조 증가.

#### 남은 차이에 대한 판단

**6,544 는 기준 부록 820 의 8.0배이고, 추가 절감은 보고 가능한 내용을 지워야만 나온다.** 남은 분량의 소재는 다음과 같다. S2 886(두 파이프라인 서술은 COBIDAS 필수 보고), S18 568(그중 약 200 은 2026-09-04 별도 편집이 추가한 protan V1 한 칸 이동 분석이므로 건드리지 않았다), S12+S13 992(그중 $L_{\rm LOCO}$ 정의 약 150 은 §2.3(E) 가 Methods 에서 가리키는 목적지다), S14+S15 727(런 맞춤 근거는 exp2 의 모든 신경 지표가 의존한다). **§0.1 의 목표 표에 부록 행을 추가한다면 4,900 이 아니라 6,500 으로 적어야 한다.**

## 6. Author Contributions — 전체 이름 산문 형식으로 교체 (2026-09-04 **본문 적용 완료**)

기준 논문(`imag_a_00440`)의 Author Contributions 는 저자마다 **전체 이름을 문장 주어로 반복**하는 산문이다. `main.tex` 의 종전 문안은 다른 IN 게재본(doi:10.1162/IMAG.a.55)을 따라 이니셜과 세미콜론으로 CRediT 역할을 나열했다. 사용자 지시에 따라 기준 논문 형식으로 교체했다.

**역할 배정은 하나도 바뀌지 않았다.** 종전 문안의 CRediT 항목 전부가 새 산문에 대응한다.

| 저자 | CRediT (종전) | 새 문안의 대응 절 |
|---|---|---|
| Jinil Kim | 12개 전부 | `led the conceptualization and the methodology` / `wrote the analysis software` / `collected ... curated and validated` / `led the formal analysis and the interpretation` / `produced the figures` / `administered the project` / `drafted the original manuscript` |
| Albert Minkue Cho | 8개 | `contributed to the conceptualization and the methodology` / `participant recruitment and data collection and curation` / `part of the formal analysis` / `shared responsibility for project administration` / `reviewed and edited` |
| Jungwoo Seo | 4개 | `in a supporting role` / `took part in data collection` / `reviewed and edited` |
| Jiook Cha | 7개 | `supervisory role` / `conceptualization and the methodology` / `validated the analyses` / `provided the imaging and computational resources` / `reviewed and edited` |
| 전원 | Funding acquisition | 마지막 문장 `All four authors applied jointly for the funding that supported this work.` |

`Investigation` 은 종전 주석이 기록한 매핑(`data collection` / `recruitment` → Investigation)을 그대로 따라 `data collection`·`participant recruitment` 로 풀었고, `Formal analysis` 는 같은 주석의 매핑(`result interpretation` → Formal analysis)에 따라 Jinil Kim 항목에서 `the formal analysis and the interpretation of the results` 로 함께 진술했다. 매핑 근거 주석은 `main.tex` 에 유지했고, 형식 변경의 근거와 CRediT 대조표를 주석으로 추가했다.

**Editorial Manager 제출 양식과의 정합에 유의할 것.** 그 양식은 역할을 taxonomy 용어와 기여 정도(supporting 등)로 따로 수집하므로, 본문이 산문이 되어도 양식 입력은 위 표의 CRediT 열을 그대로 쓴다.
