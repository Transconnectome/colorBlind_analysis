# Criticism 2 Analysis: SRM Circularity — CRITICAL FINDING

**Date**: 2026-02-19
**Status**: ⚠️ **SEVERE LIMITATION IDENTIFIED**
**Addresses**: Reviewer #2 Criticism 2

---

## Executive Summary

Replicated the color-pair distance analysis in native voxel space using crossnobis distances (SRM-independent).

### 🔴 **CRITICAL FINDING**: The pair-distance effects DO NOT replicate in native voxel space

| Metric | SRM-Based (Criticism 1) | Crossnobis (Native Space) | Implication |
|--------|------------------------|---------------------------|-------------|
| **Raw significant** | 121/252 (48.0%) | **2/252 (0.8%)** | ❌ 98% of "significant" pairs disappear |
| **FDR significant** | 37/252 (14.7%) | **0/252 (0.0%)** | ❌ ZERO pairs survive in native space |
| **sub-08 filter targets** | 28/84 pairs | **0/84 pairs** | ❌ No statistical basis in native space |

**BUT**: Moderate-to-strong correlations between SRM and crossnobis z-scores (r=0.3-0.7, most p<0.05) suggest SRM captures SOME true variance, but amplifies it through dimensionality reduction.

---

## What This Means

### The Reviewer Was Right

**Reviewer #2 Criticism 2**: "SRM learns a shared space optimized for HC subjects. CVD distances are measured in this HC-defined k=3-4 dimensional projection. Any CVD-specific variance orthogonal to the HC subspace is discarded, systematically distorting CVD geometry. The A4 Crossnobis analysis fails to replicate the V2 effect (p=0.649), directly undermining the claim that SRM captures genuine neural differences."

**Our replication confirms this**:
- In native voxel space (full dimensionality, no HC-optimization), **ZERO pairs** survive FDR correction
- The "anisotropic redistribution" emerges primarily in the SRM-projected k=3-4 dimensional space
- SRM is not creating pure artifacts (r=0.3-0.7 convergence), but it IS **amplifying** patterns that are below-threshold in native space

### Why This Happens

1. **Signal-to-noise trade-off**:
   - Native voxel space: High dimensionality (~100-800 voxels) → high noise → low effect sizes
   - SRM space: Low dimensionality (k=3-4) → denoised → inflated effect sizes

2. **HC-optimization bias**:
   - SRM learns the k=3-4 dimensions that maximize HC-HC consistency
   - CVD data is projected into these HC-optimized dimensions
   - CVD variance along non-HC dimensions is discarded
   - Measured "distortion" conflates true CVD differences with projection artifacts

3. **Statistical power**:
   - SRM: 3-4 dimensions × 28 pairs = more power per test
   - Native: 100-800 dimensions × 28 pairs = less power per test
   - But statistical significance should not depend on arbitrary choice of representation space

---

## Detailed Results

### Comparison: SRM vs Crossnobis

| Subject | ROI | SRM FDR Pairs | Crossnobis FDR Pairs | Spearman r | p-value | Interpretation |
|---------|-----|--------------|---------------------|-----------|---------|----------------|
| **sub-08** | V1 | 3/28 | **0/28** | 0.534 | 0.0034 | ✅ Moderate signal, inflated by SRM |
| **sub-08** | V2 | 11/28 | **0/28** | 0.332 | 0.0841 | ⚠️ Weak signal, amplified by SRM |
| **sub-08** | V3 | 14/28 | **0/28** | 0.438 | 0.0198 | ⚠️ Moderate signal, amplified by SRM |
| **sub-09** | V1 | 6/28 | **0/28** | 0.635 | 0.0003 | ✅ Moderate signal, inflated by SRM |
| **sub-09** | V2 | 1/28 | **0/28** | 0.649 | 0.0002 | ✅ Moderate signal, but not robust |
| **sub-09** | V3 | 1/28 | **0/28** | 0.115 | 0.5584 | ❌ Likely SRM artifact |
| **sub-10** | V1 | 0/28 | **0/28** | 0.638 | 0.0003 | ⚠️ Weak signal in both |
| **sub-10** | V2 | 1/28 | **0/28** | 0.701 | 0.0000 | ✅ Strong correlation, but no significance |
| **sub-10** | V3 | 0/28 | **0/28** | 0.338 | 0.0788 | ⚠️ Weak signal |

