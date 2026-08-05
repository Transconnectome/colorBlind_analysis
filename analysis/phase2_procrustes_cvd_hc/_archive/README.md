# phase2_procrustes_cvd_hc/_archive

**아카이브 일자**: 2026-08-05 · **근거**: `analysis/ARCHIVE_AUDIT_2026-08-05.md` §2.4 + 사용자 요청(C010 현 파이프라인 기준 재확인)

**스크립트 전량이 이동했습니다.** 폴더에는 README/CLAUDE.md/notion.md만 남습니다.

판정 근거:

- 14개 중 **13개가 `derivatives/V3_Comprehensive/BH2009_deoblique_v2/baseline81_deob_determin`를 읽습니다.** 이 경로는 **현재 존재하지 않습니다** (`derivatives/`에 `V3_Comprehensive` 없음). 즉 pre-C010 전용이며 현 파이프라인에서 재실행 불가.
- 예외인 `plot_inflated_posterior.py`(C010 기반)는 출력이 `docs/PAPER/Figures/` 어디에도 등재되지 않음.
- 이 폴더에는 `results/` 디렉토리가 **아예 없습니다** — README의 헤드라인 수치를 커밋된 산출물로 추적할 수 없음.
- `docs/PAPER/repro/MAP.md`에 E-id 매핑 0건. live tex에 이 폴더의 수치(magnitude 0.66/1.21/0.89, structure 0.505/0.118/0.310, common-decoder 32°/36–42°/84–96°) 0건.
- 저장소 전체에서 이 폴더를 import하는 코드 0건.

> `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md:15,37`이 아직 이 폴더를 RQ2/SRQ1 포인터로 가리킵니다. 원고에 넣을 계획이면 **C010로 재실행이 선행되어야 합니다** — 기존 수치는 pre-C010 데이터 산출물입니다.
