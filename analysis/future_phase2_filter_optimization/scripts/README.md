# scripts/ — Pipeline 2 code index

각 script 의 Pipeline 2 step 매핑. 자세한 narrative 는 `../PIPELINE_2_CLOSURE.md` 참조.

## Pipeline 2 core (현재 active)

| Script | Pipeline 2 Step | 역할 |
|---|---|---|
| `s10a_precondition.py` | Step 1 | HC LOO single-loss precondition gate |
| `s10b_v6_pca_rdm.py` | Step 2 + 3 | atom factories + cell enumeration + 5/2 HC split × 300 main runner |
| `s17_hc_loo.py` | Step 3 supplement | strict HC LOO 7-fold (deterministic) |
| `cycle6b_extended_raw_weight.py` | Step 4 | raw-weight scheme sweep (γ_focal + γ_all + α·RDM, 47 schemes) — Step 3 후보 robustness sanity check |
| `s13_round3.py` | Step 5 (Phase D) | multi-point recovery identifiability test on final candidates |
| `s12b_phase_c_v2.py` | (deprecated) | simplex-constrained weight sweep — final selection 기여 없음, L8 limitation 보고용 |

## Helpers (forward models + atoms)

| Script | 역할 |
|---|---|
| `two_comp.py` | 2-Component forward model: `δθ(θ) = β_s·cos(θ−90°) + β_c·cos(θ−θ_conf)` |
| `rc_1dof.py` | R+C forward model: `δθ_RC(c) = (2−g)·δθ_Machado(c; Δλ)` |
| `machado_simulator.py` | Machado cone-shift 1-way base |
| `behav_loss.py` | γ atom factories + JND baseline (HC pool) |
| `neural_loss.py` | LOCO + RDM atoms |
| `utils_forward_model.py` | FE-K basis (`create_basis_full`, `HUE_ANGLES`) |
| `s8_loo_train_test.py` | `DELTA_LAMBDA_BY_FAMILY` dict + HC LOO baseline helper |
| `diagnostic_delta_rdm.py` | `precompute_hc_W` for RDM atoms |

## Legacy / superseded (참조용으로 보관)

| Script | 대체 by |
|---|---|
| `cycle6_raw_weight.py` | `cycle6b_extended_raw_weight.py` (γ_focal 포함 + LOCO cells 포함) |
| `s10b_v2_resample.py` / `_v3_extended.py` / `_v4_single_atom.py` / `_v5_gamma_all.py` | `s10b_v6_pca_rdm.py` (PCA-aligned RDM K=6) |
| `s10b_v6_srm_rdm.py` | `s10b_v6_pca_rdm.py` (BrainIAK SRM 시도 → PCA 가 cleaner) |
| `s10b_cross_roi.py`, `s10b_inclusion_ranking.py` | Phase B v6 통합 |
| `s10_advisor_fixes.py` | Phase B v6 에 반영 |
| `s10c_sub09_cosine.py`, `s10d_sub09_weight_sweep.py` | sub-09 exploratory, Phase B v6 흡수 |
| `s11_*` (pre-Phase-C null sim variants) | Phase B v6 의 stability check 가 대체 |
| `s12_phase_c_weight_sweep.py` (v1) | `s12b_phase_c_v2.py` (v2; v2 도 deprecated) |
| `s13_multipoint_validation.py` (Round 1/2) | `s13_round3.py` (final candidates) |
| `s14_atom_redesign.py` | Cycle 5 결과, PCA-RDM 으로 흡수 |
| `s15_oos_reanalysis.py`, `s16_e2_srm_disparity.py` | Pipeline 3 deprecated |
| `run_sub08_protan_audit.py`, `cycle7b_srm_diagnostic.py`, `cycle7c_pca_diagnostic.py`, `compare_pca_vs_srm_v6.py` | exploratory, closure 에 contribution 없음 |
| `loco_distortion_fit.py`, `loco_filter*.py`, `step*.py`, older s1~s8 | pre-Pipeline 2 시도들 |

(legacy scripts 자체는 폴더에 남겨둠 — 재현성 + 이력 추적용.)

## Run order (Pipeline 2 재현)

```bash
conda activate srm  # local environment

# Step 1: precondition
python scripts/s10a_precondition.py

# Step 2/3: main Phase B v6 (5/2 HC split × 300)
python scripts/s10b_v6_pca_rdm.py --subject sub-08
python scripts/s10b_v6_pca_rdm.py --subject sub-09

# Step 3 supplement: strict HC LOO 7-fold
python scripts/s17_hc_loo.py

# Step 4: raw-weight sanity check
python scripts/cycle6b_extended_raw_weight.py

# Step 5: identifiability (Phase D Round 3)
python scripts/s13_round3.py
```

Outputs → `../results/` (results/README.md 참조).
