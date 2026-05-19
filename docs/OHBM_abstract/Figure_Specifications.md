# OHBM Abstract Figure Specifications

## Overview
- **Maximum figures allowed**: 2
- **Purpose**: Visually communicate experimental design, analysis pipeline, and main findings
- **Style**: Clear, professional, following Brouwer & Heeger (2009) as template

---

## Figure 1: Experimental Design, Analysis Pipeline, and Main Results

### Layout
4-panel figure arranged as: [A | B]
                            [C | D]

### Panel A: Experimental Paradigm
**Title**: "Experimental Design"

**Content**:
1. **Top section**: Color stimulus display
   - Show 8 isoluminant colors evenly spaced on color wheel
   - Display in CIE L*a*b* space visualization
   - Label: "8 isoluminant colors (L*=54, radius=38)"
   - Include neutral gray in center

2. **Middle section**: Trial timeline
   - Temporal diagram showing:
     - Colored background presentation (1.5 s)
     - Inter-stimulus interval (3-6 s, variable)
   - Arrow indicating trial progression

3. **Bottom section**: RSVP attention task
   - Show fixation with letter stream
   - Highlight target detection task (white K → black K)
   - Label: "RSVP attention control (400 ms/letter)"

**Dimensions**: ~25% of figure width, full height left column

---

### Panel B: Analysis Pipeline
**Title**: "Analysis Pipeline"

**Content**: Flowchart with 5 stages (top to bottom):

1. **Preprocessing** (fMRIPrep icon/box)
   - "fMRIPrep v20.2.0"
   - "Field map correction"
   - "MNI152 2mm"

2. **ROI Definition** (brain icon showing visual cortex)
   - "V1, V2, V3, hV4"
   - "Wang et al. (2015) atlas"
   - Small brain image with colored ROIs

3. **GLM Beta Estimation** (design matrix visualization)
   - "Single-trial beta maps"
   - Small design matrix graphic

4. **Feature Selection** (voxel selection visualization)
   - "ANOVA F-test"
   - "k=1-200 voxels (optimized)"

5. **Forward Encoding Model** (basis function diagram)
   - Show 6 half-wave rectified sinusoids
   - "Leave-one-run-out CV"
   - Arrow to two outputs:
     - "Classification accuracy"
     - "Reconstruction error"

**Dimensions**: ~25% of figure width, full height right column

---

### Panel C: Color Reconstruction Examples
**Title**: "Color Reconstruction: Representative Subjects"

**Content**: 2×4 grid showing circular reconstruction plots

**Layout**:
```
         V1        V2        V3        hV4
HC:    [plot]    [plot]    [plot]    [plot]
CVD:   [plot]    [plot]    [plot]    [plot]
```

**Each circular plot shows**:
- Circular color space (0-360°)
- Presented colors (filled circles on perimeter)
- Reconstructed colors (open circles connected to presented)
- Arrows showing reconstruction error
- Central chance performance reference (dashed circle at 90°)

**Color coding**:
- HC plots: Blue border
- CVD plots: Orange/red border

**Annotations**:
- Error values on each plot: "Error: XX.X°"
- Accuracy values: "Acc: XX.X%"

**Representative subjects**:
- HC: sub-06 (best performer)
- CVD: sub-08 (representative CVD)

**Dimensions**: ~50% of figure width, ~40% of total height

---

### Panel D: Group Comparison Results
**Title**: "CVD vs. Healthy Controls: No Significant Differences"

**Content**: Two side-by-side bar plots

**Left subplot**: Reconstruction Error
- X-axis: V1, V2, V3, hV4
- Y-axis: Reconstruction Error (degrees, 0-100°)
- Bars: HC (blue), CVD (orange/red), side by side
- Error bars: Standard deviation
- Horizontal dashed line at 90° (chance level)
- Horizontal dashed line at 45° (good performance reference)
- Annotations: "n.s." above each ROI pair with p-values

**Right subplot**: Classification Accuracy
- X-axis: V1, V2, V3, hV4
- Y-axis: Classification Accuracy (%, 0-80%)
- Bars: HC (blue), CVD (orange/red), side by side
- Error bars: Standard deviation
- Horizontal dashed line at 12.5% (chance level)
- Horizontal dashed line at 50% (good performance reference)
- Annotations: "n.s." above each ROI pair with p-values

**Statistical annotations format**:
- Above each pair: "n.s." or "p=.XXX"
- Effect sizes in small text if space permits: "d=X.XX"

**Legend**:
- HC (n=6): Blue bars
- CVD (n=3): Orange/red bars

**Dimensions**: ~50% of figure width, ~40% of total height

---

### Figure 1 Overall Specifications

**Size**: Standard OHBM format (likely ~180mm width for full page)

