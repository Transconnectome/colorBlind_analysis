# 문제적 파라미터 + Loss 분해 — 동료 공유 문서

> **목적**: 본 연구 `future_phase2_notion.md` §6-5에 적시된 문제적 파라미터들과, §5-4 L_LOCO 분해 표가 모델 선택 논리에 미치는 영향을 동료에게 한 문서로 공유.
>
> **핵심 질문**:
> 1. 어떤 파라미터가 "문제적"이고, 그 문제가 어떤 모델을 약화시키는가?
> 2. L_LOCO 분해 ΔL은 통계적으로 검증 가능한가?
> 3. 두 가지(문제적 파라미터 + ΔL) 결과를 결합하면 모델 선택 논리에 어떤 균열이 보이는가?

---

## 0. 한 줄 요약

| | 약화되는 모델 | 강도 |
|---|---|:---:|
| **R+C g 비현실** (sub-08 V1 g=−2.25, hV4 g=+2.25) | R+C | 중 |
| **Sub-10 V1 2-Comp p=0.004** (정상에서 FP) | 2-Component | **상** |
| **HC LOO FPR=100%** (2-Comp, all 7 HC) | 2-Component | **상** |
| **HC baseline ρ ↔ Δρ 상관 r=−0.894** | LOCO 파이프라인 전체 | **상** |
| **L_rank가 ΔL의 dominant term** (모든 케이스) | rank-only metric의 신뢰성 | 중 |

**채택 논리의 균열**: 두 모델 모두 specificity 신뢰도가 약함. 2-Component의 채택은 "**필터 실현 가능성**(pre-image bijectivity)"에 의존하지, 메커니즘 정확성에 의존하지 않음.

---

## 1. 문제적 파라미터 표 (notion.md §6-5 확장)

| # | 파라미터 | 본 연구 값 | 문헌·기대 범위 | 약화되는 claim | 처리 상태 |
|:-:|---|:---:|---|---|---|
| 1 | **sub-08 V1 g** (R+C) | −2.25 | Tregillus 20–40% over-comp | "R+C g가 cortical compensation을 표현" | §6-5 명시, R+C 부분 기각 |
| 2 | **sub-08 hV4 g** (R+C) | +2.25 (3.25× amplification) | 선례 없음 | R+C가 hV4에서 적합 ρ=0.857인데 g 극단 | §6-5 명시, R+C 부분 기각 |
| 3 | **sub-10 V1 2-Comp p** | **0.004** | normal control이면 NS여야 함 | 2-Component CVD-specificity | §6-5 인정, CLAUDE.md rule 7 면제 |
| 4 | **HC LOO FPR (2-Comp)** | **100% (7/7)** | < α=0.05 (FPR ≤ 0.05) 기대 | 2-Component LOCO+ΔRDM dual-validation | §9 제한점, "HC specificity 미해결" 유보 |
| 5 | **HC baseline ρ ↔ Δρ corr** | **r = −0.894** | 0에 가까워야 (regression-to-mean 없으면) | LOCO Δρ 자체가 baseline noise 흡수 | Job 96664, MEMORY 적시, **specificity claim 보류** |
| 6 | **HC LOCO Δρ vs CVD** | sub-08 emp_p=0.50 / sub-09 0.25 | CVD가 HC tail에 위치해야 | sub-08은 HC sub-03/04/05보다 "더 정상" | Job 96664, **CVD-only 주장 폐기** |

### 출처
- # 1, 2: `loco_distortion_fit.py` 적합 결과, `results/loco_filter/phase_a_rc_opponent/sub-08_V*_rc_opponent.json`
- # 3: `results/loco_filter/phase_a_2component/sub-10_V1_2component.json` p=0.004
- # 4: `results/hc_specificity_test/`, Job 96600 (2026-04-11)
- # 5, 6: `results/baseline_delta_rho/summary.json`, Job 96664 (2026-04-11)

### 시각화 가능 (제안)

```
hV4 LOCO Δρ landscape:
  HC sub-01 ─■■■■■─────  Δρ=+0.32
  HC sub-02 ─■■■■─────── Δρ=+0.21
  HC sub-03 ─■■■■■■■■■─ Δρ=+1.10  ← CVD sub-09(+0.98)보다 큼
  HC sub-04 ─■■■■■■■■─── Δρ=+0.81
  HC sub-05 ─■■■■■■───── Δρ=+0.55
  HC sub-06 ─■■─────────  Δρ=+0.17
  HC sub-07 ─■■■■■─────  Δρ=+0.45
  ─────────────────────
  CVD sub-08 ─■■■─────── Δρ=+0.38 (rank 5/8)
  CVD sub-09 ─■■■■■■■■── Δρ=+0.98 (rank 7/8)
  CVD sub-10 ─■■■■■■■■── Δρ=+0.93 (rank 7/8) ← normal!
```

