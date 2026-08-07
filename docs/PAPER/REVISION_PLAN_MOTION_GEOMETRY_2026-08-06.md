# 수정안 — 움직임 보고와 기하 서술 (2026-08-06)

> 근거 수치: [`RESULTS_MOTION_ARMS_2026-08-05.md`](../../analysis/phase2_SRM_across_between/results/RESULTS_MOTION_ARMS_2026-08-05.md),
> [`RESULTS_GEOMETRY_VALIDITY_2026-08-05.md`](../../analysis/phase2_SRM_across_between/results/RESULTS_GEOMETRY_VALIDITY_2026-08-05.md)

## 반영 현황 (2026-08-07 갱신)

| 항목 | 상태 | 비고 |
|---|---|---|
| M1 FD 꼬리 통계 | ✅ 반영 | `methods_v2.tex:74`, 16.2% |
| M2 민감도 포인터 | ✅ 반영 | 움직임 회귀 arm 으로 교체 |
| **M3 추정량 규칙** | ❌ **폐기** | §3-M3 참조 — 초안이 R2 와 모순 |
| M4 ΔRDM 도입 | ✅ 반영 | `methods_v2.tex:202` (§기하 안에 배치) |
| M5 PCA 공간 정당화 | ✅ 반영 | `methods_v2.tex:267` |
| R1 제목 `localizes` | ✅ 반영 | `results_v4.tex:60` |
| R2 도입 문단 ΔRDM 제거 | ✅ 반영 | |
| R3 disparity 결과 | ✅ 반영 | |
| R4 ΔRDM 문단 삭제 | ✅ 반영 | |
| R5 종합 문단 | ✅ 반영 | |
| R6 Figure 4 캡션 | ✅ 반영 | |
| S1 / S17 / S18 | ✅ 반영 | S17·S18 은 통합 `Supplementary/supplementary.tex` 로 이관 |
| §5 Discussion 한 문장 | ✅ 반영 | |

**규칙 R1–R5 는 전부 `.tex` 에 반영되었다.** 이 문서는 이제 근거 기록이며, 새 결정은 아래 §7 에 추가한다.

---

## 0. 이 수정이 필요한 이유

세 가지가 겹쳤다.

1. 분석 데이터에 **머리움직임 정렬이 적용되지 않았다.** 현재 본문은 이를 진술하나, FD 꼬리 통계와 민감도 분석이 없다.
2. sub-08 V2 disparity 가 **LOSO 에서 비유의**(p = .116)하고 **움직임 회귀에서 소멸**한다(all-HC .040 → .218). 현재 본문은 이를 "trend" 로 부르며 증거로 사용한다.
3. 보고된 색 라벨 순열 절차는 **검정력이 0** 이다. SVD 투영을 순열마다 재적합하여 라벨 뒤섞임이 흡수된다(HC 검출 0/7, 네 ROI 전부 평균 z ≈ 0).

**그리고 이번 논의에서 결정된 축 변경 하나** — ΔRDM 을 결과에서 빼고 Methods 의 손실 구성요소로 옮긴다. §1a 참조.

---

## 1. 확정할 규칙

| # | 규칙 | 근거 |
|---|---|---|
| **R1** | **임베딩 공간 = all-HC** | 파이프라인 일관성 |
| **R2** | **HC 기준분포 = LOSO** | all-HC 기준분포는 HC 를 자기 평균과 비교해 산포를 좁힌다. CVD 만 외부인이므로 편향 방향이 CVD 과장 |
| **R3** | **단일사례 추론 primary = LOSO** | R2 의 직접 귀결 |
| **R4** | **효과크기는 보고하되 주장 근거로 쓰지 않는다** | n = 7 에서 CI 가 비정보적. sub-09 V1 조차 95% CI [−0.32, +4.51] |
| **R5** | **색 특이성 순열은 투영 동결본으로 보고** | 재적합본은 검정력 0 |

**R3 의 파급** — sub-08 V2 는 primary 에서 애초에 비유의하다. 움직임 회귀 결과는 "유의한 결과를 지웠다" 가 아니라 "비유의한 결과가 비유의하게 남았다" 가 되고, 본문 해명 부담이 §S17 로 내려간다.

### 1a. 축 변경 — ΔRDM 은 결과가 아니라 손실 구성요소

$$\text{disparity} = \lVert XR - Y\rVert_F \quad (\text{최적 회전 후 스칼라})$$

**disparity 는 회전 불변 스칼라이므로 방향 정보가 없다.** "얼마나 먼가" 만 말하고 "어느 색이 어디로 갔는가" 를 말하지 않는다. 역산에는 방향이 필요하다. ΔRDM 은 28쌍 각각의 변위를 보존하므로 그 방향을 담는다. **이것이 ΔRDM 이 존재하는 이유이며, 따라서 Methods 소속이다.**

