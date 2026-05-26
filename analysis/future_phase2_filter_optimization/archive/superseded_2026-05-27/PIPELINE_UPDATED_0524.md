# Pipeline (Consolidated 2026-05-26) — Model & Loss Selection

CVD individualized inverse filter — Phase 2 (model fit) → Phase 3 (behavioral validation).

**Status snapshot (2026-05-26)**: Phase A complete · Phase B v3/v4/v5 complete (v6 PCA-RDM pending) · Phase C v2 complete · Phase D pending sub-08/sub-09 final selection · Phase 3 trigger condition #4 fails for sub-09 JND_Lamb variant.

**Sections**
- §S0 Executive summary (4-axis verdict + final candidate set)
- §S1 Model candidates (R+C / 2-Component)
- §S2 Loss candidates (L_α / L_γ / L_LOCO / L_RDM)
- §S3 Phase A — Precondition (S10a, complete)
- §S4 Phase B — Inclusion screening (v3 → v4 → v5; v6 pending)
- §S5 Phase C — Weight sweep + multi-point validation sim
- §S6 Phase D — Final selection + Phase 3 trigger
- §S7 Future TODO — v3 sim (empirical low-rank covariance)
- §S8 Cycle 1–5 diagnostic findings (behavioral-fit re-examination)
- Appendices: assumptions, limitations, files, enumeration history

Prior detailed history → `BEHAVIORAL_FIT_DIAGNOSIS_2026-05-26.md`, `PIPELINE_RESULT.md` (archive). Project-level rules → `CLAUDE.md`.

---

## §S0. Executive Summary

### Status (2026-05-26): Pipeline 3 OOS Re-Analysis in progress — final candidates PENDING

§0 framework explicit override accepted by user 2026-05-26. New 3-layer selector active. Selection NOT locked. See `BEHAVIORAL_FIT_DIAGNOSIS_2026-05-26.md` and `DECISION_CRITERIA_2026-05-26.md` for full spec.

| Layer | Status |
|---|---|
| A — P1 (fit/eval atom separation) + P2 (HC-subset robustness, lexicographic median ASC/IQR ASC; LOCO IQR ignored) | Complete; sub-08 142/284 P2-pass; sub-09 22/44 P2-pass |
| B — E1 (behavioral pair-OOS) | Complete (Cycle 10b); cross-cell fairness flag open (advisor) |
| B — E2 (SRM disparity reduction) | Script ready; direction (forward vs inverse) pending user confirmation |
| B — E3 (multi-point sim recovery) | Round 1+2 historical; Round 3 needed at new candidates |
| C — §0 LOCO-best | Demoted to complementary metric only (user override) |
| Convergence threshold | Deferred until E1+E2+E3 land |

### Working candidate list under E1+P2 (subject to E2+E3 revision)

| Subject | E1 rank-1 candidate | E1 score | Notes |
|---|---|---|---|
| sub-08 | 2-comp (β_s=14, β_c=−46) via γOY,YG,YP triple γ | 14.36 | held-out 5 pairs only (fairness flag); per-pair mean 2.87 |
| sub-08 alt | 2-comp (β_s=50, β_c=−36) via γOY,YG,YP V1+V4 | 19.62 | held-out 5 pairs |
| sub-09 | R+C g=3.00, Δλ=3 nm (Boehm_low) via γGB | 6.83 | over-comp branch (Cycle 6 verdict restored) |
| sub-09 alt | 2-comp (β_s=2, β_c=24) via γGB | 7.77 | tightest IQR=1.41 |

### Sub-08 R+C representational limitation (Pipeline 2 diagnostic)

Confirmed structural finding (kept across all selection criteria): Machado shape constrained to red-green axis cannot represent sub-08's yellow-region deficit (OY z²=16, YG z²=17 under R+C vs 4.6/0.3 under 2-comp). This is a paper-level constructive finding regardless of which OOS criterion ultimately wins.

---

## §S1. Model Candidates

Two mechanistic models compared. Single-mechanism-per-subject (§A11). Encoder fixed = ridge_gcv (§A10).

### §S1.1 R+C 1-DOF — Retinal cone shift + Cortical gain

**Mechanism**: retinal cone-peak shift Δλ generates Machado distortion; cortex applies linear gain g (Boehm 2014 compensation form).

**Forward**:
```
δθ_RC(θ; Δλ, g) = (2 − g) · δθ_Machado(θ; Δλ)
```

| g | Interpretation |
|---|---|
| 0 | Cortical attenuation (2× retinal distortion) |
| 1 | No compensation (retinal passthrough = raw Machado) |
| 2 | Full compensation (behavior = HC) |
| 3 | Overcompensation (inverted retinal direction) |

**Grid**: g ∈ [0, 3] step 0.05 (61 points). σ = 21° fixed (HC pooled 8AFC fit, 255 trials, sub-01/03/06/07).

**Δλ source candidates (3, per subject)** — entered as sensitivity sweep (§S9.A4):

