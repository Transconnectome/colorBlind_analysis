# scripts/ — Phase 2 Filter Optimization

Last updated: 2026-05-04 (subdir restructure: 65+ files → 9 semantic categories)

## Top-level (core libraries + main pipeline entry points)

**Core importable modules** (do NOT run directly — imported by others):
- `loco_distortion_fit.py` — main `grid_search`, `FILTER_MODELS`, default L_LOCO
- `step1_fit_loco_v2.py` — ridge_gcv, mean_hc_loco simulation
- `step1_machado_anchor.py` — Machado cone shift fitting
- `machado_simulator.py` — Stockman cone fundamentals
- `retinal_cortical.py` — R+C model
- `utils_distortion_models.py`, `utils_cone_3way.py` — basis + utilities
- `preimage_filter_search.py`, `preimage_separation_search.py` — pre-image search
- `diagnostic_delta_rdm.py` — ΔRDM observed/simulated computation
- `l3_loss.py` — L3 loss formulation

**Main pipeline entry points** (run sequentially):
- `step0_precompute.py`, `step0_srm_precompute.py` — Phase A precomputes
- `step2_finetune_l3.py`, `step2_finetune_l3_v2.py` — L3 finetune
- `step2c_retinal_cortical.py` — R+C fits
- `step3_validate_cognition.py`, `step3_validate_neural.py` — validation
- `step4_summary.py` — final summary
- `comprehensive_2component_analysis.py` — 2-component canonical analysis

**Active loss optimization** (cross-criterion losses for current candidates — promoted from cycles/ on 2026-05-04 since they define current main trial losses):
- `cycle12_loss_cross_roi.py` — `L = α·l_topk(V4) + β·l_rank(V1) + 0.2·Tikh`
- `cycle14_v1_rdm_cross.py` — `L = α·l_topk(V4) + β·(1-cos(ΔRDM_V1)) + 0.2·Tikh`
- `cycle15_mwjaccard_cross.py` — **CURRENT WINNER**: `L = 2·mw_jaccard(V4) + 1·l_rank(V1) + 0.2·Tikh` → ✓✓ both CVD distinct from HC

These read landscape data from `results/cycles/` and write outputs back there, but their .py is at top-level because they define the active main loss formulations.

## Subdirs (semantic categories)

```
scripts/
├── cycles/             Cycle 1~15 work (was cycle_filter_refinement)
├── refinement/         Per-subject refinement (sub-08, sub-09 fits + viz)
├── diagnostics/        Ad-hoc diagnostic analyses
├── filter_ops/         Filter design + evaluation
├── visualization/      All viz scripts (visualize_*, figs_*)
├── inventory/          Summary table builders (build_loss_inventory, etc.)
├── older_cycles/       Pre-Cycle 9 (referenced by current cycles/)
└── slurm/              SLURM batch + shell scripts
```

## Path convention

All scripts in subdirs use:
```python
_SCRIPT_DIR = Path(__file__).resolve().parent           # subdir/
sys.path.insert(0, str(_SCRIPT_DIR.parent))             # add scripts/ to path
import loco_distortion_fit                              # core modules accessible
```

For results paths, use:
```python
_PHASE2_ROOT = _SCRIPT_DIR.parent.parent                # future_phase2_filter_optimization/
out_dir = _PHASE2_ROOT / 'results' / 'fits' / ...
```

## Migration log (2026-05-04)

| Old | New |
|---|---|
| `cycle_filter_refinement/` | `cycles/` |
| `sub08_*.py`, `sub09_*.py`, `fit_hc_*` | `refinement/` |
| `diagnostic_*`, `baseline_*`, `experiment_*`, `validate_*`, `hc_specificity_*`, `srm_integrated_loco`, `delta_rho_perm_test`, `summarize_cross_family`, `analyze_loco_profile_specificity`, `extract_loco_confusion_direction` | `diagnostics/` |
| `loco_filter_*`, `compare_2component_loco`, `evaluate_preimage_filter` | `filter_ops/` |
| `visualize_*`, `figs_*` | `visualization/` |
| `build_loss_inventory`, `build_decoder_loco_csv`, `build_cvd_individual_confusion` | `inventory/` |
| `cycle_loss_redesign/`, `cycle_bootstrap/`, `cycle_math_framework/` | `older_cycles/` |
| `*.sbatch`, `*.sh` (run_*, test_*) | `slurm/` |

22 scripts in subdirs had `sys.path.insert(0, _SCRIPT_DIR)` updated to `_SCRIPT_DIR.parent`.
