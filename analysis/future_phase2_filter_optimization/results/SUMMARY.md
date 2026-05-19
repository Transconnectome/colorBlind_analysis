# Phase 2 Filter Optimization — Summary

**Date**: 2026-05-19 (narrative finalized — Phase 2 BEST strengthened; loss-external CVD-HC tests removed from paper anchor; advisor BLOCKERs resolved)
**Directory structure**: `MANIFEST.md`. **Machine-readable filter**: `BEST_summary.json`.

---

## Current Best Filter (Phase 2 closure)

The Phase 2 deliverable is a **per-subject inverse filter** — a stimulus-space angular shift δ(θ) that, when applied to the 8 DKL hue stimuli, drives a CVD subject's V4 LOCO vulnerability profile toward the HC pool's profile. The filter is a 2-component cortical opponent rotation computed in Stockman opponent hue space and accumulated in CIELab:

    h(θ_CIELab)  =  Stockman opponent hue projection of θ_CIELab  (computed from CIE Stockman cone fundamentals)
    δθ(θ_CIELab) =  β_s · cos(h − 90°)  +  β_c · cos(h − θ_conf)
    θ_perceived  =  (θ_CIELab + δθ) mod 360°

where the S-cone axis is at h = 90° (Stockman opponent) and the L/M confusion axis is set per family: **θ_conf = 150° (deutan), 16° (protan)** in Stockman opponent space. The Stockman opponent projection h(·) is the non-trivial step that makes a single (β_s, β_c) pair produce a per-color δθ vector that varies with the CIELab anchor (see per-subject table below). The S-cone term modulates blue/yellow distortion; the confusion-axis term modulates L/M opponency.

**Reproducibility note**: numerical reproduction of the δθ values below requires `colour-science` installed (full Stockman cone fundamentals). The fitting pipeline (`forward_models/two_component.py`) falls back to approximate cone fundamentals if `colour-science` is unavailable, which changes h(·) and thus the per-color δθ values. The Phase 2 BEST coordinates `(β_s, β_c)` reported here were computed under full Stockman fundamentals; local environments without `colour-science` should install it before recomputing.

| Subject | (β_s, β_c) | ‖filter‖ | max ‖δθ‖ | perm_p | ρ_LOCO | corrected P2a (post-hoc) | Pre-image | Etiology (R+C diagnostic) |
|---|---|---:|---:|---:|---:|---:|:-:|---|
| **sub-08 deutan** | (38°, **−14°**) | 40.5° | 32.1° (cyan) | **0.004 ★★** | 0.881 | **0.750** (2/8 exact, > identity 0.688) | 8/8 ✓ | Cortical-dominant (Δλ=2.5 nm, g=−2.25 — large cortical overshoot, small retinal shift) |
| **sub-09 protan** | (6°, **−22°**) | 22.8° | 21.1° (blue) | **0.035 ★** | 0.690 | **0.975** (7/8 exact, ≥ identity 0.975) | 8/8 ✓ | Retinal-dominant (Δλ=19.5 nm, g=−1.10 near-physiological — large retinal shift, minimal cortical compensation) |

**Per-subject filter δθ vector** (degrees, applied to each DKL hue to generate corrected stimulus angles):

| color (DKL θ) | red 0° | orange 45° | yellow 90° | green 135° | cyan 180° | blue 225° | purple 270° | magenta 315° |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| sub-08 δθ | −12.1° | −20.2° | −25.7° | −29.4° | −32.1° | −10.3° | **+29.4°** | +18.5° |
| sub-09 δθ | −15.5° | −10.9° | −6.5° | −2.4° | +2.4° | **+21.1°** | +2.4° | −20.7° |

Two qualitatively different signatures emerge. **Sub-08** shows a near-uniform negative shift across red→cyan (the green/cyan region most strongly compressed) with a large opposite-sign rotation at purple/magenta — a wide-amplitude L/M-rotation pattern with non-trivial β_s (38° S-cone term) that produces 66.5° total filter norm. The R+C decomposition yields large cortical overshoot (g = −2.25) on a small retinal shift (Δλ=2.5 nm), pointing to cortical-dominant CVD etiology in this subject. **Sub-09** shows a far smaller, monotonic rotation along the protan confusion axis with peak displacement at blue/magenta (consistent with the Stockman 16° axis projection), small β_s, and total filter norm 22.8°. The R+C diagnostic recovers Δλ=19.5 nm (within the published cone-shift range for protan) and g=−1.10 (near-physiological, no cortical overshoot), pointing to retinal-dominant etiology.

