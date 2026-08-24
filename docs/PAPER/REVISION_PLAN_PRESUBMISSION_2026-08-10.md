# 투고 전 최종 수정안 (2026-08-10)

> 선행 정본: [`REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md`](REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md) (R1–R5·M1–M5 반영 완료),
> [`Supplementary/REVISION_WORKLIST.md`](Supplementary/REVISION_WORKLIST.md) rev.4.
>
> 이 문서는 그 뒤 남은 잔여와, 2026-08-10 점검에서 **새로 확정된 사실**을 합쳐 하나의 반영 목록으로 만든다.
>
> **반영 방식**: 항목별로 승인한 뒤 일괄 반영. 이 문서 자체는 근거 기록이며 `.tex` 를 직접 고치지 않는다.

---

## 0. 이번 점검에서 확정된 것

세 가지다. 전부 원산출물 재실행으로 확인했고, 재현 게이트를 통과했다.

| # | 확정 | 성격 |
|---|---|---|
| **F1** | hV4 보간 게이트는 세 전처리 arm 전부에서 생존한다 ($p$ = .011 / .013 / .002) | 기여 1 강화 |
| **F2** | CVD 측 보간 결손은 어느 회귀 arm 에서도 생존하지 않는다. 원인은 **회귀자 12개 추가 비용**이지 움직임 제거가 아니다 | 본문 단서 필요 |
| **F3** | 색 특이성 7 → 15 증가는 **실제 움직임 분산 제거**에서 온다. 순환이동 대조는 3 으로 떨어져 "회귀자 부산물" 해석을 기각한다 | 기여 1 강화, **미완료 control 종결** |
| **F4** | JND staircase 이상 2건 — sub-08 세션-1 orange–yellow 는 **범위 절단(하한)**, sub-09 개인화 orange–yellow 는 **단일 트랙 lapse**. 필터·렌더링 결함 아님 | 부록 각주 필요 |
| **F5** | β_c 부호는 deutan 에서만 전처리에 강건하다. protan 은 회귀 arm 에서 300/300 반전 | protan 표현 제한 |

**F2 의 해석을 잘못 쓰면 결과를 스스로 부정하게 된다.** 아래 §2 의 문안이 그 경계를 잡는다.

**F2 와 F3 은 방향이 반대이고, 둘 다 참이다.** 회귀자 추가는 피험자 **간** 산포를 팽창시켜 단일사례 검정을 약화시키고, 움직임 제거는 피험자 **내** 색 대응을 선명하게 한다. 각 지표가 어느 성분에 노출되는지가 다르다 (§4 말미).

**움직임 회귀가 기하 성분까지 함께 제거한다는 가설은 기각된다.** 그 가설은 HC 평균의 하락을 예측하는데, 평균은 불변이고(0.456 → 0.458 → 0.483) 산포만 팽창한다. 그리고 기하 종점들은 반대로 움직인다 — protan V1 disparity 는 회귀에서 강해지고(.045 → .0215), 색 특이성은 F3 대로 늘어난다.

---

## 1. 반영 목록

| # | 대상 | 내용 | 상태 | 우선 |
|---|---|---|---|---|
| **A** | `Supplementary/supplementary.tex` §S2 | LOCO 3-arm 표 신설 + `every neural endpoint` 문장 범위 정정 | 원고 준비 완료 | **필수** |
| **B** | `Results/results_v4.tex:38` | CVD 보간 결손에 강건성 단서 1문장 | 원고 준비 완료 | **필수** |
| **C** | `Supplementary/supplementary.tex` §S13 (L464-468) | 순환이동 대조를 색 특이성 순열까지 확장 | 원고 준비 완료 | **필수** |
| **D** | §S15 표 `tab:jnd_baseline` | sub-08 orange–yellow 가 범위 절단 하한임을 각주 | 원고 준비 완료 | **필수** |
| **E** | `Results/results_v4.tex:197` + §S19 | sub-09 개인화 orange–yellow 트랙 불일치 각주 | 원고 준비 완료 | 권장 |
| **F** | `Discussion/discussion_v3.tex:48` 뒤 | U10 — 모형에 균일 회전 항 없음 (정본 §5 요구, 미반영) | 원고 준비 완료 | **필수** |
| **G** | §S2 / §S3 | fMRIPrep 정합 실패를 header-MI 채택 근거로 명시 | 서버 Dice 필요 | 선택 |
| **H** | §S16 신설 + `discussion_v3.tex:44,46` | U2 — β_c 부호 강건성. **분기 B 확정** (deutan 유지 / protan 반전) | 원고 준비 완료 | **필수** |
| **I** | `main.tex` back matter 외 | 형식 잔여 4건 | — | **차단** |

