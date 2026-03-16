#!/usr/bin/env python3
"""
utils_filter.py — Shared utilities for RDM-matching filter optimization (Steps 3-5).

Contains:
- T_ψ transforms (Fourier, per-color free shift, cone-shift Model 0)
- Loss functions (pattern-level, RDM-level)
- Monotonicity constraint checking
- Nested model comparison (F-test + AIC)
- RDM improvement metrics
"""

import numpy as np
from scipy.spatial.distance import pdist, squareform


# ============================================================================
# Constants
# ============================================================================

HUE_ANGLES = np.array([0, 45, 90, 135, 180, 225, 270, 315], dtype=float)
N_PAIRS = 28  # C(8,2) pairwise distances
COLOR_NAMES = ['red', 'orange', 'yellow', 'green',
               'cyan', 'blue', 'purple', 'magenta']

# Pair labels for 28 upper-triangle entries (consistent ordering)
PAIR_LABELS = []
for i in range(8):
    for j in range(i + 1, 8):
        PAIR_LABELS.append(f'{COLOR_NAMES[i]}-{COLOR_NAMES[j]}')


# ============================================================================
# T_ψ Transform Functions
# ============================================================================

def T_psi(theta, psi):
    """Fourier-based angular transform (Model A, 4 params).

    T_ψ(θ) = θ + a1*cos(θ) + b1*sin(θ) + a2*cos(2θ) + b2*sin(2θ)

    Args:
        theta: (n,) array of hue angles in degrees
        psi: (4,) array [a1, b1, a2, b2] in degrees

    Returns:
        theta_new: (n,) transformed angles in degrees, wrapped to [0, 360)
    """
    theta_rad = np.deg2rad(theta)
    a1, b1, a2, b2 = psi
    shift = (a1 * np.cos(theta_rad) + b1 * np.sin(theta_rad) +
             a2 * np.cos(2 * theta_rad) + b2 * np.sin(2 * theta_rad))
    return (theta + shift) % 360


def T_psi_free(theta, deltas):
    """Per-color free shift (Model B, 8 params).

    T(θ_i) = θ_i + δ_i

    Args:
        theta: (n,) array of hue angles in degrees
        deltas: (n,) array of per-color shifts in degrees

    Returns:
        theta_new: (n,) transformed angles, wrapped to [0, 360)
    """
    return (theta + deltas) % 360


def T_cone_shift(theta, delta_lambda, cvd_type='deutan'):
    """Cone-shift Model 0 (1 param): physics-based shift from Stockman.

    Approximation: each color experiences a shift proportional to its
    sensitivity to the affected cone (L for protan, M for deutan).
    Uses a simplified sinusoidal approximation of cone sensitivity
    in hue space.

    Args:
        theta: (n,) array of hue angles in degrees
        delta_lambda: scalar, cone shift in nm (positive = redward)
        cvd_type: 'deutan' or 'protan'

    Returns:
        theta_new: (n,) transformed angles, wrapped to [0, 360)
    """
    theta_rad = np.deg2rad(theta)
    # Simplified cone sensitivity profile in hue space
    # Deutan (M-cone): peak sensitivity at ~120° (green), shift along L-M axis
    # Protan (L-cone): peak sensitivity at ~0° (red), shift along L-M axis
    if cvd_type == 'deutan':
        # M-cone sensitivity peaks at green (120°), affect along opponent axis
        sensitivity = np.cos(theta_rad - np.deg2rad(120))
    else:  # protan
        # L-cone sensitivity peaks at red (0°)
        sensitivity = np.cos(theta_rad)

    # Convert nm shift to approximate degrees in hue space
    # Rough calibration: 1nm cone shift ≈ 3-5° hue shift at peak
    nm_to_deg = 4.0
    shift = delta_lambda * nm_to_deg * np.abs(sensitivity)
    # Sign: deutan positive shift moves green toward yellow
    if cvd_type == 'deutan':
        shift = shift * np.sign(np.sin(theta_rad - np.deg2rad(120)))
    else:
        shift = shift * np.sign(np.sin(theta_rad))

    return (theta + shift) % 360


