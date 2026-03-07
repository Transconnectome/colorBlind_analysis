# Future Phase 1: HC Common Space 구축 (Hyperalignment)
> Trial-aligned GPA로 HC 피험자들의 뇌 반응을 공통 표상 공간으로 정렬하여 인코더 학습의 기반 마련

## 상태
- 📋 **Planned** — 방법론 비교 완료 (`COMPARISON.md`), stimulus-wise GLM 후 구현 예정
- 작업 공간: `prediction_model_workspace/`

## 목표
- HC 피험자들의 뇌 반응을 **공통 표상 공간 (common representational space)**으로 정렬
- 현재 한계: HC 간 Procrustes stability (직교 변환 안정성) 높음 (0.91/0.88) → 좌표계가 다름 (RDM correlation 0.26/0.24)
- Generalized Procrustes Analysis (GPA, 일반화 직교 변환)를 통한 trial 단위 정렬

## 성공 기준

**Tier-1: Trial-level Metrics**

| 지표 | 목표 |
|------|------|
| Inter-subject correlation (ISC) | > 0.30 |
| LOSO decoding accuracy | > 25% (chance: 12.5%) |

**Tier-2: Color-level Metrics**

| 지표 | 목표 | 현재 baseline |
|------|------|---------------|
| Procrustes disparity | < 0.08 | 0.089 |
| Run-split stability | > 0.80 | 0.91 |
| RDM between-subject correlation | > 0.30 | 0.26 |
| Common W reconstruction error | ≤ 32° (V1 baseline) | — |

## 방법
1. **Trial-wise pattern extraction**: LS-S GLM으로 개별 trial 반응 추출
2. **Hyperalignment**: GPA로 HC 공통 공간 구축
3. **2-tier 검증**: Trial-level + Color-level metrics
4. **Common encoder 재학습**: 공통 공간에서 인코더 학습

---

## 완료 후 조치
- `prediction_model_workspace/final/phase1/` → 이 디렉토리로 이동
- 디렉토리명 변경: `future_phase1_hyperalignment` → `phase1_hyperalignment`

## 다음 단계
→ **Future Phase 2**: 공통 인코더 기반 Continuous Hue Interpolation Model

### 🔽 작업 위치 및 관련 문서
- 실험 스크립트: `prediction_model_workspace/scripts/`
- 진행 상황: `prediction_model_workspace/docs/PROGRESS_LOG.md`
- 상세 계획: `prediction_model_workspace/docs/PHASE1_HYPERALIGNMENT.md`
- 방법론 비교: `COMPARISON.md` (Hyperalignment vs SRM)
- 전체 계획: `prediction_model_workspace/MASTER_PLAN.md`
