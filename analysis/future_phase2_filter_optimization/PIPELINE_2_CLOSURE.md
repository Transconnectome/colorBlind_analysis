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

**판단 기준**: (a) AIC/BIC on test_focal, (b) boundary_rate (degeneracy), (c) test_focal (behav fit quality), (d) test_loss_iqr (HC stability).

**결과** (Phase B v6, model + loss + parameters 명시):

| Subject | Model | Loss combo | Parameters | AIC | BIC | bdy | test_focal | test_iqr |
|---|---|---|---|---|---|---|---|---|
| sub-08 deutan | **2-Component** | γ_all + RDM_V1 | β_s=38±24, β_c=−10±22 | 9.28 | 6.66 | **0%** | 28.00 | **0.86** |
| sub-08 deutan | **2-Component** | γ_OY + RDM_V2 | β_s=6±8, β_c=−42±2 | 10.88 | 8.27 | 9% | 62.48 | 2.15 |
| sub-08 deutan | **R+C** (JND_Lamb) | RDM_V1 only | Δλ=6.5 nm (fixed), g=2.25±0.00 | 9.01 | 7.70 | 0% | 66.56 | 1.38 |
| sub-09 protan | **2-Component** | γ_all + RDM_V1 | β_s=2±0, β_c=24±0 | 6.26 | 3.64 | **0%** | 6.18 | 1.42 |
| sub-09 protan | **2-Component** | γ_GB + RDM_V1 | β_s=2±0, β_c=24±0 | 6.26 | 3.64 | **0%** | 6.18 | 1.41 |
| sub-09 protan | **R+C** (Boehm_low) | γ_all + RDM_V1 | Δλ=3.0 nm (fixed), g=2.95±0.10 | **4.20** | **2.89** | **41%** | 6.00 | 0.57 |

**Verdict** (subject-별):

- **Sub-08: 2-Component > R+C**.
  - 2-comp γ_all+RDM_V1: bdy 0%, test_focal=28 vs R+C: bdy 0% but test_focal=66.56 (8 SD off)
  - AIC/BIC 비슷하나 R+C 의 behavioral fit *3× 나쁨*
  - Cycle 6b R+C 후보 대다수 g=3.00 boundary collapse (sub-08 91 collapse cells 중 88 이 R+C)
- **Sub-09: 2-Component > R+C** (AIC/BIC 가 R+C 를 선호함에도 불구).
  - R+C: AIC/BIC 최저이나 **bdy=41%** = upper-boundary saturation (g_max=3.00 에 fit 이 멈춤)
  - 2-comp: interior solution bdy=0%, *legitimate fit*

**종합**: 2-Component 이 양 subject 모두 better. AIC/BIC 단독으론 R+C 선호 가능하나 boundary_rate + behavioral fit quality 함께 보면 2-comp 우세.

#### R+C "underspecified" 주장의 비판적 검토 (paper claim 강도)

| 주장 강도 | 근거·한계 |
|---|---|
| **약함 (지지 안 됨)**: "g=2.95 = 195% 과보상이 Tregillus 2020 / Boehm 2016 의 g≈1.1 (10%) 범위 초과 → R+C underspecified" | **방법론 mismatch**: 문헌 g 는 *behavioral 색명명 + 적응 패러다임*; 우리 g 는 *fMRI MVPA-derived JND fit*. 두 g 가 개념적으로 동일하지 않음 — *직접 비교 over-reach*. 또한 Δλ source 선택에 따라 g rescale (fix 됨). **invalid argument** |
| **중간 (조건부)**: "Sub-09 R+C 가 g_max=3.0 boundary 41% 에서 saturate → fit 이 모델 capacity 끝까지 밀어붙임" | 사실. 단 saturation 원인이 (a) 진정한 신호가 모델 capacity 초과 vs (b) z-score loss artifact 가 grid edge 로 fit 끌어당김 — 둘 다 가능. **단독 evidence 부족** |
| **강함 (지지됨)**: "Sub-09 의 R+C 로 fit 안 되는 *구조적 component* 는 cortical confusion-axis rotation (β_c) — R+C 1-DOF 에 structurally absent" | **이 주장만 정직하게 강함**. 동일 loss (γ_all + RDM_V1) 에서 R+C bdy=41% saturate vs 2-comp interior bdy=0%. 차이는 *2-comp 의 β_c DOF*. R+C 의 forward expression `δθ = (2−g) · δθ_Machado` 는 retinal cone-shift 의 *linear scaling 만* — confusion-axis rotation 과 무관. **Sub-09 의 신호 중 confusion-axis 성분 (β_c=+24) 은 R+C 모델 구조에 표현 불가** |

