# Phase 2: SRM 기반 HC-CVD 집단 비교
> 그룹: V1 p=0.062 (g=1.16), V2 p=0.075 (g=1.04) trending. 개인: sub-09 V1 p=0.007*, sub-08 V2 p=0.040*. Convergent validity (crossnobis r=0.486, PCA r=0.742)로 SRM artifact 아닌 실제 신경 차이 확인

## 목표
- CVD 피험자가 HC와 체계적으로 다른 색 표상을 보이는지 SRM (Shared Response Model, 공유 반응 모델) 공통 공간에서 검정
- 분석 수준: 그룹 차이, 개인 CVD 프로파일, 색 의존성, 방법론 간 수렴 타당도

## 피험자 및 데이터

| 항목 | 내용 |
|------|------|
| 피험자 | 10명 (HC 7: sub-01~07, CVD 3: sub-08 deutan, sub-09 protan, sub-10 deutan) |
| 입력 | Phase 1 Procrustes-aligned amplitudes (C010), shape (6, 8, n_voxels) |
| ROI | V1, V2, V3, hV4 (Wang Atlas) |
| SRM k | V1=4, V2=4, V3=3, hV4=3 (7-fold LOSO mean rank aggregation) |

---

## 방법

### SRM Alignment
- Beta-based SRM: run 평균 패턴 (n_voxels × 8 colors)으로 7 HC 피험자에서 shared response S와 개인 weight matrix W 학습
- **HC-only SRM 학습** → CVD는 SVD projection으로 HC 공간에 투영 (순환성 방지)

### LOO-Consistent Disparity (편향 제거 3단계)
1. **HC-only SRM**: CVD가 공유 공간 정의에 영향 안 줌
2. **LOO for HC**: 각 HC_i를 나머지 6명의 평균과 비교 (자기 포함 방지)
3. **Same LOO references for CVD**: CVD도 HC와 동일한 7개 LOO reference 기준으로 평가

### 핵심 지표 정의

| 지표 | 정의 | 해석 |
|------|------|------|
| **SRM Disparity** | SRM 공유 공간에서 두 패턴 (8 colors × k features) 간 Procrustes 정렬 후 Frobenius 잔차 노름. 양 패턴을 중심화·단위노름화한 뒤 최적 직교 회전 R을 찾아 ‖X_n@R − Y_n‖_F 계산 | 값이 작을수록 패턴 구조가 유사. 0 = 완벽 일치, ~1.41 = 최대 비유사 |
| **LOO-Consistent Disparity** | 각 HC_i를 나머지 6명 평균 reference와 비교한 disparity. CVD도 동일한 7개 LOO reference 기준으로 평가 | HC LOO 분포 대비 CVD score가 높으면 HC 공유 구조에서 이탈 |
| **Separation** | mean(CVD LOO scores) − mean(HC LOO disparities) | 양수 = CVD가 HC보다 공유 공간에서 먼 위치 |
| **RDM Correlation** | 각 피험자의 8×8 RDM (correlation distance) 상삼각 벡터 간 Spearman 순위 상관 | 값이 높을수록 색 관계 구조가 유사. HC-CVD가 HC-HC에 가까우면 CVD가 색 구조 보존 |
| **Hedges' g** | 편향 보정 Cohen's d (소표본 보정). Bootstrap 95% CI (10,000회) | 효과 크기 지표. g > 0.8 = 큰 효과 |
| **Crawford & Howell t** | 단일 CVD 점수를 HC 분포(n=7)와 비교하는 수정 t-검정. df=6, one-tailed | 개인 수준 유의성 판단 (p < 0.05) |

**결과 테이블 해석 가이드:**
- 그룹 비교 테이블의 "HC LOO" / "CVD LOO" = LOO-consistent disparity 평균 [95% bootstrap CI]
- 색 의존성(LOSO) 테이블의 "CVD score p" = 색 라벨 셔플 시 CVD disparity가 관측값 이하일 확률 (낮으면 색 특이적)
- RDM Correlation 테이블의 HC-HC / HC-CVD / CVD-CVD = 해당 피험자 쌍의 Spearman r 평균 [95% CI]

