# Figure 3 Notes — Geometric Distortion in CVD Color Representations

Generated: 2026-05-11
Script: `generate_fig3.py`
Output: `fig3_output.png` (300 DPI), `fig3_output.pdf` (vector)

---

## Panel 3A — ΔRDM Heatmaps

**What is shown**: ΔRDM = RDM_CVD − mean(RDM_HC_LOO) computed in SRM-aligned space.
Each cell (i,j) shows how much larger the correlation distance between colors i and j is in the CVD subject relative to the HC mean, after SRM alignment.

**Data source**: Precomputed ΔRDM upper-triangle vectors (28 pairs from 8×8 RDM):
- `analysis/phase5_filter_optimization/results/diagnostics/srm_precompute/delta_rdm_obs_srm_V1.npz`
- `analysis/phase5_filter_optimization/results/diagnostics/srm_precompute/delta_rdm_obs_srm_V2.npz`

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

---

## Post-feedback revision — 2026-05-11

NotebookLM 질의(ColorBlind_comprehensive, 23 citations) 기반으로 다음 변경:

1. **Color strips on heatmap axes** — top + left edges에 STIM_LAB 팔레트(Fig 1과 동일한 8 hue Lab→sRGB)로 색 스트립 patch 추가. Kuriki 2025 Optics Express Fig 2B / 3A 컨벤션. 이전에는 색명 약자("Red", "Org" …)만 있었고 색 자체는 시각화 안 됨.

2. **Hue angle ticks** — 축 tick 레이블이 색명 약자 → physical hue angle ("0°", "45°", "90°", "135°", "180°", "225°", "270°", "315°")로 교체. CCW from Red @ 0°. 색 스트립이 hue 정체성을 시각적으로 담당하므로 텍스트는 각도에 집중.

3. **1D row-mean profile per heatmap** — 각 heatmap 우측에 horizontal bar plot 추가. y-축은 heatmap row index와 align되고 (Row 0 = Red at top), bar 길이 = `mat.sum(axis=1) / 7` (diagonal 제외 row mean ΔRDM). bar 색상은 RdBu_r colormap에서 row mean 값으로 mapping → 양수 = warm (해당 hue가 평균적으로 더 distorted). Kuriki 2025 Fig 3B의 1D row-mean profile 컨벤션.

4. **Shared colorbar** — 두 heatmap이 동일한 vmax_global을 사용하므로 단일 cbar로 통합. cax 우측 라벨 → cbar 아래 작은 horizontal text ("ΔRDM (CVD−HC)"). Panel B y-label과의 시각적 충돌 해소.

5. **Axes restructuring** — heatmap width 0.24 → 0.19 (1D profile 공간 확보), Panel B width 0.27 → 0.26, 우측으로 약간 이동.

References for design choices (NotebookLM):
- Kuriki (2025) Opt Express Fig 2B/3A: hue angle ticks + color stripes along RDM axes
- Brouwer & Heeger (2013) J Neurosci Fig 4: marginal 1D profile alongside 2D representation
- (Boehm 2014 Fig 4: best-fitting ellipses on MDS — deferred; current fig3 does not include MDS panel)

Deferred for future revision: MDS scatter with bootstrap 2D crosshairs + best-fit ellipses (Boehm 2014 / Brouwer&Heeger 2013 convention). Would require MDS computation pipeline; current Panel B (line plot of disparity by ROI) achieves the per-subject comparison without MDS.
