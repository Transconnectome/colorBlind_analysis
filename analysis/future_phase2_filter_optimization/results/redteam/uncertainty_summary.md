# Production argmin: effective uncertainty (v6 PCA RDM, redteam verification)

_Generated: 2026-05-31T17:58:10.543245+00:00_

## Bottom line

The B2 synthesis (GT=(0,0) with donor's real JND — internally consistent at the zero point, no synth design contamination) places the v6 2-component composite's argmin **~20° away from origin in β_s and ~25° away in β_c, with f10°=0.00** across all 3 candidates (n=140 each). This is the load-bearing evidence that the v6 composite cannot localize zero from zero data.

The v2 recovery (corrected synth_jnd) restores partial identifiability on the **extreme axis** of each candidate (β_c bias 30.9→4.7° for S08-robust; β_s bias 17→7.6° for S08-stable), but the modest axis remains noise-dominated. S09-primary (small GT (2,24)) sits below noise floor — synth fix even hurts slightly because the JND signal becomes another noise source rather than a constraint.

Source C (label permutation, N=1000): production loss is **not** in the lower-tail of label-shuffled distribution for any candidate (p=0.17–0.87). The production fit is no better than what random label shuffling achieves.

## Per-candidate summary

| Candidate | Production argmin | B2 uncertainty (|bs|_med / |bc|_med at GT=0) | v2 mean f10° | Source C p_perm | B1 rank |
|---|---|---|---|---|---|
| **S08-stable** | (+38, -10) | 20° / 26° (IQR 22 / 16) | 0.10 | 0.866 (n=1000) | 0.500 |
| **S08-robust** | (+6, -42) | 22° / 26° (IQR 40 / 10) | 0.26 | 0.167 (n=1000) | 0.875 |
| **S09-primary** | (+2, +24) | 16° / 24° (IQR 18 / 9) | 0.14 | 0.471 (n=1000) | 0.875 |

## Interpretation

**What can be claimed**:
- Production v6 argmin is a reproducible composite-minimum from the joint γ+RDM atom landscape
- It is a low-dimensional descriptive embedding of CVD pattern features in a 2-coordinate space
- For candidates with extreme parameter values on one axis (S08-robust β_c=-42; S08-stable β_s=38), that axis is partially identifiable above noise floor

**What cannot be claimed**:
- (β_s, β_c) as physiologically interpretable cone-shift / cortical-rotation magnitudes (any axis < ~20° is in noise floor)
- Specificity vs HC null distribution (B1 rank 0.5–0.875)
- Statistical significance vs label-shuffled null (p_perm 0.17–0.87, all > 0.05)

**Effective claim form per candidate**:

- **S08-stable**: v6 argmin places (+38°, -10°). Effective uncertainty from B2: β_s ±20°, β_c ±26°. Axes where |argmin| > 2 × B2 uncertainty (potential signal): NONE
- **S08-robust**: v6 argmin places (+6°, -42°). Effective uncertainty from B2: β_s ±22°, β_c ±26°. Axes where |argmin| > 2 × B2 uncertainty (potential signal): NONE
- **S09-primary**: v6 argmin places (+2°, +24°). Effective uncertainty from B2: β_s ±16°, β_c ±24°. Axes where |argmin| > 2 × B2 uncertainty (potential signal): NONE

## What the v1→v2 fix proved

v1 used donor HC's REAL JND as the fake CVD JND, which is approximately at GT=0 behaviourally even when synth voxels were at GT≠0. This created a γ-atom pull toward δ=0 that compounded with the voxel-driven RDM atom signal toward δ=GT. v2 synthesizes JND consistent with GT via pool baseline × (d_phys/d_perc(GT)) + N(0, pool_sd). The v2 vs v1 differences show:

- **S08-robust β_c bias 30.9° → 4.7°** — pipeline can recover β_c near GT=-42° when synth is consistent
- **S08-stable β_s bias 17.0° → 7.6°** — pipeline can recover β_s near GT=38° when synth is consistent
- **S09-primary slightly worse in v2** — confirms small GT values (|GT|<20°) sit below noise floor; consistent JND adds noise without constraint

The fix demonstrates that **identifiability is axis-asymmetric and SNR-thresholded**, not uniformly impossible. Production candidates straddle the threshold — extreme axes are identifiable, moderate axes are not.

## Methodological notes

- B2 effective uncertainty draws on n=140 realizations (7 donors × M=20 noise) per candidate at GT=(0,0).
- v2 recovery uses n=140 realizations at GT=(prod_bs, prod_bc) with consistent synth_jnd.
- Source C uses N=1000 label permutations with HC pool unchanged.
- B1 uses real HC_k amplitudes as fake CVD (7 carriers; deterministic per candidate).
- Verdict table separately at `verdict_matrix_v6_pca_v2.json` / `verdict_matrix_v2.md`.
