# LOCO Filter Pipeline — Results Log

## Phase A: Distortion Fitting (v2, 2026-04-08)

### Configuration
- **ROI**: hV4 (K=3, FE basis)
- **Method**: shift_at_both (W retrained at every LOCO fold + every δ)
- **Loss**: L_fit = α·L_vuln/4 + β·L_rank/2 + δ·L_rdm/2 + ε·L_smooth/32400
- **Weights**: α=1.0, β=0.5, δ=0.2, ε=0.1
- **v2 changes**: R+C g extended [-3,3] (was [-3,1]); Fourier L-BFGS-B → DE (3 restarts)

### Results Table

| Subject | Model | Params | ρ | perm_p | Δρ | CCC | L_fit | n_eval | Verdict |
|---------|-------|--------|---|--------|----|----|-------|--------|---------|
| sub-08 (deutan) | machado_1way | Δλ=1.5nm | 0.619 | 0.058 | +0.333 | 0.200 | 0.274 | 41 | Trending |
| **sub-08** | **rc_opponent** | **Δλ=2.0, g=2.25** | **0.857** | **0.005*** | **+0.571** | 0.173 | 0.220 | 1025 | **PRIMARY** |
| sub-08 | fourier_warp | [3.4, 29.7, -11.9, -6.1] | 0.976 | 0.0002** | +0.690 | 0.170 | 0.162 | 4228 | Ceiling |
| **sub-09** (protan) | **machado_1way** | **Δλ=13.5nm** | **0.762** | **0.018*** | **+1.095** | 0.277 | 0.210 | 41 | **PRIMARY** |
| sub-09 | rc_opponent | Δλ=13.5, g=0.0 | 0.762 | 0.018* | +1.095 | 0.277 | 0.210 | 1025 | = Machado |
| sub-09 | fourier_warp | [13.8, 20.0, -18.9, 29.6] | 0.762 | 0.018* | +1.095 | 0.441 | 0.167 | 4378 | No gain |
| **sub-10** (normal) | machado_1way | **Δλ=0.0nm** | -0.048 | 0.559 | +0.428 | -0.147 | 0.333 | 41 | **Specificity PASS** |

### Per-color δθ (degrees, primary models)

| Color | c1(red) | c2(orange) | c3(yellow) | c4(green) | c5(cyan) | c6(blue) | c7(purple) | c8(magenta) |
|-------|---------|------------|------------|-----------|----------|----------|------------|-------------|
| sub-08 R+C | -11.1 | -10.5 | -5.3 | +1.4 | +11.5 | -20.5 | -21.1 | -0.8 |
| sub-09 Machado | -13.1 | -13.7 | -5.6 | +4.6 | +21.1 | +142.7 | -48.5 | +9.5 |
| sub-10 Machado | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

### v1 → v2 Improvements

| Subject | Model | v1 ρ → v2 ρ | v1 p → v2 p | Key change |
|---------|-------|-------------|-------------|------------|
| sub-08 | rc_opponent | 0.762 → **0.857** | 0.018 → **0.005** | g escaped boundary (1.0→2.25) |
| sub-08 | fourier_warp | 0.286 → **0.976** | 0.250 → **0.0002** | DE replaced L-BFGS-B |
| sub-09 | fourier_warp | -0.333 → **0.762** | 0.805 → **0.018** | DE replaced L-BFGS-B |

### Key Interpretations

1. **Sub-08 g=2.25**: Opponent R-G channel amplifies retinal cone shift by 225%. Opposite direction from V1 ΔRDM (g=-2.25 overcompensation). hV4 amplifies deficiency; V1 overcompensates.
2. **Sub-09 g=0.0**: No opponent gain needed. hV4 distortion is purely retinal for protan (Δλ=13.5nm ≈ Machado "moderate protan").
3. **Fourier as ceiling**: Sub-08 ρ=0.976 but 4 DOF on 8 colors → overfitting risk. CCC (0.170) equal to R+C (0.173) → rank-only improvement, not magnitude.
4. **Sub-10 specificity**: Perfect null (Δλ=0, p=0.559).

### Model Selection (per Plan Step 1 decision logic)

- **Sub-08 → R+C (Δλ=2.0, g=2.25)**: 2 DOF, p=0.005, publishable. Fourier = ablation ceiling.
- **Sub-09 → Machado (Δλ=13.5)**: 1 DOF, p=0.018, most parsimonious. R+C collapses to Machado.
- **Sub-10 → No filter**: Specificity confirmed.

### Plan Checklist Validation

- [x] At least one model p<0.05 per CVD subject
- [x] L_fit monotonically decreases with DOF (Fourier < R+C < Machado)
- [x] Specificity: sub-10 Δλ=0
- [x] R+C g no longer at boundary (2.25, interior optimum)
- [x] Fourier DE functional (was FAILED with L-BFGS-B)
- [ ] |δ(c)| ≤ 30° — PASS for R+C (max 21.1°); Fourier exceeds (acceptable as ceiling)
- [ ] CCC low for all models (0.17-0.44) — rank matches but magnitudes differ

---

