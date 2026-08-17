# Gemini Nano Banana Prompts — PPT Diagrams

슬라이드별 다이어그램 프롬프트 모음. 각각 독립적으로 Gemini에 붙여넣으세요.

---

## Slide 2 — Overall Pipeline (아이콘/그림 버전)

```
Create a top-to-bottom scientific pipeline flowchart for an fMRI color vision research project. Publication quality, white background, 16:9 ratio. No 3D effects.

CRITICAL DESIGN PRINCIPLE: Replace text descriptions with ICONS and MINI-FIGURES wherever possible. Text should be limited to titles, labels, and key numbers only. Think "infographic" not "bullet-point list."

LAYOUT: Vertical flow, 5 main boxes connected by arrows. Phase 2a and 2b are side-by-side. Box 4 is highlighted (today's focus).

COLOR SCHEME:
- Box 0 (Data): light gray (#E8E8E8), dark gray border
- Box 1 (Phase 1): light blue (#D6EAF8), blue border (#2980B9)
- Box 2a/2b (Phase 2): light green (#D5F5E3), green border (#27AE60)
- Box 3 (Future Phase 1): light orange (#FDEBD0), THICK orange border (#E67E22), "★ TODAY" badge
- Box 4 (Future Phase 2): light purple (#E8DAEF), DASHED purple border (#8E44AD)

═══════════════════════════════════════════════════════════
BOX 0 — DATA (top, full width)
═══════════════════════════════════════════════════════════

Title: "Data Acquisition & Preprocessing"

VISUAL CONTENT (left to right, replacing all text):

[Icon 1] A small colorful HUE WHEEL with 8 distinct color dots around it
          (red, orange, yellow, green, cyan, blue, purple, magenta).
          Label below: "8 colors"

[Icon 2] 6 horizontal bars stacked vertically (like a film strip or timeline),
          each bar a slightly different shade of gray.
          Label below: "6 runs"

[Icon 3] A row of 10 PERSON SILHOUETTE icons:
          7 colored BLUE (HC), 3 colored RED (CVD).
          Label below: "7 HC + 3 CVD"

[Icon 4] A simplified BRAIN viewed from behind (occipital view),
          with 4 colored patches on the visual cortex:
          V1 (innermost, dark blue), V2 (next ring, medium blue),
          V3 (next, light blue), hV4 (outermost/ventral, orange).
          Label below: "V1 V2 V3 hV4"

[Icon 5] Small "fMRIPrep" logo or MRI scanner icon → arrow → "Procrustes" icon
          (two shapes being aligned/overlapped)

═══════════════════════════════════════════════════════════
BOX 1 — PHASE 1: Baseline Decoding
═══════════════════════════════════════════════════════════

Title: "Phase 1: Baseline Decoding"

VISUAL CONTENT (left to right, as a mini processing chain):

[Mini-fig A] A wavy BOLD time series signal (sine-like curve with a hemodynamic bump)
             Arrow →
[Mini-fig B] A small DESIGN MATRIX icon (rectangular grid, some cells colored)
             with label "GLM"
             Arrow →
[Mini-fig C] Two small voxel-pattern grids (like 2D heatmaps) being ROTATED
             to overlap each other, with a small curved arrow showing alignment.
             Label: "Procrustes"
             Arrow →
[Mini-fig D] A 3D data cube icon labeled "(6 × 8 × V)"
             representing the output tensor: runs × colors × voxels

Right side badge (small rounded rectangle):
  "RQ1: Discrimination? → ✓ YES"

═══════════════════════════════════════════════════════════
BOX 2a — PHASE 2a: SRM (left half)
═══════════════════════════════════════════════════════════

Title: "Phase 2a: SRM Group Comparison"

VISUAL CONTENT:

[Mini-fig] 7 small brain icons (blue, labeled "HC") with arrows converging
           into a single SHARED COORDINATE SYSTEM (a small 3D axis with k dimensions).
           Then 3 brain icons (red, "CVD") being PROJECTED into that same space
           with dashed arrows.

Below: 3 small person-profile cards showing individual results:
  - sub-09: "V1 p=.007*" (red highlight)
  - sub-08: "V2 p=.040*" (red highlight)
  - sub-10: "HC-like" (green, no highlight)

Badge: "RQ2"

═══════════════════════════════════════════════════════════
BOX 2b — PHASE 2b: Decoder Comparison (right half)
═══════════════════════════════════════════════════════════

Title: "Phase 2b: Decoder Comparison"

VISUAL CONTENT:

[Mini-fig top] Two small matrices side by side:
  Left matrix: a 6×8 grid with ONE ROW blanked out (dashed) → "LORO"
  Right matrix: an 8-color wheel with ONE COLOR blanked out (dashed "?") → "LOCO"

[Mini-fig bottom] A conceptual split:
  Left side: a ✓ checkmark with "Discrimination ✓" (green)
  Right side: a ✗ cross with "Interpolation ✗" (red)
  Between them: a ≠ symbol

Badge: "RQ1 ext."

═══════════════════════════════════════════════════════════
BOX 3 — ★ FUTURE PHASE 1: Forward Model (HIGHLIGHTED)
═══════════════════════════════════════════════════════════

Title: "★ Future Phase 1: Forward Model"   (★ in top-right as badge: "TODAY")

VISUAL CONTENT (left to right, as a model-building chain):

[Mini-fig A] The same SRM convergence icon from Box 2a, but smaller,
             with output arrow labeled "R_s"
             Arrow →
[Mini-fig B] A matrix multiplication visual: R_s × A_g = W₀
             Show two small rectangular matrices multiplying → result matrix.
             W₀ has a BLUE GLOW (validated).
             Label: "Group Prior W₀"
             Arrow →
[Mini-fig C] 6 overlapping PEAKED TUNING CURVES spanning 0°–360° on a mini axis.
             These are the FE-6 basis functions (half-wave cos²).
             Label: "FE-6 basis"
             Arrow →
[Mini-fig D] A small HEATMAP showing predicted vs actual voxel patterns,
             with a correlation value "r = 0.183" and "p = 0.044*" in orange bold.

Below the chain, a mini GO/NO-GO traffic light:
  - V1: RED light
  - V2: RED light
  - V3: YELLOW light
  - hV4: GREEN light with "PRIMARY GO"

Right side: "omnibus p = 0.002"

═══════════════════════════════════════════════════════════
BOX 4 — FUTURE PHASE 2: Distortion Estimation (DASHED)
═══════════════════════════════════════════════════════════

Title: "Future Phase 2: Distortion Estimation & Filter"

VISUAL CONTENT:

[Left side] A NORMAL hue wheel (perfect circle, evenly spaced colors)
            Arrow labeled "T_ψ" pointing right
            A WARPED hue wheel (same colors but unevenly spaced — blue/purple region
            compressed, warm colors slightly shifted). This warped wheel represents
            what CVD "sees."

[Center] The loss function as a visual equation:
         W₀ icon (blue glow, from Box 3) × basis curves × warped wheel
         ≈ (should match)
         A measured brain response icon (Ȳ_CVD, green)

[Right side] Three NESTED CIRCLES (concentric):
             Inner (small, red): "Cone shift (1p)"
             Middle (orange): "Fourier (4p)"
             Outer (blue): "Free (8p)"
             With "⊂" symbols between layers

[Bottom-right] An arrow from T_ψ being inverted: "Filter = T_ψ⁻¹"
               Show the warped wheel being UN-warped back to the normal wheel.

Badge: "RQ4"

═══════════════════════════════════════════════════════════
ARROWS BETWEEN BOXES
═══════════════════════════════════════════════════════════

Use small ICON labels on arrows instead of text where possible:

Box 0 → Box 1: Small brain-scan icon (BOLD signal)
Box 1 → Box 2a: Small data-cube icon (amplitudes)
Box 1 → Box 2b: Same data-cube icon
Box 2a + 2b → Box 3: Two small icons merging: SRM matrices + "FE confirmed" checkmark
Box 3 → Box 4: W₀ matrix icon with green checkmark + traffic light showing green

STYLE:
- Clean sans-serif font (Helvetica/Arial)
- Icons should be simple, flat, 2-color maximum per icon
- Boxes have subtle rounded corners and very light drop shadow
- Total image should be readable at 16:9 slide size
- Prioritize VISUAL CLARITY over completeness — better to show fewer things clearly
  than cram everything in
```

