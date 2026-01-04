# Future Phase 3: CVD Filter Optimization via 360° Search

**Supporting Research Question (SRQ4)**: Can optimization find display colors that make CVD responses match HC?
**최적화가 색맹 반응을 정상인과 일치시키는 디스플레이 색상을 찾을 수 있는가?**

**Status**: Planned 🎯 (Will be developed in `prediction_model_workspace/`)
**Timeline**: 2 weeks
**Scripts**: To be implemented in workspace

---

## ⚠️ IMPORTANT: Future Development

**이 phase는 Future Phase 1-2 완료 후 시작됩니다.**

**작업 위치**: `../../prediction_model_workspace/`
**상세 계획**: `../../prediction_model_workspace/docs/PHASE3_CVD_FILTER_OPTIMIZATION.md`

---

## Overview

![Phase 3 Pipeline](../../prediction_model_workspace/docs/phase3.png)

This phase finds **optimal display colors** for each original color such that CVD brain responses match HC responses, using optimization across continuous 360° hue space.

## Core Innovation

For each original color θ_orig, solve:

```python
θ_display = argmin_θ [
    Loss1: ||Ŷ_cvd(θ) - Ŷ_hc(θ_orig)||²  # Brain pattern matching
    + λ * Loss2: ||Decode(Ŷ_cvd(θ)) - θ_orig||²  # Reconstruction accuracy
]
```

**Result**: Color lookup table (θ_orig → θ_display)

## Why This Approach?

**Advantages over voxel-space filters**:
1. ✅ **360° optimization**: Works for any hue (Phase 2 encoder enables this)
2. ✅ **Personalized**: Uses individual CVD's actual response patterns
3. ✅ **Dual constraints**: Matches both neural geometry AND perceptual accuracy
4. ✅ **Theoretically grounded**: Aligns CVD brain → HC brain

## Success Criteria

- **Filter smoothness**: < 2.0°/deg (gradual color mapping)
- **Reconstruction error**: ≤ baseline 32° (maintains perceptual accuracy)
- **Inter-CVD consistency**: < 10° (similar filters for same CVD type)

## Implementation

**Step 1**: Collect CVD data (existing: sub-08, 09, 10)
**Step 2**: Project CVD into HC common space (Phase 1)
**Step 3**: Run optimization for θ_orig ∈ [0°, 360°]
**Step 4**: Generate lookup table (LUT)
**Step 5**: Validate filter (in silico + behavioral + fMRI)

## Validation Strategy

**In silico (computational)**:
- Apply filter to training data
- Check brain pattern alignment

**Psychophysical (behavioral)**:
- Farnsworth-Munsell 100 Hue test
- Color discrimination with filtered stimuli

**fMRI (neural)**:
- Scan CVD with filtered images
- Verify HC-like responses

## Scope Limitation

⚠️ **Current scope**: In-silico validation only

**Empirical validation** (filtered stimuli + behavioral testing) deferred to future work

## Documentation

**⚠️ 작업 중 문서** (Workspace): `../../prediction_model_workspace/docs/PHASE3_CVD_FILTER_OPTIMIZATION.md`

**Key sections**:
1. CVD data collection & projection
2. Optimization framework (dual-constraint loss)
3. Lookup table generation
4. Ablation study (4 scenarios)
5. Validation metrics

---

## When This Phase is Complete

**최종 스크립트 위치**: 이 디렉토리에 복사됨
**디렉토리명 변경**: `future_phase3_filter_optimization` → `phase3_filter_optimization`

---

## Expected Outcome

**Deliverable**: Personalized color LUTs for each CVD subject

**Applications**:
- Real-time image/video filters
- Display calibration
- AR glasses with personalized correction

---

## Relationship to Current Phase 3

| Aspect | Current Phase 3 (Procrustes Filter) | Future Phase 3 (360° Optimization) |
|--------|-------------------------------------|-----------------------------------|
| **Space** | Voxel space (brain) | Color space (stimulus) |
| **Method** | Direct linear transformation | Optimization-based search |
| **Coverage** | 8 measured colors | 360° continuous hue |
| **Validation** | Retrospective | Prospective (planned) |
| **Location** | `../phase3_procrustes_filter/` | This directory (when complete) |

**Current Phase 3** = Proof-of-concept for filter feasibility
**Future Phase 3** = Full stimulus-space filter pipeline
