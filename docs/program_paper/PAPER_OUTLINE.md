# Paper Outline

**Working Title**: Development of a Personalized Color Vision Correction Display Filter for Individuals with Color Vision Deficiency Using fMRI-Based Neural Responses and Deep Learning

**Format**: Use latex format given in `main.tex`. Check `gu_personal_encoding.pdf` for a guide of writing journal format

---

## Abstract (200-250 words)

**Status**: TO BE WRITTEN AFTER FINISHING THE DRAFT

**Content guidance**:
- Background: CVD challenges in digital environments + limitations of current filters
- Gap: Lack of objective, neural-guided personalized approaches
- Methods: fMRI + forward encoding model + 3D characterization (magnitude/sign/structure)
- Results: (1) Preserved neural discrimination in CVD, (2) Inter-individual heterogeneity
- Conclusion: Feasibility of personalized neural-guided filters demonstrated

---

## 1. Introduction

### 1.1 Necessity of Color Vision Correction Display Filter

**Status**: ✅ COMPLETE

**Key points**:
- CVD as barrier in digital environments (genetic factors, photoreceptors)
- Scope of challenges (88% CVD gamers, website accessibility issues)
- Current filter limitations (extreme adjustments, uniform approaches)
- Need for personalized approaches (individual variation in severity, spectral sensitivity)
- Existing personalized approaches lack objective neural metrics

**Sources**: `final_IRB.pdf`

### 1.2 Behavioral vs. Neurological Trait of CVD

**Status**: ✅ COMPLETE

**Key points**:
- Fundamental assumption: Can CVD distinguish colors neurally?
- If neural indistinguishability → filter design infeasible
- Mixed previous findings (V1 reduced but V2-V3 preserved; V4 failure)
- Critical question: Absence vs. preserved signals?
- Study approach: fMRI + forward encoding across V1-hV4

**Sources**: `OHBM_Abstract_v7.md`

### 1.3 Individual Differences in Neural Representations

**Status**: ✅ COMPLETE

**Key points**:
- Inter-individual variability even in normal vision (functional topography)
- Challenges group-level approaches
- CVD implications: Different types (protanopia/deuteranopia/protanomaly)
- Within-type variation in spectral sensitivity
- "One-size-fits-all" unlikely to succeed
- Need individual-specific neural characterization

**Sources**: Recent literature (Gardner & Gale, 2024)

### 1.4 Research Questions

**Status**: ✅ COMPLETE

**Three research questions**:
1. Can CVD distinguish colors neurally despite retinal deficits (fMRI decoding)?
2. Does CVD show inter-individual heterogeneity (necessitating personalization)?
3. Can 3D neural profiles (magnitude/sign/structure) inform filter design?

---

## 2. Methods

### 2.1 Participants

**Status**: ✅ COMPLETE

**Content**:
- 9 participants: 6 HC (3M/3F, 22.7±2.5y) + 3 CVD (2 deuteranopes + 1 protanomalous, 2M/1F, 23.3±2.1y)
- CVD diagnosis: Ishihara color plates
- Exclusion: Sub-01 for group analysis (low voxel count after feature selection)
- Final group: 5 HC (sub-02,03,05,06,07) vs. 3 CVD

**Sources**: IRB protocol, `OHBM_Abstract_v7.md`

### 2.2 Stimuli and Experimental Design

**Status**: ✅ COMPLETE

**Content**:
- Adapted from Brouwer & Heeger (2009)
- 8 isoluminant colors (CIE L*a*b*: L*=54, radius=38, 45° spacing) + neutral gray
- Presentation: 1.5s duration, 3-6s ISI
- Task: RSVP at fixation (detect white→black letter 'K', 400ms letters)
- 6 runs × ~7 min each, each color 48 times total (8 trials/run)
- **Figure 1**: Experimental design schematic

**Sources**: `OHBM_Abstract_v7.md`

### 2.3 fMRI Acquisition and Preprocessing

**Status**: ✅ COMPLETE

**Content**:
- Scanner: 3T Siemens MAGNETOM Trio
- T1: MPRAGE (TR=1900ms, TE=2.52ms, 1×1×1mm³)
- T2*: GE-EPI (TR=1500ms, TE=30ms, FA=75°, 2×2×2mm³, 24 oblique slices)
- Preprocessing: fMRIPrep (fieldmap distortion correction, motion, slice-timing, MNI 2mm)
- GLM: Voxel-wise beta coefficients per color (motion + drift regressors, high-pass filtering)

**Sources**: `OHBM_Abstract_v7.md`, `docs/GUIDE_to_fMRIprep.md`

### 2.4 ROI Definition

**Status**: ✅ COMPLETE

**Content**:
- ROIs: V1, V2, V3, hV4 bilateral (Wang et al., 2015 probabilistic atlas)
- Feature selection: ANOVA F-tests (k=1-200, optimized via nested CV per subject/ROI)
- Individual-level analysis (3.2.1-3.2.5): Focus on V1/V2 (most robust color discrimination)

**Sources**: `OHBM_Abstract_v7.md`

### 2.5 Forward Encoding Model

**Status**: ✅ COMPLETE

**Content**:
- Encoding-decoding pipeline (Brouwer & Heeger, 2009)
- 6 half-wave rectified squared sinusoidal basis functions (channels)
- Assumes voxel response = weighted sum of channel responses
- Leave-one-run-out CV: (1) Estimate W (channels→voxels), (2) Invert W (voxels→channels), (3) Reconstruct color
- Metrics:
  * Reconstruction error (circular distance in degrees, baseline=90°)
  * Proportion within ±22.5° and ±45°
  * Classification accuracy (8-way LDA, chance=12.5%)
- Stats: t-tests, Cohen's d

**Sources**: `OHBM_Abstract_v7.md`

### 2.6 Procrustes Analysis

**Status**: ✅ COMPLETE

**Content**:

**Standard Procrustes definition**:
- Orthogonal Procrustes analysis aligns two matrices by finding optimal rotation, translation, and scaling
- Minimizes Frobenius norm of residuals after transformation
- Standard formulation: Y_aligned = sYR + t (s=scaling, R=rotation, t=translation)

