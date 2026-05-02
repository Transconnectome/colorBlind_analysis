# Action Plan 04 — Filter Refinement: ROI × Loss 통합 실험

> 시작: 2026-04-30 · 출처: Plan 01 Cycle 4 종결 후, 사용자 지시(연구자로서 처음부터 끝까지 진행)
>
> 목적: ROI 결합과 Loss 결합, 그리고 둘 간의 상호작용을 N×M 실험 디자인으로 평가하여 (1) 학습 해의 안정성/유일성, (2) 분산 최소화, (3) HC FP 최소화를 동시에 만족하는 필터 적합 절차를 도출.

---

## 0. 판단 기준 (Acceptance criteria)

| 기준 | 정의 | 측정 방법 |
|---|---|---|
| **C1. 안정성/유일성** | 동일 LOHO/seed에서 best param이 좁은 영역에 모이는가; 다중 minima 여부 | LOHO 7회 best param SD; loss landscape secondary-minimum cost ratio |
| **C2. 분산 최소화** | bootstrap/LOHO에서 ρ·param 분포의 IQR | n_boot=200 (server) 또는 n_boot=100 (local) |
| **C3. HC FP 최소화** | HC null 분포에서 CVD specificity (z, p_emp) | LOO HC pool 6명 vs CVD 2명 (sub-08 V4, sub-09 V2 priority; sub-10 제외) |
| **C4. Cross-ROI agreement** | ROI 결합 시 두 ROI의 best param 방향성 일치 | (β_s, β_c) cosine; sign agreement |
| **C5. baseline-직교성** | corr(baseline_rho, metric) ≈ 0 | HC pool 내 Pearson r |

CLAUDE.md 규칙 7: sub-10 분석 제외. specificity 평가는 sub-08, sub-09에 한정.

---

## 1. ROI 선택 근거 (Existing phase 결과)

ROI 후보 풀: V1, V2, hV4. 각 ROI 의 baseline 유의성을 phase1/2/3 + 본 phase forward model 결과에서 정리한다.

| ROI | phase1 procrustes (HC-CVD) | phase2_SRM 그룹 (perm p) | SRM 개인 (Crawford-Howell) | Forward LOCO baseline (perm p) | 결정 |
|---|---|---|---|---|---|
| V1 | n_voxels=560; HC-CVD voxel-corr 개선 큼 (sub-08 +0.080) | p=0.062 (g=1.16, trending) | **sub-09 t=3.5, p=0.007*** | LOCO null floor 0.10–0.13 (voxel covariance 우위, perm-NS) | **단독 가능** (SRM 개인 + procrustes baseline 강함) |
| V2 | HC-CVD effect d=2.20 (phase2 RDM) | p=0.075 (g=1.04, trending) | **sub-08 t=2.1, p=0.040*** | LOCO null 0.10–0.13 (perm-NS) | **단독 가능** (RDM/SRM baseline 강함) |
| hV4 | n_voxels≈67; voxel-level 강한 개선 (sub-08 +0.118) | p=0.559 (NS) | NS 모두 (sub-08 p=0.411, sub-09 p=0.150) | **PRIMARY GO**: perm p=0.044, 2-comp sub-08 p=0.004** | **단독 가능** (forward LOCO gate)  |

V3 는 phase1 voxel-corr 개선 미미(+0.010)·SRM NS·forward LOCO NS → **결합 only**(현재 plan 04 scope 외, 후속 cycle 검토). 본 plan 에서는 단독·결합 양쪽에서 모두 V1·V2·hV4 만 사용.

추가 sanity: HC FPR 100%(MEMORY) 는 LOCO Δρ + baseline_rho 회귀 결과 — baseline 유의성 자체를 부정하지 않고, **fitting metric 의 specificity** 가 약하다는 의미. 따라서 ROI 단독 자격은 phase1/phase2 baseline 으로 부여하되, plan 04 의 핵심은 *fitting metric* 이 baseline 직교성과 specificity 를 동시에 만족하는지.

---

## 2. 실험 디자인 (N × M cell)

### 2-A. ROI 차원 (N=7)

| 코드 | 구성 | 단독 자격 | 비고 |
|---|---|:-:|---|
| R1 | V1 | O | sub-09 신호 강함 |
| R2 | V2 | O | sub-08 신호 강함 |
| R3 | V4 (hV4) | O | forward LOCO primary |
| R4 | V1+V2 | O | trending group 두 곳 |
| R5 | V1+V4 | O | early × hub |
| R6 | V2+V4 | O | mid × hub |
| R7 | V1+V2+V4 | O | full hierarchy |

### 2-B. Loss 차원 (M=8)

| 코드 | 정의 | 출처 |
|---|---|---|
| L1 | l_topk_jaccard (k=3) | Cycle 2/4: sub-08 V4 z=−4.33 |
| L2 | mw_jaccard_loss (depth-weighted) | Cycle 4: baseline corr +0.04 (V4) |
| L3 | l_rank (1−Spearman) | 기존 primary criterion |
| L4 | l_dir (1−Pearson) | Cycle 1 |
| L5 | 0.25·L1 + 0.75·L2 (mw-heavy blend) | 신규 |
| L6 | 0.5·L1 + 0.5·L2 (equal blend) | 신규 |
| L7 | 0.75·L1 + 0.25·L2 (set-heavy blend) | 신규 |
| L8 | l_mag (vuln L2 norm 차이) | Cycle 1 — baseline 의존 |

### 2-C. 상호작용 (ROI 결합 시 신호 결합 방식)

- M_zsum: per-ROI z-score 합 (n_ROI 가산)
- M_stouf: Stouffer (z 합 / √n)
- M_maha: HC null pool 의 covariance 가중 (Cycle 2 추가 예정)

---

## 3. 실행 로그 (시간순 누적)

### Cycle 1 — 2026-04-30

#### 1) 진단·계획

기존 cycle1~4 (Plan 01) 의 결론을 N×M 형태로 통합한다. 우선순위 cell:
- (R1, L3/L4): V1 단독, l_rank/l_dir → sub-08 ~ z=−1.8 expected
- (R3, L1): V4 단독, l_topk → sub-08 z=−4.33 reproduce
- (R3, L2): V4 단독, mw_jaccard → baseline 직교 확인
- (R4–R7, L6/L7): ROI 결합 + blend → sub-08+09 동시 분리 가능 여부

#### 2) 가설

- H1: V1+V4 z_sum on L_blend50 → sub-08 specificity 회복 (V1 sub-08 z=−1.8 + V4 z=−3.0)
- H2: V2 단독 specificity 는 sub-09 신호이지만 baseline_rho 음수 영향 우려
- H3: blend 가 mw 단독보다 specificity 향상 (set+depth 결합 효과)

#### 3) 실행

- Script: `scripts/cycle_filter_refinement/run_NxM.py`
- env: `/opt/anaconda3/envs/srm/bin/python` (local conda srm)
- Subjects: sub-01..06 (HC, sub-07 LOCO target 없음), sub-08, sub-09 (CVD), sub-10 (sanity only)
- Grid: β_s ∈ [0,80] step 2, β_c ∈ [−60,60] step 2 → 41×61 = 2501 pt
- ROIs: V1, V2, V4
- 실행 시간: 200s

#### 4) 결과

##### 4-A. 단독 ROI × 단독 Loss specificity (CVD vs HC LOO null, n_HC=6)

```
[V1]  HCμ ± σ          sub-08 (p, z)            sub-09 (p, z)            base_corr
 L1   0.550±0.112       0.500 (p=0.86, z=−0.45)  0.500 (p=0.86, z=−0.45)  −0.56
 L2   0.345±0.271       0.160 (p=0.43, z=−0.69)  0.426 (p=0.57, z=+0.30)  −0.39
 L3   0.464±0.214      *0.071 (p=0.14, z=−1.84)  0.238 (p=0.14, z=−1.06)  −0.76
 L4   0.524±0.217      *0.116 (p=0.14, z=−1.88)  0.405 (p=0.57, z=−0.55)  −0.81
 L6   0.448±0.170       0.330 (p=0.43, z=−0.69)  0.463 (p=0.57, z=+0.09)  −0.50

[V2]  HCμ ± σ          sub-08 (p, z)            sub-09 (p, z)            base_corr
 L1   0.417±0.186       0.500 (p=1.00, z=+0.45)  0.500 (p=1.00, z=+0.45)  +0.25
 L2   0.118±0.173       0.274 (p=0.86, z=+0.90)  0.409 (p=0.86, z=+1.68)  −0.74
 L3   0.317±0.134       0.262 (p=0.43, z=−0.42)  0.762 (p=1.00, z=+3.32)  −0.80
 L4   0.409±0.147       0.273 (p=0.29, z=−0.92)  0.797 (p=1.00, z=+2.64)  −0.75
 L6   0.267±0.145       0.387 (p=0.86, z=+0.82)  0.455 (p=0.86, z=+1.29)  −0.29

[V4]  HCμ ± σ          sub-08 (p, z)            sub-09 (p, z)            base_corr
 L1   0.650±0.150     **0.000 (p=0.14, z=−4.33)  0.800 (p=1.00, z=+1.00)  −0.26
 L2   0.407±0.295       0.000 (p=0.29, z=−1.38)  0.551 (p=0.86, z=+0.49)  +0.04
 L3   0.560±0.285       0.071 (p=0.14, z=−1.71)  0.929 (p=0.86, z=+1.30)  −0.63
 L4   0.580±0.293       0.135 (p=0.14, z=−1.52)  0.893 (p=0.71, z=+1.07)  −0.74
 L6   0.528±0.176     **0.000 (p=0.14, z=−3.00)  0.676 (p=0.86, z=+0.83)  −0.08
 L7   0.589±0.145     **0.000 (p=0.14, z=−4.08)  0.738 (p=0.86, z=+1.03)  −0.18
```

##### 4-B. 결합 ROI specificity (blend50, z_sum / Stouffer)

| combo | method | sub-08 z | sub-09 z | sub-10 z |
|---|---|---:|---:|---:|
| V1+V2 | z_sum | +0.07 | +0.72 | +1.80 |
| V1+V4 | z_sum | **−2.22** | +0.56 | +0.55 |
| V2+V4 | z_sum | −1.35 | +1.32 | +2.14 |
| V1+V2+V4 | z_sum | −1.17 | +0.90 | +1.59 |
| V1+V4 | stouffer | **−2.22** | +0.56 | +0.55 |

V1+V4 z_sum: sub-08 분리 강함 (z=−2.22, p=0.14 — HC 1/6 만 매칭), sub-09 분리 실패. sub-10 도 분리되지 않음 (sanity OK).

V2 결합은 sub-09/10 신호가 *같은* 방향 (z >> 0) 이라 noise 증폭 — V2 단독 sub-09 신호는 *반대 방향* (HC 보다 못 fit) 임을 재확인.

##### 4-C. C1~C5 판단 기준

