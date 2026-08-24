# Phase 2 Pipeline Summary — for PI presentation (2026-05-19)

> **이 문서의 목적**: PI 지적사항("Model/Loss selection criteria 가 evaluation criteria 와 동일 = double dipping")에 직접 대응. (a) RDM 계산 방식, (b) prediction model 사용 여부, (c) selection vs evaluation 데이터/지표 중복 지점을 §10 risk map 에 명시.
>
> **본 문서가 일관되게 유지하는 내부 입장** (CLAUDE.md §0, SUMMARY.md §2 2026-05-19 reframe):
> - `perm_p` 는 per-subject **fit-validity** 일 뿐 CVD-vs-HC group test 아님 (HC FPR=100%).
> - P2a 는 **post-hoc 보조지표**, primary endpoint 아님 (circular).
> - Specificity claim **금지** — descriptive percentile 만 허용.
> - 진정한 independent evaluation = **Phase 3 pre-registered behavioral acquisition** (미수집).

---

## 1. Goal

CVD 피험자 fMRI 패턴이 HC pool 의 V4 LOCO vulnerability 프로파일에 가까워지도록 하는 **stimulus-space 보정 필터 δθ(θ)** 를 per-subject 로 도출 (8-color DKL hue ring).

## 2. Input data

| 항목 | 값 |
|---|---|
| Amplitude | C010 procrustes-aligned, shape `(6 runs × 8 colors × n_voxels)` |
| Stimuli | 8 DKL hues, L\*=75, equal chroma, 45° spacing (red 0° → magenta 315°) |
| ROIs | V1, V2, V3, hV4 (hV4 = "V4" on disk); **canonical fit ROI = hV4** |
| HC pool | sub-01 ~ sub-07 (n=7); hV4 effective n=6 (sub-07 voxel 16개로 일부 분석 NaN) |
| CVD analyzed | sub-08 (deutan, severe), sub-09 (protan); sub-10 = 2차 행동 acquisition 중도 탈락으로 paper 제외 |

## 3. Neural-data → scalar conversion

### 3.1 RDM (distance metric · cross-validation 여부 · partition 단위)

| 측면 | 사양 |
|---|---|
| Distance metric (canonical) | **Correlation distance** = 1 − Pearson r between voxel patterns (`diagnostic_delta_rdm.py:80-89`) |
| Pattern unit | **run-averaged** per-color voxel pattern (8 × V_s) |
| Cross-validation | **없음** in canonical L_rdm path (within-subject, alignment-free). Crossnobis 는 diagnostic only. |
| Partition unit | Per-color (8 conditions → 28 pairs upper triangle) |
| ΔRDM_obs | RDM_CVD − mean_HC RDM, 28-vec (`diagnostic_delta_rdm.py:199-230`) |
| ΔRDM_sim | RDM( C(θ+δ) @ W_HC ) − RDM( C(θ) @ W_HC ), HC 평균 (`diagnostic_delta_rdm.py:233-277`) |

→ **RDM 은 prediction model (W) 가 들어가는 sim 측과, 들어가지 않는 obs 측으로 양분**. obs 측은 순수 데이터, sim 측은 forward encoder 출력의 RDM.

### 3.2 LOCO ρ (정의 · training partition · encoder)

| 측면 | 사양 |
|---|---|
| Encoder | **ridge_gcv** (GCV 로 α 선택, per-HC) — A10 으로 고정 (smooth_tikh 3회 rescue 후 reject) |
| Basis (channel space) | 360°-grid FE basis, K=3 채널 @ hV4 (project memory) |
| LOCO partition unit | **Color** (8 colors → 7 train / 1 test) |
| Train samples | 7 train colors × 6 runs = 42 pooled samples (`step1_fit_loco_v2.py:103-135`) |
| Held-out target | Test color 의 run-averaged voxel pattern |
| Per-color vulnerability | Voxel-pattern Pearson correlation(predicted, held-out actual) |
| Method (canonical) | **shift_at_both** — δ 변할 때마다 W 재학습. W_fixed 는 fast variant (`step1_fit_loco_v2.py:155-234`) |
| Mean-HC aggregation | 7 HC vulnerability 의 산술평균 (8-vec) |

→ **LOCO ρ 는 prediction model (W) 의 hold-out 성능**. RDM 과 달리 항상 forward-model 의존.

## 4. Candidate models

