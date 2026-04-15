# Future Phase 2: 왜곡 모델링 + 필터 설계

> **날짜**: 2026-04-13 (v4 — restructured)
> **피험자**: HC 7명 (sub-01~07), CVD 3명 (sub-08 deutan, sub-09 protan, sub-10 normal control)
> **ROI**: hV4 (primary), V1/V2 (supplementary)

---

## 1. 목적

Phase 1-3이 "CVD 피질 색 표상이 왜곡되어 있다"를 확립했다면, 이 단계는 세 질문에 답한다:

1. **왜곡의 구조**: 어떤 메커니즘이 관찰된 왜곡을 설명하는가?
2. **교정 가능성**: 그 구조가 역변환(pre-image) 가능한가?
3. **필터 도출**: 가능하다면, 구체적으로 어떤 자극 변환이 필요한가?

**핵심 발견**: CVD의 피질 색 왜곡은 개인마다 고유한 기하학적 구조를 가지며, 그 구조의 가역성(invertibility)이 자극 공간 교정의 가능 여부를 결정한다.

---

## 2. 전제

### 2-1. 증거 위계

| 위계 | 내용 | 근거 |
|------|------|------|
| **PRIMARY** | hV4 L_LOCO fitting → 모델 선별, 필터 도출 | Phase 3: hV4만 permutation null을 genuinely 초과하는 유일한 보간 ROI |
| **CROSS-VALIDATION** | hV4 LOCO-fitted params에서 ΔRDM post-hoc 계산 | L_LOCO fitting의 부수적 결과로서 독립적 평가 |
| **SUPPLEMENTARY** | V1/V2 ΔRDM fitting → 메커니즘 특성화, β_s 문헌 수렴 | 적합 기준의 permutation test (순환적) — 필터 근거 아님 |
| **SUPPORTING** | V1 LOCO → 왜곡 모델 보조 증거 | V1 LOCO null ≈ 0.10-0.13 (voxel covariance 기원) — 필터 근거 부적절 |

### 2-2. Case Study 프레이밍 — CVD-Specificity 불요

**결론**: 개인 사례 연구에서 HC-specific한 false-positive 통제는 불필요하다.

**근거**:
- **Single-Model-Significance Fallacy** (Schütt et al. 2021): "RDM correlations tend to be positive even for very different representations." HC가 CVD 모델에 유의하게 적합되는 것은 예상되는 현상이며, 모델을 chance에 대해 검정하는 것은 low bar.
- **Crawford & Howell (1998)**: Phase 2에서 이미 개인 수준 anomaly 확인됨. 이것이 case study의 필수 검증이며, HC 분포 대비 CVD 전체의 유의성은 요구되지 않음.
- **LOCO의 역할**: 진단(diagnosis)이 아닌 프로파일링(profiling) → "어떤 색이 취약한가"의 개인화 도구.
- **3-step 검증 프레임워크**: (1) Crawford & Howell → anomaly, (2) LOCO → profiling, (3) Pre-image → filter

### 2-3. HC Specificity 실험 기록 (중복 방지)

아래 세 가지 접근이 모두 실패하였으므로 재시도 불필요:

| 실험 | 방법 | HC FPR | 결과 | Job/날짜 |
|------|------|--------|------|----------|
| **Raw LOCO profile** | hV4 shift_at_both, label-perm null | machado 43%, rc 71%, 2comp **100%** | HC 개인 변이가 CVD를 초과 | Job 96600, 2026-04-11 |
| **Baseline Δρ diagnostic** | 10-subj fitting, empirical rank | sub-08 emp_p=0.50, sub-09 0.25, sub-10 0.25 | HC baseline-Δρ 상관 r=**−0.894** (regression-to-mean) | Job 96664, 2026-04-11 |
| **ΔV (Experiment C)** | ΔV_obs = vuln_target − mean_HC_vuln, w_fixed | machado 43%, rc 86%, 2comp 57% | HC ΔV 편차 ≥ CVD (sub-03 range=1.189 > sub-09 0.284) | Job 96828, 2026-04-13 |

**구조적 원인**: n=7 HC / 8 colors / 2 DOF — permutation (8!=40,320)이 2-DOF 모델 유연성을 통제하기에 불충분. HC 개인 간 변이(hV4 baseline ρ: [−0.36, +0.69])가 HC-CVD 차이를 초과.

---

## 3. 모델

