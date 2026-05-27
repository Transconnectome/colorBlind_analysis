# Mathematical Basis — R+C and 2-Component Forward Models

**Scope**: 두 forward model 의 derivation single source.
- R+C (retinal $r$ + cortical RG-gain $g$): §1–§5, §5.5 (angular projection).
- 2-Component (cortical angular dilation $\beta_s$, $\beta_c$): §5'.
- 공통: §6–§9 (forward summary, pre-image, sanity checks, model 비교).

PPT/논문에서 그림·캡션·수식 인용용. Code-of-truth: `scripts/retinal_cortical.py` (R+C), `scripts/loco_distortion_fit.py` §`get_shifted_design` (2-comp), `scripts/comprehensive_2component_analysis.py`.

**Date**: 2026-05-04
**Companion docs**: `notion.md` §모델, `LOCO_FILTER_PLAN.md`, `behav_validation.md`, `presentation/claude_in_ppt_prompts_meeting.md` Slide 3 / Slide 6.

---

## 0. 표기 규약

| 기호 | 의미 |
|---|---|
| $E(\lambda)$ | 자극 spectral radiance |
| $S_L, S_M, S_S$ | normal cone fundamentals (Stockman 2 deg) |
| $r$ (or $\Delta\lambda$) | retinal parameter — M-cone (deutan) 또는 L-cone (protan) peak shift |
| $g$ | cortical gain — RG opponent 축에만 작용 |
| $\mathbf{c} = (L,M,S)^\top$ | cone responses (3-vector) |
| $\mathbf{o} = (RG, BY)^\top$ | opponent responses (2-vector) |
| $\theta$ | hue angle (rad), $\operatorname{atan2}(BY, RG)$ |
| $\theta_{\mathrm{base}}, \theta_{\mathrm{ret}}, \theta_{\mathrm{final}}$ | baseline · retinal-only · retinal+cortical 후 hue angle |
| $\delta\theta$ | hue distortion (model output, "stimulus-space 보정에 들어갈 입력") |
| $\operatorname{wrap}[\cdot]$ | $(-\pi, \pi]$ 로 wrapping |

**프로젝트 컨텍스트**: 본 모델의 출력 $\delta\theta(c)$ 는 $c \in \{c_1, \ldots, c_8\}$ (8 자극색)에서 평가되어 forward LOCO ridge_gcv encoder 에 들어감. Behavioral filter 는 $\delta(\theta) = -\delta\theta(\theta)$ 를 stimulus 에 적용.

---

## 1. Stage 1 — Stimulus → Cone responses (baseline)

$$
\mathbf{c}_{\mathrm{base}}
=
\begin{pmatrix}
L_{\mathrm{base}}\\
M_{\mathrm{base}}\\
S_{\mathrm{base}}
\end{pmatrix}
=
\int E(\lambda)
\begin{pmatrix}
S_L(\lambda)\\
S_M(\lambda)\\
S_S(\lambda)
\end{pmatrix}
d\lambda
$$

스칼라 형태:

$$
L_{\mathrm{base}} = \int E(\lambda)\, S_L(\lambda)\, d\lambda,
\quad
M_{\mathrm{base}} = \int E(\lambda)\, S_M(\lambda)\, d\lambda,
\quad
S_{\mathrm{base}} = \int E(\lambda)\, S_S(\lambda)\, d\lambda.
$$

---

## 2. Stage 2 — Retinal shift parameter $r$

CVD 가정 (deutan 예시): M cone 의 spectral sensitivity 가 wavelength 축에서 $r$ 만큼 이동.

$$
S_M^{(r)}(\lambda) = S_M(\lambda - r),
\quad
S_L^{(r)}(\lambda) = S_L(\lambda),
\quad
S_S^{(r)}(\lambda) = S_S(\lambda).
$$

(protan 의 경우 동일 형식으로 $S_L \to S_L^{(r)}$ 만 shift.)

Retinal-shifted cone responses:

$$
\mathbf{c}_{\mathrm{ret}}(r)
=
\begin{pmatrix}
L_{\mathrm{ret}}(r)\\
M_{\mathrm{ret}}(r)\\
S_{\mathrm{ret}}(r)
\end{pmatrix}
=
\int E(\lambda)
\begin{pmatrix}
S_L^{(r)}(\lambda)\\
S_M^{(r)}(\lambda)\\
S_S^{(r)}(\lambda)
\end{pmatrix}
d\lambda
$$

