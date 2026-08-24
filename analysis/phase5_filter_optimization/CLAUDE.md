# phase5_filter_optimization — CLAUDE.md : CURRENT FOCUS

**Stage B + C** · **Status**: ACTIVE.

documentation should be updated rather than accumulating outdated results

## 0. Framework Decision (READ FIRST — 절대 재논의 금지)

> **📎 prior-works mapping** — 모델 관련 작업 시작 전 `prior-works.md` 를 반드시 먼저 읽는다. paper draft / presentation / README 의 prior-art claim 은 본 문서와 일치해야 함.
>
> **📎 PI feedback tracking** — Model & Loss selection validation 의 진행 추적은 `PI-feedback-priorwork.md` (living tracker). 

**Filter selection = LOCO-best descriptive fit per subject + behavioral validation.**

- **Specificity claim은 selection criterion이 아니다.** HC FPR 100% (`hc_specificity/`), baseline_ρ confound (HC corr=−0.894, `baseline_delta_rho/`), n=6 HC pool 한계 모두 확인됨. 어떤 selection-rule reformulation도 voxel-prediction L_LOCO measurement family 내에서 specificity를 만들 수 없다 — Cycle 9~13에서 13회 사이클로 확정 (action_plans/PLAN04, project memory `project_phase2_closure.md`).
- **Specificity는 descriptive reporting으로만 기술.** "HC와 비교했을 때 sub-XX의 fit은 distribution의 X percentile" 형식. p-value/FPR claim은 보류.
- **Behavioral validation 잠정 보류** (2026-05-13): behav_validation §3 "PASS"는 색 구별가능성(discriminability) 기준이며, P1/P2a (원래 색 정확 복원) 기준 아님. P2a-restoration 기준으로 재평가 필요. 현재 sub-08·sub-09 모두 P2a-validated 필터 미확정.
- **새로운 selection rule 변형 금지.** `z_combined`, `cross-ROI`, `baseline_sp 보정`, `family-aware 가중치` 등 모든 reformulation은 Cycle 9~13에서 시도되어 NET 개선 없음 확인.
- **Override 절차**: 위 결정을 재방문하려면 사용자가 세션 시작 시 명시적으로 "override §0"를 적시해야 한다. "새로운 framing"이라는 암묵적 합리화는 override가 아니다.

### §0.1 P2a/P1 reporting policy (2026-05-16, USER DECISION)

- **P2a/P1는 loss 모색을 위한 *보조지표만*.** Paper에 P2a/P1 수치를 *primary endpoint*로 보고하지 않는다. 이유: 사전 수집된 sub-08/09 color naming report와 filter prediction을 같은 데이터에서 fit↔validate → **circular**.
- **Paper에는 다음만 보고**:
  - 신경 fit 결과 (β params, ρ, perm_p, HC-comparison percentiles as descriptive)
  - R+C decomposition (retinal Δλ + cortical g)
  - Pre-image mathematics (8/8 exact)
  - **별도 수집된 behavioral test** (filter 적용 자극 → 색 명명/구별 → no-filter 통제 대비) — TO BE COLLECTED
- **P2a/P1는 loss 설계 가이드용으로만 사용**: 어떤 loss formulation이 신경적으로 sensible한 (β_s, β_c)를 줄 때, 그 (β_s, β_c)가 P2a/P1 plateau 안에 떨어지는지 *예측 가드레일*로 활용. P2a/P1를 fitting objective 또는 selection criterion으로 쓰지 않는다.
- **Loss/filter selection의 새 기준 (Nat Comms / top neuro journal 대비)**:
  1. **Neural-based**: loss는 fMRI data로부터 도출 (P2a/P1 미포함)
  2. **Statistically valid**: 각 loss component가 CVD-HC distinct (Bonferroni-style sig) AND HC specificity 통과 (boot_frac ≥ 0.975, robust to sub-04 outlier)
  3. **P1/P2a speculation**: filter (β_s, β_c)가 P1/P2a plateau 또는 R+C-predicted region에 들어감으로 *예상 effectiveness* 추정 (paper 보고는 X, internal selection 가드만)
- **이 정책은 §A4(behavioral validation 보류)와 일관**: discriminability/restoration 모두 사전 수집 데이터로는 circular. *별도 behavioral test 수집*만이 paper-reportable validation.