# ============================================================================
# Monotonicity Check
# ============================================================================

def check_monotonicity(psi, n_points=3600):
    """Check if T_ψ is monotonically increasing (dT/dθ > 0 everywhere).

    Args:
        psi: (4,) Fourier parameters
        n_points: number of evaluation points on [0, 360)

    Returns:
        is_monotone: bool
        min_derivative: float (minimum dT/dθ value)
    """
    theta = np.linspace(0, 360, n_points, endpoint=False)
    theta_rad = np.deg2rad(theta)
    a1, b1, a2, b2 = psi

    # dT/dθ = 1 + d(shift)/dθ
    # d(shift)/dθ in rad: -a1*sin(θ) + b1*cos(θ) - 2*a2*sin(2θ) + 2*b2*cos(2θ)
    # Convert to per-degree: multiply by π/180
    d_shift = (-a1 * np.sin(theta_rad) + b1 * np.cos(theta_rad)
               - 2 * a2 * np.sin(2 * theta_rad) + 2 * b2 * np.cos(2 * theta_rad))
    # d_shift is in degrees/radian, convert to degrees/degree
    d_shift_per_deg = d_shift * np.pi / 180

    derivative = 1.0 + d_shift_per_deg
    min_deriv = float(np.min(derivative))

    return min_deriv > 0, min_deriv


def monotonicity_penalty(psi, scale=1000.0, n_points=3600):
    """Soft penalty for monotonicity violation.

    Returns 0 if monotone, positive penalty otherwise.

    Args:
        psi: (4,) Fourier parameters
        scale: penalty scale factor
        n_points: evaluation resolution

    Returns:
        penalty: float >= 0
    """
    theta = np.linspace(0, 360, n_points, endpoint=False)
    theta_rad = np.deg2rad(theta)
    a1, b1, a2, b2 = psi

    d_shift = (-a1 * np.sin(theta_rad) + b1 * np.cos(theta_rad)
               - 2 * a2 * np.sin(2 * theta_rad) + 2 * b2 * np.cos(2 * theta_rad))
    d_shift_per_deg = d_shift * np.pi / 180
    derivative = 1.0 + d_shift_per_deg

    violations = np.maximum(0, -derivative)  # positive where derivative < 0
    return scale * np.sum(violations ** 2)


# ============================================================================
# Loss Functions
# ============================================================================

def compute_predicted_rdm(W0, theta_transformed, n_channels, basis_type='fe'):
    """Compute predicted RDM from W₀ @ C(transformed angles).

    Args:
        W0: (K, V_s) encoding weights
        theta_transformed: (8,) transformed hue angles in degrees
        n_channels: int, number of basis channels (K)
        basis_type: 'fe' or 'lf'

    Returns:
        rdm: (8, 8) correlation distance RDM
    """
    # Import from utils_forward_model for basis functions
    from utils_forward_model import create_basis_full

    basis_full = create_basis_full(n_channels, basis_type=basis_type)
    # Get design matrix at transformed angles
    idx = np.round(theta_transformed).astype(int) % 360
    C_test = basis_full[idx]  # (8, K)
    Y_pred = C_test @ W0  # (8, V_s)

    return squareform(pdist(Y_pred, 'correlation'))


def loss_pattern(psi, W0, Y_mean, n_channels, transform='fourier'):
    """Pattern-level loss: sum of squared prediction errors per color.

    L_pattern(ψ) = Σ_i || W₀ @ C(T_ψ(θ_i)) − Ȳ_CVD(θ_i) ||²

    Args:
        psi: transform parameters
        W0: (K, V_s) encoding weights
        Y_mean: (8, V_s) mean CVD response
        n_channels: number of basis channels
        transform: 'fourier' (4 params), 'free' (8 params), 'cone_shift' (1 param + cvd_type)

    Returns:
        loss: scalar
    """
    from utils_forward_model import create_basis_full

    if transform == 'fourier':
        theta_new = T_psi(HUE_ANGLES, psi)
    elif transform == 'free':
        theta_new = T_psi_free(HUE_ANGLES, psi)
    else:
        raise ValueError(f'Unknown transform: {transform}')

    basis_full = create_basis_full(n_channels)
    idx = np.round(theta_new).astype(int) % 360
    C_test = basis_full[idx]  # (8, K)
    Y_pred = C_test @ W0  # (8, V_s)

    return np.sum((Y_pred - Y_mean) ** 2)