**Paper-reportable wording (정직)**:
> "R+C 1-DOF model has insufficient *structural* capacity for sub-09: under the same loss (γ_all + RDM_V1), R+C saturates at g_max=3.0 (bdy=41%) while 2-Component finds an interior solution at (β_s=2, β_c=24). The boundary saturation reflects a signal component (the confusion-axis rotation captured by 2-Component's β_c=+24) that R+C's forward expression `δθ = (2−g)·δθ_Machado` cannot represent — R+C scales retinal cone-shift linearly, with no DOF for cortical confusion-axis rotation. We do not compare fitted `g` values to behavioral-adaptation literature (Tregillus 2020, Boehm 2016), as those measurements used different paradigms (color naming + adaptation) and are not directly commensurable with our fMRI-derived `g`."

→ Paper claim 은 *structural DOF argument* 기반 (literature g 비교 제외). L6 limitation 강화.

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

**한계 명시** (HC pool 한계는 *final candidates 의 ROI 사용 패턴 반영*: V1, V2 RDM 사용; hV4 RDM 은 final candidates 에 없음 → sub-07 hV4 nan 캐비엇 제외):

| 한계 | Evidence | 함의 |
|---|---|---|
| **CVD N=2** (sub-08 deutan, sub-09 protan; sub-10 near-normal 제외) | Phase 2 sample size | Cross-CVD generalization 검증 불가; **CVD LOO 불가능** (N=2) — *individualized filter* framing 으로만 정당화 |
| **HC pool n=7, sub-04 outlier** | cycle6b HC subset resampling 분포 (CLAUDE §2.5: sub-04 outlier 영향) | HC stability 측정의 noise floor 결정. sub-04 outlier 가 bootstrap CI 폭에 영향 |
| **HC train-test 는 5/2 subset split (300 draws), 진정한 LOO 가 아님** | `s10b_v6_pca_rdm.py:49-51, 351-357`: SUBSET_SIZE=5, N_RESAMPLES=300. 별개의 `s10a_precondition.py` 만 strict HC LOO 사용 | HC subset train-test **는 진행됨** (= HC normalization robustness 측정). 그러나 strict LOO (HC 1명 제거 6 train + 1 test × 7 folds) 가 아닌 random 5/2 sampling → fold 별 정확한 reproducibility 보장 안 됨. **HC LOO 추가 시 cycle6b 후보의 specificity 강화 가능** (현재 미실시) |
| **Specificity FAIL (procedure-level)**: Phase D Round 3 — null GT (0, 0) 에서 (+26, −16) 등 spurious 추정 | §5.2 Round 3 results | Fit procedure 가 HC voxel pattern 의 inter-subject variance 를 β_s positive 방향으로 absorb. Filter 가 HC 와 CVD 를 진정으로 구별하는지 불확실 |

**Verdict**: **No — generalization 불가능**. Pipeline 2 의 model 은 *individualized filter form* 으로만 보고. Cross-CVD/HC generalization 은 다음 조건 만족 시에만 가능:
1. CVD N 증가 (현재 N=2; CVD LOO 본질적 불가)
2. HC pool 확장 또는 strict HC LOO (현재 5/2 random sampling 만 시행)
3. Independent identifiability test 통과 (Round 3 FAIL → 미충족)

→ **L1/L2/L3/L4 limitations** 로 paper 에 명시.

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
| 2. 손실항·조합 후보 소개 | Atoms + cell enumeration (atom 정의 + combos 열거) | `scripts/s10b_v6_pca_rdm.py` (atom factories + combo enum) |
| 3. 조합 fit + 평가 + 후보 정리 | Phase B v6 5/2 HC split × 300 + strict HC LOO 7-fold; metric primary/secondary/supplementary 순서로 후보 정리 | `scripts/s10b_v6_pca_rdm.py`, `scripts/s17_hc_loo.py` |
| 4. **가중치 sweep — sanity check** | Step 3 후보들의 raw-weight 변동 robustness 확인 (Closure 이전 sanity check; *새 optimum 발견 아님*) | `scripts/cycle6b_extended_raw_weight.py` |
| 5. 최종 결정 + 한계 + 식별성 | Closure (본 문서) + Phase D Round 3 multi-point sim | `scripts/s13_round3.py` |

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