---

## 2. A — §S2 LOCO 3-arm

### 근거

`analysis/future_phase1_sensitivity/scripts/_perm_adjacent_arm.py` → `perm_adjacent_arm_{with_residuals,motreg,motshift}.json`.
`verify()` 가 4 ROI 전부에서 정본 `loco_canonical` 과 1e-12 일치를 확인한다. 원본 arm 은 발표값을 정확히 재현한다 (V1 .393/p=.164, V2 .357/.424, V3 .339/.586, hV4 .456/.011).

**현행 §S2 L46 은 사실과 다르다.**

> Every neural endpoint was recomputed with the six motion parameters and their temporal derivatives added to the second-level design matrix.

실제로 재산출된 것은 disparity, 동결 투영 순열, split-half 신뢰도뿐이었다. **hV4 LOCO adjacent accuracy — 순열 게이트를 통과한 유일한 보간 결과 — 는 재산출된 적이 없다.** 이번에 산출했으므로 이제 이 문장은 참이 되지만, exp2 종점은 여전히 재산출되지 않았으므로 범위를 명시해야 한다.

**결과 (hV4)**

| arm | HC 평균 | HC SD | p_perm | deutan | protan |
|---|---|---|---|---|---|
| 원본 | 0.456 | 0.102 | **.011** | 0.250 (p=.054, d=−2.02) | 0.125 (p=**.011**, d=−3.25) |
| 움직임 회귀 | 0.458 | 0.152 | **.013** | 0.271 (.148, −1.23) | 0.312 (.204, −0.95) |
| 순환이동 대조 | 0.483 | 0.127 | **.002** | 0.375 (.229, −0.85) | 0.229 (.056, −2.00) |

**판독.** HC 평균은 불변(0.456 → 0.458 → 0.483)인데 SD 만 25–50% 팽창한다. 순환이동 대조는 **실제 움직임을 하나도 제거하지 않는데도** 같은 팽창을 보인다(0.127). 따라서 단일사례 검정력 손실의 원인은 움직임 제거가 아니라 **회귀자 12개 추가**다. §S2 가 이미 disparity 에 쓰고 있는 판별식과 동일한 논리다.

기하 종점들은 반대 방향으로 움직인다는 점도 같이 봐야 한다: protan V1 disparity 는 회귀에서 **강해지고**(.045 → .0215), 색 특이성 통과 셀은 **늘어난다**(7 → 15). 회귀가 기하를 비특이적으로 제거하고 있다면 둘 다 반대로 나와야 한다.

### 제안 원고 — §S2 `Motion sensitivity analysis` 문단 정정

**현행 L46 첫 문장을 다음으로 교체**

> Every neural endpoint of the first session was recomputed with the six motion parameters and their temporal derivatives added to the second-level design matrix. The filter-evaluation session was not recomputed, since its endpoints are reported descriptively and carry no inferential claim.

### 제안 원고 — §S2 신설 문단 + 표 (기존 disparity 표 뒤)

> \paragraph{Interpolation under the motion arms.}
>
> Adjacent accuracy at hV4 was recomputed on all three arms under the design of \S S8, with the healthy-control permutation repeated at $N = 1{,}000$ per arm (\cref{tab:motion_loco}). The control gate held throughout: hue interpolation exceeded its own color-label null at hV4 in every arm, and at no other region in any arm. The single-case contrasts did not. The control mean was unchanged across arms while the control standard deviation rose from $0.102$ to $0.152$ under motion regression and to $0.127$ under the shifted control. Because the shifted regressors remove no motion-aligned variance, that inflation is attributable to the twelve added regressors rather than to motion. Leave-one-color-out trains on seven colors per fold, so it carries less residual degrees of freedom than the geometric endpoints and loses precision faster when regressors are added. The single-case interpolation contrasts are therefore reported from the primary arm, with the arms tabulated here.

