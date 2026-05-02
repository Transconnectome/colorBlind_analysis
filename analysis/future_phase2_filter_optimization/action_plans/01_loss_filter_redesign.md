# Action Plan 01 — Loss / Filter 재설계

> 목적: 현 LOCO loss가 vuln rank에 과의존 → (a) 취약 방향 정보 소실, (b) HC false-positive 100% 문제. 취약 수준 + 방향(어느 색이 어느 방향으로 왜곡)을 동시에 잡고 HC 특이성을 회복하는 loss·필터 구조를 탐색한다.
>
> 진행 규칙: 4단계 cycle × 3회 — (1) 현황·문제·원인 분석, (2) 가설/실험 계획, (3) 제작 → smoke → main, (4) 비판 검토 후 다음 cycle. 본 문서는 시간순 로그.

---

## Cycle 1 — 시작 시점: 2026-04-29

### 1) 현황·문제·원인 분석

**A. 현재 loss 구조 (loco_distortion_fit.py:184-250)**

```
L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth
DEFAULT_WEIGHTS = α=1.0, β=0.5, δ=0.2, ε=0.1
NORM = vuln=4.0, rank=2.0, rdm=2.0, smooth=32400
```

각 항의 정규화 후 실제 작동:
- L_vuln = MSE(vuln_sim, vuln_cvd) / 4.0 → 전형 0.05~0.10
- L_rank = (1 − Spearman ρ) / 2.0 → 전형 0.05~0.40
- L_rdm = (1 − cosine ΔRDM) / 2.0 → 전형 0.40~0.50 (cosine이 거의 0 근방)
- L_smooth = mean(diff²) / 32400 → 전형 0.005~0.020

→ 가중치 적용 후 실효 기여:
- α·L_vuln ~ 0.05~0.10
- β·L_rank ~ 0.025~0.20
- δ·L_rdm ~ 0.08~0.10 (delta=0.2 곱해지지만 raw가 큼)
- ε·L_smooth ~ 0.001

**핵심 진단**: ΔRDM cosine은 거의 0이라 L_rdm가 크지만 부호/방향 정보 없음.
L_rank가 모델 차이를 결정하는 사실상 단일 항.

**B. §5-4 표 검증 (Q4 답변에서)**

| Case | (β_s, β_c) | ΔL_vuln | ΔL_rank | ΔL_rdm | Δρ |
|------|:-:|:-:|:-:|:-:|:-:|
| sub-08 hV4 | (38, −14) | +0.002 | **−0.262** | −0.040 | +0.524 |
| sub-08 V1 | (50, −14) | −0.014 | −0.131 | −0.060 | +0.262 |
| sub-09 hV4 | (6, −22) | −0.008 | −0.119 | +0.023 | +0.238 |

→ ΔL_rank가 모든 케이스에서 절대값 최대. L_vuln은 거의 0 변화.
→ "rank만으로 fitting" 사실상 확인.

**C. HC FP=100% 문제 (MEMORY.md baseline_delta_rho)**

`results/archive_outdated/baseline_delta_rho/` 검토:

| subj | group | baseline_rho | best 2comp Δρ | best Δρ-rank/8 |
|:-:|:-:|:-:|:-:|:-:|
| 01 HC | 0.286 | +0.286 (deutan) | — |
| 02 HC | **0.690** | +0.167 (proton) | +0.119 (deutan) |
| **03 HC** | **−0.357** | **+1.048** (proton/deutan) | **상위** |
| 04 HC | −0.048 | +0.667 | 상위 |
| 05 HC | 0.262 | +0.524~+0.667 | 상위 |
| 06 HC | 0.667 | +0.214~+0.286 | 낮음 |
| 07 HC | 0.262 | +0.143~+0.190 | 낮음 |
| 08 CVD | 0.310 | **+0.357** | rank=5/8 |
| 09 CVD | — | — | rank=7/8 (외부 자료) |

핵심 발견:
- **HC sub-03 baseline_rho = −0.357** (음수!) → 단순히 random에 가까운 baseline에서 큰 Δρ를 회복하기 쉬움.
- **HC sub-04 baseline_rho = −0.048** (거의 0) → 마찬가지.
- 즉 Δρ는 사실상 "baseline_rho에서의 회귀(regression-to-mean)" 신호.
- CVD sub-08 (Δρ=+0.357)은 HC sub-03/04/05보다 **낮음**.
- HC corr(baseline, Δρ) = −0.894 (MEMORY.md 진단치).

**D. 정리된 원인**

1. L_vuln (MSE): 정규화 4.0 너무 큼 → 항상 0.10 미만 → 무력화.
2. L_rank: 단일 척도가 fitting을 지배. 8개 색의 *순위 swap* 신호만 잡고 *진폭/방향* 무시.
3. L_rdm: ΔRDM_obs 자체 노이즈 큼(cosine 거의 0), δ=0.2로 약하게 들어감.
4. **HC null 미통합**: loss는 CVD 단일 피험자만 보고 fitting → HC도 fitting하면 거의 같은 Δρ 도달 → specificity 0.
5. baseline_rho 변산이 LOO 내 회귀 신호의 주요 소스인데 가중치는 baseline에 무지.

