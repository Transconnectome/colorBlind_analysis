# Sub-09 Protan — RDM as Primary Fitting Metric 종합 평가

> **프로젝트**: Color Vision Deficiency Neural Representation Analysis
> **날짜**: 2026-04-07
> **대상**: Future Phase 2 — Sub-09 (protan CVD) cone-shift model evaluation
> **ROI**: V1, V2
> **목표**: ΔRDM을 primary fitting criterion으로 사용할 때의 수학적 타당성, 현재 모델의 적합도, 강화/대안 전략

---

## 1. RDM이 Sub-09의 Primary Metric이 되어야 하는 근거

### 1a. Double Dissociation — LOCO vs ΔRDM

| Subject | LOCO (per-color accuracy) | ΔRDM (pairwise geometry) |
|---------|--------------------------|--------------------------|
| **sub-08** (deutan) | **V1 p=0.033*** | cosine=−0.34 (anti-corr, FAIL) |
| **sub-09** (protan) | V1 p=0.112 (NS) | **V1: 17/28 pairs structured** |

이 이중 해리의 의미:
- **LOCO**: 개별 색의 interpolation accuracy를 평가 → sub-08에서 유효
- **ΔRDM**: 색 쌍 간 거리 구조를 평가 → sub-09에서 유효
- **sub-09의 LOCO 실패 원인**: c8 magenta anti-prediction (z=−5.59)이 전체 correlation을 파괴
- **sub-09의 ΔRDM 성공 원인**: magenta의 anti-prediction 자체가 구조적 정보 (expansion signal)

### 1b. 통계적 이점

- ΔRDM: 28 pairs (= C(8,2)) → LOCO: 8 colors → **3.5× 더 많은 data points**
- ΔRDM에서 magenta expansion은 **7개 pairs**에 걸쳐 일관됨 (c5-c8: +0.665, c2-c8: +0.542, c1-c8: +0.440 등)
- LOCO에서는 1개 color의 anti-prediction이 전체를 지배

### 1c. Sub-09 ΔRDM_obs 구조

**V1** (17 positive / 11 negative):
```
Top 5 expanding (ΔRDM > 0):
  cyan-magenta     : +0.665    ← magenta-involving
  orange-magenta   : +0.542    ← magenta-involving
  red-magenta      : +0.440    ← magenta-involving
  orange-yellow    : +0.359
  red-yellow       : +0.274

Top 5 compressing (ΔRDM < 0):
  orange-green     : −0.332    ← confusion axis
  red-orange       : −0.304    ← confusion axis
  red-green        : −0.286    ← confusion axis
  orange-cyan      : −0.240
  green-cyan       : −0.181
```

**V2** (19 positive / 9 negative): V1과 유사하나 cyan-blue expansion (+0.478) 추가

**핵심 패턴**: **Magenta expansion + confusion axis compression** = 혼합 패턴

---

## 2. MD (Machado-Dilation) 모델의 실제 적합도

### 2a. MD 모델 정의

```
θ'(c) = machado_shift(θ(c), Δλ) + β · cos(θ_base(c) − θ₀)
```

- Δλ: Machado cone shift (L-M compression 담당)
- β: Dilation amplitude (localized expansion 담당)
- θ₀: Dilation center (고정 — CVD family에 의해 결정)

### 2b. Full Pipeline Grid Search 결과 (신규)

Full pipeline: `hue_shift → basis_full[idx] → C @ W_HC → pdist(correlation) → ΔRDM_sim`

| Model | θ₀ | DOF | V1 cosine | V2 cosine | V1 Spearman | Best (Δλ, β) |
|-------|-----|-----|-----------|-----------|-------------|-------------|
| **Machado-only** | — | 1 | +0.09 | −0.17 | +0.27 (NS) | (19.5, 0) |
| **MD (physiological)** | 16.4° | 2 | **+0.30** | **+0.40** | +0.05 (NS) | (0, 2°) |
| **MD (magenta center)** | 348.5° | 2 | +0.14 | +0.27 | +0.11 (NS) | (2, 26°) |
| **MD (free θ₀)** | **90°** | 3 | **+0.45** | — | +0.33 (p=0.084) | (0, 28°) |

### 2c. 핵심 발견

1. **MD (θ₀=16.4°)는 Machado 대비 상당한 개선**
   - V1: cosine +0.09 → +0.30 (3.3× 개선)
   - V2: cosine −0.17 → +0.40 (방향 역전!)
   - 하지만 **절대 적합도는 아직 약함**: 모든 Spearman p > 0.05

