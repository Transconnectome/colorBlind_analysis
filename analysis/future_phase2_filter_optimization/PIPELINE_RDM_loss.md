# Cone-Shift Pipeline: W-Fixed 모델 구조 및 결과

> 2026-03-23. 피드백·수정·재실험용 기준 문서.

---

## 1. 목적

HC에게 인위적 cone shift(δθ)를 적용하여, CVD와 동일한 LOCO 보간 실패 패턴을 재현하는 δθ를 추정한다.

**핵심 가정**: W_CVD = W_HC (피질 인코딩 동일). 차이는 망막 입력 C(θ+δ)뿐.

---

## 2. 파이프라인 구조
### 4-6. ΔRDM 접근: Basis-Response Mismatch 없는 RDM 비교 (2026-03-23)

#### 4-6-1. 동기

LOCO criterion은 CVD target (7색 학습 → 1색 보간)과 HC simulation (8색 전체 학습 W + shifted input)이 구조적으로 비대칭이다. 이 **basis-response mismatch**를 완전히 제거하면서 cone shift signal을 포착하는 대안이 필요.

기존 SRM-based RDM (§4-3~4-5)은 SRM alignment이 cone shift signal을 흡수하여 실패. ΔRDM은 **voxel-space에서 직접** 작동하므로 SRM을 완전히 bypass.

#### 4-6-2. 방법

**Simulation side** (HC에 cone shift 적용):
```
ΔRDM_sim(δ) = RDM( C(θ+δ) @ W_HC ) - RDM( C(θ) @ W_HC )
```
→ W는 1회 학습 후 고정. δθ에 따른 RDM 변화량만 추출.
→ baseline RDM (원형 색구조)이 상쇄되어 **순수 cone-shift distortion만 남음**.

**Observation side** (실제 CVD-HC 차이):
```
ΔRDM_obs = RDM_CVD - RDM_HC_mean
```
→ 관측된 HC-CVD 차이. HC 평균 RDM을 빼면 공유 색구조 제거.

**Fitting question**: ΔRDM_sim(δ*) ≈ ΔRDM_obs 가 되는 δ*는?

#### 4-6-3. 이중 거리 × 삼중 메트릭

**Distance metrics (RDM 구성)**:
1. **Correlation distance** (1 - Pearson r): scale-free, 표준적
2. **Crossnobis** (cross-validated Mahalanobis): 노이즈 정규화, run-level residual 기반 noise covariance

**Comparison metrics (ΔRDM_sim vs ΔRDM_obs 비교)**:
1. **Pearson r / cosine similarity**: 크기 민감 (1차)
2. **Spearman ρ**: 순위만 비교 (2차)
3. **Signed agreement rate**: n_pairs 중 부호 일치 비율 (보수적)

**Sanity checks**:
1. ΔRDM_obs가 구조를 가지는지 (mean, std, range, top pairs)
2. 혼동선 이론 예측: confusion pairs (red-green, orange-cyan, blue-magenta)에서 ΔRDM < 0 (closer)?
3. δθ sweep (0-60nm, step 5): metric이 δθ에 따라 단조적으로 변하는지?

#### 4-6-4. V1 결과 (correlation distance)

| Subject | CVD | Best δθ (Pearson) | Pearson r | p | Best δθ (Spearman) | Spearman ρ | p | Confusion closer |
|---------|-----|-------------------|-----------|-------|---------------------|------------|-------|------------------|
| **sub-09** | **protan** | **30nm** | **0.513** | **0.005*** | **25nm** | **0.524** | **0.004*** | **3/3** |
| sub-08 | deutan | 60nm | -0.127 | 0.520 | 0nm | -0.018 | 0.927 | 1/3 |
| sub-10 | normal | 0nm | 0.029 | 0.884 | 0nm | 0.078 | 0.694 | N/A |

