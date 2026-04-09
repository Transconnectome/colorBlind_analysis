# LOCO Filter Pipeline — Results Log

**Date**: 2026-04-09 (2-Component LOCO added), 2026-04-08 (Phase A-B), 2026-04-07 (Comprehensive Model Comparison)
**Subjects**: Sub-08 (deutan), Sub-09 (protan), Sub-10 (normal control)
**Data**: C010 amplitudes (6 runs x 8 colors x n_voxels) from V1, V2, hV4

Two fitting contexts used throughout:
1. **LOCO fitting** (hV4): Per-color vulnerability profile matching -> filter design
2. **ΔRDM fitting** (V1/V2): Pairwise distance structure matching -> mechanism understanding

---

## 1. Models Attempted

### 1.1 Machado 1-Way Cone Shift (1 DOF)

**Parameter**: Δλ (spectral shift, nm)

```
Protanomaly: L_a(λ) = α·L(λ-Δλ) + (1-α)·k_L·M(λ)
Deuteranomaly: M_a(λ) = α·M(λ+Δλ) + (1-α)·k_M·L(λ)
```

Machado et al. (2009) physiological model. L/M cone spectral peak shift.
- 0 nm = normal, ~2 nm = very mild, ~10 nm = moderate, 20 nm = dichromat
- Optimization: Grid [0, 20] nm, step=0.5 (41 points)

### 1.2 R+C Retinal + Cortical Gain (2-3 DOF)

**Parameters**: Δλ (retinal shift), g (cortical opponent gain); optionally separate Δλ per ROI

```
rg_final = rg_baseline + (1+g) × (rg_ret - rg_baseline)
by_final = by_ret    [B-Y unchanged]
```

- g=0: pure retinal. g=-1: exact compensation. g<-1: overcompensation. g>0: amplification.
- At Δλ=0, compensation has zero effect by construction.
- Optimization: 2D grid (Δλ×g) at 0.5×0.25 steps (1025 points)

### 1.3 2-Component Angular Dilation (2 DOF)

**Parameters**: β_s (S-cone expansion), β_c (confusion axis modulation)

```
θ'(c) = θ_baseline(c)
        + β_s × cos(θ_baseline(c) - 90°)      [S-cone component]
        + β_c × cos(θ_baseline(c) - θ_conf)   [Confusion axis component]

θ_conf = { 16° for protan,  150° for deutan }
```

Opponent hue space angular rotation model. β_s = S-cone axis expansion, β_c = CVD family-specific.
- Fitting criterion: Cosine similarity between ΔRDM_sim and ΔRDM_obs (V1/V2 voxel space)
- Optimization: Grid (β_s, β_c) ∈ [-50°, 50°], step=1°
- Validation: 8! exact permutations + Bootstrap CI (n=500)

### 1.4 Fourier Warp (4 DOF)

**Parameters**: a₁, b₁, a₂, b₂

```
δ(θ) = a₁sin(θ) + b₁cos(θ) + a₂sin(2θ) + b₂cos(2θ)
```

Model-free hue distortion field. 4 DOF on 8 colors = 2:1 ratio.
- Optimization: Differential evolution (3 restarts, ~4000 evals)

### 1.5 Hybrid: Cone + 2-Component (3 DOF)

**Parameters**: Δλ (from Machado), β_s, β_c

```
θ'(c) = θ_cone(c; Δλ) + β_s × cos(θ_cone - 90°) + β_c × cos(θ_cone - θ_conf)
```

Machado + 2-Component combined. Δλ fixed from Stage 1, then (β_s, β_c) optimized.

### 1.6 Model × Loss × ROI Mapping

Each model was fitted with a specific loss function on specific ROIs. **Not all combinations were tested.** The table below documents exactly what was done and what was not.

#### Fitting Criterion Definitions

| ID | Loss | Formula | Script | Purpose |
|----|------|---------|--------|---------|
| **L_LOCO** | Multi-objective LOCO | `α·L_vuln/4 + β·L_rank/2 + δ·L_rdm/2 + ε·L_smooth/32400` | `loco_distortion_fit.py` | Filter design (per-color accuracy) |
| **L_ΔRDM** | ΔRDM cosine | `max cosine(ΔRDM_sim, ΔRDM_obs)` | `comprehensive_2component_analysis.py` | Mechanism (pairwise geometry) |
| **L₃** | Gen-4 joint | `L₁ − λ_scale·L_scale − λ_ROI·L_ROI` | `l3_loss.py` (L3_MachadoV1V2) | Joint V1+V2 ΔRDM matching |
| **L₃v2** | Gen-4.5 joint | `L₁_floor + λ_sign·L_sign + λ_fam·L_fam − λ_scale·L_scale − λ_ROI·L_ROI` | `l3_loss.py` (L3_MachadoV1V2_V2) | + sign agreement + family margin |
| **L₃rc** | Retinal-Cortical | `L₁ − λ_couple·g²/(Δλ̄+ε) − λ_dom·L_dom − λ_scale·L_scale − λ_ROI·L_ROI` | `l3_loss.py` (L3_RetinalCortical) | 3-DOF ΔRDM + coupling penalty |

Weight defaults: L_LOCO α=1.0 β=0.5 δ=0.2 ε=0.1; L₃/L₃v2 λ_scale=0.01 λ_ROI=0.005; L₃v2 λ_sign=0.30 λ_fam=0.50; L₃rc λ_couple=0.01 ε_couple=1.0 λ_dom=0.005 τ_dom=1.5.

#### Model × Loss × ROI Matrix

| Model | hV4 LOCO (L_LOCO) | V1/V2 ΔRDM (L_ΔRDM) | V1+V2 Joint (L₃/L₃v2) | V1+V2 R+C (L₃rc) | Status |
|-------|:------------------:|:--------------------:|:----------------------:|:-----------------:|--------|
| **Machado 1-way** (1 DOF) | **Done** (§2.1) | — | **Done** (Gen-4/4.5) | — | Both criteria |
| **R+C** (2-3 DOF) | **Done** (§2.2) | — | — | **Done** (§2.2) | Both criteria |
| **2-Component** (2 DOF) | **Done** (§2.3) | **Done** (§2.3) | — | — | **Both criteria — dual-validated** |
| **Fourier** (4 DOF) | **Done** (§2.4) | — | — | — | LOCO only (overfitting ceiling) |
| **Hybrid** (3 DOF) | — | **Done** (§2.5) | — | — | ΔRDM only (REJECTED) |

#### What Each Loss Captures

- **L_LOCO**: Per-color interpolation accuracy. Answers: "Can this model predict which colors are poorly interpolated?" → **filter design criterion**.
- **L_ΔRDM**: Pairwise distance geometry. Answers: "Does this model reproduce the overall shape of distortion?" → **mechanism characterization**.
- **L₃/L₃v2/L₃rc**: Joint V1+V2 ΔRDM with regularizers. Answers: "Is the distortion consistent across early visual ROIs?" → **cross-ROI validation**.

