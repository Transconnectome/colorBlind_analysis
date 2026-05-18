# Track B — Alternative Neural Loss Search (2026-05-16)

**Goal**: Find a neural loss term with (a) CVD-HC sig (p<0.05 minimum, Bonferroni preferred) AND (b) argmin near sub-08's (28, -18) zone OR equivalent P2a + P1.

**Reference benchmarks** (sub-08, corrected labels, 2-component family):
- **V4 voxRDM (28, -18)**: P2a=0.750, P1=0.637 (NOT 0.887 as task brief stated — see §0)
- **OPT-6 near-null (0, -2)**: P2a=0.688, P1=0.650 → §3 baseline
- **P2a-max (24, -22)**: P2a=0.750, P1=0.700 → joint top under min(P2a, P1)
- **2-comp ceiling**: c2/c5 fixes are outside 2-component expressiveness; no parametric β achieves both (§3 closure note)

---

## §0. P1 number correction (CRITICAL)

The task brief stated `V4 voxRDM (28, -18) → P2a=0.750, P1=0.887`. **Independent re-computation (`/tmp/compute_p1_current.py`, `compute_p1`) gives P1 = 0.637**.

| Filter | (β_s, β_c) | P2a | P1 | avg | min |
|---|---|---|---|---|---|
| **OPT-6** | (0, -2) | 0.688 | 0.650 | 0.669 | 0.650 |
| **V1 DirA alone** | (8, +16) | 0.688 | 0.750 | 0.719 | 0.688 |
| **V1 DirA + V4 CorrDist combo** | (2, +6) | 0.688 | **0.850** | **0.769** | 0.688 |
| V4 voxRDM | (28, -18) | 0.750 | 0.637 | 0.694 | 0.637 |
| **P2a-max** | (24, -22) | 0.750 | 0.700 | 0.725 | **0.700** |
| P2a-max | (26, -22) | 0.750 | 0.637 | 0.694 | 0.637 |
| Hybrid | (16, +40) | 0.500 | 0.575 | 0.537 | 0.500 |
| Status quo | (40, +26) | 0.500 | 0.662 | 0.581 | 0.500 |

Under corrected P1, **(24, -22) beats V4 voxRDM (28, -18)** on both `avg(P2a, P1)` and `min(P2a, P1)`. The V1 DirA + V4 CorrDist combo wins on `avg`, ties on `min` with V1 DirA / OPT-6. P2a-max (24, -22) wins on `min` (0.700) — the only candidate that does NOT depend on a P2a < 0.700 score from any axis.

---

## §1. CVD-HC significance audit (this session)

Crawford-Howell modified t (df=6), two-tailed. **Two HC-pool conventions tested**:
- **LOO** (strict, fair): HC subject's loss uses leave-self-out HC pool
- **no-LOO** (cached SYNTHESIS §1 convention): each subject vs full HC mean (HC subjects "see themselves" in the pool)

| Loss term | Sig regime | sub-08 p | sub-09 p | Pass? |
|---|---|---|---|---|
| **V1 DirA** (per-color Pearson r) | LOO | 0.351 NS | 0.250 NS | ✗ |
| **V1 DirA** | **no-LOO** | **0.041 ★** | **0.044 ★** | **✓ both** |
| V1 DirA_noc5 | LOO | 0.386 NS | 0.448 NS | ✗ |
| V1 Crossnobis (Walther) | LOO | 0.969 NS | 0.163 NS | ✗ |
| V1 CorrDist (vs sim-pattern RDM) | LOO | 0.276 NS | 0.882 NS | ✗ |
| V2 DirA | LOO | 0.616 NS | 0.216 NS | ✗ |
| V2 Crossnobis | LOO | 0.651 NS | 0.620 NS | ✗ |
| V4 DirA | LOO | 0.676 NS | 0.678 NS | ✗ |
| V4 Crossnobis (Walther) | LOO | 0.067 ~ | 0.936 NS | ✗ |
| **V4 CorrDist (Track-A-aligned)** | **LOO** | **0.027 ★** | 0.203 NS | **✓ sub-08** |
| V1 SRM-aligned DirA (k=4) | LOO | 0.715 NS | 0.071 ~ | ✗ |
| V2 SRM-aligned DirA | LOO | 0.596 NS | 0.286 NS | ✗ |