### 통계 검정
- **그룹 비교**: Permutation test (10,000 iterations) — pseudo-HC/CVD 배정, SRM 재학습 포함
- **개인 CVD**: Crawford & Howell (1998) modified t-test (df=6, one-tailed)
- **Effect size**: Hedges' g + bootstrap 95% CI (10,000 iterations)
- **색 의존성 (LOSO)**: Leave-one-subject-out permutation — HC도 SVD projection으로 공평한 비교

### k Selection (7-fold LOSO)

| ROI | 선택된 k | RDM reliability | Cross-subj RDM corr | Mean rank |
|-----|---------|----------------|---------------------|-----------|
| V1 | **4** | 0.496 ± 0.146 | 0.597 ± 0.229 | 1.93 |
| V2 | **4** | 0.429 ± 0.137 | 0.566 ± 0.145 | 2.14 |
| V3 | **3** | 0.446 ± 0.194 | 0.546 ± 0.279 | 2.14 (tie → parsimony) |
| hV4 | **3** | 0.560 ± 0.185 | 0.317 ± 0.169 | 2.07 |

> 💡 hV4의 해리: RDM reliability 최고 (0.560) but cross-subject RDM corr 최저 (0.317) → 강한 개인별 색 선택성이 피험자 간에 일반화 안 됨

---

## 결과

### 그룹 비교 (LOO-Consistent, 10,000 Permutations)

| ROI | HC LOO [95% CI] | CVD LOO [95% CI] | Separation [95% CI] | p (perm) | g [95% CI] |
|-----|----------------|-----------------|---------------------|----------|------------|
| **V1** | 0.453 [0.397, 0.512] | 0.590 [0.457, 0.761] | 0.137 [-0.005, 0.301] | **0.062** | 1.16 [-0.06, 3.98] |
| **V2** | 0.486 [0.418, 0.559] | 0.606 [0.505, 0.718] | 0.120 [0.001, 0.244] | **0.075** | 1.04 [0.02, 3.18] |
| V3 | 0.540 [0.476, 0.608] | 0.564 [0.404, 0.738] | 0.023 | 0.395 | 0.18 |
| hV4 | 0.700 [0.617, 0.796] | 0.677 [0.444, 0.855] | -0.023 | 0.559 | -0.14 |

> ⚠️ V1/V2 trending (p < 0.10) with large effect size (g > 1.0). V2 separation CI [0.001, 0.244]가 근소하게 zero 제외 → 가장 강한 그룹 차이 증거. 넓은 CI는 n=3 CVD의 근본적 한계

### 개인 CVD 검정 (Crawford & Howell 1998)

| 피험자 | V1 (t, p) | V2 (t, p) | V3 (t, p) | hV4 (t, p) |
|--------|-----------|-----------|-----------|------------|
| **sub-09** (protan) | **t=3.5, p=0.007*** | t=1.0, p=0.181 | t=0.1, p=0.466 | t=1.1, p=0.150 |
| **sub-08** (deutan) | t=1.1, p=0.157 | **t=2.1, p=0.040*** | t=1.9, p=0.052 | t=0.2, p=0.411 |
| sub-10 (deutan) | t=0.0, p=0.483 | t=0.2, p=0.433 | t=-1.3, p=0.884 | t=-1.9, p=0.945 |

> 💡 **영역 특이적 해리**: sub-09 (protan) = V1 특이적 (+68%), sub-08 (deutan) = V2 특이적 (+47%), sub-10 = HC 범위 내. 2/3 검출률로 그룹 p-value보다 더 정보적

### 개인 CVD 프로파일 (HC LOO 평균 대비 %)

| 피험자 | V1 | V2 | V3 | hV4 | 패턴 |
|--------|------|------|------|------|------|
| sub-08 | +20.9% | +47.4% | +35.7% | +3.5% | 중-고 상승 |
| sub-09 | +67.7% | +21.5% | +0.7% | +21.4% | V1-dominant |
| sub-10 | -0.1% | +3.1% | -26.8% | -39.1% | 정상~HC 이하 |

### 색 의존성 (LOSO Color-Dependency)

