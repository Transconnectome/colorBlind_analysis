# 필터 강건성 — 정본 vs 움직임 회귀 arm (2026-08-15)

> 라벨 없음. 이 문서는 파일명으로 참조한다 (`FILTER_ROBUSTNESS_ARMS.md`).
> 선행 `REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md` 의 U1–U10 은 그 문서의 미결 목록이며,
> **U3 는 거기서 이미 "35개 색 특이성 셀 BH-FDR" 로 쓰이고 있다.** 혼동 방지를 위해 여기서는 U 번호를 쓰지 않는다.

> **발단**: 외부 검토 2차 (2026-08-15). `U2_BETA_SIGN_PRESPEC.md` 가 답한 것은 **파라미터**의 전처리 강건성이었다.
> 검토자의 지적: 정작 물어야 할 것은 **피험자가 실제로 본 물리적 변환**이 바뀌는가이다.
>
> **선행**: [`U2_BETA_SIGN_PRESPEC.md`](U2_BETA_SIGN_PRESPEC.md) — β 추정. 그 문서의 `U2` 는
> `REVISION_PLAN_MOTION_GEOMETRY_2026-08-06.md:363` 의 미결 항목 U2("필터 provenance — motreg arm 재적합 미실시")를 가리킨다.
> **코드**: `scripts/filter_robustness_arms.py` · **결과**: `results/filter_robustness_arms/filter_robustness_arms.json`
>
> **재적합 없음.** `U2_BETA_SIGN_PRESPEC.md` 가 낸 두 β 쌍을 그대로 받아 pre-image 를 푼 **결정론적 귀결**이다.
> forward = `two_comp.forward_2comp` (closure A13), pre-image = `exp2_compute_preimage.py` 와 동일 해법.

---

## 0. 결론

| | deutan (sub-08) | protan (sub-09) |
|---|---|---|
| β 부호 | 유지 (300/300 음) | **반전** (263/300 양 → 300/300 음) |
| **필터** | **강건** — 부호 반전 0/8, $r = +0.955$ | **반전** — 부호 반전 **6/8**, $r = -0.567$ |
| 판정 | **가능성 A** — parameter non-identifiability | **가능성 C** — **intervention non-identifiability** |

**deutan 은 파라미터가 흔들려도 필터가 살아남는다.** protan 은 그렇지 않다.
그리고 protan 은 검토자가 상정한 것보다 한 단계 더 나쁘다 (§3).

### 이것은 첫 확인이 아니라 두 번째 확인이다

**교란축이 무엇인지 명확히 해 둔다. 이 분석은 시간축(움직임 회귀) 하나만 흔든다** —
F1–F3, U2 와 **같은 축**이며, 그 축을 인과 사슬 아래로 한 칸 더 내린 것이다
(종점 → β → **필터**). 정합·디페이싱과는 무관하다.

기저축(PCA↔SRM)에서는 이미 같은 계산이 있었고 **판정이 수렴한다**
(`project_color_specificity_gap.md`):

| | PCA (정본) | SRM | 필터 차이 |
|---|---|---|---|
| deutan | $(6, -42)$ | $(8, -42)$ | mean $|\Delta|$ 1.4°, **ΔE₀₀ 0.64** = 자기 효과 10.7 의 **6%** |
| protan | $(2, +24)$ | $(32, 0)$ | mean $|\Delta|$ 26.6°, **ΔE₀₀ 11.7 > 자기 효과 4.4** |

**protan 은 세 분석 선택에서 질적으로 다른 세 해를 낸다** — $(2, +24)$ / $(32, 0)$ / $(22, -24)$.
$\beta_c$ 가 양수·0·음수를 모두 오간다. deutan 은 셋 다 $\beta_c \approx -42 \sim -48$ 한 가족이다.

**따라서 protan 필터 불안정은 두 독립 축에서 확인되었고, deutan 강건성도 두 축에서만 확인되었다.**
**공간축(정합)은 세 칸 모두 비어 있다** — 그리고 시간축이라는 더 약한 교란이 이미 protan 을
뒤집었으므로, 공간축이 deutan 을 흔들지 않는다는 보장은 없다. → `STATUS_ADDITIONAL_ANALYSIS` §1 격자.

