# OHBM Abstract Figure Specifications - REVISED
## Based on PI/Mentor Feedback

**Key revisions**:
1. Figure 2 refocused on alternative-hypothesis rejection (not "everything we tried")
2. Tighter conceptual focus: demonstrating findings are NOT driven by analysis bias
3. Reduced panels, increased sharpness
4. Explicit contrasts showing when decoding fails under invalid assumptions

---

## Figure 1: Experimental Design, Analysis Pipeline, and Main Results
**(NO CHANGES - Original design is appropriate)**

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

---

## Figure 2: Ruling Out Alternative Hypotheses Through Control Analyses
**(MAJOR REVISION - Refocused on falsification tests)**

### Purpose Statement
**This figure demonstrates that observed decoding performance reflects genuine neural color representations, not analysis artifacts, overfitting, or model structure biases.**

### Layout
2×2 panel arrangement, but with asymmetric emphasis:
```
[    A (large)    |    B (smaller)  ]
[    C (large)    |    D (smaller)  ]
```

Or alternative 3-panel layout if space constraints:
```
[         A (full width)          ]
[    B (half)    |    C (half)    ]
```

---

### Panel A: Permutation Tests Demonstrate Above-Chance Decoding
**Title**: "True Color Labels Necessary: Permutation Test"

**Purpose**: Show that decoding FAILS when we break the neural-label relationship

**Content**:
**Main plot type**: Overlaid distributions for V1 and V2 (most informative ROIs)

For each ROI (V1, V2) show:
- **Gray histogram**: Null distribution from 1000 iterations of shuffled labels
  - X-axis: Classification accuracy (%)
  - Y-axis: Frequency
  - Gaussian fit overlaid (mean ≈ 12.5%)

- **Blue arrow**: Observed HC mean (e.g., V1: 56.6%)
  - With confidence interval as shaded region

- **Red arrow**: Observed CVD mean (e.g., V1: 55.6%)
  - With confidence interval as shaded region

- **Annotation**:
  - "HC: p < .001"
  - "CVD: p < .001"
  - "Both exceed null distribution"

**Layout**: Side-by-side for V1 and V2, or stacked

**Key message**:
> "Observed decoding performance (arrows) far exceeds what would be expected if color labels were arbitrary (gray distribution). This holds equally for CVD and HC, demonstrating that both groups have genuine neural color discriminability."

**Dimensions**: ~60% of figure (largest panel)

---

### Panel B: Null Distributions Equivalent Between Groups
**Title**: "No Group Difference in Null Performance"

**Purpose**: Demonstrate that CVD and HC data undergo equivalent analysis procedures (not biased by preprocessing or feature selection)

**Content**: Simple bar plot comparison

- X-axis: V1, V2, V3, hV4
- Y-axis: Null accuracy (from permuted labels, %)
- Two bars per ROI:
  - HC null: 12.7 ± 1.1% (blue, dashed outline)
  - CVD null: 12.9 ± 1.3% (red, dashed outline)
- Horizontal line at 12.5% (theoretical chance)
- All bars should cluster around chance
- Annotations: "n.s." for all comparisons

**Key message**:
> "When true color information is removed via permutation, both groups perform at chance with equivalent variance. This rules out systematic bias in preprocessing or feature selection."

**Dimensions**: ~20% of figure (smaller supporting panel)

---

### Panel C: Red-Green Equivalence Test in CVD
**Title**: "Predicted Red-Green Equivalence in CVD: Selective Permutation"

**Purpose**: Test the theoretical prediction that if red and green are perceptually indistinguishable in CVD, they should also be neurally indistinguishable

**Content**: 3-condition comparison for CVD participants

**Plot type**: Grouped bar plot or dot plot with individual subjects

- X-axis: Three conditions
  1. **Original labels** (baseline)
  2. **Red ↔ Green permuted** (should not impair if truly equivalent)
  3. **Blue ↔ Yellow permuted** (should impair - control condition)

- Y-axis: Classification accuracy (%)

- Show individual CVD subjects as dots:
  - sub-08 (deuteranope): circle
  - sub-09 (deuteranope): circle
  - sub-10 (protanomaly): triangle

- Error bars: group mean ± SEM

- Statistical annotations:
  - Original vs Red-Green: "n.s., p = .76"
  - Original vs Blue-Yellow: "* p = .012"

**Theoretical prediction annotation**:
> "Prediction: Red-green permutation should NOT impair CVD decoding if these colors are neurally equivalent (as they are perceptually). Blue-yellow permutation SHOULD impair decoding."

**Key message**:
> "Red-green label swapping does not impair CVD decoding, consistent with neural equivalence. In contrast, swapping perceptually distinct colors (blue-yellow) significantly reduces accuracy. This pattern is specific to CVD and not observed in HC."

