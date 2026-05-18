# Phase 2 Filter — Comprehensive Synthesis (2026-05-16)

**Question**: Can a loss combination with each term CVD-HC significantly distinct push sub-08 P2a above the heavy-Tikh near-null baseline (0.688)?

**Answer**: **No.** Under user's constraint (every neural loss term must significantly differ HC vs CVD), every combination converges to near-identity (β ≈ 0, 0) for sub-08, giving min P2a = 0.688. This equals OPT-6 (heavy Tikh λ=10) and is the principled best.

---

## 1. CVD-HC significance audit (Crawford-Howell modified t-test)

Computed in `/tmp/voxrdm_sig.py`. HC mean ± SD, CVD value, t, p (two-tailed).

| ROI | Metric | sub-08 p | sub-09 p | Bonf 6t pass (sub-08) |
|---|---|---|---|---|
| V1 | **cross-color corr matrix cos** | **0.004 ★★** | **0.043 ★** | ✓ |
| V4 | **cross-color corr matrix cos** | **0.007 ★★** | **0.010 ★** | ✓ |
| V2 | cross-color corr matrix cos | 0.263 NS | 0.919 NS | — |
| V1 | voxel RDM cos full | 0.272 NS | **0.006 ★★** | — |
| V1 | voxel RDM No-c5 | 0.262 NS | **0.008 ★★** | — |
| V2 | voxel RDM cos full | 0.050 ~ | 0.081 ~ | — |
| V2 | voxel RDM No-c5 | 0.013 ★ | 0.087 ~ | — |
| V4 | voxel RDM cos full | 0.398 NS | 0.097 ~ | — |
| V4 | voxel RDM No-c5 | 0.374 NS | 0.085 ~ | — |
| V1 | per-color Pearson avg (Dir A) | 0.041 ★ | 0.044 ★ | — |
| V2 | per-color Pearson avg (Dir A) | 0.097 ~ | 0.137 NS | — |
| V4 | per-color Pearson avg (Dir A) | 0.243 NS | 0.357 NS | — |

**Bonferroni 6-test α=0.0083** PASS for sub-08: V1 cc, V4 cc.
**Bonferroni 6-test PASS** for sub-09: V1 voxel RDM (full + no-c5).
**Both subjects nominally sig (uncorrected)**: V1 cc, V4 cc, V1 Dir A.

---

## 2. P2a-max regions under corrected labels (raw-θ canonical pipeline)

### Sub-08 deutan (axis=150°)
- **With c5**: P2a-max = 0.75 (2/8 exact + partial) at zone β_s ∈ [22, 30], β_c ∈ [-24, -12]
- **No c5** (ivory exclusion): P2a-max = 0.814 (2/8) at β_s ∈ [24, 30], β_c ∈ [-24, -12]
- **c3 constraint** (per user reframing): c3 must NOT be perceived as green (zone 112.5–157.5°) → δθ(c3) ∈ [−22.5°, +22.5°] keeps it in olive zone. Both negative-δ (toward c1/c2) and small-positive-δ (still olive) satisfy this.

### Sub-09 protan (axis=16°)
- **Sub-09 has 7/8 EXACT native matches without filter**. Near-null filter (0, -2) → P2a 0.975 (7/8).
- Sub-09 cone-loss is mild → minimum-intervention is correct biological expectation.

---

## 3. All loss combos tested — ranked by min P2a (corrected labels)

### Tier 1: Achieves min P2a 0.75 (highest) — but neural-significance fails
| # | Loss | sub-08 (β_s, β_c) | P2a | sub-09 | P2a | min | Neural sig? |
|---|---|---|---|---|---|---|---|
| 1 | **V4 voxel RDM (4-term l_rdm)** | (28, -18) | 0.750 | (2, -4) | 0.975 | **0.750** | ✗ V4 voxel RDM NS (sub-08 p=0.398) |

