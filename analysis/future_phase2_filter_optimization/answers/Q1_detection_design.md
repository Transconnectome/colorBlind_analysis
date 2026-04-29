# §5-1 Detection 표 추적 — 코드 및 결과 JSON 분석

## 1. P-value의 통계적 정의

표의 p-value는 **단일 CVD subject에 대한 모델 적합 vs label-permutation null**이다 (경우 a).

### 구현 상세:
- **입력**: CVD 피험자의 hV4 LOCO vulnerability 벡터 (8개 색, 각 색당 voxel 상관계수)
- **Reference**: HC 평균 (7명 each에 대해 W-fixed LOCO 계산 후 평균)
- **Fitting**: `shift_at_both` 방식 — HC 각 피험자별로 원래 설계 행렬 C(θ)로 W를 학습, 그 후 모든 색에 동일 shift δθ 적용 → 모든 HC의 shifted vulnerability 평균 계산
- **Permutation**: 8개 색 라벨을 2^8 아닌 정확히 8! = 40,320개 모두 순열(정렬 permutation test) — loco_distortion_fit.py:262-298, step1_fit_loco_v2.py

```
permutation_test_spearman(hc_vuln_fitted, cvd_vuln, n_perm=10000)
→ use_exact=True (n_perm ≥ 40320)
→ for perm in permutations(range(8)):
     r_null ← Spearman ρ(HC_shifted_vuln, CVD_vuln[perm])
   p = (sum(r_null ≥ r_obs) + 1) / (40321)
```

JSON 예시 (sub-08 Machado): `label_perm_p = 0.0575` → p=0.058.

---

## 2. HC "Reference" 처리 방식

**vuln_HC_mean** 방식이 사용된다 (LOO 아님):

- **Step 1**: `precompute_hc_W()` — HC 7명 각각에 대해 원래 색 자극 C(θ)로 ridge W 학습. 학습 데이터: 6 runs × 8 colors = 48 샘플 (loco_distortion_fit.py:156-185)
- **Step 2**: `simulate_mean_hc_wfixed()` — 적합 시마다, 모델 파라미터로부터 shifted C(θ+δ) 생성 → 각 HC의 고정 W로 패턴 예측 → 모든 HC의 vulnera 평균 계산
  
```
vuln_sim = mean([simulate_single_hc_wfixed(W_hc, amp_hc, C_shifted) 
                 for hc in HC_subjects])
```

따라서 reference는 **HC 7명 평균**, per-color basis. LOO나 H_mean의 구분 없음.

---

## 3. Fitting 데이터 흐름

```
amplitudes_procrustes.npy (HC: 6 runs × 8 colors × V_s voxels)
        ↓
    precompute_hc_W
    → ridge (GCV α 선택)
    → W_hc (K × V_s) × 7 subj
        ↓
    [적합 루프: 모델 파라미터 θ → shifted C(θ+δ)]
    → get_shifted_design() (Machado/R+C/2-Comp/Fourier)
    → simulate_mean_hc_wfixed(W_dict, amp_dict, C_shifted)
    → vulnerability_sim (8,)
        ↓
    [CVD LOCO 로드]
    CVD_amplitudes_procrustes.npy
    → load_cvd_loco_target('hV4')
    → vulnerability_cvd (8,) [미리 계산된 LOCO 값]
        ↓
    compute_fit_loss(vuln_sim, vuln_cvd, ...)
    → L_fit = 1.0·L_vuln + 0.5·L_rank + 0.2·L_rdm + 0.1·L_smooth
        ↓
    permutation_test_spearman(vuln_sim, vuln_cvd, n_perm=40320)
    → p-value
```

---

## 4. Sub-09 R+C = "=Machado" 이유

**g ≈ 0 collapse**: sub-09 protan 피험자에서 R+C 모델의 g 파라미터가 최적화 과정에서 거의 0에 수렴하여, 실질적으로 g=0인 순수 Machado 모델과 동일해진다.

### 증거:
- Phase_a (4월 8일 결과): sub-09에서 R+C grid search를 실행했지만 "=Machado" 표기
- R+C 모델: `rg' = rg_base + (1+g)·(rg_ret − rg_base)` — g=0이면 rg' = rg_base (피질 보상 제거)
- Protan의 심각도 (Δλ=13.5nm, moderate-severe range)가 L-M cone 축 위에서의 대비를 크게 손상 → 망막 shift 자체만으로도 vulnerability를 충분히 설명 가능 → 추가 피질 gain (g) 도움 안 됨

JSON 결과에서 직접 `best_params` 값 확인되지 않음 (검색 결과에서 미확인), 하지만 합의는 R+C grid가 Machado와 동일한 최적값을 산출했다는 의미.

---

## 참고 파일 및 줄번호

| 파일 | 줄 | 내용 |
|------|:---:|------|
| loco_distortion_fit.py | 257-365 | `grid_search()` — grid 구성, simulate, permutation |
| loco_distortion_fit.py | 184-250 | `compute_fit_loss()` — L_fit = α L_vuln + ... |
| step1_fit_loco_v2.py | 156-235 | `precompute_hc_W()`, `simulate_mean_hc_wfixed()` |
| step1_fit_loco_v2.py | 262-298 | `permutation_test_spearman()` — exact 8! permutation |
| results/loco_filter/phase_a/ | — | sub-0{8,9,10}_V4_{machado,rc,2comp}.json (결과) |