→ **specificity 부재가 시각적으로 명확**. (그림은 `scripts/visualize_baseline_delta_rho.py`로 생성 가능 — 미작성)

---

## 2. 모델별 영향 평가

### 2.1 R+C 모델

**손상 항목**: # 1, # 2

**해석 옵션**:
- (A) R+C 메커니즘이 본질적으로 틀림 → 모델 폐기.
- (B) R+C의 단일 축 rescaling(RG axis만)이 sub-08 deutan의 150° confusion axis를 온전히 포착하지 못해, 기존 자유도가 *흡수형(soak-up)* 으로 사용되어 g가 극단치를 띰 → **misspecification**.

**현재 입장**: (B)에 가깝게 채택. 즉 R+C는 sub-08 기각의 근거가 메커니즘이 아니라 *적합 자유도 흡수*. 따라서 §6-5 # 1, # 2가 "R+C 폐기"의 근거가 아니라 "R+C 부적합 신호" 정도.

**검증 방법** (제안):
- R+C에 YB axis gain `g_YB` 추가 (3-DOF)하여 sub-08 hV4에서 g, g_YB 분포 → 현재 RG axis only에서 g가 흡수하던 dispersion이 g_YB로 분산되는지 확인.
- 또는 R+C-2D-rotation (`(g_RG, g_YB) ∈ ℝ²`)로 grid search 후 sub-08 hV4에서 |g_RG| 정상 범위 (Tregillus 20–40%) 안으로 떨어지는지 확인.

### 2.2 2-Component 모델

**손상 항목**: # 3, # 4

**해석 옵션**:
- (A) 2-Component가 정말로 CVD-specific하지만 우리의 fit + permutation 방법론이 부족.
- (B) 2-Component가 2 DOF × 8 colors라는 underdetermined system에서 **HC-CVD 차이를 포착하지 않고 noise를 흡수** → noise level이 HC와 CVD에서 비슷해서 FPR=100%.

**현재 입장**: (B)가 더 가까움. 두 가지 정황:
1. HC LOO FPR=100% (7/7) — 모든 HC에서 같은 grid에서 같은 양상으로 적합됨.
2. sub-10 V1 p=0.004도 동일 신호 — CVD가 아닌 normal control도 같은 fit landscape를 따름.

**채택 사슬의 균열**:

```
notion.md §7 채택 근거 (정상 사슬):
  hV4 LOCO p=0.004/0.035 → fit 강함
       ↓
  pre-image 8/8 exact (양쪽 CVD) → 필터 실현 가능
       ↓
  Emery 2021 + Brettel 1997 grounding → physiological
       ↓
  R+C g 비현실 → R+C 약화
       ↓
  ∴ 2-Component 채택

균열:
  hV4 LOCO p=0.004 (sub-08) ─── HC LOO FPR=100%로 invalidated
  hV4 LOCO p=0.035 (sub-09) ─── 같은 invalidate
  Emery grounding ─── 수치 비교 미검증 (literature_math_link.md L2)
  
  유일하게 살아남는 강점: pre-image bijectivity (8/8 exact)
                       ← 이는 모델 메커니즘과 무관한 기하학적 사실
```

**결론**: 2-Component의 채택은 "**필터 실현 가능성**"에만 기반. 메커니즘 정확성·specificity는 **현재 미해결**. 행동 검증(Phase 3)이 최종 중재자.

### 2.3 Machado 1-way 모델

**손상 항목**: 없음 (단, sub-09에서 pre-image 4/8 FAIL — 모델 한계)

- Δλ는 §6-1에서 문헌 severity 직접 일치 → 가장 정합적인 모델.
- HC LOO FPR=43% → 다른 모델보다 specificity 높음 (그러나 여전히 5% 초과).
- 약점: pre-image arc compression으로 sub-09에 적용 불가 (§5-6).

→ Machado는 **검출용**(detection)으로는 가장 신뢰 가능하나, **필터 도출용**(correction)으로는 sub-08만 가능. 즉 *역할 분리*가 옳음.

---

## 3. L_LOCO 분해 (notion.md §5-4) — ΔL의 의미와 검정 가능성

### 3.1 L = Loss (모두 minimize 대상)