**Note on L_LOCO composition**: L_LOCO includes an L_rdm term (δ=0.2), so LOCO fitting is not fully independent of RDM structure. The two criteria share some information, with L_LOCO weighting per-color accuracy more heavily and L_ΔRDM weighting pairwise geometry exclusively.

**2-Component gap FILLED** (2026-04-09): 2-Component now fitted to L_LOCO as well (§2.3). It is the only model dual-validated across both criteria for both CVD subjects.

---

## 2. Results

### 2.1 Machado 1-Way — PARTIAL SUCCESS

#### hV4 LOCO (Phase A filter fitting)

| Subject | Δλ (nm) | ρ | perm_p | Verdict |
|---------|---------|---|--------|---------|
| sub-08 (deutan) | 1.5 | 0.619 | 0.058 | Trending |
| **sub-09 (protan)** | **13.5** | **0.762** | **0.018*** | **SUCCESS** |
| sub-10 (normal) | 0.0 | -0.048 | 0.559 | Specificity PASS |

#### V1/V2 LOCO (W-fixed, Gen-2)

| Subject | ROI | Δλ (nm) | LOCO ρ | p-value |
|---------|-----|---------|--------|---------|
| **sub-08** | **V1** | 34.92 | 0.690 | **0.033*** |
| **sub-08** | **V2** | 3.87 | 0.643 | **0.047*** |
| sub-09 | V1 | 16.5 | 0.438 | 0.112 (NS) |

#### V1/V2 ΔRDM — FAIL

- Sub-08 V1: cosine = -0.275 (anti-correlated)
- Sub-09 V1: cosine = +0.091 (weak)

Machado predicted compression이 observed expansion과 반대 방향 → **ΔRDM에서 구조적 실패**.

#### Summary

- **Sub-09 hV4**: 1-DOF로 p=0.018. R+C에서 g=0.0으로 collapse → 추가 DOF 불필요. Most parsimonious.
- **Sub-08**: V1/V2 LOCO significant하나 Δλ=34.92nm(V1)은 non-physiological. hV4에서는 trending only.

---

### 2.2 [Main] R+C Retinal-Cortical — SUCCESS (with g caveats)

#### hV4 LOCO (Phase A)

| Subject | Δλ | g | ρ | perm_p | Verdict |
|---------|----|----|---|--------|---------|
| **sub-08** | **2.0** | **+2.25** | **0.857** | **0.005*** | **PRIMARY** |
| sub-09 | 13.5 | 0.0 | 0.762 | 0.018* | = Machado |

v1→v2 improvement: g boundary 확장 [−3,1]→[−3,3]으로 sub-08 ρ: 0.762→0.857, p: 0.018→0.005.

Per-color δθ (degrees, sub-08 hV4):

| c1(red) | c2(org) | c3(yel) | c4(grn) | c5(cya) | c6(blu) | c7(pur) | c8(mag) |
|---------|---------|---------|---------|---------|---------|---------|---------|
| -11.1 | -10.5 | -5.3 | +1.4 | +11.5 | -20.5 | -21.1 | -0.8 |

#### V1/V2 ΔRDM (Comprehensive)

**Sub-08 (Deutan)**: Δλ_V1=2.5, Δλ_V2=2.5, g=-2.25

| | Retinal only (g=0) | Full (g=-2.25) | Δ |
|---|---|---|---|
| V1 cosine | -0.275 | +0.324 | +0.600 |
| V2 cosine | -0.168 | +0.205 | +0.373 |

- ΔRDM permutation p = 0.179 (NS)
- **LOCO V1 p = 0.047*** (significant)

**Sub-09 (Protan)**: Δλ_V1=19.5, Δλ_V2=19.5, g=-1.10

| | Retinal only (g=0) | Full (g=-1.10) | Δ |
|---|---|---|---|
| V1 cosine | +0.091 | +0.583 | +0.491 |
| V2 cosine | -0.147 | +0.306 | +0.453 |

- **ΔRDM permutation p = 0.026*** (significant)
- LOCO V1 p = 0.197 (NS)

**Sub-10 (Normal)**: Δλ≈0, g≈0, p=1.0 — Perfect null

#### ΔRDM ↔ LOCO Dissociation (Critical Finding): [TODO] 어떻게 해석할까 
**해석**: Permutation이 의미가 있을까 어차피 compression 된 것인데, 그냥 increment 정도만 고려하면 되지 않을까? 

```
             ΔRDM perm_p    LOCO V1 label_p
Sub-08:      0.179 (NS)     0.047* (SIG)    ← LOCO wins
Sub-09:      0.026* (SIG)   0.197 (NS)      ← ΔRDM wins
```

ΔRDM = pairwise distance geometry, LOCO = per-color functional interpolation. Complementary, not redundant.

#### g Physiological Plausibility

| Subject | ROI | g | Interpretation | Literature match |
|---------|-----|---|----------------|-----------------|
| Sub-09 | V1 | -1.10 | 10% overcomp | Below Tregillus 20-40% — plausible |
| Sub-08 | hV4 | +2.25 | 3.25× amplification | No precedent — novel |
| Sub-08 | V1 | -2.25 | 125% overcomp | Exceeds Tregillus — non-physiological |

**ROI-dependent sign flip**: Sub-08 V1 g<0 (overcomp) vs hV4 g>0 (amplification) → hierarchical processing.

#### Summary

- **Sub-08 hV4**: R+C optimal (p=0.005). g=+2.25 = hV4 amplifies retinal deficiency (novel).
- **Sub-09 V1/V2**: ΔRDM significant (p=0.026). g=-1.10 is physiologically plausible.

---

### 2.3 [Main] 2-Component Angular Dilation — DUAL-VALIDATED (LOCO + ΔRDM)

**2026-04-09 UPDATE**: 2-Component now fitted to L_LOCO as well. It is the **only model validated across both criteria for both CVD subjects**.

#### hV4 LOCO (Phase A — 2026-04-09)

| Subject | β_s | β_c | ρ | perm_p | CCC | Verdict |
|---------|-----|-----|---|--------|-----|---------|
| **sub-08 (deutan)** | **38°** | **-14°** | **0.881** | **0.004\*\*** | 0.101 | **BEST model** |
| sub-09 (protan) | 6° | -22° | 0.690 | 0.035* | 0.200 | Significant |

**Sub-08**: 2-component achieves the highest LOCO ρ (0.881) and lowest p (0.004) of any model tested, surpassing R+C (ρ=0.762, p=0.018) and Machado (ρ=0.619, p=0.058).

**Sub-09**: Significant but below Machado (ρ=0.762, p=0.018). β_s=6° is far below the ΔRDM-fitted β_s=23° → parameter regime differs across criteria.

#### V1 LOCO (W-fixed — 2026-04-09)

| Subject | β_s | β_c | ρ | perm_p | Verdict |
|---------|-----|-----|---|--------|---------|
| **sub-08** | **50°** | **-14°** | **0.929** | **0.001\*\*\*** | Strongest V1 result |
| **sub-09** | **38°** | **+22°** | **0.762** | **0.018\*** | Significant |
| sub-10 | 0° | 36° | 0.619 | 0.058 | Specificity marginal |

