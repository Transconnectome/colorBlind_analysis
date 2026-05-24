# OHBM v9 Figure Data Sources

작업 중 자주 참조해야 하는 데이터 위치 inventory. 경로는 모두 프로젝트 root (`colorBlind_analysis/`) 기준 상대경로.

---

## 1. LORO / LOCO decoding (forward-encoding readout)

| Metric | Path | Format |
|---|---|---|
| LORO per-subject raw | `analysis/phase3_decoder_comparing/results/loro/procrustes/{sub}_performance_raw.json` | JSON, key `results.procrustes.{ROI}.{model}` → list of fold dicts with `acc_exact`, `mae` |
| LOCO per-subject | `analysis/phase3_decoder_comparing/results/loco/procrustes/{sub}_loco.json` | JSON, key `results.{ROI}.{model}` → `overall_mae`, `fold_results[].{test_hue, pred_hues[run]}` |

- ROI keys on disk: `V1, V2, V3, V4` (display label hV4 ↔ V4 on disk)
- Models: `ForwardEncoding` (FE-6, primary), `LDA` (deprecated in v8.1)
- Subjects: HC `sub-01..07`, CVD `sub-08, sub-09, sub-10`
- v8 figures' canonical loader: `docs/OHBM_abstract/v8_figures/_data.py`

### Group statistics (v8.1)
- LORO FE: all ROIs n.s. (V1 g=0.37 p=.342, V2 g=0.92 p=.108, V3 g=0.38 p=.300, hV4 g=0.43 p=.250)
- LOCO FE: **hV4 g=1.69 p=.017**, V2 trend g=0.94 p=.075, V1 p=.242, V3 p=.633
- HC label-perm null: only **hV4 p=.026**; V1/V2/V3 all p > .35

---

## 2. SRM-aligned hue patterns (for geometry visualization)

| File | Format |
|---|---|
| `analysis/phase2_SRM_across_between/results/c010/combined_with_aligned/{ROI}_procrustes_aligned_amplitudes.npy` | `np.load(..., allow_pickle=True).item()` → dict `{sub-XX: (8 colors, k features)}` |

- **All 10 subjects** projected into the HC shared space here (HC sub-01..07 + CVD sub-08..10)
- k on disk: V1=4, V2=4, V3=3, **V4=4** (NB: MEMORY.md says canonical hV4=3 after 2026-02-18 revision; this file pre-dates that revision — verify which K to use for v9 SRM viz)

### Crawford & Howell z (per-subject vs HC distribution)
- Long-form CSV: `analysis/phase2_SRM_across_between/results/c010/individual_disparities_long.csv`
- Columns: `subject_id, subject_num, group, roi, disparity, reference`
- v8 Fig 2D individual results: **sub-09 V1 z=5.17 p=.003, sub-08 V2 z=2.94 p=.033**; sub-10 null everywhere
- Canonical computation: `docs/OHBM_abstract/v8_figures/_data.py::srm_crawford_howell`

### Optional / alternative SRM sources (if needed)
- `analysis/future_phase1_forward_model/results/srm_projections/{ROI}/shared_response.npy` — HC mean shared response only (k, 8); CVD R matrices NOT stored here
- `analysis/phase2_SRM_across_between/results/c010/separated/` — per-condition SRMs (older snapshots)

---

## 3. Stimulus colors (for visualization)

8 isoluminant DKL hues at 45° spacing, L*=75 nominal (on screen via PsychoPy `colorBlind_test.py`):

| Label | Angle | Name | Approx vivid sRGB |
|---|---|---|---|
| color_1 | 0° | Red | `#E63333` |
| color_2 | 45° | Orange | `#F28C1A` |
| color_3 | 90° | Yellow | `#F2D926` |
| color_4 | 135° | Green | `#33BF40` |
| color_5 | 180° | Cyan | `#1ACCD9` |
| color_6 | 225° | Blue | `#3366F2` |
| color_7 | 270° | Purple | `#8C33D9` |
| color_8 | 315° | Magenta | `#E64DBF` |

- Caveat: figures should ideally extract sRGB **directly from the PsychoPy screenshots** in `~/Projects/colorBlind/Screenshots/` (per `guide_for_OHBM.md` §1). The above table is a vivid HSV approximation; replace with measured RGB if precision matters.

---

## 4. Canonical scripts to reuse

- `docs/OHBM_abstract/v8_figures/_data.py` — loaders + group stats (LORO, LOCO, SRM-CH)
- `docs/OHBM_abstract/v8_figures/make_fig{1,2}_v8_1.py` — current v8.1 figure builders (reference for layout/colors)
- HC-only permutation null for LOCO MAE: live computation inside `make_fig2_v8_1.py` (1000 iter, paired t one-tailed per ROI)

---

## 5. Subject metadata

| Subject | Group | Type | Sex | Age | Notes |
|---|---|---|---|---|---|
| sub-01..07 | HC | normal | mixed | 23.1±2.4 | sub-07 hV4 only 16 voxels |
| sub-08 | CVD | deuteranope | M | ~23 | strongest sub-level LOCO signal (V1 individual perm p=.035) |
| sub-09 | CVD | protanomalous | M | ~23 | strongest SRM signal (V1 z=5.17 p=.003); LOCO V1 104° (≈chance) |
| sub-10 | CVD | mild deutan | F | ~23 | specificity control; null at all ROIs by SRM and LOCO at group test |

CVD diagnosis: Ishihara only (Cambridge Colour Test NOT administered).

---

## 6. Outstanding diagnostics needed before v9 figures

- [ ] **SRM 8-color HC mean: do the 8 colors actually form a hue circle in 2D PCA?**
      If yes → octagon viz works.
      If no → switch to "hue-anchored radial" or RDM-based viz (see `srm_diag_v9.py` output once written).
- [ ] **k=3 vs k=4 for hV4**: confirm which to use in v9 (file has k=4, MEMORY canonical k=3).
- [ ] **LOCO per-color wedge fan**: extract sub-06 hV4 and sub-09 V1 fold-mean predictions for the cartoon example.
