# Cone Shift Pipeline — Gen-4 (Machado-Anchored, L₃ Fine-Tune)

## 1. Purpose

This pipeline fits a **physiologically grounded cone-shift parameter Δλ** to
each CVD subject from their fMRI ΔRDM and feeds it into the Phase-2
stimulus-space filter. Three prior generations failed:

- **Gen-1 (SRM-RDM)** — SRM rotation absorbed the cone-shift signal.
- **Gen-2 (LOCO W-fixed)** — worked for sub-08 V1/V2 but failed sub-09 on every ROI.
- **Gen-3 (ΔRDM Differential Evolution)** — 0/18 cases passed tiered evaluation;
  optimizer drifted to unconstrained L+M double shifts
  (`archive/gen3/DIAGNOSIS_DRDM_FAILURE.md`).

**Gen-4 anchors the search to Machado, Oliveira & Fernandes (2009) Eq 5/6**,
an area-preserving cone-mixture simulator with a single free parameter
Δλ ∈ [0, 20] nm. Cone-type exclusivity (protan → L only, deutan → M only)
and the 0.96 × (Area_L/Area_M) D65 calibration are built into the model,
removing the Gen-3 convergence failures by construction. After coarse
Machado anchoring, ΔRDM (V1+V2) drives a narrow L₃ fine-tune, and **hV4
is held out** for NEURAL validation while the independent Machado simulator
provides COGNITION validation.

## 2. Pipeline diagram

```
  C010 amps + Stockman                              Machado Eq 5/6
          │                                              │
          ▼                                              ▼
  ┌─────────────────┐                          ┌───────────────────┐
  │ Stage 0         │                          │ machado_simulator │
  │ precompute      │◄─────────────────────────│ (Area-preserving) │
  │ HC W, ΔRDM_obs  │                          └───────────────────┘
  └────────┬────────┘                                   ▲
           │                                            │
           ▼                                            │
  ┌─────────────────┐      coarse Δλ       ┌────────────┴──────┐
  │ Stage 1         │──────anchor──────────▶│ machado_shifted   │
  │ Machado anchor  │       per ROI         │ hue() grid        │
  │ grid search     │                       └───────────────────┘
  └────────┬────────┘
           │ Δλ_V1*, Δλ_V2*
           ▼
  ┌─────────────────┐
  │ Stage 2         │  joint V1+V2 L₃ = L₁ − λ_scale·L_scale − λ_ROI·L_ROI
  │ L₃ fine-tune    │  ±3 nm narrow box, 0.1 nm step, exact 8! perm null
  └──┬───────────┬──┘
     │           │
     │           │ best Δλ_V1, Δλ_V2
     ▼           ▼
┌───────────┐ ┌──────────────┐
│ Stage 3a  │ │ Stage 3b     │
│ NEURAL    │ │ COGNITION    │
│ hV4 LOCO  │ │ Machado      │
│ 8! perm   │ │ canonical    │
│           │ │ hue_mse,cos  │
└────┬──────┘ └──────┬───────┘
     │               │
     └─────┬─────────┘
           ▼
  ┌─────────────────┐
  │ Stage 4         │  summary_table.csv + figures
  │ aggregation     │  verdict ∈ {PASS, NEURAL_ONLY, COGNITION_ONLY, HOLD}
  └─────────────────┘
```

## 3. Stage-by-stage table