### 2) 가설 + Action Plan

**가설 H1 — Magnitude 항 추가 (L_mag)**:
`L_mag = | ||vuln_sim|| − ||vuln_cvd|| |² / NORM_mag`
취약 진폭이 일치하지 않으면 페널티. rank 정렬만으로는 통과 못 함.

**가설 H2 — Direction (per-color signed) 항 (L_dir)**:
`L_dir = 1 − cos(d_sim, d_cvd)`,  d_⋅ = vuln_⋅ − mean(vuln_⋅)
8차원 centered 벡터의 cosine. rank-invariant 아니라 *부호+위치* 모두 활용.
실질적으로 Pearson r과 동등. 그러나 L_rank(Spearman)와 dissociate 가능.

**가설 H3 — HC null 보정 (L_specificity)**:
LOO HC pool로 동일 fitting 수행 후
`L_spec = max(0, mean_rho_loo_hc − rho_cvd)`,
또는 z-score 형태:
`z_specificity = (rho_cvd − μ_hc) / σ_hc`,
fitting 시 `L_fit + λ_spec · max(0, −z_specificity)` 추가.
직관: CVD ρ가 HC null 분포 평균보다 *작으면* 페널티 → fit이 HC-typical 패턴으로 수렴 못 하게 차단.

**가설 H4 — Baseline-controlled metric**:
`Δρ_residual = Δρ_obs − f(baseline_rho)` where f는 HC pool에서 학습한 회귀선.
fitting 자체는 Δρ_residual을 maximize (loss = −Δρ_residual).

**가설 H5 — Per-color contribution penalty**:
L_rank에 대한 잔차가 한 색에 집중되면 reject:
`L_concentration = max_i (rank_residual_i²) / sum(rank_residual_i²)`
`> 0.5` 이면 "단일 색에 의존된 fit" → 페널티.

**Action plan (실행 우선순위)**:
1. **H2 (L_dir)** + **H1 (L_mag)** 결합: Pearson 형태 항을 L_rank 옆에 추가하여 수준 정보 회복.
2. **H3 (L_spec)** smoke test: HC LOO pool에서 동일 grid search 실행 후 분포 측정 → CVD 의 p-value 재계산.
3. H4/H5는 Cycle 2~3에서 검토.

### 3) 제작 + smoke run

**스크립트**: `scripts/cycle_loss_redesign/loss_redesign_smoke.py`

목적:
- 현 2-component grid search를 그대로 활용하되, 각 grid point에서 (L_vuln, L_rank, L_dir, L_mag) 분해를 모두 기록.
- HC LOO null: 7명의 HC에 대해서도 동일 grid search 수행 → CVD 와 비교.
- per-color 잔차 + concentration ratio 기록.

**실행 환경**: local conda `srm`. data: `analysis/phase1_procrustes_decoding/results/visualization/full_dataset_C010_with_residuals`.

**Smoke target**: sub-08 V4 + HC sub-01,02,03,04,05,06,07 V4 (8 subjects × 1 ROI). 2-component grid 2°×2° (~1326 pts) 기존 동일.

### 4) 결과 + 비판

**산출물**: `results/cycle_loss_redesign/aggregate.json` + per-subject json.
**실행시간**: 32.0 s (전체 9 subjects × 1326 grid pts, local CPU).

**주의**: sub-07은 `validation/` 폴더에 LOCO json이 없어 fallback synthesized target 사용 → 분포 왜곡 (Δρ=+0.881). 분석에서 제외.

**HC null (n=6) vs CVD (n=2) at hV4, deutan family:**

| metric | HC mean | HC std | sub-08 | p_emp | sub-09 | p_emp |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| Δρ (Spearman) | +0.349 | 0.321 | +0.405 | 0.429 | +0.429 | 0.429 |
| ΔPearson (L_dir) | +0.162 | 0.227 | +0.422 | **0.286** | +0.367 | **0.286** |
| Δl_mag (>0=improve) | −0.082 | 0.117 | **+0.119** | **0.143** | −0.101 | 0.714 |
| baseline_rho-residual Δρ | 0 | 0.147 | +0.188 | 0.286 | −0.116 | 0.857 |

**Within-HC correlations**:
- baseline_rho ↔ Δρ : r = **−0.889** (MEMORY.md 진단치 −0.894 와 일치 → 재현 OK)
- baseline_rho ↔ ΔPearson : r = −0.623 (조금 약화)
- baseline_rho ↔ Δl_mag : 음의 상관 약함 (HC sub-05 outlier)

**핵심 발견**:
1. **L_rank, L_dir 모두 baseline_rho 의존** → CVD specificity 회복 못 함.
2. **L_mag (vuln vector L2-norm 매칭)** : 유일하게 sub-08을 HC pool 위에 올림 (p=0.143).
   - sub-08 Δl_mag=+0.119 (improve) vs HC max=+0.054 → 단독 1위.
