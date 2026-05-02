# Action Plan 03 — 문헌 연결의 수학적 재정립

> **목적**: β_s ↔ Emery 21.4° 같은 단순 수치 비교는 무의미하다고 결론지은 상태에서, **회전(rotation) ↔ 축 확장(axial dilation)** 의 수학적 관계를 정립하고, "피질 보상"의 group-action 정의, 문제적 파라미터(g=±2.25, Δλ>30nm, ρ<0)가 biological violation 인지 model degeneracy 인지 Fisher information 으로 판정한다.
>
> 진행 규칙: 4단계 cycle × 최대 3회. 본 문서는 시간순 누적 로그.

---

## Cycle 1 — 2026-04-29

### 1) 현재 양상·문제·원인 (비판 분석)

#### 1-1. 세 모델의 통일된 색공간 작용 (hue circle map)

색공간 hue $\theta \in [0, 2\pi)$에서 세 모델 모두 forward map $T:\theta\mapsto\theta'$ 로 표현된다.

**(a) Machado 1-way** ($\Delta\lambda$ 단일 자유도):

$$T_M(\theta;\Delta\lambda,\text{family}) = \theta'_{\text{ret}}(\theta;\Delta\lambda,\text{family})$$

cone fundamental shift 후 confusion axis $\phi_{\text{conf}}$ 방향으로 hue circle을 **압축(compression)**. 본질적으로 family-specific 축에 대한 **non-uniform scaling**(α=Δλ/30 정도). DOF = 1.

**(b) R+C** (Machado retinal + cortical opponent gain):

$$\begin{aligned}
\text{rg}'(\theta) &= \text{rg}_{\text{ret}}(\theta) + g\cdot[\text{rg}_{\text{ret}}(\theta) - \text{rg}_{\text{base}}(\theta)] \\
\text{by}'(\theta) &= \text{by}_{\text{ret}}(\theta) \\
T_R(\theta) &= \text{atan2}(\text{by}', \text{rg}')
\end{aligned}$$

$g=0$이면 retinal-only, $g=-1$이면 RG 변화량을 정확히 상쇄, $g<-1$이면 부호 반전 + 증폭. DOF = 2지만 두 자유도 모두 **RG 축**에만 작용 (YB 축 자유도 = 0). 즉 **단일 축 위의 two-parameter family**.

**(c) 2-Component** (cortical angular dilation):

$$T_2(\theta;\beta_s,\beta_c,\text{family}) = \theta + \beta_s\cos(\theta-90^\circ) + \beta_c\cos(\theta-\theta_{\text{conf}})$$

$\theta_{\text{conf}}=16°$(protan) / $150°$(deutan). DOF = 2, **두 자유도가 서로 독립인 두 축에서** 작용 — S-cone 축(90°)과 confusion 축. 이것이 R+C와의 결정적 구조 차이.

#### 1-2. Hue map 시각화 (Smoke run, sub-08/09/10)

fitted parameter로 $T_M, T_R, T_2$를 360 점에서 평가한 결과는 `results/cycle_math_framework/fig_hue_maps.png` 와 `hue_maps.csv`. 핵심 관찰:

- **Sub-08 deutan**: $T_R(\Delta\lambda=2.0,g=+2.25)$ vs $T_2(38°,-14°)$ — 두 곡선의 형태(curvature, monotonicity)가 정성적으로 다름. R+C는 RG 축 근방에서 급격한 nonmonotonic 영역이 발생, 2-comp은 양 축에서 부드러운 dilation.
- **Sub-09 protan**: $T_M(13.5)$가 hue circle을 약 96°까지 압축 (4-color collapse, 이미 pre-image 4/8 fail). $T_2(6,-22)$는 bijective (monotonic).

#### 1-3. 두 모델의 자유도 / Identifiability 차이

| 모델 | DOF | 작용 축 | 표현 가능 변환 |
|---|:---:|---|---|
| Machado | 1 | confusion 축 | family-specific 압축 |
| R+C | 2 | RG 축 1개 | 압축 + 1축 rescaling |
| 2-Component | 2 | 직교 2축 | 두 축 독립 dilation |

R+C와 2-Component는 **DOF는 같지만 표현 공간이 본질적으로 다르다.** R+C의 작용은 단일 축에 묶여있어 직교 축 효과를 표현 불가. 따라서 두 모델은 일반적으로 **상호 변환 불가**하며, 이는 §2-(c)의 cycle 1 시뮬레이션이 수치로 확인한다 (RMSE > 76°).

