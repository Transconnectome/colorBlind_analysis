# HMC 재산출 — 사전 확정 문서 (Candidate A)

**확정일**: 2026-08-05 · **상태**: 실행 전 확정. 결과를 본 뒤에는 이 문서를 고치지 않는다.

> 이 문서의 목적은 결과를 보고 규칙을 고르는 것을 막는 데 있다. 프로젝트 정책 "selection-rule
> reformulation 금지"의 적용 사례다.

---

## 1. 왜 다시 돌리는가

논문에 보고된 amplitudes는 `fmriprep_out_method3_header_mi`(exp1) / `_2nd`(exp2)에서 나왔고,
이 두 트리는 **머리 움직임 정렬(HMC)이 적용되지 않은 원본 BOLD**를 applywarp로 MNI에 얹은
출력이다(`run_method3_header_mi_all_subjects.sbatch:218,394,446`). MCFLIRT는 별도로 돌아
`.par`만 남기고 정렬본을 삭제한다(`add_motion_correction.sbatch:152`).

그 결과 잔여 미보정 움직임이 종점을 교란한다. 실측:

| 종점 | FD와의 상관 (HC n=7) |
|---|---|
| hV4 LOCO adjacent accuracy | r = −0.21 (p = 0.59) |
| V1 disparity | r = +0.02 (p = 0.96) |
| **V2 disparity** | **r = +0.57 (p = 0.18), ρ = +0.71 (p = 0.071)** |
| V3 / hV4 disparity | +0.09 / +0.26 |

sub-08의 mean FD 0.384 mm는 10명 중 최댓값이고, sub-08의 헤드라인이 V2다. FD를 공변량으로
넣은 단일사례 검정에서 sub-08 V2는 **p = 0.040 → 0.137**로 유의성을 잃는다(sub-09 V1은
0.0066 → 0.0129로 유지). 즉 현 상태로는 "움직임 때문이 아니다"라고 말할 근거가 없다.

**재산출의 목적은 sub-08 V2의 구제가 아니라 교란 요인 하나의 제거다.** 결과가 어느 쪽으로
나오든 보고한다.

---

## 2. 파이프라인 후보와 선택

| | 정합 | HMC | STC | SDC | exp1 | exp2 |
|---|---|---|---|---|---|---|
| 현행 `method3_header_mi` | header→MI | ✗ | ✗ | ✗ | 있음 | 있음 |
| **A. method3 + HMC** ← 채택 | header→MI | ✓ | ✗ | ✗ | 재실행 | 경로 있음 |
| B. `fmriprep_out_original_v3` | FLIRT→BBR | ✓ | ✓ | ✓ | 있음 | **없음** |
| C. `_new` / `_original_v2` / `_deoblique_v2` | 불명 | ✓ | ✓ | ✓ | 있음 | 없음 |
| `_registration_fix` | 불명 | ✓ | ✓ | ✓ | 7명만 | 없음 |

**A 채택 근거**

1. 현행과 **HMC 하나만** 다르다. 결과가 달라지면 원인이 확정된다. B는 정합·STC·SDC가 동시에
   바뀌어 귀인이 불가능하다.
2. B/C는 2차 촬영 대응본이 없다. `bids_2nd`에 fMRIPrep을 돌린 적이 없어 필터 검증 세션 전체를
   새로 전처리해야 한다.
3. C는 각 실행의 명령줄 기록이 남아 있지 않다.
4. FD 교란은 정의상 HMC 미적용에서 온다. A가 정확히 그것만 제거한다.

---

## 3. 실행 사양

**스크립트**: `scripts/run_method3_hmc_all_subjects.sbatch` (exp1, array 1-60),
`scripts/run_method3_hmc_2nd.sbatch` (exp2, array 1-16)

**출력**: `/storage/connectome/haba6030/fmriprep_out_method3_hmc`,
`..._method3_2nd_hmc`. **현행 트리는 건드리지 않는다** — sensitivity arm으로 보존한다.

