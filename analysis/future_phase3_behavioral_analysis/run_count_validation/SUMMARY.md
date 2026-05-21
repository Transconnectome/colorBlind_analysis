# Run-Count Validation — Process · Metrics · Criteria · Decision

**Date**: 2026-05-21
**Goal**: 2nd MRI 실험에서 사용할 **run 수** 결정 (현재 n=6 → 축소 가능 여부)
**Primary deliverable**: 본 문서 + `REPORT.md` (technical detail) + `figs/summary_overview.png` (통합 시각화)

→ 통합 시각화: `figs/summary_overview.png`

---

## 1. 진행 과정

### 1.1 출발점 (5월 19~20, v1)
- LOCO ρ + crossnobis split-half RDM만으로 n=6 vs n=4 비교
- C(6,4)=15 random subsets + 1 anchor + 1 leading = 17 subsets
- 결과: REPORT v1 작성 (5월 20)

### 1.2 피드백 (5월 21)
> "LOCO vulnerability와 같은 *이룹*만을 검증하는 지표로 충분할까요? … 신호 안정성, geometric 특징의 안정성, RDM 등 상대적 위치 등 … 무엇을 기준삼아야 할까요?"

→ **단일 outcome 지표는 불충분.** 데이터 자체의 품질·기하 재현성은 별개의 질문.

### 1.3 재정의 (3개 독립 질문)
| 질문 | 무엇을 확인하는가 |
|---|---|
| **(A) 신호 안정성** | 수집된 voxel β 패턴이 실험 noise에 안정한가? |
| **(B) 기하 재현성** | 8 색의 표현 거리 구조(RDM)가 subset마다 같은가? |
| **(C) 효과 검출** | CVD vs HC의 차이가 통계적으로 잡히는가? |

### 1.4 재실행 (5월 21, v2)
- **Tier 1 (A) + Tier 2 (B) + Tier 3 (C) 동시 평가**
- **9 metrics × 4 ROI × 10 subjects × 5 n values × C(6,n) subsets** = 2,280 cells per metric
- **Stockman-derived baseline** 사용 (v1 stale의 CIELab nominal angles 수정 — MEMORY 2026-04-07 정책 준수)
- **sub-10**을 *null control*로 분리 (gating 대상 아님)

### 1.5 결정
- **V1**을 primary endpoint로 (이전 hV4 가정 부정)
- **n = 5 baseline + n = 4 fallback** (안전 margin 포함)
- Permutation null은 deprecated (grand-mean bias로 invalid)

---

## 2. 활용 지표 (9 metrics × 3 tiers)

### Tier 1 — Signal quality (수집 신호 안정성)

| 지표 | 정의 | 측정 | 단위 |
|---|---|---|---|
| **β-split-half voxel r** | half-A vs half-B의 색별 voxel 패턴 Pearson 상관 | floor(n/2) vs ceil(n/2) 분할, 색별 r 계산 후 평균 | Pearson r ∈ [-1, 1] |
| **LORO 8-way decoding acc** | template-matching 8색 분류 정확도 | hold-out run의 패턴이 어느 색의 W·C 예측에 가장 가까운지 argmax | accuracy ∈ [0, 1], chance=0.125 |
| **GCV α distribution** | LOCO 학습 시 선택된 ridge α 분포 | per-fold α median + IQR | log scale |

### Tier 2 — Geometric stability (RDM 재현성)

| 지표 | 정의 | 측정 | 단위 |
|---|---|---|---|
| **Crossnobis noise ceiling** | RDM split-half Spearman (lower) + Spearman-Brown 보정 (upper) | Walther 2016 crossnobis + MVNN, 8×8 RDM | Spearman ρ |
| **Procrustes split-half disparity** | half-A vs half-B의 8-color configuration 회전·스케일 보정 후 잔차 | scipy.spatial.procrustes | disparity ∈ [0, 1] |
| **Circular-template RSA** | observed RDM vs 이상적 hue-circle chord-distance RDM | Spearman 상관 | Spearman ρ |

### Tier 3 — Outcome detection (HC-vs-CVD 효과)

