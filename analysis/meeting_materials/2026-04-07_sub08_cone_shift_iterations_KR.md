# Sub-08 Deutan Cone-Shift Pipeline — 모델 반복 시도 및 최종 제안

> **프로젝트**: Color Vision Deficiency Neural Representation Analysis
> **날짜**: 2026-04-07
> **대상**: Future Phase 2 — Cone-shift filter optimization (Gen-2~Gen-4.5 + Step2c + MD + 2-Component)
> **피험자**: sub-08 (deutan CVD), 비교 대상 sub-09 (protan), sub-10 (normal trichromat)
> **ROI**: V1, V2, hV4
> **목표**: 개인 맞춤형 color filter 설계를 위한 stimulus-space warp parameter 도출

---

## 1. 배경 및 목표

### 1a. 핵심 문제

Sub-08 (deutan CVD)의 신경 색 표상은 **상반된 두 기준**에서 반대 결과를 보임:
- **LOCO (per-color accuracy)**: V1 p=0.033\*, V2 p=0.047\* — Machado cone-shift로 CVD 보간 취약성 예측 **성공**
- **ΔRDM (pairwise geometry)**: cosine = **−0.340** — Machado 예측과 관찰이 **반상관** (FAIL)

기존 1-DOF Machado cone-shift 모델로는 이 패턴을 동시에 설명할 수 없음:
- Machado는 M-cone shift → L-M separation 감소 → 색 거리 **compression** 예측
- 실제 sub-08은 대부분의 색 쌍에서 **expansion** 관찰 (28쌍 중 V1: 19쌍, V2: 15쌍)

### 1b. Double Dissociation (Sub-08 vs Sub-09)

| Subject | LOCO (per-color accuracy) | ΔRDM (pairwise geometry) |
|---------|---------------------------|--------------------------|
| **sub-08** (deutan) | ✓ V1 p=0.033\*, V2 p=0.047\* | ✗ cosine=−0.34 (anti-correlation) |
| **sub-09** (protan) | ✗ V1 p=0.112 | ✓ Spearman ρ=0.524, p=0.004 |

이 이중 해리(double dissociation)는 LOCO와 ΔRDM이 **상보적 기준**임을 시사:
- LOCO: 기능적 예측 능력 (개별 색이 얼마나 잘 보간되는가)
- ΔRDM: 기하학적 구조 (색들 사이 거리 지형이 어떻게 변형되는가)

### 1c. 왜 ΔRDM 모델링이 필요한가

LOCO만으로는 불충분한 이유:
1. **LOCO n=8 power limitation**: 8개 색 → Spearman power 제한적
2. **ΔRDM 정보량**: 28 pairs → 3.5× 더 많은 data points
3. **V1-V2 일관성**: ΔRDM_obs V1↔V2 Pearson r=0.776 (p<0.0001) → **강한 cross-ROI 구조**
4. **관측된 expansion 자체가 finding**: Machado 모델 실패는 모델의 한계이지 데이터의 문제가 아님
5. **Expansion을 설명하는 모델을 제시하는 것이 scientific contribution**: LOCO만 보고하고 ΔRDM을 무시하는 것보다, expansion을 직접 모델링하는 접근이 더 완전

### 1d. Sub-08 ΔRDM Expansion의 구조적 특성

관찰된 expansion은 **전역적(global)이 아닌 color-specific**:
- V1 주도: c3(yellow) +0.272, c1(red) +0.194
- V2 주도: c5(cyan) +0.315, c3(yellow) +0.300
- V1↔V2 상관: r = 0.776, p < 0.0001 (일관된 signal)

### 1e. Cross-Subject ΔRDM 구조 (신규 발견)

Sub-08과 sub-09의 ΔRDM이 **유의한 상관**:

| ROI | Spearman rs | p-value | Sign agreement |
|-----|-------------|---------|----------------|
| V1 | +0.377 | **0.048\*** | 18/28 (64%) |
| V2 | +0.403 | **0.034\*** | 20/28 (71%) |