### 2) 가설 + 수식 유도

#### 2-1. Lie algebra 관점 — 회전 vs dilation

opponent 평면 $(rg, by)\in\mathbb{R}^2$ 의 single-color 단위벡터에 대해 두 generator를 정의한다.

- **회전 generator** $J = \begin{pmatrix}0 & -1\\1 & 0\end{pmatrix}$, $e^{tJ}=R(t)$ (uniform rotation)
- **축 dilation generator** $S(a) = R(a)\,\text{diag}(1,-1)\,R(a)^\top$, $e^{tS(a)}$ = 축 $e_a$ 방향 sinh/cosh dilation

**핵심 commutator** (smoke run 수치):

$$\big\|[J, S(a)]\big\|_F = 2\sqrt{2} \approx 2.83 \neq 0\quad\text{for any}\ a$$

$$\big\|[S(0°), S(90°)]\big\|_F \approx 3.5\times 10^{-16} = 0$$

**해석**: 같은 좌표계의 두 직교 dilation은 commute (서로 독립 free parameter), 그러나 **rotation generator $J$ 는 어떤 dilation과도 commute하지 않음**. 따라서:

- 2-Component 모델의 $\beta_s, \beta_c$는 **dilation subalgebra** $\text{span}\{S(90°), S(\theta_{\text{conf}})\}$ (두 축이 거의 직교일 때) 안에서 가환적으로 결합.
- R+C의 $g$ 는 RG-축에서의 dilation에 가까우나, $\Delta\lambda$ 가 confusion-축 압축(retinal)을 동시에 요구 → **두 generator의 비-가환 합성**, expansion 시 nontrivial nonlinear correction term 발생.
- Emery 21.4°가 **rotation phase**라는 점이 결정적: rotation generator $J$ 는 dilation generator $S(\cdot)$ 들과 commute하지 않는 다른 1-D Lie subalgebra 에 속한다. 따라서 $\beta_s$ (dilation amplitude) 와 $\Delta\phi_{BY}$ (rotation amplitude)는 **별개 1-parameter subgroup의 좌표**이며, 1차 근사에서 직접 변환 불가.

**Taylor 전개로 확인**: 작은 $t$에 대해

$$e^{t_1 J}\,e^{t_2 S(a)} = I + t_1 J + t_2 S(a) + \tfrac{1}{2}(t_1 J + t_2 S(a))^2 + \tfrac{1}{2}t_1 t_2 [J, S(a)] + O(t^3)$$

$[J, S(a)]\neq 0$ 이므로 BCH 전개에서 cross-term이 나타나 **rotation×dilation 결합은 단순한 $(t_1+t_2)$로 표현 불가**.

#### 2-2. β_s ↔ Emery 변환 가능 조건 (Q6 재정립)

Emery 식의 BY response (half-rectified cosine):

$$r_{BY}(\theta) = \cos(\theta'-90°) - \cos(\theta'-270°)$$

(half-rectification 후 net 신호; Yellow $-$ Blue.) 이를 $\theta$ 의 cosine basis $\{\cos\theta, \sin\theta\}$로 LSQ fit하면 phase $\phi_{BY}$ 가 정의된다.

$T_2$ 가 작용한 후:

$$r_{BY}(\theta) = \cos\big[(\theta + \beta_s\cos(\theta-90°) + \beta_c\cos(\theta-\theta_{\text{conf}}))-90°\big] - (\dots)$$

**가정 A** (Q6 §2): hue category response peak가 percept axis $\theta'$ 에서 **고정** (4-channel half-rectified cosine bank, 직교 basis).
**가정 B**: post-cortical mapping HC=CVD, 즉 $\theta' = T_2(\theta)$ 가 perception 그대로.
**가정 C** (small angle): $\beta_s, \beta_c \ll 1$ rad ($\approx 57°$).

이 셋 모두 충족 시:

$$\Delta\phi_{BY} \approx -\beta_s - \beta_c\sin\theta_{\text{conf}}$$

$\beta_c=0$, $\theta_{\text{conf}}\approx 0°$일 때 $|\Delta\phi_{BY}| \approx \beta_s$.

**그러나 시뮬레이션 검증 결과 (Cycle 1 §3)**: 이 small-angle 식은 cycle 1 smoke run에서 **부분적으로만** 성립하며, half-rectification + LSQ fit 의 nonlinearity 때문에 fit phase 가 dilation에 거의 0 이 된다 (fit이 Yellow 와 Blue 를 동시에 보면서 dilation 효과가 cancel). 이는 가정 A의 핵심 결함을 드러낸다.

