# Phase 2b: 디코더 모델 비교 및 검증
> 과제 의존적 최적성: LDA + SRM → classification (0.793 acc, ICC 0.666) / ForwardEncoding + Procrustes → interpolation (75.7° HC MAE). CVD는 색 변별은 HC와 동등하지만 보간은 저하 → 색 공간 왜곡 (신호 손실 아님)

## 목표
Phase 3 필터 최적화 전 4가지 디코더 가정 검증:
1. Voxel-color 매핑이 근본적으로 선형인가?
2. 정렬이 필요한가, 비선형 모델이 보상 가능한가?
3. HC와 CVD가 동일한 매핑을 공유하는가? (필터 학습의 전제)
4. 모델이 미관측 색을 연속적 색 구조로부터 보간할 수 있는가?

## 피험자 및 데이터

| 항목 | 내용 |
|------|------|
| 피험자 | 10명 (HC 7, CVD 3) |
| 입력 | C010 Procrustes-aligned amplitudes; raw 및 SRM-projected 변형 포함 |
| 모델 | 6 decoders (LDA, SVM, Ridge, KernelRidge, ForwardEncoding, MLP) + 2 hybrids |
| LORO | 6-fold leave-one-run-out (classification) |
| LOCO | 8-fold leave-one-color-out (interpolation) |
| 통계 | Bootstrap 95% CI, ICC, Mann-Whitney U, Wilcoxon signed-rank, permutation test |

---

## 결과

### 과제별 최적 파이프라인 요약

| 과제 | 최적 파이프라인 | 핵심 지표 | 근거 |
|------|----------------|-----------|------|
| LORO (classification) | LDA + SRM | 0.793 acc, ICC 0.666 | SRM이 LDA fold 불안정성 해소 |
| LOCO (interpolation) | FE + Procrustes | 75.7° HC MAE | 전체 voxel이 연속 색조 구조 보존 |
| Phase 3 (filter design) | FE + Procrustes | W cosine 0.921 | 안정적 6-channel 표상 |
| Cross-subject comparison | LDA + SRM | p=0.668 (no bias) | 편향 없는 HC→CVD 일반화 |

> 💡 Classification은 일관된 저차원 결정 경계 필요 (SRM 유리), interpolation은 전체 voxel의 연속 색조 구조 보존 필요 (Procrustes 유리)

---

### LORO Classification: 3-Alignment 비교

| Model | Raw | Procrustes | SRM |
|-------|-----|------------|-----|
| **LDA** | 0.135 | 0.758 | **0.793** |
| SVM | 0.127 | 0.685 | 0.727 |
| FE | 0.129 | 0.545 | 0.480 |
| Ridge | 0.131 | 0.388 | 0.313 |
| KRidge | 0.127 | 0.332 | 0.285 |
| MLP | 0.126 | 0.147 | 0.131 |

> ⚠️ Raw (정렬 없음)에서는 **모든 모델이 chance (0.125)**. 비선형 모델도 정렬 실패를 보상 못함. 정렬이 가장 핵심적 단일 요인

### Alignment × ROI Interaction (Wilcoxon signed-rank)

| ROI | SRM vs Procrustes p | 우세 |
|-----|---------------------|------|
| V1 | 0.002 | **SRM** |
| V2 | 0.058 | SRM (trend) |
| V3 | 9.1e-08 | **Procrustes** |
| hV4 | 1.8e-05 | **Procrustes** |

> 💡 V1/V2 (early visual) → SRM 우세 (k=4가 충분한 분산 포착). V3/hV4 (higher visual) → Procrustes 우세 (개인 특이적 구조를 SRM이 희생)

### LORO Test-Retest Reliability (ICC)

| Model | Raw | Procrustes | SRM |
|-------|-----|------------|-----|
| LDA | 0.224 | **0.013** | **0.666** |
| SVM | -0.284 | 0.495 | 0.760 |
| FE | 0.471 | 0.574 | 0.753 |

> ⚠️ **Procrustes LDA 역설**: 0.758 accuracy이지만 ICC = 0.013 (재현성 제로). 고차원 voxel 공간 (568 voxels, 40 training samples)에서 fold별로 다른 결정 경계 → 높은 정확도지만 개인차 신뢰 불가
>
> ✅ SRM이 유일하게 **모든 6개 모델 ICC > 0.66** 달성 → 개인차 바이오마커 연구에 필수