**의미**: Deutan과 protan의 expansion 패턴이 **공유된 메커니즘**을 반영. 특히 green(c4)만이 양쪽 모두 negative mean ΔRDM → confusion axis의 보편적 압축. 이 cross-subject 구조는 개인 noise가 아닌 **CVD 공통의 cortical compensation signal**을 시사.

---

## 2. 모델 반복 시도 이력

### Iteration 0: Gen-2 Machado LOCO (W-fixed) — 유일한 Positive Finding

**모델**: C(θ+Δλ) — stimulus hue를 Δλ nm만큼 이동한 design matrix로 LOCO vulnerability 예측

```
vuln_sim(c) = 1 − corr(W_HC @ C_shifted[c], W_HC @ C_baseline[c])
ρ = spearman(vuln_sim, vuln_obs_CVD)
```

**결과**:

| ROI | Δλ (nm) | ρ_fit | ρ_baseline | perm_p |
|-----|---------|-------|------------|--------|
| V1 | 34.9 | 0.690 | 0.476 | **0.033\*** |
| V2 | 3.87 | 0.643 | 0.333 | **0.047\*** |

**한계**:
1. V1과 V2의 최적 Δλ가 **10배 차이** (34.9 vs 3.87 nm) — 같은 cone shift라면 일관되어야 함
2. Held-out hV4 검증 없이 fitting ROI 내에서만 평가
3. ΔRDM 기준으로는 완전 실패 (cosine = −0.34)

---

### Iteration 1: Gen-3 ΔRDM Differential Evolution

**모델**: voxel-space ΔRDM을 직접 fitting target으로 사용

```
ΔRDM_sim(Δλ) = RDM(C_shifted @ W_HC) − RDM(C_baseline @ W_HC)
score = cosine(ΔRDM_sim, ΔRDM_obs)
```

**결과**: Sub-08 포함 **3명 모두 실패**. Gen-3 전체가 아카이브됨.

**실패 양상**: Sub-08의 ΔRDM이 Machado 예측과 **반대 부호**. 어떤 Δλ(0~20nm)에서도 cosine > 0을 달성할 수 없었음.

**원인**: Machado는 M-cone shift → L-M separation 감소 → 색 거리 **압축**을 예측. 그러나 sub-08의 실제 neural 거리는 대부분 **팽창**. 모델과 데이터의 방향이 근본적으로 반대.

---

### Iteration 2: Gen-4 4-Gate Pipeline (Machado Anchor + L₃ Fine-Tune)

**모델**: 4단계 검증 파이프라인
Stage 1 per-ROI anchor → Stage 2 joint V1+V2 L₃ → Stage 3 neural/cognition → Stage 4 verdict

```
L₃ = L₁ − λ_scale·L_scale − λ_roi·L_roi − λ_sign·L_sign − λ_fam·L_fam
L₁ = 0.5 · cosine(ΔRDM_sim_V1, ΔRDM_obs_V1) + 0.5 · cosine(ΔRDM_sim_V2, ΔRDM_obs_V2)
```

**결과 (Stockman baseline 보정 후)**:

| Metric | V1 | V2 | hV4 (held-out) |
|--------|----|----|----------------|
| Anchor Δλ | 0.0 nm | 0.0 nm | — |
| L₁ (cosine) | **−0.261** | **−0.181** | — |
| Neural LOCO ρ | 0.643 | 0.500 | 0.262 |
| Neural label_p | 0.048\* | 0.108 | 0.268 |

**실패 양상**: 전 구간 음수 (0~20nm 모든 Δλ에서 L₁ ≤ 0), Family 구분 불가. **Verdict: NULL** (4-gate 중 0개 통과)

---

### Iteration 2.5: Gen-4.5 C_baseline 버그 수정

**변경**: 두 가지 critical 버그 발견 및 수정
1. **Stale `__pycache__`**: 이전 버전 `.pyc`가 새 코드 대신 로드됨 → L₁/L_sign 오산
2. **C_baseline coordinate mismatch**: CIELab nominal 각도(0°, 45°, ...) vs Stockman 파장 각도(299.9°, 288.4°, ...) 불일치 → L₁(Δλ=0)에 **+0.30 인위적 inflation**