이 배치가 해결하는 것.

| 문제 | 해소 방식 |
|---|---|
| ΔRDM 개별 쌍이 우연 수준 (주요 ROI 각 1건, 28회 기대 1.4건) | 검정을 하지 않으므로 보고 의무 없음 |
| ΔRDM 종합 크기 16칸 FDR 0 통과 | 손실이 코사인이라 크기를 쓰지 않음 — Methods 문장이 선제 차단 |
| SRM 공간 vs PCA 공간 불일치 | Methods 의 차원축소 정당화로 전환 |
| 부분·다대일 재배열이 HC 와 안 갈림 (0/16) | 특이성 주장을 하지 않으므로 무관 |

**검증 근거는 하류로 이동한다** — ΔRDM 이 잡음이 아님은 held-out 예측이 보인다(`results_v4.tex:116`, 7/7 fold, 격자 상위 5–8%).

---

## 2. 본문 흐름

```
Methods §전처리       FOV 제약 → MI 정합 / 정렬 미적용 / FD 요약 → S1, S17 포인터
Methods §기하         [규칙] 공간 all-HC, 기준분포 LOSO → S7 포인터
Methods §손실         disparity 는 스칼라 → 방향 필요 → ΔRDM 도입 → 코사인
                      PCA 축약 + SRM 일치도 (r = .77–.89)
   ↓
Results §LOCO         보간 결손 (기존 유지)
   ↓
Results §Geometry     disparity 만
                      sub-09  V1, 두 추정량 모두 유의 (.007 / .045)
                      sub-08  V2, common space 유의 (.040), LOSO 미생존 (.116)
                              → 방향·크기 보존, 구간만 넓어짐 (정밀도 차이)
                              → 감쇠와 부재를 가르려면 더 큰 표본 필요
   ↓
Results §필터         2성분 적합 → held-out → 역산 → exp2
   ↓
S17                   움직임: FD 피험자별 / 회귀 arm / 순환이동 대조 / 한계
S18                   기하 타당성: 동결 투영 순열 / 색 특이성 / sub-09 회전
```

**서술 원칙** — 결과를 있는 그대로 보이고, 두 추정량의 차이를 **정밀도 차이**로 설명한다. sub-08 을 "약한 양성" 이나 "trend" 로 포장하지 않으면서 제목의 `distinct ROI in each case` 를 지지한다.

---

## 3. 구간별 수정안

### M1 — `methods_v2.tex:74` FD 꼬리 통계

**현재**
> mean framewise displacement was $0.32 \pm 0.04$ mm across the nine analyzed participants (HC $0.31$, CVD $0.34$; Supplementary~\S S1).

**수정**
> mean framewise displacement was $0.32 \pm 0.04$ mm across the nine analyzed participants (HC $0.31 \pm 0.04$, CVD $0.34 \pm 0.05$), with $16.2\%$ of volumes exceeding $0.5$ mm (Supplementary~\S S1).

**왜** — 평균만 보고하면 꼬리를 숨긴 것으로 읽힌다. 실제 분포는 낮지 않다(sub-05 24.7%, sub-08 24.3%). 리뷰어가 S1 에서 발견하는 것보다 본문에서 먼저 밝히는 편이 안전하다.

---

### M2 — `methods_v2.tex:74` 민감도 분석 포인터

**현재**
> A sensitivity analysis repeating the primary neural endpoints on an independently preprocessed version of the same data is reported in Supplementary~\S S17.

**수정**
> Because the primary analysis left motion uncorrected, every neural endpoint was recomputed with the motion parameters and their temporal derivatives entered as nuisance regressors (Supplementary~\S S17).

**왜** — 두 가지가 틀려 있다. ① 현재 문장이 가리키는 "independently preprocessed version" 은 HMC 재샘플링 arm 인데, 그 arm 은 재샘플링이 2회 들어가 split-half 신뢰도가 붕괴한다(HC −0.048, CVD −0.170). 판정에 쓸 수 없다. ② 실제 판별자는 재샘플링 0회인 움직임 회귀 arm 이다. 순환이동 대조 설명은 본문에서 빼고 §S17 로 보낸다.

**§S17 이 반드시 받아야 할 내용**
> A control analysis added the same twelve regressors after circularly shifting each within run. The shift preserves the autocorrelation and spectrum of the regressors while destroying their temporal alignment with the data, and therefore separates the variance inflation caused by adding twelve regressors from the removal of motion-aligned variance.

