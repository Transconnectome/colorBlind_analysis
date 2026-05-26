# Pipeline 3 Framework — Selection Backbone via Phase B v6

- **Status**: 재설계 (Layer B 폐기, Phase B v6 framework로 통합)
- **Backbone script**: `scripts/s10b_v6_pca_rdm.py` (Pipeline 2와 동일)
- **Re-analysis**: `scripts/s15_oos_reanalysis.py`
- **Date**: 2026-05-26

---

## 0a. Pipeline 2 ↔ Pipeline 3 sub-08 결과 차이 — 왜 다른가

같은 Phase B v6 backbone(s10b_v6_pca_rdm.py)을 공유함에도 두 파이프라인의 sub-08 "후보"가 다른 이유:

| 항목 | Pipeline 2 후보 | Pipeline 3 후보 |
|---|---|---|
| 소스 sprint | S7 Phase B + **Phase C Dirichlet weight sweep**(s12_phase_c_weight_sweep.py) → S08-B R+C g=2.60, S08-E_v4 2-comp (38, −44) | Phase B v6 raw cell + s15 P2 + (collapse + boundary gate) → 2-comp (6, −42)/(44, 36) |
| Selection layer | Phase B v3 composite argmin → Phase C 가중치 grid → multi-point sim filtered | Phase B v6 raw cell의 lexicographic P2 + advisor-권고 gate |
| Cell pool | Phase B v3 (γ_focal + voxel-RDM, 28 cells) | Phase B v6 (γ_focal + γ_all + PCA-RDM K=6 + LOCO, 71 cells) |
| Atom | voxel-RDM | PCA-aligned RDM K=6 (Cycle 5 finding: 2× separation) |

**핵심 framing** (user critique 1·2와 정합):
- 같은 backbone, 다른 selection rule → 다른 후보. 이는 *selection rule의 임의성*의 직접 증거
- 어느 후보 set이 "정답"인지 single selection rule로 결정 불가
- Phase 3 행동 실험만이 inter-rule tiebreaker
- 두 후보 set 모두 *plausible*하며 paper에 *parallel reporting*

---

## 0. Scope 변경

이전 (DECISION_CRITERIA_2026-05-26.md):
- 3-Layer (A: prerequisites → B: convergence E1/E2/E3 → C: §0 selector)
- §0 override → Layer B를 primary selector로 격상

현재 (user directive 2026-05-26 retrospective):
- Layer B (분리된 E1 behav / E2 neural / E3 identifiability) **폐기**
- Phase B v6 framework (single multi-atom composite + 5/2 HC split) 를 selection backbone으로 채택
- §0 LOCO-best는 *행동 실험 전 잠정 default*로 재기술
- Selection rule reformulation은 행동 실험까지 *suspended*

---

## 1. 통합 원리 (왜 Layer B 폐기인가)

User critique 2 (2026-05-26):
> "각 loss마다 behav/neural을 지닐 수도 아닐 수도 있는데, 특정 loss로 eval은 primary 부적합. Post-hoc 설명 검증은 가능."

User critique 후속:
> "어떤 loss로 converge할지는 결국 train-test로만 해소 가능. 어떠한 loss를 쓸지 모르는 상황이고 그 손실함수 또한 평가의 대상."

**결론**:
- E1 = γ-pair Σz²는 *하나의* behavioral operationalization
- E2 = SRM disparity z'는 *하나의* neural operationalization
- 둘 다 primary selector로 두면 *임의 선택*이 숨겨짐
- 통합 → Phase B v6 가 이미 γ(behav) + RDM(neural) + LOCO atom을 *single train/test framework*에서 함께 측정. E1/E2 분리 자체가 redundant

---

## 2. Selection Backbone (재정의)

