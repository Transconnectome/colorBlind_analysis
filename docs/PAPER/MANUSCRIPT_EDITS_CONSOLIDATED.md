# 원고 수정 종합 — 한 번에 반영할 전체 목록 (2026-08-16)

> **이 문서 하나만 보고 `.tex` 를 수정한다.** `REVISION_PLAN_HMC_DISCLOSURE`(M1–M9) · `REVISION_PLAN_PRESUBMISSION_2026-08-10`(A–I) · `STATUS_ADDITIONAL_ANALYSIS`(§5·§6) 에 흩어져 있던 확정 수정안을 **대상 파일 순서로** 재배열했다. 원 문서의 항목 ID 는 추적을 위해 그대로 붙여 둔다.
>
> **줄번호는 2026-08-16 에 실제 파일과 대조해 확인했다.** 인용된 「현행」 문구는 원고에서 그대로 가져온 것이다.

---

## 0. 반영 순서

| 단계 | 이유 |
|---|---|
| **1. §7 형식 (I3 → I4)** | I3(`\S S…` 참조 번호표 stale)를 먼저 고쳐야 아래 모든 신설 참조를 **한 번만** 검증한다 |
| **2. §5 Supplementary** | A(3-arm 표)가 §S2 를 신설하고 M-§S2 가 거기에 표를 얹는 구조. 역순이면 §S2 를 두 번 재편 |
| **3. §2 Results → §3 Discussion → §1 제목·초록** | 초록은 본문이 확정된 뒤 마지막에 |
| **4. §6 그림** | 별표 제거는 조판 마지막 |

**차단 항목**: **I2 (데이터 공개 방침)** — IRB 확인이 투고 저널 관리 에이전트 쪽에서 진행 중. 결론 전까지 Methods 문장과 Data availability 절을 **둘 다 비워 둔다**(한쪽만 채우면 상충한다).

---

## 1. `main.tex` — 제목·초록

### 1.1 제목 `main.tex:63` — M9

**현행**

> Individual-specific distortion of cortical hue geometry in color vision deficiency informs personalized color correction

**문제**: `Individual-specific` 이 정확히 무너진 주장이다. deutan V2 는 arm 간 **방향 역전**(.040 → .825), protan V1 은 .007 → .077 로 약화. `CLAUDE.md` Policy 의 "specificity claim 금지" 와도 정면 충돌한다. `cortical hue geometry` 는 이미 정확하므로 유지한다.

**후보**

| # | 문안 | 겨냥 |
|---|---|---|
| **T4** | From cortical hue-geometry distortion to individualized stimulus-space correction in color vision deficiency | **Imaging Neuroscience** — 두 기여를 모두 담음 |
| T1 | Hue identity and hue geometry dissociate in the cortical color representation of color-vision-deficient observers | JNeurosci — 해리가 finding. `From A to B` 형식을 review 로 읽는 경향이 있어 선언형이 안전 |
| T2 | Inverting an individual's cortical color representation into a stimulus-space correction filter | 방법 단독 강조 |
| T3 | Preserved categorical decoding with disrupted continuous hue interpolation in color vision deficiency | 보수적 대안 |

**`hue-representation` 은 쓰지 않는다.** 8색 범주 식별은 두 arm 전부에서 보존된다(최저 셀 deutan V1 hmc 0.229 vs chance 0.125). "표상이 왜곡되었다"고 쓰면 살아 있는 절반까지 죽은 것으로 진술하게 되고, 이는 본 논문의 핵심 대비(해리)를 제목이 스스로 지우는 것이다.

### 1.2 초록 중간 `main.tex:89` — M7

**현행**

> All eight colors remained decodable from cortical activity in both CVD participants, whereas the continuous hue geometry departed from controls, **differently in each individual**.

**교체**

> All eight colors remained decodable from cortical activity in both CVD participants, whereas the continuous hue geometry departed from controls in both. The two deviations differed in fitted direction, although their precise magnitude and cortical localization were sensitive to analysis choices.

