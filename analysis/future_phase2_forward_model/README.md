# Future Phase 2: Continuous Hue Interpolation Model

**Supporting Research Question (SRQ3)**: Can channel-based encoding predict brain responses for any hue in 360° space?
**채널 기반 인코딩이 360° 공간의 임의 색조에 대한 뇌 반응을 예측할 수 있는가?**

**Status**: Planned 📋 (Will be developed in `prediction_model_workspace/`)
**Timeline**: 1-2 weeks
**Scripts**: To be implemented in workspace

---

## ⚠️ IMPORTANT: Future Development

**이 phase는 Future Phase 1 완료 후 시작됩니다.**

**작업 위치**: `../../prediction_model_workspace/`
**상세 계획**: `../../prediction_model_workspace/docs/PHASE2_PREDICTION_MODEL.md`

---

## Overview

![Phase 2 Pipeline](../../prediction_model_workspace/docs/phase2.png)

This phase develops a **continuous hue encoder** that predicts brain responses for any color in 360° circular space, interpolating between the 8 measured colors (45° spacing).

## Goal

Learn the mapping: **Stimulus hue (0-360°) → Brain voxel responses**

Using 6 half-wave rectified basis channels to enable interpolation.

## Success Criteria

**Direct Validation (LOCO CV)**:
- ✅ **Required**: Reconstruction error < 60° (chance: 90°, baseline: 32°)
- ⭐ **Excellent**: Error < 45°

**Indirect Validation (Quality Metrics)**:
- RDM smoothness (gradual change across hues)
- Inter-encoder consistency across HC subjects

## Method

**Channel Response Functions**:
```python
# 6 half-wave rectified basis channels
def channel_response(stimulus_hue, channel_center, bandwidth=60):
    return max(0, exp(-((stimulus_hue - channel_center)**2) / (2 * bandwidth**2)))
```

**Encoder Training** (in HC common space from Phase 1):
```python
Y_predicted = C(θ) @ W_enc
```
where C(θ) is the channel activation vector for hue angle θ

**Leave-One-Color-Out (LOCO) Validation**:
- Train on 7 colors, predict held-out 8th color
- Assess interpolation quality

## Why This Phase Matters

**Phase 3 Dependency**: Filter optimization requires predicting responses for **arbitrary display colors** (not just 8 measured colors).

Without this encoder:
- ❌ Limited to 8 discrete colors only

With this encoder:
- ✅ Optimize across full 360° hue space

## Documentation

**⚠️ 작업 중 문서** (Workspace): `../../prediction_model_workspace/docs/PHASE2_PREDICTION_MODEL.md`

**Key sections**:
1. Channel response function design
2. HC common space training
3. 2-tier validation (direct LOCO + indirect quality)
4. Common vs individual encoder comparison

---

## When This Phase is Complete

**최종 스크립트 위치**: 이 디렉토리에 복사됨
**디렉토리명 변경**: `future_phase2_forward_model` → `phase2_forward_model`

---

## Next Phase

**Future Phase 3**: CVD Filter Optimization via 360° search
- Development workspace: `../../prediction_model_workspace/`
- Plan: `../../prediction_model_workspace/docs/PHASE3_CVD_FILTER_OPTIMIZATION.md`