| Model | Free params | Origin | Physical meaning | 본 파이프라인 역할 |
|---|---|---|---|---|
| **Machado 1-way** | 1 (Δλ) | Machado et al. 2009 IEEE TVCG | Retinal: M (deutan) / L (protan) cone spectral peak shift; α coupled | **Diagnostic only** (Tier-2 paper finding) |
| **R+C** | 2 (Δλ, g) | Tregillus et al. 2021 Curr Biol motivated | Retinal Δλ + cortical RG-axis gain g; g=0 ≡ Machado, g=−1 exact compensation | **Filter form rejected 2026-05-16** (Check 4 P2a 0.588/0.787 < 2-comp 0.750/0.975). **Etiology diagnostic 으로만 retain** (sub-08 cortical-dominant, sub-09 retinal-dominant) |
| **2-Component** | 2 (β_s, β_c) | Emery 2021 structural framework | Stimulus-space (CIELab) angular dilation; β_s = S-cone term @ 90°, β_c = confusion-axis term @ θ_conf (protan 16° / deutan 150°, Stockman) | **Canonical filter form** (Phase 2 BEST) |
| Fourier warp | 4 | — | 1st+2nd harmonic angular warp | Ablation ceiling 만; overfit (4 DOF / 8 colors) |
| 3-component | 3 (Δλ, β_s, β_c) | richer alternative | Cascade | Phase 4 preview, **pre-committed criteria fail** |

→ Forward map → 8-color δθ vector → channel basis `basis_full[round(θ+δ) % 360]` → ridge_gcv encoder 입력 (`loco_distortion_fit.py:146-204`).

## 5. Loss function

```
L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth
      = 1.0·L_vuln + 0.5·L_rank + 0.2·L_rdm + 0.1·L_smooth
```
(모든 항 [0,1] 정규화 후, `loco_distortion_fit.py:85-100, 214-280`)

| Term | Raw formula | Normalizer | 사용 데이터 |
|---|---|---|---|
| **L_vuln** | (1/8)·Σ_c (v_sim[c] − v_cvd[c])² | 4.0 | hV4 LOCO ρ (sim vs CVD obs), per-color |
| **L_rank** | 1 − Spearman ρ(v_sim, v_cvd) | 2.0 | 같은 vector 의 rank |
| **L_rdm** | 1 − cos(ΔRDM_sim, ΔRDM_obs) | 2.0 | hV4 28-pair RDM (sim vs CVD−HC obs) |
| **L_smooth** | (1/8)·Σ_c [(δθ[c+1] − δθ[c]) mod ±180]² | 32400 (=180²) | δθ regularizer (data-free) |

| ROI scope | **모든 항 hV4 단일 ROI 에서 계산.** L_rdm 은 "CVD-vs-HC 테스트" 아님 — fit ROI 내부 multi-objective 일관성 항 (SUMMARY.md §loss 명시) |

## 6. Model selection criterion

| 단계 | 절차 |
|---|---|
| Filter form 선정 | 3 model class 중 2-component 채택; **pre-image 8/8 exact** + behavioral filter pipeline 일관성 (R+C 는 sub-09 arc-compression 4/8 fail) |
| Per-subject (β_s, β_c) 선정 | hV4 LOCO L_fit 최소화하는 grid argmin (26×51=1326 points, β_s ∈ [0,50] step 2, β_c ∈ [−50,50] step 2) |
| ROI 선정 (V4 vs V1/V2/V3) | **(독립 prior) Forward LOCO gate** at HC group level: hV4 p=0.044 (단일 검정), V1/V2/V3 NS — Phase 1 결과 (`phase4_forward_model/results/loco_reinforcement/permutation_test.json`) |
| Per-subject BEST | sub-08 (β_s, β_c) = (38°, −14°); sub-09 (6°, −22°) — `BEST_summary.json` |

## 7. Evaluation criterion

| Evaluation | 절차 | 독립성 | 결과 |
|---|---|---|---|
| `perm_p` (per-subject label permutation) | CVD vulnerability label 셔플 후 best-sim 과의 Spearman ρ 재계산 (50000 perms; 8!=40320 → exact 가능) | **NOT independent** — 같은 8-vec, L_rank 포함 | sub-08 p=0.004, sub-09 p=0.035 → per-subject fit-validity 만 |
| HC specificity (`hc_specificity_check.py`) | 7 HC 에 same procedure → boot_frac of HC norm < CVD norm | Procedure-level | **HC FPR = 100%** under voxel-prediction LOCO measurement family |
| Baseline Δρ diagnostic (Job 96664) | HC LOO 분포에서 CVD Δρ percentile | Procedure-level | HC baseline_ρ vs Δρ corr = **−0.894** → baseline_ρ confound (regression-to-mean) |
| Forward LOCO gate @ HC group | HC 만으로 group-level LOCO permutation; CVD 사용 X | **Independent** (CVD 사용 X) | hV4 p=0.044 단일 검정; V4 채택 prior |
| Pre-image bijectivity | Forward map 의 수학적 역함수 가능성 | **Independent (수학적 성질)** | 2-comp 8/8 exact for sub-08·sub-09 |
| **P2a** (corrected labels) | filter 적용 → 사전 수집된 color-naming 데이터와 비교 | **Circular** — 같은 사전 데이터로 fit/validate | sub-08 0.750 (identity 0.688), sub-09 0.975 (= identity 0.975); **post-hoc only**, paper primary endpoint X |
| **Phase 3 behavioral acquisition** (TBD) | filter vs sham vs control, **pre-registered**, **신규** 수집 | **Truly independent** | 미수집 — paper-level validation 의 필수조건 |

