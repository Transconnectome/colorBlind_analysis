# Pipeline Diagnostic + OOS Re-Analysis (2026-05-26)

## 0. Trigger and root question

- User concern (2026-05-26): R+C candidate forward δθ visualization → CVD behavior/JND mismatch (sub-08, sub-09 both). 2-comp visually closer.
- Root question: does our loss capture behavior sufficiently? Should we use JND-like behavioral data in fitting + evaluation?
- Resolution path: diagnostic cycles (Cycle 1-5) → OOS re-analysis (Pipeline 3) → still pending E2 + E3.

---

## 1. Three-pipeline retrospective (data and models invariant; selection criteria evolved)

### Common across all three pipelines

- Data: C010 amplitudes `(6 runs × 8 colors × n_vox)` per (subject, ROI). Procrustes-aligned.
- Subjects: HC sub-01..07 (n=7); CVD sub-08 deutan, sub-09 protan; sub-10 near-normal (excluded).
- ROIs: V1, V2, V3, V4 (= hV4 on disk).
- Models: R+C 1-DOF, 2-Component 2-DOF, Machado 1-way.
- Encoder: ridge_gcv (locked, §A10).

### Pipeline 1 — LOCO-primary descriptive (2026-03~04)

| Aspect | Spec |
|---|---|
| Loss | L_LOCO (V4 voxel-prediction Pearson ρ), L_RDM |
| Selection | per-subject LOCO ρ best + HC percentile descriptive + behavioral P2a (later suspended) |
| Result | sub-08 V1 2-comp (β_s=50, β_c=−14) LOCO p=0.001; sub-09 hV4 R+C |
| Problem | HC FPR = 7/7 (100%); baseline_ρ confound; V1 specificity ↔ estimability dissociated |
| Lesson | §0 framework decision (2026-05-13): specificity claim forbidden, selection-rule reformulation forbidden |

### Pipeline 2 — S7 Loss combination + HC subset resample (2026-05)

| Aspect | Spec |
|---|---|
| Loss | L_α (8AFC), L_γ_focal (per-pair JND z²), L_LOCO, L_RDM; composite via z-score across HC pool |
| Selection | Phase A precondition → Phase B inclusion (5-train/2-test HC resample × 1000) → Phase C Dirichlet weight sweep → Phase D pre-image |
| Result | S08-B R+C g=2.60 (Δλ=6 nm); S08-E 2-comp (β_s=38, β_c=−44); S09-A_DPS R+C g=2.60 (Δλ=10 nm) |
| Problems (Cycles 1-5 diagnostic) | (a) R+C cannot fit sub-08 yellow region (OY z²=16, YG z²=17 vs 2-comp 4.6/0.3); (b) z-score composite equalizes atom info density → R+C artificially elevated; (c) 2-comp non-identifiable at fit point (β_c IQR=98 in multi-point sim Round 1); (d) Cycle 6 "lowest raw γ_all" primary attempt → recognized as double-dipping |

### Pipeline 3 — OOS Re-Analysis (current, 2026-05-26)

| Aspect | Spec |
|---|---|
| Loss | same atoms + γALL (8-pair sum) |
| Selection (3-layer; §0 override accepted by user 2026-05-26) | **Layer A** prerequisites: P1 fit/eval atom separation, P2 HC-subset robustness (lexicographic median ASC, IQR ASC; LOCO IQR ignored). **Layer B** convergence: E1 behavioral pair-OOS, E2 SRM disparity reduction, E3 multi-point sim recovery. **Layer C**: §0 LOCO-best demoted to complementary metric |
| Status | E1+P2 measured (Cycle 10b below); E2 + E3 pending |

---

## 2. Pipeline 2 diagnostic evidence (Cycle 1-5, kept as scientific findings)

### Cycle 1 — Per-pair JND breakdown

Total z² per (subject, candidate) summed over 8 pairs, computed at the Phase C v2 candidate point:

| Candidate | Total z² | OY z² | YG z² | YP z² (focal) |
|---|---|---|---|---|
| S08-B R+C g=2.60 | 89.4 | 16.1 | 17.3 | 42.0 |
| S08-E 2-comp (38, −44) | 49.9 | 4.6 | 0.3 | 35.1 |
| S09-A_DPS R+C g=2.60 | 4.5 | 0.9 | 0.7 | 0.9 |

