# analysis/utils/_archive

**아카이브 일자**: 2026-08-05 · **근거**: `analysis/ARCHIVE_AUDIT_2026-08-05.md` §2.12

`baseline32_layout/` — `data_loader.py`, `output_paths.py`, `memory_profiler.py`.

셋 다 저장소 전체에서 **importer 0건**이며, 시그니처가 Baseline32 레이아웃입니다:

- `data_loader.load_baseline_amplitudes(subject_id, roi, timestamp, dataset='method3_header_mi')` — 현 C010 레이아웃은 `full_dataset_C010/{subject}/{ROI}/amplitudes_procrustes.npy`
- `output_paths` — 이제 없는 `phase1_preprocess_decoding` 폴더를 반환
- `memory_profiler` — 사용 예시가 `fir_reconstruction_BH2009_system_clean.py`(현재 부재)를 호출

`__pycache__/`에 컴파일된 모듈이 `utils_color_decoding` 하나뿐인 것이 실행 이력의 증거입니다.

> `utils_color_decoding.py`는 남겼습니다. 다만 그 **KEEP은 상속된 것**입니다 — importer 7개 중 다수가 이번에 아카이브된 폴더(phase1 `feature_selection`, phase3 `LOCO_trials`)에 있었습니다. 현재 남은 실질 근거는 `docs/PAPER/Figures/scripts/phase2/generate_fig7_filter.py`가 쓰는 `STIM_LAB`입니다.
