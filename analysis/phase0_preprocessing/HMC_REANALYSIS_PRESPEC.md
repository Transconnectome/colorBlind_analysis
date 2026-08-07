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

**Primary = A.** 근거는 "움직임 보정된 데이터가 방법론적으로 옳다"이며 결과와 무관하다.
현행 미정렬본은 sensitivity arm으로 강등한다. 이 순서는 결과를 보고 바꾸지 않는다.

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
