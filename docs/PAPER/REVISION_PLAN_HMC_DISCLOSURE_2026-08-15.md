# HMC sensitivity 반영 — 원고 수정안 (2026-08-15)

> **원칙: 최소 충분 disclosure.** 분석 이력을 보고하는 것이 아니라 **최종 sensitivity 결과**만 보고한다. 유일한 금지선 = **sensitivity 결과를 생략하면서 강한 주장을 그대로 유지하는 것.**
>
> **근거**: [`STATUS_ADDITIONAL_ANALYSIS_2026-08-15.md`](STATUS_ADDITIONAL_ANALYSIS_2026-08-15.md) §3.4g–3.4i **산출**: `analysis/future_phase1_sensitivity/results/{boot_runs_*,arm_agreement,perm_mae_arm}.json`, `analysis/phase0_preprocessing/results/hmc_summary.csv`, `analysis/validation/results/disparity_arm_{canonical,hmc_v2}.json`

---

## 0. 무엇이 살아남고 무엇이 무너지는가

| 결과 | 정본 | hmc arm | 판정 |
|---|---|---|---|
| **HC hV4 보간 게이트** | $p$ = .011 | $p$ = .023 | **유지** (4 arm 전부) |
| **hV4 LOCO 지표 신뢰도** | — | ICC(2,1) = **0.825** (V1 −0.005) | **신규 자산** |
| CVD hV4 단일사례 (protan) | $p$ = .011 | $p$ = .108 | 유지 안 됨 |
| CVD hV4 단일사례 (deutan) | $p$ = .054 | $p$ = .242 | 유지 안 됨 |
| **protan V1 disparity** | $p$ = .007 | $p$ = .077 | 약화, **방향 유지** |
| **deutan V2 disparity** | $p$ = .040 | $p$ = .825 | **방향 역전** ($t$ +2.1 → −1.0) |

**deutan V2 는 약화가 아니라 부호 반전이다.** 독립 분석(LORO 색대응, 2026-08-05)에서도 같은 반전이 나왔다($p$ = .882), protan V1 도 같은 값으로 약화됐다($p$ = .079). **서로 다른 두 교란이 같은 값으로 수렴한다.**

**영향받지 않는 것 — 기여 2.** 필터 표적 ROI 는 disparity 가 아니라 **held-out test-loss** 로 선정됐다(deutan V2 = 4-ROI 1위 −2.359; protan V1 은 하드코딩이나 gate 통과 ROI 전부 동일 해). 필터 파라미터·배포본 불변. 다만 **disparity–필터 ROI 일치를 시사하는 서술은 삭제**해야 하며, 이는 2026-08-05 에 이미 결정된 조치다.

---

## 1. 본문 수정 — 6곳

### M1. `Results/results_v4.tex:56` — 소제목

```diff
- \subsection{Geometric deviation localizes to a distinct ROI in each CVD case}
+ \subsection{Hue geometry departs from the control reference in both CVD cases}
```

**근거**: localization 이 arm 간 유지되지 않는다. 제목이 established finding 을 선언한다.

### M2. `results_v4.tex:60` — 첫 문장

**현행**

> Elevated Procrustes disparity localized to a different ROI in each CVD participant, V1 in the protan participant and V2 in the deutan participant (Figure~\ref{fig:geometry}B).

**교체**

> Procrustes disparity from the healthy-control reference was elevated in both CVD participants, at V1 in the protan participant and at V2 in the deutan participant (Figure~\ref{fig:geometry}B). Which region carried the elevation was sensitive to analysis choices and is reported descriptively (Supplementary~\S S2).

**근거**: 관측 자체는 보고하되 "localize" 라는 인과·확정 어휘를 뺀다.

### M3. `results_v4.tex` §3.3 마지막 문단 — 기여 2 로 넘어가는 다리

**현행**

> The two CVD participants differ in where the deviation lies and in how strong it is. Because each deviation is participant-specific, a single family-level correction would match only one of them.

**문제**: 개인화 필요성 논거가 **ROI 편재에 얹혀 있다.** 그 근거가 무너지면 기여 2 의 도입부가 함께 흔들린다.

**교체 — 안정적인 근거로 다리를 다시 놓는다**

> The two participants' deviations differ in magnitude and in the direction of the fitted hue rotation (Section~\ref{sec:results:twocomp}), and their elevated discrimination thresholds lie on different confusion axes (Section~\ref{sec:results:jnd}). A single family-level correction would therefore match only one of them.

