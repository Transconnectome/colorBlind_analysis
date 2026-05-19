# scripts/ — Phase 2 Filter Optimization

**Last updated**: 2026-05-19 (post-reorganization: 11 canonical at root + 6 subdirs)

## Canonical pipeline (scripts/ root, 11 files)

These produce the Phase 2 BEST filter. To replicate, run `loco_distortion_fit.py`.

- `loco_distortion_fit.py` — main entry: `grid_search`, `FILTER_MODELS`, default L_fit
- `machado_simulator.py` — Stockman cone fundamentals + `machado_shifted_hue` (computes h_base)
- `utils_distortion_models.py` — model interface (`get_design_matrix`)
- `step1_fit_loco_v2.py` — helpers (`precompute_hc_W`, `load_cvd_loco_target`)
- `diagnostic_delta_rdm.py` — `compute_delta_rdm_obs/_sim` for L_rdm
- `c3_relabel_p2a.py` — NEW 9-bin labels for canonical P2a
- `c3_relabel_both_subjects.py` — per-subject NEW target maps
- `render_loco_canonical_4col.py` — BEST 4-col viz generator
- `stim_lab_render.py` — color rendering helper
- `landscape_loader.py` — parquet-backed landscape access
- `retinal_cortical.py` — R+C functions (paper Tier 2 diagnostic)

**Subdirs**:
- `forward_models/` — `two_component.py` (canonical), `three_component`, `opponent_gain`, `rc_2stage`
- `filter_ops/` — alternative filter forms compared in paper (`voxel_level_fit.py`, `render_rc_2stage_4col.py`, `multi_roi_confusion_diagnostic.py`, etc.)
- `diagnostics/` — descriptive diagnostics (HC LOO bootstrap, baseline_ρ, etc.)
- `inventory/` — inventory builders
- `visualization/` — figure generation
- `slurm/` — SLURM submission scripts
- `_archive/` — deprecated/exploratory scripts

## Canonical filter equation (single source of truth)

```
Filter form (2-component cortical opponent rotation):
    h(θ_CIELab)  = Stockman opponent hue projection (computed from CIE Stockman cone fundamentals)
    δθ(θ)        = β_s · cos(h − 90°)  +  β_c · cos(h − θ_conf)
    θ_corrected  = (θ_stimulus − δθ) mod 360°       # pre-image / corrective stimulus

Confusion axes (Stockman opponent space):
    θ_conf = 150° (deutan), 16° (protan)
```

The S-cone axis is at h=90° in Stockman opponent space (fixed). The L/M confusion axis varies per CVD family.

## Canonical h_base reference (frozen 2026-05-19)

The 8-anchor h_base vector produced by the canonical pipeline at fit time:

```python
# Stockman opponent hue projections for the 8 DKL anchors
# CIELab anchor θ° → h_base° (degrees in Stockman opponent space)
# Env: conda srm; colour-science 0.4.4; numpy 1.26.4; scipy 1.13.1
H_BASE_REFERENCE = {
    # CIELab (DKL) hue → Stockman opponent h_base
    'c1_red_0':     313.47,
    'c2_orange_45': 299.86,
    'c3_yellow_90': 288.33,
    'c4_green_135': 278.15,
    'c5_cyan_180':  267.62,
    'c6_blue_225':  227.40,
    'c7_purple_270':  86.66,
    'c8_magenta_315': 348.48,
}
# Identical for deutan and protan (Δλ=0 baseline projection).
# Family difference enters only through θ_conf (CONF_AXIS_STOCKMAN).
```

**Why a frozen reference**:
- `machado_shifted_hue(0.0, family)` output depends on the installed `colour-science` version and Stockman fundamentals path. Different envs (e.g. with vs without `colour-science`) produce different h_base values.
- The Phase 2 BEST coordinates (β_s, β_c) reported in `results/BEST_summary.json` are conditional on this exact h_base. To reproduce the canonical fit, this h_base must be reproduced.
- Internal consistency between fit, viz, pre-image, and R+C diagnostic is preserved because all use the same `machado_shifted_hue` call in the same env.
- For external reproducibility (paper Methods), use this lookup as ground truth.

## Canonical fitting method

```
Method: shift_at_both (canonical, post-2026-04-09)
Grid: β_s ∈ [0, 50], β_c ∈ [-50, 50], step = 2° (1326 points)
Encoder: ridge_gcv with GCV-selected α per HC subject
HC pool: sub-01..07 (n=7); sub-07 V4 = 16 voxels (smaller than others ~67-70)
ROI: V4 (hV4 on disk)
Loss weights: (α, β, δ, ε) = (1.0, 0.5, 0.2, 0.1)
Loss form: L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth
Permutation test: 50000 random label shuffles per subject
```

## Loss term definitions (all normalized to [0, 1])

| Term | Raw | Normalizer |
|---|---|---:|
| L_vuln | `(1/8) · Σ (v_sim − v_cvd)²` | 4.0 |
| L_rank | `1 − ρ_Spearman(v_sim, v_cvd)` | 2.0 |
| L_rdm  | `1 − cos(Δrdm_sim, Δrdm_obs)` | 2.0 |
| L_smooth | `(1/8) · Σ [(δθ[c+1] − δθ[c]) mod ±180]²` | 32400 |

## Replication checklist

1. `conda activate srm` (or any env with `colour-science 0.4.4`)
2. Verify `machado_shifted_hue(0.0, 'deutan')` returns `H_BASE_REFERENCE` values within rounding tolerance
3. Run `python scripts/loco_distortion_fit.py --subject 08 --roi V4 --method shift_at_both --models 2component`
4. Compare to `results/BEST_summary.json` per-subject params

If h_base values differ in your env, the resulting (β_s, β_c) will not match the paper's reported values. Pin h_base via the lookup above or install matching env.
