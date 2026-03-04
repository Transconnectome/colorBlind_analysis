# Phase 1: 전처리 파이프라인 및 기저선 색 디코딩
> Procrustes alignment + C010 전처리로 pipeline-level 79% noise ceiling 활용률 달성 (per-subject SB-corrected 기준 ~80%). hV4가 최강 색 선택성 (RDM correlation 0.541, noise ceiling 0.697)

## 목표
- 시각 피질에서 색 선택적 신경 표상을 추출하기 위한 최적 fMRI 전처리 파이프라인 확립
- 핵심 질문:
  - (a) C010 (2nd-level drift removal)만으로 충분한가? (confound regression 불필요?)
  - (b) Procrustes alignment (직교 변환 정렬)이 run 간 기하학적 분산을 제거하는가?
  - (c) Whitening (백색화)이 도움되는가?
- 이 Phase의 검증된 데이터가 이후 모든 분석의 입력 (Phase 2 SRM, Phase 2b decoder, Phase 3 filter)

## 피험자 및 데이터

| 항목 | 내용 |
|------|------|
| 피험자 | 10명 (HC 7명: sub-01~07, CVD 3명: sub-08 deutan, sub-09 protan, sub-10 deutan) |
| CVD 진단 | Ishihara test |
| 획득 | 6 runs/피험자, 8 이산 색 자극 (red~magenta), 48 trials/run |
| 전처리 | fMRIPrep 23.2.3, MNI152NLin2009cAsym, res-2 |
| ROI | V1, V2, V3, hV4 (Wang Atlas) |
| Voxel 수 | 67 (hV4, sub-07) ~ 568 (V1); FIR R² 상위 50% 선택 |
| 제외 | sub-07 hV4 (16 voxels → correlation distance 미결정) |

---

## 방법

### GLM Pipeline (C010)
- **1st-level GLM**: FIR basis function (8 delays, 0-12s, TR=1.5s) — 비모수적 BOLD response 추정
- **Voxel selection**: FIR R² 상위 50% — 자극 반응이 신뢰할 수 있는 voxel만 유지
- **2nd-level GLM**: 8 HRF + 8 HRF derivative + 12 drift regressors (선형+상수, run별 2개 × 6 runs)
- **Confounds**: 없음 — motion (6 DOF), CSF/WM, WM regression 모두 RDM을 ~60% 저하시킴
- **High-pass filtering**: 없음 — drift regressor로 동등하게 처리 (실증 확인)

### Procrustes Alignment
- Orthogonal transformation (회전+반사, 스케일링 없음): run 1-5 → run 0 reference 정렬
- 스케일링 제외 이유: amplitude 정보가 색 선택적 신호를 포함 — 스케일링은 이를 기하학적 정렬과 혼동
- Run 간 기하학적 분산이 색 선택적 신호보다 ~16배 큼 → Procrustes가 이 주요 노이즈원 제거
- 평균 disparity: 0.00373 ± 0.004 (40 subject-ROI pairs)

### Forward Encoding Model
- 6개 half-wave rectified Gaussian basis function (0°, 60°, …, 300°; FWHM 60°; Brouwer & Heeger, 2009)
- Cross-validation: LORO (6-fold)
- W 행렬 안정성: cosine similarity 0.921 [0.907, 0.935] (Phase 2b에서 검증)

### Noise Ceiling
- Random split-half + Spearman-Brown correction (1,000 iterations)
- LOSO bounds: 각 피험자 제외 시 ceiling 범위 제공

---

## 결과

### Raw vs. Procrustes (N = 40 subject-ROI pairs)

| 지표 | Raw C010 | C010 + Procrustes | 변화 |
|------|----------|-------------------|------|
| RDM correlation | 0.004 ± 0.197 | **0.381 ± 0.278** | +0.377 |
| Decoding accuracy | 0.131 ± 0.049 | **0.592 ± 0.121** | +0.461 |
| Procrustes disparity | — | 0.00373 ± 0.004 | — |
| Positive subject-ROI pairs | 52.5% | **100%** | 전체 양성 |

> ✅ **+1644% RDM reliability 향상** (0.028 → 0.487). Procrustes 없이는 모든 모델이 chance 수준

### ROI별 성능 (Procrustes 적용)

| ROI | N | RDM Corr† (M±SD) | Accuracy (M±SD) | Noise Ceiling‡ (M±SD) | SB-corrected Utilization§ |
|-----|---|------------------|-----------------|----------------------|--------------------------|
| V1 | 10 | 0.313 ± 0.215 | 0.560 ± 0.138 | 0.582 ± 0.172 | **76.7%** |
| V2 | 10 | 0.370 ± 0.256 | 0.581 ± 0.131 | 0.635 ± 0.200 | **84.5%** |
| V3 | 10 | 0.316 ± 0.328 | 0.613 ± 0.130 | 0.525 ± 0.226 | **75.1%** |
| **hV4** | **9*** | **0.541 ± 0.283** | **0.613 ± 0.092** | **0.697 ± 0.168** | **81.5%** |
| **전체** | **39** | **0.381** | **0.592** | **0.610** | **83.7%** |

