# Archive Audit — analysis/ 디렉토리 정리

**최초 감사**: 2026-08-05 · **정리 실행**: 2026-08-05 · **상태**: **종결** (R1–R4 전부 해소)

> 실행 내역은 각 폴더의 `_archive/README.md`에 범주별로 기록되어 있습니다.
> 남은 것은 §3 판단보류 파일 목록과 §4 별건(데이터 비대·죽은 tex 브랜치 등)뿐입니다.

---

## 1. 실행 요약

| 디렉토리 | 조치 | 남은 스크립트 |
|---|---|---|
| `phase0_preprocessing/scripts` | 11개 아카이브 (4범주) | **9** (method3 정본 2 + deploy + registration QC 3 + motion QC 3) |
| `comprehensive/` | **전량 아카이브** | 0 |
| `phase1_procrustes_decoding/` | ~38개 아카이브 (9범주) | **9** |
| `phase2_procrustes_cvd_hc/` | **스크립트 전량 아카이브** | 0 (README/CLAUDE.md/notion.md만) |
| `phase2_SRM_across_between/` | ~42개 아카이브 (5범주) | canonical + 2C + A3/A4/A5 + utils |
| `analysis/validation/` | ~50개 아카이브 (6범주) | **3** (2026-07-23자 진행 중 작업) + utils |
| `phase4_forward_model/` | ~40개 아카이브 (11범주) | **19 py + 5 sbatch** |
| `phase3_decoder_comparing/` | ~24개 아카이브 (7범주) | 22 (S-A 종속 4건 포함) |
| `phase5_filter_optimization/` | 4소그룹 아카이브 | 기존 정리 상태 유지 |
| `phase6_behavioral_analysis/` | ~10개 아카이브 (4범주) — **최초 정리** | 12 |
| `analysis/utils/` | 3개 아카이브 | 1 |
| `docs/PAPER/Figures/scripts/` | `generate_fig1.py`, `generate_fig4.py` 아카이브 | 7 |
| `future_phase3_geometry_synthesis/`, `phase_supplementary/` | 조치 없음 | 전량 유지 |

### 문서 정정 (완료)

- `future_phase2/scripts/_ACTIVE.md` §Inactive — `behav_loss.py` / `utils_distortion_models.py` / `diagnostic_delta_rdm.py` 3건 제거 + 정정 경고 추가. (실측: live importer 14 / 2 / 5건. 나머지 9건은 importer 0으로 이미 아카이브 상태임을 확인.)
- `MAP.md` E1.1 — 생산 코드를 `loro_baseline.py` → `results/loro/srm/sub-*_performance_raw.json`으로 정정 + 노트북 오참조 경고.
- `MAP.md` E3.3 — `visualize_scattered_but_parallel.py` 포인터 제거 + Fig 4 재현 불가 사유 기록.
- `MAP.md` E6 — sub-09 "미수집" 표기 전량 정정.
- `methods_v2.tex` — Baseline32 voxel-selection 주석 블록 삭제, 전처리 서술을 canonical sbatch(bet2 / mri_coreg / FLIRT-FNIRT / MNI152NLin2009cAsym)에 맞춰 보강, `smith2002` 참고문헌 추가.
- `phase0/README.md`·`EXECUTION_GUIDE.md` — 아카이브된 pilot sbatch 참조를 정본으로 교체.
- 신규: `phase0_preprocessing/PREPROCESSING_FINAL_REPORT.md`, `docs/PAPER/Supplementary/TODO_supplementary_additions.md`.

### 코드 복구 (완료)

`phase3_decoder_comparing/model_comparison_validation/scripts/run_cvd_cross_decoding.py` — 커밋 `3ec8e51`에서 삭제되었던 것을 복원 (RT-7 HC-only 버전).

---

## 2. R1–R4 — 전부 종결 (2026-08-05)

| # | 항목 | 결정 및 조치 |
|---|---|---|
| **R1** | 노트북 E1.1 셀이 폐기된 JSON 참조 | **해소.** `build_notebooks.py`의 E1.1 셀을 Figure 3A와 동일한 LORO 소스(`results/loro/srm/sub-{08,09}_performance_raw.json` → `results.srm.{ROI}.ForwardEncoding[].acc_exact`)로 교체. 8/8 셀 전부 chance 0.125 통과 검증 완료 (sub-08 0.604/0.458/0.375/0.354, sub-09 0.625/0.438/0.312/0.354) |
| **R2** | Fig 재현 불가 | **종결.** `generate_fig3.py`는 저자가 커밋 `6f66e67`("replace Fig 3 with data-derived workflow schematic")에서 이미 삭제한 상태였고, 디스크에 남아 있던 것은 untracked 잔여물이었습니다 — 이를 정리했습니다. ⚠ **정정**: 제가 앞서 "Fig 4는 대체되지 않았다"고 말한 것은 `6f66e67` 이전 상태를 보고 판단한 것으로 틀렸습니다. 다만 Methods 그림(`fig3_workflow`)과 Results 기하 패널(`fig3_geometry`)은 **서로 다른 그림**이며, 후자는 `results_v4.tex:75`에서 여전히 인용되고 생산 코드가 없습니다. 복구: `git show 6f66e67^:docs/PAPER/Figures/scripts/generate_fig3.py`. 상세는 `MAP.md` E3.3 |
| **R3** | `METHODS_phase1_baseline.md`의 두 테이블 | **제거 완료.** Noise Ceiling / Pipeline Comparison(Whitening) 삭제, 아카이브 경로 포인터로 대체. 부수 발견으로 같은 문서의 stale Settings 2건도 정정 — "fMRIPrep 23.2.3"(미사용) → 실제 custom 파이프라인, "Voxel selection: Top 50% by FIR R²"(Baseline32 잔재) → none |
| **R4** | Method 3 채택 근거 | **종결 — 조치 불요.** ROI 중첩 영상 자체가 두 방법 간 비교 대상이 되지 않는다는 저자 판단 |