스칼라:

$$
L_{\mathrm{ret}}(r) = \int E(\lambda)\, S_L^{(r)}(\lambda)\, d\lambda,
\quad
M_{\mathrm{ret}}(r) = \int E(\lambda)\, S_M(\lambda - r)\, d\lambda,
\quad
S_{\mathrm{ret}}(r) = \int E(\lambda)\, S_S(\lambda)\, d\lambda.
$$

**구현 노트**: 본 프로젝트에서는 $r$ 의 효과를 Machado et al. (2009) 의 $3\times 3$ confusion matrix
$M_{\mathrm{Mach}}(r, \mathrm{family})$ 로 근사한다. 즉

$$
\mathbf{c}_{\mathrm{ret}}(r) \approx M_{\mathrm{Mach}}(r, \mathrm{family})\, \mathbf{c}_{\mathrm{base}}.
$$

이는 spectral integral 을 매번 다시 계산하지 않고 LMS-공간 linear map 으로 대체하는 standard practice (Brettel-Viénot-Mollon 1997 의 sRGB-side counterpart).

---

## 3. Stage 3 — Cone → Opponent (retinal-stage)

선형 opponent transform:

$$
\mathbf{A} =
\begin{pmatrix}
1 & -1 & 0\\
-\tfrac12 & -\tfrac12 & 1
\end{pmatrix},
\qquad
\mathbf{o} = \mathbf{A}\, \mathbf{c}.
$$

따라서

$$
\mathbf{o}_{\mathrm{base}}
=
\begin{pmatrix}
RG_{\mathrm{base}}\\
BY_{\mathrm{base}}
\end{pmatrix}
=
\begin{pmatrix}
L_{\mathrm{base}} - M_{\mathrm{base}}\\
S_{\mathrm{base}} - \tfrac{L_{\mathrm{base}} + M_{\mathrm{base}}}{2}
\end{pmatrix},
$$

$$
\mathbf{o}_{\mathrm{ret}}(r)
=
\begin{pmatrix}
RG_{\mathrm{ret}}(r)\\
BY_{\mathrm{ret}}(r)
\end{pmatrix}
=
\begin{pmatrix}
L_{\mathrm{ret}}(r) - M_{\mathrm{ret}}(r)\\
S_{\mathrm{ret}}(r) - \tfrac{L_{\mathrm{ret}}(r) + M_{\mathrm{ret}}(r)}{2}
\end{pmatrix}.
$$

**중요**: 일반적으로 $\theta_{\mathrm{ret}}(r) \ne \theta_{\mathrm{base}} + r$. $r$ 은 hue angle 을 직접 더하지 않고, cone $\to$ opponent $\to$ atan2 합성을 통해 비선형으로 hue 에 작용한다.

**구현 컨벤션 노트**: 본 derivation 은 LMS-derived opponent ($RG = L-M$, $BY = S-(L+M)/2$) 좌표를 쓰지만, 코드 (`retinal_cortical.py:90-95`) 는 CIELab a*-b* 평면에서 $rg = \cos\theta_{\mathrm{CIELab}}$, $by = \sin\theta_{\mathrm{CIELab}}$ 로 구현. 두 표현은 small-angle 영역에서 선형근사적으로 일치하나 동일하지 않음 (CIELab 는 cone-opponent 의 색지각-등거리화된 nonlinear transform). 본 모델은 두 좌표계의 선형근사 영역에서 작동한다고 가정.

---

## 4. Stage 4 — Cortical gain $g$ on RG axis

핵심 가정: cortical gain 은 retinal stage 가 만든 RG 변화량만 증폭/감쇠하고, BY 축은 건드리지 않는다.

RG 변화량:

$$
\Delta RG(r) = RG_{\mathrm{ret}}(r) - RG_{\mathrm{base}}.
$$

Cortical-stage RG 출력:

$$
RG_{\mathrm{final}}(r,g)
= RG_{\mathrm{ret}}(r) + g\,\bigl[ RG_{\mathrm{ret}}(r) - RG_{\mathrm{base}} \bigr]
= (1+g)\, RG_{\mathrm{ret}}(r) - g\, RG_{\mathrm{base}}.
$$