**근거**: 적합된 $\hat\beta$ 의 차이($-42°$ vs $+24°$)와 심리물리 역치 축 차이는 **disparity ROI 와 독립**이며 arm 교란에 노출되지 않는다. 개인화 논거를 그쪽으로 옮긴다.

### M4. `results_v4.tex:40` — CVD hV4 단일사례

**현행**

> Both CVD participants fell below the control distribution at hV4, significantly so in the protan participant ($t = -3.04$, $p = 0.012$, $d_{cc} = -3.25$) and with a large effect in the deutan participant ($t = -1.89$, $p = 0.054$, $d_{cc} = -2.02$). ... The deutan $p$-value reflects the power of a single-case test against $n = 7$ controls.

**조치**: 수치는 그대로 두고 **마지막 문장을 교체**한다.

```diff
- The deutan $p$-value reflects the power of a single-case test against $n = 7$ controls.
+ The magnitude of this reduction was sensitive to preprocessing. Neither single-case contrast
+ reached significance when head-motion realignment was applied, although the control-level
+ interpolation architecture was unchanged (Supplementary~\S S2).
```

**근거**: 현행 문장은 유의성 미달을 **검정력** 탓으로 돌린다. 그 설명은 이제 틀렸다 — HC 를 무한히 늘려도 $p$ 는 .069 에서 멈춘다. 원인은 효과크기 축소($d_{cc}$ −3.25 → −1.48)다.

### M5. `Discussion/discussion_v3.tex:33` — localization 해석

**현행 (2곳)**

> In both CVD participants the deficit took the form of a structured distortion of cortical color geometry, **localized to a different area in each**. ... **That the two participants' distortions localized to different areas is consistent with the perceptual case.** Among anomalous trichromats, between-observer variability in hue scaling is 3.4 times the within-observer variability \cite{emery2021}.

**교체**

> In both CVD participants the deficit took the form of a structured distortion of cortical color geometry. ... The two participants' deviations differed in magnitude and in fitted direction, which is consistent with the perceptual case; the cortical region carrying the largest deviation was not stable across analysis choices and we do not interpret it. Among anomalous trichromats, between-observer variability in hue scaling is 3.4 times the within-observer variability \cite{emery2021}.

**근거**: `emery2021` 인용은 **개인차** 근거이지 **부위 편재** 근거가 아니다. 인용은 살리고 주장만 옮긴다.

### M6. `discussion_v3.tex:69` — 결론

```diff
- whereas the continuous hue geometry departed from the HC reference, at a different cortical
- area in each.
+ whereas the continuous hue geometry departed from the HC reference in both.
```

### M7. `main.tex:71` — 초록

**현행**

> All eight colors remained decodable from cortical activity in both CVD participants, whereas the continuous hue geometry departed from controls, **differently in each individual**.

**교체**

> All eight colors remained decodable from cortical activity in both CVD participants, whereas the continuous hue geometry departed from controls in both. The two deviations differed in fitted direction, although their precise magnitude and cortical localization were sensitive to analysis choices.

**근거**: 초록이 가장 강한 주장을 담고 있고, 가장 널리 인용된다. 여기를 고치지 않으면 나머지 수정이 의미가 없다.

---

### M8. `main.tex:71` — 초록 마지막 문장

**현행**

> The study introduces, to our knowledge, the first framework that derives a color correction from an individual's own cortical color representation.

**교체 (IN 판 — 한계로 닫음)**

> These findings support studying CVD as an individual-level distortion of cortical hue geometry, alongside its established retinal characterization. The inversion step provides what is, to our knowledge, the first framework for deriving a color correction from an individual's own cortical color representation. Which individual distortions, and which derived filters, are robust, identifiable, and generalizable remains to be established.

**JNeurosci 판**: 위 3문장의 **2·3 순서를 교체해 신규성으로 닫는다.** 초록을 한계로 끝내면 IN 에서는 신뢰를 벌지만 JNeurosci 편집자에게는 *저자 스스로 예비연구라고 진술한다* 로 읽힐 수 있다.

**근거**: 현행 마지막 줄은 신규성 단문 하나뿐이라 검토자가 제기한 **intervention identifiability** 에 초록 차원에서 답이 없다. `robust, identifiable, and generalizable` 이 그 지적을 어휘 수준에서 정면으로 받는다. 상세 설계 근거는 [`FRAMING_JNEURO_IMAGINGNEURO_2026-08-16.md`](FRAMING_JNEURO_IMAGINGNEURO_2026-08-16.md) §4.1.

---

### M9. 제목 — `main.tex`

