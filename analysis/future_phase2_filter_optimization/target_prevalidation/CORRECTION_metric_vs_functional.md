# CORRECTION: Metric vs Functional Dissociation (2026-03-23)

## Critical Error Identified

User correctly identified a fundamental misinterpretation in the integration tables where I labeled **Metric-Functional dissociations** as "convergence".

### Example (orange-yellow pair):

**Incorrect interpretation (before)**:
- Cone Δdist: -0.027 (compression)
- SRM z: +3.29 (overseparation)
- RDM diff: +0.498 (overseparation)
- LOCO: orange (p=0.029*), yellow (p=0.044*) — both vulnerable
- JND: HYPO (harder to discriminate)
- **Label**: "Cortical 4/4 ✓✓" (WRONG — this is NOT convergence!)

**Correct interpretation (after)**:
- **Metric indicators** (SRM +3.29, RDM +0.498): Overseparation (farther apart geometrically)
- **Functional indicators** (LOCO failure, JND HYPO): Discrimination difficulty
- **Relationship**: **DISSOCIATION ✗** (metric overseparation + functional difficulty = contradictory)

## Why This is a Dissociation, Not Convergence

### The Fundamental Distinction

| Property | What it measures | Indicators | Order | Question |
|----------|-----------------|-----------|-------|----------|
| **Metric** | Geometric distance | SRM z, RDM diff | **0th order** (pairwise endpoints) | "How far apart are the two colors?" |
| **Functional** | Interpolation/discrimination | LOCO, JND | **Higher order** (manifold regularity) | "Can we interpolate/discriminate these colors?" |

### The Expected Relationship

**Intuitive prediction**:
- Metric overseparation (farther apart) → Should be EASIER to discriminate (HYPER)
- Metric compression (closer together) → Should be HARDER to discriminate (HYPO)

### The Dissociation (3 pairs)

**What we actually observe**:
1. **orange-yellow**: Metric +3.29/+0.498 (overseparation) BUT Functional HYPO (harder) → **DISSOCIATION**
2. **yellow-green**: Metric +4.14/+0.496 (overseparation) BUT Functional HYPO (harder) → **DISSOCIATION**
3. **yellow-purple**: Metric +13.87/+0.670 (overseparation) BUT Functional HYPO (harder) → **DISSOCIATION**

Colors are geometrically FARTHER APART (metric) but HARDER TO DISCRIMINATE (functional) — this contradicts the expected relationship!

## Explanation from Behavioral Document

From `analysis/future_phase3_behavioral_analysis/notion.md` §3-1:

> **전역 vs 국소 해리**: SRM z-score(전역 끝점 거리)와 JND 방향(국소 지각 민감도)이 HC1 기준 6쌍 중 4쌍 불일치(DISCORDANT)

The document explicitly identifies this as a **dissociation** (해리), not convergence, and explains:

### 0th Order vs Higher Order Geometry (§3-1, lines 196-212)

| | SRM z-score | LOCO/JND |
|---|---|---|
| **Measures** | Pairwise endpoint distance (0th order) | Interpolation capability (higher order) |
| **Space** | SRM latent (k=3-4) | Original voxel space (hundreds of dims) |
| **Question** | "How far?" | "Can we interpolate from neighbors?" |

**Key insight** (line 211):
> SRM z와 LOCO가 **같은 색**(orange, yellow, purple)에서 이상을 감지하지만, SRM z의 **방향**(과분리→HYPER 예측)은 JND와 불일치하고, LOCO의 **방향**(보간 실패→HYPO 예측)은 JND와 일치한다.

- SRM z-score: Detects distortion **location** correctly ✓
- SRM z-score: Predicts distortion **behavioral consequence** incorrectly ✗ (overseparation ≠ easier discrimination)
- LOCO: Predicts distortion **behavioral consequence** correctly ✓ (interpolation failure = harder discrimination)

## Why the Dissociation Occurs

### Mechanism (from §3-1, lines 207-210)

**LOCO measures local manifold regularity**:
- HC: All 8 colors smoothly interpolable from neighbors → smooth manifold
- CVD (sub-08): orange, yellow, purple positions distorted → local irregularities
- Interpolation failure ≠ endpoint distance increase

**SRM z-score measures only 0th order**:
- Endpoints farther apart (overseparation) → measured
- Intermediate manifold structure → NOT captured
- Cannot predict interpolation difficulty

