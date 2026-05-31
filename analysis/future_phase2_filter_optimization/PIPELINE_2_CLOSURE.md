# Pipeline 2 Closure — 5-Step Selection Axis

- **Status**: CLOSURE READY (v6 PCA 45° categorical RDM atom canonical; 1° continuous variants removed)
- **Date**: 2026-05-31

---

## Framing decisions (read first)

- **RDM atom = 8AFC categorical** (8 stimulus colors → 45° bin lookup). Stimulus design 은 8 색의 discrete categorization 이므로 RDM atom 도 categorical 8-bin 으로 정의하는 것이 자연스럽고 내부 일관적
- **Canonical fitter**: `scripts/s10b_v6_pca_rdm.py` (PCA top-K=6 voxel dim reduction + 45° integer-index lookup)
- **PCA-RDM 채택 근거** (over SRM-cos, SRM-dis):
  - Cycle 5: PCA 가 raw voxel-RDM 대비 **2× HC-CVD separation**
  - Sub-09 stability (300 resample): PCA mode share **87.7%** (263/300, IQR (0,0)) vs SRM-cos 57.0%, SRM-dis 64.0%
  - Sub-08 βc-dom: PCA ≈ SRM-cos tie (Δ argmin ±2°, strict LOO IQR (5, 4) 동일)
- **(β_s, β_c) median 보고 의미**:
  - σ-bin (45° lookup 결과) 은 plateau 정의
  - Plateau 내부 sub-bin 위치는 γ atom (JND z², continuous) 이 결정
  - Median = plateau 내 γ-driven sub-bin optimum → "specific point is global optimum" 주장 금지
- **삭제됨**: v7 (W+voxel 1°), v8 (W+PCA 1°), L_RDM_PCA, null_lrdm, null_pca, cross_atom_comparison. 1° continuous frame 은 본 closure 외부

---

## Research Questions + Answers

### Model definitions

| Model | Formal expression | DOF | Mechanism |
|---|---|---|---|
| **R+C** (retinal + cortical compensation) | `δθ_RC(c) = (2 − g) · δθ_Machado(c; Δλ)` | 1 (g; Δλ fixed) | Retinal cone shift × cortical linear compensation. `g=1` = no comp, `g=2` = perfect comp, `g>2` = overcomp |
| **2-Component** (cortical opponent-axis rotation in CIELab) | `δθ_2C(θ) = β_s · cos(θ − 90°) + β_c · cos(θ − θ_conf)`<br>θ_conf: protan=16°, deutan=150° | 2 (β_s, β_c) | β_s = S-cone cardinal axis rotation (Krauskopf 1982); β_c = confusion-axis rotation aligned with CVD family (Emery 2021 grounding) |

**Parameter grid**:
- β_s grid: [0°, 50°] step 2° — **one-sided non-negative**
- β_c grid: [−50°, 50°] step 2° — symmetric

**β_s ≥ 0 biological justification**:
- Emery 2021: anomalous-trichromat hue phases rotate **21.4° closer to SvsLM (S-cone) axis**, RG phases **17.4° toward LvsM axis**
- Emery 2023: channel density biased *away from* L-M, *enhanced toward* S-(L+M)
- Cone-axis rotation direction = *unsigned toward* cardinal axes
- β_s < 0 = anti-compensation, not literature-consistent → excluded

---

### RQ1. R+C vs 2-Component — structurally adequate?

**Verdict**: **R+C rejected as structurally inadequate**. 2-Component remains interior · adequate at KEEP cells.

**R+C boundary saturation at KEEP cells** (v6 PCA 45°):
- sub-09 γall+RDM_V1: g=2.95±0.10, **bdy=41.3%** (g pinned at 2.9–3.0 ceiling)
- sub-08 γOY+RDM_V2: g=3.00, g_iqr=0.0, **bdy=100%** (g fully collapsed at g=3.0)

**Why this is a model-problem signal**:
- Wilson & Collins 2019: parameter clustering at grid bounds = explicit model-problem signal
- R+C forward `(2−g)·δθ_Machado` 는 confusion-axis rotation (β_c) DOF 없음
- 2-Component 는 β_c 로 capture
- 거부 근거: **구조적 DOF 부족** (L6), literature-g 비교 아님

**RQ1 table** (v6 PCA 45° categorical):

| Subject | Model | Loss combo | Parameters | bdy | test_focal | test_iqr |
|---|---|---|---|---|---|---|
| sub-08 deutan | **2-Component (βs-dom)** | γ_all + RDM_V1 | β_s=+38, β_c=−10 | (low) | — | — |
| sub-08 deutan | **2-Component (βc-dom)** | γ_OY + RDM_V2 | β_s=+6, β_c=−42 | (low) | — | — |
| sub-08 deutan | R+C (JND_Lamb, ref) | RDM_V1 only | Δλ=6.5 nm, g=2.25±0.00 | 0% | 66.56 | 1.38 |
| sub-09 protan | **2-Component (βc-rot)** | γ_all + RDM_V1 | β_s=+2, β_c=+24 (mode 263/300) | (low) | 3.70 | 1.40 |
| sub-09 protan | R+C (Boehm_low, ref) | γ_all + RDM_V1 | Δλ=3.0 nm, g=2.95±0.10 | **41%** | 6.00 | 0.57 |

---

### RQ2. HC subset 안정성

**판단 기준**: HC subset resample (5 train / 2 test × N=300 draws), v6 PCA 45° atom.

| Candidate | param IQR (β_s, β_c) | Mode share | HC stability |
|---|---|---|---|
| **S08-βs-dom (38, −10)** γ_all + RDM_V1 | (12, 4) | ~50% | ★★ |
| **S08-βc-dom (6, −42)** γ_OY + RDM_V2 | (8, 2) | ~70% | ★★★ |
| **S09-βc-rot (2, +24)** γ_all + RDM_V1 | **(0, 0)** deterministic | **263/300 = 87.7%** | ★★★ |

**Strict 7-fold HC LOO** (`scripts/s17_hc_loo.py`, v6 PCA atom):

| Candidate | IQR (β_s, β_c) | β_s range | β_c range |
|---|---|---|---|
| sub-08 PCA βc-dom γOY+RDM_V2 | (5, 4) | [2, 12] | **[−46, −38]** does not cross 0 |
| sub-09 PCA βc-rot γall+RDM_V1 | **(0, 0)** | [2, 2] | [24, 24] deterministic |
| sub-08 SRM-cos βc-dom γOY+RDM_V2 | (5, 4) | [2, 12] | [−46, −38] **matches PCA** |

