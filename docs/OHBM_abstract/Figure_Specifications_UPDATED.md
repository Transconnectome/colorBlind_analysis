# OHBM Abstract Figure Specifications - UPDATED
## Based on PI/Mentor Feedback + Latest Revisions

**Latest revisions** (2025-12-15):
1. Forward encoding pipeline visualization updated to match stimulus color space style
2. Figure 2 completely redesigned with 4 panels focusing on validation
3. Terminology unified: HC → HC throughout all figures
4. Boxplot-based visualization for group comparisons
5. Visual explanation of permutation methodology

---

## Figure 1: Experimental Design, Analysis Pipeline, and Main Results
**(UPDATED - Panel B Stage 5 visualization modified)**

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
   - **Left side**: Show 6 half-wave rectified sinusoids
   - "Leave-one-run-out CV"
   - **Right side**: **UPDATED - Circular color space visualization**
     - **Match Stimulus_Colors_Lab_Space style**:
       - Circular plot with 0-360° labels
       - **Outer perimeter**: 8 filled circles in true stimulus colors (presented colors)
       - **Inner region**: Open/hollow circles connected to perimeter (predictions)
       - **Arrows**: Connect each presented color (perimeter) to predicted color (inner)
       - **Example annotation**: Arrow showing ~90° error with label "90° predicted"
       - **Visual style**: Same as Panel A stimulus display but with prediction overlay
     - Two outputs indicated:
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
- CVD: sub-08 (representative deuteranope)

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

**TERMINOLOGY CHECK**: ✅ All instances of "HC" replaced with "HC"

---

## Figure 2: Validation Through Permutation Testing
**(COMPLETELY REDESIGNED - 4-panel layout)**

### Purpose Statement
**This figure demonstrates that observed decoding performance reflects genuine neural color representations through permutation validation.**

### Layout
4-panel figure arranged vertically or in 2×2 grid:
```
[    A (skip)                          ]
[    B (Boxplot comparison)            ]
[    C (Permutation methodology)       ]
[    D (Permutation results)           ]
```

---

### Panel A: [SKIPPED AS REQUESTED]

---

### Panel B: Group Comparison - Boxplot Visualization
**Title**: "Decoding Accuracy Across ROIs: HC vs. CVD"

**Purpose**: Show distribution of accuracy values across groups and ROIs

**Content**: Boxplot visualization

**Plot specifications**:
- **X-axis**: ROI (V1, V2, V3, hV4)
- **Y-axis**: Classification Accuracy (%, 0-80%)
- **For each ROI**: Two boxplots side by side
  - HC (blue boxes, n=6)
  - CVD (orange/red boxes, n=3)
- **Boxplot components**:
  - Box: IQR (25th-75th percentile)
  - Central line: Median
  - Whiskers: 1.5 × IQR
  - Individual points: All subject values (overlaid as dots)
  - **Mean annotation**: Display mean value on each box (e.g., "Mean: 59.6%")

**Statistical annotations**:
- Above each ROI pair: Curved line connecting two boxes
- On the line: "n.s." or "p=.XXX"
- Format examples:
  - "n.s." (for non-significant)
  - "p=.045*" (for marginally significant)
  - "p<.001***" (for highly significant)

**Reference lines**:
- Horizontal dashed line at 12.5% (chance level) - gray
- Horizontal dashed line at 50% (good performance) - light gray