```latex
\begin{table}[h]
\centering
\caption{Adjacent accuracy at hV4 across the three preprocessing arms. Control
values are the mean over seven controls with the permutation $p$ against
$N = 1{,}000$ per-subject color-label shuffles. CVD entries give adjacent
accuracy with the Crawford--Howell one-tailed $p$ and $d_{cc}$ against the same
controls.}
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

### 판단 근거 (원고에 넣지 않음)

전 ROI 값은 `perm_adjacent_arm_*.json` 에 있다. V1–V3 는 세 arm 어디서도 자기 순열 귀무를 넘지 않으므로 표에 넣지 않고 hV4 만 싣는다. 이 선택은 본문이 이미 "게이트 통과는 hV4 단독" 으로 규정한 것과 일치한다.

---

## 3. B — Results §LOCO 강건성 단서

### 대상

`Results/results_v4.tex:38`, 2문단 (`Both CVD participants fell below the control distribution at hV4 ...`).

### 제안 원고 — 문단 **끝에 1문장 추가** (기존 문장은 건드리지 않음)

> Both single-case contrasts lose significance when the motion parameters are entered as nuisance regressors, through an inflation of the control dispersion that the shifted-regressor control reproduces without removing any motion-aligned variance (Supplementary~\S S2).

### 왜 이 형태인가

- `사라졌다` 가 아니라 `검정력을 잃는다` + 그 원인을 같은 문장에 담는다. 데이터가 지지하는 것은 후자다(HC 평균 불변, 순환이동에서도 동일 팽창).
- 기존 p 값을 고치지 않는다. 1차 arm 이 primary 라는 규칙(정본 R2/R3 의 연장)이 유지된다.
- 리뷰어가 부록에서 발견하기 전에 본문이 먼저 밝힌다. M1(FD 꼬리 통계)에서 이미 쓴 전략과 같다.

---

## 4. C — §S13 순환이동 확장

### 대상

`Supplementary/supplementary.tex:464-468`. 현행 마지막 문장이 미완료를 자인한다.

> The circular-shift control that separates these accounts was applied to the disparity endpoint (S2) and remains to be extended to the permutation reported here.

### 산출

`analysis/validation/scripts/disparity_frozen_permutation.py --data-dir …_motshift`
→ `results/disparity_frozen_permutation_motshift.json`
비교: `analysis/validation/scripts/color_specificity_arm_comparison.py`
→ `results/color_specificity_arm_comparison.json`

### 판정 규칙 (산출 전 확정 — 그대로 적용)

| 패턴 | 결론 |
|---|---|
| 순환이동 ≠ 회귀 | 증가는 **실제 움직임 분산 제거** (해석 1) |
| 순환이동 ≈ 회귀 | 증가는 **회귀자 추가의 부산물** (해석 2) |

### 결과 — 해석 2 가 기각된다

35 셀 BH-FDR, arm 내 보정. 원본 7 · 회귀 15 는 §S13 현행 기술을 정확히 재현한다.

| arm | raw $p<.05$ | **BH $q<.05$** |
|---|---|---|
| 원본 | 16 / 35 | **7** |
| 움직임 회귀 | 18 / 35 | **15** |
| **순환이동 대조** | 13 / 35 | **3** |

순환이동 대조는 같은 회귀자 12개를 시간 정렬만 파괴한 채 넣는다. 해석 2 가 맞다면 이 arm 도 15 근처여야 한다. **3 이다** — 원본의 7 보다도 낮다.

→ 7 → 15 증가는 **회귀자가 데이터와 시간 정렬되어 있을 때만** 나타난다. 즉 **움직임 분산 제거에서 온다**(해석 1). 회귀자 추가의 순수 비용은 검출을 7 → 3 으로 **낮추는** 방향이고, 실제 움직임 제거가 그 손실을 뒤집고도 +8 을 만든다.

**CVD 셀 분해** (움직임 귀속분 = 회귀 − 순환이동, $p$ 단위)

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

**FDR 을 통과하는 두 CVD 셀(deutan V2, protan V3)은 세 arm 전부에서 유지된다.** deutan 의 V1·hV4 는 움직임에 가려져 있었다.

### A/B 와 방향이 반대인 것은 모순이 아니다

두 검정의 귀무가 다르다.

| | 색 특이성 순열 | LOCO 단일사례 |
|---|---|---|
| 비교 대상 | 같은 피험자·같은 arm 의 라벨 순열 귀무 | HC 7명 분포 |
| HC 산포 팽창의 영향 | **없음** (관측·귀무가 같이 이동) | **직격** (Crawford–Howell 분모) |
| 움직임 제거의 영향 | 색 대응이 선명해짐 (+) | — |

회귀자 추가는 **피험자 간 산포를 팽창**시키고(단일사례 검정에 불리), 움직임 제거는 **피험자 내 색 대응을 선명하게** 한다(순열에 유리). 두 결과는 동시에 참이며, 각 지표가 어느 성분에 노출되는지로 설명된다.

### 제안 원고 — §S13 마지막 문단 교체

현행 L464-468 (`Motion regression broadened the pattern ... remains to be extended to the permutation reported here.`) 을 다음으로 교체.

> Motion regression broadened the pattern rather than removing it. The count of cells surviving correction rose from 7 to 15, and the deutan V2 cell held at $q = .025$ while the protan V3 cell held at $q = .012$. We extended the circular-shift control of S2 to this permutation to decide whether the increase reflects the removal of motion-aligned variance or a reshaping of the residual variance by the twelve added regressors. The shifted regressors carry the same autocorrelation and spectrum without temporal alignment to the data, so they impose the cost of the added regressors while removing no motion. Under the shifted control only 3 of the 35 cells survived correction, fewer than the 7 of the primary arm. The increase therefore requires the regressors to be aligned with the data and is attributable to motion-aligned variance; the cost of adding twelve regressors, taken alone, lowers detection. The two cells that survive correction in the primary arm survive in all three arms (deutan V2, $p = .002$, $.003$, $.009$; protan V3, $p = .001$, $.001$, $.032$). The deutan V1 and hV4 cells reach significance only once motion-aligned variance is removed ($p = .105 \to .009$ and $.273 \to .029$, against $.466$ and $.774$ under the shifted control).

> This endpoint moves in the opposite direction to the interpolation contrasts of S2, and the two are consistent. The permutation compares a participant to a label-shuffled null computed within the same participant and arm, so an inflation of between-subject dispersion does not touch it, whereas the single-case interpolation test is referred to the control distribution and is directly exposed to that inflation.

---

## 5. D — §S15 sub-08 orange–yellow 범위 절단

### 근거

`analysis/phase6_behavioral_analysis/scripts/a2_staircase_diagnosis.py`
→ `results/exp2_behavior/a2_staircase_diagnosis.json`

전체 13개 trial 파일 **208 staircase 전수 스캔**. 제시 가능한 최대 수준은 0.95다. 그 수준에서 오답을 낸 staircase는 **정확히 2개**이고 둘 다 sub-08 세션-1 orange–yellow(sc0, sc1)다.

| staircase | n | 최대 수준 | 후반부 평균 | 0.7 이상 비율 | 0.95 오답 |
|---|---|---|---|---|---|
| sub-08 ses1 orange–yellow sc0 | 20 | 0.95 | 0.881 | **1.00** | 1 |
| sub-08 ses1 orange–yellow sc1 | 20 | 0.95 | 0.856 | 0.75 | 1 |

→ 보고된 역치 $t = 0.840$ ($\gamma = 3.02$, $z = +4.15$) 은 추정치가 아니라 **하한**이다.

**방향은 보수적이다.** 기준선 결손이 실제보다 작게 적혀 있었으므로 필터가 만든 개선폭도 과소 보고된 것이다. 값은 고치지 않고 절단 사실만 밝힌다.

### 제안 원고 — `tab:jnd_baseline` 캡션 끝에 추가

> Two staircases returned an incorrect response at the largest presentable separation, both of them the deutan participant's orange--yellow pair, so that threshold is a lower bound rather than an estimate; it is the only such pair among the 208 staircases collected in this study.

### 제안 원고 — §S15 본문 끝에 추가

> The deutan orange--yellow staircases spent their whole course at the top of the presented range and returned incorrect responses at the largest separation the task can present. That threshold is therefore censored, and the true value lies at or above the tabulated one. The censoring understates the baseline deficit and, with it, the improvement recorded under either filter, so the values are reported unadjusted.

---

## 6. E — sub-09 개인화 orange–yellow

### 근거

같은 산출물. sub-09 개인화 조건의 트랙 불일치 0.0813 은 **전부 한 쌍에서 온다** — orange–yellow 를 빼면 0.0193 으로, 본인 기준선 0.0156 과 같은 수준이다.

| 후보 원인 | 판정 | 근거 |
|---|---|---|
| 전역 세션 불량 | ✗ | 나머지 7쌍 정상, deployed 조건도 정상(0.0177) |
| **gamut/렌더링 결함** | ✗ **탈락** | sc1 이 같은 자극에서 0.170 으로 정상 수렴. 렌더링 실패라면 두 트랙이 함께 망가진다 |
| 범위 절단 | ✗ | 최대 0.80 < 설계 상한 0.95 |
| 피로·블록 순서 | ✗ | 이상이 블록 40% 지점에서 시작, 같은 블록 나머지 정상 |
| **단일 트랙 lapse** | ✓ | 같은 트랙 안에서 0.20 정답 → 0.80 오답. 4배 큰 분리를 놓친 것은 민감도가 아니다 |

수치 영향: orange–yellow $z$ = +1.33 (sc1 만 −0.58 / sc0 만 +3.23). 초록 근거인 green–blue 는 두 트랙 모두 정상 수렴(0.135 / 0.080)이라 **영향 없음**. mean $|z|$ 는 0.934 → 0.878/0.841 로 논문값 0.93 이 유지된다.

### 제안 원고 — `results_v4.tex:197` 문단 끝 각주 또는 §S19

> In the protan participant one of the two staircases for orange--yellow diverged from its partner under the individualized filter, settling four times higher after answering correctly at a separation four times smaller earlier in the same block. The pair's partner staircase converged normally on the same rendered stimuli, which excludes a rendering failure, and the remaining seven pairs of that block match the participant's own baseline. The pair is reported on the average of both staircases, as everywhere else; using the converged staircase alone moves it from $z = +1.33$ to $z = -0.58$ and the mean $|z|$ from $0.93$ to $0.84$.

### 선택지

값 조정은 권하지 않는다. 208개 중 이 한 트랙만 문제이므로 제외 규칙을 세우면 사후적으로 보이고, 조정 방향이 결론에 유리한 쪽이라 더 그렇다. **평균 유지 + 전량 공개**가 방어 가능한 선택이다.

---

## 7. F — Discussion U10 (미반영 잔여)

### 근거

정본 `REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md §5` 가 요구했으나 `discussion_v3.tex` 에 없다(grep 확인). §S13 이 protan V1 의 45° 재배열을 보고하는데, 2성분 모형은 균일 회전을 구조적으로 표현할 수 없다($\overline{\delta\theta} = 0$). **C 를 반영하면 §S13 이 더 주목받으므로 이 구멍이 더 노출된다.**

### 제안 원고 — `discussion_v3.tex:48` 문단 끝

> The present model represents distortion of the confusion and S-cone axes and carries no uniform rotation term, so the whole-wheel relabeling recorded at V1 in the protan participant (Supplementary~\S S13) lies outside what it can express. Extending the model to that component is left to future work.

---

## 8. G — fMRIPrep 정합 (선택)

현행 §S2 L43 / §S3 는 header-MI 채택을 `tolerates limited coverage` 라는 일반론으로만 정당화한다. 실제 사유는 **이 데이터의 모든 fMRIPrep 시도에서 정합이 실패했다**는 것이며(사용자 확정 2026-08-10), 이는 NeuroImage 리뷰어의 첫 질문에 직접 답하는 근거다. 서버 트리에서 Dice 하나만 뽑으면 한 문장이 된다 (`analysis/phase0_preprocessing/_archive/registration_method_selection/compute_dice.py`).

**보류 사유**: 서버 접속 필요. 넣지 않아도 원고는 성립하나, 넣으면 방어가 크게 싸진다.

---

## 9. H — U2 β_c 부호 강건성

> 실행 전 확정 문서: [`analysis/phase5_filter_optimization/U2_BETA_SIGN_PRESPEC.md`](../../analysis/phase5_filter_optimization/U2_BETA_SIGN_PRESPEC.md) (커밋 `cdcb6ae`, 실행 전 커밋됨)

### 왜 이것만 성격이 다른가

정본 `HMC_REANALYSIS_PRESPEC.md §6` 이 이미 "재산출 후 최우선 확인 항목" 으로 지정했다. **새 post-hoc 분석이 아니라 그때 미실시로 남은 항목의 이행**이므로 fishing 부담이 없다.

그리고 이것이 논문의 sensitivity chain 에서 유일하게 비어 있는 칸이다.

```
geometry robustness  ──✔ §S2 disparity · §S13 색 특이성 · §S2 LOCO (전부 3 arm)
        ↓