### 1.3 초록 강점 선제 제시 `main.tex:89` — F2

현재 robustness 근거가 전부 부록에만 있어 **방어 자세로 읽힌다.** 통제군 문장 뒤에 한 구를 넣어 **강점으로** 배치한다.

> In controls, continuous hue interpolation was supported at hV4 alone, and that result held under four preprocessing variants with a cross-variant reliability of ICC = 0.83.

### 1.4 초록 마지막 `main.tex:89` — M8

**현행**

> This study identifies a previously uncharacterized geometric distortion of the cortical color representation in CVD and introduces, to our knowledge, the first cortically grounded framework for individualized color correction. **Systematic studies can quantify these distortions and provide a new class of personalized filters.**

**문제**: 마지막 문장이 **약속**이다(`can quantify ... and provide`). 검토자가 제기한 **intervention identifiability** 에 초록 차원의 답이 없다.

**교체 (IN 판 — 한계로 닫음)**

> These findings support studying CVD as an individual-level distortion of cortical hue geometry, alongside its established retinal characterization. The inversion step provides what is, to our knowledge, the first framework for deriving a color correction from an individual's own cortical color representation. Which individual distortions, and which derived filters, are robust, identifiable, and generalizable remains to be established.

**JNeurosci 판**: 위 3문장의 **2·3 순서를 교체해 신규성으로 닫는다.** 초록을 한계로 끝내면 IN 에서는 신뢰를 벌지만 JNeurosci 편집자에게는 *저자 스스로 예비연구라고 진술한다* 로 읽힐 수 있다.

**설계 근거**

| 요소 | 이유 |
|---|---|
| `support studying … as` | 사실 주장이 아니라 **연구 프로그램** 진술. 개인 수준 유의성이 무너졌으므로 이 수위가 상한 |
| `cortical hue geometry` | 범주 성분은 보존된다. 제목과 같은 논리 |
| `alongside its established retinal characterization` | 망막 문헌과 대립각을 세우지 않는다 |
| `first framework … to our knowledge` | 기여 2 의 유일한 신규성 표지. 삭제하면 방법 기여가 초록에서 사라진다 |
| `robust, identifiable, and generalizable` | 검토자 지적을 **어휘 수준에서 정면으로** 받는다 |

---

## 2. `Results/results_v4.tex`

### 2.1 `:38` 뒤 — B · 강건성 단서

HC 게이트 문장 뒤에 한 문장을 넣어 **전처리 강건성을 본문에 올린다**(현재 부록 전용).

> This localization held under four preprocessing variants, and the cross-variant reliability of the interpolation metric was highest at hV4 (ICC$_{2,1} = 0.83$) and near zero at V1 (Supplementary~\S S2).

**근거**: 현행 원고는 "hV4 만 해석 가능"을 색 라벨 순열 **하나로만** 정당화한다. ICC 는 두 번째 독립 축에서 같은 결론을 준다 — **게이트를 통과하는 유일한 ROI 가 전처리 재현성도 유일하게 높다.** 논문에 유리한 사실이다.

### 2.2 `:40` — M4 · CVD hV4 단일사례

**현행 마지막 문장**

> The deutan $p$-value reflects the power of a single-case test against $n = 7$ controls.

**교체** (앞의 수치는 그대로 둔다)

```diff
- The deutan $p$-value reflects the power of a single-case test against $n = 7$ controls.
+ The magnitude of this reduction was sensitive to preprocessing. Neither single-case contrast
+ reached significance when head-motion realignment was applied, although the control-level
+ interpolation architecture was unchanged (Supplementary~\S S2).
```

**근거**: 현행 문장은 유의성 미달을 **검정력** 탓으로 돌린다. 그 설명은 틀렸다 — HC 를 무한히 늘려도 $p$ 는 .069 에서 멈춘다. 원인은 효과크기 축소($d_{cc}$ $-3.25 \to -1.48$)다.

