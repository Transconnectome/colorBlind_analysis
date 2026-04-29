# hV4 LOCO ρ Bootstrap 및 신뢰구간 추적

## 질문

future_phase2_filter_optimization 폴더에서:
1. 핵심 모델 적합 결과(ρ = Spearman/Pearson correlation)의 bootstrap 분포 산출 여부
2. 신뢰구간(CI) 결과 저장 위치
3. 부재시 추가 방법 및 자원 소요

---

## 1. 기존 Bootstrap 구현 추적

### 1.1 comprehensive_2component_analysis.py의 Bootstrap 코드

**파일**: `scripts/comprehensive_2component_analysis.py` (511–593줄)

```python
def bootstrap_ci(cvd_subj, cvd_type, roi, C_baseline,
                  hc_amps_dict, delta_rdm_obs,
                  n_boot=1000, seed=42):
    """Bootstrap HC subjects to get CI for β_s, β_c."""
    rng = np.random.RandomState(seed)
    hc_subjs = list(hc_amps_dict.keys())
    n_hc = len(hc_subjs)
    
    boot_beta_s = []
    boot_beta_c = []
    boot_cosine = []  # ← cosine similarity 저장 (not ρ)
    
    for b in range(n_boot):
        # HC 피험자 복원 재표본화
        sample_idx = rng.choice(n_hc, n_hc, replace=True)
        # 각 부트스트랩에서 W 재계산 (GCV 선택)
        W_boot = {...}  # 재적합된 가중치
        # 2-Component 모델로 β_s, β_c 최적화
        best_cos = cosine_similarity(drdm_sim, delta_rdm_obs)  # ← ρ 아님
```

**부트스트랩 대상**: β_s, β_c, **cosine similarity** (Spearman ρ 아님)
- 출력: `bootstrap_V1` 사전에 저장 (β_s, β_c 분포 + CI95)
- 결과 저장 경로: `results/2component_comprehensive_v2/sub-{cvd_subj}_2component_results.json`

**핵심 제한**: cosine similarity는 ΔRDM의 각도 유사성이며, **Spearman ρ (LOCO 취약성 상관)**과 다름.

---

## 2. hV4 LOCO ρ Bootstrap CI 현황

### 2.1 loco_distortion_fit.py 결과 구조

**파일**: `scripts/loco_distortion_fit.py`, `results/loco_filter/phase_a_2component/`

결과 JSON 예시 (`sub-09_V1_2component.json`):

```json
{
  "best_loss": {
    "spearman_r": 0.7619,  // ← 최적 매개변수에서의 Spearman ρ
    "rdm_cosine": 0.3065   // ← cosine(ΔRDM)
  },
  "permutation": {
    "label_perm_p": 0.0184,
    "spearman_r": 0.7619,  // ← permutation 관측값
    "null_rho_mean": -2.82e-18,
    "null_rho_std": 0.378   // ← permutation 널 분포 통계
  },
  "baseline": {
    "spearman_r_baseline": 0.5714,
    "delta_rho": 0.1905    // ← Δρ = 모델 - 기준선
  }
}
```

### 2.2 기존 ρ CI 보고

- **보고됨**: Spearman ρ (점 추정 + permutation p-값)
- **미보고됨**: ρ의 **bootstrap 신뢰구간** (특히 HC 재표본화 기반)
- **현재 범위**: LOCO permutation (색상 라벨 재정렬) 만 시행
  - `label_perm_p`: 8! = 40,320 순열 (색상 대각선만)
  - `null_rho_std`: 널 분포 표준편차, **부트스트랩 아님**

---

## 3. Bootstrap ρ 추가 필요성 및 설계

### 3.1 현재 부족 사항

| 항목 | 상태 | 이유 |
|------|------|------|
| LOCO ρ 점 추정 | ✓ 있음 | `loco_distortion_fit.py` 그리드 탐색 |
| ρ permutation p-값 | ✓ 있음 | 8! 색상 순열 |
| **ρ bootstrap CI** | ✗ 없음 | HC 표본화 변동성 미반영 |
| Hierarchical bootstrap | ✗ 없음 | 피험자(6개) × 색상(8개) 계층 구조 미활용 |

### 3.2 추가 방법 (3가지 옵션)

#### 옵션 A: Per-Color Residual Bootstrap (권장)
```
리소스: CPU ~2시간 (sub-08 V1+V4 1000회)
단계:
1. 최적 파라미터 (β_s*, β_c*) 고정
2. 각 부트스트랩 반복에서:
   - 8 색상 × 6 HC 피험자 = 48 LOCO 취약성 값에서 복원 재표본화
   - 해당 부트스트랩 샘플로 ρ 계산
3. 1000회 분포에서 CI95% = [2.5%, 97.5%] 백분위수
```
**구현 위치**: `loco_distortion_fit.py`에 `bootstrap_rho_fixed()` 함수 추가 (450줄 이후)