fitted distortion β  ──✘ 전처리 축 미검증                        ← 여기
        ↓
production filter    ──  β 에서 해석적으로 유도
```

현행 원고의 $\hat\beta_c$ 안정성 주장은 **HC 재표집**과 **LOO 재적합**에 한정된다 (`results_v4.tex:111-112`, `discussion_v3.tex:44`). 전처리 축 주장은 없다. 신경 종점은 전부 3 arm 을 통과했는데 그 종점에서 유도되는 생산 파라미터만 통과하지 않은 상태다.

### 실행 사양

바꾸는 것은 amplitude root 하나. 심리물리 $\gamma$ 원자는 행동 데이터라 불변이므로 **움직이는 것은 $L_{\rm RDM}$ 뿐**이다.

| 참가자 | 선정 조합 | combo index | 기준값 |
|---|---|---|---|
| deutan | `γOY\|RDMV2\|noLOCO` | **15** / 71 | $(6^\circ, -42^\circ)$ |
| protan | `γALL\|RDMV1\|noLOCO` | **9** / 11 | $(2^\circ, +24^\circ)$ |

`scripts/neural_loss.py` 에 `COLORBLIND_AMP_ROOT` env override 추가(기본값 = 발표 경로, 기존 재현 경로 불변). **조합 전수 탐색 재실행 금지** (= selection-rule reformulation).

### 판정 규칙 (실행 전 확정)

주 판정 = $\hat\beta_c$ 의 **부호**. 크기는 쓰지 않는다(2성분 12/12 절대복구 실패로 이미 descriptive embedding 제한).

| 분기 | 결론 | 원고 처리 |
|---|---|---|
| **A** deutan $-$ / protan $+$ 유지 | robustness 가 filter-generation chain 까지 이어짐 | §S16 한 문장 (문안은 prespec §7) |
| **B** deutan 만 유지 | 현행 identifiability 와 정합 (protan 은 이미 basis-dependent) | Discussion protan ambiguity 문장을 전처리 축까지 확장 |
| **C** 둘 다 변함 | 부호 대비의 전처리 강건성 **주장 안 함** | `robust individualized distortion estimate` 금지 → `descriptive embedding derived from the primary estimates` |

**어느 분기에서도 불변**: 배포 필터 파라미터, provenance 서술("세션 1 추정, 세션 2 이전 동결"). 동결 시점이 검증 세션보다 앞선다는 성질은 전처리와 무관하다.

### 재현 게이트 — 통과

단일 조합 실행 경로(`--combo-start/--combo-end`)와 `COLORBLIND_AMP_ROOT` override 는 이번에 처음 쓴 경로다. 발표 amplitude 에 같은 경로를 돌려 논문 값이 나오는지 먼저 확인했다.

| | 논문 기재 | 게이트 재실행 |
|---|---|---|
| deutan $(\hat\beta_s, \hat\beta_c)$ | $(6^\circ, -42^\circ)$ | $(6^\circ, -42^\circ)$ ✔ |
| deutan $\overline{L}_{\rm test}$ | $-2.36$ | $-2.359$ ✔ |
| protan $(\hat\beta_s, \hat\beta_c)$ | $(2^\circ, +24^\circ)$ | $(2^\circ, +24^\circ)$ ✔ |
| protan 재표집 IQR | $(0^\circ, 0^\circ)$ | $(0, 0)$ ✔ |
| protan 동일 셀 반복 | 263 / 300 | 263 / 300 ✔ |
| protan $\overline{L}_{\rm test}$ | $-1.54$ | $-1.539$ ✔ |

실행 경로가 검증되었으므로 아래 arm 간 차이는 실제 차이다.

### 결과 — 분기 B

| arm | 참가자 | $\hat\beta_s$ | $\hat\beta_c$ | $\beta_s$ IQR | $\beta_c$ IQR | boundary rate | $\overline{L}_{\rm test}$ | $\beta_c$ 음/양 |
|---|---|---|---|---|---|---|---|---|
| 발표 | deutan | $6$ | $\mathbf{-42}$ | 8 | 2 | 0.09 | $-2.359$ | **300 / 0** |
| 발표 | protan | $2$ | $\mathbf{+24}$ | 0 | 0 | 0.00 | $-1.539$ | **0 / 263** |
| 회귀 | deutan | $20$ | $\mathbf{-48}$ | 38 | 26 | **0.73** | $-1.629$ | **300 / 0** |
| 회귀 | protan | $22$ | $\mathbf{-24}$ | 14 | 10 | 0.00 | $-1.384$ | **300 / 0** |

**deutan 부호는 유지된다** — 두 arm 모두 300/300 음수.

**protan 부호는 반전된다** — 발표 arm 은 263/300 이 정확히 $(2, +24)$ 였고, 회귀 arm 은 300/300 이 음수다. 잡음으로 흩어지는 것이 아니라 **일관되게 반대 방향**을 가리킨다.

**같이 보고해야 할 두 가지**

1. deutan 은 부호가 유지되지만 위치가 크게 불안정해진다: boundary rate $0.09 \to 0.73$, $\beta_c$ IQR $2 \to 26$. **회귀 arm 에서라면 deutan 2성분 적합은 Gate 2 의 collapse guard(`boundary_rate < 0.5`)를 통과하지 못한다.**
2. 두 참가자 모두 held-out test-loss 가 나빠진다($-2.359 \to -1.629$, $-1.539 \to -1.384$).

**기존 서술과 모순되지 않는다.** 원고는 이미 protan 부호를 basis-dependent 로 기술한다(`results_v4.tex:112`, `discussion_v3.tex:46`). 전처리는 **이미 문서화된 불안정성에 두 번째 축을 추가**하는 것이다. 반대로 `discussion_v3.tex:44` 의 $\hat\beta_c$ 안정성 주장은 HC 재표집·LOO 에 한정되어 있었고, 그 범위 밖에서는 성립하지 않는다는 것이 이번에 확인되었다.

### 제안 원고 — `discussion_v3.tex:44` 문단

**첫 두 문장을 교체.** 현행:

> The two fitted distortions diverge, with $\hat\beta_c = -42^\circ$ in the deutan participant against $+24^\circ$ in the protan participant. The sign of $\hat\beta_c$ remained stable when the HC reference set was resampled.

교체안:

> The two fitted distortions diverge on the primary estimates, with $\hat\beta_c = -42^\circ$ in the deutan participant against $+24^\circ$ in the protan participant. The sign of $\hat\beta_c$ remained stable when the HC reference set was resampled, and in the deutan participant it also held when the fit was repeated on the motion-regressed amplitudes, where every one of 300 resamples returned a negative value. In the protan participant that arm returned a negative value on every resample instead, so the divergence between the two fits rests on the primary estimates and not on a preprocessing-invariant property of either.

### 제안 원고 — `discussion_v3.tex:46` 문단, `In the protan participant that sign is basis-dependent.` 뒤

> The same sign reverses when the fit is repeated on the motion-regressed amplitudes, so it is dependent on the analysis path in two independent respects.

### 제안 원고 — §S16 신설 문단

> \paragraph{Refit on the motion-regressed amplitudes.}
>
> The selected loss combination of each participant was refit with the amplitude source replaced by the motion-regression arm of \S S2 and every other element of the procedure held fixed: the same combination, the same grid, the same 300 resamples and seed. The psychophysical atoms are behavioral and do not depend on preprocessing, so the neural RDM term is the only component that differs. The deutan estimate moved from $(6^\circ, -42^\circ)$ to $(20^\circ, -48^\circ)$, negative on all 300 resamples in both arms, while its boundary-saturation rate rose from $0.09$ to $0.73$ and its held-out test-loss from $-2.36$ to $-1.63$; at that saturation rate the fit would not pass the gate of \S\ref{sec:methods:selection}. The protan estimate moved from $(2^\circ, +24^\circ)$, returned by 263 of 300 resamples, to $(22^\circ, -24^\circ)$, negative on all 300. The sign contrast between the two participants is therefore a property of the primary estimates rather than one that survives this change of preprocessing, and the parameters are interpreted accordingly as a descriptive embedding (\S\ref{app:identifiability}).

### 파급 — 표현 제한

분기 B 는 분기 C 의 어휘 제한을 **protan 에만** 적용한다.

| | 허용 | 금지 |
|---|---|---|
| deutan | 부호의 전처리 강건성 주장 가능 (단 boundary rate 병기) | 위치($\beta_s$, $|\beta_c|$)의 강건성 |
| protan | `descriptive embedding derived from the primary estimate` | `robust individualized distortion estimate`, 부호의 강건성 |

**불변**: 배포 필터 파라미터, provenance 서술("세션 1 추정, 세션 2 이전 동결"). 세션 2 는 이 필터로 이미 촬영되었고, 동결 시점이 검증 세션보다 앞선다는 성질은 전처리와 무관하다.

---

## 10. I — 형식 잔여 (제출 차단)

| # | 항목 | 대상 |
|---|---|---|
| I1 | back matter 4절 `\todo{}` 실채움 (CRediT / 이해관계 / 감사 / 데이터 가용성) | `main.tex:110-146` |
| I2 | 데이터 공개 방침 결정 — 기탁(OSF/OpenNeuro) vs 요청 시 제공. **Methods 문장과 Data availability 절을 함께** 고쳐야 한다 | `main.tex` + `methods_v2.tex` |
| I3 | `Supplementary/REVISION_WORKLIST.md` §1 번호표가 stale — S1–S19 로 적혀 있으나 실제 파일은 **S1–S21**. 본문 `\S S…` 참조가 이 표를 근거로 검증되었으므로 재검증 필요 | `REVISION_WORKLIST.md:10-34` |
| I4 | Methods 중복본 6개가 참가자 수를 `Twelve` / `Thirteen` 으로 상충 기술. `main.tex` 는 `methods_v2` 만 `\input` 하나, 코드 공개 시 읽힌다 | `Methods/methods{,_concise,_streamlined,_bibtex,_for_pi}.tex`, `*_backup.tex` |

---

## 11. 반영 순서

```
A·B·C 를 §S2 / §S13 / results_v4 에 한 번에      ← 세 항목이 서로를 참조한다
   ↓
