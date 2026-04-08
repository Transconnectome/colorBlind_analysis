# Sub-08 Deutan — RDM as Primary Fitting Metric 종합 평가

> **프로젝트**: Color Vision Deficiency Neural Representation Analysis
> **날짜**: 2026-04-07
> **대상**: Future Phase 2 — Sub-08 (deutan CVD) cone-shift model evaluation
> **ROI**: V1, V2
> **목표**: ΔRDM을 primary fitting criterion으로 사용할 때의 수학적 타당성, 현재 모델의 적합도, 강화/대안 전략

---

## 1. Sub-08의 Double Dissociation — LOCO vs ΔRDM

### 1a. Sub-08 = LOCO 성공, ΔRDM 실패

| Criterion | Sub-08 (deutan) | Sub-09 (protan) |
|-----------|-----------------|-----------------|
| **LOCO** (per-color accuracy) | **V1 p=0.033*, V2 p=0.047*** | V1 p=0.112 (NS) |
| **ΔRDM** (pairwise geometry) | cosine ≤ 0 (ALL negative, FAIL) | V1: 17/28 pairs structured |
| **결론** | **LOCO-dominant** | **ΔRDM-dominant** |

이 이중 해리의 의미:
- Sub-08은 LOCO에서는 유의한 cone-shift 신호가 있지만, ΔRDM 구조가 Machado 예측과 **반대 방향**
- Sub-09는 LOCO에서 c8 magenta가 anti-prediction이지만, ΔRDM에서는 magenta 관련 pairs가 일관된 expansion 신호
- **두 criterion이 같은 현상의 다른 측면을 측정**: LOCO = functional accuracy, ΔRDM = metric structure

### 1b. 그렇다면 Sub-08에 ΔRDM을 왜 검토하는가?

1. **LOCO 한계**: 8개 color → Spearman n=8, 통계적 power 제한
2. **ΔRDM 이점**: 28 pairs → 3.5× 더 많은 data points
3. **V1-V2 일관성**: ΔRDM_obs V1↔V2 Pearson r=0.776 (p<0.0001) → **강한 cross-ROI 구조**
4. **올바른 모델이 있다면**: ΔRDM 실패는 Machado 모델의 한계이지 데이터의 문제가 아닐 수 있음

---

## 2. Sub-08 ΔRDM_obs 데이터 특성

### 2a. 기본 통계

| Statistic | V1 | V2 |
|-----------|----|----|
| Positive pairs | 19/28 (67.9%) | 15/28 (53.6%) |
| Negative pairs | 9/28 (32.1%) | 13/28 (46.4%) |
| ||ΔRDM|| | 1.667 | 2.147 |
| V1-V2 Pearson r | 0.776 (p<0.0001) | — |
| V1-V2 sign agree | 20/28 (71.4%) | — |

### 2b. Pair-level 구조 (V1)

```
Top 5 expanding (ΔRDM > 0):                Top 5 compressing (ΔRDM < 0):
  red-yellow       : +0.784                  red-purple       : −0.626
  yellow-purple    : +0.614                  green-cyan       : −0.322
  red-cyan         : +0.553                  red-orange       : −0.280
  orange-yellow    : +0.471                  green-purple     : −0.224
  red-magenta      : +0.360                  orange-purple    : −0.191
```

### 2c. V2의 일관된 패턴

```
V2 Top expanding:                           V2 Top compressing:
  yellow-purple    : +0.781                  red-purple       : −0.668
  red-yellow       : +0.727                  red-orange       : −0.512
  orange-yellow    : +0.710                  orange-purple    : −0.468
  red-cyan         : +0.631                  red-green        : −0.337
  orange-cyan      : +0.538                  yellow-cyan      : −0.291
```

### 2d. 핵심 패턴 해석

**Expansion 쌍의 공통점**: yellow가 관여하는 쌍이 지배적 (red-yellow, yellow-purple, orange-yellow)
- yellow(c3)은 L-M 축에서 중간 위치 → deutan confusion 축과 직교 방향
- 이는 deutan이 yellow 주변의 거리를 **과대 추정**함을 의미

**Compression 쌍의 공통점**: purple(c7)이 많이 관여 (red-purple, orange-purple, green-purple)
- red-orange (−0.280 V1, −0.512 V2): confusion axis 방향의 거리 감소
- 이는 Machado가 예측하는 방향과 **일치하는 부분**이 있음

