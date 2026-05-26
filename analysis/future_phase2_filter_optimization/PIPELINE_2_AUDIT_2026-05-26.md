# Pipeline 2 Closure Audit — Logical Validity + Cycle6b Results

**Date**: 2026-05-26
**Scope**: User directive — (1) cycle6 raw-weight 확장 결과, (2) Pipeline 2 추가 layer의 double-dipping + train-test 일반 원리 부합 검증
**Purpose**: Pipeline 2 closure 가능 여부 판단. *마크다운 정리는 보류* — 본 문서는 audit-only.

---

## 1. Cycle 6b extended raw-weight 결과

**Script**: `scripts/cycle6b_extended_raw_weight.py`
**Input**: `results/s10_inclusion/s10b_v6_pca_rdm_results_{sub-08,sub-09}.json` (재실행 없음, 후처리만)
**Weight schemes**: 47 (w_focal ∈ {0,1,2,5} × w_all ∈ {0,1} × w_RDM ∈ {0,25,50,100,200,400})
**Composite**: `w_focal · γ_focal + w_all · γ_all + w_RDM · RDM` (raw, no z-score)
**Filters**: boundary_rate < 50%, collapse rejection (advisor 권고)
**Cycle6 baseline**: A/B/C schemes (γ_all only / +50RDM / +200RDM) top-8

### 1.1. Sub-08 — **8 NEW candidates** (cycle6 baseline에 없던 후보)

Cross-scheme robustness 순:

| param | NEW? | best_score | best_scheme | schemes_top_5 | test_med±iqr | bdy |
|---|---|---|---|---|---|---|
| **(β_s=44, β_c=36)** | NEW | 2.45 | 1γfocal | **15/47** | −2.20±4.03 | 7% |
| (β_s=6, β_c=−42) | base | 22.77 | 1γall | 9/47 | −2.36±2.15 | 9% |
| (β_s=32, β_c=0) | base | 23.50 | 25RDM | 9/47 | −1.58±1.21 | 0% |
| **(β_s=38, β_c=−10)** | NEW | 139.31 | 2γfocal+1γall | **12/47** | −1.14±**0.86** | **0%** |
| RC g=2.25 | NEW | 23.52 | 25RDM | 10/47 | −0.88±1.38 | 0% |
| (β_s=36, β_c=−14) | NEW | 23.20 | 25RDM | 5/47 | −1.20±2.81 | 30% |
| (β_s=45, β_c=−24) | NEW | 23.66 | 25RDM | 5/47 | −0.03±1.14 | 37% |
| (β_s=4, β_c=−26) | base | 33.30 | 1γall | 6/47 | −2.14±1.36 | 50% |

**핵심**:
- **(β_s=44, β_c=36)**: 가장 cross-scheme robust NEW candidate. Focal-fit dominant (focal=2.45). Pipeline 3 §5에서 본 후보와 일치.
- **(β_s=38, β_c=−10)**: cross-scheme robustness 두 번째 (12/47), bdy=0%, test_iqr=0.86 (가장 안정). 이 후보는 cycle6 raw-weight (γ_all + α·RDM)만으론 surface 안 했고, γ_focal 포함하니 등장.
- **RC g=2.25**: R+C에서 non-boundary + non-collapse NEW. 단 focal=66.56 (terrible behavioral fit) — RDM-driven candidate
- (β_s=6, β_c=−42)는 cycle6 baseline 유지되나 NEW들 사이에서 보면 robustness 중간.

### 1.2. Sub-09 — **1 NEW candidate (weak)**

| param | NEW? | best_score | scheme | schemes_top_5 | test_med±iqr | bdy | train_loss |
|---|---|---|---|---|---|---|---|
| (β_s=34, β_c=−8) | NEW | 0.65 | 1γfocal | 3/47 | −0.03±0.02 | 0% | **−0.03 (null-like)** |
| (β_s=26, β_c=4) | base | 20.72 | 1γfocal+25RDM | **32/47** | −0.06±0.00 | 0% | −0.06 |
| (β_s=2, β_c=24) | base | 93.19 | 1γall+100RDM | 16/47 | −1.52±1.41 | 0% | −1.66 |
| RC g=2.60 | base | 8.88 | 1γfocal+1γall | 14/47 | +0.32±**8.96** | 0% | −0.35 |
| RC g=2.95 | base | 6.41 | 1γall | 3/47 | −0.86±0.57 | 41% | −1.10 |

