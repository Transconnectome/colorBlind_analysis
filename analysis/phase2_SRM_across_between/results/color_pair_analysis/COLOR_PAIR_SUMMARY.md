# Color Pair RDM Analysis — Quick Reference

**Date**: 2026-02-19
**Analysis**: Pairwise color discrimination differences (CVD vs HC) in SRM shared space
**Method**: Bootstrap resampling (n=1000), correlation distance RDMs, 95% CI significance test
**Settings**: HC-only SRM (n=7 training), k=4,4,3,3 for V1,V2,V3,V4

---

## Summary Statistics

### Significant Pairs per ROI and Subject

| ROI | sub-08 (Deutan) | sub-09 (Protan) | sub-10 (Deutan) |
|-----|-----------------|-----------------|-----------------|
| V1  | 20/28 (71%)     | 24/28 (86%)     | 17/28 (61%)     |
| V2  | 20/28 (71%)     | 21/28 (75%)     | 19/28 (68%)     |
| V3  | 19/28 (68%)     | 17/28 (61%)     | 16/28 (57%)     |
| V4  | 26/28 (93%)     | 19/28 (68%)     | 12/28 (43%)     |

**Key observation**: sub-08 V4 shows 93% coverage (26/28 pairs significant) — strongest evidence of hierarchical amplification and cortical reorganization.

### Effect Size Ranges

| ROI | sub-08 (Deutan) | sub-09 (Protan) | sub-10 (Deutan) |
|-----|-----------------|-----------------|-----------------|
| V1  | Max=1.11, Mean=0.47 | Max=1.20, Mean=0.60 | Max=1.00, Mean=0.51 |
| V2  | Max=1.03, Mean=0.58 | Max=0.90, Mean=0.49 | Max=0.82, Mean=0.43 |
| V3  | Max=1.38, Mean=0.75 | Max=1.21, Mean=0.60 | Max=1.69, Mean=0.74 |
| V4  | Max=1.12, Mean=0.75 | Max=1.23, Mean=0.70 | Max=0.92, Mean=0.63 |

**Trend**: V3/V4 show larger mean effects (0.60–0.75) than V1/V2 (0.43–0.60) → hierarchical amplification.

---

## Individual CVD Phenotypes

### sub-08 (Deutan) — Most Severe

**Signature**: 4/4 L-M pairs significant across all ROIs; V4 26/28 coverage
**Top effects**:
- V1: Red-Cyan +1.11* (L-M over-separation)
- V2: Orange-Blue +1.03* (L-M cross-category)
- V3: Orange-Cyan −1.38* (L-M compression)
- V4: Red-Cyan +1.12* (consistent V1), Blue-Purple +1.06* (S-cone compensation)

**Interpretation**: Widespread L-M deficits with hierarchical consistency. V4 S-cone recruitment suggests cortical adaptation strategy.

### sub-09 (Protan) — Unique S-Cone Signature

**Signature**: Blue-Magenta compression across V1/V2/V4 (unique pattern)
**Top effects**:
- V1: Blue-Magenta −1.20* (S-cone compression), Green-Magenta +1.01*
- V2: Cyan-Magenta +0.90*, Blue-Magenta −0.87*
- V3: Orange-Cyan −1.21* (L-M compression, consistent V1)
- V4: Yellow-Cyan +1.23*, Yellow-Blue −1.00*

**Interpretation**: Protan-specific S-cone deficit (blue-magenta) alongside L-M deficits. Less pervasive than sub-08 but distinct mechanistic signature.

### sub-10 (Deutan) — Selective Profile

**Signature**: Lowest V4 coverage (12/28), extreme V3 yellow-purple compression
**Top effects**:
- V1: Red-Cyan +1.00* (L-M over-separation), Blue-Magenta −1.00* (S-cone)
- V2: Red-Purple −0.82*, Red-Cyan +0.67*
- V3: Yellow-Purple −1.69* (extreme, unique), Blue-Purple +1.41* (S-cone compensation)
- V4: Blue-Purple +0.92* (consistent V3)

