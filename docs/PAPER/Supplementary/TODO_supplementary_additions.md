# TODO — Supplementary 신규 섹션 2건

**작성일**: 2026-08-05 · **출처**: `analysis/ARCHIVE_AUDIT_2026-08-05.md` D1 / D3 결정
**담당**: Supplementary 작업 에이전트
**상태**: 미착수

두 항목 모두 **분석은 이미 완료되어 있고 결과 JSON도 커밋되어 있습니다.** 필요한 작업은 tex 작성 + `main.tex` include 등록이며, 새 계산은 없습니다.

---

## S-A. Alternative decoder comparison (Appendix A 참조 해소)

### 왜 필요한가 — 현재 논문에 실재하는 버그

`Methods/methods_v2.tex:132` 마지막 문장:

> *"Alternative decoders evaluated during model selection are described in Appendix~A."*

그런데 `Results/appendix_alternative_models.tex`는 **전부 Phase-2 필터 모델(R+C vs 2-component) 내용**이고 decoder 비교는 한 줄도 없습니다 (`LDA|SVM|MLP|kernel|decoder` grep 결과 0건). 해당 파일 헤더 주석(L2-7)이 2026-06-23 재작성 시 "Historical LOCO-rho-argmax fits and the 2-DOF decomposition have been removed"라고 기록하고 있어, decoder 내용은 애초에 이 파일에 있던 적이 없고 **참조만 남은 상태**로 보입니다.

즉 6-model decoder 비교는 **Methods가 약속하지만 어디에도 보고되지 않았습니다.** 이 TODO는 그 약속을 이행합니다.

### 무엇을 쓸 것인가

새 파일 `docs/PAPER/Supplementary/S_decoder_comparison.tex`를 만들고, `methods_v2.tex:132`의 "Appendix~A"를 이 새 섹션 참조로 교체합니다. (Appendix A 자체는 필터 모델 내용 그대로 유지 — 건드리지 않습니다.)

**핵심 메시지**: forward encoding이 임의 선택이 아니라 6개 모델 비교의 결과라는 것. 그리고 encoding(ρ)과 decoding(accuracy) 판독이 서로 다른 정규화를 쓰는 이유.

### 데이터 소스 (전부 커밋되어 있음)

| 항목 | 경로 |
|---|---|
| 비교 모델 6종 | `LDA, Ridge, KernelRidge, SVM, MLP, ForwardEncoding` (`results/loro/srm/config.json`) |
| LORO 결과 | `analysis/phase3_decoder_comparing/results/loro/{raw,procrustes,srm}/sub-*_performance_raw.json` → `results.srm.{ROI}.{model}[].acc_exact` |
| LOCO 결과 | `analysis/phase3_decoder_comparing/results/loco_srm/sub-*_loco.json` → `results.{ROI}.{model}.overall_adjacent_acc` |
| 생산 코드 | `model_comparison_validation/scripts/{loro_baseline.py, loco_baseline.py}` (+ 각 `_{raw,procrustes,srm}.sbatch`) |
| 그림 생성기 | `model_comparison_validation/scripts/visualize_model_comparison.py` |
| 서술 초안 | `analysis/decoder-comparison.md` (§"The double dissociation", §"Open items"), `analysis/METHODS_phase2b_decoders.md` |

### 반드시 지킬 제약

- **"correlation template matching이 최적"이라는 결론의 근거를 정확히 쓸 것.** 프로젝트 메모리 기록: PopVec/RidgeEnc/GaussML/RidgeReg가 모두 열등한 이유는 *fold당 7색 = 자유도 부족*이지 원리상 열등해서가 아닙니다. "no benefit in current data/task"로 쓰고 "unnecessary in principle"로 쓰지 말 것.
- **성능 비교 시 Brouwer & Heeger 2009와만 paradigm을 맞출 것** (그쪽 24–50 run vs 우리 6 run). Kay 2008 / Naselaris 2009는 다른 과제라 비교 부적절.
- LOCO/LORO 자체는 first가 아님 — B&H가 HC LOCO 선행.
- 앙상블(`FE_Ensemble`, `FE_EnsembleRidge`, `FE_EnsembleGaussML`)은 **기각된 계열**입니다. 결과 JSON에 키가 남아 있으나 보고하지 말 것.

### 부수 효과

이 섹션을 쓰면 아래 4개 파일이 archive 대상에서 **KEEP으로 전환**됩니다 (`ARCHIVE_AUDIT_2026-08-05.md` §2.8 "B1에 종속된 4건"):

`visualize_model_comparison.py`, `group_prior.py`, `plot_lambda_curve.py`, `run_hybrid.sbatch`

> `group_prior.py` / `plot_lambda_curve.py`(λ blending)를 **포함할지는 별도 판단**입니다. Phase-1 group prior 계열은 독립적으로 기각되었으므로, 6-model 비교만 쓰고 group prior는 빼는 쪽이 일관적입니다. 그 경우 이 둘은 archive 유지.

---

## S-B. SRM-independent triangulation (A3 / A4 / A5)

### 왜 필요한가

논문의 헤드라인 기하 결과(SRM disparity: sub-09 V1 p=0.007, sub-08 V2 p=0.040)에 대해 reviewer가 반드시 물을 질문은 **"이게 SRM alignment artifact가 아니라는 증거가 있나?"** 입니다.