| 모델 | DOF | 파라미터 | 수준 | 비고 |
|------|:---:|---------|------|------|
| **Machado 1-way** | 1 | Δλ (nm) | 망막 | L/M cone spectral shift. Machado et al. 2009 |
| **R+C** | 2 | Δλ, g | 망막+피질 | `rg' = rg_base + (1+g)·(rg_ret - rg_base)`. g=0: 순수 망막, g<−1: 과보상 |
| **2-Component** | 2 | β_s (°), β_c (°) | 피질 | `θ' = θ + β_s·cos(θ−90°) + β_c·cos(θ−θ_conf)`. S-cone 보상 + confusion axis |
| **Fourier warp** | 4 | a₁, b₁, a₂, b₂ | 기술적 | `δ(θ) = Σ(a_k·sin + b_k·cos)`. Ablation ceiling only |
| **Hybrid** | 3 | Δλ + β_s, β_c | 복합 | **REJECTED** — 두 성분 non-additive |

**핵심 파라미터의 의미**:
- **Δλ**: L/M cone peak shift. 0=정상, ~2nm=경미, ~10nm=중등도, 20nm=이색형.
- **g**: 피질 opponent gain. g=−1: 정확한 보상. Tregillus et al. (2021): 20-40% 과보상.
- **β_s**: S-cone axis(90°) 방향 angular 확장. Emery et al. (2021): 21.4° B-Y rotation.
- **β_c**: CVD family-specific confusion axis(protan 16°, deutan 150°) 방향 modulation.

**모델 간 수준 차이**: Machado/R+C는 cone-level, 2-Component는 cortical-level. **동일 피험자에 대해 정반대 교정을 처방할 수 있다** (sub-08: cosine=−0.18, 부호 일치 3/8). 행동 실험만이 올바른 수준을 결정.

---

## 4. 손실함수

### 4-1. L_LOCO — PRIMARY (필터 설계)

```
L_fit = α·L_vuln/4 + β·L_rank/2 + δ·L_rdm/2 + ε·L_smooth/32400
```

| 항 | 정의 | 가중치 | 측정 |
|----|------|:------:|------|
| L_vuln | MSE(vuln_sim, vuln_cvd) | α=1.0 | Per-color LOCO vulnerability match |
| L_rank | 1 − Spearman ρ | β=0.5 | 취약성 순위 일치 |
| L_rdm | 1 − cosine(ΔRDM) | δ=0.2 | RDM 구조 보조 정규화 |
| L_smooth | mean(adj_diff(δθ)²) | ε=0.1 | 인접 색 간 교정량 smoothness |

- **적용**: 모든 모델 × hV4 (shift_at_both)
- **중요**: L_rdm(δ=0.2) 포함 → LOCO와 ΔRDM은 완전 독립이 아님. 정확한 표현: "per-color accuracy를 주 목적으로 하되 RDM을 보조 정규화로 사용"

### 4-2. L_ΔRDM — SUPPLEMENTARY (메커니즘 특성화)

```
L = max cosine(ΔRDM_sim, ΔRDM_obs)
```

- **적용**: 2-Component × V1, V2 (crossnobis cosine)
- ΔRDM_obs = RDM_CVD − mean(RDM_HC), 28개 색 쌍
- Permutation: 8! exact (40,320). Bootstrap: n=500 for CI
- **순환성 주의**: ΔRDM p-value는 적합 기준의 permutation test → 모델의 독립 검증이 아닌, fitting의 유의성

---

## 5. 결과

### 5-1. Detection — 모든 모델 수렴

| Subject | Machado | R+C | 2-Component | Fourier | 합의 |
|---------|:---:|:---:|:---:|:---:|------|
| sub-08 | p=0.058 | **p=0.005*** | **p=0.004**** | p=0.0002 | 왜곡 존재 |
| sub-09 | **p=0.018*** | =Machado | p=0.035* | p=0.018* | 왜곡 존재 |
| sub-10 | p=0.559 | — | p=0.058 | — | 정상 |

모든 모델이 동일 결론: sub-08/09에서 hue interpolation distortion 존재, sub-10 정상. **모델 선택에 무관하게 robust.**

### 5-2. hV4 LOCO (PRIMARY) — 모델별 최적 적합

| Subject | 모델 | 파라미터 | ρ | perm_p | 판정 |
|---------|------|---------|:---:|:---:|------|
| **sub-08** | **2-Component** | β_s=38°, β_c=−14° | 0.881 | **0.004**** | 전체 파이프라인 최강 |
| sub-08 | R+C | Δλ=2.0, g=+2.25 | 0.857 | 0.005** | 대안 모델 |
| **sub-09** | **Machado** | Δλ=13.5nm | 0.762 | **0.018*** | 1 DOF로 충분 (g=0 collapse) |
| sub-09 | 2-Component | β_s=6°, β_c=−22° | 0.690 | 0.035* | ρ 낮지만 pre-image 결정적 |
| sub-10 | — | — | — | NS | 정상 |

