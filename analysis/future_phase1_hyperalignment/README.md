# Future Phase 1: Hyperalignment for HC Common Space

**Supporting Research Question (SRQ2)**: Can trial-aligned GPA create a stable HC common space for robust encoder learning?
**시행별 정렬 GPA가 견고한 인코더 학습을 위한 안정적인 HC 공통 공간을 생성할 수 있는가?**

**Status**: Planned 📋 (Methodology comparison in COMPARISON.md; implementation pending stimulus-wise GLM)
**Timeline**: 2-3 weeks
**Scripts**: Currently in development workspace

---

## ⚠️ IMPORTANT: Active Development Notice

**이 phase는 현재 개발 중입니다!**

### 작업 위치

**현재 작업 공간**: `../../prediction_model_workspace/`
- 실험 스크립트: `prediction_model_workspace/scripts/`
- 진행 상황: `prediction_model_workspace/docs/PROGRESS_LOG.md`
- 중간 결과: `prediction_model_workspace/results/`

**완성 후 이동**:
- `prediction_model_workspace/final/phase1/` → 이 디렉토리로 복사
- 디렉토리명 변경: `future_phase1_hyperalignment` → `phase1_hyperalignment`

### 관련 문서

**상세 계획**: `../../prediction_model_workspace/docs/PHASE1_HYPERALIGNMENT.md`
**전체 계획**: `../../prediction_model_workspace/MASTER_PLAN.md`

**이 README는 최종 요약 버전입니다.** 진행 중인 작업은 workspace를 참조하세요.

**⚠️ 방법론 비교**: `COMPARISON.md` 문서에서 Hyperalignment vs SRM 비교 참조
**⚠️ TODO 추적**: 전체 TODO 체크리스트는 `../../prediction_model_workspace/MASTER_PLAN.md` Phase 1 참조

---

## Overview

![Phase 1 Pipeline](../../prediction_model_workspace/docs/phase1.png)

This phase will align HC participants' brain responses into a **common representational space** using trial-aligned Generalized Procrustes Analysis (GPA). This addresses the current limitation: HC individuals have similar color structures (high Procrustes stability: 0.91/0.88) but use different coordinate systems (low RDM correlation: 0.26/0.24).

## Success Criteria

**Tier-1: Trial-level Metrics**
- Inter-subject correlation (ISC) > 0.30
- LOSO decoding > 25% (chance: 12.5%)

**Tier-2: Color-level Metrics**
- Procrustes disparity < 0.08 (baseline: 0.089)
- Run-split stability > 0.80 (baseline: 0.91)
- RDM between-subject correlation > 0.30 (baseline: 0.26)

**Downstream Performance**
- Common W reconstruction error ≤ baseline (32° for V1)

---

## Documentation

**⚠️ 작업 중 문서** (Workspace): `../../prediction_model_workspace/docs/PHASE1_HYPERALIGNMENT.md`

**Key sections**:
1. Trial-wise pattern extraction (LS-S GLM)
2. Hyperalignment using GPA
3. 2-tier validation strategy
4. Common encoder relearning

---

## When This Phase is Complete

**최종 스크립트 위치**: 이 디렉토리에 복사됨
**디렉토리명 변경**: `future_phase1_hyperalignment` → `phase1_hyperalignment`
**README 업데이트**: 최종 결과 및 검증된 코드 정보 추가

---

## Next Phase

**Future Phase 2**: Continuous Hue Interpolation Model (using common encoder from this phase)
- Development workspace: `../../prediction_model_workspace/`
- Plan: `../../prediction_model_workspace/docs/PHASE2_PREDICTION_MODEL.md`
