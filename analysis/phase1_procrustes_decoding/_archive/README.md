# phase1_procrustes_decoding/_archive

**아카이브 일자**: 2026-08-05 · **근거**: `analysis/ARCHIVE_AUDIT_2026-08-05.md` §2.3
정리 원칙: **"C010만 남긴다"**. 남은 것은 C010 amplitude 생산자와 그 driver·QC뿐입니다.

| 범주 | 왜 폐기 |
|---|---|
| `pre_C010_baseline_pipeline/` | **존재하지 않는 스크립트/디렉토리를 호출하는 dead entrypoint.** `fir_reconstruction_BH2009_system_clean.py`, `roi_pipeline_comprehensive.py`, `results/baseline/` 모두 부재 |
| `whitening_tests/` | 4-way whitening 비교. live tex에 `whiten` hit 0건. ⚠ 이 결과 테이블이 `analysis/METHODS_phase1_baseline.md` "Pipeline Comparison (Whitening Assessment)"에 남아 있음 — 논문 미보고 |
| `grid_factorial/` | 36/144-condition 전처리 factorial. `utils_grid/`의 `procrustes_normalized.py`·`crossnobis_ldw.py`는 **canonical `run_full_dataset_C010.py`의 의존성이 아님** (그 스크립트는 로컬 모듈을 하나도 import하지 않고 Procrustes를 L284-296에 inline). 유일한 importer 3개가 전부 이 아카이브 안에 함께 있음. ⚠ `validation/noise_ceiling.py`는 symlink였으므로 복원 시 상대경로 재지정 필요 |
| `feature_selection_trials/` | `baseline81_deob` / `config81` pre-C010 데이터셋 + 구 피험자 번호. `methods_v2.tex`에서 voxel-selection 문장이 Baseline32 잔재로 제거됨 |
| `hrf_variant/` | HRF 변동성 분기. 출력이 V2 단독(`results/HRF_visualization/V2/`)인 미완 실행. 참조 0건 |
| `noise_ceiling_phase1/` | ⚠ 결과가 `METHODS_phase1_baseline.md` "Noise Ceiling Analysis" 표에 있으나 **live tex 0건**. 논문의 noise ceiling(`results_v4.tex:122`)은 Phase-2의 다른 양 |
| `onset_randomization_dropped/` | `METHODS_phase1_baseline.md`: *"Onset randomization: **dropped**"* |
| `one_off_procrustes_scripts/` | 입력 디렉토리 부재 (`results/pairwise_procrustes/`, `results/baseline_anova_selected`) |
| `qc_visualizations_unpublished/` | `docs/PAPER/Figures/FIGURES_README.md`·`FIGURE_CAPTIONS.md`에 대응 그림 없음 |

**남은 KEEP**: `run_full_dataset_C010.py` + driver 3, `roi_pipeline_selected_1202used.py`(ROI mask 생산 → C010이 읽음), `visualize_roi_overlay.py`, `analyze_c010_{,residuals_}procrustes_effects.py`(C010 두 변종 모두 downstream에서 사용 중), `validation/validate_drift_removal.py`.
