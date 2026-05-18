# Track A — LOCO Extension

**Question**: User feedback (2026-05-16) — Track A only considered RDM-family losses (Euclidean voxRDM, crossnobis, correlation-distance). **Do LOCO-derived metrics at V4 (and V1/V2) (a) provide CVD-HC distinction and (b) corroborate the behaviorally-best sub-08 cell (β_s=28, β_c=−18)?**

**Status**: Six pre-specified tests run on cached landscapes (no encoder refit). Anti-fishing verdicts written before execution. Advisor-cleared 2026-05-16.

**Verdict**: **LOCO does NOT rescue (28, −18).** V4 LOCO vuln vector is CVD-HC sig descriptively (sub-08 cosine p=0.039, Euclidean p=0.005), but every LOCO-only landscape's argmin collapses either to the **identity zone (0,0)..(0,−2)** (Tikh-regularized) or to a **different, behaviorally-worse cell (40,+22)/(44,+28)** (no Tikh). Target (28, −18) ranks mid-pack (35–87 percentile) under every LOCO loss tested. The L_topk=0 plateau for sub-08 spans β_s∈[40,44], β_c∈[22,30] — completely disjoint from the (28, −18) zone.

---

## 1. Pre-specified verdicts (anti-fishing)

| Verdict | Trigger |
|---|---|
| **RESCUE** | (28,−18) inside L_topk(V4)=0 plateau **AND/OR** top-10% under any LOCO-only composite |
| **IDENTITY_COLLAPSE** | LOCO-only composite argmin lands at (0,0)..(8,−2) zone (same dilemma as RDM family) |
| **ELSEWHERE** | LOCO composite selects a non-identity, non-(28,−18) cell |

**Observed**: both IDENTITY_COLLAPSE (Tikh-regularized variants) and ELSEWHERE (Tikh-free variants).

---

## 2. Test 1 — V4 (and V1/V2) LOCO vuln vector CVD-HC distinctness

Per-color voxel_corr from `phase1_forward_model/validation/sub-XX_loco.json` (ridge_gcv encoder, 8 colors × 1 LOCO fold each = 8-vector per subject × ROI). HC pool: sub-01..06 (sub-07 has no LOCO file due to 16-voxel V4). Sub-08, sub-09 = CVD targets.

**Distance to HC pool mean → Crawford-Howell modified t-test (df=5)**.

| ROI | Distance | HC dist (LOO) mean±SD | sub-08 d, p | sub-09 d, p |
|---|---|---|---|---|
| **V4** | cosine | 0.505 ± 0.295 | **1.392 — t=+2.78, p=0.039 ★** | 1.056 — t=+1.73, p=0.145 |
| **V4** | Euclidean | 0.930 ± 0.179 | **1.867 — t=+4.84, p=0.005 ★★** | 1.290 — t=+1.86, p=0.123 |
| V4 | corr | 1.066 ± 0.306 | 0.680 — t=−1.17, p=0.296 | 0.906 — t=−0.48, p=0.649 |
| V1 | cosine | 0.543 ± 0.528 | 0.930 — t=+0.68, p=0.527 | 0.728 — t=+0.33, p=0.758 |
| V1 | Euclidean | 0.577 ± 0.238 | 0.940 — t=+1.41, p=0.217 | 0.516 — t=−0.24, p=0.820 |
| V2 | cosine | 0.523 ± 0.599 | 1.303 — t=+1.21, p=0.282 | 1.282 — t=+1.17, p=0.294 |
| V2 | Euclidean | 0.767 ± 0.443 | 1.499 — t=+1.53, p=0.187 | 0.717 — t=−0.11, p=0.920 |

**Key finding**: V4 LOCO vuln is the only CVD-HC distinct ROI under cosine and Euclidean (sub-08 only). This **replicates the project-memory finding** that "only hV4 exceeds permutation null" — V1 and V2 LOCO vuln vectors do not separate CVD from HC under distance-to-pool tests, while V4 does for sub-08 deutan.

**Sub-09 is NS at V4 under every distance** — consistent with sub-09 being a near-normal/mild protan in the LOCO frame (per memory: V4 ρ at (2,+4) corr-dist = 0.975 ≈ 7/8 native).

**§0 compliance**: HC FPR = 100% under voxel-prediction LOCO (project_phase2_closure.md). All p-values **descriptive**. Do not read sub-08 V4 cosine p=0.039 as "loss term justified" — read as "CVD-HC distance is high in HC distribution".

---

## 3. Test 2 — L_topk(V4)=0 plateau membership