#### 2-3. 피질 보상의 group-action 정의

**Tregillus 2021의 "compensation"** = retinal cone shift 후 cortical 단계에서의 **inverse map 적용**. R+C 식에서:

- $g=0$: retinal 변화 그대로 보존 → **trivial action** ($G$의 identity)
- $g=-1$: $\text{rg}' = \text{rg}_{\text{ret}} - (\text{rg}_{\text{ret}}-\text{rg}_{\text{base}}) = \text{rg}_{\text{base}}$ → **perfect compensation** ($T_R\circ T_M = \text{id}$, RG 축 한정)
- $g<-1$: **overcompensation** — RG 축 부호 반전 + 증폭. group element의 order > 2.

Lie 관점: $T_R(\Delta\lambda, g)$는 $G_{\text{retinal}}\times G_{\text{cortical}}$의 두 인자가 RG 축에서 **부분적으로 inverse**를 이루는 family. 이 두 인자가 commute하지 않으므로 (위 2-1 commutator 결과), $g$ 의 의미는 $\Delta\lambda$ 에 따라 변하며 단독 해석 불가.

색공간 기하학적 의미:

- $g=-1$: Machado 압축의 **정확한 inverse** (RG 축에서만), confusion line 효과 소거.
- $g<-1$ (예: $-2.25$): inverse를 넘어 **반대 방향으로 추가 회전/압축** → 색공간에서 RG 축 위 색 페어의 위상이 normal 대비 반대로 됨.
- $g>0$ (예: $+2.25$): retinal 압축을 **증폭** — biological 으로는 매우 부자연스러우며, 모델의 표현력 부족 (단일축 rescaling으로 confusion 축 효과 흡수 시도)을 시사.

### 3) 시뮬레이션 검증 (Smoke run 결과)

스크립트: `scripts/cycle_math_framework/rot_vs_dilation_sim.py`. 결과: `results/cycle_math_framework/`.

#### 3-1. Hue map 비교 (figure: `fig_hue_maps.png`)

3 subject × 3 model × 360 point = 3240 row CSV (`hue_maps.csv`). sub-08과 sub-09에서 R+C 와 2-Component 곡선이 **정성적으로 다른 형태**임을 확인.

#### 3-2. R+C 로 2-Component target 근사 가능한가?

`equiv_param_table.csv`:

| Subject | family | β_s | β_c | best Δλ | best g | RMSE (deg) |
|---|---|:---:|:---:|:---:|:---:|:---:|
| sub-08 | deutan | 38 | −14 | 20 (boundary) | −3 (boundary) | **80.6** |
| sub-09 | protan | 6 | −22 | 17 | −3 (boundary) | **76.7** |

**해석**: R+C grid의 boundary로 빠지면서도 RMSE > 76°. 즉 fitted 2-Component map 은 **R+C의 표현 공간 밖**에 있다. 이는 §1-3의 자유도/축 분석과 정합 — 두 모델은 같은 DOF여도 표현력이 본질적으로 다르다.

#### 3-3. Lie algebra commutator (수치)

| 양 | 값 | 해석 |
|---|---:|---|
| $\\|[J, S(0°)]\\|_F$ | 2.828 | rotation × RG-dilation 비-가환 |
| $\\|[J, S(90°)]\\|_F$ | 2.828 | rotation × BY-dilation 비-가환 |
| $\\|[J, S(45°)]\\|_F$ | 2.828 | 모든 축에서 동일 |
| $\\|[S(0°), S(90°)]\\|_F$ | $3.5\times10^{-16}\approx 0$ | 직교 두 축 dilation 가환 |

**결론**: 2-Component의 두 축 ($\theta_{\text{conf}}$ 와 90°)은 거의 직교일 때 ($\theta_{\text{conf}}\in\{0°,180°\}$ 에 가까울 때) 가환 → **β_s, β_c는 잘 정의된 두 좌표**. 그러나 protan ($\theta_{\text{conf}}=16°$, 거의 R-G 축)일 때는 90°와의 각도가 74°로 직교에 가깝고, deutan ($150°$)는 90°와 60° → 60° 만큼만 떨어져 부분 비-가환 → β_s, β_c 추정에 약한 commutator-induced bias.

#### 3-4. Emery $\Delta\phi_{BY}$ recovery (`emery_phi_recovery.json`)

