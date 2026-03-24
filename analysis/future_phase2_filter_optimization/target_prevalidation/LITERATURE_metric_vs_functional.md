# Literature Review: Metric vs Functional Dissociation

## 핵심 질문
SRM/RDM(metric properties)과 JND(functional properties) 간 해리를 설명할 선행 연구

## Category 1: Metric Tensor vs Perceptual Discriminability (핵심!)

### ⭐ Zhou et al. 2023 - "Comparing neural models using their perceptual discriminability predictions"
**Citation**: bioRxiv 2023.11.17.567604 (2023)
**URL**: https://www.biorxiv.org/content/10.1101/2023.11.17.567604

**핵심 내용**:
- **Metric tensors characterize sensitivity to stimulus perturbations**
- Metric tensors reflect both **geometric** and **stochastic** properties of representation
- Metric tensors provide an explicit prediction of **perceptual discriminability**
- Brute force comparison would require infeasible measurements → use most-informative perturbations

**우리 연구와의 관련성**:
```
Zhou et al.:  Metric Tensor → Perceptual Discriminability
우리 연구:     SRM/RDM (geometric distance) ≠ JND (perceptual discriminability)

핵심: Metric tensor는 geometric과 stochastic 속성을 모두 포함해야 perceptual discriminability 예측 가능
      → 우리의 SRM/RDM은 geometric만 포착 (0차), JND는 고차 속성 필요
```

**인용 가능성**: ⭐⭐⭐⭐⭐ (직접 관련)
- "Metric tensors characterize sensitivity... providing an explicit prediction of perceptual discriminability" → SRM/RDM은 metric만 제공, discriminability는 별도
- 우리 발견: SRM overseparation + JND HYPO → metric ≠ discriminability

---

### Hepburn et al. 2021 - "On the relation between statistical learning and perceptual distances"
**Citation**: arXiv:2106.04427 [cs.CV] (2021)
**URL**: https://arxiv.org/abs/2106.04427

**핵심 내용**:
- Perceptual sensitivity is correlated with the **probability of an image in its close neighborhood**
- Perceptual distances do not always lead to gains over Euclidean distance
- **"Double-counting" effect**: image statistics counted once in perceptual distance, once in training

**우리 연구와의 관련성**:
```
Hepburn:   Perceptual distance ≠ always better than Euclidean
우리 연구:  SRM/RDM distance ≠ JND discriminability

핵심: Statistical properties와 perceptual sensitivity의 관계가 단순하지 않음
      → SRM은 statistical alignment만, JND는 perceptual sensitivity
```

**인용 가능성**: ⭐⭐⭐⭐
- Euclidean vs perceptual distance 차이 → metric vs functional 차이의 선례
- "Double-counting" 개념 → SRM alignment + LOCO interpolation의 이중성

---

## Category 2: Post-Receptoral Compensation in CVD (S-cone Gain 직접 관련!)

### ⭐ Emery et al. 2022 - "Gaining the system: limits to compensating color deficiencies through post-receptoral gain changes"
**Citation**: J. Opt. Soc. Am. A 39, 2172-2181 (2022)
**URL**: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10157001/

**핵심 내용**:
- Post-receptoral mechanisms can **partially** compensate for chromatic losses
- Individual neurons cannot independently adjust for chromatic input changes
- **Predicts only partial recovery** of chromatic responses
- **Increased responses to achromatic contrast** as a side effect

**우리 연구와의 관련성**:
```
Emery et al.:  Post-receptoral gain → partial recovery + achromatic increase
우리 연구:      S-cone gain (β=2.5×) → overseparation (metric) but HYPO (functional)

핵심: Gain changes는 chromatic loss를 완전히 보상 못함 (partial recovery)
      → 우리 발견: Metric overseparation ≠ functional recovery
```

**인용 가능성**: ⭐⭐⭐⭐⭐ (직접 관련)
- "Individual neurons cannot independently adjust" → S-cone gain이 selective하지 않음
- "Partial recovery" → metric overseparation이지만 functional HYPO 설명 가능
- **우리 결과의 생물학적 기전을 직접 뒷받침**

