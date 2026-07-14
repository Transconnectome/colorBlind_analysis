# Phase 4 — 8-hue ring (stimulus-configuration) geometry

**Question**: Is the CVD distortion of the hue ring a **warp** (E1: stays 2-D loop,
anisotropic ellipse, *invertible* → inverse filter is coherent) or a **collapse**
(E2: ring → 1-D line, loop opens, *non-invertible* → filter premise breaks)?

This complements `future_phase1_forward_model/scripts/dimensionality/`, which
measured **population** dimensionality (voxel covariance). That cannot see the
ring; this folder measures the **configuration** geometry of the 8 hues directly.

## Method

Per subject × ROI, from `amplitudes_procrustes.npy` (6,8,V):
run-average → center across the 8 hues → 8×8 Gram → eigen-geometry. Metrics:

- **participation_ratio**, **effective_rank** — soft configuration dimensionality
- **planarity** = (λ1+λ2)/Σλ — is the config 2-D?
- **in_plane_isotropy** = λ2/λ1 — ellipse axis ratio (collapse → 0)
- **circular_corr** — stimulus hue angle vs neural angle in PC1-2 plane
  (ring ordering / loop preservation; rotation/reflection-invariant)
- **Betti-1** (optional, needs `ripser`) — number of 1-D loops

Stats: group Welch (matches Phase-1 eigenspectrum convention) + per-CVD
Crawford & Howell single-case (n=3 standard). Verdicts are **HC-relative**.

Run:
```bash
python scripts/ring_geometry.py \
  --baseline_dir <C010> \
  --output_dir results/ring_geometry
```

## Result (first pass) — null-leaning, descriptive

**The a-priori "clean 2-D ring" model is empirically false.** HC hue configurations
are ~3-5 dimensional (PR), only partially planar (0.57-0.92), and ring ordering is
unstable *even in HC* (hV4 |cc| ranges 0.09 [sub-07] to 0.84 [sub-02]). So the
top-2-PC ring is not a stable instrument; metrics are interpreted HC-relative.

| ROI | PR HC→CVD (Welch p) | isotropy (p) | \|circ corr\| HC→CVD (p) |
|---|---|---|---|
| V1 | 4.23 → 3.37 (0.38) | 0.47→0.37 (0.54) | 0.20→0.37 (0.30) |
| V2 | 4.36 → 2.78 (**0.056**) | 0.50→0.33 (0.26) | 0.28→0.13 (0.17) |
| V3 | 4.24 → 3.31 (0.52) | 0.53→0.35 (0.40) | 0.41→0.21 (0.17) |
| hV4 | 2.97 → 2.84 (0.93) | 0.34→0.32 (0.94) | 0.41→0.10 (**0.036**) |

**Single-case (Crawford-Howell), the n=3 standard — what actually survives:**
- PR: no CVD significant (best sub-08 V2 p=0.062).
- ring ordering: the only sub-threshold cell is sub-09 V1 |cc|=0.62 (p=0.018) —
  but that is *higher* than HC (= better ordering), i.e. **not** a collapse signal,
  and likely multiple-comparison noise.
- hV4 group |cc| p=0.036 does **not** survive single-case (all CVD p>0.28) and
  rests on highly variable HC → **not assertable** by project anti-overstatement rules.
- Verdicts: 11/12 CVD×ROI = "no significant deviation"; 1/12 = sub-08 V2 partial.

### Interpretation

No detectable configuration-level **collapse** (E2) in CVD that survives the
single-case standard. This **converges with the Phase-1 population null** (α/k*
n.s.): with n=3 and 8 conditions, the LOCO interpolation failure is **not**
explained by a measurable ring-dimensionality collapse. By elimination this weakly
favors **warp (E1) / invertibility** — consistent with the inverse-filter premise —
but the support is by *null*, not positive evidence. Descriptive only.

### For the paper

Use as a **framing / negative-control** result, not a headline: "the hue-ring
configuration shows no measurable dimensionality collapse in CVD (converging with
population eigenspectrum); the distortion is consistent with an invertible warp."
The nominal hV4 ring-ordering drop aligns with hV4 as the interpolation locus but
is single-case-non-significant and must be reported as such.

## Outputs
- `results/ring_geometry/ring_geometry_results.json` — per-subject + group + single-case + verdicts
- `results/ring_geometry/fig_ring_metrics.pdf` — PR / eff-rank / isotropy / circ-corr by ROI
- `results/ring_geometry/fig_rings.pdf` — 8-hue ring in PC1-2 (HC example vs 3 CVD)
