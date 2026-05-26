# Phase 2 Overall Pipeline — Model & Loss Validation

**Date**: 2026-05-21
**Status**: Pipeline plan, pre-implementation
**Purpose**: PI review (double-dipping concern) 대응 + 모든 sprint 결정 사항 통합 single source-of-truth.

**Cross-references**:
- `results/model_candidates.md` — 모델 정당성 detail
- `prior-works.md` — 문헌 inheritance
- `PI-feedback-priorwork.md` — Living tracker
- `specificity_metrics_candidates.md` — 평가 지표 후보 (Tier 1/2/3)

---

## §1. 거시적 흐름 (5-step pipeline)

```
┌──────────────────────────────────────────────────────────────────┐
│ Step 1. Behavioral anchor: Δλ external-fix (3-source robustness) │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ Step 2. Model fit (R+C 1-DOF g + 2-Comp 2-DOF (β_s, β_c))         │
│         × Target (behav-only / neural-only / joint)               │
│         × Neural loss (L_LOCO, L_RDM, L_LOCO+L_RDM)               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ Step 3. Loss selection (Pareto-optimal: behav-corr / LOO / TT)    │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ Step 4. Cross-model comparison (AICc + BIC + δθ convergence)      │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ Step 5. Generalization (LOO HC × inner LOCO × by-CVD train-test)  │
└──────────────────────────────────────────────────────────────────┘
```

---

## §2. 모델 후보 — 2-model framework

### §2.1 Candidate 1: Boehm-aligned R+C (Primary, grounded mechanism)

```
Step 1 (FIXED, no fit):     Δλ from external source — 3 options (§3.1)
Step 2 (FIXED):             Lamb 1995 cone fundamentals at Δλ_fix
                              L_AT(λ) = L_normal(λ − Δλ_L_AT)
                              M_AT(λ) = M_normal(λ − Δλ_M_AT)
Step 3 (FIXED):             r_AT(c) = L_AT(c) − M_AT(c)   ← retinal opponent
Step 4 (1-DOF fit):         r_cortical(c) = g · r_AT(c)
Step 5 (PROJECTION):        hue_perceived(c) = atan2(r_cortical(c), BY_normal(c))
                            δθ(c) = hue_perceived(c) − c

Total free parameters: 1 (g)
```

⚠️ **현재 코드의 2-DOF joint fit (Δλ, g) 와 다른 *새 form 의 proposal***. BEST_summary.json 의 sub-08 g=−2.25, sub-09 g=−1.10 은 *기존 form* 결과, 새 form 의 결과 아님 → 재fit 필요 (TBD `scripts/rc_1dof_fit.py`).

**자유 파라미터 1 개** (PI 의 double-dipping 우려 직격: Δλ external-fixed → cortical g fit 의 evaluation criteria 와 분리).

> ⚠️ **Cascade form disclaimer (PI 우려 "Biological structure 굳이?" 대응, 2026-05-21 lock-in)**:
> We adopt the R+C cascade form (retinal Δλ → cortical g) as our primary modeling target — **not because we claim a complete mechanistic account, but because the form (i) admits external-fixed Δλ from behavioral/literature sources, ensuring selection-evaluation separation, and (ii) directly inherits the test structure of Tregillus 2021**. We acknowledge Boehm et al. (2021) that simple post-receptoral compensation models do not fully account for AT color discrimination. Our 1-DOF g is therefore the *leading-order term*, not a closed mechanistic explanation. PI feedback note 의 "Retina, cortical 구분의 정당화가 과한" 우려에 대해, **본 문서는 cascade *form* 만 차용하고 *mechanism overclaim 자제*** 의 입장을 유지한다.

### §2.2 Candidate 2: 2-Component (Complementary, novel descriptor)

```
δθ(θ) = β_s · cos(θ − 90°) + β_c · cos(θ − θ_conf)
        ─────────────────   ───────────────────────
        S-cone cardinal      CVD confusion axis
        (Krauskopf 1982)     (protan 16°, deutan 150°)
                              (Stockman & Sharpe)

Total free parameters: 2 (β_s, β_c)
```

⚠️ **현재 `forward_models/two_component.py` form 과 *동일***. *interpretive reframing-not-form*. sub-08 (38°, −14°), sub-09 (6°, −22°) 의 기존 fit 결과 retained, paper-level interpretation 만 변경 ("novel descriptor", mechanism claim X).

### §2.3 두 모델의 역할 — Post-validation, not pre-assumed (사용자 lock-in 2026-05-21)

| 모델 | Mechanism | DOF | Fit objective |
|---|---|---|---|
| **R+C 1-DOF** | Retinal-cortical cascade (Boehm + Tregillus + Emery 2022) | 1 (g) | All 8 loss candidates (§4) |
| **2-Comp** | 1st-harmonic Fourier descriptor of structural distortion | 2 (β_s, β_c) | All 8 loss candidates (§4) |

**Framework principle (PI double-dipping 회피, advisor 정정 2026-05-21)**:

**Primary defense = §6.3 held-out HC transfer test (X, Y, Z metrics)**.
- Selection 은 training pool 에서만 수행, evaluation 은 held-out HC h 의 transfer.
- 이게 *진짜 selection-evaluation separation*.

**Secondary descriptive = §5.4 의 convergence matrix**:
- 두 모델 × 8 loss 의 argmin params 가 일치하는가 (32-fit consistency check)
- Convergence 자체는 *double-dipping defense 가 아닌 candidate space description*
- 사용자 통찰 ("validation 으로 일치여부 확인") = post-hoc model preference 의 *descriptive evidence*

**Expected post-hoc finding (pre-registered hypothesis)**:
- R+C 가 *behavioral-primary natural identity* → L_behav targets 에서 강한 fit + neural validation
- 2-Comp 가 *neural-primary natural identity* → L_neural targets 에서 강한 fit + behavioral validation
- 단, 이는 *검증 결과* 이지 *fitting 전 가정* 아님

---

## §3. 각 모델 정당성 + 파라미터 고정 여부

### §3.1 R+C 의 파라미터

#### Δλ (retinal cone spectral shift) — **FIXED from external source**

**정당성**:
- Tregillus 2021 (NB-verified): "this reduction model assumes that all differences between groups are due to photoreceptor sensitivity differences" + "the reduced L versus M signal strength is proportional to the reduction in L versus M contrast detection thresholds"
- Emery 2021 (NB-verified): "L vs M sensitivity differences arise when information from the cones is first combined into color-opponent signals"
- DeMarco-Pokorny-Smith 1992: cone fundamentals → Δλ direct
- Boehm 2014: Lamb 1995 cone formula at Δλ grid {3, 8, 13 nm}
- → "**Threshold sensitivity is set by cone fundamentals**" 문헌 가설

**Δλ source priority** (사용자 lock-in 2026-05-21, JND dual-role 회피):

| Source | sub-08 (deutan) | sub-09 (protan) | 역할 |
|---|---|---|---|
| **(b) DPS 1992 평균값** | M'-L ≈ 6 nm | L'-M ≈ 10 nm | ★ **PRIMARY** (literature, retinal-only assumption) |
| **(c) Boehm 2014 grid** | {3, 8, 13 nm} 중 severity-match | 동일 | Robustness check (literature grid) |
| **(d) JND-derived (Lamb inverse)** | sub-08 JND 8-pair → Δλ 추정 | sub-09 JND 8-pair → Δλ 추정 (data 가용) | Sensitivity supplement ONLY |

> ⚠️ **(d) JND-Lamb-inverse 가 sensitivity supplement only 인 이유 (JND dual-role 회피)**:
> JND 가 §4 의 L_behav_γ loss target 으로 사용됨. (d) 를 primary Δλ source 로 쓰면 *same data fits Δλ then evaluates against same data* = circularity.
> - **(d) 가 acceptable 한 경우**: (b)/(c) 와 *consistent* 한 결과로 *robustness 보강*
> - **(d) 가 unacceptable 한 경우**: (b)/(c) 와 disagreement → (d) 단독 reporting 시 circular
> - **Paper 보고**: "(b) DPS Δλ primary, (c) Boehm robustness, (d) JND-Lamb sensitivity supplement (with caveat on JND dual-role)"

#### §3.1.x Cortical compensation evidence — direct g metric (사용자 lock-in 2026-05-21)

**Method** (Δλ external-fixed → g fit on behavioral data, ΔΔλ method 폐기):

```
Step 1: Δλ external-fixed
  Δλ_protan = 10 nm (DPS, primary)
  Δλ_deutan = 6 nm  (DPS, primary)

Step 2: g fit on L_behav (subject-specific weighting per §4.1)
  g* ← argmin L_behav(α + γ; Δλ_DPS, g)
  
  Sub-08: w_α = w_γ = 0.5 (both informative)
  Sub-09: w_α = 0, w_γ = 1.0 (8AFC ceiling, JND only)
    Justification: sub-09's RSVP 8AFC accuracy = 100.00% (64/64 trials, 0 errors)
                   → L_behav_α uninformative for sub-09. Documented in 
                   future_phase3/results/N7_UPDATE_SUMMARY.md §3.
```

**g interpretation table** (R+C r_cortical = g · r_AT, advisor 정정 2026-05-21 — amplification convention):

| g range | Mechanistic interpretation | Behavior prediction | Expected subject |
|---|---|---|---|
| g = 0 | Cortical zero-out (signal loss) | Discrimination loss | severe CVD (extreme) |
| 0 < g < 1 | Attenuation, no compensation | Behavior follows attenuated retinal | partial CVD |
| g = 1 | HC-like passthrough (baseline) | Behavior reflects retinal directly | sub-08 expected (no compensation) |
| **1 < g < 2** | **Mild amplification compensation** | **Partial behavioral recovery** | partial protan |
| **g ≈ 2-3** | **Strong amplification compensation** | **Behavior ≈ HC despite cone shift** | **sub-09 predicted (if narrative holds)** |
| g = 3 (boundary) | R+C misspecified, 2-Comp 가 primary | Model failure | — |

