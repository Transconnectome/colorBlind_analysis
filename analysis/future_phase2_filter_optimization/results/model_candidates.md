# Model Candidates — Selection & Justification

**Date**: 2026-05-21 (revised from 2026-05-20)
**Purpose**: Phase 2 의 *최종* 모델 후보 2 개 (Boehm-aligned R+C, 2-Comp) 선정 정당화.

**Revision history**:
- 2026-05-20 v1 — initial draft
- 2026-05-21 v2 — critic audit 결과 반영 (3 critical issues + AIC 추가 + Robinson NOT APPLICABLE 강등 + JND/8AFC mapping 정정 by NB verification)

**Cross-references**:
- `prior-works.md` — Tregillus/Emery 와의 정확한 inheritance map
- `PI-feedback-priorwork.md` — Living tracker (model & loss validation plan)
- `specificity_metrics_candidates.md` — 평가 지표 후보

---

## §0. Critical reframing — *현재 코드 의 form vs 제안 form 명시*

본 문서는 **proposal**. 기존 코드의 form 과 다음 differences 가 있음:

| Component | 현재 code (`loco_distortion_fit.py`) | 본 문서 proposal |
|---|---|---|
| **R+C DOF** | 2-DOF joint fit (Δλ, g), grid 21×13=273 | **1-DOF (g only)**, Δλ external-fixed. 새 form. |
| **R+C 의 sub-08 결과** | g=−2.25 (non-physiological), Δλ=2.5nm (joint fit) | TBD with new 1-DOF (g 가 physiological range 로 stabilize 예상) |
| **2-Comp form** | δθ(θ) = β_s cos(θ−90°) + β_c cos(θ−θ_conf), 1326 grid | **동일** form. *reframing-not-form*. |
| **2-Comp 의 sub-08 결과** | (β_s=38°, β_c=−14°), LOCO fit | **paper-level interpretation 변경** ("novel descriptor", mechanism claim X), 같은 fit 결과 retained |

→ **R+C 는 *form 변경 proposal***. 2-Comp 는 *interpretive reframing*. 두 model 의 *paper-level position* 모두 변경.

---

## §1. Goal — 왜 2 개로 좁히는가

Phase 2 의 모델 후보 선정은 다음 3 가지 제약 조건 하에:

1. **PI double-dipping 우려 직격 답** — selection criteria 와 evaluation criteria 의 분리 가능한 form
2. **Paper-defensible grounding** — 단순 ad-hoc fit 회피
3. **Filter design 의 실용적 가능성** — stimulus-space 역함수 (pre-image) bijective

NotebookLM 검증 (2026-05-20-21) + 광범위 외부 검색 (2 search agents) 결과:

- **No truly independent grounded alternative** for cortical hue angular distortion in CVD exists in literature.
- *Cone-opponent gain* / *cortical compensation* literature family (Webster/MacLeod/Boehm/Robinson) 가 우리 R+C 의 grounding context.
- *Angular δθ(c) forward model in CVD* 는 우리가 *처음 제안*.

→ **2-model framework 가 정직한 maximum**: grounded mechanism (R+C) + novel descriptor (2-Comp).

---

## §2. Candidate 1 — Boehm-aligned R+C (Primary, grounded mechanism)

### §2.1 Form (PROPOSED CHANGE from current 2-DOF joint fit)

```
Step 1 (FIXED, no fit): Δλ from external source — 3 options:
   (b) DPS 1992 평균값 [protan ~10nm, deutan ~6nm]
   (c) Boehm 2014 grid {3, 8, 13 nm}
   (e) 8AFC-derived (사용자 paradigm 신규) — 정당성 §2.4

Step 2 (FIXED, no fit): Lamb 1995 cone fundamentals at Δλ_fix
       L_AT(λ) = L_normal(λ − Δλ_L_AT)
       M_AT(λ) = M_normal(λ − Δλ_M_AT)

Step 3 (FIXED): r_AT(c) = L_AT(c) − M_AT(c)   ← retinal opponent signal per stim c

Step 4 (1-DOF fit): r_cortical(c) = g · r_AT(c)

Step 5 (PROJECTION): hue_perceived(c) = atan2(r_cortical(c), BY_normal(c))
                     δθ(c) = hue_perceived(c) − c

Total free parameters: 1 (g)
```