| 지표 | 정의 | 측정 | 단위 |
|---|---|---|---|
| **LOCO ρ mean** | 8색 leave-one-color-out ridge encoder voxel-Pearson 평균 | 7 train colors → W (GCV α), held-out color 예측 vs 관측 | Pearson r |
| **LOCO ρ per-color** | LOCO ρ의 색별 분해 (8-vector) | 위 단계에서 color-mean 평균 전 값 | 8 × Pearson r |
| **Cohen's d (PRIMARY)** | (HC mean − CVD) / SD_HC | HC 분포 vs CVD 개별 비교, 각 n에서 | unitless d, 0.8=large |
| **Op-A rank stability** | per-color ρ profile의 subset 간 Spearman 평균 | C(6,n) subsets pairwise Spearman | Spearman ρ ∈ [-1, 1] |
| **Op-B vulnerable-set retention** | n=6 anchor의 bottom-2 색이 작은 n에서도 bottom-2인 비율 | k=2 intersection / k | fraction ∈ [0, 1], chance ≈ 0.07 |
| **~~Permutation null~~ DEPRECATED** | within-run label shuffle B=100 | grand-mean bias로 null이 0이 아닌 +0.45 중심 — 사용 안 함 | — |

---

## 3. 판단 기준 (4개 consensus criteria)

Pass criteria evaluated for **CVD-test = sub-08 deutan + sub-09 protan** only (sub-10 null control은 specificity 보조용, gating 제외):

| Criterion | 충족 조건 | 측정 지표 | 의미 |
|---|---|---|---|
| **T1** (signal) | min(β-r) ≥ 0.20 AND min(LORO acc) ≥ 0.25 | β-split-half + LORO 8-way | 신호 자체가 살아 있음 |
| **T2** (geometric) | min(crossnobis NC lower) ≥ 0.40 | crossnobis noise ceiling | RDM이 noise만이 아님 |
| **T3a** (power) | Cohen's d ≥ 0.8 **for both sub-08 AND sub-09** | HC-vs-CVD 분포 비교 | 큰 effect 검출 가능 |
| **T3b** (profile) | Op-B retention ≥ 0.50 **for both sub-08 AND sub-09** | vulnerable-set retention | *현재 vulnerable color 발견이 재현* |

**Consensus rule**: 4개 criteria 모두 통과한 n에서 채택. **Lowest such n = n\***.

### 안전 margin
- **Baseline recommendation**: n\* + 1
- **Aggressive (시간 부족 시)**: n\* (consensus 보장됨)
- **Conservative (불확실성 큰 경우)**: n\* + 2 또는 n=6 유지

---

## 4. 결과 요약 (Consensus per ROI)

| ROI | n=2 | n=3 | n=4 | n=5 | n=6 | **n*** | 권장 사용 |
|---|---|---|---|---|---|---|---|
| **V1** | T1✗ T3b✗ | T1✗ | **✓** | **✓** | **✓** | **4** | **primary endpoint** |
| **V2** | T1✗ T3b✗ | **✓** | **✓** | **✓** | **✓** | **3** | concurrent endpoint |
| **V3** | T1✗ T3a✗ | T3a✗ | **✓** | **✓** | **✓** | **4** | supporting |
| **V4 (hV4)** | T3a✗ | T3a✗ | T3a✗ | T3a✗ | T3a✗ | **∞** | **사용 불가** (sub-09 d≤0.33) |

→ **V1을 primary endpoint로 채택**. Cohen's d:
- sub-08 V1 n=6: **d = +2.25** (HC mean − sub-08 ρ가 2.25 SD)
- sub-09 V1 n=6: **d = +1.35**

→ **n* = 4** (V1 + V2 + V3 동시 통과).

---

## 5. MRI 실험 2 — 최종 권고

### 최우선 권고
**n = 5 runs** per filter condition (safety margin n* + 1).
- 2 filter conditions × 5 runs × 7 min/run ≈ **70 min functional**
- + structural + setup ≈ **90 min total session**
- vs n=6 기준 ~110 min에서 **18% 시간 감소**

### Fallback (시간 부족 시)
**n = 4 runs**: V1/V2/V3 모두 consensus 통과. hV4 endpoint는 어차피 포기.
- ~75 min total session, **30% 감소**

### Conservative (첫 실험이라 안전 우선이라면)
**n = 6 runs** 유지: 추가 발견 없으나 robustness 최대.

---

## 6. 부수 발견 (Phase 3 본실험 영향)