**Compensation magnitude metric (정정)**:
```
M_compensation = max(0, g* − 1) · Δλ_DPS   # 1을 baseline (HC passthrough) 으로
  
  g = 1 → M = 0 (no compensation)
  g = 2, Δλ = 10 nm → M = 10 nm-equivalent (full restoration)
  g = 3, Δλ = 10 nm → M = 20 nm-equivalent (overcompensation)
```

**Sub-08 vs sub-09 predicted contrast (g ∈ [0,3] amplification convention)**:
```
Sub-08 (deutan, Ishihara 7/14, behavior worse than HC):
  Δλ_deutan = 6 nm fixed
  L_behav fit g* expected:
    g* ≈ 1 (HC-like passthrough, retinal effect 발현)
    or 0 < g* < 1 (attenuation, deficit 더 큼)
  Evidence: NO compensation (M_comp ≈ 0)
  
Sub-09 (protan, Ishihara 9/14 = milder than sub-08, behavior ≈ HC):
  Δλ_protan = 10 nm fixed (DPS lit, but actual severity milder)
  L_behav fit g* expected:
    g* > 1 (amplification compensation possible)
    OR g* ≈ 1 (passthrough + milder severity → 자연 normal behavior)
  Both scenarios → CORTICAL-BEHAVIORAL DISSOCIATION narrative valid
```

**Sub-09 narrative — cortical-behavioral dissociation (사용자 lock-in 2026-05-21)**:
```
Ishihara accuracy:
  Sub-08 deutan: 7/14 plates correct (more impaired)
  Sub-09 protan: 9/14 plates correct (milder severity)

Behavioral (8AFC + JND):
  Sub-08: 82.5% 8AFC, JND HYPO 3/8 yellow-axis (clear deficit)
  Sub-09: 100% 8AFC, JND mostly within HC pool

Neural (fMRI V1):
  Sub-08: V1 LOCO p=0.047*, hV4 p=0.004**
  Sub-09: V1 LOCO p=0.007**, ΔRDM p=0.005** (STRONGEST neural signature)

→ Paper finding: "Mild protan (Ishihara 9/14) with near-normal behavioral discrimination 
  yet persistent V1 neural representation distortion. Suggests cortical-behavioral 
  dissociation — *V1 neural metric may be more sensitive to CVD than standard 
  behavioral measures, especially for mild severity cases*."

→ Dissociation narrative valid regardless of whether sub-09's 100% 8AFC is due to:
  (a) milder CVD severity (cone shift smaller than DPS population mean of 10 nm)
  (b) cortical compensation (g* > 1)
  Both interpretations support the *neural-behavioral asymmetry* claim.

→ Data integrity concerns (a, b, c, e, f) all addressed 2026-05-21 (사용자):
  (a) Logging bug: no concern
  (b) Task interpretation: no concern
  (c) Filter status: no concern
  (d) Subject identity: VERIFIED — Ishihara 9/14 = milder protan, neural V1 signature confirms protan family
  (e) Filter accidentally applied: no concern
  (f) Compensatory learned strategy: no concern (mild severity 가 simpler explanation)
```

**Δλ-source robustness check** (Tier 3, supplementary):
```
For each loss L:
    g*(Δλ_DPS), g*(Δλ_Boehm), g*(Δλ_JND-Lamb)
    Agreement on sign + magnitude → robust compensation claim
    Disagreement → caveat on load-bearing Δλ assumption
```