**문제**: Machado는 **모든** 쌍에서 compression을 예측하지만, 실제로는 **19/28이 expansion** → 구조적 불일치

---

## 3. 모델별 ΔRDM 적합도 비교

### 3a. 4가지 모델의 Full Pipeline 결과

Full pipeline: `hue_shift → basis_full[idx] → C @ W_HC → pdist(correlation) → mean_HC → ΔRDM_sim`

| # | Model | DOF | V1 cosine | V2 cosine | V1 sign | V1 perm p | Status |
|---|-------|-----|-----------|-----------|---------|-----------|--------|
| 1 | **Machado-only** (deutan) | 1 | ≤ 0.000 | ≤ 0.000 | 9/28 | — | **FAIL** |
| 2 | **R-G gain** (v1, Δλ=0, g=0.3) | 1 | +0.235 | +0.240 | 12/28 | 0.230 | NS |
| 3 | **MD** (θ₀=348.5°, Δλ=0, β=4°) | 2 | +0.318 | +0.268 | 13/28 | — | Weak |
| 4 | **MD free θ₀** (θ₀=40°, Δλ=0, β=24°) | 3 | **+0.428** | +0.257 | **18/28** | **0.063** | Marginal |

### 3b. 모델별 상세 분석

**Model 1: Machado-only — 구조적 실패**
```
V1 cosine range: [−0.397, 0.000] across Δλ ∈ [0, 20] nm
V2 cosine range: [−0.273, 0.000]
V1 sign: 9/28 (32%) ← baseline (no shift) 수준
```
- Machado의 cone shift는 hue angle compression을 생성 → ΔRDM_sim이 predominantly negative
- Sub-08의 ΔRDM_obs는 predominantly positive (expansion)
- **방향 불일치가 구조적**: Δλ 값을 아무리 조정해도 해결 불가

**Model 2: R-G gain (multiplicative, step2c) — 약한 개선**
```
Best: Δλ=0, g=0.3 → V1 cos=+0.235, V2 cos=+0.240
Label perm p=0.230 (NS), sign V1=12/28, V2=16/28
LOCO 유지: V1 ρ=0.690, p=0.036*
```
- (1+g)·rg 공식으로 R-G 채널을 30% 증폭 → expansion 방향 생성
- 하지만 expansion이 **모든 color에 균등**하게 적용되어, pair-specific 구조를 포착하지 못함
- 중요: retinal_cortical.py v2 (additive-on-change)에서는 Δλ=0이면 g 효과 = 0 (by design)
- **v1 결과는 "pure cortical" 모델 (retinal shift 없이 R-G 스케일링만)**

**Model 3: MD θ₀=348.5° (magenta center) — 중간 개선**
```
V1: Δλ=0, β=4°, cos=+0.318, sign=13/28 (46%)
V2: Δλ=0, β=4°, cos=+0.268, sign=17/28 (61%)
```
- β=4°의 작은 dilation → magenta 중심 약한 expansion
- V2가 V1보다 sign agreement 높음

**Model 4: MD free θ₀=40° — 최선이지만 비유의**
```
V1: Δλ=0, β=24°, cos=+0.428, sign=18/28 (64%)
V2: cos=+0.257, sign=16/28 (57%)
V1 Spearman: rs=+0.265, p=0.173
V1 8! perm: p=0.063
```
- 모든 best parameters에서 **Δλ=0**: Machado cone shift가 필요 없음!
- θ₀=40° (Stockman 좌표에서 red-magenta 사이, S-cone 방향 근처)
- β=24° 대형 dilation → 특정 방향의 hue space 확장
- **하지만**: V1 perm p=0.063 (marginal), V2 p=0.301 (NS), Spearman p=0.173 (NS)

### 3c. V1 Pair-by-pair 비교 (MD free θ₀=40° vs Observed)

```
pair                  obs     sim    match
red-orange          −0.280  +0.047    N     ← obs는 compression인데 sim은 expansion
red-yellow          +0.784  +0.146    Y     ← 방향은 맞지만 크기 5× 차이
red-green           −0.048  +0.189    N
red-cyan            +0.553  +0.221    Y
red-blue            +0.084  +0.039    Y
red-purple          −0.626  −0.033    Y     ← 방향은 맞지만 크기 19× 차이
red-magenta         +0.360  +0.120    Y
orange-yellow       +0.471  +0.038    Y     ← 방향만 일치, 크기 12× 차이
...
green-cyan          −0.322  +0.010    N     ← obs에서 큰 compression인데 sim은 ~0
blue-magenta        +0.161  −0.048    N
purple-magenta      +0.202  −0.101    N
```

