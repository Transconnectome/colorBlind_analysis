# older_cycles/ — Pre-Cycle 9 workflow artifacts

**Status**: ACTIVE (referenced by current cycle scripts)
**Last update**: 2026-05-04 (regrouped)

## Why kept

These directories are referenced by current `scripts/cycle_filter_refinement/` scripts (cycle5_*, cycle7_*, run_NxM, run_bootstrap). Cannot delete without breaking those scripts.

## Subdirs

- `cycle_loss_redesign/` — Cycle 4 alt metrics (Apr 29). Referenced by cycle5_c8drop, cycle5_cross_sim, cycle7_blend_wspearman, run_NxM, run_bootstrap.
- `cycle_bootstrap/` — Older bootstrap workflow (Apr 29). Referenced by 3 scripts.

## Action

Once new bootstrap (in `cycles/bootstrap/`) is verified to cover all use cases, these can be archived. Not recommended without testing.