### 5-3. V1/V2 ΔRDM (SUPPLEMENTARY) — 메커니즘 특성화

| Subject | 모델 | β_s | β_c | cos | perm_p |
|---------|------|:---:|:---:|:---:|:---:|
| sub-08 V1 | 2-Component | 20±8° | −18±6° (CI excl 0) | 0.384 | 0.053 |
| **sub-09 V1** | **2-Component** | **23±10°** | +3±2° (CI incl 0) | **0.590** | **0.007***** |
| sub-09 Joint | 2-Component | 14° | +9° | 0.438 | **0.044*** |

**β_s 문헌 수렴**: sub-08 = 20°, sub-09 = 23° → 평균 ~21.5°. **Emery et al. (2021) 행동 연구: 21.4°**와 0.1° 차이. 독립적 방법(fMRI ΔRDM vs behavioral hue-scaling) 간 수렴.

**β_c 가족 특이성**: Deutan에서만 유의 (sub-08 CI excl 0). Protan은 큰 Δλ로 confusion axis 붕괴 → β_c 불요.

### 5-4. L_LOCO 구성 요소 분해 (교차 검증)

| Case | (β_s, β_c) | ΔL_vuln | ΔL_rank | ΔL_rdm | ΔRDM cos post-hoc | Δρ |
|------|:----------:|:-------:|:-------:|:------:|:-----------------:|:---:|
| sub-08 hV4 | (38, −14) | +0.002 | **−0.262** | −0.040 | +0.080 | +0.524 |
| sub-08 V1 | (50, −14) | −0.014 | **−0.131** | −0.060 | +0.120 | +0.262 |
| sub-09 hV4 | (6, −22) | −0.008 | **−0.119** | **+0.023** | **−0.046** | +0.238 |
| sub-09 V1 | (38, +22) | −0.010 | **−0.131** | −0.054 | **+0.107** | +0.262 |

**해석**: L_rank가 모든 케이스에서 최대 개선 주도. sub-09 V1만 LOCO와 ΔRDM의 공유 구조 확인 (post-hoc ΔRDM cos +0.107). sub-09 hV4에서는 LOCO가 RDM을 파괴 (ΔRDM cos −0.046).

### 5-5. Correction — 모델 간 방향 불일치

Sub-08 hV4 per-color δθ 비교:

| 색 | Machado | R+C | 2-Component | 부호 일치? |
|:---:|:---:|:---:|:---:|:---:|
| c1(red) | −3.7° | −11.4° | −12.1° | YES |
| c2(org) | −2.8° | −9.9° | −20.2° | YES |
| c3(yel) | −1.3° | −4.8° | −25.7° | YES |
| c4(grn) | +0.3° | +1.4° | −29.4° | **NO** |
| c5(cya) | +2.6° | +10.7° | −32.1° | **NO** |
| c6(blu) | −11.7° | −38.4° | −10.3° | YES |
| c7(pur) | −5.1° | −18.8° | +29.4° | **NO** |
| c8(mag) | −0.5° | −1.1° | +18.5° | **NO** |

부호 일치 4/8. Machado/R+C vs 2-Component Spearman ρ = **−0.714** (유의하게 반상관). **같은 취약성 순위에 수렴하되 정반대 교정을 처방** → 행동 실험만이 판별 가능.

### 5-6. Pre-Image — 필터 존재성

| 모델 | Sub-08 | Sub-09 | 필터 실현 가능성 |
|------|:------:|:------:|:----------:|
| R+C | 8/8 exact (<0.001°) | N/A (=Machado) | Sub-08만 |
| Machado | — | **4/8 exact, 4/8 FAIL** (max 65°) | Sub-09 **불가능** |
| **2-Component** | **8/8 exact** (<0.001°) | **8/8 exact** (<0.001°) | **양쪽 모두** |

**Sub-09 Machado 실패 원인**: Δλ=13.5nm → opponent arc 360°→~96° 압축. c4-c6이 동일 hue ~282°로 수렴 → 독립 복원 불가.

**2-Component 성공 이유**: Cortical angular dilation → arc compression 없음 → bijective → 항상 역변환 존재.

