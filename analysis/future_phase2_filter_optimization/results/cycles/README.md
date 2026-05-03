# cycles/ — Cycle 1~15 selection-rule reformulation outputs

**Status**: ACTIVE (core)
**Last cycle**: Cycle 15 (2026-05-03)

## Layout

- `sub-XX_ROI_landscape.json` (24 files: 8 subj × 3 ROIs) — per-(β_s, β_c) grid metrics: l_rank, l_dir, l_topk_jaccard, mw_jaccard_loss, l_mag, norm_resid, sign_agree, spearman_r, pearson_r. Generator: see `scripts/cycle_filter_refinement/cycle1_*.py` (initial landscape build)
- `cycle{1..13}_*.json/csv` — per-cycle aggregates
- `cycle12_loss_cross_roi.{json,csv}` — V4 l_topk + V1 l_rank cross-ROI loss
- `cycle14_v1_rdm_cross.{json,csv}` — V4 l_topk + V1 ΔRDM cosine
- `cycle15_mwjaccard_cross.{json,csv}` — **NEW WINNER**: 2·mw_jaccard(V4) + 1·l_rank(V1) → ✓✓ both CVD distinct
- `consolidated_phase2_results.{csv,json}` — Cycle 10d 48-row aggregate (subject × ROI × family)
- `consolidated_cross_roi.csv` — Cycle 11 9-pair × 2-family
- `bootstrap/`, `bootstrap_server/`, `cycle8_voxel_bootstrap*/` — bootstrap CIs
- `cycle6_voxel_diag/`, `cycle8_figures/` — sub-analyses

## Generator scripts
`scripts/cycle_filter_refinement/cycleN_*.py`