---

### M3 — ~~Methods 기하 절, 추정량 규칙 선언~~ **폐기 (2026-08-07)**

**초안** (사용하지 않음)

> ~~The shared space was estimated from all seven HC participants. Within that space each HC participant was compared to the mean of the remaining six, so that the reference distribution for the single-case comparison is symmetric (Supplementary~\S S7).~~

**폐기 사유** — 이 문장은 all-HC LOO 기준분포를 `symmetric` 이라 부른다. **R2 가 정확히 그 반대를 말한다**: all-HC 공간에서 HC 기준은 in-sample 이고 CVD 만 out-of-sample 이므로 비대칭이며, 편향 방향이 CVD 과장이다. M3 은 R2/R3 확정 이전 초안이다.

**대체** — `methods_v2.tex:199` 가 두 추정량을 모두 정의하고 대칭 LOSO 를 추론 검정으로 지정한다. 추정량 정의를 Methods 에 둔다는 M3 의 취지는 그대로 살아 있다.

---

### M4 — Methods 손실 절, ΔRDM 도입 (신설·핵심)

> Procrustes disparity summarizes the distance between two representational geometries as a single value after optimal rotation. It therefore indicates how far a participant's geometry lies from the HC reference, without indicating which colors are displaced. Inverting the distortion requires that direction. We expressed the same comparison as a difference of representational dissimilarity matrices, $\Delta\text{RDM} = \text{RDM}_{\rm CVD} - \overline{\text{RDM}}_{\rm HC}$, which retains the displacement of every color pair. The neural loss term matches the $\Delta$RDM predicted by a candidate distortion to the observed $\Delta$RDM by cosine similarity, and is therefore sensitive to the direction of the deviation rather than its magnitude.

**왜** — 네 가지를 한 문단이 처리한다.

① **ΔRDM 의 존재 이유를 구조로 설명한다.** disparity 가 회전 불변 스칼라라는 것은 사실이고, 역산에 방향이 필요하다는 것도 사실이다. 사후 변명이 아니다.

② **마지막 문장이 "왜 크기를 안 보나" 를 선제 차단한다.** 손실이 코사인이므로 $\lVert\Delta\text{RDM}\rVert$ 은 들어가지 않는다. 크기 검정 결과를 보고할 의무가 사라진다.

③ **ΔRDM 을 결과에서 완전히 제거한다.** 개별 쌍 검정, FDR, 우연 기대치 논의가 모두 불필요해진다.

④ **식을 명시한다.** 현재 본문은 `\overline{\text{RDM}}_\text{HC}` 만 적혀 HC 기준이 LOO 인지 전체 평균인지 구분되지 않는다.

---

### M5 — Methods 손실 절, 공간 정당화 (신설)

> The loss computes $\Delta$RDM in a PCA-reduced space ($K = 6$). Across the 28 pairwise entries this estimate agreed with the SRM-aligned estimate used for disparity at V1, V2, and hV4 ($r = 0.77$--$0.89$), and less closely at V3 ($r = 0.39$--$0.58$), so the reduction does not determine the pattern the loss fits.

**왜** — "왜 PCA 인가" 에 대한 답이다. 두 공간이 서로 다른 정렬 절차인데 같은 패턴을 준다는 것이 축약의 정당화가 된다. V3 를 먼저 밝히는 것이 전수 보고의 증거가 된다.

**근거 수치 (구성 B, LOO 기준분포)**

| ROI | sub-08 | sub-09 |
|---|---|---|
| V1 | $+0.800$ | $+0.781$ |
| V2 | $+0.765$ | $+0.803$ |
| hV4 | $+0.885$ | $+0.821$ |
| V3 | $+0.385$ | $+0.577$ |

---

### R1 — `results_v4.tex:60` 소제목 — 확정

**현재**
> \subsection{Color geometry is distorted at a distinct ROI in each CVD case}

**수정**
> \subsection{Geometric deviation localizes to a distinct ROI in each CVD case}

**왜** — `is distorted ... in each CVD case` 는 두 사례 모두에서 왜곡을 단언하므로 sub-08 의 LOSO 미생존과 충돌한다. `localizes` 는 편차가 어느 ROI 에 집중되는지를 기술할 뿐 유의성을 단언하지 않는다. `distinct ROI in each case` 프레임은 유지되고 노출만 사라진다.

---

### R2 — `results_v4.tex:64` 도입 문단, ΔRDM 제거

**현재**
> To characterize the geometric basis of the LOCO impairment, we compared the pairwise representational structure of CVD and HC participants in a shared SRM-aligned space. For each CVD participant we computed disparity and the per-pair RDM difference from the HC mean ($\Delta\text{RDM} = \text{RDM}_\text{CVD} - \overline{\text{RDM}}_\text{HC}$).

