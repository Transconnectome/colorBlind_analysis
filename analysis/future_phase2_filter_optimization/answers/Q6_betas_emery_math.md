# Q6. β_s (2-Component) vs Emery 21.4° B-Y phase shift — 수학적 비교 가능성

## 1. 두 양의 정의 (수학적 형태)

**본 연구 2-Component (cortical-level hue distortion)**:

$$\theta'(\theta) = \theta + \beta_s \cdot \cos(\theta - 90^\circ) + \beta_c \cdot \cos(\theta - \theta_{conf})$$

여기서 β_s [deg] 는 **B-Y 축(θ=90°) 부근에서의 피크 각도-편이(amplitude of dilation)**. 즉 perceptual hue가 자기 자신에 대해 받는 displacement의 크기.

**Emery et al. 2021 (PMC8058247)**: 응답 비율 $r_k(\theta)$ ($k\in\{R,G,B,Y\}$) 를 half-rectified cosine으로 fit:

$$r_k(\theta) = A_k \cdot \max\left(0,\ \cos\!\big(\tfrac{2\pi}{P_k}(\theta - \phi_k)\big)\right)$$

→ B-Y response의 best-fit **phase parameter** $\phi_{BY}$가 normal에서 127.5°, AT에서 106.1°. 차이 $\Delta\phi_{BY}=21.4°$는 **응답 함수의 peak 위치 회전(peak orientation rotation)**.

따라서:
- β_s : **stimulus→percept mapping**의 dilation amplitude (각도 = 변위량)
- φ_BY (Emery) : **stimulus→response amplitude**의 peak phase (각도 = 위치)

물리적으로 같은 "도(degree)" 단위일 뿐, 측정 대상이 다르다.

## 2. 비교 가능 조건 (forward derivation)

비교를 위해서는 우리 모델로부터 Emery 식의 $\phi_{BY}$를 forward로 유도해야 한다. 가정: hue category response가 percept 각도 $\theta'$에 대해 정렬된 fixed cosine bank ($\phi_k^{percept}$ 고정)라면,

$$r_k(\theta) = \max\!\big(0,\ \cos(\theta'(\theta) - \phi_k^{percept})\big)$$

θ'의 peak (즉 $r_k$가 1이 되는 stimulus θ)에서 $\theta'(\theta^*) = \phi_k^{percept}$ → $\phi_k^{stim} = \theta'^{-1}(\phi_k^{percept})$.

**Small-angle approximation** (β_s, β_c << 1 rad):

$$\theta'^{-1}(\phi) \approx \phi - \beta_s \cos(\phi - 90°) - \beta_c \cos(\phi - \theta_{conf})$$

B-Y 채널 ($\phi_k^{percept}=90°$)의 경우:

$$\Delta\phi_{BY} = -\beta_s \cdot \cos(0°) - \beta_c \cdot \cos(90° - \theta_{conf}) = -\beta_s - \beta_c \sin(\theta_{conf})$$

→ **β_s 단독 조건** ($\beta_c=0$ 또는 $\theta_{conf}\approx 0°$)에서: $|\Delta\phi_{BY}| \approx \beta_s$. 따라서 β_s를 Emery 21.4°와 비교하려면 **(i) β_c가 R-G 축($\theta_{conf}\approx 0°$ 또는 180°)에 정렬되어 B-Y에 직교, (ii) β_s, β_c 모두 작아 small-angle이 성립, (iii) hue-scaling response peak가 percept 각도에서 fixed**라는 세 조건이 동시에 성립해야 한다.

본 연구 추정값(sub-08: β_s=20°, β_c=−14°, θ_conf=−45°; sub-09: β_s=23°, β_c=+3°, θ_conf=−10°)에서 β_c sin(θ_conf) 기여는 sub-08 ≈ +9.9°, sub-09 ≈ −0.5°. 즉 **sub-09에서만 β_s ≈ |Δφ_BY| 근사가 성립**, sub-08은 β_c 보정항이 무시 불가능.

## 3. 일치성 검증 시뮬레이션 제안

추정된 (β_s, β_c, θ_conf)로 θ'(θ)를 generate → uniform hue stimuli 360개에 대해 4-channel half-rectified cosine response simulate → least-squares로 $\phi_{BY}^{sim}$ recover → Emery 21.4°와 비교. **귀무가설 검정**: 무작위 (β_s, β_c) ~ Uniform[−30°,30°]² 으로 같은 forward pass 1000회 → $\phi_{BY}^{sim}$ 분포에서 21.4°가 차지하는 percentile. 본질적 일치라면 우리 추정값이 분포의 tail (p<0.05)에 위치해야 한다.

## 4. 두 문서 모순 해소

`simulation_recoverability_behavior.md` Abstract의 **"mean β_s 21.5° ≈ Emery 21.4°"**는 (i) sub-08/09 두 명 평균이며 (ii) β_c·sin(θ_conf) 보정 미적용 (iii) small-angle 가정 미명시 — 즉 현 상태에서는 **수치적 우연(coincidence)으로 해석할 수밖에 없다**. 반면 `future_phase2_notion.md` §6-3, §9의 "다른 물리량 — 모델 구조의 생리학적 근거로만 해석"은 §2 분석에서 보듯 **세 가지 비자명한 가정 없이는 직접 수치 비교 불가**라는 사실에 부합.

## 결론 (권고)

**`future_phase2_notion.md` 입장으로 통일하라.** 즉 β_s와 Emery 21.4°는 **서로 다른 함수공간의 양**이며, 수치 일치는 §2의 세 조건을 forward simulation으로 검증하기 전에는 우연일 가능성이 높다 (특히 sub-08은 β_c 항이 ~10° 기여). `simulation_recoverability_behavior.md` Abstract의 "≈ Emery 21.4°" 문장은 다음으로 교체 권장:

> "Estimated β_s magnitudes (20–23°) fall in the same order as Emery's 21.4° B-Y phase shift, but the two quantities measure distinct constructs (cortical mapping dilation vs. hue-response peak rotation) and are quantitatively comparable only under small-angle, fixed-percept-bank, and B-Y/R-G orthogonality assumptions. Forward-simulation convergence is left for future validation."

Sources:
- [Emery 2021 PMC8058247](https://pmc.ncbi.nlm.nih.gov/articles/PMC8058247/)
- [PubMed 33636681](https://pubmed.ncbi.nlm.nih.gov/33636681/)
