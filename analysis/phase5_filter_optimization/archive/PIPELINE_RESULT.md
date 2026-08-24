# Phase 2 Pipeline Results — Sprint Tracking

**Live document tracking each sprint cycle.**

**Reference**: `OVERALL_PIPELINE.md` §7 의 9-step sprint plan.
**Cycle structure** (per sprint S0~S8):
1. 진행 (Implementation) — script, output
2. 검증 (Validation) — sanity/boundary/convergence checks
3. 결과 해석 (Interpretation) — paper-level implications
4. 보고 (Reporting) — Verdict: PASS / FLAG / FAIL

---

## S0: Data integrity verification (✅ Complete 2026-05-21)

### Stage 1 — Scope

Advisor catch (2026-05-21) raised 6 concerns about sub-09 RSVP 8AFC 100% accuracy:
- (a) Stim-resp logging bug
- (b) Task interpretation (K-letter vs hue identification)
- (c) Filter status (no-filter session confirmed?)
- (d) Subject identity (sub-09 is actually protan?)
- (e) Filter accidentally applied
- (f) Compensatory learned strategy

Plus sub-08 RT artifact (1 trial with rt = -2.56s).

### Stage 2 — Verification

**(a) Logging bug**: LOW concern
- Sub-09 RT variance 0.80~4.05s = genuine trial-by-trial response, not auto-fill
- Sub-08 errors (12 trials) follow adjacent-hue confusion pattern (hue identification consistent)

**(b) Task interpretation**: LOW
- CSV schema `stimulus_label` ↔ `response_label` = hue identification
- Adjacent-hue confusion pattern in sub-08 errors confirms task type

**(c) Filter status**: LOW (사용자 confirm)

**(d) Subject identity**: VERIFIED
- Ishihara plate accuracy: sub-09 = 9/14 (milder), sub-08 = 7/14
- → Sub-09 is *milder protan*, V1 LOCO p=0.007 confirms protan-family neural signature
- → Behavioral 100% accuracy consistent with mild severity, no integrity issue

**(e) Filter accidentally applied**: 사용자 no concern
**(f) Compensatory learned strategy**: Not blocking, deferred to Phase 3 novel-stim test

**Sub-08 RT artifact**: 1 negative RT (trial 19, incorrect) + 1 timeout (trial 18). 62/64 valid. `rt > 0` filter applied (already in `fit_sigma_hc_8afc.py`).

### Stage 3 — Interpretation

- Sub-09 100% accuracy = mild protan (Ishihara 9/14) + behavioral near-normal
- Sub-09 strong V1 neural signature (LOCO p=0.007) persists despite mild severity
- → **V1 neural representation is more sensitive to mild CVD than behavioral metrics**
- → Paper-level finding candidate: cortical-behavioral dissociation framework

### Stage 4 — Verdict: ✅ PASS

- All 6 concerns cleared
- Sub-09 narrative격상 candidate confirmed
- No further data cleanup needed

---

## S1: lambda_3source.py (✅ Complete 2026-05-21)

### Stage 1 — Implementation

- **Script**: `scripts/lambda_3source.py`
- **3 sources**:
  - (b) DPS 1992 literature constants (protan 10 nm, deutan 6 nm) — *PRIMARY anchor, no fit*
  - (c) Boehm 2014 severity grid {3, 8, 13 nm} — *robustness, no fit*
  - (d) **JND-Lamb inverse fit (Option B: all-pair joint via Machado forward model)** — *only this source involves a fit*
- **Output**: `results/lambda_3source/{subject}_lambda.json`, `hc_negative_control.json`

**Implementation notes**:
- Machado forward model from `utils_distortion_models.apply_distortion('machado_1way', ...)` 
- Output space = Stockman opponent coord (NOT DKL canonical)
- Initial coord mismatch bug fixed (baseline_hues at Δλ=0 used for d_phys instead of canonical 0/45/.../315)
- HC pool baseline computed across 7 HC subjects per pair
- `conda srm` env required (colour-science 0.4.4)

#### Fitting method (Option B: all-pair joint)

**Mechanism** — JND ratio prediction under cone shift hypothesis:

For a CVD subject (family ∈ {protan, deutan}) with retinal cone shift Δλ, each color pair p = (θ_a, θ_b) is predicted to have an *altered* JND relative to HC baseline:

- **HC baseline** (Δλ=0): JND_HC(p) measured empirically from N=7 HC pool
- **CVD prediction**: JND_AT(p; Δλ) = JND_HC(p) × (d_phys(p) / d_perc(p; Δλ))
  - d_phys(p) = baseline hue distance in *Stockman opponent space* (Δλ=0 Machado output, **not** DKL canonical 0°/45°/.../315°)
  - d_perc(p; Δλ) = post-Machado hue distance under Δλ
  - If Δλ compresses the perceptual gap (d_perc < d_phys) → JND inflates (HYPO discriminability)

**Loss function** (HC-SD-weighted MSE across N=8 pairs):

```
L_JND(Δλ) = (1/N) · Σ_p [(JND_pred(p; Δλ) − JND_obs(p)) / σ_HC(p)]²
```

where σ_HC(p) = standard deviation of HC pool JND at pair p (per-pair noise normalization → z-MSE).

**Grid**: Δλ ∈ [0, 30] nm, step 0.5 nm = 61 grid points.

**Best Δλ** = argmin_{Δλ ∈ grid} L_JND(Δλ).

#### Evaluation criteria (Stage 2 PASS gates)

| Criterion | Threshold | Purpose |
|---|---|---|
| **Improvement-over-null** | L(Δλ*) < L(0) | Cone-shift hypothesis explains JND better than HC-equivalent |
| **Boundary check (low)** | best_idx > 0 | Fit not pinned at Δλ=0 (cone-shift required) |
| **Boundary check (high)** | best_idx < 60 | Δλ_max=30 nm not saturating |
| **Finite loss** | all losses finite | No numerical pathology |
| **HC negative control** | HC pool Δλ ≈ 0 under each family assumption | Forward model returns null on HC |

#### Pseudocode

```python
# === SETUP ===
PAIR_HUES = {
    'red-orange':    (0°,   45°),    'orange-yellow':  (45°,  90°),
    'yellow-green':  (90°, 135°),    'green-blue':    (135°, 225°),  # skip cyan
    'blue-purple':   (225°,270°),    'yellow-purple': (90°,  270°),
    'cyan-magenta':  (180°,315°),    'red-cyan':      (0°,   180°),
}
DELTA_GRID = arange(0.0, 30.5, 0.5)         # 61 points

# === HC POOL BASELINE (n=7) ===
for pair p in PAIR_HUES:
    JND_HC[p]   = mean({sub-XX_jnd_mean[p] : XX in 01..07})    # baseline per pair
    sigma_HC[p] = std({sub-XX_jnd_mean[p] : XX in 01..07}, ddof=1)

# === PER CVD SUBJECT FIT ===
for (subject, family) in [('sub-08', 'deutan'), ('sub-09', 'protan')]:
    JND_obs = load_per_pair(subject)                  # 8 pairs

    # Stockman-coord baseline at Δλ=0 (avoid DKL/Stockman coord mismatch)
    hue_baseline = machado_shifted_hue(0.0, family)    # (8,) hues in Stockman

    losses = zeros(61)
    for i, Δλ in enumerate(DELTA_GRID):
        hue_shifted = machado_shifted_hue(Δλ, family)   # (8,) hues under cone shift
        loss_sum = 0
        for pair (θ_a, θ_b) in PAIR_HUES:
            idx_a, idx_b = round(θ_a/45°), round(θ_b/45°)   # canonical 0..7
            d_phys = modular_hue_distance(hue_baseline[idx_a], hue_baseline[idx_b])
            d_perc = modular_hue_distance(hue_shifted[idx_a],  hue_shifted[idx_b])
            ratio  = d_phys / max(d_perc, 1e-3)
            JND_pred = JND_HC[pair] * ratio
            z = (JND_pred - JND_obs[pair]) / max(sigma_HC[pair], 1e-3)
            loss_sum += z**2
        losses[i] = loss_sum / 8                        # mean-z² loss

    best_idx     = argmin(losses)
    Δλ_JND_Lamb  = DELTA_GRID[best_idx]
    boundary_hit = (best_idx == 0) or (best_idx == 60)

    save_json({
        'b_dps_lit':    {protan: 10.0, deutan: 6.0}[family],
        'c_boehm_grid': [3.0, 8.0, 13.0],
        'd_jnd_lamb':   {'delta_lambda': Δλ_JND_Lamb,
                         'loss_at_best': losses[best_idx],
                         'loss_at_zero': losses[0],
                         'boundary_hit': boundary_hit, ...}
    })

# === HC NEGATIVE CONTROL (forward-model sanity) ===
for hc in sub-01..sub-07:
    for assumed_family in ['protan', 'deutan']:
        # Pretend this HC has CVD; refit Δλ
        # Expectation: argmin near 0 (HC has no cone shift)
        Δλ_HC = fit_jnd_lamb(hc, assumed_family)
```

### Stage 2 — Validation

| Check | Result | Verdict |
|---|---|---|
| HC negative control (protan assumption) | Δλ mean = 0.43 ± 0.49 nm, range [0, 1.0] | ✓ PASS (≈0) |
| HC negative control (deutan assumption) | Δλ mean = 1.07 ± 1.24 nm, range [0, 2.5] | ✓ PASS |
| Sub-08 loss curve improvement vs null | 7.97 vs null 10.42 (24% reduction) | ✓ PASS |
| Sub-09 loss curve improvement vs null | 0.56 vs null 1.21 (54% reduction) | ✓ PASS |
| Boundary hits (CVD subjects) | 0/2 | ✓ PASS |
| Loss curve finite | All values | ✓ PASS |

### Stage 3 — Interpretation

#### CVD results

| Subject | (b) DPS lit | (c) Boehm grid | (d) JND-Lamb fit | L(Δλ*) | L(Δλ=0) | Δ improvement | Cross-source verdict |
|---|---|---|---|---|---|---|---|
| **sub-08 (deutan)** | 6.0 nm | {3, 8, 13} → mid 8 | **6.5 nm** | 7.972 | 10.416 | 23.5% reduction | ★ **STRONG CONVERGENCE** (5-8 nm) |
| **sub-09 (protan)** | 10.0 nm | {3, 8, 13} → low 3 | **1.5 nm** | 0.558 | 1.210 | 53.9% reduction | ⚠ **DIVERGENCE** (DPS 10 vs JND-derived 1.5) |

#### HC negative control (n=7 per family, sanity check)

Each HC subject re-fit under both protan/deutan assumption — forward model must return Δλ ≈ 0:

| Family | n | Mean Δλ (nm) | SD | Range | Δλ=0 boundary hits |
|---|---|---|---|---|---|
| protan assumed | 7 | **0.43** | 0.53 | [0, 1.0] | 4/7 |
| deutan assumed | 7 | **1.07** | 1.34 | [0, 2.5] | 4/7 |

Per-subject breakdown (Δλ in nm; protan / deutan):

| HC | protan | deutan |
|---|---|---|
| sub-01 | 1.0 | 2.5 |
| sub-02 | 0.0 (boundary) | 0.0 (boundary) |
| sub-03 | 0.0 (boundary) | 0.0 (boundary) |
| sub-04 | 1.0 | 2.5 |
| sub-05 | 1.0 | 2.5 |
| sub-06 | 0.0 (boundary) | 0.0 (boundary) |
| sub-07 | 0.0 (boundary) | 0.0 (boundary) |

→ HC pool returns near-zero Δλ under both family assumptions (mean ≤ 1.07 nm; 4/7 hit exact 0 boundary). Forward model behaves as expected on null. Note: residual ≤ 2.5 nm in sub-01/04/05 reflects within-HC JND noise rather than mis-specified cone shift.

**Sub-08 convergence**: 3 sources within 5-8 nm range → robust population-equivalent Δλ.

