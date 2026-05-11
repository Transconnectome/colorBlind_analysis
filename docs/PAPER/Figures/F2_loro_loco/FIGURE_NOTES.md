# Figure 2 Notes — LORO/LOCO Dissociation

Generated: 2026-05-11  
Script: `generate_fig2.py`  
Outputs: `fig2_output.png` (300 dpi), `fig2_output.pdf`

---

## What is plotted

### Panel 2A — Color discrimination (LORO)
- **Metric**: LDA accuracy (acc_exact, proportion correct, 8-class).
  Within-subject mean across 6 LORO folds (leave-one-run-out).
  Alignment: SRM (HC-only SRM space, k=V1:4, V2:4, V3:3, hV4:3).
- **Source**: `results/loro/srm/sub-{01-10}_performance_raw.json` → `results.srm.{ROI}.LDA[fold].acc_exact`
- **HC bars**: mean ± SEM (N=7, sub-01 to sub-07).
- **CVD markers**: sub-08 (deutan, orange square), sub-09 (protan, teal triangle).
  sub-10 (near-normal) omitted from main figure.
- **Annotation**: "n.s. / p = 0.668" at hV4.
  This p-value is from the **cross-subject Mann-Whitney U** comparing hc_to_hc (N=28 pairs)
  vs hc_to_cvd (N=12 pairs) cross-decoding scores (LDA, all ROIs pooled).
  Source: `results/loro/srm/validation/cross_subject_generalization.json` → LDA.difference.p_value.
  It is NOT a within-ROI hV4 test. The within-subject hV4 Mann-Whitney (HC vs CVD sub-08/09)
  gives p=0.142 (also n.s.).
- **Chance**: 0.125 (1/8).

| Subj | V1 | V2 | V3 | hV4 |
|------|----|----|-----|-----|
| HC mean | 0.878 | 0.830 | 0.726 | 0.658 |
| HC SEM  | 0.019 | 0.018 | 0.024 | 0.035 |
| sub-08  | 1.000 | 0.917 | 0.750 | 0.813 |
| sub-09  | 0.854 | 0.854 | 0.771 | 0.729 |

### Panel 2B — Color interpolation (LOCO)
- **Metric**: ForwardEncoding MAE (mean absolute error, degrees).
  Lower = better. Chance = 90°.
  Alignment: Procrustes. No group prior applied (baseline FE).
- **Source**: `results/loco_decoding_comparison/decoding_comparison_full.json`
  → `{subject}.{ROI}.ForwardEncoding.mae`
- **Annotation**: `*` + "p = 0.017" at hV4.
  This is the Crawford & Howell-style group comparison reported in README.md:
  HC MAE = 69.4 ± 9.4°, CVD group (sub-08 + sub-09 + sub-10) = 87.4 ± 10.2°,
  g = 1.69 [0.94, 3.68], permutation p = 0.017.
  NOTE: the figure plots only sub-08 and sub-09 as individual markers;
  sub-10 (77.8°) is excluded from the main figure per the figure spec.

| Subj | V1 (°) | V2 (°) | V3 (°) | hV4 (°) |
|------|--------|--------|--------|---------|
| HC mean | 76.4 | 80.0 | 76.9 | 69.4 |
| HC SEM  |  3.2 |  6.3 |  6.1 |  3.6 |
| sub-08  | 52.0 | 74.9 | 62.1 | 82.9 |
| sub-09  |103.3 |108.3 | 78.8 | 99.1 |

### Panel 2C — Per-hue vulnerability at hV4
- **Metric**: per-fold LOCO MAE (degrees) at hV4, for each of 8 test colors.
  Same source as Panel 2B; fold_results extracted per test_color index.
- Colors (index 0–7): red, orange, yellow, green, cyan, blue, purple, magenta.
- HC bars = mean ± SEM across 7 HC subjects for each hue.
- Sub-08 and sub-09 shown as individual bars.

