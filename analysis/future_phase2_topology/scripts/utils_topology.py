#!/usr/bin/env python3
"""
utils_topology.py — Stimulus-configuration (8-hue ring) geometry primitives.

Phase 4 asks a DIFFERENT question from the Phase-1 dimensionality scripts:

    Phase-1 (phase4_forward_model/scripts/dimensionality/):
        POPULATION dimensionality — eigenspectrum of the n_voxels x n_voxels
        covariance over 48 (run x color) samples. "How many voxel-population
        modes carry signal." Color identity is collapsed into samples.

    Phase-4 (this folder):
        CONFIGURATION dimensionality — geometry of the 8-hue constellation
        itself (8 x 8 across-condition Gram). "What SHAPE do the 8 hues make?"
        Ideal isoluminant hue circle = a 2-D ring. Directly tied to the
        confusion-axis collapse and LOCO interpolation failure.

Goal: place each CVD subject in the warp (E1) vs collapse (E2) dichotomy.
    warp     -> ring stays 2-D loop, anisotropic (ellipse); INVERTIBLE -> filter OK
    collapse -> ring -> 1-D line; loop opens; NON-INVERTIBLE -> filter premise breaks

REUSE: data loading / subject groups / ROI mapping are imported from the
Phase-1 forward-model utils (single source of truth). This module adds only
the configuration-geometry math. No throwaway re-implementation of loaders.
"""

import sys
from pathlib import Path
import numpy as np
from scipy import stats

# --- Reuse the canonical loader + constants (do NOT re-implement) -----------
_FWD = Path(__file__).resolve().parents[2] / 'phase4_forward_model' / 'scripts'
sys.path.insert(0, str(_FWD))
from utils_forward_model import (        # noqa: E402
    load_amplitudes, save_config, get_subject_group,
    HC_SUBJECTS, CVD_SUBJECTS, ALL_SUBJECTS, ROIS, HUE_ANGLES,
)

# Optional persistent homology (Betti-1). Degrades gracefully if absent.
try:
    from ripser import ripser as _ripser
    HAS_RIPSER = True
except Exception:
    HAS_RIPSER = False


# ============================================================================
# Configuration geometry (the 8-hue ring)
# ============================================================================

def configuration_pcs(amp, eps=1e-12):
    """Eigen-geometry of the 8-hue configuration in voxel space.

    Args:
        amp: (n_runs, n_colors, n_voxels) Procrustes-aligned amplitudes.

    Returns:
        eigs:  (<=8,) positive eigenvalues (variance per PC), descending.
        coords:(n_colors, n_pc) PC coordinates of the 8 hue points
               (top eigenvectors scaled by sqrt(lambda)).
    """
    M0 = amp.mean(axis=0)                      # (8, V) run-average
    M = M0 - M0.mean(axis=0, keepdims=True)    # center ACROSS the 8 hues
    G = M @ M.T                                # (8, 8) across-condition Gram
    w, U = np.linalg.eigh(G)                   # ascending
    order = np.argsort(w)[::-1]
    w, U = w[order], U[:, order]
    w = np.clip(w, 0.0, None)
    coords = U * np.sqrt(w + eps)              # (8, 8) point coordinates
    pos = w[w > eps * max(w.max(), 1.0)]       # drop numerical-zero modes
    return pos, coords


def participation_ratio(eigs):
    """PR = (sum lambda)^2 / sum(lambda^2). Soft dimensionality."""
    eigs = np.asarray(eigs, float)
    s1 = eigs.sum()
    s2 = (eigs ** 2).sum()
    return float(s1 * s1 / s2) if s2 > 0 else np.nan


def effective_rank(eigs):
    """exp(Shannon entropy of normalized eigenvalues) (Roy & Vetterli 2007)."""
    eigs = np.asarray(eigs, float)
    s = eigs.sum()
    if s <= 0:
        return np.nan
    p = eigs / s
    p = p[p > 0]
    return float(np.exp(-(p * np.log(p)).sum()))