def loss_rdm(psi, W0, hc_rdm_upper, n_channels, transform='fourier',
             weights=None):
    """RDM-level loss: weighted sum of squared pairwise distance errors.

    L_RDM(ψ) = Σ_{i<j} w_ij · (d^ψ_ij − μ_HC_ij)²

    Args:
        psi: transform parameters
        W0: (K, V_s) encoding weights
        hc_rdm_upper: (28,) HC mean RDM upper triangle
        n_channels: number of basis channels
        transform: 'fourier', 'free', or 'cone_shift'
        weights: (28,) optional weights per pair (default: uniform)

    Returns:
        loss: scalar
    """
    if transform == 'fourier':
        theta_new = T_psi(HUE_ANGLES, psi)
    elif transform == 'free':
        theta_new = T_psi_free(HUE_ANGLES, psi)
    else:
        raise ValueError(f'Unknown transform: {transform}')

    pred_rdm = compute_predicted_rdm(W0, theta_new, n_channels)
    pred_upper = pred_rdm[np.triu_indices(8, k=1)]

    residuals = pred_upper - hc_rdm_upper
    if weights is not None:
        return float(np.sum(weights * residuals ** 2))
    return float(np.sum(residuals ** 2))


def loss_rdm_with_penalty(psi, W0, hc_rdm_upper, n_channels,
                          transform='fourier', weights=None,
                          penalty_scale=1000.0):
    """RDM loss + monotonicity penalty.

    Args:
        psi: transform parameters
        W0: (K, V_s)
        hc_rdm_upper: (28,)
        n_channels: int
        transform: 'fourier' or 'free'
        weights: (28,) optional
        penalty_scale: float

    Returns:
        loss: scalar (RDM loss + penalty)
    """
    rdm_loss = loss_rdm(psi, W0, hc_rdm_upper, n_channels,
                        transform=transform, weights=weights)
    if transform == 'fourier':
        penalty = monotonicity_penalty(psi, scale=penalty_scale)
    else:
        penalty = 0.0  # free model has no monotonicity constraint
    return rdm_loss + penalty


# ============================================================================
# Nested Model Comparison
# ============================================================================

def nested_model_comparison(rss_dict, df_dict, n_obs):
    """F-test + AIC for nested model comparison.

    Models must be nested: Model 0 ⊂ Model A ⊂ Model B.

    Args:
        rss_dict: dict of {model_name: RSS} (residual sum of squares)
        df_dict: dict of {model_name: n_params}
        n_obs: int, number of observations (28 for RDM pairs)

    Returns:
        dict with F-tests, AIC values, preferred model
    """
    results = {}

    # AIC for each model
    aic = {}
    for name in rss_dict:
        k = df_dict[name]
        rss = rss_dict[name]
        # AIC = n * ln(RSS/n) + 2k
        if rss > 0:
            aic[name] = n_obs * np.log(rss / n_obs) + 2 * k
        else:
            aic[name] = -np.inf
    results['aic'] = aic

    # AICc (corrected for small sample)
    aicc = {}
    for name in rss_dict:
        k = df_dict[name]
        rss = rss_dict[name]
        if rss > 0 and n_obs - k - 1 > 0:
            aicc[name] = (n_obs * np.log(rss / n_obs) + 2 * k +
                          2 * k * (k + 1) / (n_obs - k - 1))
        else:
            aicc[name] = np.nan
    results['aicc'] = aicc

    # F-tests between consecutive nested models
    model_names = sorted(df_dict.keys(), key=lambda x: df_dict[x])
    f_tests = {}
    for i in range(len(model_names) - 1):
        m_restricted = model_names[i]
        m_full = model_names[i + 1]
        rss_r = rss_dict[m_restricted]
        rss_f = rss_dict[m_full]
        df_r = df_dict[m_restricted]
        df_f = df_dict[m_full]
        df_diff = df_f - df_r
        df_resid = n_obs - df_f

        if df_resid > 0 and rss_f > 0 and df_diff > 0:
            from scipy.stats import f as f_dist
            f_stat = ((rss_r - rss_f) / df_diff) / (rss_f / df_resid)
            p_value = 1 - f_dist.cdf(f_stat, df_diff, df_resid)
            f_tests[f'{m_restricted}_vs_{m_full}'] = {
                'F': float(f_stat),
                'p': float(p_value),
                'df_num': int(df_diff),
                'df_den': int(df_resid),
                'significant': bool(p_value < 0.05)
            }
        else:
            f_tests[f'{m_restricted}_vs_{m_full}'] = {
                'F': np.nan, 'p': np.nan,
                'df_num': int(df_diff), 'df_den': int(df_resid),
                'significant': False
            }
    results['f_tests'] = f_tests

    # Preferred model (lowest AICc)
    valid_aicc = {k: v for k, v in aicc.items() if np.isfinite(v)}
    if valid_aicc:
        results['preferred_model'] = min(valid_aicc, key=valid_aicc.get)
    else:
        results['preferred_model'] = model_names[0]

    return results