```
Phase B v6 (Pipeline 2와 공유):
    HC 5/2 split × 300 draws → fit composite → test_loss + test_per_pair + test_agg + test_V1_RDM
    output: per-cell (train_loss_median, test_loss_median/iqr, per-atom test stats, params)

Selection layer (Pipeline 3):
    Step 1: P2 gate (HC stability) — necessary but not sufficient
    Step 2: collapse rejection (NEW, explicit)
    Step 3: per-model best 후보 추출 (immediate goal)
    Step 4: multi-criterion descriptive convergence check (post-hoc evidence)
    Step 5: behavioral validation (Phase 3) — ground-truth tiebreaker
```

---

## 3. P2 (Layer A) — HC stability gate

**Spec** (`s15_oos_reanalysis.py:100-117`):
- Sort key: `(test_loss_median ASC, test_loss_iqr ASC)` lexicographic
- LOCO cells: IQR=+∞ (CVD-internal ridge가 HC pool 변동에 불변 → IQR≈0 unfair tiebreak)
- Top 50% pass

**위치 재정의**:
- Pass = HC normalization robustness 확보 (selection criterion 아님)
- **Fail = paper limitation으로 reporting** ("후보 X는 P2 미통과; HC pool 변동에 sensitive")
- Necessary but not sufficient: P2-pass만으로 후보 lock 불가

---

## 4. Collapse rejection (NEW explicit gate) — user directive 2026-05-26

**Motivation** (user): 
> "Collapse 등 발생 시 해당 loss는 model fitting에서 활용 불가능하다는 이유로 기각 가능할 것. 이것이 train/test 목적."

**현재 상태**: s15 P2 lexicographic은 collapse를 *간접* 처리만 함 (median 악화 + IQR 폭발 cell이 자연스럽게 하위 ranking). **명시적 collapse threshold 없음**.

**실제 collapse 예시** (s10b_v6 sub-08 results):
| Combo | Model | train_loss | test_loss_median | test_loss_iqr | Collapse? |
|---|---|---|---|---|---|
| γOY,YG,YP\|RDMV2\|noLOCO | rc_DPS_lit | −2.679 | **+18.365** | **208.204** | YES |
| γOY,YG,YP\|RDMV2\|noLOCO | rc_Boehm_mid | −2.669 | +13.386 | 153.138 | YES |
| γOY\|RDMV2\|noLOCO | 2comp | −2.892 | −2.359 | 2.150 | no |

→ R+C g=3.00 boundary cells는 train→test에서 *median sign 역전* + IQR 두 자릿수 → collapse 명백.

**제안 explicit gate**:
- **Collapse criterion**: `test_loss_iqr > 3 × |test_loss_median|` OR `|test_loss_median - train_loss_median| > 3 × |train_loss_median|`
- Fail 시 해당 cell + model 조합은 selection pool에서 *기각*
- Paper에 기각 사유와 cell list 명시 (R+C g=3.00 boundary 등)

→ `s15_oos_reanalysis.py`에 추가 필요 (open task).

---

## 5. Per-model best (immediate goal) — user directive

**Gates applied** (advisor 2026-05-26 권고):
- **G1 Collapse**: `test_loss_iqr > 50` OR `sign(train) ≠ sign(test) AND |test−train| > 5`
- **G2 Boundary**: `boundary_rate < 0.5` (50%+ boundary fit = degenerate)
- **G3 P2 sort**: `(test_loss_median ASC, test_loss_iqr ASC)`, LOCO cell IQR=+∞

**Gate stats**:

| Subject | Total cells×models | Collapse | Boundary≥50% | Pass G1+G2 |
|---|---|---|---|---|
| sub-08 | 284 | 91 (32%) | 111 (39%) | **31** |
| sub-09 | 44 | 6 (14%) | 27 (61%) | **2** |

### 5.1. Sub-08 per-model best (supplementary metrics)