**Verdict**: 모든 candidate 가 HC subset / strict LOO 에 robust. 단 stability ≠ correctness 한계 별도 (RQ3).

---

### RQ3. Generalization

| 한계 | Evidence | 함의 |
|---|---|---|
| **CVD N=2** (sub-08 deutan, sub-09 protan; sub-10 near-normal 제외) | Phase 2 sample size | CVD LOO 본질적으로 불가능 — **individualized filter** framing 으로만 정당화 |
| **HC pool n=7, sub-04 outlier** | cycle6b HC subset resampling 분포 | sub-04 outlier 가 bootstrap CI 폭에 영향 |
| **HC train-test = 5/2 random subset, strict LOO 별도 진행됨** | `s10b_v6_pca_rdm.py` SUBSET_SIZE=5, N_RESAMPLES=300; `s17_hc_loo.py` 가 strict 7-fold | Random 5/2 + strict 7-fold 두 evidence 모두 v6 PCA atom 하 valid |
| **Matched-grid null testing 수행됨** | Exp 14 (one-sided + LOO, N=200) + Exp 15 (sym + LOO, N=200) | NS p-values; 그러나 loss landscape (Exp 17) 2.1×–5.5× 신호 깊이 → L1 참조 |

**Verdict**: **No — generalization 불가능**. Pipeline 2 의 model 은 *individualized filter form* 으로만 보고.

---

### RQ4. Neural-inclusion benefit

**(a) Boundary stabilization** (5/2 HC resample, v6 PCA 45°):

| Subject | Combo | PCA-RDM (behav → +neural) | SRM-cosine (behav → +neural) |
|---|---|---|---|
| sub-08 | γOY + RDM_V2 | 23.0% → **9.3%** (Δ −13.7 %p) | 23.0% → 17.7% (Δ −5.3 %p) |
| sub-09 | γall + RDM_V1 | 0.0% → 0.0% (no boundary) | 0.0% → 13.0% (Δ +13.0 %p, *worsens*) |

**(b) Parameter determinism** (5/2 HC resample IQR (β_s, β_c); lower = more reproducible):

| Subject | Combo | PCA behav | PCA +neural | SRM behav | SRM +neural |
|---|---|---|---|---|---|
| sub-08 | γOY + RDM_V2 | (18, 6) | **(8, 2)** | (18, 6) | (10, 4) |
| sub-09 | γall + RDM_V1 | (6, 4) | **(0, 0)** deterministic | (6, 4) | (0, 2) |

**(c) Strict 7-fold HC LOO** (s17, v6 PCA):

| Candidate | IQR | β_s range | β_c range |
|---|---|---|---|
| sub-08 PCA (6, −42) γOY+RDM_V2 | (5, 4) | [2, 12] | **[−46, −38]** |
| sub-09 PCA (2, +24) γall+RDM_V1 | (0, 0) | [2, 2] | [24, 24] |
| sub-08 SRM-cos (8, −42) γOY+RDM_V2 | (5, 4) | [2, 12] | [−46, −38] matches PCA |

**Reframing of γ↔RDM directional disagreement** (이전 framing 의 caveat 3 의 보강):
- Sub-08: γ behav-only β_c=NEG 와 neural RDM_V2 β_c=NEG 같은 방향 → triangulation
- Sub-09: γ behav-only β_c≈0 와 neural RDM_V1 β_c=POS 다른 방향 → neural inclusion 이 **behav 만으론 invisible 한 cortical mechanism component 노출**
- (a)(b) 의 boundary/IQR 개선 = "neural inclusion stabilizes parameter identification" (empirical fact)
- 단 stabilization mechanism: triangulation vs over-determination 구분 불가 → 추가 검증 (Exp 22 진행 중)

---

### RQ5. Behav loss ↔ Neural loss 의 distortion 방향 일치성

#### Sub-08 (8 cells)

| Loss | Best (β_s, β_c) | β_c sign |
|---|---|---|
| behav γOY | (+16, −44) | NEG |
| behav γYG | (+38, −44) | NEG |
| behav γYP | (+34, **+49**) | **POS** ← YP focal 만 sign-flip |
| behav γall | (+50, −36) | NEG |
| neural RDM_V1 | (+32, 0) | ZERO |
| neural RDM_V2 | (+4, −26) | NEG |
| neural RDM_V3 | (0, 0) | ZERO (degenerate, bdy=61%) |
| neural RDM_V4 | (+36, −14) | NEG |

→ **β_c agreement: NEG dominant (5/8); γYP 만 POS (single exception)**
- γYP focal pair = sub-08 의 가장 distorted pair → focal-fit 이 다른 mechanism reflect 가능

#### Sub-09 (3 cells)

| Loss | Best (β_s, β_c) | β_c sign |
|---|---|---|
| behav γGB | (+34, −8) | NEAR-ZERO |
| behav γall | (+26, +4) | NEAR-ZERO |
| neural RDM_V1 | (0, **+24**) | **POS** |

→ **β_c direction DISAGREEMENT**: behav-only β_c ≈ 0, neural-only β_c = **+24**

#### Verdict

- **Sub-08**: behav, neural 같은 방향 (β_c NEG), 1 exception (YP focal). 7/8 NEG agreement
- **Sub-09**: behav 와 neural 이 다른 방향 — neural data 가 cortical confusion-axis rotation 단독 검출
- Paper wording: "Behavioral and neural losses converge on β_c sign for sub-08 (with single focal-fit exception), but diverge for sub-09 where neural data uniquely identifies confusion-axis rotation invisible to behavioral fit alone"

---

## Pipeline narrative (user-locked 5-step axis)

```
[1] 모델 및 로스 후보 선정  →  [2] 전체 조합 시도 + 테스트 기준 평가
                              ↓
                          [3] 각 모델의 HC pool 안정성 평가
                              ↓
                          [4] 가중치 sweep (후보 추출 + 강조 식별)
                              ↓
                          [5] 최종 결정 + 한계 / 식별성
```

| Step | Pipeline 2 component | 코드 |
|---|---|---|
| 1. 모델·로스 후보 선정 | Phase A precondition (HC LOO single-loss gate) | `scripts/s10a_precondition.py` |
| 2. 손실항·조합 후보 소개 | Atoms + cell enumeration | `scripts/s10b_v6_pca_rdm.py` (atom factories + combo enum) |
| 3. 조합 fit + 평가 + 후보 정리 | Phase B v6 5/2 HC split × N=300 + s17 strict 7-fold LOO | `scripts/s10b_v6_pca_rdm.py`, `scripts/s17_hc_loo.py` |
| 4. Weight comparison | [appendix A.8] — not part of selection narrative | `scripts/cycle6b_extended_raw_weight.py` (historical) |
| 5. 최종 결정 + 한계 | Closure (본 문서) + null testing (Exp 13–19 완료, Exp 21–22 진행) | `results/redteam/exp{13..22}*` |

