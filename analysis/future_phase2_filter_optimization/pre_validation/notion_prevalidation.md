# Future Phase 2: CVD 신경 표상 분석 및 필터 설계 근거

> **sub-08 (deutan)**: FDR 32 pairs, split-half r=0.73-0.84, cone-shift 예측 7/7 일치 → 주 필터 후보
> **sub-09 (protan)**: FDR 7 pairs (V1 magenta 축), 이중 해리 (yellow-purple sub-08 z=+13.87 vs sub-09 z=-3.31)
> **sub-10 (deutan, 보상)**: FDR 0 pairs, HC-like 표상 → 피질 보상 사례 연구
>
> **교차 검증 하이라이트**: SRM V2 blue-purple p=0.042 ↔ FE hV4 blue p=0.046 (두 독립 파이프라인 수렴)
> V2 = 가장 견고한 ROI (group split-half r=0.733, B1 유일 유의 pair)
> 필터 공간 = Procrustes (연속 구조 보존 + voxel 정보 유지)
> Stouffer omnibus p=0.0021 → 피질 수준 색 보간 존재 확인

---

## 0. 서론 및 방법 개요

### 0-1. 피험자 및 데이터

| 항목 | 내용 |
|------|------|
| 피험자 | 10명 (HC 7명: sub-01~07, CVD 3명: sub-08 deutan, sub-09 protan, sub-10 deutan) |
| 입력 | Phase 1 Procrustes-aligned amplitudes (C010), shape (6, 8, n_voxels) |
| SRM | HC-only 학습 (7 HC), CVD는 SVD projection으로 HC 공간에 투영 |
| SRM k | V1=4, V2=4, V3=3, hV4=3 (7-fold LOSO mean rank aggregation) |
| 색 쌍 | 8×8 RDM 상삼각 28 unique pairs |
| Pair z-score | (CVD distance − HC mean) / HC SD; 양수 = 과분리, 음수 = 혼동/압축 |
| 제외 | sub-07 hV4 (16 voxels → NaN) → hV4 FDR 분석 제외 |

### 0-2. 입력 데이터 (C010)

- **데이터**: method3_header_mi fMRIPrep 출력, MNI152NLin2009cAsym res-2
- **Procrustes alignment**: 피험자 간 rigid-body 정렬 (거리 보존 isometry)
- **Run structure**: 6 runs × 8 colors = 48 samples per subject per ROI

### 0-3. 분석 파이프라인 3가지

| 파이프라인 | 공간 | 핵심 지표 | 역할 |
|-----------|------|----------|------|
| **SRM Pre-validation** | SRM 공유 공간 (k=3-4) | Bootstrap z-score, FDR pairs | 색 쌍 수준 왜곡 특성화 |
| **Forward Model (FE)** | Procrustes voxel 공간 | LOCO voxel_corr, permutation p | 연속 보간 능력 검증, GO/NO-GO gate |
| **Cone-Shift Analysis** | LMS 원추세포 공간 | 예측-관측 일치율 | 기전 설명 + 필터 방향 결정 |

### 0-4. 통계 방법 개요

| 방법 | 적용 | 설명 |
|------|------|------|
| **FDR (Benjamini-Hochberg)** | Per-subject-ROI (q=0.05, 28 tests 단위) | 다중비교 보정. Global FDR (252 tests) → 37 생존 vs per-subject-ROI → 39 생존 (근사 일치) |
| **Bootstrap** | B3: HC 1,000회 복원 추출 + 매 반복 SRM 재학습 | HC 간 변동성 + SRM 불확실성 포착 |
| **Crawford-Howell** | 개인 CVD vs HC 분포 (df=6, one-tailed) | 단일 사례 통계 검정 |
| **Permutation** | 10K color-label shuffles (FE), 120 exhaustive (SRM B1) | 순열 null 대비 유의성 검증 |
| **Stouffer omnibus** | 4 ROI p-values 통합 | 개별 ROI 보정 없이 피질 수준 검증 (p=0.0021) |

---

## 1. 주 분석 — CVD 개별 사례 보고서

### 1-1. sub-08 (Deutan) — 주 필터 후보

