# LOCO Decoder Improvement Experiments

## Problem
LOCO Forward Encoding MAE ~70deg (chance=90deg, color spacing=45deg) is too high for Phase 3 filter optimization. Root cause: **degrees of freedom** (7 training colors - 6 channels = df=1). 6 channels have biological basis (3 cone-opponent axes x 2 polarities), so we keep channels and work around df.

## Decision Tree (Revised 2026-03-04)

```
Phase 1 MDS → Circular structure?
  +- hV4/SRM only (2/4) → Partial
  +- V1/V2 → Phase 1b Extended Diagnostic
               +- V2: STRUCTURED (2/4) — 3D nonlinear manifold
               +- V1: UNSTRUCTURED (0/4) — negative control
               +- V3: MARGINAL (1/4), hV4: MARGINAL (1/4)

Phase 2 Ridge (SRM LOCO) → df stabilization baseline
  +- Improvement? → Record delta, proceed regardless

Phase 3 GP Matern (V2 SRM only) → benchmark comparison
  +- V2 improved? → Record as SRM-space ceiling
  +- No improvement → Confirms SRM space limitation

Phase 4 Procrustes Filter (★ MAIN PATH) ← notion.md 전략
  +- Operating space: Procrustes (NOT SRM)
  +- FE W matrix: W_CVD → W_HC transform
  +- Evaluation: LOCO MAE in Procrustes + SRM validation
  +- Connects to: future_phase3_filter_optimization/
```

**Key strategic pivot (2026-03-04)**: Pre-validation (notion.md)에서 SRM 공간이 연속 색 구조에 부적합함이 확인됨 (V1 stress plateau, hV4 CIELab 부호 반전). Ridge/GP는 baseline/benchmark으로 유지하되, **주력은 Procrustes 공간 필터로 전환**.

## Phases

### Phase 1: MDS Diagnostic (local) ✅ DONE
- Script: `scripts/mds_diagnostic.py`
- Output: `results/mds_diagnostic/`
- Purpose: Diagnose whether 8 colors form circular structure; which alignment preserves it
- **Result**: hV4/SRM만 2/4 통과. Equidistant circular structure 전반적 기각.

### Phase 1b: Extended V1/V2 Diagnostic (local) ✅ DONE
- Script: `scripts/mds_extended_v1v2.py`
- Output: `results/mds_diagnostic/extended_v1v2_summary.json`, `fig_ext1~6`
- Purpose: V1/V2 실패가 참조 모델 문제인지 진정한 구조 부재인지 심층 진단
- **Result**: V2=STRUCTURED (3D nonlinear manifold, L-M dominant), V1=UNSTRUCTURED (negative control)

### Phase 2: Ridge Regularization (server)
- Script: `scripts/loco_ridge.py`, `scripts/loco_ridge.sbatch`
- Output: `results/ridge/`
- Purpose: Stabilize W estimation via Ridge (keep 6 channels, shrink effective df)
- **Scope**: SRM LOCO baseline improvement — df 문제 완화 확인용

### Phase 3: GP Matern — V2 Benchmark Only (server/local)
- Script: `scripts/loco_gp.py`, `scripts/loco_gp.sbatch`
- Output: `results/gp/`
- Purpose: V2 SRM 공간에서 Anisotropic Matern GP의 LOCO 개선 상한 확인
- **Scope**: V2 only (유일한 STRUCTURED ROI). Periodic kernel 기각됨 → Matern + L-M ARD
- **Note**: SRM 공간 ceiling 확인이 목적. 주력 방법이 아닌 비교용 benchmark

### Phase 4: Procrustes Filter Design → future_phase3_filter_optimization/
- Purpose: **주력 필터 설계** — SRM + Procrustes 상보적 활용
- **SRM 역할 (필수 인프라)**: HC mean 타겟 정의 + 그룹 비교 (voxel 수 차이 해결)
- **Procrustes 역할 (개인 해상도)**: voxel 수준 필터 적용 (n_voxels × 8 params)
- **브릿지**: SRM projection W_i — 타겟 역투영 (SRM→voxel) 및 결과 검증 (voxel→SRM)
- **Filter target**: sub-08 (FDR 32 pairs), sub-09 (FDR 7 pairs)
- See: `analysis/future_phase3_filter_optimization/pre_validation/notion.md`

## Decision Criteria

### Phase 1/1b (MDS Diagnostic)

| Metric | Threshold | Result |
|--------|-----------|--------|
| 2D Stress | < 0.10 | hV4/SRM=0.084 PASS |
| Circular order | \|r\| > 0.8 | V1/Raw=0.786 FAIL (near) |
| Mantel r | > 0.5, p < 0.05 | All FAIL |
| Shepard R2 | > 0.80 | V3/SRM=0.876, hV4/SRM=0.935 PASS |
| CIELab > Equidistant (1b) | r improvement + p<0.05 | All FAIL (trend in V2 L-M) |
| H1 Topology (1b) | p < 0.05 | All FAIL |
| Higher-D stress (1b) | < 0.10 | V2=0.097 PASS |
| Isomap > MDS (1b) | \|rho\| improvement | V2 PASS |

### Phase 2/3 (Ridge & GP)

| Metric | Threshold | Purpose |
|--------|-----------|---------|
| Ridge MAE < OLS MAE | > 5deg | df stabilization effect |
| GP Matern (V2) < Ridge (V2) | > 5deg | Kernel-based interpolation gain |

### Phase 4 (Procrustes Filter) — see future_phase3 README

| Metric | Threshold | Purpose |
|--------|-----------|---------|
| LOCO MAE improvement | > 10deg | Filter efficacy |
| Filter smoothness | < 2.0°/deg | Physiological plausibility |
| Cross-ROI consistency | r > 0.5 | Generalizability |