> **JND 가 Δλ source 인 이유** (NB-verified mapping, 사용자 #3 정정 후): 
> Boehm 2014 의 4AFC discrimination threshold 가 *retinal cone-limited anchor*. Emery 2021: "detection thresholds may instead be limited by very different constraints or levels of the visual system". → JND (2AFC adaptive staircase, hue continuum threshold) 가 retinal anchor.

#### g (cortical opponent gain) — **FIT (1-DOF)**

**정당성**:
- Boehm 2014 (NB-verified): "applying a multiplicative gain (an elliptical stretch of the color space), which boosts saturation"
- Boehm 2014 (NB-verified): "postreceptoral amplification, operating prior to the compressive transformation"
- Tregillus 2021: V2v/V3v 의 sc > 1 (cortical amplification fMRI 측정)
- Emery 2022 (NB-verified): "Gain on the L-M responses independently increased twenty-fold in order to match the range of responses for luminance and chromatic signals" → *theoretical scaffold* (mechanism class 의 존재성 grounding, parametric value comparison 아님)
- Robinson 2022: C ∈ [s, 1] in $y_s = a\log(b(s/C)x)$ — *conceptual* same role, *mathematical form 은 다름* (log nonlinearity vs linear), $g = 1/C$ small-signal mapping (NB-verified CONDITIONAL grounding)

**Bounds**: **g ∈ [0, 3]** (advisor catch 2026-05-21 — sign convention 정정), grid step 0.05 → 61 points
- **이전 g ∈ [-3, +3]** 의 *negative g (inversion)* 은 R+C mechanism 에서 "report cyan when shown red" 의미 → physiologically invalid.
- 진짜 compensation 은 **g > 1 (amplification)** (Boehm 2014 multiplicative gain, Tregillus sc > 1 일관).
- 기존 sub-08 g=-2.25, sub-09 g=-1.10 = *unconstrained 2-DOF joint fit artifact* (MEMORY 의 "non-physiological" flag 정당).
- If fit hits boundary g=0 또는 g=3 → "R+C misspecified for this subject" 명시.

**한계** (Boehm 2021 limitation citation 필수):
- "the results do not support candidate simple models involving post-receptoral compensation either"
- 우리 1-DOF g 는 *leading-order term*, not complete mechanism

### §3.2 2-Comp 의 파라미터

#### θ_conf (confusion axis location) — **FIXED**
- protan: 16°
- deutan: 150°
- Source: Stockman & Sharpe cone fundamentals → isochromatic confusion line

#### β_s (S-cone term amplitude) — **FIT**
- Bounds: [0, 50°], grid step 2° → 26 points

#### β_c (confusion axis term amplitude) — **FIT**
- Bounds: [-50, +50°], grid step 2° → 51 points

**Total grid**: 26 × 51 = 1326 points (현재 코드 reuse)

**정당성** (cardinal axis 위치만, cosine form 자체는 mathematical):
- Krauskopf, Williams & Heeley 1982: cardinal cone-opponent axes
- Stockman: confusion axis derivation
- **Cosine form 자체** = 1st-harmonic Fourier (mathematical), *cortical mechanism claim 없음* (Emery 2021 disclaimer 와 평행 구조)

**한계 (정직히 명시)**:
- Prior art 없음 — novel descriptor
- Cosine 대칭성으로 sub-08 warm-side 비대칭 capture 불가
- Cardinal axes 가 cortex 에서 유지되지 않을 가능성 (Parkes 2009)

---

## §4. 활용 손실함수 + 피팅 방법

### §4.1 Behavioral loss — α + γ + β (사용자 lock-in 2026-05-21)

**Subject-specific weighting (8AFC ceiling 정당화)**:
```
L_behav(params) = w_α(subj) · L_behav_α + w_γ(subj) · L_behav_γ

Sub-08 (deutan):  w_α = 0.5, w_γ = 0.5   (8AFC=82.54%, both informative)
Sub-09 (protan):  w_α = 0.0, w_γ = 1.0   (8AFC=100.00%, ceiling, JND only)
                  → Justification: future_phase3/results/N7_UPDATE_SUMMARY.md §3
                                   sub-09 RSVP 64/64 correct, 0 errors → L_behav_α uninformative

HC pool (for sigma_HC fit only): use whichever HC has 8AFC data (sub-01/03/06/07)
```

**Α (per-color 8AFC accuracy MSE)** — lock-in:

```
L_behav_α(params) = Σ_hue [8AFC_pred(c; params) − 8AFC_obs(c)]²
                    ─────────────────────────  ────────────────
                    softmax distance derived    sub-08 RSVP 64 trial
                    from hue_perceived(c)       (data/behavior/...csv)
```

**8AFC prediction form** (softmax over hue distance):

```
hue_perceived(c; params) ← model output (R+C g or 2-Comp β_s, β_c)

P(response = j | stim = i; params, σ) ∝ exp(−|hue_perceived(i) − hue_target(j)|² / σ²)
                                          ────────────────────────────────────────────
                                          softmax distance, hue space modular

8AFC_accuracy_pred(i) = P(response = i | stim = i; ...)

σ: hue-space response noise (degrees)
```

**σ fixed primary (사용자 결정 2026-05-21, joint fit identifiability 인정)**:

**Joint fit 폐기 rationale**: (δθ, σ) likelihood landscape 가 *isolikelihood contour valley* — same 8AFC accuracy 가 (large δθ, small σ) 와 (small δθ, large σ) 둘 다 만족. Joint fit 의 argmin 도 *non-unique on contour*. Grid resolution 증가로 해결 안 됨.

**Fixed σ 의 정당화 — empirical primary + literature plausibility (NOT dual anchor)**:

> ⚠️ **Honest framing correction (사용자 catch, 2026-05-22)**:
> 이전 표현 "dual anchor" 는 *overstatement*. Literature 값들은 우리와 *동일 측정* 의 independent replication 이 아니다. 따라서 *plausibility check* 으로만 사용하고, 진정한 anchor 는 (1) HC empirical pooled fit 과 (3) σ-sensitivity sweep.

**1. Primary empirical anchor** (HC pooled, our own paradigm): **σ_HC = 20.96° ≈ 21.0°**
   - N=4 HC (sub-01, 03, 06, 07) × 64 trials = 255 trials pooled
   - sub-01 degenerate (100% accuracy → σ unidentified at floor) 제외 시 mean = 21.62°
   - **우리 task = 8AFC RSVP grating identification (drift 0.8s), Stockman opponent hue space** — σ 정의/단위 직접 일치

**2. Literature plausibility range (NOT independent measurement of same quantity)**:

   각 literature 가 우리와 *차원/개념 다름* 을 명시:

   | Source | Task | Quantity reported | 우리와 차이 |
   |---|---|---|---|
   | Schurgin et al. 2020 (TCC) | Color **working memory** continuous report (CIELAB wheel) | recall SD = encoding + maintenance + recall noise | WM ≠ immediate perception; CIELAB ≠ Stockman |
   | Bae et al. 2015 | Color **working memory** delay-dependent SD | 동상, *delay-dependent* | 동상 |
   | Witzel & Gegenfurtner 2018 | DKL **2AFC threshold** (JND) | 75% accuracy difference (deg) | metric ≠ softmax σ; DKL ≠ Stockman |

   → Literature reports σ-like quantities ∈ **18-25°** in *non-equivalent paradigms*.

   **Claim 가능한 것**: "σ_HC = 21° 는 color discrimination/memory literature 의 *order of magnitude* 와 양립 (10° 도 아니고 100° 도 아님)."

   **Claim 불가능한 것**: "literature 가 σ=21° 를 *replicates*". 다른 task, 다른 noise component, 다른 stim space.

**3. Real robustness defense — σ-sensitivity sweep** (paper-level primary defense):
```
σ candidates ∈ {15°, 18°, 21°, 24°, 28°}
For each σ_value, all fits (R+C + 2-Comp × all losses) repeat
Primary verdict 가 σ choice 에 invariant 인지 검증
→ If invariant: σ=21° 결과 robust (paper claim 유지)
→ If σ-sensitive: paper limitation 명시 + range of estimates 보고
```

**Reviewer 대응 framing** (Nat Comms / top neuro journal):
- "What is the basis of σ=21°?" → "Primary: our HC pooled 8AFC fit (n=4, 255 trials, same paradigm). Secondary: sensitivity sweep ∈ {15-28°} shows verdict invariance. We do *not* claim equivalence to working-memory or threshold literatures, which measure different quantities in different paradigms; their range (18-25°) is reported only as plausibility context."

**Robustness sensitivity sweep**:
```
σ candidates ∈ {15°, 18°, 21°, 24°, 28°}
For each σ_value, all fits (R+C + 2-Comp × all losses) repeat
Primary verdict 가 σ choice 에 invariant 인지 검증
→ If invariant: σ=21° 결과 robust
→ If σ-sensitive: paper limitation 명시 + range of estimates 보고
```

**δθ inflation 우려 (advisor catch) 의 paper-level 대응**:
- σ fixed = "deficit 이 δθ 로 attribution 된다" 가정
- 우리 paper claim: "Given σ_HC reference, R+C g* 와 2-Comp (β_s, β_c)* 는 *cortical structural distortion* 추정"
- Caveat: "Estimates assume HC-equivalent response noise. If CVD response variability differs, δθ may be overestimated."
- Sub-09 의 *response variability* check (RT distribution comparable to HC) 로 partial validation

**HC pool σ baseline (still computed for context)**:
HC 8AFC data — `data/behavior/sub-{01,03,06,07}_rsvp_8afc_ses1_run1.csv` (N=4 HC).

**Fitted σ_HC results (scripts/fit_sigma_hc_8afc.py 실행 결과 2026-05-21)**:
| Subject | N trials | Accuracy | σ_fit (°) |
|---|---|---|---|
| sub-01 | 64 | 100.00% | 6.39 (degenerate, floor) |
| sub-03 | 64 | 95.31% | 22.19 |
| sub-06 | 63 | 98.41% | 20.51 |
| sub-07 | 64 | 96.88% | 22.15 |
| **Pooled HC (4-subj combined 8×8)** | **255** | **97.65%** | **σ_HC = 20.96°** |
| Excluding sub-01 degenerate | — | — | mean = 21.62° |

→ **σ_HC primary = 21.0°** (pooled fit). Sensitivity sweep ∈ {15°, 18°, 21°, 24°, 28°} for robustness.

```python
# Step 1: HC 별 σ_HC[h] 직접 fit (per HC, training-time)
For each HC h ∈ {sub-01, sub-03, sub-06, sub-07}:
    confusion_h = build_8x8_confusion_matrix(h's 64 trials)  
    # Fit σ to HC's own confusion (assume δθ=0, i.e., normal cone, no rotation):
    σ_HC[h] = argmin_σ Σ_{i,j} [softmax(δθ=0, σ)[i,j] − confusion_h[i,j]]²

# Step 2: σ_HC distribution → 결정
σ_HC_mean = mean([σ_HC[h] for h in HCs])    # ≈ 3-5° expected (97.3% acc)
σ_HC_sd   = std([σ_HC[h] for h in HCs])     # inter-subject variability

# Step 3: σ usage
# Primary: σ = σ_HC_mean (population estimate)
# Robustness: σ sweep ∈ {σ_HC_mean ± σ_HC_sd, ± 2·σ_HC_sd}
#             paper supplement에 sensitivity reporting
```

**σ 의 의미**: HC 97.3% accuracy 의 *implicit hue-space noise* (degrees). δθ=0 (no cortical rotation) 가정 하에 fit. HC 가 *baseline reference* → CVD 의 δθ 추정 시 HC σ 사용 (response noise 는 invariant 가정).

**가정 (A_σ)**: "Response noise σ 가 HC = CVD 동일" (CVD 차이는 δθ 에만 있음). 한계: CVD 의 response variability 가 더 클 수 있음 → sub-08 confusion 자체에서도 σ_sub08 fit 가능, σ_HC_mean 와 비교 robustness check.

⚠️ **이전 "≈ 10°" claim 정정**: 사용자 첫 lock-in 의 "HC pool's empirical inter-subject SD ≈ 10°" 는 *speculative* 였음. HC 8AFC 가 실제로 존재 (N=4) → 위 fit procedure 로 정확한 σ 도출.

**Γ NEW (per-pair JND MSE)** — lock-in, sub-08 + sub-09 모두 informative:

```
L_behav_γ(params) = Σ_p [JND_pred(p; params) − JND_obs(p)]² / σ_p²
                    ─────────────────────────────────────────────
                    per-pair weighted MSE (8 pairs), σ_p = HC pool SD per pair

JND prediction (perceived-space compression/expansion):
  For pair p = (θ_a, θ_b):
    d_phys(p) = |θ_a − θ_b|  (modular)
    d_perc(p; params) = |θ_a + δθ(θ_a) − θ_b − δθ(θ_b)|  (modular)
    JND_pred(p) = JND_HC_baseline(p) × (d_phys / d_perc)
  
  HC (δθ=0): d_perc = d_phys → JND_pred = JND_HC_baseline ✓
  Compression: d_perc < d_phys → JND_pred > baseline → HYPO predicted
  Expansion:   d_perc > d_phys → JND_pred < baseline → HYPER predicted

JND data status (2026-05-21):
  - Sub-08: data/behavior/sub-08_jnd_ses1_no_filter_summary.csv (8 pairs × 2 staircases)
  - Sub-09: data/behavior/sub-09_jnd_ses1_no_filter_summary.csv (가용, 1 HYPO + 3 HYPER signature)
  - HC: sub-01~07 모두 가용, σ_p (per-pair HC SD) 계산 가능
```

**Β robustness check (per-pair confusion structure)** — supplementary:

```
L_behav_β(params) = -Σ_(i,j) log P(response = j | stim = i; params)
                    ────────────────────────────────────────────────
                    negative log-likelihood on full 8×8 confusion matrix
```

- Sub-08: 64 trial / 8×8 = ~1 trial/cell. Sparse — robustness check only.
- Sub-09: ceiling — uninformative

### §4.2 Neural loss — 후보 3 종, Pareto-optimal 선정

#### §4.2.0 Input data structure

```
C010 amplitudes (per subject, per ROI):
  shape = (N_RUNS, N_COLORS, N_VOXELS) = (6, 8, V_s)
  
  - V_s varies by ROI: V1, V2, V3, hV4
  - sub-07 hV4: V_s = 16 (sparse) → NaN handling required
  
File: derivatives/full_dataset_C010/{subject}/{ROI}/amplitudes_procrustes.npy
ROI 별 K (basis channels): V1=4, V2=4, V3=3, hV4=3 (MEMORY 기록)
```

#### §4.2.1 Step 1 — Run-averaging (per color, per subject)

```python
Y_subj_ROI = amplitudes.mean(axis=0)  # shape: (8, V_s)
# Y[c] = mean voxel pattern at color c (across 6 runs)
```

#### §4.2.2 Step 2 — HC encoder W (ridge regression, GCV)

```python
# For each HC subject independently (per ROI):
C_pooled = np.tile(C_baseline, (N_RUNS, 1))  # (48, K), K=3 for hV4
X_all = amplitudes.reshape(-1, V_s)          # (48, V_s)

alpha_GCV = gcv_select_alpha(C_pooled, X_all)
W_HC[subj] = fit_W_ridge(C_pooled, X_all, alpha_GCV)  # shape: (K, V_s)
```

#### §4.2.3 Step 3a — LOCO ρ (interpolation accuracy)

```python
# For each held-out color c:
train_colors = [c' for c' in range(8) if c' != c]  # 7 colors
X_train = amplitudes[:, train_colors].reshape(-1, V_s)  # (42, V_s)
C_train = np.tile(C_shifted[train_colors], (N_RUNS, 1))  # (42, K)

alpha = gcv_select_alpha(C_train, X_train)
W = fit_W_ridge(C_train, X_train, alpha)

# Predict held-out color's pattern:
Y_pred = C_shifted[c:c+1] @ W  # (1, V_s)
Y_actual = amplitudes[:, c].mean(axis=0, keepdims=True)  # (1, V_s)

LOCO_rho[c] = pearson_r(Y_pred[0], Y_actual[0])  # scalar
```

→ **LOCO_rho shape (8,) per subject per ROI** — per-color interpolation accuracy.

#### §4.2.4 Step 3b — RDM (per-pair dissimilarity, *primary form*)

```python
from scipy.spatial.distance import pdist

# Per subject, per ROI — correlation distance (primary):
patterns = amplitudes.mean(axis=0)  # (8, V_s), run-averaged
rdm = pdist(patterns, metric='correlation')  # (28,) = 1 - Pearson_r between hue pairs
                                                # Upper triangle of 8×8 matrix
```

→ **RDM shape (28,) per subject per ROI** — primary RDM form.

#### §4.2.5 Step 3c — ΔRDM (CVD - HC difference)

```python
# Observation side (no W, pure data):
RDM_CVD = pdist(amplitudes_CVD.mean(axis=0), metric='correlation')   # (28,)
RDM_HC_mean = mean([pdist(amplitudes_HC[s].mean(axis=0), metric='correlation') 
                     for s in HC_pool], axis=0)
ΔRDM_obs = RDM_CVD - RDM_HC_mean  # (28,)

# Simulation side (with W, model-dependent):
Y_shifted = C_shifted @ W_HC_mean   # (8, V_s)
Y_baseline = C_baseline @ W_HC_mean  # (8, V_s)

RDM_shifted = pdist(Y_shifted, metric='correlation')
RDM_baseline = pdist(Y_baseline, metric='correlation')
ΔRDM_sim = RDM_shifted - RDM_baseline  # (28,)
```

#### §4.2.6 Step 3d — Crossnobis ΔRDM (robustness check, R-1 (b) lock-in 2026-05-21)

```python
# Cross-validated Mahalanobis distance, noise-normalized:
def compute_rdm_crossnobis(amplitudes):
    # amplitudes: (N_RUNS, N_COLORS, V_s)
    sigma_reg = estimate_noise_cov(amplitudes)  # shrinkage-regularized
    L_inv = cholesky_inverse(sigma_reg)         # whitening matrix
    
    rdm_sum = np.zeros((n_colors, n_colors))
    n_pairs = 0
    for a in range(n_runs):
        for b in range(a+1, n_runs):
            pat_a = amplitudes[a] @ L_inv
            pat_b = amplitudes[b] @ L_inv
            for i in range(n_colors):
                for j in range(i+1, n_colors):
                    diff_a = pat_a[i] - pat_a[j]
                    diff_b = pat_b[i] - pat_b[j]
                    rdm_sum[i, j] += np.dot(diff_a, diff_b)
            n_pairs += 1
    return rdm_sum / n_pairs  # 28-vec, can be negative (unbiased)
```

→ Walther 2016 standard. **Robustness check 위치** — primary L_RDM 은 correlation distance, Crossnobis 는 *paper supplement* 의 agreement check.

#### §4.2.7 Step 3e — W 의 *비대칭* 명시 (RDM 의 obs vs sim)

| Computation | W 사용 여부 | 의미 |
|---|---|---|
| RDM_obs (CVD or HC) | ❌ | Pure data, observation pattern 거리 |
| ΔRDM_obs = RDM_CVD − RDM_HC_mean | ❌ | Pure data difference |
| LOCO_rho | ✓ (training data 의 W) | Forward prediction accuracy |
| ΔRDM_sim | ✓ (HC pool 의 W) | Model 의 *예측 distortion* |

**가정 (A1)**: "HC 의 W 가 CVD 에도 valid". 가정 깨지면 모든 *_sim 계산이 무의미.

#### §4.2.8 SRM-based RDM — paper 의 *다른 section*

Project memory 2026-03-22 직접:
> "RDM criterion FAILED all ROIs: **SRM alignment absorbs cone shift signal**"

→ SRM shared-space RDM 은 *cone-shift signal absorption* 으로 *fitting criterion 으로 부적합*. 단 *existence evidence* 의 paper-level role:

| RDM type | Paper 위치 | 우리 본 plan |
|---|---|---|
| **Voxel-space correlation distance ΔRDM** | Methods §fitting | ★ Primary L_RDM (본 plan) |
| **Crossnobis ΔRDM** | Methods supplement | Robustness check (§4.2.6) |
| **SRM shared-space RDM** | Results §existence (distortion 의 *존재 evidence*) | 별도 작업 (`phase2_SRM_across_between/`) |

#### §4.2.9 8 candidate losses for fitting (사용자 lock-in 2026-05-21: L8 primary)

**Individual losses (4):**
```
L1: L_behav_α  (per-color 8AFC softmax MSE)             — sub-08 ✓, sub-09 ceiling ✗
L2: L_behav_γ  (per-pair JND weighted MSE)              — sub-08 ✓, sub-09 ✓
L3: L_LOCO     (per-color hold-out interpolation MSE)   — both ✓
L4: L_RDM      (1 − cos(ΔRDM_sim, ΔRDM_obs))            — both ✓
                + Crossnobis variant for robustness
```

**Combined losses (4):**
```
L5: L_behav         = w_α(subj)·L1 + w_γ(subj)·L2       — behavioral composite
                       (subject-specific weights per §4.1)
                       
L6: L_neural        = 0.5·L3 + 0.5·L4                   — neural composite (modality-equal)

L7: L_all_equal     = (L1 + L2 + L3 + L4) / 4           — uniform 4-way mix

L8: L_modality_5050 ★ PRIMARY UNIFORM (advisor 정정 2026-05-21)
                  = 0.5·L_γ + 0.25·L_LOCO + 0.25·L_RDM     (both sub-08 and sub-09)
                  
                  Rationale: sub-08 의 L1 (8AFC) 정보 손실 in L8 specifically,
                            for cross-subject comparability under L8.
                            L1 정보 보존: 별도 L1-only fit (=L1 standalone) 결과 보고.
                  
                  Why drop L1 across all subjects (not just sub-09):
                    - Subject-specific L8 (sub-08: 4 components, sub-09: 3) →
                      cross-subject g*/argmin comparisons compare *different objectives*
                    - §6.4 cross-subtype train-test (sub-08 L8 → sub-09 apply) would 
                      be confounded by loss-form difference, not mechanism difference
                    - Solution: L8 uniform across subjects, L1 informativeness checked separately
```

**Loss scale normalization (important)**:
Before combining, each L_i is z-scored against its HC baseline distribution:
```
L_i_normalized = (L_i − μ_HC_pool_Li) / σ_HC_pool_Li
```
→ Combined losses are *scale-invariant*. Prevents L_RDM (∈ [0, 2]) 또는 L_LOCO (∈ [0, ∞]) 가 raw scale 차이로 dominate.

**Sub-09 의 L_behav_α weight=0 정당화 (advisor potential challenge 대비)**:
- 8AFC = 100.00% accuracy (sub-09, 64 trials, 0 errors)
- Reference: `future_phase3_behavioral_analysis/results/N7_UPDATE_SUMMARY.md §3` + `analyze_jnd_sub09.py` output
- Any params* (any g, β_s, β_c) producing softmax with non-degenerate σ predicts >90% accuracy → ceiling
- ∴ L_behav_α(any params; sub-09 obs) ≈ 0 → no gradient → uninformative
- Solution: drop L_behav_α for sub-09, use L_behav_γ alone (sub-09 JND HYPO 1/8 + HYPER 3/8 + ≈HC 4/8 = sufficient signal)

#### §4.2.10 ROI 결정

- **Primary fit ROI**: hV4 (Phase 1 forward LOCO gate p=0.044)
- **Supplementary**: V1, V2, V3 별도 fit → hierarchical decomposition (Tregillus V1<V2v<V3v 등가)

> **LORO 비활용** (사용자 lock-in 2026-05-21).

### §4.3 Joint loss (conditional)

```
If behav-only argmin ≈ neural-only argmin (equivalence test pass):
    → Joint fit *불필요*. paper 본문 "행동-신경 일치" 보고.

Else:
    L_joint(params; λ) = λ · L_behav_α + (1−λ) · L_neural_best
    λ sweep ∈ {0, 0.25, 0.5, 0.75, 1}
    For each λ:
        argmin params, predict held-out (behav + neural)
        Loss prediction MSE → λ_optimal
```

### §4.4 Fitting procedure — All-paths (no pre-selection)

**Framework**: 두 모델 × 8 loss × (R+C 의 경우) 3 Δλ source = full matrix. Primary L8 + all others 도 fit (post-hoc convergence check).

#### R+C 1-DOF (g only) — Δλ external-fixed
```python
g_grid = np.arange(-3.0, 3.0 + 0.05, 0.05)  # 121 points

For each Δλ_source in {DPS_primary, Boehm_robustness, JND_Lamb_supplement}:
    For each loss L in {L1, L2, L3, L4, L5, L6, L7, L8}:
        For each g in g_grid:
            δθ = forward_RC(Δλ_source, g, cvd_type)
            L_value[g] = compute_loss(L, δθ; subject)
        
        g*[Δλ_source, L] = argmin L_value
        Record (M=R+C, Δλ_source, L, g*, L_min)
```

#### 2-Comp 2-DOF (β_s, β_c)
```python
bs_grid = np.arange(0.0, 50.0 + 2.0, 2.0)    # 26 points
bc_grid = np.arange(-50.0, 50.0 + 2.0, 2.0)  # 51 points

For each loss L in {L1, L2, L3, L4, L5, L6, L7, L8}:
    For each (β_s, β_c) in 1326 combinations:
        δθ = forward_2comp(β_s, β_c, cvd_type)
        L_value[β_s, β_c] = compute_loss(L, δθ; subject)
    
    (β_s, β_c)*[L] = argmin L_value
    Record (M=2-Comp, L, (β_s, β_c)*, L_min)
```

#### Total fit count per subject

| Model | Fits per subject |
|---|---|
| R+C  | 3 (Δλ-source) × 8 (loss) = **24** |
| 2-Comp | 1 × 8 (loss) = **8** |
| **Combined per subject** | **32 argmin params** |

3 subjects (sub-08, sub-09, sub-10 normal control) × 7-fold LOO = **672 total fits**.

Wall time (revised 2026-05-21 — σ fixed at 21°, joint fit grid 폐기):
- R+C: 61 g grid × 24 paths × 7 LOO × 3 subj ≈ 31k evals
- 2-Comp: 1326 × 8 × 7 × 3 ≈ 223k evals
- σ sensitivity sweep (×5): 5× total → ~1.3M evals
- At ~0.1s/eval: ~2h with σ sweep, ~30 min without
- **SLURM on node2** (interactive 가능, overnight 불필요)

---

## §5. 모델 평가 지표

### §5.1 Loss selection criteria — AIC, BIC, 8AFC corr as separate standard metrics (사용자 lock-in 2026-05-21, advisor catch 반영)

**Reframed (composite rank 제거)**: AIC 와 BIC 는 동일 RSS+DOF 기반 → composite weighting 가 *3 independent signals* 가정 wrong. 각 metric 을 **standard separate metric** 으로 보고. *Selection 은 training set 에서만 일어남* (LOO 의 outer fold 별로 fold-specific selection).

| Criterion | Computation (training set 6 HC + CVD) | Direction | Role |
|---|---|---|---|
| **(a) Training 8AFC correlation** | predicted 8AFC vs CVD observed 8AFC — Pearson r | maximize | Behavioral fit quality |
| **(b) AICc** | n=8, k=DOF, RSS = neural loss residual + finite-sample correction | minimize | Neural fit + parsimony (small-sample) |
| **(c) BIC** | 동일, k·log(n) penalty | minimize | Neural fit + parsimony (Bayesian motivation) |

**Selection rule (Pareto-style)**:
```python
# Report all 3 criteria per (M, L) candidate
For each (M, L):
    report (AICc[M,L], BIC[M,L], 8AFC_corr[M,L])

# Three convergent verdicts (강) — three criteria agree on winner:
If AICc_best == BIC_best == 8AFC_corr_best:
    (M*, L*) = unanimous winner — STRONGEST evidence

# Two convergent (중) — neural + behavioral OR neural + neural:
ElIf AICc_best == BIC_best ≠ 8AFC_corr_best:
    (M*, L*) = AICc/BIC winner, but limitation: "behavioral signal differs"
ElIf (AICc_best == 8AFC_corr_best) or (BIC_best == 8AFC_corr_best):
    (M*, L*) = the pair-agreement winner, weaker evidence

# All disagree (약) — paper limitation:
Else:
    Report all 3 (M*, L*) candidates + paper limitation
```

**Verdict 표현**:
- "AICc, BIC, training 8AFC corr 모두 (M*, L*) 를 prefer" → strongest
- 부분 agreement → 해당 criterion 명시
- 모두 disagree → no clear winner, all candidates 보고 + paper limitation

**ΔAICc / ΔBIC interpretation** (Kass & Raftery 1995):
- |Δ| < 2: indistinguishable
- 2-6: moderate evidence
- 6-10: strong evidence
- > 10: very strong

### §5.2 Model comparison — AICc + BIC (사용자 lock-in 2026-05-21)

```python
def compute_AICc(rss, n_data, k_params):
    aic = n_data * np.log(rss / n_data) + 2 * k_params
    correction = 2 * k_params * (k_params + 1) / (n_data - k_params - 1)
    return aic + correction

def compute_BIC(rss, n_data, k_params):
    return n_data * np.log(rss / n_data) + k_params * np.log(n_data)
```

**n=8 (per-color), small-sample regime**:

| Penalty | R+C (k=1) | 2-Comp (k=2) | Difference |
|---|---|---|---|
| AICc | 2 + 4/6 ≈ 2.67 | 4 + 12/5 ≈ 6.40 | 3.73 |
| BIC | log(8) ≈ 2.08 | 2log(8) ≈ 4.16 | 2.08 |

→ **AICc 가 small-sample 에서 *더 보수적*** (finite-sample correction). BIC 는 large-n 에서 일반적으로 더 보수적이나 n=8 에선 차이 작음. **둘 다 보고 + agreement 시 robust**.

**Verdict criteria**:
- AICc, BIC agree (둘 다 같은 모델 prefer) → **robust**
- AICc, BIC disagree → criterion sensitivity; **conservative reading = R+C** (DOF parsimony)
- ΔAICc / ΔBIC interpretation:
  - |Δ| < 2: indistinguishable
  - 2-6: moderate evidence
  - 6-10: strong evidence
  - > 10: very strong (Kass & Raftery 1995 BIC convention)

### §5.3 Cross-model δθ(c) convergence

```python
def cross_model_convergence(delta_theta_RC, delta_theta_2C):
    """ Both 8-vec per color """
    cosine_sim = np.dot(delta_theta_RC, delta_theta_2C) / (
        np.linalg.norm(delta_theta_RC) * np.linalg.norm(delta_theta_2C))
    mae_deg = np.mean(np.abs(delta_theta_RC - delta_theta_2C))
    return cosine_sim, mae_deg
```

Verdict:
- cos > 0.7 AND MAE < 10°: **strong convergence** (두 모델 같은 distortion 묘사)
- cos > 0.5 AND MAE < 20°: moderate
- 이하: divergence (paper limitation)

### §5.4 Convergence check — 32-fit matrix per subject (사용자 lock-in 2026-05-21)

**Goal**: 32 argmin params 가 *서로 일치하는가* — Post-hoc model-loss preference 검정.

#### §5.4.1 Within-model loss convergence

```
For R+C (per Δλ source), 8 loss → 8 g* values:
  Pairwise TOST + BF on |g*_i − g*_j| < Δ_g  for 28 pairs (8 choose 2)
  
For 2-Comp, 8 loss → 8 (β_s, β_c)* values:
  Pairwise TOST + BF on ||(β_s, β_c)*_i − (β_s, β_c)*_j|| < Δ_β  for 28 pairs
  
Verdict:
  All 28 pairs equivalent → "Model robust across loss targets"
  Loss-specific clusters (e.g., {L1,L5,L7,L8} agree, {L3,L4,L6} agree) 
    → Cluster structure 명시: behavioral-cluster vs neural-cluster
```

#### §5.4.2 Within-model Δλ source convergence (R+C only)

```
For each loss L (8), 3 Δλ-sources → 3 g* values:
  Pairwise TOST on |g*_{DPS} − g*_{Boehm}|, |g*_{DPS} − g*_{JND}|, |g*_{Boehm} − g*_{JND}|
  
Verdict:
  All 3 sources agree → "Cortical compensation g robust to Δλ assumption"
  Disagreement → Δλ source 의 load-bearing nature 명시
```

#### §5.4.3 Cross-model δθ convergence (사용자 핵심 통찰: "validation 으로 일치여부")

```
R+C 의 g* → δθ_RC(c) 8-vec  (forward map at fit params)
2-Comp 의 (β_s, β_c)* → δθ_2C(c) 8-vec

For each (loss_RC, loss_2C) pair (8 × 8 = 64 combinations):
    TOST on ||δθ_RC − δθ_2C||² < Δ_δθ²
    Spearman correlation per (loss_RC, loss_2C) → 8-vec rank correspondence
    
Verdict:
  Models converge on δθ(c) → "Two parameterizations of same underlying distortion"
  Models diverge → "Models capture different aspects of CVD distortion"
```

#### §5.4.4 Behavioral-Neural equivalence test — TOST + BF₀₁ + n=2 limitation

**TOST (Two One-Sided Tests, Schuirmann 1987 / Lakens 2017)**:
Standard t-test 의 H₀: μ=0 → "diff 있다 vs 없다" 검정. *diff 없음* 의 power 부족 vs 진짜 같음 구분 불가. TOST reframe:

```
사전 정의 equivalence band Δ (e.g., 10°)
H₀: |argmin_behav − argmin_neural| ≥ Δ  (의미있게 다름)
H₁: |argmin_behav − argmin_neural| < Δ  (equivalent)

Test 1 (upper): H₀a: diff ≥ +Δ → one-sided t-test, p_a
Test 2 (lower): H₀b: diff ≤ −Δ → one-sided t-test, p_b
Verdict:
  둘 다 p < α (e.g., 0.05) → H₁ accept ("equivalent within ±Δ")
  한쪽이라도 p ≥ α → "cannot conclude equivalence" (≠ "different")

Δ band: HC pool inter-subject SD-derived (e.g., σ(β_s)+σ(β_c) ≈ 10°)
```

**Bayes factor BF₀₁ (Rouder 2009)**:
```
M1: behav and neural argmin from *different* distribution
M0: *same* distribution
BF₀₁ > 3 → evidence for equivalence (continuous quantification)
BF₀₁ < 1/3 → evidence against (separation)
1/3 ≤ BF₀₁ ≤ 3 → inconclusive
```

**TOST 와 BF₀₁ 보완**:
- TOST = frequentist (reject-null logic), journal 친화
- BF₀₁ = Bayesian (evidence ratio), inconclusive 결과 명시 가능
- 둘 다 보고 → robust verdict

> ⚠️ **n=2 CVD detection power limitation (advisor catch 2026-05-21)**:
> - Per-subject TOST 가능 (bootstrap CI over CVD's 8-color data) — sub-08, sub-09 각각 독립 검정
> - **Group-level TOST 한계**: n=2 의 t-test CI 가 Δ band (≈10°) 보다 큼 → 거의 항상 "cannot conclude equivalence" verdict
> - **Solution**: 
>   - **Per-subject 단일 detection** 결과 보고 (sub-08, sub-09 각자)
>   - Group-level pooled TOST 는 *supplementary* (low power 명시)
>   - **Sub-09 acquisition 후** n=2 → effective n 증가 (sub-08+sub-09 + sub-10 normal control → pooled)
>   - **Cross-subtype train-test (§6.4)** 가 subtype 차이 evidence 의 보완 — *separate test*

### §5.4' Test metric concordance — all three equal weight (사용자 lock-in 2026-05-21)

LOO outer fold (held-out HC h) 의 test 는 **3 metric equal weight + cross-correlation**:

| Metric | Form | Test 의미 |
|---|---|---|
| **(X) LOCO ρ via h** | h's W_h @ C_shifted(params*) 의 LOCO ρ vs actual CVD LOCO ρ — MSE per color | h's encoder + transferred params → CVD per-color interpolation 재현? |
| **(Y) ΔRDM via h** | h's W_h @ C_shifted(params*) 의 RDM vs actual CVD ΔRDM — 1−cos | h's encoder + params → CVD pairwise distortion 재현? |
| **(Z) 8AFC accuracy** | params* → δθ → softmax 8AFC pred vs actual CVD 8AFC — MSE per hue | Params 가 CVD *행동 패턴* 예측? (W-independent) |

**3 metric concordance test** — primary paper-level evidence (Spearman + bootstrap CI, 사용자 lock-in 2026-05-21):

```python
For each fold h, compute (X_h, Y_h, Z_h)
Across 7 folds:
  # Mean ± SD per metric
  X_mean, X_sd = mean(X_h), std(X_h)
  ...
  
  # Cross-correlation (3 × 3 matrix) — Spearman rank correlation (no absolute threshold):
  corr_XY = spearman_r([X_h], [Y_h])  # neural-neural
  corr_XZ = spearman_r([X_h], [Z_h])  # neural-behavioral
  corr_YZ = spearman_r([Y_h], [Z_h])  # neural-behavioral
  
  # Bootstrap CI (B=1000 resamples of 7 folds with replacement):
  for b in range(B):
      resample = bootstrap(folds, n=7, replace=True)
      corr_XY_b[b] = spearman_r(...)
      ...
  CI_XY_95 = percentile(corr_XY_b, [2.5, 97.5])  # bootstrap 95% CI
  
Report per (corr_XY, corr_XZ, corr_YZ):
  - Point estimate (Spearman ρ)
  - 95% bootstrap CI (e.g., [0.12, 0.89])
  - Interpretation: CI excludes 0 → directional evidence
                    CI includes 0 → directional ambiguous
  
NO absolute threshold (e.g., "ρ > 0.7 STRONG") — n=7 Pearson CI ≈ ±0.6
under null is too wide for threshold-based verdict (advisor catch).
```

**Paper-level role (descriptive, not threshold-based)**:
- **(X), (Y) Spearman ρ + 95% CI** → encoder transferability *direction* (CI 가 0 제외하면 directional evidence)
- **(Z) Spearman ρ + 95% CI** → PI 직격 답 ("최종 결과물이 행동 데이터와 유사")
- **Cross-corr matrix CI** → 3 metric 의 dependence structure 보고 (CI included 0 → independent aspect)
- **Verdict 표현**: "Spearman ρ=X.XX [95% CI: low, high]" — *threshold-free*

### §5.5 Specificity metrics (Tier 1, `specificity_metrics_candidates.md` 참조)

- **B1/B2** Bayes factor (separation + equivalence)
- **E1** TOST
- **P3** Full-grid permutation null (selection-aware) ← PI critique D1 직격
- **C1** LDA + LOO-CV (Emery k-means 의 우리식 등가)

Tier 2 supplementary:
- **M1** Mahalanobis distance (descriptive percentile)
- **P2** Baseline-corrected permutation (HC FPR 의 root cause check)

---

## §6. Ablation + LOO 계획

### §6.1 Ablation 1: Behav-only vs Neural-only vs Joint (PI 핵심 답)

For each model M ∈ {R+C 1-DOF, 2-Comp 2-DOF}:

| Variant | Fit data | Free DOF | Purpose |
|---|---|---|---|
| M_behav | 8AFC only (α primary) | Same as M | Pure behavioral fit |
| M_neural | fMRI only (best L from §5.1) | Same as M | Pure neural fit |
| M_joint (λ sweep) | both | Same as M | conditional, if behav ≠ neural |

**핵심 검정**: 
1. M_behav ≈ M_neural? → equivalence test (§5.4)
2. M_joint 이 single-modality 보다 *나은가*? → held-out prediction error

### §6.2 Ablation 2: ROI hierarchical (Tregillus V1<V4 등가)

```
For each ROI ∈ {V1, V2, V3, hV4}:
    Fit R+C g_ROI and 2-Comp (β_s, β_c)_ROI separately
    
Report:
    - g_ROI 의 hierarchical trend (Tregillus V1 reduction → V2v/V3v amplification 의 우리 등가)
    - δθ(c)_ROI 의 cross-ROI consistency
```

### §6.3 LOO scheme — Single-level outer + selection on training + transfer test (사용자 lock-in 2026-05-21)

**Rationale (사용자 비판적 통찰)**: Nested CV 의 inner LOO 는 우리 small-N (HC=7) 에 *과한 statistical machinery*. AIC/BIC + behavioral correlation 이 *selection variance 의 sufficient control* (Krstajic 2014, Varma & Simon 2006). PI 원문 "엔드투엔드로 모델 선정에서도 LOO" = *각 outer fold 마다 selection 다시 수행* (해석 B), nested 가 아닌 single-level 의 자연스러운 표현.

**Color LOCO 의 inner level 제거 (사용자 비판 정확)**: 우리 model 이 *closed-form forward map* 이므로 color LOCO 는 *strong test 아님*. 별도 Bootstrap CI of params 가 *characterization* 역할 (T-1 Form A).

#### §6.3.1 정확한 form

```
Outer LOO: HC 7-fold (single-level)

For each held-out HC h ∈ {sub-01, ..., sub-07}:
    Training pool: 6 HC + CVD's actual data
    
    Step 1 — Selection on training pool (each (M, L) ∈ 6 combinations):
        Fit (M, L) using 6 HC W (mean) + CVD's actual response
        Compute 3 selection criteria on training (§5.1 standard separate metrics):
            - AICc (DOF-fair, n=8, finite-sample correction)
            - BIC (DOF-fair, n=8)
            - Training 8AFC correlation (Pearson r)
        Selection rule:
            - If 3 criteria agree on (M*, L*) → unanimous winner
            - Partial agreement → pair-agreement winner + limitation note
            - All disagree → all candidates retained, paper limitation
        Output: best (M*, L*, params*) per fold
    
    Step 2 — Transfer test on held-out HC h:
        Apply params* with W_h (held-out HC's encoder):
        
        (X) Per-color LOCO ρ:
            Y_pred = W_h @ C_shifted(params*)  # (8, V_s of h)
            LOCO_ρ_pred = compute_LOCO_ρ(Y_pred)
            X_h = MSE(LOCO_ρ_pred, LOCO_ρ_actual_CVD)
        
        (Y) Per-pair ΔRDM:
            RDM_pred = pdist(Y_pred, metric='correlation')
            ΔRDM_pred = RDM_pred - RDM_baseline_h
            Y_h = 1 - cos(ΔRDM_pred, ΔRDM_actual_CVD)
        
        (Z) Per-hue 8AFC accuracy (W-independent):
            δθ_pred = forward_map(params*)
            8AFC_pred = softmax_distance(δθ_pred, σ)
            Z_h = MSE(8AFC_pred, 8AFC_actual_CVD)
        
        Record (X_h, Y_h, Z_h) for fold h

Final reporting:
  - 7-fold (M*, L*) consistency (which model wins how often)
  - 7-fold mean ± SD of (X, Y, Z) — equal weight
  - Cross-correlation matrix (3×3) of (X, Y, Z) — §5.4'
  - Bootstrap CI of params (T-1 Form A, separate from LOO)
```

#### §6.3.2 PI 원문 매핑

| PI quote | 본 scheme 의 답 |
|---|---|
| "엔드투엔드로 모델 선정에서도 LOO" | 각 outer fold 마다 *selection step 재수행* (training pool 만 사용) |
| "그 LOO 한 HC 를 전체에 대해 LOO" | Outer 7-fold |
| "마지막 결과물이 행동 데이터와 유사한지" | Step 2 의 (Z) 8AFC test metric |

#### §6.3.3 Cost estimation

| Step | R+C (121 grid) | 2-Comp (1326 grid) |
|---|---|---|
| Outer × selection on training | 7 × 6 × 121 = 5,082 | 7 × 6 × 1326 = 55,692 |
| Bootstrap CI (T-1 Form A) | B=1000 × 121 = 121K | B=1000 × 1326 = 1.3M |
| **Wall time (node2 ~0.1s/eval)** | ~ **10 min** | ~ **2.5h** |

Nested CV 대비 *5-9x 감소*. Overnight SLURM 불필요.

### §6.4 Train-test by-CVD subtype — CVD overfitting 통제 + 형질 차이 evidence (사용자 lock-in 2026-05-21)

**Rationale (사용자 #8 + advisor catch 통합)**:
- §6.3 의 outer LOO 는 *HC pool* 만 leave-out → CVD overfitting 별도 통제 필요
- §6.4 의 **cross-subtype train-test 가 CVD overfitting 통제 + 형질 (deutan vs protan) 차이 evidence** 의 dual role
- Sub-08 fit 이 sub-09 에 적용 안 되고 reverse 도 안 되면 → **subtype-specific (mechanism distinct)**

```
Round 1: Train sub-08 (deutan, θ_conf=150°) → Test sub-09 (protan, θ_conf=16°)
         - Fit params* on sub-08
         - Apply forward(params*; deutan θ_conf) to sub-09's stimulus → predicted δθ_pred
         - Compare with sub-09's actual δθ_obs (8AFC + LOCO + ΔRDM)
         - High prediction error → subtype mechanism distinct

Round 2: Train sub-09 → Test sub-08 (reverse)

Round 3: Within-subject (per-subject 8-color LOCO)
         - 같은 subject 내 LOCO 가 generalization 보장 (Phase 1 forward model)

Expected (paper claim):
- Cross-subtype error >> Within-subtype error → **mechanism subtype-specific**
- (1) Different θ_conf (protan 16° vs deutan 150°)
- (2) Different Δλ (DPS protan ≈10nm vs deutan ≈6nm)
- (3) Same g 의 cross-subtype 적용 → poor fit prediction

Paper claim (revised): 
  "Each CVD subtype requires a subtype-specific filter; same filter 
   does not generalize across deutan/protan. This is consistent with 
   the well-known confusion-line dichotomy (Stockman & Sharpe)."
```

**한계 명시**: n=1 fit per subtype → cross-subtype generalization 의 *qualitative claim* (effect-size descriptive), *statistical significance claim 아님*.

### §6.5 Sub-09 behavioral data status (정정 2026-05-21)

**Confirmed available** (originally assumed missing, fact-check 후 confirmed):
- JND: `data/behavior/sub-09_jnd_ses1_no_filter_summary.csv` — 8 pair × 2 staircase
- 8AFC: `data/behavior/sub-09_rsvp_8afc_ses1_run1.csv` — 64 trials (100% accuracy, ceiling)

**Sub-09 behavioral signature**:
- 8AFC: 100.00% (ceiling, uninformative for L_behav_α)
- JND: 1 HYPO (green-blue z=+2.36) + 3 HYPER (red-orange, orange-yellow, red-cyan) + 4 ≈HC
- Overall z=−0.16 (within HC pool) — but per-pair signal *exists* (Update L_behav_γ uses all 8 pairs)
- → **Sub-09 = neural distorted but behaviorally compensated** (paper key finding candidate)

**Optional supplementary** (not blocking):
- anomaloscope quotient (severity gold standard) — sub-09 acquisition wait
- Additional behavioral measures (hue scaling) — Phase 3 deferred

**No acquisition blocking for current pipeline** — all data needed for Phase 2 sprint already collected.

### §6.6 Tregillus reduction null 재현 — Form A/B/C (사용자 lock-in 2026-05-21: T-1, T-2, T-3)

PI feedback: "Tregillus 의 sc t-test vs reduction null 을 우리 데이터로 재현". Tregillus 의 *exact form* (contrast variation 필요) 적용 불가능, 단 *검정 구조* 차용 가능. 3 form 모두 채택.

#### §6.6.1 Form A — Per-subject bootstrap CI of g, behavioral fit (T-1, 사용자 lock-in 2026-05-21)

```
H₀ (reduction null): g = 0 (no compensation, retinal cone shift만이 behavior에 발현)
H₁ (compensation): g ≠ 0 (cortical modification of retinal signal)

검정 (behavioral fit, 사용자 통찰 "보상은 R+C 행동 기반 피팅"):
  Δλ external-fixed (DPS literature)
  Bootstrap CVD behavioral data (JND 8-pair + 8AFC 8-color) B=1000
  각 bootstrap 마다 g argmin re-fit on L_behav (subject-specific weights):
    Sub-08: bootstrap (JND 8-pair, 8AFC 8-color) → L_behav (α+γ) → g*
    Sub-09: bootstrap (JND 8-pair only, 8AFC ceiling) → L_behav_γ → g*
  95% CI of g*
  포함 0 → reduction null 기각 못함
  미포함 → g ≠ 0 (compensation 존재)
  
  Plus: |g* · Δλ_DPS| 분포 → compensation magnitude CI

Tregillus 등가:
  Tregillus: sc one-sample t-test against 1 (n=5 AT, behavioral CN reference)
  Ours:      bootstrap CI of g against 0 (per-subject, behavioral L_behav fit)
            ★ 정확히 Tregillus spirit (behavior-anchored compensation parameter)
```

→ **Per-subject statistical test** of cortical compensation existence. Behavioral-primary R+C identity 와 일관.

#### §6.6.2 Form B — HC pool 도 g fit, 분포 비교 (T-2, behavioral fit)

```
For each HC subject h ∈ {sub-01, sub-03, sub-06, sub-07}:  # 8AFC + JND 둘 다 가용
    Fit R+C 1-DOF g with Δλ_HC = 0 (no cone shift assumption for HC)
    on L_behav (HC's own 8AFC + JND):
        L_behav_HC = 0.5·L_α_HC + 0.5·L_γ_HC
    Record g_HC[h]

For HC subjects without 8AFC (sub-02, sub-04, sub-05):
    Fit on L_behav_γ only (JND 8-pair, 가용)
    Record g_HC[h] (caveat: different loss structure than 4-HC primary)

CVD sub-08, sub-09 의 g* vs g_HC 분포:
  - Mahalanobis distance (descriptive percentile)
  - Percentile of CVD g* in HC g distribution
  - Optional: Welch t-test (n=2 vs n=4 or n=7, low power)
```

→ **HC pool 의 *group-level* behavioral baseline**. Tregillus group-level 비교 등가 — behavioral fit 으로 일관.

⚠️ **새 작업**: 현재 HC pool 은 *encoder W 추출* 만 했음. *individual g fit on behavioral data* 은 새 sprint (S5' 추가). 1d 비용.

#### §6.6.3 Form C — Full-grid permutation null (T-3, PI critique D1 직격)

```
Selection-aware null:
  For each of B=1000 label permutations of CVD LOCO ρ 8-vec:
      Run full grid search → g* (or β_s*, β_c*)
      Record min L_neural under permuted labels
  
  Compare real-data argmin L_neural vs null distribution
  P-value = fraction of null below real-data min
```

→ **Selection variance corrected null** — PI critique D1 (grid argmin permutation 가 정확한 null 아님) 의 정밀 답.

#### §6.6.4 Cost + 3 Form integration

| Form | Cost (R+C / 2-Comp) | Paper 위치 |
|---|---|---|
| **A bootstrap CI** | 1d / 1d (S5 일부) | Main results — per-subject g ≠ 0 evidence |
| **B HC pool g fit** | 1d 추가 sprint S5' | Specificity section — HC vs CVD 분포 |
| **C full-grid perm** | 36h SLURM array | Methodological appendix — selection-aware null |

→ **3 Form 다 시행**. Form C 의 36h SLURM 은 *one-time*, overnight.

---

## §7. Sprint plan — 9-step (revised 2026-05-21)

| Step | 작업 | Output | 비용 | Pre-requisite |
|---|---|---|---|---|
| **S1** | `scripts/lambda_3source.py` — DPS / Boehm grid / JND-Lamb (per-subject inverse) | Δλ values for sub-08, sub-09 (3 sources each) | 1d | sub-08 + sub-09 JND data (둘 다 가용) |
| **S2** | `scripts/rc_1dof_fit.py` — R+C 1-DOF g fit × 3 Δλ × 8 loss + R+C inverse check | g* matrix (3 Δλ × 8 loss × 3 subj) | 1.5d | S1 |
| **S3** | `scripts/behav_loss.py` — σ_HC fit (이미 21.0°) + L_α + L_γ (JND per-pair) | L_behav 모듈 (α + γ + composite L5) | 1d | sub-08/09 8AFC + JND data + HC 4-subj 8AFC + HC 7-subj JND data |
| **S4** | `scripts/neural_loss.py` — L_LOCO + L_RDM (corr distance + Crossnobis) + composite L6 | neural loss 모듈 | 1d | 코드 reuse from existing `loco_distortion_fit.py`, `diagnostic_delta_rdm.py` |
| **S5** | All-paths fit (R+C × 24 + 2-Comp × 8 = 32 fits per subject) under all 8 losses | argmin params matrix per subject | 1d | S2, S3, S4 |
| **S5'** | HC pool g fit on L_behav (T-2 Form B) — 7 HC R+C 1-DOF on JND+8AFC | g_HC[h] for h ∈ {sub-01..sub-07} | 1d | S2, S3 |
| **S6** | Single-level outer LOO (7-fold) + Transfer test (X, Y, Z) + Bootstrap CI (T-1 Form A on behavioral) | LOO results, Bootstrap CI of g, compensation magnitude | 1.5d | S5, S5' |
| **S7** | Convergence matrix: 4×2 within-model loss + 3 Δλ-source + 64 cross-model δθ — TOST + BF + Spearman + bootstrap CI | full convergence matrix, paper-ready figs | 1d | S6 |
| **S8** | Per-loss/per-model selection rule (AICc + BIC + 8AFC corr) + Cross-subtype train-test + Form C full-grid permutation (T-3, 36h SLURM) | final filter params per subject per model | 1.5d | S7 |

**Total**: ~10.5d (sub-08 + sub-09 both included, JND/8AFC 둘 다 가용 confirmed 2026-05-21).

**Form C (full-grid permutation)** = one-time SLURM array overnight (36h on node2). Paper appendix.

**Sub-09 acquisition status (정정 2026-05-21)**: RSVP 8AFC + JND 둘 다 가용. 8AFC 가 100% ceiling 이라 L_behav_α 안 쓰지만 JND L_behav_γ informative.

---

## §8. Filter design 의 *Practical* contribution

### §8.1 R+C 의 inverse 검증 (필수, S2 의 일부)

```python
# Forward map differentiable in g
# Inverse: "어떤 stimulus 를 보여주면 sub-08 의 cortical hue 가 정상화되는가?"

For each target_hue ∈ {0, 45, 90, ..., 315}:
    pre_image_stim = inverse_RC(target_hue; Δλ_fix, g_fit)
    # 수치적 해법: scipy.optimize, monotonicity check 필요

# Validation:
#   8/8 exact (within 1°)? → R+C 도 filter form 가능
#   < 8/8 → 2-Comp 가 backup (이미 bijective)
```

만약 R+C inverse 가 안 풀리면 → 2-Comp 가 *유일한 filter form*. Paper-level **filter contribution 의 source** 가 2-Comp 의 *practical 강점* (already 8/8 exact for both subjects).

### §8.2 2-Comp 의 inverse (already validated)

- Sub-08: 8/8 exact (within 0.001°)
- Sub-09: 8/8 exact
- Filter form: `θ_corrected = (θ_stim − δθ_2comp(θ_stim))` mod 360°

---

## §9. PI feedback 직격 mapping

| PI feedback | 본 pipeline 답 |
|---|---|
| **Double-dipping (Δλ + g joint fit = circular)** | §3.1: Δλ literature-fixed (b, c) 또는 JND-anchored (d) → g 만 neural-fit, selection ≠ evaluation 분리. Neural fitting target (LOCO/RDM) 과 Δλ source (literature or JND) 가 *different measurement family*. |
| **"기존 모델이 행동 어떻게 썼는지"** | §3.1: Tregillus 4-step (CN reference / behavioral anchor / 1-DOF fit / t-test against null) 차용 |
| **Systematic 비교 + LOO + train-test** | §6.3 single-level outer LOO + §6.4 train-test by-CVD subtype |
| **Run 수 결정** | future_phase3/run_count_validation_plan_20260519.md (별도) |
| **Fitting 방법 구체화** | §4 + §5 (각 loss 의 수식 + grid search + cross-validation) |
| **행동-only sim + neural ablation** | §6.1: Behav-only vs Neural-only vs Joint |
| **Endtoend LOO** | §6.3: HC 7-fold outer + selection on training pool (color LOCO inner level *제거*, 사용자 lock-in 2026-05-21) |

---

## §10. References (paper-defensible primary set)

`results/model_candidates.md` §7 의 16 references 그대로 inherit.

핵심 1-line summary:

| Citation | Role |
|---|---|
| Boehm 2014 | Multiplicative cortical gain mechanism (primary R+C grounding) |
| Boehm 2021 | "Simple compensation models 부족" — limitation caveat |
| DPS 1992 | Anomalous cone fundamentals (Δλ source) |
| Emery 2022 | Theoretical scaffold for post-receptoral gain (citation upgrade only) |
| Krauskopf 1982 | Cardinal axes (2-Comp position grounding) |
| Lamb 1995 | Cone spectral sensitivity formula |
| Robinson 2022 | CONDITIONAL conceptual analogy for g (mathematical form 다름) |
| Stockman & Sharpe | Confusion axis derivation |
| Tregillus 2021 | V1→V4 hierarchy empirical motivation |
| DKL 1984 | 8-hue ring stimulus design grounding |

---

## §11. Open decisions — all lock-in 2026-05-21

| ID | Decision | Status |
|---|---|---|
| D-Cascade form | "Don't overclaim mechanism but cascade form OK" (a) | ✅ Lock |
| D-Behav-loss form | α primary + β robustness | ✅ Lock |
| D-Δλ source | DPS + Boehm grid + JND-derived (3-source) | ✅ Lock |
| D-Neural loss candidates | L_LOCO + L_RDM (correlation distance primary + Crossnobis robustness) + composite | ✅ Lock (R-1 (a)+(b)) |
| D-LORO | 비활용 | ✅ Lock |
| D-Joint fit | sequential (behav-only + neural-only first, joint conditional) | ✅ Lock |
| D-Model comparison | AICc + BIC (둘 다, n=8 finite-sample) | ✅ Lock |
| D-Equivalence test | TOST + BF₀₁ | ✅ Lock |
| D-Specificity metrics | Tier 1 (B1/B2, E1, P3, C1) | ✅ Lock |
| D-LOO scheme | Single-level outer LOO + selection on training + transfer test (X, Y, Z) + cross-subtype §6.4 | ✅ Lock |
| D-Test metric | (X) LOCO ρ via h + (Y) ΔRDM via h + (Z) 8AFC accuracy, Spearman ρ + bootstrap CI (threshold 제거) | ✅ Lock |
| D-Selection criteria | AICc, BIC, 8AFC corr as separate standard metrics (composite rank 제거) | ✅ Lock |
| D-Equivalence test | TOST + BF₀₁ + n=2 detection power limitation 명시 | ✅ Lock |
| D-Cross-subtype | sub-08↔sub-09 train-test 의 concrete steps (§6.4) — CVD overfitting 통제 + 형질 차이 evidence | ✅ Lock |
| D-Tregillus reduction null | Form A (bootstrap CI, **behavioral fit**) + Form B (HC pool g fit, **behavioral**) + Form C (full-grid perm) | ✅ Lock (R+C identity 일관) |
| D-Δλ source priority | (b) DPS PRIMARY + (c) Boehm robustness + (d) JND-Lamb sensitivity supplement ONLY (dual-role circularity 회피) | ✅ Lock (사용자 통찰) |
| D-Cortical compensation evidence | g* (Δλ_DPS fixed, L_behav fit) — direct metric, ΔΔλ 방법 폐기. \|g*·Δλ\| = magnitude | ✅ Lock (사용자 통찰) |
| D-σ in 8AFC softmax | **σ_HC = 21.0°** (pooled fit on 4 HC, sub-01 degenerate 제외) + sensitivity sweep | ✅ Lock (real fit 완료) |
| D-Loss inventory | **8 candidates** (4 individual L1-L4 + 4 combined L5-L8). **L8 (modality-equal 0.5·behav + 0.5·neural) PRIMARY** | ✅ Lock (사용자 lock-in) |
| D-Subject-specific behav weights | Sub-08: w_α=w_γ=0.5; Sub-09: w_α=0, w_γ=1.0 (8AFC ceiling 정당화) | ✅ Lock (사용자 통찰, 8AFC 100% evidence) |
| D-Model identity | Post-hoc validation, not pre-assigned. 두 모델 모두 8 loss 로 fit → convergence check 에서 preference 드러남 | ✅ Lock (사용자 통찰) |
| D-Convergence matrix | Within-model 28 pairs + Δλ-source 3 pairs (R+C) + Cross-model δθ 64 pairs | ✅ Lock |
| D-Sub-09 data | JND + 8AFC 둘 다 가용 (이전 "미수집" 정정). 8AFC ceiling, JND informative | ✅ Confirmed (fact-check) |
| D-Sub-09 narrative | **Cortical-behavioral dissociation**: Ishihara 9/14 (milder than sub-08 7/14) + behavioral 100%/JND≈HC + V1 LOCO p=0.007 → narrative *격상*. Data integrity (a,b,c,e,f) cleared 2026-05-21 | ✅ Lock (사용자 confirm + Ishihara evidence) |
| D-g sign convention | **g ∈ [0, 3] amplification only** (Boehm, Tregillus sc>1 일관). g<0 은 mechanistically inversion ≠ compensation | ✅ Lock (advisor 정정) |
| D-Compensation magnitude | M = max(0, g*−1)·Δλ_DPS — 1을 baseline (HC passthrough). g=1 → M=0, g=2 → full compensation | ✅ Lock (정정) |
| D-L8 uniform | L8 = 0.5·L_γ + 0.25·L_LOCO + 0.25·L_RDM (both subjects, L1 drop for cross-subject comparability) | ✅ Lock (advisor 정정) |
| D-σ fixed (joint fit 폐기) | **σ=21° fixed** (HC pooled empirical + Schurgin/Maloney literature 18-25° range). Joint fit polynomial identifiability — 폐기. Sensitivity sweep ∈ {15, 18, 21, 24, 28} | ✅ Lock (사용자 정정 — joint fit identifiability) |
| D-Paper framing | §6.3 transfer test = PRIMARY double-dipping defense. §5.4 convergence matrix = supplementary descriptive | ✅ Lock (advisor 정정) |
| D-Wall time | ~6h overnight SLURM (not 45min interactive) | ✅ Lock |
| D-Inverse R+C check | scripts/rc_inverse_check.py (S2 통합) | ⏳ TBD code (S2 일부) |

→ **모든 핵심 design decision lock-in 됨. Sprint S1 (3-source Δλ) 부터 즉시 시작 가능.**
→ 2 가지 TBD (R+C inverse check 코드 form, σ initial value) 는 *implementation detail*, plan-level 영향 없음.