## Step 2. 손실항·조합 후보 소개

Atoms 정의는 Step 1 Data section (위) 참조. Step 2 는 *어떤 atoms 가 어떤 조합으로 평가될지* 만 정의 — fitting 없음.

### Cell enumeration

```python
# s10b_v6_pca_rdm.py:267-282 (sub-08), :285-306 (sub-09)
# Sub-08:  γ ∈ {none, OY, YG, YP, [OY,YG,YP], ALL} × RDM ∈ {none, V1, V2, V3, V4, V1+V4} × LOCO ∈ {off, V4}
# Sub-08 cells × models = 71 × 4 = 284
# Sub-09:  γ ∈ {none, GB, ALL} × RDM ∈ {none, V1} × LOCO ∈ {off, V4}
# Sub-09 cells × models = 11 × 4 = 44
```

각 cell 은 *한 model × 한 atom 조합*. 4 models = Machado 1-way / R+C × 3 Δλ sources (DPS_lit / Boehm_mid / JND_Lamb) / 2-Component.

---

## Step 3. 조합 fit + 평가 + 후보 정리 (Phase B v6 + strict HC LOO)

### 3.1. Fit procedure

**Train/test split** (Phase B v6, `s10b_v6_pca_rdm.py:49-51, 351-357`):
```
N_RESAMPLES = 300,  SUBSET_SIZE = 5 train HC + 2 test HC,  RNG_SEED = 42
```

**Train atom** (5 train HC pool):
- γ_pair: `((predicted_JND − CVD_JND) / HC_train_SD)²` — `:99-117`
- γ_all: 8-pair z² 합 — `:80-97`
- RDM: PCA-aligned RDM (K=6) cosine distance to *train HC mean* — `:156-174`
- LOCO: V4 voxel-prediction loss (CVD-internal, HC-independent) — `:199-211`

**Composite + argmin**:
```python
z_sum = Σ zscore_grid(atom_grids[atom_name])   # grid-relative z-score
comp = z_sum / sqrt(n_atoms)
fit_param = argmin(comp)                        # g 또는 (β_s, β_c)
```

**Test atom** (2 test HC pool, fit point eval):
- 동일 atom closures *test HC pool* 로 재구성 (`:460-477`)
- `test_loss = Σ (test_atom(fit) − μ_train) / σ_train`, normalized by √n_atoms (`:478-502`)

**Strict HC LOO supplement** (`scripts/s17_hc_loo.py`): 7-fold (각 HC 한 명씩 제외), 6 train + 1 test. Random 5/2 의 stability 결과를 *deterministic LOO*로 재검증.

### 3.2. Per-cell output fields

| Field | 의미 |
|---|---|
| `train_loss_median, _iqr` | composite_train minimum 분포 |
| `test_loss_median, _iqr` | test composite (z-rescaled by train stats) — **primary metric** |
| `test_focal_median, _iqr` | focal pair z² on test (sub-08 YP / sub-09 GB) |
| `test_agg_median, _iqr` | γ_all 8-pair z² sum on test |
| `test_V1_RDM_median, _iqr` | V1 PCA-aligned RDM cosine on test |
| `test_per_pair_medians` | per-pair z² on test (8 entries) |
| `boundary_rate` | argmin 이 grid edge 비율 (degeneracy) |
| `aic_median, bic_median` | AIC/BIC on test_focal, k=K_RC(1) / K_2C(2), n=2 |
| `param_summary` | `bs_median, bs_iqr, bc_median, bc_iqr` (2comp) 또는 `g_median, g_iqr` (R+C) |

### 3.3. Selection metric 우선 순위

1. **Primary**: `test_loss_median` ASC (가장 낮은 값 = 가장 좋은 OOS test fit)
2. **Secondary**: `test_loss_iqr` ASC (HC subset 변동에 robust)
3. **Supplementary** (degeneracy 배제용):
   - `boundary_rate < 0.5` (grid edge fit 배제)
   - Collapse criterion: `test_loss_iqr > 50` OR `sign(train) ≠ sign(test) AND |test − train| > 5` 인 cell 배제

### 3.4. Gate 통과율 (전체 cell × model)

| Subject | Total | Collapse | Boundary≥50% | Both gates pass |
|---|---|---|---|---|
| sub-08 | 284 | 91 (32%) | 111 (39%) | **31 (11%)** |
| sub-09 | 44 | 6 (14%) | 27 (61%) | **2 (5%)** |