| Stage | Script | Inputs | Outputs | Metric | Reused helpers |
|---|---|---|---|---|---|
| 0 | `step0_precompute.py` | C010 amps, Stockman fundamentals | `hc_W_{V1,V2,hV4}.npz`, `delta_rdm_obs_*.npz`, `stockman_grid.npz`, `machado_gray_check.json` | gray-point Δ ≤ 2° | `precompute_hc_W`, `compute_delta_rdm_obs`, `load_stockman_fundamentals`, `verify_machado_gray_point` |
| 1 | `step1_machado_anchor.py` | Stage-0 cache | `sub-*_{ROI}_{model}.json` (sweep + best) | cosine(ΔRDM_sim, ΔRDM_obs) | `get_design_matrix`, `compute_delta_rdm_sim`, `cosine_similarity`, `machado_shifted_hue` |
| 2 | `step2_finetune_l3.py` | Stage-0/1 | `sub-*_{model}.json` (joint V1+V2, 8! perm) | L₃ (cosine − reg.) | `L3_MachadoV1V2.compute/permutation_null` |
| 3a | `step3_validate_neural.py` | Stage-0/2 | `sub-*_{model}.json` NEURAL | Spearman ρ, 8! label/improvement perm | `simulate_mean_hc_wfixed`, `permutation_test_spearman/improvement`, `load_cvd_loco_target` |
| 3b | `step3_validate_cognition.py` | Stage-0/2 | `sub-*_{model}.json` COGNITION | angular hue MSE (deg²), ΔRDM_sim cosine | `apply_distortion`, `compute_delta_rdm_sim`, `machado_shifted_hue` |
| 4 | `step4_summary.py` | Stage-1/2/3 | `summary_table.csv`, `figures/*.png` | verdict tally | — |

## 4. Filter models

| Model | df | Bounds | Role | Dispatched via |
|---|---|---|---|---|
| `machado_1way` | 1 | Δλ ∈ [0, 20] nm, α coupled = (20−Δλ)/20 | **primary** — Machado Eq 5/6 | `machado_simulator.machado_shifted_hue` |
| `machado_alpha_free` | 2 | Δλ ∈ [0, 20], α ∈ [0, 1] independent | candidate — decouples severity | `machado_alpha_free_fundamentals` |
| `cone_3way` | 3 | δL, δM, δS ∈ [−30, 30] nm | **ablation only** (Gen-3 failure mode) | `utils_cone_3way.compute_shifted_hue_3way` |

Legacy `fourier` / `per_color` entries remain in `utils_distortion_models.py`
for backwards compatibility but are intentionally excluded from Stage 2+.

## 5. L₃ loss

Per-ROI base similarity:
```
L₁_ROI(Δλ) = cosine_similarity(ΔRDM_sim_ROI(Δλ), ΔRDM_obs_ROI)
```

Joint L₁ (V1 + V2, equal weights):
```
L₁ = 0.5·L₁_V1(Δλ_V1) + 0.5·L₁_V2(Δλ_V2)
```

Regularisers:
```
L_scale  = [max(0, |Δλ_V1| − 20)]² + [max(0, |Δλ_V2| − 20)]²
Δλ̄₁₂    = (Δλ_V1 + Δλ_V2) / 2
L_ROI    = (Δλ_V1 − Δλ̄₁₂)² + (Δλ_V2 − Δλ̄₁₂)²  =  (Δλ_V1 − Δλ_V2)² / 2
```

Full loss (maximised):
```
L₃ = L₁ − λ_scale · L_scale − λ_ROI · L_ROI
```

**Defaults**: `λ_scale = 0.01`, `λ_ROI = 0.005`, `Δλ_max = 20 nm`.
Implementation: `scripts/l3_loss.py :: L3_MachadoV1V2`.

Stage-2 permutation null: **exact 8! = 40,320 joint V1+V2 label permutations**
on ΔRDM_obs; `L_scale` and `L_ROI` are held constant across permutations
(they depend only on Δλ, not on labels). Two p-values per fit:
- `label_perm_p` — vs random label structure
- `baseline_improvement_p` — vs Δλ = 0 null

## 6. Validation matrix

| Aspect | Method | Source script | Held out? | Primary statistic |
|---|---|---|---|---|
| **NEURAL** | hV4 LOCO vulnerability, simulated via W-fixed mean-HC, Spearman ρ vs CVD observed LOCO, exact 8! permutation | `step3_validate_neural.py` | **Yes** — hV4 never enters the L₃ loss | `label_perm_p`, `baseline_improvement_p` |
| **COGNITION** | Fitted hue profile vs Machado canonical (5/10/15/20 nm), angle-wrapped MSE; ΔRDM_sim cosine between fit and canonical | `step3_validate_cognition.py` | **Yes** — independent published simulator | `hue_mse_deg2`, `drdm_cos` |

**Dual-validation verdict** (row-level in `summary_table.csv`):