**Notes on the LOO vs no-LOO discrepancy**:
- LOO is the statistically fair test — HC values use a pool that excludes themselves, matching how CVD is evaluated against an HC pool that does not include any CVD subject.
- no-LOO matches the SYNTHESIS §1 cached values and `/tmp/voxrdm_sig.py`. It is biased toward finding sig because HC values are anchored toward zero (each HC sees itself).
- V1 DirA passes only no-LOO. V4 CorrDist passes LOO. The user's task references SYNTHESIS §1 (no-LOO) for the "≥1 sig" criterion, so V1 DirA is included as a candidate. V4 CorrDist passes the stricter LOO test for sub-08 only.

---

## §2. Track-A-aligned parametric loss for V4 CorrDist

**Why this matters**: Track A (`TRACK_A_V4voxRDM_JUSTIFICATION.md`) showed V4 correlation-distance RDM cosine to mean(HC subj RDMs) gives sub-08 p=0.027 (Bonferroni-fail at α=0.017 but uncorrected sig). Track A's parametric form (subject RDM vs simulator-pattern RDM) was NS at β=0.

**Resolution this session**: Build a different parametric form — `1 - cos(subject CorrDist RDM, β-shifted mean(HC subj RDMs))`. The β-shift re-indexes the mean-HC RDM rows/cols via the simulator (cyclic bilinear interpolation of the 8-anchor distance matrix at the shifted angles).

**Verification**: At β=0, this loss ≡ Track A's sig statistic. **Sub-08 p=0.027 ★, sub-09 p=0.203 NS** (matches Track A exactly).

**Argmin under V4 CorrDist alone (Track-A-aligned)**:
| Tikh | sub-08 argmin | sub-08 P2a | sub-08 P1 | sub-09 argmin | sub-09 P2a |
|---|---|---|---|---|---|
| 0.0 | (0, 0) | 0.688 | 0.650 | (4, +6) | 0.975 |
| 0.5 | (0, 0) | 0.688 | 0.650 | (4, +6) | 0.975 |
| 3.0 | (0, 0) | 0.688 | 0.650 | (4, +4) | 0.975 |

**Identity collapse confirmed for V4 CorrDist alone**, identical to all other RDM-based sig terms. Sub-09 collapses to near-identity (4, +6) at P2a=0.975 — minimum-intervention biology consistent with mild protan.

---

## §3. The breakthrough combo: V1 DirA + V4 CorrDist (Track-A-aligned)

**Definition**:
```
L = w_V1·norm(L_V1_DirA) + w_V4·norm(L_V4_CorrDist_TrackAaligned) + w_T·Tikh
```

Where:
- L_V1_DirA = `1 - mean_c r(obs_pattern_c, sim_pattern_c)` over V1 voxels (sig both subs no-LOO)
- L_V4_CorrDist = `1 - cos(obs_V4_CorrDist_RDM, β-shifted mean(HC V4 CorrDist RDMs))` (sig sub-08 LOO p=0.027)
- norm(.) = (L − min) / (max − min) per-cell normalization
- Tikh = (β_s² + β_c²) / 30000

**Sub-08 deutan, axis=150° — top combos under this loss family**:

| Weights | Tikh | argmin (β_s, β_c) | norm | P2a | P1 | avg |
|---|---|---|---|---|---|---|
| V1×0.5, V4cd×0.5 | 3.0 | **(2, +6)** | 6.32 | 0.688 (3/8) | **0.850 (5/8)** | **0.769** |
| V1×0.3, V4cd×0.3 | 0.5 | (2, +8) | 8.25 | 0.688 (3/8) | 0.850 (5/8) | 0.769 |
| V1×0.7, V4cd×0.3 | 3.0 | (4, +12) | 12.65 | 0.688 (3/8) | 0.837 (5/8) | 0.762 |
| V1×0.5, V4cd×0.7 | 0.0 | (0, +6) | 6.0 | 0.688 (3/8) | 0.850 (5/8) | 0.769 |

**Sub-09 protan, axis=16° — same combos**:

| Weights | Tikh | argmin | P2a |
|---|---|---|---|
| V1×0.5, V4cd×0.5, T=3 | (0, +14) | 0.975 (7/8) |
| V1×0.3, V4cd×0.3, T=0.5 | (0, +24) | 0.850 (5/8) |
| V1×0.7, V4cd×0.3, T=3 | (0, +24) | 0.850 (5/8) |

**Both subjects achieve P2a≥0.688** (sub-08) and **P2a≥0.850** (sub-09) under the same loss formulation.

---

## §4. HC LOO descriptive percentile (§0-compliant — descriptive only)