| # | 문안 | 겨냥 |
|---|---|---|
| T1 | Hue identity and hue geometry dissociate in the cortical color representation of color-vision-deficient observers | JNeurosci |
| **T4** | **From cortical hue-geometry distortion to individualized stimulus-space correction in color vision deficiency** | **Imaging Neuroscience** |
| T2 | Inverting an individual's cortical color representation into a stimulus-space correction filter | 방법 단독 강조 |
| T3 | Preserved categorical decoding with disrupted continuous hue interpolation in color vision deficiency | 보수적 대안 |

**`hue-representation` 이 아니라 `hue-geometry` 여야 한다.** 8색 범주 식별은 두 arm 전부에서 보존된다(최저 셀 deutan V1 hmc 0.229 vs chance 0.125). "표상이 왜곡되었다"고 쓰면 살아 있는 절반까지 죽은 것으로 진술하게 되고, 이는 본 논문의 핵심 대비(해리)를 제목이 스스로 지우는 것이다.

---

## 2. Discussion 한계 문단 확장 — `discussion_v3.tex:60`

**현행이 이미 절반을 공개하고 있다** — 좋은 발판이다.

> Two of the reported estimates depend on analysis choices. The deutan V2 disparity elevation is significant in the common HC space and falls to a non-significant trend under the symmetric leave-one-subject-out control, whereas the protan V1 elevation is significant under both.

**교체**

> Several of the reported estimates depend on analysis choices. The deutan V2 disparity elevation is significant in the common HC space, falls to a non-significant trend under the symmetric leave-one-subject-out control, and reverses direction when head-motion realignment is applied. The protan V1 elevation is significant under the first two and falls to a trend under the third, with its direction preserved throughout. The single-case interpolation contrasts at hV4 likewise do not reach significance under realignment. The control-level result that fixes hV4 as the only interpretable region for interpolation is unaffected by any of these choices (Supplementary~\S S2). We therefore treat the region-specific deviations as descriptive rather than as established individual localizations.

---

## 3. Supplementary §S2 — 문단 하나 + 표 하나

### 3.1 신설 문단 (기존 `Motion sensitivity analysis` 뒤)

> \paragraph{Realignment.}
>
> Head-motion realignment was not applied in the primary pipeline. We reconstructed all functional data with the per-volume rigid transform composed into the same single-interpolation chain used by the primary pipeline, so that the two arms differ in realignment alone and not in the number of resamplings. Realignment reduced temporal SNR by $1.7$–$3.0\%$ in every ROI and changed the overlap between each atlas ROI and the acquired data by less than $0.6\%$. The neural endpoints under both arms are given in \cref{tab:hmc_robustness}.

**프레이밍 주의.** 다음 셋 중 어느 것도 쓰지 않는다.

| 금지 | 이유 |
|---|---|
| `we omitted a standard step` | 태만하게 읽힌다 |
| `one of several sensitivity analyses` | 표준 단계임을 감춘다 |
| `tSNR was lower, so we did not apply it` | 방어 불가. 품질로 종점을 기각하는 논리는 양날이며, 같은 논리로 종점 변화도 무시할 수 있어야 한다 |

**품질과 종점을 분리해 각각 보고하고, 어느 쪽도 다른 쪽을 기각하는 데 쓰지 않는다.**

### 3.2 표 `tab:hmc_robustness`

| Endpoint | Primary | Realigned |
|---|---|---|
| HC hue interpolation at hV4 (permutation) | $p = .011$ | $p = .023$ |
| HC interpolation at V1 / V2 / V3 | n.s. | n.s. |
| Cross-arm reliability of adjacent accuracy, hV4 (ICC 2,1) | \multicolumn{2}{c}{$0.825$} |
| ... V1 / V2 / V3 | \multicolumn{2}{c}{$-0.005$ / $0.471$ / $0.662$} |
| Protan hV4 vs controls | $p = .011$ | $p = .108$ |
| Deutan hV4 vs controls | $p = .054$ | $p = .242$ |
| Protan V1 disparity vs controls | $p = .007$ | $p = .077$ |
| Deutan V2 disparity vs controls | $p = .040$ | $p = .825$ (direction reversed) |

**Q1 결정 (2026-08-16): all-ROI 표를 싣는다.** 단 아래 두 문장을 함께 넣는다.

**(a) 표 아래 선제 문장** — 필수

> No region-specific deviation was stable across arms. Cells reaching significance in one arm did not in the other, in both directions, and we do not interpret any single-arm cell.

**(b) 해석 범위 진술** — Results §3.2 첫머리, all-ROI 표를 인용하기 전