---
---

# Slide 3 — "왜 W₀가 필요한가" (Phase 2 Loss 개념도)

```
Create a scientific concept diagram showing how a prediction engine (W₀) connects to a distortion estimation loss function. Clean, modern, white background, 16:9 ratio.

LAYOUT: Left-to-right flow with two parallel pathways that converge at a comparison node.

TOP PATHWAY (HC Prediction — blue tones):
1. A hue circle (0°-360°, rainbow colored) with an arrow pointing right, labeled "θ (stimulus angle)"
2. Arrow goes into a box labeled "T_ψ" (orange border, representing the distortion warp). Inside, show a subtle warping of the hue circle — the colors shift slightly.
3. Arrow exits T_ψ labeled "T_ψ(θ)" and enters a box labeled "C(·)" (encoding basis — show 6 peaked tuning curves as a small icon inside)
4. Arrow exits C(·) and enters a large blue box labeled "W₀" with subtitle "(HC Group Prior, LOSO-validated)"
5. Arrow exits W₀ labeled "ŷ_HC = W₀ · C(T_ψ(θ))" showing a schematic voxel pattern (a small heatmap strip representing predicted voxel activation)

BOTTOM PATHWAY (CVD Measured Data — green tones):
1. Same hue circle with "θ" but now labeled "CVD subject sees θ"
2. Arrow goes directly to a brain icon or a box labeled "CVD Brain (measured)"
3. Arrow exits labeled "Ȳ_CVD(θ)" showing a similar voxel pattern strip (actual measured activation)

CONVERGENCE:
Both pathway outputs (ŷ_HC and Ȳ_CVD) meet at a comparison node on the right side.
Show "||ŷ − Ȳ||²" with a minimize symbol (↓ min).
Below the comparison, write: "Find T_ψ that minimizes this distance"
Below that: "Filter = T_ψ⁻¹"

KEY VISUAL ELEMENTS:
- The T_ψ box should have a subtle orange glow — this is what Phase 2 optimizes
- W₀ box should have a checkmark or "validated" badge — this is what Phase 1 delivered
- Ȳ_CVD should have a "raw data" icon — no model involved
- Draw a subtle bracket around W₀ labeled "Phase 1 output (today)"
- Draw a subtle bracket around T_ψ labeled "Phase 2 target (next)"

STYLE: Publication quality, sans-serif font, no 3D effects. Colors should be muted/professional.
```

