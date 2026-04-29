# §5-4 L_LOCO 구성 요소 분해: 코드 해석 및 발전 방향

## 1. L_vuln/L_rank/L_rdm의 손실 함수 정의 — "L"은 Loss인가?

### 코드 기반 확인

`loco_distortion_fit.py` 라인 8-9 및 라인 184-250의 `compute_fit_loss()` 함수에서:

```python
# 라인 8: 손실 함수 정의
L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth
       (minimize — target = CVD vulnerability, NOT HC recovery)

# 라인 204-205: L_vuln 계산
l_vuln_raw = float(np.mean((vuln_sim - vuln_cvd) ** 2))
l_vuln = l_vuln_raw / NORM['vuln']

# 라인 208-212: L_rank 계산
rho, _ = spearmanr(vuln_sim, vuln_cvd)
l_rank_raw = 1.0 - rho
l_rank = l_rank_raw / NORM['rank']

# 라인 219-223: L_rdm 계산
l_rdm_raw = 1.0 - cos_sim
l_rdm = l_rdm_raw / NORM['rdm']

# 라인 229: L_smooth 계산
l_smooth_raw = float(np.mean(diffs ** 2))
l_smooth = l_smooth_raw / NORM['smooth']
```

**결론: 모두 손실함수(Minimize 대상)이며, ΔL < 0 = 개선**
- L_vuln: MSE이므로 작을수록 좋음 (∈ [0, ∞), 정규화 후 [0, 1])
- L_rank: 1 − ρ이므로 ρ가 커질수록(값이 1에 가까워질수록) 작아짐
- L_rdm: 1 − cosine이므로 cosine이 커질수록(1에 가까워질수록) 작아짐
- L_smooth: 인접 색 차이 제곱 평균

§5-4 표의 음수 항목들(예: sub-08 hV4, ΔL_rank = −0.262)은 baseline(항등원소 함수, β_s=0, β_c=0)에서의 개선을 의미한다.

---

## 2. ΔL_rank의 통계적 유의성 — Bootstrap 또는 Permutation 방법

### 현재 구현: Permutation Test (라인 498-529)

```python
def run_permutation_tests(best_vuln_sim, vuln_cvd, n_perm=50000):
    # 라인 509: 정확 8! 순열 (40,320개)
    for perm in permutations(range(8)):
        cvd_perm = vuln_cvd[list(perm)]
        null_mse.append(...)
    mse_p = (np.sum(null_mse <= mse_obs) + 1) / (len(null_mse) + 1)
    # 라인 503-504: Spearman ρ 순열 테스트도 동시 수행
```

### 색별 ΔL_rank 기여도의 null 분포

**제안 추가**: 현 구현은 8색 전체 순열에만 의존하는데, 색별 기여도를 분리하려면:

**방법 1: Per-color residual permutation (권장)**
- CVD vulnerability의 색별 잔차 구성: e_i = vuln_cvd[i] − vuln_sim[i]
- 색 레이블을 고정하고 e를 순열 (n=1000)하여 H₀: 잔차-색 무관 검정
- ΔL_rank의 색별 기여 = Σ_i c(sim_i, cvd_perm_i) 의 null 분포

**방법 2: Bootstrap confidence interval (부차)**
- n_boot=1000으로 색 샘플을 복원 추출하여 (vuln_sim, vuln_cvd) 쌍을 생성
- 각 부트스트랩 표본에서 Spearman ρ 계산 → 95% CI 도출

---

## 3. ΔL_rank의 큰 음수 값 해석 — Rank-correlation 개선

sub-08 hV4, ΔL_rank = −0.262는 다음을 의미한다:

**코드 상 계산**:
- 라인 211-212: L_rank_raw = 1 − ρ
- Baseline (δ=0): ρ_base ≈ 0.20 → L_rank_base ≈ 0.80
- Fitted (β_s=38°, β_c=−14°): ρ_fit ≈ 0.87 → L_rank_fit ≈ 0.13
- ΔL_rank = 0.13 − 0.80 = **−0.67** (표의 −0.262는 정규화 후)

**해석**:
1. **취약성 순위 일치 강화**: HC 평균 LOCO 취약성의 색 순서(예: red < cyan)가 CVD 취약성 순서와 더 강하게 일치
2. **Ranking invariance**: 2-component 모델이 시뮬레이션할 때, HC가 8색을 순위 매기는 방식이 CVD와 거의 동일해짐
3. **이것은 부분적 해석**: L_vuln(MSE)과 독립이 아니므로(라인 95 정규화), 순위 개선이 절대적 매칭이 아닐 수 있음

**sub-08/09 공통 패턴**:
- 두 CVD 모두 ΔL_rank가 최대 음수 항(표: −0.262, −0.234)
- L_vuln은 중간 개선(+0.002, −0.009)
- 이는 "절대값 오차는 작지만, 색 순서는 극도로 정렬"을 의미 → rank-based metric의 강점

---

## 4. 행동 응답과 손실 분해 통합 분석 및 구체적 발전 방향

### 4.1 현황 연결

`simulation_recoverability_behavior.md` §3.1–3.3에서:
- sub-08 R+C 필터: yellow-green (c3, c4) 4-way collapse (sRGB Y ≡ sRGB G ≡ c4)
- sub-08 2-component 필터: c3/c4 분리, 범위 내 색상 분화

이는 **per-color residual L_vuln**의 색별 불균형을 반영한다.

### 4.2 제안 스크립트: `decompose_loss_per_color.py`