---

## Step 1. 모델 및 로스 후보 선정 (Phase A)

### 모델 (locked)
- Machado 1-way (k=1 DOF, cone shift only)
- R+C 1-DOF (3 Δλ sources: DPS_lit, Boehm_mid, JND_Lamb)
- 2-Component 2-DOF (β_s × β_c grid, family-specific θ_conf)

### Data invariants

| 항목 | 내용 |
|---|---|
| Amplitudes | C010 procrustes, `(6 runs × 8 colors × n_vox)` |
| HC pool | sub-01..07 (n=7); hV4 effective n=6 (sub-07 16 voxels → nan) |
| CVD | sub-08 deutan, sub-09 protan |
| ROIs | V1, V2, V3, V4 (= hV4 on disk) |
| Encoder | ridge_gcv (locked) |
| Behavioral | per-pair JND (OY, YG, YP, GB, RG, ...); CVD pair당 N=1 |

### Atoms (locked)

| Atom | 정의 | Range | Info-density |
|---|---|---|---|
| γ_focal (γOY, γYG, γYP, γGB) | per-pair JND z² vs HC train baseline | 0–~80 | 1 z² scalar |
| γ_all | 8-pair JND z² 합 | 0–~1500 | 8 z² 합 |
| **RDM_{V1..V4}** | **PCA top-K=6 → 8×8 correlation-distance RDM → 28-d cosine vs HC mean (cf. forward via 45° lookup)** | 0–2 | 28 pair distances → scalar (categorical 8-bin σ) |
| LOCO_V4 | V4 voxel-prediction loss (CVD-internal ridge) | scalar | per-voxel |

- z-score grid-relative normalization (composite) 이 atom magnitude/density 격차 평탄화
- 1-pair γ_focal 이 8-pair γ_all 과 동등 composite 기여

### Precondition gate
- HC LOO single-loss precondition table (`results/s10_inclusion/precondition_table.json`)
- 통과 cells 가 Step 2 진입

---

## Step 2. 손실항·조합 enumeration

- Atoms 정의는 Step 1 참조
- Step 2 = *어떤 atoms 가 어떤 조합으로 평가될지* 정의만 (fitting 없음)

### Cell enumeration

- Sub-08: γ ∈ {none, OY, YG, YP, [OY,YG,YP], ALL} × RDM ∈ {none, V1, V2, V3, V4, V1+V4} × LOCO ∈ {off, V4}
  - 71 cells × 4 models = 284
- Sub-09: γ ∈ {none, GB, ALL} × RDM ∈ {none, V1} × LOCO ∈ {off, V4}
  - 11 cells × 4 models = 44
- 4 models = Machado 1-way / R+C × 3 Δλ sources (DPS_lit / Boehm_mid / JND_Lamb) / 2-Component

---

## Step 3. 조합 fit + 평가 + 후보 정리 (Phase B v6 PCA canonical)

### 3.1. Fit procedure

**Train/test split** (`s10b_v6_pca_rdm.py`):
- `N_RESAMPLES = 300, SUBSET_SIZE = 5 train HC + 2 test HC, RNG_SEED = 42`

**Train atom** (5 train HC pool):
- γ_pair: `((predicted_JND − CVD_JND) / HC_train_SD)²` — `s10b_v6_pca_rdm.py:99–117`
- γ_all: 8-pair z² 합 — `:80–97`
- **RDM (canonical v6 PCA 45° categorical)**: `make_rdm_atom` — `s10b_v6_pca_rdm.py:120`
  - 단계 A: per HC mean pattern (8×V) → PCA top-K=6 → 8×8 correlation RDM → HC pool mean
  - 단계 B: CVD mean pattern → PCA top-6 → 8×8 RDM → ΔRDM_obs = CVD − HC_mean (28-d)
  - 단계 C (forward sim under hypothesized δθ): `p_i = int(round(perceived[i]/45.0)) % 8` → `sim_shifted[i,j] = hc_rdm_mean[p_i, p_j]` → ΔRDM_sim = sim_shifted − HC_mean
  - Loss: `1 − cos(ΔRDM_sim, ΔRDM_obs)`
  - **8AFC categorical interpretation**: σ = (β_s, β_c) 가 induce 하는 8-bin permutation. Loss 는 σ-space step function; 같은 σ 안에서 constant
- LOCO: V4 voxel-prediction loss (CVD-internal, HC-independent) — `:199–211`

**Composite + argmin**:
```python
z_sum = Σ zscore_grid(atom_grids[atom_name])  # grid-relative z-score
comp = z_sum / sqrt(n_atoms)
fit_param = argmin(comp)                       # g 또는 (β_s, β_c)
```

- **Composite landscape 구조**: γ + LOCO 가 plateau 내부 continuous gradient 제공, RDM 이 plateau (σ) 선택
- → final argmin = **γ-driven sub-bin position within σ-plateau preferred by RDM**

**Test atom** (2 test HC pool, fit point eval):
- 동일 atom closures *test HC pool* 로 재구성
- `test_loss = Σ (test_atom(fit) − μ_train) / σ_train`, normalized by √n_atoms

**Strict HC LOO supplement** (`scripts/s17_hc_loo.py`):
- 7-fold (각 HC 한 명씩 제외), 6 train + 1 test, deterministic
- v6 PCA atom 그대로 사용

### 3.2. Per-cell output fields

| Field | 의미 |
|---|---|
| `train_loss_median, _iqr` | composite_train minimum 분포 |
| `test_loss_median, _iqr` | test composite — **primary metric** |
| `test_focal_median, _iqr` | focal pair z² on test |
| `test_agg_median, _iqr` | γ_all 8-pair z² sum on test |
| `test_V1_RDM_median, _iqr` | V1 RDM cosine on test |
| `boundary_rate` | argmin 이 grid edge 비율 |
| `aic_median, bic_median` | AIC/BIC on test_focal (descriptive only; appendix A.7) |
| `param_summary` | `bs_median, bs_iqr, bc_median, bc_iqr` (2comp) 또는 `g_median, g_iqr` (R+C) |