| ROI | HC held-out p | CVD score p | CVD pairwise p | 해석 |
|-----|--------------|------------|----------------|------|
| V1 | 0.364 | 0.412 | 0.077 | 색 비특이적 |
| **V2** | 0.227 | **0.010** | **0.035** | **CVD 색 의존적** |
| **V3** | 0.207 | **0.000** | **0.046** | **CVD 색 의존적** |
| **hV4** | 0.330 | **0.016** | **0.031** | **CVD 색 의존적** |

> 💡 **핵심 비대칭**: HC disparity는 색 라벨에 무관 (p=0.21-0.36), CVD disparity는 V2/V3/hV4에서 **색 특이적** (p=0.000-0.016). 색 라벨 셔플 시 CVD disparity가 증가 → SRM 그룹 차이가 진짜 색 구조 차이에 의한 것 확인

### LOSO 안정성 (7-fold)

| ROI | Significant folds (p < 0.05) | Fold p-value range | 안정성 |
|-----|-------------------------------|-------------------|--------|
| V1 | **6/7** | 0.007 — 0.052 | 견고 (1 fold marginal) |
| **V2** | **7/7** | < 0.001 — 0.032 | **완벽한 안정성** |
| V3 | 0/7 | 0.199 — 0.461 | 일관되게 비유의 |
| hV4 | 0/7 | 0.147 — 0.460 | 일관되게 비유의 |

### Robustness Triangulation (수렴 타당도)

| 지표 | 방법 | V1 | V2 | 핵심 결과 |
|------|------|----|----|-----------|
| **SRM disparity** (main) | SRM shared space | p=0.062 | p=0.075 | Trending V1/V2 |
| **A4 Crossnobis** | Native voxel space | p=0.051 | ns | r=0.486 (p=0.001, pooled) |
| **A5 PCA-only** | PCA alignment | ns | ns | **r=0.742 (p<0.001, pooled)** |
| **A3 VE (LOSO)** | SRM reconstruction | CVD ≥ HC | CVD > HC, g=-1.68 | "강한 신호, 다른 구조" |

**Per-ROI 수렴도** (SRM disparity vs. crossnobis / PCA):
| ROI | Crossnobis r | PCA-only r |
|-----|-------------|-----------|
| V1 | 0.721* | 0.636* |
| **V2** | **0.806*** | **0.891**** |
| V3 | 0.200 | 0.285 |
| hV4 | 0.248 | 0.661* |

> ✅ V2 PCA-SRM 수렴도 r=0.891 (near-perfect) → 가장 설득력 있는 단일 수치. 개인 차이 패턴이 방법에 무관

### RDM Correlation (색 구조 유사성)

| ROI | HC-HC [95% CI] | HC-CVD [95% CI] | CVD-CVD [95% CI] |
|-----|---------------|----------------|----------------|
| V1 | 0.447 [0.357, 0.531] | 0.322 [0.237, 0.402] | 0.297 [0.126, 0.493] |
| **V2** | **0.517 [0.442, 0.592]** | **0.499 [0.414, 0.587]** | **0.591 [0.471, 0.702]** |
| V3 | 0.385 [0.300, 0.473] | 0.348 [0.245, 0.457] | 0.591 [0.490, 0.672] |
| hV4 | 0.158 [0.069, 0.248] | 0.224 [0.119, 0.328] | 0.276 [0.008, 0.734] |

> 💡 V2에서 HC-CVD CI와 HC-HC CI가 대폭 중첩 → CVD는 색 관계 구조를 대체로 보존. CVD-CVD V2/V3 (0.591) > HC-HC → CVD 간 공유 왜곡 패턴 존재

### SRM Alignment 비교 (Between-Subject RDM Agreement)

| ROI | Raw | Procrustes | SRM | SRM/Raw |
|-----|-----|-----------|-----|---------|
| V1 | 0.083 | 0.068 | **0.538** | **6.5x** |
| V2 | 0.152 | 0.159 | **0.556** | **3.7x** |
| V3 | 0.159 | 0.145 | **0.388** | **2.4x** |
| hV4 | 0.097 | 0.111 | **0.297** | **3.1x** |

### CVD 이질성