---

## 1. 사전 확인 — 역상 유일성 (closure invariant A5)

두 arm 모두 순사상 $\theta \mapsto \theta + \delta\theta(\theta)$ 가 순증가이고 역상이 유일하다.
$\beta$ 가 커지면 접힘(fold)이 생겨 A5 가 무너질 수 있으므로 먼저 확인했다.

| | 단조 | $\min d\theta_{\rm perc}/d\theta_{\rm disp}$ | 역상 근 개수 |
|---|---|---|---|
| deutan primary $(6, -42)$ | ✔ | $+0.313$ | 1,1,1,1,1,1,1,1 |
| deutan motion $(20, -48)$ | ✔ | $+0.271$ | 1,1,1,1,1,1,1,1 |
| protan primary $(2, +24)$ | ✔ | $+0.570$ | 1,1,1,1,1,1,1,1 |
| protan motion $(22, -24)$ | ✔ | $+0.516$ | 1,1,1,1,1,1,1,1 |

**A5 는 네 조합 모두에서 성립한다.** 아래 비교는 잘 정의된 두 필터의 비교다.

---

## 2. 색별 필터 회전량 $\delta\theta_{\rm apply}$

### deutan (sub-08) — 부호 반전 없음

| hue | primary | motion | 차 |
|---|---|---|---|
| red | $-37.91$ | $-35.99$ | $+1.93$ |
| orange | $-32.11$ | $-41.21$ | $-9.10$ |
| yellow | $+31.99$ | $+13.80$ | $-18.19$ |
| green | $+37.94$ | $+41.73$ | $+3.79$ |
| cyan | $+26.08$ | $+32.78$ | $+6.71$ |
| blue | $+9.15$ | $+16.39$ | $+7.25$ |
| purple | $-9.08$ | $-2.32$ | $+6.76$ |
| magenta | $-26.02$ | $-20.73$ | $+5.28$ |

부호 반전 **0/8** · mean $|{\rm diff}|$ **7.38°** · max **18.19°**
Pearson $r = +0.955$ · cosine $+0.954$ · 원형 $r = +0.964$
필터 크기 자체는 거의 같다 (mean $|\delta\theta|$ 26.28° vs 25.62°).

### protan (sub-09) — 6/8 반전, 음의 상관

| hue | primary | motion | 차 | 반전 |
|---|---|---|---|---|
| red | $-19.01$ | $+17.41$ | $+36.42$ | **YES** |
| orange | $-24.63$ | $+3.68$ | $+28.31$ | **YES** |
| yellow | $-13.91$ | $-10.79$ | $+3.12$ | |
| green | $+16.00$ | $-22.93$ | $-38.93$ | **YES** |
| cyan | $+24.56$ | $-27.57$ | $-52.13$ | **YES** |
| blue | $+18.12$ | $-10.13$ | $-28.25$ | **YES** |
| purple | $+6.11$ | $+23.24$ | $+17.13$ | |
| magenta | $-7.29$ | $+26.73$ | $+34.02$ | **YES** |

부호 반전 **6/8** · mean $|{\rm diff}|$ **29.79°** · max **52.13°**
Pearson $r = \mathbf{-0.567}$ · cosine $-0.567$ · 원형 $r = -0.571$

**두 필터는 무관한 정도가 아니라 서로 반대 방향이다.** 색 간격이 45° 이므로
평균 29.8° 불일치는 **약 0.66 색 단계**에 해당한다.

---

## 3. 2×2 교차평가 — 검토자 제안, 그리고 그보다 한 칸 더

각 필터의 역상을 상대 모형에 통과시켰을 때 관찰자가 겪을 **잔여 색상 오차**(deg).
검토자의 2×2 에 **무필터 기준선**을 한 줄 추가했다. 그 줄이 없으면 "다르다"까지만 말할 수 있고
**"해로운가"** 를 말할 수 없다.

### deutan (sub-08)

| | model $M_P$ | model $M_M$ |
|---|---|---|
| **무필터** | 25.70 / 36.37 | 26.09 / 41.57 |
| 필터 $F_P$ | 0.00 / 0.00 | **7.80** / 11.96 |
| 필터 $F_M$ | 7.97 / 12.15 | 0.00 / 0.00 |

