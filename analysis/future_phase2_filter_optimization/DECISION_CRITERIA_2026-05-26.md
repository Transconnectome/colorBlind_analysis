# Decision Criteria — Phase 2 Filter Candidate Evaluation

**Date**: 2026-05-26
**Status**: DRAFT — pending user confirmation on E1 details + threshold layer
**Compliance**: §0 framework honored (no override; selection rule unchanged)

---

## 1. Motivation (recap)

User-stated origin of this sub-project (2026-05-26 message):
> "loss fitting and stable but behavior difference 발생해서 loss 개선이나 판단 기준 개선이 목표"

Translation: candidates fit by Phase B test_loss are *statistically stable*, but the resulting (β_s, β_c) / (Δλ, g) do not match CVD behavior (the user's R+C visualization concern). We therefore need *evaluation criteria* that:

1. Are **train/test separated** (no double-dipping)
2. Show **loss generalizability** (HC subset, pair, model class)
3. Make **behavioral difference visible** (the original motivation)

The Cycle 6 "lowest raw γ_all" criterion failed (1): fit atom = eval atom is tautological.

---

## 2. Framework architecture

Three layers (prerequisite → evidence → selector):

```
┌──────────────────────────────────────────────────────────────┐
│ Layer A: Prerequisites (candidate inclusion / exclusion)      │
│   P1. Fit/Eval atom separation (no double-dip)                │
│   P2. HC-subset robustness (loss-robust; test_loss IQR small) │
└──────────────────────────────────────────────────────────────┘
         ↓ candidates that pass P1+P2 enter Layer B
┌──────────────────────────────────────────────────────────────┐
│ Layer B: Convergence evidence (3 axes, descriptive ranking)   │
│   E1. Behavioral generalize (pair-level)                      │
│   E2. Neural generalize (SRM-disparity-level)                 │
│   E3. Identifiability (synthetic GT recovery)                 │
└──────────────────────────────────────────────────────────────┘
         ↓ convergence label assigned (threshold TBD)
┌──────────────────────────────────────────────────────────────┐
│ Layer C: Primary selector (UNCHANGED, §0 honor)               │
│   LOCO-best descriptive fit + behavioral validation (P2a 보류)│
│   Convergence label provides supporting evidence, not override│
└──────────────────────────────────────────────────────────────┘
```

§0 honored: Layer C primary selector unchanged; Layer B is *descriptive*, not a new selector.

---

## 3. Prerequisites (Layer A)

### P1. Fit/Eval atom separation

**Rule**: an atom used in fit *cannot be the same atom used in evaluation*.

| Fit atom | Valid eval atoms | Invalid (double-dip) |
|---|---|---|
| γ_focal (e.g., γYG, γOY) | non-focal pair z² sum (held-out 7 pairs); SRM disparity; multi-point sim | same focal pair z²; γ_all summed |
| γ_all (8-pair sum) | SRM disparity; multi-point sim; **test_loss IQR if interpreted as HC-normalization robustness check** (user 답 Q2) | γ_all on same subset |
| RDM (PCA / SRM) | γ_focal pair z²; non-focal pairs; multi-point sim; SRM disparity (different ROI than fit ROI) | same RDM atom on same subset |
| LOCO | **NOT a valid fit atom** (within-CVD double-dip — CLAUDE A4) | — |

### P2. HC-subset robustness (loss-robust) — UPDATED 2026-05-26

**Rule (revised)**: candidate's `test_loss` over Phase B HC subset resample (5-train/2-test) is ranked **lexicographically by (median ASC, IQR ASC)**.

**LOCO exclusion from IQR** (user directive 2026-05-26): *"loco is not varying for hc pool so iqr shouldn't be used for loco"*. LOCO atom = within-CVD computation; HC subset resample does not change CVD-internal ridge → IQR≈0 by construction. Using IQR for LOCO cells gives unfair stability advantage.

**Implementation**:
- noLOCO cells: sort key = `(test_loss_median, test_loss_iqr)` lexicographic
- LOCO cells: sort key = `(test_loss_median, +∞)` — IQR replaced by +∞ as tiebreak so LOCO cannot dominate via fake IQR=0
- Top 50% pass P2

**Rationale**: median measures the *direction and magnitude of CVD-HC distinct signal* (negative = CVD significantly below HC pool variance reference, more distinct); IQR measures *HC subset variation robustness*. Median-first ordering aligns with original Phase B selector design (z-score composite primary). The earlier ratio-based proposal (`IQR / |median|`) is withdrawn.

---

## 4. Convergence evidence (Layer B)

### E1. Behavioral generalize (pair-level)

**Goal**: candidate's prediction of *unseen* CVD JND pairs.

| Fit atom type | E1 metric | Source |
|---|---|---|
| γ_focal cells | `Σ z²` over **non-focal pairs** (7 pairs held out from fit) | Phase B v6 JSON `test_per_pair_medians` (re-analysis only, no refit) |
| γALL cells | `test_loss median` (loss-robust ranking; not held-out-pair OOS) | same JSON |
| no-γ cells (RDM/LOCO-only) | `Σ z²` over **all 8 pairs** (none used in fit) | same JSON |

**Per-candidate E1 score**: defined above, lower is better. Convert to within-subject rank.

### E2. Neural generalize (SRM disparity reduction)

**Goal**: candidate's (β_s, β_c) / (Δλ, g) explains the CVD-HC neural distinct signal in SRM shared space.

**Baseline (sub-08 unfiltered)**: V2 z = +2.94, V1 z = +1.79, V4 z = +1.42
**Baseline (sub-09 unfiltered)**: V1 z = +5.17, V4 z = +2.47, V2 z = +1.36

**Procedure** (per candidate):
1. Apply forward δθ to CVD's predicted 8-color amplitudes (per-ROI)
2. Re-run SRM disparity using `rerun_loo_consistent.py`-style HC-only training + fixed-S Procrustes projection of the filtered CVD response
3. Compute post-filter z' = (post_disparity − HC_mean) / HC_std (using the same HC pool mean and std as baseline)
4. **E2 score** = baseline_z − post_filter_z (positive = reduction = better)

**Convention**: per-ROI scores (V1, V2, V4); also a joint "reduction at primary signal ROI" (sub-08 V2 vs sub-09 V1).

**Train/test separation**: HC pool trains SRM; CVD projection is test side. JND data does not enter SRM at any step (Verify 2 confirmed via reading `rerun_loo_consistent.py`).

### E3. Identifiability (multi-point sim)

**Goal**: candidate's (β_s, β_c) can be recovered from synthetic data generated at that GT.

**Procedure** (per candidate): generate synthetic CVD amplitudes at GT = candidate (β_s, β_c) using known HC + 2-comp forward model; refit through full Phase B pipeline; check recovery distribution IQR + median offset from GT.

**Pass**: recovery median ≈ GT (within ±10°) AND recovery IQR < 30° on each axis.

**Already-run**: Round 1 (S08-B + S08-E_v4 + S09-A_DPS); Round 2 (S08-D + S09-C). Need Round 3 for any new candidate from Layer B re-ranking.

---

## 5. Primary selector (Layer C, unchanged per §0)

**Per §0** (CLAUDE.md):
> Filter selection = LOCO-best descriptive fit per subject + behavioral validation.

Layer B convergence evidence *informs* this descriptive selection but does *not* override it.

Practical implication: candidates with strong Layer B convergence but weak LOCO descriptive fit are reported as paper-level findings (e.g., sub-08 2-comp evidence) without replacing the §0 selector output.

---

## 6. Convergence label (threshold — TBD per user Q3)

User-deferred. Candidate options:
- (a) Top-3 in ≥2 of 3 axes AND no FAIL (advisor default; likely 2–3 candidates per subject)
- (b) Top-3 in 3/3 axes (strict; may yield empty set → paper-level "no convergent mechanism for sub-08")
- (c) Top-5 in ≥2 of 3 axes (relaxed)

To be decided after Layer A + B implementation lands actual rank distributions.

---

## 7. Naming (advisor: avoid Cycle 9–13 namespace clash)

Historical Cycle 9–13 = failed selection-rule reformulations. This work is **NOT** a new cycle — it is the **Phase B v6 OOS Re-Analysis** (Layer B descriptive evaluation of existing candidates without refit).

Filename convention: `s15_oos_reanalysis_*.py`, `results/oos_reanalysis_v1/`.

---

## 8. Implementation order

1. **P2 filter**: re-evaluate all v6 cells under HC-subset-robustness threshold; record which cells / candidates excluded
2. **E1 ranking**: re-analysis of v6 `test_per_pair_medians`, no refit; output ranked tables
3. **E2 SRM disparity recompute**: per candidate, forward δθ → CVD predicted amplitudes → SRM disparity z'; ~30 min per ROI per subject
4. **E3 (deferred)**: multi-point sim Round 3 only if new candidate enters from Layer B re-ranking
5. **Convergence label**: assigned only after E1 + E2 land; threshold (Q3) decided then

---

## 9. User answers (locked 2026-05-26)

| Q | Answer | Locked spec |
|---|---|---|
| §0 override | **Explicit override §0**; LOCO-best demoted to *complementary metric only* (user direct quote: "Still E1+E2 should be converged as 'loss generalize' as loss can contain both behav and neural") | Layer B convergence = selector |
| P2 method | **Lexicographic (median ASC, IQR ASC); LOCO IQR ignored** (user: "loco is not varying for hc pool so iqr shouldn't be used for loco") | §3 P2 implementation above |
| γALL E1 | `test_loss median` (loss-robust ranking) | §4 E1 spec |
| E2 baseline | (i) **Apply forward δθ to HC too** — null control; retrain SRM each candidate | §4 E2 spec |
| Convergence threshold | *Deferred*: "we need to discuss after selecting the decision criteria" | TBD after E1+E2 lands |