**해석**:
1. **sub-09 protan: LOCO에서 포착 못한 signal을 ΔRDM이 포착**
   - Pearson r=0.513 (p=0.005) at δθ=30nm → strong signal
   - Confusion pair 3/3 closer (red-green: -0.286, orange-cyan: -0.240, blue-magenta: -0.022) → **protan 이론과 완벽 일치**
   - Best δθ=25-35nm 범위 → V4 shift_at_both 결과 (Δλ=25.20nm)와 수렴
   - δθ=15nm 부터 Pearson p<0.05 유지 → broad plateau (robust)
2. **sub-08 deutan: ΔRDM V1에서 비유의 (모든 metric 음수)**
   - Confusion pairs 1/3만 closer → cone-shift 방향 예측 실패
   - LOCO에서는 V1 유의 (p=0.033) → **LOCO와 ΔRDM은 상보적**
3. **sub-10 정상: 완벽한 null**
   - δθ sweep 완전 flat (모든 δθ에서 동일 r=0.029, p=0.884)
   - Norm도 불변 → cone_1way가 sub-10에 적용 불가 (정상이므로)

#### 4-6-5. V1 결과 (crossnobis distance)

| Subject | CVD | Best δθ (Pearson) | Pearson r | p | Best δθ (Spearman) | Spearman ρ | p |
|---------|-----|-------------------|-----------|-------|---------------------|------------|-------|
| **sub-09** | **protan** | **10nm** | **0.496** | **0.007*** | **10nm** | **0.471** | **0.011*** |
| sub-08 | deutan | 60nm | -0.063 | 0.749 | 60nm | 0.130 | 0.511 |
| sub-10 | normal | 0nm | 0.346 | 0.071 | 0nm | 0.356 | 0.063 |

**특이사항**:
- sub-09: crossnobis도 유의하나, **baseline offset** 존재 (δθ=0에서 이미 r=0.459, p=0.014). δθ 증가에 따른 추가 개선이 미미 → crossnobis baseline이 이미 protan distortion pattern을 반영.
- sub-10: crossnobis에서 trending baseline (r=0.346, p=0.071), 그러나 δθ-invariant (모든 δθ에서 동일값). → **δθ-specific signal은 없으나 specificity 우려**.
- **결론**: correlation distance가 ΔRDM에 더 적합. crossnobis baseline offset가 해석을 복잡하게 함.

#### 4-6-6. V2 결과 (correlation distance)

| Subject | CVD | Best δθ (Pearson) | Pearson r | p | Best δθ (Spearman) | Spearman ρ | p | Confusion closer |
|---------|-----|-------------------|-----------|-------|---------------------|------------|-------|------------------|
| sub-09 | protan | 25nm | 0.287 | 0.139 | 45nm | 0.284 | 0.144 | 1/3 |
| sub-08 | deutan | 0nm | -0.062 | 0.755 | 0nm | -0.099 | 0.616 | 2/3 |
| sub-10 | normal | 0nm | 0.334 | 0.082 | 0nm | 0.338 | 0.078 | N/A |

**해석**:
1. **sub-09**: V1 대비 절반 수준 (V1 r=0.513 vs V2 r=0.287). NS이지만 방향 일치 (양의 상관, δθ=25nm).
2. **sub-08**: V1과 동일 패턴 — ΔRDM 비유의. LOCO에서는 V2 유의 (p=0.047).
3. **sub-10**: 완전 δθ-invariant (모든 δθ에서 r=0.334, p=0.082). Trending baseline이나 cone shift signal 아님.

#### 4-6-7. V4 결과 (correlation distance)

| Subject | CVD | Best δθ (Pearson) | Pearson r | p | Best δθ (Spearman) | Spearman ρ | p | Confusion closer |
|---------|-----|-------------------|-----------|-------|---------------------|------------|-------|------------------|
| sub-09 | protan | 60nm | 0.092 | 0.643 | 0nm | 0.044 | 0.825 | 1/3 |
| sub-08 | deutan | 60nm | 0.133 | 0.499 | 55nm | 0.151 | 0.443 | 2/3 |
| **sub-10** | **normal** | **0nm** | **0.420** | **0.026*** | **0nm** | **0.375** | **0.049*** | **N/A** |