**수정**
> To characterize the geometric basis of the LOCO impairment, we compared the representational geometry of CVD and HC participants in a shared SRM-aligned space. Procrustes disparity indexes how far a participant's whole geometry lies from the HC reference.

**왜** — ΔRDM 정의는 M4 로 이동한다. 결과 절은 하나의 측도만 다룬다.

---

### R3 — `results_v4.tex:66` disparity 결과

**현재**
> The protan participant showed significantly elevated disparity specifically at V1 (Crawford \& Howell $p = 0.007$ in the common HC space; $p = 0.045$ under the symmetric LOSO control), with no elevation at V2, V3, or hV4. The deutan participant showed elevated disparity at V2 (common-space $p = 0.040$) that attenuated to a non-significant trend under the symmetric LOSO control ($p = 0.116$), with no elevation at V1, V3, or hV4.

**수정**
> The protan participant showed elevated disparity specifically at V1, under both the common HC space ($p = 0.007$) and the symmetric LOSO reference ($p = 0.045$), with no elevation at V2, V3, or hV4. The deutan participant showed elevated disparity at V2 in the common HC space ($p = 0.040$), which did not survive the symmetric LOSO reference ($p = 0.116$, $d_{cc} = 1.42$), with no elevation at V1, V3, or hV4. The direction and magnitude of the deutan effect were preserved under the LOSO reference while the confidence interval widened, so the two estimators differ in precision rather than in sign. Distinguishing an attenuated effect from an absent one at this ROI requires a larger cohort.

**왜** — 결과를 있는 그대로 보이되 세 가지를 고친다.

① **"non-significant trend" 삭제.** p = .116, 95% CI [−0.87, +3.61] 을 "trend" 로 부르는 것은 CI 가 지지하지 않는 수사다. `did not survive` 가 같은 사실을 수사 없이 말한다.

② **"differ in precision rather than in sign" 추가.** 두 추정량의 점추정은 같은 방향이고 LOSO 가 HC 산포를 넓힐 뿐이다(SD 0.103 → 0.144). 이 문장이 "왜 하나는 살고 하나는 죽나" 에 답한다.

③ **larger cohort 문장은 문단 끝.** `requires further investigation` 같은 상투구 대신 `Distinguishing an attenuated effect from an absent one` 으로 **무엇을 못 가리는지** 를 명시한다.

---

### R4 — `results_v4.tex:68` ΔRDM 문단 — **전체 삭제**

**삭제 대상**
> ~~The $\Delta$RDM heatmaps (Figure~\ref{fig:geometry}A) reveal subject-specific distortion structures. The deutan participant shows elevated distances among S-cone intermediate pairs at V2, and the protan participant shows a broader reorganization of pairwise distances at V1. Disparity tests how far the whole SRM-aligned geometry lies from the HC leave-one-out reference, whereas $\Delta$RDM shows which color pairs deviate and in which direction; the disparity elevation --- significant and LOSO-robust at V1 in the protan participant, a common-space trend at V2 in the deutan participant --- is independent evidence that the cortical color representation is geometrically distorted.~~

**왜** — 세 개의 문제를 한 번에 없앤다.

① `elevated distances among S-cone intermediate pairs at V2` 는 **보정 전에도 우연 수준**이다. 주요 ROI 에서 $p < .05$ 인 쌍이 각 1건이고 28회 검정의 기대는 1.4건이다($P(\geq 1) = 0.76$).

② `a common-space trend ... is independent evidence` 는 비유의 결과를 증거 목록에 넣는다.

③ ΔRDM 의 역할 설명은 M4 로 이동했다.

**참고 — 보고하지 않기로 한 ΔRDM 검정 결과 (기록용)**

| 수준 | 결과 |
|---|---|
| 개별 쌍 | 주요 ROI 각 1건 $p<.05$ (우연 기대 1.4건). 두 공간에서 최상위 쌍이 다름 |
| 종합 크기 $\lVert\Delta\rVert$ | 16칸 BH-FDR 통과 0 (최소 $p_{adj}$ = .325) |
| 종합 크기 mean$\lvert\Delta\rvert$ | 16칸 통과 0 (최소 $p_{adj}$ = .112) |
| RSA 2차 유사도 | sub-09 V1 만 명목 유의(SRM $p$=.025, PCA $p$=.034), 16칸 FDR 통과 0 |
| 부분·다대일 재배열 (2성분 격자 유도, 대칭 탐색) | 16칸 FDR 통과 0. HC 가 같은 이득을 얻음 |

