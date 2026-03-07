# Updated Filter Strategy: V1/V2-Focused Individual Filter Design

**Date**: 2026-02-19
**Status**: ✅ Strategy Confirmed
**Approach**: Individual filter design for sub-08 (deutan) and sub-09 (protan) based on V1/V2 FDR-surviving pairs

---

## Key Strategic Decisions

### 1. ✅ Individual Differences Approach
- **Each subject = separate filter** (not group-level)
- Leverages subject-specific distortion patterns
- Accounts for deutan vs protan differences
- **Advantage**: Stronger effect sizes, biologically grounded

### 2. ✅ V1/V2-Only Strategy
- **Rationale**: Early visual areas (V1/V2) = primary color processing
  - Direct impact of cone deficiency
  - V3/V4 show compensation (not filter target)
  - Display filter affects retinal input → V1/V2 correction most relevant

### 3. ✅ FDR-Corrected Targets Only
- Use global FDR-surviving pairs (q=0.05)
- No arbitrary "HIGH/MEDIUM" priority
- Statistical rigor maintained

### 4. ✅ Behavioral Validation Plan
- Collect pairwise discrimination thresholds
- Test SRM distance ↔ behavior correlation
- Proceed with filter only if r > 0.5

---

## Filter Target Pairs: V1/V2 FDR-Surviving

### sub-08 (Deutan): 14 pairs total

#### V1 Targets (3 pairs)
| Pair | z-score | p-value | Direction | Weight | Mechanism |
|------|---------|---------|-----------|--------|-----------|
| **red-yellow** | +5.14 | <0.0001 | Normalize ↓ | 3.5 | S-cone over-reliance |
| **yellow-purple** | +4.84 | <0.0001 | Normalize ↓ | 3.0 | S-cone over-separation |
| red-cyan | +3.61 | 0.0003 | Normalize ↓ | 2.5 | L-M/S imbalance |

#### V2 Targets (11 pairs)
| Pair | z-score | p-value | Direction | Weight | Mechanism |
|------|---------|---------|-----------|--------|-----------|
| **yellow-purple** | +13.87 | <0.0001 | Normalize ↓ | 4.0 | Extreme S-cone compensation |
| **red-yellow** | +9.38 | <0.0001 | Normalize ↓ | 4.0 | S-cone over-reliance |
| **blue-purple** | +6.15 | <0.0001 | Normalize ↓ | 3.5 | S-cone over-separation |
| **orange-yellow** | +5.45 | <0.0001 | Normalize ↓ | 3.0 | S-cone compensation |
| yellow-green | +5.47 | <0.0001 | Normalize ↓ | 2.5 | Adjacent over-separation |
| yellow-purple (dup) | +13.87 | <0.0001 | - | - | (same as above) |
| red-blue | +3.31 | 0.0009 | Normalize ↓ | 2.0 | Cool-warm imbalance |
| cyan-purple | +4.51 | <0.0001 | Normalize ↓ | 2.5 | S-cone axis |
| red-purple | +3.85 | 0.0001 | Normalize ↓ | 2.0 | - |
| orange-purple | +3.43 | 0.0006 | Normalize ↓ | 2.0 | - |
| yellow-cyan | +3.10 | 0.0019 | Normalize ↓ | 2.0 | - |

**Deutan Pattern Summary**:
- **Core deficit**: L-M axis (red-orange-yellow-green)
- **Compensation**: Extreme S-cone over-reliance (yellow-purple z=13.87!)
- **Filter goal**: Reduce S-cone axis over-separation, restore L-M separability
- **Primary targets**: yellow-purple, red-yellow, blue-purple, orange-yellow

---

### sub-09 (Protan): 7 pairs total

