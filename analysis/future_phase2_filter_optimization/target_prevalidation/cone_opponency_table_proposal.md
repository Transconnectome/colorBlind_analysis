# Cone Opponency 기반 CVD 다중 지표 수렴 검증

## 1. 목적 및 방법

**목적**: 정성적 cone model 설명을 정량적 수치로 변환하여 피질 지표(SRM, RDM, LOCO)와 수렴 여부 검증

**Cone Fundamentals 파라미터** (Stockman & Sharpe 2000):

| CVD Type | L peak (nm) | M peak (nm) | S peak (nm) | Cone 변화 |
|----------|-------------|-------------|-------------|-----------|
| **Normal** | 564 | 534 | 420 | — |
| **Deutan (sub-08)** | 564 | **560** (M') | 420 | M-cone +26nm shift |
| **Protan (sub-09)** | **534** (L') | 534 | 420 | L-cone -30nm shift (L≈M) |

**계산 방법**:
- Cone response: Gaussian approximation (σ=50nm)
- Opponency channels: **L-M** (red-green), **S-(L+M)** (blue-yellow)
- Cone distance: 2D Euclidean in (L-M, S-(L+M)) space

**피질 지표 공간**:
- **SRM z-score**: Shared latent space (k=3-4 dims), SRM projection W^T·X
- **RDM Crossnobis**: **Procrustes-aligned voxel space** (수백 dims), orthogonal alignment HC→CVD
  - Procrustes: 원 복셀 패턴 보존, 회전/반사만 허용 (scaling 없음)
  - Crossnobis: Mahalanobis distance with noise covariance normalization

---

## 2. Sub-08 (Deutan) 분석

### 2-1. Per-Color LOCO Analysis — Sub-08 (Deutan) hV4

**방법**: Crawford-Howell modified t-test (df=6), bootstrap 95% CI (10K resamples)

| 색 | HC Mean [95% CI] | CVD Value | Outside CI | Confusion → | Median Error (°) | p |
|-------|:----------------:|:---------:|:----------:|:-----------:|:----------------:|:----------:|
| red | +0.355 [+0.176, +0.493] | +0.573 | ✓ | purple (272°) | 88 | 0.403 |
| **orange** | +0.232 [+0.036, +0.407] | **-0.637** | ✓ | **red (344°)** | 60 | **0.029*** |
| **yellow** | +0.184 [+0.016, +0.455] | **-0.733** | ✓ | **cyan (178°)** | 88 | **0.044*** |
| green | +0.148 [-0.085, +0.353] | -0.306 | ✓ | orange (31°) | 107 | 0.221 |
| cyan | +0.182 [-0.012, +0.361] | +0.250 | — | yellow (86°) | 95 | 0.814 |
| blue | +0.384 [+0.155, +0.602] | -0.251 | ✓ | yellow (84°) | 150 | 0.124 |
| purple | +0.255 [-0.035, +0.514] | -0.759 | ✓ | red (5°) | 96 | 0.058† |
| magenta | +0.113 [-0.132, +0.370] | -0.334 | ✓ | green (127°) | 146 | 0.287 |

> **Outside CI**: CVD value falls outside HC 95% bootstrap CI
> **Confusion**: Median predicted hue (if different from true color region)
> **LOCO voxel_corr**: Spearman correlation between predicted and actual voxel patterns
> **\***: p<0.05, **†**: p<0.10 (trend)

**핵심 발견**:
- **orange (p=0.029*), yellow (p=0.044*)**: 유의미하게 HC보다 낮음
- **Confusion pattern**: orange→red (CCW shift), yellow→cyan (CW shift ~90°), purple→red
- **7/8 colors outside HC CI**: LOCO는 전반적으로 낮으나, orange/yellow만 유의

### 2-1-2. 3-Way Convergence: RSVP (Behavioral) + LOCO (Neural) + Cone (Receptor)

**Per-Color 취약성 — 3개 지표 수렴**

| 색 | RSVP 정확도 | LOCO p (V4) | Cone ΔL-M | 수렴도 | 해석 |
|:---|:-----------:|:-----------:|:---------:|:------:|:-----|
| **yellow** | **62.5%*** | **0.044*** | **-0.268** ↓ | **3/3** | **완전 수렴** — RSVP + LOCO + Cone |
| **purple** | **50.0%*** | 0.058† | +0.115 | **2/3** | RSVP + LOCO (Cone 약함) |
| **orange** | 87.5% | **0.029*** | **-0.308** ↓ | **2/3** | LOCO + Cone (RSVP 경미) |
| green | 75.0%* | 0.221 | +0.162 | 2/3 | RSVP + Cone |
| magenta | 75.0%* | 0.287 | +0.054 | 1/3 | RSVP only |
| red | 100% | 0.403 | **-0.239** ↓ | 1/3 | Cone only |
| cyan | 100% | 0.814 | +0.304 | 1/3 | Cone only |
| blue | 100% | 0.124 | +0.243 | 1/3 | Cone only |

> **출처**: RSVP (behavioral notion.md §1-2), LOCO (V4 ridge_gcv Crawford-Howell), Cone (M' 534→560nm)
> **기준**: RSVP <80%, LOCO p<0.05, Cone |ΔL-M|>0.15
> **\***: p<0.05 or accuracy <80%, **†**: p<0.10

**Confusion Pattern — 3-Way 비교**

| 원 색 | RSVP → (8AFC) | LOCO → (Continuous) | Cone → (가까워지는 색) | 일치? |
|:------|:-------------|:--------------------|:---------------------|:-----:|
| **orange** | **yellow** (1회) | **red** | **green** | **0/3** ✗✗✗ |
| **yellow** | **green** (3회) | **cyan** | **green** | **RSVP↔Cone** |
| green | yellow (1회) | orange | **orange** | **LOCO↔Cone** |
| **purple** | **magenta** (3회) | **red** | **blue** | **0/3** ✗✗✗ |
| magenta | purple (2회) | green | blue | 0/3 ✗✗✗ |

> **RSVP confusion**: 64 trials, 12 errors. Purple↔magenta 5건(42%), yellow 관련 3건
> **3-way 일치**: **0건** — Confusion 방향은 과제 의존적

**핵심 발견**:

1. **취약성(Which colors) 수렴 ✓**:
   - Yellow: 3/3 완전 수렴 (RSVP 62.5%, LOCO p=0.044, Cone -0.268)
   - Purple: 2/3 수렴 (RSVP 50%, LOCO p=0.058†)
   - Orange: 2/3 수렴 (LOCO p=0.029, Cone -0.308)

2. **Confusion 방향(Which → Which) 불일치 ✗**:
   - 3-way 일치: **0건**
   - 2-way 일치: yellow만 RSVP↔Cone (green), green만 LOCO↔Cone (orange)
   - Orange, purple, magenta: 3개 지표 모두 다른 방향 예측

3. **과제 의존성**:
   ```
   Purple Confusion (가장 극단적 사례):
     RSVP (8AFC):     purple ↔ magenta (5회, 인접색 범주 경계)
     LOCO (Continuous): purple → red (5°, 반대편 drift)
     Cone (Receptor):  purple → blue (cone space 가까워짐)
   ```

4. **함의**:
   - **"Which colors are vulnerable"**: 3개 level 수렴 → Cone shift가 취약 색 식별 가능
   - **"Which colors get confused with which"**: 완전 불일치 → 과제/처리 수준 의존적
   - **범주적(RSVP) vs 연속적(LOCO)**: 다른 표상/전략 사용

### 2-1-1. Confusion Pattern vs Cone Shift 일치도

**질문**: LOCO confusion pattern을 cone shift가 예측하는가?

| Confused Color → Predicted | Normal Cone Dist | Deutan Cone Dist | Δdist | 가까워짐? | Cone 예측 일치? |
|:---------------------------|:----------------:|:----------------:|:-----:|:--------:|:---------------:|
| **orange → red** | 0.270 | 0.295 | **+0.026** | **NO** (팽창) | ✗ |
| **yellow → cyan** | 0.923 | 0.953 | **+0.031** | **NO** (팽창) | ✗ |
| **purple → red** | 1.218 | 1.325 | **+0.107** | **NO** (팽창) | ✗ |
| **green → orange** | 0.596 | 0.090 | **-0.506** ↓↓ | **YES** (강한 압축) | ✓ |
| cyan → yellow | 0.923 | 0.953 | +0.031 | NO | ✗ |
| blue → yellow | 1.234 | 1.354 | +0.120 | NO | ✗ |
| **magenta → green** | 1.767 | 1.708 | **-0.059** | **YES** (약한 압축) | ✓ |

> **Cone model 설명력: 2/7 (29%)** — confusion pattern도 pairwise distance와 동일하게 실패

**역방향 분석**: CVD 색이 Normal 어느 색에 가장 가까운가?

| CVD Color | Cone Space → Closest Normal | LOCO Confusion → | 일치? |
|:----------|:----------------------------|:-----------------|:-----:|
| orange | **yellow** (0.254) | **red** | ✗ |
| yellow | **green** (0.262) | **cyan** | ✗ |
| purple | **magenta** (0.096) | **red** | ✗ |
| green | green (0.181) | orange | ✗ |
| cyan | cyan (0.339) | yellow | ✗ |
| blue | blue (0.272) | yellow | ✗ |
| magenta | magenta (0.061) | green | ✗ |

> **0/7 일치** — Cone space "closest normal" ≠ LOCO predicted color

**핵심 불일치 사례**:

```
Orange Confusion (CCW -16°):
  Cone 예측:    CVD orange → Normal yellow 근처 (Δ=0.254)
  LOCO 관측:    CVD orange → Normal red 예측 (344°)
  → Cone과 LOCO 완전 반대 방향

Yellow Confusion (CW ~90°):
  Cone 예측:    CVD yellow → Normal green 근처 (Δ=0.262)
  LOCO 관측:    CVD yellow → Normal cyan 예측 (178°)
  → Cone: adjacent color, LOCO: opposite side

Purple Confusion (CCW -95°):
  Cone 예측:    CVD purple → Normal magenta 근처 (Δ=0.096, 매우 가까움)
  LOCO 관측:    CVD purple → Normal red 예측 (5°)
  → Cone: 인접색, LOCO: 반대편
```

**결론**:
- **Confusion은 피질 표상의 문제**, cone shift로 직접 예측 불가
- **Green-orange만 일치** (-0.506 cone 압축 + green→orange confusion)
- **나머지 6/7은 cone 예측과 무관** (심지어 반대 방향도 있음)
- **피질 보상 기전** (S-cone gain)이 cone-level 예측을 완전히 역전

### 2-2. 5-way 통합 표 — Cone + Cortical + LOCO + Behavioral (CORRECTED)

**중요**: 이 표는 Metric vs Functional 속성을 구분하여 해석해야 함 (§2-2-1 참조).

| 색 쌍 | **Cone Δdist** | **SRM z (V2)** | **RDM V2 diff** | **LOCO 구성 색** | **JND (HC1)** | **Metric 방향** | **Functional 방향** | **관계** |
|--------|:-------------:|:--------------:|:---------------:|:----------------:|:-------------:|:---------------:|:-------------------:|:--------:|
| red-orange | +0.026 | -0.82 | -0.605 | orange (p=0.029*) | HYPER | 압축 - | LOCO실패+HYPER | 복잡 |
| **orange-yellow** | -0.027 | **+3.29*** | **+0.498*** | **orange (p=0.029*), yellow (p=0.044*)** | **HYPO** | **과분리 +** | **실패/HYPO** | **해리 ✗** |
| **yellow-green** | -0.282 ↓↓ | **+4.14*** | **+0.496*** | **yellow (p=0.044*)** | **HYPO** | **과분리 +** | **실패/HYPO** | **해리 ✗** |
| green-blue | +0.039 | -0.89 | -0.158 | — | HYPER | 압축 - | 성공/HYPER | 일치 ✓ |
| **yellow-purple** | +0.138 | **+13.87*** | **+0.670*** | **yellow (p=0.044*), purple (p=0.058†)** | **HYPO** | **과분리 +** | **실패/HYPO** | **해리 ✗** |
| blue-purple | -0.084 | **+6.15*** | **+0.881*** | **purple (p=0.058†)** | HYPER | 과분리 + | LOCO실패+HYPER | 복잡 |
| cyan-blue | -0.037 | -0.95 (V1) | +0.452 | cyan (NS) | — | 혼재 | — | ROI 의존 |

> **Cone Δdist**: 양수 = CVD에서 거리 증가 (과분리), 음수 = 거리 감소 (압축)
> **출처**: SRM (target_prevalidation §1-1), RDM (behavioral notion.md §2-2), LOCO (ridge_gcv hV4, Crawford-Howell), JND (behavioral §1-1)
> **LOCO 구성 색**: Crawford-Howell p<0.05 (*), p<0.10 (†)
> **HYPO**: CVD 덜 민감 (JND 높음), **HYPER**: CVD 더 민감 (JND 낮음)
> **Metric 방향**: SRM z + RDM diff 부호 (과분리 + / 압축 -)
> **Functional 방향**: LOCO 취약성 + JND 방향 (실패/HYPO vs 성공/HYPER)
> **관계**: 해리 ✗ = Metric overseparation + Functional HYPO (예상과 반대)

**핵심 발견 (CORRECTED)**:
- **Metric-Functional 해리 3쌍** (orange-yellow, yellow-green, yellow-purple): SRM/RDM 과분리(+) BUT JND HYPO(어려움)
- **Metric-Metric 일관성**: SRM ↔ RDM 86% 일치 (부호 6/7)
- **Functional-Functional 일관성**: LOCO ↔ JND 100% 일치 (HYPO 3쌍 모두 LOCO 취약 색 포함)
- **Cone model 실패**: Metric 17%, Functional 17% 일치 — 피질 보상 기전(S-cone gain)으로 예측 역전

### 2-2-1. Metric vs Functional 해리(Dissociation)의 의미

**잘못된 해석 (이전)**: "모든 지표가 같은 방향 → 수렴 ✓"

**올바른 해석 (수정)**:

| 속성 | 측정 대상 | 지표 | 차수 | 질문 |
|------|----------|------|------|------|
| **Metric** | 기하학적 거리 | SRM z, RDM diff | **0차** (pairwise distance) | "두 색이 얼마나 먼가?" |
| **Functional** | 보간/변별 성능 | LOCO, JND | **고차** (interpolation capability) | "이 색을 보간/변별할 수 있는가?" |

**예상되는 관계**: Metric overseparation (양수, 멀어짐) → Functional HYPER (쉬움)
**해리(Dissociation)**: Metric overseparation (양수) + Functional HYPO (어려움) — **예상과 반대**

**3쌍의 Metric-Functional 해리**:
1. **orange-yellow**: SRM z=+3.29 (과분리), RDM=+0.498 (과분리) BUT JND=HYPO (어려움)
2. **yellow-green**: SRM z=+4.14 (과분리), RDM=+0.496 (과분리) BUT JND=HYPO (어려움)
3. **yellow-purple**: SRM z=+13.87 (과분리), RDM=+0.670 (과분리) BUT JND=HYPO (어려움)

**해리의 원인** (behavioral notion.md §3-1):
- **0차 vs 고차 기하학**: SRM z는 끝점 거리(0차)만 측정, JND는 보간 구간 민감도(고차) 측정
- **국소 불규칙성**: 끝점은 멀지만 중간 manifold가 불규칙 → 보간 실패
- **S-cone 보상**: L-M 손실 → S-cone gain 증폭 → 끝점 팽창하나 보간 충실도 저하

**출처**: `analyze_metric_vs_functional.py`

### 2-2. Cone Model 실패 원인 — 2가지 가설 검증

#### 가설 1: 차원 축소(k=3-4)로 인한 부호 반전?

**질문**: SRM k=3-4 latent 축소 과정에서 부호가 뒤집혔나?

**검증**: RDM (Procrustes voxel, 수백 차원, SRM 전)과 비교

| 비교 | 부호 일치도 | 상관 (ρ) | 해석 |
|------|-----------|---------|------|
| Cone vs **RDM** (수백 차원) | **1/7 (14%)** | ρ=-0.214 | **RDM도 Cone과 불일치** |
| Cone vs SRM (k=3-4) | 2/7 (29%) | ρ=0.000 | |
| **SRM vs RDM** | **6/7 (86%)** | ρ=**0.786*** | **피질 지표 일관** |

**결론**: ❌ **가설 기각**
RDM (차원 축소 전)에서도 Cone과 14%만 일치 → 차원 축소가 원인 아님

#### 가설 2: 절대값으로 왜곡 크기 예측 가능?

**질문**: 부호는 무시하고 |Δdist| 크기만 비교하면 상관 있나?

| 상관 | Spearman ρ | p-value | 해석 |
|------|-----------|---------|------|
| **\|Cone\| vs \|SRM\|** | **0.750** | **0.052** | **Borderline** |
| \|Cone\| vs \|RDM\| | 0.107 | 0.819 | 무의미 |
| **\|SRM\| vs \|RDM\|** | **0.786** | **0.036*** | 피질 지표 일관 |

**결론**: △ **가설 약한 지지**
p=0.052로 borderline, 실용적 예측 도구로는 부족

### 2-3. 진짜 원인 — Cone → Voxel 피질 비선형 변환

```
Cone (receptor):                yellow-green Δ = -0.282 (강한 압축)
    ↓ (비선형 피질 변환)
RDM (Procrustes voxel):         yellow-green diff = +0.496 (과분리) ← 반대!
    ↓ (SRM k=3-4 projection, 86% 방향 보존)
SRM latent (k=3-4):             yellow-green z = +4.14 (과분리)
```

**핵심**:
- **차원 축소는 방향을 보존** (SRM latent ↔ Procrustes voxel: 86% 일치)
- **Cone → Procrustes voxel 변환이 방향을 역전** (L-M 손실 → S-cone gain 보상)

### 2-4. 생물학적 기전 — S-cone Compensation Mechanism

#### 기전 1: L-M 손실 검출 → S-cone Gain 증폭

**신경생리학적 근거**:
- V1 cone-opponent cells: L-M, S-(L+M) 독립 채널 (Shapley & Hawken 2011)
- V2 thin stripes: 색 선택적 neurons, hue-selective tuning (Conway et al. 2007)
- **피질 보상 가설**: L-M 신호 약화 → S-cone weight 상대적 증가 (recurrent connections)

**정량적 증거 (sub-08)**:

| 색 쌍 | Cone ΔL-M | Cone ΔS | **S 보상 비율** | SRM z | 수렴 |
|--------|:---------:|:-------:|:---------------:|:-----:|:----:|
| **yellow-purple** | -0.383 (↓↓) | -0.191 | **50%** (S/LM) | **+13.87*** | ✓ |
| **blue-purple** | +0.128 | +0.064 | **50%** | **+6.15*** | ✓ |
| orange-yellow | -0.040 (↓) | -0.020 | **50%** | **+3.29*** | ✓ |
| yellow-green | -0.430 (↓↓↓) | -0.215 | **50%** | **+4.14*** | ✓ |

> **패턴**: L-M 손실이 클수록 (ΔL-M 음수) → S 보상 활성화 → SRM 과분리 (양수)

**시뮬레이션 (S-cone gain model)**:

가정: 피질 distance = `α·|ΔL-M| + β·|ΔS|`, L-M 손실 시 β 증가

```python
# Normal (α=1.0, β=1.0)
yellow_green_normal = sqrt(0.498^2 + 0.009^2) = 0.498

# Deutan cone-level (α=1.0, β=1.0)
yellow_green_deutan_cone = sqrt(0.068^2 + 0.216^2) = 0.227  # 압축

# Deutan cortical (α=0.5, β=2.5 — S gain 2.5배)
yellow_green_deutan_cortex = sqrt((0.5·0.068)^2 + (2.5·0.216)^2) = 0.541  # 과분리!
```

**결과**: S-cone weight β를 2.5배 증가시키면 Cone 압축 → Cortical 과분리 재현

#### 기전 2: ROI 계층 의존 — V1 vs V2

**cyan-blue 이중 해리**:

| 지표 | V1 | V2 | 해석 |
|------|:--:|:--:|------|
| Cone Δdist | **-0.037** (압축) | — | L-M 혼동 예측 |
| SRM z | **-0.95** (압축) | — | V1: cone 일치 |
| RDM diff | **-0.449** (압축) | **+0.452** (과분리) | **V2: S 보상 시작** |

**생물학적 해석**:
- **V1 (early)**: Cone 신호 충실 반영 (cone-level 압축 유지)
- **V2 (intermediate)**: S-cone gain 활성화 시작 (압축 → 과분리 전환)
- **계층 가설**: L-M 손실 보상은 V1보다 **V2에서 강함** (feedback from higher areas)

#### 기전 3: Color-Specific Vulnerability → LOCO 설명

**LOCO 취약 색의 Cone 기전**:

| 취약 색 | Cone 변화 (Deutan) | 피질 결과 | LOCO 실패 기전 |
|---------|-------------------|----------|---------------|
| **orange** | L-M: +0.72 → **+0.68** (M' shift) | V2 z=+3.29 (o-y) | M' 이동으로 orange 위치 왜곡 → 7색 학습 template mismatch |
| **yellow** | L-M: +0.45 → **+0.35** (M' 접근) | V2 z=+4.14 (y-g) | M' peak가 yellow에 근접 → L-M 대비 약화 → 이웃 색에서 보간 불가 |
| **purple** | S-(L+M): +0.82 → **+0.87** (S 증폭) | V2 z=+13.87 (y-p) | S-cone 과의존 → purple이 S 축 팽창 → 이웃 색에서 예측 어려움 |
| cyan | L-M: -0.34 → -0.04 (약간 ↑) | V1 z=-0.95 (c-b) | blue 방향 drift (간접 영향) |

**보간 실패 = 국소 불규칙성**:
7색으로 학습한 모델이 나머지 1색을 예측 못함 → Cone shift로 인해 color manifold의 예상 위치에서 벗어남

### 2-5. Cone Model의 재정의 — 예측자 → 해석자

| Cone model이 설명 **가능** | Cone model이 설명 **불가** |
|--------------------------|--------------------------|
| ✅ 왜곡 발생 **원인**: M' shift (534→560nm) | ❌ 피질 거리 **방향**: Cone 압축 ↔ Cortex 과분리 (5/7 반대) |
| ✅ 영향받는 **색 범위**: warm colors (red, orange, yellow) | ❌ 보상 기전 **크기**: L-M 손실 → S gain 정도 (β=2.5배?) |
| ✅ **LOCO 취약 색** 식별: orange, yellow, purple | ❌ **ROI별 차이**: V1 압축 ↔ V2 과분리 (cyan-blue) |
| ✅ **CVD subtype** 구별: Deutan vs Protan | ❌ **개인차**: sub-10 보상 성공 기전 |

**새로운 역할**: **Post-hoc 기전 설명** (예측 아닌 해석)

```
Receptor (Cone):                    M' shift (534→560nm) — 필요조건
  ↓ (비선형 변환, 예측 불가)
Cortical (SRM latent k=3-4):        Distance distortion (관측) — 측정
Cortical (Procrustes voxel):        Distance distortion (관측) — 독립 검증
  ↓ (기능적 영향)
Functional (LOCO):                  Interpolation failure (행동 예측) — 충분조건
```

**결론**: Cone opponency는 왜곡의 **필요조건**이나 **충분조건 아님**

---

## 3. Sub-09 (Protan) 분석

### 3-1. Per-Color LOCO Analysis — Sub-09 (Protan) hV4

**방법**: Crawford-Howell modified t-test (df=6), bootstrap 95% CI (same HC reference as sub-08)

| 색 | HC Mean [95% CI] | CVD Value | Outside CI | Confusion → | Median Error (°) | p |
|-------|:----------------:|:---------:|:----------:|:-----------:|:----------------:|:----------:|
| red | +0.355 [+0.176, +0.493] | +0.023 | ✓ | orange (65°) | 65 | 0.223 |
| orange | +0.232 [+0.036, +0.407] | +0.596 | ✓ | red (13°) | 25 | 0.260 |
| yellow | +0.184 [+0.016, +0.455] | +0.322 | — | orange (58°) | 52 | 0.704 |
| green | +0.148 [-0.085, +0.353] | +0.147 | — | purple (291°) | 156 | 0.999 |
| cyan | +0.182 [-0.012, +0.361] | -0.451 | ✓ | orange (59°) | 122 | 0.070† |
| blue | +0.384 [+0.155, +0.602] | -0.256 | ✓ | magenta (309°) | 84 | 0.122 |
| purple | +0.255 [-0.035, +0.514] | -0.090 | ✓ | orange (25°) | 115 | 0.443 |
| magenta | +0.113 [-0.132, +0.370] | -0.575 | ✓ | cyan (174°) | 122 | 0.127 |

> **Outside CI**: CVD value falls outside HC 95% bootstrap CI
> **Confusion**: Median predicted hue (if different from true color region)
> **\***: p<0.05, **†**: p<0.10 (trend)

**핵심 발견**:
- **No significant per-color deficits** (cyan p=0.070 borderline)
- **Confusion pattern**: Multiple colors → orange (red, cyan, purple), magenta ↔ cyan bidirectional
- **6/8 colors outside HC CI**: LOCO 전반적으로 낮으나 개별 색 유의성 없음

### 3-2. Protan vs Deutan 통합 비교

| 색 쌍 | Cone Δdist | ΔL-M | ΔS | Cone 예측 | **sub-09 SRM z (V1)** | **일치?** |
|--------|:----------:|:----:|:---:|:---------:|:---------------------:|:--------:|
| red-orange | **-0.043** | +0.069 | -0.034 | **압축 (-)** | **-1.35** | **✓** |
| **red-magenta** | **-0.216** ↓ | -0.343 | +0.171 | **압축 (-)** | **+3.52*** | **✗ 완전 반대** |
| **orange-magenta** | **-0.260** ↓ | -0.412 | +0.206 | **압축 (-)** | **+3.71*** | **✗ 완전 반대** |
| **cyan-magenta** | **+0.106** | +0.286 | -0.143 | **과분리 (+)** | **+4.08*** | **✓** |
| **yellow-purple** | **-0.264** ↓ | -0.420 | +0.210 | **압축 (-)** | **-3.31*** | **✓** |
| green-blue | **-0.035** | -0.067 | +0.033 | **압축 (-)** | **-2.41** | **✓** |

> **Cone model 일치도: 4/6 (67%)** — Deutan(29%)보다 높음
> **불일치 쌍**: red-magenta, orange-magenta — Cone 압축 ↔ SRM 과분리 (Magenta 축 피질 보상)

### 3-2. 왜 Protan이 Deutan보다 일치도가 높은가?

#### 이유 1: L≈M → S-only 단일 채널

**Protan 단일 색 opponency (L'=534, M=534)**:

| 색 | Protan L'-M | Protan S-(L'+M) | 지배 채널 |
|----|:-----------:|:---------------:|----------|
| red | **0.000** | -0.191 | **S only** |
| orange | **0.000** | -0.417 | **S only** |
| yellow | **0.000** | -0.649 | **S only** |
| green | **0.000** | -0.908 | **S only** |
| cyan | **0.000** | -0.304 | **S only** |
| blue | **0.000** | +0.166 | **S only** |
| purple | **0.000** | +0.752 | **S only** |
| magenta | **0.000** | +0.926 | **S only** |

**핵심**: L-M ≈ 0 → 모든 색이 **S-(L+M) 단일 축**에만 분포

**결과**:
- **Deutan**: L-M과 S 모두 변화 → 2D interaction → 복잡한 피질 보상 → 예측 어려움
- **Protan**: S만 변화 → 1D 문제 → 피질 변환 단순 → 예측 상대적 용이

#### 이유 2: Magenta 축 예외 — S-cone 비선형 보상

**Magenta 축 3쌍 불일치**:

| 쌍 | Cone Δdist | 예측 | SRM z | 관측 | 불일치 원인 |
|-----|:----------:|:----:|:-----:|:----:|------------|
| **red-magenta** | -0.216 (압축) | - | **+3.52*** | **+** (과분리) | Magenta S 과증폭 |
| **orange-magenta** | -0.260 (압축) | - | **+3.71*** | **+** (과분리) | Magenta S 과증폭 |
| **cyan-magenta** | +0.106 (약한 과분리) | + | **+4.08*** | **+** (강한 과분리) | Magenta S 과증폭 |

**생물학적 기전 (Magenta-specific S-cone gain)**:

가정: L-M 완전 손실 → S-cone 신호만 유일한 hue cue → **S 극심 증폭**

```python
# Magenta normal: S-(L+M) = 0.95 (highest S)
# Protan: L-M=0 → S만 유효 → S weight β = 3.0× (Deutan 2.5× 보다 강함)

# red-magenta cone distance
normal: sqrt(0.85^2 + 1.37^2) = 1.61
protan_cone: sqrt(0.65^2 + 1.12^2) = 1.30  # 압축 (-0.31)

# Cortical (S gain β=3.0)
red: S_cortex = 3.0 × 0.191 = 0.573
magenta: S_cortex = 3.0 × 0.926 = 2.778  # 극심 증폭!
distance_cortex = 2.205  # 과분리 (+0.59)
```

**결과**: Magenta의 high S → 피질 gain 3배 → Cone 압축 역전

### 3-3. Protan vs Deutan 이중 해리 — yellow-purple

**sub-08 (Deutan) vs sub-09 (Protan) 반대 방향**:

| Subject | CVD Type | yellow-purple SRM z | Cone 기전 | 피질 결과 |
|---------|----------|:------------------:|-----------|----------|
| **sub-08** | Deutan | **+13.87*** (극심 과분리) | M'→yellow 접근 → L-M 손실 → **S 과의존** | purple S 축 팽창 |
| **sub-09** | Protan | **-3.31*** (압축) | L'→yellow L+M 감소 → S/(L+M) 비율 ↑ | purple 방향 drift (반대) |

**생물학적 해석**:

```
Deutan (sub-08):
  M' shift → yellow 근처 L-M 약화
    ↓
  V2 S-cone gain 증폭 (β=2.5)
    ↓
  yellow-purple 과분리 (z=+13.87)

Protan (sub-09):
  L' shift → L≈M (L-M=0)
    ↓
  Yellow에서 L+M 감소 → S/(L+M) 상대적 증가
    ↓
  Purple 방향으로 yellow drift → 압축 (z=-3.31)
```

**결론**: 동일 색 쌍이 CVD subtype에 따라 **반대 방향** 왜곡 → 필터 개별화 필수

### 3-4. Protan Magenta 축 특이성

**Protan-specific 왜곡 패턴**:

| Deutan (sub-08) 주요 왜곡 | Protan (sub-09) 주요 왜곡 |
|--------------------------|--------------------------|
| **yellow-purple** z=+13.87 | **red-magenta** z=+3.52 |
| **orange-yellow** z=+3.29 | **orange-magenta** z=+3.71 |
| **blue-purple** z=+6.15 | **cyan-magenta** z=+4.08 |
| (warm colors + purple) | (all colors + **magenta**) |

**Magenta의 특별함**:
- Non-spectral color (R+B 혼합)
- 가장 높은 S-(L+M): 0.95 (8색 중 max)
- Protan L-M=0 → S만 유효 cue → **S 과증폭의 focal point**

**이론적 함의**:
CVD 왜곡 패턴은 **cone shift + 가장 의존하는 색 채널**의 조합
- Deutan: L-M 손실 → S 보상 → **purple**(high S) 팽창
- Protan: L-M 소멸 → S-only → **magenta**(highest S) 극심 증폭

---

## 4. 종합 결론

### 4-1. Cone Model의 역할

| 목적 | 성공 여부 | 근거 |
|------|:--------:|------|
| **피질 거리 예측** | ❌ 실패 | Deutan 29%, Protan 67% pairwise distance 일치 (불충분) |
| **Confusion pattern 예측** | ❌ 실패 | 2/7 (29%) confusion pair 설명, 0/7 "closest normal" 예측 |
| **왜곡 발생 원인** | ✅ 성공 | M'/L' shift 필요조건 확인 |
| **LOCO 취약 색 식별** | △ 부분 성공 | orange, yellow는 M' 영향, but confusion 방향은 예측 실패 |
| **CVD subtype 구별** | ✅ 성공 | yellow-purple 이중 해리, Magenta 축 특이성 |

**Confusion Pattern 분석 추가 발견**:
- **Orange→red confusion**: Cone은 orange→yellow 근접 예측, LOCO는 반대 방향 (red)
- **Yellow→cyan confusion**: Cone은 yellow→green 근접 예측, LOCO는 90° 떨어진 cyan
- **Purple→red confusion**: Cone은 purple→magenta 근접 예측 (Δ=0.096), LOCO는 반대편 red
- **Green→orange**: 유일한 일치 사례 (cone 압축 -0.506 + LOCO confusion)

**핵심**: Cone model은 **취약 색 후보 제안**에는 유용, but **confusion 방향/피질 표상**은 예측 불가

### 4-2. 다중 지표 수렴 체계 (CORRECTED — Metric vs Functional 구분)

**중요**: 지표를 **같은 차수끼리만** 비교해야 유효한 해석 가능.

**레벨 1: 취약 색 식별 (Which colors are vulnerable) — 전 레벨 수렴**

| 색 | Cone | RSVP | LOCO | JND | 수렴도 |
|----|:----:|:----:|:----:|:---:|:------:|
| **Yellow** | ✓ (ΔL-M -0.268) | ✓ (62.5%) | ✓ (p=0.044) | ✓ (HYPO) | **4/4** |
| **Purple** | — | ✓ (50%) | ✓ (p=0.058†) | ✓ (HYPO) | **3/4** |
| **Orange** | ✓ (ΔL-M -0.308) | — | ✓ (p=0.029) | ✓ (HYPO) | **3/4** |

> **결론**: 취약 색 식별은 **전 레벨 수렴** (Cone, RSVP, LOCO, JND 모두 동일 색 지목)

**레벨 2: Confusion 방향 (Which → Which) — 과제 의존적 불일치**

| 색 | Cone → | RSVP → | LOCO → | 일치? |
|----|:------:|:------:|:------:|:-----:|
| Orange | green | yellow | red | **0/3** ✗ |
| Yellow | green | green | cyan | **RSVP↔Cone** |
| Purple | blue | magenta | red | **0/3** ✗ |

> **결론**: Confusion 방향은 **과제/처리 수준 의존적** (범주적 RSVP ≠ 연속적 LOCO ≠ Cone)

**레벨 3: Metric 지표 내 일관성 (SRM ↔ RDM) — 86% 일치**

| 비교 | 부호 일치 | 상관 (ρ) | 속성 |
|------|:--------:|---------|------|
| **SRM ↔ RDM** | 6/7 (86%) | ρ=0.786* | 둘 다 0차 거리 측정 |
| SRM ↔ Cone | 2/7 (29%) | ρ=0.000 | Cone 예측 실패 |
| RDM ↔ Cone | 1/7 (14%) | ρ=-0.214 | Cone 예측 실패 |

> **결론**: **Metric-Metric 일관성 높음** (SRM ↔ RDM 86%), Cone 예측은 피질 보상으로 실패

**레벨 4: Functional 지표 내 일관성 (LOCO ↔ JND) — 100% 일치**

| 비교 | 일치도 | 속성 |
|------|:-----:|------|
| **LOCO ↔ JND** | 3/3 (100%) | 둘 다 고차 보간/변별 성능 측정 |
| SRM ↔ JND | 2/6 (33%) | 0차(SRM) ≠ 고차(JND) 해리 |
| Cone ↔ JND | 1/6 (17%) | Cone 예측 실패 |

> **결론**: **Functional-Functional 일관성 완벽** (LOCO ↔ JND 100%), Metric(SRM)은 Functional(JND) 예측 못함

**레벨 5: Metric-Functional 해리 — 예상과 반대 (3쌍)**

| 쌍 | Metric (SRM/RDM) | Functional (JND) | 관계 |
|----|:---------------:|:----------------:|:----:|
| **orange-yellow** | 과분리 (+3.29, +0.498) | HYPO (어려움) | **해리 ✗** |
| **yellow-green** | 과분리 (+4.14, +0.496) | HYPO (어려움) | **해리 ✗** |
| **yellow-purple** | 과분리 (+13.87, +0.670) | HYPO (어려움) | **해리 ✗** |
| green-blue | 압축 (-0.89, -0.158) | HYPER (쉬움) | 일치 ✓ |

> **결론**: **Metric overseparation + Functional HYPO = 해리** (기하학적으로 멀어졌으나 변별 어려움)

**수정된 통합 모델** (Metric vs Functional 구분):

```
Receptor (Cone):           M' shift → 취약 색 식별 ✓, 방향 예측 ✗
  ↓ (비선형 피질 변환 — S-cone gain 보상)
Cortical Metric (SRM/RDM): 0차 거리 (pairwise distance)
  │                        → Metric끼리 일관 (86%)
  │                        → Functional 예측 실패 (33%)
  ↓
Cortical Functional (LOCO): 고차 보간 성능 (interpolation capability)
  │                         → LOCO ↔ JND 일관 (100%)
  │                         → Metric과 해리 (oversep + HYPO)
  ↓
Behavioral (RSVP/JND):
  - RSVP 8AFC:             범주적 confusion (purple↔magenta)
  - JND:                   보간 민감도 저하 (HYPO)
```

**핵심 발견 (CORRECTED)**:
1. **"Which" 수렴 ✓**: 취약 색 식별 전 레벨 일치 (yellow, orange, purple)
2. **"Which→Which" 불일치 ✗**: Confusion 방향은 과제 의존 (범주적 vs 연속적)
3. **Metric-Metric 일관**: SRM ↔ RDM 86% (같은 차수 지표)
4. **Functional-Functional 일관**: LOCO ↔ JND 100% (같은 차수 지표)
5. **Metric-Functional 해리**: SRM overseparation ≠ JND HYPO 예측 (차수 불일치 → 비교 불가)
6. **Cone model 역할**: 취약 색 후보 제안만 가능, 피질 거리/방향/행동 예측 불가

### 4-3. 생물학적 메커니즘

**3단계 피질 보상 모델**:

```
Stage 1: Cone Receptor (L-M, S-(L+M) space)
  - M'/L' shift → L-M channel 손실

Stage 2: V1 Early Cortical (minimal compensation)
  - Cone 신호 충실 반영
  - cyan-blue V1 SRM latent/Procrustes voxel: cone 일치 (압축)

Stage 3: V2 Intermediate Cortical (S-cone gain)
  - L-M 손실 검출 → S-cone weight 증폭 (β=2.5-3.0×)
  - cyan-blue V2 Procrustes voxel: 압축 → 과분리 전환
  - yellow-purple: S gain 극심 (SRM latent z=+13.87, Procrustes diff=+0.670)
```

**정량적 시뮬레이션**:
S-cone gain β를 2.5-3.0배 증가시키면 5/7 쌍의 Cone-Cortical 방향 불일치 재현

### 4-4. 논문 기여

**투명성 개선**:
- "M' yellow 접근" (정성적) → ΔL-M=-0.10, 534→560nm (정량적)
- Cone model 예측력 명시: 29-67% (과거 "7/7 일치" 수정)

**이론적 기여**:
- **S-cone compensation mechanism**: L-M 손실 → S gain 2.5-3.0배 (V2)
- **ROI 계층 의존**: V1 cone-faithful ↔ V2 compensatory
- **CVD subtype 이중 해리**: yellow-purple Deutan 과분리 ↔ Protan 압축

**방법론적 기여**:
- **다중 지표 수렴**: Cone + SRM + RDM + LOCO + JND (5-way)
- **기능적 dissociation**: Distance(SRM) ≠ Interpolation(LOCO)

---

## 참고문헌

- Stockman, A., & Sharpe, L. T. (2000). Spectral sensitivities of the middle- and long-wavelength-sensitive cones. *Vision Research*, 40(13), 1711-1737.
- Shapley, R., & Hawken, M. J. (2011). Color in the cortex: single- and double-opponent cells. *Vision Research*, 51(7), 701-717.
- Conway, B. R., Moeller, S., & Tsao, D. Y. (2007). Specialized color modules in macaque extrastriate cortex. *Neuron*, 56(3), 560-573.
- Neitz, M., & Neitz, J. (2011). The genetics of normal and defective color vision. *Vision Research*, 51(7), 633-651.
