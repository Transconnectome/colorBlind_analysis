# Pipeline 2 Framework — Phase B v6 Inclusion Screening

- **Status**: candidate-extraction framework, **closure 검토 단계**
- **Backbone script**: `scripts/s10b_v6_pca_rdm.py`
- **Results**: `results/s10_inclusion/s10b_v6_pca_rdm_results_{sub-08,sub-09}.json`
- **Date**: 2026-05-26

---

## 0. Scope

후보 (β_s, β_c) 또는 (Δλ, g) 추출 + HC normalization robustness 측정. **Selection primary가 아니라 candidate-pool generator + descriptive evidence engine**.

---

## 1. Data + Models (invariant across pipelines)

| 항목 | 내용 |
|---|---|
| Amplitudes | C010 procrustes, shape `(6 runs × 8 colors × n_vox)` per (subject, ROI) |
| HC pool | sub-01..07 (n=7); hV4 effective n=6 (sub-07 16 voxels → nan) |
| CVD | sub-08 deutan, sub-09 protan |
| ROIs | V1, V2, V3, V4 (= hV4 on disk) |
| Models | Machado 1-way / R+C 1-DOF (g grid) / 2-Component 2-DOF (β_s × β_c grid) |
| Encoder | ridge_gcv (locked, §A10) |
| Behavioral | per-pair JND (OY, YG, YP, GB, RG, etc.); CVD는 pair당 **N=1 measurement** |

---

## 2. Atoms

| Atom | Definition | Range |
|---|---|---|
| `γ_pair` (γOY, γYG, γYP, γGB) | per-pair JND z² vs HC pool baseline | 0 ~ ~50 |
| `γ_all` | 8-pair JND z² 합 | 0 ~ ~100 |
| `rdm_{V1..V4}` | A2 PCA-aligned RDM (K=6) cosine distance to HC mean | 0 ~ 2 |
| `loco_V4` | V4 LOCO ρ-based loss (within-CVD ridge prediction) | scalar |

**Atom info density 차이**:
- γ_pair: 1 z² scalar
- γ_all: 8 z² 합 (info-dense)
- RDM: 28 pair distances → cosine scalar
- LOCO: V4 voxel-prediction prediction error

---

## 3. Fit (per draw, 300 draws)

```
HC pool (7) ──┐ random split (seed=42 + sub_id)
              ├─→ train HC (5) ──→ atom 구성 (γ baseline + RDM HC mean)
              └─→ test HC (2)  ──→ test eval atom (재계산)
CVD JND   ────┴──→ single measurement, train/test 양쪽 reused
CVD amp   ────┴──→ shared

for each combo (γ_pairs × RDM_rois × {LOCO, noLOCO}):
    composite_train(δ) = Σ z(atom_train(δ)) / √n_atoms
    fit point = argmin_grid composite_train(δ)  # R+C: g grid; 2-comp: β_s × β_c
    test_loss(fit) = Σ (atom_test(fit) − μ_train) / σ_train, normalized by √n_atoms
    test_per_pair = γ z² per pair on test HC baseline
    test_agg = γ_all on test HC pool
    test_V1_RDM = V1 RDM cosine on test HC pool
```

**Z-score**: *grid-relative*, not HC-relative (atom 값들을 model parameter grid 위에서 normalize).

---

## 4. Combos (cells)

| Subject | γ options | RDM options | LOCO options | Total cells |
|---|---|---|---|---|
| sub-08 | [], [OY], [YG], [YP], [OY,YG,YP], [ALL] | [], [V1], [V2], [V3], [V4], [V1,V4] | [], [V4] | 71 |
| sub-09 | [], [GB], [ALL] | [], [V1] | [], [V4] | 11 |

(combo "all-empty" 제외; sub-09는 prior diagnostic 결과로 RDM은 V1만)

---

## 5. Outputs (per cell, per model)

### 5.1. Field 정의

| Field | Meaning | Use |
|---|---|---|
| `n` | resample 수 (=300) | sanity |
| `train_loss_median` / `_iqr` | composite_train minimum 분포 | fit stability |
| `test_loss_median` / `_iqr` | test composite 값 (z-rescaled by train stats) | **P2 sort key** |
| `test_focal_median` / `_iqr` | focal pair z² on test (각 subject 의 focal pair = sub-08 YP, sub-09 GB) | behavioral fit (focal pair) |
| `test_agg_median` / `_iqr` | γ_all 8-pair z² sum on test | behavioral fit (aggregate) |
| `test_V1_RDM_median` / `_iqr` | V1 PCA-aligned RDM cosine on test | neural geometry fit |
| `test_per_pair_medians` | per-pair z² on test (8 entries) | per-pair behavioral fit |
| `boundary_rate` | argmin이 grid boundary에 떨어진 비율 | degeneracy indicator |
| `aic_median`, `bic_median` | AIC/BIC at test_focal_median, k=K_RC(1) 또는 K_2C(2), n=2 | model complexity penalty |
| `param_summary` | g_median 또는 (β_s_median, β_c_median) + IQR | fitted parameter + 안정성 |