| Rank | Model | Loss combo | Fitted param | param IQR | train_loss | test_med ± iqr | test_focal | test_agg (γ_all) | test_V1_RDM | AIC | BIC | bdy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **R+C 1** | rc_Boehm_mid | γ_\|RDMV2\|LOCO | g=0.25 | 0.00 | −2.157 | −2.390 ± 1.24 | 54.52 | 101.74 | 0.990 | 8.61 | 7.30 | 0% |
| R+C 2 | rc_Boehm_mid | γ_\|RDMV3\|LOCO | g=0.25 | 0.00 | −1.964 | −2.186 ± 0.71 | 54.52 | 101.74 | 0.990 | 8.61 | 7.30 | 0% |
| R+C 3 | rc_Boehm_mid | γ_\|RDM_\|LOCO | g=0.05 | 0.00 | −2.104 | −2.104 ± 0.00 | 52.66 | 140.06 | 0.969 | 8.54 | 7.23 | 0% |
| **2-comp 1** | 2comp | γOY\|RDMV2\|noLOCO | βs=6, βc=−42 | βs:8, βc:2 | −2.892 | −2.359 ± 2.15 | 62.48 | 22.77 | 1.240 | 10.88 | 8.27 | 9% |
| 2-comp 2 | 2comp | γYP\|RDMV4\|LOCO | βs=44, βc=36 | βs:4, βc:4 | −3.194 | −2.203 ± 4.03 | **2.45** | 1386.54 | 0.990 | 4.41 | 1.79 | 7% |
| 2-comp 3 | 2comp | γ_\|RDMV2\|noLOCO | βs=4, βc=−26 | βs:4, βc:18 | −1.996 | −2.142 ± 1.36 | 61.73 | 33.30 | 1.233 | 10.86 | 8.25 | 50% |

**Critical observations** (sub-08):

| 관찰 | 함의 |
|---|---|
| R+C top 3 모두 *no-γ* cell (γ_)이며 LOCO 포함 + g ≈ 0.05~0.25 (near-null) | R+C는 behavioral atom을 포함하지 않은 채 거의 영-효과 solution만 stable. *non-trivial R+C solution 부재* |
| R+C top 3의 test_focal ≈ 53~55 (terrible behav residual) | g ≈ 0이면 perceptual shift가 거의 없으니 sub-08 behavioral signal에 fit 못 함 |
| 2-comp rank 1 (βs=6, βc=−42) vs rank 2 (βs=44, βc=36) — **방향성 contradictory** | 두 후보가 *opposite sign* of β_c. 동일 backbone에서 *non-unique* solution. Multi-point sim 식별성 한계 직접 evidence |
| 2-comp rank 2 (βs=44, βc=36) test_focal=2.45 (가장 낮음) | YP-focal fit이 우수하지만 test_agg(γ_all)=1386.54 (매우 큼) → focal pair만 fit, 다른 pair는 오히려 악화 |
| 2-comp rank 1 (βs=6, βc=−42)는 test_agg=22.77 (낮음) | γ_all 관점에선 best, 단 test_focal=62 (focal pair는 fit 안 됨). *opposite tradeoff* with rank 2 |

→ **Sub-08은 R+C가 본질적으로 부적합**. 2-comp 두 후보는 *서로 다른 behavioral evidence axis를 fit*하는 *non-overlapping solutions* (focal-fit vs aggregate-fit).

### 5.2. Sub-09 per-model best (supplementary metrics)