### 6.1 hV4 endpoint 문제
v1에서 가정한 hV4 primary endpoint는 **outcome detection에서 fundamentally 부족**:
- sub-09 hV4 Cohen's d max = +0.65 across all n (n=6에서도 +0.33)
- → run 수를 늘려도 detection power 회복 안 됨
- → MEMORY의 "HC LOCO FPR 7/7 (100%) on hV4" 와 정합
- **Filter 효능 검증 1차 endpoint를 V1으로 재설정 필요** (별도 논의 후 `project_phase2_closure.md` 정합성 확인)

### 6.2 CVD 데이터 품질
- sub-08 V1 β-split-half (n=6): 0.390 > HC mean 0.311
- sub-09 V2 LORO acc (n=6): 0.729 > HC mean 0.426
- → **CVD subjects의 데이터 품질은 HC보다 *우수*하거나 동등**
- → "CVD의 LOCO ρ 저하는 데이터 품질 문제가 아니라 *cone-shift 신호*" 강한 evidence

### 6.3 Per-color vulnerable set (사용자 요청 sub-09 포함)
- sub-08 deutan: 모든 ROI에서 **{c3 yellow, c7 purple}** = M-L 혼동축 일관
- sub-09 protan V1: **{c3 yellow, c8 magenta}** = L 혼동축
- sub-09 protan V2/hV4: **{c6 blue, c8 magenta}**
- → magenta(c8)이 sub-09에서 ROI 전반 vulnerable (protan-specific 신호)

### 6.4 Permutation null bug
Within-run color label shuffle은 global activation pattern을 보존하여 Pearson template-matching ρ가 systematic positive bias (+0.45 ± 0.08). → **deprecated**. Cohen's d (vs HC distribution)가 적절한 detection statistic.

---

## 7. 산출물 인벤토리

### 마크다운 문서
- **`SUMMARY.md`** (본 문서) — process · metrics · criteria · decision
- **`REPORT.md`** — technical detail with all data tables

### 데이터 (`run_count_validation/`)
- `v1_saturation_loco.json` — LOCO ρ + per-color + GCV α (Stockman baseline)
- `v1_saturation_crossnobis.json` — split-half crossnobis Spearman
- `tier1_signal_quality.json` — β-split-half + LORO 8-way
- `tier2_geometric_stability.json` — noise ceiling + procrustes + circular RSA
- `tier3_outcome_detection.json` — Cohen's d + HC-rank p + (deprecated) perm null
- `profile_stability.json` — Op-A + Op-B per cell
- `consensus_table.json` — pass/fail per (ROI, n)

### 시각화 (`run_count_validation/figs/`)
- **`summary_overview.png`** — 통합 시각화 (process · metrics · consensus · key results)
- `tier1_signal.png` — β-split-half + LORO + GCV α
- `tier2_geometric.png` — noise ceiling + procrustes + circular RSA
- `tier3_outcome.png` — LOCO ρ + Cohen's d
- `per_color_profile.png` — 8×n heatmap (sub-08, sub-09, sub-10 × 4 ROIs)
- `profile_stability.png` — Op-A + Op-B curves
- `consensus_decision.png` — 4-criterion pass/fail table

### 스크립트 (`scripts/`)
- `run_count_saturation.py` — LOCO ρ + per-color saturation
- `run_count_tier1.py` — Tier 1 metrics
- `run_count_tier2.py` — Tier 2 metrics
- `run_count_tier3.py` — Tier 3 metrics + permutation
- `plot_tiers.py` — Tier 1/2/3 figures + consensus
- `plot_summary.py` — composite overview figure

### 재현 (전체 ~3 min on local)
```bash
cd analysis/future_phase3_behavioral_analysis
conda activate srm
python scripts/run_count_saturation.py  # ~60s
python scripts/run_count_tier1.py        # ~3s
python scripts/run_count_tier2.py        # ~110s
python scripts/run_count_tier3.py        # ~15s
python scripts/plot_tiers.py             # ~10s
python scripts/plot_summary.py           # ~3s
```

### Superseded
- `v1_allroi_n4_vs_n6.json`, `v1_hV4_n4_vs_n6.json`, `v1_permutation_n4_vs_n6.json` (5월 20)
  — CIELab nominal-angle baseline, stale. 향후 사용 금지.
