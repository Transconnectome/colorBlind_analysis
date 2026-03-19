#!/usr/bin/env python3
"""
utils_distortion_models.py — Unified interface for 5 hue distortion models.

Models:
  cone_1way  (df=1): Single cone shift magnitude |delta_lambda| in nm
  cone_3way  (df=3): Independent L, M, S shifts in nm
  fourier    (df=4): a1,b1,a2,b2 Fourier k=1,2 (degrees)
  per_color  (df=8): delta_1..delta_8 per-color free shifts (degrees)
  fourier_8  (df=8): a1..a4,b1..b4 Fourier k=1..4 (degrees)

All models produce shifted hue angles (8,) from which C(theta+delta) design matrices
are built.
"""

import numpy as np
import sys
from pathlib import Path

# Add forward model scripts to path
_FWD_DIR = str(Path(__file__).resolve().parent.parent.parent.parent
               / 'future_phase1_forward_model' / 'scripts')
if _FWD_DIR not in sys.path:
    sys.path.insert(0, _FWD_DIR)

# Add filter scripts to path
_FILTER_DIR = str(Path(__file__).resolve().parent.parent.parent
                  / 'scripts')  # -> future_phase2_filter_optimization/scripts/
if _FILTER_DIR not in sys.path:
    sys.path.insert(0, _FILTER_DIR)

from utils_forward_model import create_basis_full, HUE_ANGLES, N_CHANNELS
from utils_filter import T_psi, T_psi_free
from utils_cone_3way import (
    compute_1way_hue_shift,
    compute_shifted_hue_3way,
)

# ============================================================================
# Constants
# ============================================================================

HUE_ANGLES_FLOAT = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)

# Sign convention:
#   deutan: M-cone shifted +delta_lambda (toward L, longer wavelengths)
#   protan: L-cone shifted -delta_lambda (toward M, shorter wavelengths)
# cone_1way bounds are [0, 60] because magnitude is always positive;
# direction is handled by cvd_type inside the shift functions.
# Upper bound 60nm (not 40) because sub-09 protan hit the 40nm ceiling.

MODELS = {
    'cone_1way': {
        'df': 1,
        'bounds': [(0, 60)],
        'x0': [10.0],
        'description': 'Single cone shift magnitude (nm)',
    },
    'cone_3way': {
        'df': 3,
        'bounds': [(-60, 60), (-60, 60), (-60, 60)],
        'x0': [0.0, 10.0, 0.0],  # default: M-cone shift for deutan
        'description': 'Independent L, M, S cone shifts (nm)',
    },
    'fourier': {
        'df': 4,
        'bounds': [(-30, 30)] * 4,
        'x0': [0.0, 0.0, 0.0, 0.0],
        'description': 'Fourier k=1,2 angular distortion (degrees)',
    },
    'per_color': {
        'df': 8,
        'bounds': [(-45, 45)] * 8,
        'x0': [0.0] * 8,
        'description': 'Per-color free shift (degrees)',
    },
    'fourier_8': {
        'df': 8,
        'bounds': [(-30, 30)] * 8,
        'x0': [0.0] * 8,
        'description': 'Fourier k=1..4 angular distortion (degrees)',
    },
}


# ============================================================================
# Core Functions
# ============================================================================

def apply_distortion(model_name, params, hue_angles=None, cvd_type='deutan'):
    """Apply distortion model to hue angles.

    Args:
        model_name: one of MODELS keys
        params: parameter array matching model df
        hue_angles: (8,) base hue angles in degrees (default: standard 8 colors)
        cvd_type: 'deutan' or 'protan' (for cone models)

    Returns:
        shifted_angles: (8,) shifted hue angles in degrees [0, 360)
    """
    if hue_angles is None:
        hue_angles = HUE_ANGLES_FLOAT.copy()
    params = np.asarray(params, dtype=float)

    if model_name == 'cone_1way':
        delta_lambda = params[0]
        _, hue_shifted, _ = compute_1way_hue_shift(delta_lambda, cvd_type)
        return hue_shifted % 360

    elif model_name == 'cone_3way':
        delta_L, delta_M, delta_S = params
        _, hue_shifted, _ = compute_shifted_hue_3way(delta_L, delta_M, delta_S)
        return hue_shifted % 360

    elif model_name == 'fourier':
        return T_psi(hue_angles, params)

    elif model_name == 'per_color':
        return T_psi_free(hue_angles, params)

    elif model_name == 'fourier_8':
        # Extended Fourier: k=1..4 harmonics
        theta_rad = np.deg2rad(hue_angles)
        shift = np.zeros_like(hue_angles)
        for k in range(4):
            shift += params[2 * k] * np.cos((k + 1) * theta_rad)
            shift += params[2 * k + 1] * np.sin((k + 1) * theta_rad)
        return (hue_angles + shift) % 360

    else:
        raise ValueError(f'Unknown model: {model_name}')


def get_design_matrix(model_name, params, n_channels=N_CHANNELS, basis_type='fe',
                      cvd_type='deutan'):
    """Get C(theta + delta_theta) design matrix for shifted angles.

    Args:
        model_name: distortion model name
        params: model parameters
        n_channels: number of basis channels (default: 6)
        basis_type: 'fe' or 'lf'
        cvd_type: CVD type for cone models

    Returns:
        C_shifted: (8, K) design matrix at shifted hue angles
    """
    shifted_angles = apply_distortion(model_name, params, cvd_type=cvd_type)
    basis_full = create_basis_full(n_channels, basis_type=basis_type)
    idx = np.round(shifted_angles).astype(int) % 360
    return basis_full[idx]


def get_delta_theta(model_name, params, cvd_type='deutan'):
    """Get per-color hue shift delta_theta (degrees).

    Args:
        model_name: distortion model name
        params: model parameters
        cvd_type: CVD type

    Returns:
        delta_theta: (8,) hue shifts in degrees, wrapped to [-180, 180]
    """
    shifted = apply_distortion(model_name, params, cvd_type=cvd_type)
    delta = shifted - HUE_ANGLES_FLOAT
    return (delta + 180) % 360 - 180


def get_initial_params(model_name, cvd_type='deutan'):
    """Get sensible initial parameters for optimization.

    Args:
        model_name: model name
        cvd_type: CVD type (affects cone_3way init)

    Returns:
        x0: initial parameter array
    """
    x0 = np.array(MODELS[model_name]['x0'], dtype=float)
    if model_name == 'cone_3way':
        if cvd_type == 'deutan':
            x0 = np.array([0.0, 10.0, 0.0])  # M-cone shift
        elif cvd_type == 'protan':
            x0 = np.array([-10.0, 0.0, 0.0])  # L-cone shift
        else:
            x0 = np.array([0.0, 0.0, 0.0])
    return x0


def compute_aicc(rss, df, n_obs=28):
    """Compute corrected AIC for model comparison.

    Args:
        rss: residual sum of squares
        df: number of free parameters
        n_obs: number of observations (28 for RDM upper triangle)

    Returns:
        aicc: corrected AIC value (lower = better)
    """
    if rss <= 0 or n_obs - df - 1 <= 0:
        return np.nan
    aic = n_obs * np.log(rss / n_obs) + 2 * df
    correction = 2 * df * (df + 1) / (n_obs - df - 1)
    return aic + correction
