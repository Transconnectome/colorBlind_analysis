# OLD-rendering 최적 모델 — §3 기준 적용 결과

**Date**: 2026-05-11
**Question**: OLD CIELab-direct formula 하에서 §3 framework(LOCO ρ argmax + behavioral validation)를 적용했을 때 각 subject·ROI의 최적 (β_s, β_c)는?

**OLD formula**: δθ = β_s · cos(θ_CIELab − 90°) + β_c · cos(θ_CIELab − 150°)
**Grid**: β_s ∈ [0, 50] step 2, β_c ∈ [−50, +50] step 2 → 1326 cells
**Loss**: L_fit = L_vuln + 0.5·L_rank (§3 weights, NORM 적용; rdm/smooth 제외 — OLD-loss simplified version)
**Subjects**: sub-08 (V4, V1), sub-09 (V4). sub-09 V1은 사용자 요청에 따라 중단.

---

## §1 — sub-08 V4 OLD

### Top 10 by L_fit + 행동 concordance (P2a)

| rank | β_s | β_c | ρ | l_fit | P2a | exact/8 |
|---|---|---|---|---|---|---|
| **1** | **10** | **−32** | **0.833** | **0.126** | 0.250 | 1 |
| 2 | 0 | −20 | 0.738 | 0.149 | 0.287 | 1 |
| 3 | 0 | −18 | 0.738 | 0.149 | 0.287 | 1 |
| **4** | **40** | **+26** | 0.690 | 0.149 | **0.575** | **4** ← Top 10 내 P2a-best (positive β_c 유일) |
| 5-10 | 0-8 | −16 ~ −28 | 0.738 | 0.150-0.152 | 0.287 | 1 |

### §3 적용 결과

**§3-Primary (LOCO ρ argmax / L_fit argmin)**: **(β_s=10, β_c=−32)**
- ρ=0.833, l_fit=0.126
- δθ pattern: 대칭 회전형 [+27.7, +15.4, −6, −23.8, −27.7, −15.4, +6, +23.8]
- 행동 미검증
- P2a 매우 낮음 (0.250, 1/8 exact) — sub-08 perception을 거의 못 잡음

**§3-Behavioral-PASS 후보 (OLD rendering 검증된 유일 행동 데이터)**: **V4-only (β_s=38, β_c=+7)**
- ρ=0.214, l_fit=0.276, rank **619/1326 (47%)** — OLD-loss 기준으로 평범
- 행동 P1 = **2+3p/8** (raw_behav.md, OLD 렌더링 자극으로 측정)
- §3 "behavioral PASS overrides" 규칙 적용 시 유효 후보

**§3-Behavior-concordance 보조 후보**: **(β_s=40, β_c=+26)**
- ρ=0.690, l_fit=0.149 (rank 4) — Top 10 진입
- P2a=0.575, **4/8 exact** — OLD-loss top 10 내 단연 최고
- per-color: ['pink', 'yellow-orange', 'green', 'cyan', 'sky', 'sky', 'sky', 'blue']
- **결정적**: c8 magenta → 'blue' 예측 = sub-08의 실제 "진파랑" 보고와 정확히 일치
- pre_image(c8) = 348° (pink zone) — V4-only OLD와 동일 메커니즘
- 행동 미검증, 차후 우선순위

### 시각화

- `results/phase3_candidates/old_formula_viz/old_sub08_V4_primary.png` — (10, −32)
- `results/phase3_candidates/old_formula_viz/old_sub08_V4_p2a_top.png` — (40, +26)
- `results/phase3_candidates/old_formula_viz/old_sub08_V4_behavPASS.png` — V4-only OLD (38, +7)

### 정직한 평가

- (10, −32) primary는 ρ 높지만 P2a 매우 낮음 → forward model이 정확하지만 sub-08 perception 못 잡음. 모순적 결과로, "ρ-P2a 비단조성"의 사례.
- (40, +26) 보조 후보가 P2a 결정적으로 좋음 → β_c sign-flip 정당화 (OLD 좌표계에서)
- §3 strict 적용 시 (10, −32) 선정 → 그러나 P2a 0.250은 forward model로서 실패에 가까움
- §3 spirit (behavioral PASS overrides) 적용 시 V4-only OLD가 유효 → 이미 P1=2+3p/8 검증
- 두 §3 해석이 다른 후보 도출. Strict는 (10, −32), spirit은 V4-only OLD.

---

## §2 — sub-08 V1 OLD

### Top 10 by L_fit

| rank | β_s | β_c | ρ | l_fit | P2a | exact/8 |
|---|---|---|---|---|---|---|
| **1** | **50** | **+50** | **0.762** | **0.081** | 0.463 | 2 |
| 2 | 50 | +48 | 0.762 | 0.082 | 0.463 | 2 |
| 3 | 48 | +50 | 0.738 | 0.088 | 0.463 | 2 |
| 4-8 | 0-4 | −40 ~ −46 | 0.690-0.714 | 0.102-0.108 | 0.287 | 2 |
| 9-10 | 16 | −4 ~ −6 | 0.667 | 0.110 | 0.400 | 1 |