2. **Free θ₀=90° (S-cone 축!)가 최적**
   - V1 cosine=+0.45, Spearman p=0.084 (marginally significant)
   - **이론적 함의**: sub-09의 distortion center가 L-M axis (protan confusion)가 아닌 **S-(L+M) axis** — cortical reorganization 시사
   - Tregillus 2020: "V2v/V3v에서 L-M full compensation" → S-cone pathway 관여 가능

3. **V1-V2 parameter 불일치**
   - V1: large β (26-28°), some Δλ (0-2nm)
   - V2: small β (6°), Δλ=0
   - 단일 warp로 두 ROI 동시 설명 어려움

4. **θ₀의 중요성**
   - θ₀=348.5° (magenta 실제 위치) vs θ₀=16.4° (protan confusion endpoint): **cosine 2× 차이**
   - θ₀ 선택이 결과를 크게 좌우 → physiological constraint 필수

**비유**: 지진 진원지(θ₀)를 어디로 잡느냐에 따라 건물 기울기 예측이 완전히 달라짐. 실제 진원지가 예상과 다른 곳(S-cone axis)에 있을 가능성.

---

## 3. 수학적 기반: "Warp → RDM Recompute" 접근

### 3a. Encoding Model → RDM 연결 (Diedrichsen & Kriegeskorte 2017)

**Generative model**:
```
Y = C · W + E        (N × P = N × K · K × P + noise)
```

**Second moment matrix**:
```
G = C · Σ_W · C^T    (K × K)
```

**Predicted RDM**:
```
d²(i,j) = G_ii + G_jj − 2·G_ij
```

**우리 접근의 해석**:
- C_baseline → C_warped(Δλ, β) 로 warp
- G_warped = C_warped · Σ_W · C_warped^T
- ΔRDM_sim = RDM(G_warped) − RDM(G_baseline)
- Score = cosine(ΔRDM_sim, ΔRDM_obs)

이는 **predicted-RDM based model comparison** (Khaligh-Razavi & Kriegeskorte 2014, PLoS CB, 800+ citations)의 특수 사례:
- Model family = C(Δλ, β)로 parameterize된 encoding model
- Brain data = ΔRDM_obs
- Comparison metric = cosine similarity (→ WUC로 개선 가능)

### 3b. Cross-Validated Mahalanobis Distance (Walther et al. 2016)

**현재 문제**: Correlation distance는 biased이고 공유 활성화에 의존

**대안**: Crossnobis (cross-validated Mahalanobis):
```
d_cv(i,j) = [1/(M(M-1))] · Σ_{m≠n} (b̂_{i,m} − b̂_{j,m})^T · Σ^{-1} · (b̂_{i,n} − b̂_{j,n}) / P
```

**이점**:
- Unbiased: E[d_cv] = 0 when true distance = 0 (correlation distance는 항상 양수 bias)
- Noise-normalized: Σ^{-1} 적용으로 voxel 간 noise 차이 보정
- 음수 값 허용: 신호 없음 = 0 (해석 용이)
- **가장 reliable한 dissimilarity measure** (Walther 2016, 506 citations)

### 3c. WUC — Whitened Unbiased Cosine (Diedrichsen et al. 2020)

**현재 문제**: 28개 ΔRDM entries는 독립이 아님 (8 stimuli에서 파생)

**WUC formula**:
```
WUC(r₁, r₂) = r₁^T · V^{-1} · r₂ / √(r₁^T V^{-1} r₁ · r₂^T V^{-1} r₂)
```

V = 28×28 covariance matrix of RDM estimation errors (analytically derived)

**이점**:
- Non-independence 보정 → 신뢰성 있는 pairs에 가중치 부여
- Likelihood-ratio test에 근접하는 near-optimal model selection
- Noise assumption 위반에 robust

**한계**: K=8 (28 entries)에서는 whitening 이점이 moderate — K가 클수록 이점 증가

---

## 4. 가정 검증 (Sub-09 데이터)

### 4a. 가정 목록

| ID | 가정 | 검증 근거 | 상태 |
|----|------|-----------|------|
| **A1** | Linear encoding (Y=CW) | ridge_gcv CONFIRMED (Phase 1) | ✓ |
| **A2** | Shared W (W_HC ≈ W_CVD) | LOSO zero-shot ≈ LORO (hV4 p=0.913) | ✓ |
| **A3** | CVD changes only C, not W | V1 OK (raw deficit); V2 ⚠️ (compensation) | ⚠️ |
| **A4** | Correlation distance optimal | Crossnobis가 더 reliable (Walther 2016) | ⚠️ |
| **A5** | RDM entries independent | **위반**: 8 stimuli → 28 pairs, highly dependent | ⚠️ |
| **A6** | Equal noise across stimuli | c8 magenta z=−5.59 → noise structure 다름 | ⚠️ |