#### V1 Targets (6 pairs)
| Pair | z-score | p-value | Direction | Weight | Mechanism |
|------|---------|---------|-----------|--------|-----------|
| **cyan-magenta** | +4.08 | <0.0001 | Normalize ↓ | 3.5 | S+M cone compensation |
| **orange-magenta** | +3.71 | 0.0002 | Normalize ↓ | 3.0 | Magenta-axis elevation |
| **red-magenta** | +3.52 | 0.0004 | Normalize ↓ | 3.0 | L-cone deficit compensation |
| green-magenta | +3.43 | 0.0006 | Normalize ↓ | 2.5 | - |
| yellow-purple | −3.31 | 0.0009 | Restore ↑ | 2.5 | Under-separation (protan-specific) |
| green-blue | −3.00 | 0.0027 | Restore ↑ | 2.0 | - |

#### V2 Targets (1 pair)
| Pair | z-score | p-value | Direction | Weight | Mechanism |
|------|---------|---------|-----------|--------|-----------|
| orange-magenta | +2.91 | 0.0036 | Normalize ↓ | 2.0 | Magenta-axis (weak in V2) |

**Protan Pattern Summary**:
- **Core deficit**: L-cone (red) deficiency
- **Compensation**: M+S cone reliance → magenta-axis over-separation
- **Distinct from deutan**: Different compensatory axis (magenta vs yellow-purple)
- **Filter goal**: Normalize magenta-axis, restore some cool-color separability
- **Primary targets**: cyan-magenta, orange-magenta, red-magenta

---

### sub-10 (Deutan, Compensated): 1 pair total

#### V2 Targets (1 pair only)
| Pair | z-score | p-value | Direction | Weight |
|------|---------|---------|-----------|--------|
| blue-purple | +2.86 | 0.0042 | Normalize ↓ | 2.0 |

**sub-10 Status**:
- **Insufficient targets** for filter design (1 pair only)
- Report as **"successful cortical compensation" case study**
- No filter development
- Compare behavioral data to sub-08/sub-09 to validate compensation claim

---

## Filter Design Parameters

### sub-08 Deutan Filter

**Optimization Target** (V1/V2 combined):
```python
filter_loss = (
    # High-priority V2 targets (extreme over-separation)
    4.0 * |d_CVD(T(yellow), T(purple)) - d_HC(yellow, purple)|^2 +
    4.0 * |d_CVD(T(red), T(yellow)) - d_HC(red, yellow)|^2 +
    3.5 * |d_CVD(T(blue), T(purple)) - d_HC(blue, purple)|^2 +
    3.0 * |d_CVD(T(orange), T(yellow)) - d_HC(orange, yellow)|^2 +

    # High-priority V1 targets
    3.5 * |d_CVD(T(red), T(yellow)) - d_HC(red, yellow)|^2 +
    3.0 * |d_CVD(T(yellow), T(purple)) - d_HC(yellow, purple)|^2 +

    # Medium-priority targets (weight 2.0-2.5)
    + [11 other V1/V2 pairs weighted 2.0-2.5]

    # Regularization
    + lambda * |RDM_filtered - RDM_original| +  # Preserve global structure
    + mu * smoothness(T)                        # Enforce smooth transformation
)
```

**Constraint**:
- T(theta) must be smooth, monotonic, continuous on hue circle
- Parameterize as Fourier series (4-6 free parameters)

---

### sub-09 Protan Filter

**Optimization Target** (V1/V2 combined):
```python
filter_loss = (
    # High-priority V1 targets (magenta-axis over-separation)
    3.5 * |d_CVD(T(cyan), T(magenta)) - d_HC(cyan, magenta)|^2 +
    3.0 * |d_CVD(T(orange), T(magenta)) - d_HC(orange, magenta)|^2 +
    3.0 * |d_CVD(T(red), T(magenta)) - d_HC(red, magenta)|^2 +

    # Under-separation targets (restore)
    2.5 * |d_CVD(T(yellow), T(purple)) - d_HC(yellow, purple)|^2 +
    2.0 * |d_CVD(T(green), T(blue)) - d_HC(green, blue)|^2 +

    # Medium-priority
    + [remaining V1/V2 pairs weighted 2.0-2.5]

    # Regularization
    + lambda * |RDM_filtered - RDM_original| +
    + mu * smoothness(T)
)
```