Uses `axis_3way/sub-08_V4_Stockman150_landscape.json` and `sub-09_V4_Stockman16_landscape.json` (1326 cells each, β_s ∈ [0,50] step 2 × β_c ∈ [−60,60] step 2). `l_topk(V4, K=3)` = 1 − Jaccard(top-3 vulnerable colors sim, top-3 vulnerable colors obs). L_topk=0 ⇔ simulator perfectly reproduces sub-08's top-3 vulnerable color set.

| Subject | Target | Target l_topk | n cells with l_topk=0 | Plateau β_s range | Plateau β_c range |
|---|---|---|---|---|---|
| sub-08 | (28, −18) | **0.80** | 4 | **[40, 44]** | **[22, 30]** |
| sub-09 | (2, −4) | 0.80 | 41 | [10, 38] | [48, 60] |

**The (28, −18) cell is NOT in sub-08's L_topk=0 plateau** (target l_topk=0.80, near worst possible). The plateau lives in β_s∈[40,44], β_c∈[22,30] — the **opposite sign** of (28, −18) in β_c. This is the same zone as Option C status quo (40, +26) and the V4-CCC+l_topk best cell (44, +28) per `CANDIDATE/v4ccc_ltopk/BEST_summary.json`.

(Project-memory mention of "162 cells" appears to refer to a different landscape — earlier CIELab axis or different K — not the current Stockman150 axis used here. **The directional verdict is invariant to plateau-size discrepancy**: every L_topk=0 / L_topk-argmin location across the V4-CCC+l_topk family — Stockman150 plateau at [40,44]×[+22,+30], v4ccc_ltopk BEST at (44, +28), 4-term L_topk argmin at (40, +22) — sits in **β_c positive territory**, while target (28, −18) is **β_c negative**. Whatever the canonical plateau size, target is on the wrong side of zero.)

---

## 4. Test 3 — Rank of (28, −18) in landscapes per LOCO loss

`vuln_sim` per cell from Stockman150 landscape. Losses recomputed against `vuln_cvd` (sub-08 V4 LOCO ρ per color).

**sub-08 target (28, −18)** — n=1586 unique cells (26 β_s × 61 β_c, Stockman150 grid):

| Loss | rank | %ile (lower=better) | val@(28,−18) | argmin coords | val@argmin |
|---|---|---|---|---|---|
| L_topk (1−Jaccard top-3) | 1227/1586 | 77.4% | 0.80 | **(40, +22)** | 0.00 |
| L_mse(vuln_sim, vuln_cvd) | 1383/1586 | 87.2% | 0.399 | (50, +24) | 0.250 |
| L_cos | 1242/1586 | 78.3% | 1.402 | (50, +24) | 0.717 |
| L_ccc (1−CCC) | 884/1586 | 55.7% | 0.958 | (0, −56) | 0.804 |
| L_rank (1−Spearman) | 594/1586 | 37.5% | 0.714 | (10, −32) | 0.167 |
| L_pearson | 699/1586 | 44.1% | 0.748 | (14, −32) | 0.302 |
| L_vuln_sim_amp (no obs) | 1289/1586 | 81.3% | 0.577 | (46, −60) | 0.266 |

**(28, −18) is mid-to-bottom on every LOCO loss for sub-08.** Best percentile is L_rank at 37.5% (still below median). Best LOCO arg mins are clustered at β_c ≥ +22 (l_topk, l_mse, l_cos — opposite β_c sign vs target) or at extreme β_c ≤ −30 (l_rank, l_pearson — outside the behavioral best zone).

**sub-09 target (2, −4)**:

| Loss | rank | %ile | argmin | val@argmin |
|---|---|---|---|---|
| L_topk | 381/1586 | 24.0% | (10, +60) | 0.00 |
| L_rank | 698/1586 | 44.0% | (34, +54) | 0.333 |
| L_ccc | 727/1586 | 45.8% | (14, +60) | 0.783 |
| L_mse | 1444/1586 | 91.0% | (36, +50) | 0.141 |

Sub-09's (2, −4) is closer to LOCO L_topk (24% — top quartile) but is **not** the argmin of any LOCO loss. Sub-09 LOCO argmins cluster in the β_c ∈ [+48, +60] region — far from (2, −4).

---

## 5. Test 4 — Composite LOCO-only loss argmin

Drop V1 SRM RDM (L_rdmV1) and use only V4 LOCO terms. Vary Tikhonov weight.

**sub-08 target (28, −18):**