### 4b. 가장 약한 링크: A5 (Non-Independence)

8개 stimuli에서 28 pairs를 생성하면, 같은 stimulus를 공유하는 pairs는 correlated noise를 가짐.

**예**: (c1-c2)와 (c1-c3)는 c1의 noise를 공유 → RDM entries 간 covariance ≠ 0

**영향**: 현재 cosine similarity는 이 dependency를 무시 → false positive risk 증가

**해결**: WUC 적용 (V matrix로 whitening)

### 4c. A3 검증 상세

**V1에서 A3 성립 근거** (Tregillus 2020):
- V1은 L-M response **reduced** (raw deficit 유지)
- 즉, V1의 W는 HC와 유사하되 input C만 달라짐

**V2에서 A3 위반 가능성**:
- V2v/V3v는 L-M response **normal** (full compensation)
- 이는 W 자체가 변경되었을 가능성 → A3 위반
- **함의**: V2 결과는 V1보다 신뢰도 낮음

---

## 5. 강화 전략 (Feedback Loop)

### Round 1: 현재 Pipeline 개선

**5a. WUC 도입** (Priority 1)
- `rsatoolbox`의 `compare_cos` with `noise_prec` parameter 활용
- RDM comparison metric를 cosine → WUC로 변경
- 예상 효과: p-value 개선 (정확한 non-independence 보정)

**5b. Cross-validated Mahalanobis** (Priority 2)
- Correlation distance → crossnobis로 ΔRDM 자체의 quality 개선
- 필요: trial-level data (run-averaged가 아닌 per-run estimates)
- 현재 데이터에서 가능: 6 runs × 8 colors → M=6 partitions

**5c. 8! Permutation Test with WUC** (Priority 3)
- 현재 Spearman permutation → WUC permutation으로 변경
- 40,320 permutations, WUC metric → corrected p-value

### Round 2: MD 모델 정밀화

**5d. θ₀ 생리학적 재검토**
- 현재: θ₀=16.4° (protan confusion endpoint, a priori)
- 발견: θ₀=90° (S-cone axis)가 더 잘 맞음
- **탐색 필요**: S-cone pathway compensation이 protan CVD에서 문헌적으로 지지되는지

**5e. BIC Model Comparison**
```
BIC = −2·ln(L) + k·ln(n)
```
- MD (k=2) vs Machado (k=1) vs Null (k=0)
- ΔBIC > 6: strong evidence
- WUC-based likelihood approximation 가능

**5f. 2-Factor Bootstrap** (Schütt et al. 2023, eLife)
- Factor 1: HC subjects (7명 resampling → W 변동)
- Factor 2: Stimuli (8개 중 7개 subsampling → condition generalization)
- β와 θ₀의 95% CI 계산

### Round 3: 대안 모델 (MD 실패 시)

**대안 1: Free θ₀ 모델 (3-DOF)**
- 현재 결과: V1 cos=+0.45, p=0.084
- WUC 적용 시 p < 0.05 가능
- 단점: 3 DOF, θ₀의 physiological justification 필요
- Tregillus 2020의 S-cone pathway 보상 = 부분적 근거

**대안 2: Per-Color Vulnerability from ΔRDM**
- 각 color c에 대해 mean(|ΔRDM(c, *)| ) → 8-dimensional vulnerability vector
- Machado model이 아닌 data-driven vulnerability → filter 직접 설계
- 장점: model-free, LOCO 불필요
- 단점: physiological interpretation 약함

**대안 3: Feature-Reweighted RSA** (Kaniuth & Hebart 2021)
- FE-6 basis features에 per-feature weights fitting
- 6 DOF (K parameters) → data-driven but overfitting risk
- Cross-validation 필수

**대안 4: Negative Result 수용**
- Sub-09 = "cortical reorganization exceeds 1-2 DOF cone-shift model class"
- Sub-08만 Phase 2 filter 진행
- 논문에서 constructive finding: "LOCO와 ΔRDM의 double dissociation이 CVD 유형별 다른 fitting strategy를 요구함을 시사"

---

## 6. PCM 적용 가능성 평가

### 6a. PCM의 이론적 우위

**Marginal likelihood** (Diedrichsen & Yokoi 2018):
```
log p(Y|θ) = −NP/2·ln(2π) − P/2·ln|V_θ| − ½·tr(Y^T·V_θ^{-1}·Y)
```

V_θ = Z·G(θ)·Z^T + Σ_ε

Neyman-Pearson Lemma에 의해, 정규 분포 가정이 맞으면 likelihood ratio가 **최강 검정**:
```
Λ = log p(Y|θ₁) − log p(Y|θ₂)
```

