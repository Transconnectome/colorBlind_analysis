# phase4_forward_model/_archive

**아카이브 일자**: 2026-08-05 · **근거**: `analysis/ARCHIVE_AUDIT_2026-08-05.md` §2.7

선례: 커밋 `fac83c0`("cleanup: remove obsolete forward-model basis-search…")가 13개 스크립트를 이미 삭제했으나 sbatch wrapper는 남겨뒀습니다 — `orphan_sbatch_fac83c0/`가 그 잔해입니다.

| 범주 | 왜 폐기 |
|---|---|
| `rejected_smooth_tikh/` | live tex에서 `smooth`/`smooth_tikh` hit **0건**. "Tikhonov" 2건은 Phase-2 필터 loss 주석. `methods_v2.tex:135`가 *"This ridge prior is isotropic and imposes no spatial structure"* 한 줄로 흡수 — **negative result로 보고되지 않음** |
| `rejected_group_prior/` | SRM group prior 계열. 폴더 CLAUDE.md "이미 기각". `results_v4.tex`는 ridge-GCV / OLS만 보고 |
| `basis_variants/` | per-ROI 최적 basis, opponent basis. 논문은 **FE-6 uniform 고정**(`methods_v2.tex:129`) |
| `rejected_cone_shift_etiology/` | `appendix_alternative_models.tex:5`가 2-DOF (Δλ, g) 분해를 *"have been removed"*로 명시 |
| `dimensionality_exploration/` | eigenspectrum decay, MEME estimator. tex hit 0건 |
| `population_maps/` | voxel color preference KDE. 출력이 논문에 없음 |
| `exploratory_expA/` | Exp A3–A6 (circular bias, confusion structure, pairwise residual, cross-phase correlation). 마지막 것은 phase4 결론이 "STOP digging" |
| `ppt_notion_figures/` | docstring이 "PPT/Notion용 시각화"라고 명시 |
| `one_off_debug/` | `_test_*`, `_inspect_*`, intercept rescue, Phase-1 voxel noise ceiling(논문의 NC는 Phase-2 산출) |
| `orphan_sbatch_fac83c0/` | 대상 스크립트가 `fac83c0`에서 삭제되어 실행 불가 |
| `excluded_subject/` | sub-10은 분석 제외 대상(프로젝트 CLAUDE.md) |

> ⚠ `stockman_cone_shift.py`는 cone-shift 계열이지만 **아카이브하지 않았습니다.** 두 홉 건너 인용 결과로 연결됩니다:
>
> `stockman_cone_shift.py → machado_simulator.py:51 → utils_distortion_models.py:40 → rc_1dof.py → s10b_v6_pca_rdm.py` (MAP.md E4.1/4.2, Appendix A).
>
> 마찬가지로 `_compute_paper_stats.py`는 `_` prefix지만 debug가 아니라 **MAP.md E1.3 생산자**입니다.
