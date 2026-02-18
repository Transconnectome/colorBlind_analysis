# CVD Display Filter Design Plan

> Last updated: 2026-02-17
> Status: Planning (pre-implementation)
> Approach: Individual case-study filter design with neural surrogate + behavioral calibration

---

## 1. Background & Motivation

### 1.1 Research Context

This project investigates neural color representations in Color Vision Deficient (CVD) individuals using fMRI (8 colors, 45deg spacing, 4 ROIs: V1/V2/V3/hV4, HC n=7, CVD n=3).

**Goal**: Design personalized display color filters that correct CVD-specific color space distortion, guided by neural data and validated by behavior.

### 1.2 Key Findings from Phase 1-2

| Finding | Evidence | Implication |
|---------|----------|-------------|
| Global RDM structure preserved | HC-CVD RDM r=0.499 vs HC-HC r=0.517 (V2) | Total RDM matching is NOT the right target |
| CVD-HC disparity is color-agnostic | Permutation p=0.953 (V2) | Global disparity driven by signal-level, not color-specific differences |
| Per-pair anisotropic redistribution | Cross-subject consistent z-scores | Color-SPECIFIC distortion exists within global similarity |
| CVD decoding >= HC | CVD 68.4% vs HC 55.2% | Neural representations are functional; "correction" must be careful |
| Cortical compensation in higher areas | sub-10: V3 |z|=0.74, hV4 |z|=0.62 | V1/V2 distortion partially resolved in V3/hV4 |

### 1.3 Critical Revision: What the Data Actually Shows

**Original hypothesis** (rejected): CVD has globally reduced local separability.

**Actual finding**: CVD shows **anisotropic redistribution** of pairwise color distances:
- **L-M axis pairs reduced** (red-orange, red-green, orange-green) -- consistent with cone dysfunction
- **S-cone axis pairs increased** (orange-yellow, cyan-blue, red-magenta) -- compensatory reliance on S-cone
- Pattern is cross-subject consistent (3/3 CVD agree on direction for key pairs)

This maps directly to known CVD psychophysics (L-M confusion axis) and provides a specific, mechanistic filter target.

---

## 2. Red Team Review Summary (2026-02-17)

### 2.1 Criticisms Raised

| # | Criticism | Severity | Status |
|---|-----------|----------|--------|
| 1 | Permutation shows disparity is color-agnostic; filter targets color-specific correction | FATAL | **ADDRESSED** -- per-pair analysis reveals color-specific patterns within color-agnostic total |
| 2 | n=3 mixed-subtype CVD, non-significant after Bonferroni | FATAL | **ACCEPTED** -- reframed as individual case studies, not group claims |
| 3 | No behavioral data to validate neural-perceptual link | FATAL | **PLANNED** -- behavioral data collection as Phase B |
| 4 | Filter overparameterized (training r=0.999) | Addressable | **TODO** -- LORO CV, low-rank constraint, baseline comparison |
| 5 | Local separability hypothesis untested | Addressable | **DONE** -- Check 5 analysis completed, hypothesis revised |

### 2.2 Resolution of Criticism 1 (Permutation vs. Filter)

The permutation test evaluates **total disparity** (global signal + color pattern mixed). The total distance is dominated by global signal differences (SNR, magnitude), so shuffling color labels does not change it (p=0.953).

However, **per-pair z-score analysis** reveals that within this total, specific color pairs systematically deviate in consistent directions across all 3 CVD subjects. The permutation test lacks power for pair-specific effects because it shuffles all 28 pairs simultaneously.