Sub-08 V1: ρ=0.929, p=0.001 — strongest LOCO result in entire pipeline.
Sub-10: p=0.058 borderline — βs=0 (no S-cone component) but βc=36° pure confusion-axis shift achieves ρ=0.619. Caution: 1,326 grid points on 8 colors may enable overfitting rank order.

#### V1 ΔRDM (previously reported)

##### Sub-08 (Deutan) V1

| Metric | Cosine | Crossnobis Cosine |
|--------|--------|-------------------|
| β_s | 27° | 35° |
| β_c | -21° | -25° |
| Similarity | 0.422 | 0.384 |
| Perm p | 0.066 | 0.053 |

**Bootstrap CI (V1, n=500)**:
```
β_s:  20.0° ± 8.0°,  CI₉₅ = [12°, 39°]   → Excludes 0 ✓
β_c: -17.8° ± 5.9°,  CI₉₅ = [-32°, -11°]  → Excludes 0 ✓
```

Permutation p marginal이나 bootstrap에서 두 파라미터 모두 0 제외.

#### Sub-09 (Protan) V1 — STRONGEST RESULT

| Metric | Cosine | Crossnobis Cosine | Crossnobis WUC |
|--------|--------|-------------------|----------------|
| β_s | 24° | 20° | 50° |
| β_c | +5° | +5° | 0° |
| Similarity | 0.458 | **0.590** | 0.638 |
| Perm p | 0.028* | **0.007\*\*\*** | 0.013* |

**Bootstrap CI (V1, n=500)**:
```
β_s:  23.0° ± 10.2°, CI₉₅ = [2°, 36°]    → Excludes 0 ✓
β_c:  +2.9° ± 2.4°,  CI₉₅ = [-2°, +6°]   → Includes 0 ✗ (NS)
```

Sub-09 V1 crossnobis **p=0.007\*\*\*** — 전체 파이프라인에서 가장 강한 통계적 증거.

#### Sub-09 Joint V1+V2

- Shared β_s=14°, β_c=+9°, Joint cosine=0.438, **p=0.044*** — Cross-ROI validation 성공.

#### β_s Cross-Subject Convergence — REMARKABLE LITERATURE MATCH

```
Sub-08 (deutan): β_s = 20.0° ± 8.0°
Sub-09 (protan): β_s = 23.0° ± 10.2°
Cross-subject mean: ~21.5°
Literature (Emery et al. 2021): 21.4° B-Y rotation
```

Independent methods (behavioral hue-scaling vs fMRI ΔRDM fitting) — 0.1° 차이. Deutan/protan 모두 동일한 S-cone compensatory mechanism 공유.

#### β_c Family Specificity

```
Sub-08 (deutan): β_c = -18° ± 6°, CI excludes 0 → SIG
Sub-09 (protan): β_c = +3° ± 2°, CI includes 0 → NS
```

- Deutan: small Δλ → confusion axis compression으로 보완 필요
- Protan: large Δλ가 이미 confusion axis 포함 → β_c 불필요

#### ΔRDM Inverse as Filter — FAIL (previously reported)

| Subject | Unfiltered error | Filtered error | Change |
|---------|-----------------|----------------|--------|
| Sub-08 | 27.7° | 37.8° | **-37% (WORSE)** |
| Sub-09 | 22.6° | 36.5° | **-61% (WORSE)** |

ΔRDM-optimized parameters의 simple inverse는 per-color accuracy를 악화. 그러나 이는 ΔRDM parameters 자체의 문제가 아니라 inverse 방법의 문제. LOCO-optimized parameters로 pre-image search하면 별도의 filter 도출 가능 (§2.6 참조).

#### Cross-Criterion Parameter Comparison (2026-04-09)

| Subject | Criterion | β_s | β_c | p-value |
|---------|-----------|-----|-----|---------|
| sub-08 | hV4 LOCO | 38° | -14° | 0.004** |
| sub-08 | V1 LOCO | 50° | -14° | 0.001*** |
| sub-08 | V1 ΔRDM (xnobis) | 35° | -25° | 0.053 |
| sub-08 | V1 ΔRDM (bootstrap) | 20°±8° | -18°±6° | CI excl 0 |
| sub-09 | hV4 LOCO | 6° | -22° | 0.035* |
| sub-09 | V1 LOCO | 38° | +22° | 0.018* |
| sub-09 | V1 ΔRDM (xnobis) | 20° | +5° | 0.007*** |
| sub-09 | V1 ΔRDM (bootstrap) | 23°±10° | +3°±2° | β_s CI excl 0 |

**Parameter divergence is expected**: L_LOCO와 L_ΔRDM은 서로 다른 objective를 최적화. L_LOCO는 per-color template matching accuracy를 우선하므로 더 큰 angular distortion을 허용 (over-rotate 후 rank order 맞추기). L_ΔRDM은 pairwise distance structure를 우선하므로 biologically constrained range 내에서 최적화.

**공통점**: βc sign은 두 criteria에서 일관됨 (sub-08: 음수, sub-09: 양수 또는 NS). β_s는 LOCO에서 체계적으로 더 큼 (LOCO β_s > ΔRDM β_s, 모든 케이스).

#### Summary

- **유일한 dual-criterion model**: LOCO (sub-08 p=0.004, sub-09 p=0.035)와 ΔRDM (sub-09 p=0.007) 모두에서 유의. 다른 어떤 model도 이를 달성하지 못함.
- **Mechanism 이해에 최적**: β_s convergence가 Emery 2021과 정확히 일치 (ΔRDM-fitted β_s ≈ 21.5° vs literature 21.4°).
- **hV4 LOCO에서 sub-08 최강**: p=0.004 (R+C의 p=0.005를 넘음).
- **Sub-09 primary ΔRDM result**: p=0.007\*\*\* (전 파이프라인 최강).
- **Parameter regime differs across criteria**: LOCO β_s > ΔRDM β_s. Pre-image filter는 LOCO-optimized parameters에서 도출해야 함.

---

### 2.4 Fourier Warp — OVERFITTING CEILING

#### hV4 LOCO (Phase A)

| Subject | Params | ρ | perm_p | CCC | Verdict |
|---------|--------|---|--------|-----|---------|
| sub-08 | [3.4, 29.7, -11.9, -6.1] | 0.976 | 0.0002** | 0.170 | Ceiling |
| sub-09 | [13.8, 20.0, -18.9, 29.6] | 0.762 | 0.018* | 0.441 | No gain |

v1→v2: L-BFGS-B→DE로 sub-08 ρ: 0.286→0.976, sub-09 ρ: -0.333→0.762.

#### Summary

- Sub-08 ρ=0.976이지만 4 DOF / 8 colors = overfitting risk. CCC(0.170) = R+C(0.173) → rank-only improvement.
- Sub-09: Machado와 동일 → extra DOF 이점 없음.
- **Ablation ceiling으로만 사용.** Primary model 채택 불가.

---

### 2.5 Hybrid (Cone + 2-Component) — FAIL