그 답이 이미 계산되어 있는데 현재 live tex에는 **0건**입니다 (`crossnobis`, `CCA`, `variance explained` 모두 main.tex include chain에서 hit 없음). `analysis/METHODS_phase2_srm.md` §"Phase 2 Robustness: SRM-Independent Triangulation (A3/A4/A5)" (L304-458)에만 결과 테이블이 있습니다.

이 세 분석의 설계 논리가 정확히 그 반박입니다:

| 분석 | SRM 의존도 | 검증하는 것 |
|---|---|---|
| A4 Crossnobis RDM | **없음** (native voxel space) | SRM 없이도 동일한 HC–CVD 패턴이 존재하는가 |
| A5 PCA→CCA | **없음** (다른 alignment 알고리즘) | 다른 정렬 방법으로도 그룹 차이가 재현되는가 |
| A3 Variance Explained | 있음 (SRM W) | SRM이 CVD 데이터를 잘 설명하는가 (설명 실패가 아닌가) |

### 무엇을 쓸 것인가

새 파일 `docs/PAPER/Supplementary/S_srm_triangulation.tex`. `main.tex`의 supplementary include 블록에 등록.

### 보고할 수치 (`METHODS_phase2_srm.md` L304-458에서 그대로)

| 분석 | 결과 |
|---|---|
| A4 Crossnobis 그룹차 | V1 **p = 0.051** (trending), V2/V3/hV4 ns |
| A4 convergent validity | pooled r = 0.486 (**), 개별 V1 r = 0.721 / V2 r = 0.806 |
| A5 PCA-only | 그룹차 ns 전 ROI, convergent **r = 0.742 (***)** |
| A5 PCA-CCA | 그룹차 ns 전 ROI, convergent r = 0.472 (p = 0.002) |
| A3 VE (LOSO) | 전 ROI CVD ≥ HC, **V2 g = −1.68** (CVD > HC) |

### 서술 프레이밍 — 여기가 핵심

**과대주장 금지.** A4/A5의 *그룹 수준 차이*는 대부분 유의하지 않습니다. 이걸 "재현됨"으로 쓰면 안 됩니다. 실제로 강한 것은 **convergent validity**입니다.

권장 논지:

> SRM disparity는 SRM에 독립적인 voxel-space crossnobis 거리(pooled r = 0.486)와 대안 정렬법인 PCA 거리(r = 0.742)에 모두 강하게 상관한다. 따라서 disparity가 측정하는 양은 SRM 특유의 산물이 아니다. 다만 그룹 수준 유의성은 SRM에서만 나타나는데, 이는 pairwise alignment(45쌍 각각 독립 정렬)가 shared space보다 noise가 크기 때문이며(`METHODS_phase2_srm.md` A5 해석), crossnobis는 *전체 RDM 유사도*를, SRM disparity는 *pair-specific alignment*를 측정한다는 점에서 서로 다른 측면을 포착한다(A4 해석).

A3는 별도 논지입니다: CVD의 VE가 HC 이상이라는 것은 **"SRM이 CVD를 설명하지 못해서 disparity가 커진 것"이라는 대안 설명을 배제**합니다. V2에서 g = −1.68로 오히려 CVD가 더 잘 설명됩니다 — 즉 "strong signal, different structure".

### 아직 열려 있는 문제 — 반드시 같이 언급

프로젝트 메모리 `project_color_specificity_gap`:

> 헤드라인 기하 결과가 **개인 수준 색 라벨 순열을 통과하지 못합니다** (p_perm .22–.98). 색과 무관한 성분이 존재한다는 뜻입니다.

A3/A4/A5는 "alignment artifact가 아니다"는 보이지만 **"색 특이적이다"는 보이지 않습니다.** 두 질문은 다릅니다. Supplementary에서 이 구분을 흐리지 마십시오. 관련 진행 중 분석: `analysis/validation/scripts/individual_color_label_permutation.py`.

### 데이터 소스

| 항목 | 경로 |
|---|---|
| 생산 코드 | `analysis/phase2_SRM_across_between/validation/compute_{crossnobis_rdm,pca_cca_replication,variance_explained}.py` |
| 서술 원본 | `analysis/METHODS_phase2_srm.md` L304-458 (Settings / 결과 테이블 / 해석 / Triangulation Matrix) |
| 상위 SRM 결과 | `phase2_SRM_across_between/results/loo_consistent/20260218_163819/loo_consistent_results.json` |

> 이 세 스크립트는 archive **하지 않습니다** (`ARCHIVE_AUDIT_2026-08-05.md` D3 결정). 원위치 유지.

---

## 공통 체크리스트

- [ ] S-A tex 작성 → `main.tex` include + `methods_v2.tex:132` 참조 교체
- [ ] S-B tex 작성 → `main.tex` include
- [ ] 두 섹션 모두 `~/.claude/writing/academic_writing_rules.md` 적용 (`/revise-draft`)
- [ ] 작성 후 `docs/PAPER/repro/MAP.md`에 신규 E-id 등록 (생산 코드 → 커밋된 JSON 매핑)
- [ ] `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md` Pending Validations 갱신
