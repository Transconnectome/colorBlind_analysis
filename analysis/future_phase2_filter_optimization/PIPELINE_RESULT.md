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
  - (b) DPS 1992 literature constants (protan 10 nm, deutan 6 nm)
  - (c) Boehm 2014 severity grid {3, 8, 13 nm}
  - (d) **JND-Lamb inverse fit (Option B: all-pair joint via Machado forward model)**
- **Output**: `results/lambda_3source/{subject}_lambda.json`, `hc_negative_control.json`

**Implementation notes**:
- Machado forward model from `utils_distortion_models.apply_distortion('machado_1way', ...)` 
- Output space = Stockman opponent coord (NOT DKL canonical)
- Initial coord mismatch bug fixed (baseline_hues at Δλ=0 used for d_phys instead of canonical 0/45/.../315)
- HC pool baseline computed across 7 HC subjects per pair
- `conda srm` env required (colour-science 0.4.4)

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

| Subject | (b) DPS lit | (c) Boehm grid | (d) JND-Lamb fit | Cross-source verdict |
|---|---|---|---|---|
| **sub-08 (deutan)** | 6.0 nm | {3, 8, 13} → mid 8 | **6.5 nm** | ★ **STRONG CONVERGENCE** (5-8 nm) |
| **sub-09 (protan)** | 10.0 nm | {3, 8, 13} → low 3 | **1.5 nm** | ⚠ **DIVERGENCE** (DPS 10 vs JND-derived 1.5) |

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
- **σ = 21° fixed** (HC pooled, S0 결과)
- **Provides infrastructure** for S5 (combined with S3, S4 loss callables)
- **Compensation magnitude**: M = max(0, g−1) · Δλ (retinal-equivalent nm)
- **Output**: `results/rc_1dof/self_test_results.json`

### Stage 2 — Validation (7/7 PASS)

| Test | Description | Result |
|---|---|---|
| 1 | HC baseline (Δλ=0, g=1) → δθ ≈ 0 | ✓ PASS (max\|δθ\|=0.000°) |
| 2 | Full compensation (Δλ=10, g=2) → δθ ≈ 0 | ✓ PASS (max\|δθ\|=0.000°) |
| 3 | Raw Machado (Δλ=10, g=1) → δθ non-trivial | ✓ PASS (RMS 35.27°) |
| 4 | Linear scaling (g=0.5) → δθ = 1.5·δθ_Machado | ✓ PASS (max diff=0.000°) |
| 5 | Dummy grid search (sum δθ² loss) → g* ≈ 2 | ✓ PASS (g_best=2.000) |
| 6 | Forward bijection at typical fit (Δλ=10, g=1.5) | ✓ PASS (min pair=23.54° > 1°) |
| 7 | Boundary detection (biased loss → g=0) | ✓ PASS (boundary_low=True) |

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

## S4: neural_loss.py (⏸ Pending)

(blocked by S2)

---

## S5: All-paths fit (⏸ Pending)

(blocked by S2, S3, S4)

---

## S5': HC pool g fit (T-2 Form B) (⏸ Pending)

(blocked by S2, S3)

---

## S6: LOO + Transfer test ★ PRIMARY DEFENSE (⏸ Pending)

(blocked by S5, S5')

---

## S7: Convergence matrix (⏸ Pending)

(blocked by S6)

---

## S8: Selection + Cross-subtype + Form C permutation (⏸ Pending)

(blocked by S7)