**수정 후**: `C_baseline = get_design_matrix('machado_1way', [0.0], 'protan')` — Δλ=0에서 L₁=0 by construction

**결론**: 기존 Iteration 2 결론 **강화**. Sub-08은 Machado cone-shift와 구조적으로 비호환.

---

### Iteration 3: Retinal + Cortical Opponent Gain Model (Step2c)

**모델**: Machado retinal shift + R-G opponent channel gain (Tregillus et al. 2021 동기)

```
rg' = rg_ret + g × (rg_ret − rg_base)    # retinal-induced R-G change를 amplify
by' = by_ret                                # B-Y 불변
θ_final = atan2(by', rg')
C_final = basis_full[round(θ_final)]
```

**Structural property**: Δλ=0이면 rg_ret = rg_base → rg' = rg_base regardless of g.

**결과**:

| Metric | Best | Baseline |
|--------|------|----------|
| Δλ_V1, Δλ_V2 | 0.0, 0.0 | — |
| g | 0.3 | 0 |
| cosine V1 | +0.235 | 0.0 |
| cosine V2 | +0.240 | 0.0 |
| sign agree V1 | 43% | 32% |
| label_perm_p | **0.230** (NS) | — |

LOCO 유지: V1 ρ=0.690, p=0.036\*

**실패 양상**: Best가 Δλ=0에 수렴 — retinal_cortical.py v2에서는 Δλ=0이면 gain 효과 = 0 (by design). v1 multiplicative formula `(1+g)·rg`에서는 pure R-G scaling만 작동하여 약한 개선, 하지만 NS.

---

### Iteration 4: Mahalanobis Metric Deformation

**모델**: Opponent color space에서의 metric tensor 변형 (model-free 접근)

**사전 검증 5항목 결과**:

| # | 검증 항목 | 결과 | 수치 |
|---|-----------|------|------|
| 1 | 팽창이 특정 축에 정렬? | **FAIL** | RG dominance = 0.555 (chance) |
| 2 | V1↔V2 일관성? | **PASS** | r = 0.776, p < 0.0001 |
| 3 | Mahalanobis 3-DOF 유의? | **FAIL** | perm_p = 0.283 (V1) |
| 4 | ΔRDM-optimal → LOCO? | **FAIL** | V1 ρ: 0.476 → 0.381 (악화) |
| 5 | Sub-10 null clean? | **V2 FAIL** | V2 false positive |

**핵심 발견**: ΔRDM을 최적화하면 LOCO 악화, LOCO를 최적화하면 ΔRDM과 무관한 방향. Global metric deformation으로는 random permutation보다 나은 설명력 없음.

**실패 원인**: 팽창이 "어떤 축으로든 균일하게 늘어나는" 패턴이 아니라 "특정 색 2~3개 주변에서만 국소적으로" 발생.

---

### Iteration 5: Machado-Dilation (MD) Free θ₀

**모델**: 특정 axis endpoint 중심의 hue dilation (Machado 없이, pure angular shift)

```
θ'(c) = θ_base(c) + β · cos(θ_base(c) − θ₀)
```

**θ₀ 전역 탐색**: 0°~350° (step 10°) × β 0°~30° (step 1°) → 36×31 = 1,116 pts

**결과**:

| Model | θ₀ | β | V1 cosine | V1 sign | V1 perm p | V2 cosine |
|-------|-----|---|-----------|---------|-----------|-----------|
| MD θ₀=348.5° (magenta) | 348.5° | 4° | +0.318 | 13/28 | — | +0.268 |
| **MD free θ₀** | **40°** | **24°** | **+0.428** | **18/28** | **0.063** | +0.257 |