M4 의 코사인 문장이 이 전부를 보고 의무에서 제외한다.

---

### R5 — `results_v4.tex:70` 종합 문단

**현재**
> Together, the interpolation deficit (§\ref{sec:results:loco}) and the geometric distortion (this section) identify a structured target for correction. In each participant the continuous arrangement of hues is displaced in a direction and magnitude specific to that individual.

**수정**
> The two cases differ in where the deviation lies and in how strongly it is supported. Because the deviation is not shared, a family-level correction cannot serve both. In each participant the continuous arrangement of hues is displaced in a direction and magnitude specific to that individual, which is what a personalized correction is required to capture.

**왜** — `differ in where ... and in how strongly it is supported` 가 제목의 `distinct ROI in each case` 를 지지하면서 sub-08 을 sub-09 와 동급으로 놓지 않는다.

**두 번째 문장이 sub-08 의 음성을 자산으로 바꾼다.** 두 사람이 같은 방식으로 다르지 않다는 것이 개인화의 근거이므로, sub-08 이 sub-09 와 다르게 나오는 것이 논증을 약화하지 않는다.

---

### R6 — Figure 4 (`fig:geometry`) — 패널 A 이동

**결정** — ΔRDM 히트맵을 **Figure 2(파이프라인)로 옮긴다.** ΔRDM 이 손실 입력이므로 파이프라인 그림이 개념적 제자리다. Figure 4 는 disparity 전용이 되고, Figure 2 는 손실함수가 실제로 무엇을 보는지 보이게 되어 강해진다.

**Figure 4 수정 캡션**
> \textbf{Procrustes disparity to the healthy-control reference.}
> Disparity per participant per ROI, which indexes the distance of the whole geometry from that reference. HC band, group mean $\pm 1$ SD ($n = 7$); dots, individual HC leave-one-out values. Single-case comparisons used the Crawford--Howell modified $t$ against the HC leave-one-out distribution; test statistics under both the common-space and symmetric LOSO references are given in \cref{tab:disparity_loso}. Exploratory single-case.

**왜** — NeuroImage 관례에 맞춰 **분석 방법과 그 의미만** 남긴다. 삭제 대상 두 개.

> ~~Each subject showed elevated disparity at a single, distinct ROI (the deutan participant V2; the protan participant V1).~~ — 결론이며 R3 과 중복. sub-08 을 `elevated` 로 단언하므로 R3 와 어긋남

> ~~(the deutan participant V2: $p = 0.040$; the protan participant V1: $p = 0.007$) ... attenuates to a trend ($p = 0.116$)~~ — $p$ 값도 결과이므로 표로 이동. 그림 자족성은 검정 이름과 기준분포로 확보됨

---

### S1 — 부록 보강

- 피험자 × 런 FD 표 (mean, max, % > 0.5 mm)
- sub-08 이 mean FD 최댓값(0.384 mm), 최대 프레임 변위 4.81 mm 임이 표에서 확인되게

기존 문장 `These parameters served as a quality-control record only, and the analyzed images were resampled once from native BOLD space into MNI space.` 는 유지. 재샘플링 1회 명시가 §S17 대조 논의로 이어진다.

---

### S17 — 신설 (움직임)

```
S17. Head motion.

[맥락] The functional series were acquired with a limited field of view covering
occipital cortex. Registration was therefore performed with header-initialized
mutual information, which is robust to limited FOV and requires no white-matter
boundary. Rigid-body motion was estimated for every run but was not applied to
the analyzed data, which were resampled once by the composed native-to-MNI
transform. Framewise displacement is reported per participant in S1.

[민감도] Every neural endpoint was recomputed with the six motion parameters and
their temporal derivatives added to the second-level design matrix, and again
with the same regressors circularly shifted within run. The shift preserves the
autocorrelation and spectrum of the regressors while destroying their temporal
alignment with the data, and therefore separates the variance inflation caused
by adding twelve regressors from the removal of motion-aligned variance.

[결과] (아래 표)

[한계] Motion regression removes variance temporally aligned with the estimated
parameters. It does not reconstruct the data that volume realignment would have
produced.

[전망] Realignment of limited-FOV series is itself nontrivial, since rigid-body
estimation is less constrained when little of the head is imaged. Acquisitions
of this type would benefit from motion correction validated for partial coverage.
```

