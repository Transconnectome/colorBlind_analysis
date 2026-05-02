# Action Plan 02 — Bootstrap 분산 및 모델 선택 기준

> 목적: filter fitting 결과를 HC subject bootstrap 등으로 평가했을 때 분산이 크다면 (a) 분산 크기 자체를 측정하고, (b) point estimate 선택 기준(평균/중앙/모드/안정성 가중)을 어떻게 정할지 정립한다. "단순 평균이 무엇을 잃는지"가 핵심 질문.
>
> 진행 규칙: 4단계 cycle × 3회 — (1) 현황·문제·원인, (2) 가설/실험, (3) 제작 → smoke → main, (4) 검토. 본 문서는 시간순 로그.

---

## Cycle 1 — 시작 시점: 2026-04-29

### 1) 현재 양상·문제·원인 비판 분석

#### 1-A. 기존 fit 파이프라인의 통계 출력

| 지표 | 위치 | 출력 형태 |
|------|------|----------|
| best Δλ / β_s / β_c | `loco_distortion_fit.py:grid_search` | point estimate (1326 grid 점) |
| Spearman ρ | `loco_distortion_fit.py:compute_fit_loss` | point (8개 색에 대한 단일 ρ) |
| label_perm_p | `step1_fit_loco_v2.py:permutation_test_spearman` | exact 8! null = 40320 |
| Δρ (vs baseline) | `step1_fit_loco_v2.py:permutation_test_improvement` | Δρ + perm p |
| baseline ρ | 위 동일, `mean_vuln_baseline` 1회 계산 | point (CI 없음) |
| **HC subject bootstrap** | `comprehensive_2component_analysis.py:bootstrap_ci` (511–593) | **β_s, β_c, cosine만** (Spearman ρ 아님) |
| ΔRDM cosine bootstrap CI | 위 동일 | V1만, n_boot=500 |

#### 1-B. 핵심 결함

1. **HC subject 차원의 ρ 분포가 부재**
   - `bootstrap_ci`는 ΔRDM cosine만 보트스트랩. LOCO ρ는 대상 외.
   - V1만 수행. hV4(primary)에서 HC subject resampling은 **수행된 적 없음**.

2. **"7-HC mean" 기반 point estimate의 취약성을 측정하지 않음**
   - 한 명의 HC가 outlier일 때 평균이 끌려가 Δλ가 흔들리는지 확인 안 됨.
   - 7-HC mean이 unimodal인지 bimodal인지 모름 (Brouwer 2009은 N≈3~6 individual variability가 큼을 시사).

3. **HC LOO LOCO null이 100% FPR**임이 이미 발견됨 (MEMORY: "HC Specificity + Baseline Δρ Diagnostic", `Job 96664`)
   - sub-08 rank 5/8 emp_p=0.50 — HC 5명이 sub-08보다 더 큰 Δρ를 보임.
   - 이는 **per-subject baseline_rho** 변동이 dominant variance source임을 시사.
   - 따라서 ρ point estimate "specificity"는 baseline 분산에 묻혀 있다.

4. **모델 선택 기준의 통계적 의미 미정립**
   - 현재: Spearman ρ point estimate + label-permutation p.
   - 미고려: ρ의 HC subject CI, median/mean/trimmed-mean 차이, mode (다봉성), HC null 분포에 대한 z-score.

#### 1-C. 재현 가능한 출처 (코드 라인)

| 항목 | 파일:줄 | 비고 |
|------|---------|------|
| `precompute_hc_W` | step1_fit_loco_v2.py:156–185 | 7-HC × 1 W (pooled 48 samples) |
| `simulate_mean_hc_wfixed` | step1_fit_loco_v2.py:212–234 | mean → 7-HC 평균 |
| `simulate_single_hc_wfixed` | step1_fit_loco_v2.py:188–209 | per-HC vuln (8,) |
| `permutation_test_spearman` | step1_fit_loco_v2.py:262–298 | 8! exact, but on mean_vuln |
| `bootstrap_ci` (ΔRDM) | comprehensive_2component_analysis.py:511–593 | ρ 미산출 |
| `load_cvd_loco_target` | step1_fit_loco_v2.py:399–408 | future_phase1_forward_model/results/validation/sub-XX_loco.json |

### 2) 가설 + 실험 계획

#### 가설

- **H1 (LOHO 변동성)**: 7-HC mean ρ는 한 HC를 빼면 ±0.05~0.20 변동하며, 어떤 HC를 빼느냐에 따라 best Δλ/β가 변동한다 (특히 hV4 K=3, 작은 dim에서 큰 변동 예상).
- **H2 (CI ↔ FPR 연결)**: CVD subject별 ρ의 95% bootstrap CI(HC resampling)가 HC LOO ρ 분포와 겹치면 specificity 부재가 점-추정-기반(MEMORY) 설명에 이어 분산 기반으로도 검증된다.
- **H3 (Robust estimator)**: 평균 대신 (a) median, (b) trimmed mean(20%), (c) HC LOO null로 z-점수 보정한 ρ가 sub-10(normal control)과 sub-08/09의 분리도를 회복할 수 있다.

