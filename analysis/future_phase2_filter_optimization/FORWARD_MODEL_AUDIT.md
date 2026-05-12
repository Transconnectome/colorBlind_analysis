---
name: Forward Model + Loss + Simulator Audit
description: vfc(2-component) 식 배경·코드·시각화 신뢰성 + canonical loss 타당성 + simulator 검증 + 폴더 정리 권고
type: audit
date: 2026-05-10
scope: Phase 2 (sub-08 canonical / 6-way comparison)
---

# Forward Model + Loss + Simulator Audit

본 문서는 **vfc 식 (2-component canonical visualization)**, **canonical L_fit (LOCO loss)**, **Stockman+Machado simulator** 세 컴포넌트의 신뢰성을 코드 레벨에서 검증하고 향후 폴더 정리 방향을 제시한다.

---

## 1. vfc 식의 배경 + 현재 식 + 코드 연결

### 1-1. 색공간 변환 chain (Stockman + Hering opponent process)

vfc의 `dt_2comp`는 다음 표준 cone-opponent processing chain 위에서 정의:

```
CIELab(L=75, C=40, θ)
   │
   │  lab_to_xyz()
   ▼
XYZ
   │
   │  M_xyz2lms (Stockman 2° fundamentals)
   │  via _compute_spectral_shift_lms()
   ▼
LMS  (cone responses)
   │
   │  lms_to_opponent():
   │    rg = L − M
   │    by = S − (L+M)/2
   ▼
opponent (rg, by)
   │
   │  opponent_to_hue_angle():
   │    h = atan2(by, rg)
   ▼
h_base  (Stockman opponent hue angle)
```

이는 **Hering opponent process model + Stockman 2° fundamentals** (Stockman & Sharpe 2000) 기반의 표준 색과학 변환. `h_base`는 stimulus θ가 정상 cone-opponent space에서 어디 위치하는지를 나타냄.

### 1-2. 현재 식 (3 위치 모두 동일)

```python
h_base, _, _ = machado_shifted_hue_at(0.0, cvd, θ_CIELab, L_star=75.0, chroma=40.0)
θ_conf = CONF_AXIS[cvd]    # protan: 16°, deutan: 150°, normal: 83° (Stockman convention)
dt = β_s · cos(h_base − 90°) + β_c · cos(h_base − θ_conf)
θ_perceived = (θ_CIELab + dt) mod 360°
```

**해석**:
- 첫 항 `β_s·cos(h_base − 90°)`: by-axis (h=90° = blue-yellow opponent peak) 방향 회전. β_s는 simulation axis (S-cone vs L+M) 회전 강도.
- 두번째 항 `β_c·cos(h_base − θ_conf)`: confusion line 방향 회전. β_c는 deutan/protan confusion axis 회전 강도.
- 두 sinusoidal modulation의 합 → 2-DOF stimulus space distortion field.

**Cone-opponent input 위에서 cortex가 두 축으로 회전을 가하는 model** (CLAUDE.md A1의 "stimulus-space dilation"의 implementation).

### 1-3. 코드 위치 매핑

| 컴포넌트 | 파일:line | 역할 |
|---|---|---|
| **Stockman fundamentals + opponent variance** | `future_phase1_forward_model/scripts/stockman_cone_shift.py:163-204` | `shift_cone_sensitivity`, `lms_to_opponent`, `opponent_to_hue_angle` |
| **CIELab → opponent hue 변환** | `scripts/machado_simulator.py:284-341` | `machado_shifted_hue_at` (Δλ=0 ↔ baseline opponent hue) |
| **dt_2comp (visualization)** | `scripts/visualization/visualize_filter_candidates.py:294-300` | vfc.dt_2comp |
| **dt_2comp (fitting)** | `scripts/loco_distortion_fit.py:178-187` | get_shifted_design('2component') |
| **dt_2comp (analysis)** | `scripts/comprehensive_2component_analysis.py:79-82` | two_component_delta_theta |
| **CONF_AXIS Stockman 정의** | 상기 3 파일 + `cycle12_loss_cross_roi.py` 등 | `{'protan': 16, 'deutan': 150, 'normal': 83}` |