# ============================================================================
# RDM Improvement Metrics
# ============================================================================

def compute_rdm_improvement(psi, W0, hc_rdm, baseline_rdm, n_channels,
                            transform='fourier'):
    """Compute percentage improvement in RDM match after applying T_ψ.

    Args:
        psi: transform parameters
        W0: (K, V_s)
        hc_rdm: (8, 8) HC mean RDM
        baseline_rdm: (8, 8) baseline (unfiltered) predicted RDM
        n_channels: int
        transform: 'fourier' or 'free'

    Returns:
        dict with rdm_loss_baseline, rdm_loss_filtered, pct_improvement,
             per_pair_improvement (28,)
    """
    hc_upper = hc_rdm[np.triu_indices(8, k=1)]
    baseline_upper = baseline_rdm[np.triu_indices(8, k=1)]

    if transform == 'fourier':
        theta_new = T_psi(HUE_ANGLES, psi)
    elif transform == 'free':
        theta_new = T_psi_free(HUE_ANGLES, psi)
    else:
        raise ValueError(f'Unknown transform: {transform}')

    filtered_rdm = compute_predicted_rdm(W0, theta_new, n_channels)
    filtered_upper = filtered_rdm[np.triu_indices(8, k=1)]

    baseline_resid = (baseline_upper - hc_upper) ** 2
    filtered_resid = (filtered_upper - hc_upper) ** 2

    baseline_loss = float(np.sum(baseline_resid))
    filtered_loss = float(np.sum(filtered_resid))

    if baseline_loss > 0:
        pct = 100.0 * (1.0 - filtered_loss / baseline_loss)
    else:
        pct = 0.0

    # Per-pair improvement
    per_pair = np.where(baseline_resid > 0,
                        100.0 * (1.0 - filtered_resid / baseline_resid),
                        0.0)

    return {
        'rdm_loss_baseline': baseline_loss,
        'rdm_loss_filtered': filtered_loss,
        'pct_improvement': float(pct),
        'per_pair_improvement': per_pair.tolist(),
        'per_pair_labels': PAIR_LABELS,
    }


def compute_rdm_spearman(pred_rdm, target_rdm):
    """Spearman correlation between upper triangles of two RDMs.

    Args:
        pred_rdm: (8, 8)
        target_rdm: (8, 8)

    Returns:
        rho: float, Spearman r
        p: float, p-value
    """
    from scipy.stats import spearmanr
    pred_upper = pred_rdm[np.triu_indices(8, k=1)]
    target_upper = target_rdm[np.triu_indices(8, k=1)]
    rho, p = spearmanr(pred_upper, target_upper)
    return float(rho), float(p)