### Biological Mechanism: S-cone Compensation (§2-4)

1. **L-M loss detection** → S-cone gain amplification (β = 2.5-3.0×)
2. **Endpoint expansion** (SRM/RDM positive): S-cone amplification pushes endpoints farther apart
3. **Interpolation fidelity degradation** (LOCO/JND HYPO): Amplification creates local irregularities, making neighbor-based interpolation fail

**Analogy**:
```
Normal manifold:     ●---●---●---●  (smooth, regular spacing)
CVD distorted:       ●-●-------●●   (endpoints farther, but irregular local structure)
                      ↑ overseparation (metric)
                        ↑ interpolation failure (functional)
```

## Corrected Framework

### What Converges (CORRECT)

1. **Metric-Metric convergence**: SRM ↔ RDM (86% agreement)
   - Both measure 0th order pairwise distance
   - High consistency across different spaces (latent vs voxel)

2. **Functional-Functional convergence**: LOCO ↔ JND (100% agreement)
   - Both measure higher order interpolation/discrimination capability
   - Perfect consistency (all HYPO pairs contain LOCO-vulnerable colors)

### What Dissociates (CORRECT)

3. **Metric-Functional dissociation**: SRM/RDM overseparation + JND HYPO (3 pairs)
   - 0th order (endpoint distance) ≠ higher order (interpolation capability)
   - Cannot compare across different orders of geometry
   - Overseparation does NOT predict easier discrimination

## Changes Made

### 1. Updated §2-2 Integration Table
- Added columns: "Metric 방향" and "Functional 방향"
- Changed "수렴 패턴" column to "관계" (relationship)
- Labeled orange-yellow, yellow-green, yellow-purple as "**해리 ✗**" (dissociation)
- Added §2-2-1 explaining Metric vs Functional framework

### 2. Updated §4-2 Multi-Level Framework
- Separated into 5 levels instead of 4
- **Level 3**: Metric-Metric consistency (SRM ↔ RDM: 86%)
- **Level 4**: Functional-Functional consistency (LOCO ↔ JND: 100%)
- **Level 5**: Metric-Functional dissociation (3 pairs)
- Updated "통합 모델" diagram to show separation

### 3. Created Analysis Scripts
- `analyze_metric_vs_functional.py`: Demonstrates the dissociation with tables
- Shows: Metric oversep + Functional HYPO = 3 pairs
- Shows: LOCO → JND 67%, SRM → JND 17% (SRM cannot predict JND)

## Key Lessons

### What I Got Wrong
❌ "All indicators point in the same direction" → convergence
❌ Comparing SRM z-score (metric) with JND (functional) directly
❌ Labeling overseparation + HYPO as "4/4 cortical convergence"

### What is Correct
✅ **Only compare same-order properties**:
  - Metric ↔ Metric (SRM ↔ RDM)
  - Functional ↔ Functional (LOCO ↔ JND)
✅ **Metric-Functional = different attributes**:
  - Metric: "How far apart?" (0th order geometry)
  - Functional: "Can we interpolate?" (higher order regularity)
✅ **Dissociation is biologically meaningful**:
  - Endpoint expansion (S-cone gain) ≠ interpolation fidelity
  - 0th order property ≠ higher order property

## References

- **Behavioral document**: `analysis/future_phase3_behavioral_analysis/notion.md` §3-1 (lines 169-212)
- **Integration table**: `cone_opponency_table_proposal.md` §2-2
- **Analysis script**: `analyze_metric_vs_functional.py`
- **User feedback**: 2026-03-23 — "SRM z, RDM이 +고 cone dist and JND가 음수 및 hypo인데, orange-yellow에서, 이게 왜 수렴이죠?"

## Bottom Line

**Orange-yellow, yellow-green, yellow-purple** show:
- ✅ **Metric-Metric convergence**: SRM and RDM both positive (overseparation)
- ✅ **Functional-Functional convergence**: LOCO and JND both show deficits (HYPO)
- ✗ **Metric-Functional DISSOCIATION**: Overseparation ≠ easier discrimination
  - This is NOT convergence
  - This is a **dissociation** between 0th order and higher order geometry
  - SRM z-score cannot predict behavioral consequences (JND)
  - LOCO can predict behavioral consequences (JND) — 100% accuracy