**핵심**:
- NEW candidate (β_s=34, β_c=−8)는 *train_loss=-0.03 = 거의 null fit*. 실제 fit 가치 약함
- Sub-09는 **(β_s=26, β_c=4)** 가 32/47 schemes에서 top-5 → 압도적 cross-scheme robust. 단 train_loss=−0.06 (null-like)
- **(β_s=2, β_c=24)** 가 train_loss=−1.66 + cross-scheme 16/47 → *non-null + robust* 양쪽 만족하는 유일한 후보
- RC g=2.60 cross-scheme top-5는 많지만 (14/47) test_med +0.32 ± 8.96 → *median 부호 역전 + IQR 발산* → collapse 경계

### 1.3. NEW candidate emergence 종합

| Subject | NEW count | 새 (γ_all + α·RDM) 재정리 가치 |
|---|---|---|
| sub-08 | 8 | **YES** — (β_s=44, β_c=36)과 (β_s=38, β_c=−10) 둘 다 cycle6 baseline 후보 robustness 초과 |
| sub-09 | 1 | NO — 유일 NEW는 train_loss≈0 (null) |

→ **Sub-08 closure는 NEW candidates를 반영하여 재정리 필요**. Sub-09는 cycle6 baseline 유지.

---

## 2. Pipeline 2 Layer Stack — Double-dipping + Train-test 검증

Pipeline 2 = 4 layers (Phase A → B → C → D).

### 2.1. Layer 정의 + 데이터 flow

| Layer | Script | 역할 | Input | Output |
|---|---|---|---|---|
| Phase A | `s10a_precondition.py` | (model × ROI × loss) precondition gate via HC LOO | C010 amplitudes + HC pool | precondition_table.json |
| Phase B v6 | `s10b_v6_pca_rdm.py` | (cell × model) composite fit + 5/2 HC split × **300 draws** | A-pass cells | s10b_v6_pca_rdm_results_{sid}.json |
| Phase C v2 | `s12b_phase_c_v2.py` | Phase B candidates에 대한 Dirichlet weight sweep + 5/2 HC split × **100 draws** | Phase B candidates (4 per subject) | sweep_{sid}.json |
| Phase D | `s13_multipoint_validation.py` | Phase C candidates의 synthetic GT recovery (50 outer × 1 inner) | Phase C candidates | s13_multipoint_recovery*.json |

### 2.2. Phase B → C train/test partition 비교

| Setting | Phase B v6 | Phase C v2 | 동일 여부 |
|---|---|---|---|
| RNG_SEED | 42 (s10b_v6:51) | 42 (s12b:67) | ✓ |
| seed offset | `0 if sub-08 else 1` (s10b_v6:351) | `0 if sub-08 else 1` (s12b:328) | ✓ |
| SUBSET_SIZE | 5 | 5 | ✓ |
| HC_SUBJS | sub-01..07 (s10b_v6:46) | sub-01..07 (s12b:62) | ✓ |
| N_RESAMPLES | 300 | 100 | Phase C는 Phase B의 **첫 100 draws 정확히 재사용** |

### 2.3. ⚠️ Critical finding: Phase B → C double-dipping

**Logic**:
1. Phase B에서 후보 cell들을 **test HC pool의 test_loss median**으로 selection (cell 단위)
2. Phase C는 **동일한 RNG seed + 같은 partition 첫 100 draws**로 후보의 weight sweep fit + evaluation
3. 결과: Phase B에서 candidate selection에 사용된 test HC가 Phase C의 evaluation에도 그대로 들어감

**일반 train/test 원리 위배**:
- Train/test split의 핵심은 *evaluation 데이터가 선택 과정에서 보이지 않음*
- Phase B의 cell selection이 test HC를 본 순간, 그 test HC는 *post-selection*
- Phase C가 같은 partition을 쓰면 selection bias가 propagation됨
- 형식적 정의: Phase C의 test_loss는 (Phase B에서 test HC가 작은 값을 준 cells에 *conditional*)

**증거 (수치)**:
- Phase B v6 sub-08 top cells의 test_loss median = −2.0 ~ −3.0 범위
- Phase C v2가 같은 cells에 weight sweep → test_loss는 *재계산되지만 같은 HC partition을 사용*
- Phase C가 다른 seed (예: 142)를 썼다면 *fresh test HC*로 평가 → Phase B selection bias 차단 가능

**Severity**:
- Strict double-dipping (같은 data로 fit + selection)은 아님 (fit 자체는 train HC만 사용)
- 그러나 *post-selection inference* 위배: Phase B에서 test HC가 conditioning되어 Phase C 결과가 inflated
- Paper-level disclosure 필요 또는 Phase C 재실행 with independent seed