## 1. Objective

(B) CVD simulator 피팅 + (C) 역문제(pre-image) → **stimulus-space 색 보정 필터**. 각 CVD 개인에 대해 δ(θ) 함수.

## 2. Pipeline Assumptions (CRITICAL — 명시적으로 적음)

| # | 가정 | 근거 / 한계 |
|---|---|---|
| A1 | Post-cortical mapping은 HC = CVD 동일 | 프로젝트 핵심 전제. CVD 차이는 (a) retinal cone shift, (b) cortical opponent gain, (c) stimulus-space dilation 중 하나. |
| A2 | 3 model classes: Machado 1-way / R+C / 2-component | 각 mechanistic level (retinal / cortical gain / stimulus-space). 추가/제거 금지. |
| A3 | Forward fit = ridge_gcv encoder + voxel-prediction LOCO ρ primary | behav_validation §3가 LOCO와 행동의 100% concordance 확인. ΔRDM/SRM은 부차. |
| A4 | Per-subject best model = LOCO ρ best (primary). 행동검증은 P2a-restoration 기준으로 재정의 필요 — 기존 discriminability-PASS는 보류. | (2026-05-13 revision) |
| A5 | Pre-image = forward model의 exact 수치 역함수 | 8/8 exact 못 풀면 subject-model 조합 **기각**. 2-comp는 sub-08/09 모두 8/8 exact 확인. |
| A6 | HC pool n=7 nominal (sub-01~07), hV4 effective n=6 (sub-07 16 voxels → nan) | 추가 모집 불가. specificity statistical claim 불가능. descriptive 위치만. |
| A7 | sub-10 (near-normal) 분석 제외 | CVD-HC 차이 미포착, downstream 분석에서 제외. |
| A8 | 8-color resolution은 model 표현력 상한 | 8 colors / 4 ROIs = 32 dof로 다중 mechanism 분리 한계. orange (45°) / magenta (315°) 같은 narrow-band 색은 fine grid로도 회복 안 될 수 있음. |
| A9 | Behavioral validation은 model class 결정 권한 (단 P2a-restoration 기준 필요) | discriminability-PASS는 보류 (2026-05-13); P2a 기반 검증 프로토콜로 재설계 필요. |
| A10 | Encoder = ridge_gcv (fixed) | smooth_tikh는 3회 rescue 시도 후 REJECTED (MEMORY 2026-03-11). 대안 encoder 제안 금지. |
| A11 | Single mechanism per subject | Per-subject 1개 model class만 채택. 모델 class 간 ensemble averaging 금지. |
| A12 | 2-component은 CIELab opponent space 작동 | RGB/cone space 아님. **R+C 의 C_baseline** 은 `machado_shifted_hue(0.0, family)` (CIELab nominal 각도 금지) — 이는 R+C baseline 규약이며, A13 의 2-Component forward 자체 (raw nominal-θ) 와는 다른 단계. |
| **A13** | **Closure 2-Component forward** = `scripts/two_comp.py:forward_2comp` (★ raw CIElab nominal-θ): `δθ = β_s·cos(θ−90°) + β_c·cos(θ−θ_conf)`, θ_conf={protan:16°, deutan:150°}. Phase B v6 main runner (`scripts/s10b_v6_pca_rdm.py:31,:231,:607`), `s17_hc_loo.py`, `s13_round3.py`, `s12b_phase_c_v2.py` 가 모두 이 forward 만 호출. | **모든 viz / post-hoc / Phase 3 자극 합성도 이 forward 사용.** `scripts/forward_models/two_component.py` 의 frozen H_BASE 변형은 `loco_distortion_fit.py` 전용 alternative entry 이며 **closure 와 무관**. 같은 (β_s, β_c) 라벨에서도 두 함수는 정반대 δθ 8-vec 을 산출 (예: 현행 S08-robust deutan (6,−42) c4 → raw −36.33° vs frozen +19.18°, 부호 반대), 혼용 금지. 이력: 2026-05-27 viz 가 frozen 으로 잘못 그려졌다가 closure 와 부합하는 raw 로 정정. |

## 2.5. Loss Atoms + Selection Framework (v6 PCA canonical, SUPERSEDED 2026-06-01)