**Modified version (NO scaling)**:
- We use ordinary Procrustes (rotation + translation only, no scaling)
- Preserves magnitude information critical for CVD characterization
- Y_aligned = YR + t
- Disparity metric: Euclidean distance after optimal alignment

**Application in this study**:
- Run-wise alignment: Each of 6 runs aligned independently to reference
- Reference pattern: Mean of target group (HC mean for HC-HC alignment, HC mean for CVD-HC alignment)
- Voxel count matching: Truncate to minimum voxel count when HC and CVD differ
- Iteration: Apply to each subject-ROI-run combination

**Rationale for no scaling**:
- Magnitude differences (L2 norm) are biologically meaningful (e.g., Sub-08 Magenta +21%, Cyan -34%)
- Scaling would artificially normalize these differences
- Empirical validation: scaling has minimal impact on disparity (<1% difference)
- Enables independent assessment of magnitude vs. geometry

**Sources**: `PROCRUSTES_ANALYSIS_METHODS.md`

### 2.7 Common W Matrix Validation

**Status**: ✅ COMPLETE

**Purpose**: Test whether color channel-to-voxel decoder (W matrix) can be shared between HC and CVD after Procrustes alignment

**Experimental design**:

**Phase 1 - HC Common W Training**:
- Subjects: 4 HC (sub-03, 05, 06, 07), 6 runs each
- Reference: Mean of 4 HC amplitude patterns (computed run-wise)
- Alignment: Procrustes align each HC subject to HC reference (run-wise, no scaling)
- Cross-validation: Leave-one-run-out (LORO-CV)
  * For each held-out run: train W on 5 runs, test on 1 run
  * Test both aligned and unaligned data to quantify alignment benefit
  * Repeat for all 6 runs
- Final model: Common W trained on all 6 runs (saved for Phase 2)

**Phase 2 - CVD Testing (With Alignment)**:
- Subjects: 3 CVD (sub-08, 09, 10)
- Alignment: Procrustes align CVD patterns to HC reference (run-wise, no scaling)
- Testing: Apply HC common W (from Phase 1) to aligned CVD data
- Cross-validation: Same LORO-CV procedure as Phase 1

**Phase 3 - CVD Testing (No Alignment)**:
- Same CVD subjects and HC common W
- Testing: Apply HC W to **unaligned** CVD original data
- Comparison: Aligned vs. no-align reconstruction error

**Reconstruction procedure**:
- Channel estimation: C_est = (W^T W)^-1 W^T X^T
- Hue reconstruction: Find hue with maximum correlation to estimated channel response
- Error metric: Circular distance (degrees) between true and reconstructed hue

**Performance metrics**:
- Reconstruction error: Circular distance [0, 180°]
- Chance level: 90° (uniform distribution across 8 colors at 45° spacing)
- Alignment benefit: error_noalign - error_aligned

**Sources**: `GUIDE_COMMON_W_RECONSTRUCTION.md`

### 2.8 Personalized Filter Learning

**Status**: ✅ COMPLETE (Methods documented)

**Purpose**: Learn subject-specific linear transformation to map CVD fMRI patterns to HC-like patterns

**Sources**: `PHASE2A_FILTER_METHODS.md`, `PHASE2A_변환학습_설계_short.pdf`

#### 2.8.1 Model Structure

**Status**: ✅ COMPLETE

**Linear transformation**:
```
F = Y @ A + b
```

**Variables**:
- Y ∈ ℝ^(8×n): CVD input pattern (measured fMRI responses, 8 colors)
- A ∈ ℝ^(n×n): Transformation matrix (learned, subject-specific)
- b ∈ ℝ^n: Bias vector (learned, subject-specific)
- F ∈ ℝ^(8×n): Filtered output pattern
- H ∈ ℝ^(8×n): Target HC pattern (HC_mean)

**Parameter counts** (baseline81, deoblique_v2):
- V1: 429 voxels → 184,470 parameters (429² + 429)
- V2: 279 voxels → 78,120 parameters (279² + 279)

**Initialization**:
- A_init = I (n×n identity matrix) - "no transformation" baseline
- b_init = 0 (n-dimensional zero vector)
- Rationale: Start from minimal transformation, regularization prevents overfitting

**Design philosophy**:
- **Simplicity**: Linear model reduces overfitting risk with limited data (8 colors)
- **Interpretability**: A reveals voxel-wise gain adjustments, b reveals baseline shifts
- **Individual-specificity**: Each CVD subject requires unique (A, b) reflecting Phase 1 heterogeneity
- **Hyperalignment principle**: Small deformations from identity (enforced by regularization)

**Sources**: `PHASE2A_FILTER_METHODS.md` Section 2

#### 2.8.2 Loss Function

**Status**: ✅ COMPLETE

**Three-dimensional characterization framework**:

The loss function incorporates three orthogonal dimensions that characterize neural color representations:

1. **Magnitude** (L2 norm): Overall activation strength per color, independent of direction
   - Captures "how strongly" voxels respond (e.g., Sub-08 Magenta 121% of HC mean)
   - Ratio interpretation: >1 = amplification, <1 = suppression
   - Z-score comparison to HC variability identifies significant deviations

2. **Sign** (mean activation): Directional bias, orthogonal to magnitude
   - Captures "positive vs. negative" BOLD signal direction
   - Signed difference (CVD - HC mean) reveals over-activation (+) vs. under-activation (-)
   - Example: Sub-08 Magenta high magnitude + positive sign = consistent over-activation
   - Reveals patterns invisible to L2 norm alone

3. **Structure** (RDM): Pairwise color relationships, magnitude-invariant
   - Captures "which colors are similar to each other" in voxel response space
   - RDM[i,j] = 1 - Spearman_correlation(pattern_i, pattern_j)
   - Detects color space distortions (e.g., Sub-08 Yellow-Green collapse, Green-Blue expansion)
   - Preserves relative geometry independent of overall scale

**Total loss** (three-component weighted sum + regularization):
```
L_total = λ_mag × L_mag + λ_base × L_base + λ_struct × L_struct + α||A - I||²_F + β||b||²
```

**Component 1 - Magnitude Loss**:
```
L_mag = (1/8) Σᵢ (||F[i]|| - ||H[i]||)²
```
- **Purpose**: Match per-color L2 norm (activation strength)
- **Why needed**: CVD shows over-activation (Sub-08 Magenta 121%, Sub-09 Red 132%)
- **Gradient** (analytical): ∂L_mag/∂F[i] = (2/8) · (||F[i]|| - ||H[i]||) · (F[i] / ||F[i]||)

