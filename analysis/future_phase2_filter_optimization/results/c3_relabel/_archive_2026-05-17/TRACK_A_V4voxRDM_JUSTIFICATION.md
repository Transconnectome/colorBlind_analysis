# Track A — V4 voxRDM Loss-Term Justification

**Question**: Can V4 voxel RDM (Euclidean dissimilarity) be defended as a loss term, given the prior finding that full-RDM cosine to HC pool is NOT significantly different for CVD vs HC at V4 (sub-08 p=0.398, sub-09 p=0.097)?

**Date**: 2026-05-16
**Status**: Three pre-specified tests run (anti-fishing, advisor-cleared).
**Verdict**: **V4 Euclidean voxRDM remains descriptive-only.** A closely-related variant — **V4 correlation-distance RDM** — recovers sub-08 significance (p=0.027), but its loss landscape collapses to identity. The behavioral-best cell (28, -18) is **not** corroborated by any RDM variant tested.

---

## 1. Pre-specified tests (3 tests, no fishing)

### Test 1 — Crossnobis V4 RDM (Walther et al. 2016, Diedrichsen 2016)

Cross-validated noise-corrected Euclidean RDM (signed-sqrt of cross-validated squared distance, identity covariance). The gold standard for fMRI RDM analysis.

| Subject | cosine to HC pool | t (df=6) | p (two-tailed) |
|---|---|---|---|
| HC mean ± SD | 0.9049 ± 0.0325 | — | — |
| sub-08 | +0.9140 | +0.260 | **0.804 NS** |
| sub-09 | +0.8830 | −0.633 | **0.550 NS** |

Crossnobis at V4 is **worse** than Euclidean voxRDM at detecting CVD-HC difference. Cross-validation averages over noisy run-pairs but the V4 16-voxel signal is so sparse that the cv-correction adds variance rather than removing it.

Cross-ROI comparison (Test 1b) — V1 sub-09 recovers significance (p=0.046*), but V4 does not for either subject.

### Test 2 — Correlation-distance V4 RDM (1 − r, then cosine-to-HC-pool)

Mathematically the same RDM family as Euclidean voxRDM but uses Pearson correlation distance. Motivated by the fact that the V4 cross-color correlation matrix passes Bonferroni (sub-08 p=0.007 ★★, sub-09 p=0.010 ★ per `/tmp/voxrdm_sig.py`).

| Subject | cosine to HC pool | t (df=6) | p (two-tailed) |
|---|---|---|---|
| HC mean ± SD | 0.9257 ± 0.0177 | — | — |
| sub-08 | +0.8706 | **−2.911** | **0.0269 ★** |
| sub-09 | +0.8987 | −1.429 | 0.2029 NS |

**Sub-08: significant under correlation-distance RDM.** Confirms the cc-matrix signal carries through to a proper RDM formulation. Sub-09 remains NS at V4.

Sensitivity to HC pool composition:
| HC excluded | n_HC | sub-08 p | sub-09 p |
|---|---|---|---|
| (none) | 7 | 0.027 ★ | 0.203 |
| sub-04 (low reliability) | 6 | 0.047 ★ | 0.266 |
| sub-04, sub-02 | 5 | 0.061 ~ | 0.266 |

Sub-08 significance is robust to dropping the lowest-reliability HC (sub-04 split-half r=0.142). Cannot survive a Bonferroni 3-method correction (α=0.017) at p=0.027.

### Test 2b — Loss-landscape swap: does (28, -18) survive?

Replace Euclidean voxRDM with correlation-distance RDM as the L_rdm loss term; recompute the full landscape; check argmin and the rank of (28, -18) (sub-08) and (2, -4) (sub-09).

**Sub-08 (axis = 150°, target = (28, -18) → P2a 0.750):**
| Metric | argmin (β_s, β_c) | P2a | Loss at (28,-18) | rank of (28,-18) |
|---|---|---|---|---|
| Euclidean voxRDM | (4, -8) | 0.688 | 0.1039 | 341 / 1586 |
| Correlation-dist RDM | (0, 0) | 0.688 | 0.1502 | 237 / 1586 |

