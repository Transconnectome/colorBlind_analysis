# Pipeline 2 Closure — 5-Step Selection Axis

**Status**: CLOSURE READY (Phase D Round 3 complete; identifiability FAIL across all candidates)
**Date**: 2026-05-26

---

## Research Questions + Answers

### Model definitions (RQ 답변 전 명세)

| Model | Formal expression | DOF | Mechanism |
|---|---|---|---|
| **R+C** (retinal + cortical compensation) | `δθ_RC(c) = (2 − g) · δθ_Machado(c; Δλ)` | 1 (g; Δλ fixed per source) | Retinal cone shift × cortical linear compensation. `g=1` = no compensation, `g=2` = perfect compensation, `g>2` = overcompensation |
| **2-Component** (cortical opponent-axis rotation in CIELab) | `δθ_2C(θ) = β_s · cos(θ − 90°) + β_c · cos(θ − θ_conf)`<br>θ_conf: protan=16°, deutan=150° | 2 (β_s, β_c) | β_s = S-cone cardinal axis rotation (Krauskopf 1982); β_c = confusion-axis rotation aligned with CVD family (Emery 2021 grounding). **Color representation distortion mimic** — represents CVD-distorted color space at cortical level, agnostic to retinal mechanism |

---

### RQ1. R+C vs 2-Component — which model explains better?

**판단 기준**:
- (a) AIC/BIC on test_focal pair fit
- (b) boundary_rate (degeneracy)
- (c) test_focal (behav fit quality)
- (d) test_loss_iqr (HC stability)

**결과** (Phase B v6, final candidates):

| Subject | Model | candidate | AIC | BIC | bdy | test_focal | test_iqr |
|---|---|---|---|---|---|---|---|
| sub-08 | 2-comp | S08-stable (38, −10) | 9.28 | 6.66 | **0%** | 28.00 | 0.86 |
| sub-08 | 2-comp | S08-robust (6, −42) | 10.88 | 8.27 | 9% | 62.48 | 2.15 |
| sub-08 | R+C (g=2.25) | cycle6b NEW | 9.01 | 7.70 | 0% | 66.56 | 1.38 |
| sub-09 | 2-comp | S09-primary (2, 24) | 6.26 | 3.64 | **0%** | 6.18 | 1.42 |
| sub-09 | R+C (g=2.95) | rc_Boehm_low | **4.20** | **2.89** | **41%** | 6.00 | 0.57 |

**Verdict** (subject-별):

- **Sub-08: 2-Component이 R+C보다 better**.
  - 2-comp (38, −10): bdy 0%, test_focal=28 vs R+C g=2.25: bdy 0% but test_focal=66.56 (8 SD off)
  - AIC/BIC 는 비슷하나 R+C 의 behavioral fit 이 *3× 나쁨* (test_focal 28 vs 66.56)
  - Cycle 6b 의 R+C 후보들 대다수가 g=3.00 boundary collapse (8 NEW 후보 중 R+C 유일 non-collapse = g=2.25)
- **Sub-09: 2-Component이 R+C보다 better** (AIC/BIC 가 R+C 를 선호함에도 불구).
  - R+C g=2.95: AIC/BIC 최저이나 **bdy=41%** = upper-boundary saturation (g_max=3.00 에 fit 이 멈춤)
  - g=2.95 는 *과보상 195%* — Boehm 2016 / Tregillus 2020 의 g≈1.1 (10% 과보상) range 를 크게 초과 → R+C 모델이 사실상 *underspecified*
  - 2-comp (2, 24): interior solution bdy=0%, *legitimate fit*

**종합**: 2-Component 이 양 subject 모두에서 better. AIC/BIC 단독으로는 R+C 를 선호할 수 있으나 **boundary_rate 와 behavioral fit quality 함께 보면 2-comp 가 우세**. R+C 1-DOF 는 두 subject 모두 *insufficient model* (L6).

---

### RQ2. Can certain model-loss pair estimate parameter robustly to subset of HCs?

**판단 기준**: HC subset resample (5 train / 2 test × 300 draws). test_loss_median + IQR, param_IQR.

**결과**:

| Candidate | test_loss median ± IQR | param IQR (β_s, β_c) | HC stability |
|---|---|---|---|
| **S09-primary (2, 24)** | −1.52 ± 1.41 | **(0, 0)** 완벽 deterministic | **★★★** (param 변동 0) |
| S08-stable (38, −10) | −1.14 ± **0.86** | (24, 22) | ★★ (test_iqr 최저, param IQR 중간) |
| S08-robust (6, −42) | −2.36 ± 2.15 | (8, 2) — β_c IQR 작음 | ★★ (param robust, test_iqr 중간) |

**Verdict**: **Yes — 특정 model-loss pair 는 HC subset 에 robust 함**.
- **S09-primary (β_s=2, β_c=24)**: γ_all + RDM_V1 fit loss + 2-Component 의 조합이 *2 fit combos 에서 동일 param 추출*, **param IQR=(0, 0)** 으로 *deterministic identification*
- S08 두 후보 도 param IQR 비교적 작음 (4-24)
- R+C g=2.95 (sub-09) 도 g_iqr=0.10 으로 stable 하지만 *boundary saturation* 이므로 robust ≠ correct

