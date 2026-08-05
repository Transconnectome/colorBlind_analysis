# phase0_preprocessing/_archive

**아카이브 일자**: 2026-08-05 · **근거**: `analysis/ARCHIVE_AUDIT_2026-08-05.md` §2.1
복원: `git mv <path> ../scripts/`

| 범주 | 왜 폐기 | 무엇이 대체 |
|---|---|---|
| `registration_method_selection/` | Method 2(Header→BBR)와 3-subject pilot Method 3, Dice 기반 방법 비교. Method 3이 채택됨(`notion.md:2`). Dice 수치는 논문 어디에도 없음. ⚠ `REGISTRATION_COMPARISON_FINAL_REPORT.md`는 **Method 2를 승자로 결론**짓는 sub-06 단일 문서 — 논문과 배치되므로 인용 금지. | `scripts/run_method3_header_mi_all_subjects.sbatch` (exp1), `run_method3_header_mi_2nd.sbatch` (exp2) |
| `confound_regression_abandoned/` | aCompCor confound 생성·QC. 논문은 confound regression을 **적용하지 않음**(`supplementary_content.tex:10`). `generate_confounds_mcflirt.py`는 손상된 TSV의 원인으로 지목됨. | 없음 (설계상 미적용) |
| `corrupted_fd_outputs/` | ⚠ **인용 금지.** `framewise_displacement`가 288 volume 전부 0.0인 placeholder TSV에서 산출된 그림·표. | `scripts/motion_qc_summary.py` → `results/motion_qc_summary.json` |
| `oneoff/` | 메모리 프로파일링, sub-01/07 brain extraction 비교 등 1회성. | — |

유효한 motion 기록은 `*_desc-motion.par`뿐입니다. 상세: `PREPROCESSING_FINAL_REPORT.md`.