| 항목 | 값 |
|---|---|
| sub-09 V1 disparity (LOSO) | 원본 .045 → 회귀 **.0215** → 순환이동 .031 |
| sub-08 V2 disparity (LOSO) | 원본 .116 → 회귀 .300 → 순환이동 .044 |
| split-half 신뢰도 실제 움직임 효과 | sub-08 **−0.338** (차순위 −0.134), sub-09 +0.002 |
| 자극 고정 움직임 | 전 피험자 없음 (순환이동 onset 귀무 대비 z −0.07 ~ +0.08, p .34–.63) |

**왜 이 배치인가** — FOV 제약을 *맥락*으로 먼저 놓되 정렬 미적용의 *원인*으로 주장하지 않는다. 스크립트에 남은 근거(`run_method3_header_mi_2nd.sbatch:22` "MI robust to limited FOV")는 **정합 방법 선택**에 대한 것이고, 정렬에 대한 기록은 `add_motion_correction_2nd.sbatch:25` 의 사실 진술("As in the 1st dataset")뿐이다. 기전상으로도 런 내부 정렬이 BOLD→T1w 정합을 깨뜨리지 않으므로, "정합을 위해 정렬을 제거했다" 는 기전 질문에 답이 없고 코드 공개 시 검증 가능하다.

---

### S18 — 신설 (기하 타당성)

```
S18. Validity of the geometric comparison.

[동결 투영] Color-label permutation was performed with the shared projection
held fixed. When the projection is re-estimated for each permutation the label
shuffle is absorbed by the re-fit, and the procedure has no power: across four
ROIs no HC participant was detected against its own distribution (0/7) and the
mean permutation z was approximately zero.

[색 특이성] (표)

[sub-09 회전] (아래)
```

**색 특이성 — 동결 투영 순열 $p$**

| | sub-08 원본 | sub-08 회귀 | sub-09 원본 | sub-09 회귀 |
|---|---|---|---|---|
| V1 | .105 | **.009** | .758 | .737 |
| V2 | **.002** | **.003** | **.013** | .084 |
| V3 | **.024** | **.005** | **.001** | **.001** |
| hV4 | .273 | **.029** | .129 | .201 |

**sub-09 V1 회전 소견** — 본문에 올리지 않고 여기에만 둔다(§4 U10).

- 항등 라벨에서 색 특이성 없음(.758 / .737)
- Procrustes disparity: 최적 이동 45°, 이득 +24.0%(원본) / +19.2%(회귀). 이동 후 disparity 0.788 < HC 평균 0.839
- RSA 2차 유사도(SRM): 항등 $\rho \approx 0.00$ (HC 0.45) → 한 색 단계 이동에서 $\rho = +0.52$. 이득 +0.523 vs HC 선택편향 귀무 0.037 ± 0.097, $z = +5.02$, $p = .002$, **16칸 BH-FDR 통과** ($p_{adj}$ = .032)
- 두 지표의 최적 이동은 **같은 한 색 단계**다(roll 관례 반대: disparity 45° ≡ RSA 315°)
- 특정되지 않는 것: SRM 공간에서 225°(+0.50)가 315°(+0.52)와 사실상 동률이고, PCA 공간은 135°를 최적으로 본다($p$ = .048, FDR 미통과)
- sub-08 은 네 ROI 전부 항등이 최적(이득 0)

**정확한 주장** — *HC 유사도를 회복시키는 색 재배열이 존재한다* 는 보정 후에도 성립한다. *어떤 재배열인가* 는 특정되지 않는다.

---

## 4. 미결

| # | 항목 | 상태 |
|---|---|---|
| **U1** | sub-08 V3 ΔRDM | **미보고 확정**, 노출 관리도 하지 않음. 근거 둘: 순환이동 대조에서 소멸, PCA 공간 미출현 |
| **U2** | 필터 provenance | 배포 필터 (6, −42) 는 원본 arm 기하에서 적합. RDM 단독 loss(`γ_\|RDMV2\|noLOCO`)도 β_c 300/300 음수로 부호 일치. **motreg arm 재적합 미실시** — 로컬에 amplitude 있음, 한 셀만 돌리면 됨 |
| **U3** | 35개 색 특이성 셀 BH-FDR | 현재 미보정 |
| **U5** | 런 수준 bootstrap CI (6 런 2000 재표집) | CVD 측정 불확실성 |
| **U6** | exp2 arm 움직임 회귀 재산출 | 미실시 |
| **U7** | `method_v1.1_0404.md:20` | 정렬 수행을 사실과 다르게 기술. 내부 문서이나 정정 필요 |
| **U9** | ΔRDM 기준분포 구성 | 구성 B(ΔRDM 대 ΔRDM) 채택. 기존 문서·그림이 구성 A 로 산출됐으면 재산출 |
| **U10** | **모형-소견 불일치** | sub-09 V1 회전이 유일하게 FDR 을 통과하는데 2성분 모형은 균일 회전을 표현할 수 없다($\overline{\delta\theta} = 0$ 구조적; 격자 1326셀 → 고유 순열 21/18개, 균일 순환이동은 항등뿐). Discussion 한 문장 필요 — §5 참조 |