| Variant | argmin | tgt rank | tgt %ile |
|---|---|---|---|
| Option C (4-term, λ_Tikh=3) ref | **(2, −2)** | 460/1326 | 34.7% |
| Option C, λ_Tikh=0.1 | **(40, +22)** | 783/1326 | 59.0% |
| Option C, λ_Tikh=10 | **(0, −2)** | 454/1326 | 34.2% |
| LOCO-only equal (no rdm), λ_Tikh=0.1 | **(40, +22)** | 912/1326 | 68.8% |
| LOCO-only equal, λ_Tikh=3 | **(0, −2)** | 465/1326 | 35.1% |
| LOCO-only equal, λ_Tikh=10 | **(0, −2)** | 455/1326 | 34.3% |
| LOCO-only topk-dominant, λ=0.1 | (40, +22) | 957/1326 | 72.2% |
| L_topk alone (no Tikh) | (40, +22) | 1058/1326 | 79.8% |
| L_ccc alone (no Tikh) | (16, +40) | 803/1326 | 60.6% |
| L_mse alone (no Tikh) | (50, +24) | 1196/1326 | 90.2% |
| L_ccc + Tikh=0.1 | **(0, −2)** | 595/1326 | 44.9% |

**Pattern**: every LOCO-only composite for sub-08 lands at one of two places —
- **β_c < 0 identity zone (0, 0)..(2, −2)** when Tikhonov is non-trivial (`λ ≥ 0.1` for L_ccc; `λ ≥ 3` for joint terms)
- **β_c > 0 antibehavioral zone (40, +22) / (44, +28) / (50, +24)** when Tikh is small or absent

The behavioral target (28, −18) is unreachable from either side: it lies between two attractors with opposite β_c signs. **No Tikh weight pulls the argmin to (28, −18).** This is structurally identical to the §5 dilemma in `SYNTHESIS_2026-05-16.md` — directional information for the 2-component simulator does not exist in the LOCO loss landscape near (28, −18).

**sub-09 target (2, −4):**

| Variant | argmin | tgt rank | tgt %ile |
|---|---|---|---|
| Option C ref (λ=3) | **(0, −2)** | **3/1326** | **0.2%** ★ |
| Option C λ=0.1 | (12, −28) | 5/1326 | 0.4% ★ |
| Option C λ=10 | (0, −2) | 5/1326 | 0.4% ★ |
| LOCO-only equal λ=0.1 | (36, +50) | 147/1326 | 11.1% |
| LOCO-only equal λ=3 | (0, 0) | 7/1326 | 0.5% ★ |
| L_ccc + Tikh=0.1 | (14, +28) | 31/1326 | 2.3% ★ |
| L_topk alone | (36, +50) | 269/1326 | 20.3% |

Sub-09's (2, −4) is top-1% on Tikh-regularized composites because (2, −4) is essentially identity for a near-normal protan. **Sub-09 needs no filter** — LOCO recovery is artifact of regularization pulling to identity, which happens to coincide with the behavioral best.

---

## 6. Test 5 — Per-color V4 LOCO ρ (Crawford-Howell, Bonferroni 8-test α=0.00625)

| color | HC mean±SD | sub-08 | t | p | p_Bonf8 |
|---|---|---|---|---|---|
| c1 Red | +0.355±0.221 | +0.573 | +0.91 | 0.403 | 1.0 |
| **c2 Orange** | +0.232±0.265 | −0.637 | **−3.04** | **0.029 ★** | 0.230 |
| **c3 Yellow→olive** | +0.184±0.317 | −0.733 | **−2.68** | **0.044 ★** | 0.352 |
| c4 Green | +0.148±0.300 | −0.306 | −1.40 | 0.221 | 1.0 |
| c5 Cyan | +0.182±0.254 | +0.250 | +0.25 | 0.814 | 1.0 |
| c6 Blue | +0.384±0.318 | −0.251 | −1.85 | 0.124 | 0.993 |
| **c7 Purple** | +0.255±0.383 | −0.759 | **−2.45** | **0.058 ~** | 0.465 |
| c8 Magenta | +0.113±0.348 | −0.334 | −1.19 | 0.287 | 1.0 |

**Three colors nominally CVD-HC sig at V4** for sub-08: c2 orange (p=0.029), c3 yellow→olive (p=0.044), c7 purple (p=0.058 marginal). None survive Bonferroni 8-test. **The deutan confusion axis = c2/c5 + c6/c1** — c2 (sig) and c7 (marginal) lie near the L-M projection extremes; c5 is NOT sig (sub-08 c5 is actually correctly decoded, ρ=+0.25 above HC mean). This is consistent with: sub-08's c5 cyan signal is preserved at V4 (lookup-table effect from 8-color paradigm), but c2 orange and c7 purple are anti-decoded.