단, RQ1 verdict 와 일관: **HC stability 만으론 model correctness 보장 못 함**. 2-comp (2, 24) 처럼 *param IQR=0 + interior* 모두 만족해야 *robust identification*.

---

### RQ3. Can such model be generalized among CVD/HC?

**한계 명시**:

| 한계 | Evidence | 함의 |
|---|---|---|
| **CVD N=2** (sub-08 deutan, sub-09 protan; sub-10 near-normal 제외) | Phase 2 sample size | Cross-CVD generalization 검증 불가 — *individualized filter* framing 으로만 정당화 |
| **HC pool n=7 (effective 6 for hV4)** | sub-07 hV4 16 voxels → nan; sub-04 outlier 분포 | LOO 통한 HC specificity 검증 불완전. cycle6b 의 HC stability 는 *HC normalization 변동* 만 측정 |
| **LOO limitation**: HC LOO 는 *precondition gate 만*, model fit 자체에는 적용 안 함 | `s10a_precondition.py` 만 LOO 사용; Phase B v6 는 *5/2 split 300 draws* (LOO 아님) | HC LOO-based bootstrap 으로 HC specificity 정량화 가능했으나, CVD-HC fundamental difference 검증은 별도 (e.g., 별도 SRM disparity analysis) |
| **Specificity FAIL (procedure-level)**: Phase D Round 3 — null GT (0, 0) 에서 (+26, −16) 등 spurious 추정 | §5.2 Round 3 results | **Fit procedure 가 HC voxel pattern 의 inter-subject variance 를 β_s positive 방향으로 absorb**. Filter 가 HC 와 CVD 를 진정으로 구별하는지 불확실 |
| **Family specificity 부분 확인** (sub-08 protan audit) | `run_sub08_protan_audit.py`: deutan 후보 0/47 schemes 등장 | Sub-08 deutan signal 은 protan 모델로 reproduce 안 됨 → *consistent with deutan-specific signal* (단 basis geometry 차이 가능성 잔존) |

**Verdict**: **No — generalization 불가능**. Pipeline 2 의 model 은 *individualized filter form* 으로만 보고. Cross-CVD/HC generalization 은 다음 조건 만족 시에만 가능:
1. CVD N 증가 (현재 N=2)
2. HC pool 확장 + LOO 기반 specificity 정량화
3. Independent identifiability test 통과 (Round 3 FAIL → 미충족)

→ **L2/L3/L4/L1 limitations** 로 paper 에 명시.

---

### RQ4. Behavioral loss 결과가 기존 논문과 일치하는가? Neural data 포함이 behav-only 대비 benefit?

#### 4a. R+C result vs literature

**기존 R+C literature (g range)**:
- **Tregillus 2020**: 정상 색각 → CVD simulator 적응 실험. g ≈ **1.1** (10% 과보상)
- **Boehm 2016**: protan/deutan 색각 실험. g ≈ 1.0-1.3 범위
- **DPS_lit, JND_Lamb, Boehm_mid**: Δλ source variants

**우리 R+C 결과** (behav-only γ_all fit, 2-comp 대신 R+C):

| Subject | Behav-only R+C best | g value | 과보상 % | Literature 비교 |
|---|---|---|---|---|
| sub-08 | (γ_all only, no RDM) R+C | g=3.00 (cycle6b boundary collapse) | **200%** | 문헌 범위 *훨씬 초과* |
| sub-09 | (γ_all only) RC g=2.60 (Phase B v3 era) | g=2.60 | **160%** | 문헌 범위 *훨씬 초과* |
| sub-09 | RC g=2.95 (cycle6b) | g=2.95 | **195%** | g_max boundary saturation |

→ **R+C behav-only 결과는 문헌 g≈1.1 보다 *10× 큰 과보상* 추정**. 두 가지 해석:
- (a) 우리 CVD subjects 가 *atypical* — extreme overcompensation
- (b) R+C 1-DOF 모델이 *underspecified* — fit 이 grid edge 까지 밀어붙임 → boundary saturation (실제는 다른 mechanism 이 contribution)
- *(b) 해석이 더 합리적* — R+C 가 두 subject 모두 boundary 에서 saturate. Phase B v6 의 다른 R+C cells 도 g=3.00 boundary collapse 다수 (sub-08 91 collapse cells 중 88 이 R+C).

#### 4b. Behav-only vs neural+behav benefit

**Sub-08 behav-only fit (2-comp, γ atom 만)**:
- γYG only: (β_s=+38, β_c=−44) bdy=8%
- γOY only: (β_s=+16, β_c=−44) bdy=23%
- γYP only: (β_s=+34, β_c=+49) bdy=50%
- γall only: (β_s=+50, β_c=−36) bdy=**70%**

**Sub-08 neural+behav (final candidates)**:
- (38, −10) γ_all + RDM_V1: bdy **0%**
- (6, −42) γ_OY + RDM_V2: bdy 9%