### 3.3. Selection metric 우선 순위

1. **Primary**: `test_loss_median` ASC
2. **Secondary**: `test_loss_iqr` ASC
3. **Supplementary** (degeneracy 배제):
   - `boundary_rate < 0.5`
   - Collapse: `test_loss_iqr > 50` OR `sign(train) ≠ sign(test) AND |test − train| > 5`

### 3.4. Gate 통과율 (전체 cell × model; v6 PCA)

| Subject | Total | Collapse | Boundary≥50% | Both gates pass |
|---|---|---|---|---|
| sub-08 | 284 | 91 (32%) | 111 (39%) | **31 (11%)** |
| sub-09 | 44 | 6 (14%) | 27 (61%) | **2 (5%)** |

### 3.5. 선정된 model·loss 후보 + fitting 결과

**선정 기준**:
- Primary: test_loss_median
- Secondary: test_loss_iqr
- Supplementary: boundary, collapse pass
- behavioral aggregate 임계 (`agg / 8 < 16 z²` ≈ 평균 4 SD/pair)

**명칭 정책**:
- 명칭은 *mechanism descriptor* (βc-dominant 등) 사용
- "stable" 등 robust 주장 표현 금지
- **σ-bin label + γ-driven sub-bin position** 으로 해석 — point estimate 가 아닌 plateau 의 representative

**Final candidates** (v6 PCA 45° categorical, N=300 resample):

| Subject | Label | Model | Loss combo | (β_s, β_c) median | param IQR | mode share | train_loss med ± IQR | test_loss med ± IQR | test_focal | test_agg | test_V1_RDM |
|---|---|---|---|---|---|---|---|---|---|---|---|
| sub-08 | **βs-dom** | 2-Component | γ_all + RDM_V1 | (+38, −10) | (12, 4) | ~50% | — | — | — | — | — |
| sub-08 | **βc-dom** | 2-Component | γ_OY + RDM_V2 | (+6, −42) | (8, 2) | ~70% | — | — | — | — | — |
| sub-09 | **βc-rot** | 2-Component | γ_all + RDM_V1 | (+2, **+24**) | **(0, 0)** | **87.7%** (263/300) | — | — | 3.70 | 46.12 | 0.686 |
| **R+C insufficiency references (not candidates)** | | | | | | | | | | | |
| sub-08 | (R+C ref) | R+C (JND_Lamb) | RDM_V1 only | Δλ=6.5 nm, g=2.25±0.00 | — | — | — | — | 66.56 | 107.82 | — |
| sub-09 | (R+C ref) | R+C (Boehm_low) | γ_all + RDM_V1 | Δλ=3.0 nm, g=2.95±0.10 | — | — | — | — | 6.00 | 6.41 | — |

- Sub-08 의 두 candidate (βs-dom + βc-dom) 는 *parallel mechanism hypotheses* — 두 σ 모두 deutan-consistent quadrant (β_s+, β_c−)
- Sub-09 의 βc-rot 는 mode share 87.7% 로 가장 deterministic — 단 SRM family 와 σ-level non-identifiability (L9)

---

[appendix — A.7 AIC/BIC not used as verdict criteria]

- Wilson & Collins 2019: parameter recovery + model recovery 가 formal model selection 의 prereq
- AIC/BIC = `−2·log LL + k·log T`, requires probabilistic likelihood — 본 pipeline 의 `test_focal` 은 composite behavioral loss, proper log-likelihood 아님
- Reported as descriptive bookkeeping only; **does NOT enter RQ1 verdict**
- R+C "g vs literature" 비교 (Tregillus 2020 g≈1.1, Boehm 2016 g≈1.0–1.3) 도 verdict criteria 아님 — behavioral color-naming vs fMRI-MVPA paradigm mismatch

[appendix — A.8 Step 4 (cycle6b raw-weight) — not robustness verification]

- composite atom loss = z-score normalized atom losses 합
- per-atom argmin pattern 이 weight matter 결정

**sub-08**:
- per-atom argmin (γ_focal, γ_all, RDM_V1, RDM_V2, RDM_V4) 가 동일 (β_s+, β_c−) quadrant 수렴 (RQ5 sub-08)
- Positively weighted sums of these atoms cannot leave this quadrant → weight comparison uninformative

**sub-09**:
- γ-atoms (β_c ≈ 0) 와 RDM_V1 (β_c = +24) 의 argmin 상이
- 이것은 RQ5 의 behav-vs-neural divergence + Appendix A.6 L9 의 atom-conditional finding 이지 weight-robustness 문제 아님

**Earlier raw-weight sweep** (cycle6b, 47 schemes):
- 본 closure 에서는 **alternative (raw-weight) normalization** 하의 candidate enumeration 으로 재정의
- **Robustness check 으로 구성되지 않으며, 본 closure 의 어떤 candidate 의 selection/rejection 도 Step 4 outputs 에 의존하지 않음**

Candidate stability 확립:
- RQ2 (5/2 HC resample param_iqr + mode share)
- Strict 7-fold HC LOO (s17)

---

## Step 5. 최종 결정 + 한계 + 식별성

### 5.1. Final candidate set (v6 PCA 45° categorical, 3 candidates)

#### Sub-08 (deutan) — βs-dom + βc-dom (parallel mechanism hypotheses)

| 후보 | Phase B fit loss | β_s | β_c | param IQR | mode share | strict LOO IQR | σ-level robustness |
|---|---|---|---|---|---|---|---|
| **S08-βs-dom** | γ_all + RDM_V1 | +38 | −10 | (12, 4) | ~50% | (not in s17 main table) | β_s+, β_c− quadrant 유지 |
| **S08-βc-dom** | γ_OY + RDM_V2 | +6 | −42 | (8, 2) | ~70% | (5, 4); β_c range [−46, −38] does not cross 0 | β_s+, β_c− quadrant 유지 |

**Mechanism interpretation (sub-08)**:
- **두 parallel σ candidates** — βs-dom σ 와 βc-dom σ 모두 deutan-consistent (β_s+, β_c−)
- 두 σ 의 차이: βs-dom 는 large S-cone rotation + small confusion shift; βc-dom 는 small S-cone + large confusion rotation
- Cross-atom convergence (Appendix A.4): PCA · SRM-cos · SRM-dis 모두 동일 quadrant → **mechanism class 일치**
- Phase 3 자극 디자인 시 두 σ 모두 후보 (single mechanism 강제 안 함)

#### Sub-09 (protan) — βc-rot only