---

### Boehm et al. 2021 - "Color discrimination in anomalous trichromacy: Experiment and theory"
**Citation**: Vision Research 187, 1-12 (2021)
**URL**: https://doi.org/10.1016/j.visres.2021.05.011

**핵심 내용**:
- Anomalous trichromats show **less impairment from chromatic pedestals** than predicted
- Suggests **post-receptoral amplification** of chromatic signals
- But simple compensation models are **rejected**
- Effective contrast of pedestal is post-receptorally amplified

**우리 연구와의 관련성**:
```
Boehm:      Post-receptoral amplification exists but complex (not simple)
우리 연구:   S-cone gain → overseparation but incomplete functional recovery

핵심: Post-receptoral compensation은 존재하나 simple model로 설명 불가
      → 우리: S-cone gain은 metric을 과분리시키나 functional은 회복 못함
```

**인용 가능성**: ⭐⭐⭐⭐
- "Simple compensation models rejected" → S-cone gain의 한계 설명
- Chromatic pedestal 효과 → contrast sensitivity와 discrimination의 해리

---

## Category 3: Neural Manifold Geometry (Local vs Global)

### ⭐ Zavatone-Veth et al. 2023 - "How does training shape the Riemannian geometry of neural network representations?"
**Citation**: arXiv:2301.11375 [cs.LG] (2023)
**URL**: https://arxiv.org/abs/2301.11375

**핵심 내용**:
- Neural networks induce **Riemannian geometry** on input space
- Training **magnifies local areas along decision boundaries**
- Networks learn to **break symmetry** through feature learning
- Geometry induced by networks is **richly nonlinear**

**우리 연구와의 관련성**:
```
Zavatone-Veth: Training → local magnification at decision boundaries
우리 연구:      SRM/RDM overseparation + JND HYPO at color boundaries

핵심: Local geometry (decision boundaries)와 global geometry (distances)가 독립적
      → SRM은 global, JND는 local manifold geometry 반영
```

**인용 가능성**: ⭐⭐⭐⭐
- "Local magnification" → JND가 local boundary sensitivity 포착
- "Richly nonlinear" → 0차 metric으로 고차 functional 예측 불가

---

### Choi et al. 2016 - "Predictive coding in area V4: dynamic shape discrimination under partial occlusion"
**Citation**: arXiv:1612.05321 [q-bio.NC] (2016)
**URL**: https://arxiv.org/abs/1612.05321

**핵심 내용**:
- V4 and PFC participate in **hierarchical inference**
- Feedback signals from PFC encode **top-down predictions**
- **Initial V4 responses** driven by bottom-up (strong occlusion sensitivity)
- **Delayed V4 responses** combine feedforward + feedback (robust to occlusion)

**우리 연구와의 관련성**:
```
Choi:       V4 bottom-up (initial) ≠ V4 top-down (delayed)
우리 연구:   SRM/RDM (feedforward distance) ≠ JND (perceptual inference)

핵심: 같은 영역(V4)에서도 bottom-up metric ≠ top-down functional inference
      → SRM은 feedforward metric, JND는 inference 결과
```

**인용 가능성**: ⭐⭐⭐
- V4에서 hierarchical inference → V4 SRM/RDM도 단순 metric일 수 있음
- Predictive coding framework → LOCO의 interpolation = prediction

---

## Category 4: Color-Specific Neural Representations

### Aston et al. 2023 - "Color constancy for daylight illumination changes in anomalous trichromats"
**Citation**: J. Opt. Soc. Am. A 40, 2058-2069 (2023)
**URL**: https://pmc.ncbi.nlm.nih.gov/articles/PMC10635589/

**핵심 내용**:
- CVD discrimination thresholds for **daylight changes** do not differ from normals
- But thresholds for **atypical illuminations** do differ
- **Reduced sensitivity to daylight** weakly preserved in CVD

**우리 연구와의 관련성**:
```
Aston:      Natural illumination → preserved, atypical → impaired
우리 연구:   Natural color pairs → complex pattern (oversep + HYPO)

핵심: CVD의 preserved capabilities는 context-dependent
      → SRM overseparation이 behavioral preservation으로 이어지지 않음
```