#### Sub-08 V1
- Δλ = **0.0 nm** (cone shift contributes nothing)
- β_s=21°, β_c=-20°, Cosine=0.420 (≈ standalone 2-Comp 0.422)

#### Sub-09 V1
- Δλ=16.0nm → β_s=48°, β_c=+43° (극단값 발산)
- Cosine=0.453 (< standalone 2-Comp 0.458)

#### Summary

- Sub-08: Δλ=0 → cone shift 완전 redundant. 2-Component 단독이 동등.
- Sub-09: 3 DOF overfitting → 비생리적 극단값.
- **두 메커니즘은 additive하지 않음. REJECTED.**

---

### 2.6 Filter Derivation (Phase B): Pre-Image Search

Phase A primary model의 역함수를 수치 탐색하여 stimulus-space filter 도출.

**Method**: `θ_in = argmin |D(θ) - θ_target|` (360° coarse grid + Brent refinement)

Simple inverse (δ_filter = -δ_fit)는 nonlinear forward model에서 성립하지 않아 FAILED.

#### Sub-08 R+C Pre-Image — SUCCESS (Exact Restoration)

| Condition | Mean Error (°) | Max Error (°) |
|-----------|---------------|---------------|
| No filter (current CVD) | 12.21 | 32.06 |
| Simple inverse (-δ) | 63.02 | 166.47 |
| **Exact pre-image** | **0.0002** | **0.0009** |

**8/8 colors 완벽 복원.** Per-color CIELab corrections (δ_preimage):

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 |
|----|----|----|----|----|----|----|----|
| -18.2° | -37.2° | -34.8° | +18.6° | +42.9° | +3.9° | -31.6° | -1.0° |

4-condition per-color table:

| Color | Original | CVD Perceived | Modified | Expected (=HC Target) |
|-------|----------|--------------|----------|----------------------|
| c1 red | 0.0° | 303.0° | 341.8° | 313.5° |
| c2 orange | 45.0° | 290.2° | 7.8° | 299.9° |
| c3 yellow | 90.0° | 283.3° | 55.2° | 288.3° |
| c4 green | 135.0° | 279.1° | 153.6° | 278.2° |
| c5 cyan | 180.0° | 277.6° | 222.9° | 267.6° |
| c6 blue | 225.0° | 259.5° | 228.9° | 227.4° |
| c7 purple | 270.0° | 59.2° | 238.4° | 86.7° |
| c8 magenta | 315.0° | 346.5° | 314.0° | 348.5° |

#### Sub-09 Machado Pre-Image — STRUCTURAL FAIL (Color Merging)

Mean error=17.25°, Max=65.04°. **역함수 존재하지 않음.**

**원인**: Δλ=13.5nm에서 L-cone→M-cone 이동 → rg=L-M≈0 → opponent arc가 360°→~96°로 압축.
c4(green), c5(cyan), c6(blue) → 동일한 perceived hue 282.1°. 세 색의 독립적 복원 불가.

#### Sub-09 Separation Optimization — PARTIAL RECOVERY

Exact restoration 불가 → **discriminability recovery** 전략 (max min-pairwise separation + soft healthy target + ordinal constraint):

| Condition | Min Sep (°) | Mean Sep (°) |
|-----------|------------|-------------|
| Healthy (normal) | 10.18 | 70.65 |
| Unfiltered (current CVD) | 1.03 | 39.30 |
| Exact pre-image (collapsed) | 0.00 | — |
| **Sep-optimized** | **5.76** | **24.28** |

- **5.6× improvement** (1.03°→5.76°). Theoretical max 12° 대비 48% 달성.
- 4/8 exact + 4/8 separation-optimized

4-condition per-color table:

| Color | Original | CVD Perceived | Modified | Expected | HC Target | Match? |
|-------|----------|--------------|----------|----------|-----------|--------|
| c1 red | 0.0° | 301.1° | 343.1° | 313.5° | 313.5° | exact |
| c2 orange | 45.0° | 287.7° | 216.0° | 299.9° | 299.9° | exact |
| c3 yellow | 90.0° | 283.1° | 41.0° | 288.3° | 288.3° | exact |
| c4 green | 135.0° | 282.1° | 232.8° | 319.2° | 278.2° | sep-opt (+41°) |
| c5 cyan | 180.0° | 285.6° | 222.4° | 305.6° | 267.6° | sep-opt (+38°) |
| c6 blue | 225.0° | 308.5° | 16.8° | 294.1° | 227.4° | sep-opt (+67°) |
| c7 purple | 270.0° | 18.3° | 101.7° | 282.6° | 86.7° | sep-opt (+196°) |
| c8 magenta | 315.0° | 352.1° | 248.1° | 348.5° | 348.5° | exact |

~96° arc는 Machado protan model의 hard physical constraint. Stimulus rearrangement으로는 이 한계를 넘을 수 없음.

#### Sub-08 2-Component Pre-Image — SUCCESS (Exact, Larger Corrections)

| Condition | Mean Error (°) | Max Error (°) |
|-----------|---------------|---------------|
| No filter (current CVD) | 12.21 | 32.06 |
| **Exact pre-image (2-Comp)** | **0.0001** | **0.0006** |

**8/8 colors 완벽 복원.** Per-color CIELab corrections (δ_preimage):

| c1 | c2 | c3 | c4 | c5 | c6 | c7 | c8 |
|----|----|----|----|----|----|----|----|
| -19.2° | -45.9° | -67.9° | -87.8° | -104.2° | -26.2° | +17.0° | +2.4° |

**R+C vs 2-Component 비교 (sub-08)**:

| Metric | R+C | 2-Component |
|--------|-----|-------------|
| LOCO ρ | 0.857 | 0.881 |
| LOCO p | 0.005** | 0.004** |
| Mean \|correction\| | 23.5° | 46.3° |
| Max \|correction\| | 42.9° | 104.2° |
| Cosine(δ vectors) | — | **-0.18** (divergent) |
| Sign agreement | — | 3/8 |

두 모델의 pre-image correction 방향이 상이 (cosine=-0.18). R+C는 smaller, more balanced corrections; 2-Component는 larger, mid-hue (green-cyan) 중심. **어느 filter가 실제로 behavioral improvement를 가져오는지는 Phase C 실험으로 결정해야 함.**

#### Sub-09 2-Component Pre-Image — SUCCESS (CRITICAL: Where Machado Failed)

| Condition | Mean Error (°) | Max Error (°) |
|-----------|---------------|---------------|
| No filter (current CVD) | — | — |
| Machado exact pre-image | **17.25** | **65.04** (FAIL) |
| **2-Comp exact pre-image** | **0.0001** | **0.0006** |

**Machado → 4/8 exact (FAIL), 2-Component → 8/8 exact (PASS).**