### 2.3 `:56` — M1 · 소제목

```diff
- \subsection{Geometric deviation localizes to a distinct ROI in each CVD case}
+ \subsection{Hue geometry departs from the control reference in both CVD cases}
```

### 2.4 `:60` — M2 · 첫 문장

**현행**

> Elevated Procrustes disparity **localized to a different ROI** in each CVD participant, V1 in the protan participant and V2 in the deutan participant (Figure~\ref{fig:geometry}B).

**교체**

> Procrustes disparity from the healthy-control reference was elevated in both CVD participants, at V1 in the protan participant and at V2 in the deutan participant (Figure~\ref{fig:geometry}B). Which region carried the elevation was sensitive to analysis choices and is reported descriptively (Supplementary~\S S2).

### 2.5 `:66` — M3 · 기여 2 로 넘어가는 다리 ★ 최우선

**현행**

> The two CVD participants differ in where the deviation lies and in how strong it is. **Because each deviation is participant-specific**, a single family-level correction would match only one of them. In each participant the continuous arrangement of hues is displaced in a direction and magnitude specific to that individual, which a personalized correction must therefore offset.

**문제**: 개인화 필요성 논거 전체가 **ROI 편재에 얹혀 있다.** 그 근거가 무너지면 기여 2 의 도입부가 함께 흔들린다.

**교체 — 안정적인 근거로 다리를 다시 놓는다**

> The two participants' deviations differ in magnitude and in the direction of the fitted hue rotation (Section~\ref{sec:results:twocomp}), and their elevated discrimination thresholds lie on different confusion axes (Section~\ref{sec:results:jnd}). A single family-level correction would therefore match only one of them.

**근거**: 적합된 $\hat\beta_c$ 의 차이($-42°$ vs $+24°$)와 심리물리 역치 축 차이는 **disparity ROI 와 독립**이고 arm 교란에 노출되지 않는다. 필터 표적 ROI 도 disparity 가 아니라 **held-out test-loss** 로 선정됐다. 개인화 논거를 그쪽으로 옮긴다.

> **단, deutan 만 3축 검증을 받았다** (§4.3 H 참조). protan $\hat\beta_c$ 는 arm 마다 부호가 바뀌므로, 이 문장은 **fitted direction 이 다르다**는 관측 진술에 머물러야 하고 "각자 안정적으로 식별된 왜곡"으로 읽히면 안 된다.

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

### 2.8 Results §3.2 첫머리 — Q1 해석 범위 진술 ★

all-ROI sensitivity 표(§5.2)를 **싣기로 했으므로** 그 앞에 해석 범위를 선언한다.

> Throughout, we interpret two quantities: the control-level localization of continuous hue interpolation, which is stable across preprocessing arms and across the color-label permutation gate, and the fitted filter parameters together with their psychophysical evaluation, which do not depend on preprocessing. The full region $\times$ arm grid is reported in Supplementary~\S S2 for completeness; individual cells within it are descriptive and are not used to support any claim in the main text.

**근거**: 표를 실으면 리뷰어는 **새로 유의해진 셀**(deutan V1, $p$ = .027)을 반드시 본다. 이 문장이 **표의 존재가 곧 주장이 아님을 사전에 선언**하고, §5.2 의 표 아래 문장이 그 셀을 막는다. 두 문장이 함께 있어야 "전부 공개했으나 본문은 견고한 것만 딛고 선다"가 성립한다.

---

## 3. `Discussion/discussion_v3.tex`

### 3.1 `:33` — M5 · localization 해석

**현행**

> In both CVD participants the deficit took the form of a structured distortion of cortical color geometry, **localized to a different area in each**. ... **That the two participants' distortions localized to different areas is consistent with the perceptual case.** Among anomalous trichromats, between-observer variability in hue scaling is 3.4 times the within-observer variability \cite{emery2021}.

**교체**