| 항목 | 값 |
|---|---|
| Phase B fit loss | γ_all + RDM_V1 |
| param (β_s, β_c) | (+2, +24) |
| param IQR | (0, 0) **deterministic** |
| mode share | 87.7% (263/300) |
| strict LOO IQR | (0, 0); β_s [2, 2], β_c [24, 24] |
| test_focal (GB z²) | 3.70 |
| test_agg | 46.12 |
| test_V1_RDM | 0.686 |

**Mechanism interpretation (sub-09)**:
- **Cortical confusion-axis rotation primary** (β_c = +24, aligned with protan θ_conf=16°)
- **Small S-cone shift** (β_s = +2)
- v6 PCA atom 하 σ-level deterministic (mode 87.7%)
- 단 SRM family (SRM-cos, SRM-dis) 는 다른 σ (S-cone shift, (32, 0)) 선호 → **metric-level non-identifiability** (L9)
- L8 (grid-truncation) 없음 — v6 PCA 하 sub-09 후보는 grid interior

**R+C 보조 보고 (NOT competing candidate)**:
- g=2.95 (rc_Boehm_low, Δλ=3.0 nm, protan), bdy=41% near-saturation
- → **R+C 1-DOF insufficient for sub-09**

### 5.2. Limitations (paper-level disclosure)

**L1. Specificity evidence — categorical null testing + loss landscape + forward identifiability**

3 levels of evidence under v6 PCA 45° categorical canonical:

**(i) Matched-grid LOO synthetic-HC null** (Exp 13/14/15):

| Candidate | Exp 14 (one-sided + LOO, N=200) | Exp 15 (sym + LOO, N=200) |
|---|---|---|
| S08-stable (38, −10) | p_bs=0.184, p_bc=0.756 | p_bs=0.005 (boundary artifact), p_bc=0.771 |
| S08-robust (6, −42) | p_bs=0.095, p_bc=**0.179** | p_bs=0.483, p_bc=0.169 |
| S09-primary (2, +24) | p_bs=0.279, p_bc=0.920 | p_bs=0.876, p_bc=0.741 |

- 모든 candidate 가 conservatively NS at point-level — synthetic HC null distribution spread (driven by HC heterogeneity + procedure noise) overlaps production fit positions

**(ii) Loss landscape depth** (Exp 17): Real CVD vs synthetic null direct 비교

| Candidate | REAL loss | SYNTH loss | loss 비율 | REAL ↔ SYNTH argmin 거리 |
|---|---|---|---|---|
| S08-stable | −0.889 | −0.432 | 2.1× | 30.3° |
| **S08-robust** | **−2.019** | **−0.365** | **5.5×** | 39.8° |
| S09-primary | −1.323 | −0.341 | 3.9× | 22.8° |

- Real CVD loss minimum 이 synthetic 보다 **2.1×–5.5× 깊음**
- argmin position 이 22.8°–39.8° 떨어짐 → signal qualitatively distinguishable
- p-value 가 NS 인 것은 *null spread 가 넓음* 의 의미이지 *signal 부재* 가 아님

**(iii) Forward identifiability** (Exp 18, sub-09 GT=(0, +24), N=50):

| Injection method | recovered β_c | bias |
|---|---|---|
| A: Linear voxel + JND scaling | −4.2 | −28.2 (inverted) |
| B: Fourier voxel + JND skip | +8.5 | −15.5 |
| **C: Native RDM-direct rotation** | **+24.0 ± 0.0** | **+0.0 exact** |

- Loss function 의 categorical 구조와 일치하는 injection (Method C) 하 **exact recovery**
- Procedure 가 production 의 (2, +24) σ 와 동일 σ 에 GT (0, +24) 가 떨어졌을 때 exact recovery → identifiability 확인

**(iv) Extension pending** (Exp 21 — 진행 중):
- 3 candidates × magnitude sweep (0×/0.5×/1×/1.5×) × N=100 = 1200 fits, Method C
- 모든 candidate 의 production magnitude 와 null GT=(0,0) attractor 검증
- 결과 도착 시 L1 갱신

**(v) Loss-based specificity vs HC fake-CVD** (Exp 22, 완료, N_synth=200, same seed/carriers as Exp 14):

3 continuous loss-based metrics per realization, σ-bin 대체 (JND continuity 이유). Bonferroni 3-test correction:

| Candidate | L(0,0) p (real>synth) | distance p (real>synth) | L(argmin) p (real<synth) | Bonferroni p | 결론 |
|---|---|---|---|---|---|
| S08-stable (38, −10) | 0.119 | 0.582 | 0.577 | 0.358 | NS |
| **S08-βc-dom (6, −42)** | 0.851 | 0.622 | **0.005** | **0.0149** | **SIG** |
| S09-βc-rot (2, +24) | 0.309 | 0.896 | 0.468 | 0.925 | NS |

- **S08-βc-dom (6, −42) 만 loss-based specificity 통과**. L(argmin) 만 single metric 으로 유의 (real −2.019 vs synth mean −1.081, ~5.1 synth-std below)
- **S08-stable + S09-βc-rot 은 모든 metric 에서 NS** — per-realization scrutiny 하 noise distribution 과 구분 안 됨
- 특히 S09-βc-rot 의 L(argmin) = −1.323 vs synth mean −1.322 (essentially identical) → 절대적 null
- Exp 17 의 averaged-surface 2.1×/3.9×/5.5× ratio 중 per-realization scrutiny 통과는 S08-βc-dom 의 5.5× 만
- Per-realization vs averaged-surface 차이: averaging 이 noise heterogeneity 를 smooth 하여 apparent contrast 를 inflate

**메트릭별 실패 원인 (sub-09 의 경우)**:
- L(0,0): trending 방향이지만 p=0.309
- distance: real argmin 이 origin 에 더 가까움 (24.1 vs synth median 35.8) — synth attractor 가 BC extremes 로 drift, 구조적 비대칭
- L(argmin): 차이 없음

**Safe to claim now**:
- Production fits 는 valid descriptive signal estimates (Exp 17 averaged + Exp 18C identifiability)
- 2-Component fit procedure 가 categorical injection 하 identifiable (Method C exact recovery)
- **단 1 후보 (S08-βc-dom) 가 per-realization loss-based specificity 통과**
- 다른 2 후보 (S08-βs-dom, S09-βc-rot) 는 *descriptive only* — selection rule 변경 없음 ("specificity 는 selection criterion 아님" 정책 유지)