> ⚠️ **이는 현재 `loco_distortion_fit.py:113-118` 의 `rc_opponent` (2-DOF joint fit) 와 다른 새 form**. BEST_summary.json 의 sub-08 g=−2.25, sub-09 g=−1.10 은 **현재 2-DOF joint fit 결과**이며 새 1-DOF form 의 결과 아님.
>
> 새 1-DOF form 의 sub-08/09 g 값은 *재fit 필요* (TBD scripts/rc_1dof_fit.py).

### §2.2 Grounding citations (NB-verified quotes)

| Component | Citation | NB verification status |
|---|---|---|
| **Anomalous cone fundamentals (Δλ source)** | DeMarco, Pokorny & Smith 1992 (JOSA-A) — protan M-L'≈10nm, deutan M'-L≈6nm | NB added (CVRL DB) |
| **Cone spectral sensitivity formula** | Lamb 1995 — pigment template formula | Cited in Boehm 2014 (NB verified) |
| **Multiplicative cortical gain (mechanism)** | Boehm, MacLeod & Bosten 2014 | NB verified (date 2026-05-20): "applying a multiplicative gain (an elliptical stretch of the color space), which boosts saturation" — 단 *exact equation form* 은 NB 발췌 내 부재 |
| **Cortical hierarchy (V1 reduction → V2v/V3v amplification)** | Tregillus et al. 2021 | NB verified: "reduced L versus M signal strength is proportional to the reduction in L versus M contrast detection thresholds" |
| **Post-receptoral gain mechanism (theoretical scaffold)** | Emery, Isherwood & Webster 2022 (JOSA A "Gaining the system") | ★ NB verified 2026-05-21 (subagent verification): theoretical scaffold for cortical gain mechanism, citation upgrade only |

### §2.3 정당성 — 각 component 의 직접 quote