| Source | sub-08 deutan | sub-09 protan | Rationale |
|---|---|---|---|
| **DPS_lit** | 6.0 nm | 10.0 nm | DeMarco 1992 population mean |
| **Boehm_low / mid** | 8.0 nm (mid) | 3.0 nm (low) | Boehm 2014 severity grid; subject-fit at S1 |
| **JND_Lamb** | 6.5 nm | 1.5 nm | Inverse fit from each subject's JND (Lamb 1999 cone-shift→JND mapping) |

**Forward magnitudes at g=1 (raw Machado)**:

| Subject | Δλ source | RMS δθ | max\|δθ\| |
|---|---|---|---|
| sub-08 | DPS 6.0 / JND 6.5 / Boehm 8.0 | 32 / 36 / 43° | 86 / 97 / 118° |
| sub-09 | DPS 10 / Boehm 3 / **JND 1.5** | 35 / 17 / **9°** | 76 / 41 / **22°** |

**g terminology (UPDATED 2026-05-25 per advisor #5)**:
- **g = 2 = operational null** (δθ_RC = 0; CVD perception = HC). Study H0 + simulation null GT.
- **g = 1 = Machado retinal baseline** (raw Machado, no cortical modulation). NOT called "null".
- **Paper claim**: `g* ≠ 2` (incomplete OR over-compensation) — the meaningful finding.

**Theoretical limits**:
- Mechanistically grounded (Boehm 2014 linear compensation form)
- 1-DOF → AIC/BIC parsimony advantage over 2-Comp
- Boundary risk at g=0 or g=3 when Δλ prior magnitude mismatches subject signal
- *Shape fixed by Machado(Δλ)*; cannot represent hue-dependent deficit direction independent of Machado red-green axis (see §S8.C1 — sub-08 yellow-region fail)

**Self-test**: 7/7 PASS (`scripts/rc_1dof.py`)

### §S1.2 2-Component — Cortical opponent rotation (S-cone + confusion axis)

**Mechanism**: cortical opponent gain operates in CIELab opponent space along two physiologically grounded axes (Krauskopf 1982 S-cone cardinal + Stockman confusion line).

**Forward**:
```
δθ_2C(θ; β_s, β_c) = β_s · cos(θ − 90°) + β_c · cos(θ − θ_conf)
θ_conf = 16°  (protan); 150° (deutan)
```

| Parameter | Axis | Interpretation |
|---|---|---|
| β_s | S-cone cardinal (90°) | Yellow ↔ blue axis amplitude (Emery 2021 grounding) |
| β_c | Confusion axis | Subtype-specific (Stockman confusion line per family) |

**Grid**: β_s ∈ [0, 50°] step 2° (26 pts), β_c ∈ [−50°, +50°] step 2° (51 pts) → 1326 combinations.

**Theoretical limits**:
- 2-DOF separates magnitude (β_s) from direction (β_c); supports yellow-region deficits R+C cannot fit
- Operates in CIELab opponent space, matching V4 geometry literature (Conway 2007; Bannert & Bartels 2018)
- 2 DOF requires parsimony penalty for fair AIC/BIC vs R+C 1-DOF
- **Non-identifiable under N=7 HC pool** per multi-point sim Round 1 (§S5.5.2) — both null and fit-point grid attraction observed

**Self-test**: pre-image 8/8 EXACT for both subjects (`scripts/two_comp.py`)

### §S1.3 Theoretical contrast

| Property | R+C 1-DOF | 2-Component 2-DOF |
|---|---|---|
| Mechanism level | Retinal cone shift × cortical gain | Cortical opponent rotation |
| Free parameters | g ∈ [0, 3] (given Δλ prior) | (β_s, β_c) ∈ [0,50] × [−50,+50] |
| Distortion shape | Fixed by Machado(Δλ) | Linear combination of two cosines |
| Subtype info | Δλ prior carries family | θ_conf carries family |
| AIC/BIC reference | k=1 | k=2 |

Models are **mechanistically distinct, not nested**.

---

## §S2. Loss Candidates

Four loss functions. Subject-specific composite weighting determined empirically in Phase B-C.

### §S2.1 L_α — 8AFC softmax categorical mismatch

8-way forced-choice response probability against observed accuracy per color. σ_HC = 21° fixed. Used when CVD shows < 99% accuracy (sub-08 only — sub-09 ceiling at ~100%).

```
P(response = j | stim = i; σ, δθ) ∝ exp(−|hue_i + δθ(i) − hue_j|² / σ²)
L_α = (1/8) · Σ_i ( P(correct | i) − obs_acc[i] )²
```

### §S2.2 L_γ — per-pair JND z-scored MSE

Per-pair JND compared to HC baseline. Aggregate dilutes single-pair atomic distortion → **per-pair decomposition** is the load-bearing variant for sub-09.

```
JND_pred(p) = JND_HC_mean(p) × (d_physical(p) / d_perceived(p; δθ))
L_γ(p)      = ((JND_pred(p) − JND_obs(p)) / σ_p)²
L_γ_mean    = (1/N_pairs) · Σ_p L_γ(p)
```

8 pairs measured: red-orange, orange-yellow, yellow-green, green-blue, blue-purple, yellow-purple, cyan-magenta, red-cyan.

**γ_all variant (Cycle 3, §S8.C3)**: sum z² over all 8 valid pairs (not z-score-normalized mean). Tested in v5 enumeration.

### §S2.3 L_LOCO — voxel-level color prediction (V4 only)

Leave-one-color-out within-subject voxel prediction accuracy. V4 only valid (V1/V2/V3 fail permutation null — voxel covariance, not color signal; project memory 2026-03-11).

```
For each held-out color c:
    W_c     = ridge_GCV trained on CVD's 7 train colors
    Y_pred  = C(θ_c + δθ(θ_c)) @ W_c
    ρ(c)    = corrcoef(Y_pred, Y_obs)
L_LOCO = mean_c ( 1 − ρ(c) )
```

**Limitation (Cycle 5 finding, §S8.C5)**: Within-CVD ridge LOCO is *direct double-dip* — train+test on same CVD. B1 run-level CV wrapper does not resolve (audit confirmed 0.03 difference). True resolution requires cross-subject SRM-aligned encoder (deferred).

### §S2.4 L_RDM — pairwise distance geometry (per-ROI)

Cosine distance between simulated ΔRDM and observed ΔRDM (CVD − HC pool).

```
ΔRDM_obs     = rdm_CVD − rdm_HC_mean
ΔRDM_sim[s]  = pdist(Y_shift, corr) − pdist(Y_base, corr)   # per HC, W-fixed
L_RDM        = 1 − cos( mean_s(ΔRDM_sim[s]), ΔRDM_obs )
```

**Variants (v6 pending)**: voxel-RDM (v3-v5) vs **A2 PCA-aligned RDM** (Cycle 5 §S8.C5 — 2× cleaner real-vs-null separation; adopted into v6).

**Static precondition limit**: cosine degenerate at δθ = 0 → Phase A admission uses raw ‖ΔRDM_obs‖ vs HC LOO null instead (§S3.2).

---

## §S3. Phase A — Precondition (S10a, complete)

### §S3.1 Pass criterion

Per (cell × loss): **signed Cohen's d = (L_CVD − L_HC_LOO_mean) / L_HC_LOO_SD ≥ +0.5**, at δθ = 0. Direction-aware (one-sided): negative d means CVD closer to HC mean than HC subjects themselves.

### §S3.2 Precondition table (cell × loss)

| Cell | L_γ_mean | L_γ_max | L_γ_top3 | L_RDM | L_LOCO (V4 only) |
|---|---|---|---|---|---|
| sub-08 V1 | +5.21 ✓ | +7.29 ✓ | +8.69 ✓ | +2.31 ✓ | — |
| sub-08 V2 | (same L_γ) | | | +1.94 ✓ | — |
| sub-08 V3 | | | | +0.86 ✓ | — |
| **sub-08 V4** | ✓ | ✓ | ✓ | +2.19 ✓ | **+3.04 ✓** |
| sub-09 V1 | −0.30 ✗ | −0.06 ✗ | −0.23 ✗ | +0.81 ✓ | — |
| sub-09 V2 | ✗ | ✗ | ✗ | −0.23 ✗ | — |
| sub-09 V3 | ✗ | ✗ | ✗ | −0.48 ✗ | — |
| **sub-09 V4** | ✗ | ✗ | ✗ | −0.24 ✗ | **+1.61 ✓** |
| sub-10 V1-V4 | NA | NA | NA | all ✗ | +0.57 ✓ (FP) |

### §S3.3 Per-pair L_γ atoms (decomposition fix)

Sub-09 aggregate L_γ fails — per-pair decomposition recovers **L_γ_GB (green-blue)** as the only admitted behavioral atom for sub-09.

| Pair | sub-08 d | sub-09 d |
|---|---|---|
| orange-yellow | **+7.97 ✓** | −0.57 ✗ |
| yellow-green | **+7.49 ✓** | −0.35 |
| yellow-purple | **+39.4 ✓** | −0.38 |
| **green-blue** | −0.50 ✗ | **+0.81 ✓** |

### §S3.4 Per-subject atom set (Phase B input)

| Subject | Admissible atoms | # |
|---|---|---|
| **sub-08** | L_γ_OY, L_γ_YG, L_γ_YP, L_RDM_{V1,V2,V3,V4}, L_LOCO_V4 | 8 |
| **sub-09** | L_γ_GB, L_RDM_V1, L_LOCO_V4 | 3 |
| sub-10 | — (descriptive control only) | 0 |

---

## §S4. Phase B — Inclusion screening

### §S4.1 Design (cross-modal generalization)

For each (subject, model, inclusion combo):
1. **Sub-08**: cross-ROI combos (γ × RDM × LOCO; 40 v3, 59 v4, 71 v5 after γ_all)
2. **Sub-09**: 8–11 combos (cross-ROI L_γ_GB + L_RDM_V1 + L_LOCO_V4 + v5 γ_all variants)

Pipeline:
1. **1000× random size-5 HC subset resample** (without replacement within draw)
2. **Baseline swap**: train HC pool ≠ test HC pool (different subset draws)
3. AIC/BIC: secondary parsimony comparison (deviance × N_pairs corrected)

### §S4.2 Composite loss

```
L_total(δθ; subject) = Σ_atom (1/√n_atoms) · z_atom(L_atom)
```

z_atom standardizes per atom within the train HC LOO distribution. Single δθ(c) 8-vector per (subject, model, combo).

### §S4.3 Selection metrics (USER DIRECTIVE 2026-05-25)

| Priority | Metric | Role |
|---|---|---|
| **Primary** | Test-loss median (over HC resample) | Direct held-out evaluation |
| **Primary** | Test-loss IQR | Stability across HC subsets |
| Supplementary | AIC / BIC | Model-class parsimony |
| Supplementary | L_JND (held-out aggregate 8-pair) | Behavioral coherence — **deprecated if L_γ in training (circular)** |
| Supplementary | Boundary rate | Grid stability |

### §S4.4 Version history (compressed)

- **v3** (initial): 40 sub-08 combos × γ × RDM forced non-empty; 8 sub-09 combos. Enumeration gap exposed (LOCO-only single-atom missing).
- **v4** (2026-05-25, `s10b_v4_single_atom.py`): single-atom combos enabled → 59 sub-08 combos. NEW combos dominate top rankings; Phase C C3 LOCO-only g=1.10 finding confirmed as enumeration-discovered (not Phase-C-derived).
- **v5** (2026-05-26, `s10b_v5_gamma_all.py`): γ_all atom added (sum z² of 8 pairs). Result: γ_all + neural composite reproduces existing fit (z-score equalizes information density). γ_all standalone reproduces Cycle 2 behavioral-only fit exactly — see §S8.C3.
- **v6 (PENDING)**: A2 PCA-RDM atom replaces voxel-RDM (Cycle 5 §S8.C5). Phase B rerun expected to preserve candidate ranking with ≤10% numerical shift.

### §S4.5 Final candidate table (v5-validated; v6 pending)

#### Multi-atom candidates (Phase C weight-sweep applied)

| ID | Subject | Combo | Model | Δλ | Best weight | Params | Test_loss (med ± IQR) | Bdy | Forward RMS | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| S08-E_v4 | sub-08 | γYG\|RDMV2\|LOCO | 2-comp | — | (1, 0, 0) γYG-only | (β_s=38, β_c=−44) | −1.33 ± 6.94 | 6% | 29° | Pipeline 2 historical; superseded by Pipeline 3 |
| S08-B | sub-08 | γ_\|RDMV2\|LOCO | R+C | DPS_lit 6.0 | (0.25, 0.75) LOCO-dom | g = 2.60 | −1.46 ± 0.21 | 0% | −19° | Pipeline 2 historical; R+C sensitivity comparison only |
| S09-A_DPS | sub-09 | γGB\|RDMV1\|noLOCO | R+C | DPS_lit 10.0 | (1, 0) γGB-only | g = 2.60 | −0.81 ± 30.50 | 0% | 21° | Pipeline 2 historical; close to Pipeline 3 E1 top (g=3.00 Boehm_low) |

#### Single-atom carry candidates (Phase B value preserved, Phase C skipped)

| ID | Subject | Combo (atoms) | Model | Δλ | Params | Test_loss | Forward RMS | Status |
|---|---|---|---|---|---|---|---|---|
| **S08-C** | sub-08 | LOCO-only | R+C | DPS_lit 6.0 | g = 1.10 ± 0.00 | −1.83 ± **0.00** | **29°** ✓ | Secondary (IQR=0 artifact caveat) |
| ~~S08-D~~ | sub-08 | γYP-only | 2-comp | — | β_s=34, β_c=48 | −1.73 ± 0.89 | **50°** ✓ | DROP (β_c grid-edge) |
| **S09-B** | sub-09 | RDM_V1-only | R+C | JND_Lamb 1.5 | g = 2.45 ± 0.05 | −1.49 ± 4.20 | **4°** ✗ | Supplementary (A2 preference; **Phase 3 fail**) |
| ~~S09-C~~ | sub-09 | RDM_V1-only | 2-comp | — | β_s=6, β_c=46 | −1.79 ± 0.11 | **34°** ✓ | DROP (Round 2 non-identifiable) |

(†) LOCO-only IQR=0 artifact: LOCO atom is CVD-internal (no HC pool dependency) → train ≡ test by construction. Not a generalization measurement. Same atom-definition limit applies to any LOCO-only weight cell in Phase C.

### §S4.6 Acknowledged caveats (apply to all candidates)

1. **Interior is minority for most sub-08 cells** (12–34% interior in 4 of 5 top candidates) — "interior-only" candidate is conditional on which 5 HCs are drawn.
2. **R+C Δλ-source bimodality (sub-08)**: same atom config → g ≈ 0.05 (Boehm_mid 8nm under-comp floor) OR g ≈ 2.65–2.95 (DPS_lit/JND_Lamb over-comp ceiling). **Mechanism direction is Δλ-prior-determined, not data-identifiable for sub-08.** Sub-09 robust within-branch (all priors g ∈ 2.25–2.95).
3. **V1-RDM cosine ≈ random for sub-08** (all 5 candidates 0.94–1.21). Sub-09 V1-RDM 0.84–0.99 stronger.
4. **β_s = 48 (sub-08 alt) is geometric boundary-adjacent** — `boundary` flag only catches ±50, so β_s = 48 sits at 96% of BS_MAX.
5. **No end-to-end LOO**: v3-v5 = candidate identification with HC subset resample (5-train/2-test), not full 7-fold LOO. Phase C v2 adds weight sweep (§S5).

---

## §S5. Phase C — Weight sweep + multi-point validation sim

### §S5.1 Design (locked 2026-05-25)

**Weight grid**: 2-simplex Dirichlet (3-atom candidates, 10 points) or 1-simplex (2-atom, 5 points):

```
Vertices (3):     (1, 0, 0), (0, 1, 0), (0, 0, 1)
Edge midpoints (3): (0.5, 0.5, 0), (0.5, 0, 0.5), (0, 0.5, 0.5)
Off-vertex (3):   (0.6, 0.2, 0.2), (0.2, 0.6, 0.2), (0.2, 0.2, 0.6)
Centroid (1):     (1/3, 1/3, 1/3)
```

For 2-atom: (1, 0), (0.75, 0.25), (0.5, 0.5), (0.25, 0.75), (0, 1).

**Composite**: `L_composite = Σ_atom w_atom · z(L_atom)`, with `Σ w_atom = 1`.

**N_RESAMPLES = 100** per weight cell (reduced from Phase B 300).

**Single-atom candidates**: Phase C SKIPPED (DOF = 0); Phase B test_loss carried forward.

**No prior / no smoothing penalty** — Task #50/#52/#53 + advisor convergent verdict; Sadil 2022 prior data-dominated. Grid-edge fits reported as Phase B caveats, not modified by Phase C.

### §S5.2 Phase C v2 results (complete 2026-05-25)

**Cost**: sub-08 = 300s, sub-09 = 57s.

#### S08-B: γ_|RDMV2|LOCO R+C DPS_lit (1-simplex 5pts)

| Weight | Test_loss | Bdy | g |
|---|---|---|---|
| RDM_V2-only (1, 0) | **−1.98 ± 0.91** | 100% | g = 3.0 ceiling |
| LOCO-only (0, 1) | −1.83 ± 0.00 | 0% | g = 1.10 (= S08-C) |
| Equal (0.50, 0.50) | −1.47 ± 0.46 | 0% | g = 2.70 |
| **LOCO-dom (0.25, 0.75)** | **−1.46 ± 0.21** | **0%** | **g = 2.60 ± 0.00** |

→ LOCO-dominant weight = tightest interior IQR in sub-08, g = 2.60 over-comp.

#### S08-E: γYG|RDMV2|LOCO 2-comp (10-pt 2-simplex)

| Weight | Test_loss | Bdy | Params |
|---|---|---|---|
| LOCO-only (0, 0, 1) | −3.43 ± 0.00 | 100% | (β_s=50, β_c=50) corner |
| **γYG-only (1, 0, 0)** | −1.33 ± 6.94 | **6%** | **(β_s=38, β_c=−44) interior** |
| Mixtures | −0.93 to +0.56 | 47–100% | corner-pulled |

→ γYG-only vertex = sole interior stable solution. Phase B v3 C2 (38, −44 with equal weight) and Phase C γYG-only (38, −44) **converge** — consistent 2-comp interior estimate.

#### S09-A_DPS: γGB|RDMV1|noLOCO R+C DPS_lit (1-simplex 5pts)

| Weight | Test_loss | Bdy | g |
|---|---|---|---|
| **γGB-only (1, 0)** | best | **0%** | **g = 2.60 (interior)** |
| RDM_V1-only (0, 1) | tight | 2% | g = 2.45 |
| Mixtures | various | various | g ∈ [2.45, 3.0] |

→ γGB single-atom vertex = preferred interior. R+C g = 2.60 stable across DPS_lit prior.

### §S5.3 Pre-Phase-C null sanity sim (v1) — summary

Bootstrap leave-one-HC-as-CVD; SUBSET_SIZE = 4; 50 outer iterations. GT: δθ = 0 (synthetic CVD = HC).

- **R+C**: g median ≈ 1.85–1.95 across all 3 Δλ sources — **PASS** (near GT = 2 within ±0.2 tolerance).
- **2-comp**: β_s median 0 (range [0, 50]); β_c median +10 (range [−34, +48]); boundary rate 70%. Full grid span at δθ = 0 GT = **concern point** (paper-level caveat, not "design FAIL").

Caveat: SUBSET_SIZE = 4 in v1 ≠ Phase B's 5. v3 sim (§S7) deferred to resolve.

Decision: Phase C launched under working hypothesis that Phase B 2-comp may be real signal; v1 2-comp concern documented.

### §S5.4 Post-Phase-C multi-point validation sim (Task #54)

#### Round 1 (Task #54.1, 2026-05-25)

Bootstrap leave-one-HC-as-CVD; SUBSET_SIZE = 4; N_outer = 50. GT set per candidate: null (g=2 R+C or β=0 2-comp) + fit-point.

| Candidate | Null GT recovery | Fit-point GT recovery | Verdict |
|---|---|---|---|
| **S08-B** R+C DPS_lit (GT g=2.60) | **FAIL**: g̃=0.50 (range [0.05, 2.40]) | g̃=2.45 ± 0.00 (range [2.05, 2.55]) | Null pull caveat; fit acceptable |
| **S08-E** 2-comp (GT 38, −44) | partial: median (0, −4) IQR (8, 64) | **FAIL**: β̃_s=26 ± 40, β̃_c=−26 ± **98** (≈ full grid) | **Non-identifiable at fit-point** |
| **S09-A_DPS** R+C DPS_lit (GT g=2.60) | **PASS**: g̃=2.00 ± 0.19 (exact at null) | g̃=2.25 ± 0.05 | **Best identifiable candidate** |

#### Round 2 (Task #54.2)

S08-D and S09-C re-tested under same design. Both confirmed non-identifiable at fit-point → DROP both per §S4.5.

**Pending**: full multi-point validation at SUBSET_SIZE = 5 with v3 empirical low-rank synthesis (§S7).

### §S5.5 Phase D trigger evaluation (per §S6.4)

| Cond | S08-B (g=2.60) | S08-E (β=38,−44) | S09-A_DPS (g=2.60) | S09-B (g=2.45) |
|---|:-:|:-:|:-:|:-:|
| **1. Test_loss CI95 excludes HC LOO p75** | TBD | TBD | TBD | TBD |
| **2. Pre-image 8/8 exact** | TBD (R+C inversion) | ✓ (2-comp confirmed §S1.2) | TBD | TBD |
| **3. Param non-boundary** | ✓ (g=2.60 mid) | ✓ (β interior) | ✓ (g=2.60 mid) | ✓ (g=2.45 mid) |
| **4. Forward δθ \|·\| ≥ 5°** | ✓ (−19°) | ✓ (29°) | ✓ (21°) | **✗ (4°)** |
| **5. HC specificity boot_frac (descriptive)** | TBD | TBD | TBD | TBD |

**Critical**: S09-B fails Cond 4 (forward 4° RMS) — JND_Lamb Δλ=1.5 nm + g=2.45 attenuates Machado(1.5nm)=9° baseline. Not Phase 3 testable. Retained as A2-PCA-preference supplementary only.

---

## §S6. Phase D — Final selection + Phase 3 trigger

Trigger: Phase C selects per-subject top-1; v6 PCA-RDM Phase B rerun confirms ranking.

### §S6.1 Pre-image extraction

For each selected (model, params), invert forward δθ over 720 hue angles → 8 canonical pre-image angles. **Required**: 8/8 EXACT (err < 0.001°). Failure → reject and fall back.

### §S6.2 Descriptive HC specificity check (§0 rule)

```bash
python scripts/hc_specificity_check.py --beta_s <val> --beta_c <val> --cvd_type <type> --roi V4
```

Report `boot_frac` as descriptive only. NOT a selection criterion (§0 framework — HC FPR 100% confirmed at 13 cycles).

### §S6.3 Forward δθ 4-col visualization

STIM_LAB convention (`scripts/stim_lab_render.py`):
- Col 1: Original 8 hues
- Col 2: CVD perceives (Machado simulation)
- Col 3: Filter pre-image (inverse)
- Col 4: CVD(Filter) — perceptual restoration estimate

### §S6.4 Phase 3 trigger conditions (5)

1. ✓ Phase C top-1 has test L_γ_focal CI95 excluding HC LOO 75th percentile
2. ✓ Pre-image 8/8 exact
3. ✓ Param non-boundary
4. ✓ Forward δθ ‖·‖ ≥ 5° (perceptually testable)
5. (Descriptive only) HC specificity boot_frac reported

### §S6.5 Acceptance criteria (post Phase 3)

Filter accepted into paper findings only if Phase 3 shows:
- Focal-atom JND improvement (z ≤ −0.5 vs no-filter)
- No degradation on non-focal pairs (z ≥ −0.5)
- Consistent across ≥ 4 of 6 runs

---

## §S7. Future TODO — v3 sim (empirical low-rank covariance)

**Status**: PENDING. Not blocking Phase D launch.

**Purpose**: address v1's SUBSET_SIZE = 4 limit (literal HC bootstrap leaves 6-HC pool) while preserving voxel correlation that RDM atoms depend on.

**Design**: Estimate `Σ_HC` per (ROI, color) from real HC pool (n=7), take top-k eigenvector low-rank approximation `Σ_HC ≈ U_k diag(λ) U_k^T`, sample synthetic CVD as `Y_synth = μ_HC + L_k @ ε`. Apply Phase B's full design at SUBSET_SIZE = 5 + 7-HC pool.

**Decision trigger**: launch v3 IF Phase D real-data 2-comp shows persistent grid attraction not seen in v1 size-4 sim — suspect inherent inflation at SUBSET_SIZE = 5 that v1 cannot rule out.

---

## §S8. Cycle 1–5 diagnostic findings (post-Phase-C re-examination)

User-triggered re-examination on 2026-05-26 — concern: R+C candidates' forward δθ visualizations did not match observed CVD behavior, while 2-comp matched approximately. See `BEHAVIORAL_FIT_DIAGNOSIS_2026-05-26.md` for full detail.

### §S8.C1 — Per-pair JND prediction error

Forward δθ → JND_pred per pair → vs observed z² mismatch.

| Candidate | Subject | Model | Total z² | Forward RMS |
|---|---|---|---|---|
| **S09-A_DPS** | sub-09 | R+C g=2.60 | **4.48** | 21° |
| **S08-E** | sub-08 | 2-comp (38, −44) | **49.87** | 29° |
| S08-C | sub-08 | R+C g=1.10 | 83.91 | 29° |
| S08-B | sub-08 | R+C g=2.60 | 89.43 | 19° |
| S09-C | sub-09 | 2-comp (6, 46) | 93.86 | 34° |
| S08-D | sub-08 | 2-comp (34, 48) | 4065 | 50° |

**Sub-08 per-pair breakdown**: R+C fails *orange-yellow z²=16* + *yellow-green z²=17* — sub-08's yellow-region deficit is outside Machado(Δλ) red-green axis. 2-comp's β_s S-cone term captures it.

**Verdict**: sub-08 R+C is *Machado-limited*; sub-09 R+C is robust (best overall behavioral fit at z²=4.48).

### §S8.C2 — Behavioral-only fit (composite minus neural atoms)

γ_all single-atom fit (no RDM, no LOCO), grid argmin.

| Subject | Model | Behavioral-only fit | Composite fit (Phase C v2) | Shift |
|---|---|---|---|---|
| sub-08 | R+C DPS_lit | **g\* = 2.25** | g = 2.60 | **+0.35 neural-biased** |
| sub-08 | 2-comp | **(β_s=48, β_c=−36)** | (β_s=38, β_c=−44) | Different grid region |
| sub-09 | R+C DPS_lit | **g\* = 2.60** | g = 2.60 | **Identical** |
| sub-09 | 2-comp | **(β_s=26, β_c=4)** | (β_s=6, β_c=46) | Different grid region |

**Verdict**: sub-08 composite g is *neural-biased* (RDM+LOCO pull g 2.25 → 2.60). sub-09 R+C is *robust across atom weights*. 2-comp shows neural-vs-behavioral conflict in both subjects.

### §S8.C3 — γ_all atom (Phase B v5)

`γ_all` = sum z² over 8 pairs added to v5 enumeration (71 sub-08 combos, 11 sub-09 combos).

**Result**: γ_all + neural composite *reproduces existing fit* — z-score normalization equalizes atom information density (γ_all = 8 z² vs γYG = 1 z² has no advantage post-z-score). γ_all *standalone* (no RDM, no LOCO) **reproduces Cycle 2 behavioral-only fit exactly** (sub-08 2-comp 26,4 etc.).

**Verdict**: γ_all atom is valid (matches behavioral-only fit) but **insufficient as composite reform** — z-score composite equalizes information density. Real fix requires either (W1) weight-sweep with explicit γ_all weights ∈ {0.5, 0.7, 0.9}, (W2) raw composite without z-score, (W3) behavioral-anchored composite `L_γ_all + λ·L_neural`, or (W4) single-atom γ_all combo. Not adopted into v6 candidate set; remains future work.

### §S8.C4 — Pipeline-level double-dipping audit

| Atom | Train source | Test source | Double-dip status |
|---|---|---|---|
| γ atom | HC train pool JND | HC test pool JND | partial (CVD JND fixed) |
| RDM atom | HC train pool RDM mean | HC test pool RDM | partial (CVD RDM fixed) |
| **LOCO atom** | within-CVD ridge LOCO | within-CVD pred | **DIRECT double-dip** — IQR=0 artifact |

Root: random source = HC subset only. CVD-internal CV absent.

### §S8.C5 — Atom redesign (A1/A2/A3/B1)

Subagent task aebe2550. Script: `scripts/s14_atom_redesign.py`. PCA proxy used in lieu of SRM/BrainIAK.

| Approach | Result |
|---|---|
| **A2 PCA-aligned RDM** | ✅ **Adopted into v6** — 2× real-vs-null separation vs voxel-RDM (sub-08 V4 gap 0.21-0.36 vs 0.0-0.18). Sub-09 V1 IQR 0.03-0.06 tight. |
| A1 cross-subject decoder | ❌ Inverted (null=0.39 best, real=0.43-0.98 worse) — Procrustes circularity |
| A3 cross-subject LOCO | ❌ Flat across candidates + nulls (range 1.13-1.34) — K=6 PCA bridge collapses signal |
| B1 CVD run-level CV wrapper | Audit only — wrapper ≈ unwrapped (0.03 diff). **LOCO double-dipping fundamentally unresolved** (within-CVD W training on train+test). Cross-subject SRM-aligned encoder required (deferred). |

**Critical conflict raised by A2**: A2 PCA-RDM prefers S09-A_orig (R+C JND_Lamb g=2.45 @ 0.696 ± 0.031) over S09-A_DPS (0.727 ± 0.042). But S09-A_orig has forward 4° < 5° threshold (Phase 3 trigger fail).

**Verdict**: Sub-09 has *neural evidence vs behavioral testability conflict*. Paper-level narrative options:
1. Honest: report conflict, no filter design possible for sub-09.
2. Compromise: S09-A_DPS for Phase 3, A2 sensitivity reported as supplementary.
3. Direct: dual-report similar to sub-08 framing.

### §S8 — Cycle 1–5 paper implications

| Cycle | Finding | Paper status |
|---|---|---|
| 1 | sub-08 R+C cannot fit yellow-region deficit (OY/YG z²>16 each) | Limitation statement; motivates 2-comp dual-report for sub-08 |
| 2 | Composite g is neural-biased for sub-08 (+0.35 shift) | Limitation; sensitivity analysis figure |
| 3 | γ_all standalone = behavioral-only fit exactly; composite equalizes via z-score | Method choice rationale; not adopted into final pipeline |
| 4 | LOCO is direct double-dip; B1 wrapper insufficient | Major limitation; deferred to cross-subject SRM (future work) |
| 5 | A2 PCA-RDM 2× cleaner — adopt into v6 | Method refinement; v6 rerun in progress |

---

## Appendix A. Pipeline assumptions (recap)

| # | Assumption | Source |
|---|---|---|
| A1 | Post-cortical mapping HC = CVD | Project core |
| A2 | 3 model classes only (Machado / R+C / 2-Comp) | Locked |
| A10 | Encoder = ridge_gcv | 3 rescue attempts of smooth_tikh failed |
| A11 | Single mechanism per subject | No model averaging |
| A12 | 2-Comp operates in CIELab opponent space | `machado_shifted_hue(0.0, family)` baseline |

## Appendix B. Limitations (paper-reportable)

1. L_LOCO and L_RDM use different encoder references (within-subject vs HC pool)
2. L8 composite = weighted compromise, not unified δθ estimate
3. Bootstrap unit = trial (color set fixed)
4. Δλ = external prior (3 sources reported as sensitivity sweep); Δλ-source bimodality for sub-08
5. HC pool g under CVD-model = procedural baseline (model misspecification noted)
6. **LOCO double-dipping**: within-CVD ridge LOCO is direct double-dip; B1 wrapper insufficient; cross-subject SRM-aligned LOCO deferred (Cycle 5)
7. **2-comp non-identifiability**: N=7 HC pool insufficient for fit-point identifiability (Round 1 multi-point sim shows β_c IQR=98 at fit-point for S08-E)
8. **Δλ-source bimodality (sub-08)**: same atom config gives g=0.05 (Boehm_mid 8nm) vs g=2.60 (DPS_lit 6nm); mechanism direction not data-identifiable
9. Phase 3 not yet executed; trigger condition #4 fails for sub-09 S09-B variant

## Appendix C. Files

- Forward models: `scripts/rc_1dof.py`, `scripts/two_comp.py`
- Loss functions: `scripts/behav_loss.py`, `scripts/neural_loss.py`
- Phase A (S10a): `scripts/s10a_precondition.py`
- Phase B (v3/v4/v5): `scripts/s10b_v3_extended.py`, `s10b_v4_single_atom.py`, `s10b_v5_gamma_all.py`
- Phase B v6 (PENDING): A2 PCA-RDM atom integration
- Phase C v2: `scripts/s12b_phase_c_v2.py`
- Multi-point sim: `scripts/s13_multipoint_validation.py`
- Atom redesign (Cycle 5): `scripts/s14_atom_redesign.py`
- Visualization: `scripts/stim_lab_render.py`, `scripts/s7_best_models_4col.py`
- Results: `results/s10_precondition/`, `results/s10_inclusion/`, `results/s12b_phase_c_v2/`, `results/s13_multipoint_sim/`, `results/s14_atom_redesign/`

## Appendix D. Phase B enumeration history (compressed)

- **v3** (40 sub-08 / 8 sub-09 combos; γ + RDM forced non-empty)
- **v4** (59 sub-08 / 8 sub-09; single-atom enabled — "not all empty" filter)
- **v5** (71 sub-08 / 11 sub-09; γ_all atom added)
- **v6 PENDING** (A2 PCA-RDM atom replaces voxel-RDM)

Full v3-v5 candidate enumeration tables: see git history `PIPELINE_UPDATED_0524.md` revision 2026-05-25.

## Appendix E. Cycle 1–5 source documents

- `BEHAVIORAL_FIT_DIAGNOSIS_2026-05-26.md` — Cycle 1–5 full narrative
- Cycle 1 script: `scripts/s10c_per_pair_jnd_diag.py` (per-pair z² report)
- Cycle 2 script: `scripts/s10d_behav_only_fit.py`
- Cycle 3 script: `scripts/s10b_v5_gamma_all.py`
- Cycle 5 script: `scripts/s14_atom_redesign.py`