`loco_distortion_fit.py:184-250`의 `compute_fit_loss()`:

```
L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth
```

| 항 | 정의 (raw) | 정규화 max | 의미 |
|---|---|:---:|---|
| L_vuln | MSE(vuln_sim, vuln_cvd) | 4.0 | per-color voxel-corr 절대값 차이 |
| L_rank | 1 − Spearman ρ | 2.0 | 색 순위 일치도 (ρ→1이면 0) |
| L_rdm | 1 − cos(ΔRDM_sim, ΔRDM_obs) | 2.0 | RDM 구조 일치 |
| L_smooth | mean(adj_diff²) | 32400 | 인접 색 δθ 부드러움 |

→ **모두 ≥0, 작을수록 좋음**. ΔL = L(fit) − L(baseline=identity), **ΔL < 0 이면 개선**.

### 3.2 §5-4 표 재해석

| Case | ΔL_vuln | **ΔL_rank** | ΔL_rdm | ΔRDM cos post-hoc | Δρ |
|---|:---:|:---:|:---:|:---:|:---:|
| sub-08 hV4 | +0.002 | **−0.262** | −0.040 | +0.080 | +0.524 |
| sub-08 V1 | −0.014 | **−0.131** | −0.060 | +0.120 | +0.262 |
| sub-09 hV4 | −0.008 | **−0.119** | +0.023 | −0.046 | +0.238 |
| sub-09 V1 | −0.010 | **−0.131** | −0.054 | +0.107 | +0.262 |

**관찰**:
1. **ΔL_rank가 모든 케이스에서 dominant** (절대값 가장 큼) → 적합이 "절대값 매칭(MSE)"이 아닌 "순위 일치"를 통해 이뤄짐.
2. ΔL_vuln은 매우 작음 (|ΔL_vuln| ≤ 0.014) → 절대값은 baseline과 거의 차이 없음.
3. sub-09 hV4에서 **ΔL_rdm = +0.023** (악화) — LOCO와 ΔRDM이 **trade-off** 관계임을 시사 (notion.md §4-1의 δ=0.2 가중치가 너무 낮을 가능성).

### 3.3 ΔL의 통계적 검정 가능성

**현재 보고**: per-fit point estimate만 제공, ΔL 자체에 대한 p-value 없음.

**검정 방법 (제안)**:

#### A. Per-color residual permutation (권장)
```python
# 색별 잔차 permutation으로 ΔL_rank null 추정
e_i = vuln_cvd[i] − vuln_sim[i]   # i=0..7

null_delta_L_rank = []
for perm in range(1000):
    e_shuffled = np.random.permutation(e)
    vuln_perm = vuln_sim + e_shuffled
    rho_perm, _ = spearmanr(vuln_sim, vuln_perm)
    null_delta_L_rank.append((1 - rho_perm)/2 - L_rank_baseline)

p = (sum(null >= delta_L_rank_obs) + 1) / 1001
```

#### B. Bootstrap CI
- 8 colors 복원추출 1000회 → 각 부트스트랩에서 ΔL_rank 계산 → 95% CI.
- 한계: n=8 작아 CI 매우 넓을 것 (~±0.15 예상).

#### C. Color leave-one-out
- 색 c 하나를 빼고 7색으로 재적합 → ΔL_rank 변동 측정. 어느 색이 ΔL_rank를 주도하는지 식별.

### 3.4 행동 보고 결합 — 다음 단계

`simulation_recoverability_behavior.md` §3.1의 sub-08 R+C 행동 보고: c3-c4-Y-G 4-way collapse, c5-c6 cyan collapse.

→ **per-color L_vuln_i + 행동 collapse 매트릭스 cross-tab** 분석으로 어느 색에서 모델이 행동과 어긋나는지 정량화 가능.

**제안 스크립트** (`scripts/decompose_loss_per_color.py` — 미작성):
- 입력: `results/loco_filter/phase_a_2component/sub-{08,09}_V4_2component.json`, `behav_validation.md`에서 추출한 행동 collapse 매트릭스.
- 출력:
  - per-color L_vuln, ΔL_rank 기여도 (residual permutation null 포함)
  - color × behavior_collapse cross-tab (Spearman ρ, χ²)
  - 색별 refinement 우선순위
- 비용: local 실행, ~10분.

---

## 4. 종합 의견

### 4.1 모델 선택 논리의 현 상태