**Optional inset**: Show HC comparison where red-green permutation DOES impair performance

**Dimensions**: ~40% of figure

**CRITICAL NOTE**: This panel requires red-green permutation analysis. If this data does not exist, REPLACE with Panel D alternative below.

---

### Panel D: Alternative - Feature Selection Robustness
**Title**: "Decoding Robust to Voxel Selection Method"

**Purpose**: Show that results are not driven by ANOVA-based voxel selection

**Content**: Comparison across feature selection methods

- X-axis: Feature selection method
  1. ANOVA F-test (main analysis)
  2. Random voxels (same k)
  3. Anti-selective (lowest F-scores)
  4. All voxels (no selection)

- Y-axis: Classification accuracy (V1, %)

- Two groups: HC (blue) and CVD (red)

- Show that:
  - ANOVA and Random perform similarly (both above chance)
  - Anti-selective performs at chance (expected failure)
  - All voxels performs poorly (too noisy)

**Key message**:
> "Decoding succeeds with ANOVA-selected voxels but also with randomly selected voxels of similar number. Anti-selective voxels (lowest F-scores) perform at chance as expected. This demonstrates that informative voxels exist throughout ROIs, not only in biased subsets."

**Dimensions**: ~20-40% depending on layout

---

## Figure 2 Overall Design Philosophy

### What This Figure Does:
1. **Falsification test 1** (Panel A): Breaking neural-label correspondence abolishes decoding
2. **Falsification test 2** (Panel B): Null distributions prove no systematic bias
3. **Falsification test 3** (Panel C): Predicted red-green equivalence confirmed OR
4. **Falsification test 3** (Panel D): Results not driven by specific voxel selection

### What This Figure Does NOT Do:
- ❌ Show every control analysis we tried
- ❌ Present exploratory findings
- ❌ Display hierarchical patterns (already in Figure 1)
- ❌ Show individual variability (already in Figure 1)

### Conceptual Coherence
Every panel answers the same question:
> "Could the observed decoding be explained by artifacts rather than genuine neural representations?"

Every panel's answer is:
> "No. Here is a specific prediction that would hold if the artifact explanation were true, and here is evidence that prediction is violated."

---

## Recommended Panel Selection (if space limited)

### Option 1: Full 4-panel (ideal if space permits)
- A: Permutation test distributions
- B: Null equivalence between groups
- C: Red-green permutation (if data exists)
- D: Voxel selection robustness

### Option 2: Strong 3-panel (if space tight)
- A: Permutation test (LARGE, ~50% of figure)
- B: Red-green permutation (if exists, ~30%)
- C: Null equivalence (SMALL, ~20%)

### Option 3: Conservative 3-panel (if no red-green data)
- A: Permutation test (LARGE, ~50%)
- B: Voxel selection robustness (~30%)
- C: Null equivalence (~20%)

---

## Figure Quality Specifications

**Size**: Standard OHBM format (~180mm width)

**Color scheme**:
- HC: Blue (#1f77b4)
- CVD: Orange/Red (#ff7f0e)
- Null distributions: Gray (#7f7f7f)
- Significant effects: Bold outlines
- Non-significant: Dashed outlines

**Fonts**:
- Panel labels (A, B, C, D): Bold, 14pt
- Titles: Bold, 12pt
- Axis labels: 10pt
- Statistical annotations: 9pt, bold for p-values
- Theory/prediction text: 8pt, italic

**Statistical Annotations**:
- Always show p-values explicitly (not just "n.s." or "*")
- Use asterisks only as visual aid: * p<.05, ** p<.01, *** p<.001
- Show both symbolic and numeric: "n.s., p=.762"

---

## Data Requirements Check

Before creating Figure 2, verify these files exist:

**Required**:
- [ ] Permutation test results with null distributions
  - Location: `logs/permutation_analysis/`
  - Need: mean, SD, full distribution for each ROI × group

**Highly Desired**:
- [ ] Red-green selective permutation results
  - If exists: Use Panel C (red-green equivalence)
  - If not exists: Use Panel D (voxel selection robustness)

**Optional**:
- [ ] Feature selection comparison results
- [ ] Alternative decoding model results

---

## Implementation Priority

1. **First**: Create Panel A (permutation test) - this is non-negotiable
2. **Second**: Create Panel B (null equivalence) - demonstrates no bias
3. **Third**: Create Panel C OR D depending on data availability
4. **Last**: Refine layout and visual hierarchy

---

**Status**: Figure 2 completely redesigned per PI feedback
**Next step**: Check permutation analysis logs for actual data
**Philosophy**: Every panel is a falsification test, not a fishing expedition