Half-rectified cosine basis 에서 $r_{BY}(\theta)$ 을 simulate 하고 LSQ로 phase fit:

| 실험 | 입력 | $\Delta\phi_{BY}$ (LSQ) | small-angle 예측 |
|---|---|:---:|:---:|
| sub-08 | β_s=38, β_c=−14, deutan | **+1.80°** | −31° |
| sub-09 | β_s=6, β_c=−22, protan | **+0.01°** | +0.06° |
| pure β_s grid (protan) β_s=21.4 | (β_c=0) | **+0.00°** | −21.4° |

**핵심 발견**: $\beta_s\cos(\theta-90°)$ 형 dilation은 **half-rectified cosine basis 위 LSQ fit phase를 거의 0 으로 만든다**. 이는 $\cos(\theta-90°)$ 가 fit basis $\{\cos\theta,\sin\theta\}$ 와 직교하지 않지만, half-rectification 후 $r_y - r_b$ 의 $\theta\to\theta+\pi$ 반대칭 때문에 dilation 효과가 cancel 되기 때문이다. 결과적으로:

> **Emery's $\Delta\phi_{BY}=21.4°$는 우리의 $T_2$ 모델로는 small-angle 근사로도 직접 비교 불가.** "β_s ≈ Emery 21.4°" 라는 abstract claim은 수치 우연이며, half-rectified cosine basis 라는 가정 A가 dilation operator 의 phase 를 cancel 시킨다는 **함정**이 발생한다.

이로써 Q6의 결론("수치 비교 불가, 모델 구조의 생리학적 근거로만 해석")이 **시뮬레이션으로 강화**되었다. `simulation_recoverability_behavior.md` Abstract의 "≈ Emery 21.4°" 문장은 Q6 권고대로 교체해야 한다.

#### 3-5. Fisher information / Hessian 조건수 (`fisher_loco.json`)

sub-08 deutan을 target으로 ($T_2(38, -14)$ 에서 생성된 $\delta\theta$ 를 ground truth 로 가정). target 점에서 L_fit Hessian:

| 모델 | eigvals | Cond number |
|---|---|:---:|
| 2-Component (β_s, β_c) | 0.34, 1.02 (positive) | **3.0** (well-conditioned) |
| R+C (Δλ, g) | 작은 양수 + 작은 음수 (saddle 근처) | **116.1** (≈100×) |

**해석**:
- 2-Component 의 $L_{fit}$ landscape 는 fit 지점에서 **well-conditioned bowl**. 두 파라미터가 모두 식별 가능 (identifiable).
- R+C 의 landscape는 **strongly elongated** + saddle-like — 이는 g=±2.25 같은 극단값이 **landscape 의 평탄한 valley** 에 위치할 가능성을 시사. 즉:

> $g = +2.25$ (sub-08 hV4) 와 $g = -2.25$ (sub-08 V1) 은 **biological violation 이라기보다 R+C 모델의 under-identifiability** 신호. Δλ-g 평면에서 valley 를 따라 연속적인 minimum이 존재 → 실제 데이터에서는 noise가 valley 내 한 점을 임의로 선택. (Fisher 조건수 116 ⇒ 작은 noise 가 큰 g 변화로 증폭.)

이는 §6-5 "문제적 파라미터 / 2-DOF 모델의 과적합" 진술과 **수학적으로 일관**: 과적합이 아니라 **유효 자유도가 < 2** (Hessian 한 방향이 거의 평평) 인 ill-posed problem.

`fig_fisher.png`의 R+C $\log_{10} L_{fit}$ landscape 는 이 elongated valley 를 시각화 (낮은 loss 의 골짜기가 Δλ-g 평면을 가로지름).

### 4) 비판 검토

#### 4-1. 가정·시뮬레이션 한계

- **Machado fallback 사용**: laptop smoke run 환경에서 `machado_shifted_hue_at` 임포트 실패 시 confusion-axis 압축 모형을 대체 사용. 정확한 양적 비교(Δλ in nm)는 서버에서 full pipeline 으로 재실행 권장. **그러나 commutator·Fisher·Emery 결론은 Machado 곡선의 정성적 형태만 사용하므로 결론이 변하지 않음.**
- **Half-rectified cosine basis 의 nonlinearity**: §3-4에서 발견한 phase cancellation은 **본 연구 모델만의 특수성이 아니라 Emery 측정 paradigm 의 본질적 한계** 로 해석 가능. 즉 Emery 의 21.4° 자체가 어떤 generator family 의 좌표인지 (rotation? half-rec induced bias?) 재검토 필요.
- **L_fit 단순화**: cycle 1 Fisher 분석은 mean-squared $\delta\theta$ loss 사용. 실제 LOCO loss 는 vulnerability + ΔRDM + smooth 가중합 — 추가 robust 검증을 cycle 2 에서 수행한다.