*(mean / max)*

**교차 칸이 무필터보다 3배 이상 좋다.** 생산 필터 $F_P$ 는 대안 모형이 참이었더라도 왜곡의
**70%를 여전히 교정**했을 것이다 (26.09 → 7.80). 이것이 검토자의 **가능성 A** 다:
파라미터는 유일하게 식별되지 않지만, **실행 가능한 역변환은 상대적으로 강건하다.**

### protan (sub-09)

| | model $M_P$ | model $M_M$ |
|---|---|---|
| **무필터** | 16.08 / 23.07 | **17.77** / 27.19 |
| 필터 $F_P$ | 0.00 / 0.00 | **29.26** / **45.83** |
| 필터 $F_M$ | 30.17 / 45.94 | 0.00 / 0.00 |

**교차 칸이 무필터보다 나쁘다.** 대안 모형이 참이었다면, 이 참가자가 실제로 착용한 생산 필터는
평균 색상 오차를 **17.77° → 29.26° 로 65% 악화**시켰을 것이고 최악 오차는 27.19° → 45.83°
(45° 색 간격을 초과)로 거의 두 배가 된다.

**이것이 검토자의 가능성 B 를 넘어선다.** 두 필터가 "다르다"가 아니라, 한쪽이 참이면 다른 쪽은
**아무것도 안 하느니 못하다.**

---

## 4. 대안 모형을 기각할 수 있는가 — 두 피험자가 정반대다

가장 곤란한 비대칭이 여기 있다.

| | boundary rate (motion arm) | 사전지정 Gate 2 (`boundary_rate < 0.5`) |
|---|---|---|
| deutan | **0.73** | **불통과 → 사전지정 근거로 기각 가능** |
| protan | **0.00** | **통과 → 기각 근거 없음** |

**deutan 의 대안 모형은 원고 자신의 사전지정 적합성 기준으로 버릴 수 있다.** 그래서 deutan 의
필터 강건성은 조건부가 아니다 — 대안이 애초에 채택 불가이고, 채택 가능했더라도 필터는 살아남는다.
**이중으로 안전하다.**

**protan 의 대안 모형은 깨끗하다.** boundary saturation 0.00, IQR (14, 10). 사전지정 기준 어디에도
걸리지 않는다. 버릴 명분이 없다.

### held-out test-loss 로 우열을 가릴 수 없다

primary $-1.539$ vs motion $-1.384$ 로 primary 가 낮지만, **두 손실은 서로 다른 전처리
데이터에서 계산되었다.** 다른 데이터 위의 손실값은 비교 가능하지 않다. 이 경로로 대안을
기각하려는 시도는 통계적으로 성립하지 않는다. (기록해 두는 이유: 가장 먼저 떠오르는 탈출구이고,
잘못된 것이기 때문이다.)

---

## 5. exp2 데이터가 판정에 쓰일 수 있는가 — 시사적이나 결정적이지 않다

$M_M$ 이 참이었다면 $F_P$ 는 protan 에게 평균 29° 회전을 남겼을 것이다. 실제 관측:

| | 무필터 | 개인화 |
|---|---|---|
| 8AFC (적합에 미사용) | 1.00 [0.94, 1.00] | 0.98 [0.92, 1.00] |
| JND mean $|z|$ | 0.90 | 0.93 |

**측정 가능한 열화가 없다.** $M_M$ 이 예측하는 악화가 관측되지 않았다는 점에서 $M_M$ 에 불리하다.

**다만 이 논증은 약하다. 세 가지 이유로 결정적이지 않다.**

1. 무필터 상태에서도 $M_M$ 은 이미 17.8° 왜곡을 예측하는데, 그 상태에서 8AFC 는 1.00 이다.
   17.8° 를 견딘 관찰자가 29.3° 를 못 견딘다는 보장이 없다.
2. 8AFC 는 **8개 이름표 중 선택**이다. 일관된 회전은 학습된 라벨링으로 상쇄될 수 있어,
   회전 크기와 식별 정확도가 단조 관계가 아니다.