BY 축은 unchanged:

$$
BY_{\mathrm{final}}(r,g) = BY_{\mathrm{ret}}(r).
$$

**$g$ 해석**:
- $g = 0$ → retinal only (cortex is normal).
- $g = -1$ → exact compensation, $RG_{\mathrm{final}} = RG_{\mathrm{base}}$ (cortex undoes all retinal RG distortion).
- $g < -1$ → overcompensation (over-correction beyond baseline).
- $g > 0$ → retinal distortion 증폭 (cortex makes it worse).

(MEMORY 기록: sub-08 deutan g = -2.25 → non-physiological; sub-09 protan g = -1.10 → cortical-compensation range.)

> ⚠️ **Tregillus 의 "20-40% overcompensation" 같은 수치 범위 와 g 의 직접 비교 금지** — 단위와 layer 가 다름. Tregillus 의 sc 는 BOLD CRF 의 contrast scaling factor (contrast multiplier 단위), 우리 g 는 dimensionless opponent gain. 자세한 매핑은 [`prior-works.md`](prior-works.md) §1.

**신경학적 site (Tregillus 2021, Curr Biol) 에서 차용하는 *가설 구조* (parameter convergence 아님)**: Tregillus 는 AT 의 BOLD CRF 분석에서 V1 은 cone-deficit reduction 그대로, V2v/V3v 에서 cortical amplification 을 *측정*. 본 모델의 $g$ 는 같은 *가설* (cortex 에서의 후-수용체 보상) 을 different observable (8-hue multivariate angular shift) 로 다른 generative form 으로 구현. Tregillus 의 sc 값 자체와 비교할 수 없으나, **"V1 에서 g ≈ 0, extrastriate (hV4) 에서 |g| > 0"** 의 hierarchy 가설은 *Tregillus 와 우리의 공통 prediction*.

---

## 5. Stage 5 — Final hue angle and distortion

Final hue:

$$
\boxed{
\theta_{\mathrm{final}}(r,g)
= \operatorname{atan2}\bigl(\, BY_{\mathrm{final}}(r,g),\; RG_{\mathrm{final}}(r,g) \,\bigr)
}
$$

LMS 풀이형:

$$
\theta_{\mathrm{final}}(r,g)
= \operatorname{atan2}\!\left(
S_{\mathrm{ret}}(r) - \tfrac{L_{\mathrm{ret}}(r) + M_{\mathrm{ret}}(r)}{2},\;
(1+g)\bigl[L_{\mathrm{ret}}(r) - M_{\mathrm{ret}}(r)\bigr] - g\bigl[L_{\mathrm{base}} - M_{\mathrm{base}}\bigr]
\right).
$$

Hue distortion (모델 output):

$$
\boxed{
\delta\theta(r,g) = \operatorname{wrap}\!\bigl[\, \theta_{\mathrm{final}}(r,g) - \theta_{\mathrm{base}} \,\bigr]
}
$$

---

## 5.5. Angular projection — small-$g$ linearization (channel-basis interpretation)

Channel basis 는 angle 만 입력으로 받으므로, $(rg', by')$ cartesian 변형이 channel space 에서 어떻게 보이는지 명시적으로 derive.

$\theta_{\mathrm{final}} = \operatorname{atan2}(by', rg')$ 의 1차 Taylor 전개 (small $g$ 가정, 단위원 근방):

$$
\boxed{\;
\delta\theta_{\mathrm{cortical}}(g)
\approx -g \cdot \sin\theta_{\mathrm{ret}} \cdot \bigl(\, RG_{\mathrm{ret}} - RG_{\mathrm{base}} \,\bigr)
\;}
$$

세 인자의 의미:
- $g$: cortical gain 의 부호·크기.
- $\sin\theta_{\mathrm{ret}}$: cardinal axis ($\theta = 0°, 180°$) 에서 0, diagonal ($\theta = 90°, 270°$) 에서 ±1. **각도 변화는 BY 성분이 0 이 아닐 때만 발생**.
- $\Delta RG = RG_{\mathrm{ret}} - RG_{\mathrm{base}}$: retinal stage 가 만든 RG 변화량. $r = 0$ 이면 0 → $g$ 무관 $\delta\theta = 0$ ($g$ 의 sanity property 의 angular 형태).