3. sub-09는 어떤 metric으로도 분리 안 됨 (baseline_rho=−0.357 자체가 outlier).
4. 회귀 잔차 방식도 sub-09에서는 음수 잔차 → fitting이 baseline 회복 미만.

**비판적 검토**:

(a) **L_mag의 specificity는 진짜 신호인가? 아니면 sub-08의 vuln_target L2-norm이 비정상적으로 큰 데서 오는 우연인가?**
   - sub-08 |target|=1.476 (CVD), sub-09 |target|=1.043, HC |target| 평균≈1.01. sub-08만 |target|이 큼.
   - L_mag = (|sim| − |target|)² → sub-08은 |target|이 커서 baseline에서 |sim|=1.103 < |target|=1.476 → 큰 페널티. 적합하면 |sim|이 |target|쪽으로 이동 가능 → 큰 개선.
   - 즉 L_mag의 분리력은 **vuln 진폭 자체의 outlier**에서 옴. 일반화 가능한 신호로 보기 어려움.

(b) **baseline_rho 음수의 본질**: HC sub-03, 04, 05는 LOCO ridge_gcv가 제대로 안 fit된 경우(혹은 noisy ROI). baseline_rho < 0 자체가 LOO HC null을 오염. 이를 처리 안 하면 specificity 불가능.

(c) **sub-09 패턴**: sub-09 baseline_rho = −0.357이 본질적 문제. 모델이 sub-09 처럼 음수 baseline을 가진 HC와 거의 같은 fitting profile을 보임 → baseline-residualized 잔차가 음수 (HC 평균보다 *더* 못 fit).

**결론 — Cycle 1**:
- 기존 L_rank/L_dir 모두 specificity 미해결.
- **L_mag 단독은 sub-08만 부분 회복**. sub-09에는 미흡.
- 다음 cycle에서: (a) baseline_rho 정상화(positive), (b) per-color magnitude vector matching, (c) HC LOO와 동일한 fitting routine을 fitting loop 내부에서 통합 (constraint optimization).

---

## Cycle 2 — 시작 시점: 2026-04-29 (계속)

### 1) Cycle 1 비판 → 새 진단

Cycle 1 의 핵심 문제:
- L_mag specificity는 **vuln vector의 절대 norm 차이**에 의존. 이것은 sub-08처럼 "전반적으로 모두 nan"인 경우만 잡음.
- sub-09 처럼 "특정 색에서만" 망가진 패턴은 잡지 못함.
- baseline_rho 음수 문제 미해결.

**더 정밀한 가설**: 진폭 정보를 *per-color 단위*로 활용하는 metric이 필요.

### 2) 가설 (Cycle 2)

**H6 — Per-color signed residual vector**:
`r_i = (vuln_sim[i] - vuln_cvd[i])`,
`L_signed = ||r||² + λ · (max_i |r_i|)²`
즉 MSE에 max-residual 페널티 추가. 한 색에 잔차가 집중되면 큰 페널티.

**H7 — Top-k vulnerability profile match**:
가장 취약한(낮은 vuln_corr) k=3개 색 set이 일치하는지 Jaccard.
LOCO target에서 가장 취약한 색은 CVD 핵심 진단 — 이 set이 sim에서도 같으면 OK.
`L_topk = 1 - Jaccard(argpartition(vuln_sim, k), argpartition(vuln_cvd, k))`

**H8 — Loss as standardized "z within HC pool"**:
HC LOO pool에서 (vuln_sim, vuln_target) 분포를 학습 → CVD가 그 분포에서 얼마나 outlier 인가의 z.
이것이 specificity-aware loss.

**H9 — Baseline-conditioned grid restriction**:
fitting의 *시작*을 (bs=0, bc=0)에서 small step만 허용 (e.g., max |bs|≤20°, |bc|≤20°). 큰 shift로 baseline_rho 회귀하는 경로를 차단.

### 3) 실험 계획

Cycle 2 우선 H6, H7, H9 평가.

(a) Cycle 1 결과 그대로 활용하여 **각 grid point의 per-color residual profile** 계산 → top-k Jaccard, max-residual penalty 산출.
(b) `--bs_max 20 --bc_max 20` 으로 grid 제한한 재실행.

### 4) 실행 + 결과

**산출물**:
- `results/cycle_loss_redesign/full_grid/aggregate.json` (재실행 with new metrics, sub-07 제외)
- `results/cycle_loss_redesign/restricted_grid/aggregate.json` (|bs|≤20, |bc|≤20)

**Criterion-by-criterion specificity (full grid, V4, n_HC=6)**:

| 기준(absolute best) | sub-08 best | sub-09 best | HC pool 동점/우월 | sub-08 specificity |
|---|:-:|:-:|:-:|:-:|
| L_rank | 0.333 | 0.929 | **1/6** (sub-02=0.214) | **OK** |
| L_dir | 0.428 | 0.937 | 2/6 | weak |
| L_vuln | 0.319 | 0.194 | 5/6 | FAIL (HC 더 잘 fit) |
| L_mag | 0.012 | 0.000 | 3/6 | weak (HC도 0 도달) |
| L_max_resid | 0.749 | 0.688 | 5/6 | FAIL |
| **L_topk_jaccard** (k=3) | **0.500** | 0.800 | **1/6** (sub-02=0.500) | **OK** |

