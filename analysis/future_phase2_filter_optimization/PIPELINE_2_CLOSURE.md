# Pipeline 2 Closure — 5-Step Selection Axis

- **Status**: CLOSURE READY (v6 PCA 45° categorical RDM atom canonical; 1° continuous variants removed) — verification complete; 4-test verdict 12/12 FAIL recorded as descriptive limitation
- **Date**: 2026-06-01
- **Verification**: see `closure.md` for 4-test summary (param recovery / (0,0) algorithm validation / HC pseudo-CVD / label permutation)
- **현행 main candidate = 2개** (2026-06): **S08-robust (+6, −42) deutan** · **S09-primary (+2, +24) protan**. **βs-dom / S08-stable (+38, −10)은 dropped** — 본 문서의 βs-dom 행(RQ2·RQ4·App.A 등)은 verification 스냅샷으로 보존된 이력이며 *현행 후보 아님*.

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

**RQ1 table** (v6 PCA 45° categorical) — 후보 (β_s, β_c) 의 평면 시각화는 §5.1 figure (`fig_candidates_param_space.png`) 참조:

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

**두 generalization 축 구분 (중요)**:
- **(i) CVD-level generalization** = "다른 CVD 피험자로 전이되는가". CVD N=2 → **불가능**.
  Pipeline 2 model 은 *individualized filter form* 으로만 보고. (위 verdict)
- **(ii) HC-reference-pool generalization** = "필터가 anchor 된 HC reference pool 안에서,
  본 적 없는 HC 로 전이되는가". 7-fold HC-LOO 로 **검증 가능하며 positive** —
  RQ4(e) 의 held-out test-loss 참조 (s18: 안정적 fit 이 held-out HC 를 no-correction 보다
  잘 예측, 7/7 fold). 이는 (i) 과 별개의 축이며, overfitting 배제 증거.

**Verdict**: CVD-level = **No (N=2)**; HC-reference-pool = **Yes (s18 test-loss positive)**.
필터는 individualized form 으로 보고하되, HC-LOO 일반성은 별도 근거로 보강.

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

**(d) Standalone term fits — neural-only as its own signal, + behavioral-benefit asymmetry**
(`scripts/s18_heldout_predictive.py`, full 7-HC pool; reports each term standalone, not just the increment):

| Subject | combined (prod) | γ-only (behav) | RDM-only (neural) |
|---|---|---|---|
| sub-08 (S08-robust) | (6, −42) | (6, −42) | **(4, −26)** non-degenerate |
| sub-09 (S09-primary) | (2, +24) | (26, +4) | **(0, +24)** non-degenerate |

- **Neural-only signal exists for BOTH subjects** — RDM-only fits are non-trivial /
  non-degenerate for each (S08 β_c=−26, S09 β_c=+24). So "neural carries its own signal"
  is symmetric across subjects.
- **Behavioral benefit is asymmetric:**
  - **sub-08 = YES (triangulation).** γ-only beats no-shift strongly (held-out ΔL=−13.8,
    neg_frac 0.71) and lands β_c<0, the *same* direction as neural RDM-only (−26). Both
    terms independently support the deutan cortical direction; the combined fit is not
    driven by one term.
  - **sub-09 = NO / weak.** γ-only gives β_c≈+4 (≈0) and does **not** beat no-shift
    (held-out ΔL=+0.01, neg_frac 0.43). The production (2,+24) is essentially the
    **neural(RDM)-only fit**; behavior does not support it.
- Consistent with (a): neural inclusion stabilizes/sharpens for sub-08 (boundary 23→9%),
  while for sub-09 the filter rests on the neural term alone (behav-only is silent).
- Stabilization mechanism for sub-08: triangulation vs over-determination not separable
  → further check (Exp 22 in progress).

**(e) Held-out test-loss in LOO — does the stable value beat no-correction?** (`s18`;
the train fit's predictive loss on the held-out HC vs the (0,0) no-correction baseline,
NOT argmin stability, NOT closeness-to-oracle):

| Candidate (combined=prod fit) | RDM L_test med | RDM ΔL vs (0,0) med | folds beating (0,0) | grid pct med | NC_rdm med | frac_above_nc med | γ ΔL vs (0,0) |
|---|---|---|---|---|---|---|---|
| sub-08 (6,−42) | 0.594 | **−0.406** | **7/7** | 0.05 (beats 95%) | 0.240 | 0.484 | −13.8 (5/7) ✓ |
| sub-09 (2,+24) | 0.528 | **−0.472** | **7/7** | 0.08 (beats 92%) | 0.274 | 0.325 | −0.55 (4/7) ≈null |

- **Neural (RDM) stable value is GOOD for BOTH subjects**: ΔL vs (0,0) < 0 on every
  held-out HC → predicts held-out geometry better than no-correction. (0,0)=1.0 is the
  no-structure floor; the grid percentile (production fit ≈92–95%) confirms the win is
  non-trivial (an arbitrary shift centers near 1.0), not just beating the degenerate floor.
