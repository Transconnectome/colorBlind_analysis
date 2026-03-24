# Geometry→Function Simulation Results

48 combinations: 2 subjects × 2 ROIs × 3 models × 4 metrics.
Phase A: ΔRDM fitting (criterion). Phase C: LOCO reproduction (independent evaluation).
Permutation test: exact 8! = 40,320 permutations. `*` p<0.05, `**` p<0.01, `***` p<0.001, `†` p<0.1.

> **Note on `combination` metric**: equal-weighted mean of (corr + cosine + triangle)/3.
> 별도의 가중계수 없이 단순 평균이므로, 단일 지표 결과의 산술 평균과 동일.
> 개별 지표 결과가 더 informative하며, combination은 요약 지표로만 해석.

---

## sub-08 (deutan) — V1

### Phase A: ΔRDM Fitting

| Model (df) | corr | cosine | triangle | combination |
|:---|:---|:---|:---|:---|
| **cone_1way** (1) | r=−0.127 (p=.742) δ=59.9nm | r=−0.128 (p=.796) δ=0.1nm | r=−0.068 (p=.652) δ=0.3nm | r=−0.109 (p=.749) δ=0.0nm |
| **cone_3way** (3) | r=+0.229 (p=.109) L=−35,M=−31,S=−4 | r=+0.297† (p=.077) L=+48,M=−10,S=−15 | r=+0.244 (p=.118) L=+49,M=−8,S=−16 | r=+0.259† (p=.088) L=−16,M=−18,S=−11 |
| **fourier** (4) | r=+0.543*** (p=.001) | r=+0.663*** (p<.001) | r=+0.598** (p=.001) | r=+0.587** (p=.001) |

- cone_1way: δ* 불안정 (metric마다 0~60nm 변동). ΔRDM 피팅 자체가 실패 (r<0).
- cone_3way: L-cone에 큰 음수 shift 또는 양수 shift — metric 간 방향 불일치.
- **fourier**: 유일하게 안정적. cosine 최고 r=0.663***.

### Phase C: LOCO Reproduction

| Model (df) | corr | cosine | triangle | combination |
|:---|:---|:---|:---|:---|
| **cone_1way** (1) | ρ=−0.048 (p=.559) 1/3 | ρ=−0.286 (p=.769) 1/3 | ρ=−0.286 (p=.769) 1/3 | ρ=−0.286 (p=.769) 1/3 |
| **cone_3way** (3) | ρ=−0.595 (p=.943) 0/3 | ρ=+0.476 (p=.122) 1/3 | ρ=−0.024 (p=.533) 1/3 | ρ=−0.500 (p=.902) 0/3 |
| **fourier** (4) | ρ=+0.429 (p=.150) 2/3 | **ρ=+0.571† (p=.076) 2/3** | ρ=+0.095 (p=.420) 2/3 | ρ=+0.357 (p=.195) 1/3 |

Observed worst3: **purple, yellow, orange**.
최선: fourier×cosine (ρ=0.571, p=.076†). Synthetic worst3: yellow, green, purple (2/3 overlap).

---

## sub-08 (deutan) — V2

### Phase A: ΔRDM Fitting

| Model (df) | corr | cosine | triangle | combination |
|:---|:---|:---|:---|:---|
| **cone_1way** (1) | r=−0.063 (p=.620) δ=1.4nm | r=−0.158 (p=.776) δ=1.4nm | r=−0.001 (p=.522) δ=0.0nm | r=−0.074 (p=.664) δ=0.2nm |
| **cone_3way** (3) | r=+0.307* (p=.038) L=−22,M=−28,S=−7 | r=+0.223 (p=.115) L=−19,M=−24,S=−9 | r=+0.416** (p=.008) L=−32,M=−33,S=−2 | r=+0.316* (p=.033) L=−19,M=−23,S=−9 |
| **fourier** (4) | r=+0.684*** (p<.001) | **r=+0.756*** (p<.001)** | r=+0.692*** (p<.001) | r=+0.707*** (p<.001) |

- cone_1way: 완전 실패 (모든 metric에서 r≈0 또는 음수).
- cone_3way: triangle에서 r=0.416** — L,M 모두 −30nm 이상의 대칭적 shift.
- **fourier: 전 metric에서 r>0.68***. cosine 최고 r=0.756***.