**정합을 다시 계산하지 않는 근거**: BOLD→T1w(런별 `.lta`)와 T1w→MNI(affine + warp)가
`<현행>/sub-XX/transforms/`에 저장되어 있다. MCFLIRT는 런의 중간 볼륨에 정렬하고, 저장된
`.lta`도 같은 중간 볼륨에서 유도되었으므로 정렬 후에도 그대로 유효하다. bet2 / mri_coreg /
FLIRT / FNIRT는 반복하지 않는다.

**변경되는 단계**: `applywarp --in` 이 원본 BOLD에서 MCFLIRT 출력으로 바뀐다. 재샘플링은
여전히 **1회**다(native → MNI).

---

## 4. 판정 규칙 (실행 전 확정)

**주 판정**: sub-08 V2 disparity, Crawford–Howell one-tailed upper, α = 0.05.

| A에서의 결과 | 처리 |
|---|---|
| p < 0.05 | 유지. 본문에 A 기준으로 보고 |
| p ≥ 0.05 | 유의성 주장에서 **서술적 관찰로 강등**. 초록·서론의 "deutan V2 / protan V1" 대비 구조를 수정 |

A에서는 FD 공변량 보정을 주 검정으로 쓰지 않는다(교란이 제거되었으므로). 참고치로만 병기한다.

**두 파이프라인 결과를 나란히 보고한다.** 유리한 쪽만 싣지 않는다.

---

## 5. 재산출 범위와 순서

1. `run_method3_hmc_*.sbatch` → 새 derivatives 트리
2. `run_full_dataset_C010.py`의 `FMRIPREP_DIR` 교체 → `full_dataset_C010_hmc`
   (exp2는 `exp2_C010_conditions.py:49`)
3. Phase 1 지표 전량 — LORO, LOCO adjacent accuracy, vulnerability profile
4. SRM 재학습 — **HC-only, k = V1 4 / V2 4 / V3 3 / hV4 3 고정**. k를 다시 고르지 않는다
5. disparity (LOO 일관), ΔRDM
6. Phase 2 β 재적합 — 격자 `β_s ∈ [0,50]` 26점 × `β_c ∈ [−50,50]` 51점, 2° (변경 없음)
7. exp2 조건별 재산출

---

## 6. 필터 provenance

배포된 필터는 **sub-08 (β_s = 6, β_c = −42)**, **sub-09 (β_s = 2, β_c = +24)** 이며,
현행(미정렬) amplitudes에서 적합한 값이다. 이 필터로 자극을 렌더해 2차 촬영을 이미 마쳤으므로
**배포본은 변경 불가**다.

논문 서술: 필터 파라미터는 Session 1 데이터에서 추정되어 **Session 2 이전에 동결**되었다.
동결 시점이 검증 세션보다 앞선다는 성질은 전처리를 바꿔도 유지되므로, 현재 서술을 그대로 쓴다.
A에서의 재적합값은 부록에 병기한다.

**β_c 부호 관문 (재산출 후 최우선 확인 항목)**
sub-08 = 음수, sub-09 = 양수라는 **부호 대비**가 논문의 개인차 주장을 지탱한다. A에서 이 대비가
유지되는지를 다른 무엇보다 먼저 확인한다. 부호가 뒤집히면 배포 필터의 근거가 흔들리므로,
그 시점에 보고 전략을 다시 논의한다.

---

## 7. 병행 작업 — 동결 투영 순열

색 라벨 순열의 귀무가 재적합 투영에 흡수되는 문제는 전처리와 무관하다. 별도로 처리한다.

현행 순열 결과(재적합 투영):

| | `cvd_score_disp` | `cvd_pairwise_disp` | `disparity_diff` | `hc_loo_disp` |
|---|---|---|---|---|
| V2 (sub-08) | **0.033** | **0.035** | 0.986 | 0.894 |
| V1 (sub-09) | 0.427 | 0.077 | 0.327 | 0.070 |