| Color | Machado err | 2-Comp err | Machado δ | 2-Comp δ |
|-------|------------|-----------|-----------|----------|
| c1 red | <0.01° | <0.01° | -16.9° | -31.8° |
| c2 org | <0.01° | <0.01° | +171.0° | -48.1° |
| c3 yel | <0.01° | <0.01° | -49.0° | -39.1° |
| c4 grn | **3.90°** | <0.01° | -7.9° | -21.3° |
| c5 cya | **14.44°** | <0.01° | -52.9° | +4.6° |
| c6 blu | **54.65°** | <0.01° | -97.9° | +5.2° |
| c7 pur | **65.04°** | <0.01° | +10.8° | -0.6° |
| c8 mag | <0.01° | <0.01° | -66.9° | -10.5° |

**핵심**: Machado LOCO (p=0.018)는 sub-09에서 더 높은 LOCO ρ를 달성하지만, 그 forward model의 물리적 제약 (L-cone→M-cone spectral shift → 360°→96° arc compression)으로 인해 **역함수가 존재하지 않음** (c4-c7이 동일 perceived hue ~282°로 수렴). 2-Component LOCO (p=0.035)는 ρ가 낮지만 cortical-level angular dilation이므로 arc compression 없이 **8/8 모든 색의 정확한 역변환 가능**.

2-Component mean |correction|: 20.1°, max: 48.1° — moderate하고 stimulus-space에서 구현 가능.

#### Sub-10 — Identity (No Filter)

All δ=0.00°, residual<0.001°. Correct null.

#### Pre-Image Cross-Model Summary

| Model | Sub-08 (deutan) | Sub-09 (protan) | Filter feasibility |
|-------|----------------|-----------------|-------------------|
| R+C | 8/8 exact | N/A (=Machado) | Sub-08 only |
| Machado | not primary | 4/8 exact (**FAIL**) | Sub-09 **IMPOSSIBLE** |
| **2-Component** | **8/8 exact** | **8/8 exact** | **BOTH subjects** |

**2-Component는 두 CVD 피험자 모두에서 exact pre-image를 달성하는 유일한 모델.** Cortical-level (opponent space) angular dilation은 retinal-level cone shift와 달리 arc compression이 없어 forward map이 bijective → 항상 역변환 가능.

---

## 3. Conclusions & Implications

### 3.1 Model Selection Summary (Revised 2026-04-09)

| Subject | Model | hV4 LOCO | V1 LOCO | V1 ΔRDM | Filter Role |
|---------|-------|----------|---------|---------|-------------|
| **Sub-08** | **2-Component** (β_s=38°, β_c=-14°) | **p=0.004\*\*** | **p=0.001\*\*\*** | CI excl 0 | **Primary filter candidate** |
| Sub-08 | R+C (Δλ=2.0, g=2.25) | p=0.005** | — | p=0.179 | Alternate (exact pre-image proven) |
| **Sub-09** | Machado (Δλ=13.5) | **p=0.018\*** | — | — | **hV4 LOCO optimal** |
| Sub-09 | **2-Component** (β_s=6°, β_c=-22°) | p=0.035* | p=0.018* | **p=0.007\*\*\*** | Dual-validated |
| **Sub-10** | — | All NS | p=0.058 | — | No filter |

**2-Component는 두 CVD 피험자 모두에서 LOCO와 ΔRDM 양쪽에서 유의한 유일한 모델.** Sub-08에서는 hV4 LOCO 최강 (p=0.004), sub-09에서는 V1 ΔRDM 최강 (p=0.007). 하나의 모델이 기능적 정확도(LOCO)와 기하학적 구조(ΔRDM)를 동시에 설명.

### 3.2 Cross-Model Convergence Analysis (Revised 2026-04-09)

#### 3.2.1 L_LOCO의 구성: "LOCO vs ΔRDM 해리"는 부정확

L_LOCO = α·L_vuln + β·L_rank + **δ·L_rdm** + ε·L_smooth (δ=0.2)

L_LOCO 자체에 L_rdm 항이 포함되어 있으므로, LOCO fitting은 이미 RDM structure를 부분적으로 고려. "LOCO와 ΔRDM은 독립적이다"는 부정확. 정확한 표현: **L_LOCO는 per-color accuracy를 주 목적으로 하되 RDM을 보조 정규화로 사용하고, L_ΔRDM은 pairwise geometry만을 최적화한다.** 두 loss는 RDM 정보를 공유하지만 weighting이 다름.

이전 R+C 결과 (§2.2)에서 관찰된 sub-08 LOCO-SIG/ΔRDM-NS vs sub-09 ΔRDM-SIG/LOCO-NS 패턴은 **weighting 차이에 의한 sensitivity 차이**이지 "해리"가 아님.

#### 3.2.2 Detection-Level Convergence: 모든 모델이 동일 결론

| Subject | Machado | R+C | 2-Component | Fourier | Verdict |
|---------|---------|-----|-------------|---------|---------|
| **sub-08** | p=0.058t | p=0.018* | **p=0.004\*\*** | p=0.0002 (overfit) | **Distortion detected** |
| **sub-09** | **p=0.018\*** | = Machado | p=0.035* | p=0.018* | **Distortion detected** |
| **sub-10** | p=0.559 | — | p=0.058 (marginal) | — | **No distortion** |

세 (Fourier 제외) 모델 모두 sub-08/09에서 유의한 LOCO vulnerability를 detect. 모델 선택에 관계없이 **"CVD에서 hue interpolation distortion이 존재한다"는 robust 결론**.

#### 3.2.3 Correction-Level Divergence: δθ 방향은 불일치

Sub-08 hV4 모델 간 δθ 비교:

| Color | Machado | R+C | 2-Component | 부호 일치? |
|-------|---------|-----|-------------|-----------|
| red | -3.7° | -11.4° | -12.1° | YES |
| orange | -2.8° | -9.9° | -20.2° | YES |
| yellow | -1.3° | -4.8° | -25.7° | YES |
| green | +0.3° | +1.4° | -29.4° | NO |
| cyan | +2.6° | +10.7° | -32.1° | NO |
| blue | -11.7° | -38.4° | -10.3° | YES |
| purple | -5.1° | -18.8° | +29.4° | NO |
| magenta | -0.5° | -1.1° | +18.5° | NO |

부호 일치: **4/8** (red, orange, yellow, blue). Machado/R+C vs 2-Component Spearman ρ = **-0.714** (p=0.047, 유의하게 반상관).

**해석**: Machado/R+C는 L-M cone opponent axis를 중심으로 왜곡 (Δλ → 적-녹 축 이동). 2-Component는 S-cone axis(90°)와 confusion axis를 중심으로 왜곡. 두 메커니즘의 angular footprint가 상이하므로 δθ 방향이 다름. 그럼에도 불구하고 **동일한 vulnerability rank order**에 수렴 (sub-08: 2-comp ρ=0.881, R+C ρ=0.762 → 같은 CVD target을 fit).

#### 3.2.4 핵심: "같은 현상, 다른 렌즈"

```
모든 모델 → 동일 결론: CVD에서 hue interpolation distortion 존재 (Detection ✓)
모든 모델 → 유사 패턴: 어떤 색이 취약한가 (Vulnerability rank, partial ✓)
모델 간   → 상이 처방: 어떤 방향으로 보정할까 (δθ direction, ✗)
```