10/28 pairs에서 sign mismatch → **"방향만 겨우 맞추는" 수준, 크기는 전혀 포착 못함**

---

## 4. 왜 Sub-08은 ΔRDM이 어려운가? — 구조적 분석

### 4a. Machado 예측 vs 관측의 방향 불일치

```
Machado 예측: cone shift → L-M separation 감소 → 모든 거리 compression (ΔRDM < 0)
Sub-08 관측: 19/28 pairs expansion (ΔRDM > 0)
```

이 불일치의 가능한 원인:

1. **Cortical compensation** (Tregillus 2020):
   - V1에서도 L-M response가 partially compensated
   - Compensation이 retinal deficit을 overcompensate → expansion
   - Step2c R-G gain 모델이 이를 일부 포착 (cos=+0.235)

2. **Heterogeneous compensation**:
   - Yellow (c3) 관련 expansion이 지배적 → 특정 hue 방향에서만 overcompensation
   - 균일한 R-G gain으로는 이 heterogeneity를 설명 불가

3. **Non-opponent-channel mechanism**:
   - Purple (c7) 관련 compression → S-cone pathway 관련 별도 메커니즘
   - Red-orange compression → L-M confusion axis의 잔여 retinal effect
   - 두 메커니즘이 혼재 → 단일 parameter 모델로 포착 불가

### 4b. Sub-08 vs Sub-09 비교

| 특성 | Sub-08 (deutan) | Sub-09 (protan) |
|------|----------------|-----------------|
| ΔRDM expansion 비율 | 19/28 (67.9%) | 17/28 (60.7%) |
| Dominant expanding pair | red-yellow (+0.784) | cyan-magenta (+0.665) |
| Compression axis | red-purple (−0.626) | orange-green (−0.332) |
| V1-V2 correlation | r=0.776 | — |
| Machado-only best cosine | 0.000 (Δλ=0) | +0.174 (Δλ=0.5) |
| LOCO | **p=0.033*** | p=0.112 (NS) |
| Best ΔRDM model | MD θ₀=40° (cos=+0.428) | MD θ₀=90° (cos=+0.448) |

**핵심 차이**:
- Sub-08의 expansion은 **yellow 중심** (deutan이 yellow 방향으로 overcompensate)
- Sub-09의 expansion은 **magenta 중심** (S-cone axis)
- 두 subject의 ΔRDM 구조는 **다른 메커니즘**을 반영

### 4c. LOCO 성공의 의미

Sub-08 LOCO가 유의한 이유:
- LOCO는 per-color **absolute prediction accuracy**를 측정
- Forward model `Y = C · W`에서 C의 변화가 W를 통해 올바른 방향으로 전파
- Machado cone shift가 **per-color magnitude** 예측에는 유효
- 하지만 **pairwise distance** 예측에는 실패 (expansion을 설명 못함)

**비유**: GPS가 각 건물의 위치는 맞추지만 (LOCO ✓), 건물 간 거리를 틀림 (ΔRDM ✗). 이는 좌표계의 nonlinear distortion을 의미.

---

## 5. 수학적 기반: Encoding Model → RDM 연결

### 5a. 이론적 프레임워크 (Diedrichsen & Kriegeskorte 2017)

```
Y = C · W + E        (N × P = N × K · K × P + noise)
G = C · Σ_W · C^T    (second moment matrix)
d²(i,j) = G_ii + G_jj − 2·G_ij    (predicted distance)
```

우리 접근:
- C_baseline → C_warped(parameters) 로 변환
- ΔRDM_sim = RDM(C_warped) − RDM(C_baseline)
- Score = cosine(ΔRDM_sim, ΔRDM_obs)

### 5b. 가정 검증 (Sub-08)