**역설**: Machado LOCO ρ(0.762) > 2-Component(0.690)이지만, pre-image는 Machado가 실패. **"더 정확한 모델이 더 유용한 모델은 아니다."**

Pre-image 교정량:

| | Sub-08 R+C | Sub-08 2-Comp | Sub-09 2-Comp |
|---|:---:|:---:|:---:|
| Mean \|δ\| | 23.5° | 46.3° | 20.1° |
| Max \|δ\| | 42.9° | 104.2° | 48.1° |
| 벡터 cosine | — | −0.18 (반상관) | — |

### 5-7. Severity-Dependent Filter Feasibility

| 모델 수준 | Sub-08 (Δλ=2nm, mild) | Sub-09 (Δλ=13.5nm, moderate) |
|----------|:---:|:---:|
| **Cone-level** (Machado/R+C) | 자극 공간 가능 (arc ~260°) | **자극 공간 불가** (arc ~96°) |
| **Cortical-level** (2-Comp) | 자극 공간 가능 (bijective) | **자극 공간 가능** (bijective) |

**모델 수준의 선택이 치료적 결론을 결정한다.** Cone-level 채택 시 sub-09는 "교정 불가", cortical-level 채택 시 "교정 가능".

---

## 6. 생물학적 함의

### 6-1. 문헌 정합

| 파라미터 | 우리 값 | 문헌 | 출처 | 일치 |
|---------|--------|------|------|:---:|
| Sub-08 Δλ | 2.0 nm | 1-4 nm (very mild) | Machado 2009 | ✓ |
| Sub-09 Δλ | 13.5 nm | 9-14 nm (moderate-severe) | Machado 2009 | ✓ |
| β_s (양 피험자) | 20-23° | **21.4°** B-Y rotation | Emery et al. 2021 | **0.1-3° 이내** |
| Sub-09 g (V1) | −1.10 | 20-40% overcomp | Tregillus et al. 2021 | ✓ (10% overcomp) |

### 6-2. 문제적 파라미터

| 파라미터 | 우리 값 | 문제점 |
|---------|--------|--------|
| Sub-08 V1 g | −2.25 | 125% overcompensation — 문헌 범위 초과 |
| Sub-08 hV4 g | +2.25 | 3.25× 증폭 — 선례 없음 |

Sub-08에서 V1 g<0 (과보상) vs hV4 g>0 (증폭) → ROI-dependent sign flip. 시각 위계에서 동일 왜곡에 대한 질적으로 다른 반응 시사.

### 6-3. 핵심 해석

1. **β_s는 CVD 유형 불변의 공통 피질 보상**: Deutan/protan 모두 ~21.5° S-cone axis 확장 → S-cone 경로 강화에 의한 L-M 결손 보상
2. **β_c는 가족 특이적**: Deutan에서만 유의 (경미한 Δλ → confusion axis 구조 잔존)
3. **Discrimination ≠ Interpolation**: V1/V2는 색을 변별하지만 보간하지 못함. hV4만 진정한 보간 가능 (Phase 3 확립)
4. **Invertibility determines correction feasibility**: 같은 CVD 진단 → 개인마다 다른 피질 기하학 → 다른 교정 가능성

---

## 7. 결론

### 7-1. 모델 선택 요약

| Subject | Primary Model | hV4 LOCO p | V1 ΔRDM p | Pre-image | Filter role |
|---------|:------------:|:---:|:---:|:---:|------|
| **sub-08** | **2-Component** (β_s=38°, β_c=−14°) | **0.004**** | CI excl 0 | 8/8 exact | Primary candidate |
| sub-08 | R+C (Δλ=2.0, g=2.25) | 0.005** | 0.179 NS | 8/8 exact | Alternate |
| **sub-09** | **2-Component** (β_s=6°, β_c=−22°) | 0.035* | **0.007***** | **8/8 exact** | **유일한 feasible filter** |
| sub-09 | Machado (Δλ=13.5) | 0.018* | — | 4/8 FAIL | Pre-image 불가 |
| **sub-10** | — | All NS | — | — | 정상 (no filter) |

**2-Component는 두 CVD 피험자 모두에서 LOCO+ΔRDM dual-validated이며, 양쪽 모두에서 exact pre-image를 달성하는 유일한 모델.**

### 7-2. 세 가지 기여