## Phase B: Pre-Image Filter Search (2026-04-08)

### Approach
Phase B simple inverse (δ_filter = -δ_fit) **FAILED** — sign reversal assumes D(θ-δ) = D(θ)-δ, which is false for nonlinear forward models.

**Pre-image search**: Numerically find CIELab input θ_in such that D(θ_in) = θ_target (normal-vision opponent hue).
- Algorithm: 360° coarse grid + Brent refinement per color
- Targets: normal-vision opponent hue angles D_normal(θ_original) = [313.5, 299.9, 288.3, 278.2, 267.6, 227.4, 86.7, 348.5]°
- **Coordinate-system fix applied**: CIELab hue ≠ opponent hue. Forward model D maps CIELab → Stockman LMS → opponent → arctan2.

### Tier 1: Model-Consistent Residuals (NECESSARY CONDITION)

| Subject | Model | Mean Error | Max Error | Pass (<0.5°) |
|---------|-------|-----------|-----------|---------------|
| **sub-08** | **R+C (Δλ=2.0, g=2.25)** | **0.0002°** | **0.0009°** | **PASS** |
| sub-09 | Machado (Δλ=13.5) | 17.25° | 65.04° | **FAIL** |
| sub-10 | Machado (Δλ=0.0) | 0.0001° | 0.0007° | **PASS (identity)** |

- Sub-08: Perfect convergence for all 8 colors
- Sub-09: c4/c5/c6 all converge to θ_in=127.1° (D degenerate — many-to-one mapping at Δλ=13.5)
- Sub-10: θ_in = θ_original (δ = 0.00° for all 8 colors) — identity confirmed

### Tier 2: Geometric Correction Profile (PRIMARY REPORTABLE)

**Sub-08 R+C (deutan) — per-color pre-image corrections (CIELab δ°):**

| Color | c1(red) | c2(orange) | c3(yellow) | c4(green) | c5(cyan) | c6(blue) | c7(purple) | c8(magenta) |
|-------|---------|------------|------------|-----------|----------|----------|------------|-------------|
| δ_preimage | -18.2 | -37.2 | -34.8 | +18.6 | +42.9 | +3.9 | -31.6 | -1.0 |

- Mean |δ| = 23.5°, Max |δ| = 42.9° (c5 cyan)
- Pattern: R-G axis colors (c1-c3, c7) shift negative (CCW); B-Y axis colors (c4-c5) shift positive (CW)
- Consistent with deutan R+C model: opponent gain g=2.25 amplifies L-M axis distortion

**Fourier approximation (4-DOF):**
- RMSE vs exact: 8.76°
- Fourier-through-model mean error: 17.43° (FAIL for deployment — R+C nonlinearity amplifies Fourier error)
- Exact 8-point lookup table required for this model

**Sub-09 Machado — STRUCTURAL FAIL:**
- Forward model compresses 360° hue circle into ~100° opponent range at Δλ=13.5
- c4(green), c5(cyan), c6(blue) → identical θ_in=127.1° → perceived=282.1° (single hue)
- Unique pre-image does NOT EXIST for c4/c5/c6 → ordinal separation recovery needed (see below)

### Tier 3: Cross-Simulator Sanity (Machado sweep)

| Subject | At fitted Δλ | Error: unfiltered | Error: preimage | Error: simple_inverse |
|---------|-------------|-------------------|-----------------|----------------------|
| sub-08 @ Δλ=2.0 | 4.41° | **11.70°** | 14.88° |
| sub-09 @ Δλ=13.5 | 25.58° | **17.25°** | 43.74° |

- **Sub-08 reversal expected**: pre-image derived from R+C model, cross-sim evaluates via Machado. Different models → cross-sim cannot validate R+C-derived corrections.
- **Sub-09**: pre-image still better than unfiltered at fitted Δλ (17.3° vs 25.6°), but merged colors dominate error.

### Tier 4: L_improve Diagnostic (CIRCULAR — same model for derivation and evaluation)

| Subject | L_improve | Sign | ρ(filtered, actual) | Flag |
|---------|-----------|------|---------------------|------|
| sub-08 | -0.015 | negative | 0.333 | Circular — c6 blue drives negative |
| sub-09 | +0.051 | positive | 0.548 | Circular — merged colors inflate |
| sub-10 | 0.000 | zero | -0.190 | Identity (expected) |

- L_improve is NOT a pass/fail gate. It is an internal consistency check.
- Sub-08 negative L_improve: c6 blue delta_v = -0.202 (largest contributor). Pre-image restores perceived angle but LOCO vulnerability at that angle can differ due to basis function shape.
- **Key insight**: Perceived angle restoration ≠ LOCO vulnerability improvement. C matrix properties (basis function weights at the restored angle) determine LOCO performance, not just the angle itself.

### Comparison Table (3 conditions)

**Sub-08 R+C:**

| Condition | Mean Error (°) | Max Error (°) |
|-----------|---------------|---------------|
| No filter (current CVD) | 12.21 | 32.06 |
| Simple inverse (-δ_fit) | 63.02 | 166.47 |
| **Exact pre-image** | **0.0002** | **0.0009** |

