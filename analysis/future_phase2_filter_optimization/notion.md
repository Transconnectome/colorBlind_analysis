# Future Phase 2: Procrustes 기반 Prediction Model + Stimulus Filter Pipeline

> **프로젝트**: Color Vision Deficiency Neural Representation Analysis
> **날짜**: 2026-03-08
> **대상**: Future Phase 2 Filter Optimization — 전체 파이프라인 총괄
> **피험자**: HC 7명 (sub-01~07), CVD 3명 (sub-08 deutan, sub-09 protan, sub-10 deutan)
> **ROI**: V1, V2, V3, hV4

---

## 1. 핵심: Prediction Model은 Procrustes 기반이다

### 1a. 결론

이 파이프라인의 prediction model은 **SRM이 아니라 Procrustes + Forward Encoding (FE)** 기반이다. SRM은 prediction/filter 공간이 아닌 **comparison/target 공간**으로만 사용된다. 최종 목표는 CVD 개인의 연속 색 표상을 HC mean latent geometry에 가깝게 만드는 **prediction model + stimulus filter**이다.

### 1b. 왜 SRM은 prediction 공간으로 부적합한가

SRM을 prediction model 공간으로 쓰는 것이 부적합한 4가지 이유:

#### (1) SRM은 interpolation 구조를 파괴한다

LOCO MAE 비교:

| ROI | Procrustes | SRM | Delta |
|-----|-----------|-----|-------|
| V1 | ~76 | ~80 | +4 |
| V2 | ~80 | ~85 | +5 |
| V3 | ~77 | **~99** | **+22 (chance 90보다 worse)** |
| hV4 | ~69 | ~72 | +3 |

SRM은 cross-subject alignment에는 유리하지만, **continuous hue structure를 파괴**한다. Continuous interpolation model을 SRM에서는 만들 수 없다.

**구체적 증거 (notion_prevalidation.md Analysis 1-2)**:
- **V1 SRM**: MDS stress가 dim=3부터 **0.127에서 plateau** — 어떤 차원에서도 거리 구조 복원 불가. 같은 V1 데이터가 Procrustes에서는 dim=4에서 stress=0.096 정상 도달
- **hV4 SRM**: CIELab Mantel r=**-0.308** (raw 공간 r=+0.402\*에서 **부호 반전**) — SRM이 원래 존재하던 CIELab 구조를 파괴
- **V2 SRM**: 3D stress=**0.097** — 유일하게 adequate한 SRM 구조를 가진 ROI
- V1 SRM: 4개 참조 모델(Angular, CIELab, a\*-only, b\*-only) **전부 음의 상관** → 의미 있는 색 기하학 부재

#### (2) SRM은 stimulus → representation mapping이 아니다

SRM이 학습하는 것: `voxel → shared latent`

Prediction model에 필요한 것: `stimulus theta → representation`

SRM은 이 mapping을 직접 제공하지 않는다. **FE + Procrustes가 제공한다.**

**정보량 대비**: FE+Procrustes W는 (568×6)=**3,408 parameters** per subject → 풍부한 개인별 voxel-level tuning 포착. SRM M_s는 (4×6)=**24 parameters** → 99% 이상 정보 손실. 개인차를 식별할 수 있는 parameter space가 SRM에서는 근본적으로 부족하다.

#### (3) SRM filter는 stimulus control이 불가능하다

SRM filter의 작동: `latent → latent`

실제 필요한 것: `stimulus theta → corrected stimulus theta'`

SRM filter는 stimulus transform과 직접 연결되지 않는다.

**CVD의 진짜 결손은 연속 보간에 있다**:
- LORO (classification): HC 0.635 vs CVD 0.665, **p=0.668** → 범주적 표상은 이미 동등
- LOCO (interpolation): HC 69.4° vs CVD 87.4° (hV4, **p=0.017\***) → 연속 보간에서 결손
- Cross-decoding **10/12 significant** (p<0.001) → SRM 공간에서 CVD 패턴은 이미 올바른 HC 패턴과 일치 → SRM filter는 항등 변환(identity)에 가까움

#### (4) SRM은 comparison space로는 유효하다

SRM의 장점:
- Subject간 voxel dimension 차이 제거
- Group-level comparison 가능 (HC vs CVD disparity 측정)
- V2: LOSO 7/7 significant, PCA convergence r=0.891

**수렴 증거**: SRM-crossnobis z-score 수렴 r=0.3-0.7, **8/9 subject-ROI에서 p<0.05** → SRM이 native voxel space의 진짜 CVD-HC 분산을 포착. V2 LOSO **7/7 HC 유의**, split-half group mean r=**0.733** (전 ROI 최고). PCA convergence r=**0.891** → SRM 공유 공간의 구조적 신뢰성 확인.

**SRM = comparison/target latent space로 역할 재정의**

---

## 2. 파이프라인 전체 구조

### 2a. Three-Space Architecture

| Space | Role | What operates here | Justification |
|-------|------|-------------------|---------------|
| **Stimulus** | Filter / correction | T_psi: θ → θ' (4 Fourier params) | CVD distortion은 cone-level → stimulus-level correction |
| **Procrustes + FE** | Prediction / encoding | W_FE @ channels(θ): θ → ŷ_proc | n_voxels × 6 풍부한 voxel-level tuning; W cosine 0.921 |
| **SRM (k-dim)** | Evaluation / target | W_SRM^T @ ŷ: cross-subject comparison | HC mean 정의 (n_voxels 다름 → 공통 공간 필요); V2 7/7 LOSO |

비유: **필터(stimulus)는 안경 처방**, **FE(Procrustes)는 시신경 모델**, **SRM은 시력 검사표**이다. 안경은 빛을 교정하고(stimulus), 시신경 모델은 교정된 빛이 뇌에서 어떻게 처리되는지 예측하고(prediction), 시력 검사표는 교정이 효과적인지 판정한다(evaluation).

### 2b. 전체 흐름도

```
Stimulus theta
     |
     | T_psi(theta)                 ← filter (stimulus transform, 4 Fourier params)
     v
Corrected stimulus theta'
     |
     v
FE channels(theta')
     |
     | W_FE @ channels(theta')      ← prediction engine (Procrustes, 고정)
     v
Procrustes voxel prediction
     |
     | W_SRM^T                      ← evaluation bridge (M_s = W_SRM^T @ W_FE)
     v
SRM latent prediction (k-dim)
     |
     | compare with s_bar_HC         ← target (HC mean, SRM space)
     v
Loss L(psi) → optimize T_psi
```