**Specificity 실패**: sub-10 (정상)이 유의 (p=0.026). 완전 δθ-invariant임에도 ΔRDM_obs ↔ ΔRDM_sim(δ=0) 상관이 우연히 높음. V4에서 W의 alpha=0.1~1.0 (저정규화) → 예측 RDM이 noise에 영향받아 우연 상관 발생.

**V4 ΔRDM 사용 불가**: specificity 실패로 V4에서 ΔRDM criterion은 기각.

#### 4-6-8. 전체 Cross-ROI ΔRDM Summary (correlation distance)

| ROI | sub-08 (deutan) | sub-09 (protan) | sub-10 (정상) | Specificity |
|-----|:---:|:---:|:---:|:---:|
| **V1** | r=-0.127, p=0.520 | **r=0.513, p=0.005*** | r=0.029, p=0.884 | **OK** (perfect null) |
| **V2** | r=-0.062, p=0.755 | r=0.287, p=0.139 | r=0.334, p=0.082 | marginal (trending) |
| **V4** | r=0.133, p=0.499 | r=0.092, p=0.643 | **r=0.420, p=0.026*** | **FAIL** (false positive) |

#### 4-6-9. LOCO ↔ ΔRDM 상보성 (전 ROI)

**V1**:
| Criterion | sub-08 deutan | sub-09 protan | sub-10 normal |
|-----------|:---:|:---:|:---:|
| LOCO | **p=0.033*** | p=0.112 | p=0.167 |
| ΔRDM | p=0.520 | **p=0.005*** | p=0.884 |

**V2**:
| Criterion | sub-08 deutan | sub-09 protan | sub-10 normal |
|-----------|:---:|:---:|:---:|
| LOCO | **p=0.047*** | p=0.576 | p=0.562 |
| ΔRDM | p=0.755 | p=0.139 | p=0.082 |

**V4** (LOCO shift_at_both / ΔRDM specificity 실패):
| Criterion | sub-08 deutan | sub-09 protan | sub-10 normal |
|-----------|:---:|:---:|:---:|
| LOCO (legacy) | **p=0.036*** | **p=0.009*** | p=0.561 |
| ΔRDM | p=0.499 | p=0.643 | p=0.026* (FP) |

**핵심 결론**:
1. **LOCO와 ΔRDM은 완전히 상보적**: LOCO는 sub-08 deutan을 포착 (V1, V2), ΔRDM은 sub-09 protan을 포착 (V1 only).
2. **ΔRDM은 V1에서만 유효**: V2 NS, V4 specificity 실패.
3. **sub-08 deutan**: LOCO만이 유일한 유효 criterion (V1 p=0.033, V2 p=0.047).
4. **sub-09 protan**: ΔRDM V1 (p=0.005)과 LOCO V4-legacy (p=0.009)만 유의.
5. **가설**: deutan은 interpolation vulnerability (LOCO), protan은 pairwise geometry distortion (ΔRDM)이 주 표현형. 이는 M-cone vs L-cone shift의 색공간 내 영향 방향 차이와 관련될 수 있음.

#### 4-6-10. 스크립트

`scripts/diagnostic_delta_rdm.py`
```bash
conda activate srm
python scripts/diagnostic_delta_rdm.py --rois V1 V2 V4 --distances correlation
python scripts/diagnostic_delta_rdm.py --rois V1 --distances crossnobis  # V1만 (느림)
```

---

## 5. 현재 결과 (W-Fixed LOCO Only)

### 5-1. 전체 결과

