# future_phase2_filter_optimization — CLAUDE.md : CURRENT FOCUS

**Stage B + C** · **Status**: ACTIVE.

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
| A12 | 2-component은 CIELab opponent space 작동 | RGB/cone space 아님. C_baseline은 `machado_shifted_hue(0.0, family)` (CIELab nominal 각도 금지). |

## 2.5. Loss Inventory + HC Sanity Check (NEW 2026-05-03, CI-revised 2026-05-04)

**Document**: `results/inventory/loss_inventory.{md,csv}` (15 loss variants × 8 subjects)

**Verdict 기준 (CI-based, robust to single HC outliers)**:
- For each (loss × subject): bootstrap HC mean (10000 resamples) → `boot_frac` = fraction of HC means below CVD norm.
- **✓✓ both sig** = both CVD `boot_frac` ≥ 0.975 (one-sided 95% CI)
- **~~ marginal** = both CVD 0.90 ≤ `boot_frac` < 0.975
- **✗ inside HC CI** = `boot_frac` < 0.90

이전 rank-based emp_p (1/6, 2/6 등 discrete)는 sub-04 같은 outlier 1개에 sensitive — CI 기반으로 변경.

**Top results**:

1. **`cycle15_opt2_v4mwj_v1lrank`** = `2·mw_jaccard(V4) + 1·l_rank(V1) + 0.2·Tikh`
   - sub-08 boot_frac=**1.000** (HC 누구도 sub-08보다 위 아님)
   - sub-09 boot_frac=**0.996** (CVD가 boot mean 분포의 99.6% 위)
   - **caveat**: sub-09는 HC가 양극화 분포 (4 HC very low + sub-04/05 high) 덕분에 wide CI, sub-09 (norm 69.7)는 sub-04 (77.2) 옆 zone에 위치. sub-04 outlier 의존 (제외 시 boot_frac 1.000으로 더 강해짐).
   - sub-08 (β_s=68, β_c=−38) — same as Cycle 12; sub-09 (β_s=44, β_c=+54) — same as mw_jaccard alone

2. **`mw_jaccard_loss`** @ V4 (alone) — **~~ marginal** (CI-based 강등)
   - sub-08 boot_frac=0.94, sub-09 boot_frac=0.97 (둘 다 0.975 미달)
   - HC 분포가 좁음 (34-78) → CVD가 같은 zone, distinct 약함
   - 이전 ✓✓ 평가는 rank-based의 outlier-단감도 한계

✓ one sig: `cycle12_cross_roi`, `l_dir`, `pearson_r`, `spearman_r`, `l_rank`, `l_mag`, `cycle15_opt3`, `cycle15_opt4`
~~ marginal: `mw_jaccard_loss` (alone), `norm_resid`, `l_rank_V1`
✗ inside CI: `l_topk_V1`, `sign_agree`, `l_topk_jaccard`

**정직한 결론**:
- **Sub-08**: 여러 loss가 strong distinct — robust signal across formulations
- **Sub-09**: cycle15_opt2만 ✓ sig, 그러나 sub-04 HC outlier 위치에 의존. **어떤 loss도 sub-04 outlier-independent 한 strong distinct 만들지 못함**. 행동 검증 결정적.

**중요한 함의**:
1. 사용자 (Q3, 2026-05-03) 통찰 evidence-confirmed: **현재 모든 loss는 HC vs CVD 통계적 구별 weak** (단 mw_jaccard_loss 예외)
2. Sub-09는 어떤 single-ROI loss로도 unambiguously distinct 안 됨 — cross-ROI 또는 mw_jaccard만이 가능성
3. **Phase A canonical L_LOCO HC fit 빠짐** — re-run 필요 (sub-01~07 V1, V4 2-component fit)
4. HC pool sub-04 outlier가 most loss에서 mean 왜곡 — bootstrap이 이를 robust하게 평가

## 2.6. HC Specificity Check Mandate (2026-05-10)

Any new filter (β_s, β_c) MUST be checked before behavioral testing.

```bash
python scripts/hc_specificity_check.py --beta_s <val> --beta_c <val> --cvd_type deutan --roi V4
```

Verdicts: ✓✓ boot_frac≥0.975 | ~~ 0.90–0.975 | ✗ <0.90

**§0 rule: DESCRIPTIVE ONLY — cannot override behavioral validation.**

Known results (V4, deutan, boot 10000):
| Filter | norm | boot_frac | Verdict |
|---|---|---|---|
| Canonical (38,−14) | 40.5° | 0.517 | ✗ |
| V4-only (38,+7) | 38.6° | 0.299 | ✗ |
| Cycle14 (58,−36) | 68.3° | 1.000 | ✓✓ |

## 3. Per-Subject Status (UPDATED 2026-05-17 — Phase 2 closed, LOCO-canonical adopted)

**Source of truth (machine-readable)**: `results/BEST_summary.json`
**Narrative**: `results/SUMMARY.md`
**Forward pipeline writeup**: `results/c3_relabel/SCIENTIFIC_NARRATIVE_2026-05-16.md`
**Rejected candidates (records only)**: `results/c3_relabel/NEAR_CONTROLS.md`

This section is a **redirect, not a duplicate**. Numbers live in `BEST_summary.json` to avoid drift. Below: only the load-bearing decisions every session must respect.