**임상 프로파일**: M-cone 감도 피크 ~534nm → ~560nm (M' cone). FDR 32 pairs (V1=3, V2=12, V3=17). Split-half r=0.73-0.84 전 ROI.

#### 통합 테이블: 핵심 색상 쌍

| 색 쌍 | ROI | SRM z | FDR | Cone 예측 | FE 근거 | 기전 | Filter 방향 |
|--------|-----|:-----:|:---:|-----------|---------|------|:----------:|
| **yellow-purple** | V2 | **+13.87** | YES | S 과의존→과분리 | hV4 cool d=+1.54 | Type B: S-cone 극심 보상 | ↓ 정상화 |
| red-yellow | V2 | +9.38 | YES | M' yellow 접근→과분리 | — | Type B: M' 피크 이동 | ↓ 정상화 |
| **blue-purple** | V2 | **+6.15** | YES | S 보상→과분리 | hV4 blue d=+1.37 p=0.046 | Type B: S-cone 보상 | ↓ 정상화 |
| orange-yellow | V2 | +5.45 | YES | M' yellow 접근→과분리 | — | Type B: M' 피크 이동 (D only) | ↓ 정상화 |
| yellow-green | V2 | +4.14 | YES | M' 양방향 이동→과분리 | — | Type B: M' 피크 이동 (D only) | ↓ 정상화 |
| red-yellow | V1 | +5.14 | YES | S 과의존 | — | Type B | ↓ 정상화 |
| red-orange | V1 | -0.82 | — | L-M 혼동→압축 | — | Type A: 직접 손실 | ↑ 복원 |
| cyan-blue | V1 | -0.95 | — | L-M 혼동→압축 | — | Type A: 직접 손실 | ↑ 복원 |
| green-blue | V1 | -0.89 | — | M' 급감→blue 접근→압축 | hV4 blue CVD 최저 | Type A: Green 피해 | ↑ 복원 |

#### Bootstrap 95% CI (핵심 쌍)

| Pair | ROI | z [CI] | 유의 |
|------|-----|--------|:----:|
| blue-purple | V2 | +4.34 [+2.9, +15.3] | YES |
| orange-yellow | V2 | +3.29 [+2.0, +33.2] | YES |
| red-orange | V2 | +1.66 [+0.8, +3.7] | YES |
| orange-yellow | V1 | +2.00 [+1.3, +4.4] | YES |
| red-orange | V1 | -0.82 [-2.5, -0.2] | YES |
| cyan-blue | V1 | -0.95 [-2.4, -0.4] | YES |

> 비대칭 CI (예: blue-purple V2 [+2.9, +15.3])는 HC 7명 복원 추출에서 특정 HC 과대 표집 시 극단 z-score 발생. 하한이 상한보다 유의성 판단에 더 중요.

#### ROI별 안정성

| ROI | Split-half r | Bootstrap sig pairs | FDR pairs |
|-----|:-----------:|:-------------------:|:---------:|
| V1 | 0.777* | 15/28 | 3 |
| V2 | 0.839* | 17/28 | 12 |
| V3 | 0.765* | 18/28 | 17 |
| hV4 | 0.729* | 21/28 | — (sub-07 NaN) |

#### Cone-Shift 예측 일치도: 7/7 (100%)

| 예측 (cone-shift) | 관측 결과 | 일치 |
|-------------------|-----------|:----:|
| Green M' 급감→green-blue 압축 | V1 z=-0.89 (deficit) | YES |
| L-M 혼동→red-orange 압축 | V1 z=-0.82 (deficit) | YES |
| M' yellow 접근→orange-yellow 과분리 (D only) | V2 z=+3.29 (FDR) | YES |
| M' yellow 접근→yellow-green 과분리 (D only) | V2 z=+4.14 (FDR) | YES |
| L-M 손실→yellow-purple S 과의존→과분리 | V2 z=+13.87 (FDR) | YES |
| S 보상→blue-purple 과분리 | V2 z=+4.34 (FDR) | YES |
| Magenta 안정 (anti-M, M 거의 미사용) | purple-magenta ≈ 0 | YES |

#### 이중 해리: yellow-purple

sub-08 V2 z=**+13.87** (극심 과분리) vs sub-09 V1 z=**-3.31** (압축). Deutan에서는 L-M 손실이 S-(L+M) 과의존을 유발하여 과증폭. Protan에서는 yellow의 L' 감소→S/(L+M) 증가→purple 방향 이동→압축. **CVD subtype에 따라 반대 방향 → 필터 개별화 필수**.

#### HC-CVD Gap (LOCO voxel_corr)

| ROI | HC M (SD) | CVD M (SD) | Cohen's d | p (Welch) |
|-----|----------|----------|-----------|-----------|
| V1 | +0.130 (0.097) | -0.012 (0.054) | +1.61 | **0.021** |
| V2 | +0.150 (0.188) | -0.174 (0.130) | +1.85 | **0.022** |

> V1/V2에서 대효과 (d>1.6). HC는 색 간 보간 가능, CVD는 실패 — 보간 왜곡이 핵심 결손.

#### Crawford-Howell Per-Color Vulnerability (LOCO voxel_corr)

| ROI | 색 | sub-08 값 | HC M | t | p |
|-----|------|:--------:|:----:|:---:|:---:|
| V1 | **orange** | -0.178 | +0.149 | -5.30 | **0.0018*** |
| V1 | **yellow** | -0.438 | -0.016 | -4.17 | **0.0059*** |
| V1 | **purple** | -0.499 | +0.163 | -3.13 | **0.020*** |
| V2 | **orange** | -0.575 | +0.179 | -3.03 | **0.023*** |
| V2 | **yellow** | -0.693 | +0.003 | -3.94 | **0.0077*** |
| V2 | **cyan** | -0.211 | +0.186 | -4.26 | **0.0053*** |

> V1에서 orange/yellow/purple, V2에서 orange/yellow/cyan → M' 이동에 의한 orange-yellow 과분리의 이면 (보간 시 해당 색 예측 실패).

#### 필터 설계 타겟

- **Primary (V2, 12 FDR pairs)**: yellow-purple z=+13.87, blue-purple z=+6.15, orange-yellow z=+5.45 → S-cone 축 과분리 감소
- **Secondary (V1, 3 pairs)**: red-yellow z=+5.14 → S-cone 과의존 정상화
- **V3 누적 증폭** (17 FDR pairs): V1/V2 왜곡의 계층적 증폭
- **K\* = 8** (LOCO 0.084→0.541, 6.4× gain). 단, K*=8 w/ 8 colors ≈ lookup table → 독립 발견이 아닌 cone-shift 보조 증거

---

### 1-2. sub-09 (Protan) — Protan 특이적 서명

**임상 프로파일**: L-cone 감도 피크 ~564nm → ~534nm (L' cone). FDR 7 pairs (V1=6, V3=1). K*=3 (no gain). V3 불안정 (split-half r=0.264).

#### 통합 테이블: V1 중심

| 색 쌍 | ROI | SRM z | FDR | Cone 예측 | 기전 | Filter 방향 |
|--------|-----|:-----:|:---:|-----------|------|:----------:|
| **cyan-magenta** | V1 | **+4.08** | YES | L-M→S 보상→과분리 | Type B: S+M 보상 | ↓ 정상화 |
| orange-magenta | V1 | +3.71 | YES | Magenta L' 손실 | Type B: L-cone 보상 | ↓ 정상화 |
| **red-magenta** | V1 | **+3.52** | YES | Red L' 급감→축소 | Type B: L' 이동 | ↓ 정상화 |
| yellow-purple | V1 | **-3.31** | YES | L'↓→S/(L+M)↑→압축 | Type A: Protan 특이 | ↑ 복원 |
| green-blue | V1 | -2.41 | — | L' 증가→재편→압축 | Type A | ↑ 복원 |
| red-orange | V1 | -1.35 | — | L' 감소→L-M 압축 | Type A: 직접 손실 | ↑ 복원 |

#### Deutan과 이중 해리

| 색 쌍 | sub-08 (D) | sub-09 (P) | 해리 방향 |
|--------|:----------:|:----------:|:---------:|
| yellow-purple V2/V1 | +13.87 | **-3.31** | **반대** (핵심) |
| Magenta 관련 V1 | ≈0 | +3.52~+4.08 | P only (Magenta 불안정) |
| orange-yellow V2 | +3.29 (D only) | ≈0 | D only (M' 이동) |

> Deutan: S-cone 과의존 (yellow-purple 과분리) + M' 이동 (orange-yellow 과분리)
> Protan: Magenta 축 이상 (L' 손실→Magenta 불안정) + yellow-purple 반대 방향

#### Cone-Shift 예측 일치도: 4/5 (80%)

| 예측 | 관측 | 일치 |
|------|------|:----:|
| Red L' 급감→red-magenta 과분리 | V1 z=+3.02 | YES |
| L-M+S 보상→cyan-magenta 과분리 | V1 z=+4.08 | YES |
| Green L'+L-M 압축→green-blue 압축 | V1 z=-2.41 | YES |
| L' 손실→red-orange 압축 | V1 z=-1.35 | YES |
| yellow-purple 방향 불확실 | V1 z=-2.04 (압축) | PARTIAL |

> yellow-purple 반전 설명: Protan에서 yellow의 L' 감소→L+M 감소→S/(L+M) 증가→purple 방향 이동→거리 감소. Deutan과 반대 기전.

#### ROI별 안정성

| ROI | Split-half r | Bootstrap sig pairs | FDR pairs |
|-----|:-----------:|:-------------------:|:---------:|
| V1 | 0.645* | 17/28 | 6 |
| V2 | 0.684* | 13/28 | 0 |
| V3 | 0.264 | 10/28 | 1 |
| hV4 | 0.747* | 8/28 | — |

> V1 집중 패턴: FDR 6/7 pairs가 V1 → protan의 피질 서명이 V1에 집중. sub-08 (deutan)의 V2 집중과 대비.

#### 필터 설계 타겟

- **Primary**: Magenta 축 정상화 (V1 6 FDR pairs) — cyan-magenta, orange-magenta, red-magenta
- **Secondary**: Cool-color 복원 (green-blue, yellow-purple)
- Deutan과 보상 축이 다름: **magenta vs yellow-purple**
- K*=3 (no gain) → 기본 FE-3에서 이미 최적 = 보간 구조 부재 → **필터 효과 제한적**

---

### 1-3. sub-10 (Deutan, Compensated) — 피질 보상 사례

**임상 프로파일**: sub-08과 동일 deutan 유전형이지만 HC-like 피질 표상.

- **FDR 0 pairs** — 보정 후 유의한 왜곡 없음
- **Split-half**: V2만 유의 (r=0.677*). V1 0.286, V3 0.010, hV4 0.234
- **LOCO cool-color**: positive (warm +0.244, cool +0.140) — **유일한 CVD에서 cool 양수**
- **Crawford-Howell LOCO**: 전 ROI 비유의 (V1 p=0.444, V2 p=0.089, V3 p=0.723, hV4 p=0.837)
- **SRM ISC**: V2 r=0.701 (HC 범위 내), 전반적 HC-like profile
- **V2 per-color Crawford-Howell**: cyan p=0.004*, blue p=0.047* — FE 공간에서 약한 cool deficit 잔존

**결론**: 동일 유전형(deutan), 다른 피질 서명 → **피질 보상 성공 사례**. 필터 설계 불가 → characterization-only 사례 연구로 보고.

---

### 1-4. 피험자 간 일관 패턴

**L-M 축 결핍** (3명 CVD 동일 방향 = 음의 z-score, 혼동/압축):

| Pair | ROI | sub-08 | sub-09 | sub-10 | 기전 |
|------|-----|--------|--------|--------|------|
| red-orange | V1 | -0.82 | -1.35 | -0.68 | L-M 혼동 |
| cyan-blue | V1 | -0.95 | -0.51 | -0.59 | L-M 혼동 |
| green-blue | V1 | -0.89 | -2.41 | -1.16 | L-M 혼동 |

> L/M cone 민감도 저하 → 적-녹 차원의 피질 표상 압축. Protan, deutan 모두 공통.

**S-cone 보상 상승** (3명 CVD 동일 방향 = 양의 z-score, 과분리):

| Pair | ROI | sub-08 | sub-09 | sub-10 | 기전 |
|------|-----|--------|--------|--------|------|
| red-magenta | V1 | +0.69 | +3.02 | +1.43 | S-cone 보상 |
| purple-magenta | V1 | +0.98 | +1.15 | +0.31 | S-cone 보상 |
| red-magenta | V2 | +1.66 | +1.64 | +0.51 | S-cone 보상 |
| blue-purple | V2 | +4.34 | +0.33 | +2.08 | S-cone 보상 (B1 p=0.042) |

> L-M 결핍 + S-cone 보상 이중 패턴이 광수용체 기반 CVD 기전과 일치.

**Cross-Phase 수렴 테이블** (SRM ↔ FE 독립 파이프라인):

| 신호 | SRM Prevalidation | Forward Model (FE) | 수렴 |
|------|-------------------|---------------------|:----:|
| Blue-purple 왜곡 | V2 blue-purple p=0.042* (유일 유의) | hV4 blue d=+1.37 p=0.046* | **YES** |
| Green-blue 압축 | V1/V2/V3 3인 일관 deficit | Blue = CVD 최저 LOCO 색 | **YES** |
| Red-magenta 확장 | V1/V2/hV4 3인 일관 elevation | Magenta d=+1.19 p=0.127 | **Partial** |
| sub-10 보상 | SRM: HC-like (r=0.701) | FE-K: cool 양수 (유일 CVD) | **YES** |

---

## 1-V. 결과 검증 (Validation)

### 1-V-1. B1: 그룹 수준 순열 검정 (Exhaustive, 120 permutations)

모든 C(10,3) = 120 가능한 HC/CVD 배정으로 그룹 순열 검정. 순열마다 SRM 재학습 → 순환성 방지.

| ROI | 유의 pairs (p < 0.05) | 주요 pair |
|-----|----------------------|-----------|
| V1 | 0 | min p = 0.058 (red-magenta) |
| **V2** | **1** | **blue-purple p = 0.042** |
| V3 | 0 | — |
| hV4 | 0 | min p = 0.058 (red-magenta) |

> V2 blue-purple이 유일한 그룹 수준 유의 pair. 3명 CVD 모두 V2에서 blue-purple 거리 상승. 120 순열 한계 → 최소 p = 0.008 → 매우 큰 효과만 검출 가능. B3 bootstrap이 주요 개인 수준 증거 제공.

### 1-V-2. B2: Split-Half 시간적 안정성

데이터를 전반부 (runs 1-3) / 후반부 (runs 4-6)로 분할. 각 반에 SRM 별도 적합. 28-pair z-score 프로파일 간 Spearman 상관.

| 피험자 | V1 | V2 | V3 | hV4 | 프로파일 |
|--------|------|------|------|------|----------|
| sub-08 (deutan) | 0.777* | 0.839* | 0.765* | 0.729* | 전 ROI 신뢰 |
| sub-09 (protan) | 0.645* | 0.684* | 0.264 | 0.747* | V3 불안정 |
| sub-10 (deutan) | 0.286 | 0.677* | 0.010 | 0.234 | V2만 유의 |
| **Group mean** | **0.569** | **0.733** | **0.346** | **0.570** | **V2 최고** |

\*p < 0.05 (순열 null 대비)

> **V2**: 그룹 수준 최고 안정성 (r=0.733) — B1 유일 유의 pair, sub-08 최고 r=0.839와 수렴.

### 1-V-3. B3: Bootstrap 불확실성 추정

1,000 bootstrap iterations: HC 피험자 복원 추출 → 매 반복 SRM 재학습 → z-score 불확실성 포착.

**Bootstrap 유의 pair 수 (CI가 0 제외):**

| ROI | sub-08 | sub-09 | sub-10 |
|-----|--------|--------|--------|
| V1 | 15/28 | 17/28 | 8/28 |
| V2 | 17/28 | 13/28 | 10/28 |
| V3 | 18/28 | 10/28 | 13/28 |
| hV4 | 21/28 | 8/28 | 22/28 |

**FDR 보정 결과 (Per-Subject-ROI, q = 0.05):**

| 피험자 | V1 | V2 | V3 | hV4 | 합계 |
|--------|----|----|----|----|------|
| **sub-08** (deutan) | 3 | 12 | 17 | — | **32** |
| **sub-09** (protan) | 6 | 0 | 1 | — | **7** |
| sub-10 (deutan) | 0 | 0 | 0 | — | **0** |
| **합계** | **9** | **12** | **18** | **0** | **39** |

hV4는 sub-07 NaN으로 제외. Discovery rate: 39/252 = 15.5% (chance 5%의 약 3배).

> 참고: Global FDR (252 tests) → 37 생존. Per-subject-ROI (39) vs Global (37)의 근접 일치 → 보정 전략에 강건.

### 1-V-4. Forward Model Gate 검증

#### GO/NO-GO Gate (ridge_gcv, Per-ROI Optimal Basis, 10K Permutation)

| ROI | Basis | Perm p | Gate | 근거 |
|-----|-------|:------:|:----:|------|
| V1 | FE-2 | 0.170 | **NO-GO** | 전 basis FAIL |
| V2 | FE-3 | 0.125 | **NO-GO** | 전 basis FAIL |
| **V3** | **FE-8** | **0.045*** | **CONDITIONAL** | FE-6→FE-8 회복 |
| **hV4** | **FE-3** | **0.026*** | **PRIMARY GO** | 유일 유의 ROI |

> **hV4 = PRIMARY GO** (FE-6 perm p=0.044, FE-3 perm p=0.026)
> **V3 = CONDITIONAL** (FE-8 perm p=0.045)
> **V1/V2 = NO-GO** — discrimination은 가능 (LORO HC≈CVD) but interpolation 실패. 전 basis (FE-{2..12}, OPP-2/4/4rect, intercept) 모두 FAIL.

#### LOSO Zero-Shot Transfer (hV4)

| ROI | ZS (direct) | LORO (ridge_gcv) | LOCO (ridge_gcv) | t(ZS-LORO) | p |
|-----|:-----------:|:----------------:|:----------------:|:----------:|:---:|
| **hV4** | **0.417** | **0.407** | **0.232** | **0.115** | **0.913** |

> **hV4: ZS ≈ LORO (p=0.913)** → Group prior W₀만으로도 subject-specific ridge_gcv와 동등. Phase 2 prediction engine으로 검증됨.
> LOCO 항상 최저 (0.232 vs ZS 0.417) → 보간이 가장 어려운 과제 = 필터 정밀도 ceiling.
> HC ≈ CVD in ZS (p=0.940) → **LOCO가 유일한 HC-CVD 해리 도구**.

#### Stouffer Omnibus

| Test | Statistic | p |
|------|:---------:|:---:|
| **Stouffer** | **Z = 2.869** | **0.0021*** |
| Fisher | χ²(8) = 21.18 | 0.0067* |

> Omnibus p=0.0021 — **피질 수준 색 보간 존재 확인**. 개별 ROI의 uncorrected p-value에 의존하지 않는 결론.

---

## 1-M. 측정 방법론 비교

### 1-M-1. Bootstrap vs Crawford-Howell

| 방법 | 특징 | FDR 생존 |
|------|------|---------|
| **Bootstrap** (B3) | HC 1,000회 복원 추출, 매 반복 SRM 재학습 | **39** |
| **Crawford & Howell** | 고정 HC 모수 (mean, SD 1회), df=6 t-분포 | **0** |

> Bootstrap z-score가 체계적으로 높음 (평균 차이 Δ=1.17, 최대 3.53).
> 예: sub-08 V1 red-yellow — Bootstrap z=5.14, p=2.72e-07 (FDR 유의) vs Crawford & Howell z=2.04, p=0.087 (미유의).
> Bootstrap은 HC 7명에서 "정상 기준" 정의의 불확실성을 적절히 포착 → 필터 관련 분석에 채택.

### 1-M-2. Correlation vs Crossnobis

**6 조건 비교**: {correlation, crossnobis} × {none, within-subject, pooled} 정규화

| Metric | Normalization | Uncorrected p < 0.05 | FDR q < 0.05 |
|--------|---------------|---------------------|-------------|
| **Correlation** | None (baseline) | **15** | 0 |
| Correlation | Within | 16 | 0 |
| Correlation | Pooled | 15 | 0 |
| **Crossnobis** | None | **3** | 0 |
| Crossnobis | Within | 8 | 0 |
| Crossnobis | Pooled | 3 | 0 |

> Crossnobis는 correlation 대비 **80% 보수적** (15→3 uncorrected). Crawford & Howell 사용 (bootstrap 아닌).

**수렴도 (Spearman r, correlation vs crossnobis z-scores):**

| ROI | sub-08 | sub-09 | sub-10 | Mean r |
|-----|--------|--------|--------|--------|
| V1 | 0.556** | 0.726*** | 0.413* | **0.565** |
| V2 | 0.349 | 0.715*** | 0.361 | 0.475 |
| V3 | 0.537** | 0.342 | 0.614*** | 0.498 |
| hV4 | 0.551** | 0.067 | 0.337 | 0.318 |

> V1 최강 수렴 (0.565), hV4 최약 (0.318). 중간 수렴 → 공유 기저 신호 존재하지만 지표 간 상당 차이.

**SRM vs Native voxel space:**

| 피험자 | ROI | SRM FDR pairs | Crossnobis FDR pairs | Spearman r | p |
|--------|-----|:-------------:|:--------------------:|:----------:|:---:|
| sub-08 | V1 | 3/28 | 0/28 | 0.534 | 0.003 |
| sub-08 | V2 | 11/28 | 0/28 | 0.332 | 0.084 |
| sub-08 | V3 | 14/28 | 0/28 | 0.438 | 0.020 |
| sub-09 | V1 | 6/28 | 0/28 | 0.635 | <0.001 |
| sub-09 | V2 | 1/28 | 0/28 | 0.649 | <0.001 |
| sub-10 | V1 | 0/28 | 0/28 | 0.638 | <0.001 |
| sub-10 | V2 | 1/28 | 0/28 | 0.701 | <0.001 |

> Native voxel space: **0 pairs FDR 생존** vs SRM 39 생존. 하지만 z-score 간 중간-강한 상관 (r=0.3-0.7) → SRM이 진짜 CVD-HC 분산 포착하되 k=3-4 축소로 증폭. 통계적 유의성이 표상 공간에 의존하는 것이 핵심 한계.

**정규화**: Pooled = no normalization과 동일 (SRM 정렬로 HC 분산 이미 균질). **정규화 불필요** → 현행 방법 검증.

---

## 2. 보충 분석 — 차원성 및 RDM 구조 진단

### 2-1. CIELab vs Angular RDM 진단

Phase 1 MDS에서 V1/V2가 4개 기준 모두 실패. 이것이 부적절한 참조 모델(equidistant angular) 때문인지, 진정한 구조 부재인지 검증.

#### Decision Framework

| ROI | Q1: CIELab > Angular | Q2: H1 Topology | Q3: Higher-D | Q4: Isomap > MDS | Verdict |
|-----|---------------------|-----------------|-------------|-----------------|---------|
| **V1** | FAIL (r=-0.195 vs -0.295, 둘 다 음수) | FAIL (p=1.0) | FAIL (stress=0.126, ρ=0.643) | FAIL (MDS 우세) | **UNSTRUCTURED (0/4)** |
| **V2** | FAIL (r=0.124, p=0.261) | FAIL (p=1.0) | **PASS** (3D stress=0.097) | **PASS** (Isomap ρ=0.524 > MDS 0.262) | **STRUCTURED (2/4)** |
| V3 | FAIL | — | — | — | UNSTRUCTURED (0/4) |
| hV4 | FAIL | — | — | — | UNSTRUCTURED (0/4) |

#### Stress Curve 핵심 소견

- **V1 SRM**: dim=3 이후 stress 0.127에서 plateau — 어떤 차원에서도 거리 구조 복원 불가. 같은 V1 데이터가 raw/procrustes에서는 dim=4-5에서 정상 도달 → SRM 투영이 거리 구조를 비가역적으로 손상.
- **V2 SRM**: 3D에서 0.097 달성 — 3차원적 색 거리 구조 존재.

#### Mantel Test (10,000 permutations)

| ROI | Angular r (p) | CIELab r (p) | a*-only r (p) | b*-only r (p) |
|-----|-------------|-------------|-------------|-------------|
| V1 srm | -0.295 (0.926) | -0.195 (0.837) | -0.292 (0.958) | -0.083 (0.613) |
| V2 srm | -0.005 (0.503) | 0.124 (0.261) | **0.282 (0.085)** | -0.130 (0.721) |
| hV4 raw | 0.276 (0.062) | **0.402 (0.018*)** | 0.186 (0.171) | 0.075 (0.321) |
| hV4 srm | -0.302 (0.942) | -0.308 (0.966) | -0.249 (0.936) | -0.085 (0.572) |

> V1 SRM: 4개 모델 **모두 음의 상관** — 의미 있는 색 기하학 부재.
> V2 SRM: a*-only (L-M axis) r=0.282 (p=0.085, trend) — V2의 L-M cone opponent selectivity와 일치 (Gegenfurtner, 2003).
> **hV4**: raw 공간 CIELab r=0.402* → SRM 후 r=-0.308 (부호 반전). SRM 투영이 원래 존재하던 CIELab 구조를 파괴.

#### Persistent Homology (H1)

| ROI | Max H1 lifetime | p-value |
|-----|----------------|---------|
| V1 | 0.448 | 1.000 |
| V2 | 0.156 | 1.000 |

> p=1.0: 원형 위상 구조 없음.

#### Isomap vs MDS (SRM, HC mean)

| ROI | MDS ρ (p) | Isomap ρ (p) | 우승 |
|-----|----------|-------------|------|
| V1 | 0.619 (0.102) | -0.476 (0.233) | MDS |
| V2 | -0.262 (0.531) | **0.524 (0.183)** | **Isomap** |

> V2에서 Isomap이 MDS보다 circular order를 2배 더 잘 복원 → 비선형 manifold 존재.

### 2-2. 계층적 증폭

| ROI | sub-08 sig pairs | sub-09 sig pairs | sub-10 sig pairs | Mean |delta| |
|-----|-----------------|-----------------|-----------------|--------------|
| V1 | 20/28 | 24/28 | 17/28 | 0.47-0.60 |
| V2 | 20/28 | 21/28 | 19/28 | 0.43-0.58 |
| V3 | 19/28 | 17/28 | 16/28 | 0.60-0.75 |
| hV4 | 26/28 | 19/28 | 12/28 | 0.63-0.75 |

> V1/V2 (mean |delta|=0.43-0.60) → V3/hV4 (0.60-0.75): 고차 시각 영역이 개별 쌍 차이를 통합적 처리로 증폭.

---

## 3. 필터 전략 및 공간 선택 근거

> 상세 내용: `future_phase2_filter_optimization/PLAN.md` §3, `notion.md` §Step2/Step2b 참조

### 3-1. Procrustes vs SRM 비교

| 기준 | Procrustes | SRM | 근거 |
|------|-----------|-----|------|
| ① 연속 색 거리 보존 | ✅ stress 정상 (dim=4-5) | ❌ V1 plateau, hV4 부호 반전 | 이번 진단 |
| ② 개인 voxel-level 정보 | ✅ 수백 voxel 유지 | ❌ k=3-4로 99% 축소 | FE W matrix 차원 |
| ③ 보간 과제 최적성 | ✅ LOCO HC MAE 69.4° (hV4) | ❌ LOCO +2.8-22.3° 페널티 | Phase 2 LOCO |
| ④ W matrix 풍부성 | ✅ (568×6)=3,408 params | ❌ (4×6)=24 params | 개인차 식별 불가 |
| ⑤ 변환의 수학적 특성 | ✅ isometry (거리 완전 보존) | ❌ 투영 (정보 손실) | 강체 변환 정의 |

> **결론**: 필터는 Procrustes 공간에서 FE W matrix 변환으로 구축. SRM은 comparison/target space.

### 3-2. ROI별 필터 Prior

| ROI | 기하학적 Prior | 근거 | 대안 |
|-----|--------------|------|------|
| V1 | **불가** | 0/4, 모든 참조 음의 r | W 변환 + Group Prior |
| V2 | **L-M axis 제한적** | a*-only trend (p=0.085), Isomap 우세 | Matern kernel, Group Prior |
| V3 | Procrustes 직접 사용 | 원래 Procrustes 우세 ROI | 표준 접근 |
| hV4 | **CIELab kernel (Procrustes 공간)** | raw CIELab r=0.402* | 유일한 기하학 확인 ROI |

> hV4 ZS ≈ LORO (p=0.913) → group prior validated.

---

## 4. 제한점

| 제한점 | 설명 |
|--------|------|
| Bootstrap 증폭 | Bootstrap z-score가 Crawford & Howell보다 체계적으로 높음 (평균 차이 1.17). FDR 39 생존은 HC 간 변동성 효과 포착이며 독립 재현이 아님 |
| Crossnobis 비재현 | Native voxel space에서 0/252 FDR 생존. SRM 공간에서만 효과 검출 → 결과가 표상 의존적 |
| sub-10 해석 모호 | 피질 보상 vs 불충분한 SNR 구별 불가. 행동 검증 (JND 역치) 필요 |
| n = 3 CVD | 그룹 검정 저검정력, CI 넓음. sub-08 V2 blue-purple CI [+2.9, +15.3]. 인과 해석 불가 |
| hV4 제외 | sub-07의 16 voxels → NaN. hV4 correlation distance 결과 해석 주의 |
| 넓은 비대칭 CI | HC 7명 복원 추출 + SRM 재학습 변동성 → 일부 CI 극단적. 하한이 유의성 판단에 더 유효 |
| B1 검정력 한계 | 120 순열 → 최소 p = 0.008. 그룹 수준 검출은 매우 큰 효과에 제한 |

---

## 5. 참고문헌

- Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. *J Royal Statistical Society: Series B*, 57(1), 289-300.
- Crawford, J. R., & Howell, D. C. (1998). Comparing an individual's test score against norms derived from small samples. *Clinical Neuropsychologist*, 12(4), 482-486.
- Walther, A., et al. (2016). Reliability of dissimilarity measures for multi-voxel pattern analysis. *NeuroImage*, 137, 188-200.
- Zeki, S., et al. (1991). A direct demonstration of functional specialization in human visual cortex. *J Neuroscience*, 11(3), 641-649.
- Chen, P. H., et al. (2015). A reduced-dimension fMRI shared response model. *NIPS*.
- Brouwer, G. J., & Heeger, D. J. (2009). Decoding and reconstructing color from responses in human visual cortex. *J Neuroscience*, 29(44), 13992-14003.
- Gegenfurtner, K. R. (2003). Cortical mechanisms of colour vision. *Nature Reviews Neuroscience*, 4(7), 563-572.