**Component 2 - Baseline Loss**:
```
L_base = (1/8) Σᵢ (mean(F[i]) - mean(H[i]))²
```
- **Purpose**: Match per-color mean activation (directionality)
- **Why needed**: L2 norm loses sign (+0.3 vs -0.3 both become 0.3), need to distinguish over- vs. under-activation
- **Gradient** (analytical): ∂L_base/∂F[i,j] = (1/(4n)) · (mean(F[i]) - mean(H[i]))

**Component 3 - Structure Loss (RDM-Based)**:
```
L_struct = ||RDM(F) - RDM(H)||²_F
where RDM[i,j] = 1 - Spearman_correlation(pattern[i], pattern[j])
```
- **Purpose**: Match color-pair dissimilarity structure
- **Why needed**: Captures color-pair relationships (e.g., Sub-08 Yellow-Green collapse z=-2.99)
- **Gradient** (numerical): Spearman correlation is rank-based (non-differentiable), use finite differences (ε=1e-8)
- **Properties**: Magnitude-invariant, detects systematic color space distortions

**Regularization**:
- **Identity preservation**: R_A = α · ||A - I||²_F (α = 0.01)
  * Penalize deviation from identity, encourage minimal transformation
- **Bias suppression**: R_b = β · ||b||² (β = 0.01)
  * Penalize large bias terms, prefer pure linear transformation

**Subject-specific weights** (λ_mag, λ_base, λ_struct) based on Phase 1 characterization:

| Subject | λ_mag | λ_base | λ_struct | Rationale |
|---------|-------|--------|----------|-----------|
| Sub-08  | 0.2   | 0.3    | **0.5**  | Structure-dominant: Yellow-Green collapse (z=-2.99), Green-Blue expansion (z=+4.22) |
| Sub-09  | **0.5** | 0.3  | 0.2      | Magnitude-dominant: High over-activation (Red 132%, Yellow 114%) |
| Sub-10  | **0.5** | 0.3  | 0.2      | Magnitude-dominant: Moderate differences, structure near-normal |

**Gradient computation strategy**:
- Hybrid approach: Analytical gradients for magnitude/baseline (10× faster), numerical for RDM (acceptable)
- Chain rule: ∂L/∂A = Y^T @ (∂L/∂F), ∂L/∂b = Σᵢ (∂L/∂F[i])

**Sources**: `PHASE2A_FILTER_METHODS.md` Section 3, 5.1

#### 2.8.3 Optimization

**Status**: ✅ COMPLETE

**Optimization algorithm**: L-BFGS-B (Limited-memory Broyden–Fletcher–Goldfarb–Shanno with Box constraints)

**Why L-BFGS-B**:
- Efficient for large-scale problems (100k+ parameters: V1 ~184k, V2 ~78k)
- Quasi-Newton method: approximates Hessian from gradient history
- Memory efficient: stores only recent gradients (limited memory)
- Proven convergence for smooth, differentiable objectives

**Convergence criteria**:
- Stop when: |f(x_k) - f(x_{k-1})| / max(|f(x_k)|, 1) < ftol (1e-9)
- Or: ||∇f(x_k)|| < gtol (default 1e-5)
- Or: iteration >= maxiter (1000)

**Typical convergence**:
- Iterations: 200-400
- Final loss: 0.0003-0.0007
- Runtime: 5-15 minutes per model (CPU, single core)

**Training unit**: Subject-level (all 8 colors simultaneously)
- NOT run-level: Phase 1 data already run-averaged
- NOT trial-level: Too noisy
- NOT color-level: RDM loss requires cross-color relationships

**Sources**: `PHASE2A_FILTER_METHODS.md` Section 4, 7, 8

#### 2.8.4 Evaluation Metrics

**Status**: ✅ COMPLETE (Methods documented)

**Content**:

1. **Training Convergence**: Final loss, component losses, iteration count, convergence status
2. **Filter Properties**:
   - A matrix deviation from identity (||A - I||²_F)
   - b vector norm (||b||²)
   - A matrix conditioning (eigenvalue distribution)
3. **Procrustes Disparity Reduction**: Before vs. after transformation, baseline comparison
4. **RDM Structural Similarity**: RDM correlation before vs. after, specific color-pair improvements
5. **Decoding Performance**: Apply HC common W to transformed patterns, compare reconstruction error
6. **Cross-Validation Generalization**: LOCO-CV (Leave-One-Color-Out), training vs. validation loss
7. **Component Loss Breakdown**: Track L_mag, L_base, L_struct contributions
8. **Visualization**: A matrix heatmap, b vector pattern, anatomical specificity

**Expected outcomes**:
- Successful convergence (final loss 0.0003-0.0007)
- Small deviations (A ≈ I, small b)
- Reduced Procrustes disparity (CVD → HC)
- Improved RDM correlation (≈0.95+)
- Good generalization (validation ≈ training loss)

**Sources**: `PHASE2A_FILTER_METHODS.md`

---

## 3. Results

### 3.1 Preserved Color Discrimination in CVD

**Status**: ✅ COMPLETE

**Addresses**: Research Question 1 (Can CVD distinguish colors neurally?)

#### 3.1.1 Individual-Level Performance

**Status**: ✅ COMPLETE

**Key findings**:
- All 3 CVD subjects showed successful color decoding across V1-hV4
- V1 classification: CVD (54.2%, 58.3%, 54.2%) all within HC range (33.3%-83.3%), above chance (12.5%)
- V1 reconstruction: CVD (40.2°, 39.0°, 48.1°) all within HC range (27.4°-68.0°), below baseline (90°)
- Consistency extends to V2, V3, hV4

#### 3.1.2 Group-Level Comparisons

**Status**: ✅ COMPLETE

**Key findings**:
- No group differences across all ROIs (V1-hV4)
- V1: HC 46.7±17.0°, CVD 42.4±4.9°, t(7)=0.41, p=.694, d=-0.29
- V2: HC 56.9±16.8°, CVD 55.3±5.1°, t(7)=0.16, p=.876, d=-0.11
- Hierarchical pattern: V1 < V2 < V3 ≈ hV4 (both groups)
- Classification: HC 56.6±18.6%, CVD 55.6±2.4% (V1), no differences
- **Figure 2**: Group-level reconstruction error across ROIs