### 4a. sub-08 V3 — 미보고, 노출 관리 없음 (확정)

ΔRDM 은 4개 ROI × 2명 = 8칸 전부 산출되었고, FDR 을 통과한 유일한 항목이 SRM 공간의 sub-08 V3 다. 보고하지 않으며 범위 규칙 선언이나 §S18 각주 같은 보완도 하지 않는다.

이 결정은 두 개의 독립 근거를 갖는다. ① 순환이동 대조에서 소멸한다. ② PCA 공간에 나타나지 않는다(PCA V3 최상위는 blu--pur $z = +2.91$). 재현되지 않는 결과이므로 미보고가 어떤 주장도 강화하거나 약화하지 않는다.

**그리고 §1a 이후로는 ΔRDM 자체가 결과가 아니므로 이 노출은 소멸한다.**

---

## 5. Discussion 에 필요한 한 문장

> The present model represents distortion of the confusion axis and does not include a uniform rotation term. Extending it to that component is left to future work.

**왜** — U10 의 긴장을 숨기면 리뷰어가 찾는다. 밝히면 모형의 범위를 스스로 정한 것이 된다. 균일 회전 소견 자체는 §S18 에만 있으므로 본문 논증에 부담을 주지 않는다.

---

## 6. 쓰지 않기로 한 것

| 항목 | 이유 |
|---|---|
| MCFLIRT vs fMRIPrep FD 불일치 ($r \approx 0.37$) | 미분이 잡음을 증폭하는 것은 일반 현상이라 0.37 이 비정상인지 판단할 벤치마크가 없다. 정당화로 쓰면 변명으로 읽히고, "전뇌 비교값은?" 에 답이 없다 |
| "limitation rather than design choice" 표현 | 문헌 가치를 낮춘다. §S17 의 사실 진술 + 전망 문단으로 대체 |
| sub-08 V2 를 "marginal" / "trend" 로 제시 | 95% CI [−0.87, +3.61] 이 지지하지 않는다. `did not survive` + `differ in precision rather than in sign` 이 같은 자리를 수사 없이 채운다 |
| ΔRDM 개별 쌍을 "significant but fails FDR" 로 제시 | 보정 전 적중이 주요 ROI 에서 각 1건이고 28회 검정의 우연 기대는 1.4건이다 |
| 효과크기를 주장 근거로 사용 | n = 7 에서 sub-09 V1 조차 95% CI [−0.32, +4.51] |
| HMC 재샘플링 arm 을 민감도 분석으로 인용 | 재샘플링 2회로 신뢰도 붕괴. 참고자료로만 |
| 모형 예측 ΔRDM 과의 단일 대비 검정 | 그 상관이 곧 $L_{\rm RDM}$ 이므로 적합된 $\boldsymbol\delta$ 에서 검정하면 순환 |
| 배포 필터 순열의 HC 대비 특이성 | CVD 는 적합된 순열, HC 는 재적합 없음 — 비대칭. 대칭 탐색 시 sub-09 $z$ = +2.18 → +0.38 로 소멸 |
| ΔRDM 특이성·크기 주장 일체 | §1a 로 ΔRDM 이 Methods 소속이 되어 주장 대상이 아님 |

---

## 7. 이후 결정 (2026-08-07)

### 7a. adjacent accuracy chance = 0.25 (3/8 아님)

`decode_hue` 는 **360 개 정수 hue** 중 argmax 를 반환하고(`utils_forward_model.py:334`), adjacent 는 그 각도의 원형거리 `err <= 45` 다(`loco_canonical.py:103`). 출력공간 360 중 91 도가 허용범위 → **91/360 = 0.253**. 무작위 응답 2 만 회 시뮬레이션에서 0.253(참 hue 별 0.249–0.257), argmax 의 8-bin 분포 균일.

`3/8` 은 예측이 **8 개 자극 hue 로만** 나오는 디코더에만 성립한다(`loco_baseline.py:940-951` 의 `labels_to_hue`). MLP 가 상수출력으로 정확히 `0.375 ± 0.000` 을 찍은 것이 그 확증이다.