3. 사후 논증이다. 사전지정된 검정이 아니다.

→ **"$M_M$ 과 부합하지 않는 관측"** 으로만 적을 수 있고, **"$M_M$ 을 기각한다"** 로는 적을 수 없다.

---

## 6. 원고 파급

### 살아남는 것 (전처리와 무관)

- 필터가 세션 2 **이전에** 동결되었다는 provenance. 전향적 구조 자체는 불변이다
- deutan 의 개인화 필터 서술 전체
- 세션 1 상류 결과 (decodability 보존 / 연속 조직 손상)

### 바뀌어야 하는 것 — protan 한정

| 현행 함의 | 교체 |
|---|---|
| `robustly identified individual cortical distortion 의 inverse 를 검증` | `하나의 preprocessing-contingent production model 에서 파생되어 사전 동결된 필터의 전향적 시험` |
| protan 필터를 개인화 교정의 사례로 제시 | 개인화 **구성**의 사례로만 제시. 그 역변환이 유일 식별되었다는 함의 제거 |

### 신설해야 하는 것

§S16 에 아래 §2–3 표를 넣는다. **β 결과만 보고하고 필터 결과를 빼면 안 된다** — β 부호 반전만 보고하면
독자는 필터도 반전되었다고 추정하는데, deutan 에서는 그것이 **거짓**이고 protan 에서는
**참보다 더 나쁘다**. 두 피험자의 방향이 반대이므로 필터 수준까지 내려가야 정확해진다.

### deutan 서술은 오히려 강화된다

`파라미터는 유일 식별되지 않으나, 그로부터 유도된 역변환은 대안 전처리에서도 왜곡의 70%를
교정한다` 는 **β 수준 결과 단독으로는 할 수 없던 진술**이다. 이 분석이 새로 벌어준 것이다.

---

## 7. 한계 (반드시 병기)

1. **2성분 모형 내부의 정합성 계산이다.** 두 모형 중 무엇이 옳은지에 대해 아무 말도 하지 않는다.
   $M_P$ 도 $M_M$ 도 ground truth 가 아니다
2. 잔여 오차는 **모형이 예측하는** 색상 오차이지 측정된 지각이 아니다
3. 두 β 쌍은 `U2_BETA_SIGN_PRESPEC.md` 가 낸 point estimate 다. 재표집 분포 전체를 통과시킨 필터 분포는 산출하지 않았다
   (가능하나, 결론이 이미 point estimate 수준에서 갈린다)
4. 전처리 축 하나만 흔들었다. 기저(PCA/SRM) 축은 이 분석 범위 밖이며, protan 은 그 축에서도
   이미 의존적임이 알려져 있다 — **즉 protan 의 필터 불안정성은 최소 두 축에 걸쳐 있다**

---

## 8. 재현

```bash
conda activate srm
python analysis/phase5_filter_optimization/scripts/filter_robustness_arms.py
```

입력 없음(β 하드코딩, U2 출처 주석). 결정론적. 정본 산출물 미변경.

---

## 9. 공간축 추가 — `hmc_v2` arm 3-arm 비교 (2026-08-16)

§7 한계 4("전처리 축 하나만 흔들었다")를 닫는다. `U2_BETA_SIGN_PRESPEC.md` §5 절차를 그대로 쓰고 `COLORBLIND_AMP_ROOT` 만 `full_dataset_C010_hmc_v2` 로 바꿨다. **조합 전수 탐색·gate 재적용·ROI 재선정 없음.** 판정 규칙은 사전 확정된 §6 (주 판정 = $\hat\beta_c$ **부호**, 크기는 판정에 쓰지 않음).

**deutan (sub-08)** — combo `γOY|RDMV2|noLOCO`, N=300 재표집

| arm | $\hat\beta_c$ median | $P(\hat\beta_c<0)$ | $\hat\beta_s$ median | $\beta_c$ 하단 edge | $\beta_c$ 상단 edge | $\beta_s$ edge | train loss |
|---|---|---|---|---|---|---|---|
| baseline | $-42$ | 1.00 | 6 | .00 | .00 | .09 | $-2.892$ |
| motreg | $-48$ | 1.00 | 20 | .36 | .00 | .37 | $-2.691$ |
| **hmc_v2** | $\mathbf{-46}$ | **0.95** | 20 | .28 | .00 | .44 | $-2.234$ |