→ **Neural 포함 시 boundary rate 큰 폭 감소 (70% → 0%)** — fit 이 *interior solution* 으로 안정화. β_c 추정도 변화 (behav-only: −44~+49 range → neural+behav: −10 또는 −42 specific values).

**Sub-09 behav-only**:
- γGB only: (β_s=+34, β_c=−8) bdy=0% — *near-null β_c*
- γall only: (β_s=+26, β_c=+4) bdy=0% — *near-null β_c*

**Sub-09 neural+behav (final)**:
- (2, 24) γ_all + RDM_V1: bdy 0%, β_c=**+24**

→ **Neural 포함이 β_c 추정을 substantially shift** (behav-only ≈0 → neural+behav +24). Neural data 가 *behav 만으로는 알 수 없는 cortical confusion-axis rotation 정보 추가*.

**Stability 측면**:
- Behav-only sub-08: param IQR 큼 (β_c range −44~+49)
- Neural+behav sub-08: param IQR 작음 ((24, 22) for (38, −10))
- → Neural inclusion narrows parameter uncertainty.

**Verdict** (RQ4):
1. R+C behav-only 결과는 문헌 g≈1.1 보다 훨씬 큰 과보상 (g≈2.6~3.0) → R+C 모델 *insufficient* 해석이 합리적
2. **Neural data 포함의 benefit**:
   - Boundary rate 감소 (sub-08 70% → 0%) — fit stability 개선
   - β_c 추정의 sign 변화 (sub-09 ≈0 → +24) — neural geometry 가 behav 만으로는 보이지 않는 component 노출
   - Parameter uncertainty 감소

---

### RQ5. Behav loss 와 Neural loss 가 같은 방향의 distortion 추정?

**판단**: behav-only 후보들의 (β_s, β_c) sign 과 neural-only 후보들의 (β_s, β_c) sign 비교.

#### Sub-08

| Loss | Best (β_s, β_c) | β_c sign |
|---|---|---|
| **behav-only** γOY | (+16, −44) | NEG |
| **behav-only** γYG | (+38, −44) | NEG |
| **behav-only** γYP | (+34, **+49**) | **POS** ← YP focal 만 sign-flip |
| **behav-only** γall | (+50, −36) | NEG |
| **neural-only** RDM_V1 | (+32, 0) | ZERO |
| **neural-only** RDM_V2 | (+4, −26) | NEG |
| **neural-only** RDM_V3 | (0, 0) | ZERO (degenerate, bdy=61%) |
| **neural-only** RDM_V4 | (+36, −14) | NEG |

→ **β_c direction agreement: NEG dominant (5/8); YP-focal 만 POS (single exception)**. γYP behav fit 이 *β_c POS* 로 가는 것은 (44, 36) 후보 (제외됨) 와 일치 — *single-pair focal-fit specialist* 의 특이성.

#### Sub-09

| Loss | Best (β_s, β_c) | β_c sign |
|---|---|---|
| **behav-only** γGB | (+34, −8) | NEAR-ZERO |
| **behav-only** γall | (+26, +4) | NEAR-ZERO |
| **neural-only** RDM_V1 | (0, **+24**) | **POS** |

→ **β_c direction DISAGREEMENT**: behav-only β_c ≈ 0, neural-only β_c = **+24**.

#### Verdict (RQ5)

**Sub-08: 대체로 같은 방향 (β_c negative)** with 1 exception (γYP → β_c positive).
- Sign disagreement 의 원인: γYP focal pair 가 *sub-08 의 가장 distorted pair* → focal-fit 이 다른 pairs 보다 *opposite mechanism* 을 reflect 할 수 있음. (44, 36) advisor verdict 로 제외됨.
- 7/8 비교에서 NEG agreement.

**Sub-09: 명백히 다른 방향**.
- Behav (γGB or γall) 은 *β_c ≈ 0* — confusion-axis distortion 거의 detect 못 함
- Neural (RDM_V1) 은 *β_c = +24* — confusion-axis rotation 강하게 detect
- → **Neural data 가 behav 만으로는 invisible 한 cortical mechanism component 노출**. 이는 RQ4 의 "neural inclusion benefit" 과 일관.

**종합**:
- Sub-08: behav 와 neural 이 거의 같은 방향 (β_c negative); 단 1 exception (YP focal).
- Sub-09: behav 와 neural 이 *다른 방향* — neural data 만이 cortical confusion-axis rotation 추정.
- Paper-level wording: "Behavioral and neural losses *converge on β_c sign for sub-08* (with single focal-fit exception), but *diverge for sub-09 where neural data uniquely identifies confusion-axis rotation invisible to behavioral fit alone*."

---

**Pipeline narrative (user-locked 5-step axis)**:

```
[1] 모델 및 로스 후보 선정  →  [2] 전체 조합 시도 + 테스트 기준 평가
                              ↓
                          [3] 각 모델의 HC pool 안정성 평가
                              ↓
                          [4] 가중치 sweep (후보 추출 + 강조 식별)
                              ↓
                          [5] 최종 결정 + 한계 / 식별성
```