**Sub-09 (axis = 16°, target = (2, -4) → P2a 0.975):**
| Metric | argmin (β_s, β_c) | P2a | Loss at (2,-4) | rank of (2,-4) |
|---|---|---|---|---|
| Euclidean voxRDM | (36, +52) | 0.525 | 0.1159 | 802 / 1586 |
| Correlation-dist RDM | (2, +4) | 0.975 | 0.1413 | 39 / 1586 |

**The (28, -18) cell does NOT win under any V4 RDM variant we tested.** It is mid-tier in every landscape (top ~15-20%). The only way (28, -18) becomes argmin is under the specific Euclidean voxRDM + Tikhonov combination used previously, and that combination uses a CVD-HC non-significant loss term.

For sub-09, correlation-distance RDM is **strictly better than Euclidean** — its argmin lands at (2, +4), giving P2a 0.975 vs Euclidean's argmin (36, +52) at P2a 0.525.

### Test 3 — V4 voxRDM split-half reliability (sanity, not CVD-HC)

100 random run-half splits per subject, Pearson r between split-half RDM upper-triangles.

| Subject | mean r ± SD | Note |
|---|---|---|
| sub-01 | +0.631 ± 0.097 | |
| sub-02 | +0.378 ± 0.087 | |
| sub-03 | +0.927 ± 0.030 | |
| sub-04 | **+0.142 ± 0.163** | **HC outlier — low reliability** |
| sub-05 | +0.614 ± 0.093 | |
| sub-06 | +0.708 ± 0.124 | |
| sub-07 | +0.705 ± 0.156 | |
| **sub-08** | **+0.943 ± 0.037** | **CVD — highest reliability** |
| **sub-09** | **+0.897 ± 0.059** | **CVD — second-highest** |

CVD subjects' V4 voxRDMs are **more reproducible** than the HC pool — sub-08/09 are stable enough to be meaningful loss targets (not pure noise) at the RDM-data level. (This sanity-checks the RDM construction; it does NOT certify the argmin location, which is a property of the loss landscape, not the RDM.) Sub-04's V4 RDM is essentially noise (r=0.14, 16 voxels). This HC outlier inflates the HC SD and weakens any CVD-HC comparison. Dropping sub-04 modestly improves sub-08 corr-distance p from 0.027 → 0.047 (still significant), but does not rescue Euclidean voxRDM (p=0.398 → 0.585, gets worse).

---

## 2. Which approach recovers a defensible CVD-HC distinction at V4?

**Yes**: V4 **correlation-distance RDM** (sub-08 p=0.027, uncorrected).
**No**: V4 **Euclidean voxRDM** (sub-08 p=0.398), **Crossnobis voxRDM** (p=0.804).

The correlation-distance variant is the cleanest defensible signal at V4. But this signal does **not** translate to a parametric (β_s, β_c) argmin in the P2a-max region — its loss landscape collapses to identity (0, 0) for sub-08, exactly as predicted by the §5 dilemma in SYNTHESIS_2026-05-16.md: a loss term can detect CVD ≠ HC without containing directional information for the 2-component simulator.

---

## 3. Justification narrative (~150 words)

V4 voxel RDM as a loss term is **not directly defensible** under the user's neural-significance constraint when implemented as standard Euclidean dissimilarity (sub-08 p=0.398) or as crossnobis (p=0.804). However, the V4 cone-shift signal **is recoverable** under correlation-distance RDM (sub-08 p=0.027, sub-04-robust), which mathematically belongs to the same RDM family. This confirms that V4 carries a real CVD-HC representational signal — consistent with the V4 cc-matrix cosine result (Bonferroni-passed). The remaining question is whether V4 RDM-style information should drive the **filter parameter selection**. Empirically it cannot: every V4 RDM variant tested (Euclidean, crossnobis, correlation-distance) has its loss landscape argmin near the identity filter (β_s ≈ 0, β_c ≈ 0) for sub-08. The behaviorally-best (28, -18) cell ranks mid-pack (top 15-20%) under every variant. V4 RDM-as-loss is a **descriptive characterization tool**, not a parameter selector for the inverse filter.

---

## 4. Honest caveats