| Verdict | NEURAL `label_perm_p` | COGNITION `hue_mse_deg2` |
|---|---|---|
| `PASS`            | ≤ 0.05 | ≤ 15 |
| `NEURAL_ONLY`     | ≤ 0.05 | >  15 |
| `COGNITION_ONLY`  | > 0.05 | ≤ 15 |
| `HOLD`            | > 0.05 | >  15 |

sub-10 (normal-color-vision control) should generally land in `HOLD` as a
specificity check.

## 7. Execution

**Sequential (interactive on node2)**:
```bash
ssh node2
conda activate nilearn
cd /scratch/connectome/haba6030/colorBlind/analysis/future_phase2_filter_optimization/cone_shift_pipeline

mpirun -np 1 python scripts/step0_precompute.py        --output_dir results/step0_precompute
mpirun -np 1 python scripts/step1_machado_anchor.py    --step0_dir results/step0_precompute --output_dir results/step1_machado_anchor
mpirun -np 1 python scripts/step2_finetune_l3.py       --step0_dir results/step0_precompute --step1_dir results/step1_machado_anchor --output_dir results/step2_finetune_l3
mpirun -np 1 python scripts/step3_validate_neural.py   --step0_dir results/step0_precompute --step2_dir results/step2_finetune_l3 --output_dir results/step3_neural
mpirun -np 1 python scripts/step3_validate_cognition.py --step0_dir results/step0_precompute --step2_dir results/step2_finetune_l3 --output_dir results/step3_cognition
mpirun -np 1 python scripts/step4_summary.py           --step1_dir results/step1_machado_anchor --step2_dir results/step2_finetune_l3 --step3_neural_dir results/step3_neural --step3_cognition_dir results/step3_cognition --output_dir results/step4_summary
```

**Batch (SLURM, node2 CPU)**:
```bash
sbatch analysis/future_phase2_filter_optimization/cone_shift_pipeline/sbatch/run_gen4.sbatch
```
The sbatch file wraps every python call in `mpirun -np 1` per the BrainIAK
MPI fix (`MEMORY.md`), uses `--no-requeue`, an absolute `--chdir`, and omits
`--qos` / `--partition` per the server's SLURM configuration.

---

## Folder layout

```
cone_shift_pipeline/
├── README.md                                     # this file
├── archive/                                      # Gen-1/2/3 (preserved)
│   ├── gen1/  gen2/  gen3/
│   ├── DIAGNOSIS_DRDM_FAILURE.md
│   └── TIERED_EVALUATION_DETAILS.md
├── scripts/
│   ├── machado_simulator.py                      # Machado Eq 5/6 + gray-point check
│   ├── l3_loss.py                                # L3_MachadoV1V2 (subclass of BaseLoss)
│   ├── step0_precompute.py                       # HC W + ΔRDM_obs + Stockman cache
│   ├── step1_machado_anchor.py                   # coarse Δλ grid
│   ├── step2_finetune_l3.py                      # joint V1+V2 L3 + 8! null
│   ├── step3_validate_neural.py                  # hV4 LOCO transfer
│   ├── step3_validate_cognition.py               # Machado canonical agreement
│   ├── step4_summary.py                          # CSV + figures
│   ├── utils_distortion_models.py                # + machado_1way/alpha_free
│   ├── utils_cone_3way.py                        # Stockman loader (legacy)
│   ├── diagnostic_delta_rdm.py                   # ΔRDM helpers
│   ├── step1_fit_loco_v2.py                      # W-fixed simulator + LOCO loaders
│   └── visualize_cone_shift_colors.py            # STIM_LAB / lab2rgb
├── sbatch/
│   └── run_gen4.sbatch                           # single SLURM entry point
└── results/
    ├── step0_precompute/
    ├── step1_machado_anchor/
    ├── step2_finetune_l3/
    ├── step3_neural/
    ├── step3_cognition/
    └── step4_summary/
```

**Key references**
- Machado, Oliveira & Fernandes (2009). *IEEE TVCG* 15(6):1291–1298.
- Stockman & Sharpe (2000). 2° cone fundamentals.
- Plan file: `~/.claude/plans/merry-baking-squid.md`