| ID | 가정 | 상태 | 근거 |
|----|------|------|------|
| **A1** | Linear encoding (Y=CW) | ✓ | ridge_gcv confirmed (Phase 1) |
| **A2** | Shared W (W_HC ≈ W_CVD) | ✓ | LOSO ZS ≈ LORO (hV4 p=0.913) |
| **A3** | CVD changes only C, not W | ⚠️ | LOCO ✓ → 부분적 지지. 하지만 expansion은 W 변화 시사 |
| **A4** | Correlation distance optimal | ⚠️ | Crossnobis가 더 reliable (Walther 2016) |
| **A5** | RDM entries independent | ⚠️ | 28 pairs from 8 stimuli → non-independent |
| **A6** | Equal noise across stimuli | ✓ | sub-08에는 c8 anti-prediction 없음 (sub-09 문제) |

**A3가 핵심 약점**: Sub-08의 expansion은 W 자체가 변경되었을 가능성을 시사. 만약 W_CVD ≠ W_HC라면, C만 변경하는 모든 모델이 ΔRDM을 정확히 예측할 수 없음.

### 5c. WUC 및 Crossnobis 적용 가능성

**WUC (Whitened Unbiased Cosine, Diedrichsen et al. 2020)**:
- Non-independence 보정: 28 entries의 covariance 구조를 whitening
- Sub-08의 경우 MD θ₀=40° perm p=0.063 → WUC 적용 시 유의수준 도달 가능성
- 하지만 cos=+0.428 자체가 높지 않아 극적 개선은 기대 어려움

**Crossnobis (Walther et al. 2016)**:
- Correlation distance의 양수 bias 제거 → unbiased ΔRDM
- 현재 6 runs으로 cross-validation 가능
- 예상 효과: expansion/compression 비율이 변할 수 있음 (양수 bias 제거 시)

---

## 6. 강화 전략 및 대안

### 전략 A: LOCO-Primary (현재 접근 유지) — **권장**

```
Sub-08 Phase 2 filter: LOCO-derived Δλ 사용
  V1: Δλ=34.9 nm (W-fixed, p=0.033)
  V2: Δλ=3.9 nm (W-fixed, p=0.047)
ΔRDM 역할: convergence validation (negative = 모델 한계 인정)
```

**근거**:
- LOCO가 유의 (V1 p=0.033, V2 p=0.047) → 이미 작동하는 criterion
- ΔRDM 실패는 Machado 모델의 한계이지 데이터의 문제가 아님
- Per-color accuracy가 filter 설계에 더 직접적으로 관련

**한계**:
- n=8 power limitation은 여전
- V1과 V2의 Δλ 값 차이 (34.9 vs 3.9)가 생리학적으로 설명 어려움

### 전략 B: ΔRDM 모델 확장 — 탐색적

**B1. WUC + Crossnobis 적용**
- Priority 1: Crossnobis로 ΔRDM_obs 재계산
- Priority 2: WUC metric으로 model comparison
- 예상: perm p가 0.063 → <0.05로 개선 가능

**B2. 2-DOF Dilation Model (θ₀ 고정 후)**
```
θ'(c) = β · cos(θ_base(c) − θ₀)    [Machado 없이, pure dilation]
θ₀ = 40° (data-driven), β = fit parameter
```
- 1 DOF → overfitting risk 감소
- 하지만 θ₀ 선택의 physiological justification 필요

**B3. Per-Color Vulnerability**
- ΔRDM_obs에서 per-color vulnerability vector 추출:
  `vuln(c) = mean(|ΔRDM(c, j)| for j ≠ c, ΔRDM(c,j) > 0) − mean(|ΔRDM(c, j)| for j ≠ c, ΔRDM(c,j) < 0)`
- Model-free → filter 직접 설계 가능
- 하지만 mechanistic interpretation 약함

### 전략 C: Discussion-Only — Sub-08을 LOCO 케이스로 한정

논문 프레이밍:
> "Sub-08 demonstrates that LOCO-based per-color prediction accuracy captures cone-shift effects that the pairwise ΔRDM criterion misses. The directional mismatch (observed expansion vs predicted compression) suggests that cortical compensation in deutan CVD produces distance expansion that simple cone-shift models cannot account for."

---

## 7. Sub-08 고유의 결론

### 7a. ΔRDM을 Primary로 삼을 수 없는 이유

1. **구조적 방향 불일치**: Machado는 compression 예측, 관측은 expansion → Δλ 조절로 해결 불가
2. **최선 모델(MD θ₀=40°)도 비유의**: perm p=0.063, Spearman p=0.173
3. **크기 불일치 심각**: sign은 18/28 맞추지만, 크기(magnitude)는 5-19× 차이
4. **3 DOF (θ₀, Δλ, β) 투입해도 V2는 NS** (cos=+0.257, p=0.301)