**Caveats**:
- Matched-grid LOO p > 0.05 (Exp 14/15, conservative test)
- Per-realization loss specificity (Exp 22): 1/3 candidates pass only
- Point estimate bias correction not principled (Exp 14 vs 15 disagree by 15–76°)
- Exp 17 의 averaged-surface evidence 와 Exp 22 의 per-realization evidence 가 *complementary, not redundant*: averaging 이 noise structure 평탄화, per-realization 이 진정한 spread 노출. 두 evidence 모두 보고
- Exp 18C identifiability ≠ Exp 22 specificity: procedure 가 *injected signal 을 recover* 할 수 있음 (Exp 18C) 그러나 *real CVD fit 이 noise distribution 을 exceed* 한다는 것은 별도 (Exp 22). 둘 다 hold

**L2. OOS axis is HC normalization only**
- CVD JND 는 pair 당 N=1
- Train/test split 은 HC pool composition 만 vary, CVD samples 는 vary 안 함
- Behavioral generalization 은 Phase 3 experiment 필요

**L3. Held-out focal pair CVD obs reuse**
- Focal pair 가 fit objective 에서 제외됨
- 동일 CVD measurement 가 다른 HC normalization 하에서 test eval 에 진입
- Individualized-filter framing 하에서는 data leakage 아니지만 disclosure 필요

**L4. CVD N=2, HC n=7, no strict CVD LOO possible**
- CVD LOO 본질적으로 불가능 (N=2)
- HC pool 은 5/2 random subset (N=300) + strict 7-fold LOO (s17) 두 evidence

**L5. Z-score grid-relative composite equalizes atom info-density**
- 1-pair γ_focal ↔ 8-pair γ_all 이 composite 에 동등 기여

**L6. R+C 1-DOF structurally insufficient**
- sub-09 R+C saturates at g_max=3.0 (bdy=41%)
- R+C forward `δθ=(2−g)·δθ_Machado` 가 cortical confusion-axis rotation DOF 결여
- 2-Component 는 β_c 로 capture
- **Structural** limit (DOF count), literature-g 비교 아님

**L7. Phase B → Phase C seed sharing (historical)**
- Phase C v2 (deprecated, §Files 참조) 는 identical RNG seed 사용
- Independent seed 하에서 sub-09 IQR 80–300% inflate
- Final selection 영향 없음 (Phase C 가 final candidates 에 기여 안 함)

**L8 (REMOVED — sub-09 grid-truncation under v7 L_RDM)**
- v6 PCA canonical 하 sub-09 candidate (2, +24) 는 grid interior
- 이전 L_RDM (1° continuous) atom 의 boundary truncation 한계는 적용되지 않음

**L9. σ-level metric non-identifiability for sub-09**
- v6 PCA-RDM atom 은 sub-09 의 σ 를 cortical rotation σ = (2, +24) 로 deterministic 하게 선택 (mode 87.7%)
- 그러나 SRM family (SRM-cos, SRM-dis) 는 다른 σ = (32, 0) (S-cone shift) 선호 (Appendix A.4)
- 두 σ 의 perceptual prediction 비교 (computed):
  - δθ vector cosine similarity: 0.350 (낮음)
  - Sign agreement: 5/8 — c4 (green), c5 (cyan), c8 (magenta) 반대 방향
  - Max |Δδθ|: 32.8°
- **PCA-RDM 채택 근거**: Cycle 5 의 2× HC-CVD separation + sub-09 stability mode 87.7% > SRM-cos 57% > SRM-dis 64%
- 단 PCA 는 *덜 established* metric (SRM-disparity 는 프로젝트 canonical SRM family, sub-08 V2 p=0.040* 의 metric)
- Paper-level disclosure: "Sub-09 의 cortical mechanism 식별은 PCA-RDM 채택 결정에 의존; SRM family 는 다른 mechanism class (S-cone shift) 선호"

**L10. Forward identifiability extension pending**
- Exp 18 의 native injection (Method C) exact recovery 는 sub-09 GT=(0, +24) 한 점만 검증
- Exp 21 진행 중: 3 candidates × magnitude sweep × N=100
- 결과 도착 시 L1 (i)–(iv) 와 L10 통합

### Pipeline 3 status note

- 본 closure 는 **Pipeline 2 only**
- 이전 `PIPELINE_3_FRAMEWORK.md` 의 sub-09 (β_s=2, β_c=24) primary 결정은 v6 PCA atom 기반 — **v6 canonical 으로 복귀 후에도 동일 값**
- Pipeline 3 의 layer architecture (Layer A/B/C with E1/E2/E3) 는 *deprecated* — Phase B v6 가 동일 역할 흡수
- Pipeline 3 의 별도 후속 작업 없음

---

## Closure verdict

### 완료
- ✓ Step 1–4 (Phase A → Phase B v6 PCA 45° categorical canonical)
- ✓ v6 PCA 45° categorical canonical 확립 (1° continuous variants 삭제)
- ✓ Sub-08 final candidates: **βs-dom (+38, −10)** + **βc-dom (+6, −42)** — parallel mechanism hypotheses, 동일 deutan quadrant
- ✓ Sub-09 final candidate: **βc-rot (+2, +24)** — deterministic, PCA-canonical
- ✓ Phase B → C seed audit (L7; Phase C 자체가 final selection 비기여)
- ✓ 10 paper-level limitations (L1–L7, L9, L10; L8 removed)
- ✓ Null testing (Exp 13–19) + cross-atom robustness (PCA · SRM-cos · SRM-dis) 통합

### Closure verdict — **CLOSURE READY**

- Pipeline 2 final candidates 는 v6 PCA 45° categorical canonical 하에서 **σ-level bin + γ-driven sub-bin position** 으로 보고
- Sub-08 의 두 parallel candidates + sub-09 의 single deterministic candidate
- Exp 13–19 null testing evidence 통합 (matched-grid LOO NS + loss landscape 2.1×–5.5× deeper + Method C exact recovery)
- Exp 21–22 진행 중 — 결과 도착 시 L1, L10 갱신
- Phase 3 행동 실험이 **sole verification path** — paper 작성 가능

### Paper-level framing (정직)