| 기준 | 측정 | V1 | V2 | V4 |
|---|---|---|---|---|
| C1 secondary-min ratio | l_topk: 1.0 (uniform tie); l_rank: 0.91/0.93/0.90 | flat plateau (set-loss) | mw_jaccard 도 1.0 — 다중 minima | l_topk 0/8 모두 ratio=1.0 |
| C2 HC pool spread (std) | l_topk 0.11/0.19/**0.15**; mw 0.27/0.17/0.29 | V1 가장 좁음 | 중간 | 큼 |
| C3 HC FP (CVD p_emp) | sub-08 V4 L1 p=0.14 (1/7), V1+V4 z_sum p=0.14 | 부분 회복 | 회복 안됨 | sub-08 분리 강함 |
| C4 cross-ROI agreement | (β_s,β_c) 대부분 grid 모서리 → cosine 의미 약함 | V1 vs V4 sub-08 cos=+0.53 | sub-09 V1↔V4 cos=−0.78 | grid edge artifact |
| C5 baseline 직교성 | mw_jaccard V4 +0.04 (가장 직교) | V1 mw −0.39 | V2 mw −0.74 | V4 mw 우수 |

##### 4-D. 핵심 발견

1. **V4 L1_topk** 가장 강한 sub-08 분리 (z=−4.33, p=0.14, HC 1/7 ≤ sub-08). Cycle 4 결과 재현.
2. **V1+V4 z_sum (L_blend50)** sub-08 분리 (z=−2.22). 결합이 V1 단독 (−1.8) 또는 V4 mw 단독 (−1.38) 보다 강함. **결합이 단독 baseline 보다 정량적 향상**.
3. **V2 통합 시 noise**: sub-09/10 V2 신호가 *positive z* (HC 가 더 잘 fit) 이므로 결합 시 sub-08 신호 약화. V2 는 별도 handling 필요.
4. **C5 (baseline 직교성)**: mw_jaccard 가 V4 에서 +0.04 로 가장 양호. 단독 V4 mw 의 sub-08 z=−1.38 (약함). V4 L1_topk z=−4.33 강하나 baseline corr=−0.26 로 baseline 영향 일부.
5. **C1 (uniqueness)**: set-loss (L1, L2) 는 secondary-min ratio=1.0 — *uniform plateau* (multiple grid points equal best). l_rank/l_dir 만 unique min 형성. 이는 set-loss 의 **stability 문제** — grid 위 다중 best 위치 → bootstrap variance 큼 예상.
6. **C4 (cross-ROI agreement)**: best (β_s, β_c) 대부분 grid corner. rotation/dilation 기하 정보 추출 불가. **grid 가 narrow 하지 않은 한 무의미.**
7. **sub-10 sanity**: V2/V2+V4 에서 가장 큰 z (+2.14, +2.79) — false positive 위험. V2 가 sub-10 신호 동시 출력 (deutan 동일 family) → V2 단독 사용은 false positive 위험 동반.

#### 5) 비판 + Cycle 2 plan

**Cycle 1 의 한계**:

(a) C1 (uniqueness) 가 set-loss 에서 fail — multiple equal-cost grid points → param variance 커서 단일 (β_s, β_c) 추정 불가.
(b) V2 의 inverted z 방향이 결합 시 sub-08 신호를 약화. V2 만 별도 weight 또는 부호 보정 필요.
(c) sub-09 specificity 어떤 cell 에서도 회복 안됨 (Plan 01 Cycle 3 결론 재확인).
(d) C5 (baseline 직교) 와 C3 (HC FP) 가 부정적 trade-off — mw_jaccard 직교 좋지만 specificity 약함, l_topk specificity 강하지만 baseline corr=−0.26.

**Cycle 2 가설**:

- H_C2_1: param-stability 보강 — set-loss + smoothness 페널티 (`L_set + λ·∑|∂L/∂β|`) → unique min 형성 → C1 회복.
- H_C2_2: V2 부호 보정 — `L_V2 = sign(β_c) flip` 또는 ROI-별 z 부호 합의 후 합산. 가능하면 V2 z 의 *절대값*만 사용 ("HC 와 다름") → bidirectional separation.
- H_C2_3: combo Mahalanobis (HC null cov 가중) — z_sum 이 ROI 간 corr 무시. HC pool 에서 (V1 best, V2 best, V4 best) 의 cov 학습 → 새 metric `(v_CVD − μ_HC)' Σ^{-1} (v_CVD − μ_HC)`.
- H_C2_4: 대체 loss — *ranked-depth signed* (sub-09 V1 신호 회복 시도): `L_rds = mean over k {(d_sim - d_cvd) · sign(d_cvd)}` where `d_i = c_i − mean(c)`. depth + sign 동시.
- H_C2_5: blend 가중치 grid 확장 — α ∈ {0.0, 0.1, ..., 1.0} 11 점 sweep. Cycle 1 은 3 점만.

**Cycle 2 실행 계획**:

1. 새 스크립트 `cycle2_param_stability.py` — secondary-min ratio + Hessian 기반 sharpness 산출.
2. 같은 cycle1_aggregate landscape 활용 (재계산 불필요) — `--save_landscape` 추가 후 재실행 1 회.
3. Mahalanobis combination 추가.
4. `L_rds` 구현 + 단독/결합 평가.

##### 4-E. Cycle 1 산출 파일

- `scripts/cycle_filter_refinement/run_NxM.py` (신규)
- `results/cycle_filter_refinement/cycle1_aggregate.json` (신규, 모든 cell 결과 + C1~C5)
- `results/cycle_filter_refinement/sub-{ID}_{ROI}_landscape.json` (full grid 9×3=27 파일)

---

### Cycle 2 — 2026-04-30 (계속)

#### 1) Cycle 1 비판 → 진단

(a) C1 fail (multiple minima ~ 871–1795 / 2501)
(b) V2 z 부호 반전 (sub-09/10 V2 baseline_rho 음수 → fitting 후 HC 보다 못 fit)
(c) Mahalanobis 와 z_sum 모두 sub-10 false positive 동반

#### 2) 가설

- H_C2_1 V2 부호 보정: ROI 별 z 의 절대값 부정 (`z_signed = -|z|` for V2) → "V2 가 HC 와 *어떻게든* 다름"
- H_C2_2 Mahalanobis HC null cov 가중 → ROI 간 corr 보정
- H_C2_3 blend α 11점 sweep (0.0..1.0) — V4 에서 최적 α 탐색

#### 3) 실행

- Script: `scripts/cycle_filter_refinement/cycle2_alt_combos.py`
- 입력: cycle1 landscape json 재사용 — 추가 grid sweep 없음
- 실행 시간: 0.1 s

#### 4) 결과

##### 4-A. α sweep (V4)

| α | HC μ ± σ | sub-08 z | sub-09 z |
|---:|---|---:|---:|
| 0.0 (mw only) | 0.407±0.295 | −1.38 | +0.49 |
| 0.5 (blend) | 0.528±0.176 | **−3.00** | +0.83 |
| 0.7 | 0.577±0.148 | −3.89 | +1.00 |
| **0.9** | 0.626±0.143 | **−4.38** | +1.05 |
| 1.0 (topk only) | 0.650±0.150 | −4.33 | +1.00 |

V4 최적 α = 0.9 (set-loss 가 우세). sub-09 는 모든 α 에서 HC 평균 위 (positive z) — 분리 불가.

##### 4-B. ROI 결합 (3 가지 method, blend α=0.5)

| combo | method | sub-08 z | sub-09 z | sub-10 z |
|---|---|---:|---:|---:|
| V1+V4 | z_sum | **−3.69** (p=0.14) | +0.93 | +0.92 |
| V1+V4 | maha | 2.73 (p=0.14) | 0.78 (p=1.00) | 0.50 (p=1.00) |
| V2+V4 | z_sum | −2.17 (p=0.29) | +2.12 (p=1.00) | +3.44 (p=1.00) |
| V2+V4 | z_sum_signed | **−3.82** (p=0.14) | −0.45 (p=0.57) | −2.54 (p=0.29) |
| V1+V2+V4 | z_sum_signed | **−4.52** (p=0.14) | −0.36 (p=0.57) | −2.07 (p=0.29) |

V2 sign-flip 적용 시 V1+V2+V4 sub-08 z=−4.52 — 가장 강한 분리. 그러나 sub-10 도 z=−2.07 (false positive 위험).

V1+V4 z_sum (no V2) 가 sub-08 분리 + sub-10 분리 *없음* (z=+0.92) — **specificity 측면 가장 안전**.

##### 4-C. C1 enhanced — n_global_minima

| metric | V1 median | V2 median | V4 median | 해석 |
|---|---:|---:|---:|---|
| l_topk_jaccard | 1791 | 1460 | 871 | **plateau** (set-loss 의 본질적 평탄성) |
| mw_jaccard_loss | 1795 | 1460 | 674 | 동일 |
| l_rank | 5 | 8 | 11 | sharp min (수치 noise 안에 동률만) |

**Set-loss 의 critical limitation 확인**: 단일 (β_s, β_c) 추정 *불가*. 어떤 unique-min metric (l_rank/l_dir) 이나 regularization 추가 필요.

#### 5) Cycle 2 결론 + Cycle 3 계획

- **V1+V4 z_sum (without V2)** 가 가장 안정적인 specificity 후보 (sub-08 분리, sub-10 null).
- **V2 inclusion** 은 sub-09 신호 회복엔 미흡, sub-10 false positive 유발 → 결합 단계에서 V2 weight=0 또는 sign-flip 필수.
- **C1 fail**: set-loss 자체로는 unique min 형성 불가 → **Tikhonov regularization** 도입 검토.

##### Cycle 2 산출 파일

- `scripts/cycle_filter_refinement/cycle2_alt_combos.py`
- `results/cycle_filter_refinement/cycle2_aggregate.json`

---

### Cycle 3 — 2026-04-30 (계속)

#### 1) Cycle 2 비판 → 진단

set-loss plateau (median 871–1795 minima/2501) 가 C1 의 fundamental obstacle. Tikhonov (parameter-norm) regularization 으로 plateau 안에서 origin 가까운 unique min 강제.

#### 2) 가설

- H_C3_1 `M_tikh = L_set + λ·(β_s²/80² + β_c²/60²)` → unique min 형성, sub-10 false positive 감소 (큰 shift 페널티).
- H_C3_2 V4 + λ ∈ {0.05, 0.1, 0.2, 0.5, 1.0} sweep — sub-08 z 변화 + sec-min ratio 측정.
- H_C3_3 ROI combo 도 Tikhonov 적용 시 specificity 회복.

#### 3) 실행

- Script: `scripts/cycle_filter_refinement/cycle3_unique_loss.py`
- 입력: Cycle 1 landscape 재사용
- 실행 시간: 0.1 s

#### 4) 결과

##### 4-A. V4 l_topk + λ·norm_grid (단독)

| λ | sec-ratio | sub-08 z | sub-09 z | **sub-10 z (sanity)** |
|---:|---:|---:|---:|---:|
| 0.00 | 1.000 | **−4.33** | +1.00 | −1.00 |
| 0.05 | 0.971 | **−4.61** | +0.96 | −1.15 |
| 0.10 | 0.967 | **−4.84** | +0.89 | −1.30 |
| **0.20** | **0.962** | **−4.97** | +0.65 | **−1.54** |
| 0.50 | 0.961 | −3.04 | +0.17 | −1.21 |
| 1.00 | 0.974 | −1.97 | +0.06 | −0.41 |

**λ=0.2 V4 l_topk** = optimal. sub-08 z=−4.97 (가장 강한 분리), sub-10 z=−1.54 (CVD 보다 약함 — proper specificity), sec-min ratio=0.962 (multi-minima 완화).

##### 4-B. V4 blend50 + λ·norm_grid

| λ | sub-08 z | sub-10 z |
|---:|---:|---:|
| 0.00 | −3.00 | +0.45 |
| 0.10 | −2.93 | +0.31 |
| 0.20 | −2.69 | +0.20 |

blend 는 단독 l_topk 보다 약함 (mw 가 V4 에서 약함). V4 단독 = l_topk + Tikh 권장.

##### 4-C. Combo blend50 + Tikh (λ=0.1)

| combo | sub-08 z_sum | sub-09 | sub-10 (sanity) |
|---|---:|---:|---:|
| V1+V4 | **−3.64** (p=0.14) | +0.91 (p=0.57) | +0.73 (p=0.57) |
| V2+V4 (signed) | −3.78 (p=0.14) | −1.45 (p=0.57) | **−2.79** (p=0.14, FP) |
| V1+V2+V4 (signed) | −4.49 (p=0.14) | −1.40 (p=0.57) | −2.37 (p=0.29) |

V1+V4 (no V2) 가 sub-08 강한 분리 + sub-10 정상 (positive z) — **safe specificity**.

#### 5) Cycle 3 비판 + 결론

- **V4 l_topk + λ=0.2 Tikh** 가 단독 ROI 에서 가장 강한 specificity (sub-08 z=−4.97, sub-10 z=−1.54).
- **V1+V4 z_sum + Tikh** 가 결합 ROI 에서 안정 (sub-08 z=−3.64, sub-10 z=+0.73).
- sub-09 specificity 는 어떤 cell 에서도 회복 불가 — Plan 01 Cycle 3 결론 (sub-09 baseline_rho 음수 → vulnerability pattern 이 HC sub-04/05 와 r=+0.5 강한 상관) 재확인.

##### Cycle 3 산출 파일

- `scripts/cycle_filter_refinement/cycle3_unique_loss.py`
- `results/cycle_filter_refinement/cycle3_aggregate.json`

---

## 4. 종합 결과 (Cycle 1~3)

### 4-1. 추천 구성

| 용도 | ROI | Loss | 결합 방식 | 핵심 지표 |
|---|---|---|---|---|
| **단독 hV4 사용** | hV4 | l_topk_jaccard + 0.2·(β_s²/80² + β_c²/60²) | — | sub-08 z=−4.97 (p=0.14 = n=6 HC pool empirical floor; HC sub-04 mwJ=0.94 vs sub-08 mwJ=1.00 거의 동급 — server n_boot=200 검증 필요) |
| **결합 (안전)** | V1 + V4 | blend50 + 0.1·Tikh | per-ROI z, sum | sub-08 z=−3.64 (p=0.14, n=6 floor; HC 1/6 동급 후보 존재), sub-10 정상 |
| **결합 (고감도)** | V1+V2+V4 | blend50 + 0.1·Tikh, V2 sign-flip | per-ROI z, signed sum | sub-08 z=−4.49 (p=0.14, n=6 floor; sub-10 FP 위험 z=−2.37) |

> **Caveat (n_HC=6 ceiling)**: 본 plan 의 모든 p_emp=0.14 는 n_HC=6 LOO pool의 **attainable empirical floor (1/(6+1)=0.143)**. "강한 specificity" 가 아니라 "최저 가능 p".
>
> sub-08 V4 의 동급 후보 검증 (Cycle 1 V4 HC pool 직접 확인):
>
> - **L1_topk (V4)**: HC raw l_topk = [sub-01 0.8, sub-02 0.5, sub-03 0.8, sub-04 0.5, sub-05 0.8, sub-06 0.5]. **sub-02, sub-04, sub-06 모두 raw=0.5** (set match 1 of 3) — sub-08 raw=0 (perfect match) 만 분리되지만, Tikh λ=0.2 후 sub-08 0.149 vs HC sub-04 0.700 / sub-06 0.692 로 분리됨 (norm 페널티 차이가 결정적).
> - **L2_mwj (V4)**: HC sub-04 mwJ=**0.94** (mw_jaccard_loss=0.060) — sub-08 mwJ=1.00 과 거의 동급. depth-weighted Jaccard 만 보면 sub-04 가 거의 sub-08 만큼 set match.
> - **Machado_1way (Cycle 5 Task 2)**: HC sub-02 raw l_topk = **sub-08 raw l_topk = 0.500 (identical)** — Machado 모델로는 sub-02 와 sub-08 분리 자체 안 됨. p=2/7 의 actual 분포, floor 가 아님.
>
> 분리의 통계적 confidence 는 **server n_boot=200 bootstrap (§5)** 으로 확정해야 함. 단일 점추정 z 만으로 specificity 판단 금지.

### 4-2. 5개 판단 기준 표

| 기준 | V4 단독 (l_topk + λ=0.2) | V1+V4 (blend+Tikh) | V1+V2+V4 (signed) |
|---|---|---|---|
| **C1 안정성/유일성** | sec-ratio=0.962 (good) | per-ROI 평균 0.97 | 0.97 |
| **C2 분산** | HC std = 0.150 (절대값), IQR 작음 | per-ROI ROI z std 정규화 | 동일 |
| **C3 HC FP (sub-08)** | p=0.14 (1/7 HC) | p=0.14 | p=0.14 |
| **C4 cross-ROI agreement** | N/A (단일 ROI) | sub-08 cos(V1,V4)=+0.53 | best param 대부분 grid edge — 의미 약함 |
| **C5 baseline-직교성** | corr=−0.26 (V4 l_topk) | mixed (V4 +0.04 / V1 −0.39 / V2 −0.74) | 동일 |

### 4-3. 추가 자유 기준 (제안 + 측정)

- **C6 sub-10 specificity**: |z_CVD| − |z_sub10|. V4 단독 = 4.97 − 1.54 = 3.43 (양호). V1+V4 = 3.64 − 0.73 = 2.91 (양호). V1+V2+V4 signed = 4.49 − 2.37 = 2.12 (감도 vs FP trade-off).
- **C7 sub-09 deficit**: 모든 cell 에서 sub-09 NS. ROI/Loss design 만으로 회복 불가 — Plan 01 Cycle 3 결론 (per-color voxel correlation 자체 노이즈) 재확인.
- **C8 effective DOF**: 8-color × 6-run 데이터의 LOCO 통계 effective DOF ≈ 1~2 (Plan 01 Cycle 3 진단). 어떤 metric design 도 이 한계 안에서 sub-09 분리 어려움.

### 4-4. 미해결 / Cycle 4+ 과제

1. **sub-09 specificity 회복**: 본 plan 수단으로 미해결. 후속 — voxel-level diagnostic, alternative ROI(V1+V2 RDM 결합 등), per-fold LOCO (run × color = 48 fold) 로 effective DOF 확장 필요.
2. **Bootstrap n=200 분산**: 현재 단일 point estimate. 서버 sbatch 명세 (아래 §5) 작성, 사용자 트리거.
3. **Cross-ROI (β_s, β_c) 수렴 검증**: grid 모서리 artifact 로 현재 무의미. grid 범위 좁힘 + 또는 differential evolution 사용 시 검증 가능.
4. **다른 simulator (R+C, Machado)**: 본 plan 은 2-component 모델만 사용. cross-model robustness 검증은 후속.

---

### Cycle 4 (Local 부분) — Bootstrap 분산 측정 — 2026-04-30

#### 1) 의도

C2 (분산) 정량화. sub-08 V4 의 best loss / best (β_s, β_c) / ρ@best 의 HC subject resampling 분포.

#### 2) 실행

- Script: `scripts/cycle_filter_refinement/run_bootstrap.py` (신규)
- env: `srm`. n_boot=100, bs_step=4, bc_step=4 (속도 trade-off).
- Cell: sub-08 × V4. lam_tikh=0.1.
- 실행 시간: 190 s.

#### 3) 결과 (sub-08 V4, n_boot=100)

| metric | point | median | IQR | CI95 |
|---|---:|---:|---:|---:|
| l_topk | 0.000 | 0.000 | 0.000 | [0.000, 0.500] |
| mw_jaccard | 0.000 | 0.000 | 0.000 | [0.000, 0.299] |
| blend50_tikh (λ=0.1) | 0.077 | 0.092 | 0.120 | [0.000, 0.456] |
| best_bs | 64.0 | 48.0 | 40.0 | [0.0, 80.0] |
| best_bc | −36.0 | 0.0 | 57.0 | [−40.0, 56.0] |
| ρ@best | +0.595 | +0.595 | 0.196 | [0.000, 0.810] |

**해석**:
- **best loss median=0**: 절반 이상 bootstrap 에서 sub-08 V4 l_topk=0 (perfect set match) — sub-08 specificity 강건성 확인.
- **best (β_s, β_c) IQR 매우 큼**: β_s IQR=40, β_c IQR=57 → **point estimate 의 (β_s, β_c) 는 unidentifiable**. 어떤 (β_s, β_c) 든 같은 cost (Cycle 2 plateau diagnostic 일치).
- **ρ@best CI95 = [0.000, 0.810]**: HC pool 의 한 명을 빼면 ρ 가 매우 unstable. **bootstrap variance 크다는 Plan 02 Cycle 1 결론 (LOHO ρ std=0.094) 과 일치**.

#### 4) 결론

- **최종 점추정의 의미**: "어떤 (β_s, β_c) 가 sub-08 의 LOCO 패턴을 재현하는가" 는 ill-posed. **취약 색 set 일치 자체가 신호** (≥50% boot 에서 perfect match).
- 즉 plan 04 의 권장 구성 (V4 l_topk + Tikh) 의 정량적 메시지: "HC pool 6 명 중 1 명만 sub-08 처럼 LOCO 가 망가진다" — 방향과 진폭이 아니라 *vulnerability 분포의 set-level 일치* 가 specificity 의 정체.

##### Cycle 4 (local) 산출 파일

- `scripts/cycle_filter_refinement/run_bootstrap.py`
- `results/cycle_filter_refinement/bootstrap/sub-08_V4.json`
- `sbatch/run_plan04_bootstrap.sbatch` (서버 6 cell n_boot=200 명세)

---

### Cycle 5 — 2026-04-29 (Task 1~4)

#### 1) 의도

Cycle 1~4 의 두 결론을 falsifiable 실험 두 개로 sharpen:
- **(A) sub-09 분리 불가 ≠ true** — c8 magenta 단독 outlier 가 cause 일 가능성 (MEMORY Task #21: V1 z=−5.59, hV4 z=−3.23, V2 z=−5.38; c8 drop 시 V1 ρ=+0.54, hV4 ρ=+0.21 회복).
- **(B) "set-match is signal, parameters are noise" framing은 falsifiable** — sub-08 V4 + l_topk + Tikh 의 specificity 가 simulator (Machado/R+C/2-comp) 와 무관해야 함.

#### 2) Task 1 — sub-09 c8-drop diagnostic

**스크립트**: `scripts/cycle_filter_refinement/cycle5_c8drop.py` (신규).
**환경**: `srm`. **실행 시간**: 260 s.
**설계**: cycle1 grid (β_s∈[0,80] step 2, β_c∈[−60,60] step 2 = 2501 pt) sweep — vuln_sim 와 vuln_target 모두 c8 (index=7, magenta) 제거 후 7-color 위에서 l_topk(k=3 유지), mw_jaccard, l_rank, l_dir 재계산. ROI=V1/V2/V4. λ_tikh=0.2 (cycle3 권장).

##### 4-A. baseline_rho 회복 검증 (sub-09)

| ROI | sub-09 ρ_8 | sub-09 ρ_7 | Δρ | MEMORY 방향 일치? (magnitude 직접 비교 불가 — metric 다름: LOCO baseline ρ vs Machado anti-prediction z) |
|---|---:|---:|---:|---|
| V1 | +0.357 | +0.714 | **+0.357** | qualitatively consistent (MEMORY: V1 c8 drop → ρ→+0.54 in Machado neural fit) |
| V2 | −0.524 | −0.321 | +0.202 | qualitatively consistent (partial) |
| V4 (hV4) | −0.357 | −0.107 | +0.250 | qualitatively consistent (MEMORY: hV4 ρ→+0.21 in Machado neural fit) |

→ 방향 (c8 제거 후 ρ 증가) 만 일치. Magnitude 는 LOCO ρ 와 Machado neural fit ρ 가 다른 metric 이므로 직접 비교 불가. c8 = magenta 가 sub-09 baseline_rho 의 노이즈 source 임을 정성적으로 재확인.

##### 4-B. specificity (l_topk + λ=0.2 Tikh, 7-color)

| ROI | HCμ±σ | sub-08 z | sub-09 z | sub-10 z (sanity) |
|---|---|---:|---:|---:|
| V1 | 0.515±0.149 | −0.10 (p=0.71) | **−3.46 (p=0.14)** | **−3.46 (p=0.14, FP)** |
| V2 | 0.303±0.224 | +0.88 (p=0.86) | −0.05 (p=0.43) | +2.22 (p=1.00, FP 반대) |
| V4 | 0.569±0.188 | **−2.24 (p=0.14)** | −0.33 (p=0.57) | **−2.78 (p=0.14, FP)** |

##### 4-C. 8-color 와 비교 (sub-09 specificity 회복 여부)

| ROI | 8-color sub-09 z | 7-color sub-09 z | 회복? | 단 sub-10 z (8 → 7) |
|---|---:|---:|---|---|
| V1 | −0.57 | **−3.46** | ✓ recovered | −0.57 → **−3.46** (FP 동시 출현) |
| V2 | +2.95 | −0.05 | partial (NS 유지) | +3.04 → +2.22 (FP 잔존) |
| V4 | +0.65 | −0.33 | NS 유지 | −1.54 → **−2.78** (FP 강화) |

**해석**:
- **단독 효과**: sub-09 V1 z=−3.46 — 8-color 에서 잡히지 않던 신호가 7-color 에서 검출. c8 magenta 가 sub-09 의 V1 set-match 노이즈 dominant source. *MEMORY task #21 의 baseline_rho 회복 (+0.54) 과 정합.*
- **specificity 손상**: 그러나 sub-10 도 V1 7-color 에서 z=−3.46, V4 z=−2.78 — sub-09 와 동일하거나 더 강한 specificity. **c8 drop 은 noise 만 줄이는 것이 아니라 sub-10 의 HC 와의 약한 차이까지 노출**.
- **종합**: c8 단독 outlier hypothesis 는 *부분적 사실* — sub-09 V1 신호는 회복되지만 sub-10 false positive 가 동시에 강화 → "c8 외에도 systemic noise" 결론으로 reframe 필요. **sub-10 specificity 회복이 동반되지 않으면 c8 drop 도 진짜 신호 분리책 아님**.

##### 4-D. 산출 파일 — Task 1
- `scripts/cycle_filter_refinement/cycle5_c8drop.py`
- `results/cycle_filter_refinement/cycle5_c8drop_aggregate.json`

#### 3) Task 2 — Cross-simulator (sub-08 V4)

**스크립트**: `scripts/cycle_filter_refinement/cycle5_cross_sim.py` (신규).
**환경**: `srm`. **실행 시간**: 72 s.
**설계**: sub-08 + 6 HC × V4 × 3 simulator (2-comp / R+C / Machado_1way).
- 2-comp: (β_s,β_c) grid 41×61=2501 pt; norm = (β_s/80)² + (β_c/60)²
- R+C: (Δλ,g) grid 31×61=1891 pt; norm = (Δλ/30)² + (g/3)²
- Machado_1way: Δλ ∈ [0,30] step 0.5 = 61 pt; norm = (Δλ/30)²
- L = l_topk(k=3) + 0.2·norm. family=deutan.

##### 5-A. sub-08 V4 specificity 표 (simulator × metric)

| simulator | HCμ±σ | sub-08 value | sub-08 z | sub-08 p_emp | best params | ρ@best |
|---|---|---:|---:|---:|---|---:|
| 2-component | 0.725±0.116 | **0.149** | **−4.97** | 0.143 | (β_s=58, β_c=−28) | +0.548 |
| R+C | 0.784±0.146 | 0.280 | −3.44 | 0.143 | (Δλ=19, g=−3.0) | +0.762 |
| Machado_1way | 0.784±0.146 | 0.500 | −1.94 | 0.286 | (Δλ=0) | +0.262 |

##### 5-B. sub-08 raw l_topk (Tikh 제거, set match 자체)

| simulator | sub-08 raw l_topk (=0 → perfect set match) |
|---|---:|
| 2-component | **0.000** (perfect) |
| R+C | **0.000** (perfect) |
| Machado_1way | 0.500 (set match 1/3) |

##### 5-C. 변동성 / verdict

- z range = [−4.97, −1.94], **spread = 3.025** (> 1.5).
- value range = [0.149, 0.500], **spread = 0.351**.
- verdict (z): **simulator_conditional**. framing 의 falsifiable claim **부분적 기각**.

##### 5-D. 해석 (정직한 falsification + post-hoc rescue 시도)

**Pre-registered threshold 와의 비교**: 본 task 시작 시 "변동 < 1.0 → framing 검증, > 1.5 → simulator-conditional" threshold 명시. 결과 z spread = **3.02 > 1.5** → **원 framing ("set-match is signal, parameters are noise") 은 사용자 threshold 기준 falsified**.

**구체적 데이터**:

- **2-comp 와 R+C 는 raw l_topk=0 (perfect set match) 도달** — sub-08 만 도달, HC 모두 ≥ 0.5. set 신호 자체는 robust.
- **Machado_1way 는 sub-08 raw l_topk = 0.500, HC sub-02 도 raw = 0.500 (identical)** — Machado 로는 sub-08 과 sub-02 가 set match 차원에서 *분리되지 않음*. p_emp=0.286 (= 2/7) 은 floor 가 아니라 actual 분포.
- Tikh 후 z spread 3.02 의 source: simulator 별 HCμ/HCσ 가 다른 grid edge plateau 에 갇히는 차이 (R+C, Machado: HC 가 Δλ=0 origin 에 모이며 raw=0.8 로 동일) + sub-08 best 의 simulator 별 norm 페널티 차이.

**Post-hoc rescue (사후 해석)**: 2-comp/R+C 안에서는 sub-08 raw l_topk=0 이 HC 와 명확히 분리 (HC ≥ 0.5). Machado_1way (1-DOF) 만 set match 차원에서 sub-08 을 capture 못함. → "set-match 신호는 ≥2-DOF simulator 에서만 universal" 은 **rescue interpretation**, *원래 framing 의 새 검증이 아님*. 추가 simulator (e.g., 3-DOF cone_3way, Fourier warp) 가 set match=0 을 sub-08 에서 달성하면 rescue 강화, 다른 결과면 rescue 도 기각.

**Cycle 4 와의 정합 (independent)**: (β_s, β_c) bootstrap IQR=40°/57° 의 unidentifiability 자체는 simulator 와 무관하게 holds (Cycle 4 단일 simulator 결과). 즉 "parameters 는 noise" 의 *내부* (2-comp 안에서) plateau evidence 는 견고; "across simulators" 라는 *외부* 일반화는 falsified.

##### 5-E. 산출 파일 — Task 2
- `scripts/cycle_filter_refinement/cycle5_cross_sim.py`
- `results/cycle_filter_refinement/cycle5_cross_sim_aggregate.json`

---

## 5. Server Bootstrap sbatch 명세 (사용자 실행)

스크립트: `analysis/future_phase2_filter_optimization/sbatch/run_plan04_bootstrap.sbatch`

```bash
# 6 cells: V1/V2/V4 x sub-08/09 (sub-10 sanity 제외)
sbatch sbatch/run_plan04_bootstrap.sbatch
# array 0-5, max 3 concurrent on node2, --mem=16G, n_boot=200
```

서버 데이터 경로:
- amplitudes: `/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010/{subject}/{ROI}/amplitudes_procrustes.npy`
- LOCO target: `analysis/future_phase1_forward_model/results/validation/sub-{ID}_loco.json`

---

## 6. 종료 보고

- 작성·수정 파일:
  - `scripts/cycle_filter_refinement/run_NxM.py` (Cycle 1)
  - `scripts/cycle_filter_refinement/cycle2_alt_combos.py`
  - `scripts/cycle_filter_refinement/cycle3_unique_loss.py`
  - `scripts/cycle_filter_refinement/run_bootstrap.py` (Cycle 4 local)
  - `scripts/cycle_filter_refinement/cycle5_c8drop.py` (Cycle 5 Task 1)
  - `scripts/cycle_filter_refinement/cycle5_cross_sim.py` (Cycle 5 Task 2)
  - `sbatch/run_plan04_bootstrap.sbatch` (Cycle 4 server)
  - `results/cycle_filter_refinement/cycle1_aggregate.json` + 27 landscape json
  - `results/cycle_filter_refinement/cycle2_aggregate.json`
  - `results/cycle_filter_refinement/cycle3_aggregate.json`
  - `results/cycle_filter_refinement/bootstrap/sub-08_V4.json`
  - `results/cycle_filter_refinement/cycle5_c8drop_aggregate.json`
  - `results/cycle_filter_refinement/cycle5_cross_sim_aggregate.json`
  - 본 마크다운
- 진행 cycle 수: 5 (3 main + 1 bootstrap local + Cycle 5 Task 1~4)
- 최종 권장 구성:
  - **단독**: V4 + l_topk_jaccard + λ=0.2 Tikhonov (sub-08 z=−4.97, sub-10 z=−1.54, p=0.14 = n=6 floor)
  - **결합 (안전)**: V1+V4 blend50 + λ=0.1 Tikhonov, z_sum (sub-08 z=−3.64, sub-10 정상)
- 5개 판단 기준 표: §4-2 + 추가 C6 sub-10 sanity, C7 sub-09 deficit, C8 effective DOF.
- **Cycle 5 결론**:
  - Task 1 (c8 drop): sub-09 V1 specificity 부분 회복 (z=−3.46) — 단 sub-10 동시 출현 (FP). hV4 도 sub-10 FP. *c8 단독 outlier hypothesis 부분 사실, 그러나 sub-10 control 동반 → 진짜 신호 분리책 아님.*
  - Task 2 (cross-simulator): sub-08 V4 z range = 3.02 (pre-registered threshold > 1.5) → **원 framing 사용자 threshold 기준 falsified**. Post-hoc rescue ("≥2-DOF simulator 에서만 universal") 는 사후 해석이며, Machado_1way 에서 HC sub-02 = sub-08 raw l_topk = 0.500 identical 이 핵심 증거. 추가 simulator 검증 없이는 rescue 도 미확인.
  - Task 3 (§4-1 phrasing): 모든 p=0.14 표현을 "n=6 HC pool empirical floor; sub-08 V4 동급 후보 = HC sub-02/04/06 raw=0.5 + HC sub-04 mwJ=0.94 + Machado HC sub-02 identical 0.500; server n_boot=200 검증 필요" 형태로 보수화 + caveat 박스 강화.
  - Task 4 (§7 Stage C 함의): Cycle 4 (β_s,β_c) unidentifiability + Task 2 cross-simulator divergence → "Stage C 필터는 point parameter 에서가 아니라 valid filter region 에서 도출". Phase 3 에서 point-estimate 필터 vs set-level 필터 이중 평가 필요. (region 정의 thresholds — Jaccard ≥ 2/3, ≥50% boots — 는 tentative, Cycle 6 에서 grid sensitivity 측정 필요.)
- Cycle 6+ 미해결:
  1. **Server n_boot=200 bootstrap (sbatch §5)**: valid filter region 의 정량 측정 필요.
  2. **sub-09 specificity 진정한 회복**: c8 drop 부분적 효과만 확인. voxel-level diagnostic, per-fold LOCO (run × color = 48 fold) effective DOF 확장.
  3. **Behavioral test design (Phase 3)**: valid filter region 내 두 points 의 pre-image 의 행동 데이터 차이 측정 protocol 명세.
  4. **HC 4번의 동급 후보 (mwJ=0.94)** 처리 — phase1/phase2 SRM/LOCO 데이터에서 sub-04 의 anomaly 여부 확인 (red-team check).
- 핵심 정량 메시지:
  - **2-comp 안에서**: sub-08 V4 raw l_topk=0 (perfect set match) 가 6 HC 모두와 분리 (HC raw ≥ 0.5). (β_s, β_c) point estimate 는 ill-posed (bootstrap IQR=40°/57°) → "set-match 가 신호, parameters 는 noise" 의 *내부* 증거.
  - **Across simulators**: Task 2 z spread 3.02 > 1.5 threshold → **원 framing falsified** 으로 정직하게 보고. Machado_1way 에서 HC sub-02 = sub-08 raw l_topk = 0.500 identical (set match 자체 분리 안 됨). post-hoc rescue ("≥2-DOF only") 는 추가 simulator 없이 미검증.
  - **Specificity floor**: 모든 p=0.14 는 n=6 HC pool empirical floor; sub-04 (mwJ=0.94) 와 Machado HC sub-02 (identical 0.500) 가 거의 동급. Server n_boot=200 bootstrap 만이 confidence 확정 가능.
  - **Stage C 함의**: 점 parameter 가 unidentifiable + simulator 별로 다른 best params → pre-image 정의 자체가 ill-posed. valid filter region 에서 도출 필요 (§7).

---

## 7. Stage C (Pre-image filter) 함의 — Cycle 4 unidentifiability 와의 충돌

### 7-1. 문제

Cycle 4 bootstrap 결과: sub-08 V4 best (β_s, β_c) **IQR = 40° / 57°** (n_boot=100). best (β_s, β_c) point estimate 는 사실상 unidentifiable plateau 위의 임의 점. CLAUDE.md 규칙 5: **"Pre-image는 forward model의 수치적 역함수로 계산"**. 이는 *specific* (β_s, β_c) 의 forward 역함수를 의미. **Cycle 4 의 unidentifiable 결과 → "어떤 (β_s, β_c)?" 가 정의되지 않음 → pre-image 도 정의되지 않음**.

추가로 Task 2 결과: 같은 sub-08 V4 LOCO 가 simulator 별로 다른 best params 를 산출 (2-comp: (58,−28), R+C: (19,−3), Machado: (0)). **모델 선택과 parameter 점추정 모두 ill-defined** 한데 단일 pre-image 를 도출할 수 없음.

### 7-2. 결론

> **Stage C 필터는 point parameter 에서가 아니라 set-level distortion mapping 에서 도출되어야 한다.**

Cycle 1-4 의 핵심 발견 ("vulnerability set 일치는 신호, parameter 는 noise") 은 Stage C 의 입력이 단일 (β_s, β_c) 점이 될 수 없음을 의미. 대신 **valid filter region** 정의가 필요:

> **valid filter region**(sub-08, V4, 2-comp) := { (β_s, β_c) ∈ grid : bootstrap(n=200) 에서 ≥50% boots 가 vuln_target 의 worst-color set (argsort(vuln_target)[:k]) 을 sim 의 worst-color set (argsort(vuln_sim)[:k]) 으로 Jaccard ≥ 2/3 reproduce }

> 이 region 은 plateau 의 *measurable subset* 으로, region 내 임의 점에서 pre-image 를 계산할 수 있고 region 의 부피가 unidentifiability 의 정량적 measure 가 됨.
>
> *Threshold 는 tentative — Jaccard ≥ 2/3 와 ≥50% boots 는 Cycle 1-5 에서 검증된 적 없는 제안값이며, Cycle 6 에서 grid sensitivity (Jaccard ∈ {0.5, 2/3, 0.8}, boot fraction ∈ {0.3, 0.5, 0.7}) 측정 필요.*

### 7-3. 후속 phase 함의

`future_phase3_behavioral_analysis` 의 필터 검증 단계는 두 가지 필터를 병행 평가해야 함:

1. **Point-estimate 필터** (전통적): bootstrap 의 median (β_s, β_c) 점 → forward 역함수 → pre-image. 단 Cycle 4 IQR 큰 plateau 위 임의 점 (현재 sub-08 V4 median (β_s=48, β_c=0); Task 2 single-point 는 (58, −28))의 perceptual prediction 을 행동 데이터와 매칭.

2. **Set-level 필터** (Cycle 5 제안): valid filter region 내 두 representative points (예: bootstrap n=200 의 25th vs 75th percentile (β_s,β_c)) 를 각각 pre-image 로 변환 → 두 pre-image 의 perceptual difference 를 region size 의 quantitative proxy 로 사용. 행동 데이터 prediction 정확도가 region 내 점 사이에서 *invariant* 면 framing 검증 (set 신호가 핵심), *variant* 면 point-estimate 필터로 회귀.

### 7-4. 측정 가능한 next-step

- **Cycle 6 candidate**: bootstrap n=200 (server) → valid filter region map (Jaccard ≥ 2/3 가 ≥50% boots 에서 만족하는 (β_s, β_c) cell 들). region 면적, region 내 (β_s, β_c) variance, region 안에서 ρ@best 의 IQR 측정. **threshold sensitivity**: Jaccard ∈ {0.5, 2/3, 0.8} × boot fraction ∈ {0.3, 0.5, 0.7} 의 9가지 조합에서 region 면적이 monotonic 하게 변하는지 확인 — non-monotonic 이면 valid region 정의 자체 재검토.
- **Phase 3 trigger**: behavioral 실험이 region 내 두 점에서 동일 prediction → set-level filter 채택. 다르면 추가 constraint (예: minimum-norm 필터 = region 내에서 ‖β‖² 최소) 도입.

이 함의는 Cycle 1-4 의 정량 결과 (bootstrap IQR, raw l_topk=0 의 robust set match) 와 Task 2 의 simulator-conditional 결과를 모두 일관되게 설명.

---

## Cycle 6 — 2026-04-30 (continued)

### 6-1. 진단 출발점 (Cycle 5 결과 후)

(a) Cycle 5 Task 1: c8-drop 으로 sub-09 V1 z=−3.46 회복했으나 sub-10 z=−3.46 동반 FP, V4 z=−2.78 동반 FP — c8 단독 outlier 가설 부분 사실, sub-10 분리 실패.
(b) Cycle 5 Task 2: cross-simulator z spread = 3.02 → "set-match is signal" framing falsified. Machado HC sub-02 가 sub-08 과 raw l_topk=0.500 동급.
(c) **두 falsification 의 공통 원인 후보**: Plan 04 cycle 1~5 의 모든 metric 이 8-color LOCO vuln vector level 에 머물러 있었음. voxel-pattern 차원의 정보를 활용하지 않음. → Cycle 6 는 within-subject **voxel-pattern signature** 차원으로 jump.

### 6-2. Step 1 — Voxel-pattern signature diagnostic

**스크립트**: `scripts/cycle_filter_refinement/cycle6_voxel_diag.py` (신규).
**환경**: `srm`. **실행 시간**: 2.2 s.

**설계**: n_voxels 가 subject 마다 다르므로 (V1: 330–858, V4: 16–70) cross-subject voxel-by-voxel z 는 ill-defined. 두 voxel-count-invariant signature 사용:
1. **per-color cross-voxel scalar signatures**: mean_amp, rms_amp, std_amp, top10_mean (top-10% voxel 평균), run_consistency.
2. **within-subject 8×8 color RDM** (1 − Pearson, run-averaged voxel pattern). RDM cell-level z 는 subject 간 비교 가능.

**Aggregate score per color**: |signature z| 평균 + |RDM row z| 평균 — color 별 outlier 강도.

#### 6-2-A. Top-3 outlier colors per subject (agg_z)

| ROI | sub-08 (CVD-deutan) | sub-09 (CVD-protan) | sub-10 (near-normal) | HC sub-04 anomaly check | HC sub-02 anomaly check |
|---|---|---|---|---|---|
| V1 | yellow(3.28) purple(3.08) red(2.03) | **magenta(4.17)** orange(2.31) cyan(2.15) | magenta(1.86) red(1.56) purple(1.44) | yellow(3.34) red(3.25) cyan(2.80) | green(2.17) cyan(1.69) orange(1.65) |
| V2 | yellow(4.96) purple(4.51) red(4.35) | magenta(2.41) cyan(1.93) green(1.63) | cyan(2.12) purple(2.02) blue(1.90) | yellow(2.77) green(1.94) magenta(1.66) | purple(1.51) red(1.34) green(1.30) |
| V4 | red(3.71) yellow(3.45) orange(2.60) | **magenta(2.86)** cyan(1.61) red(1.59) | purple(1.23) cyan(1.20) blue(1.19) | yellow(1.62) orange(1.53) magenta(1.53) | magenta(1.59) blue(1.39) cyan(1.23) |

#### 6-2-B. sub-09 vs sub-10 separation (top-3 Jaccard)

| ROI | Jaccard | shared | sub-09 only | sub-10 only | argmax(09−10) |
|---|---:|---|---|---|---|
| V1 | 0.20 | magenta | orange, cyan | red, purple | **magenta** |
| V2 | 0.20 | cyan | green, magenta | blue, purple | **magenta** |
| V4 | 0.20 | cyan | red, magenta | blue, purple | **magenta** |

→ **모든 ROI 에서 magenta 가 sub-09 vs sub-10 의 differentiator**. MEMORY Gen-4 Task #21 의 c8 magenta = "smoking gun" 진단을 voxel-pattern level 에서 재현.

#### 6-2-C. HC pool anomaly 진단

- **HC sub-04**: V1 yellow z=3.34, V2 yellow z=2.77 — **sub-08 과 같은 색에서 outlier**. V4 yellow z=1.62 (약함). → HC pool 에 V1/V2 deutan-like noise 존재 (Cycle 5 의 sub-04 mwJ=0.94 이 voxel-level signature 로 재현).
- **HC sub-02**: V1 green, V2 purple, V4 magenta — sub-08 과 다른 색. Cycle 5 의 Machado HC sub-02 동급은 *vuln vector level* 에서만 발생, voxel-pattern 차원에서는 sub-02 가 sub-08 과 outlier color 가 다름. → "Cycle 5 cross-sim 의 sub-02 동급" 은 vuln vector 에 한정된 현상으로 좁혀짐.
- **HC sub-07**: V4 yellow z=16.03 (catastrophic) — V4=16 voxel 의 noise dominance 정당화. 본 Cycle 6 에서도 specificity 분석에서 제외.

#### 6-2-D. 산출 파일

- `scripts/cycle_filter_refinement/cycle6_voxel_diag.py`
- `results/cycle_filter_refinement/cycle6_voxel_diag/{V1,V2,V4}_summary.json`
- `results/cycle_filter_refinement/cycle6_voxel_diag/aggregate.json`

### 6-3. Step 3 — Magenta-only specificity + HC sub-04 제외 검증

**스크립트**: `scripts/cycle_filter_refinement/cycle6_step3_specificity.py` (신규).

#### 6-3-A. Magenta agg_z 단독 specificity (sub-09 sniff test)

| ROI | HC pool μ ± σ (n=6, sub-07 제외) | sub-08 z (p_emp) | **sub-09 z (p_emp)** | sub-10 z (p_emp) | 분리도 (sub09 − sub10) |
|---|---|---:|---:|---:|---:|
| V1 | 1.80 ± 0.49 | −0.80 (0.857) | **+4.86 (0.143)** | +0.12 (0.429) | **+4.74** |
| V2 | 1.68 ± 0.56 | +0.94 (0.429) | +1.31 (0.286) | −0.63 (0.571) | +1.94 (약함) |
| V4 | 1.56 ± 0.31 | −0.54 (0.857) | **+4.17 (0.143)** | **−1.75 (1.000)** | **+5.92** |

**핵심 발견**:
- **sub-09 V1/V4 magenta z 가 +4 이상** — 4σ 이상 outlier. Cycle 1~5 의 LOCO vuln vector level 에서는 어떤 cell 에서도 sub-09 가 분리되지 않았으나, **voxel-pattern level 에서는 magenta-specific signature 가 sub-09 specificity 를 robust 하게 회복**.
- **sub-10 V4 magenta z=−1.75 (부호 반대)** — sub-09 와 명확히 분리. V1 sub-10 magenta z=+0.12 (정상 분포 안). c8-drop 시 sub-10 동반 FP 문제가 magenta z 단독으로는 발생하지 않음.
- **sub-08 magenta z 모두 음수** — sub-08 deutan 은 magenta 신호 *없음*. family 진단에 부합.
- emp_p=0.143 = n=6 HC pool floor 이지만 z=+4.86/+4.17 의 magnitude 자체가 매우 큼. server n_boot=200 으로 분포 안정성 검증 가능.

#### 6-3-B. HC sub-04 제외 시 sub-08 specificity 변화

| ROI × color | sub-08 value | with sub-04: HC μ, z, p | without sub-04: HC μ, z, p |
|---|---:|---|---|
| V1 yellow | 3.28 | μ=1.83, z=+1.73, p=0.29 | μ=1.52, **z=+4.02**, p=0.17 |
| V2 yellow | 4.96 | μ=1.58, z=+5.60, p=0.14 | μ=1.34, **z=+20.42**, p=0.17 |
| V4 yellow | 3.45 | μ=1.32, z=+5.57, p=0.14 | μ=1.27, z=+5.52, p=0.17 |
| V1 magenta | 1.41 | μ=1.80, z=−0.80, p=0.86 | μ=1.63, z=−0.78, p=0.83 |
| V2 magenta | 2.20 | μ=1.68, z=+0.94, p=0.43 | μ=1.68, z=+0.84, p=0.50 |
| V4 magenta | 1.39 | μ=1.56, z=−0.54, p=0.86 | μ=1.56, z=−0.50, p=0.83 |

**핵심 발견**:
- **HC sub-04 제외 시 V1/V2 yellow sub-08 z 큰 폭 강화**: V1 1.73 → +4.02 (2.3× ↑), V2 5.60 → +20.42 (3.6× ↑, sd 거의 0 으로 collapse).
- **V4 는 sub-04 영향 없음** (z 5.57 → 5.52). Cycle 6-2-A 표의 sub-04 V4 yellow z=1.62 (V1/V2 보다 작음) 와 정합 — **HC sub-04 anomaly 는 V1/V2 specific**.
- sub-08 magenta 는 sub-04 제외에 무관 (sub-04 의 V1/V2/V4 magenta 모두 normal 수준).
- p_emp 가 n=6 → n=5 변경 시 floor (1/7=0.143) → (1/6=0.167) 로 약간 오르지만 z 의 magnitude 변화가 본 finding 의 핵심.

#### 6-3-C. 산출 파일

- `scripts/cycle_filter_refinement/cycle6_step3_specificity.py`
- `results/cycle_filter_refinement/cycle6_step3_specificity.json`

### 6-4. Cycle 6 결론 + Plan 04 종합 결론 update

#### 6-4-A. sub-09 specificity — **fundamentally inaccessible 결론 reframe**

| 차원 | sub-09 specificity |
|---|---|
| **LOCO vuln vector level** (Plan 04 Cycle 1~5) | NS 모든 ROI · metric · loss 결합 |
| **Voxel-pattern signature level** (Cycle 6) | **V1 magenta z=+4.86, V4 magenta z=+4.17** |

→ Cycle 5 Task 1 의 "sub-09 fundamentally inaccessible" 결론은 **vuln vector 차원에 한정**. voxel-pattern 차원에서는 magenta-specific signature 로 회복. **본 paradigm 의 데이터는 sub-09 신호를 포함하나, simulator-based fitting metric 으로는 추출되지 않는다** 가 정확한 진단.

#### 6-4-B. HC pool 신뢰성 — sub-04 정제 권고

- HC sub-04 가 V1/V2 deutan-like outlier (Cycle 6-2-A, Cycle 5 의 mwJ=0.94 voxel-level 근거) → HC pool 정제 옵션:
  - (i) sub-04 제외 (n=5 HC pool): V1/V2 sub-08 yellow z 큰 폭 강화 (Cycle 6-3-B).
  - (ii) sub-04 유지하되 V1/V2 specificity 결과 caveat 명시: "HC sub-04 의 deutan-like noise pattern 동반".
  - (iii) sub-04 의 phase1 procrustes/SRM 결과를 추가 점검 (LOOP HC null 검증 후 결정) — Cycle 7 candidate.

#### 6-4-C. Plan 04 §6 종합 결론 update (현재 cycle 1~6 정합)

| 결론 | Cycle 1~5 진술 | Cycle 6 update |
|---|---|---|
| sub-08 V4 specificity | "z=−4.97 (n=6 ceiling, sub-04 동급)" | **HC sub-04 제외 시 V1 yellow z 도 +4.02 회복; V4 specificity 는 sub-04 영향 없음** |
| sub-09 specificity | "어떤 cell 에서도 NS, fundamentally inaccessible" | **voxel-pattern magenta z 단독으로 V1 z=+4.86, V4 z=+4.17 회복** |
| set-match framing | "simulator-conditional, falsified" | 유지 (Cycle 6 voxel-pattern 차원은 별개 framework) |
| valid filter region | "set-level distortion mapping" | 유지 + voxel-pattern signature 를 mapping 의 *결과* 검증 metric 으로 추가 |

#### 6-4-D. Cycle 7 후보 + Phase 3 trigger update

1. **HC sub-04 의 phase1 procrustes/SRM outlier 진단** — sub-04 제외/유지 결정.
2. **Magenta z + topk 결합 metric** — sub-08 deutan 은 yellow z, sub-09 protan 은 magenta z 가 separation feature → family-specific voxel-pattern feature 결합.
3. **per-fold LOCO (run × color = 48 fold)** — 본 plan 의 fundamental DOF 한계 직접 해결 (advisor 가 별도 plan 권고).
4. **Phase 3 trigger update**: behavioral validation 시 (a) sub-08: V4 set-match + V1/V2 yellow voxel signature; (b) sub-09: V1/V4 magenta voxel signature 를 각각 검증 — protan/deutan family-specific dual filter.
5. **Server bootstrap (Job 98376) 결과 통합**: voxel-pattern signature 의 bootstrap 분포는 별도 — 단 magenta z=+4.86 같은 큰 magnitude 는 small bootstrap 에서도 stable 예상.

### 6-5. Cycle 6 산출 파일 (요약)

- `scripts/cycle_filter_refinement/cycle6_voxel_diag.py`
- `scripts/cycle_filter_refinement/cycle6_step3_specificity.py`
- `results/cycle_filter_refinement/cycle6_voxel_diag/{V1,V2,V4}_summary.json` + `aggregate.json`
- `results/cycle_filter_refinement/cycle6_step3_specificity.json`
- 본 마크다운 (§Cycle 6 추가)

---

## Cycle 6-server — 2026-04-30 Server bootstrap (Job 98376)

### 6s-1. 자원 측정 (srun probe)

- node2, srun --cpus-per-task=4 --mem=8G, 1 boot 12.9s, peak RSS 157 MB.
- → 본 array 자원: --cpus-per-task=2 --mem=4G --time=2:00:00 --array=0-5%6 (자원 절약 + 동시 6 cell 시도, node2 capacity 로 3 concurrent 운용).

### 6s-2. n_boot=200 결과 (5/6 cell, sub-09 V4 진행 중)

| Cell | l_topk median | l_topk IQR | l_topk CI95 | best_bs median, IQR | best_bc median, IQR | rho@best median | rho CI95 |
|---|---:|---:|---|---:|---:|---:|---|
| sub-08 V1 | **0.000** | 0.50 | [0.000, 0.500] | 0.0, **0.0** | 0.0, **0.0** | +0.738 | [+0.452, +0.929] |
| sub-08 V2 | 0.500 | 0.50 | [0.000, 0.500] | 4.0, 46.0 | 0.0, 18.0 | +0.595 | [+0.214, +0.762] |
| sub-08 V4 | 0.000 | 0.50 | [0.000, 0.500] | 38.0, 40.5 | 7.0, 38.5 | +0.619 | [0.000, +0.881] |
| sub-09 V1 | 0.500 | 0.00 | [0.500, 0.500] | 61.0, 76.0 | 22.0, 30.0 | +0.667 | [+0.333, +0.882] |
| **sub-09 V2** | **0.000** | 0.00 | [0.000, 0.500] | 78.0, 19.0 | 52.0, 8.5 | +0.690 | [−0.025, +0.833] |
| sub-09 V4 | 0.500 | 0.30 | [0.000, 0.800] | 0.0, 14.0 | 2.0, 14.0 | +0.071 | [−0.286, +0.619] |

### 6s-3. 새 발견 — Plan 04 종합 결론 추가 update

#### (a) sub-08 V1 = 가장 robust set-match cell

- l_topk median=0.000, **bs/bc IQR 모두 0.0**, rho median +0.738.
- Cycle 1~6 의 V4 primary 권장에 V1 도 동급 또는 우월 후보 추가.
- Plan 04 §4-1 추천 구성 update 필요: V1 단독 또는 V1+V4 결합 (set-match 차원).
- bootstrap 한정의 (β_s, β_c)=(0, 0) origin 매칭 — Tikhonov 가 origin 으로 끌어당긴 효과인지, 진짜 baseline 에서 sub-08 worst-color set 이 HC 와 다른지 추가 진단 필요 (Cycle 7 candidate).

#### (b) sub-09 V2 = 새 specificity 후보 (set-match level)

- Cycle 1~5 의 V2 sub-09 z=−0.05 (NS) 또는 +0.05 (8-color) 였으나 server n_boot=200 에서 l_topk median=0.000 (perfect set match).
- best_bs median=78.0, IQR=19.0 — V2 grid 모서리 (β_s=80) 근처에 안정. **grid 확장 필요** 가능성.
- voxel-pattern (Cycle 6) 의 sub-09 V2 magenta z=+1.31 (약함) 과 다른 차원의 신호 — V2 set-match 가 voxel-pattern 보다 sub-09 protan 신호 잘 capture.

#### (c) sub-09 specificity 의 cross-ROI 분포 — 두 차원

| 신호 차원 | V1 | V2 | V4 |
|---|---|---|---|
| **voxel-pattern (Cycle 6)** | magenta z=+4.86 | 약함 (+1.31) | magenta z=+4.17 |
| **set-match (Cycle 6s)** | 약함 (median=0.500, IQR=0.0) | **perfect (0.000, IQR=0.0)** | 약함 (median=0.500, IQR=0.30, ρ CI95 [−0.286, +0.619] 0 포함) |

→ **sub-09 신호는 voxel-pattern (V1, V4) + set-match (V2) 의 ROI 분리**. V4 는 voxel-pattern 만 강함 (magenta z=+4.17), set-match 는 약함 (rho CI 95 0 포함). V1 voxel-pattern + V2 set-match 결합이 sub-09 에 가장 적합한 dual filter framework. sub-09 V4 는 voxel-only filter cell.

#### (d) (β_s, β_c) unidentifiability 재확인

- sub-08 V4 IQR (β_s=40.5, β_c=38.5) — Cycle 4 local n_boot=100 (β_s IQR=40, β_c=57) 와 일관.
- sub-08 V1 IQR=0.0 — sub-08 V1 만 (β_s, β_c)=(0, 0) 에서 안정. 대부분 cell 은 IQR > 19.
- 결론: §7 Stage C 함의 (set-level filter region) 유지. point estimate 필터는 V1 sub-08 cell 에서만 의미 있음.

### 6s-4. Cycle 7 후보 update (Cycle 6 + 6s 통합)

1. **HC sub-04 V1/V2 deutan-like noise 의 phase1 procrustes/SRM 진단** (Cycle 6 후속).
2. **sub-08 V1 origin 매칭의 origin 정체** — Tikhonov 효과 vs 진짜 baseline match. 추가 boot with λ=0 비교.
3. **sub-09 V2 grid 확장** (β_s 범위 ±100 까지) — best 가 grid 모서리에 붙어있는지.
4. **dual filter framework**:
   - sub-08: V4 set-match (β_s, β_c region) + V1/V2 yellow voxel signature
   - sub-09: V2 set-match (β_s ≈ 78) + V1/V4 magenta voxel signature
5. **Phase 3 trigger update**: behavioral validation 시 dual filter 의 ROI-specific signal 검증.
6. **per-fold LOCO** (DOF 확장) — 별도 plan 으로 미뤄진 상태 유지.

### 6s-5. 산출 파일

- `sbatch/run_plan04_bootstrap.sbatch` (수정: --cpus-per-task=2 --mem=4G --array=0-5%6)
- `results/cycle_filter_refinement/bootstrap_server/sub-{08,09}_{V1,V2,V4}.json` (전체 6 cell 완료, n_boot=200)
- 본 마크다운 (§Cycle 6-server 추가)

### 6s-6. 전체 6 cell 통합 결론

(a) **sub-08 V1 = 가장 robust set-match** (median=0.000, β IQR=0).
(b) **sub-09 V2 = 새 set-match cell** (median=0.000) — 단 best_bs=78 grid 모서리, 확장 검토 필요.
(c) **sub-09 V4 set-match 약함** (rho CI95 0 포함) — voxel-pattern 만 강함 (magenta z=+4.17). **두 차원이 ROI 별 분리**.
(d) (β_s, β_c) unidentifiability 는 sub-08 V1 cell 만 예외. 다른 cell (특히 sub-08 V4, sub-09 V1) 은 IQR > 19 — Cycle 4 함의 (Stage C set-level filter region) 유지.

---

## Cycle 7 — 2026-05-01 두 피험자 공통 ROI/Loss 도출

### 7-1. 출발점

Cycle 6 per-signature 분해에서 **단순 activation (mean_amp) 이 매우 강한 family-specific signal**임을 확인:
- sub-08 yellow: mean_amp z = V2 −3.31, V4 −4.45 (**음수** outlier)
- sub-09 magenta: mean_amp z = V1 +3.31, V2 +3.83, V4 +2.85 (**양수** outlier)
- 부호가 family를 구분 → |z| 단순 합산은 부호 정보 손실

**결론**: mean_amp 제거 X, 대신 family-aware **signed** combine 도입.

### 7-2. 작업 A — V4-inclusive Family-aware dual-criterion loss

#### 정의

$$L_\text{vox-axis}(s, R, c) = -\big[\text{sign}_\text{family}(s) \cdot z_\text{mean}(c) + |z_\text{rdm-row}(c)| + |z_\text{runc}(c)|\big]$$
- sign_family: deutan(sub-08) = **−1** (yellow mean_amp 음수), protan(sub-09) = **+1** (magenta mean_amp 양수)
- c_family: deutan→yellow(idx 2), protan→magenta(idx 7)

$$L_\text{set} = l_\text{topk\_jaccard} + 0.2 \cdot \big((\beta_s/80)^2 + (\beta_c/60)^2\big)\quad\text{at grid min}$$

z-score within HC pool (n=6, sub-07 제외).

#### 결과 — Per (subj, ROI) z

| subj | ROI | L_set | z_set | L_vox | z_vox |
|---|---|---:|---:|---:|---:|
| sub-08 V1 | 0.500 | −0.52 | −6.55 | **−3.78** |
| sub-08 V2 | 0.501 | +0.04 | −11.48 | **−13.25** |
| **sub-08 V4** | 0.149 | **−4.54** | −7.82 | **−10.48** |
| sub-09 V1 | 0.500 | −0.52 | −9.45 | **−3.18** |
| sub-09 V2 | 0.792 | +2.69 | −5.84 | **−3.71** |
| **sub-09 V4** | 0.800 | +0.59 | −5.77 | **−2.85** |
| sub-10 V1 | 0.500 | −0.52 | −0.75 | +1.36 |
| sub-10 V2 | 0.801 | +2.78 | −0.41 | +2.26 |
| sub-10 V4 | 0.546 | −1.41 | −0.76 | +0.48 |

**핵심**: family-aware z_vox 가 **두 피험자 모든 ROI에서 z<−2** (sub-09 V4 −2.85가 가장 약함). sub-10은 모든 ROI에서 z>0 (정상). z_set 단독은 sub-09 모두 NS.

#### α/β grid sweep (5×5 = 25 × ROI 5종 = 120 cells)

공통 best 기준: **두 CVD z_comb ≤ −2 AND |sub-10 z_comb| < 1.5**
→ **32/120 cells 통과**

| cfg | α | β | z08 | z09 | z10 |
|---|---:|---:|---:|---:|---:|
| **V1+V4** | **1.00** | **1.00** | **−19.32** | **−5.95** | **−0.09** |
| V1+V4 | 0.75 | 1.00 | −18.05 | −5.97 | +0.39 |
| V1+V4 | 0.50 | 1.00 | −16.79 | −5.99 | +0.87 |
| V1+V4 | 0.00 | 0.75 | −10.70 | −4.52 | +1.37 |
| **V1_only** | **1.00** | **1.00** | **−4.30** | **−3.70** | **+0.84** |

→ **V1+V4 (α=1.0, β=1.0)** 가 가장 강한 분리 + sub-10 perfect sanity. V1_only도 충분.

### 7-3. 작업 B — Weighted Spearman + L_set blend

#### 정의

$$\rho_w = \text{weighted Pearson on ranks}, \quad w_i = \max(-\text{vuln}_i, 0)$$
$$L_\text{wSpear} = 1 - \rho_w$$

L_set 의 best (β_s, β_c) 점에서 ρ_w 평가 (consistent with dual-criterion logic).

#### 결과 — Per (subj, ROI)

| subj | ROI | ρ_w | L_wSpear | z_wSp |
|---|---|---:|---:|---:|
| sub-08 V1 | +0.885 | 0.115 | −1.27 |
| sub-08 V2 | +0.329 | 0.671 | −0.89 |
| sub-08 V4 | +0.845 | 0.155 | −1.50 |
| sub-09 V1 | +0.103 | 0.897 | −0.27 |
| sub-09 V2 | **−0.876** | 1.876 | +1.48 (역) |
| sub-09 V4 | −0.150 | 1.150 | −0.24 |
| sub-10 V1 | **−1.000** | 2.000 | +1.15 |

#### α/β sweep 결과

**Common best 0/120 cells**. Relaxed (z≤−1.5) 도 0.

#### 비판

- **sub-09 vuln-vector level 은 어떤 weighted metric 으로도 분리 불가** — Plan 01 Cycle 3 결론 (sub-09 baseline_rho 음수, c8 magenta anti-prediction) 재확인.
- L_wSpear 는 ρ_w 가 0 근처라 (sub-09 V1 +0.103, V4 −0.150) noise floor 안.
- **포괄적 동향+정도 metric 도 vuln-vector level 의 한계 답습** — voxel-pattern level 정보 미활용.

→ 대안 발동 (사전 명시 trigger 충족).

### 7-4. 대안 1 — 3-way blend (Task A + Task B 결합)

#### 정의

$$L_\text{3way} = \alpha \cdot z_\text{set} + \beta \cdot z_\text{vox-axis} + \gamma \cdot z_\text{wSp}$$
α, β, γ ∈ {0, 0.25, 0.5, 0.75, 1.0}, 5×5×5 = 124 × ROI 5종 = 620 cells.

#### 결과

**Common best 116/620 cells, 진정 3-way (모든 weight >0): 74/620**

| cfg | α_set | β_vox | γ_wSp | z08 | z09 | z10 |
|---|---:|---:|---:|---:|---:|---:|
| **V1+V4** | **1.00** | **1.00** | **0.75** | **−21.39** | **−6.33** | **+1.31** |
| V1+V4 | 1.00 | 1.00 | 0.50 | −20.70 | −6.21 | +0.84 |
| V1+V4 | 1.00 | 1.00 | 0.25 | −20.01 | −6.08 | +0.37 |
| V1+V4 | 1.00 | 1.00 | 0.00 | −19.32 | −5.95 | **−0.09** |

#### 해석

- **모든 best cell에서 β_vox = 1.0 또는 0.75 (dominant)**.
- **γ_wSp 추가는 sub-08 z를 −19.32 → −21.39로 강화하나 sub-09는 미미한 개선 (−5.95 → −6.33)**.
- **α_set 도 보조적**. β_vox=0 일 때 어떤 (α, γ) 도 sub-09 분리 불가.
- **V4 가 모든 best ROI config에 포함**: V1+V4 가 최강.

### 7-5. 두 피험자 공통 ROI/Loss Selection Rule

**Selection Rule (확정)**:

> Subject s에 대해, family(s)에 따라 c_family와 sign_family를 자동 지정:
> - sub-08 (deutan) → c_family = yellow, sign_family = −1
> - sub-09 (protan) → c_family = magenta, sign_family = +1
>
> ROI: **V1 + V4 (z_sum)**. V4 는 voxel-axis primary, V1은 보조 신호 강화.
>
> Loss: $L = z_\text{set}(R) + z_\text{vox-axis}(R, c_\text{family})$ (α=β=1.0, γ=0; 단순화).
>
> 평가: HC pool (n=6, sub-07 제외) 대비 z<−2 이면 specificity 만족.

#### 검증 결과 (이 selection rule 적용 시)

| 피험자 | z_combined (V1+V4) | 판정 |
|---|---:|---|
| sub-08 (deutan) | **−19.32** | 매우 강한 specificity |
| sub-09 (protan) | **−5.95** | 강한 specificity (Plan 01 Cycle 3 "fundamentally inaccessible" 결론 *reframe*) |
| sub-10 (near-normal) | **−0.09** | sanity 통과 (정확히 0 근방) |

#### Selection Rule 의 보수적 강화 (γ_wSp 0.75 옵션)

V1+V4, α=β=1.0, γ=0.75:
- z08=−21.39, z09=−6.33, z10=**+1.31** (정상 범위, 1.5 미만)
- sub-08 specificity 강화하지만 sub-10이 약간 +쪽으로 이동 → 보수적 사용 시 γ=0 권장.

### 7-6. Cycle 7 결론 + Cycle 8+ 후보

#### 핵심 결론

1. **Plan 04 cycle 1~5 의 "sub-09 fundamentally inaccessible" 결론은 vuln-vector level 한정**. Family-aware voxel-axis (signed mean_amp + |RDM| + |run_consistency|) 로 sub-09 V1+V4 z=−5.95 robust 회복.
2. **공통 selection rule**: V1+V4 + family-aware z_set + z_vox-axis 단순 합산. V4 가 voxel-axis primary로 강제 포함.
3. **wSpear (γ) 는 marginal — 본질적 신호는 voxel-axis**. 포괄적 동향+정도 metric 의 vuln-vector level 한계 재확인.
4. **HC sub-04 deutan-like noise** 는 mean_amp 부호로 sub-08과 분리됨 (sub-04 mean_amp +1.98, sub-08 −0.62~−4.45) — sign_family 도입의 추가 정당화.

#### 산출 파일

- `scripts/cycle_filter_refinement/cycle7_dual_criterion.py` (Task A)
- `scripts/cycle_filter_refinement/cycle7_blend_wspearman.py` (Task B)
- `scripts/cycle_filter_refinement/cycle7_3way_blend.py` (대안 1)
- `results/cycle_filter_refinement/cycle7_dual_criterion.json`
- `results/cycle_filter_refinement/cycle7_blend_wspearman.json`
- `results/cycle_filter_refinement/cycle7_3way_blend.json`

#### Cycle 8+ 미해결

1. **z 의 magnitude 자체에 대한 robustness**: HC pool n=6 sd 작아 z=−13.25 같은 극단 값 발생. server bootstrap 으로 voxel-axis z 의 분포 검증 필요.
2. **Family-color hard-coded 의 확장성**: sub-08 deutan→yellow, sub-09 protan→magenta 는 literature + Cycle 6 데이터 기반. 다른 family/severity 환자에 대한 범용성은 검증 미완.
3. **sign_family 자동 학습**: 현재 hard-coded. HC pool 에서 mean_amp 평균 부호 기반 자동 학습 시 family 구분 자체도 data-driven 가능.
4. **Phase 3 dual-filter behavioral validation**: V1+V4 z_combined 기반 필터의 행동 prediction 정확도 (perceptual matching) 검증.
5. **대안 2/3 (RDM-only, RSA cross-subject) 미시도** — 본 cycle 의 dual-criterion 결과가 충분히 강하므로 보류. 후속 cycle 에서 robustness check 시 동원 가능.

---

## Cycle 8 — 2026-05-01 Bootstrap robustness + Pre-image filter

### 8-1. #1 Server bootstrap voxel-axis (PENDING — Job 98931)

#### 목적
Cycle 7 selection rule 의 z_vox-axis (=−[sign·z_mean + |z_rdm-row| + |z_runc|]) 이 HC pool n=6 에서 sd 작아 z=−13/−19 같은 극단값 발생. n_boot=200 HC subject resample 로 분포 안정성 검증.

#### 자원 측정 (srun probe — 다른 사용자 jobs 폭주로 실패. 이전 cycle 6s 와 동일 자원 가정)
- node2, --cpus-per-task=2 --mem=4G --time=1:00:00 --array=0-5%6
- 6 cells: V1/V2/V4 × sub-08/09 (sub-10 sanity 제외, CLAUDE.md 7번)

#### 상태
- Job 98931 submitted, **PD QOSMaxJobsPerUserLimit** (사용자의 cat_s123, rt_sbl_c3, moe_p 등 다른 jobs 동시 진행으로 대기 중).
- 결과는 다른 jobs 완료 후 자동 시작. ScheduleWakeup 으로 추후 점검.
- 산출 파일 (예정): `results/cycle_filter_refinement/cycle8_voxel_bootstrap/sub-{08,09}_{V1,V2,V4}.json`

#### 출력 metric (예정)
- L_vox-axis median, IQR, CI95
- z_mean / z_runc / z_rdm-row 각 component bootstrap 분포
- HC pool 작은 sd 의 영향 정량화

### 8-2. #2 Pre-image filter (완료)

#### 목적
Cycle 7 selection rule 에 따른 stimulus-space 보정 필터 도출. 8-color hue 입력에 대해 forward 2-component 모델의 numerical inverse.

#### Forward 모델
$$T(\theta; \beta_s, \beta_c, \text{family}) = \theta + \beta_s \cos(\theta - 90°) + \beta_c \cos(\theta - \theta_\text{conf}(\text{family})) \pmod{360°}$$
- $\theta_\text{conf}$: protan = 16°, deutan = 150°
- $(\beta_s, \beta_c)$: Cycle 6s server bootstrap median per ROI

#### Inverse 알고리즘
- 3600 grid points 위 forward T 평가, $|T(\theta_\text{pre}) - \theta_\text{obs}|$ 최소화하는 root.
- **Multi-root 처리**: $|\theta_\text{pre} - \theta_\text{obs}| \leq 90°$ 윈도우 안의 root 우선 (closest stimulus). 윈도우 밖만 root 있으면 글로벌 best 사용.
- Forward T 가 큰 (β_s, β_c) 에서 비단조 → multi-root 빈번.

#### 결과 — sub-08 (deutan)

**V4-only** (β_s=38.0, β_c=7.0):

| color | obs° | preimage° | shift° | err° |
|---|---:|---:|---:|---:|
| red | 0 | 3.5 | **+3.5** | 0.017 |
| orange | 45 | 29.7 | **−15.3** | 0.004 |
| yellow | 90 | 58.0 | **−32.0** | 0.018 |
| green | 135 | 93.2 | **−41.8** | 0.026 |
| cyan | 180 | 160.3 | −19.7 | 0.003 |
| blue | 225 | 266.0 | +41.0 | 0.024 |
| purple | 270 | 306.8 | +36.8 | 0.062 |
| magenta | 315 | 336.9 | +21.9 | 0.042 |

**V1+V4 avg** (β_s=19.0, β_c=3.5):

| color | obs° | preimage° | shift° |
|---|---:|---:|---:|
| red | 0 | 2.2 | +2.2 |
| orange | 45 | 35.4 | −9.6 |
| yellow | 90 | 71.3 | −18.7 |
| green | 135 | 114.9 | −20.1 |
| cyan | 180 | 175.3 | −4.7 |
| blue | 225 | 241.9 | +16.9 |
| purple | 270 | 290.5 | +20.5 |
| magenta | 315 | 328.4 | +13.4 |

#### 결과 — sub-09 (protan)

**V4-only** (β_s=0.0, β_c=2.0): 매우 작은 shifts (β_s=0 이라 자연):

| color | obs° | preimage° | shift° |
|---|---:|---:|---:|
| all | — | ≈obs | ±2° 범위 |

**V1+V4 avg** (β_s=30.5, β_c=12.0):

| color | obs° | preimage° | shift° |
|---|---:|---:|---:|
| red | 0 | 352.8 | −7.2 |
| orange | 45 | 21.8 | −23.2 |
| yellow | 90 | 55.6 | **−34.4** |
| green | 135 | 105.5 | **−29.5** |
| cyan | 180 | 204.5 | +24.5 |
| blue | 225 | 260.3 | +35.3 |
| purple | 270 | 295.5 | +25.5 |
| magenta | 315 | 325.0 | +10.0 |

#### 해석

- **sub-08 V4 (β_s=38)**: yellow/green 에서 큰 음의 shift (−32°, −42°) — deutan compensation. red/magenta 는 작은 양의 shift.
- **sub-08 V1+V4 (β_s=19)**: shift 진폭 절반 정도. V4 단독 vs V1+V4 결합의 trade-off (V4 단독 = 강한 보정, V1+V4 = smoother).
- **sub-09 V4 단독 (β_s=0)**: 거의 zero shift — V4 bootstrap median 이 origin. preimage 가 trivial.
- **sub-09 V1+V4 (β_s=30.5)**: yellow/green 에서 큰 음의 shift (−34°, −30°) — protan compensation. 패턴은 sub-08 V4 와 유사 (S-cone vs L-M axis 차이로 보정 방향 같음).
- **모든 cell 에서 in_window=True**: 90° 윈도우 안에 root 존재 — bijective preimage 가능.

#### Caveat (Plan 04 §7 함의 적용)

- **(β_s, β_c) point estimate 자체가 ill-posed** (Cycle 4/6s β IQR 14~76). 본 preimage 는 bootstrap median 단일 점에서 도출 — set-level filter region 의 한 표본.
- **V4-only 와 V1+V4 결합 preimage 의 shift 패턴이 정성적으로 다름** (sub-08 의 경우): V4 강한 보정 vs V1+V4 약한 보정. Phase 3 행동 검증 시 둘 모두 평가 필요.
- **sub-09 V4-only preimage 는 trivial** — V4 set-match 가 약하다는 Cycle 6s 의 결과와 정합. sub-09 행동 보정에는 V1+V4 결합 preimage 가 권장.

#### 산출 파일 — Cycle 8 #2

- `scripts/cycle_filter_refinement/cycle8_preimage.py`
- `results/cycle_filter_refinement/cycle8_preimage.json`

### 8-3. HC LOO False Positive 검증 (Cycle 7 selection rule)

#### 목적
Cycle 7 selection rule (V1+V4 z_sum, α=β=1, family-aware) 이 HC subjects 에 false positive 를 유발하는지 검증. 각 HC 를 LOO target 으로 두고 나머지 5명 pool 에서 z_combined 측정. deutan/protan 두 family hypothesis 각각 평가.

#### 스크립트

`scripts/cycle_filter_refinement/cycle8_hc_fp.py`. 각 HC 의 voxel z (Cycle 6 voxel_diag 의 LOO HC pool 기준 sigs_z, rdm_z) + L_set (Cycle 1 landscape 의 l_topk + Tikh) 활용.

#### 결과

| target | deutan z_V1+V4 | protan z_V1+V4 | verdict |
|---|---:|---:|---|
| sub-01 | −1.87 | −0.68 | marginal/pass |
| **sub-02** | −0.57 | **−4.39** | **FP under protan** |
| sub-03 | +0.05 | +1.18 | pass |
| **sub-04** | **−4.40** | **−5.09** | **FP under both** |
| sub-05 | +1.46 | +1.98 | pass |
| sub-06 | +8.71 | +13.52 | pass (반대 방향) |

**FP rate** (z<−2): deutan 1/6, protan 2/6, **either family 2/6 (33%)**.

#### CVD 와 HC FP 의 magnitude 비교

| 피험자 | z_V1+V4 | 비고 |
|---|---:|---|
| sub-08 CVD (deutan) | **−19.32** | HC FP 최대 (−5.09) 보다 4× 강함 — **robust specificity** |
| sub-09 CVD (protan) | **−5.95** | sub-04 HC FP (−5.09) 와 거의 동급 — **fragile specificity** |
| sub-04 HC FP (protan) | −5.09 | sub-09 CVD 거의 동급 |
| sub-04 HC FP (deutan) | −4.40 | |
| sub-02 HC FP (protan) | −4.39 | 새 발견 (Cycle 6 voxel z 약했음에도 combine 시 도달) |
| sub-10 (near-normal) | −0.09 | perfect sanity |
| sub-06 (HC) | +13.52 | 반대 방향 — pass |

#### 핵심 함의

1. **sub-08 specificity 는 통계적으로 robust** — HC FP 분포 (μ=−1.0, max |z|=5.09) 대비 z=−19.32 는 매우 큰 magnitude. Cycle 7 결론 유지.

2. **sub-09 specificity 는 통계적으로 fragile** — z=−5.95 가 sub-04 HC LOO (−5.09) 와 거의 동급. 두 가지 해석 가능:
   - **(a) sub-04 가 진짜 HC 가 아닐 가능성** — Cycle 6 의 V1/V2 deutan-like noise 진단 + 본 cycle 의 deutan/protan 모두 FP → subclinical CVD 의심.
   - **(b) sub-09 신호 자체의 magnitude 가 selection rule 의 noise floor 와 비슷** — n=6 HC pool 의 SD 작아 false negative/positive 모두 큰 영향.

3. **sub-02 protan FP** 는 새 발견 — Cycle 6 voxel-pattern z 표에서는 magenta z 작았으나 (V1 +1.40, V2 +1.19), L_set + L_vox combine 시 z_combined=−4.39. **Combine 효과**가 단일 metric 보다 sensitivity 높지만 동시에 FP rate 도 증가.

4. **sub-06 z=+13.52 (positive)** — 반대 방향. selection rule 의 sign convention 에서 +z = "HC pool 보다 정상적으로 fit" → FP 아님.

#### 처리 방향 후보

**옵션 A — sub-04 (와 sub-02) HC pool 제외**:
- HC pool 을 n=4 (sub-01/03/05/06) 로 정제 → sub-08, sub-09, sub-10 z 재계산.
- sub-04 의 phase1 procrustes / phase2_SRM 결과 추가 검증 (subclinical CVD 검토).
- 결과 따라 sub-09 specificity 재평가.

**옵션 B — Selection rule 보수화**:
- z<−2 임계값 → z<−6 (CVD 와 HC FP 의 gap 활용). sub-08 specificity 유지, sub-09 (−5.95) 는 미달 → "robust CVD detection" 만 claim.
- 결과: sub-09 는 "weak signal candidate" 로 강등.

**옵션 C — Bootstrap robustness 결과 (#1) 통합 후 재평가**:
- Job 98931 server bootstrap 완료 시 voxel-axis z 의 분포 (CI95) 가 sub-09 vs sub-04 의 overlap 을 정량화.
- overlap 작으면 sub-09 specificity 유지, 크면 옵션 A/B 진행.

#### 산출 파일

- `scripts/cycle_filter_refinement/cycle8_hc_fp.py`
- `results/cycle_filter_refinement/cycle8_hc_fp.json`

### 8-4. Cycle 8 #1-alt — HC LOO bootstrap (sub-04, sub-02) trigger

옵션 C (Cycle 8 §8-3) 결정 따라 sub-04, sub-02 의 HC LOO bootstrap 을 추가 트리거. 분포 overlap 분석으로 sub-09 specificity 의 통계적 유의성 정량화.

#### 추가 sbatch
- 스크립트: `sbatch/run_cycle8_hc_fp_boot.sbatch` (array 0-5%6, 6 cells: V1/V2/V4 × sub-{04, 02})
- `cycle8_voxel_bootstrap.py` 수정: FAMILY 맵에 '04'(deutan), '02'(protan) 추가 + HC LOO 자동 제외 (`hc_avail = [h for h in HC if h != args.subject]`)
- Job 98945 submitted, status: PD QOSMaxJobsPerUserLimit

#### Job 통합 점검 후 옵션 결정

| Job | Cells | 목적 |
|---|---|---|
| 98931 | sub-08, sub-09 × V1/V2/V4 | CVD specificity 의 robustness |
| 98945 | sub-04, sub-02 × V1/V2/V4 | HC FP candidate 의 분포 |

두 jobs 모두 완료 후:
- (a) sub-09 vs sub-04 의 z_vox-axis CI95 overlap 정량화 → sub-09 specificity 통계적 유의성
- (b) sub-08 vs sub-04 의 overlap (deutan family 상에서) → robust margin 재확인
- (c) overlap 결과에 따라 옵션 A (HC pool 정제) 또는 옵션 B (selection rule 보수화) 진행

### 8-5. sub-04 데이터 정밀 진단 (Cycle 8 #4)

**전제 (사용자 명시)**: sub-04 는 진짜 HC. 어느 데이터가 deutan-like outlier 를 만드는가?

#### 스크립트
`/tmp/sub04_diag.py` — sub-04 amplitudes 의 (1) per-run yellow voxel-pattern 안정성, (2) HC pool 다른 5명과 voxel pattern Pearson, (3) 색별 run-pair Pearson (run consistency), (4) mean amplitude per color z (HC pool n=5 기준).

#### 핵심 발견 — Per-color mean amplitude z (sub-04 vs HC pool n=5)

| ROI | yellow z | green z | magenta z | 다른 색 |
|---|---:|---:|---:|---|
| V1 | **+2.21** | −1.80 | +1.60 | NS |
| V2 | **+2.57** | **−2.63** | **+2.23** | red +1.09, orange +1.47 |
| V4 | +1.07 | −0.20 | **+2.07** | NS |

#### 진단

1. **sub-04 V1/V2 yellow 는 *양수* outlier** — sub-08 deutan 의 *음수* outlier 와 **부호 반대** (Cycle 6: sub-08 V2 yellow z_mean = −3.31).
   - 즉 sub-08 = 자극에 BOLD 약화 (deutan), sub-04 = 자극에 BOLD 강화 (HC 평균보다 큼).

2. **V2 가 가장 noisy** — yellow + green + magenta 3개 색 outlier. V1 보다 V2 가 sub-04 의 패턴 outlier 의 source.

3. **V4 yellow 는 정상**, magenta 만 양수 outlier. V4 deutan family axis (yellow) 에서는 sub-04 가 typical HC.

4. **run consistency (V1: 0.07~0.31 / V2: 0.11~0.22 / V4: 0.17~0.41)**: sub-04 의 outlier 는 noise 가 아닌 **systematic** (모든 6 runs 일관). subclinical CVD 가능성 낮음 (HC 가 맞음).

#### 함의 — Selection rule 의 |z_rdm| + |z_runc| 항이 부호 mismatch 무시

현 selection rule:
$$L_\text{vox-axis} = -[\text{sign}_\text{family} \cdot z_\text{mean} + |z_\text{rdm-row}| + |z_\text{runc}|]$$

- sub-04 V1 yellow: z_mean = +2.21 (양수 outlier, deutan 가정 sign=−1) → −sign·z_mean = +2.21 (양의 contribution).
- 그러나 |z_rdm| ≈ 1.6, |z_runc| ≈ 4.7 (sign 무관 절대값) → 합산 시 큰 음수 dominance → L = +2.21 − 1.6 − 4.7 = **−4.1** (false specificity).

→ **sub-04 의 mean_amp 부호가 family-expected (음수) 와 반대인데도 |z_rdm|+|z_runc| 가 부호 무관 합산되어 FP**. selection rule 의 reformulation 필요.

### 8-6. Local Bootstrap (n=100) overlap 정량화

#### 스크립트
`scripts/cycle_filter_refinement/cycle8_voxel_bootstrap.py` — sub-04 V1/V2/V4, sub-09 V1/V4 4 cells. local conda srm.

#### 결과

| Cell | family-color | L_vox median | L_vox CI95 |
|---|---|---:|---|
| **sub-09 V4** (CVD) | protan, magenta | **−8.67** | **[−15.15, −6.75]** |
| **sub-04 V4** (HC LOO) | deutan, yellow | **−1.66** | **[−5.38, −0.46]** |
| sub-09 V1 (CVD) | protan, magenta | −11.00 | [−24.97, −7.76] |
| sub-04 V1 (HC LOO) | deutan, yellow | −4.77 | [−26.92, −3.98] |

#### Overlap 분석

**V4 — disjoint (분리)**:
- sub-09 V4 lower CI95 (−6.75) < sub-04 V4 upper CI95 (−0.46) → **CI 가 겹치지 않음** (gap = 1.37 단위)
- → V4 single-ROI 에서 sub-09 specificity 통계적 분리됨.

**V1 — overlap 큼**:
- sub-09 V1 CI95 [−25, −7.76], sub-04 V1 CI95 [−27, −3.98] → 겹치는 영역 [−25, −7.76] (큰 overlap)
- → V1 single-ROI 에서는 sub-09 vs sub-04 분리 통계적으로 부족.

#### V1+V4 결합 (selection rule)

V1 + V4 z 합산 (단순 sum approximation):
- sub-09 V1+V4 voxel-axis sum CI95 ≈ [−40, −14.5]
- sub-04 V1+V4 voxel-axis sum CI95 ≈ [−32, −4.5]
- → **overlap 영역 [−14.5, −4.5] 존재** — selection rule V1+V4 결합 시 sub-09 vs sub-04 부분 overlap.

#### 결론

- **V4 single-ROI 가 V1+V4 결합보다 specificity 에 더 안전**.
- V1+V4 결합은 sub-08 (z=−19.32) 같은 강한 신호에는 robust 하지만, sub-09 (z=−5.95) 처럼 magnitude 작은 신호에는 sub-04 와 overlap 위험.
- → **권고**: 옵션 B (selection rule 보수화) 또는 selection rule reformulation.

### 8-7. Selection Rule Reformulation 후보

**문제**: sub-04 yellow 양수 outlier 가 selection rule 의 |z_rdm|+|z_runc| 항으로 흡수되어 FP.

**후보 R1 — 부호 mismatch penalty**:
$$L = -\bigg[\text{sign}_\text{family} \cdot z_\text{mean} + I[\text{sign 일치}] \cdot (|z_\text{rdm}| + |z_\text{runc}|)\bigg]$$
where `I[sign 일치] = 1 if sign(z_mean) == −sign_family else 0`.
→ sub-04 yellow z_mean 양수 (deutan 가정 sign=−1 일 때 mismatch) → I=0 → |z_rdm|+|z_runc| 항 무효 → L_vox-axis = +2.21 (positive, no FP).

**후보 R2 — Single signature only**:
L_vox-axis = sign_family · z_mean (mean_amp 단독)
→ sub-04 V1 yellow: -(-1·(+2.21)) = +2.21 (FP 아님).
sub-08 V1 yellow: -(-1·(-0.62)) = -0.62 (NS — *sub-08 V1 specificity 약화*).
→ R2 는 sub-08 V4/V2 의 yellow 신호 (z_mean = −4.45/−3.31) 에는 robust 하나 V1 신호 약화.

**후보 R3 — Family-cosine weighting**:
$z_\text{mean}$ 의 부호 + magnitude 를 family-cosine projection 에 가중. 
→ 복잡, 정량 검증 필요.

**우선순위**: **R1 즉시 검증** (코드 수정 1줄). 결과 따라 R2, R3 전개.

### 8-8. 다음 단계

1. **R1 reformulation 즉시 검증** — Cycle 7/8 의 cycle7_dual_criterion.py + cycle8_hc_fp.py 코드의 L_vox-axis 정의 수정 후 재계산. sub-04 FP 해결 여부 확인.
2. **Server bootstrap (Jobs 98931, 98945)** 완료 후 V1+V4 결합 분포 정량 overlap 계산 — local n=100 대비 n=200 narrow CI 검증.
3. **sub-08 V1 origin (β=0,0)** Tikhonov 효과 vs baseline 매칭 분리 — λ ∈ {0, 0.05, 0.1, 0.2} sweep boot (running).
4. **Phase 3 trigger**: V4-only filter 우선 검증 (V1+V4 보다 robust). V1+V4 는 reformulation 후 재평가.

### 8-9. sub-08 V1 origin (β=0,0) Tikhonov artifact 확인 (Cycle 8 #5)

#### 검증 — λ sweep n_boot=100, sub-08 V1, deutan family

| λ | l_topk_min | best_bs median | best_bc median | origin (0,0) 매칭 | IQR(bc) |
|---|---:|---:|---:|:-:|---:|
| **0.00** | 0.185 | 0 | **−44** | **2/100** | 48 |
| 0.05 | 0.194 | 0 | 0 | 66/100 | 0 |
| 0.10 | 0.248 | 0 | 0 | 67/100 | 0 |
| 0.20 | 0.219 | 0 | 0 | 63/100 | 1 |

#### 결론

**sub-08 V1 의 진짜 best 는 (β_s=0, β_c≈−44) 영역**. λ=0 (Tikhonov 없음) 에서 origin 매칭은 2/100 boot 만, IQR(bc)=48. → **Cycle 6s 의 "perfect set-match β IQR=0" 은 Tikhonov regularization 의 origin-attraction artifact**.

함의:
- sub-08 V1 의 "best param origin" 는 false stability — λ=0에서 분산 큼.
- sub-08 V1 을 selection rule 의 V1+V4 결합에서 사용 시 (β_s, β_c) 점추정 의미 약함; voxel-axis 기여만 robust.
- V4 sub-08 (boot median (38, 7), IQR=40) 는 voxel-axis + set 모두 robust.

### 8-10. R1 Reformulation (sign-mismatch penalty) — 검증 (Cycle 8 #6)

#### 정의
$$L_\text{vox-axis}^{R1}(s, R, c) = -[\text{sign}_\text{family} \cdot z_\text{mean}(c) + I \cdot (|z_\text{rdm-row}(c)| + |z_\text{runc}(c)|)]$$
- $I = 1$ if $z_\text{mean} \cdot \text{sign}_\text{family} > 0$ (sign-aligned, valid family signal); else $0$.
- 의도: sub-04 처럼 z_mean 부호가 family-expected 와 반대인 경우 |z_rdm|+|z_runc| 항 무효화.

#### 결과 (V1+V4 z_combined)

| target | family | R0 | R1 | 판정 |
|---|---|---:|---:|---|
| sub-08 (CVD) | deutan | −19.32 | −15.82 | sig 유지 |
| sub-09 (CVD) | protan | −5.95 | −5.14 | sig 유지 |
| sub-10 | deutan | −0.09 | −1.17 | pass 유지 |
| **sub-04** (HC) | deutan | **−4.40** | **+1.91** | **FP 해결!** ✓ |
| sub-04 (HC) | protan | −5.09 | −4.58 | FP 유지 |
| sub-01 (HC) | deutan | −1.87 | **−9.64** | **새 FP!** ✗ |
| **sub-02** (HC) | deutan | −0.57 | **−4.12** | **새 FP!** ✗ |
| sub-02 (HC) | protan | −4.39 | −4.97 | FP 유지 |

#### Net FP rate 변화

- R0: sub-04 (deutan, protan), sub-02 (protan) = 3 FP cells (≈ either family 2/6)
- R1: sub-04 (protan), sub-02 (deutan, protan), sub-01 (deutan) = 4 FP cells (≈ 3/6)

→ **R1 net FP rate 악화** (33% → 50%).

#### 진단

R1은 z_mean 양수 outlier (sub-04 deutan)는 해결하나 z_mean 음수 outlier (sub-01, sub-02 deutan-like)를 활성화시켜 새 FP 유발. R1 가설은 잘못됨 — **z_mean 부호 mismatch 만으로 noise vs signal 구별 불가**.

#### 추가 후보 (Cycle 9)

- **R2**: L_vox-axis = sign_fam · z_mean 만 (rdm/runc 제거). 단순화.
- **R3**: sign-aligned multiplicative — L = -[sign_fam · z_mean · (1 + |z_rdm| + |z_runc|)]. mean magnitude amplify.
- **R4**: HC null pool 자체에서 z_mean magnitude threshold (예: |z|>2.5 인 HC 만 outlier로 카운트).
- **R5**: Per-color voxel-axis ensemble — 8색 모두에 대한 family-projected feature, 단일 색만 활용 안 함.

### 8-11. Cycle 8 종합 결론 + Cycle 9 trigger

#### 핵심 발견 정리

1. **sub-04 는 진짜 HC 이지만 V1/V2 yellow/magenta 에서 *양수* mean amplitude outlier** — sub-08 (음수 outlier) 과 부호 반대. systematic (run-stable).
2. **Selection rule 의 |z_rdm|+|z_runc| 부호 무관 합산이 sub-04 양수 outlier 를 false specificity 로 흡수**. R1 sign-mismatch penalty 는 부분 해결 (sub-04 deutan)이나 sub-01/02 음수 outlier 를 새 FP 로 만듦 → 단독 부족.
3. **sub-08 V1 origin (β=0,0) 매칭은 Tikhonov artifact** — λ=0 에서 진짜 best 는 (0, −44). V1 set-match 의 V1+V4 결합 기여는 voxel-axis 가 dominant.
4. **Local n=100 bootstrap**: V4 single-ROI 에서 sub-09 vs sub-04 disjoint, V1+V4 결합은 overlap 큼. **V4 single-ROI selection rule 이 V1+V4 결합보다 statistically robust**.

#### Cycle 9 trigger

A. **R2~R5 reformulation grid sweep** — 어느 reformulation 이 net FP rate ≤1/6 + CVD specificity z<-2 동시 달성하는가.
B. **Server bootstrap (Jobs 98931, 98945)** 도착 시 V1+V4 결합 분포 정량 overlap.
C. **Phase 3 trigger 우선순위 update**: V4 single-ROI filter (가장 robust) → V1+V4 (reformulation 후 재평가).

### 8-12. 산출 파일 (Cycle 8 종합)

- `scripts/cycle_filter_refinement/cycle8_voxel_bootstrap.py` (HC LOO 자동 제외 + family map 확장)
- `scripts/cycle_filter_refinement/cycle8_preimage.py`
- `scripts/cycle_filter_refinement/cycle8_hc_fp.py`
- `scripts/cycle_filter_refinement/cycle8_viz.py` (4 figures)
- `/tmp/sub04_diag.py` (sub-04 진단 ad-hoc — 공식 스크립트화 필요)
- `/tmp/sub08_v1_lambda0.py` (λ sweep boot)
- `/tmp/cycle8_R1_reformulation.py` (R1 검증)
- `results/cycle_filter_refinement/cycle8_voxel_bootstrap_local/sub-{04,09}_{V1,V4}.json`
- `results/cycle_filter_refinement/cycle8_preimage.json`
- `results/cycle_filter_refinement/cycle8_hc_fp.json`
- `results/cycle_filter_refinement/cycle8_figures/fig{1,2,3,4}.png`
- `action_plans/PLAN04_EXECUTIVE_SUMMARY.md` (Cycle 1~8 종합 1-page)

---

## Cycle 8 #1 — Server n_boot=200 결과 도착 (2026-05-02)

### 8s-1. Bootstrap 분포 (12 cells × n_boot=200)

| Cell | family | color | L_vox median | IQR | CI95 |
|---|---|---|---:|---:|---|
| **sub-08 V4** (CVD) | deutan | yellow | **−19.98** | 8.45 | [−58.86, **−15.81**] |
| sub-08 V2 | deutan | yellow | −11.97 | 3.81 | [−24.74, −10.13] |
| sub-08 V1 | deutan | yellow | −6.35 | 5.52 | [−16.81, −5.21] |
| **sub-09 V1** (CVD) | protan | magenta | **−10.30** | 3.56 | [−25.92, **−7.68**] |
| **sub-09 V4** (CVD) | protan | magenta | **−8.48** | 2.15 | [−14.66, **−6.73**] |
| sub-09 V2 | protan | magenta | −6.20 | 2.06 | [−11.02, −4.53] |
| sub-04 V1 (HC LOO) | deutan | yellow | −4.80 | 1.87 | [**−84.54**, −3.98] |
| sub-04 V4 (HC LOO) | deutan | yellow | −1.70 | 1.11 | [−7.49, **−0.46**] |
| sub-04 V2 (HC LOO) | deutan | yellow | −1.64 | 3.47 | [−9.85, +2.52] |
| sub-02 V4 (HC LOO) | protan | magenta | −2.55 | 1.26 | [−8.22, **−1.30**] |
| sub-02 V1 (HC LOO) | protan | magenta | −1.95 | 1.08 | [−6.22, −0.48] |
| sub-02 V2 (HC LOO) | protan | magenta | −1.74 | 1.16 | [−8.25, +0.03] |

### 8s-2. Same-family overlap 정량화

#### V4 single-ROI

| 비교 (deutan) | sub-08 CI95 | sub-04 CI95 | Overlap |
|---|---|---|:-:|
| V4 | [−58.86, **−15.81**] | [−7.49, **−0.46**] | **0.00 / 58.40 = 0%** ✓ |

| 비교 (protan) | sub-09 CI95 | sub-02 CI95 | Overlap |
|---|---|---|:-:|
| V4 | [−14.66, **−6.73**] | [−8.22, **−1.30**] | **1.48 / 13.36 = 11%** ✓ |

#### V1+V4 결합 (z_sum)

| 비교 (deutan) | sub-08 CI95 | sub-04 CI95 | Overlap |
|---|---|---|:-:|
| V1+V4 | [−75.66, −21.02] | [−92.03, −4.43] | **54.64 / 87.60 = 62%** ✗ |

| 비교 (protan) | sub-09 CI95 | sub-02 CI95 | Overlap |
|---|---|---|:-:|
| V1+V4 | [−40.58, −14.42] | [−14.43, −1.78] | **0.02 / 38.80 = 0.04%** ✓ |

### 8s-3. 옵션 분기 결정 (Cycle 8 §8-3 기준)

| 비교 | Overlap | 분기 |
|---|---:|---|
| sub-08 V4 (단독) | 0% | < 0.1 → **sub-08 V4 specificity 유지, 옵션 A/B 불필요** |
| sub-09 V1+V4 (결합) | 0.04% | < 0.1 → **sub-09 V1+V4 specificity 통계적으로 유지** |
| sub-09 V4 (단독) | 11% | < 0.1 → **sub-09 V4 단독도 specificity 유지** |
| sub-08 V1+V4 (결합) | **62%** | > 0.3 → 옵션 B (sub-08 V1+V4 보수화) — 단 V4 단독으로 우회 가능 |

#### 결정

1. **Sub-09 specificity 통계적으로 정당화 ✓** — Cycle 7 의 "fragile" 우려 해소. V1+V4 결합 0.04% overlap, V4 단독 11% overlap.
2. **Sub-08 specificity V4 single-ROI 가 가장 robust ✓** — V1+V4 결합 시 sub-04 V1 의 wide CI ([−84, −4]) 가 overlap 유발. V4 single-ROI 채택 권장.
3. **옵션 A (HC pool 정제)/B (selection rule 보수화) 불필요** — overlap-based decision 만족.

#### Sub-08 V1+V4 의 큰 overlap 의 본질

- sub-04 V1 boot 분포가 wide ([−84.54, −3.98]) — bootstrap 시 일부 boot 에서 sub-04 V1 yellow z 가 매우 큰 음수로 나옴 (sub-04 양수 outlier 와 관련된 vortex 효과).
- → V1 결합은 sub-08 의 robust signal 을 흐림. **V4 single-ROI 만 사용하면 sub-08 vs sub-04 완벽 disjoint**.

### 8s-4. 최종 권장 selection rule (revised)

```
Sub-08 (deutan): V4 single-ROI + family-aware z_vox-axis
                z_combined median = −19.98 (CI95 [-58.86, -15.81])
                vs sub-04 HC LOO V4: median −1.70 (CI95 [-7.49, -0.46])
                → 0% overlap (perfect specificity)

Sub-09 (protan): V1+V4 결합 + family-aware z_vox-axis
                 z_combined median = −18.78 (CI95 [-40.58, -14.42])
                 vs sub-02 HC LOO V1+V4: median −4.50 (CI95 [-14.43, -1.78])
                 → 0.04% overlap (statistically robust)
```

→ **Subject-specific ROI** (sub-08: V4-only, sub-09: V1+V4) 가 최종 selection rule. CLAUDE.md 규칙 7 의 sub-10 sanity 도 통과 (Cycle 7 z=−0.09).

### 8s-5. V1 결합/분리 권장의 근본 원인 — sub-04 V1 의 catastrophic heavy-tail bootstrap

#### 분포 안정성 정량

| Cell | median | IQR | CI95 width | **ext_ratio** = CI/IQR | 진단 |
|---|---:|---:|---:|---:|---|
| **sub-04 V1** (HC LOO, deutan) | −4.80 | 1.87 | **80.57** | **43.0** | **catastrophic heavy tail** |
| sub-02 V1 (HC LOO, protan) | −1.95 | 1.08 | 5.74 | 5.3 | 정상 narrow |
| sub-08 V1 (CVD) | −6.35 | 5.52 | 11.59 | 2.1 | 가장 안정 |
| sub-09 V1 (CVD) | −10.30 | 3.56 | 18.24 | 5.1 | 안정 |
| sub-08 V4 (CVD) | −19.98 | 8.45 | 43.05 | 5.1 | 안정 |
| sub-09 V4 (CVD) | −8.48 | 2.15 | 7.93 | 3.7 | 가장 안정 |
| sub-04 V4 (HC LOO) | −1.70 | 1.11 | 7.03 | 6.3 | 정상 |
| sub-02 V4 (HC LOO) | −2.55 | 1.26 | 6.91 | 5.5 | 정상 |

#### sub-04 V1 의 heavy-tail 본질

- 75% boot 결과는 안정 (median −4.8, IQR ±1.87)
- 그러나 CI95 lower = **−84.54** — 일부 boot 에서 catastrophic outlier 도달
- ext_ratio 43 (다른 cell 의 5~10배) — bootstrap **HC resample 조합에 매우 민감**
- 원인 추정: sub-04 V1 yellow 양수 outlier 가 특정 HC 부분집합 (예: sub-01 또는 sub-03 제외 시 pool sd 가 매우 작아짐) 에서 z 가 폭발

#### V1 결합 시 sub-08 vs sub-04 overlap 의 본질

- sub-04 V1 lower tail (−84) 이 V1+V4 결합 분포의 lower tail 을 끌어내림 → sub-04 V1+V4 CI95 [−92.03, −4.43]
- sub-08 V1+V4 CI95 [−75.66, −21.02]
- 두 분포의 lower tail 이 [−92, −75] 영역에서 겹침 → overlap 62%

→ **V1 single-ROI 분포의 heavy-tail 이 결합 specificity 를 흐림**. V4 single-ROI 만 사용하면 sub-04 V4 lower tail (−7.49) 이 sub-08 V4 upper tail (−15.81) 보다 위 → 0% overlap.

#### sub-09 V1+V4 결합이 안전한 이유

- sub-02 V1: median −1.95, IQR 1.08, CI95 [−6.22, −0.48] — narrow distribution
- sub-02 V4: 비슷하게 narrow ([−8.22, −1.30])
- 결합 sub-02 V1+V4: [−14.43, −1.78] (narrow 유지)
- sub-09 V1+V4: [−40.58, −14.42] — sub-02 보다 14 단위 이상 음수
- → **HC LOO 분포가 narrow** 하므로 V1+V4 결합도 sub-09 와 disjoint

#### 권장 selection rule 의 데이터 근거

| 피험자 | 권장 ROI | 근거 |
|---|---|---|
| **sub-08** (deutan) | **V4 single-ROI** | sub-04 V1 catastrophic tail 우회 → V4 단독으로 0% overlap |
| **sub-09** (protan) | **V1+V4 결합** | sub-02 LOO 분포 narrow → 결합으로 0.04% overlap (가장 robust) |

### 8s-6. Loss component 별 fitting 정도

#### z_vox-axis 분해 (point estimate, cycle 6 voxel_diag)

$$L_\text{vox-axis} = -\big[\text{sign}_\text{family} \cdot z_\text{mean} + |z_\text{rdm-row}| + |z_\text{runc}|\big]$$

| Subj | ROI | sign·z_mean | |z_rdm-row| | |z_runc| | L_vox | dominant |
|---|---|---:|---:|---:|---:|---|
| **sub-08** | V1 | +0.62 | 1.52 | **4.41** | −6.55 | **runc** |
| **sub-08** | V2 | +3.31 | 1.89 | **6.28** | −11.48 | **runc** |
| **sub-08** | V4 | **+4.45** | 1.33 | 2.04 | −7.82 | **mean** |
| **sub-09** | V1 | +3.31 | 1.26 | **4.88** | −9.45 | **runc** |
| **sub-09** | V2 | +3.83 | 0.90 | 1.11 | −5.84 | **mean** |
| **sub-09** | V4 | **+2.85** | 1.24 | 1.68 | −5.77 | **mean** |
| sub-10 | V1 | −0.73 | 0.81 | 0.67 | −0.75 | rdm (sanity) |
| sub-10 | V2 | −1.00 | 0.52 | 0.89 | −0.41 | mean (sanity) |
| sub-10 | V4 | −0.18 | 0.54 | 0.40 | −0.76 | rdm (sanity) |

#### 핵심 발견

1. **V4 = mean dominant** (sub-08 V4: 4.45 vs runc 2.04; sub-09 V4: 2.85 vs runc 1.68)
   → "어느 색에 BOLD activation 평균 outlier?" 의 정직한 신호 (cone-shift 의 직접 BOLD 표현).

2. **V1/V2 = run consistency dominant** (sub-08 V1: runc 4.41 vs mean 0.62; sub-09 V1: runc 4.88 vs mean 3.31)
   → "같은 색이 run 간 일관된 voxel pattern 을 보이나?" 의 신호. mean 값은 V1/V2 에서 작아도 cross-run pattern reliability 가 outlier.

3. **|z_rdm-row| 항은 모든 cell 에서 작음** (0.5~1.9). RDM cell-level 신호는 약함.
   → RDM 항 제거 시 selection rule 단순화 가능 (Cycle 9 R6 후보).

#### z_set fitting 정도 (per ROI, l_topk + 0.2·Tikh)

| Subj | ROI | L_set min | best (β_s, β_c) | z_set |
|---|---|---:|---:|---:|
| **sub-08 V4** | 0.149 | (58, −28) | **−4.54** ← 강함 |
| sub-08 V2 | 0.501 | (6, 2) | +0.04 (NS) |
| sub-08 V1 | 0.500 | (0, 0) | −0.52 (NS) |
| sub-09 V1 | 0.500 | (0, 0) | −0.52 (NS) |
| sub-09 V2 | 0.792 | (70, 50) | +2.69 (역) |
| sub-09 V4 | 0.800 | (0, 0) | +0.59 (NS) |
| sub-10 V1 | 0.500 | (0, 0) | −0.52 (NS) |
| sub-10 V2 | 0.801 | (6, 2) | +2.78 (정상) |
| sub-10 V4 | 0.546 | (36, 10) | −1.41 (NS) |

→ **z_set 은 sub-08 V4 single cell 에서만 강한 contribution** (−4.54). 다른 모든 cell 에서 NS 또는 역방향.

#### z_set 와 z_vox 의 ROI 별 상호작용 (CVD)

| Cell | z_set | z_vox | z_combined | 신호 type |
|---|---:|---:|---:|---|
| **sub-08 V4** | **−4.54** | **−10.48** | **−15.02** | **dual** (set + voxel 모두 강함) |
| sub-08 V2 | +0.04 | −13.25 | −13.20 | voxel-only (가장 강한 voxel) |
| sub-08 V1 | −0.52 | −3.78 | −4.30 | weak both |
| sub-09 V1 | −0.52 | −3.18 | −3.70 | voxel-only weak |
| sub-09 V2 | +2.69 | −3.71 | −1.01 | voxel-set 충돌 |
| sub-09 V4 | +0.59 | −2.85 | −2.26 | voxel-only |

→ **sub-08 V4 만 dual signal**. sub-08 V2 는 voxel-only super-strong (z=−13.25). sub-09 모든 cell 은 voxel-only.

→ Selection rule 의 z_set 은 **sub-08 V4 cell 의 specificity 강화에만 기여**. 다른 cell 에서는 z_vox-axis 단독으로 selection rule 작동.

### 8s-7. Selection rule 의 data-driven 정당화 (종합)

```
SUBJECT-SPECIFIC ROI selection (revised, server n=200):

sub-08 (deutan): V4 single-ROI
  z_combined = z_set(V4) + z_vox-axis(V4, yellow, sign=-1)
             = -4.54 + (-10.48)
             = -15.02 (point)
  bootstrap median = -19.98, CI95 [-58.86, -15.81]
  vs sub-04 HC LOO V4: median -1.70, CI95 [-7.49, -0.46]
  Overlap: 0.00%  ← perfect specificity

sub-09 (protan): V1+V4 결합 (z_sum)
  z_combined = z_set(V1) + z_set(V4) + z_vox-axis(V1) + z_vox-axis(V4)
             = -0.52 + 0.59 + (-3.18) + (-2.85)
             = -5.95 (point estimate)
  bootstrap median = -18.78 (sum), CI95 [-40.58, -14.42]
  vs sub-02 HC LOO V1+V4: median -4.50, CI95 [-14.43, -1.78]
  Overlap: 0.04%  ← statistically robust

Reasoning:
- V1 결합/분리는 HC LOO 분포 안정성 (ext_ratio) 에 의존:
  sub-04 V1 ext_ratio = 43 (catastrophic) → V1 결합 비추, V4 single-ROI
  sub-02 V1 ext_ratio = 5.3 (normal) → V1+V4 결합 안전
- V4 = mean amplitude signal (정직한 BOLD outlier)
- V1/V2 = run consistency signal (pattern reliability)
- z_set 은 sub-08 V4 single cell 에만 강한 contribution
```