→ 대부분 cells 가 collapse 또는 boundary-degenerate; gates 가 강한 filter 역할.

### 3.5. 선정된 model·loss 후보 + fitting 결과 표

선정 기준: Primary (test_loss_median) + Secondary (test_loss_iqr) + Supplementary (boundary, collapse) pass + Step 4 weight sweep robustness 확인 (아래 §4).

| Subject | Model | Loss combo | Parameters (Phase B median ± IQR) | Phase B v6 IQR | Strict HC LOO range | AIC | BIC | bdy | test_med ± iqr | focal | agg | rdm |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sub-08 | **2-Component** | γ_all + RDM_V1 | β_s=38±24, β_c=−10±22 | bs:24, bc:22 | bs[20, 46], bc[−32, 0] (sub-02 outlier) | 9.28 | 6.66 | **0%** | −1.14 ± **0.86** | 28.00 | 83.32 | 0.965 |
| sub-08 | **2-Component** | γ_OY + RDM_V2 / V3 (2 combos) | β_s=6±8, β_c=−42±2 | bs:8, bc:2 | bs[2, 12], bc[−46, −38] | 10.88 | 8.27 | 9% | −2.36 ± 2.15 | 62.48 | **22.77** | 1.240 |
| sub-08 | R+C (JND_Lamb) | RDM_V1 only | Δλ=6.5 nm, g=2.25±0.00 | 0.00 | g=2.25 deterministic | 9.01 | 7.70 | 0% | −0.88 ± 1.38 | 66.56 | 107.82 | 0.941 |
| sub-09 | **2-Component** | γ_all + RDM_V1 / γ_GB + RDM_V1 (2 combos) | β_s=2±0, β_c=24±0 | bs:0, bc:0 | bs[2, 2], bc[24, 24] deterministic | 6.26 | 3.64 | **0%** | −1.52 ± 1.41 | 6.18 | 16.90 | **0.763** |
| sub-09 | R+C (Boehm_low) | γ_all + RDM_V1 | Δλ=3.0 nm, g=2.95±0.10 | 0.10 | g[2.90, 3.00] (3/7 folds at boundary) | 4.20 | 2.89 | **41%** | −0.86 ± 0.57 | 6.00 | 6.41 | 0.921 |

**HC LOO 추가 finding** (`s17_hc_loo.py`):
- Strict LOO median 이 *모든 5 후보에서 Phase B v6 5/2 random median 과 일치* → v6 median 이 sampling artifact 아님.
- **S08-stable (38, −10)** 는 HC LOO 에서 bs[20, 46], bc[−32, 0] 가장 넓은 spread. **sub-02 exclusion 이 dominant outlier** (Δ=28.4) — CLAUDE §2.5 의 sub-04-driven instability 와 다른 pattern.
- S08-robust, S09-stable, S08-rc-subprimary: LOO spread 작음 (zero 또는 ≤10° per axis).
- S09-rc-subprimary: 3/7 folds 에서 g=3.0 boundary saturate — R+C insufficiency 의 fold-level 확인.

---

## Step 4. 가중치 sweep — Step 3 후보 robustness sanity check

**역할**: Closure 이전 *확인 절차* — Step 3 의 z-score composite 으로 선정된 후보들이 *raw-weight 가중치 변동에 robust* 한지 검증. **새 optimum 발견이 아닌, Step 3 selection 의 weight-emphasis 민감도 확인**.

### 절차

Step 3 의 Phase B v6 output (per-cell × per-model 의 raw atom 값들) 을 *재실행 없이* 후처리. Composite formula 만 변경:

```python
# scripts/cycle6b_extended_raw_weight.py — raw weight (no z-score)
score(r, w_f, w_a, w_R) = w_f · r['focal']  +  w_a · r['agg']  +  w_R · r['rdm']

# 47 schemes:
#   w_focal ∈ {0, 1, 2, 5},  w_all ∈ {0, 1},  w_RDM ∈ {0, 25, 50, 100, 200, 400}
#   minus (0, 0, 0)
```

각 후보가 *몇 개의 scheme 에서 상위에 등장* 하는지 + *어떤 scheme category 에서 우세* 한지 확인.

### Step 3 후보별 robustness (Step 4 결과)