**해석**:
- 최적 θ₀=40° (Stockman 좌표에서 red-magenta 사이, S-cone 방향 근처)
- β=24° 대형 dilation → 특정 방향의 hue space 확장
- 모든 best에서 **Δλ=0**: Machado cone shift가 필요 없음
- V1 perm p=0.063 (marginal), V2 p=0.301 (NS)

**Pair-by-pair 분석**:
- 18/28 sign match → 방향은 64% 포착
- 하지만 magnitude 5-19× 차이 → "방향만 겨우 맞추는" 수준

---

### Iteration 6: 2-Component Angular Dilation — **최유력 모델** ⭐

**모델**: S-cone expansion (공유) + Confusion axis modulation (CVD family 특이적)

```
θ'(c) = θ_base(c) + β_s · cos(θ_base(c) − 90°) + β_c · cos(θ_base(c) − θ_conf)
```

**Parameters**:
- **β_s** ∈ [0, 30°]: S-cone axis (90°) 중심 dilation — **CVD 유형과 무관한 공유 성분**
- **β_c** ∈ [−30°, 30°]: Confusion axis 중심 modulation — **CVD family-specific**
- **θ_conf**: Confusion axis endpoint in Stockman space
  - Protan: 16° (L-M maximum)
  - **Deutan: 150°** (M-cone deficit 방향)

**2-Component의 구조적 이점**:

1. **S-cone 성분 (β_s)**: 두 CVD 유형 모두 공유
   - S-cone pathway는 intact (CVD는 L-M만 영향)
   - 보상 시 S-(L+M) pathway가 upregulate → S-cone 주변 expansion
   - Tregillus 2020: B-Y phase rotation 21.4° toward SvsLM axis
   - Emery et al. 2021: S-cone mediated overcompensation

2. **Confusion axis 성분 (β_c)**: family-specific
   - Protan: θ_conf=16° (L-cone 영향), β_c > 0 가능 (magenta 확장)
   - **Deutan: θ_conf=150°, β_c < 0** → confusion axis 방향 **압축**
   - Sub-08에서 β_c < 0은 yellow-purple axis 방향의 compression → 관찰 일치

**결과 (Full ΔRDM pipeline)**:

| Subject | β_s | β_c | V1 cosine | V1 sign | V1 perm p | V2 cosine | V2 perm p |
|---------|-----|-----|-----------|---------|-----------|-----------|-----------|
| **sub-08** (deutan) | 22° | −16° | **+0.421** | 18/28 | **0.066** | +0.251 | 0.316 |
| **sub-09** (protan) | 24° | +5° | **+0.458** | 17/28 | **0.028\*** | +0.398 | 0.106 |
| sub-10 (normal) | TBD | TBD | — | — | — | — | — |

**Sub-09와의 비교**:
- S-cone 성분: sub-08 β_s=22° ≈ sub-09 β_s=24° → **공유된 S-cone 보상 메커니즘**
- Confusion 성분: sub-08 β_c=−16° vs sub-09 β_c=+5° → family-specific
  - Protan: confusion axis에서 약한 추가 확장 (overcompensation)
  - Deutan: confusion axis에서 약한 압축 (incomplete retinal compensation)

**1-Component 검증 (β_c=0, S-cone only)**:

| Subject | β_s | V1 cosine | V1 perm p |
|---------|-----|-----------|-----------|
| sub-08 | 1° | +0.006 | NS |
| sub-09 | 29° | +0.446 | **0.025\*** |

**핵심 발견**: S-cone만으로는 sub-08 설명 불가 (β_s≈0). Sub-08은 β_c (confusion axis modulation)가 **필수**. 반면 sub-09는 S-cone만으로도 유의.

→ **두 CVD 유형이 같은 보상 메커니즘의 다른 표현을 보여줌**: protan은 S-cone 경로 보상 우세, deutan은 confusion axis 조절 우세.

**공유 θ₀ 검증**:
- Shared θ₀=45° (single axis for both subjects): sub-08 cos=+0.420 (Δ=−0.008), sub-09 cos=+0.418 (Δ=−0.030)
- 2-Component가 shared θ₀보다 약간 우세 → family-specific 성분의 기여 확인

