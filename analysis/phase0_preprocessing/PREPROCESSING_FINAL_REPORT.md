# Preprocessing — Final Report (C010)

**작성일**: 2026-08-05 · **대상**: 논문에 보고된 전처리 전량
**정본 드라이버**: `scripts/run_method3_header_mi_all_subjects.sbatch` (exp1) / `scripts/run_method3_header_mi_2nd.sbatch` (exp2)

> 이 문서가 phase0의 최종 리포트입니다. 이전 `REGISTRATION_COMPARISON_FINAL_REPORT.md`는 **Method 2를 채택하라고 결론짓는 sub-06 단일 피험자 문서**였고 논문이 채택한 Method 3과 배치되므로 `_archive/registration_method_selection/`로 이동했습니다. 인용하지 마십시오.

---

## 1. 채택된 파이프라인 (Method 3: Header → MI)

| 단계 | 도구 | 근거 (sbatch 라인) |
|---|---|---|
| BIDS 변환 · defacing | ezBIDS | — |
| T1w skull-strip | FSL `bet2 -f 0.5 -m` (fallback `mri_watershed`) | L190-192 |
| BOLD → T1w 정합 | FreeSurfer `mri_coreg --regheader` (MI, Powell) | L253-266 |
| T1w → MNI 정규화 | FSL FLIRT 12-DOF → FNIRT | L298-307 |
| 표준 공간 | `MNI152NLin2009cAsym_res-2`, 2 mm isotropic | L308-311 |

**Method 2 (Header → BBR)는 채택되지 않았습니다** (`notion.md:2` "Method 3 (Header → MI) 채택"). Method 2 코드와 Dice 기반 방법 선택 자료는 `_archive/registration_method_selection/`에 있습니다.

논문 대응 서술: `docs/PAPER/Methods/methods_v2.tex` (2026-08-05에 위 sbatch 기준으로 대조·보강 완료).

---

## 2. Confound regression — **적용하지 않음**

`docs/PAPER/Methods/supplementary_content.tex:10`:

> *"No temporal filtering or confound regression was applied; slow drift was modeled via linear per-run regressors in the general linear model."*

aCompCor 계열 코드(`generate_confounds.py`, `validate_acompcor_quality.py`, `run_generate_confounds_all.sbatch`)는 시도되었으나 채택되지 않았고 `_archive/confound_regression_abandoned/`로 이동했습니다.

### ⚠ 손상된 confounds TSV — 사용 금지

각 derivatives 폴더의 `*_desc-confounds_timeseries.tsv`는 **placeholder**입니다:

- `framewise_displacement` 컬럼이 288 volume 전부 **0.0**
- `trans_*` / `rot_*`가 header 상수값

`generate_confounds_mcflirt.py`가 실제 `.par` 파일을 찾지 못해 header 값으로 fallback한 결과로 추정됩니다. 이 TSV에서 산출된 모든 그림·표(`_archive/corrupted_fd_outputs/`)는 무효입니다.

**유효한 motion 기록은 `*_desc-motion.par` 뿐이며**, 이는 `scripts/add_motion_correction.sbatch`(exp1) / `add_motion_correction_2nd.sbatch`(exp2)가 MCFLIRT로 생성합니다. 이 realignment는 **motion parameter 기록 전용**이며 분석 데이터에 적용되지 않았습니다.

---

## 3. Motion QC (COBIDAS)

산출: `scripts/motion_qc_summary.py` → `results/motion_qc_summary.json`
FD 정의: Power et al. 2012, 회전은 r = 50 mm로 환산.

### exp1 (`.par` 보유 10명)

| 그룹 | n | mean FD (mm) | SD | range |
|---|---|---|---|---|
| 분석 대상 전체 | 9 | **0.318** | 0.044 | 0.243–0.384 |
| HC | 7 | 0.313 | 0.042 | 0.243–0.379 |
| CVD | 2 | 0.338 | 0.046 | 0.292–0.384 |
| sub-10 (분석 제외) | 1 | 0.321 | — | — |

### exp2 (2nd MRI)

| 그룹 | n | mean FD (mm) | SD | range |
|---|---|---|---|---|
| 분석 대상 전체 | 2 | **0.443** | 0.099 | 0.345–0.542 |

> exp2의 FD가 exp1보다 높습니다(0.443 vs 0.318). N=2라 통계 검정은 무의미하지만, exp2 결과를 해석할 때 염두에 둘 사항입니다.

---

## 4. Registration QC (→ Supplementary S2)

산출: `scripts/diagnose_registration_quality.py` → `scripts/analyze_registration_quality.py`
결과: `results/Method_method3_header_mi/registration_quality_report.md`

| 지표 | 값 |
|---|---|
| ROI coverage | 84.3% ± 21.7% |
| GLM valid voxels | 99.6% |
| sub-07 ROI coverage | 30.8% (known outlier; hV4 = 16 voxels) |

논문 대응: `supplementary_content.tex:17-19`.

---

## 5. 남아 있는 문제

1. **Method 3 채택의 정량적 근거가 문서화되어 있지 않습니다.** `notion.md:2`에 "채택"이라는 결론만 있고 최종 코호트에서의 Method 2 vs Method 3 head-to-head 수치가 없습니다. 아카이브된 비교 자료는 sub-06 단일 피험자 기준이며 **Method 2가 이겼다고** 결론짓습니다. Reviewer가 "왜 BBR이 아니라 MI인가"를 물으면 답할 자료가 현재 없습니다.
2. `analysis/validation/preprocess_Check/` 디렉토리가 참조되지만 존재하지 않습니다 (`methods_v2.tex:97` 주석, `TODO_additional_analysis.md:764`). `git show 47bac51:<path>`로 복원 가능.
3. `logs/`가 640 MB이며 같은 뇌 데이터가 `.nii` + `brainFiles.tar` + `.tar.gz` + `.gz`로 3중 저장되어 있습니다. gitignore 대상이라 저장소 문제는 아니지만 로컬 디스크 정리 대상.