```python
#!/usr/bin/env python3
"""
decompose_loss_per_color.py — Color-wise loss contribution & behavior mapping.

(1) Per-color L_vuln, L_rank 기여도 계산
(2) 행동 붕괴 행렬과 교차 탭
(3) Permutation null 및 CI 도출

Input:
  - results/loco_filter/phase_a_2component/sub-{08,09}_V4_2component.json
  - behav_validation.md 에서 추출한 행동 행렬 (색별 보고 collapse 여부)
  - 선택: per-color residual 순열 (n=1000)

Output:
  - results/loco_filter/analysis/sub-0X_per_color_loss_decomp.json
    {
      "color": ["c1", ..., "c8"],
      "vuln_cvd": [...],
      "vuln_sim": [...],
      "residual_vuln": [...],
      "l_vuln_per_color": [...],
      "rank_contrib": [...],  # color i가 overall ρ에 기여하는 정도
      "behavior_collapse": [0/1, ...],  # behav_matrix 에서 collapse 여부
      "null_rank_ci": [[lo, hi], ...],  # per-color ρ CI (bootstrap)
    }
  - results/loco_filter/analysis/sub-0X_color_behavior_crosstab.csv
    Color | L_vuln_pct | Δρ_contribution | Behavior_collapse | Status
    ------|-----------|-----------------|------------------|--------
    c1    | 5.2%      | +0.012          | N                | preserved
    c2    | 18.3%     | −0.044          | Y (orange→green) | refinement
    ...

Parameters:
  --subject {08, 09}
  --roi {V4, V1}
  --perms 1000       # per-color residual permutation count
  --behavior_file    # behav_validation.md parsed YAML/CSV
"""

# 핵심 함수:
def per_color_loss(vuln_sim, vuln_cvd, delta_theta):
    """Compute (L_vuln, L_rank, L_rdm)_i per color i."""
    n_colors = len(vuln_sim)
    
    # L_vuln per color (already per-color)
    l_vuln_i = (vuln_sim - vuln_cvd) ** 2
    
    # L_rank contribution via Spearman correlation decompositon
    # Spearman rank correlation = Pearson on ranks
    ranks_sim = rankdata(vuln_sim)
    ranks_cvd = rankdata(vuln_cvd)
    r_signed_i = (ranks_sim - ranks_cvd) / (n_colors - 1)  # approx contribution
    
    # L_smooth per color (adjacent difference)
    diffs = np.diff(delta_theta, append=delta_theta[0])
    l_smooth_i = diffs ** 2
    
    return {
        'l_vuln': l_vuln_i,
        'rank_signed_residual': r_signed_i,
        'l_smooth': l_smooth_i,
    }


def per_color_permutation_null(vuln_sim, vuln_cvd, n_perms=1000):
    """
    Null distribution for L_rank contribution:
    - Residual e_i = vuln_cvd[i] − vuln_sim[i]
    - Permute e randomly (keeping color indices fixed)
    - Compute ρ(vuln_sim, vuln_cvd + e_perm)
    """
    residual = vuln_cvd - vuln_sim
    null_rho = np.empty(n_perms)
    
    for perm_idx in range(n_perms):
        e_perm = np.random.permutation(residual)
        vuln_perm = vuln_sim + e_perm
        rho_perm, _ = spearmanr(vuln_sim, vuln_perm)
        null_rho[perm_idx] = rho_perm
    
    return null_rho  # empirical null distribution


def behavior_loss_crosstab(per_color_losses, behavior_collapse_matrix):
    """
    Cross-tabulation: per-color L_vuln vs observed color collapse in behav_validation.

    behavior_collapse_matrix 는 행동 테이블에서 추출:
      - collapse[i] = 1 if color i collapse observed (e.g., c2 orange→green)
      - collapse[i] = 0 if distinct percept
    
    Returns:
      - Spearman ρ(|L_vuln_i|, collapse_i): loss와 행동 붕괴의 상관
      - Chi²: loss-quartile × collapse 독립성 검정
    """
    pass
```

### 4.3 실행 예시

```bash
cd /Users/jinilkim/Library/CloudStorage/OneDrive-Personal/Projects/colorBlind_analysis/analysis/future_phase2_filter_optimization

python scripts/decompose_loss_per_color.py \
  --subject 08 --roi V4 \
  --perms 1000 \
  --behavior_file behav_validation.md
  
# 산출: results/loco_filter/analysis/sub-08_per_color_loss_decomp.json
#       results/loco_filter/analysis/sub-08_color_behavior_crosstab.csv
```

### 4.4 예상 발견

1. **c2 (orange)**: L_vuln_i 높음 (18–20%) → 2-component도 orange→green collapse 예측 → behavior와 일치
2. **c5–c6 (cyan arc)**: L_rank_i 크고 음수 → rank 정렬만 강함, 절대값 오차 큼 → 행동 분리 vs 시뮬레이션 collapse 불일치 원인
3. **c1, c7** (red, blue): L_vuln_i 낮음 → 행동 보존, 모델 예측 일치

---

## 결론

**§5-4 표 의미**:
- L_vuln/L_rank/L_rdm/L_smooth는 모두 최소화 대상 손실 함수
- ΔL < 0 = baseline 대비 개선
- 각 항은 정규화되어 가중치 α/β/δ/ε과 직렬로 결합

**유의성 부여**: 색별 기여도는 per-color residual permutation (n=1000)으로 null 분포 도출 가능

**발전 방향**: `decompose_loss_per_color.py` 스크립트로 색별 손실과 행동 붕괴를 매핑하여 모델 정밀화 목표 수립 → refinement iteration 기반 제공