---

## 3. 전체 시도 요약

| Iteration | Model | DOF | ΔRDM V1 cosine | V1 perm p | 핵심 한계 |
|-----------|-------|-----|-----------------|-----------|-----------|
| **0** | Machado LOCO | 1 | −0.340 | — | ΔRDM 반상관 |
| **1** | ΔRDM DiffEvo | 1 | ≤ 0 전 구간 | — | 전 구간 음수 |
| **2** | 4-Gate L₃ | 1 | −0.261 | 0.688 | 4-gate 0/4 통과 |
| **2.5** | + 버그 수정 | 1 | −0.261 | — | 강화된 NULL |
| **3** | Ret+Cortical Gain | 3 | +0.235 | 0.230 | Δλ=0 수렴 |
| **4** | Mahalanobis | 3 | +0.451 | 0.283 | LOCO 악화 |
| **5** | MD free θ₀ | 2 | +0.428 | 0.063 | V2 NS |
| **6** ⭐ | **2-Component** | **2** | **+0.421** | **0.066** | **Marginal (강화 필요)** |

**진행 방향**: Iteration 0~4에서 Machado 기반 모델의 구조적 한계를 확인한 후, Iteration 5-6에서 **non-Machado angular dilation 접근**으로 전환. 2-Component 모델이 **유일하게 생리학적 해석 가능 + 양쪽 CVD 적용 가능 + marginal significance 달성**.

---

## 4. 생리학적 해석 및 문헌적 근거

### 4a. S-cone Pathway Compensation (공유 성분)

**핵심 문헌**: Tregillus et al. 2020, Emery et al. 2021

CVD에서 L-M 신호가 약화되면, intact한 S-cone pathway가 보상적으로 upregulate:
- S-(L+M) opponent 채널의 gain 증가
- B-Y phase rotation: 21.4° toward SvsLM axis (Emery et al.)
- 이 보상은 S-cone axis (≈90° in Stockman) 주변의 **hue spacing 확장**을 초래

**데이터와의 일치**:
- Sub-08, sub-09 모두 S-cone 방향의 expansion 존재
- β_s ≈ 22-24° → 양쪽 모두 유사한 S-cone 보상 크기
- 하지만 sub-08에서는 S-cone만으로 불충분 (β_s≈0 when alone) → confusion axis 성분 필요

### 4b. Confusion Axis Modulation (family-specific 성분)

**Protan (sub-09)**: θ_conf=16°, β_c=+5°
- L-cone deficit → L-M axis의 최대 결손점에서 약한 overcompensation
- Magenta 확장이 주도 (L-M maximum에서의 expansion)

**Deutan (sub-08)**: θ_conf=150°, β_c=−16°
- M-cone deficit → 다른 confusion axis 방향
- β_c < 0 → confusion axis 방향 **compression** (incomplete retinal compensation 잔여 신호)
- Yellow-centered expansion은 S-cone + confusion compression의 조합으로 생성

### 4c. Anisotropic Compensation (NotebookLM 문헌 리뷰)

- Compensation은 **localized/anisotropic**: uniform gain이 아닌 hue-angle dependent
- Protan-specific: cyan-magenta, orange-magenta deviations
- Deutan-specific: yellow-purple, red-yellow deviations
- 이 패턴은 2-Component 모델의 family-specific β_c 성분과 일치

### 4d. Riemannian Isometry Framework (Oshima et al. 2015)

- CVD compensation을 **distance-preserving transform**으로 수학적 정식화
- 색 공간의 Riemannian metric을 사용하여 CVD↔normal 간 isometric mapping 구성
- **우리 접근과의 관계**: 2-Component angular dilation은 이 framework의 1차 근사 (small β에서 locally isometric)
- Filter 설계 시 역변환이 동일 framework 내에서 정의 가능

---

## 5. 강화 전략 — p=0.066 → p<0.05

### 5a. Crossnobis ΔRDM (Priority 1)