### 5.2. Per-model best supplementary metrics (advisor 권고 gates 적용)

**Gates** (Pipeline 3 §5와 동일):
- G1 Collapse: `test_loss_iqr > 50` OR `sign(train) ≠ sign(test) AND |test−train| > 5`
- G2 Boundary: `boundary_rate < 0.5`
- G3 P2 sort: `(test_loss_median ASC, test_loss_iqr ASC)`, LOCO IQR=+∞

Per-model best 후보 + supplementary metrics table은 **`PIPELINE_3_FRAMEWORK.md §5`** 참조 (sub-08 R+C/2-comp top-3, sub-09 R+C/2-comp top-3, supplementary metrics: param_IQR, train_loss, test_med±iqr, test_focal, test_agg, test_V1_RDM, AIC, BIC, boundary_rate 포함).

---

## 6. 4 Justification Points (user-directive 2026-05-26)

### 6.1. Multi-point sim 식별 불가능 한계

**Round 1 결과**: S08-E_v4 (β_s=38, β_c=−44) recovery median=−26, β_c IQR=**98°** → DECISION §4 E3 기준 (IQR<30, ±10°) FAIL.

**Paper-level qualification (반드시 명시)**:
> Forward model parameters are not uniquely identifiable around the fit point. Behavioral validation of the chosen filter (Phase 3) tests whether *this particular* (β_s, β_c) produces the predicted perceptual effect — it does NOT establish that this is the unique parameter set capable of producing the observed neural pattern. Local flatness of the model surface around the fit means alternative (β_s, β_c) values consistent with the neural data may also pass behavioral validation.

이 한계는 **Phase 3 행동 실험 완료 후에도 유효**한 paper limitation.

### 6.2. Raw-weight scheme (Cycle 6 retry, behav loss만 변경)

현재 v6 pipeline은 z-score composite. Cycle 6에서 raw `γ_all`이나 `γ_all + α·RDM` weight scheme로 re-ranking 시도됨 (`scripts/cycle6_raw_weight.py`). 

**중요 fact**: raw-weight scheme은 *combo 정의*와 *atom 구성*은 그대로. **Argmin 단계의 composite formula만 변경**. 따라서 v6 pipeline 자체 (HC subset split, 300 draws, atom 계산, train/test) 재실행 불필요. 기존 v6 JSON으로 후처리만 하면 됨 — `cycle6_raw_weight.py:64-74`의 `compute_composite(rows)` 로직 그대로 활용 가능.

향후 작업:
- γ_focal (1-pair) atom 제거 + γ_all + RDM raw weight 조합으로 candidate re-rank
- Cycle 3-4 결과 (z-score atom-equalization)와 비교
- z-score grid-relative normalization은 잔여 한계로 paper에 명시 ("descriptive weight choice, not optimum")

### 6.3. OOS 축 = HC normalization robustness; uniqueness 한계

**framing 정정**:
- OOS 축 = HC pool composition robustness
- 측정 대상 = parameter estimate가 HC sample 변동에 견고한가
- **측정하지 않는 것** = CVD에 대한 generalizability (CVD JND는 N=1, train/test 동일)

**개인화 필터 framing으로 정당화**: unseen-CVD generalizability는 *개인화* framework에서 본질적으로 불필요. 진정한 검증은 *그 individual에게* filter가 작동하는가 (Phase 3 행동 실험).

**Uniqueness 한계 명시** (paper):
> The selection pipeline measures whether the fitted parameters are stable across HC-pool resamples (HC normalization robustness). It does not establish that the fitted parameters are the *unique* solution explaining the CVD subject's neural pattern. Multi-point recovery simulations (§6.1) confirm local flatness around the optimum.

### 6.4. Behav-loss 사용 + HC stability check 검증 (현재 결과)

**(1) Behav loss 사용 cells**:

| Subject | Behav-used (γ atom 포함) | RDM/LOCO only |
|---|---|---|
| sub-08 | 60/71 (84%) | 11/71 |
| sub-09 | 8/11 (73%) | 3/11 |