def planarity(eigs):
    """Fraction of configuration variance in the best 2-plane = (l1+l2)/sum.

    Ring should be ~planar (-> ~1). Low value = the 8 hues are not 2-D.
    """
    eigs = np.asarray(eigs, float)
    s = eigs.sum()
    if s <= 0 or eigs.size < 2:
        return np.nan
    return float(eigs[:2].sum() / s)


def in_plane_isotropy(eigs):
    """l2 / l1 within the top-2 plane. Circle -> ~1, line (collapse) -> ~0.

    This is the ellipse axis ratio: the primary warp-vs-collapse indicator.
    """
    eigs = np.asarray(eigs, float)
    if eigs.size < 2 or eigs[0] <= 0:
        return np.nan
    return float(eigs[1] / eigs[0])


def _circ_mean(a):
    return np.arctan2(np.sin(a).mean(), np.cos(a).mean())


def circular_corr(stim_deg, coords2d):
    """Jammalamadaka-SenGupta circular correlation between stimulus hue angle
    and the neural angle in the top-2 PC plane.

    |r| ~ 1  => the 8 hues sit on the plane in their correct cyclic order
                (ring topology + ordering preserved; rotation/reflection-invariant).
    |r| ~ 0  => ordering destroyed (loop broken / collapsed).
    """
    alpha = np.deg2rad(np.asarray(stim_deg, float))
    beta = np.arctan2(coords2d[:, 1], coords2d[:, 0])
    da = np.sin(alpha - _circ_mean(alpha))
    db = np.sin(beta - _circ_mean(beta))
    denom = np.sqrt((da ** 2).sum() * (db ** 2).sum())
    return float((da * db).sum() / denom) if denom > 0 else np.nan


def betti1(coords2d):
    """Number of 1-D loops (Betti-1) of the 8-point ring via persistent
    homology, counting bars whose lifetime exceeds half the max. Returns
    None if ripser is not installed (primary topology metric is circular_corr).
    """
    if not HAS_RIPSER:
        return None
    pts = coords2d - coords2d.mean(0)
    scale = np.linalg.norm(pts, axis=1).max()
    if scale <= 0:
        return 0
    dgm1 = _ripser(pts / scale, maxdim=1)['dgms'][1]
    if len(dgm1) == 0:
        return 0
    life = dgm1[:, 1] - dgm1[:, 0]
    return int((life > 0.5 * life.max()).sum())


def subject_ring_metrics(amp, hue_deg=HUE_ANGLES):
    """All configuration metrics for one subject x ROI."""
    eigs, coords = configuration_pcs(amp)
    c2 = coords[:, :2]
    return {
        'n_voxels': int(amp.shape[2]),
        'participation_ratio': participation_ratio(eigs),
        'effective_rank': effective_rank(eigs),
        'planarity': planarity(eigs),
        'in_plane_isotropy': in_plane_isotropy(eigs),
        'circular_corr': circular_corr(hue_deg, c2),
        'abs_circular_corr': abs(circular_corr(hue_deg, c2)),
        'betti1': betti1(c2),
        'coords2d': c2.tolist(),
        'eigs': eigs.tolist(),
    }


# ============================================================================
# Statistics (reuse the project-canonical Crawford & Howell single-case test)
# ============================================================================

def crawford_howell(x_i, control_group):
    """Crawford & Howell (1998) single-case test (repo-canonical formula)."""
    control_group = np.asarray(control_group, float)
    n = len(control_group)
    m = control_group.mean()
    s = control_group.std(ddof=1)
    if s == 0:
        return 0.0, 1.0
    t = (x_i - m) / (s * np.sqrt((n + 1) / n))
    p = 2 * stats.t.sf(abs(t), n - 1)
    return float(t), float(p)


def welch(hc_vals, cvd_vals):
    """Welch t-test, matching the Phase-1 eigenspectrum script convention."""
    hc_vals = np.asarray(hc_vals, float)
    cvd_vals = np.asarray(cvd_vals, float)
    t, p = stats.ttest_ind(hc_vals, cvd_vals, equal_var=False)
    return float(t), float(p)