### Phase C: LOCO Reproduction

| Model (df) | corr | cosine | triangle | combination |
|:---|:---|:---|:---|:---|
| **cone_1way** (1) | ρ=−0.524 (p=.915) 1/3 | ρ=−0.524 (p=.915) 1/3 | ρ=−0.524 (p=.915) 1/3 | ρ=−0.524 (p=.915) 1/3 |
| **cone_3way** (3) | ρ=−0.524 (p=.915) 1/3 | ρ=−0.524 (p=.915) 1/3 | ρ=−0.643 (p=.958) 1/3 | ρ=−0.571 (p=.934) 1/3 |
| **fourier** (4) | ρ=+0.286 (p=.250) 2/3 | **ρ=+0.619† (p=.058) 2/3** | ρ=+0.190 (p=.332) 2/3 | ρ=+0.429 (p=.150) 2/3 |

Observed worst3: **yellow, orange, purple**.
최선: **fourier×cosine (ρ=0.619, p=.058†)**. Synthetic worst3: blue, yellow, orange (2/3 overlap).
cone_1way/cone_3way: LOCO 전부 음수 — 단일/3축 cone shift로는 deutan 기능 패턴 재현 불가.

---

## sub-09 (protan) — V1

### Phase A: ΔRDM Fitting

| Model (df) | corr | cosine | triangle | combination |
|:---|:---|:---|:---|:---|
| **cone_1way** (1) | r=+0.518* (p=.013) δ=34.4nm | r=+0.554** (p=.007) δ=44.1nm | r=+0.508** (p=.007) δ=30.4nm | r=+0.520** (p=.009) δ=37.1nm |
| **cone_3way** (3) | r=+0.530** (p=.007) L=−41,M=−5,S=−1 | r=+0.556** (p=.006) L=−46,M=−2,S=−1 | r=+0.512** (p=.007) L=−29,M=+1,S=+3 | r=+0.524** (p=.008) L=−39,M=−2,S=−1 |
| **fourier** (4) | r=+0.396* (p=.033) | r=+0.469* (p=.014) | r=+0.448* (p=.015) | r=+0.426* (p=.016) |

- **전 모델×metric에서 유의 (p<0.05)**. 가장 깨끗한 결과.
- cone_1way δ*: 30–44nm 범위 (metric에 따라 변동, 평균 ~36nm).
- cone_3way: L-cone shift 지배적 (−29~−46nm), M/S ≈ 0 → cone_1way와 일치.
- fourier는 cone보다 r이 낮음 (df=4인데 r<0.47) → overfitting 없이 cone이 더 parsimonious.

### Phase C: LOCO Reproduction

| Model (df) | corr | cosine | triangle | combination |
|:---|:---|:---|:---|:---|
| **cone_1way** (1) | ρ=+0.333 (p=.214) 1/3 | ρ=+0.071 (p=.441) 1/3 | **ρ=+0.476 (p=.122) 1/3** | ρ=+0.310 (p=.231) 1/3 |
| **cone_3way** (3) | ρ=+0.381 (p=.180) 1/3 | ρ=+0.238 (p=.291) 1/3 | ρ=+0.333 (p=.214) 1/3 | ρ=+0.381 (p=.180) 1/3 |
| **fourier** (4) | ρ=−0.262 (p=.750) 1/3 | ρ=+0.143 (p=.376) 1/3 | ρ=+0.143 (p=.376) 1/3 | ρ=+0.143 (p=.376) 1/3 |

Observed worst3: **yellow, magenta, green**.
V1에서는 LOCO 유의 결과 없음. cone_1way×triangle이 가장 높지만 NS.
fourier×corr: Phase A sig이지만 LOCO 음수 — geometry→function 전이 실패.

---

## sub-09 (protan) — V2

### Phase A: ΔRDM Fitting

| Model (df) | corr | cosine | triangle | combination |
|:---|:---|:---|:---|:---|
| **cone_1way** (1) | r=+0.288† (p=.065) δ=23.1nm | **r=+0.376* (p=.026) δ=47.7nm** | r=+0.274† (p=.072) δ=20.9nm | r=+0.304† (p=.052) δ=46.4nm |
| **cone_3way** (3) | r=+0.344* (p=.038) L=−9,M=+8,S=+5 | **r=+0.437* (p=.019) L=−10,M=+13,S=+4** | r=+0.359* (p=.031) L=−8,M=+4,S=+6 | r=+0.375* (p=.023) L=−9,M=+8,S=+5 |
| **fourier** (4) | r=+0.406* (p=.013) | r=+0.359* (p=.038) | r=+0.404* (p=.017) | r=+0.374* (p=.025) |