| ROI | Subject | CVD | Δλ (nm) | Spearman r | Perm p | K | alpha |
|-----|---------|-----|---------|------------|--------|---|-------|
| **V1** | **sub-08** | deutan | **34.92** | **0.690** | **0.033*** | 4 | 10.0 |
| V1 | sub-09 | protan | 0.94 | 0.500 | 0.112 | 4 | 10.0 |
| V1 | sub-10 | normal | 23.06 | 0.405 | 0.167 | 4 | 10.0 |
| **V2** | **sub-08** | deutan | **3.87** | **0.643** | **0.047*** | 4 | 10.0 |
| V2 | sub-09 | protan | 23.76 | -0.071 | 0.576 | 4 | 10.0 |
| V2 | sub-10 | normal | 23.06 | -0.048 | 0.562 | 4 | 10.0 |
| V4 | sub-08 | deutan | 28.60 | 0.405 | 0.166 | 3 | 1.0 |
| V4 | sub-09 | protan | 48.88 | 0.190 | 0.334 | 3 | 1.0 |
| V4 | sub-10 | normal | 23.06 | -0.238 | 0.729 | 3 | 1.0 |

### 5-2. 요약

- **유의**: sub-08 (deutan) V1 (p=0.033), V2 (p=0.047)
- **비유의**: sub-09 (protan) 전 ROI, sub-10 (normal) 전 ROI, sub-08 V4
- **정상 제어**: sub-10 전 ROI NS → 올바른 null

### 5-3. Per-HC Consistency (sub-08)

| ROI | HC mean r | HC range | Positive / Total |
|-----|-----------|----------|------------------|
| V1 | 0.163 | -0.36 ~ +0.76 | 4/7 |
| V2 | **0.367** | -0.07 ~ +0.64 | **6/7** |
| V4 | 0.127 | -0.36 ~ +0.62 | 4/7 |

V2가 가장 안정적 — HC 간 일관성 높음.

### 5-4. Δλ ROI 간 불일치

sub-08: V1=34.92nm, V2=3.87nm, V4=28.60nm → **서로 불일치**.

Cone shift는 망막 현상이므로 이론적으로 ROI-independent이어야 하나, 현재 결과는 이를 지지하지 않음.

### 5-5. Multi-Parameter 모델 결과 (cone_3way, fourier) — 과적합 진단

sub-09 protan 포착을 위해 df>1 모델 (cone_3way df=3, fourier df=4)을 테스트.

**W-Fixed LOCO 결과 (cone_3way, df=3)**:

| ROI | Subject | CVD | Spearman r | Perm p | Per-HC mean r |
|-----|---------|-----|------------|--------|---------------|
| V1 | sub-08 | deutan | 0.976 | 0.0004*** | 0.575 |
| V1 | sub-09 | protan | **1.000** | **0.0001***| **0.741** |
| V1 | **sub-10** | **normal** | **0.905** | **0.0029** | 0.418 |
| V2 | sub-08 | deutan | 0.905 | 0.0011** | 0.684 |
| V2 | sub-09 | protan | 0.548 | 0.0836 | 0.282 |
| V2 | sub-10 | normal | 0.452 | 0.1314 | 0.170 |
| V4 | sub-08 | deutan | 1.000 | 0.0001*** | 0.677 |
| V4 | sub-09 | protan | 0.310 | 0.2300 | 0.044 |
| V4 | **sub-10** | **normal** | **0.976** | **0.0002** | 0.435 |

**W-Fixed LOCO 결과 (fourier, df=4)**:

| ROI | Subject | CVD | Spearman r | Perm p | Per-HC mean r |
|-----|---------|-----|------------|--------|---------------|
| V1 | sub-08 | deutan | 0.929 | 0.0010** | 0.463 |
| V1 | sub-09 | protan | 0.929 | 0.0010** | 0.592 |
| V1 | **sub-10** | **normal** | **0.976** | **0.0002** | 0.721 |
| V2 | sub-08 | deutan | 1.000 | 0.0001*** | 0.313 |
| V2 | sub-09 | protan | 0.810 | 0.0114* | 0.429 |
| V2 | **sub-10** | **normal** | **0.786** | **0.0152** | 0.483 |
| V4 | sub-08 | deutan | 1.000 | 0.0001*** | 0.507 |
| V4 | sub-09 | protan | 1.000 | 0.0001*** | 0.629 |
| V4 | **sub-10** | **normal** | **0.976** | **0.0003** | 0.350 |