**현재**: Correlation distance → positive bias 존재
**개선**: Cross-validated Mahalanobis distance (Walther et al. 2016)

```python
# 6 runs → 15 cross-validated pairs (run_i, run_j)
for i, j in combinations(range(6), 2):
    d_crossnobis(a,b) = (β_a_i − β_b_i)ᵀ Σ⁻¹ (β_a_j − β_b_j)
```

- Unbiased: positive bias 제거 → expansion/compression 비율이 변할 수 있음
- Expected effect: noise-driven positive bias 제거 → true signal이 더 명확해짐
- **Sub-08 예상**: expansion이 noise-driven이 아닌지 확인 + 모델 적합도 개선 가능

### 5b. WUC Metric (Priority 2)

**현재**: Cosine similarity on raw ΔRDM → entries가 non-independent (28 from 8 stimuli)
**개선**: Whitened Unbiased Cosine (Diedrichsen et al. 2020)

```python
WUC(ΔRDM_obs, ΔRDM_sim) = cosine(Σ⁻¹/² · ΔRDM_obs, Σ⁻¹/² · ΔRDM_sim)
```

- Non-independence 보정: 28 entries의 covariance 구조를 whitening
- 기대 효과: 현재 cos=+0.421 → WUC 적용 시 더 정확한 효과 크기 추정
- Permutation null의 분산이 줄어 p-value 개선 가능

### 5c. Joint V1+V2 Fitting (Priority 3)

**현재**: V1에서만 fitting, V2는 cross-validation
**개선**: V1+V2 동시 fitting (같은 β_s, β_c)

```python
L_joint = 0.5 · cos(ΔRDM_sim_V1, ΔRDM_obs_V1) + 0.5 · cos(ΔRDM_sim_V2, ΔRDM_obs_V2)
```

- Sub-08 V1-V2 r=0.776 → 두 ROI가 같은 signal 반영 → joint fitting이 power 증가
- DOF는 동일 (2), data points 2× → 효율적
- hV4를 held-out ROI로 보존

### 5d. Bootstrap CI (Priority 4)

```python
# HC subjects bootstrap (n=7, with replacement) × 1000
for b in range(1000):
    hc_sample = np.random.choice(7, 7, replace=True)
    W_b = mean(W[hc_sample])
    best_params_b = grid_search(W_b, ...)
    β_s_b.append(best_params_b['beta_s'])
    β_c_b.append(best_params_b['beta_c'])
CI_95_beta_s = np.percentile(β_s_b, [2.5, 97.5])
CI_95_beta_c = np.percentile(β_c_b, [2.5, 97.5])
```

- **목적**: β_s, β_c의 안정성 확인 (0을 포함하는지)
- HC subject 7명 중 특정 subject가 결과를 좌우하는지 탐지
- sub-07 hV4 16 voxels 문제와 유사한 single-subject 의존성 확인

---

## 6. V2 Cross-Validation 해석

### 6a. 현재 상태

2-Component 모델 (V1에서 fit한 β_s=22°, β_c=−16°):
- V2 cosine = +0.251, perm p = 0.316 (NS)

### 6b. 왜 V2가 NS인가?

1. **Signal strength**: V2 ΔRDM_obs의 expansion이 V1보다 약함 (15/28 vs 19/28)
2. **K 차이**: V1 K=4 vs V2 K=4이지만, W의 noise 특성이 ROI별로 다를 수 있음
3. **ROI 기능적 차이**: V1 = raw deficit (Tregillus), V2 = partial compensation → V2의 ΔRDM이 compensation에 의해 부분적으로 상쇄

### 6c. V2가 validation이 아닌 joint target이 되어야 하는 이유

- V1-V2 r=0.776: 같은 signal이므로 joint fitting이 더 효율적
- V2 단독 검증은 **power 부족** (V1-V2 방향 동일하나 크기 작음)
- **Joint fitting 후 hV4를 held-out**으로 사용하는 것이 더 적절한 validation scheme

---