Sub-09 V4 per-color: no color reaches p<0.05 (c4 green p=0.070 closest). Consistent with mild protan.

---

## 7. Test 6 — Cross-ROI replication (memory: "only hV4 exceeds permutation null")

| ROI | sub-08 cosine p | sub-09 cosine p |
|---|---|---|
| V1 | 0.527 NS | 0.758 NS |
| V2 | 0.282 NS | 0.294 NS |
| **V4** | **0.039 ★** | 0.145 |

**Replicated**: V4 is the only ROI where LOCO vuln vector is CVD-HC distinct for sub-08 (cosine p=0.039 nominally; Euclidean p=0.005). V1 and V2 are NS under any distance metric for either CVD subject. This is the standard hV4 cone-shift framing in `FORWARD_MODEL_AUDIT.md` and `MEMORY` (gate: hV4 = PRIMARY GO; V1/V2 = discrimination-only).

---

## 8. Does LOCO rescue (28, −18)? — Honest verdict

**No.** The pre-specified RESCUE conditions both fail:

1. **L_topk(V4)=0 plateau**: target l_topk=0.80 (near worst), plateau lives at β_c∈[+22, +30] — opposite sign of target.
2. **Top-10% under any LOCO composite**: best percentile is L_rank at 37.5% (sub-08) and L_topk at 24.0% (sub-09 — but for sub-09 (2,−4) is essentially identity anyway).

**Pattern observed**: same dual-attractor dilemma as RDM family.
- Tikh-regularized LOCO composites → IDENTITY_COLLAPSE at (0, −2)
- Tikh-free LOCO composites → ELSEWHERE at (40, +22) / (44, +28) — the *opposite β_c sign* from behavioral target

**(28, −18) is "in the gap" between LOCO attractors.** The 2-component simulator cannot project the LOCO landscape's directional signal onto (β_s≈28, β_c≈−18). This is the same structural failure as RDM family identified in `SYNTHESIS_2026-05-16.md` §5.

**What LOCO does provide**:
- Strong descriptive evidence that V4 carries cone-shift signal for sub-08 (cosine p=0.039, Euclidean p=0.005)
- Per-color nominally sig: c2 orange, c3 yellow→olive, c7 purple — the deutan-axis colors where vuln_obs is most negative (worst-decoded)
- Replication of "V4 only" cone-shift gate for the LOCO measurement family

**What LOCO does NOT provide**:
- An argmin at or near (28, −18)
- A loss-term construction whose argmin coincides with the behavioral target
- Any rescue of the (28, −18) cell as a parametric optimum

---

## 9. Recommendation (~150 words)

The user's intuition that LOCO might rescue (28, −18) where RDM family failed is **empirically incorrect**: LOCO landscapes converge to the same dual-attractor dilemma identified in `SYNTHESIS_2026-05-16.md` §5. Tikh-regularized LOCO composites collapse to identity (0, −2); Tikh-free composites land at (40, +22) — the OLD Option C zone that fails the c3-olive constraint (c3 → green). The behavioral target (28, −18) sits in the gap between these attractors and ranks 35–87 percentile under every LOCO loss tested. **Use LOCO V4 vuln descriptively**: cite sub-08 V4 cosine p=0.039 / Euclidean p=0.005 as evidence that V4 carries cone-shift signal, alongside the V4-CCC Bonferroni-validated cross-color correlation matrix (p=0.007). Adopt **Framing A** from Track A V4 voxRDM justification: filter selection by behavioral-target proximity for (28, −18); descriptive neural evidence stack (V4 cc, V4 corr-distance RDM, V4 LOCO vuln cosine) supports "V4 cone-shift exists" without claiming it drives the (β_s, β_c) parameter selection. **2-component model class limit confirmed independently by LOCO family.**

---

## 10. Files

- `scripts/c3_track_A_loco_extension.py` — main analysis (pre-specified, anti-fishing)
- `results/c3_relabel/track_A_loco_extension.json` — all stats (~30 KB)

Cached inputs reused (no encoder refit):
- `phase1_forward_model/results/validation/sub-XX_loco.json` — ridge_gcv per-color voxel_corr
- `phase2/results/axis_3way/sub-{08,09}_V4_Stockman{150,16}_landscape.json` — 1326-cell vuln_sim + l_topk + l_ccc
- `phase2/results/old_formula/sub-{08,09}_V4_4term_landscape_with_vuln_sim.json` — 4-term composite cells with vuln_sim and l_rdm