### Phase 2 final filter (2026-05-17)
- Filter form: **2-component standalone** (cortical opponent rotation in CIELab)
- Loss: `L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth` @ V4 hV4 LOCO (`loco_distortion_fit.py:200`)
- Per-subject (β_s, β_c): see `BEST_summary.json` ★ canonical source
- Pre-image: 8/8 exact for both subjects

### Deprecated (DO NOT REVERT)
- **Option C** (40,+26)/(12,−28) adopted 2026-05-13 — corrected-label P2a is 0.500/0.887; **deprecated 2026-05-17**.
- **R+C 2-stage as filter form** (advisor 2026-05-16 1st call) — empirically falsified by Check 4 (P2a 0.588/0.787 < LOCO-canonical 0.750/0.975); **advisor reversal 2026-05-16 2nd call**.
- R+C decomposition (Δλ, g) RETAINED as paper diagnostic — explains differential per-subject etiology — NOT as filter form.

### sub-10 (제외, §A7 unchanged)
- 분석 대상 아님.

## 4. Active Deliverables (Phase 2 종결 전)

1. **Sub-09 behavioral protocol** + 시각화 자료 (Track A, Plan agent 진행 중)
2. **Sub-08 fine grid** (Track B1) — c2 orange 정밀화
3. **Sub-08 c8 variant** (Track B2) — magenta 정밀화
4. **Phase 2 closure document**: 두 피험자 최종 필터 + behavioral evidence 요약

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

- `behav_validation.md` — 참고만 (discriminability 기준 PASS이며 P2a-restoration 기준은 아님, 2026-05-13 보류)
- `notion.md` — 모델·피팅·pre-image 전체 서술
- `LOCO_FILTER_PLAN.md`, `LOCO_FILTER_RESULTS.md` — 필터 디자인 결정
- `COMPREHENSIVE_MODEL_RESULTS.md` — 3 모델 비교
- `PIPELINE_WFIXED.md` — W-fixed 파이프라인
- `action_plans/PLAN04_EXECUTIVE_SUMMARY.md` — Cycle 1~13 통합 서술
- `results/loco_filter/preimage_2component/` — sub-08/09 V4 pre-image JSON
- `results/loco_filter/phase_a_2component/` — 2-component fit 결과
- `simulation_recoverability_behavior.md` — recoverability 분석

## 7. Rule of Action

1. 작업 시작 전 §0(Framework Decision) → §2(Assumptions) → §3(Per-Subject Status) 순서로 확인.
2. 3 모델 (Machado / R+C / 2-Component) 추가·제거 금지. 사용자 승인 후만.
3. SRM·ΔRDM·xnobis를 fitting primary criterion으로 올리지 않는다 (metric ≠ functional, behav_validation §3 근거).
4. C_baseline은 `machado_shifted_hue(0.0, family)` 기반만 사용 (CIELab nominal 각도 사용 금지).
5. Pre-image는 forward model의 exact 수치 역함수. 근사 실패 시 subject-model 조합 **기각**.
6. **Specificity claim 금지** — descriptive ("HC distribution의 X percentile")만 허용.
7. **Sub-10 분석 시도 금지** — CVD-HC 차이 미포착, downstream 제외.
8. **Selection rule reformulation 금지** — Cycle 9~13에서 13회 시도, 동일 한계 확인.
9. **Behavioral validation 보류** (2026-05-13). discriminability-PASS는 P2a-restoration 검증을 의미하지 않음. P2a 기반 protocol 재설계 전까지 model class 결정은 LOCO ρ만 사용.
10. SLURM: hV4 전체 fit은 CPU-heavy → node2 `%5~10`, `--mem=16G`.
11. 결과 저장: flat `results/<analysis_name>/` (timestamp 서브디렉토리 금지), per-subject json, batch당 `config.json` 1개.

## 8. Anti-Pattern (자주 빠지는 함정)

- **"Just one more selection rule"**: Cycle 9→10→10b→10c→10d→10e→10f→11→11b→11c→12→13 = 12 cycle, 동일 measurement family. 같은 함정 재진입 금지.
- **"Baseline correction이 specificity 회복"**: Cycle 13에서 각 cell별 baseline_ρ 보정해도 sub-08 외 모두 NOT specific. 보정은 confound를 노출했을 뿐 해결하지 못함.
- **"Cross-ROI가 새로운 information"**: Cycle 11/12에서 V1+V4, V4|V1 등 모두 시도. specificity는 같은 한계, filter parameter는 V4-only와 수렴.
- **"Sub-10 sanity check"**: Sub-10도 specificity 양성으로 나옴 (FP). HC 통제 의미 없음, 제외.
- **"Decoder-confusion LOCO as fresh start"**: behav_validation §4가 같은 voxel covariance + small-n multi-testing 문제 transfer 가능성 명시. §4는 DEFERRED (close가 아님). 재가동 조건은 §4에 명시 — 임의 재가동 금지.
- **"Sub-09 V1 specificity → filter parameters"**: V1은 statistical specificity 보이나 forward fit β_s=β_c=0 degenerate. **Specificity와 estimability는 같은 ROI에서 동시 만족 안 됨** (project_phase2_closure §3 참조). V1을 단독 filter basis로 쓰는 시도 금지. (단, V1 정보를 cross-ROI loss에 추가하는 cycle 12 접근은 허용 — V4 LOCO + V1 RDM/rank가 jointly optimized.)