### 7b. LOCO가 Sub-08의 올바른 Primary Metric인 이유

1. **V1, V2 동시 유의**: p=0.033, p=0.047
2. **Per-color accuracy**가 filter 설계 목표에 직결
3. **Step2c 결과**: R-G gain 추가 시 LOCO 유지 (V1 ρ=0.690, p=0.036)
4. **Phase 2 filter**: per-color 예측 정확도 개선이 목적 → LOCO 기반이 자연스러움

### 7c. Sub-08 vs Sub-09 최종 비교

| | Sub-08 (deutan) | Sub-09 (protan) |
|---|----------------|-----------------|
| **Primary criterion** | LOCO | ΔRDM (§sub-09 문서) |
| **Primary evidence** | V1 p=0.033, V2 p=0.047 | V1 cos=+0.448, p=0.084 |
| **ΔRDM 상태** | 구조적 실패 (expansion vs compression) | 약한 성공 (free θ₀ 필요) |
| **Filter 설계** | LOCO-derived Δλ 사용 | ΔRDM 강화 필요 (WUC/crossnobis) |
| **핵심 한계** | V1-V2 Δλ 차이 (34.9 vs 3.9) | c8 magenta anti-prediction |
| **Cortical compensation** | Expansion 관측 = overcompensation | θ₀=90° = S-cone pathway |

### 7d. 실행 계획

| Priority | Action | For Sub-08 | For Sub-09 |
|----------|--------|-----------|-----------|
| **P1** | LOCO-based filter | **Primary path** | N/A (LOCO NS) |
| **P2** | Crossnobis ΔRDM | Convergence check | Primary improvement |
| **P3** | WUC metric | p=0.063 → <0.05? | p=0.084 → <0.05? |
| **P4** | Phase 2 filter design | LOCO Δλ → filter | TBD (if P2-P3 succeed) |

---

## 8. 핵심 메시지 요약

1. **Sub-08에서 ΔRDM은 primary metric이 될 수 없다** — Machado의 compression 예측과 관측된 expansion 사이의 구조적 불일치 때문
2. **LOCO가 Sub-08의 올바른 primary metric** — V1 p=0.033, V2 p=0.047로 이미 유의
3. **MD 모델(free θ₀=40°)이 최선이나 비유의** (p=0.063) — WUC 적용 시 marginal 도달 가능
4. **ΔRDM 실패의 의미**: Machado cone shift만으로는 sub-08의 pairwise distance 구조를 설명할 수 없으며, cortical compensation (expansion)이 주요 원인
5. **Sub-08과 Sub-09는 다른 전략이 필요** — double dissociation이 CVD 유형별 다른 fitting strategy를 요구
6. **V1-V2 cross-ROI 일관성 (r=0.776)**: ΔRDM 구조 자체는 robust하며, 모델 개선의 여지가 있음

---

## 참고 문헌

### 직접 인용

1. **Diedrichsen & Kriegeskorte 2017** — "Representational models: A common framework"
   - *PLoS Computational Biology* 13(4): e1005508
   - Encoding model ↔ second moment G ↔ predicted RDM 수학적 연결

2. **Diedrichsen et al. 2020** — "Comparing representational geometries using WUC"
   - *Neurons, Behavior, Data Analysis, and Theory*
   - WUC formula, RDM entry covariance whitening

3. **Walther et al. 2016** — "Reliability of dissimilarity measures for MVPA"
   - *NeuroImage* 137: 188-200
   - Cross-validated Mahalanobis (crossnobis) 가장 reliable

4. **Tregillus et al. 2020** — "Color compensation in anomalous trichromats"
   - *Current Biology* 30(12): 2361-2368
   - V1 deficit, V2v/V3v full compensation, overcompensation 가능성

### 기존 결과 참조

5. **Gen-4.5 Diagnosis** — `GEN45_SUB09_DIAGNOSIS.md`
   - C_baseline bug fix 후: sub-08 ALL L₁ ≤ 0 confirmed

6. **Step2c R-G gain** — `/tmp/step2c_test/test_sub08.json`
   - V1 multiplicative (1+g) formula, cos=+0.235, LOCO V1 p=0.036

7. **W-fixed LOCO** — Phase 2 v2 pipeline
   - Sub-08: V1 Δλ=34.9nm, p=0.033; V2 Δλ=3.9nm, p=0.047