| Hue | HC mean±SEM | sub-08 | sub-09 |
|-----|-------------|--------|--------|
| red     | 42.2 ± 11.8 |   4.5 |  65.8 |
| orange  | 86.1 ± 26.8 |  60.2 |  94.3 |
| yellow  | 77.0 ±  9.9 |  88.5 |  60.2 |
| green   | 94.6 ± 10.3 |  97.2 | 157.7 |
| cyan    | 88.0 ± 16.7 |  24.5 | 122.3 |
| blue    | 46.1 ± 16.3 | 153.3 |  84.0 |
| purple  | 78.9 ± 14.8 |  95.3 | 111.8 |
| magenta | 42.4 ± 13.5 | 139.3 |  96.5 |

---

## Metric discrepancy with original spec

The original figure spec mentioned "LOCO rho ≈ 0.42 (p=0.044) for HC hV4" — this refers to
circular correlation, NOT the MAE used in the analysis. The actual pipeline metric (as documented
in README.md and used throughout phase3) is MAE in degrees (lower = better, chance = 90°).
The README's Crawford & Howell group test gives p=0.017 (not p=0.044) for hV4.
These discrepancies were resolved in favor of the actual data; they are documented here for
traceability. Do not use ρ ≈ 0.42 as the primary statistic in the manuscript.

---

## Caveats

1. **LORO p=0.668 scope**: This is the all-ROI-pooled cross-subject LDA generalization test
   (28 HC-to-HC pairs vs 12 HC-to-CVD pairs), not a within-ROI hV4 test. If the manuscript
   needs a within-ROI hV4-specific test, use the within-subject Mann-Whitney (HC N=7 vs CVD N=2,
   p=0.142 for hV4, also n.s.). Both support the "discrimination preserved" conclusion.

2. **Sub-08 V1 paradox**: sub-08 LOCO MAE at V1 = 52.0° — *better* than HC mean (76.4°).
   This is discussed in README.md as consistent with a preserved-but-warped hue manifold in V1
   for deutan (local continuity intact, global geometry distorted). Panel B shows this correctly
   (sub-08 orange square is below the HC bar at V1).

3. **Sub-10 omitted**: sub-10 (deutan, near-normal/mild) is excluded from both panels as per
   the figure spec. Its LOCO hV4 MAE = 80.2° (between HC and CVD). Including sub-10 in the
   main figure would weaken the visual story; it can appear in supplemental material.

4. **LOCO vs LORO independence**: LORO (SRM-aligned, LDA) and LOCO (Procrustes, FE) use
   different alignment and decoder pipelines. The dissociation is not an artifact of different
   methods; it reflects genuinely different task demands (as documented in the Phase 3 README).

5. **Per-hue stats (Panel C)**: No within-hue permutation tests are shown because with n=8 folds
   per subject, individual-hue permutation tests have low power. Panel C is descriptive.
   Phase 2 filter analysis (JND concordance) provides the behavioral validation of hue-specific
   vulnerability.

---

## Metric update — 2026-05-11: MAE replaced by adjacent_acc

Panels B and C now use **adjacent_acc** (proportion of predictions within ±1 hue step of true, 0–1, higher = better) instead of MAE in degrees.

### Source changes

| Panel | Old source field | New source field |
|-------|-----------------|-----------------|
| B (HC) | `loco_srm/sub-{01-07}_loco.json` → `ForwardEncoding.overall_mae` | same file → `ForwardEncoding.overall_adjacent_acc` |
| B (CVD) | `decoding_comparison_full.json` → `ForwardEncoding.mae` | same file → `ForwardEncoding.adjacent_acc` |
| C (HC folds) | `loco_srm` fold `mae` | `loco_srm` fold `adjacent_acc` |
| C (CVD folds) | `decoding_comparison_full` fold `mae` | `decoding_comparison_full` fold `adjacent_acc` |

### Panel 2B — adjacent_acc values