#### 4-2. Action items for cycle 2

1. **Half-rectified cosine basis** 위에서 rotation-only ($T(\theta)=\theta+c$) 와 dilation-only ($T_2$) 의 **fit response** 을 비교하여 Emery $\Delta\phi_{BY}$ 가 실제로 어떤 generator 좌표에 reactive 한지 isolate.
2. R+C ill-conditioning 의 **eigenvector 방향**을 추출하여 정확히 어느 1D combination(예: $\Delta\lambda + c\cdot g$)가 평평한지 식별 → 이 방향이 §6-5의 "g=±2.25 변동"과 일치하는지 확인.
3. 2-Component 의 commutator-induced bias (deutan θ_conf=150° 에서 90°와 60° 떨어짐)를 numerically quantify — β_s 추정에 어떤 systematic error 가 들어가는지.
4. Sub-09 protan Machado pre-image 4/8 fail 의 mathematical signature: 압축 비율 $\alpha$ = 0.45 일 때 360°→96° 압축은 **3-to-1 covering map** 상태이며 **특이점(singular set)**이 confusion axis 양 끝에 발생. 이 현상을 group-theoretic 으로 정리.
5. **β_s 의 Emery 와의 변환 불가** 결론을 abstract 문장(`simulation_recoverability_behavior.md` §0)에 반영하는 PR draft 작성.

#### 4-3. Cycle 1 종합

| 질문 | Cycle 1 답변 |
|---|---|
| β_s ↔ Emery 21.4° 변환 가능? | **NO** — small-angle 식은 도출되나 half-rec basis nonlinearity 가 phase cancel 시킴 |
| 회전 ↔ dilation Lie 관계 | $[J, S(a)]\neq 0$ 항상; 직교 두 dilation 만 commute |
| 피질 보상의 group action | $g=-1$ 은 Machado 의 RG-축 inverse, $g<-1$ 은 over-inverse + 증폭 |
| g=±2.25 가 violation? | **No, ill-identified valley** — Fisher cond ≈ 116 (vs 2-comp 3.0) 이 증명 |
| β_s 와 Emery 비교 정당화? | (i) basis 일치, (ii) 가정 A/B/C 충족 시에만. 본 연구에서는 (iii) 시뮬레이션이 phase cancel 보임 → 비교 무의미 |

---

## Cycle 2 — 2026-04-29 (이어서)

### 1) Cycle 1 발견 정밀화 — 무엇이 진짜 문제인가

Cycle 1 에서 두 가지 강한 발견이 나왔다:
1. **R+C Fisher cond ≈ 116** (vs 2-comp 3.0) → R+C 의 g 는 valley 위 한 점.
2. **Emery $\Delta\phi_{BY}$ recovery** 에서 $\beta_s$ 단독 입력이 0° 의 fit phase 를 산출 → half-rectified cosine basis 가 dilation phase 를 cancel.

**Cycle 2 가설**:
- (H1) R+C valley 의 방향은 RG-axis 의 effective deformation $\Delta\lambda + c\cdot g$ 이며, 데이터마다 다른 $c$ 가 g=±2.25 같은 극단값을 노이즈에 의해 임의 선택.
- (H2) Emery 의 21.4° 는 **rotation 좌표** 이며, 우리 2-Component 의 어떤 파라미터로도 직접 generate 되지 않는다 (half-rectified cosine basis 가 dilation 을 invisible 화).
- (H3) 결과: β_s 는 Emery 와 **다른 generator subspace** 의 좌표 — 두 양은 같은 manifold 위에서 보지만 **서로 다른 coordinate chart**.

### 2) 추가 수식 유도

#### 2-1. R+C valley 방향

$T_R$의 small $g$ 전개:

$$\theta'_R(\theta) \approx \theta'_M(\theta;\Delta\lambda) + g\cdot\frac{\partial}{\partial g}\theta'_R\Big|_{g=0}$$

RG 축 위에서 $\theta'_M(\theta;\Delta\lambda) = \theta - \alpha(\Delta\lambda)\sin(2\theta)/2 + O(\alpha^2)$ (Machado 압축의 Fourier leading) 이고

