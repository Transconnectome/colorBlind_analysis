# PCA Dimensionality Reduction Analysis - Complete Summary

**Date**: 2026-02-09
**Status**: ✅ COMPLETE - PCA effects tested and compared with Procrustes

---

## Executive Summary

**Key Finding**: PCA dimensionality reduction on raw fMRI data provides **minimal improvement** and remains **far inferior to Procrustes alignment**.

**Bottom Line**:
- PCA vs Raw: +0.041 decoding improvement (70% cases)
- Procrustes vs PCA: +0.420 decoding advantage (100% cases)
- **Recommendation**: Use Procrustes, not PCA

---

## Motivation

After observing MDS (Multi-Dimensional Scaling) analysis results, hypothesis was that PCA dimensionality reduction on raw (non-Procrustes) data might improve performance by:
1. Filtering low-variance noise components
2. Reducing high-dimensional noise
3. Focusing on principal signal-carrying dimensions

---

## Methods

### PCA Configurations Tested

**Variance-based** (keep X% of variance):
- **95% variance**: ~31 components (mean)
- **90% variance**: ~25 components
- **85% variance**: ~20 components
- **80% variance**: ~17 components

**Fixed components** (for reference):
- 50, 100, 150 components

### Comparison Conditions

1. **Raw**: No processing (baseline)
2. **Raw + PCA**: Various PCA configurations
3. **Best PCA**: Optimal config per subject-ROI
4. **Procrustes**: Reference standard
5. **Procrustes + PCA95**: Optional test

### Metrics

- **RDM Reliability**: Split-half Spearman correlation
- **Decoding Accuracy**: LORO cross-validation (8-class LDA)
- **N_components**: Actual components retained
- **Variance Explained**: Cumulative variance captured

---

## Results

### Overall Performance (n=40 subject-ROI pairs)

| Method | RDM Reliability | Decoding Accuracy | Improvement |
|--------|----------------|-------------------|-------------|
| **Raw** | 0.004 ± 0.197 | 0.131 ± 0.049 | (baseline) |
| **PCA 95%** | -0.014 ± 0.170 | 0.125 ± 0.046 | **-0.006** ❌ |
| **PCA 90%** | -0.026 ± 0.175 | 0.133 ± 0.040 | +0.002 |
| **PCA 85%** | -0.013 ± 0.184 | **0.142 ± 0.050** | +0.011 ✓ |
| **PCA 80%** | -0.013 ± 0.171 | 0.135 ± 0.047 | +0.004 |
| **Best PCA** | 0.043 ± 0.166 | 0.172 ± 0.037 | **+0.041** ✓ |
| **Procrustes** | 0.381 ± 0.278 | 0.592 ± 0.121 | **+0.461** ✅ |

**Key Observations**:
1. Most PCA configs **worse or marginally better** than raw
2. Best PCA (optimal per subject) shows modest improvement
3. Procrustes **11× more effective** than best PCA

---

## Detailed Findings

### 1. PCA vs Raw Performance

**Improvements over Raw**:
- RDM reliability: +0.037 (70% positive cases)
- Decoding accuracy: +0.041 (70% positive cases)

**Analysis**:
- 30% of cases show degradation with PCA
- Improvement magnitude very small (+0.04)
- Absolute performance remains poor (0.172 decoding)

### 2. Procrustes vs PCA Performance

**Procrustes Advantage**:
- RDM reliability: +0.340 over best PCA (82.5% win rate)
- Decoding accuracy: +0.420 over best PCA (100% win rate)

**Critical**: No single case where PCA outperforms Procrustes for decoding

### 3. PCA Configuration Effects

**Best Configuration**: Variance 85% (20 components)
- Decoding: 0.142 (best average across subjects)
- RDM: -0.013 (still negative!)

**Variance Threshold Trade-off**:
- **Higher threshold** (95%): More components, preserves noise
- **Lower threshold** (80%): Fewer components, may lose signal
- **Sweet spot**: 85% variance (~20 components)

**Component Count by ROI**:
- V1: Largest (~40+ components at 95%)
- V2: Moderate (~35 components at 95%)
- V3: Small (~15 components at 95%)
- V4: Smallest (~10 components at 95%)

### 4. Why PCA Fails

**Four Key Reasons**:

1. **Geometric Misalignment Dominates**:
   - Between-run geometric variance 16× larger than signal
   - PCA doesn't correct rotation/reflection
   - Each run remains in different coordinate system

2. **Signal-Noise Mixing in PCs**:
   - Color signal not concentrated in top PCs
   - Noise not restricted to low-variance PCs
   - PCA can't separate signal from noise effectively