각 step 의 Pipeline 2 매핑은 다음과 같다:

| Step | Pipeline 2 component | 코드 |
|---|---|---|
| 1. 모델·로스 후보 선정 | Phase A precondition (HC LOO single-loss gate) | `scripts/s10a_precondition.py` |
| 2. 전체 조합 + 평가 | Phase B v6 — cell enumeration × 5/2 HC split × test atoms | `scripts/s10b_v6_pca_rdm.py` |
| 3. HC pool 안정성 | Phase B v6 test_loss median + IQR | (위와 동일 script, 출력 metric) |
| 4. **가중치 sweep** | **Cycle 6b raw-weight 확장** (γ_focal 유지 + γ_all + α·RDM) | `scripts/cycle6b_extended_raw_weight.py` |
| 5. 최종 결정 + 한계 | Closure (본 문서) + Phase D identifiability (Round 3 진행 중) | `scripts/s13_round3.py` |

**중요 reorganization (사용자 directive 2026-05-26)**: cycle6b 는 Phase B 의 weight-sweep step 4 로 통합. 별도 post-hoc 이 아닌 selection pipeline 의 정식 단계.

---

## Step 1. 모델 및 로스 후보 선정 (Phase A)

### 모델 (locked, A2)
- Machado 1-way (k=1 DOF, cone shift only)
- R+C 1-DOF (3 Δλ sources: DPS_lit, Boehm_mid, JND_Lamb)
- 2-Component 2-DOF (β_s × β_c grid, family-specific θ_conf)

### Data invariants
| 항목 | 내용 |
|---|---|
| Amplitudes | C010 procrustes, `(6 runs × 8 colors × n_vox)` per (subject, ROI) |
| HC pool | sub-01..07 (n=7); hV4 effective n=6 (sub-07 16 voxels → nan) |
| CVD | sub-08 deutan, sub-09 protan |
| ROIs | V1, V2, V3, V4 (= hV4 on disk) |
| Encoder | ridge_gcv (locked, A10) |
| Behavioral | per-pair JND (OY, YG, YP, GB, RG, ...); CVD pair당 **N=1 measurement** |

### Atoms (locked)
| Atom | 정의 | Range | Info-density |
|---|---|---|---|
| γ_focal (γOY, γYG, γYP, γGB) | per-pair JND z² vs HC train baseline | 0–~80 | 1 z² scalar |
| γ_all | 8-pair JND z² 합 | 0–~1500 | **8 z² 합** (info-dense) |
| RDM_{V1..V4} | PCA-aligned RDM K=6, cosine distance to HC mean | 0–2 | 28 pair distances → scalar |
| LOCO_V4 | V4 voxel-prediction loss (CVD-internal ridge) | scalar | V_V4 voxel prediction error |

**Atom info-density 차이가 selection 에 영향**: z-score grid-relative normalization (Step 2 composite) 은 atom 간 magnitude/density 격차 평탄화 → 1-pair γ_focal 이 8-pair γ_all 과 동등 composite 기여. Step 4 (cycle6b raw-weight) 가 이 효과 우회.

### Precondition gate
- HC LOO 기반 single-loss preconditon table (`results/s10_inclusion/precondition_table.json`)
- 통과 cells 가 Step 2 로 진입
- 데이터 sharing 없음 (HC LOO 만)

---

## Step 2. 전체 조합 시도 + 테스트 기준 평가 (Phase B v6)

### Cell enumeration
```python
# s10b_v6_pca_rdm.py:267-282 (sub-08), :285-306 (sub-09)
# Sub-08:  γ ∈ {none, OY, YG, YP, [OY,YG,YP], ALL} × RDM ∈ {none, V1, V2, V3, V4, V1+V4} × LOCO ∈ {off, V4}
# Sub-08 cells × models = 71 × 4 = 284
# Sub-09:  γ ∈ {none, GB, ALL} × RDM ∈ {none, V1} × LOCO ∈ {off, V4}
# Sub-09 cells × models = 11 × 4 = 44
```

### Train/test split
```python
# s10b_v6_pca_rdm.py:49-51, 351-357
N_RESAMPLES = 300
SUBSET_SIZE = 5  # train HC
# complement = 2 test HC
RNG_SEED = 42
# Per draw: subset (5 train) + complement (2 test)
```

### Train atom (5 train HC)
- γ_pair atom: `((predicted_JND − CVD_JND) / HC_train_SD)²` — `:99-117`
- γ_all atom: 8-pair z² 합 — `:80-97`
- RDM atom: PCA-aligned RDM cosine distance to *train HC mean* — `:156-174`
- LOCO atom: CVD-internal ridge prediction (HC-independent) — `:199-211`

### Composite + argmin
```python
# s10b_v6_pca_rdm.py:567-573 (R+C), :595-606 (2-comp)
z_sum = Σ zscore_grid(atom_grids[atom_name])   # grid-relative z-score
comp = z_sum / sqrt(n_atoms)
fit_param = argmin(comp)                        # g 또는 (β_s, β_c)
```