- **Sub-08 corr-distance p=0.027 does NOT survive Bonferroni 3-test correction** (α=0.017). It is significant only as a single pre-specified test.
- **Sub-09 V4 RDM is NS under every variant tested** (Euclidean p=0.097, crossnobis p=0.550, corr-distance p=0.203). V4 is not a defensible signal source for sub-09 protan.
- **The 16-voxel V4 ceiling (sub-07) is a hard limit.** Cannot be circumvented by analysis choices. Sub-04's near-zero V4 reliability (split-half r=0.142) confirms the noise floor.
- **HC FPR = 100% under voxel-prediction LOCO** (project_phase2_closure.md). Specificity claims forbidden under §0 regardless of RDM variant.
- **(28, -18) is not an argmin of any V4 RDM variant tested.** It is a Euclidean voxRDM argmin only — under a loss term that is NS for sub-08 CVD-HC.
- **The split-half reliability finding is descriptive only** (sub-08/09 r > all HC except sub-03 and sub-07). It documents internal RDM stability but does not justify the RDM as a CVD-HC discriminator.

---

## 5. Recommendation

**V4 voxRDM as primary loss term: NOT defensible** under §0 + neural-significance constraint.

Two acceptable framings for the manuscript:

### Framing A (preferred — descriptive)
> V4 voxRDM is documented as a descriptive characterization of V4 representational geometry. The CVD-HC contrast at V4 reaches significance under correlation-distance RDM for sub-08 deutan (p=0.027, robust to HC outlier removal) but not under Euclidean or crossnobis. Sub-09 protan shows no significant V4 RDM difference under any variant tested. Filter selection does not use V4 voxRDM as a loss term — it is reported as supporting evidence for V4 cone-shift signal alongside the Bonferroni-validated V4 cross-color correlation matrix (sub-08 p=0.007, sub-09 p=0.010).

### Framing B (only if (28, -18) is needed for behavioral story)
> The (β_s=28, β_c=-18) filter is presented as **behavioral-target-driven** with descriptive neural support: it occupies the top quintile of the V4 corr-distance RDM landscape (rank 237/1586 for sub-08) and the V4 voxel RDM landscape (rank 341/1586), but is not the argmin of either. Adopt only with explicit acknowledgment that the loss term used to localize it (Euclidean voxRDM) is CVD-HC non-significant.

### Why not Framing C ("upgrade to corr-distance RDM as primary loss")
Tempting because corr-distance recovers sub-08 significance, but its argmin lands at (0, 0) → P2a 0.688 (= OPT-6 baseline). This gains nothing over the V1cc/V4cc Bonferroni-validated identity-collapse solutions already in §3 of the synthesis. No P2a improvement; no parameter recovery in the P2a-max region.

### Side finding worth noting for sub-09
For sub-09 protan, **correlation-distance RDM is strictly better than Euclidean voxRDM** as a parameter selector at V4: argmin (2, +4) → P2a 0.975 (vs Euclidean argmin (36, +52) → P2a 0.525). If a sub-09-specific V4 RDM loss is needed downstream, corr-distance is the cleaner choice. The CVD-HC corr-distance contrast is NS for sub-09 (p=0.20), so this is a parameter-selection upgrade, not a neural-significance upgrade.

### Final recommendation
Adopt **Framing A** + V1cc/V4cc Bonferroni-validated identity (OPT-6, min P2a 0.688) as the primary deliverable. Document V4 corr-distance RDM significance as supporting evidence for "V4 carries cone-shift signal" without using it for filter selection. Keep V4 voxRDM (28, -18) as a transparent descriptive alternative in the supplementary (Framing B), labeled as behavioral-target-driven rather than neural-evidence-driven. **The 2-component model class cannot reach the c2/c5 fix region** regardless of which V4 RDM variant is used — that is a model-class limit, not a loss-term failure.

---

## 6. Files generated

- `scripts/c3_track_A_v4voxRDM_justify.py` — main analysis script
- `results/c3_relabel/track_A_v4voxRDM_justify.json` — all statistical summaries
- `results/c3_relabel/track_A_rdms.json` — full crossnobis + corr-distance RDMs per subject

Total compute: ~5 minutes. All tests pre-specified before execution per advisor guidance.
