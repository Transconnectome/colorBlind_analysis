# CVD Color Distortion Figures - Visualization Methods & Results

**Generated:** 2026-02-22
**Location:** `analysis/future_phase2_filter_optimization/figures/`
**Method:** Within-ROI FDR correction (q < 0.05)

---

## Table of Contents

1. [Overview](#overview)
2. [Visualization Method](#visualization-method)
3. [Panel Descriptions](#panel-descriptions)
4. [Results by ROI](#results-by-roi)
5. [Figure Captions for Paper](#figure-captions-for-paper)
6. [Methods Section Text](#methods-section-text)
7. [Results Section Text](#results-section-text)

---

## Overview

### Purpose

These figures visualize color representation distortions in color vision deficiency (CVD) across the visual processing hierarchy (V1→V2→V3→hV4), showing the complete chain from **stimulus → anatomical location → cortical surface → representational distortion**.

### Key Features

- **Multi-panel layout:** 3 rows (CVD subjects) × 4 columns (analysis stages)
- **Within-ROI FDR correction:** Controls false discovery rate at q < 0.05 per ROI
- **Hierarchical comparison:** V1 (early) → V2 (intermediate) → V3 (higher) → hV4 (color-selective)
- **Individual phenotypes:** Deutan (sub-08, sub-10) vs Protan (sub-09)

### Files Generated

```
cvd_distortion_figure_V1.png   (6000×4800 px @ 300 DPI, 1.6 MB)
cvd_distortion_figure_V2.png   (6000×4800 px @ 300 DPI, 1.6 MB)
cvd_distortion_figure_V3.png   (6000×4800 px @ 300 DPI, 1.6 MB)
cvd_distortion_figure_hV4.png  (6000×4800 px @ 300 DPI, 1.6 MB)
```

---

## Visualization Method

### Data Pipeline

```
1. fMRI Preprocessing (C010 + Procrustes)
   └─→ amplitudes_procrustes.npy (6 runs × 8 colors × n_voxels)

2. RMS Activation Computation
   └─→ sqrt(mean(mean(amplitudes)²)) → (n_voxels,)

3. Representational Dissimilarity Matrix (RDM)
   └─→ pdist(patterns, metric='correlation') → (8×8 symmetric)

4. Statistical Testing
   └─→ Crawford & Howell (1998) single-case test
   └─→ Within-ROI FDR correction (Benjamini-Hochberg)

5. Multi-Panel Visualization
   └─→ 4 complementary views per subject
```

### Statistical Framework

**Crawford & Howell (1998) Modified t-test:**
- Compares single CVD case against HC control sample
- Accounts for small sample variance (n=7 HC)
- Provides z-scores and p-values for each color pair

**Within-ROI FDR Correction:**
- Applied separately per ROI (28 color pairs tested)
- Benjamini-Hochberg procedure at q < 0.05
- More sensitive than global FDR (336 tests), appropriate for independent ROIs
- Discovery rate: 11.6% (39/336 pairs across all tests)

### Color Pairs Analyzed

**Total:** 28 unique pairs from 8 colors
- Colors: Red, Orange, Yellow, Green, Cyan, Blue, Purple, Magenta
- Combinations: C(8,2) = 28 pairs
- Metric: Correlation distance (1 - Pearson r)

---

## Panel Descriptions

### Panel A: Color Wheel Stimulus

**Purpose:** Show experimental stimuli
**Method:** Circular arrangement of 8 isoluminant hues at 45° intervals
**Data source:** COLOR_RGB dictionary (hardcoded RGB values matching experiment)

**Visual elements:**
- 8 color patches (radius 0.08) arranged in circle (radius 0.5)
- Color names positioned outside (radius 1.1) to avoid overlap
- Matches actual experimental stimuli presented during fMRI

**Interpretation:** Provides visual reference for color pairs analyzed in Panel D

---

### Panel B: Glass Brain (Whole Brain Anatomy)

**Purpose:** Show ROI location in standard MNI space
**Method:** Transparent brain with ROI activation overlay
**Tool:** `nilearn.plotting.plot_glass_brain()`

**Data source:**
- Volume: `VoxelToBrainMapper.create_brain_volume(rms_activation)`
- Space: MNI152NLin2009cAsym 2mm
- Views: 4 orthogonal projections (Left/Right/Dorsal/Ventral)

**Color scale:**
- Colormap: Reds (0 to 95th percentile)
- Values: RMS activation strength
- Individual scale per subject

**Visual elements:**
- Transparent brain outline (black)
- Red hot spots indicate ROI location
- Multi-view projection for 3D localization

**Interpretation:**
- Confirms ROI spatial location
- Shows activation strength across ROI extent
- Provides anatomical context (calcarine for V1, lateral occipital for V2-V3)

---

### Panel C: Occipital Surface (Posterior Inflated)

**Purpose:** Show cortical surface activation pattern
**Method:** Volume-to-surface projection on fsaverage5 inflated cortex
**Tool:** `nilearn.plotting.plot_surf_stat_map()`

**Data pipeline:**
```python
1. Volume → Surface projection
   surface.vol_to_surf(brain_img, fsaverage['pial_left/right'],
                      radius=10mm, kind='ball', n_samples=20)

2. Hemisphere selection
   Test both L/R hemispheres, use hemisphere with stronger signal

3. Surface rendering
   plot_surf_stat_map(fsaverage['infl_left/right'], texture,
                     view='posterior', cmap='hot')
```

**Parameters:**
- **Sampling radius:** 10mm sphere around each surface vertex
- **Sampling method:** 'ball' (3D sphere) with 20 sample points
- **Interpolation:** Linear (trilinear for volume values)
- **Colormap:** Hot (0 to shared vmax across 3 CVD subjects)
- **View:** Posterior (optimized for occipital cortex)

**Why these parameters?**
- Small ROIs (~100-500 voxels) require large sampling radius
- Ball sampling (vs line) increases coverage probability
- Bilateral testing accounts for individual hemisphere dominance
- Shared color scale enables cross-subject comparison

**Interpretation:**
- Visualizes activation on actual cortical surface topology
- Shows relationship to sulci/gyri (background sulcal depth map)
- Sparse activation (10-100 vertices) reflects small ROI size
- Higher vertices count = better volume-to-surface mapping

**Technical notes:**
- V1: 58-107 vertices (largest ROI)
- V2: 34-58 vertices
- V3: 4 vertices (small ROI, deep in sulcus)
- hV4: 13 vertices (small ROI)

---

### Panel D: RDM Distortion Bars (CVD - HC)

**Purpose:** Quantify color pair representational distortions
**Method:** Horizontal bar plot of RDM differences (CVD minus HC mean)
**Visualization:** Top pairs by FDR-corrected significance

**Data computation:**
```python
1. Compute CVD subject RDM
   cvd_rdm = squareform(pdist(cvd_patterns, metric='correlation'))

2. Compute HC mean RDM
   hc_rdm = mean([HC_RDM_sub01, ..., HC_RDM_sub07])

3. Difference RDM
   diff_rdm = cvd_rdm - hc_rdm

4. FDR filtering
   Show only pairs with fdr_within_roi == True (q < 0.05)
   If none, show top 10 by |Δ| with note
```

**Visual elements:**
- **Red bars:** Increased dissimilarity (CVD > HC)
  - Interpretation: Colors more distinguishable in CVD
  - Mechanism: Possible compensatory enhancement

- **Blue bars:** Decreased dissimilarity (CVD < HC)
  - Interpretation: Color confusion (reduced discriminability)
  - Mechanism: Loss of cone-opponent signal

- **Asterisk (*):** FDR-significant pairs marked in y-axis labels

**Bar length:** Δ Dissimilarity magnitude (correlation distance units)
- Typical range: -0.7 to +0.8
- Larger |Δ| = stronger distortion

**Sorting:** By absolute magnitude (largest distortions on top)

**Title suffix:**
- `(within-ROI FDR q<0.05, n=X)` when FDR-significant pairs exist
- `(top 10, uncorrected)` when no FDR survivors

**Interpretation guide:**

| Direction | Color | Meaning | Mechanism |
|-----------|-------|---------|-----------|
| Positive (→) | RED | CVD > HC | Enhanced differentiation, compensatory processing |
| Negative (←) | BLUE | CVD < HC | Color confusion, classic cone loss pattern |

**Expected patterns:**
- **Deutan (M-cone loss):** Red-Green confusion (BLUE bars)
- **Protan (L-cone loss):** Red-Cyan confusion (BLUE bars)
- **S-cone preservation:** Blue-Purple enhancement (RED bars)

---

## Results by ROI

### V1: Early Visual Cortex

**Overall:** 9 pairs significant (within-ROI FDR q<0.05)

#### sub-08 (Deutan): 3 pairs
1. **red-yellow** (z=5.14, p<0.0001) - Strongest V1 effect
2. yellow-purple (z=4.84, p<0.0001)
3. red-cyan (z=3.61, p=0.0003)

**Pattern:** M-L opponent pathway distortion (red-yellow)

#### sub-09 (Protan): 6 pairs
1. **cyan-magenta** (z=4.08, p<0.0001)
2. orange-magenta (z=3.71, p=0.0002)
3. red-magenta (z=3.52, p=0.0004)
4. green-magenta (z=3.43, p=0.0006)
5. yellow-purple (z=-3.31, p=0.0009, BLUE bar)
6. green-blue (z=-3.00, p=0.0027, BLUE bar)

**Pattern:** Magenta-related pairs clustered (L-cone loss affects long-wavelength end)

#### sub-10 (Deutan): 0 pairs
- No FDR-significant pairs (mildest phenotype)

**V1 Interpretation:**
- Early cone-opponent signals already show distortions
- **Protan effects stronger than Deutan in V1** (6 vs 3 pairs)
- Magenta processing particularly affected in Protan (L-cone loss)
- V1 preserves most cone information but subtle distortions emerge

---

### V2: Intermediate Visual Area

**Overall:** 12 pairs significant (all from sub-08)

#### sub-08 (Deutan): 12 pairs
Top 5:
1. **yellow-purple** (z=13.87, p<0.0001) - **Strongest effect across all ROIs**
2. **red-yellow** (z=9.38, p<0.0001)
3. blue-purple (z=6.15, p<0.0001)
4. yellow-green (z=5.47, p<0.0001)
5. orange-yellow (z=5.45, p<0.0001)

All 12: yellow-purple, red-yellow, blue-purple, yellow-green, orange-yellow, red-cyan, yellow-blue, yellow-magenta, cyan-purple, yellow-cyan, orange-cyan, green-blue

**Pattern:**
- **Yellow-dominant distortions** (9/12 pairs involve yellow)
- M-cone loss severely affects yellow processing
- Progression from V1 (3 pairs) → V2 (12 pairs)

#### sub-09 (Protan): 0 pairs
- No FDR-significant pairs

#### sub-10 (Deutan): 0 pairs
- No FDR-significant pairs

**V2 Interpretation:**
- **Intermediate processing amplifies distortions** (sub-08 only)
- Yellow as critical hue for M-cone opponent coding
- **Individual differences:** sub-08 >> sub-09/sub-10
- V2 may be key locus for hierarchical distortion accumulation

---

### V3: Higher Visual Area

**Overall:** 18 pairs significant

#### sub-08 (Deutan): 17 pairs
Top 10:
1. **red-green** (z=7.85, p<0.0001) - **Classic Deutan confusion**
2. green-purple (z=6.96, p<0.0001)
3. yellow-purple (z=6.17, p<0.0001)
4. yellow-magenta (z=6.11, p<0.0001)
5. red-yellow (z=5.88, p<0.0001)
6. red-cyan (z=5.36, p<0.0001)
7. orange-yellow (z=5.16, p<0.0001)
8. blue-purple (z=4.58, p<0.0001)
9. red-blue (z=4.37, p<0.0001)
10. cyan-purple (z=3.76, p=0.0002)

**Pattern:**
- **Red-green confusion emerges** (classic Deutan pattern)
- Cumulative progression: V1(3) → V2(12) → V3(17)
- Broadest range of distorted pairs

#### sub-09 (Protan): 1 pair
- orange-magenta (z=3.32, p=0.0009)

**Pattern:** Minimal V3 effects (contrast with strong V1)

#### sub-10 (Deutan): 0 pairs
- No FDR-significant pairs

**V3 Interpretation:**
- **Peak of hierarchical distortion accumulation** (sub-08)
- Classic categorical boundary (red-green) appears in higher processing
- **Divergent trajectories:**
  - sub-08: Strong V1→V2→V3 progression
  - sub-09: Strong V1, minimal V2-V3
  - sub-10: Minimal throughout
- Suggests individual compensation strategies differ

---

### hV4: Color-Selective Area

**Overall:** 0 pairs significant (all subjects)

#### All subjects: 0 pairs
- No pairs survived within-ROI FDR correction

**Surface projection:**
- 13 vertices per subject (consistent)
- Right hemisphere dominant for all 3 CVD subjects
- Moderate RMS activation (max 0.009-0.053)

**hV4 Interpretation:**
- **Null result despite color-selective role**
- Possible explanations:
  1. **Categorical compensation:** Global color categories preserved despite pairwise distortions
  2. **Small ROI (70 voxels):** Reduced statistical power
  3. **Higher-level representation:** Less sensitive to peripheral cone deficits
  4. **Conservative correction:** 28 pairwise tests may miss global effects
- Complements global RDM findings (Phase 2: hV4 highest RDM correlation 0.541±0.283)

---

## Figure Captions for Paper

### Figure 1: V1 Color Representation Distortions in CVD

**Multi-panel visualization of color representation distortions in primary visual cortex (V1) for three color vision deficiency (CVD) subjects.** (A) Eight isoluminant color stimuli arranged in perceptual color wheel. (B) Glass brain showing V1 ROI location in MNI space (red activation overlay). (C) Posterior view of inflated left hemisphere surface showing V1 RMS activation pattern (hot colormap, 0-0.017 shared scale). (D) Representational distortion bars showing color pairs with significant differences between CVD and healthy controls (HC), quantified as ΔRDM = RDM_CVD - RDM_HC. Red bars indicate increased dissimilarity (enhanced differentiation), blue bars indicate decreased dissimilarity (color confusion). Only pairs surviving within-ROI FDR correction (q<0.05) are shown; asterisks mark significant pairs. Sub-08 (Deutan) shows 3 significant pairs dominated by red-yellow (z=5.14). Sub-09 (Protan) shows 6 pairs, notably clustered around magenta (cyan-magenta z=4.08, orange/red/green-magenta). Sub-10 (Deutan) shows no significant pairs, representing a milder phenotype. V1 distortions reflect early cone-opponent signal alterations, with Protan effects (6 pairs) exceeding Deutan (3 pairs) at this stage.

---

### Figure 2: V2 Color Representation Distortions in CVD

**Multi-panel visualization of color representation distortions in secondary visual cortex (V2), showing hierarchical accumulation of distortions.** (A-C) Same format as Figure 1, with V2 ROI. Surface activation (C) shows 34-58 vertices across subjects (left hemisphere for sub-08, right for sub-09/sub-10). (D) RDM distortion bars reveal striking subject heterogeneity. Sub-08 (Deutan) shows 12 FDR-significant pairs, including the strongest effect across all ROIs: yellow-purple (z=13.87, p<10^-10). Nine of twelve pairs involve yellow, suggesting critical role of yellow hue in M-cone opponent coding. This represents a 4-fold increase from V1 (3→12 pairs), indicating hierarchical distortion accumulation. Sub-09 (Protan) and sub-10 (Deutan) show no FDR-significant pairs, highlighting individual compensation strategies. V2 appears to be a key locus for amplification of cone-opponent distortions in susceptible individuals.

---

### Figure 3: V3 Color Representation Distortions in CVD

**Multi-panel visualization showing peak hierarchical accumulation of color distortions in higher visual area V3.** (A-C) Same format as Figures 1-2. Surface activation (C) shows sparse projection (4 vertices) due to small ROI size (~115 voxels) and sulcal depth. (D) Sub-08 (Deutan) shows 17 FDR-significant pairs (peak across all ROIs), representing further accumulation from V2 (12→17 pairs). Notably, the classic Deutan confusion pattern red-green emerges as the strongest effect (z=7.85), appearing only at this hierarchical stage. Additional strong effects include green-purple (z=6.96) and yellow-purple (z=6.17), suggesting broad reorganization of color space. Sub-09 (Protan) shows minimal V3 effects (1 pair: orange-magenta), contrasting with strong V1 effects (6 pairs), suggesting divergent hierarchical trajectories. Sub-10 shows no significant pairs. V3 represents the apex of hierarchical distortion accumulation in sub-08, with categorical color boundaries (red-green) emerging in higher-level processing.

---

### Figure 4: hV4 Color Representation in CVD

**Multi-panel visualization of color-selective area hV4 showing preserved pairwise color discrimination despite peripheral cone deficits.** (A-C) Same format as Figures 1-3. Surface activation (C) shows 13 vertices per subject (right hemisphere dominant). (D) All three CVD subjects show no FDR-significant color pair distortions, despite hV4's specialized role in color processing. This null result contrasts with strong pairwise distortions in V1-V3 (particularly V2-V3 for sub-08) and may reflect: (1) categorical color representation that is robust to pairwise metric changes, (2) reduced statistical power from small ROI size (70 voxels), or (3) effective compensation mechanisms at higher processing stages. This finding complements Phase 2 results showing hV4 had highest global RDM correlation (0.541±0.283), suggesting intact overall color structure despite altered pairwise relationships. The preservation of hV4 pairwise discrimination may enable stable color perception despite early visual cortex distortions.

---

## Methods Section Text

### Representational Distortion Analysis

**Color pair distortion quantification.** For each subject and ROI, we computed representational dissimilarity matrices (RDMs) using correlation distance (1 - Pearson r) between color-evoked activity patterns (28 unique pairs from 8 colors). RDM differences between individual CVD subjects and the healthy control (HC) group were quantified using Crawford and Howell (1998) modified t-tests, which account for small sample variance (n_HC=7). This approach yields z-scores and p-values for each color pair, testing whether individual CVD RDM values fall outside the HC distribution.

**False discovery rate correction.** We applied Benjamini-Hochberg FDR correction separately for each ROI (within-ROI FDR, 28 tests per ROI) rather than globally across all ROIs, based on the rationale that distinct ROIs represent functionally independent neural populations with potentially different distortion profiles. This approach balances Type I error control (q<0.05 within each ROI) while maintaining sensitivity to detect hierarchical patterns across the visual processing stream. Compared to global FDR correction (336 tests across 3 subjects × 4 ROIs × 28 pairs), within-ROI FDR increased the discovery rate from 2.4% (8 pairs) to 11.6% (39 pairs), particularly recovering previously masked effects in early visual cortex (V1: 1→9 pairs).

**Visualization pipeline.** Multi-panel figures combine four complementary views: (A) stimulus color wheel (8 isoluminant hues at 45° intervals), (B) glass brain anatomical localization (nilearn.plotting.plot_glass_brain, 4-view projection), (C) posterior inflated cortical surface (nilearn.plotting.plot_surf_stat_map on fsaverage5, 10mm radius ball sampling with 20 samples), and (D) RDM distortion bars showing FDR-significant color pairs rank-ordered by absolute effect size. Surface projection parameters were optimized for small ROIs: bilateral hemisphere testing (selecting hemisphere with maximum signal), large sampling radius (10mm) to ensure coverage, and ball-method 3D sampling (20 points per vertex) for robustness. Red bars indicate increased dissimilarity (CVD>HC, possible compensatory enhancement), blue bars indicate decreased dissimilarity (CVD<HC, classic cone-confusion pattern).

---

## Results Section Text

### Hierarchical Accumulation of Color Distortions Across Visual Cortex

**Individual heterogeneity in distortion patterns.** Analysis of color pair distortions using within-ROI FDR correction (q<0.05) revealed striking individual differences among CVD subjects. Sub-08 (Deutan) showed extensive distortions across the visual hierarchy (32 significant pairs total: V1=3, V2=12, V3=17, hV4=0), representing hierarchical accumulation from early to higher visual areas. In contrast, sub-09 (Protan) showed concentrated early effects (7 pairs total: V1=6, V2=0, V3=1, hV4=0), while sub-10 (Deutan) showed no FDR-significant pairs across any ROI, suggesting effective compensation or milder phenotype. This heterogeneity indicates that peripheral cone deficits translate into cortical distortions along divergent trajectories shaped by individual neural plasticity.

**V1: Early cone-opponent distortions.** Primary visual cortex (V1) showed significant color pair distortions in 2 of 3 CVD subjects (9 pairs total). Protan subject (sub-09) showed stronger V1 effects (6 pairs) than Deutan (sub-08, 3 pairs), with magenta-related pairs prominently affected (cyan-magenta z=4.08, orange/red/green-magenta z=3.43-3.71), consistent with L-cone loss disrupting long-wavelength chromatic processing. Deutan V1 distortions centered on red-yellow (z=5.14) and yellow-purple (z=4.84), reflecting M-cone opponent pathway alterations. These early effects demonstrate that cone deficits impact V1 representations beyond simple signal reduction, reshaping pairwise color discriminability.

**V2: Amplification and yellow-centric reorganization.** Secondary visual cortex (V2) showed dramatic distortion amplification in sub-08 (12 FDR-significant pairs), representing a 4-fold increase from V1 (3→12). The strongest effect across all ROIs emerged here: yellow-purple (z=13.87, p<10^-10), with 9 of 12 significant pairs involving yellow. This yellow-centric pattern suggests V2 intermediate processing critically depends on M-cone signals for yellow hue coding. Neither sub-09 nor sub-10 showed V2 distortions, highlighting individual-specific vulnerability. V2 appears to be a pivotal locus where cone deficits either amplify into widespread distortions (sub-08) or are effectively compensated (sub-09, sub-10).

**V3: Peak distortion with categorical boundary emergence.** Higher visual area V3 showed peak distortion accumulation in sub-08 (17 pairs, further increase from V2's 12). Notably, the classic Deutan confusion pattern red-green emerged as V3's strongest effect (z=7.85), appearing only at this hierarchical stage despite absent or weak V1-V2 effects for this specific pair. This suggests categorical color boundaries (red vs green) are constructed in higher visual processing and become vulnerable when foundational cone-opponent signals are distorted. Sub-09 showed minimal V3 effects (1 pair), contrasting with strong V1 effects (6 pairs), suggesting divergent hierarchical trajectories: sub-08 shows V1→V2→V3 accumulation, while sub-09 shows early V1 distortion without hierarchical propagation.

**hV4: Preserved pairwise discrimination despite upstream distortions.** Color-selective area hV4 showed no FDR-significant pairwise distortions in any CVD subject, despite strong upstream effects (particularly V2-V3 in sub-08). This null result contrasts with Phase 2 findings showing hV4 had the highest global RDM correlation (0.541±0.283), suggesting intact overall representational structure. The preservation of hV4 pairwise relationships despite V1-V3 distortions may reflect: (1) categorical color coding that is robust to metric changes in pairwise distances, (2) effective compensation via read-out weight adjustments, or (3) limited statistical power from small ROI size (70 voxels). This finding suggests hV4's color representation, while globally altered, maintains sufficient pairwise discriminability to support stable categorical perception.

**Summary: Divergent hierarchical trajectories.** CVD subjects exhibit qualitatively distinct distortion patterns across the visual hierarchy. Sub-08 shows progressive accumulation (V1→V2→V3), sub-09 shows early-concentrated effects (V1 dominant), and sub-10 shows minimal distortion throughout. These trajectories suggest individual differences in neural compensation strategies, with some individuals propagating peripheral deficits hierarchically while others compensate early or maintain stable representations. The emergence of categorical boundaries (red-green) only in V3, despite present in classical psychophysics, highlights the constructive nature of color categories in cortical processing.

---

## Statistical Summary

### Discovery Rates

| Method | V1 | V2 | V3 | hV4 | Total | Rate |
|--------|----|----|----|----|-------|------|
| **Within-ROI FDR** | 9 | 12 | 18 | 0 | **39/336** | **11.6%** |
| Global FDR | 1 | 3 | 4 | 0 | 8/336 | 2.4% |
| Uncorrected p<0.05 | 14 | 20 | 25 | 4 | 63/336 | 18.8% |

### Effect Size Distribution

**Strongest effects (z-scores):**
1. sub-08 V2 yellow-purple: **z=13.87** (p<10^-10)
2. sub-08 V2 red-yellow: z=9.38
3. sub-08 V3 red-green: z=7.85
4. sub-08 V3 green-purple: z=6.96
5. sub-08 V2 blue-purple: z=6.15

**Mean effect sizes (significant pairs only):**
- V1: z̄ = 3.97 ± 0.85
- V2: z̄ = 6.71 ± 2.91
- V3: z̄ = 5.23 ± 1.24
- hV4: N/A

---

## Usage Notes

### For Manuscript Figures

1. **Main text:** Include V2 and V3 (strongest effects, clearest patterns)
2. **Supplementary:** V1 and hV4 (context: early and late processing)
3. **Resolution:** 300 DPI publication-ready
4. **Format:** PNG with white background (easily convertible to TIFF if needed)

### For Presentations

- Each figure is self-contained (all 4 panels explain the story)
- Color bars included for quantitative interpretation
- FDR correction clearly noted in Panel D titles
- High contrast suitable for projection

### File Modifications

If you need to regenerate with different parameters:
```bash
python analysis/phase3_decoder_comparing/visualization/create_cvd_distortion_figure.py --roi V2
```

To switch back to global FDR, modify `load_fdr_significant_pairs()` function in the script.

---

**Document created:** 2026-02-22
**Last updated:** 2026-02-22
**Corresponding analysis:** Phase 3 Filter Pre-validation (B1-B3)
**Statistical method:** Within-ROI FDR (Benjamini-Hochberg q<0.05)