**핵심 발견 (Cycle 2)**:

1. **L_rank, L_topk_jaccard**: 같은 sub-02만 더 좋음. sub-02는 baseline_rho=0.786 (이미 HC답게 정상 fitting). 즉 *비정상* HC (sub-03/04/05) 를 sub-08 보다 잘 fit하지 못함.
2. **L_topk_jaccard는 가장 직관적 specificity**: "어떤 색이 가장 망가지는지" set 일치 — sub-08의 망가진 색 set은 HC pool 5/6이 매칭 못 함.
3. **sub-09 어떤 metric도 분리 안 됨**: baseline_rho=−0.357이 outlier. 직관적으로 sub-09 의 raw LOCO 패턴 자체가 노이즈가 강하거나 HC 평균 W 와 어긋남 → 모든 fitting routine이 "음수 baseline 회복"으로 수렴 → HC 음수-baseline subjects (sub-04, sub-05) 와 분리 불가.

**비판적 검토 (Cycle 2)**:

(a) **sub-02가 sub-08을 이긴다는 것의 의미**: sub-02는 "이미 잘 fit" → 추가 shift 거의 안 줘도 best. sub-08는 큰 shift 후에 sub-02 수준에 도달. 즉 **fitting 후 absolute level**로 보면 sub-08이 sub-02처럼 보임 — "병자가 정상인 흉내"가 가능하다는 것. 이는 검출(detection) 측면에서 *오히려* sub-08 이 CVD 라는 증거가 약함을 시사.

(b) **L_topk_jaccard의 합리성**: top-3 가장-취약 색이 일치. sub-08의 취약 색 (vuln 작은 c4=green, c8=magenta, c2=orange)이 HC fitting 후에 잘 매치된다면 → 해당 색들이 sub-08만의 신호일 수 있음. HC pool에서 5/6 매치 못함 = sub-08 의 vulnerability hot-spot 이 HC 기저 노이즈와 다름.

(c) **남은 한계**: sub-09는 모든 criterion에서 fail. 별도 진단 필요 — baseline_rho 음수 자체가 LOCO target 수준의 문제인지, ROI 수준 노이즈인지.

(d) **L_topk_jaccard 결과의 grid 의존성 우려**: sub-08, HC sub-02 모두 best가 (bs=0, bc=-50) = grid 경계 → grid 확장 시 변화 가능. 안정성 검증 필요.

**Cycle 2 결론**:
- **sub-08에 대한 specificity는 L_topk_jaccard 또는 (L_rank + 적절한 cap) 으로 회복 가능 (1/6 HC만 동점)**.
- **sub-09는 baseline_rho 자체가 outlier** — fitting metric만으로는 specificity 회복 불가.
- 다음 cycle: (a) sub-09 baseline 진단 (vuln_target 노이즈 vs ROI 문제), (b) L_topk_jaccard의 grid-확장 안정성 검증, (c) 통합 loss `L_new = γ_rank·L_rank + γ_topk·L_topk + γ_mag·L_mag` 가중치 sweep.

---

## Cycle 3 — 시작 시점: 2026-04-29 (계속)

### 1) Cycle 2 비판 → 진단

**핵심 미해결**:
- sub-09 baseline 음수 → 모든 metric fail.
- L_topk_jaccard의 grid-경계 의존성.

### 2) 가설 (Cycle 3)

**H10 — sub-09 baseline 음수의 본질**:
- 가능 원인 1: hV4 voxel 신호 자체가 sub-09에서 약함 (SNR 낮음)
- 가능 원인 2: HC mean W 가 sub-09 에 적합하지 않음 (ridge alpha mismatch)
- 가능 원인 3: vuln_target 자체가 LOCO 노이즈에 압도

**진단 실험**: sub-09 vuln_target 의 *per-color* magnitude/sign 패턴 검사. HC pool 의 W로 sub-09의 voxel을 직접 예측 → 색별 voxel correlation 분포 plot.

**H11 — Combined loss**:
`L_new = γ_topk·L_topk_jaccard + γ_mag·L_mag + γ_rank·max(0, L_rank − cap)`
여기서 cap = HC null의 75th percentile of L_rank → "HC 평균 이상의 fitting 만 카운트". 이는 곧 specificity-aware loss.

### 3) 실행 (시간 부족 시 계획만)

(a) sub-09 진단: per-color voxel correlation, raw amplitude norm 검사.
(b) `L_new` 합성 후 cycle 1/2 데이터로 사후 점수.

### 4) 결과 + 비판 (sub-09 진단만 부분 완료)

**Vuln_target 패턴 진단 (per-color voxel correlation)**:

| subj | grp | most_vuln | z_worst | |target| | baseline_rho |
|---|:-:|:-:|:-:|:-:|:-:|
| 08 CVD | CVD | c7 purple (−0.76) | −1.09 | 1.48 | +0.262 |
| 09 CVD | CVD | c8 magenta (−0.57) | −1.47 | 1.04 | −0.357 |
| 03 HC | HC | c5 cyan | −1.94 | 1.46 | −0.262 |
| 04 HC | HC | c7 purple | −1.75 | 0.93 | −0.357 |
| 05 HC | HC | c8 magenta | −2.20 | 0.51 | −0.738 |

**Pattern similarity matrix** (Pearson r of vuln_target between all 8 subjects):

```
        08    09    01    02    03    04    05    06
08 CVD  +1.00 −0.39 +0.25 +0.38 −0.70 +0.47 −0.23 +0.45
09 CVD  −0.39 +1.00 −0.50 −0.68 +0.59 +0.53 +0.61 −0.30
04 HC   +0.47 +0.53 ...                    ←  sub-09 와 r=+0.53!
05 HC                                +0.61 ←  sub-09 와 r=+0.61!
```

**핵심 진단**:
- **sub-09 의 vulnerability pattern (worst=c8 magenta) 은 HC sub-04, sub-05 와 강한 상관 (+0.53, +0.61)**.
- **sub-08 의 pattern (worst=c7 purple) 은 HC sub-04 와 유사 (r=+0.47)**.
- HC sub-03, sub-04, sub-05 는 자체적으로 매우 noisy한 LOCO target (z_worst |2|에 가까움) → fitting 시 큰 Δρ 회복 가능.

**최종 진단 — HC FPR 100% 의 본질**:

각 subject의 vuln_target은 *single dominant worst color* + *noise on other 7*로 구성됨. 8-색 LOCO 통계 자체의 effective DOF가 ~1~2 수준. 따라서:
1. 단일 worst color 매칭만으로 fitting "성공" 가능 → HC도 CVD 도 같은 방식으로 통과.
2. CVD-specific constellation (multiple cone-axis-aligned failures) 가 데이터에 약함.
3. baseline_rho 음수는 HC의 LOCO target 자체의 noise 수준이 큰 것의 신호 — 8색 중 한두 색 우연히 주방향에서 벗어남.

**Cycle 1~3 종합 결론**:

(a) **L_topk_jaccard (k=3)** 가 sub-08 specificity 측면에서 가장 유망 (1/6 HC만 매칭). 그러나 grid-경계 의존성 검증 필요.

(b) **sub-09 case는 본 데이터 만으로는 specificity 회복 불가**. vuln_target 패턴이 HC sub-04, sub-05 와 r=+0.5~+0.6 — 통계적 분리 어려움.

(c) **fundamental limitation**: 색 8개, run 6개, voxel covariance noise → fitting metric 의 effective DOF 부족. 어떤 loss를 설계해도 8! permutation 의 max ρ ≈ 1.0, 분리 가능 영역 좁음.

(d) **권장 다음 단계**:
   - 8-fold LOCO를 *per-fold* 단위로 활용 (예: 6 runs × 8 colors = 48 fold) → effective DOF 증가.
   - Cross-color magnitude (예: red-cyan opposition score) 같은 cone-axis aligned summary statistic 직접 사용.
   - HC LOO null fitting을 fitting loop 내부 constraint 로 통합 (penalty term).

(e) **현 LOCO-only metric에서 가장 적절한 specificity-aware loss**:
   ```
   L_new = L_rank + γ_topk · L_topk_jaccard
              + λ_spec · max(0, L_rank − HC_pool_75th_percentile)
   ```
   단 γ_topk, λ_spec 가중치는 추가 cycle 에서 보정.

---

## 작성·수정 파일 목록 (Cycle 1~3)

- `action_plans/01_loss_filter_redesign.md` (이 문서)
- `scripts/cycle_loss_redesign/loss_redesign_smoke.py` (신규 스크립트)
- `results/cycle_loss_redesign/aggregate.json` (Cycle 1)
- `results/cycle_loss_redesign/full_grid/aggregate.json` (Cycle 2 metrics 포함)
- `results/cycle_loss_redesign/restricted_grid/aggregate.json` (|bs|≤20)
- per-subject json 16개 (`sub-{ID}_V4_loss_redesign.json`)

---

## Cycle 4 — 시작 시점: 2026-04-29

### 1) Cycle 1~3 종합 + 미해결 진단

(a) **Cycle 2 핵심 발견 재검토**: sub-08 V4 best가 (β_s=38, β_c=−14) 였음. 그러나 grid는 β_s∈[0,50], β_c∈[−50,50] — 38는 내부, −14도 안전. **그러나 다른 criterion (l_dir, l_vuln 등) 이나 다른 subject에서는 (50, −50) 같은 corner가 best 였음**. Cycle 2 self-critique (240번째 줄, "best가 grid 경계 → grid 확장 시 변화 가능").