**Δλ 고정의 정당성 (사용자 #4 우려 답)**:

Tregillus 2021 직접 (NB verified):
> "this reduction model assumes that all differences between groups are due to photoreceptor sensitivity differences"
>
> "the reduced L versus M signal strength is proportional to the reduction in L versus M contrast detection thresholds"

Emery 2021 직접 (NB verified):
> "L vs M sensitivity differences arise when information from the cones is first combined into color-opponent signals"

→ **"Threshold sensitivity is set by cone fundamentals"** 가 NB-verified 문헌 가설. Δλ 가 *retinal stage* 의 외부 anchor 로 정당.

**g (cortical gain) 의 정당성**:

Boehm 2014 (NB verified):
> "applying a multiplicative gain (an elliptical stretch of the color space), which boosts saturation"
>
> "postreceptoral amplification, operating prior to the compressive transformation, that makes the normal and anomalous postreceptoral representations of color quantitatively comparable"

Tregillus 2021 (NB verified): V2v/V3v 에서 sc > 1 (cortical amplification 직접 측정).

Emery, Isherwood & Webster 2022 (NB-verified 2026-05-21, Fig 1 legend):
> "Gain on the L-M responses independently increased twenty-fold in order to match the range of responses for luminance and chromatic signals"
>
> (p.5) "residual loss in chromatic contrast and an increased response to achromatic contrast"

→ Emery 2022 는 *forward simulation* 으로 post-receptoral gain 의 *상대 민감도 변화 + achromatic axis-leak* 을 직접 보여줌. 우리 g 의 *theoretical scaffold* (mechanism class 의 존재성 grounding) — *parametric value comparison 아님* (NB verified citation upgrade only).

→ 우리 g 는 *post-receptoral 보상* 의 *conceptual* same role. **단 mathematical form 의 *완전한* literature equivalence 는 미입증** (§2.5 참조).

**Selection ≠ Evaluation 의 분리**: Δλ 가 *external source* (8AFC or DPS or Boehm grid) 로 고정 → cortical g 의 fit 은 *neural data 만*. PI 우려 직격 해결.

### §2.4 Δλ source — 3-source robustness check (anomaloscope 없음)

사용자 confirmed: anomaloscope 없음. 3-source agreement check 으로 individual Δλ 추정:

| Source | Pros | Cons | sub-08 적용 |
|---|---|---|---|
| (b) DPS 1992 평균값 | 즉시, well-cited | population mean | protan ~10nm, deutan ~6nm |
| (c) Boehm 2014 grid {3, 8, 13nm} | 즉시, severity-stratified | discrete (3 levels) | sub-08 ≈ medium |
| (e) **8AFC-derived** | individual + 즉시 | **cortical decision involves** (NB-verified, §2.6) | sub-08 confusion matrix → Lamb inverse |

> ⚠️ JND 는 **excluded from Δλ source** (NB-verified mapping, §2.6 참조).

3-source agreement (Δλ_DPS ≈ Δλ_Boehm ≈ Δλ_8AFC) 이면 robust. Disagreement 시 paper 본문 한계 명시.

### §2.5 Mathematical equivalence 평가 — Robinson C vs Boehm gain vs 우리 g

NB-verified (2026-05-21):

| Param | Mathematical form | Quote |
|---|---|---|
| **Robinson C** | $y_s = a \log(b \cdot (s/C) \cdot x)$, C ∈ [s, 1] | "introducing C, a constant between s and 1 reflecting the amount of postreceptoral compensation" |
| **Boehm gain** | "Multiplicative" — 정확 수식 없음 | "multiplicative gain (an elliptical stretch of the color space)" |
| **우리 R+C g** | $r_{cortical} = g \cdot r_{retinal}$ (linear) | (우리 코드) |

**우리 g 와 Robinson C 의 수학적 mapping** (NB verified):
- $g = 1/C$ 의 관계 가능
- *Small-signal*: linear approximation, 두 form 비슷
- *Large-signal*: Robinson 은 log saturation, 우리는 linear 무한 증가 → *다른 곡선*

**VERDICT (NB-verified)**: 
- "Robinson C, Boehm gain, 우리 g — 셋 다 *post-receptoral 보상* 의 same *conceptual role*"
- 그러나 "*mathematical form 은 모두 다름*"
- "Robinson C 가 우리 g 의 *direct mathematical grounding* 인가" → **CONDITIONAL** (개념적 ✓, 수식적 ✗)

→ **paper-level 표현 정정**: "Robinson 2022's compensation parameter C is *conceptually analogous* to our cortical gain g (both representing post-receptoral compensation), but the *mathematical forms differ* (log-compressive vs linear-multiplicative). Robinson 의 *radial saturation* domain 과 우리의 *circular hue angle* domain 의 input geometric mismatch (NB verified NOT APPLICABLE) 로 *direct quantitative equivalence 는 미입증*."

### §2.6 Behavioral measurement layer assignment — NB-verified

사용자 #4 / #3 의 핵심 결정 — NB query (2026-05-21) 결과 *문헌 표준 mapping 이 *우리 paradigm 에 적용*:

| Behav measurement | Layer (NB-verified) | 우리 paradigm 적용 | 정당화 quote |
|---|---|---|---|
| **JND** (2AFC adaptive staircase, hue continuum threshold) | **Retinal cone-limited** | **Δλ estimation source** | Boehm 2014 의 4AFC discrimination 이 retinal anchor. Emery 2021: "detection thresholds may instead be limited by very different constraints or levels of the visual system" |
| **8AFC** (categorical discrimination) | **Cortical/cognitive decision** | **g estimation target** | Emery 2021: "tasks like color naming may be more amenable to cognitive strategies... decision stages of classifying them". Brouwer & Heeger 2013: "categorical color space in V4v and VO1" |

> ⚠️ **사용자 #3 mapping 정정**: 사용자 제안한 "8AFC → Δλ, JND → g" 는 NB-verified 결과 *문헌 mapping 과 반대*. 다음 mapping 으로 진행:
> - **JND → Δλ inversion** (retinal anchor, Lamb inverse) — *adds to 3-source as option (d)*
> - **8AFC → g fit target** (cortical, post-receptoral)
> 
> 이게 *Boehm 2014 의 4AFC threshold-as-retinal* 와 *Brouwer-Heeger 2013 의 categorical-as-cortical* 의 우리 paradigm 적용.

→ **정정된 Δλ source**: (b) DPS + (c) Boehm + **(d) JND-derived** (NB-corrected). 8AFC 는 *g fit target* 으로만.

### §2.7 한계 — Boehm 2021 limitation citation 필수

Boehm, Bosten & MacLeod 2021 (Vis Res 188:85-95, NB pending):
> "the results do not support candidate simple models involving post-receptoral compensation either"

→ Paper limitation:
> "We acknowledge Boehm et al. (2021) as a caveat: simple post-receptoral compensation models do not fully account for AT color discrimination patterns. Our 1-DOF g should be interpreted as the *leading-order term* of cortical compensation, not a complete mechanism."

### §2.8 Filter design 실용성

- Forward map: stim θ → δθ(c) is differentiable in g
- Inverse (pre-image): "어떤 stimulus 를 보여주면 sub-08 의 cortical hue 가 정상화되는가" — **수치적 검증 필요** (TBD: scripts/rc_inverse_check.py, 2-3d)
- ⚠️ Inverse 가 안 풀리면 *filter contribution 손실* → 2-Comp 가 backup

---

## §3. Candidate 2 — 2-Component (Novel descriptor, complementary)

### §3.1 Form — *current Cycle 12 form 과 동일*

```
δθ(θ) = β_s · cos(θ − 90°) + β_c · cos(θ − θ_conf)
        ─────────────────   ───────────────────────
        S-cone cardinal     CVD confusion axis
        (90°, 270°)         (protan 16°, deutan 150°)

Free parameters: 2 (β_s, β_c)
```

> ⚠️ **본 form 은 현재 `forward_models/two_component.py` 의 2-component model 과 *동일***. BEST_summary.json 의 sub-08 (38°, −14°), sub-09 (6°, −22°) 가 *기존 Cycle 12 result* 그대로 retain. **The contribution is the *interpretive reframing as descriptor*, not a new equation.**

### §3.2 정직한 grounding — *novel descriptor, no prior art for the parametric form*

NotebookLM + 광범위 외부 검색 (2 search agents) 결과:
> **No published parametric forward model parameterizes CVD-specific cortical hue angular distortion in this 1st-harmonic cosine form**.

따라서 2-Comp 의 paper-level claim 은 **"novel 1st-harmonic Fourier descriptor"** — *mechanism claim 금지*.

### §3.3 정당성 — 두 축의 *위치* + *왜곡 묘사 도구* 로서의 정당성

**Cardinal axis 위치 정당성**:

| Axis | Cardinal 위치 의 출처 | 정확한 cite |
|---|---|---|
| S-cone (90°/270°) | Krauskopf, Williams & Heeley 1982 — cone-opponent cardinal axes | classical reference |
| L-M confusion axis (protan 16°, deutan 150°) | Stockman & Sharpe cone fundamentals | derived |

> ⚠️ **Cosine *form* 자체는 mathematical (1st-harmonic Fourier)**. Krauskopf 1982 와 Stockman 는 *axis position* 만 grounding, *cosine form* 의 grounding 이 아님.

**왜곡 묘사 도구로서의 정당성**:

사용자 (2026-05-21): "2comp 는 기존 Cycle 12 form 과 동일하나 이 역시도 우리가 왜곡 묘사를 위해서 시도한 것".

본 2-Comp 는 Phase 2 의 Cycle 1~12 (action_plans/PLAN04) 에서 *cortical representational distortion 의 parametric 묘사* 의 목적으로 도입. 형태 자체는 다음 4 가지 합리적 선택의 결과:

1. **Direction-dependent**: 단순 rotation 1-DOF 가 *deutan/protan 의 *subtype-specific 비대칭* 못 capture (Bohon V4 rotation 의 약점)
2. **Parsimonious**: 2-DOF, 8-color 에 적절 (DOF/data ratio 4:1)
3. **Cardinal-anchored**: S-cone + confusion axis 의 두 *생물학적 axis* 가 cos basis 의 phase
4. **Bijective**: pre-image 8/8 exact (sub-08/09 모두) — filter design 의 *수치적 강점*

### §3.4 Paper 본문 명문 (proposed)

> "We characterize the structural distortion of cortical hue representation in CVD using a first-harmonic Fourier descriptor: $\delta\theta(\theta) = \beta_s \cos(\theta − 90°) + \beta_c \cos(\theta − \theta_{conf})$. **The cosine *form* is purely mathematical** (1st-harmonic of the simplest direction-dependent angular shift expansion); **only the *axis positions* (90°, θ_conf)** are grounded in cardinal cone-opponent axes (Krauskopf, Williams & Heeley, 1982) and CVD-specific confusion axis from Stockman cone fundamentals. The descriptor does not claim a specific cortical mechanism; rather, it serves as a quantitative summary of the structural distortion observed in cortical voxel patterns, complementary to the retinal-cortical cascade (R+C) anchored to Boehm 2014, Robinson 2022, Tregillus 2021, Emery 2022, and DeMarco-Pokorny-Smith 1992. The 2-component form was adopted across Cycles 1-12 of model development for its bijective inverse property (8/8 exact for both CVD subjects), making it the primary candidate for stimulus-space filter design."

### §3.5 2-Comp 의 *구조적 강점*

| Strength | 정당성 |
|---|---|
| **Pre-image bijective (8/8 exact, sub-08/09)** | ★ Filter design 의 *수치적* 강점 — paper 의 실용적 contribution |
| **Subtype-specific (θ_conf 가 protan 16°, deutan 150°)** | Stockman confusion axis 직접 인용 |
| **1st-harmonic = parsimonious (2 DOF for 8 colors)** | DOF/data ratio 4:1 적절 |
| **R+C 와 *complementary***: R+C 는 retinal-cortical cascade, 2-Comp 는 *structural geometric descriptor* | 2-level architecture |

### §3.6 한계 — 정직히 명시

| Limitation | Paper 본문 inherit |
|---|---|
| **Cosine 대칭성으로 warm-side 비대칭 capture 불가** (sub-08 의 orange/yellow/purple HYPO + blue HYPER) | `behavioral_alignment_2026-05-19.md` §3 |
| **Prior art 없음** — *novel* claim 정직 | "We introduce, as a complementary descriptor, ..." |
| **Cardinal axis 의 *cortical* grounding 약함** | Parkes 2009: cardinal axes 가 cortex 에서 *유지되지 않음*. 명시 필요. |
| **Mechanism claim 없음** | Emery 2021 식 disclaimer 와 평행 구조 |

---

## §4. 두 모델의 *역할 분담* + Cross-model comparison

```
┌──────────────────────────────────────────────────────┐
│  Boehm-aligned R+C (PRIMARY, grounded mechanism)     │
│  - 1-DOF g (cortical gain)                            │
│  - Δλ from external source (DPS/Boehm/JND-derived)   │
│  - Mechanism: retinal-cortical cascade                │
└──────────────────────────────────────────────────────┘
                            +
┌──────────────────────────────────────────────────────┐
│  2-Component (COMPLEMENTARY, novel descriptor)        │
│  - 2-DOF (β_s, β_c)                                   │
│  - 1st-harmonic Fourier (cosine form)                 │
│  - Mechanism interpretation: NONE (descriptive)      │
│  - Practical contribution: bijective filter pre-image │
└──────────────────────────────────────────────────────┘
                            ↓
┌──────────────────────────────────────────────────────┐
│  Cross-model ablation                                 │
│  - δθ(c) vector convergence (cosine similarity)      │
│  - g vs (β_s, β_c) 의 *predicted δθ(c)* 비교         │
│  - AICc (DOF-penalty) model selection                 │
└──────────────────────────────────────────────────────┘
```

### §4.1 AICc + BIC-based model comparison (DOF-fair) (사용자 #1 요구)

DOF 가 다른 두 model 의 *fair* 비교 위해 AICc + BIC 둘 다 reporting:

```
AICc = n · log(RSS/n) + 2k + 2k(k+1)/(n-k-1)
BIC  = n · log(RSS/n) + k · log(n)
       n = data points (8 colors), k = free parameters
       RSS = residual sum of squares

For R+C (k=1):    AICc_RC = 8·log(RSS_RC/8) + 2 + 6/(8-1-1)
                  BIC_RC  = 8·log(RSS_RC/8) + 1·log(8)
For 2-Comp (k=2): AICc_2C = 8·log(RSS_2C/8) + 4 + 12/(8-2-1)
                  BIC_2C  = 8·log(RSS_2C/8) + 2·log(8)

ΔAICc = AICc_RC − AICc_2C
  < -2: R+C decisively preferred
  -2 ~ +2: indistinguishable
  > +2: 2-Comp preferred

ΔBIC = BIC_RC − BIC_2C
  < -6:  R+C strongly preferred
  -6 ~ -2: R+C moderately preferred
  -2 ~ +2: indistinguishable
  +2 ~ +6: 2-Comp moderately preferred
  > +6:  2-Comp strongly preferred
  > +10: very strong evidence for 2-Comp
```

**BIC vs AICc**: BIC 의 k penalty 는 `log(n)` (n=8 → ~2.08), AICc 의 base penalty 는 `2` (asymptotic). **n=8 일 때 BIC penalty 가 AICc base penalty 의 ~약 1.04 배**; AICc 의 small-sample correction term `2k(k+1)/(n−k−1)` (k=2, n=8 일 때 +2.4) 까지 합하면 R+C(k=1) 와 2-Comp(k=2) DOF 차이 penalty 는 AICc 의 경우 ΔPenalty ≈ +5.4, BIC 의 경우 ΔPenalty ≈ +2.08. → **AICc 가 R+C(parsimonious) 쪽으로 더 강한 penalty 차이 부과**; BIC 는 large-n 에서 parsimony bias 가 더 강하나 n=8 small-sample 에서는 AICc 의 finite-sample correction 이 더 보수적. **두 criterion 이 *agree* 하면 결론 strength 더 강함** (criterion-independence robustness).

**Per-subject 별도 AICc + BIC** + **per-fold (LOO HC) 별도 AICc + BIC** 보고. *DOF-penalty fair comparison* 으로 PI 우려 직격.

### §4.2 *predicted δθ(c)* 의 cross-model convergence

Critic 지적 정확: g (scalar) vs (β_s, β_c) (2D angular) 의 *parameter space convergence* metric 없음. 대신:

```
Both models predict per-color δθ(c) ∈ ℝ⁸ (same space)

Cosine similarity: cos(δθ_RC, δθ_2C) = (δθ_RC · δθ_2C) / (|δθ_RC| |δθ_2C|)
  Range [-1, 1]; > 0.7 = strong convergence

Per-color difference: MAE = (1/8) Σ |δθ_RC(c) − δθ_2C(c)|
  Threshold: < 10° = practical convergence
```

이게 *cross-model convergence* 의 정확한 form (critic 의 issue #1 답).

→ **Paper-level contribution**:
1. **Methodological**: 첫 cortical angular distortion forward modeling in CVD fMRI (R+C 의 우리 paradigm 확장)
2. **Descriptive**: novel 1st-harmonic descriptor (2-Comp) 의 introduction
3. **Practical**: bijective stimulus-space filter (2-Comp pre-image 8/8 exact)

---

## §5. Rejected candidates — 정직한 기록

### §5.1 Bohon V4 rotation 1-DOF R(θ)
- **Rejection 이유**: NotebookLM verification (2026-05-20): Bohon 2016 본인 *수학적 model 없음* — *descriptive observation 만* (MDS embedding ↔ CIELUV correlation).
- **이전 제안의 출처**: OUR EXTRAPOLATION (제 발명) — 정직히 자기 비판 기록.

### §5.2 ~~Robinson 2022/2023 hue-axis 변형~~ — NOT APPLICABLE

- **Rejection 이유 (강화)**: 
  - NotebookLM verification (2026-05-20): Robinson 의 input domain (radial chromatic contrast) 과 우리 (circular hue angle) 의 *geometric dimension 다름*. "NOT APPLICABLE".
  - NotebookLM verification (2026-05-21): C ↔ g 의 *mathematical form 다름* (log nonlinearity vs linear multiplier). "CONDITIONAL grounding only".
- **이전 제안의 출처**: OUR EXTRAPOLATION — 정직히 자기 비판 기록.
- **Cite role**: R+C 의 *conceptual* grounding 으로 cite 가능 (post-receptoral compensation 의 same role), *direct mathematical equivalence 아님*. paper limitation 에 명시.

> ⚠️ **사용자 결정 (2026-05-21)**: "Robinson not applicable, we might use R+C and 2-comp only" → 2-model framework (R+C + 2-Comp) 확정.

### §5.3 Brouwer-Heeger channel gain model
- **Rejection 이유**: HC encoder 의 channel gain 으로 CVD modeling → *stimulus-space inverse 불가*. Filter design 의 *목적* 과 충돌.
- **단** Forward channel model framework 자체는 2-Comp 의 *form-only motivation* 으로 cite.

### §5.4 Fourier warp (4-DOF, 1st+2nd harmonic)
- **Rejection 이유**: 4 DOF / 8 colors = overfitting ceiling. 기존 결과 (`LOCO_FILTER_RESULTS.md`) 에서 *모든 subject 에 1st-harmonic 으로 sufficient*.

### §5.5 Machado 1-way alone
- **Rejection 이유**: Sub-09 의 pre-image 4/8 fail (arc compression). 기존 Phase 2 finding (project memory: "sub-09 reclassified to 2-Comp").
- R+C 의 *retinal stage* 로만 retain (Step 1-3).

### §5.6 3-component cascade (Machado + 2-Comp)
- **Rejection 이유**: 3 DOF / 8 colors = 더 심한 overfitting. 기존 결과 (results path: `results/phase4_preview/`) 에서 *no convergent improvement* — sub-09 c4 sign fail 명시 (project memory `LOCO-Primary Filter Design`).

---

## §6. 다음 단계 — Lock-in 후 진행 (revised cost estimates)

| 작업 | 위치 | 비용 (revised) |
|---|---|---|
| **Emery 2022 NB verification** (theoretical scaffold vs complementary) | NB query | 진행 중 |
| **R+C 1-DOF inverse 수치 검증** (filter pre-image) | scripts/rc_inverse_check.py | **2-3d** (Δλ_fix + g fit + 8 hue inverse + sub-08/09 별도 validation) |
| **3-source Δλ agreement check** (DPS, Boehm grid, JND-derived) | scripts/lambda_3source.py | 1d |
| **R+C 1-DOF refit** (sub-08, sub-09 with each Δλ source) | scripts/rc_1dof_fit.py | 1d |
| **Cross-model ablation** (R+C vs 2-Comp 의 predicted δθ 비교 + AICc) | scripts/cross_model_ablation.py | 1d |
| **Behavioral-only vs neural-only g fit (R+C)** | scripts/g_behav_neural.py | 1.5d |
| **Loss & 평가 방법 finalization** | FITTING_PLAN.md | 1d (13 prior cycles consideration) |
| → **MODEL_LOSS_VALIDATION_PLAN.md lock-in** | | 0.5d |

**합계**: ~8d (sub-09 acquisition 제외).

---

## §7. References (paper-defensible primary set)

### Primary (mechanism grounding)
1. Boehm, A. E., MacLeod, D. I. A., & Bosten, J. M. (2014). Compensation for red-green contrast loss in anomalous trichromats. *Journal of Vision*, 14(13):19.
2. Boehm, A. E., Bosten, J. M., & MacLeod, D. I. A. (2021). Color discrimination in anomalous trichromacy: Experiment and theory. *Vision Research*, 188, 85-95. **[limitation citation]**
3. DeMarco, P., Pokorny, J., & Smith, V. C. (1992). Full-spectrum cone sensitivity functions for X-chromosome-linked anomalous trichromats. *JOSA A*, 9(9), 1465-1476.
4. Emery, K. J., Isherwood, Z. J., & Webster, M. A. (2022). Gaining the system: limits to compensating color deficiencies through post-receptoral gain changes. *JOSA A*, 40(3), A16-A25. **[NB verified 2026-05-21: theoretical scaffold / citation upgrade only — no parametric value comparison]**
5. Krauskopf, J., Williams, D. R., & Heeley, D. W. (1982). Cardinal directions of color space. *Vision Research*, 22(9), 1123-1131. **[2-Comp cardinal axis source]**
6. Lamb, T. D. (1995). Photoreceptor spectral sensitivities: Common shape in the long-wavelength region. *Vision Research*, 35(22), 3083-3091.
7. Stockman, A., & Sharpe, L. T. (2000). The spectral sensitivities of the middle- and long-wavelength-sensitive cones derived from measurements in observers of known genotype. *Vision Research*, 40(13), 1711-1737.
8. Tregillus, K. E. M., Isherwood, Z. J., Vanston, J. E., Engel, S. A., MacLeod, D. I. A., Kuriki, I., & Webster, M. A. (2021). Color compensation in anomalous trichromats assessed with fMRI. *Current Biology*, 31(5), 936-942.

### Stimulus space (DKL design)
9. **Derrington, A. M., Krauskopf, J., & Lennie, P. (1984)**. Chromatic mechanisms in lateral geniculate nucleus of macaque. *Journal of Physiology*, 357, 241-265. **[8-hue DKL ring grounding]**

### Secondary (supporting context, conceptual-only)
10. Bohon, K. S., Hermann, K. L., Hansen, T., & Conway, B. R. (2016). Representation of perceptual color space in macaque posterior inferior temporal cortex (the V4 complex). *eNeuro*, 3(4), ENEURO.0039-16.2016. **[2-Comp form-only context]**
11. Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. *Journal of Neuroscience*, 29(44), 13992-14003. **[forward channel model framework]**
12. Brouwer, G. J., & Heeger, D. J. (2013). Categorical clustering of the neural representation of color. *Journal of Neuroscience*, 33(39), 15454-15465. **[categorical clustering as cortical, supports 8AFC→g]**
13. Emery, K. J., Kuppuswamy Parthasarathy, M., Joyce, D. S., & Webster, M. A. (2021). Color perception and compensation in color deficiencies assessed with hue scaling. *Vision Research*, 183, 1-15. **[Emery disclaimer pattern]**
14. Machado, G. M., Oliveira, M. M., & Fernandes, L. A. F. (2009). A physiologically-based model for simulation of color vision deficiency. *IEEE TVCG*, 15(6), 1291-1298.
15. Parkes, L., Marsman, J.-B., Oxley, D., Goulermas, J., & Wuerger, S. (2009). Multivoxel fMRI analysis of color tuning in human primary visual cortex. *Journal of Vision*, 9(1):1. **[cardinal axes caveat]**
16. Robinson, J. E., Bosten, J. M., & MacLeod, D. I. A. (2022). Nonlinear cortical encoding of color predicts enhanced McCollough effects in anomalous trichromats. *Vision Research*, 203, 108153. **[CONDITIONAL conceptual analogy only — NB-verified NOT APPLICABLE for direct grounding]**

### Negative result
- Boehm 2021 (above #2): "simple post-receptoral compensation models 부족"

---

## §8. AICc + BIC + cross-model comparison details (사용자 #1 신규 추가)

### §8.1 AICc + BIC 계산

```python
def compute_AICc(rss, n_data, k_params):
    """
    rss: residual sum of squares (per-color or per-pair)
    n_data: 8 (color) or 28 (RDM pair)
    k_params: R+C=1, 2-Comp=2
    """
    aic = n_data * np.log(rss / n_data) + 2 * k_params
    correction = 2 * k_params * (k_params + 1) / (n_data - k_params - 1)
    return aic + correction


def compute_BIC(rss, n_data, k_params):
    """
    Parallel form to compute_AICc.
    BIC = n · log(RSS/n) + k · log(n)
    Note: BIC k-penalty is log(n), heavier than AICc base penalty 2
    when n > e^2 ≈ 7.39. For n=8: log(8)≈2.08, so per-k penalty is
    slightly heavier than AICc base; but AICc adds finite-sample
    correction 2k(k+1)/(n-k-1) on top, so AICc differs more strongly
    by DOF in small-n regime.
    """
    return n_data * np.log(rss / n_data) + k_params * np.log(n_data)
```

### §8.2 Per-subject AICc + BIC reporting

```
Subject  | Model     | k | RSS    | AICc   | ΔAICc | BIC    | ΔBIC  | Verdict
sub-08   | R+C 1-DOF | 1 | TBD    | TBD    | -     | TBD    | -     | (R+C 재fit 후)
sub-08   | 2-Comp    | 2 | 0.XX   | XX.XX  | XX    | XX.XX  | XX    |
sub-09   | R+C 1-DOF | 1 | TBD    | TBD    | -     | TBD    | -     |
sub-09   | 2-Comp    | 2 | 0.XX   | XX.XX  | XX    | XX.XX  | XX    |
```

**ΔAICc interpretation**:
- ΔAICc < -2: R+C decisively preferred (despite extra DOF disadvantage)
- ΔAICc ∈ [-2, +2]: indistinguishable
- ΔAICc > +2: 2-Comp preferred

**ΔBIC interpretation** (Kass & Raftery 1995 convention):
- ΔBIC < -10: very strong evidence for R+C
- ΔBIC ∈ [-10, -6]: strong evidence for R+C
- ΔBIC ∈ [-6, -2]: moderate (positive) evidence for R+C
- ΔBIC ∈ [-2, +2]: indistinguishable
- ΔBIC ∈ [+2, +6]: moderate evidence for 2-Comp
- ΔBIC ∈ [+6, +10]: strong evidence for 2-Comp
- ΔBIC > +10: very strong evidence for 2-Comp

**Joint AICc + BIC verdict**:
- *Both agree* (same sign, both pass respective thresholds) → **robust conclusion** (criterion-independent).
- *Disagree* (AICc one way, BIC other) → report 둘 다, paper 본문에 *criterion sensitivity* 명시. BIC 가 parsimony 더 강하게 favor → typical pattern: BIC favors R+C, AICc favors 2-Comp 면 결론 *DOF-sensitive*, conservative reading = R+C.

### §8.3 LOO HC cross-model AICc

Outer HC LOO 7-fold → 각 fold 에 AICc 재계산 → AICc 의 *stability* 평가 (SD across folds).

### §8.4 Cross-model δθ(c) convergence

```python
def cross_model_convergence(delta_theta_RC, delta_theta_2C):
    """
    Both 8-vec per color
    """
    cosine_sim = np.dot(delta_theta_RC, delta_theta_2C) / (
        np.linalg.norm(delta_theta_RC) * np.linalg.norm(delta_theta_2C))
    mae_deg = np.mean(np.abs(delta_theta_RC - delta_theta_2C))
    return cosine_sim, mae_deg
```

Verdict criteria:
- cos > 0.7 AND mae < 10°: **strong convergence** (두 모델 같은 distortion 묘사)
- cos > 0.5 AND mae < 20°: moderate
- 이하: divergence (paper limitation)
