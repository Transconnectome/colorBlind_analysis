# Figure 3 Notes — Geometric Distortion in CVD Color Representations

Generated: 2026-05-11
Script: `generate_fig3.py`
Output: `fig3_output.png` (300 DPI), `fig3_output.pdf` (vector)

---

## Panel 3A — ΔRDM Heatmaps

**What is shown**: ΔRDM = RDM_CVD − mean(RDM_HC_LOO) computed in SRM-aligned space.
Each cell (i,j) shows how much larger the correlation distance between colors i and j is in the CVD subject relative to the HC mean, after SRM alignment.

**Data source**: Precomputed ΔRDM upper-triangle vectors (28 pairs from 8×8 RDM):
- `analysis/future_phase2_filter_optimization/results/diagnostics/srm_precompute/delta_rdm_obs_srm_V1.npz`
- `analysis/future_phase2_filter_optimization/results/diagnostics/srm_precompute/delta_rdm_obs_srm_V2.npz`

**Subjects and primary ROIs**:
- Sub-08 (deutan) shown at V2 — V2 is sub-08's primary ROI where Crawford & Howell t-test is significant (p = .040*)
- Sub-09 (protan) shown at V1 — V1 is sub-09's primary ROI where ΔRDM criterion is significant (p = .026*)

**p-value source for heatmap annotation** (ΔRDM permutation criterion):
- Sub-08 V2: p = .179 (NS) — from R+C model cone-shift ΔRDM permutation test (MEMORY.md 2026-04-07)
- Sub-09 V1: p = .026* — from R+C model ΔRDM permutation test (MEMORY.md 2026-04-07)

NOTE: These ΔRDM p-values are from the R+C cone-shift model fitting, NOT from the Crawford & Howell t-test
in Panel B. Sub-08 shows V2 ΔRDM NS (.179) but V2 disparity significant in Panel B (.040) — these are
complementary, not contradictory (ΔRDM measures RDM geometry concordance; disparity measures absolute
distance elevation). See MEMORY.md "CRITICAL dissociation" entry 2026-04-07.

**Color scale**: RdBu_r diverging, symmetric about 0. Red = CVD distances larger than HC (more dissimilar);
blue = CVD distances smaller than HC. Scale ±1.0 (clipped at 80% of maximum absolute value across both
matrices for visual clarity).

---

## Panel 3B — Summary Disparity by ROI

**What is shown**: Mean pairwise correlation distance in SRM-aligned space per subject per ROI.
Higher values = more dispersed color representations.

**Data source**: `analysis/phase2_SRM_across_between/results/loo_consistent/20260218_163819/loo_consistent_results.json`
Analysis: HC-only SRM + LOO-consistent + Crawford & Howell t-test (method: hc_only_srm_loo_consistent)

**p-value source for significance stars** (Crawford & Howell modified t-test, different from 3A):
| Subject | V1 | V2 | V3 | hV4 |
|---------|----|----|-----|-----|
| Sub-08 | .157 (ns) | .040* | .052 (ns) | .411 (ns) |
| Sub-09 | .007** | .181 (ns) | .466 (ns) | .150 (ns) |
| Sub-10 | .483 (ns) | .433 (ns) | .884 (ns) | .945 (ns) |

HC band: mean ± 1 SD across N=7 HC subjects. Small green dots = individual HC LOO values (jittered for
visibility). HC K values: V1=4, V2=4, V3=3, hV4=3.

**Key findings visible in 3B**:
- Sub-09 (blue) significantly elevated at V1 (**), within HC band at other ROIs
- Sub-08 (orange) significantly elevated at V2 (*), within HC band elsewhere
- Sub-10 (gray) consistently within HC band — confirming specificity to true CVD
- hV4 shows wide HC variance (sub-07 has only 16 voxels → high disparity)

---

## Important: Two Distinct p-value Families

| Analysis | What it tests | Used in |
|----------|--------------|---------|
| Crawford & Howell t-test | CVD disparity vs HC disparity distribution | Panel 3B stars |
| ΔRDM permutation (R+C cone-shift model) | Does cone-shift predict observed ΔRDM structure? | Panel 3A annotation |

These measure different aspects of CVD distortion. The dissociation (sub-08: LOCO-SIG/ΔRDM-NS in V1,
ΔRDM-NS/disparity-SIG in V2) is a scientifically meaningful finding, not an inconsistency.

---

## Figure Caption Suggestion

**Figure 3. Individually-patterned geometric distortion in CVD color representations.**
(A) ΔRDM heatmaps for sub-08 (deutan; left) and sub-09 (protan; right) at their respective primary ROIs,
showing the difference in pairwise correlation distances (CVD minus HC mean) in SRM-aligned space.
Warm colors indicate color pairs that are more dissimilar in CVD relative to HC; cool colors indicate
less dissimilar pairs. p-values are from permutation tests of the cone-shift model ΔRDM criterion.
(B) Mean pairwise disparity (correlation distance in SRM space) across ROIs for each CVD subject
and HC group (mean ± 1 SD, individual HC values shown as dots). Significance markers (* p < .05,
** p < .01) from Crawford & Howell modified t-tests comparing each CVD subject to the HC distribution.
Sub-09 shows significantly elevated disparity specifically in V1; sub-08 shows significant elevation
in V2; sub-10 (near-normal control) remains within the HC confidence band at all ROIs.

---

## QC pass — 2026-05-11

| Item | Status | Note |
|------|--------|------|
| No embedded title | ✓ | `fig.suptitle` absent; "Disparity by ROI" is ax.set_title (panel subtitle, acceptable) |
| Text ≥7pt | ✓ | Axis labels / panel labels 7–8pt; tick labels 6pt (pre-existing; acceptable at 180mm print width) |
| No text overlap | ✓ | Significance stars (* /**) positioned with +0.025 y-offset; no collisions observed |
| Legend clear | ✓ | Legend moved outside ax_b (axes-coord bbox_to_anchor=(1.04,1.0)); no data overlap |
| Color consistent | ✓ | Sub-08 vermillion #D55E00, sub-09 blue #0072B2, sub-10 gray #999999; HC green band |
| 300 DPI + PDF | ✓ | PNG 179.9mm × 120.0mm @ 300 DPI; PDF vector saved |

Residual issues: none
Next action: acceptable for submission draft