---

# Slide 4 — Algorithm Steps A–D

```
Create a left-to-right scientific pipeline diagram showing 4 sequential steps (A through D) of building a group-prior prediction model for neuroscience. White background, 16:9, clean design.

LAYOUT: 4 connected boxes in a horizontal chain, with small data icons between them.

STEP A — "HC Common Space (SRM)" [light blue box]:
- Show 7 small brain icons (labeled "HC 1-7") each with different voxel counts
- Arrows converge into a central shared space (show as a small k-dimensional coordinate system, k=3-4)
- Inside: "Y_i → R_i, Z_i = R_i^T Y_i"
- Output arrow labeled "R_i (projection matrices), Z_i (shared coords)"

STEP B — "Group Prior Learning" [light green box]:
- Show the shared coordinates Z_i being fit to a basis matrix C
- Show 6 peaked tuning curves icon (FE-6 basis) at the bottom
- Inside: "A_i = ridge(Z_i, C)" then "A_g = mean(A_i)"
- Output arrow labeled "A_g (group-average encoder)"

STEP C — "Target Subject Projection" [light orange box]:
- Show a single brain icon (could be HC or CVD) with "new subject s"
- Arrow from R_s and A_g combining: "W₀ = R_s · A_g"
- Show this as matrix multiplication visually (small matrix icons)
- Output arrow labeled "W₀ (initial weight matrix, n_vox × K)"

STEP D — "Fine-Tuning" [light red/coral box]:
- Show W₀ being adjusted with the subject's own data Y_s
- Inside: "W_s = (Y·C' + λW₀)(CC' + λI)⁻¹"
- Show a dial or slider icon for λ: "λ=0: OLS, λ=∞: pure prior"
- Output: "W_s (final prediction model)"

BELOW THE CHAIN, add a horizontal bar showing:
"Encoding Basis: FE-6 — 6 half-wave rectified cos² channels, 60° spacing"
With a small plot showing 6 overlapping peaked tuning curves spanning 0°-360°.

ARROWS between steps: solid, dark gray, with small data-flow labels.

STYLE: Rounded rectangle boxes, slight drop shadow, professional color palette. Each step box slightly larger than the previous to show progression.
```

---

# Slide 5 — Validation 구조 (LORO / LOCO / LOSO)