> **⚠️ 구 §2.5 (cycle15 / mw_jaccard / l_rank / boot_frac ≥ 0.975) 는 S7 sprint 이전 단계이며 v6 PCA canonical 이 이를 전면 supersede.** cycle15_opt2, mw_jaccard 등 구 loss variant 를 selection criterion 으로 쓰지 않는다. 아래가 현행 기준.

**Canonical fitter**: `scripts/s10b_v6_pca_rdm.py` (v6 PCA 45° categorical RDM atom)
**Source of truth**: `PIPELINE_2_CLOSURE.md` (2026-06-01, CLOSURE READY)

### Loss atoms (locked)

| Atom | 정의 | 역할 |
|---|---|---|
| **γ_focal** (γOY, γYG, γYP, γGB) | per-pair JND z² vs HC train baseline | 행동 focal pair |
| **γ_all** | 8-pair JND z² 합 | 행동 전체 |
| **RDM_{V1..V4}** (canonical) | PCA top-K=6 → 8×8 correlation-RDM → 28-d cosine vs HC mean (categorical 45° σ-bin) | 신경 구조 |
| LOCO_V4 | V4 voxel-prediction loss | precondition gate 전용 |

**Composite**: `z_sum = Σ zscore_grid(atom)` → `comp / sqrt(n_atoms)` → `argmin`

### Selection metric hierarchy (`PIPELINE_2_CLOSURE.md §3.3`)

1. **Primary**: `test_loss_median` ASC (5/2 HC split × N=300 resample 의 test composite)
2. **Secondary**: `test_loss_iqr` ASC
3. **Supplementary**: `boundary_rate < 0.5`; collapse: `iqr > 50` OR `sign(train) ≠ sign(test) AND |Δ| > 5`

## 2.6. HC Specificity (DESCRIPTIVE ONLY — 2026-06-01 confirmation)

**§0 rule 불변**: specificity = descriptive only, selection criterion 아님.

v6 PCA canonical null testing (`PIPELINE_2_CLOSURE.md §5.2 Theme A`) 결과:
- Exp 22 loss-based specificity: **0/3 candidates dual-pass** (S08-βc-dom Bonferroni p=0.0149 = single-null-source marginal, Test 2c label-perm 0/3 FAIL)
- Exp 14/15 matched-grid LOO: 모든 candidate 보수적 NS
- **Safe to claim**: mechanism class (sign quadrant) descriptive, averaged-surface signal presence (2.1×–5.5× deeper than null)
- **Cannot claim**: per-realization specificity, absolute (β_s, β_c) physiological interpretation

→ `hc_specificity_check.py` (boot_frac) 는 보조 descriptive 도구. v6 PCA test_loss_median 이 primary.

## 3. Per-Subject Status (CLOSURE READY 2026-06-01 — v6 PCA 45° categorical)

**Source of truth**: `PIPELINE_2_CLOSURE.md` (2026-06-01). **S7 sprint = COMPLETED. v6 PCA 45° categorical canonical 채택.**