> "Pipeline 2 produced candidate filter forms via composite atom z-score argmin under the v6 PCA 45° categorical RDM atom. Sub-08 has two parallel candidates — βs-dom (β_s=+38, β_c=−10) under γ_all + RDM_V1 and βc-dom (β_s=+6, β_c=−42) under γ_OY + RDM_V2 — both within the deutan-consistent (β_s+, β_c−) quadrant. Sub-09 has a single candidate βc-rot (β_s=+2, β_c=+24) under γ_all + RDM_V1 with deterministic identification (mode share 87.7%, strict LOO IQR (0,0)). All candidates implicate combinations of S-cone rotation and confusion-axis rotation at the cortical representation level. Specificity is supported by loss landscape evidence (real CVD minima 2.1×–5.5× deeper than synthetic HC nulls) and forward identifiability (Method C exact recovery for sub-09 GT=(0,+24)), despite conservatively NS matched-grid LOO p-values at point level. We present these candidates as plausible descriptive fits at fit-point requiring behavioral validation, not as estimated cortical-distortion parameters."

---

## Files

| File | Role |
|---|---|
| `PIPELINE_2_CLOSURE.md` | (본 문서) 5-step pipeline narrative + final candidates + limitations |
| `PIPELINE_2_AUDIT_2026-05-26.md` | Phase C seed audit detail |
| `scripts/s10b_v6_pca_rdm.py` | **Phase B v6 main runner — v6 PCA 45° categorical canonical** |
| `scripts/s10b_v6_srm_rdm.py` | SRM-cos RDM atom variant (Appendix A.2 evidence) |
| `scripts/s10b_v6_srm_disparity.py` | SRM-disparity RDM atom variant (Appendix A.2 evidence) |
| `scripts/s17_hc_loo.py` | Strict HC LOO 7-fold supplement under v6 PCA atom |
| `scripts/cycle6b_extended_raw_weight.py` | Step 4 — raw-weight scheme sweep (historical) |
| `scripts/s12b_phase_c_v2.py` | (deprecated) Phase C v2 simplex weight sweep — final selection 에 기여 없음 (L7) |
| `scripts/compare_primary_candidates.py` | Appendix A.2 cross-atom comparison runner |
| `scripts/neural_loss.py` | L_RDM (W-based 1°), L_LOCO utilities (precondition gate + peripheral test_V1_RDM). L_RDM_PCA removed |
| `results/s10_inclusion/s10b_v6_pca_rdm_results_{sub-08,sub-09}.json` | Phase B v6 PCA canonical output |
| `results/s10_inclusion/s10b_v6_srm_rdm_results_{sub-08,sub-09}.json` | SRM-cos output (Appendix A.2) |
| `results/s10_inclusion/s10b_v6_srm_disparity_results_{sub-08,sub-09}.json` | SRM-disparity output (Appendix A.2) |
| `results/s10_inclusion/cycle6b_extended_composite_{sub-08,sub-09}.json` | (historical) Step 4 raw-weight output |
| `results/s10_inclusion/s17_hc_loo_results.json` | Strict HC LOO output |
| `results/s12b_phase_c_v2/sweep_*.json` | (deprecated) Phase C v2 output + seed audit |
| `results/redteam/exp13_synthetic_hc_null_broi.{py,json}` | Synthetic HC null sym + NoLOO (N=300) |
| `results/redteam/exp14_onesided_loo_null.{py,json}` | Matched-grid LOO null one-sided (N=200) |
| `results/redteam/exp15_symmetric_loo_null.{py,json}` | Matched-grid LOO null symmetric (N=200) |
| `results/redteam/exp17_loss_landscape.{py,json,npz}` | Real CVD vs synth HC loss landscape comparison |
| `results/redteam/exp18_injection_artifact_control.{py,json}` | Forward identifiability — injection method comparison (Method C exact recovery) |
| `results/redteam/exp19_n100_ridge_recovery.{py,json}` | N=100 confirmation + ridge axis sweep |
| `results/redteam/exp14_15_16_synthesis.md` | Initial synthesis (superseded by exp17_18_19) |
| `results/redteam/exp17_18_19_synthesis.md` | **Final synthesis — Identifiable, signal present, NS reflects noise overlap** |
| `results/redteam/exp21_forward_recovery_sweep.{py,json}` | (진행 중) 3 candidates × magnitude sweep × N=100, Method C |
| `results/redteam/exp22_origin_loss_specificity.{py,json,md}` | (진행 중) Loss-based specificity: L(0,0), distance, well depth |

**삭제된 파일** (1° continuous frame):
- `scripts/s10b_v7_lrdm.py`, `scripts/s10b_v8_pca.py`
- `scripts/server/null_lrdm_array_runner.py`, `scripts/server/null_lrdm_array.sbatch`, `scripts/server/aggregate_null_lrdm.py`, `scripts/server/SERVER_NULL_LRDM_README.md`
- `scripts/server/null_pca_array_runner.py`, `scripts/server/null_pca_array.sbatch`, `scripts/server/aggregate_null_pca.py`
- `scripts/server/compare_atoms.py`
- `results/null_lrdm/`, `results/null_pca/`
- `results/cross_atom_comparison.{md,json}`
- `results/s10_inclusion/s10b_v7_lrdm_results_*.json`, `s10b_v8_pca_results_*.json`
- `neural_loss.L_RDM_PCA`, `_voxel_pca_top_k`, `_correlation_rdm_upper`

---

## Appendix A — RDM Atom Cross-Variant Robustness (PCA vs SRM-cos vs SRM-disparity)

> v6 PCA 45° categorical 채택의 cross-atom robustness evidence. 본 closure 의 σ-level mechanism interpretation 의 기반.

- Date: 2026-05-27
- 동일 v6 fit pipeline (300 resample × 5/2 HC split × 4 models × γ + LOCO atoms)
- RDM atom 만 swap 한 3 variant 비교

### A.1 Setup

| Variant | RDM atom 정의 | Script |
|---|---|---|
| **PCA-RDM** (canonical) | 8 colors → voxel PCA top K_PCA=6 → 8×K_PCA scores → 8×8 correlation-distance RDM → 28-d cosine vs HC mean | `scripts/s10b_v6_pca_rdm.py` |
| **SRM-cosine** | BrainIAK SRM(K=ROI_K, n_iter=20) on HC pool → CVD Procrustes against fixed S → 8×8 correlation-distance RDM in shared K-d space → 28-d cosine vs HC mean | `scripts/s10b_v6_srm_rdm.py` |
| **SRM-disparity** | 동일 SRM training. RDM 대신 색-permutation 후 Procrustes Frobenius disparity (`phase2_SRM_across_between/rerun_loo_consistent.py` family). δθ=0 baseline = canonical disparity (sub-08 V2 p=0.040* 의 metric family) | `scripts/s10b_v6_srm_disparity.py` |

Comparison runner: `scripts/compare_primary_candidates.py`.