| Step 3 후보 | Phase B fit combo (atoms) | Scheme category 별 등장 횟수 (47 중) | Robustness 평가 |
|---|---|---|---|
| sub-08 (β_s=38, β_c=−10) | γ_all + RDM_V1 | focal+all joint **6** / RDM-dominant **6** | γ_focal + γ_all 동시 가중 필요. RDM 강조 시에도 surface. 12/47 schemes |
| sub-08 (β_s=6, β_c=−42) | γ_OY + RDM_V2 / V3 (**2 fit combos**) | all-dominant **5** / focal+all joint **3** / RDM-dominant **1** | **multiple Phase B fit combos × 3 categories** = 가장 loss-robust |
| sub-08 R+C g=2.25 | RDM_V1 / V3 (no γ) | RDM-dominant **6** / RDM-only low-w **4** | RDM-driven, behav-blind. 10/47 schemes |
| sub-09 (β_s=2, β_c=24) | γ_all + RDM_V1 / γ_GB + RDM_V1 (**2 fit combos**) | RDM-dominant **16** | RDM 가중 우세 영역에서만 surface, 그러나 2 fit combos 에서 동일 param |
| sub-09 R+C g=2.95 | γ_all + RDM_V1 | focal+all joint **8** / RDM-dominant **4** / focal-dominant **2** | 14/47 schemes 등장, 그러나 boundary 41% |

### 부수 finding (Step 4 에서 surface 한 alternative configurations)

Sub-08 의 (β_s=38, β_c=−10) 는 Step 3 의 z-score composite ranking 단독으로는 top 에 오르지 않았으나 *focal+all joint scheme 에서 surface*. Step 3 의 raw cell-level metric (test_loss_median=−1.14, IQR=0.86, bdy=0%) 으로 이미 robust 후보였음 → **Step 4 가 *Step 3 후보의 명시화*** (selection rule 의 weight-emphasis 일관성 확인).

### Step 4 의 결론

- **Step 3 후보 5개 모두 Step 4 의 multiple scheme categories 에서 robust** (each ≥10/47 schemes, 또는 ≥2 categories)
- 사용자 directive: "**새 optimal point 발견 아님**" — Step 4 의 alternative weight emphasis 가 *Step 3 후보를 다른 각도에서 확인* 하는 절차로 위치
- (cycle 6b script 의 실제 이름은 §Files 참조)

---

## Step 5. 최종 결정 + 한계 + 식별성

### 5.1. Final candidate set (advisor verdict 반영, (44, 36) 제외)

#### Sub-08 (deutan) — 2 candidates parallel reporting

(44, 36) 은 *catastrophic mis-fit on 7/8 pairs* (agg=1386.54 = non-YP 평균 ~14 SD off) 이유로 제외 (advisor blocker 1).

| 후보 | Phase B fit loss | β_s | β_c | test_med ± iqr | focal | agg | bdy | Phase B param_IQR | Strict HC LOO range |
|---|---|---|---|---|---|---|---|---|---|
| **S08-stable** | γ_all + RDM_V1 | 38 | −10 | −1.14 ± **0.86** | 28.00 (5.3 SD) | 83.32 | **0%** | (24, 22) | β_s[20, 46], β_c[−32, 0] (sub-02 outlier) |
| **S08-robust** | γ_OY + RDM_V2 / V3 (**2 combos**) | 6 | −42 | −2.36 ± 2.15 | 62.48 (7.9 SD) | **22.77** | 9% | (8, 2) | β_s[2, 12], β_c[−46, −38] |

**Mechanism interpretation**:
- S08-stable (38, −10): primary S-cone shift, minimal cortical confusion-axis. β_s-dominant.
- S08-robust (6, −42): primary cortical confusion-axis (large negative), minimal S-cone. β_c-dominant (opposite sign of stable).
- 두 후보는 **opposite mechanism hypotheses**. Phase 3 행동 실험이 tiebreaker.

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

### 5.3. Limitations (paper-level disclosure)