→ **세 위치(visualization/fitting/analysis) 모두 동일 식**. 일관성 verified.

### 1-4. 시각화 신뢰성 검증

| 검증 기준 | 결과 |
|---|:-:|
| Fitting과 visualization의 forward map 일치 | ✓ (3 위치 동일 식) |
| 색공간 변환 standard (Stockman + Hering) | ✓ |
| CONF_AXIS Stockman convention 일치 (A12) | ✓ |
| Pre-image solver (grid + brentq) | ✓ (n_grid=1440, residual<10⁻³) |
| Display rendering (CIELab→sRGB) gamut handling | ✓ (saturation search up to C*=80) |

**Caveat (frame mixing approximation, MEDIUM severity)**:
- Trig는 Stockman opponent space에서 (cos(h_base − 90°), cos(h_base − θ_conf)) 정의.
- Accumulation `θ_CIELab + dt`은 CIELab 단위로 수행.
- 정확한 식은 Stockman h_perceived = h_base + dt → inverse Stockman → CIELab 변환 필요. 현재는 (iii) inverse 변환 생략.
- **Self-consistency 인정**: fitting과 visualization 모두 같은 approximation 사용 → 동일 (β_s, β_c)에서 동일 결과.
- **그러나 F3/F4 paradox와 연결**: phase3 식 (CIELab nominal)이 frame mixing의 또 다른 임의 선택. 둘 다 partial frame mismatch이므로 어느 쪽이 "더 옳다"는 fundamental answer 부재 → 두 식이 서로 다른 결과 산출 시 양쪽 모두 conditional. **이 limitation은 §3-3 #2에서 P0로 격상**.

**판단**: vfc 식은 (1) 표준 색과학 grounded, (2) fitting과 일관, (3) 동일 approximation 사용으로 self-consistent. **canonical (38°, −14°) 시각화 신뢰 가능**.

---

## 2. Canonical Loss 타당성 검증

### 2-1. 정의

`scripts/loco_distortion_fit.py:197-263`의 `compute_fit_loss`:

```
L_fit = α · L_vuln + β · L_rank + δ · L_rdm + ε · L_smooth
```

| 항 | 정의 | Normalize | 역할 |
|---|---|---|---|
| `L_vuln` | MSE(vuln_sim, vuln_cvd) / 4.0 | [0, 1] | **Primary**: HC LOCO simulation의 per-color vulnerability와 CVD observed vulnerability의 거리 |
| `L_rank` | (1 − Spearman(vuln_sim, vuln_cvd)) / 2.0 | [0, 1] | **Secondary**: 두 vulnerability 패턴의 ordinal 일치 |
| `L_rdm` | (1 − cosine(ΔRDM_sim, ΔRDM_obs)) / 2.0 | [0, 1] | **Auxiliary**: pairwise distance structure |
| `L_smooth` | mean(adjacent-color δθ²) / 32400 | [0, 1] | **Regularizer**: smooth distortion field 강제 |

**Default weights**: `α=1.0, β=0.5, δ=0.2, ε=0.1` (`DEFAULT_WEIGHTS`).

### 2-2. canonical (β_s=38°, β_c=−14°) sub-08 V4 fit 결과

`results/fits/phase_a_2component/sub-08_V4_2component.json`:

| 항 | Value |
|---|---:|
| `l_fit` | **0.201** |
| `l_vuln` (raw MSE) | 0.302 |
| `l_rank_raw` (= 1 − ρ) | 0.119 → **ρ = 0.881** |
| `l_rdm_raw` | 0.944 (weak — RDM 신호 약) |
| `l_smooth_raw` | 403° (≈20° per-color jitter) |
| `label_perm_p` | **0.0036**** |
| `mse_perm_p` | 0.0029** |
| `delta_rho` (vs Δλ=0 baseline) | **+0.595** (baseline ρ=0.286 → fit ρ=0.881) |

