# Phase 1: Preprocessing & Baseline Decoding (C010 + Procrustes)

## Table of Contents
- [Settings](#settings)
- [Overall Performance (N=40 subject-ROI pairs, 10 subjects × 4 ROIs)](#overall-performance-n40-subject-roi-pairs-10-subjects--4-rois)
- [Results by ROI](#results-by-roi)
- [Results by Group](#results-by-group)
- [Removed 2026-08-05 — Noise Ceiling Analysis, Pipeline Comparison (Whitening)](#removed-2026-08-05--noise-ceiling-analysis-pipeline-comparison-whitening)
- [Validation Status (Phase 1)](#validation-status-phase-1)

---

### Settings

- **Preprocessing**: custom pipeline — FSL `bet2` → FreeSurfer `mri_coreg` (MI, header-initialized) → FSL FLIRT 12-DOF + FNIRT → MNI152NLin2009cAsym res-2. Driver: `phase0_preprocessing/scripts/run_method3_header_mi_all_subjects.sbatch`. **fMRIPrep is NOT used** — that name survives only as an output *directory* name (corrected 2026-08-05)
- **Pipeline**: C010 (2nd-level drift removal) + Procrustes alignment
- **1st-level GLM**: FIR basis (8 delays, 0–12s post-stimulus at TR=1.5s)
- **Voxel selection**: none. (Top-50%-by-FIR-R² belonged to the superseded Baseline32 pipeline; stored C010 amplitudes carry the full mask. Corrected 2026-08-05, matching `methods_v2.tex`.)
- **2nd-level GLM**: 8 HRF + 8 HRF derivative + 12 per-run drift (linear + constant)
- **Confounds**: None (motion/tissue/WM regression degrades signal by −60%)
- **High-pass filtering**: None (drift regressors handle slow trends)
- **Procrustes alignment**: Orthogonal (rotation + reflection), runs 1–5 aligned to run 0 reference
- **Procrustes disparity**: Sum of squared differences after optimal orthogonal transformation; range [0, ∞), lower = better alignment
- **Forward encoding model**: 6 half-wave rectified basis functions at [0°, 60°, 120°, 180°, 240°, 300°] hue
- **Cross-validation**: LORO (Leave-One-Run-Out)
- **ROIs**: V1, V2, V3, hV4 (Wang Atlas, 2015)
- **Space**: MNI152NLin2009cAsym, res-2
- **Subjects**: 10 total (HC: sub-01~07, n=7; CVD: sub-08~10, n=3)
- **CVD diagnosis**: Ishihara test
- **CVD subtypes**: sub-08 deutan, sub-09 protan, sub-10 deutan
- **Status**: VALIDATED (2026-02-09)

### Overall Performance (N=40 subject-ROI pairs, 10 subjects × 4 ROIs)

| Metric | Raw (pre-Procrustes) | Procrustes-aligned | Improvement |
|--------|---------------------|-------------------|-------------|
| RDM correlation | 0.004 ± 0.197 | **0.381 ± 0.278** | +0.377 |
| Decoding accuracy | 0.131 ± 0.049 | **0.592 ± 0.121** | +0.461 |
| Procrustes disparity | — | 0.00373 ± 0.004 | — |
| Positive pairs | 52.5% | **100%** | — |

### Results by ROI

| ROI | N | RDM Correlation (M ± SD) | Decoding Accuracy (M ± SD) |
|-----|---|--------------------------|---------------------------|
| V1 | 10 | 0.313 ± 0.215 | 0.560 ± 0.138 |
| V2 | 10 | 0.370 ± 0.256 | 0.581 ± 0.131 |
| V3 | 10 | 0.316 ± 0.328 | 0.613 ± 0.130 |
| hV4 | 10 | **0.541 ± 0.283** | **0.613 ± 0.092** |

> hV4 shows strongest color selectivity: highest RDM correlation and most consistent decoding accuracy.

### Results by Group

| Group | N (pairs) | RDM Correlation (M ± SD) | Decoding Accuracy (M ± SD) |
|-------|-----------|--------------------------|---------------------------|
| HC (sub-01~07) | 28 | 0.345 ± 0.278 | 0.552 ± 0.111 |
| CVD (sub-08~10) | 12 | **0.462 ± 0.273** | **0.684 ± 0.094** |
| Difference | — | +0.117 | +0.132 (13.2 pp) |

> Note: CVD subjects show numerically higher decoding performance. This may reflect higher signal quality or genuine representational differences; it does not imply superior color processing.

### Removed 2026-08-05 — Noise Ceiling Analysis, Pipeline Comparison (Whitening)

두 테이블을 이 문서에서 제거했습니다. 어느 쪽도 **논문 live tex에 대응 수치가 없고**, 생산 코드는 2026-08-05 정리에서 아카이브되었습니다.

| 제거된 테이블 | 생산 코드 (현 위치) |
|---|---|
| Noise Ceiling Analysis (N=40) | `phase1_procrustes_decoding/_archive/noise_ceiling_phase1/compute_noise_ceiling_analysis.py` |
| Pipeline Comparison (Whitening, N=40) | `phase1_procrustes_decoding/_archive/whitening_tests/` |

수치가 필요하면 `git show 4b92d8e:analysis/METHODS_phase1_baseline.md`에서 확인할 수 있습니다.

> 혼동 방지: 논문이 보고하는 noise ceiling (`results_v4.tex:122`, 52%/67%, `lagecastellanos2018`)은 **다른 양**입니다 — Phase-2의 HC split-half filter-fit ceiling이며 `phase5_filter_optimization/scripts/s18_heldout_predictive.py`가 생산합니다. 위 표의 Phase-1 RDM 기반 ceiling과 섞어 쓰지 마십시오.

Whitening이 해로웠다는 결론 자체는 아래 Validation Status에 유지합니다.

### Validation Status (Phase 1)

- [x] Procrustes alignment: 100% positive pairs, +1644% improvement (0.028 → 0.487)
- [x] Whitening assessment: harmful, excluded
- [x] Noise ceiling: ~30% utilization (per-subject split-half); pipeline-level RDM reliability 0.487 vs ceiling 0.613 (79%) uses a different metric. Per-ROI breakdown removed 2026-08-05 (see above)
- [x] Temporal stability: method difference = 0.101 (excellent)
- [x] Drift validation: 1st+2nd and 2nd-only produced identical HRF — passed
- [x] Onset randomization: dropped (FIR with fixed ISI; timing jitter not applicable)