**S7 이전 sprint (S5', S6, S11_legacy) + 구 closure (2026-05-17) 은 역사적 기록. 재활성화 금지.**

### Model class verdict (RQ1 — FINAL)

- **R+C: REJECTED** — boundary saturation (sub-08 bdy=100%, sub-09 bdy=41%); DOF 부족 (confusion-axis β_c 없음, `δθ=(2−g)·δθ_Machado` 형태)
- **2-Component: ACTIVE** — β_s (S-cone cardinal axis) + β_c (confusion-axis rotation) covers both axes

### Final candidates (v6 PCA 45°, 2026-06)

| Subject | Label | Model | Loss combo | (β_s, β_c) | param IQR | Stability |
|---|---|---|---|---|---|---|
| sub-08 deutan | **S08-robust (βc-dom)** | 2-Component | γ_OY + RDM_V2 | (+6, −42) | (8, 2) | 7-fold LOO β_c [−46, −38], cross-0 없음 |
| sub-09 protan | **S09-primary (βc-rot)** | 2-Component | γ_all + RDM_V1 | (+2, +24) | **(0, 0)** | mode share 87.7% (263/300) |

**S08-βs-dom (+38, −10) = DROPPED** (2026-06-01 closure 결정).

### 식별성 한계 (Theme A, `PIPELINE_2_CLOSURE.md §5.2`)

- **보고 가능**: mechanism class (sign quadrant) — sub-08 β_s+/β_c−, sub-09 β_c+; averaged-surface signal (2.1×–5.5× deeper than HC null)
- **보고 불가**: 절대 (β_s, β_c) 값 physiological 해석 — noise floor ~20°(β_s)/25°(β_c), f10° < 0.30 FAIL for all 3 candidates, 0/3 dual-pass null tests
- **Sub-09 추가 한계**: PCA (2,+24) vs SRM (32,0) — σ-level metric non-identifiability (mechanism class itself is metric-dependent)

### Held-out test evidence (`s18`, RQ4e)

- sub-08 (6,−42): RDM ΔL=−0.406, **7/7 folds beat (0,0)**, γ ΔL=−13.8 (5/7) ✓
- sub-09 (2,+24): RDM ΔL=−0.472, **7/7 folds beat (0,0)**, γ ΔL=−0.55 (4/7) ≈null
- Neural (RDM) stable value = good for both; behavioral (γ) benefit asymmetric (sub-08 YES, sub-09 NO/weak)

### Behavioral validation status
- **Phase 3 = sole CVD-generalization verification path**
- sub-09 의 sub-08-equivalent behavioral session 1회 acquisition = Phase 3 first priority
- P2a/P1 = descriptive guardrail only (§0.1, circular on existing data)

### S5' procedural-bias caveat (2026-05-23, unchanged)
HC pool g 산출 시 CVD-prior Δλ를 HC에 강제 대입 → procedural artifact. CVD g≈3 claim은 paper에서 **caveat 동반** 또는 제외.

### sub-10 (제외, §A7 unchanged)
분석 대상 아님.

## 4. Active Deliverables (Phase 2 CLOSURE READY — Phase 3 준비 단계)

1. **Sub-09 behavioral session acquisition** (Phase 3 first priority) — JND 8 pair + 8AFC 64 trial, sub-08-equivalent protocol
2. **Paper write-up**: `PIPELINE_2_CLOSURE.md §Paper-level framing` 기준 — candidates as descriptive fits + Theme A/B/C limitations
3. **Phase 3 stimulus synthesis**: pre-image 적용 자극 생성 (`scripts/s12b_phase_c_v2.py`, closure forward 사용)

## 5. Closed (재논의 금지)

| Cycle | 시도 | 결과 |
|---|---|---|
| 9 | l_signed_jaccard | REJECTED, 부호 정보 noise dominate |
| 10/10b/10c | z_vox simplification, sub-04 exclusion, server bootstrap | NET 개선 없음 |
| 10d/10e/10f | bootstrap CI, threshold envelope | data-limit 확인 |
| 11/11b | per-term cross-ROI specificity | post-hoc fishing 인정, V1\|V4 권장 철회 |
| 12 | cross-ROI loss (filter fitting) | **REOPENED 2026-05-03**: specificity 게임은 dead-end, **그러나 alternative filter generation method로 valid**. sub-09 V4-only (0,0) degenerate → cross-ROI loss (β_s=30, β_c=26) non-trivial 추출. sub-08 cross-ROI loss (β_s=68, β_c=−38) 추출. 행동검증 ground truth로 사용. |
| 14 | V1 RDM cross-criterion (V1 l_rank → V1 RDM cosine) | sub-08 (58, -36) ≈ Cycle 12 (68, -38); sub-09 (32, +22) ≈ Cycle 12 (30, +26). **V1 metric 종류는 결과에 거의 영향 없음**. 새 행동 후보 추출 안 됨. **그러나 sub-09 V1 RDM cosine +0.29 → V1 신호 confirmation**, sub-08 V1 RDM cosine +0.02 → sub-08 V1 신호 약함. Cross-ROI 접근 자체의 필요성은 sub-09에서 강하게 재확인. |
| 13 | baseline_sp regression correction | confound −0.968 노출, framework critical limit 확정 |

전체 cycle 기록: `action_plans/04_filter_refinement_integrated.md`, `action_plans/PLAN04_EXECUTIVE_SUMMARY.md`.

## 6. Results & Documentation Map

**PRIMARY (v6 canonical)**:
- `PIPELINE_2_CLOSURE.md` — **5-step pipeline + final candidates + RQ1-RQ5 + §5.2 Limitations** (source of truth)
- `closure.md` — 4-test verification summary (canonical user-facing)
- `results/s10_inclusion/s10b_v6_pca_rdm_results_{sub-08,sub-09}.json` — Phase B v6 PCA output
- `results/s10_inclusion/s17_hc_loo_results.json` — Strict 7-fold HC LOO
- `results/redteam/` — Exp13-22 null testing evidence

**REFERENCE (prior work)**:
- `action_plans/PLAN04_EXECUTIVE_SUMMARY.md` — Cycle 1~13 이력 (구 cycle15 포함)
- `notion.md` — 전체 서술 (일부 구형 terminology 포함 가능)

**REMOVED (git history only, commit 91796b6 정리에서 삭제 — 필요 시 `git show 91796b6~1:<path>`)**:
- `COMPREHENSIVE_MODEL_RESULTS.md`, `simulation_recoverability_behavior.md` (구 3-모델 비교 / recoverability)
- `LOCO_FILTER_PLAN.md`, `LOCO_FILTER_RESULTS.md`, `results/loco_filter/` (구 single-loss LOCO 설계, v6 이전)

## 7. Rule of Action

1. 작업 시작 전 §0(Framework Decision) → §2(Assumptions) → §3(Per-Subject Status) 순서로 확인.
2. 3 모델 (Machado / R+C / 2-Component) 추가·제거 금지. 사용자 승인 후만.
3. SRM·ΔRDM·xnobis를 fitting primary criterion으로 올리지 않는다 (metric ≠ functional, behav_validation §3 근거).
4. C_baseline은 `machado_shifted_hue(0.0, family)` 기반만 사용 (CIELab nominal 각도 사용 금지).
5. Pre-image는 forward model의 exact 수치 역함수. 근사 실패 시 subject-model 조합 **기각**.
6. **Specificity claim 금지** — descriptive ("HC distribution의 X percentile")만 허용.
7. **Sub-10 분석 시도 금지** — CVD-HC 차이 미포착, downstream 제외.
8. **Selection rule reformulation 금지** — Cycle 9~13에서 13회 시도, 동일 한계 확인.
9. **Model class 결정 = v6 PCA canonical (PIPELINE_2_CLOSURE.md RQ1 FINAL)**. R+C = REJECTED (boundary saturation). LOCO_V4 는 precondition gate 전용; primary metric 아님. behavioral validation (Phase 3 acquisition) = sole CVD-generalization path.
10. SLURM: hV4 전체 fit은 CPU-heavy → node2 `%5~10`, `--mem=16G`.
11. 결과 저장: flat `results/<analysis_name>/` (timestamp 서브디렉토리 금지), per-subject json, batch당 `config.json` 1개.

## 8. Anti-Pattern (자주 빠지는 함정)

- **"Just one more selection rule"**: Cycle 9→10→10b→10c→10d→10e→10f→11→11b→11c→12→13 = 12 cycle, 동일 measurement family. 같은 함정 재진입 금지.
- **"Baseline correction이 specificity 회복"**: Cycle 13에서 각 cell별 baseline_ρ 보정해도 sub-08 외 모두 NOT specific. 보정은 confound를 노출했을 뿐 해결하지 못함.
- **"Cross-ROI가 새로운 information"**: Cycle 11/12에서 V1+V4, V4|V1 등 모두 시도. specificity는 같은 한계, filter parameter는 V4-only와 수렴.
- **"Sub-10 sanity check"**: Sub-10도 specificity 양성으로 나옴 (FP). HC 통제 의미 없음, 제외.
- **"Decoder-confusion LOCO as fresh start"**: behav_validation §4가 같은 voxel covariance + small-n multi-testing 문제 transfer 가능성 명시. §4는 DEFERRED (close가 아님). 재가동 조건은 §4에 명시 — 임의 재가동 금지.
- **"Sub-09 V1 specificity → filter parameters"**: V1은 statistical specificity 보이나 forward fit β_s=β_c=0 degenerate. **Specificity와 estimability는 같은 ROI에서 동시 만족 안 됨** (project_phase2_closure §3 참조). V1을 단독 filter basis로 쓰는 시도 금지. (단, V1 정보를 cross-ROI loss에 추가하는 cycle 12 접근은 허용 — V4 LOCO + V1 RDM/rank가 jointly optimized.)