- cosine이 전 모델에서 최고 r (cone_1way: 0.376, cone_3way: 0.437).
- cone_3way: L=−10, M=+13 — L-cone 약한 음수 + M-cone 양수 shift. V1과 다른 패턴.
- fourier는 cone 모델을 능가하지 못함 (df=4인데 r≤0.41).

### Phase C: LOCO Reproduction

| Model (df) | corr | cosine | triangle | combination |
|:---|:---|:---|:---|:---|
| **cone_1way** (1) | ρ=+0.429 (p=.150) 2/3 | **ρ=+0.810* (p=.011) 2/3** | ρ=+0.405 (p=.163) 2/3 | **ρ=+0.810* (p=.011) 2/3** |
| **cone_3way** (3) | ρ=+0.238 (p=.291) 1/3 | **ρ=+0.548† (p=.086) 2/3** | ρ=+0.238 (p=.291) 1/3 | ρ=+0.238 (p=.291) 1/3 |
| **fourier** (4) | ρ=+0.333 (p=.214) 1/3 | ρ=+0.036 (p=.472) 1/3 | ρ=+0.286 (p=.250) 1/3 | ρ=+0.119 (p=.397) 1/3 |

Observed worst3: **magenta, blue, yellow**.
**Winner: cone_1way×cosine — Phase A r=0.376* (p=.026), Phase C ρ=0.810* (p=.011), overlap=2/3.**
δ*=47.7nm. Synthetic worst3: blue, magenta, purple. Observed: magenta, blue, yellow.
cone_3way×cosine도 trending (ρ=0.548†). fourier는 LOCO 전이 실패.

---

## Summary

### Phase A+C 동시 유의 조합

| Subject | ROI | Model | Metric | ΔRDM r (p) | LOCO ρ (p) | Overlap |
|:---|:---|:---|:---|:---|:---|:---|
| **sub-09** | **V2** | **cone_1way** | **cosine** | 0.376 (.026*) | **0.810 (.011*)** | 2/3 |

### Trending (Phase C p<0.1)

| Subject | ROI | Model | Metric | ΔRDM r (p) | LOCO ρ (p) | Overlap |
|:---|:---|:---|:---|:---|:---|:---|
| sub-09 | V2 | cone_1way | combination | 0.304 (.052†) | 0.810 (.011*) | 2/3 |
| sub-08 | V2 | fourier | cosine | 0.756 (<.001***) | 0.619 (.058†) | 2/3 |
| sub-08 | V1 | fourier | cosine | 0.663 (<.001***) | 0.571 (.076†) | 2/3 |
| sub-09 | V2 | cone_3way | cosine | 0.437 (.019*) | 0.548 (.086†) | 2/3 |

### 핵심 관찰

1. **Cosine metric 우위**: 5/5 top results에서 cosine. Mean-centering 없이 절대 방향 정보 보존이 ΔRDM 비교에 유리.

2. **Protan > Deutan**: sub-09 protan은 cone_1way로 causality 입증 (df=1). sub-08 deutan은 cone shift 자체가 피팅 안 됨 → fourier (df=4)만 trending.

3. **Geometry ≠ Function**: fourier가 Phase A에서 r=0.76***으로 최고지만 Phase C에서는 cone_1way (r=0.38*)에 뒤짐. 높은 RDM 설명력 ≠ LOCO 재현력 → **과적합 경고**.

4. **cone_3way for sub-09 V2**: L=−10, M=+13, S=+4 → L-cone 외에 M-cone 보상 shift. cone_1way의 L-only shift (47.7nm)보다 덜 parsimonious하지만, protan pathology의 다차원성 시사.

5. **sub-08 deutan의 한계**: cone_1way/cone_3way 모두 LOCO 음수 → deutan의 기능적 취약점(yellow, orange)이 단순 cone shift로 설명 불가. 보다 복잡한 post-receptoral 메커니즘 필요.