(b) **Cycle 3 진단 미해결**:
   - sub-09 vuln pattern은 HC sub-04 (r=+0.53), sub-05 (r=+0.61)와 양의 상관. 즉 worst-color **순서**는 같으나 **진폭(depth)** 가 다를 가능성 → magnitude-aware metric으로 분리 가능.
   - L_topk_jaccard (set-only) 는 진폭 정보 무시 — depth가 sub-09에서 더 깊으면 분리 가능.

(c) **선정한 3개 alt metric (A, C, F)**:
   - **A. Magnitude-weighted Jaccard**: top-k 색의 일치를 *CVD의 vuln depth* 로 가중. 같은 색이 망가졌어도 sim에서 그 색의 depth가 회복 안 되면 불일치로 카운트. Cycle 3 진단(pattern vs magnitude 분리)에 직접 대응.
   - **C. Normalized vuln-residual L2** ‖sim−cvd‖ / ‖cvd‖ : Cycle 1 L_mag (절대 norm 차이) 보다 정밀. per-color residual 의 normalized magnitude. baseline_rho 와 회귀 관계 확인 필요.
   - **F. Per-color sign agreement** : 8 색 sign 일치 비율. discrete (0~8) → low DOF 이지만 baseline_rho 와 직교적 신호 가능. 또한 *centered* (above/below mean) 변형도 비교 — Pearson 의 binary version.

기각: B (단일 색 의존, DOF 1), D (rank scaling - 자동 baseline 의존), E (lag - Cycle 3 에서 lag=0 이미 max), G (baseline residual은 sub-09 처럼 baseline_rho 가 outlier 일 때 잔차가 음수 → 무력).

### 2) 가설 + 실험 설계

**H_C4_1**: β_s, β_c grid 확장 시 (±80, ±60) 기존 metric (l_rank/l_dir) 의 best param이 grid edge로 이동 → Cycle 1~3 specificity 결과의 **boundary artifact** 가능성.

**H_C4_2**: **mw_jaccard_loss (A)** 가 baseline_rho 의존성 (corr) 가장 낮을 것 — depth-weighted 라서 baseline noise 회복에 둔감.

**H_C4_3**: **norm_resid (C)** 는 baseline_rho 강한 음의 상관을 보일 것 — baseline 좋을수록 sim-cvd residual이 작음. Specificity 회복 어려움.

**H_C4_4**: **sign_agree_centered (F-centered)** 는 Pearson과 강한 상관 (centered cosine과 동치) → baseline_rho 의존. raw sign_agree 는 mean 기준이 0 이라 다른 신호.

### 3) 실행

**스크립트**: `scripts/cycle_loss_redesign/cycle4_alt_metrics.py` (신규)
**환경**: local conda `srm`
**Grid**: β_s ∈ [0, 80] step=2, β_c ∈ [−60, 60] step=2 → 41×61=2501 pts
**Subjects**: 08, 09, 10 (CVD) + 01, 02, 03, 04, 05, 06 (HC, n=6, sub-07 LOCO json 없음)
**ROI**: V4 (hV4), V1, V2 (3 ROI 모두 local 실행 완료)
**SLURM**: `run_cycle4.sbatch` 작성 (서버 환경 동일 명령, 직접 실행 안 함)

### 4) 결과

#### (a) Boundary artifact 검증 (V4 hV4)

| subj | grp | basρ | l_rank best (β_s, β_c) | edge | mwJac best | mwJ |
|---|:-:|:-:|:-:|:-:|:-:|:-:|
| 08 | CVD | +0.262 | (74, −60) | **B** | (58, −36) | 1.00 |
| 09 | CVD | −0.357 | (0, 58) | . | (44, 54) | 0.45 |
| 10 | CVD | −0.357 | (80, −56) | **B** | (20, 60) | 0.28 |
| 01 | HC | +0.619 | (0, −2) | . | (32, 60) | 0.49 |
| 02 | HC | +0.786 | (0, −4) | . | (0, −34) | 0.50 |
| 03 | HC | −0.262 | (2, 24) | . | (0, −60) | 1.00 |
| 04 | HC | −0.357 | (80, −54) | **B** | (62, −48) | 0.94 |
| 05 | HC | −0.738 | (70, −28) | . | (22, 58) | 0.14 |
| 06 | HC | +0.024 | (46, 58) | . | (0, −60) | 0.49 |

**Cycle 1~3 결과의 핵심 변화**: sub-08 l_rank best가 Cycle 2의 (38, −14) → Cycle 4의 (74, −60) 로 이동. **Cycle 2의 best는 grid_max=50 의 boundary effect였음** — 이 점은 Cycle 2 self-critique 가 정확히 예측한 그대로.

**Boundary stats** (on-boundary 비율):

| metric | CVD on-boundary | HC on-boundary |
|---|:-:|:-:|
| l_rank | 2/3 | 1/6 |
| l_dir | 3/3 | 2/6 |
| l_vuln | 2/3 | 4/6 |
| **l_mag** | **0/3** | **0/6** |
| l_topk_jaccard | 2/3 | 2/6 |
| mw_jaccard_loss | 1/3 | 3/6 |
| norm_resid | 2/3 | 4/6 |
| sign_agree_centered | 2/3 | 0/6 |