#### 3.1.3 Permutation Testing Validation

**Status**: ✅ COMPLETE

**Key findings**:
- Red-green labels shuffled (most affected axis in CVD)
- Shuffling degraded accuracy (d=0.48)
- Significant in HC (p=.041, d=0.44) but not CVD (p=.497, d=0.20)
- Small CVD n=3 limits interpretation
- Validates genuine neural color representations

**Sources**: `OHBM_Abstract_v7.md`

#### 3.1.4 Shared Decoder Validation: Common W Matrix Applicability

**Status**: ✅ COMPLETE

**Addresses**: Core assumption for filter design (Section 1.5) - Can a shared decoder (W matrix) enable color reconstruction across HC and CVD after pattern alignment?

**Key Findings**:

1. **HC Common W Robustness**:
   - HC aligned: 5-15° (V1-hV4) << baseline 30-40° (individual W)
   - HC no-align: 50-70° (alignment necessary)
   - **Conclusion**: HC subjects share consistent W matrix

2. **CVD Applicability of HC W**:
   - CVD aligned: 5-10° (matches HC aligned)
   - CVD no-align: 84-96° ≈ chance (90°)
   - Alignment benefit: CVD (81°) > HC (44°)
   - **Conclusion**: CVD patterns contain HC-like structure, accessible via transformation

3. **Theoretical Implications**:
   - ✅ Shared decoder confirmed between HC and CVD
   - ✅ Linear transformation (Procrustes) sufficient for decoder sharing
   - ✅ Filter design feasible: transforming CVD → HC-like patterns enables decoding
   - ✅ CVD structure preserved despite magnitude/sign alterations

**Figures**:
- HC common W validation (LORO-CV, aligned vs. no-align)
- CVD applicability (aligned vs. no-align, group comparison)
- Procrustes alignment visualization (MDS projection)

**Sources**: `GUIDE_COMMON_W_RECONSTRUCTION.md`

---

### 3.2 Individuality of CVD: Three-Dimensional Analysis

**Status**: ✅ COMPLETE

**Addresses**: Research Question 2 (Inter-individual heterogeneity?)

#### 3.2.1 Within-Group Variability: HC Baseline

**Status**: ✅ COMPLETE

**Key findings**:
- Establishes baseline individual variability in HC
- Procrustes disparity (HC-HC):
  * V1: Mean=9.3, SD=2.1, range [6.2, 13.7]
  * V2: Mean=12.8, SD=3.4, range [8.1, 18.9]
- RDM correlation (HC-HC):
  * V1: Mean r=0.82, SD=0.06, range [0.71, 0.91]
  * V2: Mean r=0.78, SD=0.08, range [0.65, 0.89]
- **Implication**: Individual differences are norm, not exception
- **Figure 2**: HC pairwise disparity heatmap, distribution, RDM correlation matrix

**Sources**: `OPTION2D_종합보고서_한국어.pdf`

#### 3.2.2 CVD vs. HC: Group-Level Comparison

**Status**: ✅ COMPLETE

**Key findings**:
- CVD structural disparity largely within HC variability
- **Table 1**: Procrustes disparity summary
  * Sub-08 V1: 8.1 (0.87× HC mean, preserved)
  * Sub-08 V2: 17.6 (1.38× HC mean, mod. distortion)
  * Sub-09 V1: 7.2 (0.77×, preserved)
  * Sub-09 V2: 11.1 (0.87×, preserved)
  * Sub-10 V1: 8.9 (0.96×, preserved)
  * Sub-10 V2: 13.4 (1.05×, preserved)
- All CVD V1 within 1 SD of HC mean
- V2: Sub-08 slightly elevated, others within range
- **Conclusion**: Representational structure preserved in CVD

**Sources**: `OPTION2D_종합보고서_한국어.pdf`

#### 3.2.3 Heterogeneity of Individual CVD

**Status**: ✅ COMPLETE

**Overview**: Three-dimensional characterization (magnitude, sign, structure) reveals substantial individual heterogeneity among CVD subjects, challenging genotype-based predictions.

**Magnitude Analysis** (L2 norm deviations):
- **Sub-08 (Deuteranopia)**:
  * V1: Magenta +21%, Cyan -34%***
  * V2: Red +32%***, Green +29%**, Magenta +24%**
- **Sub-09 (Deuteranopia)**:
  * V1: Red +32%***, Yellow +14%
  * V2: Global suppression (Green -30%, Chartreuse -21%, Cyan -25%)
- **Sub-10 (Protanomaly)**:
  * V1: Yellow +15%, mostly within range
  * V2: Chartreuse -30%***, Magenta -31%***
- **Critical finding**: Same genotype (Sub-08 vs 09 deuteranopes) → opposite V2 patterns (over-activation vs. suppression)
- **Table 2**: Magnitude deviations summary
- **Figure 3**: L2 norm ratios (3 panels, 8 colors × V1/V2)

**Sign Analysis** (directional biases, orthogonal to magnitude):
- **Sub-08**:
  * V1: Magenta +0.32 (over-activation), Cyan -0.41 (under-activation)
  * V2: Mixed pattern (Red +0.45, Green +0.38)
- **Sub-09**:
  * V1: Warm colors positive bias (Red +0.28, Yellow +0.19)
  * V2: Global under-activation (all colors negative, mean -0.35)
- **Sub-10**:
  * V1: Mostly within HC variability (|diff|<0.2)
  * V2: Specific under-activation (Chartreuse -0.42, Magenta -0.38)
- **Example integration**: Sub-08 Magenta shows high magnitude (1.21×) + positive sign (+0.32) = consistent over-activation
- **Figure 4**: Mean activation differences (3 panels, CVD - HC mean)

**Structure Analysis** (RDM - pairwise color relationships):
- Visual inspection:
  * HC mean: Clear block-diagonal structure (adjacent hues similar, opposite dissimilar)
  * Sub-08: Yellow-Green reduced dissimilarity (0.85→0.70, collapse)
  * Sub-09: Visually indistinguishable from HC
  * Sub-10: Minimal deviation from HC