The filter is **bijective in 8-color stimulus space** — `inverse_2component` recovers the exact pre-image angles for all 8 colors in both subjects (`results/loco_filter/preimage_2component/`). This means the corrective stimulus angles `θ_corrected = θ_original − δθ` are well-defined and renderable; behavioral filter application is mathematically realizable.

P2a (per-subject post-hoc consistency check, **not paper-reportable as primary endpoint due to circularity**): sub-08 reaches 0.750 (2/8 exact + partial color matches under the 9-bin scheme; identity-filter baseline 0.688), sub-09 reaches 0.975 (7/8 exact, tied with identity baseline — consistent with retinal-dominant etiology predicting minimal cortical-side benefit).

**Loss form**: `L_fit = α·L_vuln + β·L_rank + δ·L_rdm + ε·L_smooth` with `(α, β, δ, ε) = (1.0, 0.5, 0.2, 0.1)` (`loco_distortion_fit.py:88,214–266`) @ V4 hV4 LOCO
**Source of truth**: `BEST_summary.json` | **Viz**: `BEST_4col_sub-{08,09}_V4_LOCO_canonical_*.{png,pdf}`

### Loss term definitions (all terms in [0,1] after normalization)

Let `v_sim ∈ R^8` = simulated HC vulnerability (per-color LOCO 1−ρ) at shifted angles, `v_cvd ∈ R^8` = observed CVD vulnerability target, `Δrdm_sim, Δrdm_obs ∈ R^28` = simulated and observed CVD−HC RDM differences over 8C2 color pairs at hV4, `δθ ∈ R^8` = per-color hue shift in degrees produced by the 2-comp model.

| Term | Raw formula | Normalizer | Range | Role |
|---|---|---:|:-:|---|
| **L_vuln** | `(1/8)·Σ_c (v_sim[c] − v_cvd[c])²`  (per-color MSE) | 4.0 | [0,1] | **Primary fit**: match per-color predictability profile (where CVD breaks down vs preserves) |
| **L_rank** | `1 − ρ_Spearman(v_sim, v_cvd)`  (8-point rank correlation) | 2.0 | [0,1] | **Ordering**: penalize rank-reordering of vulnerable colors |
| **L_rdm** | `1 − cos(Δrdm_sim, Δrdm_obs)`  (cosine over 28-pair upper-tri) | 2.0 | [0,1] | **Geometry**: match V4 cross-color distance distortion direction |
| **L_smooth** | `(1/8)·Σ_c [(δθ[c+1] − δθ[c]) mod ±180]²`  (circular adjacent-diff²) | 32400 (=180²) | [0,1] | **Regularizer**: discourage discontinuous per-color shifts; favor smooth filter |

**Weights rationale** (`scripts/loco_distortion_fit.py:85–88`): α=1.0 (L_vuln dominant — direct fit to CVD voxel-prediction signature); β=0.5 (ordering tiebreaker when MSE landscape flat); δ=0.2 (geometric convergence check, downweighted because RDM and per-color signals overlap); ε=0.1 (smoothness prior).

**ROI scope**: All four terms computed at **hV4 (V4 on disk)** only. L_vuln/L_rank use V4 LOCO encoder predictions; L_rdm uses V4 voxel-level RDM.

**Why hV4 — biological prior**: hV4 is the canonical **color processing hub** at the highest hierarchical level of the ventral color stream and the cortical region most directly associated with conscious color perception (Brouwer & Heeger 2009; Bannert & Bartels 2018; Kuriki et al. 2015). The 2-component cortical opponent rotation operates at this level by construction; fitting at hV4 is the biologically motivated default, not a post-hoc statistical choice.

**Forward-model gate (independent supporting evidence)**: hV4 is the **only ROI** whose HC group-level LOCO interpolation exceeds the permutation null (`future_phase1_forward_model/results/loco_reinforcement/permutation_test.json`; **single uncorrected test, n=7 HC subjects** — paper Methods will state these qualifiers verbatim):