3. **Insufficient Dimensionality Reduction**:
   - 17-31 components still high-dimensional
   - Not enough to escape curse of dimensionality
   - Color signal requires many voxels

4. **Wrong Problem Addressed**:
   - PCA solves: "Too many noisy dimensions"
   - Actual problem: "Runs in different coordinate systems"
   - Need alignment, not dimensionality reduction

---

## Comparison with Literature

### Expected PCA Benefits

Literature typically reports PCA benefits for:
1. **Single-run analysis**: No between-run misalignment
2. **Aligned data**: After registration/normalization
3. **High SNR data**: Clear signal in top PCs
4. **Category decoding**: Large signal differences

### Why Our Case Differs

1. **Multi-run design**: Geometric variance compounds
2. **No alignment**: Raw runs in arbitrary orientations
3. **Low SNR**: Weak color signal (~2-3% BOLD)
4. **Fine discrimination**: 8 similar colors, not categories

---

## Statistical Tests

### PCA vs Raw

| Metric | Mean Diff | % Positive | Wilcoxon p |
|--------|-----------|------------|------------|
| RDM | +0.037 | 70% | 0.034* |
| Decoding | +0.041 | 70% | 0.002** |

**Interpretation**: Statistically significant but small effect

### Procrustes vs Best PCA

| Metric | Mean Diff | % Positive | Wilcoxon p |
|--------|-----------|------------|------------|
| RDM | +0.340 | 82.5% | < 1e-6*** |
| Decoding | +0.420 | 100% | < 1e-10*** |

**Interpretation**: Huge and highly significant difference

---

## Individual Subject Analysis

### Best Performers with PCA (Decoding)

| Subject-ROI | Raw | Best PCA | Procrustes | PCA Gain | Proc Gain |
|-------------|-----|----------|------------|----------|-----------|
| sub-05 V4 | 0.104 | **0.208** | 0.708 | +0.104 | +0.604 |
| sub-02 V3 | 0.104 | **0.208** | 0.729 | +0.104 | +0.625 |
| sub-06 V3 | 0.208 | **0.250** | 0.708 | +0.042 | +0.500 |

**Observation**: Even best PCA cases still **far below Procrustes** (0.21 vs 0.71)

### Worst Performers with PCA

| Subject-ROI | Raw | Best PCA | Procrustes | PCA Change | Proc Gain |
|-------------|-----|----------|------------|------------|-----------|
| sub-07 V2 | 0.042 | **0.021** | 0.313 | -0.021 ❌ | +0.271 |
| sub-01 V1 | 0.125 | **0.083** | 0.729 | -0.042 ❌ | +0.604 |

**Observation**: PCA can hurt performance in some cases

---

## Visualization Summary

### Figure 1: PCA Effects Summary (6-panel)

**Panel A**: RDM Reliability by configuration
- Shows all PCA configs vs raw vs Procrustes
- PCA configs cluster near zero, Procrustes much higher

**Panel B**: Decoding Accuracy by configuration
- Similar pattern: PCA marginally above chance
- Procrustes far superior

**Panel C**: N_components vs RDM reliability
- No clear relationship
- More components ≠ better performance

**Panel D**: RDM Improvement distribution (PCA - Raw)
- Most improvements small and centered near zero
- 30% show negative improvement

**Panel E**: Decoding Improvement distribution
- Similar to RDM: small improvements
- Variance threshold doesn't matter much

**Panel F**: Variance Explained vs N_components
- Shows 80-95% thresholds capture 17-31 components
- Linear relationship as expected

### Figure 2: PCA vs Procrustes (3-panel)

**Panel A**: Boxplot comparison (Raw, Best PCA, Procrustes)
- Clear hierarchy: Raw < PCA < Procrustes
- PCA only slightly above raw

**Panel B**: Decoding comparison
- Procrustes mean: 0.59
- Best PCA mean: 0.17
- 3.5× difference

**Panel C**: Scatter plot (PCA vs Procrustes per subject)
- All points below diagonal (Procrustes wins)
- Procrustes wins: 40/40 (100%)

---

## Procrustes + PCA Test (Optional)

**Question**: Does PCA help after Procrustes?

**Result**: Mixed
- Procrustes alone: RDM 0.381, Decoding 0.592
- Procrustes + PCA95: RDM varies, Decoding ~0.59

**Interpretation**:
- Minimal benefit from PCA on top of Procrustes
- Alignment solves the main problem
- Additional dimensionality reduction not needed

---

## Theoretical Interpretation

### What Procrustes Solves (that PCA doesn't)

**Geometric Misalignment**:
- Between runs: Rotation, reflection
- Magnitude: 16× larger than signal
- Solution: Orthogonal transformation to common reference
- Effect: Aligns coordinate systems