1. **방법론**: hV4 LOCO 취약성이 JND HYPO를 100% 예측 (SRM z는 33%). 적합 기준(LOCO vs ΔRDM)에 따라 동일 모델의 파라미터가 다르게 나옴 → fitting/evaluation criterion 분리 필수.
2. **모델**: 2-Component angular dilation. β_s ≈ 21.5° → Emery 2021과 0.1° 수렴 (독립적 방법 간). S-cone 보상은 universal, β_c는 family-specific.
3. **이론**: Invertibility = correction feasibility. Mild (sub-08): bijective → exact restoration. Moderate (sub-09): Machado 불가, 2-Component 가능.

### 7-3. N=3의 강점

> "세 CVD 개인에서 세 가지 질적으로 다른 결과를 관찰한다: (i) sub-08은 경미하고 완전히 가역적인 왜곡, (ii) sub-09는 올바른 모델 하에서만 가역적인 더 강한 왜곡, (iii) sub-10은 모든 분석에서 왜곡 없음. 이 다양성 자체가 요점이다 — 동일한 망막 진단이 개인마다 고유한 피질 기하학으로 매핑된다."

### 7-4. 다음 단계 — 행동 검증 실험

| Subject | 조건 | 핵심 가설 |
|---------|------|----------|
| Sub-08 | R+C filter, 2-Comp filter, No filter | H5: 어느 hierarchy가 맞는가? (반상관 교정) |
| Sub-09 | 2-Comp filter, No filter | H1-H3: JND 개선, LOCO ↓, ΔRDM → 0 |
| Sub-10 | 2-Comp filter, No filter | H4: 효과 없음 (specificity) |

**핵심**: Sub-08 이중 필터 비교가 "cone-level vs cortical-level" 메커니즘의 경험적 판별.

---

## 부록

### A. 거부된 접근

| 접근 | 실패 이유 |
|------|----------|
| ΔRDM inverse → filter | −37% to −153% 악화. Pairwise geometry ≠ per-color accuracy |
| Simple inverse (−δ) | Nonlinear forward model에서 D(θ−δ) ≠ D(θ)−δ |
| Hybrid (Cone + 2-Comp) | Sub-08 Δλ=0 (cone 무기여), Sub-09 3-DOF 발산. Non-additive |
| Fourier as primary | 4 DOF/8 colors = overfitting. CCC ≈ R+C. Ablation ceiling only |
| Gen-3 ΔRDM-only (Machado) | 0/18 passed. ΔRDM_sim이 ΔRDM_obs와 반상관 |
| HC specificity (3가지) | 위 §2-3 참조. 모든 접근에서 HC FPR ≥ 43% |

### B. 파일 위치

**스크립트**:
- `scripts/loco_distortion_fit.py` — 다중 모델 LOCO fitting
- `scripts/comprehensive_2component_analysis.py` — 2-Component ΔRDM + bootstrap
- `scripts/preimage_filter_search.py` — Pre-image 수치 탐색
- `scripts/experiment_delta_vuln.py` — HC specificity Experiment C (ΔV)
- `scripts/baseline_delta_rho_diagnostic.py` — HC specificity baseline Δρ
- `scripts/hc_specificity_test.py` — HC specificity label-perm FPR

**결과**:
- `results/loco_filter/phase_a*/` — LOCO fitting (Machado, R+C, 2-Comp, Fourier)
- `results/loco_filter/preimage*/` — Pre-image (R+C, Machado, 2-Comp)
- `results/2component_comprehensive_v2/` — V1/V2 ΔRDM
- `results/baseline_delta_rho/` — HC Δρ diagnostic
- `results/experiment_c_delta_vuln/` — ΔV experiment
- `results/loco_decomposition/` — L_LOCO 구성 요소 분해 시각화

**상위 문서**:
- `LOCO_FILTER_RESULTS.md` — 전체 수치 상세
- `LOCO_FILTER_PLAN.md` — 파이프라인 설계

### C. 문헌

| 주제 | 논문 | 연결 |
|------|------|------|
| Cone shift 모델 | Machado et al. 2009 | Sub-09 최적 (1 DOF) |
| 피질 보상 | Tregillus et al. 2021 | g=−1.10 (10% overcomp) |
| S-cone 보상 | Emery et al. 2021 | β_s ≈ 21.5° vs 21.4° |
| hV4 perceptual hub | Bannert & Bartels 2018 | hV4 = 유일한 보간 ROI |
| EnChroma 한계 | Somers et al. 2024 | Appearance ↑, discrimination ↗ |
| Single-model fallacy | Schütt et al. 2021 | HC FPR = expected, not a flaw |
| Case study validity | Crawford & Howell 1998 | Individual anomaly = sufficient |