D·E (부록 각주 2건) → F (Discussion 1문장)
   ↓
H prespec 커밋 → 실행 → 결과에 따라 §S16 한 문장
   ↓
G (서버 접속 시)
   ↓
I1–I4 → 빌드 → 최종 교정
```

A·B·C 는 한 묶음이다. B 의 단서 문장이 §S2 의 새 표를 가리키고, C 의 마지막 문단이 §S2 와의 방향 차이를 설명한다. 따로 넣으면 상호 참조가 깨진다.

---

## 12. 미결 — 결정 필요

| # | 항목 | 선택지 |
|---|---|---|
| **Q1** | F3 을 본문으로 올릴 것인가 | 색 특이성은 현재 부록 전용이다. 순환이동 대조로 종결된 지금은 기여 1 의 **직접 증거**가 된다. 다만 `CLAUDE.md` 정책의 "specificity claim 금지" 와 어휘가 겹치므로(그 정책은 *필터 선정 기준*으로서의 HC specificity 를 가리키지만) 확인 없이 올리지 않는다. **권고: 부록 유지 + Results §geometry 에 §S13 포인터 한 개** |
| **Q2** | D — sub-08 절단 표기 | 각주만(권고) / 값 조정 |
| **Q3** | E — sub-09 트랙 처리 | 평균 유지 + 각주(권고) / sc0 제외 |
| **Q4** | G — 서버 Dice 를 뽑을 것인가 | 뽑으면 §S2·§S3 의 header-MI 정당화가 일반론에서 데이터 근거로 바뀐다 |

---

## 13. 산출물

| 항목 | 스크립트 | 결과 |
|---|---|---|
| A·B | `analysis/future_phase1_sensitivity/scripts/_perm_adjacent_arm.py` | `perm_adjacent_arm_{with_residuals,motreg,motshift}.json`, `perm_arm_*_null_*.npy` |
| C | `analysis/validation/scripts/disparity_frozen_permutation.py`, `color_specificity_arm_comparison.py` | `disparity_frozen_permutation_motshift.json`, `color_specificity_arm_comparison.json` |
| D·E | `analysis/phase6_behavioral_analysis/scripts/a2_staircase_diagnosis.py` | `results/exp2_behavior/a2_staircase_diagnosis.json` |

---

## 부록 — U2 산출물 경로

| | 경로 |
|---|---|
| prespec (실행 전 커밋 `cdcb6ae`) | `analysis/phase5_filter_optimization/U2_BETA_SIGN_PRESPEC.md` |
| 재현 게이트 (발표 arm) | `results/s10_inclusion/u2_baseline/s10b_v6_pca_rdm_results_sub-0{8,9}_c*.json` |
| 회귀 arm | `results/s10_inclusion/u2_motreg/s10b_v6_pca_rdm_results_sub-0{8,9}_c*.json` |
| override | `scripts/neural_loss.py` `COLORBLIND_AMP_ROOT` (기본값 = 발표 경로) |

두 arm 모두 `--combo-start/--combo-end` 로 선정 조합 1개만 실행했고 canonical 결과 파일은 건드리지 않았다.