```
Create a scientific diagram comparing three cross-validation schemes used in neuroscience. White background, 16:9 ratio, clean publication style.

LAYOUT: Three panels arranged vertically (or as 3 columns), each showing one CV scheme. Use consistent visual language.

PANEL 1 — "LORO: Leave-One-Run-Out" [blue header]:
- Show 6 horizontal bars representing 6 runs, each containing 8 colored dots (8 hue colors)
- 5 bars colored blue (training), 1 bar colored red with dashed outline (held-out test)
- Label: "Train on 5 runs → Test on 1 run"
- Below: "Question: Does W generalize to new runs?"
- Small badge: "Model stability"

PANEL 2 — "LOCO: Leave-One-Color-Out" [orange header, HIGHLIGHTED with thicker border]:
- Show 8 colored circles arranged in a hue wheel (red, orange, yellow, green, cyan, blue, purple, magenta)
- 7 circles filled (training), 1 circle with dashed outline and "?" inside (held-out)
- An arrow from the 7 training colors to a W matrix, then arrow to the "?" color showing prediction
- Label: "Train on 7 colors → Predict 1 held-out color"
- Below: "Question: Can W interpolate unseen colors?"
- Small badge: "★ PRIMARY — directly validates Phase 2 loss"

PANEL 3 — "LOSO: Leave-One-Subject-Out" [green header]:
- Show 7 person icons representing HC subjects
- 6 icons colored (training SRM), 1 icon with dashed outline (held-out)
- Arrow from 6 subjects through "SRM refit" to the held-out subject
- Label: "Train SRM on 6 HC → Test W₀ on 1 held-out HC"
- Below: "Question: Does W₀ transfer to new subjects?"
- Small badge: "Group prior reliability"

BOTTOM ANNOTATION spanning all panels:
"Permutation test (10K shuffles) = only valid statistical test"
"t-test (H₀: μ=0) uses WRONG null — voxel covariance creates non-zero baseline"

STYLE: Clean grid layout. LOCO panel should be visually emphasized (thicker border or subtle highlight) since it's the primary validation.
```

---

# Slide 6 — Permutation Test 결과 (히스토그램)

```
Create a 2×2 grid of histogram plots showing permutation test results for 4 brain regions. White background, publication quality, suitable for a 16:9 slide.

LAYOUT: 2 rows × 2 columns. Each panel is one ROI.

COMMON ELEMENTS per panel:
- X-axis: "LOCO voxel correlation" ranging from -0.1 to 0.3
- Y-axis: "Count" (frequency from 10,000 permutations)
- A gray/light blue histogram showing the null distribution (10,000 shuffled values)
- A vertical RED dashed line showing the observed value
- A shaded gray area showing the null 95% CI
- Text in top-right corner: "p = [value]"

PANEL 1 (top-left) — "V1":
- Null distribution centered at ~0.109, roughly normal shape
- Observed line at 0.130 (within the distribution, not far in the tail)
- p = 0.274 (shown in gray text, indicating non-significant)
- Border: thin gray

PANEL 2 (top-right) — "V2":
- Null centered at ~0.130
- Observed line at 0.150
- p = 0.311 (gray text)
- Border: thin gray

PANEL 3 (bottom-left) — "V3":
- Null centered at ~0.078
- Observed line at 0.023 (LEFT of the null center — model performs below chance)
- p = 0.880 (gray text)
- Border: thin gray

PANEL 4 (bottom-right) — "hV4" [HIGHLIGHTED with thick orange border]:
- Null centered at ~0.080, somewhat spread out
- Observed line at 0.183 (clearly in the RIGHT tail, beyond the 95% CI)
- p = 0.044* (shown in RED BOLD text, with asterisk)
- Border: THICK orange (#E67E22)
- Subtle orange background tint

KEY ANNOTATION below all panels:
"V1/V2 null ≈ 0.10-0.13 (not zero) — voxel covariance structure creates baseline"
"Only hV4 exceeds this covariance baseline → genuine color-specific interpolation"

STYLE: Matplotlib/seaborn aesthetic. Consistent axis ranges across panels for fair comparison. Histograms semi-transparent. Red line clearly visible.
```

---

# Slide 8 — hV4 보간 품질 4-panel 증거