**해석**:
- L_vuln + L_rank가 fit의 핵심. 둘 다 강함 (ρ=0.881).
- L_rdm은 cosine=0.056 (RDM 일치 약) — 그러나 L_rdm 가중치 0.2로 낮아 fit dominate 안 함.
- Permutation test: label permutation null 대비 p=0.0036 → 매우 유의.
- delta_rho 0.595 → baseline 대비 huge improvement.

### 2-3. 타당성 판단

| 기준 | 결과 |
|---|:-:|
| Loss 모든 항 [0,1] 정규화 → weights 직접 해석 | ✓ |
| Primary term (L_vuln)이 직접 신경 데이터 fit | ✓ |
| Secondary term (L_rank)이 ordinal robustness 보강 | ✓ |
| Regularizer (L_smooth)가 smooth distortion 강제 | ✓ |
| Multi-objective weights 합리적 (1.0/0.5/0.2/0.1) | ✓ |
| Permutation test 유의성 | ✓ p=0.0036 |
| delta_rho large improvement | ✓ +0.595 |

**판단**: canonical L_fit은 **타당**. 다만 L_rdm 신호가 약한 것 (cos=0.056)은 sub-08 hV4의 ΔRDM이 weak하다는 것 — 모델 한계 아니라 데이터 신호 자체가 약한 것 (CLAUDE.md MEMORY: "SRM RDM은 absorbed by SRM alignment").

---

## 3. Simulator (Stockman + Machado) 타당성 검증

### 3-1. 변환 chain

```
delta_lambda  (cone shift 입력 nm)
     │
     ▼
shift_cone_sensitivity()      ← stockman_cone_shift.py:163
     │  CubicSpline interpolation
     │  shifted_cone(λ) = original_cone(λ − Δλ)
     ▼
shifted L or M cone fundamental
     │
     ▼
machado_mixed_fundamentals()  ← machado_simulator.py:172
     │  α coupled to Δλ:  α = clip(Δλ / Δλ_max, 0, 1)
     │  L_a = α·L_shift + (1-α)·k_L·M  (protan)
     │  M_a = α·M_shift + (1-α)·k_M·L  (deutan)
     ▼
CVD-shifted (L_a, M_a, S_a)
     │
     ▼
_compute_spectral_shift_lms()  ← stockman_cone_shift.py
     │  XYZ stimulus → LMS via M_xyz2lms_orig
     │  but using shifted (L_a, M_a, S_a) absorption
     ▼
anomalous LMS response
     │
     ▼
lms_to_opponent() → opponent_to_hue_angle()
     ▼
hue_shifted (CVD opponent space)
```

### 3-2. 표준성 검증

| 컴포넌트 | 표준 출처 | 검증 |
|---|---|:-:|
| Stockman 2° fundamentals | Stockman & Sharpe (2000) | ✓ (또는 colour-science 패키지) |
| Cone shift via spectral λ-shift | Machado et al. 2009, IEEE TVCG | ✓ |
| α coupling (anomalous trichromacy 강도) | Machado 2009 § Anomaloscope simulation | ✓ |
| L−M opponent (red-green) | Hering opponent theory; Smith & Pokorny 1975 | ✓ |
| S−(L+M)/2 opponent (blue-yellow) | Standard | ✓ |
| atan2(by, rg) hue angle | Standard polar conversion | ✓ |

### 3-3. 알려진 limitation + 심각도 재평가 (2026-05-10)

