# Q3: colorBlind_analysis의 Permutation Test 설계 분석

## 1. 셔플되는 라벨 (Label Shuffle)

**CVD vulnerability 기반 Permutation**
- **셔플 대상: Color label (8개 색상)**
- 정확히 8! = 40,320개의 모든 순열을 정확히(exact) 수행
- 코드 근거:
  - `step1_fit_loco_v2.py:283-287`: `permutations(range(8))`로 8개 색상 라벨을 모두 순열
  - `cvd_vuln[list(perm)]`로 CVD 취약성 벡터의 색상 순서만 변경
  - Run label, voxel, fold는 셔플되지 않음

**ΔRDM 기반 Permutation**
- `comprehensive_2component_analysis.py:324-331`: 8×8 RDM의 행과 열을 동일하게 순열
- 28개 색쌍(pair)의 순서가 재배치됨
- 8! 정확 순열 사용

## 2. 비교되는 통계량

### LOCO Vulnerability 피팅 (기본)
- **Spearman ρ** (`step1_fit_loco_v2.py:275`): 
  - 관찰값: `rho_obs = spearmanr(hc_vuln_fitted, cvd_vuln)`
  - 프로파일 매칭(level-independent) 기준
  
- **MSE** (`loco_distortion_fit.py:507-513`):
  - MSE 관찰값: `mse_obs = mean((best_vuln_sim - cvd_vuln)²)`
  - 색상 라벨 순열 null 분포와 비교

### ΔRDM 기반 (2-Component 모델)
- **Cosine similarity** (`comprehensive_2component_analysis.py:272`):
  - `cos_val = cosine_similarity(drdm_sim, delta_rdm_obs)`
  - 28개 색쌍 벡터의 코사인 유사도
  
- **WUC (Whitened Unbiased Cosine)** (`comprehensive_2component_analysis.py:277`):
  - Covariance-정규화된 코사인 (Diedrichsen et al. 2020)

## 3. 두 가지 Permutation 변형

### 변형 1: LOCO Vulnerability Permutation (Label-based)
- **적용 대상**: 모든 모델 (Machado 1-way, R+C, 2-Component, Fourier)
- **셔플**: `cvd_vuln[list(perm)]` — 색상 순서만 변경
- **통계량**: Spearman ρ 또는 MSE
- **코드**: `step1_fit_loco_v2.py:262-298`, `loco_distortion_fit.py:498-530`
- **격자 검색과의 관계**: 
  - 최적 파라미터 결정 후 해당 `vuln_sim`에 대해 post-hoc 검사
  - 격자 검색의 모든 점에 대해 null을 재계산하지 않음 (single best-point test)

### 변형 2: ΔRDM Permutation (28-pair vectorized)
- **적용 대상**: 2-Component, V1/V2 분석
- **셔플**: `square_v1[np.ix_(perm, perm)]` — 8×8 RDM 행/열 동시 순열
- **통계량**: cosine 또는 WUC similarity
- **코드**: `comprehensive_2component_analysis.py:305-359` (8! 정확), `l3_loss.py:310-322` (V1+V2 joint)
- **격자 검색과의 관계**:
  - 단순 8! label permutation 사용 → multi-comparison 보정 미시행
  - MaxStat 검사 (`maxstat_permutation_test`, 362-422행)는 선택적

## 4. P-value 정의

### 표준 정의: Conventional (count + 1) / (N + 1)
```python
# Spearman permutation
p = (np.sum(null >= rho_obs) + 1) / (len(null) + 1)
  # step1_fit_loco_v2.py:297

# MSE permutation (lower is better)
p = (np.sum(null <= mse_obs) + 1) / (len(null) + 1)
  # step1_fit_loco_v2.py:391

# ΔRDM cosine
perm_p_cos = float(np.mean(null_cos >= observed_cos))
  # comprehensive_2component_analysis.py:344 (1/N format, +1 없음)

# L₃ (V1+V2 joint)
label_perm_p = (np.sum(null_l3 >= obs_l3) + 1) / (len(null_l3) + 1)
  # l3_loss.py:321-322
```

**주목**: 
- LOCO (Spearman/MSE) 및 L₃: `(count + 1) / (N + 1)` ✓
- ΔRDM cosine: `mean(null ≥ obs)` (보수적이지 않음) ⚠

## 5. HC Specificity Test (`hc_specificity_test.py`)와 독립성

**별개의 permutation 체계**
- 동일한 `grid_search()`, `optimize_de()`, `run_permutation_tests()` 함수 사용
- **차이점**:
  - HC specificity: LOO (Leave-One-Out) 풀에서 재계산
  - CVD 피팅: 전체 7명 HC 풀 사용
  - 라벨 셔플은 동일하나, 대상 vulnerability가 다름 (HC pseudo-CVD vs. 실제 CVD)

**설정 동기화**: `hc_specificity_test.py:86-94`에서 모델과 가중치를 하드코딩

## 6. 2-Component 격자 검색과 Permutation의 다중비교 문제

### 관찰된 설계
```python
# Grid search: (β_s, β_c) 격자 탐색
landscape = []  # 101 × 101 = 10,201 점
for bs, bc in grid:
    cos_val = cosine_similarity(drdm_sim(bs, bc), delta_rdm_obs)
    # 최대값 선택
best_cos = max(landscape['cosine'])
best_params = argmax(landscape['cosine'])

# Permutation: 최적점에서만 post-hoc
C_shifted = two_component_design_matrix(best_bs, best_bc, ...)
drdm_sim_best = compute_delta_rdm_sim(...)
perm_p = permutation_test_8factorial(drdm_sim_best, drdm_obs)
  # comprehensive_2component_analysis.py:254-269
```

### 다중비교 보정 여부
| 방법 | 구현 | 상태 |
|-----|------|------|
| **단순 8! label perm** | ✓ | 기본값 |
| **MaxStat correction** | ✓ 선택적 | `maxstat_permutation_test()` |
| **FDR / Bonferroni** | ✗ | 미시행 |

**해석**: 
- 격자의 최대값 → permutation null 계산 시 **multi-comparison 인플레이션** 위험
- 보정 없이는 p-value가 낙관적 (Type I 오류 상향)
- MaxStat 함수는 이를 보정하나, 기본 pipeline에서는 선택적

---

## 요약

| 항목 | 설명 |
|-----|------|
| **라벨** | 8개 색상 (8! = 40,320 정확 순열) |
| **LOCO 통계량** | Spearman ρ 또는 MSE |
| **ΔRDM 통계량** | cosine 또는 WUC |
| **LOCO p-value** | (count + 1) / (N + 1) |
| **ΔRDM p-value** | mean(null ≥ obs) 또는 (count+1)/(N+1) |
| **HC 독립성** | 함수 재사용, 데이터 독립 ✓ |
| **다중비교** | 격자→permutation 간 보정 미흡 ⚠ |

**파일 인용**
- `step1_fit_loco_v2.py:262-298` — Spearman permutation
- `loco_distortion_fit.py:498-530` — MSE/Spearman (post-fit)
- `comprehensive_2component_analysis.py:305-359` — ΔRDM 8! label permutation
- `l3_loss.py:246-351` — V1+V2 joint permutation with regularisation
- `hc_specificity_test.py:154-299` — LOO-based specificity test