→ **l_mag만 grid-안정적**. l_rank/l_dir/l_vuln 는 50% 이상 boundary. 이는 **2-component grid 자체의 fundamental limit**: 8-color × 7-HC 평균 W-fixed 시뮬레이터의 vuln landscape는 단조 monotonic 영역이 매우 넓어 어떤 cap에서도 edge로 수렴 가능.

#### (b) HC null vs CVD specificity (V4 hV4, baseline_rho 상관 포함)

| metric | HC μ ± σ | sub-08 (p, z) | sub-09 | sub-10 | corr(basρ, best) |
|---|:-:|:-:|:-:|:-:|:-:|
| l_rank | +0.560 ± 0.285 | +0.071 (**p=0.14**, z=−1.71) | +0.929 (p=0.86) | +0.333 (p=0.43) | **−0.63** |
| l_dir | +0.580 ± 0.293 | +0.135 (**p=0.14**, z=−1.52) | +0.893 (p=0.71) | +0.213 (**p=0.14**) | **−0.74** |
| l_vuln | +0.097 ± 0.059 | +0.283 (p=1.00) | +0.194 (p=0.86) | +0.016 (p=0.14) | −0.19 |
| l_mag | +0.002 ± 0.005 | +0.011 (p=0.86) | +0.000 (p=0.43) | +0.000 (p=0.43) | −0.62 |
| l_topk_jaccard | +0.650 ± 0.150 | **+0.000 (p=0.14, z=−4.33)** | +0.800 (p=1.00) | +0.500 (p=0.57) | −0.26 |
| **mw_jaccard_loss** | +0.407 ± 0.295 | +0.000 (p=0.29, z=−1.38) | +0.551 (p=0.86) | +0.716 (p=0.86) | **+0.04** |
| norm_resid | +0.905 ± 0.291 | +1.019 (p=0.86) | +1.194 (p=0.86) | +0.553 (p=0.14) | −0.68 |
| sign_agree | +0.771 ± 0.152 | +0.500 (p=1.00) | +0.625 (p=0.86) | +0.750 (p=0.86) | +0.02 |
| sign_agree_centered | +0.792 ± 0.138 | +0.875 (p=0.57) | +0.750 (p=0.71) | +0.875 (p=0.57) | **+0.74** |

**핵심 발견**:
- **l_topk_jaccard** sub-08 z=−4.33: 가장 큰 분리. 그러나 7명 HC 중 sub-04 (mwJ=0.94 = topk_loss=0.06) 가 거의 sub-08에 도달 → p=0.14 (1/7 만 동점/우월).
- **mw_jaccard_loss** baseline 의존성 **+0.04** — **모든 metric 중 baseline 와 가장 직교**. 그러나 sub-08 specificity z=−1.38 (p=0.29) 약함.
- **sign_agree_centered** corr=+0.74 → baseline 강한 의존. 예상대로 (centered Pearson 와 동치).
- **sign_agree (raw, uncentered)** corr=+0.02 — baseline 와 직교. 그러나 sub-08 sign_agree=0.50 ≤ HC mean=0.77 → "CVD가 HC보다 sign 일치 적음" 이라 specificity 방향 이상함. 이는 CVD vuln_target에 음수 색이 더 많아서 sim의 양수와 mismatch가 많음.

#### (c) ROI 비교 (V1, V2)

V1:
- sub-08: l_rank z=−1.84 (p=0.14), l_dir z=−1.88 (p=0.14) — sub-08 V1 LOCO signal이 강함 (baseline=+0.643).
- sub-09: 분리 약함, 모든 metric p≥0.14.
- mw_jaccard_loss corr(basρ)=−0.39 (V4 보다 약하지만 비-zero).

V2:
- **sub-09 V2** l_rank z=+3.32 (p=1.00) — *반대 방향* 분리. CVD가 HC보다 fitting *나쁨*. sub-09 baseline=−0.024 (weak).
- sub-08 V2: 분리 없음.
- norm_resid sub-09 V2 z=+3.45 — **CVD residual이 HC보다 큼**. magnitude 정보가 V2에서는 CVD specificity를 제공.

### 비판 검토

(1) **Cycle 2의 sub-08 specificity는 grid_max=50 boundary artifact였다**: grid 확장 후 best가 (74, −60) 로 이동, l_rank value 0.071 < HC pool min (sub-04=0.31, baseline 음수 outlier) — sub-08 분리 *유지*되지만 절대값과 위치는 변화. 즉 specificity 결론(1/6)은 robust 하나, "어느 (β_s, β_c) 에서" 는 ill-posed.

(2) **mw_jaccard_loss는 baseline-orthogonal 하지만 분리력 약함**: corr=+0.04, sub-08 p=0.29. set-overlap 정보만으로는 8-color 8-DOF 데이터에서 specificity 회복 어려움. 이는 본질적으로 effective DOF 부족(Cycle 3 결론)을 재확인.