**파급** — 본문 8 곳 + 그림 3 개(`generate_fig2/fig8/figS16`) 정정. 주장 역전 1 건: `results_v4.tex:220` deutan 개인화 0.31 은 0.25 **위**이므로 "below the 3/8 chance threshold" 삭제. `tab:loco_decoders` 는 디코더별 chance 를 분리 표기하고, forward encoding 이 자기 chance 를 넘는 유일한 디코더이며 V1(.360)·V2(.283)·hV4(.470) 에서 넘는다는 사실로 서술 교체. ROI 특이성 근거는 순열 귀무로 명시 이관.

**검정 통계는 불변** — 순열 p 와 Crawford–Howell 은 해석적 chance 를 쓰지 않는다.

### 7b. `L_RDM` 식의 `/2` 제거

`methods_v2.tex:262` 가 $(1-\cos)/2$ 였으나 `s10b_v6_pca_rdm.py:195` 와 `s18_heldout_predictive.py:258` 은 `1 - cos` 다.

**영향 0** — 원자는 합산 전 격자 z-정규화된다(`zscore_grid`, 605–611 행). 상수배는 z-score 에서 정확히 소거되므로 결합 가중·argmin·배포 필터 (6,−42)·(2,+24) 어디에도 영향이 없다. 코드가 canonical 이고 식에서 `/2` 만 뺀다.

### 7c. 신설 문단 2 개 (코드 대조로 발견한 미기재 사항)

| 위치 | 내용 |
|---|---|
| `L_{\rm RDM}` 문단 | **45° 스냅** — `p_i = round(perceived[i]/45) % 8` 이므로 $\Delta\text{RDM}_{\rm sim}$ 은 HC RDM 기존 칸의 재색인이다. 후보 왜곡은 8 색 순열로 작용하고 같은 순열로 가는 왜곡은 이 항에서 구별 불가. **U10 의 "격자 1326셀 → 고유 순열 21/18개" 가 이 스냅의 귀결**이므로, 명시하면 U10 논증의 근거가 본문에 생긴다 |
| `Composite loss` 신설 | 원자 스케일이 다르므로(γ 비율 vs 유계 비유사도) 격자 전체에서 z-표준화 후 합산, $\sqrt{n_a}$ 로 나눔. 기존 본문은 296 행에서 **test-loss 에 대해서만** 언급했다 |

### 7e. Gate 1 은 양방향 — 확정 (2026-08-07)

`s10a_precondition.py:209` 은 `pass = bool(abs(d) >= 0.5)` 로 **부호 무관**이다. 기존 본문은 `signed Cohen's d ≥ +0.5` 와 `exceeded the HC LOO distribution in the expected direction` 로 방향 요건을 선언해 실제 규칙보다 강했다.

**사용자 확정: 양방향이 의도된 규칙이다.** 코드가 canonical 이며 재적합 불요. 본문을 코드에 맞춰 정정했다.

| | 이전 | 이후 |
|---|---|---|
| 게이트 명칭 | `Directional precondition` | `Separation precondition` |
| 기준 | `signed $d \geq +0.5$` | `magnitude $0.5$ or greater, in either direction` |

이번 자료에서 `precondition_table.json` 의 $d$ 는 모두 양수이므로 두 규칙의 통과 집합은 동일하다. 정정은 규칙 진술의 정확성 문제이지 결과 변경이 아니다.

### 7f. 미기재였던 선정 규칙 요소 (반영 완료)

`CLAUDE.md §2.5` 의 규칙은 `test_loss_median` ASC → `test_loss_iqr` ASC → `boundary_rate < 0.5`, collapse guard `iqr > 50` OR (`sign(train) ≠ sign(test)` AND `|Δ| > 5`) 다.

| 요소 | 조치 |
|---|---|
| collapse guard | Gate 2 에 신설 |
| $\overline{L}_{\rm RDM}^{\rm LOO}$ 가 순위 기준이 아님 | 순위 밖 별도 문단으로 분리, `These two quantities were the only ranking criteria` 명시 |
| $\overline{L}_{\rm RDM}^{\rm LOO}$ 의 의의 | **심리물리 항을 뺀 신경항 단독 효과**. `the neural component` 라는 표현은 신경항 = RDM 을 전제하므로(LOCO 도 신경항) `a candidate's neural atoms with the psychophysical term excluded` 로 서술 |

### 7d. disparity — fold 평균 비대칭 (미반영, 제안 상태)

`rerun_loo_consistent.py:287` 은 CVD 점수를 `cvd_fold_disps.mean(axis=1)` 로 7 fold 평균하는 반면, HC 는 자기가 held-out 된 fold 의 단일값만 갖는다. HC 분포가 fold 잡음을 유지하는데 CVD 통계량은 그것을 평균으로 지운다 → Crawford–Howell 분모 팽창 → **상측 검정에서 보수적**. 현재 본문 미기재.