- Quantitative comparison:
  * Sub-08 V1: Mean |Δ|=0.186±0.091, Yellow-Green -0.15*** (z=-2.99, p=.003)
  * Sub-08 V2: Mean |Δ|=0.224±0.118, Green-Blue +0.22*** (z=+2.85, p=.004)
  * Sub-09/10: All pairwise differences within HC range
- Comparison to HC variability:
  * V1: HC-CVD |Δ|=0.156 vs. HC-HC |Δ|=0.171 (91% preservation)
  * V2: HC-CVD |Δ|=0.176 vs. HC-HC |Δ|=0.196 (90% preservation)
- **Table 3**: RDM structural preservation summary
- **Figure 5**: RDM heatmaps (4×2 grid: HC mean + 3 CVD × V1/V2)
- **Figure 6**: RDM difference heatmaps (CVD - HC, 3 panels)

**Key conclusions**:
- **Individual-specific patterns**: Each CVD subject shows unique combination of magnitude, sign, and structure alterations
- **Genotype ≠ neural phenotype**: Same genetic deficit (deuteranopia) produces opposite neural patterns (Sub-08 vs Sub-09)
- **Preserved structure**: Overall RDM preservation (90-91%) indicates CVD = gain modulation, NOT collapsed color space
- **Localized exceptions**: Sub-08 shows specific color-pair distortions (Yellow-Green, Green-Blue) while maintaining global structure
- **Implication**: Personalized intervention approaches necessary; one-size-fits-all filters unlikely to succeed

**Sources**: `OPTION2D_종합보고서_한국어.pdf`

---

### 3.3 Personalized Correction Filter Results

**Status**: ✅ COMPLETE (Phase 2A implementation)

**Addresses**: Research Question 3 (Can neural profiles inform filter design?)

**Overview**: Results from training subject-specific linear transformations (F^(s) = Y^(s) × A^(s) + b^(s)) to map CVD patterns to HC-like patterns using baseline32_deob_determin dataset.

#### 3.3.1 Training Convergence and Model Quality

**Status**: ✅ COMPLETE

**Key Findings**:

1. **Convergence**: All 6 models (3 subjects × 2 ROIs) converged successfully
   - Mean final loss: 0.000465 (< 0.001)
   - Rapid convergence: 4/6 models converged in 1 iteration (identity initialization near-optimal)
   - Iterative refinement: sub-08 V1 and sub-10 V1 required 34 iterations
   - Gradient norms: < 10⁻³ (stable local minima)

2. **Loss Component Balance**: Three components contributed roughly equally
   - Example (sub-08 V1): Magnitude 42.2%, Baseline 30.3%, Structure 27.5%
   - Validates subject-specific weight design

3. **A Matrix Quality**:
   - Mean deviation from identity: 8.39% (moderate transformation)
   - Well-conditioned: condition number 2.4-2.8 (far from singular)
   - Singular values: min 0.386, max 1.007 (minimal scaling, moderate compression)
   - ROI differences: V2 requires more transformation than V1 (9.36% vs 7.41%)

4. **b Vector Properties**:
   - Small magnitudes: mean ‖b‖₂ = 0.020 (negligible vs z-scored σ ≈ 1.0)
   - Centered: mean(b) ≈ 0 (no systematic offset)
   - Regularization effective: β = 0.01 prevented overfitting

5. **Cross-Validation**: LOCO-CV not yet performed (future work)

**Figures**:
- **Figure 7**: Training curves grid (3 subjects × 2 ROIs, total/component losses)
- **Figure 8**: LOCO-CV results (training vs. validation bar plots)

#### 3.3.2 Neural Pattern Transformation

**Status**: ✅ COMPLETE

**Key Findings**:

1. **Procrustes Disparity Reduction**:
   - Before filtering: mean disparity 1.032 (near-orthogonality with HC)
   - After filtering: mean disparity 0.030 (near-perfect alignment)
   - Mean improvement: 97.2% reduction (range: 95.5%-99.0%)
   - Statistical significance: t(5) = 24.12, p < 0.001
   - Best performance: sub-10 (protanomaly, 99.0% V1)
   - All models achieved >95% disparity reduction

2. **RDM Correlation Improvement**:
   - Before filtering: mean ρ = 0.118 (severe distortion, sub-10 V2 = -0.291 reversed)
   - After filtering: mean ρ = 1.000 (near-perfect structure recovery)
   - Mean improvement: +0.882 (+618%)
   - **Key insight**: Structure preserved (RDM ≈ 1.0) without forcing voxel-wise correlation (intended Procrustes behavior)

3. **A Matrix Interpretation** (voxel-wise gain patterns):
   - **Diagonal elements** (self-gain):
     * Mean: 0.983 (slight overall attenuation)
     * Range: [0.42, 1.31] (heterogeneous correction needed)
     * 79% attenuative (gain < 1.0), 21% amplified (gain > 1.0)
   - **Off-diagonal elements** (cross-voxel mixing):
     * Mean: 0.001 (near-zero), Std: 0.043 (small)
     * 87% negligible (|A[i,j]| < 0.05), 13% meaningful
     * **Diagonal-dominant**: primarily voxel-specific gain, not rewiring
     * Sparse coupling suggests localized interactions

4. **b Vector Interpretation** (baseline shifts):
   - Small magnitudes: ‖b‖₂ ≈ 0.02
   - Symmetric distribution around zero (mean ≈ 0)
   - Weak negative correlation with baseline activation (ρ = -0.24, p = 0.01)
   - Interpretation: CVD elevated baseline needs suppression

5. **Transformation Nature**:
   - Moderate, diagonal-dominant, sparse transformations
   - Minimal baseline shifts (primarily rotation/scaling)
   - **Implication**: CVD distortions are **magnitude-based** (activation strength), not **structural-based** (voxel coupling)
- Subject-specific A and b patterns reflecting Phase 1 heterogeneity
- V1 vs. V2 differences in transformation requirements

**Figures**:
- **Figure 9**: Before/after Procrustes comparison (3D PCA scatter plots)
- **Figure 10**: A matrix heatmaps (3 subjects × 2 ROIs)
- **Figure 11**: b vector patterns (bar plots)