Sub-08 R+C cannot fit OY + YG (yellow region pairs). Machado shape constrained to red-green axis. 2-comp's β_s S-cone term reaches yellow region. *Behavioral evidence sub-08 mechanism ≠ pure R+C*.

### Cycle 2 — Behavioral-only fit (γ_all sum, no neural atom)

| Subject | R+C best behavioral | 2-comp best behavioral | Ratio |
|---|---|---|---|
| sub-08 | g=2.25, z²=82 | (β_s=48, β_c=−36), z²=46 | 2-comp 2× better |
| sub-09 | g=2.60, z²=4.5 | (β_s=26, β_c=4), z²=3.1 | tie |

### Cycle 3-4 — γALL atom integration (Phase B v5)

γALL atom (8-pair sum) added. z-score composite *equalizes* atom magnitude — γALL with 8 z² terms gives same composite contribution as γ_focal with 1 z² term. **Composite-level effect: none.**

### Cycle 5 — A2 PCA-aligned RDM (other A/B options failed)

| Method | Result |
|---|---|
| A1 cross-subject color decoder | inverted discrimination (Procrustes circular) |
| A2 PCA-aligned RDM (K=6) | **2× cleaner separation**; sub-08 V4 gap 0.21-0.36; sub-09 V1 IQR 0.03-0.06 |
| A3 cross-subject LOCO (PCA bridge) | flat (no signal at K=6) |
| B1 CVD run-level CV wrapper | LOCO double-dipping unresolved |

### Cycle 6 — Cycle of double-dipping recognition

"Lowest raw γ_all" ranking attempted; user critique 2026-05-26 confirmed γ_all is fit objective → using it as evaluation criterion = tautological double-dip. *Verdict withdrawn*. The (β_s=6, β_c=−42) point estimate is descriptive only, not a primary.

### Cycle 7b — Empirical SRM (BrainIAK)

| Cell | K | SRM RDM cosine sep z | Phase2 SRM disparity z |
|---|---|---|---|
| sub-08 V2 | 4 | +0.28 (weak shape) | **+2.94** (strong magnitude+shape) |
| sub-08 V4 | 3 | +0.11 (null) | +1.42 |
| sub-09 V1 | 4 | +1.34 (strong) | **+5.17** (very strong) |
| sub-09 V4 | 3 | — | +2.47 |
| sub-10 V4 | 3 | — | −1.79 (correct null) |

Two SRM measures complementary: RDM-cosine = shape only; disparity = magnitude+shape.

---

## 3. Pipeline 3 current spec (locked 2026-05-26)

### Layer A: prerequisites

| Step | Rule |
|---|---|
| P1 | Atom used in fit ≠ atom used in evaluation. LOCO is *not a valid fit atom* per §A4 (within-CVD double-dip) |
| P2 | HC-subset robustness. Sort all candidates lexicographically by `(test_loss_median ASC, test_loss_iqr ASC)`. LOCO cells use `iqr=+∞` since HC subset variation does not change CVD-internal ridge. Top 50% pass |

### Layer B: convergence evidence (3 axes; lower = better)

| Axis | Quantity | Source |
|---|---|---|
| E1 | Behavioral pair-OOS. γ_focal: Σ z² over non-focal pairs. γALL: test_loss median. no-γ: Σ over all 8 pairs | Phase B v6 JSON test_per_pair_medians (re-analysis only, no refit) |
| E2 | Neural OOS. Inverse filter applied to CVD (and HC, see open question §4) → retrain SRM → CVD shared-space disparity post-filter z reduction | `s16_e2_srm_disparity.py` pending direction confirmation |
| E3 | Identifiability. Multi-point sim recovery at candidate as GT (β_c IQR < 30°, recovery median within ±10° of GT) | Round 1 (S08-B/E/S09-A_DPS) and Round 2 (S08-D/S09-C) already; Round 3 needed for new candidates |

### Layer C

§0 LOCO-best demoted to complementary metric only (user explicit override 2026-05-26). Not a primary selector.

---

## 4. Current results (Cycle 10b)

### Sub-08 P2-pass (n=142 of 284) — E1 top (focal + no-γ subset)