### §3 적용 결과

**§3-Primary**: **(β_s=50, β_c=+50)** — **GRID EDGE 포화 (degenerate 위험)**
- Grid bounds: β_s ∈ [0, 50], β_c ∈ [−50, 50]. (50, +50)은 두 축 모두 최대값.
- 실제 optimum이 grid 밖에 있을 가능성. 또는 V1 LOCO가 극단적 회전을 선호하는 over-fit.
- ρ=0.762, l_fit=0.081 — 그러나 grid edge에서 평가되어 해석 어려움.
- δθ가 |max β| 영향으로 극단적 분포 → 안정성 의문.

**§3 결정**:
- Grid edge 도달은 V1 LOCO의 well-defined optimum 부재 시사
- CLAUDE.md §3 sub-09 V1 "β_s=β_c=0 degenerate" 사례와 유사 (CURRENT framework에서)
- **V1 단독 filter basis 사용 금지** (CLAUDE.md §8 Anti-Pattern: "V1을 단독 filter basis로 쓰는 시도 금지")
- V1 정보는 cross-ROI loss(Cycle 12)에 부가적으로 사용해야 함

### 정직한 평가

- sub-08 V1 OLD는 well-defined optimum 없음 (grid edge)
- §3 strict 적용 무의미 — CLAUDE.md §3/§8이 V1 단독 사용을 이미 금지
- 결론: sub-08 V1 OLD는 standalone filter generator로 사용 불가

### 시각화
- `results/phase3_candidates/old_formula_viz/old_sub08_V1_primary.png` — (50, +50) edge

---

## §3 — sub-09 V4 OLD

### Top 10 by L_fit

| rank | β_s | β_c | ρ | l_fit | P2a | exact/8 |
|---|---|---|---|---|---|---|
| **1** | **30** | **+46** | **0.500** | **0.156** | 0.500 | 1 |
| 2 | 34 | +44 | 0.500 | 0.157 | 0.500 | 1 |
| 3-8 | 24-36 | +42 ~ +50 | 0.357-0.452 | 0.170-0.197 | 0.500 | 1 |
| 9 | 44 | −32 | 0.381 | 0.201 | 0.450 | 1 |
| 10 | 38 | +42 | 0.333 | 0.204 | **0.537** | **2** |

### §3 적용 결과

**§3-Primary**: **(β_s=30, β_c=+46)** — **positive β_c family**
- ρ=0.500 (sub-08 V4의 0.833 대비 매우 낮음)
- l_fit=0.156
- per-color: ['magenta', 'orange', 'green', 'sky', 'sky', 'sky', 'sky', 'blue']
- c4-c7 4-way collapse → 'sky' 동일 예측. forward model의 over-rotation 의심.
- 행동 미검증

**참고: CURRENT framework sub-09 V4 fit**:
- (β_s=6, β_c=−22), Phase A LOCO 결과 (CLAUDE.md §3)
- 부호 차이: CURRENT β_c=−22 vs OLD β_c=+46 — **부호 반전**
- 강도 차이: CURRENT |β_c|=22 vs OLD |β_c|=46 — OLD가 훨씬 큰 회전 적용

**관찰**:
- Sub-09는 protan으로 sub-08 deutan보다 신경 신호 약함 (ρ=0.500 < 0.833)
- OLD-formula 하 sub-09 V4 fit은 강한 positive β_c로 over-fit 가능성
- 행동 검증 없이는 진정한 §3-primary 결정 불가

### 시각화
- `results/phase3_candidates/old_formula_viz/old_sub09_V4_primary.png` — (30, +46)

---

## §4 — 종합 비교

### OLD vs CURRENT framework optima

| Subject_ROI | OLD §3-Primary | CURRENT §3-Primary | β_c 부호 일치? |
|---|---|---|---|
| sub-08 V4 | (10, −32) | (38, −14) | ✓ 둘 다 negative |
| sub-08 V1 | (50, +50) edge | (50, −14) | ✗ 반전 |
| sub-09 V4 | (30, +46) | (6, −22) | ✗ 반전 |

**부호 반전**: 좌표계 차이 (CIELab vs Stockman opponent)에서 confusion axis (θ_conf=150°)의 effective 위치가 달라짐. 같은 신경 데이터가 OLD에서는 positive β_c로, CURRENT에서는 negative β_c로 fit됨.

### Sub-08 V4 candidates — 행동 데이터와의 cross-reference

