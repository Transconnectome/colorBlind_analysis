# Archive Audit — analysis/ 디렉토리 정리

**최초 감사**: 2026-08-05 · **정리 실행**: 2026-08-05 · **상태**: 실행 완료, 잔여 판단 4건

> 완료된 항목은 이 문서에서 제거했습니다. 실행 내역은 각 폴더의 `_archive/README.md`에 범주별로 기록되어 있습니다.
> 이 문서는 이제 **미해결 항목만** 다룹니다.

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
| `future_phase1_forward_model/` | ~40개 아카이브 (11범주) | **19 py + 5 sbatch** |
| `phase3_decoder_comparing/` | ~24개 아카이브 (7범주) | 22 (S-A 종속 4건 포함) |
| `future_phase2_filter_optimization/` | 4소그룹 아카이브 | 기존 정리 상태 유지 |
| `future_phase3_behavioral_analysis/` | ~10개 아카이브 (4범주) — **최초 정리** | 12 |
| `analysis/utils/` | 3개 아카이브 | 1 |
| `docs/PAPER/Figures/scripts/` | `generate_fig1.py`, `generate_fig4.py` 아카이브 | 7 |
| `future_phase4_geometry_synthesis/`, `phase_supplementary/` | 조치 없음 | 전량 유지 |

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

## 2. 미해결 — 판단 필요

### R1. `01_discrimination.ipynb`의 E1.1 검증 셀이 폐기된 JSON을 봅니다

노트북이 `cvd_cross_decoding_procrustes.json`(2026-02-18 **12:50**, all-subject SRM)을 읽습니다. 이는 5시간 뒤 순환성 제거를 위해 나온 RT-7 수정본(`cvd_cross_decoding_hconly.json`, **17:38**)이 대체한 파일입니다.

**논문 주장 자체는 안전합니다.** `results_v4.tex:31`은 Figure 3A를 인용하고, 그 그림은 live 생산자가 있는 LORO 결과로 만들어집니다:

| | V1 | V2 | V3 | V4 |
|---|---|---|---|---|
| sub-08 | 0.604 | 0.458 | 0.375 | 0.354 |
| sub-09 | 0.625 | 0.438 | 0.312 | 0.354 |

전부 chance 0.125를 크게 상회합니다.

> ⚠ **다만 셀을 옮길 때 주의**: RT-7(비순환) cross-decoding 수치는 hV4에서 **더 약합니다** — sub-08 0.75 → **0.375** (permutation **p = 0.057**), sub-09 0.75 → 0.625. 폐기본 수치를 제시해서는 안 됩니다.

**필요한 결정**: 셀을 (a) Figure 3A와 동일한 LORO 소스로 옮길지, (b) RT-7 `hconly` JSON으로 옮길지. (a)가 tex·그림·MAP.md와 모두 일치합니다.

### R2. Fig 4 (`fig3_geometry`)는 재현 불가입니다

`generate_fig3.py`는 4개 ROI(`V1, V2, V3, hV4`)의 ΔRDM을 요구하는데, 트리에 남은 유일한 `srm_precompute`는

- **V1·V2만** 포함 (`manifest.json` → `rois: [V1, V2]`), 그리고
- **2026-04-12**자로 **2026-05-16 label-scheme cutoff 이전**이며 `old_labels_pre_2026-05-16/`(13-bin 구 스킴) 아래에 있음

따라서 아카이브본을 되살리는 것은 **오답**입니다. 게재된 `fig3_geometry.pdf`는 현재 트리에 재현 가능한 소스가 없습니다.

**필요한 결정**: 현 label scheme으로 4-ROI ΔRDM precompute를 재생성할지, 아니면 Fig 4를 재현 불가 상태로 두고 supplementary에 명시할지.

### R3. `METHODS_phase1_baseline.md`의 두 테이블이 아카이브된 코드 산출물입니다

- "Pipeline Comparison (Whitening Assessment)" ← `_archive/whitening_tests/`
- "Noise Ceiling Analysis" ← `_archive/noise_ceiling_phase1/`

둘 다 **live tex에 대응 수치 0건**이라 정리 규칙대로 아카이브했으나, 이 두 항목에서만 내부 문서와 논문이 어긋납니다.

**필요한 결정**: 두 테이블을 `METHODS_phase1_baseline.md`에서 제거할지, 아니면 아카이브 경로를 명시하는 provenance 주석을 달지.

### R4. Method 3 채택의 정량적 근거가 없습니다

`notion.md:2`에 "Method 3 (Header → MI) 채택"이라는 결론만 있고, 최종 코호트에서의 Method 2 vs Method 3 head-to-head 수치가 없습니다. 아카이브된 비교 자료는 **sub-06 단일 피험자** 기준이며 **Method 2가 이겼다고** 결론짓습니다.

Reviewer의 "왜 BBR이 아니라 MI인가"에 답할 자료가 현재 없습니다. 정리와 무관한 사전 문제이나, `PREPROCESSING_FINAL_REPORT.md` §5에 함께 기록했습니다.

---

## 3. 참고 — 판단보류로 남긴 파일

archive하지 않고 원위치에 둔 항목입니다. 근거가 약해 자동 처분하지 않았습니다.

| 파일 | 위치 | 보류 사유 |
|---|---|---|
| `project_filtered_session.py` | `phase2_SRM_across_between/` | MAP.md E6.2d가 exp2 SRM을 `exp2_convergent.py`로 배정 → 대체된 것으로 보이나 **명시적 폐기 기록 없음** |
| `step_{a..d}_*.py` (4) | `future_phase1_forward_model/scripts/` | 프로젝트 CLAUDE.md는 canonical로 지정, 폴더 CLAUDE.md는 "group prior 계열 기각". E1.1의 `prior_only`/`prior_finetune` arm 상류 |
| `n1_stouffer_omnibus.py` 외 robustness 3종 | 〃 | `TODO_robustness_supplement.md`가 main.tex 체인에 없음. supplement 발행 여부에 종속 |
| `group_prior.py`, `plot_lambda_curve.py` | `phase3_decoder_comparing/.../scripts/` | S-A(decoder Supplementary)에 group prior λ blending을 **포함할지 미정**. 제외하면 archive 대상 |
| `filter_input_stability.py` | `future_phase3_behavioral_analysis/scripts/` | 출력 JSON은 있으나 REPORT/SUMMARY/tex 참조 0건 |
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