**Color scheme**:
- HC: Blue (#1f77b4)
- CVD: Orange (#ff7f0e)

**Dimensions**: ~35% of figure height

**TERMINOLOGY CHECK**: ✅ Uses "HC" not "HC"

---

### Panel C: Permutation Methodology Illustration
**Title**: "Permutation Testing: Breaking Color-Label Correspondence"

**Purpose**: Visual explanation of how permutation disrupts true color labels

**Content**: Schematic diagram showing label shuffling

**Visualization components**:

1. **Original (True) Labels** (left side):
   - Show timeline of runs (e.g., Run 1, Run 2, Run 3, Run 4)
   - Each run shows colored stimuli with correct labels
   - Example: Red stimulus → "Red" label (✓)
            Green stimulus → "Green" label (✓)
   - Arrow labeled "Correct correspondence"

2. **Permuted Labels** (right side):
   - Same timeline of runs
   - **Half of runs have swapped labels** (e.g., Run 1 & 2)
   - Example: Red stimulus → "Green" label (✗)
            Green stimulus → "Red" label (✗)
   - Other half remains correct (Run 3 & 4)
   - Arrow labeled "Shuffled correspondence"

3. **Visual indicators**:
   - Use color boxes for stimuli (actual RGB colors)
   - Use text labels ("Red", "Green", etc.)
   - Crossed arrows (⤫) showing label swaps
   - Check marks (✓) for correct, X marks (✗) for incorrect

4. **Annotation box**:
   > "If decoding relies on true color-neural mapping, permutation should impair performance"

**Color scheme**:
- Red/Green highlighted as example colors being swapped
- Use all 8 colors in full diagram

**Dimensions**: ~25% of figure height

---

### Panel D: Permutation Test Results - Group Comparison
**Title**: "Permutation Increases Error: Evidence of Valid Decoding"

**Purpose**: Show that permutation impairs performance, validating genuine decoding

**Content**: Grouped bar plot with error change visualization

**Plot specifications**:
- **X-axis**: Two groups (HC, CVD)
- **Y-axis**: Reconstruction Error (degrees)
  - **IMPORTANT**: Add downward arrow (↓) near axis label
  - Annotation: "Lower is better ↓"
  - Range: 70-90°

**For each group**:
- **Two bars side by side**:
  1. **Original** (solid fill)
     - HC: Blue (#1f77b4)
     - CVD: Orange (#ff7f0e)
  2. **Permuted** (striped/hatched fill, same colors)
     - HC: Blue with hatching
     - CVD: Orange with hatching

**Error increase visualization**:
- **Red curved arrow** between Original and Permuted bars
- Arrow points from Original → Permuted (upward, showing error increase)
- Arrow label: "+3.86°" (HC) and "+4.70°" (CVD)
- **Effect size** annotation: "d=0.27" (HC), "d=0.42" (CVD)

**Error bars**: Standard deviation or SEM

**Statistical annotations**:
- Above each group's comparison:
  - HC: "p=0.031*"
  - CVD: "p=0.011*"
- Legend: "* p < 0.05 (significant)"

**Data values** (from permutation results):
- HC: Original 78.0° → Permuted 81.9° (Δ +3.86°)
- CVD: Original 79.0° → Permuted 83.7° (Δ +4.70°)

**Key message annotation**:
> "Both groups show significant error increase when labels are shuffled, confirming genuine color decoding"

**Color scheme**:
- Original bars: Solid colors (blue/orange)
- Permuted bars: Hatched/striped colors (blue/orange)
- Error arrows: Red (#d62728)
- Significance stars: Black

**Dimensions**: ~40% of figure height

**TERMINOLOGY CHECK**: ✅ Uses "HC" not "HC"

---

## Figure 2 Design Philosophy

### What This Figure Does:
1. **Panel B**: Shows accuracy distributions with no significant group differences
2. **Panel C**: Explains permutation methodology visually
3. **Panel D**: Demonstrates permutation validation with significant error increase in both groups

### What This Figure Does NOT Do:
- ❌ Show null distributions (removed per request)
- ❌ Show every control analysis
- ❌ Present exploratory findings

### Conceptual Coherence
> "Permutation testing validates that observed decoding reflects true color-neural mappings, equally in both HC and CVD groups"

---

## Terminology Consistency Check

**Throughout ALL figures**:
- ✅ "HC" (Healthy Controls) - ALWAYS
- ❌ "HC" - NEVER
- ✅ "CVD" (Color Vision Deficiency)

**Search and replace completed**:
- Figure 1 Panel C: HC vs. CVD ✓
- Figure 1 Panel D: HC vs. CVD ✓
- Figure 2 Panel B: HC vs. CVD ✓
- Figure 2 Panel D: HC vs. CVD ✓

---

## Figure Quality Specifications

**Size**: Standard OHBM format (~180mm width)

**Color scheme**:
- HC: Blue (#1f77b4)
- CVD: Orange/Red (#ff7f0e)
- Permuted: Hatched versions of above
- Error arrows: Red (#d62728)
- Null/reference: Gray (#7f7f7f)
- Significant effects: Bold outlines
- Non-significant: Regular outlines

**Fonts**:
- Panel labels (A, B, C, D): Bold, 14pt
- Titles: Bold, 12pt
- Axis labels: 10pt
- Statistical annotations: 9pt, bold for p-values
- Theory/prediction text: 8pt, italic

**Statistical Annotations**:
- Always show p-values explicitly
- Use asterisks as visual aid: * p<.05, ** p<.01, *** p<.001
- Show both symbolic and numeric: "p=0.031*"

---

## Data Requirements Check

Before creating figures, verify these files exist:

**Figure 1**:
- [x] Representative subject reconstruction plots (sub-06, sub-08)
- [x] Group comparison statistics
- [ ] Updated pipeline diagram with circular color space visualization

**Figure 2**:
- [x] Permutation test results with error increase
  - Location: `logs/permutation_analysis/`
  - HC: 78.0° → 81.9° (p=0.031)
  - CVD: 79.0° → 83.7° (p=0.011)
- [x] Accuracy distributions for boxplots (all subjects, all ROIs)
- [ ] Permutation methodology illustration (to be created)

---

## Implementation Priority

### Figure 1:
1. Update Panel B Stage 5 to match stimulus color space style
2. Verify all "HC" → "HC" terminology
3. Generate final reconstruction examples

### Figure 2:
1. Create Panel B boxplot (accuracy distributions)
2. Create Panel C permutation methodology illustration
3. Create Panel D permutation results with error increase
4. Verify all "HC" → "HC" terminology

---

## Key Changes Summary (2025-12-15)

1. **Forward Encoding Pipeline (Fig 1, Panel B)**:
   - Stage 5 right side: Circular color space now matches stimulus display style
   - Filled circles on perimeter (presented colors)
   - Open circles inside (predictions)
   - Arrows showing reconstruction error
   - Example: 90° prediction error labeled

2. **Figure 2 Complete Redesign**:
   - Panel A: Skipped
   - Panel B: Boxplot visualization (x=ROI, y=accuracy, HC vs CVD)
   - Panel C: Permutation methodology illustration
   - Panel D: Error increase from permutation (x=group, original vs permuted bars)

3. **Terminology Unified**:
   - All "HC" → "HC"
   - Verified across all figures and panels

---

**Status**: Specifications updated per latest requirements
**Next step**: Implement updated visualizations
**Philosophy**: Clear validation through permutation, consistent terminology