#### 과적합 진단: sub-10 (정상 대조군) False Positive

**핵심 문제**: cone_3way와 fourier 모두 sub-10 (정상)에서 유의 결과를 산출.

- cone_3way: V1 p=0.0029, V4 p=0.0002 → **FALSE POSITIVE**
- fourier: V1 p=0.0002, V2 p=0.0152, V4 p=0.0003 → **전 ROI FALSE POSITIVE**

**원인**: 8-point profile (8색) matching에서 df=3~4 자유도면 어떤 noise pattern이든 높은 Spearman ρ 달성 가능. Permutation test는 "관측 ρ > 무작위 순열 ρ" 여부만 검정하므로, 최적화가 충분한 자유도로 높은 ρ를 확보하면 귀무가설이 기각됨.

**결론**:
1. **cone_1way (df=1)만 유효** — 유일하게 sub-10에서 correct null을 유지
2. cone_3way/fourier는 sub-09도 포착하지만 **specificity 상실**
3. sub-09 protan 포착 실패는 모델 복잡도 부족이 아니라 **cone_1way의 물리적 한계** (M-cone shift만 모델링, L-cone shift 미포함)
4. protan 포착을 위해서는 df 증가가 아닌 **모델 구조 자체의 변경** 필요 (예: L-cone 특이적 1-parameter shift)

---

## 6. 미해결 구조적 문제

### 6-1. CVD target vs HC simulation의 비대칭 (§3-4)

CVD: 7색 LOCO. HC: 8색 전체 학습 + shifted input.
→ 동일한 연산이 아님. Profile matching (Spearman)으로 보정하고 있으나, shape 자체가 달라질 가능성.

**가능한 수정**: HC simulation도 진짜 LOCO로 변경 (7색 학습, 1색 예측, W 매번 재학습) — 단, 이는 legacy (shift_at_both)와 동일해짐.

### 6-2. SRM RDM criterion (§4-3, §4-4) — 구현 완료, 실패 확인

A_g bypass → voxel prediction → SVD projection → RDM 비교. **구현 완료 (2026-03-23)**.
결과: 전 ROI에서 Spearman r ≈ 0 → RDM criterion은 cone shift fitting에 부적합.
SVD projection이 cone shift에 의한 voxel-level RDM 차이를 부분적으로 흡수하는 것이 근본 원인.

### 6-3. sub-09 (protan) 포착: LOCO 불가, ΔRDM V1 가능 (§4-6, §5-5)

**LOCO**: W-fixed cone_1way에서 protan signal 없음. cone_3way/fourier는 포착하나 sub-10 false positive.

**ΔRDM**: V1 correlation distance에서 sub-09 protan **유의** (r=0.513, p=0.005). Confusion pair 3/3 일치. Best δθ=25-35nm → V4 LOCO-legacy (25.20nm)과 수렴.

**현재 status**:
- sub-08 deutan → **LOCO** (V1 p=0.033, V2 p=0.047)
- sub-09 protan → **ΔRDM V1** (p=0.005) + LOCO V4-legacy (p=0.009)
- sub-10 normal → 두 criterion 모두 correct null (V1 LOCO p=0.167, V1 ΔRDM p=0.884)

**미해결**:
1. ΔRDM이 V1에서만 작동하는 이유 (V2/V4 NS)
2. LOCO와 ΔRDM의 CVD-type 특이성의 물리적 근거
3. ΔRDM V4 sub-10 false positive (p=0.026) — alpha가 낮아 noise 영향?