**Color scheme**:
- HC: Blue (#1f77b4)
- CVD: Orange/Red (#ff7f0e)
- ROI colors (if needed):
  - V1: Light blue
  - V2: Green
  - V3: Yellow
  - hV4: Red

**Fonts**:
- Panel labels (A, B, C, D): Bold, 14pt
- Titles: Bold, 12pt
- Axis labels: 10pt
- Tick labels: 8pt
- Annotations: 8pt

**File format**:
- High resolution (300 DPI minimum)
- PDF or TIFF format
- RGB color space

---

## Figure 2: Statistical Validation and Control Analyses

### Layout
2×2 panel arrangement: [A | B]
                        [C | D]

### Panel A: Permutation Test Results
**Title**: "Decoding Above Chance: Permutation Test"

**Content**: Histogram-style plot for each ROI (4 subplots)

**Each subplot shows**:
- X-axis: Classification accuracy (%)
- Y-axis: Frequency (number of permutations)
- Gray histogram: Null distribution from permuted labels (1000 iterations)
- Vertical blue line: Observed HC mean accuracy
- Vertical red line: Observed CVD mean accuracy
- Shaded regions: 95% confidence interval of null distribution
- P-value annotation: "p < .001" (or actual value)

**Layout**: 2×2 grid of subplots (V1, V2, V3, hV4)

**Dimensions**: ~50% width, ~45% height

---

### Panel B: Feature Selection Robustness
**Title**: "Optimal Voxel Selection Across Subjects"

**Content**: Box plots or violin plots

- X-axis: ROI (V1, V2, V3, hV4)
- Y-axis: Optimal k (number of voxels, 1-200)
- Separate box plots for HC (blue) and CVD (orange)
- Individual data points overlaid as dots
- Median line, quartiles, and whiskers

**Annotations**:
- Median k values labeled
- No significant group difference indicators

**Dimensions**: ~25% width, ~45% height

---

### Panel C: Individual Subject Performance
**Title**: "Individual Variability: All CVD Within HC Range"

**Content**: Scatter plot with error bars

- X-axis: ROI (V1, V2, V3, hV4)
- Y-axis: Classification Accuracy (%)
- HC subjects: Blue points with subject IDs
- CVD subjects: Large orange/red points with subject IDs (sub-08, sub-09, sub-10)
- HC range shaded as light blue band (min-max or ±1 SD)
- Horizontal dashed line at chance (12.5%)

**Annotations**:
- Individual CVD subject labels
- "All CVD within HC range" text annotation

**Dimensions**: ~25% width, ~45% height

---

### Panel D: Hierarchical Pattern Analysis
**Title**: "Visual Hierarchy: Consistent Pattern Across Groups"

**Content**: Line plot showing hierarchical effects

- X-axis: Visual hierarchy (V1 → V2 → V3 → hV4)
- Y-axis (left): Reconstruction Error (degrees)
- Y-axis (right): Classification Accuracy (%)
- HC line: Blue with error ribbons (±SEM)
- CVD line: Orange/red with error ribbons (±SEM)
- Both metrics on same plot (dual y-axes) or two subplots

**Pattern to show**:
- Increasing reconstruction error: V1 < V2 < V3 ≈ hV4
- Decreasing classification accuracy: V1 > V2 > V3 ≈ hV4
- Parallel lines (no group × ROI interaction)

**Annotations**:
- "Hierarchical decrease in performance"
- "No group × ROI interaction" or "p > .05 for all interactions"

**Dimensions**: ~50% width, ~45% height

---

### Figure 2 Overall Specifications

**Size**: Standard OHBM format (~180mm width)

**Color scheme**: Same as Figure 1
- HC: Blue (#1f77b4)
- CVD: Orange/Red (#ff7f0e)
- Null distribution: Gray (#7f7f7f)

**Fonts**: Same specifications as Figure 1

**File format**:
- High resolution (300 DPI minimum)
- PDF or TIFF format
- RGB color space

---

## Implementation Notes

### Data Sources

**Figure 1**:
- Panel A: Based on final_IRB.pdf experimental description
- Panel B: From GUIDE_to_classify_reconstruct.md and GUIDE_to_fMRIprep.md
- Panel C: Individual subject data from FULL_STATISTICS_SUMMARY.md (lines 73-99)
  - HC: Use sub-06 (best: V1 83.3%, 27.4°)
  - CVD: Use sub-08 (representative: V1 54.2%, 40.2°)
- Panel D: Group statistics from FULL_STATISTICS_SUMMARY.md (lines 29-59)

**Figure 2**:
- Panel A: Permutation test results (need to generate or extract from logs/permutation_analysis/)
- Panel B: Feature selection k values across subjects (from ANOVA RFE results)
- Panel C: Individual subject data from FULL_STATISTICS_SUMMARY.md (lines 73-99)
- Panel D: Same data as Panel D in Figure 1, but reorganized to show hierarchy

### Python Visualization Libraries

Recommended tools:
- **matplotlib**: Core plotting
- **seaborn**: Statistical visualizations
- **nilearn**: Brain visualizations for Panel B
- **numpy/scipy**: Circular statistics for reconstruction plots

### Code Structure

Create separate scripts:
1. `create_figure1_ohbm.py` - Main experimental results
2. `create_figure2_ohbm.py` - Statistical validation
3. `figure_utils.py` - Shared plotting functions (circular plots, color schemes, etc.)

### Quality Checks

Before finalizing:
- [ ] All text is legible at print size
- [ ] Color scheme is colorblind-friendly (ironic but important!)
- [ ] All statistical values match source documents exactly
- [ ] Panel labels (A, B, C, D) are clear and consistent
- [ ] Figure legends are complete
- [ ] No overlapping text or elements
- [ ] All axis labels and titles are present
- [ ] Error bars are visible and distinguishable
- [ ] File size is reasonable (<5 MB per figure)

---

## Timeline for Figure Creation

**Estimated time per figure**: 2-3 hours including:
- Data extraction and organization: 30 min
- Plotting and layout: 60-90 min
- Refinement and quality checks: 30-45 min

**Recommended order**:
1. Figure 1 Panel D (simplest - bar plots with existing data)
2. Figure 1 Panel C (moderate - circular reconstruction plots)
3. Figure 1 Panels A & B (schematic diagrams - can use illustration tools)
4. Figure 2 (after Figure 1 complete, reuses some elements)

---

**Created**: 2025-12-14
**For**: OHBM 2026 Abstract Submission
**Author**: Jinil Kim et al.