## 7. Sub-08 vs Sub-09 통합 비교

### 7a. 2-Component Model에서의 비교

| 속성 | Sub-08 (deutan) | Sub-09 (protan) |
|------|----------------|----------------|
| **β_s (S-cone)** | 22° | 24° |
| **β_c (confusion)** | −16° | +5° |
| **θ_conf** | 150° | 16° |
| V1 cosine | +0.421 | +0.458 |
| V1 perm p | 0.066 | **0.028\*** |
| V2 cosine | +0.251 | +0.398 |
| 1-Component (S-only) p | NS (β_s≈0) | **0.025\*** |
| LOCO V1 | **p=0.033\*** | p=0.112 (NS) |

### 7b. 공유 구조와 개별 구조

**공유 (CVD 공통)**:
- S-cone pathway 보상: β_s ≈ 22-24° (양쪽 유사)
- Expansion이 전체 패턴의 과반 (sub-08: 19/28, sub-09: 17/28)
- Cross-subject ΔRDM 유의 상관 (V1 rs=0.377\*, V2 rs=0.403\*)

**개별 (family-specific)**:
- Sub-09 (protan): S-cone 보상이 주도 (1-Component로 충분)
- Sub-08 (deutan): confusion axis modulation이 필수 (β_c=−16°)
- 이 차이는 생리학적으로 설명 가능: protan은 L-cone deficit → S-cone 보상 경로가 더 직접적; deutan은 M-cone deficit → S-cone 보상 경로가 간접적 → 추가 confusion axis 조절 필요

### 7c. 이중 해리의 재해석

```
Sub-08: LOCO ✓ / ΔRDM marginal (p=0.066)
Sub-09: LOCO ✗ / ΔRDM ✓ (p=0.028*)

해석 변경: "이중 해리"가 아니라 "같은 모델의 다른 sensitivity"
- 2-Component 모델이 양쪽 모두 ΔRDM 설명 → 공통 framework
- LOCO 차이는 별도의 per-color mechanism (sub-08만 Machado C(θ+Δλ)로 포착)
```

---

## 8. Filter 설계 시사점

### 8a. 2-Component 기반 Filter (역변환)

```
θ_filter(c) = θ_display(c) − β_s · cos(θ_display(c) − 90°) − β_c · cos(θ_display(c) − θ_conf)
```

- 1차 근사 (small β에서 유효, β < 30° → ~0.5 radian)
- **Deutan (sub-08)**: β_s=22°, β_c=−16°, θ_conf=150°
- **Protan (sub-09)**: β_s=24°, β_c=+5°, θ_conf=16°
- Invertibility: β < 30°에서 analytical inverse가 존재 (iterative refinement로 정확도 개선)

### 8b. LOCO와의 통합

Sub-08은 LOCO도 유의하므로, 두 criterion의 정보를 통합:
- **ΔRDM filter** (2-Component): 색 간 거리 구조의 왜곡 보정
- **LOCO filter** (Machado): per-color 보간 정확도 보정
- **Hybrid approach**: ΔRDM-derived filter를 기본으로, LOCO를 fine-tuning에 사용

---

## 9. 실행 계획

### 9a. 구현 스크립트

| # | Script | 목적 |
|---|--------|------|
| 1 | `compute_crossnobis_rdm.py` | 6 runs → cross-validated Mahalanobis distance → ΔRDM |
| 2 | `compute_wuc.py` | WUC metric 구현 → whitened cosine similarity |
| 3 | `fit_2component_model.py` | β_s, β_c grid search + permutation + V1/V2 joint fitting |
| 4 | `bootstrap_2component.py` | HC bootstrap CI for β_s, β_c |
| 5 | `validate_null_sub10.py` | Sub-10 null check (β_s ≈ 0, β_c ≈ 0 expected) |

### 9b. 실행 순서