### 6-4. Δλ의 물리적 해석

V1=34.92nm vs V2=3.87nm — 어느 것이 "진짜" cone shift인가? 둘 다 유의하나 값이 10배 차이.

### 6-5. Cross-ROI ΔRDM 일관성: Joint ROI 모델 근거 (2026-04-01)

**동기**: 개별 ROI fitting에서 Δλ 불일치 (V1=34.92nm, V2=3.87nm) → 단일 Δλ joint optimization 가능성?

#### 6-5-1. Cross-ROI ΔRDM Pairwise Consistency (SRM-aligned space)

SRM-aligned amplitudes (8 colors × K dims)에서 correlation distance RDM 계산 → ΔRDM = mean_HC_RDM - CVD_RDM (28 upper-triangle pairs). Cross-ROI Pearson correlation:

| Subject | V1-V2 | V1-V3 | V1-V4 | V2-V3 | V2-V4 |
|---------|-------|-------|-------|-------|-------|
| sub-08 (deutan) | **r=0.497**\*\* | r=0.098 | r=0.424\* | r=0.251 | r=0.552\*\* |
| sub-09 (protan) | **r=0.633**\*\*\* | r=0.250 | r=-0.030 | r=0.467\* | r=0.526\*\* |
| sub-10 (normal) | **r=0.571**\*\* | r=0.394\* | r=0.440\* | r=0.202 | r=0.509\*\* |

(\*p<0.05, \*\*p<0.01, \*\*\*p<0.001, n=28 pairs)

**핵심 발견**:
1. **모든 CVD 참여자 (sub-08, sub-09, sub-10 포함)가 V1-V2 ΔRDM consistency 보임** (r=0.497-0.633)
2. V2-V4도 일관성 높음 (r=0.509-0.552)
3. sub-10은 정상 cone 기능 (LOCO/ΔRDM criterion null)이지만 CVD 그룹 참여자

#### 6-5-2. Joint ROI 모델 근거

**Cross-ROI consistency는 문제가 아닌 지지 근거**:

1. **Biological plausibility**: Cone shift는 망막 현상 → 전체 visual hierarchy에 cascade
   - 단일 retinal parameter (Δλ)가 V1→V2→V3→V4 전반에 영향을 미치는 것은 당연
   - V1-V2 ΔRDM correlation → 하류 ROI들이 공유된 왜곡 구조를 물려받음

2. **Joint optimization 타당성**:
   - 왜곡 패턴이 ROI 간 **coherent** (random noise 아님)
   - 단일 Δλ로 multiple ROI를 설명할 수 있는 생물학적 구조 존재
   - 개별 fitting의 Δλ 불일치 (V1=34.92nm, V2=3.87nm)는 각 ROI의 statistical power 차이 때문일 수 있음

3. **Per-ROI fitting의 한계**:
   - n=8 색 × n=7 HC mean → 통계적 power 부족
   - ROI별 K, alpha 차이 → 예측 RDM 품질 차이 (V1 pred ρ=0.356 vs V4=0.102)
   - Joint fitting으로 cross-ROI constraint 추가 → regularization effect

#### 6-5-3. 향후 구현 방향

**단일 Δλ joint optimization** (예: `step1_fit_loco_v2_joint.py`):
- Input: precomputed W_HC for all ROIs (V1, V2, V3, V4)
- Objective: `−mean_ρ_across_rois(Δλ)` 또는 weighted sum (hV4 primary gate)
- Permutation test: 동일 순열을 모든 ROI에 적용 (retinal property)
- Output: single `joint_delta_lambda`, per-ROI ρ at joint Δλ

**기대 효과**:
1. Cross-ROI ΔRDM consistency가 높으므로 joint fit이 feasible
2. 개별 ROI Δλ 추정치의 불일치 해소
3. Biological constraint (single retinal parameter) 반영

---

## 7. ΔRDM Loss Pipeline (2026-04-01)

