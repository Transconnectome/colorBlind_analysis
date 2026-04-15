#!/usr/bin/env python3
"""
utils_cone_3way.py — 3-way independent cone shifts + full spectral integration.

Extends stockman_cone_shift.py with:
  - 3-way independent cone shifts (delta_L, delta_M, delta_S)
  - Full spectral integration: integral SPD(lambda) * cone(lambda - delta) dlambda
  - Matrix method wrapper for consistency

All functions return (hue_normal_8, hue_shifted_8, delta_theta_8) for consistent interface.

Runs locally (conda env: srm).
Prereq: pip install colour-science
"""

import numpy as np
import sys
from pathlib import Path

# Add forward model scripts to path for imports
_PHASE2_DIR = Path(__file__).resolve().parent.parent
for _base in [_PHASE2_DIR.parent, _PHASE2_DIR.parent.parent]:
    _fwd = _base / 'future_phase1_forward_model' / 'scripts'
    if _fwd.exists() and str(_fwd) not in sys.path:
        sys.path.insert(0, str(_fwd))
        break

from stockman_cone_shift import (
    load_stockman_fundamentals,
    shift_cone_sensitivity,
    lab_to_xyz,
    lms_to_opponent,
    opponent_to_hue_angle,
    _compute_spectral_shift_lms,
    compute_xyz_to_lms_matrix,
    compute_shifted_hue_angles,
    COLOR_LAB,
    D65_XYZ,
    HUE_ANGLES_DEG,
    COLOR_NAMES,
)

# Cache cone fundamentals (loaded once)
_CONE_CACHE = {}


def _get_cone_fundamentals():
    """Load and cache Stockman cone fundamentals."""
    if 'data' not in _CONE_CACHE:
        wl, L, M, S = load_stockman_fundamentals()
        M_xyz2lms = compute_xyz_to_lms_matrix(wl, L, M, S)
        _CONE_CACHE['data'] = (wl, L, M, S, M_xyz2lms)
    return _CONE_CACHE['data']


def _compute_normal_hue():
    """Compute unshifted hue angles (cached)."""
    if 'hue_normal' not in _CONE_CACHE:
        wl, L, M, S, M_xyz2lms = _get_cone_fundamentals()
        xyz = lab_to_xyz(COLOR_LAB)
        lms = _compute_spectral_shift_lms(wl, L, M, S, M_xyz2lms, xyz)
        rg, by = lms_to_opponent(lms)
        _CONE_CACHE['hue_normal'] = opponent_to_hue_angle(rg, by)
    return _CONE_CACHE['hue_normal']


def compute_shifted_hue_3way(delta_L, delta_M, delta_S):
    """3-way independent cone shift.

    Args:
        delta_L: L-cone shift in nm (positive = longer wavelengths)
        delta_M: M-cone shift in nm
        delta_S: S-cone shift in nm

    Returns:
        hue_normal: (8,) normal hue angles in degrees
        hue_shifted: (8,) shifted hue angles
        delta_theta: (8,) hue differences (shifted - normal), wrapped [-180, 180]
    """
    wl, L, M, S, M_xyz2lms = _get_cone_fundamentals()
    hue_normal = _compute_normal_hue()

    # Apply independent shifts
    L_s = shift_cone_sensitivity(wl, L, delta_L) if delta_L != 0 else L
    M_s = shift_cone_sensitivity(wl, M, delta_M) if delta_M != 0 else M
    S_s = shift_cone_sensitivity(wl, S, delta_S) if delta_S != 0 else S

    xyz = lab_to_xyz(COLOR_LAB)
    lms_shifted = _compute_spectral_shift_lms(wl, L_s, M_s, S_s, M_xyz2lms, xyz)
    rg, by = lms_to_opponent(lms_shifted)
    hue_shifted = opponent_to_hue_angle(rg, by)

    delta_theta = hue_shifted - hue_normal
    delta_theta = (delta_theta + 180) % 360 - 180
    return hue_normal, hue_shifted, delta_theta


def compute_shifted_hue_full_spectral(delta_lambda, cvd_type='deutan',
                                       monitor_spd=None):
    """Full spectral integration with SPD weighting.

    Computes: LMS_i = integral SPD(lambda) * cone_i(lambda - delta) * r_j(lambda) dlambda
    where r_j is the spectral reflectance/emission for color j.

    Falls back to flat SPD if monitor_spd is None.

    Args:
        delta_lambda: shift magnitude in nm
        cvd_type: 'deutan' or 'protan'
        monitor_spd: (N,) spectral power distribution or None for flat

    Returns:
        hue_normal: (8,) normal hue angles
        hue_shifted: (8,) shifted hue angles
        delta_theta: (8,) differences
    """
    wl, L, M, S, M_xyz2lms = _get_cone_fundamentals()
    hue_normal = _compute_normal_hue()

    # Apply SPD weighting to cone fundamentals
    if monitor_spd is not None:
        # Interpolate SPD to cone wavelength grid
        spd = np.interp(wl, np.linspace(wl[0], wl[-1], len(monitor_spd)),
                        monitor_spd)
        L_w = L * spd
        M_w = M * spd
        S_w = S * spd
    else:
        L_w, M_w, S_w = L.copy(), M.copy(), S.copy()

    # Apply cone shift
    if cvd_type == 'deutan':
        M_shifted = shift_cone_sensitivity(wl, M_w, delta_lambda)
        lms_shifted = _compute_spectral_shift_lms(
            wl, L_w, M_shifted, S_w, M_xyz2lms, lab_to_xyz(COLOR_LAB))
    elif cvd_type == 'protan':
        L_shifted = shift_cone_sensitivity(wl, L_w, -delta_lambda)
        lms_shifted = _compute_spectral_shift_lms(
            wl, L_shifted, M_w, S_w, M_xyz2lms, lab_to_xyz(COLOR_LAB))
    else:
        lms_shifted = _compute_spectral_shift_lms(
            wl, L_w, M_w, S_w, M_xyz2lms, lab_to_xyz(COLOR_LAB))

    rg, by = lms_to_opponent(lms_shifted)
    hue_shifted = opponent_to_hue_angle(rg, by)

    delta_theta = hue_shifted - hue_normal
    delta_theta = (delta_theta + 180) % 360 - 180
    return hue_normal, hue_shifted, delta_theta


def compute_shifted_hue_matrix(delta_lambda, cvd_type='deutan'):
    """Matrix method wrapper (existing _compute_spectral_shift_lms).

    Uses the standard XYZ->LMS least-squares recomputation.

    Args:
        delta_lambda: shift magnitude in nm
        cvd_type: 'deutan' or 'protan'

    Returns:
        hue_normal: (8,) normal hue angles
        hue_shifted: (8,) shifted hue angles
        delta_theta: (8,) differences
    """
    wl, L, M, S, _ = _get_cone_fundamentals()
    return compute_shifted_hue_angles(wl, L, M, S, delta_lambda, cvd_type)


def compute_1way_hue_shift(delta_lambda, cvd_type='deutan'):
    """1-way cone shift (convenience wrapper).

    Sign convention:
      - deutan: M-cone shifted +delta_lambda (toward L, longer wavelengths)
      - protan: L-cone shifted -delta_lambda (toward M, shorter wavelengths)
    delta_lambda is always positive magnitude; direction from cvd_type.

    Args:
        delta_lambda: shift magnitude in nm (>= 0)
        cvd_type: 'deutan' or 'protan'

    Returns:
        hue_normal: (8,)
        hue_shifted: (8,)
        delta_theta: (8,)
    """
    return compute_shifted_hue_matrix(abs(delta_lambda), cvd_type)