**함의**: $g$ 의 angular 효과는 $\theta$ 에 대해 대략 $\sin(2\theta)$ 형태의 wave. 이 wave 의 phase 와 amplitude 가 한 scalar $g$ 로만 조절되는 것이 R+C 의 본질적 1-knob 한계. 2-component 의 $\beta_c$ term ($\cos(\theta - \theta_{\mathrm{conf}})$) 은 이 wave 의 phase 를 독립적으로 풀어주는 추가 DOF 로 해석 가능.

## 5'. Two-component model — formal derivation

R+C 와 병행 위치한 두 번째 forward map. R+C 가 LMS / opponent 좌표계에 작용하는 반면, 2-component 는 **stimulus-space hue angle 에 직접 작용**.

### 5'.1. 입력 정의

**★ Closure (Phase B v6) 의 forward**: $\theta_{\mathrm{base}}(c) = \theta$ — **CIElab nominal hue 그대로** ($c_1 = 0°, c_2 = 45°, \dots, c_8 = 315°$). 변환 없이 trig 에 직접 대입. 구현: `scripts/two_comp.py:forward_2comp` (lines 21–29), `s10b_v6_pca_rdm.py:31,:231,:607` 가 import 하여 호출. 모든 closure step (Phase B v6, `s17_hc_loo`, `s13_round3`, `s12b_phase_c_v2`) + viz (`p2_primary_4col.py`) + Phase 3 자극 합성이 이 정의를 사용. 이력: deutan (38,−10) 의 8-vec δθ 가 [+8.66, +29.46, +33.0, +17.21, −8.66, −29.46, −33.0, −17.21] 로 산출되는 함수.

$\theta_{\mathrm{conf}}$: a priori 고정된 confusion axis 각도 — Stockman cone fundamental 에서 derive.

> **Alternative (NOT closure)** — `scripts/forward_models/two_component.py:dt_2comp` 는 $\theta_{\mathrm{base}}(c) =$ `machado_shifted_hue_at(0, family, θ)` (Stockman opponent space 로 변환된 h_base) 또는 frozen `H_BASE_CANONICAL_8` lookup 을 사용. `loco_distortion_fit.py` 전용 entry 이며 closure 가 호출하지 않음. 같은 (β_s, β_c) 라벨에서 closure forward 와 정반대 부호의 δθ 8-vec 을 산출 (deutan (38,−10) c1: closure +8.66° vs frozen −16.0°). 두 forward 혼용 금지 — see CLAUDE.md A13.
>
> R+C 모델의 *C_baseline* 결정 (MEMORY 2026-04-07: "machado_shifted_hue(0.0, family) for baseline, CIELab nominal angles caused +0.30 L1 artifact") 은 R+C 의 baseline state 를 정하는 별개 규약이며, 2-Component forward 의 입력 변환과 무관.

| Family | $\theta_{\mathrm{conf}}$ |
|---|---|
| protan | 16° |
| deutan | 150° |
| normal (sub-10 specificity check) | 83° |

### 5'.2. Forward map

$$
\boxed{\;
\delta\theta_{\mathrm{2C}}(c; \beta_s, \beta_c)
= \beta_s \cdot \cos\!\bigl(\theta_{\mathrm{base}}(c) - 90°\bigr)
+ \beta_c \cdot \cos\!\bigl(\theta_{\mathrm{base}}(c) - \theta_{\mathrm{conf}}\bigr)
\;}
$$

$$
\theta'(c) = \bigl[\theta_{\mathrm{base}}(c) + \delta\theta_{\mathrm{2C}}(c)\bigr] \mod 360°
$$

### 5'.3. 두 항의 기하학적 의미 — **shear field, NOT axis dilation**

각 cosine term 은 hue circle 위의 **tangential displacement field** 이다 (axis 자체의 stretching 이 아님). 정확한 기하학적 정량은 **local stretch factor**:

$$
\frac{d\theta'}{d\theta}
= 1 + \frac{d(\delta\theta)}{d\theta}
= 1 - \beta\sin(\theta - \theta_{\mathrm{axis}})
\qquad (\beta\text{ in radians})
$$

| 위치 $\theta$ | sin$(\theta-\theta_{\mathrm{axis}})$ | local stretch | 해석 |
|---|---|---|---|
| $\theta_{\mathrm{axis}}$ | 0 | 1 | 단순 translation (no stretching) |
| $\theta_{\mathrm{axis}} + 90°$ | $+1$ | $1-\beta$ | $\beta>0$ → **압축**; $\beta<0$ → 팽창 |
| $\theta_{\mathrm{axis}} + 180°$ | 0 | 1 | translation |
| $\theta_{\mathrm{axis}} - 90°$ | $-1$ | $1+\beta$ | $\beta>0$ → **팽창**; $\beta<0$ → 압축 |

**핵심**: $\beta$ 의 부호는 named axis ($\theta_{\mathrm{axis}}$, $\theta_{\mathrm{axis}}+180°$) 의 dilation 이 아니라, **perpendicular 방향** ($\theta_{\mathrm{axis}}\pm 90°$) 의 asymmetric 압축/팽창을 결정한다. 시각화: `results/visualizations/meeting/two_comp_stretch_anatomy.png` (`figs_2comp_stretch.py`).

| Term | Reference axis | 압축/팽창 일어나는 위치 | Cardinal-axis 선택 출처 (NOT parameter convergence) |
|---|---|---|---|
| $\beta_s \cos(\theta - 90°)$ | S-(L+M) cardinal (90°/270°) | L-M 축 (0°/180°) 양쪽 asymmetric | Cardinal axis 위치 (S at 90°) = Krauskopf-Williams-Heeley 1982 cone-opponent convention. Emery 2021 도 동일 axis 를 사용하지만 *측정 방식 (hue-scaling cosine, MacLeod-Boynton) 과 layer (perceptual descriptive) 가 다름* — see [`prior-works.md`](prior-works.md) §1-§3. $\beta_s$ 값 자체는 Emery 21.4° 와 직접 비교 불가. |
| $\beta_c \cos(\theta - \theta_{\mathrm{conf}})$ | CVD confusion axis | confusion-axis perpendicular 양쪽 asymmetric | Confusion axis 위치 (protan 16°, deutan 150°) = Stockman & Sharpe cone fundamentals 의 isochromatic confusion line. |

**경고**: "S-cone pathway upregulation" 이나 "confusion-axis dilation" 같은 mechanistic 매핑은 1차 근사 framing 일 뿐, 모델의 실제 효과는 위 stretch table 이 정확하다. 미팅·논문에서 "dilation along the named axis" 표현 금지.

**두 direction 은 직교가 아님** (sub-10 specificity 자연 degenerate):
- deutan: 90° vs 150° → $\angle = 60°$
- protan: 90° vs 16° → $\angle = 74°$
- normal: 90° vs 83° → $\angle = 7°$ (거의 collinear)

따라서 $(\beta_s, \beta_c)$ 는 부분적으로 trade-off 가 존재 — joint grid search 필요. Sub-10 normal 은 두 cosine basis 가 거의 같은 함수라 모델이 자연스럽게 underdetermined.

### 5'.4. R+C 와의 본질적 차이

| Property | R+C | 2-Component |
|---|---|---|
| 작용 좌표계 | LMS / opponent (cartesian) | hue angle (modular) |
| 합성 비선형성 | atan2 reduction | additive (modular sum) |
| $\Delta\lambda = 0$ sanity | $g$ 무관 $\delta\theta = 0$ | $(\beta_s, \beta_c) = (0, 0)$ 만 $\delta\theta = 0$ |
| Pre-image bijectivity | 일반 깨질 수 있음 (sub-09 4/8) | bijective (8/8 exact, sub-08·09 모두) |
| 자유 DOF on RG axis | 1 ($g$) | 1 ($\beta_c$ on confusion direction) |
| 자유 DOF on YB axis | 0 | 1 ($\beta_s$ on S-cone direction) |

R+C 의 1-knob 한계 (RG axis 만 free, YB axis 0 DOF) 가 sub-08 의 yellow-green-cyan 4-way collapse 의 mechanistic 원인 (`behav_validation.md` §2). 2-component 의 $\beta_s$ 가 이 missing DOF 를 채워 collapse 해소 (§3 PASS).

### 5'.4b. Single-shear reparameterization $(A, \varphi)$ — 모델의 실효 자유도

두 cosine 의 합은 단일 1st-harmonic shear 로 환원:

$$
\delta\theta(\theta)
= \beta_s \cos(\theta - 90°) + \beta_c \cos(\theta - \theta_{\mathrm{conf}})
= A\cos(\theta - \varphi)
$$

$$
A = \sqrt{\beta_s^2 + \beta_c^2 + 2\beta_s\beta_c\cos(90°-\theta_{\mathrm{conf}})},
\quad
\varphi = \operatorname{atan2}\!\bigl(\beta_s\sin 90° + \beta_c\sin\theta_{\mathrm{conf}},\;
\beta_s\cos 90° + \beta_c\cos\theta_{\mathrm{conf}}\bigr).
$$

**모델의 실효 자유도는 $(A, \varphi)$ — 즉 한 방향의 single shear**. $(\beta_s, \beta_c)$ 는 a priori 두 axis 위의 decomposition 일 뿐. **두 후보가 같은 distortion 인지 비교할 때 $(\beta_s, \beta_c)$ 가 아니라 $(A, \varphi)$ 를 봐야 한다.**

**Sanity check 결과** (`results/diagnostics/aphi_sanity/aphi_polar.png`, 2026-05-04):

| Subject | Source | $\beta_s$ | $\beta_c$ | $A$ | $\varphi$ |
|---|---|---:|---:|---:|---:|
| sub-08 | Phase A V4 | 38 | -14 | 33.3 | 68.6° |
| sub-08 | cycle12 / cycle15_opt2 | 68 | -38 | 59.0 | 56.1° |
| sub-08 | mw_jaccard_V4 | 58 | -36 | 50.7 | 52.1° |
| sub-09 | Phase A V4 | 6 | -22 | 21.1 | **180.2°** |
| sub-09 | cycle12 | 30 | +26 | 44.8 | 56.1° |
| sub-09 | cycle15_opt2 / mw_jaccard_V4 | 44 | +54 | 78.5 | 48.6° |

**함의**:
- **sub-08**: 4 candidates 모두 $\varphi \in [52°, 69°]$ — **shear 방향 일치**, magnitude 만 $A: 33→59$ 차이. 같은 distortion 의 다른 강도 추정.
- **sub-09**: 3/4 candidates $\varphi \in [49°, 56°]$ (sub-08 과 같은 방향), 단 **Phase A 만 $\varphi = 180°$ anti-parallel**. → "두 cluster" 의 정체 = **반대 방향 shear**, **mechanism 자체가 다름**. Behavioral test 의 결정력이 sub-08 보다 sub-09 에서 큼.

### 5'.5. Sanity check

| Case | $\beta_s$ | $\beta_c$ | Result |
|---|---|---|---|
| Identity | 0 | 0 | $\delta\theta = 0$ for all $\theta$ |
| Pure S-axis | $\beta$ | 0 | $\delta\theta = \beta\cos(\theta-90°)$ — translation max at 90°/270°; **stretch effect** max at 0°/180° (L+/L- asymmetry, 부호 의존) |
| Pure confusion-axis | 0 | $\beta$ | translation max at $\theta_{\mathrm{conf}}$; **stretch effect** max at $\theta_{\mathrm{conf}}\pm 90°$ (perpendicular asymmetry) |
| Sub-08 hV4 canonical | 38° | −14° | LOCO ρ=0.881, perm p=0.004**, behav §3 PASS |
| Sub-09 hV4 candidate | 6° | −22° | LOCO ρ=0.690, perm p=0.035*, behav pending |

---

## 6. Forward map summary (8-color encoder input)

자극 set $\{E_c(\lambda)\}_{c=1}^{8}$ 에 대해

$$
\delta\theta_c(r,g)
= \operatorname{wrap}\!\bigl[\, \theta_{\mathrm{final}}(E_c; r, g) - \theta_{\mathrm{base}}(E_c) \,\bigr],
\qquad c = 1, \ldots, 8.
$$

이 8-vector $\boldsymbol\delta\theta(r,g) \in [-\pi,\pi]^8$ 가 ridge_gcv encoder 에 들어가
voxel-prediction LOCO ρ 를 산출한다 (cf. `LOCO_FILTER_PLAN.md` §2).

**Discretization — chroma loss 명시**: encoder 입력은 `basis_full[round(θ_final) % 360]` (FE basis at integer-degree grid). R+C 가 $(rg', by')$ 평면에서 만드는 chroma 변화 $\sqrt{rg'^2 + by'^2} \neq 1$ 은 atan2 reduction 에서 소실되며, channel basis 는 angle 만 인코딩. 따라서 R+C / 2-component 가 forward model 에 미치는 효과는 **각도 변화로만** 측정되며 chroma 모듈레이션은 모델 외부.

---

## 7. Pre-image (inverse problem for stimulus correction)

목표: 관찰자가 $\theta_{\mathrm{target}}$ 을 보도록 만드는 input hue $\theta_{\mathrm{pre}}$.

$$
\theta_{\mathrm{pre}}(\theta_{\mathrm{target}}; r, g)
= \arg\min_{\theta}\, \bigl|\, \theta_{\mathrm{final}}(\theta; r, g) - \theta_{\mathrm{target}} \,\bigr|.
$$

R+C 의 $\operatorname{atan2}$ 합성은 일반적으로 monotone bijective 가 아니므로
(특히 $g \ll -1$ overshoot 영역에서 RG 부호 반전), 8/8 exact pre-image 가 보장되지 않는다.
실측: sub-08 R+C 8/8 부분 통과, sub-09 R+C arc compression 으로 일부 색 unrecoverable.
이 한계가 2-component model 채택의 직접 동기.
(`COMPREHENSIVE_MODEL_RESULTS.md`, MEMORY 2026-04-09 참조.)

---

## 8. Special cases and sanity checks

| Case | $r$ | $g$ | Result | 의미 |
|---|---|---|---|---|
| Normal observer | 0 | 0 | $\theta_{\mathrm{final}} = \theta_{\mathrm{base}}$, $\delta\theta = 0$ | identity check |
| Pure retinal CVD | $r > 0$ | 0 | $\theta_{\mathrm{final}} = \theta_{\mathrm{ret}}(r)$ | Machado 1-way 와 동일 |
| Exact cortical compensation | $r > 0$ | $-1$ | $RG_{\mathrm{final}} = RG_{\mathrm{base}}$, BY 만 retinal-shifted | RG 축 normal, BY 축 만 distorted |
| Overcompensation | $r > 0$ | $g < -1$ | $RG_{\mathrm{final}}$ 부호 반전 가능 | 비-단조, pre-image 불안정 |
| Cortical amplification | $r > 0$ | $g > 0$ | retinal distortion 증폭 | physiological 비현실적 |

---

## 9. Connection to other models in the project

**Machado 1-way (1 DOF, retinal only)**: $g \equiv 0$ 강제. R+C 의 $g = 0$ slice.

**R+C (this doc, 2 DOF)**: retinal $r$ + cortical RG-only gain $g$.
- 작용 stage: cones + opponent RG.
- BY 축 untouched.
- $\operatorname{atan2}$ 합성으로 인한 비선형성 → pre-image 부분 실패.

**2-Component (2 DOF, cortical only)**: stimulus-space 직접 angular operator.
$$\theta' = \theta + \beta_s \cos(\theta - 90°) + \beta_c \cos(\theta - \theta_{\mathrm{conf}})$$
- $r \equiv 0$ (no retinal term).
- 두 angular operator 가 independent → bijective pre-image 8/8 보장 (sub-08, sub-09 모두).
- Behavioral validation 으로 sub-08 채택 (MEMORY 2026-04-17, behav_validation §3).

R+C 와 2-component 의 본질적 차이: R+C 는 LMS / opponent 좌표계에 작용 (atan2 비선형성),
2-component 는 hue angle 자체에 작용 (각도 합 → 항상 invertible).

---

## 10. Visualization spec — pipeline-centric figure (4 panels)

발표/논문용 R+C 시각화 권장 구조. 기존 `presentation/claude_in_ppt_prompts_meeting.md` Slide 3 Column 2
("knob on RG axis" static schematic) 과 별개로, R+C 메커니즘을 단독 슬라이드/논문 그림으로 풀 때 사용.

**원칙**: $r$ 과 $g$ 가 작용하는 stage 를 명시적으로 분리하고, 각 단계에서
**baseline 상태와 변형된 상태를 나란히** 보여준다.

### Panel A — Cone-level retinal shift

X축: wavelength $\lambda$ (400–700 nm). Y축: spectral sensitivity.

세 곡선 $S_L(\lambda), S_M(\lambda), S_S(\lambda)$ 를 그리고, family 에 따라
하나의 cone sensitivity 가 $r$ 만큼 이동하는 것을 dashed overlay 로 표시.

$$
S_M^{(r)}(\lambda) = S_M(\lambda - r) \quad (\text{deutan}),
\qquad
S_L^{(r)}(\lambda) = S_L(\lambda - r) \quad (\text{protan}).
$$

작은 화살표로 shift 방향 표시. 다른 두 cone 은 unchanged.

### Panel B — LMS → opponent transform

작은 inset 또는 텍스트 박스로 변환식 명시:

$$
RG = L - M, \qquad BY = S - \tfrac{L+M}{2}.
$$

baseline cone responses $(L_b, M_b, S_b)$ 와 retinal-shifted $(L_r, M_r, S_r)$
가 각각 $(RG_b, BY_b)$, $(RG_r, BY_r)$ 로 매핑되는 흐름 화살표.

### Panel C — Opponent hue plane (retinal stage)

X축: $RG$. Y축: $BY$. (단위원 또는 좌표평면.)

두 점 표시:
- baseline point: $(RG_{\mathrm{base}}, BY_{\mathrm{base}})$, 각도 $\theta_{\mathrm{base}}$
- retinal-shifted point: $(RG_{\mathrm{ret}}(r), BY_{\mathrm{ret}}(r))$, 각도 $\theta_{\mathrm{ret}}(r)$

두 점을 원호 화살표로 연결, 라벨 $\theta_{\mathrm{ret}} - \theta_{\mathrm{base}}$.

**핵심 메시지**: $r$ 은 hue angle 을 직접 회전시키는 것이 아니라,
LMS → opponent → atan2 합성을 거쳐 비선형으로 hue 를 이동시킨다 (Panel A → B → C).

### Panel D — Cortical RG-axis displacement gain

Panel C 와 같은 좌표평면 위에 retinal point 와 final point 를 모두 표시.

$$
RG_{\mathrm{final}} = (1+g)\, RG_{\mathrm{ret}} - g\, RG_{\mathrm{base}},
\qquad
BY_{\mathrm{final}} = BY_{\mathrm{ret}}.
$$

retinal point 에서 final point 로의 화살표는 **수평** (BY 좌표 변화 없음).

```
       BY
        ↑
        |
        |   retinal point ●─────────● final point
        |                  RG-axis displacement × (1+g)
        |
        |   baseline point ●
        |
        +─────────────────────────────────→  RG
```

**라벨링 주의**: "gain extending/compressing the x-axis" 표현 금지 (좌표축 자체가 변형되는 것처럼 들림).
정확한 표현은 "amplifying / compressing the retinally induced displacement along the RG axis".

### Recommended caption (figure-level)

> The retinal component is visualized as a shift in cone spectral sensitivity (Panel A),
> which changes LMS responses (Panel B) and thereby remaps the stimulus in the opponent
> RG–BY hue plane (Panel C). The cortical component is visualized as a selective gain
> on the retinally induced displacement along the RG axis (Panel D), leaving the BY
> coordinate unchanged before recovering the final hue angle with $\operatorname{atan2}$.

### Two-stage boxed summary (논문/슬라이드 헤더용)

$$
\boxed{\;
r:\ \text{cone sensitivity shift} \;\to\; (L,M,S) \;\to\; (RG, BY) \;\to\; \theta_{\mathrm{ret}}
\;}
$$

$$
\boxed{\;
g:\ RG\text{-axis displacement gain} \;\to\; \theta_{\mathrm{final}}
\;}
$$

---

## 11. References to project artifacts

- Forward fit code: `scripts/loco_distortion_fit.py` (R+C model class)
- Pre-image code: `scripts/preimage_*.py`
- Results: `results/loco_filter/phase_a_rc/`, `results/2component_comprehensive_v2/`
- Behavioral comparison (R+C vs 2-comp): `behav_validation.md` §3 (sub-08 R+C YG-C 4-way collapse FAIL)
- MEMORY: "R+C Model & 2-Component Findings (2026-04-07)", "LOCO-Primary Filter Design (2026-04-09)"