| ROI | observed ρ | null mean | null SD | p_perm |
|---|---:|---:|---:|---:|
| **hV4** | 0.183 | 0.080 | 0.059 | **0.044 ★** |
| V1 | 0.130 | 0.109 | 0.034 | 0.274 NS |
| V2 | 0.150 | 0.130 | 0.039 | 0.311 NS |
| V3 | 0.023 | 0.078 | 0.046 | 0.880 NS |

This means the HC encoder can interpolate held-out colors at hV4 but not at V1/V2/V3. Fitting cone-shift `(β_s, β_c)` at hV4 yields parameters interpretable as voxel-level shifts in a working interpolation manifold. The same fit at V1/V2 would optimize 8-color ranking on an encoder that has no validated interpolation capacity, so its parameters lack voxel-level cone-shift interpretation — even when the per-subject `perm_p` is small.

**L_rdm role**: geometric **multi-objective component at the fit ROI** (V4) — penalizes filter solutions that match per-color predictability but distort the V4 pairwise distance structure. This is an *internal-consistency* term, not a CVD-vs-HC test. A magnitude-weighted variant `L_rdm = ‖Δrdm_obs‖·(1−cos)` was identified as a possible robustness check (sub-08/09 BEST stability under reweighting) and is deferred to revision-time if reviewers request it.

**ΔRDM convention**: `Δrdm_obs[k] = RDM_cvd[k] − mean_HC RDM[k]` over k=1..28 upper-triangle pairs, distance='correlation' (`diagnostic_delta_rdm.py:199`). `Δrdm_sim` uses each HC's W to predict CVD-shifted responses, then averages across HC.

Viz: `BEST_4col_sub-{08,09}_V4_LOCO_canonical_bs*_bcm*.{png,pdf}` (results/ root); identical content under `c3_relabel/CORRECTED_LOCO_canonical_4col_sub-{08,09}.{png,pdf}`.

---

## Sub-10 — excluded from paper (2nd-scan dropout)

sub-10 (mild deutan, axis=150°) **dropped out of the 2nd-scan behavioral acquisition**; no validation data is available, and the subject is **excluded from the paper**. A canonical fit was run for technical completeness only:

- 2-comp V4 LOCO, `method=shift_at_both`, canonical weights → (β_s, β_c) = (10, +22), L_fit=0.127, ρ=0.762, label_perm_p=0.018 ★
- File: `results/sub10_mild_deutan/sub-10_V4_2component.json`

Not analyzed further; not in `BEST_summary`. No within-family severity claim is made in the paper.

---

## ROI selection — side-by-side fit comparison

V1 and V4 2-comp fits exist for sub-08/09 (`results/fits/phase_a_2component/`). V4 adoption is not driven by smaller V1 fit performance — V1 actually yields lower L_fit and stronger per-subject perm_p. The decision is principled, not empirical:

| sid | ROI | (β_s, β_c) | L_fit | ρ | label_perm_p | Forward LOCO gate (HC group) |
|---|:-:|---|---:|---:|---:|---|
| sub-08 | V1 | (**50†**, **−14**) | 0.159 | 0.929 | 0.001 ★★ | p=0.274 NS |
| sub-08 | **V4** | (38, **−14**) | 0.201 | 0.881 | 0.004 ★★ | **p=0.044 ★** |
| sub-09 | V1 | (38, **+22**) | 0.151 | 0.762 | 0.018 ★ | p=0.274 NS |
| sub-09 | **V4** | (6, **−22**) | 0.209 | 0.690 | 0.035 ★ | **p=0.044 ★** |

**†** Sub-08 V1 β_s = 50.0 hits the canonical grid upper bound (β_s ∈ [0, 50]); the unconstrained V1 optimum may lie outside ±50°. V4 adoption rests on the forward LOCO gate independently of V1's free-optimum location, so this boundary effect does not load-bear on Phase 2 closure. Extended-grid verification deferred to revision-time if requested.

**Why V4 is adopted despite V1 having lower L_fit**:

1. **Forward LOCO interpolation gate**: hV4 is the only ROI whose HC group LOCO interpolation exceeds the permutation null (p=0.044 ★, n=7 HC, single uncorrected test; V1/V2/V3 NS). The HC encoder learned at V4 can predict held-out colors above chance; at V1/V2/V3 it cannot. Cone-shift parameters fit on an encoder that cannot interpolate held-out colors lack voxel-level cone-shift interpretation — they only optimize per-color rank ordering of vulnerability, not the underlying voxel patterns.