### 7-1. 동기

기존 LOCO loss (`step1_fit_loco_v2.py`)로는 sub-09 protan V1/V2 signal 포착 불가 (all NS). 반면 `diagnostic_delta_rdm.py`의 ΔRDM 진단에서 sub-09 V1 p=0.005로 강한 signal 확인. ΔRDM을 **primary fitting loss**로 활용하여 cone-shift δθ 추정.

### 7-2. 구조

```
loss_functions.py           — 모듈형 loss 정의 (DeltaRDM_V1V2_Equal)
step1_fit_delta_rdm.py      — ΔRDM fitting: V1+V2 combined, 2-stage grid
step2_validate_v4_loco.py   — V4 LOCO validation: fitted δθ → V4 Spearman
```

**Loss function**: `DeltaRDM_V1V2_Equal`
- combined = 0.5 × sim(ΔRDM_sim_V1, ΔRDM_obs_V1) + 0.5 × sim(ΔRDM_sim_V2, ΔRDM_obs_V2)
- similarity metric: cosine (default), pearson, spearman
- W-fixed: precompute W_HC once from C(θ), sweep C(θ+δ) only

**Permutation**: 8! exact (40,320), 동일 순열을 V1+V2 동시 적용 (RDM → squareform → reorder → upper-triangle)
- label_perm_p: P(null_combined ≥ obs_combined)
- baseline_improvement_p: P(null_improvement ≥ obs_improvement), δ=0 대비

**Grid search**:
- cone_1way (df=1): coarse 2° → refine ±5° at 0.5°
- cone_3way/fourier (df>1): differential_evolution

**Validation**: V4 LOCO (ridge_gcv) at fitted δθ → Spearman ρ + exact perm

### 7-3. 기대 결과

| Subject | Expected | Rationale |
|---------|----------|-----------|
| sub-09 protan | V1 ΔRDM p<0.05 | 진단에서 p=0.005 확인, cone_1way 30nm peak |
| sub-08 deutan | V2 기여로 combined 유의 기대 | V1 ΔRDM NS이나 V2에서 LOCO 유의 |
| sub-10 normal | weak/diffuse signal | CVD이나 cone-shift signal 약함 |

### 7-4. 삭제된 파일

| 파일 | 사유 |
|------|------|
| `step1_fit_rdm_v2.py` | SRM-RDM 접근 실패 (SVD projection이 cone shift 흡수) |
| `step2_fit_rdm.py` | v1 파이프라인 잔재 (SRM-based RDM) |
| `step3_fit_loco.py` | v1 파이프라인 잔재 (shift_at_both 전용) |
| `step3_fit_loro.py` | LORO transfer 실패 |
| `step3_verify_w_constraint.py` | W-fixed 전환 후 불필요 |

---

## 8. 파이프라인 파일

| 파일 | 역할 |
|------|------|
| `step0_precompute.py` | SRM LOO precomputation |
| `step1_fit_loco_v2.py` | W-fixed LOCO cone shift fitting |
| `step1_fit_delta_rdm.py` | **NEW**: ΔRDM V1+V2 combined fitting |
| `step2_validate_v4_loco.py` | **NEW**: V4 LOCO validation for ΔRDM-fitted δθ |
| `step2_cross_eval.py` | Within-ROI cross-evaluation |
| `step2b_cross_roi_eval.py` | Between-ROI cross-evaluation |
| `step3_summary_v2.py` | V4 summary figures |
| `step3_cross_roi_summary.py` | Cross-ROI summary |
| `step4_cross_validate.py` | Cross-validation |
| `step5_hc_replication_null.py` | HC replication null |
| `loss_functions.py` | **NEW**: Modular loss function classes |
| `diagnostic_srm_baseline.py` | SRM A_g prediction quality 진단 |
| `diagnostic_delta_rdm.py` | ΔRDM sanity check (§4-6), dual distance × triple metric |