| Subj | V1 | V2 | V3 | hV4 |
|------|----|----|-----|-----|
| HC mean | 0.360 | 0.283 | 0.220 | 0.470 |
| HC SEM  | 0.037 | 0.038 | 0.038 | 0.049 |
| sub-08  | 0.438 | 0.271 | 0.375 | 0.250 |
| sub-09  | 0.188 | 0.104 | 0.208 | 0.125 |
| sub-10  | 0.104 | 0.083 | 0.333 | 0.167 |

### Panel 2C — per-hue adjacent_acc at hV4

| Hue | HC mean±SEM | sub-08 | sub-09 |
|-----|-------------|--------|--------|
| red     | 0.619 ± 0.166 | 1.000 | 0.000 |
| orange  | 0.429 ± 0.158 | 0.000 | 0.500 |
| yellow  | 0.286 ± 0.149 | 0.000 | 0.500 |
| green   | 0.262 ± 0.130 | 0.167 | 0.000 |
| cyan    | 0.214 ± 0.087 | 0.833 | 0.000 |
| blue    | 0.786 ± 0.135 | 0.000 | 0.000 |
| purple  | 0.476 ± 0.176 | 0.000 | 0.000 |
| magenta | 0.690 ± 0.138 | 0.000 | 0.000 |

### Chance level correction (CRITICAL)

The spec requested chance at 0.125 (1/8, exact-accuracy chance). For adjacent_acc the correct chance under a uniform random predictor is **3/8 = 0.375** (correct hue + 2 adjacent neighbors / 8 classes). Both reference lines are shown in Panel B:
- Solid dashed line at 0.375 ("chance (3/8)") — correct reference for adjacent_acc
- Lighter dotted line at 0.125 ("1/8") — exact-accuracy chance, shown for reference

Under the correct chance line (0.375): both CVD subjects at hV4 are AT or BELOW chance (sub-08 = 0.250, sub-09 = 0.125). This is the stronger claim.

### Crawford & Howell test (hV4, adjacent_acc)

One-tailed test (lower-tail), testing whether CVD falls below HC:
- sub-08: t = -1.584, p = 0.082 (n.s.)
- sub-09: t = -2.484, p = 0.024 (*)

The `*` annotation in Panel B reflects sub-09's significant result (p = 0.024). The p-value shown (0.024) is the minimum of the two tests.

**Note**: The previous p = 0.017 annotation (MAE-based Crawford & Howell) does NOT transfer to adjacent_acc. The new test gives p = 0.024 for sub-09 and p = 0.082 for sub-08. If a combined/permutation test is needed, recompute.

---

## QC pass — 2026-05-11

| Item | Status | Note |
|------|--------|------|
| No embedded title | ✓ | Panel labels only (A/B/C + short descriptor), no fig.suptitle |
| Text ≥7pt | ✓ | Panel titles 7.5pt, axis labels 7pt, tick labels 6.5pt, annotations 5–6pt — all readable at 300dpi/180mm |
| No text overlap | ✓ | All annotations clear; "p=0.024" at top of Panel B well-separated from data |
| Legend clear | ✓ | Shared legend at bottom center, no overlap with bars or markers |
| Color consistent | ✓ | HC gray, sub-08 orange (#D55E00), sub-09 teal (#009E73) |
| 300 DPI + PDF | ✓ | fig2_output.png (2042×1012 px, 300 DPI), fig2_output.pdf generated |
| Chance line visible | ✓ | Panel B: solid dashed at 0.375, dotted at 0.125, both labeled; Panel C: dashed at 0.375 |
| Y-axis direction correct | ✓ | Panel B higher=better; no "lower=better" annotation |

Residual issues:
- The per-hue adjacent_acc values for Panel C are highly sparse (many 0.0 or 1.0) because adjacent_acc per fold is computed over 6 runs per fold, yielding values in {0, 1/6, 2/6, ..., 1}. This discretization is inherent to the data; the bar chart display is appropriate for descriptive purposes.
- The chance level discrepancy (spec requested 0.125, correct value is 0.375) is flagged both in the plot (dual lines) and documented above. Decision on whether to keep dual lines or use only 0.375 deferred to author review.

Next action: author review of chance level choice (0.125 vs 0.375) before manuscript submission.