| Rank | Model | Loss combo | Fitted param | param IQR | train_loss | test_med ± iqr | test_focal | test_agg (γ_all) | test_V1_RDM | AIC | BIC | bdy |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **R+C 1** | rc_DPS_lit | γ_\|RDMV1\|LOCO | g=0.50 | 0.00 | −2.190 | −2.384 ± 1.36 | 18.05 | 13.33 | 0.885 | 6.40 | 5.09 | 0% |
| R+C 2 | rc_DPS_lit | γ_\|RDMV1\|noLOCO | g=0.20 | 0.00 | −1.604 | −1.878 ± 1.92 | 15.65 | 17.18 | 0.911 | 6.12 | 4.81 | 0% |
| R+C 3 | rc_DPS_lit | γ_\|RDM_\|LOCO | g=0.50 | 0.00 | −1.494 | −1.494 ± 0.00 | 18.05 | 13.33 | 0.885 | 6.40 | 5.09 | 0% |
| **2-comp 1** | 2comp | γALL\|RDMV1\|noLOCO | βs=2, βc=24 | βs:0, βc:0 | −1.681 | −1.539 ± 1.42 | 6.18 | 16.90 | 0.763 | 6.26 | 3.64 | 0% |
| 2-comp 2 | 2comp | γGB\|RDMV1\|noLOCO | βs=2, βc=24 | βs:0, βc:0 | −1.661 | −1.519 ± 1.41 | 6.18 | 16.90 | 0.763 | 6.26 | 3.64 | 0% |
| 2-comp 3 | 2comp | γALL\|RDM_\|noLOCO | βs=26, βc=4 | βs:6, βc:4 | −0.061 | −0.060 ± 0.00 | 0.99 | 9.44 | 0.789 | 2.59 | −0.03 | 0% |

**Critical observations** (sub-09):

| 관찰 | 함의 |
|---|---|
| R+C top 3 모두 *no-γ* cell + small g (0.20~0.50) | sub-09는 R+C가 behav atom 없을 때 작은 shift를 추정. behav 포함 시 collapse (g=3.0 또는 boundary)으로 가는 패턴 |
| 2-comp rank 1, 2가 **동일 param** (βs=2, βc=24), 다른 cell — **convergent across loss combos** | sub-09 2-comp solution이 *non-trivially convergent*. γALL과 γGB cells 모두 같은 point. param_IQR=0,0 (perfect stability) |
| 2-comp rank 3 (βs=26, βc=4) — train_loss ≈ 0 (거의 null fit) | rank 1/2와 *상충*. param convergent set 외 또 다른 basin |
| 2-comp rank 1 test_focal=6.18, test_agg=16.90, test_V1_RDM=**0.763** (가장 낮음) | RDM cosine distance가 sub-09에서는 best fit으로 떨어짐. neural geometry alignment 확인 |

→ **Sub-09 2-comp (β_s=2, β_c=24)는 multiple loss combos 사이 convergent + RDM과 behav 양쪽에서 best**. R+C는 sub-09에서도 non-trivial solution 부재.

### 5.3. 두 subject 종합 — per-model best 최종

| Subject | Model | 후보 | Stability | Notes |
|---|---|---|---|---|
| sub-08 | 2-comp | (βs=6, βc=−42) γOY\|RDMV2 | param_IQR=(8, 2), test_iqr=2.15 | aggregate-fit (γ_all=22.77 낮음), focal-fit 약함 |
| sub-08 | 2-comp | (βs=44, βc=36) γYP\|RDMV4 | param_IQR=(4, 4), test_iqr=4.03 | focal-fit (test_focal=2.45 최저), aggregate 약함 — *방향성 contradictory*하므로 둘 다 paper에 보고 |
| sub-08 | R+C | (g=0.25) no-γ | 본질적 부적합 | non-trivial R+C 부재, paper에 limitation 명시 |
| sub-09 | 2-comp | (βs=2, βc=24) γALL\|RDMV1 + γGB\|RDMV1 convergent | param_IQR=(0, 0) perfect | best convergent, dual-loss agreement |
| sub-09 | R+C | (g=0.50) no-γ | small shift only | sub-09에서도 non-trivial 부재 |

**Open task**: s15에 (a) collapse gate explicit, (b) boundary gate, (c) per-model best 자동 dump JSON. 위 table을 s15 output으로 자동 생성하도록.

---

## 6. Multi-criterion descriptive convergence (post-hoc)

User directive:
> "Multi-criterion descriptive convergence 동의, 동시에 collapse 발생 시 해당 loss는 기각."