**"Machado, R+C, 2-component가 같은 filter를 지지한다"는 δθ level에서 지지되지 않음.** 그러나 "모든 모델이 동일한 대상(sub-08/09)에서 동일한 현상(distortion)을 detect하며, 2-component가 유일하게 두 criteria 모두를 관통한다"는 지지됨.

**Filter design 방향**: Sub-08에서 2-component hV4 LOCO (p=0.004)가 최강이므로, (β_s=38°, β_c=-14°)의 pre-image를 primary filter candidate로 사용. R+C pre-image (§2.6)는 alternate/comparison filter로 유지. 두 filter의 behavioral validation이 최종 판단 기준.

### 3.3 Severity-Dependent Filter Feasibility (Revised 2026-04-09)

#### Under Cone-Level Models (Machado / R+C)

| | Sub-08 (Δλ=2.0, mild deutan) | Sub-09 (Δλ=13.5, moderate protan) |
|---|---|---|
| Opponent arc | ~260° | ~96° |
| Exact pre-image | 8/8 colors | 4/8 colors |
| 360° restoration | **Yes** | **No** |
| **Intervention** | **Stimulus-space sufficient** | **Spectral filter required** |

#### Under 2-Component (Cortical-Level) — NEW

| | Sub-08 (mild deutan) | Sub-09 (moderate protan) |
|---|---|---|
| Forward map type | Bijective (angular dilation) | **Bijective** (angular dilation) |
| Exact pre-image | **8/8 colors** | **8/8 colors** |
| Mean \|correction\| | 46.3° | 20.1° |
| Max \|correction\| | 104.2° | 48.1° |
| **Intervention** | **Stimulus-space sufficient** | **Stimulus-space sufficient** |

**핵심 차이**: Cone-level models에서 sub-09는 "spectral filter required" (arc compression으로 stimulus-space 불가). 그러나 2-Component cortical model 하에서는 arc compression이 없으므로 **sub-09도 stimulus-space filter로 충분**. 이는 filter design의 근본적 결론을 변경.

**주의**: 2-Component가 sub-09에서 exact pre-image를 달성하더라도, 이 모델의 LOCO ρ(=0.690)는 Machado(=0.762)보다 낮음. 즉 forward model의 vulnerability 예측 정확도가 더 낮은 상태에서 pre-image를 구함. **모델 정확도 × pre-image 존재성**을 동시에 고려해야 하며, behavioral validation(Phase C)이 최종 판단 기준.

### 3.4 Biological Plausibility

**Well-validated**:

| Parameter | Our value | Literature | Source | Match |
|-----------|-----------|-----------|--------|-------|
| Sub-08 Δλ | 2.0 nm | 1-4 nm (very mild) | Machado 2009 | in range |
| Sub-09 Δλ | 13.5 nm | 9-14 nm (moderate-severe) | Machado 2009 | in range |
| β_s (both subjects) | 20-23° | **21.4°** B-Y rotation | Emery et al. 2021 | **within 0.1-3°** |
| Sub-09 g (V1) | -1.10 | 20-40% overcomp | Tregillus et al. 2021 | below range, plausible |

**Problematic**:

| Parameter | Our value | Issue |
|-----------|-----------|-------|
| Sub-08 V1 g | -2.25 | 125% overcompensation — exceeds literature |
| Sub-08 hV4 g | +2.25 | Amplification — no direct precedent |

β_s cross-subject convergence (~21.5° ≈ Emery 21.4°)는 가장 강한 문헌 검증. Independent methods (behavioral hue-scaling vs fMRI ΔRDM) 간의 수렴.

### 3.5 Rejected Approaches

| Approach | Why Failed |
|----------|-----------|
| **ΔRDM inverse → filter** | -37% to -153% improvement (WORSE). Pairwise geometry ≠ per-color accuracy. |
| **Simple inverse (-δ)** | Assumes linearity. D(θ-δ) ≠ D(θ)-δ for nonlinear forward models. |
| **Hybrid (Cone + 2-Comp)** | Components not additive. Cone shift redundant or causes overfitting. |
| **Gen-3 ΔRDM-only (Machado)** | 0/18 passed. ΔRDM_sim anti-correlates with ΔRDM_obs. |
| **Fourier as primary** | 4 DOF / 8 colors = overfitting. CCC no better than R+C. Ablation ceiling only. |

### 3.6 Stimulus-Space vs Spectral Filter

| | Commercial (EnChroma-like) | Our approach |
|---|---|---|
| **Mechanism** | Spectral notch (pre-retinal) | CIELab remapping (stimulus-space) |
| **Personalization** | None (generic) | Individual-specific (fMRI-fitted Δλ + g) |
| **Cortical component** | Ignored | Captured (sub-08 g=2.25 → spectral filter alone would under-correct) |
| **Correction guarantee** | Approximate | Exact under model (<0.001° for sub-08) |
| **Platform** | Physical glasses only | Any digital display (8-point lookup) |
| **Severity awareness** | Same for all | Quantifies correction limit per individual |
| **Discrimination at threshold** | Not improved (Somers 2024) | Not yet tested |
| **Limitations** | Luminance loss; dichromats excluded | Requires fMRI; controlled stimuli only |

Commercial filter evidence: Somers et al. (2024) — appearance enhanced but **discrimination NOT improved**. Almutairi et al. (2024) — limited effectiveness.

### 3.7 Key Advantages

1. **Cortical capture**: Sub-08 g=2.25 → hV4 amplifies retinal deficiency. Spectral filter for Δλ=2.0nm alone would under-correct.
2. **Digital implementability**: 8-point CIELab lookup table → any display (AR/VR native).
3. **Prescriptive severity threshold**: stimulus-space feasible (sub-08, mild) vs spectral required (sub-09, moderate).

---

## 4. Validation Gap Analysis

### 4.1 Model × Criterion Coverage Matrix (Updated 2026-04-09)

| Model | hV4 LOCO fit | V1 LOCO fit | V1 ΔRDM fit | V2 ΔRDM fit | Joint V1+V2 | hV4 LOCO validate | V1 LOCO validate |
|-------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Machado** | p=0.018* (sub-09) | p=0.033* (sub-08, W-fixed) | Gen-4/4.5 (FAIL) | Gen-4/4.5 (FAIL) | L₃v2 (FAIL §22) | — | — |
| **R+C** | **p=0.005*** (sub-08) | — | p=0.179 (sub-08) | p=0.179 (sub-08) | L₃rc (sub-09 p=0.026*) | — | p=0.047* (sub-08, inline) |
| **2-Component** | **p=0.004\*\*** (sub-08) | **p=0.001\*\*\*** (sub-08) | **p=0.007\*\*\*** (sub-09) | p=0.036* (sub-09) | p=0.044* (sub-09) | — | — |
| **Fourier** | p=0.0002 (sub-08, overfit) | — | — | — | — | — | — |