#### 옵션 B: Hierarchical Bootstrap (더 강건)
```
리소스: CPU ~4시간
단계:
1. HC 피험자 계층 (n=6 중복 복원 재표본화)
2. 각 피험자 내 색상-run 계층 (n_run=6 중복)
3. 계층적 재적합 없음 — W 고정, LOCO만 재계산
결과: 피험자-수준 + 색상-수준 변동성 분리
```

#### 옵션 C: 비교 대안 (기존 permutation 확장)
```
color-wise permutation bootstrap:
- 각 반복에서 색상 순서 재정렬 (option A의 구조적 버전)
- 실행 빠름 (~30분)
```

---

## 4. 구현 제안

### 4.1 코드 추가 위치

**파일**: `scripts/loco_distortion_fit.py` (compute_fit_loss 이후, ~450줄)

```python
def bootstrap_rho_ci(best_params, hc_amps_dict, vuln_cvd, cvd_type,
                     method='shift_at_both', n_boot=1000, seed=42):
    """
    최적 매개변수 고정, HC 취약성 값 부트스트랩으로 ρ CI 계산.
    
    Args:
        best_params: 최적 모델 파라미터 (예: [38.0, 22.0] for 2-component)
        hc_amps_dict: {subj: (6,8,V)} HC 진폭
        vuln_cvd: (8,) CVD 취약성 (관측)
        cvd_type: 'deutan' | 'protan'
        method: 'shift_at_both' | 'w_fixed'
        n_boot: 부트스트랩 반복 (기본 1000)
        
    Returns:
        {rho_mean, rho_ci95, rho_dist: [...]}
    """
    rng = np.random.RandomState(seed)
    C_shifted, _ = get_shifted_design(model_name, best_params, cvd_type)
    
    rho_dist = []
    for b in range(n_boot):
        # HC 취약성 값 (per-color) 복원 재표본화
        colors = np.arange(8)
        color_samples = rng.choice(colors, size=8, replace=True)
        vuln_boot = vuln_cvd[color_samples]
        
        # 고정 최적 모델에서 LOCO 시뮬레이션
        vuln_sim, _ = simulate_mean_hc_wfixed(hc_W_dict, hc_amps_dict, C_shifted)
        vuln_sim_boot = vuln_sim[color_samples]
        
        # ρ 계산
        rho, _ = spearmanr(vuln_sim_boot, vuln_boot)
        rho_dist.append(rho if np.isfinite(rho) else 0.0)
    
    rho_dist = np.array(rho_dist)
    return {
        'n_boot': n_boot,
        'rho_mean': float(rho_dist.mean()),
        'rho_std': float(rho_dist.std()),
        'rho_ci95': [float(np.percentile(rho_dist, 2.5)),
                     float(np.percentile(rho_dist, 97.5))],
        'rho_dist': rho_dist.tolist(),
    }
```

### 4.2 결과 저장 형식

기존 JSON에 추가:
```json
{
  "best_loss": {...},
  "permutation": {...},
  "bootstrap_rho": {
    "n_boot": 1000,
    "rho_mean": 0.762,
    "rho_std": 0.048,
    "rho_ci95": [0.658, 0.845],
    "method": "per_color_residual"
  }
}
```

---

## 5. 7-HC 평균 Baseline Bootstrap 고려

### 5.1 Hierarchical Bootstrap 가능성

**계층 1** (피험자): 6개 HC → 복원 재표본화
**계층 2** (색상-run): 8색 × 6run = 48 → 복원 재표본화

현재는 **baseline ρ** (매개변수 없음, Machado Δλ=0)을 1회 계산만 함.
부트스트랩하면 baseline CI도 얻어 **Δρ = ρ_model - ρ_baseline**의 신뢰도 향상.

**추가 리소스**: +500–1000회 반복 (배경 계산 가능)

---

## 6. 요약 및 권장

| 상태 | 내용 |
|------|------|
| **(a) 기존 bootstrap** | ✓ `comprehensive_2component_analysis.py`에 **HC 피험자 부트스트랩** 있음 (β_s, β_c, cosine) |
| **(b) LOCO ρ bootstrap** | ✗ **부재** — 색상 permutation만 있음, HC 표본화 변동성 미반영 |
| **추가 필요성** | 높음 — LOCO ρ는 모델 비교의 핵심 지표, CI 없으면 신뢰도 저하 |
| **권장 구현** | **옵션 A** (per-color residual, 2시간) + **7-HC baseline 부트스트랩** (추가 30분) |
| **저장 위치** | `results/loco_filter/phase_a_2component/` (기존 JSON 확장) |

---

## 참고

- **Bootstrap 코드**: `comprehensive_2component_analysis.py:511–593`
- **LOCO 그리드 탐색**: `loco_distortion_fit.py:257–365` (grid_search)
- **LOCO permutation**: `loco_distortion_fit.py` (내부 permutation_test_spearman 호출)
- **결과 경로**: `results/loco_filter/phase_a_2component/*.json` (spearman_r, permutation, **bootstrap_rho 부재**)