*hV4 N=9; sub-07 제외 (16 voxels)

> **지표 정의:**
> - †RDM Corr: per-run RDM의 oddeven split Spearman 상관 (uncorrected). 개별 run 수준 RDM 신뢰도 반영
> - ‡Noise Ceiling: oddeven split-half + Spearman-Brown 보정. Full-data 기준 이론적 상한
> - §SB-corrected Utilization: per-subject SB-corrected RDM reliability / oddeven ceiling × 100 (noise_ceiling_analysis.json 기준). Pipeline-level = 0.487/0.613 = **79%**
>
> **주의**: 이전 테이블에서 % of Ceiling (24.2~41.8%)은 uncorrected split-half 값을 SB-corrected ceiling으로 나누어 과소 추정. SB-corrected utilization이 올바른 apple-to-apple 비교

### 그룹별 성능 (Procrustes 적용)

| 그룹 | N (pairs) | RDM Corr (M±SD) | Accuracy (M±SD) |
|------|-----------|-----------------|-----------------|
| HC (sub-01~07) | 28 | 0.345 ± 0.278 | 0.552 ± 0.111 |
| CVD (sub-08~10) | 12 | 0.462 ± 0.273 | 0.684 ± 0.094 |
| 차이 | — | +0.117 | +13.2 pp |

> 💡 CVD가 수치적으로 높은 디코딩 성능 → CVD 뇌에 **강한 색 선택적 신호**가 존재 (신호 결핍이 아닌 기하학적 왜곡 지지)

### 파이프라인 비교 (N = 40)

| 파이프라인 | RDM Reliability | Noise Ceiling | 상태 |
|-----------|-----------------|---------------|------|
| Raw C010 | 0.028 ± 0.225 | -0.038 ± 0.434 | 불량 |
| **Raw → Procrustes** | **0.487 ± 0.253** | **0.613 ± 0.248** | **최적** |
| Raw → Whitening → Procrustes | 0.036 ± 0.153 | 0.020 ± 0.182 | -92% (유해) |
| Raw → Procrustes → Whitening | 0.259 ± 0.245 | 0.352 ± 0.315 | -47% (유해) |

> ⚠️ **Whitening은 적용 순서와 무관하게 성능 저하**: 공분산 추정이 신호와 노이즈를 혼동하여 색 공간 구조 제거

---

## 핵심 해석

1. **Procrustes alignment 필수** — Run 간 기하학적 분산이 색 신호의 ~16배. 정렬 없이는 모든 모델 chance
2. **Whitening 유해** — 47-92% 성능 저하. voxel 수(67-568) 대비 샘플 수가 부족하여 공분산 추정 불안정
3. **Confound regression 불필요** — Motion, tissue signal 추가 시 RDM ~60% 저하. Drift regressor만으로 충분
4. **hV4가 최강 색 선택성** — RDM 0.541, noise ceiling 0.697, SB-corrected 활용률 81.5%. 피험자 간 SD도 최저 (0.092)
5. **Per-subject SB-corrected ceiling ~84%** (pipeline-level 79%) → 높은 within-subject 활용률이지만, between-subject 일치도는 낮아 SRM (Phase 2) 동기 부여

---

## 제한점

| 제한점 | 설명 |
|--------|------|
| Noise ceiling 활용률 ~84% (SB-corrected) | Within-subject 신뢰도는 높으나, between-subject RDM agreement는 낮음 (raw 0.083~0.159) → SRM (Phase 2)이 해소 |
| sub-07 hV4 제외 | C010에서 16 voxels → 모든 hV4 그룹 통계에 전파 |
| 이산 자극 8개 | 색 공간 해상도 제한. Phase 2b LOCO에서 보간 시도 |
| CVD N = 3 | 그룹 차이는 기술적(descriptive) 수준. 인과 해석 불가 |
| 단일 reference run | Run 0 기준. 대안 reference 전략 미비교 (영향 미미할 것으로 예상) |
| 공분산 추정 한계 | Whitening 실패가 이 voxel 수 범위에 한정적일 수 있음. Ledoit-Wolf shrinkage 미테스트 |

### 🔽 References
- Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. *J Neuroscience*, 29(44), 13992-14003.
- Wang, L., et al. (2015). Probabilistic maps of visual topography in human cortex. *Cerebral Cortex*, 25(10), 3911-3931.
- Gower, J. C., & Dijksterhuis, G. B. (2004). *Procrustes Problems*. Oxford University Press.
- Zeki, S., et al. (1991). A direct demonstration of functional specialization in human visual cortex. *J Neuroscience*, 11(3), 641-649.
- Ledoit, O., & Wolf, M. (2004). A well-conditioned estimator for large-dimensional covariance matrices. *J Multivariate Analysis*, 88(2), 365-411.