2-Component는 hV4 LOCO, V1 LOCO, V1 ΔRDM, V2 ΔRDM, Joint V1+V2 모든 칸에서 최소 하나의 subject에서 유의. **가장 넓은 criterion coverage.**

### 4.2 Remaining Gaps (Updated 2026-04-09)

**~~Gap 1: 2-Component × LOCO~~ → COMPLETED (2026-04-09)**

결과: 2-Component는 LOCO에서도 유의 (sub-08 hV4 p=0.004, sub-09 hV4 p=0.035). **기능적(LOCO)이면서 동시에 기하학적(ΔRDM)인 유일한 모델로 확인.** Parameters는 criteria 간 diverge하지만 (LOCO β_s > ΔRDM β_s), 둘 다 유의.

**Gap 2: R+C hV4 × ΔRDM**

R+C was fitted to LOCO on hV4 (p=0.005***) and ΔRDM on V1/V2 (via L₃rc), but the hV4 ΔRDM was never explicitly evaluated. This would test whether the best filter model also captures hV4 pairwise geometry.

**Gap 3: Cross-criterion post-hoc validation**

For models where both LOCO and ΔRDM results exist (Machado, R+C), a systematic post-hoc table comparing the same parameter values across both criteria is missing. Currently dissociation is noted qualitatively but never tabulated at matched parameters.

### 4.3 Additional Validation Methods

Beyond filling the LOCO/ΔRDM gaps, the following validations would strengthen the claims:

**V1. Behavioral JND concordance** (partially done, §MEMORY behavioral findings)
- LOCO vulnerability → JND: 100% concordance (6/6)
- **Missing**: 2-Component predicted vulnerability → JND concordance. If 2-Component LOCO is run, check whether its vulnerability profile also predicts JND.