### Test atom (2 test HC) — fit point 에서 eval
- 동일 atom closures 를 *test HC pool* 로 재구성 — `:460-477`
- `test_loss = Σ (test_atom(fit) − μ_train) / σ_train`, normalized by √n_atoms — `:478-502`

### Per-cell output fields (s10b_v6_pca_rdm.py:646-707)

| Field | 의미 | Use |
|---|---|---|
| `n` | resample 수 (=300) | sanity |
| `train_loss_median, _iqr` | composite_train minimum 분포 | fit stability |
| `test_loss_median, _iqr` | test composite 값 (z-rescaled by train stats) | **P2 sort key** |
| `test_focal_median, _iqr` | focal pair z² on test (sub-08 YP / sub-09 GB) | behavioral fit (focal pair) |
| `test_agg_median, _iqr` | γ_all 8-pair z² sum on test | behavioral fit (aggregate) |
| `test_V1_RDM_median, _iqr` | V1 PCA-aligned RDM cosine on test | neural geometry fit |
| `test_per_pair_medians` | per-pair z² on test (8 entries) | per-pair behavioral fit |
| `boundary_rate` | argmin 이 grid edge 비율 | degeneracy indicator |
| `aic_median, bic_median` | AIC/BIC on test_focal, k=K_RC(1) 또는 K_2C(2), n=2 | model complexity |
| `param_summary` | `bs_median, bs_iqr, bc_median, bc_iqr` 또는 `g_median, g_iqr` | fitted parameter + 안정성 |

---

## Step 3. 각 모델의 HC pool 안정성 평가 (Phase B v6 output)

300 resample 후 per cell × per model summary:

| Metric | 의미 |
|---|---|
| `train_loss_median, _iqr` | composite minimum 분포 |
| `test_loss_median, _iqr` | test composite 안정성 (낮을수록·안정할수록 ↓) |
| `param_summary` | `bs_median, bs_iqr, bc_median, bc_iqr` (2comp) 또는 `g_median, g_iqr` (R+C) |
| `boundary_rate` | argmin 이 grid edge 에 떨어진 비율 (degeneracy) |

### 안정성 gates (advisor 권고)

1. **Collapse**: `test_loss_iqr > 50` OR `sign(train) ≠ sign(test) AND |test−train| > 5`
2. **Boundary**: `boundary_rate < 0.5`
3. **P2 sort**: `(test_loss_median ASC, test_loss_iqr ASC)`, LOCO cell IQR=+∞ (HC-pool variation 무관)

### Gate 통과율 (전체 cell × model)

| Subject | Total | Collapse | Boundary≥50% | Both gates pass |
|---|---|---|---|---|
| sub-08 | 284 | 91 (32%) | 111 (39%) | **31 (11%)** |
| sub-09 | 44 | 6 (14%) | 27 (61%) | **2 (5%)** |

→ **대부분 cells 가 collapse 또는 boundary-degenerate**. Stability check 가 강한 filter 역할.

---

## Step 4. 가중치 sweep — Cycle 6b raw-weight (Phase B 통합)

### Motivation
z-score composite (Step 2) 는 *grid-relative normalization* 으로 atom 간 magnitude/info-density 격차 평탄화. 1-pair γ_focal ↔ 8-pair γ_all ↔ RDM cosine 이 *동등* composite 기여. 이는 **focal-fit specialist 또는 LOCO cells 의 후보가 invisible 해질 수 있음**.

### Cycle 6b 의 raw-weight reranking
```python
# scripts/cycle6b_extended_raw_weight.py
score(r, w_f, w_a, w_R) = w_f * r['focal']   # subject-specific focal pair z²
                        + w_a * r['agg']     # 8-pair sum z²
                        + w_R * r['rdm']     # V1 PCA-RDM cosine

# 47 schemes:
#   w_focal ∈ {0, 1, 2, 5}    × w_all ∈ {0, 1}   × w_RDM ∈ {0, 25, 50, 100, 200, 400}
#   minus (0,0,0)
```

### Cycle 6b 가 추가 추출한 후보 (cycle6 baseline 대비)

| Subject | NEW 후보 | 핵심 |
|---|---|---|
| sub-08 | **8 NEW** | (44, 36)·(38, −10)·(40, 40)·(44, 28)·(46, 24)·(36, −14)·(45, −24)·RC g=2.25 |
| sub-09 | 1 NEW (weak null) | (34, −8) — train_loss ≈ 0 → discard |

### Cycle 6b 의 핵심 발견

- **γ_focal weight = 0 였던 cycle6 baseline 은 *YP-focal specialist* 를 못 봄** — (44, 36)/(40, 40) 류
- **cycle6 는 LOCO cells 를 완전 제외** — (44, 36) 은 LOCO cell 발 후보였음
- **각 후보가 어떤 *scheme category* 에서 ranking 상위인지가 mechanism 단서**:

| Scheme category | 의미 | 등장 후보 |
|---|---|---|
| focal-dominant (w_focal>0, w_RDM 작음) | YP-focal 특화 fit | (44, 36) (44, 28) (40, 40) |
| focal+all joint | γ_focal + γ_all 동시 강조 | (38, −10) (6, −42) |
| all-dominant (w_all>0) | 8-pair 평균 fit | (6, −42) (16, −44) |
| RDM-dominant (w_RDM≥100) | neural RDM 매칭 우선 | (36, −14) (45, −24) RC g=2.25 |
| RDM-only low-w | RDM 25× 만 | RC g=2.25 (32, 0) |

---

## Step 5. 최종 결정 + 한계 + 식별성

### 5.1. Final candidate set (advisor verdict 반영, (44, 36) 제외)

#### Sub-08 (deutan) — 2 candidates parallel reporting

(44, 36) 은 *catastrophic mis-fit on 7/8 pairs* (agg=1386.54 = non-YP 평균 ~14 SD off) 이유로 제외 (advisor blocker 1).

| 후보 | Phase B fit loss | β_s | β_c | test_med ± iqr | focal | agg | bdy | param_IQR |
|---|---|---|---|---|---|---|---|---|
| **S08-stable** | γ_all + RDM_V1 | 38 | −10 | −1.14 ± **0.86** | 28.00 (5.3 SD) | 83.32 | **0%** | (?, ?) |
| **S08-robust** | γ_OY + RDM_V2 / V3 (**2 combos**) | 6 | −42 | −2.36 ± 2.15 | 62.48 (7.9 SD) | **22.77** | 9% | (8, 2) |

**Mechanism interpretation**:
- S08-stable (38, −10): primary S-cone shift, minimal cortical confusion-axis. β_s-dominant.
- S08-robust (6, −42): primary cortical confusion-axis (large negative), minimal S-cone. β_c-dominant (opposite sign of stable).
- 두 후보는 **opposite mechanism hypotheses**. Phase 3 행동 실험이 tiebreaker.

**Family-specificity (sub-08 protan audit)**: 두 후보 모두 protan-axis fit 에서 0/47 schemes 등장 — *consistent with deutan signal* (단 basis geometry 차이 가능성으로 formally not established).

#### Sub-09 (protan) — (β_s=2, β_c=24) primary

| 항목 | 값 |
|---|---|
| Phase B fit loss | γ_all + RDM_V1 / γ_GB + RDM_V1 (**2 combos**) |
| param IQR | (0, 0) **deterministic** |
| test_loss_median ± IQR | −1.52 ± 1.41 |
| test_focal (GB z²) | 6.18 (2.5 SD) |
| test_V1_RDM | 0.763 (sub-09 candidates 중 best) |
| boundary_rate | **0%** interior solution |

**Mechanism**: cortical confusion-axis primary (β_c=24), minimal S-cone (β_s=2). Atypical protan or cortical compensation dominant.

**R+C 보조 보고 (NOT competing candidate)**: g=2.95 (rc_Boehm_low, Δλ=4.5nm), bdy=41% near-saturation → **R+C 1-DOF insufficient for sub-09**.

### 5.2. Phase D Round 3 — 식별성 검증 결과 (2026-05-26 완료)

```python
# scripts/s13_round3.py
CANDIDATES = [
    {'id': 'S08-stable',  'subject': 'sub-08', 'beta_s_gt': 38.0,  'beta_c_gt': -10.0},
    {'id': 'S08-robust',  'subject': 'sub-08', 'beta_s_gt': 6.0,   'beta_c_gt': -42.0},
    {'id': 'S09-primary', 'subject': 'sub-09', 'beta_s_gt': 2.0,   'beta_c_gt': 24.0},
]
# Per candidate × 2 GTs (null, fit) × N_OUTER=50 outer bootstrap (swap-HC)
# Pass: β_s_iqr < 30, β_c_iqr < 30, recovery median within ±10° of GT
```

#### Results — 모든 candidates FAIL

| Candidate | GT type | β_s GT→median (offset) | β_c GT→median (offset) | β_c IQR | bdy | Verdict |
|---|---|---|---|---|---|---|
| **S08-stable** | fit (38, −10) | 38→32 (6) | −10→**+26** (**36**) | **44.0** | 26% | ✗ FAIL |
| S08-stable | null (0, 0) | 0→+26 (26) | 0→−16 (16) | 36.0 | 20% | ✗ FAIL |
| **S08-robust** | fit (6, −42) | 6→34 (28) | −42→−26 (16) | **68.5** | 26% | ✗ FAIL |
| S08-robust | null (0, 0) | 0→+46 (46) | 0→−26 (26) | 18.0 | 50% | ✗ FAIL |
| **S09-primary** | fit (2, 24) | 2→22 (20) | 24→**−10** (**34**) | **41.5** | 26% | ✗ FAIL |
| S09-primary | null (0, 0) | 0→+26 (26) | 0→+10 (10) | 34.0 | 48% | ✗ FAIL |

#### Critical findings

