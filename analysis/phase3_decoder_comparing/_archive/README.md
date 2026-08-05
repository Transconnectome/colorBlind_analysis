# phase3_decoder_comparing/_archive

**아카이브 일자**: 2026-08-05 · **근거**: `analysis/ARCHIVE_AUDIT_2026-08-05.md` §2.8

| 범주 | 왜 폐기 |
|---|---|
| `loco_trials_early/` | pre-canonical LOCO decoder 탐색 전량(GP, ridge, MDS, cone contrast 등). 폴더 CLAUDE.md 규칙 1–2: *"새 디코더 제안 금지 — 기존 탐색에서 이미 결론 도출됨"* |
| `rejected_ensembles/` | `FE_Ensemble` 계열 파서·플롯. 앙상블은 기각됨 |
| `superseded_mae_metric/` | `results_v4.tex:8`이 *"LOCO metric updated: adjacent accuracy … replacing circular correlation rho"*를 기록. MAE 기반 분석·시각화는 대체됨 |
| `cvd_distortion_viz/` | 논문 figure 목록에 없음 |
| `wrong_dataset_baseline32/` | `baseline32_deob_determin` 사용. canonical 토큰은 **C010** |
| `superseded_phase1_reruns/` | RSA는 `rerun_loo_consistent.py` 소관, cross-subject LOSO는 `validation_tests.py`(E1.2 생산자)로 대체 |
| `orphan_sbatch_fac83c0/` | 대상 `loco_fek_retry.py`가 `fac83c0`에서 삭제됨 |

**의도적으로 남긴 것**:

- `visualize_model_comparison.py`, `group_prior.py`, `plot_lambda_curve.py`, `run_hybrid.sbatch` — `methods_v2.tex:132`가 약속하는 decoder 비교를 Supplementary로 작성하기로 결정(`docs/PAPER/Supplementary/TODO_supplementary_additions.md` S-A). 그 작업이 취소되면 archive 대상으로 복귀합니다.
- `run_cvd_cross_decoding.py` — 2026-08-05에 `3ec8e51^`에서 **복원**했습니다(RT-7 HC-only 버전). 상세: `docs/PAPER/repro/MAP.md` E1.1 correction note.