### 6b. 우리 데이터에서의 한계

| 요인 | PCM | RSA (WUC) |
|------|-----|-----------|
| Data format | Trial-level 최적 | Run-averaged OK |
| K=8 conditions | 장점 (RDM entries 적어 정보 손실) | 단점 (28 entries로 충분) |
| 정규성 가정 | 필수 | Robust (rank-based 가능) |
| 구현 난이도 | `PcmPy` toolbox | `rsatoolbox` |
| Model complexity | G(θ) 직접 parameterize | ΔRDM cosine |

**판단**: PCM 적용 가능하나, 현재 데이터 구조(run-averaged)에서 RSA+WUC 대비 실질적 이점 불확실. **WUC가 more practical first step**.

---

## 7. 결론 및 실행 계획

### 7a. 즉시 실행 (Priority 순)

| Priority | Action | Expected outcome |
|----------|--------|-----------------|
| **P1** | Crossnobis로 ΔRDM_obs 재계산 | Unbiased, noise-normalized RDM |
| **P2** | WUC metric 구현 | Non-independence 보정된 model comparison |
| **P3** | MD (θ₀=16.4°) + WUC 재평가 | Corrected p-value |
| **P4** | Free θ₀ grid + WUC | θ₀=90° 유의성 확인 |
| **P5** | 8! permutation with WUC | Proper null distribution |

### 7b. 판단 기준

```
IF WUC + crossnobis에서 MD (θ₀=16.4°) p < 0.05:
    → Phase 2 filter 진행 (physiological MD model)
ELIF Free θ₀ p < 0.05:
    → θ₀ 생리학적 해석 탐색 후 결정
    → S-cone pathway 문헌 검증 필요
ELSE:
    → Sub-09 = negative result
    → Sub-08만 filter 진행
    → 논문에서 "model class limitation" discussion
```

### 7c. 핵심 메시지

1. **RDM은 sub-09의 올바른 primary metric** — LOCO가 아닌 ΔRDM에 신호가 있음
2. **MD 모델은 방향적으로 유효** — Machado 대비 V1 cos 3.3× 개선, V2 방향 역전
3. **현재 metric (correlation + cosine)이 suboptimal** — crossnobis + WUC로 개선 필요
4. **Free θ₀=90°의 발견은 이론적으로 흥미** — S-cone pathway reorganization 시사
5. **V1-V2 불일치는 근본적 한계** — 단일 warp model의 구조적 제약

---

## 참고 문헌

### 수학적 기반 (직접 인용)

1. **Diedrichsen & Kriegeskorte 2017** — "Representational models: A common framework"
   - *PLoS Computational Biology* 13(4): e1005508, 304 citations
   - Encoding model ↔ second moment G ↔ predicted RDM 수학적 연결

2. **Diedrichsen et al. 2020** — "Comparing representational geometries using WUC"
   - *Neurons, Behavior, Data Analysis, and Theory*, 42 citations
   - WUC formula, RDM entry covariance V의 analytical derivation

3. **Walther et al. 2016** — "Reliability of dissimilarity measures for MVPA"
   - *NeuroImage* 137: 188-200, 506 citations
   - Cross-validated Mahalanobis distance (crossnobis)가 가장 reliable

4. **Schütt et al. 2023** — "Statistical inference on representational geometries"
   - *eLife* 12: e82566
   - 2-factor bootstrap (subjects × conditions) for RSA inference

5. **Diedrichsen & Yokoi 2018** — "Pattern component modeling"
   - *NeuroImage* 180(A): 119-133
   - PCM marginal likelihood, Bayesian model comparison

### Model comparison 방법론

6. **Khaligh-Razavi & Kriegeskorte 2014** — "Deep supervised models explain IT"
   - *PLoS Computational Biology* 10(11): e1003915
   - Predicted RDM → brain RDM comparison methodology

7. **Cai et al. 2019** — "BRSA: Bayesian RSA"
   - *PLoS Computational Biology* 15(5): e1006299
   - Structured noise bias 해결, trial-level marginalization

8. **Kaniuth & Hebart 2021** — "Feature-reweighted RSA"
   - *NeuroImage* 231: 117890, 41 citations
   - Per-feature weight fitting for model-brain comparison

### CVD compensation (생리학적 근거)

9. **Tregillus et al. 2020** — "Color compensation in anomalous trichromats"
   - *Current Biology* 30(12): 2361-2368, 35 citations
   - V1 deficit, V2v/V3v full compensation

10. **Boehm et al. 2014** — "Compensation for red-green contrast loss"
    - *Journal of Vision* 14(13): 19, 44 citations
    - Protan gain ~3.5×