## 3. 참고 — 판단보류로 남긴 파일

archive하지 않고 원위치에 둔 항목입니다. 근거가 약해 자동 처분하지 않았습니다.

| 파일 | 위치 | 보류 사유 |
|---|---|---|
| `project_filtered_session.py` | `phase2_SRM_across_between/` | MAP.md E6.2d가 exp2 SRM을 `exp2_convergent.py`로 배정 → 대체된 것으로 보이나 **명시적 폐기 기록 없음** |
| `step_{a..d}_*.py` (4) | `phase4_forward_model/scripts/` | 프로젝트 CLAUDE.md는 canonical로 지정, 폴더 CLAUDE.md는 "group prior 계열 기각". E1.1의 `prior_only`/`prior_finetune` arm 상류 |
| `n1_stouffer_omnibus.py` 외 robustness 3종 | 〃 | `TODO_robustness_supplement.md`가 main.tex 체인에 없음. supplement 발행 여부에 종속 |
| `group_prior.py`, `plot_lambda_curve.py` | `phase3_decoder_comparing/.../scripts/` | S-A(decoder Supplementary)에 group prior λ blending을 **포함할지 미정**. 제외하면 archive 대상 |
| `filter_input_stability.py` | `phase6_behavioral_analysis/scripts/` | 출력 JSON은 있으나 REPORT/SUMMARY/tex 참조 0건 |
| `analyze_c010_procrustes_effects.py` | `phase1_procrustes_decoding/` | `_residuals` 판본과 near-duplicate이나 **서로 다른 live C010 변종**을 대상으로 함 (canonical SRM은 non-residual, LOCO/exp2는 residual) |

### 이번 정리로 live importer가 0이 된 공유 유틸

공유 유틸 보존 원칙에 따라 남겼으나 실질적으로 dead code입니다. 다음 정리 사이클에서 재평가하십시오.

- `phase2_SRM_across_between/brain_mapping_utils.py` — importer였던 `create_cvd_distortion_figure.py`가 아카이브됨
- `phase2_SRM_across_between/utils/srm_alignment.py` — canonical `rerun_loo_consistent.py`는 로컬 모듈을 import하지 않음
- `analysis/utils/utils_color_decoding.py` — 남은 실질 근거는 `generate_fig7_filter.py`가 쓰는 `STIM_LAB`뿐

---

## 4. 정리와 무관한 별건

**데이터 비대** — 코드 아카이브와 분리해서 처리해야 합니다. 954 MB 중 git에 들어간 것은 markdown 26개뿐이므로 **로컬 디스크 문제이지 저장소 문제가 아닙니다.**

| 경로 | 크기 | 성격 |
|---|---|---|
| `phase0_preprocessing/logs/` | 640M | 같은 뇌 데이터가 `.nii` + `.tar` + `.tar.gz` + `.gz`로 3중 저장 |
| `phase1_.../past_grid_factorial_archive_2026-02-19.tar.gz` | 642M | 미보고 실험 산출물 단일 파일 → 저장소 밖으로 |
| `future_phase2/results/s10_inclusion/` 중 v3/v4/v5 | ~203M | 생산 스크립트가 이미 아카이브됨 → 회수 가능 |
| `future_phase2/results/_archive/` | 201M | 순수 히스토리, cold storage 후보 |

**기타**

- **죽은 tex 브랜치가 오판의 근원입니다.** `methods.tex`, `methods_concise.tex`, `results.tex`, `*_prewrap_backup.tex`, `main_2col.tex`가 ICC / crossnobis / bootstrap-CI 문장을 여전히 갖고 있어, naive `grep --include=*.tex`로 재감사하면 "인용됨"으로 오판합니다. `docs/PAPER/archive/`로 분리 권장.
- `phase3_decoder_comparing/results/` 하위 timestamp 서브디렉토리 ~50개 — CLAUDE.md 규칙 위반.
- `analysis/validation/preprocess_Check/`가 참조되지만 부재 (`git show 47bac51:<path>`로 복원 가능).
- `future_phase2/results/redteam/exp*.py` 22개가 gitignore(`.gitignore:119`)인데 그 산출물 `*_synthesis.md`는 tracked이고 폴더 CLAUDE.md §2.6이 인용 — **인용된 증거에 버전관리가 없음**. `scripts/redteam/`으로 이동 권장.
- `analysis/FILE_CLEANUP_RECOMMENDATIONS.md`(2026-02-19)는 이 문서로 대체됨.