**Interpretation**: Most selective CVD profile. V3 yellow-purple extreme compression suggests idiosyncratic cortical reorganization. Filter candidate for V2-specific interventions.

---

## Color Axis Breakdown

### L-M Axis (Red-Green, Orange-Cyan, Yellow-Green)

**Universal deficits**:
- Red-Cyan over-separation: sub-08 (V1 +1.11, V4 +1.12), sub-10 (V1 +1.00)
- Orange-Cyan compression: all subjects in V1/V3 (−0.92 to −1.38)
- Red-Orange adjacent deficit: sub-08/sub-09 V1 (−0.60 to −0.82)

**ROI patterns**:
- **V1/V2**: 1–4 L-M pairs per subject (sub-08 strongest: 4/4)
- **V3/V4**: 2–4 L-M pairs (consistency maintained)

**Conclusion**: L-M deficits pervasive across hierarchy. sub-08 shows 100% L-M coverage in all ROIs.

### S-Cone Axis (Yellow-Blue, Purple-Magenta, Blue-Magenta)

**Compensation signature**:
- Purple-Magenta elevation: sub-08 (V1 +0.98, V4 +0.97), sub-09 (V1 +1.15)
- Blue-Purple elevation: sub-08 V2/V4 (+0.88, +1.06), sub-10 V3/V4 (+1.41, +0.92)
- Yellow-Blue over-separation: sub-10 V1 (+0.76), sub-09 V4 (−1.00 deficit)

**Unique compression (sub-09 only)**:
- Blue-Magenta deficit: V1 −1.20*, V2 −0.87*, V4 −0.81* (protan-specific)

**Conclusion**: S-cone compensation prevalent in V1 (2–3 pairs), suggesting early cortex recruits intact S-cone pathway. sub-09 shows opposite pattern (S-cone compression).

---

## Key Findings for Paper

1. **Hierarchical amplification confirmed**: Mean effect sizes increase V1→V3/V4 (0.43–0.60 → 0.60–0.75), suggesting cortical integration magnifies single-pair differences.

2. **Individual differences exceed group trends**:
   - sub-08: Widespread reorganization (V4 93% coverage)
   - sub-09: Unique S-cone deficit (blue-magenta compression)
   - sub-10: Selective pattern (V2 filter candidate)

3. **Filter targets validated**:
   - RED-ORANGE deficit (pre-val z=−0.82/−1.35 → current Δ=−0.60*)
   - BLUE-PURPLE elevation (pre-val z=+4.34 → current Δ=+0.88*)
   - Pattern stability across SRM versions and distance metrics

4. **Cortical adaptation strategy**: S-cone compensation in V1 (purple-magenta, blue-purple) suggests early visual cortex plasticity to offset L-M deficits. sub-09 exception highlights mechanistic heterogeneity.

---

## Validation Status

✅ **Replicated pre-validation (B3 bootstrap)**: L-M deficits + S-cone compensation structure preserved
✅ **Cross-metric consistency**: Correlation distance (RDM) vs Euclidean (z-score) show same directionality
✅ **Hierarchical consistency**: Red-cyan over-separation V1→V4 (sub-08: +1.11 → +1.12)
✅ **Filter priorities confirmed**: sub-08 primary (all-ROI), sub-10 V2-only

---

## File Paths

**Input**: `/scratch/connectome/haba6030/colorBlind/derivatives/full_dataset_C010/`
**Script**: `analysis/phase2_SRM_across_between/analysis/analyze_color_pair_differences.py`
**Results**: `analysis/phase2_SRM_across_between/results/color_pair_analysis/color_pair_analysis_all_rois.json`
**Summary**: `analysis/METHODS_RESULTS_SUMMARY_FOR_PAPER.md` (appended 2026-02-19)
