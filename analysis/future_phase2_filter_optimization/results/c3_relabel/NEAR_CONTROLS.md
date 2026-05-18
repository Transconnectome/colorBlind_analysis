# Near-Control Filter Candidates — Records Only (No Viz Retained)

**Date**: 2026-05-17
**Purpose**: Document the per-candidate filter parameters and corrected-P2a screen results for behavioral test design. Viz files removed per cleanup policy 2026-05-17 — only LOCO-canonical (current best) retains 4-col viz.

**Companion docs**: `SCIENTIFIC_NARRATIVE_2026-05-16.md`, `SYNTHESIS_2026-05-16.md`
**Re-generation**: All viz can be re-rendered via `scripts/c3_render_corrected_p2a.py`, `scripts/render_loco_canonical_4col.py`, `scripts/render_rc_2stage_4col.py` if needed.

---

## Selection Framework (2026-05-16)

Per CLAUDE.md §0.1 (P2a-as-screen, REVISED 2026-05-17):
- **HARD threshold**: P2a_filter ≥ P2a_identity → PRIMARY
- **Below identity** → CONTROL (predicted degradation in behavioral test)
- P2a used only as binary gate, not as primary endpoint. Actual paper validation = pre-registered behavioral acquisition.

Per advisor (2026-05-16, 2nd call):
- Filter form: **2-comp standalone** (LOCO-canonical)
- R+C decomposition: diagnostic only (not filter form — falsified by Check 4 + P2a)

---

## Sub-08 deutan (axis 150°) candidates

| Filter | (β_s, β_c) | norm | P2a | exact | Classification | Provenance |
|---|---|---:|---:|---:|---|---|
| **LOCO-canonical** ★ | (38, −14) | 40.5 | **0.750** | 2/8 | **PRIMARY** | V4 LOCO 2-comp fit, perm_p=0.004★★ |
| P2a-max zone min-norm | (24, −22) | 32.6 | 0.750 | 2/8 | PRIMARY (alt) | Behavioral plateau center, smaller norm |
| P2a-max zone V4-aligned | (28, −18) | 33.3 | 0.750 | 2/8 | PRIMARY (alt) | Track A V4 voxRDM landscape rank 237/1586 |
| Identity baseline | (0, 0) | 0.0 | 0.688 | 3/8 | baseline | No filter |
| LIT2Neural Bayesian | (20, +22) | 29.7 | 0.600 | 3/8 | CONTROL | Lit-prior bootstrap; β_c sign conflicts with V4 LOCO |
| R+C 2-stage | (Δλ=2.5, 38, −14) | — | 0.588 | 2/8 | CONTROL | Rejected as filter form (advisor reversal 2026-05-16) |
| Cycle 12 cross-ROI | (68, −38) | 77.9 | 0.750 | 1/8 | CONTROL (extreme) | V4 LOCO + V1 RDM cross loss; norm > 60° |
| Cycle 15 mw_jaccard (✓✓ HC sig) | (68, −38) | 77.9 | 0.750 | 1/8 | CONTROL (extreme) | Only ✓✓ loss; sub-04 outlier dep |
| **Option C** (former CURRENT BEST) | (40, +26) | 47.7 | **0.500** | 2/8 | **CONTROL** | Tikh-heavy; β_c +26 worst-direction. To be deprecated. |

## Sub-09 protan (axis 16°) candidates

| Filter | (β_s, β_c) | norm | P2a | exact | Classification | Provenance |
|---|---|---:|---:|---:|---|---|
| **LOCO-canonical** ★ | (6, −22) | 22.8 | **0.975** | 7/8 | **PRIMARY** | V4 LOCO 2-comp, tied with identity. R+C retinal-dominant prediction confirmed |
| Identity baseline | (0, 0) | 0.0 | 0.975 | 7/8 | baseline (tied PRIMARY) | No filter; viable per R+C |
| Option C (former CURRENT BEST) | (12, −28) | 30.5 | 0.887 | 5/8 | CONTROL | β_c −28 not biologically grounded (Brettel revalidation 2026-05-14) |
| Cycle 14 V1 RDM cross | (32, +22) | 38.8 | 0.825 | 3/8 | CONTROL | V1 RDM cosine +0.29 confirms V1 signal but cortical fit overshoots |
| LIT2Neural | (22, −22) | 31.1 | 0.812 | 6/8 | CONTROL | Lit-prior bootstrap |
| R+C 2-stage | (Δλ=19.5, 0, 0) | — | 0.787 | 4/8 | CONTROL | Rejected as filter form; Machado overshoot at large Δλ |
| Cycle 12 cross-ROI | (30, +26) | 39.7 | 0.700 | 1/8 | CONTROL | V4 LOCO + V1 RDM cross; non-physiological β_c sign |
| Cycle 15 mw_jaccard | (44, +54) | 69.7 | 0.525 | 1/8 | CONTROL (extreme) | sub-04 outlier dep; β_c +54 boundary; strong degradation predicted |

---

## R+C 2-stage Diagnostic (Retained for Paper)

Even though R+C 2-stage filter form rejected (advisor 2026-05-16 2nd call), the standalone R+C decomposition stands as paper finding:

| Subject | Δλ (retinal) | g (cortical gain) | Etiology | Implication |
|---|---:|---:|---|---|
| sub-08 deutan | 2.5 nm | −2.25 (125% overshoot) | **cortical-dominant** | Filter via cortical 2-comp (β large) |
| sub-09 protan | 19.5 nm | −1.10 (Tregillus range) | **retinal-dominant** | Near-physiological cortical compensation; minimal filter benefit |
| sub-10 normal | ~0 | ~0 | null | Perfect control |

**Paper use**: "R+C decomposition localizes the dominant CVD mechanism per subject; the V4 cortical 2-comp filter then captures the cortical-stage signature that remains accessible for stimulus-space correction." (advisor 권고)

---

## Behavioral Test Design Implications (for OSF Pre-Reg)

When all candidates above are presented in the pre-registered behavioral acquisition:

**Sub-08 asymmetric prediction**:
- LOCO-canonical (38, −14) → improvement over identity (large effect predicted)
- Option C (40, +26) → degradation predicted (wrong β_c sign)
- LIT2Neural (20, +22) → degradation
- Identity → baseline
- *Confirmation pattern*: LOCO-canonical > others = framework predictive validity

**Sub-09 asymmetric prediction**:
- LOCO-canonical (6, −22) ≈ Identity (R+C retinal-dominant prediction: no cortical filter needed)
- Option C (12, −28), LIT2Neural (22, −22) → small to moderate degradation
- *Confirmation pattern*: "no-cortical-filter effective" = R+C decomp validity

This asymmetric design is stronger than sham-vs-filter comparison alone.

---

## What Was Removed (2026-05-17 cleanup)

All `CORRECTED_*_4col_*.{png,pdf}` viz files for: OPT1_status_quo, OPT2_lam4, OPT3_drop_topk, OPT6_lam10, V4voxRDM, V2voxRDM_noc5, P2amax_24m22, P2amax_28m18, V1_V4_cc_Bonf, RC_2stage. Also `LOSSREV_*`, `BRIGHTNESS_TRADEOFF`, `sub_*` viz.

**Re-generation if needed**: `python scripts/c3_render_corrected_p2a.py` (regenerates 9 candidates × 2 subjects). All numeric data preserved in `landscapes_consolidated.parquet` and `phase_a_summary.csv`.
