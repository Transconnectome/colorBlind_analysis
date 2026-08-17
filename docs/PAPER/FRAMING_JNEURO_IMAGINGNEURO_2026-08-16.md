# 프레이밍 — JNeurosci / Imaging Neuroscience 겨냥 (2026-08-16)

> 근거: [`STATUS_ADDITIONAL_ANALYSIS_2026-08-15.md`](STATUS_ADDITIONAL_ANALYSIS_2026-08-15.md), [`REVISION_PLAN_HMC_DISCLOSURE_2026-08-15.md`](REVISION_PLAN_HMC_DISCLOSURE_2026-08-15.md)

---

## 0. 프레이밍의 출발점 — 우리가 실제로 가진 것

**전처리 축(4 arm)을 통과한 것**

| | |
|---|---|
| 8색 식별 보존 | 두 arm 전 ROI 에서 chance 1.8배 이상 |
| HC 보간은 hV4 단독 | $p$ = .011 / .013 / .002 / .023, 다른 ROI 는 어느 arm 도 통과 못함 |
| **지표 신뢰도** | hV4 ICC(2,1) = **0.825**, V1 = $-0.005$ |
| **CVD 두 명 모두 HC 평균 아래** | primary 0.250 / 0.125 · hmc 0.354 / 0.271 (HC 0.456 / 0.451) — **방향은 네 arm 전부 보존** |
| 필터 역산 8/8 exact | 수학, 전처리 무관 |
| 심리물리 전량 | 전처리 무관 |
| deutan 필터 강건성 | **시간·기저·공간 3축 전부에서 $\hat\beta_c$ 부호 유지** (−42 / −48 / −46) |

**통과하지 못한 것**

| | |
|---|---|
| CVD hV4 결손의 **유의성** | 6가지 검정 형태 전부 .10 이상 (§1) |
| 개인별 ROI 편재 | deutan V2 **방향 역전** |
| protan 필터 강건성 | 6/8 색 부호 반전; $\hat\beta_c$ 는 3축 전부에서 반전 (+24 → −24 / −12) |

**핵심 통찰**: 무너진 것은 **개인 수준 통계적 주장**이고, 살아남은 것은 **집단 수준 구조 + 방법론**이다. 따라서 프레이밍은 **개인차 발견**에서 **표상 해리 + 방법 프레임워크**로 무게를 옮겨야 한다.

---

## 1. 검정 형태를 더 시도하지 않는다 (기록)

CVD hV4 결손을 살리려 여섯 형태를 시도했고 전부 같은 답이다.

| 형태 | primary | hmc |
|---|---|---|
| Crawford–Howell 직접 | .011 | .108 |
| 개인 색라벨 순열 | **HC 도 5/7 실패** → 구분 불가 | 〃 |
| 귀무 정규화 $z$ + CH | .021 | .101 |
| 원시 $\text{obs}-\text{null}$ + CH | .013 | .101 |
| run-level bootstrap | arm CI 겹침 17–29% | 〃 |
| 연속 MAE + CH | .011 | .454 |

귀무는 arm 간에 거의 움직이지 않으므로(0.339 → 0.353) 정규화가 흡수할 것이 없다. **더 시도하면 p-hacking 이다. 종료.** 여섯 형태가 수렴한다는 사실 자체를 강건성 근거로 쓴다.

---

## 2. 제목안

| # | 제목 | 겨냥 |
|---|---|---|
| **T1** | Hue identity and hue geometry dissociate in the cortical color representation of color-vision-deficient observers | **JNeurosci** — 해리가 finding |
| **T2** | Inverting an individual's cortical color representation into a stimulus-space correction filter | **Imaging Neuroscience** — 방법이 헤드라인 |
| **T4** | From cortical **hue-geometry** distortion to individualized stimulus-space correction in color vision deficiency | **Imaging Neuroscience** — 두 기여를 모두 담음 |
| T3 | Preserved categorical decoding with disrupted continuous hue interpolation in color vision deficiency | 보수적 대안 |