Phase B v6 output에 이미 4개 axis가 존재:
1. `test_loss_median` (composite 안정성)
2. `test_per_pair_medians` (behavioral pair-level)
3. `test_V1_RDM_median` (neural geometry)
4. `test_agg_median` (γ_all aggregate)

**Post-hoc convergence table** (per candidate, paper supporting evidence):
- 각 axis에서 top-N rank
- ≥ 3/4 axis에서 top-5에 들면 "convergent"
- 1-2 axis만 top이면 "criterion-specific" (paper에 명시)

이는 *selection rule*이 아니라 *robustness reporting*. Single primary 대체 아님.

---

## 7. §0 LOCO-best 재기술

**기존 (CLAUDE.md §0)**:
> Filter selection = LOCO-best descriptive fit per subject + behavioral validation.

**현재 (재기술 권고)**:
> Filter selection = (잠정) per-model best within HC-stability-pass cells, pending Phase 3 behavioral experiment as ground-truth tiebreaker. LOCO is one specific loss family and does not uniquely characterize CVD signal; LOCO-best is not the primary selector.

**근거**:
- LOCO 자체가 single loss family. Phase B v6에서 LOCO cell들은 HC pool 변동에 불변 (IQR=+∞ 처리됨) → HC stability evidence 약함
- BEHAVIORAL_FIT §2.5 (CLAUDE)에서 mw_jaccard, l_rank 등 multiple loss alternative가 등장. LOCO 단독 정당화 불충분
- Phase 3 행동 실험만이 inter-loss tiebreaker

---

## 8. N=1 한계 (Pipeline 2 §6.3·§6.4와 동일)

- CVD JND는 pair당 single measurement
- HC train/test split은 HC normalization robustness만 측정
- 개인화 필터 framing으로 unseen-CVD generalizability 불필요로 정당화
- Paper에 limitation 명시

---

## 9. 추가 분석 필요성 (advisor 질의 사항)

### 9.1. 명시적 collapse gate 추가
- s15에 `test_loss_iqr / |test_loss_median|` ratio threshold 추가
- R+C g=3.00 boundary cells 자동 기각 → R+C 후보가 어떻게 변하는가
- Threshold value (3×, 5×, etc.) 결정 근거

### 9.2. Per-model best 자동 추출
- s15 출력에 per-model best 후보 JSON dump 추가
- R+C와 2-comp 각각 top-1, top-3 후보 + HC robustness percentile

### 9.3. Multi-criterion convergence table 생성
- 4 axis (test_loss, test_per_pair, test_V1_RDM, test_agg) ranking
- Cross-axis agreement 시각화 (heatmap or rank-rank scatter)

### 9.4. §0 재기술 PR
- CLAUDE.md §0 + DECISION_CRITERIA §5 (Layer C)
- "LOCO-best primary" → "per-model best within HC-stability + collapse gate pending Phase 3"

### 9.5. s16 E2 SRM disparity 위치 재정의
- E2 (SRM disparity reduction)는 *post-hoc convergence axis 중 하나*로 강등
- Primary selector 기여 없음
- direction 결정 (forward vs inverse −δθ to CVD only) 단순화

---

## 10. Files

- `scripts/s10b_v6_pca_rdm.py` — Phase B v6 (shared with Pipeline 2)
- `scripts/s15_oos_reanalysis.py` — P2 + E1 re-analysis (수정 필요: collapse gate + per-model best)
- `scripts/s16_e2_srm_disparity.py` — SRM disparity post-hoc axis (NOT primary)
- `DECISION_CRITERIA_2026-05-26.md` — 재작성 필요 (Layer B 폐기 반영)
- `BEHAVIORAL_FIT_DIAGNOSIS_2026-05-26.md` §3 — 재작성 필요 (동일)
- `results/s10_inclusion/s10b_v6_pca_rdm_results_{sub-08,sub-09}.json` — backbone output
- `results/oos_reanalysis_v1/{sub-08,sub-09}_e1_p2.json` — P2+E1 output (현재 Layer B 기준)