**Sub-09 Machado:**

| Condition | Mean Error (°) | Max Error (°) |
|-----------|---------------|---------------|
| No filter (current CVD) | 25.58 | 81.10 |
| Simple inverse (-δ_fit) | 52.35 | 163.33 |
| Exact pre-image | 17.25 | 65.04 |

### Sub-09 Color Merging Problem & Proposed Solutions

At Machado Δλ=13.5nm, the forward model D maps c4(green→127°), c5(cyan→127°), c6(blue→127°) to the same opponent hue 282°. This is a **structural degeneracy**: the forward model is many-to-one in this hue region.

**Exact pre-image restoration is impossible for c4/c5/c6** — no CIELab inputs exist that would produce three distinct perceived hues for these colors under this level of protan shift.

**Alternative approaches (task-oriented correction, not exact restoration):**

1. **Order-preserving spread (A)**: Maintain healthy ordinal ranking of c4<c5<c6 with minimum angular separation. Not exact hue recovery but ensures ordinal discriminability.

2. **Nearest-neighbor discrimination optimization (B)**: Maximize minimum pairwise separation among merged colors AND their neighbors (c3, c7). Objective: max_θ min_pairs circular_dist(D(θ_i), D(θ_j)).

3. **Healthy prior + minimum distortion (C)**: Use HC spacing as soft target, penalize large CIELab shifts from original. Balances restoration fidelity against physical stimulus plausibility.

**Status**: Implemented and run (see separation results below).

### Sub-09 Separation Optimization Results (2026-04-08)

#### Why Does the Protan Forward Model Compress 360° → ~96°?

The Machado model simulates protan color vision by shifting the L-cone spectral peak toward M-cone:

```
CIELab θ → XYZ → LMS (shifted L-cone) → opponent(rg, by) → arctan2(by, rg)
```

**Normal vision**: L and M cones peak ~30nm apart → `rg = L - M` has wide dynamic range. Combined with `by = S - (L+M)/2`, `arctan2(by, rg)` covers full 360°.

**Protan Δλ=13.5nm**: L-cone peak shifts 13.5nm toward M-cone → L ≈ M → rg ≈ 0.
- **rg channel collapses**: L-M approaches zero for most wavelengths
- **by channel preserved**: S-cone is unaffected, so S-(L+M)/2 still varies
- **Result**: `arctan2(by, rg≈0)` is dominated by by → hue angles cluster near 90° (by>0) or 270° (by<0)
- The residual rg variation creates only ±18° spread around these poles

For our 8 stimuli, most are in the by<0 region → perceived hues concentrate in [282°, 350°], with only c7 (purple, strong S-cone component) reaching ~18°. This gives the ~96° effective bandwidth.

**This is the fundamental mechanism of protan CVD**: colors that differ primarily along L-M (reds, greens, browns) become indistinguishable because the opponent channel encoding them collapses.

#### Forward Model Image Analysis

Note: D's image technically covers nearly 360° (min=0.05°, max=360.0°), but the mapping is **extremely non-uniform**: most of the CIELab circle compresses into a dense ~66° band (282°–348°), with only isolated inputs reaching other regions. The "96° arc" is the effective separation bandwidth within which all 8 perceived hues must fit: [282°, 349°] ∪ [349°, 18°].

**Consequence**: Healthy targets 86.7° (c7 purple) and 227.4° (c6 blue) fall in the sparse region → unreachable with adequate separation. c4 target 278.2° is at the boundary. c5 target 267.6° is also unreachable.

**Merged colors (4)**: c4(green), c5(cyan), c6(blue), c7(purple) — all with exact pre-image residual > 1°.
**Fixed colors (4)**: c1(red), c2(orange), c3(yellow), c8(magenta) — exact pre-image preserved.

**Optimization**: Combined A+B approach — maximize min pairwise separation (w_sep=1.0) + soft healthy target proximity (w_target=0.1) + ordinal constraint (w_order=0.5). Differential evolution, popsize=40, 225 iterations, 4.7s.

**Final perceived hue distribution (8 points in ~96° achievable arc):**

| Color | CIELab input | Perceived | Healthy target | Residual | Type |
|-------|-------------|-----------|----------------|----------|------|
| c7 purple | 101.7° | **282.6°** | 86.7° | 164.1° | sep-opt |
| c3 yellow | 41.0° | **288.3°** | 288.3° | 0.0° | exact |
| c6 blue | 16.8° | **294.1°** | 227.4° | 66.7° | sep-opt |
| c2 orange | 216.0° | **299.9°** | 299.9° | 0.0° | exact |
| c5 cyan | 222.4° | **305.6°** | 267.6° | 38.0° | sep-opt |
| c1 red | 343.1° | **313.5°** | 313.5° | 0.0° | exact |
| c4 green | 232.8° | **319.2°** | 278.2° | 41.1° | sep-opt |
| c8 magenta | 248.1° | **348.5°** | 348.5° | 0.0° | exact |

**Separation metrics:**