| Filter | (β_s, β_c) | Formula | LOCO ρ | P2a | 행동 P1 |
|---|---|---|---|---|---|
| OLD §3-Primary | (10, −32) | OLD | 0.833 | 0.250 (1/8) | 미측정 |
| OLD top10 P2a-best | (40, +26) | OLD | 0.690 | **0.575 (4/8)** | 미측정 |
| **V4-only OLD** | **(38, +7)** | **OLD** | **0.214** | **0.487 (2/8)** | **2+3p/8** ✓ |
| Canonical (CURRENT) | (38, −14) | CURRENT | 0.881 | 0.450 | 2+2p/8 |
| Cycle14 | (58, −36) | CURRENT | — | 0.450 | 2+1p/8 |

**핵심 관찰**:
1. OLD §3-Primary (10, −32)는 ρ 최강이나 P2a/행동 약함 (model fidelity ≠ filter quality 패턴 재확인)
2. OLD top10 P2a-best (40, +26)이 행동 모델 정합도 최강 — c8 magenta→blue 예측이 sub-08 실제 보고와 일치
3. V4-only OLD (38, +7)이 OLD-loss로는 평범하지만 **유일하게 행동 P1 검증 완료** (P1=2+3p/8)

### sub-08 V4 OLD 권장 후보 (§3-spirit 적용, 우선순위)

| 우선순위 | 후보 | 근거 | 다음 액션 |
|---|---|---|---|
| 1 | **V4-only OLD (38, +7)** | 유일하게 행동 검증 완료 (P1=2+3p/8), §3 behavioral PASS overrides | Phase 3 진입 후보 |
| 2 | **(40, +26)** | OLD top10 내 P2a 최고, c8 anomaly 예측, mechanism 유사 | 행동 cycle 추가 |
| 3 | (10, −32) | §3-strict LOCO ρ best, 그러나 P2a 약함 | 보류 (model fidelity만 좋고 filter 효과 낮을 가능성) |

---

## §5 — Caveats

1. **OLD-formula L_fit은 simplified** (l_vuln + 0.5·l_rank만 사용; CURRENT의 L_rdm/L_smooth 제외). 정확한 §3 weights 적용 시 ranking 약간 달라질 수 있음.
2. **sub-08 V1**과 **sub-09 V4**는 underdetermined: V1 grid edge degenerate, sub-09 ρ 낮음 → 단독 filter 결정 어려움.
3. **HC specificity 미산정**: HC under OLD formula의 bootstrap 분포 없음. Specificity는 §0상 selection 아니므로 critical 아님.
4. **rendering vs formula**: OLD/CURRENT formula는 δθ 계산식 차이. 실제 시각화에서 같은 (β_s, β_c)라도 OLD/CURRENT가 다른 col2/col4 예측. 행동 데이터는 어떤 rendering으로 자극을 보여줬는지에 종속.
5. **V4-only OLD P1=2+3p/8 검증의 rendering 출처**: raw_behav.md 자극이 OLD 렌더링으로 제작됨 — STIM_LAB 기준 보정 전 자료. 현 STIM_LAB 렌더링과는 다른 RGB 출력일 수 있음.

---

## §6 — 결론

**OLD rendering 하 §3 최적 (간략)**:

| Subject_ROI | §3 strict (LOCO best) | §3 spirit (behav PASS overrides) | 권장 |
|---|---|---|---|
| sub-08 V4 | (10, −32) — P2a poor | V4-only (38, +7) — P1=2+3p/8 ✓ | **V4-only OLD (38, +7)** |
| sub-08 V1 | (50, +50) — edge degen | (해당 없음) | **사용 금지** (§8 Anti-Pattern) |
| sub-09 V4 | (30, +46) — ρ 낮음 | (해당 없음) | 행동 검증 후 결정 |

**주요 차이점 vs CURRENT framework**:
- sub-08 V4: 부호 일치, 크기 차이 (CURRENT β_s=38 vs OLD β_s=10)
- sub-08 V1: V1 fit이 OLD에서도 degenerate — V1 단독 사용 불가 재확인
- sub-09 V4: 부호 반전 + 크기 차이 (CURRENT β_s=6 negative vs OLD β_s=30 positive)

**§3 framework 충족 후보**: **sub-08 V4 OLD = V4-only (38, +7)** (행동 P1 PASS 보유, OLD-loss top range 밖이지만 §3 spirit "behavioral PASS overrides" 적용 가능).

---

## §7 — 산출물

- `scripts/phase3_old_formula_full_grid.py` — 4 subject-ROI full-grid OLD refit
- `results/old_formula_refit_full/sub-08_V4_summary.json` — V4 OLD 결과
- `results/old_formula_refit_full/sub-08_V4_landscape.json` — full 1326-cell scores
- `results/old_formula_refit_full/sub-08_V1_{summary,landscape}.json`
- `results/old_formula_refit_full/sub-09_V4_{summary,landscape}.json`
- `scripts/phase3_render_old_formula.py` — OLD-formula 시각화 스크립트
- `results/phase3_candidates/old_formula_viz/*.png` — 5개 candidate 시각화
- 이 문서.

**제외**: sub-09 V1 OLD refit (사용자 요청에 따라 중단).