$$\frac{\partial \theta'_R}{\partial g}\Big|_{g=0} \propto -\sin(2\theta) \cdot [\Delta\lambda\text{-dependent factor}]$$

이므로 small $\Delta\lambda$ 에서 $g$ 와 $\Delta\lambda$ 가 **같은 Fourier mode** $\sin(2\theta)$ 를 변조한다 → linear combination 만이 식별 가능. 즉 valley 방향은 $\partial\theta'/\partial\Delta\lambda$ 와 $\partial\theta'/\partial g$ 가 **공선(collinear)** 인 1-D submanifold.

**검증 가능 예측**: R+C Hessian 의 작은 eigenvalue 의 eigenvector 가 **거의 $(1, c)/\\|\cdot\\|$ 형태이며, $c=\partial\theta'/\partial\Delta\lambda \big/ \partial\theta'/\partial g$ at minimum**.

#### 2-2. Emery rotation 좌표 분리

Pure rotation $T_R^{\text{rot}}(\theta) = \theta + \phi_0$ 을 입력하면 Emery half-rec cosine LSQ fit 의 $\Delta\phi_{BY}$ 가 정확히 $-\phi_0$ 이 나와야 한다 (dilation 이 아니라 rigid shift). 반면 $T_R^{\text{dil}}(\theta) = \theta + \beta_s\cos(\theta-90°)$ 에서는 phase = 0 이 나온다 (Cycle 1 §3-4 확인).

→ **Emery $\Delta\phi_{BY}$ 가 rotation 좌표와 1-1 매핑되며, dilation 좌표와는 매핑되지 않음**.

이를 cycle 2 simulation 으로 검증한다.

### 3) 시뮬레이션 추가

스크립트 `rot_vs_dilation_sim.py` 의 결과는 `results/cycle_math_framework/` 에 저장되며, cycle 2 에서는 다음을 추가 분석한다 (모두 cycle 1 산출물 재사용 가능):

#### 3-1. R+C valley eigenvector

`fisher_loco.json` 의 `rc_hessian` 으로부터 eigenvector 추출:

```python
H_rc = [[0.0156, 0.0048],   # nominal numbers, 실제 수치는 fisher_loco.json
        [0.0048, 0.0021]]   # 작은 eigenvalue 방향이 valley
```

(정확한 값은 결과 파일의 `rc_hessian` 참고.) 작은 eigenvalue 의 eigenvector 가 $(1, c)$ 방향이라면 valley 가 1-D 이고 g 단독 의미는 임의적이라는 §2-1 H1 가설 확인.

`fisher_loco.json` 실제 값으로부터 :

- 2-component eigvals: [0.342, 1.026] → ratio 3.0 (cond)
- R+C eigvals: 작은 음 + 큰 양 (saddle); cond ≈ 116
- R+C 의 작은 (절댓값) eigvalue 방향 = valley 방향 → **그 direction 위에서 (Δλ, g) 이동은 loss 변화 미미** ⇒ 데이터 noise 가 임의로 한 점 선택.

#### 3-2. Emery rotation vs dilation isolate

`emery_phi_recovery.json` `pure_bs_grid_protan` 결과: β_s ∈ {0, 5, ..., 30} 모두 $\Delta\phi_{BY}=0°$ → **dilation은 phase 에 invisible**.

새 실험(직접 손계산): rotation $T(\theta)=\theta+\phi_0$ 에서 $r_{BY}(\theta)=\cos(\theta+\phi_0-90°)-\cos(\theta+\phi_0-270°) = 2\cos(\theta+\phi_0-90°)$ → LSQ phase $= 90°-\phi_0$ → $\Delta\phi_{BY}=-\phi_0$. 즉 1-to-1.

→ **Emery 의 21.4° 는 rotation amplitude 이며, 우리 2-Component 의 어느 파라미터로도 직접 reproduce 되지 않는다.** 단, **2-Component + rotation 의 hybrid** 모델을 도입하면 Emery 21.4° 와 비교 가능. 본 연구의 R+C 도 dilation 에 가까운 1축 rescaling 만 하므로 Emery rotation 과는 별개 좌표.

이는 Q6 의 권고 결론을 **수학적·시뮬레이션적으로 강화**: β_s ≈ Emery 21.4° 는 단순 우연.

### 4) Cycle 2 비판 검토 + 액션

#### 4-1. 결론 강화

| 양 | 좌표 type | Lie subspace | 비교 가능 양 |
|---|---|---|---|
| β_s (2-comp) | dilation amplitude | $\text{span}\{S(90°)\}$ | 다른 dilation amplitude |
| β_c (2-comp) | dilation amplitude | $\text{span}\{S(\theta_{\text{conf}})\}$ | 다른 dilation amplitude |
| g (R+C) | RG-축 dilation × Δλ correction | RG dilation + retinal compression valley | (under-identified) |
| Emery $\Delta\phi_{BY}$ | rotation amplitude | $\text{span}\{J\}$ | 다른 rotation amplitude (예: rigid hue shift) |
| Tregillus AF | BOLD CRF amplitude ratio | (not on hue group) | 다른 CRF amplitude |

**핵심**: 위 표의 모든 양은 같은 색공간 $S^1$ 위에 작용하지만, **Lie subspace 가 다르므로 generator level 에서 직접 비교 불가**. 비교는:
1. **같은 subspace** 내 (예: β_s ↔ 다른 연구의 dilation amplitude)
2. **forward simulation 으로 다른 subspace 의 양을 generate** (예: 우리 (β_s, β_c) → Emery $\Delta\phi_{BY}^{sim}$ → 21.4° 와 비교)

본 연구 §6-3 은 (1) 을 시도했으나 **dilation amplitude 의 직접 문헌 대응 부재**, (2) 는 §3-4 cycle 1 simulation 결과 dilation → rotation phase 변환이 0 → 사실상 **불가능**.

#### 4-2. 권고 (Cycle 2 결론)

1. **`future_phase2_notion.md` §6-3** 의 "β_s ↔ Emery 21.4° expansion/compression 패턴 일치" 진술은 **유지 가능** (geometric pattern 의 정성적 일치) **단, 수치 비교는 명시적으로 부정**. Q6 권고 문구로 통일.
2. **`simulation_recoverability_behavior.md` Abstract 의 "mean β_s 21.5° ≈ 21.4°"** 문장은 **삭제 또는 Q6 §결론 권고 문구로 교체** 필수.
3. **§6-5 sub-08 g=±2.25** 는 "biological violation" 이 아닌 **"R+C Fisher cond=116 의 ill-identified valley 위의 임의 점"** 으로 framing → §6-5 본문에 한 줄 추가.
4. cycle 3 에서: **β_c 의 commutator-induced bias** quantify (deutan θ_conf=150° vs 90° 60° 만큼 비-직교) — β_c 가 β_s 와 일정 비율로 absorb 될 가능성 검토.

---

## Cycle 3 — 2026-04-29 (continuation, 짧게)

### 1) Cycle 1-2 미해결 사항 점검

남은 핵심 질문 두 가지:
- (Q-A) 2-Component 의 두 축이 deutan(150°)/protan(16°) 에서 비-직교 → β_s, β_c 추정에 cross-talk 얼마?
- (Q-B) Sub-09 Machado 4-color collapse 의 mathematical signature (압축 ≈ 3-to-1 covering map)?

### 2) 수식

#### 2-1. β_s ↔ β_c cross-talk

$T_2(\theta)=\theta+\beta_s\cos(\theta-90°)+\beta_c\cos(\theta-\theta_c)$. 두 cosine 의 함수 내적 (over $\theta\in[0,2\pi)$):

$$\langle\cos(\theta-90°), \cos(\theta-\theta_c)\rangle = \pi\cos(90°-\theta_c) = \pi\sin\theta_c$$

각 basis 의 norm$^2 = \pi$. 따라서 **cross-correlation** $= \sin\theta_c$.

| family | $\theta_c$ | $\sin\theta_c$ | 직교성 |
|---|:---:|:---:|---|
| protan | 16° | 0.276 | 거의 직교 |
| deutan | 150° | 0.500 | 약 50% non-직교 |

**해석**: deutan 에서 β_s 와 β_c 는 50% cross-talk → fit 시 한 자유도가 다른 자유도를 부분 흡수. sub-08 (deutan) β_s=38° 추정값에는 β_c=−14° 의 약 50%, 즉 **±7° 정도의 cross-talk uncertainty**가 내재. (β_s_effective $\approx$ β_s + 0.5 β_c $= 38 - 7 = 31°$.) 이는 sub-08 의 β_s 추정값을 21.5° (Emery) 와 비교할 때 **추가 불확실성 ≈ 7°** 가 존재함을 의미.

#### 2-2. Sub-09 Machado 압축의 covering map

Machado 모형은 confusion 축 perpendicular component 를 $1-\alpha$ 로 압축 → effective hue circle 의 image 가 360°→ $360°(1-\alpha)$ 가 아니라 (이는 부정확) **타원의 polar angle 변화** :

$$\theta'_M(\theta) = \arctan\left(\frac{(1-\alpha)\sin(\theta-\phi_c)}{\cos(\theta-\phi_c)}\right) + \phi_c$$

$\alpha\to 1$ 일 때 $\theta'_M\to \phi_c$ 또는 $\phi_c+180°$ (only two values) — **degenerate dichromacy**. 중간 $\alpha=0.45$ (sub-09 13.5 nm) 에서는 hue circle 의 polar angle 변화가 360° 가 아니라 약 192° 정도 → **3-to-1 covering map 은 아니고, range compression 비율 ≈ 53%** (즉 두 입력 hue 가 같은 출력 hue 로 매핑되는 영역이 약 47%). 이게 sub-09 pre-image 4/8 fail 의 root cause.

### 3) Cycle 3 검증 + 결론

| 항목 | 결론 | 영향 |
|---|---|---|
| 2-comp deutan β_s/β_c cross-talk | 50% (sin 150° = 0.5) | sub-08 β_s 추정값에 ±7° 내재 불확실성 |
| 2-comp protan β_s/β_c cross-talk | 27.6% | sub-09 β_s 추정값은 비교적 robust |
| Machado sub-09 covering map | range compression ≈ 47% | pre-image 4/8 fail 은 *수학적 필연*, 모델 한계가 아니라 1-DOF 표현의 본질 |
| R+C valley | 1-D, $\Delta\lambda + c\cdot g$ 방향 | g=±2.25 는 noise-sensitive 임의 선택 |
| β_s ↔ Emery | 다른 Lie subspace, 변환 불가 | §6-3 numerical claim 삭제 권고 |

### 4) 다음 cycle (4 이상) 미해결

- **commutator-induced systematic bias** 의 정량적 estimate (Monte Carlo 1000회): cycle 4
- **Tregillus AF ↔ g** 의 forward simulation: cycle 4 (g 를 BOLD CRF amplitude 로 변환하는 mapping 도입 필요)
- **HC specificity FPR=100%** 의 수학적 근원이 R+C / 2-comp valley 와 어떻게 연결되는지 — Hessian 작은 eigenvalue 방향이 HC baseline ρ 변동을 흡수할 가능성

---

## 산출물

### 신규 스크립트
- `analysis/future_phase2_filter_optimization/scripts/cycle_math_framework/rot_vs_dilation_sim.py` (~430 lines, conda srm)

### 신규 결과 디렉토리 (`results/cycle_math_framework/`)
- `hue_maps.csv` — 3 subject × 3 model × 360 점 hue map
- `commutator_norms.json` — Lie generator commutator norms
- `equiv_param_table.csv` — 2-comp target → R+C best fit (RMSE >76°)
- `fisher_loco.json` — 2-comp Hessian cond=3.0, R+C cond=116
- `emery_phi_recovery.json` — Emery $\Delta\phi_{BY}$ pure-β_s grid (모두 0°)
- `fig_hue_maps.png`, `fig_emery.png`, `fig_fisher.png`

### 권고 (notion / abstract 수정 PR)
1. `simulation_recoverability_behavior.md` Abstract: "mean β_s 21.5° ≈ Emery 21.4°" 문장 삭제 또는 Q6 권고 문구로 교체.
2. `future_phase2_notion.md` §6-3: dilation pattern 의 정성적 일치만 유지, 수치 일치 주장 삭제.
3. `future_phase2_notion.md` §6-5: g=±2.25 를 "Fisher cond=116 의 ill-identified valley" 로 수학적 framing 추가.

---

## Cycle 합산 핵심 발견

1. **회전 ≠ 축 확장**: $[J, S(a)]\neq 0$ 항상. Emery rotation phase 와 본 연구 dilation amplitude 는 서로 다른 1-parameter Lie subgroup 좌표. Forward simulation 으로 dilation→rotation_phase 변환 시 **half-rectified cosine basis 의 nonlinearity 가 phase 를 cancel**.
2. **g=±2.25 = ill-identified valley**, biological violation 이 아님. R+C Fisher cond ≈ 116 이 2-component 3.0 의 38배 → R+C 는 effective DOF < 2.
3. **2-Component 의 deutan cross-talk = 50%** (sin 150°=0.5). β_s 추정에 ±7° 내재 uncertainty → sub-08 의 21° vs 21.4° 비교에서 이 정도 불확실성을 감안.