| E1 rank | Combo | Model | (β_s, β_c) | median | IQR | E1 score | held-out pairs |
|---|---|---|---|---|---|---|---|
| 1 | γOY,YG,YP\|RDMV2\|noLOCO | 2-comp | (14, −46) | +0.78 | 32.25 | 14.36 | 5 |
| 2 | γOY,YG,YP\|RDMV1+V4\|noLOCO | 2-comp | (50, −36) | +0.77 | 19.82 | 19.62 | 5 |
| 3 | γOY,YG,YP\|RDMV4\|LOCO | 2-comp | (50, −32) | +0.76 | n/a | 19.78 | 5 |
| ... | γYG\|RDMV3\|noLOCO | 2-comp | (46, −38) | −1.39 | 5.02 | 67.16 | 7 |

Advisor flag (open question §5 below): triple γ holds out only 5 pairs, γYG holds out 7. Direct sum comparison unfair. Per-pair mean: triple γ (14.36/5=2.87) still beats γYG (67.16/7=9.60) but by ~3×, not ~5×.

### Sub-09 P2-pass (n=22 of 44) — E1 top

| E1 rank | Combo | Model | params | median | IQR | E1 score |
|---|---|---|---|---|---|---|
| 1 | γGB\|RDMV1\|noLOCO | R+C | g=3.00, Δλ=3 nm (Boehm_low) | −1.86 | 10.96 | 6.83 |
| 2 | γGB\|RDM_\|noLOCO | R+C | g=3.00 | −1.66 | 29.58 | 7.08 |
| 3 | γGB\|RDMV1\|noLOCO | 2-comp | (β_s=2, β_c=24) | −1.52 | **1.41** | 7.77 |

Sub-09 over-comp R+C (g=3.00, Cycle 6 verdict) restored under new lexicographic P2. 2-comp (2, 24) alternate hypothesis with very tight IQR.

---

## 5. Open issues before E2 (advisor 2026-05-26)

### O1. E2 script direction

Current `s16_e2_srm_disparity.py` applies `+δθ` (forward) to both HC and CVD. Advisor: this is *forward simulation*, not filter test. CVD becomes double-distorted → disparity expected to *increase*. The Phase 2 deliverable is an *inverse filter* (stimulus correction): apply `−δθ` to CVD so CVD's distorted perception cancels → CVD shared response approaches HC pool.

Three options:
- (α) Inverse `−δθ` to CVD only; HC baseline = phase2 fixed reference. *Simplest filter test, matches Phase 2 Stage C deliverable*.
- (β) Inverse `−δθ` to both HC and CVD. Matches advisor's original "null control" intent: filter shouldn't move HC if CVD-specific.
- (γ) Keep forward `+δθ` to both (current script). Reframes metric as "forward simulation accuracy", not filter quality.

User's Q4 answer was "(i) forward δθ to HC too — null control" — the *wording* of "null control" implies (β), the *literal δθ direction* implies (γ). Needs disambiguation.

### O2. E1 cross-cell fairness

Triple γ cells hold out 5 pairs (sub-08's *easy* RG-axis pairs); γYG cells hold out 7 pairs (including OY/YP which are sub-08's *hard* yellow pairs). Sum z² has different denominators.

Three fixes:
- Mean z² per held-out pair (simple normalization)
- Baseline-normalized improvement (model z² − null z²) per pair (controls for baseline difficulty)
- Restrict comparison to same held-out count

### O3. E3 still needed

E1+E2 alone cannot catch identifiability disasters like Round 1 β_c IQR=98 for S08-E_v4. E3 multi-point sim at new candidates (sub-08 (14, −46), (50, −36); sub-09 R+C g=3.0, 2-comp (2, 24)) before any primary lock.

### O4. Convergence threshold (user deferred)

User Q3 2026-05-26: "we need to discuss after selecting the decision criteria". Decide after E1+E2+E3 land.

---

## 6. Files

- `DECISION_CRITERIA_2026-05-26.md` — Layer A+B specification (current)
- `scripts/s15_oos_reanalysis.py` — P2 + E1 measurement (no refit)
- `results/oos_reanalysis_v1/{sub-08, sub-09}_e1_p2.json` — E1+P2 output
- `scripts/s16_e2_srm_disparity.py` — E2 (candidate list updated; **direction pending O1**)
- `scripts/cycle6_raw_weight.py` — descriptive only (Cycle 6, double-dip recognized)
- `scripts/cycle7b_srm_diagnostic.py` — SRM diagnostic