> Throughout, we interpret two quantities: the control-level localization of continuous hue interpolation, which is stable across preprocessing arms and across the color-label permutation gate, and the fitted filter parameters together with their psychophysical evaluation, which do not depend on preprocessing. The full region $\times$ arm grid is reported in Supplementary~\S S2 for completeness; individual cells within it are descriptive and are not used to support any claim in the main text.

**근거**: all-ROI 표를 실으면 리뷰어는 새로 유의해진 셀(deutan V1, $p$ = .027)을 반드시 본다. 설명 없는 별표 옆의 침묵이 한 문장보다 나쁘다. (a)가 그 셀을 막고, (b)는 **표의 존재가 곧 주장이 아님을 사전에 선언**한다. 두 문장이 있어야 "전부 공개했으나 본문은 견고한 것만 딛고 선다"가 성립한다. **Results 에서 개별 셀을 서사로 만들지 않는다.**

### 3.3 ICC 를 넣어야 하는 이유

동료 의견의 최소 세트에는 ICC 가 없었으나 **넣기를 권한다.** 종점 결과와 독립인 **지표 신뢰도** 사실이고, **논문에 유리하다.** 현행 원고는 "hV4 만 해석 가능" 을 색 라벨 순열 하나로 정당화한다. ICC 는 두 번째 독립 축에서 같은 결론을 준다 — **게이트를 통과하는 유일한 ROI 가 전처리 재현성도 유일하게 높다.**

---

## 4. 그림 캡션

| 그림 | 조치 |
|---|---|
| `fig:geometry` (Fig 4) | **Q2 결정: 별표를 패널에서 제거하고 각주로 강등.** 캡션에 `Asterisks are omitted; the region-specific elevations did not hold across preprocessing arms and the arm-wise tests are given in Supplementary~\S S2.` |
| `fig:loco` (Fig 3) | 변경 불필요. 캡션이 이미 측정·기호·검정 방향만 기술한다 |

**Q2 근거**: deutan V2 가 arm 에서 **방향까지 역전**했으므로(.040 → .825) 패널의 별표는 방어할 수 없다. 별표를 남기고 캡션에서만 단서를 다는 것은 그림과 캡션이 서로 다른 말을 하게 만든다 — 그림은 인용·발표에서 캡션과 분리되어 유통되므로 **패널 자체에서 제거해야 한다.**

---

## 5. 논문에 넣지 않는 것

| 항목 | 이유 |
|---|---|
| 이중보간 HMC arm 실패 (신뢰도 −0.048/−0.170) | 구현 오류의 이력. 유효 arm 만 보고하면 족하다 |
| node4 FSL 5.0 사고 | 실행 인프라 문제 |
| MAE 순열 귀무 8개 수치 | 내부 판별용. 결론(`이산화 인공물 아님`)만 §S2 문장에 반영 |
| run-level bootstrap CI 상세 | 동일 |
| Bland–Altman 그림 | 동일. ICC 한 줄로 대체 |
| 색별 분해 (protan 3/8색) | 동일 |
| deutan V1 $p$ = .027 을 서사화 | post-hoc ROI 사냥으로 읽힌다. 표에만 존재 + 선제 문장 |

---

## 6. 반영 순서

```
M7 초록  →  M1·M2·M3 Results §3.3  →  M4 Results §3.2
   ↓
M5·M6 Discussion  →  §2 한계 문단 확장
   ↓
§S2 문단 + tab:hmc_robustness  →  Fig 4 캡션
   ↓
빌드 · 상호참조 확인
```

M3 이 가장 중요하다 — **개인화 논거의 하중을 disparity ROI 에서 적합 파라미터·심리물리로 옮기는 작업**이며, 이걸 하지 않으면 기여 2 의 도입부가 무너진 근거 위에 남는다.

---

## 7. 결정 완료 (2026-08-16)

| # | 항목 | 결정 |
|---|---|---|
| Q1 | all-ROI sensitivity 표를 실을 것인가 | **싣는다** + §3.2 (a) 선제 문장 + (b) 해석 범위 진술 |
| Q2 | `Figure~\ref{fig:geometry}` 의 별표 | **패널에서 제거, 각주로 강등** (§4) |
| Q3 | §S2 에 `exp2` 종점 arm 재산출 미실시를 명시 | **불요** — 사용자가 ses-2 ezBIDS 디페이싱을 진행해 `anat_harmonized` + `hmc` 를 한 번에 적용하고 exp2 종점을 재산출하므로 미실시 자체가 소멸 |

**남은 차단 요인 없음. `.tex` 착수 가능.**