> In both CVD participants the deficit took the form of a structured distortion of cortical color geometry. ... The two participants' deviations differed in magnitude and in fitted direction, which is consistent with the perceptual case; the cortical region carrying the largest deviation was not stable across analysis choices and we do not interpret it. Among anomalous trichromats, between-observer variability in hue scaling is 3.4 times the within-observer variability \cite{emery2021}.

**근거**: `emery2021` 은 **개인차** 근거이지 **부위 편재** 근거가 아니다. 인용은 살리고 주장만 옮긴다.

### 3.2 `:44` `:46` — H · $\hat\beta_c$ 부호 강건성 (3-arm 으로 확장)

**현행 `:44`**

> The two fitted distortions diverge, with $\hat\beta_c = -42^\circ$ in the deutan participant against $+24^\circ$ in the protan participant. The sign of ...

**추가할 것**: 이 대비가 **전처리 축에서 어떻게 되는가.** 2026-08-16 에 세 arm 전부 확인 완료.

| | baseline | motreg | hmc_v2 | 판정 |
|---|---|---|---|---|
| deutan $\hat\beta_c$ | $-42$ | $-48$ | $-46$ | **부호 유지 3/3** |
| protan $\hat\beta_c$ | $+24$ | $-24$ | $-12$ | **부호 반전 2/2** |

**protan 의 반전은 분산이 아니라 배타적이다.** baseline 은 300 재표집 중 263 이 $+24$, 나머지 37 이 $0$ — **음수가 한 번도 없다.** motreg 은 218 이 $-24$, 82 가 $-34$ — **양수가 한 번도 없다.** 두 arm 의 지지집합이 부호에서 겹치지 않는다.

**deutan 에 반드시 병기할 단서**: 부호는 유지되나 교란 arm 에서 적합의 조건수가 나빠진다. 결합 `boundary_rate` 가 $.09 \to .73 / .72$ 로, **정본 선택 규칙이 쓰는 `boundary_rate < 0.5` 문턱을 두 교란 arm 모두 넘는다.** 다만 edge 적중이 세 arm 전부 $-50$ 쪽 **단측**이고 $+50$ 은 0.00 이므로 퇴화는 **크기에만** 있고 부호 주장을 훼손하지 않는다. (크기는 애초에 판정에 쓰지 않는다 — 2성분 모형 12/12 절대복구 실패 → descriptive embedding)

**문안 (§S16 신설 또는 `:46` 뒤)**

> Refitting the same loss combination on the motion-regression and the realignment arms, with every other element of the procedure held fixed, preserved the sign of $\hat\beta_c$ for the deutan participant on both arms ($-42$, $-48$, $-46$; negative in at least 95\% of resamples throughout) and reversed it for the protan participant on both ($+24$ to $-24$ and $-12$; the primary and motion-regression resample distributions do not overlap in sign). The fit for the deutan participant was more poorly conditioned on the perturbed arms, with the fraction of resamples reaching a grid boundary rising from $0.09$ to $0.72$–$0.73$; these boundary solutions lie on the same side as the median, so they bear on the magnitude rather than the sign. The psychophysical atoms do not depend on preprocessing, so the neural term is the only component that differs between arms.

**연쇄 조치**: protan ambiguity 문장을 **전처리 축까지 확장**한다(사전 확정 분기 B).

### 3.3 `:48` 뒤 — F · U10 · 균일 회전 항 부재

모형에 **균일 회전 항이 없다**는 사실을 명시. 정본 §5 가 요구했으나 미반영. (등급: 필수)

### 3.4 `:60` — 한계 문단 확장

**현행**

> Two of the reported estimates depend on analysis choices. The deutan V2 disparity elevation is significant in the common HC space and falls to a non-significant trend under the symmetric leave-one-subject-out control, whereas the protan V1 elevation is significant under both.

**교체**