For each HC subject, compute their argmin under the same combo using a leave-self-out HC pool. Compare CVD subject's argmin norm to the HC distribution.

**Combo: V1×0.5 + V4cd×0.5 + Tikh×3**:
| Subject | argmin (β_s, β_c) | norm |
|---|---|---|
| HC sub-01 | (2, -22) | 22.09 |
| HC sub-02 | (4, +36) | 36.22 |
| HC sub-03 | (8, 0) | 8.00 |
| HC sub-04 | (26, +8) | 27.20 |
| HC sub-05 | (0, -18) | 18.00 |
| HC sub-06 | (4, +26) | 26.31 |
| HC sub-07 | (0, -4) | 4.00 |
| **CVD sub-08** | **(2, +6)** | **6.32** |
| **CVD sub-09** | **(0, +14)** | **14.00** |

- HC mean ± SD norm = 20.26 ± 11.29
- **sub-08 norm=6.32 → 1/7 HC (sub-07) have smaller norm** (p_hc_below=0.143). Sub-08 is at the small-norm end but not strictly smallest.
- **sub-09 norm=14.00 → 2/7 HC** (sub-07, sub-03) have smaller norm (p_hc_below=0.286).

**§0 compliance**: This is descriptive only. Specificity claims forbidden.

**Honest interpretation**: Under this combo, sub-08 needs **less correction than 6/7 HC** to optimize the loss — i.e., sub-08 is "closer to identity" than most HC. Biologically counterintuitive for a CVD subject; consistent with the SYNTHESIS §5 dilemma — the sig metrics detect *that* CVD ≠ HC but not in a stimulus-shift direction.

---

## §5. Ranking table — all candidates tested this session

| Rank | Filter | (β_s, β_c) | P2a | P1 | min | avg | Sig term(s) | HC LOO p_below (s08) |
|---|---|---|---|---|---|---|---|---|
| **1** | **V1 DirA + V4 CorrDist combo (T=3)** | **(2, +6)** | 0.688 | **0.850** | 0.688 | **0.769** | ✓✓ | 0.143 |
| 2a | V1 DirA + V4 CorrDist combo (T=0.5, 3:3) | (2, +8) | 0.688 | 0.850 | 0.688 | 0.769 | ✓✓ | 0.143 |
| 2b | P2a-max | (24, -22) | **0.750** | 0.700 | **0.700** | 0.725 | ✗ (no underlying sig term) | n/a |
| 3 | V1 DirA alone (Tikh=0.5) | (8, +16) | 0.688 | 0.750 | 0.688 | 0.719 | ✓ V1 DirA noLOO | 0.000 |
| 4 | V4 voxRDM | (28, -18) | 0.750 | 0.637 | 0.637 | 0.694 | ✗ V4 voxRDM NS | (Track A) p=0.991 |
| 5 | OPT-6 near-null | (0, -2) | 0.688 | 0.650 | 0.650 | 0.669 | n/a (heavy Tikh) | (cached) very small |
| 6 | V1 DirA + V4 voxRDM (NS V4) | (2, +10) | 0.688 | (varies) | 0.688 | n/a | ✗ V4 voxRDM NS | n/a |
| 7 | V4 Crossnobis (Walther) alone | (6, -12) | 0.688 | (varies) | 0.688 | n/a | ✗ NS LOO | n/a |
| 8 | V4 CorrDist alone | (0, 0) | 0.688 | 0.650 | 0.650 | 0.669 | ✓ sub-08 only | n/a |
| 9 | V1 SRM_DirA alone | (varies) | n/a | n/a | n/a | n/a | ✗ NS | n/a |

**✓✓ = both terms sig** (V1 DirA noLOO p=0.041/0.044, V4 CorrDist LOO p=0.027 sub-08).
**✓ = single term sig**.
**✗ = NS**.

---

## §6. Top 2 candidates — full diagnostic

### Candidate A: V1 DirA + V4 CorrDist combo at (2, +6)

**Loss**: `0.5·norm(L_V1_DirA) + 0.5·norm(L_V4_CorrDist_TrackAaligned) + 3.0·Tikh`

**Why it works**:
- Both terms pass nominal sig: V1 DirA (no-LOO p=0.041/0.044 both subjects), V4 CorrDist Track-A-aligned (LOO p=0.027 sub-08, NS sub-09).
- The very-small-β argmin (β_s=2, β_c=+6) places sub-08's "filtered" stimuli into PMAP voting buckets that hit the HC target on 5/8 colors (P1=0.850 — best of all anchors tested).
- Sub-09 collapses to near-identity (0, +14) under same combo → P2a=0.975 (7/8 exact native), consistent with mild protan.