#### 실험 설계

**Bootstrap A — HC LOHO (Leave-One-HC-Out)**: 결정론적, n=7
- 7가지 LOHO 조합으로 mean_vuln 계산 → 각 조합에서 **grid search 재실행** → 7개 (Δλ, ρ, p)
- ρ_LOHO 분산, best param 분산, p_LOHO IQR 측정
- 비용: 7 LOHO × 3 CVD × 3 model × 1 ROI(hV4) = 63 grid search ≈ 7×34s = 4분/조합 → 252분. 너무 큼.
- 단순화: hV4 + sub-08/09/10 + 2component만 → 21 fits ≈ 12분.

**Bootstrap B — HC subject resampling (with replacement)**: 확률적, n_boot=500
- 매 반복 7명을 복원 추출 → mean_vuln(7개의 LOO-precomputed W 사용) 평균 → 고정 best params에서 ρ 산출
- W 재학습 안 하므로 빠름.
- 분포: ρ_mean, ρ_CI95, ρ_median, ρ의 다봉성 (Hartigans' dip).

**Bootstrap C — 색상-permutation null**: 기존(`label_perm_p`) 그대로. 비교 baseline.

**HC LOO null distribution**: 각 HC도 CVD처럼 fit 시 (LOO HC mean + held-out HC를 "pseudo-CVD"로) → ρ_HC 7개 → CVD ρ가 이 분포 어디에 위치?

#### 측정 metric

1. ρ_mean, ρ_median, ρ_trimmed20, ρ_mode (KDE peak)
2. ρ_CI95 (percentile, BCa 보조)
3. **ρ_z = (ρ_CVD − mean(ρ_HC_LOO)) / std(ρ_HC_LOO)** ← HC null 보정 핵심
4. CVD–sub10 분리도: |ρ_CVD − ρ_sub10| / ρ_std
5. param 분포: best Δλ / β_s / β_c per LOHO

### 3) 제작 → smoke → main

#### 3-A. Smoke (이번 turn)

- 위치: `scripts/cycle_bootstrap/bootstrap_smoke.py`
- 범위: hV4 ROI, sub-08 + 2개 LOHO HC 제외 case + 2-component 모델 1개
- 검증: precompute_hc_W → simulate_mean_hc_wfixed가 정확히 호출되는지, ρ가 logical range인지
- 출력: stdout 표 + smoke JSON

#### 3-B. Main (sbatch 설계)

- 위치: `scripts/cycle_bootstrap/bootstrap_main.py` + `sbatch/run_bootstrap_main.sbatch`
- 범위: hV4, 3 CVD × 3 model × {7 LOHO + 500 boot} → 4500 fit
- 비용 추정: 1 grid eval ≈ 0.026s, 1326 grid → 34s, 4500 fit → ≈42시간. CPU-heavy → node2 sbatch.
- LOHO만(빠른 변종, 21 fit)은 local에서 실행 가능.

### 4) 결과 비판 검토

#### 4-A. Smoke + LOHO+HC null 결과 (n_boot=0; 시간상 main bootstrap은 sbatch 위임)

| Subject | ROI | Model | all7 ρ | LOHO mean | LOHO std | LOHO range | HC null μ±σ | **z(CVD)** | emp_p |
|---------|-----|-------|:------:|:---------:|:---------:|:----------:|:-----------:|:----------:|:-----:|
| sub-08  | V4  | 2comp | 0.667  | 0.667     | 0.094     | 0.524–0.786 | 0.405±0.324 | **+0.81** | 0.375 |
| sub-08  | V1  | 2comp | 0.833  | 0.813     | 0.065     | 0.690–0.905 | 0.497±0.206 | **+1.64** | 0.125 |
| sub-09  | V4  | 2comp | 0.071  | 0.089     | 0.073     | 0.000–0.214 | 0.442±0.324 | **−1.14** | 0.875 |
| sub-10  | V4  | 2comp | 0.452  | 0.446     | 0.038     | 0.405–0.500 | 0.405±0.332 | **+0.14** | 0.500 |

#### 4-B. 가설 검증

- **H1 검증 — LOHO 변동성**: ✓ 부분적으로. hV4(K=3)에서 sub-08 LOHO std=0.094, range=0.262 → ρ는 ±0.13 변동. **best param은 더 불안정** — drop_01에서 (50, -36), drop_02에서 (0, -50), drop_04에서 (50, -24) → β_s가 0↔50 사이를 점프. V1(K=4 더 안정)에서는 β_s=50 fixed로 stable, β_c만 −28~−50 변동.
- **H2 검증 — CI ↔ FPR 연결**: ✓ **명확히 확인**. hV4 z=+0.81 (sub-08), z=−1.14 (sub-09), z=+0.14 (sub-10) → 세 CVD 모두 HC null 분포 안에 포함. emp_p ≥ 0.375 모두 → **specificity 부재**가 분산 분석으로도 확인됨. MEMORY의 "FPR 100%" 발견(point estimate Δρ baseline 분석)이 ρ-bootstrap 차원에서도 동일한 결론.
- **H3 검증 — Robust estimator의 회복 가능성**: ✗ hV4에서는 회복 불가. mean/median/trimmed20 모두 거의 동일 (0.667/0.690/0.671). LOHO 점들이 단봉 분포 → mode/median 차이 없음. **V1에서는 부분 회복**: z=+1.64 (one-sided p ≈ 0.05), 분산 작음 → V1을 primary specificity ROI 후보로 검토 필요.

#### 4-C. 부수 발견

1. **W-fixed vs shift_at_both 차이가 sub-09 V4에서 결정적**:
   - 보고된 sub-09 V4 ρ=0.690 (shift_at_both)
   - W-fixed에서는 ρ=0.071 (NS)
   - HC null 평균 0.442로 CVD가 그 *아래*에 있음 → V4(K=3, alpha=1.0)에서 W-fixed는 부적합. **ROI별 method 선택은 specificity에도 영향**을 준다.

2. **HC null 분포 자체가 매우 넓음** (std=0.20–0.33):
   - 한 명의 HC sub-02는 V4 pseudo-CVD ρ=0.786 — sub-08 fit ρ=0.667보다 큼.
   - 즉, **HC subject 본연의 LOCO 보간 변동이 CVD signal보다 크다**.
   - baseline_rho 분산 우위(MEMORY: 1-sub baseline ρ ∈ [−0.36, +0.69])와 직접 일치.

3. **sub-10(normal) LOHO 분산이 가장 작음** (std=0.038): 안정성을 specificity 대용으로 사용하면 **sub-10 > sub-08/09**가 되어 false positive 위험. Bayes-style stability-weighted ρ 도입 시 sub-10이 "가장 일관된 신호" 사례가 될 우려 → **단순 안정성 가중은 위험**.

#### 4-D. 모델 선택 기준에 대한 잠정 결론

| 추정량 | hV4 신뢰성 | V1 신뢰성 | 위험 |
|--------|:---------:|:---------:|------|
| mean | 표준 | 표준 | outlier에 끌림 (sub-08 V4 drop_01 case) |
| median | 거의 동일 | 거의 동일 | 단봉 분포 → 차이 없음 |
| trimmed20 | 거의 동일 | 거의 동일 | n=8에서 trim 효과 미미 |
| **HC-null z-score** | **권장** | **권장** | std_HC null 추정 불안정 (n=7) |
| param mode | 불안정 (β jump) | 안정 (V1 β_s=50) | LOHO에서 fitting bimodal 위험 |
| stability-weighted | **위험** | 위험 | sub-10이 가장 안정 — FP 유도 |

**잠정 권장**: ρ point estimate 옆에 **(a) LOHO ρ std·range, (b) HC null z-score, (c) emp_p**를 함께 보고. specificity claim은 z ≥ 2(혹은 emp_p ≤ 0.05)에서만.

#### 4-E. Cycle 2 진입 결정

- **진입**: 예. 다음 cycle 목표:
  1. 현재 LOHO + HC null pipeline에 main bootstrap (n_boot=200) 추가 — sbatch 실행 또는 V1만 local 1시간 실행.
  2. V1을 primary specificity ROI로 가설 설정하고, 3 CVD × 3 model 체계적 평가.
  3. baseline_rho 보정(`Δρ = ρ_fitted − ρ_baseline`) 결합 시 z-score 변동 측정.
  4. parameter mode 분석 — LOHO에서 (Δλ, β_s, β_c) 벡터의 KDE peak이 통합 estimate로 적절한지.
- **전제 점검**: V4가 W-fixed에서는 약하다는 점 → cycle 2에서는 **shift_at_both LOHO**도 1 case 정도 검증해야 (소요 시간이 W-fixed보다 약 10배 — sbatch 필수).

---

## Cycle 1 산출물 (정리)

- **Action plan**: `analysis/future_phase2_filter_optimization/action_plans/02_bootstrap_variance.md`
- **Smoke**: `scripts/cycle_bootstrap/bootstrap_smoke.py` → `results/cycle_bootstrap/smoke/smoke_sub-08_V4_2component.json`
- **Main**: `scripts/cycle_bootstrap/bootstrap_main.py` → `results/cycle_bootstrap/main/sub-{08,09,10}_{V1,V4}_2component.json`
- **Analyzer**: `scripts/cycle_bootstrap/analyze_bootstrap.py` → `results/cycle_bootstrap/summary.json`
- **Plot**: `scripts/cycle_bootstrap/plot_distributions.py` → `results/cycle_bootstrap/rho_distributions.png`
- **SBATCH**: `sbatch/cycle_bootstrap/run_bootstrap_main.sbatch` (9-array, n_boot=200)