| ROI | CVD-CVD / HC-HC disparity ratio |
|-----|-------------------------------|
| V1 | 1.47x |
| V2 | 1.37x |
| V3 | 1.59x |
| hV4 | 1.44x |

> ⚠️ CVD는 전 ROI에서 HC보다 1.4-1.6x 더 분산 → 그룹 수준 CVD 필터 부적합, 개인화 필요

---

## 핵심 해석

1. **"Scattered but structured"** — 그룹 효과는 trending이지만, CVD disparity가 **색 특이적** (V2/V3/hV4 LOSO p<0.05)인 반면 HC는 아님 → 가장 강한 증거
2. **개인 해리가 이질성 해소** — sub-09 V1-specific (+68%, p=0.007), sub-08 V2-specific (+47%, p=0.040), sub-10 HC 범위 내
3. **수렴 타당도가 핵심 증거** — SRM, crossnobis, PCA 간 개인 차이 패턴 일치 (V2: r=0.891) → SRM artifact 아님
4. **CVD VE ≥ HC = "다른 구조, 노이즈 아님"** — CVD 데이터가 HC-trained SRM에 더 잘 재구성 (V2 g=-1.68) → 기하학적 변환된 신호
5. **V2가 가장 견고한 ROI** — 7/7 LOSO folds, 양쪽 split-half 유의, PCA 수렴도 0.891, VE g=-1.68

---

## 제한점

| 제한점 | 설명 |
|--------|------|
| n=3 CVD | 그룹 검정 저검정력, CI 넓음 (V1 g CI: [-0.06, 3.98]) |
| Trending group effects | V1 p=0.062, V2 p=0.075 → α=0.05 미달. 수렴 타당도로 보완 |
| SRM k 제약 | 8 색 자극 → k ≤ 8. 최적 k=3-4가 색 표상 전체 차원성 미포착 가능 |
| CVD 이질성 | 1.4-1.6x ratio → 그룹 필터 부적합 |
| HC floor effect (LOSO) | HC가 SRM을 학습하여 색 라벨 셔플에 둔감 → LOSO가 보수적 대안 |
| 수렴 ≠ 인과 | SRM, crossnobis, PCA 모두 같은 교란변수 공유 가능. 행동 검증 필요 |

### 🔽 Validation Summary Table

| 검증 | V1 | V2 | V3 | hV4 |
|------|----|----|----|----|
| LOSO stability | 6/7 | **7/7** | 0/7 | 0/7 |
| Split-half (양쪽 유의) | No | **Yes** | No | No |
| Split-half set A / B p | 0.059/0.019 | **0.006/0.022** | 0.156/0.074 | 0.402/0.174 |
| k selection (unanimous) | k=4 | k=4 | k=3 (tie) | k=3 |
| Alignment advantage | **6.5x** | 3.7x | 2.4x | 3.1x |
| Crossnobis convergence r | 0.721* | 0.806** | 0.200 | 0.248 |
| PCA convergence r | 0.636* | 0.891*** | 0.285 | 0.661* |

### 🔽 Run-Split ICC (CVD 개인 신뢰도)

| 피험자 | V1 | V2 | V3 | hV4 | 평가 |
|--------|------|------|------|------|------|
| sub-08 | 0.58 | **0.75** | 0.71 | **0.83** | 가장 안정적 CVD |
| sub-09 | 0.46 | 0.53 | 0.73 | 0.74 | 중간 |
| sub-10 | 0.45 | 0.55 | 0.61 | 0.67 | 중간 |

### 🔽 References
- Chen, P. H., et al. (2015). A reduced-dimension fMRI shared response model. *NIPS*.
- Crawford, J. R., & Howell, D. C. (1998). Comparing an individual's test score against norms derived from small samples. *Clinical Neuropsychologist*, 12(4), 482-486.
- Brouwer, G. J., & Heeger, D. J. (2009). *J Neuroscience*, 29(44), 13992-14003.
- Walther, A., et al. (2016). *NeuroImage*, 137, 188-200.
- Haxby, J. V., et al. (2011). *Neuron*, 72(2), 404-416.
- Neitz, J., & Neitz, M. (2011). *Vision Research*, 51(7), 633-651.