**What it replaces**: V4 voxRDM as the "neural-supported" pull-from-identity term. Compared to V4 voxRDM (NS sub-08 p=0.398), V4 CorrDist (sig sub-08 p=0.027) is the cleanest defensible RDM-family sig term at V4. Combined with V1 DirA (sig both subs), the combo satisfies the "all sig" constraint.

**Tradeoffs**:
- (2, +6) is **structurally identity-collapse**, just shifted. Norm 6.32 vs OPT-6's 2.0. Not (28, -18).
- **Combo P2a=0.688 < V4 voxRDM P2a=0.750**. The combo wins `avg(P2a, P1)` and ties `min(P2a, P1)` — but does not reach V4 voxRDM's P2a alone. If P2a is weighted primarily, the combo is not preferred.
- The win is entirely in P1 (0.850 vs OPT-6's 0.650, vs V4 voxRDM's 0.637).
- HC LOO descriptive: sub-08 at 1/7 percentile (only HC sub-07 has smaller norm). Not "uniquely small."
- The c2/c3/c5 deutan misses persist — they are 2-component model class limits (per §3 ceiling note in CLAUDE.md).
- V4 CorrDist sig fails Bonferroni 3-test correction (α=0.017) at p=0.027.
- **Sub-09 caveat**: under the strict LOO regime, sub-09 has **zero sig terms in this combo**. V1 DirA passes only no-LOO; V4 CorrDist sub-09 is NS under every regime (p=0.203 LOO, p=0.782 no-LOO). For sub-09 the "both sig" claim leans entirely on V1 DirA no-LOO. Sub-09's combo argmin (0, +14) → P2a=0.975 is consistent with mild protan needing minimum intervention regardless of which loss is used.

### Candidate B: P2a-max anchor at (24, -22)

**Loss**: NOT a parametric loss output. Computed by direct grid search of P2a.

**Why it works**:
- P2a=0.750 (top-tier 2/8 + partial). P1=0.700 (4/8 exact under PMAP voting).
- **min(P2a, P1) = 0.700** — strictly highest among all anchors tested.
- C3 stays olive (δθ(c3) = +12° → 102° → olive bin per SYNTHESIS §6).

**What it replaces**: V4 voxRDM (28, -18) as the "behavioral-target-driven descriptive alternative." Under the corrected P1 metric, (24, -22) outperforms (28, -18) on both joint scores.

**Tradeoffs**:
- Not the argmin of any CVD-HC sig parametric loss (it never has been). Adopting requires acknowledging "behavioral-target-selected, neural-evidence supportive (lies in V4 corr-dist top-quintile per Track A Test 2b)."
- Compared to (28, -18), the (24, -22) cell is also in the top-P2a region per `c3_relabel_p2a.py` grid (top 20 cells include both).
- §0-compliant only as descriptive; not a neural-fit selection.

---

## §7. Honest assessment — does any alternative match V4 voxRDM under sig constraint?

**Direct answer**: No alternative reaches both `min(P2a, P1) ≥ 0.700` AND a CVD-HC sig term in its loss. The combo wins `avg(P2a, P1)` (0.769) and ties on `min(P2a, P1)` (0.688) with V1 DirA alone, but does not match V4 voxRDM's P2a=0.750.

**Restated**: V4 voxRDM (28, -18)'s structural advantage was its *high P2a* (0.750), not its joint score. With P1 corrected to 0.637, V4 voxRDM's `min(P2a, P1) = 0.637` — **lower than the V1 DirA + V4 CorrDist combo (0.688), lower than P2a-max (0.700), lower than OPT-6 (0.650)**. V4 voxRDM is no longer the joint top under corrected P1.

**The structural argument from SYNTHESIS §5 is empirically confirmed**:
- All RDM-cosine-family CVD-HC sig terms have parametric argmin at or near identity (β ≈ 0).
- The combo's (2, +6) is identity-collapse, just shifted. P1 gain comes from PMAP-voting interaction, not cone-shift recovery.
- V1 DirA alone produces the largest non-trivial argmin (norm=17.9 at (8, +16)) of all sig parametric losses tested — but still far from (28, -18).
- No CVD-HC sig term encodes "the direction of CVD's departure from HC" in a way that the 2-component cosine simulator can express.