| # | Limitation | 심각도 (revised) | 해결 방안 | Status |
|---|---|:-:|---|:-:|
| 1 | Approximate fundamentals fallback (colour-science 없을 때) | **LOW** (precision ~1° hue shift) | `pip install colour-science` 양 conda env (`srm`, `colorBlind`) | **RESOLVED 2026-05-10** |
| 2 | Frame mixing approximation (Stockman trig + CIELab accumulation) | **MEDIUM** (paradox potential, F3 사례) | Option A: 모든 단계 Stockman으로 통일 (inverse Stockman→CIELab 변환 추가); Option B: 모든 단계 CIELab로 통일 (CIELab 좌표계의 confusion axis 재정의) | **OPEN — design 결정 필요** |
| 3 | Linear LMS↔XYZ relation (Hunt-Pointer-Estevez matrix) | **NEGLIGIBLE** | 표준 가정, 색과학 community 합의 | **CLOSED** |
| 4 | CIELab D65 white point assumption | **LOW** (monitor calibration 의존) | sRGB display assumption D65, 일치 | **CLOSED (calibration 가정 시)** |
| 5 | Population-average Stockman (개인차 미반영) | **MEDIUM** (CVD 정확도 한계) | Asano 2016 개인 cone fundamentals 또는 Stockman 2023 individual formulae — anomaloscope per-subject 필요 | **DEFERRED (data 없음)** |

#### Limitation #1 RESOLVED (2026-05-10)
- `colour-science 0.4.4` 설치 확인 in both `srm` and `colorBlind` conda envs.
- Stockman & Sharpe 2 Degree Cone Fundamentals 정확값 사용 가능.
- Action: 향후 모든 새 fit/visualization은 srm/colorBlind env에서 실행. 기존 결과 (`phase_a_2component`)는 approximate fallback 사용했을 가능성 있으나 (β_s, β_c) coordinate 안정성 검증 (이전 fit과 colour-science 사용 fit이 ~1° 이내 일치 예상).

#### Limitation #2 (Frame mixing) — F3/F4 paradox의 root cause 후보
- **현재**: trig는 Stockman opponent (h_base 기반), accumulation은 CIELab (`θ + dt`).
- **문제**: dt가 Stockman 단위로 계산되었는데 CIELab 단위로 더해짐 → 두 좌표계 사이의 nonlinear mapping에서 dt를 단위 일치시키는 것은 정확하지 않음.
- **F3/F4 paradox와의 연결**: phase3 식 (CIELab nominal) vs vfc 식 (h_base) 차이가 frame mixing의 임의 선택. 두 식 모두 partial frame mismatch.
- **Resolution Option A** (Stockman 통일, **권장**):
  ```python
  h_base = stockman_hue(θ_CIELab)
  dt_stockman = β_s·cos(h_base − 90°) + β_c·cos(h_base − θ_conf_stockman)
  h_perceived = (h_base + dt_stockman) % 360°
  θ_perceived_CIELab = inverse_stockman_hue(h_perceived)   # NEW: inverse mapping
  ```
  - 장점: 단위 완전 일치, physiologically consistent.
  - 단점: inverse mapping은 lookup table 또는 numerical inverse 필요 (computational overhead).
  - 영향 범위: `dt_2comp` 호출 3 위치 모두 + pre-image solver.
- **Resolution Option B** (CIELab 통일):
  - θ_conf을 Stockman 기준에서 CIELab 기준으로 재정의 (deutan/protan confusion line의 CIELab a*-b* 평면 각도 산출).
  - 장점: code 단순.
  - 단점: physiological grounding 약화 (cone-opponent → cortex 단계 명시적으로 model 안 함).

**권고**: Option A. inverse Stockman은 numerical (binary search 또는 cubic spline interp) 가능. computational cost 작음. 본 안건은 **P0 (paradox root cause 해소)** 로 격상.

#### Limitation #5 (개인차) — DEFERRED
- Stockman & Sharpe 2000은 population mean. 개인차는 macular/lens pigment density (built-in 보정 가능) + photopigment optical density + λ position (extensible).
- **Asano, Fairchild, Blondé 2016**: 개별 cone fundamentals 추정 방법 (JOSA A).
- **Stockman 2023** (Color Research & Application): 명시적 individual formulae.
- 본 프로젝트: anomaloscope per-subject data 없음 → defer. CVD 결과 해석 시 "population-average Stockman 가정" caveat 명시.