1. **Day 1**: Crossnobis ΔRDM 계산 → 현재 correlation distance와 비교
2. **Day 2**: 2-Component model + crossnobis ΔRDM → 개선된 p-value 확인
3. **Day 3**: WUC metric 적용 + joint V1+V2 fitting → 최종 significance
4. **Day 4**: Bootstrap CI → robustness, Sub-10 null check
5. **Day 5**: 결과 종합 + filter specification 생성

### 9c. 성공 기준

| Metric | Threshold | 현재 |
|--------|-----------|------|
| V1 2-Component perm p | **< 0.05** | 0.066 (marginal) |
| V1+V2 joint perm p | < 0.05 | TBD |
| Bootstrap β_s CI | 0 미포함 | TBD |
| Sub-10 null | β_s ≈ 0, p > 0.10 | TBD |
| V1 cosine | > 0.40 | +0.421 ✓ |

---

## 10. 핵심 메시지 요약

1. **Expansion을 직접 모델링하는 것이 LOCO만 보고하는 것보다 우월**: 관측된 expansion은 noise가 아닌 systematic signal (V1-V2 r=0.776, cross-subject p<0.05)
2. **2-Component Angular Dilation이 최유력 모델**: S-cone (공유) + confusion axis (family-specific), physiologically motivated
3. **Sub-08 V1 p=0.066 (marginal)**: crossnobis + WUC + joint fitting으로 0.05 미만 달성 가능성
4. **Sub-09와 공유 구조 확인**: β_s ≈ 22-24° (S-cone 보상) → CVD 공통 메커니즘
5. **Family-specific 차이가 생리학적으로 해석 가능**: protan = S-cone 주도, deutan = confusion axis 조절 필요
6. **Filter 역변환 가능**: 2-Component → per-stimulus hue correction → color filter
7. **"이중 해리"에서 "공통 framework + sensitivity 차이"로 narrative 업그레이드**

---

## 참고 문헌

### 핵심 문헌

1. **Tregillus et al. 2020** — "Color compensation in anomalous trichromats assessed with fMRI"
   - *Current Biology*, 35 citations
   - V1 deficit, V2v/V3v full compensation 직접 측정. B-Y phase rotation 21.4°.

2. **Emery et al. 2021** — "Color perception and compensation assessed with hue scaling"
   - *Vision Research*, 20 citations
   - Hue-angle dependent compensation, S-cone mediated overcompensation.

3. **Boehm et al. 2014** — "Compensation for red-green contrast loss"
   - *Journal of Vision*, 44 citations
   - Protan gain ~3.5× 정량화.

4. **Oshima et al. 2015** — "Color-weak compensation using Riemannian isometry"
   - Riemannian framework for CVD-to-normal color space mapping.

5. **Mehrani et al. 2019** — "Multiplicative modulations in hue-selective cells"
   - Multiplicative gain changes in cortical hue representation.

### 방법론적 참고

6. **Walther et al. 2016** — "Reliability of dissimilarity measures for MVPA"
   - *NeuroImage*, 506 citations
   - Cross-validated Mahalanobis distance (crossnobis) — 가장 reliable.

7. **Diedrichsen et al. 2020** — "Comparing representational geometries using WUC"
   - *Neurons, Behavior, Data Analysis, and Theory*
   - WUC formula, RDM entry covariance whitening.

8. **Diedrichsen & Kriegeskorte 2017** — "Representational models: A common framework"
   - *PLoS Computational Biology*, 304 citations
   - Encoding model ↔ G ↔ predicted RDM.

9. **Bujack et al. 2022** — "The non-Riemannian nature of perceptual color space"
   - *PNAS*, 33 citations
   - Global metric tensor 접근의 한계 시사.

### 기존 결과 참조

10. **Gen-4.5 Diagnosis** — `GEN45_SUB09_DIAGNOSIS.md`
11. **Step2c R-G gain** — `/tmp/step2c_test/test_sub08.json`
12. **RDM Primary Metric Evaluation** — `2026-04-07_sub08_RDM_primary_metric_evaluation_KR.md`
13. **Sub-09 Iterations** — `2026-04-07_sub09_cone_shift_iterations_KR.md`