**인용 가능성**: ⭐⭐⭐
- Context-dependent preservation → metric vs functional의 해리 예시

---

## 종합 논의 구성 제안

### 1. Introduction to Metric-Functional Dissociation
**인용**: Zhou et al. 2023, Hepburn et al. 2021

"While metric tensors capture geometric properties of neural representations (Zhou et al., 2023), they do not necessarily predict perceptual discriminability (Hepburn et al., 2021). Our findings extend this insight to color vision: SRM/RDM distances (0th order metrics) show overseparation for certain color pairs, yet JND measurements reveal discrimination difficulty (functional deficit)."

### 2. Biological Mechanisms: S-cone Gain Hypothesis
**인용**: Emery et al. 2022, Boehm et al. 2021

"Post-receptoral gain adjustments can partially compensate for chromatic losses (Emery et al., 2022; Boehm et al., 2021), but such compensation has inherent limits. Emery et al. (2022) demonstrated that individual neurons cannot independently adjust for chromatic input changes, predicting only partial recovery. Our S-cone gain hypothesis (β=2.5×) accounts for the metric overseparation, while the **partial recovery** framework explains why this does not translate to improved behavioral discriminability."

### 3. Hierarchical Geometry: 0th vs Higher Order
**인용**: Zavatone-Veth et al. 2023, Choi et al. 2016

"Neural representations exhibit hierarchical geometric structure (Zavatone-Veth et al., 2023). While pairwise distances (SRM/RDM) capture 0th order geometry, perceptual discriminability depends on higher-order properties such as local manifold curvature and decision boundary magnification. This dissociation parallels findings in V4, where initial bottom-up responses differ from delayed feedback-modulated responses during shape discrimination (Choi et al., 2016)."

### 4. Context-Dependent Functional Properties
**인용**: Aston et al. 2023, Boehm et al. 2021

"Color vision deficiencies exhibit context-dependent preservation of function (Aston et al., 2023). Similarly, our findings reveal that metric overseparation (SRM/RDM) does not guarantee functional improvement, as JND remains impaired (HYPO). This aligns with evidence that post-receptoral compensation mechanisms, while present, follow complex rules that cannot be captured by simple gain models (Boehm et al., 2021)."

---

## 핵심 논문 우선순위

### Must-Cite (직접 관련):
1. **Zhou et al. 2023** - Metric vs discriminability framework (⭐⭐⭐⭐⭐)
2. **Emery et al. 2022** - Post-receptoral gain limits (⭐⭐⭐⭐⭐)
3. **Boehm et al. 2021** - CVD compensation complexity (⭐⭐⭐⭐)

### Should-Cite (강력 지지):
4. **Zavatone-Veth et al. 2023** - Riemannian geometry training (⭐⭐⭐⭐)
5. **Hepburn et al. 2021** - Perceptual vs statistical distance (⭐⭐⭐⭐)

### Optional (보충):
6. **Choi et al. 2016** - V4 hierarchical inference (⭐⭐⭐)
7. **Aston et al. 2023** - Context-dependent CVD (⭐⭐⭐)

---

## 논문 획득 상태

### Open Access 가능:
- Zhou et al. 2023 - bioRxiv (GREEN)
- Hepburn et al. 2021 - arXiv
- Emery et al. 2022 - PMC (GREEN)
- Zavatone-Veth et al. 2023 - arXiv
- Choi et al. 2016 - arXiv

### 기관 구독 필요:
- Boehm et al. 2021 - Vision Research (HYBRID)
- Aston et al. 2023 - JOSA A (HYBRID)

---

## 다음 단계

1. **Zhou et al. 2023** 정독 - metric tensor framework 이해
2. **Emery et al. 2022** 정독 - S-cone gain 메커니즘 상세 분석
3. Discussion 초안 작성 시 위 구성 활용
4. 추가 키워드 검색:
   - "representational geometry" + "behavior"
   - "manifold learning" + "discrimination"
   - "chromatic adaptation" + "neural compensation"
