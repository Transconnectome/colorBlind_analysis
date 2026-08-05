# future_phase3_behavioral_analysis/_archive

**아카이브 일자**: 2026-08-05 · **근거**: `analysis/ARCHIVE_AUDIT_2026-08-05.md` §2.10
이 폴더는 이번이 **최초 정리**입니다.

| 범주 | 왜 폐기 |
|---|---|
| `run_count_design_v2/` | run-count 설계 검증 tier 1/2/3 + saturation/crossnobis/subsample. `run_count_validation/SUMMARY.md` §1.5에 따르면 산출물은 2차 MRI의 n=5/n=4 결정이었고 **그 세션은 이미 수집 완료** — 목적 소진 |
| `deprecated_permutation/` | `run_count_permutation.py` — grand-mean bias로 **invalid**. `SUMMARY.md` §1.5와 `S16_filter_eval_design.tex:28`이 동일하게 기술 |
| `superseded_planning_docs/` | v2 SUMMARY + v3 addendum으로 대체된 기획 문서 3건 |
| `orphans/` | `plot_exp2_mllm_report.py` — 저장소 전체 참조 0건 |

**남은 KEEP 중 주의**: `scripts/run_count_adjacc.py`는 v3 addendum 산출물로, `generate_figS16.py`가 읽어 `S16_filter_eval_design.tex:23`의 그림을 만듭니다. 같은 run-count 계열이지만 **논문에 실제로 들어갑니다.**

exp2_neural은 sub-08·sub-09 **양쪽 모두** 산출물이 있습니다(`MAP.md` E6는 2026-08-05에 정정). "sub-09 미수집"을 근거로 아무것도 archive하지 마십시오.