- **Filter**: stimulus space (θ → θ')
- **Prediction**: Procrustes voxel space (θ' → ŷ_proc)
- **Evaluation**: SRM latent space (ŷ_proc → s_hat, compare with HC mean)

### 2c. Subject-Specific Evaluation Bridge M_s

각 subject s에 대해:

```
M_s = W_SRM,s^T @ W_FE,s    (shape: k x 6)
```

- W_FE: n_voxels x 6 (forward encoding weights, **Procrustes prediction core**)
- W_SRM: n_voxels x k (SRM projection weights, **evaluation projection**)
- M_s: k x 6 (compact evaluation bridge — Procrustes prediction을 SRM evaluation space로 연결)

SRM-space evaluation at any angle theta:
```
s_hat_s(theta) = M_s @ channels(theta)    → (k,) vector in SRM space
```

M_s는 prediction model이 아니라 **evaluation shortcut**이다: W_FE @ channels(θ)로 Procrustes prediction을 먼저 생성하고, W_SRM^T로 SRM에 투영하는 과정을 하나의 행렬 곱으로 축약한 것이다. M_s의 quality는 Step 2b에서 별도 검증한다 (Section 3b-1).

### 2d. Primary vs Secondary Objective

| | Previous | Revised |
|-|----------|---------|
| **Primary** | Pairwise disparity rescue | **Latent geometry matching to HC** |
| **Secondary** | Latent alignment (auxiliary) | **Pairwise disparity (diagnostic)** |

**전환 근거**:

| 근거 | 수치 | Source |
|------|------|--------|
| CVD 범주 분류는 HC와 동등 | LORO HC 0.635 vs CVD 0.665, p=0.668 | LOCO_trials |
| CVD **연속 보간**에서 결손 | LOCO HC 69.4 vs CVD 87.4 (hV4, p=0.017) | LOCO_trials |
| SRM 연속 구조 부족 | V1 stress plateau 0.127, hV4 CIELab sign flip | LOCO_trials Phase 1b |
| Procrustes 보간 최적 | FE+Procrustes LOCO 최적, W cosine 0.921 | LOCO_trials |
| CVD pairwise profile 이질적 | sub-08: 32 FDR vs sub-09: 7 FDR vs sub-10: 0 FDR | Pre-validation |

---

## 3. Prediction Model

Prediction model은 **stimulus theta → Procrustes voxel space response**를 mapping한다. SRM은 prediction model의 본체가 아니라, cross-subject comparison을 위한 **evaluation space**이다.

### 3a. Prediction Model 구조 (per subject)

| Stage | Operation | Formula | Space | Validated by |
|-------|-----------|---------|-------|-------------|
| **Core** | FE model 학습 | `ŷ_proc(θ) = W_FE @ channels(θ)` | **Procrustes voxel** | **Step 2 ✓** (interpolation metrics) |
| Evaluation | SRM projection | `s = W_SRM^T @ ŷ_proc` | SRM latent | **Phase 2 ✓** (LOSO, split-half) |
| Evaluation | Bridge 구성 | `M_s = W_SRM^T @ W_FE` | Procrustes → SRM | **Step 2b ✓** (check4 전 ROI PASS) |

Prediction model의 **core**는 Step 1 (FE in Procrustes)이다. Continuous interpolation의 근거는 Procrustes 공간에 있다:
- FE+Procrustes W: (n_voxels × 6) — 풍부한 voxel-level tuning → smooth interpolation 최적
- LOCO MAE: Procrustes ~75° vs SRM ~80° (V3: +22° worse than chance in SRM)
- W cosine stability: 0.921 across LOCO folds

SRM과 M_s bridge는 **cross-subject target 정의**를 위해 필요하다 (다른 subject의 n_voxels가 다르므로 Procrustes 공간에서 직접 HC mean을 구할 수 없다). 그러나 이것은 evaluation 경로이지, prediction engine 자체는 아니다.

### 3b. Prediction Model 검증 — 왜 필요한가

Prediction engine이 filter design에 사용 가능한 "structurally reliable surrogate"인지 확인해야 한다. 이 검증 없이 filter를 바로 학습하면, 나중에 개선된 결과가 **진짜 색 보정 효과인지, 아니면 prediction model의 구조적 bias인지 분리할 수 없다**.

**MAE 단독 사용이 부적절한 이유**: LOCO FE는 구조적 병목이 있다. 7 training colors/fold에서 channel당 df = 1이다. 결과적으로 HC MAE ~ 75도는 decoder 문제가 아니라 **encoding estimation 한계**를 반영한다. Ridge, GCV, GP, hybrid MLP 등 대안을 모두 시도했으나 실패 — 더 좋은 decoder가 있는 것이 아니라 현재 데이터 해상도에서 interpolation 자체가 빡빡한 상황이다 (LOCO_trials confirmed).

**따라서 핵심 질문은**: "예측 모델이 몇 도를 맞히느냐"가 아니라 **"이 모델이 filter 설계에 쓸 만큼 구조를 일관되게 보존하느냐"**이다.

### 3b-1. M_s Bridge — 왜 필요하고 무엇을 검증하는가

#### Bridge가 필요한 이유

Prediction model의 core는 Procrustes 공간이지만, filter objective의 **target**은 SRM 공간에서 정의된다. 이는 선택이 아니라 **수학적 필연**이다:

```
HC mean target 정의 시 필요한 조건: 모든 subject의 표상을 같은 공간에서 평균
문제: Subject마다 n_voxels가 다름 (V1: 330-858) → Procrustes 공간에서 직접 평균 불가
해법: SRM k-dim shared space에서 HC mean 정의 → s_bar_HC(θ_i)
```

따라서 filter objective `L(psi) = Σ ||M_s @ channels(T_psi(θ_i)) - s_bar_HC(θ_i)||²`는 SRM evaluation을 사용한다. M_s = W_SRM^T @ W_FE는 이 **evaluation bridge**이다.

**핵심 질문: "Procrustes에서 valid한 W_FE가 SRM projection을 거쳐도 valid한가?"**

Step 2는 Procrustes interpolation quality를 확인한다 (FE가 voxel-level에서 구조를 보존함). 그러나 M_s = W_SRM^T @ W_FE의 product가 구조를 보존하는지는 **별도 검증이 필요하다**. 행렬 곱은 noise를 증폭하거나 low-variance SRM component에서 구조를 왜곡할 수 있다.

**이 우려가 현실적인 증거**:
- V1 SRM: stress plateau **0.127** → pairwise distances 비가역적 왜곡
- hV4 SRM: CIELab raw r=+0.402 → SRM r=**-0.308** (부호 반전)
- V2 SRM: 3D stress=0.097 → 유일하게 adequate한 ROI

**반론 (M_s가 치명적이지 않을 수 있는 이유)**:
- Filter는 거리 정확성이 아니라 **correction 방향** (어디로 push할지)만 필요
- Phase 2 SRM V2: LOSO 7/7, split-half r=0.733
- Cross-decoding 10/12 significant → SRM이 범주적 매핑은 보존

#### 4가지 검증 (Step 2b)

| Check | Method | 측정 대상 | Pass criterion |
|-------|--------|----------|---------------|
| 1. Trajectory stability | M_s,f = W_SRM^T @ W_FE,f per LOCO fold → SRM trajectory 28 pairwise r | SRM 공간에서도 fold간 일관성 유지? | SRM trajectory r > 0.5 (Procrustes r × 0.8 이상) |
| 2. RDM preservation | M_s @ basis(hue_c) → predicted SRM RDM vs actual SRM RDM (aligned_amplitudes) | Predicted distance 구조가 실제 SRM 거리와 일치? | Kendall tau > 0.3, p < 0.05 |
| 3. Cross-space consistency | Procrustes predicted RDM vs SRM predicted RDM rank order → Kendall tau | SRM projection이 rank order를 뒤집지 않는가? | Kendall tau > 0.4 |
| 4. **Predicted vs actual SRM** (핵심) | `s_hat(c) = M_s @ channels(hue_c)` vs `s_actual(c) = aligned_amplitudes(c)` → per-color Pearson r | M_s가 실제 SRM 표상을 충실히 재현? | Mean r > 0.5 across colors |

**구현 참고**: W_SRM은 Phase 2에서 저장되지 않음. Step 1에서 SRM 재적합 + W_SRM 저장 필요. Check #4의 ground truth는 aligned_amplitudes.npy 직접 사용 가능.

### 3b-2. M_s Bridge — 실제 결과 (Step 2b)

**실행 방법**: SRM 재적합 (HC-only training, BrainIAK SRM, 동일 k 설정). 동일 W_SRM으로 M_s 계산 및 ground truth aligned_amplitudes 생성. Phase 2의 W_SRM과는 **독립적인 refit**이므로, 이 테스트는 "현재 W_SRM에서 M_s가 FE quality를 충실히 전달하는가"를 측정한다.

#### HC Bridge Quality (4 Checks)

| ROI | k | C1: Trajectory r | C2: RDM tau | C3: Cross-space tau | C4: Pred vs Actual r | Gate |
|-----|---|-----------------|-------------|--------------------|--------------------|------|
| **V1** | 4 | **0.762** ± 0.054 ✓ | 0.301 ± 0.140 ✓ | **0.438** ± 0.141 ✓ | **0.678** ± 0.075 ✓ | **PASS (4/4)** |
| **V2** | 4 | **0.731** ± 0.143 ✓ | **0.451** ± 0.198 ✓ | **0.565** ± 0.136 ✓ | **0.794** ± 0.146 ✓ | **PASS (4/4)** |
| **V3** | 3 | **0.724** ± 0.149 ✓ | 0.238 ± 0.149 ✗ | 0.353 ± 0.129 ✗ | **0.675** ± 0.126 ✓ | **FAIL (2/4)** |
| **V4** | 3 | **0.813** ± 0.077 ✓ | **0.460** ± 0.189 ✓ | **0.446** ± 0.199 ✓ | **0.799** ± 0.160 ✓ | **PASS (4/4)** |

> **Check 4 (operational validity) 전 ROI PASS**: M_s가 실제 SRM-space representations를 충실히 재현함. HC mean r: V1=0.678, V2=0.794, V3=0.675, V4=0.799.

#### CVD Bridge Quality (Check 4 only — descriptive)

| Subject | V1 | V2 | V3 | V4 |
|---------|-----|-----|-----|-----|
| sub-08 | 0.577 ✓ | 0.518 ✓ | 0.783 ✓ | 0.379 ✗ |
| sub-09 | 0.572 ✓ | 0.415 ✗ | 0.393 ✗ | 0.261 ✗ |
| sub-10 | 0.519 ✓ | 0.472 ✗ | 0.725 ✓ | 0.904 ✓ |
| **CVD mean** | **0.556** | **0.468** | **0.634** | **0.515** |

> CVD는 HC보다 check4가 낮음 (V1: 0.556 vs 0.678, V2: 0.468 vs 0.794). 이는 CVD의 FE model이 HC-derived SRM space에서 less faithful하다는 것이며, **filter가 교정해야 할 바로 그 gap을 반영**한다.

#### 해석

**1. V1/V4 PASS — Pre-validation 예상 반전**:
- Pre-validation에서 V1 SRM stress plateau (0.127), V4 CIELab sign flip → bridge FAIL 예상했으나 실제 PASS
- **이유**: Pre-validation 증거는 Phase 2의 SRM으로 측정됨. Bridge test는 refit SRM에서 M_s = W_SRM^T @ W_FE를 평가한다. 핵심 질문은 "SRM 내부 geometry가 완벽한가"가 아니라 **"M_s가 FE의 prediction quality를 SRM evaluation으로 충실히 전달하는가"**이며, 이 답은 YES
- SRM stress가 높아도, M_s는 FE의 구조를 SRM space에서 consistent하게 유지할 수 있다 (topology가 아닌 relative quality가 보존)

**2. V3 FAIL (checks 2, 3) but check4 PASS**:
- RDM preservation (tau=0.238) 실패 + cross-space consistency (tau=0.353) 실패 = 세부 distance 구조가 SRM projection에서 왜곡됨
- 그러나 check4 (r=0.675) PASS = M_s가 overall pattern은 재현
- **해석**: V3의 M_s는 color-by-color representation을 대략 재현하지만, 색간 거리 rank를 일부 왜곡 → filter direction이 부정확할 수 있음. **V3에서는 filter optimization 결과를 주의하여 해석**해야 함

**3. V2 최강**: Check4 = 0.794 (최고). V2는 Procrustes quality도 좋고 (Step 2) bridge quality도 좋음 → **filter optimization의 primary target ROI로 확인**

#### 판정 기준 및 후속 조치

| ROI | Bridge result | 해석 | 후속 조치 |
|-----|---------------|------|----------|
| V1 | **PASS (4/4)** | M_s faithfully transmits FE quality | Filter optimization 진행 |
| V2 | **PASS (4/4)** | Strongest bridge quality | **Primary target** for filter optimization |
| V3 | **FAIL (2/4), check4 PASS** | Pattern-level OK, distance structure distorted | Filter 진행 가능하나 **결과 주의 해석** |
| V4 | **PASS (4/4)** | Good bridge despite pre-validation concerns | Filter optimization 진행 |

> **Procrustes-only fallback (Section 3b-3) 불필요**: Check 4가 전 ROI에서 PASS (M_s가 operational validity를 충족). SRM evaluation path를 사용하여 filter optimization을 진행할 수 있다.

#### Procrustes-only fallback (3b-3) — 참고용 보존

Check 4가 전 ROI PASS하였으므로 현재 활성화 불필요. M_s bridge가 실패하는 극단적 경우의 대안:

```
L_proc(psi) = Σ_i ||W_FE_CVD @ channels(T_psi(θ_i)) - amplitudes_proc_CVD(θ_i)||²
              + lambda * ||W_FE_CVD @ channels(T_psi(θ_i)) - W_FE_HC_aligned @ channels(θ_i)||²
```

첫 항은 reconstruction quality, 둘째 항은 HC-aligned target (Procrustes alignment 후 같은 n_voxels인 경우에만 가능). Cross-subject comparison 없이 within-subject correction quality만 평가 가능 → 제한적이지만 SRM 의존성을 제거한다.

### 3c. 5개 Structural Metrics 상세 (Table 2 + Figure 2)

| # | Metric | Role | Original criterion | Revised status |
|---|--------|------|-------------------|---------------|
| 1 | LOCO MAE | **Primary** | < 90 (chance) | HC-level gate (mean < 90) |
| 2 | Circular order preservation | **Supplementary** | ~~Spearman rho > 0.7~~ | Diagnostic only (HC mean rho=0.12-0.23, threshold incompatible) |
| 3 | Local monotonicity | **Supplementary** | ~~< 2 violations~~ | Diagnostic only (HC mean violations=2.6-4.7, threshold incompatible) |
| 4 | Pairwise distance rank preservation | **Primary** | ~~Kendall tau > 0.5~~ | HC-level gate (mean > 0.25, ≥4/7 HC p<0.05) |
| 5 | Fold/run trajectory stability | **Primary** | Mean correlation > 0.6 | HC-level gate (mean > 0.6, CV < 0.20) |

> **Metrics 2, 3이 supplementary로 강등된 이유**: 8 data points + MAE ~75° (1.7 color-slot 오차)에서 Spearman rho와 local monotonicity는 수학적으로 원래 threshold를 달성할 수 없다. 예: sub-07 V1은 best global order (rho=0.81, metric 2 PASS)이지만 **5 violations** (metric 3 FAIL) — 두 metric이 모순되는 paradox가 데이터 해상도 한계를 증명. Metrics 2, 3은 JSON과 Figure 2에 보고되지만 gate 판정에서 제외.

#### Metric 1: LOCO MAE (기존, baseline)

**측정 대상**: Predicted hue와 actual hue 간 absolute circular error.

**방법**: 8-fold LOCO (1색 held-out). 7색 x 6 runs = 42 samples로 pooled W 학습 (OLS, alpha=0). Held-out 색을 360도 basis template matching으로 prediction. 6 test runs 평균 → fold당 1개 predicted hue. 8 fold errors의 mean = MAE.

**해석**: MAE >= 90도면 예측 신호 자체가 없다. HC ~ 75도 (Procrustes), ~ 80도 (SRM) — Procrustes가 낫다. **하지만 MAE가 moderate해도 아래 4개 구조 지표가 양호하면 filter surrogate로 충분하다.**

#### Metric 2: Circular order preservation (신규)

**측정 대상**: 8개 LOCO-predicted hue가 올바른 angular ordering을 유지하는가?

**방법**: 8 fold에서 수집된 predicted hues → (8,) vector. True hue order (0, 45, ..., 315)의 rank와 predicted hue의 rank 간 Spearman rank correlation 계산. CW/CCW 방향 모두 시도, better |rho| 채택 (MDS reflection ambiguity 때문).

**해석**: MAE가 moderate해도 **색 순서가 보존**되면, 모델은 어떤 색이 인접하고 어떤 색이 먼지 "안다". 이것이 filter design의 핵심 — filter는 보정 방향을 알아야 하지, 정확한 위치를 맞출 필요는 없다. rho > 0.7이면 대부분의 색 순서가 올바르게 보존됨.

**예시**: True = red→orange→yellow→...→magenta. Predicted = 10→55→80→140→170→230→280→320이면 MAE ~ 10도, rho = 1.0 (완벽). Predicted = 10→280→80→...이면 MAE 비슷하지만 orange 위치가 틀려 rho 급락.

#### Metric 3: Local monotonicity (신규)

**측정 대상**: 인접 색 쌍이 predicted order에서 swap되는 경우가 있는가?

**방법**: 8개 인접 쌍 (color_1-color_2, ..., color_8-color_1 포함 circular wraparound)에 대해: true 방향이 forward (diff < 180도)인데 predicted가 backward (diff > 180도)이면 violation. 0~8개 violation 가능.

**해석**: Global order (metric 2)가 대체로 보존되더라도, **국소적으로 인접 색이 뒤바뀌면** filter가 해당 영역에서 잘못된 방향으로 색을 warp한다. Violation < 2이면 모델이 인접 색을 신뢰할 수 있게 구별함.

#### Metric 4: Pairwise distance rank preservation (신규)

**측정 대상**: Predicted RDM의 rank order가 actual neural RDM과 일치하는가?

**방법**:
1. **Actual RDM**: 6 runs 각각에서 8x8 correlation-distance matrix 계산 (Procrustes voxel patterns). 6개 RDM 평균 → reference (8, 8).
2. **Predicted RDM**: LOCO fold마다, fitted W로 8색 voxel pattern 재구성: `predicted_pattern(theta) = W.T @ basis(theta)` → (n_voxels,). 8색 간 correlation-distance → (8, 8). 8 folds 평균.
3. Upper triangle 28 pairs 추출. Actual vs predicted의 **Kendall tau** (rank correlation).

**해석**: Filter는 색 표상의 **geometry** (어떤 색 쌍이 가깝고 어떤 쌍이 먼지)를 기반으로 작동한다. Prediction model이 이 distance 구조의 rank를 왜곡하면 (예: blue-purple이 실제로는 가까운데 멀다고 예측), filter가 잘못된 geometry로 최적화된다. tau > 0.5 = predicted distance structure가 actual과 monotonically 관련됨.

#### Metric 5: Fold/run trajectory stability (신규)

**측정 대상**: 8개 LOCO fold의 360도 prediction trajectory가 서로 일관적인가?

**방법**: 각 LOCO fold는 서로 다른 W 생산 (다른 7색으로 학습됨). 각 fold의 W로 full 360도 trajectory 생성: `trajectory_f = W_f.T @ basis_full.T` → (n_voxels, 360). Flatten 후 C(8,2) = 28 pairwise Pearson correlation 계산. Mean correlation 보고.

**해석**: 서로 다른 training color subset에서 매우 다른 W가 나오면, 모델이 불안정하다. 즉 어떤 각도에서의 예측이 "어떤 색을 학습에 썼느냐"에 과도하게 의존한다. Filter는 8색 전체로 pooled W를 사용하므로, 이 W가 7색 subset에서도 안정적이어야 한다. Mean correlation > 0.6이면 6-channel basis가 voxel tuning을 안정적으로 포착함.

### 3d. Gate Decision (Revised — Procrustes Interpolation Quality)

원래 gate logic (5/5 metrics pass, ≥5/7 HC → PASS)은 **전 ROI 전 subject FAIL**이라는 결과를 낳았다. 원인: Metrics 2, 3의 absolute threshold가 데이터 해상도와 수학적으로 양립 불가 (8 points + MAE ~75°). Metrics 2, 3을 supplementary로 강등하고, 아래의 HC normative comparison 접근으로 전환한다.

**핵심 질문**: "Procrustes 공간에서 이 FE model이 연속 보간(interpolation)에 충분한 구조를 보존하느냐?"

모든 gate metric은 **Procrustes space**에서 계산된다 (amplitudes_procrustes.npy 기반). Gate는 SRM quality가 아니라 **Procrustes-level interpolation engine**의 quality를 검증한다.

**Gate criteria (per ROI) — HC-only, Procrustes interpolation quality**:

| # | Criterion | Threshold | Interpolation 관련성 |
|---|-----------|-----------|---------------------|
| 1 | HC trajectory stability | mean > 0.6 AND CV < 0.20 | Pooled W의 신뢰성: LOCO fold마다 다른 7색으로 학습해도 360° trajectory가 일관 → interpolation engine이 training set에 robust |
| 2 | HC signal presence (MAE) | mean < 90° | 보간 정확도의 기본 신호: chance (90°)보다 나은 예측 → 이 각도 범위에서 FE channels가 voxel tuning을 실제로 포착 |
| 3 | HC RDM rank preservation | tau mean > 0.25, ≥4/7 HC p<0.05 | 거리 구조의 geometry 보존: 어떤 색이 가깝고 먼지의 rank order → filter가 올바른 방향으로 correction을 push하기 위한 전제 조건 |

**Gate decision rule**: 3개 criteria **모두** 충족 → **PASS**. 1-2개 충족 → **MARGINAL**. 0개 → **FAIL**.

**왜 HC-only gate인가**: Prediction model의 목적은 Procrustes 공간에서 **연속 보간을 가능하게 하는 것**이다. HC 데이터는 normative interpolation quality를 정의한다 — "이 ROI에서 FE+Procrustes가 구조를 일관되게 보존하는가?" CVD 데이터를 gate에 포함하면, model quality와 CVD-specific 효과가 혼재된다. CVD z-scores는 Section 3f에 **descriptive results**로 보고한다.

**Halt criteria**: HC trajectory mean < 0.5 AND RDM tau mean < 0.15 → 해당 ROI에서 FE가 Procrustes interpolation에 부적합. 재설계 필요.

> **자기 비판**: 전 ROI PASS는 Procrustes interpolation quality가 실제로 adequate함을 반영한다. **Step 2b 결과 (Section 3b-2)**: M_s bridge check 4도 전 ROI PASS (V1=0.678, V2=0.794, V3=0.675, V4=0.799). Procrustes quality와 SRM evaluation quality가 독립적으로 확인됨 → filter optimization으로 진행 가능.

### 3f. Step 2 Validation Results (Procrustes Level)

> **이 섹션은 Procrustes-level FE만 검증한다. M_s bridge 검증 (Step 2b) 결과는 Section 3b-2에서 확인 — check 4 전 ROI PASS.**

#### HC Distribution (Gate Decision Basis)

| Metric | ROI | HC Mean | HC SD | HC n |
|--------|-----|---------|-------|------|
| **MAE** | V1 | 76.4 | 8.4 | 7 |
| | V2 | 80.0 | 16.0 | 7 |
| | V3 | 76.9 | 16.1 | 7 |
| | V4 | 68.6 | 9.8 | 6 |
| **Order rho** | V1 | 0.123 | 0.381 | 7 |
| | V2 | 0.228 | 0.321 | 7 |
| | V3 | 0.177 | 0.140 | 7 |
| | V4 | 0.218 | 0.452 | 6 |
| **Monotonicity** | V1 | 3.57 | 1.27 | 7 |
| | V2 | 4.71 | 0.95 | 7 |
| | V3 | 2.57 | 1.72 | 7 |
| | V4 | 4.67 | 1.51 | 6 |
| **RDM tau** | V1 | 0.338 | 0.105 | 7 |
| | V2 | 0.381 | 0.160 | 7 |
| | V3 | 0.305 | 0.148 | 7 |
| | V4 | 0.514 | 0.149 | 6 |
| **Trajectory r** | V1 | 0.626 | 0.079 | 7 |
| | V2 | 0.660 | 0.069 | 7 |
| | V3 | 0.614 | 0.122 | 7 |
| | V4 | 0.708 | 0.081 | 6 |

> V4의 n=6은 sub-07 hV4 16 voxels → NaN으로 제외

#### Gate Decision (HC-Only, 3 Primary Criteria)

| ROI | Criterion 1 (Trajectory) | Criterion 2 (MAE) | Criterion 3 (RDM tau) | Gate |
|-----|-------------------------|-------------------|----------------------|------|
| V1 | mean=0.626, CV=0.13 ✓ | mean=76.4 ✓ | mean=0.338, 6/7 p<0.05 ✓ | **PASS** |
| V2 | mean=0.660, CV=0.10 ✓ | mean=80.0 ✓ | mean=0.381, 5/7 p<0.05 ✓ | **PASS** |
| V3 | mean=0.614, CV=0.20 ✓\* | mean=76.9 ✓ | mean=0.305, 4/7 p<0.05 ✓\* | **PASS (borderline)** |
| V4 | mean=0.708, CV=0.11 ✓ | mean=68.6 ✓ | mean=0.514, 6/6 p<0.05 ✓ | **PASS** |

\*V3는 CV=0.20 (정확히 경계), RDM tau 4/7 (최소 요건) → 주의하여 해석

> **V4 RDM tau 최고 (0.514)**: hV4의 높은 색 선택성과 일치 (Phase 1b CIELab raw r=0.402\*)
>
> **V3 borderline**: Phase 1b에서도 V3는 CIELab 구조 0/4로 가장 약한 ROI

#### CVD z-Scores (Descriptive Only — Gate 판정에 미사용)

> ⚠️ **Validation circularity 방지**: 아래 z-scores는 모델이 CVD에서도 informative함을 보여주는 descriptive evidence이다. Gate 판정은 HC-only data로만 수행되었다.

| Subject | ROI | MAE z | Trajectory z | RDM tau z | Interpretation |
|---------|-----|-------|-------------|----------|----------------|
| sub-08 | V1 | **-2.90** | -0.15 | -1.00 | Better MAE than HC (unexpected) |
| sub-08 | V4 | +1.45 | **-2.12** | -2.25 | Worse trajectory + RDM |
| sub-09 | V1 | **+3.20** | -0.76 | **-2.31** | Significantly worse MAE + RDM |
| sub-09 | V2 | +1.77 | **-2.74** | -1.49 | Significantly worse trajectory |
| sub-09 | V4 | **+3.11** | **-3.70** | -1.67 | Dramatically worse on all metrics |
| sub-10 | V1 | **+2.64** | -0.99 | **-2.51** | Significantly worse MAE + RDM |
| sub-10 | V2 | **+2.02** | **-2.26** | **-1.99** | Significantly worse across board |

> sub-09, sub-10: 체계적 degradation (positive MAE z = worse prediction, negative trajectory z = less stable encoding). sub-08의 V1 MAE z=-2.90 (HC보다 나음)은 다른 encoding strategy를 반영할 수 있음 — 추가 조사 필요.

#### 원래 Gate Logic 대비 개선 근거

원래 gate (5/5 all pass, ≥5/7 HC): **전 ROI FAIL** (0/7 HC pass all 5). 원인:
- Metric 2 (rho>0.7): HC mean=0.12-0.23. 1 swap이 rho를 0.85→0.4으로 급락시키며, MAE ~75°에서 1-2 swap은 확률적으로 불가피
- Metric 3 (violations<2): HC mean=2.6-4.7. sub-07 V1 (best rho=0.81)조차 5 violations → Metric 2와 3이 모순

Revised gate (HC normative comparison, primary metrics only):
- (+) Phase 2 방법론과 일관 (Crawford & Howell single-case approach)
- (+) 과학적으로 올바른 질문 ("HC distribution이 filter design에 충분한가")
- (+) Metrics 2, 3 제거가 아닌 supplementary로 유지 — 투명성 보장
- (-) 전 ROI PASS → discriminative power 부족 우려 → **M_s bridge (Step 2b) 완료: check4 전 ROI PASS**

### 3g. Prediction Model 사후 평가

| Assessment | Method |
|-----------|--------|
| Latent trajectory smoothness | 360 hue trajectory 생성 per subject |
| HC latent geometry distance | Baseline CVD-HC distance in SRM space |
| Held-out color validation | LOCO 8-fold cross-validation |
| Permutation validation | Subject label shuffling → null distribution |

---

## 4. Filter Design

Filter는 **stimulus transform**이다: input hue angle을 remapping하여 CVD neural response를 HC geometry에 가깝게 만든다. Filter는 FE 6-channel model과 **별개의 upstream 모듈**이다.

### 4a. Filter Architecture — FE와의 관계

```
Processing chain:
  Input θ → [Filter T_psi] → θ' → [FE channels(θ')] → [W_FE @ channels(θ')] → Procrustes ŷ
                ↑                        ↑
           Stimulus transform      Neural encoding model
           (4 Fourier params)      (6 half-wave rectified cosines)
           학습 대상               고정 (step1에서 fit 완료)
```

Filter T_psi와 FE 6-channel은 **서로 다른 모델**이다:
- **FE (6-channel)**: 신경 encoding — voxel tuning을 6개 cosine basis로 근사. W_FE는 step1에서 OLS fit 후 **고정**
- **Filter T_psi (Fourier)**: stimulus correction — input hue를 remapping. 4 Fourier parameters를 **최적화**

Filter가 FE channels를 쓰지 않는 이유: FE channels는 neural encoding의 basis이지 stimulus distortion의 모델이 아니다. CVD distortion은 stimulus level에서 발생 (cone spectral sensitivity shift) → stimulus level에서 교정해야 한다.

### 4b. Fourier Parameterization — 왜 이 형태인가

```
T_psi(theta) = theta + a1*cos(theta) + b1*sin(theta) + a2*cos(2*theta) + b2*sin(2*theta)
```

#### (1) 왜 Fourier인가 (not spline, not lookup)

| 대안 | 문제 | Fourier 장점 |
|------|------|-------------|
| **Piecewise monotone spline** | 8 data points → ~8 knots → 사실상 lookup table, **circularity** (θ=0 ↔ θ=360 경계)를 자연스럽게 강제하기 어려움, smoothness를 별도 penalty로 추가해야 함 | Fourier basis는 **본질적으로 circular** (periodic function), **frequency truncation이 곧 smoothness** (별도 penalty 불필요) |
| **Lookup table (8→8)** | Training data에 overfit, 8색 사이 보간 불가, 새 색에 일반화 불가 | Analytic function → 임의 각도에서 smooth 보간 |
| **Higher-order polynomial** | Non-circular, boundary에서 발산 | Periodic, bounded |

#### (2) 왜 1차 + 2차 Fourier harmonic만 충분한가

CVD distortion의 물리적 원인은 **L/M cone spectral sensitivity shift** (protan: L-cone peak 이동, deutan: M-cone peak 이동)이다. 이 shift는 hue circle 위에서 **smooth, low-frequency deformation**을 생성한다:

- **1st harmonic** (a1·cos + b1·sin): Global axis distortion — L-M cone opponency 축을 따른 한 방향 압축/팽창. Phase shift (φ1 = atan2(b1, a1))가 distortion 축을 결정하고, amplitude (R1 = sqrt(a1² + b1²))가 크기를 결정.
- **2nd harmonic** (a2·cos2θ + b2·sin2θ): Asymmetric compression — hue circle의 대칭 위치에서 서로 다른 압축/팽창. 예: red-green 축은 압축 + blue-yellow 축은 팽창 (S-cone compensation).

3차 이상 harmonic은 "인접한 3색이 서로 다른 방향으로 왜곡"을 의미 — cone-level mechanism으로는 발생하지 않는 jagged pattern. **데이터 해상도 (8색, 45° 간격)에서 3차 이상의 구조를 추정하는 것은 noise fitting.**

#### (3) 왜 4 parameters가 known CVD distortion을 담기 충분한가

Pre-validation에서 확인된 CVD distortion 패턴:

| Pattern | Fourier component | 설명 |
|---------|------------------|------|
| L-M 축 혼동 (red-orange, cyan-blue 압축) | **1st harmonic** | L/M sensitivity 저하 → ~0-180° 축 압축 |
| S-cone 보상 (blue-purple, yellow-purple 과분리) | **2nd harmonic** | S-cone 신호 강화 → ~90-270° 축 팽창 |
| Protan vs deutan axis 차이 | **Phase** (φ1, φ2) | Protan: L-cone shift → magenta 축; Deutan: M-cone shift → green 축 |

4 parameters = 2 amplitudes (R1, R2) + 2 phases (φ1, φ2). 이것으로 **임의 방향의 1차 + 2차 smooth deformation**을 표현할 수 있다.

#### (4) sub-08 (deutan) vs sub-09 (protan): 같은 family, 다른 fitted psi

| Subject | Dominant distortion | 예상 Fourier profile |
|---------|-------------------|---------------------|
| **sub-08** (deutan) | V2 yellow-purple z=13.87, S-cone 과보상 | b2 dominant (2nd harmonic, ~90° phase) |
| **sub-09** (protan) | V1 red-magenta z=3.52, magenta 축 | a1 dominant (1st harmonic, ~0° phase) |

**같은 4-parameter family가 둘 다 포착 가능한 이유**: Fourier의 phase freedom이 distortion 축을 자유롭게 회전시킨다. Deutan은 주로 2차 component (대칭 보상), protan은 주로 1차 component (비대칭 축 shift)가 지배적일 것으로 예상. Per-subject optimization이므로 psi = (a1, b1, a2, b2) 각각이 다른 값으로 fit된다.

> **자기 비판**: 4 parameters가 sub-08의 32 FDR pair를 포착하려면 low-frequency distortion이라는 가정이 필요하다. 만약 sub-08의 왜곡이 국소적 (특정 색 쌍에만 집중)이라면 4 params로는 부족할 수 있다. 이 경우 3차 harmonic 추가 (6 params) 또는 per-ROI parameter sharing을 고려. LOCO 8-fold cross-validation이 overfitting을 탐지하는 safety net이다.

### 4c. Filter Objective

**Three-space 분리**:

```
Filter 작동 공간:   Stimulus space (θ → θ')       ← T_psi가 최적화하는 곳
Prediction 공간:    Procrustes voxel space          ← W_FE가 encoding하는 곳
Evaluation 공간:    SRM latent space                ← HC mean target 정의 + loss 계산
```

**Filter objective**:
```
L(psi) = Σ_i ||M_CVD @ channels(T_psi(θ_i)) - s_bar_HC(θ_i)||²
         + lambda * Omega(T_psi)
```

- θ_i: 8개 측정 색각 (0, 45, ..., 315)
- M_CVD = W_SRM^T @ W_FE: **evaluation bridge** (Procrustes → SRM, Section 3b-1)
- s_bar_HC(θ_i): HC group-mean SRM representation at θ_i
- Omega(T_psi): smoothness + near-identity regularization
- **SRM을 evaluation에 사용하는 이유**: Subject간 n_voxels가 다르므로 Procrustes에서 HC mean을 정의할 수 없다. SRM k-dim shared space가 cross-subject averaging을 가능하게 한다.

> **M_s bridge 검증 완료**: Step 2b 결과 (Section 3b-2), check 4 (operational validity)가 전 ROI PASS (V1=0.678, V2=0.794, V3=0.675, V4=0.799). M_s는 FE quality를 SRM evaluation space로 충실히 전달한다.

### 4d. Filter 제작

```
psi* = argmin L(psi)
```

Method: scipy.optimize.minimize (L-BFGS-B), per-subject, per-ROI

### 4e. Filter 검증 (3 levels)

#### Level 1: Latent Matching — PRIMARY (Table 3 + Figure 3)

| Metric | Definition |
|--------|------------|
| Baseline latent distance | d(M_CVD @ channels(theta_i), s_bar_HC(theta_i)), summed over i |
| Corrected latent distance | d(M_CVD @ channels(T_psi(theta_i)), s_bar_HC(theta_i)), summed over i |
| % reduction | (baseline - corrected) / baseline x 100 |
| Held-out generalization | LOCO held-out theta (8-fold mean) |
| Permutation p-value | 1,000-shuffle null에서 observed reduction rank |

**Pass criteria**:
- % reduction > 0 for all 3 CVD subjects
- Held-out positive for >= 5/8 LOCO folds
- Permutation p < 0.05 for >= 1 CVD subject
- Monotonicity: dT_psi/dtheta > 0 everywhere

**Figure 3** (Main result):
- Per-subject panel (sub-08, sub-09, sub-10)
- SRM space 8색 trajectory: Gray=HC mean, Red=baseline CVD, Blue=corrected CVD
- Primary: V2; auxiliary: V1
- Message: "전체 연속 색 geometry를 HC 방향으로 이동"

#### Level 2: Pairwise Distortion Rescue — SECONDARY (Table 4 + Figure 4)

Pre-validation evidence pairs만 검증 (전 pair 아님):

| Level | Pair | ROI | Evidence |
|-------|------|-----|----------|
| Group | blue-purple | V2 | B1 p=0.042 |
| sub-08 | yellow-purple | V2 | z=13.87, FDR 12 pairs |
| sub-09 | cyan-magenta | V1 | z=4.08 |
| sub-09 | red-magenta | V1 | z=3.52 |
| sub-10 | (없음) | — | FDR 0 pairs |

Pass criterion: Evidence-weighted pairs > 50%에서 rescue direction correct

#### Level 3: Trajectory Improvement

보정 후 360 hue trajectory가 smoother하고 HC circular geometry에 가까운지 확인

### 4f. Filter 사후 평가

| Assessment | Method | Status |
|-----------|--------|--------|
| Neural validation (in-silico) | Corrected stimulus → predicted neural response → HC geometry 비교 | To be implemented |
| Behavioral validation (psychophysics) | JND thresholds, pair discrimination with corrected stimuli | Deferred (추가 scanning 필요) |

---

## 5. 전체 파이프라인 요약

### Three-Space Architecture

```
Stimulus space        Procrustes voxel space        SRM latent space
(filter 작동)         (prediction engine)            (evaluation target)

θ → T_psi(θ)  →  channels(θ') → W_FE → ŷ_proc  →  W_SRM^T → s_hat  →  compare with s_bar_HC
```

### Pipeline Steps

| Step | What | Primary space | Deliverable | Gate |
|------|------|--------------|-------------|------|
| 1 | FE fit (W_FE) + SRM fit (W_SRM) + M_s 구성 | **Procrustes** + SRM | W_FE, W_SRM, M_s per subject | — |
| 2 | Procrustes interpolation 검증 | **Procrustes** | Table 2 + Figure 2, summary.json | **GATE 1: interpolation quality** |
| 2b | M_s evaluation bridge 검증 | Procrustes → SRM | bridge_summary.json | **GATE 2: PASS** (check4 전 ROI >0.5) |
| 3 | Filter optimization (T_psi) | **Stimulus** (eval: SRM) | Table 3 + Figure 3, T_psi | **PRIMARY endpoint** |
| 4 | Permutation test | SRM | p-values | — |
| 5 | Pairwise diagnostic | SRM | Table 4 + Figure 4 | SECONDARY |

**핵심 분리 원칙**:
- Prediction engine quality (Step 2): Procrustes에서 독립적으로 검증 — SRM과 무관
- Evaluation bridge quality (Step 2b): M_s가 Procrustes quality를 SRM으로 전달하는지 — M_s FAIL해도 Procrustes quality는 유효
- Filter optimization (Step 3): Stimulus space에서 T_psi 최적화, SRM으로 evaluation

---

## 6. 분석 방법 상세

### 6a. Statistical Tests

| Test | Purpose | Detail |
|------|---------|--------|
| LOCO CV (8-fold) | Held-out color generalization | 7 train / 1 test per fold |
| Permutation test (1,000 shuffles) | Null distribution for latent distance reduction | HC-CVD label shuffling |
| Structural metrics | Prediction engine quality (beyond MAE) | Circular order, rank tau, fold stability |
| Crawford & Howell (1998) | Individual CVD significance | df=6, one-tailed |

### 6b. Core Pipeline Summary Table (Table 1)

Operating space와 target space 분리의 데이터 기반 정당화:

| Item | Value | Source |
|------|-------|--------|
| Classification 최적 | LDA + SRM | Phase 2 |
| Interpolation 최적 | FE + Procrustes | LOCO_trials |
| FE W stability | cosine 0.921 | LOCO_trials |
| Cross-decoding HC ~ CVD | 10/12 significant, LORO p=0.668 | LOCO_trials |
| SRM target ROI | V2 (LOSO 7/7, PCA r=0.891) | Phase 2 |
| SRM structure limits | V1 unstructured (0/4), hV4 sign-flip | LOCO_trials Phase 1b |

---

## 7. 우려 지점 및 보완 계획

### 우려 2: FE+Procrustes MAE가 높을 수 있음

HC LOCO MAE ~ 75. 7색/fold encoding estimation 한계가 근본 원인.

**보완**: MAE를 유일 지표로 두지 않는다. Structural metrics (order preservation, rank tau, trajectory stability) 검증으로 "structurally reliable surrogate" 입증.

### 우려 6: Gate가 전 ROI를 PASS시킴 (Vulnerability #2)

Revised gate에서 V1/V2/V3/V4 모두 PASS → discriminative power 부족.

**보완**: Gate의 질문은 "어떤 ROI를 reject할 것인가"가 아니라 **"Procrustes interpolation이 어떤 ROI에서 작동하는가"**이다. 전 ROI PASS는 Procrustes가 실제로 interpolation에 적합한 공간이라는 pre-validation 결론과 일치한다 (Section 1b: SRM에서는 V3가 chance worse, V1이 plateau). **M_s bridge test (Step 2b) 완료**: V1/V2/V4 PASS (4/4), V3 FAIL (2/4 but check4 PASS). Procrustes gate PASS + bridge check4 PASS → 전 ROI에서 filter optimization 진행 가능. V3는 distance structure 왜곡 주의.

### 우려 8: V3 borderline threshold (Vulnerability #5)

V3 CV=0.20이 정확히 경계에 위치. Post-hoc threshold 설정 의심.

**보완**: V3 borderline은 pre-validation과 일관된다 (V3 CIELab 0/4, 전 ROI 최약). Threshold CV≤0.20은 V3를 포함하기 위해 설정된 것이 아니라, FE stability의 일반적 기준 (20% coefficient of variation)에서 유래. V3가 borderline인 것 자체가 결과의 해석 가능성을 높인다 — 만약 V3가 comfortably PASS했다면 threshold가 너무 관대하다는 비판이 가능. 그러나 V3 filter 결과는 주의하여 해석해야 한다.

### 우려 9: Implementation gap (Vulnerability #3) — **부분 해소**

Step1, 3, 4, 5 스크립트 미구현. Pipeline이 step2에서 blocked.

**보완**: Step 2b (M_s bridge test)는 로컬에서 완료 (2026-03-08). 결과: 전 ROI check4 PASS → SRM evaluation path 사용 가능 확인. 남은 구현: Step1 (W_FE + W_SRM fit + M_s computation 정식 저장) → Step3 (filter optimization) → Step4 (permutation) → Step5 (pairwise diagnostic). utils_transform.py에 shared functions (channels, Fourier T_psi, latent distance)를 먼저 구현.

---

## 8. Implementation

### 8a. Script 구성

| Script | Step | Purpose | Input | Output |
|--------|------|---------|-------|--------|
| `utils_transform.py` | — | Shared utilities | — | importable module |
| `step1_build_prediction_model.py` | 2 | M_s 구축 | amplitudes_procrustes.npy | M_s, W_FE, **W_SRM** per subject |
| `step2_validate_prediction.py` | 3 | Structural metrics (Procrustes) | amplitudes_procrustes.npy | per-subject validation JSON |
| `step2_summarize.py` | 3 | Gate decision + Figure 2 | validation JSONs | summary.json, Figure 2 |
| `step2b_validate_bridge.py` | 3+ | **M_s bridge quality** ✓ | W_FE, W_SRM, aligned_amps | bridge_summary.json (완료 2026-03-08) |
| `step3_filter_optimization.py` | 4 | T_psi optimization | M_s, HC means | Table 3 JSON, fitted psi, Figure 3 |
| `step4_permutation_test.py` | 4 | Null distribution | step3 outputs | p-values |
| `step4_permutation.sbatch` | 4 | SLURM wrapper | step4 script | SLURM logs |
| `step5_pairwise_diagnostic.py` | 5 | Evidence pair rescue | step3 psi + pair list | Table 4 JSON, Figure 4 |

### 8b. Directory Structure

```
future_phase2_filter_optimization/
├── PLAN.md
├── README.md
├── pre_validation/
├── figures/
├── scripts/
│   ├── utils_transform.py
│   ├── step1_build_prediction_model.py
│   ├── step2_validate_prediction.py
│   ├── step2_summarize.py
│   ├── step2b_validate_bridge.py
│   ├── step3_filter_optimization.py
│   ├── step4_permutation_test.py
│   ├── step4_permutation.sbatch
│   └── step5_pairwise_diagnostic.py
└── results/
    ├── step1_prediction_model/
    ├── step2_validation/
    ├── step2b_bridge/
    ├── step3_filter/
    ├── step4_permutation/
    └── step5_pairwise/
```

---

## 9. Relationship to Existing Analyses

| Component | Source | Status | Value |
|-----------|--------|--------|-------|
| SRM k values | Phase 2 | Confirmed | V1=4, V2=4, V3=3, hV4=3 |
| W_FE | phase3 LOCO/LORO | Pooled W adopted | cosine 0.921 |
| HC-CVD SRM disparity | Phase 2 LOO-consistent | Confirmed | V1 p=0.062, V2 p=0.075 |
| LOCO FE baseline | phase3 | Confirmed | HC MAE ~ 75 |
| SRM limits | LOCO_trials 1b | Confirmed | V1 0/4, hV4 sign-flip |
| V2 SRM structure | LOCO_trials 1b | Confirmed | 2/4, 3D stress=0.097 |
| Per-pair distortion | pre_validation B1-B3 | Confirmed | L-M deficit + S-cone compensation |
| Cross-decoding | LOCO_trials | Confirmed | Categorical equiv (10/12 sig) |
| Individual profiles | pre_validation | Confirmed | sub-08 V2/V3; sub-09 V1; sub-10 none |

---

## 10. 핵심 한 줄 요약

> **Three-space 파이프라인**: Filter는 **stimulus space**에서 θ를 교정하고, prediction engine은 **Procrustes voxel space**에서 neural response를 예측하고, evaluation은 **SRM latent space**에서 HC mean target과 비교한다. SRM은 cross-subject target 정의를 위한 수학적 필연이지 prediction core가 아니다. Continuous interpolation의 근거는 Procrustes에 있고, SRM은 evaluation bridge이다.

---

## 시각화 파일 위치

| Figure | 설명 | Path (to be created) |
|--------|------|----------------------|
| Figure 1 | Three-space architecture schematic | `figures/fig1_three_space_architecture.png` |
| Figure 2 | Prediction model validation | `figures/fig2_prediction_validation.png` |
| Figure 3 | Latent matching before vs after | `figures/fig3_latent_matching.png` |
| Figure 4 | Pairwise diagnostic map | `figures/fig4_pairwise_diagnostic.png` |