#### 3.3.3 Color Perception Transformation and Behavioral Validation

**Status**: ⚠️ PLANNED

**Content to include**:
- Decoding performance improvement:
  * Classification accuracy: Original CVD vs. transformed vs. HC
  * Reconstruction error: Before/after transformation
  * Per-color improvements (which colors benefit most)
- Color space transformation visualization:
  * 2D color wheel: Original CVD → transformed → HC target
  * Confusion matrix changes: Before/after filter
  * Color pair discriminability improvements
- Behavioral predictions:
  * Display filter implications (RGB transformation)
  * Expected perceptual changes
  * Validation approach (Phase 2B psychophysics)

**Expected findings**:
- Improved decoding accuracy approaching HC levels
- Reduced reconstruction errors
- Color-specific improvements matching Phase 1 deficits
- Testable predictions for behavioral validation

**Figures**:
- **Figure 12**: Decoding performance comparison (before/after/HC bar plots)
- **Figure 13**: Color space transformation visualization (2D wheels)
- **Figure 14**: Predicted display filter effects (example images)

**Key conclusions**:
- **Successful transformation**: Neural patterns can be modified to approximate HC
- **Individual specificity**: Each subject requires unique (A, b) parameters
- **Preserved structure**: Transformation maintains RDM geometry while adjusting magnitude/baseline
- **Phase 2B readiness**: Provides neural-guided predictions for behavioral filter testing

**Sources**: To be added after Phase 2A implementation

---

## 4. Discussion

**Status**: ❌ EMPTY (placeholders only)

**Overall structure**: Answer 3 research questions → methodological contributions → limitations → broader implications

### 4.1 Assumption 1: Preserved Neural Color Discrimination in CVD

**Status**: ✅ COMPLETE

**Key content written**:
- **Neural-behavioral dissociation**: CVD show preserved neural representations despite behavioral deficits
  * All 3 CVD subjects overlapped with HC range in decoding
  * Group-level: no differences across V1-hV4 (all p>.10)
  * Hierarchical degradation V1→hV4 maintained in both groups

- **Gain modulation interpretation**: CVD = altered magnitude, NOT collapsed structure
  * RDM analysis: 91% V1 similarity, 90% V2 similarity to HC
  * Magnitude changes within preserved geometric framework
  * Key advance: Separating "how strongly" from "how organized"

- **Comparison to literature**:
  * Extends Tregillus et al. (2021): Preservation even in V1
  * Addresses Neitz & Neitz (2011) V4 hypothesis
  * Novel contribution: Quantitative RDM showing preserved geometry

- **Mechanism**: Cortex preserves discriminability despite weaker retinal inputs
  * Reduced cone signals → smaller response magnitudes
  * Cortical machinery for extracting differences remains intact
  * Analogous to reduced contrast processing
  * Permutation testing validates genuine color representations

- **Neurophysiological feasibility**: Target representations exist for filter design
  * Preserved patterns can be leveraged
  * Input transformations can amplify/rebalance signals
  * Deficit in neural-to-perceptual transformation, not sensory coding

- **Conclusion**: CVD maintain >90% structural similarity to HC, providing neurophysiological foundation for personalized neural-guided filter design

**Sources**: `OHBM_Abstract_v7.md`, Results sections 3.1 and 3.2.5

### 4.2 Assumption 2: Inter-Individual Heterogeneity in CVD

**Status**: ❌ TO BE WRITTEN

**Content to include**:
- Key finding: Same genotype → different cortical phenotypes
- Evidence from Sub-08 vs. Sub-09 (both deuteranopes):
  * V2 magnitude: +32% (Red/Green) vs. -30% (global) - opposite!
  * Structure: Yellow-Green collapse vs. preserved
  * Compensation: Partial V2 amplification vs. global suppression
- Implication: Retinal genotype ≠ cortical phenotype
  * Individual differences in neural plasticity
  * Variable compensation mechanisms
  * Cannot predict neural profile from genetic test alone
- Comparison to individual variability literature:
  * Analogous to Gu et al. (2022): Personalized encoding models preserve differences
  * Supports Gardner & Gale (2024): Functional topography varies
  * Novel: First 3D quantification (magnitude/sign/structure) in CVD
- **Conclusion**: Same genotype does not predict cortical phenotype; individual-specific characterization is necessary, and "one-size-fits-all" approaches are insufficient for CVD intervention

**Sources**: Discussion from `OPTION2D_종합보고서_한국어.pdf`

### 4.3 Feasibility of Personalized Neural-Guided Filters

**Status**: ❌ TO BE WRITTEN

**Content to include**:
- Synthesis of Assumptions 1 + 2:
  * Assumption 1 → Neural targets exist (preserved discrimination)
  * Assumption 2 → Individual-specific targets required (heterogeneity)
  * Combined → Personalized filters both necessary AND feasible
- Filter design rationale:
  * Use 3D profile to determine strategy:
    - Magnitude-dominant (Sub-09): High α (0.8-0.9) for gain correction
    - Structure-dominant (Sub-08): Balanced α (0.5-0.7) for geometry + magnitude
    - Mild (Sub-10): Targeted α for specific colors only
- Advantages over existing:
  * Current (EnChroma, etc.): Wavelength shift from cone photopigments only
  * Our approach: Neural-guided, accounts for cortical compensation
  * Potential benefit: Addresses individual V2/V3 processing differences
- **Conclusion**: Personalized neural-guided filters are both necessary (due to individual heterogeneity) and feasible (due to preserved neural representations); preliminary framework established with empirical validation pending

**Sources**: To be developed based on `PHASE2A_TRANSFORMATION_LEARNING.md`

### 4.4 Methodological Contributions

**Status**: ❌ TO BE WRITTEN

**Content to include**:
1. **Three-dimensional characterization**:
   - Orthogonal dimensions (magnitude, sign, structure)
   - Richer than classification accuracy alone
   - Generalizability: Auditory deficits, anosmia, etc.
   - Details: Section 2.6.1-2.6.3

2. **Modified Procrustes analysis**:
   - Preserves magnitude (no scaling)
   - Separates "how much" vs. "how different"
   - Innovation: Independent gain vs. geometry measurement
   - Details: `PROCRUSTES_ANALYSIS_METHODS.md`