> Several of the reported estimates depend on analysis choices. The deutan V2 disparity elevation is significant in the common HC space, falls to a non-significant trend under the symmetric leave-one-subject-out control, and reverses direction when head-motion realignment is applied. The protan V1 elevation is significant under the first two and falls to a trend under the third, with its direction preserved throughout. The single-case interpolation contrasts at hV4 likewise do not reach significance under realignment. The control-level result that fixes hV4 as the only interpretable region for interpolation is unaffected by any of these choices (Supplementary~\S S2). We therefore treat the region-specific deviations as descriptive rather than as established individual localizations.

### 3.5 `:69` — M6 · 결론

```diff
- whereas the continuous hue geometry departed from the HC reference, at a different cortical
- area in each.
+ whereas the continuous hue geometry departed from the HC reference in both.
```

### 3.6 Introduction 마지막 문단 — F3

기여 진술을 **해리 + 프레임워크** 2축으로 재배치. 현재는 "개인차 발견"이 1축으로 서 있다.

---

## 4. `Supplementary/supplementary.tex`

### 4.1 §S2 — A · LOCO 3-arm 표 + 범위 정정

`every neural endpoint` 문장의 **범위를 정정**하고 LOCO 3-arm 표를 신설. (등급: 필수)

### 4.2 §S2 — 재정렬 문단 신설 (`Motion sensitivity analysis` 뒤)

> \paragraph{Realignment.}
>
> Head-motion realignment was not applied in the primary pipeline. We reconstructed all functional data with the per-volume rigid transform composed into the same single-interpolation chain used by the primary pipeline, so that the two arms differ in realignment alone and not in the number of resamplings. Realignment reduced temporal SNR by $1.7$–$3.0\%$ in every ROI and changed the overlap between each atlas ROI and the acquired data by less than $0.6\%$. The neural endpoints under both arms are given in \cref{tab:hmc_robustness}.

**프레이밍 금지 사항**

| 금지 | 이유 |
|---|---|
| `we omitted a standard step` | 태만하게 읽힌다 |
| `one of several sensitivity analyses` | 표준 단계임을 감춘다 |
| `tSNR was lower, so we did not apply it` | 방어 불가. 품질로 종점을 기각하는 논리는 양날이며, 같은 논리로 종점 변화도 무시할 수 있어야 한다 |

**품질과 종점을 분리해 각각 보고하고, 어느 쪽도 다른 쪽을 기각하는 데 쓰지 않는다.**

### 4.3 §S2 — `tab:hmc_robustness` (신설)

| Endpoint | Primary | Realigned |
|---|---|---|
| HC hue interpolation at hV4 (permutation) | $p = .011$ | $p = .023$ |
| HC interpolation at V1 / V2 / V3 | n.s. | n.s. |
| Cross-arm reliability of adjacent accuracy, hV4 (ICC$_{2,1}$) | \multicolumn{2}{c}{$0.825$} |
| … V1 / V2 / V3 | \multicolumn{2}{c}{$-0.005$ / $0.471$ / $0.662$} |
| Protan hV4 vs controls | $p = .011$ | $p = .108$ |
| Deutan hV4 vs controls | $p = .054$ | $p = .242$ |
| Protan V1 disparity vs controls | $p = .007$ | $p = .077$ |
| Deutan V2 disparity vs controls | $p = .040$ | $p = .825$ (direction reversed) |

**표 아래 선제 문장 — 필수**

> No region-specific deviation was stable across arms. Cells reaching significance in one arm did not in the other, in both directions, and we do not interpret any single-arm cell.

### 4.4 §S2 / §S3 — G + BBR QC 그림

**Dice 표를 인용하지 않는다.** 아카이브 정량 지표(BBR Dice 0.33–0.50 vs MI 0.27–0.36; ROI coverage 99.95% vs 85.4%)는 **BBR 을 지지한다** — 이 지표들이 "슬랩이 뇌 안에서 잘못된 위치에 안착"하는 실패 모드에 둔감하기 때문이다. 게다가 아카이브 method3 는 FSL MNI152 로 돌아 현행 정본(MNI152NLin2009cAsym res-2)과 공간이 다르다.