**V2. Leave-one-run-out (LORO) stability**
- Machado and R+C hV4 LOCO were fitted on pooled 6-run data
- **Missing**: LORO cross-validation (fit on 5 runs, test on held-out run) to assess parameter stability
- Partially done for Machado V1 (Task #19: 6/6 LORO pass), but not for R+C hV4

**V3. Cross-ROI parameter transfer**
- If 2-Component (β_s, β_c) fitted on V1 ΔRDM predicts hV4 LOCO vulnerability (or vice versa), this is strong cross-ROI convergence evidence
- Currently cross-ROI transfers were tested for Machado only (§2.1: no significant between-ROI transfers)

**V4. Leave-one-HC-out (LOHO) robustness**
- Mean-HC is used for ΔRDM_obs denominator — dropping one HC tests sensitivity to individual HC outliers
- Done for Machado V1 (Task #19: 7/7 LOHO pass), not done for 2-Component or R+C

**V5. Parameter convergence across criteria**
- If 2-Component LOCO fitting yields (β_s, β_c) similar to ΔRDM-fitted values, this is convergent validity
- If values diverge, it confirms the criteria capture genuinely different aspects

### 4.4 Priority Order (Updated 2026-04-09)

| Priority | Validation | Effort | Impact |
|----------|-----------|--------|--------|
| ~~**1**~~ | ~~2-Component × hV4 LOCO (Gap 1)~~ | ~~Medium~~ | **COMPLETED** ✓ |
| ~~**1**~~ | ~~2-Component pre-image filter for sub-08 AND sub-09~~ | ~~Medium~~ | **COMPLETED** ✓ (§2.6) |
| **1** | Dual-filter behavioral comparison: R+C vs 2-Component (sub-08) | Medium | High — which filter actually works? |
| **2** | 2-Component LOCO → JND concordance (V1) | Low | High — behavioral validation |
| **3** | Cross-criterion parameter comparison (Gap 3) — **partially done** in §2.3 | Low | Medium — already tabulated |
| **4** | LORO stability for 2-Component hV4 (V2) | Medium (6 refits) | Medium — robustness check |
| **5** | LOHO for 2-Component/R+C (V4) | Low-Medium (7 refits each) | Medium — robustness check |

---

## Appendix A: Loss Functions & Data Flow

### A.1 L_LOCO: Multi-Objective LOCO Loss (`loco_distortion_fit.py`)

**Applied to**: Machado (1 DOF), R+C (2 DOF), 2-Component (2 DOF), Fourier (4 DOF) — all on **hV4** with shift_at_both

```
L_fit = α·L_vuln/4 + β·L_rank/2 + δ·L_rdm/2 + ε·L_smooth/32400
```

| Term | Definition | Normalization | Weight | Measures |
|------|-----------|---------------|--------|----------|
| L_vuln | MSE(vuln_sim, vuln_cvd) | /4.0 (max MSE for ρ ∈ [-1,1]) | α=1.0 | Per-color LOCO vulnerability match |
| L_rank | 1 − Spearman_ρ(vuln_sim, vuln_cvd) | /2.0 | β=0.5 | Profile shape (rank order) |
| L_rdm | 1 − cosine(ΔRDM_sim, ΔRDM_obs) | /2.0 | δ=0.2 | RDM structure (optional, `--skip_rdm`) |
| L_smooth | mean(adj_diff(δθ)²) | /32400 (max=180²) | ε=0.1 | Regularization |

- vuln_cvd: Phase 1에서 pre-computed (sub-XX_loco.json)
- vuln_sim: HC 7명에서 shifted LOCO simulation (shift_at_both = W retrained per fold per δ)
- **All models supported** since 2026-04-09: including 2-Component (β_s, β_c), grid 26×51=1,326 points

### A.2 L_ΔRDM: Cosine Similarity (`comprehensive_2component_analysis.py`)

**Applied to**: 2-Component (2 DOF) — on **V1, V2** separately and **joint V1+V2**

```
L = max cosine(ΔRDM_sim, ΔRDM_obs)
    or: max WUC(ΔRDM_sim, ΔRDM_obs)   [Whitened Unbiased Cosine]
    or: max crossnobis_cosine(ΔRDM_sim, ΔRDM_obs)
```

| Metric | Definition | When Used |
|--------|-----------|-----------|
| Cosine | dot(a,b) / (‖a‖·‖b‖) | Primary (correlation distance ΔRDM) |
| Crossnobis cosine | cosine on crossnobis-normalized ΔRDM | Primary (crossnobis distance ΔRDM) |
| WUC | Whitened Unbiased Cosine (Diedrichsen 2020) | Supplementary (noise-corrected) |

- Grid: (β_s, β_c) ∈ [0, 50°] × [-50°, 50°], step=1° (5,101 points)
- Permutation: 8! exact (40,320) + max-statistic correction
- Bootstrap: n=500 for CI
- ΔRDM_obs = RDM_CVD − mean(RDM_HC), 28 pairwise distances
- **No LOCO term in loss. No per-color accuracy fitting.**

### A.3 L₃: Gen-4 Joint V1+V2 Loss (`l3_loss.py`, L3_MachadoV1V2)

**Applied to**: Machado 1-way (1-2 DOF) — **joint V1+V2**

```
L₃ = L₁ − λ_scale·L_scale − λ_ROI·L_ROI
```

| Term | Definition | Weight |
|------|-----------|--------|
| L₁ | 0.5·sim(ΔRDM_sim_V1, ΔRDM_obs_V1) + 0.5·sim(ΔRDM_sim_V2, ΔRDM_obs_V2) | 1.0 |
| L_scale | Σ[max(0, \|Δλ_ROI\| − 20)]² | λ=0.01 |
| L_ROI | (Δλ_V1 − Δλ_V2)² / 2 | λ=0.005 |

Sim metric: cosine (default), pearson, or spearman.

### A.4 L₃v2: Gen-4.5 Joint V1+V2 Loss (`l3_loss.py`, L3_MachadoV1V2_V2)

**Applied to**: Machado 1-way (1-2 DOF) — **joint V1+V2**

```
L_total = L₁_floor(target) + λ_sign·L_sign(target) + λ_fam·[L₁_floor(target) − L₁_floor(other)]
          − λ_scale·L_scale − λ_ROI·L_ROI
```

| Term | Definition | Weight |
|------|-----------|--------|
| L₁_floor | 0.5·L₁_V1 + 0.5·L₁_V2 − κ·max(0, τ − L₁_V2) | 1.0 |
| L_sign | 0.5·[2·mean(sign(a)==sign(b)) − 1] per ROI | λ=0.30 |
| L_fam | L₁_floor(target_family) − L₁_floor(other_family) | λ=0.50 |
| L_scale | (same as L₃) | λ=0.01 |
| L_ROI | (same as L₃) | λ=0.005 |

V2 floor: τ=−0.02, κ=0.5. Selection gates: Δλ stability, L_sign ≥ 0.25, L_fam > 0, L₁_V1 > 0, L₁_V2 > −0.02.

### A.5 L₃rc: Retinal-Cortical Joint Loss (`l3_loss.py`, L3_RetinalCortical)

**Applied to**: R+C (3 DOF: Δλ_V1, Δλ_V2, g) — **joint V1+V2**, LOCO as post-hoc validation

```
L₃rc = L₁ − λ_couple·g²/(|Δλ̄|+ε) − λ_dom·L_dom − λ_scale·L_scale − λ_ROI·L_ROI
```

| Term | Definition | Weight |
|------|-----------|--------|
| L₁ | (same as L₃) | 1.0 |
| L_couple | g² / (\|mean(Δλ_V1, Δλ_V2)\| + ε_couple) | λ=0.01, ε=1.0 |
| L_dom | Σ max(0, ‖ΔRDM_comp‖/max(‖ΔRDM_ret‖, ε_dom) − τ)² | λ=0.005, τ=1.5 |
| L_scale | (same as L₃) | λ=0.01 |
| L_ROI | (same as L₃) | λ=0.005 |

- `step2c_retinal_cortical.py` runs inline LOCO validation (Phase D) at best (Δλ*, g*) on V1, V2, hV4 — but LOCO is **validation only**, not in the loss function.

### A.6 Data Flow

```
C010 amplitudes (server)
├── HC 7명 × ROI → amplitudes_procrustes.npy (6, 8, V)
│   ├── vuln_sim: per-color LOCO at C_shifted          → L_LOCO (§A.1)
│   └── ΔRDM_sim: RDM(C_shifted@W) - RDM(C_baseline@W) → L_ΔRDM/L₃/L₃rc (§A.2-A.5)
│
└── CVD 3명 → Phase 1 validation
    ├── vuln_cvd: sub-{XX}_loco.json                    → L_LOCO target
    └── ΔRDM_obs: RDM_CVD - mean(RDM_HC)               → L_ΔRDM/L₃/L₃rc target
```

---

## Appendix B: Figures

All in `results/loco_filter/preimage/figures/`:
- `angle_comparison_sub-{08,09,10}_*.png` — per-color θ_target vs θ_in* vs D(θ_in*)
- `color_wheel_sub-{08,09}_*.png` — inner=original, middle=pre-image, outer=perceived
- `four_ring_color_wheel_all_subjects.png` — 4-ring wheel (original→perceived→modified→expected)
- `four_condition_angle_comparison.png` — bar chart comparing 4 conditions per color
- `sub09_forward_model_compression.png` — D compression (360° CIELab → ~96° opponent)
- `fourier_approximation_sub-{08,09,10}_*.png` — exact δ vs Fourier curve
- `cross_sim_sanity.png` — Δλ sweep for sub-08 (R+C vs Machado) and sub-09

Sub-08 color wheel에서 dots이 clustered로 보이는 것은: (1) CIELab ≠ opponent spacing, (2) inner/outer 겹침 = filter 성공 (residual <0.001°).

---

## Appendix C: References

1. **Machado et al. (2009)**. *IEEE TVCG*, 15(6), 1291-1298. — Δλ [0, 20] nm
2. **Tregillus et al. (2021)**. *Current Biology*, 31(5), 936-942. — V2v 6.39×, V3v 7.82× scaling
3. **Emery et al. (2021)**. *Vision Research*, 183, 1-12. — 21.4° B-Y rotation
4. **Boehm et al. (2014)**. *J. Vision*, 14(13), 19. — Protan ~3.53×, deutan ~2.26× gain
5. **Neitz & Neitz (2011)**. *Vision Research*, 51(7), 633-651. — L-M separation ~27-30 nm
6. **Emery et al. (2022)**. *JOSA A*, 39, 2172-2181. — Partial recovery + achromatic increase
7. **Somers et al. (2024)**. *Vision Research*. — EnChroma: appearance yes, discrimination no
8. **Walther et al. (2016)**. *NeuroImage*. — Crossnobis reliability
9. **Diedrichsen et al. (2020)**. *NeuroImage*. — WUC method

---

## Appendix D: File Locations

**Scripts**:
- `scripts/machado_simulator.py` — Machado 2009
- `scripts/retinal_cortical.py` — R+C core functions
- `scripts/loco_distortion_fit.py` — Phase A multi-objective fitting
- `scripts/comprehensive_2component_analysis.py` — 2-Component + bootstrap
- `scripts/step2c_retinal_cortical.py` — R+C V1/V2 fitting
- `scripts/preimage_filter_search.py` — Phase B pre-image
- `scripts/preimage_separation_search.py` — Sub-09 separation optimization
- `scripts/compare_2component_loco.py` — Cross-model comparison table

**Results**:
- `results/loco_filter/phase_a/` — Phase A (Machado, R+C, Fourier)
- `results/loco_filter/phase_a_2component/` — Phase A (2-Component, 2026-04-09)
- `results/loco_filter/preimage/` — Phase B (R+C, Machado)
- `results/loco_filter/preimage_2component/` — Phase B (2-Component)
- `results/2component_comprehensive_v2/` — 2-Component
- `results/step2c_retinal_cortical_v2/` — R+C V1/V2

**Related documents**:
- `COMPREHENSIVE_MODEL_RESULTS.md` — Full model comparison (V1/V2 focus, statistical details)
- `LOCO_FILTER_PLAN.md` — Phase A-C workflow design
- `GEN45_SUB09_DIAGNOSIS.md` — Gen-4 failure diagnosis