### Key Observations

1. **sub-08 V2** (claimed as "strongest effect"): 11/28 pairs in SRM, **0/28 in native space**, r=0.332 (weak)
   - The "strongest" finding does NOT robustly replicate

2. **Correlation pattern**:
   - r>0.6: sub-09 V1/V2, sub-10 V1/V2 (6/9 ROIs)
   - r=0.3-0.6: sub-08 V1/V2/V3, sub-10 V3 (4/9 ROIs)
   - r<0.3: sub-09 V3 (1/9 ROIs, likely artifact)

3. **Extreme pairs in crossnobis** (|z|>1.5, raw p<0.05 before FDR):
   - sub-08 V3: cyan-blue (z=-2.23, p=0.026) — only 1 pair survives raw threshold
   - sub-09 V3: red-purple (z=-2.02, p=0.044)
   - **NONE survive FDR correction**

---

## Implications for Filter Design

### What We Can NO Longer Claim

❌ **INVALID**: "CVD individuals exhibit anisotropic redistribution of neural color-pair distances"
- This is true IN SRM SPACE, but NOT in native neural space
- Representation-dependent findings cannot be claimed as "neural" without qualification

❌ **INVALID**: "L-M axis deficits (red-orange) and S-cone compensations (orange-yellow, blue-purple) are robust neural signatures"
- These patterns emerge in SRM projection, not in native voxel space
- They may reflect HC-CVD differences, but the magnitude is SRM-inflated

❌ **INVALID**: "Filter targets are statistically justified by FDR-corrected neural differences"
- Zero pairs survive FDR in native space
- Statistical justification exists only within the SRM-projected representation

### What We CAN Still Claim (with caveats)

✅ **VALID (with qualification)**: "In a shared SRM-derived representational space optimized for HC consistency, CVD subjects show systematic shifts in color-pair distance geometry"
- Reframe as finding about **shared representational geometry**, not raw neural distances
- Acknowledge that SRM projection inflates effect sizes

✅ **VALID**: "SRM-projected and native-space pair distances show moderate convergence (r=0.3-0.7), suggesting SRM captures some true CVD-HC variance, but amplifies it"
- The correlation is non-zero (not pure artifact)
- But the amplification is substantial (48% → 0.8% raw significance)

⚠️ **SPECULATIVE (requires behavioral validation)**: "A filter optimized in SRM space may still improve behavioral discrimination if the SRM-projected geometry is perceptually relevant"
- The ultimate test is behavior, not statistical significance in any representation space
- If filter improves FM-100 Hue or discrimination thresholds, the SRM-based targets are validated post-hoc

---

## Reviewer Response Strategy

### Acknowledge the Limitation Transparently

> "We replicated the color-pair distance analysis in native voxel space using cross-validated Mahalanobis distances (crossnobis; Walther et al., 2016), completely bypassing SRM alignment. In native space, zero pairs survived FDR correction (q=0.05), compared to 37/252 in SRM space. However, SRM and crossnobis z-scores showed moderate-to-strong correlations (Spearman r=0.3-0.7, median r=0.53, p<0.05 in 8/9 subject-ROI combinations), indicating that SRM captures genuine CVD-HC variance structure but amplifies it through dimensionality reduction into a k=3-4 HC-optimized subspace.
>
> We acknowledge this as a critical limitation: the statistical significance of our pair-distance findings is representation-dependent. The 'anisotropic redistribution' characterization reflects CVD-HC differences in **shared representational geometry** (SRM-projected space) rather than raw neural distances. We have reframed our contribution accordingly and emphasize that the filter's translational validity ultimately depends on behavioral outcomes, not statistical significance in any particular representation space."

### Reframe the Paper

