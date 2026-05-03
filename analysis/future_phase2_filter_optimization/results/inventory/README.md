# inventory/ — Cross-cutting summary tables

**Status**: ACTIVE (CORE)
**Last update**: 2026-05-04

## Contents

- `loss_inventory.md` — 12+ loss variants × HC sanity check (rank-based emp_p + bootstrap CI). Generator: `scripts/build_loss_inventory.py`
- `loss_inventory.csv` — flat data (row-per-(loss, subject))
- `consolidated_phase2_results.{csv,json}` — Cycle 10d 48-row aggregate (subject × ROI × family with z metrics + bootstrap CI)
- `consolidated_cross_roi.csv` — Cycle 11 9-pair × 2-family cross-ROI specificity

These are the primary "current state" summaries — read first to understand current candidate landscape.

## Current winner (per `loss_inventory.md`)

`cycle15_opt2_v4mwj_v1lrank` = `2·mw_jaccard(V4) + 1·l_rank(V1) + 0.2·Tikh`
- sub-08 emp_p=0.00 (perfect — 0/6 HC above)
- sub-09 emp_p=0.17 (1/6 HC above)
- → ✓✓ both CVD distinct from HC distribution
