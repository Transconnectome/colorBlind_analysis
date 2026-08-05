# analysis/validation/_archive

**아카이브 일자**: 2026-08-05 · **근거**: `analysis/ARCHIVE_AUDIT_2026-08-05.md` §2.6

이 폴더는 논문 디렉토리가 아니라 전처리 QC + 방법론 탐색 sandbox입니다. live tex 참조 0건 (유일한 hit은 `methods_v2.tex:97`의 **주석 처리된** 줄이며, 가리키는 `preprocess_Check/`는 현재 부재).

| 범주 | 왜 폐기 |
|---|---|
| `rejected_pipelines/GLMsingle/` | 4개 revision report가 GLMsingle을 pre-draft **drift**로 기록. 논문의 canonical은 2-stage FIR+GLM (`methods_v2.tex`). live tex hit 0건 |
| `rejected_pipelines/whitening/` | live tex에 `whiten` hit 0건 |
| `superseded_alignment/postSRM_procrustes/` | PCA→iterative Procrustes→crossnobis 대안 파이프라인. canonical C010 + `rerun_loo_consistent.py`로 대체 |
| `superseded_alignment/between_procrustes/` | ANOVA voxel-selection / unfiltered-FIR 변종 |
| `preprocessing_qc_oneoff/` | 00–06 QC 체인. 03 계열은 `within_hc_reliability.py`(2026-07-23)로 대체, 05 계열은 `phase3_decoder_comparing` 소관, noise ceiling은 Phase-2 소관 |
| `plans_superseded/` | 위 서브트리들의 기획 문서 |

**남은 KEEP — 진행 중인 작업이므로 archive 금지**:

- `scripts/within_hc_reliability.py` → `results/within_hc_reliability.json`
- `scripts/basis_sensitivity_filter.py` (protan ΔE₀₀ 11.7 basis-swap 민감도)
- `scripts/individual_color_label_permutation.py` (canonical에 없는 개인수준 색라벨 순열)
- `scripts/utils/`, `scripts/BASELINE_SETTINGS_SUMMARY.md`, `plans_decoder.md`

셋 다 2026-07-23자이며 열려 있는 color-specificity gap에 직결됩니다.