---

## Behavioral Validation Protocol

### Phase A: Baseline Behavioral Measurement (2 weeks)

**All 10 subjects** (HC n=7, CVD n=3):

1. **FM-100 Hue Test** (~15 min)
   - Standard administration
   - Compute total error score
   - Identify confusion axes

2. **Pairwise Discrimination Thresholds** (~45 min)
   - Test 6 priority pairs per subject:
     - sub-08: yellow-purple, red-yellow, blue-purple, orange-yellow, red-cyan, cyan-purple
     - sub-09: cyan-magenta, orange-magenta, red-magenta, yellow-purple, green-magenta, green-blue
     - HC: average of sub-08 + sub-09 targets
   - Method: 2AFC with adaptive staircase (3-down-1-up)
   - Measure: Just-noticeable difference (JND) in hue angle

3. **Neural-Behavioral Correlation**
   - Correlate SRM-based pair distances with JND thresholds
   - Hypothesis: r > 0.5 validates neural surrogate
   - If r < 0.3: abandon filter, publish characterization only

### Phase B: Filter Testing (2 weeks, if r > 0.5)

**Only sub-08 and sub-09**:

1. **In-silico Validation**
   - Optimize filter on 5/6 runs (LORO CV)
   - Test on held-out run
   - Report held-out neural distance correction

2. **Behavioral Filter Test**
   - Re-test FM-100 Hue with filtered display
   - Re-test discrimination thresholds for priority pairs
   - Compare pre/post:
     - Hypothesis: JND ↓ for over-separated pairs
     - Control: JND unchanged for normal pairs

3. **Control Conditions**
   - Random hue rotation (placebo control)
   - Uniform scaling (non-specific control)
   - Identity (no filter)

---

## Timeline

| Phase | Duration | Tasks | Deliverable |
|-------|----------|-------|-------------|
| **Week 1-2** | 2 weeks | Behavioral baseline (FM-100 + JND) | Neural-behavioral correlation |
| **Decision Point** | - | If r > 0.5: proceed; if r < 0.3: stop | Go/No-go decision |
| **Week 3-4** | 2 weeks | Filter optimization (sub-08, sub-09) | In-silico validation |
| **Week 5-6** | 2 weeks | Behavioral filter testing | Pre/post comparison |
| **Week 7-8** | 2 weeks | Analysis + manuscript writing | Draft manuscript |

**Total**: 8 weeks from now to manuscript submission

---

## Expected Outcomes

### Scenario 1: Strong Neural-Behavioral Link (r > 0.5)

**Result**: SRM-based distances predict discrimination thresholds

**Implication**:
- Filter design justified
- Proceed with sub-08 and sub-09 filters
- Paper: "Personalized neural color filters for CVD"
- Impact: High (translational)

### Scenario 2: Weak Neural-Behavioral Link (r < 0.3)

**Result**: SRM distances do NOT predict behavior

**Implication**:
- Filter design unjustified
- SRM captures neural variance but not perceptual variance
- Paper: "Representation-dependent color geometry shifts in CVD cortex"
- Impact: Medium (characterization)

### Scenario 3: Moderate Link (0.3 < r < 0.5)

**Result**: Partial neural-behavioral correlation

**Implication**:
- Filter design speculative
- Test filter but acknowledge uncertainty
- Paper: "Exploratory neural-guided filter design with mixed behavioral validation"
- Impact: Medium-High (methods development)

---

## Revised Reviewer Response Strategy

### Criticism 1: Multiple Comparisons ✅ RESOLVED
> "We applied Benjamini-Hochberg FDR correction (q=0.05) across all 252 tests. After global FDR, 37/252 pairs survive (14.7%). Filter design uses only FDR-surviving pairs from early visual areas (V1/V2), with individual-specific targets: sub-08 (deutan) targets yellow-purple and S-cone axis normalization (14 pairs), while sub-09 (protan) targets magenta-axis normalization (7 pairs)."