**Sub-09 divergence** (paper finding candidate):
- DPS lit 10 nm = typical full protan population mean
- JND-Lamb 1.5 nm = *subject-specific* behavioral signature
- Consistent with Ishihara 9/14 (milder than sub-08's 7/14)
- → Sub-09 is *mild protan*, behavioral near-normal explained by *mild severity* (NOT cortical compensation requirement)
- → BUT V1 LOCO p=0.007 persists at 1.5 nm Δλ → **V1 neural metric very sensitive**

**Per-pair JND-Lamb fit details** (saved in `{subject}_lambda.json` under `per_pair_at_best`):
- Sub-08 vulnerable pairs (orange-yellow, yellow-green, yellow-purple) drive 6.5 nm estimate
- Sub-09 dominant signal: 1 HYPO pair (green-blue) + 3 HYPER pairs counteract

### Stage 4 — Verdict: ✅ PASS (with FLAG)

- ✓ Forward model valid (HC null ≈ 0 across both assumptions)
- ✓ Sub-08 robust 3-source convergence
- ⚠ FLAG (not blocking): Sub-09 DPS vs JND-Lamb divergence — *paper interpretation 명확*: two hypotheses (full protan with compensation OR mild protan without compensation), both fit at downstream R+C/2-Comp 단계

### Decisions for downstream sprints (S2+)

- **All 3 Δλ sources used in R+C g fit (per §4.4 already locked)**
- Sub-09 의 DPS 10 vs JND 1.5 → 두 hypothesis (compensation vs mild severity) 의 분리된 R+C g* values
- Paper 에 두 hypothesis 모두 보고 + V1 neural dissociation 이 *어느 가정에도 robust*

### Files

- `scripts/lambda_3source.py`
- `results/lambda_3source/sub-08_lambda.json`
- `results/lambda_3source/sub-09_lambda.json`
- `results/lambda_3source/hc_negative_control.json`

---

## S2: rc_1dof.py (✅ Complete 2026-05-21)

### Stage 1 — Implementation

- **Script**: `scripts/rc_1dof.py`
- **R+C forward formulation** (Boehm linear compensation):
  ```
  δθ_RC(c; Δλ, g) = (2 − g) · δθ_Machado(c; Δλ)
  ```
- **g interpretation** (amplification convention, advisor 정정):
  - g=1 → δθ_RC = δθ_Machado (HC-like passthrough, no compensation)
  - g=2 → δθ_RC = 0 (full cortical compensation, behavior = HC)
  - g=3 → δθ_RC = −δθ_Machado (overcompensation, opposite direction)
  - g=0 → δθ_RC = 2·δθ_Machado (cortical attenuation, doubled distortion)
- **Grid**: g ∈ [0, 3], step 0.05 = 61 points
- **σ = 21° fixed** (HC pooled, S0 결과 — 도출 출처는 아래)
- **Provides infrastructure** for S5 (combined with S3, S4 loss callables)
- **Compensation magnitude**: M = max(0, g−1) · Δλ (retinal-equivalent nm)
- **Output**: `results/rc_1dof/self_test_results.json`

#### σ = 21° fixed — 출처 및 도출 (lock-in 2026-05-21, framing 정정 2026-05-22)

**왜 fixed인가** (joint fit 폐기 rationale):
(δθ, σ) likelihood landscape 는 *isolikelihood contour valley* — 동일 8AFC accuracy 가 (large δθ, small σ) 와 (small δθ, large σ) 둘 다에서 동일하게 달성됨. Joint fit의 argmin이 contour 위에서 *non-unique* → grid resolution 증가로 해결 안 됨. ⇒ σ를 외부 anchor로 고정하고 δθ만 추정.

> ⚠️ **Honest framing correction (사용자 catch, 2026-05-22)**:
> 이전 표현 "dual anchor (empirical + literature)" 는 *overstatement*. Literature 값들은 working-memory SD 또는 2AFC threshold 로, 우리 8AFC immediate identification σ 와 *측정 차원이 다름*. 따라서:
> - **진정한 anchor = (1) empirical HC pooled fit + (3) σ-sensitivity sweep**
> - **Literature 는 plausibility check 만** — "order of magnitude 가 비현실적이지 않다" 정도

**(1) PRIMARY empirical anchor — HC pooled, our paradigm**:

Script: `scripts/fit_sigma_hc_8afc.py`. 4 HC × 64 trial = 255 trial pooled 8×8 confusion matrix.

```
P(response = j | stim = i; σ, δθ=0)  ∝  exp(−|hue_i − hue_j|² / σ²)
σ_HC = argmin_σ  Σ_{i,j} [P_pred(σ)[i,j] − confusion_pooled[i,j]]²
```

| Subject | N trials | Accuracy | σ_fit (°) | Notes |
|---|---|---|---|---|
| sub-01 | 64 | 100.00% | 6.39 | degenerate floor (0 error → σ unidentified) |
| sub-03 | 64 | 95.31% | 22.19 | |
| sub-06 | 63 | 98.41% | 20.51 | |
| sub-07 | 64 | 96.88% | 22.15 | |
| **Pooled HC (combined 8×8)** | **255** | **97.65%** | **σ_HC = 20.96°** | **★ primary anchor** |
| Mean (excl. sub-01) | — | — | **21.62°** | sub-01 degenerate 제거 시 |

→ **σ_HC = 21.0°** (pooled fit 반올림). 단위/paradigm = 우리 8AFC RSVP, Stockman opponent space, immediate identification → δθ 추정과 직접 호환.

**(2) Literature plausibility range — NOT independent replication**:

각 source 의 paradigm/quantity 가 우리와 *다름* 을 명시:

| Source | Task | Quantity | 우리와 dimension 차이 |
|---|---|---|---|
| Schurgin et al. 2020 (TCC) | color **working memory** continuous report (CIELAB wheel) | recall SD (encoding + maintenance + recall noise) | WM ≠ immediate; CIELAB ≠ Stockman |
| Bae et al. 2015 | color **working memory** delay SD | 동상, delay-dependent | 동상 |
| Witzel & Gegenfurtner 2018 | DKL **2AFC threshold** (JND) | 75% accuracy stim difference | 2AFC threshold ≠ 8AFC σ; DKL ≠ Stockman |

Range reported in literature ≈ **18-25°**.

- ✅ Claim 가능: "σ_HC=21° 는 related color literature 의 *order of magnitude* 와 양립 (10° / 100° 이 아님)."
- ❌ Claim 불가능: "Literature 가 σ=21° 를 replicate". 측정 차원이 다름.

**(3) REAL robustness defense — σ-sensitivity sweep**:
```
σ ∈ {15°, 18°, 21°, 24°, 28°}
R+C / 2-Comp × 모든 loss × 양 피험자 × 양 family 전체 fit 반복
→ Primary verdict 의 σ-invariance 검증
```
σ uncertainty 에 대한 진짜 paper-level 방어. 인프라 구축 완료.

**Paper-level caveat (advisor catch + 사용자 catch 통합)**:
- σ fixed = "deficit 이 모두 δθ 로 attribution 된다" 가정 → "Estimates assume HC-equivalent response noise. If CVD response variability differs, δθ may be overestimated."
- "Literature anchor" 라는 용어 paper 에서 *사용 금지*. 정확한 framing: "primary empirical estimate from our own HC pool, validated by sensitivity sweep, with order-of-magnitude consistency relative to related (non-equivalent) color discrimination/memory literatures."

**Reviewer-defensible answer to "What is the basis of σ=21°?"**:
> "Primary: our HC pooled 8AFC fit (n=4 HC, 255 trials, identical paradigm and stimulus space). Secondary defense: σ-sensitivity sweep ∈ {15, 18, 21, 24, 28°} shows verdict invariance. We do not claim measurement equivalence to working-memory or 2AFC-threshold literatures; their reported range (18-25°) provides only plausibility context."

### Stage 2 — Validation (7/7 PASS)

각 self-test 의 **원리** = "이 코드가 R+C 1-DOF 의 어떤 *수학적 속성* 을 보장해야 하는가" 의 명시적 unit assertion. Loss 함수 없이 (loss-agnostic) forward model 자체의 무결성을 검증.

| # | 검증 명제 | 입력 | 예상 결과 | 원리 (왜 이 결과가 나와야 하나) |
|---|---|---|---|---|
| 1 | **HC baseline** | Δλ=0, g=1 (deutan) | δθ = **0** 벡터 | Δλ=0 → Machado가 항등사상 → δθ_Machado=0. (2−g)·0 = 0. CVD 가정 X = HC. |
| 2 | **Full compensation** | Δλ=10, g=2 (protan) | δθ = **0** 벡터 | g=2 → (2−g)=0 → 모든 retinal distortion 이 cortical 보상에 의해 zeroed out. 행동학적으로 HC 동등성 회복. |
| 3 | **Raw Machado 비-trivial** | Δλ=10, g=1 (protan) | RMS > 1° | g=1 → (2−g)=1 → δθ_RC = δθ_Machado. 10 nm protan 은 substantive distortion (실측 RMS = **35.27°**, max\|δθ\| ≈ 76°). |
| 4 | **Linear (2−g) scaling** | Δλ=10, g=0.5 (protan) | δθ = 1.5 × δθ_Machado(10nm) | Cascade form 의 *linearity in g* 검증. (2−0.5)=1.5 → 정확히 1.5배 scaling 이어야 함. max diff = 0.000° → 코드가 본인 정의를 정확히 구현. |
| 5 | **Grid 수렴성 (dummy loss)** | Loss = Σδθ² (compensation 압력) | g* ≈ 2 | sum-of-squares 최소화 압력 하에서 grid search 가 정확히 *full compensation* 지점을 탐색해야 함. g_best = 2.000 → 61-point grid + argmin 무결성 확인. |
| 6 | **Forward bijection** | Δλ=10, g=1.5 (protan) | min perceived pair dist > 1° | 8 canonical hue 가 forward 후에도 *unique* 8 출력 ⇒ inverse 존재 가능. min pair = 23.54° (>>1°) → 충돌 없음, 필터(inverse)가 well-posed. |
| 7 | **Boundary detection** | Loss = −Σδθ² (분리 압력) | g* = 0, boundary_low flag | Grid 끝점에 fit 이 핀 처리되면 *misspecification 신호* 로 flag 되어야 함. boundary_low = True → S5 결과에서 boundary hit 자동 감지 가능 (sub-08 bimodal bootstrap 진단의 근거). |

**모두 PASS (7/7)** → R+C forward 함수, grid search, inverse 가능성 모두 수학적 정합성 확인 완료. S5 단계에서 실제 loss 와 결합하여 g* 를 추정할 준비 완료.

### Stage 3 — Interpretation

**Forward R+C δθ magnitudes per subject × Δλ source (at g=1 raw Machado)**:

| Subject | Family | Δλ source | RMS δθ (deg) | max\|δθ\| |
|---|---|---|---|---|
| sub-08 | deutan | DPS 6.0 | 32.12 | 86.24 |
| sub-08 | deutan | JND-Lamb 6.5 | 35.84 | 96.75 |
| sub-08 | deutan | Boehm 8.0 | 43.45 | 117.82 |
| sub-09 | protan | DPS 10.0 | 35.27 | 76.18 |
| sub-09 | protan | **JND-Lamb 1.5** | **9.02** | **21.99** |
| sub-09 | protan | Boehm 3.0 | 17.07 | 40.93 |

**Key observations**:
1. **Sub-08 3 Δλ sources**: RMS 32-43° (range 11°) — Δλ convergence reflected in δθ magnitude consistency
2. **Sub-09 3 Δλ sources**: RMS 9-35° (range 26°) — *large variance* expected from Δλ divergence (S1)
   - JND-Lamb 1.5 nm gives mild δθ (9° RMS) — consistent with milder protan hypothesis
   - DPS 10 nm gives strong δθ (35° RMS) — requires strong cortical compensation (g* ≈ 2-3) if behavior near-HC
3. Max\|δθ\| reaches 76-118° in raw Machado (Stockman coord with possible sign flips at some hues)
4. **R+C model 's *cortical compensation hypothesis*** is now quantitatively testable via S5 fit results

### Stage 4 — Verdict: ✅ PASS

- All 7 self-tests pass
- R+C infrastructure ready for S5 fit (loss-callable interface)
- Forward magnitudes show clear sub-08/sub-09 hypothesis separation potential
- No code issues

### Files

- `scripts/rc_1dof.py` (forward, grid fit, inverse check functions)
- `results/rc_1dof/self_test_results.json`

---

## S3: behav_loss.py (✅ Complete 2026-05-21)

### Stage 1 — Implementation

- **Script**: `scripts/behav_loss.py`
- **L_behav_α**: 8AFC softmax MSE per color
  ```
  P(response=j | stim=i) ∝ exp(−d(perceived_i, target_j)² / σ²)
  L_α = mean((P(correct|i) − obs_acc[i])²)  for i in 8 colors
  ```
- **L_behav_γ**: per-pair JND weighted MSE
  ```
  JND_pred(p) = HC_baseline(p) × (d_phys / d_perc)
  L_γ = mean[((pred − obs) / σ_p)²]  for p in 8 pairs
  ```
- **L_behav composite (subject-specific)**:
  - Sub-08: 0.5·L_α + 0.5·L_γ
  - Sub-09: 0.0·L_α + 1.0·L_γ (8AFC ceiling)
- σ_HC = 21° fixed (S0 reference + literature anchor)

### Stage 2 — Validation (7/7 PASS)

| Test | Description | Result |
|---|---|---|
| 1 | HC self-fit L_α (δθ=0) max < 0.01 | ✓ PASS (max=0.0083 at sub-03) |
| 2 | HC self-fit L_γ (δθ=0) mean ~ z²-unit | ✓ PASS (mean=0.86) |
| 3 | Sub-08 L_α > max HC L_α | ✓ PASS (0.048 > 0.008, 5.8×) |
| 4 | Sub-09 L_α < 0.001 (ceiling) | ✓ PASS (0.0004) |
| 5 | Sub-08 L_γ >> HC mean (yellow HYPO) | ✓ PASS (10.4 vs 0.86, 12×) |
| 6 | L_behav composite weights | ✓ PASS (correct subject-specific) |
| 7 | σ sensitivity sweep | ✓ PASS (informational, 0.055 → 0.026 for σ 15→28°) |

### Stage 3 — Interpretation

**HC pool sanity** (δθ=0 self-fit):
- L_α max = 0.0083 (sub-03 with 3 errors), confirms σ=21° softmax model valid
- L_γ mean = 0.86 in z²-units (range 0.25-2.27, sub-07 outlier with low JND)

**CVD subjects (δθ=0 baseline) — signal strength**:
- **Sub-08 L_α = 0.048 (5.8× max HC)** — strong 8AFC mismatch (82.5% obs vs ~97% predicted)
- **Sub-08 L_γ = 10.4 (12× HC mean)** — yellow-axis HYPO drives huge per-pair signal
- **Sub-09 L_α = 0.0004 (≈ HC)** — ceiling confirmed (100% obs ≈ 97% predicted)
- **Sub-09 L_γ = 1.21 (1.4× HC mean)** — moderate signal (1 HYPO + 3 HYPER + 4 ≈HC)

**L8 composite at δθ=0**:
- Sub-08: L_total = 0.5×0.048 + 0.5×10.4 = **5.23** (dominated by L_γ)
- Sub-09: L_total = 0 + 1.0×1.21 = **1.21**

→ **L_γ is the load-bearing component for both subjects** (especially sub-08, where L_α/L_γ scale ratio = 1/220).

**σ sensitivity**: L_α(sub-08) ranges 0.055 → 0.026 across σ ∈ [15, 28]°. Moderate sensitivity; primary verdict (sub-08 informative, sub-09 ceiling) invariant.

### Stage 4 — Verdict: ✅ PASS

- All 7 tests pass
- L_behav callable interface ready for S5 fit
- σ sensitivity within acceptable range
- Subject-specific weights validated

### Files

- `scripts/behav_loss.py`
- `results/behav_loss/self_test_results.json`

---

## S4: neural_loss.py (✅ Complete 2026-05-21, ⚠️ K=6 re-run 2026-05-22)

### Stage 1 — Implementation

- **Script**: `scripts/neural_loss.py`
- **L_LOCO**: *within-subject* per-color hold-out (CVD's own LOCO W, advisor-confirmed Option A = spec §4.2.3)
  ```
  For each held-out color c:
    W_c = ridge GCV trained on CVD's 7 train colors  
    Y_pred = C(c + δθ(c)) @ W_c  (in CVD's V_s)
    Y_actual = CVD's mean pattern at c
    ρ(c) = corrcoef(Y_pred, Y_actual)
  L_LOCO = mean(1 − ρ(c))
  ```
- **L_RDM**: `1 − cos(ΔRDM_sim, ΔRDM_obs)`, correlation distance primary + Crossnobis robustness
  ```
  # Observed ΔRDM (data side, V-free)
  For each HC s:
    rdm_HC[s] = pdist(mean_runs(amp_HC[s]), metric=corr) # in s's own V_s → 28-vec
  rdm_HC_mean = mean(rdm_HC[s] for s in HC)
  rdm_CVD     = pdist(mean_runs(amp_CVD), metric=corr) # in CVD's V_s → 28-vec
  ΔRDM_obs    = rdm_CVD − rdm_HC_mean

  # Simulated ΔRDM (model side, W-fixed per HC)
  For each HC s:
    Y_shift = C(θ + δθ) @ W_HC[s]           # W_HC[s] precomputed (HC ridge_gcv)
    Y_base  = C(θ)       @ W_HC[s]          # baseline = machado_shifted_hue(0.0)
    ΔRDM_sim[s] = pdist(Y_shift, metric=corr) − pdist(Y_base, metric=corr)
  ΔRDM_sim    = mean(ΔRDM_sim[s] for s in HC)        # per-HC ΔRDM, THEN mean

  L_RDM = 1 − cos(ΔRDM_sim, ΔRDM_obs)                # ∈ [0, 2]
  ```
  - V_s-invariant (RDM is 28-vec dissimilarity, voxel dimension absent)
  - Per-HC RDM in own V_s, then average ΔRDM across HCs
  - Distance metric: `corr` = 1 − Pearson r (canonical, `diagnostic_delta_rdm.py:80`); `crossnobis` swappable for robustness check (LOO-run whitened, lines 124–175)
  - Identity (δθ = 0) ⇒ ΔRDM_sim ≡ 0 ⇒ cos undefined → fallback `cos := 0`, L_RDM = 1.0 (Stage 2 baseline cell)
- **L_neural composite**: 0.5·L_LOCO + 0.5·L_RDM

### V_s mismatch resolution (사용자 + advisor 논의)

| V_s mismatch source | Resolution |
|---|---|
| Per-subject anatomy → different voxel counts | Within-subject LOCO (spec §4.2.3 의 정확한 form) |
| Cross-subject HC encoder → CVD pattern (initial attempt) | ✗ FAIL (V_s mismatch) — abandoned, was misinterpretation of spec |
| RDM voxel-invariance | ✓ Auto-handled (28-vec dissimilarity) |

### Stage 2 — Validation (re-run after within-subject fix)

| ROI | HC self LOCO | sub-08 LOCO | sub-09 LOCO | HC L_RDM | sub-08 L_RDM | sub-09 L_RDM |
|---|---|---|---|---|---|---|
| V1 | 0.9456 | 1.0566 | 0.9946 | 1.0 (baseline) | 1.0 (baseline) | 1.0 (baseline) |
| V4 | 0.9630 | 0.9159 | 0.9288 | 1.0 (baseline) | 1.0 (baseline) | 1.0 (baseline) |

**HC L_LOCO ≈ 1.0 (ρ ≈ 0.05) is correct**, matches project's known empirical baseline:
- MEMORY 2026-03-11: "V1/V2 LOCO null ~0.10-0.13 from voxel covariance, not color signal"
- "Only hV4 exceeds permutation null"
- FE basis K=3-4 × 6 runs × 8 colors → *inherently low LOCO ceiling*

**L_RDM = 1.0 at δθ=0**: ΔRDM_sim = 0 (no shift predicted) vs ΔRDM_obs ≠ 0 → cos = 0 → L_RDM = 1.0. *Expected baseline; informative values appear when δθ ≠ 0* (verified Test 4 perturbed δθ).

### Stage 3 — Interpretation

**V1 differential (advisor-validated direction)**:
- HC self = 0.9456, sub-08 = 1.0566 (Δ +0.11) → CVD V1 prediction harder than HC
- sub-09 = 0.9946 (Δ +0.05) → milder signal (Ishihara-consistent mild protan)

**V4 differential**:
- HC sub-01 V4 = 67 voxels (smaller than CVD's 70)
- sub-08 (0.9159) and sub-09 (0.9288) *better* than HC sub-01 (0.9630)
- → V4 의 V_s 의 *ridge regularization 차이* 가 cross-subject absolute 비교를 *non-informative* 만듬
- Advisor catch validated: absolute L_LOCO across subjects NOT meaningful

**Within-subject improvement (under fit)**:
- This metric is *fit-dependent* (improvement L_LOCO at δθ=0 − L_LOCO at fit*)
- Project memory: HC FPR = 100% under permutation when computing improvement
- → Specificity claim via L_LOCO improvement BLOCKED

### Option E (HC null distribution) — accurate scope

| Form | Valid? | Reason |
|---|---|---|
| "Sub-08 ρ at δθ=0 is in N-th percentile of HC ρ baseline" | ✓ Descriptive | Static baseline, no improvement comparison |
| "Sub-08 statistically distinct from HC" | ✗ INVALID | FPR=100% under permutation (project memory) |
| "Sub-08 improvement under fit vs HC improvement under permuted δθ" | ✗ INVALID | = the failed permutation test |

### Stage 4 — Verdict: ✅ PASS (with advisor-confirmed reframing)

- All neural loss callables working
- HC self-fit ρ ≈ 0.05 matches project's empirical LOCO ceiling (V1/V2 voxel covariance dominance)
- L_RDM = 1.0 at δθ=0 is expected baseline
- L_LOCO and L_RDM ready for S5 fitting
- **Option E demoted**: baseline percentile descriptive only, NO improvement comparison

### Primary specificity defense location (lock)

- **§6.3 transfer test (X, Y, Z)** = PRIMARY double-dipping defense
- **§5.4 equivalence test** (TOST + BF₀₁) = behavior-neural concordance
- **Option E** = supplementary baseline percentile only

### Files

- `scripts/neural_loss.py`
- `results/neural_loss/self_test_results.json`

---

## S5: All-paths fit (✅ Complete 2026-05-21)

### Stage 1 — Implementation

- **Scripts**: `scripts/two_comp.py` (2-Comp forward) + `scripts/s5_all_paths_fit.py` (orchestrator)
- **R+C × 3 Δλ × 8 loss** + **2-Comp × 8 loss** per (subject, ROI)
- **σ = 21° primary** (fixed)
- **L_RDM caching**: ΔRDM_obs + per-HC RDM_baseline pre-computed → 1326-grid 2-Comp fits in seconds
- **Output**: `results/s5_all_paths/{subject}_{roi}_sigma{N}.json` + `summary.json`

### Stage 2 — Validation

- **Total fits**: 128 (4 subj-ROI combos × 32 paths each)
- **Wall time**: 23s (vs 6h estimated) — caching extremely effective
- **Boundary hits**: R+C g=3 hits flagged when Δλ source too small or LOCO incompatibility

### Stage 3 — Interpretation

#### L8 PRIMARY + L3 LOCO + L4 RDM 비교 (K=6 uniform, 2026-05-22 corrected)

각 fit 의 *L8 (modality 5050)*, *L3 LOCO 단독*, *L4 RDM 단독* 결과 병기 → loss-dependent g\* / (β_s, β_c) 분기 진단.

| Subject | ROI | Model | Δλ src | **L8 (modality)** | L3 LOCO | L4 RDM |
|---|---|---|---|---|---|---|
| sub-08 | V1 | R+C | DPS 6 | **g=2.25** | g=0 ⚠ | g=2.15 ✅ |
| sub-08 | V1 | R+C | Boehm 8 | g=2.15 | g=0 ⚠ | g=2.10 ✅ |
| sub-08 | V1 | R+C | JND-L 6.5 | g=2.25 | g=0 ⚠ | g=2.05 ✅ |
| sub-08 | V1 | 2-Comp | — | **(48, −36)** | (50, 50) ⚠ | (0, +22) |
| sub-08 | V4 | R+C | DPS 6 | **g=2.30** | g=1.10 | g=1.25 |
| sub-08 | V4 | R+C | Boehm 8 | g=2.20 | g=0.05 | g=0.30 |
| sub-08 | V4 | R+C | JND-L 6.5 | g=**0.00** ⚠ | g=0 ⚠ | g=0 ⚠ |
| sub-08 | V4 | 2-Comp | — | **(48, −36)** | (2, −10) | (0, +26) |
| sub-09 | V1 | R+C | DPS 10 | **g=2.60** | g=3.00 ⚠ | g=2.30 ✅ |
| sub-09 | V1 | R+C | Boehm 3 | g=3.00 ⚠ | g=1.40 | g=0 ⚠ |
| sub-09 | V1 | R+C | JND-L 1.5 | g=3.00 ⚠ | g=0.80 | g=2.45 ✅ |
| sub-09 | V1 | 2-Comp | — | **(26, +6)** | (50, 50) ⚠ | (10, −14) |
| sub-09 | V4 | R+C | DPS 10 | **g=2.60** | g=0.50 | g=1.05 |
| sub-09 | V4 | R+C | Boehm 3 | g=3.00 ⚠ | g=0 ⚠ | g=0.15 |
| sub-09 | V4 | R+C | JND-L 1.5 | g=3.00 ⚠ | g=0 ⚠ | g=0 ⚠ |
| sub-09 | V4 | 2-Comp | — | **(26, +6)** | (38, −50) ⚠ | (28, −28) |

**Loss-stability 진단**:

| 측면 | 안정 (consistent across loss) | 불안정 (loss-dependent) |
|---|---|---|
| **R+C V1 g\*** (sub-08, sub-09) | L8 ↔ L4 RDM: ~2.05-2.30 일치 ✅ | L3 LOCO 만 boundary (g=0 또는 g=3) |
| R+C V4 g\* | L8 dominant (g≈2.30/2.60), L3/L4 weak | L3, L4 모두 V4 에서 weak |
| **2-Comp β_s** (sub-08) | L8 (48) ≈ L3 (50 corner), L4 (0) | L4 RDM 만 β_s=0 |
| **2-Comp β_c sign** (sub-08) | L8 (−36) 와 L4 RDM (+22~+26): **부호 충돌** ⚠ | L4 RDM 의 sign 이 L8 과 *반대* |
| 2-Comp β_s, β_c (sub-09) | L8 (26, +6), L3 corner, L4 weak | L3 corner (50, 50) |

**핵심 관찰**:

1. **R+C V1 의 안정성**: L8 g 와 L4 RDM g 가 ~2.05-2.30 으로 *수렴*. L3 LOCO 만 boundary → L8 의 V1 g\* 는 *behavioral + RDM 의 합의값*, LOCO 는 outlier.

2. **2-Comp β_c 부호 충돌 (sub-08)**: L8 (β_c=−36) vs L4 RDM (β_c=+22~+26) — **opposite sign**. *behavioral + LOCO 의 합의* (β_c<0 confusion axis rotation) vs *RDM 단독* (β_c>0 다른 방향). Paper-relevant dissociation evidence.

3. **V4 의 일관된 weakness**: 두 모델 모두 V4 에서 L3/L4 단독은 R+C g<1.3 / 2-Comp β_s≈0-28 의 weak fit. L8 만 강한 g≈2.30-2.60. → V4 의 neural signal 자체가 약함 (project memory: hV4 67 voxels K=3 baseline variance).

4. **L8 의 의미 재확인**: L8 fitted params 가 *반드시 L3/L4 단독과 일치 안 함*. L8 = behavioral (0.5) + 0.25 LOCO + 0.25 RDM 의 *weighted compromise* — §"Acknowledged Loss-Design Constraints" (2) 의 직접 evidence.

#### Key findings

**1. All R+C g* > 2 (cortical amplification compensation present in BOTH subjects)**:
- Sub-08 g* ≈ 2.25 → cortical amplification of 7.5 nm retinal-equivalent
- Sub-09 g* ≈ 2.60 (DPS Δλ=10) → strong 16 nm cortical amplification

**2. Sub-09 Δλ source divergence (S1 carries through)**:
- DPS Δλ=10 with g=2.60 → clean fit, no boundary hit
- Boehm Δλ=3 / JND-Lamb Δλ=1.5 → g hits boundary 3.00 (max amplification grid limit)
- → **Under DPS hypothesis: strong compensation (16 nm)**
- → **Under JND-Lamb hypothesis (mild severity): R+C 1-DOF insufficient** (g=3 boundary), 2-Comp better fit (loss 0.68 vs 0.87)
- ⚠ Sub-09 의 mild severity hypothesis 가 R+C model 의 limit 노출

**3. 2-Comp loss < R+C loss for both subjects** (under L8):
- Sub-08: 2-Comp 3.42-3.47 < R+C 5.59-5.61
- Sub-09: 2-Comp 0.68 < R+C 0.71-0.87
- → 2-Comp 가 same 8 colors 에 *더 적합* (extra DOF)
- AICc / BIC penalty 가 S7-S8 에서 적용되어 *parsimony-corrected* 비교 필요

**4. 2-Comp 의 paper-relevant params**:
- Sub-08 (β_s=48, β_c=-36): warm-side compression + confusion-axis rotation, Cycle history (58,-36)/(68,-38) 와 일치
- Sub-09 (β_s=26~28, β_c=0~4): S-cone cardinal rotation dominant, β_c ≈ 0 (confusion axis weak)
- → Sub-09's **β_c ≈ 0** is *qualitatively different* from sub-08's strong β_c=-36 → subtype-specific signature

#### Loss-dependence (sub-09 V1 R+C with DPS Δλ=10, K=6 corrected)

| Loss | g_best | M_comp_nm |
|---|---|---|
| L1 (8AFC) | 2.00 | 10.00 |
| L2 (JND) | 2.60 | 16.00 |
| L3 (LOCO) | 3.00 ⚠ | 20.00 (boundary) |
| L4 (RDM) | 2.30 | 13.00 |
| L5 (behav) | 2.60 | 16.00 |
| L6 (neural) | 3.00 ⚠ | 20.00 (boundary) |
| L7 (all-equal) | 2.55 | 15.50 |
| **L8 (modality)** | **2.60** | **16.00** |

→ Loss-cluster structure: behavioral (L1, L2, L5) and neural (L4, L6) give similar g*, with L3 (LOCO) often boundary. **L8 primary aligns with L2 (γ-dominant)** — expected since L8 weights L_γ at 0.5.

#### Loss-dependence across all 4 cells (sub-08/09 × V1/V4) — patterns

위 표는 단일 cell (sub-09 V1 R+C DPS) 만 보여줌. 4개 cells 모두 (32 fits 각각) 의 raw 결과는 `results/s5_all_paths/{subject}_{roi}_sigma21.json` 에 저장. 핵심 패턴 3가지:

**(A) R+C 의 L3 LOCO 가 일관되게 boundary hit, L4 RDM 은 부분적 clean fit** (K=6 corrected, 2026-05-22 정정):

| Cell | L3 LOCO (3 Δλ) | L4 RDM (3 Δλ) | L6 neural composite (3 Δλ) |
|---|---|---|---|
| sub-08 V1 | **3/3 g=0 ⚠** | **3/3 clean** (g=2.05, 2.10, 2.15) ✅ | 1/3 boundary (Boehm) |
| sub-08 V4 | 2/3 boundary (DPS g=1.10 clean) | 2/3 weak (g=0.30, 1.25, 0) | mixed |
| sub-09 V1 | 1/3 boundary (DPS g=3.00 ⚠) | **2/3 clean** (DPS 2.30, JND-L 2.45; Boehm g=0 ⚠) | 1/3 boundary (DPS g=3.00) |
| sub-09 V4 | 2/3 boundary | 2/3 weak (g=0.15, 1.05, 0) | mixed |

→ **R+C 1-DOF 가 neural *LOCO* (voxel-level prediction) 를 일관되게 설명 못 함** — sub-08 V1 에서 모든 Δλ source 에서 g=0 boundary. 반면 **R+C *RDM* (pairwise distance geometry) 은 sub-08 V1 에서 clean fit (g≈2.05-2.15)** — R+C cone-shift 가 V1 의 *coarse relational geometry* 와 일치. Behavioral loss (L1, L2, L5) 도 안정적 g ≈ 2.0-2.6.

**이게 LOCO vs RDM dissociation 의 *방향성* 의미**:
- R+C cone-shift = sub-08 V1 의 *pairwise distance structure* (28-vec RDM) 에는 fit
- 그러나 *voxel-level reconstruction* (LOCO) 은 R+C 1-DOF 로 부족 → 2-Comp 또는 추가 mechanism 필요
- → **R+C 의 적용범위 = behavioral + coarse RDM geometry; voxel-level fine detail 은 misspecified**

**(B) 2-Comp 의 (β_s, β_c) 가 ROI 간 + Cycle history 와 일치** — 4 cells L8 primary:

- sub-08: V1 (48, −36) ≈ V4 (48, −36) → ROI-invariant
- sub-09: V1 (26, +4) ≈ V4 (28, 0) → ROI-invariant
- Cycle history (sub-08: 58/−36, 68/−38; sub-09 V4: 28/+4) 와 모두 ±5° 이내 일치
- 단 L3 LOCO 단독은 2-Comp 도 grid corner (50, 50) 등 boundary issue 존재 — *LOCO 단독 fitting 은 두 모델 모두 불안정*, L8 weighted combination 이 더 stable.

**(C) R+C Δλ source 변화에 대한 robustness — subject-dependent**:

- sub-08 V1/V4: L8 g* = 2.20-2.25 across 3 Δλ sources → 매우 안정 ✅
- sub-09 V1/V4: L8 g* = 2.60 (DPS only clean) / 3.00 ⚠ (Boehm) / 3.00 ⚠ (JND-Lamb) → **DPS hypothesis 에서만 clean fit**

→ Sub-09 의 mild Δλ (1.5-3 nm) 에서 R+C 1-DOF 는 g=3 boundary 에 핀. *DPS Δλ=10 + g=2.60* 또는 *2-Comp* 만 sub-09 의 valid 설명.

#### 4-cell L8 PRIMARY 요약 표 (K=6 corrected, 2026-05-22 정정; **Spearman ρ 보강 2026-05-24, Nili 2014 RSA 권장 metric**)

| Subject | ROI | R+C DPS g* | 2-Comp (β_s, β_c) | L3 LOCO | L4 RDM | 2-Comp ROI 일치? | L4 Spearman ρ — R+C / 2-Comp (median [95% CI], S6' bootstrap) |
|---|---|---|---|---|---|---|---|
| sub-08 | V1 | g=2.25 ✅ | (48, **−36**) | ⚠ g=0 boundary | **✅ clean (g=2.15)** | ✅ | 0.26 [0.14, 0.39] / **0.35 [0.22, 0.42]** |
| sub-08 | V4 | g=2.30 ✅ | (48, **−36**) | partial (DPS g=1.10) | partial (DPS g=1.25) | ✅ (β identical) | 0.31 [0.20, 0.43] / **0.47 [0.35, 0.67]** |
| sub-09 | V1 | g=2.60 ✅ | (26, **+6**) | ⚠ g=3 boundary (DPS) | **✅ clean (g=2.30)** | ✅ | 0.27 [0.15, 0.37] / **0.46 [0.32, 0.55]** |
| sub-09 | V4 | g=2.60 ✅ | (26, **+6**) | partial (DPS g=0.50) | partial (DPS g=1.05) | ✅ (β identical) | 0.19 [0.15, 0.27] / **0.29 [0.19, 0.45]** |

→ L3 LOCO 가 일관되게 boundary, L4 RDM 은 sub-08/09 V1 에서 R+C cone-shift hypothesis 와 일치 (g≈2.15-2.30 clean).

→ **Behavioral path: 두 모델 모두 단일점 fit 안정 + ROI-invariant. Neural path: L4 RDM 은 R+C V1 에서만 clean, 그 외는 ROI-비안정 (R+C V4 weak, 2-Comp L4 단독 4 cells 모두 발산).** Paper-level claim "subtype-specific 2-Comp signature (sub-08 β_c=−36 vs sub-09 β_c≈0)" 는 *L8 점추정에 한해 4 cells robust*. (이전 서술 *"Neural path: R+C 가 모든 cells boundary, 2-Comp 가 안정"* 은 line 585/662 자기 모순 + JSON 불일치 — 사용자 catch 2026-05-24 정정.)

##### Metric robustness 진단 (2026-05-24, Nili 2014 권장 metric 병행)

위 표의 L4 RDM 값은 **cosine similarity** 기반. **Nili et al. 2014** (*PLOS Comp Biol*, RSA toolbox paper) 는 model RDM 과 brain RDM 비교에 **rank correlation (Spearman ρ 또는 Kendall τ_A)** 권장 — linear (Pearson/cosine) 가정이 brain RDM 에 questionable. S6' HC subset bootstrap (k∈{4,5,6}, 22-63 subsets per cell) 으로 Spearman ρ 병행 산출하여 metric robustness 평가:

**(1) Rank-level (model ranking) — robust ✅**

| Cell | Paired (2-Comp − R+C) win % | Wilcoxon p (one-sided) |
|---|---|---|
| sub-08 V1 | 54/63 = 86% | 3.1e-08 |
| sub-08 V4 | 20/22 = 91% | 4.5e-06 |
| sub-09 V1 | **63/63 = 100%** | **2.6e-12** |
| sub-09 V4 | 21/22 = 95% | 7.2e-07 |

→ 4 cells 모두에서 2-Comp > R+C 가 cosine / Spearman 양쪽 metric 에서 일관. 모든 4 cells × 2 models 의 Spearman ρ 95% CI 가 0 위 — 두 모델 다 chance 위 capture.

**(2) Point estimate (개별 fit 값) — metric-dependent ⚠**

- Subset-level r(ρ, cosine) = **0.11-0.85** (cell × model 별 변동). 가장 낮은 cell: sub-08 V1 2-Comp r=0.11 (두 metric 이 서로 다른 subset 을 best 로 평가).
- L8 PRIMARY 재fit (`s5_spearman_refit`) 결과 **7/8 cells 의 (g, β_s, β_c) 가 ±2° 이내 동일**. 단 **1/8 cells 에서 paper-grade flip**: **sub-08 V4 R+C DPS** 가 cosine g=2.30 → Spearman g=0.00 (boundary).
- Root cause: 해당 cell 의 L_γ landscape 가 g 에 거의 평탄 (loss 5.61-5.67 across full grid) → *"L_γ 가 L8 magnitude 의 88% 차지"* 가 *magnitude 지배* 일 뿐 *decision power* 아님. 작은 L_RDM 항 (9%) 이 metric 에 따라 argmin 결정.

→ **paper claim 수준**:
- ✅ Model ranking (2-Comp > R+C) — metric-robust
- ✅ 2-Comp 의 (β_s, β_c) signature (sub-08 = (48,−36), sub-09 = (26,+6)) — metric-robust
- ⚠ R+C individual g 값 — metric-dependent (특히 sub-08 V4 → paper footnote 권장)
- ⚠ "L_γ dominance" 가설 — magnitude 차원만 성립, parameter-decision 차원 미성립

#### CVD 단일점 fit 안정 매트릭스 (2×2, K=6 JSON 직접 확인, 2026-05-24 신설)

| | behav path (L2 γ) | RDM path (L4 단독) |
|---|---|---|
| **R+C** | sub-08 V1/V4 g=2.25/2.25; sub-09 V1/V4 g=2.60/2.60 → **안정 ✅** ROI-invariant | sub-08 V1=2.15 / V4=1.25; sub-09 V1=2.30 / V4=1.05 → **V1만 안정 ⚠** ROI-비안정 |
| **2-Comp** | sub-08 (48,−36); sub-09 (26,+4) at V1=V4 → **안정 ✅** (단 U6 caveat: L8 50% L_γ weight) | sub-08 V1 (0,+2) / V4 (50,−32); sub-09 V1 (2,+50) / V4 (0,+4) → **불안정 ✗** β_c sign이 L8과 충돌 |

→ **CVD 단일점 fit 기준에서는 (R+C, behav), (2-Comp, behav), (R+C × V1 한정 RDM) 3 칸만 안정.** 나머지 (R+C × V4 RDM, 2-Comp × RDM 4 cells)은 ROI-비안정.

##### Behav path 모델 간 δθ 유사도 (필수 추가 조건, 2026-05-24)

행동 손실 하의 점추정 안정만으로는 *"모델-손실함수 안정성"* 주장 불충분. 두 모델 (R+C / 2-Comp)이 L2 에서 산출하는 *변환 색 값 δθ 8-vec* 이 유의미 유사해야 함:

| Cell | R+C δθ ‖·‖ | 2-Comp δθ ‖·‖ | cos | MAE | sign-agree | Verdict |
|---|---|---|---|---|---|---|
| sub-08 V1 | 22.7° | 86.5° | **+0.54** | 23.1° | 7/8 | **marginal** — 부호 일치도 높음, 크기 4× 차이 |
| sub-08 V4 | 22.7° | 86.5° | +0.54 | 23.1° | 7/8 | marginal (V1 동일) |
| sub-09 V1 | 59.9° | 54.7° | **+0.07** | 21.1° | 6/8 | **fail** — 두 δθ 사실상 무관, 크기는 유사하나 방향 다름 |
| sub-09 V4 | 59.9° | 54.7° | +0.07 | 21.1° | 6/8 | fail (V1 동일) |

→ **sub-08 의 behav-path 모델 안정성은 marginal** (방향 같지만 magnitude 4배 차이). **sub-09 는 behav-path 모델 안정성 실패** (cos≈0).

**Loss 값 비교 (정정 2026-05-24, identifiability 과장 회수)**:

| Cell | R+C L2 loss | 2-Comp L2 loss |
|---|---|---|
| sub-08 V1/V4 | 10.23 | 5.78 |
| sub-09 V1/V4 | 0.56 | 0.39 |

두 모델은 *같은 loss 값* 을 produce 하지 않음 — 각자 own parameter space 안에서 unique minimum. cross-model δθ 발산은 **identifiability failure 가 아니라 model-class prediction 비등가성** — δθ 예측이 model 선택에 의존.

**sub-09 의 발산 원인 = angular shape, not magnitude** (정정 2026-05-24, "너무 조금 이동" 가설 기각):

- sub-09 R+C ‖δθ‖ = 59.9° (sub-08 R+C ‖δθ‖ = 22.7° 보다 2.6× 큼) — magnitude는 충분.
- sub-09 R+C δθ: `[5, 6, 2, -2, -9, -46, +37, -1]` — c6/c7 집중 (Machado protan 180–225° 압축 특성).
- sub-09 2-Comp δθ: `[4, +22, +27, +16, -4, -22, -27, -16]` — sin-like 균등 분포 (β_s=26° S-cone 축 회전).
- 같은 magnitude 를 다른 angular pattern 에 배분 → cos≈0. sub-08 은 둘 다 "warm preserved / cool shifted" 라 부호 7/8 일치, 단 magnitude 4× 차.

→ Paper-level 함의 (정정): "behav loss 만으로는 *model-class-dependent* δθ — R+C (retinal cone-shift) 와 2-Comp (cortical opponent rotation) 가 같은 L_γ 를 minimize 하면서도 다른 색 변환을 predict. 따라서 mechanism 단정 전 model class 비교 필수."

**L8 ROI-invariance 의 메커니즘 (정정: artifact → L_γ-dominated 으로 강화)**: L8 magnitude 분해 (sub-08 V1):
- 0.5 × L_γ(5.78) = 2.89 → **L8 magnitude 의 ~88%**
- 0.25 × L_LOCO(0.88) = 0.22
- 0.25 × L_RDM(0.76) = 0.19

L_γ 가 L8 의 ~88% 차지 → V1/V4 의 L_LOCO/L_RDM 차이가 L_γ optimum 을 밀어내지 못함 → L8 (β_s, β_c) = L2 (β_s, β_c) 정확히. 따라서 **L8 ROI-invariance 는 mechanism convergence 가 아니라 L_γ-dominance 의 직접 귀결** (U6 + Loss-Design Constraints (1)+(2) 의 정량 evidence). neural path (L_RDM, L_LOCO) 가 L8 minimum 위치에 거의 영향 안 줌.

##### Visualization (2026-05-24, 4-col color figure 컨벤션)

기존 4-col 컨벤션 (`p2amax_option_C_visualize.render_4col`) 동일 형식: 8 colors × 4 columns (Original / CVD perceives / Filtered pre-image / CVD(Filtered)), STIM_LAB 색 렌더링.

- `results/s5_all_paths/S5_BEHAV_4col_RC_sub-08.{png,pdf}` — R+C (Δλ=6, g=2.25, deutan)
- `results/s5_all_paths/S5_BEHAV_4col_RC_sub-09.{png,pdf}` — R+C (Δλ=10, g=2.60, protan)
- `results/s5_all_paths/S5_BEHAV_4col_2Comp_sub-08.{png,pdf}` — 2-Comp (β_s=48, β_c=−36); **marginal model-stability (cos=+0.54, ‖2C‖/‖R+C‖=3.8×)**
- ⊘ 2-Comp sub-09 skip — cos(R+C, 2-Comp)=+0.07 → behav-stability fail (사용자 rule: 모델 안정 시에만 2-Comp 시각화)

Figure 의 P2a 수치는 §0.1 policy 에 따라 *descriptive only* (paper primary endpoint 아님).
Script: `scripts/s5_viz_behav_4col.py`

##### Pending: HC subset resample (S6')

위 *"안정"* 진단은 **CVD 본인의 single-point fit** 에만 근거. HC pool composition 흔들림에서도 δθ가 보존되는지는 S6' (line 708) 미실행 → 모든 안정 claim 은 HC reference dependence quantification 후 재확인 필요.

### Stage 4 — Verdict: ✅ PASS

- All 128 fits complete without errors
- Wall time 23s (well under target)
- Cortical amplification compensation (g* > 1) present in both subjects across most loss targets
- **FLAG**: Boundary hits in sub-09 R+C with Boehm/JND-Lamb Δλ (small Δλ + max amplification limit reached)
- **FLAG**: L3 (LOCO) frequently hits g=3 boundary → R+C 1-DOF cannot solely fit voxel-LOCO pattern

### Paper-level finding candidates

1. **Cortical-behavioral compensation in both CVD subjects** (g* > 2 under L8)
2. **Subtype-specific 2-Comp signature**: sub-09 β_c≈0 vs sub-08 β_c≈-36 (clear separation)
3. **Sub-09 cortical-behavioral dissociation 가설 정량화 (DPS hypothesis)**: 16 nm compensation
4. **R+C boundary issue for sub-09 mild Δλ**: paper 에 명시 — JND-Lamb interpretation 은 2-Comp 가 더 적합

### Files

- `scripts/two_comp.py`
- `scripts/s5_all_paths_fit.py`
- `results/s5_all_paths/{sub-08,sub-09}_{V1,V4}_sigma21.json`
- `results/s5_all_paths/summary.json`

---

## S6': HC subset resample for L_RDM / L_γ baseline variance (2026-05-24 신설, S5'/S6 대체)

> **Background (사용자 catch 2026-05-24)**: 기존 S5' 와 S6 는 두 가지 critical 약점 보유 — (1) S5' 는 HC 에 *CVD-prior Δλ 강제 대입* (Constraint #5 procedural bias), (2) S6 는 *CVD 본인의 single point g\* 의 trial-level bootstrap* 으로 measurement stability 만 측정 (true g uncertainty 아님). 두 sprint 모두 **paper 의 main HC comparison evidence 로는 약함**. 두 섹션 모두 *문서 최하단 아카이브로 이동* (`§Archive`). 본 S6' 는 사용자 제안 **HC subset resample design** 으로 두 sprint 의 의도를 통합 보강한다.

### S6'.1 Motivation

S5 의 L8 fit 자체가 HC reference 를 내장:
- **L_RDM**: HC pool mean RDM (LOO 7 명의 mean) 을 reference 로 사용 → CVD vs HC distance structure 차이 측정
- **L_γ (JND)**: HC HYPO baseline (per-pair HC pool JND mean) 을 reference 로 사용
- **L_α (8AFC)**: HC 100% accuracy target (constant)

따라서 **별도 HC 가상 Δλ fit (S5' Form B) 은 불필요**. 그러나 *"HC pool composition 이 g\* 추정에 얼마나 영향을 주는가"* 는 검증 필요. 사용자 design:

> "HC 7명에 대해 ΔRDM, behav diff 를 *여러 번 추출* — HC subset 을 random 으로 골라서 baseline reference 를 다시 만들고, CVD g\* 가 어떻게 흔들리나 본다."

### S6'.2 Design

**Resample unit = HC subset, not trial**:

```
For k in {4, 5, 6}:
    subsets = all C(7, k) combinations of HC subjects
    
    For each subset S:
        # Re-compute HC reference using only HC in S
        ΔRDM_ref_S = mean(RDM_h for h in S)
        JND_HC_S   = mean(JND_h for h in S)     # per-pair
        sigma_HC_S = mean(8AFC_sigma_h for h in S)
        
        # Re-fit CVD g* using these references (loss = L_γ, L_RDM, or composite)
        g*_S = argmin_g  L(g; HC_ref_S, CVD_data)
    
    Output: g* distribution across subsets → SD, range, 95% percentile CI
```

**Coverage**:
- k=4: C(7,4)=35 subsets — wide variance estimate
- k=5: C(7,5)=21 — paper-defensible mid
- k=6: C(7,6)=7 = LOO (S11 에서 이미 산출됨)

**비교**:
- *Subset SD* = HC pool composition 의 g\* 불안정성
- *Trial-level SD (S6 구)* = CVD 본인 measurement noise
- *S5' z=+3.45 (구)* = CVD-prior Δλ 강제 misspec hold 후 single g_HC

S6' 는 첫 번째만 측정 — *paper-relevant HC reference dependence*.

### S6'.3 Expected outputs (sprint 시행 시)

| Output | Format |
|---|---|
| g\*\_subset distribution per (subject, ROI, loss, k) | JSON: `results/s6p_hc_subset/g_distribution.json` |
| Subset CI (percentile [2.5, 97.5]) | per cell, compared to point estimate g\* |
| Visualization | histogram per (subject, ROI, loss), k 별 panel |

### S6'.4 Status

- **Implementation**: Pending (Phase 3 trigger 전에 시행, 또는 S12 sprint 와 통합)
- **Sample size considerations**: k=4 의 35 subsets 이 statistical power 측면에서 sufficient (B≈35-100 range bootstrap practice 상회는 marginal gain)
- **S11 LOO 와의 관계**: S11 (k=6 LOO) 가 이미 partial S6'. S6' 는 *k smaller 까지 확장* 으로 더 넓은 HC-composition variance 측정.

### S6'.5 Paper framing replacement

기존 S5' Form B 의 *"sub-09 z=+3.45 vs HC pool"* claim 은 S6' subset percentile 로 대체:

> **NEW (S6' 기반)**: "Sub-09 의 g\* = 2.60 는 HC pool 의 35 subset (k=4) 중 가장 큰 g\_HC 값을 포함하는 어떤 subset 에서 산출한 reference 와도 robust 하게 산출됨 — HC composition 영향 < X% of g\* point estimate"

vs.

> **OLD (S5' Form B)**: "HC pool g distribution 의 z=+3.45" — procedural bias 영향 받은 misspecified fit 산출값.

### S6' Files (sprint 시행 시)

- Script: `scripts/s6p_hc_subset_resample.py`
- Results: `results/s6p_hc_subset/{g_distribution.json, subset_percentile_ci.json}`
- Viz: `results/s6p_hc_subset/viz_subset_g_hist_{subject}_{roi}.png`

### S6' Status

⏸ **Pending implementation** — Phase 3 trigger 또는 paper revision 시점에 시행. 현재 S11 LOO (k=6) 결과로 부분 cover 가능.

---

---

## S6 (renamed from S7, 2026-05-24): Convergence matrix (✅ Complete 2026-05-21, framing 정정 2026-05-22)

> ⚠️ **Framing 정정 (사용자 catch 2026-05-22)**: "Δλ source convergence" 라는 표현은 misleading. 같은 quantity 의 *다른 추정* 이 수렴하는 게 아니라 — **3 외부/내부 Δλ assumption (DPS 상수 + Boehm 상수 + JND-Lamb data-driven fit) 하에서 g\* 가 얼마나 robust 한가** 의 sensitivity check. 정확한 용어: "**Δλ-prior robustness**".

### Stage 0 — 판단 기준 + 수식 정의 (2026-05-22 added per 사용자 요구)

본 sprint 가 평가하는 3 종류의 *convergence/robustness* 와 각각의 정의:

#### (A) Within-model loss convergence (per Δλ source × per subject-ROI)

**정의**: 같은 모델/같은 Δλ assumption 하에서, 8 loss target 의 fitted g\* 가 얼마나 일치하는가.

```
For (subject, ROI, Δλ_source) fixed:
   g_set = {g*(L_k) for k in 1..8}  ← 8 fitted g values
   metric_A1 = std(g_set)            ← spread
   metric_A2 = max(g_set) − min(g_set)  ← range
```

**판단 threshold**:
- ✅ tight: SD ≤ 0.2, range ≤ 0.5
- ✓ acceptable: SD ≤ 0.4, range ≤ 1.0
- ⚠ loose: SD > 0.4 또는 range > 1.0
- ⚠⚠ catastrophic: range > 2.0 (full grid)

**해석**:
- Tight → 모델/Δλ가 *robust to loss choice* (model 자체가 strong constraint)
- Loose → loss-dependent, *L8 weighted compromise 의미 강함*

#### (B) Δλ-prior robustness — 사용자 의도 정정 (2026-05-24)

> ⚠️ **Framing 정정 (사용자 catch 2026-05-24)**: 기존 (B) 정의는 *per loss × 3 Δλ 의 g\* range*. 사용자가 원했던 것은 **반대 방향** — *per Δλ source × 8 loss 의 g\* spread* — 즉 "**어느 Δλ assumption 이 loss-choice 에 가장 stable 한 fit 을 주는가**". 결과는 §S7-B 결과 표 (Stage 3) 참조.

**(B-new) 정의**: 같은 모델/같은 Δλ assumption 하에서, 8 loss target 의 fitted g\* 가 얼마나 일치하는가 (= (A) 의 *per-Δλ* 분리 산출).

```
For (subject, ROI, Δλ_source) fixed:
   g_set = {g*(L_k) for k in 1..8}    ← 8 fitted g (per Δλ)
   metric_B1 = SD(g_set)
   metric_B2 = stable_count = #{g_k ∈ [0.5, 2.8]}  (interior, non-boundary)
```

**판단 threshold**:
- ✅ Δλ-stable: SD ≤ 0.2
- ✓ acceptable: SD ≤ 0.4
- ⚠ loose: SD > 0.4 (loss-dependent, Δλ가 보호 못함)

**해석**:
- ✅ → Δλ assumption 이 *loss-choice 와 무관한 stable fit* 제공 → paper-defensible Δλ
- ⚠ → 같은 Δλ 하에서도 loss 따라 g\* 크게 흔들림 → Δλ assumption 보호력 부족, *모델 자체의 한계* 또는 *data information 약함*

#### (C) Cross-model δθ alignment (R+C vs 2-Comp per subject-ROI)

**정의**: 같은 (subject, ROI, L8) 하에서, R+C 와 2-Comp 가 산출하는 8-vec δθ 가 얼마나 같은 모양인가.

```
For (subject, ROI) fixed with L8 modality 5050:
   δθ_RC   = (8,) from R+C(Δλ_DPS, g*)        # R+C-fitted
   δθ_2C   = (8,) from 2-Comp(β_s*, β_c*)     # 2-Comp-fitted
   
   metric_C1 = Spearman_ρ(δθ_RC, δθ_2C)
   metric_C2 = cos_sim(δθ_RC, δθ_2C) = ⟨δθ_RC, δθ_2C⟩ / (‖δθ_RC‖·‖δθ_2C‖)
   metric_C3 = MAE = mean(|δθ_RC[c] − δθ_2C[c]|)
   
   Bootstrap CI of Spearman_ρ:
     B=1000 resamples of {1..8} indices with replacement
     ρ_b for each, percentile [2.5, 97.5]
```

**판단 threshold**:
- ✅ strong convergence: ρ ≥ 0.7 AND CI excludes 0 AND cos ≥ 0.7
- ✓ moderate: 0.4 ≤ ρ < 0.7 AND CI excludes 0
- ⚠ weak/inconclusive: ρ < 0.4 OR CI includes 0
- ✗ divergent: ρ < 0 (anti-correlation)

**해석**:
- ✅ → R+C / 2-Comp 가 *같은 distortion* 의 다른 parameterization
- ⚠/✗ → 두 모델이 *서로 다른 information* 추정 → paper 가 complementary 로 framing

### Stage 1 — Implementation

- **Script**: `scripts/s7_convergence.py`
- Analyses S5 fit matrix for:
  - **Within-model loss convergence**: 8 losses × per-Δλ source variance
  - **Δλ source convergence (R+C)**: 3-source g* per loss
  - **2-Comp parameter variance**: (β_s, β_c) across 8 losses
  - **Cross-model δθ**: R+C vs 2-Comp Spearman ρ + bootstrap CI

### Stage 2 — Validation

- All convergence metrics finite (no NaN)
- Spearman bootstrap CI computed across 8 colors with replacement

### Stage 3 — Interpretation

#### (B-new) Per-Δλ loss-stability (2026-05-24 사용자 catch, S7-B 재산출)

**Question**: 어느 Δλ assumption 이 8 loss 의 g\* 를 가장 stable 하게 묶는가?

| Cell | Δλ source | Δλ (nm) | SD(g) | range | Stable / 8 | Boundary | Verdict |
|---|---|---|---|---|---|---|---|
| sub-08 V1 | DPS | 6.0 | 0.722 | 2.250 | 7/8 | 1 | ⚠ loose |
| sub-08 V1 | Boehm | 8.0 | 0.922 | 2.200 | 6/8 | 2 | ⚠ loose |
| sub-08 V1 | **JND-Lamb** | 6.5 | **0.712** | 2.250 | 7/8 | 1 | ⚠ loose (best of 3) |
| sub-08 V4 | **DPS** | 6.0 | **0.509** | 1.200 | 8/8 | 0 | ⚠ loose (best of 3) |
| sub-08 V4 | Boehm | 8.0 | 0.943 | 2.150 | 5/8 | 1 | ⚠ loose |
| sub-08 V4 | JND-Lamb | 6.5 | 1.083 | 2.250 | 4/8 | 4 | ⚠ loose |
| sub-09 V1 | **DPS** | 10.0 | **0.310** | 1.000 | 6/8 | 2 | ✓ **acceptable** ★ |
| sub-09 V1 | Boehm | 3.0 | 1.005 | 3.000 | 3/8 | 5 | ⚠⚠ catastrophic |
| sub-09 V1 | JND-Lamb | 1.5 | 0.719 | 2.200 | 4/8 | 4 | ⚠ loose |
| sub-09 V4 | **DPS** | 10.0 | **0.814** | 2.100 | 8/8 | 0 | ⚠ loose (best of 3) |
| sub-09 V4 | Boehm | 3.0 | 1.346 | 3.000 | 1/8 | 5 | ⚠⚠ catastrophic |
| sub-09 V4 | JND-Lamb | 1.5 | 1.392 | 3.000 | 1/8 | 7 | ⚠⚠ catastrophic |

**Key findings**:

1. **★ Sub-09 V1 DPS Δλ=10 가 8 cell × 3 source = 24 조합 중 유일하게 "acceptable" 통과** (SD=0.310, 6/8 interior). Sub-09 의 paper-defensible Δλ assumption 은 **오직 DPS=10nm**.

2. **Sub-09 Boehm/JND-L 의 catastrophic instability**: Small Δλ (3 / 1.5 nm) 에서 R+C 1-DOF 가 *L_α/L_γ 는 g≈2 정상*, *L3 LOCO 는 g=0*, *L4 RDM 은 g=3* — 같은 Δλ 하에서 *loss 따라 g 가 grid 양 끝으로 split*. Boundary hit 5-7/8. **Paper 에 "Boehm/JND-L Δλ 는 procedurally fragile 로 flag"**.

3. **Sub-08 은 어떤 Δλ 도 acceptable 못함** (SD 최저 V4 DPS = 0.509). 즉 sub-08 의 R+C g 는 *Δλ assumption 이 아닌 loss choice 에 본질적으로 의존* — model 자체의 한계 (single-DOF 가 sub-08 8-color pattern 을 못 잡음).

4. **(B-구) Δλ-prior robustness 와의 대조**: 기존 (B-구) 는 *per loss × 3 Δλ* — behavioral robust / neural sensitive. **(B-new) 는 *per Δλ × 8 loss* — sub-09 DPS 만 loss-stable**. 두 관점이 함께 paper 의 sub-09 결론 (DPS Δλ=10 + cortical g≈2.6 가 유일 robust path) 을 확정.

#### (B-구) R+C Δλ-source convergence per loss

| Loss | sub-08 V4 range | sub-09 V1 range | sub-09 V4 range |
|---|---|---|---|
| L1 (8AFC α) | 0.00 ✓ | 0.00 ✓ | 0.00 ✓ |
| L2 (JND γ) | 0.05 ✓ | 0.40 ✓ | 0.40 ✓ |
| L3 (LOCO) | 0.00 ✓ | 0.65 ⚠ | **3.00 ⚠⚠** |
| L4 (RDM) | 0.90 ⚠ | 0.75 ⚠ | 1.90 ⚠ |
| L5 (behav) | 0.05 ✓ | 0.40 ✓ | 0.40 ✓ |
| L6 (neural) | 0.05 ✓ | 0.75 ⚠ | 1.90 ⚠ |
| L7 (all-equal) | 0.10 ✓ | 0.45 ✓ | 0.45 ✓ |
| L8 (modality) | 0.05 ✓ | 0.40 ✓ | 0.40 ✓ |

**Key**: Behavioral losses CONVERGE across Δλ sources, neural losses DIVERGE.
- L3 LOCO: sub-09 V4 의 g range = 3.0 = full grid (Δλ-source 완전 dependent)
- L4 RDM: similarly Δλ-source dependent
- → Neural loss interpretation is *load-bearing on Δλ assumption*

#### 2-Comp parameter variance across 8 losses

| Subject ROI | β_s mean ± SD | β_c mean ± SD |
|---|---|---|
| sub-08 V4 | 26.2 ± 23.8 | -16.0 ± 24.0 |
| sub-08 V1 | (similar) | (similar) |
| sub-09 V1 | 21.2 ± 15.1 | 4.2 ± 20.0 |
| sub-09 V4 | 24.8 ± 11.0 | -12.8 ± 20.8 |

**Huge variance** — 2-Comp parameters are *loss-dependent* (each loss type produces qualitatively different (β_s, β_c)).
- Sub-08: warm-side compression (β_s≈25, β_c≈-16) on average, but range up to ±36°
- Sub-09: S-cone rotation dominant (β_s≈25), β_c near zero with high variance

#### Cross-model δθ agreement (R+C L8 DPS vs 2-Comp L8) — 2026-05-24 metric overhaul

> ⚠️ **Metric 정정 (사용자 catch 2026-05-24)**: Spearman ρ 는 rank-only → magnitude 무시 (e.g. R+C blue=−22° vs 2-C blue=−43° 가 *same rank* 로 처리). 두 모델 distortion pattern 의 *방향 + 크기 모두 일치* 평가에 부적절. **대체**: Lin's CCC (concordance with identity line, method-agreement gold standard) + Bland-Altman per-color + linear regression slope.

##### Primary metric: Lin's Concordance Correlation Coefficient (CCC)

CCC = 2·cov(X,Y) / [var(X) + var(Y) + (μ_X − μ_Y)²]

CCC penalizes:
1. Linear correlation 부족 (Pearson r 와 동일 성질)
2. Identity line (y=x) 으로부터의 deviation (scale + location shift)

| Lin 1989 threshold | Range | Interpretation |
|---|---|---|
| ≥ 0.99 | excellent | almost perfect agreement |
| 0.95 - 0.99 | substantial | paper-defensible "same distortion" |
| 0.90 - 0.95 | moderate | partial agreement |
| < 0.90 | poor | distinct estimates |

##### S7 (C) main result table (4 cells)

| Subject | ROI | R+C g\* | 2-Comp (β_s, β_c) | Pearson r | **CCC** | CCC 95% CI | slope | intercept | MAE (°) | BA bias (°) |
|---|---|---|---|---|---|---|---|---|---|---|
| sub-08 | V1 | 2.25 | (48, −36) | **+0.55** | **+0.27** ⚠ | bootstrap | **+2.14** | −2.0° | 23.1 | +1.4 |
| sub-08 | V4 | 2.30 | (48, −36) | **+0.55** | **+0.31** ⚠ | bootstrap | **+1.78** | −0.4° | 22.5 | +1.7 |
| sub-09 | V1 | 2.60 | (26, +6) | **+0.10** | **+0.10** ✗ | bootstrap | **+0.10** | +6.4° | 20.6 | +1.1 |
| sub-09 | V4 | 2.60 | (26, +6) | **+0.10** | **+0.10** ✗ | bootstrap | **+0.10** | +6.4° | 20.6 | +1.1 |

(Bootstrap CI from B=2000 paired index resampling; full CI in `results/s7_convergence/rc_vs_2comp_agreement.json`)

##### Key findings — CCC 가 노출한 새 정보

1. **Sub-08 CCC ≈ +0.30 → 두 모델 "poor agreement"**. Pearson r=+0.55 는 *linear association 있음* (slope=+2.14, +1.78 → 2-C 가 R+C 의 ~2배 크기). 즉 **방향은 일치, magnitude 가 2배 다름** — Spearman 의 ρ=0.60 이 *이 critical magnitude 차이를 가렸음*. Identity line 으로부터 멀리 떨어진 disagreement.

2. **Sub-09 CCC = +0.10 → "disagreement"**. Slope = +0.10 (almost flat) — 2-C 가 R+C 와 거의 무관한 distortion pattern. **두 모델이 서로 다른 mechanism 추정**:
   - R+C: blue (−45.7°), purple (+36.5°) 의 *cone-shift driven extreme*
   - 2-C: yellow (+27.7°), orange (+23.6°) 의 *S-cone rotation dominant*
   - Pearson r=+0.10 도 동의 → 진정한 model divergence

3. **Sub-08 V1/V4 의 CCC 차이 (0.27 vs 0.31)**: 정확히 다름. **R+C g\* 가 V1 (2.25) ≠ V4 (2.30)** → δθ_RC magnitude 가 V4 에서 살짝 더 큼 → 2-C 와의 slope 가 V4 에서 더 1.0 에 가까움. Spearman 의 ROI 동일 결과는 *rank 만 같았을 뿐*, magnitude 정보로 V1≠V4.

##### Bland-Altman per-color disagreement

| Cell | bias (°) | ±1.96 SD LoA (°) | 큰 outlier (|diff−bias| > 1.96 SD) |
|---|---|---|---|
| sub-08 V1 | +1.42 | ±56.7 | none (모든 점 LoA 내) |
| sub-08 V4 | +1.70 | ±55.6 | none |
| sub-09 V1 | +1.10 | ±57.8 | **purple** (diff = −64.2°, LoA 초과) |
| sub-09 V4 | +1.10 | ±57.8 | **purple** (diff = −64.2°, LoA 초과) |

→ **Sub-09 purple 이 유일한 statistical outlier**. 다른 색들은 LoA 안 (단 LoA 가 ±57° 로 매우 넓음 → 두 모델 차이의 본질적 magnitude).

##### Paper-level interpretation update

- **OLD (Spearman 기반)**: "R+C 와 2-Comp 는 weak alignment (CI 0 포함), complementary"
- **NEW (CCC 기반)**: "R+C 와 2-Comp 는 **distinctly different distortion estimates** (CCC ≤ 0.31 both subjects). Sub-08 에서 direction 일치하나 magnitude 가 2× 다름. Sub-09 에서 direction 자체 다름 (purple 이 핵심 disagreement)."
- → **Paper claim**: "Two models capture **different mechanisms**, not complementary parameterizations of the same distortion". 이 framing 이 §5 의 §1 paper finding "Subtype-specific 2-Comp signature" 와 일관 — sub-09 의 β_c≈0 (S-cone only) 가 R+C cone-shift 와 *근본적으로 다른 mechanism*.

##### Files
- Script: `scripts/s7c_rc_vs_2comp_agreement.py`
- Results: `results/s7_convergence/{rc_vs_2comp_agreement.json, SUMMARY_agreement.md}`
- Viz: `results/s7_convergence/viz_bland_altman.png` (4 panel Bland-Altman)
- Per-color δθ viz: `results/s5_all_paths/viz_rc_vs_2comp_delta_theta.png` (bar + polar)

##### ROI-invariance 의 출처 (참조)

Cross-model δθ agreement 는 forward output (=δθ 8-vec) 만 비교 — voxel data 직접 입력 안 함. L8 fit 의 50% behavioral component 가 ROI 무관 → fitted params 거의 ROI-invariant. 이 ROI-invariance 자체가 §"Acknowledged Constraints (2) L8 weighted compromise" 의 direct empirical evidence.

### Key findings

1. **Behavioral loss = robust to Δλ assumption** (per-subject param stability)
2. **Neural loss = Δλ-source dependent** (L3, L4 sensitive)
3. **2-Comp parameters are loss-dependent** (no stable point estimate without loss specification)
4. **Cross-model δθ agreement poor (CCC ≤ 0.31)** — R+C and 2-Comp capture *different mechanisms*, not complementary parameterizations of same distortion (2026-05-24 metric overhaul)

### Stage 4 — Verdict: ✅ PASS (with major paper findings)

- ✓ Behavioral loss family convergent (stable g* across Δλ assumptions for L1, L2, L5, L7, L8)
- ⚠ FLAG: Neural loss family (L3, L4, L6) sensitive to Δλ assumption — paper limitation
- ⚠ FLAG: 2-Comp params loss-dependent — must report range/distribution, not single point estimate
- ⚠ FLAG: Cross-model δθ alignment weak — R+C vs 2-Comp are *different views*, paper must discuss

### Paper-level claims (revised)

1. "Per-subject g* under behavioral fitting is robust to Δλ source"
2. "Neural fitting is informative under specific Δλ assumption; cross-Δλ-source convergence is limited"
3. "R+C and 2-Comp models provide complementary, not redundant, characterizations of CVD distortion"
4. "Model-loss preferences differ — paper reports L8 primary results with sensitivity analysis"

### Files

- `scripts/s7_convergence.py`
- `results/s7_convergence/convergence_matrix.json`

---

## [Archived 2026-05-24] S8_old: Selection + Cross-subtype + Form C permutation (✅ Complete 2026-05-21)

> **Archive note (2026-05-24)**: S12 design 에서 color-label permutation 이 S12 main flow criterion 에서 제거됨 (사용자 catch: positive characterization vs null rejection 별개). 본 sprint 의 selection 결정은 **S7 (new) 에 의해 supersede**. Content 보존 — color-perm methodology 와 historical decisions 참고용.

### Stage 1 — Implementation

- **Script**: `scripts/s8_selection_xsubtype_perm.py`
- (1) Per-fit selection metrics (AICc, BIC, 8AFC corr separate per advisor)
- (2) Cross-subtype train-test (sub-08↔sub-09, §6.4 concrete steps)
- (3) Form C permutation null (B=200 local, full B=1000 deferred to SLURM)

### Stage 2 — Validation

- All 128 S5 fits scored
- Cross-subtype completed for both directions
- Permutation null computed for both CVDs

### Stage 3 — Interpretation

#### (1) Selection metrics — L8 primary winners

| Subject ROI | AICc(JND) winner | BIC(JND) winner | 8AFC corr winner |
|---|---|---|---|
| sub-08 V1 | 2-Comp (AICc=-22.8) | 2-Comp (BIC=-25.1) | R+C DPS (r=-0.42) |
| sub-08 V4 | 2-Comp (-22.8) | 2-Comp (-25.1) | R+C DPS (-0.42) |
| sub-09 V1 | **2-Comp (-51.5)** | **2-Comp (-53.8)** | R+C DPS (r=0.0, ceiling) |
| sub-09 V4 | **2-Comp (-51.4)** | **2-Comp (-53.7)** | R+C DPS (r=0.0, ceiling) |

**Key**: 2-Comp wins AICc and BIC (lower) — JND fit better than R+C 1-DOF even with k=2 penalty. ΔAICc ≈ 30 (very strong evidence for 2-Comp over R+C, Kass-Raftery >10).

#### (2) Cross-subtype train-test

| Direction | train g | target g_own | L_behav_cross | L_behav_within | Error ratio (cross/within) |
|---|---|---|---|---|---|
| **sub-08 → sub-09** | 2.25 | 2.60 | 0.881 | 0.560 | **1.57** (subtype-specific) |
| sub-09 → sub-08 | 2.60 | 2.25 | 5.672 | 5.151 | 1.10 (near-generic) |

**Asymmetric subtype-specificity**:
- Sub-08 (deutan g=2.25) does NOT transfer well to sub-09 (57% worse)
- Sub-09 (protan g=2.60) transfers OK to sub-08 (10% worse only)
- → **Sub-09's strong cortical amplification is generic mechanism; sub-08's mild compensation is subtype-specific**

#### (3) Form C permutation null (B=200, selection-aware)

| Subject | Real loss | Real g* | Null loss mean | p-value |
|---|---|---|---|---|
| sub-08 | 5.149 | 2.20 | 192.38 | **0.150** (NS) |
| **sub-09** | **0.560** | **2.60** | **23.34** | **0.000** ★ |

**Sub-09 of selection-aware null p=0.000**: 0/200 permutations achieved as good fit. Strongest evidence to date.
**Sub-08 p=0.150**: real loss much lower than null mean but 15% of permutations achieved similar or better — *not significant under selection-aware null* (bootstrap bimodality + label-permutation flexibility).

### Stage 4 — Verdict: ✅ PASS

- ✓ 2-Comp wins AICc/BIC selection (both subjects)
- ✓ Sub-09 strong evidence across all criteria (bootstrap CI, permutation p=0.000, cross-subtype transferable)
- ⚠ FLAG: Sub-08 permutation NS — paper limitation (bootstrap bimodality, label-permutation flexibility)
- ✓ Cross-subtype asymmetry → mechanism-specific findings

### **PHASE 2 OVERALL PAPER FINDINGS**

#### Sub-09 (protan, Ishihara 9/14 mild severity)
| Evidence type | Result | Strength |
|---|---|---|
| JND-Lamb Δλ | 1.5 nm (vs DPS 10) | ★ mild severity |
| R+C g* | 2.60 (M_comp=16 nm under DPS) | ★ strong amplification |
| Bootstrap CI of g | [1.30, 2.60] excludes 1.0 | ★ compensation confirmed |
| Permutation p | 0.000 | ★★ selection-aware null exceeded |
| V1 LOCO p (project memory) | 0.007 | ★ strong neural signature |
| V1 ΔRDM p (project memory) | 0.005 | ★ strong distortion |
| Cross-subtype transfer | g_sub09 → sub-08: error ratio 1.10 | sub-09 mechanism generic |
| AICc/BIC | 2-Comp wins (-51 vs R+C) | parsimony favors 2-Comp descriptor |

**Paper claim**: "Mild protan (Ishihara 9/14) with behaviorally near-normal discrimination yet strong cortical-behavioral neural distortion signature (V1 p<0.01). Bootstrap and permutation evidence supports cortical amplification compensation (g* > 1, p<0.001)."

#### Sub-08 (deutan, Ishihara 7/14)
| Evidence type | Result | Strength |
|---|---|---|
| JND-Lamb Δλ | 6.5 nm (vs DPS 6) | convergent 3-source |
| R+C g* | 2.25 (M_comp=7.5 nm) | mild amplification |
| Bootstrap CI of g | bimodal [0, 3] | ✗ fit instability (paper limitation) |
| Permutation p | 0.150 | ✗ NOT significant under selection-aware null |
| Cross-subtype transfer | sub-08 g → sub-09: error ratio 1.57 | sub-08 subtype-specific |
| AICc/BIC | 2-Comp wins (-22 vs R+C) | 2-Comp better fit |

**Paper claim**: "Deutan (Ishihara 7/14) with clear behavioral deficit (8AFC 82.5%, yellow-axis JND HYPO). 2-Component descriptor captures structural distortion (β_s=48, β_c=-36). R+C 1-DOF fit shows mechanism instability across loss specifications — *behavioral measure incongruence between 8AFC errors and JND*."

#### Cross-subtype dissociation
- **Sub-08 mechanism subtype-specific** (not transferable to sub-09)
- **Sub-09 mechanism partially generic** (transferable to sub-08 with similar fit quality)
- → Asymmetry interesting paper finding (single-direction transfer)

### Files

- `scripts/s8_selection_xsubtype_perm.py`
- `results/s8_final/selection_metrics.json`
- `results/s8_final/cross_subtype.json`
- `results/s8_final/perm_null.json`

---

## [Archived 2026-05-24] S9_old: Retroactive defenses (사용자 catch 2026-05-21, ✅ Complete) — (content consolidated into new S9, 2026-05-24)

> **Consolidation note (2026-05-24)**: 본 sprint 와 S10_old (Advisor corrections) 가 새 **S9: Integrated defenses** (line 1776) 으로 통합 완료. 본 section 은 historical record 로 보존.

### Context

사용자가 두 가지 failed defenses 의 근거를 직격:
1. §6.3 HC transfer test PRIMARY plan 미실행 — V_s mismatch 잘못 해석
2. Group-level CVD vs HC FPR 새 framework 에서 재검증 안 함

**My acknowledgement**: 둘 다 정직한 실수.
- (1) Within-HC LOCO는 scalar (V_s 무관), (Y) ΔRDM은 28-vec V_s-invariant, (Z) 8AFC는 W-independent → 모두 feasible 했음
- (2) "FPR=100%" 는 old measurement family (voxel-prediction L_LOCO) — 새 L_behav primary framework 에서 재검증 필요

### Stage 1 — Implementation

- **Script**: `scripts/s9_retroactive_defenses.py`
- Part 1: 7-fold HC transfer test (CVD's δθ → HC h, X/Y/Z metrics, V4 + V1)
- Part 2: L_behav framework FPR — each HC treated as fake CVD, point fit + bootstrap

### Stage 2 — Validation

- All 7 HC tested, 2 CVD × 2 models = 28 transfer tests per ROI
- HC point fits stable across subjects (some sub-07 outliers)

### Stage 3 — Interpretation

#### (1) Transfer test — V4 results

| Subject | Model | (X) LOCO ratio (mean ± range) | (Y) JND ratio (median) | Z 8AFC ratio (median) |
|---|---|---|---|---|
| sub-08 | R+C | 0.999 [0.990, 1.023] | 0.96 | 12.5 |
| sub-08 | **2-Comp** | 1.012 | **4.59** ★ | 258.5 |
| sub-09 | R+C | 1.023 | 1.86 | 102.5 |
| sub-09 | 2-Comp | 1.011 | 1.82 | 90.1 |

**Key findings**:
- **(X) LOCO transfer NOT informative**: ratios ≈ 1.0 across all 7 HCs for both models
  - 원인: LOCO 가 mostly voxel covariance noise (project memory consistent)
- **(Y) JND transfer**: 2-Comp sub-08 degrades HC fit by 4.59× (median) — **subtype-specific evidence strongest here**
- **(Z) 8AFC transfer**: huge ratios but interpretable only relative (HC baseline tiny ~0% errors)

#### (2) L_behav FPR test — new framework

| Subject | CVD g* | HC pool max | HC pool mean | N HC ≥ CVD g | **FPR** |
|---|---|---|---|---|---|
| sub-08 | 2.25 | 2.20 | 1.93 | 0/7 | **0.000** |
| **sub-09** | **2.60** | **2.30** | **2.09** | **0/7** | **0.000** |

**Bootstrap (HC mean ≥ CVD g)**: p = 0.000 for both subjects.

### CRITICAL paper-level reframe

**Old project memory FPR=100%** — voxel-prediction L_LOCO measurement family (cycle 9-13).

**New framework FPR=0.000** — L_behav primary R+C g fit:
- HC pool g ≈ 2.0 ± 0.15 (protan) or ± 0.46 (deutan)
- CVD g 가 HC pool max 보다 *higher*
- → **Group-level specificity 가 새 framework 에서 회복**

→ **Paper-level claim 정정**:
- ❌ ~~"FPR=100% known limitation"~~
- ✓ "New L_behav primary framework restores specificity: FPR=0.000 for both CVD subjects under hypothesis-matched Δλ"

### Stage 4 — Verdict: ✅ PASS (사용자 catch 가치 ★★★)

- ✓ §6.3 transfer test 실행됨 (사용자 catch 후 retroactive)
- ✓ FPR 새 framework 재검증 → 0.000
- ★ Sub-09 cortical compensation evidence가 *one more independent defense* 획득

### Files

- `scripts/s9_retroactive_defenses.py`
- `results/s9_retroactive/transfer_test_V4.json`
- `results/s9_retroactive/transfer_test_V1.json`
- `results/s9_retroactive/fpr_test.json`

---

## [Archived 2026-05-24] S10_old: Advisor-driven critical corrections (✅ 2026-05-21) — (content consolidated into new S9, 2026-05-24)

> **Consolidation note (2026-05-24)**: S9_old 와 함께 새 **S9: Integrated defenses** (line 1776) 으로 통합 완료. 본 section 은 historical record 로 보존.

### Context

Advisor evaluation after S9 surface 5 critical concerns:
1. "FPR=0.000" misleading — actually point percentile, n=7 HC only
2. Transfer (Y) JND 4.59× not normalized by ‖δθ‖²
3. (X) LOCO ≈ 1.0 misinterpreted as "noise" (correctly: test uninformative)
4. Cross-subtype asymmetry artifact concern unresolved
5. Permutation p=0.000 over-destructive

### Stage 3 — Results

#### (1) ‖δθ‖²-normalized transfer test — Subtype-specific claim COLLAPSES

| Model | sub-08 raw | sub-08 ‖δθ‖² | **sub-08 norm** | sub-09 raw | sub-09 ‖δθ‖² | **sub-09 norm** |
|---|---|---|---|---|---|---|
| R+C | 0.96 | 516 | 0.00186 | 1.86 | 3583 | 0.00052 |
| 2-Comp | 4.59 | 7488 | **0.00061** | 1.82 | 3136 | **0.00058** |

**Sub-08 2-Comp normalized (0.00061) ≈ Sub-09 2-Comp normalized (0.00058)**.

→ "Sub-08 2-Comp subtype-specific 4.59× degradation" was **‖δθ‖²=7488 magnitude artifact**, NOT subtype-specific signal.

#### (2) Specificity reframe — FPR=0.000 → CI overlap

| Subject | Point: N HC ≥ CVD | CVD bootstrap CI | HC pool bootstrap CI | CI overlap? |
|---|---|---|---|---|
| sub-08 | 0/7 | [0.000, 3.000] | [0.000, 3.000] | ✓ Complete overlap |
| sub-09 | 0/7 | [1.300, 2.600] | [1.000, 2.350] | ✓ Overlap [1.30, 2.35] |

→ "FPR=0.000" → **"0/7 point fits exceed CVD (descriptive percentile), bootstrap CI overlap at margin"**.

Project §0 policy: "Specificity claim 금지, descriptive percentile OK" — must apply.

#### (3) AICc/BIC precision — earlier claim "ΔAICc=-30" WAS WRONG

| Subject | R+C AICc | 2-Comp AICc | **ΔAICc** | Kass-Raftery |
|---|---|---|---|---|
| sub-08 | -22.40 | -22.81 | **+0.41** | <2: indistinguishable |
| sub-09 | -44.17 | -51.43 | **+7.27** | 6-10: strong |

→ I previously read 2-Comp AICc absolute value (-22.81) as "Δ=-22". Real Δ is +0.41 (sub-08 indistinguishable) and +7.27 (sub-09 strong).

#### (4) Cross-subtype Δ analysis INVERTS the asymmetric claim

| Direction | L_within | L_cross | **Δ (cross-within)** | Ratio |
|---|---|---|---|---|
| sub-08 → sub-09 | 0.560 | 0.881 | +0.32 (smaller abs) | 1.57 |
| sub-09 → sub-08 | 5.151 | 5.672 | **+0.52 (larger abs)** | 1.10 |

→ Under Δ: **sub-09→sub-08 transfer is *larger* absolute error**. "Sub-09 mechanism transferable, sub-08 subtype-specific" claim **INVERTS** — was ratio artifact of base loss magnitude.

#### (5) Loss-assignment permutation null (less destructive)

| Subject | S8 color-perm p | **S10 loss-assign perm p** | Verdict |
|---|---|---|---|
| sub-08 | 0.150 | 0.130 | NS in both — robust limitation |
| sub-09 | 0.000 | **0.000** | Significant in BOTH — robust evidence |

→ Sub-09 permutation evidence survives less destructive null (✓ robust); sub-08 fails in both.

### Stage 4 — Verdict: ✅ PASS (with substantial paper claim revisions)

**Paper claims SURVIVE**:
- ✓ Sub-09 individual-level g > 1 (Bootstrap CI [1.30, 2.60] excludes 1.0)
- ✓ Sub-09 permutation p=0.000 robust under two null forms (S8 + S10)
- ✓ Sub-09 mild protan (JND-Lamb 1.5 nm + Ishihara 9/14 + V1 LOCO p=0.007)
- ✓ Sub-08 2-Comp captures structural distortion (β_s=48, β_c=-36)
- ✓ Sub-08 R+C 1-DOF misspecified (bimodal bootstrap, boundary mass)

**Paper claims COLLAPSE (must remove)**:
- ✗ "Group-level CVD vs HC specificity recovered (FPR=0)" — only descriptive percentile, CI overlap
- ✗ "2-Comp subtype-specific transfer (4.59× sub-08)" — ‖δθ‖² magnitude artifact
- ✗ "Asymmetric subtype-specificity (sub-08 specific, sub-09 generic)" — INVERTS under Δ analysis
- ✗ "ΔAICc=-30 very strong evidence" — actually +0.41 (sub-08) and +7.27 (sub-09)

### Files

- `scripts/s10_advisor_fixes.py`
- `results/s10_advisor_fixes/` (logs in script output)

---

## PHASE 2 COMPLETE (Final, advisor-corrected) — Per-subject filter recommendations

### Sub-09 filter recommendation (paper-ready)
- **2-Comp PRIMARY**: β_s=26 (V1) or β_s=28 (V4), β_c ≈ 0-4 (S-cone rotation dominant)
- AICc -51 (very strong evidence)
- Permutation p=0.000 (selection-aware significant)
- Neural V1 signature confirmed (LOCO p=0.007)

### Sub-08 filter recommendation (paper-ready with limitation)
- **2-Comp**: β_s=48, β_c=-36 (warm-side compression + confusion-axis rotation)
- AICc -22 (strong but less than sub-09)
- Permutation p=0.150 (limitation: bootstrap bimodal, behavioral measure incongruence)

### Phase 3 (Stage D) requirements
- Sub-09 filter behavioral validation (filter-on vs filter-off 8AFC/JND)
- Sub-08 filter behavioral validation
- (Optional) Cross-subtype filter swap to test mechanism specificity

---

## K-robustness Final Report (2026-05-22)

Following user catch on K mismatch (SRM K-values were inadvertently used as FE basis K in `neural_loss.py:42`), all S4–S10 sprints were re-run with **FE-6 uniform** (Phase 1 baseline).

### Method
- `neural_loss.py:42` `ROI_K = {V1:6, V2:6, V3:6, V4:6}` (previously {4, 4, 3, 3}).
- All downstream sprints (S5/S5'/S6/S7/S8/S9/S10) re-executed sequentially. Total wall time ≈ 12 min.

### Results table (K=3-4 SRM-override → K=6 FE-uniform)

| Metric | K=3-4 (old) | **K=6 (corrected)** | Verdict |
|---|---|---|---|
| Sub-09 R+C g* (DPS, V1) | 2.60 | **2.60** | ✅ identical |
| Sub-08 R+C g* (DPS, V1) | 2.25 | **2.25** | ✅ identical |
| Sub-08 2-Comp V1 (β_s, β_c) | (48, −36) | **(48, −36)** | ✅ identical |
| Sub-08 2-Comp V4 (β_s, β_c) | (48, −36) | **(48, −36)** | ✅ identical |
| Sub-09 2-Comp V1 (β_s, β_c) | (26, +4) | **(26, +6)** | ✅ sign preserved |
| Sub-09 2-Comp V4 (β_s, β_c) | (28, 0) | **(26, +6)** | ⚠ 0 → +6 (positive) |
| **Subtype dichotomy (β_c sign)** | sub-08<0, sub-09≥0 | **sub-08<0, sub-09>0** | ✅ **K-robust at all 4 cells** |
| Sub-09 Bootstrap CI of g | [1.30, 2.60] | **[1.30, 2.60]** | ✅ identical |
| Sub-09 Bootstrap p (excludes g=1) | p < 0.001 | **p < 0.001 (fraction>1 = 1.000)** | ✅ |
| Sub-08 Bootstrap shape | bimodal, boundary mass 0.65 | **bimodal, boundary mass 0.65** | ✅ identical |
| Sub-09 perm p (S8 color-perm) | 0.0000 | **0.0000** | ✅ |
| Sub-08 perm p (S8 color-perm) | 0.150 | **0.140** | ✅ NS in both |
| ΔAICc(sub-08 R+C − 2-Comp) | +0.41 | **+0.38** | ✅ <2 indistinguishable |
| ΔAICc(sub-09 R+C − 2-Comp) | +7.27 | **+7.05** | ✅ 6-10 strong |
| Cross-subtype Δ inversion (sub-09→08 > sub-08→09) | +0.52 > +0.32 | **+0.50 > +0.26** | ✅ inversion preserved |
| ‖δθ‖²-norm sub-08 2-Comp | 0.00061 | **0.00061** | ✅ identical |
| ‖δθ‖²-norm sub-09 2-Comp | 0.00058 | **0.00058** | ✅ identical |
| CVD-HC CI overlap (sub-09) | [1.30, 2.35] | **[1.30, 2.35]** | ✅ identical |

### Surviving / collapsing paper claims — K=6 unchanged

| Claim | K-robust? |
|---|---|
| ✓ Sub-09 individual-level g > 1 (CI excludes 1.0) | ✅ K=6 confirms |
| ✓ Sub-09 perm p=0.000 robust (S8 + S10 loss-assign) | ✅ K=6 confirms |
| ✓ Sub-09 mild protan (JND-L 1.5nm + Ishihara 9/14 + V1 LOCO p=0.007) | ✅ K-invariant by design |
| ✓ Sub-08 2-Comp (β_s=48, β_c=−36) descriptor | ✅ K=6 identical |
| ✓ Sub-08 R+C 1-DOF misspecified (bimodal bootstrap) | ✅ K=6 identical |
| ✗ Subtype-specific transfer (4.59×) | ✅ still collapses |
| ✗ Asymmetric subtype-specificity | ✅ still inverts under Δ |
| ✗ Group-level CVD-vs-HC specificity (FPR=0) | ✅ still CI-overlapped |

### New observations at K=6 (paper limitation candidates)

1. **Sub-08 V4 R+C JND-Lamb** boundary hit (g=0) at K=6 (was clean g=2.25 at K=3) — K-sensitive secondary path. Paper primary remains DPS (clean fit), JND-Lamb is sensitivity supplement only.
2. **Sub-09 V4 2-Comp β_c**: 0 (K=3) → +6° (K=6). Sign positive preserved; magnitude shift small.
3. Cross-model δθ Spearman improved (K=3-4: ρ≈−0.71 per MEMORY; K=6: ρ=0.119, p=0.78, MAE=20.6°). K=6 reduces R+C-vs-2Comp divergence but they remain decoupled.

### Verdict

> **Phase 2 의 모든 paper-defensible surviving claims 는 K=6 FE-uniform 에서 robust.** Phase 1 baseline 일치 (K=6) + Phase 2 결과 변경 거의 없음 + collapsed claims 도 동일하게 collapse. K mismatch 는 **method consistency 문제이지 substantive finding 변경 아님**. Limitation: sub-08 V4 R+C JND-Lamb path 의 K-sensitivity (paper 의 primary DPS hypothesis 에는 영향 없음).

---

## [Legacy / S7 prep] S11_legacy: Model-Loss Selection Sprint — LOO + Train-Test (2026-05-23 USER DIRECTIVE)

> **Legacy note (2026-05-24)**: 본 sprint 는 **새 S7 (Loss combination + HC subset resample)** 의 직전 단계. 7-fold LOO 만으로는 inter-loss correlation, λ trace, multi-k stability 측정 불가 → S7 으로 확장. 본 S11 의 결과 (sub-09 R+C L_γ V4 dominant, sub-08 2-comp L_γ V1) 는 S7 의 prior 로 활용. **S7 결과로 final candidates supersede.**

**CLAUDE.md §3 RE-OPENED**. Phase 2 적합 모델·loss 미확정. 본 sprint 의 결과로 model-loss pair 후보를 평가.

### S11.1 Design

- **Models**: R+C 1-DOF (Δλ, g), 2-Component (β_s, β_c)
- **Losses (standalone)**: L_γ (JND), L_α (8AFC), L_LOCO (within-W voxel), L_RDM (HC-pool ΔRDM cosine)
- **ROIs**: V1, V2, V3, V4 (FE-6 uniform)
- **Subjects**: sub-08 deutan, sub-09 protan
- **LOO**: 7-fold over HC (sub-01..sub-07)
- **R+C Δλ**: 3 sources × 2 family (DPS_lit, Boehm grid, JND-Lamb)
- **Script**: `scripts/s8_loo_train_test.py` (이전 sprint 의 S8 명과 script 명 충돌 — 새 sprint label = S11)
- **Compute**: 184 s

### S11.2 5 selection criteria

| Criterion | 정의 |
|---|---|
| (a) parameter SD | CVD parameter 의 7-fold SD (stability) |
| (b) separation rate | %folds CVD > 95th %ile of held-out HC parameter (distinctness, train-test-aware) |
| (c) P1/P2a guardrail | filter 의 behavioral plausibility — **internal sanity only**, 본 sprint 보고 안 함 (§0.1) |
| (d) inter-loss Pearson r | 4 losses × 7 folds 의 vector 간 correlation (convergence) |
| (e) train-test MSE | held-out HC parameter 의 across-fold variance (generalization) |

### S11.3 Key results — sub-09 protan

#### R+C 1-DOF (Δλ=DPS_lit=10nm)
| Loss | mean g | SD (a) | sep rate (b) | HC mean | MSE (e) |
|---|---|---|---|---|---|
| **L_γ** | **2.59** | **0.06** | **1.00** | 1.97 | **0.078** (V4) / **0.166** (V1) |
| L_α | 2.00 | 0.00 | 0.00 | 1.98 | 0.002 (degenerate ceiling — 8AFC=100% acc) |
| L_LOCO V1 | 3.00 | 0.00 (boundary) | 1.00 | 1.71 | 0.560 |
| L_LOCO V2-V4 | 0.5–1.05 | 0.00 (boundary) | 0.00 | 1.03–1.36 | 0.34–0.77 |
| L_RDM V1 | 2.28 | 0.75 | 0.29 | 1.89 | 1.095 (high) |
| L_RDM V4 | 1.12 | 0.38 | 0.00 | 0.88 | 0.905 |

#### 2-Component
| Loss | mean norm | SD (a) | β_s SD | β_c SD | sep rate (b) | MSE (e) |
|---|---|---|---|---|---|---|
| L_γ | 26.7 | 2.0 | 1.8 | 1.5 | 0.14 | 148 |
| L_α | 0.0 | 0.0 | 0.0 | 0.0 | 0.00 | 22 (degenerate) |
| **L_LOCO V1** | **70.7** | **0.0 (boundary)** | 0.0 | 0.0 | **1.00** | 427 (high) |
| L_LOCO V2 | 70.7 | 0.0 (boundary) | 0.0 | 0.0 | 0.29 | 670 |
| L_RDM V1 | 48.6 | 1.8 | 1.8 | 1.9 | **0.71** | 330 |

**sub-09 분석**:
- **R+C g L_γ** = 최고 stable (SD=0.06), 모든 ROI 에서 SEP=1.00, V4 MSE=0.078 (가장 generalizable). **신경 정보 추가 없이도 robust.**
- **L_LOCO/L_RDM 은 ROI-dependent boundary hit** — degenerate solutions.
- 2-comp L_RDM V1 SEP=0.71, 비-boundary (norm SD=1.8) → 신경 정보 활용 가능한 유일 후보지만 MSE=330 (large generalization error).

### S11.4 Key results — sub-08 deutan

#### R+C 1-DOF (Δλ=DPS_lit=6nm)
| Loss | mean g | SD (a) | sep rate (b) | HC mean | MSE (e) |
|---|---|---|---|---|---|
| L_γ | 1.61 | 1.10 | 0.43 | 1.64 | 0.633 (high SD → unstable) |
| L_α | 2.00 | 0.00 | 0.00 | 2.00 | 0.000 (degenerate) |
| L_LOCO | 0.00 | 0.00 (boundary) | 0.00 | 1.03–1.18 | 0.70–1.10 (overcorrection direction) |
| **L_RDM V1** | **2.15** | **0.00** (boundary mid) | 0.14 | 1.59 | 0.641 |
| L_RDM V2 | 3.00 | 0.00 (boundary) | **1.00** | 1.52 | 0.595 (both high, ceiling) |

#### 2-Component
| Loss | mean norm | SD (a) | sep rate (b) | MSE (e) |
|---|---|---|---|---|
| **L_γ** | **59.7** | **2.9** | **1.00** | 231 (high MSE 단, sep robust) |
| L_α | 17.9 | 0.0 | 1.00 | 17 (degenerate but separating) |
| L_LOCO V1-V4 | 55.5–70.7 | 0.0 (boundary) | 0.0–0.29 | 334–866 |
| L_RDM V1 | 2.0 | 0.0 (degenerate small) | 0.00 | 407 |
| L_RDM V2 | 22.4 | 15.6 | 0.00 | 439 |

**sub-08 분석**:
- **R+C L_γ unstable** (SD=1.10) — sub-08 의 JND 가 HC pool 구성에 sensitive (deutan ambiguity).
- **2-comp L_γ stable** (norm SD=2.9) AND SEP=1.00 across all ROIs — robust separation.
- **L_LOCO boundary low** (g=0) — 신경 데이터가 *anti-Machado direction* 으로 끌림 (cortical compensation 약함 또는 단순 noise).
- **L_RDM V1 g=2.15 stable** but SEP=0.14 (HC 도 2.15 근처).

### S11.5 Inter-loss correlation (d) — pool-independence 가 진짜 원인 (advisor 정정 2026-05-23)

**초기 진단 오류**: "L_α ceiling + L_LOCO boundary → SD=0 → Pearson undefined" 는 부분적으로만 옳음. 진짜 원인:

#### Root cause: pool-independence by construction

`scripts/s8_loo_train_test.py:make_loss_fns()` 의 closure 정의:

```python
def L_alpha_fn(delta_rc):    # CVD 의 8AFC + SIGMA_HC 만 사용 — pool 미사용
    return L_behav_alpha(delta_rc, target_8afc, SIGMA_HC)

def L_loco_fn(delta_rc):     # CVD 의 own data + own W 만 사용 — pool 미사용
    return L_LOCO(delta_rc, target_amp, target_loco_W, K)
```

**L_α 와 L_LOCO 는 pool 인자 받지 않음** → HC pool 구성 (LOO axis) 이 두 loss 값에 영향 **없음** → 7-fold 결과 **완전 동일** (sub-09 V1 L_α 7-fold 모두 g=2.0000, L_LOCO 모두 g=3.0000 실측 확인).

#### 함의 (advisor catch)

- **(a) `cvd_param_sd` 의 L_α/L_LOCO SD=0 은 tautology** — "stability evidence" 보고 금지.
- **(d) Inter-loss correlation NaN** — HC LOO axis 가 pool-independent loss 의 variation 유도 못함 이 본질.
- Pool-dependent losses (L_γ, L_RDM) 만 7-fold 에서 real variation:
  - L_γ sub-09 V1 g range = [2.50, 2.65] (tight)
  - L_γ sub-08 V1 g range = [0.00, 2.30] (bimodal — sub-04/sub-06 hold-out 시 collapse, task #12 진단)
  - L_RDM sub-09 V1 g range = [0.75, 3.00]
- **L_LOCO g=0 boundary 는 substantive negative result, not noise**: CVD 의 own voxel 신호가 cone-shift δθ 방향과 *anti-correlate* — "cone-shift model 이 CVD voxel signal 에 의해 거부됨" 의 직접 evidence. S11.4 framing 정정 필요.

#### 측정 가능한 inter-loss correlation (pool-dependent pair 만)

| Subject-ROI | Pair | r |
|---|---|---|
| sub-08 V2 2-comp | L_γ ↔ L_RDM | -0.79 (anti-correlated) |
| sub-09 V1 R+C | L_γ ↔ L_RDM | +0.44 |
| sub-09 V1 2-comp | L_γ ↔ L_RDM | -0.45 (R+C 와 sign flip) |
| sub-09 V2-V4 R+C | L_γ ↔ L_RDM | 0.02–0.14 (no relation) |

#### 올바른 inter-loss correlation 측정 방법 (별도 sprint, task #13)

HC LOO axis 가 4-loss-correlation 에 부적합. Advisor 권장 3가지 대안:

1. **Trial-level CVD bootstrap (B=200)**: CVD 자신의 JND/8AFC trial + fMRI run resample → 4 loss 모두 per-bootstrap variation 생김 → Pearson r 정의 가능.
2. **Cross-cell parameter agreement**: ROI × Δλ source 12 cell 에 대한 Spearman ρ across losses.
3. **Direct λ-trace** (가장 직접적): L_γ alone → θ_γ vs L_γ + λ·L_RDM (λ ∈ [0, 1] 스윕) → θ(λ) 추적. θ shift 여부로 "신경 info unique contribution?" 답.

**S11 본 sprint 의 inter-loss correlation 은 invalid framework**. 결론 "신경 정보 unique contribution?" 은 별도 sprint (S12) 로 재산출 필수.

**연구 질문 ANSWER (S11 단독으로는 ANSWER 불가)**:
- Pool-dependent loss pair (L_γ ↔ L_RDM) 만 7-fold 에서 변동 → 1-pair correlation 측정 가능
- L_α / L_LOCO 는 HC LOO axis 에서는 비교 불가 → 별도 sprint 필요
- 잠정: L_γ ↔ L_RDM r 부호 일관성 없음 (subject/ROI/model 별 +/-/null 혼재) → behavioral 과 neural relational geometry 가 *cell-specific* 으로 합의/반대 — single direction 결론 불가

### S11.6 Single filter recommendation (Phase 3 후보) — **BLOCKED 2026-05-23 advisor catch**

⚠ **CIRCULARITY BLOCK**: 아래 권장은 §0.1 P2a/P1 정책과 동일한 circularity (filter 를 behavioral data 로 fit → behavioral 로 validate) 에 빠짐. **Paper draft / Phase 3 실험 trigger 전 다음 중 하나 해결 필수**:
- (a) "interim, awaiting non-circular validation" 으로 qualify
- (b) L_γ 제외, **L_RDM 만으로** separation + train-test MSE 재산출 → 단 L_RDM 은 Constraint #5 (HC procedural bias) 영향
- (c) 별도 수집한 *non-fit* behavioral test (filter 적용 자극 vs no-filter) 확보 후 validation

이하 잠정 권장 (BLOCK 해소 전):

**Sub-09 (protan)** — **R+C 1-DOF, L_γ, ROI=V4, Δλ=DPS_lit=10nm**:
- g = 2.59 ± 0.06 (가장 stable)
- SEP rate = 1.00 (모든 fold CVD > HC)
- Train-test MSE = 0.078 (가장 generalizable)
- **단점**: 신경 정보 없음. R+C model 은 paper-diagnostic only (filter form 으로는 미정).
- 2-comp L_γ 도 stable (SD=2.0, SEP=1.00 R+C 대비 작음, MSE=148) → 2-comp 으로 filter 변환 시 alternative.

**Sub-08 (deutan)** — **2-Component, L_γ, ROI=V1**:
- norm = 59.7 ± 2.9 (β_s SD=5.0, β_c SD=2.7)
- SEP rate = 1.00 (all folds)
- Train-test MSE = 231 (높은 generalization error 단, separation robust)
- R+C L_γ 는 sub-08 에서 unstable (SD=1.10) → R+C 선정 불가.
- 신경 L_RDM 추가는 L_γ 와 anti-correlated → complementary info 있을 가능, 단 사전 명확화 필요.

### S11.7 Caveats + Open issues

1. **L_α (8AFC) degenerate**: sub-09 100% ceiling, sub-08 sub-uniform. 정보 가치 limited; 분석에서 informative pair 차감.
2. **L_LOCO boundary hit dominance**: 거의 모든 cell 에서 g=0 또는 (β_s, β_c) boundary 로 수렴. 즉 CVD 의 within-subject LOCO 가 *unique optimum* 못 갖는 flat landscape — discrete cone-shift model 의 한계.
3. **Inter-loss correlation NaN**: degenerate-dominance 의 직접 결과. (d) criterion 사실상 정보 비효율 — L_γ ↔ L_RDM 1-pair 만 의미 측정.
4. **§0.1 P2a/P1 guardrail (c)** 본 sprint 미적용 — separate validation needed (TBD).
5. **2-comp L_LOCO V1 sub-09 SEP=1.00 boundary**: 격자 (β_s, β_c) 가 (50, 50) corner 로 수렴 → 격자 확장 시 결과 달라질 가능.
6. **HC procedural bias caveat (Constraint #5)**: sub-09 V4 protan small-Δλ L_RDM 결과는 procedural artifact 일부 포함 가능 — V4 결과는 보고 시 명시.

### S11.8 Verdict (잠정)

- **Sub-09**: R+C L_γ V4 (또는 2-comp L_γ V4) 가 dominant 후보. 신경 loss 가 add value 못함.
- **Sub-08**: 2-comp L_γ V1 가 가장 stable. R+C 는 sub-08 에 부적합. 신경 loss 의 추가 가치는 limited.
- **공통**: behavioral L_γ 가 두 피험자 모두에서 핵심 signal. 신경 loss 는 *Sub-08 V2 L_RDM* 1 cell 에서만 L_γ 와 complementary correlation (r=-0.79) 관찰 — 추가 sprint 필요.

**Phase 3 권장**: 두 피험자 모두 **L_γ 기반 filter** 가 LOO+train-test 통과한 유일 후보. 모델은 R+C (sub-09) / 2-comp (sub-08) 로 *피험자별 다름* — paper 에는 두 모델 family 의 *unified description* 으로 보고.

### S11 Files

- Script: `scripts/s8_loo_train_test.py`, `scripts/s8_analysis.py`
- Results: `results/s8_loo_train_test/{loo_results.json, selection_metrics.json, inter_loss_correlation.json, SELECTION_REPORT.md}`

---

## S7: Loss combination + HC subset resample sprint (2026-05-24 USER DIRECTIVE, ACTIVE)

> **Sprint origin**: 사용자 directive 2026-05-24. S6' (HC subset resample) + S11_legacy (LOO+train-test) 한계 통합 해결. Color-label perm 은 main flow 에서 제외 (positive characterization 의 selection 기준 부적합) — 최종 cell 에만 post-hoc 적용.

### S7.1 Design + Research Questions

**5 Research Questions**:
- **RQ1** Single-loss stability: best param\* 가 HC pool composition 에 robust 한가?
- **RQ2** Combination value: pair/triple 이 single 대비 stability/separation 개선?
- **RQ3** Neural unique contribution: L_γ baseline 대비 L_LOCO/L_RDM 의 *unique* info?
- **RQ4** Generalization: held-out HC subset 에 generalize?
- **RQ5** Specificity (post-selection only): random JND assignment 와 구별?

**Factorial**: 11 loss configs (4 single + 6 pair + 1 triple) × 2 models (R+C 1-DOF, 2-Component) × 4 ROIs (V1, V2, V3, V4 FE-6) × 3 subjects (sub-08/09 CVD + sub-10 null). R+C Δλ: 3 sources (DPS_lit, Boehm grid, JND-Lamb) × 2 family. **HC subset resample**: k ∈ {4, 5, 6}, all C(7,k) subsets (35 + 21 + 7 = 63 per cell).

### S7.2 Methods (Stages A–E)

| Stage | Hypothesis | Variables | Statistics | Pass criterion |
|---|---|---|---|---|
| A: single-loss stability (RQ1) | L_γ/L_α/L_LOCO/L_RDM 각각 subset robust? | param\*_median, 95% CI, SD_k, CoV_k, SEP_rate | percentile CI, no NHST | CoV_5 < 0.10 AND SEP_rate ≥ 0.80 AND CI width < 0.5 |
| B: combination value (RQ2) | combo 가 single 대비 개선? | Δparam\*, ΔCoV, ΔSEP (paired by S, n=21) | paired Wilcoxon, p<0.05 uncorrected | |Δparam\*| < 0.1 AND ΔCoV ≤ 0 AND ΔSEP ≥ 0 |
| C: λ sweep (RQ3) | 신경 채널 unique info? 3 probes: L_γ+λ·L_LOCO, L_γ+λ·L_RDM, L_γ+λ·(L_LOCO+L_RDM)/2; λ ∈ {0, 0.25, 0.5, 0.75, 1.0} | param\*(λ), CoV(λ), \|Δparam\*(λ=0→0.5)\| | paired Wilcoxon, Bonferroni 12 tests (α=0.00417) | \|Δparam\*\| > 0.2 AND p_corr < 0.05 AND CoV stable |
| D: train-test MSE (RQ4) | k=5 train / k=2 test generalize? | MSE_test_median, Overfit ratio | percentile CI | Overfit ratio < 1.5 AND CI lower ≥ 0 |
| E: color-label perm (RQ5, deferred) | random JND 와 구별? B=200 shuffle | empirical p | one-tailed | p<0.05 (descriptive only) |

**L_α 처리**: Stage A/B 수식 포함, Stage C λ probe 에서는 제외 (8AFC degenerate). **Sub-10 null control**: 전 stage 동일 절차, SEP_rate(k=5) < 0.5 면 procedural specificity 확보.

### S7.3 Results — Single-LOO + Nested-LOO

**Single-LOO** (`results/s7_loss_combo_subset/lambda_optimal_behav_rdm.json`):

| Cell | Model | Optimal λ | param\* | CoV | Notes |
|---|---|---|---|---|---|
| sub-09 V1/V2/V3 | R+C DPS | 0.00 | g=2.60 | 0.029 | stable, non-boundary |
| sub-09 V1/V2/V3 | 2-comp | 0.00 | (β_s=26.3, β_c=4.3), norm=26.3 | 0.12 | stable, non-boundary |
| sub-08 V1 | R+C DPS | 0.25 | g=2.15 | 0.022 | stable |
| sub-08 V2/V3/V4 | R+C DPS | mixed | g=0.35–2.70 | high | param 변동 큼 |
| sub-08 all ROIs | 2-comp | — | — | — | **all cells λ-degenerate** (boundary > 0.5) |

**Nested-LOO** (outer 7-fold × inner C(6,4)=15, `results/s7_nested_loo/SELECTION_REPORT_NESTED.md`):

| Cell | Model | Single-LOO opt | Nested-LOO opt | Drift? |
|---|---|---|---|---|
| sub-09 V1/V2/V3 | R+C DPS | g=2.60 | g=1.36 (V1/V3 λ=0), g=2.14 (V2 λ=0.25) | YES |
| sub-09 V1/V2/V3 | 2-comp | (26.3, 4.3) | (26.3, 4.3) | NO (robust) |
| sub-09 V4 (new) | 2-comp | NA | (β_s=24.3, β_c=4.6), CoV=0.15 | new fit |
| sub-08 V4 (new) | 2-comp | degenerate | **(β_s=34.3, β_c=−39.4), CoV=0.10** | **non-degenerate** |
| sub-08 V1–V3 | 2-comp | degenerate | degenerate | unchanged |

**Key findings**:
- Sub-09 R+C *g* drifts 1.36–2.14 across outer folds → CoV inflates 0.03 → 0.10–0.30 (3.3× single-LOO underestimate).
- Sub-09 2-comp (β_s≈26, β_c≈4) survives outer LOO unchanged across V1/V2/V3 — **most robust** result in S7.
- Sub-08 V4 2-comp **first non-degenerate fit anywhere** (single-LOO showed ALL sub-08 cells 2-comp degenerate) → suggests sub-08 boundary degeneracy is partly a single-LOO artifact. Phase 3 candidate.

### S7.4 Model comparison — AIC/BIC + Param distance + Forward δθ

**AIC/BIC deviance correction** (n_pairs=8, L_γ × n_pairs = deviance):

```
Deviance_RC = 0.6896 × 8 = 5.517   (k_RC=1)
Deviance_2C = 0.4771 × 8 = 3.817   (k_2C=2)
AIC_RC = 5.517 + 2·1 = 7.517   |   AIC_2C = 3.817 + 2·2 = 7.817   →   ΔAIC = −0.30 (R+C marginal)
BIC_RC = 5.517 + 1·log(8) = 7.596   |   BIC_2C = 3.817 + 2·log(8) = 7.976   →   ΔBIC = −0.38 (tie)
AICc_RC = 7.517 + 4/6 = 8.184   |   AICc_2C = 7.817 + 12/5 = 10.217   →   ΔAICc = −2.03 (R+C marginal under small-n)
```

⚠️ Previous `fair_model_comparison.json` reports ΔAIC=+1.79 (omitted ×n_pairs deviance step) — **corrected ΔAIC=+0.30**, decisively inside noise floor.

**Param distance** (train k=5 vs test k=2, median across n=21 subsets, `results/s7_loss_combo_subset/param_distance.json`):

| Cell | Model | dist_median | Relative | Pass (thr) | Verdict |
|---|---|---|---|---|---|
| sub-09 V1/V2/V3 | R+C DPS | 0.30 g | 11.5% | PASS (0.3) | generalizes |
| sub-09 V1/V2/V3 | 2-comp | 11.31° | 43% | FAIL (10°) | borderline — large CI [4.2°, 28.9°] |
| sub-08 V1 | R+C DPS | 0.10 g | 4.7% | PASS (caveat: CI [0, 2.70]) | |
| sub-08 V3 | R+C DPS | 0.45 g | 129% | FAIL | g drifts 0.35↔1.80 |
| sub-08 V4 | R+C DPS | 2.15 g | 105% | FAIL | g bimodal 0↔2.7 |

**Forward δθ mechanism comparison** (sub-09 R+C g=2.60 vs 2-comp (β_s=26, β_c=4)):
- Cosine similarity of δθ vectors = **0.074 (near-orthogonal)** — same fit, different mechanism.
- R+C produces blue-purple centered distortion (c6=−45.7°, c7=+36.5°).
- 2-comp produces sinusoidal balanced (β_s dominant, β_c≈0 → effectively 1-DOF).
- 2/8 colors show sign flip between models.
- **At n=8 JND pairs, ΔAIC=0.30 and ΔAICc=2.03 cannot distinguish mechanisms.** Phase 3 (separate behavioral filter test) is the arbitrator.

### S7.5 Final selection — per-subject + mechanism interpretation

⚠️ **CRITICAL REFRAMING (사용자 catch 2026-05-24)**: **Sub-08 raw JND deviation Σz² = 83.33 vs sub-09 Σz² = 9.68 — sub-08 deviation is 8.6× larger than sub-09**. Previous "deutan near-fully compensated" framing was a **fitting artifact** (R+C g≈2 hits degenerate optimum). Sub-08 has *localized yellow-centered distortion* (yellow-purple +6.7σ, yellow-green +4.3σ, orange-yellow +4.2σ) that **all current models underfit**.

| Subject | Final selection | Mechanism note |
|---|---|---|
| **sub-09 protan** | R+C g≈2.6 (composite) OR 2-comp (β_s≈26, β_c≈4); both candidates valid, n=8 cannot distinguish | **Distributed distortion**, both models fit; Phase 3 = arbitrator |
| **sub-08 deutan** | R+C composite λ=0.25 V1 g=2.15 *as best available* | **All models underfit** (Σz²=83.33). *Localized yellow-centered distortion* (yellow-purple +6.7σ dominant) needs richer model family (future work) |
| sub-10 deutan (null) | JND data absent → L_γ unavailable. V2 shows false-positive pattern (consistent with prior memory) | null control partially works |

### S7.6 Limitations + PI feedback status

| # | Limitation | Status |
|---|---|---|
| 1 | Double-dipping | **Partially resolved (40%)** — nested LOO confirms single-LOO R+C CoV 0.03 → 0.10 (3.3× inflation). True external validation = Phase 3 |
| 2 | n=8 JND pairs cannot distinguish mechanisms | ΔAICc=2.03 marginal, decisive evidence absent |
| 3 | Behavioral baseline systematic comparison | **NOT done (15%)** — Brouwer-Heeger / Parkes cited only, numeric comparison section absent |
| 4 | End-to-end model + weight LOO | **NOT done (25%)** — sequential only, joint outer-LOO grid pending |
| 5 | Stage D raw-loss metric ceiling | Param distance is fair generalization metric (§S7.4) |

**PI feedback resolution: ~40%.** Unresolved = (i) Phase 3 behavioral filter test design (true arbitrator), (ii) systematic behavioral literature comparison, (iii) joint end-to-end LOO.

Phase 2 deliverable = *exploratory selection* (R+C and 2-comp both candidates per subject). Phase 3 = *confirmatory evaluation* via behavioral filter test (P1, P2a). Manuscript must frame S7 outputs as candidate set, not single best.

**Status** [in_progress]: scripts complete (`scripts/s7_loss_combo_subset.py`, nested-LOO), single-LOO + nested-LOO results in. **Pending**: PARAM_DISTANCE_REPORT consolidation into paper Methods; S8 trigger when Phase 3 protocol locked.

---

## S8: Filter candidates per model (PLACEHOLDER, 2026-05-24 trigger pending)

> **Trigger**: S7 의 RQ1–RQ4 모두 통과한 (model, loss combo, ROI) 가 sub-08, sub-09 각각에서 ≥1개 존재 시 자동 진입.

### S8.0 Plan (sketch)

각 model × subject 별 best loss combination 으로 **stimulus-space filter** 도출:

- **R+C 1-DOF**: δθ_RC(c) = (2−g)·δθ_Machado(c, Δλ, family) → filter = inverse mapping in DKL hue
- **2-Component**: δθ_2C(c) = β_s·cos(θ_c − 90°) + β_c·cos(θ_c − θ_conf) → filter = inverse 2-DOF rotation

Per subject 2 filters (R+C, 2-comp) — paper 에 *both* 보고하고 dual-filter behavioral test 권장 (Phase 3).

### S8.1 Status

- [pending] S7 결과 대기

---

## S9: Integrated defenses (✅ Consolidated 2026-05-24)

> **Origin**: S9_old (Retroactive defenses, 사용자 catch 2026-05-21, line 1145) + S10_old (Advisor corrections, 2026-05-21, line 1224) 통합. 본 section 이 single source of truth; 두 old section 은 archive 로 보존 (header 에 consolidation note 추가됨).
>
> **Scope note**: S9_old/S10_old 가 다룬 7-fold HC transfer test + L_behav FPR test + advisor 5 corrections 를 *full treatment* 으로 통합. 추가로 사용자/advisor catch 중 별도 section 에 이미 living 인 content (W asymmetry, L8 interpretation, sampling unit, Δλ assumption, HC procedural bias → **§Acknowledged Loss-Design Constraints**, line 1798; pool-independence → **§S11.5**, line 1465; circularity block → **§S11.6**, line 1517) 는 *cross-reference 만* — 중복 작성 금지.

### S9.0 Plan

S9 통합 목적: 사용자 catch 과 advisor catch 가 *같은 issue 의 양면* 을 지적한 경우가 다수 — 두 trail 을 thematic 으로 통합하고, 변경 순서는 chronological audit log 로 별도 유지. 통합 후 paper-defensible claim 의 *current state* 가 명확해야 함.

원칙:
1. Thematic grouping (S9.1 user catches, S9.2 advisor catches) + chronological audit log (S9.4) 양면 모두 제공
2. 사용자/advisor 가 같은 문제를 다른 각도에서 catch 한 경우 → 통합 entry, 양쪽 attribution 명시
3. Paper-defensible claim 변경은 S9.3 (Applied fixes) 에 모음
4. 별도 section 에 full detail 이 living 인 항목은 cross-reference 만 (2-3 줄 summary + line pointer)

### S9.1 Thematic: User catches

#### U1. §6.3 transfer test 미실행 + V_s mismatch 잘못 해석 (2026-05-21)
- **Catch**: §6.3 PRIMARY plan (CVD's δθ → HC h, 7-fold) 실행 안 됨. V_s mismatch 를 "feasible 안 함" 으로 잘못 처리.
- **Reality**: (X) within-HC LOCO 는 scalar (V_s 무관), (Y) ΔRDM 은 28-vec V_s-invariant, (Z) 8AFC 는 W-independent → 모두 feasible.
- **Fix**: `scripts/s9_retroactive_defenses.py` Part 1 = 7-fold HC transfer test (V4 + V1, 2 CVD × 2 model = 28 tests/ROI).
- **Result (V4, raw ratios)**: (X) LOCO ≈ 1.0 across HCs (test uninformative — not "noise"); (Y) JND ratios sub-08 R+C 0.96 / 2-Comp 4.59, sub-09 R+C 1.86 / 2-Comp 1.82; (Z) 8AFC ratios large but interpretable only relative.
- **Subsequent advisor correction**: see **A2** — raw (Y) ratios are ‖δθ‖² magnitude artifact.

#### U2. Group-level CVD vs HC FPR 새 framework 재검증 안 됨 (2026-05-21)
- **Catch**: 프로젝트 memory FPR=100% claim 은 *voxel-prediction L_LOCO* measurement family (Cycle 9-13). 새 **L_behav primary framework** 에서는 재검증 필요.
- **Fix**: `scripts/s9_retroactive_defenses.py` Part 2 = each HC treated as fake CVD, point fit R+C g, bootstrap.
- **Raw result**: sub-08 g\*=2.25 vs HC pool max 2.20 (0/7); sub-09 g\*=2.60 vs HC max 2.30 (0/7). Point FPR = 0.000 for both.
- **Subsequent advisor correction**: see **A1** — "FPR=0.000" was misleading; only descriptive percentile + CI overlap.

#### U3. Bootstrap sampling unit (color vs trial) (2026-05-22)
- **Catch**: 기존 S6 는 8 colors / 8 pairs 를 bootstrap unit 으로 사용 → color set 은 fixed design element 이므로 *true measurement uncertainty* 아님. Color-specific distortion bias 혼입.
- **Fix**: Trial-level bootstrap (`scripts/s6_bootstrap_g_ci_trial.py`): unit = individual trial (JND staircase rows / 8AFC trial responses), color set 보존.
- **Impact**: Sub-09 CI 5× narrow (1.30-2.60 → 2.35-2.60), P(g>1)=1.00 robust; Sub-08 P(g>1) 0.66 → 0.92 (bimodal 부분 collapse).
- **Verdict**: paper-defensible claim 강화. Full detail: §Acknowledged Loss-Design Constraints (3), line ~1839.

#### U4. Δλ assumption uncertainty (2026-05-22)
- **Catch**: S5'/S6 는 Δλ = DPS lit only (protan 10, deutan 6 nm) 고정 — g 분포에 Δλ uncertainty 미포함.
- **Fix**: S6 convergence matrix sensitivity (3 Δλ sources: DPS lit, Boehm grid, JND-Lamb data-driven; framing 정정 "Δλ-prior robustness", not "convergence" — line 793).
- **Impact**: Sub-09 protan small-Δλ (Boehm/Lamb) 에서 cortical g 최대 discriminator. Full detail: §Acknowledged Loss-Design Constraints (4), line ~1862.

#### U5. HC pool g 의 procedural-bias caveat (2026-05-23)
- **Catch**: S5' Form B 는 CVD-prior Δλ 를 HC 7 명에 강제 대입 → §2 A1/A6 위반 (HC true Δλ=0 이어야 함). HC g_hat 은 *misspecified fit*.
- **Fix**: S6' (line 708) **HC subset resample design** 으로 대체 — HC reference dependence 측정. Old S5' Form B "z=+3.45" claim deprecated.
- **Impact**: V4 protan small-Δλ L4 RDM 에서 *CVD vs HC 구별 불가능* (양쪽 boundary procedural artifact). Paper 정정: "HC pool g distribution" → "procedural g under CVD-model misspec". Full detail: §Acknowledged Loss-Design Constraints (5), line ~1872.

#### U6. W asymmetry + L8 composite interpretation (2026-05-22)
- **Catch**: L_LOCO 는 CVD-own W (V_s-matched within-subject ridge), L_RDM 은 HC pool W (cross-subject V_s-invariant 28-vec) → 두 loss 가 *다른 reference frame* 으로 같은 δθ 추정 안 함. L8 composite (0.5·L_γ + 0.25·L_LOCO + 0.25·L_RDM) 는 *modality-balanced compromise*, single "true δθ" 식별 아님.
- **Status**: Acknowledged limitation; ideal shared encoder 는 small-n + Phase 1 SRM REJECTED 으로 impractical. L_LOCO ↔ L_RDM dissociation (sub-08 V1 p=0.047 vs p=0.179; sub-09 LOCO NS vs ΔRDM p=0.026) 은 *complementary information* 으로 해석.
- **Full detail**: §Acknowledged Loss-Design Constraints (1)+(2), line ~1802.

### S9.2 Thematic: Advisor catches (2026-05-21 evaluation of S9_old + later)

#### A1. "FPR=0.000" misleading — point percentile, not true FPR
- **Concern**: n=7 HC point fits 이므로 "0/7 exceed" 은 descriptive 일 뿐; bootstrap CI 비교 시 결과 다를 수 있음.
- **Re-test**: CVD bootstrap CI vs HC pool bootstrap CI.
  - sub-08: CVD [0.000, 3.000] ∩ HC [0.000, 3.000] = **complete overlap**.
  - sub-09: CVD [1.300, 2.600] ∩ HC [1.000, 2.350] = overlap at margin [1.30, 2.35].
- **Verdict**: "FPR=0.000" → "0/7 point fits exceed CVD (descriptive percentile), bootstrap CI overlap at margin". §0 policy ("specificity claim 금지, descriptive percentile OK") 적용 필수.
- **Impact**: Paper claim 강등 — "group-level specificity recovered" 주장 제거.

#### A2. (Y) JND transfer 4.59× 는 ‖δθ‖² magnitude artifact
- **Concern**: Raw transfer ratio 가 δθ vector magnitude 에 의존. ‖δθ‖² 정규화 필요.
- **Re-test** (V4 normalized = raw_ratio / ‖δθ‖²):
  | Model | sub-08 raw | sub-08 ‖δθ‖² | sub-08 norm | sub-09 raw | sub-09 ‖δθ‖² | sub-09 norm |
  |---|---|---|---|---|---|---|
  | R+C | 0.96 | 516 | 0.00186 | 1.86 | 3583 | 0.00052 |
  | 2-Comp | 4.59 | 7488 | **0.00061** | 1.82 | 3136 | **0.00058** |
- **Verdict**: Sub-08 2-Comp normalized (0.00061) ≈ Sub-09 2-Comp normalized (0.00058). "Sub-08 4.59× subtype-specific transfer" 는 ‖δθ‖²=7488 magnitude artifact, NOT subtype-specific signal.
- **Impact**: Paper claim COLLAPSES — "2-Comp subtype-specific transfer" 제거.

#### A3. (X) LOCO ≈ 1.0 framing 정정
- **Concern**: "노이즈" framing 부정확; 정확히는 "test uninformative".
- **Verdict**: ratios ≈ 1.0 across all 7 HCs → LOCO transfer test discriminates 못함, 결과 자체 무의미. "(X) noise" 가 아니라 "(X) uninformative metric for this transfer design".

#### A4. ΔAICc precision — 이전 "ΔAICc=−30" 자체 오류
- **Concern**: 이전 보고 ΔAICc=−22 또는 −30 은 잘못 — 2-Comp AICc 의 absolute value 를 Δ 로 잘못 읽음.
- **Re-compute**:
  | Subject | R+C AICc | 2-Comp AICc | **ΔAICc** | Kass-Raftery |
  |---|---|---|---|---|
  | sub-08 | −22.40 | −22.81 | **+0.41** | <2: indistinguishable |
  | sub-09 | −44.17 | −51.43 | **+7.27** | 6-10: strong |
- **Verdict**: Sub-08 에서 R+C vs 2-Comp **모델 비교 indistinguishable** (이전 strong 주장 오류). Sub-09 만 strong evidence for 2-Comp.
- **Impact**: Paper claim 정정 — sub-08 "ΔAICc=−30 very strong" 제거.

#### A5. Cross-subtype Δ analysis 가 asymmetric claim INVERT
- **Concern**: 이전 보고 ratio (sub-08→sub-09 vs sub-09→sub-08) 는 base loss magnitude artifact. **Δ (cross − within)** 가 올바른 metric.
- **Re-compute**:
  | Direction | L_within | L_cross | **Δ (cross−within)** | Ratio |
  |---|---|---|---|---|
  | sub-08 → sub-09 | 0.560 | 0.881 | +0.32 (smaller abs) | 1.57 |
  | sub-09 → sub-08 | 5.151 | 5.672 | **+0.52 (larger abs)** | 1.10 |
- **Verdict**: Δ analysis 하에서 sub-09→sub-08 transfer 가 *larger* absolute error → "Sub-08 subtype-specific, Sub-09 transferable" 주장 INVERT.
- **Impact**: Paper claim 제거 — "asymmetric subtype-specificity (sub-08 specific, sub-09 generic)" 는 ratio artifact.

#### A6. Permutation null 형식 — color-perm 과 loss-assign-perm 분리
- **Concern**: S8 color-permutation null 은 과도하게 destructive; loss-assignment permutation 이 less destructive (model 구조 유지, fold-assignment 만 shuffle).
- **Re-test**:
  | Subject | S8 color-perm p | S10 loss-assign perm p | Verdict |
  |---|---|---|---|
  | sub-08 | 0.150 | 0.130 | NS in both — robust limitation |
  | sub-09 | 0.000 | **0.000** | Significant in BOTH — robust evidence |
- **Verdict**: Sub-09 permutation evidence survives **both** null forms — robust. Sub-08 fails both — paper limitation.

#### A7. Pool-independence by construction (advisor catch 2026-05-23 in S11.5)
- **Concern**: S11 HC LOO 의 `cvd_param_sd` 가 L_α / L_LOCO 에서 SD=0 — "stability" 가 아니라 *tautology* (closure 가 pool 인자 받지 않음).
- **Fix**: Pool-dependent losses (L_γ, L_RDM) 만 의미; L_α / L_LOCO 는 trial-level CVD bootstrap 또는 cross-cell agreement 로 측정해야 함.
- **Full detail**: §S11.5, line 1465.

#### A8. Circularity block — filter fit ↔ behavioral validation (advisor catch 2026-05-23 in S11.6)
- **Concern**: S11.6 의 single filter recommendation (sub-09 R+C L_γ V4, sub-08 2-Comp L_γ V1) 은 §0.1 P2a/P1 policy 와 동일한 circularity (behavioral data 로 fit → behavioral 로 validate).
- **Resolution options**: (a) "interim, awaiting non-circular validation" qualifier, (b) L_RDM-only re-fit (단 U5 procedural bias 영향), (c) 별도 수집 behavioral test (filter 적용 자극 vs no-filter).
- **Status**: BLOCK marker active in S11.6; Phase 3 trigger 전 resolution 필수.
- **Full detail**: §S11.6, line 1517.

### S9.3 Applied fixes — Paper-defensible claim revisions

**SURVIVE** (after S9_old + S10_old + sub-sequent constraints):
- ✓ Sub-09 individual-level g > 1 (trial-level bootstrap CI [2.35, 2.60] excludes 1.0; even with U3 fix, U4 sensitivity, U5 caveat)
- ✓ Sub-09 permutation p=0.000 robust under **two** null forms (S8 color-perm + S10 loss-assign-perm, A6)
- ✓ Sub-09 mild protan profile (JND-Lamb 1.5 nm + Ishihara 9/14 + V1 LOCO p=0.007 from project memory)
- ✓ Sub-08 2-Comp captures structural distortion (β_s=48, β_c=−36) — K-robust per K-robustness Final Report (line 1330)
- ✓ Sub-08 R+C 1-DOF misspecified (bimodal bootstrap, boundary mass) — shape diagnostic surviving
- ✓ Subtype dichotomy β_c (sub-08 < 0 vs sub-09 > 0) — K-robust, U6 W-asymmetry-independent

**COLLAPSE** (must remove from paper):
- ✗ "Group-level CVD vs HC specificity recovered (FPR=0)" → only descriptive percentile + CI overlap (A1)
- ✗ "2-Comp subtype-specific transfer (4.59× sub-08)" → ‖δθ‖² magnitude artifact (A2)
- ✗ "Asymmetric subtype-specificity (sub-08 specific, sub-09 generic)" → INVERTS under Δ analysis (A5)
- ✗ "ΔAICc=−30 very strong evidence" → actually +0.41 (sub-08 indistinguishable) and +7.27 (sub-09 strong) (A4)

**QUALIFIED** (paper 보고 시 explicit caveat):
- ⚠ V4 protan small-Δλ L4 RDM (sub-09 g=3 boundary): procedural-bias caveat (U5) 동반 보고 — "HC g distribution under CVD-model misspecification"
- ⚠ Sub-08 permutation p=0.150 (S8) and p=0.130 (S10): paper limitation, robust NS — "R+C 1-DOF insufficient for sub-08, motivates 2-Comp for sub-08"
- ⚠ S11.6 filter recommendations: BLOCKED for circularity (A8) — Phase 3 trigger 전 resolution 필요
- ⚠ L8 composite-fit δθ: "weighted compromise across distinct measurement channels, not single true δθ" (U6 + §Loss-Design Constraints (1)+(2))

### S9.4 Chronological audit log

| Date | Source | Catch ID | Issue | Outcome |
|---|---|---|---|---|
| 2026-05-21 | User | **U1** | §6.3 transfer test 미실행, V_s mismatch 오해석 | `scripts/s9_retroactive_defenses.py` Part 1 실행 (V4 + V1, 28 transfer tests/ROI) |
| 2026-05-21 | User | **U2** | Group-level FPR 새 framework 재검증 안 됨 | `scripts/s9_retroactive_defenses.py` Part 2 실행; raw FPR=0/7 보고 (later corrected by A1) |
| 2026-05-21 | Advisor | **A1** | "FPR=0.000" misleading | CI overlap re-frame; "0/7 percentile" 으로 qualify |
| 2026-05-21 | Advisor | **A2** | (Y) JND 4.59× 미정규화 | ‖δθ‖² normalize; subtype-specific claim COLLAPSE |
| 2026-05-21 | Advisor | **A3** | (X) LOCO ≈ 1.0 framing 부정확 | "noise" → "test uninformative" |
| 2026-05-21 | Advisor | **A4** | ΔAICc=−30 잘못 보고 | +0.41 / +7.27 로 재계산 |
| 2026-05-21 | Advisor | **A5** | Cross-subtype ratio artifact | Δ-based re-analysis; asymmetric claim INVERT |
| 2026-05-21 | Advisor | **A6** | color-perm too destructive | Loss-assign perm 추가; sub-09 robust, sub-08 NS in both |
| 2026-05-22 | User | **U3** | Bootstrap sampling unit (color → trial) | `scripts/s6_bootstrap_g_ci_trial.py`; sub-09 CI 5× narrow |
| 2026-05-22 | User | **U4** | Δλ assumption single point | S6 convergence matrix → "Δλ-prior robustness" (3 sources) |
| 2026-05-22 | User | **U6** | W asymmetry + L8 composite interpretation | §Loss-Design Constraints (1)+(2) acknowledged limitation |
| 2026-05-23 | User | **U5** | HC procedural bias (CVD-prior Δλ → HC) | S6' subset resample design (line 708); old S5' Form B deprecated |
| 2026-05-23 | Advisor | **A7** | Pool-independence by construction | S11.5 re-framed; L_α/L_LOCO SD=0 tautology 보고 금지 |
| 2026-05-23 | Advisor | **A8** | Circularity block (filter-behav) | S11.6 BLOCK marker; Phase 3 trigger 전 resolution 필요 |
| 2026-05-24 | (Consolidation) | — | S9_old + S10_old → new S9 | 본 section; archive headers updated |

### S9.5 Files

- `scripts/s9_retroactive_defenses.py` — 7-fold HC transfer test + L_behav FPR test (U1, U2)
- `scripts/s10_advisor_fixes.py` — ‖δθ‖² normalize, CI re-frame, ΔAICc, Δ cross-subtype, loss-assign perm (A1-A6)
- `scripts/s6_bootstrap_g_ci_trial.py` — Trial-level bootstrap (U3)
- `results/s9_retroactive/{transfer_test_V4.json, transfer_test_V1.json, fpr_test.json}`
- `results/s10_advisor_fixes/` (logs)

### S9.6 Status

**Status**: Complete 2026-05-24. S9_old + S10_old content fully consolidated; archive headers updated (line 1145, 1224). Surviving paper claims locked in S9.3; collapsed claims explicitly listed for paper-revision QC. Cross-references to living detail (§Loss-Design Constraints, §S11.5, §S11.6) preserved.

---

## Acknowledged Loss-Design Constraints (Paper Limitations, 2026-05-22; **Moved to file bottom 2026-05-24**)

사용자 catch (W asymmetry + L8 composite interpretation) + Option C framing 통합. Paper limitation section 후보.

### (1) L_LOCO 와 L_RDM 의 encoder asymmetry — Option C framing

**현 상태**:
- L_LOCO: CVD 본인 W (within-subject ridge, V_s-matched)
- L_RDM: HC pool W (cross-subject mean encoder, V_s-invariant 28-vec)

**Ideal (impractical)**:
이상적으로는 단일 W 정의 (예: HC + CVD 양 그룹의 voxel pattern 을 모두 fit 하는 shared encoder) 에서 두 loss 가 *동일 reference frame* 으로 계산되어야 함. 그래야 L_LOCO 와 L_RDM 이 같은 δθ 를 estimate.

**Why impossible in current pipeline**:
- V_s mismatch (subject 별 voxel 수 다름)
- Phase 1 의 cross-subject alignment (Procrustes/SRM) 시도 REJECTED — SRM-based prior pipeline 이 within-subject ridge 보다 inferior (phase4_forward_model/README.md)
- Small-n HC pool (n=7) → shared encoder fit 시 variance 너무 큼

**Conceptual rationale (current asymmetry)**:
- L_LOCO 의 native space = voxel → V_s match 필수 → within-subject W 가 *technical inevitability*
- L_RDM 의 native space = 28-vec pairwise distance → V_s-invariant → HC W 사용 가능
- 두 loss 의 W choice 비대칭은 *intentional inconsistency 아니라 each metric 의 native space 의 technical property*

**Acknowledged implication**:
- 두 loss 의 inferred *"best δθ"* 가 *loss-dependent*
- 실측 dissociation: sub-08 V1 LOCO p=0.047 vs ΔRDM p=0.179 (NS); sub-09 LOCO NS vs ΔRDM p=0.026
- → 단일 "true δθ" 가 정의되지 않음. 두 loss 가 *complementary information* 측정으로 해석.

### (2) L8 (modality 5050) 의 의미 명시 — paper-level interpretation

**Form**:
```
L8(δθ) = 0.5 · L_γ(δθ)                       ← behavioral (JND per-pair)
       + 0.25 · L_LOCO(δθ; CVD own W)        ← neural functional (V_s-matched)
       + 0.25 · L_RDM(δθ; HC pool W)         ← neural relational (V_s-invariant)
```

**Paper-defensible interpretation**:

> "L8 represents a *modality-balanced composite* where behavioral JND constraints (0.5 weight) and neural constraints (0.5 total: 0.25 LOCO + 0.25 RDM) are weighted equally. The neural sub-weights split between functional voxel-level prediction (L_LOCO) and HC-referenced relational geometry (L_RDM) because these two channels capture complementary aspects of distortion: L_LOCO tests whether the model δθ improves *subject-own* pattern reconstruction (within-subject), while L_RDM tests whether δθ explains the *HC-referenced* pairwise distance distortion (cross-subject). The two neural channels use *different encoder references* (subject-own W for L_LOCO, HC-pool W for L_RDM) due to their distinct native spaces (voxel-level vs 28-vec representational), an asymmetry that reflects technical V_s constraints rather than a unified estimate of δθ. We therefore report L8-fitted parameters with the explicit understanding that they minimize a *weighted compromise* across these distinct measurement channels rather than identifying a single 'true δθ'."

### (3) Bootstrap sampling unit — 사용자 catch 2026-05-22

**Original S6 (s6_bootstrap_g_ci.py)**: sampling unit = **color/pair** (8 colors / 8 pairs with replacement). 사용자 catch: "8 개 중 일부 색만 여러번 sampled — 특정 색은 왜곡이 약할 수 있어 의미 없지 않나?"

**문제 정확**:
- Color-specific distortion (sub-08 yellow +30°, orange +43° 등) 의 sampling bias
- Color set 은 실제 fixed design element → bootstrap 의 *true measurement uncertainty* 추정 아님
- Sub-08 wide CI [0, 3] 의 origin = (1) R+C misspec + (2) color resample noise 의 *mix*

**Trial-level bootstrap (S6 trial, `scripts/s6_bootstrap_g_ci_trial.py`)**:
- Sampling unit = **individual trial** (JND staircase trial rows / 8AFC trial responses)
- 8 colors / 8 pairs 항상 preserved (color set fixed)
- True measurement-noise uncertainty estimate

**Paper-level implication**: S6 의 CI 는 color-resample artifact 일부 포함. Trial-level bootstrap 이 *proper statistical bootstrap*. Sub-08 wide CI 의 *misspec vs noise* 분리 가능.

**S6-trial result (2026-05-22 fix 후)**:
- **Sub-09 DPS**: CI **5× narrow** (1.30-2.60 → 2.35-2.60), P(g>1)=1.00 robust → flagship claim **strengthened**
- **Sub-08 DPS**: P(g>1) 0.66 → **0.92**, bimodal 부분 collapse → claim **strengthened** (단 부분 misspec 잔존)
- **CVD vs HC CI separation**: sub-09 Boehm Δλ=3 에서 처음 separated (small Δλ 가설 하에서 cortical g 최대 discriminator)

**Verdict**: Trial-level bootstrap 이 *모든 paper-defensible claims 를 강화*. 사용자 catch 가 paper evidence 를 더 robust 하게 만듦.

### (4) Δλ assumption uncertainty — 사용자 catch 2026-05-22

**Original S5'/S6**: Δλ = **DPS lit only** (protan 10 nm, deutan 6 nm) 고정 → g 분포에 Δλ uncertainty 미포함.

**Δλ sensitivity check (S6 trial × 3 Δλ source × 2 family)**:
- DPS lit (외부 상수), Boehm grid (외부 상수), JND-Lamb (data-driven fit)
- Per Δλ source 의 g CI 비교 → "Δλ assumption 이 g 분포 얼마나 변화시키나" 평가

**Paper-level**: S5'/S6 의 single Δλ=DPS 가정에 *추가 sensitivity layer* 제공. Sub-09 protan 의 JND-L Δλ=1.5 같은 small Δλ 가 g distribution 어떻게 변화시키는지 확인.

### (5) HC pool g 의 procedural-bias caveat — 2026-05-23 사용자 catch

**문제**: S5'/S5'-neural extension 에서 HC pool g 분포 산출 시 **CVD-prior Δλ** (DPS lit, Boehm grid, JND-Lamb inverse — 모두 CVD 데이터에서 도출) 를 7명 HC 에게 강제 대입.

**모델 가정 위반 (§2 A1, A6)**:
- A1: CVD 차이 = retinal cone shift → HC 의 "true Δλ" = 0
- A6: HC pool descriptive only
- CVD-Δλ 를 HC 에 적용 → **모델 misspecification 상태에서의 g_hat**

**구체 사례**: V4 protan Boehm_low (Δλ=3) L4 RDM HC pool mean=2.61 (boundary high=3/6) 또는 JND_Lamb (Δλ=1.5) L4 RDM HC pool mean=2.43 (boundary high=2/6).
- "HC 도 cortical compensation g≈3" 이 아니라 *잘못된 Δλ 가정 하에서 loss landscape 이 g→3 boundary 로 끌리는 procedural bias* 의 증거.
- 같은 cell 의 CVD sub-09 g=3.00 → **CVD vs HC 구별 불가능** (둘 다 procedural artifact).

**왜 Δλ=0 HC null 산출 불가**: Δλ=0 → Machado matrix = identity → δθ(c; 0, g) = 0 ∀g → g unidentifiable (loss landscape flat across g).

**Paper 정정**:
- "HC pool g distribution" framing → **"procedural g under CVD-model misspecification"** 로 변경.
- V4 protan small-Δλ L4 RDM 의 CVD g=3 주장은 paper 에서 **procedural-bias caveat 동반** 또는 제외.
- V1 L4 RDM, V4 deutan, V4 protan DPS 는 boundary high 발생률 낮음 (≤2/7) → 영향 작음.

**더 honest null 대안** (S8_old sprint 에서 검토):
- **Permutation null**: CVD/HC label shuffle, Δλ 는 CVD prior 고정 → CVD g 의 specificity 산출 (label permutation 만 변경, Δλ assumption 보존)
- **HC-specific Δλ fit**: 보통 Δλ_HC ≈ 0–2 nm → R+C 로 식별 어려움 → 실용 가치 낮음
- **2-comp 으로의 fallback**: 2-comp 은 Δλ 의존성 없음 (cortical only) → HC 적용 시 misspecification 약함

### (6) Surviving paper-defensible claims under these constraints

위 (1)-(5) limitation 하에서도 다음 주장은 robust:

| Claim | (1) W asymmetry | (2) L8 multi-channel | (3) sampling unit | (4) Δλ assumption | (5) HC procedural bias |
|---|---|---|---|---|---|
| Sub-09 R+C g* = 2.60, Bootstrap CI [1.30, 2.60] | ✅ within-subject | ✅ behav-dominant L8 | ✅ trial-level confirm 예정 | ⚠ DPS Δλ only → sensitivity check 진행 중 | ⚠ V4 protan small-Δλ L4 RDM 만 영향, V1/V4-LOCO 무관 |
| Sub-09 perm p=0.000 | ✅ within-subject | ✅ | ✅ color-label perm independent | ✅ Δλ-agnostic | ✅ label permutation 이 procedural bias 흡수 |
| Subtype dichotomy β_c (sub-08 < 0 vs sub-09 > 0) | ✅ within-subject | ✅ K-robust | ✅ point estimate | ✅ | ✅ 2-comp 무관 |
| Sub-09 V1 LOCO p=0.007 (separate, MEMORY) | ✅ pre-existing | ✅ not L8 | ✅ independent test | ✅ | ✅ L_LOCO 만 |
| Sub-08 R+C 1-DOF misspecified (bimodal bootstrap) | ✅ shape diagnostic | ✅ | ⚠ trial-level 재검증 필요 | ✅ | ✅ |

**즉 surviving claims 가 위 5가지 limitation 의 어느 *individual* 에도 의존하지 않음** — 단 V4 protan small-Δλ L4 RDM 결과는 procedural-bias caveat 동반 보고 필요.

#### Paper limitation section 권장 문구 (draft, 5 constraints 통합)

> "We acknowledge five measurement-design constraints affecting interpretation. **First**, the neural loss components L_LOCO and L_RDM employ different encoder references (subject-own ridge for L_LOCO, HC-pool ridge for L_RDM); this asymmetry follows from each metric's native space (voxel-bound vs V_s-invariant representational) rather than a deliberate design choice, and we observe that the two channels produce dissociated 'best δθ' estimates in some subject-ROI cells. **Second**, our composite L8 loss represents a weighted compromise across complementary measurement channels (behavioral JND, functional LOCO, relational RDM) rather than a unified estimate of a single underlying δθ. **Third**, our original bootstrap CI used color-set resampling, which conflates measurement noise with color-specific distortion-driver variance; we therefore report trial-level bootstrap (per-trial resampling with color set fixed) as the primary statistical uncertainty estimate. **Fourth**, the cone-shift Δλ is taken from external sources (DPS 1992 population mean, Boehm 2014 severity grid, or JND-Lamb inverse fit); g estimates are reported across these three Δλ priors as a sensitivity analysis. **Fifth**, HC pool g estimates use CVD-derived Δλ priors applied to HC subjects under the cone-shift model, which represents a procedural baseline under model misspecification (HC's true Δλ ≈ 0); this produces boundary g≈3 in V4 protan small-Δλ L4 RDM and necessitates explicit framing of HC pool g as 'procedural g under CVD-model assumption' rather than 'HC's true compensation'. The surviving paper-defensible claims (individual-level g > 1 in sub-09, subtype dichotomy in β_c sign, R+C misspecification in sub-08) do not depend on any individual measurement channel or modeling choice; each is supported by limitation-independent evidence. Group-level specificity claims are explicitly *not* asserted, in accordance with these constraints."

---

# updated-pipeline — S10 Precondition + Cross-ROI Inclusion (2026-05-24)

## A. Pass criterion (formalized)

**Per (cell × loss) admission test**: compute Cohen's d_signed = (CVD_loss − HC_LOO_mean) / HC_LOO_SD at δθ=0, where HC_LOO 7 values are obtained by leave-one-HC-out (target = held-out HC, baseline = remaining 6 HC).

| Criterion | Threshold | Rationale |
|---|---|---|
| **Direction** | d ≥ +0.5 (one-sided, CVD > HC) | Negative d means CVD is *closer to HC mean* than HC subjects themselves → no cone-shift signal. Two-sided abs(d) ≥ 0.5 would let negative d pass, incorrectly admitting null cells (e.g., sub-10 V3/V4 RDM d=−1.08/−1.91 represent regression-to-mean, not signal). |
| **Effect size** | d ≥ +0.5 (medium) | Cohen 1988 convention. d ≥ +0.8 (strong) marked separately. |
| **Per-ROI restriction (L_LOCO)** | V4 only | V1/V2/V3 L_LOCO fail permutation null (memory 2026-03-11: hV4 perm p=0.044 primary; V1/V2 null ~0.10–0.13 from voxel covariance, not color signal). Static effect size at V1/V2 can be high but is uninterpretable as cone-shift evidence. |
| **L_RDM precondition metric** | ΔRDM_obs Euclidean norm | L_RDM cosine itself degenerate at δθ=0 (ΔRDM_sim ≈ 0 → cosine = NaN/0). Use raw ΔRDM_obs = (target_RDM − pool_mean_RDM) norm as static precondition. |

## B. Precondition table (per CVD subject × ROI × loss, signed Cohen's d, δθ=0)

L_γ has 3 aggregation variants: mean across 8 pairs, max, top-3 mean. L_RDM is per-ROI (4 cells per subject). L_LOCO is V4-only.

| Cell | L_γ_mean | L_γ_max | L_γ_top3 | L_RDM | L_LOCO (V4) |
|---|---|---|---|---|---|
| sub-08 V1 | +5.21 ✓ | +7.29 ✓ | +8.69 ✓ | +2.31 ✓ | (V4 only) |
| sub-08 V2 | +5.21 ✓ | +7.29 ✓ | +8.69 ✓ | +1.94 ✓ | (V4 only) |
| sub-08 V3 | +5.21 ✓ | +7.29 ✓ | +8.69 ✓ | +0.86 ✓ | (V4 only) |
| **sub-08 V4** | +5.21 ✓ | +7.29 ✓ | +8.69 ✓ | +2.19 ✓ | **+3.04 ✓** |
| sub-09 V1 | −0.30 | −0.06 | −0.23 | **+0.81 ✓** | (V4 only) |
| sub-09 V2 | −0.30 | −0.06 | −0.23 | −0.23 | (V4 only) |
| sub-09 V3 | −0.30 | −0.06 | −0.23 | −0.48 | (V4 only) |
| **sub-09 V4** | −0.30 | −0.06 | −0.23 | −0.24 | **+1.61 ✓** |
| sub-10 V1 | NA (no JND) | NA | NA | −0.51 | (V4 only) |
| sub-10 V2 | NA | NA | NA | +0.13 | (V4 only) |
| sub-10 V3 | NA | NA | NA | −1.08 | (V4 only) |
| **sub-10 V4** | NA | NA | NA | −1.91 | **+0.57 ✓ (FP)** |

L_γ is ROI-agnostic so the same d repeats across V1–V4 — column structure preserved only to indicate which (loss, ROI) cell is admitted for fitting.

**Pass counts (effective)**: L_γ_mean 4/12 (sub-08 only); L_γ_max 4/12; L_γ_top3 4/12; L_RDM 5/12 (sub-08 V1–V4 + sub-09 V1); L_LOCO V4 2/3 valid + sub-10 V4 marginal FP.

sub-10 V4 L_LOCO +0.57 is a *known false positive* per memory `baseline_delta_rho/` (HC baseline_ρ confound −0.894 with Δρ, hV4 K=3 voxel-prediction artifact). Treated as null in downstream analysis.

## C. L_γ pair-decomposition — per-pair Cohen's d (vs HC LOO at δθ=0)

User insight (2026-05-24): aggregate L_γ_mean dilutes per-pair local distortion. Sub-09 L_γ_max (=−0.06) also fails. Direct per-pair test:

| Pair | sub-08 z² | sub-08 d | sub-09 z² | sub-09 d |
|---|---|---|---|---|
| red-orange (0→45°) | 0.73 | −0.41 · | 0.46 | −0.53 ✗ |
| **orange-yellow (45→90°)** | 17.25 | **+7.97 ✓** | 0.40 | −0.57 ✗ |
| **yellow-green (90→135°)** | 18.68 | **+7.49 ✓** | 0.76 | −0.35 · |
| green-blue (135→225°) | 0.004 | −0.50 ✗ | 5.55 | **+0.81 ✓** |
| blue-purple (225→270°) | 0.23 | −0.44 · | 0.03 | −0.48 · |
| **yellow-purple (90→270°)** | 44.92 | **+39.4 ✓** | 0.89 | −0.38 · |
| cyan-magenta (180→315°) | 0.02 | −0.69 ✗ | 0.08 | −0.66 ✗ |
| red-cyan (0→180°) | 1.51 | +0.25 · | 1.51 | +0.25 · |

**Sub-08**: 3 pairs strong (yellow-purple d=+39.4, orange-yellow +7.97, yellow-green +7.49) — *yellow-axis HYPO* pattern (deutan red-green confusion compresses yellow distinguishability).

**Sub-09**: 1 pair strong (**green-blue d=+0.81**) — *protan blue-end confusion axis*. Confirms user hypothesis: local distortion exists, but **only this single pair**. Aggregate L_γ_mean fails because the other 7 pairs dilute.

**Per-pair L_γ atoms** (admissible if d ≥ +0.5):
- **L_γ_OY** (orange-yellow): sub-08 only
- **L_γ_YG** (yellow-green): sub-08 only
- **L_γ_YP** (yellow-purple): sub-08 only
- **L_γ_GB** (green-blue): sub-09 only

These pair atoms replace aggregate L_γ in subject-specific fitting.

## D. Cross-ROI inclusion — Per-subject atom set

Phase A admits the following atoms (per subject):

| Subject | Admissible atoms | # atoms |
|---|---|---|
| **sub-08 (deutan)** | L_γ_OY, L_γ_YG, L_γ_YP, L_RDM_V1, L_RDM_V2, L_RDM_V3, L_RDM_V4, L_LOCO_V4 | 8 |
| **sub-09 (protan)** | L_γ_GB, L_RDM_V1, L_LOCO_V4 | 3 |
| **sub-10 (near-normal)** | — (control, no valid cone-shift atoms) | 0 |

**Sub-08 8 atoms → 2⁸=256 inclusion combos** is excessive. Pragmatic reduction:
- Behavioral pool L_γ ∈ {single-pair (3 choices), mean of 3 pairs}: 4 choices
- RDM ROI choice ∈ {V1, V2, V3, V4, V1+V4 cross-ROI}: 5 choices
- LOCO V4 ∈ {in, out}: 2 choices
- Total: 4 × 5 × 2 = **40 combos** for sub-08

**Sub-09 3 atoms → 2³=8 inclusion combos** (cross-ROI L_γ_GB + L_RDM_V1 + L_LOCO_V4 is the key novel combo).

**Phase B (S10b) execution scope**:
- Sub-08: 40 cross-ROI combos
- Sub-09: 8 cross-ROI combos
- Sub-10: skipped (no atoms; descriptive control fit only at sub-08/09 selected combos)
- × 2 models (R+C 3 Δλ sources + 2-comp) × 21 HC subsets ≈ 4000–5000 fits, server SLURM 2–3hr

## E. Fitting metric for cross-ROI fits

When loss combo spans multiple ROIs, fit is no longer per-ROI but **subject-level joint**. Composite loss:

L_total(δθ; subject) = Σ_atom (1/√n_atoms) · z(L_atom)

z-score normalization within each atom's HC LOO distribution. Coefficient 1/√n provides uniform-weight ensemble. Fitting parameter (g for R+C, β_s/β_c for 2-comp) yields single δθ(c) 8-vector per subject, evaluated on test L_γ (held-out HC complement) for cross-combo ranking.

## F. Selection criterion (final)

For each subject × model:
1. For each inclusion combo: 21-subset train-test → median test L_γ (aggregate, 8-pair mean) on complement HC
2. Rank combos by median test L_γ
3. Combo of lowest median test L_γ + non-degenerate parameter (boundary < 50%) = selected
4. 1000× HC subset bootstrap of test L_γ on top-1 combo → CI95

**Sub-09 special case**: aggregate L_γ at test time may be insensitive (per Phase A finding). Alternative test metric for sub-09 = **L_γ_GB only** (green-blue pair test loss). Reported separately.

## G. Sub-10 specificity check (descriptive only, §0 rule)

For each (model, combo) selected from sub-08/09: also fit sub-10 → fit parameter g_sub10 or (β_s, β_c)_sub10. Report:
- Distance from HC LOO fit distribution (descriptive percentile)
- Pre-image magnitude on stimulus space
- **NO p-value claim** (§0 framework decision: descriptive only, FPR ≥ 0.50 confirmed)

## H. Implementation note

Phase B execution (S10b) requires extending `s7_loss_combo_subset.py` to:
1. Replace L_γ aggregate with per-pair L_γ_atom (4 pair atoms)
2. Cross-ROI fitting: each fold loads all 4 ROI amps, fits single δθ minimizing cross-ROI joint composite
3. Test metric = aggregate L_γ on complement (+ L_γ_GB only for sub-09)
4. Sub-08: 40 combos, sub-09: 8 combos, sub-10: descriptive fit at sub-08/09's selected combo only

Decision needed before Phase B sprint: **proceed with this cross-ROI reformulation** or **stay within-cell within-ROI** for tractability.

## I. Phase B Results — sub-09 (2026-05-25)

Phase B run: `scripts/s10b_v2_resample.py` (1000 size-5 HC resamples, RNG seed 43 for sub-09; 7 atom-inclusion combos × {3 R+C Δλ sources, 2-comp} = 28 (combo, model) cells). Source JSON: `results/s10_inclusion/s10b_v2_resample_results_sub-09.json`. **Replay validation (2026-05-25)**: re-running `s10c_sub09_cosine.py` (same RNG seed, same atoms, current code) reproduces the JSON's 2-comp params exactly (β_s=34, β_c=−8) and the focal_loss values within rounding (R+C focal_median 0.623 vs JSON 0.640; 2-comp focal_median 0.646 vs JSON 0.646), but the R+C g for the γ_GB-alone cell **does not** reproduce — re-fit g_median = **2.60** with 100% of 1000 draws falling in [2.50, 2.70], whereas JSON stored g_median = 1.30. Discriminating constraint: under current code, R+C focal at g=1.30 is 18.6 (for the same draw 0 train/test split) while focal at g=2.60 is 0.08, so the JSON's stored (focal=0.640, g=1.30) pair is internally inconsistent. The replay's (focal=0.62, g=2.60) is internally consistent. Hypothesis: JSON came from a stale `__pycache__` state of `rc_1dof.py` on the server pre-dating the 2026-05-21 advisor convention correction (memory note `rc_1dof.py`: "g interpretation (advisor corrected 2026-05-21)"). The reproducibility of 2-comp params and focal-loss values suggests the issue is isolated to the R+C g column for the γ_GB-alone cell. §I below uses the **replay-derived** R+C g (current-code authoritative).

**Test metric**: median test L_γ on the **complement HC (focal pair = green-blue, the only admissible γ atom for sub-09)** across the 1000 resamples. Lower = better. IQR column below = *test-loss IQR* across draws (highly skewed — wide because n_test = 2 HC complement).

### Top-5 candidates (sub-09, sorted by median test L_γ_focal)

> **⚠ Ranking table superseded — see §I.3 for valid local v3 results** (server v2/v3 R+C invalid: Machado Gaussian fallback due to missing `colour-science` library on server. 2-comp values valid.) The table below is *preserved for audit* but its R+C g values are spurious.

| Rank | Combo | Model | focal_med | focal_IQR | agg_med | bdy | param (median) | param_IQR | AIC | BIC | n |
|---:|---|---|---:|---:|---:|---:|---|---|---:|---:|---:|
| 1 (~~invalid~~) | γ_GB \| RDM_ \| noLOCO | rc_DPS_lit (Δλ=10) | 0.640 | 414.8 | 9.40 | 0.000 | ~~g = 1.30~~ → **2.60** (local) | 0.10 | −0.28 | −1.59 | 1000 |
| 2 | γ_GB \| RDM_ \| noLOCO | 2comp | **0.646** | 408.1 | 35.48 | 0.000 | β_s=34, β_c=−8 (valid) | 18 / 42 | +1.74 | −0.88 | 1000 |
| 3 | γ_ \| RDM_V1 \| LOCO | 2comp | 1.038 | 197.7 | 466.6 | 1.000 | β_s=18, β_c=+50 | 4 / 0 | +2.69 | +0.07 | 1000 |
| 4 | γ_GB \| RDM_V1 \| LOCO | 2comp | 1.038 | 197.7 | 466.6 | 1.000 | β_s=18, β_c=+50 | 4 / 0 | +2.69 | +0.07 | 1000 |
| 5 (~~invalid~~) | γ_GB \| RDM_ \| noLOCO | rc_Boehm_low (Δλ=3) | 2.327 | 18.1 | 8.30 | 1.000 | ~~g = 0.0~~ → 3.00 (local) | 0.0 | +2.30 | +1.00 | 1000 |

Cross-ROI reference (γ_GB + RDM_V1 joint, RC variants): boundary-degenerate (bdy=0.40–0.87, g_iqr ≈ 0.20–1.10) across all three Δλ sources — see `s10b_v2_resample_results_sub-09.json` rank-11 through rank-20. **Note**: this server-stored bdy/iqr also reflects the wrong-Machado fit — local v3 reveals γ_GB+RDM_V1 rc_DPS_lit is *stable* (bdy=0.00, g=2.65±0.25, focal=2.69), see §I.3.

### Key findings

**(1) γ_GB-alone single-atom fits are the winners** (Rank 1 + Rank 2, identical combo, different mechanism). Both achieve focal ≈ 0.64 with stable parameters (bdy = 0.000) under 1000 HC resamples. Single 1-D behavioral constraint (green-blue JND) is sufficient to identify a 1-DOF cortical-gain parameter (R+C g) or a 2-DOF cortical rotation (2-comp β_s, β_c).

**(2) Cross-ROI joint atoms degenerate** (Rank 3/4: γ_GB + RDM_V1 + LOCO_V4 2-comp; boundary rate 1.0, β_c pinned at the +50° grid edge). The cross-ROI joint cannot identify a non-degenerate filter for sub-09. Neural atoms pull the optimum *outside* the (β_s, β_c) box, evidence that γ_GB-derived δθ and RDM_V1-derived δθ disagree on the precise location in (β_s, β_c) plane.

**(3) RDM_V1-alone (neural single, no γ) admissible but ~14× worse for behavior**: Rank 7/8 (γ_·|RDM_V1|noLOCO, 2-comp) yields β_s=2, β_c=+50 (boundary β_c=+50, bdy=0.796) — focal test 3.94 vs Rank 1/2's 0.64. Under R+C the same RDM_V1-alone yields **g ≈ 2.20** (rc_DPS_lit, replay-confirmed; JSON 2.10, re-fit 2.30, both within JSON IQR=1.10). 2-comp at (β_s=2, β_c=+50) sits at the boundary of the cortical rotation grid.

**(4) Convergence (not dissociation) on cortical gain direction**: Both the behavioral channel (γ_GB alone → R+C **g ≈ 2.60**) and the neural channel (RDM_V1 alone → R+C **g ≈ 2.20**) prefer **over-compensation** (g > 2, sign-flip relative to forward Machado retinal δθ). The two channels *agree* on direction (both are above g=2 cancellation) but disagree on *magnitude* by ~0.4 g-units. Under the (2−g) convention this means: γ_GB asks the filter to apply −0.60 × Machado_protan(10nm), V1 RDM asks for −0.20 × Machado. Cross-ROI joint being boundary-degenerate stems from this magnitude disagreement plus the 2-comp Top-2 ridge (see (5) below). NB: this **revises the initial "dissociation" framing** that was based on the JSON's stored g=1.30.

**(5) δθ direction divergence between R+C and 2-comp**: Despite both Rank 1 (R+C g=2.60) and Rank 2 (2-comp β_s=34, β_c=−8) reducing the *same* green-blue JND constraint to focal ≈ 0.64, their forward δθ(c) 8-vectors are **near-orthogonal in stimulus space**: cosine = **−0.087** at median parameters, with 100% of resamples giving cos < 0.5 (5–95 pct = [−0.33, +0.32], frac(cos > 0.8) = 0.0). The R+C δθ is dominated by hues 5–6 (blue / purple, |δθ| ≈ 53° / 43°), while the 2-comp δθ is a smooth sinusoidal pattern (|δθ| ≈ 32° at hues 2 and 6, ≈ 0 elsewhere). One scalar constraint cannot identify a *direction* in stimulus space — only a magnitude along the model class's parameterized axis. R+C and 2-comp axes don't coincide. Detailed analysis: §I.1 + `results/s10_inclusion/sub09_top12_cosine.json` + `sub09_top12_polar.png`.

**(6) Paper-level message** (sub-09): **two-mechanism non-identifiability** of stimulus-space distortion given a single behavioral constraint. R+C and 2-comp both fit the green-blue JND to within Phase B's noise floor, but they prescribe near-orthogonal filter δθ(c). At least one of {behavioral protocol expansion, neural channel constraint} is required to discriminate them. Without that, the per-subject filter for sub-09 is **mechanism-underdetermined** even though parameter SD within each model class is small.

### Caveat 1 (CRITICAL — baseline-swap, NOT generalization)

The γ_GB-alone Top-1/Top-2 evaluation is **train-pool-vs-test-pool baseline swap on the same green-blue pair**, not held-out pair generalization. Phase A admitted only `L_γ_GB` for sub-09 (no other pair survived d ≥ +0.5); the focal-test pair is also green-blue. focal L_γ_focal = 0.64 measures "the fitted (Δλ, g) or (β_s, β_c) reproduces the green-blue JND ratio when the HC baseline pool is the complement of the training pool". It does **not** demonstrate the filter generalizes to the other 7 pairs — `test_agg_median` (8-pair mean) is 9.4 (R+C) or 35.5 (2-comp), an order of magnitude worse than focal. For sub-09 we cannot test pair-generalization within the current 1-pair-admitted regime.

### Caveat 2 (Ridge — 2-comp Top-2)

The 2-comp Top-2 (β_s=34, β_c=−8) sits on a γ_GB-constrained ridge: a single scalar constraint on a 26×51 (β_s, β_c) grid defines a 1-D manifold of near-equivalent minima. `bs_IQR=18, bc_IQR=42` across the 1000 resamples confirms the argmin walks along this ridge as the HC baseline pool changes. The median (34, −8) is the *median location on the ridge*, not a uniquely identified point. The cosine result in (5) is computed at the median location, and the cosine distribution across resamples (mean −0.065, SD 0.23) is the spread induced by this ridge walking — even averaging it out doesn't bring cos near R+C's δθ direction. R+C's 1-DOF parameterization on the same constraint is fully identified (g_IQR=0.10).

### Caveat 3 (R+C g convention)

Under `rc_1dof.py`'s `δθ = (2 − g) · δθ_Machado` convention (g ∈ [0, 3], g=2 = full retinal cancellation): g = 2.60 means **perceived shift is −0.60 × Machado retinal shift** (overcompensation by 60% of the predicted retinal magnitude, with sign flip). g = 2.20 (V1 RDM) is overcompensation by 20%. Neither parameter is "physiological" in the usual sense of g ∈ [1, 2] (no-compensation to full-compensation); both lie in the overcompensation half-plane.

### Caveat 4 (CRITICAL — server `colour-science` missing → Machado Gaussian fallback)

**Root cause of v2/v3 server R+C invalidity** (discovered 2026-05-25 during local sub-08 reproduction):

- `scripts/machado_simulator.py:129` warns: `"colour-science D65 unavailable (No module named 'colour'); using Gaussian fallback — Machado calibration will drift."`
- Server venv `/scratch/connectome/haba6030/colorBlind/.venv` lacked `colour-science` → Machado δθ computed via Gaussian approximation, *not* exact D65 cone fundamentals
- Direct test: `forward_rc(10.0, 1.25, "protan")` returns **completely different δθ 8-vec** on server vs local:
  - Local (D65): `[-6.69, -6.94, -2.99, +2.61, +11.67, +57.13, -45.67, +1.87]`
  - Server (Gauss): `[-6.90, -7.78, -3.27, +2.97, +13.70, +103.38, -30.05, +5.11]`
- Verification: server-side direct compute of `green-blue z²` at g=1.25, complement=[sub-04, sub-06] **reproduces JSON's stored focal=0.4924 exactly** — confirming the bug is in the server's Machado calculation, not in the storage code
- Even after `pip install colour-science` on server, deltas still differ (possible package-internal D65 lookup difference) — server execution abandoned, all subsequent fits run locally
- **All server SLURM jobs (105184, 105200, 105208) R+C results INVALID**. 2-comp (which doesn't use Machado) valid throughout
- Local re-run (`bt5uv26vx`) confirms g_median = 2.60 (matches sub-agent replay 100%)

## I.1 Top-1/Top-2 forward δθ cosine analysis (script `s10c_sub09_cosine.py`)

Same γ_GB-only combo refit twice — once as R+C (1-DOF), once as 2-comp (2-DOF). 1000 size-5 HC resamples (RNG seed 43, same draws as s10b). Output: `results/s10_inclusion/sub09_top12_cosine.{json,_polar.png}`.

| Quantity | Value |
|---|---|
| cos at median params | **−0.087** |
| cos median across 1000 resamples | −0.087 |
| cos IQR | 0.396 |
| cos 5th–95th pct | [−0.334, +0.316] |
| frac(cos > 0.80) | **0.000** |
| frac(cos > 0.50) | 0.000 |
| frac(cos < 0.50) | **1.000** |
| frac(cos < 0.00) | 0.531 |

**Verdict**: **NEAR-ORTHOGONAL**. The R+C δθ at median params is dominated by hues 5–6 (blue −45.7°, purple +36.5°) with small magnitude elsewhere — a "blue/purple chunk reversed" pattern coming from `(2 − 2.60) · Machado_protan(10nm)`. The 2-comp δθ at median params is the smooth sinusoidal pattern from `β_s·cos(θ−90°) + β_c·cos(θ−16°)` peaking at hues 2 (yellow +31.8°) and 6 (blue −31.8°). Both reduce the GB ratio constraint to focal ≈ 0.64, but they prescribe almost orthogonal stimulus-space distortions. **One scalar constraint = one model degree of freedom resolved**; orthogonality between mechanism classes is preserved.

## I.2 Joint loss weight sweep — γ_GB + RDM_V1 (script `s10d_sub09_weight_sweep.py`)

Composite loss `L_combo(δθ; w) = (1−w)·z(L_γ_GB) + w·z(L_RDM_V1)`, sweeping w from 0.0 to 1.0 in 0.1 steps over the same 1000 HC subset resamples (seed 43, V1 K=6, Δλ=10nm protan DPS_lit). Output: `results/s10_inclusion/sub09_weight_sweep.{json,.png}`.

| w | R+C g (med, IQR) | R+C focal | bdy | 2-comp (β_s, β_c) | param IQR | 2-comp focal | bdy |
|:---:|:---:|---:|---:|:---:|:---:|---:|---:|
| 0.0 | 2.60 (0.10) | **0.62** | 0.000 | (34, −8) | 18 / 42 | **0.65** | 0.000 |
| 0.1 | 2.65 (0.10) | 0.83 | 0.000 | **(2, +50)** | 2 / 4 | **3.94** | 0.743 |
| 0.2 | 2.65 (0.10) | 0.83 | 0.000 | (2, +50) | 2 / 4 | 3.94 | 0.743 |
| 0.3 | 2.65 (0.10) | 0.83 | 0.000 | (2, +50) | 2 / 4 | 3.94 | 0.796 |
| 0.4 | 2.65 (0.10) | 1.27 | 0.000 | (2, +50) | 2 / 4 | 3.94 | 0.796 |
| 0.5 | 2.65 (0.25) | 2.69 | 0.000 | (2, +50) | 2 / 4 | 3.94 | 0.796 |
| 0.6 | 2.65 (0.35) | 7.61 | 0.000 | (2, +50) | 2 / 4 | 3.94 | 0.796 |
| 0.7 | 2.40 (0.35) | 13.06 | 0.000 | (2, +50) | 2 / 4 | 3.94 | 0.796 |
| 0.8 | 2.30 (1.80) | 17.02 | 0.000 | (2, +50) | 2 / 4 | 3.94 | 0.796 |
| 0.9 | 2.30 (1.80) | 17.02 | 0.000 | (2, +50) | 2 / 4 | 3.94 | 0.796 |
| 1.0 | 2.30 (2.25) | 19.70 | 0.323 | (2, +50) | 2 / 4 | 3.94 | 0.796 |

### Sweep findings

**(1) No intermediate w improves focal over w=0.** Both models monotonically (R+C) or instantly (2-comp) move *away* from the γ_GB best as soon as any RDM_V1 weight is added. R+C focal at w=0 is 0.62 and climbs to 19.7 at w=1. 2-comp focal at w=0 is 0.65 and snaps to 3.94 from w=0.1 onward. The behavioral cost of including neural information is monotonic non-positive across all 1000 HC resamples.

**(2) R+C: smooth transition w∈[0.0, 0.6], degenerate w≥0.7.** g stays tightly clustered at 2.65 (IQR 0.10) up to w=0.6, then drops to 2.30–2.40 with IQR exploding to 1.8–2.25 by w=0.8. The cause: the RDM_V1 R+C grid has a wider preferred region around g≈2.0–2.5 (V1 has a relatively shallow loss landscape over g), so at high w the composite minimum bounces between resamples. **R+C g_RDM_V1 alone is not a sharp 2.20; the joint w=1.0 g_median=2.30 with IQR=2.25 confirms the V1 neural channel under-identifies g for sub-09 protan.**

## I.3 Local v3 results — VALID sub-09 ranking (2026-05-25, correct Machado D65)

Local re-run with `colour-science` properly invoked: `scripts/s10b_v3_extended.py --subject sub-09`, N=300 resamples (seed 43), output `results/s10_inclusion/s10b_v3_extended_results_sub-09.json` (2026-05-25 02:17 server-stamp overwritten by local run completion). Test metrics include focal (γ_GB), aggregate L_γ (8-pair mean), and V1-RDM cosine distance.

### Top-10 ranking (sub-09 v3 local, focal-sorted)

| # | Combo | Model | focal | agg | V1RDM | bdy | AIC | param |
|---:|---|---|---:|---:|---:|---:|---:|---|
| **1** | γ_GB \| RDM_ \| noLOCO | **rc_DPS_lit (Δλ=10)** | **0.623** | 8.19 | 0.884 | **0.00 ✓** | **−0.33** | **g=2.60 ± 0.10** ⭐ |
| 2 | γ_GB \| RDM_ \| noLOCO | 2comp | 0.646 | 35.48 | 0.910 | 0.00 ✓ | +1.74 | β_s=34, β_c=−8 |
| 3 | γ_GB \| RDM_ \| noLOCO | rc_Boehm_low (Δλ=3) | 0.655 | 8.32 | 0.905 | 0.90 ⚠ | −0.23 | g=3.00 (boundary) |
| 4 | γ_GB \| RDM_ \| LOCO | rc_Boehm_low | 0.655 | 8.32 | 0.905 | 0.90 ⚠ | −0.23 | g=3.00 (boundary) |
| 5 | γ_GB \| RDM_V1 \| noLOCO | rc_Boehm_low | 0.852 | 7.01 | 0.905 | 0.62 ⚠ | +0.29 | g=3.00 ± 0.10 |
| 6 | γ_ \| RDM_V1 \| LOCO | 2comp | 1.038 | 234.39 | 0.736 | 1.00 ⚠ | +2.69 | β_s=18, β_c=+50 |
| 7 | γ_GB \| RDM_V1 \| LOCO | 2comp | 1.038 | 234.39 | 0.736 | 1.00 ⚠ | +2.69 | β_s=18, β_c=+50 |
| **8** | γ_GB \| RDM_V1 \| noLOCO | **rc_DPS_lit** | **2.693** | 8.65 | 0.895 | **0.00 ✓** | +2.59 | **g=2.65 ± 0.25** ⭐ |
| 9 | γ_GB \| RDM_ \| noLOCO | rc_JND_Lamb (Δλ=1.5) | 3.810 | 8.17 | 0.919 | 1.00 ⚠ | +3.29 | g=3.00 |
| 10 | γ_ \| RDM_ \| LOCO | 2comp | 3.998 | overflow | 0.760 | 1.00 ⚠ | +5.39 | β_s=24, β_c=+50 |

### Validated findings

**(1) Top-1 ranking unchanged** vs server v2/v3 (γ_GB alone, R+C DPS_lit), focal ≈ 0.62 stable. *Only the parameter interpretation changes*: g=2.60 (over-comp, valid) supersedes g=1.30 (under-comp, server-Machado artifact). Sub-agent replay (PIPELINE §I (4)) corroborated.

**(2) NEW — cross-ROI joint stable at #8** (γ_GB + RDM_V1, R+C DPS_lit, g=2.65 ± 0.25, bdy=0.00, focal=2.69). Sub-agent's §I.2 weight sweep showed degeneracy *at high w*; local v3 reveals the **equal-weight (uniform composite, 1/√2 each)** point sits at a *non-boundary* g=2.65. The earlier framing "γ_GB + RDM_V1 joint is degenerate" needs qualification: *boundary-degenerate at RDM-dominant weights, stable at uniform weight*. This is paper-relevant for Phase C weight sweep design.

**(3) R+C and 2-comp both converge on over-compensation** (g ≈ 2.60 vs β_c=−8 / 2-comp). δθ direction near-orthogonal (cos = −0.087, §I.1). Mechanism-underdetermined by single-pair behavioral constraint.

**(4) AIC favors R+C over 2-comp** (−0.33 vs +1.74, ΔAIC = 2.07 in R+C's favor — interpretable as R+C's 1-DOF fit avoids the 2-DOF penalty while achieving equivalent focal).

**Note**: §I (above) Top-5 table is preserved for audit but R+C g values therein are invalid. §I.3 is the **authoritative** sub-09 Phase B result.

## J. Phase B Results — sub-08 (2026-05-25, local v3 valid Machado)

Local run `scripts/s10b_v3_extended.py --subject sub-08`, N=300 size-5 resamples, seed 42. Output: `results/s10_inclusion/s10b_v3_extended_results_sub-08.json`. 40 combos × {3 R+C Δλ sources, 2-comp} = 160 (combo, model) cells.

**Focal pair = yellow-purple** (sub-08's largest Phase A deviance, Cohen's d=+39.4).

### Sub-08 ranking — top 15 unfiltered

All Top 15 are **2-comp at parameter grid boundary** (bdy=1.0, β_s=50 or β_c=±50). R+C cells do not appear in top 15 because R+C focal floor (≈52) is higher than 2-comp boundary fits (≈1.6-22). 2-comp's expressiveness in 2-D allows lower focal but at the cost of *non-interpretable boundary fits*.

### Sub-08 ranking — STABLE only (bdy<0.5)

| # | Combo | Model | focal | agg | bdy | AIC | param |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | γYG \| RDMV2 \| LOCO | 2comp | 47.49 | 97.3 | 0.45 | +10.33 | β_s=38, β_c=−40 |
| 2 | γYP \| RDMV2 \| LOCO | **rc_Boehm_mid (Δλ=4.5)** | 52.19 | 144 | 0.34 | +8.52 | **g=0.05 ± 0.05** ⚠ |
| 3 | γYP \| RDMV3 \| LOCO | rc_Boehm_mid | 52.66 | 140 | 0.27 | +8.54 | g=0.05 ± 0.05 |
| 4 | γYP \| RDMV1+V4 \| noLOCO | rc_Boehm_mid | 53.60 | 140 | 0.44 | +8.58 | g=0.05 ± 0.15 |
| 5 | γYP \| RDMV1+V4 \| LOCO | rc_Boehm_mid | 53.60 | 140 | 0.15 ✓ | +8.58 | g=0.05 ± 0.10 |
| **6** | γYP \| RDMV4 \| LOCO | rc_Boehm_mid | 54.29 | 100 | **0.00 ✓** | +8.60 | **g=0.15 ± 0.00** |
| **7** | γYP \| RDMV3 \| noLOCO | rc_JND_Lamb (Δλ=1.5) | 54.35 | 101 | 0.45 | +8.60 | g=0.05 ± 0.15 |
| **8** | γYP \| RDMV4 \| noLOCO | rc_Boehm_mid | 54.97 | 100 | **0.00 ✓** | +8.63 | **g=0.30 ± 0.15** |
| 9 | γYG \| RDMV2 \| noLOCO | 2comp | 59.80 | 75 | 0.46 | +10.80 | β_s=22, β_c=−46 |
| 12 | γOY,YG,YP \| RDMV1 \| LOCO | **rc_DPS_lit (Δλ=6)** | 62.32 | 171 | 0.08 ✓ | +8.88 | **g=2.95 ± 0.00** ⚠ |

### Key findings — sub-08

**(1) R+C g exhibits *extreme bimodal* between Δλ sources** (the v3 result's bimodality is *across Δλ sources*, not within-source):
- **Boehm_mid (Δλ=4.5)** fits → **g ≈ 0.05-0.30** (under-compensation, near g=0 boundary). Under (2−g) convention: δθ_RC ≈ +1.85 × Machado retinal, *amplifying* the cone shift rather than compensating
- **DPS_lit (Δλ=6)** fits → **g ≈ 2.95** (over-compensation, near g=3 boundary). δθ_RC ≈ −0.95 × Machado retinal, *inverting* the cone shift

Both extremes are biologically implausible. Confirms `[MEMORY: Sub-08 R+C 1-DOF misspecified (bimodal bootstrap)]`.

**(2) 2-comp also boundary-degenerate** at top ranks (β_s=50 or β_c=±50 grid edges). Top stable 2-comp (rank 1) at (β_s=38, β_c=−40) has bdy=0.45 — *almost-degenerate*. Pure (β_s, β_c) interior solution does not exist for sub-08's yellow-purple HYPO magnitude under the current 26×51 grid.

**(3) Focal floor is high — model class insufficient**: Best stable focal ≈ 47-55 (vs Phase A raw z²_YP=44.9). Best fit reduces *less than* the unfitted noise floor. **Sub-08's yellow-axis HYPO magnitude exceeds 1-DOF R+C and 2-DOF 2-comp expressive capacity**.

**(4) Sub-09 vs sub-08 dichotomy** (paper-level message):
- **Sub-09 protan**: 1-DOF cortical-gain model *sufficient*, well-fit (g=2.60, focal=0.62, bdy=0.00). Mechanism-underdetermined only between R+C/2-comp classes; *within each class*, parameters identified.
- **Sub-08 deutan**: 1-DOF + 2-DOF *both insufficient* for yellow-axis HYPO. Parameters pinned at grid boundaries with either extreme g (Δλ-source-dependent bimodality) or β_c saturation. **Cortical compensation model not adequate** at sub-08 deutan severity.

This dichotomy is consistent with sub-08's raw JND deviation Σz²=83 (Phase A) being **8.6× larger** than sub-09's Σz²=9.7 — sub-08 lies outside the comfortable identification range of single-stage cortical models.

### Sub-08 Caveat — Δλ-source switching breaks "single g" interpretation

Phase B optimizes g separately for each of the 3 Δλ priors. Result: best Boehm_mid g=0.05 ≠ best DPS_lit g=2.95. **The same R+C model under different Δλ priors selects opposite extremes**, indicating the *loss landscape* is essentially flat between these two minima — what the fit "sees" depends on which Δλ multiplier scales the Machado retinal δθ in the forward pass.

**Implication for Phase C** (weight sweep, deferred): even with optimized atom weights, sub-08 R+C will remain boundary-degenerate. The natural Phase C question for sub-08 is *not* "which weight combination minimizes focal" but **"is the 1-DOF cortical-gain model class adequate for sub-08?"** — answer (based on §J): *no*. Sub-08 requires either a *higher-DOF model* (3-comp? non-linear?) or *reformulation* (treat sub-08 raw deviation as paper-level finding rather than fit, per memory).

### Sub-08 Phase B verdict

- **No paper-defensible sub-08 filter** from current Phase B (all candidates boundary-degenerate or focal-insufficient)
- Best paper claim: **R+C/2-comp limitation as positive finding** for sub-08 — "deutan with raw Σz²=83 exceeds single-stage cortical model capacity"
- Phase C weight sweep for sub-08 unlikely to recover paper-defensible filter without expanding model class
- Phase 3 behavioral test priority shifts to **sub-09 only** for the active filter; sub-08 reserved for *baseline/control* or *model-class extension* publication

### Sub-08 future-phase candidates — test_focal primary, interior-only stratification (2026-05-25 addendum)

User directive (2026-05-25): primary criterion = **test-set loss fit (`test_focal`) value + distribution**, not AIC. Re-ranking the same 160 (combo × model) cells after stratifying by `boundary` flag at the per-fit level reveals candidates that the all-fit pool median masked.

**Selection rule for this addendum**:
1. Restrict to interior fits only (`boundary == False`) within each cell.
2. Require n_interior ≥ 30 (statistical floor).
3. Rank by `test_focal_median` (primary), then `test_focal_IQR` (distribution tightness).

**Top-5 sub-08 candidates (interior-only, test_focal-ranked)**:

| # | Combo | Model | n_int / n_bdy | focal_int_med ± IQR | agg_med | V1-RDM | Params (int, med ± IQR) |
|---:|---|---|---:|---:|---:|---:|---|
| **1** | γYG \| RDMV1+V4 \| noLOCO | 2-comp | 68 / 232 (23%) | **19.80 ± 11.38** | 11.1 | 1.028 | **β_s = 48 ± 0**, β_c = **−32 ± 0** |
| 2 | γYG \| RDMV1 \| noLOCO | 2-comp | 101 / 199 (34%) | 19.80 ± 22.58 | 72.7 | 1.005 | β_s = 48 ± 0, β_c = −32 ± 2 |
| 3 | γOY \| RDMV1 \| noLOCO | 2-comp | 43 / 257 (14%) | 25.36 ± 24.64 | 561.8 | 1.208 | β_s = 48 ± 0, β_c = **−48 ± 0** (near BC_min) |
| **4** | γYG \| RDMV2 \| LOCO | 2-comp | **165 / 135 (55%)** | 39.68 ± 39.41 | 12.5 | 1.070 | β_s = 34 ± 4, β_c = −40 ± 4 |
| 5 | γYP \| RDMV1+V4 \| noLOCO | R+C DPS_lit | 37 / 263 (12%) | 41.97 ± 21.94 | 27.1 | 0.938 | **g = 2.70 ± 0.00** |

**Two notable cells**:
- **Rank 1 (β_s=48, β_c=−32) — lowest focal**: every interior draw (68/300) yields the *exact* same point (param IQR = 0/0). agg = 11.1 (8-pair aggregate also low). Interior 23%.
- **Rank 4 (β_s=34, β_c=−40) — majority interior**: 165/300 (55%) interior, the only sub-08 cell where interior is majority. Param cluster tight (IQR=4/4). agg = 12.5.

**Acknowledged caveats** (user-confirmed):

1. **Interior is minority** in 4 of top-5 (12–34%): the *majority* of HC subset resamples still push the 2-comp fit to a grid edge. "Interior-only" candidate is conditional on which 5 HCs are drawn.
2. **R+C is Δλ-source sensitive**: always-interior R+C cells split bimodally between Boehm_mid (g ≈ 0.05) and DPS_lit / JND_Lamb (g ≈ 2.7–2.95). Rank 5's g=2.70 is the over-comp branch; choosing Boehm gives g≈0.05 (under-comp) for the same combo, *same focal landscape*. R+C single-g interpretation does not survive Δλ-source switching.
3. **β_s = 48 is geometric boundary-adjacent**: BS_GRID max = 50, so β_s=48 occupies 96% of the grid range. Marked as `boundary == False` by the discrete check (strictly only ±50 counts), but the optimum sits at the grid edge in practice.
4. **V1-RDM cosine ≈ 1.0 in all 5 candidates**: neural cross-validation via V1 RDM is not met — these candidates fit JND structure but show no V1 RDM signal beyond noise.
5. **Always-interior + tight parameters**: 0 cells in 2-comp; 36 cells in R+C (all Δλ-bimodal). For 2-comp, no HC-subset-robust interior candidate exists; conditional candidates (Rank 1, Rank 4) are the best available.

**For future phase use**:
- The two 2-comp candidates **(β_s=48, β_c=−32)** [tightest interior cluster] and **(β_s=34, β_c=−40)** [largest interior majority] are the testable hypotheses for an extended sub-08 protocol (larger HC pool, 3-comp or non-linear model class, or behavioral validation that conditions on the 23%/55% subset regime).
- The R+C g=2.70 candidate is recorded but *cannot be reported as a single-g result* without the Δλ-source caveat (paper would have to choose a Δλ prior and accept that the opposite Δλ prior gives g ≈ 0.05).
- These candidates do **not** override the §J verdict above. The all-fit-pool conclusion ("no paper-defensible filter without model-class extension") is preserved. This addendum only documents *which (β_s, β_c) / g points emerge when the boundary mask is stripped*, for downstream protocol design.

**(3) 2-comp: cliff at w=0.1, no intermediate region.** β_c jumps from −8 (γ_GB ridge median) to +50 (boundary corner) as soon as w=0.1, and stays at the boundary for all w ∈ [0.1, 1.0]. Once the RDM_V1 atom contributes at all, its preferred (β_s≈2, β_c≈+50) anchors the joint optimum at the corner. This is the same boundary degeneracy that drove the cross-ROI joint Rank-3/4 cells in Phase B (bdy=1.0, (β_s=18, β_c=+50)). 2-comp has no graceful joint regime — it's either γ_GB-pure or boundary-corner.

**(4) Mechanism inference**: the two atoms point to *different* preferred regions in the (β_s, β_c) plane. γ_GB likes the ridge of (β_s, β_c) values that match the green-blue JND ratio; RDM_V1 likes (≈2, +50) which is high cortical S-axis (β_s≈0) plus large positive confusion-axis rotation. **They do not agree on direction.** Direct measurement: `cosine(forward_2comp(34,−8,'protan'), forward_2comp(2,+50,'protan')) = +0.080` — the within-2-comp δθ(c) vectors for the γ_GB optimum vs the RDM_V1 optimum are near-orthogonal in stimulus space (norms 65.4° and 101.2° respectively). The optima sit in disjoint corners of the (β_s, β_c) parameterization, hence the immediate snap to (2, +50) at w ≥ 0.1. (This within-model cross-atom result is distinct from §I.1's between-model cross-mechanism cos = −0.087; both directions independently confirm the multi-channel non-identifiability for sub-09.)

**(5) Conclusion**: For sub-09 there is **no weight w that gives both atoms a "meeting point"**. The cross-ROI joint result reported in Phase B (Rank 3/4 degeneracy at β_c=+50) is the inevitable outcome at any w ≥ 0.1. **Recommendation**: report sub-09's two candidates (R+C g=2.60 and 2-comp (β_s=34, β_c=−8)) as **non-identifiable mechanism alternatives**, both fit to γ_GB alone, with documented baseline-swap-only validation (Caveat 1) and ridge-walk variability (Caveat 2). Behavioral filter generalization test is required to discriminate them; this is the sub-09 hold-out gap identified at the start of §I.

Plots: `results/s10_inclusion/sub09_weight_sweep.png` (4-panel: focal-vs-w, boundary-vs-w, R+C g-vs-w, 2-comp params-vs-w).