**protan (sub-09)** — combo `γALL|RDMV1|noLOCO`, N=300 재표집

| arm | $\hat\beta_c$ median | $P(\hat\beta_c<0)$ | $\hat\beta_s$ median | $\beta_c$ 하단 edge | $\beta_c$ 상단 edge | $\beta_s$ edge | train loss |
|---|---|---|---|---|---|---|---|
| baseline | $+24$ | 0.00 | 2 | .00 | .00 | .00 | $-1.681$ |
| motreg | $-24$ | 1.00 | 22 | .00 | .00 | .00 | $-1.730$ |
| **hmc_v2** | $\mathbf{-12}$ | **0.79** | 24 | .00 | .11 | .00 | $-1.482$ |

### 9.1 판정 — 분기 B

| | 판정 |
|---|---|
| **deutan** | **부호 유지 (3/3 arm).** 이로써 시간축·기저축·**공간축** 세 축 전부에서 유지 |
| **protan** | **부호 반전 (2/2 교란 arm).** 기저축(ΔE₀₀ 11.7)까지 합해 세 축 전부에서 불안정 |

`U2_BETA_SIGN_PRESPEC.md` §6 **분기 B** — "현행 identifiability 결과와 정합. deutan 강, protan 모호" → 조치: Discussion 의 protan ambiguity 문장을 **전처리 축까지 확장**.

**protan 의 반전은 분산이 아니라 배타적이다.** baseline 은 300 중 263 이 $+24$, 나머지 37 이 $0$ — **음수가 한 번도 없다.** motreg 은 218 이 $-24$, 82 가 $-34$ — **양수가 한 번도 없다.** 두 arm 의 지지집합이 겹치지 않는다. hmc_v2 는 224 가 $-12$ 로 음수 쪽이나 상단 edge($+50$)에 32 가 남아 baseline 만큼 깨끗하지 않다.

### 9.2 deutan 에 반드시 병기할 단서 — 조건수 악화

부호는 유지되지만 **교란 arm 에서 적합이 나빠진다.** 결합 `boundary_rate` 가 baseline .09 → motreg .73 → hmc .72 로, 정본 선택 규칙이 쓰는 **`boundary_rate < 0.5` 문턱을 두 교란 arm 모두 넘는다.** 즉 정본 arm 이 고른 조합은, 교란 arm 위에서 재적합하면 **정본 arm 자신의 경계 기준을 만족하지 못한다.**

**이것을 근거로 재선정하지 않는다** (selection-rule reformulation 금지). 사실만 병기한다.

다만 이 악화는 **부호 주장을 훼손하지 않는다.** deutan 의 edge 적중은 세 arm 전부 $-50$ 쪽 단측이고 $+50$ 은 **0.00** 이다 — 경계 고착이 중앙값과 **같은 부호 방향**으로만 밀린다. 퇴화는 크기에 있고, 크기는 애초에 판정에 쓰지 않는다(2성분 모형 12/12 절대복구 실패 → descriptive embedding).

### 9.3 원고 서술 (§S16 또는 Discussion)

> Refitting the same loss combination on the motion-regression and the realignment arms, with every other element of the procedure held fixed, preserved the sign of $\hat\beta_c$ for the deutan participant on both arms ($-42$, $-48$, $-46$; negative in at least 95% of resamples throughout) and reversed it for the protan participant on both ($+24$ to $-24$ and $-12$; the primary and motion-regression resample distributions do not overlap in sign). The fit for the deutan participant was more poorly conditioned on the perturbed arms, with the fraction of resamples reaching a grid boundary rising from 0.09 to 0.72–0.73; these boundary solutions lie on the same side as the median, so they bear on the magnitude rather than the sign. The psychophysical atoms do not depend on preprocessing, so the neural term is the only component that differs between arms.

### 9.4 산출

`results/filter_robustness_arms/beta_sign_three_arms.json`, `results/s10_inclusion/u2_hmc_v2/`