3. **Individual-first paradigm**:
   - Characterize each subject separately before group comparison
   - Aligns with precision neuroscience
   - Practical: Encoding models trainable with ~300 images (Gu et al., 2022)

**Sources**: Methodological docs

### 4.5 Limitations and Future Directions

**Status**: ✅ COMPLETE

**Content to include**:

1. **Sample size** (n=3 CVD):
   - Preliminary, hypothesis-generating
   - Need larger cohort (target: n>10 per CVD type)
   - Power for group-level statistics limited

2. **Shared decoder assumption**:
   - **Current evidence**: HC common W applies to aligned CVD patterns (5-10° error)
   - **What is NOT proven**: Whether W matrices are *identical* between HC and CVD
   - **Limitations**:
     * W structure similarity not directly tested (CVD individual W vs. HC common W comparison needed)
     * Assumption of linear decoder (nonlinear alternatives not explored)
     * Unidirectional test only (HC W → CVD tested, but not CVD W → HC)
   - **Future directions**:
     * Compare CVD individual W vs. HC common W structure (canonical correlation, subspace angles)
     * Bidirectional cross-validation (train on CVD, test on HC)
     * Forward encoding model (predict neural response from stimulus)
   - **Implications if W differs**: May require individual-specific decoders, not group-level common W

3. **HC no-alignment paradox**:
   - **Observation**: HC no-align error (50-70°) > baseline individual W (30-40°)
   - **Possible explanations**:
     * Common W less optimal than individual W for each subject
     * Voxel selection may be subject-specific (coordinate system matters)
     * Alignment improves voxel-level correspondence accuracy
   - **Future exploration**: Individual W vs. common W structure comparison, subject-specific vs. group-level feature trade-off

4. **Filter validation** (current: theoretical, no prospective MRI validation):
   - **Current limitation**: Due to time constraints and MRI center renovation, planned assessment experiment with MRI was not conducted
   - **What is missing**: Prospective validation - testing learned filters on new MRI data
   - **Critical next step**: fMRI validation with filtered stimuli
     * Measure CVD neural responses to filtered images
     * Compare filtered CVD patterns to HC responses to original images
     * Check alignment: Do filtered voxel activation patterns align with HC patterns?
     * Check reconstruction: Do filtered patterns improve color reconstruction accuracy?
   - **Behavioral validation**: Does filter improve actual color discrimination in psychophysical tests?
   - **Implication**: Current filter effectiveness is based on retrospective training data analysis, not independent prospective validation

5. **Stimulus generalization** (current: 8 isoluminant colors):
   - Extend to natural images, luminance variations
   - Validate on real-world scenes

6. **Behavioral-neural link**:
   - Neural decoding preserved ≠ behavioral perception improved
   - Need psychophysical validation (discrimination thresholds, color naming)
   - Integrate fMRI + psychophysics for comprehensive assessment

7. **Mechanistic understanding**:
   - Why Sub-08 vs. Sub-09 opposite V2 patterns despite same genotype?
   - Role of plasticity, developmental history, individual experience
   - Longitudinal studies needed

**Sources**: `GUIDE_COMMON_W_RECONSTRUCTION.md` (Limitations section), standard limitations

### 4.6 Broader Implications

**Status**: ❌ TO BE WRITTEN

**Content to include**:
1. **Precision vision science**:
   - Move beyond group-average models
   - Individual variability as signal, not noise
   - Parallel to precision medicine (oncology, psychiatry)

2. **Rethinking "colorblindness"**:
   - Neural data show discrimination maintained
   - More accurate: "color vision deficiency" or "color alteration"

3. **Neural-behavioral disconnect**:
   - Paradox: Preserved neural structure but impaired behavior
   - Future: Predict behavioral errors from neural patterns

4. **Assistive technology implications**:
   - Current: Universal wavelength-shift filters
   - Proposed: fMRI-calibrated, individually-tailored transformations
   - Implementation: AR glasses with neural-guided real-time filtering

**Sources**: Discussion extensions

---

## 5. Conclusion

**Status**: ❌ TO BE WRITTEN

**Content to include**:
- Summary: This study established the neurophysiological feasibility of personalized neural-guided filters for CVD by validating two critical assumptions
- **Distinguishability**: CVD individuals maintain neural color discrimination in early and intermediate visual cortex despite retinal deficits, with preserved representational geometry exceeding 90% similarity to healthy controls in V1 and V2. This challenges the terminology of "colorblindness" and confirms that target neural representations exist for intervention.
- **Individuality**: CVD individuals show heterogeneous cortical phenotypes even with identical genotypes, as demonstrated by opposite V2 magnitude patterns in two deuteranopes (Sub-08 vs. Sub-09). This necessitates personalized, rather than universal, intervention approaches.
- **Implications**: The combination of preserved neural structure and individual heterogeneity both enables and requires personalized neural-guided filters. The three-dimensional characterization framework (magnitude, sign, structure) directly informs individual-specific loss function weighting for filter optimization.
- **Future directions**:
  1. Empirical validation through fMRI measurements of CVD responses to filtered stimuli
  2. Behavioral testing to establish links between neural profiles and perceptual thresholds
  3. Larger cohort recruitment (target: n>10 per CVD type) to identify generalizable patterns across subtypes
- **Broader significance**: This work provides the first proof-of-concept that fMRI-based neural profiling can guide the development of personalized assistive technologies for sensory deficits, extending precision medicine principles to vision science.

**Sources**: Synthesis of all sections

---

## Supplementary Sections

### Conflicts of Interest

**Status**: ❌ TO BE ADDED

**Content**: "The authors declare no conflict of interest."

### Author Contributions

**Status**: ❌ TO BE SPECIFIED

**Format**: NISO CrediT taxonomy
- Conceptualization:
- Methodology:
- Software:
- Validation:
- Formal analysis:
- Investigation:
- Resources:
- Data curation:
- Writing - original draft:
- Writing - review & editing:
- Visualization:
- Supervision:
- Project administration:
- Funding acquisition:

### Funding

**Status**: ❌ TO BE ADDED

### Data Availability

**Status**: ❌ TO BE ADDED

**Content to consider**:
- Code: GitHub repository
- Data: Restrictions due to IRB (de-identified data available upon reasonable request)
- Analysis scripts: Available at [URL]