- **Behavioral (γ)**: good for sub-08 (ΔL=−13.8), ≈null for sub-09 (ΔL=−0.55, 4/7) —
  reinforces (d)'s asymmetry.
- **Stable + good, but not value-crowning.** Stable train fit (s17: S08 β_c[−46,−38];
  S09 (2,24) deterministic) + beats-no-correction are *both* positive, and *both* coexist
  with the closure's ~20° non-identifiability (Test 2a): one **broad, shallow low-loss
  basin** — consistently centered (stable), shared + beats (0,0) (good), ~20° wide
  (absolute value unresolved). The value is **in the good region**, not point-resolved.
  Detail + retraction of an earlier over-claim (gen_gap/oracle was the wrong reference;
  per-fold oracle β_c flips = single-HC noise, NOT the test-loss):
  `results/s10_inclusion/s18_INTERPRETATION.md`.
- **Noise ceiling (Lage-Castellanos et al. 2018)**: split-half NC from held-out HC amplitude
  reliability = 0.240 (S08) / 0.274 (S09). frac_above_nc = 0.484 / 0.325 — production fit은
  "noise ceiling → no-correction floor" 가용 범위의 33–48% 위치. 이는 broad shallow basin
  해석(§Theme A)과 일관. **Caveat**: NC는 HC-side split-half만 추정; CVD amplitude 노이즈
  (ΔRDM_obs의 CVD 항)는 미포함 → 실제 NC ≥ 보고값. 코드: `s18_heldout_predictive.py`
  `compute_rdm_nc_splithalf()` (10 balanced 3-3 splits of held-out HC's 6 runs).

**(f) Methods note — stability vs overfitting/generalization, and how each term is scored**
(`s18`; supports RQ2 stability ↔ RQ3(ii) generalization).

*Two questions, two estimators (the chain):*
- **Stability (RQ2/c, s17)** = "HC 부분집합을 바꿔 refit 하면 같은 (β_s,β_c)?" → **estimator
  분산(재현성)**. 한계: 모델이 misspecified 여도 모든 부분집합이 같은 *틀린* 값으로 수렴 가능 →
  재현성은 정확성·과적합을 검출 못 함.
- **Held-out test-loss (RQ4/e, s18)** = "6 HC 로 fit 한 값이 *본 적 없는* 7번째 HC 도 설명?"
  → **held-out 예측**. (a) overfitting 과 (b) 값의 임의성을 배제. stability 를 *넘어서는*
  정보. 단 ~20° basin 폭(Test 2a) 안의 절대값은 고정 못 함 → "good region", not point.
- 종합: **재현 가능(stable) + 무보정보다 예측 우수(generalizes) + 값은 ±~20° 불확실** —
  하나의 broad shallow basin 기하로 모두 설명. specificity claim 아님(§0).

*과적합 방지 설계 (s18 가 plug-in 이 아닌 이유):*
- fold 마다 (β_s,β_c) 를 **6 train HC 로 재추정** (`composite_argmin`); production (6,−42)/(2,24)
  를 대입하지 않음. 고정된 것은 *모델 구조*(combo·family·θ_conf) 와 CVD target 데이터뿐.
  HC 만 train(6)/test(1) 분할, CVD 는 항상 target.
- 두 term 모두 **무보정 baseline (δθ=0) 대비 개선 ΔL** 로 채점 (uniform).

*γ vs RDM — held-out HC 의 역할이 다름 (user-agreed 비대칭):*
- **RDM = 진짜 held-out 예측**: held-out HC 의 *기하구조(ΔRDM_obs)* 가 target. L_RDM =
  1−cos(ΔRDM_sim(δθ), ΔRDM_obs). (0,0) → ΔRDM_sim=0 → loss≡1.0 = no-structure floor;
  ΔL=L(fit)−1.0, percentile 이 floor-trivial 여부를 de-confound.
- **γ = reference-robustness**: held-out HC 의 JND 는 *baseline 입력*, target 은 *고정 CVD JND*.
  `pred = HC_baseline_JND × (d_phys / d_perceived(δθ))`, L_γ = mean((pred−CVD_JND)/train_SD)².
  δθ=0 → pred=HC baseline (무보정); ΔL<0 = fit 왜곡이 HC baseline 에서 출발해도 CVD JND
  anomaly 를 무보정보다 잘 재현. HC 가 target 이 아니므로 엄밀한 held-out 예측은 아님 → 라벨 분리.
  NC 미적용: CVD JND 는 단일 측정값(N=1 per pair), split-half 추정 불가.
- **RDM NC 비대칭**: NC (0.240/0.274) 는 HC-side amplitude noise만 반영; CVD amplitude noise는
  별도. γ 에는 NC 가 없으므로 γ ΔL 과 rdm frac_above_nc 는 직접 비교 불가.
- 코드: `scripts/s18_heldout_predictive.py` `rdm_heldout_eval`(L173), `gamma_heldout_loss`(L140),
  fold 루프(L223–262).

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

1. **Gate**: `boundary_rate < 0.5` + collapse 배제
   (`test_loss_iqr > 50` OR `sign(train) ≠ sign(test) AND |test − train| > 5`)
2. **Primary**: `test_loss_median` ASC — composite z-score (`Σ zscore_grid(atom) / √n_atoms`).
   각 atom을 자신의 grid 분포 대비 표준화하므로 combo 간 scope 차이(focal vs all-pair)는
   z-score reference 에 흡수됨 → 값 비교 유효. 단 selection은 subject 내부에서만.
3. **Secondary**: `test_loss_iqr` ASC — parameter stability
4. **Supplementary**: `rdm L_test med` ASC (s18 7-fold strict LOO) — neural component
   고정 criterion (L_RDM = 1−cosine, 모든 combo 동일 공식). behavioral equivalent 없으므로
   primary 진입 불가; composite selection 이후 neural validation 역할.

### 3.4. Gate 통과율 (전체 cell × model; v6 PCA)

| Subject | Total | Collapse | Boundary≥50% | Both gates pass |
|---|---|---|---|---|
| sub-08 | 284 | 91 (32%) | 111 (39%) | **31 (11%)** |
| sub-09 | 44 | 6 (14%) | 27 (61%) | **2 (5%)** |

### 3.5. 선정된 model·loss 후보 + fitting 결과

**선정 기준** (→ §3.3 상세):
- Gate: boundary_rate < 0.5 + collapse 배제
- Primary: test_loss_median (composite z-score)
- Secondary: test_loss_iqr
- Supplementary: rdm L_test med (s18 7-fold LOO, neural fixed criterion) + behavioral aggregate 임계 (`agg / 8 < 16 z²` ≈ 평균 4 SD/pair)

**명칭 정책**:
- 명칭은 *mechanism descriptor* (βc-dominant 등) 사용
- "stable" 등 robust 주장 표현 금지
- **σ-bin label + γ-driven sub-bin position** 으로 해석 — point estimate 가 아닌 plateau 의 representative

**Final candidates** (v6 PCA 45° categorical, N=300 resample):

| Subject | Label | Model | Loss combo | (β_s, β_c) median | param IQR | mode share | train_loss med ± IQR | test_loss med ± IQR | bdy | test_focal | test_agg | test_V1_RDM |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sub-08 | ~~βs-dom~~ (**DROPPED** 2026-06-01) | 2-Component | γ_all + RDM_V1 | (+38, −10) | (24, 22) | ~50% | −1.24 ± 0.86 | −1.14 ± 0.86 | 0.000 | — | — | — |
| sub-08 | **βc-dom** ✓ | 2-Component | γ_OY + RDM_V2 | (+6, −42) | (8, 2) | ~70% | **−2.89 ± 0.27** | **−2.36 ± 2.15** | 0.093 | — | — | — |
| sub-09 | **βc-rot** ✓ | 2-Component | γ_all + RDM_V1 | (+2, **+24**) | **(0, 0)** | **87.7%** (263/300) | **−1.68 ± 0.46** | **−1.54 ± 1.42** | 0.000 | 3.70 | 46.12 | 0.686 |
| **R+C insufficiency references (not candidates)** | | | | | | | | | | | | |
| sub-08 | (R+C ref) | R+C (JND_Lamb) | RDM_V1 only | Δλ=6.5 nm, g=2.25±0.00 | — | — | −1.30 ± 0.23 | −0.88 ± 1.38 | 0.000 | 66.56 | 107.82 | — |
| sub-09 | (R+C ref) | R+C (Boehm_low) | γ_all + RDM_V1 | Δλ=3.0 nm, g=2.95±0.10 | — | — | −1.10 ± 0.11 | −0.86 ± 0.57 | 0.413 | 6.00 | 6.41 | — |

- Sub-08 βs-dom 은 2026-06-01 closure 에서 **DROPPED** (test_loss 및 param IQR 열등; IQR=(24,22) vs βc-dom (8,2))
- Sub-09 의 βc-rot 는 mode share 87.7% 로 가장 deterministic — 단 SRM family 와 σ-level non-identifiability (L9)

**Gate-2-passed 비교 (bdy < 0.5, test_loss_median 기준, 2comp only)**:

| Subject | N cells | 선정 rank | 선정값 | 2위 | 최하위 |
|---|---|---|---|---|---|
| sub-08 | 25 | **#1** | −2.36 (iqr=2.15, bdy=0.093) | −2.20 (iqr=4.03, bdy=0.067) | +0.78 |
| sub-09 | 4 | **#1** | −1.54 (iqr=1.42, bdy=0.000) | −1.52 (iqr=1.41, bdy=0.000) | −0.03 |

**R+C Gate-2-passed 최우수값 (참고용 — model rejection 이전)**:

| Subject | Best R+C test_loss | combo | 비고 |
|---|---|---|---|
| sub-08 | −2.39 (iqr=1.24, bdy=0.000) | γ_\|RDMV2\|LOCO\|rc_Boehm_mid | LOCO 포함 combo; primary R+C (bdy=100%) rejected |
| sub-09 | −2.38 (iqr=1.36, bdy=0.000) | γ_\|RDMV1\|LOCO\|rc_DPS_lit | LOCO 포함 combo; primary R+C (bdy=41%) rejected |

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

**Figure (앞부분 통계 결과)** — `results/figures/fig_candidates_param_space.png` (재현 `scripts/fig_candidates_param_space.py`; (β_s, β_c) 는 v6 fit 결과 JSON 의 per-subset median 직접 read → Appendix A.2 표 재현):

![Candidate filters in (β_s, β_c) space](results/figures/fig_candidates_param_space.png)

- 세 후보를 (β_s, β_c) 평면에 표시. 각 후보당 PCA(production, ★) · SRM-cos(●) · SRM-dis(▲) 세 metric argmin 을 얇은 선으로 연결 → cross-metric spread
- **Sub-08 (βs-dom, βc-dom)**: 세 metric 모두 deutan-consistent 하단 (β_s>0, β_c<0) 에 수렴 → mechanism class 일치 (RQ1·App. A.3)
- **Sub-09 (βc-rot)**: PCA (+2, +24) 와 SRM (32, 0) 가 β_c=0 선을 가로질러 크게 벌어짐 → **σ-level metric non-identifiability** (Theme A.2 / 구 L9)
- R+C 후보(1-DOF g)는 (β_s, β_c) 좌표가 아니므로 본 평면에서 제외 (RQ1 saturation 은 본문 표 참조)

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

한계는 **3개 큰 주제**로 묶어 보고한다 — **A: parameter 식별성·specificity**, **B: 표본·out-of-sample 구조**, **C: 모델링 프레임 선택**. 개별 라벨(구 L1–L9)은 주제 하위에 재배치하고 traceability 를 위해 괄호로 병기한다. (해소·비적용된 구 L7 seed-공유, 구 L8 grid-truncation, 구 L10 pending-experiment 은 삭제 — 구 L10 의 완료된 결과는 Theme A.1 (iv)–(v) 에 통합됨.)

```
§5.2 Limitations 분류도
│
│  [삭제]  구 L7 seed-공유 · 구 L8 grid-truncation · 구 L10 pending-exp
│          └─ 해소/비적용 (구 L10 의 완료 결과만 A.1 (iv)–(v) 로 흡수)
│
├─ Theme A · 식별성 / specificity ........... 구 L1 + 구 L9
│     └▶ "mechanism class (부호 quadrant) 는 robust, 절대 magnitude 는 아니다"
│
├─ Theme B · 표본 / out-of-sample 구조 ...... 구 L4 + 구 L2 + 구 L3
│     └▶ "CVD N=2 → 모든 OOS 축이 HC pool 위에서만 정의됨"
│
└─ Theme C · 모델링 프레임 선택 ............. 구 L5 + 구 L6
      └▶ "composite normalization + model DOF = 의도된 설계 trade-off"
```

---

#### Theme A — Parameter identifiability & specificity (구 L1 + L9)

> 핵심 메시지: **mechanism class (sign quadrant) 는 robust, 절대 magnitude 는 아니다.** 모든 candidate 는 descriptive only.

**Figure (통계 결과)** — `results/figures/fig_specificity_summary.png` (재현 스크립트 `scripts/fig_specificity_summary.py`, 원자료 redteam JSON 직접 read):

![Theme A specificity summary](results/figures/fig_specificity_summary.png)

- **(A)** Averaged-surface loss depth (Exp 17): REAL CVD 최소값이 synthetic HC null 보다 2.1×/5.5×/3.9× 깊음 → signal 존재 (= 증거 (ii))
- **(B)** Per-realization specificity p-value heatmap: Exp22 Bonferroni · Exp22 L(argmin) · Test2c label-perm. **S08-βc-dom 의 Exp22 만 p<0.05 (single null source); 나머지 8/9 cell NS** (= 증거 (i)(v)(vi))
- **(C)** Production-GT parameter recovery bias 벡터 (Test 1): 세 후보 모두 10° tol 밖 → f₁₀° < 0.30 FAIL (= 증거 (iv))
- **(D)** GT=(0,0) algorithm validation (Test 2a/B2): f₁₀°(origin)=0/140, |β_s|·|β_c| median 이 ~20°/25° → pipeline noise floor (= 증거 (iv) 보강)

```
Theme A 증거 구조 — 두 축이 complementary (모순 아님)

  averaged-surface 증거                       per-realization 증거
  (surface 가 noise 평탄화)                    (진짜 spread 노출)
  ───────────────────────                     ──────────────────────────
  (ii) loss depth   Exp17  REAL 2.1–5.5× 깊음   (i)  matched-grid LOO   Exp14/15  NS
  (iii) forward id  Exp18C Method C exact        (iv) param recovery    Test1     f10°<0.30  FAIL
                                                 (v)  loss specificity  Exp22     1/3 single-source
                                                 (vi) label-perm null   Test2c    0/3        FAIL
        │                                                │
        ▼                                                ▼
  "signal 존재 + categorical 식별 가능"          "절대값 식별 불가 · noise floor ~20°/25°"
        │                                                │
        └───────────────────────┬────────────────────────┘
                                 ▼
   A.2 (구 L9): sub-09 는 metric 선택(PCA vs SRM) 자체가 mechanism class 를 가름
                                 ▼
        ┌──────────────────────────────────────────────────────────┐
        │ 결론: descriptive only — mechanism class(부호 quadrant)만 보고 │
        │       (β_s, β_c) 값 자체는 low-dim embedding 으로만 해석        │
        └──────────────────────────────────────────────────────────┘
```

**A.1 Specificity evidence — categorical null testing + loss landscape + forward identifiability** (구 L1)

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

**(iv) Parameter recovery + (0,0) algorithm validation** (Exp 21 완료, 2026-05-31, v2 GT-consistent fake JND, n=140 per candidate):

Production GT recovery (Test 1, mag=1.0):
| Candidate | bias (β_s, β_c) | f10° | Verdict |
|---|---|---|---|
| S08-stable  (+38, −10) | (−6, +19)  | 0.10 | FAIL |
| S08-robust  (+6,  −42) | (+16, −4)  | 0.26 | FAIL |
| S09-primary (+2,  +24) | (+11, −27) | 0.14 | FAIL |

- 축-비대칭 식별가능성: v1→v2 합성-JND 일관성 수정 후 큰 |GT| 축 회수 개선 — S08-robust β_c bias 30.9°→4.7°; S08-stable β_s bias 17.0°→7.6°
- 작은 |GT| 축은 noise floor 아래 — S09-primary GT=(2, 24) 의 작은 β_s 축에서 v2 가 v1 대비 marginal 악화 (β_s noise 가 신호보다 큼)
- 이는 production argmin 의 절대 위치를 ±10° 이내로 보고 불가능을 의미; **mechanism class (β_s sign × β_c sign quadrant)** 만 보고 가능

(0,0) algorithm validation (Test 2a, B2 Source A) — **load-bearing**:
| Candidate | β_s_med (IQR) | β_c_med (IQR) | β_s p95 | β_c p95 | f10°_origin |
|---|---|---|---|---|---|
| S08-stable  | 20° (22)   | 26° (16)   | 42° | 46° | 0.00 |
| S08-robust  | 22° (40)   | 26° (10.5) | 50° | 44° | 0.00 |
| S09-primary | 16° (17.5) | 24° (9)    | 30° | 48° | 0.00 |

- Synth design contamination 으로부터 자유로운 영점 합성 (donor real JND + GT=(0,0) synth voxels, both at zero-signature)
- 모든 후보 f10°_origin = 0/140 — argmin 이 단 한 번도 origin 10° 이내 안착 못함
- Pipeline 의 **effective noise floor / built-in bias** = ~20° (β_s axis) / ~25° (β_c axis)
- Production argmin 의 effective uncertainty 하한 = 이 noise floor 수준
- → 절대값 physiological 해석 (cone shift 정도, cortical rotation 각도) 불가; 저차원 descriptive embedding 으로만 사용

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

**(vi) Label permutation specificity** (Test 2c / Source C, 2026-05-31, N=1000 within-subject trial-label shuffle, HC pool unchanged):

| Candidate | real_loss | perm 5% cut | p_perm | Verdict |
|---|---|---|---|---|
| S08-stable  | −1.236 | −2.613 | 0.866 | FAIL |
| S08-robust  | −2.892 | −3.136 | 0.167 | FAIL |
| S09-primary | −1.681 | −3.053 | 0.471 | FAIL |

- Within-subject 색-라벨 signal magnitude 가 random shuffle 분포 대비 lower-tail (p<0.05) 진입 못함
- 어느 후보도 trial-shuffled null 의 5% 컷보다 깊지 않음

**(v)–(vi) reconcile — Exp 22 vs Test 2c**:
- Exp 22 (synthetic HC fake-CVD): S08-βc-dom Bonferroni p=0.0149 SIG (L(argmin)=−2.019 vs synth mean=−1.081, single metric)
- Test 2c (real CVD label permutation): S08-βc-dom p_perm=0.167 FAIL
- 두 test 의 null source 다름: Exp 22 = HC heterogeneity 기반 noise distribution; Test 2c = within-subject label entropy 기반 noise distribution
- Conservative reading: per-realization scrutiny across both null sources → **0/3 candidates dual-pass**
- S08-βc-dom 의 Exp 22 Bonferroni-SIG 는 **single null-source marginal evidence** 로 강등; Test 2c 와 합치면 descriptive only

**메트릭별 실패 원인 (sub-09 의 경우)**:
- L(0,0): trending 방향이지만 p=0.309
- distance: real argmin 이 origin 에 더 가까움 (24.1 vs synth median 35.8) — synth attractor 가 BC extremes 로 drift, 구조적 비대칭
- L(argmin): 차이 없음

**Safe to claim (긍정 — 보고 가능)**:

- **Averaged-surface 수준에서 CVD별 distortion 방향성을 descriptive 하게 포착.** — group-averaged loss surface 에서 real CVD 신호가 null 보다 뚜렷이 깊음 → *신호 존재 자체*는 확립.
  - Production fits = valid descriptive signal estimates at averaged-surface level (Exp 17: real minima 2.1–5.5× deeper than synthetic HC null)
  - Categorical injection 하 fit procedure identifiable (Exp 18C Method C exact recovery)
- **Mechanism class (sign quadrant) 는 보고 가능.** — "어느 *방향*으로 distortion 이 일어나는가"(deutan β_s+/β_c−, protan β_c+)는 robust.
  - 모든 후보가 family-consistent quadrant 유지 (RQ1 · App. A.3 cross-metric)
  - selection rule 변경 없음 ("specificity 는 selection criterion 아님" 정책 유지)

**Cannot claim (한계 — 주장 불가)**:

- **Per-realization specificity — 사분면(quadrant)까지만 제한적으로 확정되고, 그 안의 구체적 값은 재현·구분 불가.** 의미: realization 단위로 보면 real CVD 가 null 과 구분되지 않고(CVD-specificity fail) 알려진 GT 도 회수되지 않음(simulation fail) → 신뢰 가능한 해상도가 *방향(quadrant)* 에서 멈춤.
  - Simulation (Test 1 parameter recovery): production GT 에서 f10° < 0.30, 3/3 FAIL
  - CVD-specificity test: Test 2c label-perm 0/3, Test 2b HC pseudo-CVD, Exp 22 loss-specificity 1/3 (single null-source, S08-βc-dom only), Exp 14/15 matched-grid LOO p>0.05
  - 종합: **0/3 candidates dual-pass** across null sources
- **현재 지표의 값 자체를 보고하기 어려움 — 절대 (β_s, β_c) 의 robustness · 생리 해석 불가.** 의미: pipeline 내재 noise floor 가 신호 위치 해상도보다 커서, 절대 각도를 cone-shift / cortical-rotation 물리량으로 읽을 수 없음.
  - Test 2a (0,0) algorithm validation: f10°_origin = 0/140, noise floor ~20°(β_s)/25°(β_c) — 모델 내재 bias
  - Point-estimate bias 보정 unprincipled (Exp 14 vs 15 가 15–76° 불일치)
  - → 절대값은 low-dim descriptive embedding 으로만; physiological cortical-distortion parameter 로 해석 금지

**Interpretation notes (reconcile)**:

- Averaged-surface (Exp 17) ↔ per-realization (Exp 22, Test 1/2a/2c) 는 *complementary, not redundant* — averaging 이 noise structure 평탄화, per-realization 이 진짜 spread 노출. 두 evidence 모두 보고.
- Exp 18C identifiability ≠ Test 1 production GT recovery — categorical-injected single-σ 는 recover 가능(Exp 18C exact), voxel-level full-pipeline recovery 는 noise floor 위에서만(Test 1 axis-asymmetric).

**A.2 σ-level metric non-identifiability for sub-09** (구 L9)

- PCA - SRM 간 차이 및 PCA 선택
  - v6 PCA-RDM atom 은 sub-09 의 σ 를 cortical rotation σ = (2, +24) 로 deterministic 하게 선택 (mode 87.7%)
  - 그러나 SRM family (SRM-cos, SRM-dis) 는 다른 σ = (32, 0) (S-cone shift) 선호 (Appendix A.4)
  - 두 σ 의 perceptual prediction 비교 (computed): δθ vector cosine 0.350 (낮음); sign agreement 5/8 — c4 (green), c5 (cyan), c8 (magenta) 반대 방향; max |Δδθ| 32.8°
- **PCA-RDM 채택 근거**: Cycle 5 의 2× HC-CVD separation + sub-09 stability mode 87.7% > SRM-cos 57% > SRM-dis 64%
  - 단 PCA 는 *덜 established* metric (SRM-disparity 는 프로젝트 canonical SRM family, sub-08 V2 p=0.040* 의 metric)
- Paper-level disclosure: "Sub-09 의 cortical mechanism 식별은 PCA-RDM 채택 결정에 의존; SRM family 는 다른 mechanism class (S-cone shift) 선호"
- **Theme A 와의 관계**: A.1 이 *절대 magnitude* 의 식별 불가(noise floor·null overlap)를 보였다면, A.2 는 *metric 선택* 자체가 sub-09 의 mechanism class 를 가른다는 더 깊은 식별성 한계 — 둘 다 "absolute parameter 해석 금지, mechanism class 만 보고" 결론으로 수렴.

---

#### Theme B — Sample size & out-of-sample structure (구 L4 + L2 + L3)

> 핵심 메시지: CVD 표본이 N=2 이고 CVD 측정이 pair 당 N=1 이므로, **모든 out-of-sample 축은 HC pool 위에서만 정의**된다. CVD generalization 은 Phase 3 행동 실험만이 제공할 수 있다.

```
Theme B — fit/test 에서 무엇이 vary 하는가

        CVD 쪽 (N=2, pair당 N=1)          HC pool 쪽 (n=7)
        ─────────────────────            ──────────────────────────
  fit:   ▣ 고정 (vary 불가)       ×       ◇ vary: 5/2 resample (N=300)
  test:  ▣ 동일 obs 재사용 (B.3)          ◇ vary: strict 7-fold LOO (s17)
            │                                    │
        B.1 CVD LOO 불가능                   유일하게 움직이는 축
            └───────────────┬────────────────────┘
                            ▼
              B.2 모든 out-of-sample 축 = HC normalization 만
                            ▼
              B.3 held-out focal pair 도 CVD obs 는 그대로,
                  HC norm 만 바뀌어 test 재진입
                            ▼
            ┌──────────────────────────────────────────┐
            │ CVD generalization → Phase 3 행동실험만 가능 │
            └──────────────────────────────────────────┘
```

**B.1 CVD N=2, HC n=7 — strict CVD LOO 불가능** (구 L4)
- CVD LOO 본질적으로 불가능 (N=2: sub-08 deutan, sub-09 protan)
- HC pool 은 5/2 random subset (N=300) + strict 7-fold LOO (s17) 두 evidence 로 평가

**B.2 Out-of-sample 축 = HC normalization 만** (구 L2)
- CVD JND 는 pair 당 N=1
- Train/test split 은 HC pool composition 만 vary, CVD samples 는 vary 안 함
- Behavioral generalization 은 Phase 3 experiment 필요

**B.3 Held-out focal pair 의 CVD obs 재사용** (구 L3)
- Focal pair 가 fit objective 에서 제외되나, 동일 CVD measurement 가 다른 HC normalization 하에서 test eval 에 재진입
- Individualized-filter framing 하에서는 data leakage 아니지만 disclosure 필요
- B.1–B.2 의 직접 귀결: CVD 축이 vary 하지 않으므로 test 가 HC-축으로만 구성됨

---

#### Theme C — Modeling-framework choices (구 L5 + L6)

> 핵심 메시지: composite 구성과 model DOF 선택은 의도된 설계 결정이며, 각각 명시적 trade-off 를 동반한다.

```
Theme C — 두 의도된 설계 선택과 trade-off

  C.1 z-score grid-relative composite
       1-pair γ_focal  ─┐
                        ├─(z-score)─▶  동등 기여   ◀── trade-off: info-density 차이 평탄화
       8-pair γ_all   ─┘                              (소수 pair 가 8-pair 와 같은 무게)

  C.2 R+C = 1 DOF (g)
       δθ = (2−g)·δθ_Machado   ──▶  confusion-axis(β_c) DOF 없음  ──▶ g 가 경계 saturate
                                                                       (sub-09 bdy=41%)
                                          │
                                          └──▶ 2-Component (β_s, β_c) 가 β_c 로 capture
                                               (RQ1: R+C 구조적 기각 근거)
```

**C.1 Z-score grid-relative composite 가 atom info-density 평탄화** (구 L5)
- 1-pair γ_focal ↔ 8-pair γ_all 이 composite 에 동등 기여 (의도된 normalization, §L5 원문 §2.5 일관)

**C.2 R+C 1-DOF 구조적 부족** (구 L6)
- sub-09 R+C saturates at g_max=3.0 (bdy=41%)
- R+C forward `δθ=(2−g)·δθ_Machado` 가 cortical confusion-axis rotation DOF 결여 → 2-Component 가 β_c 로 capture
- **Structural** limit (DOF count) 이며 literature-g 비교 아님 (RQ1 verdict 근거)

### Pipeline 3 status note

- 본 closure 는 **Pipeline 2 only**

---

## Closure verdict

### 완료
- ✓ Step 1–4 (Phase A → Phase B v6 PCA 45° categorical canonical)
- ✓ v6 PCA 45° categorical canonical 확립 (1° continuous variants 삭제)
- ✓ Sub-08 final candidates: **βs-dom (+38, −10)** + **βc-dom (+6, −42)** — parallel mechanism hypotheses, 동일 deutan quadrant
- ✓ Sub-09 final candidate: **βc-rot (+2, +24)** — deterministic, PCA-canonical
- ✓ Phase B → C seed audit (L7; Phase C 자체가 final selection 비기여)
- ✓ Limitations 를 3개 주제로 계층화: **A 식별성·specificity** (구 L1+L9), **B 표본·OOS 구조** (구 L4+L2+L3), **C 모델링 프레임** (구 L5+L6). 해소·비적용된 구 L7/L8/L10 은 삭제 (구 L10 의 완료 결과는 A.1 에 통합)
- ✓ Null testing (Exp 13–19) + cross-atom robustness (PCA · SRM-cos · SRM-dis) 통합

### Closure verdict — **CLOSURE READY**

- Pipeline 2 final candidates 는 v6 PCA 45° categorical canonical 하에서 **σ-level bin + γ-driven sub-bin position** 으로 보고
- Sub-08 의 두 parallel candidates + sub-09 의 single deterministic candidate
- Exp 13–19 null testing evidence 통합 (matched-grid LOO NS + loss landscape 2.1×–5.5× deeper + Method C exact recovery)
- Exp 21–22 진행 중 — 결과 도착 시 L1, L10 갱신
- Phase 3 행동 실험이 **sole verification path** — paper 작성 가능

### Paper-level framing (정직)

> "Pipeline 2 produced candidate filter forms via composite atom z-score argmin under the v6 PCA 45° categorical RDM atom. Sub-08 has βc-dom (β_s=+6, β_c=−42) under γ_OY + RDM_V2 as a final candidate within the deutan-consistent (β_s+, β_c−) quadrant. Sub-09 has a single candidate βc-rot (β_s=+2, β_c=+24) under γ_all + RDM_V1 with deterministic identification at the σ-bin level (mode share 87.7%, strict LOO IQR (0,0)). All candidates implicate combinations of S-cone rotation and confusion-axis rotation at the cortical representation level. Averaged-surface evidence supports signal presence (Exp 17 real CVD minima 2.1×–5.5× deeper than synthetic HC nulls) and categorical identifiability holds (Exp 18C Method C exact recovery for sub-09 GT=(0,+24)); however per-realization parameter recovery FAIL across all three candidates (f10° < 0.30 at production GT, f10°_origin = 0 at GT=(0,0) confirming a ~20°/25° per-axis noise floor on β_s/β_c), and Source C label-permutation null is NS for all three (p_perm = 0.17–0.87). We therefore present these candidates as plausible descriptive fits at fit-point requiring behavioral validation, with absolute (β_s, β_c) values interpretable only as low-dimensional embedding rather than physiological cortical-distortion parameters. Mechanism class (sign quadrant) is robust; magnitudes are not."

---

## Files

| File | Role |
|---|---|
| `PIPELINE_2_CLOSURE.md` | (본 문서) 5-step pipeline narrative + final candidates + limitations |
| `closure.md` | **4-test verification summary (canonical user-facing)** — content/purpose/metric/result per test |
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
| `results/redteam/exp21_forward_recovery_sweep.{py,json}` | (deprecated by Test 1/2a) 3 candidates × magnitude sweep × N=100, Method C |
| `results/redteam/exp22_origin_loss_specificity.{py,json,md}` | Loss-based specificity (synthetic HC null): L(0,0), distance, well depth — single null-source marginal evidence only (S08-βc-dom Bonferroni p=0.0149) |
| `results/redteam/param_recovery_voxel_v6_pca_v2.json` | Test 1 — Production GT parameter recovery (v2 GT-consistent fake JND) |
| `results/redteam/null_within_hc_loo_v6_pca.json` | Test 2a (B2 / Source A) + Test 2b (B1 / Source B) — algorithm validation at (0,0) + HC pseudo-CVD specificity |
| `results/redteam/null_label_permutation_v6_pca.json` | Test 2c (Source C, N=1000) — within-subject color-label permutation |
| `results/redteam/verdict_matrix_v6_pca_v2.json` / `verdict_matrix_v2.md` | 4-test verdict matrix (FDR-corrected) |
| `results/redteam/uncertainty_summary.json` / `uncertainty_summary.md` | Per-candidate effective uncertainty (B2 σ) + v1/v2 comparison + Source C + B1 ranks |
| `scripts/fig_specificity_summary.py` | **§5.2 Theme A figure 재현 스크립트** — exp17/exp22/verdict_matrix_v2/uncertainty_summary JSON 직접 read |
| `results/figures/fig_specificity_summary.{png,pdf}` | **§5.2 Theme A 통계 figure** (4-panel: loss depth / specificity p-heatmap / recovery bias / (0,0) noise floor) |
| `scripts/fig_candidates_param_space.py` | **§5.1 / RQ1 candidate (β_s,β_c) figure 재현 스크립트** — v6 fit 결과 JSON 의 per-subset median (App. A.2 재현) |
| `results/figures/fig_candidates_param_space.{png,pdf}` | **§5.1 앞부분 figure** — 3 candidate (β_s,β_c) + cross-metric (PCA/SRM-cos/SRM-dis) spread |

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