| Condition | Min Sep (°) | Mean Sep (°) |
|-----------|------------|-------------|
| Healthy (normal) | 10.18 | 70.65 |
| Unfiltered (current CVD) | 1.03 | 39.30 |
| Exact pre-image (collapsed) | 0.00 | — |
| **Sep-optimized** | **5.76** | **24.28** |

- **Min sep improvement**: 1.03° → 5.76° (**5.6× improvement** over unfiltered)
- **Collapse rescue**: 0.00° → 5.76° (exact preimage had 3 colors at identical angle)
- **Theoretical max**: 8 points in 96° = 12° per slot → achieved 48% of theoretical max
- **Ordinal concordance**: ρ=0.667 (partial — optimized colors interleave with fixed)
- **Bottleneck**: c7(282.6°)–c3(288.3°) gap = 5.76° is the min pair

**Ordinal order comparison:**
- Healthy: c8 > c1 > c2 > c3 > c4 > c5 > c6 > c7
- Optimized: c8 > c4 > c1 > c5 > c2 > c6 > c3 > c7
- Merged colors interleave with fixed colors (necessary to spread across available range)

**Interpretation**: The ~96° achievable range is a hard physical constraint of the Machado protan model at Δλ=13.5nm. Within this constraint, the separation optimization distributes 8 perceived hues as evenly as possible. The result is not hue restoration but **discriminability recovery** — each color is at least 5.76° separated from its nearest neighbor, compared to 1.03° unfiltered.

### Fundamental Limit: Stimulus-Space Filter vs Spectral Filter

#### Why stimulus-space remapping cannot exceed the ~96° arc

Our filter operates **after** the retinal information bottleneck:

```
Stimulus-space filter (our approach):
  Change CIELab input → SAME retinal processing (L≈M) → SAME opponent compression
  → Can only redistribute within the compressed ~96° arc

Spectral notch filter (EnChroma-like):
  Block overlapping L/M wavelengths → INCREASE L-M separation → EXPAND opponent range
  → Partially decompresses the arc itself
```

The 96° arc is set by the opponent channel: at Δλ=13.5nm, L-cone peak shifts toward M-cone → rg = L-M ≈ 0 → arctan2(by, rg) is dominated by the by channel. No stimulus rearrangement can change how the retina encodes the signal.

#### Could uniform 12° spacing help LOCO?

Even if all 8 colors are freed (not fixing 4 exact preimages) to achieve the theoretical maximum 12° uniform spacing within 96°, the **LOCO decoder remains limited**:

- FE basis (6 channels, peaks at 0°/60°/120°/180°/240°/300°): 8 perceived hues in [282°, 18°] activate only 3-4 of 6 channels (120° and 180° channels contribute zero)
- Adjacent color C-vector difference: Δ ≈ 0.08–0.21 (normal vision: Δ ≈ 0.5–1.0)
- Correlation template matching cannot reliably distinguish 12° differences with reduced channel coverage
- **Conclusion**: uniform spacing is achievable but insufficient for LOCO improvement at this severity

#### Advantages over commercial CVD filters

| | Commercial (EnChroma-like) | Our approach |
|---|---|---|
| **Mechanism** | Optical: spectral notch removes L-M overlap wavelengths (pre-retinal) | Computational: CIELab angle remapping via forward model inversion (stimulus-space) |
| **Personalization** | None (generic filter for all users) | **Individual-specific** (fMRI-fitted Δλ + g per subject) |
| **Cortical component** | Ignored entirely | **Captured**: sub-08 g=2.25 = V4 amplifies retinal deficiency 2.25× → spectral filter correcting only Δλ=2.0 would under-correct |
| **Correction guarantee** | Approximate, mixed evidence | **Exact** under fitted model (<0.001° residual for sub-08) |
| **Implementable on** | Physical glasses only | **Any digital display** (monitor, phone, AR/VR) — 8-point lookup table |
| **Severity awareness** | Same product regardless of severity | **Quantifies correction limit** per individual: identifies when stimulus-space is sufficient vs spectral intervention needed |
| **Discrimination at threshold** | Not improved (Somers 2024) | Not yet tested (behavioral validation = future work) |
| **Limitations** | Luminance loss; dichromats excluded; no cortical model | Requires fMRI to fit; controlled stimuli only (not natural scenes) |

**Key advantage 1 — Cortical compensation capture:**
Sub-08's g=2.25 reveals V4 amplifies the retinal deficiency (not just passively reflects it). A spectral filter designed for retinal Δλ=2.0nm alone would under-correct because it does not account for the 2.25× cortical gain. Our model corrects the full neural distortion chain: retinal(Δλ) + cortical(g).

**Key advantage 2 — Digital display implementability:**
The 8-point CIELab lookup table is directly implementable as software color remapping on any digital display. No physical optics needed. Particularly suited for AR/VR environments where stimulus control is native.

**Key advantage 3 — Prescriptive severity threshold:**
Our framework identifies EXACTLY when stimulus-space correction is feasible (sub-08, mild) vs impossible (sub-09, moderate), providing a quantitative criterion for choosing between software (stimulus remapping) and hardware (spectral filter) interventions. Commercial filters cannot provide this per-individual assessment.