→ candidates 대부분이 behav loss를 fit objective에 포함. behavior-blind candidate는 control 비교용으로 남음.

**(2) HC stability check + train/test 적용**:

| 항목 | 확인 |
|---|---|
| 모든 cell이 N=300 resample 통과 | ✓ (`s10b_v6_pca_rdm.py:49, 353-357`) |
| 5-train HC로 atom 구성, 2-test HC로 eval | ✓ (`:422, :462-477`) |
| Train/test HC가 fit objective와 evaluation을 분리 | ✓ |
| CVD JND는 train/test 양쪽 동일 single measurement | ✓ (`:340`) — §6.3 framing으로 정당화 |
| Held-out focal pair의 CVD obs reuse | ✓ — paper disclosure 필요 (위 §6.3) |

---

## 7. Identifiability + Robustness 약점 (paper limitation 명시 항목)

| 약점 | 증거 | Paper-level 표현 |
|---|---|---|
| Multi-point sim 식별 실패 | β_c IQR=98° at S08-E_v4 (Round 1) | "Parameters locally non-identifiable; behavioral validation tests effect of chosen filter, not uniqueness" |
| Z-score atom info density 균등화 | 1-pair γ ↔ 8-pair γ_all 동등 기여 | "Atom weighting reflects descriptive choice; raw-weight scheme (Cycle 6) explored" |
| OOS 축 한계 | CVD JND N=1; HC split만 OOS | "OOS axis = HC normalization robustness; CVD generalizability requires Phase 3 behavioral experiment" |
| Held-out focal CVD obs reuse | 같은 CVD pair JND가 fit objective held-out + test eval 양쪽 | "Focal pair excluded from fit objective; same pair's CVD measurement enters test under different HC normalization. Under individualized-filter framing this is not data leakage" |
| HC n=7 (hV4 effective 6) | sub-07 hV4 nan | "Limited HC pool; sub-04 outlier impact reported via bootstrap" |
| Boundary fits | g=3.00 (R+C upper boundary) for many sub-08/09 cells | "R+C model saturates at upper g boundary for both CVD subjects, consistent with R+C insufficiency for full cone-shift signal" |

---

## 8. Closure 후보 평가 (user directive: closure 가능성)

### 8.1. Closure 가능 조건 (제안)

Pipeline 2를 *candidate-pool generator + HC-robustness check + paper-level descriptive evidence*로만 위치시키고, **selection primary는 §0 LOCO-best + Phase 3 행동 실험**으로 명시하면 Pipeline 2 자체는 closure 가능.

남은 작업 (closure 직전):
1. (선택) Cycle 6 raw-weight scheme 재실행 — 위 §6.2 (z-score 우회 시도)
2. (선택) γ_focal (1-pair) atom 제거 + γ_all + RDM 조합으로 candidate set 재정리
3. Identifiability/robustness 5개 약점을 paper limitation으로 명시화 (위 §7 table)

### 8.2. Closure 후 산출물

- Sub-08 후보 set (R+C g=2.60, 2-comp (50,−36)/(14,−46) 등) — descriptive label, HC robustness evidence 포함
- Sub-09 후보 set (R+C g=3.00 Boehm_low, 2-comp (2, 24) 등) — 동일
- 각 후보의 HC bootstrap percentile + multi-point recovery + boundary rate를 paper에 보고

### 8.3. Open question (advisor에 질의)

- Multi-point sim Round 3는 Pipeline 2 closure 전 필수인가, Phase 3 행동 실험 결과 도착 후 supplementary로 충분한가
- §6.2 raw-weight scheme이 closure 전 반드시 시도되어야 하는가
- §6.4 behav-blind cells (RDM/LOCO only) 11+3개는 control 비교 evidence로 paper에 포함할 가치가 있는가

---

## 9. Files

- `scripts/s10b_v6_pca_rdm.py` — Phase B v6 main runner (300 resample × cells)
- `scripts/cycle6_raw_weight.py` — raw-weight composite post-processor
- `scripts/cycle7b_srm_diagnostic.py` — BrainIAK SRM RDM atom diagnostic
- `scripts/s13_multipoint_validation.py` — Round 1/2 identifiability simulation
- `scripts/behav_loss.py` — γ atom + JND baseline
- `scripts/neural_loss.py` — LOCO + RDM atoms
- `scripts/rc_1dof.py`, `scripts/two_comp.py` — forward model grids
- `results/s10_inclusion/s10b_v6_pca_rdm_results_{sub-08,sub-09}.json` — main output
- `results/multipoint_validation/round1_*.json` — identifiability simulation