**T1 권고 (JNeurosci)**: `dissociate` 가 정확하다. 우리가 가진 가장 강한 것은 **같은 복셀 패턴에서 한 성분은 살아 있고 다른 성분은 무너진다**는 대비이며, 이건 두 CVD 모두에서 네 arm 전부 성립한다. JNeurosci 는 `From A to B` 형식을 review/perspective 로 읽는 경향이 있어 선언형이 안전하다.

**T4 권고 (IN)**: T1 은 finding 만, T2 는 framework 만 담는다. T4 는 둘을 모두 담아 논문의 실제 2-기여 구조와 일치한다.

> **`hue-representation` 이 아니라 `hue-geometry` 여야 한다.** 8색 범주 식별은 두 arm 전부에서 보존된다(최저 셀 deutan V1 hmc 0.229 vs chance 0.125). "표상이 왜곡되었다"고 쓰면 살아 있는 절반까지 죽은 것으로 진술하게 되고, 이는 **본 논문의 핵심 대비(해리)를 제목이 스스로 지우는** 것이다. `geometry` 는 실제로 무너진 성분만 정확히 지목한다.

---

## 3. 주장 사다리 — 이 순서로만 쓴다

```
1  HC 에서 연속 hue 보간은 hV4 단독에서 지지된다          [n=7, 4 arm, ICC 0.83]
        ↓  측정 가능한 성질을 확립
2  두 CVD 에서 8색 식별은 보존된다                        [4 arm, chance 1.8배+]
        ↓  신호 자체는 살아 있음
3  같은 참가자에서 hV4 보간은 HC 평균 아래로 떨어진다      [4 arm 방향 보존]
        ↓  ★ 해리 — 여기가 finding
4  이 왜곡을 2축 hue 회전으로 기술하고 역산하면
   물리적으로 구현 가능한 자극공간 필터가 나온다           [8/8 exact]
        ↓
5  동결된 필터를 2차 세션에서 전향적으로 평가했다          [심리물리 우호적]
```

**3번의 표현이 관건이다.**

| 금지 | 허용 |
|---|---|
| `significantly below controls` | `below the control mean in both participants and under every preprocessing arm; the single-case contrast reached significance only in the primary arm` |
| `localized to a different area in each` | (삭제) |
| `individual-specific cortical distortion` | `individually fitted description of the distortion` |

---

## 4. 초록 재구성 (`main.tex:71`)

**현행 문제**: `departed from controls, differently in each individual` 가 무너진 주장이다.

**교체안**

> Color vision deficiency (CVD) is typically corrected with generic filters designed from a retina-based model. Such filters change how colors appear but improve discrimination only in some products and tasks, and their design omits visual cortex, where the retinal loss and the observer's partial compensation combine. Here we show that CVD dissociates two components of the cortical color representation. We scanned two adults with CVD, one with each red–green subtype, and seven healthy controls. In controls, continuous hue interpolation was supported at hV4 alone, and that result held under four preprocessing variants with a cross-variant reliability of ICC = 0.83. All eight colors remained decodable in both CVD participants at every region, whereas hue interpolation at hV4 fell below the control mean in both, under every variant. The individual magnitude of that reduction, and the region carrying the largest geometric deviation, were sensitive to analysis choices and are reported descriptively. We modeled each participant's distortion as a hue rotation about two fixed color-space axes and inverted the fit into a stimulus-space filter, exact at all eight target hues. Both participants completed a second session with the filter frozen before acquisition. Under the individualized filter the four hue-discrimination thresholds that had exceeded the control range moved within it, and color identification was preserved where the deployed accessibility filter reduced it. This small sample cannot establish superiority over that comparator, and the cortical readouts moved inconsistently. The study introduces, to our knowledge, the first framework that derives a color correction from an individual's own cortical color representation.