```
Create a 2×2 evidence summary figure for a neuroscience presentation. Each panel shows a different type of evidence that hV4 is the only brain region with genuine color interpolation. White background, 16:9, publication quality.

PANEL A (top-left) — "Permutation Test":
- A simple horizontal bar chart with 4 bars (V1, V2, V3, hV4)
- X-axis: "p-value (permutation)"
- A vertical red dashed line at p=0.05
- V1 (0.274), V2 (0.311), V3 (0.880): bars extend past the red line (gray color, labeled "FAIL")
- hV4 (0.044): bar stops before the red line (orange color, labeled "PASS*")
- Title: "A. Permutation p-value"

PANEL B (top-right) — "Friedman Per-Color Uniformity":
- Show 4 small hue wheels, one per ROI
- V1: wheel with uneven colored segments (blue/cyan large, yellow/green small) — labeled "Non-uniform p=0.011"
- V2: similarly uneven — "Non-uniform p=0.047"
- V3: neutral — "No structure p=0.123"
- hV4: perfectly even segments — "Uniform p=0.485" with a green checkmark
- Title: "B. Per-Color Uniformity"
- Annotation: "hV4 interpolates ALL colors equally"

PANEL C (bottom-left) — "Residual Structure":
- A grouped bar chart: 4 ROI groups, each with 2 bars
- Bar 1 (blue): "r(prediction, original)" — V1:0.39, V2:0.41, V3:0.42, hV4:0.56
- Bar 2 (red): "r(residual, original)" — V1:0.45, V2:0.45, V3:0.33, hV4:0.05
- hV4's red bar should be visibly tiny compared to others
- Title: "C. Residual vs Prediction Correlation"
- Annotation: "hV4 residual ≈ random → model captures all available structure"

PANEL D (bottom-right) — "Opponent Basis Test":
- A heatmap/matrix: rows = 4 bases (OPP-2, OPP-4, OPP-4rect, FE-6), columns = 4 ROIs (V1, V2, V3, hV4)
- Cell values are p-values. Color: red if >0.05 (FAIL), green if <0.05 (PASS)
- Only ONE green cell: FE-6 × hV4 (p=0.039)
- All other cells red
- Title: "D. Basis × ROI Permutation"
- Annotation: "All opponent bases fail V1/V2 → not basis mismatch"

STYLE: Consistent font sizes. Each panel clearly labeled A-D. hV4 results visually emphasized in each panel (bold, orange highlight, or checkmark).
```

---

# Slide 9 — LOSO 3-Tier 비교 (막대 그래프)

```
Create a grouped bar chart comparing three validation tiers across 4 brain regions. Publication quality, white background, 16:9.

LAYOUT: One bar chart with 4 ROI groups on the x-axis (V1, V2, V3, hV4), each containing 3 bars.

BARS per ROI group (3 bars, side by side):
1. "Zero-Shot (W₀ only)" — BLUE bar
2. "LORO (ridge_gcv)" — GREEN bar
3. "LOCO (ridge_gcv)" — ORANGE bar

VALUES:
V1:  ZS=0.529, LORO=0.202, LOCO=0.113
V2:  ZS=0.555, LORO=0.235, LOCO=0.137
V3:  ZS=0.472, LORO=0.287, LOCO=0.037
hV4: ZS=0.417, LORO=0.407, LOCO=0.232

Y-AXIS: "Voxel Correlation (mean)" from 0 to 0.6

KEY VISUAL FEATURES:
- For hV4 group: draw a bracket or "n.s." annotation between ZS and LORO bars showing "p=0.913" — they are nearly equal height
- For V1/V2/V3: draw arrows or "***" between ZS and LORO showing "p<0.003" — large gap
- LOCO bars are always the shortest — add a horizontal annotation: "Interpolation always hardest"
- hV4 group should have a subtle orange background highlight

ANNOTATION at the bottom:
"hV4: ZS ≈ LORO (p=0.913) → W₀ alone matches subject-specific model"
"Gap: ZS − LOCO = 0.185 → room for Phase 2 T_ψ to improve"

ERROR BARS: Add thin error bars (SD) on each bar.

STYLE: Clean matplotlib aesthetic. Legend in top-right. No gridlines or minimal. Font size appropriate for presentation.
```

---

# Slide 10 — LORO-LOCO 해리 개념도