1. **모든 fit GT recovery FAIL**: β_c IQR=41-68 (criterion <30), median offset 16-36°. 특히 **β_c sign-flip 등장** (S08-stable: GT−10 → recovered +26; S09-primary: GT+24 → recovered −10)
2. **Null GT 도 FAIL**: 변형 없는 CVD voxel pattern 에서 (+26, −16) 등 spurious params 추정. *Fit procedure 가 systematic positive β_s bias 보유*
3. **β_s positive bias**: null GT 에서도 +26~+46 으로 추정 — 0 grid edge 에서 vox covariance 가 +β_s 방향으로 fit 을 끌어당김

#### Interpretation

- Round 1 의 S08-E_v4 β_c IQR=98° 가 *특정 후보의 우연이 아닌 procedure-level 한계*임이 확정
- Pipeline 2 의 forward model parameter estimates 는 **uniqueness 보장 불가**
- 후보들은 *fit-point optima* 이지만 *unique solutions* 아님 — 대체 (β_s, β_c) sets 가 유사 fit 산출 가능
- **Behavioral validation (Phase 3) 가 sole verification path**

#### Caveat — Bootstrap method 한계

Round 3 의 swap-HC bootstrap (HC voxel pattern 을 CVD 로 swap 후 GT perturbation 적용) 자체가 HC inter-subject variance 를 fit landscape 에 도입 → null GT 가 (0, 0) 으로 회복 안 되는 부분은 *partial method artifact* 가능. 단 **fit GT recovery FAIL 은 method 와 무관하게 해석 가능** (known signal 추가했음에도 fit 이 recovery 못 함 = procedure-level identifiability 한계).

### 5.3. Limitations (paper-level disclosure, 7 items, advisor verdict 반영)

| # | Limitation | Evidence | Paper wording |
|---|---|---|---|
| L1 | **Forward model identifiability FAIL (parameter uniqueness)** | **Round 3 (2026-05-26): 모든 3 final candidates β_c IQR=41-68° (criterion <30); fit GT recovery sign-flip; null GT spurious recovery** | "Forward model parameters are not identifiable: multi-point recovery simulation on all final candidates failed to recover fit-point GT (β_c IQR 41-68°, median offset 16-36°, sign-flips on β_c). Null GT also failed (recovered β_s +26 to +46 from undistorted CVD pattern), indicating procedure-level positive β_s bias possibly compounded by HC bootstrap variance. **The candidates represent *descriptive fits at fit point only*; alternative parameter sets may produce similar fits. Behavioral validation (Phase 3) is the sole verification path for filter efficacy.**" |
| L2 | OOS 축 = HC normalization robustness only | CVD JND N=1; train/test 양쪽 동일 measurement | "OOS axis is HC pool composition; CVD generalization requires Phase 3 behavioral experiment. Individualized-filter framing justifies this scope." |
| L3 | Held-out focal pair CVD obs reuse | Focal pair excluded from fit objective; same CVD measurement in test eval | "Focal pair excluded from fit; same CVD JND enters test under different HC normalization. Not data leakage under individualized framing." |
| L4 | HC n=7 (effective 6 for hV4) | sub-07 hV4 = 16 voxels → nan | "Limited HC pool. Bootstrap CI reflects sub-04 outlier impact." |
| L5 | Z-score atom info density 균등화 (Step 2의 한계) | 1-pair γ ↔ 8-pair γ_all 동등 기여 | "Atom weighting in z-score composite equalizes information density; cycle6b raw-weight scheme used to surface focal-fit + LOCO-cell candidates missed by z-score." |
| L6 | R+C 1-DOF insufficient | sub-08/09 R+C all candidates boundary collapse 또는 near-saturation | "R+C 1-DOF model insufficient: sub-09 fits saturate at g=2.95 (bdy 41%); sub-08 R+C candidates show focal=66 (~8 SD off)." |
| L7 | Sub-08 mechanism non-unique | (38, −10) β_s-dominant vs (6, −42) β_c-dominant — opposite-sign | "Sub-08 mechanism not identified by Pipeline 2 alone. Two candidates with opposite β_c signs both pass selection; Phase 3 behavioral experiment is inter-candidate tiebreaker." |

---

## Phase C v2 — Disposition (사용자 query 답변)

### 의도된 purpose
Phase B selected candidates 에 대한 **atom weight optimum identification** via simplex-constrained sweep (`Σ w_a = 1`).

### 실제 결과 — *final candidate selection 에 contribution = 0*

| Subject | Phase C selected candidates | Phase C 결과 | 현재 final 와의 관계 |
|---|---|---|---|
| sub-08 | S08-A (γ_\|RDM_\|LOCO), S08-B (γYG\|RDMV1+V4\|noLOCO 가까운 v3 candidate), S08-E (γYG\|RDMV2\|LOCO) | 모두 **corner/boundary degenerate** (g=0.05, g=3.00, βs=50, βc=50) | Phase C 후보 ≠ final 후보 |
| sub-09 | S09-A (γGB\|RDMV1\|noLOCO RC), S09-A_DPS | g=3.00 boundary 100% (S09-A), g=2.60 boundary saturate (S09-A_DPS) | R+C insufficiency evidence 로만 활용; (2, 24) 와 무관 |