sub-08 V2는 부풀려진 귀무(0.674 vs 관측 0.718)를 뚫고 통과한다. 투영을 동결하면 귀무가
내려가므로 이 검정은 강해진다. sub-09 V1은 통과하지 못하므로 동결판에서 재검정이 필요하다.

`analysis/validation/scripts/color_correspondence_loro.py`가 동결 투영 기계를 갖고 있으나
계산하는 통계량이 RDM 상관이다. disparity용 동결 순열은
`analysis/validation/scripts/disparity_frozen_permutation.py`로 신규 작성한다.

---

# 부록 A — 사후 기록: 원고에서 `hmc_v2` arm 을 제외한 결정 (2026-08-24)

> **본문(§1–§7)은 고치지 않았다.** 사전 확정 문서는 실행 전 상태로 보존한다. 이 부록은 **결정과 그 사유를 남기기 위한 사후 기록**이며, 사전 확정 조항을 대체하지 않는다.

## A.1 무엇을 결정했나

**저자 결정 (2026-08-24)**: 재정렬 arm(`hmc_v2`)을 **원고에서 제외**한다. 재정렬 미적용의 근거는 **Methods 에서 보간 비용**으로 제시한다. 원고가 보고하는 전처리 arm 은 셋이 된다.

| arm | 역할 |
|---|---|
| `with_residuals` | 정본 |
| `motreg` | 민감도 주 arm |
| `motshift` | `motreg` 의 음성 대조 |

원고 반영안 전문 = [`docs/PAPER/MANUSCRIPT_EDITS_CONSOLIDATED.md`](../../docs/PAPER/MANUSCRIPT_EDITS_CONSOLIDATED.md) §0.4.

## A.2 §4 조항과의 관계 — 따르지 않았다

§4 는 *"두 파이프라인 결과를 나란히 보고한다. 유리한 쪽만 싣지 않는다"* 로 적혀 있고, `STATUS_ADDITIONAL_ANALYSIS_2026-08-15:327` 은 *"색 종점은 결과와 무관하게 전량 보고하되 판정에는 쓰지 않는다"* 로 적혀 있다. **이번 결정은 그 조항을 따르지 않는다.** 감추지 않고 이 사실을 여기에 명시한다.

**판단 근거는 종점과 무관하게 진술 가능한 성격이다.**

1. 재정렬이 되돌리는 실제 변위가 기준 볼륨 대비 **최대 0.37 복셀**(0.74 mm)이다.
2. 볼륨마다 다른 변환은 보간 오차를 **시변 잡음**으로 만든다. 정본은 전 볼륨에 동일 변환을 쓰므로 그 오차가 시간에 대해 일정해 다중복셀 패턴에서 대체로 상쇄된다.
3. 본 분석의 종점은 미세 복셀 패턴이 지는 표상 기하이므로 그 시변 성분에 직접 노출된다.
4. 실측으로도 ROI tSNR 이 1.7–3.0% 낮아진다.

§4 가 상정한 상황은 **"두 파이프라인 중 어느 쪽을 primary 로 삼을지 결과를 보고 고르는 것"** 이었고, 그 위험은 2026-08-18 에 primary = 정본으로 확정하면서 이미 닫혔다. 이번 결정은 그 위에서 **보고 범위**를 줄인 것이다. 두 사안이 같지 않다는 것이 저자 판단이다.

## A.3 이 결정이 실제로 바꾸는 것

**한 칸이다.** protan V1 disparity 는 `hmc_v2` 가 약화시킨 유일한 arm 이었으므로, 제외하면 보고되는 세 arm 전부에서 유의해진다.

| | 정본 | `motreg` | `motshift` | *(제외)* `hmc_v2` |
|---|---|---|---|---|
| sub-09 V1 | p = .007 / LOSO .045 | p = **.0040** / .0215 | p = **.0048** / .031 | ~~.077~~ |