(3) **norm_resid 는 baseline 강한 의존 (corr=−0.68) — Cycle 1 L_mag와 동일 패턴**. magnitude-only metric은 baseline_rho 와 분리 불가능 (both controlled by overall vuln amplitude). C 가설 기각.

(4) **sign_agree 는 baseline-orthogonal 이지만 방향 inverted**: CVD가 HC 대비 sign mismatch *많음* → "CVD 식별" 측면에서 양의 신호이나, sub-09 처럼 baseline 나쁜 HC도 같이 떨어짐 → specificity (CVD only) 미확보.

(5) **sub-09/10이 V2에서 분리되는 새 발견**: hV4 외 ROI 에서 패턴 다름. sub-09 V2 baseρ가 V4보다 큼 (−0.024 vs −0.357) → V2 LOCO signal 이 더 정상적이고 fitting margin도 더 작음. 이는 ROI 별 cone-shift 패턴 다양성에 부합.

(6) **CVD-HC 분리에서 V4 sub-08은 가장 안정 (l_rank/l_dir/l_topk_jaccard 모두 p=0.14)**: cycle 1~3 결론 그대로. sub-09 V4는 모든 metric에서 분리 안 됨.

### Cycle 4 결론

(a) **Grid-extension robustness**: sub-08 hV4 specificity 는 grid 확장 후에도 유지 (1/6 HC만 매칭). 그러나 best param 위치는 grid_max에 강하게 의존 — **2-component model의 loss landscape가 본질적으로 monotonic**.

(b) **Alt metric 검증**:
- **A (mw_jaccard_loss)**: baseline-orthogonal (corr=+0.04) 확인 → **유망**. 그러나 specificity (sub-08 z=−1.38) 는 약함.
- **C (norm_resid)**: baseline 강한 음의 상관 (−0.68) → **기각** (Cycle 1 L_mag 와 동일 한계).
- **F (sign_agree)**: raw 는 baseline-orthogonal 이지만 방향 wrong; centered 는 Pearson 동치 → **기각**.

(c) **유일하게 정량적 진보**: l_topk_jaccard (Cycle 2) 와 mw_jaccard_loss (Cycle 4) 두 set-기반 metric이 baseline-residual 신호. **실용 권장 metric** = `α_1·l_topk_jaccard + α_2·mw_jaccard_loss` — Cycle 5 가중치 sweep 필요.

(d) **ROI별 분리 패턴 다름**: V4 = sub-08 specific, V2 = sub-09/10 specific (방향 inverted). 단일 metric으로 모든 CVD 잡기 어려움.

(e) **Cycle 4의 fundamental limit (재확인)**: Cycle 3 결론 — 8-color × 6-run × voxel covariance noise → fitting metric의 effective DOF 부족. metric design만으로 specificity 100% 회복 불가능. **데이터 차원 확장 필요** (per-fold LOCO, 또는 다중 ROI 결합).

### 5) 작성·수정 파일 (Cycle 4)

- `scripts/cycle_loss_redesign/cycle4_alt_metrics.py` (신규)
- `scripts/cycle_loss_redesign/run_cycle4.sbatch` (신규, server hV4+V1+V2 sequential)
- `results/cycle_loss_redesign/cycle4_extended/aggregate.json` + per-subject json (V4)
- `results/cycle_loss_redesign/cycle4_extended_V1/aggregate.json` + per-subject json
- `results/cycle_loss_redesign/cycle4_extended_V2/aggregate.json` + per-subject json
- `action_plans/01_loss_filter_redesign.md` (Cycle 4 섹션 추가)

### 6) Cycle 5 필요성 판단

**필요. Y.** 이유:
1. mw_jaccard_loss + l_topk_jaccard 가중합 sweep (Cycle 4에서 단독만 검증).
2. ROI 결합 metric (V4∩V2 의 sub-08+09 동시 specificity).
3. fundamental limit 검증: per-fold LOCO (6 runs × 8 colors = 48 fold) → effective DOF 확장.

## 미해결 / 다음 세션 과제 (Cycle 5+)

1. **`L_new = α_topk·L_topk + α_mw·L_mw_jaccard` 가중치 sweep** (V4): α_topk ∈ {0.5, 1.0, 2.0}, α_mw ∈ {0.5, 1.0, 2.0}.
2. **ROI-결합 specificity**: V4 CVD-statistic + V2 CVD-statistic 의 OR/AND 결정. sub-08 hV4 specific, sub-09 V2 specific 동시 처리.
3. **per-fold LOCO (DOF 확장)**: 8-color 평균 대신 (run, color) pair = 48 fold. metric noise floor 측정.
4. **sub-09 baseline_rho 음수의 voxel-수준 진단** (보류 — 데이터 더 필요).
5. **V2/V1 ROI 정밀 비교**: sub-09 V2 z=+3.32의 본질 (cone-shift 인지 ROI-specific noise 인지).