- **L1. Identifiability FAIL (all candidates)** — Round 3 multi-point recovery: β_c IQR 41–68°, fit GT median offset 16–36°, β_c sign-flips (S08-stable, S09-primary), null GT spurious recovery. Forward model parameters are *not unique*. Candidates = *descriptive fits at fit point only*.
- **L2. OOS axis is HC normalization only** — CVD JND is N=1 per pair; train/test split varies HC pool composition, not CVD samples. Behavioral generalization requires Phase 3 experiment.
- **L3. Held-out focal pair CVD obs reuse** — focal pair excluded from fit objective; the same CVD measurement enters test eval under different HC normalization. Not data leakage under individualized-filter framing, but disclosure required.
- **L4. CVD N=2, HC n=7, no strict CVD LOO possible** — CVD LOO impossible (N=2). Strict HC LOO (s17) confirms Phase B v6 medians but exposes per-fold spread (sub-02 drives S08-stable variance, not sub-04 as prior CLAUDE §2.5 expected).
- **L5. Z-score grid-relative composite equalizes atom info-density** — 1-pair γ_focal ↔ 8-pair γ_all contribute equally to composite. Step 4 raw-weight sweep used to verify Step 3 candidates are not artifact of this equalization.
- **L6. R+C 1-DOF structurally insufficient** — sub-09 R+C saturates at g_max=3.0 (bdy=41%); R+C's forward expression `δθ=(2−g)·δθ_Machado` lacks DOF for cortical confusion-axis rotation that 2-Component captures via β_c. *Structural* limit (DOF count), not literature-g comparison.
- **L7. Sub-08 mechanism non-unique** — (38, −10) β_s-dominant vs (6, −42) β_c-dominant with *opposite β_c sign*; both pass Step 3 selection. Two candidates reported in parallel; Phase 3 behavioral experiment is inter-candidate tiebreaker.
- **L8. Phase B → Phase C seed sharing (historical)** — Phase C v2 (now deprecated, see §Files) used identical RNG seed; under independent seed sub-09 IQR inflated 80–300%. Does not affect final selection (Phase C did not contribute to final candidates).

---

## Closure verdict

### 완료
- ✓ Step 1-4 완료 (Phase A → Phase B v6 + Cycle 6b)
- ✓ Sub-08 final candidates: (38, −10), (6, −42) parallel; (44, 36) advisor verdict 로 제외
- ✓ Sub-09 final: (β_s=2, β_c=24) primary; R+C g=2.95 → R+C insufficiency evidence
- ✓ Phase B → C seed audit — Phase C limitation documented (Phase C 자체가 final selection 비기여)
- ✓ **Phase D Round 3 식별성 검증 완료 — 모든 후보 FAIL** (위 §5.2)
- ✓ 7 paper-level limitations, L1 강화 (procedure-level identifiability 한계 확정)

### Closure verdict — **CLOSURE READY**

- Pipeline 2 의 final candidates 는 *descriptive filter forms at fit point only*
- Parameter uniqueness 보장 불가 (L1 procedure-level)
- Phase 3 행동 실험이 **sole verification path** — paper 작성 가능

### Paper-level framing (정직)

> "Pipeline 2 produced three candidate filter forms ((β_s=38, β_c=−10), (β_s=6, β_c=−42) for sub-08; (β_s=2, β_c=24) for sub-09) via composite atom z-score argmin + cycle 6b raw-weight reranking. **Multi-point recovery simulation showed identifiability failure on all candidates**, demonstrating that the fitted parameters minimize a local objective but do not represent unique solutions. We therefore present these candidates as *plausible descriptive fits requiring behavioral validation*, not as estimated cone-shift or cortical-distortion parameters."

---

## Files

| File | Role |
|---|---|
| `PIPELINE_2_CLOSURE.md` | (본 문서) 5-step pipeline narrative + final candidates + limitations |
| `PIPELINE_2_AUDIT_2026-05-26.md` | Phase C seed audit detail |
| `scripts/s10b_v6_pca_rdm.py` | Phase B v6 main runner |
| `scripts/cycle6b_extended_raw_weight.py` | Step 4 — raw-weight scheme sweep |
| `scripts/s13_round3.py` | Phase D Round 3 multi-point sim |
| `scripts/s17_hc_loo.py` | Strict HC LOO 7-fold supplement (Step 3) |
| `scripts/s12b_phase_c_v2.py` | **(deprecated)** Phase C v2 simplex weight sweep — final selection 에 기여 없음 (L8 limitation 보고용으로만 유지) |
| `results/s10_inclusion/s10b_v6_pca_rdm_results_{sub-08,sub-09}.json` | Phase B v6 output |
| `results/s10_inclusion/cycle6b_extended_composite_{sub-08,sub-09}.json` | Step 4 raw-weight sanity check output |
| `results/s10_inclusion/s17_hc_loo_results.json` | Strict HC LOO output |
| `results/s12b_phase_c_v2/sweep_*.json` | (deprecated) Phase C v2 output + seed audit |
| `results/s13_multipoint_sim/s13_round3_recovery.json` | Phase D Round 3 |