**Remaining validation needed**: Pair-level permutation test to confirm specific pair z-scores exceed chance (see TODO #1).

### 2.3 Resolution of Criticism 2 (n=3)

The filter is designed as an **individual case study** for each CVD subject. No group-level claims are made. Each subject's filter is:
- Trained on their own data
- Validated with their own held-out runs (LORO)
- Calibrated with their own behavioral performance

Sub-type heterogeneity (2 deutan + 1 protan) becomes an advantage: it demonstrates the personalization framework works across CVD types.

---

## 3. Individual CVD Neural Profiles

### 3.1 Summary Table: Mean |z-score| from HC

| Subject | Type | V1 | V2 | V3 | hV4 | Mean | Filter Need |
|---------|------|-----|-----|-----|------|------|-------------|
| **sub-08** | Deutan | **1.40** | **1.67** | 1.18 | 1.47 | **1.43** | Strong |
| **sub-09** | Protan | 1.15 | 0.96 | 0.91 | 1.00 | 1.00 | Moderate |
| **sub-10** | Deutan | 0.94 | **1.11** | 0.74 | 0.62 | 0.85 | Weak (V2 only) |

### 3.2 Extreme Pair Counts (|z| > 1.5 out of 28 pairs)

| Subject | V1 | V2 | V3 | hV4 |
|---------|----|----|----|----|
| sub-08 | 12 | 13 | 9 | 13 |
| sub-09 | 8 | 4 | 6 | 5 |
| sub-10 | 5 | 8 | 2 | 3 |

### 3.3 sub-08 (Deutan) -- Strongest case

**Pattern**: Systematic L-M axis deficit + S-cone compensation across ALL ROIs.

| ROI | Key deficits (z < -1.5) | Key elevations (z > +1.5) |
|-----|------------------------|--------------------------|
| V1 | red-orange(adj) z=-2.15, green-cyan(adj) z=-2.15, red-purple z=-2.96 | orange-yellow(adj) z=+5.08, yellow-purple z=+3.56, red-yellow z=+2.36 |
| V2 | red-orange(adj) z=-1.89, orange-purple z=-2.63, red-purple z=-2.56 | cyan-purple z=+5.25, yellow-purple z=+4.40, red-yellow z=+4.09, orange-yellow(adj) z=+2.81 |
| V3 | red-orange(adj) z=-2.05, red-magenta(adj) z=-1.95, purple-magenta(adj) z=-1.86 | orange-yellow(adj) z=+4.05, red-yellow z=+3.17, yellow-purple z=+2.78 |
| hV4 | cyan-blue(adj) z=-2.35, orange-purple z=-1.73, red-orange(adj) z=-1.69 | red-cyan z=+2.65, green-magenta z=+2.40, red-yellow z=+2.18, blue-purple(adj) z=+2.07 |

**Interpretation**: Consistent deutan signature. Red-orange boundary is the primary confusion point. Yellow becomes hyper-separated from neighboring colors (orange-yellow z=+5 in V1), likely reflecting enhanced S-cone reliance.

### 3.4 sub-09 (Protan) -- Distinct from deutan pattern

| ROI | Key deficits (z < -1.5) | Key elevations (z > +1.5) |
|-----|------------------------|--------------------------|
| V1 | red-orange(adj) z=-2.33, orange-green z=-2.57, red-green z=-1.84 | orange-yellow(adj) z=+3.88, cyan-magenta z=+3.21, orange-magenta z=+3.09 |
| V2 | (none at z<-1.5) | cyan-blue(adj) z=+2.82, cyan-magenta z=+2.36 |
| V3 | red-orange(adj) z=-1.91 | orange-yellow(adj) z=+2.03, cyan-magenta z=+1.99 |
| hV4 | red-orange(adj) z=-2.10, green-magenta z=-3.40 | red-magenta(adj) z=+2.31, cyan-blue(adj) z=+2.19 |

**Interpretation**: Protan-specific: orange-green deficit (z=-2.57, V1) is distinctive from deutan. Shared red-orange deficit but with different compensatory pattern (cyan-magenta instead of yellow-purple).

### 3.5 sub-10 (Deutan) -- Mild with cortical compensation

| ROI | Key deficits (z < -1.5) | Key elevations (z > +1.5) |
|-----|------------------------|--------------------------|
| V1 | blue-magenta z=-3.12, yellow-purple z=-2.02, red-purple z=-1.93 | yellow-magenta z=+2.15, red-magenta(adj) z=+1.63 |
| V2 | red-purple z=-1.50 | blue-purple(adj) z=+2.80, cyan-purple z=+2.32, red-blue z=+2.24, cyan-blue(adj) z=+2.21 |
| V3 | yellow-purple z=-2.34 | yellow-magenta z=+1.86 (only 2 extreme pairs total) |
| hV4 | cyan-blue(adj) z=-2.02 | blue-purple(adj) z=+1.61 (only 3 extreme pairs total) |

**Interpretation**: Shares deutan signature with sub-08 in V1/V2 but much weaker. V3/hV4 show near-normal profiles, suggesting effective cortical compensation. V2 cool-color (blue/cyan/purple) over-separation is the most distinctive feature. **Filter target limited to V1/V2 cool-axis correction.**

### 3.6 Cross-Subject Consistent Patterns

**V1 -- All 3 CVD agree:**

| Pair | Step | Direction | sub-08 | sub-09 | sub-10 | Mechanism |
|------|------|-----------|--------|--------|--------|-----------|
| red-orange | 1 (adj) | DEFICIT | -2.15 | -2.33 | -1.33 | L-M confusion |
| orange-yellow | 1 (adj) | ELEVATION | +5.08 | +3.88 | +0.75 | S-cone compensation |
| red-magenta | 1 (adj) | ELEVATION | +1.87 | +2.28 | +1.63 | S-cone compensation |

**V2 -- All 3 CVD agree:**

| Pair | Step | Direction | sub-08 | sub-09 | sub-10 | Mechanism |
|------|------|-----------|--------|--------|--------|-----------|
| cyan-blue | 1 (adj) | ELEVATION | +2.24 | +2.82 | +2.21 | S-cone compensation |
| blue-purple | 1 (adj) | ELEVATION | +2.45 | +1.07 | +2.80 | S-cone compensation |

**Deutan-specific (sub-08 + sub-10):**

| Pair | ROI | Direction | sub-08 | sub-10 |
|------|-----|-----------|--------|--------|
| red-purple | V1, V2 | DEFICIT | -2.96, -2.56 | -1.93, -1.50 |
| green-cyan | V2 | ELEVATION | +1.48 | +1.85 |
| red-green | V2 | DEFICIT | -1.23 | -1.23 |
| cyan-blue | hV4 | DEFICIT | -2.35 | -2.02 |

---

## 4. Revised Filter Design

### 4.1 Rejected Approaches

| Approach | Why rejected | Evidence |
|----------|-------------|---------|
| "Match global RDM to HC" | RDM already similar | HC-CVD r=0.499 vs HC-HC r=0.517 |
| "Increase overall local separability" | No global deficit | CVD adjacent distances >= HC in V1/V2 |
| "Reduce total disparity to HC" | Disparity is color-agnostic | Permutation p=0.953 |
| "Full voxel-space transformation" | Overparameterized | r=0.999 on training data = overfitting |

### 4.2 Proposed Approach: Anisotropy Correction Filter

**Core idea**: Correct the pair-specific distance distortion while preserving the already-functional global structure.

**Target**: Per-pair distance profile matching, NOT global RDM matching.

```
L_total = L_anisotropy + lambda * L_structure + mu * L_smoothness

L_anisotropy = SUM_pairs w(i,j) * |d_CVD(T(i), T(j)) - d_HC(i, j)|^2
L_structure  = 1 - spearman(RDM_CVD_filtered, RDM_CVD_original)
L_smoothness = SUM |T(theta) - T(theta + delta)|^2   (filter continuity)
```

Where:
- `T(theta)`: stimulus color transformation function (input: original hue -> output: display hue)
- `w(i,j)`: pair weight based on cross-subject consistency and z-score magnitude
- `d_CVD(T(i), T(j))`: predicted neural distance when CVD sees transformed colors
- `d_HC(i, j)`: observed HC neural distance for original colors

### 4.3 Pair-Specific Weights

Based on Check 5 results, weights proportional to cross-subject consistency:

| Priority | Pairs | Direction | Weight | Rationale |
|----------|-------|-----------|--------|-----------|
| HIGH | red-orange (adj) | Restore (increase) | 3.0 | 3/3 CVD deficit, z: -1.3 to -2.3 |
| HIGH | orange-yellow (adj) | Normalize (decrease) | 3.0 | 3/3 CVD elevation, z: +0.8 to +5.1 |
| HIGH | cyan-blue (adj) | Normalize (decrease) | 3.0 | 3/3 CVD elevation, z: +2.2 to +2.8 |
| MEDIUM | red-magenta (adj) | Normalize (decrease) | 2.0 | 3/3 CVD elevation, z: +1.6 to +2.3 |
| MEDIUM | blue-purple (adj) | Normalize (decrease) | 2.0 | 2/3 CVD elevation (deutan) |
| MEDIUM | red-green | Restore (increase) | 2.0 | 2/3 CVD deficit (deutan) |
| LOW | Remaining 22 pairs | Preserve | 1.0 | Already similar to HC |

### 4.4 Personalization Strategy

| Subject | Filter strength | Primary targets | Special considerations |
|---------|----------------|-----------------|----------------------|
| sub-08 | Strong | All 6 priority pairs, all ROIs | Most data-rich case; prototype here first |
| sub-09 | Moderate | red-orange, orange-green (protan-specific) | Different compensatory axis (cyan-magenta) |
| sub-10 | Weak | V2 cool-axis only (blue-purple, cyan-blue) | V3/hV4 compensation means minimal intervention needed |

### 4.5 Two-Phase Pipeline

**Phase A: Neural surrogate optimization (repeatable, no subject needed)**

1. Use forward encoding model (from Future Phase 2) to predict voxel responses for arbitrary hue
2. Optimize T(theta) to minimize L_total
3. Constraint: T must be smooth, monotonic, and close to identity (regularization)
4. Validation: LORO cross-validation on held-out runs

**Phase B: Behavioral calibration (1 session per subject)**

Purpose: Validate that neural surrogate predicts perceptual improvement.

Minimal measurement protocol:
- **Primary**: Discrimination thresholds for top-deficit pairs (red-orange, orange-green)
- **Control**: Discrimination thresholds for top-elevation pairs (cyan-blue) -- should not worsen
- **Global**: Farnsworth-Munsell 100 Hue test (pre/post filter comparison)

This design respects the constraint that repeated behavioral testing is difficult while providing the minimum data needed to validate the neural-perceptual link.

---

## 5. Relationship to Existing Phases

| Phase | Status | Relationship to filter |
|-------|--------|----------------------|
| Phase 1 (Preprocessing) | DONE | Provides within-subject Procrustes-aligned amplitudes |
| Phase 2 (SRM between-subject) | DONE | Provides "scattered but parallel" characterization |
| **Check 5 (Local separability)** | **DONE** | **Identifies anisotropy correction as filter target** |
| Future Phase 1 (Hyperalignment) | Planned | HC common space for filter target definition |
| Future Phase 2 (Forward model) | Planned | **PREREQUISITE** -- enables prediction for arbitrary hue |
| **Future Phase 3 (Filter)** | **This plan** | Anisotropy correction filter |

### Critical dependency

The filter requires Future Phase 2 (continuous hue encoder) to predict neural responses for transformed colors. Without this, optimization is limited to the 8 measured hues.

---

## 6. Visualizations

- `analysis/cvd_pairwise_zscore_heatmap.png` -- Per-CVD per-ROI z-score heatmap (temporary, .gitignored)
- `analysis/validation/scripts/results/check5_local_separability/` -- Full Check 5 analysis outputs:
  - `local_separability_by_step.png` -- Distance by hue step (HC vs CVD)
  - `per_pair_difference_heatmap.png` -- Per-pair CVD-HC difference
  - `color_wheel_separability.png` -- Adjacent pair separability on color wheel
  - `check5_results.json` -- Complete numerical results

---

## 7. TODO: Remaining Validations & Development

### 7.1 Immediate (before filter implementation)

- [ ] **Pair-level permutation test** (~2h)
  - Test whether specific pair z-scores (e.g., red-orange z=-2.3) exceed what random label assignment produces
  - Method: For each pair, permute HC/CVD labels 10,000 times, compute null z-distribution
  - Required to defend per-pair claims against reviewer criticism
  - Priority: HIGH

- [ ] **Split-half stability of pair profiles** (~2h)
  - Split 6 runs into halves (runs 1-3 vs 4-6)
  - Compute per-pair z-scores from each half independently
  - Correlation between halves = reliability of individual pair deviations
  - If pair profiles are unstable across halves, filter targets are unreliable
  - Priority: HIGH

- [ ] **Bootstrap 95% CIs for per-pair z-scores** (~1h)
  - Resample HC subjects with replacement (1000 iterations)
  - Recompute z-scores for each CVD subject
  - Report 95% CI for each extreme pair
  - Priority: MEDIUM

### 7.2 Phase 2 SRM pending validations (server)

- [ ] **LOSO stability** -- verify no single HC subject drives results
- [ ] **Split-half SRM reliability** -- test SRM temporal stability
- [ ] **SRM k-value selection** -- justify k=4
- [ ] **Alignment comparison** -- SRM vs Procrustes vs Raw

### 7.3 Pre-filter development (Future Phase 1-2)

- [ ] **Hyperalignment / HC common space** -- define filter target space
- [ ] **Continuous hue encoder** -- predict responses for arbitrary hue angles
- [ ] **Encoder validation** -- LOCO CV, reconstruction error < 60deg

### 7.4 Filter implementation (Future Phase 3)

- [ ] **Prototype on sub-08** (strongest case) with pair-weighted loss
- [ ] **LORO cross-validation** -- report held-out, NOT training performance
- [ ] **Low-rank constraint** -- rank-4 transformation (match SRM dimensionality)
- [ ] **Baseline comparison** -- identity, mean-shift, random orthogonal
- [ ] **Extend to sub-09, sub-10** with personalized weights
- [ ] **Ablation study** -- effect of each loss component

### 7.5 Behavioral validation (future experiment)

- [ ] **Collect FM-100 Hue** for all 10 subjects
- [ ] **Pairwise discrimination thresholds** for priority pairs
- [ ] **Neural-behavioral correlation** -- validate surrogate
- [ ] **Post-filter behavioral test** (if filter shows in-silico improvement)

---

## 8. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Per-pair patterns unstable across run halves | Medium | High | Split-half test (TODO 7.1) |
| Forward encoder too inaccurate for optimization | Medium | High | Conservative interpolation, fall back to 8-color discrete filter |
| Behavioral data shows no neural-perceptual link | Medium | Fatal | Reframe as pure characterization paper |
| sub-10 has no meaningful filter target | High | Low | Report as "compensation case study" |
| Reviewers reject n=3 despite case-study framing | Medium | Medium | Emphasize cross-subject consistency + cone biology alignment |

---

## 9. Publication Strategy

### If filter works (in-silico + behavioral):
**Title direction**: "Personalized neural color filters for CVD: from anisotropic cortical representations to targeted hue correction"

### If filter doesn't work but characterization holds:
**Title direction**: "Preserved but distorted: anisotropic color space redistribution in CVD cortex"

The "scattered but parallel" + "anisotropic redistribution" characterization is publishable independently of the filter. The filter adds translational impact but is not required for the core scientific contribution.