2. **Biological prior**: hV4 is the canonical color processing hub at the highest hierarchical level of the ventral color stream, most directly tied to color perception (Brouwer & Heeger 2009; Bannert & Bartels 2018; Kuriki et al. 2015). The 2-component cortical opponent rotation operates at this level by construction.

3. **Cross-ROI sub-09 β_c flip is consistent with the gate failure**: sub-09 yields β_c=+22° at V1 vs −22° at V4. If V1 fit recovered a true voxel-level cone-shift, the sign should match V4 (same retinal etiology, same Stockman confusion axis). The flip indicates V1 fit captures something other than cone-shift — likely 8-color rank reordering driven by V1's chance-level forward model.

4. **Cross-ROI sub-08 β_c sign agreement is acknowledged but not interpreted as V1 recovering cone-shift**: sub-08 yields the same β_c = −14° at V1 and V4. Two readings are possible — (i) coincidental rank-ordering alignment at chance-level V1 forward gate (sub-09 evidence supports this reading), or (ii) sub-08 V1 partially captures cone-shift direction (incompatible with the V1 forward gate failure). The paper-level claim takes reading (i): a single sign agreement on a chance-level encoder is not evidence for V1 cone-shift recovery when sub-09 V1 simultaneously shows sign flip.

5. **`L_fit` is a fit-validity metric, not a CVD-vs-HC test**: lower V1 L_fit reflects better self-prediction of the 8-color vulnerability profile, not stronger CVD signal. Self-prediction quality without forward interpolability cannot be cleaned into a stimulus-space filter parameter.

**Methods reporting plan**: V1/V2 fits will be reported in supplementary tables with the same statistical descriptors as V4, and the V4 adoption decision will be justified by the forward LOCO gate result in a single Methods paragraph. V2 was not refit because the forward gate result (V2 p=0.311 NS) is similar to V1, so the V1-vs-V4 contrast is sufficient.

---

## Three Convergent Failures (Phase 4 preview — paper Discussion claim)

Three independent attempts to fit per-individual filter parameters using progressively richer metric classes were all pre-committed with strict criteria, all failed to beat 2-comp standalone LOCO-canonical:

| # | Attempt | Class | Sub-08 outcome | Sub-09 outcome | All-pass | File |
|---|---|---|---|---|:-:|---|
| 1 | L_dir (per-pair RDM direction) | richer pairwise metric | argmin (14,−26), ratio **0.047** (flat) | argmin (−34,+16), ratio **0.067** (flat) | ✗ | `phase4_preview/l_dir_one_shot_test.json` |
| 2 | 3-comp joint (Δλ + β_s + β_c) | richer model class (R+C 2-stage) | (15, 25, −15), ratio 0.526, P2a 0.562 | (20, 0, +15), ratio 0.690, P2a 0.787 | ✗ (sub-09 c4 sign fail; c6 magenta wraparound) | `phase4_preview/3component_joint_oneshot.json` |
| 3 | Voxel-level direct MSE | bypass aggregation, full Y prediction | argmin (4, 4), ratio **0.017** (flat), P2a 0.688 (=identity) | argmin (0, +36), ratio 0.601 (sharp but wrong sign), P2a 0.775 (vs id 0.975) | ✗ | `voxel_level_fit/voxel_landscape_sub-{08,09}.json` |

**Mechanistic claim**: **In our two CVD subjects**, richer neural-fit metrics yield argmins that either flatten landscape (sub-08 across all three; voxel-level ratio 0.017 is essentially indistinguishable from identity) or sharpen toward parameters that DEGRADE behavioral P2a (sub-09 voxel-level β_c=+36° flips sign vs canonical −22°; 3-comp sub-09 β_c=+15° also flips). **Neural fit improvement ≠ behavioral filter quality.** This dissociation, observed across three independent metric classes for both subjects, supports 2-comp standalone retention as Phase 2 filter form. Generality beyond N=2 requires replication.

---

## Key Framework Decisions (logged 2026-05-16 / 2026-05-17 / 2026-05-18)