**나머지는 바뀌지 않는다.** deutan V2 는 `motreg` 이 대조까지 갖춰 지우므로 강등 유지(.218 대 `motshift` .005, 정본 LOSO .116), CVD hV4 개인 결손도 `motreg` 에서 비유의(.148 / .204)이므로 정본 한정 유지, protan $\beta_c$ 부호 반전도 `motreg` 에서 그대로다($+24 \to -24$).

즉 **`hmc_v2` 를 빼서 되살아나는 강등 주장은 없다.** 되살아나는 것은 이미 다른 두 arm 에서도 유의하던 셀 하나의 표현 수위뿐이다.

## A.4 함께 폐기한 것 — ICC 자산

발표 예정이던 ICC(2,1) = 0.825 는 **정본과 `hmc_v2` 사이에서만** 계산된 값이었고(`_arm_agreement.py` 의 `ARMS = ["with_residuals","hmc_v2"]`), 대체 계산이 전부 실패했다.

| 계산 방식 | hV4 | V3 | V2 | V1 |
|---|---|---|---|---|
| 정본↔`hmc_v2` (n=9) | **0.825** | 0.662 | 0.471 | −0.005 |
| 정본↔`motreg` (n=9) | 0.710 | 0.502 | 0.615 | −0.037 |
| 정본↔`motshift` (n=9) | 0.809 | 0.670 | 0.553 | 0.642 |
| 정본↔`motreg` (**HC만 n=7**) | 0.634 | 0.678 | **0.826** | 0.067 |
| 정본 arm 내부 split-half (n=9) | 0.744 | 0.518 | 0.724 | 0.485 |

깨끗한 그림은 `hmc_v2` 쌍 하나에서만 나오고, n=9 값은 **CVD 두 명의 극단값이 피험자 간 분산을 키워 부풀린 것**이다. `hmc_v2` 제외와 무관하게 **인용 금지**로 확정했다.

→ hV4 단독성은 **색 라벨 순열 게이트의 3 arm 재현**(.011 / .013 / .002)만으로 지탱한다.

## A.5 저장소에는 남는다

`hmc_v2` 트리·종점·QC·생성 스크립트는 전부 저장소에 남으며 삭제하지 않는다.

| | 경로 |
|---|---|
| 생성 스크립트 · 코드 감사 · 항등 검사 | `analysis/phase0_preprocessing/hmc_reanalysis/server_recovered/` |
| 품질 (tSNR · ROI 겹침) | `analysis/phase0_preprocessing/results/hmc_summary.csv` |
| 종점 | `analysis/future_phase1_sensitivity/results/perm_adjacent_arm_hmc_v2.json`, `analysis/future_phase1_sensitivity/results/disparity_individual_arms.json` |
| 상세 표 | `analysis/future_phase1_sensitivity/README.md`, `TEAM_BRIEF_2026-08-18.md` |

**리뷰어가 재정렬을 물으면 이 자료로 답한다.** 원고에 싣지 않는 것과 자료를 없애는 것은 다르다.

## A.6 구현 검증 기록 (2026-08-24)

제외 결정과 별개로, `hmc_v2` 구현 자체는 감사를 통과했다.

- **변환 합성 순서**: `convert_xfm -omat M -concat b2t.mat mc.mat/MAT_v` 는 FSL 규약상 뒤 인자를 먼저 적용하므로 `볼륨 v → 기준 볼륨 → T1w` 가 맞다.
- **기준 볼륨 일치**: `REF=$((NV/2))` 하나를 `mcflirt -refvol` 과 `fslroi ... boldref` 에 함께 쓴다.
- **항등 검사 통과**: 기준 볼륨에서 MCFLIRT 행렬이 항등이므로 `hmc_v2` 출력이 정본과 같아야 한다. sub-01·sub-09 는 완전 일치(차 0.000), sub-08 은 차이 나는 복셀이 전부 ±1(정수 저장 반올림, 평균 신호 248 대비 0.4%, 인접 볼륨 차이 12.3 의 1/12).

**따라서 이 arm 을 뺀 근거는 구현 결함이 아니라 방법론적 교환비다.** 두 사유를 혼동해 기록하지 않는다.