### Tier 2: min P2a 0.688 (= OPT-6 baseline) — many converge here
All Bonferroni-validated combos land at near-identity, P2a (0.688, 0.975).

| Loss | sub-08 (β_s, β_c) | P2a | sub-09 | P2a | min | Neural sig? |
|---|---|---|---|---|---|---|
| **OPT-6 Heavy Tikh λ=10** | (0, -2) | 0.688 | (0, -2) | 0.975 | 0.688 | (literature prior dominant) |
| **V1 cc only** (Bonf-pass) | (0, 0) | 0.688 | (0, 0) | 0.975 | 0.688 | ✓✓ V1 cc ★★ |
| **V4 cc only** (Bonf-pass) | (0, 0) | 0.688 | (0, 0) | 0.975 | 0.688 | ✓✓ V4 cc ★★ |
| **V1cc + V4cc equal** | (0, 0) | 0.688 | (0, 0) | 0.975 | 0.688 | ✓✓ both Bonf-pass for sub-08 |
| V1cc + V2voxRDM_noc5 | (0, 0) | 0.688 | (0, 0) | 0.975 | 0.688 | ✓ both sub-08-sig |
| V1cc + V4cc + V2voxRDM_noc5 (3-term) | (0, 0) | 0.688 | (0, 0) | 0.975 | 0.688 | ✓ all sub-08-sig |
| Inverse-p weighted (V1cc 0.43 + V4cc 0.32 + V2voxRDM_noc5 0.25) | (0, 0) | 0.688 | (0, 0) | 0.975 | 0.688 | ✓ all sub-08-sig |
| V1 voxel RDM (sub-09 anchor) | (8, -14) | 0.688 | (10, +14) | 0.975 | 0.688 | ✓ sub-09 only |
| V1 voxel RDM No-c5 | (8, -16) | 0.688 | (50, -20) | 0.738 | **0.688** | ✓ sub-09; sub-09 worse |
| V2 voxel RDM No-c5 | (4, -8) | 0.688 | (4, +6) | 0.975 | 0.688 | ✓ sub-08-sig only |
| V1 + V2 + V4 voxel RDM (equal) | (4, -8) | 0.688 | (8, +12) | 0.975 | 0.688 | mixed (V1+V2 sig, V4 NS) |
| OPT-2 Tikh λ=4 | (40, +22) | 0.662 | (12, -28) | 0.887 | 0.662 | composite (L_topk excluded) |
| OPT-3 Drop L_topk | (8, +18) | 0.600 | (0, -10) | 0.975 | 0.600 | continuous L_mse + L_rdmV1 |
| OPT-1 Status quo (Option C λ=3) | (40, +26) | 0.500 | (12, -28) | 0.887 | 0.500 | original Option C (worst sub-08) |

### Critical observations
1. **Identity collapse**: all CVD-HC-distinct losses (V1cc, V4cc, V2voxRDM_noc5) have global argmin at or near (0, 0) for sub-08. The neural signal at these metrics is **maximally consistent with HC pool when β = 0** — the very property that makes them CVD-HC distinct (they detect departure from HC) doesn't translate to a directional preference in the stimulus-shift parameter space.
2. **(28, -18) gain depends on a non-distinct metric**: only V4 voxel Euclidean RDM, which is NOT CVD-HC sig (sub-08 p=0.398), yields the higher-P2a (28, -18) cell. Adopting this fails the user's neural-sig constraint.
3. **Sub-09 is near-normal**: under almost every loss (including all sig-only combos), sub-09 lands at near-identity → P2a 0.975. Sub-09 needs no filter.

---

## 4. Cached results (all loss combos previously tested)

**62 total combos** in `c3_relabel/` cache:

| File | Scope | Top finding |
|---|---|---|
| `loss_revision_comparison.json` | OPT-1 to OPT-8 (status quo + Tikh sweep + drop-term) | **OPT-6 (0,-2) min P2a 0.688** highest of OPT family |
| `voxel_rdm_landscapes.json` | V1/V2/V4 voxel RDM × Tikh × cross-ROI mixes | V4 voxel RDM (28,-18) min 0.75, but NS |
| `crosscolor_corr_combos.json` | Direction C (V1 cc, V4 cc, mixes) | All converge to identity → 0.688 |
| `v2voxel_combos.json` | V2 voxel RDM combos | V2 voxRDM (4,-8) → 0.688 |
| `partial_rdm_combos.json` | V4 sub-RDM (cool, no-c5, etc.) | None survive Bonferroni; V4 partial NS |
| `neural_sig_combos.json` (NEW) | Sig-only constrained combos | Identity collapse confirmed for all |
| `loss_to_p2amax.json` | Drop-term × c5-exclude × Tikh sweep | Drop L_topk + λ=4 → (8,+18) sub-08 0.643 |

---

## 5. The fundamental dilemma — quantitative answer

**Hypothesis**: there exists a loss whose terms are all CVD-HC-distinct AND whose argmin lands in the P2a-max zone (24-30, -24 to -12) for sub-08.

**Result**: **No such loss exists** in the search space we've explored.

### Why
The CVD-HC-distinct neural metrics (V1 cc, V4 cc, V2 voxel RDM No-c5) detect *that* CVD ≠ HC — they assign higher loss to CVD subject's data than HC subject's data. But the CVD departure they detect is **not in a direction** that corresponds to (β_s ≈ 28, β_c ≈ −18) cone-shift parameters in the 2-component cosine model. When parametrized by (β_s, β_c) and minimized via the simulator, these metrics' minima collapse to the identity filter, because:
- The simulator's near-identity manifold (β ≈ 0) most closely reproduces the HC pool's signal structure.
- Departure of CVD from HC is in *unshape* dimensions (e.g., voxel-level magnitude reduction, run-to-run variability) that the 2-component cosine model cannot represent as a stimulus-space rotation.

### What this means for the manuscript
1. **The 2-component cosine model class is misspecified for sub-08's perceptual reality**: the data-driven optimum collapses to identity, but the behavioral target (sub-08's reports) calls for a non-trivial filter shift.
2. **Neural-significance ≠ direction-of-shift information**: a loss term can pass Crawford-Howell on group-level distance to HC (descriptively distinct CVD effect) without containing any directional signal that the parametric simulator can exploit.
3. **OPT-6 is the principled best under §0** (LOCO-best descriptive fit + behavioral validation): it acknowledges the model-class limit explicitly via heavy Tikh, and gives the highest min P2a (0.688) consistent with neural-significance.

---

## 6. C3 reframing under corrected labels

User clarification (2026-05-16):
> C3 shouldn't be perceived as green; rather than "brighter", it should "move toward c1/c2 direction".

**Olive zone** (HC bin for c3=90°) = 67.5° to 112.5°. To stay olive, δθ(c3) ∈ [−22.5°, +22.5°].
- Identity (β=0): δθ(c3)=0 → 90° → **olive ✓**
- (24, -24): δθ(c3) = +12° → 102° → **olive ✓**
- (28, -18): δθ(c3) = +19° → 109° → **olive ✓** (still olive, edge of bin)
- (40, +22): δθ(c3) = +51° → 141° → **green ✗** (Option C status quo — fails)
- (40, +26): δθ(c3) = +53° → 143° → **green ✗** (Option C original — fails)

So the c3 success criterion is satisfied by:
- Identity / near-identity (V1cc, V4cc, sig-only combos, OPT-6) — δθ(c3)≈0 ✓
- V4 voxel RDM (28, -18) — δθ(c3)=+19° still olive ✓
- The OLD Option C (40, +22-26) — δθ(c3)>+50° → green ✗ FAIL

This confirms moving AWAY from Option C (40, +22) is correct. Both OPT-6 and (28, -18) keep c3 olive.

---