### 1. P2a as post-hoc consistency check (§0.1, REVISED 2026-05-17)
- **Not paper-reportable** as primary endpoint (circular — same data used for fit + validation)
- Used internally as binary screen: P2a ≥ identity → PRIMARY candidate; below identity → CONTROL
- All candidates (PRIMARY + CONTROL) presented in pre-registered behavioral test; asymmetric prediction is paper claim
- Independent paper validation requires NEW behavioral acquisition (pre-registered)

### 2. Statistical criteria reframe (CLAUDE.md §0.2, updated 2026-05-19)
- (2a) **Label permutation perm_p**: per-subject fit-validity on real CVD LOCO data (8-color ordering between sim_HC and obs_CVD vuln profiles). NOT a CVD-vs-HC group test; HC subjects also pass (HC FPR=100% under `hc_specificity_check.py`).
- (2b) **Loss-external CVD-vs-HC Bonferroni anchors REMOVED from paper claim** (2026-05-19): cc-matrix Bonferroni-pass story dropped because (i) sub-09 V4 cc strict-Bonf-fail at α=0.0083 (p=0.010), (ii) V4 cc Bonferroni-pass depends on n_vox=16 harmonization driven by sub-07 V4 voxel count outlier. V4 ROI choice rests on **biological prior** (hV4 = color hub, highest hierarchy, most directly tied to color perception) and **forward-model LOCO gate** (hV4 p=0.044, V1/V2/V3 NS).
- (2c) **HC LOO descriptive percentile**: context only, no p-value claim
- Strict specificity NOT validated under HC FPR=100% — descriptive only per §0

### 3. R+C decomposition: diagnostic only (advisor reversal 2026-05-16)
- R+C 2-stage as filter form: **rejected** (Check 4 empirical falsification; P2a 0.588/0.787 < 2-comp standalone 0.750/0.975)
- R+C decomposition retained as paper finding: "differential mechanism per subject (sub-08 cortical, sub-09 retinal)"
- Filter form: 2-comp standalone (LOCO-canonical)

### 4. Richer loss / model class rejection (2026-05-18, three convergent failures)
- L_dir, 3-comp joint, voxel-level direct MSE — all pre-committed with strict criteria, all failed
- L@id inversion under L_rank attributable to correlation + HC LOO + small-n structural artifact, not loss defect
- Pivot: report neural-vs-behavioral dissociation as Discussion mechanistic claim; do not chase additional loss formulations within voxel-prediction LOCO measurement family (§8 Anti-Pattern)

### 5. Phase 2 closure
- Option C (40,+26)/(12,−28) — adopted 2026-05-13 under OLD labels — **deprecated 2026-05-17**
  - Corrected-label P2a is 0.500 (sub-08, worst zone cell) / 0.887 (sub-09, below identity)
- LOCO-canonical adopted as final Phase 2 filter

---

## Next Steps (Phase 3 trigger)

1. **OSF pre-registration** (30-50 lines, prospective): freeze pipeline + behavioral acquisition protocol before subject session
2. **Independent behavioral test**: filter (PRIMARY: LOCO-canonical) vs sham vs Control candidates vs no-filter, per-color naming accuracy
3. **Subject acquisition for replication**: ≥1 additional deutan + ≥1 additional protan (within-category)
4. **Paper draft** (IMRaD framing — "computational assay, not classifier"):
   - Headline: cortical-vs-retinal etiology dissociation via 2-comp standalone fit + R+C diagnostic
   - Discussion: three convergent failures (L_dir, 3-comp, voxel-level) as evidence that behavioral primacy is necessary in filter selection
   - Acknowledged limits: N=2, HC FPR, descriptive-only

---

## Caveats (per CLAUDE.md §0)

- All filter selection is descriptive — specificity claims forbidden under HC FPR=100%
- L_rank artifact (L@id inversion) documented as methodological subtlety (correlation + HC LOO + small n)
- Three richer-metric attempts (L_dir, 3-comp joint, voxel-level) **all failed pre-committed criteria** — reframed as paper finding, not as candidates to chase
- Behavioral validation requires pre-registered independent acquisition (TO BE COLLECTED)
- Paper claims should reframe "framework" → "proof-of-concept methodology" (N=2 limit)