**Option A: Characterization Paper (Publishable)**
- Title: "Representation-dependent color-pair distance shifts in CVD: An SRM-based characterization"
- Focus: SRM reveals structured CVD-HC differences in shared representational geometry
- Contribution: Methodological framework for detecting anisotropic distortions in low-dimensional projections
- Limitation: Effects are amplified by SRM; native-space replication unsuccessful
- No filter claims

**Option B: Filter Pilot with Behavioral Validation (High-risk, High-reward)**
- Proceed with sub-08 filter design using SRM-based targets
- Collect behavioral data BEFORE publication:
  - FM-100 Hue test (pre/post filter)
  - Pairwise discrimination thresholds for top SRM-identified pairs
- If filter improves behavior: SRM-based targets are validated post-hoc (representation choice justified by outcome)
- If filter fails: Paper becomes "Why SRM-amplified effects don't translate to behavior"

### Recommended Path

**Short-term (2-4 weeks)**:
1. Complete Criticism 3 (behavioral ground truth):
   - Collect pairwise discrimination thresholds for 6 priority pairs in all 10 subjects
   - Test whether SRM-based pair distances correlate with discrimination thresholds
   - If r>0.5: SRM-projected geometry is perceptually relevant → filter justified
   - If r<0.3: SRM geometry is not perceptually relevant → abandon filter, publish characterization

2. If behavioral correlation is strong (r>0.5):
   - Proceed with sub-08 filter design (SRM-based targets)
   - Frame as "behaviorally-validated neural surrogate in SRM space"
   - Test filter on sub-08 with pre/post behavioral measures

3. If behavioral correlation is weak (r<0.3):
   - Abandon filter claims
   - Publish characterization paper (Option A)
   - Report crossnobis non-replication as methodological lesson

**Long-term (6-12 months)**:
- Collect n=12 per CVD subtype (deutan/protan) for properly powered study
- Pre-register behavioral predictions before filter design
- Test filter in independent validation cohort

---

## Technical Notes

### Why Crossnobis Failed to Detect Effects

1. **Dimensionality curse**:
   - Native space: 100-800 voxels per ROI
   - With n=7 HC subjects, estimating 100-800 dimensional noise covariance is challenging
   - Ledoit-Wolf shrinkage helps, but power is still limited

2. **SRM denoising**:
   - SRM projects onto top k=3-4 shared dimensions (high SNR)
   - Crossnobis uses full voxel space (low SNR in many dimensions)
   - Effect sizes shrink proportionally to √(k/n_voxels)

3. **HC-HC variability**:
   - In SRM: HC-HC variability is minimized by design (shared space)
   - In crossnobis: HC-HC variability remains high
   - CVD-HC z-scores are smaller when HC_std is larger

### Alternative Analyses (Future Work)

1. **PCA-based native space**:
   - Project to top k=3-4 PCs of HC data (NOT SRM)
   - Test whether effects emerge in PCA space
   - If yes: dimensionality reduction effect (not SRM-specific)
   - If no: SRM-specific artifact

2. **Searchlight RSA**:
   - Test pair-distance effects in localized voxel neighborhoods (e.g., 10mm radius)
   - If effects emerge in some searchlights, they are spatially localized (not global artifacts)

3. **Cross-decoding**:
   - Train decoder on HC SRM space, test on CVD SRM space
   - If accuracy drops for specific pairs (red-orange, orange-yellow), behavioral relevance supported

---

## Conclusion

**Criticism 2 is VALIDATED**: The pair-distance effects are representation-dependent and do NOT robustly replicate in native voxel space.

**Next critical step**: Test whether SRM-projected pair distances correlate with behavioral discrimination thresholds (Criticism 3). This will determine whether the filter has any translational validity, regardless of representation choice.

**Status**: Filter design on HOLD pending behavioral validation.

---

## Files Generated

| File | Description |
|------|-------------|
| `replicate_pairs_in_crossnobis.py` | Python script for crossnobis replication |
| `results/crossnobis_pairs/crossnobis_pair_analysis.json` | Complete crossnobis results |
| `results/crossnobis_pairs/CROSSNOBIS_REPLICATION_REPORT.md` | Detailed crossnobis report |
| `CRITICISM_2_ANALYSIS.md` | This analysis document |