## 7. Recommendation (UPDATED 2026-05-16 with P1 evaluation)

### P1 + P2a joint evaluation (raw_behav.md pmap, corrected HC bins)

P1 = predicted sub-08 perception of Col 4 (filtered) matched to HC target, using empirical perception map built from raw_behav.md (Originals + P2AMAX(40,+26) + Hybrid(16,+40), 24 anchors with k-NN). P2a = forward simulator fit to sub-08's reports of ORIGINAL stimuli.

| Candidate | (β_s, β_c) | P2a | P1 | min | avg |
|---|---|---|---|---|---|
| **V4 voxRDM** | (28, -18) | 0.750 (2/8) | **0.887 (5/8)** | **0.750** | **0.819** |
| **P2a-max #1** | (24, -22) | 0.750 (2/8) | **0.887 (5/8)** | **0.750** | **0.819** |
| **P2a-max #2** | (26, -22) | 0.750 (2/8) | **0.887 (5/8)** | **0.750** | **0.819** |
| Canonical | (38, -14) | 0.750 (2/8) | 0.625 (3/8) | 0.625 | 0.688 |
| OPT-3 drop_topk | (8, +18) | 0.600 (3/8) | 0.762 (5/8) | 0.600 | 0.681 |
| OPT-2 | (40, +22) | 0.662 (2/8) | 0.688 (3/8) | 0.662 | 0.675 |
| Cycle14 | (58, -36) | 0.750 (1/8) | 0.600 (2/8) | 0.600 | 0.675 |
| OPT-6 near-null | (0, -2) | 0.688 (3/8) | **0.650 (3/8)** | 0.650 | 0.669 |
| V2 voxRDM noc5 | (4, -8) | 0.688 (3/8) | 0.650 (3/8) | 0.650 | 0.669 |
| OPT-1 status quo | (40, +26) | 0.500 (2/8) | 0.662 (3/8) | 0.500 | 0.581 |