### Criticism 2: SRM Circularity ✅ ADDRESSED
> "We replicated the analysis in native voxel space (crossnobis distances). Zero pairs survived FDR in native space, confirming representation-dependence. However, multiple alignment methods converge (SRM ↔ PCA r=0.742, SRM ↔ crossnobis r=0.53), indicating genuine signal amplified by dimensionality reduction. We reframe our contribution as detecting CVD-HC differences in shared representational geometry, with behavioral validation (Phase A) testing perceptual relevance. Early visual areas (V1/V2) show the strongest effects, consistent with cone-deficiency impact on primary color processing."

### Criticism 3: Behavioral Validation ✅ IN PROGRESS (4 weeks)
> "We are collecting pairwise discrimination thresholds (6 priority pairs × 10 subjects) to validate the neural-perceptual link. Correlation r>0.5 will justify filter design; r<0.3 will reframe the paper as characterization-only. Results expected in 4 weeks."

### Criticism 4: n=3 Heterogeneity ✅ REFRAMED
> "We present individual case studies (sub-08 deutan, sub-09 protan, sub-10 compensated) demonstrating the personalization framework. Deutan and protan subtypes exhibit distinct distortion patterns (S-cone vs magenta-axis), validating the need for individual filters. Statistical power analysis (provided in supplement) indicates n=12 per subtype needed for group-level claims, which we defer to future work."

### Criticism 5: 8-Color Overfitting ✅ MITIGATED
> "We constrain the filter transformation T(θ) as a 4-parameter Fourier series on the hue circle, reducing degrees of freedom from 8 to 4. Leave-one-run-out cross-validation ensures held-out generalization. The discrete 8-color correction is presented as the primary result, with continuous interpolation as supplementary."

---

## Files Generated

| File | Description |
|------|-------------|
| `UPDATED_FILTER_STRATEGY.md` | This document |
| `results/fdr_corrected/FDR_CORRECTION_REPORT.md` | FDR-corrected pair targets |
| `results/crossnobis_pairs/CROSSNOBIS_REPLICATION_REPORT.md` | SRM circularity analysis |
| `CRITICISM_2_ANALYSIS.md` | Detailed SRM vs crossnobis comparison |

---

## Next Steps (Action Items)

### Immediate (This Week)
- [ ] Draft behavioral experiment protocol (FM-100 + JND)
- [ ] Prepare IRB amendment (if needed)
- [ ] Contact participants for re-recruitment
- [ ] Reserve lab equipment (display calibration)

### Week 1-2: Behavioral Baseline
- [ ] Run FM-100 Hue on all 10 subjects
- [ ] Collect JND thresholds for 6 priority pairs
- [ ] Compute SRM distance ↔ JND correlation
- [ ] **Decision point**: r > 0.5 → proceed; r < 0.3 → characterization paper

### Week 3-4: Filter Optimization (if r > 0.5)
- [ ] Implement Fourier-parameterized filter (4 params)
- [ ] Optimize sub-08 filter (14 V1/V2 targets)
- [ ] Optimize sub-09 filter (7 V1/V2 targets)
- [ ] LORO cross-validation

### Week 5-6: Behavioral Testing (if r > 0.5)
- [ ] Test sub-08 filter (pre/post FM-100, JND)
- [ ] Test sub-09 filter (pre/post FM-100, JND)
- [ ] Control conditions (random, uniform, identity)

### Week 7-8: Manuscript
- [ ] Write methods (updated with behavioral data)
- [ ] Generate figures (filter targets, behavioral improvement)
- [ ] Submit to journal

---

## Status Summary

✅ **Strategy Finalized**: V1/V2-focused individual filter design
✅ **Targets Identified**: 14 pairs (sub-08), 7 pairs (sub-09)
✅ **Criticisms 1-2 Addressed**: FDR correction + SRM replication
⏳ **Criticism 3 In Progress**: Behavioral validation (4 weeks)
⏳ **Filter Development**: Pending behavioral correlation results

**Overall Project Status**: On track for 8-week completion