#### Commercial CVD filter evidence

| Study | Filter | Finding |
|-------|--------|---------|
| Somers et al. (2024) [Vision Res.](https://pubmed.ncbi.nlm.nih.gov/38531192/) | EnChroma multi-notch | Color matching improved (gamut expansion); appearance enhanced along R-G axis; **discrimination at threshold NOT improved** |
| Almutairi et al. (2024) [JPMS](https://jpmsonline.com/article/jpms-volume-13-issue-2-pages129-136-ra/) | EnChroma | Limited effectiveness; no discernible impact on most CVD subjects' performance |

Key insight from spectral filter literature: notch filters can change **which colors appear distinct** (suprathreshold appearance) but cannot improve **how finely colors are discriminated** (threshold sensitivity). The underlying cone pigment sensitivity is the hard limit — same principle as our 96° arc.

#### Severity-dependent dissociation (key finding)

| | Sub-08 (deutan, Δλ=2.0) | Sub-09 (protan, Δλ=13.5) |
|---|---|---|
| Forward model compression | ~260° arc (mild) | ~96° arc (severe) |
| Pre-image exact restoration | 8/8 colors | 4/8 colors |
| Filter restores 360° coverage? | **Yes** | **No** |
| LOCO improvement possible? | Yes (all 6 basis channels active) | No (only 3-4 channels active) |
| Intervention needed | Stimulus-space sufficient | Spectral-domain required |

**Manuscript framing**: Unlike spectral notch filters that operate generically at the retinal level, our neural-data-driven approach captures both retinal (Δλ) and cortical (g) components of color distortion, enabling subject-specific correction that accounts for compensatory cortical processing not addressed by optical interventions. Stimulus-space remapping achieves exact hue restoration for mild anomalous trichromacy (sub-08, Δλ=2.0nm) but reaches a fundamental physical limit for moderate protanomaly (sub-09, Δλ=13.5nm). The forward model quantifies this limit: at Δλ=13.5nm, opponent channel compression restricts achievable perceived hues to ~96°, rendering full chromatic restoration impossible through stimulus manipulation alone. This severity-dependent threshold provides a quantitative benchmark for when spectral-domain interventions become necessary.

### Verdict Summary

| Subject | Pre-image | Separation | Stimulus-space filter | Next step |
|---------|-----------|------------|----------------------|-----------|
| **sub-08** | **PASS** (0.0002°) | — | **Sufficient** (full 360° restoration) | Use exact 8-point lookup |
| sub-09 | FAIL (merging) | PASS (5.76° min sep) | **Insufficient** (96° arc limit) | Theoretical limit reached |
| sub-10 | PASS (identity) | — | N/A | No filter needed |

---

### Per-Color Summary Table (All Subjects)

Four conditions for each color: Original stimulus (CIELab°), CVD perceived without filter (opponent°), Modified stimulus after filter (CIELab°), Expected CVD perception with filter (opponent°). HC target (opponent°) shown for reference.

**Sub-08 (Deutan, R+C pre-image — exact restoration):**

| Color | Original | Perceived | Modified | Expected | HC Target | Match? |
|-------|----------|-----------|----------|----------|-----------|--------|
| c1 red | 0.0 | 303.0 | 341.8 | 313.5 | 313.5 | exact |
| c2 orange | 45.0 | 290.2 | 7.8 | 299.9 | 299.9 | exact |
| c3 yellow | 90.0 | 283.3 | 55.2 | 288.3 | 288.3 | exact |
| c4 green | 135.0 | 279.1 | 153.6 | 278.2 | 278.2 | exact |
| c5 cyan | 180.0 | 277.6 | 222.9 | 267.6 | 267.6 | exact |
| c6 blue | 225.0 | 259.5 | 228.9 | 227.4 | 227.4 | exact |
| c7 purple | 270.0 | 59.2 | 238.4 | 86.7 | 86.7 | exact |
| c8 magenta | 315.0 | 346.5 | 314.0 | 348.5 | 348.5 | exact |

**Sub-09 (Protan, Machado separation-optimized — discriminability recovery):**

| Color | Original | Perceived | Modified | Expected | HC Target | Match? |
|-------|----------|-----------|----------|----------|-----------|--------|
| c1 red | 0.0 | 301.1 | 343.1 | 313.5 | 313.5 | exact |
| c2 orange | 45.0 | 287.7 | 216.0 | 299.9 | 299.9 | exact |
| c3 yellow | 90.0 | 283.1 | 41.0 | 288.3 | 288.3 | exact |
| c4 green | 135.0 | 282.1 | 232.8 | 319.2 | 278.2 | sep-opt (+41°) |
| c5 cyan | 180.0 | 285.6 | 222.4 | 305.6 | 267.6 | sep-opt (+38°) |
| c6 blue | 225.0 | 308.5 | 16.8 | 294.1 | 227.4 | sep-opt (+67°) |
| c7 purple | 270.0 | 18.3 | 101.7 | 282.6 | 86.7 | sep-opt (+196°) |
| c8 magenta | 315.0 | 352.1 | 248.1 | 348.5 | 348.5 | exact |

**Sub-10 (Normal, identity — no filter needed):**

| Color | Original | Perceived | Modified | Expected | HC Target | Match? |
|-------|----------|-----------|----------|----------|-----------|--------|
| c1 red | 0.0 | 313.5 | 0.0 | 313.5 | 313.5 | identity |
| c2 orange | 45.0 | 299.9 | 45.0 | 299.9 | 299.9 | identity |
| c3 yellow | 90.0 | 288.3 | 90.0 | 288.3 | 288.3 | identity |
| c4 green | 135.0 | 278.2 | 135.0 | 278.2 | 278.2 | identity |
| c5 cyan | 180.0 | 267.6 | 180.0 | 267.6 | 267.6 | identity |
| c6 blue | 225.0 | 227.4 | 225.0 | 227.4 | 227.4 | identity |
| c7 purple | 270.0 | 86.7 | 270.0 | 86.7 | 86.7 | identity |
| c8 magenta | 315.0 | 348.5 | 315.0 | 348.5 | 348.5 | identity |

**Reading guide:**
- *Original*: CIELab angle of physical stimulus shown in experiment
- *Perceived*: Opponent hue angle as perceived by CVD (forward model at original)
- *Modified*: CIELab angle of filtered stimulus (preimage/separation input)
- *Expected*: Opponent hue angle as CVD would perceive the modified stimulus
- *HC Target*: Opponent hue angle under normal healthy vision (goal)
- For sub-08: all 8 Expected ≈ HC Target (exact restoration)
- For sub-09: 4/8 exact + 4/8 separation-optimized (c4-c7 shifted from HC target but mutually distinguishable)
- For sub-10: Modified ≈ Original, Expected ≈ Perceived (identity, no correction needed)

---

## Phase A Training: Data Flow & Metrics

### Loss Function

```
L_fit = 1.0·L_vuln/4 + 0.5·L_rank/2 + 0.2·L_rdm/2 + 0.1·L_smooth/32400
```

All loss terms are normalized to [0,1] so weights are directly interpretable.

### L_vuln (MSE, weight=1.0) — Primary fitting metric

- **Definition**: `MSE(vuln_sim, vuln_cvd)` — per-color LOCO vulnerability profile match
- **vuln_cvd (fitting target)**: Pre-computed from Phase 1 forward model validation
  - Source: `future_phase1_forward_model/results/validation/sub-{XX}_loco.json`
  - Computation: CVD subject's `amplitudes_procrustes.npy` (6 runs × 8 colors × V voxels) → ridge_gcv 8-fold LOCO → per-color `voxel_corr` (r values)
  - This is already computed; Phase A simply loads it
- **vuln_sim (simulated)**: HC 7명의 amplitudes에서 shifted LOCO 시뮬레이션
  - Input: HC `amplitudes_procrustes.npy` from C010 dataset
  - Method (shift_at_both): For each candidate δθ:
    1. Model (Machado or R+C) generates `C_shifted` = shifted 8×K design matrix
    2. Per HC: LOCO with C_shifted (W retrained at every fold — 42 train samples per fold)
    3. Per HC per color: `voxel_corr = corr(C_shifted[held_out] @ W, actual_pattern)`
    4. Average across 7 HC → `vuln_sim(δθ)` (8,)
- **Meaning**: "HC에게 δθ만큼 warped된 자극을 주면, CVD의 실제 LOCO 패턴과 얼마나 비슷한가?"

### L_rank (1−ρ, weight=0.5) — Profile shape match

- **Definition**: `1 - Spearman_ρ(vuln_sim, vuln_cvd)`
- Same vuln_sim / vuln_cvd, but rank correlation → absolute bias 무시, 프로파일 형태만 평가

### L_rdm (1−cosine, weight=0.2) — RDM structure match

- **ΔRDM_obs**: `RDM_CVD - mean(RDM_HC)` (28 pairwise distances, 8C2)
  - RDM = correlation distance matrix of run-averaged voxel patterns
  - Computed from actual amplitudes_procrustes.npy
- **ΔRDM_sim**: `RDM(C_shifted @ W) - RDM(C_baseline @ W)`, averaged over 7 HC
  - W is precomputed (W-fixed), only C changes
  - Always uses correlation distance for consistency
- **Loss**: `1 - cosine(ΔRDM_sim, ΔRDM_obs)`

### L_smooth (weight=0.1) — Regularization

- **Definition**: `mean(diff(delta_theta)²) / 32400`
- Adjacent-color shift 차이의 제곱 → smooth distortion field 유도
- 32400 = 180² (최대 가능 인접 차이)

### Data Flow Summary

```
C010 amplitudes (server)
├── HC 7명 × ROI → amplitudes_procrustes.npy (6, 8, V)
│   ├── precompute W_HC (ridge_gcv, pooled 48 samples)
│   ├── vuln_sim: per-color LOCO at C_shifted (shift_at_both)
│   └── ΔRDM_sim: RDM(C_shifted@W) - RDM(C_baseline@W)
│
└── CVD 3명 → Phase 1 validation
    ├── vuln_cvd: sub-{XX}_loco.json (per-color voxel_corr)
    └── ΔRDM_obs: RDM_CVD - mean(RDM_HC)

Model parameter sweep:
├── machado_1way: Δλ ∈ [0, 20] nm, step=0.5 → 41 grid points
├── rc_opponent: (Δλ, g) → 41×25 = 1025 grid points
└── fourier_warp: 4-DOF → DE optimizer (~4000 evals)

Each evaluation:
  C_shifted = model(params) → vuln_sim, ΔRDM_sim → L_fit
```

**핵심**: vuln_cvd는 이미 계산된 값을 로드, vuln_sim은 매 파라미터마다 HC 데이터로 새로 시뮬레이션. 둘의 profile match를 최대화하는 파라미터가 Phase A output.

---

## Biological Plausibility Assessment

### Overview: Which Parameters Match Literature?

| Parameter | Our value | Literature value | Source | Agreement |
|-----------|-----------|-----------------|--------|-----------|
| Sub-08 Δλ (deutan, hV4) | **2.0 nm** | 1-4 nm = very mild | Machado 2009 | in range |
| Sub-09 Δλ (protan, hV4) | **13.5 nm** | 9-14 nm = moderate-severe | Machado 2009 | in range |
| Sub-10 Δλ (normal) | **0.0 nm** | 0 nm = normal | Machado 2009 | exact |
| β_s (S-cone expansion) | **20-23°** | **21.4°** B-Y rotation | Emery et al. 2021 | within 1-3° |
| Sub-09 g (V1, R+C) | **-1.10** (10% overcomp) | 20-40% overcomp range | Tregillus et al. 2021 | below range |
| Sub-08 g (hV4, R+C) | **+2.25** (amplification) | No direct precedent | — | novel / problematic |
| Sub-08 g (V1, R+C) | **-2.25** (125% overcomp) | 20-40% overcomp range | Tregillus et al. 2021 | far exceeds |

### 1. Cone Shift Δλ — WELL SUPPORTED

**Machado et al. (2009)** defines the spectral shift domain as [0, 20] nm:
- 0 nm = normal trichromatic vision
- ~2 nm = very mild anomaly
- ~5 nm = mild anomaly
- ~10 nm = moderate
- ~14 nm = moderate-severe
- 20 nm = dichromat equivalent (protanope/deuteranope)

**Our values**:
- Sub-08 Δλ=2.0 nm → "very mild deutan" — consistent with the subject being an anomalous trichromat who passed most clinical screening tests
- Sub-09 Δλ=13.5 nm → severity ≈ 0.675 → "moderate-severe protan" — consistent with noticeable color confusion
- Sub-10 Δλ=0.0 nm → correct null

**Neitz & Neitz (2011)**: Normal L-M cone separation is ~27-30 nm. Anomalous trichromats have 1-12 nm separation remaining. Our Δλ values represent the shift FROM normal, so:
- Sub-08: 30 - 2 = ~28 nm remaining separation (near-normal — mild)
- Sub-09: 30 - 13.5 = ~16.5 nm remaining separation (moderate, consistent with clinical protanomaly)

### 2. S-Cone Expansion β_s — STRONG MATCH

**Emery et al. (2021)**: Measured B-Y phase shift of anomalous trichromats using hue-scaling task:
- AT B-Y absolute phase: **106.1°**, NT B-Y phase: **127.5°**
- Difference = **21.4° rotation** toward the S-vs-LM axis

**Our 2-Component model** (from V1 ΔRDM crossnobis):
- Sub-08 β_s = **20.0° ± 8.0°**, CI₉₅ = [12°, 39°]
- Sub-09 β_s = **23.0° ± 10.2°**, CI₉₅ = [2°, 36°]
- Cross-subject mean: **~21.5°** — within **0.1°** of Emery's 21.4°

This is the strongest literature match: two completely independent methods (behavioral hue-scaling vs fMRI ΔRDM fitting) converge on nearly identical S-cone expansion values. Both CIs exclude 0 and overlap substantially, suggesting a shared compensatory mechanism across deutan and protan subjects.

### 3. Cortical Gain g — MIXED / PROBLEMATIC

Our R+C model uses: `rg' = rg_ret + g × (rg_ret - rg_base)`
- g = 0: pure retinal (no cortical effect)
- g = -1: exact compensation (rg' = rg_base)
- g < -1: overcompensation
- g > 0: amplification (hV4 makes distortion WORSE)
- |1+g| = effective gain factor on retinal change

**Literature gain values** (defined differently — total scaling needed to equate AT responses to NT):

| Source | Measure | Value |
|--------|---------|-------|
| Tregillus et al. 2021 | V2v scaling factor | **6.39 ± 5.21** (p=0.01) |
| Tregillus et al. 2021 | V3v scaling factor | **7.82 ± 5.76** (p=0.03) |
| Tregillus et al. 2021 | V1 scaling factor | 2.94 ± 2.81 (NS) |
| Boehm et al. 2014 | Protan implied gain | **~3.53×** |
| Boehm et al. 2014 | Deutan implied gain | **~2.26×** |
| Emery et al. 2021 | Suprathreshold gain | **~4.1×** |

**Direct comparison is problematic** because:
1. **Different gain definitions**: Tregillus/Boehm measure total response scaling; our g measures only the cortical amplification of the retinal-induced R-G change
2. **Different ROIs**: Tregillus reports V2v/V3v; our Phase A fits hV4; our COMPREHENSIVE_MODEL_RESULTS fit V1
3. **Sign depends on ROI**: Sub-08 V1 g=-2.25 (overcompensation) vs hV4 g=+2.25 (amplification) — opposite directions

**What IS comparable**:
- Sub-09 V1 g=-1.10 → |1+g|=0.10 → 90% compensation + 10% overcompensation. Tregillus found V1 deficit + V2v/V3v full compensation. 10% overcompensation at V1 is plausible (slightly below their estimated 20-40% range).
- Sub-08 hV4 g=+2.25 → |1+g|=3.25 → hV4 amplifies retinal distortion by 3.25×. This is a novel finding without direct literature precedent. Boehm deutan gain (~2.26×) is in a similar magnitude range but measures something different.

**Sub-08 V1 g=-2.25** (125% overcompensation): Exceeds Tregillus range (20-40%). Likely reflects overfitting with extreme gain compensating for small Δλ=2.5nm. Flagged as non-physiological.

### 4. Summary: What Is and Isn't Validated

**Well-validated by literature**:
- Δλ values: within Machado [0, 20] nm, consistent with clinical severity
- β_s (S-cone expansion): 20-23° ≈ Emery's 21.4° (remarkable match)
- Sub-10 null: correct rejection

**Partially supported**:
- Sub-09 V1 g=-1.10: plausible direction, slightly below Tregillus range
- Cone shift as primary retinal mechanism: consistent with all CVD literature

**Not validated / problematic**:
- Sub-08 hV4 g=+2.25: novel finding, no direct precedent (amplification, not compensation)
- Sub-08 V1 g=-2.25: exceeds literature range, likely overfitting
- The g parameter comparison to literature is indirect (different gain definitions)

### References

1. **Machado et al. (2009)**. "A Physiologically-based Model for Simulation of Color Vision Deficiency." *IEEE TVCG*, 15(6), 1291-1298. — Δλ range [0, 20] nm
2. **Tregillus et al. (2021)**. "Color Compensation in Anomalous Trichromats Assessed with fMRI." *Current Biology*, 31(5), 936-942. — V2v 6.39×, V3v 7.82× scaling
3. **Emery et al. (2021)**. "Color perception and compensation in color deficiencies assessed with hue scaling." *Vision Research*, 183, 1-12. — 21.4° B-Y rotation
4. **Boehm et al. (2014)**. "Compensation for red-green contrast loss in anomalous trichromats." *J. Vision*, 14(13), 19. — Protan ~3.53×, deutan ~2.26× gain
5. **Neitz & Neitz (2011)**. "The genetics of normal and defective color vision." *Vision Research*, 51(7), 633-651. — Normal L-M separation ~27-30 nm
6. **Emery et al. (2022)**. "Gaining the system: limits to compensating color deficiencies through post-receptoral gain changes." *JOSA A*, 39, 2172-2181. — Partial recovery + achromatic increase

---

## Figures (Phase B)

All in `results/loco_filter/preimage/figures/`:
- `angle_comparison_sub-{08,09,10}_*.png` — per-color θ_target vs θ_in* vs D(θ_in*)
- `color_wheel_sub-{08,09}_*.png` — inner=original, middle=pre-image, outer=perceived
- `fourier_approximation_sub-{08,09,10}_*.png` — exact δ vs Fourier curve
- `cross_sim_sanity.png` — Δλ sweep for sub-08 (R+C vs Machado) and sub-09
- `four_ring_color_wheel_all_subjects.png` — 4-ring wheel (original→perceived→modified→expected) for all 3 subjects
- `four_condition_angle_comparison.png` — bar chart comparing 4 conditions per color with HC targets
- `sub09_forward_model_compression.png` — scatter plot showing D compression (360° CIELab → ~96° opponent)

### Figure interpretation note: sub-08 color wheel appears "overlapping"

The sub-08 color wheel and 4-ring wheel show dots that appear clustered. This is NOT a bug — it reflects two real phenomena:

1. **CIELab ≠ opponent hue spacing**: The 8 CIELab stimuli at uniform 45° intervals map to **non-uniform** opponent hue angles. c1–c5 (red→cyan) span only 46° in opponent space (avg 11.5° per pair), while c6→c7 spans 141°. This is normal — opponent coding is not a linear transform of CIELab.

2. **Inner/outer ring overlap = filter success**: In the 3-ring wheel, inner=healthy target and outer=D(θ_in*). Since residuals are <0.001°, outer dots sit ON TOP of inner dots. This overlap is the desired outcome — the filter perfectly restores target positions.

The `angle_comparison_sub-08_rc_opponent.png` bar chart is the clearest visualization for sub-08: blue bars (target) and green bars (perceived) match exactly, with orange bars (preimage CIELab input) showing the required stimulus modifications.