| 차원 | Machado | R+C | 2-Component |
|---|:---:|:---:|:---:|
| 적합도 (hV4 LOCO ρ) | sub-08 0.74 / sub-09 0.76 | sub-08 0.86 / sub-09 = Machado | sub-08 0.88 / sub-09 0.69 |
| 파라미터 현실성 | ✅ severity 범위 | ❌ g 극단 | △ β_s order 일치, β_c structurally OK |
| Pre-image | sub-08 ✅ / sub-09 ❌ | sub-08 ✅ | **양쪽 ✅** |
| HC specificity | FPR 43% | FPR 71% | **FPR 100%** |
| sub-10 FP (V1) | NS | — | **p=0.004** |
| 문헌 직접 비교 | ✅ | ❌ | 미검증 (L2) |

**채택**: 2-Component (notion.md §7), 단 *제약적 타당성*. 강점은 pre-image, 약점은 specificity.

### 4.2 만약 reviewer가 본다면 — 예상 비판

1. *"Why 2-Component when HC FPR is 100%?"* → "필터 실현 가능성은 별개의 차원"이라고 답해야 하나, 추가 specificity 통제 실험 없이는 약함.
2. *"sub-10 V1 p=0.004 contradicts your CVD-specificity claim"* → CLAUDE.md rule 7로 sub-10 제외했음을 명시하되, 이는 post-hoc 면제로 보일 수 있음.
3. *"Mean β_s 21.5° ≈ Emery 21.4° — coincidence?"* → forward simulation 미실시. 우연 가능성 명시 필요.
4. *"L_rank dominates ΔL — does that mean MSE matching is not driving the fit?"* → yes, 적합은 순위 일치에 의해 주도됨. notion.md §5-4 표만으로는 이 점이 명시 안 됨.

### 4.3 권고 액션 (우선순위)

| # | 액션 | 비용 | 영향 | 위치 |
|:-:|---|:---:|:---:|---|
| **1** | per-color residual permutation script (`decompose_loss_per_color.py`) | local 1일 | 중 | `scripts/` |
| **2** | β_s ↔ Emery forward simulation (literature_math_link.md L2) | local 1일 | **상** | `scripts/validate_betas_emery_phase.py` |
| **3** | HC baseline Δρ visualization figure | local 0.5일 | 상 (논문용) | `scripts/visualize_baseline_delta_rho.py` |
| **4** | R+C-2D-rotation pilot (sub-08 hV4) | server 0.5일 | 중 (R+C 회생 가능성) | `scripts/loco_distortion_fit.py` 확장 |
| **5** | 2-Component permutation을 "fit-vs-baseline Δρ"로 재정의 | server 1일 | **상** | `loco_distortion_fit.py` 수정 |

특히 **# 5**는 §6-5 # 5 (HC baseline ρ-Δρ 상관 r=−0.894)에 대응하기 위한 핵심 — 현재 permutation은 fit-fixed에서 색 라벨만 셔플하는데, fit-baseline Δρ로 바꾸면 HC FPR이 떨어질 가능성.

---

## 5. 한 페이지 요약 (동료 공유용)

```
[문제적 파라미터]
  R+C g 극단 (sub-08 hV4 +2.25, V1 −2.25): R+C misspecification 신호
  2-Comp HC FPR=100%, sub-10 V1 p=0.004: specificity 부재
  HC baseline ρ ↔ Δρ r=−0.894: regression-to-mean이 Δρ를 지배

[로스 분해]
  L = loss (모두 minimize), ΔL<0 = 개선
  L_rank가 dominant → 순위 일치 위주 적합 (MSE는 marginal)
  ΔL_rank의 p-value: per-color residual permutation으로 추정 가능 (미실시)
  sub-09 hV4 ΔL_rdm=+0.023 → LOCO와 RDM trade-off 존재

[모델 선택 균열]
  2-Component 채택 = pre-image 8/8 exact 강점 vs HC specificity 미해결 약점
  최종 중재 = 행동 검증 (Phase 3 진행 중)

[다음 액션 우선순위]
  1. per-color residual permutation
  2. β_s ↔ Emery forward simulation
  3. HC Δρ landscape 시각화
  4. R+C-2D-rotation pilot
  5. permutation을 fit-vs-baseline Δρ로 재정의
```

---

## 참고 답변 문서
- [`answers/Q4_loss_decomposition.md`](../answers/Q4_loss_decomposition.md) — L 분해 코드 추적
- [`answers/Q7_problem_params_implication.md`](../answers/Q7_problem_params_implication.md) — 문제 파라미터 → 모델 선택 균열
- [`peer_review/literature_math_link.md`](literature_math_link.md) — 문헌 연결 수학 기반 재시도