**V4 voxRDM is uniquely positioned to give (28, -18) only because it is NOT CVD-HC sig** — its loss landscape encodes general distance-matching information that allows the simulator to walk to (28, -18) without being constrained by "where CVD actually departs from HC." Adopting V4 voxRDM is a neural-evidence-free choice; the (28, -18) coordinate is behavioral-target-driven.

---

## §8. Recommendation (~150 words)

Under corrected P1 numbers, **V4 voxRDM (28, -18) is no longer the joint-best filter** — `min(P2a, P1) = 0.637` ranks below P2a-max (24, -22) (0.700) and the V1 DirA + V4 CorrDist combo (0.688). The combo `0.5·V1 DirA + 0.5·V4 CorrDist (Track-A-aligned) + 3.0·Tikh` has both terms passing nominal CVD-HC sig for sub-08 (V1 DirA no-LOO p=0.041; V4 CorrDist LOO p=0.027) and lands at sub-08 (2, +6) → **P2a=0.688, P1=0.850 (best P1 of any anchor)**. **Caveat — combo P2a (0.688) < V4 voxRDM P2a (0.750); combo wins joint avg only**. Sub-09 (0, +14) → P2a=0.975 — but sub-09 has zero LOO-sig terms; the "sig" status is V1 DirA-no-LOO only. **The combo is structural identity-collapse, just shifted**; P1 gain comes from PMAP-voting interaction, not cone-shift recovery. **Primary recommendation**: P2a-max (24, -22) — highest `min(P2a, P1) = 0.700` and `P2a = 0.750`, framed as behavioral-target-driven (per Track A Framing B). **Alternative under strict sig constraint**: V1 DirA + V4 CorrDist combo at (2, +6) — joint-avg-best, all terms sub-08-sig, but does not match V4 voxRDM's P2a. The 2-component model class ceiling for c2/c5 deutan misses remains the binding limit; Phase 4 model expansion is the only escape.

---

## §9. Files generated

- `scripts/c3_track_b_alternative_loss.py` — main analysis script (significance + landscapes + HC LOO)
- `results/c3_relabel/track_B_summary.json` — single-term + initial combo results
- `results/c3_relabel/track_B_landscapes_meta.json` — landscape min/max/argmin metadata
- `results/c3_relabel/track_B_combo_test.json` — (V1 DirA + V4 CorrDist) sweep results
- `results/c3_relabel/track_B_combo_hc_loo.json` — HC LOO for the original (non-Track-A-aligned) combo
- `results/c3_relabel/track_B_corrdist_TrackA_aligned.json` — Track-A-aligned V4 CorrDist parametric sig + landscape
- `results/c3_relabel/track_B_final_hc_loo.json` — HC LOO for top 3 combos under Track-A-aligned V4 CorrDist
- `TRACK_B_ALTERNATIVE_LOSS.md` — this document

---

## §10. What was NOT done (transparency)

- **Triangle RDM as a sig parametric loss**: existing `c3_triangle_rdm_loss.py` uses `vuln_sim` from a different cached landscape (4-term axis_3way), incompatible with my interpolated-pattern simulator. Building a Track-B-compatible triangle RDM loss would require ~30 min more compute. Skipped because the structural argument predicts identity collapse (RDM-family loss on local triangles still falls under the same RDM-family trap).
- **Crossnobis (Walther) at V1**: tested LOO p=0.969 NS, no-LOO p=0.871 NS. Not pursued.
- **Pattern-correlation-to-HC-mean per color (Direction A no-LOO with full HC)**: this is exactly what the no-LOO V1 DirA test computes (sig sub-08 p=0.041, sub-09 p=0.044). Used as parametric loss; argmin (8, +16). Documented in §3, §5.
- **Reliability-weighted RDM**: skipped — same structural family as cosine RDM (just reweighting), expected identity collapse per advisor triage. Limited compute budget.
- **Bonferroni-strict subset**: V1 cc + V4 cc remain the only Bonf-strict sig terms (per SYNTHESIS §1, no-LOO). Both have argmin at (0, 0) per SYNTHESIS §3 — already documented identity collapse. Adding them to the combo would not change the (2, +6) location materially (their gradient at small β is weak).
- **Sub-09 V1 DirA + V4 CorrDist combo HC LOO**: included in `track_B_final_hc_loo.json` but not foregrounded in the table because sub-09 V4 CorrDist sig is NS — for sub-09, the V4 CorrDist contribution is statistically dubious. Sub-09's combo argmin (0, +14) gives P2a=0.975 either way (sub-09 is near-normal under almost any loss).