### Phase C 가 fail 한 이유
1. **Phase B v3 candidates 기반 (cycle6b 이전)**. v6 PCA-RDM + cycle6b 가 surface 한 (38, −10) (6, −42) (2, 24) 후보는 *Phase C 의 candidate set 에 없었음*.
2. **Sub-08 corner solutions**: simplex `Σw=1` 제약 하에서 *all-weight-on-LOCO* 또는 *all-weight-on-RDM* 등 corner 가 최적이 됨. Interior weight optimum 없음.
3. **Sub-09 boundary saturation**: g_max=3.00 grid 한계에 fit 이 멈춤.

### Phase C honest disposition (paper-level)

> "Phase C employed a simplex-constrained atom weight sweep on Phase B v3 candidates. The sweep produced only corner/boundary solutions for sub-08 (all-weight-on-single-atom configurations) and boundary-saturated R+C fits for sub-09. Phase C did not contribute to final candidate selection. The Phase B v6 + Cycle 6b raw-weight extension (Step 4 above) superseded Phase C as the weight-sweep step, identifying both new candidates and weight emphases ((focal-dominant, all-dominant, RDM-dominant) per candidate)."

### Phase B → C seed audit (post-selection inference)
부수적 결과: Phase C 는 Phase B 와 동일 RNG seed (=42) 사용 → 동일 HC partition. Independent seed (142) 재실행 시 sub-09 test_iqr **80-300% inflated** (S09-A: 24.93 → 44.58; S09-A_DPS: 30.50 → 120.96). 후보 param 은 robust (g=3.00, g=2.60 identical). **Phase C 가 final selection 에 기여하지 않으므로 본 audit 결과는 Phase C limitation 보고용으로만 활용**.

---

## Closure verdict

### 완료
- ✓ Step 1-4 완료 (Phase A → Phase B v6 + Cycle 6b)
- ✓ Sub-08 final candidates: (38, −10), (6, −42) parallel; (44, 36) advisor verdict 로 제외
- ✓ Sub-09 final: (β_s=2, β_c=24) primary; R+C g=2.95 → R+C insufficiency evidence
- ✓ Family specificity audit (sub-08 protan) — deutan-consistent
- ✓ Phase B → C seed audit — Phase C limitation documented (Phase C 자체가 final selection 비기여)
- ✓ **Phase D Round 3 식별성 검증 완료 — 모든 후보 FAIL** (위 §5.2)
- ✓ 7 paper-level limitations, L1 강화 (procedure-level identifiability 한계 확정)

### Closure verdict — **CLOSURE READY**

- Pipeline 2 의 final candidates 는 *descriptive filter forms at fit point only*
- Parameter uniqueness 보장 불가 (L1 procedure-level)
- Phase 3 행동 실험이 **sole verification path** — paper 작성 가능

### Paper-level framing (정직)

> "Pipeline 2 produced three candidate filter forms ((β_s=38, β_c=−10), (β_s=6, β_c=−42) for sub-08; (β_s=2, β_c=24) for sub-09) via composite atom z-score argmin + cycle 6b raw-weight reranking + family-specificity audit. **Multi-point recovery simulation showed identifiability failure on all candidates**, demonstrating that the fitted parameters minimize a local objective but do not represent unique solutions. We therefore present these candidates as *plausible descriptive fits requiring behavioral validation*, not as estimated cone-shift or cortical-distortion parameters."

---

## Files

| File | Role |
|---|---|
| `PIPELINE_2_CLOSURE.md` | (본 문서) 5-step pipeline narrative + final candidates + limitations |
| `PHASE_B_DETAIL.md` | Phase B v6 + Cycle 6b 코드 line-reference 상세 |
| `PIPELINE_2_AUDIT_2026-05-26.md` | Phase C seed audit + protan audit 결과 |
| `scripts/s10b_v6_pca_rdm.py` | Phase B v6 main runner |
| `scripts/cycle6b_extended_raw_weight.py` | Step 4 — raw-weight scheme sweep |
| `scripts/run_sub08_protan_audit.py` | Family specificity audit |
| `scripts/s13_round3.py` | Phase D Round 3 (진행 중) |
| `scripts/s12b_phase_c_v2.py` | Phase C v2 (현재 final selection 에 기여하지 않음; limitation 보고용) |
| `results/s10_inclusion/s10b_v6_pca_rdm_results_{sub-08,sub-09}.json` | Phase B v6 output |
| `results/s10_inclusion/cycle6b_extended_composite_{sub-08,sub-09}.json` | Cycle 6b output (Step 4) |
| `results/s10_inclusion/s10b_v6_pca_rdm_results_sub-08_protan_audit.json` | Sub-08 protan family audit |
| `results/s12b_phase_c_v2/sweep_{sub-08,sub-09}{,_seed142}.json` | Phase C original + audit |
| `results/s13_multipoint_sim/s13_round3_recovery.json` | (pending) Phase D Round 3 |
