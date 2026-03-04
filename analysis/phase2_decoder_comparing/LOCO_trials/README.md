# LOCO Decoder Improvement Experiments

## Problem
LOCO Forward Encoding MAE ~70deg (chance=90deg, color spacing=45deg) is too high for Phase 3 filter optimization. Root cause: **degrees of freedom** (7 training colors - 6 channels = df=1). 6 channels have biological basis (3 cone-opponent axes x 2 polarities), so we keep channels and work around df.

## Decision Tree

```
Phase 1 MDS -> Circular structure confirmed?
  +- YES -> Phase 2 Ridge -> Improvement?
  |          +- YES -> Ridge+GP combined (Phase 3)
  |          +- NO  -> Phase 3 GP (periodic kernel)
  |                    +- GP improved? -> GP adopted, extend 3-2/3-3
  |                    +- No improvement -> Keep Group Prior (lambda=0)
  +- NO  -> 3D+ MDS check
           +- Higher-dim structure -> Matern/RBF kernel GP (non-circular)
           +- No structure -> Data quality limit, keep Group Prior
```

## Phases

### Phase 1: MDS Diagnostic (local)
- Script: `scripts/mds_diagnostic.py`
- Output: `results/mds_diagnostic/`
- Purpose: Diagnose whether 8 colors form circular structure; which alignment preserves it

### Phase 2: Ridge Regularization (server)
- Script: `scripts/loco_ridge.py`, `scripts/loco_ridge.sbatch`
- Output: `results/ridge/`
- Purpose: Stabilize W estimation via Ridge (keep 6 channels, shrink effective df)

### Phase 3: Gaussian Process LOCO (server/local)
- Script: `scripts/loco_gp.py`, `scripts/loco_gp.sbatch`
- Output: `results/gp/`
- Purpose: Replace/augment FE channel model with GP for principled interpolation

## Decision Criteria

| Metric | Threshold | Pass | Fail |
|--------|-----------|------|------|
| 2D Stress | < 0.10 | 2D sufficient | Check 3D+ |
| Circular order | rank r > 0.8 | Circular preserved | Periodic kernel may not fit |
| Mantel r | > 0.5, p < 0.05 | Circular structure significant | Consider non-circular kernel |
| Shepard R2 | > 0.80 | MDS interpretation reliable | MDS interpretation cautious |
| Ridge MAE < OLS MAE | > 5deg | Adopt Ridge | Move to GP |
| GP_periodic < FE_OLS | > 10deg | Periodic prior powerful | Data quality bottleneck |