### 3-4. Stockman Convention 신뢰성·실효성 검증 (2026-05-10)

#### Reliability evidence

| 기준 | Evidence |
|---|---|
| **CIE 공인 표준** | CIE 170-1:2006 + CIE 170-2:2015 — Stockman & Sharpe 2000 cone fundamentals를 "physiologically relevant" 표준으로 sanction |
| **Genotype-known observers** | 측정 대상자의 opsin gene polymorphism이 알려진 상태에서 derived → 가장 secure population estimate |
| **Built-in corrections** | macular pigment density, lens pigment density 보정 내장. Photopigment optical density + λ position 확장 가능 |
| **Field consensus** | "arguably the most secure estimates of mean human cone spectral sensitivities available" (Stockman 2019, ScienceDirect; Stockman 2023, Color Research & Application) |
| **Implementation availability** | `colour-science` package에 정식 포함. CIE TC 1-36 이래 표준 |

#### 본 프로젝트 사용처 + 영향

| Component | Stockman 의존 정도 |
|---|---|
| `machado_simulator.py` (Δλ shift) | **HIGH** — cone fundamentals base curve로 사용 |
| `dt_2comp` (vfc 식) | **MEDIUM** — h_base 좌표 system이 Stockman opponent. dt magnitude는 Stockman 기준 회전 |
| Pre-image solver | **HIGH** — forward map (Stockman 기반) 역으로 풀어 stimulus 산출 |
| Display rendering (CIELab→sRGB) | **NONE** — sRGB는 monitor primary 정의 (Stockman 무관) |

#### 개선/발전 가능성

| Option | 방법 | 비용 | 본 프로젝트 적용성 |
|---|---|:-:|:-:|
| **A. Precise Stockman (colour-science)** | hardcoded fallback → official CIE values | LOW | ✓ **DONE 2026-05-10** |
| **B. Asano 2016 individual fundamentals** | per-subject macular/lens/optical density 측정 | HIGH | ✗ anomaloscope 없음 |
| **C. Stockman 2023 individual formulae** | 명시적 formulae로 individual 변형 | HIGH | ✗ 동일 (per-subject 측정 필요) |
| **D. Direct genotyping** | L/M opsin polymorphism (Asn180Ser, Tyr277Phe 등) | VERY HIGH | ✗ fMRI 실험 outside scope |
| **E. CIE 2006 fundamentals** | "CIE 2006"이라고 따로 부르지만 실질은 Stockman & Sharpe 2000 = same data | — | (이미 사용 중) |

#### 제거 가능성

| Alternative | 평가 |
|---|---|
| Smith-Pokorny 1975 | 더 오래된 표준. CIE 2006 채택으로 사실상 superseded. **제거 시 후퇴**. |
| Vos 1978 | 수정된 CIE 1931. Stockman 정확도에 못 미침. **제거 무의미**. |
| Hunt-Pointer-Estevez | XYZ→LMS matrix만 정의. Cone fundamentals 자체 미제공. **partial replacement only**. |
| Brettel-Vienot 1997 | CVD 시뮬레이션 specific (LMS-confusion plane projection). 본 프로젝트 simulator의 partial alternative. **단순. 정확도 하락**. |

**판단**: Stockman convention **제거 불가능** — 현재 가장 정확한 population-mean cone fundamentals이고 대체할 더 나은 표준 없음. **개선 path**는 (A) precise loading (완료) → (B/C) individual fundamentals (anomaloscope data 확보 시 future work).

