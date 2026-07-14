# phase4_topology — CLAUDE.md

**Stage**: A-side geometry characterization (complements Phase-1 population dimensionality).
**Status**: First pass complete (descriptive, null-leaning).

## Objective

Ask the **stimulus-configuration** question that the Phase-1 dimensionality scripts
do NOT: does the **8-hue ring** itself warp (E1, invertible) or collapse (E2,
non-invertible) in CVD? This is the geometry directly tied to LOCO interpolation
failure and to the inverse-filter invertibility premise.

## Distinction from Phase-1 (do not conflate)

| | `future_phase1/scripts/dimensionality/` | **this folder** |
|---|---|---|
| object | voxel population (n_vox cov, 48 samples) | 8-hue configuration (8x8 Gram) |
| metric | power-law alpha, MEME k* | PR, effective rank, isotropy, circular corr, Betti-1 |
| question | how many population modes | what SHAPE the 8 hues make |

## Reuse policy (enforced)

- Data loading / subject groups / ROI map / `save_config` are **imported** from
  `future_phase1_forward_model/scripts/utils_forward_model.py`. Do NOT re-implement.
- Crawford & Howell single-case = project-canonical formula (n=3 CVD standard).
- matplotlib only (no seaborn). Flat output `results/<name>/` + one `config.json`.

## Key empirical caveat (load-bearing)

The a-priori "HC = clean 2-D ring (PR~2, |cc|~1)" model is **empirically false** here:
HC hue configs are ~3-5 dimensional (PR), only partially planar (0.57-0.92), and
top-2-PC ring ordering is unstable even within HC (|cc| 0.09-0.84). Therefore:
- Absolute thresholds on these metrics are invalid — verdicts are **HC-relative**
  (Crawford-Howell), never absolute.
- Any configuration claim is **descriptive only** (8 conditions, n=3 CVD).

## Result (first pass)

No robust CVD dimensionality collapse or ring-topology break survives the
single-case standard → **converges with Phase-1 population null**; weakly supports
warp(E1)/invertibility by null. See `README.md` for numbers.