### HC vs CVD LORO 비교 (SRM, Mann-Whitney U)

| Model | HC Mean | CVD Mean | Diff | p-value |
|-------|---------|----------|------|---------|
| LDA | 0.635 | 0.665 | -0.030 | 0.668 |
| SVM | 0.464 | 0.488 | -0.024 | 0.647 |
| FE | 0.526 | 0.462 | +0.064 | 0.076 |

> ✅ LDA/SVM: CVD도 HC와 동등하게 디코딩 → 범주적 색 구조 보존. FE만 HC 우세 trend (p=0.076) → FE는 CVD가 왜곡하는 연속 색조 기하학에 민감

---

### LOCO Interpolation: ForwardEncoding MAE (degrees)

| ROI | Raw HC | Raw CVD | Proc HC | Proc CVD | SRM HC | SRM CVD |
|-----|--------|---------|---------|----------|--------|---------|
| V1 | 76.9 | 76.4 | 76.4 | 84.6 | 80.0 | 93.5 |
| V2 | 74.8 | 78.5 | 80.0 | 98.5 | 84.9 | 90.5 |
| V3 | 77.8 | 76.4 | 77.0 | 73.5 | 99.3 | 88.3 |
| hV4 | 73.5 | 76.0 | 69.4 | 87.4 | 72.2 | 90.9 |

> ⚠️ CVD 결손은 **정렬 후에만 드러남** (raw: HC ≈ CVD < 4° 차이; Procrustes: V2 +18.5°, hV4 +18.0°). SRM은 LOCO에 최악 — 차원 축소가 연속 색조 구조 파괴

### LOCO Crawford & Howell 검증 (Procrustes, FE)

| ROI | HC MAE (SD) | CVD MAE (SD) | Separation | g [95% CI] | p (perm) |
|-----|------------|-------------|-----------|-----------|----------|
| V1 | 79.2 (8.4) | 84.6 (28.3) | +8.3 | 0.47 | 0.237 |
| V2 | 80.0 (16.7) | 98.5 (20.5) | +18.5 | 0.94 | 0.072 |
| V3 | 77.0 (16.2) | 73.5 (9.9) | -3.4 | -0.21 | 0.642 |
| **hV4** | **69.4 (9.4)** | **87.4 (10.2)** | **+18.0** | **1.69 [0.94, 3.68]** | **0.017*** |

> ✅ hV4가 유일하게 유의한 그룹 LOCO 결손 (p=0.017, g=1.69, CI가 zero 제외). Phase 2 SRM disparity (hV4 p=0.559)와는 다른 양상 → 독립 방법의 수렴이 hV4 증거 강화

### 개인 CVD LOCO 프로파일 (Procrustes, FE MAE)

| 피험자 | V1 | V2 | V3 | hV4 | 프로파일 |
|--------|------|------|------|------|----------|
| sub-08 (deutan) | **52.0** | 68.4 | 59.1 | 68.4 | 최우수 CVD (전 ROI < chance) |
| sub-09 (protan) | 104.1 | 105.9 | 72.2 | 97.5 | 최저 (3/4 > chance) |
| sub-10 (deutan) | 97.5 | 108.8 | 75.0 | 77.8 | 혼합 |

> 💡 sub-08은 V1에서 대부분의 HC보다 우수 (52.0°) — deutan 색 공간이 왜곡되었지만 V1의 국소 색조 연속성은 보존. sub-09 (protan)이 가장 심한 보간 장애

---

### Cross-Decoding: HC→CVD (SRM space)

| ROI | k | sub-08 (acc, p) | sub-09 (acc, p) | sub-10 (acc, p) |
|-----|---|-----------------|-----------------|-----------------|
| V1 | 4 | 1.000, p<0.001 | 0.875, p<0.001 | 1.000, p<0.001 |
| V2 | 4 | 0.750, p<0.001 | 0.875, p<0.001 | 1.000, p<0.001 |
| V3 | 3 | 0.625, p<0.001 | 0.750, p<0.001 | 0.875, p<0.001 |
| hV4 | 3 | 0.375, p=0.057 | 0.625, p<0.001 | 0.375, p=0.056 |

> ✅ **10/12 검정 유의** (chance 12.5%). HC-trained decoder가 CVD 색 표상 디코딩 성공 → 공유 매핑 확인 (필터 학습의 전제 충족)

### FE Channel Weight 안정성