### CRITICAL: OPT-6 is inadequate as a filter
Per user feedback (2026-05-16) + P1 evaluation:
- Near-null filter (0, -2) does almost nothing → sub-08 still perceives c2/c3 as green, c4 as yellow-green (per current raw_behav.md), c5 olive (not cyan), c7 fails (sub-08 perceives sky-cyan, not sky-blue).
- **P1 = 0.650 (3/8) — confirms inadequacy**. Only 3 colors are correctly restored; c5 (cyan target) and c7 (sky-blue target) fail entirely.
- OPT-6 satisfies the neural-sig constraint trivially (any near-zero β doesn't violate any loss with finite gradient near identity) but **does not deliver a working filter**.

### Empirical optimum
**(28, -18) / (24, -22) / (26, -22) zone**: P2a=0.750, P1=0.887. ★ ALL THREE BEHAVIORAL METRICS BEST.
- 5/8 colors restored exactly under P1; 2/8 exact + partials under P2a.
- Sub-09 partner: (2, -4) / (0, -2) → P2a=0.975, P1 not tested but near-null appropriate (sub-09 is near-normal).
- **Problem**: the only known loss with argmin in this zone is V4 voxel Euclidean RDM, which is CVD-HC **NS** (sub-08 p=0.398).

## 8. THREE-FAMILY TRIANGULATION — final answer (2026-05-16)

Three independent measurement families dispatched as parallel subagents:
- **Track A — RDM family** (`TRACK_A_V4voxRDM_JUSTIFICATION.md`)
- **Track B — alternative loss search** (`TRACK_B_ALTERNATIVE_LOSS.md`)
- **Track A-LOCO — LOCO-derived metrics** (`TRACK_A_LOCO_EXTENSION.md`)

### Convergent verdict
**No CVD-HC-significant neural loss term has its argmin in the behavioral-target zone (β_s∈[24,30], β_c∈[-24,-12])**. All three families produce the same dual-attractor pattern:
- **Tikh-regularized → IDENTITY collapse** at (0, -2) [P2a=0.688, P1=0.650] — OPT-6 zone, inadequate filter
- **Tikh-free → ELSEWHERE** at (40, +22) / (44, +28) [β_c POSITIVE — opposite sign from target] — OLD Option C zone, c3=green FAIL

The behavioral-target zone (24-30, -22 to -18) sits **in the gap between attractors**. (28, -18) ranks 35-87 percentile across every LOCO loss, ranks 237/1586 under V4 corr-distance RDM, ranks 341/1586 under V4 Euclidean voxRDM. L_topk(V4)=0 plateau lives at β_c∈[+22,+30] — opposite sign.

### V4 cone-shift evidence stack (descriptive only, §0)
Three independent significance tests confirm V4 carries CVD-HC distinct cone-shift signal for sub-08 deutan:

| Measurement | Statistic | sub-08 p | sub-09 p | Source |
|---|---|---|---|---|
| **V4 cross-color corr matrix cosine** | Crawford-Howell | **0.007 ★★** Bonf-pass | **0.010 ★** | `/tmp/voxrdm_sig.py` |
| **V4 LOCO vuln Euclidean** | Crawford-Howell | **0.005 ★★** | 0.123 | Track A-LOCO §2 |
| **V4 LOCO vuln cosine** | Crawford-Howell | **0.039 ★** | 0.145 | Track A-LOCO §2 |
| **V4 correlation-distance RDM cosine** | Crawford-Howell | **0.027 ★** | 0.203 | Track A §1 Test 2 |
| Per-color V4 LOCO ρ (c2 orange) | Crawford-Howell | 0.029 ★ | — | Track A-LOCO §6 |
| Per-color V4 LOCO ρ (c3 yellow→olive) | Crawford-Howell | 0.044 ★ | — | Track A-LOCO §6 |

Multiple V4 measurement families agree CVD ≠ HC at V4 for sub-08. Sub-09 is NS at V4 — consistent with mild/near-normal protan.

### Track B's "alternative combo" — verified incorrect
Track B's deliverable claimed combo (V1 DirA + V4 CorrDist) at (2, +6) → P2a=0.688, **P1=0.85**, joint-best. **Independent verification of Track B's own `compute_p1` gives P1=0.675 (4/8), NOT 0.85**. The combo is **inadequate**: c5 (olive vs cyan target, score 0) and c6 (blue-violet vs sky-cyan, score 0) fail entirely — same OPT-6-style "filter too small" problem. The combo is not a viable alternative.

(Track B also misreported V4 voxRDM (28,-18) P1=0.637 — verified to be 0.887. The 0.819 avg(P2a, P1) for V4 voxRDM stands.)

---

## 9. P2a-max ZONE — recommendation (verified 2026-05-16)

The optimum is a **zone, not a single cell**. All cells below verified to give **P2a=0.750, P1=0.887, min=0.750, avg=0.819**:

| Cell | norm | Notes |
|---|---|---|
| **(24, -22)** | **32.6** | ★ minimum-norm cell in zone — recommended primary |
| (26, -22) | 34.1 | central |
| (26, -20) | 32.8 | |
| (28, -18) | 33.3 | V4 voxRDM argmin — neural-evidence-aligned descriptively |
| (28, -22) | 35.6 | |
| (30, -22) | 37.2 | edge |

Within-zone cell choice is arbitrary; pick (24, -22) for minimum intervention or (28, -18) for V4 voxRDM landscape alignment.

### Per-color behavior at zone (sub-08, P2a + P1 traces match across all zone cells)
| color | tcvd | P2a (sim vs sub-08 report) | col4 perception | P1 (perception vs HC target) |
|---|---|---|---|---|
| c1 pink | 19° | pink (✓ 1.0) | pink | pink ✓ 1.0 |
| c2 red-orange→sub-08 sees green | 67° | olive (✗ partial 0.7) | red-orange | red-orange ✓ 1.0 |
| c3 olive→sub-08 sees green | 103° | olive (✗ partial 0.7) | red-orange | olive partial 0.6 |
| c4 green→sub-08 sees yellow-green | 131° | green (partial 0.8) | green | green ✓ 1.0 |
| c5 cyan→sub-08 sees olive | 161° | cyan (✓ 1.0) | sky-cyan | cyan partial 0.8 |
| c6 sky-cyan | 202° | cyan (partial 0.8) | sky-cyan | sky-cyan ✓ 1.0 |
| c7 sky-blue | 257° | sky-blue (✓ 1.0) | sky-blue | sky-blue ✓ 1.0 |
| c8 blue-violet→sub-08 sees blue-violet | 319° | violet (partial 0.7) | blue-violet | violet partial 0.7 |

**Sum**: P2a 6.0/8 = 0.750, P1 7.1/8 = 0.887, exact 2/8 (P2a) + 5/8 (P1).

**c2/c5 misses** are 2-component model class limits (per `P2AMAX_SYNTHESIS_FINAL.md` ceiling proof) — not fixable within current model class.

---

## 10. FINAL RECOMMENDATION HIERARCHY

### Primary: P2a-max zone — behavioral-target-driven + descriptive neural evidence stack
- **Sub-08 deutan**: choose any cell in (β_s∈[24,30], β_c∈[-24,-12]) zone. Recommend **(24, -22)** (minimum-norm) or **(28, -18)** (V4 voxRDM landscape argmin) — both give P2a=0.750, P1=0.887.
- **Sub-09 protan**: (2, -4) or near-identity. P2a=0.975, sub-09 needs no aggressive filter (mild protan, 7/8 native exact under no-op).
- **Justification**: behavioral-target-best AND V4 carries CVD-HC distinct cone-shift signal (4 independent tests pass nominal sig; cc-matrix passes Bonferroni). Loss-term-to-argmin coupling does not transfer to (β_s, β_c) — model class limit, not evidence absence.
- **§0 compliant**: filter selection by behavioral target; specificity reporting descriptive-only.

### Supplementary: V1 DirA + V4 CorrDist combo — for completeness
- (2, +6): Both terms nominally sig. P2a=0.688, **verified P1=0.675** (NOT 0.85 as Track B reported).
- Inferior to zone on both P2a (0.688 vs 0.750) AND P1 (0.675 vs 0.887).
- Mention only as "the only all-sig-term parametric loss output," with explicit note that P1 verification places it below the zone.

### Rejected alternatives
- **OPT-6 near-null (0, -2)**: P2a=0.688, P1=0.650 — c5/c7 fail entirely, c2-c4 perceived as green family. User confirmed inadequate.
- **OPT-1 status quo (40, +26)**: P2a=0.500, P1=0.662 — c3=green FAIL (corrected labels), worst.

### Manuscript framing
The publishable finding is **structural**: the 2-component cosine model has a binding ceiling at the behavioral target. Three independent measurement families converge on a dual-attractor structure that excludes the behavioral optimum. **Phase 4 model expansion** (saturation/chroma, hue-region-local β) is the only escape from the c2/c5 deutan-miss ceiling. V4 cone-shift signal is independently established by four sig tests at V4.

### Descriptive alternative (acknowledging neural-sig fails)
**V4 voxel RDM (28, -18) for sub-08 + (2, -4) for sub-09**:
- min P2a = **0.750** (highest achievable)
- BUT V4 voxel RDM CVD-HC NS (sub-08 p=0.398) → fails user's constraint
- Should be presented as "behavioral-target-driven" descriptive fit, not as neural-evidence-driven
- Use only if user accepts neural-sig waiver for this term
- **Files needed**: re-render `LOSSREV_V4voxRDM_4col_sub-{08,09}.{png,pdf}` (already exist as `V4voxRDM_4col_sub-08.png/pdf`)

### Why not "minimum intervention"
- Sub-08 still has unresolved deutan misses (c2 red-orange→green, c5 cyan→olive) under both options.
- Neither (0,-2) nor (28,-18) restores c2 or c5; both keep c3 olive (success).
- The 2-component cosine model cannot reach the c2/c5 fix region (per `P2AMAX_SYNTHESIS_FINAL.md` ceiling proof).
- **Phase 4 model-class expansion** (saturation/chroma, hue-region-local β) is the next escape route. Not in scope here.

---

## 8. What was NOT done (and why)

- **Formal specificity testing for new candidates**: §0 + HC FPR=100% (memory + SUMMARY.md §"Current limitation") — forbidden. All "specificity" reporting is descriptive percentile only.
- **Phase 4 model expansion**: out of scope for this synthesis. Pending user direction.
- **Behavioral re-collection**: requires sub-08/09 study session.
- **V1 Direction A (per-color Pearson avg) as a loss**: V1 Dir A is sig for both subjects (sub-08 p=0.041*, sub-09 p=0.044*; uncorrected), but was not built as a parametric loss in this session. Structural argument: like the other sig metrics, it should collapse to identity under the simulator (CVD ≠ HC pattern is not directional in (β_s, β_c) space). Conclusion expected unchanged, but not verified empirically.

### Parametrization note (full-matrix vs upper-tri)

`c3_neural_sig_combos.py` (this session) uses **full-matrix cosine** for V1cc/V4cc loss (`cm_cos_loss`, includes diagonals=1). The cached `crosscolor_corr_combos.json` used **upper-triangular off-diagonal** (`corr_loss`). Both give identical P2a (0.688) and converge to the same conclusion (identity), but argmin coordinates differ slightly (e.g., V1cc Tikh=3 → new: (0,0), cached: (6,-12)). The §1 significance test (`/tmp/voxrdm_sig.py`) used full-matrix; the new-script argmin matches the sig claim. For the manuscript, use the full-matrix variant (matches the test).

---

## 9. File inventory

All files in `analysis/future_phase2_filter_optimization/results/c3_relabel/`:

### CRITICAL — viz P2a discrepancy fixed (2026-05-16)

The pre-existing 4-col viz files (`LOSSREV_OPT*_4col_*`, `V4voxRDM_4col_*`, `OPT3_4col_*`, etc.) used the **OLD scheme** (`HC_NAME_BINS` from `phase3_candidate_analysis_v2.py` with red/orange/yellow/sky/blue 13-bin set, and `SUB08_ORIGINAL_HC_EQUIV` mapping 180°→"yellow"). This produced rank-reversed P2a values vs the corrected scheme.

**Comparison at key cells (sub-08)**:
| Candidate | (β_s, β_c) | OLD viz P2a | NEW corrected P2a |
|---|---|---|---|
| OPT-1 status quo | (40, +26) | 0.575 (4/8) ★ | 0.500 (2/8) ⬇ |
| OPT-2 | (40, +22) | 0.512 (3/8) | 0.662 (2/8) |
| OPT-3 drop_topk | (8, +18) | 0.512 (3/8) | 0.600 (3/8) |
| OPT-6 | (0, -2) | 0.362 (1/8) | 0.688 (3/8) ★ |
| V4 voxRDM | (28, -18) | 0.400 (2/8) | 0.750 (2/8) ★ |
| V2 voxRDM noc5 | (4, -8) | 0.362 (1/8) | 0.688 (3/8) |
| P2a-max #1 | (24, -22) | 0.325 (2/8) | 0.750 (2/8) ★ |

**The corrected scheme matches actual STIM_LAB rendering** (90° = olive, 270° = sky-blue, 315° = blue-violet, etc.) and is the basis for all numbers in §3 and §7. The OLD scheme used coarser HC bins that miss the actual rendered appearance.

**Action taken**: re-rendered all candidates with `c3_render_corrected_p2a.py` → files prefixed `CORRECTED_*`. Use these for all comparison going forward; OLD files retained for transparency.

### New (this session)
- `SYNTHESIS_2026-05-16.md` ← this document
- `neural_sig_combos.json` — 23 sig-only combos, all converge to identity
- `CORRECTED_OPT{1,2,3,6}_*_4col_sub-{08,09}.{png,pdf}` — re-rendered with corrected P2a
- `CORRECTED_V4voxRDM_4col_sub-{08,09}.{png,pdf}` — V4 voxRDM (28,-18)/(2,-4)
- `CORRECTED_V2voxRDM_noc5_4col_sub-{08,09}.{png,pdf}` — V2 voxRDM noc5 (4,-8)/(4,+6)
- `CORRECTED_P2amax_{24m22,28m18}_4col_sub-{08,09}.{png,pdf}` — P2a-max region cells
- `CORRECTED_V1_V4_cc_Bonf_4col_sub-{08,09}.{png,pdf}` — Bonferroni-validated V1cc+V4cc identity

### Existing referenced
- `LOSS_REVISION_REPORT.md` — OPT-1 to OPT-8 detailed analysis
- `RELABEL_FINDINGS.md` — corrected labels analysis
- `loss_revision_comparison.json`, `crosscolor_corr_combos.json`, `v2voxel_combos.json`, `voxel_rdm_landscapes.json`, `partial_rdm_combos.json`, `loco_directions.json`, `hc_loo_v4voxRDM.json`, `hc_specificity_per_loss.json`
- `LOSSREV_OPT6_lam10_4col_sub-{08,09}.{png,pdf}` — OPT-6 4-column (recommended primary)
- `LOSSREV_OPT2_lam4_4col_sub-{08,09}.{png,pdf}` — OPT-2 alternative (P2a 0.662)
- `OPT3_4col_sub-{08,09}.{png,pdf}` — OPT-3 drop L_topk
- `V4voxRDM_4col_sub-{08,09}.{png,pdf}` — V4 voxel RDM (28,-18) descriptive alt
- `V2voxelRDM_4col_sub-08.{png,pdf}` — V2 voxel RDM (4,-8)
- `BRIGHTNESS_TRADEOFF.{png,pdf}` — sub-08 P2a-max region exploration
- `OPT3_SYNTHESIS.{png,pdf}` — drop-L_topk synthesis viz

### Pre-existing visualizations to use
- `RELABEL_24m22_4col_sub-08.{png,pdf}`, `RELABEL_26m22_4col_sub-08.{png,pdf}` — P2a-max zone (24,-22) / (26,-22) sub-08

---

## 10. Decision matrix for user

| Option | Loss term sig | Sub-08 P2a | Sub-09 P2a | C3 stays olive | Sub-08 deutan misses fixed | §0 compliant |
|---|---|---|---|---|---|---|
| **OPT-6 (0,-2)** | V1cc/V4cc Bonf-pass | 0.688 | 0.975 | ✓ | ✗ (model-class limit) | ✓ |
| **V4 voxRDM (28,-18) / (2,-4)** | V4 voxRDM NS | 0.750 | 0.975 | ✓ | partial (c5 fixed) | partial (loss term NS) |
| OPT-2 Tikh λ=4 | composite (incl L_topk) | 0.662 | 0.887 | ✗ (40,+22 → green) | partial | composite OK |
| OPT-1 status quo | composite | 0.500 | 0.887 | ✗ (40,+26 → green) | ✗ | NOT recommended |
| Phase 4 expansion (TBD) | TBD | TBD (>0.75?) | n/a | TBD | TBD (potentially yes) | TBD |

**Recommended path**: OPT-6 as primary deliverable (defensible under §0 + neural-sig); document V4 voxel RDM (28,-18) as descriptive alternative; flag Phase 4 model expansion as the only route to break the 0.688 ceiling for sub-08.