### 2.4. Phase A → B logical validity

- Phase A는 *precondition gate* (어떤 cells가 Phase B에 들어갈지 결정)
- Phase A는 HC LOO 기반 precondition table만 산출. Phase B의 train/test와 데이터 sharing 없음
- ✓ 큰 문제 없음

### 2.5. Phase C → D logical validity

- Phase D는 *synthetic GT data*에서 recovery test
- 원본 HC pool은 GT amplitude pattern 생성에만 사용 (forward perturbation)
- Recovery fit은 synthetic CVD에서 진행되며 GT는 알려진 값
- ✓ Double-dipping 없음 (synthetic data는 ground truth 알려져 있음)

### 2.6. Phase B 내부 train/test 자체 (Pipeline 2 framework §6.3-6.4)

| 항목 | 상태 |
|---|---|
| Train atom (5 HC) ≠ test atom (2 HC) HC normalization | ✓ |
| CVD JND는 train/test 양쪽 동일 (N=1) | ✓ — *개인화 framework로 정당화* |
| Held-out focal pair: fit objective에 제외, eval에 등장 | ✓ — disclosure 필요 (위 §6.4) |
| OOS 축은 HC robustness only | ✓ |

### 2.7. 종합 verdict

| Layer 조합 | Logical validity | 문제 |
|---|---|---|
| Phase A → B | ✓ | 없음 |
| **Phase B → C (현재 구현)** | ⚠️ | RNG seed 공유로 인한 post-selection inference 위배 |
| Phase C → D | ✓ | 없음 (synthetic GT) |
| Phase B 내부 train/test | ✓ (qualified) | OOS = HC robustness only, CVD JND N=1 (framework §6.3로 정당화) |

---

## 3. Closure 가능성 평가

### 3.1. 충족 항목

- ✓ Cycle 6b raw-weight 확장 실행 — sub-08 8 NEW candidates, sub-09 1 NEW (null)
- ✓ Phase B 내부 train/test 분리는 logically valid (HC partition split clean)
- ✓ Phase A, D는 데이터 sharing 없음
- ✓ Sub-09 candidates는 cycle6b에서 baseline 유지로 충분

### 3.2. Blocker — closure 전 해결 필요

**B1. Phase B → C post-selection inference**:
- Phase C v2를 **independent RNG seed**로 재실행 → 새 test HC partition으로 후보 re-evaluation
- 또는 paper-level disclosure: "Phase C used identical HC partitions to Phase B, introducing post-selection inference. Phase C results should be interpreted as candidate refinement, not independent validation"

**B2. Sub-08 NEW candidates 정리**:
- (β_s=44, β_c=36): cross-scheme 15/47 — top robust NEW
- (β_s=38, β_c=−10): cross-scheme 12/47, IQR=0.86 — most stable NEW
- 이들에 대한 multi-point sim Round 3 필요 (Phase D)

**B3. R+C 두 subject 모두 본질적 부적합 명시**:
- Cycle 6b도 R+C top은 g≈2.25 (sub-08) / g=2.60~2.95 (sub-09) but bdy=41% (sub-09) 또는 train=-1.30 only (sub-08)
- R+C는 paper limitation으로만 처리

### 3.3. Closure 시점 권고

**즉시 closure 가능** if:
- B1 disclosure approach 채택 (paper-level qualification으로 처리)
- B2 NEW candidates를 Phase D 없이 *descriptive candidate set*으로 paper에 보고

**Recommend additional work** if:
- B1 Phase C re-run with independent seed (Phase C는 100 draws × 4 candidates × 작은 weight grid → ~30 min)
- B2 Phase D Round 3 multi-point sim 실행 (~15 min)

→ **사용자 결정 필요**: closure 직행 (disclosure 채택) vs. B1+B2 추가 실행 후 closure.

---

## 4. Files

- `scripts/cycle6b_extended_raw_weight.py` — extension (new)
- `results/s10_inclusion/cycle6b_extended_composite_{sub-08,sub-09}.json` — output (new)
- `scripts/s10b_v6_pca_rdm.py` (line 51, 351) — Phase B seed
- `scripts/s12b_phase_c_v2.py` (line 67, 328) — Phase C seed (**동일**)
- `scripts/s13_multipoint_validation.py` (line 56) — Phase D seed (다름: 13579, valid)
- `results/s12b_phase_c_v2/sweep_{sub-08,sub-09}.json` — Phase C output
- `results/s13_multipoint_sim/s13_multipoint_recovery*.json` — Phase D output
