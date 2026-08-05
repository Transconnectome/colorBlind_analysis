# comprehensive/_archive

**아카이브 일자**: 2026-08-05 · **근거**: `analysis/ARCHIVE_AUDIT_2026-08-05.md` §2.2

`baseline32_orchestration/` — 이 폴더의 **전량**입니다. Baseline32 시대 SLURM 오케스트레이션.

폐기 근거 3중:

1. `diagnose_memory.sh:22` → `TIMESTAMP="baseline32_${DATASET}"`
2. `docs/PAPER/Methods/methods_v2.tex` — Baseline32는 superseded이며 C010이 논문의 모든 결과를 생산
3. 출력이 `results/${TIMESTAMP}/` (프로젝트 CLAUDE.md의 timestamp 서브디렉토리 금지 위반) + 이제 없는 `phase1_preprocess_decoding/`를 대상으로 함

`run_phase3_filter_learning.py`(lstsq 선형 필터)는 `analysis/future_phase2_filter_optimization` 프레임워크 전체로 대체되었습니다. `docs/PAPER/repro/MAP.md`에 이 폴더 항목 0건.