**근거는 서술로만 남긴다** (2026-08-17 결정 — QC 그림 제작 제외). 방법 이력 진술이지 결과 주장이 아니므로 그림 없이 성립하며, 아래 선제 공개가 있으면 리뷰어가 Dice 를 직접 계산해도 반박이 되지 않는다. 근거는 채택 당시 기록(`notion.md:29-35`)이다.

두 층위를 **같이** 써야 완성된다.

| 층위 | 시도했고 실패한 것 | 정당화하는 것 |
|---|---|---|
| 파이프라인 | fMRIPrep 정합 전 시도 실패 | 커스텀 파이프라인을 쓴 것 |
| 정합 방법 | BBR 육안 실패 — partial FOV 에서 잘못된 경계 스냅 (10 mm 오차 위험 vs MI ~1 mm) | 커스텀 안에서 MI 를 고른 것 |

이렇게 써야 "표준을 안 썼다"가 아니라 **"표준을 시도했고, 이 취득에서 실패한 측정된 이유를 보고한다"** 가 된다. **"전뇌 중첩 지표는 BBR 을 선호하나 슬랩 오위치에 둔감하다"를 선제 공개**하는 편이 안전하다.

### 4.5 §S13 (L464-468) — C · 순환이동 대조 확장

순환이동 대조를 **색 특이성 순열**까지 확장. (등급: 필수)

### 4.6 §S15 `tab:jnd_baseline` — D · 범위 절단 각주

sub-08 orange–yellow 가 **범위 절단 하한**임을 각주. (등급: 필수)

### 4.7 §S16 신설 — H

§3.2 의 문안을 여기에 배치(또는 Discussion `:46` 뒤).

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

**산출**: `analysis/future_phase1_sensitivity/results/exp2_endpoints_arms.json`, `analysis/future_phase1_sensitivity/results/exp2_disparity_arms.json`, `derivatives/full_dataset_C010_exp2_harm_hmc{,_matched}`

---

## 5. 그림

### 5.1 `fig:geometry` (Fig 4) — Q2

**패널에서 별표를 제거하고 각주로 강등한다.**

**캡션 추가구**

> Asterisks are omitted; the region-specific elevations did not hold across preprocessing arms, and the arm-wise tests are given in Supplementary~\S S2.

**근거**: deutan V2 가 arm 에서 **방향까지 역전**했으므로(.040 → .825) 패널의 별표는 방어할 수 없다. 별표를 남기고 캡션에서만 단서를 다는 것은 그림과 캡션이 서로 다른 말을 하게 만든다 — 그림은 발표·인용에서 캡션과 분리되어 유통되므로 **패널 자체에서 제거해야 한다.**

### 5.2 `fig:loco` (Fig 3)

변경 불필요. 캡션이 이미 측정·기호·검정 방향만 기술한다 (`CLAUDE.md` figure caption 규칙 준수).

---

## 6. 형식·제출 차단 — I

| # | 항목 | 대상 | 상태 |
|---|---|---|---|
| **I3** | `\S S…` 참조 번호표가 stale — S1–S19 로 적혀 있으나 실제 파일은 **S1–S21**. 본문 참조가 이 표를 근거로 검증되었으므로 **전수 재검증** | `Supplementary/REVISION_WORKLIST.md:10-34` | **최우선** |
| **I4** | Methods 중복본 6개가 참가자 수를 `Twelve` / `Thirteen` 으로 상충 기술. `main.tex` 는 `methods_v2` 만 `\input` 하나 **코드 공개 시 읽힌다** | `Methods/methods{,_concise,_streamlined,_bibtex,_for_pi}.tex`, `*_backup.tex` | 5분 |
| **I1** | back matter 4절 `\todo{}` 실채움 (CRediT / 이해관계 / 감사 / 데이터 가용성) | `main.tex:110-146` | I2 후 |
| **I2** | **데이터 공개 방침 결정** — 기탁(OSF/OpenNeuro) vs 요청 시 제공. Methods 문장과 Data availability 절을 **함께** 고쳐야 한다 | `main.tex` + `methods_v2.tex` | **IRB 확인 대기** |