| 지표 | 값 |
|------|------|
| Grand mean cosine similarity | **0.921** [0.907, 0.935] |
| Range (min-max) | 0.878 — 0.978 |
| Mean SD per subject-ROI | 0.017 |

> ✅ W 행렬이 LORO folds 간 매우 안정 (cosine > 0.87 everywhere) → Phase 3 필터 설계의 신뢰할 수 있는 6-channel 기반

---

### Group Prior (GP) 개선

**LOCO (누출 보정된 nested CV)**

| ROI | HC Change | CVD Change |
|-----|-----------|------------|
| V1 | +4.3% | +8.3% |
| V2 | +8.3% | +5.7% |
| V3 | -5.3% | -27.0% |
| hV4 | -6.1% | -5.2% |

- Lambda = 0.0 (pure GP) 선택률 80.6% → 7 LOCO 색으로는 개인 W 추정 불안정, group mean이 더 안정
- V1/V2 개선, V3/hV4 악화 (높은 개인 변이를 group mean이 소거)

**LORO (표준 nested CV)**

| ROI | Baseline MAE | GP MAE | Improvement |
|-----|-------------|--------|-------------|
| V1 | 42.40 | 34.47 | -18.7% |
| V2 | 50.96 | 32.72 | -35.8% |
| V3 | 60.63 | 54.25 | -10.5% |
| hV4 | 62.21 | 61.34 | -1.4% |

---

## 핵심 해석

1. **선형 channel representation 존재** — LDA, FE가 모든 비선형 모델을 능가. 정렬 후 voxel-color 매핑은 근본적으로 선형
2. **과제 의존적 최적성** — Classification → SRM, Interpolation → Procrustes. SRM × ROI interaction 추가 (V1/V2 → SRM, V3/hV4 → Procrustes)
3. **LORO-LOCO 해리 = CVD 색 공간 왜곡의 직접 증거** — CVD는 색 변별 동등 (LORO ≈ HC) + 보간 저하 (LOCO V2 +18.5°, hV4 +18.0°). 범주 경계 보존 but 연속 색조 다양체 왜곡
4. **Procrustes LDA 역설** — 높은 accuracy (0.758) but ICC = 0.013. 높은 디코딩 정확도 ≠ 신뢰할 수 있는 개인차. SRM이 유일한 해결책
5. **FE channel weight 안정** — cosine 0.921 → Phase 3 필터 설계의 안정적 기반

---

## 제한점

| 제한점 | 설명 |
|--------|------|
| LOCO MAE = encoding estimation 한계 | 7색/fold → channel당 df=1. 디코딩이 아닌 인코딩 추정이 병목 |
| SRM → LOCO 부적합 | 수백 voxel → k=3-4 → 연속 색조 구조 손실 (V3: +22.3° MAE) |
| GP leakage 보정 | 초기 LOCO GP (-50.9%) 결과는 누출 artifact. 보정 후 +4-8% (V1/V2만) |
| LOCO 개인 유의성 희박 | 4/40 pairs만 p<0.05 (8 folds × 6 runs으로 검정력 낮음) |
| CVD LOCO 이질성 | sub-08 V1 52.0° (HC 이상) vs sub-09 104.1° → "CVD 보간 결손" 단일 특성화 부적절 |

### 🔽 Negative Results 요약

| 시도 | 결과 | 해석 |
|------|------|------|
| PopVec, RidgeEnc, GaussML, RidgeReg (LOCO 대안) | 모두 baseline correlation 대비 열위 | 7색/fold = 부족한 df |
| MLP architecture sweep | +57° penalty (131.9° vs FE 74.9°) | LOCO OOD extrapolation에 비선형 readout 부적합 |
| FE+SVM, FE+MLP hybrids | FE와 동등 또는 퇴화 | Channel→color 매핑이 이미 선형으로 충분 |
| Sequential training | MLP warm_start 무효, FE는 수학적 동치 | 순차 학습 방향 종료 |
| Non-linear LOCO (all alignments) | 전 ROI/정렬/그룹에서 FE 대비 +19-46° | 비선형 실패는 정렬/ROI/그룹 비특이적 |

### 🔽 References
- Brouwer, G. J., & Heeger, D. J. (2009). *J Neuroscience*, 29(44), 13992-14003.
- Chen, P. H., et al. (2015). A reduced-dimension fMRI shared response model. *NIPS*.
- Crawford, J. R., & Howell, D. C. (1998). *Clinical Neuropsychologist*, 12(4), 482-486.