```
Create a conceptual diagram illustrating the dissociation between color discrimination (preserved) and color interpolation (impaired) in color vision deficiency. White background, 16:9, clean scientific style.

LAYOUT: Two-panel side-by-side comparison.

LEFT PANEL — "LORO: Run Generalization (Discrimination)" [blue-green tones]:
- Top: Show 8 colored circles (hue wheel) with solid borders — all 8 colors present in both training and test
- Middle: A brain icon processing these colors
- Bottom: Two grouped bar charts showing HC and CVD performance side-by-side
  - Heights nearly equal (HC ≈ 0.42, CVD ≈ 0.41 for hV4)
  - Label: "HC ≈ CVD (p > 0.22)"
- Large GREEN checkmark
- Caption: "Color information PRESERVED"
- Subtext: "CVD brains receive color signals normally"

RIGHT PANEL — "LOCO: Color Interpolation" [orange-red tones]:
- Top: Show 8 colored circles in a hue wheel, but ONE circle (e.g., blue) is replaced by a dashed "?" outline
- Middle: A brain icon with a "predict" arrow pointing to the missing color
- Bottom: Two grouped bar charts showing HC and CVD
  - HC bar positive (~0.18), CVD bar near zero or negative (~-0.06)
  - Label: "HC > CVD (d = 1.19)"
- Large RED X mark for CVD
- Caption: "Continuous geometry DISTORTED"
- Subtext: "Inter-color structure is disrupted in CVD"

CENTER DIVIDER between panels:
A vertical arrow or dividing line with text: "Same data, same subjects, different question"

BOTTOM ANNOTATION spanning both panels:
"Implication: CVD deficit is NOT information loss — it is geometry distortion"
"→ Stimulus-space warp (T_ψ) is the natural correction model"

STYLE: Symmetric layout. Clear visual contrast between "preserved" (green/blue) and "impaired" (orange/red). Icons simple and recognizable.
```

---

# Slide 14 — 중첩 모델 비교 (Nested Models)

```
Create a diagram showing three nested statistical models for estimating color vision distortion, arranged as concentric structures or a Venn-like nesting. White background, 16:9, publication quality.

LAYOUT: Three concentric rounded rectangles (or nested boxes), smallest inside largest. Left side shows the models, right side shows what each level tests.

INNERMOST (smallest) — Model 0: "Cone Shift" [red/warm tone]:
- Label: "Model 0: Cone Shift"
- "T(θ) = θ + δ_cone(Δλ)"
- "1 parameter"
- Small icon: a cone sensitivity curve shifting left/right
- Right annotation: "Pure retinal origin?"

MIDDLE — Model A: "Fourier Warp (T_ψ)" [orange tone]:
- Label: "Model A: Fourier Warp"
- "T(θ) = θ + Σ(aₖsin kθ + bₖcos kθ)"
- "4 parameters (k=1,2)"
- Small icon: a smooth sinusoidal warp of the hue circle
- Right annotation: "Smooth cortical contribution?"

OUTERMOST (largest) — Model B: "Free Shift" [blue tone]:
- Label: "Model B: Per-Color Free"
- "T(θᵢ) = θᵢ + δᵢ"
- "8 parameters"
- Small icon: 8 independent arrows on a hue wheel, each pointing different directions
- Right annotation: "Non-smooth distortion?"

BETWEEN LEVELS, show subset symbols (⊂):
- Model 0 ⊂ Model A ⊂ Model B

RIGHT SIDE — Decision table:
Three comparison rows:
1. "0 ≈ A ≈ B → Cone shift explains all (retinal)" with a simple icon
2. "0 < A ≈ B → Smooth warp beyond cone shift (cortical)" with a different icon
3. "A < B → Non-smooth → T_ψ insufficient" with a warning icon

BOTTOM:
"Common Loss: L = Σ‖W₀ · C(T(θ)) − Ȳ_CVD(θ)‖²"
"Statistical comparison: F-test / AIC"

STYLE: The nesting should be visually clear — use decreasing opacity or different color intensities. Clean, not cluttered. The nested structure is the key visual message.
```

---

# 프롬프트 사용 우선순위

| 순위 | 슬라이드 | 다이어그램 내용 | 효과 |
|:----:|:--------:|----------------|------|
| 1 | **Slide 2** | Overall Pipeline | 전체 맥락 한눈에 |
| 2 | **Slide 3** | W₀ + T_ψ loss 개념도 | Phase 2 연결 직관적 이해 |
| 3 | **Slide 6** | Permutation 히스토그램 | 핵심 결과 시각화 |
| 4 | **Slide 10** | LORO-LOCO 해리 | 핵심 발견의 개념적 전달 |
| 5 | **Slide 4** | Algorithm Steps A-D | 방법론 이해 |
| 6 | **Slide 5** | LORO/LOCO/LOSO 비교 | CV 구조 한눈에 |
| 7 | **Slide 9** | 3-Tier 막대 그래프 | LOSO 수치 비교 |
| 8 | **Slide 8** | 4-panel 증거 | hV4 특수성 종합 |
| 9 | **Slide 14** | 중첩 모델 | Phase 2 설계 |