---

## 7. 원고 밖 잔여 작업

| # | 작업 | 산출물 | 왜 필요한가 |
|---|---|---|---|
| 2 | **macOS 필터 per-hue $L^*$ 실측** | 필터 ON 8색 스크린샷 + $L^*$ 표 (평균 이동 · 8색 산포) | §4.8 의 두 분기 중 하나를 확정. **배포 조건에서만 등휘도가 깨지므로 비교자 해석 전체가 여기 달려 있다** |
| ~~3~~ | ~~ses-2 ezBIDS 디페이싱~~ | `colorBlind_data/data/2nd_exp/bids_2nd_defaced` | **완료 2026-08-17.** 0 복셀 sub-08 30.9% · sub-09 35.1% (ses-1 30.9% / 33.0%), 중시상면 절단면 형상 4장 동일, 뇌 조직 손실 없음 |
| ~~4~~ | ~~exp2 재전처리 + 종점 14칸 재산출~~ | `full_dataset_C010_exp2_harm_hmc{,_matched}`, `future_phase1_sensitivity/results/exp2_endpoints_arms.json` | **완료 2026-08-17.** native 10개 중 **8개** · matched 10개 중 **5개** 역전. 두 arm 병기, 방향 주장 없음 (§4.9) |
| ~~5~~ | ~~색 라벨 ↔ 렌더 값 방향 확인~~ | 실험 스크립트 8개 주석 | **종결 2026-08-17.** 라벨이 정본(화면 관찰). 겉보기 반전은 PsychoPy 보색 렌더링 |

---

## 8. 근거 색인

| 주장 | 산출물 |
|---|---|
| 4-arm 종점 · ICC · MAE 순열 | `analysis/future_phase1_sensitivity/results/{perm_adjacent_arm_*,arm_agreement,perm_mae_arm,boot_runs_*}.json` |
| disparity arm 비교 | `analysis/validation/results/disparity_arm_{canonical,hmc_v2}.json` |
| HMC 품질 (tSNR · ROI 겹침) | `analysis/phase0_preprocessing/results/hmc_summary.csv`, `hmc_roi_comparison.json` |
| $\hat\beta_c$ 3-arm | `analysis/phase5_filter_optimization/results/filter_robustness_arms/beta_sign_three_arms.json`, `results/s10_inclusion/u2_{baseline,motreg,hmc_v2}/` |
| 필터 교차평가 | `results/filter_robustness_arms/filter_robustness_arms.json` |
| 비교자 구현 | `~/…/OneDrive-Personal/Projects/colorBlind/colorBlind_exp2.py:150,169,723,733,741,744,799` |
| SDC 미적용 정당화 | `analysis/phase0_preprocessing/results/roi_shift_summary.csv`, `figures/sdc_cohort/` |

**상세 논거**: [`REVISION_PLAN_HMC_DISCLOSURE_2026-08-15.md`](REVISION_PLAN_HMC_DISCLOSURE_2026-08-15.md) · [`REVISION_PLAN_PRESUBMISSION_2026-08-10.md`](REVISION_PLAN_PRESUBMISSION_2026-08-10.md) · [`STATUS_ADDITIONAL_ANALYSIS_2026-08-15.md`](STATUS_ADDITIONAL_ANALYSIS_2026-08-15.md) · [`FRAMING_JNEURO_IMAGINGNEURO_2026-08-16.md`](FRAMING_JNEURO_IMAGINGNEURO_2026-08-16.md) · [`FILTER_ROBUSTNESS_ARMS.md`](../../analysis/phase5_filter_optimization/FILTER_ROBUSTNESS_ARMS.md)