**바뀐 것**: ① `dissociates` 를 헤드라인 동사로 ② ICC·4-arm 을 **강점으로 선제 제시** ③ `differently in each individual` → `sensitive to analysis choices and reported descriptively` ④ 필터 동결 시점을 명시(전향적 설계가 강점).

### 4.1 마지막 문장 — 연구 프로그램 + 한계로 닫기

현행 마지막 줄은 신규성 주장 단문(`The study introduces, to our knowledge, the first framework…`)이다. 검토자가 제기한 **identifiability** 에 답하려면 여기에 프로그램 진술과 한계가 함께 와야 한다.

**교체안 (IN 판 — 한계로 닫음)**

> These findings support studying CVD as an individual-level distortion of cortical hue geometry, alongside its established retinal characterization. The inversion step provides what is, to our knowledge, the first framework for deriving a color correction from an individual's own cortical color representation. Which individual distortions, and which derived filters, are robust, identifiable, and generalizable remains to be established.

**JNeurosci 판**: 위 3문장의 **2·3 순서를 바꿔 신규성으로 닫는다.** 초록을 한계로 끝내면 IN 에서는 신뢰를 벌지만, JNeurosci 편집자에게는 *저자 스스로 예비연구라고 진술한다* 로 읽힐 수 있다.

**설계 근거**

| 요소 | 이유 |
|---|---|
| `support studying … as` | 사실 주장이 아니라 **연구 프로그램** 진술. 개인 수준 유의성이 무너졌으므로 이 수위가 상한이다 |
| `cortical hue geometry` (≠ `representational geometry`) | 범주 성분은 보존된다. T4 의 제목 논리와 동일 |
| `alongside its established retinal characterization` | 망막 문헌과 대립각을 세우지 않는다 |
| `first framework … to our knowledge` | Contribution 2 의 유일한 신규성 표지. 삭제하면 방법 기여가 초록에서 사라진다 |
| `robust, identifiable, and generalizable` | 검토자의 intervention-identifiability 지적에 **정면으로** 답하는 어휘 |

---

## 5. 저널별 포지셔닝

### 5.1 Imaging Neuroscience — **1순위 권고**

**왜 맞나**

| 우리 자산 | IN 이 보상하는 것 |
|---|---|
| 4-arm 전처리 검정, ICC, SDC 정량, 6가지 검정 형태 수렴 | **투명성·재현성 자체가 게재 가치** |
| 어디까지 말할 수 있는지 명시한 회계 | 뉘앙스 있는 결과를 벌하지 않음 |
| 방대한 부록 | 분량 제약 사실상 없음 |
| 비관습적 커스텀 파이프라인 + 그 정당화(fMRIPrep·BBR 실패, 재정렬 검정) | NeuroImage 계열 방법 독자층이 정확히 판단 가능 |

**IN 용 커버레터 축**: 이 논문은 개인 수준 신경 소견을 주장하는 논문이 아니라, **개인의 피질 표상에서 자극공간 개입을 역산하는 방법과, 그 개입의 어느 성분이 분석 선택에 견디는지를 끝까지 추적한 기록**이다.

**IN 에서는 §S2 가 약점이 아니라 세일즈 포인트다.** 다른 저널이면 숨기고 싶은 표를 IN 에서는 앞세운다.

### 5.2 JNeurosci — 2순위, 조건부

**성립 조건**: T1 처럼 **해리를 finding 으로** 세우고, 개인차 주장을 전부 뺄 것.

| JNeurosci 심사 위험 | 대응 |
|---|---|
| "N=2 로 신경과학적 발견을 주장하나" | 발견의 주체를 **HC n=7 의 hV4 특이성**으로 옮기고, CVD 는 **case series** 로 명시. Crawford–Howell 은 단일사례 검정임을 전면에 |
| "Brouwer & Heeger 재현 아닌가" | 재현임을 **먼저 인정**하고, 신규성은 ① 그 성질이 CVD 에서 선택적으로 무너진다 ② 그 기술을 역산해 개입을 만든다 로 배치 |
| "개인 소견이 전처리에 흔들린다" | **선제 공개.** 6형태 수렴 표가 오히려 방법적 신뢰를 준다 |
| "필터 효과가 일관되지 않는다" | 우월성 주장을 하지 않는다. 전향적 **feasibility** 로 한정 |