**PCA's Limitations**:
- Operates within each run's coordinate system
- Can't relate different coordinate systems
- Dimensionality reduction ≠ alignment

### Why Alignment > Dimensionality Reduction

**Signal Structure**:
- Color representations: Distributed across many voxels
- Geometric: Consistent orientation matters
- Low-dimensional manifold but needs alignment first

**Analogy**:
- PCA: Looking at rotated images through narrower lens
- Procrustes: Rotating images to same orientation
- Need orientation before dimensionality matters

---

## Recommendations

### For Current Analysis

1. ❌ **Do NOT use PCA instead of Procrustes**
   - Only 0.172 decoding vs 0.592 with Procrustes
   - 100% of cases show Procrustes advantage

2. ✅ **Continue using Procrustes**
   - Addresses fundamental geometric misalignment
   - 11× more effective than PCA

3. ⚠️ **PCA after Procrustes: Optional**
   - Small benefit (~0-5% improvement)
   - Adds complexity without substantial gain
   - Not recommended for routine use

### For Future Studies

1. **If Between-Run Alignment Important**: Use Procrustes first
2. **If Dimensionality Matters**: Consider PCA after alignment
3. **If Computational Cost Matters**: Raw → Procrustes → Analysis (skip PCA)

### When PCA Might Help

PCA could be beneficial if:
1. **Single-run analysis**: No between-run misalignment
2. **Already aligned**: After Procrustes or registration
3. **Very high-dimensional**: 1000+ voxels per ROI
4. **Computational constraints**: Need faster decoding

**BUT**: For color fMRI analysis, Procrustes solves main problem

---

## Alternative Approaches Considered

### 1. CCA (Canonical Correlation Analysis)
- **Purpose**: Find maximally correlated projections between runs
- **Why not tested**: More complex than PCA, no clear advantage
- **Future**: Could test if PCA shows promise (it doesn't)

### 2. ICA (Independent Component Analysis)
- **Purpose**: Find independent signal sources
- **Why not tested**: Signal assumption (independence) questionable
- **Future**: Might help separate BOLD from artifacts

### 3. Procrustes → PCA
- **Purpose**: Align first, then reduce dimensionality
- **Tested**: Procrustes + PCA95%
- **Result**: Minimal benefit over Procrustes alone

### 4. Whitening → Procrustes
- **Already tested**: Failed (see `updated_noise_procrustes.md`)
- **Result**: 47-92% degradation
- **Reason**: Covariance includes signal, not just noise

---

## Conclusions

### Main Findings

1. **PCA Provides Minimal Benefit**:
   - +0.041 decoding improvement over raw
   - 70% positive cases (30% degradation)
   - Absolute performance poor (0.172)

2. **Procrustes Remains Superior**:
   - 11× more effective than PCA
   - 100% cases show improvement
   - Addresses fundamental misalignment

3. **Geometric Misalignment Dominates**:
   - 16× larger than signal
   - PCA can't fix this
   - Alignment essential

4. **Dimensionality Reduction Insufficient**:
   - Color signal needs many voxels
   - 17-31 components too few
   - Noise mixed with signal in PCs

### Key Insight

> "The primary problem in multi-run fMRI color data is **geometric misalignment between runs**, not high-dimensional noise. PCA reduces dimensionality but doesn't align coordinate systems, leaving the fundamental problem unsolved. Procrustes alignment addresses the root cause and provides 11× better performance than PCA."

### Final Recommendation

✅ **Use C010 + Procrustes** (no PCA)
- Simplest effective pipeline
- Best performance (0.592 decoding)
- No unnecessary complexity

---

## Data and Code

### Generated Files

**Visualizations**:
```
pca_analysis/pca_effects_summary.png       # 6-panel PCA effects
pca_analysis/pca_vs_procrustes.png         # 3-panel comparison
```

**Data**:
```
pca_analysis/pca_analysis_summary.json     # Summary statistics
pca_analysis/pca_analysis_detailed.csv     # Per subject-ROI results
```

### Analysis Script

```bash
analyze_pca_effects.py    # Main PCA analysis script
```

**Run time**: ~5-10 minutes (40 subjects × multiple PCA configs)

---

## Acknowledgments

**Analysis Date**: 2026-02-09
**Motivation**: User observation from MDS analysis suggesting PCA might help
**Result**: Systematic testing confirms Procrustes superiority

**Related Documentation**:
- `DECODING_VALIDATION_SUMMARY.md` - Procrustes validation
- `updated_noise_procrustes.md` - Procrustes vs whitening
- `README.md` - Overall preprocessing validation

---

**Status**: ✅ **ANALYSIS COMPLETE** - PCA tested and found inferior to Procrustes