## 8. Pre-image (inverse filter) 산출

| 항목 | 사양 |
|---|---|
| 목표 | 관찰자가 θ_target 을 인지하도록 만드는 input θ_pre |
| 수식 | θ_pre = argmin_{θ} \|forward(θ; β_s, β_c) − θ_target\| |
| 2-component bijectivity | hue 가산 modular → 항상 invertible, **8/8 exact** for sub-08·sub-09 |
| Stimulus correction | θ_corrected = (θ_stim − δθ) mod 360° |
| Per-subject δθ vector | sub-08: [−12.1, −20.2, −25.7, −29.4, −32.1, −10.3, +29.4, +18.5]; sub-09: [−15.5, −10.9, −6.5, −2.4, +2.4, +21.1, +2.4, −20.7] (`BEST_summary.json`) |

## 9. Current status / known limits

| 항목 | 결과 / 위치 |
|---|---|
| Phase 2 status | **CLOSED 2026-05-17**; canonical BEST reproducibility verified 2026-05-19 server (`BEST_summary.json`) |
| HC LOCO FPR | **7/7 = 100%** under label-permutation null (Job 96600); 2component=100%, R+C=71%, Machado=43% → specificity 통계적 주장 불가 |
| Baseline ρ + Δρ dissociation | HC corr = **−0.894** (Job 96664). sub-08 Δρ rank 5/8 emp_p=0.50 (HC sub-03/04/05 보다 worse); sub-09 rank 7/8 emp_p=0.25; sub-10 rank 7/8 (정상이어야 할 통제 = CVD 와 indistinguishable) — `baseline_delta_rho/summary.json` |
| Loss inventory (15 variants × 8 subjects, CI-based bootstrap) | sub-08 multiple convergent ✓✓; sub-09 단 1개 (cycle15_opt2) ✓ sig, sub-04 HC outlier 의존; mw_jaccard_loss alone ~~ marginal (`results/inventory/loss_inventory.md`) |
| Three convergent richer-model failures | L_dir (ratio 0.047/0.067 flat), 3-comp joint (sub-09 c4 sign fail), voxel-level direct MSE (sub-09 (0,+36) sign flip vs canonical −22°) — `phase4_preview/`, `voxel_level_fit/` |
| sub-09 ΔRDM 단독 유의 vs LOCO 비유의 | sub-09 ΔRDM perm_p=0.026 vs LOCO V1 label_p=0.197 → "sensitivity 차이" (L_rdm @ δ=0.2 weighting), true dissociation 아님 |
| sub-10 status | 2차 행동 acquisition 중도 탈락; technical 2-comp fit (10°,+22°) p=0.018 존재하나 paper 분석 제외 |
| Behavioral validation | **사전 수집 P2a / discriminability 모두 circular** → 별도 Phase 3 acquisition 필수 |
| Removed (2026-05-19) | cc-matrix Bonferroni anchor (sub-09 V4 cc p=0.010 strict-Bonf-fail, sub-07 n_vox=16 harmonization 의존) |

## 10. Double-dipping risk map (PI 피드백 직접 대응)

> 같은 데이터/지표를 selection 과 evaluation 양쪽에 쓰는 지점을 명시하고, 진정으로 독립적인 evaluation 이 무엇인지 분리.

### 10.1 Risk cell table