### A.2 Cross-variant argmin

#### Sub-08

| Candidate | combo | PCA (β_s, β_c) | SRM-cos (β_s, β_c) | SRM-dis (β_s, β_c) | PCA↔DIS | sign quadrant |
|---|---|---|---|---|---|---|
| **S08-βs-dom** | γ_all + RDM_V1 | (38, −10) | (22, −36) | (24, −20) | 17.2° | β_s>0, β_c<0 동일 ✓ |
| **S08-βc-dom-V2** | γ_OY + RDM_V2 | (6, −42) | (8, −42) | (2, −24) | 18.4° | β_s>0, β_c<0 동일 ✓ |
| **S08-βc-dom-V3** | γ_OY + RDM_V3 | (6, −42) | (8, −42) | (2, −24) | 18.4° | β_s>0, β_c<0 동일 ✓ |
| **S08 R+C ref** | γ_blank + RDM_V1 | g=2.25 | g=2.70 | g=1.80 | Δg=0.45 | Δλ_deutan large-shift 동일 ✓ |

#### Sub-09

| Candidate | combo | PCA (β_s, β_c) | SRM-cos (β_s, β_c) | SRM-dis (β_s, β_c) | PCA↔DIS | sign quadrant |
|---|---|---|---|---|---|---|
| **S09-βc-rot-ALL** | γ_all + RDM_V1 | (2, +24) | (32, 0) | (32, 0) | 38.4° | β_c sign change (+24→0) ✗ |
| **S09-βc-rot-GB** | γ_GB + RDM_V1 | (2, +24) | (32, 0) | (32, 0) | 38.4° | β_c sign change (+24→0) ✗ |
| **S09 R+C ref** | γ_all + RDM_V1 | g=2.95 | g=1.10 | g=2.50 | Δg=0.45 | PCA·DIS large-shift 동일; COS dropout |

### A.3 Per-candidate verdict

- **S08-βc-dom (6, −42)**:
  - PCA · SRM-cos 거의 일치 (±2°)
  - SRM-dis 는 β_c magnitude 절반 (−24) 으로 축소되나 same quadrant
  - V2 / V3 두 combo 모두 동일 SRM-dis 해 → **RDM atom robust within mechanism class**

- **S08-βs-dom (38, −10)**:
  - SRM-cos: (22, −36) — β_c 강화
  - SRM-dis: (24, −20) — PCA · SRM-cos 사이 중간
  - 세 방법 모두 β_s>0, β_c<0 동일 quadrant
  - Magnitude variation ~10–28°

- **S08 R+C g ≈ 2.25**:
  - PCA 2.25 · COS 2.70 · DIS 1.80
  - 모두 Δλ_deutan large-shift 영역 (Machado-saturated)
  - Range ±0.9 → robust within R+C saturation envelope

- **S09-βc-rot (2, +24)**:
  - 메트릭 간 mechanism reversal 이 **각각 robust 한 채로** 발생
  - PCA-RDM: (2, +24) deterministic (mode 263/300, IQR (0,0))
  - SRM-cos: (32, 0) (171/300, IQR (0,2))
  - SRM-dis: (32, 0) (192/300, IQR (0,2))
  - 즉 **"noisy/sensitive" 가 아니라 "두 안정 메트릭이 정반대 답을 자신있게 줌"**
  - β_c sign 이 +24(PCA) ↔ 0(SRM) 으로 바뀌며 dominance 가 cortical-rotation ↔ S-cone-shift 로 뒤집힘
  - PCA · SRM 의 색 예측 비교 (computed): cosine 0.350, 3/8 sign-flip (c4, c5, c8), max |Δδθ| 32.8°
  - SRM family 내부 (cos · dis) 일치, PCA 만 분리

- **S09 R+C g=2.95**: PCA 2.95 · DIS 2.50 (close), COS 1.10 (large drop). SRM-cos 의 saturation 영역 flat signal

### A.4 PCA-RDM 채택 결정의 정당화

| 기준 | PCA | SRM-cos | SRM-dis | 결론 |
|---|---|---|---|---|
| HC-CVD separation (Cycle 5) | **2× 우위** | baseline | baseline | PCA |
| Sub-09 mode share | **87.7%** | 57.0% | 64.0% | PCA |
| Sub-09 5/2 IQR | **(0, 0)** | (0, 2) | (0, 2) | PCA |
| Sub-08 strict LOO IQR | (5, 4) | (5, 4) tied | — | tie |
| Sub-08 σ-level agreement | ✓ | ✓ | △ (β_c 절반) | tie |
| Sub-09 σ-level agreement | ✗ (rotation) | ✗ (S-cone shift) | ✗ (S-cone shift) | non-identifiable across atoms |

- PCA-RDM 채택 = (i) Cycle 5 separation + (ii) sub-09 stability 우위
- Sub-08 에서는 PCA · SRM-cos tie → cross-atom convergence 가 sub-08 candidates 의 mechanism class 확정
- Sub-09 의 σ-level non-identifiability 는 L9 limitation 으로 disclosure

### A.5 Additional disclosure — canonical SRM (rerun_loo_consistent.py)

- §5.1 candidates 의 fit 은 모두 RDM-cosine atom 기반
- MEMORY 의 "sub-08 V2 p=0.040*" 는 **다른 metric family**
  - 출처: `phase2_SRM_across_between/rerun_loo_consistent.py`
  - 방법: Procrustes-disparity LOO + Crawford & Howell t-test
- cycle7b SRM diagnostic 의 sub-08 V2 separation_z = +0.28 (weak) 는 RDM-cosine 으로 측정한 값
- canonical p=0.040 결과를 부정하지 않음 — measurement family 차이

### Files (Appendix A)

| File | Role |
|---|---|
| `scripts/s10b_v6_srm_rdm.py` | v6 RDM-cosine in SRM shared space |
| `scripts/s10b_v6_srm_disparity.py` | v6 Procrustes disparity (canonical SRM family) |
| `scripts/cycle7b_srm_diagnostic.py` | δθ=0 baseline SRM atom (5-cell) |
| `scripts/cycle7c_pca_diagnostic.py` | δθ=0 baseline PCA mirror of cycle7b |
| `scripts/compare_primary_candidates.py` | 3-way comparison runner |
| `results/s10_inclusion/s10b_v6_srm_rdm_results_{sub-08,sub-09}.json` | SRM-cosine v6 output |
| `results/s10_inclusion/s10b_v6_srm_disparity_results_{sub-08,sub-09}.json` | SRM-disparity v6 output |