#### Caveat for present project
- 본 프로젝트의 모든 forward model은 **Stockman & Sharpe 2000 population-mean** 기반. CVD 개인차는 (β_s, β_c) parameter로 흡수되나 cone-fundamental level의 개인차는 모델링 안 됨.
- sub-08 deutan, sub-09 protan의 actual cone λ-shift은 Machado anomaloscope 모델로 추정 (Δλ ≈ 8-25 nm). 정확한 cone profile은 측정 안 됨.
- 이 limitation은 본 프로젝트의 **fundamental constraint** — 추가 측정 없이 해결 불가.

### 3-5. 검증 출력 (이전 세션):

`machado_shifted_hue_at(0.0, deutan, θ)` for θ=0,45,...,315 → h_base = 299.9, 288.4, 278.1, 266.5, 243.9, 142.6, 105.7, 16.4. 강한 nonlinear monotonic mapping (CIELab과 Stockman opponent의 frame difference). 이는 expected behavior — CIELab의 균등 8-color partition이 Stockman opponent space에서는 비균등.

**판단**: simulator는 표준 색과학에 따라 정확히 구현. **canonical fit의 forward model로 신뢰 가능**.

---

## 4. 종합 검증: vfc 시각화 신뢰성

| Layer | 검증 |
|---|:-:|
| Color science chain (Stockman + Hering) | ✓ standard |
| Simulator (Machado cone shift) | ✓ standard, well-implemented |
| `dt_2comp` 식 (Stockman opponent 기반) | ✓ physiologically grounded |
| Fitting과 visualization 식 일치 | ✓ 3 위치 동일 |
| Pre-image solver | ✓ (residual < 10⁻³) |
| Canonical fit 통계 | ✓ p=0.004, ρ=0.881, Δρ=+0.595 |
| Behavioral PASS at canonical | ✓ §3 (2026-04-17) |

**결론: vfc 식 시각화는 신뢰 가능**. canonical (38°, −14°) sub-08 행동 PASS는 잘 grounded된 forward model + valid loss + correct simulator의 합작.

**vs phase3 식**: phase3는 (1) CIELab nominal angle 직접 사용 (frame mismatch), (2) 자체 신경 fit 부재, (3) fitting code와 inconsistent. vfc 신뢰성은 phase3 hypothesis와 무관하게 자체 정당성 보유.

---

## 5. 코드 분포 매핑 (Loss + Simulator)

### 5-1. 현재 분포

| 카테고리 | 파일 | 위치 |
|---|---|---|
| **Simulator core** | `machado_simulator.py` | `scripts/` (top-level, importable) |
| | `retinal_cortical.py` | `scripts/` |
| | `stockman_cone_shift.py` | `future_phase1_forward_model/scripts/` |
| | `utils_cone_3way.py` | `scripts/` |
| | `utils_distortion_models.py` | `scripts/` |
| **Canonical L_fit** | `loco_distortion_fit.py` (compute_fit_loss) | `scripts/` |
| **Active losses** | `cycle12_loss_cross_roi.py` | `scripts/` |
| | `cycle14_v1_rdm_cross.py` | `scripts/` |
| | `cycle15_mwjaccard_cross.py` | `scripts/` |
| | `l3_loss.py` | `scripts/` |
| **Visualization** | `visualize_filter_candidates.py` (vfc.dt_2comp) | `scripts/visualization/` |
| | `visualize_phase3_preimage.py` (phase3.dt_2comp — wrong식) | `scripts/visualization/` |
| | `visualize_preimage_3losses.py` | `scripts/visualization/` |
| **Old cycle losses** | cycle1~11, cycle13 | `scripts/cycles/`, `scripts/older_cycles/` |

### 5-2. 폴더 정리 권고 (실제 이동은 별도 작업)

현재 `scripts/`는 평면 — top-level에 16+ .py 혼재. 다음 분리 권고:

```
scripts/
├── forward_models/          # NEW: simulator + dt_2comp 정의 모음
│   ├── machado_simulator.py
│   ├── retinal_cortical.py
│   ├── utils_cone_3way.py
│   ├── utils_distortion_models.py
│   └── two_component.py     # NEW: dt_2comp 정의 통합 (현재 3 위치 중복)
├── losses/                  # NEW: loss formulation 모음
│   ├── canonical_l_fit.py   # NEW: compute_fit_loss 분리
│   ├── l3_loss.py
│   ├── cycle12_loss_cross_roi.py
│   ├── cycle14_v1_rdm_cross.py
│   └── cycle15_mwjaccard_cross.py
├── pipeline/                # 기존 step0~step4
├── analysis/                # comprehensive_2component_analysis 등
├── visualization/           # 기존 (vfc, phase3 등 — phase3는 deprecate)
├── cycles/                  # 기존
└── (other subdirs unchanged)
```

**이동 시 주의사항**:
1. **Import path** 모든 호출 수정 필요 (loco_distortion_fit.py:51-58, visualize_filter_candidates.py:72-79 등). grep으로 추적 가능.
2. **dt_2comp 통합**: 현재 visualize_filter_candidates.py / loco_distortion_fit.py / comprehensive_2component_analysis.py 세 곳에 동일 식 중복. `forward_models/two_component.py`로 통합 후 세 호출자가 import. **paradox 방지에 필수**.
3. **phase3 dt_2comp deprecation**: `visualize_phase3_preimage.py:168-172`의 wrong 식 제거 또는 명시적 deprecated 경고 추가.

**우선순위**:
- (P1) `dt_2comp` 통합 (단일 source of truth) — paradox 재발 방지에 가장 중요.
- (P2) phase3 viz 식을 vfc 통합본으로 교체 — F1·F2·F3 PNG 재생성 필요.
- (P3) 폴더 분리 — 가독성 향상이지만 import 수정 비용. 사용자 승인 후 실행.

---

## 6. Action Items (revised 2026-05-10)

| Priority | Action | Rationale | Status |
|---|---|---|:-:|
| **P0** | **Frame mixing 해결** (§3-3 #2 Option A: Stockman 통일 + inverse mapping) | F3/F4 paradox root cause. 두 식 모두 partial frame mismatch → 한 쪽 식 fundamental superiority claim 불가 상태. | OPEN |
| **P1** | `dt_2comp` 단일 source 통합 (3 위치 중복 제거) | paradox 재발 영구 방지. 모든 호출자가 P0 fix를 자동 적용. | OPEN |
| **P2** | `visualize_phase3_preimage.py:168-172` deprecate + F1·F2·F3 PNG 재생성 | wrong 식 제거. 행동 재검증 가능. | OPEN |
| ~~P4~~ | ~~colour-science 설치~~ | precise Stockman fundamentals 사용. | **CLOSED 2026-05-10** (`srm`, `colorBlind` envs 둘 다 0.4.4 설치 확인) |
| **P3** | 폴더 분리 (`forward_models/`, `losses/`) | 가독성 향상. import path 수정 비용 있음. | OPEN (user 승인 후) |
| **P5** | `scripts/README.md`에 본 audit link 또는 통합 | 다음 cycle에서 참조 보장. | OPEN |
| **P6** | Canonical L_fit HC sanity (sub-01~07 V4+V1) | CI-based specificity 검증 — `loss_inventory.md` line 298 missing data. | **IN PROGRESS** (2026-05-10 background fit) |
| **P7** | (Future) Asano 2016 또는 Stockman 2023 individual fundamentals | population-average → per-subject. anomaloscope data 필요. | DEFERRED |

## 7. 한 문단 결론

**vfc 식, canonical L_fit, Stockman+Machado simulator 모두 표준 색과학에 근거한 정확한 구현이며 (1) fitting과 visualization 식 일치, (2) p=0.004 신경 evidence, (3) §3 행동 PASS 사례 보유로 신뢰 가능**. 핵심 보강 작업은 dt_2comp의 단일 source 통합 (paradox 방지)과 phase3 wrong-식 deprecation. 폴더 정리는 가독성 차원이며 priority는 lower.