| # | Cell (selection step → evaluation step) | Data / metric | Independence | 우리의 입장 |
|:--|---|---|:--:|---|
| **R1** | (β_s, β_c) argmin via L_fit @ V4 → per-subject `perm_p` | **동일** CVD V4 LOCO vulnerability 8-vec; L_rank 가 Spearman ρ 정의 자체 | **CIRCULAR** | `perm_p` 는 per-subject **fit-validity** 만, **CVD-vs-HC group test 아님**. HC FPR=100% 가 empirical 확인. SUMMARY.md §2a 명시. |
| **R2** | L_rdm @ V4 (fit objective) → ΔRDM cosine evaluation @ V4 | **동일** V4 28-pair ΔRDM | **CIRCULAR (definitional)** | L_rdm 은 fit ROI 내부 multi-objective **consistency 항**, **CVD-vs-HC 테스트 아님** (SUMMARY.md §loss terms) |
| **R3** | filter (β_s, β_c) → P2a (사전 수집된 color naming) | 사전 수집된 동일 behavioral data 가 (a) fit 가이드 + (b) validation 양쪽에 노출 | **CIRCULAR** | CLAUDE.md §0.1 명시: P2a/P1 는 **post-hoc 보조지표**, paper primary endpoint **금지**. Independent Phase 3 acquisition 필수. |
| **R4** | Loss inventory 15 variants 의 best loss 선정 → 같은 HC pool 에서 bootstrap CI | 같은 HC pool n=6 가 (a) loss tuning + (b) sanity check | **PROCEDURALLY DEPENDENT** | "Just one more selection rule" anti-pattern (CLAUDE.md §8). Cycle 9~13 closed, reformulation 금지. |
| **R5** | HC specificity / baseline Δρ percentile | HC LOO 가 selection 기준에도 영향 (loss tuning) + evaluation 에도 사용 | **PROCEDURALLY DEPENDENT** | Descriptive percentile 만 — "HC distribution 의 X percentile" 형식. p-value claim 금지 (CLAUDE.md §0). |

### 10.2 Independent criteria (PI 에게 강조할 점)

| # | 독립 evaluation | 왜 독립인가 |
|:--|---|---|
| **I1** | **Forward LOCO gate @ HC group** (hV4 p=0.044, V1/V2/V3 NS) | CVD 데이터 사용 X. HC 만으로 ROI 의 interpolation 능력 검증. ROI 채택 prior 로 사용. (Phase 1 결과) |
| **I2** | **2-component pre-image 8/8 exact** | Forward map 의 수학적 성질 (modular hue 가산 → bijective). 통계 테스트 아님. R+C 는 sub-09 4/8 fail → filter form 에서 rejected. |
| **I3** | **Three convergent richer-model failures** (L_dir, 3-comp, voxel-MSE) | Pre-committed criteria 로 model class 확장 시도, 모두 fail. 같은 데이터를 쓰지만 **다른 방향** (within-class fine-tuning 이 아닌 class enrichment). |
| **I4** | **Phase 3 pre-registered behavioral acquisition** (미수집) | **유일한 paper-level independent validation**. OSF pre-reg → 신규 subject session → filter vs sham vs control → per-color naming. |

### 10.3 PI 질문에 대한 한 줄 답

> "현재 Phase 2 의 `perm_p`, P2a, HC specificity 는 selection 과 데이터/지표를 공유하며 fit-validity 또는 descriptive 위치로만 기능한다. **CVD-vs-HC 검증으로 해석되지 않음을 paper 본문에서 명시**한다. 진정한 independent evaluation 은 (a) Phase 1 의 HC-only forward LOCO gate (ROI prior) + (b) 2-component pre-image bijectivity (수학) + (c) **Phase 3 pre-registered behavioral acquisition** (수집 필요) 세 갈래로 분리되어 있다."

### 10.4 Paper-level mitigations (PI 우려 대응책)

1. **Methods section**: `perm_p` 를 **per-subject fit-validity** 로만 기술; HC FPR=100% 사실 명시.
2. **L_rdm 역할 재명명**: "fit-ROI 내 geometric consistency term", **NOT** "geometric evaluation criterion".
3. **P2a 제외**: paper primary endpoint 에서 빼고, 별도 Phase 3 behavioral acquisition 을 validation 으로 제시.
4. **ROI 선택 근거**: Phase 1 의 HC-only forward LOCO gate (p=0.044) + biological prior (hV4 = color hub) 를 prior 로 제시. CVD 데이터로 ROI 선택 X 명시.
5. **N=2 한계**: "proof-of-concept methodology" framing — "framework" 아님.

---

**Source-of-truth 파일** (재현용)

- `BEST_summary.json` — canonical (β_s, β_c), perm_p, P2a, etiology
- `results/SUMMARY.md` — 위 narrative 의 long form
- `scripts/loco_distortion_fit.py:85-280` — loss 정의 + grid search
- `scripts/step1_fit_loco_v2.py:103-300` — LOCO simulation + permutation
- `scripts/diagnostic_delta_rdm.py:80-310` — RDM/ΔRDM 정의
- `phase4_forward_model/results/loco_reinforcement/permutation_test.json` — independent ROI gate

**확인 필요 (slide 발표 시 PI 질문 대비)**

- Phase 3 behavioral protocol 의 pre-registration 일정 및 acceptance criteria (현재 OSF draft 단계).
- "Three convergent failures" 의 pre-commitment 시점 문서 (`phase4_preview/` 내 README 또는 commit log) — reviewer 가 post-hoc 가능성 제기 시 대응 자료.