**JNeurosci 는 Brief Communication 형식도 고려할 만하다** — 해리 + 프레임워크만 압축하고 robustness 는 부록으로 밀면 분량 대비 밀도가 맞는다.

### 5.3 두 저널 동시 준비 전략

본문은 **한 벌**로 쓰고 강조점만 바꾼다.

| | JNeurosci | Imaging Neuroscience |
|---|---|---|
| 제목 | T1 (해리, 선언형) | **T4** (왜곡 → 교정) |
| 초록 첫 문장 | `CVD dissociates two components...` | `We derive a stimulus-space color correction from an individual's cortical color representation...` |
| 초록 마지막 (§4.1) | 신규성으로 닫음 (2·3 순서 교체) | **한계로 닫음** |
| §S2 위치 | 부록 뒤쪽 | **부록 앞쪽, Methods 에서 명시 인용** |
| ICC | 한 줄 | 표 + 본문 언급 |
| 강조 | 신경과학적 해리 | 방법·재현성 |

### 5.4 투고 순서 — IN 우선 (2026-08-16 개정)

이전 권고는 JNeurosci 선행이었고, 그 근거의 상당 부분은 **IN 의 IF 부여 여부가 미확인**이라는 점이었다. 확인 결과 **IN 초년도 IF = 3.0**(창간 연도 저volume 효과 포함, 상승 추세)이므로 "기관 실적 미인정" 이라는 결격 사유는 소멸한다.

| | JNeurosci | Imaging Neuroscience |
|---|---|---|
| IF | ~4.4 | **3.0** (상승 추세) |
| 게재 확률(수정안 반영 후) | 15–25% | 50–65% |
| fit | 조건부 — T1 프레이밍으로 자격은 생김 | **§S2 가 세일즈 포인트** |
| 기관 실적 | 인정 | **인정** |

**IF 격차가 1.5배로 좁혀진 이상 fit 논거가 이긴다.** ① 이 논문은 CVD n=2 와 불안정한 개인 소견이라는 구조 때문에 JNeurosci 에서 구조적으로 불리하고(집단 수준에 남는 것은 B&H 재현), ② IN 에서는 4-arm 검정·ICC 0.83·6형태 수렴·커스텀 파이프라인 실패 기록이 **방어 대상이 아니라 게재 사유**가 된다.

**단, 마감 여유가 9개월 이상이면 JNeurosci 선행도 합리적이다.** desk reject(~35%)는 2–4주로 끝나 하방이 얕고, 심사 후 거절(~45%)이면 리뷰가 IN 투고 자산이 된다. **결정 기준은 IF 가 아니라 일정이다.**

---

## 6. 이 프레이밍이 요구하는 원고 작업

`REVISION_PLAN_HMC_DISCLOSURE_2026-08-15.md` 의 M1–M7 과 **충돌하지 않는다.** 다만 추가 3건:

| # | 작업 |
|---|---|
| F1 | 초록 전면 교체 (§4) — M7 을 흡수·확대 |
| F2 | Results §3.2 에 **4-arm + ICC 를 강점으로** 한 문장 추가 (현재 §S2 에만 있음) |
| F3 | Introduction 마지막 문단의 기여 진술을 **해리 + 프레임워크** 2축으로 재배치 |

**F2 가 프레이밍의 핵심이다.** 지금은 robustness 가 전부 부록에 있어 방어 자세로 읽힌다. `hV4 alone, under four preprocessing variants, ICC = 0.83` 을 **Results 본문**에 올리면 같은 사실이 **강점**으로 읽힌다.
