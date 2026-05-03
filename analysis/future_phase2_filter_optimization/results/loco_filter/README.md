# loco_filter/ — Phase A LOCO fits + pre-images

**Status**: ACTIVE (core)
**Last fits**: 2026-04-09 (CVD canonical), 2026-05-03 (sub-08 fine grid)

## Subdirs

- `phase_a/` — Machado / R+C / fourier_warp fits (CVD only). Generator: `scripts/loco_distortion_fit.py`
- `phase_a_2component/` — 2-component fits (CVD only). β_s ∈ [0,50] step 2, β_c ∈ [-50,50] step 2 (1326 grid). Generator: same.
- `phase_a_2component_finegrid/` — sub-08 fine grid β_s∈[32,44]×β_c∈[-18,-10] @ 1° (B1 plan). Generator: `scripts/sub08_fine_grid_2component.py`
- `phase_a_2component_hc_sanity/` — HC subjects fitted (PARTIAL — server re-run needed; local job killed per user request)
- `phase_a_v2/`, `phase_b_v2/`, `phase_a_test/` — older intermediate; keep for ref
- `preimage/` — opponent-convention pre-images (Machado, R+C, fourier)
- `preimage_2component/` — opponent-convention pre-images (2-comp). NOTE: visualize_filter_candidates.py uses CIELab convention (different angles)
- `roi_hierarchy/` — cross-ROI agreement analysis

## Key files
- `phase_a_2component/sub-08_V4_2component.json` — sub-08 canonical fit (38, -14, ρ=0.881)
- `phase_a_2component/sub-09_V4_2component.json` — sub-09 canonical fit (6, -22, ρ=0.690)
- `preimage_2component/sub-08_V4_2component_preimage.json` — sub-08 pre-image (opponent)