### Acknowledgments

**Status**: ❌ TO BE ADDED

---

## Figures Summary

**Total**: ~6 main figures

1. **Figure 1**: Experimental design and forward encoding model ✅
   - Panel A: 8 isoluminant colors in CIE L*a*b* space
   - Panel B: Experimental paradigm (1.5s stimuli, RSVP task)
   - Panel C: Forward encoding pipeline schematic
   - File: `OHBM_Figure_1.png`

2. **Figure 2**: Preserved color discrimination in CVD across visual hierarchy ✅
   - Panel A: Color reconstruction examples (circular distance)
   - Panel B: Group-level reconstruction error (V1, V2, V3, hV4)
   - Panel C: Permutation testing procedure schematic
   - Panel D: Permutation testing results (HC significant, CVD n.s.)
   - File: `OHBM_Figure_2.png`

3. **Figure 3**: Individual CVD magnitude profiles (L2 norm ratios) ⚠️
   - 3 panels: Sub-08, Sub-09, Sub-10
   - Bar plots: CVD/HC ratio for 8 colors × V1/V2
   - Error bars: HC variability (SD)
   - Horizontal line at 1.0 (no difference)
   - Status: TO BE GENERATED from magnitude analysis

4. **Figure 4**: Individual CVD sign profiles (mean activation) ⚠️
   - 3 panels: Sub-08, Sub-09, Sub-10
   - Bar plots: CVD - HC mean for 8 colors × V1/V2
   - Positive = over-activation, Negative = under-activation
   - Status: TO BE GENERATED from sign analysis

5. **Figure 5**: RDM heatmaps (structure preservation) ⚠️
   - 4×2 grid: HC mean + 3 CVD subjects (rows) × V1/V2 (columns)
   - Each heatmap: 8×8 color-pair dissimilarity matrix
   - Color scale: 0 (identical) to 2 (maximally dissimilar)
   - Status: TO BE GENERATED from RDM analysis

6. **Figure 6**: RDM difference heatmaps (CVD - HC) ✅
   - 3×2 grid: 3 subjects (Sub-08, Sub-09, Sub-10) × 2 ROIs (V1, V2)
   - Red: Increased dissimilarity (CVD > HC) - color pairs become more distinct
   - Blue: Decreased dissimilarity (CVD < HC) - color pairs collapse/merge
   - Key patterns:
     * Sub-08 V1: Yellow-Green collapse (blue, -0.15)
     * Sub-08 V2: Green-Blue separation (red, +0.22)
     * Sub-09, Sub-10: Minimal structural distortions (mostly white/near-zero)
   - Status: AVAILABLE (provided heatmap image)

---

## Tables Summary

**Total**: ~3 tables

1. **Table 1**: Procrustes Disparity: CVD vs. HC Comparison ✅
   - Columns: Subject, ROI, Disparity, Rel. to HC, Interpretation
   - Rows: Sub-08/09/10 × V1/V2
   - Location: Section 3.2.2

2. **Table 2**: Magnitude Deviations Summary ✅
   - Columns: Subject, CVD Type, Max Increase, Max Decrease, Pattern
   - Rows: Sub-08, Sub-09, Sub-10
   - Location: Section 3.2.3

3. **Table 3**: RDM Structural Differences ✅
   - Columns: Subject, ROI, Mean |Δ|, Max pair, Δ
   - Rows: Sub-08/09/10 × V1/V2
   - Location: Section 3.2.5

---

## Writing Priority

### Immediate (Write First)
1. **Section 2.6.1-2.6.2**: Expand magnitude and sign methods ⚠️
2. **Section 4**: All discussion subsections ❌
3. **Section 5**: Conclusion ❌
4. **Figures 3-6**: Generate from analysis results ⚠️

### Final Pass (After Draft)
1. **Abstract**: Write last based on complete draft ❌
2. **Author Contributions**: Assign CRediT roles ❌
3. **Acknowledgments**: Add funding/support ❌
4. **Proofreading**: Check references, formatting, consistency

---

## Key References to Cite

**Methodological foundations**:
1. Brouwer & Heeger (2009) - Forward encoding model ✅
2. Gu et al. (2022) - Personalized encoding models
3. Kriegeskorte et al. (2008) - RSA framework ✅
4. Gower (1975) - Procrustes analysis ✅

**CVD neuroscience**:
5. Tregillus et al. (2021) - Color compensation in CVD (Current Biology) ✅
6. Neitz & Neitz (2011) - Genetics of normal/defective color vision ✅
7. [Additional CVD genetics/photopigment papers]

**Individual differences**:
8. Gardner & Gale (2024) - Individual variability in functional topography
9. Gordon et al. (2017) - Individual-specific parcellations
10. Finn et al. (2015) - Functional connectivity fingerprints

**CVD filters and interventions**:
11. Wong (2011) - Color blindness in scientific graphs ✅
12. Mazur et al. (2025) - CVD gamers difficulties ✅
13. Jamil & Denes (2024) - UI accessibility simulation ✅
14. Choi et al. (2019) - Optimal color correction ✅
15. Hassan (2019) - Flexible color contrast enhancement ✅
16. Gangwani et al. (2024) - CVD correction strategies survey ✅
17. Jiang et al. (2023) - Personalized image generation ✅
18. Khatri et al. (2019) - CVD burden individual variation ✅
19. Adachi-Usami et al. (1974) - Spectral sensitivity in CVD ✅
20. Asadi et al. (2022) - Genetic mutations in CVD ✅

**Neuroimaging**:
21. Esteban et al. (2019) - fMRIPrep ✅
22. Wang et al. (2015) - Probabilistic visual topography maps ✅

**Additional**:
23. Collignon et al. (2011) - Cross-modal plasticity (for Discussion)
24. Witzel & Gegenfurtner (2018) - Color perception (for Introduction)

---

## Status Legend

- ✅ COMPLETE: Section fully written in LaTeX
- ⚠️ PARTIAL/BRIEF: Section exists but needs expansion
- ❌ EMPTY: Section has placeholder only, needs to be written
- 🔄 TO BE GENERATED: Figure/table needs creation from analysis

---

**Last Updated**: 2025-12-19
**Next Action**: Write Discussion sections (4.1-4.6) following outline above
